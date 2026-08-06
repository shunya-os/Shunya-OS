"""
SHUNYA Outcome Model — persists outcomes across restarts.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, JSON
from app import db


class Outcome(db.Model):
    """Persistent outcome record. Survives server restarts, provider outages, browser closes."""
    __tablename__ = "sh_outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    outcome_id = Column(String(12), unique=True, nullable=False, index=True)
    identity_id = Column(String(64), nullable=False, index=True)

    # The original user intention
    intention = Column(Text, nullable=False)

    # Current stage: accepted, queued, executing, monitoring, completed, failed
    stage = Column(String(20), nullable=False, default="accepted")

    # Progress description (human-readable)
    progress = Column(String(200), nullable=False, default="Received")

    # Expected completion (seconds, with 30% buffer)
    expected_completion_seconds = Column(Integer, default=30)

    # Actual completion time (seconds)
    actual_completion_seconds = Column(Integer, nullable=True)

    # Recovery history: list of {level, attempt, strategy, success, error, timestamp}
    recovery_history = Column(JSON, default=list)

    # Final summary: {created, modified, relationships, monitoring, manual_decisions}
    final_summary = Column(JSON, nullable=True)

    # Steps executed: list of {action, type, success, result}
    steps = Column(JSON, default=list)

    # Error tracking
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "outcome_id": self.outcome_id,
            "intention": self.intention,
            "stage": self.stage,
            "progress": self.progress,
            "expected_completion_seconds": self.expected_completion_seconds,
            "actual_completion_seconds": self.actual_completion_seconds,
            "recovery_history": self.recovery_history or [],
            "final_summary": self.final_summary,
            "steps": self.steps or [],
            "last_error": self.last_error,
            "error_count": self.error_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Outcome {self.outcome_id}: {self.stage}>"