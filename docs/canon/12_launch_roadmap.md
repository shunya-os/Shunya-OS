# Launch Roadmap

> **Canonical Document · Phase C1**
> **Status: CANONICAL — Implementation-Independent Roadmap**
> **Version: 1.0**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Roadmap Overview](#2-roadmap-overview)
3. [Milestone M1: Canonical Architecture (Phase C1)](#3-milestone-m1-canonical-architecture-phase-c1)
4. [Milestone M2: Core Runtime](#4-milestone-m2-core-runtime)
5. [Milestone M3: Intelligence Layer](#5-milestone-m3-intelligence-layer)
6. [Milestone M4: Experience Layer](#6-milestone-m4-experience-layer)
7. [Milestone M5: Domain Extraction](#7-milestone-m5-domain-extraction)
8. [Milestone M6: Production Hardening](#8-milestone-m6-production-hardening)
9. [Milestone M7: SHUNYA v1.0](#9-milestone-m7-shunya-v10)
10. [Dependency Graph](#10-dependency-graph)
11. [Acceptance Criteria Summary](#11-acceptance-criteria-summary)
12. [Risk Mitigation](#12-risk-mitigation)
13. [Relationship to Other Canonical Documents](#13-relationship-to-other-canonical-documents)

---

## 1. Purpose

This document defines the complete roadmap from the current state to SHUNYA v1.0. Every milestone has clear dependencies, acceptance criteria, and deliverables. This is the governing roadmap — no work outside a defined milestone may begin without an ADR.

---

## 2. Roadmap Overview

### 2.1 Visual Timeline

```
M1: Canonical Architecture (CURRENT) ──── Done
    │
    ▼
M2: Core Runtime ──────────────────────── Estimated: 1-2 weeks
    │
    ▼
M3: Intelligence Layer ────────────────── Estimated: 2-3 weeks
    │
    ▼
M4: Experience Layer ──────────────────── Estimated: 2-3 weeks
    │
    ▼
M5: Domain Extraction ─────────────────── Estimated: 1-2 weeks
    │
    ▼
M6: Production Hardening ──────────────── Estimated: 2-3 weeks
    │
    ▼
M7: SHUNYA v1.0 ───────────────────────── Estimated: T+10-13 weeks
```

### 2.2 Key Dates

| Milestone | Target | Duration |
|-----------|--------|----------|
| **M1: Canonical Architecture** | Phase C1 Complete | Complete (Phase C1) |
| **M2: Core Runtime** | Phase C2 | ~1-2 weeks |
| **M3: Intelligence Layer** | Phase C3 | ~2-3 weeks |
| **M4: Experience Layer** | Phase C4 | ~2-3 weeks |
| **M5: Domain Extraction** | Phase C5 | ~1-2 weeks |
| **M6: Production Hardening** | Phase C6 | ~2-3 weeks |
| **M7: SHUNYA v1.0** | Launch | ~10-13 weeks from start |

---

## 3. Milestone M1: Canonical Architecture (Phase C1)

### 3.1 Status

**CURRENTLY IN PROGRESS** — This is the explicit deliverable of Phase C1.

### 3.2 Deliverables

| Deliverable | File | Status |
|-------------|------|--------|
| Vision | docs/canon/01_shunya_vision.md | ✓ |
| Constitution | docs/canon/02_shunya_constitution.md | ✓ |
| Business Canon | docs/canon/03_business_canon.md | ✓ |
| Universal Object Protocol | docs/canon/04_universal_object_protocol.md | ✓ |
| Runtime Canon | docs/canon/05_runtime_canon.md | ✓ |
| Data Canon | docs/canon/06_data_canon.md | ✓ |
| AI Canon | docs/canon/07_ai_canon.md | ✓ |
| Experience Canon | docs/canon/08_experience_canon.md | ✓ |
| Repository Canon | docs/canon/09_repository_canon.md | ✓ |
| Migration Canon | docs/canon/10_migration_canon.md | ✓ |
| Engineering Canon | docs/canon/11_engineering_canon.md | ✓ |
| Launch Roadmap | docs/canon/12_launch_roadmap.md | ✓ |
| Index | docs/canon/INDEX.md | ✓ |

### 3.3 Acceptance Criteria

- [x] All 12 documents exist
- [x] Documents are internally consistent
- [x] Cross-references verified
- [ ] Formal review by SHUNYA Founder
- [ ] Governance board established

### 3.4 Dependencies

None (this is the starting point).

---

## 4. Milestone M2: Core Runtime

### 4.1 Objective

Extract and implement the universal core runtime as defined in documents 04 and 05.

### 4.2 Modules

| Module | Based On | Description |
|--------|----------|-------------|
| `core/kernel/` | 04 (Protocol) | UniversalObject implementation, type registry |
| `core/identity/` | 03 (Identity) | Identity resolution, management |
| `core/relationship/` | 04 §6 | Relationship graph |
| `core/timeline/` | 04 §7, 05 §6 | Timeline engine |
| `core/evidence/` | 04 §12 | Evidence chain management |
| `core/audit/` | 04 §16 | Immutable audit trail |
| `core/event/` | 05 §4 | Event bus |
| `core/search/` | 04 §15 | Search interface |
| `core/storage/` | 05 (all) | Storage abstraction layer |

### 4.3 Dependencies

- M1 must be complete and reviewed
- Existing `app/kernel/` provides partial implementation
- Existing `app/temporal/` provides partial timeline

### 4.4 Acceptance Criteria

- [ ] All core modules exist
- [ ] UniversalObject protocol is implemented and tested
- [ ] Protocol conformance test suite exists and passes
- [ ] All existing tests still pass (zero regressions)
- [ ] app/ delegates to core/ via adapters
- [ ] No domain-specific code in core/

---

## 5. Milestone M3: Intelligence Layer

### 5.1 Objective

Organize all intelligence engines into the canonical `intelligence/` structure.

### 5.2 Modules

| Module | Source | Based On |
|--------|--------|----------|
| `intelligence/observation/` | app/intelligence/ | 05 §8 |
| `intelligence/knowledge/` | app/knowledge/ + app/gkf/ | 03 §17 |
| `intelligence/reasoning/` | app/intelligence/reasoning/ | 07 §5 |
| `intelligence/planning/` | app/planning/ | 07 §4 |
| `intelligence/governance/` | New + app/shunya/governance/ | 05 §9 |
| `intelligence/execution/` | app/orchestration/ + app/execution/ | 05 §7 |
| `intelligence/decisions/` | app/decision_runtime/ | 03 §14 |
| `intelligence/learning/` | app/learning_intelligence/ | 05 (loop) |
| `intelligence/memory/` | app/memory/ | 03 §16 |
| `intelligence/temporal/` | app/temporal/ | 05 §6.3 |
| `intelligence/prediction/` | app/prediction/ | 07 (reasoning) |
| `intelligence/context/` | app/cortex/ | 05 §6.3 |

### 5.3 Dependencies

- M2 must be complete (intelligence depends on core/)
- Existing intelligence modules provide partial implementations

### 5.4 Acceptance Criteria

- [ ] All engine modules exist in intelligence/
- [ ] Every engine implements the Engine interface (05 §10)
- [ ] No circular dependencies between engines
- [ ] Engine registry is functional
- [ ] Flask app factory integrates intelligence layer
- [ ] All existing tests pass (zero regressions)

---

## 6. Milestone M4: Experience Layer

### 6.1 Objective

Extract and organize the experience layer into `experience/`.

### 6.2 Modules

| Module | Source | Based On |
|--------|--------|----------|
| `experience/ui/` | templates/ + static/ | 08 §7 |
| `experience/navigation/` | app/space/ | 08 §4 |
| `experience/ai/` | AI interaction patterns | 07 §9 |
| `experience/api/` | app/routes/ | 05 (entry points) |
| `experience/adapters/` | app/adapters/ | 05 §10.2 |

### 6.3 Dependencies

- M3 must be complete (experience calls intelligence)
- Existing routes and templates provide partial implementation

### 6.4 Acceptance Criteria

- [ ] All experience modules exist
- [ ] UI component library is documented
- [ ] Space navigation is functional
- [ ] API versioning is implemented
- [ ] All routes work with zero regressions
- [ ] All existing tests pass
- [ ] Key user flows tested end-to-end

---

## 7. Milestone M5: Domain Extraction

### 7.1 Objective

Extract all travel-specific code into `domains/travel/`.

### 7.2 Activities

| Activity | Source | Target |
|----------|--------|--------|
| Extract travel models | app/models.py (travel parts) | domains/travel/models/ |
| Extract travel workflows | shunya_os_crm/workflows/ | domains/travel/workflows/ |
| Extract travel adapters | Existing integration code | domains/travel/adapters/ |
| Extract travel UI | templates/ (travel parts) | domains/travel/ui/ |
| Merge shunya_os_crm/ | Entire app | domains/travel/ |
| Merge shunya_os_dashboard/ | Entire app | domains/travel/ui/ + experience/ |
| Merge shunya_os_documents/ | Relevant models | domains/travel/models/ |
| Merge shunya_os_gmail/ | Email adapter | experience/adapters/ |
| Merge shunya_os_workflow/ | Workflow engine | intelligence/execution/ |

### 7.3 Dependencies

- M4 must be complete (domain modules depend on experience)
- Existing shunya_os_crm/ must continue working during extraction

### 7.4 Acceptance Criteria

- [ ] domains/travel/ is a complete, working domain surface
- [ ] All travel-specific code is extracted from core/
- [ ] No core module imports from domains/
- [ ] Domain can be enabled/disabled via config
- [ ] All existing tests pass (zero regressions)
- [ ] End-to-end test passes for travel domain

---

## 8. Milestone M6: Production Hardening

### 8.1 Objective

Harden the system for production use.

### 8.2 Activities

| Activity | Description |
|----------|-------------|
| **Performance optimization** | Profile and optimize critical paths |
| **Load testing** | Verify system under expected load |
| **Security audit** | Third-party security review |
| **Constitutional audit** | Verify Constitutional compliance in production |
| **Documentation** | Complete API docs, user guides, ops runbook |
| **Monitoring setup** | Production monitoring, alerting, dashboards |
| **Backup verification** | Test restore from backup |
| **Disaster recovery** | Test failover procedures |

### 8.3 Dependencies

- M5 must be complete

### 8.4 Acceptance Criteria

- [ ] Performance meets targets: p95 < 500ms for core APIs
- [ ] Load test: supports expected concurrent users with < 1% error rate
- [ ] Security audit: zero critical or high findings
- [ ] Constitutional audit: zero violations
- [ ] Documentation complete
- [ ] Monitoring and alerting functional
- [ ] Backup and restore verified

---

## 9. Milestone M7: SHUNYA v1.0

### 9.1 Objective

Launch SHUNYA v1.0 with travel domain surface.

### 9.2 Launch Activities

| Activity | Description |
|----------|-------------|
| **Feature flag audit** | All flags reviewed, stable features enabled |
| **Staging final check** | Full end-to-end test on production-like environment |
| **Rollout plan** | Gradual rollout (alpha → beta → GA) |
| **Communication** | Launch announcement, changelog |
| **Support readiness** | Support team trained, runbooks ready |
| **Post-launch monitoring** | 72-hour intensive monitoring |

### 9.3 Dependencies

- M6 must be complete

### 9.4 Acceptance Criteria v1.0

- [ ] All M1-M6 acceptance criteria met
- [ ] Travel domain fully operational
- [ ] Core runtime protocol-conformant
- [ ] Intelligence loop operational (Observation → Decision → Outcome → Learning)
- [ ] Experience layer functional
- [ ] Production hardening verified
- [ ] No known P0 or P1 bugs
- [ ] Documentation complete and reviewed

---

## 10. Dependency Graph

```
M1 (Canonical Docs)
 │
 ▼
M2 (Core Runtime) ◄──── M1
 │
 ▼
M3 (Intelligence Layer) ◄──── M2
 │
 ▼
M4 (Experience Layer) ◄──── M3
 │
 ▼
M5 (Domain Extraction) ◄──── M4
 │
 ▼
M6 (Production Hardening) ◄──── M5
 │
 ▼
M7 (SHUNYA v1.0) ◄──── M6
```

---

## 11. Acceptance Criteria Summary

| Milestone | Key Criteria |
|-----------|-------------|
| **M1** | 12 canonical documents, reviewed, internally consistent |
| **M2** | core/ modules exist, protocol implemented, zero regressions |
| **M3** | intelligence/ modules exist, engine interface, zero regressions |
| **M4** | experience/ modules exist, UI component library, zero regressions |
| **M5** | domains/travel/ extracted, no core→domain imports, zero regressions |
| **M6** | Performance OK, security OK, constitutional OK, docs complete |
| **M7** | All criteria met, no P0/P1 bugs, travel domain operational |

---

## 12. Risk Mitigation

### 12.1 Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Scope creep on M1 | High | Medium | Phase C1 is documentation-only; no code changes |
| Data migration complexity | Medium | High | Strangler fig pattern, additive-first approach |
| Performance regression | Medium | High | Performance baseline, per-phase measurement |
| Security regression | Low | High | Security gates at every phase |
| Engineering productivity drop | Medium | Medium | Clear phase boundaries, documentation |
| Third-party dependency changes | Low | Medium | Minimize external dependencies |

### 12.2 Contingency

If a milestone is blocked:
1. **Blocked by dependency** — address the dependency first
2. **Blocked by technical challenge** — spike investigation (see spike skill)
3. **Blocked by decision** — escalate to governance board
4. **Blocked by scope** — phase scope for requested change via ADR

---

## 13. Relationship to Other Canonical Documents

| Document | Relationship |
|----------|-------------|
| **00_universal_ontology.md** | Roadmap sequences the implementation of ontological primitives into concrete milestones |
| **02_shunya_constitution.md** | Every milestone includes Constitutional compliance check |
| **03_business_canon.md** | Objects are implemented and extracted per roadmap |
| **04_universal_object_protocol.md** | Protocol implementation is M2 |
| **05_runtime_canon.md** | Runtime milestones follow the canon sequence |
| **06_data_canon.md** | Data classification drives M5 extraction |
| **07_ai_canon.md** | AI capabilities mature across M2-M5 |
| **08_experience_canon.md** | Experience layer is M4 |
| **09_repository_canon.md** | Repository consolidation happens across M2-M5 |
| **10_migration_canon.md** | Migration phases align with M2-M5 |
| **11_engineering_canon.md** | Engineering standards apply to all milestones |

---

> **End of Launch Roadmap**

**[Return to INDEX](INDEX.md)**