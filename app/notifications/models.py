"""SHUNYA — Push Notifications (Web Push / PWA).

Persistence for Web Push API subscriptions (PushSubscription) and a
notification dispatch service.

This implements the browser/PWA notification path for CG-10 (D-10). The
Web Push API provides end-to-end push notifications through the browser
service worker — no app store deployment required. This satisfies the
SHUNYA product requirement for transactional notifications (commitment
due, status change, conversation reply, automation fired).

Platform coverage (Web Push API):
  - Desktop: Chrome, Firefox, Edge, Safari 16.4+
  - Mobile: Android Chrome (PWA-installed), Android WebView
  - iOS: Safari 16.4+ PWA with limited support
"""

from __future__ import annotations

from datetime import datetime

from app import db
from sqlalchemy import Index, Text


class PushSubscription(db.Model):
    """A user's Web Push subscription (per device/browser).

    The subscription object is the opaque JSON the browser returns from
    PushManager.subscribe(). It is passed verbatim to the push service.
    """

    __tablename__ = "shunya_push_subscriptions"
    __table_args__ = (
        Index("ix_push_sub_identity", "identity_id"),
        Index("ix_push_sub_endpoint", "endpoint", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    # Browser push endpoint URL supplied by the push service.
    endpoint = db.Column(Text, nullable=False)
    # Keys object from the PushSubscription JSON ({p256dh, auth}).
    p256dh = db.Column(Text, default="")
    auth = db.Column(Text, default="")
    # Full subscription JSON for round-trip fidelity.
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