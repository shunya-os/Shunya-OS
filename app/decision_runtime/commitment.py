"""
SHUNYA Decision Runtime — Commitment Integration
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.decision_runtime.models import Decision, DecisionStatus
from app.execution import BusinessExecutionInstance, ExecState, ExecutionService


@dataclass
class Commitment:
    commitment_id: str
    decision_id: str
    exec_id: str
    label: str
    description: str
    tenant_id: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outcome_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "commitment_id": self.commitment_id,
            "decision_id": self.decision_id,
            "exec_id": self.exec_id,
            "label": self.label,
            "description": self.description,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "outcome_id": self.outcome_id,
            "metadata": self.metadata,
        }


class CommitmentService:
    def __init__(self, execution_service: Optional[ExecutionService] = None):
        self.execution = execution_service or ExecutionService()
        self._commitments: dict[str, Commitment] = {}

    def create_commitment(self, decision: Decision) -> dict:
        if decision.status != DecisionStatus.APPROVED:
            return {"error": f"Decision is {decision.status.value}, not 'approved'"}
        result = self.execution.activate(commitment_type="decision", commitment_id=decision.decision_id, tenant_id=decision.tenant_id)
        if result.get("error"):
            return result
        exec_id = result["exec_id"]
        cmt_id = f"cmt_{decision.decision_id}"
        cmt = Commitment(commitment_id=cmt_id, decision_id=decision.decision_id, exec_id=exec_id, label=decision.label, description=decision.description, tenant_id=decision.tenant_id)
        self._commitments[cmt_id] = cmt
        decision.transition_to(DecisionStatus.COMMITTED)
        return {"commitment_id": cmt_id, "exec_id": exec_id, "state": result.get("state")}

    def get_commitment(self, commitment_id: str) -> Optional[Commitment]:
        return self._commitments.get(commitment_id)

    def get_by_decision(self, decision_id: str) -> Optional[Commitment]:
        for c in self._commitments.values():
            if c.decision_id == decision_id:
                return c
        return None

    def get_execution(self, commitment_id: str) -> Optional[dict]:
        cmt = self._commitments.get(commitment_id)
        if not cmt:
            return None
        return self.execution.inspect(cmt.exec_id, cmt.tenant_id)

    @property
    def count(self) -> int:
        return len(self._commitments)

    def clear(self) -> None:
        self._commitments.clear()
        self.execution = ExecutionService()


_service: Optional[CommitmentService] = None


def get_service() -> CommitmentService:
    global _service
    if _service is None:
        _service = CommitmentService()
    return _service


def reset_service() -> None:
    global _service
    _service = None