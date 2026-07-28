"""SHUNYA Execution Runtime.

The authoritative orchestration layer for all real-world work.
No business capability may execute work directly.

The Cognitive Runtime decides. The Execution Runtime performs.

Usage:
    from core.execution_runtime import ExecutionRuntime, ExecutionInstance

    runtime = ExecutionRuntime()
    runtime.register_default_actions()
    instance = runtime.create_instance(action_id="noop", actor="system", objective="Test")
    result = await runtime.schedule(instance)
"""

from __future__ import annotations

from core.execution_runtime.models import (
    VALID_EXECUTION_TRANSITIONS,
    ActionContract,
    CompensationPolicy,
    ConcurrencyPolicy,
    EscalationPolicy,
    EvidenceRecord,
    ExecutionContext,
    ExecutionEvent,
    ExecutionGraph,
    ExecutionInstance,
    ExecutionPolicies,
    ExecutionState,
    ExecutionTiming,
    ExecutionTrace,
    PermissionPolicy,
    PriorityPolicy,
    RateLimitPolicy,
    RegisteredAction,
    RetryPolicy,
    RollbackPolicy,
    ScheduleRequest,
    ScheduleType,
    TimeoutPolicy,
)
from core.execution_runtime.orchestrator import ExecutionRuntime

__all__ = [
    "VALID_EXECUTION_TRANSITIONS",
    "ActionContract",
    "CompensationPolicy",
    "ConcurrencyPolicy",
    "EscalationPolicy",
    "EvidenceRecord",
    "ExecutionContext",
    "ExecutionEvent",
    "ExecutionGraph",
    "ExecutionInstance",
    "ExecutionPolicies",
    "ExecutionRuntime",
    "ExecutionState",
    "ExecutionTiming",
    "ExecutionTrace",
    "PermissionPolicy",
    "PriorityPolicy",
    "RateLimitPolicy",
    "RegisteredAction",
    "RetryPolicy",
    "RollbackPolicy",
    "ScheduleRequest",
    "ScheduleType",
    "TimeoutPolicy",
]