# Founder Workspace Architecture Specification

**Phase 8 — SHUNYA OS**
**Status: PROPOSED**
**Version: 1.0**

---

## 1. Philosophy

### 1.1 The Founder is never managing software

The Founder is managing reality. Reality consists of People, Companies, Documents, Tasks, Meetings, Projects, Commitments, Messages, Knowledge, Workflows, and Conversations. SHUNYA understands all of these simultaneously. The screen simply exposes the object the founder is currently thinking about.

### 1.2 The workspace answers four questions

1. What am I currently looking at?
2. What does SHUNYA understand about it?
3. What should happen next?
4. How can I change it through conversation?

### 1.3 No dashboard thinking

Reject: traditional CRM, ERP layout, menu-heavy UI, navigation trees, widget dashboards, multiple applications. Instead: one workspace, infinite context.

### 1.4 Design principles

- 70% whitespace
- 20% context
- 10% controls
- Minimal UI. Maximum understanding.

---

## 2. Canonical Layout

### 2.1 Three-zone structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CONTEXT HEADER                                                         │
│  Current object: Person · Ritu Sharma  ·  Status: Active  ·  ⟐ Aware   │
├──────────────────────┬───────────────────────────────┬──────────────────┤
│                      │                               │                  │
│  LEFT PANEL          │  CENTER — LIVING WORKSPACE    │  RIGHT PANEL     │
│                      │                               │                  │
│  Ambient context     │  The object itself renders    │  SHUNYA          │
│  Recent objects      │  here. No chrome, no chrome,  │  Intelligence    │
│  Relationships       │  no chrome.                   │  (never hidden)  │
│  Pinned references   │                               │                  │
│  Search trigger      │  Customer timeline            │  Understanding   │
│                      │  Proposal                     │  Recommendations │
│                      │  Email                        │  Predictions     │
│                      │  Workflow                     │  Detected risks  │
│                      │  Document                     │  Related objects │
│                      │  Meeting notes                │  Possible actions│
│                      │  Relationship                 │  Reasoning trace │
│                      │  Prediction                   │                  │
│                      │                               │                  │
│                      │  The object is the            │  Persistent.     │
│                      │  application.                 │  Never chatbot.  │
│                      │                               │                  │
├──────────────────────┴───────────────────────────────┴──────────────────┤
│  UNIVERSAL COMPOSER                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Type naturally. "Call Rahul tomorrow." "Convert this to          │   │
│  │ proposal." "Summarise this." "Why is this delayed?"              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Context Header

Always visible. Shows:

| Field | Content | Example |
|-------|---------|---------|
| Object type | Canonical type name | Person, Company, Proposal, Meeting |
| Object name | Human-readable label | Ritu Sharma |
| Status | Current lifecycle state | Active, Draft, Pending, Completed |
| Awareness | SHUNYA's awareness state | Aware, Searching, Learning, Idle |

No generic dashboard cards. No navigation breadcrumbs. The header states what the founder is looking at.

### 2.3 Left Panel — Ambient Context

Width: 280px. Shows:

| Section | Content | Behaviour |
|---------|---------|-----------|
| Search | Single input, Ctrl+K trigger | Full-text across all objects |
| Recent | Last 10 objects by recency | Click to switch context |
| Relationships | Objects related to current focus | 2-hop relationship graph |
| Pinned | Founder-pinned references | Manual pin/unpin |

Collapsible at < 900px viewport width.

### 2.4 Center — Living Workspace

The object renders itself here. The same interface renders every object type:

| Component | What it shows | Universal |
|-----------|--------------|-----------|
| Object header | Type icon, name, status, metadata | Yes |
| Timeline | Chronological event stream | Yes |
| Content | The object's primary content | Yes |
| Evidence | Supporting observations, sources | Yes |
| Conversation | Linked conversation history | Yes |
| Related | 1-hop relationship navigation | Yes |

No module-specific rendering logic. Every object type implements the same interface contract.

### 2.5 Right Panel — SHUNYA Intelligence

Width: 320px. Persistent. Never disappears. Never becomes a chatbot.

| Section | Content | Source |
|---------|---------|--------|
| Understanding | What SHUNYA knows about this object | Knowledge Engine |
| Recommendations | 3-5 suggested actions | Planner Engine |
| Predictions | Trend, risk, opportunity forecasts | Prediction Engine |
| Risks | Active risks with severity | Risk Engine |
| Reasoning | 8-stage cognitive trace | Cognitive Engine |
| Related | 2-hop link suggestions | Relationship Engine |

Each section is a collapsible card. The panel is always present but never steals focus.

### 2.6 Universal Composer

Single input at the bottom. Always visible. Never a multi-field form.

The founder types naturally:

| Input | Behaviour |
|-------|-----------|
| "Call Rahul tomorrow" | Creates task, sets reminder |
| "Convert this to proposal" | Triggers proposal generation |
| "Summarise this" | Invokes Knowledge Engine summary |
| "Why is this delayed?" | Queries Reasoning Engine |
| "Show previous conversations" | Filters timeline |
| "Send this" | Triggers execution |

One input. Entire OS.

---

## 3. Universal Object Model

### 3.1 Canonical interface

Every object exposes:

```python
interface UniversalObject:
    # Identity
    object_id: str
    object_type: str
    name: str
    
    # Metadata
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    # Content
    content: Any  # Type-specific primary data
    summary: str  # Always computed
    
    # Relationships
    relationships: List[Relationship]
    
    # Timeline
    events: List[TimelineEvent]
    
    # Evidence
    evidence: List[Evidence]
    
    # State
    current_state: State
    predictions: List[Prediction]
    
    # Actions
    suggested_actions: List[Action]
    
    # Conversation
    conversation_history: List[Message]
```

### 3.2 Object contract

Every object type implements:

| Method | Returns | Purpose |
|--------|---------|---------|
| `load(id)` | Object data | Retrieve from store |
| `summary()` | dict | Structured summary for Intelligence panel |
| `timeline()` | List[Event] | Chronological event stream |
| `evidence()` | List[Evidence] | Supporting observations |
| `reasoning()` | ReasoningTrace | How SHUNYA reached its understanding |
| `actions()` | List[Action] | Suggested actions |
| `related()` | List[Relationship] | 1-hop and 2-hop relationships |
| `render()` | ViewModel | Data for the Living Workspace |

### 3.3 Object types (initial)

| Type | Primary content | Timeline events |
|------|----------------|-----------------|
| Person | Profile, contact, preferences | Interactions, lifecycle |
| Company | Profile, industry, size | Deals, engagement |
| Document | Content, metadata, version | Edits, reviews |
| Task | Description, assignee, due | Status changes |
| Meeting | Agenda, notes, decisions | Preparation, follow-up |
| Project | Goals, milestones, team | Progress, blockers |
| Commitment | Parties, terms, status | Obligations, fulfilment |
| Message | Content, thread, participants | Replies, reactions |
| Knowledge | Facts, sources, confidence | Updates, validation |
| Workflow | Stages, current step, actors | State transitions |
| Conversation | Messages, participants, context | New messages |

### 3.4 No module-specific rendering

A Person renders through the same interface as a Proposal. The Living Workspace calls `object.render()` and displays the result. The Intelligence panel calls `object.summary()` and `object.reasoning()`. The Universal Composer operates on `object.actions()`.

---

## 4. State Management Architecture

### 4.1 Single state tree

```
state = {
    currentObject: { type, id, data },
    currentView: "morning-zero" | "ambient" | "focused" | "deep",
    intelligence: { understanding, recommendations, predictions, risks, reasoning },
    leftPanel: { visible, search, recent, relationships, pinned },
    composer: { input, suggestions, mode },
    history: [ ...state snapshots ],  # max 50
}
```

### 4.2 State transitions

| Action | Transition |
|--------|------------|
| Click object | `currentObject = new; currentView = "focused"` |
| Search | `leftPanel.search = query; render results` |
| Composer input | `composer.input = text; compute suggestions` |
| Context switch | `history.push(state); currentObject = new` |
| Back | `currentObject = history.pop()` |

### 4.3 Server-driven state

The frontend never reasons. All intelligence payloads come from the backend:

```
GET /api/founder/object/<type>/<id>  → { object, summary, intelligence, actions }
GET /api/founder/recent              → [{ type, id, name, updated_at }]
GET /api/founder/relationships/<type>/<id> → [{ type, id, name, relationship }]
POST /api/founder/composer           → { intent, action, updated_object }
```

---

## 5. Workspace Routing Model

### 5.1 URL-based navigation

```
/workspace                          → Morning Zero (default)
/workspace/object/<type>/<id>       → Focused on object
/workspace/search?q=<query>         → Search results
/workspace/space/<space_id>         → Ambient within space
```

### 5.2 Client-side routing

No full-page reloads. JavaScript `history.pushState` updates the URL hash. A `popstate` listener restores the previous state.

### 5.3 Four views

| View | When | Content |
|------|------|---------|
| **Morning Zero** | Workspace load, no active context | SHUNYA's current understanding, active alerts, suggested starting points |
| **Ambient** | Founder scanning, no specific object | Recent objects, relationships, system health, pending items |
| **Focused** | Object selected | The object in the Living Workspace |
| **Deep** | Immersive work on an object | Full-screen object view, left/right panels collapsed |

---

## 6. Conversation Integration Layer

### 6.1 Architecture

```
┌──────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Universal   │─────▶│  Intent Parser   │─────▶│  Action Router   │
│  Composer    │      │  (deterministic) │      │  (deterministic) │
└──────────────┘      └──────────────────┘      └──────────────────┘
                                                         │
                    ┌────────────────────────────────────┼────────────────────┐
                    │                                    │                    │
                    ▼                                    ▼                    ▼
            ┌──────────────┐                    ┌────────────────┐  ┌────────────────┐
            │  Object      │                    │  Task          │  │  Query         │
            │  Mutation    │                    │  Creation      │  │  Engine        │
            └──────────────┘                    └────────────────┘  └────────────────┘
```

### 6.2 Intent parsing

Deterministic pattern matching — no AI dependency for routing:

| Pattern | Intent | Action |
|---------|--------|--------|
| "Call X [time]" | Create call task | Task creation |
| "Convert to X" | Transform object | Proposal generation |
| "Summarise" | Request summary | Knowledge Engine |
| "Why X" | Request reasoning | Reasoning Engine |
| "Show X" | Filter timeline | Timeline query |
| "Send X" | Execute action | Execution Engine |
| "Who X" | Identity query | Identity resolver |
| "Create X" | Object creation | Object factory |

### 6.3 Conversation as enhancement

Conversation is not the operating model. SHUNYA continuously observes, understands, relates, predicts, recommends, and executes without requiring prompts. The composer is for the founder to steer, not to wake up.

---

## 7. Context Persistence Architecture

### 7.1 Three layers

| Layer | Lifetime | Storage | Content |
|-------|----------|---------|---------|
| Session | Browser session | JavaScript state | Current object, view, scroll position |
| Browser | Persistent | localStorage | Recent objects, pinned items, preferences |
| Server | Permanent | Database | All object data, conversation history |

### 7.2 State restoration

On workspace load:
1. Check URL hash for object reference
2. If absent, check `localStorage` for last context
3. If absent, render Morning Zero
4. Restore left panel state (pinned, recent)

### 7.3 No data loss

Every composable action is persisted to the server before the frontend state changes. Optimistic updates are not used — the server is the source of truth.

---

## 8. Relationship Navigation

### 8.1 Graph-based navigation

The founder navigates by following relationships, not by traversing menus.

```
Current: Person (Ritu Sharma)
  ├── Company: Acme Corp
  │     ├── Document: Proposal Q3
  │     ├── Commitment: Service Agreement
  │     └── Person: Amit (co-founder)
  ├── Meeting: Strategy Review (Jul 20)
  │     └── Task: Follow-up on pricing
  ├── Task: Send proposal (due Jul 25)
  └── Conversation: 3 messages
```

### 8.2 Two-hop default

The left panel shows the 1-hop graph. Clicking any node expands to 2-hop. The founder can traverse freely without leaving the workspace.

### 8.3 Relationship engine

The Relationship Engine (kernel) provides:

```
GET /api/founder/relationships/<type>/<id>?depth=2
```

Returns a JSON graph of connected objects. The frontend renders it as a navigable tree.

---

## 9. Desktop Layout

### 9.1 Dimensions

| Zone | Width | Behaviour |
|------|-------|-----------|
| Context Header | Full width | 48px height, always visible |
| Left Panel | 280px | Scrollable, collapsible |
| Center | flex (1fr) | Scrollable, primary content |
| Right Panel | 320px | Scrollable, always visible |
| Universal Composer | Full width | 56px height, always visible |

### 9.2 Minimum viewport

1280 × 800px. Below this, panels collapse responsively.

### 9.3 Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+K | Focus search |
| Escape | Clear search, return to current object |
| Alt+Left | Navigate back |
| Alt+Right | Navigate forward |
| Ctrl+Enter | Submit composer |

---

## 10. Tablet Layout

### 10.1 Breakpoint: 768-900px

| Zone | Behaviour |
|------|-----------|
| Left Panel | Hidden by default, slide-in overlay |
| Center | Full width |
| Right Panel | Hidden by default, slide-in overlay |
| Composer | Always visible |

### 10.2 Navigation

- Swipe left → show Intelligence panel
- Swipe right → show Ambient context
- Tap header → toggle between object types

### 10.3 Touch targets

Minimum 44×44px for all interactive elements.

---

## 11. Mobile Layout

### 11.1 Breakpoint: < 768px

| Zone | Behaviour |
|------|-----------|
| Left Panel | Hidden, accessible via top-left button |
| Center | Full width, single column |
| Right Panel | Hidden, accessible via top-right button |
| Composer | Always visible, above keyboard |

### 11.2 Single-object focus

The mobile view shows exactly one object at a time. No split panels. Context switching is a full-screen transition.

### 11.3 Composer behaviour

- Input field moves above the keyboard
- Autofocus on tap
- Results appear inline (not a popup)

---

## 12. Accessibility Considerations

### 12.1 Standards

- WCAG 2.1 AA minimum
- Full keyboard navigation
- Screen reader support (ARIA labels on all interactive elements)
- Focus indicators on all focusable elements

### 12.2 Colour

| Requirement | Value |
|-------------|-------|
| Text contrast | ≥ 4.5:1 (normal), ≥ 3:1 (large) |
| Non-text contrast | ≥ 3:1 |
| Colour dependence | No information conveyed by colour alone |

### 12.3 Motion

`prefers-reduced-motion: reduce` → all animations disabled.

### 12.4 Font

- System font stack (Inter, system-ui, sans-serif)
- Minimum 14px body text
- Line height 1.5 minimum

---

## 13. Performance Strategy

### 13.1 Targets

| Metric | Target |
|--------|--------|
| Workspace load | < 2s (first paint) |
| Object switch | < 250ms (client-side) |
| Search | < 150ms (pre-loaded index) |
| Composer response | < 200ms (intent parse + action) |
| Intelligence panel | < 500ms (server round-trip) |

### 13.2 Techniques

| Technique | Where |
|-----------|-------|
| Preload object index | On workspace load |
| Lazy-load intelligence | Right panel renders after center |
| Debounce search | 300ms after last keystroke |
| Cache relationship graph | localStorage, 5-minute TTL |
| Background prefetch | Intelligence for current + 1-hop objects |

### 13.3 No paid-model dependency

All intelligence is deterministic backend computation. No AI model calls for workspace rendering, navigation, or context assembly.

---

## 14. Implementation Roadmap

### Phase 8A — Core Layout (Sprint 1-2)

| Deliverable | Files | Description |
|-------------|-------|-------------|
| Three-zone layout | `templates/founder/workspace.html` | Context header, left/center/right |
| Universal Composer | `app/founder/composer.py` | Intent parser + action router |
| Workspace routing | `app/founder/routes.py` | URL-based routing, 4 views |
| Session state | `app/founder/state.py` | Single state tree, history |

### Phase 8B — Universal Object Renderer (Sprint 3-4)

| Deliverable | Files | Description |
|-------------|-------|-------------|
| Object interface | `app/founder/renderer.py` | Universal renderer, no switch statements |
| Object registry | `app/founder/registry.py` | Type-to-handler mapping |
| Timeline renderer | `app/founder/timeline.py` | Universal event stream |
| Evidence renderer | `app/founder/evidence.py` | Universal evidence display |

### Phase 8C — Intelligence Panel (Sprint 5-6)

| Deliverable | Files | Description |
|-------------|-------|-------------|
| Understanding bridge | `app/founder/bridge.py` | Knowledge Engine → Intelligence cards |
| Recommendations bridge | `app/founder/bridge.py` | Planner Engine → action cards |
| Predictions bridge | `app/founder/bridge.py` | Prediction Engine → forecast cards |
| Reasoning trace | `app/founder/bridge.py` | Cognitive Engine → trace display |

### Phase 8D — Relationship Navigation & Context Persistence (Sprint 7-8)

| Deliverable | Files | Description |
|-------------|-------|-------------|
| Relationship graph | `app/founder/graph.py` | 2-hop graph navigation |
| Context persistence | `app/founder/persistence.py` | Session + browser + server layers |
| Search integration | `app/founder/search.py` | Full-text across all objects |
| Responsive layout | `static/css/workspace.css` | Three breakpoints |

### Phase 8E — Polish & Verification (Sprint 9-10)

| Deliverable | Files | Description |
|-------------|-------|-------------|
| Accessibility audit | `accessibility/` | WCAG 2.1 AA verification |
| Performance benchmarks | `tests/performance/` | All targets verified |
| Keyboard navigation | `static/js/workspace.js` | Full keyboard support |
| Integration tests | `tests/founder/` | End-to-end workspace tests |

---

## Appendix A: Object Interface Contract

```python
@dataclass
class ObjectViewModel:
    object_id: str
    object_type: str
    name: str
    status: str
    summary: str
    content: Any
    timeline: List[TimelineEvent]
    evidence: List[Evidence]
    relationships: List[Relationship]
    suggested_actions: List[Action]
    intelligence: IntelligencePayload
    conversation: ConversationPreview

@dataclass
class IntelligencePayload:
    understanding: str
    recommendations: List[str]
    predictions: List[Prediction]
    risks: List[Risk]
    reasoning: ReasoningTrace
    related: List[RelatedObject]

@dataclass
class TimelineEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    title: str
    description: str
    actor: str
    importance: float  # 0.0 - 1.0
```

## Appendix B: API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/founder/object/<type>/<id>` | Full object view model |
| GET | `/api/founder/recent` | Recent objects |
| GET | `/api/founder/relationships/<type>/<id>` | Relationship graph |
| POST | `/api/founder/composer` | Process natural language input |
| GET | `/api/founder/search?q=<query>` | Full-text search |
| GET | `/api/founder/state` | Workspace state snapshot |
| GET | `/api/founder/morning` | Morning Zero data |
| GET | `/api/founder/ambient` | Ambient scan data |

## Appendix C: Dependencies

| Dependency | Purpose | Already exists? |
|------------|---------|-----------------|
| Knowledge Engine | Object understanding, summaries | ✅ ES-002 |
| Planner Engine | Action recommendations | ✅ ES-004 |
| Prediction Engine | Trend/risk/opportunity | ✅ Milestone III |
| Cognitive Engine | Reasoning traces | ✅ Milestone VA |
| Execution Engine | Action execution | ✅ ES-005 |
| Relationship Engine | Graph navigation | ✅ Kernel |
| Identity Resolver | Person/company resolution | ✅ Kernel |
| Object Registry | Type-to-handler mapping | ✅ Kernel |
| WorkspaceRuntime | JSON API bridge | ✅ `app/workspace_runtime.py` |
| Composite UI | Template + JS SPA | ✅ `app/founder/` |