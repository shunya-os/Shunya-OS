"""SHUNYA Execution Runtime — data models.

Domain-agnostic execution models. No industry-specific concepts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# ── Helpers ────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _generate_id() -> str:
    from core.kernel.types import generate_uuid7
    return generate_uuid7()


# ── Execution State Machine ─────────────────────────────────────────────────

class ExecutionState(str, Enum):
    CREATED = "created"
    READY = "ready"
    QUEUED = "queued"
    EXECUTING = "executing"
    WAITING = "waiting"
    BLOCKED = "blocked"
    PARTIALLY_COMPLETED = "partially_completed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"
    EXPIRED = "expired"

    @property
    def is_terminal(self) -> bool:
        return self in TERMINAL_STATES

    @property
    def is_active(self) -> bool:
        return not self.is_terminal


# ── Valid Transitions ───────────────────────────────────────────────────────

VALID_EXECUTION_TRANSITIONS: dict[ExecutionState, list[ExecutionState]] = {
    ExecutionState.CREATED: [ExecutionState.READY, ExecutionState.CANCELLED],
    ExecutionState.READY: [ExecutionState.QUEUED, ExecutionState.BLOCKED,
                           ExecutionState.CANCELLED],
    ExecutionState.QUEUED: [ExecutionState.EXECUTING, ExecutionState.CANCELLED,
                            ExecutionState.FAILED],
    ExecutionState.EXECUTING: [ExecutionState.COMPLETED, ExecutionState.FAILED,
                                ExecutionState.BLOCKED, ExecutionState.CANCELLED,
                                ExecutionState.QUEUED],
    ExecutionState.BLOCKED: [ExecutionState.WAITING, ExecutionState.CANCELLED,
                              ExecutionState.FAILED, ExecutionState.READY],
    ExecutionState.WAITING: [ExecutionState.READY, ExecutionState.CANCELLED,
                              ExecutionState.EXPIRED],
    ExecutionState.PARTIALLY_COMPLETED: [ExecutionState.COMPLETED, ExecutionState.FAILED,
                                          ExecutionState.CANCELLED, ExecutionState.ROLLED_BACK],
    ExecutionState.COMPLETED: [],
    ExecutionState.FAILED: [ExecutionState.ROLLED_BACK],
    ExecutionState.CANCELLED: [],
    ExecutionState.ROLLED_BACK: [ExecutionState.COMPLETED],
    ExecutionState.EXPIRED: [],
}


# Terminal states (cannot transition out of)
TERMINAL_STATES: frozenset[ExecutionState] = frozenset({
    ExecutionState.COMPLETED,
    ExecutionState.CANCELLED,
    ExecutionState.EXPIRED,
})


# ── Execution Event ─────────────────────────────────────────────────────────

@dataclass
class ExecutionEvent:
    event_type: str = ""
    execution_id: str = ""
    timestamp: str = field(default_factory=_now_iso)
    payload: dict[str, Any] = field(default_factory=dict)


# ── Evidence Record ─────────────────────────────────────────────────────────

@dataclass
class EvidenceRecord:
    evidence_id: str = field(default_factory=_generate_id)
    execution_id: str = ""
    event_type: str = ""
    timestamp: str = field(default_factory=_now_iso)
    data: dict[str, Any] = field(default_factory=dict)
    immutable: bool = True


# ── Execution Timing ────────────────────────────────────────────────────────

@dataclass
class ExecutionTiming:
    created_at: str = ""
    queued_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    queue_duration_ms: float = 0.0
    execution_duration_ms: float = 0.0
    total_duration_ms: float = 0.0


# ── Execution Trace ─────────────────────────────────────────────────────────

@dataclass
class ExecutionTrace:
    timeline: list[ExecutionEvent] = field(default_factory=list)
    dependency_graph: dict[str, list[str]] = field(default_factory=dict)
    critical_path: list[str] = field(default_factory=list)
    queue_duration_ms: float = 0.0
    execution_duration_ms: float = 0.0
    total_duration_ms: float = 0.0
    retry_count: int = 0
    rollback_count: int = 0
    resource_usage: dict[str, Any] = field(default_factory=dict)
    confidence_evolution: list[float] = field(default_factory=list)


# ── Execution Instance ──────────────────────────────────────────────────────

@dataclass
class ExecutionInstance:
    """A single unit of executable work. Every commitment is an instance."""

    execution_id: str = field(default_factory=_generate_id)
    action_id: str = ""
    actor: str = ""
    objective: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] | None = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    state: ExecutionState = ExecutionState.CREATED
    priority: int = 100
    confidence: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    timeout_ms: int = 30_000
    dependencies: list[str] = field(default_factory=list)
    parent_execution_id: str | None = None
    root_execution_id: str = ""
    session_id: str = ""
    history: list[ExecutionEvent] = field(default_factory=list)
    timing: ExecutionTiming = field(default_factory=ExecutionTiming)
    trace: ExecutionTrace = field(default_factory=ExecutionTrace)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def __post_init__(self) -> None:
        if not self.root_execution_id:
            self.root_execution_id = self.execution_id

    def transition_to(self, new_state: ExecutionState, reason: str = "") -> None:
        """Transition state with deterministic validation."""
        allowed = VALID_EXECUTION_TRANSITIONS.get(self.state, [])
        if new_state not in allowed:
            raise ValueError(
                f"Invalid execution state transition: {self.state.value} → {new_state.value}"
            )
        self.state = new_state
        self.updated_at = _now_iso()
        self._record_event("ExecutionTransitioned", {
            "from": self.state.value,
            "to": new_state.value,
            "reason": reason,
        })

    def _record_event(self, event_type: str, payload: dict[str, Any] | None = None) -> ExecutionEvent:
        event = ExecutionEvent(
            event_type=event_type,
            execution_id=self.execution_id,
            payload=payload or {},
        )
        self.history.append(event)
        self.trace.timeline.append(event)
        return event


# ── Execution Context ───────────────────────────────────────────────────────

@dataclass
class ExecutionContext:
    execution_id: str = ""
    parent_execution_id: str | None = None
    root_execution_id: str = ""
    session_id: str = ""
    actor: str = ""
    objective: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] | None = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    state: ExecutionState = ExecutionState.CREATED
    timing: ExecutionTiming = field(default_factory=ExecutionTiming)
    ownership: str = ""
    priority: int = 100
    confidence: float = 0.0
    history: list[ExecutionEvent] = field(default_factory=list)


# ── Action Contract ─────────────────────────────────────────────────────────

@dataclass
class ActionContract:
    """Contract that every executable action must fulfil."""

    action_id: str = ""
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    has_rollback: bool = False
    default_timeout_ms: int = 30_000
    default_retries: int = 3
    idempotent: bool = False
    required_permissions: list[str] = field(default_factory=list)
    side_effects: list[str] = field(default_factory=list)


# ── Schedule Request ────────────────────────────────────────────────────────

class ScheduleType(str, Enum):
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    DELAYED = "delayed"
    EVENT_DRIVEN = "event_driven"
    DEPENDENCY_DRIVEN = "dependency_driven"
    MANUAL_APPROVAL = "manual_approval"


@dataclass
class ScheduleRequest:
    execution_id: str = ""
    schedule_type: ScheduleType = ScheduleType.IMMEDIATE
    scheduled_at: str | None = None
    delay_ms: int | None = None
    priority: int = 100
    dependencies: list[str] = field(default_factory=list)


# ── Policies ────────────────────────────────────────────────────────────────

@dataclass
class RetryPolicy:
    max_retries: int = 3
    backoff_ms: int = 100
    retryable_errors: tuple[type[Exception], ...] = (
        TimeoutError, ConnectionError, OSError,
    )


@dataclass
class TimeoutPolicy:
    default_timeout_ms: int = 30_000


@dataclass
class ConcurrencyPolicy:
    max_concurrent_executions: int = 10


@dataclass
class RateLimitPolicy:
    max_per_second: int = 100


@dataclass
class PermissionPolicy:
    required_permission_level: str = "user"


@dataclass
class RollbackPolicy:
    auto_rollback_on_failure: bool = True


@dataclass
class CompensationPolicy:
    enable_compensation: bool = True


@dataclass
class EscalationPolicy:
    escalate_on_retry_exhaustion: bool = True


@dataclass
class PriorityPolicy:
    priority_inheritance: bool = True


@dataclass
class ExecutionPolicies:
    """Centralised execution policies. No hardcoded behaviour."""
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    timeout: TimeoutPolicy = field(default_factory=TimeoutPolicy)
    concurrency: ConcurrencyPolicy = field(default_factory=ConcurrencyPolicy)
    rate_limit: RateLimitPolicy = field(default_factory=RateLimitPolicy)
    permissions: PermissionPolicy = field(default_factory=PermissionPolicy)
    rollback: RollbackPolicy = field(default_factory=RollbackPolicy)
    compensation: CompensationPolicy = field(default_factory=CompensationPolicy)
    escalation: EscalationPolicy = field(default_factory=EscalationPolicy)
    priority: PriorityPolicy = field(default_factory=PriorityPolicy)


# ── Registered Action ───────────────────────────────────────────────────────

@dataclass
class RegisteredAction:
    action_id: str
    contract: ActionContract
    handler: Any  # async callable
    handler_name: str = ""


# ── Execution Graph ─────────────────────────────────────────────────────────

@dataclass
class ExecutionGraph:
    """A DAG of execution instances."""

    nodes: dict[str, ExecutionInstance] = field(default_factory=dict)
    edges: dict[str, list[str]] = field(default_factory=dict)  # execution_id → [dependency_ids]

    def add_instance(self, instance: ExecutionInstance) -> None:
        self.nodes[instance.execution_id] = instance
        self.edges[instance.execution_id] = list(instance.dependencies)

    def get_dependencies(self, execution_id: str) -> list[str]:
        return self.edges.get(execution_id, [])

    def get_dependents(self, execution_id: str) -> list[str]:
        """Return all executions that depend on this one."""
        return [eid for eid, deps in self.edges.items() if execution_id in deps]

    def has_cycle(self) -> bool:
        """Detect cycles using DFS-based topological sort."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {nid: WHITE for nid in self.nodes}

        def dfs(node_id: str) -> bool:
            color[node_id] = GRAY
            for dep_id in self.edges.get(node_id, []):
                if dep_id not in color:
                    continue
                if color[dep_id] == GRAY:
                    return True
                if color[dep_id] == WHITE and dfs(dep_id):
                    return True
            color[node_id] = BLACK
            return False

        return any(dfs(nid) for nid in self.nodes if color[nid] == WHITE)

    def compute_critical_path(self) -> list[str]:
        """Return the longest dependency chain (simple heuristic)."""
        if self.has_cycle():
            return []
        # Topological sort
        visited: set[str] = set()
        topo: list[str] = []
        def dfs_topo(nid: str) -> None:
            if nid in visited:
                return
            visited.add(nid)
            for dep_id in self.edges.get(nid, []):
                if dep_id in self.nodes:
                    dfs_topo(dep_id)
            topo.append(nid)
        for nid in self.nodes:
            if nid not in visited:
                dfs_topo(nid)

        # Longest path (by edge count) in DAG
        dist: dict[str, int] = {nid: 0 for nid in self.nodes}
        pred: dict[str, str | None] = {nid: None for nid in self.nodes}
        for nid in topo:
            for dep_id in self.edges.get(nid, []):
                if dep_id in self.nodes and dist[dep_id] + 1 > dist[nid]:
                    dist[nid] = dist[dep_id] + 1
                    pred[nid] = dep_id

        if not dist:
            return []
        farthest = max(dist, key=lambda k: dist[k])
        path: list[str] = []
        cur: str | None = farthest
        while cur is not None:
            path.append(cur)
            cur = pred[cur]
        return list(reversed(path))