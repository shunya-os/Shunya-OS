# E-004 Evidence Engine

**Architecture Specification**

*Constitutional — Pre-Implementation*

---

---

## 0. PREAMBLE

### 0.1 Purpose

The Evidence Engine is the canonical subsystem by which SHUNYA OS records, attributes, validates, and reasons about the origins of every claim the system holds. It is the system of record for **why** the system believes what it believes.

### 0.2 Scope

This document defines the architecture of E-004. It establishes the ontology, invariants, trust model, and API surface. It does not prescribe implementation language, storage engine, wire protocol, or framework.

### 0.3 Status

Architecture only. Pre-implementation. No code has been written.

### 0.4 Relationship to Other Subsystems

| Subsystem | Relationship |
|---|---|
| Kernel (Node/Edge store) | Evidence annotates Nodes and Edges; Kernel never depends on Evidence |
| Graph Traversal | May filter or rank results by evidence confidence |
| Identity / Auth (E-001) | Provides identity tokens for provenance records |
| Inference Engine | Produces evidence objects; is itself a provenanced source |

---

---

## 1. WHAT IS EVIDENCE?

### 1.1 Definition

**Evidence** is an atomic, versioned record that asserts a specific claim about a specific target (Node or Edge) and declares the provenance, confidence, and temporal bounds of that assertion.

### 1.2 Structure (contract)

Every Evidence object SHALL contain:

- **id** — globally unique identifier
- **target_id** — the Node or Edge this evidence addresses
- **target_type** — `node` | `edge`
- **observation** — the specific asserted claim (see §2)
- **source** — the origin of this evidence (see §4)
- **provenance** — the chain of custody (see §3)
- **confidence** — 0.0 to 1.0 (see §5)
- **freshness** — temporal metadata (see §9)
- **version** — monotonic integer (see §16)
- **status** — `active` | `superseded` | `withdrawn` | `expired`
- **supersedes** — optional id of the Evidence this replaces
- **withdrawn_by** — optional id of the withdrawing Evidence

### 1.3 Identity

Evidence identity is content-addressed over its immutable fields: target, observation, source, and timestamp. Two Evidence objects that assert the same thing about the same target from the same source at the same time MUST have the same id.

> **Rule E-004-R1**: Evidence id SHALL be derived from a canonical hash of `(target_id, observation, source_id, version_1_timestamp)`.

### 1.4 Immutability

Once committed, an Evidence object MUST NOT be mutated in place. All state transitions (supersede, withdraw, expire) produce NEW Evidence objects that reference their predecessor.

> **Rule E-004-R2**: Evidence is append-only. No UPDATE, only INSERT + supersede chain.

---

---

## 2. WHAT IS OBSERVATION?

### 2.1 Definition

An **Observation** is the atomic declarative statement that forms the claim of an Evidence object. It is the **what** that is being asserted.

### 2.2 Form

Observations SHALL be expressed as subject-predicate-object triples where the subject is implicit (the target).

Examples:

- `type: "species" value: "Quercus robur"`
- `type: "relationship" value: "predates"`
- `type: "attribute" value: "mass_kg: 340"`
- `type: "temporal" value: "existed_from: 1847"`
- `type: "provenance_fact" value: "generated_by: inference-7e9a"`

### 2.3 Observation Granularity

> **Rule E-004-R3**: One Observation per Evidence object. If a source makes multiple claims, each claim gets its own Evidence object.

This rule is non-negotiable. It prevents ambiguity about which part of a compound assertion is supported, contradicted, or withdrawn.

### 2.4 Observation Types (Open Set)

The Observation type system is extensible. The architecture defines these foundational types:

| Type | Description | Example Value |
|---|---|---|
| `tag` | A categorical label | `"deciduous"` |
| `attribute` | A key-value property | `"height_m: 12.4"` |
| `relationship` | A typed edge claim | `"predates"` |
| `temporal` | A time-bound fact | `"existed_from: 1892"` |
| `provenance_fact` | A fact about evidence itself | `"generated_by: pipeline-alpha"` |
| `negation` | Assertion that something is NOT | `"NOT endangered"` |
| `composite` | A derived claim combining multiple observations | `"habitat_overlap: 0.74"` |

### 2.5 Observation Constraints

- An Observation MUST be self-contained — its meaning MUST NOT depend on other Observations.
- An Observation MUST be falsifiable — there must exist a conceivable state of the world in which it is false.
- An Observation MAY be negative (see `negation` type).

---

---

## 3. WHAT IS PROVENANCE?

### 3.1 Definition

**Provenance** is the chain-of-custody record that answers: *who or what produced this evidence, through what process, at what time, and from what prior evidence?*

### 3.2 Provenance Record Structure

Every Evidence object SHALL carry:

- **actor_id** — the identity that created the evidence (user, sensor, inference pipeline)
- **actor_type** — `human` | `sensor` | `inference_engine` | `system` | `external_service`
- **process** — the specific process/algorithm that produced it (e.g. `"inference-v2.1/resnet50"`, `"manual-entry"`, `"ocr-pipeline-3"`)
- **timestamp** — ISO 8601 when the evidence was created
- **input_evidence_ids[]** — zero or more Evidence ids that were inputs to this evidence (for derived / inferred evidence)
- **signature** — optional cryptographic signature of `(target_id, observation, timestamp, actor_id)`

### 3.3 Provenance Chain Depth

> **Rule E-004-R4**: Every Evidence object MUST have a complete provenance chain. If `input_evidence_ids` is non-empty, each referenced Evidence MUST itself have a complete provenance chain, recursively.

### 3.4 Provenance Root Types

| Root Type | Description | input_evidence_ids |
|---|---|---|
| `human_observation` | A person asserts a claim | empty |
| `sensor_reading` | A physical sensor measures | empty |
| `system_event` | A system log or timestamp | empty |
| `external_import` | Data ingested from outside SHUNYA | empty |
| `derived_inference` | An inference engine produces a claim | non-empty |

### 3.5 Provenance Completeness

> **Rule E-004-R5**: A provenance chain terminates at a root type. An Evidence object whose chain does not terminate at a root type within a configurable maximum depth SHALL be rejected.

---

---

## 4. WHAT IS SOURCE?

### 4.1 Definition

A **Source** is the origin entity that produced the raw evidence. Sources are registered, typed, and optionally authenticated.

### 4.2 Source Types

| Type | Description | Trust Baseline |
|---|---|---|
| `calibrated_sensor` | Hardware sensor at known coordinates | High (per calibration) |
| `authenticated_human` | User with verified identity | Medium (per reputation) |
| `anonymous_human` | Unverified user submission | Low |
| `trusted_inference` | Inference engine passing validation | Medium (per eval) |
| `untrusted_inference` | Third-party AI model | Low |
| `authoritative_database` | Curated external registry | High |
| `web_scrape` | Automated web content fetch | Very Low |
| `system` | SHUNYA OS internal events | Maximum |

### 4.3 Source Registration

Every Source MUST be registered before it can produce Evidence. Registration requires:

- **source_id** — globally unique identifier
- **source_type** — from the table above
- **metadata** — type-specific metadata (e.g. sensor calibration date, human identity token, inference model version)
- **trust_baseline** — initial trust score (see §18)
- **is_active** — boolean; inactive sources cannot produce new evidence

### 4.4 Source Authentication

> **Rule E-004-R6**: Evidence from unregistered sources SHALL be rejected.

> **Rule E-004-R7**: Sources of type `authenticated_human`, `calibrated_sensor`, and `authoritative_database` MUST present verifiable credentials with each evidence submission.

---

---

## 5. WHAT IS CONFIDENCE?

### 5.1 Definition

**Confidence** is a floating-point value in the closed interval [0.0, 1.0] representing the system's assessed likelihood that the Observation is true given the Source, Provenance, and any corroborating or contradicting Evidence.

### 5.2 Semantics

| Value | Meaning |
|---|---|
| 1.0 | Certain — no reasonable doubt |
| 0.9 - 0.99 | Very high confidence |
| 0.7 - 0.89 | High confidence |
| 0.5 - 0.69 | Moderate confidence |
| 0.3 - 0.49 | Low confidence |
| 0.01 - 0.29 | Very low confidence / speculative |
| 0.0 | Known false (negative evidence) |

### 5.3 Confidence Composition

An Evidence object carries two confidence values:

1. **initial_confidence** — the confidence assigned at creation by the source/process
2. **computed_confidence** — the confidence after system-level adjustment (§18)

The system SHALL NOT modify `initial_confidence`. All adjustments MUST be reflected in `computed_confidence` with an audit trail.

### 5.4 Confidence is Per-Edge, Per-Observation

Confidence is NOT a property of a Node. It is a property of the Evidence that attaches to a Node or Edge. Two Evidence objects on the same target may have different confidence values.

### 5.5 Confidence Floor

> **Rule E-004-R8**: There exists a configurable `confidence_floor` below which Evidence SHALL be excluded from query results by default. Excluding by confidence floor MUST be explicitly overridable per query.

---

---

## 6. CAN EVIDENCE CONTRADICT EVIDENCE?

### 6.1 Answer: Yes.

Two Evidence objects that assert contradictory Observations about the same target constitute a **contradiction**.

### 6.2 Contradiction Resolution

> **Rule E-004-R9**: The system MUST detect contradictions automatically and surface them. It MUST NOT silently pick a winner.

Contradiction detection compares:

- Same target_id
- Same observation type
- Mutually exclusive values (e.g. `species: "Quercus robur"` vs `species: "Fagus sylvatica"`)

### 6.3 Contradiction Record

When a contradiction is detected, the system SHALL create a **ContradictionRecord**:

- **evidence_a_id**, **evidence_b_id**
- **contradiction_type** — `direct` (same type, exclusive values) | `indirect` (logical implication violation)
- **resolved** — boolean
- **resolution** — optional reference to Evidence that resolves the contradiction

### 6.4 Contradiction is NOT an Error

Contradictions are first-class citizens. They represent the real-world fact that sources disagree. The system must preserve the disagreement and make it queryable.

---

---

## 7. CAN EVIDENCE EXPIRE?

### 7.1 Answer: Yes.

Evidence can expire based on temporal bounds.

### 7.2 Expiration Mechanisms

| Mechanism | Trigger | Effect |
|---|---|---|
| `valid_until` | Absolute timestamp in the past | `status = expired` |
| `session_bound` | Computation session ended | `status = expired` |
| `source_lifetime` | Source deactivated or recalibrated | All evidence from source re-evaluated |
| `max_age` | Configurable TTL per source type | `status = expired` |

### 7.3 Expiration is Reversible

If a time-bound evidence had `valid_until` set but the temporal extendability is established (e.g. a sensor recalibration confirms prior readings remain valid), a new Evidence object MAY supersede the expiration.

### 7.4 TTL Defaults

| Source Type | Default Max Age |
|---|---|
| `calibrated_sensor` | Configurable (default: sensor calibration period) |
| `authenticated_human` | No default TTL |
| `anonymous_human` | 90 days |
| `trusted_inference` | Session duration |
| `untrusted_inference` | 30 days |
| `web_scrape` | 7 days |

---

---

## 8. CAN EVIDENCE BE SUPERSEDED?

### 8.1 Answer: Yes.

Evidence is superseded when new evidence replaces it. This is the mechanism for correction, refinement, and versioning.

### 8.2 Supersession Rules

> **Rule E-004-R10**: Only `active` evidence can be superseded. `withdrawn` or `expired` evidence SHALL NOT be superseded.

> **Rule E-004-R11**: A superseding Evidence object MUST reference the superseded Evidence in its `supersedes` field.

> **Rule E-004-R12**: The superseded Evidence's `status` SHALL be set to `superseded` with a reference to the superseding Evidence in `superseded_by`.

### 8.3 Supersession Chain

Evidence forms a singly-linked forward chain:

```
E_v1 (active) --superseded_by--> E_v2 (active) --superseded_by--> E_v3 (active)
```

At query time, only the terminal (most recent) `active` evidence for any given `(target_id, observation_type)` pair is returned by default. Historical versions are available via explicit version traversal.

### 8.4 When to Supersede vs. Contradict

| Scenario | Mechanism |
|---|---|
| Correction of an error | Supersede |
| Refinement with higher precision | Supersede |
| Different source disagrees | Create contradicting evidence (no supersede) |
| Source corrects own prior statement | Supersede |
| New sensor reading replaces old | Supersede (if same sensor); contradict (if different sensor) |

---

---

## 9. CAN EVIDENCE BE WITHDRAWN?

### 9.1 Answer: Yes.

Withdrawal is the mechanism by which a source retracts its own prior evidence without replacing it.

### 9.2 Withdrawal Rules

> **Rule E-004-R13**: Only the originating source (or an admin with explicit override authority) MAY withdraw its own evidence.

> **Rule E-004-R14**: Withdrawal produces a new Evidence object with `status = withdrawn` and an observation of type `withdrawal` referencing the withdrawn evidence. The withdrawn evidence SHALL have `status = withdrawn` and `withdrawn_by` set.

### 9.3 Withdrawal vs. Supersession

| | Supersession | Withdrawal |
|---|---|---|
| Replacement | Yes — new evidence replaces old | No — nothing replaces it |
| Reason | Improvement / correction | Retraction / error |
| Observation of withdrawn evidence | Still accessible but not default | Still accessible but not default |
| Query default | Show newest active | Exclude withdrawn |

### 9.4 Irreversible

> **Rule E-004-R15**: Withdrawal is irreversible. A withdrawn Evidence object SHALL NOT be reinstated. To correct a mistaken withdrawal, create new Evidence.

---

---

## 10. CAN ONE FACT HAVE MANY EVIDENCE OBJECTS?

### 10.1 Answer: Yes.

This is the core design. A single claim about a single target may accumulate multiple Evidence objects from multiple sources over time.

### 10.2 Multi-Evidence Semantics

When multiple Evidence objects assert the same Observation about the same target:

1. They are NOT deduplicated.
2. They are all stored.
3. The system tracks them as a **corpus** (see §18.3).
4. Confidence aggregation is a query-time function, not a storage-time function.

### 10.3 Deduplication Boundary

> **Rule E-004-R16**: Two Evidence objects SHALL be considered duplicates only if they share the same `(target_id, observation, source_id, creation_timestamp)`. A duplicate Evidence submission SHALL return the existing Evidence id, not create a new one.

---

---

## 11. CAN ONE EVIDENCE OBJECT SUPPORT MANY FACTS?

### 11.1 Answer: No.

> **Rule E-004-R17**: One Evidence object SHALL support exactly one target (one Node or one Edge) and exactly one Observation.

This is a deliberate constraint. Rationale:

- Eliminates ambiguity about which part of a multi-claim evidence is contradicted or withdrawn
- Simplifies the versioning model
- Makes the supersession chain unambiguous
- Enables precise confidence attribution

---

---

## 12. CAN AI-GENERATED EVIDENCE EXIST?

### 12.1 Answer: Yes.

AI-generated evidence is a first-class citizen, but with strict provenance requirements.

### 12.2 Requirements for AI-Generated Evidence

| Requirement | Detail |
|---|---|
| Source type | MUST be `trusted_inference` or `untrusted_inference` |
| Provenance required | Full chain including model version, input evidence IDs, hyperparameters |
| Confidence required | The inference engine MUST supply a calibrated confidence |
| Auditable | The inference MUST be reproducible (same inputs → same output) |
| Labeled | Evidence SHALL carry `actor_type: inference_engine` and `process: "<model_name>/<version>"` |

### 12.3 AI Confidence Calibration

> **Rule E-004-R18**: Inference engines that produce confidence values MUST demonstrate calibration on a held-out validation set. Uncalibrated confidences SHALL be flagged as `uncalibrated` and the confidence value SHALL be treated as an order-of-magnitude estimate only.

---

---

## 13. HOW IS MACHINE INFERENCE DISTINGUISHED FROM OBSERVATION?

### 13.1 Taxonomy of Evidence Origin

All Evidence SHALL be classified along two orthogonal axes:

**Axis 1: Origin Method**

| Value | Definition |
|---|---|
| `direct_observation` | The claim is a direct recording of sensed state |
| `derived_computation` | The claim is computed from other evidence |
| `human_testimony` | The claim is asserted by a person |
| `external_assertion` | The claim is imported from an external system |
| `synthetic` | The claim is generated by a process for testing or simulation |

**Axis 2: Certainty Class**

| Value | Definition |
|---|---|
| `certain` | The origin guarantees the claim (e.g., identity assertion from auth system) |
| `measured` | The origin provides a measurement with known precision |
| `estimated` | The origin provides an estimate with stated uncertainty bounds |
| `inferred` | The origin computed the claim from incomplete inputs |
| `speculative` | The origin generated a hypothesis with no direct evidence |

### 13.2 Distinction in Practice

- **Observation**: A sensor reading of `temperature: 23.4°C` is a `direct_observation/measured`.
- **Machine Inference**: An inference model predicting `species: Quercus robur` from leaf images is `derived_computation/inferred`.
- **Human Assertion**: A person stating `common_name: English Oak` is `human_testimony/estimated` (unless they are a recognized expert, in which case `human_testimony/measured`).

### 13.3 Query Filtering

All queries against the Evidence store SHALL support filtering by Origin Method and Certainty Class.

---

---

## 14. HOW DOES EVIDENCE ATTACH TO NODES?

### 14.1 Attachment Model

Evidence attaches to Nodes via the `target_id` field. A Node MAY have zero or more Evidence objects attached.

### 14.2 Node-Evidence Contract

- Evidence does NOT live inside Nodes. Nodes and Evidence are separate stores.
- Evidence references Nodes by their `node_id`. This is a unidirectional reference.
- Nodes SHALL NOT know about their attached Evidence.
- The Evidence store SHALL maintain an index by `target_id` for efficient lookup.

### 14.3 What Evidence Can Assert About a Node

Evidence can assert:

- A Node has a property: `observation: { type: "attribute", value: "color: #336699" }`
- A Node has a type: `observation: { type: "tag", value: "deciduous_tree" }`
- A Node exists: `observation: { type: "existence", value: "true" }` (default for any created Node)
- A Node does NOT have a property: `observation: { type: "negation", value: "NOT color: #FF0000" }`

### 14.4 Node Property Resolution

> **Rule E-004-R19**: A Node's resolved property value at any point in time is a function of all `active` Evidence objects attached to that Node, filtered by the query's confidence floor and freshness requirements.

The Node store SHALL NOT cache resolved properties. Resolution is always a query-time cross-store operation.

---

---

## 15. HOW DOES EVIDENCE ATTACH TO EDGES?

### 15.1 Attachment Model

Evidence attaches to Edges identically to Nodes — via `target_id` referencing the Edge's `edge_id`.

### 15.2 What Evidence Can Assert About an Edge

Evidence can assert:

- The edge exists (default for any created Edge)
- The edge type is `X`: `observation: { type: "relationship", value: "predates" }`
- The edge has weight/distance: `observation: { type: "attribute", value: "weight: 0.74" }`
- The edge is valid only within a time range: `observation: { type: "temporal", value: "valid_from: 1800, valid_until: 1900" }`
- The edge does NOT exist: `observation: { type: "negation", value: "NOT exists" }`

### 15.3 Edge Validity

An Edge's existence is itself a claim backed by Evidence. An Edge MAY exist in the Graph store but have zero active Evidence supporting it — this is the default for directly-created edges (the system self-attests existence with maximum confidence).

> **Rule E-004-R20**: When an Edge has Evidence contradicting its existence AND zero Evidence supporting it, the Edge SHALL be flagged as `contested` in the Graph store.

---

---

## 16. HOW IS EVIDENCE VERSIONED?

### 16.1 Versioning Model

Evidence uses a **monotonic version counter** scoped to a version chain. A version chain is defined by `(target_id, observation_type)`.

### 16.2 Version Chain Rules

- The first Evidence object for a given `(target_id, observation_type)` has `version = 1`.
- Each superseding Evidence increments the version.
- Withdrawals do NOT increment the version number of the withdrawn evidence; they append a new Evidence object with `status = withdrawn`.
- Version gaps SHALL NOT exist.

### 16.3 Version Chain State

At any point, a version chain has exactly one terminal state:

| Terminal State | Meaning |
|---|---|
| `active` | The chain has an active terminal evidence |
| `withdrawn` | The terminal evidence was withdrawn, nothing replaces it |
| `expired` | The terminal evidence expired |
| `empty` | No evidence has ever existed for this key |

### 16.4 Snapshot Queries

The system SHALL support:

- `get_evidence(id)` — retrieve by id
- `get_evidence_chain(target_id, observation_type)` — return ordered version chain
- `get_active_evidence(target_id)` — return the terminal active evidence for each observation_type
- `get_evidence_at(target_id, timestamp)` — return evidence as it stood at a given point in time

---

---

## 17. HOW IS TRUST CALCULATED?

### 17.1 Trust Model Overview

Trust is not a single number. It is a multi-dimensional score computed per source and per evidence corpus.

### 17.2 Source Trust

Each Source has a **Source Trust Score (STS)** in [0.0, 1.0].

**Components:**

| Component | Weight | Description |
|---|---|---|
| Baseline | Fixed | Set at source registration based on source_type |
| Historical accuracy | Variable | Ratio of non-contradicted evidence to total evidence from this source |
| Longevity | Variable | Duration the source has been active contributing evidence |
| Calibration status | Binary | Sensor calibrated / model validated (pass/fail) |
| Peer endorsement | Variable | Number of independent sources that corroborate this source's evidence |
| Recency | Variable | More recent evidence weighted higher |

### 17.3 Evidence Trust

Each Evidence object has a **Computed Confidence** derived from:

```
computed_confidence = initial_confidence × source_trust_factor
                      × corroboration_factor × freshness_factor
```

Where:

| Factor | Range | Detail |
|---|---|---|
| `source_trust_factor` | [0.5, 1.0] | `1.0 - (1.0 - STS) × 0.5` — dampened impact of source trust on individual evidence |
| `corroboration_factor` | [1.0, 1.25] | Independent corroborating sources boost confidence (capped) |
| `freshness_factor` | [0.5, 1.0] | Decay based on age vs. expected TTL (see §18) |

### 17.4 Trust is NOT Global

> **Rule E-004-R21**: Trust calculations are scoped. There is no global trust score. A source may have different trust in different domains (e.g., a botanist on species identification vs. on geolocation).

### 17.5 Trust Transparency

> **Rule E-004-R22**: All trust calculations SHALL be explainable. The system MUST be able to answer "why does this evidence have computed_confidence = 0.73?"

---

---

## 18. HOW IS FRESHNESS REPRESENTED?

### 18.1 Freshness Metadata

Every Evidence object SHALL carry:

- **created_at** — ISO 8601 timestamp of creation
- **observed_at** — ISO 8601 timestamp when the observation was actually made (may differ from created_at for historical claims)
- **valid_until** — optional ISO 8601 timestamp after which the evidence MAY be considered stale
- **ttl** — optional duration; if set, evidence expires `ttl` after `observed_at`

### 18.2 Freshness Decay

> **Rule E-004-R23**: Evidence SHALL support configurable decay functions that map age to a freshness multiplier in [0.0, 1.0].

Example decay functions:

- **step**: full confidence until TTL, then 0
- **linear**: linear decay from 1.0 at `observed_at` to 0.5 at TTL, to 0.0 at 2× TTL
- **exponential**: `e^(-λ × age)` where λ is type-specific
- **none**: no time-based decay (for permanent facts)

### 18.3 Corpus Freshness

A **corpus** (the set of all evidence for a given `(target_id, observation_type)`) has a collective freshness derived from:

- The most recent evidence timestamp
- The proportion of evidence in the corpus that is `active` vs. `expired`
- The rate of evidence accumulation

### 18.4 Freshness-Aware Queries

All queries SHALL support:

- `freshness_min: 0.8` — only return evidence with freshness ≥ 0.8
- `freshness_order: "newest"` — order results by recency
- `decay_function: "exponential"` — use specified decay for filtering

---

---

## 19. REQUIRED APIS

### 19.1 Evidence CRUD

```
create_evidence(target_id, target_type, observation, source_id,
                initial_confidence, provenance, valid_until?, ttl?)
  → Evidence { id, version, status, ... }

get_evidence(evidence_id) → Evidence
get_evidence_by_target(target_id, filters?) → Evidence[]

supersede_evidence(evidence_id, observation, source_id,
                   initial_confidence, provenance, ...)
  → Evidence { id, version, status: active, supersedes: evidence_id }

withdraw_evidence(evidence_id, source_id, reason)
  → Evidence { id, status: withdrawn, withdrawn_by: evidence_id }
```

### 19.2 Source Management

```
register_source(source_type, metadata, trust_baseline)
  → Source

update_source_trust(source_id, trust_adjustment)
  → Source

deactivate_source(source_id)
  → status

get_source(source_id) → Source
list_sources(filters?) → Source[]
```

### 19.3 Query

```
query_evidence(target_id, filter:
  - confidence_min: float
  - freshness_min: float
  - status: active | any
  - origin_method: direct_observation | ...
  - certainty_class: certain | ...
  - source_types: [calibrated_sensor, ...]
  - limit: int
  - offset: int
) → Evidence[]

resolve_target(target_id, filter:
  - as_of_timestamp: ISO 8601
  - confidence_floor: float
  - freshness_required: bool
) → ResolvedTarget { properties: { key: { value, evidence_id, confidence } } }
```

### 19.4 Contradiction

```
detect_contradictions(target_id?)
  → ContradictionRecord[]

resolve_contradiction(evidence_a_id, evidence_b_id,
                      resolution_type, resolution_evidence_id)
  → ContradictionRecord
```

### 19.5 Version Chain

```
get_version_chain(target_id, observation_type)
  → Evidence[] (ordered by version)

get_snapshot(target_id, as_of_timestamp)
  → Evidence[] (active as of that time)

get_evidence_history(evidence_id)
  → Evidence[] (supersession chain from this id to root)
```

### 19.6 Trust

```
explain_confidence(evidence_id)
  → TrustExplanation {
      initial_confidence: float
      source_trust: { score: float, components: {...} }
      corroboration_factor: float
      freshness_factor: float
      computed_confidence: float
    }

get_source_trust(source_id, domain?)
  → SourceTrust { score: float, components: {...} }

recalculate_trust(source_id)
  → SourceTrust (updated)
```

---

---

## 20. REQUIRED INVARIANTS

### 20.1 Structural Invariants

| ID | Invariant | Violation Handling |
|---|---|---|
| I-001 | Every Evidence object MUST have a unique id | Reject creation |
| I-002 | Every Evidence object MUST reference an existing target_id | Reject creation |
| I-003 | Every Evidence object MUST reference a registered source_id | Reject creation |
| I-004 | `confidence` MUST be in [0.0, 1.0] inclusive | Clamp on creation |
| I-005 | `version` MUST be > 0 and monotonically increasing per chain | Reject creation |
| I-006 | A superseding Evidence MUST reference an existing, active Evidence | Reject supersede |
| I-007 | A withdrawing Evidence MUST reference an existing Evidence | Reject withdrawal |
| I-008 | Only the originating source MAY withdraw its own Evidence | Reject withdrawal |
| I-009 | Withdrawn or expired Evidence MUST NOT be superseded | Reject supersede |
| I-010 | One Evidence object SHALL reference exactly one target | Structural constraint |
| I-011 | One Evidence object SHALL contain exactly one Observation | Structural constraint |

### 20.2 Chain Invariants

| ID | Invariant | Violation Handling |
|---|---|---|
| I-020 | A version chain MUST NOT have branching (one predecessor → one successor) | Reject cyclic or branching supersede |
| I-021 | A version chain MUST NOT have cycles | Reject supersede that would create cycle |
| I-022 | An Evidence object MUST NOT be in more than one version chain | Structural constraint |
| I-023 | A version chain terminator MUST have status `active`, `withdrawn`, or `expired` | Repair on detection |

### 20.3 Temporal Invariants

| ID | Invariant | Violation Handling |
|---|---|---|
| I-030 | `created_at` MUST be ≤ current system time | Reject future timestamps beyond clock skew tolerance |
| I-031 | `valid_until` MUST be > `observed_at` (if both present) | Reject creation |
| I-032 | In a supersede chain, `version[i].created_at` ≤ `version[i+1].created_at` | Reject supersede |

### 20.4 Trust Invariants

| ID | Invariant | Violation Handling |
|---|---|---|
| I-040 | Source Trust Score MUST be in [0.0, 1.0] | Clamp on update |
| I-041 | Computed confidence MUST be ≤ initial_confidence | Structural guarantee |
| I-042 | Trust recalculation MUST NOT change historical Evidence.initial_confidence | Structural guarantee |
| I-043 | `explain_confidence()` MUST always succeed for any committed Evidence | Availability guarantee |

### 20.5 Store Invariants

| ID | Invariant | Violation Handling |
|---|---|---|
| I-050 | Evidence store SHALL NOT have UPDATE operations, only INSERT | Architectural guarantee |
| I-051 | Evidence deletion SHALL NOT be supported. Period. | Architectural guarantee |
| I-052 | Source deactivation SHALL NOT cascade-delete or cascade-expire Evidence | Source deactivation must be explicit per-evidence |

---

---

## 21. REQUIRED TESTS

### 21.1 Structural Tests

| Test ID | Description |
|---|---|
| T-001 | Creating Evidence with valid fields succeeds and returns correct id |
| T-002 | Creating Evidence with unknown target_id is rejected |
| T-003 | Creating Evidence with unregistered source_id is rejected |
| T-004 | Creating Evidence with confidence > 1.0 is clamped |
| T-005 | Creating Evidence with confidence < 0.0 is clamped |
| T-006 | Evidence with identical (target, observation, source, timestamp) returns existing id |
| T-007 | One Evidence per target per observation guarantee (structural test) |

### 21.2 Version Chain Tests

| Test ID | Description |
|---|---|
| T-010 | First evidence for a key gets version = 1 |
| T-011 | Superseding increments version by 1 |
| T-012 | Superseded evidence has status `superseded` |
| T-013 | Superseding withdrawn evidence is rejected |
| T-014 | Superseding expired evidence is rejected |
| T-015 | `get_version_chain` returns ordered list |
| T-016 | `get_snapshot` returns correct state for any past timestamp |
| T-017 | Withdrawing creates new evidence with `status: withdrawn`, no version increment of target |
| T-018 | Withdrawing someone else's evidence is rejected |
| T-019 | Withdrawal is irreversible — reinstating rejected |

### 21.3 Contradiction Tests

| Test ID | Description |
|---|---|
| T-020 | Direct contradiction is detected on creation |
| T-021 | Indirect contradiction (logical implication) is detected |
| T-022 | Non-contradictory evidence on same target does not trigger contradiction |
| T-023 | Contradiction record is queryable |
| T-024 | Resolved contradiction is marked as resolved |
| T-025 | Contradiction across different observation types is NOT flagged |

### 21.4 Confidence & Trust Tests

| Test ID | Description |
|---|---|
| T-030 | initial_confidence preserved unchanged after storage |
| T-031 | computed_confidence derived correctly from all factors |
| T-032 | Source trust affects computed confidence as expected |
| T-033 | Corroboration factor boosts confidence within cap |
| T-034 | Freshness decay applied correctly |
| T-035 | `explain_confidence()` returns full breakdown |
| T-036 | Confidence floor filter excludes low-confidence evidence |
| T-037 | Confidence floor can be overridden per query |

### 21.5 Freshness Tests

| Test ID | Description |
|---|---|
| T-040 | Evidence with `valid_until` in past has status `expired` |
| T-041 | Freshness > 0 query returns correct subset |
| T-042 | Decay functions produce expected values |
| T-043 | No TTL = no decay (permanent) |
| T-044 | Expiration is reversible via supersession |
| T-045 | TTL default applied per source type |

### 21.6 Query Tests

| Test ID | Description |
|---|---|
| T-050 | Query by target returns all evidence |
| T-051 | Query by target + filter returns correct subset |
| T-052 | `get_active_evidence` returns only terminal active for each observation type |
| T-053 | `resolve_target` produces correct property map |
| T-054 | Query with `as_of_timestamp` returns historical state |
| T-055 | Pagination works correctly |
| T-056 | Query with origin_method filter excludes non-matching |

### 21.7 Integration Tests

| Test ID | Description |
|---|---|
| T-060 | Evidence created → visible in query → superseded → old excluded, new shown |
| T-061 | Chain: create → supersede → supersede → withdraw → chain terminates at withdrawn |
| T-062 | Source deactivated → new evidence from that source rejected → existing evidence unaffected |
| T-063 | Multi-source same observation → all queryable, no deduplication |
| T-064 | Contradiction → resolution → contradiction marked resolved |
| T-065 | Node creation creates default existence evidence |
| T-066 | Edge creation creates default existence evidence |
| T-067 | Edge existence contradicted → edge flagged contested |

### 21.8 Negative Tests

| Test ID | Description |
|---|---|
| T-080 | Cannot UPDATE evidence in place |
| T-081 | Cannot DELETE evidence |
| T-082 | Cannot supersede non-existent evidence |
| T-083 | Cannot create cycle in version chain |
| T-084 | Cannot create branch in version chain |
| T-085 | Cannot create evidence with future timestamp beyond skew tolerance |
| T-086 | Evidence with empty origin_method is rejected |
| T-087 | Evidence with non-terminating provenance chain is rejected |

---

---

## 22. NON-GOALS

### 22.1 Explicitly Out of Scope

| Non-Goal | Rationale |
|---|---|
| **Full-text search of evidence content** | Evidence observations are structured, not free-text. Use tag/attribute query. |
| **Machine learning model serving** | E-004 stores inference results. Model serving is a separate subsystem. |
| **Distributed consensus / replication** | E-004 is a single-system evidence store. Cluster replication is infrastructure. |
| **Natural language explanation generation** | Trust explanations are structured. Human-readable NL is a presentation layer concern. |
| **Blockchain / immutable ledger** | Append-only with content-addressed ids provides immutability without blockchain overhead. |
| **Real-time streaming ingestion** | E-004 accepts evidence synchronously. Streaming is a transport concern, not architectural. |
| **Multi-tenancy / evidence isolation** | Evidence scoping is per-target, not per-tenant. Multi-tenancy is an infrastructure layer. |
| **Evidence visualization** | Graph visualization of evidence chains is a UI concern, not in scope for the engine. |
| **Rule-based automated resolution** | Contradiction detection is in scope. Automated resolution policy is a future concern. |
| **Caching layer** | Query-time resolution from evidence store is architecturally required. Caching is an optimization. |
| **Backup / restore** | Data durability is infrastructure, not architecture. |
| **Evidence migration between systems** | E-004 governs evidence within SHUNYA OS. Inter-system migration is a future concern. |
| **Confidence as probability** | Confidence is a heuristic score in [0,1]. Not a calibrated probability. |

### 22.2 Deliberate Constraints

| Constraint | Why |
|---|---|
| No batch evidence creation API in v1 | Enforces atomicity per evidence and simplifies version chains |
| No evidence merging | Merging two version chains creates ambiguity. Create fresh evidence instead. |
| No soft delete | Withdrawal IS the delete mechanism. No hidden states. |
| No cascading status changes | Expiring a source does not auto-expire its evidence. Each evidence manages its own lifecycle. |
| No evidence templates | Every evidence object is a first-class independent record. Templates would imply mutable schema. |

---

---

## A. APPENDIX: GLOSSARY

| Term | Definition |
|---|---|
| **Evidence** | An atomic, versioned record asserting a claim about a target |
| **Observation** | The specific claim within an Evidence object |
| **Provenance** | Chain of custody: who, what process, from what inputs |
| **Source** | Registered origin entity that produces evidence |
| **Confidence** | Heuristic score [0,1] of truth-likelihood |
| **Freshness** | Temporal relevance derived from timestamps and TTL |
| **Version Chain** | Ordered sequence of superseding evidence for a (target, observation_type) |
| **Corpus** | All evidence for a given (target, observation_type) |
| **Contradiction** | Two or more evidence objects asserting mutually exclusive observations |
| **Supersession** | Replacement of old evidence with new evidence |
| **Withdrawal** | Retraction of evidence without replacement |

---

## B. APPENDIX: EVIDENCE LIFECYCLE STATE MACHINE

```
                         ┌──────────────┐
                         │   CREATED    │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                  ┌──────│    ACTIVE    │──────┐
                  │      └──────────────┘      │
                  │                            │
           supersede                    valid_until
                  │                      exceeded
                  │                            │
          ┌───────▼────────┐          ┌────────▼───────┐
          │   SUPERSEDED   │          │    EXPIRED     │
          └────────────────┘          └────────────────┘

                    ┌──────────────┐
                    │  CREATED     │──withdraw──┐
                    └──────────────┘            │
                                         ┌─────▼──────┐
                                         │  WITHDRAWN │
                                         └────────────┘
```

Evidence enters as `active`. Three exit transitions:
1. **Superseded** — replaced by newer evidence
2. **Expired** — TTL or valid_until exceeded
3. **Withdrawn** — retracted by source (terminal, no replacement)

---

## C. APPENDIX: TRUST CALCULATION DETAIL

### C.1 Source Trust Score Formula

```
STS = 0.40 × baseline +
      0.30 × historical_accuracy +
      0.15 × longevity_factor +
      0.10 × calibration_status +
      0.05 × peer_endorsement
```

### C.2 Components

- **baseline**: Fixed per source_type (calibrated_sensor = 0.95, anonymous_human = 0.30, etc.)
- **historical_accuracy**: `1.0 - (contradicted_count / total_count)` over a sliding window of the last N evidence objects from this source
- **longevity_factor**: `min(1.0, age_in_days / 365)` — reaches 1.0 after one year
- **calibration_status**: `1.0` if source is confirmed calibrated/validated, `0.5` if pending, `0.0` if failed
- **peer_endorsement**: `min(1.0, corroborating_sources / 5 × 0.25)` — each corroborating independent source adds up to 0.25 to the factor

### C.3 Computed Confidence

```
computed_confidence = initial_confidence ×
                      (1.0 - (1.0 - STS) × 0.5) ×
                      (1.0 + min(0.25, corroboration_bonus)) ×
                      freshness_factor
```

Where:
- `corroboration_bonus = n_independent_corroborating_sources × 0.05` (capped at 0.25)
- `freshness_factor = decay_function(age, ttl, observed_at, now)`

---

## D. APPENDIX: CONTRADICTION DETECTION MATRIX

```
                          A says X     A says ~X     A says Y
                          (same type)  (same type)  (diff type)
B says X (same type):       SAME        CONTRADICT     NO
B says ~X (same type):    CONTRADICT      SAME         NO
B says Y (diff type):       NO             NO         INDEPENDENT
```

- **SAME**: Not a contradiction. Either deduplicate (exact match) or accumulate (version chain).
- **CONTRADICT**: Mutually exclusive. Create ContradictionRecord.
- **INDEPENDENT**: Different observation types on same target. Not contradicted.
- **NO**: Not a contradiction.

---

*End of E-004 Evidence Engine Architecture Specification.*
