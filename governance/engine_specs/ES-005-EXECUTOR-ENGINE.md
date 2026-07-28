# ES-005: Executor Engine

**Status:** Draft
**Phase:** Phase 2 (Executor Layer)
**Layer:** Executor
**Author:** Chief Software Architect
**Date:** 2026-07-18
**Approver:** (filled on approval)

---

## Section 0 — Compounding Intelligence Position

### What Enters the Executor Engine

- **Approved plans** — governance-approved execution plans from the Governance Engine (ES-001). Include sequenced tasks, dependencies, schedules, and resource assignments.
- **Execution graphs** — the time-bound, dependency-resolved execution sequence from the Planner Engine (ES-004). Contains the ordered list of tasks, their interdependencies, and the critical path.
- **Resource assignments** — allocated resources per task: people, systems, time, money, external services.
- **Policies** — active governance policies that constrain execution behaviour (e.g., retry limits, timeout bounds, channel restrictions).
- **Credentials** — securely resolved authentication tokens and secrets for external service calls. Retrieved from the credential store at execution time, never stored in plans.
- **Context** — workspace context: tenant, actor, purpose, subject, correlation ID, trace ID.
- **Execution metadata** — delivery preferences: synchronous vs asynchronous, retry policy, timeout, channel selection.

### What Leaves the Executor Engine

- **Execution events** — real-time status updates for every task: started, completed, failed, retrying, skipped.
- **Execution evidence** — recorded proof of execution: delivery confirmations, API responses, receipts, timestamps.
- **Task status** — per-task state: pending, in_progress, completed, failed, skipped, cancelled.
- **Workflow state** — overall execution state: active, paused, blocked, at_risk, completed, failed, cancelled.
- **Failures** — structured failure records with error type, message, stack trace, and recovery attempt history.
- **Completion reports** — summary of what was executed, what succeeded, what failed, and what was skipped.
- **Execution metrics** — latencies, throughput, error rates, resource consumption per task and per workflow.
- **Outcome package** — the complete execution result packaged for the Observer Engine (discrepancy detection and learning).

### What Intelligence Is Compounded

The Executor Engine compounds **execution reliability** over time. Every execution produces evidence about what worked, what failed, and why. Retry policies improve as the system learns which failure modes are transient vs permanent. Channel selection improves as the system learns which channels are most reliable for which message types.

The compounding mechanism is **outcome-feedback via the Observer and Learning Engines**: execution outcomes are observed, discrepancies are detected, and learning signals improve future execution behaviour — better retry strategies, better channel selection, better timeout policies.

### Which Engines Depend Upon It

| Engine | Dependency | Criticality |
|--------|-----------|-------------|
| Observer Engine | Consumes execution outcomes for observation | **Critical** — cannot observe without execution results |
| Governance Engine | Receives execution feedback for policy refinement | **Medium** — governance can refine policies based on execution outcomes |
| Learning Engine | Analyzes execution outcomes for improvement | **High** — cannot learn without knowing what happened during execution |

### What Fails If It Becomes Unavailable

- **The system becomes purely advisory** — it can reason, plan, and govern, but cannot act
- **The compounding loop breaks at execution** — no outcomes are produced, so observation and learning have nothing to analyze
- **External commitments are not fulfilled** — messages are not sent, bookings are not made, payments are not processed
- **The user experience collapses** — users see plans and approvals but never see actions completed

---

## Section 1 — Mission

### Purpose of the Executor Inside SHUNYA

The Executor Engine transforms governance-approved plans into real-world actions. It is the bridge between *what should be done* (Planner + Governance) and *what actually happens* (the real world). The Executor coordinates task execution across internal services and external channels, monitors progress, collects evidence, and reports outcomes.

The canonical lifecycle (SHUNYA System Flow §2) positions Execution after Governance and before Observation:

```
Governance → Execution → Observation → Knowledge Update → Learning
```

### The Executor SHALL

- Execute governance-approved plans in the correct sequence
- Coordinate workflows: manage task dependencies, retries, timeouts, and cancellations
- Invoke internal services (Knowledge Engine writes, notification delivery, data mutations)
- Invoke external services (API calls, messaging channels, email, webhooks)
- Monitor execution state and detect anomalies (stalled tasks, stuck workflows)
- Report execution progress through real-time events
- Collect execution evidence: delivery confirmations, responses, receipts, timestamps

### The Executor SHALL NEVER

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never reason | Would violate Separation of Responsibilities | Reasoning Engine |
| Never plan | Would violate Layer Boundaries | Planner Engine |
| Never approve plans | Would violate Governance Before Execution | Governance Engine |
| Never learn from outcomes | Would violate Layer Boundaries | Learning Engine |
| Never modify knowledge | Would violate Layer Boundaries | Knowledge Engine |
| Never bypass governance | Would violate Constitutional Principle | Governance Engine |
| Never invent missing information | Would violate Explainable Decisions | (return errors instead) |
| Never mutate governance policies | Would violate Auditability | Governance Engine / Constitutional administration |

---

## Section 2 — Inputs

All inputs conform to the canonical models defined in SHUNYA Core Models and the output contracts of upstream engines.

### Input Contract

```
ExecutorInput:
  approved_plan: ExecutionPlan          — From ES-004, approved by ES-001. Sequenced tasks,
                                          dependencies, schedules, resource assignments.
  execution_graph: ExecutionGraph       — Time-bound, dependency-resolved execution sequence.
  resource_assignments: ResourceAssignment[] — Allocated resources per task.
  policies: Policy[]                    — Active governance policies constraining execution.
  credentials: CredentialRef[]          — Securely resolved credential references for external
                                          service calls. Resolved at execution time.
  context: WorkspaceContext             — Tenant, actor, purpose, correlation ID, trace ID.
  execution_config: ExecutionConfig     — Delivery preferences: sync/async, retry policy,
                                          timeout, channel selection.
  request_metadata: RequestInfo         — Correlation ID, trace ID, tenant ID.
```

### Input Sources

| Input | Source | Retrieval Method |
|-------|--------|-----------------|
| Approved plan | Governance Engine (ES-001) | Governance `APPROVE` verdict includes the plan |
| Execution graph | Planner Engine (ES-004), embedded in plan | Part of the approved plan payload |
| Resource assignments | Planner Engine (ES-004) | Part of the approved plan payload |
| Policies | Governance Engine (ES-001) | In-memory policy registry snapshot |
| Credentials | Credential Store | Resolved at task execution time, not stored in plan |
| Context | Context Fusion (Phase 10) | Propagated through request lifecycle |
| Execution config | Governance Engine / Interface Layer | Part of the approved plan or execution request |

### Input Validation

| Field | Constraint | Rejection |
|-------|-----------|-----------|
| `approved_plan.governance_verdict` | Must be `APPROVE` | `PLAN_NOT_APPROVED` — cannot execute without governance approval |
| `approved_plan.tasks` | Non-empty | `EMPTY_PLAN` — nothing to execute |
| `execution_graph.dependencies` | Must be acyclic | `CIRCULAR_DEPENDENCY` |
| `credentials` | May be empty (no external calls) | Warning — external tasks will fail |
| `context.tenant_id` | Must match request tenant | `TENANT_MISMATCH` |

---

## Section 3 — Outputs

All outputs conform to the canonical models defined in SHUNYA Core Models.

### Output Contract

```
ExecutorOutput:
  outcome_package: OutcomePackage       — Complete execution result for Observer Engine.
                                          Includes task outcomes, evidence, failures, metrics.
  execution_events: ExecutionEvent[]    — Real-time status updates per task.
  task_statuses: TaskStatus[]           — Per-task final state: completed, failed, skipped,
                                          cancelled.
  workflow_state: string                — Overall state: completed, partial, failed, cancelled.
  failures: ExecutionFailure[]          — Structured failure records with recovery history.
  completion_report: CompletionReport   — Summary: tasks total, succeeded, failed, skipped,
                                          duration.
  execution_evidence: ExecutionEvidence[] — Proof of execution: delivery confirmations, API
                                          responses, receipts, timestamps.
  execution_metrics: ExecutionMetrics   — Latencies, throughput, error rates, resource use.
```

### Output Destinations

| Output | Destination | Format |
|--------|-------------|--------|
| Outcome package | Observer Engine | `OutcomePackage` — complete execution result for discrepancy detection |
| Execution events | Event Bus (all subscribers) | Canonical event envelope |
| Task statuses | Interface Layer (for user feedback) | Real-time status updates |
| Workflow state | Interface Layer, human review UI | Current workflow state |
| Execution evidence | Knowledge Engine (ES-002) | Immutable evidence records |
| Execution metrics | Observability backend | Prometheus metrics |

### Output Guarantees

- **At-least-once delivery:** Every execution event is delivered at least once. Consumers must handle duplicates via idempotency (event_id).
- **Exactly-once task execution (within a workflow):** A task within a single workflow is executed at most once. If a task fails, it is retried (not re-executed from scratch).
- **Outcome completeness:** Every execution produces a complete outcome package. Partial executions produce partial outcome packages with documented gaps.

---

## Section 4 — Execution Pipeline

### Canonical Stages

```
Execution Preparation
     │
     ▼
Dependency Verification
     │
     ▼
Resource Acquisition
     │
     ▼
Task Dispatch
     │
     ▼
Execution Monitoring
     │
     ▼
Evidence Collection
     │
     ▼
Completion Verification
     │
     ▼
Outcome Packaging
     │
     ▼
Observation Handoff
```

### Stage Definitions

| Stage | Purpose | Inputs | Outputs | Failure Condition |
|-------|---------|--------|---------|-------------------|
| **Execution Preparation** | Validate the execution environment, resolve credentials, initialize channels | Approved plan, credentials, context | Initialized execution context | Credentials unavailable; channel misconfigured |
| **Dependency Verification** | Verify that all task dependencies can be satisfied before starting | Execution graph, resource state | Verified dependency graph | Circular dependency (should not happen — verified by Planner) |
| **Resource Acquisition** | Acquire required resources (locks, connections, API rate limits) | Resource assignments, resource pool | Acquired resources | Resource timeout; resource exhausted |
| **Task Dispatch** | Dispatch each task to the appropriate executor (internal service, channel adapter, external API) | Verified tasks, acquired resources, credentials | Dispatched tasks with tracking IDs | Dispatch failure; channel unavailable |
| **Execution Monitoring** | Monitor task progress, detect stalls, trigger retries, manage timeouts | Dispatched tasks, policies | Real-time task status | Task stall; timeout exceeded |
| **Evidence Collection** | Collect execution evidence: delivery confirmations, API responses, receipts | Completed tasks, channel responses | Execution evidence records | Evidence source unavailable |
| **Completion Verification** | Verify that all tasks completed successfully and outputs are consistent | Task statuses, execution evidence | Completion verdict (success, partial, failed) | Inconsistent outputs; missing evidence |
| **Outcome Packaging** | Package the complete execution result for the Observer Engine | Completion verdict, evidence, metrics, failures | OutcomePackage | Outcome too large |
| **Observation Handoff** | Deliver the outcome package to the Observer Engine | OutcomePackage | Delivery confirmation | Observer Engine unavailable (retry with backoff) |

---

## Section 5 — Execution Types

| Execution Type | Description | When Used | Example |
|----------------|-------------|-----------|---------|
| **Synchronous** | Execute task and wait for completion. Caller blocks until result is available. | Simple, fast operations where response is needed immediately | "Send a confirmation message and wait for delivery confirmation" |
| **Asynchronous** | Dispatch task and return immediately. Result is delivered via event when complete. | Long-running operations, operations that don't require immediate response | "Generate a PDF invoice and notify when ready" |
| **Human-assisted** | Task requires human action. Dispatch to human review queue and wait for completion. | Approval workflows, manual data entry, exception handling | "Review and approve the generated proposal before sending to customer" |
| **Long-running** | Execution may take minutes, hours, or days. Workflow is checkpointed and resumable. | Multi-step processes with external dependencies | "Book a complete trip: flights → hotels → transport → activities" |
| **Batch** | Execute multiple tasks as a group. Success requires all or a defined subset to succeed. | Bulk operations, data migrations, synchronizations | "Import 1000 contacts from a CSV file" |
| **Streaming** | Tasks arrive continuously and are processed as they arrive. No fixed task set. | Real-time data processing, event-driven responses | "Process incoming customer messages as they arrive" |
| **Scheduled** | Execution is triggered by a timer or calendar event. | Periodic tasks, delayed actions, cron jobs | "Send weekly report every Monday at 9 AM" |
| **Event-driven** | Execution is triggered by an event from another engine or external system. | Reactive workflows, chained operations | "When payment is received, update invoice status and notify customer" |
| **Distributed** | Tasks execute across multiple nodes or systems. Coordination required. | Multi-region, multi-system, multi-tenant operations | "Provision resources across three cloud regions" |
| **Transactional** | All tasks must succeed or the entire execution is rolled back. | Financial operations, state-changing operations | "Process payment: charge card AND update ledger AND send receipt" |

---

## Section 6 — Workflow Model

### Workflow Structure

A workflow is a set of tasks with dependencies, managed as a single execution unit.

```
Workflow:
  id: string                    — Unique workflow identifier
  plan_id: string               — Reference to the originating plan
  tenant_id: int                — Owning tenant
  state: string                 — active | paused | blocked | at_risk | completed | failed | cancelled
  tasks: Task[]                 — The tasks in this workflow
  dependencies: Dependency[]    — Ordering constraints between tasks
  created_at: datetime
  updated_at: datetime
  checkpoints: Checkpoint[]     — Resumable state snapshots
```

### Task Model

```
Task:
  id: string                    — Unique task identifier
  type: string                  — execution type (see Section 5)
  action: string                — What to execute: "send_message", "create_record", "call_api", etc.
  target: string                — Where to execute: channel name, service name, API endpoint
  payload: dict                 — The data to send or action parameters
  dependencies: string[]        — Task IDs that must complete before this task
  state: string                 — pending | in_progress | completed | failed | skipped | cancelled
  retry_policy: RetryPolicy     — Max attempts, backoff, timeout
  compensation: string | null   — Compensation action to undo this task
  timeout: int                  — Maximum execution time in seconds
  evidence: dict                — Execution evidence collected during/after execution
  started_at: datetime | null
  completed_at: datetime | null
  failure: ExecutionFailure | null
```

### Retry Policy

```
RetryPolicy:
  max_attempts: int             — Maximum retry attempts (default: 3)
  backoff: string               — "exponential" | "linear" | "fixed"
  initial_delay_ms: int         — Delay before first retry (default: 1000)
  max_delay_ms: int             — Maximum delay between retries (default: 60000)
  retryable_errors: string[]    — Error types that trigger retry
  non_retryable_errors: string[] — Error types that immediately fail
```

### Compensation

Every task may define a compensation action. Compensation is a reverse action that undoes the task:

- `send_message` → compensation is `none` (messages cannot be unsent)
- `create_record` → compensation is `delete_record`
- `charge_payment` → compensation is `refund_payment`
- `book_service` → compensation is `cancel_booking`

Compensation actions are executed in reverse dependency order when a workflow is rolled back or cancelled with compensation.

### Checkpoints

Workflows are checkpointed at every task boundary. A checkpoint captures:

- Current task states
- Completed task evidence
- Failed task history
- Resource allocation state
- Workflow metadata

Checkpoints enable resume after pause, retry after failure, and rollback after cancel.

---

## Section 7 — External Integration

### Integration Types

| Integration Type | Mechanism | Authentication | Reliability |
|-----------------|-----------|---------------|-------------|
| **Internal engines** | Direct API calls or Event Bus events | Engine-to-engine trust within the same deployment | High — same infrastructure |
| **External APIs** | HTTP(S) requests via channel adapters | API tokens, OAuth, mTLS | Variable — depends on provider |
| **Email** | SMTP or email API (SendGrid, etc.) | SMTP credentials or API token | Medium — delivery delays possible |
| **Messaging** | WhatsApp Business API, Telegram Bot API | OAuth, bot tokens | Medium — rate limits apply |
| **Storage** | S3, local filesystem, database | IAM roles, connection strings | High — same infrastructure |
| **Databases** | SQLAlchemy (same DB), direct connection | Connection strings, IAM | High — same DB cluster |
| **Webhooks** | Outbound HTTP POST to configured URL | HMAC signatures, API keys | Low — no delivery guarantee |
| **Third-party systems** | Provider-specific SDKs or REST APIs | Provider-specific | Variable |

### Channel Adapter Contract

Every external integration uses a channel adapter implementing:

```
ChannelAdapter:
  channel_type: string          — Unique channel identifier
  send(message: OutboundMessage) → DeliveryResult
  parse_inbound(raw: dict) → InboundMessage | null
  is_configured() → bool
```

Channel adapters are registered with the Executor Engine at startup. The Executor routes tasks to the appropriate adapter based on the task's `target` field.

### Credential Resolution

Credentials are resolved at task execution time, never stored in plans or task definitions:

1. The task references a credential by ID or alias (e.g., `credential: "whatsapp_api_token"`)
2. The Executor resolves the credential from the credential store
3. The credential is passed to the channel adapter for authentication
4. The credential is discarded after the task completes

---

## Section 8 — Failure Modes

| Failure Mode | Cause | Detection | Effect | Recovery |
|--------------|-------|-----------|--------|----------|
| Task failure | Task logic error, invalid payload, business rule violation | Task returns error status | Task marked as failed; workflow may continue or halt depending on criticality | Retry if retryable; escalate if non-retryable |
| Resource failure | Required resource (connection, lock, rate limit) unavailable | Resource acquisition timeout or rejection | Task cannot start; workflow blocked | Retry with backoff; alternative resource; escalate if persistent |
| Network failure | Downstream service unreachable, DNS failure, TLS error | HTTP timeout or connection error | Task cannot complete; delivery fails | Retry with exponential backoff; fallback channel; dead-letter if persistent |
| Timeout | Task exceeds its configured timeout | Timer | Task marked as failed | Retry (if timeout was transient); escalate (if timeout indicates systemic issue) |
| Partial execution | Some tasks succeed, some fail | Completion verification stage | Workflow enters `partial` state | Compensate completed tasks; retry failed tasks; report partial completion |
| Duplicate execution | Same task executed twice due to retry without idempotency | Idempotency key collision detection | **Critical** — duplicate side effects | Idempotency check before every task; deduplication on task dispatch |
| Compensation failure | Compensation action fails during rollback | Compensation task returns error | **Critical** — system state inconsistent | Log compensation failure; alert operator; manual resolution required |
| External dependency failure | Third-party API returns 5xx, rate limit exceeded, service degraded | HTTP error, rate limit response | Task cannot complete | Retry with backoff; fallback to alternative provider; escalate if all providers fail |

---

## Section 9 — Interaction Matrix

| Layer / Engine | Reads | Writes | Events Published | Events Consumed |
|----------------|-------|--------|-----------------|-----------------|
| **Governance Engine** (ES-001) | Approved plans, policies | — | `execution.completed`, `execution.failed` | `governance.action.approved` |
| **Planner Engine** (ES-004) | Execution graphs, resource assignments | — | — | — |
| **Knowledge Engine** (ES-002) | Channel config, templates | Execution evidence | — | — |
| **Observer Engine** | — | — | `execution.completed`, `execution.failed` | `execution.ready` (from governance) |
| **Learning Engine** | — | — | — | `execution.completed` (outcome analysis) |
| **Channel Adapters** | Credentials (resolved at runtime) | — | — | Task dispatch |
| **Credential Store** | Secrets | — | — | Credential resolution request |

### Dependencies

| Dependency | Type | Criticality |
|------------|------|-------------|
| Governance Engine (ES-001) | Input — approved plans | **Critical** — cannot execute without approval |
| Planner Engine (ES-004) | Input — execution graphs | **Critical** — cannot execute without a plan |
| Channel Adapters | Execution — external delivery | **Critical** — cannot reach external systems |
| Credential Store | Read — secrets for external calls | **High** — cannot authenticate without credentials |
| Knowledge Engine (ES-002) | Read — channel configuration | **Medium** — can use cached configuration |

### Ownership

- The Executor Engine **owns** task execution, workflow management, evidence collection, and outcome packaging.
- It **does not own** plans, policies, credentials, knowledge, or governance decisions.
- It **shares ownership** of execution evidence with the Knowledge Engine (evidence is written to the Knowledge Engine for audit).

---

## Section 10 — Performance

| Dimension | Target | Measurement |
|-----------|--------|-------------|
| **Task dispatch latency p50** | < 10ms | Per task dispatch (synchronous) |
| **Task dispatch latency p99** | < 100ms | Per task dispatch |
| **Concurrent workflows** | 100 / instance | Per Executor instance |
| **Concurrent tasks** | 500 / instance | Per Executor instance |
| **Throughput** | 1000 tasks/second | Per instance (simple tasks) |
| **Event publication latency** | < 5ms | Per execution event |
| **Checkpoint write latency** | < 50ms | Per checkpoint |

### Scaling

- The Executor Engine is designed for horizontal scaling. Multiple instances process tasks concurrently.
- Workflows are assigned to instances by workflow ID (consistent hashing ensures one instance handles one workflow).
- No shared state between instances except the workflow state store (durable database).

### Queueing

- Asynchronous tasks are queued in an in-process or Redis-backed task queue.
- Queue depth is monitored. If queue depth exceeds 10,000 tasks, backpressure is applied (new workflow acceptance slows).
- Dead-letter queue captures tasks that exceed max retries. Dead-letter queue is monitored and alerted.

### Backpressure

When the Executor Engine is under load:

1. New workflow acceptance slows (proportional to queue depth)
2. Non-critical tasks are deprioritized
3. If overload persists, new workflow requests are rejected with a `503 Service Unavailable` response

---

## Section 11 — Security

### Secrets

- Secrets (API tokens, passwords, encryption keys) are stored in a dedicated credential store.
- The Executor Engine resolves secrets at task execution time, not at plan time.
- Secrets are never stored in plan definitions, task payloads, or execution events.
- Secrets are passed to channel adapters via memory-only references and discarded after task completion.

### Authentication

- The Executor Engine authenticates to external services using resolved credentials.
- Credential types supported: API tokens, OAuth 2.0 access tokens, Basic Auth, mTLS certificates, HMAC signatures.
- Authentication failures are logged and retried per the task's retry policy.

### Authorization

- The Executor Engine does not enforce authorization. Authorization is verified by the Governance Engine (ES-001) before the plan reaches the Executor.
- The Executor Engine assumes all tasks in an approved plan are authorized.

### Least Privilege

- The Executor Engine operates with the minimum set of permissions required for its function.
- Channel adapters have access only to the credentials they need (not all credentials).
- The Executor Engine cannot modify governance policies, knowledge facts, or plans.

### Auditability

- Every task execution is audited: task ID, action, target, state, timestamps, evidence, failure details.
- Audit records are written to the Knowledge Engine (ES-002) as immutable evidence records.
- Workflow-level audit is maintained by the workflow state store.

### Tenant Isolation

- All execution is scoped to the requesting tenant's `tenant_id`.
- Task payloads, evidence, and audit records carry the tenant ID.
- No cross-tenant execution leakage.

---

## Section 12 — Observability

### Metrics

| Metric | Type | Unit | Target |
|--------|------|------|--------|
| `executor.tasks_dispatched_total` | Counter | tasks | Per second |
| `executor.tasks_completed_total` | Counter | tasks | Per second |
| `executor.tasks_failed_total` | Counter | tasks | Per second (by failure type) |
| `executor.tasks_retried_total` | Counter | retries | Per second |
| `executor.workflows_active` | Gauge | workflows | Current active count |
| `executor.workflows_completed_total` | Counter | workflows | Per second |
| `executor.workflows_failed_total` | Counter | workflows | Per second |
| `executor.latency_dispatch_p50` | Histogram | ms | < 10ms |
| `executor.latency_dispatch_p99` | Histogram | ms | < 100ms |
| `executor.latency_task_p50` | Histogram | ms | Per task type |
| `executor.latency_task_p99` | Histogram | ms | Per task type |
| `executor.queue_depth` | Gauge | tasks | Current queue depth |
| `executor.retry_attempts` | Histogram | attempts | Per task |
| `executor.compensation_executed_total` | Counter | compensations | Per second |

### Tracing

- **Span: `executor.workflow`** — Full workflow lifecycle
  - Child span: `executor.task_dispatch` — Per task dispatch
  - Child span: `executor.task_execute` — Per task execution (includes channel adapter call)
  - Child span: `executor.evidence_collection` — Per task evidence collection
  - Child span: `executor.compensation` — Per compensation action
- Trace context propagated from caller (Governance Engine or Interface Layer)

### Workflow Metrics

| Metric | Purpose |
|--------|---------|
| **Workflow completion rate** | Fraction of workflows that complete successfully |
| **Workflow duration p50/p99** | End-to-end execution time |
| **Task failure rate** | Fraction of tasks that fail (by failure type) |
| **Retry effectiveness** | Fraction of retried tasks that eventually succeed |
| **Compensation success rate** | Fraction of compensations that succeed |
| **Channel reliability** | Per-channel success/failure rate |

---

## Section 13 — Constitutional Mapping

| Responsibility | Constitutional Principle | Source |
|---------------|------------------------|--------|
| Execute approved plans only after governance approval | 6.6 Governance Before Execution | SHUNYA_ARCHITECTURE.md §6.6 |
| Channel-agnostic execution | 5 (Executor Layer) — Channel-agnostic, same action any channel | SHUNYA_ARCHITECTURE.md §5 |
| Never execute without governance approval | 2.3 AI Proposes, Humans Dispose | SHUNYA_ARCHITECTURE.md §2.3 |
| Collect execution evidence for audit | 6.7 Continuous Observation | SHUNYA_ARCHITECTURE.md §6.7 |
| Report outcome for observation and learning | 6.7 Continuous Observation — Execute → Observe → Compare → Learn | SHUNYA_ARCHITECTURE.md §6.7 |
| Never reason, plan, approve, or learn | 5 (Executor Layer) — Performs approved actions, never reasons | SHUNYA_ARCHITECTURE.md §5 |
| Secrets resolved at execution time, not stored in plans | 6.3 Principle of Least Authority | SHUNYA_ARCHITECTURE.md §6.3 |
| Tenant isolation on all execution data | 9 (Multi-Tenant Behaviour) | SHUNYA System Flow §9 |
| Every execution is observable | 6 (Execution is observable) | SHUNYA System Flow §14 |
| Every execution produces evidence | 4.3 No Disappearing Evidence | SHUNYA_ENGINEERING_CONSTITUTION.md §4.3 |

---

## Section 14 — Layer Responsibilities

### The Executor Engine SHALL

- Execute governance-approved plans in dependency order
- Coordinate workflows: manage task dependencies, retries, timeouts, cancellations, and compensations
- Invoke internal services and external APIs through channel adapters
- Resolve credentials at task execution time from the credential store
- Monitor execution state and detect anomalies (stalled tasks, stuck workflows)
- Report execution progress through real-time events
- Collect execution evidence: delivery confirmations, API responses, receipts, timestamps
- Package complete execution outcomes for the Observer Engine
- Enforce tenant isolation on all execution data

### The Executor Engine SHALL NEVER

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never reason about tasks or outcomes | Would violate Separation of Responsibilities | Reasoning Engine |
| Never create or modify plans | Would violate Layer Boundaries | Planner Engine |
| Never approve or reject plans | Would violate Governance Before Execution | Governance Engine |
| Never learn from execution outcomes | Would violate Layer Boundaries | Learning Engine |
| Never modify knowledge facts | Would violate Layer Boundaries | Knowledge Engine |
| Never bypass governance | Would violate Constitutional Principle | Governance Engine |
| Never invent missing information | Would violate Explainable Decisions | (return errors instead) |
| Never mutate governance policies | Would violate Auditability | Constitutional administration |
| Never store credentials in task payloads | Would violate Least Authority Principle | Credential Store |
| Never modify channel adapter configuration at runtime | Would violate Security (authorized configuration changes only) | Configuration management |

---

## Section 15 — Complexity Analysis

### CPU Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Task dispatch | O(1) | Per task, constant time |
| Dependency resolution | O(T + D) | T = tasks, D = dependencies |
| Retry scheduling | O(1) | Per retry, constant time |
| Compensation execution | O(C × T) | C = compensations, T = tasks in reverse order |
| Checkpoint write | O(S) | S = workflow state size |
| Workflow completion verification | O(T) | T = tasks |
| Outcome packaging | O(P) | P = outcome payload size |
| Event publication | O(1) | Per event |

### Memory Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Workflow state in memory | O(T + D) | T = tasks, D = dependencies |
| Task queue | O(Q) | Q = queued tasks |
| Execution evidence buffer | O(E) | E = evidence records per workflow |
| Outcome package | O(P) | P = outcome payload size |

### Queue Growth

Queue growth is bounded by:

- Maximum concurrent workflows (100/instance) × maximum tasks per workflow (100) = 10,000 tasks maximum in queue
- Backpressure applied when queue depth exceeds 10,000
- Dead-letter queue for tasks exceeding max retries

### Workflow Growth

- Active workflows per instance: 100 max
- Completed workflows are archived after outcome delivery
- Failed workflows are retained for 7 days for analysis, then archived
- Compensation-pending workflows are retained until compensation completes or is escalated

### Failure Isolation

- Task failure is isolated to that task. Other tasks in the same workflow continue unless the failed task is on the critical path.
- Workflow failure is isolated to that workflow. Other workflows are unaffected.
- Channel adapter failure is isolated to that channel. The Executor can fall back to alternative channels.
- Credential resolution failure is isolated to that task. Other tasks with different credentials are unaffected.
- Executor Engine instance failure: workflows are recovered from the last checkpoint by another instance.

---

## Section 16 — Future Extensions

The following capabilities are anticipated but not specified for implementation. They are documented here to inform the architecture and avoid design decisions that would preclude them.

### 16.1 Autonomous Execution

The Executor Engine autonomously determines execution strategies — channel selection, retry policies, timeout values — based on historical execution outcomes and real-time conditions.

### 16.2 Distributed Orchestration

Workflows that span multiple Executor Engine instances, data centers, or cloud regions. State synchronization and distributed consensus for cross-region workflows.

### 16.3 Edge Execution

Running specific tasks at the edge (near the user or device) for low-latency or offline execution. Edge results sync to the central Knowledge Engine when connectivity is available.

### 16.4 Self-Healing Execution

The Executor Engine detects execution anomalies (stalled tasks, degraded channels, resource exhaustion) and automatically applies corrective actions — re-routing tasks, scaling resources, or pausing non-critical workflows.

### 16.5 Dynamic Scheduling

Task execution order is optimized dynamically based on real-time conditions — channel availability, resource contention, cost optimization — rather than following a static execution graph.

### 16.6 Adaptive Retries

Retry policies adapt based on error type, channel health, and historical retry success rates. The system learns which error types are transient vs permanent and adjusts retry strategies accordingly.

### 16.7 Workflow Optimization

The Executor Engine analyzes workflow execution patterns and suggests optimizations to the Planner Engine — re-ordering tasks, merging redundant operations, parallelizing independent work.

### 16.8 Agent Collaboration

Multiple Executor Engines or external execution agents collaborating on a single workflow, each responsible for a subset of tasks. Coordination via a shared workflow state store.

---

## Section 17 — References

| Document | Relationship |
|----------|-------------|
| **SHUNYA Constitution** (`SHUNYA_ARCHITECTURE.md`) | Supersedes this specification where constitutional principles conflict |
| **SHUNYA Core Models** (`/architecture/SHUNYA_CORE_MODELS.md`) | Defines canonical event envelope (§8), evidence model (§5), provenance model (§6) — all inherited by this specification |
| **SHUNYA System Flow** (`/architecture/SHUNYA_SYSTEM_FLOW.md`) | Defines pipeline position (§2), execution stage in lifecycle (§2), engine responsibilities (§3), failure behaviour (§7) — this specification's behavioral context |
| **SHUNYA Engineering Constitution** (`/governance/SHUNYA_ENGINEERING_CONSTITUTION.md`) | Article 5 (Governance Before Execution), Article 8 (Divergence Protocol) — governs this specification |
| **ES-001: Governance Engine** (`/governance/engine_specs/ES-001-GOVERNANCE-ENGINE.md`) | Provides approved plans for execution |
| **ES-002: Knowledge Engine** (`/governance/engine_specs/ES-002-KNOWLEDGE-ENGINE.md`) | Stores channel configuration, execution evidence |
| **ES-003: Reasoning Engine** (`/governance/engine_specs/ES-003-REASONING-ENGINE.md`) | Provides the reasoning behind the plan being executed |
| **ES-004: Planner Engine** (`/governance/engine_specs/ES-004-PLANNER-ENGINE.md`) | Provides execution graphs and resource assignments |
| `app/shunya/executor.py` | Current ExecutorLayer implementation (412 lines) — v2 with WhatsApp, Telegram, Email channel adapters |