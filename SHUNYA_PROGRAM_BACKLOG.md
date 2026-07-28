# SHUNYA Program Backlog

**Authority:** SHUNYA_IMPLEMENTATION_PROGRAM.md
**Date:** 2026-07-18
**Status:** Active

---

## Task ID Convention

```
INFR-{NNN}  — Infrastructure (Phase A–B)
IKS-{NNN}   — Knowledge Store Transition (Phase C)
IDEN-{NNN}  — Identity Engine (Phase D)
CTX-{NNN}   — Context Fusion Engine (Phase E)
REAS-{NNN}  — Reasoning Engine (Phase F)
PLAN-{NNN}  — Planner Engine (Phase G)
GOV-{NNN}   — Governance Engine (Phase H)
EXEC-{NNN}  — Executor Engine (Phase I)
OBS-{NNN}   — Observer Engine (Phase J)
LEARN-{NNN} — Learning Engine (Phase K)
DOC-{NNN}   — Doctor Engine (Phase K parallel)
RET-{NNN}   — KnowledgeLayer Retirement (Phase M)
INT-{NNN}   — Integration & Hardening (Phase N)
REL-{NNN}   — Release (Phase O)
```

---

## Phase A — Foundation Infrastructure

### INFR-001: Dependency Injection Container

| Field | Value |
|-------|-------|
| **Description** | Implement lightweight DI container (`app/shunya/di.py`). Supports singleton and factory registrations. Constructor injection by type hint. |
| **Dependencies** | None |
| **Owner** | Infrastructure team |
| **Effort** | 3 days |
| **Verification gate** | DI container can instantiate a registered service with its dependencies. Singleton returns same instance. Factory returns new instance per call. |
| **Completion criteria** | `di.py` implemented. Unit tests pass (5 tests). |

### INFR-002: Configuration Loading

| Field | Value |
|-------|-------|
| **Description** | Implement YAML configuration loader (`app/shunya/config.py`). Schema validation. Per-environment config files. Environment variable override. |
| **Dependencies** | None |
| **Owner** | Infrastructure team |
| **Effort** | 3 days |
| **Verification gate** | Config loads from default YAML. Environment variable overrides apply. Invalid config raises validation error. Missing required field raises error. |
| **Completion criteria** | `config.py` implemented. Unit tests pass (8 tests). |

### INFR-003: Persistence Layer

| Field | Value |
|-------|-------|
| **Description** | Implement database session management (`app/shunya/infrastructure/persistence.py`). SQLAlchemy session factory. Connection pooling. Alembic migration runner. |
| **Dependencies** | INFR-002 (Config — DB URL, pool size) |
| **Owner** | Infrastructure team |
| **Effort** | 3 days |
| **Verification gate** | Session factory creates valid sessions. Connection pooling respects pool size. Alembic migrations run cleanly up and down. |
| **Completion criteria** | `persistence.py` implemented. Alembic configured. Migration test passes. Unit tests pass (6 tests). |

### INFR-004: Structured Logging

| Field | Value |
|-------|-------|
| **Description** | Implement centralized structured logging (`app/shunya/infrastructure/logging.py`). JSON output. Configurable levels per module. Privacy filters (PII stripping). correlation_id propagation. |
| **Dependencies** | INFR-002 (Config — log level, output) |
| **Owner** | Infrastructure team |
| **Effort** | 2 days |
| **Verification gate** | JSON log output at configured level. Correlation_id propagates through child loggers. Privacy filter strips PII patterns. |
| **Completion criteria** | `logging.py` implemented. Unit tests pass (5 tests). |

### INFR-005: Metrics Collection

| Field | Value |
|-------|-------|
| **Description** | Implement Prometheus-compatible metrics collection (`app/shunya/infrastructure/metrics.py`). Support counters, histograms, gauges. Per-engine metric namespacing. |
| **Dependencies** | INFR-002 (Config — metrics port, enabled) |
| **Owner** | Infrastructure team |
| **Effort** | 2 days |
| **Verification gate** | Metrics endpoint returns Prometheus-formatted output. Counter increments correctly. Histogram records observations. Per-engine namespaces separated. |
| **Completion criteria** | `metrics.py` implemented. Unit tests pass (5 tests). |

### INFR-006: Health Endpoint

| Field | Value |
|-------|-------|
| **Description** | Implement centralized health endpoint (`app/shunya/infrastructure/health.py`). Health registry where components register check functions. Aggregated endpoint. |
| **Dependencies** | INFR-001 (DI — health registry), INFR-004 (Logging), INFR-005 (Metrics) |
| **Owner** | Infrastructure team |
| **Effort** | 2 days |
| **Verification gate** | Health endpoint returns status per registered component. Degraded component reflected in overall status. Unresponsive component times out and reports unhealthy. |
| **Completion criteria** | `health.py` implemented. Unit tests pass (4 tests). |

---

## Phase B — Event Bus & Credential Store

### INFR-007: Event Bus — Core Implementation

| Field | Value |
|-------|-------|
| **Description** | Implement `EventBus` singleton per ADR-001 contract. Methods: `publish()`, `subscribe()`, `unsubscribe()`. In-process queue-based delivery. |
| **Dependencies** | INFR-001 (DI), INFR-002 (Config), INFR-004 (Logging) |
| **Owner** | Infrastructure team |
| **Effort** | 5 days |
| **Verification gate** | Events delivered to matching subscribers. Non-matching subscribers do not receive events. Wildcard pattern matching works (`knowledge.*`). Unsubscribe removes subscription. |
| **Completion criteria** | `event_bus.py` implemented. Unit tests pass (10 tests). |

### INFR-008: Event Bus — Delivery Guarantees

| Field | Value |
|-------|-------|
| **Description** | Implement at-least-once delivery, idempotency cache (24h TTL), per-producer per-event-type ordering, consumer timeout. |
| **Dependencies** | INFR-007 (Event Bus core) |
| **Owner** | Infrastructure team |
| **Effort** | 4 days |
| **Verification gate** | At-least-once delivery verified (consumer may receive duplicates). Idempotency cache deduplicates within TTL. Same-type same-producer events delivered in order. Consumer exceeding timeout is disconnected. |
| **Completion criteria** | Delivery guarantees implemented. Unit tests pass (8 tests). |

### INFR-009: Event Bus — Retry and Dead-Letter

| Field | Value |
|-------|-------|
| **Description** | Implement retry policy (3 attempts, exponential backoff). Dead-letter queue (max 1000 events). Manual replay. 30-day archival. |
| **Dependencies** | INFR-008 (Event Bus delivery) |
| **Owner** | Infrastructure team |
| **Effort** | 3 days |
| **Verification gate** | Failed deliveries are retried 3 times with exponential backoff. After max retries, event moves to dead-letter queue. Dead-letter events are replayable. Events older than 30 days are archived. |
| **Completion criteria** | Retry and dead-letter implemented. Unit tests pass (6 tests). |

### INFR-010: Event Bus — Tenant Isolation & Security

| Field | Value |
|-------|-------|
| **Description** | Implement tenant isolation (events carry tenant_id; consumers filter by tenant). Publisher authentication (engine identity verified). Schema validation against canonical event envelope (Core Models §8). |
| **Dependencies** | INFR-007 (Event Bus core), INFR-008 (Event Bus delivery) |
| **Owner** | Infrastructure team |
| **Effort** | 3 days |
| **Verification gate** | Tenant A events not delivered to Tenant B consumers. Invalid envelope (missing required field) rejected. Unregistered event type rejected. |
| **Completion criteria** | Security features implemented. Unit tests pass (6 tests). |

### INFR-011: Event Bus — Health Endpoint

| Field | Value |
|-------|-------|
| **Description** | Implement Event Bus health endpoint: status, queue depth, dead-letter count, consumer latency p50/p99, error count per consumer. |
| **Dependencies** | INFR-009 (Event Bus retry/DLQ), INFR-006 (Health endpoint) |
| **Owner** | Infrastructure team |
| **Effort** | 2 days |
| **Verification gate** | Health endpoint returns all required fields. Queue depth reflects pending events. Dead-letter count reflects DLQ state. |
| **Completion criteria** | Event Bus health implemented. Unit tests pass (3 tests). |

### INFR-012: Credential Store — Core Implementation

| Field | Value |
|-------|-------|
| **Description** | Implement `CredentialStore` per ADR-003 contract. Methods: `resolve()`, `store()`, `revoke()`, `list()`. Encrypted storage (AES-256-GCM). Credential metadata table. |
| **Dependencies** | INFR-003 (Persistence — credential_metadata table), INFR-002 (Config — encryption key) |
| **Owner** | Infrastructure team |
| **Effort** | 5 days |
| **Verification gate** | Credential stored and resolved correctly. Encrypted at rest (AES-256-GCM verified). Resolved value returned in memory only (never persisted). Metadata stored in plaintext. |
| **Completion criteria** | `credential_store.py` implemented. Unit tests pass (10 tests). |

### INFR-013: Credential Store — Security

| Field | Value |
|-------|-------|
| **Description** | Implement caller authentication (only Executor may call `resolve()`). Tenant isolation. Audit logging (no credential values in logs). Expiry enforcement. Revocation enforcement. |
| **Dependencies** | INFR-012 (Credential Store core) |
| **Owner** | Infrastructure team |
| **Effort** | 3 days |
| **Verification gate** | Non-Executor caller rejected. Tenant A cannot resolve Tenant B credentials. No credential values in audit logs. Expired credential returns `CredentialExpiredError`. Revoked credential returns error. |
| **Completion criteria** | Security features implemented. Unit tests pass (8 tests). |

### INFR-014: Credential Store — Phase 4 Eligibility Gate

| Field | Value |
|-------|-------|
| **Description** | Implement Phase 4 eligibility gate integration. `resolve()` takes `purpose_code` and checks eligibility before releasing credential. Gate unavailable → safe failure (deny). |
| **Dependencies** | INFR-012 (Credential Store core) |
| **Owner** | Infrastructure team |
| **Effort** | 2 days |
| **Verification gate** | Valid purpose_code returns credential. Invalid purpose_code returns `EligibilityDeniedError`. Gate unavailable returns deny (safe failure). |
| **Completion criteria** | Phase 4 integration implemented. Unit tests pass (4 tests). |

---

## Phase C — Knowledge Store Transition (ADR-002 Phase 1–2)

### IKS-001: ImmutableKnowledgeStore — Fact Operations

| Field | Value |
|-------|-------|
| **Description** | Implement core IKS fact operations per existing `knowledge_store.py` (383 lines). `set_fact()`, `get_fact()`, `get_fact_history()`, `search_facts()`. Versioning through supersession. No in-place updates. |
| **Dependencies** | INFR-003 (Persistence — knowledge_facts table) |
| **Owner** | Knowledge team |
| **Effort** | 5 days |
| **Verification gate** | `set_fact()` creates new version (increments version). `get_fact()` returns latest active version. `get_fact_history()` returns all versions. `search_facts()` returns filtered results. |
| **Completion criteria** | IKS fact operations implemented. Unit tests pass (12 tests). Existing `knowledge_store.py` is reference; new implementation in `app/shunya/knowledge/immutable_store.py`. |

### IKS-002: ImmutableKnowledgeStore — Lifecycle and Invariants

| Field | Value |
|-------|-------|
| **Description** | Implement fact lifecycle: Unknown → Observed → Verified → Trusted → Superseded → Archived → Retired. Enforce invariants: no in-place updates, no deletions, complete version history. |
| **Dependencies** | IKS-001 (IKS fact operations) |
| **Owner** | Knowledge team |
| **Effort** | 3 days |
| **Verification gate** | Fact lifecycle transitions work correctly. Superseded fact returns from history but not from `get_fact()`. Archived fact excluded from search. Retired fact in terminal state. No in-place update possible. |
| **Completion criteria** | Lifecycle implemented. Invariant enforcement tests pass (6 tests). |

### IKS-003: KnowledgeEngine Facade

| Field | Value |
|-------|-------|
| **Description** | Implement `KnowledgeEngine` facade wrapping IKS + KnowledgeLayer. Phase 1: IKS primary, KnowledgeLayer fallback. Methods: `get_fact()`, `set_fact()`, `search_facts()`, `get_fact_history()`. |
| **Dependencies** | IKS-001 (IKS), existing `knowledge.py` (KnowledgeLayer in `legacy/`) |
| **Owner** | Knowledge team |
| **Effort** | 4 days |
| **Verification gate** | `get_fact()` returns from IKS if present, falls back to KnowledgeLayer if not. `set_fact()` writes to IKS only (KnowledgeLayer read-only). `search_facts()` returns merged results. |
| **Completion criteria** | `engine.py` implemented. All 5 existing KnowledgeLayer call sites function through facade. Unit tests pass (8 tests). |

### IKS-004: KnowledgeLayer Wrapper in Legacy

| Field | Value |
|-------|-------|
| **Description** | Move existing `knowledge.py` (KnowledgeLayer) to `app/shunya/legacy/knowledge_layer.py`. Add adapter methods matching KnowledgeEngine interface. Ensure all existing imports continue to function. |
| **Dependencies** | IKS-003 (KnowledgeEngine facade) |
| **Owner** | Knowledge team |
| **Effort** | 2 days |
| **Verification gate** | All 5 existing call sites import from legacy wrapper without modification. Wrapper returns same data as original KnowledgeLayer. |
| **Completion criteria** | KnowledgeLayer in legacy/. All imports verified. Unit tests pass (3 tests). |

### IKS-005: Migration Script — Read KnowledgeLayer Data

| Field | Value |
|-------|-------|
| **Description** | Implement migration script (`scripts/migrate_knowledge_layer.py`). Read all data from KnowledgeLayer markdown parser. Parse each `Destination` into IKS `KnowledgeFact` per ADR-002 fact key mapping. |
| **Dependencies** | IKS-001 (IKS — target store), existing `knowledge.py` (KnowledgeLayer — source parser) |
| **Owner** | Knowledge team |
| **Effort** | 4 days |
| **Verification gate** | Script reads all destinations from KnowledgeLayer. Each destination field maps to correct IKS fact key (11 mappings verified). Migration report shows destination count. |
| **Completion criteria** | Migration script implemented. Unit tests pass (6 tests). |

### IKS-006: Migration Script — Seed IKS

| Field | Value |
|-------|-------|
| **Description** | Implement IKS seeding logic in migration script. Create KnowledgeFact for each destination field. Set confidence=0.7, status=active, version=1. Handle duplicate fact keys (supersede instead of overwrite). |
| **Dependencies** | IKS-005 (Migration script — read) |
| **Owner** | Knowledge team |
| **Effort** | 3 days |
| **Verification gate** | All destinations written to IKS. Fact key mapping verified (spot-check 10 random destinations). No data loss (destination count matches). Duplicate handling creates supersession, not error. |
| **Completion criteria** | Seeding implemented. Dry-run passes. Unit tests pass (5 tests). |

### IKS-007: Migration Script — Verification Report

| Field | Value |
|-------|-------|
| **Description** | Implement verification report: compare IKS count vs KnowledgeLayer count. Log any destinations that failed to migrate. Random sample verification (10 destinations manually verified). Export report as JSON. |
| **Dependencies** | IKS-006 (Migration script — seed) |
| **Owner** | Knowledge team |
| **Effort** | 2 days |
| **Verification gate** | Report includes: total destinations, migrated count, failed count, sample verification results. Zero failures required for migration to pass. |
| **Completion criteria** | Verification report implemented. Migration script complete with report output. Unit tests pass (3 tests). |

### IKS-008: Facade Fallback Verification

| Field | Value |
|-------|-------|
| **Description** | Verify that KnowledgeEngine facade correctly falls back to KnowledgeLayer for data not yet migrated. Test with unmigrated fact keys. Verify that migrated data returns from IKS (no fallback). |
| **Dependencies** | IKS-003 (KnowledgeEngine facade), IKS-006 (Migration script — seed) |
| **Owner** | Knowledge team |
| **Effort** | 2 days |
| **Verification gate** | Unmigrated fact key: returns from KnowledgeLayer fallback. Migrated fact key: returns from IKS (no fallback call made). Migration + fallback work correctly together. |
| **Completion criteria** | Fallback verification tests pass (4 tests). |

---

## Phase D — Identity Engine (ES-010)

### IDEN-001: Identity Normalizer

| Field | Value |
|-------|-------|
| **Description** | Implement identity value normalization per identity type. Email: lowercase, stripped. Phone: E.164 format. Channel: provider-specific normalization. Document: issuer-scoped. External: provider-scoped. Alias: no normalization (weak). |
| **Dependencies** | None |
| **Owner** | Identity team |
| **Effort** | 3 days |
| **Verification gate** | All 8 identity types normalized correctly. Invalid values rejected per type. Normalized values are deterministic (same input → same output). |
| **Completion criteria** | `normalizer.py` implemented. Unit tests pass (10 tests). |

### IDEN-002: Identity Resolution Engine

| Field | Value |
|-------|-------|
| **Description** | Implement core identity resolution (`app/shunya/identity/engine.py`). `resolve(claim)` returns MATCHED, NO_MATCH, or AMBIGUOUS. Lookup by normalized value + tenant_id. Single match → MATCHED. No match → NO_MATCH. Multiple → AMBIGUOUS. |
| **Dependencies** | IDEN-001 (Normalizer), IKS-001 (IKS — stores identity records) |
| **Owner** | Identity team |
| **Effort** | 5 days |
| **Verification gate** | Single identity match returns MATCHED with person_id and confidence. No match returns NO_MATCH with null person_id. Multiple matches return AMBIGUOUS with candidates list. Deterministic (same input → same output). |
| **Completion criteria** | `engine.py` implemented. Unit tests pass (12 tests). |

### IDEN-003: Identity Registration

| Field | Value |
|-------|-------|
| **Description** | Implement identity registration. When resolution returns NO_MATCH, register new identity record. Required fields: identity_id, person_id, identity_type, identity_value, normalized_value, confidence, provenance, status=active. |
| **Dependencies** | IDEN-002 (Resolution engine) |
| **Owner** | Identity team |
| **Effort** | 3 days |
| **Verification gate** | New identity registered with all required fields. Duplicate normalized_value + tenant_id rejected (identity conflict). Person_id links to existing or new person record. |
| **Completion criteria** | Registration implemented. Unit tests pass (6 tests). |

### IDEN-004: Identity Lifecycle State Machine

| Field | Value |
|-------|-------|
| **Description** | Implement identity state machine per ES-010 §6: Active → Verified → Superseded → Merged. Transition methods: `verify()`, `supersede()`, `merge()`. Verification state (unverified/verified/failed). |
| **Dependencies** | IDEN-002 (Resolution engine) |
| **Owner** | Identity team |
| **Effort** | 4 days |
| **Verification gate** | All 7 transitions work correctly. Active → Verified updates verification_state. Active → Superseded creates new identity record, marks old as superseded. Active → Merged links to canonical identity. Supersession loop detection (A→B→A) rejects. |
| **Completion criteria** | State machine implemented. Unit tests pass (10 tests). |

### IDEN-005: Identity Tenant Isolation

| Field | Value |
|-------|-------|
| **Description** | Implement tenant isolation. All identity lookups include tenant_id. Same phone number in different tenants resolves to different persons. Cross-tenant resolution returns NO_MATCH. |
| **Dependencies** | IDEN-002 (Resolution engine) |
| **Owner** | Identity team |
| **Effort** | 2 days |
| **Verification gate** | Tenant A resolves phone to Person A. Tenant B resolves same phone to Person B. Cross-tenant lookup returns NO_MATCH. Identity records never leak across tenants. |
| **Completion criteria** | Tenant isolation tests pass (4 tests). |

### IDEN-006: Identity Events and Integration

| Field | Value |
|-------|-------|
| **Description** | Implement event publishing: `identity.resolved`, `identity.ambiguous`, `identity.registered`, `identity.superseded`, `identity.merged`, `identity.verified`. Events use canonical envelope. |
| **Dependencies** | IDEN-002 (Resolution engine), INFR-010 (Event Bus — tenant isolation, canonical envelope) |
| **Owner** | Identity team |
| **Effort** | 2 days |
| **Verification gate** | Each event type published on correct trigger. Events conform to canonical envelope (Core Models §8). Event carries tenant_id, actor, object. |
| **Completion criteria** | Events implemented. Unit tests pass (6 tests). |

---

## Phase E — Context Fusion Engine (ES-009)

### CTX-001: Context Request Handling

| Field | Value |
|-------|-------|
| **Description** | Implement context request handler. `assemble(request)` accepts ContextRequest with tenant_id, actor_id, purpose_code, subject_id, current_object_ref, max_items, timeout_ms. Validate all required fields. |
| **Dependencies** | IDEN-002 (Identity Engine — resolution), INFR-001 (DI) |
| **Owner** | Context team |
| **Effort** | 3 days |
| **Verification gate** | Valid request accepted. Invalid request (missing field) rejected with appropriate error. Timeout respected. Budget limits enforced. |
| **Completion criteria** | Request handling implemented. Unit tests pass (6 tests). |

### CTX-002: Identity Source Provider Integration

| Field | Value |
|-------|-------|
| **Description** | Implement identity source provider. Call IdentityEngine.resolve() for actor_id and subject_id. Handle MATCHED, NO_MATCH, AMBIGUOUS results. Return identity section with resolved identities. |
| **Dependencies** | CTX-001 (Request handling), IDEN-002 (Identity resolution) |
| **Owner** | Context team |
| **Effort** | 3 days |
| **Verification gate** | Actor identity resolved and included in context. Subject identity resolved and included. AMBIGUOUS identity returns degraded section. Identity timeout returns empty section with documented exclusion. |
| **Completion criteria** | Identity provider implemented. Unit tests pass (5 tests). |

### CTX-003: Knowledge Source Provider Integration

| Field | Value |
|-------|-------|
| **Description** | Implement knowledge source provider. Read memory items, evidence records, document references from KnowledgeEngine. Scope by tenant_id and workspace_id. |
| **Dependencies** | CTX-001 (Request handling), IKS-003 (KnowledgeEngine facade) |
| **Owner** | Context team |
| **Effort** | 3 days |
| **Verification gate** | Memory items returned from KnowledgeEngine. Evidence records returned. Document references returned. All scoped to tenant/workspace. Knowledge timeout returns degraded section. |
| **Completion criteria** | Knowledge provider implemented. Unit tests pass (5 tests). |

### CTX-004: Phase 4 Eligibility Gate Integration

| Field | Value |
|-------|-------|
| **Description** | Implement Phase 4 eligibility gate for each context section. `EligibilityGate.check(purpose_code, section_name)` returns allowed/denied. Denied sections are excluded with documented reason. Gate unavailable → safe denial. |
| **Dependencies** | CTX-002 (Identity provider), CTX-003 (Knowledge provider) |
| **Owner** | Context team |
| **Effort** | 3 days |
| **Verification gate** | Allowed purpose_code → section included. Denied purpose_code → section excluded with reason. Gate unavailable → section excluded with "gate unavailable" reason. |
| **Completion criteria** | Eligibility gate implemented. Unit tests pass (5 tests). |

### CTX-005: Budget Enforcement

| Field | Value |
|-------|-------|
| **Description** | Implement budget enforcement per context request. Track item count and total serialized size. Truncate when over budget (remove lowest-confidence items first). Report BudgetReport in output. |
| **Dependencies** | CTX-002, CTX-003 (Source providers — produce items) |
| **Owner** | Context team |
| **Effort** | 2 days |
| **Verification gate** | Context within budget delivered fully. Context over budget truncated to fit. BudgetReport reflects total_items, max_items, truncated flag. Truncation removes lowest-confidence items first. |
| **Completion criteria** | Budget enforcement implemented. Unit tests pass (4 tests). |

### CTX-006: Fingerprint Computation

| Field | Value |
|-------|-------|
| **Description** | Implement cryptographic fingerprint of assembled context. Hash of serialized context content (sorted keys, canonical JSON). Fingerprint included in WorkspaceContext. |
| **Dependencies** | CTX-005 (Budget enforcement — produces final context) |
| **Owner** | Context team |
| **Effort** | 1 day |
| **Verification gate** | Same context produces same fingerprint. Different context produces different fingerprint. Fingerprint included in WorkspaceContext output. |
| **Completion criteria** | Fingerprint computation implemented. Unit tests pass (2 tests). |

### CTX-007: WorkspaceContext Assembly and Delivery

| Field | Value |
|-------|-------|
| **Description** | Implement final WorkspaceContext assembly. Combine all sections. Set context_id, tenant_id, actor_id, purpose_code, fingerprint, assembled_at, is_degraded flag. Return to caller. |
| **Dependencies** | CTX-002 through CTX-006 (All providers, gates, budget, fingerprint) |
| **Owner** | Context team |
| **Effort** | 3 days |
| **Verification gate** | WorkspaceContext contains all required fields. Section order preserved. Degraded flag set when any provider timed out or eligibility denied. Context delivered to caller. |
| **Completion criteria** | Assembly pipeline complete. Unit tests pass (6 tests). Integration with Identity, Knowledge verified. |

### CTX-008: Context Fusion State Machine

| Field | Value |
|-------|-------|
| **Description** | Implement state machine per ES-009 §6. States: Idle, Resolving_Identity, Collecting_Source_Data, Applying_Eligibility_Gates, Enforcing_Budget, Computing_Fingerprint, Delivering_Context, Error. All 9 transitions. |
| **Dependencies** | CTX-007 (Assembly pipeline — provides state transitions) |
| **Owner** | Context team |
| **Effort** | 2 days |
| **Verification gate** | All 9 state transitions implemented. Invalid transition raises error. Terminal states (Error) cannot transition further. Timeout transitions work correctly. |
| **Completion criteria** | State machine implemented. Unit tests pass (9 tests). |

---

## Phase F — Reasoning Engine (ES-003)

### REAS-001: Context Consumption

| Field | Value |
|-------|-------|
| **Description** | Implement context consumption from Context Fusion. `reason(request)` calls ContextFusionEngine.assemble() to get WorkspaceContext. Handle degraded context (lower confidence in output). Handle error (return reason failure). |
| **Dependencies** | CTX-007 (Context Fusion — context assembly) |
| **Owner** | Reasoning team |
| **Effort** | 3 days |
| **Verification gate** | Full context → reasoning proceeds normally. Degraded context → reasoning proceeds with lower confidence. Context unavailable → reason failure returned. |
| **Completion criteria** | Context consumption implemented. Unit tests pass (4 tests). |

### REAS-002: Evidence Chain Building

| Field | Value |
|-------|-------|
| **Description** | Implement evidence chain building. For each reasoning output, produce evidence chain linking each claim to source facts from KnowledgeEngine. Include: evidence_id, source_id, relationship (supports/contradicts), weight, quality, confidence. |
| **Dependencies** | REAS-001 (Context consumption — provides facts), IKS-003 (KnowledgeEngine — fact access) |
| **Owner** | Reasoning team |
| **Effort** | 5 days |
| **Verification gate** | Evidence chain produced for every reasoning output. Each claim linked to source facts. Evidence fields (weight, quality, confidence) populated correctly. Empty evidence chain handled (no supporting facts found). |
| **Completion criteria** | Evidence chain building implemented. Unit tests pass (8 tests). |

### REAS-003: Confidence Scoring

| Field | Value |
|-------|-------|
| **Description** | Implement canonical confidence scoring per Core Models §7. Scale 0.0–1.0. Propagation: `derived_confidence = min(confidence_of_inputs) * derivation_quality`. Combination: `1 - ∏(1 - confidence_i)`. |
| **Dependencies** | REAS-002 (Evidence chain — provides confidence inputs) |
| **Owner** | Reasoning team |
| **Effort** | 3 days |
| **Verification gate** | Single source confidence correct. Combined confidence from multiple independent sources correct. Propagation with derivation quality correct. Confidence never exceeds 1.0 or below 0.0. |
| **Completion criteria** | Confidence scoring implemented. Unit tests pass (8 tests). |

### REAS-004: Reasoning Strategies

| Field | Value |
|-------|-------|
| **Description** | Implement reasoning strategies per ES-003 §5. Types: deductive, inductive, abductive, analogical, causal, comparative, temporal, compositional, counterfactual, evaluative. Each strategy produces ReasoningResult. |
| **Dependencies** | REAS-001 (Context), REAS-002 (Evidence), REAS-003 (Confidence) |
| **Owner** | Reasoning team |
| **Effort** | 8 days |
| **Verification gate** | All 10 reasoning types implemented. Each produces ReasoningResult with decision, confidence, evidence_chain, explanation, alternatives, risk_flags. Insufficient context → low-confidence result with explanation. |
| **Completion criteria** | All strategies implemented. Unit tests pass (20 tests). |

### REAS-005: Reasoning State Machine

| Field | Value |
|-------|-------|
| **Description** | Implement reasoning state machine: Idle, Receiving_Context, Resolving_Knowledge, Reasoning, Producing_Result, Completed, Failed. All transitions. |
| **Dependencies** | REAS-004 (Strategies — provides transitions) |
| **Owner** | Reasoning team |
| **Effort** | 2 days |
| **Verification gate** | All state transitions implemented. Invalid transitions raise error. Terminal states (Completed, Failed) handled correctly. Timeout transitions work. |
| **Completion criteria** | State machine implemented. Unit tests pass (7 tests). |

---

## Phase G — Planner Engine (ES-004)

### PLAN-001: Plan Generation

| Field | Value |
|-------|-------|
| **Description** | Implement plan generation. `plan(reasoning_result, context)` creates executable plan from ReasoningResult. Sequence steps with dependencies, timelines, resource estimates. Include alternatives. |
| **Dependencies** | REAS-004 (Reasoning strategies — produces ReasoningResult), CTX-007 (Context Fusion — workspace context) |
| **Owner** | Planner team |
| **Effort** | 5 days |
| **Verification gate** | Plan produced from reasoning result. Steps sequenced in order. Dependencies between steps correct. Timeline computed for each step. Cost estimates produced. Alternative plans generated. |
| **Completion criteria** | Plan generation implemented. Unit tests pass (10 tests). |

### PLAN-002: Plan Templates

| Field | Value |
|-------|-------|
| **Description** | Implement plan templates for common action types. Template types: message_send, record_create, api_call, financial_transaction, multi_step_workflow. Each template produces structured PlanObject per ES-004 input contract. |
| **Dependencies** | PLAN-001 (Plan generation) |
| **Owner** | Planner team |
| **Effort** | 4 days |
| **Verification gate** | All 5 template types produce valid PlanObject. PlanObject conforms to Governance input contract. Missing data produces degraded plan (not failure). |
| **Completion criteria** | Templates implemented. Unit tests pass (10 tests). |

### PLAN-003: Planner State Machine

| Field | Value |
|-------|-------|
| **Description** | Implement planner state machine: Idle, Receiving_Input, Creating_Plan, Estimating_Costs, Completed, Failed. All transitions. |
| **Dependencies** | PLAN-001 (Plan generation — provides transitions) |
| **Owner** | Planner team |
| **Effort** | 2 days |
| **Verification gate** | All state transitions implemented. Invalid transitions raise error. Terminal states handled correctly. |
| **Completion criteria** | State machine implemented. Unit tests pass (5 tests). |

---

## Phase H — Governance Engine (ES-001)

### GOV-001: Policy Registry

| Field | Value |
|-------|-------|
| **Description** | Implement policy registry. Store policies by name, domain, scope, severity. Methods: `register_policy()`, `get_policy()`, `list_policies()`, `remove_policy()`. Tenant-scoped policies + GLOBAL policies. |
| **Dependencies** | IKS-003 (KnowledgeEngine — policy storage) |
| **Owner** | Governance team |
| **Effort** | 4 days |
| **Verification gate** | Policy registered and retrievable. Tenant-scoped policies isolated. GLOBAL policies apply to all tenants. Policy removal works. Unknown policy reference handled gracefully. |
| **Completion criteria** | Policy registry implemented. Unit tests pass (8 tests). |

### GOV-002: Plan Validation

| Field | Value |
|-------|-------|
| **Description** | Implement plan validation. Validate plan structure against Governance input contract. Check required fields present. Validate action_type, proposal structure, evidence_chain, confidence. Reject invalid plans. |
| **Dependencies** | PLAN-001 (Plan generation — produces PlanObject) |
| **Owner** | Governance team |
| **Effort** | 3 days |
| **Verification gate** | Valid plan accepted. Missing action_type rejected. Empty proposal rejected. Missing tenant_id rejected. Unknown domain produces warning but not rejection. |
| **Completion criteria** | Plan validation implemented. Unit tests pass (6 tests). |

### GOV-003: Constitutional Policy Evaluation

| Field | Value |
|-------|-------|
| **Description** | Implement constitutional policy evaluation. Map all 10 constitutional principles from SHUNYA_ARCHITECTURE.md to evaluable policies. Each policy: evaluate(plan, context) → pass/fail/warning. |
| **Dependencies** | GOV-001 (Policy registry), GOV-002 (Plan validation), CTX-007 (Context Fusion — context enrichment) |
| **Owner** | Governance team |
| **Effort** | 6 days |
| **Verification gate** | All 10 constitutional principles evaluable. Each returns pass/fail/warning with explanation. Violation recorded with policy_name, severity, detail. Policy evaluation error returns REJECT with error detail. |
| **Completion criteria** | Constitutional policies implemented. Unit tests pass (15 tests). |

### GOV-004: Business Policy Evaluation

| Field | Value |
|-------|-------|
| **Description** | Implement business policy evaluation. Domain-specific policies (travel, healthcare, legal). Risk threshold policies. Action-type policies. Policy conflicts handled (conflicting policies → REVIEW required). |
| **Dependencies** | GOV-003 (Constitutional policy evaluation) |
| **Owner** | Governance team |
| **Effort** | 4 days |
| **Verification gate** | Domain policies scoped correctly (travel policy not applied to healthcare). Risk thresholds enforced. Policy conflict detected and produces REVIEW verdict. |
| **Completion criteria** | Business policies implemented. Unit tests pass (10 tests). |

### GOV-005: Risk Assessment

| Field | Value |
|-------|-------|
| **Description** | Implement risk assessment. Compute risk score from policy evaluation results. Low risk (<0.3) → APPROVE. Medium risk (0.3–0.7) → REVIEW. High risk (>0.7) → REJECT. |
| **Dependencies** | GOV-004 (Business policy evaluation — provides policy results) |
| **Owner** | Governance team |
| **Effort** | 3 days |
| **Verification gate** | Low risk → APPROVE verdict. Medium risk → REVIEW verdict. High risk → REJECT verdict. Risk score computed correctly from policy severity and count. |
| **Completion criteria** | Risk assessment implemented. Unit tests pass (5 tests). |

### GOV-006: Governance Verdict Production

| Field | Value |
|-------|-------|
| **Description** | Implement verdict production. Produce GovernanceVerdict with: approved, decision (APPROVE/REVIEW/REJECT), confidence, explanation, blocking_policies, warnings, reviews_required, evidence_checked, audit_id, evaluated_at, context_snapshot. |
| **Dependencies** | GOV-005 (Risk assessment — produces verdict) |
| **Owner** | Governance team |
| **Effort** | 3 days |
| **Verification gate** | APPROVE verdict produced correctly. REVIEW verdict produced with reviews_required list. REJECT verdict produced with blocking_policies list. All verdict fields populated. Context snapshot frozen at decision time. |
| **Completion criteria** | Verdict production implemented. Unit tests pass (6 tests). |

### GOV-007: Immutable Audit Trail

| Field | Value |
|-------|-------|
| **Description** | Implement audit trail. Every governance decision produces immutable audit record. Audit fields: audit_id, input context (frozen), policies evaluated + results, final verdict, timestamp, evaluating instance identity. Append-only. |
| **Dependencies** | GOV-006 (Verdict production — produces audit data) |
| **Owner** | Governance team |
| **Effort** | 3 days |
| **Verification gate** | Every decision creates audit record. Audit record contains all required fields. Append-only (no delete, no update). Historical records unaffected by policy changes. |
| **Completion criteria** | Audit trail implemented. Unit tests pass (5 tests). |

### GOV-008: Governance State Machine

| Field | Value |
|-------|-------|
| **Description** | Implement governance state machine per ES-001 §6. States: Idle, Receiving, Validating_Context, Validating_Constitution, Evaluating_Policies, Assessing_Risk, Approved, Review_Required, Rejected, Error. All 14 transitions. |
| **Dependencies** | GOV-003 through GOV-007 (All governance logic — provides transitions) |
| **Owner** | Governance team |
| **Effort** | 3 days |
| **Verification gate** | All 14 state transitions implemented. Invalid transitions raise error. Terminal states (Approved, Review_Required, Rejected, Error) handled correctly. Timeout transition (Receiving → Error) works. |
| **Completion criteria** | State machine implemented. Unit tests pass (14 tests). |

---

## Phase I — Executor Engine (ES-005)

### EXEC-001: Channel Adapter — WhatsApp

| Field | Value |
|-------|-------|
| **Description** | Implement WhatsApp channel adapter. Send messages via WhatsApp Business API. Resolve credentials from CredentialStore at execution time. Handle delivery confirmation. Retry on failure. |
| **Dependencies** | INFR-013 (Credential Store — credential resolution) |
| **Owner** | Executor team |
| **Effort** | 5 days |
| **Verification gate** | Message sent successfully. Credential resolved and discarded after send. Delivery confirmation received. Retry on transient failure (3 attempts, exponential backoff). Fallback to alternative channel on persistent failure. |
| **Completion criteria** | WhatsApp adapter implemented. Unit tests pass (8 tests). Integration test with Credential Store. |

### EXEC-002: Channel Adapter — Telegram

| Field | Value |
|-------|-------|
| **Description** | Implement Telegram channel adapter. Send messages via Telegram Bot API. Resolve credentials. Handle delivery confirmation. Retry on failure. (Replaces existing Telegram-only executor.) |
| **Dependencies** | INFR-013 (Credential Store) |
| **Owner** | Executor team |
| **Effort** | 3 days |
| **Verification gate** | Message sent successfully. Credential resolved and discarded. Delivery confirmation received. Retry on transient failure. |
| **Completion criteria** | Telegram adapter implemented. Unit tests pass (6 tests). |

### EXEC-003: Channel Adapter — Email

| Field | Value |
|-------|-------|
| **Description** | Implement email channel adapter. Send via SMTP or email API. Resolve SMTP credentials. HTML and plaintext support. Handle delivery reports. |
| **Dependencies** | INFR-013 (Credential Store) |
| **Owner** | Executor team |
| **Effort** | 4 days |
| **Verification gate** | Email sent via SMTP and API modes. HTML and plaintext both supported. Delivery report received. Retry on SMTP failure. |
| **Completion criteria** | Email adapter implemented. Unit tests pass (6 tests). |

### EXEC-004: Channel Adapter — Generic API

| Field | Value |
|-------|-------|
| **Description** | Implement generic API channel adapter. HTTP requests (GET, POST, PUT, DELETE). Bearer token, basic auth, API key authentication. Headers, body, timeout configuration. |
| **Dependencies** | INFR-013 (Credential Store) |
| **Owner** | Executor team |
| **Effort** | 4 days |
| **Verification gate** | All HTTP methods supported. All auth types supported. Response handled correctly. Timeout enforced. Retry on 5xx responses. |
| **Completion criteria** | API adapter implemented. Unit tests pass (8 tests). |

### EXEC-005: Execution Engine — Task Dispatch

| Field | Value |
|-------|-------|
| **Description** | Implement execution engine task dispatch. `execute(approved_plan, verdict, context)` → DeliveryResult. Validate approved plan. Resolve credentials per task. Dispatch to correct channel adapter. Collect results. |
| **Dependencies** | EXEC-001 through EXEC-004 (Channel adapters), GOV-006 (Governance verdict) |
| **Owner** | Executor team |
| **Effort** | 5 days |
| **Verification gate** | Approved plan dispatched to correct channel adapter. Credentials resolved before dispatch. Credentials discarded after task completion. Multiple tasks dispatched in sequence. Results collected per task. |
| **Completion criteria** | Task dispatch implemented. Unit tests pass (10 tests). |

### EXEC-006: Execution Failure Handling

| Field | Value |
|-------|-------|
| **Description** | Implement execution failure handling per ES-005 §8. Retry with backoff. Fallback to alternative channel. Partial delivery reporting. Credential resolution failure isolated to that task. Task timeout handling. |
| **Dependencies** | EXEC-005 (Task dispatch — produces deliveries) |
| **Owner** | Executor team |
| **Effort** | 3 days |
| **Verification gate** | Transient failure triggers retry. Persistent failure triggers fallback channel. All channels fail → partial delivery result. Credential failure isolated (other tasks unaffected). Task timeout handled. |
| **Completion criteria** | Failure handling implemented. Unit tests pass (6 tests). |

### EXEC-007: Execution State Machine

| Field | Value |
|-------|-------|
| **Description** | Implement executor state machine: Idle, Receiving_Plan, Validating_Plan, Resolving_Credentials, Dispatching_Tasks, Awaiting_Confirmation, Completed, Partial, Failed. All transitions. |
| **Dependencies** | EXEC-005, EXEC-006 (Execution logic — provides transitions) |
| **Owner** | Executor team |
| **Effort** | 2 days |
| **Verification gate** | All state transitions implemented. Invalid transitions raise error. Terminal states handled correctly. |
| **Completion criteria** | State machine implemented. Unit tests pass (8 tests). |

---

## Phase J — Observer Engine (ES-006)

### OBS-001: Observation Recording

| Field | Value |
|-------|-------|
| **Description** | Implement basic observation recording. `observe(outcome, expected_outcome, context)` → OutcomeObservation. Record: observation_id, observer_id, observed_at, content, confidence, source. 100% of executions produce basic observation. |
| **Dependencies** | EXEC-006 (Execution failure handling — produces DeliveryResult), IKS-003 (KnowledgeEngine — observation storage) |
| **Owner** | Observer team |
| **Effort** | 3 days |
| **Verification gate** | Every execution produces a basic observation record. Observation contains all required fields. Observation stored in KnowledgeEngine. |
| **Completion criteria** | Observation recording implemented. Unit tests pass (5 tests). |

### OBS-002: Discrepancy Detection

| Field | Value |
|-------|-------|
| **Description** | Implement discrepancy detection. Compare actual outcome to expected outcome from plan. Detect: success (match), discrepancy (partial match), anomaly (unexpected outcome). Produce discrepancy score. |
| **Dependencies** | OBS-001 (Observation recording — produces outcome data) |
| **Owner** | Observer team |
| **Effort** | 4 days |
| **Verification gate** | Matching outcome → no discrepancy. Partial match → discrepancy detected with details. Unexpected outcome → anomaly flagged. Discrepancy score computed (0.0 = perfect match, 1.0 = complete mismatch). |
| **Completion criteria** | Discrepancy detection implemented. Unit tests pass (6 tests). |

### OBS-003: Observation Events

| Field | Value |
|-------|-------|
| **Description** | Implement event publishing: `observation.recorded`, `observation.discrepancy.detected`, `observation.anomaly.flagged`. Events use canonical envelope. Consumed by: Knowledge Engine (storage), Learning Engine (analysis). |
| **Dependencies** | OBS-001 (Observation recording), OBS-002 (Discrepancy detection), INFR-010 (Event Bus) |
| **Owner** | Observer team |
| **Effort** | 2 days |
| **Verification gate** | Events published on correct triggers. Events conform to canonical envelope. Events consumed by Knowledge Engine and Learning Engine. |
| **Completion criteria** | Events implemented. Unit tests pass (4 tests). |

---

## Phase K — Learning Engine (ES-007)

### LEARN-001: Outcome Analysis

| Field | Value |
|-------|-------|
| **Description** | Implement outcome analysis. `learn(observations, historical_outcomes)` → LearningSignal. Analyze outcome against expected outcome. Identify patterns across multiple observations. Cold start mode: collect without recommending. |
| **Dependencies** | OBS-003 (Observation events — provides observations) |
| **Owner** | Learning team |
| **Effort** | 6 days |
| **Verification gate** | Outcome analyzed against expected outcome. Patterns identified across multiple observations. Cold start mode: signal collected but not applied. Minimum observation threshold configurable. |
| **Completion criteria** | Outcome analysis implemented. Unit tests pass (8 tests). |

### LEARN-002: Learning Signal Generation

| Field | Value |
|-------|-------|
| **Description** | Implement learning signal generation. LearningSignal: insight, recommendation, knowledge_fact_key, confidence. Signal types: knowledge_improvement, reasoning_refinement, policy_optimization. |
| **Dependencies** | LEARN-001 (Outcome analysis — produces signal data) |
| **Owner** | Learning team |
| **Effort** | 4 days |
| **Verification gate** | All 3 signal types produced correctly. Signal contains insight (human-readable), recommendation (actionable), fact_key (if applicable), confidence (canonical 0.0–1.0). |
| **Completion criteria** | Signal generation implemented. Unit tests pass (6 tests). |

### LEARN-003: Confidence Calibration

| Field | Value |
|-------|-------|
| **Description** | Implement confidence calibration per ES-007 §7. Damping factor to prevent oscillation. Calibration formula with configurable learning_rate. Apply calibration to knowledge_fact and reasoning model updates. |
| **Dependencies** | LEARN-002 (Signal generation — provides signals with confidence) |
| **Owner** | Learning team |
| **Effort** | 4 days |
| **Verification gate** | Confidence calibration formula correct. Damping factor prevents oscillation. Calibration within 0.0–1.0 bounds. Calibration converges over repeated signals. |
| **Completion criteria** | Confidence calibration implemented. Unit tests pass (6 tests). |

### LEARN-004: Governance Integration for Learning Signals

| Field | Value |
|-------|-------|
| **Description** | Implement Governance integration. Learning signals pass through Governance before application. Governance validates signal against policies. Approved signals applied. Rejected signals logged. REVIEW signals flagged for human review. |
| **Dependencies** | LEARN-003 (Signal generation — produces signals), GOV-006 (Governance verdict — signal validation) |
| **Owner** | Learning team |
| **Effort** | 4 days |
| **Verification gate** | Approved signal → applied (KnowledgeEngine updated, reasoning model refined). Rejected signal → logged, not applied. REVIEW signal → flagged for human review. Constitutional: Invariant 4 (Learning never bypasses governance) verified. |
| **Completion criteria** | Governance integration implemented. Unit tests pass (6 tests). |

---

## Phase K (Parallel) — Doctor Engine (ES-008)

### DOC-001: Integrity Checks

| Field | Value |
|-------|-------|
| **Description** | Implement integrity check type. Verify: required packages exist and importable, required files exist, DB tables present, engine modules importable. |
| **Dependencies** | None (checks filesystem, imports, DB — not other engines' APIs) |
| **Owner** | Doctor team |
| **Effort** | 3 days |
| **Verification gate** | Package existence check works. File existence check works. DB table presence check works. Module importability check works. Missing component returns fail. |
| **Completion criteria** | Integrity checks implemented. Unit tests pass (5 tests). |

### DOC-002: Architecture Drift Detection

| Field | Value |
|-------|-------|
| **Description** | Implement architecture drift detection. Compare implementation against frozen architecture. Check: engine modules present, layer boundaries respected, Event Bus subscriptions registered, events published per spec. |
| **Dependencies** | INFR-010 (Event Bus — subscription registry), GOV-007 (Audit trail — compliance reference) |
| **Owner** | Doctor team |
| **Effort** | 4 days |
| **Verification gate** | All engine modules present detected. Missing module flagged as drift. Event subscriptions match spec. Event publications match spec. Layer boundary check verifies no unexpected cross-engine imports. |
| **Completion criteria** | Drift detection implemented. Unit tests pass (6 tests). |

### DOC-003: Package Health Validation

| Field | Value |
|-------|-------|
| **Description** | Implement package health check. Verify: package versions match config, no known vulnerable packages, dependency declarations match installed packages. |
| **Dependencies** | None (checks filesystem, package manager) |
| **Owner** | Doctor team |
| **Effort** | 3 days |
| **Verification gate** | Version match detected correctly. Version mismatch flagged. Vulnerable package detected (if vulnerability database available). Dependency declaration matches installed. |
| **Completion criteria** | Package health implemented. Unit tests pass (4 tests). |

### DOC-004: Compliance Verification

| Field | Value |
|-------|-------|
| **Description** | Implement compliance check. Verify: Governance decisions made for all Executor actions, audit trail complete, constitutional policies evaluated. |
| **Dependencies** | GOV-007 (Audit trail — compliance data) |
| **Owner** | Doctor team |
| **Effort** | 3 days |
| **Verification gate** | All Executor actions have Governance approval verified. Audit trail completeness verified. Constitutional policy evaluation verified. Missing compliance flagged as violation. |
| **Completion criteria** | Compliance check implemented. Unit tests pass (4 tests). |

### DOC-005: Health Aggregation

| Field | Value |
|-------|-------|
| **Description** | Implement health aggregation. Collect health status from all engines. Aggregate into overall health summary. Publish `doctor.health.summary` event. Mark engine as degraded if health data unavailable for 3 consecutive cycles. |
| **Dependencies** | INFR-006 (Health endpoint — engine health data) |
| **Owner** | Doctor team |
| **Effort** | 3 days |
| **Verification gate** | All engine health data collected. Overall health computed correctly. Degraded after 3 missing reports. Health summary published as event. |
| **Completion criteria** | Health aggregation implemented. Unit tests pass (4 tests). |

### DOC-006: DoctorReport and Events

| Field | Value |
|-------|-------|
| **Description** | Implement DoctorReport assembly. Combine all check results into structured report. Publish `doctor.check.completed` and `doctor.violation.detected` events on Event Bus. |
| **Dependencies** | DOC-001 through DOC-005 (All check types), INFR-010 (Event Bus) |
| **Owner** | Doctor team |
| **Effort** | 2 days |
| **Verification gate** | DoctorReport contains all check results. Events published on check completion and violation detection. Events conform to canonical envelope. |
| **Completion criteria** | Report and events implemented. Unit tests pass (4 tests). |

---

## Phase M — KnowledgeLayer Retirement (ADR-002 Phase 3–4)

### RET-001: Cutover to IKS (ADR-002 Phase 3)

| Field | Value |
|-------|-------|
| **Description** | Switch KnowledgeEngine facade to IKS-primary mode. IKS is authoritative source. KnowledgeLayer fallback only for unmigrated fact keys. Freeze KnowledgeLayer data source (no more markdown file updates accepted). |
| **Dependencies** | IKS-003 (KnowledgeEngine facade), IKS-008 (Fallback verification) |
| **Owner** | Knowledge team |
| **Effort** | 2 days |
| **Verification gate** | IKS returns all migrated facts correctly. KnowledgeLayer fallback used only for unmigrated keys. No data loss (all previously KnowledgeLayer-sourced paths return through IKS). |
| **Completion criteria** | Cutover verified. Integration tests pass (6 tests). |

### RET-002: Verify No KnowledgeLayer Dependencies

| Field | Value |
|-------|-------|
| **Description** | Audit all code paths for KnowledgeLayer imports. Search for `from app.shunya.knowledge import KnowledgeLayer`, `from .knowledge import KnowledgeLayer`, `KnowledgeLayer(`. Confirm zero remaining imports. |
| **Dependencies** | RET-001 (Cutover to IKS) |
| **Owner** | Knowledge team |
| **Effort** | 1 day |
| **Verification gate** | Code search returns zero KnowledgeLayer import paths. CI fails if any import path found. |
| **Completion criteria** | Audit confirmed. No KnowledgeLayer imports remain. |

### RET-003: Remove KnowledgeLayer (ADR-002 Phase 4)

| Field | Value |
|-------|-------|
| **Description** | Remove KnowledgeLayer class. Remove markdown KB file (`knowledge-base.md`). Remove KnowledgeLayer-specific tests. Remove legacy wrapper. |
| **Dependencies** | RET-002 (No KnowledgeLayer dependencies) |
| **Owner** | Knowledge team |
| **Effort** | 1 day |
| **Verification gate** | KnowledgeLayer code removed. All tests pass without KnowledgeLayer. Knowledge-base.md archived (not deleted — moved to `docs/implementation/`). |
| **Completion criteria** | KnowledgeLayer removed. Full test suite passes. |

### RET-004: End-to-End Verification

| Field | Value |
|-------|-------|
| **Description** | Verify that all 5 previously KnowledgeLayer-dependent paths function through IKS via KnowledgeEngine. End-to-end test: routes → workflow → facade → IKS. |
| **Dependencies** | RET-003 (KnowledgeLayer removed) |
| **Owner** | Knowledge team |
| **Effort** | 2 days |
| **Verification gate** | All 5 call sites return correct data. Data matches pre-migration expectations. Performance is comparable or better. |
| **Completion criteria** | End-to-end verification passes. Integration tests pass (5 tests). |

---

## Phase N — Integration & Hardening

### INT-001: Full Pipeline Integration Test

| Field | Value |
|-------|-------|
| **Description** | Implement full pipeline end-to-end test: External Trigger → Observation → Knowledge Resolution → Context Fusion → Reasoning → Planning → Governance → Execution → Observation → Knowledge Update → Learning → Continuous Improvement. |
| **Dependencies** | All engine phases (D through K) complete, all infrastructure phases (A–B) complete |
| **Owner** | Integration team |
| **Effort** | 5 days |
| **Verification gate** | Full pipeline test passes end-to-end. Test covers both success and failure paths. Each lifecycle stage verified. |
| **Completion criteria** | Full pipeline test implemented and passing (1 test, multi-scenario). |

### INT-002: Constitutional Invariant CI Pipeline

| Field | Value |
|-------|-------|
| **Description** | Implement CI pipeline for all 26 architectural invariants. Each invariant has an automated test. CI fails if any invariant test fails. Invariant tests run on every PR. |
| **Dependencies** | INT-001 (Full pipeline — exercises all invariants) |
| **Owner** | Integration team |
| **Effort** | 4 days |
| **Verification gate** | All 26 invariant tests pass. CI configured to fail on invariant violation. Test names match invariant numbers (e.g., test_invariant_8_identity_globally_unique). |
| **Completion criteria** | Constitutional CI pipeline operational. 26 tests running in CI. |

### INT-003: Performance Benchmarks

| Field | Value |
|-------|-------|
| **Description** | Implement performance benchmark suite. Per-engine latency (p50, p99). Throughput. Memory usage. Compare against engine specification targets. Fail if any engine exceeds budget. |
| **Dependencies** | INT-001 (Full pipeline — provides realistic load), all engine phases complete |
| **Owner** | Integration team |
| **Effort** | 5 days |
| **Verification gate** | All engine latency within budget (p50 and p99 per spec). Throughput meets minimum targets. Memory within budget. Benchmark results reported. |
| **Completion criteria** | Performance benchmarks implemented. Results within spec. |

### INT-004: Architecture Checkpoint

| Field | Value |
|-------|-------|
| **Description** | Run architecture compliance scan. Compare implementation against frozen architecture. Check: all engines exist, all API contracts match specs, all SHALL NEVER enforced, all events match specs, all invariants enforced. |
| **Dependencies** | INT-002 (Constitutional CI), INT-003 (Performance) |
| **Owner** | Chief Software Architect |
| **Effort** | 3 days |
| **Verification gate** | Zero divergence between implementation and frozen architecture confirmed. All engine specifications satisfied. ADR compliance confirmed. |
| **Completion criteria** | Architecture checkpoint passed. Divergence report: zero items. |

---

## Phase O — Release

### REL-001: Operations Runbook

| Field | Value |
|-------|-------|
| **Description** | Create operations runbook: startup sequence, health check interpretation, common failure modes and recovery, database backup/restore, Event Bus dead-letter replay, Credential Store key rotation, KnowledgeEngine fact recovery. |
| **Dependencies** | INT-004 (Architecture checkpoint) |
| **Owner** | Infrastructure team |
| **Effort** | 3 days |
| **Verification gate** | Runbook verified by walkthrough. Each recovery procedure executable from runbook. |
| **Completion criteria** | Runbook published. Walkthrough completed. |

### REL-002: Security Audit

| Field | Value |
|-------|-------|
| **Description** | Perform security audit: credential handling review, tenant isolation verification, input validation audit, event payload inspection for credentials/PII, SHALL NEVER enforcement audit. |
| **Dependencies** | INT-004 (Architecture checkpoint) |
| **Owner** | Infrastructure team |
| **Effort** | 3 days |
| **Verification gate** | Zero critical or high findings. Medium findings documented with remediation plan. |
| **Completion criteria** | Security audit passed. Findings documented. |

### REL-003: Deployment

| Field | Value |
|-------|-------|
| **Description** | Deploy to production (Contabo VPS). Run database migrations. Verify health endpoint. Run smoke tests. Confirm all engines operational. |
| **Dependencies** | REL-001 (Runbook), REL-002 (Security audit) |
| **Owner** | Infrastructure team |
| **Effort** | 1 day |
| **Verification gate** | Deployment completes without error. Health endpoint reports all engines healthy. Smoke tests pass. |
| **Completion criteria** | Production deployment operational. |

### REL-004: Release Sign-Off

| Field | Value |
|-------|-------|
| **Description** | Release sign-off by Chief Software Architect (engineering compliance) and Chief Constitutional Architect (constitutional compliance). Release notes published. |
| **Dependencies** | REL-003 (Deployment) |
| **Owner** | Chief Software Architect / Chief Constitutional Architect |
| **Effort** | 1 day |
| **Verification gate** | Both sign-offs obtained. Release notes complete. |
| **Completion criteria** | Release approved. |

---

## Backlog Summary

| Phase | Task Count | Total Effort (days) | Dependencies (inbound) |
|-------|-----------|---------------------|----------------------|
| A — Foundation | 6 | 15 | 0 |
| B — Event Bus & Credential Store | 8 | 27 | 5 (to Phase A) |
| C — Knowledge Store Transition | 8 | 25 | 2 (to Phase B) |
| D — Identity Engine | 6 | 19 | 2 (to Phase B, C) |
| E — Context Fusion | 8 | 20 | 3 (to Phase B, C, D) |
| F — Reasoning | 5 | 21 | 2 (to Phase C, E) |
| G — Planner | 3 | 11 | 2 (to Phase E, F) |
| H — Governance | 8 | 29 | 4 (to Phase C, E, G) |
| I — Executor | 7 | 26 | 3 (to Phase B, E, H) |
| J — Observer | 3 | 9 | 3 (to Phase C, E, I) |
| K — Learning | 4 | 18 | 4 (to Phase C, E, H, J) |
| K (parallel) — Doctor | 6 | 18 | 2 (to Phase B, H) |
| M — KnowledgeLayer Retirement | 4 | 6 | 1 (to Phase C) |
| N — Integration & Hardening | 4 | 17 | 8 (all phases) |
| O — Release | 4 | 8 | 1 (to Phase N) |
| **Total** | **84** | **269** | |

*Note: Effort estimates are engineering days, not calendar days. Parallelizable work will reduce calendar duration.*

---

*End of SHUNYA_PROGRAM_BACKLOG.md*