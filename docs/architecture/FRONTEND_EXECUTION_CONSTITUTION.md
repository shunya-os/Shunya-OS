# FRONTEND EXECUTION CONSTITUTION — PHASE 1: LIVING WORKSPACE ARCHITECTURE

> **Status:** Architectural Blueprint — Ready for Implementation
> **Authority:** Derived from Product Experience Constitution v3.0. This document defines the frontend runtime architecture from which every screen, component, and interaction shall naturally emerge.
> **Constitutional Rule:** No production UI shall be implemented before this architecture is ratified. After ratification, implementation shall feel mechanical — the architecture answers every structural question.

---

## CHAPTER 1 — WORKSPACE RUNTIME

### 1.1 What Is a Workspace?

A workspace is a **named, persistent, stateful container** for one or more business objects and their associated runtimes (timeline, intelligence, conversation, components).

A workspace is not a page. Pages are transient views. Workspaces are persistent sessions. Closing a workspace preserves its state. Reopening it restores exactly where the user left off.

### 1.2 Workspace Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Workspace Runtime                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Object   │ │ Timeline │ │Intelligence│ │Component  │ │
│  │ Runtime  │ │ Runtime  │ │ Runtime  │ │ Runtime   │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │              Layout Engine (active)              │ │
│  │  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐       │ │
│  │  │Panel A│ │Panel B│ │Panel C│ │Panel D│       │ │
│  │  └───────┘ └───────┘ └───────┘ └───────┘       │ │
│  └──────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │           Design Token Runtime (active)          │ │
│  │  theme | context | display | accessibility       │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 1.3 Workspace Lifecycle

```
Create ──→ Load ──→ Hydrate ──→ Active ──→ Suspend ──→ Resume ──→ Destroy
                 │                                       │
                 └──→ Error ──→ Recover ───┘             │
                                                          └──→ Archive (persist)
```

**Create:** A workspace is created when the user navigates to a business object or explicitly opens a new workspace. Creation is synchronous (instant) — the workspace frame appears immediately. Content hydrates asynchronously.

**Load:** The workspace runtime loads the workspace definition (layout, panels, components) from the layout registry. This is cached. No network call.

**Hydrate:** The object runtime loads the primary object. The timeline runtime loads recent events. The intelligence runtime loads AI understanding. Components mount with skeleton states.

**Active:** All runtimes are streaming. The user can interact. Components receive state updates.

**Suspend:** The workspace is navigated away from but not closed. All runtimes pause network activity. Component state is serialised to local storage. Memory is released.

**Resume:** The workspace is navigated back to. State is deserialised. Runtimes reconnect. Components rehydrate from cached state (not from scratch).

**Destroy:** The user explicitly closes the workspace. State is serialised to a workspace snapshot (local storage). After 7 days of no access, the snapshot is pruned.

### 1.4 Workspace Types

| Type | Persistence | Layout | Object Requirement |
|------|------------|--------|-------------------|
| Object | Session + snapshot | Object layout | Single primary object |
| Dashboard | Persistent (always exists) | Executive layout | None (aggregate) |
| Conversation | Session | Conversation layout | Optional context object |
| Approval Queue | Persistent | Approval layout | None (queue-based) |
| Search | Ephemeral | Search layout | None (query-based) |
| Document | Session | Document layout | Document object |
| Comparison | Ephemeral | Comparison layout | 2+ objects |

### 1.5 Workspace Navigation

Navigation is object-centric, not page-centric. The user navigates by opening objects, not by clicking menu items. The primary navigation is:

1. **Command Palette (Cmd+K):** Search any object, open any workspace
2. **Object Links:** Click a customer → opens the customer workspace. Click an invoice → opens the invoice workspace
3. **Workspace Bar:** Horizontal list of active workspaces (like tabs in an IDE). Drag to reorder. Right-click to close, pin, suspend.
4. **Sidebar:** Organisational navigation by business concept (Who → What → Money → Know → Intelligence)

### 1.6 Workspace Bar Rules
🟢 Maximum 12 open workspaces. Opening a 13th prompts the user to close one. Workspaces can be pinned (immune to automatic closure). The workspace bar shows a favicon-style icon + object name for each workspace. The active workspace is visually distinct.

---

## CHAPTER 2 — OBJECT RUNTIME

### 2.1 Object Lifecycle

```
Request ──→ Cache Check ──→ Fetch ──→ Normalise ──→ Hydrate ──→ Subscribe ──→ Active
                │                           │
                └──→ From Cache ────────────┘
                                          │
                                    ┌─────┴─────┐
                                    │            │
                                 Mutation    WebSocket
                                 (local)     (server)
```

### 2.2 Object Loading

🟢 Every object loads in phases:

1. **Identity frame:** Object name, type, status, key metric. This appears immediately (cached or skeleton). Target: 0ms.
2. **Summary frame:** AI-generated one-paragraph understanding. This loads from cache (100ms) or generates on first request (500ms-2s).
3. **Data frames:** Fields, relationships, timeline, metrics. These load in priority order (timeline first, then metrics, then full data). Target: 200ms per frame.
4. **Intelligence frame:** AI recommendations, observations, confidence. This loads lazily (after the user has been viewing for 1s). Target: 1s after view.

### 2.3 Object Streaming

🟢 Objects receive updates via WebSocket connection. When an object is updated by any user or system process, the workspace receives a delta and merges it into the current state. The user sees the update in context (a badge appears on the affected field, the timeline adds an entry). No full-page refresh.

### 2.4 Object Relationship Graph

Every object maintains a relationship graph of connected objects. This graph is loaded lazily — only the first degree of relationships loads by default. Expanding a relationship loads the next degree.

```
Customer ──→ Proposal ──→ Invoice ──→ Payment
  │            │            │
  └──→ Timeline             └──→ Ledger Entry
```

### 2.5 Object Caching

🟢 Objects are cached in a local index (IndexedDB or similar) with a TTL of 5 minutes for frequently accessed objects, 30 minutes for infrequently accessed objects. Cache is invalidated on WebSocket update. Offline: objects accessed within the last 24 hours are available for read-only access.

---

## CHAPTER 3 — UNIVERSAL LAYOUT ENGINE

### 3.1 Layout Philosophy

A layout is a **reusable panel arrangement** that a workspace can adopt based on its type and the available viewport. Layouts are not pages. They are runtime configurations that can be applied to any object.

### 3.2 Layout Registry

| Layout | Panels | Responsive Behaviour |
|--------|--------|---------------------|
| **Executive** | Single metric area (top), insights (left), risks (right), activity (bottom) | Stacks: metric → insights → risks → activity on phone |
| **Object** | Identity + summary (top-left), timeline (left), details (right), AI (right-bottom) | Stacks: identity → timeline → details → AI |
| **Conversation** | Messages (center), context (right), suggestions (bottom) | Full-width messages on phone, context as overlay |
| **Timeline** | Filter bar (top), timeline stream (full), detail panel (right, on selection) | Timeline full-width, detail as bottom sheet |
| **Approval** | Queue (left), approval detail (right) | Stacks vertically on phone |
| **Dashboard** | Metric grid (configurable), chart areas | 2-column on tablet, single-column on phone |
| **Knowledge** | Search (top), results (left), document (right) | Document full-width on phone, search as overlay |
| **Document** | Document content (full), AI insights (right overlay) | AI insights as bottom sheet on phone |
| **Comparison** | Object A (left), Object B (right), differences (center) | Stacks vertically on phone, diff as summary |
| **Presentation** | Full-bleed content, no chrome | Same across all sizes |

### 3.3 Layout Adaptation

Layouts adapt via container queries, not viewport breakpoints. Each panel has a minimum width and a preferred width. When the container shrinks beyond the minimum, panels stack vertically. When it grows, panels expand to fill available space. The layout engine never uses horizontal scroll.

### 3.4 Custom Layouts
🟡 Workspaces may have custom layouts defined at creation time. Users cannot create custom layouts in v1.0. This is a v2.0 capability.

---

## CHAPTER 4 — COMPONENT RUNTIME

### 4.1 Component Philosophy

Every component is state-aware, memory-aware, object-aware, accessibility-aware, adaptive, and AI-aware. Components never manage their own data — they receive data from the object runtime via props or a shared state layer.

### 4.2 Component Lifecycle

```
Register ──→ Receive props ──→ Mount ──→ Hydrate ──→ Update ──→ Unmount
  │                              │
  └──→ From registry             └──→ Skeleton → Content
```

### 4.3 Component States

Every component implements these states:

| State | Visual | Behaviour |
|-------|--------|-----------|
| **Skeleton** | Grey shimmer matching component shape | No interaction possible |
| **Empty** | Guidance message + suggested action | No data to display |
| **Content** | Actual data | Full interaction |
| **Error** | Error message + retry action | Retry triggers reload |
| **Loading more** | Bottom loading indicator | Existing content remains interactive |
| **Updating** | Subtle pulse on changed fields | Full interaction |

### 4.4 Component Registry

Components are registered centrally and loaded lazily. A timeline component registered as `shunya-timeline` can be used in any workspace. The component registry is the single source of truth for all available components.

---

## CHAPTER 5 — CONVERSATION RUNTIME

### 5.1 Philosophy

Conversation is not a chat window. Conversation is another way of navigating the operating system. Every message can reference objects, trigger actions, and modify state.

### 5.2 Conversation Architecture

```
┌─────────────────────────────────────────────┐
│              Conversation Runtime             │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ Message  │ │ Context  │ │ Action Router │ │
│  │ Stream   │ │ Resolver │ │ (object CRUD, │ │
│  │          │ │ (ties to │ │  timeline,    │ │
│  │          │ │ current  │ │  approvals)   │ │
│  │          │ │ object)  │ │              │ │
│  └──────────┘ └──────────┘ └──────────────┘ │
│  ┌──────────────────────────────────────────┐ │
│  │          Suggestion Engine               │ │
│  │  (contextual suggestions based on        │ │
│  │   current object + user history)         │ │
│  └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 5.3 Conversation Object Interaction

When a user types in a conversation that references an object ("show me Priya Ventures' invoices"), the conversation runtime:
1. Parses the intent (object query)
2. Resolves the object (customer matching "Priya Ventures")
3. Routes to the object runtime (load invoices for that customer)
4. Returns structured data
5. Renders the response as a rich card (not just text)

The user can then interact with the card — click an invoice to open it, approve it, or share it — without leaving the conversation.

---

## CHAPTER 6 — TIMELINE RUNTIME

### 6.1 Philosophy

One timeline. Universal. Every event from every object flows into a single, queryable timeline. The timeline is not a component — it is a runtime that any component can render.

### 6.2 Timeline Architecture

```
┌─────────────────────────────────────────────┐
│              Timeline Runtime                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ Event    │ │ Filter   │ │ Subscription │ │
│  │ Stream   │ │ Engine   │ │ (WebSocket)  │ │
│  └──────────┘ └──────────┘ └──────────────┘ │
│  ┌──────────────────────────────────────────┐ │
│  │           Virtual List                    │ │
│  │  (1000s of events, renders 20)           │ │
│  └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 6.3 Timeline Rendering

Timelines are rendered as virtual lists. Only visible events are rendered. Events are grouped by date. Each event has: icon (type-based), title, description, timestamp, reference object link.

### 6.4 Timeline Filtering

Timelines can be filtered by: event type, date range, object type, user, AI-generated vs human-generated. Filters are applied client-side (events are already cached).

---

## CHAPTER 7 — INTELLIGENCE RUNTIME

### 7.1 Philosophy

AI is not inside a widget. AI is not inside a page. AI is not inside a chat. AI is a runtime — always present, always contextual, always understanding, always accessible from any workspace via the command palette or a dedicated intelligence panel.

### 7.2 Intelligence Runtime Architecture

```
┌─────────────────────────────────────────────┐
│             Intelligence Runtime              │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ Context  │ │ Provider │ │ Confidence   │ │
│  │ Resolver │ │ Router   │ │ Scorer       │ │
│  │(current  │ │(which AI │ │(high/med/low)│ │
│  │ object,  │ │ endpoint)│ │              │ │
│  │ history) │ │          │ │              │ │
│  └──────────┘ └──────────┘ └──────────────┘ │
│  ┌──────────────────────────────────────────┐ │
│  │          Suggestion Cache                │ │
│  │  (pre-generated insights, refreshed      │ │
│  │   every 5 minutes per object)            │ │
│  └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 7.2 Intelligence Integration Points

| Integration | Where | Behaviour |
|-------------|-------|-----------|
| Morning briefing | Dashboard workspace | Auto-generated on first daily login |
| Object insights | Object workspace sidebar | Pre-generated, cached, refreshed every 5min |
| Conversation | Conversation runtime | On-demand |
| Command palette | Anywhere | On-demand |
| Proactive notification | System | Risk-triggered only |
| Timelines | Timeline runtime | AI observations appear as timeline events |

---

## CHAPTER 8 — ADAPTIVE RUNTIME

### 8.1 Philosophy

Not responsive design. Runtime adaptation. The same workspace loads on any device. The layout engine selects an appropriate layout for the viewport. The object runtime loads the same data. The user's session is uninterrupted.

### 8.2 Adaptation Points

| Device | Layout | Navigation | Interaction |
|--------|--------|------------|-------------|
| Phone | Single-column, stacked panels | Bottom tab bar (5), Cmd+K via gesture | Touch + swipe |
| Tablet | 2-column, side-by-side panels | Sidebar (collapsible), Cmd+K | Touch + keyboard |
| Laptop | Multi-column, panel system | Sidebar + workspace bar, Cmd+K | Keyboard + mouse |
| Desktop | Expanded multi-column | Full sidebar + workspace bar, Cmd+K | Keyboard + mouse |
| Ultrawide | Ambient mode (info flows) | Auto-hiding sidebar, Cmd+K | Keyboard + mouse |
| Executive display | Glanceable metrics | Remote control or voice | Minimal interaction |

---

## CHAPTER 9 — PERFORMANCE RUNTIME

### 9.1 Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| First paint | < 200ms | Navigation timing API |
| Workspace load (cached) | < 500ms | From Cmd+K to interactive |
| Workspace load (cold) | < 2s | From Cmd+K to interactive |
| Timeline render (1000 events) | < 100ms | Virtual list mount |
| Command palette response | < 50ms | Keypress to results |
| AI response (cached insight) | < 100ms | Cache hit |
| AI response (generated) | < 3s | From submit to render |
| WebSocket update → UI | < 100ms | Server event to component update |

### 9.2 Performance Strategies

**Streaming:** Objects load in priority order. Identity frame first, then data frames, then intelligence frames. The user sees progress at every step.

**Lazy loading:** Components below the fold, AI insights, and relationship graphs load after the primary content is interactive.

**Caching:** Objects are cached locally with TTLs. Cache-first strategy for reads. Write-through for mutations.

**Predictive loading:** When the user hovers over a link for >200ms, the target object begins loading. When they hover over a workspace tab, the workspace begins rehydrating.

**Timeline virtualisation:** Only visible timeline events are rendered. The virtual list manages 1000s of events with 20 rendered nodes.

**Incremental rendering:** Large content areas (timelines, tables, long documents) render incrementally. The first 50 items appear immediately. More items render as the user scrolls.

**Offline readiness:** Objects accessed within the last 24 hours are available for read-only access offline. Mutations are queued and synced when online.

---

## CHAPTER 10 — ANIMATION RUNTIME

### 10.1 Philosophy

Animations originate from runtime state, not from CSS classes or component logic. The animation runtime manages all transitions. Components declare their animation intent; the runtime executes it.

### 10.2 Animation Intent Model

Components declare animation intents:

```json
{
  "enter": "fade-in-up",
  "exit": "fade-out-down",
  "stateChange": {
    "loading → content": "cross-fade",
    "content → error": "shake"
  }
}
```

The animation runtime resolves the intent to actual animation values (duration, curve, properties) based on the current theme and accessibility settings.

### 10.3 Reduced Motion

When reduced motion is enabled, the animation runtime ignores all animation intents and sets duration to 0. Components mount and unmount instantly. State changes are instant.

---

## CHAPTER 11 — DESIGN TOKEN RUNTIME

### 11.1 Philosophy

Design tokens are not constants. They are living values that change with theme, accessibility settings, display context, and environment. The design token runtime provides tokens to all components via a reactive store.

### 11.2 Token Delivery

```
User preference ──→ Token Runtime ──→ CSS Custom Properties
System setting                      → Component Props
Accessibility                       → Canvas 2D contexts
Display context
```

Tokens are delivered as CSS custom properties at the root level. Components reference tokens via `var(--shunya-spacing-md)` in CSS or via a `useToken()` hook in components that need token values in JavaScript.

### 11.3 Token Categories

| Category | Count | Example |
|----------|-------|---------|
| Spacing | 15 tokens | `--shunya-spacing-md: 16px` |
| Colour | 200+ tokens | `--shunya-color-primary-500: #8B7D52` |
| Typography | 20 tokens | `--shunya-font-size-lg: 18px` |
| Elevation | 5 tokens | `--shunya-elevation-2: 0 4px 12px...` |
| Radius | 5 tokens | `--shunya-radius-md: 8px` |
| Animation | 10 tokens | `--shunya-timing-normal: 300ms` |
| Icon | 5 tokens | `--shunya-icon-stroke: 2px` |
| Opacity | 10 tokens | `--shunya-opacity-disabled: 0.4` |

---

## CHAPTER 12 — FRONTEND GOVERNANCE

### 12.1 Directory Architecture

```
src/
├── runtimes/           # Core runtimes (workspace, object, timeline, intelligence...)
│   ├── workspace/
│   ├── object/
│   ├── timeline/
│   ├── intelligence/
│   ├── conversation/
│   ├── layout/
│   ├── component/
│   ├── animation/
│   ├── token/
│   └── performance/
├── layouts/            # Layout definitions (executive, object, conversation...)
│   └── registry.ts
├── components/         # Component implementations
│   ├── core/           # Button, Input, Card, Badge...
│   ├── object/         # Timeline, Summary, Metrics, RelationshipGraph...
│   └── workspace/      # WorkspaceBar, Panel, Sidebar...
├── objects/            # Object type definitions
│   ├── customer.ts
│   ├── invoice.ts
│   └── proposal.ts
├── tokens/             # Design token definitions + generation
│   ├── colors.ts
│   ├── typography.ts
│   └── spacing.ts
├── styles/             # Global styles, CSS custom properties
├── api/                # API client, WebSocket, caching
├── state/              # Global state (workspace registry, auth, preferences)
└── app.tsx             # Root component — initialises runtimes, renders workspace
```

### 12.2 Module Boundaries

🟢 Runtimes never import from components. Components import from runtimes. Layouts import from runtimes and components. Objects are type definitions only — no runtime logic. Tokens are consumed by all layers via CSS custom properties.

### 12.3 Testing Strategy

| Layer | Test Type | Tool |
|-------|-----------|------|
| Runtimes | Unit + Integration | Vitest |
| Components | Unit + A11y + Visual | Storybook + Vitest + Axe |
| Layouts | Visual regression | Chromatic/Percy |
| Workspaces | E2E | Playwright |
| Tokens | Snapshot | Vitest |
| Accessibility | Automated + Manual | Axe + Screen reader |

### 12.4 Storybook Strategy
🟢 Every component has a Storybook story. Stories cover: default state, skeleton state, empty state, error state, loading-more state, each variant, each size, dark mode, RTL, reduced motion, high contrast mode.

### 12.5 Component Ownership
🟢 Each component has a single owner (team or individual). Ownership is documented in the component's Storybook page. Changes require owner review.

---

## RATIFICATION STATEMENT

This Frontend Execution Constitution defines the complete runtime architecture for SHUNYA's production frontend.

Every workspace emerges from the Workspace Runtime.
Every object becomes alive through the Object Runtime.
Every timeline flows from the Timeline Runtime.
Every AI interaction routes through the Intelligence Runtime.
Every conversation navigates through the Conversation Runtime.
Every layout adapts through the Layout Engine.
Every component lives within the Component Runtime.
Every animation originates from the Animation Runtime.
Every token is delivered by the Design Token Runtime.

No page will ever be built. Only workspaces.

The architecture answers every structural question. Implementation may begin.

---

*Frontend Execution Constitution — Ready for ratification and implementation.*