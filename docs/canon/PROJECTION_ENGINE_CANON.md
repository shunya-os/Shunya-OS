# Projection Engine Canon

> **Phase K · SHUNYA OS**
> **Status: CANONICAL — Implementation-Independent Specification**
> **Version: 1.0**

---

## 1. Purpose

The Projection Engine bridges the graph layer and the workspace. It transforms raw graph state (Nodes, Edges, evidence chains, predictions) into structured, filtered **projections** that the workspace renders. The workspace never queries the graph directly — it receives projections.

### 1.1 Dependency chain

```
Knowledge Graph (how things connect)
    ↓
Projection Engine (what the workspace sees)
    ↓
Workspace Runtime (how cognition flows)
    ↓
Founder Workspace (what the founder interacts with)
```

### 1.2 Principles

1. **The workspace never queries raw storage.** Every render comes from a projection.
2. **Projections are read-only.** The workspace cannot mutate state through a projection — all writes go through the Intent Pipeline.
3. **Projections are deterministic.** Identical graph state + identical parameters → identical projection.
4. **Projections are minimal.** Only what is relevant for the current purpose is included.
5. **Projections are snapshots.** Computed at request time, cached per TTL.

---

## 2. Projection Types

### 2.1 Inventory

| # | Projection | Purpose | Max nodes | Cache TTL |
|---|------------|---------|-----------|-----------|
| 1 | **Workspace** | Render current object + intelligence | 50 | None (fresh) |
| 2 | **Conversation** | Render a conversation | 200 | 30s |
| 3 | **Execution** | Render an execution trace | 100 | Until complete |
| 4 | **Meeting** | Render a meeting | 100 | 5 min |
| 5 | **Relationship** | Render relationship graph around a Node | 200 | 1 min |
| 6 | **Timeline** | Render chronological events | 500 | 5 min |
| 7 | **Evidence** | Render evidence chain for a Node | 100 | 5 min |
| 8 | **Prediction** | Render active predictions for a Node | 50 | 1 min |
| 9 | **Commitment** | Render active commitments for a Node | 50 | 1 min |
| 10 | **Search** | Render search results | 100 | None (fresh) |

### 2.2 Projection dataclass

```
GraphProjection {
    projection_id: str        (UUID, unique per assembly)
    projection_type: str      (one of the 10 types above)
    root_node: NodeView       (the focal Node)
    nodes: List[NodeView]     (projected Nodes)
    edges: List[EdgeView]     (projected Edges)
    evidence: List[EvidenceView]  (evidence chain)
    metadata: ProjectionMetadata  (timing, source, filters applied)
    timestamp: datetime       (when assembled)
}
```

### 2.3 NodeView / EdgeView

Projections use lightweight view types — not full graph Nodes/Edges:

- **NodeView**: node_id, type, name, status, confidence, labels, attributes (key subset)
- **EdgeView**: edge_id, source_id, target_id, type, direction, confidence, validity

---

## 3. Projection Assembly Pipeline

Every projection is assembled by:

```
1. Resolve root Node(s)
    ↓
2. Traverse graph by projection strategy
    ↓
3. Filter by visibility, confidence, temporal validity, type
    ↓
4. Score by relevance to current context
    ↓
5. Limit to max node count
    ↓
6. Serialize to GraphProjection
```

### 3.1 Resolve

Input: object_id, projection_type
Output: root Node(s)

- Workspace, Relationship, Timeline, Evidence, Prediction, Commitment: single root Node
- Conversation: Conversation Node (resolved from message or thread ID)
- Execution: Execution Node (resolved from trace ID)
- Meeting: Meeting Node (resolved from meeting ID)
- Search: multiple match Nodes (resolved from query)

### 3.2 Traverse

| Projection | Traversal strategy |
|------------|-------------------|
| Workspace | 1-hop + evidence + prediction edges |
| Conversation | Message chain edges, chronological |
| Execution | Causal chain edges, forward |
| Meeting | 1-hop attendee + agenda edges |
| Relationship | 2-hop, filtered by relationship type |
| Timeline | Temporal edges, chronological order |
| Evidence | Evidence edges, backward to source |
| Prediction | Prediction edges, forward |
| Commitment | Commitment edges, dependency chain |
| Search | Type-based node lookup |

### 3.3 Filter

All projections apply:
- **Visibility filter** — only nodes the caller's security context can see
- **Confidence filter** — minimum threshold (default 0.3)
- **Type filter** — projection-specific type whitelist
- **Status filter** — exclude ARCHIVED/PENDING/SUPERSEDED unless explicitly requested

### 3.4 Score

| Projection | Scoring dimension |
|------------|------------------|
| Workspace | Temporal recency + confidence |
| Conversation | Chronological (by timestamp) |
| Execution | Causal order |
| Meeting | Agenda order |
| Relationship | Edge weight + confidence |
| Timeline | Temporal order |
| Evidence | Recency + confidence |
| Prediction | Horizon nearness + confidence |
| Commitment | Due-date nearness + priority |
| Search | Relevance score |

### 3.5 Limit

Hard limit per projection type (see §2.1). If the limit is exceeded, lowest-scored items are dropped. The `total_available` field in ProjectionMetadata records how many items were available before limiting.

---

## 4. Caching

### 4.1 Cache behaviour

| Projection type | TTL | Invalidation trigger |
|----------------|-----|---------------------|
| Workspace | None (fresh) | — |
| Conversation | 30s | New message event |
| Execution | Until complete | Execution outcome event |
| Meeting | 5 min | Meeting update event |
| Relationship | 1 min | RelationshipChanged event |
| Timeline | 5 min | Any event involving root Node |
| Evidence | 5 min | EvidenceAdded event |
| Prediction | 1 min | PredictionResolved event |
| Commitment | 1 min | CommitmentUpdated event |
| Search | None (fresh) | — |

### 4.2 Cache entry

```
CacheEntry {
    key: str               (projection_type:root_id[:query_hash])
    projection: GraphProjection
    expires_at: datetime
    invalidated: bool      (marked for early expiry)
}
```

### 4.3 Invalidation

- Cache can be explicitly invalidated by event type + root node ID
- Invalidated entries are not returned but remain until garbage collected
- Garbage collection runs lazily (on read of expired entries)

---

## 5. Context Resolution

### 5.1 Purpose

Context Resolution provides the surrounding graph context for a given object. It is consumed by the Workspace Projection and Relationship Projection.

### 5.2 Resolution outputs

| Output | Source | Description |
|--------|--------|-------------|
| Current object | Root Node | The object being projected |
| Surrounding graph | 1-hop neighbourhood | Directly connected Nodes and Edges |
| Related entities | 2-hop neighbourhood | Indirectly connected Nodes |
| Active commitments | Commitment edges | Current obligations involving the object |
| Relevant history | Temporal edges | Historical events involving the object |
| Supporting evidence | Evidence edges | Evidence backing the object |
| Prediction context | Prediction edges | Active predictions involving the object |

### 5.3 Resolution parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `depth` | 1 | Number of hops from target |
| `max_nodes` | 50 | Maximum nodes to return |
| `confidence_min` | 0.3 | Minimum confidence filter |
| `temporal_scope` | current | Temporal scope (current, historical, future) |
| `node_types` | all | Node type whitelist |

---

## 6. Degraded Mode

When the Knowledge Graph is unavailable or slow, projections degrade gracefully:

| Failure | Behaviour |
|---------|-----------|
| Graph unavailable | Return minimal projection (root node only, no neighbours) |
| Graph slow (>500ms) | Return cached version if available, else minimal |
| Cache miss + graph failure | Return error projection with `degraded=True` flag |

---

## 7. Constitutional Invariants

1. **Projections are read-only.** The workspace cannot write to cognitive state through a projection.
2. **Projections are deterministic.** Identical inputs → identical outputs for the same graph state.
3. **Projections are snapshots.** Computed at request time, never streamed.
4. **Projections carry provenance.** Every projection has a unique projection_id and timestamp.
5. **No business logic in projections.** The Projection Engine is universal and business-agnostic.
6. **Degraded mode never returns wrong data.** It returns less data, never incorrect data.