# Knowledge Engine — Engineering Summary

**Engine:** Knowledge Engine (ES-002)
**Layer:** Knowledge
**Phase:** Phase 2 (Knowledge Layer)
**Status:** Draft specification

---

## One-Page Summary

### What It Is

The Knowledge Engine is the single source of truth for all facts within SHUNYA. It stores, versions, retrieves, and validates every piece of knowledge — from destination weather data to customer preferences, from business policies to learned insights — with the fundamental guarantee that **no fact is ever silently overwritten**. Every mutation creates a new version. Every version is permanently traceable. Every retrieval includes a confidence score and an evidence chain.

### Why It Exists

The SHUNYA Constitution requires immutable knowledge. Mutable memory (in-place updates) breaks traceability — a decision traced to a fact that no longer exists is an untraceable decision. The Knowledge Engine is the implementation of constitutional principles 6.4 (Immutable Knowledge) and 6.5 (Explainable Decisions). It ensures that every fact has a complete, verifiable history from observation to verification to trust to supersession to archival.

### What It Does

The Knowledge Engine is the intersection point of the Compounding Intelligence Loop:

```
Observer → [Knowledge Engine] ← Learning
              ↓            ↑
         Reasoning      Context Fusion
              ↓
         Planner → Governance
```

**Inputs:** Observations from the Observer Layer, learning signals from the Learning Layer, human corrections, document extractions, external API syncs, and conversation events.

**Outputs:** Fact retrieval with confidence scores, evidence chains with provenance, workspace context packages, relationship graphs, and historical timelines.

### State Lifecycle

Every fact progresses through a deterministic lifecycle:

```
Unknown → Observed → Verified → Trusted → Superseded → Archived → Retired
```

With a `Conflict` state when contradictory facts are detected. Facts enter at `Observed` (from automated sources) or `Verified` (from human assertions). They reach `Trusted` only after independent verification from multiple sources. They are superseded when a newer version is created, archived when they expire, and retired when their retention period ends.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage model | SQLAlchemy + PostgreSQL `knowledge_facts` table | Leverages existing stack; no new infrastructure |
| Versioning | Monotonically increasing integer per fact key | Simple, deterministic, stable ordering |
| State machine | 8 states with 14 transitions | Covers full fact lifecycle from observation to retirement |
| Integrity | SHA-256 checksums on every version | Tamper-evident storage; verifiable by downstream consumers |
| Retrieval | Structured (primary) + Semantic (future) | Structured queries work today; semantic search is an extension point |
| Tenant isolation | Every fact scoped to tenant_id | Prevents cross-tenant contamination by design |
| Right to forget | Supersession with anonymization, not deletion | Preserves audit trail while honoring privacy requirements |

### Current Implementation vs Specification

| Aspect | Current (`knowledge.py` + `knowledge_store.py`) | Specification Target |
|--------|--------------------------------------------------|---------------------|
| Fact storage | Both implementations exist but `knowledge_store.py` is not wired | Single unified Immutable Knowledge Store |
| Knowledge base | Markdown file (`data/knowledge-base.md`) parsed at startup | Facts seeded from markdown, stored in the IKS |
| State machine | None (facts are written and read; no lifecycle tracking) | Full 8-state lifecycle with transitions |
| Versioning | Implemented in `knowledge_store.py` | Same model, wired into the pipeline |
| Checksums | Implemented in `knowledge_store.py` | Same model, verified on every read |
| Semantic search | Not implemented | Extension point — pluggable provider interface |
| Tenant isolation | `tenant_id` column exists on `KnowledgeFact` | Enforced at query level |
| Integration with pipeline | `KnowledgeLayer` is wired; `ImmutableKnowledgeStore` is not | Both unified and wired into all downstream consumers |

### Architectural Position in the Pipeline

```
Current:
  Inquiry → KnowledgeLayer (markdown KB) → Reasoning → Planner → Workflow

Target:
  Observation → [Knowledge Engine] ← Learning
     ↓                                    ↓
  Reasoning ← Evidence Chain     Learned Facts
     ↓
  Planner ← Destination/Supplier Data
     ↓
  Governance ← Policy Definitions
```

---

## Open Architectural Questions

1. **How should the existing KnowledgeLayer (markdown KB parser) and ImmutableKnowledgeStore (versioned DB) be unified?** Two implementations exist. The KnowledgeLayer is wired into the pipeline but reads from a markdown file. The ImmutableKnowledgeStore has the correct data model but is not wired. Options: (a) replace KnowledgeLayer entirely with calls to IKS, (b) seed the IKS from the markdown file and have KnowledgeLayer query IKS instead of parsing the file, or (c) keep both with the IKS as the authoritative store and the markdown file as a seed source. This is an **Engineering ADR** candidate.

2. **When should semantic/vector search be introduced?** The specification defines semantic retrieval as an extension point but does not mandate it. The current keyword-based search works for small knowledge bases (tens of destinations). At what scale does keyword search become insufficient? The architecture document references pgvector but no implementation exists. Recommendation: implement structured retrieval first, add semantic retrieval as a performance optimization when knowledge base exceeds 10,000 facts or when search recall becomes a user-facing issue.

3. **What is the fact conflict resolution workflow?** The specification defines what happens when a conflict is detected (both facts are flagged, human review is required) but not the human review interface or workflow. Does this use the existing notification system, a new review queue, or the Phase 17 Continuous Surface? This depends on the Phase 17 timeline.

4. **Should the state machine be implemented in the database (SQL triggers/constraints) or in the application layer?** Application-layer state machines are more flexible and testable. Database-layer enforcement is more robust against concurrent access. Recommendation: application layer for flexibility, with database-level unique constraints on (fact_key, version) to prevent duplicate versions.

5. **What is the retention policy for retired facts?** The specification requires configurable retention policies but does not define defaults. Recommendation: 90 days for Retired state before physical deletion (with tombstone). This is a Phase 4 (Privacy) policy decision.

---

## Assumptions Made

| Assumption | Detail | Validated? | Assumed Until |
|------------|--------|-----------|---------------|
| All facts fit in a single PostgreSQL table | No sharding or partitioning required | No | Fact count exceeds 10M or write throughput exceeds 500/s |
| SHA-256 checksums are sufficient for integrity | No hardware-level attestation or TPM | Yes | Standard practice for content integrity |
| Temporal validity is linear (one valid_from per fact) | No overlapping validity periods | No | First requirement for overlapping validities |
| Conflict detection is post-write (not pre-write) | Contradictions are detected after both facts are stored | No | First requirement for pre-write conflict prevention |
| The Knowledge Engine is read-heavy | Reads significantly outnumber writes | No | Production traffic analysis |
| Single-region deployment | No geo-distribution or active-active replication | No | Multi-region requirement |
| PostgreSQL `knowledge_facts` table is append-only | No UPDATE, no DELETE for fact values | No | First schema migration |
| Fact keys are human-readable strings | Not UUIDs or hashed identifiers | Yes | Current convention in knowledge.py |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Storage growth exceeds projections** | Medium | Medium | Version archival after 90 days; retention policies per domain |
| **Fact conflict rate is high** | Medium | Medium | Automated conflict detection with clear resolution workflow; reduce by improving source reliability scoring |
| **Write throughput bottleneck** | Low | High | Batch writes, async checksum computation, connection pooling |
| **Cross-tenant contamination via query error** | Low | Critical | Every query explicitly scoped to tenant_id; integration tests verify isolation |
| **Unification of KnowledgeLayer and IKS introduces regressions** | Medium | High | Comprehensive test suite for all existing KnowledgeLayer functionality |
| **Semantic search introduces unacceptable latency** | Medium | Medium | Separate read path for semantic vs structured; structured is always available |
| **Fact key namespace collision** | Low | Medium | Domain-prefixed keys (e.g., "destination.bali.visa"); domain registry prevents cross-domain collisions |
| **Retired fact restoration is impossible** | Low | Medium | Tombstone records enable identification of what was deleted; re-import from source |

---

## Dependencies

| Dependency | Type | Status | Required By |
|------------|------|--------|-------------|
| PostgreSQL `knowledge_facts` table | Database migration | Not yet created | Implementation phase |
| ImmutableKnowledgeStore integration | Code | `knowledge_store.py` exists but not wired | Implementation phase |
| KnowledgeLayer replacement | Code | `knowledge.py` exists, must be replaced | Implementation phase |
| Fact state machine | Implementation | Not yet implemented | Implementation phase |
| Temporal query support | Implementation | Not yet implemented | Implementation phase |
| Conflict detection | Implementation | Not yet implemented | Implementation phase |
| Semantic search extension point | Interface definition | Not yet implemented | Future phase |
| Phase 4 (Privacy) eligibility gates | Integration | Computation-only | Future integration |
| Phase 7 (Evidence) source references | Integration | Models exist | Implementation phase |
| Phase 10 (Context Fusion) integration | Integration | Computation-only | Future integration |
| Phase 11 (Knowledge Resolution) migration | Integration | Computation-only | Implementation phase |

---

**End of Engineering Summary**