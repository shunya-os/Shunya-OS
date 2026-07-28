# SHUNYA Architecture Specification v1.0

> **Authoritative engineering reference — SHUNYA Operating System v1.x**
>
> This document is the constitutional reference for all SHUNYA development.
> It defines what SHUNYA IS, not merely what it currently DOES.
> Every engineer and AI agent building on this platform must understand
> and uphold the architecture documented here.

---

## Table of Contents

- [Part I — Vision](#part-i--vision)
- [Part II — Canonical Domain](#part-ii--canonical-domain)
- [Part III — Runtime](#part-iii--runtime)
- [Part IV — Execution Architecture](#part-iv--execution-architecture)
- [Part V — Execution Intelligence](#part-v--execution-intelligence)
- [Part VI — Autonomous Operational Awareness](#part-vi--autonomous-operational-awareness)
- [Part VII — Organizational Intelligence](#part-vii--organizational-intelligence)
- [Part VIII — Knowledge Architecture](#part-viii--knowledge-architecture)
- [Part IX — Memory Architecture](#part-ix--memory-architecture)
- [Part X — Governance](#part-x--governance)
- [Part XI — API Philosophy](#part-xi--api-philosophy)
- [Part XII — Data Ownership](#part-xii--data-ownership)
- [Part XIII — Architectural Decision Records](#part-xiii--architectural-decision-records)
- [Part XIV — Engineering Constitution](#part-xiv--engineering-constitution)
- [Part XV — Extension Points](#part-xv--extension-points)

---

# Part I — Vision

## 1.1 Mission

SHUNYA exists to enable any organization to operate with **deterministic, explainable, business-agnostic intelligence** across every dimension of execution: planning, governance, execution, observation, learning, and organizational awareness.

SHUNYA is not a CRM. Not a project management tool. Not an ERP. It is the **operating system** beneath all of them — the substrate on which domain-specific applications are built without rebuilding the intelligence layer.

## 1.2 Philosophy

1. **Deterministic-first.** Given identical inputs and state, every engine produces identical outputs. No randomness. No ML opacity. No hidden state.
2. **Business-agnostic.** No core engine contains travel, healthcare, retail, or any domain-specific assumption. All business knowledge is data, not code.
3. **Evidence-backed.** Every computed conclusion carries traceable evidence. No output exists without provenance.
4. **Explainable.** Every intelligence output can be decomposed into its contributing evidence and reasoning steps.
5. **Role-centric, not person-centric.** Organizations are modeled as systems of roles. Persons fulfill roles. Roles hold responsibilities, authority, and ownership.
6. **No duplicated state.** Every canonical entity exists in exactly one module. Derived state is recomputed, not cached.
7. **Event-driven awareness.** The system is continuously aware through deterministic observation propagation, not polling.
8. **Immutable history.** State transitions are recorded, never overwritten. History is append-only.

## 1.3 Non-Goals

- SHUNYA does **not** replace human judgment. It provides intelligence that humans (or authorized agents) act upon.
- SHUNYA does **not** store business-specific data models (customer profiles, product catalogs, pricing tiers). Those belong in domain applications built on SHUNYA.
- SHUNYA does **not** provide a UI. It is a computation engine with defined APIs.
- SHUNYA does **not** execute arbitrary external actions without governance approval.
- SHUNYA does **not** learn from execution in a way that mutates canonical state without evidence.
- SHUNYA does **not** require a paid model API for core reasoning. All intelligence engines are pure computation.

## 1.4 Business-Agnostic Principles

1. Domain-specific concepts appear **only** as string labels on canonical entities (e.g., `commitment_type="booking"`, `obl_type="payment"`).
2. All engines operate on entity state, not entity meaning.
3. Domain-specific validation and business rules belong in Governance policies, not in core engines.
4. New business domains require zero core changes — only policy definitions and data intake.

## 1.5 Deterministic-First Principles

1. Pure computation functions produce identical outputs for identical inputs.
2. Randomness is prohibited in all intelligence engines.
3. Time-dependent computations (e.g., timeline prediction) are explicit about their time basis.
4. Idempotency keys prevent duplicate processing in pipelines.
5. Module-level singletons are resettable for test determinism.

## 1.6 Evidence-Backed Reasoning

Every intelligence output carries an `evidence: List[str]` field. Each string traces to a specific piece of observable state:

- A state value (`exec_id=e1`, `state=blocked`)
- An audit log entry (`approved_at=2026-07-21T12:00:00Z`)
- A responsibility record (`provenance=responsibility_graph`)
- An observation ID (`triggered_by=obs_abc123`)
- A computed metric (`satisfied=3/5 obligations`)

Evidence is not optional. An output without evidence is not a valid output.

## 1.7 Explainability Philosophy

Every intelligence component includes an `ExplainabilityLayer` that:

1. Receives the same inputs as the computation engine.
2. Produces a structured `Explanation` with `topic`, `conclusion`, `traces` (list of `EvidenceTrace`), and `confidence`.
3. Is deterministic: same inputs → same explanation.
4. Is separable: explanations can be generated without re-running the computation.

---

# Part II — Canonical Domain

## 2.1 Entity Catalog

The following are all canonical entities in the SHUNYA domain. Each belongs to exactly one module. Entities from other modules are referenced by ID only — never duplicated.

### 2.1.1 Tenant & Auth Layer (`app/tenant.py`, `app/auth.py`)

| Entity | Module | Description |
|---|---|---|
| `Tenant` | `app.tenant` | A company/tenant using SHUNYA. Isolated data namespace. |
| `TenantTheme` | `app.tenant` | Per-company theme (branding, colors, logo). |
| `TeamMember` | `app.auth` | A person with login credentials and role-based access. |
| `UserRole` | `app.auth` | Enum: ADMIN, MANAGER, AGENT. |

### 2.1.2 Business Execution (`app/execution/__init__.py`)

| Entity | Module | Description |
|---|---|---|
| `BusinessExecutionInstance` | `app.execution` | A single business execution (e.g., fulfilling a booking, processing a payment). |
| `ExecutionObligation` | `app.execution` | An individual obligation within an execution (e.g., "collect payment"). |
| `ExecutionResourceAllocation` | `app.execution` | Allocation of a resource to an execution. |
| `ExecutionResourceConsumption` | `app.execution` | Consumption of an allocated resource. |
| `ExecutionResourceRequirement` | `app.execution` | Expected resource need for an obligation. |
| `ExecutionException` | `app.execution` | An exception or anomaly recorded on an execution. |
| `ExecutionService` | `app.execution` | In-memory service managing all execution entities. |

**Lifecycle states** (`ExecState`): PENDING → ACTIVE → (BLOCKED | AT_RISK | PARTIALLY_FULFILLED) → FULFILLED | FAILED | CANCELLED.

**Obligation states** (`ObligationState`): PENDING → READY → IN_PROGRESS → (SATISFIED | FAILED | WAIVED). May enter BLOCKED at any point.

### 2.1.3 Execution Intelligence (`app/execution_intelligence/`)

| Entity | Module | Description |
|---|---|---|
| `HealthAssessment` | `execution_intelligence.models` | Multi-dimensional health evaluation of an execution. |
| `TimelineSnapshot` | `execution_intelligence.models` | Progress snapshot with milestone tracking. |
| `CompletionPrediction` | `execution_intelligence.models` | Predicted completion time with confidence. |
| `RiskAssessment` | `execution_intelligence.models` | Risk evaluation with typed factors. |
| `RiskFactor` | `execution_intelligence.models` | Single identified risk with evidence. |
| `NextAction` | `execution_intelligence.models` | Recommended action with priority and evidence. |
| `PortfolioSummary` | `execution_intelligence.models` | Cross-execution aggregated intelligence. |
| `EvidenceTrace` | `execution_intelligence.models` | A single traceable evidence item. |
| `Explanation` | `execution_intelligence.models` | Full explanation with evidence chain. |

### 2.1.4 Autonomous Operational Awareness (`app/awareness/`)

| Entity | Module | Description |
|---|---|---|
| `CanonicalObservation` | `awareness.models` | Unified event type — every system event becomes one of these. |
| `ObservationEnrichment` | `awareness.models` | Contextual enrichment added by the pipeline. |
| `ImpactAssessment` | `awareness.models` | What an observation changes about system understanding. |
| `AwarenessSnapshot` | `awareness.models` | Current awareness state for a single execution. |
| `OrganizationalAwarenessState` | `awareness.models` | Per-tenant aggregated awareness. |
| `PrioritizedObservation` | `awareness.models` | Observation with computed priority score. |
| `AwarenessMemoryEntry` | `awareness.models` | A single entry in the awareness ring buffer. |

**Observation categories** (11): execution_state_change, execution_health_change, risk_level_change, obligation_change, resource_change, exception_occurred, intelligence_output, portfolio_change, timeline_event, external_signal, system_event.

### 2.1.5 Organizational Intelligence (`app/organizational/`)

| Entity | Module | Description |
|---|---|---|
| `OrgUnit` | `organizational.models` | An organizational unit (department, team, project). Hierarchical. |
| `OrgRole` | `organizational.models` | A role within the organization. |
| `RoleAssignment` | `organizational.models` | Assignment of a person to a role in a unit. |
| `Responsibility` | `organizational.models` | A role's responsibility for an entity. |
| `Ownership` | `organizational.models` | Ownership of an entity by a role or person. |
| `Delegation` | `organizational.models` | Temporary transfer of authority between roles. |
| `Authority` | `organizational.models` | Authority grant for a specific action on an entity type. |
| `ApprovalChain` | `organizational.models` | Multi-step approval workflow. |
| `Collaboration` | `organizational.models` | Recorded interaction between roles. |
| `OrgHealth` | `organizational.models` | Health assessment of an organizational unit. |
| `InstitutionalMemoryEntry` | `organizational.models` | A piece of institutional knowledge. |
| `OrgKnowledgeNode` | `organizational.models` | A node in the organizational knowledge graph. |
| `OrgKnowledgeEdge` | `organizational.models` | A relationship edge in the knowledge graph. |

### 2.1.6 Observer Engine (`app/shunya/observer_engine/`)

| Entity | Module | Description |
|---|---|---|
| `VerifiedObservation` | `observer_engine.models` | A validated, immutable record of what actually happened. |
| `DeviationReport` | `observer_engine.models` | Quantified deviation between expected and actual. |
| `AnomalyReport` | `observer_engine.models` | Report of an unexpected pattern or outlier. |
| `LearningSignal` | `observer_engine.models` | Structured signal for the Learning Engine. |
| `EvidenceValidationResult` | `observer_engine.models` | Quality assessment across 6 evidence dimensions. |

### 2.1.7 Engine Pipeline Modules

| Entity | Module | Description |
|---|---|---|
| `Planner Engine` | `app/shunya/planner/` | ES-004: 9-stage deterministic planning pipeline. |
| `Governance Engine` | `app/shunya/governance_engine/` | ES-001: 6-stage deterministic governance validation. |
| `Executor Engine` | `app/shunya/executor_engine/` | ES-005: 9-stage deterministic execution pipeline. |
| `Observer Engine` | `app/shunya/observer_engine/` | ES-006: 9-stage deterministic observation pipeline. |
| `Learning Engine` | `app/shunya/learning_engine/` | ES-007: 9-stage deterministic learning pipeline. |
| `Knowledge Engine` | `app/shunya/knowledge_engine/` | ES-002: Immutable versioned fact store. |
| `Reasoning Engine` | `app/shunya/reasoning/` | Evidence-grounded reasoning with confidence scoring. |
| `Context Fusion Engine` | `app/shunya/context_fusion_engine/` | ES-009: Snapshot-consistent workspace context. |
| `Identity Engine` | `app/shunya/identity/` | Human identity resolution and normalization. |

### 2.1.8 Service Modules

| Module | Description |
|---|---|
| `app/privacy/` | Privacy policies, sensitivity, retention, forget requests. |
| `app/memory/` | Memory records, candidates, provenance. |
| `app/evidence/` | Source references, evidence links, assertion records. |
| `app/document/` | Document records, sections, comparisons. |
| `app/llm/` | LLM model run tracking (audit, not core reasoning). |
| `app/relationship/` | Relationship intelligence (person-to-person, person-to-organization). |
| `app/communication/` | Communication ingestion, normalization, policies. |
| `app/intake/` | Data intake and transformation pipeline. |
| `app/human_context/` | Human context items, proposals, concepts. |
| `app/planning/` | Persistent plans governed by the Planner Engine. |
| `app/runtime/` | Evidence runtime distinction service. |
| `app/relevance/` | Relevance and attention scoring. |
| `app/inference/` | Inference control plane. |
| `app/acquisition/` | Acquisition source and paid lead intake. |
| `app/automation/` | Automation and trigger engine. |
| `app/artifact/` | Artifact and document generation. |
| `app/growth/` | Growth and campaign intelligence. |
| `app/brand/` | Creative intelligence and brand runtime. |
| `app/assistant/` | Relationship-aware assistant. |
| `app/learning/` | Closed learning loop. |
| `app/knowledge/` | Internal-first knowledge resolution. |
| `app/world/` | World intelligence (external data integration). |
| `app/watch/` | Watch/monitoring service. |

## 2.2 Entity Identity

All entities carry an `entity_id` generated by `hashlib.sha256(unique_raw_material).hexdigest()[:16]`. The raw material is chosen to guarantee uniqueness within the tenant:

- `BusinessExecutionInstance`: `f"{tenant_id}:{commitment_type}:{commitment_id}"`
- `ExecutionObligation`: `f"{exec_id}:{obl_type}:{description}"`
- `CanonicalObservation`: `f"{source}:{source_id}:{timestamp}"`
- `OrgUnit`: `f"{tenant_id}:{name}:{timestamp}"`
- All others follow the same pattern.

Entity IDs are **deterministic** given the same inputs but are **not** semantically meaningful. They are 16-character hex strings.

## 2.3 Tenant Identity

Every entity carries `tenant_id: int`. The tenant namespace is the fundamental isolation boundary:
- No cross-tenant queries in core engines.
- Cross-tenant data access requires explicit authorization in Governance.
- Execution service methods validate tenant_id on every operation.

## 2.4 Invariants

1. **No orphaned references.** If entity A references entity B by ID, B must exist within the same tenant.
2. **No cycle in dependencies.** The `ExecutionService.add_dependency()` method validates acyclic graphs.
3. **No terminal state transitions.** FULFILLED, FAILED, and CANCELLED are terminal — no transitions out.
4. **No stale delegations.** The `DelegationEngine.get_active()` method filters expired delegations.
5. **No duplicate idempotency keys.** The `ObservationPipeline` rejects already-seen keys.
6. **No supersession without history.** When ownership transfers, the previous ownership is marked `superseded_at`, never deleted.

---

# Part III — Runtime

## 3.1 Execution Lifecycle

```
Planner → Governance → Executor → Observer → Learning
                                     ↓
                           Execution Intelligence
                                     ↓
                           Autonomous Awareness
```

The core pipeline is:

1. **Planner** produces a plan (set of tasks with dependencies).
2. **Governance** validates the plan against policies. Returns approved or rejected.
3. **Executor** transforms approved plans into real-world actions via channel adapters.
4. **Observer** validates execution evidence, detects deviations/anomalies, packages observations.
5. **Learning** processes learning signals from observations to improve future planning.
6. **Execution Intelligence** continuously assesses health, risk, timeline, and next actions.
7. **Autonomous Awareness** ingests all system events as canonical observations and propagates them.

## 3.2 Observation Lifecycle

```
System Event
    ↓
CanonicalObservation (11 categories)
    ↓
ObservationPipeline → validate → enrich → prioritize
    ↓
ChangeImpactAnalyzer → what does this observation change?
    ↓
ContinuousRiskMonitor → re-evaluate risk for affected executions
    ↓
OrganizationalAwareness → update per-tenant awareness state
    ↓
AwarenessMemory → record in ring buffer
    ↓
Propagation to: ExecutionIntelligence, Memory, Planner, Knowledge
```

## 3.3 Planner (ES-004)

The Planner Engine implements a deterministic 9-stage pipeline:

1. Input Intake & Validation
2. Goal Analysis & Objective Setting
3. Context Gathering & Evidence Collection
4. Option Generation (computation-only, no AI)
5. Constraint Evaluation
6. Dependency Mapping
7. Step Sequencing (topological ordering)
8. Plan Packaging
9. Governance Handoff

The planner does NOT:
- Reason about goals (Reasoning Engine)
- Approve/reject plans (Governance Engine)
- Execute plans (Executor Engine)
- Learn from outcomes (Learning Engine)

## 3.4 Governance (ES-001)

The Governance Engine implements a deterministic 6-stage pipeline:

1. Input Intake
2. Policy Resolution
3. Constraint Evaluation
4. Risk Assessment
5. Approval Decision
6. Audit Logging

Governance is:
- **Stateless**: decisions depend only on inputs and policies.
- **Deterministic**: same plan + same policies → same verdict.
- **Audited**: every decision is logged with reason.

## 3.5 Memory Architecture (Revisited)

Memory in SHUNYA is not a cache. It is a **canonical record**:

- `MemoryRecord`: A stored memory with effective date, provenance, and dispute status.
- `MemoryCandidate`: A proposed memory awaiting approval.
- `MemoryProvenance`: Chain of custody for a memory.
- `MemoryEligibilityPolicy`: Rules determining what can become memory.

Memory flows: Observation → MemoryEligibility check → MemoryCandidate → Approval → MemoryRecord.

## 3.6 Knowledge Architecture (Revisited)

Knowledge in SHUNYA is the **authoritative fact layer**:

- `KnowledgeFact`: An immutable fact with version history.
- `KnowledgeObject`: A versioned knowledge entry with namespace, type, payload.
- `SearchQuery/Filter`: Deterministic retrieval with type/namespace filtering.
- `VersionHistory`: Immutable version lineage with rollback capability.

Knowledge is written by the Knowledge Engine and read by all other engines. No engine bypasses the knowledge layer to store authoritative facts.

## 3.7 Runtime Coordination

The `ExecutionIntelligenceEngine`, `AwarenessEngine`, and `OrganizationalIntelligenceEngine` are **independent facades**. They do not call each other directly. Coordination happens through:

1. **Shared state**: All engines read from `ExecutionService` (the canonical execution store).
2. **Event propagation**: The `RuntimeService` in `AwarenessEngine` receives observations and calls `ExecutionIntelligence` for risk/health re-evaluation.
3. **Singleton access**: Each engine provides `get_*()` / `reset_*()` for module-level singleton management.

## 3.8 Scheduling

SHUNYA does not have a built-in scheduler. Scheduled operations (cron, timed tasks) are considered external signals that generate `CanonicalObservation` entries via the awareness pipeline. Time-based checks (stale awareness, expired delegations) are evaluated on access, not via background processes.

## 3.9 Event Propagation

Events propagate through the awareness layer:

```
1. Source (any engine or external system) creates CanonicalObservation
2. ObservationPipeline processes: validate → enrich → prioritize
3. ChangeImpactAnalyzer assesses impact
4. ContinuousRiskMonitor re-evaluates risk for affected executions
5. OrganizationalAwareness updates awareness snapshot
6. AwarenessMemory records in ring buffer
```

Propagation targets are determined by observation category:
- Execution state change → `execution_intelligence`
- Exception occurred → `memory`
- Intelligence output → `planner`
- All → `awareness`

---

# Part IV — Execution Architecture

## 4.1 BusinessExecutionInstance

`BusinessExecutionInstance` is the **canonical runtime entity** representing a single business execution. It is computation-only — it holds state but does not execute anything.

```
BusinessExecutionInstance
├── exec_id          : str (canonical ID)
├── tenant_id        : int
├── commitment_type  : str (domain label, e.g. "booking", "payment")
├── commitment_id    : str (external reference)
├── state            : ExecState
├── created_at       : str (ISO datetime)
├── started_at       : str | None
├── completed_at     : str | None
├── plan_refs        : List[str]
├── workflow_refs    : List[str]
├── history          : List[dict] (append-only state transitions)
```

**Lifecycle:**

```
PENDING → ACTIVE → (BLOCKED | AT_RISK | PARTIALLY_FULFILLED) → FULFILLED
                                                              → FAILED
                                                              → CANCELLED
```

Terminal states: FULFILLED, FAILED, CANCELLED. No transitions out.

**Why it exists (ADR-001):** See Part XIII.

## 4.2 Execution Services

`ExecutionService` manages all execution entities in-memory:

- `activate()` — Create a new execution instance (idempotent by tenant:type:id key).
- `transition()` — Change execution state with validation against `ExecState.VALID_TRANSITIONS`.
- `add_obligation()` — Add an obligation to an execution.
- `add_dependency()` — Add a dependency between obligations (with cycle detection).
- `allocate_resource()`, `record_consumption()`, `add_requirement()` — Resource tracking.
- `compute_resource_position()` — Deterministic resource position calculation.
- `add_exception()` — Record an exception.
- `inspect()` — Full execution inspection with obligations, exceptions, resource position.

## 4.3 Commitments

A `BusinessExecutionInstance` is created in response to a **commitment**. Commitments come from external systems (e.g., a booking confirmation, a payment authorization) and are identified by `commitment_type` (domain string) and `commitment_id` (external ID).

Commitments are **not** stored as canonical entities — they are external references. The `commitment_type` string is the only domain-specific concept in the execution layer.

## 4.4 Evidence

Execution evidence is collected by the Executor Engine and validated by the Observer Engine across 6 dimensions:

1. **Completeness** — All required fields present.
2. **Authenticity** — Evidence IDs are non-empty and unique.
3. **Consistency** — Evidence success/failure matches task states.
4. **Correlation** — Evidence references known task IDs.
5. **Timestamp integrity** — Timestamps are present and not in the future.
6. **Provenance** — Evidence has a known source (channel).

Quality score is the **product** of all 6 dimensions (multiplicative per ES-006).

## 4.5 Dependencies

Dependencies between obligations form a directed acyclic graph (DAG). The `ExecutionService` enforces acyclicity via DFS cycle detection on every `add_dependency()` call.

Dependencies are used by:
- **Execution Intelligence**: `DependencyGraphEngine` builds the DAG and finds critical paths.
- **Next Action Engine**: Blocked obligations (all dependencies unsatisfied) trigger unblock recommendations.
- **Health Engine**: Blocked obligations reduce dependency health dimension score.

---

# Part V — Execution Intelligence

## 5.1 Health Engine

The `ExecutionHealthEngine` evaluates execution health across **6 dimensions**:

| Dimension | Weight | Description |
|---|---|---|
| State | 25% | Execution state validity (ACTIVE=healthy, BLOCKED=critical, etc.) |
| Progress | 20% | Ratio of satisfied to total obligations |
| Timeliness | 15% | Proportion of overdue timed obligations |
| Resource Position | 15% | Resource sufficiency (sufficient → healthy, shortfall → critical) |
| Exception Burden | 10% | Penalty per exception (each → -0.15) |
| Dependency Health | 15% | Penalty per blocked obligation (each → -0.20) |

**Terminal state early return:** FULFILLED → healthy. FAILED → critical. CANCELLED → critical. BLOCKED → critical. These skip dimension computation.

**Overall score:** Weighted average of all dimensions. Thresholds: >=0.7 healthy, >=0.4 warning, >0 at_risk, 0 critical.

## 5.2 Timeline Intelligence

The `TimelineIntelligenceEngine` tracks progress and predicts completion:

- **Snapshot**: Records elapsed time, completion ratio (satisfied/total obligations), milestones passed/remaining.
- **Prediction**: `remaining = elapsed / completion_ratio - elapsed`. Confidence = min(0.9, completion_ratio). Optimistic = 0.7×, Pessimistic = 1.5×.

Not started → confidence 0.0. Already completed → confidence 1.0.

## 5.3 Risk Detection

The `RiskDetectionEngine` evaluates 5 risk patterns:

| Risk Pattern | Trigger | Level |
|---|---|---|
| Timeout | Execution active > 48h threshold | HIGH |
| Blocked Obligations | Any blocked obligations | HIGH |
| Resource Shortfall | Resource position < 0.4 threshold | CRITICAL |
| Critical Exceptions | High/critical severity exceptions | HIGH |
| Stalled Progress | No obligations satisfied in 24h+ | MEDIUM |

Overall risk: If any CRITICAL factor → CRITICAL. If any HIGH → HIGH. If any MEDIUM → MEDIUM. Else NONE.

## 5.4 Portfolio Intelligence

The `PortfolioIntelligence` aggregates across all executions for a tenant:

- State breakdown (active, fulfilled, failed, cancelled, etc.)
- Health distribution (healthy, warning, at_risk, critical)
- Top K risks across portfolio
- Top K next actions across portfolio

## 5.5 Next Action Engine

Deterministic rule-based recommendations:

| Action Type | Trigger | Priority |
|---|---|---|
| Unblock obligation | Blocked obligations | IMMEDIATE if overdue, else HIGH |
| Satisfy obligation | Ready obligations | IMMEDIATE if overdue, else HIGH |
| Mitigate risk | CRITICAL/HIGH risk factors | IMMEDIATE if CRITICAL, else HIGH |
| Allocate resources | Resource shortfall detected | HIGH |
| Escalate overdue | Overdue pending obligations | IMMEDIATE |

Results are deduplicated by action type + description and capped at 10.

## 5.6 Explainability

Every intelligence output includes an `ExplainabilityLayer` that produces:

- `topic`: What is being explained.
- `conclusion`: Human-readable summary.
- `traces`: List of `EvidenceTrace` objects (claim, evidence, source, confidence).
- `confidence`: Overall confidence in the explanation.

---

# Part VI — Autonomous Operational Awareness

## 6.1 Canonical Observation Model

Every meaningful system event becomes a `CanonicalObservation` with:

- `observation_id`: Deterministic hash of source + source_id + timestamp.
- `category`: One of 11 categories (see 2.1.4).
- `tenant_id`: Tenant namespace.
- `source`: Which component generated this (e.g., "execution", "execution_intelligence").
- `source_id`: Specific entity ID (exec_id, obl_id, etc.).
- `previous_state` / `current_state`: State transition that triggered the observation.
- `payload`: Structured event data.
- `idempotency_key`: Used for de-duplication.
- `priority`: Computed by the pipeline.

## 6.2 Observation Pipeline

The pipeline is: **validate → enrich → prioritize**.

1. **Idempotency check**: If `idempotency_key` already seen, mark as duplicate and return.
2. **Validation**: Missing tenant_id? Missing source? Unknown category?
3. **Enrichment**: Determine propagation targets based on category.
4. **Priority computation**: Category-based mapping (exception→CRITICAL, risk→HIGH, system→INFO).

## 6.3 Impact Analysis

The `ChangeImpactAnalyzer` determines what each observation changes:

| Category | Impact Type |
|---|---|
| execution_state_change | STATE_CHANGE |
| exception_occurred | RISK_CHANGE + STATE_CHANGE |
| execution_health_change | HEALTH_CHANGE |
| risk_level_change | RISK_CHANGE |
| intelligence_output | RECOMMENDATION_CHANGE |
| Other | NO_IMPACT |

## 6.4 Propagation

Observations propagate to:
- `execution_intelligence`: For re-evaluating risk/health on affected executions.
- `memory`: For recording significant events (exceptions).
- `planner`: For triggering re-planning (intelligence outputs).
- `awareness`: Always — for organizational awareness tracking.

## 6.5 Organizational Awareness

Per-tenant awareness is tracked via `OrganizationalAwarenessState`:

- `awareness_distribution`: Count of executions at each awareness level.
- `overall_awareness`: FULL if ≥50% executions at FULL, STALE if >50% stale, etc.
- `stale_execution_count`: Executions with no observations within `stale_threshold_hours` (default 72h).

Awareness levels: FULL (10+ observations), PARTIAL (5+), LIMITED (1+), BLIND (0).

## 6.6 Awareness Memory

Ring buffer of recent observations (default capacity: 1000). Supports:
- Filtering by tenant_id and priority.
- Reverse chronological order (newest first).
- Source-based lookup.
- FIFO eviction when capacity exceeded.

---

# Part VII — Organizational Intelligence

## 7.1 Organization Model

Organizations are modeled as hierarchical trees of `OrgUnit` entities:

```
Company (org_unit_type="company")
├── Division ("division")
│   ├── Department ("department")
│   │   ├── Team ("team")
│   │   └── Team ("team")
│   └── Department ("department")
└── Division ("division")
```

Each unit has a `parent_unit_id` for the hierarchy. The `OrgModelStore.get_unit_tree()` method builds the tree from the flat list.

## 7.2 Role Model

Roles (`OrgRole`) are the fundamental organizational atom. Everything attaches to roles, not persons:

- **Responsibilities** attach to roles.
- **Ownership** attaches to roles (or optionally persons).
- **Authority** attaches to roles.
- **Delegations** transfer authority between roles.
- **Collaborations** are recorded between roles.

Persons fulfill roles through `RoleAssignment` entities. A person can hold multiple roles. A role can be held by multiple persons.

## 7.3 Responsibility Graph

The `ResponsibilityGraph` tracks which roles are responsible for which entities:

```
Responsibility
├── role_id: str
├── entity_type: str (execution, obligation, commitment, resource)
├── entity_id: str
├── is_primary: bool
└── provenance: str
```

`resolve_owners()` resolves responsibilities to actual persons by looking up role assignments.

## 7.4 Ownership

Ownership is distinct from responsibility: **owner = accountable**, **responsible = assigned to do the work**. Ownership supports transfer:

1. `set_owner()` supersedes any previous ownership for the same entity.
2. `transfer()` creates a new ownership and marks the previous one as superseded.
3. `get_owner()` returns only the current (non-superseded) ownership.

## 7.5 Delegation

Delegation is temporary transfer of authority between roles:

- Auto-expires at `expires_at` if set.
- Capped at `delegation_max_duration_hours` (default 720h = 30 days).
- Can be explicitly revoked.
- `resolve_effective_authority()` considers active delegations when determining a role's authority.

## 7.6 Authority & Approvals

Authority grants are role-based: "Role X has authority to perform action Y on entity type Z".

Approval chains are multi-step workflows:
```
Chain: budget_approval for execution exec1
  Step 1: manager → approved
  Step 2: director → in_progress
  Status: in_progress
```

Each step specifies the role that must approve. The chain progresses sequentially.

## 7.7 Collaboration Intelligence

Collaborations are recorded between roles. The `CollaborationIntelligence` engine:

- Increments frequency on repeated collaborations between the same roles for the same entity.
- Computes `network_density` = `actual_edges / max_possible_edges` for a tenant.
- Provides `get_for_role()` to find all collaborations involving a role.

## 7.8 Institutional Memory

Versioned knowledge about the organization:

- `add()` creates a new entry. If an entry with the same topic exists, the old one is marked `superseded_by`.
- `get()` returns the latest (non-superseded) entry.
- `get_history()` returns all versions.
- Topics are free-form strings (e.g., "onboarding_process", "budget_policy", "decision_2026_q3").

## 7.9 Organizational Knowledge Graph

The `OrgKnowledgeGraph` connects all organizational entities:

- Built automatically from existing org data via `build_from_org_data()`.
- Supports BFS shortest-path queries via `find_path()`.
- Supports neighbor queries via `get_neighbors()`.
- Edges carry relationship types (contains, responsible_for, collaborates_with, etc.).

---

# Part VIII — Knowledge Architecture

## 8.1 Knowledge Representation

Knowledge in SHUNYA is stored as `KnowledgeObject` entities:

```
KnowledgeObject
├── object_id: str
├── key: str (unique within namespace)
├── namespace: str (isolation scope)
├── type: str (fact, config, policy, etc.)
├── payload: dict (the actual knowledge data)
├── version: int (monotonic)
├── is_active: bool
├── metadata: dict
├── created_at / updated_at: datetime
```

## 8.2 Evidence Relationships

Knowledge objects can reference evidence via:

- `EvidenceLink`: Connects a knowledge object to source evidence.
- `SourceReference`: References an external source (execution, observation, document).
- `AssertionRecord`: Records a knowledge assertion with confidence and provenance.

## 8.3 Reasoning Model

The `Reasoning Engine` (`app/shunya/reasoning/`) provides evidence-grounded reasoning:

- `evidence_graph.py`: Builds and queries evidence graphs.
- `confidence.py`: Computes confidence scores from evidence quality.
- `rules.py`: Deterministic rule application.
- `registry.py`: Reasoning pattern registry.

Reasoning is:
- **Evidence-grounded**: Every conclusion references supporting evidence objects.
- **Confidence-scored**: Outputs include confidence based on evidence quality.
- **Deterministic**: Same evidence + same rules → same conclusion.

## 8.4 Persistence

Knowledge is persisted in:
- `KnowledgeStore`: In-memory store with namespaces, versioning, search, and rollback.
- `ImmutableKnowledgeStore`: Versioned store that never mutates existing objects (append-only versions).

## 8.5 Retrieval

Retrieval is deterministic:
- `get_by_key(namespace, key)`: Exact lookup.
- `get(object_id, version=None)`: By ID, optionally at a specific version.
- `search(query)`: Namespace + type + filter-based search with pagination.

---

# Part IX — Memory Architecture

## 9.1 Working Memory

Working memory is the in-memory state of active engines:
- `ExecutionService._execs` — active executions.
- `AwarenessMemory._entries` — recent observations (ring buffer).
- `RiskMonitor._risk_cache` — cached risk levels.

Working memory is **ephemeral**. Loss on restart is acceptable.

## 9.2 Long-Term Memory

Long-term memory is the `MemoryRecord` entity:
- Active memory with effective date range.
- Linked to evidence via `MemoryProvenance`.
- Subject to `DisputeFlag` for contested memories.
- Governed by `MemoryEligibilityPolicy`.

## 9.3 Organizational Memory

Organizational memory is the `InstitutionalMemoryEntry`:
- Versioned (supersession model).
- Topic-based retrieval.
- Tenant-scoped.
- Source-traced (source_role_id, source_entity).

## 9.4 Evidence Memory

The evidence layer (`app/evidence/`) stores:
- `SourceReference`: External source metadata.
- `EvidenceLink`: Connection between knowledge and evidence.
- `AssertionRecord`: Recorded assertions with confidence.

## 9.5 Retention Philosophy

- **Working memory:** No explicit retention. Evicted by capacity (ring buffer).
- **Long-term memory:** Retention governed by `RetentionPolicy` in `app/privacy/`.
- **Organizational memory:** Never automatically deleted. Superseded entries remain for history.
- **Evidence:** Never deleted. Append-only.

---

# Part X — Governance

## 10.1 Policies

Governance policies are defined in `app/shunya/governance_engine/`:

- `Policy` entities with conditions and effects.
- `Constraint` entities for validation rules.
- Policies are resolved by `PolicyResolver` based on action type and context.

## 10.2 Constraints

Constraints are deterministic rules:
- Input validation (required fields, value ranges).
- State transition validation (ExecState.VALID_TRANSITIONS).
- Dependency validation (acyclic DAG enforcement).
- Authority validation (role-based access checks).

## 10.3 Deterministic Validation

The Governance Engine validates every plan against every applicable policy. Validation is:
- **Complete:** Every applicable policy is checked.
- **Deterministic:** Same plan + same policies → same validation result.
- **Auditable:** Every validation decision is logged with the policies that were checked.

## 10.4 Permissions

Permissions are role-based:
- `TeamMember.role` defines base permissions (ADMIN, MANAGER, AGENT).
- `Authority` grants define fine-grained action permissions.
- Authority checks via `AuthorityApprovalModel.check()` are deterministic.

## 10.5 Compliance

Compliance is enforced through:
- `PrivacyPolicy`: Data handling rules.
- `RetentionPolicy`: Data retention rules.
- `SensitivityPolicy`: Data classification rules.
- `ForgetRequest`: Right-to-be-forgotten compliance.

---

# Part XI — API Philosophy

## 11.1 Module Boundaries

SHUNYA modules follow these rules:

1. **No circular imports.** Dependencies flow from higher-level intelligence to lower-level state.
2. **Intelligence reads from state, never writes directly.** `ExecutionIntelligence` reads from `ExecutionService` but doesn't create/modify executions.
3. **Awareness reads from Intelligence and State.** `ContinuousRiskMonitor` calls `ExecutionIntelligence.assess_risk()`.
4. **Organizational Intelligence reads from State only.** It does not depend on Awareness or Execution Intelligence.

```
Execution State (app/execution)
    ↑ reads
Execution Intelligence (app/execution_intelligence)
    ↑ reads
Autonomous Awareness (app/awareness)
    ↑ independent
Organizational Intelligence (app/organizational)
```

## 11.2 Dependency Rules

1. State modules depend only on models and infrastructure.
2. Intelligence modules depend on state modules and their own models.
3. Service modules (privacy, memory, evidence) depend on state modules.
4. No module depends on a higher-level module.

## 11.3 Public Interfaces

Every module exposes:
- `__init__.py`: Public API — classes, functions, and `__all__`.
- `models.py`: Canonical data types (dataclasses, enums).
- `engine.py`: Implementation — computation, validation, coordination.

Public API is defined by `__all__`. Everything else is implementation-private.

## 11.4 Extension Mechanisms

1. **New intelligence dimensions** — Add a new engine to the appropriate module and hook into the `RuntimeService`.
2. **New observation categories** — Add to `ObservationCategory` enum and update `ObservationPipeline._compute_priority()` and `ChangeImpactAnalyzer.assess()`.
3. **New organizational entity types** — Add to `OrgEntityType` enum and update `OrgKnowledgeGraph.build_from_org_data()`.
4. **New governance policies** — Add to the Governance Engine's policy registry.

---

# Part XII — Data Ownership

## 12.1 Canonical Ownership

Every canonical entity belongs to exactly one module. The module that owns an entity is solely responsible for creating, updating, and deleting it.

| Entity | Owner Module |
|---|---|
| BusinessExecutionInstance | `app.execution` |
| ExecutionObligation | `app.execution` |
| CanonicalObservation | `app.awareness` |
| OrgUnit, OrgRole, RoleAssignment | `app.organizational` |
| Responsibility, Ownership, Delegation | `app.organizational` |
| HealthAssessment, RiskAssessment | `app.execution_intelligence` |
| KnowledgeObject | `app.shunya.knowledge_store` |
| MemoryRecord | `app.memory` |

## 12.2 Derived State

Derived state is computed on demand, never stored as canonical entities:
- `HealthAssessment`: Computed from execution state + obligations + exceptions.
- `RiskAssessment`: Computed from execution state + health.
- `NextAction`: Computed from execution state + health + risk + timeline.
- `AwarenessSnapshot`: Computed from observation history.
- `OrgHealth`: Computed from roles + assignments + delegations + collaborations.

The rule: **If you can recompute it, don't store it.**

## 12.3 Computed State

Computed state (cached for performance) is explicitly marked:
- `ContinuousRiskMonitor._risk_cache`: Risk levels cached for performance, invalidated by new observations.
- `OrgKnowledgeGraph._nodes / _edges`: Knowledge graph rebuilt on demand via `build_from_org_data()`.

Cached state is always recomputable from canonical sources.

## 12.4 Immutable History

The following are **append-only**:
- `BusinessExecutionInstance.history`: State transition log.
- `AwarenessMemory._entries`: Observation ring buffer.
- `InstitutionalMemory`: Superseded entries are preserved.
- `Ownership`: Superseded ownerships are preserved.

No entity is ever deleted from these append-only structures.

## 12.5 Versioning

Versioned entities:
- `KnowledgeObject`: Version increments on update. Previous versions preserved.
- `InstitutionalMemoryEntry`: Supersession model — new entry references old one.
- `Ownership`: Supersession model — new ownership marks old one as superseded.

---

# Part XIII — Architectural Decision Records

## ADR-001: Why BusinessExecutionInstance Exists

**Problem:** Early SHUNYA prototypes modeled executions as workflows (Executor Engine's `Workflow` entity). But workflows are execution *mechanisms*, not business commitments. A booking is not a workflow — it may involve multiple workflows over its lifetime. The system needed an entity that represents "this thing we committed to" rather than "this specific execution plan."

**Alternatives considered:**
1. Use the existing `Workflow` entity from the Executor Engine.
2. Use the Relationship Engine's `Commitment` entity.
3. Create a new `BusinessExecutionInstance` as a runtime-only abstraction.

**Decision:** Create `BusinessExecutionInstance`. It is:
- Computationally lightweight (in-memory only, no DB).
- Lifecycle-managed (state machine with validated transitions).
- Commitment-referencing (by type + ID, not by object).
- Workflow-agnostic (references workflow_refs but doesn't contain workflows).

**Consequences:**
- Positive: Clean separation between business commitment and execution mechanism.
- Positive: Enables portfolio-level intelligence across heterogeneous executions.
- Positive: Zero database overhead for the intelligence layer.
- Negative: Loss on restart (acceptable — all intelligence is recomputable).

**Trade-offs:** In-memory state means no persistence. This is intentional — the intelligence layer is designed to be recomputed from the knowledge store and observation history.

## ADR-002: Why Deterministic-First

**Problem:** Many intelligence systems rely on probabilistic methods (ML, Monte Carlo, randomized algorithms). These produce different outputs on different runs, making them untestable, un-auditable, and unpredictable.

**Alternatives considered:**
1. Pure probabilistic (ML-based risk assessment, fuzzy matching).
2. Hybrid (deterministic core + probabilistic extensions).
3. Pure deterministic (all computation, no randomness).

**Decision:** Pure deterministic. All engines are pure functions of their inputs. No randomness. No ML. No hidden state.

**Consequences:**
- Positive: Identical inputs → identical outputs. Testable, auditable, predictable.
- Positive: No "it works on my machine" problems.
- Positive: Easy to reason about causality.
- Negative: Some problems harder to solve without ML (anomaly detection, pattern recognition).
- Mitigated: Rule-based anomaly detection (Observer Engine) covers the most critical patterns.

**Trade-offs:** Some advanced use cases (predictive anomaly detection, adaptive learning) will require the Learning Intelligence extension point (see Part XV). The deterministic core ensures those extensions can be validated against a known baseline.

## ADR-003: Why Role-Centric Organizations

**Problem:** Organizational modeling typically centers on persons. But persons change roles, leave organizations, and hold multiple roles simultaneously. Person-centric modeling creates ownership churn and makes it difficult to reason about organizational structure independently of staffing.

**Alternatives considered:**
1. Person-centric: Responsibilities attach to persons directly.
2. Role-centric: Responsibilities attach to roles; persons fulfill roles.
3. Hybrid: Both persons and roles can hold responsibilities.

**Decision:** Pure role-centric. Every organizational entity (responsibility, ownership, authority, delegation, collaboration) attaches to a `OrgRole`. Persons are related to roles through `RoleAssignment`.

**Consequences:**
- Positive: Organizational structure is stable even as people change roles.
- Positive: Role-based authority is independent of who fills the role.
- Positive: Delegation is natural (role-to-role, not person-to-person).
- Positive: Institutional memory survives individual departures.
- Negative: Requires explicit role assignment.
- Mitigated: `RoleAssignment` is a thin entity — creating one is trivial.

**Trade-offs:** Requires a role assignment step when onboarding. This is a one-time cost that pays dividends in organizational stability.

## ADR-004: Why Evidence-Backed Computation

**Problem:** Intelligence outputs without traceable evidence are magic. They cannot be audited, explained, or challenged.

**Alternatives considered:**
1. No evidence tracking (outputs are opaque).
2. Evidence as optional metadata.
3. Evidence as mandatory part of every output.

**Decision:** Evidence is mandatory. Every intelligence output includes an `evidence: List[str]` or `traces: List[EvidenceTrace]` field. An output without evidence is invalid.

**Consequences:**
- Positive: Every conclusion can be traced to its source.
- Positive: Auditing is built-in, not bolted on.
- Positive: Debugging is straightforward — trace evidence back to root cause.
- Positive: Third parties can verify conclusions independently.
- Negative: Slightly more verbose output format.
- Mitigated: Evidence is a list of strings — low overhead.

**Trade-offs:** Slightly larger output payloads. Negligible compared to the value of traceability.

## ADR-005: Why Business-Agnostic Modeling

**Problem:** Building domain-specific engines (TravelEngine, HealthcareEngine) creates a combinatorial explosion of maintenance and prevents cross-domain intelligence.

**Alternatives considered:**
1. Domain-specific engines for each business vertical.
2. Generic engines with domain-specific configuration.
3. Fully generic engines with no domain awareness at all.

**Decision:** Fully generic engines. Domain concepts appear only as string labels on canonical entities (`commitment_type`, `obl_type`, `resource_type`). No engine contains domain-specific logic.

**Consequences:**
- Positive: One engine, any domain.
- Positive: Cross-domain intelligence (e.g., "how does our travel booking performance compare to our healthcare compliance?") is straightforward.
- Positive: New domains require zero core changes.
- Negative: Domain-specific validation must live in Governance policies.
- Mitigated: Governance policies are the right place for business rules.

**Trade-offs:** Governance becomes the domain-specific layer. This is correct — governance is supposed to encode business rules.

## ADR-006: Why No Duplicated State

**Problem:** When multiple modules store overlapping data, they inevitably diverge. The system becomes inconsistent and no single module is authoritative.

**Alternatives considered:**
1. Each module duplicates needed data (eventual consistency).
2. Each module references canonical sources by ID (strong consistency).
3. Centralized state store.

**Decision:** Each module references canonical sources by ID. No entity is duplicated. Derived state is computed, not stored.

**Consequences:**
- Positive: No divergent state.
- Positive: Always consistent.
- Positive: Clear ownership.
- Negative: Computation must be deterministic (can't recompute from divergent state).
- Mitigated: Computation is deterministic (see ADR-002).

## ADR-007: Why Explainability Is Mandatory

**Problem:** Without explainability, intelligence outputs are trust-but-verify at best, opaque at worst. Users cannot understand why a recommendation was made or a risk was flagged.

**Alternatives considered:**
1. No explainability (outputs are authoritative).
2. Explainability as an optional post-hoc analysis.
3. Explainability as a mandatory, integrated layer.

**Decision:** Explainability is mandatory and integrated. Every intelligence component includes an `ExplainabilityLayer` that produces structured explanations with evidence traces.

**Consequences:**
- Positive: Every output can be explained.
- Positive: Explanations are deterministic (same inputs → same explanation).
- Positive: Explanations can be generated independently of computation.
- Negative: Requires explainability logic for every engine.
- Mitigated: Explanations follow a consistent pattern (topic, conclusion, traces, confidence).

## ADR-008: Why Event-Driven Awareness

**Problem:** Polling-based awareness (checking every N seconds) is wasteful, laggy, and creates unnecessary load. It also misses transient states that occur between polls.

**Alternatives considered:**
1. Polling (periodic state checks).
2. Event-driven (state changes trigger observation).
3. Hybrid (polling + events).

**Decision:** Event-driven. Every meaningful system event creates a `CanonicalObservation` that flows through the pipeline. No polling.

**Consequences:**
- Positive: Immediate awareness.
- Positive: No wasted computation on unchanged state.
- Positive: Transient states are captured.
- Positive: Observation pipeline provides idempotency, so replay is safe.
- Negative: Requires event sources to generate observations.
- Mitigated: Facade methods (`observe_execution_state()`, `observe_exception()`, etc.) make event creation trivial.

## ADR-009: Why Organizational Intelligence Is Role-Centric

(Combined with ADR-003 above — role-centric organizations.)

---

# Part XIV — Engineering Constitution

## 14.1 The Rules

Every engineer and AI agent building on SHUNYA must follow these rules:

### Rule 1: Never create parallel sources of truth.

If a canonical entity already exists, reference it by ID rather than duplicating it. If you need data that doesn't exist, add it to the owning module — don't create a copy in your module.

### Rule 2: Never duplicate canonical entities.

Every canonical entity belongs to exactly one module. If you need to represent the same concept, extend the existing entity rather than creating a parallel one.

### Rule 3: Never bypass evidence.

Every intelligence output must carry evidence that traces back to observable state. Evidence-free outputs are not valid.

### Rule 4: Never introduce hidden business state.

Business-specific concepts (customer tiers, product catalogs, pricing rules) must not appear in core engine code. They belong in data (payload dictionaries, configuration) or in Governance policies.

### Rule 5: Never make AI the authoritative business state.

AI-generated outputs (from LLM calls or external AI services) must never be the single source of truth for business data. AI outputs are intelligence signals — they inform decisions but do not constitute state.

### Rule 6: Never hardcode industry-specific assumptions.

No core engine or model file may contain domain-specific strings (e.g., "travel", "healthcare", "booking") except as documentation examples in test files.

### Rule 7: Never compromise explainability for convenience.

An opaque solution is not a valid solution. Every computation must be traceable.

### Rule 8: Never mutate history.

State transitions, ownership changes, and knowledge updates are append-only. Supersede rather than overwrite. Archive rather than delete.

### Rule 9: Never depend on module internals.

Modules expose their public API through `__all__`. Accessing `module._private_attr` from another module is a violation of module boundaries.

### Rule 10: Never bypass Governance.

Every externally-visible action (sending a message, executing a workflow, modifying state) must pass through Governance.

## 14.2 Module Boundary Rules

1. Modules import from lower-level modules, never from higher-level modules.
2. The import order is: `app.execution` → `app.execution_intelligence` → `app.awareness` → `app.organizational`.
3. No circular imports. If a dependency would create a cycle, extract the common type into a lower-level module.

## 14.3 Test Rules

1. Every engine must have deterministic tests that verify identical inputs → identical outputs.
2. Every edge case must be tested (empty state, unknown entity, terminal state).
3. Concurrency tests are required for singleton-managed engines.
4. Full regression must pass before any commit.

---

# Part XV — Extension Points

The following capabilities are recognized as future work. Their attachment points are documented here so that the current architecture does not constrain them.

## 15.1 Learning Intelligence

**Attachment point:** `app/learning/` (exists as stub) → connect to `AwarenessEngine` observations + `ExecutionIntelligence` assessments.

**Design intent:** A Learning Engine that processes sequences of observations to identify patterns, improve risk detection thresholds, and optimize next-action recommendations. Does not replace the deterministic engines — it tunes their parameters.

## 15.2 Prediction

**Attachment point:** Extend `TimelineIntelligenceEngine.predict_completion()` with historical data from `InstitutionalMemory` and `KnowledgeStore`.

**Design intent:** Predict future execution outcomes based on patterns learned from past executions. The current prediction is simple (linear extrapolation). Future versions should incorporate distributional data.

## 15.3 Simulation

**Attachment point:** Before `Governance` in the pipeline — simulate plan outcomes before execution.

**Design intent:** "What if" analysis. Given a proposed plan, simulate its likely outcomes using execution intelligence and historical data. No state mutation — simulation is read-only.

## 15.4 Executive Intelligence

**Attachment point:** Cross-cutting across `PortfolioIntelligence`, `OrgHealthEngine`, `OrganizationalAwarenessState`.

**Design intent:** Dashboard-level intelligence for organization leaders. Aggregate all intelligence outputs into strategic recommendations. "What should the organization do next?"

## 15.5 Human Operating System

**Attachment point:** `app/human_context/` + `app/organizational/` + `app/relationship/`.

**Design intent:** A complete model of human actors in the system — their skills, availability, workload, performance, and growth trajectories. Integrates with organizational roles and execution responsibilities.

## 15.6 External Integrations

**Attachment point:** `app/adapters/` (currently has WhatsApp, Gmail).

**Design intent:** Standard adapter interface for external systems (CRMs, ERPs, payment gateways, messaging platforms). Each adapter implements send/receive/parse lifecycle.

## 15.7 Partner Ecosystem

**Attachment point:** New module `app/ecosystem/` or extend `app/organizational/` with tenant-to-tenant relationships.

**Design intent:** Enable multi-tenant collaboration — partner organizations with shared obligations, cross-tenant delegations, and federated awareness.

---

## Document Metadata

- **Title:** SHUNYA Architecture Specification v1.0
- **Status:** Authoritative
- **Last updated:** 2026-07-21
- **Canonical modules referenced:** 43
- **ADRs documented:** 9
- **Engineering rules:** 10
- **Extension points identified:** 7

---

*This document defines what SHUNYA IS. Every module, every entity, every decision recorded here is the constitutional reference for all future development. No change to this document's architecture may be made without updating the corresponding ADR.*
