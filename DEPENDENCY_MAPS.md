# SHUNYA Architectural Dependency Map
> **Part of the Canonical Repository & Knowledge Runtime Directive**
> **Date:** 2026-07-28
> **Status:** Candidate for Founder Review

---

## 1. Constitutional Authority Hierarchy

```
CONST-I (First Principles) ─── 13 Principles
  │
  ├── CONST-II (SHUNYA Constitution) ─── 9 Articles, 10 Engines, 17 Guarantees
  │     │
  │     ├── CONST-III (Canonical Definitions) ─── 31 definitions
  │     │
  │     ├── CONST-IV (Constitutional Compliance) ─── Enforcement, violations, audits
  │     │
  │     └── CONST-V (Hermes Implementation Charter) ─── Implementation obligations
  │
  └── All architecture, governance, and implementation derive from this chain
```

**Rule:** No downstream document may contradict an upstream document. Amendment requires CAP.

---

## 2. Engine Dependency Graph

```
ENG-OBS (Observer)
  │
  ├──> ENG-MEM (Memory) ─── stores observations as experiences
  │
  ├──> ENG-KNW (Knowledge) ─── consolidates observations into knowledge
  │
  ├──> ENG-RSN (Reasoner) ─── reasons over knowledge
  │     │
  │     ├──> ENG-SIM (Simulation) ─── simulates reasoned futures
  │     │     │
  │     │     └──> ENG-PLN (Planner) ─── plans through simulated landscapes
  │     │           │
  │     │           └──> ENG-EXC (Executive) ─── executes approved plans
  │     │                 │
  │     │                 └──> ENG-EVL (Evaluator) ─── evaluates outcomes
  │     │                       │
  │     │                       └──> ENG-LRN (Learner) ─── learns from evaluations
  │     │                             │
  │     │                             └── feeds back to ENG-RSN, ENG-SIM
  │     │
  │     └── ENG-GOV (Governance) ─── constrains ALL engines at every step
  │
  └── ENG-GOV (Governance) ─── constrains every engine-to-engine message
```

**Dependency Direction:** Information flows top-to-bottom. Governance constrains all.

---

## 3. Runtime Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RUNTIME PIPELINE                          │
│                    core/runtime_pipeline/                        │
│  Orchestrates all runtimes through CANONICAL_STAGES pipeline     │
└──────┬──────────────────────────────────────────────────┬────────┘
       │                                                  │
       ▼                                                  ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│  COGNITIVE        │  │  EXECUTION       │  │  INTEGRATION         │
│  RUNTIME          │  │  RUNTIME         │  │  RUNTIME              │
│  core/cognitive/  │  │  core/execution/ │  │  core/integration/   │
│  10 engines       │  │  Commitments     │  │  Connectors          │
│  governance check │  │  Tasks/Workflows │  │  External adapters   │
└──────────────────┘  └──────────────────┘  └──────────────────────┘
       │                       │                       │
       ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MEMORY/KNOWLEDGE RUNTIME                     │
│                    core/memory_knowledge_runtime/                  │
│  Memory Engine │ Knowledge Engine │ Timeline │ Evidence Store    │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      WORKSPACE RUNTIME                            │
│                    core/workspace_runtime/                         │
│  Workspace model │ Object protocol │ User sessions                │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      KERNEL RUNTIME                               │
│                    core/kernel/                                   │
│  Identity │ Object primitives │ Relationships │ State │ Types    │
└─────────────────────────────────────────────────────────────────┘
```

**Layer Rule:** Each layer imports only from layers above it. No layer imports from below.

---

## 4. Engine → Runtime Mapping

| Engine | Primary Runtime | Supporting Runtimes |
|--------|----------------|---------------------|
| Observer | core/intelligence/perception/ | core/event/, core/timeline/ |
| Memory | core/memory_knowledge_runtime/ | core/timeline/, core/storage/ |
| Knowledge | core/memory_knowledge_runtime/ | core/registry/, core/search/ |
| Reasoner | core/intelligence/reasoning/ | core/evidence/, core/validation/ |
| Simulation | core/projection/ | core/intelligence/, core/timeline/ |
| Planner | core/planning_runtime/ | core/intelligence/planning/ |
| Executive | core/execution_runtime/ | core/evidence/, core/identity/ |
| Evaluator | core/intelligence/decision/ | core/evidence/, core/validation/ |
| Learner | core/intelligence/learning/ | core/registry/, core/storage/ |
| Governance | core/runtime_pipeline/ | core/identity/, core/validation/ |

---

## 5. Document Dependency Map

```
FIRST PRINCIPLES (CONST-I)
  │
  ├──> SHUNYA CONSTITUTION (CONST-II)
  │     │
  │     ├──> CANONICAL DEFINITIONS (CONST-III)
  │     │
  │     ├──> CONSTITUTIONAL COMPLIANCE (CONST-IV)
  │     │
  │     ├──> HERMES CHARTER (CONST-V)
  │     │
  │     ├──> SHUNYA_ARCHITECTURE_v1.0
  │     │     │
  │     │     ├──> ADRs (ADR-001 through ADR-007)
  │     │     │
  │     │     ├──> Engine Specs (ES-001 through ES-010)
  │     │     │     │
  │     │     │     └──> Implementation Phases (PHASE-A through PHASE-N)
  │     │     │
  │     │     ├──> DNA-01 Architecture (DNA-01.x)
  │     │     │
  │     │     └──> Design Canons (CANON-00 through CANON-12)
  │     │           │
  │     │           └──> UX Canons (CANON-UX-01 through CANON-UX-19)
  │     │
  │     ├──> SHUNYA_ENGINEERING_CONSTITUTION (GOV-ENG)
  │     │
  │     └──> SHUNYA_GOVERNANCE_MODEL (GOV-MODEL)
  │
  └──> GOVERNANCE DOCUMENTS (GOV-*)
```

---

## 6. Phase Dependency Graph

```
PHASE-A (Foundation Infrastructure)
  │
  ├──> PHASE-B (Reasoning Engine)
  │     │
  │     ├──> PHASE-C (Observer Engine)
  │     │
  │     ├──> PHASE-D (Evaluator Engine)
  │     │
  │     ├──> PHASE-E (Knowledge Engine)
  │     │
  │     ├──> PHASE-F (Executive Engine)
  │     │     │
  │     │     ├──> PHASE-G (Learner Engine)
  │     │     │
  │     │     ├──> PHASE-H (Memory Engine)
  │     │     │
  │     │     ├──> PHASE-I (Planner Engine)
  │     │     │
  │     │     ├──> PHASE-J (Automation/Event Engine)
  │     │     │
  │     │     ├──> PHASE-K (Projection/Simulation Engine)
  │     │     │
  │     │     ├──> PHASE-L (Convergence)
  │     │     │
  │     │     ├──> PHASE-M (Platform)
  │     │     │
  │     │     └──> PHASE-N (Platform)
  │     │
  │     └──> PHASE-X4 (Workspace Runtime)
  │
  └──> Canon Documents (C1, C2)
```

---

## 7. Frontend → Backend Dependency

```
Frontend (TypeScript/React)
  │
  ├── frontend/src/runtimes/*/engine.ts  ─── UI runtimes
  │     │
  │     ├── experience/engine.ts  ─── manages experience state
  │     ├── layout/engine.ts  ─── manages layout
  │     ├── workspace/store.ts  ─── workspace state
  │     ├── object/engine.ts  ─── object protocol
  │     ├── graph/engine.ts  ─── knowledge graph
  │     ├── intelligence/engine.ts  ─── AI collaboration
  │     ├── commitment/engine.ts  ─── commitment management
  │     ├── conversation/engine.ts  ─── conversation
  │     ├── timeline/engine.ts  ─── timeline
  │     └── composition/engine.ts  ─── composition
  │
  ├── frontend/src/api/client.ts  ─── API client → backend routes
  │
  └── Depends on: CANON-UX-01 through 19 (experience canons)
              CANON-08 (Experience Canon)
              DNA-01 (Device-Native Architecture)
```

---

## 8. Repository → Git Branches

```
master (mainline)
  │
  ├── docs ─── documentation updates
  │
  ├── feature/alpha-001a-gmail-oauth
  ├── feature/alpha-001b-gmail-sync
  ├── feature/alpha-001c-document-import
  ├── feature/alpha-001j-workflow
  ├── feature/alpha-002a-universal-crm
  └── feature/alpha-003a-dashboard
```

---

## 9. Key Dependency Rules

1. **No circular dependencies between engines** — each engine depends only on earlier engines in the pipeline
2. **No circular dependencies between layers** — layers import from above, not below
3. **Constitutional hierarchy is strict** — no downstream document overrides an upstream one
4. **Governance constrains all** — every engine-to-engine message passes through Governance
5. **Phase ordering is sequential** — later phases depend on earlier phases
6. **ADRs precede implementation** — architectural decisions are made before implementation begins
7. **Engine specs precede engine code** — specifications are frozen before implementation

---

## 10. Dependency Verification

| Rule | Verification Method | Status |
|------|-------------------|--------|
| No circular engine dependencies | Knowledge graph analysis | See KNOWLEDGE_GRAPH.yaml |
| Layer import direction | Code review | See architecture/SHUNYA_CONSTITUTION.md |
| Constitutional hierarchy | Document comparison | See CONSTITUTIONAL_COMPLIANCE.md |
| Governance constraint | Pipeline verification | See core/runtime_pipeline/ |
| Phase ordering | Implementation program | See SHUNYA_IMPLEMENTATION_PROGRAM.md |
| ADR → Implementation | ADR status tracking | See ADR records |
| Spec → Code | Spec-to-code mapping | See engine specs |