"""Notification Preference API — event_type × channel toggle matrix.

Routes:
  GET  /api/v1/notifications/preferences   — list preferences for current identity
  PUT  /api/v1/notifications/preferences   — bulk update preference rows
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from app import db
from app.notifications.models import (
    DEFAULT_EVENT_TYPES,
    CHANNELS,
    NotificationPreference,
)
from app.authz.decorators import require_permission

logger = logging.getLogger(__name__)

preferences_bp = Blueprint(
    "notification_preferences",
    __name__,
    url_prefix="/api/v1/notifications/preferences",
)


def _ensure_defaults(identity_id: str, tenant_id: str | None = None):
    """Create default preference rows for this identity if none exist."""
    existing = (
        db.session.query(NotificationPreference.event_type, NotificationPreference.channel)
        .filter_by(identity_id=identity_id)
        .all()
    )
    if len(existing) >= len(DEFAULT_EVENT_TYPES) * len(CHANNELS):
        return  # already seeded

    existing_set = set(existing)
    now = datetime.now(timezone.utc)
    rows = []
    for et in DEFAULT_EVENT_TYPES:
        for ch in CHANNELS:
            if (et, ch) not in existing_set:
                rows.append(
                    NotificationPreference(
                        identity_id=identity_id,
                        tenant_id=tenant_id,
                        event_type=et,
                        channel=ch,
                        enabled=True,
                        created_at=now,
                        updated_at=now,
                    )
                )
    if rows:
        db.session.bulk_save_objects(rows)
        db.session.commit()
        logger.info("Seeded %d preference rows for %s", len(rows), identity_id)


@preferences_bp.route("", methods=["GET"])
@require_permission("rel.view")
def list_preferences():
    """Return all notification preferences for the current identity.

    Ensures default rows exist before returning.
    """
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401

    tenant_id = getattr(g, "current_org_id", None)
    _ensure_defaults(identity_id, str(tenant_id) if tenant_id else None)

    prefs = (
        NotificationPreference.query.filter_by(identity_id=identity_id)
        .order_by(NotificationPreference.event_type, NotificationPreference.channel)
        .all()
    )

    # Group by event_type
    grouped: dict[str, dict[str, bool]] = {}
    for p in prefs:
        grouped.setdefault(p.event_type, {})[p.channel] = p.enabled

    return jsonify({
        "success": True,
        "preferences": [p.to_dict() for p in prefs],
        "grouped": grouped,
        "event_types": list(DEFAULT_EVENT_TYPES),
        "channels": list(CHANNELS),
    })


@preferences_bp.route("", methods=["PUT"])
@require_permission("rel.view")
def update_preferences():
    """Bulk-update notification preferences.

    Expects JSON body:
      { "preferences": [ { "event_type": "...", "channel": "...", "enabled": bool }, ... ] }
    """
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    updates = data.get("preferences", [])

    if not updates:
        return jsonify({"error": "No preferences provided"}), 400

    tenant_id = getattr(g, "current_org_id", None)
    now = datetime.now(timezone.utc)
    updated_count = 0
    errors: list[str] = []

    for item in updates:
        et = item.get("event_type", "")
        ch = item.get("channel", "")
        enabled = item.get("enabled", True)

        if et not in DEFAULT_EVENT_TYPES:
            errors.append(f"Unknown event_type: {et}")
            continue
        if ch not in CHANNELS:
            errors.append(f"Unknown channel: {ch}")
            continue

        pref = NotificationPreference.query.filter_by(
            identity_id=identity_id,
            event_type=et,
            channel=ch,
        ).first()

        if pref:
            pref.enabled = enabled
            pref.updated_at = now
        else:
            pref = NotificationPreference(
                identity_id=identity_id,
                tenant_id=str(tenant_id) if tenant_id else None,
                event_type=et,
                channel=ch,
                enabled=enabled,
                created_at=now,
                updated_at=now,
            )
            db.session.add(pref)
        updated_count += 1

    db.session.commit()
    logger.info("Updated %d preference rows for %s", updated_count, identity_id)

    return jsonify({
        "success": True,
        "updated": updated_count,
        "errors": errors,
    })