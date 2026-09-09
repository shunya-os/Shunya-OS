"""Execution Run Service — service for creating and managing ExecutionRuns and TaskLifecycle.

Provides a clean service layer over the core execution models.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app import db
from app.execution.core_models import ExecutionRun, ExecutionStateTransition
from app.execution.task_lifecycle import TaskLifecycle

logger = logging.getLogger(__name__)


class RunServiceError(Exception):
    """Raised when a run-service operation cannot be completed."""


class ExecutionRunService:
    """Service for creating and managing ExecutionRuns and TaskLifecycle."""

    # ── Execution Run CRUD ─────────────────────────────────────────────────

    def create_run(
        self,
        organization_id: int,
        identity_id: Optional[int],
        intent: str,
        run_type: str = "task",
        source: str = "user",
        **kwargs,
    ) -> ExecutionRun:
        """Create a new ExecutionRun and persist it to the database."""
        if not organization_id or organization_id < 1:
            raise ValueError(f"Invalid organization_id: {organization_id}")
        execution_id = kwargs.pop("execution_id", None) or f"exec_{uuid.uuid4().hex[:12]}"
        run = ExecutionRun(
            execution_id=execution_id,
            organization_id=organization_id,
            identity_id=identity_id,
            intent=intent,
            run_type=run_type,
            source=source,
            **kwargs,
        )
        db.session.add(run)
        db.session.commit()
        logger.info(
            "ExecutionRun %s created (org=%s, type=%s)",
            execution_id, organization_id, run_type,
        )
        return run

    def get_run(self, execution_id: str) -> Optional[ExecutionRun]:
        """Get an ExecutionRun by its execution_id."""
        return ExecutionRun.query.filter_by(execution_id=execution_id).first()

    def get_runs(
        self,
        organization_id: int,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> list:
        """Get recent ExecutionRuns for an organization, optionally filtered by status."""
        query = ExecutionRun.query.filter_by(organization_id=organization_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(ExecutionRun.created_at.desc()).limit(limit).all()

    def get_active_runs(self, organization_id: int) -> list:
        """Get all active (queued or in_progress) runs for an organization."""
        return (
            ExecutionRun.query
            .filter_by(organization_id=organization_id)
            .filter(ExecutionRun.status.in_(["queued", "in_progress"]))
            .order_by(ExecutionRun.created_at.desc())
            .all()
        )

    # ── Execution Run Lifecycle ────────────────────────────────────────────

    def transition(self, execution_id: str, new_phase: str, reason: str = "") -> ExecutionRun:
        """Record a phase transition on an existing ExecutionRun."""
        run = self.get_run(execution_id)
        if not run:
            raise ValueError(f"ExecutionRun {execution_id} not found")
        run.transition_to(new_phase, reason=reason)
        db.session.commit()
        return run

    def complete(self, execution_id: str, result=None, summary=None) -> ExecutionRun:
        """Mark an ExecutionRun as completed."""
        run = self.get_run(execution_id)
        if not run:
            raise ValueError(f"ExecutionRun {execution_id} not found")
        run.complete(result=result, result_summary=summary)
        db.session.commit()
        return run

    def fail(self, execution_id: str, error=None) -> ExecutionRun:
        """Mark an ExecutionRun as failed."""
        run = self.get_run(execution_id)
        if not run:
            raise ValueError(f"ExecutionRun {execution_id} not found")
        run.fail(error=error)
        db.session.commit()
        return run

    # ── Task Lifecycle ─────────────────────────────────────────────────────

    def create_task(
        self,
        organization_id: int,
        identity_id: Optional[int],
        title: str,
        description: str = "",
        execution_run_id: Optional[str] = None,
    ) -> TaskLifecycle:
        """Create a new TaskLifecycle record."""
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        task = TaskLifecycle(
            task_id=task_id,
            organization_id=organization_id,
            identity_id=identity_id,
            execution_run_id=execution_run_id,
            title=title,
            description=description,
        )
        db.session.add(task)
        db.session.commit()
        logger.info("TaskLifecycle %s created: %s", task_id, title[:60])
        return task

    def get_task(self, task_id: str) -> Optional[TaskLifecycle]:
        """Get a TaskLifecycle by its task_id."""
        return TaskLifecycle.query.filter_by(task_id=task_id).first()

    def get_recent_tasks(self, organization_id: int, limit: int = 20) -> list:
        """Get the most recent tasks for an organization."""
        return (
            TaskLifecycle.query
            .filter_by(organization_id=organization_id)
            .order_by(TaskLifecycle.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_tasks_needing_attention(self, organization_id: int) -> list:
        """Get tasks that need user attention (blocked or failed)."""
        return (
            TaskLifecycle.query
            .filter_by(organization_id=organization_id)
            .filter(TaskLifecycle.status.in_(["blocked", "failed"]))
            .order_by(TaskLifecycle.created_at.desc())
            .all()
        )

    def get_active_tasks(self, organization_id: int) -> list:
        """Get active (in_progress) tasks for an organization."""
        return (
            TaskLifecycle.query
            .filter_by(organization_id=organization_id)
            .filter(TaskLifecycle.status.in_(["in_progress", "pending"]))
            .order_by(TaskLifecycle.created_at.desc())
            .all()
        )


# ── Singleton ──────────────────────────────────────────────────────────────

_run_service: Optional[ExecutionRunService] = None


def get_run_service() -> ExecutionRunService:
    """Get or create the singleton ExecutionRunService."""
    global _run_service
    if _run_service is None:
        _run_service = ExecutionRunService()
    return _run_service