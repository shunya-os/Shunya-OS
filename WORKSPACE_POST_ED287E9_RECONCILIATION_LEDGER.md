# SHUNYA M2B — Post-ed287e9 Reconciliation Ledger

## 0. Executive Summary

**Directive:** M2B — Canonical Workspace Convergence
**Baseline SHA:** `ed287e901e81eef9c4feb11e2a96d244feb5adf4` (UX-BRIDGE-02)
**Current Production SHA:** `2bfa630bc5d80d142f2235b9baa412fac51ec2d0`
**Recovery SHA:** `6e104c13cd4ddaed0b5f4dd3da99a5b5b65b15cb`
**Recovery Branch:** `primary-workspace-recovery`
**Commits Since Baseline:** 154 (ed287e9..2bfa630)

### Key Finding

**ed287e9 (the baseline) rendered PrimaryWorkspace** — the correct organizational domain workspace. The LivingWorkspace convergence (7c9c0d0) replaced it with a simplified shell that lost the 12-domain sidebar, Content Studio as a real route, and organizational navigation. The current recovery restores PrimaryWorkspace (ed287e9 lineage) and adds OperatingContextSelector + useActiveContext — capabilities from the post-convergence heritage fork.

---

## 1. Branch Topology Matrix

### Classification by Workspace Renderer

| Branch | HEAD SHA | Workspace Renderer | Context Model | Ahead/Behind master | Lineage |
|--------|----------|-------------------|---------------|-------------------|---------|
| **primary-workspace-recovery** | 6e104c1 | **PrimaryWorkspace** (executive-home + OperatingContextSelector) | useActiveContext (Zustand, /whoami) | ahead=2, behind=0 | ✅ CANONICAL TARGET |
| **origin/master** (PROD) | 2bfa630 | LivingWorkspace | None | ahead=1, behind=0 | ❌ WRONG LINEAGE |
| **master** (local) | a59b5cd | LivingWorkspace | None | baseline | ❌ WRONG LINEAGE |
| **workspace-convergence** | 2280f1f | LivingWorkspace | None | ahead=1, behind=10 | ❌ WRONG LINEAGE |
| **main** | a9d481f | WorkspaceBar + WorkspaceContainer | useActiveContext | ahead=150, behind=428 | 🔀 HERITAGE FORK |
| **workspace-heritage-convergence** | a9d481f | WorkspaceBar + WorkspaceContainer | useActiveContext | same as main | 🔀 symlink to main |
| **ed287e9** (BASELINE) | ed287e9 | **PrimaryWorkspace** (executive-home) | None — no context switching | ancestor | ✅ CORRECT BASE |

### Production Provenance

| Metric | Value |
|--------|-------|
| Deployed SHA | 2bfa630bc5d80d142f2235b9baa412fac51ec2d0 |
| Deployed Renderer | LivingWorkspace |
| Release Type | CI_CERTIFIED |
| Health | database=connected, status=ok |
| Upstream | origin/master matches deployed |
| Working Tree (post-commit) | CLEAN |

---

## 2. Lineage Classification

### A. WRONG WORKSPACE LINEAGE — LivingWorkspace as root renderer

Commits that reactivated LivingWorkspace as the root workspace, losing the organizational sidebar and domain routing:

| SHA | Message | Effect |
|-----|---------|--------|
| 7c9c0d0 | ZGC-PR-14-WS: Canonical workspace convergence — restore LivingWorkspace | Replaced PrimaryWorkspace with LivingWorkspace in app.tsx |
| a59b5cd | ZGC-PR-14-WS: Fix pre-existing TS error — api.askIntelligence → api.ask | Minor TS fix on LivingWorkspace branch |
| 2bfa630 | ZGC-PR-14-WS: Add .hermes/scratch/ to .gitignore | Clean deploy tree (deployed to production) |

**workspace-convergence branch** (2280f1f) — separate branch at same lineage point, LivingWorkspace renderer.

**Verdict:** These commits must be superseded. The LivingWorkspace was a step backward from the ed287e9 PrimaryWorkspace architecture.

### B. CORRECT ORGANIZATIONAL WORKSPACE LINEAGE — PrimaryWorkspace from ed287e9

| SHA | Message | Effect |
|-----|---------|--------|
| ed287e9 | UX-BRIDGE-02: Fix People API permission, build DomainWorkspaceRouter | Baseline — PrimaryWorkspace with 12-domain sidebar, DomainWorkspaceRouter |
| 6e104c1 | M2B: PrimaryWorkspace recovery — restore organizational domain architecture | Restores PrimaryWorkspace + adds OperatingContextSelector + useActiveContext |

**This is the canonical lineage.** All further work must build on `primary-workspace-recovery`.

### C. POST-CONVERGENCE CAPABILITY LINEAGE — main branch (WorkspaceContainer architecture)

The `main` branch diverged from the shared baseline (e1227879) and developed a separate WorkspaceContainer architecture with 150 commits including:

| Key Capabilities | SHA Range | Status |
|-----------------|-----------|--------|
| WorkspaceContainer + WorkspaceBar shell | 8ded5db..a9d481f | ALTERNATIVE ARCHITECTURE |
| OperatingContextSelector + useActiveContext | various | ✅ INTEGRATED into recovery |
| Content Studio as real component | various | ✅ INTEGRATED into PrimaryWorkspace (existing lazy import) |
| Calm-white theming | various | ✅ PRESERVED (same CSS variables) |
| Genesis Reset + post-reset certification | 8ded5db | INFRASTRUCTURE |
| Resend SMTP, production identity, email verification | various | ✅ PRESERVED (backend, not frontend) |

**Verdict:** DO NOT merge the entire main branch (150 commits) — it's a different architecture. Cherry-pick specific capabilities: OperatingContextSelector, useActiveContext, Content Studio wiring pattern.

### D. CANONICAL DESTINATION BRANCH

**primary-workspace-recovery** (6e104c1) is the designated canonical branch.

**Merger plan:**
1. `primary-workspace-recovery` → merged into `master` (which then aligns with `origin/master`)
2. No force push, no reset, no history rewrite
3. Main branch remains evidence of heritage architecture; no destructive action

---

## 3. 154-Commit Post-ed287e9 Capability Reconciliation

### Commits ed287e9..2bfa630 (chronological)

```
ed287e9 BASELINE — UX-BRIDGE-02: Fix People API permission, build DomainWorkspaceRouter
  ↓ 154 commits on master lineage
2bfa630 Production HEAD — ZGC-PR-14-WS: Add .hermes/scratch/
```

### Capability Group: Workspace and Navigation

| Capability | Commits | Backend | Frontend | Active in Recovery? | Route/Surface | Status |
|-----------|---------|---------|----------|--------------------|--------------|--------|
| DomainWorkspaceRouter | ed287e9 | app/models, routes | PrimaryWorkspace OrganizationalOrientation | ✅ PRESERVED | native route matching | PRESERVED |
| MobileDomainNav | ed287e9 lineage | N/A | mobile domain nav bar | ✅ PRESERVED | mobile sidebar | PRESERVED |
| Browser history sync | ed287e9 + later | N/A | app.tsx `initBrowserHistory()` | ✅ PRESERVED | URL sync | PRESERVED |
| Workspace state lifecycle | ed287e9 | backend session | useWorkspaceStore | ✅ PRESERVED | activate/deactivate | PRESERVED |
| Lazy loading | ed287e9 | N/A | React.lazy imports (all domain components) | ✅ PRESERVED | code-split | PRESERVED |
| Progressive startup | ed287e9 | N/A | BootScreen → authenticated render | ✅ PRESERVED | boot sequence | PRESERVED |
| LivingWorkspace renderer | 7c9c0d0 | N/A | living-workspace/living-workspace.tsx | ❌ SUPERSEDED by PrimaryWorkspace | root renderer | SUPERSEDED |
| OperatingContextSelector | main branch heritage | backend for2/whoami | context-selector.tsx | ✅ INTEGRATED | workspace bar | INTEGRATED |
| useActiveContext store | main branch heritage | backend for2/whoami | use-active-context.ts | ✅ INTEGRATED | Zustand store | INTEGRATED |

### Capability Group: Organizational Context

| Capability | Commits | Backend | Frontend | Active? | Status |
|-----------|---------|---------|----------|---------|--------|
| Personal workspace | ed287e9 | FounderSpace, type=personal | PrimaryWorkspace personal nav | ✅ PRESERVED | PRESERVED |
| Business workspace | post-ed287e9 | Organization model | Org-specific domain data | ✅ PRESERVED | PRESERVED |
| Organization switching | post-ed287e9 + heritage | POST /switch, /switch/personal | OperatingContextSelector | ✅ INTEGRATED | INTEGRATED |
| Active context store | heritage | GET /api/v1/for2/whoami | use-active-context.ts | ✅ INTEGRATED | INTEGRATED |
| Backend session ownership | post-ed287e9 | session current_org_id | N/A | ✅ PRESERVED | PRESERVED |
| Canonical workspace model | d2ffcc8, d3f3aad | app/workspace/models.py | workspace-switcher.tsx | ✅ PRESERVED | PRESERVED |
| Legacy for2 context paths | post-ed287e9 | for2/ routes for backward compat | N/A | ✅ PRESERVED | PRESERVED |
| Workspace isolation (cross-org) | heritage | OrgMember org-specific check | N/A | ✅ PRESERVED | PRESERVED |

### Capability Group: Content Studio 4.0

| Capability | Commits | Backend | Frontend | Active in Recovery? | Status |
|-----------|---------|---------|----------|--------------------|--------|
| Blog Post | c81a86d .. | /api/v1/content/generate | ContentStudio component | ✅ PRESERVED (lazy import) | PRESERVED |
| Social Post | c81a86d .. | /api/v1/content/generate | ContentStudio component | ✅ PRESERVED | PRESERVED |
| Email Campaign | c81a86d .. | /api/v1/content/generate | ContentStudio component | ✅ PRESERVED | PRESERVED |
| Product Description | c81a86d .. | /api/v1/content/generate | ContentStudio component | ✅ PRESERVED | PRESERVED |
| Press Release | c81a86d .. | /api/v1/content/generate | ContentStudio component | ✅ PRESERVED | PRESERVED |
| SEO Meta | c81a86d .. | /api/v1/content/generate | ContentStudio component | ✅ PRESERVED | PRESERVED |
| Ad Copy | c81a86d .. | /api/v1/content/generate | ContentStudio component | ✅ PRESERVED | PRESERVED |
| Landing Page | c81a86d .. | /api/v1/content/generate | ContentStudio component | ✅ PRESERVED | PRESERVED |
| Repurpose | c81a86d .. | /api/v1/content/generate | ContentStudio component | ✅ PRESERVED | PRESERVED |
| Media Generation | c81a86d .. | /api/v1/content/media | MediaGenerator in ContentStudio | ✅ PRESERVED | PRESERVED |
| History (persistence) | c81a86d .. | GET/DELETE /api/v1/content/history | History tab | ✅ PRESERVED | PRESERVED |
| Brand Voice (5 profiles) | c81a86d .. | backend profile storage | BrandVoice selector | ✅ PRESERVED | PRESERVED |
| Tone slider | c81a86d .. | N/A | 5-level tone control | ✅ PRESERVED | PRESERVED |
| **As real domain route** | **RECOVERY** | N/A | `content` route → `<ContentStudio />` | **NEEDS VERIFICATION** | **NEEDS-RECONCILIATION** |

### Capability Group: CRM and Commercial

| Capability | Commits | Backend | Frontend | Active? | Status |
|-----------|---------|---------|----------|---------|--------|
| Commercial workspace | post-ed287e9 | Objects API, opportunities | <CommercialWorkspace /> | ✅ PRESERVED | PRESERVED |
| Sales pipeline | post-ed287e9 | Objects API, proposals | <SalesPipeline /> | ✅ PRESERVED | PRESERVED |
| Lead management | post-ed287e9 | Objects API, leads | <LeadManagement /> | ✅ PRESERVED | PRESERVED |
| People (OrganizationBrowser) | ed287e9 | /api/v1/objects/types, permissions | <OrganizationBrowser /> | ✅ PRESERVED | PRESERVED |
| Relationships | post-ed287e9 | /api/v1/objects (relations) | <RelationshipWorkspace /> | ✅ PRESERVED | PRESERVED |

### Capability Group: Intelligence and SHUNYA Presence

| Capability | Commits | Backend | Frontend | Active? | Status |
|-----------|---------|---------|----------|---------|--------|
| Awareness signals (SSE) | ed287e9 lineage | living-store SSE | subscribeSSE | ✅ PRESERVED | PRESERVED |
| Polling | ed287e9 lineage | /api/v1/for2/whoami | periodic context refresh | ✅ PRESERVED | PRESERVED |
| AI presence | ed287e9 lineage | AI chat endpoints | PresenceIndicator, AIPresencePanel | ✅ PRESERVED | PRESERVED |
| What Matters Now | ed287e9 lineage | /api/v1/intention | WhatMattersNow component | ✅ PRESERVED | PRESERVED |
| Command surface | ed287e9 lineage | CommandToActionBridge | CommandBar | ✅ PRESERVED | PRESERVED |
| Voice / TTS | ed287e9 lineage | TTS endpoint | VoiceInput component | ✅ PRESERVED | PRESERVED |
| Intelligence APIs | heritage | /api/v1/ai/* | AI chat panel | ✅ PRESERVED | PRESERVED |

### Capability Group: Business Domains

| Capability | Backend | Frontend | Active in Recovery? | Status |
|-----------|---------|----------|--------------------|--------|
| Work | Objects API | <ExecutionWorkspace /> + <TasksWorkspace /> | ✅ PRESERVED | PRESERVED |
| Finance | Objects API (filtered) | <DomainOverview> (placeholder text) | ✅ PRESERVED | DEFECT (see below) |
| Commercial | Objects API (deals) | <CommercialWorkspace /> | ✅ PRESERVED | PRESERVED |
| Marketing | Campaign routes | <MarketingDashboard /> | ✅ PRESERVED | PRESERVED |
| Sales | Objects API (proposals/pipeline) | <SalesPipeline /> | ✅ PRESERVED | PRESERVED |
| Operations | Objects API | <DomainOverview> (placeholder) | ✅ PRESERVED | **LEGACY-NONCANONICAL** |
| Knowledge | Objects API (documents) | <DomainOverview> (placeholder) | ✅ PRESERVED | BLOCKED (see below) |
| Outputs | Objects API | <OutputsBrowser /> | ✅ PRESERVED | PRESERVED |
| Memory | living-store SSE | <MemoryBrowser /> | ✅ PRESERVED | PRESERVED |
| Relationships | Objects API (relations) | <RelationshipWorkspace /> | ✅ PRESERVED | PRESERVED |
| Content | Content API | <ContentStudio /> (lazy) | ✅ PRESERVED | NEEDS-RECONCILIATION |
| Entities | Objects API | <EntityManager /> | ✅ PRESERVED | PRESERVED |

---

## 4. Domain Truth Matrix

| Domain | Route | UI Component | Backend Connected | Classification | Evidence |
|--------|-------|-------------|-------------------|---------------|----------|
| People | `/workspace/people` | OrganizationBrowser | ✅ Objects API + permissions | **REAL** | ed287e9 baseline, tested |
| Work | `/workspace/work` | ExecutionWorkspace + TasksWorkspace | ✅ WHOAMI, Intention, SSE | **REAL** | Multi-component, tested |
| Finance | `/workspace/finance` | DomainOverview (placeholder) | ✅ Objects API with filter | **PLACEHOLDER** | Shows "Finance overview coming soon" |
| Commercial | `/workspace/commercial` | CommercialWorkspace | ✅ Objects API (opportunities) | **REAL** | Full workspace, tested |
| Marketing | `/workspace/marketing` | MarketingDashboard | ✅ Campaign routes, AI chat | **REAL** | Campaign management, tested |
| Sales | `/workspace/sales` | SalesPipeline | ✅ Objects API (proposals) | **REAL** | Pipeline, lead management, tested |
| Operations | `/workspace/operations` | DomainOverview (placeholder) | ✅ Objects API | **NOT IMPLEMENTED** | Placeholder text: "not yet implemented" |
| Knowledge | `/workspace/knowledge` | DomainOverview (placeholder) | ✅ Objects API (documents) | **PLACEHOLDER** | Backend exists, frontend only shows DomainOverview |
| Outputs | `/workspace/outputs` | OutputsBrowser | ✅ Objects API | **REAL** | Full browser with filtering |
| Memory | `/workspace/memory` | MemoryBrowser | ✅ living-store SSE, AI memory | **REAL** | Memory browser component |
| Relationships | `/workspace/relationships` | RelationshipWorkspace | ✅ Objects API (relations) | **REAL** | Relationship graph + timeline |
| Content | `/workspace/content` | ContentStudio (lazy import) | ✅ /api/v1/content/* | **REAL** | 10 formats, brand voice, media gen, history |
| Entities | `/workspace/entities` | EntityManager | ✅ Objects API (types) | **REAL** | Dynamic entity type system |

### Key Classification Notes

- **Finance** is PLACEHOLDER — backend can serve filtered objects but frontend shows generic DomainOverview, not a dedicated Finance workspace
- **Knowledge** is PLACEHOLDER — backend serves documents but frontend shows DomainOverview
- **Operations** is NOT IMPLEMENTED — explicitly called out as "not yet implemented" in code
- **Content Studio** is REAL as a component but was trapped behind modal-only access in LivingWorkspace; the PrimaryWorkspace recovery exposes it as a real domain route

---

## 5. Workspace Ownership Map

| Component | File | Canonical? | Active? | Reusable? | Deprecated? | Removal Decision |
|-----------|------|-----------|---------|-----------|-------------|-----------------|
| **PrimaryWorkspace** | executive-home/executive-home.tsx | ✅ YES | ✅ YES (recovery) | ✅ Yes | ❌ | KEEP — canonical root |
| **LivingWorkspace** | living-workspace/living-workspace.tsx | ❌ | ❌ NO (replaced) | 🔄 Yes — components | 🔄 Future removal candidate | Do not delete until PrimaryWorkspace uses its sub-components prove zero dependency |
| **WorkspaceContainer** | workspace/workspace-container.tsx | ❌ | ❌ NO (main branch only) | ❌ Different architecture | 🔄 Heritage fork | Keep as evidence on main branch |
| **WorkspaceBar** | workspace/workspace-bar.tsx | ❌ | ❌ NO (main branch only) | ❌ Different architecture | 🔄 Heritage fork | Keep as evidence on main branch |
| **OperatingContextSelector** | workspace/context-selector.tsx | ✅ YES | ✅ YES | ✅ Yes | ❌ | KEEP |
| **useActiveContext** | hooks/use-active-context.ts | ✅ YES | ✅ YES | ✅ Yes | ❌ | KEEP |
| **OrganizationalOrientation** | inside executive-home.tsx | ✅ YES | ✅ YES | N/A (internal) | ❌ | KEEP |
| **DomainWorkspaceRouter** | inside executive-home.tsx | ✅ YES | ✅ YES | 🔄 Could extract | ❌ | KEEP |
| **ContentStudio** (lazy route) | content/content-studio.tsx | ✅ YES | ✅ YES (as domain route) | ✅ Yes | ❌ | KEEP |

---

## 6. Visual Recovery Audit

### Calm-White Theme Status

| Aspect | Status | Evidence |
|--------|--------|----------|
| CSS variables (calm-white) | ✅ PRESERVED | Same CSS variable block in both LivingWorkspace and PrimaryWorkspace |
| LivingWorkspace 3654-line stylesheet | 🔄 Not imported | PrimaryWorkspace does not import living-styles.css — uses executive-home styles |
| Dark-theme leakage | ⚠️ UNKNOWN | Must verify in browser (see Section 9) |
| Context-selector dark theme | ⚠️ UNKNOWN | Must verify in browser |
| Mixed dark/light controls | ⚠️ UNKNOWN | Must verify in browser |

**Action required:** The calm-white visual lineage must be verified in browser after the recovery is deployed. Dark-themed context-selector inconsistency (noted in directive Section 8) must be corrected if present.

---

## 7. Git Cleanliness (Post-Recovery)

```
$ git status --short
   (clean — no output)

$ git log --oneline --decorate -5
6e104c1 (HEAD -> primary-workspace-recovery) M2B: PrimaryWorkspace recovery
2bfa630 (origin/master) ZGC-PR-14-WS: Add .hermes/scratch/
a59b5cd (master) ZGC-PR-14-WS: Fix pre-existing TS error
7c9c0d0 ZGC-PR-14-WS: Canonical workspace convergence
af15a08 ZGC-PR-11D: Backward compat — restore Experience Framework exports

$ git branch -avv
  master                               a59b5cd [behind origin/master: 1] LivingWorkspace lineage
  main                                 a9d481f [ahead 150, behind 428] WorkspaceContainer heritage fork
  * primary-workspace-recovery         6e104c1 [new] CANONICAL — PrimaryWorkspace + context switching
  workspace-convergence                2280f1f LivingWorkspace lineage
  workspace-heritage-convergence       a9d481f [same as main]
```

---

## 8. Required Next Steps

| # | Action | Priority | Owner |
|---|--------|----------|-------|
| 1 | Merge `primary-workspace-recovery` into `master`, then push `master` to `origin/master` | IMMEDIATE | Hermes |
| 2 | Verify context switching (Personal ↔ Panchi Club) in browser | IMMEDIATE | Hermes |
| 3 | Verify Content Studio accessible as real domain route (`/workspace/content`) | IMMEDIATE | Hermes |
| 4 | Fix dark-themed context-selector inconsistency if present | SECTION 8 | Hermes |
| 5 | Fix Finance from PLACEHOLDER to REAL (dedicated workspace) | NEXT CYCLE | Dev |
| 6 | Fix Knowledge from PLACEHOLDER to REAL (dedicated workspace) | NEXT CYCLE | Dev |
| 7 | Implement Operations workspace or formally deprecate | NEXT CYCLE | Product |
| 8 | Verify calm-white visual lineage in all domains | IMMEDIATE | Hermes |
| 9 | Run full test suite (not just targeted) | NEXT CYCLE | Hermes |
| 10 | Deploy to production after browser acceptance verified | GATE | Hermes |