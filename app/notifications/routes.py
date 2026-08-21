"""PWA Notification Service — VAPID key management, subscription, push dispatch.

Routes:
  POST   /api/v1/notifications/subscribe          — save a push subscription
  DELETE /api/v1/notifications/subscribe?endpoint= — remove a subscription
  GET    /api/v1/notifications/vapid-public-key    — return the VAPID public key
  POST   /api/v1/notifications/send                — send a push notification
  GET    /api/v1/notifications                      — list user's in-app notifications
  POST   /api/v1/notifications/mark-read            — mark notifications as read
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from flask import Blueprint, g, jsonify, request

from app import db
from app.integration.models import Notification as NotificationRecord
from app.notifications.models import PushSubscription

logger = logging.getLogger(__name__)

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/v1/notifications")

# ---------------------------------------------------------------------------
# VAPID key management
# ---------------------------------------------------------------------------

_VAPID_PRIVATE_KEY: str | None = None
_VAPID_PUBLIC_KEY: str | None = None


def _get_vapid_keys() -> tuple[str, str]:
    """Get or generate VAPID keys for Web Push.

    Keys are stored in environment variables. If not set, they are generated
    once and held in memory for the process lifetime.
    """
    global _VAPID_PRIVATE_KEY, _VAPID_PUBLIC_KEY

    if _VAPID_PRIVATE_KEY and _VAPID_PUBLIC_KEY:
        return _VAPID_PRIVATE_KEY, _VAPID_PUBLIC_KEY

    env_priv = os.environ.get("VAPID_PRIVATE_KEY")
    env_pub = os.environ.get("VAPID_PUBLIC_KEY")

    if env_priv and env_pub:
        _VAPID_PRIVATE_KEY = env_priv
        _VAPID_PUBLIC_KEY = env_pub
        return _VAPID_PRIVATE_KEY, _VAPID_PUBLIC_KEY

    # Generate new keys
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    # Private key in PEM format
    _VAPID_PRIVATE_KEY = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")

    # Public key in uncompressed point format (65 bytes), base64-encoded
    pub_bytes = public_key.public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    _VAPID_PUBLIC_KEY = base64url_encode(pub_bytes)

    logger.info("Generated new VAPID keys for Web Push")
    return _VAPID_PRIVATE_KEY, _VAPID_PUBLIC_KEY


def base64url_encode(data: bytes) -> str:
    """Base64 URL-safe encode without padding."""
    import base64

    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_decode(data: str) -> bytes:
    """Base64 URL-safe decode with padding restoration."""
    import base64

    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@notifications_bp.route("/vapid-public-key", methods=["GET"])
def get_vapid_public_key():
    """Return the VAPID public key so the client can subscribe."""
    _, pub_key = _get_vapid_keys()
    return jsonify({"public_key": pub_key})


@notifications_bp.route("/subscribe", methods=["POST"])
def subscribe():
    """Save a push subscription for the current user.

    Expects JSON body:
      {
        "endpoint": "https://...",
        "keys": { "p256dh": "...", "auth": "..." },
        "user_agent": "optional"
      }
    """
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    endpoint = data.get("endpoint", "")
    keys = data.get("keys", {})
    user_agent = data.get("user_agent", request.headers.get("User-Agent", ""))

    if not endpoint:
        return jsonify({"error": "endpoint is required"}), 400

    p256dh = keys.get("p256dh", "")
    auth = keys.get("auth", "")
    subscription_json = json.dumps(data)

    # Check for existing subscription by endpoint
    existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if existing:
        existing.p256dh = p256dh
        existing.auth = auth
        existing.subscription_json = subscription_json
        existing.user_agent = user_agent or existing.user_agent
        existing.last_used_at = datetime.utcnow()
        existing.is_active = True
    else:
        sub = PushSubscription(
            identity_id=identity_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            subscription_json=subscription_json,
            user_agent=user_agent,
            last_used_at=datetime.utcnow(),
        )
        db.session.add(sub)

    db.session.commit()
    logger.info("Push subscription saved for %s", identity_id)
    return jsonify({"success": True, "identity_id": identity_id})


@notifications_bp.route("/subscribe", methods=["DELETE"])
def unsubscribe():
    """Remove a push subscription by endpoint."""
    endpoint = request.args.get("endpoint", "")
    if not endpoint:
        return jsonify({"error": "endpoint is required"}), 400

    sub = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if sub:
        sub.is_active = False
        db.session.commit()
        logger.info("Push subscription deactivated for endpoint=%s", endpoint[:50])

    return jsonify({"success": True})


@notifications_bp.route("/send", methods=["POST"])
def send_notification():
    """Send a push notification to all active subscriptions for an identity.

    Expects JSON body:
      {
        "identity_id": "sid_xxx",           // optional — defaults to g.identity_id
        "title": "Notification title",
        "body": "Notification body",
        "url": "/objects/abc123",           // optional — click target
        "tag": "commitment_due",            // optional — grouping tag
        "save_notification": true           // optional — also save in-app notification
      }
    """
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")
    data = request.get_json(silent=True) or {}

    target_identity = data.get("identity_id", identity_id)
    if not target_identity:
        return jsonify({"error": "No identity specified"}), 400

    title = data.get("title", "SHUNYA")
    body = data.get("body", "")
    url = data.get("url", "/")
    tag = data.get("tag", "general")
    save_notification = data.get("save_notification", True)

    # Save in-app notification record
    if save_notification:
        notif = NotificationRecord(
            identity_id=target_identity,
            notification_type=tag,
            title=title,
            body=body,
            object_id=url.split("/")[-1] if "/" in url else None,
            is_read=False,
        )
        db.session.add(notif)
        db.session.commit()

    # Send to all active push subscriptions
    subs = PushSubscription.query.filter_by(
        identity_id=target_identity, is_active=True
    ).all()

    if not subs:
        return jsonify({
            "success": True,
            "sent": 0,
            "total_subs": 0,
            "message": "No push subscriptions — in-app notification saved",
        })

    priv_key, _ = _get_vapid_keys()
    from pywebpush import webpush

    sent_count = 0
    failed_count = 0
    for sub in subs:
        try:
            sub_info = sub.to_subscription_dict()
            webpush(
                subscription_info=sub_info,
                data=json.dumps({
                    "title": title,
                    "body": body,
                    "url": url,
                    "tag": tag,
                    "timestamp": datetime.utcnow().isoformat(),
                }),
                vapid_private_key=priv_key,
                vapid_claims={
                    "sub": f"mailto:{os.environ.get('VAPID_CONTACT', 'shunya@nousresearch.com')}",
                },
            )
            sent_count += 1
            sub.last_used_at = datetime.utcnow()
        except Exception as exc:
            logger.warning("Push failed for sub %d: %s", sub.id, exc)
            # If the push service returns 410 Gone, the subscription is dead
            if "410" in str(exc) or "gone" in str(exc).lower():
                sub.is_active = False
                logger.info("Deactivated dead subscription %d", sub.id)
            failed_count += 1

    db.session.commit()
    return jsonify({
        "success": True,
        "sent": sent_count,
        "failed": failed_count,
        "total_subs": len(subs),
    })


@notifications_bp.route("", methods=["GET"])
def list_notifications():
    """List in-app notifications for the current user."""
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401

    limit = min(int(request.args.get("limit", 50)), 200)
    offset = int(request.args.get("offset", 0))
    unread_only = request.args.get("unread_only", "").lower() in ("true", "1")

    q = NotificationRecord.query.filter_by(identity_id=identity_id)
    if unread_only:
        q = q.filter_by(is_read=False)
    q = q.order_by(NotificationRecord.created_at.desc()).offset(offset).limit(limit)
    notifications = [n.to_dict() for n in q.all()]

    unread_count = NotificationRecord.query.filter_by(
        identity_id=identity_id, is_read=False
    ).count()

    return jsonify({
        "notifications": notifications,
        "unread_count": unread_count,
        "limit": limit,
        "offset": offset,
    })


@notifications_bp.route("/mark-read", methods=["POST"])
def mark_read():
    """Mark notifications as read.

    Expects JSON body:
      { "ids": [1, 2, 3] }   // optional — omitting marks all as read
    """
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])

    if ids:
        NotificationRecord.query.filter(
            NotificationRecord.id.in_(ids),
            NotificationRecord.identity_id == identity_id,
        ).update({"is_read": True, "read_at": datetime.utcnow()}, synchronize_session=False)
    else:
        NotificationRecord.query.filter_by(
            identity_id=identity_id, is_read=False
        ).update({"is_read": True, "read_at": datetime.utcnow()}, synchronize_session=False)

    db.session.commit()
    return jsonify({"success": True})


@notifications_bp.route("/unread-count", methods=["GET"])
def unread_count():
    """Return the number of unread notifications."""
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401

    count = NotificationRecord.query.filter_by(
        identity_id=identity_id, is_read=False
    ).count()
    return jsonify({"unread_count": count})