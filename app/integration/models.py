"""SHUNYA M6 — Connected Business Models.

Persistence models for notifications, integrations, and email linking.
"""

from datetime import datetime

from app import db
from sqlalchemy import Index, Text


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

class Notification(db.Model):
    """In-app notification for users. Supports entity linking, read tracking,
    and email dispatch status."""

    __tablename__ = "m6_notifications"
    __table_args__ = (
        Index("ix_m6_notif_user", "identity_id", "is_read", "created_at"),
        Index("ix_m6_notif_object", "object_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    notification_type = db.Column(db.String(40), nullable=False)
    # Types: entity_created, entity_updated, status_changed, commitment_due,
    #        conversation_new, reminder, system, automation_fired
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(Text, default="")
    object_id = db.Column(db.String(64), nullable=True)
    space_id = db.Column(db.String(64), nullable=True)
    conv_id = db.Column(db.String(64), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    is_email_sent = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "notification_type": self.notification_type,
            "title": self.title,
            "body": self.body,
            "object_id": self.object_id,
            "space_id": self.space_id,
            "conv_id": self.conv_id,
            "is_read": self.is_read,
            "is_email_sent": self.is_email_sent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }


# ---------------------------------------------------------------------------
# Integration Connection
# ---------------------------------------------------------------------------

class IntegrationConnection(db.Model):
    """OAuth connection to external services (email, calendar, etc.)."""

    __tablename__ = "m6_integrations"
    __table_args__ = (
        Index("ix_m6_integ_type", "identity_id", "provider"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    provider = db.Column(db.String(40), nullable=False)
    # Providers: gmail, outlook, google_calendar, outlook_calendar
    label = db.Column(db.String(255), default="")
    access_token = db.Column(db.Text, default="")
    refresh_token = db.Column(db.Text, default="")
    token_expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_sync_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "provider": self.provider,
            "label": self.label,
            "is_active": self.is_active,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Email Cache (synced emails linked to entities)
# ---------------------------------------------------------------------------

class CachedEmail(db.Model):
    """Cached email that has been synced and linked to entities."""

    __tablename__ = "m6_cached_emails"
    __table_args__ = (
        Index("ix_m6_email_msg", "message_id", unique=True),
        Index("ix_m6_email_object", "object_id"),
        Index("ix_m6_email_from", "from_email"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    message_id = db.Column(db.String(255), nullable=False)
    thread_id = db.Column(db.String(255), nullable=True)
    from_email = db.Column(db.String(255), nullable=False)
    from_name = db.Column(db.String(255), default="")
    to_email = db.Column(db.Text, default="")
    subject = db.Column(db.String(500), default="")
    body_preview = db.Column(db.String(500), default="")
    body_text = db.Column(Text, default="")
    received_at = db.Column(db.DateTime, nullable=True)
    object_id = db.Column(db.String(64), nullable=True)
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "subject": self.subject,
            "body_preview": self.body_preview,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "object_id": self.object_id,
            "is_processed": self.is_processed,
        }


# ---------------------------------------------------------------------------
# Notification Preference
# ---------------------------------------------------------------------------

class NotificationPreference(db.Model):
    """Per-user notification preferences."""

    __tablename__ = "m6_notif_prefs"

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    email_notifications = db.Column(db.Boolean, default=True)
    in_app_notifications = db.Column(db.Boolean, default=True)
    digest_frequency = db.Column(db.String(20), default="immediate")
    # immediate, daily, weekly
    quiet_hours_start = db.Column(db.String(5), default="")
    quiet_hours_end = db.Column(db.String(5), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "email_notifications": self.email_notifications,
            "in_app_notifications": self.in_app_notifications,
            "digest_frequency": self.digest_frequency,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
        }