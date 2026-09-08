"""SHUNYA Execution Run and State Transition models.

Canonical execution tracking with lifecycle state machine.
NOT an execution engine — records state, does not drive progression.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, JSON, Float, Boolean,
    ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from app import db

logger = logging.getLogger(__name__)


def _elapsed_seconds(started_at, completed_at):
    """Compute elapsed seconds, tolerating naive vs aware datetime mixing.

    PostgreSQL returns naive datetimes for `timestamp` columns while the
    model defaults produce aware datetimes — normalize before subtracting.
    """
    if not started_at or not completed_at:
        return None
    start = started_at
    end = completed_at
    if start.tzinfo and not end.tzinfo:
        end = end.replace(tzinfo=timezone.utc)
    elif end.tzinfo and not start.tzinfo:
        start = start.replace(tzinfo=timezone.utc)
    return (end - start).total_seconds()


class ExecutionRun(db.Model):
    """Canonical execution run record.

    Tracks a single execution from queue → in_progress → completed/failed.
    NOT an execution engine — it records state, it does not drive progression.
    """
    __tablename__ = "execution_runs"

    __table_args__ = (
        Index("ix_execution_runs_org_status", "organization_id", "status"),
        Index("ix_execution_runs_org_created", "organization_id", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    execution_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    identity_id = Column(Integer, ForeignKey("shunya_identities.id"), nullable=True)
    workspace_id = Column(Integer, nullable=True)

    # The kind of execution
    run_type = Column(String(50), nullable=False, default="task")  # task, analysis, execution, intelligence

    # Current status (the lifecycle state machine)
    status = Column(String(30), nullable=False, default="queued", index=True)

    # Current phase for user-facing display
    current_phase = Column(String(50), nullable=True)

    # Intent
    intent = Column(Text, nullable=False)
    intent_summary = Column(String(255), nullable=True)

    # Context tracking — what sources were used
    used_company_data = Column(Boolean, default=False)
    used_internet_data = Column(Boolean, default=False)
    used_ai = Column(Boolean, default=False)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Result
    result = Column(JSON, nullable=True)
    result_summary = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)

    # Correlation
    correlation_id = Column(String(36), nullable=True, index=True)
    parent_run_id = Column(String(36), nullable=True, index=True)

    # Source
    source = Column(String(30), default="user")  # user, scheduled, system

    # Link to outcome
    outcome_id = Column(String(12), nullable=True, index=True)

    # Link to commitment
    commitment_id = Column(String(64), nullable=True, index=True)
    commitment_type = Column(String(64), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────

    transitions = relationship(
        "ExecutionStateTransition",
        primaryjoin="ExecutionRun.execution_id == ExecutionStateTransition.execution_id",
        foreign_keys="ExecutionStateTransition.execution_id",
        back_populates="run",
        lazy="dynamic",
    )

    # ── Lifecycle Methods ──────────────────────────────────────────────────

    def start(self):
        """Mark this run as in_progress with a started_at timestamp."""
        self.status = "in_progress"
        self.started_at = datetime.now(timezone.utc)
        logger.info("ExecutionRun %s started", self.execution_id)

    def complete(self, result=None, result_summary=None):
        """Mark this run as completed with duration."""
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)
        self.result = result
        self.result_summary = result_summary or self.result_summary
        self.duration_seconds = _elapsed_seconds(self.started_at, self.completed_at)
        logger.info("ExecutionRun %s completed in %.2fs", self.execution_id, self.duration_seconds or 0)

    def fail(self, error=None):
        """Mark this run as failed with an error message."""
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc)
        if error:
            self.error = error
            self.error_count = (self.error_count or 0) + 1
        self.duration_seconds = _elapsed_seconds(self.started_at, self.completed_at)
        logger.warning("ExecutionRun %s failed: %s", self.execution_id, error or "unknown error")

    def transition_to(self, phase: str, reason: str = ""):
        """Record a phase transition for this run.

        Records the transition in the ExecutionStateTransition table
        and updates the current_phase on the run.
        """
        state_before = self.current_phase or self.status
        self.current_phase = phase
        transition = ExecutionStateTransition(
            execution_id=self.execution_id,
            state_before=state_before,
            state_after=phase,
            reason=reason,
        )
        db.session.add(transition)
        logger.info("ExecutionRun %s phase: %s → %s (%s)", self.execution_id, state_before, phase, reason)

    def record_source(self, company=False, internet=False, ai=False):
        """Record which data sources were used in this execution."""
        if company:
            self.used_company_data = True
        if internet:
            self.used_internet_data = True
        if ai:
            self.used_ai = True

    # ── Serialization ──────────────────────────────────────────────────────

    def to_dict(self, include_transitions: bool = False) -> dict:
        data = {
            "execution_id": self.execution_id,
            "organization_id": self.organization_id,
            "identity_id": self.identity_id,
            "workspace_id": self.workspace_id,
            "run_type": self.run_type,
            "status": self.status,
            "current_phase": self.current_phase,
            "intent": self.intent,
            "intent_summary": self.intent_summary,
            "used_company_data": self.used_company_data,
            "used_internet_data": self.used_internet_data,
            "used_ai": self.used_ai,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "result_summary": self.result_summary,
            "error": self.error,
            "error_count": self.error_count,
            "correlation_id": self.correlation_id,
            "parent_run_id": self.parent_run_id,
            "source": self.source,
            "outcome_id": self.outcome_id,
            "commitment_id": self.commitment_id,
            "commitment_type": self.commitment_type,
        }
        if include_transitions:
            data["transitions"] = [
                t.to_dict() for t in self.transitions.order_by(ExecutionStateTransition.id.asc()).all()
            ]
        return data

    def __repr__(self) -> str:
        return f"<ExecutionRun {self.execution_id} status={self.status}>"


class ExecutionStateTransition(db.Model):
    """Audit trail of state/phase transitions for an ExecutionRun.

    Every call to ExecutionRun.transition_to() creates one of these.
    """
    __tablename__ = "execution_state_transitions"

    __table_args__ = (
        Index("ix_execution_state_transitions_exec_phase", "execution_id", "state_after"),
    )

    id = Column(Integer, primary_key=True)
    execution_id = Column(String(36), ForeignKey("execution_runs.execution_id"), nullable=False, index=True)
    state_before = Column(String(50), nullable=False)
    state_after = Column(String(50), nullable=False)
    transitioned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    actor = Column(String(64), default="system")
    reason = Column(Text, default="")
    correlation_id = Column(String(36), nullable=True)
    extra_metadata = Column(JSON, default=dict)

    # ── Relationships ──────────────────────────────────────────────────────

    run = relationship(
        "ExecutionRun",
        primaryjoin="ExecutionStateTransition.execution_id == ExecutionRun.execution_id",
        foreign_keys="ExecutionStateTransition.execution_id",
        back_populates="transitions",
    )

    # ── Serialization ──────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "transitioned_at": self.transitioned_at.isoformat() if self.transitioned_at else None,
            "actor": self.actor,
            "reason": self.reason,
            "correlation_id": self.correlation_id,
            "metadata": self.extra_metadata or {},
        }

    def __repr__(self) -> str:
        return f"<ExecutionStateTransition {self.state_before}→{self.state_after}>"