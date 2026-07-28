# SHUNYA Navigation Canon

> **Canonical Reference — Phase X1**
> Defines the complete navigation grammar: how users move through SHUNYA, how orientation is maintained, and how spatial memory is preserved.

---

## 1. Navigation Philosophy

### Principles

| Principle | Meaning |
|-----------|---------|
| **One application, not a website** | SHUNYA is a single-page application. Navigation is spatial, not URL-based. No page loads. |
| **Object-first, not page-first** | Navigation is organized around objects. You navigate to objects, not to pages. |
| **Spatial continuity** | Every transition animates the relationship between the departure point and the destination. Nothing appears or disappears without explanation. |
| **State is sacred** | Navigation never resets state. Scroll position, selection, open panels persist across navigation. |
| **Direct, not menu-driven** | The most efficient navigation path is direct: search, command palette, or keyboard shortcut. Menus are secondary. |

---

## 2. Global Navigation (Zone 1)

Zone 1 is the persistent bar at the top of every workspace. It is always present, always identical.

### Elements (Left to Right)

```
[Logo/Home] [Workspace Switcher] [Breadcrumb] [Search Bar] [Notifications] [User Menu]
```

| Element | Behavior |
|---------|----------|
| **Logo/Home** | Click to return to Home workspace. Right-click for context menu (workspace switcher, settings). |
| **Workspace Switcher** | Icon grid of available workspaces. Active workspace is highlighted. Click switches workspace. Max 14 icons. |
| **Breadcrumb** | Current path: Workspace > Object > Section. Click any segment to navigate. Collapsed on narrow screens. |
| **Search Bar** | Always visible. Ctrl+K opens command palette. Type to search globally. |
| **Notifications** | Bell icon. Badge shows unread count (max 9+). Click opens notification panel. |
| **User Menu** | User avatar/initials. Click opens: profile, preferences, settings, help, sign out. |

### Rules

- Zone 1 is always visible, always at the top.
- Zone 1 height: 56px (desktop), 48px (mobile).
- Zone 1 does not scroll. It is fixed.
- Zone 1 is identical across all workspaces. No workspace-specific chrome.
- Zone 1 background: semi-transparent with backdrop blur (frosted glass effect).

---

## 3. Workspace Switcher

### Behavior

| Interaction | Result |
|-------------|--------|
| **Click icon** | Switch to that workspace. Current workspace state is preserved. |
| **Ctrl+[1-9]** | Switch to the Nth workspace in the user's order. |
| **Ctrl+Tab** | Next workspace in order. |
| **Ctrl+Shift+Tab** | Previous workspace in order. |
| **Hover** | Tooltip shows workspace name. |
| **Right-click** | Context menu: Pin to favorites, Reorder, Hide. |

### Display

- User's workspaces (up to 14 icons).
- Icons are 28x28px with a subtle active indicator (gold underline).
- User can reorder, hide, and pin favorites.
- Hidden workspaces are accessible via the overflow menu ("...").

---

## 4. Context Panel (Zone 2) Navigation

The Context Panel is the persistent left-side panel. It is the secondary navigation mechanism.

### Structure

```
┌─ Current Object ───────────────────┐
│  [Object Icon] [Name]              │
│  [Type] · [Status] · [Confidence]  │
│  [Summary line]                    │
├─ Quick Actions ────────────────────┤
│  [Action 1] [Action 2] [...]       │
├─ Relationships ────────────────────┤
│  ┌─ Type A ────────────────────┐   │
│  │  ● Object 1                 │   │
│  │  ● Object 2                 │   │
│  └─────────────────────────────┘   │
│  ┌─ Type B ────────────────────┐   │
│  │  ● Object 3                 │   │
│  └─────────────────────────────┘   │
├─ Recent Items ─────────────────────┤
│  Last 5 objects                    │
├─ AI Resident ──────────────────────┤
│  [Minimized — click to expand]     │
└────────────────────────────────────┘
```

### Behavior

| Interaction | Result |
|-------------|--------|
| **Collapse/Expand** | Toggle with Ctrl+\ or click the grip handle. Collapsed to 40px strip. |
| **Click relationship** | Navigate to the related object. Current object goes into history. |
| **Click quick action** | Execute action on the current object (no navigation). |
| **Click recent item** | Navigate to that object. |
| **Context Panel open** | Content Area shrinks to fill remaining space (calc(100vw - 300px)). |
| **Context Panel closed** | Content Area expands to full width. |

### Width

- Default: 300px.
- Min: 40px (collapsed strip showing only the grip handle).
- Resizable by dragging the right edge (240px–400px range).
- Width preference is persisted per user, not per workspace.

---

## 5. Content Area Navigation (Zone 3)

### Section Tabs

Every object workspace has a tab bar with fixed-ordered sections:

```
[Identity] [Relationships] [Timeline] [Knowledge] [Tasks] [Execution] [Metrics] [Documents] [AI] [History]
```

| Interaction | Result |
|-------------|--------|
| **Click tab** | Scroll to that section. Tab becomes active. |
| **Horizontal scroll** | Tabs scroll horizontally if they overflow. |
| **Tab keyboard nav** | Left/Right arrows to navigate tabs. |
| **Swipe (touch)** | Swipe left/right to navigate sections. |

### Section Internal Navigation

- Sections are scrollable (virtualized for large datasets).
- Within a section, sub-sections are collapsible/expandable.
- Deep links to sub-sections are supported: `#relationships--key`.
- Section scroll position is preserved when switching tabs.

---

## 6. Command Palette (Ctrl+K)

### Activation

- **Ctrl+K** (or Cmd+K) opens the palette.
- Escape closes it.
- Clicking outside closes it.

### Content

```
┌─ Command Palette ────────────────────┐
│  [Search input — autofocused]        │
│                                      │
│  Recent Objects:                     │
│  ○ Project Alpha  (Project)          │
│  ○ Decision 42    (Decision)         │
│  ○ Person: Smith  (Person)           │
│                                      │
│  Quick Actions:                      │
│  ○ New Project                       │
│  ○ New Decision                      │
│  ○ New Task                          │
│                                      │
│  Commands:                           │
│  ○ Switch to Home Workspace          │
│  ○ Open Settings                     │
│  ○ Run Report                        │
└──────────────────────────────────────┘
```

### Behavior

| Input | Result |
|-------|--------|
| **Type 2+ characters** | Universal object search results appear. |
| **Type "/"** | Command mode. Search commands and actions. |
| **Type ">"** | Workspace switch mode. Search workspaces. |
| **Type "?"** | Show keyboard shortcut reference. |
| **Up/Down arrows** | Navigate results. |
| **Enter** | Execute selection. |
| **Tab** | Cycle through result groups (Objects / Actions / Commands). |

### Command Palette Invariants

- Always available (Ctrl+K).
- Non-modal — can be dismissed without losing state.
- Search is fuzzy and contextual (current workspace objects rank higher).
- Recent objects from all workspaces are shown on open (before typing).

---

## 7. Search Behavior

### Search Bar (Zone 1)

| State | Behavior |
|-------|----------|
| **Empty / focused** | Dropdown shows: recent searches, recent objects, suggested searches |
| **Typing** | Real-time results after 2 characters. Debounced 150ms. |
| **Results** | Grouped by object type. Each result: icon, name, type, status summary. |
| **Select result** | Navigate to the object's workspace. |
| **Escape** | Close search dropdown, return focus to previous element. |
| **Enter (no selection)** | Open full search results in the Search Workspace. |

### Search Operators

| Operator | Example | Behavior |
|----------|---------|----------|
| `type:` | `type:decision budget` | Filter by object type |
| `ws:` | `ws:project launch` | Filter by workspace |
| `status:` | `status:active` | Filter by status |
| `from:` | `from:2024-01-01` | Filter by date range |
| `tag:` | `tag:urgent` | Filter by tag |
| `@` | `@jane` | Search objects related to a person |
| `#` | `#budget` | Search by object ID or reference |

---

## 8. Keyboard Navigation

### System-Wide Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+K** | Command palette |
| **Ctrl+\** | Toggle Context Panel |
| **Ctrl+Tab** | Next workspace |
| **Ctrl+Shift+Tab** | Previous workspace |
| **Ctrl+[1-9]** | Switch to workspace N |
| **Ctrl+,** | User settings |
| **Ctrl+Shift+K** | Focus AI Resident |
| **Ctrl+Shift+H** | Open history |
| **Ctrl+Shift+F** | Global search (if not visible) |
| **Escape** | Close overlay, panel, or go up one level |
| **Ctrl+Z** | Undo (session-wide) |
| **Ctrl+Shift+Z** | Redo |

### Object Navigation Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+[** | Navigate back in object history |
| **Ctrl+]** | Navigate forward in object history |
| **Ctrl+Shift+[** | Previous object in current list |
| **Ctrl+Shift+]** | Next object in current list |
| **Ctrl+Shift+E** | Edit current object |
| **Ctrl+Shift+S** | Save (when in edit mode) |
| **Ctrl+Shift+Up** | Focus section above |
| **Ctrl+Shift+Down** | Focus section below |
| **Alt+[1-9]** | Jump to tab N (1=Identity, 2=Relationships, ...) |

### Focus Management

- Tab order follows visual order: Zone 1 → Zone 2 → Zone 3 → Zone 2 secondary.
- Focus indicator is always visible (2px gold outline).
- Focus never leaves the visible viewport.
- Tab stops are limited to interactive elements only.
- Arrow keys navigate within component groups (lists, tables, tabs).

---

## 9. Breadcrumb System

### Format

```
[Workspace Icon] Workspace Name  >  Object Name  >  Section
```

### Behavior

| Segment | Click Behavior |
|---------|---------------|
| **Workspace** | Return to workspace root (no object selected) |
| **Object** | Return to object workspace (current section resets to default) |
| **Section** | Return to that section within the current object |

### Rules

- Breadcrumbs appear in Zone 1, after the workspace switcher.
- Breadcrumbs appear only when an object is selected.
- Breadcrumbs show at most 3 levels. Additional levels are truncated with "..." (click to see full path in tooltip).
- Breadcrumbs are not clickable for the current level (it is the current location).
- Breadcrumbs update with animation when the path changes.

---

## 10. History Navigation

### Object History Stack

Each workspace maintains an independent object history stack (up to 50 entries).

| Action | Behavior |
|--------|----------|
| **Navigate to object** | Push current object onto history stack. |
| **Navigate back (Ctrl+[)** | Pop current object, restore previous object with its context (section, scroll position). |
| **Navigate forward (Ctrl+])** | Push the next object forward from the history stack. |
| **Switch workspace** | Freeze current workspace's history stack. Activate target workspace's stack. |

### History Panel

Accessible from the Context Panel (History tab) or Ctrl+Shift+H.

```
┌─ History ──────────────────────┐
│  Today                         │
│  ○ Decision 42  — 2m ago       │
│    → reviewed evidence         │
│  ○ Project Alpha — 15m ago     │
│    → updated timeline          │
│  ○ Person: Smith — 1h ago      │
│    → viewed profile            │
│                                │
│  Earlier                       │
│  ○ Document: Q3 Report — 3h   │
│  ○ Task: Review budget — 5h   │
└────────────────────────────────┘
```

### History Rules

- History shows: object name, type, time, context (what section or action).
- Click any history item to return to that exact state.
- History is per-workspace. Each workspace has its own trail.
- History is preserved across sessions (persisted in local storage, synced when online).
- User can clear history (per-workspace or global).

---

## 11. Forward/Back Model

SHUNYA intercepts browser forward/back to navigate the object history stack, not the URL history stack.

### Behavior

| User Action | SHUNYA Action |
|-------------|---------------|
| **Browser Back (Alt+Left)** | Navigate back in object history (Ctrl+[) |
| **Browser Forward (Alt+Right)** | Navigate forward in object history (Ctrl+]) |
| **Click link** | Navigate to object (push onto history) |
| **Search result click** | Navigate to object (push onto history) |

### URL Model

- URL is updated on every navigation for deep-linkability.
- URL format: `/workspace/[workspace-id]/object/[object-id]/[section]`
- URL history is synced with object history (one URL per object).
- Browser back navigates the object history in reverse.
- URL can be shared and bookmarked. Opens to the exact object and section.

---

## 12. "No Page-Jumping" Philosophy

### Core Rule

Navigating within SHUNYA never causes a page reload, a full-screen transition, or a white flash.

### Implementation

| Pattern | Allowed? | Alternative |
|---------|----------|-------------|
| Full page reload | NEVER | Single-page navigation with animated transitions |
| White flash / loading spinner | NEVER | Progressive content rendering with skeleton placeholders |
| URL change → page reload | NEVER | URL change is a pushState only — no server round-trip |
| Scroll to top on navigation | NEVER | Scroll position is preserved. Only new content is revealed. |
| Content shift on data load | NEVER | Fixed container dimensions. Content loads into reserved space. |
| Modal that covers full screen | RARELY | Panel or drawer pattern. Full-screen only for compose/create flows. |
| New tab/window | RARELY | Only for external links. Internal navigation is always in-app. |

### Single Application Behavior

- SHUNYA is a single browser tab. No internal links open new tabs.
- All navigation is rendered client-side.
- The application bootstraps once and never reloads.
- Updates are pushed via WebSocket or SSE — no polling.
- The browser back/forward buttons control SHUNYA's navigation, not the browser's.

---

## 13. Navigation Invariants

1. **No page reloads.** All navigation is client-side. Zero full-page transitions.
2. **No scroll reset on navigation.** Scroll position is always preserved per section.
3. **No focus loss on navigation.** Focus moves intentionally to the next logical interactive element.
4. **All navigation is keyboard-accessible.** Every navigation action has a keyboard shortcut.
5. **Every object has a canonical URL.** Direct linking works for every object and section.
6. **Workspace state is serialized and restored.** Switch away and back — everything is as you left it.
7. **The Context Panel is the secondary navigation hub.** It shows relationships, recent items, and quick actions.
8. **The command palette is the primary navigation accelerator.** Every navigation action is available from Ctrl+K.
9. **Breadcrumbs show the relationship chain, not the file path.** Navigation is relational, not hierarchical.
10. **History is per-workspace and persistent.** Your trail never disappears.