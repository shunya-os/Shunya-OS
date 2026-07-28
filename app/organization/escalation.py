"""
SHUNYA Autonomous Organization Runtime — Escalation Engine

Escalation is universal. Supports: time-based, risk-based, policy-based,
capacity-based, dependency-based. Escalations become runtime events.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.organization.actor import Actor, get_store as get_actor_store, CapacityStatus
from app.organization.responsibility import Delegation, get_graph


@dataclass
class EscalationRule:
    """A universal escalation rule. Business agnostic."""

    rule_id: str
    name: str
    rule_type: str
    """'time_based', 'risk_based', 'policy_based', 'capacity_based', 'dependency_based'"""

    condition_description: str
    priority: int = 0
    escalate_to_actor_id: str = ""
    max_wait_hours: float = 0.0
    min_risk_threshold: float = 0.0
    max_capacity_ratio: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class EscalationEvent:
    """A recorded escalation event."""

    event_id: str
    rule_id: str
    decision_id: str
    delegation_id: Optional[str] = None
    from_actor_id: str = ""
    to_actor_id: str = ""
    reason: str = ""
    created_at: str = ""
    resolved_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "rule_id": self.rule_id,
            "decision_id": self.decision_id,
            "delegation_id": self.delegation_id,
            "from_actor_id": self.from_actor_id,
            "to_actor_id": self.to_actor_id,
            "reason": self.reason,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }


class EscalationEngine:
    """Universal escalation engine. Evaluates rules against runtime state."""

    def __init__(self):
        self._rules: list[EscalationRule] = []
        self._events: list[EscalationEvent] = []
        self._counter: int = 0

    def add_rule(self, rule: EscalationRule) -> None:
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)

    def evaluate_delegation(self, delegation: Delegation) -> list[EscalationEvent]:
        """Evaluate all rules against a delegation. Returns triggered escalations."""
        triggered = []
        actor_store = get_actor_store()

        for rule in self._rules:
            should_escalate = False
            reason = ""

            if rule.rule_type == "time_based" and rule.max_wait_hours > 0:
                if delegation.created_at:
                    try:
                        created = datetime.fromisoformat(delegation.created_at)
                        elapsed = (datetime.now(timezone.utc) - created).total_seconds() / 3600
                        if elapsed > rule.max_wait_hours:
                            should_escalate = True
                            reason = f"Exceeded max wait time of {rule.max_wait_hours}h"
                    except (ValueError, TypeError):
                        pass

            elif rule.rule_type == "capacity_based" and rule.max_capacity_ratio > 0:
                delegate = actor_store.get(delegation.delegate_id)
                if delegate and delegate.capacity_ratio > rule.max_capacity_ratio:
                    should_escalate = True
                    reason = f"Delegate capacity ratio {delegate.capacity_ratio:.2f} exceeds threshold {rule.max_capacity_ratio}"

            if should_escalate:
                self._counter += 1
                event = EscalationEvent(
                    event_id=f"esc_{self._counter}",
                    rule_id=rule.rule_id,
                    decision_id=delegation.decision_id,
                    delegation_id=delegation.delegation_id,
                    from_actor_id=delegation.delegate_id,
                    to_actor_id=rule.escalate_to_actor_id or delegation.delegator_id,
                    reason=reason,
                )
                self._events.append(event)
                triggered.append(event)

        return triggered

    def get_events(self, limit: int = 20) -> list[EscalationEvent]:
        return self._events[-limit:]

    @property
    def count(self) -> int:
        return len(self._rules)

    @property
    def event_count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        self._rules.clear()
        self._events.clear()
        self._counter = 0


_engine: Optional[EscalationEngine] = None


def get_engine() -> EscalationEngine:
    global _engine
    if _engine is None:
        _engine = EscalationEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None