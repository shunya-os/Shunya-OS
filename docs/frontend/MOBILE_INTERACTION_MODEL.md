# SHUNYA Mobile Interaction Model

> **Canonical Frontend Document · Phase C3 Parallel**
> **Status: CANONICAL — Implementation-Independent Interaction Specification**
> **Version: 1.0**
> **Derived From: 08_experience_canon.md (Experience Canon)**
> **Target: Mobile (< 600px viewport) · Tablet (600–899px)**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Mobile Philosophy](#2-mobile-philosophy)
3. [Mobile Surface Layout](#3-mobile-surface-layout)
4. [Touch Interaction Model](#4-touch-interaction-model)
5. [Gesture Vocabulary](#5-gesture-vocabulary)
6. [Navigation Architecture](#6-navigation-architecture)
7. [Keyboard & Hardware](#7-keyboard--hardware)
8. [Offline Behavior](#8-offline-behavior)
9. [Tablet Adaptation](#9-tablet-adaptation)
10. [Relationship to Other Documents](#10-relationship-to-other-documents)

---

## 1. Purpose

This document defines how humans interact with SHUNYA on mobile devices (< 600px) and tablets (600–899px). It specifies the complete touch interaction vocabulary, gesture model, and responsive adaptation patterns.

**The mobile experience is not a shrunken desktop. It is a purpose-built experience for consuming objects, triaging attention, and performing quick actions on the go.** (08 §4.12)

---

## 2. Mobile Philosophy

### 2.1 Core Principle

Mobile SHUNYA is for **consumption, triage, and quick action** — never for deep object manipulation or complex analysis. The mobile experience:

- **Assumes partial attention** — the human is likely walking, commuting, or multitasking
- **Prioritizes reading over writing** — object consumption is the default; creation is secondary
- **Respects thumb zones** — all interactive elements are within thumb reach
- **Assumes intermittent connectivity** — offline resilience is a first-class concern
- **Leverages device context** — location, time, notifications, and voice are primitives

### 2.2 Mobile vs Desktop Differences

| Aspect | Desktop | Mobile |
|--------|---------|--------|
| **Work mode** | Deep work, creation, analysis | Consumption, triage, quick action |
| **Input** | Keyboard + mouse | Touch + voice |
| **Navigation** | Continuous surface, keyboard shortcuts | Bottom bar, swipe gestures |
| **Layout** | Multi-column | Single column |
| **Panels** | Persistent sidebars | Bottom sheets, overlays |
| **Attention** | Full attention | Partial, interruptible |
| **Connectivity** | Stable, always-on | Intermittent, variable |
| **Speed** | Keyboard-speed | Thumb-reach optimized |

### 2.3 Mobile Design Values

| Value | Manifestation |
|-------|--------------|
| **One-handed** | All interactions are reachable with a thumb on a 6.7" screen |
| **Fast** | Sub-second responses, optimistic UI, offline-first reads |
| **Clear** | Minimal information density, single-object focus |
| **Connected** | Notifications link directly to objects; context is never lost |
| **Capable offline** | Objects are readable without connectivity; actions queue |

---

## 3. Mobile Surface Layout

### 3.1 Mobile Surface (Default State)

```
┌──────────────────────────────────────┐
│ TOP BAR                               │
│  ← Workspace   Object Type    🔍 🔔 👤│  (44px)
├──────────────────────────────────────┤
│                                       │
│       FOCAL OBJECT AREA               │
│       (primary surface)               │
│                                       │
│  ╔══════════════════════════╗         │
│  ║  OBJECT: "Q3 Budget     ║         │
│  ║  Approval"               ║         │
│  ║                          ║         │
│  ║  Status: IN_REVIEW       ║         │
│  ║  Owner: Alice            ║         │
│  ║                          ║         │
│  ║  ┌────────────────────┐  ║         │
│  ║  │  Content area      │  ║         │
│  ║  │  (scrolls within)  │  ║         │
│  ║  └────────────────────┘  ║         │
│  ║                          ║         │
│  ║  [Approve] [Changes]     ║         │
│  ╚══════════════════════════╝         │
│                                       │
│                                       │
├──────────────────────────────────────┤
│ BOTTOM NAVIGATION                     │
│  [Objects] [Search] [AI] [Notifs]    │  (56px)
└──────────────────────────────────────┘
```

### 3.2 Mobile Layout Rules

1. **Top bar is 44px** — compact, shows workspace, object type, and status icons.
2. **Bottom navigation is 56px** — thumb-reachable, contains 4 primary tabs.
3. **Focal area fills remaining space** — single column, scrollable.
4. **No persistent sidebars** — all panels become bottom sheets or overlays.
5. **Content area never exceeds 600px** — designed for mobile viewport.

### 3.3 Tablet Surface (Landscape)

```
┌──────────────────────────────────────────────────────────┐
│ TOP BAR (48px)                                            │
├────────────────────────────────────────┬─────────────────┤
│                                        │                 │
│ OBJECT BROWSER                         │  FOCAL AREA     │
│ (bottom sheet trigger)                 │                 │
│                                        │  The object     │
│  Recent objects in this workspace       │  in full view   │
│  ┌────────────────────────────────┐    │                  │
│  │ ○ Decision: Q3 Budget         │    │  70/20/10 ratio  │
│  │ ○ Task: Hire Engineers       │    │  maintained      │
│  │ ● Event: Review Meeting      │    │                  │
│  └────────────────────────────────┘    │                  │
│                                        │                  │
│  [Show all ▸]                           │                  │
│                                        │                  │
├────────────────────────────────────────┴─────────────────┤
│ BOTTOM BAR (compact)                                      │
│  [Objects ▼] [Search] [AI] [Notifications]               │
└──────────────────────────────────────────────────────────┘
```

### 3.4 Tablet Layout Rules

1. **Tablet landscape uses a two-column layout** — object browser (compact, 240px) and focal area.
2. **Object browser is collapsible** — slides in from left, triggered by tapping "Objects" in bottom bar.
3. **Relationship panel is a slide-over** — triggered by tapping a relationship link, slides from right, 300px.
4. **Bottom bar is compact** — 48px, same 4 items as mobile but with labels.
5. **Tablet portrait** — behaves like mobile layout (single column, bottom sheets).

---

## 4. Touch Interaction Model

### 4.1 Touch Targets

| Element | Minimum Size | Spacing | Notes |
|---------|-------------|---------|-------|
| Bottom nav items | 56×44px | 0 | Fill width, 4 items |
| Object cards | Full width × 72px | 8px between | Tappable entire area |
| Buttons | 44×44px | 8px between | Minimum for all touch targets |
| Icon buttons | 44×44px | 8px | Expanded hit area |
| Input fields | Full width × 44px | 16px margin | Minimum height |
| Bottom sheet handles | 44×16px | — | Always visible |
| Swipeable items | Full width × 72px | — | Swipe gesture target |

### 4.2 Touch States

| State | Visual Feedback | Trigger |
|-------|----------------|---------|
| **Touch down** | Background tint (press state) | Finger touches surface |
| **Touch move** | Element tracks finger (draggable) | Finger moves while touching |
| **Touch up (tap)** | Brief highlight, then action | Finger lifts within target bounds |
| **Touch up (cancel)** | Background returns to normal | Finger lifts outside target bounds |
| **Long press** | Haptic vibration, context menu after 500ms | Finger held in place |
| **Swipe** | Element follows finger, action on threshold | Finger moves horizontally or vertically |

### 4.3 Touch Interaction Rules

1. **All touch feedback is within 100ms** — every touch event has immediate visual response.
2. **Touch targets have 44×44px minimum** — no touch target violates the WCAG 2.5.5 minimum.
3. **No hover-dependent interactions** — hover does not exist on mobile; all information is available on tap.
4. **Touch cancellation is always possible** — dragging a finger outside the target cancels the action.
5. **Haptic feedback for destructive actions** — delete, archive, confirm destructive operations trigger haptic.

---

## 5. Gesture Vocabulary

### 5.1 Navigation Gestures

| Gesture | Action | Sensitivity |
|---------|--------|-------------|
| **Tap (single)** | Select object, follow link, press button | Standard |
| **Tap (double)** | Edit inline (if editable), zoom content | 300ms window |
| **Long press** | Context menu for object or element | 500ms hold |
| **Swipe left** | Delete/archive object (with confirmation) | 30% threshold |
| **Swipe right** | Mark as read / complete | 30% threshold |
| **Swipe up** | Open object relationships bottom sheet | 40px vertical |
| **Swipe down** | Close current overlay, dismiss keyboard | 40px vertical |
| **Pinch** | Expand/collapse object disclosure level | 20% threshold |
| **Pull to refresh** | Refresh current object state | 60px pull |

### 5.2 Bottom Sheet Gestures

| Gesture | Action |
|---------|--------|
| **Tap sheet handle** | Toggle between peek and full height |
| **Swipe down on sheet** | Dismiss sheet (if content scrolled to top) |
| **Swipe up on sheet** | Expand sheet to full height |
| **Drag handle** | Scroll sheet height between peek and full |
| **Tap outside sheet** | Dismiss sheet |

### 5.3 Object Specific Gestures

| Gesture | Context | Action |
|---------|---------|--------|
| **Swipe left on object card** | Object browser | Archive object (undoable) |
| **Swipe right on object card** | Notification list | Mark notification as read |
| **Long press on object card** | Object browser | Multi-select mode enters |
| **Tap relationship link** | Focal area | Open bottom sheet with object preview |
| **Swipe up on timeline** | Object detail | Scroll to next/previous timeline event |

### 5.4 Gesture Rules

1. **All gestures are discoverable** — visual hints indicate swipable/tappable elements on first use.
2. **All gestures have button equivalents** — no action is gesture-only.
3. **Swipe actions are reversible** — swipe-to-archive shows an "Undo" toast.
4. **Edge gestures are reserved** — system back gestures (iOS/Android) are preserved.
5. **Gesture conflicts are avoided** — horizontal swipe only where vertical scroll is absent.

---

## 6. Navigation Architecture

### 6.1 Bottom Navigation

The bottom navigation bar contains exactly 4 items:

| Tab | Icon | Behavior |
|-----|------|----------|
| **Objects** | Grid icon | Shows object browser bottom sheet for the current workspace |
| **Search** | Search icon | Opens object search with auto-focus on search input |
| **AI** | Sparkle icon | Opens AI collaborator as a full-screen panel |
| **Notifications** | Bell icon | Opens notification list overlay |

### 6.2 Navigation Flow

```
DEFAULT STATE
    │
    ├── Tap "Objects" ──► Object Browser (bottom sheet)
    │                           │
    │                           ├── Tap object ──► Focal object (dismisses sheet)
    │                           ├── Search within ──► Filtered list
    │                           └── Swipe ──► Quick action on object
    │
    ├── Tap "Search" ──► Object Search (overlay)
    │                           │
    │                           ├── Type query ──► Results update in real-time
    │                           ├── Tap result ──► Focal object (dismisses search)
    │                           └── Escape ──► Dismiss search
    │
    ├── Tap "AI" ──► AI Panel (full-screen)
    │                           │
    │                           ├── Type / voice query ──► AI responds
    │                           ├── Tap suggestion ──► Execute action
    │                           └── Back ──► Return to focal object
    │
    └── Tap "Notifications" ──► Notification List (overlay)
                                │
                                ├── Tap notification ──► Navigate to linked object
                                └── Swipe right ──► Mark as read
```

### 6.3 Back Navigation

| Action | Behavior |
|--------|----------|
| **Hardware back button** | Closes current overlay → returns to previous surface state |
| **Swipe from left edge** | Same as hardware back (system gesture) |
| **Close button (X)** | Closes current overlay/sheet |
| **Tap outside sheet** | Dismisses bottom sheet |

### 6.4 Deep Linking

| URL Pattern | Mobile Behavior |
|-------------|----------------|
| `/workspace/<id>` | Opens workspace, shows default focal object |
| `/workspace/<id>/<type>/<obj_id>` | Opens workspace directly to specific object |
| `/search?q=<query>` | Opens search overlay with pre-populated query |
| `shunya://workspace/<id>` | Custom scheme deep link (native app) |

---

## 7. Keyboard & Hardware

### 7.1 Hardware Keyboard (Tablet with keyboard)

When a hardware keyboard is detected on a tablet:

| Shortcut | Action |
|----------|--------|
| `Cmd+K` | Open search |
| `Cmd+Shift+K` | Open AI |
| `Cmd+[` | Back |
| `Escape` | Close overlay |
| `Tab` | Move through interactive elements |

### 7.2 Software Keyboard

| Event | Behavior |
|-------|----------|
| **Keyboard opens** | Bottom navigation hides. Content area adjusts to avoid overlap. |
| **Keyboard closes** | Bottom navigation reappears. |
| **Search input focus** | Search results appear below. Keyboard stays open. |
| **Form input focus** | Content scrolls to keep focused field visible. |

### 7.3 Voice Input

| Trigger | Behavior |
|---------|----------|
| **Mic icon in search** | Opens system voice recognition, fills search input |
| **Mic icon in AI panel** | Opens system voice recognition, fills AI input |
| **Voice shortcut** | "Create a task called…" — parses and creates object |

---

## 8. Offline Behavior

### 8.1 Offline Capabilities

| Operation | Offline Behavior |
|-----------|-----------------|
| **View last-seen state** | ✓ Available — object cache persists locally |
| **View cached objects** | ✓ Available — last 50 objects are cached |
| **Create object** | ✓ Queued — object created locally, queued for sync |
| **Update object** | ✓ Queued — update stored in pending queue |
| **Delete object** | ✓ Queued — deletion queued for sync |
| **AI interaction** | ✗ Unavailable — requires network |
| **Search all objects** | ✗ Unavailable — server-side index required |
| **Relationship navigation** | ✓ Available — cached relationships work |

### 8.2 Sync Behavior

| Event | Behavior |
|-------|----------|
| **Object created offline** | Shows in local object list with "pending sync" indicator |
| **Connection restored** | Pending queue flushes in order. Conflicts resolved by "last write wins." |
| **Sync conflict** | Both versions preserved. User notified via notification. |
| **Sync progress** | Progress indicator in top bar during sync |
| **Sync failure** | Pending items retry with exponential backoff. User notified after 3 failures. |

### 8.3 Offline Limits

| Resource | Limit |
|----------|-------|
| Cached objects | 50 most recently viewed |
| Pending actions | 100 queued actions max |
| Cache storage | 50MB max |
| Cache duration | 7 days without refresh |

---

## 9. Tablet Adaptation

### 9.1 Tablet-Specific Behaviors

| Aspect | Tablet Behavior |
|--------|----------------|
| **Layout** | Landscape: two-column (browser + focal). Portrait: single column. |
| **Object browser** | Landscape: persistent compact sidebar. Portrait: bottom sheet. |
| **Relationship panel** | Slide-over from right (300px). |
| **AI panel** | Slide-over from right (400px, not full screen). |
| **Keyboard** | Hardware keyboard shortcuts active. |
| **Multi-window** | Split view is respected (50/50 or 70/30 SHUNYA + another app). |

### 9.2 Tablet Breakpoints

| Orientation | Width | Layout |
|-------------|-------|--------|
| Portrait | 600–899px | Single column, mobile-like |
| Landscape small | 900–1023px | Two-column, compact browser |
| Landscape large | 1024–1199px | Two-column, full browser |

### 9.3 Tablet Interaction Model

| Aspect | Mobile | Tablet |
|--------|--------|--------|
| Bottom nav | 56px, 4 items | 48px, 4 items with labels |
| Object browser | Bottom sheet | Side panel (landscape), sheet (portrait) |
| Relationship panel | Bottom sheet | Slide-over (landscape), sheet (portrait) |
| AI panel | Full screen | Slide-over (landscape), full screen (portrait) |
| Drag and drop | Long press + drag | Standard drag (with stylus support) |

---

## 10. Relationship to Other Documents

| Document | Relationship |
|----------|-------------|
| **08_experience_canon.md** | Mobile philosophy (08 §4.12) is the foundation of this document |
| **INFORMATION_ARCHITECTURE.md** | Mobile navigation architecture (bottom nav, overlays) implements the IA for small screens |
| **DESIGN_SYSTEM.md** | All design tokens apply at mobile breakpoints with spacing reductions |
| **DESKTOP_INTERACTION_MODEL.md** | Both derive from the same philosophy; mobile is a purpose-adapted alternative, not a subset |
| **COMPONENT_SPECIFICATION.md** | Mobile uses the same component set with responsive adaptations specified here |

---

> **End of Mobile Interaction Model**
> **[Return to INDEX](#)**