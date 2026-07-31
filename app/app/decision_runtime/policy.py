"""
SHUNYA Decision Runtime — Policy Engine
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable


class PolicyAction(Enum):
    INFORM = "inform"
    RECOMMEND = "recommend"
    REQUEST_APPROVAL = "request_approval"
    EXECUTE_AUTOMATICALLY = "execute_automatically"
    ESCALATE = "escalate"


@dataclass
class PolicyResult:
    action: PolicyAction
    reason: str
    confidence_threshold: float = 0.0
    escalation_target: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class Policy:
    policy_id: str
    name: str
    description: str
    priority: int = 0
    evaluate_fn: Optional[Callable] = None

    def evaluate(self, decision: dict) -> Optional[PolicyResult]:
        if self.evaluate_fn:
            return self.evaluate_fn(decision)
        return None


class PolicyEngine:
    def __init__(self):
        self._policies: list[Policy] = []

    def register(self, policy: Policy) -> None:
        self._policies.append(policy)
        self._policies.sort(key=lambda p: p.priority, reverse=True)

    def evaluate(self, decision: dict) -> Optional[PolicyResult]:
        for policy in self._policies:
            result = policy.evaluate(decision)
            if result is not None:
                return result
        return None

    @property
    def policy_count(self) -> int:
        return len(self._policies)

    def clear(self) -> None:
        self._policies.clear()


# ─── Built-in policies ───

def _policy_high_confidence(decision: dict) -> Optional[PolicyResult]:
    conf = decision.get("confidence", 0.0)
    impact = decision.get("business_impact", "unknown")
    if conf >= 0.9 and impact in ("low", "negligible", "unknown"):
        return PolicyResult(action=PolicyAction.EXECUTE_AUTOMATICALLY, reason=f"Very high confidence ({conf:.2f}), low impact")

def _policy_low_confidence(decision: dict) -> Optional[PolicyResult]:
    if decision.get("confidence", 0.0) < 0.5:
        return PolicyResult(action=PolicyAction.REQUEST_APPROVAL, reason="Low confidence — requires human approval")

def _policy_high_impact(decision: dict) -> Optional[PolicyResult]:
    if decision.get("business_impact") == "high":
        return PolicyResult(action=PolicyAction.REQUEST_APPROVAL, reason="High business impact — requires human approval")

def _policy_critical_urgency(decision: dict) -> Optional[PolicyResult]:
    if decision.get("urgency") == "critical":
        return PolicyResult(action=PolicyAction.ESCALATE, reason="Critical urgency — escalating", escalation_target=decision.get("owner", "default"))

def _policy_medium_confidence(decision: dict) -> Optional[PolicyResult]:
    conf = decision.get("confidence", 0.0)
    if 0.5 <= conf < 0.75:
        return PolicyResult(action=PolicyAction.RECOMMEND, reason=f"Medium confidence ({conf:.2f}) — recommending")

def _policy_high_confidence_low_urgency(decision: dict) -> Optional[PolicyResult]:
    if decision.get("confidence", 0.0) >= 0.75 and decision.get("urgency") == "low":
        return PolicyResult(action=PolicyAction.INFORM, reason="High confidence, low urgency — informing only")

DEFAULT_POLICIES = [
    Policy(policy_id="critical-urgency", name="Critical Urgency", description="Escalate critical urgency", priority=100, evaluate_fn=_policy_critical_urgency),
    Policy(policy_id="high-impact", name="High Impact", description="Request approval for high impact", priority=90, evaluate_fn=_policy_high_impact),
    Policy(policy_id="low-confidence", name="Low Confidence", description="Request approval for low confidence", priority=80, evaluate_fn=_policy_low_confidence),
    Policy(policy_id="high-confidence-auto", name="High Confidence Auto", description="Execute automatically", priority=70, evaluate_fn=_policy_high_confidence),
    Policy(policy_id="medium-confidence", name="Medium Confidence", description="Recommend", priority=60, evaluate_fn=_policy_medium_confidence),
    Policy(policy_id="high-confidence-info", name="High Confidence Info", description="Inform only", priority=50, evaluate_fn=_policy_high_confidence_low_urgency),
]


_engine: Optional[PolicyEngine] = None


def get_engine() -> PolicyEngine:
    global _engine
    if _engine is None:
        _engine = PolicyEngine()
        for p in DEFAULT_POLICIES:
            _engine.register(p)
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None