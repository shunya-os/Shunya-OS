"""SHUNYA — Notification models.

PushSubscription for Web Push / PWA subscriptions.
NotificationPreference for event-type × channel preference matrix.
"""

from __future__ import annotations

from datetime import datetime

from app import db
from sqlalchemy import Index, Text


class PushSubscription(db.Model):
    """A user's Web Push subscription (per device/browser)."""

    __tablename__ = "shunya_push_subscriptions"
    __table_args__ = (
        Index("ix_push_sub_identity", "identity_id"),
        Index("ix_push_sub_endpoint", "endpoint", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    endpoint = db.Column(Text, nullable=False)
    p256dh = db.Column(Text, default="")
    auth = db.Column(Text, default="")
    subscription_json = db.Column(Text, default="")
    user_agent = db.Column(db.String(255), default="")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "endpoint": self.endpoint,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }

    def to_subscription_dict(self):
        """Reconstruct the PushSubscription JSON for pywebpush."""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh,
                "auth": self.auth,
            },
        }


DEFAULT_EVENT_TYPES = [
    "attention.item",
    "execution.completed",
    "execution.failed",
    "document.processed",
    "invitation.received",
    "proposal.status",
    "payment.received",
    "system.alert",
]

CHANNELS = ["email", "push", "in-app", "browser"]


class NotificationPreference(db.Model):
    """Per-event-type × per-channel preference toggle.

    One row per (identity_id, event_type, channel) combination.
    Created lazily on first read for the default-set of event_types × channels.
    """

    __tablename__ = "notif_event_preferences"
    __table_args__ = (
        Index("ix_notif_pref_identity", "identity_id", "tenant_id"),
        Index("ix_notif_pref_lookup", "identity_id", "event_type", "channel", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    tenant_id = db.Column(db.String(64), nullable=True)
    event_type = db.Column(db.String(60), nullable=False)
    channel = db.Column(db.String(20), nullable=False)  # email, push, in-app, browser
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "tenant_id": self.tenant_id,
            "event_type": self.event_type,
            "channel": self.channel,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }