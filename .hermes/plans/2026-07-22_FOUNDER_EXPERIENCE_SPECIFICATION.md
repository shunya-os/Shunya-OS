# SHUNYA OS — Founder Experience Specification

> **Document Type:** Constitutional Specification
> **Status:** DRAFT — Awaiting Founder Review
> **Phase:** Experience Design (Sprint 2)
> **Precedes:** Implementation

---

## Table of Contents

1. [Foundational Philosophy](#1-foundational-philosophy)
2. [The One Living Workspace](#2-the-one-living-workspace)
3. [Morning Zero Specification](#3-morning-zero-specification)
4. [Object-Focus Interaction Model](#4-object-focus-interaction-model)
5. [Search-as-Thought Specification](#5-search-as-thought-specification)
6. [AI Contextual Behaviour Specification](#6-ai-contextual-behaviour-specification)
7. [Workspace State Transitions](#7-workspace-state-transitions)
8. [Navigation Elimination Strategy](#8-navigation-elimination-strategy)
9. [Desktop Interaction Model](#9-desktop-interaction-model)
10. [Mobile Interaction Model](#10-mobile-interaction-model)
11. [UX Flow Diagrams](#11-ux-flow-diagrams)
12. [Implementation Roadmap](#12-implementation-roadmap)

---

## 1. Foundational Philosophy

### 1.1 The Principle of Continuity

SHUNYA is not an application. An application has pages, menus, and navigation. SHUNYA is a **living workspace** — a continuous environment that evolves around what the founder is doing.

The experience must feel like walking into a room where everything is exactly where the founder left it, and the room itself has been tidied and prepared overnight.

### 1.2 The Design Question

Every design decision answers:

> **"What should the founder naturally see next?"**

Never:

> "What page comes next?"

### 1.3 The 70/20/10 Rule

Every visual state must satisfy:

| Proportion | Content | Purpose |
|-----------|---------|---------|
| **70%** | Calm whitespace | Breathing room, focus, clarity |
| **20%** | Contextual information | What the founder needs to know |
| **10%** | Interaction controls | What the founder can do |

### 1.4 Antipatterns

**Do not build:**
- CRUD forms (create/edit/delete pages)
- Dashboards with metric grids
- Menu trees and sidebar navigation
- Wizard flows
- Tab bars
- Modal dialogs for primary actions
- Traditional admin interfaces

**Do build:**
- Continuous surfaces that transform
- Context that anticipates attention
- Controls that appear when needed, fade when not
- Transitions that feel like focus shifts, not page loads

---

## 2. The One Living Workspace

### 2.1 Architecture

The workspace is a single continuous surface. All elements exist simultaneously:

```
┌─────────────────────────────────────────────────────┐
│                     THE WORKSPACE                     │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │                                                   │ │
│  │   Identity (always present, always calm)          │ │
│  │                                                   │ │
│  │   ↓                                               │ │
│  │                                                   │ │
│  │   Space (the container, always visible as context) │ │
│  │                                                   │ │
│  │   ↓                                               │ │
│  │                                                   │ │
│  │   Object (the current focus, at center)           │ │
│  │                                                   │ │
│  │   ┌─────────┐  ┌──────────┐  ┌─────────────┐    │ │
│  │   │Relations│  │Conversat.│  │ Commitments │    │ │
│  │   └─────────┘  └──────────┘  └─────────────┘    │ │
│  │                                                   │ │
│  │   Evidence  ·  History  ·  Knowledge  ·  AI       │ │
│  │                                                   │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│   Search (always accessible, always listening)        │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### 2.2 Focus Levels

The workspace has three focus levels:

| Level | State | Description |
|-------|-------|-------------|
| **Ambient** | Default | Morning Zero, low interaction, scanning |
| **Focused** | Active work | Object-centered, tools visible |
| **Deep** | Immersive | Full-screen object, minimal chrome |

Transitions between levels are animated, smooth, and feel like adjusting focus — not navigating.

### 2.3 The Chrome

The workspace chrome is minimal:

- **Top strip:** Identity indicator (name, avatar). Calm, small, 32px.
- **Bottom strip:** Search input. Always present, always accepting text.
- **Everything else:** Content.

No sidebar. No navbar. No breadcrumbs. No tabs.

---

## 3. Morning Zero Specification

### 3.1 Purpose

The first screen the founder sees every morning. It is not a dashboard. It answers one question:

> **"What happened while I was away?"**

### 3.2 Visual Structure

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   Good morning, Alice.                              │
│                                                     │
│   3 things need your attention:                     │
│                                                     │
│   ┌────────────────────────────────────────────────┐│
│   │  ● Rahul's proposal is waiting for approval    ││
│   │    → 2 days remaining                          ││
│   └────────────────────────────────────────────────┘│
│                                                     │
│   ┌────────────────────────────────────────────────┐│
│   │  ○ Q3 Strategy — 3 new messages                ││
│   │    → "Can we review the budget allocation?"    ││
│   └────────────────────────────────────────────────┘│
│                                                     │
│   ┌────────────────────────────────────────────────┐│
│   │  ○ Acme Corp — onboarding complete             ││
│   │    → 2 new team members ready                  ││
│   └────────────────────────────────────────────────┘│
│                                                     │
│   2 opportunities observed:                         │
│                                                     │
│   ┌────────────────────────────────────────────────┐│
│   │  ○ Renewal conversation showed intent          ││
│   │  → Consider reaching out today                 ││
│   └────────────────────────────────────────────────┘│
│                                                     │
│   Everything else is quiet.                         │
│                                                     │
│   [Search or type to begin...]                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 3.3 Data Sources

Morning Zero aggregates from:

| Source | What it surfaces | Priority |
|--------|-----------------|----------|
| Commitments | Approvals, deadlines, promises | High |
| Conversations | Unread messages, @mentions, unanswered questions | High |
| AI Observations | Detected patterns, anomalies, opportunities | Medium |
| Relationships | New members, status changes, role changes | Medium |
| Objects | Expiring items, stalled workflows, completed items | Medium |
| Calendar | Meetings, events, time-sensitive items | Medium |

### 3.4 Behaviour Rules

1. **Never empty.** If nothing happened, show: "Everything is quiet. You have [X] active objects across [Y] spaces."
2. **Never overwhelming.** Maximum 7 items. Group by priority.
3. **Always actionable.** Each item is clickable. Clicking moves founder into focused state on that object.
4. **Always respectful.** No notifications, badges, or red dots. Calm language only.
5. **Always learnable.** Items that founder ignores repeatedly fade in priority.

### 3.5 State Transitions

```
Morning Zero ──click item──→ Focused (object-centered)
Morning Zero ──type search──→ Search results overlay
Morning Zero ──type command──→ AI interaction
Morning Zero ──idle 30s──→ Ambient (fade to calm)
```

---

## 4. Object-Focus Interaction Model

### 4.1 Principle

When the founder focuses on something, SHUNYA brings that object to the center of the workspace. Around it, relevant context appears. Everything else fades.

### 4.2 The Object Shell

Every object in focus is rendered in a consistent shell:

```
┌─────────────────────────────────────────────────────┐
│  ← Space Name              [Type]  [Status]  [⋯]    │
│─────────────────────────────────────────────────────│
│                                                       │
│                    OBJECT NAME                        │
│                    (large, calm)                      │
│                                                       │
│  ┌─────────────── DESCRIPTION ─────────────────────┐ │
│  │  Content area. Calm, readable, spacious.         │ │
│  │  If the object has content, it appears here.     │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  ──── Relationships ─────────────────────────────── │
│  │ ○ Rahul (Contact)    ○ Acme Corp (Organization) │ │
│  │ ○ Q3 Budget (Object) ○ Alice (Creator)          │ │
│  ──── Conversations ─────────────────────────────── │
│  │ ○ "Can we review the budget?" — 2h ago           │ │
│  │ ○ "Timeline looks good" — yesterday              │ │
│  ──── AI Understanding ──────────────────────────── │
│  │   This object is a strategy proposal. It has     │ │
│  │   been reviewed by 3 people. The next step is    │ │
│  │   budget approval.                               │ │
│  ──── Evidence · History ────────────────────────── │
│  │   Created 3 days ago · Last modified 2h ago      │ │
│  │   Version 4 · 2 attachments                      │ │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### 4.3 Interaction Zones

| Zone | Behaviour | Trigger |
|------|-----------|---------|
| Header | Shows context (space, type, status) | Always visible |
| Name | Editable inline on click | Click |
| Content | Editable, scrollable | Click or focus |
| Relationships | Expandable, navigable | Click opens connected object |
| Conversations | Expandable, scrollable, type to reply | Click or auto-expand on new message |
| AI Understanding | Always present, updates as context changes | Continuous |
| Evidence/History | Collapsible, details on demand | Click |

### 4.4 Focus Transitions

```
Click object in workspace → Object slides to center, background fades
Click relationship → Current object slides left, new object slides to center
Type search → Search overlay appears, object dims
Press Escape → Return to previous focus
```

---

## 5. Search-as-Thought Specification

### 5.1 Principle

Search is not navigation. Search is thought.

The founder should be able to think "Rahul" and immediately continue working with Rahul. Not open Rahul. **Continue Rahul.**

### 5.2 Behaviour

The search bar is always present at the bottom of the workspace. It is always ready.

```
[Search or type to begin...]
```

**When the founder types:**

| Input | Behaviour |
|-------|-----------|
| `Rahul` | Search identifies Rahul as a person (identity), shows recent context, opens Rahul's workspace |
| `Q3 budget` | Full-text search across objects, shows best match first |
| `@mentions` | Direct references to specific objects |
| `#project` | Scoped search within a space or type |
| Natural language | AI interprets intent, presents most relevant action |

### 5.3 Search Results Display

Search results are not a list. They are a **continuation surface**:

```
┌─────────────────────────────────────────────────────┐
│  Rahul [Contact]                                    │
│  ────                                               │
│  Last conversation: "Sent the proposal yesterday"   │
│  Open commitments: Approve budget proposal          │
│  Related objects: Q3 Strategy, Acme Corp            │
│                                                     │
│  [Click to continue working with Rahul]             │
└─────────────────────────────────────────────────────┘
```

### 5.4 Search as Navigation Elimination

Search replaces:
- The menu bar
- The navigation sidebar
- The breadcrumb trail
- The "recent items" list
- The bookmark system

All of these are replaced by a single search bar that understands the founder's context.

---

## 6. AI Contextual Behaviour Specification

### 6.1 Principle

AI must never appear as a chatbot beside the application.

The workspace itself is the AI.

### 6.2 AI Presence

The AI is not a separate window. It is the behaviour of the workspace:

| Situation | AI Behaviour |
|-----------|-------------|
| Founder opens an object | AI shows its understanding of the object |
| Founder types in search | AI interprets intent, suggests best action |
| Founder is idle | AI observes, prepares Morning Zero |
| Founder starts typing | AI completes thoughts, suggests references |
| Founder is in conversation | AI summarises, suggests next actions |
| Deadline approaches | AI surfaces reminder calmly |
| Pattern detected | AI surfaces observation in Morning Zero |

### 6.3 AI Expression

AI communicates through:

1. **The workspace itself** — objects appear, relationships connect, context shifts
2. **Subtle text** — "I noticed..." "This might be relevant..." "Rahul's proposal is ready..."
3. **Silence** — when nothing needs to be said, nothing appears

The AI never interrupts. The AI never uses notifications. The AI never demands attention.

### 6.4 AI Context Window

The AI's context is the entire workspace. It understands:

- What object the founder is focused on
- What relationships that object has
- What conversations are happening
- What commitments exist
- What the founder's patterns are
- What time it is (morning, afternoon, late night)
- What the founder last worked on

---

## 7. Workspace State Transitions

### 7.1 State Diagram

```
                    ┌─────────────┐
                    │             │
       ┌───────────→│  MORNING    │←──────────────┐
       │            │   ZERO      │               │
       │            │             │               │
       │            └──────┬──────┘               │
       │                   │                       │
       │         click item│type search             │
       │                   ↓                       │
       │            ┌─────────────┐               │
       │            │             │               │
       │            │   AMBIENT   │───────────────┤
       │            │  (scanning) │  idle 30s     │
       │            │             │               │
       │            └──────┬──────┘               │
       │                   │                       │
       │         focus on  │type search             │
       │         object    │                       │
       │                   ↓                       │
       │            ┌─────────────┐               │
       │            │             │               │
       ├────────────│  FOCUSED    │───────────────┤
       │   escape   │  (working)  │  select object│
       │            │             │               │
       │            └──────┬──────┘               │
       │                   │                       │
       │         double-   │type / focus           │
       │         click     │                       │
       │                   ↓                       │
       │            ┌─────────────┐               │
       │            │             │               │
       │            │   DEEP      │───────────────┤
       │            │ (immersive) │  escape        │
       │            │             │               │
       │            └─────────────┘               │
       │                                           │
       └───────────────────────────────────────────┘
                    new day / return
```

### 7.2 Transition Rules

| From | To | Trigger | Animation |
|------|----|---------|-----------|
| Morning Zero | Ambient | Click item, dismiss | Item slides to center, background fades |
| Ambient | Focused | Click object | Object zooms to center, context appears |
| Focused | Deep | Double-click or `/` | Chrome fades, object fills workspace |
| Deep | Focused | Escape | Chrome returns, object shrinks |
| Focused | Ambient | Escape | Object returns to grid position |
| Ambient | Morning Zero | New day / Ctrl+M | Morning items fade in |
| Any | Search | Type anywhere | Overlay slides up from bottom |
| Search | Focused | Click result | Result slides to center |

---

## 8. Navigation Elimination Strategy

### 8.1 What Is Eliminated

| Eliminated Pattern | Replaced By |
|-------------------|-------------|
| Sidebar navigation | Search + continuous workspace |
| Top menu bar | Identity strip + contextual controls |
| Breadcrumb trail | Object header with parent space link |
| Dashboard | Morning Zero |
| Tab bar | Focus transitions |
| "Back" button | Escape key / click outside |
| Modal dialogs | Inline transforms |
| Wizard flows | Progressive disclosure in workspace |
| Admin interface | Ambient controls that appear on focus |

### 8.2 The Only Persistent UI Elements

1. **Identity strip** (top, 32px) — name, avatar, space indicator
2. **Search bar** (bottom, always visible, always accepting input)
3. **Status dot** (bottom-right, shows AI activity: calm/thinking/observing)

Everything else is transient and context-dependent.

---

## 9. Desktop Interaction Model

### 9.1 Canvas

The workspace is a single scrollable canvas. Objects are positioned on the canvas. The canvas has infinite horizontal and vertical extent.

### 9.2 Input

| Input | Behaviour |
|-------|-----------|
| Click object | Focus on that object |
| Click background | Return to ambient state |
| Type anywhere | Search activates |
| Escape | Return to previous state |
| Arrow keys | Navigate between adjacent objects |
| Scroll | Move through canvas (ambient) or through content (focused) |
| Double-click | Enter deep focus on object |
| Drag object | Reposition on canvas (founder's personal layout) |

### 9.3 Window Management

The workspace is not a browser window. It is a full-screen experience. The browser chrome is hidden by default.

### 9.4 Multi-Monitor

On multi-monitor setups, the workspace spans all monitors. The focused object is on the primary monitor. Related context appears on secondary monitors.

---

## 10. Mobile Interaction Model

### 10.1 Adaptation

The mobile experience is not a responsive version of the desktop. It is a distinct interaction model.

### 10.2 Changes

| Desktop | Mobile |
|---------|--------|
| Single canvas | Vertical stack |
| Click to focus | Tap to focus |
| Type anywhere | Tap search bar |
| Drag objects | Long-press to rearrange |
| Multi-monitor | Single screen, deeper layers |
| 70% whitespace | 50% whitespace, scrollable content |

### 10.3 Gestures

| Gesture | Behaviour |
|---------|-----------|
| Tap object | Focus on object |
| Swipe left | Return to previous state |
| Swipe right | Show relationships |
| Swipe down | Show Morning Zero |
| Pull down | Refresh context |
| Long press | Show object actions |
| Pinch | Zoom between ambient/focused/deep |

### 10.4 Bottom Sheet

The search bar on mobile is a bottom sheet that rises when tapped. It behaves like the desktop search but with a mobile-optimized keyboard.

---

## 11. UX Flow Diagrams

See accompanying Excalidraw files:
- `.hermes/plans/diagrams/state_transitions.excalidraw`
- `.hermes/plans/diagrams/object_focus.excalidraw`
- `.hermes/plans/diagrams/morning_zero.excalidraw`
- `.hermes/plans/diagrams/workspace_architecture.excalidraw`

---

## 12. Implementation Roadmap

### 12.1 Phase 1: Foundation (Week 1-2)

**Objective:** Replace page-based navigation with continuous workspace.

| Task | Effort | Dependencies |
|------|--------|-------------|
| 1.1 Single canvas workspace shell | 2 days | None |
| 1.2 Focus level system (ambient/focused/deep) | 2 days | 1.1 |
| 1.3 Object rendering in shell | 2 days | 1.1 |
| 1.4 Smooth transitions between states | 2 days | 1.2 |
| 1.5 Chrome reduction (remove sidebar, tabs) | 1 day | 1.1 |

### 12.2 Phase 2: Morning Zero (Week 2-3)

**Objective:** Replace dashboard with Morning Zero.

| Task | Effort | Dependencies |
|------|--------|-------------|
| 2.1 Morning Zero data aggregation engine | 3 days | 1.2 |
| 2.2 Morning Zero rendering (calm card layout) | 2 days | 2.1 |
| 2.3 Click-to-focus transitions from Morning Zero | 1 day | 1.4, 2.2 |
| 2.4 Learning which items matter to founder | 2 days | 2.1 |

### 12.3 Phase 3: Search-as-Thought (Week 3-4)

**Objective:** Replace navigation with search.

| Task | Effort | Dependencies |
|------|--------|-------------|
| 3.1 Universal search bar (always present) | 1 day | 1.1 |
| 3.2 Natural language intent parsing | 2 days | 3.1 |
| 3.3 Search results as continuation surface | 2 days | 3.1 |
| 3.4 Click-to-continue from search | 1 day | 1.4, 3.3 |

### 12.4 Phase 4: AI Context (Week 4-5)

**Objective:** Make the workspace itself the AI.

| Task | Effort | Dependencies |
|------|--------|-------------|
| 4.1 AI context gathering (what founder is doing) | 2 days | 1.2 |
| 4.2 AI understanding display in object shell | 2 days | 1.3 |
| 4.3 AI observation engine (for Morning Zero) | 2 days | 2.1 |
| 4.4 AI silence discipline (never interrupt) | 1 day | 4.1 |

### 12.5 Phase 5: Mobile (Week 5-6)

**Objective:** Mobile interaction model.

| Task | Effort | Dependencies |
|------|--------|-------------|
| 5.1 Mobile gesture system | 2 days | 1.1 |
| 5.2 Mobile object focus | 2 days | 1.3 |
| 5.3 Mobile search (bottom sheet) | 1 day | 3.1 |
| 5.4 Mobile Morning Zero | 1 day | 2.2 |

### 12.6 Phase 6: Polish (Week 6-7)

**Objective:** Quality, performance, and edge cases.

| Task | Effort | Dependencies |
|------|--------|-------------|
| 6.1 Animation quality pass | 2 days | 1.4 |
| 6.2 Whitespace audit (70/20/10 rule) | 1 day | All |
| 6.3 Performance optimisation | 2 days | All |
| 6.4 Edge case handling | 2 days | All |
| 6.5 Founder testing and iteration | 3 days | All |

### Total Estimated Effort: 6-7 weeks

---

## 13. Verification

### 13.1 Founder Test

A founder who has used SHUNYA for one week should:

1. Never need to ask "where is X?" — search replaces navigation
2. Never feel interrupted — AI is silent until needed
3. Never see a loading page — transitions are continuous
4. Never be confused about what to do next — Morning Zero guides
5. Find traditional software uncomfortable to return to

### 13.2 Technical Verification

| Check | Criteria |
|-------|----------|
| State transitions | All 6 states reachable, all transitions smooth |
| Chrome count | Exactly 3 persistent UI elements |
| Whitespace ratio | ≥70% whitespace in every state |
| AI silence | 0 unsolicited interruptions per session |
| Search latency | <100ms to first result |
| Focus transition | <300ms animation |

---

*End of Specification. Awaiting Founder Review.*