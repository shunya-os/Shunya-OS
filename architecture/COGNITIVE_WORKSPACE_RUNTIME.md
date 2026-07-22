# Cognitive Workspace Runtime

**Phase 8B — SHUNYA OS**
**Classification: Constitutional Architecture**
**Status: PROPOSED**
**Version: 1.0**

---

## Preamble

### Authority

This document defines the constitutional runtime that governs how SHUNYA thinks, what it pays attention to, what it predicts, what it recommends, what it renders, what it remembers, and what it ignores — before a single pixel reaches the screen.

### Dependency chain

This document's dependency chain is derived from the canonical chain defined in UNIVERSAL_ONTOLOGY.md §20. The canonical chain is authoritative and must not be redefined.

```
Reality
  ↓
Observation
  ↓
Evidence
  ↓
Object (Universal Object Graph)
  ↓
Relationship (Relationship Graph)
  ↓
Knowledge (Knowledge Graph)
  ↓
Reasoning
  ↓
Prediction
  ↓
Execution (Execution Graph)
  ↓
Workspace Projection Engine
  ↓
Founder Workspace
```

This chain is never reversed. The workspace does not drive cognition. Cognition drives the workspace.

### Principles

1. The workspace is NOT the source of truth. Reality is.
2. The workspace is a projection of SHUNYA's internal understanding of reality.
3. No screen owns data. The runtime owns understanding. The screen projects understanding.
4. The runtime — not the UI — defines how SHUNYA behaves.
5. Every interaction flows through the Universal Intent Pipeline.
6. The current object always exists. Conversation never loses context. Object identity never changes.
7. Business-agnostic. Universal. No domain-specific logic.

---

## 1. Reality Runtime

### 1.1 Purpose

The Reality Runtime is the subsystem that transforms real-world entities into canonical SHUNYA objects. It is the entry point through which all external information enters the cognitive workspace.

### 1.2 Ingestion boundaries

| Source | How reality enters | Transformation |
|--------|-------------------|----------------|
| Founder conversation | Universal Composer → Intent Pipeline | Structured object + evidence |
| External API | Webhook → Event Bus → Object Factory | Mapped to canonical type |
| File upload | Upload handler → Document Analyzer | Parsed → chunked → knowledge |
| Email | Email adapter → Message Extractor | Threaded → linked to contacts |
| Calendar | Calendar sync → Event parser | Meeting → task relationships |
| Manual entry | Founder creates object directly | Minimal schema, enriched later |

### 1.3 Object factory

Every external entity passes through the Object Factory, which:

1. Classifies the entity to a canonical type (Person, Company, Document, Task, Meeting, Project, Commitment, Message, Knowledge, Workflow, Conversation)
2. Assigns a permanent object identity
3. Attaches provenance metadata (source, timestamp, confidence)
4. Registers the object in the Universal Object Graph
5. Emits `ObjectCreated` event

### 1.4 Identity stability

Once assigned, an object's identity NEVER changes. Mergers create a superior identity and deprecate the inferior. Identity is never recycled.

### 1.5 Evidence attachment

Every object carries an immutable evidence chain. Each evidence entry records:

- What was observed
- Who observed it
- When it was observed
- Confidence in the observation
- Source of the observation

---

## 2. Attention Engine

### 2.1 Purpose

The Attention Engine determines what SHUNYA pays attention to at any moment. It is the cognitive filter that decides which objects, relationships, predictions, and risks are surfaced to the founder.

### 2.2 Attention levels

| Level | Definition | When active | What is surfaced |
|-------|------------|-------------|------------------|
| **Active Attention** | The object the founder is currently interacting with | Object is focused | Full object view, complete intelligence, all relationships |
| **Background Attention** | Objects related to the current focus that need awareness | Current object is focused | 1-hop relationships, relevance-scored, compressed |
| **Ambient Awareness** | Objects that are important but not directly related | No active focus, or periodic background scan | Prioritized by importance × urgency, top 5-7 items |
| **Interrupted Context** | The object the founder was viewing before focus changed | Focus switched to another object | Preserved state, ready for one-click restoration |
| **Returning Context** | The object the founder was viewing in a previous session | Session begins | Last-focused object, restored from session memory |
| **Context Expiration** | When an object transitions out of active attention | 30 minutes of inactivity on that object | State frozen, moved to session memory |
| **Context Restoration** | When an object is refocused after expiration | Founder clicks or navigates to the object | Full state restored from memory, freshness check performed |

### 2.3 Attention scoring

Every object in the system has an attention score, computed as:

```
attention_score = (recency × 0.3) + (relevance × 0.25) + (urgency × 0.2) + (importance × 0.15) + (relationship_strength × 0.1)
```

| Factor | Definition | Scale |
|--------|------------|-------|
| recency | Time since last interaction | 0.0 (never) — 1.0 (now) |
| relevance | Semantic similarity to current focus | 0.0 (unrelated) — 1.0 (identical) |
| urgency | Time-sensitive actions pending | 0.0 (passive) — 1.0 (overdue) |
| importance | Founder-assigned or computed priority | 0.0 (trivial) — 1.0 (critical) |
| relationship_strength | Connection strength to current focus | 0.0 (none) — 1.0 (direct) |

### 2.4 Attention decay

When an object is not in focus, its attention score decays:

```
score(t) = score(0) × e^(-λt)
```

Where λ (decay rate) depends on object type:

| Object type | λ (per hour) | Half-life |
|-------------|--------------|-----------|
| Person | 0.1 | ~7 hours |
| Company | 0.05 | ~14 hours |
| Task (overdue) | 0.02 | ~35 hours |
| Task (normal) | 0.2 | ~3.5 hours |
| Meeting | 0.3 | ~2.3 hours |
| Message | 0.5 | ~1.4 hours |
| Document | 0.15 | ~4.6 hours |
| Commitment | 0.08 | ~8.7 hours |
| Project | 0.04 | ~17 hours |

### 2.5 Attention promotion

An object in Ambient Awareness can be promoted to Active Attention by:

1. Founder explicitly focuses on it
2. Attention score exceeds the active threshold (≥ 0.7)
3. A critical event fires (risk detected, commitment delayed)
4. The founder's conversation explicitly references it

### 2.6 Attention demotion

An object in Active Attention is demoted to Background Attention when:

1. Founder switches to another object (instantly)
2. No interaction for 5 minutes (graceful decay)
3. An object with higher attention score demands focus

### 2.7 Interruption policy

Not all events trigger an interruption. The Attention Engine evaluates:

| Event type | Interrupts? | Condition |
|------------|-------------|-----------|
| Risk detected | Conditional | Only if severity ≥ HIGH and relevance ≥ 0.5 |
| Commitment delayed | Yes | Always interrupt |
| Task overdue | Conditional | Only if importance ≥ HIGH |
| Message received | Conditional | Only if from key contact |
| Prediction generated | No | Surface in intelligence panel, never interrupt |
| System event | No | Logged, never interrupt |

---

## 3. Workspace Projection Engine

### 3.1 Purpose

The Workspace Projection Engine transforms the runtime's cognitive state into a structured view model that the workspace renders. It is the bridge between cognition and UI. No screen owns data. The runtime owns understanding. The screen projects understanding.

### 3.2 Projection pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Cognitive    │────▶│  Projection  │────▶│  View Model  │────▶│  Workspace   │
│  State        │     │  Engine      │     │  Assembly    │     │  Renderer    │
│               │     │              │     │              │     │              │
│  Object Graph │     │  Selects     │     │  Builds      │     │  Renders     │
│  Relationships│     │  what to     │     │  structured  │     │  the view    │
│  Knowledge    │     │  project     │     │  response    │     │  model       │
│  Attention    │     │  based on    │     │  from        │     │              │
│  Reasoning    │     │  attention   │     │  projections │     │              │
│  Predictions  │     │  and context │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 3.3 What the projection engine produces

For every workspace render, the Projection Engine produces:

| Component | Source | Content |
|-----------|--------|---------|
| Context Header | Attention Engine | Current object type, name, status, awareness state |
| Left Panel | Object Graph + Relationship Graph | Recent objects, relationships, pinned items |
| Center (Living Workspace) | Object Graph + Knowledge Graph | Object content, timeline, evidence, conversation |
| Right Panel (Intelligence) | Knowledge Graph + Reasoning Engine | Understanding, recommendations, predictions, risks, reasoning |
| Composer suggestions | Intent Pipeline | Predicted next actions, context-aware completions |
| Ambient awareness | Attention Engine | Background attention items, notifications |

### 3.4 Projection rules

1. **The projection is a snapshot.** It is computed at request time. It is never cached beyond the current render cycle.
2. **The projection is read-only.** The workspace cannot write to the cognitive state through the projection. All writes go through the Intent Pipeline.
3. **The projection is minimal.** Only what the Attention Engine determines is relevant is included.
4. **The projection is deterministic.** Identical cognitive state + identical attention state → identical projection.

### 3.5 View model contract

```python
@dataclass
class WorkspaceProjection:
    header: ContextHeader
    left_panel: LeftPanel
    center: LivingWorkspace
    right_panel: IntelligencePanel
    composer: ComposerState
    ambient: AmbientState
    timestamp: datetime
    projection_id: str
```

Every projection carries a unique `projection_id` for traceability.

---

## 4. Universal Intent Pipeline

### 4.1 Purpose

Every interaction — whether typed, clicked, spoken, or triggered — flows through the Universal Intent Pipeline. This is the single path by which the founder's intent becomes SHUNYA action.

### 4.2 Pipeline stages

```
Natural Language
  ↓
Intent Classification
  ↓
Object Resolution
  ↓
Relationship Resolution
  ↓
Policy Evaluation
  ↓
Deterministic Execution
  ↓
Reasoning Escalation (only if required)
  ↓
Workspace Update
```

### 4.3 Stage definitions

| Stage | Input | Output | Behaviour |
|-------|-------|--------|-----------|
| **Natural Language** | Raw text or speech | Normalized query | Strip filler, normalize contractions, extract entities |
| **Intent Classification** | Normalized query | Intent + parameters | Pattern-match against known intents (see 4.4) |
| **Object Resolution** | Intent with parameters | Resolved object reference | Map "Rahul" → Person object, "proposal" → Document object |
| **Relationship Resolution** | Object reference + intent context | Related object set | Resolve 1-hop relationships relevant to the intent |
| **Policy Evaluation** | Intent + objects + relationships | Allow/Deny/RequireApproval | Check governance policies, permission boundaries, escalation rules |
| **Deterministic Execution** | Approved intent | Action result | Execute the action without AI (create, update, query, navigate) |
| **Reasoning Escalation** | Complex intent or policy failure | Reasoning result | Only if deterministic execution cannot resolve — invoke Reasoning Engine |
| **Workspace Update** | Action result + reasoning | New projection | Trigger Projection Engine to recompute the workspace view |

### 4.4 Intent catalogue

| Intent | Example | Action | Requires reasoning? |
|--------|---------|--------|---------------------|
| CREATE | "Create a task for Rahul" | Object factory → Task | No |
| UPDATE | "Change the due date" | Object mutation | No |
| QUERY | "What's the status?" | Object read → summarize | No |
| NAVIGATE | "Show me the proposal" | Attention switch | No |
| EXECUTE | "Send this" | Execution Engine | No |
| TRANSFORM | "Convert to proposal" | Object transformation | Yes |
| ANALYZE | "Why is this delayed?" | Reasoning Engine | Yes |
| COMPARE | "How does this compare?" | Reasoning Engine | Yes |
| PREDICT | "What's the risk?" | Prediction Engine | Yes |
| SUMMARIZE | "Summarise this" | Knowledge Engine | No |

### 4.5 Intent classification method

Intent classification is deterministic pattern matching. No AI model is required for routing.

Priority order (first match wins):

1. Explicit verb patterns: "Create X", "Show Y", "Send Z"
2. Question patterns: "What", "Why", "How", "When", "Who"
3. Contextual patterns: references to current object or recent objects
4. Default: QUERY on current object

### 4.6 Pipeline failure behaviour

| Failure | Behaviour | Recovery |
|---------|-----------|----------|
| Unknown intent | Surface suggested intents to founder | "I can: create, show, send, summarize" |
| Object not found | Surface nearest matches | "Did you mean: Rahul Sharma, Rahul Kapoor?" |
| Policy denied | Surface reason + appeal path | "This requires approval from [name]" |
| Execution error | Surface error + rollback | "Task creation failed. Reason: [detail]" |

---

## 5. Cognitive Memory Layers

### 5.1 Purpose

SHUNYA maintains multiple memory layers. The canonical memory model is defined in UNIVERSAL_ONTOLOGY.md §17. This section is the authoritative reference for all memory-related cognition. No document may redefine memory independently.

### 5.2 Memory hierarchy

The memory hierarchy is defined in UNIVERSAL_ONTOLOGY.md §17.2. It consists of six layers: Working Memory, Conversation Memory, Relationship Memory, Knowledge Memory, Historical Memory, and Constitutional Memory.

Active Attention (defined in §2 of this document) is an attention concept, not a memory layer. It consumes Working Memory but is not itself a memory store.

### 5.3 Runtime memory promotion

The Cognitive Runtime manages promotion between layers as follows:

| From | To | Condition |
|------|----|-----------|
| Working Memory → Session Memory | Object is unfocused | Recorded on every focus switch |
| Session Memory → Historical Memory | Session ends | All session objects archived |
| Working Memory → Relationship Memory | Interaction occurs | Relationship strength updated |
| Relationship Memory → Organizational Memory | Pattern detected across 3+ sessions | Generalised pattern promoted |
| Working Memory → Long-Term Knowledge | Knowledge Engine confirms fact | Validated fact stored permanently |
| Ambient Awareness → Working Memory | Founder focuses on object | Full projection loaded |

### 5.4 Decay rules

| Layer | Decay function | Threshold | Action |
|-------|---------------|-----------|--------|
| Active Attention | `score(t) = score(0) × e^(-0.2t)` | < 0.3 | Demote to Working Memory |
| Working Memory | `score(t) = score(0) × e^(-0.1t)` | < 0.2 | Demote to Session Memory |
| Session Memory | `score(t) = score(0) × e^(-0.05t)` | Session end | Archive to Historical |
| Relationship Memory | `strength(t) = strength(0) × e^(-0.05t)` | < 0.1 | Remove from active graph |
| Organizational Memory | No reinforcement for 90 days | 90 days | Flag for review, not deleted |

### 5.5 Memory consolidation

The Consolidation Engine runs every 5 minutes:

1. Scan Working Memory for objects not interacted with in 30 minutes
2. Demote to Session Memory with a compressed projection
3. Update Relationship Memory based on interactions during the window
4. Execute Knowledge Engine promotion candidates

---

## 6. Universal Object Lifecycle

### 6.1 Purpose

Every object in the system follows one lifecycle. There is no type-specific lifecycle logic. The same state machine governs Person, Company, Document, Task, Meeting, Project, Commitment, Message, Knowledge, Workflow, and Conversation.

### 6.2 Lifecycle states

```
                  ┌──────────┐
                  │  CREATE  │
                  └────┬─────┘
                       │
                       ▼
                  ┌──────────┐
         ┌───────▶│ OBSERVE  │◀────────┐
         │        └────┬─────┘         │
         │             │               │
         │             ▼               │
         │        ┌──────────┐         │
         │        │  ENRICH  │         │
         │        └────┬─────┘         │
         │             │               │
         │             ▼               │
         │        ┌──────────┐         │
         │        │  RELATE  │         │
         │        └────┬─────┘         │
         │             │               │
         │             ▼               │
         │        ┌──────────┐         │
         │        │ PREDICT  │         │
         │        └────┬─────┘         │
         │             │               │
         │             ▼               │
         │        ┌──────────┐         │
         │        │ EXECUTE  │         │
         │        └────┬─────┘         │
         │             │               │
         │        ┌────┴────┐          │
         │        │         │          │
         │        ▼         ▼          │
         │  ┌─────────┐ ┌────────┐     │
         │  │ ARCHIVE │ │ RESTORE│─────┘
         │  └────┬────┘ └────────┘
         │       │
         │       ▼
         │  ┌──────────┐
         └──│  DELETE  │
            └──────────┘
```

### 6.3 State transitions

| Transition | Trigger | Behaviour |
|------------|---------|-----------|
| CREATE → OBSERVE | Object registered | Initial observation recorded, identity assigned |
| OBSERVE → ENRICH | New information arrives | Evidence attached, knowledge updated |
| ENRICH → RELATE | Relationship detected | Graph edges created, strength scored |
| RELATE → PREDICT | Prediction cycle | Prediction Engine invoked, forecasts generated |
| PREDICT → EXECUTE | Action triggered | Execution Engine invoked, outcome recorded |
| EXECUTE → OBSERVE | Outcome observed | Execution result becomes new observation |
| EXECUTE → ARCHIVE | Object inactive for 30 days | State frozen, removed from Active Attention |
| ARCHIVE → RESTORE | Founder accesses object | Full state restored, entered at OBSERVE |
| ARCHIVE → DELETE | Founder confirms deletion | Object removed, provenance preserved |
| DELETE → (terminal) | Deletion confirmed | Identity retired, never reused |

### 6.4 Lifecycle invariants

1. Every object is created exactly once.
2. An object can be ENRICHED any number of times.
3. An object can be in at most one state at a time.
4. ARCHIVE preserves all data; it only removes from active attention.
5. DELETE is irreversible. The object_id is retired permanently.
6. RESTORE transitions to OBSERVE, not to the previous state.
7. The lifecycle is event-sourced. Every transition emits an event.

---

## 7. Workspace Invariants

### 7.1 Constitutional invariants

These rules are absolute. No implementation may violate them.

Invariants marked with (O-NNN) are defined in UNIVERSAL_ONTOLOGY.md §19. They are listed here for completeness but are owned by the Ontology.

| ID | Invariant | Rationale | Violation consequence |
|----|-----------|-----------|----------------------|
| I-01 | The current object always exists | Workspace cannot render an empty state | Workspace falls back to Morning Zero |
| I-02 | Conversation never loses context | Every message references the current object | Conversation tree is immutable |
| I-03 | (O-01) Object identity never changes | Defined in Ontology | Identity is a permanent anchor |
| I-04 | (O-17) Relationships are never duplicated | Defined in Ontology | Deduplication on every relationship creation |
| I-05 | UI cannot mutate cognition directly | All mutations flow through Intent Pipeline | Projection Engine rejects direct writes |
| I-06 | Reasoning is reproducible | Same input → same reasoning trace | All reasoning is deterministic |
| I-07 | (O-07) Predictions are traceable | Defined in Ontology | Prediction is invalid without trace |
| I-08 | Execution is observable | Every execution produces an observation | Execution is not complete until observation is recorded |
| I-09 | (O-15) The dependency chain is never reversed | Defined in Ontology | Architectural violation, rejected at runtime |
| I-10 | Every projection is a snapshot | Projections are computed at request time | Never cached beyond render cycle |
| I-11 | The workspace is read-only projection | Workspace cannot write to cognitive state | All writes go through Intent Pipeline |
| I-12 | Memory decays deterministically | Decay follows the defined functions | Decay is computed, not approximated |
| I-13 | Object lifecycle is event-sourced | Every transition emits an event | Event bus must record every transition |
| I-14 | Attention is computed, not configured | No manual attention assignments | Attention Engine is the sole authority |
| I-15 | The composer is the single input channel | No other input may mutate state | All mutations are Intent Pipeline traces |

### 7.2 Invariant enforcement

Invariants I-01 through I-15 are enforced by the Workspace Runtime. Violations are:

1. Logged with full context
2. Surfaced to the founder as a system alert
3. Prevented at the architectural boundary (the boundary between the Projection Engine and the Intent Pipeline)

---

## 8. Context Transition Model

### 8.1 Purpose

The Context Transition Model defines exactly how cognition moves from one object to another. The founder switches between objects without changing applications. Only the current object changes. Everything else remains.

### 8.2 Transition anatomy

```
Current object: Person (Ritu Sharma)
    │
    │ Founder clicks "Proposal Q3" link
    ▼
Context Transition initiated
    │
    ├── Stage 1: Freeze current context
    │     - Current object state → Working Memory
    │     - Attention score computed for current object
    │     - Interrupted Context = Person (Ritu Sharma)
    │
    ├── Stage 2: Resolve target object
    │     - Object ID resolved from link
    │     - Object loaded from Universal Object Graph
    │     - Object identity verified
    │
    ├── Stage 3: Compute new context
    │     - Attention Engine evaluates new focus
    │     - 1-hop relationships loaded
    │     - Intelligence panel recomputed
    │     - Relationship strength between old and new recorded
    │
    ├── Stage 4: Build projection
    │     - Projection Engine assembles view model
    │     - Left panel updated for new context
    │     - Center renders new object
    │     - Right panel shows new intelligence
    │
    ├── Stage 5: Emit transition event
    │     - ObjectFocused event emitted
    │     - ContextChanged event emitted
    │     - Previous object added to session memory
    │
    └── Stage 6: Background refresh
          - 1-hop objects prefetched
          - Intelligence panel refined
          - Relationship graph updated
```

### 8.3 Transition types

| Type | Trigger | Latency | Full projection? |
|------|---------|---------|------------------|
| **Direct** | Click link, search result | < 250ms | Yes |
| **Back** | Alt+Left, browser back | < 100ms | Yes (from Working Memory) |
| **Forward** | Alt+Right, browser forward | < 250ms | Yes |
| **Composer** | Natural language navigation | < 500ms | Yes (includes Intent Pipeline) |
| **Return** | Returning to a recent object | < 150ms | Yes (from Session Memory) |
| **Restore** | Returning from a new session | < 1s | Yes (from Historical Memory) |

### 8.4 Transition depth

| Depth | Objects loaded | Latency budget |
|-------|----------------|----------------|
| 0 (current) | 1 | Instant |
| 1 (1-hop) | Current + directly related | < 250ms |
| 2 (2-hop) | Current + 1-hop + 2-hop | < 500ms (background) |

### 8.5 Cross-type transitions

The founder can transition between any object types. The transition model is identical regardless of source and target type. There is no special handling for:

- Person → Company
- Company → Document
- Document → Task
- Task → Meeting
- Meeting → Project
- Project → Commitment
- Commitment → Conversation
- Conversation → Person

Every transition follows the same 6-stage anatomy.

---

## 9. Cognitive Event Bus

### 9.1 Purpose

The Cognitive Event Bus is the nervous system of the runtime. Every cognitive event — attention changes, relationship updates, predictions, risks, executions, memory promotions — flows through this bus. The bus is the foundation for synchronization, observability, and traceability.

### 9.2 Canonical events

| Event | Payload | Emitter | Consumers |
|-------|---------|---------|-----------|
| `ObjectCreated` | object_id, type, provenance | Reality Runtime | Object Graph, Knowledge Engine, Memory |
| `ObjectFocused` | object_id, previous_id, timestamp | Attention Engine | Memory, Projection Engine, Sync |
| `ObjectUnfocused` | object_id, attention_score | Attention Engine | Memory |
| `RelationshipChanged` | source_id, target_id, type, strength | Relationship Graph | Attention Engine, Memory |
| `ContextChanged` | previous_id, current_id, transition_type | Attention Engine | Projection Engine, Sync |
| `PredictionGenerated` | object_id, prediction_id, category, confidence | Prediction Engine | Intelligence Panel, Attention |
| `RiskDetected` | object_id, risk_id, severity, description | Risk Engine | Attention Engine, Projection |
| `CommitmentDelayed` | object_id, commitment_id, delay | Execution Engine | Attention Engine, Alert |
| `EvidenceObserved` | object_id, evidence_id, source, confidence | Reality Runtime | Knowledge Engine, Object Graph |
| `ExecutionCompleted` | object_id, execution_id, outcome | Execution Engine | Object Lifecycle, Memory |
| `MemoryPromoted` | from_layer, to_layer, object_id | Consolidation Engine | Memory |
| `MemoryExpired` | from_layer, object_id | Consolidation Engine | Memory |
| `IntentProcessed` | intent, object_id, result, latency | Intent Pipeline | Projection Engine, Audit |
| `ProjectionCreated` | projection_id, object_id, timestamp | Projection Engine | Audit, Sync |
| `AttentionPromoted` | object_id, from_level, to_level | Attention Engine | Projection Engine |
| `AttentionDemoted` | object_id, from_level, to_level | Attention Engine | Memory |

### 9.3 Event envelope

Every event carries:

```python
@dataclass
class CognitiveEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    correlation_id: str  # Links events from the same interaction
    causation_id: str    # Links to the event that caused this one
    object_id: Optional[str]
    payload: dict
    provenance: EventProvenance
```

### 9.4 Event ordering

Events within a single interaction are ordered by causation. The causation_id forms a DAG. Events from different interactions are unordered.

Consumers must handle out-of-order arrival. The pattern is:
- Use `correlation_id` to group events from the same interaction
- Use `causation_id` to reconstruct the causal chain
- Apply events idempotently (event_id is the deduplication key)

### 9.5 Event retention

| Event type | Retention | Purpose |
|------------|-----------|---------|
| All cognitive events | 7 days in active bus | Synchronization, debugging |
| `ObjectCreated`, `EvidenceObserved` | Permanent in Historical Memory | Traceability |
| `ExecutionCompleted` | Permanent in Historical Memory | Audit trail |
| `ProjectionCreated` | 24 hours | Debugging |
| `AttentionPromoted`, `AttentionDemoted` | 7 days | Pattern analysis |

---

## 10. Workspace Synchronization

### 10.1 Purpose

Multiple browser tabs, mobile, tablet, desktop, and future native applications must all observe one runtime. The workspace is a projection of a single cognitive state. There is no per-device state.

### 10.2 Synchronization model

```
┌──────────────────────────────────────────────────────────────┐
│                     COGNITIVE RUNTIME                          │
│                     (single source of truth)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Attention│  │  Object  │  │ Knowledge│  │  Reasoning   │  │
│  │  Engine  │  │  Graph   │  │  Engine  │  │  Engine      │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              │
                    Cognitive Event Bus
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Workspace    │   │  Workspace    │   │  Workspace    │
│  Projection 1 │   │  Projection 2 │   │  Projection 3 │
│  (Browser A)  │   │  (Browser B)  │   │  (Mobile)     │
└───────────────┘   └───────────────┘   └───────────────┘
```

### 10.3 Synchronization rules

1. **One runtime.** There is exactly one cognitive runtime. All projections derive from it.
2. **Projections are independent.** Each client computes its own projection. Clients do not share state.
3. **Events are broadcast.** All cognitive events are broadcast to all connected clients.
4. **Clients are stateless projection consumers.** The runtime holds all state; clients hold only the current projection.
5. **Conflict resolution is impossible.** There are no conflicts because there is no per-client state.

### 10.4 Connection protocol

| Client type | Connection | Event delivery | Reconnection |
|-------------|------------|----------------|--------------|
| Browser tab | WebSocket | Real-time push | Full state sync |
| Mobile | WebSocket (when foreground) | Push notification (when background) | Full state sync |
| Tablet | WebSocket | Real-time push | Full state sync |
| Native app | WebSocket (when active) | Push notification (when background) | Full state sync |

### 10.5 State sync on reconnect

When a client reconnects:

1. Client sends `last_projection_id`
2. Runtime sends all events since that projection
3. Client replays events to rebuild current state
4. If events are too many (> 1000), runtime sends full state snapshot

---

## 11. Runtime Performance

### 11.1 Latency targets

| Operation | Target | Degraded threshold |
|-----------|--------|-------------------|
| Object focus (direct) | < 250ms | > 500ms |
| Object focus (composer) | < 500ms | > 1s |
| Context transition | < 250ms | > 500ms |
| Projection assembly | < 100ms | > 300ms |
| Intent classification | < 50ms | > 100ms |
| Object resolution | < 100ms | > 300ms |
| Relationship resolution | < 200ms | > 500ms |
| Policy evaluation | < 50ms | > 100ms |
| Deterministic execution | < 200ms | > 500ms |
| Reasoning escalation | < 5s | > 10s |
| Prediction generation | < 3s | > 8s |
| Intelligence panel refresh | < 500ms | > 1s |
| Ambient awareness scan | < 2s | > 5s |

### 11.2 Caching strategy

| Cache | What | TTL | Invalidation |
|-------|------|-----|--------------|
| Object data | Full object view | 5 minutes | On object mutation event |
| Relationship graph | 1-hop edges | 1 minute | On RelationshipChanged event |
| Intelligence panel | Understanding, recommendations | 30 seconds | On any cognitive event |
| Attention scores | All object scores | 1 minute | On ObjectFocused event |
| Projection | Current workspace view | Never | Computed fresh each request |
| Search index | Object names + summaries | 1 minute | On ObjectCreated, ObjectUpdated |

### 11.3 Incremental updates

The Projection Engine supports incremental updates:

1. Initial projection: full view model
2. Subsequent updates: only changed sections

The workspace applies patches, not full re-renders.

### 11.4 Relationship indexing

Relationships are indexed bidirectionally. For every relationship `(A → B)`, the index stores `(A → B)` and `(B → A)`. This ensures:

- 1-hop resolution from any object is O(1)
- 2-hop resolution is O(n) where n is the number of 1-hop relationships
- Relationship strength updates are O(1)

### 11.5 Prediction refresh

Predictions are refreshed:

- On object focus (immediate)
- Every 30 minutes for objects in Working Memory
- Every 2 hours for objects in Ambient Awareness
- On critical events (risk detected, commitment delayed)

### 11.6 Background reasoning

The Reasoning Engine runs in the background for:

1. Objects in Active Attention (continuous)
2. Objects in Working Memory (every 5 minutes)
3. Objects in Ambient Awareness (every 30 minutes)
4. Objects triggered by events (immediate)

Background reasoning is preemptible. If the system is under load, background cycles are skipped.

---

## 12. Failure Modes

### 12.1 Constitutional recovery

Every failure mode has a defined recovery. The runtime never reaches an undefined state.

| Failure | Detection | Recovery | Data loss? |
|---------|-----------|----------|------------|
| **Missing object** | Object ID not found in Universal Object Graph | Return object not found error; surface nearest matches from search index | No |
| **Broken relationship** | Relationship edge points to non-existent object | Remove broken edge; log for investigation | No (edge removed) |
| **Conflicting evidence** | Two evidence entries with contradictory claims | Present both with confidence scores; do not resolve automatically | No |
| **Lost context** | Client reconnects without valid projection_id | Full state sync from Historical Memory | No (memory is permanent) |
| **Interrupted execution** | Execution Engine receives action but fails to complete | Rollback to previous state; surface error with reason | No (atomic rollback) |
| **Reasoning disagreement** | Two reasoning paths produce contradictory conclusions | Present both to founder with evidence chains; do not resolve | No |
| **Memory corruption** | Memory layer has inconsistent state | Rebuild from Historical Memory; log corruption details | No (historical is immutable) |
| **Attention Engine failure** | Attention scores cannot be computed | Fall back to recency-only scoring; log error | No (degraded but functional) |
| **Projection Engine failure** | View model cannot be assembled | Return minimal projection (object data only, no intelligence) | No (degraded) |
| **Intent Pipeline failure** | Stage in pipeline fails | Surface error at current stage; offer alternatives | No |
| **Event Bus failure** | Events cannot be published | Queue locally; retry on reconnect; max 1000 events | No (persistent queue) |
| **Cognitive Runtime crash** | Entire runtime restarts | Rebuild from Historical Memory; replay event log | No (events are durable) |

### 12.2 Degraded mode behaviour

| Condition | Behaviour |
|-----------|-----------|
| Intelligence panel unavailable | Display "Intelligence unavailable" placeholder; show object data only |
| Attention Engine degraded | Fall back to recency-only scoring |
| Prediction Engine unavailable | Hide predictions panel; do not delay workspace rendering |
| Relationship Graph unavailable | Show current object only; hide left panel relationships |
| Event Bus unavailable | Queue events locally; retry every 5 seconds |
| Historical Memory unavailable | Use Session Memory only; warn founder |

### 12.3 Recovery verification

After any failure recovery, the runtime must verify:

1. I-01 (current object exists) — satisfied
2. I-03 (object identity unchanged) — satisfied
3. I-06 (reasoning reproducible) — satisfied
4. I-08 (execution observable) — satisfied
5. I-09 (dependency chain not reversed) — satisfied

If any invariant is violated, the runtime enters safe mode (Morning Zero only) until the invariant is restored.

---

## Appendix A: Runtime Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          COGNITIVE WORKSPACE RUNTIME                             │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  REALITY LAYER                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │   │
│  │  │  Reality     │─▶│  Object      │─▶│  Identity    │─▶│  Evidence    │ │   │
│  │  │  Runtime     │  │  Factory     │  │  Registry    │  │  Chain       │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│  ┌──────────────────────────────────────┴───────────────────────────────────┐   │
│  │  COGNITIVE LAYER                                                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │   │
│  │  │  Universal   │  │  Relationship│  │  Execution   │  │  Knowledge   │ │   │
│  │  │  Object Graph│  │  Graph       │  │  Graph       │  │  Graph       │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │   │
│  │                                                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐   │   │
│  │  │  Attention   │─▶│  Reasoning   │  │  Cognitive Memory            │   │   │
│  │  │  Engine      │  │  Engine      │  │  ┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐│   │   │
│  │  └──────────────┘  └──────────────┘  │  │WM││SM││RM││OM││HM││LK││AA││   │   │
│  │                                       │  └──┘└──┘└──┘└──┘└──┘└──┘└──┘│   │   │
│  │                                       └──────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│  ┌──────────────────────────────────────┴───────────────────────────────────┐   │
│  │  PROJECTION LAYER                                                        │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │   │
│  │  │  Workspace       │  │  Universal       │  │  Projection          │   │   │
│  │  │  Projection      │  │  Intent Pipeline │  │  Assembly            │   │   │
│  │  │  Engine          │  │                  │  │                      │   │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│  ┌──────────────────────────────────────┴───────────────────────────────────┐   │
│  │  SYNCHRONIZATION LAYER                                                    │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │   │
│  │  │  Cognitive       │  │  Client          │  │  State Sync         │   │   │
│  │  │  Event Bus       │  │  Registry        │  │  Protocol           │   │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│  ┌──────────────────────────────────────┴───────────────────────────────────┐   │
│  │  ERROR LAYER                                                             │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │   │
│  │  │  Failure         │  │  Degraded        │  │  Recovery            │   │   │
│  │  │  Detection       │  │  Mode Router     │  │  Verification        │   │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Active Attention** | The single object currently in focus |
| **Ambient Awareness** | Background objects that are important but not focused |
| **Attention Score** | Computed score determining what SHUNYA pays attention to |
| **Cognitive Event** | A canonical event emitted by any subsystem |
| **Context Transition** | Movement from one focused object to another |
| **Intent Pipeline** | The single path by which founder intent becomes action |
| **Living Workspace** | The center panel that renders the current object |
| **Memory Layer** | One of seven cognitive memory stores |
| **Object Lifecycle** | The 9-state state machine governing all objects |
| **Projection** | A snapshot of the cognitive state for workspace rendering |
| **Reality Runtime** | The subsystem that ingests real-world entities |
| **Relationship Graph** | The directed graph of connections between objects |
| **Universal Object Graph** | The complete graph of all objects in the system |
| **Workspace Projection** | The view model sent to the workspace renderer |
| **Workspace Synchronization** | Protocol for multiple clients observing one runtime |

## Appendix C: Cross-References

| Document | Reference |
|----------|-----------|
| Founder Workspace Specification | Defines the workspace layout that this runtime projects to |
| SHUNYA Core Models (A1.1) | Universal Object Model, Identity Model, Evidence Model |
| SHUNYA System Flow (A1.2) | Engine responsibilities, event flow, state machines |
| ES-001 (Governance) | Policy evaluation in the Intent Pipeline |
| ES-002 (Knowledge) | Long-term Knowledge promotion |
| ES-004 (Planner) | Recommendation generation |
| ES-005 (Executor) | Deterministic execution |
| ES-006 (Observer) | Observation ingestion |
| ES-007 (Learning) | Memory consolidation patterns |
| ES-009 (Context Fusion) | Context assembly for projection |
| Kernel Primitives | Object identity, space, relationship, registry |