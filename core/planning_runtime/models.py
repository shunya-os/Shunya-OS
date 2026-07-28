"""SHUNYA Planning & Reasoning Runtime — data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _generate_id() -> str:
    from core.kernel.types import generate_uuid7
    return generate_uuid7()


class PlanStatus(str, Enum):
    DRAFT = "draft"
    VALIDATING = "validating"
    VALIDATED = "validated"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REPAIRED = "repaired"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    COMPOUND = "compound"
    PRIMITIVE = "primitive"


class ConstraintType(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class ConstraintCategory(str, Enum):
    RESOURCE = "resource"
    DEPENDENCY = "dependency"
    TEMPORAL = "temporal"
    BUDGET = "budget"
    PERMISSION = "permission"
    CUSTOM = "custom"


@dataclass
class Constraint:
    constraint_id: str = field(default_factory=_generate_id)
    constraint_type: ConstraintType = ConstraintType.HARD
    category: ConstraintCategory = ConstraintCategory.CUSTOM
    description: str = ""
    expression: str = ""  # Simple expression string, e.g. "cost < 1000"
    satisfied: bool = True


@dataclass
class Resource:
    resource_id: str = field(default_factory=_generate_id)
    name: str = ""
    resource_type: str = ""
    quantity: float = 1.0
    unit: str = "units"


@dataclass
class Task:
    task_id: str = field(default_factory=_generate_id)
    parent_id: str | None = None
    task_type: TaskType = TaskType.PRIMITIVE
    label: str = ""
    description: str = ""
    action_id: str = ""          # For primitive: which Execution Runtime action
    sub_goals: list[str] = field(default_factory=list)  # For compound: decomposed sub-goals
    dependencies: list[str] = field(default_factory=list)  # task_ids this depends on
    resources: list[Resource] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_risk: float = 0.0
    estimated_duration_sec: float = 0.0
    requires_approval: bool = False
    approved: bool = False
    rationale: str = ""
    alternatives: list[str] = field(default_factory=list)  # alternative task_ids
    created_at: str = field(default_factory=_now_iso)


@dataclass
class Goal:
    goal_id: str = field(default_factory=_generate_id)
    label: str = ""
    description: str = ""
    priority: int = 50
    parent_goal_id: str | None = None
    sub_goals: list[str] = field(default_factory=list)  # child goal_ids
    constraints: list[Constraint] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)  # task_ids
    achieved: bool = False
    created_at: str = field(default_factory=_now_iso)


@dataclass
class Plan:
    plan_id: str = field(default_factory=_generate_id)
    label: str = ""
    goal_id: str = ""
    tasks: list[Task] = field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    constraints: list[Constraint] = field(default_factory=list)
    total_cost: float = 0.0
    total_risk: float = 0.0
    total_duration_sec: float = 0.0
    version: int = 1
    provenance: list[str] = field(default_factory=list)  # rationale/log entries
    parent_plan_id: str | None = None           # For repairs/re-plans
    approval_checkpoints: list[str] = field(default_factory=list)  # task_ids requiring approval
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class AlternativePlan:
    alternative_id: str = field(default_factory=_generate_id)
    plan_id: str = ""
    label: str = ""
    tasks: list[Task] = field(default_factory=list)
    total_cost: float = 0.0
    total_risk: float = 0.0
    total_duration_sec: float = 0.0
    rationale: str = ""


@dataclass
class PlanTrace:
    operation: str = ""
    plan_id: str = ""
    task_id: str = ""
    status: str = ""
    latency_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now_iso)


@dataclass
class PlanStats:
    total_plans: int = 0
    total_tasks: int = 0
    plans_by_status: dict[str, int] = field(default_factory=dict)
    avg_cost: float = 0.0
    avg_risk: float = 0.0
    avg_duration_sec: float = 0.0