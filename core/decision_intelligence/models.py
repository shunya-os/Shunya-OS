"""Universal Decision Intelligence — Data Models.

Decision Intelligence models how decisions are made by composing from
every frozen Universal Capability. It does not model workflow software,
approvals, or business rules. It models decision making.

UCP-05 — Universal Decision Intelligence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _generate_id() -> str:
    import uuid
    return str(uuid.uuid4())


# ── Enums ─────────────────────────────────────────────────────────────────

class DecisionCategory(str, Enum):
    """Universal decision categories."""
    PERSONAL = "personal"
    BUSINESS = "business"
    INVESTMENT = "investment"
    HIRING = "hiring"
    MEDICAL = "medical"
    TRAVEL = "travel"
    BUDGET = "budget"
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    RELATIONSHIP = "relationship"
    CAREER = "career"
    EDUCATION = "education"
    PURCHASE = "purchase"
    LIFESTYLE = "lifestyle"


class DecisionStatus(str, Enum):
    """Lifecycle of a decision."""
    PENDING = "pending"
    EVALUATING = "evaluating"
    RECOMMENDED = "recommended"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    SUPERSEDED = "superseded"


class ImpactType(str, Enum):
    """Dimensions of impact for decision evaluation."""
    FINANCIAL = "financial"
    RELATIONSHIP = "relationship"
    TIME = "time"
    RESOURCE = "resource"
    KNOWLEDGE = "knowledge"
    HEALTH = "health"
    CAREER = "career"
    EMOTIONAL = "emotional"
    ENVIRONMENTAL = "environmental"
    REPUTATION = "reputation"
    RISK = "risk"
    OPPORTUNITY = "opportunity"


class ConstraintType(str, Enum):
    """Types of decision constraints."""
    BUDGET = "budget"
    TIME = "time"
    RESOURCE = "resource"
    POLICY = "policy"
    REGULATORY = "regulatory"
    CAPACITY = "capacity"
    COMMITMENT = "commitment"
    RELATIONSHIP = "relationship"
    ETHICAL = "ethical"
    LEGAL = "legal"


class PriorityLevel(str, Enum):
    """Priority levels for decision options."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class CertaintyLevel(str, Enum):
    """Certainty about a decision or option."""
    CERTAIN = "certain"
    HIGHLY_LIKELY = "highly_likely"
    LIKELY = "likely"
    POSSIBLE = "possible"
    UNLIKELY = "unlikely"
    HIGHLY_UNLIKELY = "highly_unlikely"
    UNKNOWN = "unknown"


# ── Data Models ────────────────────────────────────────────────────────────

@dataclass
class DecisionConstraint:
    """A constraint that limits decision options."""
    constraint_id: str = field(default_factory=_generate_id)
    constraint_type: str = ConstraintType.BUDGET.value
    description: str = ""
    max_value: float = 0.0
    min_value: float = 0.0
    is_hard: bool = True  # hard cannot be violated; soft can be stretched
    evidence: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "constraint_type": self.constraint_type,
            "description": self.description,
            "max_value": self.max_value,
            "min_value": self.min_value,
            "is_hard": self.is_hard,
            "evidence": list(self.evidence),
        }


@dataclass
class ImpactAssessment:
    """Assessment of impact on a specific dimension."""
    impact_id: str = field(default_factory=_generate_id)
    impact_type: str = ImpactType.FINANCIAL.value
    description: str = ""
    magnitude: float = 0.0  # 0-1 scale
    direction: str = "positive"  # positive, negative, neutral
    certainty: str = CertaintyLevel.POSSIBLE.value
    value: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "impact_id": self.impact_id,
            "impact_type": self.impact_type,
            "description": self.description,
            "magnitude": self.magnitude,
            "direction": self.direction,
            "certainty": self.certainty,
            "value": dict(self.value),
            "evidence": list(self.evidence),
        }


@dataclass
class DecisionOption:
    """A single option within a decision."""
    option_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    priority: str = PriorityLevel.MEDIUM.value
    overall_score: float = 0.0
    confidence: float = 0.0
    impacts: list[ImpactAssessment] = field(default_factory=list)
    constraints_satisfied: list[str] = field(default_factory=list)
    constraints_violated: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    risks: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "option_id": self.option_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "overall_score": self.overall_score,
            "confidence": self.confidence,
            "impacts": [i.to_dict() for i in self.impacts],
            "constraints_satisfied": list(self.constraints_satisfied),
            "constraints_violated": list(self.constraints_violated),
            "assumptions": list(self.assumptions),
            "risks": list(self.risks),
            "evidence": list(self.evidence),
            "metadata": dict(self.metadata),
        }


@dataclass
class Decision:
    """A decision — the universal unit of reasoning about what to do next."""
    decision_id: str = field(default_factory=_generate_id)
    title: str = ""
    context: str = ""
    category: str = DecisionCategory.PERSONAL.value
    status: str = DecisionStatus.PENDING.value
    decision_maker: str = ""
    options: list[DecisionOption] = field(default_factory=list)
    constraints: list[DecisionConstraint] = field(default_factory=list)
    selected_option_id: str = ""
    final_recommendation: str = ""
    final_confidence: float = 0.0
    reasoning: str = ""
    assumptions: list[str] = field(default_factory=list)
    expected_outcome: str = ""
    evidence_sources: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def is_decided(self) -> bool:
        return self.status in (DecisionStatus.ACCEPTED.value, DecisionStatus.REJECTED.value,
                                DecisionStatus.IMPLEMENTED.value, DecisionStatus.SUPERSEDED.value)

    @property
    def ranked_options(self) -> list[DecisionOption]:
        return sorted(self.options, key=lambda o: o.overall_score, reverse=True)

    @property
    def best_option(self) -> DecisionOption | None:
        return self.ranked_options[0] if self.options else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "context": self.context,
            "category": self.category,
            "status": self.status,
            "decision_maker": self.decision_maker,
            "options": [o.to_dict() for o in self.options],
            "constraints": [c.to_dict() for c in self.constraints],
            "selected_option_id": self.selected_option_id,
            "final_recommendation": self.final_recommendation,
            "final_confidence": self.final_confidence,
            "reasoning": self.reasoning,
            "assumptions": list(self.assumptions),
            "expected_outcome": self.expected_outcome,
            "evidence_sources": list(self.evidence_sources),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_decided": self.is_decided,
            "option_count": len(self.options),
        }


@dataclass
class DecisionProfile:
    """A decision-making profile for an entity.

    Tracks decision history, patterns, and preferences.
    """
    profile_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    label: str = ""
    decisions: list[Decision] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def total_decisions(self) -> int:
        return len(self.decisions)

    @property
    def implemented_decisions(self) -> list[Decision]:
        return [d for d in self.decisions if d.status == DecisionStatus.IMPLEMENTED.value]

    @property
    def pending_decisions(self) -> list[Decision]:
        return [d for d in self.decisions if d.status == DecisionStatus.PENDING.value]

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "owner_id": self.owner_id,
            "label": self.label,
            "decisions": [d.to_dict() for d in self.decisions],
            "preferences": dict(self.preferences),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "total_decisions": self.total_decisions,
            "implemented_count": len(self.implemented_decisions),
            "pending_count": len(self.pending_decisions),
        }