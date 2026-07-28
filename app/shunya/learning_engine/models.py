"""SHUNYA — Learning Engine canonical models (Phase K — ES-007).

Canonical learning data models: immutable representations of patterns,
learning recommendations, knowledge proposals, confidence calibrations,
outcome evaluations, and supporting types.

Architectural authority: ES-007 — Learning Engine Specification
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class LearningType(Enum):
    """Types of learning supported by the Learning Engine (ES-007 §5)."""
    SUPERVISED = "supervised"
    REINFORCEMENT = "reinforcement_inspired"
    RULE_REFINEMENT = "rule_refinement"
    PATTERN = "pattern_learning"
    STATISTICAL = "statistical"
    TEMPORAL = "temporal"
    COMPARATIVE = "comparative"
    HUMAN_GUIDED = "human_guided"


class PatternType(Enum):
    """Types of discovered patterns (ES-007 §6)."""
    SUCCESS = "success"
    FAILURE = "failure"
    TREND = "trend"
    ANOMALY = "anomaly"
    BEHAVIOR = "behavior"


class FrequencyTrend(Enum):
    """Trend direction for pattern frequency."""
    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"
    UNKNOWN = "unknown"


class RecurrenceType(Enum):
    """Recurrence classification for patterns (ES-007 §6)."""
    CONTINUOUS = "continuous"
    PERIODIC = "periodic"
    SPORADIC = "sporadic"
    ONE_TIME = "one_time"


class KnowledgeProposalState(Enum):
    """Lifecycle state of a knowledge proposal (ES-007 §7)."""
    PROPOSED = "proposed"
    REVIEW = "review"
    APPROVED = "approved"
    APPLIED = "applied"
    VERIFIED = "verified"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


class FailureMode(Enum):
    """Failure modes for learning processing (ES-007 §8)."""
    INSUFFICIENT_OBSERVATIONS = "insufficient_observations"
    CONFLICTING_PATTERNS = "conflicting_patterns"
    LOW_CONFIDENCE = "low_confidence"
    OVERFITTING = "overfitting"
    FALSE_LEARNING = "false_learning"
    CONCEPT_DRIFT = "concept_drift"
    LEARNING_BACKLOG = "learning_backlog"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------


@dataclass
class PatternScope:
    """Scope where a pattern applies (ES-007 §6)."""
    domains: List[str] = field(default_factory=list)
    channels: List[str] = field(default_factory=list)
    action_types: List[str] = field(default_factory=list)
    tenant_ids: List[int] = field(default_factory=list)


@dataclass
class Recurrence:
    """Recurrence classification for a pattern (ES-007 §6)."""
    type: str = RecurrenceType.CONTINUOUS.value
    period: Optional[str] = None      # "daily" | "weekly" | "monthly"
    confidence: float = 0.5
    last_occurrence: Optional[datetime] = None
    predicted_next: Optional[datetime] = None


@dataclass
class Pattern:
    """A discovered recurring pattern across observations (ES-007 §6)."""
    pattern_id: str = ""
    name: str = ""
    description: str = ""
    pattern_type: str = PatternType.TREND.value
    frequency: int = 0
    frequency_trend: str = FrequencyTrend.UNKNOWN.value
    confidence: float = 0.5
    impact: float = 0.0
    scope: Optional[PatternScope] = None
    recurrence: Optional[Recurrence] = None
    source_signal_ids: List[str] = field(default_factory=list)
    first_observed: Optional[datetime] = None
    last_observed: Optional[datetime] = None
    status: str = "active"

    def __post_init__(self) -> None:
        if not self.pattern_id:
            self.pattern_id = str(uuid.uuid4())
        if self.first_observed is None:
            self.first_observed = datetime.now(timezone.utc)
        if self.last_observed is None:
            self.last_observed = self.first_observed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "pattern_type": self.pattern_type,
            "frequency": self.frequency,
            "frequency_trend": self.frequency_trend,
            "confidence": self.confidence,
            "impact": self.impact,
            "status": self.status,
            "first_observed": self.first_observed.isoformat() if self.first_observed else None,
            "last_observed": self.last_observed.isoformat() if self.last_observed else None,
        }


@dataclass
class LearningRecommendation:
    """A structured improvement recommendation (ES-007 §3)."""
    recommendation_id: str = ""
    title: str = ""
    description: str = ""
    recommendation_type: str = ""  # "knowledge_update" | "policy_update" | "confidence_calibration"
    priority: float = 0.5
    confidence: float = 0.5
    impact_estimate: float = 0.0
    source_pattern_ids: List[str] = field(default_factory=list)
    source_signal_ids: List[str] = field(default_factory=list)
    approved: bool = False
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.recommendation_id:
            self.recommendation_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "description": self.description,
            "recommendation_type": self.recommendation_type,
            "priority": self.priority,
            "confidence": self.confidence,
            "impact_estimate": self.impact_estimate,
            "source_pattern_ids": self.source_pattern_ids,
            "approved": self.approved,
        }


@dataclass
class ConfidenceCalibration:
    """A confidence score adjustment (ES-007 §7)."""
    calibration_id: str = ""
    dimension: str = ""
    old_confidence: float = 0.0
    new_confidence: float = 0.0
    outcome_accuracy: float = 0.0
    learning_rate: float = 0.1
    source_signal_ids: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.calibration_id:
            self.calibration_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "calibration_id": self.calibration_id,
            "dimension": self.dimension,
            "old_confidence": self.old_confidence,
            "new_confidence": self.new_confidence,
            "outcome_accuracy": self.outcome_accuracy,
            "learning_rate": self.learning_rate,
        }


@dataclass
class OutcomeEvaluation:
    """Quality evaluation of an outcome against objectives (ES-007 §3)."""
    dimension: str = ""
    expected_value: Any = None
    actual_value: Any = None
    quality_score: float = 0.0      # 0.0 to 1.0
    explanation: str = ""


@dataclass
class KnowledgeProposal:
    """A proposed knowledge fact update (ES-007 §7)."""
    proposal_id: str = ""
    fact_key: str = ""
    current_value: Any = None
    proposed_value: Any = None
    proposal_type: str = ""          # "create" | "update" | "supersede"
    rationale: str = ""
    state: str = KnowledgeProposalState.PROPOSED.value
    confidence: float = 0.5
    source_recommendation_id: str = ""
    source_signal_ids: List[str] = field(default_factory=list)
    rollback_plan: str = ""
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.proposal_id:
            self.proposal_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "fact_key": self.fact_key,
            "proposal_type": self.proposal_type,
            "state": self.state,
            "confidence": self.confidence,
            "source_recommendation_id": self.source_recommendation_id,
        }


@dataclass
class PerformanceInsight:
    """Aggregated performance metric across observations."""
    dimension: str = ""
    success_rate: float = 0.0
    total_count: int = 0
    trend: str = FrequencyTrend.UNKNOWN.value
    insight: str = ""


@dataclass
class LearningInput:
    """Input contract for learning (ES-007 §2)."""
    signals: List[Dict[str, Any]] = field(default_factory=list)
    observation_ids: List[str] = field(default_factory=list)
    tenant_id: Optional[int] = None

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.signals and not self.observation_ids:
            errors.append("NO_OBSERVATIONS: nothing to learn from")
        if self.signals:
            for i, sig in enumerate(self.signals):
                conf = sig.get("confidence", 0.0)
                if conf <= 0.0:
                    errors.append(f"ZERO_CONFIDENCE: signal {i} has confidence <= 0")
        if self.tenant_id is None or self.tenant_id <= 0:
            errors.append("TENANT_MISMATCH: missing or invalid tenant_id")
        return errors


@dataclass
class LearningOutput:
    """Output contract for learning (ES-007 §3)."""
    patterns: List[Pattern] = field(default_factory=list)
    recommendations: List[LearningRecommendation] = field(default_factory=list)
    calibrations: List[ConfidenceCalibration] = field(default_factory=list)
    proposals: List[KnowledgeProposal] = field(default_factory=list)
    evaluations: List[OutcomeEvaluation] = field(default_factory=list)
    insights: List[PerformanceInsight] = field(default_factory=list)
    success: bool = True
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patterns": [p.to_dict() for p in self.patterns],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "calibrations": [c.to_dict() for c in self.calibrations],
            "proposals": [p.to_dict() for p in self.proposals],
            "success": self.success,
        }


@dataclass
class LearningStats:
    """Learning engine statistics."""
    total_cycles: int = 0
    total_signals_processed: int = 0
    patterns_discovered: int = 0
    recommendations_generated: int = 0
    calibrations_performed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_cycles": self.total_cycles,
            "total_signals_processed": self.total_signals_processed,
            "patterns_discovered": self.patterns_discovered,
            "recommendations_generated": self.recommendations_generated,
            "calibrations_performed": self.calibrations_performed,
        }