"""AIExecutionRecord — persistent observability model for AI execution traces.

G3 Phase 7.2.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app import db


class AIExecutionRecord(db.Model):
    """Records every AI execution for observability and audit.

    Each row tracks one ask() call through the intelligence pipeline:
    request metadata, classification, provider latency, and outcome.
    """

    __tablename__ = "ai_execution_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_id = db.Column(db.String(64), nullable=False, index=True)
    session_id = db.Column(db.String(128), nullable=True, index=True)
    query = db.Column(db.Text, nullable=False)
    action_class = db.Column(db.String(64), nullable=True)
    provider = db.Column(db.String(64), nullable=True)
    model = db.Column(db.String(128), nullable=True)
    latency_ms = db.Column(db.Float, nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    evidence_count = db.Column(db.Integer, nullable=True, default=0)
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "query": self.query[:200] if self.query else "",
            "action_class": self.action_class,
            "provider": self.provider,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }