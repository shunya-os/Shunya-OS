"""Universal Health Intelligence — Data Models.

Health Intelligence models health for individuals and organizations.
Health extends beyond medicine.

Every Living Object has:
  identity (UUID), time (created_at/updated_at),
  space (owner_id), reality (notify), evidence (evidence_ids).

Every recommendation exposes:
  reasoning, evidence, confidence, assumptions, alternatives, expected impact.

UCP-10 — Universal Health Intelligence.
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


# ── Enums ────────────────────────────────────────────────────────────────


class HealthDimension(str, Enum):
    """The dimensions of health this UCP models."""

    PERSONAL = "personal"
    MEDICAL_HISTORY = "medical_history"
    WELLNESS = "wellness"
    PREVENTIVE_CARE = "preventive_care"
    MENTAL_WELLBEING = "mental_wellbeing"
    ORGANIZATIONAL = "organizational"
    TEAM = "team"
    FINANCIAL_HEALTH = "financial_health"
    INITIATIVE_HEALTH = "initiative_health"
    RELATIONSHIP_HEALTH = "relationship_health"


class HealthSeverity(str, Enum):
    """Severity of a health condition or indicator."""

    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    MINIMAL = "minimal"
    UNKNOWN = "unknown"


class HealthStatus(str, Enum):
    """Overall health status."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    AT_RISK = "at_risk"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthMetricType(str, Enum):
    """Types of health metrics that can be tracked."""

    # Personal / Physical
    STEPS = "steps"
    SLEEP_HOURS = "sleep_hours"
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE = "blood_pressure"
    WEIGHT = "weight"
    BMI = "bmi"
    EXERCISE_MINUTES = "exercise_minutes"
    WATER_INTAKE = "water_intake"
    CALORIES = "calories"
    BLOOD_SUGAR = "blood_sugar"
    CHOLESTEROL = "cholesterol"
    # Mental Wellbeing
    STRESS_LEVEL = "stress_level"
    MOOD_SCORE = "mood_score"
    MINDFULNESS_MINUTES = "mindfulness_minutes"
    SOCIAL_INTERACTIONS = "social_interactions"
    # Preventive
    SCREENING_DATE = "screening_date"
    VACCINATION_STATUS = "vaccination_status"
    CHECKUP_FREQUENCY = "checkup_frequency"
    # Organizational / Team
    TEAM_SATISFACTION = "team_satisfaction"
    WORK_LIFE_BALANCE = "work_life_balance"
    BURNOUT_RISK = "burnout_risk"
    ABSENTEEISM = "absenteeism"
    TURNOVER_RISK = "turnover_risk"
    # Custom
    CUSTOM = "custom"


# ── Data Models ──────────────────────────────────────────────────────────


@dataclass
class HealthRecommendation:
    """A recommendation with full explainability.

    Every recommendation exposes: reasoning, evidence, confidence,
    assumptions, alternatives, expected impact.
    """

    rec_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    priority: str = "medium"
    reasoning: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    expected_impact: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rec_id": self.rec_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "reasoning": self.reasoning,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
            "assumptions": list(self.assumptions),
            "alternatives": list(self.alternatives),
            "expected_impact": self.expected_impact,
        }


@dataclass
class HealthMetric:
    """A single health data point.

    Every Living Object pattern: identity (metric_id), time (recorded_at),
    space (owner_id), evidence (evidence_ids).
    """

    metric_id: str = field(default_factory=_generate_id)
    metric_type: str = HealthMetricType.CUSTOM.value
    value: float = 0.0
    unit: str = ""
    recorded_at: str = field(default_factory=_now_iso)
    owner_id: str = ""
    notes: str = ""
    source: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "metric_type": self.metric_type,
            "value": self.value,
            "unit": self.unit,
            "recorded_at": self.recorded_at,
            "owner_id": self.owner_id,
            "notes": self.notes,
            "source": self.source,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass
class HealthCondition:
    """A health condition — medical, wellness, or otherwise.

    identity (condition_id), time (diagnosed_at/updated_at),
    space (owner_id), evidence (evidence_ids).
    """

    condition_id: str = field(default_factory=_generate_id)
    name: str = ""
    description: str = ""
    dimension: str = HealthDimension.MEDICAL_HISTORY.value
    severity: str = HealthSeverity.UNKNOWN.value
    status: str = HealthStatus.UNKNOWN.value
    diagnosed_at: str = ""
    updated_at: str = field(default_factory=_now_iso)
    owner_id: str = ""
    managed: bool = False
    notes: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    related_metrics: list[str] = field(default_factory=list)
    recommendations: list[HealthRecommendation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "name": self.name,
            "description": self.description,
            "dimension": self.dimension,
            "severity": self.severity,
            "status": self.status,
            "diagnosed_at": self.diagnosed_at,
            "updated_at": self.updated_at,
            "owner_id": self.owner_id,
            "managed": self.managed,
            "notes": self.notes,
            "evidence_ids": list(self.evidence_ids),
            "related_metrics": list(self.related_metrics),
            "recommendations": [r.to_dict() for r in self.recommendations],
        }


@dataclass
class WellnessActivity:
    """A wellness activity (exercise, meditation, screening, etc.).

    identity (activity_id), time (performed_at/created_at),
    space (owner_id), evidence (evidence_ids).
    """

    activity_id: str = field(default_factory=_generate_id)
    name: str = ""
    activity_type: str = "exercise"
    dimension: str = HealthDimension.WELLNESS.value
    duration_minutes: float = 0.0
    intensity: str = "moderate"
    performed_at: str = field(default_factory=_now_iso)
    created_at: str = field(default_factory=_now_iso)
    owner_id: str = ""
    notes: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "name": self.name,
            "activity_type": self.activity_type,
            "dimension": self.dimension,
            "duration_minutes": self.duration_minutes,
            "intensity": self.intensity,
            "performed_at": self.performed_at,
            "created_at": self.created_at,
            "owner_id": self.owner_id,
            "notes": self.notes,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass
class HealthProfile:
    """A Living Object representing the health status of an entity.

    Every Living Object has:
      identity (profile_id), time (created_at/updated_at),
      space (owner_id), reality (notify), evidence (evidence_ids).

    Composes from:
      Journey (health history as a life journey),
      Relationship (relationship health),
      Financial (financial health),
      Knowledge (health knowledge base),
      Decision (health decisions made),
      Agreement (care agreements, insurance),
      Asset (health assets — devices, records),
      Initiative (health goals as initiatives).
    """

    profile_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    label: str = ""
    entity_type: str = "individual"  # individual, family, team, organization

    # Living Object constitution
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    evidence_ids: list[str] = field(default_factory=list)

    # Core health data
    metrics: list[HealthMetric] = field(default_factory=list)
    conditions: list[HealthCondition] = field(default_factory=list)
    activities: list[WellnessActivity] = field(default_factory=list)
    recommendations: list[HealthRecommendation] = field(default_factory=list)

    # Composition references to other UCPs (by canonical ID)
    journey_ids: list[str] = field(default_factory=list)
    relationship_ids: list[str] = field(default_factory=list)
    financial_profile_ids: list[str] = field(default_factory=list)
    knowledge_ids: list[str] = field(default_factory=list)
    decision_ids: list[str] = field(default_factory=list)
    agreement_ids: list[str] = field(default_factory=list)
    asset_ids: list[str] = field(default_factory=list)
    initiative_ids: list[str] = field(default_factory=list)

    # Metadata
    health_status: str = HealthStatus.UNKNOWN.value
    health_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    # ── Derived Properties ──────────────────────────────────────────

    @property
    def active_conditions(self) -> list[HealthCondition]:
        return [
            c for c in self.conditions
            if c.status in (HealthStatus.FAIR.value, HealthStatus.AT_RISK.value, HealthStatus.CRITICAL.value)
        ]

    @property
    def managed_conditions(self) -> list[HealthCondition]:
        return [c for c in self.conditions if c.managed]

    def recent_metrics(self, limit: int = 10) -> list[HealthMetric]:
        """Return the most recent metrics sorted by recorded_at descending."""
        sorted_m = sorted(self.metrics, key=lambda m: m.recorded_at, reverse=True)
        return sorted_m[:limit]

    def recent_activities(self, limit: int = 10) -> list[WellnessActivity]:
        sorted_a = sorted(self.activities, key=lambda a: a.performed_at, reverse=True)
        return sorted_a[:limit]

    # ── Identity & Space ────────────────────────────────────────────

    @property
    def identity(self) -> str:
        return self.profile_id

    @property
    def space(self) -> str:
        return self.owner_id

    # ── Serialization ───────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "owner_id": self.owner_id,
            "label": self.label,
            "entity_type": self.entity_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "evidence_ids": list(self.evidence_ids),
            "metrics_count": len(self.metrics),
            "conditions_count": len(self.conditions),
            "active_conditions": len(self.active_conditions),
            "activities_count": len(self.activities),
            "recommendations_count": len(self.recommendations),
            "health_status": self.health_status,
            "health_score": self.health_score,
            "compositions": {
                "journeys": len(self.journey_ids),
                "relationships": len(self.relationship_ids),
                "financial_profiles": len(self.financial_profile_ids),
                "knowledge": len(self.knowledge_ids),
                "decisions": len(self.decision_ids),
                "agreements": len(self.agreement_ids),
                "assets": len(self.asset_ids),
                "initiatives": len(self.initiative_ids),
            },
        }