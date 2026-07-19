"""SHUNYA — Observer Engine (Phase J — ES-006).

The Observer Engine transforms execution outcomes into verified observations.
It is the bridge between *what actually happened* (Executor) and *what should
change as a result* (Learning, Knowledge).

The engine implements a deterministic 9-stage pipeline:
  1. Observation Intake
  2. Evidence Validation
  3. Outcome Comparison
  4. Deviation Detection
  5. Anomaly Detection
  6. Confidence Assessment
  7. Observation Packaging
  8. Learning Handoff
  9. Knowledge Notification

The engine does NOT:
  - Execute actions (Executor Engine)
  - Create or modify plans (Planner Engine)
  - Reason (generate new conclusions) (Reasoning Engine)
  - Govern (evaluate policies) (Governance Engine)
  - Modify knowledge directly (Knowledge Engine)
  - Invent observations (must be grounded in evidence)
  - Learn from observations (Learning Engine)
  - Mutate evidence after validation (Architectural Invariant)

Architectural authority: ES-006 — Observer Engine Specification
"""

from app.shunya.observer_engine.models import (
    # Enums
    ObservationType, ObservationSeverity, EvidenceValidationStatus, FailureMode,

    # Core models
    Tolerance, ObservationVariance, ObservationState,
    EvidenceValidationResult, DeviationReport, AnomalyReport,
    LearningSignal, VerifiedObservation,
    ObserverInput, ObserverOutput,
    ObserverStats,
)

from app.shunya.observer_engine.engine import (
    ObserverEngine, get_observer_engine, reset_observer_engine,
)

# Legacy backward-compatible exports
from app.shunya.observer_engine._legacy_observer import (
    ObserverLayer,
)

__all__ = [
    # Enums
    "ObservationType", "ObservationSeverity", "EvidenceValidationStatus", "FailureMode",

    # Core models
    "Tolerance", "ObservationVariance", "ObservationState",
    "EvidenceValidationResult", "DeviationReport", "AnomalyReport",
    "LearningSignal", "VerifiedObservation",
    "ObserverInput", "ObserverOutput",
    "ObserverStats",

    # Engine
    "ObserverEngine", "get_observer_engine", "reset_observer_engine",

    # Legacy
    "ObserverLayer",
]