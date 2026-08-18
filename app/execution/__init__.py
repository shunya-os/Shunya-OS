"""SHUNYA Execution — thin persistence layer.

The canonical execution authority is:

    runtime/entry.py → execution_engine → Object / Execution / ExecutionLog

This module provides Outcome persistence for backward compatibility.
It is NOT an execution engine. No step-based execution, no lifecycle
progression, no workflow semantics.

All existing APIs remain valid as thin wrappers around canonical state.
"""
from typing import Optional

from app import db

# ── Outcome Model ──
from app.execution.models import Outcome

# ── Execution Runtime (thin persistence wrapper) ──
from app.execution.runtime import OutcomeRuntime, get_runtime

# ── Backward-compatible state constants (no lifecycle) ──
from app.execution.constants import ExecState, ObligationState

# ── Backward-compatible execution service (thin wrapper) ──


class ExecutionService:
    """Backward-compatible wrapper — delegates to canonical execution_engine.
    
    This is NOT an independent execution authority. All execution goes
    through the canonical path: runtime/entry.py → execution_engine.
    """
    def __init__(self):
        self._runtime = get_runtime()

    def activate(self, commitment_type: str = "", commitment_id: str = "",
                 tenant_id: int = 1, idempotency_key: Optional[str] = None):
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

        return {"success": True, "exec_id": outcome.outcome_id, "idempotent": False}

    def inspect(self, execution_id: str = "", tenant_id: int = 1):
        """Inspect execution status."""
        outcome = self._runtime.get(execution_id)
        if outcome:
            return {"status": "completed", "exec_id": execution_id}
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
    
    This is NOT an execution engine. Thin wrapper only.
    """
    def __init__(self):
        self._runtime = get_runtime()

    def activate(self, commitment_type: str = "", commitment_id: str = "",
                 tenant_id: int = 1, idempotency_key: Optional[str] = None):
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
            db.session.rollback()
            existing = IdempotencyRecord.query.filter_by(
                idempotency_key=effective_key,
            ).first()
            if existing:
                return {"success": True, "exec_id": existing.outcome_id, "idempotent": True}
            raise

        return {"success": True, "exec_id": outcome.outcome_id, "idempotent": False}

    def inspect(self, execution_id: str = "", tenant_id: int = 1):
        """Inspect execution status."""
        outcome = self._runtime.get(execution_id)
        if outcome:
            return {"status": "completed", "exec_id": execution_id}
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
]