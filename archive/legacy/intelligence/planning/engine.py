"""
SHUNYA Planning Engine — Objective Generation, Dependency Mapping, and Plan Construction

Generates plans, manages objectives, maps dependencies, and tracks progress.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from core.runtime.models import Engine, EngineStatus, HealthLevel, HealthStatus


class PlanStatus(Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


@dataclass
class PlanObjective:
    objective_id: str
    description: str
    completed: bool = False


@dataclass
class Plan:
    plan_id: str
    name: str
    objectives: list[PlanObjective] = field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None


class PlanningEngine(Engine):
    """Canonical planning engine for plan creation and lifecycle."""

    engine_id: str = "planning"
    engine_type: str = "intelligence"

    def __init__(self) -> None:
        super().__init__()
        self._plans: dict[str, Plan] = {}
        self._dependencies: dict[str, list[str]] = {}
        self._initialized = False

    def initialize(self) -> None:
        self._status = EngineStatus.ACTIVE
        self._initialized = True

    def shutdown(self) -> None:
        self._plans.clear()
        self._dependencies.clear()
        self._status = EngineStatus.OFFLINE
        self._initialized = False

    def health_check(self) -> HealthStatus:
        return HealthStatus(
            status=HealthLevel.HEALTHY if self._initialized else HealthLevel.UNHEALTHY,
            checks={"initialized": self._initialized, "plan_count": len(self._plans)},
        )

    def handle_event(self, event: Any) -> None:
        if not self._initialized:
            return

    def get_capabilities(self) -> List[str]:
        return ["planning.plan.create", "planning.plan.update", "planning.dependency.map"]

    def create(self, name: str, objectives: list[str] | None = None) -> Plan:
        plan = Plan(
            plan_id=f"plan-{len(self._plans) + 1}",
            name=name,
            objectives=[PlanObjective(objective_id=f"obj-{i}", description=d)
                        for i, d in enumerate(objectives or [])],
        )
        self._plans[plan.plan_id] = plan
        return plan

    def get(self, plan_id: str) -> Optional[Plan]:
        return self._plans.get(plan_id)

    def list(self) -> list[Plan]:
        return list(self._plans.values())

    def add_dependency(self, source_id: str, target_id: str) -> None:
        self._dependencies.setdefault(source_id, []).append(target_id)

    def get_dependency_order(self) -> list[str]:
        visited: set[str] = set()
        order: list[str] = []

        def dfs(node: str) -> None:
            if node in visited:
                return
            visited.add(node)
            for dep in self._dependencies.get(node, []):
                dfs(dep)
            order.append(node)

        for node in list(self._dependencies.keys()) + [p.plan_id for p in self._plans.values()]:
            dfs(node)
        return order