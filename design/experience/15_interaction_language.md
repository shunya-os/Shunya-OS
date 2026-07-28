# SHUNYA Interaction Language

> **Canonical Reference — Phase X2A**
> This document is the permanent architectural contract between philosophy and frontend engineering. Every future SHUNYA interface must inherit this language. Nothing should be invented per application.
>
> The Human Principles define *why*.
> The Presence Canon defines *how it feels*.
> The Experience Canon defines *how it works*.
> This Interaction Language defines *the reusable grammar* from which every interface is constructed.

---

## Preamble: Grammar Before Application

SHUNYA is not built one screen at a time. It is built from a reusable interaction grammar that every screen inherits.

This document defines that grammar:

- **Primitives** — the atomic interaction units
- **Composition rules** — how primitives combine
- **Spatial language** — where things appear
- **Interaction vocabulary** — what actions are possible
- **Attention language** — when to act and when to be silent
- **Confidence language** — how certainty is expressed
- **Presence language** — how intelligence feels continuous

A frontend engineer unfamiliar with SHUNYA should be able to reconstruct every prototype screen from this document alone — and build entirely new applications — without inventing new interaction patterns.

---

## 1. Interaction Primitives

### 1.1 Primitive Vocabulary

Every interaction in SHUNYA is composed from the following 21 primitives. No new interaction should be invented that does not decompose into these.

| Primitive | Definition | Inverse | When Used |
|-----------|-----------|---------|-----------|
| **Reveal** | Content appears in place, with spatial continuity, at a measured pace | Hide | Loading content, showing a section that was collapsed |
| **Hide** | Content disappears in place, making room for what remains | Reveal | Collapsing a section, removing a notification |
| **Expand** | A region grows to show more detail | Collapse | Opening a knowledge item, showing a sub-section |
| **Collapse** | A region shrinks to show less detail | Expand | Closing an expanded section |
| **Focus** | An element receives keyboard or visual priority | Defocus | Tab navigation, clicking an input |
| **Defocus** | An element releases keyboard or visual priority | Focus | Moving to another element, closing a dialog |
| **Inspect** | Temporarily examine a thing without committing to navigate | Dismiss | Hover preview, peek at a relationship |
| **Navigate** | Move to a different object or workspace | Return | Opening an object, switching workspaces |
| **Select** | Mark an item as chosen for an operation | Deselect | Choosing a list item, activating a tab |
| **Compare** | Place two or more items side by side for evaluation | Uncompare | Reviewing options |
| **Suggest** | Surface an AI-generated recommendation without demanding action | Dismiss | AI Resident showing a suggestion |
| **Explain** | Reveal the reasoning behind an assertion | Unexplain | Clicking "Why?" on a confidence display |
| **Confirm** | Require explicit user acknowledgment before an irreversible action | Cancel | Deleting an object, executing a decision |
| **Undo** | Reverse the last user action | Redo | Reverting a change |
| **Preview** | Show a summary or miniature version of a thing without full open | Unpreview | Hovering over a card, showing a document thumbnail |
| **Promote** | Move an item to higher importance or visibility | Demote | Pinning a recent item, marking a task as priority |
| **Demote** | Move an item to lower importance or visibility | Promote | Archiving a notification, deprioritizing a task |
| **Queue** | Place an item in a pending list for later processing | Dequeue | Saving an AI suggestion for later |
| **Dismiss** | Permanently remove a transient element from view | _(none)_ | Closing a toast, dismissing a suggestion |
| **Escalate** | Move a decision or issue to a higher authority for review | De-escalate | Raising a decision for approval |
| **Defer** | Postpone an action or decision to a later time | Act now | Snoozing a suggestion, delaying a review |

### 1.2 Primitive Constraints

| Constraint | Rule |
|------------|------|
| **No new primitives without council** | Adding a new primitive requires approval from the architectural body that owns the Interaction Language. |
| **Every interaction decomposes** | Any proposed user-facing interaction must be expressible as a sequence of these primitives. If it cannot, either it is not SHUNYA-compliant or a new primitive is needed. |
| **Inverses are paired** | Every primitive that causes a state change has a defined inverse. Orphaned state changes are not permitted. |
| **No ambiguous primitives** | Each primitive has exactly one meaning. "Reveal" is not "Expand." "Suggest" is not "Notify." |

### 1.3 Primitive State Machine

```
Idle ──→ Focus ──→ Select ──→ Confirm ──→ Navigate ──→ (new Idle)
         │
         ├──→ Inspect ──→ Dismiss ──→ Idle
         ├──→ Suggest ──→ Dismiss ──→ Idle
         │              └─→ Expand ──→ Explain ──→ (reads) ──→ Collapse
         ├──→ Preview ──→ Navigate
         └──→ Defer ──→ (timer) ──→ Suggest
```

Every interaction follows one of these paths. No interaction skips states or transitions out of order.

---

## 2. Component Primitives

### 2.1 Atomic Components

These are the irreducible visual elements. Every composite component is built from these.

| Primitive | Purpose | Responsibilities | Allowed Children | Forbidden Children |
|-----------|---------|------------------|------------------|--------------------|
| **TextBlock** | Display text at a specified level | Render text at correct hierarchy level | Text nodes only | Interactive elements, images |
| **Icon** | Represent an object, action, or state symbolically | Convey meaning at a glance | SVG or character glyph | Text, interactive elements |
| **Indicator** | Show state without text (dot, bar, badge) | Communicate presence, status, or count at a glance | Nothing | Text labels |
| **Button** | Trigger a single action | Communicate what happens on activation, handle click/enter/space | TextBlock, Icon | Other buttons, forms |
| **Input** | Accept user text input | Collect text, show placeholder, manage cursor | Text nodes only | Interactive elements |
| **Separator** | Divide visual regions | Create visual hierarchy through spacing | Nothing | Content |

### 2.2 Composite Components

These are the reusable building blocks of every SHUNYA screen.

#### Primary Object

| Property | Definition |
|----------|-----------|
| **Purpose** | The central entity the user is working on. Every workspace has exactly one active Primary Object. |
| **Responsibilities** | Display object identity, surface status, provide entry points to all sections |
| **Children** | ObjectHeader, ExecutiveSummary, SectionTabBar |
| **Interaction Rules** | ObjectHeader is always visible. ExecutiveSummary is always present. SectionTabBar provides access to all section primitives. |
| **Visual Hierarchy** | Highest elevation in the workspace. Primary content area. |
| **Accessibility** | `role="article"`, `aria-label` with object name and type. Tab order begins here. |

#### ObjectHeader

| Property | Definition |
|----------|-----------|
| **Purpose** | Display object identity and provide global actions |
| **Children** | ObjectIcon, ObjectName, Badge (type), Badge (status), ConfidenceIndicator, ObjectMeta, ObjectActions |
| **Interaction Rules** | Fixed (does not scroll). Always visible. Actions appear on hover or by default for primary actions. |
| **Accessibility** | `role="banner"` scoped to the object. Object name is an `h1`. |

#### ExecutiveSummary

| Property | Definition |
|----------|-----------|
| **Purpose** | Provide the minimum information needed to make a decision about this object |
| **Children** | TextBlock (3 lines max), ConfidenceIndicator, SummarySources, SummaryActions |
| **Interaction Rules** | Collapsible. Always renders AI-generated text. Never empty — use static template if AI unavailable. |
| **Accessibility** | `aria-live="polite"`, updated on object state change. |

#### SectionTabBar

| Property | Definition |
|----------|-----------|
| **Purpose** | Navigate between sections of the current object |
| **Children** | SectionTab (one per section) |
| **Interaction Rules** | Scrollable horizontally. Active tab has gold underline indicator. Tabs reveal content panels without navigation. |
| **Accessibility** | `role="tablist"`. Each tab is `role="tab"` with `aria-selected`. Content panels are `role="tabpanel"`. |

#### IdentityPanel

| Property | Definition |
|----------|-----------|
| **Purpose** | Display the canonical definition of an object — what it is, what type, what identifies it |
| **Children** | IdentityGrid (key-value pairs), TagList, CustomFields |
| **Interaction Rules** | Read-only by default. Click to edit individual fields. |
| **Visibility** | First section. Never hidden. |

#### EvidenceBlock

| Property | Definition |
|----------|-----------|
| **Purpose** | Display a single piece of evidence with source attribution and confidence |
| **Children** | EvidenceText, ConfidenceIndicator, SourceLink, Timestamp |
| **Interaction Rules** | Source is always one click away. Multiple evidence blocks compose into a chain. |
| **Accessibility** | `aria-label` includes evidence summary, confidence, and source. |

#### RelationshipGraph

| Property | Definition |
|----------|-----------|
| **Purpose** | Display connections between the current object and other objects in the system |
| **Children** | RelationshipGroup, RelationshipItem |
| **Interaction Rules** | Interactive: click a relationship to inspect or navigate. Groups are collapsible. |
| **Visibility** | Always present. Empty state shows "No relationships yet." |

#### Timeline

| Property | Definition |
|----------|-----------|
| **Purpose** | Display the chronological history of events, changes, and decisions affecting an object |
| **Children** | TimelineDateGroup, TimelineEvent |
| **Interaction Rules** | Newest first. Grouped by date. Filterable and searchable. Virtualized beyond 200 items. |
| **Accessibility** | `aria-label` with event count. Each event is a `listitem` in a `list`. |

#### KnowledgeSurface

| Property | Definition |
|----------|-----------|
| **Purpose** | Display accumulated knowledge, observations, and analysis about an object |
| **Children** | KnowledgeCard (AI-generated, curated, observation variants) |
| **Interaction Rules** | Three sub-categories: AI-generated, Curated, Observations. Each card is expandable. |
| **Accessibility** | `aria-label` includes knowledge type and confidence. |

#### MemorySurface

| Property | Definition |
|----------|-----------|
| **Purpose** | Display what the system remembers about the user's interactions with this object |
| **Children** | RecentActivity, PreviousConversations, LearnedPreferences |
| **Interaction Rules** | Invisible by default. Revealed on user request or AI context handoff. |
| **Accessibility** | `aria-live="polite"` for memory recall events. |

#### ConfidenceIndicator

| Property | Definition |
|----------|-----------|
| **Purpose** | Communicate how certain the system is about an assertion |
| **Children** | ConfidenceBar, ConfidenceLabel, ConfidenceSource |
| **Interaction Rules** | Always visible on AI-sourced content. Shows bar + percentage. Click for breakdown. |
| **Color Rules** | 0.90-1.00: `--color-success` (green). 0.70-0.89: `--color-brand-primary` (gold). 0.50-0.69: `--color-warning` (amber). 0.30-0.49: `--color-error` (orange). 0.00-0.29: `--color-error` (red). |
| **Accessibility** | `role="progressbar"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`. |

#### SuggestionPanel

| Property | Definition |
|----------|-----------|
| **Purpose** | Surface AI-generated recommendations without demanding action |
| **Children** | SuggestionItem (text, confidence, source count, action button) |
| **Interaction Rules** | Show 1-3 suggestions maximum. Each has a confidence indicator. Dismissible individually. |
| **Visibility** | Lives in Context Panel (AI Resident section). Also appears as an object section tab. |
| **Accessibility** | `aria-label` includes suggestion count. Each item is focusable. |

#### ReasoningSurface

| Property | Definition |
|----------|-----------|
| **Purpose** | Show the reasoning chain behind an AI assertion |
| **Children** | ReasoningStep (each step: premise, evidence, conclusion) |
| **Interaction Rules** | Revealed by click on "Why?" from any AI assertion. Depth-adjustable (executive/professional/technical/full evidence). |
| **Accessibility** | `aria-live="polite"` when revealed. Each step is a `listitem`. |

#### ActionSurface

| Property | Definition |
|----------|-----------|
| **Purpose** | Present available actions on the current object or suggestion |
| **Children** | Button (primary, secondary, ghost variants) |
| **Interaction Rules** | 1-3 actions maximum. Primary action is visually distinct. Secondary actions are ghost buttons. |
| **Accessibility** | Tab order matches visual order. |

#### HistorySurface

| Property | Definition |
|----------|-----------|
| **Purpose** | Display the object access and change history |
| **Children** | HistoryGroup (Access history, Change history) |
| **Interaction Rules** | Read-only. Each version is clickable to view diff. |
| **Accessibility** | `aria-label` "History" with entry count. |

#### ContextPanel

| Property | Definition |
|----------|-----------|
| **Purpose** | Provide persistent secondary navigation and context reference while the user works in the content area |
| **Children** | PanelHeader, PanelSection (QuickActions, Relationships, RecentItems, AIResident) |
| **Interaction Rules** | Collapsible (Ctrl+\). Width: 300px default, resizable 240-400px. Always present but can collapse to 40px strip. |
| **Accessibility** | `role="complementary"`, `aria-label="Context panel"`. Skip-link to bypass. |

#### WorkspaceHeader

| Property | Definition |
|----------|-----------|
| **Purpose** | Identify the current workspace and provide workspace-level context |
| **Children** | WorkspaceIcon, WorkspaceName, WorkspaceActions |
| **Interaction Rules** | Fixed at top of content area. Replaced by ObjectHeader when an object is active. |
| **Accessibility** | `role="heading"` at level appropriate to hierarchy (h1 for workspace name at workspace root, h2 when object is active). |

#### NotificationSurface

| Property | Definition |
|----------|-----------|
| **Purpose** | Surface time-relevant information without demanding action |
| **Children** | NotificationItem (icon, message, timestamp, optional action) |
| **Interaction Rules** | Appears and disappears with animation. Auto-dismisses after 4 seconds or on interaction. Stacks vertically. |
| **Accessibility** | `role="status"`, `aria-live="polite"`. |

### 2.3 Primitive Hierarchy

```
Workspace
├── WorkspaceHeader (when no object active)
│   └── Icon + Name + Actions
└── ObjectWorkspace (when object active)
    ├── ObjectHeader
    │   ├── ObjectIcon
    │   ├── ObjectName (h1)
    │   ├── Badge (type)
    │   ├── Badge (status)
    │   ├── ConfidenceIndicator
    │   ├── ObjectMeta
    │   └── ObjectActions
    ├── ExecutiveSummary
    │   ├── TextBlock (3 lines)
    │   ├── ConfidenceIndicator
    │   ├── SummarySources
    │   └── SummaryActions (ActionSurface)
    ├── SectionTabBar
    │   └── SectionTab × N
    └── SectionContent × N
        ├── IdentityPanel
        ├── RelationshipGraph
        ├── Timeline
        ├── KnowledgeSurface
        ├── MemorySurface
        ├── SuggestionPanel
        ├── ReasoningSurface
        ├── ActionSurface
        └── HistorySurface

ContextPanel (Zone 2)
├── PanelHeader
│   ├── ObjectIcon
│   └── ObjectInfo
├── PanelSection (QuickActions)
├── PanelSection (Relationships)
│   └── RelationshipItem × N
├── PanelSection (RecentItems)
└── AIResident (PanelSection)
    ├── SuggestionPanel
    └── ReasoningSurface

GlobalNavBar (Zone 1)
├── Logo
├── WorkspaceSwitcher
├── Breadcrumb
├── SearchBar
├── ThemeToggle
├── NotificationSurface (icon)
└── UserMenu
```

---

## 3. Composition Rules

### 3.1 Deterministic Composition

Composition must always produce the same result for the same inputs. No random or state-dependent layout decisions.

| Rule | Implication |
|------|-------------|
| **Section order is fixed** | Identity → Relationships → Timeline → Knowledge → Tasks → Execution → Metrics → Documents → AI → History. Irrelevant sections are hidden, never reordered. |
| **Tab order follows section order** | Section tabs appear in the same order as sections. Always. |
| **Context panel section order is fixed** | Object info → Quick Actions → Relationships → Recent Items → AI Resident. |
| **Navigation bar element order is fixed** | Logo → Workspace Switcher → Breadcrumb → Search → Theme → Notifications → User. |
| **Workspace content fills the content area** | No centering, no offset. Content begins at the left edge of the content area. |

### 3.2 Nesting Rules

| Composite | Can Contain | Cannot Contain |
|-----------|-------------|----------------|
| Workspace | WorkspaceHeader, ObjectWorkspace, ContextPanel | Another Workspace |
| ObjectWorkspace | ObjectHeader, ExecutiveSummary, SectionTabBar, SectionContent | Another ObjectWorkspace |
| SectionContent | IdentityPanel, RelationshipGraph, Timeline, KnowledgeSurface, SuggestionPanel, ActionSurface, etc. | ObjectHeader, SectionTabBar |
| ContextPanel | PanelHeader, PanelSection (any type) | WorkspaceHeader, SectionTabBar |
| PanelSection | RelationshipItem, SuggestionItem, ActionItem, TextBlock, Icon | Full section content, another PanelSection |

### 3.3 Overlay Rules

| Overlay Type | Position | Max Count | Dismissal |
|-------------|----------|-----------|-----------|
| CommandPalette | Centered, full-screen backdrop | 1 | Escape, click outside, selection |
| Dialog | Centered, modal backdrop | 1 | Escape, Cancel button, action |
| Drawer | Right edge, 400px | 1 | Escape, click outside, Close button |
| BottomSheet (mobile) | Bottom, 60% height | 1 | Swipe down, backdrop tap |
| Tooltip | Above/below trigger element | 1 per trigger | 250ms hover end, Escape |
| Dropdown | Below/above trigger | 1 per trigger | Escape, click outside |
| Toast | Bottom-right, stacked | 5 max | Auto-dismiss 4s, click dismiss |

---

## 4. Spatial Language

### 4.1 Spatial Zones

SHUNYA defines five spatial zones. Every element belongs to exactly one zone.

```
┌───────────────────────────────────────────┐
│  Z1: Global Navigation Bar  (56px)        │  Fixed. Always visible.
├─────────────┬─────────────────────────────┤
│  Z2:        │  Z3: Content Area            │  Z2: Collapsible, 300px
│  Context    │                             │  Z3: Scrollable, flex
│  Panel      │                             │
│  300px      │                             │
│             │                             │
│             │                             │
├─────────────┴─────────────────────────────┤
│  Z4: Command/Overlay Layer  (full-screen)  │  Modal, on demand
├───────────────────────────────────────────┤
│  Z5: Notification Layer  (bottom-right)    │  Transient, auto-dismiss
└───────────────────────────────────────────┘
```

### 4.2 Spatial Rules

| Rule | Description |
|------|-------------|
| **Objects occupy persistent space** | Every object of the same type appears in the same layout position. The user learns where things are and they never move. |
| **Nothing visually teleports** | Every element that changes position animates with spatial continuity. Elements never appear or disappear without a transition. |
| **Z2 and Z3 share horizontal space** | When Z2 is open, Z3 shrinks. When Z2 is collapsed, Z3 fills the width. Never overlapping. |
| **Overlays obscure, never shift** | Dialogs, drawers, and palettes appear above the content. The content beneath does not shift or resize. |
| **Notifications do not steal focus** | Toasts appear in Z5. They do not interfere with keyboard focus or mouse interaction. |

### 4.3 Persistent vs. Temporary Regions

| Region | Persistence | Behavior |
|--------|-------------|----------|
| **Z1 (Global Nav)** | Permanent | Never scrolls away. Never hides. Same on every workspace. |
| **Z2 (Context Panel)** | Semi-permanent | Default open. Collapsible. Remembers state per user. |
| **Z3 Header (Object Header)** | Semi-permanent | Fixed within scroll context. Scrolls away only when content area scrolls past a threshold. |
| **Z3 Summary** | Permanent in workspace | Always visible when an object is active. Collapsible. |
| **Z3 Section Tabs** | Semi-permanent | Sticks below header. Scrolls with content. |
| **Z3 Section Content** | Scrollable | The only region that scrolls freely. |
| **Z4 (Overlay)** | Temporary | Appears on demand, disappears on completion or dismissal. |
| **Z5 (Notification)** | Transient | Appears automatically, disappears after 4 seconds. |

---

## 5. Information Hierarchy

### 5.1 Priority Levels

Every piece of content in SHUNYA has a priority level. The interface always reveals information in this order:

| Level | Definition | Visual Treatment | Time to Surface |
|-------|-----------|-----------------|-----------------|
| **Critical** | Requires immediate action or awareness | High contrast, prominent position, color-coded badge | Always visible |
| **Primary** | Directly supports the current decision or task | Normal weight, full opacity, in primary view | Always visible |
| **Supporting** | Provides context or background for Primary content | Secondary text color, smaller size | One interaction away |
| **Reference** | Reference material, historical data, documentation | Tertiary text color, minimal size | Expandable section |
| **Historical** | Past states, previous versions, archival data | Muted, timestamped | Explicit request required |
| **Archived** | No longer relevant but preserved for audit | Grayed out, moved to archive section | Search or explicit navigation |

### 5.2 Progressive Disclosure Canon

```
Step 1: Show Critical + Primary only (executive summary, status, key actions)
Step 2: User expands → Show Supporting (relationships, timeline overview)
Step 3: User expands further → Show Reference (full data, knowledge items)
Step 4: User requests → Show Historical (change history, previous versions)
Step 5: User searches → Show Archived (old data, audit trail)
```

The interface never skips levels. The user always controls depth.

### 5.3 Priority Decay

Information priority decays over time without user interaction:

| Age | New Priority |
|-----|-------------|
| < 1 hour | Current |
| 1–24 hours | Slight demotion (still Primary, less prominent) |
| 1–7 days | Demoted to Supporting |
| 7–30 days | Demoted to Reference |
| 30–90 days | Demoted to Historical |
| > 90 days | Archived (searchable, not visible) |

---

## 6. Attention Language

### 6.1 Attention States

Every interaction primitive operates within an attention context. The attention state determines which primitives may fire.

| State | Definition | Permitted Primitives | Prohibited Primitives |
|-------|-----------|---------------------|----------------------|
| **Silent** | Default state. The system is present but not communicating. | Focus, Inspect (user-initiated only) | Suggest, Notify, Queue |
| **Attentive** | The system has relevant information but is waiting for an appropriate moment. | Focus, Inspect, Suggest (stored, not displayed) | Notify |
| **Suggestive** | The system has high-confidence information to share. | Focus, Inspect, Suggest, Preview | Notify, Confirm |
| **Conversational** | The user has engaged the system. | All primitives | _(none)_ |
| **Alerting** | Time-critical information requires user attention. | Suggest, Notify, Confirm | Defer (for this specific item only) |

### 6.2 State Transitions

```
Silent ──(AI detects relevance, confidence >0.80)──▶ Attentive
Attentive ──(user becomes available, 5s idle after task)──▶ Suggestive
Suggestive ──(user clicks suggestion or opens AI panel)──▶ Conversational
Conversational ──(user dismisses, 30s no interaction)──▶ Silent
Suggestive ──(user ignores, 30s)──▶ Attentive
Attentive ──(state change makes suggestion irrelevant)──▶ Silent
Alerting ──(user acknowledges)──▶ Silent
```

### 6.3 Interruption Rules

| Condition | Action | Rationale |
|-----------|--------|-----------|
| User is in Silent state | No interruption. All primitives are user-initiated. | The user has not invited communication. |
| User is typing or editing | Remain in Silent state. Queue suggestions. | Active creation or editing must not be interrupted. |
| User is reading (slow scrolling, long page dwell) | Suggestive state only. No Notify. | Reading requires sustained focus. Interruptions reset comprehension. |
| User is scanning (rapid object switches) | Remain in Attentive. Defer all suggestions. | The user is exploring. Suggestions would be contextual noise. |
| User has been idle >5 minutes | Suggestive state. One suggestion maximum. | Brief re-engagement signal. Not an interruption. |
| User has dismissed a specific suggestion twice | Suppress that suggestion permanently for this object. | Continued suggestions of the same thing are harassment. |
| Confidence for all suggestions <0.50 | Remain in Silent. | Low-confidence suggestions erode trust. |

---

## 7. Confidence Language

### 7.1 Confidence Scale (Visual Scale)

```css
--confidence-very-high: #22C55E;  /* 0.90–1.00 */
--confidence-high:      #D4A843;  /* 0.70–0.89 */
--confidence-moderate:  #F59E0B;  /* 0.50–0.69 */
--confidence-low:       #EF4444;  /* 0.30–0.49 */
--confidence-very-low:  #DC2626;  /* 0.00–0.29 */
```

### 6.2 Representation

| Confidence Value | Bar Color | Label | Language Prefix |
|-----------------|-----------|-------|-----------------|
| 0.90–1.00 | Green | High confidence | Direct statement |
| 0.70–0.89 | Gold | Good confidence | Statement + confidence indicator |
| 0.50–0.69 | Amber | Moderate confidence | "Based on what I know…" |
| 0.30–0.49 | Orange | Low confidence | "I cannot be certain. Here is what I found:" |
| 0.00–0.29 | Red | Very low confidence | "Insufficient evidence." |

### 6.3 Confidence Display Rules

| Rule | Implementation |
|------|----------------|
| **Always visible** | Every AI-sourced assertion displays its confidence. No exceptions. |
| **Per-assertion** | Composite or averaged confidence scores are never used. Each claim has its own indicator. |
| **Click for breakdown** | Clicking the indicator reveals: factors, source quality, source quantity, model certainty. |
| **Not for human-sourced data** | Human-entered data does not display confidence (human confidence is presumed). |
| **Confidence decays** | Confidence older than 90 days shows a "historical" label. Effective confidence reduces by half-life formula. |

### 6.4 Uncertainty Display

| Situation | Display |
|-----------|---------|
| Single source, high confidence | Direct statement with source link |
| Multiple sources, consistent | Statement with unified confidence (min of source confidences) |
| Multiple sources, conflicting | "N sources support X. M sources support Y." Separate confidence per position. |
| Single source, low confidence | "Based on limited data (1 source, 0.45 confidence)." |
| No data available | "Insufficient evidence for a conclusion." No confidence bar shown. |
| AI model uncertainty | Bar at appropriate level + "Model confidence is limited for this type of query." |

---

## 8. Presence Language

### 7.1 Presence States

| State | Visual | Primitives Active | Duration |
|-------|--------|-------------------|----------|
| **Arriving** | Content enters workspace (workspace-enter animation, 400ms) | Reveal | 400ms |
| **Present** | Content fully rendered, system ready | All user-initiated | Indefinite |
| **Waiting** | Gold dot visible, no AI text | Focus, Inspect | Indefinite |
| **Thinking** | Gold dot glows steadily (not animated) | Focus, Inspect | <2s (processing is done before display) |
| **Suggesting** | Gold dot + subtle glow, suggestions visible | Suggest, Preview | Until dismissed or acted upon |
| **Completing** | Confirmation toast (4s) | Notify | 4s |
| **Erroring** | Error state in relevant region | Notify (polite) | Until dismissed |
| **Uncertain** | Confidence indicator at appropriate level | Explain (available on click) | Until dismissed |
| **Absent** | AI Resident collapsed, no dot | _(none)_ | Indefinite (user preference) |

### 7.2 Presence Continuity

| Rule | Implementation |
|------|----------------|
| **Presence is continuous** | Even when no AI content is visible, the system is present. The gold dot in the AI Resident header is always there (unless user has collapsed it). |
| **No "connection lost" messages** | If the system goes offline, it continues to function with cached data. No error bars or disconnection indicators. |
| **No "AI is thinking" indicators** | Processing completes before display. The user never sees intermediate states. |
| **Memory feels continuous** | Conversations persist. State restores. The system remembers where the user left off — across sessions. |

---

## 9. Motion Language

### 8.1 Motion Primitives

| Primitive | Duration | Curve | Purpose |
|-----------|----------|-------|---------|
| **Appear** | 200ms | ease-out | Element enters the page (should be rare — most content is already present) |
| **Disappear** | 150ms | ease-in | Element leaves the page |
| **SlideIn** | 300ms | ease-out | Panel or drawer enters from an edge |
| **SlideOut** | 200ms | ease-in | Panel or drawer leaves to an edge |
| **Expand** | 300ms | ease-out | Region grows to reveal content |
| **Collapse** | 200ms | ease-in | Region shrinks to hide content |
| **CrossFade** | 200ms | ease-out | One element replaces another (tab content, section content) |
| **Stagger** | 50ms/item | ease-out | Sequential appearance of siblings (use sparingly, max 5 items) |
| **Pulse** | 1.5s cycle | ease-in-out | Loading skeleton placeholder |
| **Glow** | Steady state | none | AI gold dot presence indicator (never animated, always steady) |

### 8.2 Combined Motion Sequences

| Sequence | Duration | Steps |
|----------|----------|-------|
| Workspace enter | 400ms | 1. Content slides in from right (300ms). 2. Header fades in (100ms offset). |
| Object open | 300ms | 1. Header slides down (200ms). 2. Summary fades in (300ms, 100ms delay). 3. Content sections stagger (50ms each, max 200ms). |
| Panel open | 300ms | 1. Panel slides from edge (300ms). 2. Content inside appears (0ms — no fade, content is already in the panel). |
| Panel close | 200ms | Panel slides to edge (200ms). Content disappears with panel. |
| Dialog open | 300ms | 1. Backdrop fades (200ms). 2. Dialog scales from 0.95 to 1.0 + fades (300ms, 50ms delay). |
| Section tab switch | 200ms | Cross-fade between old and new content (150ms old out, 50ms gap, 200ms new in). |

### 8.3 Motion Constraints

| Constraint | Rule |
|------------|------|
| **No animation without purpose** | Every animation must answer: "What spatial relationship does this communicate?" |
| **No flashing** | Any element that changes opacity more than once in 3 seconds is flashing. Prohibited. |
| **No parallax, scroll-triggered reveals, or decorative entrance animations** | Content enters once and stays. No scroll-driven animation. |
| **Maximum animation duration: 400ms** | No animation may last longer than 400ms in any direction. |
| **Animation duration respects reduced motion** | `@media (prefers-reduced-motion: reduce)` reduces all durations to 0.01ms. |
| **No animation on status indicators** | Confidence bars, status badges, and progress bars change instantly. No transition. |
| **Opening is slower than closing** | Open: 300ms. Close: 200ms. This creates a sense of returning to stillness. |

---

## 10. Design Token Hierarchy

The complete token system is documented in `16_design_system_foundation.md`. The Interaction Language defines how tokens are used, not their values.

### 9.1 Token Typology

```
Global Tokens (inherited by every component)
├── Color Tokens (brand, surface, text, border, semantic)
├── Typography Tokens (family, size, weight, line-height)
├── Spacing Tokens (base scale, semantic spacing)
├── Elevation Tokens (shadow, z-index)
├── Radius Tokens (border-radius scale)
└── Motion Tokens (duration, easing)

Component Tokens (per component, reference global tokens)
├── Button Tokens (padding, font-size, border-radius, hover, active)
├── Card Tokens (padding, gap, background, border)
└── ...
```

### 9.2 Token Usage Rules

| Rule | Implementation |
|------|----------------|
| **No hardcoded values** | Every visual property references a token. Zero exceptions. |
| **Components reference semantic tokens** | `--color-surface-primary`, not `--color-gray-900`. |
| **Global tokens never change per component** | A global token has one value. Components that need variation use component-level tokens that reference global tokens. |
| **Token names are stable** | Once published, a token name never changes. Deprecated tokens are marked `--deprecated-*` for two release cycles before removal. |

---

## 11. Accessibility Language

### 10.1 Inherited Accessibility

Every primitive inherits accessibility behaviour. No component-level accessibility work is needed for standard usage — only for novel compositions.

| Primitive | Role | Keyboard | ARIA |
|-----------|------|----------|------|
| TextBlock | (implicit) | Tab skipped | — |
| Icon | `img` with `aria-hidden="true"` | Tab skipped | `aria-label` when meaning is not conveyed by visible text |
| Indicator | `img` or `status` | Tab skipped | `aria-label` describing the state |
| Button | `button` | Enter/Space to activate | `aria-disabled`, `aria-expanded`, `aria-label` |
| Input | `textbox` | Tab to focus, type to enter | `aria-label`, `aria-describedby` |
| TabBar | `tablist` | Arrow keys to navigate tabs | `aria-orientation` |
| Tab | `tab` | Enter/Space to select | `aria-selected`, `aria-controls` |
| TabPanel | `tabpanel` | Content inside is tabbable | `aria-labelledby` |
| Dialog | `dialog` | Tab trap, Escape to close | `aria-modal`, `aria-labelledby` |
| Panel | `complementary` | Tab into content | `aria-label` |
| Toast | `status` | Auto-dismiss, no focus steal | `aria-live="polite"` |

### 10.2 Focus Ring and Focus Order

| Rule | Implementation |
|------|----------------|
| **Z1 → Z2 → Z3** | Tab order follows visual order: Global Nav → Context Panel → Content Area. |
| **Within each zone, top to bottom** | Tab moves through elements in visual order (top to bottom, left to right). |
| **Modal traps focus** | When a dialog or overlay is open, Tab cycles within it. Focus returns to the trigger element on close. |
| **No invisible elements in tab order** | Elements with `display: none` or `visibility: hidden` are not in the tab order. |
| **Skip link** | First focusable element is a skip-link to jump to the main content area. |

---

## 12. Multifaceted Validation

### 11.1 Business-Agnostic Verification

The Interaction Language has been validated against the following domains to confirm no domain assumptions are embedded:

| Domain | Relevant Primitives | Assumptions Verified |
|--------|-------------------|---------------------|
| Knowledge Management | KnowledgeSurface, Timeline, RelationshipGraph | No document type assumptions |
| Project Management | Timeline, ActionSurface, ExecutiveSummary | No methodology assumptions |
| Finance | ConfidenceIndicator, EvidenceBlock, ExecutiveSummary | No currency or ledger assumptions |
| Healthcare | EvidenceBlock, Timeline, MemorySurface | No patient or diagnosis assumptions |
| Legal | EvidenceBlock, Timeline, ReasoningSurface | No case or jurisdiction assumptions |
| Education | KnowledgeSurface, Timeline, RelationshipGraph | No student or course assumptions |
| Manufacturing | Timeline, ActionSurface, RelationshipGraph | No BOM or supply chain assumptions |
| CRM | RelationshipGraph, Timeline, IdentityPanel | No lead or account assumptions |
| Government | EvidenceBlock, Timeline, ConfidenceIndicator | No regulation or compliance assumptions |
| Hospitality | Timeline, ActionSurface, RelationshipGraph | No booking or reservation assumptions |
| Travel | RelationshipGraph, Timeline, ExecutiveSummary | No itinerary or destination assumptions |
| Technology | KnowledgeSurface, ActionSurface, SuggestionPanel | No product or sprint assumptions |

**Conclusion:** The Interaction Language is domain-independent. All domain-specific terms are configuration, not primitives.

### 11.2 Prototype Reconstruction

Every screen in the Phase X2 prototype can be reconstructed entirely from the primitives, composition rules, and spatial language documented here:

| Prototype Screen | Primitives Used |
|-----------------|-----------------|
| Home workspace | WorkspaceHeader, NotificationSurface (change summary), Card objects composed from Icon + TextBlock + Indicator |
| Object workspace | ObjectHeader, ExecutiveSummary, SectionTabBar, IdentityPanel, RelationshipGraph, Timeline, KnowledgeSurface, SuggestionPanel, ReasoningSurface, ActionSurface, HistorySurface |
| Context Panel | ContextPanel → PanelHeader + PanelSection (QuickActions) + PanelSection (Relationships) + PanelSection (RecentItems) + AIResident |
| Command palette | CommandPalette (overlay primitive from composition rules) composed from Input + Icon + TextBlock |
| Toast | NotificationSurface (Z5, transient) |
| All workspace shells | WorkspaceHeader + placeholder text |

**No application-specific components were required.** Every prototype element derives from documented primitives.

---

## 13. Production Readiness

### 12.1 What May Be Customized

| Element | Customization Scope |
|---------|-------------------|
| Object type icons | Per organization, per object type |
| Color scheme (light mode) | Tonal variation only (hue shift <15 degrees, saturation shift <10%) |
| Workspace icons | Per organization |
| Brand name and logo | Per deployment |
| Default section order | Per user preference |
| Context panel width | Per user (240-400px range) |

### 12.2 What May Never Change

| Element | Rationale |
|---------|-----------|
| Three-zone layout | Fundamental architecture of SHUNYA |
| Section order (canonical) | Consistency across all objects |
| Primitive definitions | The interaction grammar is immutable |
| Confidence display rules | Transparency is a Human Principle |
| Attention state machine | Respecting user attention is non-negotiable |
| Motion curves and durations | Consistency of spatial experience |
| Typography hierarchy | Reading comfort and executive readability |
| Token hierarchy | Design system integrity |

### 12.3 How New Components Are Created

1. Verify the component is expressible using existing primitives. If it is, build from primitives.
2. If a new primitive is needed, submit for architectural review with: purpose, responsibilities, allowed children, forbidden children, interaction rules, visual hierarchy, accessibility expectations.
3. If no new primitive is needed, compose from existing primitives and document the composition.
4. All new components must pass the 7-question test (Human Principles §13).

### 12.4 How New Primitives Are Approved

| Gate | Criteria |
|------|----------|
| **Architectural review** | Does this decompose the interaction space in a way no existing primitive covers? |
| **Necessity** | Can the same outcome be achieved by composing existing primitives? |
| **Consistency** | Does this primitive follow the naming and behavioral conventions of existing primitives? |
| **Accessibility** | Can this primitive be made keyboard-accessible and screen-reader-accessible? |
| **Motion** | Does this primitive have defined entry, exit, and reduced-motion behaviours? |

### 12.5 How Tokens Evolve

| Action | Policy |
|--------|--------|
| **New token** | Added to the end of the token category. Never inserted in the middle (would renumber existing tokens). |
| **Deprecated token** | Marked with `--deprecated-` prefix. Support maintained for 2 release cycles. |
| **Removed token** | Removed only after 2 release cycles of deprecation. Listed in migration notes. |
| **Changed value** | Never. A changed value is a new token with a new name. Old tokens are deprecated. |

### 12.6 How Interaction Consistency Is Maintained

| Practice | Frequency | Owner |
|----------|-----------|-------|
| **Primitive audit** | Quarterly | Experience architecture team |
| **Token review** | Per release | Design system team |
| **Accessibility regression** | Every commit | CI pipeline |
| **Interaction consistency review** | Per feature | Frontend engineering + design review |
| **Validation against canon** | Per major release | Architecture review board |

---

## Canonical Status

This Interaction Language is the permanent architectural contract between:

- **Human Principles** (the why)
- **Presence Canon** (the feel)
- **Experience Canon** (the how)
- **Design System Foundation** (the tokens and contracts)
- **Frontend Engineering** (the implementation)

Every future SHUNYA interface inherits this language. Nothing should be invented per application. If a new screen requires an interaction not covered by this document, the deficiency is in the screen design, not in the language.

---

*Canonical reference — Phase X2A. July 2026.*