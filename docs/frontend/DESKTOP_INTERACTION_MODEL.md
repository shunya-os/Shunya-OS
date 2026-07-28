# SHUNYA Desktop Interaction Model

> **Canonical Frontend Document · Phase C3 Parallel**
> **Status: CANONICAL — Implementation-Independent Interaction Specification**
> **Version: 1.0**
> **Derived From: 08_experience_canon.md (Experience Canon)**
> **Target: Desktop (≥ 1200px viewport)**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Desktop Philosophy](#2-desktop-philosophy)
3. [The Workspace Desktop](#3-the-workspace-desktop)
4. [Object Interaction Model](#4-object-interaction-model)
5. [Keyboard Model](#5-keyboard-model)
6. [Mouse & Pointer Model](#6-mouse--pointer-model)
7. [Drag and Drop](#7-drag-and-drop)
8. [Panel Management](#8-panel-management)
9. [Multi-Window Considerations](#9-multi-window-considerations)
10. [Cross-Device Continuity](#10-cross-device-continuity)
11. [Relationship to Other Documents](#11-relationship-to-other-documents)

---

## 1. Purpose

This document defines how humans interact with SHUNYA on a desktop computer — keyboard, mouse, touchpad, and pointer interactions. It specifies the complete interaction vocabulary for the desktop experience.

**This document defines how interactions feel and behave. It does not define visual design (see DESIGN_SYSTEM.md) or component structure (see COMPONENT_SPECIFICATION.md).**

---

## 2. Desktop Philosophy

### 2.1 Core Principle

The desktop is the **primary work surface** for SHUNYA. It is where deep work happens — object creation, relationship mapping, decision-making, and complex analysis. The desktop experience assumes:

- **Full attention** — the human is focused on SHUNYA as the primary application
- **Keyboard proficiency** — keyboard shortcuts are the primary interaction method for power users
- **Spacious display** — ≥ 1200px width with generous whitespace
- **Stable connection** — network is reliable, offline mode is secondary
- **Multiple surfaces** — the human may operate multiple objects simultaneously

### 2.2 Desktop Interaction Values

| Value | Manifestation |
|-------|--------------|
| **Speed** | Keyboard-first, minimal clicks, instant response |
| **Precision** | Pixel-accurate pointer targets, generous but not wasteful |
| **Power** | Progressive disclosure reveals advanced capabilities |
| **Flow** | No modal interruptions, no context switches |
| **Memory** | Workspace state persists, return is resume |

### 2.3 What Desktop Is Not

- **Not a mobile app enlarged** — desktop has its own interaction patterns
- **Not a web page** — no page loads, no navigation menu, no back button
- **Not a dashboard** — desktop is for work, not just monitoring
- **Not a terminal** — AI handles automation; the human handles judgment

---

## 3. The Workspace Desktop

### 3.1 Desktop Surface Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ TOP BAR (fixed, 48px)                                                 │
│ ┌──────────┐ ┌─────────┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌────┐ ┌───────────┐ │
│ │Workspace▼│ │Object ▼ │ │AI│ │🔍│ │🔔│ │👤│ │💾 │ │ ⏎ Object  │ │
│ └──────────┘ └─────────┘ └──┘ └──┘ └──┘ └──┘ └────┘ └───────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│                    │                          │                      │
│ OBJECT BROWSER     │   FOCAL AREA             │ RELATIONSHIP PANEL  │
│ (300px, resizable) │   (flexible)             │ (280px, collapsible)│
│                    │                          │                      │
│ Objects in this    │   The object itself.      │ Connected objects   │
│ workspace:         │   70% whitespace          │                     │
│                    │   20% content             │ ┌─────────────────┐ │
│ ○ Decision: Q3    │   10% controls            │ │ Decision        │ │
│ ○ Task: Hire      │                          │ │ Q3 Budget       │ │
│ ○ Document: RFP   │   ╔══════════════════╗    │ │    ↑ involves   │ │
│ ● Event: Review   │   ║  FOCAL OBJECT   ║    │ ├─────────────────┤ │
│   (current)       │   ║                  ║    │ │ Document        │ │
│ ○ Outcome: Q2     │   ║  ┌────────────┐ ║    │ │ Q3 Proposal     │ │
│                    │   ║  │  Content   │ ║    │ │    ↑ references │ │
│                    │   ║  │  (20%)     │ ║    │ ├─────────────────┤ │
│                    │   ║  └────────────┘ ║    │ │ Human: Alice    │ │
│                    │   ║                  ║    │ │    ↑ author     │ │
│                    │   ║  [Controls 10%]  ║    │ └─────────────────┘ │
│                    │   ╚══════════════════╝    │                      │
│                    │                          │                      │
└──────────────────────────────────────────────────────────────────────┘
│ Object Breadcrumb: Workspace > Object Type > Object Name               │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 Desktop Layout Rules

1. **Top bar is always 48px** — never hidden, never resized.
2. **Object browser is 300px by default**, resizable by dragging the right edge (min 200px, max 400px).
3. **Relationship panel is 280px by default**, collapsible to 0 width.
4. **Focal area fills remaining space** — never scrolls beyond the viewport (only its content scrolls).
5. **Panels are fixed to viewport edges** — object browser left, relationship panel right, top bar top.

---

## 4. Object Interaction Model

### 4.1 Object Selection

| Action | Behavior |
|--------|----------|
| **Click on object in browser** | Object becomes focal. Focal area loads object detail. Browser shows object as selected (highlighted). |
| **Click on object in relationship panel** | Object becomes focal. Relationship panel updates to show the new object's relationships. |
| **Click on relationship link in focal area** | The linked object becomes focal. Relationship panel updates. |
| **Cmd+Click on relationship link** | Opens linked object in focus without losing current position. Relationship panel shows both contexts. (Future) |

### 4.2 Object Actions

| Action | Trigger | Behavior |
|--------|---------|----------|
| **Primary action** | Primary button in action bar or keyboard shortcut | Executes the object's primary action |
| **Secondary actions** | Secondary buttons or context menu | Show additional available actions |
| **Context menu** | Right-click on object | Shows all available actions for the object type |
| **Quick action** | Keyboard shortcut (single key) | Executes action without moving from current focus |

### 4.3 Progressive Disclosure Navigation

| Level | Trigger | Behavior |
|-------|---------|----------|
| **Default** | Initial view | Object identity, current state, primary action |
| **Expand** | Click "▼" or press `Cmd+↓` | Key relationships, recent activity, secondary actions |
| **Detail** | Click "▼▼" or press `Cmd+Shift+↓` | Full object data, all relationships, history |
| **Advanced** | Context menu or settings icon | Permissions, integrations, audit, raw data |

### 4.4 Object Timeline Navigation

| Action | Behavior |
|--------|----------|
| **Scroll timeline** | Mouse wheel or touchpad scroll — moves through the object's event timeline |
| **Click timeline event** | Expands the event to show details |
| **Click evidence link** | Opens the evidence object in a detail overlay |
| **Timeline filter** | Dropdown to filter events by type, actor, or time range |

---

## 5. Keyboard Model

### 5.1 Universal Shortcuts

These shortcuts work everywhere in SHUNYA:

| Shortcut | Action |
|----------|--------|
| `Cmd+K` | Object search (global) |
| `Cmd+Shift+K` | AI collaboration (contextual to current object) |
| `Cmd+Shift+W` | Workspace switcher |
| `Cmd+[` | Navigate to previous focal object in history |
| `Cmd+]` | Navigate to next focal object in history |
| `Cmd+Shift+F` | Focus object browser |
| `Cmd+Shift+R` | Refresh current object state |
| `Cmd+Shift+E` | Export current object |
| `Cmd+Shift+P` | Open profile/settings object |
| `Escape` | Clear search / close overlay / return to focal object |
| `Cmd+.` | Toggle AI panel |
| `Cmd+,` | Open preferences |

### 5.2 Object Navigation Shortcuts

| Shortcut | Action |
|----------|--------|
| `↑` / `↓` | Navigate object browser entries |
| `→` | Select the next item in the object browser |
| `←` | Select the previous item in the object browser |
| `Enter` | Open selected object as focal object |
| `Cmd+↑` | Navigate to parent object (if applicable) |
| `Cmd+↓` | Expand current object disclosure level |
| `Cmd+Shift+↓` | Expand to next disclosure level |
| `Cmd+Shift+↑` | Contract disclosure level |

### 5.3 Object Action Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+S` | Save current object (if editing) |
| `Cmd+Z` | Undo last action |
| `Cmd+Shift+Z` | Redo last undone action |
| `Cmd+D` | Duplicate current object |
| `Cmd+Backspace` | Delete/archive current object (with confirmation) |
| `Cmd+Shift+A` | Show all actions for current object |
| `Space` | Quick primary action on focal object |
| `Cmd+Enter` | Confirm / Submit (in forms, AI input) |

### 5.4 Workspace Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+1`–`Cmd+9` | Switch to workspace by index (recent order) |
| `Cmd+T` | Create new object (type picker opens) |
| `Cmd+N` | New workspace |
| `Cmd+Shift+T` | Create new object of the current type |

### 5.5 AI Interaction Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+Shift+K` | Open AI panel |
| `Cmd+Enter` | Submit AI input |
| `Escape` | Close AI panel |
| `Tab` | Move focus to AI panel from focal area |
| `Shift+Tab` | Move focus from AI panel back to focal area |

### 5.6 Keyboard Interaction Rules

1. **All shortcuts are discoverable** — pressing `Cmd+/` shows the shortcuts cheat sheet.
2. **No shortcut conflicts** — SHUNYA shortcuts do not conflict with browser/OS standard shortcuts (Cmd+C, Cmd+V, Cmd+W are preserved).
3. **Shortcuts are overridable** — users can customize keyboard shortcuts.
4. **Full keyboard access** — every interactive element is reachable via Tab in logical order.
5. **Focus indicator is always visible** — the currently focused element has a clear 2px outline.

---

## 6. Mouse & Pointer Model

### 6.1 Click Behavior

| Action | Target | Behavior |
|--------|--------|----------|
| **Single click** | Object card | Select and focus object |
| **Single click** | Button | Execute action |
| **Single click** | Relationship link | Follow relationship (new focal object) |
| **Single click** | Breadcrumb segment | Navigate to that level |
| **Double click** | Object field | Enter inline edit mode (if editable) |
| **Double click** | Object name | Rename object inline |
| **Right click** | Object in any context | Open context menu with all available actions |
| **Right click** | Relationship panel | Filter/sort/group relationships |

### 6.2 Hover Behavior

| Element | Hover Effect | Delay |
|---------|-------------|-------|
| Object card | Slight lift (translateY -1px, shadow-md) | 50ms |
| Button | Background shift (surface-alt) | 0ms |
| Relationship link | Underline + text color shift | 0ms |
| Icon button | Background circle appears | 0ms |
| Tooltip target | Tooltip appears | 300ms |
| Object field | Subtle background tint (editable fields only) | 0ms |

### 6.3 Scroll Behavior

| Context | Behavior |
|---------|----------|
| **Object browser** | Scrolls independently of focal area. Content follows scroll. |
| **Focal area** | Scrolls independently of browser and panel. Long objects scroll naturally. |
| **Relationship panel** | Scrolls independently. Only active relationships visible. |
| **AI panel** | Scrolls independently. Message history scrolls to latest. |
| **Timeline** | Horizontal or vertical scroll depending on layout. |

### 6.4 Mouse Interaction Rules

1. **No click-jacking** — hover previews are not interactive; always click to access.
2. **Context menus are consistent** — right-click always shows the same action list regardless of where on the object you click.
3. **Hover is optional** — no information is available only on hover (accessibility).
4. **Scroll is passive** — scroll events never trigger object actions.
5. **Precision is not required** — click targets are generous (44×44px minimum).

---

## 7. Drag and Drop

### 7.1 Supported Drag Operations

| Source | Target | Behavior |
|--------|--------|----------|
| Object card (browser) | Focal area | Open object as focal |
| Object card (browser) | Relationship panel | Add relationship between current focal and dropped object |
| Object card (browser) | Another workspace (sidebar) | Move/copy object to workspace |
| File (OS) | Focal area | Upload file as evidence attached to focal object |
| File (OS) | Object browser | Upload file and create Document object |
| Relationship link | Object browser | Create relationship between two objects |
| Object card (browser) | Object card (browser) | Reorder within workspace (when custom ordering is enabled) |

### 7.2 Drag Visual Feedback

| State | Visual |
|-------|--------|
| **Drag start** | Source object reduces opacity to 0.5. Ghost follows pointer at 0.8 opacity. |
| **Valid target** | Target area shows a subtle highlight (border-accent, background-accent-subtle). |
| **Invalid target** | No highlight. Pointer shows "no drop" cursor. |
| **Drop** | Brief success animation (checkmark, 200ms). Object state updates. |
| **Cancel** | Ghost fades out. Source returns to full opacity. |

### 7.3 Drop Zones

| Drop Zone | Behavior |
|-----------|----------|
| Focal area | Opens object |
| Relationship panel | Adds relationship to current focal object |
| Object browser | Between items: reorder. In empty space: create link. |
| Workspace list | Move object to that workspace |
| File upload zone | Attach file as evidence |

### 7.4 Drag and Drop Rules

1. **All drag operations have keyboard equivalents** — no feature is drag-only.
2. **Undo works after drag operations** — dropping an object into a relationship can be undone.
3. **Drag operations are disabled during offline mode** — queued for sync.
4. **Touch drag is supported** — mobile and tablet drag works via long-press.
5. **Multi-select drag** — Cmd+click to select multiple objects, then drag as group.

---

## 8. Panel Management

### 8.1 Panel Behavior

| Panel | Show | Hide | Resize | Behavior |
|-------|------|------|--------|----------|
| Object browser | Always visible (desktop) | Close button in panel | Drag right edge (200–400px) | Independent scroll |
| Relationship panel | Always visible (desktop) | Close button (X) | Drag left edge (200–400px) | Independent scroll |
| AI panel | Cmd+Shift+K or AI button | Escape or close button | Fixed 420px | Slide-over, no backdrop dim |

### 8.2 Panel Interaction Rules

1. **Panels are not modal** — the focal area remains interactive while panels are open.
2. **Panel state persists** — if you close the relationship panel, it stays closed until reopened.
3. **Panel width is sticky per session** — resizing a panel persists for the current session.
4. **Panels animate at 250ms ease-out** — no jarring appearance or disappearance.
5. **AI panel is the only exception to single-overlay rule** — it can coexist with overlays.

---

## 9. Multi-Window Considerations

### 9.1 Single Window

SHUNYA operates within a **single browser window** (or native window). The surface is the window — there is no multi-window mode in v1.0.

### 9.2 Future Multi-Window

Multi-window support is identified for a future version. When implemented:

- Each window shows a different workspace
- Windows share the same session (single sign-on)
- Drag and drop between windows is supported
- Each window has independent state

### 9.3 Browser Tab Considerations

| Behavior | Rule |
|----------|------|
| **Tab away and return** | Surface state preserved exactly — return is resume |
| **Multiple tabs** | Each tab is a separate session (for evaluation purposes) |
| **Refresh** | Surface reinitializes to last persistent state |
| **Close and reopen** | Opens to last persistent workspace and focal object |

---

## 10. Cross-Device Continuity

### 10.1 Session Continuity

| Scenario | Behavior |
|----------|----------|
| **Desktop → Mobile** | Workspace and last focal object sync. Mobile opens to the same object in mobile layout. |
| **Mobile → Desktop** | Same — the last active workspace and object are restored. |
| **Desktop → Desktop** | State syncs across desktop browsers if logged into the same account. |

### 10.2 Sync Latency

| Data Type | Sync Speed |
|-----------|-----------|
| Object state | Real-time (WebSocket) |
| Workspace state | On workspace switch |
| AI conversation | On AI panel open |
| User preferences | On change (debounced 2s) |
| Navigation history | On navigation event |

---

## 11. Relationship to Other Documents

| Document | Relationship |
|----------|-------------|
| **08_experience_canon.md** | Desktop interaction model implements all 12 experience principles defined in the canon |
| **INFORMATION_ARCHITECTURE.md** | Desktop interactions navigate the IA defined in that document |
| **DESIGN_SYSTEM.md** | Visual feedback for interactions (hover, drag, focus) follows design token specs |
| **MOBILE_INTERACTION_MODEL.md** | Both models derive from the same philosophy but adapt to their respective form factors |
| **COMPONENT_SPECIFICATION.md** | Components in this document's interaction patterns are fully specified there |

---

> **End of Desktop Interaction Model**
> **[Return to INDEX](#)**