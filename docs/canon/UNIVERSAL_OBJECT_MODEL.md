# SHUNYA Universal Object Model Specification

> **Phase L · Canonical Document**
> **Status: CANONICAL — All business entities shall conform to this model.**

---

## 1. Universal Object Contract

Every business entity inside SHUNYA exists as one universal object. No runtime may create a parallel object representation without explicit documentation as an adapter.

```
UniversalObject {
    identity:        ObjectIdentity       (permanent, unique, never reused)
    type:            ObjectType            (from Universal Type System, immutable)
    name:            string                (human-readable label)
    status:          ObjectStatus          (lifecycle state)
    confidence:      float                 (0.0–1.0)
    attributes:      dict                  (type-specific key-value pairs)
    relationships:   List[Relationship]    (typed, bidirectional)
    evidence:        List[EvidenceRef]     (immutable provenance chain)
    timeline:        List[TimelineEvent]   (append-only chronological record)
    commitments:     List[CommitmentRef]   (active promises involving this object)
    memory:          List[MemoryRef]       (cross-layer memory references)
    projections:     List[ProjectionRef]   (computed views — not stored on object)
    metadata: {
        created_at, updated_at, created_by, updated_by,
        provenance, version, source
    }
}
```

## 2. Object Identity

| Field | Rule |
|-------|------|
| `object_id` | Assigned at creation. Never changes. Never reused. |
| Format | `obj_<timestamp_ms><hex_random>` (e.g. `obj_1721800000000a1b2c3d4`) |
| Resolution | Via Identity Runtime — O(1) lookup by object_id |

## 3. Type System

Types are defined in the kernel TypeRegistry. Every object has exactly one type, assigned at creation, immutable for life.

| Type Group | Examples | Lifecycle |
|-----------|----------|-----------|
| Entity | Person, Organization, Project, Document | CREATE → ACTIVE → ARCHIVED |
| Event | Meeting, Conversation, Observation | CREATE → COMPLETED |
| Commitment | Task, Agreement, Promise | CREATE → ACTIVE → RESOLVED |
| Knowledge | Insight, Pattern, Policy | CREATE → ACTIVE → SUPERSEDED |

## 4. Convergence: Object Migration

All current object representations converge onto UniversalObject in priority order:

| Priority | Current Model | Module | Migration Strategy |
|----------|--------------|--------|-------------------|
| P0 | FounderObject | `app.founder.models` | Add adapter in `app/founder/adapters.py` that reads/writes kernel UniversalObject |
| P0 | UniversalObject (kernel) | `core.kernel.object` | Authoritative — no migration needed |
| P0 | Node (graph) | `app.graph.node` | Wrap with UniversalObject in `core/memory_knowledge_runtime/` |
| P1 | MemoryObject | `core.memory_knowledge_runtime` | Add adapter to UniversalObject schema |
| P1 | Lead | `app.models` | Add kernel-backed adapter, deprecate Flask model |
| P2 | Task, Payment, Invoice, Document | `app.models` | Add kernel-backed adapters |