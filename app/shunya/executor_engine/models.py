"""SHUNYA — Executor Engine canonical models (Phase I — ES-005).

Canonical execution data models: immutable representations of workflows,
tasks, retry policies, compensations, checkpoints, execution evidence,
outcome packages, and supporting types.

Architectural authority: ES-005 — Executor Engine Specification
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class WorkflowState(Enum):
    """Lifecycle state of an execution workflow."""
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"
    AT_RISK = "at_risk"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class TaskState(Enum):
    """Lifecycle state of an individual task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    COMPENSATED = "compensated"


class ExecutionType(Enum):
    """Types of execution supported by the Executor Engine."""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    HUMAN_ASSISTED = "human_assisted"
    LONG_RUNNING = "long_running"
    BATCH = "batch"
    STREAMING = "streaming"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    DISTRIBUTED = "distributed"
    TRANSACTIONAL = "transactional"


class BackoffStrategy(Enum):
    """Retry backoff strategies."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


class FailureType(Enum):
    """Categorised failure types for execution failures."""
    TASK_FAILURE = "task_failure"
    RESOURCE_FAILURE = "resource_failure"
    NETWORK_FAILURE = "network_failure"
    TIMEOUT = "timeout"
    PARTIAL_EXECUTION = "partial_execution"
    DUPLICATE_EXECUTION = "duplicate_execution"
    COMPENSATION_FAILURE = "compensation_failure"
    EXTERNAL_DEPENDENCY_FAILURE = "external_dependency_failure"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------


@dataclass
class RetryPolicy:
    """Retry configuration for a task (ES-005 §6)."""
    max_attempts: int = 3
    backoff: str = BackoffStrategy.EXPONENTIAL.value
    initial_delay_ms: int = 1000
    max_delay_ms: int = 60000
    retryable_errors: List[str] = field(default_factory=list)
    non_retryable_errors: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.max_attempts = max(1, self.max_attempts)
        self.initial_delay_ms = max(100, self.initial_delay_ms)

    def calculate_delay(self, attempt: int) -> int:
        """Calculate delay in ms for a given retry attempt (1-indexed)."""
        if attempt < 1:
            attempt = 1
        if self.backoff == BackoffStrategy.EXPONENTIAL.value:
            delay = self.initial_delay_ms * (2 ** (attempt - 1))
        elif self.backoff == BackoffStrategy.LINEAR.value:
            delay = self.initial_delay_ms * attempt
        else:
            delay = self.initial_delay_ms
        return min(delay, self.max_delay_ms)

    def should_retry(self, attempt: int, error: str) -> bool:
        """Determine if a task should be retried after a failure."""
        if attempt >= self.max_attempts:
            return False
        if self.non_retryable_errors and any(e in error for e in self.non_retryable_errors):
            return False
        if self.retryable_errors:
            return any(e in error for e in self.retryable_errors)
        return True  # retry by default

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "backoff": self.backoff,
            "initial_delay_ms": self.initial_delay_ms,
            "max_delay_ms": self.max_delay_ms,
        }


@dataclass
class Compensation:
    """A compensation action to undo a task (ES-005 §6)."""
    action: str                 # e.g., "none", "delete_record", "refund_payment", "cancel_booking"
    task_id: str = ""           # Task this compensates
    payload: Dict[str, Any] = field(default_factory=dict)

    def is_noop(self) -> bool:
        return self.action in ("none", "", "noop")


@dataclass
class ExecutionFailure:
    """Structured failure record for a failed task (ES-005 §6)."""
    failure_type: str
    message: str
    task_id: str = ""
    error_code: str = ""
    detail: str = ""
    attempt: int = 1
    recovered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_type": self.failure_type,
            "message": self.message,
            "task_id": self.task_id,
            "error_code": self.error_code,
            "detail": self.detail,
            "attempt": self.attempt,
            "recovered": self.recovered,
        }


@dataclass
class ExecutionEvidence:
    """Proof of execution collected during/after a task (ES-005 §3)."""
    evidence_id: str = ""
    task_id: str = ""
    action: str = ""
    channel: str = ""
    recipient: str = ""
    message_id: str = ""
    success: bool = False
    response: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    tenant_id: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.evidence_id:
            self.evidence_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "task_id": self.task_id,
            "action": self.action,
            "channel": self.channel,
            "recipient": self.recipient,
            "message_id": self.message_id,
            "success": self.success,
            "response": self.response,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "tenant_id": self.tenant_id,
        }


@dataclass
class Checkpoint:
    """A resumable state snapshot of a workflow (ES-005 §6)."""
    checkpoint_id: str = ""
    workflow_id: str = ""
    task_states: Dict[str, str] = field(default_factory=dict)
    completed_task_evidence: List[str] = field(default_factory=list)
    failures: List[ExecutionFailure] = field(default_factory=list)
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.checkpoint_id:
            self.checkpoint_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


@dataclass
class Task:
    """A single executable task within a workflow (ES-005 §6)."""
    task_id: str = ""
    type: str = ExecutionType.SYNCHRONOUS.value
    action: str = ""              # "send_message", "create_record", "call_api"
    target: str = ""              # channel name, service name, API endpoint
    payload: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    state: str = TaskState.PENDING.value
    retry_policy: Optional[RetryPolicy] = None
    compensation: Optional[Compensation] = None
    timeout: int = 30             # max execution time in seconds
    evidence: Optional[ExecutionEvidence] = None
    failure: Optional[ExecutionFailure] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempt: int = 0
    tenant_id: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.task_id:
            self.task_id = str(uuid.uuid4())

    @property
    def is_completed(self) -> bool:
        return self.state == TaskState.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        return self.state == TaskState.FAILED.value

    @property
    def is_pending(self) -> bool:
        return self.state == TaskState.PENDING.value

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "type": self.type,
            "action": self.action,
            "target": self.target,
            "dependencies": self.dependencies,
            "state": self.state,
            "retry_policy": self.retry_policy.to_dict() if self.retry_policy else None,
            "compensation": self.compensation.action if self.compensation else None,
            "timeout": self.timeout,
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "failure": self.failure.to_dict() if self.failure else None,
            "attempt": self.attempt,
            "tenant_id": self.tenant_id,
        }


@dataclass
class Workflow:
    """A workflow — a set of tasks managed as a single execution unit (ES-005 §6)."""
    workflow_id: str = ""
    plan_id: str = ""
    tenant_id: Optional[int] = None
    state: str = WorkflowState.ACTIVE.value
    tasks: List[Task] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    checkpoints: List[Checkpoint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.workflow_id:
            self.workflow_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.created_at

    def find_task(self, task_id: str) -> Optional[Task]:
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None

    @property
    def completed_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.is_completed]

    @property
    def failed_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.is_failed]

    @property
    def pending_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.is_pending]

    @property
    def all_completed(self) -> bool:
        return all(t.is_completed for t in self.tasks)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "plan_id": self.plan_id,
            "tenant_id": self.tenant_id,
            "state": self.state,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class ExecutionMetrics:
    """Execution metrics for a workflow (ES-005 §3)."""
    total_tasks: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    cancelled: int = 0
    total_retries: int = 0
    total_duration_seconds: float = 0.0
    avg_task_duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tasks": self.total_tasks,
            "completed": self.completed,
            "failed": self.failed,
            "skipped": self.skipped,
            "cancelled": self.cancelled,
            "total_retries": self.total_retries,
            "total_duration_seconds": self.total_duration_seconds,
            "avg_task_duration_seconds": self.avg_task_duration_seconds,
        }


@dataclass
class OutcomePackage:
    """Complete execution result packaged for the Observer Engine (ES-005 §3)."""
    outcome_id: str = ""
    workflow_id: str = ""
    plan_id: str = ""
    tenant_id: Optional[int] = None
    workflow_state: str = ""
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[ExecutionEvidence] = field(default_factory=list)
    failures: List[ExecutionFailure] = field(default_factory=list)
    metrics: Optional[ExecutionMetrics] = None
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.outcome_id:
            self.outcome_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "workflow_id": self.workflow_id,
            "plan_id": self.plan_id,
            "tenant_id": self.tenant_id,
            "workflow_state": self.workflow_state,
            "tasks": self.tasks,
            "evidence": [e.to_dict() for e in self.evidence],
            "failures": [f.to_dict() for f in self.failures],
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class ExecutorInput:
    """Input contract for executor execution (ES-005 §2)."""
    workflow_id: str = ""
    plan_id: str = ""
    governance_approved: bool = False
    governance_audit_id: str = ""
    tenant_id: Optional[int] = None
    actor_id: str = ""
    tasks: List[Task] = field(default_factory=list)
    execution_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate input and return list of error messages. Empty = valid."""
        errors: List[str] = []
        if not self.governance_approved:
            errors.append("PLAN_NOT_APPROVED: cannot execute without governance approval")
        if not self.tasks:
            errors.append("EMPTY_PLAN: no tasks to execute")
        if self.tenant_id is None or self.tenant_id <= 0:
            errors.append("TENANT_MISMATCH: missing or invalid tenant_id")
        # Check for circular dependencies
        task_ids = {t.task_id for t in self.tasks}
        for task in self.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    errors.append(f"CIRCULAR_DEPENDENCY: task {task.task_id} references unknown dependency {dep}")
        return errors


@dataclass
class ExecutorOutput:
    """Output contract for executor results (ES-005 §3)."""
    success: bool = False
    workflow_id: str = ""
    workflow_state: str = ""
    outcome: Optional[OutcomePackage] = None
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "workflow_id": self.workflow_id,
            "workflow_state": self.workflow_state,
            "outcome": self.outcome.to_dict() if self.outcome else None,
            "errors": self.errors,
        }


@dataclass
class ExecutorStats:
    """Executor engine statistics."""
    total_workflows: int = 0
    completed: int = 0
    failed: int = 0
    partial: int = 0
    total_tasks: int = 0
    total_retries: int = 0
    adapters_registered: int = 0

    def to_dict(self) -> Dict[str, Any]:
        total = self.total_workflows or 1
        return {
            "total_workflows": self.total_workflows,
            "completed": self.completed,
            "failed": self.failed,
            "partial": self.partial,
            "completion_rate": round(self.completed / total * 100, 1),
            "total_tasks": self.total_tasks,
            "total_retries": self.total_retries,
            "adapters_registered": self.adapters_registered,
        }