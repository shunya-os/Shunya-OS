"""SHUNYA Outcome Model — thin persistence wrapper around canonical execution state.

Outcome is a compatibility/persistence layer. It records the user's original
intention and the current execution state. All execution history is represented
through canonical ExecutionLog.

This is NOT an execution engine. It is a thin state wrapper.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON
from app import db


class IdempotencyRecord(db.Model):
    """Execution idempotency — maps idempotency_key → execution outcome_id.

    This is the canonical idempotency enforcer for execution requests.
    The DB-level unique constraint on idempotency_key provides atomic
    check-then-create semantics, safe against concurrent submissions.

    The same idempotency_key always returns the same outcome_id.
    Different keys for the same commitment create distinct executions.
    """
    __tablename__ = "execution_idempotency"

    id = Column(Integer, primary_key=True, autoincrement=True)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    outcome_id = Column(String(12), nullable=False)
    identity_id = Column(String(64), nullable=False)
    commitment_type = Column(String(64), default="")
    commitment_id = Column(String(64), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "idempotency_key": self.idempotency_key,
            "outcome_id": self.outcome_id,
            "identity_id": self.identity_id,
            "commitment_type": self.commitment_type,
            "commitment_id": self.commitment_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


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