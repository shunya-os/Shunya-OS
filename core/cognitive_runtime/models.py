"""SHUNYA Cognitive Runtime — data models.

All dataclasses for sessions, states, events, policies, and plugins.
Domain-agnostic, business-neutral, no app/ coupling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar

# ── Helpers ────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _generate_id() -> str:
    from core.kernel.types import generate_uuid7
    return generate_uuid7()


# ── Pipeline Stages ─────────────────────────────────────────────────────────

class PipelineStage(str, Enum):
    """Canonical pipeline execution stages in order."""

    RECEIVED = "received"
    PERCEIVING = "perceiving"
    ASSEMBLING_CONTEXT = "assembling_context"
    REASONING = "reasoning"
    PLANNING = "planning"
    DECIDING = "deciding"
    REFLECTING = "reflecting"
    LEARNING = "learning"
    CONFIDENCE_UPDATE = "confidence_update"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in (PipelineStage.COMPLETED, PipelineStage.FAILED, PipelineStage.CANCELLED)

    @property
    def is_active(self) -> bool:
        return not self.is_terminal and self != PipelineStage.RECEIVED


# ── Session State ───────────────────────────────────────────────────────────

class SessionState(str, Enum):
    """Runtime state of a CognitiveSession."""

    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    ESCALATED = "escalated"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"

    @property
    def is_terminal(self) -> bool:
        return self in (SessionState.COMPLETED, SessionState.FAILED, SessionState.CANCELLED)


# ── Escalation State ────────────────────────────────────────────────────────

@dataclass
class EscalationRecord:
    """A single escalation event in a session."""

    escalation_id: str = field(default_factory=_generate_id)
    reason: str = ""
    engine_id: str = ""
    confidence_threshold: float = 0.7
    current_confidence: float = 0.0
    prompt: str = ""
    provider: str = ""
    response: str = ""
    cost: float = 0.0
    latency_ms: float = 0.0
    outcome: str = ""
    timestamp: str = field(default_factory=_now_iso)


# ── Cancellation State ──────────────────────────────────────────────────────

@dataclass
class CancellationState:
    """Tracks cancellation details for a session."""

    cancelled: bool = False
    reason: str = ""
    at_stage: str = ""
    timestamp: str = ""


# ── Completion State ────────────────────────────────────────────────────────

@dataclass
class CompletionState:
    """Tracks completion details for a session."""

    completed: bool = False
    final_confidence: float = 0.0
    total_duration_ms: float = 0.0
    stages_completed: list[str] = field(default_factory=list)
    stages_failed: list[str] = field(default_factory=list)
    timestamp: str = ""


# ── Performance Metrics ─────────────────────────────────────────────────────

@dataclass
class EngineTiming:
    """Timing for a single engine invocation."""

    engine_id: str = ""
    stage: str = ""
    start_time_ms: float = 0.0
    end_time_ms: float = 0.0
    duration_ms: float = 0.0
    queue_time_ms: float = 0.0
    memory_estimate_bytes: int = 0


# ── Runtime Event ───────────────────────────────────────────────────────────

@dataclass
class RuntimeEvent:
    """A canonical runtime event emitted during session execution."""

    event_type: str = ""
    session_id: str = ""
    trace_id: str = ""
    timestamp: str = field(default_factory=_now_iso)
    payload: dict[str, Any] = field(default_factory=dict)


# ── Session Trace ───────────────────────────────────────────────────────────

@dataclass
class SessionTrace:
    """Deterministic trace of a complete session execution."""

    timeline: list[RuntimeEvent] = field(default_factory=list)
    engine_timings: list[EngineTiming] = field(default_factory=list)
    confidence_evolution: list[dict[str, Any]] = field(default_factory=list)
    reasoning_chain: list[dict[str, Any]] = field(default_factory=list)
    decision_chain: list[dict[str, Any]] = field(default_factory=list)
    escalations: list[EscalationRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    resource_usage: dict[str, Any] = field(default_factory=dict)


# ── Cognitive Session ───────────────────────────────────────────────────────

@dataclass
class CognitiveSession:
    """A single cognitive execution session.

    Nothing executes outside a CognitiveSession. This is the canonical
    container for all execution state, traceability, and outcomes.
    """

    session_id: str = field(default_factory=_generate_id)
    trace_id: str = field(default_factory=_generate_id)
    actor: str = ""
    triggering_event: str = ""
    objective: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    confidence_history: list[dict[str, Any]] = field(default_factory=list)
    reasoning_history: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    engine_results: dict[str, Any] = field(default_factory=dict)
    timing: dict[str, EngineTiming] = field(default_factory=dict)
    state: SessionState = SessionState.RUNNING
    current_stage: PipelineStage = PipelineStage.RECEIVED
    cancellation: CancellationState = field(default_factory=CancellationState)
    escalation: list[EscalationRecord] = field(default_factory=list)
    completion: CompletionState = field(default_factory=CompletionState)
    trace: SessionTrace = field(default_factory=SessionTrace)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    # Class-level transition map (not a dataclass field)
    VALID_SESSION_TRANSITIONS: ClassVar[dict[SessionState, list[SessionState]]] = {
        SessionState.RUNNING: [SessionState.WAITING, SessionState.PAUSED,
                               SessionState.ESCALATED, SessionState.RETRYING,
                               SessionState.COMPLETED, SessionState.FAILED,
                               SessionState.CANCELLED],
        SessionState.WAITING: [SessionState.RUNNING, SessionState.CANCELLED,
                               SessionState.FAILED],
        SessionState.PAUSED: [SessionState.RUNNING, SessionState.CANCELLED,
                              SessionState.FAILED],
        SessionState.ESCALATED: [SessionState.RUNNING, SessionState.CANCELLED,
                                 SessionState.FAILED],
        SessionState.RETRYING: [SessionState.RUNNING, SessionState.FAILED,
                                SessionState.CANCELLED],
        SessionState.COMPLETED: [],
        SessionState.FAILED: [],
        SessionState.CANCELLED: [],
    }

    def transition_to(self, new_state: SessionState, reason: str = "") -> None:
        """Transition session state with validation."""
        allowed = self.VALID_SESSION_TRANSITIONS.get(self.state, [])
        if new_state not in allowed:
            raise ValueError(
                f"Invalid session state transition: {self.state.value} → {new_state.value}"
            )
        self.state = new_state
        self.updated_at = _now_iso()

    def add_event(self, event_type: str, payload: dict[str, Any] | None = None) -> RuntimeEvent:
        """Record a runtime event on this session's trace."""
        event = RuntimeEvent(
            event_type=event_type,
            session_id=self.session_id,
            trace_id=self.trace_id,
            payload=payload or {},
        )
        self.trace.timeline.append(event)
        return event


# ── Engine Plugin ───────────────────────────────────────────────────────────

@dataclass
class EnginePlugin:
    """Registration record for an intelligence engine in the Cognitive Runtime."""

    engine_id: str
    stage: PipelineStage
    capabilities: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    confidence_weight: float = 0.125
    parallel_safe: bool = False
    engine_ref: Any = None  # The actual engine instance (set at registration)


# ── Policies ────────────────────────────────────────────────────────────────

@dataclass
class RetryPolicy:
    """Retry behaviour on transient engine errors."""

    max_retries: int = 3
    backoff_ms: int = 100
    retryable_errors: tuple[type[Exception], ...] = (
        TimeoutError, ConnectionError, OSError,
    )


@dataclass
class TimeoutPolicy:
    """Time limits for engine and pipeline execution."""

    engine_timeout_ms: int = 30_000
    pipeline_timeout_ms: int = 300_000


@dataclass
class EscalationPolicy:
    """Controls when and how escalation to AI occurs."""

    allow_escalation: bool = True
    max_escalations_per_session: int = 20


@dataclass
class ParallelPolicy:
    """Controls parallel execution of independent stages."""

    max_parallel_stages: int = 2


@dataclass
class ConfidencePolicy:
    """Minimum confidence thresholds for session execution."""

    minimum_acceptable_confidence: float = 0.3


@dataclass
class FailurePolicy:
    """Behaviour on engine failure."""

    fail_fast: bool = True


@dataclass
class RuntimePolicies:
    """Centralised policy store. No policy is hardcoded inside engines."""

    retry: RetryPolicy = field(default_factory=RetryPolicy)
    timeout: TimeoutPolicy = field(default_factory=TimeoutPolicy)
    escalation: EscalationPolicy = field(default_factory=EscalationPolicy)
    parallel: ParallelPolicy = field(default_factory=ParallelPolicy)
    confidence: ConfidencePolicy = field(default_factory=ConfidencePolicy)
    failure: FailurePolicy = field(default_factory=FailurePolicy)


# ── Pipeline Stage Ordering ─────────────────────────────────────────────────

PIPELINE_ORDER: list[PipelineStage] = [
    PipelineStage.RECEIVED,
    PipelineStage.PERCEIVING,
    PipelineStage.ASSEMBLING_CONTEXT,
    PipelineStage.REASONING,
    PipelineStage.PLANNING,
    PipelineStage.DECIDING,
    PipelineStage.REFLECTING,
    PipelineStage.LEARNING,
    PipelineStage.CONFIDENCE_UPDATE,
    PipelineStage.COMPLETED,
]

# Safe to parallelize: (REFLECTING, LEARNING) — no data dependency
PARALLEL_GROUPS: list[tuple[PipelineStage, ...]] = [
    (PipelineStage.REFLECTING, PipelineStage.LEARNING),
]


# ── Valid Pipeline Stage Transitions ────────────────────────────────────────

VALID_PIPELINE_TRANSITIONS: dict[PipelineStage, list[PipelineStage]] = {
    PipelineStage.RECEIVED: [PipelineStage.PERCEIVING, PipelineStage.FAILED,
                             PipelineStage.CANCELLED],
    PipelineStage.PERCEIVING: [PipelineStage.ASSEMBLING_CONTEXT,
                               PipelineStage.FAILED, PipelineStage.CANCELLED],
    PipelineStage.ASSEMBLING_CONTEXT: [PipelineStage.REASONING,
                                       PipelineStage.FAILED, PipelineStage.CANCELLED],
    PipelineStage.REASONING: [PipelineStage.PLANNING, PipelineStage.FAILED,
                              PipelineStage.CANCELLED],
    PipelineStage.PLANNING: [PipelineStage.DECIDING, PipelineStage.FAILED,
                             PipelineStage.CANCELLED],
    PipelineStage.DECIDING: [PipelineStage.REFLECTING, PipelineStage.FAILED,
                             PipelineStage.CANCELLED],
    PipelineStage.REFLECTING: [PipelineStage.LEARNING, PipelineStage.FAILED,
                               PipelineStage.CANCELLED],
    PipelineStage.LEARNING: [PipelineStage.CONFIDENCE_UPDATE, PipelineStage.FAILED,
                             PipelineStage.CANCELLED],
    PipelineStage.CONFIDENCE_UPDATE: [PipelineStage.COMPLETED, PipelineStage.FAILED,
                                      PipelineStage.CANCELLED],
    PipelineStage.COMPLETED: [],
    PipelineStage.FAILED: [],
    PipelineStage.CANCELLED: [],
}


# ── Default Engine Weights ──────────────────────────────────────────────────

DEFAULT_ENGINE_WEIGHTS: dict[str, float] = {
    "perception": 0.15,
    "context_assembly": 0.12,
    "reasoning": 0.18,
    "planning": 0.12,
    "decision": 0.15,
    "reflection": 0.10,
    "learning": 0.08,
    "confidence": 0.10,
}