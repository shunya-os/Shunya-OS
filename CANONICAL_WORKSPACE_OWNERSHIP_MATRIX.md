# SHUNYA — Canonical Workspace Ownership Matrix

> Generated: 2026-08-27 | Directive: M2B (Extended)
> Purpose: Establish one authoritative authenticated workspace architecture

## 1. Root Workspace Renderers

| Component | File | Historical Role | Current Role | Active? | Canonical? | Depends On | Migration Decision |
|-----------|------|----------------|--------------|---------|------------|------------|-------------------|
| **PrimaryWorkspace** | `frontend/src/components/executive-home/executive-home.tsx` (1966 lines) | Organizational workspace root (since ed287e9) | **CANONICAL ROOT** | ✅ YES | ✅ YES | OrganizationalOrientation, PrimaryFocusArea, CommandBar, AIPresencePanel, OperatingContextSelector | **KEEP** — canonical authenticated workspace root |
| LivingWorkspace | `frontend/src/components/living-workspace/living-workspace.tsx` (322 lines) | Simplified workspace shell (post-7c9c0d0) | Superseded by PrimaryWorkspace | ❌ NO | ❌ NO | living-store, AI panels, PresenceIndicator | **DEPRECATE** as root — extract reusable sub-components (AIPresencePanel, living-store, PresenceIndicator) |
| WorkspaceContainer | `frontend/src/components/workspace/workspace-container.tsx` | Zone 3 content area (main branch) | Heritage fork only | ❌ NO | ❌ NO | WorkspaceBar, WorkspaceShell, CompositionEngine | **KEEP** on main branch as evidence — do not port |
| WorkspaceBar | `frontend/src/components/workspace/workspace-bar.tsx` | Three-zone shell header (main branch) | Heritage fork only | ❌ NO | ❌ NO | zone management | **KEEP** on main branch as evidence |

## 2. Sub-Components (Shared / Reusable)

| Component | File | Owner | Used By | Active? | Notes |
|-----------|------|-------|---------|---------|-------|
| OperatingContextSelector | `frontend/src/components/workspace/context-selector.tsx` | PrimaryWorkspace | PrimaryWorkspace (PrimaryFocusArea) | ✅ YES | Personal/Org context dropdown |
| useActiveContext | `frontend/src/hooks/use-active-context.ts` | PrimaryWorkspace | PrimaryWorkspace, context-selector | ✅ YES | Zustand store, fetches /whoami |
| OrganizationalOrientation | embedded in `executive-home.tsx` | PrimaryWorkspace | PrimaryWorkspace | ✅ YES | 14-domain sidebar navigation |
| PrimaryFocusArea | embedded in `executive-home.tsx` | PrimaryWorkspace | PrimaryWorkspace | ✅ YES | Main content area |
| CommandBar | embedded in `executive-home.tsx` | PrimaryWorkspace | PrimaryWorkspace | ✅ YES | "Ask SHUNYA" command surface |
| AIPresencePanel | embedded in `executive-home.tsx` | PrimaryWorkspace | PrimaryWorkspace | ✅ YES | SHUNYA presence + awareness |
| AIPresencePanel | `frontend/src/components/living-workspace/living-presence.tsx` | LivingWorkspace | LivingWorkspace (dead) | ❌ NO | Could extract to shared |
| living-store | `frontend/src/components/living-workspace/living-store.tsx` | LivingWorkspace | LivingWorkspace, PrimaryWorkspace | ✅ YES | Shared via imports |
| useWorkspaceStore | `frontend/src/runtimes/workspace/store.ts` | Runtime layer | All workspace variants | ✅ YES | Object tab management |
| useWorkspaceHydration | `frontend/src/hooks/workspace-hooks.ts` | App shell | app.tsx | ✅ YES | Hydrates workspace state |
| DomainWorkspaceRouter | embedded in `executive-home.tsx` | PrimaryWorkspace | PrimaryWorkspace | ✅ YES | Maps routes to domain components |

## 3. CSS / Styling

| Stylesheet | Owner | Used By | Active? |
|------------|-------|---------|---------|
| Executive home styles (embedded) | PrimaryWorkspace | executive-home.tsx | ✅ YES |
| living-styles.css (3654 lines) | LivingWorkspace | living-workspace.tsx | ❌ NO (dead import) |
| Workspace styles (embedded in container) | WorkspaceContainer | workspace-container.tsx | ❌ NO (heritage fork) |

## 4. State Stores

| Store | File | Purpose | Active? | Notes |
|-------|------|---------|---------|-------|
| useActiveContext | hooks/use-active-context.ts | Org/Personal context | ✅ YES | Canonical context store |
| useWorkspaceStore | runtimes/workspace/store.ts | Object tab management | ✅ YES | Different from context |
| useLivingStore | living-workspace/living-store.ts | AI awareness, SSE state | ✅ YES | Shared by both variants |
| useActiveWorkspace | hooks/workspace-hooks.ts | Active workspace resolution | ✅ YES | Used by container |

## 5. Current Render Tree (app.tsx)

```
AuthenticatedWorkspace
  └─ <TokenProvider>
       └─ <PrimaryWorkspace />   ← CANONICAL ROOT
            ├─ <OrganizationalOrientation />   ← 14-domain sidebar
            ├─ <PrimaryFocusArea />
            │   ├─ <OperatingContextSelector /> ← Personal/Org dropdown
            │   └─ {domain} route → lazy-loaded component
            ├─ <CommandToActionBridge />        ← Command surface
            └─ <AIPresencePanel />             ← SHUNYA presence
```

## 6. Dead / Dormant Components (Not Active but Still Importable)

| Component | File | Last Active | Why Dead |
|-----------|------|-----------|----------|
| LivingWorkspace (as root) | living-workspace/living-workspace.tsx | SHA 2bfa630 | Replaced by 6e104c1 (PrimaryWorkspace recovery) |
| WorkspaceContainer | workspace/workspace-container.tsx | SHA a9d481f (main branch) | Heritage fork — not merged |
| WorkspaceBar | workspace/workspace-bar.tsx | SHA a9d481f (main branch) | Heritage fork — not merged |
| WorkspaceShell | workspace/workspace-shell.tsx | SHA a9d481f (main branch) | Heritage fork — not merged |

## 7. Summary: Canonical Stack

```
Layer                │ Canonical Choice
─────────────────────┼─────────────────────────────
Workspace Root       │ PrimaryWorkspace (executive-home.tsx)
Sidebar              │ OrganizationalOrientation (embedded)
Content Area         │ PrimaryFocusArea (embedded)
Context Store        │ useActiveContext (hooks/use-active-context.ts)
Org Switch           │ OperatingContextSelector (workspace/context-selector.tsx)
Tab Management       │ useWorkspaceStore (runtime store — separate concern)
AI/Intelligence      │ AIPresencePanel, living-store (shared)
Command Surface      │ CommandToActionBridge (actions/)
```

No competing root workspace architectures remain wired. LivingWorkspace, WorkspaceContainer, and WorkspaceBar are all dead code — not wired into app.tsx.