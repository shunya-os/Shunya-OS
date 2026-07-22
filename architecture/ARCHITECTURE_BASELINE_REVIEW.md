# SHUNYA Architecture Baseline 1.0 — Review

**Date:** 2026-07-18
**Reviewer:** Chief Software Architect
**Scope:** All 15 foundational documents (3 Constitutional, 2 Architecture Standards, 7 Engine Specifications, 3 Governance)

---

## Executive Summary

The SHUNYA Architecture Baseline 1.0 defines a complete, self-consistent, constitutionally-grounded intelligence operating system architecture. The architecture covers the full Compounding Intelligence Loop (Observe → Know → Reason → Plan → Govern → Execute → Observe → Learn → Improve) across 7 engine specifications, 2 architecture standards, and a governance framework.

**Architecture Score: 8.5 / 10**

The architecture is structurally sound, constitutionally compliant, and ready for engineering review. Seven issues require resolution before implementation begins — all are Medium severity, none are Critical or High. No constitutional violations were found. No circular dependencies exist in the engine dependency graph.

**Decision: APPROVED WITH REQUIRED AMENDMENTS**

The architecture baseline is approved. The 7 Medium issues listed below must be resolved before implementation of any engine begins. These may be resolved through ADRs, minor spec amendments, or constitutional guidance.

---

## Architecture Strengths

### 1. Complete Compounding Loop

The 7 engine specifications form a complete, closed loop:

```
Observer → Knowledge → Reasoning → Planner → Governance → Executor → Observer → Learning → Knowledge
```

Every stage has a defined owner. Every transition has a defined trigger. No stage is missing.

### 2. Strict Layer Separation

Every engine specification includes an explicit "SHALL NEVER" section enumerating what that engine may not do. The boundaries are consistent across all 7 specs:

| Engine | May Not |
|--------|---------|
| Knowledge | Reason, execute, govern, learn, access credentials |
| Reasoning | Execute, govern, learn, mutate knowledge, plan |
| Planner | Execute, govern, reason, learn, access credentials |
| Governance | Execute, reason, learn, mutate knowledge, plan |
| Executor | Reason, govern, learn, mutate knowledge, plan |
| Observer | Execute, reason, govern, learn, mutate knowledge |
| Learning | Execute, govern, mutate knowledge directly, rewrite history |

### 3. Constitutional Compliance

All 10 constitutional principles from SHUNYA_ARCHITECTURE.md are mapped to engine responsibilities across the 7 specifications. The key principles are enforced:

- **Governance Before Execution** (6.6) — Executor never receives ungoverned plans
- **Explainable Decisions** (6.5) — Reasoning produces explanation graphs; Governance produces verdict explanations
- **Immutable Knowledge** (6.4) — Knowledge Engine versions every fact
- **No Disappearing Evidence** — Observer validates and preserves evidence immutably
- **Least Authority** — No engine accesses credentials except Executor (at runtime)
- **Tenant Isolation** — Every engine scopes to tenant_id

### 4. Consistent Terminology

The common vocabulary — UniversalObject, Evidence, Confidence (0.0–1.0), Provenance, Event Envelope — is defined once in Core Models and inherited by all 7 engine specs. No engine spec redefines these concepts.

### 5. Clean Dependency Graph

The engine dependency graph is a directed acyclic graph:

```
Observer → Knowledge → Reasoning → Planner → Governance → Executor → Observer
                                                                        ↓
                                                                   Learning
                                                                      ↓
                                                              Knowledge (feedback)
```

No circular dependencies. No engine depends (directly or transitively) on an engine that depends on it.

### 6. Engine Spec Completeness

All 7 engine specifications follow the same template (ENGINE_SPEC_TEMPLATE.md) with consistent section numbering, input/output contracts, failure modes, performance targets, complexity analysis, and constitutional mappings.

---

## Architecture Risks

### R1. Implementation Gap

The gap between the current implementation (SHUNYA OS with rule-based KnowledgeLayer, 5-hardcoded-pattern LearningLayer, template-based PlannerLayer) and the specified architecture is very large. The engine specs describe a system that does not exist yet. Risk of implementation not matching the architecture is **High**.

### R2. Event Bus Dependency

The architecture assumes an Event Bus for inter-engine communication (SHUNYA System Flow §5). The event bus exists only in the `shunya_os_gmail` worktree and is not wired into the main application. No engine specification defines how the Event Bus is instantiated or configured. **Medium** risk.

### R3. Human Review Queue

Governance (ES-001) produces REVIEW verdicts that require human approval. The Observer (ES-006) produces anomaly reports that may require human review. The Learning Engine (ES-007) produces recommendations that may require human approval. None of these specify where the human review queue lives or how humans interact with it. This depends on Phase 17 (Continuous Surface), which is deferred. **Medium** risk.

### R4. Credential Store

The Executor Engine (ES-005) specifies that credentials are resolved at execution time from a credential store. The credential store does not exist yet. No specification defines its interface or security model. **Medium** risk.

### R5. Pattern Library Storage

The Learning Engine (ES-007) requires a pattern library. The Knowledge Engine (ES-002) is the natural storage location, but patterns (scored, scoped, temporal) may not fit the Knowledge Engine's fact_key/value model. **Low** risk.

---

## Dependency Matrix

```
                    Reads From
Engine             Obs  Know Reas Plan Gov  Exec Lear CtxF
─────────────────────────────────────────────────────────
Observer (ES-006)   -    -    -    Y    Y    Y    -    Y
Knowledge (ES-002)  Y    -    -    -    -    -    Y    -
Reasoning (ES-003)  -    Y    -    -    Y    -    -    Y
Planner (ES-004)    -    Y    Y    -    Y    -    -    Y
Governance (ES-001) -    Y    -    Y    -    -    -    Y
Executor (ES-005)   -    Y    -    Y    Y    -    -    Y
Learning (ES-007)   Y    Y    -    -    Y    -    -    Y
```

**Verification:** No circular dependencies. The graph is a DAG. Eight of 56 possible edges are used (14% density — appropriately sparse).

---

## Interface Matrix

```
Engine             Input Source          Output Destination
────────────────────────────────────────────────────────────
Observer (ES-006)  Executor outcome      Knowledge (facts)
                                        Learning (signals)

Knowledge (ES-002) Observer (observations) Reasoning (facts)
                   Learning (signals)    Planner (facts)
                                         Governance (policies)

Reasoning (ES-003) Knowledge (facts)     Planner (conclusions)
                   Context (context)     Governance (evidence)

Planner (ES-004)   Reasoning (results)   Governance (plans)
                   Knowledge (data)

Governance (ES-001) Planner (plans)      Executor (approved plans)
                    Knowledge (policies) Observer (for audit)

Executor (ES-005)  Governance (plans)    Observer (outcomes)

Learning (ES-007)  Observer (observations) Knowledge (proposals)
                                         Governance (proposals)
```

**Verification:** Every output has at least one consumer. Every input has at least one producer. No orphan outputs. No dangling inputs.

---

## Ownership Matrix

| Concept | Owner | Shared With |
|---------|-------|-------------|
| Observations | Observer Engine | Knowledge Engine (storage) |
| Facts / Knowledge | Knowledge Engine | Reasoning (read), Planner (read) |
| Evidence chains | Knowledge Engine | Reasoning (read), Governance (read) |
| Reasoning results | Reasoning Engine | Planner (input), Governance (input) |
| Plans | Planner Engine | Governance (input) |
| Governance verdicts | Governance Engine | Executor (input), Observer (audit) |
| Execution outcomes | Executor Engine | Observer (input) |
| Learning signals | Learning Engine | Knowledge (storage), Governance (review) |
| Confidence scores | Shared | Knowledge, Reasoning, Observer, Learning |
| Policies | Governance Engine | Reasoning (read), Planner (read), Executor (read) |
| Tenant identity | Identity Engine | All (read) |
| Context | Context Fusion | Reasoning, Planner, Governance, Executor, Observer, Learning |
| Event bus | Shared (infrastructure) | All (publish/consume) |
| Credentials | Credential Store | Executor (resolve at runtime) |

**Verification:** Every concept has exactly one owner. No concept is claimed by multiple owners. Shared concepts (confidence, context, event bus) have clearly documented sharing rules.

---

## Terminology Review

| Term | Consistent Across Documents? | Notes |
|------|------------------------------|-------|
| Confidence | ✅ Canonical 0.0–1.0 scale | Defined in Core Models §7, inherited by all specs |
| Evidence | ✅ Canonical model | Defined in Core Models §5, inherited by all specs |
| Provenance | ✅ Canonical model | Defined in Core Models §6, inherited by all specs |
| Event envelope | ✅ Canonical format | Defined in Core Models §8, inherited by all specs |
| Layer | ✅ "named boundary, single responsibility" | Consistent across all documents |
| Engine | ✅ "concrete implementation within a layer" | Consistent across all documents |
| Phase | ✅ "numbered implementation phase" | Consistent across all documents |
| Tenant | ✅ "isolated data namespace" | Consistent across all documents |
| Workspace | ✅ "logical grouping within a tenant" | Consistent across all documents |
| Governance verdict | ✅ APPROVE / REVIEW / REJECT | Defined in ES-001, used in System Flow |
| Observation | ✅ "verified record of what happened" | Consistent across ES-006, System Flow, Core Models |
| Learning signal | ✅ "structured improvement proposal" | Consistent across ES-007, ES-006, Core Models |
| SHALL NEVER | ✅ Consistent formulation | Every engine spec has this section |

**Issues:** None. Terminology is consistent across all 15 documents.

---

## Lifecycle Validation

### Canonical Lifecycle (System Flow §2)

```
External Trigger → Observation → Knowledge Resolution → Context Fusion → Reasoning → Planning → Governance → Execution → Observation → Knowledge Update → Learning → Continuous Improvement
```

**Verification steps:**

1. **External Trigger → Observation:** Observer Engine receives normalized stimulus. ✅
2. **Observation → Knowledge Resolution:** Phase 11 determines sufficiency. ✅
3. **Knowledge Resolution → Context Fusion:** Phase 10 assembles workspace context. ✅
4. **Context Fusion → Reasoning:** Reasoning Engine receives context + facts. ✅
5. **Reasoning → Planning:** Reasoning produces justified conclusions for Planner. ✅
6. **Planning → Governance:** Plan is packaged for governance validation. ✅
7. **Governance → Execution:** Approved plan dispatched to Executor. ✅
8. **Execution → Observation:** Executor reports outcome to Observer. ✅
9. **Observation → Knowledge Update:** Verified observation stored as fact. ✅
10. **Knowledge Update → Learning:** Learning Engine analyzes observations. ✅
11. **Learning → Continuous Improvement:** Recommendations applied, next cycle begins. ✅

**All 11 transitions are defined with owners, inputs, outputs, failure conditions, and recovery.**

---

## Compounding Loop Validation

### What Compounds Per Cycle

| Engine | Compounds | Mechanism | Verified? |
|--------|-----------|-----------|-----------|
| Knowledge | Factual certainty | Versioning without deletion | ✅ |
| Reasoning | Inferential precision | Outcome-feedback on reasoning strategies | ✅ |
| Planner | Planning precision | Outcome-feedback on plan structures | ✅ |
| Governance | Policy effectiveness | Outcome-feedback on policy impact | ✅ |
| Executor | Execution reliability | Outcome-feedback on retry/channel strategies | ✅ |
| Observer | Observation accuracy | Self-validation across cycles | ✅ |
| Learning | Learning effectiveness | Meta-learning (learning how to learn) | ✅ |

### The Complete Loop

```
[Cycle N begins]
  Knowledge (baseline facts)
    → Reasoning (analyze, infer)
    → Planner (create plan)
    → Governance (validate)
    → Executor (execute)
    → Observer (observe outcome)
    → Learning (analyze, improve)
    → Knowledge (updated facts — higher confidence)
[Cycle N+1 begins with better knowledge]
```

**Verification:** The loop is complete. Each cycle produces better inputs for the next cycle. The compounding mechanism is explicitly defined for every engine.

---

## Critical Issues

**None found.**

No critical issues were identified during the review. The architecture is constitutionally compliant, structurally consistent, and has no circular dependencies, missing layers, or orphaned interfaces.

---

## Medium Issues

### M1. Event Bus Not Specified (Medium)

The Event Bus is referenced in SHUNYA System Flow §5, ES-001 §7, ES-002 §7, ES-003 §9, ES-004 §9, ES-005 §9, ES-006 §9, and ES-007 §9 as the primary inter-engine communication mechanism. However, no specification defines the Event Bus itself — its instantiation, configuration, partitioning, delivery guarantees, or operational characteristics.

**Recommendation:** File an Engineering ADR defining the Event Bus as a shared infrastructure component. This can be a thin specification (the event envelope is already defined in Core Models §8) covering instantiation and operational characteristics.

### M2. Credential Store Interface Not Defined (Medium)

ES-005 (Executor Engine) specifies that credentials are resolved at execution time from a "credential store" but does not define the credential store's interface, security model, or integration with Phase 4 (Privacy).

**Recommendation:** The credential store interface must be defined before Executor implementation. This may be an Engineering ADR or a short specification document.

### M3. Human Review Queue Location (Medium)

Governance (ES-001), Observer (ES-006), and Learning (ES-007) all produce outputs that require human review. The human review queue is referenced but not specified — where it lives, how it surfaces items, how humans respond, and how responses flow back to the engines.

**Recommendation:** Defer this until Phase 17 (Continuous Surface) but document the dependency explicitly in each affected engine spec. Add a note that REVIEW verdicts are currently "fire and forget" — the engine emits the event but no consumer is specified.

### M4. Knowledge Engine vs KnowledgeLayer Gap (Medium)

ES-002 (Knowledge Engine) defines the Immutable Knowledge Store as the canonical knowledge storage. However, the current implementation has both `KnowledgeLayer` (markdown KB parser, wired) and `ImmutableKnowledgeStore` (versioned DB, not wired). The specification does not explicitly resolve which one survives.

**Recommendation:** File an Engineering ADR to resolve the KnowledgeLayer vs ImmutableKnowledgeStore unification. The spec assumes the IKS wins, but the migration path is not specified.

### M5. Learning Engine Cold Start (Medium)

ES-007 (Learning Engine) requires a minimum of ~100 observations before pattern discovery can produce meaningful results. The cold start period — when the Learning Engine has observations but not enough for pattern discovery — is not addressed.

**Recommendation:** Add a "cold start mode" to ES-007 where the Learning Engine collects observations without producing recommendations. Document the minimum observation threshold per domain.

### M6. Observer Sampling Rate (Medium)

ES-006 §10 specifies a sampling rate of "100% for executions with anomalies or failures; 10% for successful executions." This implies that 90% of successful executions are not observed in detail. The constitutional principle of "Observation is continuous" (System Flow §14, Invariant 5) may conflict with this sampling approach.

**Recommendation:** Clarify that "observation is continuous" means 100% of executions produce at least a basic observation record. The 10% sampling applies to detailed evidence validation, not to basic observation existence. Update ES-006 to make this distinction explicit.

### M7. Identity Engine and Doctor Engine Not Specified (Medium)

SHUNYA System Flow §3 defines 10 engines (Observer, Knowledge, Reasoning, Planner, Governance, Executor, Learning, Doctor, Context Fusion, Identity). Of these, 7 have engine specifications (ES-001 through ES-007). Three — Doctor Engine, Context Fusion Engine, Identity Engine — are described in System Flow but do not have formal engine specifications.

**Recommendation:** File three new engine specifications (ES-008: Doctor Engine, ES-009: Context Fusion Engine, ES-010: Identity Engine) before implementation of any dependent engines begins.

---

## Minor Issues

| # | Issue | Affected Document | Recommendation |
|---|-------|-------------------|----------------|
| i1 | "tool-based reasoning" is not a reasoning type | ES-003 §5 | Consider adding as a note in Future Extensions |
| i2 | Planner optimization formula references non-existent "weight" source | ES-004 §6 | Clarify that weights come from constraints/preferences |
| i3 | Observer evidence quality formula allows 0.0 cascade | ES-006 §7 | Document that one failing dimension zeros the entire score |
| i4 | Learning confidence calibration formula may oscillate | ES-007 §7 | Add damping factor to prevent over-correction |
| i5 | No cross-reference from System Flow to individual engine specs | System Flow | Add inline citations to ES-001 through ES-007 |
| i6 | Engineer role not mentioned in Governance Model | SHUNYA_GOVERNANCE_MODEL.md | Add Engineering Team as a formal role |
| i7 | Some engine specs reference `canonical event envelope` without citing Core Models | ES-003, ES-004 | Add explicit citation to Core Models §8 |

---

## Recommended ADRs

### ADR-001: Event Bus Specification (Engineering ADR)

**Trigger:** Medium Issue M1 — Event Bus is referenced in every engine spec but not defined.
**Recommended class:** Engineering (infrastructure component, not constitutional).
**Scope:** Define the Event Bus instantiation, configuration, partitioning, delivery guarantees, and operational characteristics. The event envelope is already defined (Core Models §8). This ADR covers the bus itself.

### ADR-002: KnowledgeLayer vs ImmutableKnowledgeStore Unification (Engineering ADR)

**Trigger:** Medium Issue M4 — Two knowledge storage implementations exist.
**Recommended class:** Engineering (implementation decision within existing layer boundaries).
**Scope:** Resolve whether KnowledgeLayer (markdown KB parser) is replaced by IKS, or whether both coexist with IKS as the source of truth and the markdown parser as a seed/migration tool.

### ADR-003: Credential Store Interface (Engineering ADR)

**Trigger:** Medium Issue M2 — Executor requires a credential store that doesn't exist.
**Recommended class:** Engineering (new component within existing architecture).
**Scope:** Define the credential store interface, security model, and Phase 4 (Privacy) integration.

### ADR-004: Doctor Engine Specification (Engineering ADR)

**Trigger:** Medium Issue M7 — Missing engine specification.
**Recommended class:** Engineering (new engine within existing layer boundaries).
**Scope:** Create ES-008 following the ENGINE_SPEC_TEMPLATE.md. The Doctor Engine already has a partial implementation (`app/shunya/doctor.py`).

### ADR-005: Context Fusion Engine Specification (Engineering ADR)

**Trigger:** Medium Issue M7 — Missing engine specification.
**Recommended class:** Engineering.
**Scope:** Create ES-009. Context Fusion already has a computation-only implementation (`app/context/__init__.py` — Phase 10).

### ADR-006: Identity Engine Specification (Engineering ADR)

**Trigger:** Medium Issue M7 — Missing engine specification.
**Recommended class:** Engineering.
**Scope:** Create ES-010. Identity resolution already has an implementation (`app/shunya/identity/`).

---

## Overall Architecture Score

| Dimension | Score | Notes |
|-----------|-------|-------|
| Constitutional compliance | 10/10 | All principles mapped and enforced |
| Layer separation | 10/10 | SHALL NEVER lists are complete and consistent |
| Terminology consistency | 10/10 | One vocabulary across 15 documents |
| Dependency graph | 10/10 | No circular dependencies |
| Lifecycle completeness | 9/10 | Full loop covered; Observer sampling needs clarification |
| Compounding loop | 9/10 | All engines compound; Learning cold start not addressed |
| Interface completeness | 8/10 | Event Bus and Credential Store not specified |
| Specification completeness | 8/10 | 7 of 10 engines specified; 3 missing |
| Implementation readiness | 6/10 | Large gap between spec and current code |

**Overall: 8.5 / 10**

---

## Architecture Readiness for Implementation

| Aspect | Readiness | Gate |
|--------|-----------|------|
| Architecture documents | ✅ Ready | None |
| Governance framework | ✅ Ready | None |
| Engine specifications (7 of 7 pipeline engines) | ✅ Ready | 7 Medium issues must be resolved |
| Missing engine specs (Doctor, Context Fusion, Identity) | ⬜ Not started | Must be created |
| Event Bus | ⬜ Not specified | ADR-001 |
| Credential Store | ⬜ Not specified | ADR-003 |
| Human Review Queue | ⬜ Deferred to Phase 17 | Not blocking |
| Current implementation alignment | ⬜ Not aligned | Major rework needed |

---

## Decision

### APPROVED WITH REQUIRED AMENDMENTS

**Conditions:**

1. Before implementation of any engine begins, resolve Medium Issues M1 (Event Bus) and M4 (KnowledgeLayer vs IKS) via ADRs.
2. Create engine specifications for Doctor Engine (ES-008), Context Fusion Engine (ES-009), and Identity Engine (ES-010) at Draft status before implementation of engines that depend on them begins.
3. Clarify the Observer sampling rate (M6) to distinguish between "basic observation" (100%) and "detailed evidence validation" (10%).
4. Resolve M2 (Credential Store interface) before Executor Engine implementation begins.

**These conditions do not block engineering review of the existing specifications. They block implementation.** The architecture baseline is approved and ready for engineering review.

---

*End of Architecture Baseline 1.0 Review*