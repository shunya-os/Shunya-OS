"""Feedback Model — user feedback on recommendations.

Phase 5.4: User feedback signals for accepted/rejected recommendations.
Stores feedback on proactive signals so the learning system can improve.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app import db


class Feedback(db.Model):
    """User feedback on a recommendation, signal, or action.

    Captures whether the user accepted or rejected a proactive signal,
    along with an optional comment for qualitative context.
    """

    __tablename__ = "feedback_signals"

    id = db.Column(db.Integer, primary_key=True)
    signal_id = db.Column(db.String(128), nullable=False, index=True)
    accepted = db.Column(db.Boolean, nullable=False)
    comment = db.Column(db.Text, default="")
    identity_id = db.Column(db.String(64), default="", index=True)
    tenant_id = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "signal_id": self.signal_id,
            "accepted": self.accepted,
            "comment": self.comment,
            "identity_id": self.identity_id,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }