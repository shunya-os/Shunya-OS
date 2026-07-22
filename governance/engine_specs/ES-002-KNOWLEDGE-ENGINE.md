# ES-002: Knowledge Engine

**Status:** Draft
**Phase:** Phase 2 (Knowledge Layer)
**Layer:** Knowledge
**Author:** Chief Software Architect
**Date:** 2026-07-18
**Approver:** (filled on approval)

---

## Section 0 — Compounding Intelligence Position

### What Enters This Engine

- **Observations** — direct recordings of reality from the Observer Layer
- **Documents** — ingested files, emails, attachments, and structured data
- **External APIs** — supplier data, government databases, market intelligence
- **Human corrections** — manual fact assertions, overrides, and annotations
- **Learning signals** — distilled insights from the Learning Layer
- **Workspace updates** — changes to organizational context, preferences, and relationships
- **Conversation events** — facts extracted from human communication
- **Imports** — bulk data from legacy systems, CSV imports, API migrations

### What Leaves This Engine

- **Knowledge retrieval** — structured and semantic fact lookups for downstream layers
- **Evidence chains** — provenance-verified fact bundles for reasoning and governance
- **Context packages** — bounded workspace knowledge for the Context Fusion service
- **Relationship graphs** — entity linkages for the relationship layer
- **Historical timelines** — versioned fact histories for audit and temporal queries
- **Knowledge confidence** — confidence scores accompanying every fact retrieval

### What Intelligence Is Compounded

The Knowledge Engine compounds **factual certainty** over time. Every fact evolves through a lifecycle: Unknown → Observed → Verified → Trusted → Superseded → Archived → Retired. As facts accumulate, the system's understanding of reality becomes more complete, more precise, and more confidently held. A fact that was once "observed with 0.3 confidence" may become "trusted with 0.95 confidence" after repeated verification from independent sources.

The compounding mechanism is **versioning without deletion**. Old facts are never lost — they are superseded by newer versions. A future learning cycle can revisit a superseded fact and determine it was correct all along, restoring it with higher confidence.

### Which Downstream Engines Depend Upon It

| Engine | Dependency | Criticality |
|--------|-----------|-------------|
| Reasoning Layer | Consumes evidence chains and knowledge facts | **Critical** — cannot reason without facts |
| Planner Layer | Consumes destination knowledge, supplier data, past itineraries | **Critical** — cannot plan without domain knowledge |
| Governance Layer | Consumes policy definitions (stored as knowledge facts) | **High** — cannot evaluate without policy knowledge |
| Observer Layer | Writes observations that become knowledge facts | **High** — observation without storage is lost |
| Learning Layer | Writes learned facts, reads existing knowledge for context | **Critical** — cannot improve without reading and writing facts |
| Executor Layer | Reads channel configuration, template definitions | **Medium** — can use cached defaults |
| Context Fusion (Phase 10) | Reads workspace context from knowledge records | **Medium** — can operate with degraded context |
| Phase 11 (Knowledge Resolution) | Is the consumption boundary — reads from Knowledge Engine | **Critical** — is the Knowledge Engine's primary consumer |

### What Fails If This Engine Becomes Unavailable

- **Reasoning collapses** — no evidence chains, no confidence scores, no fact-based inference
- **Planning halts** — no destination knowledge, supplier data, or past itineraries
- **Governance blind** — policy evaluation continues but cannot verify facts against stored knowledge
- **Learning is mute** — no facts to read for context, no store to write improvements
- **Context Fusion degrades** — workspace context is partial or empty
- **Identity resolution fails** — no person records, channel identities, or relationship data
- **Document processing pauses** — extracted fields have nowhere to be stored
- **Recovery requires replay** — all observations during downtime must be replayed

---

## 1. Objective

### Mission

The Knowledge Engine is the single source of truth for all facts within SHUNYA. It stores, versions, retrieves, and validates every piece of knowledge — from destination weather data to customer preferences, from business policies to learned insights — and guarantees that no fact is ever silently lost or overwritten.

### Why SHUNYA Requires Immutable Knowledge Rather Than Mutable Memory

Mutable memory (a database that allows in-place updates) creates a fundamental trust problem: when a fact is overwritten, the previous version is gone. The system cannot answer "what did we know on Tuesday?" because Tuesday's knowledge was overwritten on Wednesday. This breaks every constitutional principle that depends on traceability:

- **Explainable Decisions** — a decision traced to a fact that no longer exists is an untraceable decision
- **Continuous Observation** — "what changed?" cannot be answered if the previous state is gone
- **Compounding Intelligence** — learning compounds on accumulated knowledge, not on the latest snapshot
- **Trust** — the system cannot prove it hasn't lost or altered information

Immutable knowledge means every fact is versioned, every version is permanent, and the complete history is always queryable. The Knowledge Engine is the implementation of this principle.

### Architectural Responsibility

The Knowledge Engine is the foundation of the Compounding Intelligence Loop. Every other layer reads from it or writes to it. It does not reason, plan, execute, govern, observe, or learn — it stores and retrieves facts with integrity guarantees.

Position in the pipeline:

```
Observer → [Knowledge Engine] ← Learning
   ↑            │    │              ↑
   │            │    │              │
   └────────────┘    └──────────────┘
        │                   │
   Reasoning ←──── Knowledge Engine ────→ Context Fusion
        │                   │
   Planner ←──── Knowledge Engine ────→ Governance
```

---

## 2. Scope

### In Scope

- Store immutable, versioned knowledge facts with checksum integrity
- Retrieve facts by key, domain, category, temporal range, and confidence threshold
- Support semantic, structured, hybrid, temporal, and relationship-based retrieval
- Version every fact mutation — never overwrite, always append new version
- Maintain complete fact history with supersession tracking
- Compute and verify content integrity via SHA-256 checksums
- Provide confidence scoring for every fact and fact retrieval
- Enforce tenant isolation — facts are scoped per tenant
- Support domain-specific namespacing (travel, healthcare, legal, etc.)
- Seed knowledge from markdown knowledge bases and structured imports
- Support batch operations for bulk ingestion
- Provide verification and integrity checking
- Maintain temporal validity — facts are valid from a start time to an optional end time
- Track ownership and provenance for every fact
- Support right-to-be-forgotten workflows through supersession (not deletion)

### Out of Scope

- **Never reason about facts.** The Knowledge Engine retrieves facts — it does not infer new facts from existing ones.
- **Never execute actions.** The Knowledge Engine does not send messages, create database records, or call external APIs.
- **Never govern.** The Knowledge Engine does not evaluate policies or make approval decisions.
- **Never learn independently.** The Knowledge Engine accepts learning signals from the Learning Layer — it does not generate them.
- **Never access credentials.** The Knowledge Engine does not read API tokens, passwords, or payment secrets.
- **Never observe reality.** The Knowledge Engine stores observations — it does not produce them.
- **Never generate plans.** The Knowledge Engine provides data for planning — it does not create plans.
- **Never handle real-time streaming.** The Knowledge Engine is optimized for durable storage, not event streaming.
- **Never serve as a cache.** The Knowledge Engine is the source of truth, not a cache layer.
- **Never provide real-time guarantees.** Write operations are durable but not necessarily synchronous for all downstream consumers.

---

## 3. Dependencies

### Internal Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| Observer Layer | Input | Writes observations that become new knowledge facts |
| Learning Layer | Input | Writes learned facts and improvements to existing facts |
| Reasoning Layer | Output | Reads evidence chains and knowledge facts for analysis |
| Planner Layer | Output | Reads destination knowledge, supplier data, past itineraries |
| Governance Layer | Output | Reads policy definitions stored as knowledge facts |
| Context Fusion (Phase 10) | Output | Reads workspace context from knowledge records |
| Phase 11 (Knowledge Resolution) | Output | Primary consumer — evaluates knowledge sufficiency |
| Phase 7 (Evidence) | Input | Provides source references for fact provenance |
| Phase 4 (Privacy) | Protocol | Enforces eligibility gates on fact retrieval |

### External Dependencies

- PostgreSQL database (for the `knowledge_facts` table)
- No external APIs, no third-party libraries beyond the application stack

---

## 4. Inputs

### Input Contract

```
KnowledgeInput:
  fact_key: string              — Unique identifier, e.g. "destination.bali.visa"
  value: any                    — The fact value (text, JSON, number, markdown)
  domain: string                — "travel" | "healthcare" | "legal" | etc.
  category: string              — "visa" | "tax" | "venue" | "policy" | etc.
  value_type: string            — "text" | "json" | "number" | "markdown" | "boolean"
  confidence: float             — 0.0 to 1.0
  evidence: string              — Source or reasoning behind this fact
  source: string                — "manual" | "web_scrape" | "reasoning" | "learning" | "observer" | "import"
  created_by: string            — User or system component creating the fact
  tenant_id: int                — Owning tenant
  workspace_id: int | null      — Owning workspace (optional)
  valid_from: datetime          — When this fact becomes valid
  valid_until: datetime | null  — When this fact expires (null = no expiry)
  tags: string[]                — Arbitrary tags for categorization
```

### Input Sources

| Source | Event | Trigger |
|--------|-------|---------|
| Observer Layer | `observation.recorded` | On every observation completion |
| Learning Layer | `learning.signal.generated` | On learning signal approval |
| Human correction | `knowledge.manually.asserted` | Via admin interface or API |
| Document processing | `document.field.extracted` | On document field extraction |
| External API sync | `knowledge.external.ingested` | On scheduled or event-driven sync |
| Import pipeline | `knowledge.bulk.imported` | On bulk data import |
| Workspace update | `workspace.context.changed` | On workspace context mutation |
| Conversation event | `conversation.fact.extracted` | On fact extraction from messages |

### Input Validation

| Field | Constraint | Default | Rejection |
|-------|-----------|---------|-----------|
| `fact_key` | Non-empty, max 255 chars, alphanumeric+dots+underscores | None (required) | `INVALID_FACT_KEY` |
| `value` | Non-empty, max 1MB serialized | None (required) | `EMPTY_VALUE` |
| `domain` | Must be recognized in domain registry | None (required) | `UNKNOWN_DOMAIN` |
| `tenant_id` | Must be positive integer | None (required) | `MISSING_TENANT` |
| `confidence` | 0.0 to 1.0 | 1.0 | Clamped to range |
| `valid_from` | Must not be in the future (unless explicitly allowed) | Current time | `FUTURE_DATE_NOT_ALLOWED` |
| `valid_until` | Must be after valid_from if set | null | `INVALID_DATE_RANGE` |
| `source` | Must be recognized source type | "manual" | `UNKNOWN_SOURCE` |

---

## 5. Outputs

### Output Contract

```
KnowledgeRetrievalResult:
  fact_key: string              — Requested fact key
  version: int                  — Current version number
  value: any                    — Deserialized fact value
  value_type: string            — "text" | "json" | "number" | "markdown" | "boolean"
  confidence: float             — 0.0 to 1.0
  evidence: string              — Source or reasoning behind this fact
  source: string                — "manual" | "web_scrape" | "reasoning" | etc.
  checksum: string              — SHA-256 integrity check
  created_by: string            — Creator identifier
  created_at: datetime          — When this version was created
  superseded_at: datetime|null  — When this version was superseded
  valid_from: datetime          — When this fact becomes valid
  valid_until: datetime|null    — When this fact expires
  tenant_id: int                — Owning tenant
  workspace_id: int|null        — Owning workspace

KnowledgeSearchResult:
  results: KnowledgeRetrievalResult[]
  total_count: int              — Total matching results
  query_time_ms: int            — Query execution time
  confidence_range: [float,float] — Min and max confidence in results

EvidenceChain:
  fact: KnowledgeRetrievalResult    — The target fact
  source_references: SourceRef[]    — All source references linked to this fact
  supporting_facts: KnowledgeRetrievalResult[]  — Facts that support this fact
  contradicting_facts: KnowledgeRetrievalResult[]  — Facts that contradict this fact
  resolution_state: string          — "supported" | "unsupported" | "contradicted" | "conflict" | "no_evidence"
```

### Output Destinations

| Destination | Consumer | Delivery Guarantee |
|-------------|----------|-------------------|
| Reasoning Layer | Evidence chains, destination facts | Best-effort (read-only) |
| Planner Layer | Destination knowledge, supplier data | Best-effort (read-only) |
| Governance Layer | Policy definitions | Best-effort (read-only) |
| Context Fusion (Phase 10) | Workspace context items | Best-effort (read-only) |
| Phase 11 (Knowledge Resolution) | Knowledge sufficiency evaluation | Best-effort (read-only) |
| Observer Layer | Read confirmation for observation | At-least-once (write) |
| Learning Layer | Read existing facts for context | Best-effort (read-only) |

### Output Guarantees

- **Read-after-write consistency:** A fact written by any source is immediately readable by any consumer.
- **Deterministic ordering:** Fact versions are ordered by version number, not by timestamp. Rolls are stable.
- **No phantom reads:** A fact retrieved at time T reflects all writes committed before T.
- **Checksum verification:** All retrievals include a checksum that the consumer can verify independently.

---

## 6. State Machine

### States

```
Unknown
 │
 │ [observed]
 ▼
Observed ──[verification_failed]──→ Retired
 │
 │ [verified]
 ▼
Verified ──[verification_failed]──→ Retired
 │
 ├──[evidence_strengthened]──→ Trusted
 │
 └──[conflict_detected]──→ Conflict
      │
      ├──[conflict_resolved_favor]──→ Trusted
      │
      └──[conflict_resolved_against]──→ Superseded
 │
Trusted
 │
 ├──[new_version_created]──→ Superseded
 │
 ├──[expired]──→ Archived
 │
 └──[retracted]──→ Retired
 │
Superseded ──[archived]──→ Archived
 │
Archived ──[retention_expired]──→ Retired
 │
Retired (terminal)
 │
Conflict ──[resolution_pending]──→ Conflict (remains)
```

### State Definitions

| State | Meaning | Is Terminal? |
|-------|---------|-------------|
| Unknown | Fact has not been observed or recorded | No (initial) |
| Observed | Fact has been recorded but not yet verified | No |
| Verified | Fact has passed automated verification checks | No |
| Trusted | Fact has been verified from multiple independent sources or by human confirmation | No |
| Superseded | A newer version of this fact exists; this version is historical | No |
| Archived | Fact is no longer actively used but preserved for audit | No |
| Retired | Fact has been removed from active use and may be deleted per retention policy | Yes |
| Conflict | Two or more facts provide contradictory information | No (stable) |

### Transition Table

| From State | Event | Condition | To State | Action |
|------------|-------|-----------|----------|--------|
| Unknown | observed | Observation received | Observed | Record fact with initial confidence |
| Observed | verified | Automated checks pass | Verified | Update confidence, attach verification evidence |
| Observed | verification_failed | Automated checks fail | Retired | Log failure, flag for human review |
| Verified | evidence_strengthened | Multiple independent sources confirm | Trusted | Increase confidence, update state |
| Verified | conflict_detected | Contradictory fact exists | Conflict | Flag both facts, create conflict record |
| Verified | verification_failed | Re-verification fails | Retired | Log failure, preserve as historical |
| Verified | superseded | New version created | Superseded | Mark superseded_at, link to new version |
| Trusted | new_version_created | New version supersedes | Superseded | Mark superseded_at, link to new version |
| Trusted | expired | valid_until passed | Archived | Set archived_at, remove from active queries |
| Trusted | retracted | Human or system retraction | Retired | Log retraction reason, preserve as historical |
| Superseded | archived | Retention policy triggers archival | Archived | Move to archival storage |
| Superseded | restored | Re-evaluation confirms correctness | Trusted | Create new version with restored value |
| Archived | retention_expired | Retention period exceeded | Retired | Schedule for deletion per policy |
| Conflict | conflict_resolved_favor | Human confirms one version | Trusted | Update confidence, link to resolution evidence |
| Conflict | conflict_resolved_against | Human rejects one version | Superseded | Mark as superseded, link to resolution evidence |

---

## 7. Events

### Events Consumed

| Event | Source | Payload | Action Taken |
|-------|--------|---------|-------------|
| `observation.recorded` | Observer Layer | `{fact_key, value, confidence, evidence}` | Create new fact version in Observed state |
| `learning.signal.generated` | Learning Layer | `{fact_key, new_value, confidence, evidence}` | Create new version, supersede old |
| `knowledge.manually.asserted` | Human Interface | `{fact_key, value, evidence, confidence}` | Create new version in Trusted state |
| `document.field.extracted` | Document Service | `{fact_key, value, source_reference}` | Create new version in Observed state |
| `knowledge.external.ingested` | External API | `{fact_key, value, source, confidence}` | Create new version in Observed state |
| `knowledge.verification.requested` | Any trusted source | `{fact_key}` | Trigger verification workflow |
| `knowledge.conflict.resolved` | Human Interface | `{fact_key, resolution, new_value}` | Resolve conflict, create new version |

### Events Produced

| Event | Destination | Payload | Trigger Condition |
|-------|-------------|---------|-------------------|
| `knowledge.fact.created` | All subscribers | `{fact_key, version, domain, tenant_id}` | New fact version created |
| `knowledge.fact.superseded` | Reasoning, Context Fusion | `{fact_key, old_version, new_version}` | Existing fact superseded |
| `knowledge.fact.conflict.detected` | Human Review Queue | `{fact_key, versions_in_conflict}` | Contradictory facts detected |
| `knowledge.fact.retired` | Privacy, Retention | `{fact_key, version, reason}` | Fact retired |
| `knowledge.integrity.violation` | Alerting, Doctor | `{fact_key, version, expected_checksum, actual_checksum}` | Checksum mismatch detected |
| `knowledge.verification.completed` | Requesting source | `{fact_key, result, confidence}` | Verification workflow completes |

### Failure Events

| Event | Payload | Trigger |
|-------|---------|---------|
| `knowledge.store.failed` | `{fact_key, error, context}` | Write operation fails |
| `knowledge.retrieval.failed` | `{fact_key, error}` | Read operation fails |
| `knowledge.integrity.violation` | `{fact_key, version, detail}` | Checksum mismatch detected |
| `knowledge.validation.failed` | `{fact_key, field, reason}` | Input validation fails |

### Recovery Events

| Event | Payload | Trigger |
|-------|---------|---------|
| `knowledge.store.recovered` | `{fact_key, retry_count}` | Write succeeds after failure |
| `knowledge.integrity.restored` | `{fact_key, version}` | Checksum violation resolved |
| `knowledge.replay.completed` | `{batch_id, fact_count}` | Post-downtime replay finishes |

---

## 8. Failure Modes

| Failure Mode | Cause | Detection | Effect | Recovery |
|--------------|-------|-----------|--------|----------|
| Corrupted knowledge | Hardware fault, software bug, checksum mismatch | Periodic integrity scan | Fact is unavailable; integrity violation event raised | Restore from replica or replay from source |
| Conflicting knowledge | Two sources provide contradictory facts | Post-write conflict detection | Both facts are flagged; human review required | Manual or automated conflict resolution |
| Circular relationships | Fact A references Fact B which references Fact A | Cycle detection on write | Write is rejected or placed in Conflict state | Break the cycle by removing one reference |
| Missing evidence | Fact stored without provenance link | Schema validation | Warning logged; fact usable but low confidence | Link evidence retroactively or mark as low-confidence |
| Low confidence | Single source, partial verification | Automated confidence threshold check | Fact available but not used in critical reasoning paths | Seek additional sources or human verification |
| Outdated knowledge | Fact has been superseded but consumer uses old version | Version check on retrieval | Warning in retrieval result | Consumer must request latest version explicitly |
| Duplicate knowledge | Same fact written twice with different keys | Periodic deduplication scan | Both facts exist; confidence is split | Merge facts, supersede duplicate |
| Cross-tenant contamination | Tenant A writes to Tenant B's namespace | Tenant check on every write | **Critical security failure** | Immediate isolation, audit, restore from backup |
| Storage exhaustion | Knowledge_facts table grows beyond capacity | Storage monitoring | Write operations fail | Scale storage, archive old versions |
| Performance degradation | Index fragmentation, query pattern change | Latency monitoring | Retrieval slows | Re-index, optimize query patterns |

---

## 9. Observability

### Logging

| Event | Log Level | Data | Privacy Constraint |
|-------|-----------|------|-------------------|
| Fact created | INFO | fact_key, version, domain, tenant_id | No personal data |
| Fact superseded | INFO | fact_key, old_version, new_version | No personal data |
| Fact retrieved | DEBUG | fact_key, tenant_id, latency_ms | No personal data |
| Fact conflict detected | WARN | fact_key, versions, tenant_id | No personal data |
| Integrity violation | ERROR | fact_key, version, detail | No personal data |
| Cross-tenant contamination | CRITICAL | tenant_id, affected_keys | Escalate immediately |
| Storage warning | WARN | usage_pct, table_size | No personal data |
| Fact retired | INFO | fact_key, version, reason | No personal data |

### Tracing

- **Span: `knowledge.store`** — Full write lifecycle (validation → versioning → checksum → commit)
- **Span: `knowledge.retrieve`** — Full read lifecycle (key resolution → version selection → deserialization → checksum verify)
- **Span: `knowledge.search`** — Search query lifecycle (query parsing → index lookup → result assembly)
- **Span: `knowledge.verify`** — Integrity check lifecycle
- Trace context propagated from caller. Fact key included as a trace tag.

### Alerting

| Condition | Severity | Threshold |
|-----------|----------|-----------|
| Write failure rate > 1% | Pager | Per minute |
| Integrity violation detected | Pager | Immediate |
| Cross-tenant contamination | Pager | Immediate |
| Retrieval latency p99 > 500ms | Ticket | Per minute |
| Storage usage > 80% | Warning | Per hour |
| Conflict rate > 5% of writes | Warning | Per hour |
| Verification failure rate > 2% | Ticket | Per hour |

---

## 10. Metrics

| Metric | Type | Unit | Target | Measurement |
|--------|------|------|--------|-------------|
| `knowledge.facts_total` | Gauge | facts | N/A | Absolute count |
| `knowledge.facts_current` | Gauge | facts | N/A | Count of non-superseded facts |
| `knowledge.facts_by_domain` | Gauge | facts | N/A | Per domain |
| `knowledge.writes_total` | Counter | writes | N/A | Per second |
| `knowledge.reads_total` | Counter | reads | N/A | Per second |
| `knowledge.write_latency_p50` | Histogram | ms | < 10ms | Per write |
| `knowledge.write_latency_p99` | Histogram | ms | < 50ms | Per write |
| `knowledge.read_latency_p50` | Histogram | ms | < 5ms | Per read |
| `knowledge.read_latency_p99` | Histogram | ms | < 30ms | Per read |
| `knowledge.search_latency_p50` | Histogram | ms | < 50ms | Per search |
| `knowledge.search_latency_p99` | Histogram | ms | < 200ms | Per search |
| `knowledge.conflict_count` | Gauge | conflicts | N/A | Current unresolved conflicts |
| `knowledge.integrity_pass_rate` | Gauge | % | > 99.9% | Per integrity scan |
| `knowledge.storage_usage` | Gauge | bytes | N/A | Total table size |
| `knowledge.version_depth_p50` | Histogram | versions | N/A | Per fact key |

---

## 11. Rollback Strategy

### Rollback Triggers

- Data corruption detected by integrity scan
- Accidental mass deletion or supersession
- Cross-tenant contamination detected
- Faulty import or learning signal corrupts a broad set of facts
- Manual rollback authorized by the Chief Software Architect

### Rollback Procedure

1. **Freeze writes:** Stop accepting new fact writes at the Knowledge Engine boundary.
2. **Identify the corruption boundary:** Determine the last known-good version of each affected fact.
3. **Restore by re-versioning:** For each affected fact, create a new version with the known-good value. Do not delete the corrupted versions — they remain in the audit trail.
4. **Verify integrity:** Run a full integrity scan across all restored facts.
5. **Resume writes:** Reopen the write boundary.
6. **Audit:** Record the rollback in the governance changelog with full detail of affected facts and restoration action.

### Rollback Limitations

- The Knowledge Engine never deletes data. "Rollback" means creating new versions, not removing old ones. Corrupted versions remain in the history as a permanent record.
- Facts that were read by downstream consumers before the rollback are not recalled. The consumers' decisions may be based on the corrupted data.
- Mass rollback (restoring thousands of facts) must be tested before execution. The re-versioning process itself must be verified.

---

## 12. Migration Strategy (when applicable)

### Migration Type

Schema migration — the `knowledge_facts` table schema may evolve as new fact types, metadata fields, or indexing requirements are added.

### Migration Steps

1. **Pre-migration validation:** Verify all existing facts are valid under the new schema. Run a dry-run migration.
2. **Dual-write (if schema changes affect write path):** Write to both old and new schemas, log discrepancies.
3. **Backfill (if new columns are added):** Populate new columns from existing data where possible.
4. **Cutover:** Switch read and write paths to the new schema atomically.
5. **Post-migration verification:** Run integrity checks on all migrated facts, verify no data loss.

### Rollback During Migration

- Point-in-time: The pre-migration schema snapshot.
- Data consistency: All historical facts remain valid under the old schema. Migration is forward-only for the schema, but the old schema's data remains intact.
- Migration is zero-downtime if dual-write is used. Read-path migration requires a brief switch-over window.

---

## 13. Verification

### Unit Tests

- State transitions: 14 tests (one per transition in the transition table)
- Error handling: 9 tests (one per failure mode)
- Edge cases: 15 tests (empty value, null confidence, future dates, max key length, concurrent writes, duplicate keys, integrity violation, tenant isolation, etc.)

### Integration Tests

- Integration with Observer Layer: 4 tests (observation → fact creation, observation with missing evidence, observation with conflict)
- Integration with Reasoning Layer: 4 tests (fact retrieval, evidence chain assembly, confidence scoring, superseded fact handling)
- Integration with Learning Layer: 4 tests (learning signal → fact update, supersession, rollback)
- Integration with Governance Layer: 2 tests (policy definition storage and retrieval)
- Integration with Phase 4 (Privacy): 3 tests (eligibility gate on retrieval, tenant isolation, retention enforcement)
- Cross-tenant isolation: 4 tests (write isolation, read isolation, search isolation, bulk operation isolation)

### Security Review

- [ ] No eval/exec patterns — the Knowledge Engine uses parameterized queries, never eval
- [ ] No credential leakage — verify no credentials are stored as fact values without privacy classification
- [ ] Input validation — all fields validated before write
- [ ] Tenant isolation — every query scoped to tenant_id; integration test for cross-tenant leakage
- [ ] No SQL injection — all queries use parameterized SQLAlchemy queries

### Performance

- Latency budget: 10ms p50 write, 5ms p50 read, 50ms p50 search
- Memory budget: 512MB steady-state, 1GB peak
- Concurrent capacity: 500 writes/second, 2000 reads/second per instance
- Storage growth: Estimated 1GB per 1M facts (including version history)

---

## 14. Knowledge Model

### Categories of Knowledge

| Category | Description | Lifecycle | Example |
|----------|-------------|-----------|---------|
| **Facts** | Atomic pieces of information | Observed → Verified → Trusted → Superseded/Archived/Retired | "Bali requires a visa for Indian citizens" |
| **Entities** | Real-world objects (people, places, organizations) | Observed → Verified → Trusted → Superseded/Retired | "Hotel XYZ, 5-star, Ubud" |
| **Relationships** | Typed connections between entities | Observed → Verified → Trusted → Superseded/Retired | "Supplier ABC provides transport in Bali" |
| **Policies** | Business rules and governance constraints | Verified → Trusted → Superseded | "Minimum 60 days lead time for destination weddings" |
| **User Knowledge** | Individual user preferences, constraints, intents | Observed → Verified → Trusted → Superseded | "Customer prefers beachfront hotels" |
| **Workspace Knowledge** | Team/organizational context | Observed → Verified → Trusted → Superseded | "Team works 9 AM to 6 PM IST" |
| **Organizational Knowledge** | Company-wide facts, brand guidelines, standard procedures | Verified → Trusted → Superseded | "Standard markup is 25% on all bookings" |
| **Historical Knowledge** | Past events, outcomes, and decisions | Observed → Verified → Archived | "Lead PC10072601 was converted on 10 July 2026" |
| **Learned Knowledge** | Insights derived by the Learning Layer | Observed → Verified → Trusted | "Customers from Mumbai prefer direct flights to Bali" |
| **Derived Knowledge** | Computed from other facts (not directly observed) | Verified → Trusted → Superseded | "Average booking value for Q3 is ₹45,000" |
| **Context Snapshots** | Frozen workspace state for decision traceability | Observed → Archived | "Workspace state at time of proposal approval" |
| **Evidence Records** | Source references supporting other facts | Observed → Verified → Archived | "Email from supplier confirming rate of ₹5,000/night" |

### Lifecycle

Every knowledge category follows the same lifecycle but may enter at different states:

- **Facts** enter at `Observed` (from observation, learning, import) or `Verified` (from human assertion)
- **Policies** enter at `Verified` (must pass validation before being active)
- **User Knowledge** enters at `Observed` (must be verified before use in critical decisions)
- **Historical Knowledge** enters at `Observed` and transitions to `Archived` without passing through `Trusted`
- **Evidence Records** enter at `Observed` and remain `Observed` — they are not independently verified

---

## 15. Immutability

### Versioning Strategy

Every fact mutation creates a new version. The version number is a monotonically increasing integer scoped to the fact key. Version 1 is the initial write. Version 2 is the first supersession. There is no upper bound on version count.

```
fact_key: "destination.bali.visa"
  Version 1: "Visa required for Indian citizens" (created 2026-01-01)
  Version 2: "Visa on arrival for Indian citizens" (created 2026-06-15, supersedes v1)
  Version 3: "Visa-free for Indian citizens" (created 2026-07-01, supersedes v2)
```

### Knowledge History

The complete history of every fact is always queryable. The `history(fact_key)` operation returns all versions in ascending order, from oldest to newest. Each version record includes:

- The fact value (deserialized)
- Version number
- Created timestamp
- Superseded timestamp (null if current)
- Creator identity
- Source
- Evidence
- Confidence
- Checksum

### Superseded Knowledge

When a fact is superseded:

1. The previous `current` version has its `superseded_at` timestamp set to the current time.
2. A new version is created with `version = previous_version + 1` and `superseded_at = null`.
3. The previous version's checksum is preserved. The new version's checksum is computed from its content.
4. Superseded versions remain in the database and are queryable by explicit `history()` call.

### Conflict Resolution

When two sources provide contradictory facts:

1. Both facts are stored as separate versions.
2. A `Conflict` record is created linking both versions.
3. The system does not automatically resolve the conflict — it requires human or trusted-source intervention.
4. Resolution creates a new version marked as `Trusted`, and the conflicting versions are marked as `Superseded` with a reference to the resolution.

### Rollback

Rollback is achieved by creating a new version with the restored value. The corrupted versions remain in the history with a note that they were rolled back. This is not a true rollback (no data is deleted), but it achieves the same effect for downstream consumers (they see the correct value).

### Temporal Validity

Every fact has:

- `valid_from` — The date/time from which this fact is considered true. Defaults to creation time.
- `valid_until` — The date/time after which this fact is no longer considered true. Null means no expiry.

Temporal queries can retrieve the state of knowledge at any point in time:

```
get_fact_at(fact_key, "2026-06-01T00:00:00Z") → Version 1 (valid at that date)
get_fact_at(fact_key, "2026-07-10T00:00:00Z") → Version 3 (valid at that date)
```

### Auditability

Every fact mutation is auditable:

- Who created it (created_by)
- When (created_at)
- What changed (value diff between versions)
- Why (evidence field)
- From where (source field)
- What was the previous version (superseded references)

---

## 16. Knowledge Retrieval

### Semantic Retrieval

Semantic retrieval matches fact values by meaning, not by exact string. This requires a vector embedding index. The Knowledge Engine provides a pluggable interface for semantic search providers (pgvector, external vector database).

**Contract:**
```
search_semantic(query: string, domain: string, top_k: int, threshold: float)
  → KnowledgeSearchResult
```

### Structured Retrieval

Structured retrieval matches facts by exact key, domain, category, or tags. This is the primary retrieval path and does not require any AI infrastructure.

**Contract:**
```
get(fact_key: string) → KnowledgeRetrievalResult | null
get_by_domain(domain: string, category: string) → KnowledgeRetrievalResult[]
search(query: string, filters: Filter[]) → KnowledgeSearchResult
```

### Hybrid Retrieval

Hybrid retrieval combines semantic and structured approaches, returning results ranked by a weighted combination of semantic similarity and structured filter match.

### Temporal Retrieval

Temporal retrieval returns the state of knowledge at a specific point in time. This is essential for:

- Replaying past decisions with the knowledge available at the time
- Auditing decisions against the knowledge that was available
- Temporal analysis of knowledge evolution

**Contract:**
```
get_at_time(fact_key: string, timestamp: datetime) → KnowledgeRetrievalResult | null
get_history(fact_key: string) → KnowledgeRetrievalResult[]
```

### Relationship Traversal

Relationship traversal follows links between entities. Given a fact key, it returns all facts that reference it and all facts it references.

**Contract:**
```
traverse(fact_key: string, direction: "incoming" | "outgoing" | "both", depth: int)
  → KnowledgeRetrievalResult[]
```

### Evidence Retrieval

Evidence retrieval returns the full provenance chain for a fact, including all source references, supporting facts, and contradicting facts.

**Contract:**
```
get_evidence_chain(fact_key: string) → EvidenceChain
```

### Confidence Scoring

Every fact carries a confidence score (0.0 to 1.0). Retrieval can filter by minimum confidence:

```
get(fact_key, min_confidence=0.7) → Returns fact only if confidence >= 0.7
```

Confidence is updated as facts progress through the lifecycle:
- `Observed` → Initial confidence from source (0.3–0.7)
- `Verified` → Increased confidence (0.7–0.9)
- `Trusted` → High confidence (0.9–1.0)

---

## 17. Data Model

### Logical Schema

```
KnowledgeItem:
  id: int                          — Primary key
  fact_key: string                 — Unique identifier within domain
  version: int                     — Monotonically increasing per fact_key
  domain: string                   — "travel" | "healthcare" | "legal" | etc.
  category: string                 — "visa" | "tax" | "venue" | "policy" | etc.
  value: text                      — Serialized fact value (JSON for complex types)
  value_type: string               — "text" | "json" | "number" | "markdown" | "boolean"
  confidence: float                — 0.0 to 1.0
  evidence: text                   — Source or reasoning
  source: string                   — "manual" | "web_scrape" | "reasoning" | "learning" | etc.
  checksum: string                 — SHA-256 of domain:fact_key:version:value
  created_by: string               — Creator identifier
  superseded_at: datetime|null     — When this version was superseded
  valid_from: datetime             — Fact validity start
  valid_until: datetime|null       — Fact validity end
  tenant_id: int                   — Owning tenant
  workspace_id: int|null           — Owning workspace
  tags: string[]                   — Arbitrary categorization tags
  created_at: datetime             — Record creation time

Evidence:
  id: int                          — Primary key
  knowledge_item_id: int           — FK to KnowledgeItem
  source_reference_id: int         — FK to SourceReference (Phase 7)
  evidence_type: string            — "source" | "supporting_fact" | "contradicting_fact"
  description: text                — Description of the evidence link
  created_at: datetime             — Record creation time

Relationship:
  id: int                          — Primary key
  source_fact_key: string          — Source fact
  target_fact_key: string          — Target fact
  relationship_type: string        — "supports" | "contradicts" | "derives_from" | "references" | etc.
  confidence: float                — 0.0 to 1.0
  created_by: string               — Creator identifier
  created_at: datetime             — Record creation time

Source:
  id: int                          — Primary key
  name: string                     — Human-readable source name
  source_type: string              — "api" | "document" | "human" | "system" | "import"
  reliability: float               — 0.0 to 1.0
  metadata: json                   — Arbitrary source metadata
  created_at: datetime             — Record creation time

Version:
  (Inline within KnowledgeItem — version is a column, not a separate table)
  Each fact_key has N rows, one per version, ordered by version number.

Confidence:
  (Inline within KnowledgeItem — confidence is a column)
  Updated as facts progress through the lifecycle.

Validity:
  (Inline within KnowledgeItem — valid_from and valid_until are columns)

Ownership:
  (Inline within KnowledgeItem — created_by and tenant_id are columns)

Tenant:
  (ForeignKey to the Tenant model — tenant_id is a column on every KnowledgeItem)

Workspace:
  (Optional ForeignKey to a Workspace model — workspace_id is a nullable column)

Metadata:
  tags: string[] — stored as a PostgreSQL array column, or as a JSON column for more complex metadata
```

### Index Strategy

| Index | Columns | Purpose |
|-------|---------|---------|
| Primary | (fact_key, version) | Unique fact version lookup |
| Current lookup | (fact_key) WHERE superseded_at IS NULL | Fast current-version retrieval |
| Domain search | (domain, category, superseded_at) | Domain-scoped queries |
| Tenant isolation | (tenant_id, fact_key) | Tenant-scoped operations |
| Temporal query | (valid_from, valid_until, superseded_at) | Time-based fact retrieval |
| Tag search | (tags, superseded_at) | Tag-based filtering |
| Full-text search | (value) GIN index | Text search on fact values |

---

## 18. Security

### Tenant Isolation

Every fact is explicitly scoped to a `tenant_id`. All queries — read, write, search, history — are scoped to the requesting tenant's identifier. No query can access facts from another tenant without explicit cross-tenant authorization (which is not part of the Knowledge Engine's scope).

### Workspace Isolation

Facts may optionally be scoped to a `workspace_id`. Workspace-scoped facts are visible only to consumers operating within that workspace. Workspace isolation is a logical subset of tenant isolation.

### Encryption

Fact values are stored in plaintext in the database. If encryption at rest is required, it is provided by the database layer (PostgreSQL TDE or filesystem encryption). The Knowledge Engine does not implement application-level encryption of fact values.

### Privacy

Privacy-sensitive facts must be classified with appropriate sensitivity levels (via Phase 4 integration). The Knowledge Engine provides a `privacy_decision_id` column on each fact for linkage to privacy decisions. Retrieval can be gated by Phase 4 eligibility checks.

### Retention

The Knowledge Engine supports configurable retention policies per domain, category, and tenant. Retention policies are enforced by the `Archived` and `Retired` states. Facts in the `Retired` state may be physically deleted in accordance with the retention policy, but a tombstone record (fact_key, version, checksum, retirement_reason) must remain.

### Deletion Policy

The Knowledge Engine does not support hard deletion of individual facts. The only permitted deletion path is:

1. Supersede the fact (creates a new version)
2. Archive the superseded version (moves it out of active queries)
3. Retire the archived version (marks it for physical deletion)
4. Physical deletion per retention policy (after retention period expires)

### Right to Be Forgotten

The right to be forgotten is implemented through supersession, not deletion:

1. A new version of the fact is created with the personal data removed or anonymized.
2. The old version is superseded and marked with the privacy decision reference.
3. The old version remains in the audit trail but is excluded from all non-audit queries.
4. If full deletion is legally required, the fact is moved to `Retired` state and physically deleted after the retention period, with only a tombstone remaining.

---

## 19. Constitutional Mapping

| Responsibility | Constitutional Principle | Source |
|---------------|------------------------|--------|
| Immutable fact storage — never overwrite | 6.4 Immutable Knowledge | SHUNYA_ARCHITECTURE.md §6.4 |
| Version history for complete traceability | 6.4 Immutable Knowledge | SHUNYA_ARCHITECTURE.md §6.4 |
| No hidden edits, no disappearing evidence | 4.3 No Disappearing Evidence | SHUNYA_ENGINEERING_CONSTITUTION.md §4.3 |
| Every recommendation traceable to source evidence | 6.5 Explainable Decisions | SHUNYA_ARCHITECTURE.md §6.5 |
| Evidence chain with Decision + Confidence + Evidence + Explanation | 6.5 Explainable Decisions | SHUNYA_ARCHITECTURE.md §6.5 |
| Least Authority — only facts needed are provided | 6.3 Principle of Least Authority | SHUNYA_ARCHITECTURE.md §6.3 |
| Tenant isolation | 6.7 Architectural Trust | SHUNYA_ARCHITECTURE.md §6.7 |
| Knowledge verified by integrity checksums | 6.4 Immutable Knowledge | SHUNYA_ARCHITECTURE.md §6.4 |
| Learning feeds into Knowledge (not back into live credentials) | 6.4 Learning Layer constraint | SHUNYA_ARCHITECTURE.md §5 (Learning Layer) |
| Privacy gates on sensitive knowledge | 4.3 No Disappearing Evidence | SHUNYA_ENGINEERING_CONSTITUTION.md §4.3 |

---

## 20. Layer Responsibilities

### The Knowledge Engine SHALL

- Store facts immutably with version tracking
- Retrieve facts by key, domain, category, temporal range, and confidence
- Verify integrity via SHA-256 checksums
- Enforce tenant isolation on all operations
- Maintain complete fact history
- Support temporal queries (knowledge at a point in time)
- Provide confidence scores with every fact
- Accept observations from the Observer Layer
- Accept learning signals from the Learning Layer
- Provide evidence chains to the Reasoning Layer
- Provide policy definitions to the Governance Layer
- Provide workspace context to the Context Fusion service
- Support bulk operations for ingestion and migration
- Log all mutations for auditability

### The Knowledge Engine SHALL NEVER

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never reason about facts | Would violate Separation of Responsibilities | Reasoning Layer |
| Never execute actions | Would violate Separation of Responsibilities | Executor Layer |
| Never govern | Would violate Layer Boundaries | Governance Layer |
| Never learn independently | Would violate Layer Boundaries | Learning Layer |
| Never access credentials | Would violate Least Authority Principle | Credential Store / Adapter Layer |
| Never observe reality | Would violate Layer Boundaries | Observer Layer |
| Never generate plans | Would violate Layer Boundaries | Planner Layer |
| Never delete facts permanently | Would violate Immutability | Privacy / Retention |
| Never modify fact values in place | Would violate Immutability | (none — this is the core principle) |
| Never serve unverified facts as truth | Would violate Explainable Decisions | (confidence scoring exists) |

---

## 21. Interaction Matrix

| Layer | Reads | Writes | Events Published | Events Consumed |
|-------|-------|--------|-----------------|-----------------|
| **Observer** | — | Observations become facts | `knowledge.fact.created` | `observation.recorded` |
| **Learning** | Existing facts for context | Learned facts, improvements | `knowledge.fact.created`, `knowledge.fact.superseded` | `learning.signal.generated` |
| **Reasoning** | Evidence chains, destination facts | — | — | `knowledge.fact.created`, `knowledge.fact.superseded` |
| **Planner** | Destination knowledge, supplier data, past itineraries | — | — | `knowledge.fact.created` |
| **Governance** | Policy definitions | — | — | `knowledge.fact.superseded` |
| **Context Fusion** | Workspace context items | — | — | `knowledge.fact.created`, `knowledge.fact.superseded` |
| **Phase 11 (Knowledge Resolution)** | Knowledge sufficiency evaluation | — | — | — |
| **Phase 4 (Privacy)** | — | Privacy decisions linked to facts | `knowledge.fact.retired` | `knowledge.fact.created` |
| **Phase 7 (Evidence)** | — | Source references for provenance | — | `knowledge.fact.created` |
| **Document Service** | — | Extracted fields as facts | `knowledge.fact.created` | `document.field.extracted` |
| **Doctor** | Integrity verification | — | `knowledge.integrity.violation` | — |

---

## 22. Complexity Analysis

### CPU Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Fact write (single) | O(1) | One INSERT + one UPDATE (supersede previous) |
| Fact retrieval by key | O(log N) | B-tree index on fact_key |
| Fact search by domain | O(log N + M) | B-tree index scan + filter |
| Semantic search | O(N * D) | Vector similarity search (N = fact count, D = vector dimension) |
| Temporal retrieval | O(log N) | B-tree index on valid_from/valid_until |
| History retrieval | O(V) | V = version count for the fact key |
| Integrity scan (full) | O(N) | Full table scan with checksum recomputation |
| Conflict detection | O(N^2) worst case | Pairwise comparison within domain |
| Deduplication | O(N log N) | Sort + compare by normalized value |

### Memory Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Read path | O(result_size) | Fact values deserialized on read |
| Write path | O(1) | Single fact value held in memory |
| Search results | O(page_size) | Configurable page size (default 20) |
| Integrity scan | O(1) | Streaming — one fact at a time |
| Semantic search index | O(N * D) | Vector index in memory (optional) |

### Storage Growth

| Component | Growth Rate | Notes |
|-----------|-------------|-------|
| Fact values | ~1KB per fact + version overhead | 1M facts ≈ 1GB |
| Version history | ~1KB per version | 5 versions/fact average ≈ 5GB |
| Indexes | ~20% of table size | B-tree indexes |
| Checksums | 64 bytes per version | SHA-256 hex |
| Total estimate | ~1.5GB per 1M current facts, ~7.5GB with 5x version history | Conservative estimate |

### Scaling Bottlenecks

| Bottleneck | Stage | Mitigation |
|------------|-------|------------|
| Write throughput | Versioning + checksum computation | Batch writes, async checksum |
| Semantic search latency | Vector similarity computation | Approximate nearest neighbor (ANN) index |
| Full integrity scan | Checksum recomputation | Incremental integrity checks (scan recent versions only) |
| History retrieval | Version count per fact | Pagination, version limit per query |
| Conflict detection | Pairwise comparison | Only run on newly written facts within same domain |

### Failure Isolation

- **Read failure:** Does not affect writes. Consumers receive errors for individual fact keys.
- **Write failure:** Does not affect reads. Previous versions remain readable.
- **Index corruption:** Does not affect data integrity. Index rebuild possible.
- **Storage full:** Writes fail, reads continue. Alerting triggers before exhaustion.
- **Cross-tenant contamination:** Isolated to a single tenant's operation. Full audit trail.

---

## 23. Future Extensions

The following capabilities are anticipated but not specified for implementation. They are documented here to inform the architecture and avoid design decisions that would preclude them.

### 23.1 Knowledge Graph

A fully connected graph of entities and relationships, enabling graph traversal queries (shortest path, centrality, community detection) across the entire knowledge base.

### 23.2 Vector Memory

Persistent vector embeddings for every fact, enabling similarity search across the entire knowledge base without requiring a separate vector database.

### 23.3 Graph Retrieval

Retrieval augmented by graph traversal — given a seed fact, traverse the relationship graph to find related facts, rank by relevance, and return as a context bundle.

### 23.4 Ontology Engine

A formal ontology layer that defines the types, categories, relationships, and constraints for every domain. The ontology drives validation, inference, and query optimization.

### 23.5 Cross-Workspace Reasoning

The ability to query knowledge across workspace boundaries within the same tenant, enabling insights that span teams, departments, or business units.

### 23.6 Federated Knowledge

The ability to query knowledge across tenant boundaries for authorized use cases (e.g., a parent company querying aggregate data across subsidiaries without exposing individual records).

### 23.7 Knowledge Compression

Automatic deduplication, consolidation, and summarization of redundant or overlapping facts to reduce storage growth and improve retrieval relevance.

### 23.8 Automated Fact Verification

Integration with external fact-checking services or automated verification workflows that validate facts against authoritative sources before they reach Trusted state.

### 23.9 Knowledge Impact Analysis

Given a proposed fact change, predict which downstream consumers, decisions, and workflows would be affected. Enables safe policy updates and data corrections.

### 23.10 Temporal Knowledge Graph

A knowledge graph where edges are time-aware — supporting queries like "what was the relationship between X and Y during June 2026?"

---

## 24. References

- [SHUNYA_ARCHITECTURE.md](/SHUNYA_ARCHITECTURE.md) — Sections 5 (Knowledge Layer), 6.3, 6.4, 6.5, 6.7
- [SHUNYA_ENGINEERING_CONSTITUTION.md](/governance/SHUNYA_ENGINEERING_CONSTITUTION.md) — Articles 1, 2, 4
- [SHUNYA_GOVERNANCE_MODEL.md](/governance/SHUNYA_GOVERNANCE_MODEL.md) — Roles, decision types, approval hierarchy
- [ES-001-GOVERNANCE-ENGINE.md](/governance/engine_specs/ES-001-GOVERNANCE-ENGINE.md) — Governance Engine specification
- [VERIFICATION_CHECKLIST.md](/governance/verification/VERIFICATION_CHECKLIST.md) — Standard verification protocol
- [GOVERNANCE_CHANGELOG.md](/governance/GOVERNANCE_CHANGELOG.md) — Governance change history
- `app/shunya/knowledge.py` — Current KnowledgeLayer implementation (189 lines)
- `app/shunya/knowledge_store.py` — Current ImmutableKnowledgeStore implementation (383 lines)
- `app/knowledge/__init__.py` — Phase 11 Knowledge Resolution (computation-only, 292 lines)
- `app/evidence/models.py` — Phase 7 Evidence models
- `app/privacy/models.py` — Phase 4 Privacy models