"""SHUNYA — Executor Engine (Phase I — ES-005).

The Executor Engine transforms governance-approved plans into real-world
actions. It is the bridge between *what should be done* (Planner + Governance)
and *what actually happens* (the real world).

The engine implements a deterministic 9-stage pipeline:
  1. Execution Preparation
  2. Dependency Verification
  3. Resource Acquisition
  4. Task Dispatch
  5. Execution Monitoring
  6. Evidence Collection
  7. Completion Verification
  8. Outcome Packaging
  9. Observation Handoff

The engine does NOT:
  - Reason about tasks or outcomes (Reasoning Engine)
  - Create or modify plans (Planner Engine)
  - Approve or reject plans (Governance Engine)
  - Learn from execution outcomes (Learning Engine)
  - Modify knowledge facts (Knowledge Engine)
  - Bypass governance (Governance Engine)

Architectural authority: ES-005 — Executor Engine Specification
"""

from app.shunya.executor_engine.models import (
    # Enums
    WorkflowState, TaskState, ExecutionType,
    BackoffStrategy, FailureType,

    # Core models
    RetryPolicy, Compensation, ExecutionFailure,
    ExecutionEvidence, Checkpoint,
    Task, Workflow,
    ExecutionMetrics, OutcomePackage,
    ExecutorInput, ExecutorOutput,
    ExecutorStats,
)

from app.shunya.executor_engine.engine import (
    ExecutorEngine, get_executor_engine, reset_executor_engine,
    ExecutorChannelAdapter, TaskExecutorFn,
)

# Legacy backward-compatible exports
from app.shunya.executor_engine._legacy_executor import (
    ExecutorLayer,
)

__all__ = [
    # Enums
    "WorkflowState", "TaskState", "ExecutionType",
    "BackoffStrategy", "FailureType",

    # Models
    "RetryPolicy", "Compensation", "ExecutionFailure",
    "ExecutionEvidence", "Checkpoint",
    "Task", "Workflow",
    "ExecutionMetrics", "OutcomePackage",
    "ExecutorInput", "ExecutorOutput",
    "ExecutorStats",

    # Engine
    "ExecutorEngine", "get_executor_engine", "reset_executor_engine",
    "ExecutorChannelAdapter", "TaskExecutorFn",

    # Legacy
    "ExecutorLayer",
]