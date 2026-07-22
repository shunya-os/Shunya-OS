# SHUNYA System Flow

**Status:** Draft Architecture Standard
**Authority:** SHUNYA Constitution, SHUNYA Architecture, SHUNYA Engineering Constitution, SHUNYA Core Models, Governance Baseline v1.0
**Version:** 1.0
**Date:** 2026-07-18
**Author:** Chief Software Architect

---

## Section 1 — Purpose

### Why SHUNYA Requires a Canonical System Flow

The SHUNYA Core Models define the *what* — the static structure of objects, identities, evidence, confidence, and events. This document defines the *how* — the dynamic behavior of the system as work flows through it.

Without a canonical system flow, each engine specification must independently define how requests traverse the pipeline, how events propagate, how failures are handled, and how the system recovers. This leads to architectural divergence: the Governance Engine assumes synchronous validation while the Executor expects asynchronous delivery; the Knowledge Engine expects events in order while the Observer publishes them out of sequence.

A canonical system flow guarantees that:

- Every request follows the same lifecycle, regardless of entry point
- Every engine knows its position in the pipeline and its responsibilities at that position
- Every failure has a defined recovery path
- Every human intervention point is known and documented
- Every workflow is recoverable, auditable, and observable

### Static Architecture vs Dynamic Architecture

| Dimension | Static Architecture | Dynamic Architecture |
|-----------|-------------------|---------------------|
| **Defined by** | SHUNYA Core Models | SHUNYA System Flow |
| **Answers** | What exists? What are its properties? | How does work move through the system? |
| **Examples** | Object model, identity model, confidence model, event envelope | Request lifecycle, event propagation, failure recovery, human collaboration |
| **Changes** | Rare — changes require Architectural/Constitutional ADR | More fluid — new flows can be added without changing models |
| **Violations** | Invariant violations (see Core Models §11) | Behavioral violations (e.g., governance bypass, missing observability) |

This document defines **system behaviour** rather than system structure. It is the companion to SHUNYA Core Models — together they form the complete architectural specification of SHUNYA.

---

## Section 2 — Complete Intelligence Lifecycle

### Canonical Lifecycle

```
External Trigger
     │
     ▼
  Observation ─────────────────────────────────────┐
     │                                              │
     ▼                                              │
  Knowledge Resolution                              │
     │                                              │
     ▼                                              │
  Context Fusion                                    │
     │                                              │
     ▼                                              │
  Reasoning                                         │
     │                                              │
     ▼                                              │
  Planning                                          │
     │                                              │
     ▼                                              │
  Governance ────[REVIEW]──→ Human Approval ────────┤
     │                                              │
     │[APPROVE]                                     │
     ▼                                              │
  Execution                                         │
     │                                              │
     ▼                                              │
  Observation (outcome)                             │
     │                                              │
     ▼                                              │
  Knowledge Update ─────────────────────────────────┘
     │
     ▼
  Learning
     │
     ▼
  Continuous Improvement
```

### Stage Definitions

#### External Trigger

| Property | Description |
|----------|-------------|
| **Purpose** | Accept a stimulus from outside the system — human message, API call, scheduled job, webhook, document upload, external event |
| **Inputs** | Raw external payload (HTTP request, message text, file bytes, webhook JSON) |
| **Outputs** | Normalized internal stimulus routed to the appropriate engine |
| **Owner** | Interface Layer (multi-channel), Acquisition Engine (Phase 14D), Adapters |
| **Failure conditions** | Malformed payload, unknown source, authentication failure, rate limit exceeded |
| **Recovery** | Reject with error to caller; log for analysis; dead-letter for replay if transient |

#### Observation

| Property | Description |
|----------|-------------|
| **Purpose** | Record the raw stimulus as an observation before any processing. Capture what was observed, when, by which channel, and with what initial confidence |
| **Inputs** | Normalized internal stimulus from External Trigger stage |
| **Outputs** | Observation record written to the Knowledge Engine |
| **Owner** | Observer Engine |
| **Failure conditions** | Knowledge Engine unavailable, storage failure, invalid observation structure |
| **Recovery** | Retry with backoff (3 attempts); dead-letter if persistent; alert Operator |

#### Knowledge Resolution

| Property | Description |
|----------|-------------|
| **Purpose** | Determine whether existing knowledge is sufficient to handle the stimulus, or whether external information is required. Resolve internal facts first |
| **Inputs** | Observation record, workspace context |
| **Outputs** | Knowledge sufficiency verdict (internal_only, external_required, insufficient_and_unavailable, blocked) |
| **Owner** | Phase 11 (Knowledge Resolution Engine) |
| **Failure conditions** | Knowledge Engine unavailable, unresolved identity, ambiguous context |
| **Recovery** | Fall back to "external_required" if internal knowledge cannot be resolved; flag ambiguity for human review |

#### Context Fusion

| Property | Description |
|----------|-------------|
| **Purpose** | Assemble a bounded workspace context from all source providers: identity, relationships, conversations, human context, memory, evidence, documents. Apply purpose-based eligibility gates. Enforce budget limits |
| **Inputs** | Tenant ID, actor ID, purpose code, subject ID, current object reference |
| **Outputs** | WorkspaceContext — a bounded, fingerprinted set of context items with inclusion/exclusion reasons |
| **Owner** | Phase 10 (Context Fusion Engine) |
| **Failure conditions** | Phase 4 (Privacy) gate blocks eligibility; source provider unavailable; budget exceeded |
| **Recovery** | Return degraded context with empty sections and documented exclusion reasons |

#### Reasoning

| Property | Description |
|----------|-------------|
| **Purpose** | Analyze the stimulus against the workspace context. Infer intent, assess risks, build evidence chains, produce recommendations with confidence scores |
| **Inputs** | WorkspaceContext, knowledge facts, observation |
| **Outputs** | ReasoningResult — decision, confidence, evidence chain, explanation, alternatives, risk flags |
| **Owner** | Reasoning Engine |
| **Failure conditions** | Insufficient context, conflicting evidence, low confidence across all alternatives |
| **Recovery** | Return low-confidence result with explicit explanation of what is missing; request additional information |

#### Planning

| Property | Description |
|----------|-------------|
| **Purpose** | Create an executable plan from the reasoning result. Structure the plan into sequenced steps with dependencies, timelines, and resource estimates |
| **Inputs** | ReasoningResult, WorkspaceContext |
| **Outputs** | Plan — structured sequence of actions with dependencies, estimated costs, alternatives |
| **Owner** | Planner Engine |
| **Failure conditions** | Reasoning result too ambiguous to plan; required knowledge missing; no valid plan possible |
| **Recovery** | Return error stating why planning failed; request more specific reasoning |

#### Governance

| Property | Description |
|----------|-------------|
| **Purpose** | Validate the plan against constitutional principles, business policies, and risk thresholds. Return APPROVE, REVIEW, or REJECT |
| **Inputs** | Plan, evidence chain, workspace context, domain, action type |
| **Outputs** | GovernanceVerdict — approved boolean, decision (APPROVE/REVIEW/REJECT), blocking policies, warnings, reviews required, evidence checked |
| **Owner** | Governance Engine |
| **Failure conditions** | Policy evaluation error (timeout, exception, conflict); missing required evidence |
| **Recovery** | Return REJECT with documented policy evaluation error; flag for human review if conflict |

#### Human Approval (conditional)

| Property | Description |
|----------|-------------|
| **Purpose** | When Governance returns REVIEW, a human with appropriate authority reviews the plan and evidence, then approves, rejects, or modifies |
| **Inputs** | GovernanceVerdict (REVIEW), plan, evidence chain, context |
| **Outputs** | Human decision — approve (proceed), reject (return to planning), modify (with tracked changes) |
| **Owner** | Human Operator via Human Review Queue |
| **Failure conditions** | Human does not respond within SLA; ambiguous evidence; insufficient authority |
| **Recovery** | Escalate to next authority level; auto-reject after SLA expiry |

#### Execution

| Property | Description |
|----------|-------------|
| **Purpose** | Perform the approved action through the appropriate channel adapter. Deliver messages, create records, call external APIs, execute financial operations |
| **Inputs** | Approved plan, GovernanceVerdict, channel routing information |
| **Outputs** | DeliveryResult — success, message_id, channel, error (if any) |
| **Owner** | Executor Engine |
| **Failure conditions** | Channel unavailable, downstream API failure, timeout, partial delivery |
| **Recovery** | Retry with backoff; fallback to alternative channel; return partial delivery report |

#### Observation (outcome)

| Property | Description |
|----------|-------------|
| **Purpose** | Record what actually happened. Compare actual outcome to expected outcome. Detect discrepancies |
| **Inputs** | DeliveryResult, expected outcome from plan |
| **Outputs** | OutcomeObservation — success, discrepancy (if any), actual outcome, confidence |
| **Owner** | Observer Engine |
| **Failure conditions** | Observation write fails; discrepancy detection algorithm error |
| **Recovery** | Queue observation for retry; discrepancies are logged regardless of observation write success |

#### Knowledge Update

| Property | Description |
|----------|-------------|
| **Purpose** | Store the outcome as a new knowledge fact or an update to an existing fact. If the plan succeeded, reinforce the knowledge. If it failed, record the failure for learning |
| **Inputs** | OutcomeObservation |
| **Outputs** | KnowledgeFact version update |
| **Owner** | Knowledge Engine |
| **Failure conditions** | Conflict with existing fact; storage failure |
| **Recovery** | Flag conflict for resolution; retry on storage failure |

#### Learning

| Property | Description |
|----------|-------------|
| **Purpose** | Analyze the outcome against the expected outcome. Generate learning signals: what worked, what didn't, what should change. Apply improvements to knowledge, reasoning models, and policies |
| **Inputs** | OutcomeObservation, historical outcomes for the same or similar contexts |
| **Outputs** | LearningSignal — insight, recommendation, knowledge_fact_key (optional), confidence |
| **Owner** | Learning Engine |
| **Failure conditions** | Insufficient historical data; ambiguous outcome; learning signal contradicts established knowledge |
| **Recovery** | Flag ambiguous signals for human review; store low-confidence signals without applying |

#### Continuous Improvement

| Property | Description |
|----------|-------------|
| **Purpose** | The system is permanently improved. Knowledge is more accurate. Reasoning is more precise. Policies are more effective. The next cycle starts from a better foundation |
| **Inputs** | Applied learning signals over time |
| **Outputs** | Updated knowledge base, refined reasoning models, optimized policies |
| **Owner** | All engines (collective) |
| **Failure conditions** | Improvement degrades performance (over-correction, concept drift) |
| **Recovery** | Roll back to previous knowledge/policy state; flag drift for human analysis |

---

## Section 3 — Engine Responsibilities

### Observer Engine

| Property | Description |
|----------|-------------|
| **Responsibilities** | Record raw observations from all channels; compare actual vs expected outcomes; detect discrepancies |
| **May do** | Write observations to Knowledge Engine; compute discrepancy between expected and actual; flag anomalies |
| **Shall never do** | Govern, reason, execute, learn, mutate evidence, plan |
| **Events published** | `observation.recorded`, `observation.discrepancy.detected`, `observation.anomaly.flagged` |
| **Events consumed** | `execution.completed`, `knowledge.fact.created` |
| **Dependencies** | Knowledge Engine (write observations), Executor (receive completion notifications) |

### Knowledge Engine

| Property | Description |
|----------|-------------|
| **Responsibilities** | Store facts immutably with versioning; retrieve facts by key, domain, temporal range; verify integrity; maintain complete history; enforce tenant isolation |
| **May do** | Write new fact versions; supersede existing facts; return fact history; verify checksums |
| **Shall never do** | Reason, execute, govern, learn independently, access credentials, observe reality, plan |
| **Events published** | `knowledge.fact.created`, `knowledge.fact.superseded`, `knowledge.fact.conflict.detected`, `knowledge.integrity.violation` |
| **Events consumed** | `observation.recorded`, `learning.signal.generated`, `knowledge.manually.asserted` |
| **Dependencies** | Observer (receives observations), Learning (receives learning signals), all other engines (provides facts) |

### Reasoning Engine

| Property | Description |
|----------|-------------|
| **Responsibilities** | Analyze stimuli against context; infer intent; assess risks; build evidence chains; produce recommendations with confidence |
| **May do** | Read facts from Knowledge Engine; read workspace context from Context Fusion; produce reasoning results with evidence chains |
| **Shall never do** | Execute, govern, learn, access credentials, mutate knowledge, plan |
| **Events published** | `reasoning.completed`, `reasoning.insufficient.evidence` |
| **Events consumed** | `context.fusion.completed`, `knowledge.fact.created`, `knowledge.fact.superseded` |
| **Dependencies** | Knowledge Engine (read facts), Context Fusion (read workspace context) |

### Planner Engine

| Property | Description |
|----------|-------------|
| **Responsibilities** | Create executable plans from reasoning results; structure plans into sequenced steps; estimate costs and timelines |
| **May do** | Read reasoning results; read knowledge facts for plan data; produce structured plans |
| **Shall never do** | Execute, govern, reason, learn, access credentials, mutate knowledge |
| **Events published** | `plan.created`, `plan.failed` |
| **Events consumed** | `reasoning.completed` |
| **Dependencies** | Reasoning Engine (receives reasoning results), Knowledge Engine (reads facts) |

### Governance Engine

| Property | Description |
|----------|-------------|
| **Responsibilities** | Validate plans against constitutional principles and business policies; return APPROVE, REVIEW, or REJECT; maintain immutable audit trail |
| **May do** | Evaluate policies against plans; assess risk; enrich context with computed fields; audit all decisions |
| **Shall never do** | Execute, reason, learn, mutate knowledge, access credentials, plan |
| **Events published** | `governance.action.approved`, `governance.human.review.required`, `governance.policy.violation`, `governance.decision.logged` |
| **Events consumed** | `plan.created`, `policy.registry.updated` |
| **Dependencies** | Planner (receives plans), Knowledge Engine (reads policy definitions) |

### Executor Engine

| Property | Description |
|----------|-------------|
| **Responsibilities** | Perform approved actions through channel adapters; deliver messages; create records; call external APIs |
| **May do** | Send messages via channel adapters; create records per approved plan; return delivery results |
| **Shall never do** | Reason, govern, learn, access credentials beyond adapter configuration, mutate knowledge, plan |
| **Events published** | `execution.completed`, `execution.failed`, `execution.delivery.confirmed` |
| **Events consumed** | `governance.action.approved` |
| **Dependencies** | Governance Engine (receives approved actions), Channel Adapters (performs delivery) |

### Learning Engine

| Property | Description |
|----------|-------------|
| **Responsibilities** | Analyze outcomes against expectations; generate learning signals; apply improvements to knowledge, reasoning, and policies |
| **May do** | Read observations and outcomes; write learned facts to Knowledge Engine; propose policy changes |
| **Shall never do** | Mutate evidence, execute, govern, reason independently, access credentials, plan |
| **Events published** | `learning.signal.generated`, `learning.signal.applied`, `learning.anomaly.detected` |
| **Events consumed** | `observation.recorded`, `observation.discrepancy.detected`, `execution.completed` |
| **Dependencies** | Observer (reads outcomes), Knowledge Engine (writes learned facts) |

### Doctor Engine

| Property | Description |
|----------|-------------|
| **Responsibilities** | Verify system integrity; check architecture drift; validate package health; confirm governance compliance |
| **May do** | Run integrity checks; compare implementation against architecture; report violations |
| **Shall never do** | Modify system state, execute user actions, govern real-time decisions, learn |
| **Events published** | `doctor.check.completed`, `doctor.violation.detected` |
| **Events consumed** | `knowledge.integrity.violation`, `governance.decision.logged` (for audit verification) |
| **Dependencies** | All engines (checks their health and integrity) |

### Context Fusion Engine

| Property | Description |
|----------|-------------|
| **Responsibilities** | Assemble bounded workspace context from all source providers; enforce purpose-based eligibility; compute fingerprints |
| **May do** | Read from identity, relationship, conversation, human context, memory, evidence, document providers; return bounded context |
| **Shall never do** | Reason about context content; modify source data; govern; learn |
| **Events published** | `context.fusion.completed` |
| **Events consumed** | `workspace.context.requested`, `source.provider.updated` |
| **Dependencies** | All source providers (Phase 4, 5, 6, 7, 7A), Identity Engine |

### Identity Engine

| Property | Description |
|----------|-------------|
| **Responsibilities** | Resolve persons to canonical identities; register and normalize identities; detect and flag ambiguous resolutions |
| **May do** | Resolve by email, phone, channel; register new identities; mark identities as verified, superseded, or merged |
| **Shall never do** | Reason about identity context; govern; execute; learn |
| **Events published** | `identity.resolved`, `identity.ambiguous`, `identity.registered` |
| **Events consumed** | `person.created`, `identity.verification.requested` |
| **Dependencies** | Person model, channel adapters (for identity extraction) |

---

## Section 4 — Canonical Request Lifecycle

Every request within SHUNYA follows one canonical lifecycle. The lifecycle is the same whether the request originates from a WhatsApp message, an API call, a scheduled job, or a document upload.

```
Intent → Understanding → Planning → Validation → Execution → Verification → Learning
```

### Transition Definitions

| Transition | From | To | Trigger | Owner | Expected Duration |
|------------|------|----|---------|-------|-------------------|
| T1 | Intent | Understanding | External trigger received and normalized | Interface Layer | < 1s |
| T2 | Understanding | Planning | Reasoning completed with sufficient confidence | Reasoning Engine | < 5s |
| T3 | Planning | Validation | Plan created | Planner Engine | < 2s |
| T4 | Validation | Execution | Governance returns APPROVE | Governance Engine | < 1s |
| T4a | Validation | Intent (loop) | Governance returns REVIEW → human modifies intent | Human Operator | < 24h |
| T4b | Validation | Understanding (loop) | Governance returns REJECT → re-analyze | Reasoning Engine | < 5s |
| T5 | Execution | Verification | Action completed or failed | Executor Engine | < 30s |
| T6 | Verification | Learning | Outcome recorded and compared to expected | Observer Engine | < 1s |
| T7 | Learning | Intent (next cycle) | Learning signal applied | Learning Engine | < 5s |

### State Definitions per Stage

| Stage | Purpose | Acceptable States | Exit Condition |
|-------|---------|-------------------|----------------|
| **Intent** | The raw human or system goal | `pending`, `routed` | Route to Understanding |
| **Understanding** | Context assembly + reasoning | `pending`, `fusing_context`, `resolving_knowledge`, `reasoning`, `completed`, `failed` | Reasoning completed with result |
| **Planning** | Plan generation | `pending`, `creating_plan`, `estimating_costs`, `completed`, `failed` | Plan created or failure determined |
| **Validation** | Governance check | `pending`, `evaluating_policies`, `assessing_risk`, `approved`, `review_required`, `rejected` | Verdict returned |
| **Execution** | Action performance | `pending`, `dispatching`, `awaiting_confirmation`, `completed`, `partial`, `failed` | Action performed or failed |
| **Verification** | Outcome comparison | `pending`, `comparing`, `recording`, `completed` | Observation written |
| **Learning** | Improvement | `pending`, `analyzing`, `generating_signal`, `applying`, `completed`, `deferred` | Learning signal applied or deferred |

### Loops

| Loop | Path | Trigger | Max Iterations |
|------|------|---------|----------------|
| **Human refinement** | Validation → Intent | Governance returns REVIEW | 3 (after which auto-REJECT) |
| **Re-analysis** | Validation → Understanding | Governance returns REJECT due to insufficient evidence | 2 (after which human review) |
| **Continuous improvement** | Learning → Intent (next request) | Learning signal applied | Infinite (compounding) |

---

## Section 5 — Event Flow

### Event Propagation

```
Human ───→ Observer ───→ Knowledge ───→ Reasoning ───→ Planner ───→ Governance ───→ Executor ───→ Observer ───→ Learning
  │           │              │               │             │              │              │             │            │
  │           │              │               │             │              │              │             │            │
  ▼           ▼              ▼               ▼             ▼              ▼              ▼             ▼            ▼
Event Bus ── Event Bus ── Event Bus ──── Event Bus ─── Event Bus ──── Event Bus ──── Event Bus ─── Event Bus ── Event Bus
```

### Event Ordering

- Events of the same type from the same producer are delivered in order (per partition).
- Events of different types or from different producers have no ordering guarantee.
- Consumers must handle out-of-order delivery by checking event timestamps and version numbers.

### Idempotency

- Every event carries an `event_id` (UUID v7). Consumers use `event_id` for idempotency.
- If a consumer receives the same `event_id` twice, it must return the same result without re-processing.
- Idempotency cache TTL: 24 hours (events older than 24h are assumed delivered at most once).

### Retry

| Retry Level | Mechanism | Max Attempts | Backoff |
|-------------|-----------|--------------|---------|
| In-process | Synchronous retry within the consumer | 3 | Exponential (100ms, 500ms, 2s) |
| Queue-level | Event bus re-delivery | 5 | Exponential (1s, 5s, 30s, 2m, 10m) |
| Dead-letter | Manual replay or skip | N/A | N/A |

### Dead-Letter Handling

- After 5 failed delivery attempts, an event moves to the dead-letter queue.
- Dead-letter events are logged with full context (event, error, attempt history).
- An operator can replay dead-letter events manually.
- Dead-letter events older than 30 days are archived.

### Correlation

- Every request generates a `correlation_id` at the entry point.
- The `correlation_id` is propagated through all events in the request's lifecycle.
- All logs, metrics, and traces for a single request share the same `correlation_id`.

### Traceability

- Every event carries a `trace_id` that spans all operations in a request flow.
- Traces are emitted to the observability backend for distributed tracing.
- The complete event flow for any request can be reconstructed from the trace_id.

---

## Section 6 — State Flow

### Request State

```
Received → Routed → Processing → Succeeded | Failed | Cancelled
```

Transitions: Received → Routed (validated and routed to engine), Routed → Processing (engine begins work), Processing → Succeeded (successful completion), Processing → Failed (error), Processing → Cancelled (human or timeout cancellation).

### Workflow State

```
Pending → Active → Paused → Active → Completed | Failed | Cancelled
                ↘         ↘
                  Blocked     At_Risk
```

Transitions: Pending → Active (started), Active → Paused (suspended by human or system), Paused → Active (resumed), Active → Blocked (dependency not met), Blocked → Active (dependency resolved), Active → At_Risk (approaching deadline), At_Risk → Active (recovered), Active → Completed (success), Active → Failed (irrecoverable error), Active → Cancelled (human or timeout).

### Task State

```
Pending → Assigned → In_Progress → Completed | Failed | Skipped
```

Transitions: Pending → Assigned (allocated to engine or human), Assigned → In_Progress (work started), In_Progress → Completed (success), In_Progress → Failed (error), In_Progress → Skipped (dependency failed, task no longer needed).

### Knowledge State

As defined in ES-002:

```
Unknown → Observed → Verified → Trusted → Superseded → Archived → Retired
                          ↘               ↗
                        Conflict
```

### Identity State

As defined in SHUNYA Core Models §3:

```
Active → Verified → Superseded | Merged
```

### Policy State

```
Draft → Review → Active → Superseded | Retired
```

Transitions: Draft → Review (submitted for approval), Review → Active (approved), Review → Draft (returned for revision), Active → Superseded (replaced by newer policy), Active → Retired (removed without replacement).

### Execution State

As defined in ES-001 (Governance Engine state machine):

```
Idle → Receiving → Validating_Context → Validating_Constitution → Evaluating_Policies → Assessing_Risk → Approved | Review_Required | Rejected | Error
```

---

## Section 7 — Failure Behaviour

### Per-Stage Failure Handling

| Stage | Failure | Fallback | Recovery | Rollback | Human Intervention | Retry Policy | Timeout | Degraded Mode |
|-------|---------|----------|----------|----------|-------------------|--------------|---------|---------------|
| External Trigger | Malformed payload | Reject with error | Log and dead-letter | N/A | Manual replay from dead-letter | None | 10s | Return error to caller |
| Observation | Knowledge Engine unavailable | Buffer locally | Retry with backoff | N/A | Alert Operator | 3 attempts, exponential | 5s | Buffer and continue |
| Knowledge Resolution | Knowledge Engine unavailable | Assume external_required | Retry next cycle | N/A | None (degraded is safe) | 2 attempts | 3s | Assume external knowledge needed |
| Context Fusion | Source provider unavailable | Return empty section | Retry on next context request | N/A | Flag missing section | 2 attempts | 5s | Return degraded context |
| Reasoning | Insufficient context | Return low-confidence result | Request additional info | N/A | Human can provide missing context | None | 10s | Return best-effort with low confidence |
| Planning | Reasoning too ambiguous | Return planning failure | Request re-analysis | N/A | Human can plan manually | None | 5s | Return failure — cannot plan without clear reasoning |
| Governance | Policy evaluation error | Return REJECT with error detail | Alert Operator | N/A | Human reviews and overrides | 2 attempts | 30s | Return REJECT (safe failure) |
| Execution | Channel unavailable | Fallback to alternative channel | Retry with backoff | Compensation action if partial | Alert Operator | 3 attempts, exponential | 30s | Queue for later delivery |
| Observation (outcome) | Write failure | Log to local buffer | Retry | N/A | None | 3 attempts | 5s | Outcome recorded in log only |
| Knowledge Update | Conflict with existing fact | Flag conflict | Await resolution | N/A | Human resolves conflict | None | 5s | Fact held in conflict state |
| Learning | Insufficient historical data | Defer learning signal | Retry when more data available | N/A | Human reviews deferred signals | None | 10s | Defer — no learning this cycle |

### Degraded Mode Principles

1. **Safe degradation is preferred over failure.** The system should return a degraded result rather than no result.
2. **Degradation is explicit.** The consumer is informed that the result is degraded and which sections are missing.
3. **Degradation is temporary.** The system retries in the background to restore full capability.
4. **Critical paths never degrade silently.** If Governance cannot evaluate, the action is REJECTED (safe failure). If the Knowledge Engine is unavailable, the system can use cached knowledge but must flag it as potentially stale.

---

## Section 8 — Human Collaboration

### Where Humans Participate

| Point | Role | Action | Authority Boundary |
|-------|------|--------|-------------------|
| **Approval** (Governance REVIEW) | Human Operator | Approve, reject, or modify a plan | Within their defined authority scope (tenant, domain, action type, value) |
| **Correction** | Knowledge Manager | Correct a fact value or confidence | Cannot modify evidence records; can supersede facts |
| **Override** | Administrator | Override a Governance decision or policy evaluation | Must be logged and audited; override reason required |
| **Escalation** | Senior Operator | Review a decision that exceeds junior authority | Escalation chain defined per tenant |
| **Review** | Any authorized human | Review context, evidence, decisions for quality | Read-only unless explicitly authorized for correction |
| **Feedback** | Any human | Provide feedback on system behavior, suggestions for improvement | No authority to change system behavior; feedback feeds Learning |
| **Learning** | Knowledge Manager | Review and approve/reject learning signals before application | Can reject, modify, or approve learning signals |

### Human Authority Boundaries

| Authority Level | Can Approve Up To | Can Override Governance | Can Modify Knowledge | Can Modify Policies |
|-----------------|-------------------|------------------------|---------------------|---------------------|
| Operator | REVIEW decisions within domain | No | No | No |
| Senior Operator | REVIEW decisions across domains | Yes, with reason logged | Yes, facts only | No |
| Knowledge Manager | N/A | No | Yes, all facts | Propose changes only |
| Administrator | All | Yes, with reason logged | Yes | Yes, with audit trail |
| Chief Constitutional Architect | All | Yes | Yes | Yes, irrevocably |

---

## Section 9 — Multi-Tenant Behaviour

### Tenant Isolation

Every engine enforces tenant isolation as a hard boundary:

- **Data isolation:** All objects carry `tenant_id`. Queries are scoped to the requesting tenant. No cross-tenant data access without explicit authorization.
- **Identity isolation:** Each tenant has its own identity namespace. The same phone number may refer to different persons in different tenants.
- **Knowledge isolation:** Facts are scoped per tenant. Tenant A cannot query Tenant B's facts even if the fact keys are identical.
- **Event isolation:** Events carry `tenant_id`. Consumers filter by tenant. No engine processes events from another tenant.
- **Audit isolation:** Governance audit logs are scoped per tenant. Cross-tenant audit requires administrative privilege.

### Workspace Isolation

Workspace isolation is a logical subset of tenant isolation:

- Objects may optionally carry a `workspace_id`, making them visible only within that workspace.
- A workspace can access objects from its parent workspace (upward traversal) but not sibling or child workspaces (downward traversal) unless explicitly authorized.
- Context Fusion respects workspace boundaries when assembling context.

### Cross-Workspace Restrictions

- An engine may not read or write objects from a workspace it is not authorized for.
- Cross-workspace references are permitted (e.g., a task in workspace A references a person in workspace B), but the referenced object is resolved within its own workspace boundary.
- Cross-workspace events are not automatically propagated. Workspaces interested in cross-workspace events must subscribe explicitly.

---

## Section 10 — Long Running Workflows

### Lifecycle States

```
Pending → Active → Paused → Resumed → Active → Completed
                ↘                    ↘
                  Blocked              At_Risk
                      ↘                  ↘
                        Failed            Cancelled
```

### Pause and Resume

| Action | Trigger | Effect | Data Guarantee |
|--------|---------|--------|----------------|
| **Pause** | Human operator, system overload, dependency unavailable | Workflow stops at the next safe point; in-flight tasks complete or are rolled back | All state is checkpointed before pause |
| **Resume** | Human operator, dependency restored, overload cleared | Workflow continues from the last checkpoint | State is restored from checkpoint |

### Cancel

| Action | Trigger | Effect |
|--------|---------|--------|
| **Cancel** | Human operator, timeout, governance rejection | Workflow is terminated; active tasks are rolled back; compensation actions are executed for completed tasks |
| **Cancel with compensation** | Same as Cancel | For each completed task, a compensating action is executed (e.g., refund payment, cancel booking) |

### Retry

- Long-running workflows define their own retry policy per step.
- The default retry policy for a workflow step is 3 attempts with exponential backoff.
- After exhausting retries, the workflow enters `Failed` state.
- A failed workflow can be retried from the last successful checkpoint.

### Compensation

- Compensation is a reverse action that undoes a completed task.
- Compensation actions are defined in the workflow definition.
- If compensation fails, the workflow enters `Failed` state with compensation pending.
- A human must resolve compensation failures.

### Rollback

- Rollback restores the system state to before the workflow started.
- Rollback executes all compensation actions in reverse order.
- Rollback does not modify audit logs — it creates new audit entries documenting the rollback.

### Checkpoint

- Workflow state is checkpointed at every safe point (after each task completion, before each new task).
- Checkpoints enable resume after pause, retry after failure, and rollback after cancel.
- Checkpoints are stored in the workflow engine's durable store.

### Expiry

- Workflows have a configurable expiry time (default: 7 days).
- If a workflow has not completed within the expiry time, it is automatically cancelled.
- Expired workflows are archived after cancellation.

---

## Section 11 — Observability

### Logs

| Log Category | What | Level | Retention |
|-------------|------|-------|-----------|
| Engine lifecycle | Start, stop, health status | INFO | 30 days |
| Request lifecycle | Request received, routed, completed | INFO | 90 days |
| Governance decisions | Approved, REVIEW, REJECT | INFO | 7 years (audit requirement) |
| Policy violations | Which policy, severity, detail | WARN | 7 years |
| Knowledge mutations | Fact created, superseded, conflict | INFO | Permanent |
| Errors | All engine errors | ERROR | 90 days |
| Degraded mode | When system operates degraded | WARN | 30 days |
| Human interventions | Approval, override, correction | INFO | 7 years |

### Metrics

| Metric Category | Example Metrics | Aggregation |
|-----------------|----------------|-------------|
| **Business metrics** | Requests per second, active users, conversion rate, revenue processed | Per tenant, per domain |
| **Intelligence metrics** | Reasoning confidence, evidence completeness, context coverage | Per engine, per request type |
| **Learning metrics** | Learning signals generated, signals applied, knowledge improvements | Per cycle, per domain |
| **Governance metrics** | Approval rate, rejection rate, REVIEW rate, average policy evaluation time | Per tenant, per policy |
| **Pipeline metrics** | End-to-end latency per stage, throughput, active workflows, queue depth | Per engine |
| **Health metrics** | Error rate, availability, resource usage (CPU, memory, storage) | Per instance |

### Traces

- Every request generates a distributed trace spanning all engines.
- Traces include spans for each stage of the lifecycle.
- Governance decisions, knowledge mutations, and learning signals are traced as discrete spans.
- Traces are sampled: 100% for REVIEW and REJECT decisions, 10% for APPROVE decisions.

### Health

- Every engine exposes a health endpoint.
- Health includes: status (healthy, degraded, down), last check timestamp, error count, latency p50/p99.
- The Doctor Engine aggregates health across all engines and reports overall system health.
- Health checks run every 30 seconds.

---

## Section 12 — Security Behaviour

### Authentication

- Human operators authenticate via session-based auth (current implementation) or OAuth 2.0 (future).
- Machine principals (engines) authenticate via API tokens or mutual TLS.
- Authentication is verified before any request enters the lifecycle.

### Authorization

- Authorization is checked at every stage: can this actor perform this action on this object in this tenant?
- Authorization is enforced by the Governance Engine for all actions.
- Authorization decisions are audited.

### Least Privilege

- Every engine operates with the minimum set of permissions required for its function.
- The Knowledge Engine can read and write facts but cannot access credentials.
- The Executor can send messages via configured adapters but cannot modify adapter configurations.
- The Learning Engine can read outcomes and write learned facts but cannot modify evidence.

### Secrets

- Secrets (API tokens, passwords, encryption keys) are stored in a dedicated credential store.
- No engine stores secrets in its own data store.
- No engine passes secrets through event payloads.
- The Executor resolves secrets from the credential store at delivery time, not at plan time.

### Audit

- Every governance decision is audited.
- Every knowledge mutation is audited.
- Every human intervention is audited.
- Audit records are immutable and append-only.
- Audit records include: who, what, when, why, and the evidence that supported the decision.

### Evidence

- Every decision is supported by evidence.
- Evidence is immutable.
- Evidence is linked to the decision through the provenance chain.
- Evidence can be retrieved and verified independently of the decision.

### Privacy

- Privacy is enforced by Phase 4 (Privacy) eligibility gates.
- No engine accesses personal data without a valid purpose code and eligibility check.
- The Right to Be Forgotten is implemented through supersession (not deletion).

### Compliance

- Compliance policies are encoded as Governance policies.
- Compliance is enforced at the Governance stage.
- Compliance violations are audited and alerted.
- Compliance reports are generated by the Doctor Engine.

---

## Section 13 — Architectural Sequence Diagrams

### 13.1 Customer Conversation

```
Human         Interface        Observer        Knowledge       Reasoning       Planner      Governance     Executor
 │                │               │               │               │               │             │            │
 │──message──────→│               │               │               │               │             │            │
 │                │──observe─────→│               │               │               │             │            │
 │                │               │──store────────→│               │               │             │            │
 │                │               │               │──resolve──────→│               │             │            │
 │                │               │               │               │──reason────────→│             │            │
 │                │               │               │               │               │──plan────────→│            │
 │                │               │               │               │               │             │──validate──→│
 │                │               │               │               │               │             │            │
 │                │               │               │               │               │             │◀─APPROVED──│
 │                │               │               │               │               │             │──execute───→│
 │                │               │               │               │               │             │            │──send────→ External
 │                │               │               │               │               │             │            │
 │                │◀──confirm──────────────────────────────────────────────────────│             │            │
 │                │               │               │               │               │             │            │
 │                │               │◀─observe_outcome───────────────────────────────│             │            │
 │                │               │               │               │               │             │            │
 │                │               │               │◀─update─────────────────────────│             │            │
 │                │               │               │               │               │             │            │
 │                │               │◀─learn─────────────────────────────────────────│             │            │
```

### 13.2 Governance Approval Flow

```
Planner       Governance      Policy Registry    Human Review       Executor
   │               │               │                 │                │
   │──plan────────→│               │                 │                │
   │               │──get_policies─→│                 │                │
   │               │◀─policies─────│                 │                │
   │               │               │                 │                │
   │               │──evaluate─────│                 │                │
   │               │(all pass)     │                 │                │
   │               │               │                 │                │
   │               │──assess_risk──│                 │                │
   │               │(medium risk)  │                 │                │
   │               │               │                 │                │
   │               │──REVIEW───────│────────────────→│                │
   │               │               │                 │                │
   │               │               │                 │──approve───────│
   │               │◀───────────────────────────────│                 │
   │               │               │                 │                │
   │               │──APPROVED────│                 │                │
   │◀──────────────│               │                 │                │
   │               │               │                 │                │
   │               │──audit_log────│                 │                │
```

### 13.3 Error Recovery Flow

```
Engine A        Engine B        Dead-Letter     Operator        Engine A (retry)
   │               │               │               │               │
   │──event───────→│               │               │               │
   │               │──(fails)──────│               │               │
   │               │               │               │               │
   │               │──retry(1)─────│               │               │
   │               │──(fails)──────│               │               │
   │               │               │               │               │
   │               │──retry(2)─────│               │               │
   │               │──(fails)──────│               │               │
   │               │               │               │               │
   │               │──retry(3)─────│               │               │
   │               │──(fails)──────│               │               │
   │               │               │               │               │
   │               │──to_deadletter───────────────→│               │
   │               │               │               │               │
   │               │               │               │──replay───────│
   │               │               │               │               │
   │               │◀──────────────retry────────────│               │
   │               │──(succeeds)───│               │               │
```

---

## Section 14 — Architectural Invariants (Behavioral)

These invariants extend the structural invariants defined in SHUNYA Core Models §11. They govern **behavior** rather than structure.

| # | Invariant | Rationale | Violation Consequence |
|---|-----------|-----------|----------------------|
| 1 | **Every execution follows governance.** No action reaches the Executor without an APPROVE verdict from the Governance Engine. | Core constitutional principle — "AI Proposes, Humans Dispose" | Unchecked execution, security breach |
| 2 | **Every decision is explainable.** Every governance decision includes the evidence chain, policies evaluated, and reasoning. | Explainability is a constitutional requirement (SHUNYA_ARCHITECTURE.md §6.5) | Black-box decisions, untraceable outcomes |
| 3 | **Evidence precedes learning.** The Learning Engine does not generate signals without analyzing outcome observations. | Learning without evidence is guessing | False improvements, system degradation |
| 4 | **Learning never bypasses governance.** Learned policies and knowledge updates pass through the same governance validation as human-initiated changes. | All mutations must be governed, regardless of source | Unchecked system self-modification |
| 5 | **Observation is continuous.** The Observer Engine records every execution outcome without exception. No action goes unobserved. | The compounding loop requires complete observation | Blind spots in learning, untraceable failures |
| 6 | **Execution is observable.** The Executor Engine reports every execution outcome — success, failure, partial, timeout. | Without observability, the Observer cannot observe and Learning cannot improve | Silent failures, missed learning opportunities |
| 7 | **No engine communicates outside defined contracts.** Inter-engine communication uses only the defined APIs, events, and data stores. No back channels. | Layer isolation requires defined interfaces | Undocumented dependencies, brittle architecture |
| 8 | **No engine mutates another engine's state directly.** All cross-engine mutations go through the owning engine's API or through the Event Bus. | Write ownership is explicit | Data corruption, ownership violations |
| 9 | **Every workflow is recoverable.** If a long-running workflow fails, it can be retried from the last checkpoint without data loss. | Production reliability requirement | Unrecoverable workflows, data loss |
| 10 | **Every workflow is auditable.** Every task within a workflow is logged with timestamps, actor, action, and outcome. | Auditability is a constitutional requirement | Blind spots in workflow execution |
| 11 | **Human review is time-boxed.** REVIEW decisions that are not acted upon within the SLA are auto-rejected or escalated. | Prevents indefinite blocking of workflows | Stalled workflows, degraded user experience |
| 12 | **Degradation is explicit.** When the system operates in degraded mode, the consumer is informed which capabilities are degraded and why. | Transparency is a constitutional value (Explainable Decisions) | Silent degradation, false confidence |

---

## Section 15 — Future Extensions

The following capabilities are anticipated but not specified for implementation. They are documented here to inform the architecture and avoid design decisions that would preclude them.

### 15.1 Multi-Agent Collaboration

Multiple SHUNYA instances or engines collaborating on a single workflow — splitting reasoning across specialized agents, aggregating results, and resolving conflicts through a coordinator agent.

### 15.2 Distributed Execution

Workflow steps executing across multiple nodes, data centers, or regions. State synchronization, distributed consensus, and fault-tolerant execution across geographic boundaries.

### 15.3 Edge Execution

Running specific engines or workflows at the edge (near the user or device) for low-latency or offline scenarios. Syncing results to the central Knowledge Engine when connectivity is available.

### 15.4 Real-Time Streaming

Support for streaming stimuli (live chat, sensor data, market feeds) that require continuous processing rather than discrete request-response cycles. The lifecycle adapts to handle streaming windows rather than atomic requests.

### 15.5 Predictive Execution

The system anticipates likely next steps based on historical patterns and pre-positions knowledge, context, and resources before the user requests them. Reduces perceived latency.

### 15.6 Autonomous Optimization

The Learning Engine identifies optimization opportunities autonomously — adjusting policies, refining reasoning models, and reconfiguring workflows without human intervention — within bounds defined by the Governance Engine.

### 15.7 Federated Knowledge

Multiple SHUNYA tenants sharing knowledge across tenant boundaries for authorized use cases. Knowledge is shared without compromising tenant isolation — facts are aggregated, anonymized, or shared with explicit consent.

### 15.8 Self-Healing Workflows

Workflows that detect failures, diagnose root causes, and automatically apply recovery procedures without human intervention. Self-healing is governed by the Governance Engine to prevent runaway behavior.

---

## Section 16 — References

| Document | Relationship |
|----------|-------------|
| **SHUNYA Constitution** (`SHUNYA_ARCHITECTURE.md`) | Supersedes this document where constitutional principles conflict |
| **SHUNYA Core Models** (`/architecture/SHUNYA_CORE_MODELS.md`) | Defines the static structure that this document's dynamic behavior operates on. All objects, events, and confidence scores in this document conform to Core Models |
| **SHUNYA Engineering Constitution** (`/governance/SHUNYA_ENGINEERING_CONSTITUTION.md`) | Behavioral invariants in this document are divergence-checkable under Article 8 |
| **Governance Baseline v1.0** (`/governance/`) | This document is an Architecture Standard per the governance model |
| **ES-001: Governance Engine** (`/governance/engine_specs/ES-001-GOVERNANCE-ENGINE.md`) | Governance Engine's state machine and behavior conform to this document's lifecycle |
| **ES-002: Knowledge Engine** (`/governance/engine_specs/ES-002-KNOWLEDGE-ENGINE.md`) | Knowledge Engine's lifecycle and event flow conform to this document |

---

**End of SHUNYA System Flow**