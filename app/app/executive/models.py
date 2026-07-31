"""SHUNYA — Executive Intelligence canonical models (Milestone VI).

All executive entities are derived intelligence — never canonical state.
Every insight traces back to validated operational artifacts.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================================================
# Enums
# =========================================================================

class PriorityCategory(str, Enum):
    CRITICAL_COMMITMENT = "critical_commitment"
    BLOCKED_EXECUTION = "blocked_execution"
    REPEATED_FAILURE = "repeated_failure"
    RAPID_DETERIORATION = "rapid_deterioration"
    HIGH_VALUE_OPPORTUNITY = "high_value_opportunity"
    ESCALATION = "escalation"
    DEADLINE_THREAT = "deadline_threat"
    LEADERSHIP_BOTTLENECK = "leadership_bottleneck"


class RiskCategory(str, Enum):
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    RELATIONSHIP = "relationship"
    CAPACITY = "capacity"
    GOVERNANCE = "governance"
    EXECUTION = "execution"
    PREDICTION_UNCERTAINTY = "prediction_uncertainty"
    RISK_ACCUMULATION = "risk_accumulation"


class OpportunityCategory(str, Enum):
    GROWTH = "growth"
    EFFICIENCY = "efficiency"
    RELATIONSHIP = "relationship"
    RESOURCE = "resource"
    ACCELERATION = "acceleration"
    KNOWLEDGE = "knowledge"
    LEARNING = "learning"


class HealthDimension(str, Enum):
    EXECUTION = "execution_health"
    ORGANIZATIONAL = "organizational_health"
    DECISION = "decision_health"
    LEARNING = "learning_health"
    PREDICTION = "prediction_health"
    GOVERNANCE = "governance_health"
    RELATIONSHIP = "relationship_health"
    OVERALL = "overall_health"


class NarrativeSection(str, Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    CRITICAL_CHANGES = "critical_changes"
    TOP_RISKS = "top_risks"
    TOP_OPPORTUNITIES = "top_opportunities"
    DECISION_REQUESTS = "decision_requests"
    TREND_ANALYSIS = "trend_analysis"
    CONFIDENCE_SUMMARY = "confidence_summary"
    RECOMMENDED_FOCUS = "recommended_focus"


# =========================================================================
# 1. ExecutiveInsight (base type for all executive objects)
# =========================================================================

@dataclass
class ExecutiveInsight:
    """Base executive insight with full lineage traceability."""
    insight_id: str = ""
    tenant_id: int = 0
    title: str = ""
    description: str = ""
    evidence: List[str] = field(default_factory=list)
    decision_lineage: List[str] = field(default_factory=list)
    prediction_lineage: List[str] = field(default_factory=list)
    confidence: float = 0.0
    urgency: float = 0.0
    impact: float = 0.0
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.insight_id:
            raw = f"ei:{self.tenant_id}:{self.title}:{datetime.now(timezone.utc).isoformat()}"
            self.insight_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_id": self.insight_id[:12], "title": self.title[:60],
            "description": self.description[:80],
            "confidence": round(self.confidence, 4),
            "urgency": round(self.urgency, 4), "impact": round(self.impact, 4),
            "evidence": self.evidence[:3],
            "created_at": self.created_at,
        }


# =========================================================================
# 2. ExecutivePriority
# =========================================================================

@dataclass
class ExecutivePriority(ExecutiveInsight):
    """A ranked executive priority requiring attention."""
    category: str = PriorityCategory.CRITICAL_COMMITMENT.value
    entity_id: str = ""
    entity_type: str = "execution"
    attention_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"category": self.category, "entity_id": self.entity_id[:12],
                   "attention_score": round(self.attention_score, 4)})
        return d


# =========================================================================
# 3. ExecutiveRisk
# =========================================================================

@dataclass
class ExecutiveRisk(ExecutiveInsight):
    """An executive-level risk aggregation."""
    category: str = RiskCategory.OPERATIONAL.value
    likelihood: float = 0.5
    impact: float = 0.5
    trend: str = "stable"          # increasing, stable, decreasing
    affected_entities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"category": self.category, "likelihood": round(self.likelihood, 4),
                   "trend": self.trend})
        return d


# =========================================================================
# 4. ExecutiveOpportunity
# =========================================================================

@dataclass
class ExecutiveOpportunity(ExecutiveInsight):
    """An executive-level opportunity."""
    category: str = OpportunityCategory.GROWTH.value
    expected_value: float = 0.0
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"category": self.category,
                   "expected_value": round(self.expected_value, 4)})
        return d


# =========================================================================
# 5. ExecutiveDecisionRequest
# =========================================================================

@dataclass
class ExecutiveDecisionRequest:
    """A decision surfaced for leadership attention."""
    request_id: str = ""
    tenant_id: int = 0
    summary: str = ""
    available_options: List[Dict[str, Any]] = field(default_factory=list)
    tradeoffs: List[Dict[str, Any]] = field(default_factory=list)
    constraint_summary: List[str] = field(default_factory=list)
    prediction_summary: List[str] = field(default_factory=list)
    governance_implications: List[str] = field(default_factory=list)
    recommended_review_level: str = "standard"
    urgency: float = 0.5
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.request_id:
            raw = f"edr:{self.tenant_id}:{self.summary}:{datetime.now(timezone.utc).isoformat()}"
            self.request_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id[:12], "summary": self.summary[:60],
            "option_count": len(self.available_options),
            "recommended_review_level": self.recommended_review_level,
            "urgency": round(self.urgency, 4),
        }


# =========================================================================
# 6. ExecutiveHealth
# =========================================================================

@dataclass
class ExecutiveHealth:
    """Multi-dimensional health view with trend awareness."""
    tenant_id: int = 0
    dimensions: Dict[str, float] = field(default_factory=dict)
    trends: Dict[str, str] = field(default_factory=dict)
    overall: float = 0.0
    overall_trend: str = "stable"
    critical_dimensions: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": round(self.overall, 4),
            "overall_trend": self.overall_trend,
            "dimensions": {k: round(v, 4) for k, v in self.dimensions.items()},
            "trends": self.trends,
            "critical_dimensions": self.critical_dimensions,
        }


# =========================================================================
# 7. ExecutiveTrend
# =========================================================================

@dataclass
class ExecutiveTrend:
    """A trend detected from operational data."""
    trend_id: str = ""
    tenant_id: int = 0
    dimension: str = ""
    direction: str = "stable"   # increasing, decreasing, stable
    magnitude: float = 0.0
    period: str = "7d"
    evidence: List[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend_id": self.trend_id[:12], "dimension": self.dimension,
            "direction": self.direction, "magnitude": round(self.magnitude, 4),
            "period": self.period,
        }


# =========================================================================
# 8. ExecutiveNarrative
# =========================================================================

@dataclass
class ExecutiveNarrative:
    """Structured executive briefing, never hallucinated."""
    narrative_id: str = ""
    tenant_id: int = 0
    sections: Dict[str, str] = field(default_factory=dict)
    reference_artifacts: List[str] = field(default_factory=list)
    confidence: float = 0.0
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.narrative_id:
            raw = f"en:{self.tenant_id}:{datetime.now(timezone.utc).isoformat()}"
            self.narrative_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "narrative_id": self.narrative_id[:12],
            "section_count": len(self.sections),
            "reference_artifacts": len(self.reference_artifacts),
            "confidence": round(self.confidence, 4),
        }


# =========================================================================
# 9. ExecutiveDigest (aggregate brief)
# =========================================================================

@dataclass
class ExecutiveDigest:
    """Complete executive digest — the output of a synthesis cycle."""
    digest_id: str = ""
    tenant_id: int = 0
    brief: Optional[ExecutiveBrief] = None
    priorities: List[ExecutivePriority] = field(default_factory=list)
    risks: List[ExecutiveRisk] = field(default_factory=list)
    opportunities: List[ExecutiveOpportunity] = field(default_factory=list)
    decisions: List[ExecutiveDecisionRequest] = field(default_factory=list)
    health: Optional[ExecutiveHealth] = None
    narrative: Optional[ExecutiveNarrative] = None
    attention: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.digest_id:
            raw = f"dig:{self.tenant_id}:{datetime.now(timezone.utc).isoformat()}"
            self.digest_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "digest_id": self.digest_id[:12], "tenant_id": self.tenant_id,
            "priorities": len(self.priorities),
            "risks": len(self.risks), "opportunities": len(self.opportunities),
            "decisions": len(self.decisions),
            "health": self.health.to_dict() if self.health else None,
            "narrative_sections": len(self.narrative.sections) if self.narrative else 0,
            "attention_items": len(self.attention),
        }


# =========================================================================
# 10. ExecutiveBrief (summary)
# =========================================================================

@dataclass
class ExecutiveBrief:
    """High-level executive summary."""
    brief_id: str = ""
    tenant_id: int = 0
    summary: str = ""
    critical_count: int = 0
    risk_count: int = 0
    opportunity_count: int = 0
    decision_count: int = 0
    overall_health: float = 0.0
    confidence: float = 0.0
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brief_id": self.brief_id[:12], "summary": self.summary[:80],
            "critical_count": self.critical_count, "risk_count": self.risk_count,
            "opportunity_count": self.opportunity_count,
            "decision_count": self.decision_count,
            "overall_health": round(self.overall_health, 4),
            "confidence": round(self.confidence, 4),
        }


# =========================================================================
# 11. AttentionScore
# =========================================================================

@dataclass
class AttentionScore:
    """Decomposed attention score for a single item."""
    item_id: str = ""
    label: str = ""
    category: str = ""
    total_score: float = 0.0
    business_impact: float = 0.0
    urgency: float = 0.0
    confidence: float = 0.0
    strategic_importance: float = 0.0
    cross_functional_effect: float = 0.0
    time_sensitivity: float = 0.0
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id[:12], "label": self.label[:40],
            "category": self.category,
            "total_score": round(self.total_score, 4),
            "factors": {"business_impact": round(self.business_impact, 4),
                        "urgency": round(self.urgency, 4),
                        "confidence": round(self.confidence, 4),
                        "strategic_importance": round(self.strategic_importance, 4),
                        "cross_functional_effect": round(self.cross_functional_effect, 4),
                        "time_sensitivity": round(self.time_sensitivity, 4)},
        }


# =========================================================================
# 12. Runtime Types
# =========================================================================

@dataclass
class ExecutiveConfig:
    """Configuration for Executive Intelligence."""
    synthesis_interval_hours: float = 6.0
    max_priorities: int = 10
    max_risks: int = 10
    max_opportunities: int = 5
    max_decisions: int = 5
    attention_factors: Dict[str, float] = field(default_factory=lambda: {
        "business_impact": 0.25, "urgency": 0.20, "confidence": 0.15,
        "strategic_importance": 0.15, "cross_functional_effect": 0.10,
        "time_sensitivity": 0.15,
    })
    version: str = "mi6.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_priorities": self.max_priorities, "max_risks": self.max_risks,
            "max_opportunities": self.max_opportunities,
            "max_decisions": self.max_decisions, "version": self.version,
        }


@dataclass
class ExecutiveStats:
    """Executive Intelligence statistics."""
    total_digests: int = 0
    total_priorities: int = 0
    total_risks: int = 0
    total_opportunities: int = 0
    total_decisions: int = 0
    avg_confidence: float = 0.0
    avg_health: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_digests": self.total_digests,
            "total_priorities": self.total_priorities,
            "total_risks": self.total_risks,
            "total_opportunities": self.total_opportunities,
            "total_decisions": self.total_decisions,
            "avg_confidence": round(self.avg_confidence, 4),
            "avg_health": round(self.avg_health, 4),
        }