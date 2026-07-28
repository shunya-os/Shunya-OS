# Universal Knowledge Graph Architecture

**Phase 9 — SHUNYA OS**
**Classification: Implementation Architecture**
**Status: PROPOSED**
**Version: 1.0**

---

## Preamble

### Authority

This document defines the implementation architecture for the Universal Knowledge Graph. It realizes the constitutional definitions established in Phase 8A–8D. It does NOT redefine constitutional concepts — it references them.

### Constitutional sources

| Document | What it provides | How this architecture references it |
|----------|-----------------|--------------------------------------|
| UNIVERSAL_ONTOLOGY.md | What every concept IS | Defines the node and edge types |
| COGNITIVE_WORKSPACE_RUNTIME.md | How cognition flows | Defines the attention, intent, and projection contracts |
| ADAPTIVE_INTELLIGENCE_RUNTIME.md | How SHUNYA evolves | Defines the learning, confidence, and calibration feedback loops |
| FOUNDER_WORKSPACE_SPECIFICATION.md | What the workspace renders | Defines the projection consumption contract |

### First principles

1. **Reality is represented as a graph.** Not a collection of tables. Not disconnected modules. Not application silos.
2. **Everything SHUNYA understands exists as one connected graph.**
3. **The graph is the executable representation of the ontology.** The ontology defines what things ARE; the graph defines how they connect.
4. **No technology lock-in.** This architecture is implementable in any graph-capable storage system.

### Dependency chain

```
Ontology (what things ARE)
  ↓
Knowledge Graph (how things connect)
  ↓
Graph Projections (what the workspace sees)
  ↓
Workspace Runtime (how cognition flows)
```

---

## 1. Graph Architecture

### 1.1 Graph primitives

The Universal Knowledge Graph consists of exactly two primitives:

| Primitive | Ontology reference | Description |
|-----------|-------------------|-------------|
| **Node** | §1 (Object) | A single Object in the Universal Type System |
| **Edge** | §5 (Relationship) | A connection between two Nodes |

### 1.2 Node structure

Every Node carries:

```
Node {
  identity:    NodeID          (permanent, unique, never reused)  [§3]
  type:        NodeType        (from Universal Type System)       [§18]
  labels:      Label[]         (zero or more classification tags)
  attributes:  Attribute[]     (key-value pairs per type schema)  [§4]
  metadata:    Metadata        (created, updated, provenance)     [§1.2]
  evidence:    EvidenceRef[]   (evidence chain references)         [§7]
  confidence:  float           (0.0 – 1.0)                       [§14.3]
  version:     int             (monotonic, per-node)
}
```

### 1.3 Edge structure

Every Edge carries:

```
Edge {
  source:      NodeID          (must exist in graph)
  target:      NodeID          (must exist in graph)
  type:        EdgeType        (from canonical edge families)
  direction:   Direction       (DIRECTED, BIDIRECTIONAL)
  confidence:  float           (0.0 – 1.0)
  evidence:    EvidenceRef[]   (evidence chain references)
  validity:    TimeRange       (optional: when this edge is/was valid)
  weight:      float           (0.0 – 1.0, for traversal scoring)
  provenance:  Provenance      (created by, when, why)
  metadata:    Metadata
}
```

### 1.4 Identity

- Node identity follows the constitutional identity rules (§3): permanent, unique, never reused.
- Edge identity is a triple: `(source_id, target_id, edge_type)`. No two edges may share the same triple.
- Identity is NOT a database key. It is a semantic concept. Implementations may use any internal addressing scheme as long as the identity contract is honoured.

### 1.5 Labels

Labels are zero or more classification tags attached to a Node. They are:

- **Optional** — a Node may have zero labels.
- **Multi-valued** — a Node may have multiple labels.
- **Mutable** — labels can be added or removed over time.
- **Non-identifying** — labels are not part of identity.

Canonical labels include: `active`, `archived`, `verified`, `pending`, `resolved`, `confidential`, `temporary`, `system`.

### 1.6 Types

Type follows the Universal Type System hierarchy (§18). Every Node has exactly one type. Type is immutable.

### 1.7 Metadata

Every Node and Edge carries:

```
Metadata {
  created_at:   Timestamp
  updated_at:   Timestamp
  created_by:   ActorID
  provenance:   Provenance  (how, why, which constitutional process)
}
```

### 1.8 Weights

Edges carry a weight value (0.0 – 1.0) used for:

- Traversal scoring (higher weight → more likely traversal path)
- Attention scoring (higher weight → more relevant to current context)
- Relationship strength (higher weight → stronger connection)

Weight is NOT confidence. Weight is a structural property. Confidence is an evidential property.

### 1.9 Confidence

Every Node and Edge carries a confidence score (0.0 – 1.0). Confidence follows the constitutional Confidence Engine rules (§2 of ADAPTIVE_INTELLIGENCE_RUNTIME.md):

- Initial confidence is assigned at creation.
- Confidence decays over time.
- Confidence can be promoted with repeated evidence.
- Confidence is always explainable via the evidence chain.

### 1.10 Versioning

Every Node has a version number that increments on each modification. Versioning enables:

- Optimistic concurrency control
- Historical reconstruction
- Conflict detection
- Audit trail

Edges are not versioned individually. Edge changes are recorded as events on the Event Bus.

---

## 2. Node Categories

### 2.1 Canonical node families

The following node families derive from the Universal Type System (§18). Each family corresponds to a top-level type in the ontology.

| Family | Ontology type | Example subtypes | Persistence |
|--------|---------------|------------------|-------------|
| **Person** | Entity::Person | Contact, TeamMember, ExternalPerson | Permanent |
| **Organization** | Entity::Organization | Company, Team, Department | Permanent |
| **Document** | Entity::Document | Note, Proposal, Contract, Report | Permanent |
| **Conversation** | Conversation | Thread, Message, Transcript | Permanent |
| **Meeting** | Entity::Meeting | Internal, External, Recurring | Permanent |
| **Task** | Action::Task | ToDo, Subtask, RecurringTask | Permanent |
| **Commitment** | Commitment | Promise, Obligation, Agreement, Deadline | Permanent |
| **Workflow** | Action::Workflow | Process, Pipeline, Stage | Permanent |
| **Knowledge** | Knowledge | Fact, Inference, Rule, Pattern | Permanent |
| **Policy** | Policy | Constitutional, Runtime, Business, Personal | Permanent |
| **Prediction** | Prediction | Forecast, Risk, Opportunity, Trend | Temporal |
| **Evidence** | Evidence | Observation, Verification, Source | Permanent |
| **Observation** | Evidence::Observation | Raw data point | Ephemeral |
| **Event** | Event | Creation, Modification, Decision, Execution | Permanent |
| **Decision** | Event::Decision | Approval, Rejection, Deferral | Permanent |
| **Outcome** | Event::Execution | Success, Failure, Partial | Permanent |
| **Execution** | Action::Execution | Operation, Automation, Command | Permanent |
| **Memory** | Memory | Working, Session, Relationship, Historical | Layered |

### 2.2 Node creation rules

1. Every Node is created from at least one piece of Evidence.
2. Every Node has a type from the Universal Type System.
3. Every Node is assigned a permanent identity at creation.
4. Every Node is connected to at least one other Node within 24 hours of creation (or flagged as isolated).

### 2.3 Node lifecycle

Every Node follows the Universal Object Lifecycle (§6 of COGNITIVE_WORKSPACE_RUNTIME.md):

```
CREATE → OBSERVE → ENRICH → RELATE → PREDICT → EXECUTE → ARCHIVE → RESTORE
```

Alternative: `ARCHIVE → DELETE` (terminal).

---

## 3. Relationship Architecture

### 3.1 Canonical edge families

The following edge families derive from the constitutional Relationship types (§5 of UNIVERSAL_ONTOLOGY.md).

| Family | Direction | Examples | Evidence required? |
|--------|-----------|----------|-------------------|
| **ownership** | Directed | owns, created_by, assigned_to | Yes |
| **membership** | Directed | belongs_to, member_of, works_at | Yes |
| **dependency** | Directed | depends_on, requires, blocks | Yes |
| **reference** | Directed | mentions, references, cites | Yes |
| **evidential** | Directed | supports, contradicts, proves | Yes |
| **causal** | Directed | causes, results_in, leads_to | Yes |
| **temporal** | Directed | precedes, follows, overlaps | Yes |
| **derivation** | Directed | derived_from, inferred_from, predicted_by | Yes |
| **hierarchical** | Directed | contains, parent_of, supersedes | Yes |
| **inheritance** | Directed | inherits_from, extends, specializes | Constitutional |
| **social** | Bidirectional | knows, collaborates_with, relates_to | Yes |
| **contextual** | Directed | observed_in, occurred_during, relevant_to | Yes |
| **predicted** | Directed | predicted_by, forecast_for | Yes (prediction evidence) |
| **historical** | Directed | superseded_by, archived_from, version_of | Yes |
| **attribution** | Directed | attributed_to, source_of, originated_from | Yes |

### 3.2 Edge creation rules

1. Every Edge must have a valid source and target Node (both must exist in the graph).
2. Every Edge must have at least one piece of Evidence (except constitutional edges — e.g., inheritance).
3. No two Edges may share the same `(source, target, type)` triple.
4. Bidirectional edges are stored as a single Edge with `direction = BIDIRECTIONAL`.
5. Self-referencing Edges (source = target) are valid for certain types (e.g., `supersedes`, `version_of`).

### 3.3 Edge lifecycle

```
PROPOSED (predicted, evidence pending)
  ↓
ACTIVE (confirmed, evidence present)
  ↓
STALE (no recent interaction, weight decaying)
  ↓
ARCHIVED (historical, no longer active)
  ↓
REMOVED (determined incorrect, flagged)
```

### 3.4 Edge validation

Every Edge is validated on creation:

1. Source Node exists → FAIL if not
2. Target Node exists → FAIL if not
3. No duplicate triple → FAIL if exists
4. Evidence references exist → WARN if not (edges without evidence are flagged)
5. Edge type is valid for source and target types → WARN if not (edges between incompatible types are flagged)

---

## 4. Evidence Graph

### 4.1 Purpose

Everything must be explainable. Every prediction, every recommendation, every decision, every relationship, every confidence score must trace back to evidence. The Evidence Graph makes this possible.

### 4.2 Evidence lineage

```
┌──────────────────────────────────────────────────────────────────────────┐
│  EVIDENCE LINEAGE                                                         │
│                                                                           │
│  Observation (raw data)                                                   │
│    │                                                                      │
│    ├──→ Evidence (verified observation)                                    │
│    │      │                                                               │
│    │      ├──→ Node (Object created from evidence)                        │
│    │      ├──→ Edge (Relationship created from evidence)                  │
│    │      ├──→ Knowledge (fact derived from evidence)                     │
│    │      ├──→ Prediction (forecast based on evidence)                    │
│    │      └──→ Confidence (confidence score justified by evidence)        │
│    │                                                                      │
│    └──→ Alternative Evidence (conflicting observation)                    │
│           │                                                               │
│           └──→ Contradiction (both held until resolved)                   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Evidence chain

Every Node, Edge, Knowledge, Prediction, and Confidence score carries an `evidence_refs` list. Each reference is:

```
EvidenceRef {
  evidence_id:    NodeID     (the Evidence Node)
  contribution:   float      (0.0 – 1.0, how much this evidence contributes)
  timestamp:      Timestamp  (when the evidence was incorporated)
  type:           EvidenceType  (PRIMARY, SECONDARY, EXTERNAL, etc.)
}
```

### 4.4 Evidence traversal

From any Node or Edge, the graph supports:

- **Upward traversal**: Given a Node, find all Evidence that created it.
- **Downward traversal**: Given an Evidence Node, find all Nodes and Edges that reference it.
- **Confidence trace**: Given a Confidence score, find all Evidence that contributed to it.
- **Contradiction detection**: Given an Evidence Node, find all contradicting Evidence.

### 4.5 Evidence invariants

1. Evidence is immutable once recorded (constitutional: O-03).
2. Evidence is append-only (constitutional: O-03).
3. Every Node must have at least one Evidence reference (except constitutional Nodes).
4. Every Edge must have at least one Evidence reference (except constitutional edges).
5. Every Prediction must have an Evidence chain (constitutional: O-07).
6. Conflicting Evidence is preserved (constitutional: both positions held until resolution).

---

## 5. Temporal Graph

### 5.1 Purpose

Reality changes. The Temporal Graph enables SHUNYA to reason about the past, present, and future simultaneously.

### 5.2 Temporal edge types

| Edge type | Meaning | Example |
|-----------|---------|---------|
| **historical** | Was true in the past, may no longer be true | Person WORKED_AT Company (past) |
| **current** | Is true now | Person WORKS_AT Company (present) |
| **future** | Predicted to be true | Person WILL_WORK_AT Company (predicted) |
| **scheduled** | Will be true at a specific future time | Meeting OCCURS_ON date |
| **expired** | Was true, is no longer true, and will not become true again | Contract EXPIRED_ON date |
| **superseded** | Was true, has been replaced by a newer truth | Address SUPERSEDED_BY new_address |

### 5.3 Temporal edge validity

Every Edge carries an optional validity period:

```
Edge {
  ...
  validity: TimeRange {
    start: Timestamp   (when the edge became valid)
    end:   Timestamp   (when the edge ceased to be valid, or null if still valid)
  }
}
```

### 5.4 Temporal queries

The graph supports:

- **Point-in-time query**: "What was the relationship graph at time T?"
- **Range query**: "What relationships were active between T1 and T2?"
- **Change query**: "What changed between T1 and T2?"
- **Future query**: "What relationships are predicted to be active at time T?"
- **Alternative timeline**: "What if scenario X had occurred?"

### 5.5 Temporal invariants

1. Every Edge may have a `validity` period. If absent, the edge is assumed valid from creation.
2. Historical edges are not deleted. They are marked with `end` timestamp.
3. Temporal queries that do not specify a time return the current state.
4. Alternative timelines are isolated from the main timeline.

---

## 6. Context Resolution Engine

### 6.1 Purpose

The Context Resolution Engine determines what the founder is currently looking at, what surrounds it, and what is relevant — without loading the entire graph.

### 6.2 Resolution pipeline

```
Founder intention (navigation, search, click)
  ↓
Resolve target Node identity
  ↓
Load Node (by identity)
  ↓
Load 1-hop neighbourhood (edges + adjacent Nodes)
  ↓
Score neighbourhood by relevance to current context
  ↓
Load 2-hop neighbourhood (if needed for depth)
  ↓
Filter by:
  - Visibility (founder can see)
  - Temporal validity (currently active)
  - Confidence threshold (≥ 0.3)
  ↓
Return resolved context
```

### 6.3 Context resolution outputs

| Output | Source | Description |
|--------|--------|-------------|
| **Current object** | Target Node | The object the founder is focused on |
| **Surrounding graph** | 1-hop neighbourhood | Directly connected Nodes and Edges |
| **Related entities** | 2-hop neighbourhood | Indirectly connected Nodes |
| **Active commitments** | Commitment Nodes in 1-hop | Current obligations involving the object |
| **Relevant history** | Temporal Edges | Historical events involving the object |
| **Supporting evidence** | Evidence Nodes | Evidence backing the object and its relationships |
| **Prediction context** | Prediction Nodes | Active predictions involving the object |

### 6.4 Resolution parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `depth` | 1 | Number of hops from target |
| `max_nodes` | 50 | Maximum nodes to return |
| `confidence_min` | 0.3 | Minimum confidence filter |
| `temporal` | current | Temporal scope (current, historical, future) |
| `types` | all | Node type filter |

### 6.5 Context caching

Context resolution results are cached with the following TTLs:

| Context type | TTL | Invalidation trigger |
|-------------|-----|---------------------|
| Current object | Session | Object focused |
| 1-hop neighbourhood | 1 minute | RelationshipChanged event |
| 2-hop neighbourhood | 5 minutes | Any event involving the neighbourhood |
| Active commitments | 1 minute | CommitmentUpdated event |
| Supporting evidence | 5 minutes | EvidenceAdded event |

---

## 7. Knowledge Traversal

### 7.1 Purpose

The Knowledge Traversal subsystem provides efficient strategies for navigating the graph.

### 7.2 Traversal strategies

| Strategy | Description | Complexity | Use case |
|----------|-------------|------------|----------|
| **Nearest relationships** | Fetch 1-hop neighbours | O(degree) | Current context resolution |
| **Causal traversal** | Follow causal edges forward/backward | O(path_length) | "Why did this happen?" |
| **Timeline traversal** | Follow temporal edges in chronological order | O(event_count) | "What happened before/after?" |
| **Commitment traversal** | Follow commitment edges through dependency chain | O(depth) | "What depends on this?" |
| **Conversation traversal** | Follow conversation thread edges | O(message_count) | "What was said about this?" |
| **Semantic traversal** | Follow edges by type and weight | O(neighbourhood) | "What is related to this?" |
| **Prediction traversal** | Follow prediction edges to related predictions | O(prediction_count) | "What predictions involve this?" |
| **Evidence traversal** | Follow evidence edges to source Nodes | O(evidence_count) | "Why does SHUNYA think this?" |
| **Confidence traversal** | Follow confidence-weighted edges | O(neighbourhood) | "What is most certain about this?" |

### 7.3 Complexity goals

| Operation | Target complexity | Degraded threshold |
|-----------|------------------|-------------------|
| 1-hop neighbour fetch | O(1) | O(log n) |
| 2-hop neighbour fetch | O(degree²) | O(degree³) |
| Path finding (shortest) | O(n + e) | O(n²) |
| Subgraph projection | O(k) where k = nodes in subgraph | O(k log k) |
| Evidence chain traversal | O(evidence_count) | O(evidence_count²) |
| Timeline reconstruction | O(event_count) | O(event_count log event_count) |

### 7.4 Traversal invariants

1. Every traversal is bounded by `max_nodes` and `max_depth`.
2. Traversals are read-only. They never modify the graph.
3. Traversal results are deterministic for the same graph state.
4. Traversal timeouts are configurable per strategy.

---

## 8. Graph Projection

### 8.1 Purpose

The Founder Workspace never queries raw storage. It receives graph projections. A projection is a structured, filtered view of the graph optimised for a specific purpose.

### 8.2 Projection types

| Projection | Purpose | Content | Max nodes |
|------------|---------|---------|-----------|
| **Workspace Projection** | Render the current object + intelligence | Current Node, 1-hop neighbourhood, evidence, predictions | 50 |
| **Conversation Projection** | Render a conversation | Conversation Node, message chain, referenced Nodes | 200 |
| **Execution Projection** | Render an execution trace | Execution Node, causal chain, outcomes | 100 |
| **Meeting Projection** | Render a meeting | Meeting Node, attendees, agenda, decisions | 100 |
| **Relationship Projection** | Render the relationship graph around a Node | 2-hop neighbourhood, filtered by type | 200 |
| **Timeline Projection** | Render chronological events | Event Nodes, temporal edges, ordered by time | 500 |
| **Evidence Projection** | Render the evidence chain for a Node | Evidence Nodes, observation chain, confidence trace | 100 |
| **Prediction Projection** | Render active predictions for a Node | Prediction Nodes, evidence, confidence, horizon | 50 |
| **Commitment Projection** | Render active commitments for a Node | Commitment Nodes, dependency chain, status | 50 |
| **Search Projection** | Render search results | Matching Nodes, brief context, relevance score | 100 |

### 8.3 Projection assembly

Every projection is assembled by:

1. **Resolve** the root Node(s) for the projection.
2. **Traverse** the graph according to the projection's strategy.
3. **Filter** by visibility, confidence, temporal validity.
4. **Score** by relevance to the current context.
5. **Limit** to the projection's max node count.
6. **Serialize** to the projection format.

### 8.4 Projection contract

```python
@dataclass
class GraphProjection:
    projection_id: str
    projection_type: str
    root_node: NodeView
    nodes: List[NodeView]
    edges: List[EdgeView]
    evidence: List[EvidenceView]
    metadata: ProjectionMetadata
    timestamp: Timestamp
```

### 8.5 Projection caching

| Projection type | Cache TTL | Invalidation |
|----------------|-----------|--------------|
| Workspace | None (computed fresh) | — |
| Conversation | 30 seconds | New message event |
| Execution | Until execution completes | Execution outcome event |
| Meeting | 5 minutes | Meeting update event |
| Relationship | 1 minute | RelationshipChanged event |
| Timeline | 5 minutes | Any event involving the root Node |
| Evidence | 5 minutes | EvidenceAdded event |
| Prediction | 1 minute | PredictionResolved event |
| Commitment | 1 minute | CommitmentUpdated event |
| Search | None (computed fresh) | — |

---

## 9. Consistency Model

### 9.1 Purpose

Reality must remain internally consistent. The Consistency Model defines how the graph validates itself.

### 9.2 Validation types

| Validation | Scope | Frequency | Action on failure |
|------------|-------|-----------|-------------------|
| **Graph validation** | Entire graph | Periodic (daily) | Flag inconsistencies |
| **Relationship validation** | Per relationship | On creation | Reject invalid relationships |
| **Identity validation** | Per node | On creation | Reject duplicate identities |
| **Evidence validation** | Per evidence reference | On creation | Reject orphaned references |
| **Context validation** | Per context resolution | On resolution | Return partial context |
| **Prediction validation** | Per prediction | On creation | Reject unsupported predictions |

### 9.3 Graph validation rules

| Rule | Description | Severity |
|------|-------------|----------|
| No orphaned Nodes | Every Node must have at least one Edge within 24 hours | WARNING |
| No duplicate identities | Two Nodes may not share the same identity | ERROR |
| No self-referencing cycles | A Node may not directly reference itself (except for valid self-relationships) | ERROR |
| No broken references | Every Edge source and target must exist | ERROR |
| Evidence integrity | Every Evidence reference must point to an existing Evidence Node | ERROR |
| Confidence bounds | Every confidence score must be 0.0 – 1.0 | ERROR |
| Type validity | Every Node type must exist in the Universal Type System | ERROR |
| State validity | Every Node state must be a valid transition from its previous state | ERROR |

### 9.4 Consistency levels

| Level | Behaviour | When used |
|-------|-----------|-----------|
| **Strong** | All mutations validated before commit | Workspace operations, governance operations |
| **Eventual** | Mutations accepted, validated asynchronously | Bulk imports, background operations |
| **Read-only** | No mutations, validation on read | Projection assembly, traversal |

---

## 10. Graph Events

### 10.1 Purpose

All graph changes are published as events on the Cognitive Event Bus. This enables real-time synchronisation, audit, and reactive behaviour.

### 10.2 Canonical graph events

| Event | Trigger | Payload | Consumers |
|-------|---------|---------|-----------|
| `NodeCreated` | New Node added to graph | Node identity, type, attributes | Projection Engine, Memory, Search Index |
| `NodeUpdated` | Node attributes modified | Node identity, changed attributes | Projection Engine, Memory, Search Index |
| `NodeArchived` | Node moved to ARCHIVE state | Node identity | Projection Engine, Memory |
| `NodeDeleted` | Node removed from active graph | Node identity | Projection Engine, Memory |
| `RelationshipCreated` | New Edge added | Source, target, type, confidence | Context Resolution, Attention Engine |
| `RelationshipRemoved` | Edge removed | Source, target, type | Context Resolution, Attention Engine |
| `RelationshipUpdated` | Edge weight/confidence changed | Source, target, type, changes | Context Resolution, Attention Engine |
| `EvidenceAdded` | New Evidence referenced | Node/Edge identity, evidence ref | Knowledge Engine, Confidence Engine |
| `PredictionCreated` | New Prediction added | Prediction Node, target, horizon | Intelligence Panel, Attention Engine |
| `PredictionResolved` | Prediction outcome determined | Prediction Node, outcome, accuracy | Learning Engine, Calibration |
| `CommitmentUpdated` | Commitment state changed | Commitment Node, new state | Attention Engine, Intelligence Panel |
| `ContextChanged` | Founder focus changed | Previous Node, current Node | Workspace Projection, Memory |
| `KnowledgePromoted` | Knowledge moved to higher tier | Knowledge Node, new tier | Knowledge Engine, Memory |
| `MemoryPromoted` | Memory moved to higher layer | Memory reference, new layer | Memory Consolidation |
| `ExecutionCompleted` | Execution finished | Execution Node, outcome | Learning Engine, Timeline |

### 10.3 Event propagation

1. Events are published to the Cognitive Event Bus (see COGNITIVE_WORKSPACE_RUNTIME.md §9).
2. Consumers subscribe to event types.
3. Events are delivered at least once.
4. Event ordering is by causation (causation_id forms a DAG).
5. Events carry a `correlation_id` for tracing across subsystems.

---

## 11. Scalability Strategy

### 11.1 Purpose

The Universal Knowledge Graph must support millions of Nodes, millions of Relationships, and years of history. This section defines the architectural strategy for scale — not a specific technology implementation.

### 11.2 Partitioning

| Strategy | Description | Trade-off |
|----------|-------------|-----------|
| **Type-based sharding** | Nodes partitioned by type family | Even distribution depends on data shape |
| **Temporal partitioning** | Historical data in cold storage, active data in hot storage | Query complexity increases for cross-temporal queries |
| **Relationship-local clustering** | Nodes with dense relationships stored together | Reduces traversal cost for 1-hop queries |
| **Tenant isolation** | Multi-tenant graph partitioned by tenant | Cross-tenant queries not supported |

### 11.3 Incremental loading

The graph supports incremental loading:

- Nodes are loaded on demand (context resolution loads only the required neighbourhood).
- Full graph scans are never required for workspace operations.
- Bulk operations (import, migration) use eventual consistency.

### 11.4 Projection caching

Projections are cached at the workspace boundary (see §8.5). The cache is:

- Per-user (different users see different projections based on visibility).
- Per-session (projections expire when the session ends).
- Invalidation-based (events trigger cache invalidation).

### 11.5 Lazy traversal

Traversal is lazy:

- 1-hop neighbourhood is loaded eagerly (on context resolution).
- 2-hop neighbourhood is loaded on demand (when the founder expands a relationship).
- Evidence chain is loaded on demand (when the founder opens the intelligence panel).
- Full history is loaded on demand (when the founder opens the timeline).

### 11.6 Background indexing

| Index | What it indexes | Update frequency | Used by |
|-------|----------------|------------------|---------|
| Identity index | All Node identities | Real-time | Context Resolution |
| Type index | Nodes by type | Real-time | Search, Projection |
| Label index | Nodes by label | Real-time | Search, Filtering |
| Edge index | Edges by source, target, type | Real-time | Traversal |
| Text index | Node attributes (text) | Periodic (30s) | Search |
| Temporal index | Edges by validity period | Periodic (60s) | Timeline, Temporal queries |

---

## 12. Failure Recovery

### 12.1 Failure modes

| Failure | Detection | Recovery | Data loss? |
|---------|-----------|----------|------------|
| **Missing Node** | Edge references non-existent Node | Remove broken Edge; log for investigation | No (Edge removed) |
| **Broken Edge** | Edge source or target cannot be loaded | Return partial context; flag Edge | No |
| **Circular relationship** | Traversal detects cycle | Break cycle at lowest-weight Edge; log | No |
| **Duplicate identity** | Two Nodes share same identity | Merge into single Node; flag for review | No (all evidence preserved) |
| **Conflicting evidence** | Two Evidence Nodes contradict each other | Present both with confidence scores; do not resolve | No |
| **Graph corruption** | Integrity check fails | Restore from last verified checkpoint; replay event log | No (checkpoint restore) |
| **Projection failure** | Projection assembly fails | Return minimal projection (Node identity only) | No (degraded) |
| **Traversal timeout** | Traversal exceeds time limit | Return partial results; log timeout | No |
| **Context ambiguity** | Multiple Nodes match resolution | Return all candidates with confidence scores | No |

### 12.2 Recovery behaviour

| Failure | Immediate action | Background action | Notification |
|---------|-----------------|-------------------|--------------|
| Missing Node | Remove broken Edge | Log investigation ticket | Governance |
| Broken Edge | Flag Edge for repair | Run integrity check | None |
| Circular relationship | Break cycle | Log for review | Governance |
| Duplicate identity | Lock both Nodes | Schedule merge | Founder |
| Conflicting evidence | Hold both positions | Flag for resolution | None |
| Graph corruption | Restore checkpoint | Replay event log | Governance |
| Projection failure | Return minimal projection | Retry assembly | None |
| Traversal timeout | Return partial results | Optimise traversal | None |
| Context ambiguity | Return all candidates | Improve resolution | None |

---

## 13. Security Model

### 13.1 Purpose

The graph must enforce visibility, ownership, and permissions at the architectural level — not at the application level.

### 13.2 Visibility

| Visibility level | Who can see | Default for |
|------------------|-------------|-------------|
| **Public** | All users | System Nodes, constitutional Nodes |
| **Organisation** | All members of the organisation | Organisational Nodes |
| **Team** | Members of the team | Team-specific Nodes |
| **Private** | Owner only | Personal Nodes |
| **Confidential** | Explicitly authorised users | Sensitive Nodes |

Every Node carries a `visibility` attribute. Every projection filters by the requesting user's visibility level.

### 13.3 Ownership

Every Node has exactly one owner (constitutional: O-13). Ownership determines:

- Who can modify the Node.
- Who can delete the Node.
- Who can grant access to the Node.

### 13.4 Permissions

| Operation | Permission required | Who can grant |
|-----------|---------------------|---------------|
| Create Node | WRITE on parent context | Owner |
| Read Node | READ on the Node | Owner or granted access |
| Update Node | WRITE on the Node | Owner |
| Delete Node | DELETE on the Node | Owner or Governance |
| Add Edge | WRITE on source Node | Source owner |
| Remove Edge | WRITE on source Node | Source owner |
| Add Evidence | WRITE on target Node | Target owner |
| Grant access | OWNER on the Node | Owner |

### 13.5 Evidence privacy

Evidence Nodes carry the visibility of the source that created them. A founder's direct observation is PRIVATE. A system observation is ORGANISATION.

### 13.6 Relationship privacy

Relationship Edges carry the minimum visibility of their source and target Nodes. If source is PRIVATE and target is PUBLIC, the Edge is PRIVATE.

### 13.7 Graph isolation

- Multi-tenant graphs are isolated at the Tenant level.
- Cross-tenant queries are not supported.
- Tenant isolation is enforced by the graph layer, not the application layer.

### 13.8 Auditability

Every mutation to the graph is recorded in the audit trail:

| Mutation | Audit record |
|----------|-------------|
| Node created | Actor, timestamp, Node identity |
| Node updated | Actor, timestamp, changed attributes |
| Node deleted | Actor, timestamp, Node identity |
| Edge created | Actor, timestamp, source, target, type |
| Edge removed | Actor, timestamp, source, target, type |
| Evidence added | Actor, timestamp, Evidence reference |

---

## 14. Implementation Boundaries

### 14.1 Purpose

Prevent architectural leakage. Every subsystem has a defined boundary. No subsystem may cross into another's territory.

### 14.2 Boundary definitions

| Subsystem | Owns | Does NOT own | Reference document |
|-----------|------|--------------|-------------------|
| **Ontology** | What things ARE | How things connect | UNIVERSAL_ONTOLOGY.md |
| **Knowledge Graph** | How things connect | How cognition flows | This document |
| **Workspace Runtime** | How cognition flows | How things are stored | COGNITIVE_WORKSPACE_RUNTIME.md |
| **Adaptive Runtime** | How SHUNYA evolves | How the graph is stored | ADAPTIVE_INTELLIGENCE_RUNTIME.md |
| **Execution Engine** | How actions are performed | How predictions are made | ES-005 |
| **Prediction Engine** | How predictions are made | How actions are performed | Milestone III |
| **Memory System** | How knowledge is stored and retrieved | How knowledge is validated | COGNITIVE_WORKSPACE_RUNTIME.md §5 |

### 14.3 Boundary rules

1. **The Knowledge Graph does not implement cognition.** It stores and connects. It does not reason.
2. **The Workspace Runtime does not query raw storage.** It receives projections.
3. **The Adaptive Runtime does not modify the graph directly.** It emits events that the graph consumes.
4. **The Execution Engine does not read the graph directly.** It receives context from the Workspace Runtime.
5. **The Prediction Engine does not write to the graph.** It creates Prediction Nodes that are committed by the Knowledge Graph.

### 14.4 Communication pattern

All cross-boundary communication follows the Event Bus pattern (§10 of COGNITIVE_WORKSPACE_RUNTIME.md):

```
Subsystem A → Cognitive Event Bus → Subsystem B
```

No subsystem directly calls another subsystem's internal API.

---

## 15. Implementation Roadmap

### 15.1 Phase overview

```
Phase 9A: Core Graph       (foundation — nodes, edges, identity)
Phase 9B: Relationship     (edges, validation, traversal)
Phase 9C: Evidence Graph   (evidence chain, lineage, confidence)
Phase 9D: Projection       (projection assembly, caching)
Phase 9E: Traversal        (all traversal strategies, optimisation)
Phase 9F: Scalability      (partitioning, indexing, performance)
```

### 15.2 Phase 9A — Core Graph

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the core graph data model: Nodes, Edges, identity, types, labels, metadata |
| **Dependencies** | Universal Ontology (Phase 8D) |
| **Deliverables** | Graph data model, Node creation API, Edge creation API, identity assignment, type validation, label management |
| **Validation criteria** | Create 1000 Nodes in < 1s. Create 1000 Edges in < 1s. No duplicate identities. No orphaned Edges. |

### 15.3 Phase 9B — Relationship Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the relationship architecture: canonical edge families, validation, lifecycle, temporal edges |
| **Dependencies** | Phase 9A |
| **Deliverables** | Edge creation with validation, edge lifecycle management, temporal edge support, edge type validation |
| **Validation criteria** | All 14 canonical edge families supported. Temporal queries return correct results. No duplicate triples. |

### 15.4 Phase 9C — Evidence Graph

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the evidence graph: evidence chain, lineage, confidence traceability |
| **Dependencies** | Phase 9A, Phase 9B |
| **Deliverables** | Evidence creation, evidence chain traversal, confidence trace, contradiction detection, evidence validation |
| **Validation criteria** | Every Node has evidence chain. Every Prediction is traceable to evidence. Conflicting evidence is preserved. |

### 15.5 Phase 9D — Projection Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement graph projections: all 10 projection types, assembly, caching |
| **Dependencies** | Phase 9A, Phase 9B, Phase 9C |
| **Deliverables** | Projection assembly pipeline, 10 projection types, projection caching, invalidation |
| **Validation criteria** | All 10 projection types assemble correctly. Cache invalidation fires on relevant events. Degraded mode returns minimal projection. |

### 15.6 Phase 9E — Traversal Runtime

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement all traversal strategies: nearest, causal, timeline, commitment, conversation, semantic, prediction, evidence, confidence |
| **Dependencies** | Phase 9A, Phase 9B, Phase 9C |
| **Deliverables** | 9 traversal strategies, traversal bounds, timeout handling, complexity guarantees |
| **Validation criteria** | All 9 strategies return correct results. Timeouts do not crash. Complexity targets met. |

### 15.7 Phase 9F — Scalability

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement scalability strategy: partitioning, incremental loading, projection caching, lazy traversal, background indexing, security model |
| **Dependencies** | Phase 9A – Phase 9E |
| **Deliverables** | Partitioning strategy, incremental loading, lazy traversal, event-driven index updates, security model (visibility, ownership, permissions, audit) |
| **Validation criteria** | 1M Nodes loaded. 10M Edges loaded. 1-hop traversal < 10ms. 2-hop traversal < 100ms. Timeline reconstruction < 500ms. Tenant isolation verified. |

---

## Appendix A: Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      UNIVERSAL KNOWLEDGE GRAPH                               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  CORE GRAPH LAYER                                                      │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐  │   │
│  │  │  Node Store      │  │  Edge Store      │  │  Identity          │  │   │
│  │  │  (create, read,  │  │  (create, read,  │  │  Registry          │  │   │
│  │  │   update, delete)│  │   validate,      │  │  (assignment,      │  │   │
│  │  │                  │  │   lifecycle)     │  │   resolution,      │  │   │
│  │  │                  │  │                  │  │   uniqueness)      │  │   │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌────────────────────────────────┼─────────────────────────────────────┐   │
│  │  RELATIONSHIP LAYER            │                                      │   │
│  │  ┌──────────────────┐  ┌──────┴───────────┐  ┌────────────────────┐  │   │
│  │  │  Edge Families   │  │  Temporal        │  │  Edge Validation   │  │   │
│  │  │  (14 canonical)  │  │  Edge Manager    │  │  (type, existence, │  │   │
│  │  │                  │  │  (historical,    │  │   duplicate check) │  │   │
│  │  │                  │  │  current, future) │  │                    │  │   │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌────────────────────────────────┼─────────────────────────────────────┐   │
│  │  EVIDENCE LAYER                │                                      │   │
│  │  ┌──────────────────┐  ┌──────┴───────────┐  ┌────────────────────┐  │   │
│  │  │  Evidence Chain  │  │  Confidence      │  │  Contradiction     │  │   │
│  │  │  (lineage,       │  │  Trace           │  │  Detection         │  │   │
│  │  │   traversal)     │  │  (confidence     │  │  (conflicting      │  │   │
│  │  │                  │  │   decomposition) │  │   evidence)        │  │   │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌────────────────────────────────┼─────────────────────────────────────┐   │
│  │  PROJECTION LAYER              │                                      │   │
│  │  ┌──────────────────┐  ┌──────┴───────────┐  ┌────────────────────┐  │   │
│  │  │  Projection      │  │  Context         │  │  Projection        │  │   │
│  │  │  Assembly        │  │  Resolution      │  │  Cache             │  │   │
│  │  │  (10 types)      │  │  Engine          │  │  (TTL, invalidation)│  │   │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌────────────────────────────────┼─────────────────────────────────────┐   │
│  │  TRAVERSAL LAYER               │                                      │   │
│  │  ┌──────────────────┐  ┌──────┴───────────┐  ┌────────────────────┐  │   │
│  │  │  Traversal       │  │  Index           │  │  Scaling           │  │   │
│  │  │  Strategies (9)  │  │  Manager         │  │  (partitioning,    │  │   │
│  │  │                  │  │  (identity, type,│  │   lazy loading,    │  │   │
│  │  │                  │  │   label, edge,   │  │   caching)         │  │   │
│  │  │                  │  │   text, temporal)│  │                    │  │   │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌────────────────────────────────┼─────────────────────────────────────┐   │
│  │  SECURITY LAYER                │                                      │   │
│  │  ┌──────────────────┐  ┌──────┴───────────┐  ┌────────────────────┐  │   │
│  │  │  Visibility      │  │  Permission      │  │  Audit Trail       │  │   │
│  │  │  (public →       │  │  Enforcement     │  │  (all mutations    │  │   │
│  │  │   confidential)  │  │  (CRUD per role) │  │   recorded)        │  │   │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Appendix B: Glossary

| Term | Definition | Reference |
|------|------------|-----------|
| **Edge** | A connection between two Nodes | §1.3 |
| **Evidence Chain** | The traceable lineage from a Node or Edge back to its source Evidence | §4.3 |
| **Graph Projection** | A structured, filtered view of the graph for a specific purpose | §8 |
| **Knowledge Graph** | The executable representation of the constitutional ontology | This document |
| **Node** | A single Object in the Universal Type System | §1.2 |
| **Projection** | See Graph Projection | §8 |
| **Temporal Edge** | An Edge with a validity period | §5 |
| **Traversal** | A strategy for navigating the graph | §7 |

## Appendix C: Cross-References

| Document | How this architecture references it |
|----------|--------------------------------------|
| UNIVERSAL_ONTOLOGY.md | All Node and Edge types derive from the ontology (§18) |
| COGNITIVE_WORKSPACE_RUNTIME.md | Projections feed the Workspace Projection Engine (§3); Events feed the Cognitive Event Bus (§9) |
| ADAPTIVE_INTELLIGENCE_RUNTIME.md | Evidence Graph feeds the Confidence Engine (§2); Knowledge Evolution Engine validates Nodes (§5) |
| FOUNDER_WORKSPACE_SPECIFICATION.md | Workspace Projection (§8) delivers the view model the workspace renders |
| ES-005 (Executor Engine) | Execution Nodes are created by the Execution Engine, consumed by the graph |
| ES-006 (Observer Engine) | Observation Nodes are created by the Observer Engine |
| ES-007 (Learning Engine) | Knowledge promotion events are emitted by the graph |