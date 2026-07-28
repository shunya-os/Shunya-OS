"""SHUNYA Intelligence Runtime — shared models.

Defines the common dataclasses used by all Intelligence Engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EngineStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"


@dataclass
class EngineInput:
    """Input to any Intelligence Engine."""

    input_type: str
    payload: dict[str, Any]
    context: dict[str, Any] | None = None
    trace_id: str = ""
    confidence_threshold: float = 0.7

    def __post_init__(self):
        if not self.trace_id:
            from core.kernel.types import generate_uuid7
            self.trace_id = generate_uuid7()


@dataclass
class EngineOutput:
    """Output from any Intelligence Engine."""

    output_type: str
    payload: dict[str, Any]
    confidence: float = 0.0
    confidence_factors: dict[str, float] = field(default_factory=dict)
    deterministic: bool = True
    trace_id: str = ""
    escalation_used: bool = False
    processing_time_ms: float = 0.0


@dataclass
class EscalationResult:
    """Result of escalating to an external AI inference provider."""

    input_type: str
    prompt: str
    context: dict[str, Any] | None = None
    trace_id: str = ""


@dataclass
class Observation:
    """A structured observation produced by the Perception Engine."""

    observation_id: str = ""
    input_type: str = ""
    source: str = ""
    priority: str = "normal"
    summary: str = ""
    raw_payload: dict[str, Any] = field(default_factory=dict)
    enriched: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    timestamp: str = ""
    trace_id: str = ""

    def __post_init__(self):
        if not self.observation_id:
            from core.kernel.types import generate_uuid7
            self.observation_id = generate_uuid7()
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class Context:
    """Assembled context for a reasoning request."""

    context_id: str = ""
    observations: list[Observation] = field(default_factory=list)
    timeline_events: list[dict[str, Any]] = field(default_factory=list)
    evidence_items: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    knowledge_facts: list[dict[str, Any]] = field(default_factory=list)
    memory_records: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    assembled_at: str = ""

    def __post_init__(self):
        if not self.context_id:
            from core.kernel.types import generate_uuid7
            self.context_id = generate_uuid7()
        if not self.assembled_at:
            self.assembled_at = datetime.now(timezone.utc).isoformat()


@dataclass
class Plan:
    """A structured plan produced by the Planning Engine."""

    objective: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    estimated_duration: str = ""
    risks: list[dict[str, Any]] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    confidence: float = 0.0
    plan_id: str = ""

    def __post_init__(self):
        if not self.plan_id:
            from core.kernel.types import generate_uuid7
            self.plan_id = generate_uuid7()


@dataclass
class Decision:
    """A decision in the decision lifecycle."""

    decision_id: str = ""
    label: str = ""
    description: str = ""
    status: str = "candidate"
    options: list[dict[str, Any]] = field(default_factory=list)
    selected_option: dict[str, Any] | None = None
    confidence: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)
    owner: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.decision_id:
            from core.kernel.types import generate_uuid7
            self.decision_id = generate_uuid7()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


@dataclass
class ReflectionRecord:
    """A reflection record produced by the Reflection Engine."""

    reflection_id: str = ""
    subject_id: str = ""
    subject_type: str = ""
    expected_outcome: dict[str, Any] | None = None
    actual_outcome: dict[str, Any] | None = None
    success_score: float = 0.0
    anomalies: list[str] = field(default_factory=list)
    improvement_signals: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.reflection_id:
            from core.kernel.types import generate_uuid7
            self.reflection_id = generate_uuid7()
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class Pattern:
    """A learned pattern produced by the Learning Engine."""

    pattern_id: str = ""
    pattern_type: str = ""
    description: str = ""
    confidence: float = 0.0
    support_count: int = 0
    evidence_ids: list[str] = field(default_factory=list)
    created_at: str = ""
    last_observed: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.pattern_id:
            from core.kernel.types import generate_uuid7
            self.pattern_id = generate_uuid7()
        if not self.created_at:
            self.created_at = now
        if not self.last_observed:
            self.last_observed = now