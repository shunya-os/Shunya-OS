# Runtime Canon

> **Canonical Document · Phase C1**
> **Status: CANONICAL — Implementation-Independent Runtime Specification**
> **Version: 1.0**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Runtime Architecture Overview](#2-runtime-architecture-overview)
3. [Object Lifecycle Management](#3-object-lifecycle-management)
4. [Event System](#4-event-system)
5. [Workflow Runtime](#5-workflow-runtime)
6. [Timeline Engine](#6-timeline-engine)
7. [Execution Engine](#7-execution-engine)
8. [Observation Engine](#8-observation-engine)
9. [Runtime Governance](#9-runtime-governance)
10. [Runtime Pluggability](#10-runtime-pluggability)
11. [Future Extensibility](#11-future-extensibility)
12. [Relationship to Other Canonical Documents](#12-relationship-to-other-canonical-documents)

---

## 1. Purpose

This document defines the canonical runtime architecture of SHUNYA — how objects live, how events flow, how work executes, and how intelligence compounds. It is the dynamic companion to the static object model defined in the Business Canon and Universal Object Protocol.

The Runtime Canon is implementation-independent. It describes what the runtime does, not how it is implemented. Any runtime implementation (Flask, FastAPI, Rust, Go) must conform to this specification.

---

## 2. Runtime Architecture Overview

### 2.1 Runtime Layers

```
┌──────────────────────────────────────────────────────────────────┐
│                   EXPERIENCE LAYER                                 │
│  UI, API, CLI, Adapters — entry points for humans and systems     │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                              │
│  Routes requests to the correct engine, manages flow             │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER                              │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────┐    │
│  │ Observer │  │ Knowledge│  │ Reasoning  │  │  Planner     │    │
│  │ Engine   │  │ Engine   │  │ Engine     │  │  Engine      │    │
│  └──────────┘  └──────────┘  └────────────┘  └──────────────┘    │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────┐    │
│  │ Decision │  │Governance│  │  Learning  │  │  Temporal    │    │
│  │ Runtime  │  │ Engine   │  │  Engine    │  │  Intelligence │    │
│  └──────────┘  └──────────┘  └────────────┘  └──────────────┘    │
│                                                                   │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    EXECUTION LAYER                                 │
│  Commitments, Tasks, Workflows — work gets done                  │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                                   │
│  Objects, Events, Timeline, Audit — everything persists          │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Engine Dependency Graph

```
Identity Engine ──► Context Fusion ──► Observer Engine
                                          │
                                          ▼
                                    Knowledge Engine
                                          │
                                          ▼
                                    Reasoning Engine
                                          │
                                          ▼
                                     Planner Engine
                                          │
                                          ▼
                                    Governance Engine
                                          │
                                          ▼
                                    Decision Runtime
                                          │
                                          ▼
                                    Execution Engine
                                          │
                                          ▼
                                    Observer Engine (outcome)
                                          │
                                          ▼
                                    Learning Engine
                                          │
                                          ▼
                                    Doctor Engine (health, continuous)
```

All engines depend on:
- **Timeline Engine** — for event recording
- **Audit Engine** — for action logging

---

## 3. Object Lifecycle Management

### 3.1 The Object Factory

Every object in SHUNYA is created, managed, and retired by the Object Factory — the canonical lifecycle manager. The Object Factory is not a single class or service; it is the pattern by which objects enter, exist, and leave the system.

### 3.2 Creation

```
Actor → Create Request → Object Factory:
    1. Generate identity (object_id)
    2. Set mandatory fields (§3 of 04_universal_object_protocol.md)
    3. Attach provenance (who created, when, why, from what evidence)
    4. Attach initial evidence
    5. Set initial status (according to object type lifecycle)
    6. Record ObjectCreated timeline event
    7. Record creation in audit log
    8. Return created object
```

### 3.3 Modification

```
Actor → Update Request → Object Factory:
    1. Verify actor has permission
    2. Validate field mutations
    3. Create new version
    4. Preserve previous version as immutable snapshot
    5. Record ObjectModified timeline event
    6. Record modification in audit log
    7. Recalculate confidence if evidence changed
    8. Return updated object
```

### 3.4 State Transition

```
Actor → Status Change Request → Object Factory:
    1. Verify actor has permission
    2. Verify transition is valid (from lifecycle definition)
    3. Verify transition requirements are met (evidence sufficiency, etc.)
    4. Update status
    5. Record StatusChanged timeline event
    6. Record transition in audit log
    7. Trigger any lifecycle hooks (e.g., notification on Dormant)
    8. Return updated object
```

### 3.5 Deletion (Retirement)

```
Actor → Delete Request → Object Factory:
    1. Verify actor has delete permission
    2. Verify object is deletable (some objects are never deleted)
    3. Verify deletion requirements (no pending commitments, etc.)
    4. Mark as Deleted/Retired (not physically removed)
    5. Record ObjectDeleted timeline event
    6. Record deletion in audit log
    7. Object becomes read-only from this point
    8. Identity is retired (never reused)
```

---

## 4. Event System

### 4.1 Event Schema

Every event in the system follows the canonical event envelope:

```
Event {
    event_id: String (UUID v7)
    event_type: String  // From canonical event types
    event_version: Integer  // Schema version
    timestamp: ISO-8601
    source: String  // Which engine/component generated the event
    actor_id: ObjectID  // Who/what caused the event
    object_id: ObjectID  // The primary object the event is about
    related_object_ids: ObjectID[]  // Other objects involved
    payload: Map  // Event-specific data
    evidence_ids: String[]  // Evidence supporting this event
    priority: Enum  // Critical, High, Normal, Low
    ttl: Duration?  // Time after which the event is no longer relevant
}
```

### 4.2 Canonical Event Types

| Event Type | Description | Source |
|-----------|-------------|--------|
| `object.created` | A new object was created | Object Factory |
| `object.modified` | An object's fields were modified | Object Factory |
| `object.status_changed` | An object's lifecycle status changed | Object Factory |
| `object.deleted` | An object was deleted/retired | Object Factory |
| `relationship.added` | A relationship was created | Relationship Engine |
| `relationship.removed` | A relationship was removed | Relationship Engine |
| `evidence.attached` | Evidence was attached to an object | Evidence Engine |
| `evidence.superseded` | Evidence was superseded | Evidence Engine |
| `observation.created` | A new observation was recorded | Observer Engine |
| `observation.status_changed` | Observation lifecycle changed | Observer Engine |
| `decision.created` | A decision was initiated | Decision Runtime |
| `decision.status_changed` | Decision status changed | Decision Runtime |
| `commitment.created` | A commitment was made | Decision Runtime |
| `commitment.status_changed` | Commitment status changed | Decision Runtime |
| `task.completed` | A task was completed | Execution Engine |
| `workflow.completed` | A workflow completed | Execution Engine |
| `outcome.recorded` | An outcome was measured | Execution Engine |
| `knowledge.updated` | Knowledge was added or modified | Knowledge Engine |
| `memory.formed` | A new memory was created | Memory Engine |
| `human.action` | A human performed an action | Experience Layer |

### 4.3 Event Propagation

Events propagate through the system via the event bus:

```
Publisher → Event Bus → Subscribers
    (fire and forget)    (asynchronous, ordered per channel)
```

**Rules:**
- Events are published asynchronously (publisher does not wait for subscribers)
- Events within a channel (per object_id) are delivered in order
- Event delivery is at-least-once (duplicates are handled by idempotency)
- Failed event delivery goes to dead-letter queue
- Event retention is governed by data retention policy

### 4.4 Event Subscription

Engines subscribe to event types they care about:

| Engine | Subscribes To |
|--------|--------------|
| Observer Engine | All events |
| Knowledge Engine | observation.created, knowledge.updated |
| Reasoning Engine | observation.created, knowledge.updated |
| Planner Engine | decision.created, commitment.created |
| Governance Engine | decision.created, commitment.status_changed |
| Decision Runtime | observation.created, decision.status_changed |
| Execution Engine | commitment.created, task.completed |
| Learning Engine | outcome.recorded |
| Temporal Engine | All events (for timeline recording) |

---

## 5. Workflow Runtime

### 5.1 Workflow Definition

A Workflow is a directed graph of steps. Each step is a Task, a Decision, or a sub-Workflow.

```
Workflow {
    workflow_id: String (UUID)
    name: String
    description: String
    steps: Step[]
    transitions: Transition[]  // Step A → Step B (with conditions)
    start_step: StepID
    end_steps: StepID[]
    timeout: Duration?
    error_handling: ErrorPolicy
    version: Integer
}
```

### 5.2 Step Types

| Step Type | Description |
|-----------|-------------|
| **Task** | Execute a defined action |
| **Decision** | Make a choice (may require human approval) |
| **SubWorkflow** | Execute another workflow |
| **Wait** | Pause until a condition is met or timeout |
| **Parallel** | Execute multiple steps concurrently |
| **Condition** | Branch based on a condition |
| **Loop** | Repeat until a condition is met |

### 5.3 Workflow Execution

```
1. Workflow is activated (triggered by event or human)
2. Runtime loads the workflow definition
3. Start step is identified
4. Step is executed:
   a. Task: dispatched to Execution Engine
   b. Decision: dispatched to Decision Runtime
   c. SubWorkflow: spawned as child workflow
   d. Wait: suspended until condition met
   e. Parallel: spawn concurrent step executions
5. On step completion, transition to next step(s)
6. On all end steps completed, workflow is completed
7. Outcome is recorded
8. Learning signals are generated
```

### 5.4 Error Handling

| Error | Behavior |
|-------|----------|
| Step timeout | Retry (configurable count) → Escalate → Fail workflow |
| Step failure | Retry → Escalate to human → Fail workflow |
| Invalid transition | Log + Halt workflow → Escalate |
| Workflow timeout | Escalate to human → Force complete or fail |

---

## 6. Timeline Engine

### 6.1 Purpose

The Timeline Engine provides the universal timeline service used by every object. It is not a separate engine — it is a capability embedded in the runtime that every object uses.

### 6.2 Timeline Rules

- Every event on every object is recorded in that object's timeline
- Timeline events are immutable after recording
- Timeline events are ordered by timestamp within a single object
- Timeline events support full-text search
- Timeline supports time-range queries

### 6.3 Temporal Intelligence

The Timeline Engine feeds into the Temporal Intelligence system:

```
Timeline Engine
    │
    ├──► Snapshot Engine — captures point-in-time state of any object or aggregate
    │
    ├──► Trajectory Engine — detects movement patterns (improving, declining, stable)
    │
    ├──► Trend Engine — detects long-term patterns (9 types: linear, seasonal, cyclic, etc.)
    │
    └──► Forecast Engine — predicts future states based on trajectory + trends
```

---

## 7. Execution Engine

### 7.1 Purpose

The Execution Engine dispatches and monitors work. It does not do the work itself — it manages who does what, when, and with what result.

### 7.2 Execution Model

```
Commitment → Execution Engine → Task Queue → Actor(s) → Outcome
                │                                     │
                └───────── Monitor ───────────────────┘
                          │
                          ▼
                    Status Updates → Timeline Events
```

### 7.3 Actor Types

| Actor Type | Description |
|-----------|-------------|
| **Human** | A human performs the work |
| **AI** | An AI agent performs the work |
| **System** | The system performs the work automatically |
| **External** | An external system performs the work (via API) |
| **Delegated** | Work is delegated to another workflow or process |

### 7.4 Execution Lifecycle

```
Pending → Assigned → InProgress → Completed → Verified
    │                    │            │
    └──→ Cancelled       └──→ Failed  └──→ Outcome
```

### 7.5 Execution Monitoring

The Execution Engine continuously monitors:
- Progress against expected timeline
- Resource utilization
- Failure rates
- Bottlenecks (blocked tasks, waiting decisions)
- SLA compliance

---

## 8. Observation Engine

### 8.1 Purpose

The Observation Engine is the entry point for all reality into the system. Every external signal, every event, every change enters through the Observation Engine.

### 8.2 Observation Flow

```
External Signal
    │
    ▼
1. Capture — raw signal recorded with metadata
    │
    ▼
2. Validate — is the signal well-formed? From a known source?
    │
    ▼
3. Enrich — add context (source reliability, timeliness, etc.)
    │
    ▼
4. Classify — what type of observation is this?
    │
    ▼
5. Record — create Observation object
    │
    ▼
6. Publish — emit observation.created event
```

### 8.3 Observation Types

| Type | Description |
|------|-------------|
| **Direct** | Directly observed by a human or trusted sensor |
| **Indirect** | Reported by a second party |
| **Derived** | Computed from other observations |
| **Inferred** | Inferred by the Reasoning Engine |
| **External** | Received from an external system |
| **System** | Generated by the system itself |

### 8.4 Confidence in Observations

Every observation carries a confidence score derived from:
- Source reliability
- Observation freshness
- Evidence completeness
- Relationship consistency (does it match what we already know?)
- Conflict detection (does it contradict other observations?)

---

## 9. Runtime Governance

### 9.1 Governance Gates

The runtime enforces these governance gates at every critical action:

| Gate | Triggered By | What It Checks |
|------|-------------|----------------|
| **Permission Gate** | Every action | Does the actor have permission? |
| **Constitutional Gate** | Every action | Does this violate the Constitution? |
| **Policy Gate** | Decisions, Commitments | Does this comply with active policies? |
| **Evidence Gate** | Status transitions | Is sufficient evidence attached? |
| **Approval Gate** | High-impact actions | Has a human approved this? |
| **Quota Gate** | Resource-intensive actions | Are we within resource limits? |

### 9.2 Runtime Integrity

The runtime must guarantee:
- **No silent actions** — every action produces timeline events
- **No unlogged actions** — every action is in the audit log
- **No untracked state** — every object's state is versioned
- **No unrecoverable failures** — every failure has a defined recovery path
- **No unmonitored processes** — every execution is monitored

---

## 10. Runtime Pluggability

### 10.1 Engine Interface

Every engine implements the same contract:

```
Engine {
    engine_id: String
    engine_type: String
    status: Enum (active, paused, degraded, offline)
    initialize(): void
    shutdown(): void
    health_check(): HealthStatus
    handle_event(event): void
    get_capabilities(): Capability[]
}
```

### 10.2 Domain Adapters

Domain-specific logic is injected as adapters:

```
DomainAdapter {
    domain: String  // travel, healthcare, finance, etc.
    supported_object_types: String[]
    supported_workflows: String[]
    transform_input(object): DomainObject
    transform_output(domain_object): Object
    get_domain_policies(): Policy[]
}
```

---

## 11. Future Extensibility

### 11.1 New Engines

New engines can be added by:
1. Defining their position in the dependency graph
2. Implementing the Engine interface
3. Registering for relevant event types
4. Documenting their capabilities

### 11.2 Runtime Deployment Options

The runtime can be deployed as:
- **Monolith** — all engines in one process (development, small orgs)
- **Microservices** — each engine is a separate service (medium orgs)
- **Distributed** — engines across multiple data centers (large orgs, multi-tenant)

The architecture supports all three without code changes — only deployment configuration changes.

---

## 12. Relationship to Other Canonical Documents

| Document | Relationship |
|----------|-------------|
| **00_universal_ontology.md** | Runtime manages the lifecycle of Object, Entity, Event, Decision, Action, and Outcome — the dynamic layer of the ontology |
| **02_shunya_constitution.md** | Runtime enforces governance gates based on Constitution |
| **03_business_canon.md** | Runtime manages lifecycles of business objects |
| **04_universal_object_protocol.md** | Runtime protocol wraps all object interactions |
| **06_data_canon.md** | Data architecture supports runtime storage needs |
| **07_ai_canon.md** | AI behaviors are executed through the runtime |
| **08_experience_canon.md** | Experience layer calls runtime APIs |
| **09_repository_canon.md** | Repository structure maps to runtime layers |
| **10_migration_canon.md** | Migration operates through runtime lifecycle |
| **11_engineering_canon.md** | Engineering standards govern runtime implementation |
| **12_launch_roadmap.md** | Runtime completion is a core milestone |

---

> **Next:** [06_data_canon.md](06_data_canon.md)