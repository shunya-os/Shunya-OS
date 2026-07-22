# SHUNYA Core Models

**Status:** Draft Architecture Standard
**Authority:** SHUNYA Constitution, SHUNYA Architecture, SHUNYA Engineering Constitution, Governance Baseline v1.0
**Version:** 1.0
**Date:** 2026-07-18
**Author:** Chief Software Architect

---

## Section 1 — Purpose

### Why Canonical Models Exist

Every engine within SHUNYA operates on the same underlying concepts: objects, identities, evidence, confidence, provenance, and events. When each engine defines these concepts independently, architectural divergence is inevitable. The Knowledge Engine's "fact" and the Governance Engine's "policy" and the Reasoning Engine's "evidence" — if each defines its own structure — cannot be composed into a coherent system.

Canonical models exist to guarantee that:

- **A fact written by the Knowledge Engine is the same type of thing read by the Reasoning Engine.**
- **An evidence chain produced by the Knowledge Engine is consumable by the Governance Engine without transformation.**
- **A confidence score from the Reasoning Engine means the same thing as a confidence score from the Learning Engine.**
- **An event published by any engine is consumable by any other engine without schema negotiation.**
- **An identity resolved by the Identity Engine is the same identity referenced by the Relationship Engine.**

### Why No Engine May Redefine These Concepts Independently

Every engine specification shall reference this document for shared concepts. An engine may extend a canonical model with engine-specific fields, but it may not:

- Redefine the core structure of a canonical model
- Change the semantics of a canonical field (e.g., declaring confidence as 0–100 when the canonical scale is 0.0–1.0)
- Ignore a mandatory canonical field
- Introduce a competing identity system
- Invent a proprietary event format

Violations are architectural divergence as defined in the SHUNYA Engineering Constitution, Article 8.

---

## Section 2 — Universal Object Model

### Inheritance Hierarchy

```
UniversalObject
    │
    ├── Entity
    │       ├── Person
    │       ├── Organization
    │       ├── Place
    │       ├── Document
    │       ├── Conversation
    │       ├── Event
    │       ├── Policy
    │       ├── Workflow
    │       ├── Asset
    │       ├── Product
    │       ├── Task
    │       └── KnowledgeItem
    │
    ├── Relationship
    │       ├── Ownership
    │       ├── Membership
    │       ├── Reference
    │       ├── Derivation
    │       ├── Support
    │       └── Contradiction
    │
    └── Activity
            ├── Observation
            ├── Decision
            ├── Action
            ├── Mutation
            └── Communication
```

### UniversalObject — Mandatory Fields

Every object in the system, regardless of type, MUST include these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `object_id` | UUID (v7) | Yes | Globally unique identifier. Never reused. |
| `tenant_id` | Integer | Yes | Owning tenant. All objects are tenant-scoped. |
| `workspace_id` | Integer | No | Owning workspace within the tenant (optional). |
| `created_at` | datetime (UTC) | Yes | When the object was first created. Immutable. |
| `updated_at` | datetime (UTC) | Yes | When the object was last modified. |
| `created_by` | String | Yes | Engine or human that created the object. |
| `updated_by` | String | Yes | Engine or human that last modified the object. |
| `status` | String | Yes | Object lifecycle status. Varies by type but all include `active`, `superseded`, `archived`. |
| `version` | Integer | Yes | Monotonically increasing. Starts at 1. |
| `confidence` | Float (0.0–1.0) | Yes | Canonical confidence score. See Section 7. |
| `evidence` | Evidence[] | No | Evidence chain supporting this object. See Section 5. |
| `metadata` | JSON | No | Arbitrary key-value metadata. Engine-specific. |
| `relationships` | Relationship[] | No | Typed links to other UniversalObjects. |

### Entity — Additional Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | Yes | Human-readable display name. |
| `description` | Text | No | Human-readable description. |
| `tags` | String[] | No | Categorization tags. |
| `aliases` | String[] | No | Alternative names or identifiers. |

### Relationship — Additional Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | UUID | Yes | The source object of the relationship. |
| `target_id` | UUID | Yes | The target object of the relationship. |
| `relationship_type` | String | Yes | The type of relationship (see hierarchy above). |
| `direction` | String | Yes | `directed` or `undirected`. |
| `strength` | Float (0.0–1.0) | No | Strength or weight of the relationship. |

### Activity — Additional Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `actor_id` | UUID | Yes | The entity that performed the activity. |
| `action_type` | String | Yes | The type of action performed. |
| `object_id` | UUID | Yes | The object the activity was performed on. |
| `outcome` | String | No | The outcome of the activity. |
| `duration_ms` | Integer | No | How long the activity took. |

---

## Section 3 — Identity Model

### Identity Resolution Principles

1. **Identity is globally unique.** A person, organization, or channel has exactly one canonical identity within a tenant. Duplicate identities are detected and merged, never created.
2. **Identity is resolved deterministically.** The same input always produces the same resolution outcome. No randomness, no LLM calls.
3. **Identity is never silently merged.** Ambiguous resolutions produce an `AMBIGUOUS` result that requires human intervention.
4. **Identity is versioned.** If a person's identity changes (e.g., new email, name change), the identity record is superseded, not overwritten.

### Identity Types

| Identity Type | Example | Strength | Uniqueness Guarantee |
|---------------|---------|----------|----------------------|
| `email` | `user@example.com` | Strong | Normalized (lowercase, stripped) |
| `phone` | `+919999999999` | Strong | Normalized (E.164 format) |
| `channel:whatsapp` | `919999999999` | Strong | Per-channel normalized |
| `channel:telegram` | `123456789` | Strong | Per-channel |
| `document_id` | `PASSPORT_INDIA_1234` | Strong | Issuer-scoped |
| `external_id` | `CRM_CUST_1001` | Medium | Provider-scoped |
| `alias` | `Johnny` | Weak | No uniqueness guarantee |
| `merged` | (reference to primary identity) | — | Merged identity points to canonical |

### Identity Lifecycle

```
Active
  │
  ├──[verified]──→ Verified
  │
  ├──[superseded_by_new_identity]──→ Superseded
  │
  └──[merged_into_canonical]──→ Merged
```

### Identity Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `identity_id` | UUID | Yes | Unique identity record ID. |
| `person_id` | UUID | Yes | The canonical person this identity belongs to. |
| `identity_type` | String | Yes | One of the types above. |
| `identity_value` | String | Yes | The raw identity value. |
| `normalized_value` | String | Yes | Normalized form for lookup. |
| `verification_state` | String | Yes | `unverified`, `verified`, `failed`. |
| `confidence` | Float | Yes | Confidence in this identity-to-person mapping. |
| `status` | String | Yes | `active`, `superseded`, `merged`. |
| `provenance` | Provenance | Yes | Where this identity was first observed. |
| `created_at` | datetime | Yes | When this identity was registered. |
| `superseded_at` | datetime | No | When this identity was superseded. |
| `merged_into_id` | UUID | No | If merged, the canonical identity ID. |

---

## Section 4 — Knowledge Hierarchy

### Canonical Hierarchy

```
Observation ─── Raw data from reality. Unprocessed, unverified.
    │
    ▼
    Fact ───────── Verified observation. Structured, confidence-scored.
    │
    ▼
    Knowledge ──── Integrated facts. Cross-referenced, contextualized.
    │
    ▼
    Wisdom ─────── Applied knowledge. Actionable, experience-informed.
```

### Transitions

| Transition | Trigger | Confidence Change | Ownership |
|------------|---------|-------------------|-----------|
| Observation → Fact | Verification by the Knowledge Engine | 0.3–0.7 → 0.7–0.9 | Observer → Knowledge |
| Fact → Knowledge | Integration by the Reasoning Engine | 0.7–0.9 → 0.8–0.95 | Knowledge → Reasoning |
| Knowledge → Wisdom | Application by the Governance Engine | 0.8–0.95 → 0.9–1.0 | Reasoning → Governance |

### Ownership

| Level | Owner | Responsibility |
|-------|-------|----------------|
| Observation | Observer Layer | Record reality. No interpretation. |
| Fact | Knowledge Engine | Store, version, verify. Immutable. |
| Knowledge | Reasoning Engine | Integrate, contextualize, infer. |
| Wisdom | Governance Engine | Apply, evaluate, decide. |

### Confidence Evolution

- **Observation:** 0.1–0.5 (single source, unverified)
- **Fact:** 0.5–0.9 (verified, provenance established)
- **Knowledge:** 0.7–0.95 (cross-referenced, consistent)
- **Wisdom:** 0.9–1.0 (applied successfully, outcome confirmed)

---

## Section 5 — Evidence Model

### Evidence

An evidence record is a link between a claim and the source that supports or contradicts it.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `evidence_id` | UUID | Yes | Unique evidence record ID. |
| `claim_id` | UUID | Yes | The claim being supported or contradicted. |
| `source_id` | UUID | Yes | The source reference. |
| `relationship` | String | Yes | `supports`, `contradicts`, `qualifies`, `supersedes`, `duplicates`, `derived_from`, `references`. |
| `weight` | Float (0.0–1.0) | Yes | How much weight this evidence carries. |
| `quality` | Float (0.0–1.0) | Yes | Quality of the evidence (source reliability + collection method). |
| `confidence` | Float (0.0–1.0) | Yes | Confidence in this evidence link. |
| `created_at` | datetime | Yes | When the evidence was recorded. |
| `expires_at` | datetime | No | When the evidence expires (temporal validity). |

### Observation

An observation is the raw recording of reality before any verification.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `observation_id` | UUID | Yes | Unique observation ID. |
| `observer_id` | UUID | Yes | The engine or human that made the observation. |
| `observed_at` | datetime | Yes | When the observation was made. |
| `content` | Text | Yes | The raw observation content. |
| `confidence` | Float | Yes | Observer's confidence in the observation. |
| `source` | Source | Yes | The source of the observation. |

### Claim

A claim is a statement that can be supported or contradicted by evidence.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claim_id` | UUID | Yes | Unique claim ID. |
| `claim_key` | String | Yes | Canonical claim identifier (e.g., "entity.hotel.star_rating"). |
| `value` | Any | Yes | The claim value. |
| `claim_type` | String | Yes | `fact`, `assertion`, `inference`, `prediction`, `policy`. |
| `status` | String | Yes | `unverified`, `supported`, `contradicted`, `conflict`, `no_evidence`. |

### Verification

Verification is the process of confirming a claim against evidence.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verification_id` | UUID | Yes | Unique verification ID. |
| `claim_id` | UUID | Yes | The claim being verified. |
| `verifier_id` | UUID | Yes | The engine or human performing verification. |
| `result` | String | Yes | `confirmed`, `rejected`, `inconclusive`. |
| `confidence` | Float | Yes | Confidence in the verification result. |
| `verified_at` | datetime | Yes | When verification occurred. |
| `method` | String | Yes | `automated`, `cross_reference`, `human_review`, `external_validation`. |

### Source

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | UUID | Yes | Unique source ID. |
| `source_type` | String | Yes | `api`, `document`, `human`, `system`, `import`, `external`. |
| `reliability` | Float (0.0–1.0) | Yes | Historical reliability of this source. |
| `name` | String | Yes | Human-readable source name. |
| `metadata` | JSON | No | Source-specific metadata. |

### Evidence Quality

`evidence_quality = source_reliability * collection_method_reliability * freshness_factor`

| Collection Method | Reliability |
|------------------|-------------|
| Direct observation | 0.95 |
| Verified API | 0.90 |
| Document extraction | 0.80 |
| Human assertion (verified) | 0.75 |
| Human assertion (unverified) | 0.40 |
| Inference | 0.60 |
| External import | 0.50–0.90 (source-dependent) |

### Evidence Weight

`evidence_weight = evidence_quality * confidence_in_evidence_link`

### Evidence Lifetime

Evidence expires when its source expires or when a superseding observation is made. The `expires_at` field on the evidence record determines when the evidence is no longer considered valid. Expired evidence is not deleted — it is marked as `expired` and excluded from active queries.

### Evidence Relationships

Evidence records relate to each other through the same relationship types as UniversalObjects: `supports`, `contradicts`, `qualifies`, `supersedes`, `duplicates`, `derived_from`, `references`.

### Evidence Versioning

When a source is re-observed, a new evidence record is created. The old evidence record is marked as `superseded` with a link to the new record. Evidence is never updated in place.

---

## Section 6 — Provenance Model

### Every Object Shall Answer

| Question | Field | Always Present? |
|----------|-------|-----------------|
| Where did this originate? | `provenance.origin` | Yes |
| Who observed it? | `provenance.observer` | Yes |
| Who modified it? | `provenance.modified_by[]` | Yes (at least one entry) |
| When? | `provenance.created_at`, `provenance.modified_at[]` | Yes |
| Why? | `provenance.reason` | Yes |
| Which engine? | `provenance.engine` | Yes |
| Which model? | `provenance.model_version` | Yes |
| Which evidence? | `provenance.evidence_ids[]` | No (empty if no evidence) |

### Provenance Record

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `origin` | String | Yes | Where the object originated. One of: `observation`, `inference`, `import`, `manual`, `derivation`, `external`. |
| `observer` | String | Yes | The engine or human that first observed the object. |
| `engine` | String | Yes | The engine that created the object. |
| `model_version` | String | Yes | The version of the engine or model. |
| `reason` | String | Yes | Why the object was created or modified. |
| `created_at` | datetime | Yes | When the object was first created. |
| `modified_by` | ProvenanceModification[] | Yes | List of all modifications. At least one entry (the creation). |
| `evidence_ids` | UUID[] | No | Links to evidence supporting the object. |

### ProvenanceModification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `modified_by` | String | Yes | Engine or human that made the modification. |
| `modified_at` | datetime | Yes | When the modification occurred. |
| `reason` | String | Yes | Why the modification was made. |
| `previous_version` | Integer | Yes | Version before modification. |
| `new_version` | Integer | Yes | Version after modification. |
| `change_summary` | String | Yes | Human-readable summary of what changed. |

### Version History

Every object carries a `version` field (integer, monotonically increasing). The complete version history is queryable through the Provenance record's `modified_by` array. There is no upper bound on version count per object.

### Audit History

The Provenance record, combined with the immutable audit trail in the Governance Engine, provides a complete audit history for every object:

- What was the object's state at time T? → Version history + temporal query
- Who changed it and why? → Provenance modification records
- Was this change governed? → Governance audit log (cross-reference)
- What evidence supported this change? → Evidence IDs in provenance

---

## Section 7 — Confidence Model

### Scale

Confidence is expressed as a single float in the range **0.0 (no confidence) to 1.0 (absolute certainty)**.

No engine, specification, or implementation may use:

- Integer scales (0–100, 1–5, 1–10)
- Categorical scales (low, medium, high)
- String-based confidence
- Negative confidence
- Confidence > 1.0

### Meaning

| Range | Label | Meaning |
|-------|-------|---------|
| 0.0–0.2 | Speculative | No reliable evidence. May be incorrect. |
| 0.2–0.4 | Weak | Single unverified source. Needs confirmation. |
| 0.4–0.6 | Moderate | Some evidence. Reasonable but not reliable. |
| 0.6–0.8 | Strong | Verified from multiple sources. Reliable. |
| 0.8–0.95 | Very Strong | Multiple independent verifications. Highly reliable. |
| 0.95–1.0 | Certain | Indisputable. Human-confirmed or mathematically proven. |
| 1.0 | Absolute | Reserved for mathematical truths and system invariants. |

### Propagation

When a new fact is derived from existing facts, the derived confidence is:

```
derived_confidence = min(confidence_of_inputs) * derivation_quality
```

Where `derivation_quality` is the reliability of the derivation method (0.0–1.0).

### Combination

When multiple independent sources confirm the same fact:

```
combined_confidence = 1 - ∏(1 - confidence_i)
```

Where `confidence_i` is the confidence from each independent source. Sources must be provably independent for this formula to apply. If sources are not independent, the highest single confidence is used.

### Decay

Confidence decays over time when a fact is not re-verified. The decay function:

```
current_confidence = original_confidence * decay_rate^(days_since_verification / half_life_days)
```

Where `decay_rate = 0.5` (half-life model). Each fact type has a configurable `half_life_days`:

| Fact Type | Half-Life | Example |
|-----------|-----------|---------|
| Static fact | 365 days | "Paris is the capital of France" |
| Seasonal fact | 90 days | "Hotel peak season dates" |
| Dynamic fact | 30 days | "Hotel room rate" |
| Volatile fact | 7 days | "Weather forecast" |
| Learned fact | 60 days | "Customer preference from Learning Layer" |

### Increase

Confidence increases when:

- An independent source confirms the fact (see Combination formula)
- A human with authority explicitly confirms the fact (confidence set to 0.95)
- The fact is successfully applied in a decision (confidence increases by 0.05, up to 0.95)

### Thresholds

| Threshold | Meaning | Used By |
|-----------|---------|---------|
| 0.3 | Minimum for any downstream use | All engines |
| 0.5 | Minimum for automated decision-making | Reasoning Layer |
| 0.7 | Minimum for financial or commitment actions | Governance Layer |
| 0.9 | Minimum for irreversible actions | Governance Layer |

### Human Override

A human with appropriate authority can:

- Set confidence to any value (0.0–1.0) for a specific fact
- The override is recorded in the provenance with the human's identity
- The override is visible in the confidence history
- The override can be superseded by a future override or by new evidence

### Explainability

Every confidence score must be explainable:

```
ConfidenceExplanation:
  value: float                    — The confidence score
  method: string                  — "direct" | "propagation" | "combination" | "decay" | "override"
  inputs: ConfidenceInput[]       — Facts used to compute this score
  formula: string                 — Which formula was applied
  computed_at: datetime           — When the confidence was computed
  expires_at: datetime | null     — When this confidence score should be re-evaluated
```

### No Engine May Invent Its Own Confidence Model

All engines use the canonical confidence model defined in this section. An engine may define additional thresholds or decay rates specific to its domain, but the core scale, propagation, combination, decay, and explanation mechanisms are invariant.

---

## Section 8 — Canonical Event Envelope

### Event Format

Every event published or consumed within SHUNYA MUST use this envelope format:

```json
{
  "event_id": "uuid-v7",
  "correlation_id": "uuid-v7",
  "trace_id": "uuid-v7",
  "timestamp": "2026-07-18T12:00:00Z",
  "tenant_id": 1,
  "workspace_id": null,
  "actor": {
    "id": "uuid",
    "type": "engine | human | system",
    "name": "GovernanceEngine"
  },
  "object": {
    "id": "uuid",
    "type": "GovernanceVerdict",
    "version": 1
  },
  "event_type": "governance.action.approved",
  "event_version": 1,
  "schema_version": "1.0",
  "payload": {},
  "evidence": [],
  "confidence": 1.0,
  "metadata": {},
  "provenance": {}
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | UUID (v7) | Yes | Globally unique event identifier. Never reused. |
| `correlation_id` | UUID (v7) | Yes | Correlates related events across engines. Same for a workflow. |
| `trace_id` | UUID (v7) | Yes | Distributed trace identifier. Same across all spans in a request. |
| `timestamp` | datetime (UTC) | Yes | When the event was produced. |
| `tenant_id` | Integer | Yes | Owning tenant. All events are tenant-scoped. |
| `workspace_id` | Integer | No | Owning workspace. |
| `actor` | Actor | Yes | Who or what produced the event. |
| `object` | Object | Yes | The object the event is about. |
| `event_type` | String | Yes | Namespaced event type (e.g., `knowledge.fact.created`). |
| `event_version` | Integer | Yes | Version of the event schema. Starts at 1. |
| `schema_version` | String | Yes | Version of the envelope schema. Currently "1.0". |
| `payload` | JSON | Yes | Event-specific data. |
| `evidence` | Evidence[] | No | Evidence supporting the event. |
| `confidence` | Float | Yes | Confidence in the event payload. Canonical scale. |
| `metadata` | JSON | No | Arbitrary key-value metadata. |
| `provenance` | Provenance | No | Provenance of the event itself. |

### Actor

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | The actor's unique identifier. |
| `type` | String | Yes | `engine`, `human`, `system`. |
| `name` | String | Yes | Human-readable actor name. |

### Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | The object's unique identifier. |
| `type` | String | Yes | The object type (e.g., `GovernanceVerdict`, `KnowledgeFact`). |
| `version` | Integer | Yes | The object's version at the time of the event. |

### No Engine May Define Its Own Event Format

All engines use the canonical event envelope. An engine may extend the `payload` field with engine-specific data, but the envelope fields are invariant.

---

## Section 9 — Engine Contract

Every engine specification MUST expose the following sections. This is the minimum contract for any engine within SHUNYA.

| Section | Description | Always Required? |
|---------|-------------|-----------------|
| **Purpose** | Mission, why it exists, architectural responsibility | Yes |
| **Inputs** | Input contract, sources, validation | Yes |
| **Outputs** | Output contract, destinations, guarantees | Yes |
| **Reads** | Which engines/layers it reads from | Yes |
| **Writes** | Which engines/layers it writes to | Yes |
| **Events Published** | Canonical event envelope for each event type | Yes |
| **Events Consumed** | Canonical event envelope for each consumed event | Yes |
| **State** | Full state machine with states, transitions, terminal states | Yes |
| **Dependencies** | Internal and external dependencies | Yes |
| **Latency** | p50, p99, and maximum latency budgets | Yes |
| **Failure Modes** | At least 5 failure modes with cause, detection, effect, recovery | Yes |
| **Security** | Tenant isolation, credential access, auditability | Yes |
| **Observability** | Logging, metrics, tracing, alerting | Yes |
| **Constitutional Mapping** | Every responsibility mapped to a constitutional principle | Yes |
| **Interaction Matrix** | Reads, writes, events published, events consumed per layer | Yes |
| **Complexity** | CPU, memory, storage, scaling bottlenecks | Yes |
| **Future Extensions** | Anticipated capabilities | Yes |

### Engine Contract Template

Engine specifications shall use the ENGINE_SPEC_TEMPLATE.md as the structural template, with the sections above as mandatory minimum content. An engine specification may add sections beyond this minimum but may not omit any.

---

## Section 10 — Interaction Principles

### Read Ownership

- An engine may read from any other engine whose output contract is defined.
- An engine must not read from an engine whose output contract is not yet defined.
- Read operations must not modify the source engine's state.
- Read operations must respect tenant isolation boundaries.

### Write Ownership

- An engine owns writes to its own data store. No other engine may write directly to an engine's data store.
- An engine may request a write from another engine via an event or API call. The receiving engine validates and performs the write.
- Write ownership is explicit: the Knowledge Engine owns fact writes. The Governance Engine owns audit log writes. The Observer Engine owns observation writes.
- No engine may write to another engine's store without authorization.

### Publish Rules

- An engine publishes events to the Event Bus when its state changes in a way that other engines may need to know about.
- Events must use the canonical event envelope (Section 8).
- An engine must not publish events that contain data it does not own.
- Events are published at-least-once. Consumers must handle duplicates via idempotency keys.

### Consumption Rules

- An engine consumes events from the Event Bus when it needs to react to state changes in other engines.
- A consumer must not modify the event. Events are immutable records.
- A consumer must handle events idempotently (same event delivered twice produces the same result).
- A consumer that cannot process an event must place it on a dead-letter queue, not silently drop it.

### Circular Dependency Prevention

- The dependency graph between engines must be a directed acyclic graph (DAG).
- No engine may depend (directly or transitively) on an engine that depends on it.
- If a circular dependency is discovered, one of the dependencies must be broken by introducing an intermediate event or by restructuring the layer boundaries.
- The canonical dependency direction is: Observer → Knowledge → Reasoning → Planner → Governance → Executor → Observer (completing the loop through the Learning Layer).

### Layer Isolation

- An engine may not call another engine's internal functions. Interaction is through defined interfaces (API, events, or shared data stores with explicit read/write ownership).
- An engine's internal state is not visible to other engines except through published outputs.
- Layer isolation is enforced at the architectural level, not the code level. The architecture defines the interfaces; the implementation respects them.

### Failure Isolation

- An engine's failure must not cascade to other engines.
- If engine A depends on engine B and B is unavailable, A must degrade gracefully (use cached data, return reduced confidence, or reject the request with a clear error).
- Circuit breakers are required for synchronous dependencies.
- Event-driven dependencies are naturally isolated (events are queued; the consumer can catch up when available).

### Synchronization

- Synchronous interactions (API calls) are used when the caller needs the result before proceeding.
- Asynchronous interactions (events) are used when the caller does not need the result immediately.
- The synchronous/asynchronous boundary is defined in the engine specification's interaction matrix.

### Async Behavior

- Event publishing is non-blocking. The publisher does not wait for consumers to process the event.
- Event consumption is asynchronous. The consumer processes events from its queue.
- Event ordering is not guaranteed across event types. Consumers must handle out-of-order delivery.
- Events of the same type from the same producer are delivered in order (per partition).

---

## Section 11 — Architectural Invariants

These rules are absolute. No engine, specification, or implementation may violate them. Violations are architectural divergence and must be escalated per the Engineering Constitution, Article 8.

| # | Invariant | Rationale | Violation Consequence |
|---|-----------|-----------|----------------------|
| 1 | **Evidence is immutable.** Evidence records are created once and never modified. | Traceability requires that evidence cannot be changed after the fact. | Broken explainability, untraceable decisions. |
| 2 | **Knowledge is versioned.** Every fact mutation creates a new version. No in-place updates. | The compounding intelligence loop requires that past knowledge is preserved. | Lost audit trail, broken temporal queries. |
| 3 | **Governance precedes execution.** No action reaches the Executor without passing through the Governance Engine. | The constitution requires that no single component can independently compromise execution. | Unchecked actions, security vulnerability. |
| 4 | **Reasoning never executes.** The Reasoning Layer produces analysis, evidence, and recommendations. It does not send messages, create records, or call APIs. | Separation of responsibilities prevents the Reasoning Layer from independently acting on its own recommendations. | Reasoning could bypass governance. |
| 5 | **Executor never reasons.** The Executor Layer delivers messages and performs actions. It does not analyze, infer, or decide. | The Executor's role is delivery, not judgment. Judgment belongs to Governance. | Executor could independently decide to execute. |
| 6 | **Observer never governs.** The Observer Layer records reality. It does not evaluate policies or make decisions. | Observation must be unbiased. Governance requires judgment. | Observation could be influenced by policy. |
| 7 | **Learning never mutates evidence.** The Learning Layer reads evidence and writes learned facts. It does not modify or delete evidence records. | Evidence is the foundation of trust. If Learning could modify evidence, it could conceal its own errors. | Self-deception, broken trust. |
| 8 | **Identity is globally unique within a tenant.** No two persons may have the same canonical identity. | Identity resolution is the foundation of relationship, context, and memory. | Duplicate records, split context, broken relationships. |
| 9 | **Tenant isolation is mandatory.** No engine may access data from another tenant without explicit authorization. | Multi-tenant security. | Cross-tenant data leakage. |
| 10 | **Audit trails are append-only.** Governance decisions, knowledge versions, and evidence records are never deleted or modified. | Permanent traceability is a constitutional requirement. | Irrecoverable loss of audit history. |
| 11 | **Confidence is always explicit.** Every fact, decision, and event carries a confidence score. No implicit confidence assumptions. | Every consumer must know how much to trust the data they receive. | Silent over-reliance on unconfident data. |
| 12 | **Provenance is always present.** Every object carries its origin, creator, and modification history. | Traceability requires that every object can answer "where did this come from?" | Untraceable decisions. |
| 13 | **Events use the canonical envelope.** No engine may define its own event format. | Interoperability requires a shared event schema. | Broken event bus, incompatible consumers. |
| 14 | **The dependency graph is acyclic.** No circular dependencies between engines. | Circular dependencies prevent independent deployment, testing, and reasoning about the system. | Fragile system, deployment deadlocks. |

---

## Section 12 — Glossary

| Term | Definition |
|------|------------|
| **Activity** | A recorded action performed by an actor on an object. |
| **Actor** | The entity (engine, human, system) that performs an action or produces an event. |
| **Architectural Invariant** | A rule that no engine, specification, or implementation may violate. |
| **Canonical Model** | A shared definition of a concept that all engines must use. |
| **Claim** | A statement that can be supported or contradicted by evidence. |
| **Confidence** | A value in [0.0, 1.0] expressing the system's certainty in a fact, decision, or event. |
| **Context Fusion** | The process of assembling a bounded workspace context from multiple source providers. |
| **Correlation ID** | An identifier that groups related events across engines for a single workflow. |
| **Engine** | A concrete implementation unit within a layer (e.g., GovernanceEngine, KnowledgeEngine). |
| **Entity** | A real-world object with a persistent identity (Person, Organization, Place, etc.). |
| **Event** | A record of something that happened, formatted in the canonical event envelope. |
| **Event Bus** | The publish/subscribe infrastructure for asynchronous engine communication. |
| **Evidence** | A link between a claim and a source that supports or contradicts it. |
| **Evidence Chain** | The complete set of evidence supporting or contradicting a claim. |
| **Fact** | A verified observation stored in the Knowledge Engine. |
| **Governance** | The process of evaluating proposed actions against policies and constitutional principles. |
| **Identity** | The canonical representation of a person, organization, or channel within a tenant. |
| **Immutable** | Cannot be modified after creation. New versions may supersede, but originals persist. |
| **Knowledge** | Integrated facts that have been cross-referenced and contextualized by the Reasoning Engine. |
| **Layer** | A named architectural boundary with a single responsibility (Knowledge, Reasoning, Governance, etc.). |
| **Observation** | A raw recording of reality before verification. |
| **Provenance** | The complete history of an object: origin, creator, modifications, and evidence. |
| **Relationship** | A typed link between two UniversalObjects. |
| **Tenant** | An isolated data namespace representing a company using SHUNYA. |
| **Trace ID** | An identifier that spans all events and operations in a single request flow. |
| **UniversalObject** | The base type for all objects in the SHUNYA object model. |
| **Verification** | The process of confirming a claim against evidence. |
| **Version** | A monotonically increasing integer tracking the evolution of an object. |
| **Wisdom** | Applied knowledge that has been evaluated and acted upon by the Governance Engine. |
| **Workspace** | A logical grouping of objects within a tenant, typically corresponding to a team or project. |

---

## Section 13 — Cross References

### Referenced Documents

| Document | Reference | How This Document Relates |
|----------|-----------|--------------------------|
| **SHUNYA Constitution** (`SHUNYA_ARCHITECTURE.md`) | Supersedes this document where constitutional principles conflict | This document derives canonical models from constitutional principles; the Constitution is the higher authority |
| **SHUNYA Engineering Constitution** (`/governance/SHUNYA_ENGINEERING_CONSTITUTION.md`) | Article 8 defines divergence — this document's invariants are divergence-checkable | Engineering Constitution Article 8 provides the escalation path for violations of this document's invariants |
| **Governance Baseline v1.0** (`/governance/`) | This document is an Architecture Standard per the governance model | This document is subject to the approval hierarchy defined in the Governance Model |
| **ES-001: Governance Engine** (`/governance/engine_specs/ES-001-GOVERNANCE-ENGINE.md`) | References this document for canonical models | ES-001's confidence model, evidence model, and event envelope inherit from this document |
| **ES-002: Knowledge Engine** (`/governance/engine_specs/ES-002-KNOWLEDGE-ENGINE.md`) | References this document for canonical models | ES-002's knowledge hierarchy, confidence model, and provenance model inherit from this document |
| **ADR Template** (`/governance/adr/ADR_TEMPLATE.md`) | ADRs that reference shared concepts shall cite this document | Prevents each ADR from redefining canonical models |

### How to Use This Document

1. **Engine specification authors:** When writing an engine spec, reference this document for all shared concepts (confidence, evidence, provenance, event envelope, object model). Do not redefine them.
2. **ADR authors:** When filing an ADR that touches shared concepts, reference this document. If the ADR proposes a change to a shared concept, the ADR class is Architectural/Constitutional.
3. **Implementers:** When implementing an engine, use the canonical models defined here. If the implementation needs to deviate, file an ADR first.
4. **Reviewers:** When reviewing an engine spec or implementation, verify that shared concepts are not being redefined. Flag violations as architectural divergence.

### Request for Augmentation

This document defines the initial set of canonical models. As new engines are specified, new shared concepts may be discovered. When a concept appears in three or more engine specifications, it should be promoted to this document as a canonical model. The promotion process is:

1. Identify the concept appearing in multiple engine specs
2. File an ADR proposing the canonical model
3. Update this document with the new model
4. Update all affected engine specs to reference the canonical model

---

**End of SHUNYA Core Models**