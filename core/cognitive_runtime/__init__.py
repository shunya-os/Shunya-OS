"""SHUNYA Cognitive Runtime.

The canonical execution layer for all intelligent behaviour in SHUNYA.
No engine is invoked directly — all execution passes through this runtime.

Phase E — implements cognition on top of Phase D intelligence engines.

Usage:
    from core.cognitive_runtime import CognitiveRuntime, CognitiveSession

    runtime = CognitiveRuntime()
    runtime.register_default_engines()
    session = runtime.create_session(actor="user", objective="Analyze data")
    result = await runtime.execute(session)
"""

from __future__ import annotations

from core.cognitive_runtime.models import (
    DEFAULT_ENGINE_WEIGHTS,
    PIPELINE_ORDER,
    VALID_PIPELINE_TRANSITIONS,
    CancellationState,
    CognitiveSession,
    CompletionState,
    EnginePlugin,
    EngineTiming,
    EscalationPolicy,
    EscalationRecord,
    FailurePolicy,
    ParallelPolicy,
    PipelineStage,
    RetryPolicy,
    RuntimeEvent,
    RuntimePolicies,
    SessionState,
    SessionTrace,
    TimeoutPolicy,
)
from core.cognitive_runtime.orchestrator import CognitiveRuntime

__all__ = [
    "DEFAULT_ENGINE_WEIGHTS",
    "PIPELINE_ORDER",
    "VALID_PIPELINE_TRANSITIONS",
    "CancellationState",
    "CognitiveRuntime",
    "CognitiveSession",
    "CompletionState",
    "EnginePlugin",
    "EngineTiming",
    "EscalationPolicy",
    "EscalationRecord",
    "FailurePolicy",
    "ParallelPolicy",
    "PipelineStage",
    "RetryPolicy",
    "RuntimeEvent",
    "RuntimePolicies",
    "SessionState",
    "SessionTrace",
    "TimeoutPolicy",
]