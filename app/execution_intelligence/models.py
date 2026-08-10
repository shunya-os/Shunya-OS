"""Compatibility stub — execution_intelligence models archived during Phase 1 consolidation.

Original files: _archive/execution_variants/execution_intelligence/models.py
This stub provides minimal model classes for test compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    AT_RISK = "at_risk"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthDimension(str, Enum):
    STATE = "state"
    PROGRESS = "progress"
    TIMELINESS = "timeliness"
    RESOURCE_POSITION = "resource_position"
    EXCEPTION_BURDEN = "exception_burden"
    OBLIGATION_HEALTH = "obligation_health"
    DEPENDENCY_HEALTH = "dependency_health"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HealthAssessment:
    entity_id: str = ""
    status: HealthStatus = HealthStatus.UNKNOWN
    score: float = 0.0
    dimensions: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence: list = field(default_factory=list)


@dataclass
class TimelineSnapshot:
    entity_id: str = ""
    events: list = field(default_factory=list)
    trend: str = "stable"


@dataclass
class CompletionPrediction:
    entity_id: str = ""
    predicted_completion: Optional[str] = None
    confidence: float = 0.0
    risk_factors: list = field(default_factory=list)


@dataclass
class DependencyNode:
    id: str = ""
    type: str = "task"
    state: str = "pending"
    dependencies: list = field(default_factory=list)


@dataclass
class DependencyEdge:
    source: str = ""
    target: str = ""
    relationship: str = "depends_on"


@dataclass
class CriticalPath:
    nodes: list = field(default_factory=list)
    total_duration: float = 0.0
    risk_score: float = 0.0


@dataclass
class RiskAssessment:
    entity_id: str = ""
    level: str = "low"
    score: float = 0.0
    factors: list = field(default_factory=list)


@dataclass
class RiskFactor:
    name: str = ""
    impact: float = 0.0
    probability: float = 0.0
    description: str = ""


@dataclass
class NextAction:
    action: str = ""
    priority: str = "medium"
    entity_id: str = ""
    reason: str = ""


@dataclass
class PortfolioSummary:
    total: int = 0
    healthy: int = 0
    at_risk: int = 0
    critical: int = 0


@dataclass
class PortfolioBreakdown:
    by_type: dict = field(default_factory=dict)
    by_status: dict = field(default_factory=dict)


@dataclass
class EvidenceTrace:
    trace_id: str = ""
    events: list = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class Explanation:
    summary: str = ""
    details: str = ""
    evidence: list = field(default_factory=list)


@dataclass
class RuntimeConfig:
    max_concurrent: int = 5
    timeout_seconds: int = 300
    retry_count: int = 3


@dataclass
class QueryFilter:
    field: str = ""
    operator: str = "eq"
    value: Any = None