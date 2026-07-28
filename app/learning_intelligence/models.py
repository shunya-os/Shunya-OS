"""SHUNYA — Learning Intelligence canonical models (Milestone II).

All learning artifacts: deterministic patterns, outcome profiles,
confidence factors, similarity results, organizational insights,
knowledge evolution epochs, and learning memory entries.

Architectural authority: ES-013 — Learning Intelligence
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

class LearningCategory(str, Enum):
    """Categories of learning that the engine can produce."""
    PATTERN = "pattern"
    OUTCOME_PROFILE = "outcome_profile"
    RECOMMENDATION = "recommendation"
    CONFIDENCE = "confidence"
    SIMILARITY = "similarity"
    ORGANIZATIONAL = "organizational"
    KNOWLEDGE_EVOLUTION = "knowledge_evolution"


class PatternStrength(str, Enum):
    """Strength classification for a discovered pattern."""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    INCONCLUSIVE = "inconclusive"


class ConfidenceFactor(str, Enum):
    """Explicit factors that contribute to confidence scores."""
    SAMPLE_SIZE = "sample_size"
    CONSISTENCY = "consistency"
    RECENCY = "recency"
    EVIDENCE_QUALITY = "evidence_quality"
    DEVIATION_MAGNITUDE = "deviation_magnitude"
    CROSS_VALIDATION = "cross_validation"
    TENANT_MATURITY = "tenant_maturity"


class SimilarityMetric(str, Enum):
    """Metrics used for similarity computation."""
    STATE_MATCH = "state_match"
    OBLIGATION_TYPE_MATCH = "obligation_type_match"
    OUTCOME_MATCH = "outcome_match"
    DURATION_PROXIMITY = "duration_proximity"
    RESOURCE_PATTERN = "resource_pattern"


# =========================================================================
# 1. Pattern Recognition
# =========================================================================

@dataclass
class LearnedPattern:
    """A recurring pattern identified from execution outcomes."""
    pattern_id: str = ""
    tenant_id: int = 0
    name: str = ""
    description: str = ""
    category: str = LearningCategory.PATTERN.value
    strength: str = PatternStrength.INCONCLUSIVE.value
    frequency: int = 0
    confidence: float = 0.0
    signature: str = ""                     # hash of the pattern's defining characteristics
    observation_ids: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    first_observed: str = ""
    last_observed: str = ""

    def __post_init__(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        if not self.pattern_id:
            raw = f"{self.tenant_id}:{self.signature}:{now}"
            self.pattern_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.first_observed:
            self.first_observed = now
        if not self.last_observed:
            self.last_observed = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id, "tenant_id": self.tenant_id,
            "name": self.name, "description": self.description,
            "strength": self.strength, "frequency": self.frequency,
            "confidence": self.confidence, "signature": self.signature,
            "observation_count": len(self.observation_ids),
            "evidence": self.evidence,
            "first_observed": self.first_observed,
            "last_observed": self.last_observed,
        }


# =========================================================================
# 2. Outcome Learning
# =========================================================================

@dataclass
class OutcomeProfile:
    """Success/failure profile for a dimension of execution."""
    profile_id: str = ""
    tenant_id: int = 0
    dimension: str = ""                     # commitment_type, obl_type, resource_type
    dimension_value: str = ""
    total_outcomes: int = 0
    successful: int = 0
    failed: int = 0
    success_rate: float = 0.0
    avg_duration_seconds: Optional[float] = None
    evidence: List[str] = field(default_factory=list)
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.profile_id:
            raw = f"{self.tenant_id}:{self.dimension}:{self.dimension_value}"
            self.profile_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "tenant_id": self.tenant_id,
            "dimension": self.dimension, "dimension_value": self.dimension_value,
            "total_outcomes": self.total_outcomes,
            "successful": self.successful, "failed": self.failed,
            "success_rate": round(self.success_rate, 4),
            "avg_duration_seconds": self.avg_duration_seconds,
        }


# =========================================================================
# 3. Recommendation Learning
# =========================================================================

@dataclass
class RefinedRecommendation:
    """A next-action recommendation refined by historical outcomes."""
    recommendation_id: str = ""
    tenant_id: int = 0
    action_type: str = ""                   # unblock_obligation, satisfy_obligation, etc.
    context_signature: str = ""             # hash of the triggering conditions
    historical_success_rate: float = 0.0
    historical_count: int = 0
    confidence: float = 0.0
    priority_adjustment: int = 0            # shift from default priority
    evidence: List[str] = field(default_factory=list)
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.recommendation_id:
            raw = f"{self.tenant_id}:{self.action_type}:{self.context_signature}"
            self.recommendation_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "tenant_id": self.tenant_id,
            "action_type": self.action_type,
            "historical_success_rate": round(self.historical_success_rate, 4),
            "historical_count": self.historical_count,
            "confidence": round(self.confidence, 4),
            "priority_adjustment": self.priority_adjustment,
        }


# =========================================================================
# 4. Confidence Model
# =========================================================================

@dataclass
class FactorContribution:
    """A single factor's contribution to a confidence score."""
    factor: str = ""
    value: float = 0.0
    weight: float = 1.0
    contribution: float = 0.0
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor": self.factor, "value": self.value,
            "weight": self.weight, "contribution": round(self.contribution, 4),
            "explanation": self.explanation,
        }


@dataclass
class ConfidenceAssessment:
    """Full confidence score with factor breakdown."""
    assessment_id: str = ""
    tenant_id: int = 0
    target_type: str = ""                   # pattern, profile, recommendation
    target_id: str = ""
    overall: float = 0.0
    factors: List[FactorContribution] = field(default_factory=list)
    assessed_at: str = ""

    def __post_init__(self) -> None:
        if not self.assessment_id:
            raw = f"{self.tenant_id}:{self.target_type}:{self.target_id}:{datetime.now(timezone.utc).isoformat()}"
            self.assessment_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.assessed_at:
            self.assessed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "tenant_id": self.tenant_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "overall": round(self.overall, 4),
            "factors": [f.to_dict() for f in self.factors],
            "assessed_at": self.assessed_at,
        }


# =========================================================================
# 5. Similarity Engine
# =========================================================================

@dataclass
class SimilarExecution:
    """A single similar execution match."""
    source_exec_id: str = ""
    target_exec_id: str = ""
    similarity_score: float = 0.0
    matching_dimensions: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_exec_id": self.source_exec_id,
            "target_exec_id": self.target_exec_id,
            "similarity_score": round(self.similarity_score, 4),
            "matching_dimensions": self.matching_dimensions,
        }


@dataclass
class SimilarityResult:
    """Complete similarity query result."""
    query_exec_id: str = ""
    tenant_id: int = 0
    matches: List[SimilarExecution] = field(default_factory=list)
    total_candidates: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_exec_id": self.query_exec_id,
            "tenant_id": self.tenant_id,
            "matches": [m.to_dict() for m in self.matches],
            "total_candidates": self.total_candidates,
        }


# =========================================================================
# 6. Organizational Learning
# =========================================================================

@dataclass
class OrgLearningInsight:
    """A learning insight specific to an organizational unit or role."""
    insight_id: str = ""
    tenant_id: int = 0
    unit_id: str = ""
    role_id: str = ""
    dimension: str = ""
    observation: str = ""
    success_rate: float = 0.0
    sample_count: int = 0
    evidence: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.insight_id:
            raw = f"{self.tenant_id}:{self.unit_id}:{self.role_id}:{self.dimension}:{datetime.now(timezone.utc).isoformat()}"
            self.insight_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_id": self.insight_id, "tenant_id": self.tenant_id,
            "unit_id": self.unit_id[:12] if self.unit_id else "",
            "role_id": self.role_id[:12] if self.role_id else "",
            "dimension": self.dimension, "observation": self.observation,
            "success_rate": round(self.success_rate, 4),
            "sample_count": self.sample_count,
        }


@dataclass
class OrgLearningProfile:
    """Aggregated learning profile for a tenant."""
    tenant_id: int
    total_patterns: int = 0
    total_profiles: int = 0
    total_insights: int = 0
    top_patterns: List[LearnedPattern] = field(default_factory=list)
    top_insights: List[OrgLearningInsight] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "total_patterns": self.total_patterns,
            "total_profiles": self.total_profiles,
            "total_insights": self.total_insights,
            "top_patterns": [p.to_dict() for p in self.top_patterns[:5]],
            "top_insights": [i.to_dict() for i in self.top_insights[:5]],
        }


# =========================================================================
# 7. Knowledge Evolution
# =========================================================================

@dataclass
class EvolutionEntry:
    """A single entry in the evolution of a learned insight."""
    entry_id: str = ""
    artifact_id: str = ""
    tenant_id: int = 0
    previous_confidence: float = 0.0
    new_confidence: float = 0.0
    previous_success_rate: float = 0.0
    new_success_rate: float = 0.0
    sample_delta: int = 0
    reason: str = ""
    recorded_at: str = ""

    def __post_init__(self) -> None:
        if not self.entry_id:
            raw = f"{self.tenant_id}:{self.artifact_id}:{datetime.now(timezone.utc).isoformat()}"
            self.entry_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.recorded_at:
            self.recorded_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id, "artifact_id": self.artifact_id,
            "previous_confidence": round(self.previous_confidence, 4),
            "new_confidence": round(self.new_confidence, 4),
            "previous_success_rate": round(self.previous_success_rate, 4),
            "new_success_rate": round(self.new_success_rate, 4),
            "sample_delta": self.sample_delta,
            "reason": self.reason, "recorded_at": self.recorded_at,
        }


@dataclass
class KnowledgeEpoch:
    """A versioned snapshot of learning state at a point in time."""
    epoch_id: str = ""
    tenant_id: int = 0
    label: str = ""
    pattern_count: int = 0
    profile_count: int = 0
    confidence_distribution: Dict[str, int] = field(default_factory=dict)
    recorded_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch_id": self.epoch_id, "tenant_id": self.tenant_id,
            "label": self.label,
            "pattern_count": self.pattern_count,
            "profile_count": self.profile_count,
            "confidence_distribution": self.confidence_distribution,
            "recorded_at": self.recorded_at,
        }


# =========================================================================
# 8. Learning Memory
# =========================================================================

@dataclass
class LearningArtifact:
    """A stored learning artifact — pattern, profile, or insight."""
    artifact_id: str = ""
    tenant_id: int = 0
    artifact_type: str = LearningCategory.PATTERN.value
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    created_at: str = ""
    superseded_at: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raw = f"{self.tenant_id}:{self.artifact_type}:{datetime.now(timezone.utc).isoformat()}"
            self.artifact_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id, "tenant_id": self.tenant_id,
            "artifact_type": self.artifact_type,
            "confidence": round(self.confidence, 4),
            "created_at": self.created_at,
            "superseded_at": self.superseded_at,
        }


@dataclass
class LearningMemoryEntry:
    """A single entry in the learning memory ring buffer."""
    artifact_id: str
    tenant_id: int
    artifact_type: str
    confidence: float
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id, "tenant_id": self.tenant_id,
            "artifact_type": self.artifact_type,
            "confidence": round(self.confidence, 4),
            "created_at": self.created_at,
        }


# =========================================================================
# 9. Runtime Types
# =========================================================================

@dataclass
class LearnerConfig:
    """Configuration for the Learning Intelligence Engine."""
    min_pattern_frequency: int = 3
    confidence_sample_threshold: int = 5
    similarity_match_threshold: float = 0.5
    max_similarity_matches: int = 10
    learning_memory_size: int = 500
    evolution_decay_hours: float = 720.0    # 30 days
    version: str = "mi2.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_pattern_frequency": self.min_pattern_frequency,
            "confidence_sample_threshold": self.confidence_sample_threshold,
            "similarity_match_threshold": self.similarity_match_threshold,
            "max_similarity_matches": self.max_similarity_matches,
            "learning_memory_size": self.learning_memory_size,
            "evolution_decay_hours": self.evolution_decay_hours,
            "version": self.version,
        }


@dataclass
class LearnerFilter:
    """Filter for querying learning intelligence."""
    tenant_id: Optional[int] = None
    categories: Optional[List[str]] = None
    min_confidence: Optional[float] = None
    limit: int = 50
    offset: int = 0


@dataclass
class LearnerStats:
    """Learning Intelligence statistics."""
    total_patterns: int = 0
    total_profiles: int = 0
    total_recommendations: int = 0
    total_assessments: int = 0
    total_insights: int = 0
    total_artifacts: int = 0
    memory_utilization_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_patterns": self.total_patterns,
            "total_profiles": self.total_profiles,
            "total_recommendations": self.total_recommendations,
            "total_assessments": self.total_assessments,
            "total_insights": self.total_insights,
            "total_artifacts": self.total_artifacts,
            "memory_utilization_pct": round(self.memory_utilization_pct, 1),
        }
