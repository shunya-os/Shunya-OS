# SHUNYA Component Specification

> **Canonical Frontend Document · Phase C3 Parallel**
> **Status: CANONICAL — Implementation-Independent Component Specification**
> **Version: 1.0**
> **Derived From: 08_experience_canon.md, DESIGN_SYSTEM.md**
> **Target: All frontend implementations**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Component Contract](#2-component-contract)
3. [Surface Components](#3-surface-components)
4. [Object Components](#4-object-components)
5. [Action Components](#5-action-components)
6. [Navigation Components](#6-navigation-components)
7. [Feedback Components](#7-feedback-components)
8. [AI Components](#8-ai-components)
9. [Overlay Components](#9-overlay-components)
10. [Component Testing Requirements](#10-component-testing-requirements)
11. [Relationship to Other Documents](#11-relationship-to-other-documents)

---

## 1. Purpose

This document provides the complete specification for every UI component in the SHUNYA design system. Each component is specified with its API (props), states, behavior, accessibility requirements, and responsive behavior.

**This is the engineering specification for frontend component implementation.** Every component defined here must be implemented exactly as specified.

---

## 2. Component Contract

### 2.1 Every Component Must Implement

| Requirement | Description |
|-------------|-------------|
| **Props interface** | All props with type, required/optional, default |
| **All states** | Default, hover, active, focus, disabled, error, loading |
| **Accessibility** | ARIA roles, labels, keyboard navigation, focus management |
| **Responsive behavior** | Adapts to breakpoints as specified |
| **Edge cases** | Empty state, error state, loading state, overflow state |

### 2.2 Component Definition Format

Each component is specified as:

```
### ComponentName

**Category:** [Surface | Object | Action | Navigation | Feedback | AI | Overlay]
**Role:** One-line description of purpose
**States:** [default, hover, active, focus, disabled, error, loading, empty]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|

#### States

| State | Visual | Behavior |
|-------|--------|----------|

#### Accessibility

- ARIA role:
- Keyboard interaction:
- Focus management:

#### Responsive

| Breakpoint | Behavior |
|------------|----------|

#### Edge Cases

[Description of how the component handles edge cases]
```

---

## 3. Surface Components

### 3.1 Workspace

**Category:** Surface
**Role:** Root container that hosts all other components. Manages the surface state machine.
**States:** [default, empty]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `workspaceId` | string | yes | — | Current workspace ID |
| `focalObjectId` | string | no | null | Current focal object ID |
| `children` | ReactNode | yes | — | TopBar, ObjectBrowser, FocalArea, RelationshipPanel |
| `onStateChange` | callback | no | — | Fired when surface state changes |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Full layout with all panels | Renders children in specified layout |
| Empty | Empty workspace guidance | Shows EmptyState when no objects exist in workspace |

#### Accessibility

- ARIA role: `main`
- Keyboard: Tab moves between panels. Arrow keys navigate within panels.
- Focus: Initial focus on the focal object's first interactive element.

#### Responsive

| Breakpoint | Behavior |
|------------|----------|
| Desktop | Full multi-column layout |
| Tablet | Two-column (landscape) or single (portrait) |
| Mobile | Single column, bottom navigation |

#### Edge Cases

- **No workspace selected**: Redirects to last workspace or shows workspace picker.
- **Invalid workspace ID**: Shows error state with guidance.
- **Workspace deleted**: Shows "workspace not found" with option to return to default.

---

### 3.2 TopBar

**Category:** Surface
**Role:** Persistent header bar showing workspace context, object type, and global actions.
**States:** [default, compact, minimal]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `workspaceName` | string | yes | — | Current workspace display name |
| `objectType` | string | no | null | Current focal object type |
| `objectName` | string | no | null | Current focal object name |
| `onSearchOpen` | callback | yes | — | Opens object search |
| `onAIOpen` | callback | yes | — | Opens AI panel |
| `onNotificationsOpen` | callback | yes | — | Opens notification panel |
| `onProfileOpen` | callback | yes | — | Opens profile/settings |
| `onWorkspaceSwitch` | callback | yes | — | Opens workspace switcher |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Full: workspace name, object type, actions with labels | Desktop ≥ 1200px |
| Compact | Icons only, no labels | Tablet 600–899px |
| Minimal | Hamburger menu + workspace name + profile icon | Mobile < 600px |

#### Accessibility

- ARIA role: `navigation` with `aria-label="Top bar"`
- Keyboard: Tab through action items. Cmd+K opens search.
- Focus: Skip to content link is first focusable element.

#### Responsive

| Breakpoint | Behavior |
|------------|----------|
| Desktop | Full labels + icons. Height: 48px. |
| Tablet | Icons only, tooltips on hover. Height: 44px. |
| Mobile | Minimal. Height: 44px. |

#### Edge Cases

- **No workspace name**: Shows "Workspace" as fallback.
- **Too many items**: Overflow items collapse into a "More" menu.
- **Long workspace name**: Truncated with ellipsis, tooltip on hover.

---

### 3.3 ObjectBrowser

**Category:** Surface
**Role:** Sidebar listing objects in the current workspace. Collapsible.
**States:** [default, collapsed, empty, loading]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `objects` | ObjectCard[] | yes | — | Objects in the current workspace |
| `selectedId` | string | no | null | Currently selected object ID |
| `onSelect` | callback | yes | — | Object selection handler |
| `sortBy` | enum | no | 'recent' | Sort order: 'recent', 'type', 'alphabetical' |
| `filterType` | string | no | null | Filter by object type |
| `width` | number | no | 300 | Panel width in pixels |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Scrollable object list, sort/filter controls | Objects displayed as ObjectCards |
| Collapsed | Hidden, ~16px grip on left edge | Click grip to expand |
| Empty | "No objects in this workspace" | EmptyState component shown |
| Loading | Skeleton shimmer rows | 3–5 skeleton rows |

#### Accessibility

- ARIA role: `region` with `aria-label="Object browser"`
- Keyboard: Arrow keys to navigate, Enter to select. Focus search input automatically.
- Focus: Focus wraps within the browser when using arrow keys.

#### Responsive

| Breakpoint | Behavior |
|------------|----------|
| Desktop | Persistent sidebar, resizable |
| Tablet | Collapsible overlay, trigger from bottom bar |
| Mobile | Bottom sheet, trigger from "Objects" tab |

#### Edge Cases

- **No objects**: Shows EmptyState with "Create your first object" action.
- **Long object names**: Truncated to 2 lines, tooltip on hover.
- **Many objects (>100)**: Virtualized list, only visible items rendered.

---

### 3.4 FocalArea

**Category:** Surface
**Role:** Primary content area that displays the currently focused object.
**States:** [default, empty, loading, error]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `object` | object | no | null | Current focal object data |
| `disclosureLevel` | enum | no | 'default' | 'default', 'expand', 'detail', 'advanced' |
| `onAction` | callback | yes | — | Object action handler |
| `onRelationshipFollow` | callback | yes | — | Relationship link handler |
| `onDisclosureChange` | callback | no | — | Disclosure level change handler |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Object detail with 70/20/10 spacing | Object identity, state, primary action |
| Empty | Centered guidance | "Select an object from the browser" |
| Loading | Skeleton layout | Object-shaped skeleton with content blocks |
| Error | Error state | "Could not load object" with retry button |

#### Accessibility

- ARIA role: `region` with `aria-label="Focal object"`
- Keyboard: Tab through object fields and actions. Arrow keys for navigation within lists.
- Focus: Auto-focuses on the object's primary action button.

#### Responsive

| Breakpoint | Behavior |
|------------|----------|
| Desktop | Full width, multi-column content layout |
| Tablet | Full width, single column |
| Mobile | Full width, single column, reduced spacing |

#### Edge Cases

- **Deleted object**: Shows "Object no longer exists" with workspace return option.
- **Permission denied**: Shows "You don't have permission to view this object."
- **Very long content**: Scrolling container, object content scrolls independently.

---

### 3.5 RelationshipPanel

**Category:** Surface
**Role:** Sidebar showing relationships for the current focal object.
**States:** [default, collapsed, empty, loading]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `relationships` | Relationship[] | yes | — | Relationships of the focal object |
| `onFollow` | callback | yes | — | Relationship link click handler |
| `onFilter` | callback | no | — | Filter relationships by type |
| `width` | number | no | 280 | Panel width in pixels |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Typed relationship list | RelationshipLink items grouped by type |
| Collapsed | Hidden, ~16px grip on right edge | Click grip to expand |
| Empty | "No relationships for this object" | Subtle guidance text |
| Loading | Skeleton text lines | 3–4 relationship-shaped skeletons |

#### Accessibility

- ARIA role: `complementary` with `aria-label="Relationships"`
- Keyboard: Arrow keys to navigate relationships, Enter to follow.
- Focus: Focus starts on the first relationship link.

#### Responsive

| Breakpoint | Behavior |
|------------|----------|
| Desktop | Persistent sidebar, collapsible |
| Tablet | Slide-over panel from right |
| Mobile | Bottom sheet |

#### Edge Cases

- **No relationships**: Shows "Add first relationship" link.
- **Circular relationships**: Detected and displayed with a visual indicator.
- **Many relationships (>20)**: Collapsed by default, "Show all N" link.

---

## 4. Object Components

### 4.1 ObjectCard

**Category:** Object
**Role:** Compact display of an object for use in lists and browsers.
**States:** [default, selected, hover, loading]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `object` | Object | yes | — | Object data to display |
| `selected` | boolean | no | false | Is this object currently selected? |
| `onClick` | callback | yes | — | Click handler |
| `onContextMenu` | callback | no | — | Right-click/long-press context menu |
| `compact` | boolean | no | false | Compact mode for mobile |

#### Display

```
┌──────────────────────────────────────────────┐
│ [Icon]  Object Name                    [Type] │
│         Owner · Status · 2h ago              │
└──────────────────────────────────────────────┘
```

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | White bg, subtle border | Card at rest |
| Selected | Gold left border (3px), accent-subtle bg | Card is the current focal object |
| Hover | Slight lift (translateY -1px), shadow-md | Pointer hovers over card |
| Loading | Skeleton shimmer | Card placeholder |

#### Accessibility

- ARIA role: `article` with `aria-label="{type}: {name}"`
- Keyboard: Enter to select, ContextMenu key or Shift+F10 for context menu.
- Focus: Focus outline on card border.

#### Responsive

| Breakpoint | Behavior |
|------------|----------|
| Desktop | Full width, 72px height |
| Tablet | Full width, 64px height |
| Mobile | Full width, 60px height, compact mode |

#### Edge Cases

- **No name**: Shows "[Untitled {type}]" in italics.
- **Truncated text**: Name truncated to 2 lines, tooltip on hover.
- **Empty metadata**: Only shows available fields.

---

### 4.2 ObjectDetail

**Category:** Object
**Role:** Full object view in the focal area with progressive disclosure.
**States:** [default, expanded, detail, advanced, loading, error]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `object` | Object | yes | — | Object data |
| `disclosureLevel` | enum | no | 'default' | Current disclosure level |
| `onDisclosureChange` | callback | no | — | Level change handler |
| `onAction` | callback | yes | — | Action handler |
| `readOnly` | boolean | no | false | Prevent editing |

#### Display Structure

```
╔══════════════════════════════════════════════╗
║  Object Name                                 ║
║  Status ● Owner · Created 2h ago             ║
║                                              ║
║  ┌ Disclosure Level: Default ───────────┐    ║
║  │  Identity · State · Primary Action    │    ║
║  └───────────────────────────────────────┘    ║
║                                              ║
║  ▼ [Expand]  ─────────────────────────────── ║
║  │  Key Relationships · Recent Activity      ║
║  │  Secondary Actions                        ║
║  └───────────────────────────────────────────║
║                                              ║
║  ▼▼ [Detail]  ────────────────────────────── ║
║  │  All Fields · Full History · Change Log   ║
║  └───────────────────────────────────────────║
║                                              ║
║  ■■■ [Advanced]  ─────────────────────────── ║
║  │  Permissions · Integrations · Audit       ║
║  └───────────────────────────────────────────║
╚══════════════════════════════════════════════╝
```

#### Accessibility

- ARIA role: `article` with `aria-label="Object detail: {name}"`
- Keyboard: Tab through sections. Enter to expand/collapse sections.
- Focus: Focus on the object name as the first focusable element.

#### Responsive

| Breakpoint | Behavior |
|------------|----------|
| Desktop | Multi-column content layout, full spacing |
| Tablet | Single column, reduced spacing |
| Mobile | Single column, compact spacing |

#### Edge Cases

- **No content**: Shows "This object has no content yet" with create action.
- **Very long history**: Paginated timeline, 20 events per page.
- **Permission-restricted fields**: Greyed out, "Request access" tooltip.

---

### 4.3 ObjectField

**Category:** Object
**Role:** Single field display within an object detail.
**States:** [default, hover, editing, error, read-only]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `label` | string | yes | — | Field label |
| `value` | any | yes | — | Field value |
| `type` | enum | no | 'text' | 'text', 'number', 'date', 'boolean', 'select', 'relationship', 'markdown' |
| `editable` | boolean | no | false | Is this field editable? |
| `onEdit` | callback | no | — | Edit handler (returns new value) |
| `validation` | callback | no | — | Value validation function |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Label (--text-sm, secondary) + Value (--text-base, primary) | Read-only display |
| Hover | Subtle background tint if editable | Indicates editability |
| Editing | Inline input replaces value | TextInput, TextArea, or Select based on type |
| Error | Red border on input, error message below | Validation error display |
| Read-only | Greyed out, no edit indicator | Field is informational only |

#### Accessibility

- ARIA role: Depends on type. `textbox` for editable fields. `status` for read-only.
- Keyboard: Enter to edit (if editable). Tab to move between fields.
- Focus: Focus on the value when entering edit mode.

#### Edge Cases

- **Empty value**: Shows "—" (em dash) for empty fields, not blank.
- **Long value**: Truncated with "Show more" link for long text.
- **Invalid value**: Shows error state with validation message.

---

## 5. Action Components

### 5.1 Button

**Category:** Action
**Role:** Single action trigger.
**States:** [default, hover, active, focus, disabled, loading]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `variant` | enum | no | 'primary' | 'primary', 'secondary', 'ghost', 'danger', 'accent' |
| `size` | enum | no | 'md' | 'sm' (32px), 'md' (40px), 'lg' (48px) |
| `label` | string | yes | — | Button text |
| `icon` | string | no | null | Optional icon name |
| `iconPosition` | enum | no | 'left' | 'left', 'right' |
| `disabled` | boolean | no | false | Disabled state |
| `loading` | boolean | no | false | Loading state |
| `onClick` | callback | yes | — | Click handler |
| `type` | string | no | 'button' | 'button', 'submit', 'reset' |
| `fullWidth` | boolean | no | false | Stretch to container width |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Filled (primary), outline (secondary), no bg (ghost) | At rest |
| Hover | Slight background shift, cursor pointer | Pointer over button |
| Active | Pressed state, background shift | Mouse down |
| Focus | 2px accent outline | Keyboard focus |
| Disabled | 0.4 opacity, no pointer events | Cannot interact |
| Loading | Spinner replaces icon, label dimmed | Asynchronous action in progress |

#### Accessibility

- ARIA role: `button`
- Keyboard: Enter/Space to activate.
- Focus: Visible focus indicator.

#### Responsive

| Breakpoint | Behavior |
|------------|----------|
| Desktop | Icon + label |
| Mobile | Icon only (with tooltip) or full width |

#### Edge Cases

- **Rapid clicks**: Debounced at 300ms to prevent double-submission.
- **No onClick**: Rendered as a disabled button.
- **Very long label**: Truncated with ellipsis.

---

### 5.2 SearchBar

**Category:** Action
**Role:** Object search input with real-time results.
**States:** [default, focused, hasResults, noResults, loading]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `placeholder` | string | no | 'Search objects…' | Placeholder text |
| `onSearch` | callback | yes | — | Search query handler |
| `onSelect` | callback | yes | — | Result selection handler |
| `results` | ObjectCard[] | no | [] | Search results |
| `recentSearches` | string[] | no | [] | Recent search history |
| `autoFocus` | boolean | no | false | Auto-focus on open |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Search icon + placeholder text | At rest |
| Focused | Accent border, placeholder fades | User types query |
| HasResults | Results list below input | Real-time filtered results |
| NoResults | "No results found" message | Empty result state |
| Loading | Spinner in input field | Results loading |

#### Accessibility

- ARIA role: `combobox` with `aria-expanded` and `aria-activedescendant`
- Keyboard: Type to search, Arrow keys to navigate results, Enter to select, Escape to dismiss.
- Focus: Auto-focus on open. Focus trap within search.

#### Responsive

| Breakpoint | Behavior |
|------------|----------|
| Desktop | Full-width overlay, centered |
| Mobile | Full-screen overlay, keyboard opens |

#### Edge Cases

- **Empty query**: Shows recent searches or "Start typing to search."
- **Network error**: Shows "Search unavailable. Try again." with retry.
- **Very long query**: Full-width input, scrolls within.

---

## 6. Navigation Components

### 6.1 Breadcrumb

**Category:** Navigation
**Role:** Shows the current position in the object graph.
**States:** [default, truncated]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `path` | PathSegment[] | yes | — | Array of path segments |
| `onNavigate` | callback | yes | — | Click handler for any segment |

#### PathSegment

| Prop | Type | Description |
|------|------|-------------|
| `label` | string | Display label |
| `type` | string | Object type (for icon) |
| `id` | string | Object ID for navigation |
| `isCurrent` | boolean | Is this the current position? |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Full path: Workspace > Type > Name | All segments visible |
| Truncated | Workspace > … > Name | Middle segments collapsed when > 3 |

#### Accessibility

- ARIA role: `navigation` with `aria-label="Breadcrumb"`
- Keyboard: Tab through segments. Enter to navigate.
- Focus: Current segment is not focusable (aria-current="page").

#### Responsive

| Breakpoint | Behavior |
|------------|----------|
| Desktop | Full path |
| Mobile | Name only, with back button |

---

### 6.2 RelationshipLink

**Category:** Navigation
**Role:** Displays a relationship between objects and allows navigation.
**States:** [default, hover, active]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `relationship` | Relationship | yes | — | Relationship data |
| `onFollow` | callback | yes | — | Click handler |
| `direction` | enum | no | 'outgoing' | 'outgoing', 'incoming' |

#### Display

```
┌──────────────────────────────────────────────┐
│  ↑ involves  ────  Document: Q3 Proposal     │
│                    Updated 2h ago · Alice     │
└──────────────────────────────────────────────┘
```

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Type label + target name + metadata | At rest |
| Hover | Underline + accent text color | Pointer over link |
| Active | Brief flash | Click |

#### Accessibility

- ARIA role: `link` with `aria-label="{type} to {target name}"`
- Keyboard: Enter to follow.
- Focus: Visible focus indicator.

---

## 7. Feedback Components

### 7.1 Toast

**Category:** Feedback
**Role:** Temporary notification for action results.
**States:** [success, error, info, warning]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `message` | string | yes | — | Toast message |
| `type` | enum | no | 'info' | 'success', 'error', 'info', 'warning' |
| `duration` | number | no | 4000 | Auto-dismiss time in ms (0 = persistent) |
| `action` | Action | no | null | Optional action button |
| `onDismiss` | callback | no | — | Dismiss handler |
| `undo` | callback | no | null | Optional undo action |

#### Action

| Prop | Type | Description |
|------|------|-------------|
| `label` | string | Action button label |
| `onClick` | callback | Action handler |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Success | Green left border, checkmark icon | Auto-dismiss 4s |
| Error | Red left border, X icon | Auto-dismiss 8s |
| Info | Blue left border, info icon | Auto-dismiss 4s |
| Warning | Orange left border, warning icon | Auto-dismiss 6s |

#### Accessibility

- ARIA role: `alert` with `aria-live="polite"`
- Keyboard: Focus moves to toast. Escape to dismiss. Tab to action button.
- Focus: Toast appears in top-right, does not steal focus unless critical.

#### Edge Cases

- **Multiple toasts**: Stacked vertically, max 3 visible.
- **Very long message**: Truncated to 2 lines with "Show more" link.
- **Persistent toast**: No auto-dismiss, requires user action.

---

### 7.2 EmptyState

**Category:** Feedback
**Role:** Guidance when no content exists.
**States:** [default]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `icon` | string | yes | — | Icon name for the empty state |
| `title` | string | yes | — | Primary message |
| `description` | string | no | null | Secondary guidance |
| `action` | Action | no | null | Optional primary action button |

#### Display

```
┌──────────────────────────────────────────────┐
│                                              │
│              [Icon, 64px]                     │
│                                              │
│         No objects in this workspace          │
│                                              │
│    Create your first object to get started    │
│                                              │
│         [Create Object]                       │
│                                              │
└──────────────────────────────────────────────┘
```

#### Accessibility

- ARIA role: `status`
- Keyboard: Focus on action button if present.

---

## 8. AI Components

### 8.1 AIPanel

**Category:** AI
**Role:** AI collaborator conversation panel, contextual to the current object.
**States:** [closed, open, loading, empty]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `objectId` | string | no | null | Current object context |
| `onSend` | callback | yes | — | Send message handler |
| `messages` | AIMessage[] | yes | — | Conversation history |
| `onClose` | callback | yes | — | Close panel handler |
| `suggestions` | AISuggestion[] | no | [] | Contextual AI suggestions |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Closed | Hidden | Panel is not visible |
| Open | Slide-over from right edge | Message history + input + suggestions |
| Loading | "Thinking..." indicator | AI is generating response |
| Empty | Welcome message | "I'm here to help with this object." |

#### Accessibility

- ARIA role: `complementary` with `aria-label="AI collaborator"`
- Keyboard: Tab to cycle through messages, suggestions, and input. Cmd+Enter to send.
- Focus: Focus input on open. Escape to close.

#### Responsive

| Breakpoint | Behavior |
|------------|----------|
| Desktop | Slide-over panel, 420px width |
| Tablet | Slide-over, 100% width |
| Mobile | Full-screen overlay |

#### AI Message

| Prop | Type | Description |
|------|------|-------------|
| `id` | string | Message ID |
| `role` | 'human' | 'ai' | Sender role |
| `content` | string | Message content |
| `confidence` | enum | 'high', 'medium', 'low', 'unknown' | AI confidence level |
| `evidence` | Evidence[] | Optional evidence links |
| `actions` | Action[] | Optional proposed actions |
| `timestamp` | string | ISO timestamp |

---

### 8.2 AISuggestion

**Category:** AI
**Role:** Inline AI suggestion within the focal area.
**States:** [default, dismissed, accepted]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `message` | string | yes | — | Suggestion text |
| `confidence` | enum | no | 'medium' | 'high', 'medium', 'low' |
| `onAccept` | callback | yes | — | Accept handler |
| `onDismiss` | callback | yes | — | Dismiss handler |
| `onLearnMore` | callback | no | — | "Show reasoning" handler |

#### Display

```
┌──────────────────────────────────────────────────┐
│  💡 AI suggests: Add evidence to this decision   │
│     I notice this Decision is missing a link to   │
│     supporting evidence. Would you like to add    │
│     the Q3 Revenue Report as evidence?            │
│                                                  │
│     [Accept]  [Dismiss]  [Show reasoning ▸]      │
│                                    ── low conf.   │
└──────────────────────────────────────────────────┘
```

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | Subtle accent background, visible | Suggestion is displayed |
| Dismissed | Fades out, removed from DOM | User dismissed |
| Accepted | Checkmark animation, transitions to done | User accepted |

#### Accessibility

- ARIA role: `status` with `aria-live="polite"`
- Keyboard: Tab to accept/dismiss buttons. Escape to dismiss.

---

## 9. Overlay Components

### 9.1 Modal

**Category:** Overlay
**Role:** Blocking dialog requiring user action.
**States:** [open, closed]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `isOpen` | boolean | yes | — | Modal visibility |
| `title` | string | yes | — | Modal title |
| `children` | ReactNode | yes | — | Modal content |
| `onClose` | callback | yes | — | Close handler |
| `size` | enum | no | 'md' | 'sm' (400px), 'md' (560px), 'lg' (720px) |
| `closeOnOverlay` | boolean | no | true | Close when clicking backdrop |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Open | Centered card, backdrop dim (0.4 opacity) | Focus trap, scroll lock |
| Closed | Hidden | Removed from DOM |

#### Accessibility

- ARIA role: `dialog` with `aria-modal="true"` and `aria-labelledby` for title
- Keyboard: Focus trap within modal. Tab cycles through elements. Escape to close.
- Focus: Focus on first interactive element on open. Return focus to trigger on close.

---

### 9.2 BottomSheet

**Category:** Overlay
**Role:** Mobile action sheet or content panel.
**States:** [closed, peek, half, full]

#### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `isOpen` | boolean | yes | — | Sheet visibility |
| `children` | ReactNode | yes | — | Sheet content |
| `onClose` | callback | yes | — | Close handler |
| `peekHeight` | number | no | 80 | Peek height in pixels |
| `fullHeight` | number | no | 0.85 | Full height as fraction of viewport |
| `dragHandle` | boolean | no | true | Show drag handle indicator |

#### States

| State | Visual | Behavior |
|-------|--------|----------|
| Closed | Hidden below viewport | Not visible |
| Peek | 80px visible, drag handle | Quick glance at content |
| Half | 50% of viewport | Content browsing |
| Full | 85% of viewport | Full content interaction |

#### Accessibility

- ARIA role: `dialog` with `aria-modal="true"`
- Keyboard: Escape to close. Tab through content.
- Gesture: Swipe down to dismiss, drag handle to resize.

---

## 10. Component Testing Requirements

### 10.1 Every Component Must Have

| Test Type | Coverage | Examples |
|-----------|----------|----------|
| **Render test** | 100% | Renders with default props, renders with all props |
| **State test** | 100% | Each state renders correctly |
| **Interaction test** | 100% | Click, hover, focus, keyboard |
| **Accessibility test** | 100% | ARIA roles, keyboard navigation, focus management |
| **Responsive test** | 100% | Renders correctly at each breakpoint |
| **Edge case test** | 90%+ | Empty, error, loading, overflow, truncation |

### 10.2 Testing Tools

| Tool | Purpose |
|------|---------|
| **React Testing Library** | Component render and interaction tests |
| **Jest** | Test runner and assertions |
| **Storybook** | Visual state documentation and manual testing |
| **axe-core** | Automated accessibility testing |
| **Playwright** | Responsive and E2E testing |

### 10.3 Test Example

```javascript
// Button component test
describe('Button', () => {
  it('renders with label', () => {
    render(<Button label="Submit" onClick={() => {}} />);
    expect(screen.getByText('Submit')).toBeInTheDocument();
  });

  it('fires onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button label="Submit" onClick={handleClick} />);
    fireEvent.click(screen.getByText('Submit'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<Button label="Submit" onClick={() => {}} loading />);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByTestId('spinner')).toBeInTheDocument();
  });

  it('is keyboard accessible', () => {
    const handleClick = jest.fn();
    render(<Button label="Submit" onClick={handleClick} />);
    screen.getByText('Submit').focus();
    fireEvent.keyDown(screen.getByText('Submit'), { key: 'Enter' });
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

---

## 11. Relationship to Other Documents

| Document | Relationship |
|----------|-------------|
| **08_experience_canon.md** | Components implement the experience principles defined in the canon |
| **INFORMATION_ARCHITECTURE.md** | Components are the building blocks of the IA surfaces |
| **DESIGN_SYSTEM.md** | Components use the design tokens, typography, spacing, and colors defined there |
| **DESKTOP_INTERACTION_MODEL.md** | Components implement the interaction patterns defined there |
| **MOBILE_INTERACTION_MODEL.md** | Components implement the mobile-specific adaptations defined there |
| **09_repository_canon.md** | Component code is organized by category in the repository |
| **11_engineering_canon.md** | Component testing follows the engineering standards defined there |

---

> **End of Component Specification**
> **[Return to INDEX](#)**