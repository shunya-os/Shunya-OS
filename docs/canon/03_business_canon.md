# Business Canon — Universal Business Objects

> **Canonical Document · Phase C1**
> **Status: CANONICAL — Implementation-Independent**
> **Version: 2.0**

> **Foundation:** This document derives from [00_universal_ontology.md](00_universal_ontology.md). Every Business Object defined here has an **Ontological Parent** in that ontology. No Business Object may contradict its ontological primitive. See §2 for the derived hierarchy.

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Canonical Object Hierarchy](#2-canonical-object-hierarchy)
3. [Object Definitions](#3-object-definitions)
4. [Lifecycle Patterns](#4-lifecycle-patterns)
5. [Relationship Graph](#5-relationship-graph)
6. [AI Understanding](#6-ai-understanding)
7. [Timeline Behavior](#7-timeline-behavior)
8. [Ownership Model](#8-ownership-model)
9. [Permission Model](#9-permission-model)
10. [Future Extensibility](#10-future-extensibility)
11. [Relationship to Other Canonical Documents](#11-relationship-to-other-canonical-documents)

---

## 1. Purpose

This document defines every universal business object that SHUNYA recognizes. These objects are the vocabulary of reality — they are not database tables, not API endpoints, not UI components. They are **what things are**.

Every implementation, every schema, every API, every AI behavior derives from these definitions. No implementation may introduce a new fundamental object type without amending this document.

**Relationship to the Universal Ontology (00_universal_ontology.md):**

The Universal Ontology defines the fundamental primitives of reality — Entity, Identity, Relationship, Event, Observation, Evidence, Decision, Action, Outcome, Knowledge, Memory, Context, and Workspace. This Business Canon defines **concrete Business Objects** that are either:

- **Entity types** from the ontology (Human, Organization, Workspace, Document, FinancialObject) — these have independent existence in reality.
- **Non-Entity concepts** from the ontology represented as Business Objects (Identity, Relationship, Event, Observation, Evidence, Decision, Outcome, Knowledge, Memory) — these are always *of* or *about* Entities.
- **Derived Business Objects** not defined as ontological primitives (Conversation, Commitment, Task, Workflow) — these are composite or domain-specific Objects built from ontological primitives.

Every Business Object table below includes an **Ontological Parent** field that cites the exact section of the Universal Ontology from which it derives.

---

## 2. Canonical Object Hierarchy

```
                  Object (from Universal Ontology, §5)
                       │
          ┌────────────┴──────────────────┐
          │                                │
      Entity (from §3)           Non-Entity Concepts (from §5.4)
          │                                │
    ┌─────┼──────┐            ┌──────┬─────┼─────┬──────┐
    │     │      │            │      │     │     │      │
  Human  Org  Workspace    Identity  Event  Decision  Outcome
  Document  FinObj         Relationship  Observation  Evidence
                                    Knowledge  Memory

          ┌─────────────────────────┘
          │
          Derived Business Objects
          (composites of ontological primitives)
          ┌──────┬───────┬───────┬──────┐
          │      │       │       │      │
      Conversation  Commitment  Task  Workflow
```

**Key:**
- **Entity types** have independent existence in reality — they are the "who" and "what" of the system.
- **Non-Entity concepts** are ontological primitives that SHUNYA reasons about but that do not have independent existence — they are always *of* or *about* Entities.
- **Derived Business Objects** are composite Objects built from ontological primitives for domain-specific purposes.

All objects implement the Universal Object Protocol ([04_universal_object_protocol.md](04_universal_object_protocol.md)).

---

## 3. Object Definitions

Each object is defined by a canonical table. The required fields are:

| Field | Description |
|-------|-------------|
| **Purpose** | What this object *is* — its essential nature |
| **Ontological Parent** | Reference to the primitive in 00_universal_ontology.md that this object derives from |
| **Lifecycle** | The stages this object passes through from creation to retirement |
| **Relationships** | How this object connects to other objects |
| **AI Understanding** | What AI systems must understand about this object |
| **Timeline Behavior** | How this object generates timeline events |
| **Ownership** | Who or what owns this object |
| **Permissions** | Access control constraints |
| **Search behavior** | How this object can be discovered, found, and queried |
| **Evidence behavior** | How this object interacts with Evidence — what requires evidence, what serves as evidence |

---

### 3.1 Identity

| Property | Definition |
|----------|------------|
| **Purpose** | The permanent, unique designation of any entity in the system. Identity is not an account — it is the fundamental "who" or "what" that everything else attaches to. |
| **Ontological Parent** | [Identity — Non-Entity Concept (§4)](00_universal_ontology.md#4-identity) — Identity is the property of an Entity that makes it *this* Entity and not any other. The Business Object Identity is the system's representation of that ontological property. |
| **Lifecycle** | Created → Active → Merged/Split → Retired (never reused) |
| **Relationships** | Owns: Human, Organization. Owned By: Identity Authority. |
| **AI Understanding** | Identity is the anchor of all knowledge. AI must never confuse distinct identities. Identity is permanent and non-reusable. |
| **Timeline Behavior** | Identity creation is the first event in every object's timeline. Merges and splits are recorded as events. |
| **Ownership** | System-owned. No human or organization owns an identity — they are assigned one. |
| **Permissions** | Read: all. Write: Identity Engine only. Delete: never (can only be retired). |
| **Search behavior** | Identity is the canonical lookup key in the system. Search by identity ID must be exact — identity resolution is the foundation of all object reference. Fuzzy search is not permitted on identity; matches must be precise. Identity search returns exactly one result or none. Cross-reference search (find all objects associated with an identity) is supported. |
| **Evidence behavior** | Identity cannot be directly evidenced (it is assigned by the Identity Authority, not discovered). Identity merges and splits require authoritative Evidence from an Identity Authority or other trusted source. Identity verification of a Human may produce Evidence that links a Human to their identity. |

---

### 3.2 Human

| Property | Definition |
|----------|------------|
| **Purpose** | A human being known to the system. Not a "user" or "contact" — a human with identity, attributes, and relationships. A Human IS an Entity — it has independent existence in reality. |
| **Ontological Parent** | [Entity — Human Entity Type (§3.4)](00_universal_ontology.md#3-entity) — Human is a canonical Entity type. As an Entity, a Human has Existence, Persistence, Distinctness, Identity, Attributes, and Relationships. |
| **Lifecycle** | Observed → Recognized → Known → Verified → Departed |
| **Relationships** | Has: Identity. Member of: Organization. Participant in: Conversation, Commitment, Decision. |
| **AI Understanding** | Humans are the reason the system exists. Every Human represents a real person with agency, privacy rights, and dignity. A Human Entity is not the same as a "user" account. |
| **Timeline Behavior** | Every interaction with a Human is recorded as timeline events. Lifecycle transitions are major events. |
| **Ownership** | Self-owned. A Human's core profile is owned by the Human themselves. |
| **Permissions** | Read: Human themselves + orgs they belong to. Write: Human themselves (attributes), Identity Engine (status). |
| **Search behavior** | Search by name, known attributes, organizational membership, relationship proximity to other Humans or Objects. Fuzzy matching is allowed (names have variations). Identity-backed disambiguation: when fuzzy search returns multiple candidates, identity provides exact resolution. Temporal search (find Humans active during a time period) supported. |
| **Evidence behavior** | Human existence and attributes can be supported by Evidence. Identity verification requires Evidence (credential, attestation, biometric verification). Profile attribute changes (name, contact, role) should be accompanied by Evidence of the change. A Human can serve as a Source of Evidence for other objects. |

---

### 3.3 Organization

| Property | Definition |
|----------|------------|
| **Purpose** | A group of Humans organized around a common purpose. Organizations are containers — they exist to structure relationships, permissions, and work. |
| **Ontological Parent** | [Entity — Organization Entity Type (§3.4)](00_universal_ontology.md#3-entity) — Organization is a canonical Entity type. As an Entity, it has Identity, Attributes, Relationships, and persists across time. |
| **Lifecycle** | Formed → Active → Restructuring → Dormant → Dissolved |
| **Relationships** | Has: Members (Humans). Has: Workspaces. Has: Policies. Owns: Commitments, Decisions, Documents. |
| **AI Understanding** | Organizations are the context for collective work. An Organization is not a Human — it has different rights, permissions, and lifecycle. Organizational decisions are collective, not individual. |
| **Timeline Behavior** | Major events: formation, membership changes, restructuring, dissolution. |
| **Ownership** | Owned by its founding Human or designated governing body. |
| **Permissions** | Read: members + public. Write: designated administrators. Membership: governed by Organization policy. |
| **Search behavior** | Search by name, domain, industry, member count, location, or status. Hierarchical search (parent Organization → child departments/teams). Membership queries (find all Humans in an Organization). Temporal search for organizational state at a point in time. |
| **Evidence behavior** | Organizational attributes (legal registration, policies, membership records, structural decisions) should be supported by Evidence. Membership changes should be evidenced (join request, invitation, termination record). Organizational decisions require Evidence of the decision-making process. |

---

### 3.4 Workspace

| Property | Definition |
|----------|------------|
| **Purpose** | A bounded context for work, collaboration, and knowledge. Workspaces are the primary way Humans organize their interaction with SHUNYA. A Workspace IS an Entity — it has its own Identity, State, Relationships, and Lifecycle. |
| **Ontological Parent** | [Workspace (§17)](00_universal_ontology.md#17-workspace) — Workspace is an ontological primitive: a bounded context within which Entities collaborate, make Decisions, and build Knowledge. A Workspace is also an Entity type (§3.4). |
| **Lifecycle** | Draft → Active → Dormant → Archived → Historical |
| **Relationships** | Belongs to: Organization or Human. Contains: Conversations, Documents, Tasks, Decisions, Commitments, Knowledge, Observations. Provides Context for all contained Objects. |
| **AI Understanding** | Workspaces define the scope of AI attention and the boundary of Context. The AI must understand which Workspace it is in and respect its boundaries. Contents of one Workspace are isolated from another unless explicitly shared. |
| **Timeline Behavior** | Full timeline of creation, active periods, archival, and reactivation. Membership changes are timeline events. |
| **Ownership** | Owned by the creating Human or Organization. |
| **Permissions** | Read: members. Write: members with appropriate role. Admin: workspace owner. |
| **Search behavior** | Search by name, membership, contained object types, creation date, activity level. Workspace boundaries constrain all search within them — queries default to the current Workspace unless cross-workspace search is explicitly authorized. Full-text search across all contained Objects. |
| **Evidence behavior** | Workspace creation and configuration may require Evidence of authorization (organizational policy, owner consent). Workspace membership changes can be supported by Evidence. Workspace serves as the boundary within which Evidence is collected and evaluated — Evidence from outside the Workspace may need explicit import. |

---

### 3.5 Relationship

| Property | Definition |
|----------|------------|
| **Purpose** | A typed connection between two UniversalObjects. Relationships are the structure of reality — they describe how things relate to each other. A Relationship is a Non-Entity Object: it is always *between* Entities, not itself an Entity. |
| **Ontological Parent** | [Relationship (§6)](00_universal_ontology.md#6-relationship) — A directed, typed connection between two Objects with Directionality, Typedness, Time-boundedness, and Strength. |
| **Lifecycle** | Proposed → Active → Superseded → Ended |
| **Relationships** | Connects: any two UniversalObjects (source → target). Type: defined by relationship taxonomy. |
| **AI Understanding** | Relationships are directional, typed, and time-bound. The AI must understand the type and strength of relationships when reasoning. A Relationship is not an attribute — it connects two distinct Objects. |
| **Timeline Behavior** | Full timeline: creation, strength changes, type changes, supersession, ending. |
| **Ownership** | Owned by the source object's owner. |
| **Permissions** | Read: both endpoints' owners. Write: source owner. |
| **Search behavior** | Search by source, target, type, strength range, time range (active during period). Graph traversal queries: find paths between any two Objects, shortest path, all relationships of a given type for an Object. Relationship type taxonomy browsing. Temporal queries for relationship state at a point in time. |
| **Evidence behavior** | Relationships can be supported by Evidence (e.g., a contract Document proving a Human works for an Organization). Relationship strength may be derived from Evidence weight. A Relationship can itself serve as Evidence for other inferences (e.g., a membership relationship implies certain permissions). Relationship termination should be evidenced. |

---

### 3.6 Conversation

| Property | Definition |
|----------|------------|
| **Purpose** | A sequence of messages between two or more participants (Human or AI). Conversations are the primary communication channel and the context in which meaning is co-created. |
| **Ontological Parent** | [Object (§5)](00_universal_ontology.md#5-object) — Conversation is a derived Business Object not defined as an ontological primitive. It is a composite Object built from Events (messages), Participants (Entities), and Relationships (participant-to-conversation). |
| **Lifecycle** | Initiated → Active → Idle → Archived → Deleted |
| **Relationships** | Participants: Humans, AI. References: Documents, Decisions, Commitments, Observations. |
| **AI Understanding** | Conversations are context-rich. The AI must understand the full conversation history, not just the latest message. Each message is an Event. The conversation as a whole is a Relationship container. |
| **Timeline Behavior** | Every message is a timeline event. Conversation lifecycle is separate from individual message timeline. |
| **Ownership** | Owned collectively by participants. |
| **Permissions** | Read: participants. Write: participants. Add participant: existing participants. |
| **Search behavior** | Full-text search across all messages in the Conversation. Search by participant, date range, topic tags, referenced Objects (Documents, Decisions, etc.). Semantic search supported for meaning-based retrieval. Threaded search within replies. Time-range queries for conversation activity patterns. |
| **Evidence behavior** | Messages in a Conversation can serve as Evidence for Observations, Decisions, or Relationships. A Conversation is not itself Evidence but contains evidentiary content. Key messages (decisions made, commitments stated) may be extracted as Evidence for their respective Objects. Conversation participants serve as Sources for Evidence extracted from messages. |

---

### 3.7 Commitment

| Property | Definition |
|----------|------------|
| **Purpose** | A promise to perform a specific action or achieve a specific outcome. Commitments are the bridge between decision and execution — they make intention actionable. |
| **Ontological Parent** | [Object (§5)](00_universal_ontology.md#5-object) — Commitment is a derived Business Object not defined as an ontological primitive. It is a composite of a Decision (the choice to commit) and an Action (the promised execution), linked by a Relationship between the promiser and the promisee. |
| **Lifecycle** | Proposed → Accepted → Active → In Progress → Completed → Verified → Failed → Cancelled |
| **Relationships** | Originates from: Decision. Assigned to: Human or AI. Relates to: Task, Outcome. |
| **AI Understanding** | Commitments are binding. The AI must track commitment status and alert on deadlines. A Commitment is not a Task — it is a promise that may generate Tasks. |
| **Timeline Behavior** | Full lifecycle timeline with status transitions. Deadlines are milestone events. |
| **Ownership** | Owned by the assignee. |
| **Permissions** | Read: commitment participants + workspace members. Write: assignee, manager, or governance. |
| **Search behavior** | Search by assignee, status, deadline range, originating Decision, related Outcome. Deadline-based alerts and proximity searches (commitments due soon). Overdue commitment queries. Commitment density search (how many commitments per Human or Workspace). |
| **Evidence behavior** | Commitment creation should be supported by Evidence (the Decision or conversation that produced it). Commitment fulfillment (completion) should be evidenced by the deliverable or outcome. Missed commitments generate Evidence of failure for Outcome evaluation. The Commitment itself can serve as Evidence of intent for Decision tracking. |

---

### 3.8 Task

| Property | Definition |
|----------|------------|
| **Purpose** | A discrete unit of work with a defined outcome. Tasks are the atomic unit of execution — the smallest trackable unit of work that can be assigned, completed, and verified. |
| **Ontological Parent** | [Object (§5)](00_universal_ontology.md#5-object) — Task is a derived Business Object not defined as an ontological primitive. It is a composite of Action (the work to be performed), Outcome (the expected result), and Relationship (assignment to an Actor). |
| **Lifecycle** | Created → Ready → Assigned → In Progress → Completed → Verified → Cancelled |
| **Relationships** | Belongs to: Workflow, Commitment, or Workspace. Assigned to: Human or AI. Depends on: other Tasks. |
| **AI Understanding** | Tasks are the smallest trackable unit of work. The AI should understand dependencies, deadlines, priorities, and assignment. Task completion triggers downstream effects. |
| **Timeline Behavior** | Status changes, time tracking, and dependency resolution are timeline events. |
| **Ownership** | Owned by assignee. |
| **Permissions** | Read: workspace members. Write: assignee or manager. |
| **Search behavior** | Search by assignee, status, priority, deadline, dependency relationships, workflow membership. Dependency graph queries (blocked-by, blocking). Work breakdown queries (parent task → subtasks). Time-in-status queries. |
| **Evidence behavior** | Task completion requires Evidence of the completed work (deliverable, verification, acceptance). Status transitions (especially to Completed or Verified) may require supporting Evidence. Task creation should be evidenced by its source (Decision, Commitment, Workflow). A completed Task serves as Evidence for Workflow progress or Outcome achievement. |

---

### 3.9 Event

| Property | Definition |
|----------|------------|
| **Purpose** | Something that happens at a point in time. Events are the atoms of the timeline — everything that happens is an Event. Events are immutable: once they occur, they cannot be un-occurred. |
| **Ontological Parent** | [Event (§8)](00_universal_ontology.md#8-event) — An Event is an ontological primitive: something that happens at a point in time, with Occurrence, Immutability, Atomicity, and Causality. Every Event is caused by an Action or another Event. |
| **Lifecycle** | Scheduled → Occurring → Occurred → Recorded → Superseded |
| **Relationships** | Generated by: Object, System, Human. Consumed by: Timeline, Observer Engine. |
| **AI Understanding** | Events are the primary input to the intelligence loop. The AI must understand the event type, context, and significance. Events are immutable — the timeline is the truth. |
| **Timeline Behavior** | Events ARE the timeline. Every event has a timestamp and is immutable after recording. Events form causal chains. |
| **Ownership** | Owned by the generating entity. |
| **Permissions** | Read: all authorized. Write: system only (Humans create events indirectly through actions). |
| **Search behavior** | Search by time range (before, after, between), event type, source Object, causality chain (what caused this Event, what Events did it cause). Timeline queries are deterministic — results are identical across queries for the same parameters. Pattern detection queries (event sequences, frequency analysis). |
| **Evidence behavior** | Events are the subject of Evidence. An Event cannot itself be Evidence — it is what happens, not a record of what happened. Observations (see §3.10) are the records of Events. Evidence supports or contradicts the Observation of an Event. The Event's occurrence is the truth against which Evidence is measured. |

---

### 3.10 Observation

| Property | Definition |
|----------|------------|
| **Purpose** | An Event that has been captured and recorded by the system. Observations are the raw material of intelligence — they are how reality enters SHUNYA. An Observation can be mistaken (the Event may not have occurred as observed). |
| **Ontological Parent** | [Observation (§9)](00_universal_ontology.md#9-observation) — An Observation is an ontological primitive: an Event that has been captured and recorded, with Derivation, Recording, Fallibility, and Timeliness properties. |
| **Lifecycle** | Detected → Validated → Active → Superseded → Archived |
| **Relationships** | Originates from: Event. Supported by: Evidence. Consumed by: Knowledge Engine, Reasoning Engine. |
| **AI Understanding** | Observations are the system's view of reality. The AI must understand confidence levels and evidence backing. An Observation is not fact — it is a recorded perception that may be wrong. |
| **Timeline Behavior** | Observation creation is an event. Status changes are timeline events. Observation capture time may differ from Event occurrence time. |
| **Ownership** | System-owned. |
| **Permissions** | Read: all authorized. Write: Observer Engine only. |
| **Search behavior** | Search by observed Event, capture time range, confidence range, source system, validation status. Time-window queries for pattern detection across multiple Observations. Cross-referencing queries (find all Observations of the same Event type). |
| **Evidence behavior** | Observations are supported by Evidence. An Observation without supporting Evidence has low confidence and may be provisional. Observations can serve as input to Evidence chains (an Observation can be used as Evidence for a Decision). Evidence can upgrade an Observation's confidence level or contradict it, triggering re-observation. |

---

### 3.11 Evidence

| Property | Definition |
|----------|------------|
| **Purpose** | Information that supports or contradicts an Observation, a Fact, or a Decision. Evidence is the foundation of confidence — without Evidence, nothing is certain. Evidence is append-only and forms chains. |
| **Ontological Parent** | [Evidence (§10)](00_universal_ontology.md#10-evidence) — Evidence is an ontological primitive: information that supports or contradicts, with Supportiveness, Gradability, Appendability, Chainability, and Source-dependence. |
| **Lifecycle** | Collected → Verified → Supporting → Contradicted → Superseded |
| **Relationships** | Supports: Observation, Fact, Decision. Originates from: Source (Human, System, External). |
| **AI Understanding** | Evidence is the basis of confidence. The AI must weigh evidence quality and source reliability. Evidence can be strong or weak, and can support or contradict. |
| **Timeline Behavior** | Evidence collection timestamp is the most critical metadata. Evidence chains form over time. |
| **Ownership** | Owned by the source. |
| **Permissions** | Read: all authorized. Write: append-only (evidence cannot be modified, only superseded). |
| **Search behavior** | Search by subject (what it supports or contradicts), source, collection time range, type (document, testimony, sensor data), strength range. Evidence chain queries (find all Evidence supporting a given Observation, recursively). Source reliability filtering. |
| **Evidence behavior** | Evidence IS the behavior. This object defines the mechanism by which all other objects gain or lose confidence. Key properties: (1) Evidence supports or contradicts — it is directional; (2) Evidence is gradable — strength is quantified; (3) Evidence is append-only — once added it cannot be removed; (4) Evidence forms chains — Evidence can support other Evidence; (5) Every piece of Evidence has a Source. |

---

### 3.12 Document

| Property | Definition |
|----------|------------|
| **Purpose** | A persistent, structured collection of information. Documents are how humans organize and share knowledge. A Document IS an Entity — it has independent existence, identity, state, and relationships. |
| **Ontological Parent** | [Entity — Document Entity Type (§3.4)](00_universal_ontology.md#3-entity) — Document is a canonical Entity type. As an Entity, it has Identity, Attributes (content, format), Persistence, and Relationships. |
| **Lifecycle** | Draft → Review → Published → Archived → Superseded |
| **Relationships** | Authored by: Human. Contains: Knowledge. References: Objects, Events, Decisions. |
| **AI Understanding** | Documents are both sources of knowledge and objects of processing. The AI can read, summarize, extract from, and generate documents. Document authorship and versioning matter. |
| **Timeline Behavior** | Version history is a timeline. Each edit is a timeline event. Document lifecycle transitions are major events. |
| **Ownership** | Owned by author or organization. |
| **Permissions** | Read: workspace members. Write: author or editor. Publish: authorized role. |
| **Search behavior** | Full-text search across content and metadata. Search by author, creation/modification date, tags, referenced Objects, document type, publication status. Version history search (find content as of a specific version). Semantic similarity search across document corpus. |
| **Evidence behavior** | Documents frequently serve as Evidence for Observations, Facts, and Decisions. A Document's content can be cited as Evidence (with specific section or paragraph references). Document authenticity may itself require Evidence (provenance chain, digital signature). Documents can be placed in an Evidence chain as supporting material for a Decision or Observation. |

---

### 3.13 FinancialObject

| Property | Definition |
|----------|------------|
| **Purpose** | Any object representing financial value, obligation, or transaction. FinancialObjects are the universal representation of economic activity — currency, invoices, payments, budgets, financial instruments. |
| **Ontological Parent** | [Entity — FinancialObject Entity Type (§3.4)](00_universal_ontology.md#3-entity) — FinancialObject is a canonical Entity type. As an Entity, it has Identity, Attributes (amount, currency, parties), Persistence, and Relationships. |
| **Lifecycle** | Initiated → Pending → Settled → Reconciled → Disputed → Resolved |
| **Relationships** | Relates to: Commitment, Decision, Organization, Human. |
| **AI Understanding** | Financial data requires high confidence and strict audit trails. The AI must handle financial data with appropriate caution — precision is mandatory, and all financial operations must be traceable. |
| **Timeline Behavior** | Every financial event is a critical timeline entry. Double-entry semantics preserved. Reconciliation is a timeline-spanning process. |
| **Ownership** | Owned by the organization or Human responsible for the financial obligation. |
| **Permissions** | Read: restricted (financial data is sensitive). Write: highly restricted. Admin: finance role. |
| **Search behavior** | Search by financial type (invoice, payment, budget), amount range, currency, date range, involved parties, status. Audit-trail queries — every state change must be fully traceable. Strict precision requirements: monetary amounts must be exact to the smallest currency unit. Reconciliation queries (match payments to invoices). |
| **Evidence behavior** | Financial transactions REQUIRE Evidence (receipts, invoices, approvals, bank records). Every FinancialObject state change must be supported by Evidence for audit compliance. Evidence chains for FinancialObjects must be complete — a gap in the Evidence chain breaks reconciliation. Financial Evidence has strict retention requirements. |

---

### 3.14 Decision

| Property | Definition |
|----------|------------|
| **Purpose** | A choice made by a Human or AI, recorded with all supporting context. Decisions are the central unit of intelligence — they connect observations to outcomes. A Decision involves agency, alternatives, and intentionality. |
| **Ontological Parent** | [Decision (§11)](00_universal_ontology.md#11-decision) — Decision is an ontological primitive: a choice made by an Entity among alternatives, with Agency, Alternatives, Intentionality, Consequentiality, and Recordability. |
| **Lifecycle** | Candidate → Evaluating → Under Review → Approved → Executing → Completed → Failed → Superseded |
| **Relationships** | Originates from: Insight, Observation, Human, AI. Generates: Commitment, Action. Evaluated by: Policy Engine. Supported by: Evidence. |
| **AI Understanding** | Decisions are the core of the intelligence loop. The AI must understand the full decision context: what was decided, why, with what confidence, what alternatives were considered, and what the outcome was. |
| **Timeline Behavior** | Full lifecycle with status transitions. Every review, approval, and outcome is a timeline event. Decision-to-outcome latency is tracked. |
| **Ownership** | Owned by the decision-maker. |
| **Permissions** | Read: decision participants + workspace. Write: decision-maker. Approve: designated approver. |
| **Search behavior** | Search by decider, date, status, referenced Observations and Evidence. Full context retrieval: what was decided, why, what alternatives were considered, what Evidence was weighed. Impact queries: what Commitments, Actions, and Outcomes resulted from this Decision. Decision chain queries (decisions that led to decisions). |
| **Evidence behavior** | Decisions MUST be supported by Evidence — the Observations and reasoning that led to the choice. Without supporting Evidence, a Decision is a mere assertion. The Decision itself generates Evidence for Outcome evaluation (the Decision is evidence of intent). Every Decision should have a traceable Evidence chain from Observation through reasoning to choice. |

---

### 3.15 Workflow

| Property | Definition |
|----------|------------|
| **Purpose** | A sequence of Tasks and Decisions that produce a defined Outcome. Workflows are how work gets done — they structure execution from initiation to completion. |
| **Ontological Parent** | [Object (§5)](00_universal_ontology.md#5-object) — Workflow is a derived Business Object not defined as an ontological primitive. It is a composite of ordered Actions (Tasks), Decision Points, and their Relationships, designed to produce an Outcome. |
| **Lifecycle** | Defined → Activated → Running → Suspended → Completed → Failed → Archived |
| **Relationships** | Contains: Tasks, Decisions. Triggers: Events. Orchestrates: Commitments. |
| **AI Understanding** | Workflows are the structure of execution. The AI should understand where each workflow is in its lifecycle, what stage is active, what decisions are pending, and what tasks are blocked. |
| **Timeline Behavior** | Workflow progress is a timeline. Each task completion is a milestone event. Workflow lifecycle transitions are major events. |
| **Ownership** | Owned by the workflow definer. |
| **Permissions** | Read: workspace members. Write: workflow designer. Execute: authorized actors. |
| **Search behavior** | Search by name, status, containing Tasks and Decisions, associated Workspace. Progress queries: how far along is this Workflow, what percentage of Tasks are complete. Instance history search across all runs of a Workflow definition. Bottleneck queries (stages with longest duration). |
| **Evidence behavior** | Workflow state transitions can be supported by Evidence (approval for stage progression, completion evidence for Task completion). Workflow completion Evidence feeds Outcome measurement. Workflow definitions themselves may be Evidence-backed (approved process documents, SOPs). Deviations from defined Workflow require Evidence of authorization. |

---

### 3.16 Memory

| Property | Definition |
|----------|------------|
| **Purpose** | A durable record of past interactions, patterns, and lessons that SHUNYA retains across sessions. Memory is the system's experience — "what happened" rather than "what is true." Memory is experiential, contextual, and subject to decay. |
| **Ontological Parent** | [Memory (§15)](00_universal_ontology.md#15-memory) — Memory is an ontological primitive: the system's retained experience, with Experience-dependence, Decay, Consolidation, Subjectivity, and Forgetability. |
| **Lifecycle** | Formed → Consolidated → Strengthened → Fading → Archived |
| **Relationships** | Derived from: Observations, Events, Outcomes. Relates to: Knowledge, Human (as subject). |
| **AI Understanding** | Memory is distinct from Knowledge. Memory is experiential ("what happened") while Knowledge is structural ("what is true"). Memory may decay or be forgotten; Knowledge persists until superseded. |
| **Timeline Behavior** | Memory formation, consolidation, and decay are timeline events. Memory strength changes over time. |
| **Ownership** | Owned by the subject (Human or Organization). |
| **Permissions** | Read: subject. Write: Memory Engine. Delete: subject (right to be forgotten). |
| **Search behavior** | Search by subject, time range, memory type (interaction, pattern, lesson), consolidation state. Associative recall: retrieve Memories related to a given context or Object. Decay-weighted search: recent and reinforced Memories rank higher. Emotional salience filtering. |
| **Evidence behavior** | Memory is derived from Experience (Events, Observations, Outcomes). Evidence can reinforce Memory (increasing consolidation strength) or contradict it (triggering re-evaluation and potential decay). Memory without supporting Evidence has lower confidence and is more susceptible to decay. Forgetting (Memory deletion) may be evidenced by a right-to-be-forgotten request. |

---

### 3.17 Knowledge

| Property | Definition |
|----------|------------|
| **Purpose** | A verified fact or relationship that the system holds as true. Knowledge is the system's understanding of reality — the product of reasoning over Observations and Evidence. Knowledge is structural, verified, and organized. |
| **Ontological Parent** | [Knowledge (§14)](00_universal_ontology.md#14-knowledge) — Knowledge is an ontological primitive: verified, structured information that the system holds as true, with Verification, Structure, Confidence, Derivation, and Supersedability. |
| **Lifecycle** | Hypothesized → Validated → Established → Challenged → Superseded |
| **Relationships** | Supported by: Evidence. Belongs to: Knowledge Domain. References: Objects. |
| **AI Understanding** | Knowledge is the highest-confidence representation of reality. The AI must prefer Knowledge over raw Observations when both are available. Knowledge can be challenged and superseded by better Knowledge. |
| **Timeline Behavior** | Knowledge discovery, validation, and supersession are timeline events. Knowledge age affects confidence. |
| **Ownership** | System-owned (knowledge is objective) or Human-owned (personal knowledge). |
| **Permissions** | Read: all authorized. Write: Knowledge Engine + authorized humans. |
| **Search behavior** | Search by domain, confidence level, supporting Evidence count, referenced Objects. Factual queries: what does the system know about X? Derivation-chain queries: trace Knowledge back through its Evidence chain to original Observations. Knowledge gap queries: what is not yet known about a topic. |
| **Evidence behavior** | Knowledge REQUIRES Evidence for validation and maintenance. Every Knowledge claim should be traceable to its supporting Evidence chain. Knowledge that loses Evidence support (because Evidence is contradicted or superseded) becomes suspect and may be reclassified as Hypothesis. New Evidence can challenge established Knowledge, triggering re-validation. |

---

### 3.18 Outcome

| Property | Definition |
|----------|------------|
| **Purpose** | The measurable result of a Decision, Commitment, or Workflow. Outcomes close the intelligence loop — they connect intention to result and enable learning. An Outcome is the state of the world after an Action, measured against the intended state. |
| **Ontological Parent** | [Outcome (§13)](00_universal_ontology.md#13-outcome) — Outcome is an ontological primitive: the state of the world after an Action or set of Actions, measured against the intended state, with Measurability, Relationality, Temporality, and Learning-potential. |
| **Lifecycle** | Expected → Measured → Verified → Reported → Learned |
| **Relationships** | Results from: Decision, Commitment, Workflow. Generates: Learning (for Knowledge Engine, Memory). |
| **AI Understanding** | Outcomes are how the system learns. The AI must correlate outcomes with predictions and decisions. The gap between expected and actual outcome is the most important signal. |
| **Timeline Behavior** | Outcome measurement is a key timeline event. Comparison with expected outcome is a derived event. Outcome-to-learning latency is tracked. |
| **Ownership** | Owned by the decision-maker or executor. |
| **Permissions** | Read: decision participants + workspace. Write: Outcome Engine. |
| **Search behavior** | Search by associated Decision, Commitment, or Workflow. Measured value range queries (outcomes within certain thresholds). Date range queries. Intention alignment search (outcomes that met/exceeded/fell short of expectations). Comparative queries: expected vs actual outcome side-by-side. |
| **Evidence behavior** | Outcome measurement REQUIRES Evidence of the resulting state. Without Evidence, an Outcome is just an assertion. Outcome is the terminal point of the Evidence chain: Decision → Action → Outcome. The Evidence chain must be traceable from the originating Decision through all intermediate steps to the measured Outcome. Outcome Evidence feeds the Learning loop. |

---

## 4. Lifecycle Patterns

### 4.1 Standard Lifecycle States

Every object uses a subset of these states (Lifecycle is itself an expression of the **State** ontological primitive — the state of an Object at a point in time):

| State | Meaning | Immutable? | Append-only? |
|-------|---------|-----------|-------------|
| Draft/Proposed/Initiated | Object exists but is not yet active | Yes | Yes |
| Active/Running/InProgress | Object is in use | No | Yes |
| Pending/Waiting | Object is waiting for something | No | Yes |
| Superseded/Replaced | Object has been replaced by a newer version | Yes | Yes |
| Archived | Object is no longer active but retained | Yes | Yes |
| Deleted/Retired | Object is no longer available | Yes | Yes |
| Failed/Cancelled | Object did not complete successfully | Yes | Yes |

### 4.2 Transition Rules

- All transitions must be valid (defined by object type)
- Invalid transitions are rejected by the runtime
- Every transition is recorded as a **Event** (from the ontology — see §3.9)
- Transitions requiring Evidence must have it attached before proceeding
- Lifecycle state is part of the Object's **State** (from the ontology — see §7 of 00_universal_ontology.md)

---

## 5. Relationship Graph

The graph below shows the primary relationship paths between Business Objects. Every edge is a **Relationship** (from the ontology, §6) with a specific type, direction, and time-boundedness.

```
   Identity ──── Human ──── Organization
       │          │  │  │        │
       │          │  │  │        │
       │          │  │  └─── Workspace
       │          │  │            │
       │          │  │     ┌──────┼──────┐
       │          │  │     │      │      │
       │          │  │  Conversation  │  Knowledge
       │          │  │     │          │      │
       │          │  │   Decision ────┘      │
       │          │  │     │                 │
       │          │  │  Commitment ──────────┘
       │          │  │     │
       │          │  │  ┌──┴──┐
       │          │  │  │     │
       │          │  │ Task Outcome
       │          │  │              │
       │          │  └────── Event ──┘
       │          │            │
       └──────────┼───── Observation
                  │            │
                  └────── Evidence
                  │
             FinancialObject
                  │
              Workflow
                  │
              Memory
```

**Relationship types include:** membership, ownership, assignment, derivation, reference, support, containment, participation, generation, evaluation.

---

## 6. AI Understanding

Per-object AI Understanding requirements are defined in each object's definition table in [§3](#3-object-definitions). These describe what an AI system must understand about each object's nature, constraints, and behavior.

**Comprehensive AI behavior guidelines — including how AI systems reason about, manipulate, and interact with these objects — are defined in [07_ai_canon.md](07_ai_canon.md).** That document covers:

- How AI engines (Observer, Reasoner, Decision Engine, Memory Engine) operate on these objects
- Confidence propagation through object relationships
- AI decision-making with Evidence and Knowledge
- AI responsibility boundaries for each object type
- Human oversight requirements for AI actions

> **Note:** This document defines what objects *are*; 07_ai_canon.md defines how AI *behaves* toward them. The two are complementary — do not duplicate AI behavioral guidelines here.

---

## 7. Timeline Behavior

Every object has a timeline. The timeline is composed of **Events** (from the ontology, §8):

- **Append-only** — events can be added but never removed
- **Immutable** — once recorded, an event cannot be modified
- **Ordered** — events have a monotonically increasing timestamp
- **Searchable** — timeline can be queried by time range, event type, and related objects
- **Causal** — events form causal chains that can be traced forward and backward

### 7.1 Required Timeline Events

| Lifecycle Stage | Required Timeline Event |
|----------------|------------------------|
| Object creation | ObjectCreated |
| Status transition | StatusChanged (old → new) |
| Attribute change | AttributeModified |
| Relationship change | RelationshipAdded / RelationshipRemoved |
| Evidence addition | EvidenceAttached |
| Action performed | ActionExecuted |
| Decision made | DecisionRecorded |
| Object deletion | ObjectDeleted / ObjectRetired |

### 7.2 Timeline as Evidence

The timeline itself serves as Evidence for what happened, in what order, and when. Timeline events are the raw material from which Observations are made and Knowledge is derived. The integrity of the timeline is foundational to the system's truth model.

---

## 8. Ownership Model

| Owner Type | Can Own | Cannot Own |
|-----------|---------|------------|
| **Human** | Personal objects, documents, conversations, decisions | System objects, organizational policies |
| **Organization** | Workspaces, policies, organizational documents, commitments | Human identities, personal memories |
| **AI/System** | Observations, evidence, knowledge, system events | Human decisions, human commitments |
| **Shared** | Workspace objects, collaborative documents | Identity, personal data |

### 8.1 Ownership Transfer

- Ownership can be transferred only with the current owner's consent
- System objects cannot be transferred
- Ownership transfer is recorded as a timeline event
- Ownership transfer may require Evidence of authorization

---

## 9. Permission Model

### 9.1 Canonical Roles

| Role | Scope | Abilities |
|------|-------|-----------|
| **Owner** | Individual object | Full control |
| **Admin** | Organization or Workspace | Manage roles, settings, policies |
| **Member** | Organization or Workspace | Read, create, edit within scope |
| **Contributor** | Workspace | Create and edit assigned objects |
| **Viewer** | Workspace | Read-only |
| **System** | Global | System operations |

### 9.2 Permission Inheritance

Permissions flow downward:
- Organization → Workspace → Objects within Workspace
- A Human's permissions in an Organization apply to all Workspaces unless overridden

### 9.3 Permission-Evidence Relationship

- Permission grants may require Evidence of authorization
- Access decisions should be auditable through timeline events
- Permission violations generate Events that feed the Observation system

---

## 10. Future Extensibility

### 10.1 Adding New Business Objects

A new business object may be added by:
1. Determining its **Ontological Parent** from 00_universal_ontology.md
2. Defining its purpose, lifecycle, relationships, AI understanding, timeline behavior, ownership, permissions, search behavior, and evidence behavior
3. Ensuring it inherits from its ontological parent (via 04_universal_object_protocol.md)
4. Ensuring it does not duplicate an existing object
5. Amending this document

### 10.2 Domain-Specific Extensions

Domain-specific objects (e.g., "Booking" for travel, "Diagnosis" for healthcare) are created as extensions of the universal objects, not as new fundamental types. They inherit all properties of their parent universal object and, transitively, of the ontological primitive that the parent derives from.

---

## 11. Relationship to Other Canonical Documents
| Document | Relationship |
|----------|-------------|
| **00_universal_ontology.md** | **Every Business Object derives from an ontological primitive defined here** |
| **01_shunya_vision.md** | Business objects are the vocabulary of the vision |
| **02_shunya_constitution.md** | Objects must respect all Constitutional rights and obligations |
| **04_universal_object_protocol.md** | Every object defined here implements the protocol |
| **05_runtime_canon.md** | Runtime manages the lifecycle of these objects |
| **06_data_canon.md** | Data architecture derives from object definitions |
| **07_ai_canon.md** | Comprehensive AI behavior guidelines for interacting with these objects |
| **08_experience_canon.md** | Experience surfaces these objects to humans |
| **09_repository_canon.md** | Repository structure maps to object boundaries |
| **10_migration_canon.md** | Migration converts existing models to these objects |
| **11_engineering_canon.md** | Engineering standards enforce object contract compliance |
| **12_launch_roadmap.md** | Object implementation is a milestone |

---

> **Next:** [04_universal_object_protocol.md](04_universal_object_protocol.md)

> **Foundation:** [00_universal_ontology.md](00_universal_ontology.md) — read this first to understand the primitives from which all Business Objects derive.
