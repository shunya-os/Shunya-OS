# SHUNYA Information Architecture

> **Canonical Frontend Document · Phase C3 Parallel**
> **Status: CANONICAL — Implementation-Independent IA Specification**
> **Version: 1.0**
> **Derived From: 08_experience_canon.md (Experience Canon)**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [One Continuous Surface Principle](#2-one-continuous-surface-principle)
3. [Navigation Architecture](#3-navigation-architecture)
4. [Screen Hierarchy](#4-screen-hierarchy)
5. [Object Taxonomy](#5-object-taxonomy)
6. [Workspace Organization](#6-workspace-organization)
7. [Context Preservation Structure](#7-context-preservation-structure)
8. [URL Schema](#8-url-schema)
9. [Responsive IA Adaptation](#9-responsive-ia-adaptation)
10. [Relationship to Canonical Documents](#10-relationship-to-canonical-documents)

---

## 1. Purpose

This document defines the information architecture of SHUNYA — the structural organization of screens, navigation, objects, and workspaces. It is the implementation specification derived from the Experience Canon (08) and is the authoritative blueprint for all frontend development.

**This document defines what exists and how it connects. It does not define visual styling (see DESIGN_SYSTEM.md) or interaction behavior (see DESKTOP_INTERACTION_MODEL.md).**

---

## 2. One Continuous Surface Principle

### 2.1 Definition

SHUNYA is **not a collection of pages**. It is a single continuous surface through which the user navigates by shifting focus between objects, workspaces, and relationships. There is no page load, no page transition, and no hierarchy of pages.

The One Continuous Surface means:

- **No page boundaries** — the user never experiences a "page load" or a "page refresh." State transitions are seamless.
- **Focus shifting, not navigation** — the user moves their attention from one object to another, not from one URL to another.
- **Spatial memory preserved** — the user's position in the object graph is always maintained; returning to a previous focus is a shift, not a reload.
- **Workspace as container** — the workspace is the persistent container; objects are the focal targets within it.

### 2.2 Visual Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    TOP BAR (persistent)                          │
│  [Workspace Name]  ·  [Object Type]  ·  [Object Identity]       │
│  [Search] [Create] [AI] [Notifications] [Profile]               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┬─────────────────────────────────┬──────────────┐  │
│  │  OBJECT   │     FOCAL OBJECT (the surface)   │  RELATIONSHIP│  │
│  │  BROWSER  │                                   │  PANEL      │  │
│  │  ──────── │  The object is the center.        │  ────────── │  │
│  │           │  Everything else recedes.          │             │  │
│  │  Related  │  Whitespace (70%) frames it.       │  Connected  │  │
│  │  objects  │  Content (20%) describes it.       │  objects    │  │
│  │  in this  │  Controls (10%) act on it.         │             │  │
│  │  workspace│                                   │             │  │
│  └──────────┴─────────────────────────────────┴──────────────┘  │
│                                                                  │
│  Object Breadcrumb: [Workspace] > [Object Type] > [Object Name]  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 What the Continuous Surface Replaces

| Traditional Page Concept | SHUNYA Continuous Surface Equivalent |
|-------------------------|--------------------------------------|
| "Homepage" | Default workspace with last focal object |
| "Settings page" | Profile object with embedded settings panel |
| "Dashboard" | Dashboard-type workspace |
| "Detail page" | Focal object with expanded disclosure |
| "Search results page" | Object search overlay |
| "Notifications page" | Notification panel (overlay, not a page) |
| "Login page" | Identity resolution overlay |
| "404 page" | Object-not-found state within the surface |

---

## 3. Navigation Architecture

### 3.1 Navigation Primitives

SHUNYA has exactly **five navigation primitives**:

| Primitive | Trigger | Behavior | Scope |
|-----------|---------|----------|-------|
| **Object Search** | Cmd+K / Click search bar | Opens overlay, searches all objects across all workspaces | Global |
| **Workspace Switch** | Workspace menu / Cmd+Shift+W | Changes workspace context, preserves focal object if possible | Global |
| **Object Focus** | Click on any object reference | Shifts focal object to the selected object, loads its detail | Within workspace |
| **Relationship Follow** | Click on a relationship link | Follows relationship to the related object, which becomes the new focal object | Within workspace |
| **AI Collaboration** | Cmd+Shift+K / AI button | Opens AI collaborator panel contextual to the current object | Within workspace |

### 3.2 Navigation Rules

1. **Every navigation action is a focus shift, not a page load.** The surface never reloads.
2. **The breadcrumb is always visible** and shows the current position: `[Workspace] > [Object Type] > [Object Name]`.
3. **Object Search is always accessible** and is the primary navigation method.
4. **Workspace switching preserves the focal object** when the object exists in the target workspace.
5. **Relationship following is reversible** — the back action returns to the previous focal object.
6. **No navigation is more than 3 clicks from any object** to any related object (see 08 §4.1.2).

### 3.3 Navigation Surface Anatomy

```
┌─────────────────────────────────────────────────────────────────────┐
│ TOP BAR                                                              │
│ ┌──────────────┐  ┌──────────┐  ┌──────┐  ┌──┐  ┌──┐  ┌───────┐   │
│ │ Workspace ▼  │  │ Object ▼│  │ ⚡ AI │  │🔍│  │🔔│  │ 👤   │   │
│ │ (current)    │  │ (type)   │  │      │  │  │  │  │  │       │   │
│ └──────────────┘  └──────────┘  └──────┘  └──┘  └──┘  └───────┘   │
├─────────────────────────────────────────────────────────────────────┤
│ LEFT SIDEBAR (optional, collapsible, workspace-relative)            │
│                                                                     │
│ OBJECT BROWSER                                                      │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ Workspace Objects                                                ││
│ │                                                                  ││
│ │ ● Decision: "Q3 Budget Approval"  ← current focal               ││
│ │   ├── Related: Document "Q3 Proposal"  (click to follow)         ││
│ │   ├── Related: Task "Compile Revenue Data"                       ││
│ │   └── Related: Human "Alice" (owner)                             ││
│ │                                                                  ││
│ │ ○ Task: "Hire 3 Engineers"                                       ││
│ │ ○ Event: "Budget Review Meeting"                                 ││
│ │ ○ Outcome: "Q2 Results"                                          ││
│ │                                                                  ││
│ │ [View all workspace objects ▸]                                   ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ FOCAL OBJECT AREA (primary surface)                                 │
│                                                                     │
│ Decision: Q3 Budget Approval ──────────────────────────────────     │
│                                                                     │
│  Status: IN_REVIEW · Owner: Alice · Created: 2 hours ago            │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                │ │
│  │  [Object content — 20% of the surface]                         │ │
│  │  Context, description, rationale, attachments.                 │ │
│  │                                                                │ │
│  │  [Whitespace — 70% of the surface frames the content]          │ │
│  │                                                                │ │
│  │  [Controls — 10% of the surface]                               │ │
│  │  [Approve] [Request Changes] [Delegate] [Archive]              │ │
│  │                                                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.4 Keyboard Navigation

| Key Combination | Action |
|----------------|--------|
| `Cmd+K` | Object Search (global) |
| `Cmd+Shift+K` | AI Collaboration |
| `Cmd+Shift+W` | Workspace Switcher |
| `Cmd+[` | Back to previous focal object |
| `Cmd+]` | Forward to next focal object |
| `Cmd+Shift+F` | Focus object browser |
| `Escape` | Clear search / close overlay / return to focal object |
| `Tab` | Move between object fields |
| `Enter` | Open selected object / follow relationship |
| `↑/↓` | Navigate object browser or search results |
| `Space` | Quick action on current focal object |

---

## 4. Screen Hierarchy

### 4.1 Surface Layers

The SHUNYA surface is composed of exactly **three layers**:

| Layer | Z-Index | Content | Behavior |
|-------|---------|---------|----------|
| **Base** | 0 | Top bar + object browser + focal object area + relationship panel | Persistent, always visible |
| **Overlay** | 100 | Search, notifications, workspace switcher, object type picker | Modal overlays that appear on top of the base |
| **AI Panel** | 200 | AI collaborator conversation, object-linked AI context | Slide-over panel from the right edge |

### 4.2 Screen Types

SHUNYA does not have "screens" in the traditional sense. It has **surface states**:

| Surface State | When It Appears | Transition |
|--------------|-----------------|------------|
| **Default Workspace** | On load, on workspace switch | Base layer |
| **Focal Object** | After selecting an object | Object content fills the focal area |
| **Object Search** | After Cmd+K | Overlay, dims background |
| **AI Collaboration** | After Cmd+Shift+K | Slide-over panel from right |
| **Notification Panel** | After clicking bell icon | Overlay from right |
| **Workspace Switcher** | After Cmd+Shift+W | Overlay, centered |
| **Object Not Found** | When an object reference is invalid | Surface state within focal area |
| **Empty Workspace** | When a workspace has no objects | Surface state with guidance |

### 4.3 Surface State Machine

```
LOAD ──────────────────────────────────────────────────────────────────┐
  │                                                                      │
  ▼                                                                      │
Default Workspace ◄─────────────────────────────────────────────────────┘
  │
  ├── Select object ─────► Focal Object (primary interaction)
  │                            │
  │                            ├── Select relationship ──► New Focal Object
  │                            ├── AI button ────────────► AI Collaboration (overlay)
  │                            ├── Search ───────────────► Object Search (overlay)
  │                            │                              │
  │                            │                              ├── Select result ──► Focal Object
  │                            │                              └── Escape ────────► Return to prior
  │                            ├── Notifications ───────────► Notification Panel (overlay)
  │                            └── Escape (empty) ──────────► Default Workspace
  │
  ├── Cmd+K ──────────────────► Object Search (overlay)
  ├── Cmd+Shift+K ────────────► AI Collaboration (overlay)
  ├── Cmd+Shift+W ────────────► Workspace Switcher (overlay)
  └── Bell icon ──────────────► Notification Panel (overlay)
```

### 4.4 Surface State Rules

1. **One overlay at a time.** Opening a new overlay closes the current one.
2. **AI Panel is the only exception** — it can coexist with other overlays, appearing above them.
3. **Escape always returns to the focal object.** Escape from an overlay closes it. Escape from the focal object returns to the default workspace state.
4. **The top bar is always visible** in all states.
5. **The object browser is always visible** in base layer states, collapsible at the user's discretion.

---

## 5. Object Taxonomy

### 5.1 Object Type Hierarchy

The 18 canonical object types (03 Business Canon) are organized into 6 ontological categories for navigation:

| Category | Object Types | Navigation Group |
|----------|-------------|-----------------|
| **Identity** | Identity, Human, Organization | Who |
| **Work** | Workspace, Task, Commitment, Workflow | What |
| **Communication** | Conversation, Event, Document | How |
| **Intelligence** | Observation, Knowledge, Memory, Evidence | Why |
| **Decisions** | Decision, Outcome | Which |
| **Resources** | FinancialObject, Relationship | What With |

### 5.2 Object Browser Organization

The object browser lists objects within the current workspace, organized by:

1. **Recent** (default) — objects sorted by last interaction time
2. **Type** — grouped by object type within the category hierarchy
3. **Relationship** — organized by proximity to the current focal object
4. **Custom** — user-defined object collections (pinned, tagged, saved searches)

### 5.3 Object Identity Display

Every object in the browser displays:

```
[Type Icon]  Object Name
             Owner · Status · Last Modified
```

- **Type Icon** — a consistent icon per object type (see DESIGN_SYSTEM.md)
- **Object Name** — the object's primary identity label
- **Status** — current lifecycle status (visual indicator)
- **Owner** — the human or identity that owns the object

---

## 6. Workspace Organization

### 6.1 Workspace Types

| Type | Purpose | Default Object Scope | Persistence |
|------|---------|---------------------|-------------|
| **Project** | Bounded work output | Task, Decision, Document, Event, Commitment, Outcome | Session + device |
| **Conversation** | Communication history | Conversation, Decision, Document, Evidence | Session + device |
| **Knowledge** | Understanding synthesis | Knowledge, Observation, Evidence, Document, Memory | Session + device |
| **Dashboard** | Awareness and metrics | Event, Outcome, Observation, Decision, FinancialObject | Session + device |
| **Personal** | Private workspaces | Memory, Document, Decision, Observation, Task | Session + device |

### 6.2 Workspace State

Each workspace maintains independent state:

| State Element | Scope | Persistence |
|--------------|-------|-------------|
| Current focal object | Per-workspace | Session-persistent |
| Object browser scroll position | Per-workspace | Session-persistent |
| Relationship panel open/closed | Per-workspace | Session-persistent |
| Object disclosure level | Per-object-type | User-persistent |
| AI conversation history | Per-object | User-persistent (object-linked) |

### 6.3 Workspace Navigation

- **Workspace list** — accessible from the workspace dropdown in the top bar
- **Workspace search** — object search includes workspace objects; workspace type is a filter
- **Workspace creation** — triggered from the workspace switcher overlay
- **Workspace deletion** — requires confirmation; objects are unlinked, not deleted

---

## 7. Context Preservation Structure

### 7.1 Session State

The following state is preserved within a session:

```
Session State
├── Current workspace ID
├── Current focal object ID
├── Focal object disclosure level
├── Object browser: scroll position, sort order, filter
├── Relationship panel: open/closed, active relationship
├── AI panel: open/closed, conversation position
├── Undo stack (per-workspace)
└── Navigation history (per-workspace, max 50 entries)
```

### 7.2 Cross-Session State

The following state is preserved across sessions:

```
Persistent State
├── Last workspace ID
├── Last focal object ID (per workspace)
├── Recent objects list (global, max 20)
├── Pinned objects (per workspace, user-defined)
├── Object disclosure preferences (per object type, per user)
├── AI conversation history (per object, indexed)
└── Workspace list (persistent, user-created)
```

### 7.3 State Storage Architecture

| State Type | Storage | Access Pattern |
|-----------|---------|---------------|
| Session state | In-memory (client-side) | Direct read, instant |
| Cross-session state | LocalStorage / IndexedDB | Async read on load, write on change |
| Workspace state | Server-side (workspace object) | API call on workspace switch |
| AI conversation history | Server-side (object-linked) | API call on AI panel open |

---

## 8. URL Schema

### 8.1 URL Structure

SHUNYA uses a flat URL schema that reflects the object graph, not a page hierarchy:

```
/workspace/<workspace_id>/<object_type>/<object_id>
```

### 8.2 URL Patterns

| Pattern | Behavior |
|---------|----------|
| `/` | Redirect to last workspace |
| `/workspace/<id>` | Open workspace with last focal object |
| `/workspace/<id>/<type>/<obj_id>` | Open workspace with specific focal object |
| `/search?q=<query>` | Pre-populate object search with query |
| `/ai/<object_type>/<object_id>` | Open AI panel contextual to object |

### 8.3 URL Rules

1. **URLs are shareable** — any URL opens the correct surface state.
2. **URLs are not pages** — the URL is a surface state encoding, not a page identifier.
3. **URLs are readable** — object IDs are UUIDs, but the URL also includes the object type for readability.
4. **URL changes are surface transitions** — changing the URL triggers a focus shift, not a page load.
5. **Deep linking works** — opening a URL restores the workspace and focal object.

---

## 9. Responsive IA Adaptation

### 9.1 Breakpoint IA Changes

| Breakpoint | Width | IA Changes |
|-----------|-------|------------|
| **Desktop XL** | ≥ 1400px | Full IA: object browser + focal area + relationship panel simultaneously |
| **Desktop** | 1200–1399px | Full IA: object browser collapsible, relationship panel always visible |
| **Small Desktop** | 900–1199px | Object browser hidden by default, relationship panel collapsible |
| **Tablet** | 600–899px | Single column: object browser + relationship panel become overlays |
| **Mobile** | < 600px | Single column, bottom navigation bar, all panels become overlays or bottom sheets |

### 9.2 Object Browser Adaptation

| Breakpoint | Object Browser Behavior |
|-----------|----------------------|
| Desktop | Persistent sidebar, ~300px |
| Small Desktop | Collapsible, slides in from left |
| Tablet | Overlay panel, triggered by hamburger or swipe |
| Mobile | Bottom sheet, triggered by "Show objects" button |

### 9.3 Relationship Panel Adaptation

| Breakpoint | Relationship Panel Behavior |
|-----------|---------------------------|
| Desktop | Persistent sidebar, ~280px |
| Small Desktop | Persistent, narrow, ~220px |
| Tablet | Slide-over panel from right |
| Mobile | Bottom sheet |

### 9.4 Top Bar Adaptation

| Breakpoint | Top Bar Changes |
|-----------|----------------|
| Desktop | Full: workspace name, object type, search, actions |
| Tablet | Compact: workspace name, icons without labels |
| Mobile | Minimal: hamburger menu, workspace name, profile icon |

---

## 10. Relationship to Canonical Documents

| Document | Relationship |
|----------|-------------|
| **00_universal_ontology.md** | IA structures ontological concepts into navigable surfaces |
| **02_shunya_constitution.md** | Article 9 "Calm Before Complexity" mandates the flat, calm navigation model |
| **03_business_canon.md** | Object taxonomy (18 types) is the IA's navigational vocabulary |
| **04_universal_object_protocol.md** | Object identity and relationships (04 §4, §6) define how objects are found and linked |
| **05_runtime_canon.md** | Context preservation and workspace state derive from runtime state model |
| **08_experience_canon.md** | This document is the implementation specification of the Experience Canon |
| **09_repository_canon.md** | Frontend code structure follows this IA (modules per navigation primitive) |
| **11_engineering_canon.md** | Frontend engineering standards enforce this IA |

---

> **End of Information Architecture**
> **[Return to INDEX](#)**