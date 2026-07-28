"""
SHUNYA Autonomous Organization Runtime — Responsibility Graph

Every BusinessExecutionInstance resolves through:
  Decision → Responsible Actor → Delegated Actors → Current Owner →
  Supporting Actors → Evidence Providers → Outcome Owner

The graph supports many-to-many relationships.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.organization.actor import Actor, get_store as get_actor_store


class DelegationStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class Delegation:
    """Universal delegation. Who delegated, who accepted, why, when, authority."""

    delegation_id: str
    decision_id: str
    delegator_id: str
    delegate_id: str
    reason: str = ""
    authority_granted: str = ""
    expected_outcome: str = ""
    status: DelegationStatus = DelegationStatus.PENDING
    created_at: str = ""
    expires_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "delegation_id": self.delegation_id,
            "decision_id": self.decision_id,
            "delegator_id": self.delegator_id,
            "delegate_id": self.delegate_id,
            "reason": self.reason,
            "authority_granted": self.authority_granted,
            "expected_outcome": self.expected_outcome,
            "status": self.status.value,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }


@dataclass
class Responsibility:
    """A responsibility links a decision to an actor through the graph."""

    responsibility_id: str
    decision_id: str
    actor_id: str
    role: str
    """'responsible', 'delegated', 'current_owner', 'supporting', 'evidence_provider', 'outcome_owner'"""

    delegation_id: Optional[str] = None
    created_at: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "responsibility_id": self.responsibility_id,
            "decision_id": self.decision_id,
            "actor_id": self.actor_id,
            "role": self.role,
            "delegation_id": self.delegation_id,
            "created_at": self.created_at,
        }


class ResponsibilityGraph:
    """The responsibility graph. Many-to-many relationships between decisions and actors."""

    def __init__(self):
        self._responsibilities: dict[str, Responsibility] = {}
        self._delegations: dict[str, Delegation] = {}

    # ─── Responsibilities ───

    def add_responsibility(self, resp: Responsibility) -> None:
        self._responsibilities[resp.responsibility_id] = resp

    def get_responsibilities_for_decision(self, decision_id: str) -> list[Responsibility]:
        return [r for r in self._responsibilities.values() if r.decision_id == decision_id]

    def get_responsibilities_for_actor(self, actor_id: str) -> list[Responsibility]:
        return [r for r in self._responsibilities.values() if r.actor_id == actor_id]

    def resolve_chain(self, decision_id: str) -> dict:
        """Resolve the full responsibility chain for a decision.

        Returns: Decision → Responsible Actor → Delegated Actors →
                 Current Owner → Supporting Actors → Evidence Providers → Outcome Owner
        """
        chain = self.get_responsibilities_for_decision(decision_id)
        result = {
            "decision_id": decision_id,
            "responsible": [],
            "delegated": [],
            "current_owner": [],
            "supporting": [],
            "evidence_providers": [],
            "outcome_owner": [],
        }
        for r in chain:
            role_key = r.role.replace(" ", "_")
            if role_key in result:
                actor_store = get_actor_store()
                actor = actor_store.get(r.actor_id)
                result[role_key].append({
                    "actor_id": r.actor_id,
                    "actor_name": actor.name if actor else r.actor_id,
                    "responsibility_id": r.responsibility_id,
                    "delegation_id": r.delegation_id,
                })
        return result

    # ─── Delegations ───

    def add_delegation(self, delegation: Delegation) -> None:
        self._delegations[delegation.delegation_id] = delegation

    def get_delegation(self, delegation_id: str) -> Optional[Delegation]:
        return self._delegations.get(delegation_id)

    def get_delegations_for_decision(self, decision_id: str) -> list[Delegation]:
        return [d for d in self._delegations.values() if d.decision_id == decision_id]

    def get_delegations_for_actor(self, actor_id: str) -> list[Delegation]:
        return [d for d in self._delegations.values()
                if d.delegator_id == actor_id or d.delegate_id == actor_id]

    @property
    def count(self) -> int:
        return len(self._responsibilities)

    def clear(self) -> None:
        self._responsibilities.clear()
        self._delegations.clear()


_graph: Optional[ResponsibilityGraph] = None


def get_graph() -> ResponsibilityGraph:
    global _graph
    if _graph is None:
        _graph = ResponsibilityGraph()
    return _graph


def reset_graph() -> None:
    global _graph
    _graph = None