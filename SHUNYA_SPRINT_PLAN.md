# SHUNYA Sprint Plan

**Authority:** SHUNYA_IMPLEMENTATION_PROGRAM.md
**Date:** 2026-07-18
**Status:** Active
**Sprint cadence:** 2 weeks
**Sprint count:** 42

---

## Sprint Block 1: Foundation + Infrastructure (Sprints 1–5, 10 weeks)

---

### Sprint 1

| Field | Value |
|-------|-------|
| **Objectives** | Establish shared infrastructure foundation. DI container and configuration loading operational. |
| **Stories** | |
| | S1.1 — Implement `app/shunya/di.py` with singleton and factory registration (INFR-001) |
| | S1.2 — Implement `app/shunya/config.py` with YAML loading, schema validation, env override (INFR-002) |
| **Deliverables** | `app/shunya/di.py`, `app/shunya/config.py`, `config.yaml` |
| **Verification** | DI container instantiates a service with dependencies. Singleton returns same instance. Config loads from YAML. Env override applies. Invalid config raises error. |
| **Definition of Done** | DI unit tests pass (5). Config unit tests pass (8). All tests pass in CI. Code reviewed. |

### Sprint 2

| Field | Value |
|-------|-------|
| **Objectives** | Persistence layer and structured logging operational. |
| **Stories** | |
| | S2.1 — Implement `app/shunya/infrastructure/persistence.py` with SQLAlchemy session factory, connection pooling, Alembic migration runner (INFR-003) |
| | S2.2 — Implement `app/shunya/infrastructure/logging.py` with JSON output, configurable levels, privacy filters, correlation_id propagation (INFR-004) |
| **Deliverables** | `app/shunya/infrastructure/persistence.py`, `app/shunya/infrastructure/logging.py`, Alembic configuration, initial migration |
| **Verification** | DB session creates valid connections. Connection pooling respects pool size. Alembic migrations run up/down. JSON log output at configured level. Correlation_id propagates. Privacy filter strips PII. |
| **Definition of Done** | Persistence unit tests pass (6). Logging unit tests pass (5). Migration test passes. All tests pass in CI. Code reviewed. |

### Sprint 3

| Field | Value |
|-------|-------|
| **Objectives** | Metrics collection and health endpoint operational. |
| **Stories** | |
| | S3.1 — Implement `app/shunya/infrastructure/metrics.py` with Prometheus counters, histograms, gauges, per-engine namespacing (INFR-005) |
| | S3.2 — Implement `app/shunya/infrastructure/health.py` with health registry and aggregated endpoint (INFR-006) |
| **Deliverables** | `app/shunya/infrastructure/metrics.py`, `app/shunya/infrastructure/health.py` |
| **Verification** | Metrics endpoint returns Prometheus output. Counter increments. Histogram records. Per-engine namespaces separated. Health endpoint returns status per component. Degraded component reflected. |
| **Definition of Done** | Metrics unit tests pass (5). Health unit tests pass (4). All tests pass in CI. Code reviewed. Phase A exit criteria met. |

### Sprint 4

| Field | Value |
|-------|-------|
| **Objectives** | Event Bus core implementation and credential store core implementation. |
| **Stories** | |
| | S4.1 — Implement `EventBus` singleton: `publish()`, `subscribe()`, `unsubscribe()`, in-process queue delivery (INFR-007) |
| | S4.2 — Implement `CredentialStore` core: `resolve()`, `store()`, `revoke()`, `list()`, AES-256-GCM encryption, credential_metadata table (INFR-012) |
| **Deliverables** | `app/shunya/infrastructure/event_bus.py`, `app/shunya/infrastructure/credential_store.py`, credential_metadata migration |
| **Verification** | Events delivered to matching subscribers. Unsubscribe works. Credential stored and resolved. Encrypted at rest. |
| **Definition of Done** | Event Bus unit tests pass (10). Credential Store unit tests pass (10). All tests pass in CI. Code reviewed. |

### Sprint 5

| Field | Value |
|-------|-------|
| **Objectives** | Event Bus delivery guarantees, security, health. Credential Store security and Phase 4 gate. |
| **Stories** | |
| | S5.1 — Implement at-least-once delivery, idempotency cache, per-producer ordering, consumer timeout (INFR-008) |
| | S5.2 — Implement retry policy (3 attempts, exponential backoff), dead-letter queue, manual replay (INFR-009) |
| | S5.3 — Implement tenant isolation, publisher authentication, canonical envelope validation (INFR-010) |
| | S5.4 — Implement Event Bus health endpoint (INFR-011) |
| | S5.5 — Implement Credential Store caller authentication, tenant isolation, audit logging, expiry, revocation (INFR-013) |
| | S5.6 — Implement Credential Store Phase 4 eligibility gate integration (INFR-014) |
| **Deliverables** | Event Bus delivery guarantees. Event Bus retry/DLQ. Event Bus security. Event Bus health. Credential Store security. Credential Store Phase 4 gate. |
| **Verification** | At-least-once delivery verified. Idempotency deduplicates within TTL. Retry with backoff. Dead-letter queue operational. Tenant isolation enforced. Invalid envelope rejected. Credential expiry enforced. Phase 4 gate integrated. |
| **Definition of Done** | Event Bus unit tests: 8 (delivery) + 6 (retry) + 6 (security) + 3 (health) = 23. Credential Store tests: 8 (security) + 4 (Phase 4) = 12. All tests pass in CI. Code reviewed. Phase B exit criteria met. |

---

## Sprint Block 2: Core Knowledge + Identity + Context (Sprints 6–12, 14 weeks)

---

### Sprint 6

| Field | Value |
|-------|-------|
| **Objectives** | Immutable Knowledge Store core operational. Identity normalizer implemented. |
| **Stories** | |
| | S6.1 — Implement IKS fact operations: `set_fact()`, `get_fact()`, `get_fact_history()`, `search_facts()`, versioning through supersession (IKS-001) |
| | S6.2 — Implement identity normalizer: email, phone, channel, document, external, alias normalization (IDEN-001) |
| **Deliverables** | `app/shunya/knowledge/immutable_store.py`, `app/shunya/identity/normalizer.py`, knowledge_facts migration |
| **Verification** | IKS: fact created, retrieved, versioned. Supersession creates new version. Normalizer: all 8 types normalized correctly. Invalid values rejected. |
| **Definition of Done** | IKS unit tests pass (12). Normalizer unit tests pass (10). All tests pass in CI. Code reviewed. |

### Sprint 7

| Field | Value |
|-------|-------|
| **Objectives** | IKS lifecycle and invariants enforced. Identity resolution engine implemented. |
| **Stories** | |
| | S7.1 — Implement IKS fact lifecycle (Observed → Verified → Trusted → Superseded → Archived → Retired). Enforce no in-place updates, no deletions (IKS-002) |
| | S7.2 — Implement identity resolution engine: `resolve(claim)` → MATCHED/NO_MATCH/AMBIGUOUS, lookup by normalized value + tenant_id (IDEN-002) |
| **Deliverables** | IKS lifecycle. Identity resolution engine (`app/shunya/identity/engine.py`). |
| **Verification** | IKS lifecycle transitions work. No in-place update possible. Identity: single match → MATCHED. No match → NO_MATCH. Multiple → AMBIGUOUS. Deterministic. |
| **Definition of Done** | IKS lifecycle tests pass (6). Identity resolution tests pass (12). All tests pass in CI. Code reviewed. |

### Sprint 8

| Field | Value |
|-------|-------|
| **Objectives** | Identity registration, state machine, tenant isolation, events. KnowledgeEngine facade implemented. |
| **Stories** | |
| | S8.1 — Implement identity registration (IDEN-003) |
| | S8.2 — Implement identity lifecycle state machine: `verify()`, `supersede()`, `merge()` (IDEN-004) |
| | S8.3 — Implement identity tenant isolation (IDEN-005) |
| | S8.4 — Implement identity events: `identity.resolved`, `identity.ambiguous`, `identity.registered`, `identity.superseded`, `identity.merged`, `identity.verified` (IDEN-006) |
| | S8.5 — Implement KnowledgeEngine facade wrapping IKS + KnowledgeLayer (IKS-003) |
| **Deliverables** | Identity registration, state machine, tenant isolation, events. `app/shunya/knowledge/engine.py`. |
| **Verification** | Identity: registration creates records. All 7 state transitions work. Tenant isolation enforced. Events published on correct triggers. KnowledgeEngine: IKS primary, KnowledgeLayer fallback. |
| **Definition of Done** | Identity tests: 6 (registration) + 10 (state machine) + 4 (isolation) + 6 (events) = 26. KnowledgeEngine tests: 8. All tests pass in CI. Code reviewed. Phase D exit criteria met. |

### Sprint 9

| Field | Value |
|-------|-------|
| **Objectives** | Migration script reads KnowledgeLayer data. KnowledgeLayer legacy wrapper implemented. |
| **Stories** | |
| | S9.1 — Move KnowledgeLayer to `app/shunya/legacy/knowledge_layer.py` with adapter methods (IKS-004) |
| | S9.2 — Implement migration script: read all KnowledgeLayer destinations, parse into IKS fact keys per ADR-002 mapping (IKS-005) |
| **Deliverables** | `app/shunya/legacy/knowledge_layer.py`, `scripts/migrate_knowledge_layer.py` |
| **Verification** | All 5 existing call sites function through legacy wrapper. Migration script reads all destinations. Fact key mapping correct (11 mappings verified). |
| **Definition of Done** | Legacy wrapper tests pass (3). Migration script unit tests pass (6). All tests pass in CI. Code reviewed. |

### Sprint 10

| Field | Value |
|-------|-------|
| **Objectives** | Migration script seeds IKS. Verification report produced. Fallback verified. |
| **Stories** | |
| | S10.1 — Implement IKS seeding: create KnowledgeFact per destination field, confidence=0.7, status=active, version=1 (IKS-006) |
| | S10.2 — Implement verification report: compare counts, log failures, random sample verification (IKS-007) |
| | S10.3 — Verify facade fallback: unmigrated keys fall back to KnowledgeLayer, migrated keys return from IKS (IKS-008) |
| **Deliverables** | Seeded IKS. Migration report. Fallback verification. |
| **Verification** | All destinations written to IKS. Zero failures. Report confirms 100% coverage. Fallback works correctly. |
| **Definition of Done** | Seed tests pass (5). Report tests pass (3). Fallback tests pass (4). All tests pass in CI. Code reviewed. Phase C exit criteria met. |

### Sprint 11

| Field | Value |
|-------|-------|
| **Objectives** | Context Fusion: request handling, identity source provider, knowledge source provider. |
| **Stories** | |
| | S11.1 — Implement context request handler: `assemble(request)`, validate required fields, timeout, budget (CTX-001) |
| | S11.2 — Implement identity source provider: call IdentityEngine.resolve() for actor and subject, handle MATCHED/NO_MATCH/AMBIGUOUS (CTX-002) |
| | S11.3 — Implement knowledge source provider: read memory, evidence, documents from KnowledgeEngine, scope by tenant/workspace (CTX-003) |
| **Deliverables** | `app/shunya/context/engine.py`, `app/shunya/context/providers.py` |
| **Verification** | Request validated. Identity provider returns resolved identity. Knowledge provider returns facts. Source provider timeout returns degraded section. |
| **Definition of Done** | Context request tests pass (6). Identity provider tests pass (5). Knowledge provider tests pass (5). All tests pass in CI. Code reviewed. |

### Sprint 12

| Field | Value |
|-------|-------|
| **Objectives** | Context Fusion: eligibility gates, budget enforcement, fingerprint, assembly, state machine. |
| **Stories** | |
| | S12.1 — Implement Phase 4 eligibility gate: `check(purpose_code, section)` → allowed/denied, safe failure on gate unavailable (CTX-004) |
| | S12.2 — Implement budget enforcement: track item count and size, truncate lowest-confidence items first (CTX-005) |
| | S12.3 — Implement fingerprint computation: cryptographic hash of serialized context (CTX-006) |
| | S12.4 — Implement WorkspaceContext assembly and delivery (CTX-007) |
| | S12.5 — Implement Context Fusion state machine (9 transitions) (CTX-008) |
| **Deliverables** | Complete Context Fusion Engine. |
| **Verification** | Eligibility gate allows/denies correctly. Budget enforcement truncates over-limit context. Fingerprint computed. WorkspaceContext contains all required fields. State machine transitions correct. |
| **Definition of Done** | Eligibility tests pass (5). Budget tests pass (4). Fingerprint tests pass (2). Assembly tests pass (6). State machine tests pass (9). All tests pass in CI. Code reviewed. Phase E exit criteria met. |

---

## Sprint Block 3: Pipeline Engines 1 — Reasoning → Planner → Governance (Sprints 13–25, 26 weeks)

---

### Sprint 13

| Field | Value |
|-------|-------|
| **Objectives** | Reasoning Engine: context consumption and evidence chain building. |
| **Stories** | |
| | S13.1 — Implement context consumption: `reason(request)` calls ContextFusionEngine.assemble(), handle degraded and error context (REAS-001) |
| | S13.2 — Implement evidence chain building: link each claim to source facts, populate evidence fields (weight, quality, confidence) (REAS-002) |
| **Deliverables** | `app/shunya/reasoning/engine.py` |
| **Verification** | Context consumed correctly. Degraded context produces lower confidence. Evidence chain produced for each reasoning output. Empty evidence chain handled. |
| **Definition of Done** | Context consumption tests pass (4). Evidence chain tests pass (8). All tests pass in CI. Code reviewed. |

### Sprint 14

| Field | Value |
|-------|-------|
| **Objectives** | Reasoning Engine: confidence scoring and reasoning strategies (part 1). |
| **Stories** | |
| | S14.1 — Implement canonical confidence scoring: propagation, combination, decay per Core Models §7 (REAS-003) |
| | S14.2 — Implement reasoning strategies: deductive, inductive, abductive, analogical, causal (5 of 10 types) (REAS-004 — part 1) |
| **Deliverables** | Confidence scoring. 5 reasoning strategies. |
| **Verification** | Confidence scores canonical (0.0–1.0). Propagation correct. Combination correct. Decay correct. 5 reasoning strategies produce valid ReasoningResult. |
| **Definition of Done** | Confidence scoring tests pass (8). Strategy tests pass (10). All tests pass in CI. Code reviewed. |

### Sprint 15

| Field | Value |
|-------|-------|
| **Objectives** | Reasoning Engine: remaining strategies and state machine. |
| **Stories** | |
| | S15.1 — Implement remaining reasoning strategies: temporal, compositional, counterfactual, evaluative, comparative (5 of 10 types) (REAS-004 — part 2) |
| | S15.2 — Implement reasoning state machine (7 transitions) (REAS-005) |
| **Deliverables** | All 10 reasoning strategies. Reasoning state machine. |
| **Verification** | All 10 reasoning types produce ReasoningResult with decision, confidence, evidence_chain, explanation, alternatives, risk_flags. Insufficient context → low-confidence result. State machine transitions correct. |
| **Definition of Done** | Strategy tests pass (20 total). State machine tests pass (7). All tests pass in CI. Code reviewed. Phase F exit criteria met. |

### Sprint 16

| Field | Value |
|-------|-------|
| **Objectives** | Planner Engine: plan generation and templates. |
| **Stories** | |
| | S16.1 — Implement plan generation: `plan(reasoning_result, context)` → Plan with sequenced steps, dependencies, timelines, cost estimates, alternatives (PLAN-001) |
| | S16.2 — Implement plan templates: message_send, record_create, api_call, financial_transaction, multi_step_workflow (PLAN-002) |
| **Deliverables** | `app/shunya/planner/engine.py` |
| **Verification** | Plan produced from reasoning result. Steps sequenced. Dependencies correct. Timeline computed. Cost estimates produced. Alternatives included. All 5 template types produce valid PlanObject. |
| **Definition of Done** | Plan generation tests pass (10). Template tests pass (10). All tests pass in CI. Code reviewed. |

### Sprint 17

| Field | Value |
|-------|-------|
| **Objectives** | Planner Engine: state machine. Governance Engine: policy registry. |
| **Stories** | |
| | S17.1 — Implement planner state machine (5 transitions) (PLAN-003) |
| | S17.2 — Implement policy registry: `register_policy()`, `get_policy()`, `list_policies()`, `remove_policy()`, tenant-scoped + GLOBAL policies (GOV-001) |
| **Deliverables** | Planner state machine. `app/shunya/governance/engine.py` (policy registry). |
| **Verification** | Planner state machine transitions correct. Policy registry: policies stored and retrievable. Tenant isolation enforced. Unknown policy handled gracefully. |
| **Definition of Done** | Planner state machine tests pass (5). Policy registry tests pass (8). All tests pass in CI. Code reviewed. Phase G exit criteria met. |

### Sprint 18

| Field | Value |
|-------|-------|
| **Objectives** | Governance Engine: plan validation and constitutional policy evaluation. |
| **Stories** | |
| | S18.1 — Implement plan validation: validate plan structure against Governance input contract (GOV-002) |
| | S18.2 — Implement constitutional policy evaluation: map all 10 constitutional principles to evaluable policies (GOV-003) |
| **Deliverables** | Plan validation. Constitutional policies. |
| **Verification** | Valid plan accepted. Missing fields rejected. All 10 constitutional principles evaluable. Each returns pass/fail/warning with explanation. |
| **Definition of Done** | Plan validation tests pass (6). Constitutional policy tests pass (15). All tests pass in CI. Code reviewed. |

### Sprint 19

| Field | Value |
|-------|-------|
| **Objectives** | Governance Engine: business policy evaluation and risk assessment. |
| **Stories** | |
| | S19.1 — Implement business policy evaluation: domain-specific policies, risk threshold policies, action-type policies, policy conflict detection (GOV-004) |
| | S19.2 — Implement risk assessment: compute risk score, low → APPROVE, medium → REVIEW, high → REJECT (GOV-005) |
| **Deliverables** | Business policies. Risk assessment. |
| **Verification** | Domain policies scoped correctly. Risk thresholds enforced. Policy conflict detected (→ REVIEW). Risk score computed correctly. |
| **Definition of Done** | Business policy tests pass (10). Risk assessment tests pass (5). All tests pass in CI. Code reviewed. |

### Sprint 20

| Field | Value |
|-------|-------|
| **Objectives** | Governance Engine: verdict production and immutable audit trail. |
| **Stories** | |
| | S20.1 — Implement governance verdict production: GovernanceVerdict with all required fields (GOV-006) |
| | S20.2 — Implement immutable audit trail: append-only, all required fields, frozen context snapshot (GOV-007) |
| **Deliverables** | Verdict production. Audit trail. |
| **Verification** | APPROVE/REVIEW/REJECT produced correctly. All verdict fields populated. Context snapshot frozen at decision time. Audit trail append-only. Historical records unaffected by policy changes. |
| **Definition of Done** | Verdict tests pass (6). Audit trail tests pass (5). All tests pass in CI. Code reviewed. |

### Sprint 21

| Field | Value |
|-------|-------|
| **Objectives** | Governance Engine: state machine. Doctor Engine: integrity checks and package health (parallel). |
| **Stories** | |
| | S21.1 — Implement governance state machine (14 transitions) (GOV-008) |
| | S21.2 — Implement Doctor integrity checks: package existence, file existence, DB table presence, module importability (DOC-001) |
| | S21.3 — Implement Doctor package health validation: version match, vulnerability check, dependency declaration match (DOC-003) |
| **Deliverables** | Governance state machine. `app/shunya/doctor/engine.py` (integrity checks, package health). |
| **Verification** | Governance: 14 state transitions correct. Invalid transitions raise error. Doctor: integrity checks pass/fail correctly. Package health detects version mismatch. |
| **Definition of Done** | Governance state machine tests pass (14). Doctor integrity tests pass (5). Doctor package health tests pass (4). All tests pass in CI. Code reviewed. Phase H exit criteria met. |

### Sprint 22

| Field | Value |
|-------|-------|
| **Objectives** | Executor Engine: channel adapters (WhatsApp, Telegram, Email, API) — part 1. |
| **Stories** | |
| | S22.1 — Implement WhatsApp channel adapter: send message, resolve credentials, delivery confirmation, retry (EXEC-001) |
| | S22.2 — Implement Telegram channel adapter: send message, resolve credentials, delivery confirmation, retry (EXEC-002) |
| **Deliverables** | `app/shunya/executor/adapters/whatsapp.py`, `app/shunya/executor/adapters/telegram.py` |
| **Verification** | WhatsApp: message sent, credential resolved and discarded, delivery confirmed. Telegram: same pattern. |
| **Definition of Done** | WhatsApp tests pass (8). Telegram tests pass (6). All tests pass in CI. Code reviewed. |

### Sprint 23

| Field | Value |
|-------|-------|
| **Objectives** | Executor Engine: channel adapters (Email, API). Doctor Engine: architecture drift, compliance, health aggregation. |
| **Stories** | |
| | S23.1 — Implement Email channel adapter: SMTP and API modes, HTML and plaintext, delivery reports (EXEC-003) |
| | S23.2 — Implement Generic API channel adapter: HTTP methods, auth types, timeout, retry (EXEC-004) |
| | S23.3 — Implement Doctor architecture drift detection: engine modules, layer boundaries, event subscriptions, event publications (DOC-002) |
| | S23.4 — Implement Doctor compliance verification: Governance decisions, audit trail completeness, constitutional policy evaluation (DOC-004) |
| **Deliverables** | `app/shunya/executor/adapters/email.py`, `app/shunya/executor/adapters/api.py`. Doctor drift detection, compliance checks. |
| **Verification** | Email sent via SMTP and API. API adapter supports all HTTP methods and auth types. Doctor: drift detection flags missing modules. Compliance detection flags missing governance. |
| **Definition of Done** | Email tests pass (6). API tests pass (8). Doctor drift tests pass (6). Doctor compliance tests pass (4). All tests pass in CI. Code reviewed. |

### Sprint 24

| Field | Value |
|-------|-------|
| **Objectives** | Executor Engine: task dispatch and failure handling. |
| **Stories** | |
| | S24.1 — Implement execution task dispatch: `execute(approved_plan, verdict, context)` → DeliveryResult, resolve credentials, dispatch to correct adapter, collect results (EXEC-005) |
| | S24.2 — Implement execution failure handling: retry with backoff, fallback to alternative channel, partial delivery reporting, credential failure isolation, timeout (EXEC-006) |
| **Deliverables** | `app/shunya/executor/engine.py`. Execution failure handling. |
| **Verification** | Plan dispatched to correct adapter. Credentials resolved and discarded. Retry on transient failure. Fallback on persistent failure. Partial delivery reported. Credential failure isolated to one task. |
| **Definition of Done** | Task dispatch tests pass (10). Failure handling tests pass (6). All tests pass in CI. Code reviewed. |

### Sprint 25

| Field | Value |
|-------|-------|
| **Objectives** | Executor Engine: state machine. Doctor Engine: health aggregation, report, events. |
| **Stories** | |
| | S25.1 — Implement executor state machine (8 transitions) (EXEC-007) |
| | S25.2 — Implement Doctor health aggregation: collect health from all engines, aggregate, degrade after 3 missing reports (DOC-005) |
| | S25.3 — Implement DoctorReport assembly and events: `doctor.check.completed`, `doctor.violation.detected` (DOC-006) |
| **Deliverables** | Executor state machine. Complete Doctor Engine. |
| **Verification** | Executor: 8 state transitions correct. Doctor: health aggregation from all engines. DoctorReport contains all check results. Events published correctly. |
| **Definition of Done** | Executor state machine tests pass (8). Doctor health tests pass (4). Doctor report/events tests pass (4). All tests pass in CI. Code reviewed. Phase I exit criteria met. |

---

## Sprint Block 4: Pipeline Engines 2 — Observer → Learning (Sprints 26–36, 22 weeks)

---

### Sprint 26

| Field | Value |
|-------|-------|
| **Objectives** | Observer Engine: observation recording and discrepancy detection. |
| **Stories** | |
| | S26.1 — Implement observation recording: `observe(outcome, expected_outcome, context)` → OutcomeObservation, 100% basic observation coverage (OBS-001) |
| | S26.2 — Implement discrepancy detection: compare actual vs expected, success/discrepancy/anomaly, discrepancy score (OBS-002) |
| **Deliverables** | `app/shunya/observer/engine.py` |
| **Verification** | Every execution produces basic observation. Discrepancy detection works (match → no discrepancy, partial → discrepancy, unexpected → anomaly). Discrepancy score computed. |
| **Definition of Done** | Observation recording tests pass (5). Discrepancy detection tests pass (6). All tests pass in CI. Code reviewed. |

### Sprint 27

| Field | Value |
|-------|-------|
| **Objectives** | Observer Engine: events. Learning Engine: outcome analysis. |
| **Stories** | |
| | S27.1 — Implement observation events: `observation.recorded`, `observation.discrepancy.detected`, `observation.anomaly.flagged` (OBS-003) |
| | S27.2 — Implement learning outcome analysis: `learn(observations, historical_outcomes)`, pattern identification, cold start mode (LEARN-001) |
| **Deliverables** | Observer events. `app/shunya/learning/engine.py` (outcome analysis). |
| **Verification** | Observer events published on correct triggers. Events consumed by Knowledge Engine. Learning: outcome analyzed, patterns identified, cold start mode collects without recommending. |
| **Definition of Done** | Observer event tests pass (4). Outcome analysis tests pass (8). All tests pass in CI. Code reviewed. Phase J exit criteria met. |

### Sprint 28

| Field | Value |
|-------|-------|
| **Objectives** | Learning Engine: learning signal generation and confidence calibration. |
| **Stories** | |
| | S28.1 — Implement learning signal generation: knowledge_improvement, reasoning_refinement, policy_optimization signal types (LEARN-002) |
| | S28.2 — Implement confidence calibration: damping factor, configurable learning_rate, calibration formula (LEARN-003) |
| **Deliverables** | Learning signal generation. Confidence calibration. |
| **Verification** | All 3 signal types produced. Signal contains insight, recommendation, fact_key, confidence. Calibration formula correct. Damping prevents oscillation. |
| **Definition of Done** | Signal generation tests pass (6). Calibration tests pass (6). All tests pass in CI. Code reviewed. |

### Sprint 29

| Field | Value |
|-------|-------|
| **Objectives** | Learning Engine: Governance integration. |
| **Stories** | |
| | S29.1 — Implement Governance integration for learning signals: signals pass through Governance before application, approved applied, rejected logged, REVIEW flagged (LEARN-004) |
| **Deliverables** | Complete Learning Engine. |
| **Verification** | Approved signal → applied (KnowledgeEngine updated). Rejected signal → logged. REVIEW signal → flagged for human review. Constitutional: Invariant 4 (Learning never bypasses governance) verified. |
| **Definition of Done** | Governance integration tests pass (6). All tests pass in CI. Code reviewed. Phase K exit criteria met. |

### Sprint 30

| Field | Value |
|-------|-------|
| **Objectives** | Integration testing preparation. Begin KnowledgeLayer retirement Phase 3 (cutover). |
| **Stories** | |
| | S30.1 — Switch KnowledgeEngine facade to IKS-primary mode. IKS authoritative, KnowledgeLayer fallback only for unmigrated keys. Freeze KnowledgeLayer data source (RET-001) |
| **Deliverables** | IKS-primary cutover. |
| **Verification** | IKS returns all migrated facts. KnowledgeLayer fallback only for unmigrated keys. No data loss. |
| **Definition of Done** | Cutover tests pass (6). All tests pass in CI. Code reviewed. |

### Sprint 31

| Field | Value |
|-------|-------|
| **Objectives** | KnowledgeLayer retirement: dependency audit, removal, end-to-end verification. |
| **Stories** | |
| | S31.1 — Audit all code paths for KnowledgeLayer imports. Confirm zero remaining (RET-002) |
| | S31.2 — Remove KnowledgeLayer class, markdown KB file, legacy wrapper, KnowledgeLayer tests (RET-003) |
| | S31.3 — End-to-end verification: all 5 previously KnowledgeLayer-dependent paths function through IKS via KnowledgeEngine (RET-004) |
| **Deliverables** | KnowledgeLayer removed. IKS is sole knowledge store. |
| **Verification** | Zero KnowledgeLayer imports. All tests pass. All 5 call sites return correct data. |
| **Definition of Done** | Audit complete. Removal verified. End-to-end tests pass (5). Phase M exit criteria met. |

### Sprint 32

| Field | Value |
|-------|-------|
| **Objectives** | Full pipeline integration test — implementation. |
| **Stories** | |
| | S32.1 — Implement full pipeline end-to-end test: External Trigger → Observation → Knowledge Resolution → Context Fusion → Reasoning → Planning → Governance → Execution → Observation → Knowledge Update → Learning → Continuous Improvement (INT-001) |
| **Deliverables** | Full pipeline integration test. |
| **Verification** | Full pipeline test passes. Success and failure paths covered. Each lifecycle stage verified. |
| **Definition of Done** | Pipeline test implemented and passing. |

### Sprint 33

| Field | Value |
|-------|-------|
| **Objectives** | Full pipeline integration test — hardening. Constitutional invariant CI pipeline. |
| **Stories** | |
| | S33.1 — Harden full pipeline test: edge cases, degraded modes, concurrent requests, error recovery (INT-001 — hardening) |
| | S33.2 — Implement constitutional invariant tests: 14 structural invariants + 12 behavioral invariants (INT-002 — part 1) |
| **Deliverables** | Hardened pipeline test. 14 structural invariant tests. |
| **Verification** | Pipeline test covers edge cases and degraded modes. 14 structural invariants verified. |
| **Definition of Done** | Pipeline test hardening complete. 14 invariant tests passing in CI. |

### Sprint 34

| Field | Value |
|-------|-------|
| **Objectives** | Constitutional invariant CI pipeline — completion. |
| **Stories** | |
| | S34.1 — Implement remaining 12 behavioral invariant tests (INT-002 — part 2) |
| | S34.2 — Configure CI pipeline to run all 26 invariant tests on every PR. CI fails on invariant violation. |
| **Deliverables** | Complete constitutional invariant CI pipeline. |
| **Verification** | All 26 invariant tests pass. CI configured correctly. PR violates invariant → CI fails. |
| **Definition of Done** | 26 invariant tests passing in CI. |

### Sprint 35

| Field | Value |
|-------|-------|
| **Objectives** | Performance benchmarks. |
| **Stories** | |
| | S35.1 — Implement performance benchmark suite: per-engine latency (p50, p99), throughput, memory usage (INT-003) |
| | S35.2 — Run benchmarks against all engines. Compare against spec targets. Fix any out-of-budget engines. |
| **Deliverables** | Performance benchmark suite. Benchmark results report. |
| **Verification** | All engines within latency budget (p50 and p99 per spec). Throughput meets minimum. Memory within budget. |
| **Definition of Done** | Benchmarks implemented. Results within spec. Any out-of-budget engines documented with remediation plan. |

### Sprint 36

| Field | Value |
|-------|-------|
| **Objectives** | Architecture checkpoint. |
| **Stories** | |
| | S36.1 — Run architecture compliance scan: compare implementation against frozen architecture. Check all engines, API contracts, SHALL NEVER, events, invariants (INT-004) |
| **Deliverables** | Architecture checkpoint report. |
| **Verification** | Zero divergence between implementation and frozen architecture. All engine specifications satisfied. ADR compliance confirmed. |
| **Definition of Done** | Architecture checkpoint passed. Divergence report: zero items. Phase N exit criteria met. |

---

## Sprint Block 5: Release (Sprints 37–42, 12 weeks)

---

### Sprint 37

| Field | Value |
|-------|-------|
| **Objectives** | Operations runbook and security audit. |
| **Stories** | |
| | S37.1 — Create operations runbook: startup sequence, health check interpretation, failure recovery, DB backup/restore, Event Bus DLQ replay, Credential Store key rotation, KnowledgeEngine fact recovery (REL-001) |
| | S37.2 — Perform security audit: credential handling, tenant isolation, input validation, event payload inspection, SHALL NEVER enforcement audit (REL-002) |
| **Deliverables** | Operations runbook. Security audit report. |
| **Verification** | Runbook walkthrough successful. Security audit: zero critical/high findings. Medium findings documented with remediation plan. |
| **Definition of Done** | Runbook published and walkthrough completed. Security audit passed. |

### Sprint 38

| Field | Value |
|-------|-------|
| **Objectives** | Pre-deployment verification. |
| **Stories** | |
| | S38.1 — Run full test suite on staging environment. |
| | S38.2 — Run performance benchmarks on staging. |
| | S38.3 — Run architecture compliance scan on staging. |
| **Deliverables** | Staging verification report. |
| **Verification** | All tests pass on staging. Performance within budget. Architecture compliance confirmed. |
| **Definition of Done** | Staging verification complete. Sign-off from Chief Software Architect. |

### Sprint 39

| Field | Value |
|-------|-------|
| **Objectives** | Production deployment preparation. |
| **Stories** | |
| | S39.1 — Prepare deployment scripts. |
| | S39.2 — Prepare database migration scripts. |
| | S39.3 — Prepare smoke test suite. |
| **Deliverables** | Deployment scripts. Migration scripts. Smoke test suite. |
| **Verification** | Deployment scripts run on staging without error. Migration scripts run cleanly. Smoke tests pass on staging. |
| **Definition of Done** | Deployment preparation complete. |

### Sprint 40

| Field | Value |
|-------|-------|
| **Objectives** | Production deployment. |
| **Stories** | |
| | S40.1 — Deploy to production (Contabo VPS). Run database migrations. (REL-003) |
| | S40.2 — Verify health endpoint. Run smoke tests. Confirm all engines operational. |
| **Deliverables** | Production deployment. |
| **Verification** | Deployment completes without error. Health endpoint reports all engines healthy. Smoke tests pass. |
| **Definition of Done** | Production deployment operational. |

### Sprint 41

| Field | Value |
|-------|-------|
| **Objectives** | Production monitoring and stabilization. |
| **Stories** | |
| | S41.1 — Monitor production for 2 weeks. Triage any issues. |
| | S41.2 — Address any production incidents. |
| **Deliverables** | Production incident report (if any). |
| **Verification** | Zero critical incidents. All incidents resolved within SLA. |
| **Definition of Done** | Production stable for 2 weeks. |

### Sprint 42

| Field | Value |
|-------|-------|
| **Objectives** | Release sign-off and program completion. |
| **Stories** | |
| | S42.1 — Release sign-off by Chief Software Architect (engineering compliance) (REL-004) |
| | S42.2 — Release sign-off by Chief Constitutional Architect (constitutional compliance) (REL-004) |
| | S42.3 — Publish release notes. |
| **Deliverables** | Release sign-off. Release notes. |
| **Verification** | Both sign-offs obtained. Release notes published. |
| **Definition of Done** | Release approved. Program complete. |

---

## Sprint Summary

| Sprint Block | Sprints | Duration | Phase | Focus |
|-------------|---------|----------|-------|-------|
| Block 1 | 1–5 | 10 weeks | A–B | Foundation + Infrastructure |
| Block 2 | 6–12 | 14 weeks | C–E | Core Knowledge + Identity + Context |
| Block 3 | 13–25 | 26 weeks | F–H, I (part) | Pipeline Engines 1: Reasoning → Planner → Governance |
| Block 4 | 26–36 | 22 weeks | I (part), J–K, M, N | Pipeline Engines 2: Executor → Observer → Learning + Retirement + Integration |
| Block 5 | 37–42 | 12 weeks | O | Release |

**Total: 42 sprints, 84 weeks (~19 months)**

---

*End of SHUNYA_SPRINT_PLAN.md*