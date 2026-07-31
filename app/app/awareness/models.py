"""SHUNYA — Autonomous Operational Awareness canonical models (Phase N+3).

Unified event types, enrichment metadata, impact assessments, awareness
snapshots, and supporting types for the awareness layer.

Architectural authority: ES-011 — Autonomous Operational Awareness
"""

from __future__ import annotations

import hashlib, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================================================
# Enums
# =========================================================================

class ObservationCategory(str, Enum):
    """Categories of events that can be observed."""
    EXECUTION_STATE_CHANGE = "execution_state_change"
    EXECUTION_HEALTH_CHANGE = "execution_health_change"
    RISK_LEVEL_CHANGE = "risk_level_change"
    OBLIGATION_CHANGE = "obligation_change"
    RESOURCE_CHANGE = "resource_change"
    EXCEPTION_OCCURRED = "exception_occurred"
    INTELLIGENCE_OUTPUT = "intelligence_output"
    PORTFOLIO_CHANGE = "portfolio_change"
    TIMELINE_EVENT = "timeline_event"
    EXTERNAL_SIGNAL = "external_signal"
    SYSTEM_EVENT = "system_event"


class ObservationPriority(int, Enum):
    """Event priority for processing order."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4


class AwarenessLevel(str, Enum):
    """How well the system understands a given execution/tenant."""
    FULL = "full"
    PARTIAL = "partial"
    LIMITED = "limited"
    BLIND = "blind"
    STALE = "stale"


class PropagationTarget(str, Enum):
    """Targets for observation propagation."""
    EXECUTION_INTELLIGENCE = "execution_intelligence"
    AWARENESS = "awareness"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    PLANNER = "planner"
    ALL = "all"


class ImpactType(str, Enum):
    """Types of impact an observation can have."""
    STATE_CHANGE = "state_change"
    HEALTH_CHANGE = "health_change"
    RISK_CHANGE = "risk_change"
    AWARENESS_CHANGE = "awareness_change"
    KNOWLEDGE_UPDATE = "knowledge_update"
    RECOMMENDATION_CHANGE = "recommendation_change"
    NO_IMPACT = "no_impact"


# =========================================================================
# Core Models
# =========================================================================

@dataclass
class CanonicalObservation:
    """Unified event type — every system event becomes one of these.

    Carries the originating event data plus metadata for deterministic
    propagation through the awareness layer.
    """
    observation_id: str = ""
    category: str = ObservationCategory.SYSTEM_EVENT.value
    tenant_id: int = 0
    source: str = ""                  # which component generated this
    source_id: str = ""               # specific entity id (exec_id, obl_id, etc.)

    # Event payload — structured per category
    previous_state: Optional[str] = None
    current_state: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    timestamp: str = ""
    idempotency_key: str = ""
    correlation_id: str = ""

    # Enrichment (set by pipeline)
    priority: int = ObservationPriority.INFO.value
    enrichment: Optional[ObservationEnrichment] = None

    def __post_init__(self) -> None:
        now = datetime.now(timezone.utc)
        if not self.observation_id:
            raw = f"{self.source}:{self.source_id}:{now.isoformat()}"
            self.observation_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.timestamp:
            self.timestamp = now.isoformat()
        if not self.idempotency_key:
            self.idempotency_key = self.observation_id
        if not self.correlation_id:
            self.correlation_id = self.observation_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "category": self.category,
            "tenant_id": self.tenant_id,
            "source": self.source,
            "source_id": self.source_id,
            "previous_state": self.previous_state,
            "current_state": self.current_state,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "idempotency_key": self.idempotency_key,
            "correlation_id": self.correlation_id,
            "priority": self.priority,
            "enrichment": self.enrichment.to_dict() if self.enrichment else None,
        }


@dataclass
class ObservationEnrichment:
    """Contextual enrichment added by the Observation Pipeline."""
    execution_health: Optional[str] = None
    risk_level: Optional[str] = None
    awareness_level: str = AwarenessLevel.LIMITED.value
    propagation_targets: List[str] = field(default_factory=list)
    impact_assessment: Optional[ImpactAssessment] = None
    related_observations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_health": self.execution_health,
            "risk_level": self.risk_level,
            "awareness_level": self.awareness_level,
            "propagation_targets": self.propagation_targets,
            "impact_assessment": self.impact_assessment.to_dict() if self.impact_assessment else None,
            "related_observations": self.related_observations,
        }


@dataclass
class ImpactAssessment:
    """What this observation changes about the system's understanding."""
    impact_types: List[str] = field(default_factory=list)
    affected_executions: List[str] = field(default_factory=list)
    affected_tenants: List[int] = field(default_factory=list)
    description: str = ""
    severity: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "impact_types": self.impact_types,
            "affected_executions": self.affected_executions,
            "affected_tenants": self.affected_tenants,
            "description": self.description,
            "severity": self.severity,
        }


@dataclass
class AwarenessSnapshot:
    """Current awareness state for a single execution."""
    exec_id: str
    tenant_id: int
    level: str = AwarenessLevel.LIMITED.value
    last_observation_at: str = ""
    observation_count: int = 0
    enrichment: Optional[ObservationEnrichment] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exec_id": self.exec_id,
            "tenant_id": self.tenant_id,
            "level": self.level,
            "last_observation_at": self.last_observation_at,
            "observation_count": self.observation_count,
            "enrichment": self.enrichment.to_dict() if self.enrichment else None,
        }


@dataclass
class OrganizationalAwarenessState:
    """Per-tenant aggregated awareness across all executions."""
    tenant_id: int
    total_executions: int = 0
    monitored_executions: int = 0
    awareness_distribution: Dict[str, int] = field(default_factory=dict)
    overall_awareness: str = AwarenessLevel.BLIND.value
    last_activity_at: str = ""
    stale_execution_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "total_executions": self.total_executions,
            "monitored_executions": self.monitored_executions,
            "awareness_distribution": self.awareness_distribution,
            "overall_awareness": self.overall_awareness,
            "last_activity_at": self.last_activity_at,
            "stale_execution_count": self.stale_execution_count,
        }


@dataclass
class PrioritizedObservation:
    """An observation with its computed priority."""
    observation: CanonicalObservation
    priority_score: int = ObservationPriority.INFO.value
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation": self.observation.to_dict(),
            "priority_score": self.priority_score,
            "reason": self.reason,
        }


@dataclass
class AwarenessMemoryEntry:
    """A single entry in the awareness memory ring buffer."""
    observation_id: str
    category: str
    source: str
    source_id: str
    tenant_id: int
    priority: int
    timestamp: str
    payload_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "category": self.category,
            "source": self.source,
            "source_id": self.source_id,
            "tenant_id": self.tenant_id,
            "priority": self.priority,
            "timestamp": self.timestamp,
            "payload_summary": self.payload_summary,
        }


@dataclass
class RuntimeConfig:
    """Configuration for the Awareness Engine."""
    max_memory_size: int = 1000
    stale_threshold_hours: float = 72.0
    awareness_decay_hours: float = 24.0
    enable_propagation: bool = True
    enable_risk_monitoring: bool = True
    enable_organizational_awareness: bool = True
    version: str = "n+3.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_memory_size": self.max_memory_size,
            "stale_threshold_hours": self.stale_threshold_hours,
            "awareness_decay_hours": self.awareness_decay_hours,
            "enable_propagation": self.enable_propagation,
            "enable_risk_monitoring": self.enable_risk_monitoring,
            "enable_organizational_awareness": self.enable_organizational_awareness,
            "version": self.version,
        }


@dataclass
class AwarenessFilter:
    """Filter for querying awareness state."""
    tenant_id: Optional[int] = None
    exec_ids: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    min_priority: Optional[int] = None
    limit: int = 50
    offset: int = 0


@dataclass
class AwarenessStats:
    """Awareness engine statistics."""
    total_observations: int = 0
    observations_by_category: Dict[str, int] = field(default_factory=dict)
    unique_executions_monitored: int = 0
    risk_monitoring_active: bool = False
    memory_utilization_pct: float = 0.0
    total_propagations: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_observations": self.total_observations,
            "observations_by_category": self.observations_by_category,
            "unique_executions_monitored": self.unique_executions_monitored,
            "risk_monitoring_active": self.risk_monitoring_active,
            "memory_utilization_pct": round(self.memory_utilization_pct, 1),
            "total_propagations": self.total_propagations,
        }
