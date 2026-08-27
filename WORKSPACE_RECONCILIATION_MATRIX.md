# SHUNYA Workspace Recovery — Domain Reconciliation Matrix

**Forensic Baseline:** ed287e9 (UX-BRIDGE-02) — DomainWorkspaceRouter with 12 organizational domains
**HEAD:** 2bfa630 (ZGC-PR-14-WS) — LivingWorkspace restored, lost organizational sidebar
**Generated:** 2026-08-27

## 1. CRITICAL FINDING: Two Competing Workspace Renderers

| Aspect | LivingWorkspace (ACTIVE) | PrimaryWorkspace (DORMANT) |
|---|---|---|
| Rendered by app.tsx | ✅ Yes (line 445) | ❌ No |
| File | `living-workspace/living-workspace.tsx` (322 lines) | `executive-home/executive-home.tsx` (1966 lines) |
| Route `/workspace/content` | ❌ Modal overlay only | ✅ Real domain workspace |
| 12-domain sidebar | ❌ None | ✅ `OrganizationalOrientation` (260px) |
| Context selector | ✅ `OperatingContextSelector` | ❌ Missing |
| Content Studio | 🔴 Modal (`✍ Content` button) | ✅ Lazy-loaded domain component |
| AI Presence | ✅ `AIPresencePanel` sidebar | ✅ `PresenceIndicator` + `WhatMattersNow` |
| Browser history sync | ✅ `initBrowserHistory()` | ❌ Not integrated |
| Calm-white theme | ✅ | ✅ (same CSS variables) |

## 2. Domain Reconciliation Matrix

### Legend
- **🔴** = Not present / non-functional
- **🟡** = Partial / placeholder / needs improvement
- **🟢** = Functional and real

| Domain | Historical UI (ed287e) | Current UI (LivingWorkspace) | Backend/API | Real Capability | Final Route in PrimaryWorkspace | Status |
|--------|----------------------|------------------------------|-------------|-----------------|--------------------------------|--------|
| **People** | `OrganizationBrowser` | ❌ Not rendered | `GET /api/v1/objects/types` + people permissions | 🟢 Organization browser with hierarchy, search, roles | `people` → `<OrganizationBrowser />` | 🟡 Sidebar exists in PrimaryWorkspace but app renders LivingWorkspace |
| **Work** | `ExecutionWorkspace` | `ExecutiveBriefing` + `RealityStream` | `/api/v1/for2/whoami`, `/api/v1/intention`, `living-store` SSE | 🟢 Execution visibility, work tracking | `work` → `<ExecutionWorkspace />` | 🟡 Partial — LivingWorkspace shows work status but no dedicated workspace |
| **Finance** | `ObjectWorkspaceViewer` via CompositionEngine | ❌ Not rendered | `/api/v1/objects` with filter | 🟢 Universal finance export (ZGC-PR-12C: 7 views x XLSX/CSV, ledger, payments, reports) | `finance` → `<DomainOverview>` (no dedicated component) | 🟡 Backend exists, frontend only shows DomainOverview placeholder |
| **Commercial** | `CommercialWorkspace` | ❌ Not rendered | `/api/v1/objects` with deal/opportunity support | 🟢 Real workspace with opportunities, proposals, deals | `commercial` → `<CommercialWorkspace />` | 🟡 Component exists but not rendered |
| **Marketing** | `MarketingDashboard` | ❌ Not rendered | `/api/v1/ai/chat` + campaign routes | 🟢 Campaign management, AI-powered marketing insights | `marketing` → `<MarketingDashboard />` | 🟡 Component exists but not rendered |
| **Sales** | `SalesPipeline` | ❌ Not rendered | `/api/v1/objects` (proposals, customers, pipeline) | 🟢 Pipeline viewer, lead management, proposals | `sales` → `<SalesPipeline />` | 🟡 Component exists but not rendered |
| **Operations** | `DomainOverview` placeholder | ❌ Not rendered | `/api/v1/objects` | 🟡 Capability not yet implemented (confirmed by DomainOverview text) | `operations` → `<DomainOverview>` | 🔴 Placeholder only — "not yet implemented" per code |
| **Knowledge** | `ObjectWorkspaceViewer` | ❌ Not rendered | `/api/v1/objects` (documents, knowledge) | 🟢 Knowledge store with full CRUD, SQL-backed | `knowledge` → `<DomainOverview>` | 🟡 Backend exists, frontend shows DomainOverview |
| **Outputs** | `OutputsBrowser` | ❌ Not rendered | `/api/v1/objects` | 🟢 Outputs/artifacts browser with filtering | `outputs` → `<OutputsBrowser />` | 🟡 Component exists but not rendered |
| **Memory** | `MemoryBrowser` | `AIPresencePanel` (partial, sidebar) | `/api/v1/for2/whoami`, `living-store` SSE | 🟢 AI memory, observations, reflections | `memory` → `<MemoryBrowser />` | 🟡 Partial — living-store has memory data but not exposed as domain |
| **Relationships** | `RelationshipWorkspace` | ❌ Not rendered | `/api/v1/objects` (relations) | 🟢 Relationship graph, timeline, entity connections | `relationships` → `<RelationshipWorkspace />` | 🟡 Component exists but not rendered |
| **Content** | `ContentStudio` (domain workspace) | 🔴 Modal overlay only (`✍ Content` button) | `/api/v1/content/generate`, `/api/v1/content/history` | 🟢 FULL Content Studio 4.0 — 10 formats, brand voice, media generation, history | `content` → `<ContentStudio />` | 🔴 BLOCKED — Only accessible as modal, not as real domain workspace |
| **Entities** | `EntityManager` | ❌ Not rendered | `/api/v1/objects/types` | 🟢 Dynamic entity type system | `entities` → `<EntityManager />` | 🟡 Component exists but not rendered |

## 3. Content Studio 4.0 — Capability Inventory

The Content Studio component at `frontend/src/components/content/content-studio.tsx` (1646 lines) provides:

| Feature | Status |
|---------|--------|
| Blog posts | 🟢 Full implementation |
| Social posts (Twitter, LinkedIn, Instagram, Threads) | 🟢 Full implementation |
| Email campaigns | 🟢 Full implementation |
| Product descriptions | 🟢 Full implementation |
| Press releases | 🟢 Full implementation |
| SEO meta content | 🟢 Full implementation |
| Ad copy (Google, Facebook, LinkedIn) | 🟢 Full implementation |
| Landing pages | 🟢 Full implementation |
| Content repurposing | 🟢 Full implementation |
| Media generation (via `MediaGenerator`) | 🟢 Integrated |
| History tab with API persistence | 🟢 Full implementation (`GET /api/v1/content/history`, `DELETE /api/v1/content/history/<id>`) |
| Brand voice profiles (5 profiles) | 🟢 Full implementation |
| Tone slider (5 levels) | 🟢 Full implementation |
| **As real domain workspace** | 🔴 BLOCKED — Only opens as modal in LivingWorkspace |
| **Persistent navigation entry** | 🔴 BLOCKED — No domain sidebar entry in rendered workspace |

## 4. Personal vs Organizational Workspace Switching — Current Implementation

### Frontend context store (`use-active-context.ts`)
```
currentOrgId: number | null
init(): fetch /api/v1/for2/whoami → sets currentOrgId
switchContext(orgId): POST /api/v1/for2/organizations/{id}/switch or /switch/personal
```

### Identity model (`app/workspace/models.py`)
```
WorkspaceType enum: PERSONAL, BUSINESS, TEAM, PROJECT, FAMILY, COMMUNITY, NONPROFIT, CREATOR, EDUCATION, OTHER
CapabilityPolicy: capability sets per type
resolve_context(session, workspace_id, identity) → canonical context
```

### Current rendering path
```
app.tsx phase='ready'
  → AuthenticatedWorkspace
    → LivingWorkspace (no domain switching)
      → OperatingContextSelector in TopBar (org switch only, no workspace type switch)
      → No workspace-type-aware rendering
```

### What's missing for Personal↔Org switching
1. ❌ LivingWorkspace has NO personal vs organizational mode
2. ❌ `OperatingContextSelector` switches org context but doesn't change the rendered workspace
3. ❌ No workspace-type-specific domain filtering
4. ❌ PrimaryWorkspace's `OrganizationalOrientation` sidebar shows ALL domains regardless of workspace type
5. ❌ No data scope rehydration on context switch
6. ❌ `domain availability` varies by workspace type but is not checked

## 5. Context Model Convergence — Runtime Path Map

```
Frontend selection (OperatingContextSelector / domain click)
    ↓
useActiveContext.set({ currentOrgId })
    ↓
LivingWorkspace/useLivingStore (no workspace awareness)
  OR
PrimaryWorkspace/DomainWorkspaceRouter (domain aware but not org-aware)
    ↓
API calls via fetchWithAuth() → X-Identity-Id + X-Workspace-Id
    ↓
Flask backend session: session["current_workspace_id"], session["current_workspace_type"]
    ↓
app/workspace/models.py: resolve_context(session, workspace_id, identity)
    ↓
Authorization: WorkspaceMembership-based tenant isolation
    ↓
CapabilityPolicy: capability sets per WorkspaceType
    ↓
Response
```

### Multiple competing context keys found

| Key | Location | Purpose | Authoritative? |
|-----|----------|---------|---------------|
| `for2 current_org_id` | `use-active-context.ts` | Current organization context | ✅ Primary for org |
| `active_workspace_id` | `workspace/store.ts` | Workspace runtime state | ✅ Primary for workspace |
| `current_workspace_id` | Flask `session` | Legacy session workspace | 🟡 Compatibility adapter |
| `current_workspace_type` | Flask `session` | Legacy session workspace type | 🟡 Compatibility adapter |

## 6. Recovery Roadmap

### Phase 1: Render PrimaryWorkspace
- Replace `LivingWorkspace` with `PrimaryWorkspace` in `app.tsx`
- Add `OperatingContextSelector` to `PrimaryWorkspace`'s `PrimaryFocusArea` top bar
- Integrate `initBrowserHistory()` from living-workspace into primary workspace

### Phase 2: Domain Workspace Verification
- Verify each domain workspace component renders correctly
- Fix routing for Financial and Operations domains (currently `DomainOverview` placeholders)
- Ensure Content Studio renders as a proper domain workspace (not modal)

### Phase 3: Personal ↔ Org Context Switching
- Implement workspace-type filtering in `OrganizationalOrientation` sidebar
- Add data scope rehydration on context switch
- Verify Personal→Org, Org→Personal, Org A→Org B transitions
- No `window.location.reload()` dependency

### Phase 4: Context Model Convergence
- Converge to single canonical authority chain
- Legacy keys (`current_workspace_id`) behind compatibility adapter only

## 7. STOP Condition

> Do not claim success because the page is white.
> Do not claim success because LivingWorkspace renders.
> Do not claim success because Content Studio opens.

Success exists only when **all 12 domains are accessible as real organizational workspace routes** with verified functionality, **Content Studio 4.0 is a primary domain workspace** (not a modal), and **Personal↔Organization context switching** changes the rendered workspace with data scope isolation.