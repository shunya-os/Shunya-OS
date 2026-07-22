# SHUNYA Implementation Program

**Authority:** Architecture Baseline 1.0 (Frozen)
**Date:** 2026-07-18
**Status:** Program Definition
**Next:** First Engineering Sprint

---

## 1. Executive Summary

### Implementation Philosophy

The SHUNYA implementation program transforms a frozen, constitutionally-grounded architecture into executable engineering work. The architecture is complete — 10 engine specifications, 3 architecture standards, 3 infrastructure ADRs, 14 + 12 frozen invariants. Implementation does not discover architecture; it realizes it.

The program follows five principles:

1. **Architecture before code** — Every implementation decision must be traceable to the architecture. If the architecture does not specify it, it is not implemented.
2. **Interface before implementation** — Every engine's API contract is implemented and verified before its internal logic.
3. **Tests before merge** — No code enters the main branch without passing its verification gate.
4. **Verification before completion** — No phase is complete until its verification checklist is satisfied.
5. **Small incremental commits** — Every commit represents a single, verifiable step. No bulk merges.

### Relationship to the Frozen Architecture

The architecture is the input, not the output. All architecture documents are frozen:

| Document Set | Count | Status |
|---|---|---|
| Constitutional documents | 3 | Locked (SHUNYA_ARCHITECTURE.md v2.0) |
| Architecture Standards | 2 | Draft — frozen for implementation |
| Engine Specifications (ES-001–ES-010) | 10 | Draft — frozen for implementation |
| Infrastructure ADRs (ADR-001–ADR-003) | 3 | Proposed — frozen for implementation |
| Analysis documents | 4 | Informative reference |
| Governance documents | 5 | Active |

No implementation may deviate from these documents. Divergence must be escalated per the Engineering Constitution Article 8.

### Engineering Principles

1. **Single Responsibility** — No module may have two responsibilities. Each engine owns exactly what its specification defines and nothing else.
2. **Layered Validation** — No request reaches execution without passing through Governance. No engine bypasses another engine's authority.
3. **Immutability** — Knowledge is never overwritten. Evidence is never modified. Audit trails are append-only.
4. **Least Authority** — Every engine has the minimum permissions required for its function. No engine accesses credentials except Executor (at runtime).
5. **Degradation is explicit** — When a dependency is unavailable, the engine degrades gracefully and documents the degradation.
6. **Constitutional compliance** — Every engine's SHALL NEVER list is enforced at the architectural boundary, not just in documentation.

### Implementation Authority

| Role | Authority | Scope |
|---|---|---|
| Engineering Team | Implementation within specified boundaries | Per-engine implementation |
| Chief Software Architect | Engineering decisions, spec interpretation, ADR amendments | Cross-engine integration |
| Chief Constitutional Architect | Constitutional decisions, architecture amendments (require ADR) | Architecture changes |

No engineering team may modify an engine specification without an ADR. No team may introduce a new architectural concept without constitutional review.

### Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| All 10 engines implemented | Complete | Each engine passes its verification gate |
| Dependency graph respected | Acyclic | Integration tests verify each engine communicates only through specified contracts |
| Constitutional invariants enforced | Zero violations | Automated invariant checks in CI |
| Shared infrastructure operational | Event Bus, Credential Store, IKS operational | Infrastructure integration tests pass |
| Existing codebase migrated | KnowledgeLayer → IKS complete | KnowledgeEngine facade is the only knowledge access path |
| All verification checklists satisfied | 100% | Per-engine checklist sign-off |

---

## 2. Repository Strategy

### Repository Layout

```
shunya_os/
├── app/
│   ├── __init__.py
│   ├── routes.py                    — API routes (existing, to be refactored)
│   ├── client_portal.py             — Client portal (existing, to be refactored)
│   ├── templates/                   — HTML templates (existing, to be refactored)
│   ├── static/                      — Static assets (existing, to be refactored)
│   │
│   ├── shunya/                      — SHUNYA platform root
│   │   ├── __init__.py              — Package exports
│   │   ├── config.py                — Centralized configuration
│   │   ├── di.py                    — Dependency injection container
│   │   │
│   │   ├── infrastructure/          — Shared infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── event_bus.py         — EventBus (ADR-001)
│   │   │   ├── credential_store.py  — CredentialStore (ADR-003)
│   │   │   ├── logging.py           — Centralized logging
│   │   │   ├── metrics.py           — Metrics collection
│   │   │   ├── health.py            — Health endpoint
│   │   │   └── persistence.py       — Database session management
│   │   │
│   │   ├── knowledge/               — Knowledge Engine (ES-002)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            — KnowledgeEngine facade
│   │   │   ├── immutable_store.py   — ImmutableKnowledgeStore
│   │   │   ├── models.py            — KnowledgeFact model
│   │   │   └── migration.py         — KnowledgeLayer → IKS migration (ADR-002)
│   │   │
│   │   ├── identity/                — Identity Engine (ES-010)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            — IdentityEngine
│   │   │   ├── models.py            — IdentityRecord model
│   │   │   └── normalizer.py        — Identity value normalization
│   │   │
│   │   ├── context/                 — Context Fusion Engine (ES-009)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            — ContextFusionEngine
│   │   │   ├── providers.py         — Source provider integrations
│   │   │   └── eligibility.py       — Phase 4 eligibility gate
│   │   │
│   │   ├── reasoning/               — Reasoning Engine (ES-003)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            — ReasoningEngine
│   │   │   └── strategies.py        — Reasoning strategies
│   │   │
│   │   ├── planner/                 — Planner Engine (ES-004)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            — PlannerEngine
│   │   │   └── templates.py         — Plan templates
│   │   │
│   │   ├── governance/              — Governance Engine (ES-001)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            — GovernanceEngine
│   │   │   ├── policies.py          — Policy registry and evaluation
│   │   │   └── audit.py             — Audit trail
│   │   │
│   │   ├── executor/                — Executor Engine (ES-005)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            — ExecutorEngine
│   │   │   └── adapters/            — Channel adapters
│   │   │       ├── whatsapp.py
│   │   │       ├── telegram.py
│   │   │       ├── email.py
│   │   │       └── api.py
│   │   │
│   │   ├── observer/                — Observer Engine (ES-006)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            — ObserverEngine
│   │   │   └── models.py            — Observation model
│   │   │
│   │   ├── learning/                — Learning Engine (ES-007)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            — LearningEngine
│   │   │   └── patterns.py          — Pattern detection
│   │   │
│   │   ├── doctor/                  — Doctor Engine (ES-008)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            — DoctorEngine
│   │   │   └── checks.py            — Integrity check definitions
│   │   │
│   │   └── legacy/                  — Legacy code wrappers (during migration)
│   │       ├── __init__.py
│   │       ├── knowledge_layer.py   — KnowledgeLayer wrapper (ADR-002 Phase 1-3)
│   │       └── workflow.py          — Existing workflow adapter
│   │
│   ├── data/                        — Data files
│   │   ├── knowledge-base.md        — Legacy KB (to be migrated per ADR-002)
│   │   └── migrations/              — Database migrations
│   │
│   └── routes.py                    — API routes (kept during migration)
│
├── tests/
│   ├── conftest.py                  — Shared fixtures
│   ├── infrastructure/              — Infrastructure tests
│   │   ├── test_event_bus.py
│   │   ├── test_credential_store.py
│   │   └── test_di.py
│   ├── engines/                     — Per-engine tests
│   │   ├── test_governance.py
│   │   ├── test_knowledge.py
│   │   ├── test_identity.py
│   │   ├── test_context_fusion.py
│   │   ├── test_reasoning.py
│   │   ├── test_planner.py
│   │   ├── test_executor.py
│   │   ├── test_observer.py
│   │   ├── test_learning.py
│   │   └── test_doctor.py
│   ├── integration/                 — Cross-engine integration tests
│   │   ├── test_context_to_reasoning.py
│   │   ├── test_reasoning_to_governance.py
│   │   └── test_full_pipeline.py
│   ├── migration/                   — Migration tests
│   │   ├── test_knowledge_layer_migration.py
│   │   └── test_iks_seed.py
│   ├── constitutional/              — Constitutional invariant tests
│   │   ├── test_invariants.py
│   │   └── test_shall_never.py
│   ├── performance/                 — Performance benchmarks
│   │   ├── benchmarks.py
│   │   └── latency_tests.py
│   └── data/                        — Test data
│       ├── golden_dataset.json
│       └── fixtures/
│
├── docs/
│   ├── architecture/                — Architecture documents (frozen reference)
│   ├── governance/                  — Governance documents
│   └── implementation/              — Implementation documentation
│
├── scripts/
│   ├── migrate_knowledge_layer.py   — ADR-002 Phase 2 migration script
│   ├── seed_iks.py                  — IKS seeding
│   └── verify_architecture.py       — Architecture invariant checker
│
├── pyproject.toml                   — Project configuration
├── config.yaml                      — Application configuration
└── Dockerfile                       — Deployment container
```

### Module Ownership

| Module | Owner | Engine Spec |
|--------|-------|-------------|
| `app/shunya/infrastructure/` | Infrastructure team | ADR-001, ADR-003 |
| `app/shunya/knowledge/` | Knowledge team | ES-002 |
| `app/shunya/identity/` | Identity team | ES-010 |
| `app/shunya/context/` | Context team | ES-009 |
| `app/shunya/reasoning/` | Reasoning team | ES-003 |
| `app/shunya/planner/` | Planner team | ES-004 |
| `app/shunya/governance/` | Governance team | ES-001 |
| `app/shunya/executor/` | Executor team | ES-005 |
| `app/shunya/observer/` | Observer team | ES-006 |
| `app/shunya/learning/` | Learning team | ES-007 |
| `app/shunya/doctor/` | Doctor team | ES-008 |
| `app/shunya/legacy/` | Infrastructure team | ADR-002 |

### Shared Packages

| Package | Purpose | Consumers |
|---------|---------|-----------|
| `app.shunya.infrastructure.event_bus` | EventBus singleton | All engines |
| `app.shunya.infrastructure.credential_store` | CredentialStore | Executor only |
| `app.shunya.infrastructure.logging` | Centralized logging | All modules |
| `app.shunya.infrastructure.metrics` | Prometheus metrics | All modules |
| `app.shunya.infrastructure.health` | Health endpoint | Operator dashboard |
| `app.shunya.infrastructure.persistence` | DB session, migrations | All engines |
| `app.shunya.infrastructure.di` | Dependency injection container | Application bootstrap |

### Engine Packages

Each engine package (`app.shunya/{engine}/`) owns:
- `engine.py` — Primary engine class implementing the specification
- `models.py` — Data models (if any)
- Internal sub-modules as needed

An engine package may import from:
- `app.shunya.infrastructure.*` — Shared infrastructure
- `app.shunya.{dependency_engine}.*` — Direct dependencies only (per dependency matrix)
- Canonical model types from `app.shunya.__init__`

An engine package must never import from:
- Another engine's private modules (only the public `engine.py` interface)
- Another engine's data store directly

### API Boundaries

| Interface | Provider | Consumer | Mechanism |
|-----------|----------|----------|-----------|
| EventBus.publish() | Event Bus | All engines | In-process API call |
| EventBus.subscribe() | Event Bus | All engines | In-process API call |
| CredentialStore.resolve() | Credential Store | Executor only | In-process API call |
| KnowledgeEngine.get_fact() | Knowledge Engine | Reasoning, Planner, Governance, Context Fusion, Doctor | In-process API call |
| IdentityEngine.resolve() | Identity Engine | Context Fusion | In-process API call |
| ContextFusionEngine.assemble() | Context Fusion | Reasoning, Planner, Governance, Executor, Observer, Learning | In-process API call |
| ReasoningEngine.reason() | Reasoning | Planner | In-process API call |
| PlannerEngine.plan() | Planner | Governance | In-process API call |
| GovernanceEngine.validate() | Governance | Executor | In-process API call |
| ExecutorEngine.execute() | Executor | Observer (via Event Bus) | Event |
| ObserverEngine.observe() | Observer | Knowledge, Learning | Event |
| LearningEngine.learn() | Learning | Knowledge | Event |
| DoctorEngine.check() | Doctor | All engines (via Event Bus) | Event |

### Test Structure

| Test Directory | Purpose | Runs On |
|----------------|---------|---------|
| `tests/engines/test_{engine}.py` | Unit tests per engine | Every commit |
| `tests/infrastructure/test_{component}.py` | Infrastructure unit tests | Every commit |
| `tests/integration/` | Cross-engine workflows | CI (per PR) |
| `tests/constitutional/` | Invariant enforcement | CI (per PR) |
| `tests/migration/` | Migration correctness | Pre-deployment |
| `tests/performance/` | Latency/throughput benchmarks | Weekly or per release |

### Migration Strategy (Repository)

The existing codebase (`app/shunya/knowledge.py`, `app/shunya/workflow.py`, `app/routes.py`, etc.) is not deleted during migration. Legacy modules are moved to `app/shunya/legacy/` with wrappers that conform to the new engine interfaces. The migration proceeds per ADR-002 phases:

- **Phase 1 (Coexistence):** New engine modules exist alongside legacy. Legacy call sites continue to function.
- **Phase 2 (Seed):** Data migrated from legacy to new stores.
- **Phase 3 (Cutover):** New engines become primary. Legacy become fallback.
- **Phase 4 (Retirement):** Legacy modules removed.

### Configuration Management

Configuration is centralized in `config.yaml` and loaded at application startup via `app/shunya/config.py`. Per-engine configuration is namespaced:

```yaml
event_bus:
  max_queue_size: 10000
  consumer_timeout_ms: 5000
  idempotency_cache_ttl_hours: 24

credential_store:
  encryption_key_id: "key-1"
  audit_log_enabled: true

knowledge:
  iks_enabled: true
  knowledge_layer_fallback: true  # Phase 1-3 only

governance:
  policy_registry_path: "policies/"
  audit_log_enabled: true
```

### Dependency Management

| Tool | Purpose | Configuration |
|------|---------|---------------|
| `uv` | Python package management | `pyproject.toml` |
| `pytest` | Test runner | `pyproject.toml` [tool.pytest.ini_options] |
| `ruff` | Linting and formatting | `pyproject.toml` [tool.ruff] |
| `mypy` | Type checking | `pyproject.toml` [tool.mypy] |
| `alembic` | Database migrations | `app/data/migrations/` |

---

## 3. Implementation Principles

The following principles are mandatory for all engineering work. Violations are divergence per Engineering Constitution Article 8.

### P1. Architecture Before Code

No implementation may proceed without traceability to a specific section of a frozen architecture document. Every function, class, and module header must cite its architectural authority.

### P2. Interface Before Implementation

Every engine's public API contract (inputs, outputs, events) must be implemented and tested before its internal logic. Integration tests are written against the interface contract before the implementation exists.

### P3. Tests Before Merge

No code enters the `main` branch without passing:
- Unit tests for the changed module
- Integration tests for the affected interface
- Constitutional invariant tests
- Linting and type checking

### P4. Verification Before Completion

No phase is complete until its verification checklist (Section 8) is 100% satisfied. An incomplete checklist is an incomplete phase.

### P5. Small Incremental Commits

Every commit must be:
- **Atomic** — one logical change
- **Verifiable** — includes tests that pass
- **Reversible** — can be rolled back without cascading effects
- **Documented** — commit message references the architectural authority

### P6. Backward Compatibility During Migration

During ADR-002 migration phases, all existing code paths must continue to function. Legacy call sites are wrapped, never broken.

### P7. No Engine May Violate Another Engine's Responsibility

Each engine's SHALL NEVER list (ES-001 through ES-010, Section 16) is enforceable at the architectural boundary. An engine may not call another engine's internal functions, access its data store, or perform its prohibited actions.

### P8. No Engine May Bypass Governance

No action reaches the Executor without passing through the Governance Engine. This is enforced at the architectural level — the Governance Engine is the only entry point to the Executor (ES-001, ES-005).

### P9. No Engine May Access Another Engine's Storage Directly

All cross-engine data access goes through the owning engine's public API or through the Event Bus. Direct database access to another engine's tables is a constitutional violation.

### P10. Credential Isolation

Only the Executor Engine may call `CredentialStore.resolve()`. No other engine may access credential values. Credential values must never appear in:
- Event payloads
- Plan documents
- Log outputs
- Audit trails
- Error messages

### P11. Tenant Isolation Enforcement

Every engine operation is scoped by `tenant_id`. No engine may access data from another tenant. Cross-tenant operations require explicit authorization.

### P12. Immutable Knowledge

All knowledge mutations must use the supersession pattern (ADR-002). No in-place updates. No deletions. Complete version history must be preserved.

### P13. Degradation Is Explicit

When a dependency is unavailable, the engine must:
1. Return a degraded result (not fail silently)
2. Document which sections are degraded and why
3. Continue to operate with available data

### P14. Event-Driven Communication

Engines communicate asynchronously through the Event Bus wherever possible. Synchronous API calls are used only when the caller needs a result before proceeding (Core Models §10 — Synchronization).

---

## 4. Engine Implementation Order

### Canonical Order

```
Phase 1 ─── Shared Infrastructure ─── Event Bus, Credential Store, IKS, DI
                │
                ▼
Phase 2 ─── Foundation Engines ────── Identity (ES-010), Knowledge (ES-002)
                │
                ▼
Phase 3 ─── Context Engine ────────── Context Fusion (ES-009)
                │
                ▼
Phase 4 ─── Analysis Engine ───────── Reasoning (ES-003)
                │
                ▼
Phase 5 ─── Planning Engine ───────── Planner (ES-004)
                │
                ▼
Phase 6 ─── Validation Engine ─────── Governance (ES-001)
                │
                ▼
Phase 7 ─── Execution Engine ──────── Executor (ES-005)
                │
                ▼
Phase 8 ─── Observation Engines ───── Observer (ES-006), Doctor (ES-008)
                │
                ▼
Phase 9 ─── Learning Engine ───────── Learning (ES-007)
```

### Engine 1: Identity Engine (ES-010)

| Property | Value |
|----------|-------|
| **Purpose** | Resolve persons to canonical identities. Foundation for all context-aware operations. |
| **Dependencies** | Knowledge Engine (stores identity records), Channel adapters (identity extraction) |
| **Inputs** | Identity claims (email, phone, channel, document, external, alias) |
| **Outputs** | ResolutionResult (MATCHED/NO_MATCH/AMBIGUOUS), IdentityRecord |
| **Completion criteria** | All identity types supported (8 types). Resolution deterministic. AMBIGUOUS correctly returned. Tenant isolation enforced. |
| **Verification gate** | 7 unit tests (state transitions), 7 error handling tests, 12 edge case tests. Integration with Knowledge Engine verified. |
| **Why first** | Identity is a prerequisite for Context Fusion. Without identity resolution, context assembly cannot begin. No downstream engine requires identity data directly — all identity flows through Context Fusion. |

### Engine 2: Knowledge Engine (ES-002)

| Property | Value |
|----------|-------|
| **Purpose** | Immutable, versioned fact store. Single source of truth for all knowledge. |
| **Dependencies** | Observer (observations), Learning (learned facts), IKS implementation |
| **Inputs** | Observations, documents, learning signals, human corrections |
| **Outputs** | KnowledgeFacts with version history, evidence chains, confidence scores |
| **Completion criteria** | IKS operational. ADR-002 Phase 1-2 complete. KnowledgeEngine facade wraps both IKS and KnowledgeLayer. All 5 existing call sites function through facade. |
| **Verification gate** | Unit tests for all fact operations (set, get, history, search, supersede). Integration tests with Observer, Learning. Constitutional invariant tests (no in-place updates, versioning preserved). |
| **Why second** | Knowledge Engine stores identity records (Identity Engine dependency). It is the foundation engine — no other engine can function without facts, policies, or identity records. |

### Engine 3: Context Fusion Engine (ES-009)

| Property | Value |
|----------|-------|
| **Purpose** | Assemble bounded workspace context from identity, relationships, conversations, memory, evidence, documents. Apply eligibility gates. Enforce budgets. |
| **Dependencies** | Identity Engine (identity resolution), Knowledge Engine (memory, evidence, documents), Phase 4 (Privacy — eligibility gates) |
| **Inputs** | ContextRequest (tenant_id, actor_id, purpose_code, subject_id), source provider data |
| **Outputs** | WorkspaceContext — bounded, fingerprinted, degrated sections documented |
| **Completion criteria** | Context assembly from all source providers. Phase 4 eligibility gates integrated. Budget enforcement active. Fingerprints computed. Degraded mode returns documented exclusions. |
| **Verification gate** | 9 state transition tests, 6 error handling tests. Integration with Identity Engine, Knowledge Engine, Phase 4. |
| **Why third** | Context Fusion is the most-depended-upon engine (6 of 7 pipeline engines). It must exist before Reasoning, Planner, Governance, Executor, Observer, or Learning can receive workspace context. |

### Engine 4: Reasoning Engine (ES-003)

| Property | Value |
|----------|-------|
| **Purpose** | Analyze stimuli against workspace context. Infer intent, assess risks, build evidence chains, produce recommendations with confidence scores. |
| **Dependencies** | Knowledge Engine (facts), Context Fusion (workspace context) |
| **Inputs** | WorkspaceContext, knowledge facts, observation |
| **Outputs** | ReasoningResult — decision, confidence, evidence chain, explanation, alternatives, risk flags |
| **Completion criteria** | All reasoning types supported. Evidence chains produced for every decision. Confidence scores canonical (0.0–1.0). Insufficient context handled (low-confidence result returned). |
| **Verification gate** | Unit tests for reasoning strategies. Integration with Context Fusion (context delivered, degraded, error). Constitutional: evidence chains produced, confidence explicit. |
| **Why fourth** | Reasoning produces the analysis that Planning and Governance need. It consumes Context Fusion output — must be implemented after Context Fusion. |

### Engine 5: Planner Engine (ES-004)

| Property | Value |
|----------|-------|
| **Purpose** | Create executable plans from reasoning results. Sequence steps with dependencies, timelines, resource estimates. |
| **Dependencies** | Reasoning Engine (reasoning results), Knowledge Engine (domain data), Context Fusion (workspace context) |
| **Inputs** | ReasoningResult, WorkspaceContext |
| **Outputs** | Plan — structured action sequence with dependencies, cost estimates, alternatives |
| **Completion criteria** | Plans produced from reasoning results. Cost and timeline estimates accurate. Degraded planning works with incomplete context. Failure modes handled (ambiguous reasoning, missing knowledge). |
| **Verification gate** | Unit tests for plan generation, cost estimation, timeline computation. Integration with Reasoning. Plans conform to Governance input contract. |
| **Why fifth** | Planning produces the artifact that Governance validates. It must come after Reasoning (consumes reasoning results) and before Governance (produces Governance input). |

### Engine 6: Governance Engine (ES-001)

| Property | Value |
|----------|-------|
| **Purpose** | Validate plans against constitutional principles and business policies. Return APPROVE, REVIEW, or REJECT. Maintain immutable audit trail. |
| **Dependencies** | Planner (plans), Knowledge Engine (policy definitions), Context Fusion (workspace context) |
| **Inputs** | Plan, evidence chain, WorkspaceContext, domain, action type |
| **Outputs** | GovernanceVerdict — approved boolean, decision, blocking policies, warnings, reviews required, evidence checked |
| **Completion criteria** | Policy registry operational. All 10 constitutional principles mapped to evaluable policies. APPROVE/REVIEW/REJECT returned correctly. Audit trail immutable. Tenant isolation enforced. |
| **Verification gate** | 14 state transition tests, 8 error handling tests. Constitutional: Invariant 3 (Governance precedes execution) verified. Integration with Planner, Executor. |
| **Why sixth** | Governance validates plans before execution. It must come after Planning (receives plans) and before Execution (sends approved plans). It also needs Context Fusion for context enrichment and Knowledge Engine for policy definitions. |

### Engine 7: Executor Engine (ES-005)

| Property | Value |
|----------|-------|
| **Purpose** | Perform approved actions through channel adapters. Deliver messages, create records, call external APIs. |
| **Dependencies** | Governance Engine (approved plans), Credential Store (credentials at runtime), Context Fusion (workspace context) |
| **Inputs** | Approved plan, GovernanceVerdict, channel routing information |
| **Outputs** | DeliveryResult — success, message_id, channel, error |
| **Completion criteria** | All channel adapters implemented (WhatsApp, Telegram, email, API). Credential resolution at execution time working. Credentials discarded after task completion. Failure handling per spec (retry, fallback, partial delivery). |
| **Verification gate** | Unit tests for each channel adapter. Integration with Governance (approved plan received), Credential Store (credential resolved and discarded). Constitutional: Invariant 5 (Executor never reasons) verified. |
| **Why seventh** | Execution is the output of the pipeline. It depends on Governance (approved plans), Credential Store (credentials), and Context Fusion (context). It must come after all three. |

### Engine 8: Observer Engine (ES-006)

| Property | Value |
|----------|-------|
| **Purpose** | Record raw observations. Compare actual vs expected outcomes. Detect discrepancies. |
| **Dependencies** | Executor (execution outcomes), Knowledge Engine (observation storage), Context Fusion (workspace context) |
| **Inputs** | DeliveryResult, expected outcome from plan |
| **Outputs** | OutcomeObservation — success, discrepancy, actual outcome, confidence |
| **Completion criteria** | Observations recorded for every execution. Discrepancy detection operational. Basic observation (100%) distinguished from detailed validation (10% sampling). Anomaly detection flags discrepancies. |
| **Verification gate** | Unit tests for observation recording, discrepancy computation. Integration with Executor (outcome received), Knowledge Engine (observation stored). Constitutional: Invariant 5 (Observation is continuous) verified. |
| **Why eighth** | Observation closes the compounding loop. It consumes Executor output — must come after Execution. It feeds Knowledge (observations become facts) and Learning (outcomes enable learning). |

### Engine 9: Doctor Engine (ES-008)

| Property | Value |
|----------|-------|
| **Purpose** | Verify system integrity, check architecture drift, validate package health, confirm governance compliance. |
| **Dependencies** | All engines (health data), Knowledge Engine (integrity data), Governance Engine (audit log) |
| **Inputs** | Health data from all engines, architecture snapshots, governance audit log, package manifests |
| **Outputs** | DoctorReport — structured check results, Violation events |
| **Completion criteria** | All check types implemented (integrity, drift, package health, compliance). Health aggregation from all engines. Violation events published correctly. Check schedule configurable. |
| **Verification gate** | 5 state transition tests, 5 error handling tests. Integration tests with Knowledge Engine, Governance Engine, Event Bus. |
| **Why ninth** | Doctor checks all engines. It must be implemented after at least the core engines (Knowledge, Governance, Observability) so it has something to check. It is not in the pipeline — it runs independently and does not block pipeline operation. |

### Engine 10: Learning Engine (ES-007)

| Property | Value |
|----------|-------|
| **Purpose** | Analyze outcomes against expectations. Generate learning signals. Apply improvements to knowledge, reasoning, and policies. |
| **Dependencies** | Observer (outcome observations), Knowledge Engine (facts), Governance Engine (decisions), Context Fusion (workspace context) |
| **Inputs** | OutcomeObservation, historical outcomes, learning context |
| **Outputs** | LearningSignal — insight, recommendation, knowledge_fact_key, confidence |
| **Completion criteria** | Learning signals generated from outcome analysis. Cold start mode implemented (collect without recommending). Confidence calibration with damping factor. Signals pass through Governance before application. |
| **Verification gate** | Unit tests for pattern detection, signal generation, confidence calibration. Integration with Observer (outcomes received), Knowledge (facts written), Governance (signals validated). Constitutional: Invariant 3 (Evidence precedes learning), Invariant 4 (Learning never bypasses governance) verified. |
| **Why tenth** | Learning is the last stage in the compounding loop. It depends on all pipeline engines having produced outcomes. It must come after Observation (consumes outcomes), Knowledge (writes learned facts), Governance (validates learning signals). |

---

## 5. Shared Infrastructure Order

Shared infrastructure must be implemented before any dependent engine. The order is:

### Order 1: Dependency Injection Container

| Property | Value |
|----------|-------|
| **Purpose** | Centralized wiring of all engines and infrastructure. Each engine receives its dependencies through the container (constructor injection). |
| **Dependencies** | None (foundation infrastructure) |
| **Why first** | Every engine and infrastructure component depends on DI for wiring. Without DI, engines cannot be instantiated with their dependencies. |
| **Implementation** | Lightweight container (`app/shunya/di.py`). Supports singleton and factory registrations. Auto-wiring by type hint. |

### Order 2: Configuration

| Property | Value |
|----------|-------|
| **Purpose** | Load and validate application configuration from `config.yaml`. Provide typed config objects to all components. |
| **Dependencies** | None (foundation infrastructure) |
| **Why second** | Every infrastructure component needs configuration (queue sizes, timeouts, encryption keys). Configuration must be loaded before any component that reads it. |
| **Implementation** | YAML loader with schema validation. Per-environment config files (config.yaml, config.production.yaml). Environment variable override support. |

### Order 3: Persistence

| Property | Value |
|----------|-------|
| **Purpose** | Database session management, connection pooling, migration runner. |
| **Dependencies** | Configuration (DB URL, pool size) |
| **Why third** | Knowledge Engine, Identity Engine, Governance Engine all need database access. Persistence layer must exist before any engine that stores data. |
| **Implementation** | SQLAlchemy session factory. Alembic migration runner. Connection pooling with health checks. |

### Order 4: Logging

| Property | Value |
|----------|-------|
| **Purpose** | Centralized structured logging with configurable levels, output targets, and privacy constraints. |
| **Dependencies** | Configuration (log level, output file) |
| **Why fourth** | Every component must log. Logging must be operational before any component that produces logs. |
| **Implementation** | Structured JSON logging. Configurable levels per module. Privacy filters (PII stripping). Correlation_id propagation. |

### Order 5: Event Bus (ADR-001)

| Property | Value |
|----------|-------|
| **Purpose** | In-process publish/subscribe for inter-engine communication. At-least-once delivery, idempotency, dead-letter queue. |
| **Dependencies** | DI, Configuration, Logging |
| **Why fifth** | The Event Bus is the primary communication mechanism for all 10 engines. It must be operational before any engine that publishes or consumes events. |
| **Implementation** | Singleton EventBus per ADR-001 contract. In-process queue-based delivery. Idempotency cache (24h TTL). Dead-letter queue. Health endpoint. |

### Order 6: Metrics

| Property | Value |
|----------|-------|
| **Purpose** | Prometheus-compatible metrics collection. Counters, histograms, gauges per engine. |
| **Dependencies** | Configuration (metrics port, enabled flag) |
| **Why sixth** | Metrics are consumed by the Doctor Engine and operator dashboards. They must exist before engines produce metrics. |
| **Implementation** | Prometheus client library. Per-engine metric namespaces. Configurable scrape endpoint. |

### Order 7: Health

| Property | Value |
|----------|-------|
| **Purpose** | Centralized health endpoint aggregating health status from all engines and infrastructure. |
| **Dependencies** | Event Bus (to receive health events), Logging, Metrics |
| **Why seventh** | Health endpoint is consumed by the Doctor Engine (for aggregation) and operators (for monitoring). Must exist before Doctor Engine checks run. |
| **Implementation** | Health registry where components register their health check functions. Aggregated endpoint returning status per component. |

### Order 8: Immutable Knowledge Store (IKS)

| Property | Value |
|----------|-------|
| **Purpose** | Versioned, immutable fact store backing the Knowledge Engine. |
| **Dependencies** | Persistence (DB session), Logging |
| **Why eighth** | IKS is the data backbone for Knowledge Engine (ES-002). It must exist before Knowledge Engine implementation begins. ADR-002 Phase 1 (KnowledgeEngine facade) starts here. |
| **Implementation** | `ImmutableKnowledgeStore` per existing `app/shunya/knowledge_store.py` (383 lines). SQLAlchemy model (`KnowledgeFact`). Versioning through supersession. |

### Order 9: Credential Store (ADR-003)

| Property | Value |
|----------|-------|
| **Purpose** | Encrypted credential storage with Phase 4 eligibility gating. Accessible only by Executor Engine. |
| **Dependencies** | Persistence (credential_metadata table), Configuration (encryption key), Logging |
| **Why ninth** | Credential Store is consumed by Executor Engine (ES-005). It must exist before Executor implementation. However, it is not needed by earlier engines (Identity, Knowledge, Context Fusion). |
| **Implementation** | `CredentialStore` per ADR-003 contract. AES-256-GCM encryption. Phase 4 eligibility gate integration. Audit logging (without credential values). |

### Order 10: KnowledgeLayer → IKS Migration (ADR-002 Phase 1-2)

| Property | Value |
|----------|-------|
| **Purpose** | KnowledgeEngine facade wrapping IKS + KnowledgeLayer. Migration script to seed IKS from KnowledgeLayer markdown data. |
| **Dependencies** | IKS (exists), KnowledgeLayer (existing, in legacy/) |
| **Why tenth** | Phase 1 (Coexistence) requires IKS to exist. Phase 2 (Seed) requires the migration script. Both depend on IKS being operational. |
| **Implementation** | `KnowledgeEngine` facade per ADR-002 contract. Migration script reading `knowledge-base.md` and creating KnowledgeFacts. Verification report. |

---

## 6. Phase Implementation Plan

### Phase A: Foundation

| Property | Value |
|----------|-------|
| **Objectives** | Establish shared infrastructure foundation. All infrastructure components operational before any engine implementation begins. |
| **Deliverables** | DI container, Configuration loading, Persistence layer, Logging, Metrics, Health endpoint |
| **Dependencies** | None |
| **Exit criteria** | All 6 infrastructure components pass unit tests. Application boots with valid configuration. Database migrations run cleanly. Structured logging produces output at configured level. Metrics endpoint responds with prometheus format. Health endpoint reports healthy. |
| **Verification criteria** | Infrastructure tests pass (test_di.py, test_config.py, test_persistence.py, test_logging.py, test_metrics.py, test_health.py). Full startup sequence verified. |
| **Estimated complexity** | Low (2-3 sprints) |
| **Risk** | Low — well-understood patterns. No novel infrastructure. |

### Phase B: Event Bus & Credential Store

| Property | Value |
|----------|-------|
| **Objectives** | Core shared infrastructure operational. Event Bus enables inter-engine communication. Credential Store operational (but not yet consumed). |
| **Deliverables** | EventBus (ADR-001), CredentialStore (ADR-003), IKS implementation |
| **Dependencies** | Phase A (DI, Config, Persistence, Logging, Metrics, Health) |
| **Exit criteria** | EventBus publishes and delivers events per ADR-001 contract. Event ordering, idempotency, retry, dead-letter verified. CredentialStore stores, resolves, revokes, lists credentials per ADR-003 contract. Encrypted at rest. Phase 4 eligibility gate integrated. |
| **Verification criteria** | Infrastructure tests pass (test_event_bus.py, test_credential_store.py). EventBus contract tests (publish, subscribe, unsubscribe, idempotency, retry, dead-letter). CredentialStore contract tests (resolve, store, revoke, list, expiry, eligibility, tenant isolation). |
| **Estimated complexity** | Medium (3-4 sprints) |
| **Risk** | Low — Event Bus is in-process (no distributed complexity). Credential Store is greenfield but well-specified. |

### Phase C: Knowledge Store Transition (ADR-002 Phase 1-2)

| Property | Value |
|----------|-------|
| **Objectives** | KnowledgeEngine facade operational. IKS seeded with KnowledgeLayer data. KnowledgeLayer is read-only fallback. |
| **Deliverables** | KnowledgeEngine facade (ADR-002 Phase 1), Migration script (ADR-002 Phase 2), Seeded IKS |
| **Dependencies** | Phase B (IKS, Event Bus) |
| **Exit criteria** | KnowledgeEngine facade wraps IKS + KnowledgeLayer. All 5 existing KnowledgeLayer call sites function through facade. Migration script reads all KnowledgeLayer data and creates IKS KnowledgeFacts. Migration report confirms 100% coverage. IKS is authoritative source. KnowledgeLayer is read-only fallback. |
| **Verification criteria** | KnowledgeEngine tests (get_fact, set_fact, search_facts, get_fact_history). Migration tests (all destinations migrated, no data loss, fact key mapping correct). ADR-002 Phase 1-2 verification items satisfied. |
| **Estimated complexity** | Medium (3-4 sprints) |
| **Risk** | Medium — migration script must handle edge cases in KnowledgeLayer markdown parsing. Fact key mapping must be verified for all destination types. |

### Phase D: Identity Engine (ES-010)

| Property | Value |
|----------|-------|
| **Objectives** | Identity Engine operational. Identity resolution, registration, verification, supersession, merge implemented. |
| **Deliverables** | IdentityEngine (engine.py, models.py, normalizer.py) |
| **Dependencies** | Phase B (IKS — stores identity records), Phase A (Logging, Metrics) |
| **Exit criteria** | All 8 identity types supported. Resolution deterministic. AMBIGUOUS correctly returned for multiple matches. Identity lifecycle (Active → Verified → Superseded → Merged) implemented. Tenant isolation enforced. No silent merges. Identity records versioned. |
| **Verification criteria** | ES-010 verification gate satisfied — 7 state transition tests, 7 failure mode tests, 12 edge case tests. Integration with Knowledge Engine verified. Tenant isolation test: same phone in different tenants resolves to different persons. |
| **Estimated complexity** | Medium (3-4 sprints) |
| **Risk** | Low — deterministic identity resolution is well-understood. Implementation exists (270 lines). |

### Phase E: Context Fusion Engine (ES-009)

| Property | Value |
|----------|-------|
| **Objectives** | Context Fusion Engine operational. Context assembly from identity, memory, evidence, documents. Phase 4 eligibility gates. Budget enforcement. |
| **Deliverables** | ContextFusionEngine (engine.py, providers.py, eligibility.py) |
| **Dependencies** | Phase D (Identity Engine), Phase C (Knowledge Engine), Phase B (Event Bus) |
| **Exit criteria** | Context assembly from all source providers. Identity resolution integrated. Phase 4 eligibility gates applied per section. Budget enforcement (item count and size). Fingerprints computed. Degraded mode returns documented exclusions. Serves all 6 downstream engines. |
| **Verification criteria** | ES-009 verification gate satisfied — 9 state transition tests, 6 failure mode tests. Integration with Identity Engine, Knowledge Engine, Phase 4. Degraded mode verified (source provider timeout returns empty section with documented reason). Budget enforcement verified (context truncated when over limit). |
| **Estimated complexity** | High (4-5 sprints) |
| **Risk** | Medium — Phase 4 (Privacy) integration is external. Source provider reliability affects degradation. Computation-only implementation exists (334 lines) as reference. |

### Phase F: Reasoning Engine (ES-003)

| Property | Value |
|----------|-------|
| **Objectives** | Reasoning Engine operational. Stimulus analysis, evidence chain building, confidence scoring, recommendation production. |
| **Deliverables** | ReasoningEngine (engine.py, strategies.py) |
| **Dependencies** | Phase E (Context Fusion), Phase C (Knowledge Engine) |
| **Exit criteria** | All reasoning strategies implemented. Evidence chains produced for every decision. Confidence scores canonical (0.0–1.0). Explainable decisions (decision + confidence + evidence chain + explanation). Insufficient context handled (low-confidence result). |
| **Verification criteria** | ES-003 verification gate satisfied. Integration with Context Fusion (context delivered, degraded, error). Constitutional: Invariant 4 (Reasoning never executes) verified. SHALL NEVER enforced. |
| **Estimated complexity** | High (5-6 sprints) |
| **Risk** | Medium — reasoning quality depends on context quality. Evidence chain building is the core intellectual challenge. |

### Phase G: Planner Engine (ES-004)

| Property | Value |
|----------|-------|
| **Objectives** | Planner Engine operational. Plan creation from reasoning results with step sequencing, cost estimation, timeline computation. |
| **Deliverables** | PlannerEngine (engine.py, templates.py) |
| **Dependencies** | Phase F (Reasoning Engine), Phase C (Knowledge Engine), Phase E (Context Fusion) |
| **Exit criteria** | Plans produced from reasoning results. Steps sequenced with dependencies. Cost and timeline estimates computed. Alternatives generated. Degraded planning works with incomplete context. Failure modes handled (ambiguous reasoning, missing knowledge). |
| **Verification criteria** | ES-004 verification gate satisfied. Integration with Reasoning (reasoning results received, ambiguous reasoning handled). Plans conform to Governance input contract. |
| **Estimated complexity** | Medium (3-4 sprints) |
| **Risk** | Low — planning is well-understood. Template-based approach reduces complexity. |

### Phase H: Governance Engine (ES-001)

| Property | Value |
|----------|-------|
| **Objectives** | Governance Engine operational. Policy evaluation, constitutional compliance checking, risk assessment, audit trail. |
| **Deliverables** | GovernanceEngine (engine.py, policies.py, audit.py) |
| **Dependencies** | Phase G (Planner), Phase C (Knowledge Engine — policy definitions), Phase E (Context Fusion) |
| **Exit criteria** | Policy registry operational. All 10 constitutional principles mapped to evaluable policies. APPROVE/REVIEW/REJECT returned correctly. Audit trail immutable. Tenant isolation enforced. Context enrichment operational. |
| **Verification criteria** | ES-001 verification gate satisfied — 14 state transition tests, 8 failure mode tests. Integration with Planner (plan received), Executor (approved plan dispatched), Observer (decision recorded). Constitutional: Invariant 3 (Governance precedes execution) verified. |
| **Estimated complexity** | High (5-6 sprints) |
| **Risk** | Medium — policy evaluation is the core of constitutional compliance. Audit immutability must be verified. Existing implementation (411 lines) provides reference. |

### Phase I: Executor Engine (ES-005)

| Property | Value |
|----------|-------|
| **Objectives** | Executor Engine operational. Multi-channel execution with credential resolution, retry, fallback. |
| **Deliverables** | ExecutorEngine (engine.py), Channel adapters (whatsapp.py, telegram.py, email.py, api.py) |
| **Dependencies** | Phase H (Governance Engine), Phase B (Credential Store), Phase E (Context Fusion) |
| **Exit criteria** | All 4 channel adapters implemented. Credential resolution at execution time operational. Credentials discarded after task completion. Retry with backoff operational. Fallback to alternative channel operational. Partial delivery reporting operational. |
| **Verification criteria** | ES-005 verification gate satisfied. Integration with Governance (approved plan received), Credential Store (credential resolved, discarded). Constitutional: Invariant 5 (Executor never reasons) verified. Security: credential leakage test passes. |
| **Estimated complexity** | Medium (4-5 sprints) |
| **Risk** | Medium — channel adapter reliability depends on external APIs. Credential handling must be security-reviewed. |

### Phase J: Observer Engine (ES-006)

| Property | Value |
|----------|-------|
| **Objectives** | Observer Engine operational. Continuous observation, discrepancy detection, anomaly flagging. |
| **Deliverables** | ObserverEngine (engine.py, models.py) |
| **Dependencies** | Phase I (Executor), Phase C (Knowledge Engine), Phase E (Context Fusion) |
| **Exit criteria** | Observations recorded for every execution (100% basic observation). Discrepancy detection operational. Detailed validation sampling (configurable, default 10% for successful executions). Anomaly detection flags discrepancies. Observations stored in Knowledge Engine. |
| **Verification criteria** | ES-006 verification gate satisfied. Integration with Executor (outcome received), Knowledge Engine (observation stored). Constitutional: Invariant 5 (Observation is continuous), Invariant 6 (Execution is observable) verified. M6 clarified: basic observation 100%, detailed validation configurable. |
| **Estimated complexity** | Low (2-3 sprints) |
| **Risk** | Low — observation is straightforward recording. Discrepancy detection is the only non-trivial component. |

### Phase K: Doctor Engine (ES-008)

| Property | Value |
|----------|-------|
| **Objectives** | Doctor Engine operational. System integrity checks, architecture drift detection, package health validation, compliance confirmation. |
| **Deliverables** | DoctorEngine (engine.py, checks.py) |
| **Dependencies** | All engines (health data), Phase C (Knowledge Engine — integrity data), Phase H (Governance — audit log) |
| **Exit criteria** | All 4 check types implemented (integrity, drift, package health, compliance). Health aggregation from all engines operational. Violation events published on Event Bus. Check schedule configurable. Degraded when engine health data unavailable. |
| **Verification criteria** | ES-008 verification gate satisfied — 5 state transition tests, 5 failure mode tests. Integration with Knowledge Engine (integrity violation received), Governance (audit log read). |
| **Estimated complexity** | Low (2-3 sprints) |
| **Risk** | Low — checks are observation-only (no side effects). Partial implementation exists (113 lines). |

### Phase L: Learning Engine (ES-007)

| Property | Value |
|----------|-------|
| **Objectives** | Learning Engine operational. Outcome analysis, pattern detection, learning signal generation, confidence calibration. |
| **Deliverables** | LearningEngine (engine.py, patterns.py) |
| **Dependencies** | Phase J (Observer — outcomes), Phase C (Knowledge Engine — facts), Phase H (Governance — decisions), Phase E (Context Fusion — workspace context) |
| **Exit criteria** | Learning signals generated from outcome analysis. Cold start mode implemented (collects without recommending). Confidence calibration with damping factor. Signals validated by Governance before application. Knowledge Engine updated with learned facts. |
| **Verification criteria** | ES-007 verification gate satisfied. Integration with Observer (outcomes received), Knowledge Engine (facts written), Governance (signals validated). Constitutional: Invariant 3 (Evidence precedes learning), Invariant 4 (Learning never bypasses governance) verified. |
| **Estimated complexity** | High (5-6 sprints) |
| **Risk** | Medium — learning quality depends on observation quality. Cold start period may be lengthy. Confidence calibration requires tuning. |

### Phase M: KnowledgeLayer Retirement (ADR-002 Phase 3-4)

| Property | Value |
|----------|-------|
| **Objectives** | KnowledgeLayer fully retired. No code path depends on it. IKS is the sole knowledge store. |
| **Deliverables** | KnowledgeEngine facade (IKS only), KnowledgeLayer removed, knowledge-base.md archived |
| **Dependencies** | Phase C (KnowledgeEngine facade operational, IKS seeded) |
| **Exit criteria** | No code path falls back to KnowledgeLayer. KnowledgeLayer class and markdown file removed. All imports updated to KnowledgeEngine. KnowledgeLayer tests removed. End-to-end verification: all 5 previously KnowledgeLayer-dependent paths function through IKS. |
| **Verification criteria** | ADR-002 Phase 3-4 verification items satisfied. No KnowledgeLayer imports remain. KnowledgeLayer removal confirmed by code search. |
| **Estimated complexity** | Low (1 sprint) |
| **Risk** | Low — KnowledgeLayer is already wrapped. Removal is mechanical verification. |

### Phase N: Integration & Hardening

| Property | Value |
|----------|-------|
| **Objectives** | Full pipeline end-to-end verified. All 10 engines integrated. Constitutional invariants enforced in CI. Performance benchmarks established. |
| **Deliverables** | Full pipeline integration tests, Performance benchmarks, Constitutional invariant CI checks |
| **Dependencies** | All phases A–M complete |
| **Exit criteria** | Full pipeline test passes (External Trigger → Observation → Knowledge Resolution → Context Fusion → Reasoning → Planning → Governance → Execution → Observation → Knowledge Update → Learning → Continuous Improvement). All 14 structural invariants and 12 behavioral invariants verified in CI. Performance within budget (latency p99 for each engine per spec). |
| **Verification criteria** | Full pipeline integration test. Constitutional invariant test suite (26 invariants). Performance benchmark suite. |
| **Estimated complexity** | Medium (3-4 sprints) |
| **Risk** | Medium — integration may reveal interface mismatches. Performance may require optimization. |

### Phase O: Release

| Property | Value |
|----------|-------|
| **Objectives** | First production release of SHUNYA platform. All engines operational. Documentation updated. Operations runbook complete. |
| **Deliverables** | Production deployment, Operations runbook, Release notes, Architecture checkpoint |
| **Dependencies** | Phase N (Integration & Hardening) |
| **Exit criteria** | All Definition of Done criteria for Program satisfied. Architecture checkpoint confirms zero divergence. Operations runbook verified. Release approved by Chief Software Architect and Chief Constitutional Architect. |
| **Verification criteria** | Release checklist complete. Operations runbook walkthrough successful. Architecture checkpoint: no new divergence between implementation and frozen architecture. |
| **Estimated complexity** | Medium (2-3 sprints) |
| **Risk** | Low — all risk is in preceding phases. Release is verification and deployment. |

---

## 7. Integration Matrix

| Engine A | Engine B | API Contract | Event Contract | Failure Contract | Retry | Ownership |
|----------|----------|-------------|---------------|-----------------|-------|-----------|
| Identity (ES-010) | Knowledge (ES-002) | `IKStore.get_fact()`, `IKStore.set_fact()` | `identity.resolved`, `identity.ambiguous`, `identity.registered`, `identity.superseded`, `identity.merged` | Knowledge Engine unavailable → buffer and retry with backoff (3 attempts) | Exponential (100ms, 500ms, 2s) | Identity Engine owns resolution; Knowledge Engine owns storage |
| Context Fusion (ES-009) | Identity (ES-010) | `IdentityEngine.resolve(claim)` | `identity.resolved` | Identity unavailable → return empty identity section | 2 attempts, 5s timeout | Context Fusion reads; Identity Engine resolves |
| Context Fusion (ES-009) | Knowledge (ES-002) | `IKStore.get_fact()`, `IKStore.search_facts()` | `knowledge.fact.created`, `knowledge.fact.superseded` | Knowledge unavailable → return degraded context | 2 attempts, 5s timeout | Context Fusion reads; Knowledge Engine stores |
| Context Fusion (ES-009) | Phase 4 (Privacy) | `EligibilityGate.check(purpose_code, section)` | (None — synchronous API) | Gate unavailable → return section denied (safe failure) | None | Phase 4 gates; Context Fusion enforces |
| Reasoning (ES-003) | Context Fusion (ES-009) | `ContextFusionEngine.assemble(request)` | `context.fusion.completed`, `context.fusion.section.degraded` | Context unavailable → return low-confidence result | None | Reasoning reads; Context Fusion assembles |
| Reasoning (ES-003) | Knowledge (ES-002) | `IKStore.get_fact()`, `IKStore.search_facts()` | `knowledge.fact.created`, `knowledge.fact.superseded` | Knowledge unavailable → degraded reasoning | 2 attempts, 3s timeout | Reasoning reads; Knowledge Engine stores |
| Planner (ES-004) | Reasoning (ES-003) | `ReasoningEngine.reason(context)` | `reasoning.completed` | Reasoning unavailable → cannot plan | None | Planner reads; Reasoning produces |
| Planner (ES-004) | Knowledge (ES-002) | `IKStore.get_fact()`, `IKStore.search_facts()` | (None — read-only) | Knowledge unavailable → plan with cached data | 2 attempts | Planner reads; Knowledge Engine stores |
| Planner (ES-004) | Context Fusion (ES-009) | `ContextFusionEngine.assemble(request)` | `context.fusion.completed` | Context degraded → plan with degraded context | None | Planner reads; Context Fusion assembles |
| Governance (ES-001) | Planner (ES-004) | `GovernanceEngine.validate(plan, context)` | `plan.created` | Planner unavailable → cannot validate | None | Governance validates; Planner produces |
| Governance (ES-001) | Knowledge (ES-002) | `IKStore.get_fact()` (policy definitions) | `policy.registry.updated` | Knowledge unavailable → cannot evaluate policies | 2 attempts | Governance reads; Knowledge Engine stores policies |
| Governance (ES-001) | Context Fusion (ES-009) | `ContextFusionEngine.assemble(request)` | `context.fusion.completed` | Context degraded → lower confidence evaluation | None | Governance reads; Context Fusion assembles |
| Executor (ES-005) | Governance (ES-001) | `GovernanceEngine.validate(plan, context)` | `governance.action.approved` | Governance unavailable → cannot execute | None (must have APPROVE) | Executor consumes; Governance produces |
| Executor (ES-005) | Credential Store (ADR-003) | `CredentialStore.resolve(ref, tenant, purpose, actor)` | (None — synchronous API) | Credential unavailable → task fails; isolate to task | 3 attempts, exponential | Executor resolves; Credential Store stores |
| Executor (ES-005) | Context Fusion (ES-009) | `ContextFusionEngine.assemble(request)` | `context.fusion.completed` | Context degraded → execute with degraded context | None | Executor reads; Context Fusion assembles |
| Observer (ES-006) | Executor (ES-005) | (None — event-driven) | `execution.completed`, `execution.failed` | Executor unavailable → cannot observe | 3 attempts | Observer consumes; Executor produces |
| Observer (ES-006) | Knowledge (ES-002) | `IKStore.set_fact()` (observation storage) | `observation.recorded` | Knowledge unavailable → buffer observation locally | 3 attempts, 5s timeout | Observer writes; Knowledge Engine stores |
| Observer (ES-006) | Context Fusion (ES-009) | `ContextFusionEngine.assemble(request)` | `context.fusion.completed` | Context degraded → observation without context | None | Observer reads; Context Fusion assembles |
| Learning (ES-007) | Observer (ES-006) | (None — event-driven) | `observation.recorded`, `observation.discrepancy.detected` | Observer unavailable → no new signals | None | Learning consumes; Observer produces |
| Learning (ES-007) | Knowledge (ES-002) | `IKStore.set_fact()` (learned facts) | `learning.signal.generated` | Knowledge unavailable → defer signal | 3 attempts | Learning writes; Knowledge Engine stores |
| Learning (ES-007) | Governance (ES-001) | (None — event-driven) | `governance.decision.logged` | Governance unavailable → learn without governance context | None | Learning consumes; Governance produces |
| Learning (ES-007) | Context Fusion (ES-009) | `ContextFusionEngine.assemble(request)` | `context.fusion.completed` | Context degraded → learn without full context | None | Learning reads; Context Fusion assembles |
| Doctor (ES-008) | All engines | Health API (read) | `doctor.check.completed`, `doctor.violation.detected` | Engine health unavailable → degraded report | None (next cycle) | Doctor reads; All engines expose health |
| Doctor (ES-008) | Knowledge (ES-002) | Integrity API (read) | `knowledge.integrity.violation` | Knowledge unavailable → skip integrity checks | None (next cycle) | Doctor reads; Knowledge Engine exposes |
| Doctor (ES-008) | Governance (ES-001) | Audit Log API (read) | `governance.decision.logged` | Governance unavailable → skip compliance checks | None (next cycle) | Doctor reads; Governance Engine exposes |

---

## 8. Verification Program

### Per-Engine Verification Gates

| Engine | Unit Tests | Contract Tests | Integration Tests | Constitutional Tests | Performance Tests | Failure Tests | Security Tests | Acceptance Tests |
|--------|-----------|---------------|-------------------|---------------------|-------------------|---------------|----------------|------------------|
| ES-001 Governance | 14 state transition, 8 error, 12 edge case | Input/output contract | Planner, Executor, Observer, Context Fusion | Invariant 3 (Governance precedes execution) | p50 < 50ms, p99 < 200ms | 8 failure modes | No eval/exec, no credential leakage, input validation | All verdict types produced |
| ES-002 Knowledge | All fact operations, versioning, supersession | Fact key schema, confidence model | Observer (write), Learning (write), Context Fusion (read) | Invariant 1 (Evidence immutable), Invariant 2 (Knowledge versioned) | p50 < 10ms, p99 < 50ms | 5 failure modes | No credentials in fact values | IKS operational, KnowledgeLayer wrapped |
| ES-003 Reasoning | Strategy tests, evidence chain building | ReasoningResult contract | Context Fusion (context received) | Invariant 4 (Reasoning never executes) | p50 < 100ms, p99 < 500ms | 5 failure modes | No credential access | All reasoning types supported |
| ES-004 Planner | Plan generation, cost estimation, timeline | Plan contract | Reasoning (results received) | Invariant 2 (Every decision explainable) | p50 < 50ms, p99 < 200ms | 4 failure modes | No credential access | Plans produced from any reasoning result |
| ES-005 Executor | Channel adapters, credential resolution | DeliveryResult contract | Governance (approved plan), Credential Store (resolve/discard) | Invariant 5 (Executor never reasons) | p50 < 100ms, p99 < 500ms | 6 failure modes | Credential leakage test, no credentials in logs | All channels operational |
| ES-006 Observer | Observation recording, discrepancy detection | OutcomeObservation contract | Executor (outcome), Knowledge (storage) | Invariant 5 (Observation continuous), Invariant 6 (Execution observable) | p50 < 50ms, p99 < 200ms | 4 failure modes | No credential access | 100% basic observation |
| ES-007 Learning | Pattern detection, signal generation, calibration | LearningSignal contract | Observer (outcomes), Knowledge (write), Governance (validate) | Invariant 3 (Evidence precedes learning), Invariant 4 (Learning never bypasses governance) | p50 < 200ms, p99 < 1s | 5 failure modes | No live credential/payment data access | Signals generated, Governance-validated |
| ES-008 Doctor | Check type tests, report assembly | DoctorReport contract | Knowledge (integrity), Governance (compliance) | Article 7 (Documentation Currency), Article 8 (Divergence Protocol) | p50 < 200ms, p99 < 1s per cycle | 5 failure modes | Read-only, no write access | All 4 check types operational |
| ES-009 Context Fusion | State transitions, source providers, budgets | WorkspaceContext contract | Identity (resolution), Knowledge (memory), Phase 4 (eligibility) | Invariant 7 (No back channels), §9 (Workspace isolation) | p50 < 100ms, p99 < 500ms | 6 failure modes | No credential access, tenant isolation | All source providers integrated |
| ES-010 Identity | State transitions, normalization, ambiguity | ResolutionResult contract | Knowledge (storage), Context Fusion (resolution) | Invariant 8 (Identity globally unique), §3 Principles 1-4 | p50 < 10ms, p99 < 50ms | 7 failure modes | Tenant isolation, no silent merges | All 8 identity types supported |

### Cross-Cutting Verification

| Verification | Scope | Method | Frequency |
|-------------|-------|--------|-----------|
| Dependency graph acyclicity | All engines | Static analysis (import graph) | Every commit |
| SHALL NEVER enforcement | Per engine | Integration test verifying prohibited action rejected | Per PR |
| Tenant isolation | All engines | Integration test: cross-tenant access returns error | Per PR |
| Immutable knowledge | Knowledge Engine | Integration test: update creates new version, original preserved | Per PR |
| Event envelope compliance | All engines | Schema validation on every event published | Every commit |
| Confidence scale compliance | All engines | Range check (0.0–1.0) on every confidence output | Every commit |

---

## 9. Testing Strategy

### Test Pyramid

```
             ╱╲
            ╱  ╲         Constitutional Tests (5-10)
           ╱    ╲
          ╱      ╲       System Tests (10-20)
         ╱        ╲
        ╱          ╲     Integration Tests (50-100)
       ╱            ╲
      ╱              ╲   Contract Tests (100-200)
     ╱                ╲
    ╱                  ╲  Unit Tests (500-1000)
   ╱                    ╲
  ╱──────────────────────╲
```

### Test Categories

**Unit Tests** — Test a single class or function in isolation. Mock all external dependencies. Coverage target: 90%+ per engine module.

**Contract Tests** — Test that an engine's public API conforms to its specification's input/output contract. Run against the interface before the implementation exists (interface-first principle).

**Integration Tests** — Test that two engines or components work together correctly. Use real implementations for the engines under test; mock external dependencies.

**System Tests** — Test the full pipeline end-to-end. All 10 engines connected. External dependencies (WhatsApp API, email) are mocked at the adapter boundary.

**Constitutional Tests** — Test that architectural invariants are enforced. These are the most important tests — they verify constitutional compliance, not just functional correctness.

### Fixtures

- **Golden Dataset** — `tests/data/golden_dataset.json`: A complete, pre-verified dataset containing sample identity records, knowledge facts, policies, plans, and expected outcomes for every engine. Used for regression testing across all engines.
- **Per-Engine Fixtures** — Each engine's `conftest.py` provides engine-specific fixtures (sample identity claims, sample knowledge facts, sample plans).
- **Integration Fixtures** — `tests/conftest.py` provides shared fixtures (EventBus instance, DB session, application context).

### Simulation / Mocking

| Component | Mock Strategy | Notes |
|-----------|--------------|-------|
| Event Bus | Real in-process instance | Lightweight enough for test use — no mocking needed |
| Credential Store | In-memory implementation | Test credentials stored in-memory, never persisted |
| Channel adapters (WhatsApp, email) | Mock at adapter boundary | External API calls are mocked |
| Phase 4 (Privacy) | Mock gate | Returns configurable eligibility results per test case |
| Knowledge Engine | In-memory IKS implementation | Test facts stored in-memory |
| Identity Engine | Real implementation | Deterministic — no external dependencies |

### Golden Datasets

| Dataset | Purpose | Size |
|---------|---------|------|
| `identity_fixtures` | Sample identity claims + expected resolution results | 50 records |
| `knowledge_fixtures` | Sample knowledge facts with versions | 200 facts |
| `context_fixtures` | Sample context requests + expected WorkspaceContext | 30 scenarios |
| `reasoning_fixtures` | Sample context + expected reasoning results | 20 scenarios |
| `plan_fixtures` | Sample reasoning results + expected plans | 15 scenarios |
| `governance_fixtures` | Sample plans + expected verdicts | 25 scenarios |
| `execution_fixtures` | Sample approved plans + expected delivery results | 15 scenarios |
| `observation_fixtures` | Sample execution outcomes + expected observations | 20 scenarios |
| `learning_fixtures` | Sample observations + expected learning signals | 10 scenarios |
| `doctor_fixtures` | Sample health data + expected DoctorReports | 10 scenarios |

### Constitutional Tests

These tests are the highest priority. They verify that the implementation does not violate any architectural invariant.

```
tests/constitutional/
├── test_invariant_1_evidence_immutable.py
├── test_invariant_2_knowledge_versioned.py
├── test_invariant_3_governance_before_execution.py
├── test_invariant_4_reasoning_never_executes.py
├── test_invariant_5_executor_never_reasons.py
├── test_invariant_6_observer_never_governs.py
├── test_invariant_7_learning_never_mutates_evidence.py
├── test_invariant_8_identity_globally_unique.py
├── test_invariant_9_tenant_isolation.py
├── test_invariant_10_audit_append_only.py
├── test_invariant_11_confidence_explicit.py
├── test_invariant_12_provenance_present.py
├── test_invariant_13_canonical_event_envelope.py
├── test_invariant_14_acyclic_dependencies.py
├── test_behavioral_1_every_execution_follows_governance.py
├── test_behavioral_2_every_decision_explainable.py
├── test_behavioral_3_evidence_precedes_learning.py
├── test_behavioral_4_learning_never_bypasses_governance.py
├── test_behavioral_5_observation_continuous.py
├── test_behavioral_6_execution_observable.py
├── test_behavioral_7_no_back_channels.py
├── test_behavioral_8_no_direct_state_mutation.py
├── test_behavioral_9_every_workflow_recoverable.py
├── test_behavioral_10_every_workflow_auditable.py
├── test_behavioral_11_human_review_timeboxed.py
└── test_behavioral_12_degradation_explicit.py
```

---

## 10. Migration Strategy

### What Stays

| Component | Reason | Duration |
|-----------|--------|----------|
| `app/shunya/knowledge.py` (KnowledgeLayer) | Wired in 5 call sites | Until ADR-002 Phase 4 |
| `app/data/knowledge-base.md` | Data source for KnowledgeLayer | Until ADR-002 Phase 4 |
| `app/routes.py` | Web routing | Kept during migration |
| `app/shunya/workflow.py` | Workflow orchestration | Kept during migration |
| `app/client_portal.py` | Client portal | Kept during migration |
| Database tables (existing) | Panchi Club data | Kept, may be migrated later |
| `app/shunya/__init__.py` exports | Existing package API | Extended (not removed) |

### What Is Replaced

| Component | Replacement | Phase |
|-----------|-------------|-------|
| KnowledgeLayer (data source) | ImmutableKnowledgeStore | ADR-002 Phase 2-4 |
| `from .knowledge import KnowledgeLayer` | `from ..knowledge.engine import KnowledgeEngine` | ADR-002 Phase 1-3 |
| Existing GovernanceLayer (411 lines) | GovernanceEngine per ES-001 | Phase H |
| Existing ReasoningLayer | ReasoningEngine per ES-003 | Phase F |
| Existing PlannerLayer | PlannerEngine per ES-004 | Phase G |
| Existing Executor (Telegram-only) | ExecutorEngine per ES-005 with multi-channel | Phase I |

### What Is Wrapped

| Component | Wrapper | Duration |
|-----------|---------|----------|
| KnowledgeLayer | `KnowledgeEngine` facade (ADR-002) | Phases 1-3 (then retired) |
| Existing workflow | `LegacyWorkflowAdapter` in `app/shunya/legacy/workflow.py` | Phases A-M (then replaced) |
| Existing routes | `LegacyRouteAdapter` in `app/shunya/legacy/routes.py` | Phases A-M (then refactored) |

### What Is Retired

| Component | Retired In | Condition |
|-----------|-----------|-----------|
| `app/shunya/knowledge.py` (KnowledgeLayer) | Phase M | All data migrated to IKS, no code path falls back |
| `app/data/knowledge-base.md` | Phase M | All destinations represented in IKS, migration verified |
| Legacy workflow | After Phase M | Full pipeline operational |
| Legacy routes | After Phase M | New API contract in place |

### Rollback Strategy

| Migration Step | Rollback Action | Data Safety |
|---------------|----------------|-------------|
| ADR-002 Phase 1 (Coexistence facade) | Remove facade, restore direct KnowledgeLayer imports | Safe — IKS is not yet primary |
| ADR-002 Phase 2 (Seed IKS) | IKS is seeded but not primary | Safe — KnowledgeLayer is still authoritative |
| ADR-002 Phase 3 (Cutover) | Revert to KnowledgeLayer as primary | IKS data is preserved |
| ADR-002 Phase 4 (Retire KnowledgeLayer) | Restore KnowledgeLayer from git + verify markdown file | Complex — requires manual KB restore |
| Engine replacement (Phase D-K) | Old implementation preserved in `legacy/` until next phase | Old code is importable |

### Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| KnowledgeLayer migration loses data | Dry-run migration before actual seed. Compare record counts. Verify random sample manually. |
| Engine replacement breaks existing call sites | Legacy wrappers maintain backward compatibility. Every engine replacement has a coexistence phase. |
| IKS performance worse than KnowledgeLayer | Latency benchmarks before cutover. IKS uses indexed DB queries vs in-memory dict — expected to be comparable or better. |
| ADR-002 Phase 4 removes code that is still needed | Code search confirms zero remaining imports before removal. CI fails if any import path is broken. |

---

## 11. Delivery Strategy

### Branch Strategy

```
main                  ── Production-ready. Only merge-ready, verified code.
  │
  ├── develop         ── Integration branch. All feature branches merge here.
  │     │
  │     ├── phase/{phase-name}    ── Phase-specific development branch.
  │     │     │
  │     │     ├── engine/{engine-name}/interface    ── Interface implementation
  │     │     ├── engine/{engine-name}/logic         ── Internal logic
  │     │     └── engine/{engine-name}/integration   ── Integration tests
  │     │
  │     └── infra/{component}     ── Infrastructure component development
  │
  └── release/v1.0.0  ── Release branch (cut from develop at phase completion)
```

### Merge Strategy

1. Feature branch → `develop`: Requires PR review + passing CI (unit, integration, constitutional tests)
2. `develop` → `main`: Requires milestone completion + architecture checkpoint sign-off
3. No direct commits to `main` — all changes flow through `develop`

### Review Strategy

| Change Type | Required Reviewers | Approval |
|-------------|-------------------|----------|
| Engine implementation | 2 senior engineers | Both must approve |
| Infrastructure change | 2 senior engineers + infrastructure lead | Both + lead |
| Engine spec change | Chief Software Architect | Requires ADR |
| Constitutional change | Chief Constitutional Architect | Requires Constitutional ADR |
| Migration (ADR-002) | Knowledge team lead + Chief Software Architect | Both |
| Integration test | Both affected engine owners | Both |

### Verification Gates

| Gate | Trigger | What Passes | Blocking? |
|------|---------|-------------|-----------|
| Pre-commit | Every commit | Linting (ruff), type checking (mypy) | Yes |
| CI (unit) | Every push | Unit tests, contract tests | Yes |
| CI (integration) | Every PR | Integration tests, constitutional tests | Yes |
| CI (full pipeline) | Merge to develop | System tests, performance benchmarks | Yes |
| Architecture checkpoint | Phase completion | Constitutional invariant tests, architecture compliance scan | Yes (milestone) |
| Release gate | Merge to release | All gates + security audit + operations verification | Yes (release) |

### Release Cadence

| Phase | Duration | Target |
|-------|----------|--------|
| Development sprints | 2 weeks | Feature completion |
| Integration sprints | 1 week | Cross-engine integration stabilization |
| Hardening sprints | 1 week | Performance, security, documentation |
| Release | 1 day | Deployment, verification, announcement |

**Expected phase duration: 10-15 sprints total (20-30 weeks for full program)**

### Deployment Strategy

1. **Deployment target:** Current Contabo VPS (single instance) — consistent with in-process Event Bus design
2. **Database migrations:** Alembic, applied before new code deployment
3. **Zero-downtime:** Not required for Phase 1 (maintenance window acceptable)
4. **Rollback:** Previous deployment kept ready for 24 hours post-deployment

### Documentation Requirements

| Document | Author | Maintained |
|----------|--------|------------|
| Engine API reference | Engine owner | Updated per PR |
| Operations runbook | Infrastructure team | Per release |
| Architecture checkpoint report | Chief Software Architect | Per phase completion |
| Release notes | Engineering team | Per release |

---

## 12. Risk Register

### Technical Risks

| ID | Risk | Probability | Impact | Mitigation | Owner |
|----|------|------------|--------|------------|-------|
| TR-01 | Event Bus performance degrades under load (queue overflow) | Medium | Medium | Queue size limits configured per ADR-001. Backpressure with configurable max queue size. Dead-letter queue prevents loss. | Infrastructure team |
| TR-02 | Credential Store encryption key management fails (key rotation, key loss) | Low | High | Encryption key managed by infrastructure platform, not Credential Store. Key backup in secure vault. Key rotation procedure documented. | Infrastructure team |
| TR-03 | IKS write throughput insufficient for high-volume observation recording | Low | Medium | IKS uses indexed PostgreSQL. Write performance is not expected to be a bottleneck for Phase 2 scale. Benchmarks in Phase N. | Knowledge team |
| TR-04 | Channel adapter reliability (WhatsApp API downtime, email SMTP failure) | Medium | Medium | Retry with backoff (3 attempts, exponential). Fallback to alternative channel. Partial delivery reporting. | Executor team |
| TR-05 | Learning Engine cold start produces no useful signals for extended period | Medium | Low | Cold start mode defined in ES-007. System operates correctly without learning signals. No blocking impact. | Learning team |

### Architectural Risks

| ID | Risk | Probability | Impact | Mitigation | Owner |
|----|------|------------|--------|------------|-------|
| AR-01 | Implementation diverges from frozen architecture (scope creep, convenience-driven changes) | High | High | Architecture checkpoint at every phase completion. Constitutional invariant tests in CI. Divergence protocol (Article 8) enforced. | Chief Software Architect |
| AR-02 | Engine SHALL NEVER lists are not enforced at the architectural boundary | Medium | High | Integration tests verify that prohibited actions are rejected. Constitution tests per engine. | Chief Software Architect |
| AR-03 | Circular dependency discovered in engine interaction (event bus creates hidden cycle) | Low | High | Static analysis verifies acyclic dependency graph on every commit. Event Bus is communication infrastructure, not an engine — it does not create cycles. | Chief Software Architect |

### Migration Risks

| ID | Risk | Probability | Impact | Mitigation | Owner |
|----|------|------------|--------|------------|-------|
| MR-01 | KnowledgeLayer → IKS migration loses or corrupts data | Low | High | Dry-run migration before actual seed. Report compares record counts. Random sample manually verified. Rollback available. | Knowledge team |
| MR-02 | Legacy code removal (Phase M) breaks a code path not caught by tests | Medium | Medium | Code search confirms zero remaining imports. CI runs full test suite. Coexistence phase catches issues before retirement. | Knowledge team |
| MR-03 | Engine replacement breaks API contract for existing consumers | Medium | Medium | Legacy wrappers maintain backward compatibility. Interface-first principle ensures contract tests pass before replacement. | Respective engine teams |

### Organizational Risks

| ID | Risk | Probability | Impact | Mitigation | Owner |
|----|------|------------|--------|------------|-------|
| OR-01 | Team does not have sufficient context on frozen architecture | Medium | High | Architecture baseline documents are reference material. Every engineer must read their engine's specification before implementation begins. | Chief Software Architect |
| OR-02 | Dependency between teams causes blocking (e.g., Context Fusion waits for Identity) | Medium | Medium | Phase plan sequences engines to minimize blocking. Identity and Knowledge are Phase 2 (no wait). Context Fusion is Phase 3 (after Identity). | Program management |
| OR-03 | Scope creep — requests to add features not in the frozen architecture | High | Medium | Architecture is frozen. New features require constitutional ADR. Scope discipline enforced per Engineering Constitution Article 9. | Chief Constitutional Architect |

### Operational Risks

| ID | Risk | Probability | Impact | Mitigation | Owner |
|----|------|------------|--------|------------|-------|
| OpR-01 | Single VPS instance cannot handle all 10 engines concurrently | Medium | High | Performance benchmarks in Phase N determine capacity. If insufficient, horizontal scaling options assessed (distributed Event Bus becomes required). | Infrastructure team |
| OpR-02 | Database migrations cause downtime | Medium | Low | Alembic migrations are forward-compatible. Maintenance window acceptable for Phase 2 releases. | Infrastructure team |

---

## 13. Definition of Done

### Feature Done

- [ ] Implementation matches the relevant section of the engine specification
- [ ] Unit tests pass (90%+ coverage for the feature)
- [ ] Contract tests pass (input/output validation)
- [ ] Integration tests pass for direct dependencies
- [ ] Constitutional invariant tests pass (no new violations)
- [ ] Code reviewed and approved
- [ ] No credentials, secrets, or PII in code
- [ ] Commit message references architectural authority (spec section, ADR number)
- [ ] Linting and type checking pass

### Engine Done

- [ ] All features implemented (per engine specification)
- [ ] All state transitions implemented (per state machine)
- [ ] All events published and consumed correctly
- [ ] All failure modes handled with documented recovery
- [ ] All SHALL NEVER prohibitions enforced and verified
- [ ] All constitutional mappings satisfied
- [ ] Observability (logging, metrics, tracing) operational
- [ ] Rollback strategy documented and verified
- [ ] Verification checklist (ES-{NNN} §13) 100% satisfied
- [ ] Integration tests with all dependent engines pass
- [ ] Performance within budget (p50, p99 per spec)
- [ ] Security review completed

### Phase Done

- [ ] All engines in this phase satisfy their Engine Done criteria
- [ ] All infrastructure components operational
- [ ] Integration tests for cross-engine workflows within the phase pass
- [ ] Constitutional invariant tests pass (full suite run)
- [ ] Architecture checkpoint: zero divergence between implementation and frozen architecture
- [ ] Phase documentation updated
- [ ] Phase exit criteria met (per Section 6)
- [ ] Chief Software Architect sign-off

### Release Done

- [ ] All phases for the release complete
- [ ] Full pipeline system tests pass
- [ ] Performance benchmarks within budget
- [ ] Security audit complete
- [ ] Operations runbook verified
- [ ] All verification checklists signed off
- [ ] Release candidate deployed to staging and verified
- [ ] Release notes published
- [ ] Chief Software Architect sign-off
- [ ] Chief Constitutional Architect sign-off (constitutional compliance)

### Program Done

- [ ] All 15 Implementation Phases (A through O) complete
- [ ] All 10 Engines (ES-001 through ES-010) implemented
- [ ] All shared infrastructure (ADR-001, ADR-002, ADR-003) operational
- [ ] KnowledgeLayer retired (ADR-002 Phase 4 complete)
- [ ] Full pipeline end-to-end test passes
- [ ] All 26 architectural invariants enforced and verified
- [ ] All verification checklists satisfied
- [ ] Architecture checkpoint confirms zero divergence
- [ ] Production deployment operational
- [ ] Operations runbook verified
- [ ] Release approved by Chief Software Architect and Chief Constitutional Architect

---

## 14. Master Timeline

### Dependency-Aware Roadmap

```
Sprint  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15
Phase   ◄── A ──►◄── B ──►◄── C ──►◄── D ──►◄── E ──►◄── F ──►◄── G ──►◄── H ──►◄── I ──►◄── J ──►◄── K ──►◄M►◄N►◄O►
         Foundation  EventBus/   IKS        Identity   Context    Reasoning  Planner    Governance Executor  Observer   Learning   Retire  Int  Rel
                     CredStore   Migration                       
                                 
Phase A (Foundation):       ████████████████  (2 sprints — 4 weeks)
Phase B (EventBus/Cred):   ║     ████████████████████  (3 sprints — 6 weeks)
Phase C (IKS Migration):   ║     ║     ████████████████████  (3 sprints — 6 weeks)
Phase D (Identity):        ║     ║     ║     ████████████████████  (3 sprints — 6 weeks)
Phase E (Context Fusion):  ║     ║     ║     ║     ██████████████████████  (4 sprints — 8 weeks)
Phase F (Reasoning):       ║     ║     ║     ║     ║     ██████████████████████  (5 sprints — 10 weeks)
Phase G (Planner):         ║     ║     ║     ║     ║     ║     ████████████████  (3 sprints — 6 weeks)
Phase H (Governance):      ║     ║     ║     ║     ║     ║     ║     ██████████████████████  (5 sprints — 10 weeks)
Phase I (Executor):        ║     ║     ║     ║     ║     ║     ║     ║     ████████████████████  (4 sprints — 8 weeks)
Phase J (Observer):        ║     ║     ║     ║     ║     ║     ║     ║     ║     ████████████  (2 sprints — 4 weeks)
Phase K (Learning):        ║     ║     ║     ║     ║     ║     ║     ║     ║     ║     ██████████████████████  (5 sprints — 10 weeks)
Phase M (Retire KL):       ║     ║     ║     ║     ║     ║     ║     ║     ║     ║     ║     ████  (1 sprint — 2 weeks)
Phase N (Integration):     ║     ║     ║     ║     ║     ║     ║     ║     ║     ║     ║     ║  ████████████████  (3 sprints — 6 weeks)
Phase O (Release):         ║     ║     ║     ║     ║     ║     ║     ║     ║     ║     ║     ║  ║  ████████████  (2 sprints — 4 weeks)

Total: 15 phases × ~2.2 sprints avg = ~33 sprints ≈ 66 weeks (15 months)
```

### Critical Path

The critical path is: **Phase A → Phase B → Phase C → Phase D → Phase E → Phase F → Phase G → Phase H → Phase I → Phase J → Phase K → Phase M → Phase N → Phase O**

This is the dependency chain. Any delay in any phase on this path directly delays the program end date.

### Parallel Work

The following phases can proceed in parallel once their dependencies are met:

| Parallel Group | Phases | Prerequisite | Rationale |
|----------------|--------|-------------|-----------|
| Infrastructure | A, B | None | Foundation + EventBus/Credential Store are independent of engines |
| Knowledge Foundation | C | B | IKS migration depends on Event Bus but not on identity |
| Identity + Knowledge | D | C | Identity depends on Knowledge (IKS stores identity records) |
| Context Fusion | E | D | Context Fusion depends on Identity |
| Reasoning + Planner | F, G | E | Reasoning depends on Context Fusion; Planner depends on Reasoning |
| Governance | H | F, G | Governance depends on Planner and Context Fusion |
| Executor | I | H, B | Executor depends on Governance and Credential Store |
| Observer | J | I | Observer depends on Executor |
| Learning | K | J, H | Learning depends on Observer and Governance |
| Retirement | M | C | KnowledgeLayer retirement depends on IKS migration |
| Integration | N | A-M | All phases must be complete before integration |
| Release | O | N | Release depends on integration |

### Blocked Work

| Blocked Work | Blocked By | Unblocking Condition |
|-------------|-----------|---------------------|
| Phase D (Identity Engine) | Phase C (Knowledge Engine) | IKS must exist to store identity records |
| Phase E (Context Fusion) | Phase D (Identity Engine) | Identity Engine must exist for identity resolution |
| Phase F (Reasoning Engine) | Phase E (Context Fusion) | Context Fusion must exist to provide workspace context |
| Phase G (Planner Engine) | Phase F (Reasoning Engine) | Reasoning must exist to provide reasoning results |
| Phase H (Governance Engine) | Phase G (Planner Engine), Phase C (Knowledge Engine) | Planner must produce plans; Knowledge must store policies |
| Phase I (Executor Engine) | Phase H (Governance Engine) | Governance must approve plans before execution |
| Phase J (Observer Engine) | Phase I (Executor Engine) | Executor must produce outcomes to observe |
| Phase K (Learning Engine) | Phase J (Observer Engine), Phase H (Governance) | Observer must produce observations; Governance must produce decisions |
| Phase M (KnowledgeLayer Retirement) | Phase C (IKS Migration) | IKS must be fully operational and seeded |

### Verification Milestones

| Milestone | Phase | Trigger | Deliverable |
|-----------|-------|---------|-------------|
| Infrastructure verified | A, B | Infrastructure tests pass | Infrastructure verification report |
| Knowledge foundation verified | C | IKS migration complete (ADR-002 Phase 2) | Migration completion report |
| Identity verified | D | Identity Engine Done | ES-010 verification checklist |
| Context verified | E | Context Fusion Engine Done | ES-009 verification checklist |
| Reasoning verified | F | Reasoning Engine Done | ES-003 verification checklist |
| Planner verified | G | Planner Engine Done | ES-004 verification checklist |
| Governance verified | H | Governance Engine Done | ES-001 verification checklist |
| Execution verified | I | Executor Engine Done | ES-005 verification checklist |
| Observation verified | J | Observer Engine Done | ES-006 verification checklist |
| Learning verified | K | Learning Engine Done | ES-007 verification checklist |
| Doctor verified | (parallel) | Doctor Engine Done | ES-008 verification checklist |
| KnowledgeLayer retired | M | ADR-002 Phase 4 complete | ADR-002 verification checklist |
| Full pipeline verified | N | System tests pass | System test report |
| Architecture checkpoint | N | Zero divergence confirmed | Architecture checkpoint report |
| Production ready | O | Release gate passed | Release sign-off |

### Architecture Checkpoints

| Checkpoint | When | What | Who |
|------------|------|------|-----|
| CP-01 | After Phase C (Knowledge Foundation) | Verify IKS conformance to ES-002 | Chief Software Architect |
| CP-02 | After Phase E (Context Fusion) | Verify context assembly meets System Flow §2 requirements | Chief Software Architect |
| CP-03 | After Phase H (Governance) | Verify Governance Engine constitutional compliance | Chief Constitutional Architect |
| CP-04 | After Phase K (All engines implemented) | Verify all 10 engines conform to specifications | Chief Software Architect |
| CP-05 | After Phase N (Integration) | Verify zero divergence between implementation and frozen architecture | Chief Constitutional Architect |

---

## 15. Program Governance

### Decision Authority

| Decision Type | Authority | Process |
|--------------|-----------|---------|
| Implementation approach within spec | Engineering team | Engineering decision — no ADR required |
| Spec interpretation (within bounds) | Chief Software Architect | Written clarification |
| Spec amendment (minor) | Chief Software Architect | Engineering ADR |
| Spec amendment (constitutional impact) | Chief Constitutional Architect | Constitutional ADR |
| New architectural concept | Chief Constitutional Architect | Constitutional ADR |
| Scope change (within architecture) | Chief Software Architect | Engineering decision |
| Scope change (outside architecture) | Chief Constitutional Architect | Constitutional ADR |
| Phase completion sign-off | Chief Software Architect | Verification checklist review |
| Release approval | Chief Software Architect + Chief Constitutional Architect | Joint sign-off |

### Change Process

1. **Identify change need** — Any engineer may identify a need to change the architecture
2. **Document the divergence** — File an ADR per ADR_TEMPLATE.md
3. **Classify the ADR** — Engineering (Chief Software Architect approves) or Constitutional (Chief Constitutional Architect approves)
4. **Review** — ADR reviewed per governance model
5. **Approve or reject** — Decision documented in the ADR
6. **Implement** — Approved ADR is implemented
7. **Update** — Affected documents updated with ADR reference

### Scope Control

- No change may broaden the scope of the frozen architecture without a constitutional ADR
- Engineering Constitution Article 9 — Scope Discipline — is enforced
- "While we're here" changes are prohibited
- Each directive authorizes a single change

### Issue Escalation

```
Engineer discovers issue
        │
        ▼
Team lead triages
        │
        ├── Can resolve within spec? → Implement
        │
        ├── Requires spec clarification? → Escalate to Chief Software Architect
        │
        ├── Requires ADR? → File Engineering ADR → Chief Software Architect
        │
        └── Constitutional impact? → File Constitutional ADR → Chief Constitutional Architect
```

### Engineering Reviews

| Review Type | Frequency | Participants | Focus |
|-------------|-----------|--------------|-------|
| Sprint review | Every 2 weeks | Engineering team | Feature completion, test results |
| Architecture checkpoint | Per phase | Chief Software Architect | Divergence detection, spec conformance |
| Integration review | Per phase (N only) | All engine owners | Cross-engine contract verification |
| Security review | Per engine | Infrastructure team | Credential handling, tenant isolation, injection |

### Constitutional Reviews

| Review Type | Frequency | Participants | Focus |
|-------------|-----------|--------------|-------|
| Constitutional compliance review | Per phase (CP-03, CP-05) | Chief Constitutional Architect | Invariant enforcement, constitution compliance |
| Architecture divergence review | On ADR filing | Chief Constitutional Architect | ADR classification, constitutional impact |
| Release constitutional sign-off | Per release | Chief Constitutional Architect | Zero divergence certification |

### Verification Authority

The Chief Software Architect is the verification authority for all engineering decisions. The Chief Constitutional Architect is the verification authority for all constitutional decisions. No phase or release is complete without both authorities signing off within their respective domains.

---

## 16. Final Readiness Assessment

### Overall Implementation Readiness

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                     READY FOR IMPLEMENTATION                         ║
║                                                                      ║
║  Architecture Baseline 1.0 — FROZEN                                  ║
║  10 engine specifications — COMPLETE (ES-001 through ES-010)         ║
║  3 infrastructure ADRs — COMPLETE (ADR-001 through ADR-003)          ║
║  26 architectural invariants — FROZEN                                ║
║  Dependency graph — ACYCLIC                                         ║
║  Implementation program — DEFINED (this document)                    ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Remaining Assumptions

| Assumption | Confidence | Validation Trigger |
|-----------|-----------|-------------------|
| Current Contabo VPS can run all 10 engines in-process | Medium | Performance benchmarks in Phase N |
| In-process Event Bus is sufficient for Phase 2 scale | High | Phase 2 is single-instance by architecture |
| Phase 4 (Privacy) eligibility gate interface will be available when Context Fusion integrates | Medium | Phase E depends on external Phase 4 API |
| Channel adapters (WhatsApp, email) can be implemented per ES-005 contract | High | Standard API patterns |
| KnowledgeLayer → IKS migration will not lose data | High | Dry-run + verification report |
| Learning Engine will receive sufficient observations within reasonable time | Medium | Cold start mode handles this |
| All 8 identity types are represented in existing data | Medium | Identity Engine validation will confirm |

### Remaining External Dependencies

| Dependency | Needed By | Status | Risk |
|-----------|-----------|--------|------|
| Phase 4 (Privacy) API | Phase E (Context Fusion) | External | Eligibility gate interface must be available |
| WhatsApp Business API credentials | Phase I (Executor) | External | Requires business account setup |
| Email SMTP/API credentials | Phase I (Executor) | External | Depends on email provider |
| Distributed message broker (future) | Post-Phase 2 | Not needed yet | In-process Event Bus sufficient for Phase 2 |

### Recommended First Engineering Sprint

| Item | Detail |
|------|--------|
| **Goal** | Phase A Sprint 1 — Foundation infrastructure |
| **Deliverables** | DI container, Configuration loader, Persistence layer |
| **Start with** | `app/shunya/di.py` — dependency injection container |
| **Test target** | Infrastructure unit tests pass |
| **Duration** | 2 weeks |
| **Team** | All engineers (foundation is prerequisite for all engine work) |
| **Success criteria** | Application boots from configuration. DI container can instantiate a test service. Database migrations run cleanly. |

### First Implementation Milestone

| Milestone | Phase A Complete |
|-----------|------------------|
| **Criteria** | All Phase A exit criteria met (DI, Config, Persistence, Logging, Metrics, Health) |
| **Estimated completion** | Sprint 2 (4 weeks from program start) |
| **Verification** | Infrastructure tests pass. Full startup sequence verified. |
| **Sign-off** | Chief Software Architect |

### Program Approval Recommendation

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              PROGRAM APPROVED FOR IMPLEMENTATION                     ║
║                                                                      ║
║  The SHUNYA Implementation Program defines the complete engineering  ║
║  execution plan for realizing Architecture Baseline 1.0. The         ║
║  architecture is frozen, the engine specifications are complete,     ║
║  the infrastructure ADRs are specified, and the implementation       ║
║  sequencing is dependency-verified.                                  ║
║                                                                      ║
║  Remaining work is execution only — no architectural discovery.      ║
║                                                                      ║
║  No further architectural expansion is authorized unless approved    ║
║  through the constitutional governance process (ADR per              ║
║  ADR_TEMPLATE.md, approval per SHUNYA_GOVERNANCE_MODEL.md).          ║
║                                                                      ║
║  The architecture is now an input. Implementation begins.            ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

*End of SHUNYA_IMPLEMENTATION_PROGRAM.md*

*Architecture Baseline 1.0 — Frozen*
*Implementation Program — Defined*
*Next: First Engineering Sprint — Phase A: Foundation Infrastructure*