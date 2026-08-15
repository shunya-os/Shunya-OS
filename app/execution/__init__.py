"""SHUNYA Execution — thin persistence layer.

The canonical execution authority is:

    runtime/entry.py → execution_engine → Object / Execution / ExecutionLog

This module provides Outcome persistence for backward compatibility.
It is NOT an execution engine. No step-based execution, no lifecycle
progression, no workflow semantics.

All existing APIs remain valid as thin wrappers around canonical state.
"""
from typing import Optional

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

    def activate(self, commitment_type: str = "", commitment_id: str = "", tenant_id: int = 1):
        """Record an execution activation."""
        outcome = self._runtime.accept(
            identity_id=str(tenant_id),
            intention=f"Execute {commitment_type} {commitment_id}",
        )
        return {"success": True, "exec_id": outcome.outcome_id}

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

    def activate(self, commitment_type: str = "", commitment_id: str = "", tenant_id: int = 1):
        outcome = self._runtime.accept(
            identity_id=str(tenant_id),
            intention=f"Execute {commitment_type} {commitment_id}",
        )
        return {"success": True, "exec_id": outcome.outcome_id, "idempotent": False}

    def inspect(self, execution_id: str = "", tenant_id: int = 1):
        outcome = self._runtime.get(execution_id)
        if outcome:
            return {"status": "completed", "exec_id": execution_id}
        return {"status": "not_found", "exec_id": execution_id}


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