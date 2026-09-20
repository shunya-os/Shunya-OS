"""AttentionItem model — persistent operating intelligence items.

Lifecycle: SIGNAL → ATTENTION ITEM → PERSIST → DISPLAY → EXPLAIN → DISMISS/RESOLVE → AUDIT → REFRESH → RESTART → RECOVER
"""
from datetime import datetime, timezone
from enum import Enum as PyEnum
from app import db


class AttentionState(str, PyEnum):
    ACTIVE = "active"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class AttentionSource(str, PyEnum):
    INTENTION_ENGINE = "intention.engine"
    SIGNAL = "signal"
    AI = "ai"


class AttentionItem(db.Model):
    """A persistent attention item — what deserves the user's focus right now.

    Every item retains full provenance: identity, organization, workspace, source,
    related object, reason, priority, confidence, lifecycle state, timestamps,
    resolution/dismissal actor, and generation provenance.
    """
    __tablename__ = "attention_items"
    __table_args__ = (
        db.Index("ix_attention_org_state", "organization_id", "state"),
        db.Index("ix_attention_identity", "identity_id", "state"),
        db.Index("ix_attention_workspace", "workspace_id", "state"),
        db.Index("ix_attention_source", "source"),
        db.Index("ix_attention_created", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    workspace_id = db.Column(db.String(64), nullable=True, index=True)

    source = db.Column(db.String(32), nullable=False,
                       default=AttentionSource.INTENTION_ENGINE.value)
    related_object_type = db.Column(db.String(64), nullable=True)
    related_object_id = db.Column(db.String(128), nullable=True)

    reason = db.Column(db.Text, nullable=False, default="")
    priority = db.Column(db.Integer, nullable=False, default=3)
    confidence = db.Column(db.Float, nullable=True)

    state = db.Column(db.String(20), nullable=False, default=AttentionState.ACTIVE.value)

    dismissed_at = db.Column(db.DateTime, nullable=True)
    dismissed_by = db.Column(db.String(64), nullable=True)

    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.String(64), nullable=True)

    provenance = db.Column(db.JSON, default=dict)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "source": self.source,
            "related_object_type": self.related_object_type,
            "related_object_id": self.related_object_id,
            "reason": self.reason,
            "priority": self.priority,
            "confidence": self.confidence,
            "state": self.state,
            "dismissed_at": self.dismissed_at.isoformat() if self.dismissed_at else None,
            "dismissed_by": self.dismissed_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "provenance": self.provenance if self.provenance else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }