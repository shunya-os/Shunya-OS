# PHASE_L_IMPLEMENTATION_PLAN.md

**Governance Directive:** G11.0 — Phase L Authorization
**Engine:** Knowledge Engine (ES-002)
**Layer:** Knowledge

---

## 1. Objectives

1. Implement canonical Knowledge Engine data models (ES-002 §4–5, §14)
2. Implement immutable, versioned knowledge store (append-only, SHA-256 checksums)
3. Implement 8-state fact lifecycle with 14 transitions (ES-002 §6)
4. Implement conflict detection (contradictory facts)
5. Implement evidence chain construction
6. Implement temporal queries (get_at_time, get_history)
7. Implement structured retrieval (by key, domain, category, search)
8. Implement backward-compatible legacy wrapper
9. Comprehensive verification: architecture contracts, invariants, system contracts, pipeline, replay, lifecycle, traceability

## 2. Scope Boundaries

| In Scope | Out of Scope |
|----------|-------------|
| Immutable versioned fact store (in-memory) | PostgreSQL `knowledge_facts` table (deferred) |
| SHA-256 checksum on every version | Semantic/vector search (pgvector deferred) |
| 8-state lifecycle with 14 transitions | Event Bus integration |
| Conflict detection | Relationship traversal beyond evidence chains |
| Evidence chain construction | Batch operations for bulk ingestion |
| Temporal queries (get_at_time, get_history) | Right-to-forget (anonymization deferred) |
| Structured retrieval (key, domain, category, search) | Real-time streaming guarantees |
| Legacy backward compatibility | Knowledge seeding from markdown files |

## 3. ES-002 Requirement Mapping

| § | Requirement | Implementation |
|---|-------------|---------------|
| §1 | Immutable knowledge store | `ImmutableKnowledgeStore` with append-only versions |
| §2 | 10 in-scope capabilities | Models, retrieval, versioning, checksum, lifecycle, conflict, tenant isolation |
| §4 | Input contract | `KnowledgeInput` with 16 fields, validation |
| §5 | Output: RetrievalResult, SearchResult, EvidenceChain | 3 output types |
| §6 | 8-state lifecycle, 14 transitions | `FactState` enum, `_transition()` method, state machine |
| §14 | 12 knowledge categories | `KnowledgeCategory` enum |
| §15 | Versioning, conflict, temporal validity | Monotonic versioning, conflict detection, valid_from/valid_until |
| §16 | Structured retrieval, temporal retrieval | `get()`, `get_by_domain()`, `search()`, `get_at_time()`, `get_history()` |

## 4. Engine Boundary Matrix

| Engine | Allowed Reads | Allowed Writes | Forbidden Imports |
|--------|-------------|-------------|------------------|
| Knowledge (L) | Own fact store, own patterns | Own fact store | reasoning, planner, executor, governance, observer, learning |

## 5. System Contracts (G11.0)

| # | Contract | Verification |
|---|----------|-------------|
| 1 | No information disappears through pipeline | Pipeline end-to-end test |
| 2 | Every object preserves provenance | `source`, `evidence`, `created_by` on all facts |
| 3 | Every identifier remains stable | `fact_key` immutable, version monotonic |
| 4 | Every recommendation traces to observations | (Covered by Phase K traceability) |
| 5 | Every knowledge proposal traces to learning signals | `source_signal_ids` on proposals |
| 6 | Every governance decision traces to planner outputs | (Covered by Phase H) |
| 7 | Every execution traces to approved governance | (Covered by Phase I) |
| 8 | Every observation traces to execution evidence | `evidence` field on facts |
| 9 | Every learning result traces to observations | `source_signal_ids` on patterns/recommendations |
| 10 | Every state transition is auditable | `created_at`, `superseded_at` on all versions |

## 6. Lifecycle Audit (ES-002 §6)

| State | Terminal | Allowed Transitions | Forbidden Transitions |
|-------|----------|-------------------|---------------------|
| Unknown | Initial | → Observed | → Verified, Trusted, Superseded, Archived, Retired |
| Observed | No | → Verified, Retired, Conflict | → Trusted (direct), Superseded (direct) |
| Verified | No | → Trusted, Conflict, Superseded, Retired | → Observed |
| Trusted | No | → Superseded, Archived, Retired | → Observed, Verified |
| Superseded | No | → Archived, Trusted (restored) | → Observed, Verified |
| Conflict | Stable | → Trusted, Superseded | → Observed, Verified |
| Archived | No | → Retired | → Trusted, Superseded |
| Retired | Yes | — | Any |

## 7. Testing Strategy

1. **Model tests** (~15): Fact, version, retrieval, evidence chain, state machine
2. **Lifecycle tests** (~14): One per state transition
3. **Conflict detection tests** (~3): Store, detect, flag
4. **Evidence chain tests** (~3): Construction, integrity, missing evidence
5. **Temporal query tests** (~4): get_at_time, get_history, version ordering
6. **Architecture contract tests** (~6): Forbidden imports, eval/exec, engine isolation
7. **Architectural invariant tests** (~6): Immutability, provenance, tenant isolation
8. **System contract tests** (~5): Object integrity, provenance, identifier stability
9. **Pipeline verification tests** (~3): End-to-end object flow through lifecycle
10. **Replay verification tests** (~2): Identical inputs → identical outputs
11. **Determinism tests** (~2): Same store operations produce same state
12. **Backward compatibility tests** (~2): Legacy API

---

**Ready for implementation.**