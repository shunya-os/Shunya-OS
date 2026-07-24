"""
SHUNYA Universal Planning Runtime — Objective Model

Every organization exists to achieve Objectives.
Objectives become Plans. Plans become Milestones.
Milestones become Executions. Executions produce Evidence.
Evidence produces Outcomes. Everything is explainable.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ObjectiveStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


OBJECTIVE_TRANSITIONS = {
    ObjectiveStatus.DRAFT: {ObjectiveStatus.ACTIVE, ObjectiveStatus.CANCELLED},
    ObjectiveStatus.ACTIVE: {ObjectiveStatus.PAUSED, ObjectiveStatus.COMPLETED, ObjectiveStatus.CANCELLED, ObjectiveStatus.SUPERSEDED},
    ObjectiveStatus.PAUSED: {ObjectiveStatus.ACTIVE, ObjectiveStatus.CANCELLED, ObjectiveStatus.SUPERSEDED},
    ObjectiveStatus.COMPLETED: set(),
    ObjectiveStatus.CANCELLED: set(),
    ObjectiveStatus.SUPERSEDED: set(),
}


@dataclass
class Objective:
    objective_id: str
    purpose: str
    priority: int = 0
    owner_actor_id: str = ""
    stakeholder_ids: list[str] = field(default_factory=list)
    expected_outcomes: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    dependency_ids: list[str] = field(default_factory=list)
    evidence_requirements: list[str] = field(default_factory=list)
    status: ObjectiveStatus = ObjectiveStatus.DRAFT
    health: float = 0.5
    trajectory: str = "stable"
    created_at: str = ""
    completed_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def transition_to(self, new_status: ObjectiveStatus) -> None:
        allowed = OBJECTIVE_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status
        if new_status == ObjectiveStatus.COMPLETED:
            self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "objective_id": self.objective_id,
            "purpose": self.purpose,
            "priority": self.priority,
            "owner_actor_id": self.owner_actor_id,
            "stakeholder_ids": self.stakeholder_ids,
            "expected_outcomes": self.expected_outcomes,
            "constraints": self.constraints,
            "dependency_ids": self.dependency_ids,
            "evidence_requirements": self.evidence_requirements,
            "status": self.status.value,
            "health": self.health,
            "trajectory": self.trajectory,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class ObjectiveStore:
    def __init__(self):
        self._objectives: dict[str, Objective] = {}

    def add(self, obj: Objective) -> None:
        self._objectives[obj.objective_id] = obj

    def get(self, objective_id: str) -> Optional[Objective]:
        return self._objectives.get(objective_id)

    def get_active(self) -> list[Objective]:
        return [o for o in self._objectives.values() if o.status == ObjectiveStatus.ACTIVE]

    def get_by_owner(self, actor_id: str) -> list[Objective]:
        return [o for o in self._objectives.values() if o.owner_actor_id == actor_id]

    @property
    def count(self) -> int:
        return len(self._objectives)

    def clear(self) -> None:
        self._objectives.clear()


_store: Optional[ObjectiveStore] = None


def get_store() -> ObjectiveStore:
    global _store
    if _store is None:
        _store = ObjectiveStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None