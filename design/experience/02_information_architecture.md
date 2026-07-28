# SHUNYA Information Architecture

> **Canonical Reference — Phase X1**
> Defines the global hierarchy, object-centric organization, workspace topology, and relationship navigation. Every frontend implementation must conform to this architecture.

---

## 1. Core Principle: Object-Centric Hierarchy

SHUNYA has no module hierarchy. There is no "CRM module" containing "Customers" containing "Customer Detail." Instead:

```
Workspace
  └─ Object (the active entity)
       ├─ Context
       ├─ Timeline
       ├─ Actions
       ├─ Knowledge
       └─ AI
```

Everything revolves around **the object currently being worked on**. Not around modules, pages, or features.

### Why Object-Centric?

| Module-First Problem | Object-First Solution |
|---------------------|----------------------|
| User must know which module contains the thing they need | User searches for the object directly |
| Navigation is a tree of features | Navigation is a graph of relationships |
| Each module has a different layout | Every object has the same workspace architecture |
| Cross-module workflows require context switching | Cross-object workflows are natural relationship navigation |
| Adding a new feature means adding a new module | Adding a new object type reuses the existing architecture |
| AI cannot help across modules | AI operates on objects and their relationships, not on module boundaries |

---

## 2. Global Hierarchy

### Level 1: Workspace

The workspace is the top-level container. It defines the domain of focus. A workspace is defined by the **type of object** it surfaces by default.

There are exactly 14 canonical workspaces (defined in 03_workspace_model.md). A user may customize which workspaces appear in their navigation, but the canonical set is immutable.

### Level 2: Object

The active entity. Every workspace has a primary object type, but any object can be viewed in any workspace relevant to it.

### Level 3: Context

The user's current focus within an object. Context is determined by:
- Which section of the object workspace is open (Timeline, Knowledge, Actions, etc.)
- Which relationship tab is selected
- Which AI resident panel is active
- Scroll position within each section

### Level 4–7: Sub-Layers

```
Level 4: Timeline          — ordered history of events, changes, decisions
Level 5: Actions           — available and pending actions on the object
Level 6: Knowledge         — accumulated facts, documents, notes, analysis
Level 7: AI                — AI resident conversation, suggestions, analysis
```

These sub-layers are sections within the object workspace. They are not navigational destinations.

---

## 3. Workspace Topology

### Three-Zone Layout

Every workspace follows a three-zone layout:

```
┌────────────────────────────────────────────┐
│  Zone 1: Global Navigation Bar             │
│  [Logo] [Search] [Workspace Switcher]      │
│  [History] [Settings] [User]               │
├────────────────────┬───────────────────────┤
│  Zone 2:           │  Zone 3:              │
│  Context Panel     │  Content Area         │
│                    │                       │
│  - Current object  │  - Object workspace   │
│  - Relationships   │  - Sections           │
│  - Quick actions   │  - Data               │
│  - AI resident     │  - Actions            │
│  (collapsible)     │                       │
└────────────────────┴───────────────────────┘
```

**Zone 1** — Fixed. Present on every workspace. Does not change.
**Zone 2** — Contextual. Can be collapsed to a thin strip or hidden entirely.
**Zone 3** — Primary content. Always visible. Expands when Zone 2 is collapsed.

---

## 4. Navigation Model

### Types of Navigation

| Type | Trigger | Behavior |
|------|---------|----------|
| **Workspace switch** | Click workspace icon, command palette, keyboard shortcut | Content area transitions to the new workspace's default view. Context Panel updates to show the new workspace's primary context. |
| **Object selection** | Click object link, relationship, search result | Object workspace opens in the Content Area. Context Panel updates to the selected object. |
| **Section switch** | Click section tab within object workspace | Content Area scrolls or transitions to the selected section. Context Panel remains focused on the same object. |
| **Relationship follow** | Click relationship in Context Panel | Navigates to the related object. The previous object goes into the history stack. |
| **Deep link** | External link, bookmark, notification | Opens directly to the object and section specified. Restores the full workspace context. |

### No Page-Jumping

- Navigation never causes a full page load.
- All navigation is client-side, instant, and animated with spatial continuity.
- The URL updates for deep-linkability but never causes a reload.

### Forward/Back Model

- Forward/back navigates the object history stack, not the page history stack.
- Each workspace has its own history stack.
- Back always returns to the previous object — not to a previous page.
- The history stack is preserved across sessions.

---

## 5. Search Architecture

Search is the primary navigation mechanism. It is not a secondary feature.

### Search Behavior

| State | Behavior |
|-------|----------|
| **Command palette (Ctrl+K)** | Opens overlay. Defaults to universal object search. |
| **Typing** | Real-time results after 2 characters. Results grouped by object type. |
| **Results** | Each result shows: object name, type icon, primary identifier, status, confidence |
| **Selection** | Opens the object in the current workspace. If the object belongs to a different workspace, switches workspace. |
| **No results** | Shows: "No objects found. Would you like to search across all fields?" and "Create new [object type]?" |
| **Global search bar** | Always visible in Zone 1. Same behavior as command palette. |

### Search Scope

| Scope | Description |
|-------|-------------|
| **Universal** | All objects across all workspaces. Default scope. |
| **Workspace-scoped** | Objects within the current workspace. Prefixed with workspace name (e.g., "proj: launch"). |
| **Object-scoped** | Content within the current object. Prefixed with object reference. |
| **AI-assisted** | Natural language query that searches across relationships, knowledge, and timeline. |

---

## 6. Recent Items & History

### Recent Items

- Recent items are per-workspace.
- Maximum: 20 items per workspace.
- Items are ordered by last access time.
- Pinned items appear at the top with a pin indicator.
- Recent items are accessible from the Context Panel and the command palette.

### History

- Object history is per-workspace.
- Each workspace maintains a stack of up to 50 objects.
- History includes: object ID, object name, timestamp, context (section), and how it was reached (search, relationship, direct navigation).
- History is available from the Context Panel's history tab.

### Forward/Back Navigation

| Action | Behavior |
|--------|----------|
| **Back** | Returns to the previous object in the current workspace's history. Restores the section and scroll position. |
| **Forward** | Advances to the next object in the history stack (if back was used). |
| **Back to workspace root** | Returns to the workspace's default view (no object selected). |

---

## 7. Breadcrumb System

Breadcrumbs in SHUNYA are object-relationship chains, not page-path chains.

### Format

```
[Workspace] > [Current Object] > [Relationship Type] > [Related Object]
```

### Rules

- Breadcrumbs are optional — they appear only when the user is more than one level deep into a relationship chain.
- Clicking any breadcrumb segment navigates to that level.
- The breadcrumb is context-sensitive: it shows the path taken, not the full tree.
- Breadcrumbs are always visible at the top of the Content Area, below Zone 1.

---

## 8. Workspace Transitions

### Switching Workspaces

When switching workspaces:

1. The current workspace's state (scroll position, open panels, history stack) is serialized and preserved.
2. The target workspace opens with its last-used state restored.
3. If the target workspace was never visited, it opens in its default state.
4. The transition animation is a horizontal slide (300ms, ease-out) that communicates spatial relationship.

### Entering and Exiting Objects

| Direction | Animation | Meaning |
|-----------|-----------|---------|
| Enter object | Content zooms in / slides up (200ms) | "We are now focused on this object" |
| Exit object (back) | Content zooms out / slides down (200ms) | "Returning to the previous context" |
| Switch object (forward) | Content slides left (250ms) | "Moving to a related object" |
| Switch object (back) | Content slides right (250ms) | "Returning to the previous object" |

---

## 9. Information Organization Within Objects

Every object workspace follows a fixed section organization:

```
┌────────────────────────────────────────┐
│  Header                                │
│  ┌─────┐ ┌─────────────────────────┐  │
│  │ Icon│ │ Name / Title            │  │
│  │     │ │ Status · Type · ID      │  │
│  └─────┘ │ Confidence: ████░░ 0.82 │  │
│          │ [Actions] [Share] [...]  │  │
│          └─────────────────────────┘  │
├────────────────────────────────────────┤
│  Executive Summary                     │
│  ┌──────────────────────────────────┐ │
│  │ 3-line AI-generated summary     │ │
│  │ Key metric · Trend · Next step  │ │
│  └──────────────────────────────────┘ │
├──────┬─────────────────────────────────┤
│      │  Tab Bar                        │
│ Nav  │  [Identity] [Relationships]     │
│ Side │  [Timeline] [Knowledge]         │
│      │  [Tasks] [Execution] [Metrics]  │
│      │  [Documents] [AI] [History]     │
│      ├─────────────────────────────────┤
│      │  Section Content               │
│      │                                 │
│      │  (varies by selected tab)      │
│      │                                 │
└──────┴─────────────────────────────────┘
```

---

## 10. Content Priority Within Sections

### Information Density Rules

| Zone | Density | Rationale |
|------|---------|-----------|
| Header | High | Identity and orientation — must be scannable at a glance |
| Summary | Medium | Decision support — enough to act, not enough to read |
| Tab content | User-determined | The user controls expansion and depth |
| Context Panel | Medium | Always-visible reference — never overwhelming |
| AI Resident | Low | Chat-like density — spacious, readable |

### Section Internal Hierarchy

Within each section:

1. **Summary view** (default): collapsed sections, key metrics, expandable content
2. **Detail view** (expanded): full content with all sub-sections visible
3. **Edit view** (when applicable): inline editing with visible save state

---

## 11. Information Architecture Invariants

1. **Every screen is anchored to exactly one object.** There is no "dashboard page" — only the Home workspace with no object selected.
2. **No concept of "page" exists in the IA.** There are workspaces, objects, sections, and overlays. No pages.
3. **Navigation is object-relationship graph traversal, not page-to-page.** Every click navigates via a relationship.
4. **Search is the primary navigation mechanism.** Menus and navigation bars are secondary.
5. **The hierarchy is depth-agnostic.** Following relationships can go arbitrarily deep. Breadcrumb and back always provide orientation.
6. **State is never lost.** Forward, back, workspace switch, session reopen — none lose state.
7. **Workspace topology is universal.** Every workspace has the same three-zone layout. Only the content differs.
8. **Section order is fixed.** Every object workspace has the same tab order. Objects may omit irrelevant sections but may not reorder them.
9. **Content density adapts to role.** An executive sees summary-dense views. An analyst sees detail-expanded views. The user controls their default.
10. **URLs are stable and human-readable.** Every object has a canonical URL. Sections have anchors. URLs do not change on data updates.