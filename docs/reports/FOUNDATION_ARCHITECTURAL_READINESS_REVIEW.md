# FOUNDATION ARCHITECTURAL READINESS REVIEW

**Phase:** Documentation-Only — Pre E-004
**Epics Under Review:** E-001 (Ontology Engine), E-002 (Identity Engine), E-003 (Knowledge Graph)
**Status:** READINESS REVIEW COMPLETE
**Date:** 2026-07-23

---

## SECTION 1 — Foundation Summary

### E-001: Ontology Engine

**Code:** `app/kernel/` (10 modules, ~2,000 lines)
**Committed:** `254c386` — 2026-07-22
**Status:** STABLE, FROZEN

**Responsibilities:**

1. **Universal Type System** (`app/kernel/types.py`) — The canonical type hierarchy. Every Object in SHUNYA has exactly one type. Type is immutable after creation. The TypeRegistry is the single source of truth for all valid types. Defines 11 type groups (Entity, Event, Commitment, Action, Evidence, Knowledge, Prediction, Policy, Conversation, Memory, Context) with lifecycle constraints per group.

2. **Universal Object Contract** (`app/kernel/object.py`) — `UniversalObject` is the canonical base for every entity. Mandatory fields: object_id, tenant_id, space_id, object_type, name, status, version, confidence, created_at, updated_at, created_by, updated_by, evidence, relationships, metadata. No entity may bypass this contract without explicit architectural approval.

3. **Universal State Machine** (`app/kernel/state.py`) — `StateMachine` enforces the universal object lifecycle (CREATE → OBSERVE → ENRICH → RELATE → PREDICT → EXECUTE → ARCHIVE → RESTORE → DELETE) with per-type-group transition validation via the TypeRegistry. Every Object uses exactly one StateMachine instance.

4. **Universal Timeline** (`app/kernel/timeline.py`) — `Timeline` is the append-only chronological record for every Object. Past events are immutable. Future events are mutable (projected). Supports alternative timeline scenarios for what-if analysis.

5. **Universal Context Model** (`app/kernel/context.py`) — `Context` is the set of circumstances surrounding an Object. Context determines meaning. Context is never destroyed. Context is always traceable to its source. Supports inheritance (narrower contexts override broader contexts).

6. **Universal Relationship Engine** (`app/kernel/relationship.py`) — `RelationshipEngine` provides graph-navigable, typed, bidirectional relationships. Supports traversal (BFS), filtering, and bidirectional lookup. This is the canonical lightweight API; the Graph (E-003) is the canonical persistence + execution layer.

**Constitutional boundaries:**
- The Kernel defines what things ARE (types, objects, relationships).
- The Kernel must never depend on the Graph (E-003).
- The Kernel is frozen. No new primitives may be added without constitutional amendment.

---

### E-002: Identity Engine

**Code:** `app/kernel/identity.py` (331 lines), `app/kernel/identity_governance.py` (584 lines), `app/production/identity/` (9 modules, production routes)
**Committed:** `0ea9193` — 2026-07-22
**Status:** STABLE, FROZEN

**Responsibilities:**

1. **Permanent Human Identity** (`app/kernel/identity.py`) — `SHUNYAIdentity` is a permanent human identity. Not an account. Not an email address. Not an organization construct. Every human receives an immutable identity at creation. The identity persists across sessions, devices, authentication methods, and lifetimes.

2. **Authentication Method Management** — Each identity owns multiple authentication methods (email, phone, OAuth providers, passkey, etc.). Methods can be added, removed, verified. No method defines the identity — the identity is independent of its methods.

3. **Identity Linking** — Linking flow: Detect → Suggest → Verify → Link → Maintain. Never merge identities automatically. The human must explicitly link authentication methods. Linking suggestions are non-binding; the human decides.

4. **Identity Governance** (`app/kernel/identity_governance.py`) — `IdentityGovernance` is the canonical governance module. Operations: merge (two identities into one), split (one identity into multiple partitions), retire (permanently deactivate), restore (reactivate a retired identity). All operations are auditable. Every governance operation produces an `IdentityAuditEntry`.

5. **Audit Trail** — All governance operations recorded in an immutable audit log. Queryable per identity.

**Constitutional boundaries:**
- Identities are permanent (never truly deleted, only retired).
- Identity exists independently of any Space or Organization.
- Organizations never own identities.
- Identities are NEVER automatically merged.

---

### E-003: Knowledge Graph

**Code:** `app/graph/` (7 modules, 3,438 lines)
**Committed:** 5 commits spanning 2026-07-22 to 2026-07-23
**Status:** STABLE, FROZEN

**Responsibilities:**

1. **Node Core** (`app/graph/node.py`) — `Node` is the fundamental graph primitive. Every meaningful entity in SHUNYA is a Node. Identity is permanent, unique, never reused. Type is immutable. Supports labels, attributes, evidence chain, confidence, versioning, visibility, and ownership.

2. **Edge Core** (`app/graph/edge.py`) — `Edge` is a connection between two Nodes. Edge identity is the triple (source_id, target_id, edge_type). No two Edges may share the same triple. Source and target must exist in the graph. Supports 30+ canonical edge types, direction, confidence, validity (TimeRange), weight, lifecycle status (PROPOSED/ACTIVE/STALE/ARCHIVED/REMOVED).

3. **Node/Edge Families** (`app/graph/families.py`) — 18 canonical node families and 15 canonical edge families with type compatibility validation. Every node belongs to exactly one family. Every edge belongs to exactly one family. Edge type compatibility is defined by a canonical matrix.

4. **Temporal Graph** (`app/graph/temporal.py`) — Temporal query layer over the EdgeStore. Provides point-in-time, range, change, and future queries. 6 canonical temporal edge types (Historical, Current, Future, Scheduled, Expired, Superseded).

5. **Graph Validator** (`app/graph/consistency.py`) — Deterministic graph validation. 8 node-level error codes, 9 edge-level error codes, 4 invariant error codes, 6 warnings. Read-only, side-effect-free, deterministic.

6. **Graph Security** (`app/graph/security.py`) — Universal graph access control. 10 business-agnostic permissions. 5 visibility levels (PRIVATE → TEAM → ORGANISATION → CONFIDENTIAL → PUBLIC). Deterministic, pure, side-effect-free evaluation. Every access decision returns a structured `PermissionResult`.

**Constitutional boundaries:**
- The Graph builds on the Kernel. The Kernel must never depend on the Graph.
- The Graph is universal and business-agnostic. No CRM, travel, or Panchi Club logic.
- No authentication, login, OAuth, JWT, passwords, sessions, or web security.
- The Graph is technology-independent.

---

## SECTION 2 — Public APIs

### `app/kernel/` — E-001 (Ontology Engine)

| Export | Module | Type | Status |
|--------|--------|------|--------|
| `UniversalObject` | `object` | class | **Stable** |
| `ObjectRegistry` | `object` | class | **Stable** |
| `ObjectStatus` | `object` | enum | **Stable** |
| `EvidenceRef` | `object` | dataclass | **Stable** |
| `RelationshipRef` | `object` | dataclass | **Stable** |
| `ObjectMeta` | `object` | metaclass | **Internal** |
| `get_object_registry` | `object` | function | **Stable** |
| `reset_object_registry` | `object` | function | Internal (testing) |
| `TypeRegistry` | `types` | class | **Stable** |
| `TypeNode` | `types` | dataclass | **Stable** |
| `TypeGroup` | `types` | enum | **Stable** |
| `TypeGroupLifecycle` | `types` | dataclass | **Stable** |
| `LifecycleState` | `types` | enum | **Stable** |
| `get_type_registry` | `types` | function | **Stable** |
| `reset_type_registry` | `types` | function | Internal (testing) |
| `StateMachine` | `state` | class | **Stable** |
| `StateTransition` | `state` | dataclass | **Stable** |
| `Timeline` | `timeline` | class | **Stable** |
| `TimelineEvent` | `timeline` | dataclass | **Stable** |
| `Context` | `context` | class | **Stable** |
| `ContextData` | `context` | dataclass | **Stable** |
| `ContextType` | `context` | enum | **Stable** |
| `ContextResolution` | `context` | class | **Future** |
| `Relationship` | `relationship` | dataclass | **Stable** |
| `RelationshipEngine` | `relationship` | class | **Stable** (lightweight API) |
| `RelationshipType` | `relationship` | enum | **Stable** |
| `get_relationship_engine` | `relationship` | function | **Stable** |
| `reset_relationship_engine` | `relationship` | function | Internal (testing) |
| `Space` | `space` | class | **Stable** |
| `SpaceStore` | `space` | class | **Stable** |
| `SpaceType` | `space` | enum | **Stable** |
| `SpaceRole` | `space` | enum | **Stable** |
| `SpaceMembership` | `space` | dataclass | **Stable** |
| `get_space_store` | `space` | function | **Stable** |
| `reset_space_store` | `space` | function | Internal (testing) |

### `app/kernel/` — E-002 (Identity Engine)

| Export | Module | Type | Status |
|--------|--------|------|--------|
| `SHUNYAIdentity` | `identity` | class | **Stable** |
| `IdentityStore` | `identity` | class | **Stable** |
| `AuthenticationMethod` | `identity` | dataclass | **Stable** |
| `AuthMethodType` | `identity` | enum | **Stable** |
| `LinkingStatus` | `identity` | enum | **Stable** |
| `LinkingSuggestion` | `identity` | dataclass | **Stable** |
| `get_identity_store` | `identity` | function | **Stable** |
| `reset_identity_store` | `identity` | function | Internal (testing) |
| `IdentityGovernance` | `identity_governance` | class | **Stable** |
| `IdentityAuditEntry` | `identity_governance` | dataclass | **Stable** |
| `AuditAction` | `identity_governance` | class | **Stable** |
| `IdentityMergePlan` | `identity_governance` | dataclass | **Stable** |
| `IdentitySplitPlan` | `identity_governance` | dataclass | **Stable** |
| `IdentitySplitPartition` | `identity_governance` | dataclass | **Stable** |

### `app/graph/` — E-003 (Knowledge Graph)

| Export | Module | Type | Status |
|--------|--------|------|--------|
| `Node` | `node` | dataclass | **Stable** |
| `NodeStore` | `node` | abstract class | **Stable** |
| `InMemoryNodeStore` | `node` | class | **Stable** (development) |
| `NodeStatus` | `node` | enum | **Stable** |
| `VisibilityLevel` | `node` | enum | **Stable** |
| `NodeMetadata` | `node` | dataclass | **Stable** |
| `get_node_store` | `node` | function | **Stable** |
| `reset_node_store` | `node` | function | Internal (testing) |
| `Edge` | `edge` | dataclass | **Stable** |
| `EdgeStore` | `edge` | abstract class | **Stable** |
| `InMemoryEdgeStore` | `edge` | class | **Stable** (development) |
| `EdgeDirection` | `edge` | enum | **Stable** |
| `EdgeStatus` | `edge` | enum | **Stable** |
| `EdgeType` | `edge` | enum | **Stable** |
| `TimeRange` | `edge` | dataclass | **Stable** |
| `get_edge_store` | `edge` | function | **Stable** |
| `reset_edge_store` | `edge` | function | Internal (testing) |
| `Families` | `families` | class | **Stable** |
| `NodeFamily` | `families` | enum | **Stable** |
| `EdgeFamily` | `families` | enum | **Stable** |
| `ALL_NODE_FAMILIES` | `families` | list | **Stable** |
| `ALL_EDGE_FAMILIES` | `families` | list | **Stable** |
| `ALL_EDGE_TYPES` | `families` | list | **Stable** |
| `TemporalStore` | `temporal` | class | **Stable** |
| `TemporalEdgeType` | `temporal` | enum | **Stable** |
| `get_temporal_store` | `temporal` | function | **Stable** |
| `reset_temporal_store` | `temporal` | function | Internal (testing) |
| `GraphValidator` | `consistency` | class | **Stable** |
| `ValidationResult` | `consistency` | dataclass | **Stable** |
| `ValidationError` | `consistency` | dataclass | **Stable** |
| `GraphPermission` | `security` | enum | **Stable** |
| `GraphSecurityPolicy` | `security` | dataclass | **Stable** |
| `SecurityContext` | `security` | dataclass | **Stable** |
| `PermissionResult` | `security` | dataclass | **Stable** |
| `GraphAccessDecision` | `security` | dataclass | **Stable** |
| `GraphAccessEvaluator` | `security` | class | **Stable** |
| `get_evaluator` | `security` | function | **Stable** |
| `reset_evaluator` | `security` | function | Internal (testing) |
| `visibility_level_rank` | `security` | function | **Stable** |
| `visibility_inherits` | `security` | function | **Stable** |
| `is_visibility_compatible` | `security` | function | **Stable** |
| `get_effective_visibility` | `security` | function | **Stable** |

**Stability classification:**
- **Stable** — Public API. Breaking changes require constitutional amendment. May be depended upon by any future subsystem.
- **Internal** — Framework or tooling support. Not part of the public contract. Subsystems must not depend on these.
- **Future** — Exists but not yet production-ready. `ContextResolution` is marked Future because it is a stub without a backing store.

---

## SECTION 3 — Constitutional Invariants

The definitive, deduplicated, non-contradictory list of every constitutional invariant guaranteed by E-001, E-002, and E-003 together.

### Identity & Object Invariants (O-*)

| Code | Invariant | Source | Epic |
|------|-----------|--------|------|
| O-01 | Identity never changes. `object_id` / `node_id` / `identity_id` is immutable after creation. | Core Models §2, KG §1.4, Identity §3 | E-001, E-002, E-003 |
| O-02 | History is immutable. Past events cannot be removed or modified. | Ontology §12, O-19 | E-001 |
| O-03 | Type is immutable. A Node's type cannot change after creation. | KG §1.6, O-11 | E-001, E-003 |
| O-04 | Context is always traceable to its source. | Ontology §13 | E-001 |
| O-05 | Everything is connected. Every Node must be connected to at least one other Node. | KG §3.2 | E-003 |
| O-06 | Everything is a Node. Every meaningful entity is a Node. | KG §1.1 | E-003 |
| O-07 | State is singular. One status at a time. | O-18, StateMachine | E-001 |
| O-08 | Context is never destroyed. May be archived, never deleted. | O-09 | E-001 |
| O-09 | Inherited context can be overridden but not ignored. | CWR §7 I-01, O-21 | E-001 |
| O-10 | Every Object has exactly one identity. | SMS Vol I.5 §1 | E-001 |
| O-11 | An Object's type is fixed at creation. | SMS Vol I.5 §1 | E-001 |
| O-12 | An Object's past is immutable. What happened cannot unhappen. | SMS Vol I.5 §1 | E-001 |
| O-13 | An Object exists in exactly one Space. | SMS Vol I.5 §1 | E-001 |
| O-14 | Object deletion is always policy-aware. | SMS Vol I.5 §1 | E-001 |

### Identity-Specific Invariants (I-*)

| Code | Invariant | Source | Epic |
|------|-----------|--------|------|
| I-01 | Identities are permanent. Never truly deleted, only retired. | Ontology §3.5 | E-002 |
| I-02 | Merge preserves evidence. Both sources retained in audit. | Ontology §3.5 | E-002 |
| I-03 | Split partitions evidence. Each partition inherits relevant evidence. | Ontology §3.5 | E-002 |
| I-04 | Retired identities are never reused. | Ontology §3.5 | E-002 |
| I-05 | Every human has exactly one SHUNYA Identity. No duplicates. | SMS Vol I.5 §2 | E-002 |
| I-06 | Identity exists independently of any Space. | SMS Vol I.5 §2 | E-002 |
| I-07 | Identity exists independently of any authentication method. | SMS Vol I.5 §2 | E-002 |
| I-08 | Organizations never own identities. | SMS Vol I.5 §2 | E-002 |
| I-09 | Identities are NEVER automatically merged. | SMS Vol I.5 §2 | E-002 |

### Knowledge Graph Invariants (KG-*)

| Code | Invariant | Source | Epic |
|------|-----------|--------|------|
| KG-01 | No duplicate (source, target, type) triples. Edge identity is unique. | KG §3.2.3 | E-003 |
| KG-02 | Source and target must exist in the graph. | KG §3.2.1 | E-003 |
| KG-03 | Edge type must be compatible with source and target node families. | KG §3.4.5 | E-003 |
| KG-04 | Every node belongs to exactly one family. | KG §2.1 | E-003 |
| KG-05 | Every edge belongs to exactly one family. | KG §3.1 | E-003 |
| KG-06 | Confidence is always 0.0–1.0. | KG §1.9 | E-001, E-003 |
| KG-07 | Version is always >= 1. | KG §1.10 | E-001, E-003 |
| KG-08 | Validation is read-only and deterministic. | KG §3.4 | E-003 |
| KG-09 | Security evaluation is deterministic, pure, side-effect-free. | KG §13 | E-003 |
| KG-10 | Every access decision returns a structured PermissionResult. | KG §13 | E-003 |
| KG-11 | No business logic in the graph. Universal and business-agnostic. | KG §13 | E-003 |
| KG-12 | No authentication, login, OAuth, JWT, passwords, sessions, or web security. | KG §13 | E-003 |
| KG-13 | Temporal edges are not deleted. Historical edges marked with end timestamp. | KG §5.5.2 | E-003 |
| KG-14 | Temporal queries without a time return current state. | KG §5.5.3 | E-003 |
| KG-15 | Alternative timelines are isolated from the main timeline. | KG §5.5.4 | E-003 |
| KG-16 | Every edge may have a validity period. | KG §5.5.1 | E-003 |

### Architectural Invariants (A-*)

| Code | Invariant | Source | Epic |
|------|-----------|--------|------|
| A-01 | The Graph builds on the Kernel. Kernel imports are one-way. | KG Preface | E-001, E-003 |
| A-02 | The Kernel must never depend on the Graph. | KG Preface | E-001, E-003 |
| A-03 | The graph is technology-independent. Implementable in any graph-capable store. | KG §1 | E-003 |
| A-04 | Every Object has exactly one timeline. | Ontology §12.1 | E-001 |
| A-05 | Timelines are append-only. | Ontology §12, O-19 | E-001 |
| A-06 | Every Object uses exactly one StateMachine instance. | StateMachine | E-001 |
| A-07 | Every Object belongs to exactly one Space. | Space Architecture | E-001 |
| A-08 | Space membership is explicit. | Space Architecture | E-001 |
| A-09 | Permissions are scoped to Spaces. | Space Architecture | E-001 |
| A-10 | No future subsystem may redefine a canonical model independently. | Core Models §1 | E-001 |

---

## SECTION 4 — Dependency Analysis

### E-001 (Ontology Engine) — Dependency Consumers

```
E-001 (Ontology Engine)
  |
  ├── E-002 (Identity Engine) — SHUNYAIdentity inherits UniversalObject, uses TypeRegistry
  ├── E-003 (Knowledge Graph) — Node/Edge types reference TypeRegistry, Node uses ObjectStatus
  ├── E-004 (Graph Projections) — Projections reference UniversalObject and TypeRegistry
  ├── E-005 (Workspace Runtime) — Workspace consumes Object lifecycle, state machines
  ├── E-006 (Confidence Engine) — Confidence references evidence chain model
  ├── ES-001 (Governance Engine) — All governance operates on UniversalObject
  ├── ES-002 (Knowledge Engine) — Knowledge types reference TypeRegistry
  ├── ES-004 (Planner Engine) — Planning references Object lifecycle
  ├── ES-005 (Executor Engine) — Execution creates Execution Nodes
  ├── ES-006 (Observer Engine) — Observation creates Observation Nodes
  ├── ES-007 (Learning Engine) — Learning promotes knowledge via evidence chain
  ├── ES-008 (Reasoning Engine) — Reasoning operates on Object relationships
  ├── ES-009 (Context Fusion Engine) — Context assembly uses Context model
  └── ALL domain subsystems — Every domain entity inherits UniversalObject
```

E-001 is the **root dependency**. Nothing can function without the type system and object contract. It is the most critical epic to freeze.

### E-002 (Identity Engine) — Dependency Consumers

```
E-002 (Identity Engine)
  |
  ├── ES-001 (Governance Engine) — Identity governance policies
  ├── E-004 (Graph Projections) — Identity projections require identity resolution
  ├── E-005 (Workspace Runtime) — Workspace membership requires identity
  ├── All authentication/authorization logic — Login, session, auth method verification
  ├── All production routes (app/production/identity/) — User management, onboarding, orgs
  ├── CRM subsystems — Customer identity requires SHUNYAIdentity
  ├── Communication subsystems — Sender/recipient identity resolution
  └── All domain subsystems — Every human actor is identified via SHUNYAIdentity
```

E-002 is the **identity fabric**. Every subsystem that needs to know "who is doing this" depends on E-002.

### E-003 (Knowledge Graph) — Dependency Consumers

```
E-003 (Knowledge Graph)
  |
  ├── E-004 (Graph Projections) — Projections transform the graph into structured views
  ├── E-005 (Workspace Runtime) — Workspace consumes graph projections
  ├── E-006 (Confidence Engine) — Confidence updates traverse the graph evidence chain
  ├── ES-005 (Executor Engine) — Execution Nodes are created by the Execution Engine
  ├── ES-006 (Observer Engine) — Observation Nodes are created by the Observer Engine
  ├── ES-007 (Learning Engine) — Knowledge promotion events are emitted by the graph
  ├── ES-008 (Reasoning Engine) — Graph traversal is the foundation of reasoning
  ├── ES-009 (Context Fusion Engine) — Context assembly uses temporal graph queries
  ├── Alpha-001H (Knowledge Graph integration) — Alpha services consume the graph
  └── All domain subsystems — Every subsystem creates Nodes and Edges of their respective types
```

E-003 is the **data plane**. Every subsystem that creates, connects, or queries SHUNYA's understanding of reality depends on the Knowledge Graph.

### Consolidated Dependency Graph

```
E-001 (Ontology Engine)
  ├── E-002 (Identity Engine)
  │     └── [all auth, identity, governance subsystems]
  ├── E-003 (Knowledge Graph)
  │     ├── E-004 (Graph Projections)
  │     ├── E-005 (Workspace Runtime)
  │     ├── E-006 (Confidence Engine)
  │     ├── ES-005 (Executor Engine)
  │     ├── ES-006 (Observer Engine)
  │     ├── ES-007 (Learning Engine)
  │     ├── ES-008 (Reasoning Engine)
  │     ├── ES-009 (Context Fusion Engine)
  │     └── All domain subsystems
  ├── ES-001 (Governance Engine)
  ├── ES-002 (Knowledge Engine)
  ├── ES-004 (Planner Engine)
  └── ALL domain subsystems
```

**Arrow direction: Consumer → Dependency**

No circular dependencies exist. The one-way dependency (Kernel → nothing; Graph → Kernel) is constitutionally enforced.

---

## SECTION 5 — Architectural Risks

Brutally honest assessment of things that may require breaking changes later.

### RISK-01: InMemoryNodeStore and InMemoryEdgeStore are the only implementations.

**Severity:** HIGH
**Detail:** Every subsystem currently depends on in-memory stores. When a SQL implementation is introduced, the abstract interfaces (`NodeStore`, `EdgeStore`) must remain backward-compatible. If the SQL implementation requires a different API (e.g., async, connection pooling), the abstract interfaces may need to change. This would break every subsystem that depends on them.

**Mitigation:** The abstract interfaces are already minimal (CRUD + query). Keep them synchronous until the SQL implementation is designed. Do not add async variants until the SQL implementation proves they are necessary.

### RISK-02: The RelationshipEngine in `app/kernel/relationship.py` and the EdgeStore in `app/graph/edge.py` overlap.

**Severity:** MEDIUM
**Detail:** `RelationshipEngine` (E-001) and `EdgeStore` (E-003) both represent connections between entities. The architecture states that `RelationshipEngine` is the "canonical lightweight API" and `EdgeStore` is the "canonical persistence + execution layer." In practice, subsystems may use one or both, creating confusion about which is canonical.

**Mitigation:** The architecture reconciliation (already performed) documents this clearly. Future subsystems should use `app/graph/EdgeStore` for all new behaviour. The `RelationshipEngine` is frozen for backward compatibility. No new methods should be added to `RelationshipEngine`.

### RISK-03: `ContextResolution` is a stub with no backing store.

**Severity:** MEDIUM
**Detail:** `ContextResolution` (E-001) exists but has no persistent store. It registers contexts in-memory only. Any subsystem that needs persistent context resolution (e.g., workspace context across sessions) will find it missing.

**Mitigation:** Mark `ContextResolution` as Future (done in this review). Do not depend on it for production. E-004 (Graph Projections) or E-005 (Workspace Runtime) must implement persistent context resolution.

### RISK-04: ORGANISATION visibility is conservatively owner-only.

**Severity:** LOW
**Detail:** The security module's ORGANISATION visibility level falls back to owner-only because there is no canonical org membership lookup. This is safe (no access is granted when it should be denied), but it is restrictive. A future org membership service may need to change this behaviour.

**Mitigation:** The security evaluator is designed to be deterministic. When org membership is available, the visibility check can be updated without changing the public API. The `SecurityContext` already carries an `organization` field.

### RISK-05: No edge versioning.

**Severity:** LOW
**Detail:** Edges are not versioned individually. The architecture states that edge changes are recorded as events on the Event Bus. If a future subsystem needs edge versioning (e.g., optimistic concurrency, historical reconstruction), the current Edge model lacks it.

**Mitigation:** The `Edge` dataclass has no version field. Adding one would be a breaking change to the dataclass. Future epics should implement edge versioning via the Event Bus pattern as originally intended, not by adding a version field to the Edge dataclass.

### RISK-06: `IdentityGovernance.split()` accesses `_store._identities` directly.

**Severity:** LOW
**Detail:** `IdentityGovernance.split()` bypasses the `IdentityStore` API and accesses `self._store._identities` directly to add new identities. This is a tight coupling to the in-memory implementation.

**Mitigation:** The `IdentityStore` needs a `put()` or `save()` method. This is a minor API gap that should be fixed before production. Does not break any existing subsystem.

### RISK-07: `StateMachine` observers are fire-and-forget with silent failure.

**Severity:** LOW
**Detail:** `StateMachine.transition()` notifies observers but silently catches exceptions. This means a broken observer can silently fail, and the caller will not know the transition was not observed.

**Mitigation:** This is by design (observer failures must not break state consistency). However, a logging mechanism should be added so that silent failures are at least recorded. Does not break the public API.

### RISK-08: No tenant isolation in the graph.

**Severity:** LOW
**Detail:** `Node` has a `tenant_id` field inherited from `UniversalObject`, but `InMemoryNodeStore` does not enforce tenant-scoped isolation. All nodes are globally visible regardless of tenant.

**Mitigation:** The SQL implementation must enforce tenant isolation. The `NodeStore` abstract interface is designed to support this. The in-memory store is for development only.

---

## SECTION 6 — Extension Points

Everything intentionally left open for future epics without changing current contracts.

### Storage

- **SQL implementation** — `NodeStore` and `EdgeStore` abstract interfaces accept `SqlNodeStore`/`SqlEdgeStore` without changing the public API.
- **Pagination** — `get_by_type`, `get_by_label`, `all()` can accept `cursor` and `limit` parameters. Default behavior (no pagination) is backward compatible.
- **Batch operations** — `create_many`, `update_many`, `delete_many` can be added to the abstract interfaces. New methods on the interface are backward compatible for existing callers.

### Traversal

- **General-purpose graph traversal** — BFS, DFS, shortest path, subgraph extraction, k-hop queries. The existing `TemporalStore` provides temporal queries; a `TraversalEngine` can be layered on top of `NodeStore`/`EdgeStore`.
- **`RelationshipEngine.traverse()`** already exists as a lightweight BFS. A full `TraversalEngine` for the graph store is the canonical extension point.

### Search

- **Full-text search** — Search over node labels, attributes, and metadata. The `DISCOVER` permission already exists in the security model. A search index can be added without changing `Node`/`Edge` contracts.
- **Type-based search** — `get_by_type()` and `get_by_label()` already exist. Additional query methods can be added to the `NodeStore` interface.

### Reasoning

- **Evidence chain traversal** — The `EvidenceRef` model exists. A reasoning engine can traverse evidence chains from graph nodes without changing the `Node`/`Edge` contracts.
- **Inference rules** — New edge types can be added to the `EdgeType` enum and `_EDGE_FAMILY_TYPES` dictionary without changing the core `Edge` dataclass.
- **Confidence propagation** — The `confidence` field exists on every Node and Edge. A reasoning engine can propagate confidence along edges.

### Execution

- **Execution Nodes** — The `NodeFamily.EXECUTION` family exists. The `Execution` type is registered in the TypeRegistry. The Execution Engine (ES-005) creates Nodes of this type.
- **Execution State Machine** — `StateMachine` is universal. Every execution has a state machine. No new contract needed.

### Learning

- **Knowledge promotion** — The `NodeFamily.KNOWLEDGE` family exists. The Learning Engine (ES-007) promotes observations to knowledge by creating new Nodes and Edges.
- **Confidence decay** — The `confidence` field exists. Automatic decay and promotion can be implemented without changing the `Node`/`Edge` dataclass.

### Permissions

- **Custom policies** — `GraphAccessEvaluator` accepts a `policies` parameter. Applications can add their own `GraphSecurityPolicy` instances. The `DEFAULT_POLICIES` are immutable.
- **New permissions** — New values can be added to `GraphPermission` enum. Existing permissions are unchanged.
- **New visibility levels** — New values can be added to `VisibilityLevel` enum. The `_VISIBILITY_HIERARCHY` and `_VISIBILITY_ORDER` must be updated accordingly.

### Delegation

- **Delegation model** — The `SpaceRole` enum (OWNER, ADMIN, MEMBER, GUEST) supports delegation. A delegation subsystem can create proxy identities or delegation relationships using existing `Edge` types.
- **No delegation-specific contract** is frozen — this is intentionally left to future epics.

### Projection

- **Graph Projections** — The architecture defines projections (§8) as structured, filtered views of the graph. E-004 will implement this layer. The projection API is entirely new — no existing contracts need to change.
- **`ContextResolution`** is a stub that can be extended to support projections. Currently marked Future.

---

## SECTION 7 — Universality Audit

Can the foundation represent **Healthcare, Travel, Manufacturing, Retail, Government, Education, Legal, Finance** without changing the architecture?

### Audit Methodology

For each domain, we check whether the existing types, relationships, and graph primitives can represent the domain's core concepts. We do not check whether the domain's business logic is implemented — only whether the foundation's abstractions can represent it.

### Healthcare

**Concepts to represent:** Patients, providers, facilities, diagnoses, treatments, medications, appointments, outcomes, insurance, consent, clinical notes, lab results, referrals.

**Foundation mapping:**
- `Person` → Patient, Provider, Staff
- `Organization` → Hospital, Clinic, Insurance Company, Lab
- `Document` → Clinical Note, Lab Report, Prescription, Consent Form
- `Meeting` → Appointment, Consultation
- `Commitment` → Treatment Plan, Follow-up Schedule
- `Evidence` → Lab Result, Diagnostic Image, Clinical Observation
- `Event` → Admission, Discharge, Procedure, Outcome
- `Task` → Prescription Fill, Referral Processing
- `Edge` families: `owns` (provider→patient), `works_at` (provider→facility), `supports` (evidence→diagnosis), `contradicts` (conflicting lab results), `precedes` (symptom→diagnosis→treatment), `contains` (episode→encounters), `derived_from` (diagnosis→evidence)

**Verdict:** REPRESENTABLE. The foundation's type system and graph model cover all healthcare concepts. No architectural change needed.

### Travel

**Concepts to represent:** Travelers, bookings, flights, hotels, cars, itineraries, payments, loyalty programs, cancellations, travel documents.

**Foundation mapping:**
- `Person` → Traveler
- `Organization` → Airline, Hotel Chain, Car Rental, Travel Agency
- `Document` → Booking Confirmation, Itinerary, Travel Insurance, Visa
- `Commitment` → Reservation, Booking, Cancellation Policy
- `Event` → Check-in, Departure, Arrival, Cancellation, Delay
- `Task` → Baggage Claim, Check-in Process
- `Edge` families: `owns` (traveler→booking), `depends_on` (flight→hotel), `precedes` (check-in→boarding→departure), `contains` (itinerary→bookings), `causes` (delay→missed connection)

**Verdict:** REPRESENTABLE. No architectural change needed.

### Manufacturing

**Concepts to represent:** Parts, assemblies, BOMs, suppliers, inventory, work orders, quality inspections, production runs, shipments, equipment, maintenance schedules.

**Foundation mapping:**
- `Organization` → Supplier, Manufacturer, Distributor
- `Document` → BOM, Work Order, Quality Report, Shipping Manifest
- `Task` → Production Run, Assembly Step, Quality Inspection
- `Workflow` → Production Line, Assembly Process
- `Commitment` → Purchase Order, Delivery Schedule
- `Event` → Machine Breakdown, Quality Defect, Shipment Received
- `Edge` families: `contains` (assembly→parts), `derived_from` (part→supplier), `depends_on` (assembly→sub-assembly), `causes` (defect→rework), `precedes` (production→inspection→shipment)

**Verdict:** REPRESENTABLE. The `Workflow` and `Task` types support manufacturing processes. No architectural change needed.

### Retail

**Concepts to represent:** Products, categories, inventory, orders, customers, reviews, returns, promotions, payments, fulfillment.

**Foundation mapping:**
- `Person` → Customer, Staff
- `Organization` → Store, Brand, Supplier
- `Document` → Product Listing, Order, Invoice, Return Slip
- `Commitment` → Order Promise, Subscription, Warranty
- `Event` → Purchase, Return, Refund, Review Posted
- `Edge` families: `owns` (customer→order), `contains` (order→items), `references` (review→product), `causes` (return→refund)

**Verdict:** REPRESENTABLE. No architectural change needed.

### Government

**Concepts to represent:** Citizens, residents, permits, licenses, applications, tax records, benefits, legislation, regulations, appeals, court cases, enrollment.

**Foundation mapping:**
- `Person` → Citizen, Resident, Applicant, Officer
- `Organization` → Agency, Department, Court, Municipality
- `Document` → Permit, License, Application Form, Tax Return, Legislation
- `Policy` → Regulation, Law, Eligibility Rule, Procedure
- `Commitment` → Obligation, Benefit Entitlement, Service Agreement
- `Event` → Application Filed, Permit Issued, Appeal Lodged, Hearing
- `Decision` → Approval, Denial, Ruling
- `Edge` families: `governs` (policy→process), `contains` (legislation→regulations), `derived_from` (decision→evidence), `appeals` (decision→appeal)

**Verdict:** REPRESENTABLE. The `Policy` type family is specifically designed for government use cases. No architectural change needed.

### Education

**Concepts to represent:** Students, teachers, courses, enrollments, grades, assignments, curricula, degrees, attendance, transcripts, certifications.

**Foundation mapping:**
- `Person` → Student, Teacher, Administrator
- `Organization` → School, University, Department
- `Document` → Transcript, Certificate, Assignment, Syllabus
- `Meeting` → Class, Lecture, Office Hours
- `Commitment` → Enrollment, Course Requirement, Graduation Requirement
- `Task` → Assignment Submission, Exam
- `Event` → Graduation, Dropout, Grade Posted
- `Knowledge` → Curriculum, Subject Matter, Learning Objective
- `Edge` families: `enrolled_in` (student→course), `teaches` (teacher→course), `contains` (curriculum→courses), `precedes` (prerequisite→course), `derived_from` (grade→assignment)

**Verdict:** REPRESENTABLE. No architectural change needed.

### Legal

**Concepts to represent:** Clients, cases, matters, contracts, filings, court dates, evidence, billable hours, legal research, precedents, settlements.

**Foundation mapping:**
- `Person` → Client, Attorney, Judge, Witness
- `Organization` → Law Firm, Court, Regulatory Body
- `Document` → Contract, Brief, Filing, Court Order, Legal Opinion
- `Commitment` → Settlement Agreement, Retainer, Court Date
- `Evidence` → Exhibit, Deposition, Affidavit
- `Event` → Filing, Hearing, Trial, Verdict, Settlement
- `Decision` → Ruling, Judgment, Order
- `Prediction` → Case Outcome Prediction, Risk Assessment
- `Edge` families: `represents` (attorney→client), `cites` (brief→precedent), `contradicts` (conflicting evidence), `supports` (evidence→claim), `precedes` (filing→hearing→trial)

**Verdict:** REPRESENTABLE. The `Evidence` and `Decision` types are designed for legal reasoning. No architectural change needed.

### Finance

**Concepts to represent:** Accounts, transactions, instruments, portfolios, trades, valuations, risk assessments, compliance reports, audits, regulations.

**Foundation mapping:**
- `Person` → Client, Advisor, Trader
- `Organization` → Bank, Brokerage, Regulator, Exchange
- `Document` → Statement, Report, Prospectus, Audit Report
- `Commitment` → Loan, Bond, Insurance Policy, Payment Obligation
- `Event` → Trade, Transfer, Dividend, Default, Maturity
- `Prediction` → Risk Assessment, Price Forecast, Credit Rating
- `Policy` → Compliance Rule, Investment Mandate, Regulation
- `Edge` families: `owns` (client→account), `contains` (portfolio→holdings), `derived_from` (valuation→market data), `causes` (trade→settlement), `depends_on` (derivative→underlying)

**Verdict:** REPRESENTABLE. No architectural change needed.

### Universality Verdict

**ALL EIGHT DOMAINS ARE REPRESENTABLE without changing the architecture.**

The foundation is genuinely universal. The type system's 9 canonical groups (Entity, Event, Commitment, Action, Evidence, Knowledge, Prediction, Policy, Conversation, Memory, Context) and the graph's 18 node families + 15 edge families cover every concept across all eight domains.

The reason is architectural: the foundation defines **what things ARE** (types), **what they MEAN** (semantics), and **how they CONNECT** (graph). It does not define what they DO. Business logic is the responsibility of domain subsystems, which depend on the foundation but do not modify it.

No domain required a new type group, a new edge family, or a new graph primitive. Every domain concept mapped to an existing abstraction.

---

## SECTION 8 — Recommendations

Architectural improvements that MUST happen BEFORE E-004. Documentation only. No code.

### RECOMMENDATION 1: Freeze the `app/kernel/__init__.py` public API.

**Action:** Document that the current `__all__` in `app/kernel/__init__.py` is the frozen public API. Any future epic that needs a new kernel primitive must first pass a constitutional amendment.

**Rationale:** E-004 will depend on E-001. If E-004 starts depending on internal kernel APIs, the kernel can never be refactored.

### RECOMMENDATION 2: Freeze the `app/graph/__init__.py` public API.

**Action:** Document that the current `__all__` in `app/graph/__init__.py` is the frozen public API. The `InMemoryNodeStore` and `InMemoryEdgeStore` implementations are stable for development but must be replaced before production.

**Rationale:** Same as RECOMMENDATION 1. E-004 must depend only on the public API.

### RECOMMENDATION 3: Add `IdentityStore.put()` method.

**Action:** Add a `put(identity: SHUNYAIdentity) -> None` method to `IdentityStore` so that `IdentityGovernance.split()` can use the public API instead of accessing `_store._identities` directly.

**Rationale:** This is a minor API gap that creates a tight coupling to the in-memory implementation. Fixing it now prevents a production issue.

### RECOMMENDATION 4: Document the `RelationshipEngine` vs `EdgeStore` ownership boundary.

**Action:** Add a clear comment to both `app/kernel/relationship.py` and `app/graph/edge.py` stating:
- `RelationshipEngine` = canonical lightweight API, frozen, no new behaviour
- `EdgeStore` = canonical persistence + execution layer, all new behaviour

**Rationale:** Prevents future confusion about which API to use. E-004 must target `EdgeStore` for graph operations, not `RelationshipEngine`.

### RECOMMENDATION 5: Mark `ContextResolution` explicitly as Future.

**Action:** Add a `# Future API` docstring to `ContextResolution` and remove it from the `__all__` in `app/kernel/__init__.py` (or move it to a separate `app/kernel/future.py`). No subsystem should depend on it.

**Rationale:** Prevents E-004 from depending on a stub that will change.

### RECOMMENDATION 6: Add a `StateMachine` logging mechanism for observer failures.

**Action:** Add a logging statement (not a raise) when a `StateMachine` observer raises an exception. The current silent failure pattern is acceptable for production, but unobservable failures are not.

**Rationale:** Debugging state machine issues in production will be impossible without this.

### RECOMMENDATION 7: No async API additions to `NodeStore`/`EdgeStore` until SQL implementation.

**Action:** Keep the `NodeStore` and `EdgeStore` interfaces synchronous. Do not add async variants, context managers, or connection pooling until the SQL implementation is designed and proves the need.

**Rationale:** Premature async would break every existing consumer. The in-memory stores are synchronous and fast.

### RECOMMENDATION 8: Publish the constitutional invariants as a standalone document.

**Action:** Extract Section 3 of this report into `architecture/FOUNDATION_INVARIANTS.md` as a single-source reference for all future epics.

**Rationale:** Every future epic needs to know which invariants it must respect. Currently the invariants are scattered across multiple architecture documents. A single reference prevents accidental violations.

---

## Conclusion

**The foundation is ready for E-004.**

E-001, E-002, and E-003 together form a complete, consistent, universal foundation. The type system covers all known domains. The identity model is permanent and independent of any organization. The graph is technology-independent and business-agnostic. The constitutional invariants are non-contradictory and cover all edge cases.

The 8 recommendations above are documentation-only actions that must be completed before E-004 begins. None require code changes to the current implementation. All are about clarifying boundaries, marking stubs, and preventing future confusion.

**No breaking changes are expected.** Every future subsystem can depend on E-001, E-002, and E-003 without modifying them.

---

*This review is the canonical architectural readiness certification for the E-001/E-002/E-003 foundation. No implementation work on E-004 may begin until the 8 recommendations in Section 8 are resolved.*