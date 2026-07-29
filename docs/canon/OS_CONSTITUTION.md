# SHUNYA Operating System Constitution

> **Phase L · System Convergence & Operating System Unification**
> **Status: CANONICAL — This document is the governing constitution for all SHUNYA OS development.**
> **Version: 1.0**
> **Governed By: [SHUNYA Constitution](../docs/canon/02_shunya_constitution.md) — This document operates within the SHUNYA Constitution's framework. No article herein may contradict the SHUNYA Constitution.**
> **Governance Authority: [SHUNYA Governance Model](../governance/SHUNYA_GOVERNANCE_MODEL.md) — Amendment process, conflict resolution, and role definitions are governed by the Governance Model.**

---

## Preamble

SHUNYA is an operating system for human organizations. It is not a collection of runtimes, frameworks, user interfaces, or business applications. It is one living operating system.

This Constitution defines the immutable laws that govern all SHUNYA OS development. No implementation decision may violate this Constitution. Any violation discovered during review must be remediated before the next phase can begin.

---

## Article I — The Operating System Principle

**SHUNYA is the operating system. Everything else is a consumer.**

### §1.1 Separation

```
┌─────────────────────────────────────────────────────────────┐
│                    SHUNYA Operating System                    │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │Kernel│ │Graph │ │Memory│ │Plan  │ │Exec  │ │Auto  │   │
│  │      │ │      │ │      │ │      │ │      │ │      │   │
│  │Types │ │Nodes │ │Store │ │HTN   │ │State │ │Events│   │
│  │State │ │Edges │ │Recall│ │Decomp│ │Mach  │ │Rules │   │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │
│         ↑ canonical pipeline ↓                              │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │
│  │Proj  │ │Intel│ │Ident │ │Evi-  │ │Audit │             │
│  │ection│ │ligence│ │ity   │ │dence │ │      │             │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘             │
└─────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐     ┌──────────────────────────┐
│  Flask Gateway    │     │  Presentation Layer       │
│  (app/)           │     │  (Next.js frontend)       │
│  Routes, Auth,    │     │  Renders OS projections   │
│  Session, CORS    │     │  Never owns business      │
│  Webhook ingress  │     │  logic                   │
└──────────────────┘     └──────────────────────────┘
```

### §1.2 The OS owns everything

- The OS owns types, state, identity, relationships, memory, execution, automation, evidence, and projections.
- The Flask gateway (`app/`) owns routing, authentication, session management, CORS, webhooks, and template rendering.
- The presentation layer (Next.js) owns rendering, layout, interaction, and accessibility.
- Neither Flask nor the frontend may own business logic.

### §1.3 The pipeline is the only path

There is exactly one canonical execution pipeline. Every user action — every intent — flows through it. No alternate paths may be introduced. Any code that bypasses the pipeline is an architectural violation.

---

## Article II — The Canonical Pipeline

The canonical pipeline is the single authoritative execution path for every user action.

### §2.1 Pipeline definition

```
Human Intent
    ↓
① Intent Resolution      — classify, parameterize, route
② Identity Resolution    — who is acting
③ Object Resolution      — which universal object
④ Knowledge Graph Update — update relationships
⑤ Memory Update          — store in working/episodic memory
⑥ Planning Update        — re-evaluate goals and plans
⑦ Reasoning Update       — infer consequences
⑧ Execution Update       — execute commitments
⑨ Automation Evaluation  — evaluate triggers and rules
⑩ Projection Assembly    — build workspace view
    ↓
Workspace Update
    ↓
Human
```

### §2.2 Pipeline invariants

1. Every intent completes exactly one pipeline pass.
2. Every runtime in the pipeline receives the pipeline context.
3. Every runtime may return events that feed back into the pipeline.
4. No step may be skipped. If a step has no work, it must explicitly declare "no-op."
5. The pipeline is deterministic for the same input state.
6. The pipeline produces an execution trace that is queryable by projection_id.

### §2.3 Pipeline context

```
PipelineContext {
    intent_id: str          — unique per action
    intent: str             — e.g. "talk_to_customer"
    parameters: dict        — extracted parameters
    identity_id: str        — resolved actor
    object_id: str | None   — resolved object (if applicable)
    trace: List[StepRecord] — populated as pipeline executes
    state: PipelineState    — RUNNING, COMPLETED, FAILED
    started_at: str
    completed_at: str | None
}
```

---

## Article III — Universal Object Model

Every business entity inside SHUNYA exists as one universal object. No runtime may create a parallel object representation.

### §3.1 UniversalObject contract

```python
UniversalObject {
    object_id: str          — permanent, unique, never reused
    type: str               — from Universal Type System
    name: str               — human-readable label
    status: ObjectStatus    — lifecycle state
    confidence: float       — 0.0–1.0
    identity_ids: list[str] — resolved owner identities
    relationships: list[Relationship]
    evidence: list[EvidenceRef]
    timeline: list[TimelineEvent]
    commitments: list[CommitmentRef]
    memory: list[MemoryRef]
    projections: list[ProjectionRef]
    attributes: dict        — type-specific key-value pairs
    metadata: {
        created_at, updated_at, created_by, updated_by,
        provenance, version
    }
}
```

### §3.2 Object invariants

1. Every object has exactly one `object_id`. It is assigned at creation and never changes.
2. Every object has exactly one `type`. It is assigned at creation and never changes.
3. Every object has exactly one `status` at any time.
4. Every object carries its complete evidence chain.
5. Every object carries its complete timeline.
6. Every object carries its current commitments.
7. Every object's memory is queryable across all memory layers.
8. Every object's projections are computed by the Projection Runtime — never stored on the object itself.

### §3.3 Convergence requirement

The following object representations must converge onto UniversalObject:

| Current representation | Type | Converged to | Priority |
|---|---|---|---|
| `app.founder.models.FounderObject` | Flask-SQLAlchemy model | UniversalObject | P0 |
| `core.kernel.object.UniversalObject` | Dataclass (kernel) | UniversalObject (authoritative) | P0 |
| `core.memory_knowledge_runtime models.MemoryObject` | Dataclass | UniversalObject adapter | P1 |
| `core.graph.*.Node` | Graph node | UniversalObject graph binding | P1 |
| `app.models.Lead` | Flask-SQLAlchemy model | UniversalObject | P2 |
| `app.models.Task` | Flask-SQLAlchemy model | UniversalObject | P2 |
| `app.models.Payment` | Flask-SQLAlchemy model | UniversalObject | P2 |
| `app.models.Document` | Flask-SQLAlchemy model | UniversalObject | P2 |
| `app.models.Invoice` | Flask-SQLAlchemy model | UniversalObject | P2 |

---

## Article IV — Runtime Grammar

Every runtime shall explicitly define its responsibilities and prohibitions. These boundaries are immutable.

### §4.1 Kernel Runtime

| Aspect | Definition |
|--------|-----------|
| **May** | Define types, state machines, object contracts, space model, timeline append, context assembly |
| **Must never** | Execute business actions, infer identity, query external systems, hold business-specific state |
| **Produces** | `ObjectCreated`, `ObjectUpdated`, `ObjectArchived`, `StateTransitioned`, `TypeRegistered` |
| **Consumes** | `IntentResolved` (from Intent Pipeline) |

### §4.2 Identity Runtime

| Aspect | Definition |
|--------|-----------|
| **May** | Resolve identity, manage auth methods, merge/split/retire identities, maintain audit trail |
| **Must never** | Execute business actions, create/update business objects, hold business state |
| **Produces** | `IdentityResolved`, `IdentityCreated`, `AuthMethodAdded`, `IdentityMerged`, `IdentityRetired` |
| **Consumes** | `IntentResolved` (from Intent Pipeline) |

### §4.3 Knowledge Graph Runtime

| Aspect | Definition |
|--------|-----------|
| **May** | Store nodes and edges, traverse relationships, validate graph consistency, enforce security policies |
| **Must never** | Execute business actions, infer identity, hold mutable business state outside graph |
| **Produces** | `NodeCreated`, `NodeUpdated`, `NodeArchived`, `EdgeCreated`, `EdgeArchived`, `RelationshipChanged` |
| **Consumes** | `ObjectResolved`, `IdentityResolved` |

### §4.4 Memory Runtime

| Aspect | Definition |
|--------|-----------|
| **May** | Store, retrieve, search, and consolidate memory across 6 layers (working, conversation, relationship, knowledge, historical, constitutional) |
| **Must never** | Execute business actions, create/update business objects, modify knowledge graph directly |
| **Produces** | `MemoryStored`, `MemoryConsolidated`, `MemoryPromoted`, `MemoryDecayed` |
| **Consumes** | `KnowledgeGraphUpdated` |

### §4.5 Planning Runtime

| Aspect | Definition |
|--------|-----------|
| **May** | Decompose goals, generate plans, validate constraints, estimate cost/risk, manage alternatives |
| **Must never** | Execute plans, mutate business objects, send external communications |
| **Produces** | `PlanCreated`, `PlanValidated`, `PlanRejected`, `ConstraintViolated`, `AlternativeGenerated` |
| **Consumes** | `ObjectUpdated`, `CommitmentCreated` |

### §4.6 Reasoning Runtime

| Aspect | Definition |
|--------|-----------|
| **May** | Infer relationships, detect patterns, evaluate risks, predict outcomes, explain recommendations |
| **Must never** | Execute actions, mutate state, issue external commands |
| **Produces** | `InferenceDrawn`, `RiskAssessed`, `PredictionUpdated`, `RecommendationGenerated` |
| **Consumes** | `KnowledgeGraphUpdated`, `MemoryRetrieved` |

### §4.7 Execution Runtime

| Aspect | Definition |
|--------|-----------|
| **May** | Execute commitments, manage execution lifecycle, roll back failed executions, enforce policies |
| **Must never** | Infer identity, create/update knowledge graph nodes, modify memory directly |
| **Produces** | `ExecutionCreated`, `ExecutionCompleted`, `ExecutionFailed`, `ExecutionRolledBack`, `CommitmentExecuted` |
| **Consumes** | `PlanApproved`, `IntentToExecute` |

### §4.8 Automation Runtime

| Aspect | Definition |
|--------|-----------|
| **May** | Publish/subscribe events, evaluate triggers, execute workflows, manage dead-letter queue, enforce idempotency |
| **Must never** | Mutate business state directly (must delegate to Execution Runtime) |
| **Produces** | `EventPublished`, `TriggerFired`, `WorkflowAdvanced`, `WorkflowCompleted`, `DeadLetterEvent` |
| **Consumes** | All runtime events |

### §4.9 Integration Runtime

| Aspect | Definition |
|--------|-----------|
| **May** | Communicate with external systems, manage connectors, enforce rate limits, handle retry/circuit-breaker |
| **Must never** | Hold business state, execute business logic, make business decisions |
| **Produces** | `ExternalMessageSent`, `ExternalMessageReceived`, `ConnectionStateChanged`, `RateLimitExceeded` |
| **Consumes** | `ExecutionCompleted` (when execution requires external action) |

### §4.10 Projection Runtime

| Aspect | Definition |
|--------|-----------|
| **May** | Assemble projections from runtime state, cache projections, return degraded projections on failure |
| **Must never** | Mutate business state, modify knowledge graph, execute business actions |
| **Produces** | `ProjectionAssembled`, `ProjectionCached`, `ProjectionInvalidated` |
| **Consumes** | All runtime events (to invalidate caches) |

### §4.11 Audit Runtime

| Aspect | Definition |
|--------|-----------|
| **May** | Record immutable audit entries, query audit history, enforce retention policies |
| **Must never** | Modify audit entries, execute business actions, hold business state |
| **Produces** | `AuditEntryCreated` |
| **Consumes** | All runtime events |

---

## Article V — Intent-first Architecture

No operation shall be designed around CRUD. Every operation begins with business intent.

### §5.1 Intent catalogue

| Intent | Description | Pipeline stages invoked |
|--------|-------------|----------------------|
| `talk_to_customer` | Engage with a person or organization | Intent → Identity → Object → Graph → Memory → Plan → Reason → Execute → Automate → Project |
| `understand_opportunity` | Learn about a potential value exchange | Intent → Identity → Object → Graph → Memory → Reason → Project |
| `commit_to_follow_up` | Promise future action | Intent → Identity → Object → Graph → Memory → Plan → Execute → Project |
| `approve_proposal` | Authorize a course of action | Intent → Identity → Object → Graph → Memory → Reason → Execute → Automate → Project |
| `execute_work` | Perform a defined action | Intent → Identity → Object → Graph → Memory → Plan → Execute → Automate → Integration → Project |
| `learn_from_outcome` | Incorporate results into knowledge | Intent → Object → Graph → Memory → Reason → Project |

### §5.2 Intent resolution

The Intent Runtime (core/intent/) resolves raw input to structured intent:
- Pattern-matches against known intents
- Extracts parameters (entities, dates, references)
- Routes to pipeline with appropriate runtime subset
- Returns structured `IntentResult` with confidence

---

## Article VI — Capability States

Replace phase-oriented reporting with a living capability matrix.

| State | Definition |
|-------|-----------|
| **Designed** | Architecture defined, interfaces specified, no implementation |
| **Implemented** | Code exists, unit tests pass, standalone module |
| **Integrated** | Wired into canonical pipeline, participating in OS |
| **Operational** | End-to-end tested, metrics collected, production-ready |

### §6.1 Current state (Phase L baseline)

| Capability | State | Notes |
|-----------|-------|-------|
| Kernel (types, state, objects) | **Implemented** | Standalone in core/kernel/, partially used by founder routes |
| Identity | **Implemented** | Standalone in core/identity/, partially used |
| Knowledge Graph | **Implemented** | Standalone in core/memory_knowledge_runtime/ |
| Memory | **Implemented** | Standalone |
| Planning | **Implemented** | Standalone |
| Reasoning | **Implemented** | Standalone |
| Execution | **Implemented** | Standalone |
| Automation | **Implemented** | Standalone |
| Integration | **Implemented** | Standalone |
| Projection | **Implemented** | Standalone |
| Workspace | **Implemented** | Standalone |
| Intent Pipeline | **Designed** | Not yet implemented |
| Canonical Pipeline | **Designed** | Not yet implemented |
| OS Kernel Bootstrap | **Designed** | Not yet implemented |

---

## Article VII — Convergence Directives

### §7.1 Immediate actions

1. **Create the canonical pipeline** — `core/runtime_pipeline/` — the single execution path
2. **Create the OS kernel** — `core/os.py` — the bootstrap that wires all runtimes
3. **Implement the Intent Runtime** — `core/intent/` — intent resolution
4. **Wire all runtimes** — each runtime registers with the OS kernel
5. **Produce traces** — every pipeline execution produces a structured trace

### §7.2 Migration actions

1. Add `core/os.py` adapters between Flask routes and core runtimes
2. Migrate `app.founder.models.FounderObject` to use `core.kernel.object.UniversalObject` as authoritative
3. Remove demo data paths (Next.js `data/objects.ts`, founder scenario data)
4. Wire Next.js frontend to Flask API that calls the canonical pipeline

### §7.3 Forbidden items

- No new Flask-SQLAlchemy models for domain concepts
- No new hardcoded demo data
- No new route that bypasses the canonical pipeline
- No new parallel object representations

---

## Article VIII — Verification

### §8.1 Pipeline verification

Every canonical pipeline execution must produce:
- A `PipelineContext` with complete trace
- Every step recorded with start/end time, result, and runtime identity
- No step skipped (explicit no-op declaration allowed)
- Deterministic output for same input state

### §8.2 Integration verification

For each integrated runtime:
- Input contract test passes
- Output contract test passes  
- Event production test passes
- Health check returns healthy
- Trace contributes to pipeline trace

### §8.3 Convergence verification

- Count of business object representations must not increase
- Count of execution paths must not increase
- Count of workspace implementations must not increase
- Count of demo data paths must not increase

---

*This Constitution is the governing document for all SHUNYA OS development from Phase L onward. No implementation may violate these articles. Violations must be remediated within one phase cycle.*