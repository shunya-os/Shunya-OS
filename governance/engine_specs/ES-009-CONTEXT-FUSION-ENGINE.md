# ES-009: Context Fusion Engine

**Status:** Draft
**Phase:** Phase 10
**Layer:** Context Fusion
**Author:** Chief Software Architect
**Date:** 2026-07-18
**Approver:** (filled on approval)

---

## Section 0 — Compounding Intelligence Position

### What Enters This Engine

- **Context request** — from any pipeline engine: tenant_id, actor_id, purpose_code, subject_id, current_object_ref
- **Source provider data** — identity resolutions, relationship records, conversations, human context, memory items, evidence records, document references
- **Eligibility decisions** — from Phase 4 (Privacy): purpose-based eligibility gates

### What Leaves This Engine

- **WorkspaceContext** — a bounded, fingerprinted set of context items with inclusion/exclusion reasons and budget enforcement
- **Fingerprints** — cryptographic hashes enabling cache invalidation and change detection

### What Intelligence Is Compounded

Context Fusion itself does not learn or improve — it is a deterministic assembly pipeline. However, the quality of context directly affects the quality of reasoning, planning, governance, execution, observation, and learning. Better context enables better decisions downstream.

The compounding mechanism is indirect: as the source providers (identity, memory, evidence) compound intelligence through their own lifecycles, the context that Context Fusion assembles becomes progressively richer, more complete, and more relevant. The assembly pipeline itself does not change — the inputs improve over time.

### Which Downstream Engines Depend Upon It

| Engine | Dependency | Criticality |
|--------|-----------|-------------|
| Reasoning Engine (ES-003) | Reads workspace context for evidence-grounded reasoning | **High** — reduced quality without context |
| Planner Engine (ES-004) | Reads workspace context for constraint-aware planning | **Medium** — can plan with degraded context |
| Governance Engine (ES-001) | Reads workspace context for policy evaluation | **Medium** — policies can partially evaluate without context |
| Executor Engine (ES-005) | Reads workspace context for execution | **Medium** — can execute with degraded context |
| Observer Engine (ES-006) | Reads workspace context for observation | **Low** — observation is independent of context |
| Learning Engine (ES-007) | Reads workspace context for pattern analysis | **Low** — learning can proceed without full context |
| Knowledge Engine (ES-002) | Provides workspace context items to Context Fusion | **Medium** — Context Fusion reads from Knowledge |

**Total: 6 of 7 pipeline engines depend on Context Fusion. It is the most-depended-upon engine in the architecture.**

### What Fails If This Engine Becomes Unavailable

- **Reasoning is blind** — no workspace context for evidence-grounded inference
- **Planning is unconstrained** — no awareness of actor, relationships, or domain restrictions
- **Governance is uninformed** — cannot evaluate policies that depend on context enrichment
- **Execution is context-free** — no workspace, tenant, or actor awareness
- **Observation lacks provenance** — cannot associate observations with their originating context
- **Learning lacks scope** — cannot analyze patterns within workspace boundaries

---

## 1. Objective

### Mission

Context Fusion assembles a bounded workspace context from all source providers — identity, relationships, conversations, human context, memory, evidence, and documents — applying purpose-based eligibility gates and budget enforcement before delivering the context to downstream engines.

### Why It Exists

The SHUNYA System Flow (§2 — Canonical Lifecycle) defines Context Fusion as a required stage between Knowledge Resolution and Reasoning. Without a dedicated engine for context assembly, each downstream engine would need to independently resolve identity, relationships, memory, and evidence from disparate source providers — duplicating logic, violating single responsibility, and creating inconsistent workspace boundaries.

Context Fusion exists to:
1. Centralize context assembly — one engine owns the process
2. Enforce constitutional eligibility gates — Phase 4 (Privacy) before context release
3. Guarantee workspace boundaries — context never leaks across workspaces
4. Provide a bounded, fingerprinted context — downstream engines receive only what they need

### Architectural Responsibility

Context Fusion owns the **workspace context lifecycle** within the Compounding Intelligence Loop. It does not reason, execute, govern, learn, or observe — it assembles and delivers context.

Position in the pipeline (SHUNYA_SYSTEM_FLOW.md §2):

```
Knowledge Resolution → [Context Fusion] → Reasoning
                                              │
                                         Planning
                                              │
                                        Governance
                                              │
                                        Executor
                                              │
                                        Observer
                                              │
                                        Learning
```

---

## 2. Scope

### In Scope

- Assemble bounded workspace context from all source providers
- Integrate identity resolution (from Identity Engine) as a source provider
- Integrate relationship records, conversations, human context, memory, evidence, and documents as source providers
- Apply purpose-based eligibility gates (Phase 4 — Privacy) before context release
- Enforce budget limits per context request (number of items, total size)
- Compute fingerprints for change detection and cache invalidation
- Return degraded context with documented exclusion reasons when sources are unavailable
- Serve context requests from all pipeline engines (Reasoning, Planner, Governance, Executor, Observer, Learning)

### Out of Scope

- **Never reason about context content.** Context Fusion assembles context — it does not analyze or interpret it.
- **Never modify source data.** Context Fusion reads from source providers — it does not write back.
- **Never govern context access.** Eligibility gates are enforced by Phase 4 (Privacy) — Context Fusion calls the gate, it does not set policy.
- **Never learn from context patterns.** Pattern analysis belongs to the Learning Engine.
- **Never store workspace context durably.** Context is assembled on-demand and delivered transiently.
- **Never perform identity resolution.** Identity resolution belongs to the Identity Engine.
- **Never manage relationship graphs.** Relationship management belongs to the Relationship Engine.

---

## 3. Dependencies

### Internal Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| Identity Engine (ES-010) | Input | Resolves persons to canonical identities for context assembly |
| Knowledge Engine (ES-002) | Input | Provides evidence, memory, and document facts for context |
| Relationship Engine (ES-NNN, planned) | Input | Provides relationship records (person-to-person, person-to-entity) |
| Phase 4 (Privacy) | Protocol | Purpose-based eligibility gate — determines whether context items may be released |
| Source providers (Phase 5, 6, 7, 7A) | Input | Conversations, human context, and other source data |

### External Dependencies

- None. Context Fusion is a computation-only engine with no external API calls.

---

## 4. Inputs

### Input Contract

```
ContextRequest:
  tenant_id: integer              — Owning tenant
  actor_id: uuid                  — The person or engine requesting context
  purpose_code: string            — Purpose classification for eligibility gating
  subject_id: uuid | null         — Subject of the context request (may be same as actor)
  current_object_ref: string | null — Current object or workspace reference
  max_items: integer              — Maximum number of context items to return (budget)
  timeout_ms: integer             — Maximum wait time for source provider resolution

SourceProviderInput:
  identity: ResolutionResult[]    — Identity resolutions for actor and subject
  relationships: Relationship[]   — Relationship records scoped to the workspace
  conversations: Conversation[]   — Recent conversation history
  human_context: HumanContext[]   — Actor preferences, settings, state
  memory: KnowledgeFact[]         — Memory items from the Knowledge Engine
  evidence: Evidence[]            — Evidence chains relevant to the context
  documents: Document[]           — Documents referenced in the workspace
```

### Input Sources

| Source | Type | Trigger |
|--------|------|---------|
| Pipeline engines (ES-003 through ES-007) | API call | On context request from any downstream engine |
| Identity Engine (ES-010) | API call (read) | On identity resolution need during context assembly |
| Knowledge Engine (ES-002) | API call (read) | On memory, evidence, or document retrieval |
| Phase 4 (Privacy) | API call | On each source provider section before assembly |
| Source provider queues | Event stream | On source provider data availability |

### Input Validation

| Field | Constraint | Default | Rejection |
|-------|-----------|---------|-----------|
| `tenant_id` | Must be positive integer | None (required) | `MISSING_TENANT` |
| `actor_id` | Must be valid UUID | None (required) | `MISSING_ACTOR` |
| `purpose_code` | Must be a recognized purpose code | None (required) | `INVALID_PURPOSE` |
| `max_items` | Must be 1–1000 | 100 | Clamped to range |
| `timeout_ms` | Must be 100–30000 | 5000 | Clamped to range |

---

## 5. Outputs

### Output Contract

```
WorkspaceContext:
  context_id: string              — Unique identifier for this context assembly
  tenant_id: integer              — Owning tenant
  actor_id: uuid                  — The requesting actor
  subject_id: uuid | null         — The context subject
  purpose_code: string            — Purpose used for eligibility gating
  fingerprint: string             — Cryptographic hash of context content
  assembled_at: datetime          — When context was assembled
  budget: BudgetReport            — Item count and size vs limits
  sections: ContextSection[]
  is_degraded: boolean            — True if any source provider was unavailable

ContextSection:
  source: string                  — Source provider name ("identity", "memory", "evidence", etc.)
  items: ContextItem[]
  eligibility: EligibilityResult  — Phase 4 gate result (allowed, blocked, degraded)
  is_degraded: boolean            — True if this section could not be fully assembled

ContextItem:
  id: string                      — Item identifier
  type: string                    — Item type (person, fact, evidence, document, etc.)
  value: any                      — Item data (typed per source provider)
  confidence: float               — Canonical confidence score (0.0–1.0)
  provenance: Provenance          — Origin and modification history
  included: boolean               — True if included, false if excluded
  exclusion_reason: string | null — Why this item was excluded (if included=false)

BudgetReport:
  total_items: integer            — Number of items in the assembled context
  max_items: integer              — Maximum allowed items
  total_size_bytes: integer       — Total serialized size
  max_size_bytes: integer         — Maximum allowed size
  truncated: boolean              — True if context was truncated to fit budget

EligibilityResult:
  purpose_code: string            — The purpose code checked
  allowed: boolean                — True if eligible
  gate: string                    — Which gate produced this result ("identity", "memory", etc.)
  reason: string                  — Human-readable explanation
```

### Output Destinations

| Destination | Consumer | Delivery Guarantee |
|-------------|----------|-------------------|
| Reasoning Engine (ES-003) | WorkspaceContext for evidence-grounded reasoning | Best-effort |
| Planner Engine (ES-004) | WorkspaceContext for constraint-aware planning | Best-effort |
| Governance Engine (ES-001) | WorkspaceContext for policy evaluation | Best-effort |
| Executor Engine (ES-005) | WorkspaceContext for execution | Best-effort |
| Observer Engine (ES-006) | WorkspaceContext for observation | Best-effort |
| Learning Engine (ES-007) | WorkspaceContext for pattern analysis | Best-effort |

### Output Guarantees

- **Determinism:** Same context request with same source provider data always produces the same WorkspaceContext.
- **Bounded output:** Context never exceeds `max_items` or budget limits.
- **Degradation explicitness:** Every degraded section is documented with exclusion reasons.
- **Fingerprinted:** Every WorkspaceContext carries a fingerprint for change detection.
- **No mutation:** Context Fusion never writes to source providers.

---

## 6. State Machine

### States

```
Idle
 │
 │ [context_request_received]
 ▼
Resolving_Identity
 │
 ├──[identity_resolved]──→ Collecting_Source_Data
 │
 └──[identity_ambiguous]──→ Error
 │
Collecting_Source_Data
 │
 ├──[all_sources_collected]──→ Applying_Eligibility_Gates
 │
 └──[source_timeout]──→ Applying_Eligibility_Gates (degraded)
 │
Applying_Eligibility_Gates
 │
 ├──[all_allowed]──→ Enforcing_Budget
 │
 └──[some_denied]──→ Enforcing_Budget (with exclusions)
 │
Enforcing_Budget
 │
 ├──[within_budget]──→ Computing_Fingerprint
 │
 └──[over_budget]──→ Truncating → Computing_Fingerprint
 │
Computing_Fingerprint
 │
 └──[fingerprint_computed]──→ Delivering_Context
 │
Delivering_Context ──[context_delivered]──→ Idle
 │
Error ──[error_logged]──→ Idle
```

### State Definitions

| State | Meaning | Is Terminal? |
|-------|---------|-------------|
| Idle | Waiting for a context request | No |
| Resolving_Identity | Resolving actor and subject identities via Identity Engine | No |
| Collecting_Source_Data | Retrieving data from all source providers | No |
| Applying_Eligibility_Gates | Checking Phase 4 eligibility for each context section | No |
| Enforcing_Budget | Truncating or limiting context to fit budget constraints | No |
| Computing_Fingerprint | Generating a cryptographic hash of the assembled context | No |
| Delivering_Context | Returning the assembled WorkspaceContext to the requester | No |
| Error | Processing failed before context could be delivered | Yes |

### Transition Table

| From State | Event | Condition | To State | Action |
|------------|-------|-----------|----------|--------|
| Idle | context_request_received | Request validated | Resolving_Identity | Begin identity resolution |
| Resolving_Identity | identity_resolved | Actor and subject identities resolved | Collecting_Source_Data | Begin source data retrieval |
| Resolving_Identity | identity_ambiguous | Identity Engine returns AMBIGUOUS | Error | Log ambiguous identity error |
| Collecting_Source_Data | all_sources_collected | All providers responded | Applying_Eligibility_Gates | Begin eligibility checks |
| Collecting_Source_Data | source_timeout | One or more providers timed out | Applying_Eligibility_Gates | Flag degraded sections |
| Applying_Eligibility_Gates | all_allowed | All sections pass Phase 4 gates | Enforcing_Budget | Apply budget limits |
| Applying_Eligibility_Gates | some_denied | One or more sections blocked | Enforcing_Budget | Mark excluded items with reasons |
| Enforcing_Budget | within_budget | Item count and size within limits | Computing_Fingerprint | Compute context fingerprint |
| Enforcing_Budget | over_budget | Item count or size exceeds limits | Truncating | Truncate to fit budget |
| Computing_Fingerprint | fingerprint_computed | Hash generated | Delivering_Context | Return WorkspaceContext |
| Delivering_Context | context_delivered | Context returned to requester | Idle | Log completion |
| Error | error_logged | Error recorded | Idle | Log completion |

---

## 7. Events

### Events Consumed

| Event | Source | Payload | Action Taken |
|-------|--------|---------|-------------|
| `workspace.context.requested` | Any pipeline engine | `{tenant_id, actor_id, purpose_code, subject_id, current_object_ref}` | Begin context assembly (if not direct API call) |
| `source.provider.updated` | Source provider (Phase 4–7) | `{provider_type, tenant_id, workspace_id}` | Invalidate cache for affected workspace |
| `identity.resolved` | Identity Engine (ES-010) | `{actor_id, person_id, resolution_result}` | Update identity data for in-flight request |
| `knowledge.fact.created` | Knowledge Engine (ES-002) | `{fact_key, version}` | Invalidate memory/evidence section cache |
| `knowledge.fact.superseded` | Knowledge Engine (ES-002) | `{fact_key, old_version, new_version}` | Invalidate memory/evidence section cache |

### Events Produced

| Event | Destination | Payload | Trigger Condition |
|-------|-------------|---------|-------------------|
| `context.fusion.completed` | Requesting engine, Event Bus | `{context_id, tenant_id, actor_id, purpose_code, fingerprint, is_degraded}` | Context assembled and delivered |
| `context.fusion.section.degraded` | Requesting engine | `{context_id, section, reason}` | A source provider was unavailable |
| `context.fusion.eligibility.denied` | Governance Engine, Alerting | `{context_id, section, purpose_code, reason}` | Phase 4 gate blocked a section |

---

## 8. Failure Modes

| Failure Mode | Cause | Detection | Effect | Recovery |
|--------------|-------|-----------|--------|----------|
| Source provider unavailable | Provider outage | Timeout | Return empty section with degradation flag | Retry on next context request |
| Identity ambiguous | Identity Engine returns AMBIGUOUS | API response | Return error — cannot assemble context without identity | Require human identity resolution |
| Phase 4 gate blocks eligibility | Privacy gate denies access | API response | Exclude section with documented reason | Return degraded context |
| Budget exceeded | Max item count or size reached | Budget check | Truncate context; flag as truncated | Requester may request with higher budget |
| Source provider timeout | Provider exceeds per-provider timeout | Timer | Return partial section with degradation flag | Retry; flag missing section |
| Fingerprint collision | Different contexts produce same hash | Post-assembly comparison (extremely rare) | Accept — probabilistic guarantee | None required |
| All sources unavailable | Complete provider outage | Timeout on all providers | Return empty context with all sections degraded | Retry on next request |

---

## 9. Observability

### Logging

| Event | Log Level | Data | Privacy Constraint |
|-------|-----------|------|-------------------|
| Context request received | INFO | context_id, tenant_id, actor_id, purpose_code | No personal data |
| Identity resolution | DEBUG | context_id, resolution_result | No personal data |
| Source provider call | DEBUG | context_id, provider, status, duration_ms | None |
| Eligibility gate result | INFO | context_id, section, allowed, gate | No personal data |
| Budget enforcement | INFO | context_id, total_items, max_items, truncated | None |
| Context delivered | INFO | context_id, is_degraded, section_count, duration_ms | No personal data |
| Source unavailable | WARN | context_id, provider, error | None |
| Eligibility denied | WARN | context_id, section, purpose_code, reason | No personal data |
| Assembly error | ERROR | context_id, error_detail | No personal data |

### Tracing

- **Span: `context_fusion.assemble`** — Full context assembly lifecycle
  - Child span: `context_fusion.resolve_identity` — Identity resolution phase
  - Child span: `context_fusion.collect_provider` — Per-source-provider collection
  - Child span: `context_fusion.gate_eligibility` — Phase 4 gate check phase
  - Child span: `context_fusion.enforce_budget` — Budget enforcement phase
  - Child span: `context_fusion.fingerprint` — Fingerprint computation phase
- context_id propagated as a trace tag
- correlation_id propagated from the originating engine

### Alerting

| Condition | Severity | Threshold |
|-----------|----------|-----------|
| All source providers unavailable | Pager | Per request |
| Identity resolution failure rate > 5% | Pager | Per minute |
| Any section degraded for > 3 consecutive requests | Ticket | Per provider |
| p99 latency > 2s | Ticket | Per minute |

---

## 10. Metrics

| Metric | Type | Unit | Target | Measurement |
|--------|------|------|--------|-------------|
| `context_fusion.requests_total` | Counter | requests | N/A | Per second, by requesting engine |
| `context_fusion.degraded_total` | Counter | requests | < 1% | Per second |
| `context_fusion.eligibility_denied_total` | Counter | denials | N/A | Per section, per purpose_code |
| `context_fusion.truncated_total` | Counter | truncations | < 5% | Per hour |
| `context_fusion.latency_p50` | Histogram | ms | < 100ms | Per request |
| `context_fusion.latency_p99` | Histogram | ms | < 500ms | Per request |
| `context_fusion.context_size_p50` | Histogram | items | < 50 | Per request |
| `context_fusion.context_size_p99` | Histogram | items | < 200 | Per request |
| `context_fusion.provider_latency_p99` | Histogram | ms | < 200ms | Per provider |

---

## 11. Rollback Strategy

### Rollback Triggers

- Context Fusion produces incorrect WorkspaceContext (wrong identity, missing sections, incorrect eligibility)
- Performance degradation causes timeout cascades to downstream engines
- Memory leak from cached fingerprint data

### Rollback Procedure

1. **Stop accepting new context requests:** Block at the API boundary.
2. **Drain in-flight:** Allow current assembly to complete.
3. **Restore previous version:** Deploy the previous version of Context Fusion.
4. **Verify:** Request a known test context; confirm it matches expected output.
5. **Resume:** Accept new context requests.

### Rollback Limitations

- Context already delivered cannot be recalled. Downstream engines that received incorrect context must handle their own recovery.
- Fingerprint cache is ephemeral and is rebuilt on restart. No data loss.

---

## 12. Migration Strategy (when applicable)

### Migration Type

Configuration migration — source provider connection configurations, budget limits, eligibility gate configurations.

### Migration Steps

1. **Pre-migration validation:** Verify that all source providers are reachable with the new configuration.
2. **Shadow requests (if applicable):** Run a percentage of context requests through both old and new configurations, compare outputs.
3. **Cutover:** Switch from old configuration to new configuration.
4. **Post-migration verification:** Confirm all downstream engines receive valid WorkspaceContext.

### Rollback During Migration

- Point-in-time: Configuration snapshot before migration.
- Data consistency: WorkspaceContext is ephemeral — no persistent state is affected.

---

## 13. Verification

### Unit Tests

- State transitions: 9 tests (one per transition in the transition table)
- Error handling: 6 tests (one per failure mode)
- Edge cases: 10 tests (empty context, all-provider-timeout, mixed-degraded, budget-overflow, identity-ambiguous, all-sections-denied, single-section-request, cross-workspace request, malformed purpose code, fingerprint collision)

### Integration Tests

- Integration with Identity Engine: 4 tests (identity resolved, identity ambiguous, identity timeout, multiple identities)
- Integration with Knowledge Engine: 3 tests (memory retrieval, evidence retrieval, document retrieval)
- Integration with Phase 4 (Privacy): 3 tests (all allowed, some denied, gate unavailable)
- Integration with Reasoning Engine: 3 tests (context delivered, context degraded, context error)

### Security Review

- [ ] No eval/exec patterns
- [ ] No credential leakage — Context Fusion never accesses credentials
- [ ] No write access to source providers — read-only reads, no mutations
- [ ] Input validation — context request fields validated before processing
- [ ] Output sanitization — eligibility denial reasons do not expose internal policy details

### Performance

- Latency budget: 100ms p50, 500ms p99 per context request
- Memory budget: 256MB steady-state, 512MB peak
- Concurrent capacity: 50 context assemblies/second per instance
- Per-context budget: max 1000 items, max 1MB serialized

---

## 14. Security

### Tenant Isolation

Every WorkspaceContext is scoped to a single tenant. Source providers are queried with tenant_id isolation. Context Fusion never returns data from one tenant in response to a request from another tenant.

### Workspace Isolation

Context Fusion respects workspace boundaries (SHUNYA_SYSTEM_FLOW.md §9). Objects are only returned if they belong to the requesting workspace or an ancestor workspace with upward traversal authorization.

### Eligibility Gates

Phase 4 (Privacy) eligibility gates are enforced before any context item is included. Purpose codes classify every request. Items for which the purpose is not authorized are excluded with documented reasons.

### No Credential Access

Context Fusion never reads:
- API tokens or secrets
- Database passwords
- Encryption keys
- Credential references

It has no access to the Credential Store.

---

## 15. Constitutional Mapping

| Responsibility | Constitutional Principle | Source |
|---------------|------------------------|--------|
| Assemble bounded workspace context | §2 — Canonical Lifecycle (Context Fusion stage) | SHUNYA_SYSTEM_FLOW.md §2 |
| Apply purpose-based eligibility gates | §12 — Privacy | SHUNYA_SYSTEM_FLOW.md §12 |
| Respect workspace boundaries | §9 — Workspace Isolation | SHUNYA_SYSTEM_FLOW.md §9 |
| Enforce budget limits | §2 — Context Fusion stage (budget enforcement) | SHUNYA_SYSTEM_FLOW.md §2 |
| Return degraded context with exclusion reasons | §12 — Degradation is explicit (Invariant 12) | SHUNYA_SYSTEM_FLOW.md §14 |
| Never reason about context content | §3 — Context Fusion Engine SHALL NEVER | SHUNYA_SYSTEM_FLOW.md §3 |
| Never modify source data | §10 — Write Ownership | SHUNYA_CORE_MODELS.md §10 |

---

## 16. Layer Responsibilities

### What the Context Fusion Engine Does

- Assembles bounded workspace context from identity, relationships, conversations, human context, memory, evidence, and documents
- Resolves identity through the Identity Engine
- Applies Phase 4 eligibility gates per section
- Enforces budget limits (item count, size)
- Computes fingerprints for change detection
- Returns degraded context with documented exclusion reasons
- Serves 6 downstream pipeline engines

### What the Context Fusion Engine May Never Do

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never reason about context content | Would violate Layer Boundaries | Reasoning Engine |
| Never modify source data | Would violate Write Ownership | Source providers (their own stores) |
| Never govern context access | Would violate Separation of Responsibilities | Phase 4 (Privacy) / Governance Engine |
| Never learn from context patterns | Would violate Layer Boundaries | Learning Engine |
| Never store context durably | Would violate on-demand assembly principle | Knowledge Engine (for persistent facts) |
| Never resolve identities | Would violate Separation of Responsibilities | Identity Engine |
| Never manage relationships | Would violate Layer Boundaries | Relationship Engine |

---

## 17. Future Extensions

### 17.1 Proactive Context Prefetching

Pre-assembling context for anticipated requests based on user behavior patterns — reducing perceived latency for common workflows.

### 17.2 Context Cache with Invalidation

Caching WorkspaceContext by fingerprint with TTL-based and event-driven invalidation — reducing assembly overhead for identical or overlapping context requests.

### 17.3 Incremental Context Updates

Delivering incremental context updates (deltas) instead of full context assemblies when only a subset of source providers have changed — reducing bandwidth and processing time.

### 17.4 Cross-Workspace Context Requests

Supporting context requests that span multiple workspaces with explicit authorization — enabling cross-team collaboration within a tenant.

### 17.5 Source Provider Priority and SLA

Defining priority levels per source provider and per section — ensuring that critical sections (e.g., identity) are delivered before less critical ones (e.g., document references).

---

## 18. References

- [SHUNYA_ARCHITECTURE.md](/SHUNYA_ARCHITECTURE.md) — Sections 2.6 (Continuous Surface), 6.3 (Least Authority)
- [SHUNYA_SYSTEM_FLOW.md](/architecture/SHUNYA_SYSTEM_FLOW.md) — Section 2 (Canonical Lifecycle — Context Fusion stage), 3 (Context Fusion Engine), 9 (Workspace Isolation)
- [SHUNYA_CORE_MODELS.md](/architecture/SHUNYA_CORE_MODELS.md) — Section 3 (Identity Model), Section 5 (Evidence Model), Section 8 (Event Envelope), Section 10 (Interaction Principles), Section 12 (Glossary)
- [SHUNYA_ENGINEERING_CONSTITUTION.md](/governance/SHUNYA_ENGINEERING_CONSTITUTION.md) — Articles 1, 3
- [ARCHITECTURE_BASELINE_REVIEW.md](/architecture/ARCHITECTURE_BASELINE_REVIEW.md) — M7 (Missing Engine Spec), ADR-005, Ownership Matrix, Dependency Matrix
- [ES-001: Governance Engine](/governance/engine_specs/ES-001-GOVERNANCE-ENGINE.md) — References Phase 10/Context Fusion
- [ES-002: Knowledge Engine](/governance/engine_specs/ES-002-KNOWLEDGE-ENGINE.md) — Provides workspace context items to Context Fusion
- [ES-003: Reasoning Engine](/governance/engine_specs/ES-003-REASONING-ENGINE.md) — Reads workspace context from Context Fusion
- [ES-004: Planner Engine](/governance/engine_specs/ES-004-PLANNER-ENGINE.md) — Reads workspace context from Context Fusion
- [ES-005: Executor Engine](/governance/engine_specs/ES-005-EXECUTOR-ENGINE.md) — Reads workspace context from Context Fusion
- [ES-006: Observer Engine](/governance/engine_specs/ES-006-OBSERVER-ENGINE.md) — Reads workspace context from Context Fusion
- [ES-007: Learning Engine](/governance/engine_specs/ES-007-LEARNING-ENGINE.md) — Reads workspace context from Context Fusion
- [ENGINE_SPEC_TEMPLATE.md](/governance/engine_specs/ENGINE_SPEC_TEMPLATE.md) — Specification template
- `app/context/__init__.py` — Current computation-only implementation (334 lines)