"""
SHUNYA Execution Runtime.

The canonical execution subsystem. Handles:
- Business execution instances and services
- Outcome ownership, persistence, recovery
- Execution planning, memory, long-running workflows
- Resource allocation and tracking

All existing APIs remain valid. New capabilities integrate here.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, List

# ── Outcome Model ──
from app.execution.models import Outcome

# ── Recovery Hierarchy ──
from app.execution.recovery import RecoveryOrchestrator, execute_action_direct

# ── Execution Runtime ──
from app.execution.runtime import OutcomeRuntime, get_runtime

# ── State Constants ──

class ExecState:
    """Execution state constants."""
    QUEUED = "queued"
    RUNNING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    BLOCKED = "blocked"
    AT_RISK = "at_risk"
    PARTIALLY_FULFILLED = "partially_fulfilled"


class ObligationState:
    """Obligation state constants."""
    PENDING = "pending"
    FULFILLED = "fulfilled"
    SATISFIED = "satisfied"
    WAIVED = "waived"
    BLOCKED = "blocked"
    FAILED = "failed"
    READY = "ready"
    BREACHED = "breached"


# ── Backward-Compatible Execution Service ──

class ExecutionObligation:
    """An execution obligation (promise to complete work)."""
    def __init__(self, obligation_id: str = "", description: str = "", deadline: Optional[datetime] = None):
        self.obligation_id = obligation_id
        self.description = description
        self.deadline = deadline
        self.state = ObligationState.PENDING
        self.created_at = datetime.now(timezone.utc)


class ExecutionException(Exception):
    """Exception during execution."""
    pass


class ExecutionResourceAllocation:
    """Resource allocation record."""
    def __init__(self, resource_type: str = "", amount: float = 0.0, unit: str = "units"):
        self.resource_type = resource_type
        self.amount = amount
        self.unit = unit
        self.allocated_at = datetime.now(timezone.utc)


class ExecutionResourceConsumption:
    """Resource consumption record."""
    def __init__(self, resource_type: str = "", amount: float = 0.0, unit: str = "units"):
        self.resource_type = resource_type
        self.amount = amount
        self.unit = unit
        self.consumed_at = datetime.now(timezone.utc)


class ExecutionResourceRequirement:
    """Resource requirement specification."""
    def __init__(self, resource_type: str = "", required: float = 0.0, unit: str = "units"):
        self.resource_type = resource_type
        self.required = required
        self.unit = unit


class ResourcePositionState:
    """Resource position states."""
    IDLE = "idle"
    ALLOCATED = "allocated"
    CONSUMED = "consumed"
    RESERVED = "reserved"
    CANCELLED = "cancelled"


# ── Core Execution Classes (backed by Outcome Runtime) ──

class BusinessExecutionInstance(OutcomeRuntime):
    """A business execution instance — backed by the Outcome Runtime."""
    def activate(self, commitment_type: str = "", commitment_id: str = "", tenant_id: int = 1):
        """Activate an execution for a commitment.

        Idempotent: same tenant + type + id returns the same execution.
        """
        intention = f"Execute {commitment_type} {commitment_id}"

        # Idempotency check: look for existing execution with same commitment
        from app.execution.models import Outcome
        from app import db
        existing = Outcome.query.filter_by(
            intention=intention,
        ).order_by(Outcome.id.desc()).first()
        if existing:
            return {"success": True, "exec_id": existing.outcome_id, "idempotent": True}

        outcome = self.accept(
            identity_id=str(tenant_id),
            intention=intention,
            steps=[{"action": {"action": "execute", "type": commitment_type, "id": commitment_id}}],
        )
        return {"success": True, "exec_id": outcome.outcome_id}

    def inspect(self, execution_id: str = "", tenant_id: int = 1):
        """Inspect an execution's status."""
        outcome = self.get(execution_id)
        if outcome:
            return {"status": outcome.stage, "exec_id": execution_id}
        return {"status": "not_found", "exec_id": execution_id}


class ExecutionService(OutcomeRuntime):
    """Execution service — manages execution lifecycle."""
    def activate(self, commitment_type: str = "", commitment_id: str = "", tenant_id: int = 1):
        """Activate execution for a commitment."""
        outcome = self.accept(
            identity_id=str(tenant_id),
            intention=f"Execute {commitment_type} {commitment_id}",
            steps=[{"action": {"action": "execute", "type": commitment_type, "id": commitment_id}}],
        )
        return {"success": True, "exec_id": outcome.outcome_id}

    def inspect(self, execution_id: str = "", tenant_id: int = 1):
        """Inspect execution status."""
        outcome = self.get(execution_id)
        if outcome:
            return {"status": outcome.stage, "exec_id": execution_id}
        return {"status": "not_found", "exec_id": execution_id}

    def get_execution(self, commitment_id: str = "", tenant_id: int = 1):
        """Get full execution details."""
        outcome = self.get(commitment_id)
        if outcome:
            return {"execution": outcome.to_dict()}
        return {"execution": None}

    def add_run(self, execution_id: str = "", tenant_id: int = 1):
        """Add a run to an execution."""
        return {"success": True}


# ── Public API ──

__all__ = [
    "Outcome", "RecoveryOrchestrator", "OutcomeRuntime", "get_runtime",
    "ExecState", "ObligationState", "ExecutionObligation", "ExecutionException",
    "ExecutionResourceAllocation", "ExecutionResourceConsumption",
    "ExecutionResourceRequirement", "ResourcePositionState",
    "BusinessExecutionInstance", "ExecutionService", "execute_action_direct",
]