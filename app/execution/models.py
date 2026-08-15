"""SHUNYA Outcome Model — thin persistence wrapper around canonical execution state.

Outcome is a compatibility/persistence layer. It records the user's original
intention and the current execution state. All execution history is represented
through canonical ExecutionLog.

This is NOT an execution engine. It is a thin state wrapper.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON
from app import db


class Outcome(db.Model):
    """Outcome record — persists user intention and current execution state.

    This is a thin state wrapper, NOT an execution engine.
    Execution history is in canonical ExecutionLog.
    """
    __tablename__ = "sh_outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    outcome_id = Column(String(12), unique=True, nullable=False, index=True)
    identity_id = Column(String(64), nullable=False, index=True)

    # The original user intention
    intention = Column(Text, nullable=False)

    # Opaque current state — no predefined lifecycle progression
    # Represents the current truth: Execution = f(State, Intent, Evidence, Time)
    state = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "outcome_id": self.outcome_id,
            "intention": self.intention,
            "state": self.state or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Outcome {self.outcome_id}>"