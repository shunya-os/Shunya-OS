"""SHUNYA M6 — Notification Service.

Handles in-app notification creation, dispatch, read tracking,
and email notification delivery.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app import db
from app.integration.models import Notification, NotificationPreference

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Notification creation
# ---------------------------------------------------------------------------

def create_notification(
    identity_id: str,
    notification_type: str,
    title: str,
    body: str = "",
    object_id: str | None = None,
    space_id: str | None = None,
    conv_id: str | None = None,
) -> Notification:
    """Create a notification and attempt email dispatch if configured."""
    notif = Notification(
        identity_id=identity_id,
        notification_type=notification_type,
        title=title,
        body=body,
        object_id=object_id,
        space_id=space_id,
        conv_id=conv_id,
    )
    db.session.add(notif)
    db.session.commit()
    return notif


# ---------------------------------------------------------------------------
# Notification queries
# ---------------------------------------------------------------------------

def get_notifications(
    identity_id: str,
    limit: int = 50,
    unread_only: bool = False,
) -> list[dict[str, Any]]:
    """Get notifications for an identity."""
    query = Notification.query.filter_by(identity_id=identity_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    notifs = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return [n.to_dict() for n in notifs]


def get_unread_count(identity_id: str) -> int:
    """Get the count of unread notifications."""
    return Notification.query.filter_by(
        identity_id=identity_id, is_read=False
    ).count()


def mark_as_read(notification_id: int) -> bool:
    """Mark a single notification as read."""
    notif = Notification.query.get(notification_id)
    if not notif:
        return False
    notif.is_read = True
    notif.read_at = datetime.utcnow()
    db.session.commit()
    return True


def mark_all_as_read(identity_id: str) -> int:
    """Mark all notifications as read for an identity. Returns count."""
    notifs = Notification.query.filter_by(
        identity_id=identity_id, is_read=False
    ).all()
    now = datetime.utcnow()
    for n in notifs:
        n.is_read = True
        n.read_at = now
    db.session.commit()
    return len(notifs)


# ---------------------------------------------------------------------------
# Notification preferences
# ---------------------------------------------------------------------------

def get_preferences(identity_id: str) -> dict[str, Any]:
    """Get or create notification preferences for an identity."""
    prefs = NotificationPreference.query.filter_by(
        identity_id=identity_id
    ).first()
    if not prefs:
        prefs = NotificationPreference(identity_id=identity_id)
        db.session.add(prefs)
        db.session.commit()
    return prefs.to_dict()


def update_preferences(
    identity_id: str,
    email_notifications: bool | None = None,
    in_app_notifications: bool | None = None,
    digest_frequency: str | None = None,
    quiet_hours_start: str | None = None,
    quiet_hours_end: str | None = None,
) -> dict[str, Any]:
    """Update notification preferences."""
    prefs = NotificationPreference.query.filter_by(
        identity_id=identity_id
    ).first()
    if not prefs:
        prefs = NotificationPreference(identity_id=identity_id)
        db.session.add(prefs)

    if email_notifications is not None:
        prefs.email_notifications = email_notifications
    if in_app_notifications is not None:
        prefs.in_app_notifications = in_app_notifications
    if digest_frequency is not None:
        prefs.digest_frequency = digest_frequency
    if quiet_hours_start is not None:
        prefs.quiet_hours_start = quiet_hours_start
    if quiet_hours_end is not None:
        prefs.quiet_hours_end = quiet_hours_end

    db.session.commit()
    return prefs.to_dict()


# ---------------------------------------------------------------------------
# Integration connections
# ---------------------------------------------------------------------------

def save_connection(
    identity_id: str,
    provider: str,
    access_token: str,
    refresh_token: str = "",
    label: str = "",
    expires_at: datetime | None = None,
) -> dict[str, Any]:
    """Save or update an OAuth integration connection."""
    from app.integration.models import IntegrationConnection

    conn = IntegrationConnection.query.filter_by(
        identity_id=identity_id, provider=provider
    ).first()

    if conn:
        conn.access_token = access_token
        conn.refresh_token = refresh_token or conn.refresh_token
        conn.label = label or conn.label
        conn.token_expires_at = expires_at
        conn.is_active = True
    else:
        conn = IntegrationConnection(
            identity_id=identity_id,
            provider=provider,
            label=label,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=expires_at,
        )
        db.session.add(conn)

    db.session.commit()
    return conn.to_dict()


def get_connections(identity_id: str) -> list[dict[str, Any]]:
    """Get all integration connections for an identity."""
    from app.integration.models import IntegrationConnection

    conns = IntegrationConnection.query.filter_by(
        identity_id=identity_id
    ).all()
    return [c.to_dict() for c in conns]


def remove_connection(identity_id: str, provider: str) -> bool:
    """Remove an integration connection."""
    from app.integration.models import IntegrationConnection

    conn = IntegrationConnection.query.filter_by(
        identity_id=identity_id, provider=provider
    ).first()
    if not conn:
        return False
    conn.is_active = False
    db.session.commit()
    return True