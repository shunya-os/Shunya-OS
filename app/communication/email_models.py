"""
email_models.py — Durable email record model with full lifecycle tracking.

Lifecycle states:
  requested      → initial state, not yet sent to provider
  accepted       → provider accepted the send request
  delivered      → provider confirmed delivery to recipient inbox
  bounced        → provider returned bounce (invalid address, mailbox full, etc.)
  complained     → recipient marked as spam
  failed         → hard failure (provider rejected, auth error, etc.)
  retry_pending  → temporary failure, retry scheduled
  exhausted      → all retries exhausted, final failure
  cancelled      → send cancelled before provider acceptance

Required by: FDA36, M2C.5R, ADR-003 (communication audit)
"""

import enum
from datetime import datetime, timezone

from app import db


class EmailDeliveryState(enum.Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    COMPLAINED = "complained"
    FAILED = "failed"
    RETRY_PENDING = "retry_pending"
    EXHAUSTED = "exhausted"
    CANCELLED = "cancelled"


class EmailCategory(enum.Enum):
    SECURITY = "security"
    OPERATIONAL = "operational"
    BUSINESS = "business"
    MARKETING = "marketing"


class EmailRecord(db.Model):
    """Durable record of every email send attempt.

    Provides idempotency, delivery tracking, bounce handling,
    and audit trail for all transactional email.
    """
    __tablename__ = "email_records"

    id = db.Column(db.Integer, primary_key=True)
    # Business operation identity (idempotency key)
    business_event_id = db.Column(db.String(128), nullable=False, index=True)
    notification_type = db.Column(db.String(64), nullable=False)
    # Recipient
    recipient = db.Column(db.String(255), nullable=False, index=True)
    # Content (for audit/reconciliation)
    subject = db.Column(db.String(255), nullable=False)
    body_hash = db.Column(db.String(64), nullable=False)
    # Category
    category = db.Column(db.String(32), nullable=False, default="operational")
    # Provider
    provider = db.Column(db.String(32), nullable=False, default="resend")
    provider_message_id = db.Column(db.String(128), nullable=True, index=True)
    # Lifecycle
    state = db.Column(db.String(32), nullable=False, default=EmailDeliveryState.REQUESTED.value)
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    max_retries = db.Column(db.Integer, nullable=False, default=2)
    last_error = db.Column(db.Text, nullable=True)
    # Provenance
    tenant_id = db.Column(db.Integer, nullable=True, index=True)
    identity_id = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    # Webhook verification
    webhook_verified_at = db.Column(db.DateTime, nullable=True)
    webhook_event_id = db.Column(db.String(128), nullable=True)

    def set_state(self, new_state: EmailDeliveryState, error: str = None):
        self.state = new_state.value
        if error:
            self.last_error = error
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "business_event_id": self.business_event_id,
            "notification_type": self.notification_type,
            "recipient": self.recipient,
            "subject": self.subject,
            "category": self.category,
            "provider": self.provider,
            "provider_message_id": self.provider_message_id,
            "state": self.state,
            "retry_count": self.retry_count,
            "last_error": self.last_error,
            "tenant_id": self.tenant_id,
            "identity_id": self.identity_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }