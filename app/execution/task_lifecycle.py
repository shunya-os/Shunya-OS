"""SHUNYA Task Lifecycle model.

User-facing task tracking with phase history. Links to the canonical
ExecutionRun via execution_run_id.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey, Index

from app import db

logger = logging.getLogger(__name__)


def _elapsed_seconds(started_at, completed_at):
    """Compute elapsed seconds, tolerating naive vs aware datetime mixing."""
    if not started_at or not completed_at:
        return None
    start = started_at
    end = completed_at
    if start.tzinfo and not end.tzinfo:
        end = end.replace(tzinfo=timezone.utc)
    elif end.tzinfo and not start.tzinfo:
        start = start.replace(tzinfo=timezone.utc)
    return (end - start).total_seconds()


class TaskLifecycle(db.Model):
    """User-facing task lifecycle record.

    Tracks a task from pending → in_progress → completed/failed/cancelled,
    with a phase history JSON for user-facing display.
    """
    __tablename__ = "task_lifecycle"

    __table_args__ = (
        Index("ix_task_lifecycle_org_status", "organization_id", "status"),
        Index("ix_task_lifecycle_org_created", "organization_id", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    task_id = Column(String(36), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    identity_id = Column(Integer, ForeignKey("shunya_identities.id"), nullable=True)
    execution_run_id = Column(String(36), ForeignKey("execution_runs.execution_id"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    # User-facing status
    status = Column(String(30), default="pending", index=True)  # pending, in_progress, completed, failed, cancelled, blocked
    # User-facing phases with timestamps
    current_phase = Column(String(50), nullable=True)
    phase_history = Column(JSON, default=list)  # [{"phase": "...", "started_at": "...", "duration": 0.0}, ...]

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Result
    result_summary = Column(Text, nullable=True)
    result_detail = Column(JSON, nullable=True)
    outcome = Column(String(30), nullable=True)  # completed, partial, failed, cancelled

    # Next action
    next_action = Column(String(255), nullable=True)
    next_action_url = Column(String(255), nullable=True)

    # ── Lifecycle Methods ──────────────────────────────────────────────────

    def start(self):
        """Mark task as in_progress and record the start timestamp."""
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc)
        self.status = "in_progress"
        logger.info("TaskLifecycle %s started", self.task_id)

    def complete(self, result_summary=None, result_detail=None, outcome="completed"):
        """Mark task as completed with duration."""
        self.status = "completed"
        self.outcome = outcome
        self.completed_at = datetime.now(timezone.utc)
        if result_summary:
            self.result_summary = result_summary
        if result_detail is not None:
            self.result_detail = result_detail
        if self.started_at:
            self.duration_seconds = _elapsed_seconds(self.started_at, self.completed_at)
        logger.info("TaskLifecycle %s completed", self.task_id)

    def fail(self, result_summary=None, outcome="failed"):
        """Mark task as failed."""
        self.status = "failed"
        self.outcome = outcome
        self.completed_at = datetime.now(timezone.utc)
        if result_summary:
            self.result_summary = result_summary
        if self.started_at:
            self.duration_seconds = _elapsed_seconds(self.started_at, self.completed_at)
        logger.warning("TaskLifecycle %s failed", self.task_id)

    def enter_phase(self, phase: str):
        """Record a phase entry in the phase_history JSON."""
        history = list(self.phase_history or [])
        history.append({
            "phase": phase,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "duration": 0.0,
        })
        self.phase_history = history
        self.current_phase = phase

    def set_next_action(self, action: str, url: str = ""):
        """Set the next action a user must take."""
        self.next_action = action
        self.next_action_url = url
        self.status = "blocked"

    # ── Serialization ──────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "organization_id": self.organization_id,
            "identity_id": self.identity_id,
            "execution_run_id": self.execution_run_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "current_phase": self.current_phase,
            "phase_history": self.phase_history or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "result_summary": self.result_summary,
            "result_detail": self.result_detail,
            "outcome": self.outcome,
            "next_action": self.next_action,
            "next_action_url": self.next_action_url,
        }

    def __repr__(self) -> str:
        return f"<TaskLifecycle {self.task_id} status={self.status}>"