"""SHUNYA — Platform Models (FDA26).

Webhook subscription + delivery log models.

Canonical rules:
- Webhook subscriptions are scoped to an identity (creator) and optional workspace.
- A webhook secret is generated server-side per subscription; used for HMAC
  signature verification on delivery.
- Every delivery attempt is recorded in WebhookDelivery for evidence/audit.
- Idempotency is enforced by (subscription_id, event_id) unique constraint.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from app import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WebhookSubscription(db.Model):
    """A server-side webhook subscription.

    The creator identity owns the subscription. The secret is generated
    server-side and only ever shown once at creation (and on explicit
    rotation) — it is never returned in list responses.
    """

    __tablename__ = "platform_webhook_subscriptions"
    __table_args__ = (
        db.UniqueConstraint("identity_id", "url", name="uq_webhook_identity_url"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(100), nullable=False, index=True)
    workspace_id = db.Column(db.String(50), nullable=True, index=True)
    label = db.Column(db.String(200), default="")
    url = db.Column(db.String(500), nullable=False)
    events_json = db.Column(db.Text, default="[]")  # JSON array of event names
    secret = db.Column(db.String(64), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    last_delivery_at = db.Column(db.DateTime, nullable=True)
    last_delivery_status = db.Column(db.String(30), default="never")
    delivery_count = db.Column(db.Integer, default=0)

    @property
    def events(self) -> list[str]:
        import json

        try:
            return json.loads(self.events_json or "[]")
        except (ValueError, TypeError):
            return []

    @events.setter
    def events(self, value: list[str]) -> None:
        import json

        self.events_json = json.dumps(value or [])

    def to_dict(self, include_secret: bool = False) -> dict:
        d = {
            "id": self.id,
            "identity_id": self.identity_id,
            "workspace_id": self.workspace_id,
            "label": self.label,
            "url": self.url,
            "events": self.events,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_delivery_at": self.last_delivery_at.isoformat() if self.last_delivery_at else None,
            "last_delivery_status": self.last_delivery_status,
            "delivery_count": self.delivery_count,
        }
        if include_secret:
            d["secret"] = self.secret
        return d

    @staticmethod
    def generate_secret() -> str:
        return secrets.token_urlsafe(32)


class WebhookDelivery(db.Model):
    """One delivery attempt (or event) for a webhook subscription.

    Evidence: every attempt is persisted. Retry count, response status,
    and error are recorded for observability and audit.
    """

    __tablename__ = "platform_webhook_deliveries"
    __table_args__ = (
        db.UniqueConstraint("subscription_id", "event_id", name="uq_webhook_delivery_event"),
    )

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(
        db.Integer, db.ForeignKey("platform_webhook_subscriptions.id"), nullable=False, index=True
    )
    event_id = db.Column(db.String(100), nullable=False)
    event_name = db.Column(db.String(100), nullable=False)
    payload_json = db.Column(db.Text, default="{}")
    attempt = db.Column(db.Integer, default=1)
    max_attempts = db.Column(db.Integer, default=3)
    status = db.Column(db.String(30), default="pending")  # pending, delivered, failed, exhausted
    http_status = db.Column(db.Integer, nullable=True)
    response_body = db.Column(db.Text, default="")
    error = db.Column(db.Text, default="")
    next_retry_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    delivered_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subscription_id": self.subscription_id,
            "event_id": self.event_id,
            "event_name": self.event_name,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "status": self.status,
            "http_status": self.http_status,
            "error": self.error[:500],
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }
