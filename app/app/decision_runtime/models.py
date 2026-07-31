"""
SHUNYA Decision Runtime — Decision Object Model

A universal Decision Runtime object.
Every decision includes:
  Decision ID, Origin Insight, Supporting Evidence, Reasoning Reference,
  Confidence, Business Impact, Urgency, Owner, Approval Requirement,
  Current Status, Created Time, Executed Time, Outcome, Learning Reference

The Decision object is completely business agnostic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class DecisionStatus(Enum):
    CANDIDATE = "candidate"
    POLICY_EVALUATING = "policy_evaluating"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMMITTED = "committed"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


VALID_DECISION_TRANSITIONS = {
    DecisionStatus.CANDIDATE: {DecisionStatus.POLICY_EVALUATING, DecisionStatus.CANCELLED, DecisionStatus.SUPERSEDED},
    DecisionStatus.POLICY_EVALUATING: {DecisionStatus.AWAITING_APPROVAL, DecisionStatus.APPROVED, DecisionStatus.CANCELLED, DecisionStatus.SUPERSEDED},
    DecisionStatus.AWAITING_APPROVAL: {DecisionStatus.APPROVED, DecisionStatus.REJECTED, DecisionStatus.CANCELLED, DecisionStatus.SUPERSEDED},
    DecisionStatus.APPROVED: {DecisionStatus.COMMITTED, DecisionStatus.CANCELLED, DecisionStatus.SUPERSEDED},
    DecisionStatus.REJECTED: {DecisionStatus.CANCELLED, DecisionStatus.SUPERSEDED},
    DecisionStatus.COMMITTED: {DecisionStatus.EXECUTING, DecisionStatus.FAILED, DecisionStatus.CANCELLED},
    DecisionStatus.EXECUTING: {DecisionStatus.COMPLETED, DecisionStatus.FAILED, DecisionStatus.CANCELLED},
    DecisionStatus.COMPLETED: set(),
    DecisionStatus.FAILED: {DecisionStatus.CANCELLED},
    DecisionStatus.CANCELLED: set(),
    DecisionStatus.SUPERSEDED: set(),
}


@dataclass
class Decision:
    decision_id: str
    origin_insight_id: str
    label: str
    description: str
    supporting_evidence_ids: list[str] = field(default_factory=list)
    reasoning_reference: str = ""
    confidence: float = 0.0
    business_impact: str = "unknown"
    urgency: str = "normal"
    owner: str = ""
    approval_required: bool = True
    status: DecisionStatus = DecisionStatus.CANDIDATE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evaluated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    committed_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outcome_id: Optional[str] = None
    learning_id: Optional[str] = None
    tenant_id: int = 1
    metadata: dict = field(default_factory=dict)

    def transition_to(self, new_status: DecisionStatus, record_time: bool = True) -> None:
        allowed = VALID_DECISION_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from {self.status.value} to {new_status.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        self.status = new_status
        now = datetime.now(timezone.utc)
        if record_time:
            ts = {
                DecisionStatus.POLICY_EVALUATING: "evaluated_at",
                DecisionStatus.APPROVED: "approved_at",
                DecisionStatus.COMMITTED: "committed_at",
                DecisionStatus.EXECUTING: "executed_at",
                DecisionStatus.COMPLETED: "completed_at",
                DecisionStatus.FAILED: "completed_at",
            }
            attr = ts.get(new_status)
            if attr:
                setattr(self, attr, now)

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "origin_insight_id": self.origin_insight_id,
            "label": self.label,
            "description": self.description,
            "supporting_evidence_ids": self.supporting_evidence_ids,
            "reasoning_reference": self.reasoning_reference,
            "confidence": self.confidence,
            "business_impact": self.business_impact,
            "urgency": self.urgency,
            "owner": self.owner,
            "approval_required": self.approval_required,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "committed_at": self.committed_at.isoformat() if self.committed_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "outcome_id": self.outcome_id,
            "learning_id": self.learning_id,
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
        }


class DecisionStore:
    def __init__(self):
        self._decisions: dict[str, Decision] = {}

    def add(self, decision: Decision) -> None:
        self._decisions[decision.decision_id] = decision

    def get(self, decision_id: str) -> Optional[Decision]:
        return self._decisions.get(decision_id)

    def get_by_insight(self, insight_id: str) -> list[Decision]:
        return [d for d in self._decisions.values() if d.origin_insight_id == insight_id]

    def get_active(self) -> list[Decision]:
        active = {
            DecisionStatus.CANDIDATE, DecisionStatus.POLICY_EVALUATING,
            DecisionStatus.AWAITING_APPROVAL, DecisionStatus.APPROVED,
            DecisionStatus.COMMITTED, DecisionStatus.EXECUTING,
        }
        return [d for d in self._decisions.values() if d.status in active]

    @property
    def count(self) -> int:
        return len(self._decisions)

    def clear(self) -> None:
        self._decisions.clear()


_store: Optional[DecisionStore] = None


def get_store() -> DecisionStore:
    global _store
    if _store is None:
        _store = DecisionStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None