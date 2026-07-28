# SHUNYA v1.0 — Repository Audit Report

Generated: 2026-07-26
Status: Draft for review

## Executive Summary

- **1,392 Python files** across 56 backend packages
- **1,277 TypeScript/TSX files** across 12 frontend packages
- **249 HTML files** (templates)
- **62 frontend build modules**, ~4,600 lines of authored source
- **20 passing backend tests**

---

## Backend Packages

### Canonical Core (active, maintained)

| Package | Files | Purpose | Status | Notes |
|---------|-------|---------|--------|-------|
| `app/__init__.py` | 1 | App factory, blueprint registration, middleware | ✅ Active | Serves frontend + API |
| `app/founder/` | 3 | Founder routes, models, templates | ✅ Active | Primary auth + space system |
| `app/for1/` | 4 | Business domain: proposals, leads | ◐ Partial | Legacy HTML-only endpoints, mixed JS API |
| `app/for2/` | 3 | Business domain: CFO, finance intelligence | ◐ Partial | Working CFO Q&A, but travel-specific |
| `app/finance/` | 9 | Finance models, routes, intelligence | ✅ Active | Invoices, payments, accounts |
| `app/relationship/` | 9 | Relationship routes, models, intelligence | ✅ Active | `@relationship_bp` at `/relationships` |
| `app/onboarding/` | 3 | Business onboarding wizard | ◐ Partial | Routes exist, not frontend-integrated |
| `app/workspace/` | 3 | Workspace backend | ◐ Partial | Policies, models, routes |

### Intelligence & AI

| Package | Files | Purpose | Status | Notes |
|---------|-------|---------|--------|-------|
| `app/intelligence/` | 9 | AI runtime, explainability, context | ✅ Active | Core intelligence engine |
| `app/execution_intelligence/` | 3 | Execution intelligence | ◐ Partial | |
| `app/learning_intelligence/` | 3 | Learning engine | ◐ Partial | |
| `app/llm/` | 2 | LLM integration | ◐ Partial | |
| `app/cognitive/` | 3 | Cognitive runtime | ◐ Partial | |

### Organizational

| Package | Files | Purpose | Status | Notes |
|---------|-------|---------|--------|-------|
| `app/organizational/` | 3 | Org models (OrgUnit, OrgRole, OrgHealth) | ◐ Partial | Dataclass-based, not SQLAlchemy |
| `app/organization/` | 6 | Organization CRUD | ◐ Partial | Overlaps with `app/organizational/` |
| `app/space/` | 17 | Space management | ◐ Partial | May overlap with `app/founder/` spaces |

### Legacy / Overlapping

| Package | Files | Purpose | Status | Notes |
|---------|-------|---------|--------|-------|
| `app/shunya/` | 74 | Original SHUNYA kernel | 🔄 Deprecated | Large, contains legacy identity, auth, context |
| `app/kernel/` | 10 | Kernel models, identity | 🔄 Deprecated | May overlap with `app/shunya/` |
| `app/production/` | 17 | Production identity, deployment | ◐ Active | Identity repository used by 20 tests |
| `app/authz/` | 4 | Authorization models | ◐ Partial | `OrgMemberRole`, `Identity` |
| `app/graph_universal/` | 8 | Universal graph/identity | ◐ Partial | |
| `app/temporal/` | 7 | Temporal runtime | ◐ Partial | |
| `app/orchestration/` | 6 | Orchestration runtime | ◐ Partial | |
| `app/communication/` | 8 | Communication channels | ◐ Partial | |
| `app/intake/` | 8 | Data intake pipeline | ◐ Partial | |

### Minor / Single-File

| Package | Files | Purpose | Status | Notes |
|---------|-------|---------|--------|-------|
| `app/acquisition/` | 1 | Customer acquisition | ◐ Unclear | |
| `app/artifact/` | 1 | Artifact storage | ◐ Unclear | |
| `app/assistant/` | 1 | Assistant runtime | ◐ Unclear | |
| `app/automation/` | 1 | Automation | ◐ Unclear | |
| `app/awareness/` | 3 | Context awareness | ◐ Unclear | |
| `app/brand/` | 1 | Brand management | ◐ Unclear | |
| `app/collaboration/` | 3 | Collaboration runtime | ◐ Unclear | |
| `app/context/` | 1 | Context | ◐ Unclear | |
| `app/cortex/` | 6 | Cortex runtime | ◐ Unclear | |
| `app/data/` | 0 | Empty | ❌ Empty | |
| `app/decision/` | 3 | Decision runtime | ◐ Unclear | |
| `app/decision_runtime/` | 7 | Alternative decision runtime | 🔄 Duplicate | Overlaps with `app/decision/` |
| `app/document/` | 2 | Document management | ◐ Unclear | |
| `app/evidence/` | 6 | Evidence engine | ◐ Partial | |
| `app/execution/` | 1 | Execution runtime | ◐ Unclear | |
| `app/executive/` | 3 | Executive dashboard | ◐ Unclear | |
| `app/gkf/` | 4 | Knowledge framework | ◐ Unclear | |
| `app/graph/` | 7 | Graph runtime | ◐ Unclear | Overlaps with `app/graph_universal/` |
| `app/growth/` | 1 | Growth engine | ◐ Unclear | |
| `app/human_context/` | 2 | Human context | ◐ Unclear | |
| `app/inference/` | 1 | Inference engine | ◐ Unclear | |
| `app/knowledge/` | 1 | Knowledge store | ◐ Unclear | |
| `app/learning/` | 1 | Learning engine | ◐ Unclear | |
| `app/memory/` | 2 | Memory runtime | ◐ Unclear | |
| `app/planning/` | 6 | Planning runtime | ◐ Unclear | |
| `app/prediction/` | 3 | Prediction runtime | ◐ Unclear | |
| `app/privacy/` | 2 | Privacy controls | ◐ Unclear | |
| `app/relevance/` | 1 | Relevance engine | ◐ Unclear | |
| `app/runtime/` | 1 | Adapter | ◐ Unclear | |
| `app/watch/` | 1 | Watch/monitoring | ◐ Unclear | |
| `app/world/` | 1 | World engine | ◐ Unclear | |
| `app/adapters/` | 6 | OS pipeline adapter | ✅ Active | Used by `sign_in`, `create_object` |
| `app/relationship/` | 9 | Relationship routes/models | ✅ Active | |

---

## Frontend Source

### Runtimes (17 files)

| File | Lines | Status | Notes |
|------|-------|--------|-------|
| `orchestrator.ts` | 250 | ✅ Stable | Lifecycle, dependency resolution, recovery |
| `state-fabric.ts` | 345 | ✅ Stable | Versioning, snapshots, persistence, transactions |
| `event-bus.ts` | 60 | ✅ Stable | Typed events, pub/sub |
| `module-registry.ts` | 135 | ✅ Stable | Dynamic module discovery via manifest |
| `composition/engine.ts` | 120 | ✅ Stable | Panel arrangement, workspace composition |
| `experience/engine.ts` | 260 | ✅ Stable | Navigation, commands, focus, notifications |
| `workspace/store.ts` | 120 | ✅ Stable | Lifecycle, persistence, event-driven |
| `layout/engine.ts` | 80 | ✅ Stable | 8 layouts, container-query adaptation |
| `object/engine.ts` | 80 | ✅ Stable | Object fetch, cache |
| `graph/engine.ts` | 100 | ✅ Stable | Relationship authority |
| `timeline/engine.ts` | 60 | ✅ Stable | Event stream |
| `intelligence/engine.ts` | 80 | ✅ Stable | Context insights |
| `commitment/engine.ts` | 200 | ✅ Stable | Evidence-driven progress |
| `conversation/engine.ts` | 160 | ✅ Stable | Multi-object intent |
| `tokens/definitions.ts` | 200 | ✅ Stable | 260+ design tokens |
| `registration.ts` | 100 | ✅ Stable | Runtime registration + dependencies |
| `modules/business.ts` | 165 | ✅ Active | Business module, recently updated |

### Components (10 files, 10 dirs)

| File | Lines | Status | Notes |
|------|-------|--------|-------|
| `executive/index.tsx` | 281 | ◐ Partial | Panel, Metric, InsightCard, ProgressBar — functional but no visual polish |
| `search/universal-search.tsx` | 148 | ◐ Partial | Keyboard nav, overlay — no result detail view |
| `conversation/conversation-workspace.tsx` | 113 | ◐ Partial | Loading/empty/error states added |
| `commitment/commitment-workspace.tsx` | 104 | ◐ Partial | Loading/empty/error states added |
| `workspace/workspace-container.tsx` | 70 | ◐ Partial | Empty module state, Copilot sidebar |
| `workspace/workspace-bar.tsx` | 74 | ◐ Partial | IDE-like tabs |
| `auth/login-page.tsx` | 90 | ◐ Partial | Form, error messages — no branding/landing |
| `copilot/ai-copilot.tsx` | 100 | ◐ Partial | Context-aware, generic fallbacks |
| `dev/runtime-console.tsx` | 84 | ✅ Stable | Dev-only diagnostic tool |

---

## Duplicate / Overlapping Implementations

| Duplicate Set | Files | Recommendation |
|---------------|-------|---------------|
| `app/organization/` vs `app/organizational/` | 6+3 | Consolidate into `app/organizational/` |
| `app/decision/` vs `app/decision_runtime/` | 3+7 | Consolidate into canonical one |
| `app/graph/` vs `app/graph_universal/` | 7+8 | Consolidate into `app/graph_universal/` |
| `app/kernel/` vs `app/shunya/` | 10+74 | Deprecate `app/kernel/`, use `app/shunya/` |
| `app/relationship/` routes prefix | 9 | Uses `/relationships` prefix — align with rest of API |
| `FounderSpace` vs `OrgUnit` vs `Organization` | 3 models | FounderSpace is canonical for demo; OrgUnit/Org for production |

---

## Hidden / Unused Capabilities

| Capability | Location | Should Surface? |
|------------|----------|-----------------|
| CFO Q&A | `app/for2/` | Yes — AI Copilot already queries it |
| Onboarding wizard | `app/onboarding/` | Yes — but needs frontend integration |
| Workspace policies | `app/workspace/` | Yes — context-aware availability |
| Evidence engine | `app/evidence/` | Yes — commitment workspace |
| Organizational intelligence | `app/organizational/` | Yes — multi-org switching |

---

## Test Coverage

- **20 tests** — all passing
- Coverage focused on: Identity engine, core models, production repository
- **No frontend tests** exist
- **No integration tests** exist for the founder API endpoints

---

## Frontend Exposure

| Backend Capability | Frontend Module | Frontend Component | Exposed? |
|--------------------|-----------------|-------------------|----------|
| Founder objects | business.ts | Executive Home panels | ✅ Yes |
| Founder spaces | — | — | ❌ No |
| Finance invoices | — | — | ❌ Module queries /founder/objects instead |
| Relationships | business.ts (legacy) | — | ◐ Legacy endpoint still queried |
| CFO Q&A | ModuleRegistry.askAll | AiCopilot | ✅ Yes |
| Commitments | business.ts | Executive Home metrics | ✅ Yes |
| Conversations | business.ts | — | ❌ No workspace for conversations |
| Timeline milestones | business.ts | InsightCard | ✅ Yes (milestones panel) |
| Onboarding | — | — | ❌ No |
| Workspace policies | — | — | ❌ No |

---

## Key Findings for Convergence

1. **56 backend packages, ~30 are unclear/duplicate** — significant consolidation opportunity
2. **No frontend tests** — risk for refactoring
3. **FounderSpaces created by seed script not discoverable via signin** — identity_id mismatch
4. **app/organization/ vs app/organizational/ duplicate** — merge needed
5. **app/decision/ vs app/decision_runtime/ duplicate** — merge needed
6. **app/graph/ vs app/graph_universal/ duplicate** — merge needed
7. **app/kernel/ vs app/shunya/ duplicate** — deprecation needed
8. **No canonical identity model** — Identity in authz, shunya, production, kernel — 4+ implementations
9. **CORS warning at startup** — flask-cors not installed (minor)
10. **20 tests is insufficient** for a v1.0 release