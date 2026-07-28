"""
SHUNYA Governance Engine — Policy Evaluation, Compliance, and Approval

Evaluates policies, checks compliance, and manages approval workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional

from core.runtime.models import Engine, EngineStatus, HealthLevel, HealthStatus


@dataclass
class PolicyRule:
    policy_id: str
    name: str
    allowed_actions: list[str]
    conditions: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def evaluate(self, request: dict) -> bool:
        action = request.get("action", "")
        if action not in self.allowed_actions:
            return False
        for key, expected in self.conditions.items():
            if request.get(key) != expected:
                return False
        return True


class GovernanceEngine(Engine):
    """Canonical governance engine for policy evaluation and compliance."""

    engine_id: str = "governance"
    engine_type: str = "intelligence"

    def __init__(self) -> None:
        super().__init__()
        self._policies: dict[str, PolicyRule] = {}
        self._initialized = False

    def initialize(self) -> None:
        self._status = EngineStatus.ACTIVE
        self._initialized = True

    def shutdown(self) -> None:
        self._policies.clear()
        self._status = EngineStatus.OFFLINE
        self._initialized = False

    def health_check(self) -> HealthStatus:
        return HealthStatus(
            status=HealthLevel.HEALTHY if self._initialized else HealthLevel.UNHEALTHY,
            checks={"initialized": self._initialized, "policy_count": len(self._policies)},
        )

    def handle_event(self, event: Any) -> None:
        if not self._initialized:
            return

    def get_capabilities(self) -> List[str]:
        return ["governance.policy.register", "governance.policy.evaluate", "governance.compliance.check"]

    def register(self, name: str, allowed_actions: list[str], conditions: dict | None = None) -> PolicyRule:
        policy = PolicyRule(
            policy_id=f"pol-{len(self._policies) + 1}",
            name=name, allowed_actions=allowed_actions, conditions=conditions or {},
        )
        self._policies[policy.policy_id] = policy
        return policy

    def evaluate(self, request: dict) -> dict:
        results = {}
        for pid, policy in self._policies.items():
            results[pid] = {"allowed": policy.evaluate(request), "policy_name": policy.name}
        return {"allowed": all(r["allowed"] for r in results.values()), "policy_results": results}

    def check_compliance(self, object_id: str, action: str) -> bool:
        result = self.evaluate({"action": action, "object_id": object_id})
        return result["allowed"]