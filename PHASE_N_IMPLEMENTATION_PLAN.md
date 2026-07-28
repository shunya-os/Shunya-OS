# PHASE_N_IMPLEMENTATION_PLAN.md

**Governance Directive:** G13.0 — Phase N Authorization
**Phase:** Integration & Hardening
**Program Reference:** SHUNYA_IMPLEMENTATION_PROGRAM.md §"Phase N: Integration & Hardening"

---

## 1. Authoritative Phase N Specification

| Property | Value |
|----------|-------|
| **Source** | SHUNYA_IMPLEMENTATION_PROGRAM.md (lines 821–831) |
| **Phase Name** | Phase N: Integration & Hardening |
| **Engine** | None — this is a cross-cutting integration phase |
| **Estimated Complexity** | Medium (3–4 sprints) |
| **Risk** | Medium — integration may reveal interface mismatches; performance may require optimization |

### Specification Text (verbatim)

> **Phase N: Integration & Hardening**
>
> | Property | Value |
> |----------|-------|
> | **Objectives** | Full pipeline end-to-end verified. All 10 engines integrated. Constitutional invariants enforced in CI. Performance benchmarks established. |
> | **Deliverables** | Full pipeline integration tests, Performance benchmarks, Constitutional invariant CI checks |
> | **Dependencies** | All phases A–M complete |
> | **Exit criteria** | Full pipeline test passes (External Trigger → Observation → Knowledge Resolution → Context Fusion → Reasoning → Planning → Governance → Execution → Observation → Knowledge Update → Learning → Continuous Improvement). All 14 structural invariants and 12 behavioral invariants verified in CI. Performance within budget (latency p99 for each engine per spec). |

---

## 2. Purpose Within SHUNYA Architecture

Phase N is the **system-level integration** phase. All 10 engines have been implemented in phases D–M as canonical wrappers around the existing codebase. Phase N does not add new engine functionality. It verifies that:

1. The **full pipeline** works end-to-end — an external trigger flows through all engines and returns to a closed loop.
2. All **26 constitutional invariants** (14 structural + 12 behavioral) are enforced in CI.
3. Each engine performs within its **specified latency budget**.
4. **Architecture divergence** is zero — the implementation matches the frozen architecture.

This is the final verification gate before Phase O (Release).

---

## 3. Inputs

### Engine Packages (already implemented)

| Phase | Engine | Canonical Package | ES Spec |
|-------|--------|-------------------|---------|
| D | Identity Engine | `app/shunya/identity/` | ES-010 |
| E | Context Fusion Engine | `app/shunya/context/` | ES-009 |
| F | Reasoning Engine | `app/shunya/reasoning/` | ES-003 |
| G | Planner Engine | `app/shunya/planner/` | ES-004 |
| H | Governance Engine | `app/shunya/governance_engine/` | ES-001 |
| I | Executor Engine | `app/shunya/executor_engine/` | ES-005 |
| J | Observer Engine | `app/shunya/observer_engine/` | ES-006 |
| K | Learning Engine | `app/shunya/learning_engine/` | ES-007 |
| L | Knowledge Engine | `app/shunya/knowledge_engine/` | ES-002 |
| M | Context Fusion (canonical) | `app/shunya/context_fusion_engine/` | ES-009 |

### Infrastructure Packages (from earlier phases)

| Component | Package | Spec |
|-----------|---------|------|
| Event Bus | `app/shunya/infrastructure/event_bus.py` | ADR-001 |
| Credential Store | `app/shunya/infrastructure/credential_store.py` | ADR-003 |
| Configuration | `tests/infrastructure/test_config.py` | INFR-002 |
| Logging | `tests/infrastructure/test_logging.py` | INFR-004 |
| Metrics | `tests/infrastructure/test_metrics.py` | INFR-005 |
| Health | `tests/infrastructure/test_health.py` | INFR-006 |
| Persistence | `tests/infrastructure/test_persistence.py` | INFR-003 |
| DI Container | `tests/infrastructure/test_di.py` | INFR-001 |

### Existing Test Infrastructure

| Category | File(s) |
|----------|---------|
| Engine unit tests | `tests/engines/test_{engine}_engine.py` (10 files) |
| Infrastructure tests | `tests/infrastructure/test_*.py` (7 files) |
| Phase acceptance tests | `tests/test_phase*.py` (~20 files) |
| Characterization tests | `tests/test_characterization.py` |
| Shared conftest | `tests/conftest.py` |

### Integration Matrix (24 integration points)

Defined in SHUNYA_IMPLEMENTATION_PROGRAM.md §7. Each engine pair has:
- **API contract** — the direct call interface
- **Event contract** — events produced/consumed
- **Failure contract** — degraded behaviour when dependency is unavailable
- **Retry policy** — backoff parameters

---

## 4. Outputs

### Deliverable 1: Full Pipeline Integration Test Suite

| Test | Scope | What It Verifies |
|------|-------|-----------------|
| `test_full_pipeline_basic_flow` | Full pipeline | External trigger → Knowledge Resolution → Context Fusion → Reasoning → Planning → Governance → Execution → Observation → Knowledge Update → Learning completes successfully |
| `test_full_pipeline_no_learning` | Full pipeline minus Learning | Pipeline completes correctly when Learning Engine returns no signals (cold start) |
| `test_full_pipeline_degraded_identity` | Full pipeline with degraded Identity | Context Fusion degrades gracefully when Identity Engine unavailable; pipeline continues with degraded context |
| `test_full_pipeline_degraded_knowledge` | Full pipeline with degraded Knowledge | Context Fusion, Reasoning, Governance degrade gracefully when Knowledge Engine unavailable |
| `test_full_pipeline_governance_rejection` | Full pipeline with Governance rejection | Governance rejects a plan; Execution is never called; Observer records the rejection |
| `test_full_pipeline_concurrent_requests` | Full pipeline under concurrency | 10 concurrent pipeline requests all complete without interference, tenant isolation maintained |
| `test_full_pipeline_tenant_isolation` | Cross-tenant full pipeline | Tenant A's pipeline cannot access Tenant B's knowledge, identity, or governance state |
| `test_full_pipeline_error_recovery` | Full pipeline with mid-pipeline failure | Engine failure mid-pipeline (e.g., Reasoning timeout) returns appropriate error; subsequent requests unaffected |

### Deliverable 2: Constitutional Invariant Test Suite

#### 14 Structural Invariants

| # | Invariant | Source | Test Name | Enforcement |
|---|-----------|--------|-----------|-------------|
| S1 | Evidence is immutable | Core Models §11 — Invariant 1 | `test_invariant_evidence_immutable` | Knowledge Engine creates new version on update; original preserved |
| S2 | Knowledge is versioned | Core Models §11 — Invariant 2 | `test_invariant_knowledge_versioned` | Every fact mutation creates new version with monotonic counter |
| S3 | Governance precedes execution | Core Models §11 — Invariant 3 | `test_invariant_governance_before_execution` | Executor refuses execution without Governance APPROVE verdict |
| S4 | Reasoning never executes | Core Models §11 — Invariant 4 | `test_invariant_reasoning_never_executes` | Reasoning Engine has no channel adapters, no execution imports |
| S5 | Executor never reasons | Core Models §11 — Invariant 5 | `test_invariant_executor_never_reasons` | Executor Engine has no reasoning strategies, no inference imports |
| S6 | Observer never governs | Core Models §11 — Invariant 6 | `test_invariant_observer_never_governs` | Observer Engine has no policy evaluation, no governance imports |
| S7 | Learning never mutates evidence | Core Models §11 — Invariant 7 | `test_invariant_learning_never_mutates_evidence` | Learning Engine produces proposals, never writes evidence |
| S8 | Identity is globally unique within a tenant | Core Models §11 — Invariant 8 | `test_invariant_identity_globally_unique` | Identity Engine rejects duplicate normalized value per tenant |
| S9 | Tenant isolation is mandatory | Core Models §11 — Invariant 9 | `test_invariant_tenant_isolation` | All engines scope reads/writes by tenant_id; cross-tenant access returns error |
| S10 | Audit trails are append-only | Core Models §11 — Invariant 10 | `test_invariant_audit_append_only` | Governance and Observer logs are append-only; no DELETE or UPDATE |
| S11 | Confidence is always explicit | Core Models §11 — Invariant 11 | `test_invariant_confidence_explicit` | Every engine output carrying a decision includes confidence in [0.0, 1.0] |
| S12 | Provenance is always present | Core Models §11 — Invariant 12 | `test_invariant_provenance_present` | Every knowledge fact, observation, and identity record traces to origin |
| S13 | Events use canonical envelope | Core Models §11 — Invariant 13 | `test_invariant_event_canonical_envelope` | All events conform to Event Bus schema (event_type, source, payload, timestamp, tenant_id, correlation_id) |
| S14 | Dependency graph is acyclic | Core Models §11 — Invariant 14 | `test_invariant_dependency_graph_acyclic` | Static analysis of import graph across all engine packages |

#### 12 Behavioral Invariants

| # | Invariant | Source | Test Name | Enforcement |
|---|-----------|--------|-----------|-------------|
| B1 | Every execution follows governance | Core Models §B1 | `test_invariant_execution_follows_governance` | Executor checks Governance verdict before every action |
| B2 | Every decision is explainable | Core Models §B2 | `test_invariant_decision_explainable` | Reasoning, Governance, Learning outputs include explanation field |
| B3 | Evidence precedes learning | Core Models §B3 | `test_invariant_evidence_precedes_learning` | Learning Engine refuses to learn without evidence-grounded observations |
| B4 | Learning never bypasses governance | Core Models §B4 | `test_invariant_learning_no_bypass_governance` | Learning proposals must pass through Governance before knowledge update |
| B5 | Observation is continuous | Core Models §B5 | `test_invariant_observation_continuous` | Observer Engine records every execution outcome, including failures |
| B6 | Execution is observable | Core Models §B6 | `test_invariant_execution_observable` | Executor emits execution events for every action (success and failure) |
| B7 | No engine communicates outside contracts | Core Models §B7 | `test_invariant_no_contract_violation` | Engines communicate only through defined API/event contracts |
| B8 | No direct state mutation across engines | Core Models §B8 | `test_invariant_no_direct_state_mutation` | Engines cannot write to another engine's data store directly |
| B9 | Every workflow is recoverable | Core Models §B9 | `test_invariant_workflow_recoverable` | Mid-pipeline failure allows retry from last committed checkpoint |
| B10 | Every workflow is auditable | Core Models §B10 | `test_invariant_workflow_auditable` | Every pipeline execution produces an audit trail |
| B11 | Human review is time-boxed | Core Models §B11 | `test_invariant_human_review_timeboxed` | Governance flags pending human review that exceeds configured TTL |
| B12 | Degradation is explicit | Core Models §B12 | `test_invariant_degradation_explicit` | When an engine degrades (e.g., dependency unavailable), it documents the degradation |

### Deliverable 3: Performance Benchmarks

| Benchmark | Engine | Target (p50) | Target (p99) | Test Name |
|-----------|--------|-------------|-------------|-----------|
| Identity resolution | ES-010 | < 10ms | < 50ms | `bench_identity_resolution` |
| Knowledge fact retrieval | ES-002 | < 10ms | < 50ms | `bench_knowledge_retrieval` |
| Context assembly | ES-009 | < 100ms | < 500ms | `bench_context_assembly` |
| Reasoning | ES-003 | < 100ms | < 500ms | `bench_reasoning` |
| Plan generation | ES-004 | < 50ms | < 200ms | `bench_plan_generation` |
| Governance validation | ES-001 | < 50ms | < 200ms | `bench_governance_validation` |
| Execution (in-process) | ES-005 | < 100ms | < 500ms | `bench_execution` |
| Observation recording | ES-006 | < 50ms | < 200ms | `bench_observation` |
| Learning | ES-007 | < 200ms | < 1s | `bench_learning` |
| Doctor checks | ES-008 | < 200ms | < 1s | `bench_doctor` |
| **Full pipeline** | All | < 1s | < 3s | `bench_full_pipeline` |

### Deliverable 4: CI Configuration

Constitutional invariant tests must run on every commit. Full pipeline integration tests run on merge to develop. Performance benchmarks run weekly or per release candidate.

---

## 5. Dependencies

### Completed Phases (all dependencies met)

| Phase | Engine | Status | Evidence |
|-------|--------|--------|----------|
| A–C | Infrastructure | ✅ Complete | Event Bus, Config, DI, Logging, Metrics, Health tests exist |
| D | Identity Engine (ES-010) | ✅ Complete | `app/shunya/identity/`, test_identity_engine.py |
| E | Context Fusion Engine (ES-009) | ✅ Complete | `app/shunya/context/`, test_context_fusion.py |
| F | Reasoning Engine (ES-003) | ✅ Complete | `app/shunya/reasoning/`, test_reasoning_engine.py |
| G | Planner Engine (ES-004) | ✅ Complete | `app/shunya/planner/`, test_planner_engine.py |
| H | Governance Engine (ES-001) | ✅ Complete | `app/shunya/governance_engine/`, test_governance_engine.py |
| I | Executor Engine (ES-005) | ✅ Complete | `app/shunya/executor_engine/`, test_executor_engine.py |
| J | Observer Engine (ES-006) | ✅ Complete | `app/shunya/observer_engine/`, test_observer_engine.py |
| K | Learning Engine (ES-007) | ✅ Complete | `app/shunya/learning_engine/`, test_learning_engine.py |
| L | Knowledge Engine (ES-002) | ✅ Complete | `app/shunya/knowledge_engine/`, test_knowledge_engine.py |
| M | Context Fusion canonical (ES-009) | ✅ Complete | `app/shunya/context_fusion_engine/`, test_context_fusion_engine.py |

### No External Dependencies

Phase N depends only on the completed engine and infrastructure packages. No external API calls, third-party libraries, or infrastructure provisioning is required.

---

## 6. Engine Boundaries

Phase N is **not an engine**. It does not own:
- Any data store
- Any state machine
- Any public API consumed by other engines
- Any event production/consumption as an engine

Phase N owns the **integration verification layer**:
| Responsibility | Owner | Evidence |
|---------------|-------|----------|
| Full pipeline integration test | Phase N | `tests/integration/test_full_pipeline.py` |
| Constitutional invariant test suite | Phase N | `tests/constitutional/` |
| Performance benchmark suite | Phase N | `tests/benchmarks/` |
| CI configuration for invariant enforcement | Phase N | CI pipeline config |

No existing engine is modified by Phase N. All changes are additive test infrastructure.

---

## 7. Public Interfaces

Phase N does not expose any new public API consumed by engines. The interfaces it verifies are the existing engine-to-engine contracts from §7 of the implementation program:

| Caller | Callee | API Contract | Event Contract |
|--------|--------|-------------|---------------|
| Context Fusion | Identity | `IdentityEngine.resolve(claim)` | `identity.resolved` |
| Context Fusion | Knowledge | `IKStore.get_fact()`, `IKStore.search_facts()` | `knowledge.fact.created`, `knowledge.fact.superseded` |
| Reasoning | Context Fusion | `ContextFusionEngine.assemble(request)` | `context.fusion.completed` |
| Reasoning | Knowledge | `IKStore.get_fact()`, `IKStore.search_facts()` | `knowledge.fact.created`, `knowledge.fact.superseded` |
| Planner | Reasoning | `ReasoningEngine.reason(context)` | `reasoning.completed` |
| Planner | Knowledge | `IKStore.get_fact()`, `IKStore.search_facts()` | (none — read-only) |
| Planner | Context Fusion | `ContextFusionEngine.assemble(request)` | `context.fusion.completed` |
| Governance | Planner | `GovernanceEngine.validate(plan, context)` | `plan.created` |
| Governance | Knowledge | `IKStore.get_fact()` (policy definitions) | `policy.registry.updated` |
| Governance | Context Fusion | `ContextFusionEngine.assemble(request)` | `context.fusion.completed` |
| Executor | Governance | `GovernanceEngine.validate(plan, context)` | `governance.action.approved` |
| Executor | Credential Store | `CredentialStore.resolve(ref, tenant, purpose, actor)` | (none — synchronous) |
| Executor | Context Fusion | `ContextFusionEngine.assemble(request)` | `context.fusion.completed` |
| Observer | Executor | (none — event-driven) | `execution.completed`, `execution.failed` |
| Observer | Knowledge | `IKStore.set_fact()` | `observation.recorded` |
| Observer | Context Fusion | `ContextFusionEngine.assemble(request)` | `context.fusion.completed` |
| Learning | Observer | (none — event-driven) | `observation.recorded`, `observation.discrepancy.detected` |
| Learning | Knowledge | `IKStore.set_fact()` | `learning.signal.generated` |
| Learning | Governance | (none — event-driven) | `governance.decision.logged` |
| Learning | Context Fusion | `ContextFusionEngine.assemble(request)` | `context.fusion.completed` |
| Doctor | All engines | Health API (read) | `doctor.check.completed`, `doctor.violation.detected` |
| Doctor | Knowledge | Integrity API (read) | `knowledge.integrity.violation` |
| Doctor | Governance | Audit Log API (read) | `governance.decision.logged` |

---

## 8. Success Criteria

### Exit Criteria (from specification)

| # | Criterion | Verification Method |
|---|-----------|-------------------|
| 1 | Full pipeline test passes | `tests/integration/test_full_pipeline.py` — all test cases green |
| 2 | All 14 structural invariants verified in CI | `tests/constitutional/test_structural_invariants.py` — all tests green |
| 3 | All 12 behavioral invariants verified in CI | `tests/constitutional/test_behavioral_invariants.py` — all tests green |
| 4 | Performance within budget per engine spec | `tests/benchmarks/` — all benchmarks meet p50/p99 targets |
| 5 | Zero regressions on existing test suite | Full test suite (all engine tests + infrastructure tests + phase tests) passes without regressions |
| 6 | Zero divergence between implementation and frozen architecture | Architecture checkpoint (CP-05) verified by Chief Constitutional Architect |

### Completion Criteria (per G13.0)

- [x] Implementation matches the authoritative specification (this plan documents it)
- [ ] All newly added integration tests pass
- [ ] Existing regression suite remains green
- [ ] Independent verification succeeds
- [ ] Documentation is complete

---

## 9. File Structure (to be created)

```
tests/
├── integration/
│   ├── __init__.py
│   ├── conftest.py                    — Shared fixtures for pipeline tests
│   ├── test_full_pipeline.py          — 8 pipeline integration tests (basic flow, degraded modes, rejection, concurrency, tenant isolation, error recovery)
│   └── test_engine_pair_integration.py — 24 pairwise engine integration tests (one per integration matrix row)
├── constitutional/
│   ├── __init__.py
│   ├── conftest.py                    — Shared fixtures for invariant tests
│   ├── test_structural_invariants.py  — 14 structural invariant tests (S1–S14)
│   └── test_behavioral_invariants.py  — 12 behavioral invariant tests (B1–B12)
└── benchmarks/
    ├── __init__.py
    ├── conftest.py                    — Benchmark timing fixtures
    ├── test_engine_benchmarks.py      — Per-engine latency benchmarks (10 engines)
    └── test_pipeline_benchmark.py     — Full pipeline end-to-end latency
```

No existing files are modified. All changes are additive.

---

## 10. Verification Strategy

### Phase N Self-Verification

| Check | How Verified |
|-------|-------------|
| Integration tests use real engine implementations | No mocks at engine boundary; only external channels mocked |
| All 24 engine pairs from integration matrix covered | One test per matrix row |
| Each invariant has a dedicated test case | 26 test methods, one per invariant |
| Benchmarks measure wall-clock time with warmup | Minimum 100 iterations per benchmark, first 10 discarded as warmup |
| Zero regressions | `python3 -m pytest tests/ -q --tb=short` passes before acceptance |

### Independence from Engine Implementation

All Phase N tests are integration/constitutional tests — they exercise engines through their public contracts, never through internal implementation details. This guarantees that Phase N tests remain valid even if an engine is refactored internally, as long as its public API and behavioral contracts are preserved.

---

**Plan complete. Awaiting governance approval to begin implementation.**