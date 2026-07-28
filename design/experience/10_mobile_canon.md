# SHUNYA Mobile Canon

> **Canonical Reference — Phase X1**
> Defines how SHUNYA behaves on mobile devices. Desktop-first with mobile integrity.

---

## 1. Mobile Philosophy

### Principles

| Principle | Meaning |
|-----------|---------|
| **Desktop-first, not desktop-only** | SHUNYA is designed for desktop first but adapted with integrity for mobile. Not a responsive skin — a thoughtful adaptation. |
| **Portrait-first** | The primary mobile orientation is portrait. Landscape is supported but secondary. |
| **Progressive, not reduced** | Mobile is not "desktop minus features." Mobile has a distinct interaction model optimized for touch and small screens. |
| **Read-first, act-when-needed** | On mobile, reading and reviewing are primary. Heavy actions (editing, configuration) are deferred to desktop. |
| **Continuity** | The user experiences SHUNYA as one continuous system across devices. State, history, and preferences are synchronized. |

### What Mobile Is Not

- Mobile is not a PWA (although it may be installable as one).
- Mobile is not a native app — it is a responsive web application.
- Mobile does not have every feature of desktop — it has the features that make sense on mobile.
- Mobile does not have "full" mode and "mobile" mode. It has one integrated experience.

---

## 2. Responsive Breakpoints

| Breakpoint | Width | Device |
|------------|-------|--------|
| Mobile | < 640px | Phone portrait/landscape |
| Tablet | 640px – 1024px | Tablet portrait |
| Desktop | 1024px – 1440px | Standard desktop |
| Wide | > 1440px | Large desktop monitors |

### Breakpoint Behavior

| Element | < 640px | 640-1024px | > 1024px |
|---------|---------|------------|----------|
| Zone 1 (Global Nav) | Compact (48px) | Standard (56px) | Standard (56px) |
| Zone 2 (Context Panel) | Bottom sheet | Collapsible side panel | Side panel (300px) |
| Zone 3 (Content) | Full width | Full with CP collapsible | Standard width |
| Section Nav | Bottom tab bar | Left icon bar | Left icon bar |
| Workspace Switcher | Bottom bar (5 max) | Top bar (icons) | Top bar (icons) |

---

## 3. Mobile Layout

### Portrait Layout (< 640px)

```
┌──────────────────┐
│  Zone 1 (48px)   │
│  [Back] [Title] [Menu] │
├──────────────────┤
│                   │
│  Zone 3 (Content) │
│  Full width       │
│                   │
│                   │
│                   │
├──────────────────┤
│  Bottom Bar (56px)│
│ [WS1][WS2][WS3]  │
│ [+4 more]        │
└──────────────────┘
```

### Context Panel on Mobile

The Context Panel (Zone 2) becomes a **bottom sheet** on mobile:

- Triggered by swiping up from the bottom or tapping the object indicator.
- Sheet covers 60% of screen height (configurable).
- Sheet has a drag handle at the top for resize.
- Sheet can be dismissed by swiping down or tapping outside.
- When sheet is open, the content area behind is dimmed.

### Bottom Bar

The bottom bar replaces the workspace switcher. It shows:

- Up to 5 workspace icons (the user's most frequently used).
- "+" icon to expand and show all workspaces.
- Active workspace is highlighted with gold underline.
- Tap workspace icon to switch.

---

## 4. Touch Interactions

### Gestures

| Gesture | Action |
|---------|--------|
| **Swipe left** | Navigate to next object in history |
| **Swipe right** | Navigate to previous object in history |
| **Swipe down** | Close panel, sheet, or overlay |
| **Swipe up** | Open context panel bottom sheet |
| **Long press** | Context menu (on lists, cards, items) |
| **Double tap** | Expand/collapse section |
| **Pinch** | Not used (content is not zoomable by gesture) |
| **Tap** | Select, click, navigate |
| **Tap and hold + drag** | Reorder items (if supported) |

### Touch Targets

| Element | Minimum Size | Purpose |
|---------|-------------|---------|
| Icon buttons | 44x44px | Navigation, actions |
| List items | 44px height | Selection |
| Cards | 48px minimum touch area | Interaction |
| Bottom bar icons | 48x48px | Navigation |
| Buttons | 44px height, 64px width | Primary actions |
| Chips | 36px height | Filters, tags |

### Touch Feedback

- Tap: 100ms visual feedback (subtle background tint).
- Long press: 300ms haptic-like visual (scale 0.97).
- Swipe: Visual indicator of direction (arrow or ghost motion).
- Scroll: Overscroll with subtle elastic bounce (iOS-style).

---

## 5. Mobile Navigation

### Navigation Stack

Mobile uses a navigation stack (like a native app):

```
Stack Root: Workspace Default View
  ├── Pushed: Object Workspace
  │     └── Pushed: Related Object
  └── Pushed: Search Results
```

| Action | Behavior |
|--------|----------|
| **Tap object** | Push object workspace onto the stack. Slide in from right. |
| **Back (header or gesture)** | Pop current view, return to previous. Slide out to right. |
| **Tap workspace icon** | Pop to root of that workspace. |
| **Deep link** | Replace entire stack with the target object's workspace. |

### Header Navigation (Mobile)

```
Left: [Back arrow]  Center: [Object name / Section]  Right: [Menu / Actions]
```

- Back arrow appears when not at stack root.
- Title truncates to one line.
- Right menu always shows "..." with overflow actions.

### Bottom Tab Navigation

The bottom bar shows:

| Item | Icon | Action |
|------|------|--------|
| Workspace 1 | W1 icon | Switch to first workspace |
| Workspace 2 | W2 icon | Switch to second workspace |
| Workspace 3 | W3 icon | Switch to third workspace |
| Workspace 4 | W4 icon | Switch to fourth workspace |
| More | "+" | Show all workspaces grid |

---

## 6. Mobile Search

Search on mobile is a full-screen overlay (triggered by a search icon or swipe down).

```
┌──────────────────────┐
│ 🔍 Search SHUNYA     │
│                      │
│ Recent Objects:      │
│ ○ Decision 42        │
│ ○ Project Alpha      │
│                      │
│ Quick Actions:       │
│ ○ New Decision       │
│ ○ New Task           │
│ ○ New Document       │
└──────────────────────┘
```

- Search input is always visible at the top.
- Results appear after 2 characters.
- Results are grouped by object type (collapsible).
- Tap result to navigate.
- Search history is shown below the input.
- Keyboard opens automatically when search is activated.

---

## 7. Mobile Object Workspace

The object workspace is adapted for mobile:

### Section Navigation (Bottom Tab Bar)

Sections are navigated via a horizontal scrollable tab bar above the content:

```
[Identity] [Relationships] [Timeline] [Knowledge] [...]
```

- Tabs scroll horizontally (no wrap).
- Active tab has gold underline.
- Swipe left/right to navigate between sections.
- Tab bar hides when scrolling down (reappears on scroll up).

### Section Content on Mobile

| Section | Mobile Adaptation |
|---------|-------------------|
| Header | Compact (48px icon, single-line name). Status and ID are secondary. |
| Summary | Same 3 lines. Actions become swipeable rows. |
| Identity | Key-value list. Tap to expand details. |
| Relationships | Card list. Swipe to reveal actions. |
| Timeline | Compact timeline. Tap event to expand. |
| Knowledge | Card list. Tap to read full. |
| Tasks | Swipeable task rows. Checkbox + title. |
| Documents | File list with download button. |
| AI Resident | Icon in bottom-right. Tap to open chat. |
| History | Accessible from overflow menu. |

### Inline Editing on Mobile

- Edit mode is NOT available on mobile (except for short text fields).
- To edit an object, user must switch to desktop or tap "Edit on Desktop."
- Creating new objects is possible with simplified forms (minimal required fields only).

---

## 8. Tablet Behavior (640-1024px)

Tablets use a hybrid layout:

| Element | Tablet Behavior |
|---------|----------------|
| Zone 1 | Standard (56px). Logo + workspace switcher + search icon. |
| Zone 2 | Collapsible side panel (280px). Auto-collapses when object is selected. |
| Zone 3 | Content at full remaining width. |
| Section nav | Left icon bar (expanded on tap). |
| Search | Overlay (like mobile) or inline (like desktop) — user preference. |
| Context Panel | Side panel (default) or bottom sheet (when collapsed, swipe up). |

Tablet supports:
- Split-view (context panel + content simultaneously).
- Keyboard with external keyboard support.
- Landscape and portrait.
- Drag-and-drop between panels.

---

## 9. Mobile-Specific Components

### BottomSheet

```
┌──────────────────────┐
│ ─── (drag handle)    │
│                      │
│  Context Panel       │
│  Content             │
│                      │
│                      │
└──────────────────────┘
```

**Props:** open, height, onClose, children, dragHandle

### BottomBar

```
┌──────────────────────────────────┐
│ [W1] [W2] [W3] [W4] [+ 4 more] │
└──────────────────────────────────┘
```

**Props:** workspaces, activeId, onSwitch

### MobileTabBar

Horizontally scrollable section tabs.

```
┌──────────────────────────────────────┐
│ [Identity] [Relationships] [Timeline] │
│ [Knowledge] [Tasks] [Execution] ...  │
└──────────────────────────────────────┘
```

**Props:** tabs, activeTab, onTabChange, scrollable

### SwipeableRow

Row with swipe-to-reveal actions.

```
┌───────────────────────────┐
│ Swipe left →
│ [Action1]  [Action2]
│
│ Content row
│
└───────────────────────────┘
```

**Props:** children, actions (array of { icon, label, onClick, variant })

---

## 10. Mobile Keyboard Behavior

| Event | Behavior |
|-------|----------|
| Keyboard opens | Content adjusts to fit above keyboard. Bottom bar is hidden. |
| Keyboard closes | Bottom bar reappears. Scroll position is preserved. |
| Search active | Keyboard stays open until dismissed. |
| Form input | Keyboard opens automatically on focus. Type is 'text' by default, 'search' in search. |
| Return key | "Search" on search input, "Next" on form fields, "Done" on final field. |
| Keyboard shortcut bar | Suggested actions above keyboard (autofill, quick text). |

---

## 11. Mobile Performance

| Requirement | Target |
|-------------|--------|
| Time to interactive | < 3s on 4G |
| Smooth scrolling | 60fps |
| Touch response | < 100ms |
| First contentful paint | < 1.5s |
| JavaScript bundle | < 200KB (critical path), code-split |
| Image loading | Lazy loading with low-res placeholder |

---

## 12. Mobile Invariants

1. **Mobile is not "desktop without features"** — it has a distinct interaction model optimized for touch.
2. **Portrait is the primary orientation.** Landscape is secondary but supported.
3. **Context Panel becomes a bottom sheet on mobile.** Never a side panel.
4. **Navigation is a stack (push/pop)**, not a free-form graph.
5. **Editing is limited on mobile** — create and short edits only. Full editing requires desktop.
6. **Every touch target is at least 44x44px.** No exceptions.
7. **Gesture navigation supplements, does not replace, standard UI.** Every action also available via tap.
8. **State syncs seamlessly between desktop and mobile.** No data loss on device switch.
9. **No horizontal scroll on any viewport.** Content wraps or becomes a horizontal tab bar.
10. **Mobile respects reduced motion** with the same standards as desktop.