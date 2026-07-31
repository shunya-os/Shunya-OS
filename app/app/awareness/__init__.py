"""SHUNYA — Autonomous Operational Awareness (Phase N+3)

Transforms system events into canonical Observations that deterministically
propagate through SHUNYA, updating execution intelligence, organizational
awareness, knowledge, and recommendations.

Architecture:
  CanonicalObservationModel   → Unified event type (6 categories)
  ObservationPipeline         → Ingest → Validate → Enrich → Propagate
  AwarenessEngine             → Continuous system awareness assessment
  ChangeImpactAnalyzer        → Determines what each observation changes
  ContinuousRiskMonitor       → Background risk that updates per observation
  OrganizationalAwareness     → Per-tenant awareness state
  EventPrioritization         → Priority scoring for observations
  AwarenessMemory             → Recent observation ring buffer
  RuntimeService              → Integration layer
  PublicAPI                   → Clean consumer interface
"""

from app.awareness.models import (
    # Core enums
    ObservationCategory, ObservationPriority, AwarenessLevel,
    PropagationTarget, ImpactType,
    # Core models
    CanonicalObservation,
    ObservationEnrichment,
    ImpactAssessment,
    AwarenessSnapshot,
    OrganizationalAwarenessState,
    PrioritizedObservation,
    AwarenessMemoryEntry,
    RuntimeConfig, AwarenessFilter, AwarenessStats,
)
from app.awareness.engine import (
    AwarenessEngine, get_awareness_engine, reset_awareness_engine,
    # Sub-engines
    ObservationPipeline,
    ChangeImpactAnalyzer,
    ContinuousRiskMonitor,
    OrganizationalAwareness,
    EventPrioritization,
    AwarenessMemory,
    RuntimeService,
)

__all__ = [
    "AwarenessEngine", "get_awareness_engine", "reset_awareness_engine",
    "ObservationPipeline", "ChangeImpactAnalyzer",
    "ContinuousRiskMonitor", "OrganizationalAwareness",
    "EventPrioritization", "AwarenessMemory", "RuntimeService",
    # Enums
    "ObservationCategory", "ObservationPriority", "AwarenessLevel",
    "PropagationTarget", "ImpactType",
    # Models
    "CanonicalObservation", "ObservationEnrichment", "ImpactAssessment",
    "AwarenessSnapshot", "OrganizationalAwarenessState",
    "PrioritizedObservation", "AwarenessMemoryEntry",
    "RuntimeConfig", "AwarenessFilter", "AwarenessStats",
]