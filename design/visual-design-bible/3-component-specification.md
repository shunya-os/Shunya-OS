# SHUNYA Component Specification v1.0

> **Figma-equivalent design specification**
> Implementation-ready specification for every SHUNYA component.
> Every component defines: purpose, anatomy, spacing, variants, interaction states, accessibility, animation, and usage rules.

---

## Table of Contents

1. [Button](#1-button)
2. [Card](#2-card)
3. [Input](#3-input)
4. [Dropdown / Select](#4-dropdown--select)
5. [Navigation Item](#5-navigation-item)
6. [Tab](#6-tab)
7. [Modal / Dialog](#7-modal--dialog)
8. [Drawer / Side Panel](#8-drawer--side-panel)
9. [Identity Strip](#9-identity-strip)
10. [Search Overlay](#10-search-overlay)
11. [Timeline Item](#11-timeline-item)
12. [Event Card (Activity Card)](#12-event-card-activity-card)
13. [Conversation Message](#13-conversation-message)
14. [Notification / Flash Message](#14-notification--flash-message)
15. [Empty State](#15-empty-state)
16. [Link Chip](#16-link-chip)
17. [Health Indicator (Status Dot)](#17-health-indicator-status-dot)
18. [Skeleton Loader](#18-skeleton-loader)
19. [Badge](#19-badge)
20. [Section Label](#20-section-label)

---

## 1. Button

### Purpose
Primary call-to-action, secondary action, or tertiary/link-style action.

### Anatomy

```
┌──────────────────────┐
│  Label          →    │
└──────────────────────┘
```

### Dimensions

| Property | Value |
|----------|-------|
| Height | 36px |
| Horizontal padding | 22px |
| Border-radius | 10px |
| Font | Inter, 12px, weight 500 |
| Letter-spacing | 0.02em |
| Icon size | 14px (arrow) |
| Gap (icon–text) | 6px |

### Variants

#### Primary Button (`btn-p`)

| State | Background | Text | Border |
|-------|------------|------|--------|
| Default | `--shunya-text` (#1a1c1d) | `--shunya-surface` (#ffffff) | None |
| Hover | Same | Same | Opacity: 0.85 |
| Active | Same | Same | Opacity: 0.75 |
| Focus-visible | Same | Same | `outline: 2px solid var(--shunya-gold); outline-offset: 2px` |
| Disabled | Same | Same | Opacity: 0.4, cursor: not-allowed |

#### Outline Button (`btn-o`)

| State | Background | Text | Border |
|-------|------------|------|--------|
| Default | Transparent | `--shunya-text` | 1px solid `--shunya-border` |
| Hover | Transparent | `--shunya-text` | 1px solid `--shunya-border-hover` |
| Active | Transparent | `--shunya-text` | 1px solid `--shunya-border-hover` |
| Focus-visible | Transparent | `--shunya-text` | `outline: 2px solid var(--shunya-gold); outline-offset: 2px` |
| Disabled | Transparent | `--shunya-text-tertiary` | 1px solid `--shunya-border` |

#### Ghost Button

| State | Background | Text | Border |
|-------|------------|------|--------|
| Default | Transparent | `--shunya-text-secondary` | None |
| Hover | Transparent | `--shunya-text` | None |
| Active | Transparent | `--shunya-text` | None |
| Focus-visible | Transparent | `--shunya-text` | `outline: 2px solid var(--shunya-gold); outline-offset: 2px` |
| Disabled | Transparent | `--shunya-text-faint` | None |

### Animation

| State | Effect | Duration | Easing |
|-------|--------|----------|--------|
| Hover | Opacity transition | 200ms | `--shunya-ease` |
| Arrow hover | TranslateX(2px) | 300ms | `--shunya-ease` |
| Disabled | Instant | 0ms | — |

### Accessibility

- `role="button"` for non-`<button>` elements
- `aria-disabled` for disabled state, not just CSS class
- Focus-visible ring must be visible in high-contrast mode
- Minimum touch target: 44px × 44px (use padding to meet this)

### Usage Rules

- One primary button per section
- Primary is always the dark text colour (`--shunya-text`)
- Gold is never used for buttons
- Button text is not uppercase
- Arrow icon is optional (used for "Get started →" style CTAs)

---

## 2. Card

### Purpose
Grouped content container for information, events, and data.

### Anatomy

```
┌──────────────────────────────┐
│  Title / Header  (optional)   │
│  ─────────────────────────────│
│  Body content                 │
│                               │
│  Footer / Meta  (optional)    │
└──────────────────────────────┘
```

### Dimensions

| Property | Value |
|----------|-------|
| Padding | 20px (standard), 16px (compact) |
| Border-radius | 16px |
| Border | 1px solid `--shunya-border` |
| Background | `--shunya-surface` (#ffffff) |
| Shadow | None (default), `--shunya-shadow-md` (elevated) |

### Variants

| Variant | Padding | Border | Hover | Usage |
|---------|---------|--------|-------|-------|
| Default | 20px | `--shunya-border` | `--shunya-border-hover` | General content |
| Event | 20px | `--shunya-border` | `--shunya-gold-light` | Landing page activity |
| Intel | 10px 12px | `--shunya-border` | None | Intelligence pane |
| mz-item | 12px 16px | `--shunya-border` | `--shunya-border-hover` | Morning Zero items |
| Compact | 16px | `--shunya-border` | `--shunya-border-hover` | Dense content |

### Interaction States

| State | Effect | Duration |
|-------|--------|----------|
| Default | Border: `--shunya-border` | — |
| Hover | Border: `--shunya-border-hover` or `--shunya-gold-light` | 300ms |
| Focus-visible | Outline: 2px gold, offset 2px | — |

### Accessibility

- Cards are not interactive by default
- If clickable, use `role="button"`, `tabindex="0"`, and keyboard handler
- Card title should be a heading element (`h2`, `h3`, etc.)

### Usage Rules

- Cards remain on the same elevation — no hover lift effect
- No shadow on default cards
- Event cards use gold border on hover (not default)
- Intel cards have no hover effect

---

## 3. Input

### Purpose
Text input for forms, search, and data entry.

### Anatomy

```
┌──────────────────────────────┐
│  Label (above)               │
│  ┌──────────────────────────┐│
│  │ Placeholder text...      ││
│  └──────────────────────────┘│
└──────────────────────────────┘
```

### Dimensions

| Property | Value |
|----------|-------|
| Height | 38px |
| Horizontal padding | 14px |
| Border-radius | 10px |
| Font | Inter, 14px, weight 400 |
| Background | `--shunya-surface` |
| Border | 1px solid `--shunya-border` |

### States

| State | Border | Background | Text |
|-------|--------|------------|------|
| Default | `--shunya-border` | `--shunya-surface` | `--shunya-text` |
| Focus | `rgba(26,28,29,0.2)` | `--shunya-surface` | `--shunya-text` |
| Placeholder | `--shunya-border` | `--shunya-surface` | `--shunya-text-faint` |
| Disabled | `--shunya-border` | `--shunya-surface` | `--shunya-text-tertiary`, opacity: 0.4 |
| Error | `#ff6b6b` | `--shunya-surface` | `--shunya-text` |
| Read-only | `--shunya-border` | Transparent | `--shunya-text` |

### Label

| Property | Value |
|----------|-------|
| Font | Inter, 12px, weight 500 |
| Colour | `--shunya-text-secondary` |
| Margin-bottom | 6px |

### Accessibility

- `label` element with `for` attribute matching `id`
- Error message linked with `aria-describedby`
- Placeholder text is not a substitute for a label
- Minimum contrast: 4.5:1 for label text

### Usage Rules

- No blue focus ring (use subtle dark border)
- No input background change on focus
- No custom styling for autofill (browser default)
- Use `type="search"` for search inputs

---

## 4. Dropdown / Select

### Purpose
Choosing from a list of options.

### Anatomy

```
┌──────────────────────┐
│  Selected option  ▼  │
└──────────────────────┘
┌──────────────────────┐
│  Option 1            │
│  Option 2         ✓  │
│  Option 3            │
└──────────────────────┘
```

### Dimensions

| Element | Property | Value |
|---------|----------|-------|
| Trigger | Height | 38px |
| Trigger | Padding | 10px 14px |
| Trigger | Border-radius | 10px |
| Menu | Padding | 6px 0 |
| Menu | Border-radius | 10px |
| Menu | Shadow | `--shunya-shadow-lg` |
| Item | Padding | 8px 14px |
| Item | Font | Inter, 13px |

### States

| State | Trigger | Menu |
|-------|---------|------|
| Closed | Same as input default | Hidden |
| Open | Same as input focus | `--shunya-surface`, shadow-lg |
| Selected | — | Subtle background tint |
| Hover (item) | — | `rgba(26,28,29,0.05)` |
| Focus-visible | Gold outline | — |

### Accessibility

- Use native `<select>` for simple dropdowns
- Custom dropdowns require `role="listbox"`, `role="option"`, `aria-selected`
- Keyboard navigation: arrow keys, Enter, Escape

### Usage Rules

- No custom dropdown for fewer than 3 options (use radio buttons)
- No multi-select in v1.0
- No search within dropdown (deferred)

---

## 5. Navigation Item

### Purpose
Primary navigation link within the workspace left zone.

### Anatomy

```
┌──────────────────────────────────┐
│  SECTION LABEL                   │
│  ┌──────────────────────────────┐│
│  │  ○  Label                23  ││
│  │  ○  Label              →    ││
│  └──────────────────────────────┘│
└──────────────────────────────────┘
```

### Dimensions

| Element | Property | Value |
|---------|----------|-------|
| Nav item | Padding | 7px 16px |
| Nav item | Font | Inter, 13px, weight 400 |
| Nav item | Gap (icon-label) | 8px |
| Icon | Size | 18px |
| Badge | Font | 10px, weight 500 |
| Badge | Padding | 1px 6px |
| Badge | Border-radius | 8px |
| Section label | Padding | 8px 16px 4px |
| Section label | Font | Inter, 10px, weight 600, uppercase, letter-spacing 0.06em |

### States

| State | Background | Text | Icon |
|-------|------------|------|------|
| Default | Transparent | `--shunya-text-secondary` | `--shunya-text-secondary` |
| Hover | `rgba(25,27,28,0.05)` | `--shunya-text` | `--shunya-text` |
| Active | `rgba(25,27,28,0.07)` | `--shunya-text`, weight 500 | `--shunya-text` |
| Focus-visible | Highlighted | — | — |

### Accessibility

- `role="navigation"` on the nav container
- `aria-current="page"` on active item
- Keyboard: Tab to enter, arrow keys to navigate, Enter to select

### Usage Rules

- Section labels are uppercase, 10px, faint colour
- Icons are 18px stroke-only
- Badges float right with faint background
- No nested sub-navigation in v1.0

---

## 6. Tab

### Purpose
Switch between content panels within a workspace object.

### Anatomy

```
┌──────┬──────┬──────┬──────┐
│ Tab1 │ Tab2 │ Tab3 │ Tab4 │
└──────┴──────┴──────┴──────┘
```

### Dimensions

| Property | Value |
|----------|-------|
| Padding | 10px 16px |
| Font | Inter, 12px, weight 400 |
| Colour (default) | `--shunya-text-tertiary` |
| Colour (active) | `--shunya-text` |
| Active indicator | 2px solid bottom border |

### States

| State | Text | Bottom Border |
|-------|------|---------------|
| Default | `--shunya-text-tertiary` | Transparent, 2px |
| Hover | `--shunya-text-secondary` | Transparent |
| Active | `--shunya-text` | `--shunya-text`, 2px |
| Focus-visible | — | Gold outline |

### Accessibility

- `role="tablist"` on container, `role="tab"` on each tab
- `aria-selected="true"` on active tab
- `role="tabpanel"` with `aria-labelledby` on panels
- Keyboard: arrow keys to switch tabs

### Usage Rules

- Tabs are used within object workspaces only
- Maximum 7 tabs per object
- No icons within tabs
- No dropdown tabs

---

## 7. Modal / Dialog

### Purpose
Focused task requiring user attention before continuing.

### Anatomy

```
┌──────────────────────────────────────┐
│  Title                    Close (×)  │
│  ─────────────────────────────────── │
│  Body content                        │
│                                      │
│  [Cancel]  [Confirm]                 │
└──────────────────────────────────────┘
```

### Dimensions

| Property | Value |
|----------|-------|
| Max width | 480px |
| Padding | 24px |
| Border-radius | 16px |
| Overlay background | `rgba(250,249,247,0.97)` |
| Overlay backdrop-filter | `blur(12px)` |
| Shadow | `--shunya-shadow-xl` |

### Animation

| State | Animation | Duration | Easing |
|-------|-----------|----------|--------|
| Enter | Scale(0.95→1) + opacity(0→1) | 400ms | `--shunya-ease` |
| Exit | Opacity(1→0) | 200ms | `--shunya-ease-out` |

### Accessibility

- `role="dialog"`, `aria-modal="true"`, `aria-labelledby` for title
- Trap focus within the modal when open
- Close on Escape key
- Close on overlay click (optional, but recommended)
- Return focus to trigger element on close

### Usage Rules

- Modals are for focused tasks, not information display
- Use a drawer for supplementary content
- Maximum height: 80vh (scroll body if needed)
- No nested modals

---

## 8. Drawer / Side Panel

### Purpose
Supplementary content that doesn't require full navigation.

### Anatomy

```
┌──────────────┬─────────────────────┐
│  Main Content│  Drawer (340px)     │
│              │  ┌───────────────┐  │
│              │  │  Title        │  │
│              │  │  ──────────── │  │
│              │  │  Content...   │  │
│              │  └───────────────┘  │
└──────────────┴─────────────────────┘
```

### Dimensions

| Property | Value |
|----------|-------|
| Width | 340px |
| Padding | 16px |
| Header | 11px, weight 600, uppercase, 0.06em tracking |
| Shadow | `--shunya-shadow-lg` |

### Animation

| State | Animation | Duration | Easing |
|-------|-----------|----------|--------|
| Enter | Slide from right | 400ms | `--shunya-ease` |
| Exit | Slide to right | 300ms | `--shunya-ease-out` |

### Accessibility

- `role="complementary"` or `role="region"`
- `aria-label` describing the drawer content
- Close on Escape key

### Usage Rules

- Drawers slide from the right edge
- Drawers overlay content (not push it)
- Drawers do not have a visible overlay (unlike modals)
- Use for: object details, context panels, quick edits

---

## 9. Identity Strip

### Purpose
Top bar providing context, navigation breadcrumbs, and system status.

### Anatomy

```
┌─────────────────────────────────────────────────────────┐
│  ● SHUNYA  ›  Objects  ›  Project Alpha     ⚠  14:30  │
└─────────────────────────────────────────────────────────┘
```

### Dimensions

| Property | Value |
|----------|-------|
| Height | 44px |
| Padding | 0 20px |
| Background | `--top-bar-bg` (#faf9f8) |
| Border-bottom | 1px solid `--shunya-border` |
| Font | Inter, 12–13px |

### Elements

| Element | Position | Spec |
|---------|----------|------|
| Gold dot | Left | 5px, `--shunya-gold` |
| SHUNYA wordmark | Left | 13px, weight 500 |
| Breadcrumb | Left | 12px, `--shunya-text-tertiary`, sep: `--shunya-text-faint` |
| Attention dot | Right | 6px, colour-coded (green/yellow/red) |
| Time | Right | 12px, tabular-nums |

### Accessibility

- `role="banner"` or `<header>`
- Breadcrumb: `nav` with `aria-label="Breadcrumb"`

---

## 10. Search Overlay

### Purpose
Full-screen command palette and search interface.

### Anatomy

```
┌───────────────────────────────────────────────┐
│                                               │
│                                               │
│              ┌────────────────────┐           │
│              │  Search...         │           │
│              └────────────────────┘           │
│              Type to search                   │
│                                               │
│              ┌─ Search Results ─┐             │
│              │  Result 1        │             │
│              │  Result 2        │             │
│              │  Result 3        │             │
│              └──────────────────┘             │
│                                               │
└───────────────────────────────────────────────┘
```

### Dimensions

| Property | Value |
|----------|-------|
| Overlay background | `rgba(250,249,247,0.97)` |
| Backdrop filter | `blur(12px)` |
| Input font | 26px, weight 300 |
| Input background | Transparent |
| Input border | None |
| Max width | 520px |
| Results max height | 50vh |

### Animation

| State | Animation | Duration | Easing |
|-------|-----------|----------|--------|
| Open | Opacity(0→1) | 300ms | `--shunya-ease` |
| Close | Opacity(1→0) | 200ms | `--shunya-ease-out` |

### Accessibility

- Auto-focus the input on open
- Close on Escape
- `aria-label="Search"` on the overlay
- Results role="listbox" with role="option"

### Usage Rules

- Triggered by keyboard shortcut (Cmd+K / Ctrl+K)
- No decorative search icon in the input
- No recent searches in v1.0

---

## 11. Timeline Item

### Purpose
Chronological history of events, decisions, and changes for an object.

### Anatomy

```
  ●  Title
  │  Meta information
  │
  ●  Title
  │  Meta information
```

### Dimensions

| Element | Property | Value |
|---------|----------|-------|
| Item | Padding | 10px 0 |
| Gap (dot–content) | 12px |
| Dot | Size | 8px |
| Dot | Border-radius | 50% |
| Connecting line | Width | 2px |
| Connecting line | Colour | `--shunya-border` |
| Title | Font | 13px, `--shunya-text` |
| Meta | Font | 11px, `--shunya-text-tertiary` |

### Dot Colours

| Type | Colour | Usage |
|------|--------|-------|
| Default | `--shunya-text-faint` | Generic events |
| Decision | `#74c0fc` (blue) | Decisions made |
| Change | `#fab005` (yellow) | State changes |
| Risk | `#fd7e14` (orange) | Risks identified |
| Evidence | `#51cf66` (green) | Evidence collected |

### Usage Rules

- Connecting line stretches between all dots
- Last item has no trailing line
- Timeline is read-only (no drag-to-reorder)

---

## 12. Event Card (Activity Card)

### Purpose
Real-time activity display on the landing page.

### Anatomy

```
┌──────────────────────────────────┐
│  ●  Contract signed              │
│     New partnership agreement... │
│     Just now · Legal             │
└──────────────────────────────────┘
```

### Dimensions

| Element | Property | Value |
|---------|----------|-------|
| Card | Padding | 20px |
| Card | Border-radius | 16px |
| Icon container | Size | 36px × 36px |
| Icon container | Border-radius | 10px |
| Title | Font | 13px, weight 500, `--shunya-text` |
| Description | Font | 11px, `--shunya-text-label` (rgba 35%) |
| Timestamp | Font | 10px, `--shunya-text-faint` |
| Gap (icon–content) | 14px | |
| Gap (title–desc) | 2px | |
| Gap (desc–time) | 6px | |

### Icon Background Colours

| Icon | Background |
|------|------------|
| Gold | `rgba(164,134,95,0.1)` |
| Blue | `rgba(59,130,246,0.1)` |
| Emerald | `rgba(16,185,129,0.1)` |
| Amber | `rgba(245,158,11,0.1)` |

### Interaction

| State | Effect | Duration |
|-------|--------|----------|
| Default | Border: `--shunya-border` | — |
| Hover | Border: `--shunya-gold-light` | 300ms |

---

## 13. Conversation Message

### Purpose
Display AI-human conversation within the workspace.

### Anatomy

```
┌──────────────────────────────────────┐
│  ┌──────────────────────────────┐    │
│  │  Human message               │    │
│  │  10:30 AM                    │    │
│  └──────────────────────────────┘    │
│                                      │
│    ┌──────────────────────────────┐  │
│    │  Assistant message           │  │
│    │  10:30 AM                    │  │
│    └──────────────────────────────┘  │
│                                      │
│  ┌──────────────────────────────┐    │
│  │  Type a message...  [Send]   │    │
│  └──────────────────────────────┘    │
└──────────────────────────────────────┘
```

### Human Message

| Property | Value |
|----------|-------|
| Background | `--shunya-text` (#1a1c1d) |
| Text colour | White |
| Margin-left | 32px |
| Border-radius | 10px |
| Padding | 10px 14px |
| Font | 13px, line-height 1.5 |

### Assistant Message

| Property | Value |
|----------|-------|
| Background | `--shunya-surface` (#ffffff) |
| Text colour | `--shunya-text-secondary` |
| Margin-right | 32px |
| Border | 1px solid `--shunya-border` |
| Border-radius | 10px |
| Padding | 10px 14px |
| Font | 13px, line-height 1.5 |

### Input Row

| Element | Property | Value |
|---------|----------|-------|
| Input | Height | 38px |
| Input | Border-radius | 10px |
| Input | Font | 13px |
| Button | Height | 38px |
| Button | Background | `--shunya-text` |
| Button | Colour | White |
| Gap (input–button) | 8px |

### Usage Rules

- Human messages are right-aligned (dark bg, white text)
- Assistant messages are left-aligned (light bg, border, secondary text)
- Timestamps are 10px, 40% opacity
- No avatars in v1.0

---

## 14. Notification / Flash Message

### Purpose
Inform the user of system events, errors, and confirmations.

### Types

| Type | Position | Duration | Colour |
|------|----------|----------|--------|
| Flash message | Top of page, below nav | 5s auto-dismiss | Success/Error/Warning |
| Status dot | Bottom-right | Persistent | Green/Yellow/Off |
| Strip attention | Top-right identity strip | Persistent | Green/Yellow/Red |

### Flash Message

| Property | Value |
|----------|-------|
| Padding | 12px 16px |
| Border-radius | 10px |
| Font | 14px, weight 500 |
| Margin-bottom | 6px |
| Animation (enter) | Fade in, 300ms |
| Animation (exit) | Fade + slide right, 300ms |

### Flash Message Colours

| Type | Background | Text | Border |
|------|------------|------|--------|
| Success | `#dcfce7` | `#166534` | `#bbf7d0` |
| Error | `#fee2e2` | `#991b1b` | `#fecaca` |
| Warning | `#fef3c7` | `#92400e` | `#fde68a` |

### Usage Rules

- Flash messages stack vertically (newest on top)
- Close button (×) on hover
- Auto-dismiss after 5 seconds
- No sound or vibration on notification

---

## 15. Empty State

### Purpose
Guide the user when no content exists in a section.

### Anatomy

```
┌──────────────────────────────────┐
│                                  │
│         [Icon 40px, 0.3 opacity] │
│                                  │
│      Heading (18px, 300w)       │
│                                  │
│   Description (13px, tertiary)   │
│   max-width: 320px               │
│                                  │
└──────────────────────────────────┘
```

### Dimensions

| Property | Value |
|----------|-------|
| Container padding | 40px |
| Icon | 40px, `opacity: 0.3` |
| Heading | Inter, 18px, weight 300, `--shunya-text-secondary` |
| Description | Inter, 13px, `--shunya-text-tertiary`, line-height 1.5 |
| Description max-width | 320px |
| Gap (icon–heading) | 16px |
| Gap (heading–desc) | 8px |

### Usage Rules

- Empty states are centered in their container
- No illustrations in empty states (deferred to v2.0)
- Empty states should explain why the section is empty and what to do

---

## 16. Link Chip

### Purpose
Display linked objects or relationships between entities.

### Anatomy

```
┌──────────────┐
│  Type  Name  │
└──────────────┘
```

### Dimensions

| Property | Value |
|----------|-------|
| Padding | 6px 14px |
| Border-radius | 20px |
| Background | `--shunya-surface` |
| Border | 1px solid `--shunya-border` |
| Font | 12px, `--shunya-text-secondary` |
| Type label | 10px, `--shunya-text-tertiary` |
| Gap (type–name) | 5px |

### States

| State | Border | Text |
|-------|--------|------|
| Default | `--shunya-border` | `--shunya-text-secondary` |
| Hover | `--shunya-border-hover` | `--shunya-text` |
| Focus-visible | Gold outline | — |

### Usage Rules

- Chips are displayed in a flex-wrap grid
- Type label is optional (shown in parentheses or as a prefix)
- Clickable chips navigate to the linked object

---

## 17. Health Indicator (Status Dot)

### Purpose
Communicate the health status of an object or system.

### Anatomy

```
  ●  Healthy
  ●  Warning
  ●  Critical
```

### Dimensions

| Context | Size | Usage |
|---------|------|-------|
| Status dot (bottom-right) | 6px | System health |
| Strip attention dot | 6px | Identity strip |
| Object health dot | 6px | Object header |
| Timeline dot | 8px | Timeline items |

### Colours

| Status | Colour | Usage |
|--------|--------|-------|
| Good / Healthy | `#51cf66` | Everything is fine |
| Warning / Caution | `#fab005` | Needs attention |
| At Risk | `#fd7e14` | Escalating |
| Critical / Error | `#ff6b6b` | Requires immediate action |
| Silent / Offline | `--shunya-text-faint` | Inactive |

### Animation

| State | Animation |
|-------|-----------|
| Thinking | Pulse (1.5s, opacity 1→0.4→1) |
| Static | No animation |

### Usage Rules

- Dot is always a `<span>` with border-radius 50%
- Dot is always accompanied by text label (except system status dot)
- Maximum 4 status levels

---

## 18. Skeleton Loader

### Purpose
Indicate content loading without using spinners.

### Anatomy

```
┌──────────────────────────────────┐
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│  ━━━━━━━━━━━━                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│  ━━━━━━━━━━━━                    │
└──────────────────────────────────┘
```

### Dimensions

| Property | Value |
|----------|-------|
| Line height | 12px |
| Line margin-bottom | 8px |
| Border-radius | 10px (or `--shunya-radius-sm`) |
| Colour | `--shunya-border` (7% opacity) |
| Short line width | 60% |
| Medium line width | 80% |

### Animation

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--shunya-border) 25%,
    rgba(26,26,26,0.02) 50%,
    var(--shunya-border) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### Usage Rules

- Skeleton shapes match the layout of the final content
- No spinners, no loading bars, no circular progress
- Shimmer animation is the only loading indicator
- Suspended on reduced-motion

---

## 19. Badge

### Purpose
Display counts, status, or metadata in a compact format.

### Anatomy

```
┌──────────┐
│  23      │
└──────────┘
```

### Dimensions

| Property | Value |
|----------|-------|
| Padding | 2px 10px (or 1px 6px for nav) |
| Border-radius | 9999px (full) |
| Font | 10px, weight 500–600, monospace (nav) |
| Font | 12px, weight 600 (standalone) |

### Colours

| Variant | Background | Text |
|---------|------------|------|
| Default | `--shunya-border` | `--shunya-text-tertiary` |
| Success | `#dcfce7` | `#166534` |
| Warning | `#fef3c7` | `#92400e` |
| Error | `#fee2e2` | `#991b1b` |
| Info | `#dbeafe` | `#1d4ed8` |

### Usage Rules

- Badges are always `display: inline-block`
- Badges in navigation use `--shunya-border` background
- Semantic badges use the same colour system as flash messages
- No icons within badges

---

## 20. Section Label

### Purpose
Label sections of content with a consistent, minimal heading.

### Anatomy

```
REAL-TIME
```

### Dimensions

| Property | Value |
|----------|-------|
| Font | Inter, 11px, weight 600 |
| Text transform | Uppercase |
| Letter-spacing | 0.12em |
| Colour | `--shunya-gold` (#a4865f) |
| Margin-bottom | 16px |
| Text-align | Center (landing page sections) |

### Usage Rules

- Section labels are gold
- Used for section headings on landing page and workspace panels
- Not used for form labels (use 12px, `--shunya-text-secondary`)
- Always uppercase

---

*End of Component Specification v1.0*