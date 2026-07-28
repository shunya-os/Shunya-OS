# Experience Canon — Object-First, Workspace-First

> **Canonical Document · Phase C1**
> **Status: CANONICAL — Implementation-Independent UX Specification**
> **Version: 2.0**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [UX Philosophy](#2-ux-philosophy)
3. [Design Constants](#3-design-constants)
4. [12 Experience Principles](#4-experience-principles)
   - [4.1 Object-First Navigation](#41-object-first-navigation)
   - [4.2 Workspace-First Interaction](#42-workspace-first-interaction)
   - [4.3 Relationship-First Exploration](#43-relationship-first-exploration)
   - [4.4 AI Collaboration Model](#44-ai-collaboration-model)
   - [4.5 Attention Management](#45-attention-management)
   - [4.6 Cognitive Load Management](#46-cognitive-load-management)
   - [4.7 Context Preservation](#47-context-preservation)
   - [4.8 Progressive Disclosure](#48-progressive-disclosure)
   - [4.9 Founder Experience](#49-founder-experience)
   - [4.10 Executive Experience](#410-executive-experience)
   - [4.11 Team Experience](#411-team-experience)
   - [4.12 Mobile Philosophy](#412-mobile-philosophy)
5. [Responsive Philosophy](#5-responsive-philosophy)
6. [Accessibility](#6-accessibility)
7. [Future Extensibility](#7-future-extensibility)
8. [Relationship to Other Canonical Documents](#8-relationship-to-other-canonical-documents)

---

## 1. Purpose

This document defines how SHUNYA *feels* to use. It translates the Constitutional principle of **"Calm Before Complexity"** (02 §Article 9) and the **object-first architecture** of the Business Canon (03) and Universal Object Protocol (04) into concrete UX principles.

**No implementation mockups.** This defines the philosophy, not the pixels. The experience is the human-facing surface of the object model — every screen, interaction, and flow presents **Objects** from the Business Canon, surfaced through **Actions** from the Universal Object Protocol, within **Workspaces** as the primary container.

---

## 2. UX Philosophy

### 2.1 Core Statement

**SHUNYA reduces cognitive load. Every pixel, every word, every interaction exists to make the human's mental task easier.**

The entire experience revolves around a single question: *What object does the human need to see, and what action do they need to take?*

### 2.2 The Cognitive Load Test

Every design decision is measured against one question:

> **Does this reduce or increase cognitive load?**

If a feature, animation, color, layout, or word increases cognitive load, it must be simplified or removed. The object-first model reduces cognitive load by making the system's mental model match the human's mental model — objects with relationships, not pages with hierarchies.

### 2.3 Beauty Is Consequence, Not Objective

Beauty in SHUNYA is the natural result of clarity, spaciousness, and purpose — not a design goal itself. A beautiful SHUNYA interface is one that feels effortless to use. When the system presents objects clearly, with their relationships visible and their actions accessible, the visual result is inherently beautiful.

### 2.4 Design Values

| Value | Description | Manifests As |
|-------|-------------|-------------|
| **Calm** | The system is quiet until spoken to | Spacious layouts, no noise, object detail hidden until needed |
| **Clear** | Every element communicates its purpose | Objects are self-describing, actions are unambiguous |
| **Kind** | The system is patient and forgiving | Generous hit targets, undo everywhere, object state is never lost |
| **Capable** | The system does more than expected | Progressive disclosure, power features on objects, AI collaboration |
| **Consistent** | Patterns are reliable across surfaces | Every object follows the Universal Object Protocol, every action is where expected |
| **Personal** | Feels like it was made for you | Workspace adapts to your objects, remembers your context |

---

## 3. Design Constants

These constants are preserved across all experience surfaces and persona experiences. They are the visual and structural invariants of the SHUNYA experience.

### 3.1 The 70/20/10 Rule

| Proportion | Content | Purpose |
|-----------|---------|---------|
| **70% whitespace** | Empty space, margins, padding | Visual breathing room, focus on the object |
| **20% content** | Object data, context, relationships | What the human needs to know about the object |
| **10% controls** | Actions, buttons, inputs | What the human can do to/with the object |

The 70/20/10 rule applies within every object view, every workspace, every panel. The object is the center of attention; whitespace frames it; controls are secondary.

### 3.2 Visual Palette (Warm Minimalism)

| Role | Color | Hex |
|------|-------|-----|
| **Surface** | Paper white | `#fbfaf8` |
| **Primary text** | Near black | `#1a1c1d` |
| **Secondary text** | Muted | `rgba(26,28,29,0.5)` |
| **Accent** | Gold | `#a4865f` |
| **Border** | Subtle | `rgba(0,0,0,0.06)` |
| **Error** | Soft red | `#d1453b` |
| **Success** | Soft green | `#2e7d32` |
| **Link** | Blue | `#1a73e8` |

### 3.3 Typography

| Role | Font | Characteristics |
|------|------|-----------------|
| **Headings** | Playfair Display | Serif, warm, elegant |
| **Body** | Inter | Sans-serif, clean, readable |
| **Mono** | JetBrains Mono | Code, data, technical |
| **Scale** | 10/12/14/16/20/28/36/48px | — |

### 3.4 Spacing

| Name | Size | Used For |
|------|------|----------|
| **XS** | 4px | Tight spacing, object metadata |
| **SM** | 8px | Component internal, relationship labels |
| **MD** | 16px | Between components, object cards |
| **LG** | 32px | Section spacing, workspace sections |
| **XL** | 64px | Page margins, workspace boundaries |
| **XXL** | 96px | Hero spacing, object detail start |

### 3.5 Content Design

| Principle | Description |
|-----------|-------------|
| **Short** | Say what needs saying, nothing more |
| **Clear** | Use plain language, avoid jargon |
| **Active** | Use active voice |
| **Kind** | Assume good intent, offer help not blame |
| **Consistent** | Same term means same thing everywhere |

**Error messages:**

Good error messages tell the human what happened, what they can do about it, in plain language, with a specific action. Never blame the human.

*Example:* "Couldn't save the document. Your internet connection might be down. [Try again] or [Save offline]"

---

## 4. Experience Principles

### 4.1 Object-First Navigation

**Principle:** Navigation is organized around **objects**, not pages. The human navigates by identifying, selecting, and acting on objects from the Business Canon (03).

#### 4.1.1 What This Means

In a page-based system, the human thinks "I need to go to the Settings page." In an object-first system, the human thinks "I need to find the Workspace object, then find the member object, then adjust their permission."

The navigation model reflects the Universal Object Protocol hierarchy:

```
Objects (the universe of everything)
  │
  ├── My Objects (recent, pinned, owned by me)
  │       ├── Object: "Project Alpha" (Workspace object)
  │       │       ├── Contains: Task objects, Decision objects, Document objects
  │       │       ├── Relates to: Human objects (members), Organization object
  │       │       └── Actions: Create, Edit, Archive, Share
  │       │
  │       ├── Object: "Client Beta" (Organization object)
  │       │       └── ...
  │       │
  │       └── Object: "Personal" (Workspace object)
  │               └── ...
  │
  ├── Object Types (browse by type — Identity, Human, Organization, Workspace,
  │   │              Relationship, Conversation, Commitment, Task, Event,
  │   │              Observation, Evidence, Document, FinancialObject, Decision,
  │   │              Workflow, Memory, Knowledge, Outcome)
  │
  └── Relationships (follow links between objects)
```

#### 4.1.2 Navigation Principles

| Principle | Description |
|-----------|-------------|
| **Object-centered** | Every navigation target is an object, identified by its type and identity |
| **Flat** | Never more than 3 object hops from the current object to any related object |
| **Contextual** | Navigation adapts to the current object type and its available relationships |
| **Persistent** | The primary object search (Cmd+K) is always accessible |
| **Spatial** | Position in the object graph is always clear — what object you're viewing, what relationships it has |
| **Searchable** | Object search is faster than browsing — find any object by name, type, or relationship |

#### 4.1.3 Primary Actions

The primary actions are always visible and are object-relative:

| Action | Trigger | Behavior |
|--------|---------|----------|
| **Search Objects** | Cmd+K | Find any object by identity, type, relationship, or content |
| **Create Object** | Object-type contextual | Create a new object in the current workspace context |
| **AI Collaboration** | Cmd+Shift+K | Summon AI collaborator in the context of the current object |
| **Notifications** | Object-specific | Events and changes to objects you follow |
| **Profile** | Personal object | Your own Human object — settings and preferences |

#### 4.1.4 Object Type Navigation

The 18 canonical object types (03 §2) each have a consistent navigation surface:

- **Identity** — Search, resolve, merge, verify
- **Human** — Profile, activity, memberships, decisions
- **Organization** — Structure, members, relationships, authority
- **Workspace** — Content, members, settings, state
- **Relationship** — Graph, strength, type, evidence
- **Conversation** — Messages, participants, decisions, state
- **Commitment** — Promises, deadlines, status, fulfillment
- **Task** — Assignments, dependencies, status, timeline
- **Event** — Occurrences, participants, outcomes, evidence
- **Observation** — Facts, sources, confidence, evidence
- **Evidence** — Attachments, verification, chain of custody
- **Document** — Content, versions, collaborators, references
- **FinancialObject** — Transactions, balances, commitments, reconciliation
- **Decision** — Context, options, reasoning, outcome, evidence
- **Workflow** — Stages, state, actors, transitions, history
- **Memory** — Stored context, retrieval, relevance, decay
- **Knowledge** — Synthesized understanding, sources, confidence
- **Outcome** — Results, measurements, learning, relationships

---

### 4.2 Workspace-First Interaction

**Principle:** The **Workspace** is the primary interaction container. Every human action occurs within a workspace — a bounded context for objects, relationships, and work.

#### 4.2.1 What This Means

The workspace is not a "page" or a "folder." It is a scoped object ecosystem. When a human enters a workspace, they are entering a context where a specific set of objects, relationships, and participants are active. The workspace defines:

- **Scope** — which objects are visible and relevant
- **Membership** — which humans and identities participate
- **Persistence** — context and state persist across sessions
- **Permissions** — what actions are available to whom
- **Focus** — the workspace filters the universe of objects to what matters

#### 4.2.2 Workspace Types

| Type | Purpose | Object Scope |
|------|---------|-------------|
| **Project** | Bounded work | Task, Decision, Document, Event, Human, Commitment, Observation, Outcome |
| **Conversation** | Communication | Conversation, Decision, Human, Document, Evidence, Commitment |
| **Knowledge** | Understanding | Knowledge, Observation, Evidence, Document, Memory, Outcome |
| **Dashboard** | Awareness | Event, Outcome, Observation, Decision, Workflow, FinancialObject |
| **Personal** | Private self | Memory, Document, Decision, Observation, Knowledge, Task |

#### 4.2.3 Workspace Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  Object Bar (always present, workspace-relative)                  │
│  [Workspace Name] · [Current Object Type] · [Object Identity]     │
│  [Search Objects...] [Create] [AI] [Notif] [Profile]             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┬────────────────────────────────────┬──────────────┐│
│  │ Object   │      Object Detail                  │  Relationship│
│  │ Browser  │     (primary area, 70/20/10)        │  Panel       │
│  │ (opt.)   │                                      │  (collaps.)  │
│  │          │  The object itself.                  │              │
│  │ Related  │  Whitespace frames it.               │ Connected    │
│  │ objects  │  Content describes it.               │ objects      │
│  │          │  Controls act on it.                 │              │
│  └──────────┴────────────────────────────────────┴──────────────┘│
│                                                                   │
│  Object Breadcrumb: [Workspace] > [Object Type] > [Object Name]   │
└──────────────────────────────────────────────────────────────────┘
```

#### 4.2.4 Workspace Principles

| Principle | Description |
|-----------|-------------|
| **Bounded** | A workspace has clear boundaries — what's in it and what's not |
| **Persistent** | Workspace state survives sessions; returning is like resuming |
| **Shareable** | Workspaces can be shared with other humans, each with their own permissions |
| **Composable** | Objects can appear in multiple workspaces simultaneously |
| **Navigable** | Workspaces are objects themselves — findable, searchable, organizable |

---

### 4.3 Relationship-First Exploration

**Principle:** Humans navigate by following **relationships between objects**, not by traversing a menu hierarchy. The object graph is the navigation map.

#### 4.3.1 What This Means

Every object carries its relationships explicitly (04 §6). When viewing any object, the human can see what it connects to, how, and with what strength or type. Navigation is a matter of following a relationship from one object to another:

```
Object: Decision "Approve Q3 Budget"
    │
    ├── relates to → Workspace "Q3 Planning"
    ├── involves → Human "Alice" (author), Human "Bob" (approver)
    ├── references → Document "Q3 Budget Proposal"
    ├── produces → Commitment "Allocate $500K to Engineering"
    ├── depends on → Decision "Hire 3 Engineers" (precedent)
    ├── supported by → Evidence "Revenue Forecast Q3"
    └── results in → Outcome "Budget Approved" (actual)
```

Each relationship is a navigable link. The human clicks on any relationship to view the related object, then follows *its* relationships outward. This creates a natural, human-explorable graph.

#### 4.3.2 Relationship Navigation Principles

| Principle | Description |
|-----------|-------------|
| **Always visible** | Every object view shows its direct relationships |
| **Typed** | Relationships have types (relates_to, involves, references, produces, depends_on, etc.) |
| **Bidirectional** | If A relates to B, B's view shows the relationship back to A |
| **Weighted** | Relationship strength or relevance is indicated when meaningful |
| **Filterable** | The human can filter relationships by type, direction, or recency |
| **Explorable** | Following a relationship is always one click — no modal, no page load |

#### 4.3.3 The Object Graph

The complete object graph is the union of all objects and all their relationships. The human never sees the entire graph (too large) but always sees their local neighborhood. The experience supports:

- **Star exploration** — start at one object, follow relationships outward
- **Path finding** — how is object A connected to object B?
- **Cluster visualization** — what objects are densely connected around a topic?
- **Timeline traversal** — how did relationships evolve over time?

---

### 4.4 AI Collaboration Model

**Principle:** The AI collaborator is a peer within the workspace, operating on the same objects with the same protocol. AI interaction is object-contextual, not chat-modal.

See **07_ai_canon.md** for the complete AI interaction specification. This section defines only the experience-level principles.

#### 4.4.1 AI Presence

AI in SHUNYA is:
- **Object-contextual** — the AI always knows what object you're viewing and what actions are available
- **Present, not intrusive** — available when needed, quiet when not, visible as a collaborator in the workspace
- **Discreet** — shown as suggestion, not interruption; confidence expressed naturally
- **Tool-using, not answer-giving** — the AI operates on objects through the Universal Object Protocol, not through free-form chat

#### 4.4.2 AI Interface Patterns

| Pattern | Description |
|---------|-------------|
| **AI Button** | Summon AI in the context of the current object |
| **AI Sidebar** | AI conversation alongside the object — shows the object, the AI's understanding, and proposed actions |
| **Inline Suggestion** | AI suggestion within object content — subtle, dismissible, always actionable |
| **AI Notification** | AI-initiated alert about object state changes — quiet, actionable |
| **Object Action Proposal** | AI proposes an action on the current object (e.g., "I notice this Decision is missing an evidence link. Add one?") |

#### 4.4.3 AI Communication Rules

- Always framed as **suggestion**, never as directive
- Confidence expressed naturally ("I'm fairly sure", "I'm not certain")
- Evidence shown on request, not by default
- Technical details available but not prominent
- Every AI action is performed through the Universal Object Protocol — the AI calls the same `create`, `update`, `relate`, `archive` actions as the human

---

### 4.5 Attention Management

**Principle:** The system manages what the human should focus on, not by shouting louder, but by arranging the workspace to make the right object salient.

#### 4.5.1 What This Means

Attention is a finite resource. SHUNYA does not compete for attention — it respects it. The system directs attention through:

| Mechanism | Description |
|-----------|-------------|
| **Spatial priority** | The most important object occupies the most visible position |
| **Whitespace framing** | The object worth focusing on has the most breathing room around it |
| **Temporal priority** | Time-sensitive objects are surfaced; static objects recede |
| **Relationship proximity** | Related objects are visually closer than unrelated ones |
| **State indication** | Objects with changed state are subtly indicated, not loudly announced |

#### 4.5.2 Attention Rules

1. **One primary object at a time** — the workspace has one focal object. Everything else is secondary.
2. **No modal notifications** — notifications appear in a dedicated space, never as interruptions.
3. **Badge counts are minimal** — badges indicate truly new information, not every state change.
4. **AI suggestions are quiet** — the AI proposes without demanding attention.
5. **The object leads, the interface follows** — if the human is focused on an object, the interface adapts, not the other way around.

---

### 4.6 Cognitive Load Management

**Principle:** Every design decision is measured against the cognitive load test. The object-first model is itself a cognitive load reduction strategy — it replaces arbitrary page hierarchies with the human's natural mental model of "things and their connections."

#### 4.6.1 Cognitive Load Reductions

| Technique | How It Reduces Load |
|-----------|-------------------|
| **Object-first navigation** | No need to remember where things "live" — find the object, follow its relationships |
| **Workspace scoping** | The workspace filters the universe to what's relevant — no irrelevant objects |
| **Relationship-first exploration** | Navigate by following connections, not by remembering a menu tree |
| **Progressive disclosure** | Default shows only what's needed; complexity is opt-in |
| **Consistent object patterns** | Every object type has the same surface — learn one, learn all |
| **Keyboard-first** | No context switching between keyboard and mouse |
| **Undo everywhere** | Freedom to explore without fear of irreversible actions |
| **AI collaboration** | The AI handles routine object operations, freeing human attention for decisions |

#### 4.6.2 Information Hierarchy

```
Primary (20%)    — The object's identity and current state
    │
Secondary (5%)   — Key relationships and recent activity
    │
Tertiary (2%)    — Object details, metadata, history
    │
Quaternary (1%)  — Technical data, audit trail, version history
```

The remaining 72% is whitespace (70% whitespace + 2% for controls).

---

### 4.7 Context Preservation

**Principle:** Context persists across interactions, sessions, and devices. The human never loses their place in the object graph.

#### 4.7.1 What This Means

When a human returns to a workspace, the workspace is exactly as they left it — same focal object, same relationship panel state, same scroll position. The system remembers:

| Context Element | Persistence Scope |
|----------------|-------------------|
| Current workspace | Session-persistent, device-persistent |
| Current focal object | Session-persistent |
| Open relationship panels | Session-persistent |
| Object search history | Session-persistent, configurable |
| Undo stack | Session-persistent |
| AI collaboration history | Persistent (object-linked) |
| View preferences per object type | Persistent (user-linked) |
| Recent objects | Persistent (cross-session) |

#### 4.7.2 Context Preservation Rules

1. **Return is resume** — closing and reopening the system returns to the same object context
2. **Workspaces remember state** — each workspace maintains its own context independently
3. **AI retains object context** — the AI remembers the conversation history for each object
4. **Undo survives accidental navigation** — navigating away and back preserves the undo stack
5. **Cross-device continuity** — context follows the human across devices via the workspace state

---

### 4.8 Progressive Disclosure

**Principle:** Complexity is revealed gradually. The human sees what they need for their current task, and nothing more. Additional capability is one click away, never hidden.

#### 4.8.1 Disclosure Levels

| Level | What the Human Sees | Trigger |
|-------|---------------------|---------|
| **Default** | Object identity, current state, primary action | Always visible |
| **Expand** | Key relationships, recent activity, secondary actions | Click to reveal |
| **Detail** | Full object data, all relationships, history | Click to expand |
| **Advanced** | Technical configuration, APIs, audit trail | Settings/context menu |
| **Developer** | Protocol details, raw data, schema | Developer mode toggle |

#### 4.8.2 Object-Specific Disclosure

Every object type follows the same disclosure pattern:

```
Object: [Name]
    ▼ (Default) Identity · State · Primary Action
        ▼ (Expand) Relationships · Activity · Secondary Actions
            ▼ (Detail) All Fields · Full History · Change Log
                ▼ (Advanced) Permissions · Integrations · Audit
```

The human can expand any level independently. Levels are sticky — if the human expands "Detail" for a Task object, all Task objects show at the Detail level until collapsed.

#### 4.8.3 Progressive Disclosure Rules

1. **Default is always usable** — the default view contains everything needed for 90% of tasks
2. **Expand is one click** — no multi-step reveals
3. **Detail preserves relationships** — even at the most detailed level, relationship navigation remains visible
4. **Advanced is never required** — no core workflow requires advanced settings
5. **Disclosure is sticky per object type** — the human's preference is remembered

---

### 4.9 Founder Experience

**Principle:** The founder experience is designed for a single, authoritative decision-maker who owns the business end-to-end. The founder operates on objects directly, with minimal indirection.

#### 4.9.1 Characteristics

| Attribute | Description |
|-----------|-------------|
| **Direct ownership** | The founder is the default owner of all objects they create |
| **Minimal hierarchy** | No layers of approval for the founder's own actions |
| **Full visibility** | The founder sees all objects across all workspaces |
| **Immediate action** | The founder's actions take effect immediately, with full undo |
| **Personal workspace** | A private workspace for the founder's direct objects and decisions |

#### 4.9.2 Founder Experience Principles

1. **Create first, organize later** — the founder can create an object without deciding where it goes
2. **No permission friction** — the founder always has permission to act on any object
3. **AI as advisor** — the AI proposes options and consequences; the founder decides
4. **Minimal ceremony** — no workflow steps, no approvals, no routing for the founder's own actions
5. **Direct delegation** — the founder can delegate an object to a team member with one action
6. **Single-pane visibility** — the founder can see all objects, all workspaces, all activity in one view

---

### 4.10 Executive Experience

**Principle:** The executive experience is designed for an organizational leader who needs awareness, delegation, and oversight — not hands-on object manipulation.

#### 4.10.1 Characteristics

| Attribute | Description |
|-----------|-------------|
| **Delegated ownership** | The executive owns through delegation — objects are owned by team members |
| **Dashboard-first** | The executive's primary view is aggregated, not individual |
| **Exception-based** | The executive sees what needs attention, not everything |
| **Summary-aware** | The executive sees outcomes, not processes |
| **Multi-workspace** | The executive operates across all workspaces in their organization |

#### 4.10.2 Executive Experience Principles

1. **Dashboard before detail** — the executive sees aggregated state before individual objects
2. **Outcome-first** — the executive sees outcomes (Outcome objects) before the work that produced them
3. **Exception notification** — the executive is notified only of objects that need their decision
4. **Delegation chain** — the executive can see who owns what, and can reassign
5. **Reading mode** — the executive consumes object information without needing to edit
6. **AI briefing** — the AI provides a summarized view of workspace state, highlighting what needs executive attention

---

### 4.11 Team Experience

**Principle:** The team experience is designed for collaborative groups working on shared objects within a shared workspace.

#### 4.11.1 Characteristics

| Attribute | Description |
|-----------|-------------|
| **Shared ownership** | Objects are owned by the team, with individual responsibility assigned |
| **Workspace-centric** | The team operates within a shared workspace with common objects |
| **Activity-aware** | The team sees each other's object activity in real time |
| **Role-based** | Different team members have different permissions on objects |
| **Communication-integrated** | Conversation objects are adjacent to the objects they relate to |

#### 4.11.2 Team Experience Principles

1. **Shared workspace, individual views** — the team shares a workspace, but each member has their own focal object
2. **Real-time object awareness** — team members see changes to shared objects without refreshing
3. **Object-linked communication** — every conversation is attached to the object it relates to
4. **Responsibility clarity** — every object has a clear owner, even in a shared workspace
5. **Approval workflows** — objects can require approval from specific team members before transitioning state
6. **Activity feeds** — the team sees what changed, who changed it, and what the object's current state is
7. **AI as team member** — the AI participates in the workspace, taking actions on objects when authorized

---

### 4.12 Mobile Philosophy

**Principle:** The mobile experience is not a shrunken desktop. It is a purpose-built experience for consuming objects, triaging attention, and performing quick actions on the go.

#### 4.12.1 Characteristics

| Attribute | Description |
|-----------|-------------|
| **Consumption-first** | Mobile is primarily for viewing objects, not creating them |
| **Triage, not deep work** | Mobile handles notifications, quick decisions, and object checks |
| **Context-aware** | Mobile uses device context (location, time, activity) to surface relevant objects |
| **Offline-resilient** | Objects are available offline; actions are queued and synced |
| **Voice-optional** | Voice input is a first-class citizen on mobile |

#### 4.12.2 Mobile Experience Principles

1. **Object-first, even at small sizes** — the focal object is still the center of the screen
2. **Bottom navigation** — mobile uses bottom navigation for thumb reachability
3. **Relationship panel as overlay** — relationships are accessible via a bottom sheet, not a sidebar
4. **Notifications are object links** — every notification links directly to the relevant object
5. **Quick actions** — common actions on objects (approve, assign, comment) are one tap
6. **Voice object creation** — create objects by voice ("Create a task to review Q3 budget")
7. **Offline object cache** — the last-seen state of objects is available offline, with queued actions
8. **Responsive breakpoints** — the mobile layout activates below 600px width

---

## 5. Responsive Philosophy

### 5.1 Breakpoints

| Breakpoint | Width | Layout |
|-----------|-------|--------|
| **Desktop** | ≥ 1200px | Full layout with object browser sidebar |
| **Small Desktop** | 900–1199px | Full layout, collapsed object browser |
| **Tablet** | 600–899px | Single column, object browser as overlay |
| **Mobile** | < 600px | Single column, bottom navigation, bottom sheet relationships |

### 5.2 Responsive Rules

| Element | Desktop | Tablet | Mobile |
|---------|---------|--------|--------|
| **Object Browser** | Visible | Overlay | Hidden (bottom sheet) |
| **Relationship Panel** | Visible | Collapsible | Bottom sheet |
| **Navigation** | Object bar | Object bar | Bottom bar |
| **Object Detail** | Multi-section | Single section | Single section |
| **AI Panel** | Sidebar | Overlay | Full screen |
| **Data tables** | Full | Horizontal scroll | Object card list |
| **70/20/10** | Preserved | Preserved | Tightened spacing |

---

## 6. Accessibility

### 6.1 Standards

SHUNYA targets WCAG 2.1 Level AA as minimum. Level AAA for core object workflows.

### 6.2 Requirements

| Requirement | Standard |
|-------------|----------|
| Color contrast | 4.5:1 (normal text), 3:1 (large text) |
| Touch targets | Minimum 44×44px |
| Keyboard navigation | Full keyboard access to all objects and actions |
| Screen reader support | ARIA labels, semantic HTML, object role announcements |
| Motion | Respect `prefers-reduced-motion` |
| Focus indicators | Clear, visible focus states |
| Text resize | Readable at 200% zoom |
| Alternative text | All non-decorative images |
| Object navigation | Screen reader can navigate object relationships by type |
| Status announcements | Object state changes are announced to assistive technology |

### 6.3 Object Accessibility

Every object surface must be accessible via:
- **Keyboard**: Tab through object fields, relationships, and actions
- **Screen reader**: Object identity, state, and relationships are announced
- **Focus management**: Navigating between objects preserves focus position
- **Action announcement**: Object actions are announced by type and effect

---

## 7. Future Extensibility

### 7.1 Domain Surfaces

Each domain (travel, healthcare, finance) customizes:
- Color palette (within warm minimalism)
- Typography (heading font may change)
- Iconography (domain-specific icons for object types)
- Terminology (domain-specific language for object names)
- Component composition (domain-specific object detail layouts)

The core experience framework — object-first navigation, workspace-first interaction, relationship-first exploration — remains unchanged.

### 7.2 Theme System

The experience layer supports theming through:
- CSS custom properties for all visual constants
- Component-level theme tokens
- Workspace-level theme overrides
- Organization-level branding
- Object-type-specific visual treatments

### 7.3 New Object Types

When new object types are added to the Business Canon (03), they automatically inherit the complete experience framework:
- Object-first navigation (type appears in object browser)
- Workspace interaction (objects can be created in any workspace)
- Relationship exploration (new relationship types are navigable)
- Progressive disclosure (default/expand/detail/advanced levels)
- All persona experiences (founder, executive, team, mobile)

---

## 8. Relationship to Other Canonical Documents

| Document | Relationship |
|----------|-------------|
| **00_universal_ontology.md** | Experience surfaces ontological concepts (Entity, Identity, Relationship, Context, Workspace) to humans |
| **02_shunya_constitution.md** | "Calm Before Complexity" (Article 9) is the primary UX mandate |
| **03_business_canon.md** | Experience surfaces business objects to humans — the 18 canonical object types are the vocabulary of every screen |
| **04_universal_object_protocol.md** | Experience renders actions from the protocol — every action available in the UI derives from the protocol |
| **05_runtime_canon.md** | Experience calls the runtime layer to execute object operations |
| **06_data_canon.md** | Experience reads from and writes to object stores |
| **07_ai_canon.md** | AI collaboration model and interaction patterns defined here — this document references, not duplicates |
| **09_repository_canon.md** | Frontend code organized by component philosophy to implement the experience |
| **10_migration_canon.md** | UX migration is part of overall migration |
| **11_engineering_canon.md** | Frontend standards derived from this canon |
| **12_launch_roadmap.md** | UX milestones are front-loaded (Phase Z) |
| **docs/frontend/INFORMATION_ARCHITECTURE.md** | Implementation specification — navigation architecture, screen hierarchy, IA for the canon |
| **docs/frontend/DESIGN_SYSTEM.md** | Implementation specification — design tokens, motion, accessibility for the canon |
| **docs/frontend/DESKTOP_INTERACTION_MODEL.md** | Implementation specification — desktop interactions, keyboard model, drag-and-drop |
| **docs/frontend/MOBILE_INTERACTION_MODEL.md** | Implementation specification — mobile interactions, gestures, offline behavior |
| **docs/frontend/COMPONENT_SPECIFICATION.md** | Implementation specification — every component's props, states, and behaviors |

---

> **Next:** [09_repository_canon.md](09_repository_canon.md)