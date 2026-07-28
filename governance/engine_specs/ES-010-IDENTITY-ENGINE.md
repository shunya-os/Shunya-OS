# ES-010: Identity Engine

**Status:** Draft
**Phase:** Phase 10 (pre-Context Fusion)
**Layer:** Identity
**Author:** Chief Software Architect
**Date:** 2026-07-18
**Approver:** (filled on approval)

---

## Section 0 — Compounding Intelligence Position

### What Enters This Engine

- **Identity claims** — raw identity data from multiple sources: email addresses, phone numbers, channel IDs (WhatsApp, Telegram), document IDs (passport, driver's license), external references (CRM IDs), aliases
- **Verification requests** — requests to confirm or reject an identity-to-person mapping
- **Merge/supersession requests** — requests to resolve ambiguous identities or merge duplicate records

### What Leaves This Engine

- **ResolutionResult** — structured identity resolution with one of three outcomes: MATCHED (person reference + confidence), NO_MATCH (no identity found), or AMBIGUOUS (multiple potential matches — requires human intervention)
- **Verified identity records** — normalized, versioned identity records stored in the Knowledge Engine

### What Intelligence Is Compounded

The Identity Engine does **not** compound intelligence. Identity resolution is deterministic — the same input always produces the same output. The engine does not learn or improve over time. Each resolution is independent of previous resolutions.

However, the Identity Engine is foundational to the compounding loop: every downstream engine depends on correct identity resolution. Without a reliable identity foundation, relationships cannot be tracked, context cannot be assembled, learning cannot be personalized, and memory cannot be scoped to the correct person.

### Which Downstream Engines Depend Upon It

| Engine | Dependency | Criticality |
|--------|-----------|-------------|
| Context Fusion Engine (ES-009) | Resolves identities for workspace context assembly | **Required** — identity is the first source provider |
| Reasoning Engine (ES-003) | Reads identity via context for personalized reasoning | **Medium** — identity needed for personalization |
| All pipeline engines (indirectly) | Via Context Fusion — identity flows into context for all downstream engines | **High** — identity is foundational to all context-aware operations |

### What Fails If This Engine Becomes Unavailable

- **Context Fusion cannot assemble context** — identity resolution is the first step of context assembly
- **No personalized reasoning** — cannot distinguish between actors, cannot tailor responses
- **Relationship tracking breaks** — cannot link records to the correct person
- **Multi-tenant isolation degrades** — cannot verify which tenant a person belongs to
- **Memory is unscoped** — cannot associate memories with the correct person
- **Learning cannot improve per-user** — cannot analyze patterns per person

---

## 1. Objective

### Mission

The Identity Engine resolves persons to canonical identities — registering, normalizing, verifying, and merging identity records from multiple sources while detecting ambiguous resolutions and never silently merging uncertain identities.

### Why It Exists

The SHUNYA Core Models (§3 — Identity Model) establishes identity resolution as the foundation of relationship, context, and memory. Architectural Invariant 8 (Core Models §11) states: "Identity is globally unique within a tenant. No two persons may have the same canonical identity."

Without a dedicated Identity Engine, identity resolution would be duplicated across every engine that needs it — each implementing its own normalization rules, its own resolution logic, and its own ambiguity detection. This would lead to inconsistent identity handling, duplicate records, and untraceable merges.

The Identity Engine exists to:
1. Centralize identity resolution — one engine determines canonical identity
2. Enforce global uniqueness — no duplicate identities within a tenant
3. Guarantee deterministic resolution — same input always produces same output
4. Never silently merge — ambiguous results require human intervention
5. Version identity records — changes create supersessions, never overwrites

### Architectural Responsibility

The Identity Engine owns **identity resolution** within the Compounding Intelligence Architecture. It does not reason, execute, govern, learn, or observe — it resolves and manages identities.

Position in the architecture:

```
Context Fusion (ES-009) ─── reads identity ──→ Identity Engine (ES-010)
     │                                                    │
     │                                              (reads/writes)
     │                                                    │
     ▼                                               Knowledge Engine
All pipeline engines                                    (ES-002)
(via Context Fusion)
```

---

## 2. Scope

### In Scope

- Resolve persons to canonical identities from identity claims (email, phone, channel ID, document ID, external reference, alias)
- Register new identities when no match is found
- Normalize identity values per type (E.164 for phone, lowercase for email, etc.)
- Detect and flag ambiguous resolutions — return AMBIGUOUS when multiple potential matches exist
- Verify identity-to-person mappings through verification requests
- Supersede identities when a person's identity changes (new email, name change)
- Merge duplicate identities with explicit human confirmation
- Enforce tenant isolation — identity namespaces are per-tenant
- Version identity records — identity changes create new versions, never overwrite
- Store identity records in the Knowledge Engine for durability and traceability

### Out of Scope

- **Never reason about identity context.** The Identity Engine resolves identities — it does not analyze what the identity means.
- **Never govern identity access.** Identity resolution is prerequisite to governance, not a governance function.
- **Never learn from resolution patterns.** Pattern analysis belongs to the Learning Engine.
- **Never execute actions on behalf of an identity.** Execution belongs to the Executor Engine.
- **Never manage authentication.** Authentication (verifying that a person is who they claim to be) belongs to the Interface Layer and channel adapters.
- **Never manage authorization.** Authorization (determining what an identity may do) belongs to the Governance Engine.
- **Never silently merge identities.** All merges require explicit human confirmation.

---

## 3. Dependencies

### Internal Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| Knowledge Engine (ES-002) | Read/Write | Stores identity records and person records; retrieves identity data for resolution |
| Person model | Reference | Identity records map to canonical persons (person_id field) |
| Channel adapters | Input | Extracts identity claims from incoming messages and events |

### External Dependencies

- None. The Identity Engine is self-contained with no external API calls, no network dependencies, and no third-party libraries for resolution.

---

## 4. Inputs

### Input Contract

```
IdentityClaim:
  identity_type: string           — "email" | "phone" | "channel:whatsapp" | "channel:telegram"
                                  | "document_id" | "external_id" | "alias"
  identity_value: string          — Raw identity value (e.g., "user@example.com", "+919999999999")
  tenant_id: integer              — Owning tenant
  source: string                  — Where this claim was observed ("message", "api", "import", etc.)

ResolutionRequest:
  claim: IdentityClaim            — The identity claim to resolve

VerificationRequest:
  identity_id: uuid               — The identity record to verify
  person_id: uuid                 — The person being verified against
  verifier: string                — The engine or human performing verification
  method: string                  — "automated" | "human_review" | "document_check"

MergeRequest:
  primary_identity_id: uuid       — The canonical identity to keep
  secondary_identity_id: uuid     — The identity to merge into the primary
  reason: string                  — Why the merge is being performed
  authorized_by: string           — Human or system authorizing the merge
```

### Input Sources

| Source | Type | Trigger |
|--------|------|---------|
| Channel adapters | Message/Event | On incoming message from any channel |
| Context Fusion (ES-009) | API call | On context assembly — identity resolution for actor and subject |
| Human Operator | API call | On manual identity verification or merge |
| Import/batch process | Event | On bulk identity import from legacy systems |
| Knowledge Engine (ES-002) | Event | On person record creation (for identity registration) |

### Input Validation

| Field | Constraint | Default | Rejection |
|-------|-----------|---------|-----------|
| `identity_type` | Must be recognized type | None (required) | `UNKNOWN_IDENTITY_TYPE` |
| `identity_value` | Must be non-empty string | None (required) | `EMPTY_IDENTITY_VALUE` |
| `tenant_id` | Must be positive integer | None (required) | `MISSING_TENANT` |
| `identity_value` (email) | Must match email pattern | None | `INVALID_EMAIL_FORMAT` |
| `identity_value` (phone) | Must be normalized to E.164 | None | `INVALID_PHONE_FORMAT` |
| `identity_type` ("channel:*") | Must include provider and channel ID | None | `INVALID_CHANNEL_FORMAT` |

---

## 5. Outputs

### Output Contract

```
ResolutionResult:
  status: string                  — "MATCHED" | "NO_MATCH" | "AMBIGUOUS"
  person_id: uuid | null          — The resolved canonical person (null if NO_MATCH or AMBIGUOUS)
  identity_id: uuid | null        — The identity record used for resolution
  confidence: float               — Canonical confidence score (0.0–1.0)
  candidates: PersonMatch[] | null — Potential matches if AMBIGUOUS
  normalized_value: string        — Normalized form of the identity value

PersonMatch:
  person_id: uuid                 — Candidate person ID
  identity_type: string           — Which identity type matched
  confidence: float               — Confidence in this specific match

IdentityRecord:
  identity_id: uuid               — Unique identity record ID
  person_id: uuid                 — The canonical person this identity belongs to
  identity_type: string           — Type of identity
  identity_value: string          — Raw identity value
  normalized_value: string        — Normalized form for lookup
  verification_state: string      — "unverified" | "verified" | "failed"
  confidence: float               — Confidence in identity-to-person mapping
  status: string                  — "active" | "superseded" | "merged"
  provenance: Provenance          — Origin and modification history
  created_at: datetime            — When this identity was registered
  superseded_at: datetime | null  — When this identity was superseded
  merged_into_id: uuid | null     — If merged, the canonical identity ID
```

### Output Destinations

| Destination | Consumer | Delivery Guarantee |
|-------------|----------|-------------------|
| Context Fusion (ES-009) | ResolutionResult for context assembly | Best-effort |
| Channel adapters | ResolutionResult for message routing | Best-effort |
| Knowledge Engine (ES-002) | IdentityRecord for durable storage | At-least-once |
| Requesting engine | ResolutionResult | Best-effort |
| Event Bus | Events for downstream consumers | At-least-once |

### Output Guarantees

- **Determinism:** Same input always produces the same resolution outcome. No randomness, no LLM calls (SHUNYA_CORE_MODELS.md §3, Principle 2).
- **Global uniqueness:** Within a tenant, no two active identity records may have the same normalized_value for the same identity_type.
- **No silent merges:** AMBIGUOUS results are never auto-resolved. Human intervention is required.
- **Versioning:** Identity records are immutable after creation. Changes create new versions (supersession) or merge records.
- **Isolation:** Identity resolution is always scoped to a tenant. No cross-tenant identity lookups.

---

## 6. State Machine

### States

```
Active
 │
 ├──[verified]──────────────────────→ Verified
 │
 ├──[superseded_by_new_identity]────→ Superseded
 │
 ├──[merged_into_canonical]─────────→ Merged
 │
 └──[verification_failed]───────────→ Failed

Verified
 │
 ├──[superseded_by_new_identity]────→ Superseded
 │
 └──[merged_into_canonical]─────────→ Merged

Failed ──[re_verified]──────────────→ Active

Superseded (terminal)
Merged (terminal)
```

### Resolution Lifecycle (per request)

```
Claim Received
   │
   ├──[normalize]──→ Normalized
   │                    │
   │                    ├──[lookup: single match]──→ MATCHED
   │                    │
   │                    ├──[lookup: no match]──→ NO_MATCH → Register New Identity
   │                    │
   │                    └──[lookup: multiple matches]──→ AMBIGUOUS → Human Review
   │
   └──[invalid]──→ Invalid Claim (rejected)
```

### State Definitions

| State | Meaning | Is Terminal? |
|-------|---------|-------------|
| Active | Identity is registered and usable for resolution | No |
| Verified | Identity has been confirmed through a verification process | No |
| Failed | Verification attempt did not confirm identity-to-person mapping | No |
| Superseded | Identity has been replaced by a newer identity for the same person | Yes |
| Merged | Identity has been merged into another canonical identity | Yes |

### Transition Table

| From State | Event | Condition | To State | Action |
|------------|-------|-----------|----------|--------|
| Active | verified | Verification confirms mapping | Verified | Update verification_state, increase confidence |
| Active | superseded_by_new_identity | New identity supersedes this one | Superseded | Set status to superseded, record supersession |
| Active | merged_into_canonical | Merge authorized and executed | Merged | Set status to merged, record merge reference |
| Active | verification_failed | Verification does not confirm mapping | Failed | Update verification_state, log failure |
| Verified | superseded_by_new_identity | New identity supersedes this one | Superseded | Set status to superseded, record supersession |
| Verified | merged_into_canonical | Merge authorized and executed | Merged | Set status to merged, record merge reference |
| Failed | re_verified | Re-verification confirms mapping | Active | Update verification_state, restore to active |

---

## 7. Events

### Events Consumed

| Event | Source | Payload | Action Taken |
|-------|--------|---------|-------------|
| `person.created` | Knowledge Engine / Interface | `{person_id, tenant_id}` | Prepare for identity registration |
| `identity.verification.requested` | Human Operator / Governance | `{identity_id, person_id, method}` | Begin verification process |
| `identity.merge.request` | Human Operator | `{primary_identity_id, secondary_identity_id, reason}` | Execute or reject merge |

### Events Produced

| Event | Destination | Payload | Trigger Condition |
|-------|-------------|---------|-------------------|
| `identity.resolved` | Context Fusion, Event Bus | `{identity_id, person_id, resolution_status, confidence, tenant_id}` | Identity successfully resolved (MATCHED) |
| `identity.ambiguous` | Human Review Queue, Governance | `{claim, candidates, tenant_id}` | Resolution produced multiple potential matches |
| `identity.registered` | Knowledge Engine, Event Bus | `{identity_id, person_id, identity_type, normalized_value, tenant_id}` | New identity registered (NO_MATCH → created) |
| `identity.superseded` | Context Fusion, Event Bus | `{old_identity_id, new_identity_id, person_id, tenant_id}` | Identity superseded by new identity |
| `identity.merged` | Context Fusion, Event Bus | `{primary_identity_id, secondary_identity_id, person_id, tenant_id}` | Two identities merged |
| `identity.verified` | Event Bus | `{identity_id, person_id, method, confidence}` | Identity verification completed |

---

## 8. Failure Modes

| Failure Mode | Cause | Detection | Effect | Recovery |
|--------------|-------|-----------|--------|----------|
| Ambiguous resolution | Multiple identities match the same claim | Lookup returned >1 result | Return AMBIGUOUS with candidates list | Require human intervention to resolve |
| Invalid identity value | Malformed email, phone, or channel ID | Schema validation per type | Reject claim with validation error | Return error to caller; log for analysis |
| Knowledge Engine unavailable | Downstream storage outage | Timeout/circuit breaker | Cannot read or write identity records | Retry with backoff; buffer identity registration for later |
| Identity conflict | Concurrent attempts to register the same identity | Optimistic lock on normalized_value | Second registration rejected | Return existing identity; log conflict |
| Duplicate merge request | Attempt to merge already-merged identity | Check merged_into_id field | Reject with "already merged" | Return error with current merge status |
| Tenant isolation violation | Cross-tenant identity lookup attempted | Tenant ID mismatch in request | Reject with cross-tenant error | Log violation; escalate |
| Supersession loop | Identity A superseded by B, B superseded by A | Cycle detection on supersession chain | Reject supersession | Log error; require human resolution |

---

## 9. Observability

### Logging

| Event | Log Level | Data | Privacy Constraint |
|-------|-----------|------|-------------------|
| Resolution request | INFO | identity_id (if known), identity_type, tenant_id, result status | No personal data — log normalized form, not raw value |
| Identity resolved | INFO | identity_id, person_id, confidence, tenant_id | No personal data |
| Identity ambiguous | WARN | identity_id, candidate_count, tenant_id | No personal data |
| Identity registered | INFO | identity_id, person_id, identity_type, tenant_id | No personal data |
| Identity verified | INFO | identity_id, person_id, method, tenant_id | No personal data |
| Identity superseded | INFO | old_identity_id, new_identity_id, person_id, tenant_id | No personal data |
| Identity merged | INFO | primary_identity_id, secondary_identity_id, person_id, tenant_id | No personal data |
| Invalid identity value | WARN | identity_type, validation_error | Mask identity value (log only first 3 chars) |
| Knowledge Engine unavailable | ERROR | operation, duration_ms | None |
| Tenant isolation violation | ERROR | requesting_tenant, target_tenant | Escalate |

### Tracing

- **Span: `identity.resolve`** — Full resolution lifecycle
  - Child span: `identity.normalize` — Identity value normalization
  - Child span: `identity.lookup` — Store lookup for matching identities
  - Child span: `identity.register` — New identity registration
- identity_id and person_id propagated as trace tags

### Alerting

| Condition | Severity | Threshold |
|-----------|----------|-----------|
| Ambiguous resolution rate > 5% | Warning | Per minute |
| Knowledge Engine unavailable for > 3 consecutive attempts | Pager | Per identity operation |
| Identity conflict rate > 1% | Warning | Per hour |
| Supersession loop detected | Pager | Per occurrence |

---

## 10. Metrics

| Metric | Type | Unit | Target | Measurement |
|--------|------|------|--------|-------------|
| `identity.resolutions_total` | Counter | resolutions | N/A | Per second, by result status |
| `identity.matched_total` | Counter | matches | N/A | Per second |
| `identity.no_match_total` | Counter | no_match | N/A | Per second |
| `identity.ambiguous_total` | Counter | ambiguous | < 1% | Per minute |
| `identity.registrations_total` | Counter | registrations | N/A | Per second |
| `identity.verifications_total` | Counter | verifications | N/A | Per second |
| `identity.merges_total` | Counter | merges | N/A | Per hour |
| `identity.supersessions_total` | Counter | supersessions | N/A | Per hour |
| `identity.latency_p50` | Histogram | ms | < 10ms | Per resolution |
| `identity.latency_p99` | Histogram | ms | < 50ms | Per resolution |
| `identity.conflicts_total` | Counter | conflicts | < 0.1% | Per hour |

---

## 11. Rollback Strategy

### Rollback Triggers

- Identity resolution produces incorrect matches (false positive MATCHED)
- Identity merge was executed erroneously
- Identity supersession was executed incorrectly (wrong identity superseded)
- Data corruption in identity records

### Rollback Procedure

1. **Stop accepting new identity operations:** Block at the API boundary.
2. **Assess impact:** Determine which resolutions, registrations, merges, or supersessions need reversal.
3. **Reverse merge:** Create a new identity record for the incorrectly merged identity. Set status to active.
4. **Reverse supersession:** Restore the superseded identity to active. Create a new version of the superseding identity.
5. **Verify:** Run a sample of recent resolution requests through the corrected state.
6. **Resume:** Accept new identity operations.

### Rollback Limitations

- Identity records that were already consumed by downstream engines (Context Fusion, Reasoning) cannot be recalled. Downstream context may reference the old identity until next context assembly.
- Merges that resulted in dependent actions (messages sent, actions taken on behalf of the merged identity) may require compensation actions outside the Identity Engine's scope.
- Identity version history is append-only. Previous states are preserved in superceded/merged records.

---

## 12. Migration Strategy (when applicable)

### Migration Type

Data migration — identity records from legacy systems to the Identity Engine.

### Migration Steps

1. **Pre-migration validation:** Verify that legacy identity data can be parsed and normalized per identity type.
2. **Dry-run:** Run identity registration for a sample of legacy records, verify resolution matches expected outcomes.
3. **Bulk import:** Register all legacy identities through the Identity Engine's batch import interface.
4. **Verify:** Run resolution queries for a statistical sample of imported identities, confirm results match expected.
5. **Cutover:** Switch identity resolution from legacy system to the Identity Engine.

### Rollback During Migration

- Point-in-time: The state before bulk import.
- Data consistency: Legacy system remains available during migration for fallback.
- Cutover is reversible — switch back to legacy resolution if discrepancies are found.

---

## 13. Verification

### Unit Tests

- State transitions: 7 tests (one per transition in the transition table)
- Error handling: 7 tests (one per failure mode)
- Edge cases: 12 tests (empty identity, invalid email format, invalid phone format, channel ID parsing, ambiguous resolution with 2 candidates, ambiguous resolution with 10+ candidates, duplicate registration, already-merged merge request, supersession loop detection, tenant isolation, concurrent resolution, cross-tenant resolution attempt)

### Integration Tests

- Integration with Knowledge Engine: 4 tests (identity record write, identity record read, identity record update/supersession, Knowledge Engine unavailable)
- Integration with Context Fusion: 3 tests (identity resolved, identity ambiguous, identity not found)
- Integration with Channel Adapters: 3 tests (identity extraction from WhatsApp, Telegram, API)

### Security Review

- [ ] No eval/exec patterns
- [ ] No credential leakage — Identity Engine never accesses credentials or secrets
- [ ] Input normalization — all identity values are normalized before storage (reducing injection risk)
- [ ] Tenant isolation enforcement — identity lookups are always scoped to tenant_id
- [ ] No personal data in logs — identity values are masked or replaced with references

### Performance

- Latency budget: 10ms p50, 50ms p99 per resolution
- Memory budget: 128MB steady-state, 256MB peak (plus cache)
- Concurrent capacity: 200 resolutions/second per instance
- Identity cache: LRU cache of recently resolved identities, TTL 5 minutes

---

## 14. Security

### Tenant Isolation

Every identity namespace is scoped to a tenant (SHUNYA_CORE_MODELS.md §3, Principle 1 — global uniqueness within a tenant). The same phone number may refer to different persons in different tenants (SHUNYA_SYSTEM_FLOW.md §9 — Identity isolation). Identity lookups always include tenant_id and never return results from another tenant.

### Deterministic Resolution

Identity resolution is fully deterministic (SHUNYA_CORE_MODELS.md §3, Principle 2). The same input always produces the same resolution outcome. No randomness, no LLM calls, no external service dependency. This guarantees that identity resolution is predictable and testable.

### No Silent Merges

Ambiguous resolutions are never auto-resolved (SHUNYA_CORE_MODELS.md §3, Principle 3). If an identity claim matches multiple persons, the Identity Engine returns AMBIGUOUS with the list of candidates. Human intervention is required to resolve the ambiguity. This prevents accidental identity merging that could corrupt relationships, context, and memory.

### Versioning and Supersession

Identity records are never updated in place. When a person's identity changes (new email, name change), the existing identity record is marked as superseded and a new record is created (SHUNYA_CORE_MODELS.md §3, Principle 4). The complete identity history is preserved for audit and traceability.

### No Credential Access

The Identity Engine never reads:
- API tokens or secrets
- Database passwords
- Encryption keys
- Authentication tokens

It resolves identities — it does not authenticate or authorize.

---

## 15. Constitutional Mapping

| Responsibility | Constitutional Principle | Source |
|---------------|------------------------|--------|
| Resolve persons to canonical identities | §3 — Identity Model | SHUNYA_CORE_MODELS.md §3 |
| Enforce global uniqueness within a tenant | §11 — Invariant 8: "Identity is globally unique within a tenant" | SHUNYA_CORE_MODELS.md §11 |
| Resolve deterministically (same input, same output) | §3 — Identity Resolution Principle 2 | SHUNYA_CORE_MODELS.md §3 |
| Never silently merge ambiguous identities | §3 — Identity Resolution Principle 3 | SHUNYA_CORE_MODELS.md §3 |
| Version identity records (supersede, never overwrite) | §3 — Identity Resolution Principle 4 | SHUNYA_CORE_MODELS.md §3 |
| Normalize identities per type | §3 — Identity Types and normalization rules | SHUNYA_CORE_MODELS.md §3 |
| Enforce tenant isolation per identity namespace | §9 — Identity isolation | SHUNYA_SYSTEM_FLOW.md §9 |
| Provide resolution data to Context Fusion | §2 — Source providers for Context Fusion | SHUNYA_SYSTEM_FLOW.md §2 |
| Never silently merge — AMBIGUOUS → human intervention | §3 — Identity Engine SHALL NEVER | SHUNYA_SYSTEM_FLOW.md §3 |

---

## 16. Layer Responsibilities

### What the Identity Engine Does

- Resolves persons to canonical identities from multiple source types
- Normalizes identity values per type (email, phone, channel, document, external, alias)
- Detects and flags ambiguous resolutions
- Registers new identities when no match is found
- Verifies identity-to-person mappings
- Supersedes identities when identity data changes
- Merges duplicate identities with human approval
- Enforces tenant isolation per identity namespace
- Provides identity data to Context Fusion for workspace context assembly

### What the Identity Engine May Never Do

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never reason about identity context | Would violate Layer Boundaries | Reasoning Engine |
| Never govern identity access | Would violate Separation of Responsibilities | Governance Engine |
| Never learn from resolution patterns | Would violate Layer Boundaries | Learning Engine |
| Never execute actions on behalf of identity | Would violate Layer Boundaries | Executor Engine |
| Never manage authentication | Would violate Separation of Responsibilities | Interface / Channel adapters |
| Never manage authorization | Would violate Separation of Responsibilities | Governance Engine |
| Never silently merge identities | Would violate Identity Resolution Principle 3 | Human operator (must intervene) |
| Never mutate evidence | Would violate Layer Boundaries | Evidence is immutable (invariant) |

---

## 17. Future Extensions

### 17.1 Identity Strength Scoring

Expanding identity type strength values (already defined in Core Models §3 — Strong, Medium, Weak) into a formal scoring algorithm that considers verification history, source reliability, and cross-referencing.

### 17.2 Automated Identity Verification

Verifying identity claims against trusted external sources (e.g., phone carrier OTP confirmation, email domain verification, document authenticity check) to increase confidence without requiring human review.

### 17.3 Identity Expiry and Refresh

Defining expiry TTLs per identity type — phone numbers may be reassigned, email addresses may become inactive, document IDs may expire. The Identity Engine would flag expired identities for re-verification.

### 17.4 Cross-Tenant Identity Resolution

Supporting identity resolution across tenant boundaries for authorized use cases (e.g., a person verified in one tenant is recognized in another tenant they also belong to) while maintaining tenant isolation.

### 17.5 Identity Graph

Building an identity graph that links related identities (same person across multiple channels, same organization across multiple persons) to support richer relationship discovery.

---

## 18. References

- [SHUNYA_ARCHITECTURE.md](/SHUNYA_ARCHITECTURE.md) — Sections 2.5 (Architectural Trust), 6.3 (Least Authority)
- [SHUNYA_SYSTEM_FLOW.md](/architecture/SHUNYA_SYSTEM_FLOW.md) — Section 2 (Source providers), 3 (Identity Engine), 6 (Identity State), 9 (Identity isolation)
- [SHUNYA_CORE_MODELS.md](/architecture/SHUNYA_CORE_MODELS.md) — Section 3 (Identity Model — principles, types, lifecycle, Identity Object), 6 (Provenance Model), 11 (Invariant 8 — identity global uniqueness), 12 (Glossary)
- [SHUNYA_ENGINEERING_CONSTITUTION.md](/governance/SHUNYA_ENGINEERING_CONSTITUTION.md) — Articles 1, 3, 4
- [ARCHITECTURE_BASELINE_REVIEW.md](/architecture/ARCHITECTURE_BASELINE_REVIEW.md) — M7 (Missing Engine Spec), ADR-006, Ownership Matrix
- [ES-002: Knowledge Engine](/governance/engine_specs/ES-002-KNOWLEDGE-ENGINE.md) — Stores identity records
- [ES-003: Reasoning Engine](/governance/engine_specs/ES-003-REASONING-ENGINE.md) — Reads identity via context
- [ES-009: Context Fusion Engine](/governance/engine_specs/ES-009-CONTEXT-FUSION-ENGINE.md) — Depends on Identity Engine for identity resolution
- [ENGINE_SPEC_TEMPLATE.md](/governance/engine_specs/ENGINE_SPEC_TEMPLATE.md) — Specification template
- [VERIFICATION_CHECKLIST.md](/governance/verification/VERIFICATION_CHECKLIST.md) — Standard verification protocol
- `app/shunya/identity/__init__.py` — Current implementation (270 lines)