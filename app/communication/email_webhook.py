"""
email_webhook.py — Resend webhook endpoint using Svix verification protocol.

Resend's webhook infrastructure uses Svix (https://docs.svix.com/).
Headers:
  svix-id          — unique event ID
  svix-timestamp   — Unix timestamp
  svix-signature   — v1=<base64_hmac_sha256>

Verification:
  1. Extract signed_payload = f"{svix_id}.{svix_timestamp}.{body}"
  2. Compute HMAC-SHA256(whsec_<secret>, signed_payload)
  3. Compare against each signature in svix-signature (space-separated, v1= prefix)
  4. Replay protection: timestamp must be within 5 minutes of now

Endpoints:
  POST /api/v1/email/webhook — Receive delivery events from Resend
"""

import base64
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app import db
from app.communication.email_models import EmailRecord, EmailDeliveryState

logger = logging.getLogger(__name__)

email_webhook_bp = Blueprint("email_webhook", __name__, url_prefix="/api/v1/email")

_WH_SECRET = ""
_WH_SECRET_ENV = "RESEND_WEBHOOK_SECRET"
_WH_TIMESTAMP_TOLERANCE = 300  # 5 minutes


def _init_webhook_secret():
    """Load webhook secret from environment."""
    global _WH_SECRET
    import os
    _WH_SECRET = os.environ.get(_WH_SECRET_ENV, "")


def _verify_svix_signature(body: bytes, headers: dict) -> bool:
    """Verify Resend/Svix webhook signature.

    Svix format:
      svix-id: <event_id>
      svix-timestamp: <unix_epoch_seconds>
      svix-signature: v1=<base64_hmac>,v1=<base64_hmac2>...

    The secret is the whsec_... string (with or without the whsec- prefix).
    """
    if not _WH_SECRET:
        return False

    svix_id = headers.get("svix-id", "")
    svix_timestamp = headers.get("svix-timestamp", "")
    svix_signature = headers.get("svix-signature", "")

    if not svix_id or not svix_timestamp or not svix_signature:
        logger.warning("Svix webhook: missing required headers")
        return False

    # Replay protection: timestamp within tolerance
    try:
        event_time = int(svix_timestamp)
        now = int(time.time())
        if abs(now - event_time) > _WH_TIMESTAMP_TOLERANCE:
            logger.warning(
                "Svix webhook: timestamp %ds outside tolerance window",
                abs(now - event_time),
            )
            return False
    except ValueError:
        logger.warning("Svix webhook: invalid timestamp: %s", svix_timestamp)
        return False

    # Build signed payload: svix_id.svix_timestamp.body
    signed_payload = f"{svix_id}.{svix_timestamp}.".encode() + body

    # Normalize secret: Svix accepts whsec_ prefix but Resend may also
    # pass it with or without the prefix.
    secret = _WH_SECRET.encode("utf-8")

    # Compute expected signature
    expected = hmac.new(secret, signed_payload, hashlib.sha256).digest()
    expected_b64 = base64.b64encode(expected).decode("utf-8")

    # Each signature in svix-signature is space-separated: "v1=xxx v1=yyy"
    for part in svix_signature.split(" "):
        part = part.strip()
        if not part.startswith("v1="):
            continue
        sig_value = part[3:]  # strip "v1=" prefix
        if hmac.compare_digest(expected_b64, sig_value):
            return True

    logger.warning("Svix webhook: no matching signature found")
    return False


def _handle_delivery_event(event_type: str, payload: dict) -> bool:
    """Process a delivery event and update EmailRecord lifecycle state."""
    provider_id = payload.get("email_id", "")
    if not provider_id:
        logger.warning("Webhook: event has no email_id: %s", payload.get("id", "?"))
        return False

    record = EmailRecord.query.filter_by(provider_message_id=provider_id).first()
    if not record:
        logger.warning("Webhook: no EmailRecord for provider_id=%s", provider_id)
        return False

    event_to_state = {
        "delivered": EmailDeliveryState.DELIVERED,
        "bounced": EmailDeliveryState.BOUNCED,
        "complained": EmailDeliveryState.COMPLAINED,
        "opened": None,
        "clicked": None,
    }

    new_state = event_to_state.get(event_type)
    if new_state is None:
        logger.info("Webhook: info event %s for %s (record %d)", event_type, provider_id, record.id)
        return True

    error_msg = None
    if event_type == "bounced":
        bounce = payload.get("bounce", {})
        error_msg = f"Bounce type={bounce.get('type','?')} reason={bounce.get('reason','?')}"
    elif event_type == "complained":
        complaint = payload.get("complaint", {})
        error_msg = f"Complaint type={complaint.get('type','?')}"

    record.set_state(new_state, error=error_msg)
    record.webhook_verified_at = datetime.now(timezone.utc)
    record.webhook_event_id = payload.get("id", "")
    db.session.commit()

    logger.info("Webhook: %s %s (record %d, %s)", event_type, record.recipient, record.id, provider_id)
    return True


@email_webhook_bp.route("/webhook", methods=["POST"])
def resend_webhook():
    """Receive delivery events from Resend (Svix-signed webhooks)."""
    if not _WH_SECRET:
        return jsonify({"error": "Webhook not configured", "status": "unconfigured"}), 501

    body = request.get_data()

    # Verify Svix signature
    headers = {
        "svix-id": request.headers.get("svix-id", ""),
        "svix-timestamp": request.headers.get("svix-timestamp", ""),
        "svix-signature": request.headers.get("svix-signature", ""),
    }
    if not _verify_svix_signature(body, headers):
        return jsonify({"error": "Invalid signature"}), 401

    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    events = data if isinstance(data, list) else [data]
    results = []
    for event in events:
        event_type = event.get("type", "")
        payload = event.get("data", event)
        if event_type in ("email.delivered", "email.bounced", "email.complained",
                          "email.opened", "email.clicked"):
            norm_type = event_type.replace("email.", "")
            handled = _handle_delivery_event(norm_type, payload)
            results.append({"event_id": payload.get("id", ""), "event_type": event_type, "handled": handled})
        else:
            logger.debug("Webhook: unhandled event: %s", event_type)
            results.append({"event_id": event.get("id", ""), "event_type": event_type, "handled": False})

    return jsonify({"status": "ok", "events": results}), 200


_init_webhook_secret()