"""SHUNYA Execution — thin persistence layer.

The canonical execution authority is:

    runtime/entry.py → execution_engine → Object / Execution / ExecutionLog

This module provides Outcome persistence for backward compatibility
plus the new ExecutionRun / TaskLifecycle models for structured
execution tracking.

All existing APIs remain valid as thin wrappers around canonical state.
"""
from typing import Optional

from app import db

import logging
logger = logging.getLogger(__name__)

# ── Outcome Model ──
from app.execution.models import Outcome

# ── Execution Runtime (thin persistence wrapper) ──
from app.execution.runtime import OutcomeRuntime, get_runtime

# ── Backward-compatible state constants (no lifecycle) ──
from app.execution.constants import ExecState, ObligationState

# ── Core Execution Models (new) ──
from app.execution.core_models import ExecutionRun, ExecutionStateTransition

# ── Task Lifecycle Model (new) ──
from app.execution.task_lifecycle import TaskLifecycle

# ── Execution Run Service (new) ──
from app.execution.run_service import ExecutionRunService, get_run_service

# ── Backward-compatible execution service (thin wrapper) ──


def _dispatch_execution(
    outcome,
    identity_id: str,
    intention: str,
    run=None,
    commitment_type: str = "",
    commitment_id: str = "",
    source: str = "business_execution",
) -> dict:
    """Dispatch an outcome through the canonical execution authority.

    runtime/entry.process_event is the ONLY execution entry point. This helper
    persists the truthful result:

    - success → outcome state stage='executed' (+ trace id); run marked complete.
    - unavailable/failure → outcome state stage='queued' with the recorded error.
      The caller still succeeds (the outcome IS registered) but never claims
      'activated'-implies-running — the status is explicitly 'queued'.
    """
    from app.runtime.entry import process_event as _process_event

    try:
        exec_result = _process_event(
            "business_execution",
            {
                "id": outcome.outcome_id,
                "intention": intention,
                "identity_id": identity_id,
                "commitment_type": commitment_type,
                "commitment_id": commitment_id,
            },
            source=source,
        )
        state = dict(outcome.state or {})
        state.update({
            "stage": "executed",
            "execution_status": exec_result.get("status", "completed"),
            "execution_trace_id": exec_result.get("decision_trace_id"),
            "execution_result": {
                "status": exec_result.get("status"),
                "entity_id": exec_result.get("entity_id"),
                "decision_trace_id": exec_result.get("decision_trace_id"),
            },
        })
        outcome.state = state
        if run is not None:
            try:
                run.complete(
                    result=exec_result.get("execution") or {},
                    result_summary=f"Dispatched via canonical authority: {exec_result.get('status')}",
                )
            except Exception:
                logger.warning("ExecutionRun %s could not be marked complete", run.execution_id, exc_info=True)
        db.session.commit()
        logger.info("Execution %s dispatched via canonical authority", outcome.outcome_id)
        return {
            "status": "executed",
            "execution_status": exec_result.get("status"),
            "decision_trace_id": exec_result.get("decision_trace_id"),
        }
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        state = dict(outcome.state or {})
        state.update({
            "stage": "queued",
            "queue_note": (
                "Execution authority unavailable at dispatch time — outcome is "
                f"registered and will run when available. ({e})"
            ),
            "last_error": str(e),
        })
        outcome.state = state
        db.session.commit()
        logger.warning("Execution authority unavailable for %s — outcome queued: %s", outcome.outcome_id, e)
        return {"status": "queued", "error": str(e)}


class ExecutionService:
    """Backward-compatible wrapper — delegates to canonical execution_engine.
    
    This is NOT an independent execution authority. All execution goes
    through the canonical path: runtime/entry.py → execution_engine.
    """
    def __init__(self):
        self._runtime = get_runtime()

    def activate(self, commitment_type: str = "", commitment_id: str = "",
                 tenant_id: int | None = None, idempotency_key: Optional[str] = None):
        """Record an execution activation.

        Idempotent ONLY when an explicit idempotency_key is provided:
          same idempotency_key → same outcome_id (idempotent replay).

        When no explicit key is given, each call creates a DISTINCT execution
        via a UUID-based execution-request identity. This allows legitimate
        future executions of the same commitment.

        DB-level unique constraint on idempotency_key prevents TOCTOU races.
        """
        from app.execution.models import IdempotencyRecord
        from sqlalchemy.exc import IntegrityError
        import uuid

        # When no explicit idempotency_key, generate a UUID-based execution-request
        # identity so each call creates a distinct execution for the same commitment.
        effective_key = idempotency_key or f"req_{uuid.uuid4().hex[:16]}"

        # Fast path: check for existing idempotency record
        existing = IdempotencyRecord.query.filter_by(
            idempotency_key=effective_key,
        ).first()
        if existing:
            return {"success": True, "exec_id": existing.outcome_id, "idempotent": True}

        intention = f"Execute {commitment_type} {commitment_id}"
        outcome = self._runtime.accept(
            identity_id=str(tenant_id),
            intention=intention,
        )

        # Persist idempotency binding (DB unique constraint prevents races)
        try:
            idem = IdempotencyRecord(
                idempotency_key=effective_key,
                outcome_id=outcome.outcome_id,
                identity_id=str(tenant_id),
                commitment_type=commitment_type,
                commitment_id=commitment_id,
            )
            db.session.add(idem)
            db.session.commit()
        except IntegrityError:
            # Race lost — another request committed first
            db.session.rollback()
            existing = IdempotencyRecord.query.filter_by(
                idempotency_key=effective_key,
            ).first()
            if existing:
                return {"success": True, "exec_id": existing.outcome_id, "idempotent": True}
            raise

        # Dispatch through the canonical execution authority. The returned
        # status is truthful: 'executed' when the authority ran it, 'queued'
        # when the authority was unavailable (the outcome is registered and
        # will run when available) — never a claim of running that didn't happen.
        dispatch = _dispatch_execution(
            outcome,
            identity_id=str(tenant_id),
            intention=intention,
            commitment_type=commitment_type,
            commitment_id=commitment_id,
            source="execution_service",
        )
        return {
            "success": True,
            "exec_id": outcome.outcome_id,
            "idempotent": False,
            "status": dispatch["status"],
        }

    def inspect(self, execution_id: str = "", tenant_id: int = 1):
        """Inspect execution status — truthful, from the persisted outcome state."""
        outcome = self._runtime.get(execution_id)
        if outcome:
            stage = (outcome.state or {}).get("stage", "accepted")
            status = {
                "executed": "completed",
                "queued": "queued",
                "failed": "failed",
                "accepted": "accepted",
            }.get(stage, stage)
            return {"status": status, "exec_id": execution_id}
        return {"status": "not_found", "exec_id": execution_id}

    def get_execution(self, commitment_id: str = "", tenant_id: int = 1):
        """Get full execution details."""
        outcome = self._runtime.get(commitment_id)
        if outcome:
            return {"execution": outcome.to_dict()}
        return {"execution": None}

    def add_run(self, execution_id: str = "", tenant_id: int = 1):
        """Add a run to an execution (no-op — state-driven)."""
        return {"success": True}


class BusinessExecutionInstance:
    """Backward-compatible wrapper — delegates to canonical execution.

    Now also creates an ExecutionRun on activate() for structured
    execution tracking alongside the legacy Outcome.
    """
    def __init__(self):
        self._runtime = get_runtime()
        self._run_service = get_run_service()

    def activate(self, commitment_type: str = "", commitment_id: str = "",
                 tenant_id: int | None = None, idempotency_key: Optional[str] = None,
                 organization_id: Optional[int] = None,
                 identity_id: Optional[int] = None,
                 intent: Optional[str] = None):
        """Record an execution activation.

        Creates both an Outcome (legacy) and an ExecutionRun (new).
        The ExecutionRun links to the outcome via outcome_id.

        Idempotent ONLY when an explicit idempotency_key is provided:
          same idempotency_key → same outcome_id (idempotent replay).

        When no explicit key is given, each call creates a DISTINCT execution
        via a UUID-based execution-request identity. This allows legitimate
        future executions of the same commitment.

        DB-level unique constraint on idempotency_key prevents TOCTOU races.
        """
        from app.execution.models import IdempotencyRecord
        from sqlalchemy.exc import IntegrityError
        import uuid

        # When no explicit idempotency_key, generate a UUID-based execution-request
        # identity so each call creates a distinct execution for the same commitment.
        effective_key = idempotency_key or f"req_{uuid.uuid4().hex[:16]}"

        # Fast path: check for existing idempotency record
        existing = IdempotencyRecord.query.filter_by(
            idempotency_key=effective_key,
        ).first()
        if existing:
            return {"success": True, "exec_id": existing.outcome_id, "idempotent": True}
        intention = intent or f"Execute {commitment_type} {commitment_id}"
        outcome = self._runtime.accept(
            identity_id=str(tenant_id),
            intention=intention,
        )

        # Create an ExecutionRun alongside the Outcome
        effective_org_id = organization_id or tenant_id
        effective_identity_id = identity_id or tenant_id
        try:
            run = self._run_service.create_run(
                organization_id=effective_org_id,
                identity_id=effective_identity_id,
                intent=intention,
                run_type="execution",
                source="system",
                outcome_id=outcome.outcome_id,
                commitment_id=commitment_id,
                commitment_type=commitment_type,
            )
        except Exception:
            # Non-fatal: execution run creation should not block the outcome
            logger.warning("Failed to create ExecutionRun for outcome %s", outcome.outcome_id, exc_info=True)
            run = None

        # Persist idempotency binding (DB unique constraint prevents races)
        try:
            idem = IdempotencyRecord(
                idempotency_key=effective_key,
                outcome_id=outcome.outcome_id,
                identity_id=str(tenant_id),
                commitment_type=commitment_type,
                commitment_id=commitment_id,
            )
            db.session.add(idem)
            db.session.commit()
        except IntegrityError:
            # Race lost — another request committed first
            db.session.rollback()
            existing = IdempotencyRecord.query.filter_by(
                idempotency_key=effective_key,
            ).first()
            if existing:
                return {"success": True, "exec_id": existing.outcome_id, "idempotent": True}
            raise

        result = {"success": True, "exec_id": outcome.outcome_id, "idempotent": False}
        if run:
            result["execution_run_id"] = run.execution_id

        # Dispatch through the canonical execution authority. The returned
        # status is truthful: 'executed' when the authority ran it, 'queued'
        # when the authority was unavailable (the outcome is registered and
        # will run when available) — never a claim of running that didn't happen.
        dispatch = _dispatch_execution(
            outcome,
            identity_id=str(effective_identity_id),
            intention=intention,
            run=run,
            commitment_type=commitment_type,
            commitment_id=commitment_id,
            source="business_execution_instance",
        )
        result["status"] = dispatch["status"]
        return result

    def inspect(self, execution_id: str = "", tenant_id: int = 1):
        """Inspect execution status — truthful, from the persisted outcome state."""
        outcome = self._runtime.get(execution_id)
        if outcome:
            stage = (outcome.state or {}).get("stage", "accepted")
            status = {
                "executed": "completed",
                "queued": "queued",
                "failed": "failed",
                "accepted": "accepted",
            }.get(stage, stage)
            return {"status": status, "exec_id": execution_id}
        return {"status": "not_found", "exec_id": execution_id}

    def get(self, outcome_id: str) -> Optional[Outcome]:
        """Get an Outcome by ID (delegates to OutcomeRuntime)."""
        return self._runtime.get(outcome_id)

class ExecutionObligation:
    """Backward-compatible obligation class."""
    def __init__(self, obligation_id: str = "", description: str = "", deadline=None):
        self.obligation_id = obligation_id
        self.description = description
        self.deadline = deadline
        self.state = ObligationState.PENDING


class ExecutionException(Exception):
    """Exception during execution."""
    pass


# ── Public API ──

__all__ = [
    "Outcome", "OutcomeRuntime", "get_runtime",
    "ExecState", "ObligationState",
    "ExecutionService", "BusinessExecutionInstance",
    "ExecutionObligation", "ExecutionException",
    # New execution models
    "ExecutionRun", "ExecutionStateTransition",
    "TaskLifecycle",
    # New service
    "ExecutionRunService", "get_run_service",
]