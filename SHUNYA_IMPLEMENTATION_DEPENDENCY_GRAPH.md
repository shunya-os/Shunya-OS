# SHUNYA Implementation Dependency Graph

**Authority:** SHUNYA_IMPLEMENTATION_PROGRAM.md
**Date:** 2026-07-18
**Status:** Frozen

---

## 1. Task Dependency Graph

```
Phase A — Foundation
├── INFR-001: DI Container (root)
├── INFR-002: Configuration (root)
├── INFR-003: Persistence Layer (depends: INFR-002)
├── INFR-004: Structured Logging (depends: INFR-002)
├── INFR-005: Metrics Collection (depends: INFR-002)
└── INFR-006: Health Endpoint (depends: INFR-001, INFR-004, INFR-005)

Phase B — Event Bus & Credential Store
├── INFR-007: Event Bus Core (depends: INFR-001, INFR-002, INFR-004)
├── INFR-008: Event Bus Delivery (depends: INFR-007)
│   └── INFR-009: Event Bus Retry/DLQ (depends: INFR-008)
├── INFR-010: Event Bus Security (depends: INFR-007, INFR-008)
├── INFR-011: Event Bus Health (depends: INFR-009, INFR-006)
├── INFR-012: Credential Store Core (depends: INFR-003, INFR-002)
│   ├── INFR-013: Credential Store Security (depends: INFR-012)
│   └── INFR-014: Credential Store Phase 4 Gate (depends: INFR-012)

Phase C — Knowledge Store Transition
├── IKS-001: IKS Fact Operations (depends: INFR-003)
├── IKS-002: IKS Lifecycle & Invariants (depends: IKS-001)
├── IKS-003: KnowledgeEngine Facade (depends: IKS-001)
│   └── IKS-004: KnowledgeLayer Legacy Wrapper (depends: IKS-003)
├── IKS-005: Migration Script — Read (depends: IKS-001)
│   └── IKS-006: Migration Script — Seed (depends: IKS-005)
│       └── IKS-007: Migration Script — Report (depends: IKS-006)
└── IKS-008: Facade Fallback Verification (depends: IKS-003, IKS-006)

Phase D — Identity Engine
├── IDEN-001: Identity Normalizer (root)
├── IDEN-002: Identity Resolution Engine (depends: IDEN-001, IKS-001)
│   ├── IDEN-003: Identity Registration (depends: IDEN-002)
│   ├── IDEN-004: Identity Lifecycle State Machine (depends: IDEN-002)
│   ├── IDEN-005: Identity Tenant Isolation (depends: IDEN-002)
│   └── IDEN-006: Identity Events & Integration (depends: IDEN-002, INFR-010)

Phase E — Context Fusion Engine
├── CTX-001: Context Request Handling (depends: IDEN-002, INFR-001)
│   ├── CTX-002: Identity Source Provider (depends: CTX-001, IDEN-002)
│   └── CTX-003: Knowledge Source Provider (depends: CTX-001, IKS-003)
├── CTX-004: Phase 4 Eligibility Gate (depends: CTX-002, CTX-003)
├── CTX-005: Budget Enforcement (depends: CTX-002, CTX-003)
├── CTX-006: Fingerprint Computation (depends: CTX-005)
├── CTX-007: WorkspaceContext Assembly (depends: CTX-002 through CTX-006)
└── CTX-008: Context Fusion State Machine (depends: CTX-007)

Phase F — Reasoning Engine
├── REAS-001: Context Consumption (depends: CTX-007)
├── REAS-002: Evidence Chain Building (depends: REAS-001, IKS-003)
├── REAS-003: Confidence Scoring (depends: REAS-002)
├── REAS-004: Reasoning Strategies (depends: REAS-001, REAS-002, REAS-003)
└── REAS-005: Reasoning State Machine (depends: REAS-004)

Phase G — Planner Engine
├── PLAN-001: Plan Generation (depends: REAS-004, CTX-007)
│   ├── PLAN-002: Plan Templates (depends: PLAN-001)
│   └── PLAN-003: Planner State Machine (depends: PLAN-001)

Phase H — Governance Engine
├── GOV-001: Policy Registry (depends: IKS-003)
├── GOV-002: Plan Validation (depends: PLAN-001)
├── GOV-003: Constitutional Policy Evaluation (depends: GOV-001, GOV-002, CTX-007)
├── GOV-004: Business Policy Evaluation (depends: GOV-003)
├── GOV-005: Risk Assessment (depends: GOV-004)
├── GOV-006: Governance Verdict Production (depends: GOV-005)
├── GOV-007: Immutable Audit Trail (depends: GOV-006)
└── GOV-008: Governance State Machine (depends: GOV-003 through GOV-007)

Phase I — Executor Engine
├── EXEC-001: WhatsApp Channel Adapter (depends: INFR-013)
├── EXEC-002: Telegram Channel Adapter (depends: INFR-013)
├── EXEC-003: Email Channel Adapter (depends: INFR-013)
├── EXEC-004: Generic API Channel Adapter (depends: INFR-013)
├── EXEC-005: Execution Engine — Task Dispatch (depends: EXEC-001-004, GOV-006)
├── EXEC-006: Execution Failure Handling (depends: EXEC-005)
└── EXEC-007: Execution State Machine (depends: EXEC-005, EXEC-006)

Phase J — Observer Engine
├── OBS-001: Observation Recording (depends: EXEC-006, IKS-003)
├── OBS-002: Discrepancy Detection (depends: OBS-001)
└── OBS-003: Observation Events (depends: OBS-001, OBS-002, INFR-010)

Phase K — Learning Engine
├── LEARN-001: Outcome Analysis (depends: OBS-003)
├── LEARN-002: Learning Signal Generation (depends: LEARN-001)
├── LEARN-003: Confidence Calibration (depends: LEARN-002)
└── LEARN-004: Governance Integration (depends: LEARN-003, GOV-006)

Phase K (Parallel) — Doctor Engine
├── DOC-001: Integrity Checks (root)
├── DOC-002: Architecture Drift Detection (depends: INFR-010, GOV-007)
├── DOC-003: Package Health Validation (root)
├── DOC-004: Compliance Verification (depends: GOV-007)
├── DOC-005: Health Aggregation (depends: INFR-006)
└── DOC-006: DoctorReport & Events (depends: DOC-001 through DOC-005, INFR-010)

Phase M — KnowledgeLayer Retirement
├── RET-001: Cutover to IKS (depends: IKS-003, IKS-008)
├── RET-002: Verify No KnowledgeLayer Deps (depends: RET-001)
├── RET-003: Remove KnowledgeLayer (depends: RET-002)
└── RET-004: End-to-End Verification (depends: RET-003)

Phase N — Integration & Hardening
├── INT-001: Full Pipeline Integration Test (depends: all engines complete)
├── INT-002: Constitutional Invariant CI Pipeline (depends: INT-001)
├── INT-003: Performance Benchmarks (depends: INT-001)
└── INT-004: Architecture Checkpoint (depends: INT-002, INT-003)

Phase O — Release
├── REL-001: Operations Runbook (depends: INT-004)
├── REL-002: Security Audit (depends: INT-004)
├── REL-003: Deployment (depends: REL-001, REL-002)
└── REL-004: Release Sign-Off (depends: REL-003)
```

---

## 2. Critical Path

The critical path is the longest dependency chain from root to release:

```
INFR-001 → INFR-007 → INFR-008 → INFR-009 → INFR-010
(Phase A)  (Phase B)  (Phase B)  (Phase B)  (Phase B)
    │
    └── IKS-001 → IKS-003 → CTX-001 → CTX-002 → CTX-004 → CTX-005 → CTX-006 → CTX-007
        (Phase C) (Phase C) (Phase E) (Phase E) (Phase E) (Phase E)  (Phase E) (Phase E)
                                                                          │
                                                                          └── REAS-001 → REAS-002 → REAS-003 → REAS-004
                                                                              (Phase F)  (Phase F)  (Phase F)  (Phase F)
                                                                                                          │
                                                                                                          └── PLAN-001 → GOV-002 → GOV-003 → GOV-004 → GOV-005 → GOV-006
                                                                                                              (Phase G)  (Phase H) (Phase H) (Phase H) (Phase H) (Phase H)
                                                                                                                                                        │
                                                                                                                                                        └── EXEC-005 → EXEC-006 → OBS-001 → OBS-002 → OBS-003
                                                                                                                                                            (Phase I)  (Phase I) (Phase J) (Phase J) (Phase J)
                                                                                                                                                                                        │
                                                                                                                                                                                        └── LEARN-001 → LEARN-002 → LEARN-003 → LEARN-004
                                                                                                                                                                                            (Phase K)   (Phase K)   (Phase K)   (Phase K)
                                                                                                                                                                                                                    │
                                                                                                                                                                                                                    └── INT-001 → INT-002 → INT-004 → REL-001 → REL-003 → REL-004
                                                                                                                                                                                                                        (Phase N)  (Phase N) (Phase N) (Phase O) (Phase O) (Phase O)
```

**Critical path span:** INFR-001 → REL-004 = 84 tasks across 15 phases

**Critical path estimated duration:** ~33 sprints (66 weeks, ~15 months) assuming sequential execution on the critical path.

### Critical Path Bottlenecks

| Bottleneck | Phase | Tasks | Risk | Mitigation |
|------------|-------|-------|------|------------|
| Event Bus (INFR-007→010) | B | 5 tasks, 17 days | Low — well-specified in-process implementation | Parallelize with Credential Store (INFR-012) |
| IKS (IKS-001→003) | C | 3 tasks, 12 days | Low — existing implementation (383 lines) | Parallelize migration script with facade |
| Context Fusion (CTX-001→007) | E | 7 tasks, 18 days | Medium — most complex engine, 6 source providers | Source providers can be implemented in parallel |
| Governance (GOV-001→007) | H | 7 tasks, 26 days | Medium — policy evaluation is core logic | Policy registry parallel with plan validation |
| Learning (LEARN-001→004) | K | 4 tasks, 18 days | Medium — pattern detection and calibration tuning | Cold start reduces risk — no immediate correctness requirement |

---

## 3. Parallelizable Work

### Parallel Within Phase

| Phase | Parallel Groups | Prerequisite | Rationale |
|-------|----------------|-------------|-----------|
| A | INFR-001 + INFR-002 (parallel) | None | DI and Config are independent |
| A | INFR-003 + INFR-004 (parallel) | INFR-002 | Persistence and Logging both depend on Config but not on each other |
| B | INFR-007→011 (Event Bus chain) vs INFR-012→014 (Credential Store chain) | INFR-002, INFR-003 | Event Bus and Credential Store are independent of each other |
| C | IKS-001→002 (IKS core) vs IKS-005→006 (Migration script) | INFR-003 | IKS implementation and migration script can be built in parallel |
| D | IDEN-001 (Normalizer) + IDEN-002 (Resolution) | None | Normalizer independent of resolution logic |
| E | CTX-002 (Identity provider) + CTX-003 (Knowledge provider) | CTX-001 | Source providers are independent of each other |
| F | REAS-001 (Context) + REAS-002 (Evidence) | Partial | Context consumption must come first; evidence building can start after |
| G | PLAN-001 (Generation) + PLAN-002 (Templates) | Partial | Templates depend on generation structure |
| H | GOV-001 (Registry) + GOV-002 (Validation) | IKS-003, PLAN-001 | Registry and plan validation are independent |
| I | EXEC-001→004 (All channel adapters) | INFR-013 | All 4 adapters are independent of each other |
| J | OBS-001 (Recording) + OBS-002 (Discrepancy) | EXEC-006 | Recording comes first; discrepancy builds on recording |
| K | DOC-001→006 (Doctor) vs LEARN-001→004 (Learning) | Various | Doctor and Learning are completely independent engines |
| M | RET-001→004 (retirement chain) | IKS-003 | Sequential within phase — no parallel |
| N | INT-001→004 (integration chain) | All engines | Sequential within phase — no parallel |
| O | REL-001 (Runbook) + REL-002 (Security) | INT-004 | Runbook and security audit are independent |

### Parallel Across Phases

| Phase Pair | Prerequisite | Rationale |
|------------|-------------|-----------|
| C + D (partially) | IKS-001 (IKS core) | Identity Engine can begin once IKS exists (stores identity records). Identity Engine does not need KnowledgeLayer migration to complete. |
| K (Doctor) + any phase | INFR-010 (Event Bus), INFR-006 (Health) | Doctor Engine checks all engines. It can begin once infrastructure and at least some engines exist. But full Doctor requires all engines. |
| G (Planner) + H (Governance) first tasks | PLAN-001, GOV-001 | Planner plan generation and Governance policy registry can be built in parallel once their respective prerequisites are met. |

### Fully Parallel Engines (Same Phase)

| Engine | Phase | Parallelizable With | Constraint |
|--------|-------|--------------------|------------|
| Doctor (ES-008) | K | Learning (ES-007) | Both in Phase K, completely independent |
| Identity (ES-010) | D | Knowledge migration tasks (C) | Once IKS core exists |

---

## 4. Blockers

### Hard Blockers (Cannot Start Until Prerequisite Complete)

| Blocked Task | Blocked By | Blocking Phase | Severity |
|-------------|-----------|---------------|----------|
| All Phase B tasks | Phase A (INFR-001, INFR-002, INFR-003, INFR-004) | Phase B | High — no infrastructure |
| IKS-001 (IKS core) | INFR-003 (Persistence) | Phase C | High — no DB access |
| IDEN-002 (Identity resolution) | IKS-001 (IKS stores identity records) | Phase D | High — no storage |
| CTX-001 (Context request) | IDEN-002 (Identity resolution) | Phase E | High — no identity |
| CTX-003 (Knowledge provider) | IKS-003 (KnowledgeEngine facade) | Phase E | High — no knowledge access |
| REAS-001 (Context consumption) | CTX-007 (Context assembly) | Phase F | High — no context |
| PLAN-001 (Plan generation) | REAS-004 (Reasoning strategies) | Phase G | High — no reasoning output |
| GOV-002 (Plan validation) | PLAN-001 (Plan generation) | Phase H | High — no plan to validate |
| EXEC-005 (Task dispatch) | GOV-006 (Governance verdict) | Phase I | High — no approved plan |
| OBS-001 (Observation recording) | EXEC-006 (Execution outcome) | Phase J | High — no outcome to observe |
| LEARN-001 (Outcome analysis) | OBS-003 (Observation events) | Phase K | High — no observations |
| INT-001 (Full pipeline test) | All engine phases (D through K) | Phase N | High — no full system |
| REL-003 (Deployment) | INT-004 (Architecture checkpoint) | Phase O | High — no verified release |

### Soft Blockers (Can Start with Degraded Mode)

| Task | Blocked By | Degraded Mode |
|------|-----------|---------------|
| REAS-001 (Context consumption) | Context Fusion degraded | Reasoning proceeds with lower confidence, degraded context |
| PLAN-001 (Plan generation) | Context Fusion degraded | Plan with degraded context (medium dependency) |
| GOV-003 (Constitutional policy evaluation) | Context Fusion degraded | Policy evaluation with lower confidence, not blocked |
| EXEC-005 (Task dispatch) | Credential Store unavailable | Cannot execute credentialed tasks, can execute non-credentialed tasks |
| LEARN-001 (Outcome analysis) | Insufficient observations | Cold start mode — collect without recommending |

### Non-Blocking Work (Can Start Independently)

| Task | Phase | Independent Of |
|------|-------|---------------|
| IDEN-001 (Identity normalizer) | D | Everything — no dependencies |
| DOC-001 (Integrity checks) | K | Everything — filesystem only |
| DOC-003 (Package health) | K | Everything — package manager only |
| IKS-005 (Migration script — read) | C | Can be built before IKS is fully operational |
| INFR-012 (Credential Store core) | B | Event Bus chain — independent of Event Bus |

---

## 5. Sequencing

### Recommended Implementation Sequence

```
Sprint 1-2:  Phase A (Foundation) + IDEN-001 (Normalizer, no deps)
Sprint 3-5:  Phase B (Event Bus + Credential Store) + IKS-001 (IKS core)
Sprint 6-8:  Phase C (IKS migration) + IDEN-002→006 (Identity Engine, once IKS exists)
Sprint 9-12: Phase E (Context Fusion) + DOC-001, DOC-003 (Doctor checks, no deps)
Sprint 13-17: Phase F (Reasoning) + GOV-001 (Policy registry, no engine deps)
Sprint 18-20: Phase G (Planner) + DOC-005 (Health aggregation, depends on Phase A)
Sprint 21-25: Phase H (Governance) + DOC-002, DOC-004 (Drift, compliance)
Sprint 26-29: Phase I (Executor) + DOC-006 (Doctor report, needs all checks)
Sprint 30-31: Phase J (Observer)
Sprint 32-36: Phase K (Learning) + Doctor (parallel)
Sprint 37:   Phase M (KnowledgeLayer retirement)
Sprint 38-40: Phase N (Integration)
Sprint 41-42: Phase O (Release)
```

### Phase Grouping by Sprint Blocks

```
Sprints 1-5:   Foundation + Infrastructure  (Phases A-B)
Sprints 6-12:  Core Knowledge + Identity + Context  (Phases C-D-E)
Sprints 13-25: Pipeline Engines 1: Reasoning → Planner → Governance  (Phases F-G-H)
Sprints 26-36: Pipeline Engines 2: Executor → Observer → Learning  (Phases I-J-K)
Sprints 37-42: Retirement + Integration + Release  (Phases M-N-O)
```

### Team Allocation

| Team | Phase A | Phase B | Phase C | Phase D | Phase E | Phase F | Phase G | Phase H | Phase I | Phase J | Phase K | Phase M | Phase N | Phase O |
|------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
| Infrastructure | ████████ | ████████ | | | | | | | | | | | | ██ |
| Identity | | | | ████████ | | | | | | | | | | |
| Knowledge | | | ████████ | | | | | | | | | ████████ | | |
| Context | | | | | ████████ | | | | | | | | | |
| Reasoning | | | | | | ████████ | | | | | | | | |
| Planner | | | | | | | ████████ | | | | | | | |
| Governance | | | | | | | | ████████ | | | | | | |
| Executor | | | | | | | | | ████████ | | | | | |
| Observer | | | | | | | | | | ████████ | | | | |
| Learning | | | | | | | | | | | ████████ | | | |
| Integration | | | | | | | | | | | | | ████████ | |

---

## 6. Dependency Summary Table

| Task | Immediate Dependencies | Phase | Parallelizable? | Critical Path? |
|------|----------------------|-------|-----------------|----------------|
| INFR-001 | None | A | With INFR-002 | Yes |
| INFR-002 | None | A | With INFR-001 | Yes |
| INFR-003 | INFR-002 | A | With INFR-004 | No |
| INFR-004 | INFR-002 | A | With INFR-003 | Yes |
| INFR-005 | INFR-002 | A | With INFR-003 | No |
| INFR-006 | INFR-001, INFR-004, INFR-005 | A | None | No |
| INFR-007 | INFR-001, INFR-002, INFR-004 | B | With INFR-012 | Yes |
| INFR-008 | INFR-007 | B | Sequential | Yes |
| INFR-009 | INFR-008 | B | Sequential | Yes |
| INFR-010 | INFR-007, INFR-008 | B | Sequential | Yes |
| INFR-011 | INFR-009, INFR-006 | B | None | No |
| INFR-012 | INFR-003, INFR-002 | B | With INFR-007 | No |
| INFR-013 | INFR-012 | B | Sequential | No |
| INFR-014 | INFR-012 | B | Sequential | No |
| IKS-001 | INFR-003 | C | With IKS-005 | Yes |
| IKS-002 | IKS-001 | C | Sequential | No |
| IKS-003 | IKS-001 | C | With IKS-005 | Yes |
| IKS-004 | IKS-003 | C | Sequential | No |
| IKS-005 | IKS-001 | C | With IKS-001 | No |
| IKS-006 | IKS-005 | C | Sequential | No |
| IKS-007 | IKS-006 | C | Sequential | No |
| IKS-008 | IKS-003, IKS-006 | C | Sequential | No |
| IDEN-001 | None | D | With IDEN-002 | No |
| IDEN-002 | IDEN-001, IKS-001 | D | Sequential | Yes |
| IDEN-003 | IDEN-002 | D | With IDEN-004 | No |
| IDEN-004 | IDEN-002 | D | With IDEN-003 | No |
| IDEN-005 | IDEN-002 | D | With IDEN-003 | No |
| IDEN-006 | IDEN-002, INFR-010 | D | Sequential | No |
| CTX-001 | IDEN-002, INFR-001 | E | None | Yes |
| CTX-002 | CTX-001, IDEN-002 | E | With CTX-003 | Yes |
| CTX-003 | CTX-001, IKS-003 | E | With CTX-002 | No |
| CTX-004 | CTX-002, CTX-003 | E | Sequential | Yes |
| CTX-005 | CTX-002, CTX-003 | E | Sequential | Yes |
| CTX-006 | CTX-005 | E | Sequential | Yes |
| CTX-007 | CTX-002–006 | E | Sequential | Yes |
| CTX-008 | CTX-007 | E | Sequential | No |
| REAS-001 | CTX-007 | F | None | Yes |
| REAS-002 | REAS-001, IKS-003 | F | With REAS-003 | Yes |
| REAS-003 | REAS-002 | F | With REAS-002 | Yes |
| REAS-004 | REAS-001, REAS-002, REAS-003 | F | Sequential | Yes |
| REAS-005 | REAS-004 | F | Sequential | No |
| PLAN-001 | REAS-004, CTX-007 | G | None | Yes |
| PLAN-002 | PLAN-001 | G | Sequential | No |
| PLAN-003 | PLAN-001 | G | Sequential | No |
| GOV-001 | IKS-003 | H | With GOV-002 | No |
| GOV-002 | PLAN-001 | H | With GOV-001 | Yes |
| GOV-003 | GOV-001, GOV-002, CTX-007 | H | Sequential | Yes |
| GOV-004 | GOV-003 | H | Sequential | Yes |
| GOV-005 | GOV-004 | H | Sequential | Yes |
| GOV-006 | GOV-005 | H | Sequential | Yes |
| GOV-007 | GOV-006 | H | Sequential | No |
| GOV-008 | GOV-003–007 | H | Sequential | No |
| EXEC-001 | INFR-013 | I | With EXEC-002,003,004 | No |
| EXEC-002 | INFR-013 | I | With EXEC-001,003,004 | No |
| EXEC-003 | INFR-013 | I | With EXEC-001,002,004 | No |
| EXEC-004 | INFR-013 | I | With EXEC-001,002,003 | No |
| EXEC-005 | EXEC-001–004, GOV-006 | I | Sequential | Yes |
| EXEC-006 | EXEC-005 | I | Sequential | Yes |
| EXEC-007 | EXEC-005, EXEC-006 | I | Sequential | No |
| OBS-001 | EXEC-006, IKS-003 | J | Sequential | Yes |
| OBS-002 | OBS-001 | J | Sequential | Yes |
| OBS-003 | OBS-001, OBS-002, INFR-010 | J | Sequential | Yes |
| LEARN-001 | OBS-003 | K | Sequential | Yes |
| LEARN-002 | LEARN-001 | K | Sequential | Yes |
| LEARN-003 | LEARN-002 | K | Sequential | Yes |
| LEARN-004 | LEARN-003, GOV-006 | K | Sequential | Yes |
| DOC-001 | None | K | With DOC-003 | No |
| DOC-002 | INFR-010, GOV-007 | K | With DOC-004 | No |
| DOC-003 | None | K | With DOC-001 | No |
| DOC-004 | GOV-007 | K | With DOC-002 | No |
| DOC-005 | INFR-006 | K | None | No |
| DOC-006 | DOC-001–005, INFR-010 | K | Sequential | No |
| RET-001 | IKS-003, IKS-008 | M | Sequential | No |
| RET-002 | RET-001 | M | Sequential | No |
| RET-003 | RET-002 | M | Sequential | No |
| RET-004 | RET-003 | M | Sequential | No |
| INT-001 | All engines complete | N | Sequential | Yes |
| INT-002 | INT-001 | N | Sequential | Yes |
| INT-003 | INT-001 | N | Sequential | No |
| INT-004 | INT-002, INT-003 | N | Sequential | Yes |
| REL-001 | INT-004 | O | With REL-002 | Yes |
| REL-002 | INT-004 | O | With REL-001 | No |
| REL-003 | REL-001, REL-002 | O | Sequential | Yes |
| REL-004 | REL-003 | O | Sequential | Yes |

---

*End of SHUNYA_IMPLEMENTATION_DEPENDENCY_GRAPH.md*