# Execution Runtime Canon

> **Canonical Document · Phase F**
> **Status: CANONICAL — Implementation Specification**
> **Version: 1.0**

---

## 1. Purpose

The Cognitive Runtime (Phase E) decides. The Execution Runtime (Phase F) performs.

The Execution Runtime is the authoritative orchestration layer for all real-world work in SHUNYA. Every business action — regardless of industry — executes through this runtime. No capability may execute work directly.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        EXECUTION RUNTIME                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    ExecutionRuntime                          │  │
│  │  create, schedule, execute, cancel, rollback                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │ Execution│ │Execution │ │Execution │ │ Execution         │  │
│  │ Instance │ │  Graph   │ │Scheduler │ │ Observability     │  │
│  │ lifecycle│ │ DAG, dep │ │ schedule │ │ timeline, trace,  │  │
│  │ execution│ │ fan-out  │ │ priority │ │ critical path     │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────────┘  │
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │Execution │ │Execution │ │Execution │ │ Action            │  │
│  │ Policies │ │  Events  │ │ Recovery │ │ Contracts         │  │
│  │ retry,   │ │ canonical│ │ rollback │ │ idempotent,       │  │
│  │ timeout  │ │ runtime  │ │ resume   │ │ permissions       │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Plugin Architecture                       │  │
│  │  register_action(action_id, contract, handler)              │  │
│  │  No runtime changes for new capabilities                   │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    COGNITIVE RUNTIME (Phase E)                     │
│  Decides what to do. Delegates execution to Execution Runtime.    │
└──────────────────────────────────────────────────────────────────┘
```

### 2.1 Layers

| Layer | Authority |
|-------|-----------|
| **Execution Runtime** | The only layer authorised to execute work |
| **Cognitive Runtime** | The only layer authorised to decide what work to do |
| **Intelligence Engines** | Cognitive processors — never execute or decide directly |

### 2.2 Business-Agnostic Guarantee

The Execution Runtime contains zero industry-specific concepts. CRM, ERP, healthcare, legal, education, manufacturing, travel, and knowledge workflows all execute through the same runtime without code changes. Only action implementations differ.

---

## 3. Execution Instance

Every unit of work is an ExecutionInstance.

```python
@dataclass
class ExecutionInstance:
    execution_id: str
    parent_execution_id: str | None
    root_execution_id: str
    session_id: str
    action_id: str
    actor: str
    objective: str
    inputs: dict
    outputs: dict | None
    artifacts: list
    evidence: list
    state: ExecutionState
    priority: int
    confidence: float
    retry_count: int
    max_retries: int
    timeout_ms: int
    dependencies: list[str]
    history: list[ExecutionEvent]
    created_at: str
    updated_at: str
```

### 3.1 Properties

| Property | Description |
|----------|-------------|
| execution_id | UUID7, globally unique |
| parent_execution_id | Parent execution (for nested/sub-executions) |
| root_execution_id | Root of the execution tree |
| session_id | Cognitive session that created this execution |
| action_id | Which action this instance executes |
| actor | Identity that initiated the execution |
| objective | What this execution aims to accomplish |
| inputs | Input parameters for the action |
| outputs | Output produced (populated after completion) |
| artifacts | Files, records, evidence produced |
| evidence | Immutable evidence records |
| state | Current lifecycle state |
| priority | Execution priority (lower = higher priority) |
| confidence | Confidence that this execution will succeed |
| dependencies | Execution IDs this instance depends on |

---

## 4. Execution Lifecycle

### 4.1 State Machine

```
CREATED ──► READY ──► QUEUED ──► EXECUTING ──► COMPLETED
                │           │           │
                │           │           ├──► FAILED
                │           │           ├──► CANCELLED
                │           │           └──► BLOCKED ──► WAITING
                │           │                       │
                │           ▼                       ▼
                │       PARTIALLY_COMPLETED    READY (resume)
                │           │
                ▼           ▼
            CANCELLED   ROLLED_BACK
                            │
                            ▼
                         EXPIRED
                            │
                            ▼
                      COMPLETED (with compensation)
```

### 4.2 State Definitions

| State | Meaning |
|-------|---------|
| CREATED | Instance created but not yet ready |
| READY | Dependencies satisfied, ready to execute |
| QUEUED | Scheduled and waiting for resources |
| EXECUTING | Action handler is running |
| WAITING | Waiting for external signal |
| BLOCKED | Blocked by dependency or resource |
| PARTIALLY_COMPLETED | Some sub-executions completed |
| COMPLETED | Successfully finished |
| FAILED | Terminally failed |
| CANCELLED | Cancelled before execution |
| ROLLED_BACK | Execution rolled back |
| EXPIRED | Timed out waiting |

### 4.3 Transition Rules

All transitions are deterministic. Valid transitions:

```python
CREATED: [READY, CANCELLED]
READY: [QUEUED, BLOCKED, CANCELLED]
QUEUED: [EXECUTING, CANCELLED, FAILED]
EXECUTING: [COMPLETED, FAILED, BLOCKED, CANCELLED]
BLOCKED: [WAITING, CANCELLED, FAILED]
WAITING: [READY, CANCELLED, EXPIRED]
PARTIALLY_COMPLETED: [COMPLETED, FAILED, CANCELLED, ROLLED_BACK]
COMPLETED: []
FAILED: [ROLLED_BACK]
CANCELLED: []
ROLLED_BACK: [EXPIRED, COMPLETED]
EXPIRED: []
```

---

## 5. Execution Graph

### 5.1 Dependency Model

Execution instances form a Directed Acyclic Graph (DAG).

```
Execution A ──► Execution B ──► Execution D ──► Execution F
                                    │
Execution C ────────────────────────┘
                                    │
Execution E ────────────────────────┘

Serial:    A → B → D → F
Parallel:  C ‖ E (fan-in on D)
Fan-out:   D → F (single successor)
Fan-in:    C + E + B → D (multiple predecessors)
```

### 5.2 Execution Patterns

| Pattern | Description |
|---------|-------------|
| Serial | Execute one after another |
| Parallel | Execute multiple simultaneously |
| Fan-out | One execution triggers multiple children |
| Fan-in | Multiple executions converge into one |
| Conditional | Execute based on prior result |
| Barrier | Wait for all predecessors before proceeding |
| Join | Merge multiple execution outputs |
| Nested | Sub-executions under a parent |
| Sub-execution | Child execution within a parent scope |

### 5.3 Cycle Detection

The runtime must reject any graph with cycles. Detection uses DFS-based topological sort.

---

## 6. Execution Context

Every execution carries complete context:

```python
@dataclass
class ExecutionContext:
    execution_id: str
    parent_execution_id: str | None
    root_execution_id: str
    session_id: str
    actor: str
    objective: str
    inputs: dict
    outputs: dict | None
    artifacts: list
    evidence: list[EvidenceRecord]
    state: ExecutionState
    timing: ExecutionTiming
    ownership: str
    priority: int
    confidence: float
    history: list[ExecutionEvent]
```

---

## 7. Action Contracts

```python
@dataclass
class ActionContract:
    action_id: str
    description: str
    input_schema: dict
    output_schema: dict
    preconditions: list[Callable]
    postconditions: list[Callable]
    rollback_handler: Callable | None
    default_timeout_ms: int
    default_retry_policy: RetryPolicy
    idempotent: bool
    required_permissions: list[str]
    side_effects: list[str]
```

### 7.1 Contract Validation

Every action must declare:
1. What inputs it expects (schema)
2. What outputs it produces (schema)
3. What must be true before execution (preconditions)
4. What must be true after execution (postconditions)
5. How to undo if something fails (rollback)
6. Whether it can be safely retried (idempotency)
7. What permissions are required
8. What side effects it has

---

## 8. Scheduler

```python
@dataclass
class ScheduleRequest:
    execution_id: str
    schedule_type: ScheduleType  # IMMEDIATE, SCHEDULED, DELAYED, EVENT_DRIVEN, DEPENDENCY_DRIVEN
    scheduled_at: str | None
    delay_ms: int | None
    priority: int
    dependencies: list[str]
```

### 8.1 Schedule Types

| Type | Behaviour |
|------|-----------|
| IMMEDIATE | Execute as soon as dependencies allow |
| SCHEDULED | Execute at a specific time |
| DELAYED | Execute after a delay |
| EVENT_DRIVEN | Execute when an event fires |
| DEPENDENCY_DRIVEN | Execute when dependencies complete |
| MANUAL_APPROVAL | Wait for human approval |

### 8.2 Execution Order

The scheduler orders executions by:
1. Dependency satisfaction (DAG order)
2. Priority (lower number = higher priority)
3. Creation time (FIFO for same priority)

---

## 9. Transaction Management

### 9.1 Atomic Execution

An execution either fully succeeds or fully fails. No partial side effects leak.

### 9.2 Compensation

If an execution fails after producing side effects, the compensation handler is invoked. Compensation is the Execution Runtime's equivalent of a database rollback.

### 9.3 Rollback

Rollback reverses an execution and all its children. The runtime:
1. Marks the instance as ROLLED_BACK
2. Invokes the action's rollback handler
3. Recursively rolls back child executions
4. Records rollback evidence

### 9.4 Retry

On transient failure:
1. Check retry policy
2. If retries remaining → increment retry_count, re-queue
3. On retry exhaustion → FAILED

### 9.5 Resume

A WAITING or BLOCKED execution can be resumed when its dependency resolves or external signal arrives.

### 9.6 Failure Isolation

A failed execution does not automatically fail its dependents. Dependents may proceed with degraded confidence or wait for manual resolution.

---

## 10. Evidence Collection

Every execution automatically records:

| Event | Contents |
|-------|----------|
| Started | execution_id, action_id, timestamp, inputs |
| Completed | execution_id, outputs, duration, confidence |
| Failed | execution_id, error, retry_count |
| Rolled back | execution_id, reason, compensation result |
| Cancelled | execution_id, reason |
| Blocked | execution_id, blocking_dependency |
| Waiting | execution_id, reason |

Evidence is immutable — once recorded, it cannot be modified.

---

## 11. Observability

### 11.1 Execution Trace

Every execution produces:

```
ExecutionTrace:
  timeline: list[ExecutionEvent]
  dependency_graph: dict[str, list[str]]
  critical_path: list[str]
  queue_duration_ms: float
  execution_duration_ms: float
  total_duration_ms: float
  retry_count: int
  rollback_count: int
  resource_usage: dict
  confidence_evolution: list[float]
```

### 11.2 Critical Path

The runtime computes the critical path — the longest dependency chain determining overall duration.

---

## 12. Policies

```python
@dataclass
class ExecutionPolicies:
    retry: RetryPolicy          # max_retries, backoff_ms, retryable_errors
    timeout: TimeoutPolicy      # default_timeout_ms
    concurrency: ConcurrencyPolicy  # max_concurrent_executions
    rate_limit: RateLimitPolicy     # max_per_second
    permissions: PermissionPolicy   # required_permission_level
    rollback: RollbackPolicy        # auto_rollback_on_failure
    compensation: CompensationPolicy  # enable_compensation
    escalation: EscalationPolicy    # escalate_on_retry_exhaustion
    priority: PriorityPolicy        # priority_inheritance
```

No execution behaviour is hardcoded. All policies are configurable.

---

## 13. Plugin Architecture

### 13.1 Action Registration

```python
runtime.register_action(
    action_id="send_notification",
    contract=ActionContract(...),
    handler=send_notification_handler,
)
```

### 13.2 Registration Requirements

To add a new executable capability:
1. Implement a handler function (async) matching the ActionContract
2. Register it via `runtime.register_action()`

No runtime core code changes.

---

## 14. Execution Events

```python
@dataclass
class ExecutionEvent:
    event_type: str   # ExecutionCreated, ExecutionStarted, ExecutionCompleted, etc.
    execution_id: str
    timestamp: str
    payload: dict
```

### 14.1 Event Catalog

| Event | Trigger |
|-------|---------|
| ExecutionCreated | New instance created |
| ExecutionStarted | Instance begins executing |
| ExecutionCompleted | Instance succeeds |
| ExecutionFailed | Instance fails |
| ExecutionCancelled | Instance cancelled |
| ExecutionRolledBack | Instance rolled back |
| ExecutionBlocked | Instance blocked |
| ExecutionResumed | Instance resumes from waiting |
| ExecutionExpired | Instance timed out |
| ChildExecutionCreated | Sub-execution created |

---

## 15. Universal Validation

The same runtime executes across industries without code changes:

| Workflow | Action IDs | Execution Pattern |
|----------|-----------|-------------------|
| CRM Lead → Opportunity → Deal | validate_lead, score_opportunity, approve_deal | Sequential + Approval |
| ERP Purchase Order → Invoice → Payment | create_po, approve_po, receive_goods, pay_invoice | Parallel + Fan-in |
| Healthcare Patient Intake → Triage → Treatment | register_patient, triage, assign_doctor, start_treatment | Sequential + Barrier |
| Legal Case Filing → Discovery → Hearing | file_case, collect_evidence, schedule_hearing | Nested + Fan-out |
| Education Course Enrollment → Grading | enroll_student, deliver_content, grade_assignment | Sequential + Parallel |
| Manufacturing Order → Schedule → Produce | create_work_order, schedule_production, manufacture | Sequential + Barrier |
| Travel Booking → Itinerary → Payment | search_flights, book_flight, confirm_payment | Fan-out + Fan-in |
| Knowledge Research → Analysis → Report | gather_data, analyze, generate_report | Sequential + Nested |

---

*End of Execution Runtime Canon*