"""
SHUNYA Universal Planning Runtime — Plan Engine

Plans decompose Objectives into ordered milestones.
Support: versioning, alternative paths, contingency paths, dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class PlanStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


PLAN_TRANSITIONS = {
    PlanStatus.DRAFT: {PlanStatus.ACTIVE, PlanStatus.CANCELLED},
    PlanStatus.ACTIVE: {PlanStatus.PAUSED, PlanStatus.COMPLETED, PlanStatus.CANCELLED, PlanStatus.SUPERSEDED},
    PlanStatus.PAUSED: {PlanStatus.ACTIVE, PlanStatus.CANCELLED},
    PlanStatus.COMPLETED: {PlanStatus.ARCHIVED},
    PlanStatus.CANCELLED: {PlanStatus.ARCHIVED},
    PlanStatus.SUPERSEDED: {PlanStatus.ARCHIVED},
    PlanStatus.ARCHIVED: set(),
}


@dataclass
class Milestone:
    milestone_id: str
    plan_id: str
    label: str
    description: str = ""
    order: int = 0
    responsible_actor_id: str = ""
    checkpoint_ids: list[str] = field(default_factory=list)
    dependency_ids: list[str] = field(default_factory=list)
    is_completed: bool = False
    completed_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def complete(self) -> None:
        self.is_completed = True
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "milestone_id": self.milestone_id,
            "plan_id": self.plan_id,
            "label": self.label,
            "description": self.description,
            "order": self.order,
            "responsible_actor_id": self.responsible_actor_id,
            "checkpoint_ids": self.checkpoint_ids,
            "dependency_ids": self.dependency_ids,
            "is_completed": self.is_completed,
            "completed_at": self.completed_at,
        }


@dataclass
class PlanVersion:
    version_id: str
    plan_id: str
    version_number: int
    milestones: list[Milestone] = field(default_factory=list)
    alternative_paths: list[list[str]] = field(default_factory=list)
    contingency_paths: list[list[str]] = field(default_factory=list)
    created_at: str = ""
    notes: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "plan_id": self.plan_id,
            "version_number": self.version_number,
            "milestones": [m.to_dict() for m in self.milestones],
            "alternative_paths": self.alternative_paths,
            "contingency_paths": self.contingency_paths,
            "created_at": self.created_at,
            "notes": self.notes,
        }


@dataclass
class Plan:
    plan_id: str
    objective_id: str
    label: str
    description: str = ""
    status: PlanStatus = PlanStatus.DRAFT
    versions: list[PlanVersion] = field(default_factory=list)
    current_version: int = 0
    created_at: str = ""
    completed_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def current(self) -> Optional[PlanVersion]:
        if self.versions:
            return self.versions[-1]
        return None

    @property
    def milestones(self) -> list[Milestone]:
        if self.current:
            return self.current.milestones
        return []

    def transition_to(self, new_status: PlanStatus) -> None:
        allowed = PLAN_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status
        if new_status == PlanStatus.COMPLETED:
            self.completed_at = datetime.now(timezone.utc).isoformat()

    def add_version(self, version: PlanVersion) -> None:
        self.versions.append(version)
        self.current_version = version.version_number

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "objective_id": self.objective_id,
            "label": self.label,
            "description": self.description,
            "status": self.status.value,
            "current_version": self.current_version,
            "milestone_count": len(self.milestones),
            "version_count": len(self.versions),
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class PlanEngine:
    def __init__(self):
        self._plans: dict[str, Plan] = {}

    def create_plan(self, objective_id: str, label: str,
                    milestones: list[Milestone], description: str = "") -> Plan:
        import hashlib, time
        plan_id = f"plan_{hashlib.md5(f'{objective_id}:{label}:{time.time()}'.encode()).hexdigest()[:8]}"
        plan = Plan(plan_id=plan_id, objective_id=objective_id, label=label, description=description)
        version = PlanVersion(
            version_id=f"v1_{plan_id}",
            plan_id=plan_id,
            version_number=1,
            milestones=milestones,
        )
        plan.add_version(version)
        self._plans[plan_id] = plan
        return plan

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        return self._plans.get(plan_id)

    def get_plans_for_objective(self, objective_id: str) -> list[Plan]:
        return [p for p in self._plans.values() if p.objective_id == objective_id]

    def get_active(self) -> list[Plan]:
        return [p for p in self._plans.values() if p.status == PlanStatus.ACTIVE]

    @property
    def count(self) -> int:
        return len(self._plans)

    def clear(self) -> None:
        self._plans.clear()


_engine: Optional[PlanEngine] = None


def get_engine() -> PlanEngine:
    global _engine
    if _engine is None:
        _engine = PlanEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None