# SHUNYA Design System

> **Canonical Frontend Document · Phase C3 Parallel**
> **Status: CANONICAL — Implementation-Independent Design Specification**
> **Version: 1.0**
> **Derived From: 08_experience_canon.md (Experience Canon)**
> **Palette: Warm Minimalism · Gold Accent**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Design Philosophy](#2-design-philosophy)
3. [Design Tokens](#3-design-tokens)
4. [Component Categories](#4-component-categories)
5. [Motion Principles](#5-motion-principles)
6. [Accessibility Guidelines](#6-accessibility-guidelines)
7. [Responsive Behaviour](#7-responsive-behaviour)
8. [Theme System Architecture](#8-theme-system-architecture)
9. [Relationship to Other Documents](#9-relationship-to-other-documents)

---

## 1. Purpose

This document defines the complete design system for SHUNYA — the visual language, component taxonomy, motion principles, accessibility baseline, and responsive behavior that every frontend implementation must follow.

**This is the specification that bridges the Experience Canon (08) to concrete frontend code.** All design tokens, component specifications, and interaction patterns defined here are binding on all frontend implementations.

---

## 2. Design Philosophy

### 2.1 Core Statement

**SHUNYA reduces cognitive load. Every pixel, every word, every interaction exists to make the human's mental task easier.**

The design system exists to serve the Experience Canon's 70/20/10 rule:
- **70% whitespace** — visual breathing room, focus on the object
- **20% content** — what the human needs to know about the object
- **10% controls** — what the human can do to/with the object

### 2.2 Design Values

| Value | Description | Manifests As |
|-------|-------------|-------------|
| **Calm** | The system is quiet until spoken to | Spacious layouts, no noise, minimal chrome |
| **Clear** | Every element communicates its purpose | Self-describing objects, unambiguous actions |
| **Kind** | The system is patient and forgiving | Generous hit targets, undo everywhere, errors without blame |
| **Capable** | The system does more than expected | Progressive disclosure, power features on objects |
| **Consistent** | Patterns are reliable across surfaces | Every object type follows the same layout contract |
| **Personal** | Feels like it was made for you | Workspace adapts, remembers context |

### 2.3 Warm Minimalism

SHUNYA's visual identity is **warm minimalism** — the starkness of minimal design softened by warm tones, serif headings, and generous whitespace. The palette is inspired by paper, ink, and natural materials.

---

## 3. Design Tokens

### 3.1 Color Palette

#### 3.1.1 Core Colors

| Token | Role | Value | Usage |
|-------|------|-------|-------|
| `--color-surface` | Primary background | `#fbfaf8` | Main surface, workspace background |
| `--color-surface-alt` | Secondary background | `#f7f5f1` | Sidebars, panels, hover states |
| `--color-surface-elevated` | Elevated surface | `#ffffff` | Modals, overlays, tooltips |
| `--color-text-primary` | Primary text | `#1a1c1d` | Headings, object names, body text |
| `--color-text-secondary` | Secondary text | `rgba(26,28,29,0.55)` | Labels, metadata, captions |
| `--color-text-tertiary` | Tertiary text | `rgba(26,28,29,0.35)` | Placeholder, disabled |
| `--color-text-inverse` | Text on dark bg | `#fbfaf8` | Inverted surfaces |
| `--color-accent` | Brand accent | `#a4865f` | Active states, highlights, branded elements |
| `--color-accent-hover` | Accent hover | `#8e7450` | Accent interaction states |
| `--color-accent-subtle` | Accent subtle | `rgba(164,134,95,0.1)` | Accent backgrounds, active indicators |
| `--color-border` | Default border | `rgba(0,0,0,0.06)` | Element borders, dividers |
| `--color-border-hover` | Border hover | `rgba(0,0,0,0.12)` | Interactive border states |
| `--color-border-accent` | Accent border | `rgba(164,134,95,0.3)` | Focused/selected element borders |
| `--color-error` | Error | `#d1453b` | Error states, destructive actions |
| `--color-error-subtle` | Error subtle | `rgba(209,69,59,0.08)` | Error backgrounds |
| `--color-success` | Success | `#2e7d32` | Success states, completed |
| `--color-success-subtle` | Success subtle | `rgba(46,125,50,0.08)` | Success backgrounds |
| `--color-warning` | Warning | `#c97b2d` | Warning states |
| `--color-warning-subtle` | Warning subtle | `rgba(201,123,45,0.08)` | Warning backgrounds |
| `--color-info` | Information | `#1a73e8` | Link text, information states |
| `--color-info-subtle` | Info subtle | `rgba(26,115,232,0.08)` | Info backgrounds |

#### 3.1.2 Semantic Color Map

| Semantic State | Background | Border | Text | Icon |
|---------------|-----------|--------|------|------|
| Default | `--color-surface` | `--color-border` | `--color-text-primary` | `--color-text-secondary` |
| Hover | `--color-surface-alt` | `--color-border-hover` | `--color-text-primary` | `--color-text-primary` |
| Active / Focused | `--color-surface` | `--color-border-accent` | `--color-text-primary` | `--color-accent` |
| Selected | `--color-accent-subtle` | `--color-accent` | `--color-text-primary` | `--color-accent` |
| Disabled | `--color-surface` | `--color-border` | `--color-text-tertiary` | `--color-text-tertiary` |
| Error | `--color-error-subtle` | `--color-error` | `--color-error` | `--color-error` |
| Success | `--color-success-subtle` | `--color-success` | `--color-success` | `--color-success` |
| Read-only | `--color-surface-alt` | `--color-border` | `--color-text-secondary` | `--color-text-tertiary` |

#### 3.1.3 Object Type Colors

Each of the 18 object types has a subtle identification color used for icons and accents:

| Object Type | Color | Hex |
|-------------|-------|-----|
| Identity | Slate | `#5f6b7a` |
| Human | Amber | `#c97b2d` |
| Organization | Teal | `#2d7a6e` |
| Workspace | Indigo | `#4a5f8e` |
| Relationship | Rose | `#b35f7a` |
| Conversation | Blue | `#1a73e8` |
| Commitment | Green | `#2e7d32` |
| Task | Orange | `#c97b2d` |
| Event | Purple | `#7a5f8e` |
| Observation | Cyan | `#2d8e8e` |
| Evidence | Red | `#d1453b` |
| Document | Brown | `#8e7a5f` |
| FinancialObject | Emerald | `#1b8e5f` |
| Decision | Gold (accent) | `#a4865f` |
| Workflow | Blue-grey | `#5f7a8e` |
| Memory | Mauve | `#8e6b8e` |
| Knowledge | Jade | `#2d8e5f` |
| Outcome | Teal-green | `#2d7a5f` |

### 3.2 Typography

#### 3.2.1 Font Family

| Role | Font | Fallback | Usage |
|------|------|----------|-------|
| **Heading** | `'Playfair Display'` | `Georgia, serif` | h1–h4, object names, section titles |
| **Body** | `'Inter'` | `-apple-system, sans-serif` | Body text, labels, everything else |
| **Mono** | `'JetBrains Mono'` | `'SF Mono', monospace` | Code, data values, object IDs, timestamps |

#### 3.2.2 Type Scale

| Token | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| `--text-xs` | 10px | 1.4 | 400 | Metadata, timestamps, object IDs |
| `--text-sm` | 12px | 1.4 | 400 | Labels, secondary info, captions |
| `--text-base` | 14px | 1.5 | 400 | Body text, object content |
| `--text-md` | 16px | 1.5 | 400 | Large body, object descriptions |
| `--text-lg` | 20px | 1.3 | 500 | Object detail subheadings |
| `--text-xl` | 28px | 1.2 | 600 | Object names, section headings |
| `--text-2xl` | 36px | 1.1 | 600 | Primary headings, object detail title |
| `--text-3xl` | 48px | 1.1 | 700 | Hero headings, workspace titles |

#### 3.2.3 Font Weights

| Weight | Value | Usage |
|--------|-------|-------|
| Regular | 400 | Body text, metadata |
| Medium | 500 | Emphasized text, subheadings |
| Semibold | 600 | Headings, object names |
| Bold | 700 | Primary headings, strong emphasis |

#### 3.2.4 Heading Hierarchy

```
h1 — Playfair Display, 36px, Semibold    (--text-2xl, serif)
  Object name, workspace title

h2 — Inter, 20px, Medium                 (--text-lg, sans-serif)
  Section headings within object detail

h3 — Inter, 16px, Medium                 (--text-md, sans-serif)
  Sub-section headings, panel titles

h4 — Inter, 14px, Semibold               (--text-base, semibold)
  Group labels, field names
```

### 3.3 Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | 4px | Tight spacing, object badges |
| `--space-sm` | 8px | Component internal spacing, icon gaps |
| `--space-md` | 16px | Between components, card padding |
| `--space-lg` | 32px | Section spacing, panel padding |
| `--space-xl` | 64px | Page margins, workspace boundaries |
| `--space-2xl` | 96px | Hero spacing, large section separators |

#### 3.3.1 Spacing Rules

- **Horizontal rhythm**: content columns use 16px padding. Sidebars use 24px padding.
- **Vertical rhythm**: object detail sections are separated by 32px. Related groups within sections by 16px.
- **Hit targets**: minimum 44×44px for all interactive elements (WCAG 2.5.5).
- **Whitespace priority**: the 70% whitespace rule means spacing between elements is generous. When in doubt, add spacing.

### 3.4 Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 4px | Input fields, small badges |
| `--radius-md` | 8px | Cards, panels, buttons |
| `--radius-lg` | 12px | Modals, overlays, AI panel |
| `--radius-full` | 9999px | Avatars, pills, status indicators |

### 3.5 Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.04)` | Subtle card elevation |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,0.06)` | Panel elevation, dropdowns |
| `--shadow-lg` | `0 8px 24px rgba(0,0,0,0.08)` | Modals, AI panel |
| `--shadow-xl` | `0 16px 48px rgba(0,0,0,0.12)` | Large overlays, focused state |

### 3.6 Z-Index Scale

| Layer | Value | Elements |
|-------|-------|----------|
| Base | 0 | Surface, top bar, object browser, focal area |
| Sticky | 10 | Sticky headers within panels |
| Overlay backdrop | 90 | Dimmed backdrop behind overlays |
| Overlay | 100 | Search, notifications, workspace switcher |
| AI Panel | 200 | AI collaborator slide-over panel |
| Tooltip | 500 | Tooltips, popovers |
| Notification toast | 1000 | Toast notifications on top of everything |

### 3.7 Iconography

- **Icon set**: Feather icons (or equivalent stroke-based set) — consistent 1.5px stroke weight.
- **Sizes**: 16px (inline), 20px (buttons), 24px (object type icons), 32px (empty states).
- **Color**: Inherits text color by default; accent color for active/highlighted states.
- **Object type icons**: 24px, colored by the object type color map (§3.1.3).

---

## 4. Component Categories

### 4.1 Component Taxonomy

All SHUNYA components fall into exactly 7 categories:

| Category | Role | Examples |
|----------|------|----------|
| **Surface** | Structural layout containers | Workspace, TopBar, Sidebar, Panel, Overlay |
| **Object** | Object-rendering components | ObjectCard, ObjectDetail, ObjectField, ObjectList |
| **Action** | User interaction components | Button, Input, Select, SearchBar, ObjectAction |
| **Navigation** | Wayfinding components | Breadcrumb, TabBar, ObjectBrowser, RelationshipLink |
| **Feedback** | System response components | Toast, EmptyState, Loading, ProgressIndicator |
| **AI** | AI collaboration components | AIPanel, AISuggestion, AIButton, AIConfidence |
| **Overlay** | Temporary surface components | Modal, BottomSheet, Dropdown, Tooltip |

### 4.2 Surface Components

These components form the structural layout. They have no business logic — only spatial responsibility.

| Component | Role | Children | Behavior |
|-----------|------|----------|----------|
| `Workspace` | Root container | TopBar, ObjectBrowser, FocalArea, RelationshipPanel | State machine host |
| `TopBar` | Persistent header | WorkspaceSelector, ObjectTypeLabel, SearchTrigger, AIButton, NotifIcon, ProfileIcon | Always visible |
| `ObjectBrowser` | Object list sidebar | ObjectCard[] | Collapsible, scrollable |
| `FocalArea` | Primary content area | ObjectDetail | Scrollable, single object focus |
| `RelationshipPanel` | Relationship sidebar | RelationshipLink[] | Collapsible |
| `AIPanel` | AI collaborator | AIConversation, AISuggestion[] | Slide-over from right |
| `Overlay` | Modal backdrop | Content | Dims background, traps focus |

### 4.3 Object Components

These components render objects and their properties. They are the most numerous and most important category.

| Component | Role | Props |
|-----------|------|-------|
| `ObjectCard` | Compact object display | object, selected, onClick |
| `ObjectDetail` | Full object view | object, disclosureLevel |
| `ObjectField` | Single field display | label, value, type |
| `ObjectStatus` | Status indicator | status, statusDetail |
| `ObjectTimeline` | Object event timeline | events[] |
| `ObjectRelationshipList` | Related objects | relationships[] |
| `ObjectActionBar` | Action buttons | actions[], onAction |
| `ObjectBreadcrumb` | Navigation context | path: Workspace → Type → Name |
| `ObjectSearchResult` | Search hit | object, matchContext, onClick |

### 4.4 Action Components

| Component | Role | States |
|-----------|------|--------|
| `Button` | Single action | default, hover, active, disabled, loading |
| `ButtonGroup` | Related actions | horizontal, vertical |
| `IconButton` | Icon-only action | same as Button, 44×44px minimum |
| `TextInput` | Single-line text | default, focus, error, disabled, read-only |
| `TextArea` | Multi-line text | same as TextInput |
| `Select` | Option picker | default, focus, error, disabled |
| `SearchBar` | Object search | default, focus, empty, hasResults, noResults |
| `ObjectAction` | Contextual object action | icon, label, onClick, confirmation? |

### 4.5 Navigation Components

| Component | Role | Behavior |
|-----------|------|----------|
| `Breadcrumb` | Position context | Always shows 3-level path |
| `ObjectBrowser` | Object list | Sortable, filterable, scrollable |
| `RelationshipLink` | Follow relationship | Displays relationship type + target name |
| `WorkspaceSelector` | Switch workspace | Dropdown, shows recent workspaces first |
| `ObjectTypeFilter` | Filter by type | Checkbox group, shows counts |
| `TabBar` | Switch sections | Within ObjectDetail (Info, Timeline, Relationships) |

### 4.6 Feedback Components

| Component | Role | Behavior |
|-----------|------|----------|
| `Toast` | Temporary notification | Auto-dismiss, stackable, types (success/error/info) |
| `EmptyState` | No content guidance | Icon + message + suggested action |
| `Loading` | Content loading | Skeleton shimmer, respects reduced motion |
| `ProgressIndicator` | Long operation | Determinate (percentage) or indeterminate |
| `Confirmation` | Destructive action | "Are you sure?" dialog, cancel + confirm |

### 4.7 AI Components

| Component | Role | Behavior |
|-----------|------|----------|
| `AIButton` | Summon AI | Cmd+Shift+K trigger, subtle pulse animation |
| `AIPanel` | AI conversation container | Slide-over, object-contextual header |
| `AIMessage` | AI response | Confidence indicator, evidence link, action proposals |
| `AISuggestion` | Inline suggestion | Subtle background, dismiss/accept buttons |
| `AIConfidence` | Confidence display | Bar/dot indicator, natural language label |
| `AIInput` | Human-to-AI input | Multi-line, submit via Enter/Cmd+Enter |

### 4.8 Overlay Components

| Component | Role | Behavior |
|-----------|------|----------|
| `Modal` | Blocking dialog | Centered, dimmed backdrop, Escape to close |
| `BottomSheet` | Mobile action sheet | Slides up from bottom, drag to dismiss |
| `Dropdown` | Menu selector | Click to open, click outside to close |
| `Tooltip` | Contextual info | Hover to show, 300ms delay, accessible |
| `Popover` | Rich tooltip | Click to open, contains interactive content |

---

## 5. Motion Principles

### 5.1 Motion Philosophy

Motion in SHUNYA is **functional, not decorative**. Every animation serves a purpose:
- **Spatial orientation** — the user understands where something came from and where it went
- **State clarity** — the user understands that something changed
- **Reduced cognitive load** — motion guides attention without demanding it

### 5.2 Motion Tokens

| Token | Duration | Easing | Usage |
|-------|----------|--------|-------|
| `--motion-instant` | 0ms | — | State changes, toggles |
| `--motion-fast` | 100ms | ease-out | Micro-interactions, hover effects |
| `--motion-base` | 200ms | ease-out | Standard transitions, panel slides |
| `--motion-slow` | 300ms | ease-in-out | Overlay transitions, page shifts |
| `--motion-expressive` | 400ms+ | ease-out | Object focus transitions, spatial shifts |

### 5.3 Motion Patterns

| Pattern | Duration | Easing | Description |
|---------|----------|--------|-------------|
| **Focus shift** | 200ms | ease-out | Object shifts to center of focal area, subtle scale (1→1) |
| **Panel slide** | 250ms | ease-out | Panels (relationship, AI) slide in from edge |
| **Overlay fade** | 200ms | ease-out | Overlays fade in with backdrop dim |
| **Object card hover** | 100ms | ease-out | Slight lift (+1px translateY, shadow-sm→shadow-md) |
| **State change** | 150ms | ease-out | Status badges, checkmarks, toggles |
| **Loading shimmer** | 1.5s loop | linear | Skeleton loaders, indefinite |
| **Empty state fade** | 300ms | ease-out | Empty state elements fade in |
| **Accordion expand** | 200ms | ease-out | Progressive disclosure sections |

### 5.4 Motion Rules

1. **No motion without purpose.** Every animation must serve orientation, clarity, or cognitive load reduction.
2. **Respect `prefers-reduced-motion`.** All motion degrades gracefully to instant (0ms) transitions.
3. **Duration increases with distance.** A panel sliding from right is slower (250ms) than a hover effect (100ms).
4. **No overlapping motion.** Animations sequence, never overlap. The first completes before the second begins.
5. **No motion on input delay.** Motion should not delay user interaction. Inputs are immediately responsive.
6. **Spatial continuity.** Objects in motion maintain spatial continuity — the user can track where they go.

### 5.5 Motion Accessibility

| Condition | Behavior |
|-----------|----------|
| `prefers-reduced-motion: reduce` | All durations set to 0ms, animations disabled |
| `prefers-reduced-motion: no-preference` | Full motion as specified above |
| Forced colors mode | Motion preserved (not color-dependent) |

---

## 6. Accessibility Guidelines

### 6.1 Standard Compliance

SHUNYA targets **WCAG 2.1 Level AA** as minimum, with **Level AAA for core object workflows**.

### 6.2 Color & Contrast

| Requirement | Standard | Verification |
|-------------|----------|-------------|
| Normal text contrast | 4.5:1 minimum | All text tokens verified |
| Large text contrast | 3:1 minimum | Headings ≥ 18px bold or ≥ 24px regular |
| UI component contrast | 3:1 minimum | Borders, icon states |
| Focus indicator | 3:1 minimum | 2px outline, visible on all backgrounds |
| Non-text contrast | 3:1 minimum | Icons, charts, status indicators |

### 6.3 Keyboard Accessibility

| Requirement | Implementation |
|-------------|---------------|
| Full keyboard navigation | Tab through all interactive elements in logical order |
| Visible focus indicator | 2px outline on accent color, never removed |
| Focus trap in overlays | Focus cycles within open overlays; Escape returns to surface |
| Skip to content | Skip navigation link at page load |
| Object keyboard shortcuts | All object actions accessible via keyboard (Cmd+K, shortcuts) |
| No keyboard traps | All interactive elements are reachable and dismissable |

### 6.4 Screen Reader Support

| Requirement | Implementation |
|-------------|---------------|
| ARIA landmarks | `role="navigation"` on TopBar, `role="main"` on FocalArea, `role="complementary"` on panels |
| Object roles | Each object card has `role="article"` with `aria-label="{type}: {name}"` |
| State announcements | Object state changes use `aria-live="polite"` |
| Relationship announcements | Relationship links include `aria-label="{type} to {target}"` |
| Action announcements | Buttons include `aria-label` when icon-only |
| Search results | Result list has `role="listbox"` with `aria-activedescendant` |
| Breadcrumb | `aria-label="Breadcrumb"`, items separated by `aria-hidden` separators |
| AI responses | AI messages have `role="status"` with `aria-live="polite"` |
| Loading states | Skeleton loaders have `aria-busy="true"` |

### 6.5 Touch & Target Sizes

| Requirement | Standard |
|-------------|----------|
| Minimum target | 44×44px (WCAG 2.5.5) |
| Target spacing | 8px minimum between adjacent targets |
| Touch feedback | Visual feedback within 100ms of touch |
| Touch target expansion | Smallest targets (icons) expand hit area via padding |

### 6.6 Text & Zoom

| Requirement | Implementation |
|-------------|---------------|
| Text resize | All text readable at 200% zoom with no loss of functionality |
| Reflow | No horizontal scroll at 400% zoom (single column layout) |
| Line height | Minimum 1.5 for body text |
| Paragraph spacing | 1.5× line height between paragraphs |
| Text spacing | No loss of content when user overrides text spacing |

### 6.7 Motion Sensitivity

| Requirement | Implementation |
|-------------|---------------|
| `prefers-reduced-motion` | All motion disabled, instant transitions |
| Flashing content | No content flashes more than 3 times per second |
| Animation trigger | Animations are never auto-playing on page load |

---

## 7. Responsive Behaviour

### 7.1 Breakpoints

| Breakpoint | Width | Layout Strategy |
|-----------|-------|-----------------|
| Mobile | < 600px | Single column, bottom navigation |
| Tablet | 600–899px | Single column, top navigation |
| Small Desktop | 900–1199px | Multi-column with collapsible panels |
| Desktop | 1200–1399px | Full layout |
| Desktop XL | ≥ 1400px | Full layout with extended workspace |

### 7.2 Responsive Design Token Overrides

At the mobile breakpoint, all spacing tokens are reduced by one level:

| Desktop Token | Mobile Equivalent |
|--------------|-------------------|
| `--space-xl` (64px) | `--space-lg` (32px) |
| `--space-lg` (32px) | `--space-md` (16px) |
| `--space-md` (16px) | `--space-sm` (8px) |

### 7.3 Responsive Component Behaviour

| Component | Desktop | Tablet | Mobile |
|-----------|---------|--------|--------|
| ObjectBrowser | Persistent sidebar, 300px | Collapsible overlay | Bottom sheet |
| RelationshipPanel | Persistent sidebar, 280px | Collapsible overlay | Bottom sheet |
| AIPanel | Slide-over, 400px | Slide-over, full width | Full screen |
| TopBar | Full labels + icons | Icons only | Icons + hamburger |
| ObjectDetail | Full width | Full width | Single column |
| Data tables | Horizontal scroll | Object card list | Object card list |
| Breadcrumb | Full text | Type + name | Name only |

---

## 8. Theme System Architecture

### 8.1 Token Implementation

All design tokens are implemented as **CSS custom properties** on `:root`:

```css
:root {
  /* Colors */
  --color-surface: #fbfaf8;
  --color-accent: #a4865f;
  /* ... */

  /* Typography */
  --font-heading: 'Playfair Display', Georgia, serif;
  --font-body: 'Inter', -apple-system, sans-serif;
  /* ... */

  /* Spacing */
  --space-md: 16px;
  /* ... */

  /* Motion */
  --motion-base: 200ms;
  /* ... */
}
```

### 8.2 Theme Override Structure

```css
/* Domain theme: travel */
[data-domain="travel"] {
  --color-accent: #b8860b;
  --color-surface: #faf9f6;
}

/* Workspace theme override */
[data-workspace-theme="dark"] {
  --color-surface: #1a1c1d;
  --color-text-primary: #fbfaf8;
}
```

### 8.3 Theme Layers

| Layer | Scope | Override Mechanism |
|-------|-------|-------------------|
| **Base** | Global | `:root` CSS custom properties |
| **Domain** | Per domain | `[data-domain="name"]` |
| **Workspace** | Per workspace | `[data-workspace-id="id"]` |
| **User** | Per user preference | `[data-user-preference]` |
| **Organization** | Organization branding | `[data-org-brand]` |

---

## 9. Relationship to Other Documents

| Document | Relationship |
|----------|-------------|
| **08_experience_canon.md** | This document implements the visual and component specification of the Experience Canon |
| **INFORMATION_ARCHITECTURE.md** | Components in this document implement the IA structures defined there |
| **COMPONENT_SPECIFICATION.md** | Each component in the taxonomy is fully specified in the Component Spec |
| **DESKTOP_INTERACTION_MODEL.md** | Desktop interactions use the motion and feedback patterns defined here |
| **MOBILE_INTERACTION_MODEL.md** | Mobile interactions use the responsive and touch tokens defined here |
| **09_repository_canon.md** | Frontend code organization follows the component category structure |

---

> **End of Design System**
> **[Return to INDEX](#)**