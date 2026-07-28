# PHASE_M_IMPLEMENTATION_PLAN.md

**Governance Directive:** G12.0 — Phase M Authorization
**Engine:** Context Fusion Engine (ES-009)

---

## 1. Objectives

1. Create canonical `context_fusion_engine` package wrapping existing `app/shunya/context/`
2. Implement snapshot consistency (workspace context immutability, fingerprint identity)
3. Implement replay integrity (same request → same context)
4. Implement provenance completeness (every context item has origin trace)
5. Implement all G12.0 verification: architecture contracts, invariants, system contracts, snapshots, replay, lifecycle
6. Backward compatibility via re-export

## 2. Engine Boundary Matrix

| Engine | Allowed Reads | Allowed Writes | Forbidden Imports |
|--------|-------------|-------------|------------------|
| Context Fusion (M) | ContextRequest, identity, knowledge facts | WorkspaceContext (in-memory) | reasoning, planner, executor, governance, observer, learning |

**Existing code preserved:** `app/shunya/context/` untouched. New package re-exports it.

## 3. G12.0 Verification Requirements

| Check | How Verified |
|-------|-------------|
| Snapshot consistency | ContextRequest → same fingerprint → same WorkspaceContext |
| Replay integrity | Identity + knowledge snapshots → replayable |
| Provenance completeness | Every ContextItem has type, confidence, provenance |
| Architecture contracts | 6 forbidden import checks, no eval/exec |
| Architectural invariants | Immutable context, deterministic assembly, tenant isolation |
| System contracts | No info loss, provenance continuity, identifier stability |

---

**Implementation ready to begin.**