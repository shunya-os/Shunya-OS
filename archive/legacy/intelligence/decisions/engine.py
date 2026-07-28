"""
SHUNYA Decisions Engine — Decision Lifecycle, Commitment, Outcome, and Learning

Manages the complete decision lifecycle from context through commitment
to outcome and learning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from core.runtime.models import Engine, EngineStatus, HealthLevel, HealthStatus


class DecisionStatus(Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMMITTED = "committed"
    IMPLEMENTED = "implemented"
    OBSOLETE = "obsolete"


@dataclass
class Decision:
    decision_id: str
    title: str
    context: dict = field(default_factory=dict)
    options: list[dict] = field(default_factory=list)
    status: DecisionStatus = DecisionStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    outcome: Optional[dict] = None


class DecisionsEngine(Engine):
    """Canonical decisions engine for the full decision lifecycle."""

    engine_id: str = "decisions"
    engine_type: str = "intelligence"

    def __init__(self) -> None:
        super().__init__()
        self._decisions: dict[str, Decision] = {}
        self._initialized = False

    def initialize(self) -> None:
        self._status = EngineStatus.ACTIVE
        self._initialized = True

    def shutdown(self) -> None:
        self._decisions.clear()
        self._status = EngineStatus.OFFLINE
        self._initialized = False

    def health_check(self) -> HealthStatus:
        return HealthStatus(
            status=HealthLevel.HEALTHY if self._initialized else HealthLevel.UNHEALTHY,
            checks={"initialized": self._initialized, "decision_count": len(self._decisions)},
        )

    def handle_event(self, event: Any) -> None:
        if not self._initialized:
            return

    def get_capabilities(self) -> List[str]:
        return ["decision.create", "decision.evaluate", "decision.commit", "decision.outcome.track"]

    def create(self, title: str, context: dict | None = None, options: list[dict] | None = None) -> Decision:
        decision = Decision(
            decision_id=f"dec-{len(self._decisions) + 1}",
            title=title, context=context or {}, options=options or [],
        )
        self._decisions[decision.decision_id] = decision
        return decision

    def evaluate(self, decision_id: str) -> dict:
        decision = self._decisions.get(decision_id)
        if not decision:
            return {"error": "not_found"}
        analysis = []
        for opt in decision.options:
            analysis.append({"option": opt, "score": 0.5, "confidence": "medium"})
        return {"decision_id": decision_id, "analysis": analysis}

    def get(self, decision_id: str) -> Optional[Decision]:
        return self._decisions.get(decision_id)

    def list(self) -> list[Decision]:
        return list(self._decisions.values())

    def record_outcome(self, decision_id: str, outcome: dict) -> bool:
        decision = self._decisions.get(decision_id)
        if decision:
            decision.outcome = outcome
            decision.status = DecisionStatus.IMPLEMENTED
            return True
        return False