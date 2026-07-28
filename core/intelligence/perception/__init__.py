"""SHUNYA Perception Engine.

The Perception Engine is the entry point into the Intelligence Runtime. It
receives raw signals from the world (events, messages, state changes) and
transforms them into structured Observations that downstream engines consume.

Exports:
    PerceptionEngine: The main engine class.
    IntelligenceEngine: Abstract base class for all engines.
    EngineInput: Canonical engine input contract.
    EngineOutput: Canonical engine output contract.
    EscalationResult: Escalation bridge result.
    Observation: A structured observation produced by the Perception Engine.
    InputType: Canonical input types.
    ObservationStatus: Lifecycle status of an observation.
    PerceptionPriority: Priority levels for perception inputs.
    SourceMetadata: Source provenance metadata.
"""

from __future__ import annotations

from core.intelligence.perception.engine import IntelligenceEngine, PerceptionEngine
from core.intelligence.perception.models import (
    EngineInput,
    EngineOutput,
    EscalationResult,
    InputType,
    Observation,
    ObservationStatus,
    PerceptionPriority,
    SourceMetadata,
)

__all__ = [
    "EngineInput",
    "EngineOutput",
    "EscalationResult",
    "InputType",
    "IntelligenceEngine",
    "Observation",
    "ObservationStatus",
    "PerceptionEngine",
    "PerceptionPriority",
    "SourceMetadata",
]