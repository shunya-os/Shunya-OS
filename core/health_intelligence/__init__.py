"""Universal Health Intelligence — UCP-10.

Model health for individuals and organizations.
Health extends beyond medicine. Not medical software, not wellness app. Model Health.

Composes exclusively from frozen SHUNYA UCPs:
  - Journey, Relationship, Financial, Knowledge,
    Decision, Agreement, Asset, Initiative

No Health Runtime. No Medical Runtime. No Wellness Runtime.
"""

from core.health_intelligence.engine import HealthIntelligenceEngine
from core.health_intelligence.models import (
    HealthCondition,
    HealthDimension,
    HealthMetric,
    HealthMetricType,
    HealthProfile,
    HealthRecommendation,
    HealthSeverity,
    HealthStatus,
    WellnessActivity,
)
from core.health_intelligence.runtime import HealthIntelligenceRuntime

__all__ = [
    # Runtime
    "HealthIntelligenceRuntime",
    "HealthIntelligenceEngine",
    # Models
    "HealthProfile",
    "HealthMetric",
    "HealthCondition",
    "HealthRecommendation",
    "WellnessActivity",
    # Enums
    "HealthDimension",
    "HealthMetricType",
    "HealthSeverity",
    "HealthStatus",
]