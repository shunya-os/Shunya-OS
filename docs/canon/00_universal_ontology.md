# Universal Ontology

> **Canonical Document · Phase C1A**
> **Status: CANONICAL — Foundational Ontology**
> **Version: 1.0**
> **Position: 00 — Before Business Canon**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Ontological Principles](#2-ontological-principles)
3. [Entity](#3-entity)
4. [Identity](#4-identity)
5. [Object](#5-object)
6. [Relationship](#6-relationship)
7. [State](#7-state)
8. [Event](#8-event)
9. [Observation](#9-observation)
10. [Evidence](#10-evidence)
11. [Decision](#11-decision)
12. [Action](#12-action)
13. [Outcome](#13-outcome)
14. [Knowledge](#14-knowledge)
15. [Memory](#15-memory)
16. [Context](#16-context)
17. [Workspace](#17-workspace)
18. [Ontological Dependency Graph](#18-ontological-dependency-graph)
19. [Relationship to Other Canonical Documents](#19-relationship-to-other-canonical-documents)

---

## 1. Purpose

This document defines the fundamental nature of reality inside SHUNYA from first principles. It answers: **what are the primitive kinds of things that exist?**

Every Business Object (03_business_canon.md) derives from these primitives. Every protocol contract (04_universal_object_protocol.md) implements these primitives. No downstream document may introduce a new primitive without amending this ontology.

This is not a data model. This is not an implementation specification. This is ontology — the study of what things are.

---

## 2. Ontological Principles

### 2.1 First Principles

1. **Reality precedes representation.** SHUNYA does not invent reality. It models reality. The ontology reflects what exists in the real world, not what is convenient to store.

2. **One concept, one definition.** Every concept has exactly one authoritative definition in this document. No other document may redefine it. Other documents may extend it with domain-specific constraints but may not change its fundamental nature.

3. **Layered reality.** Reality has layers: Entities exist. Entities have Identity. Entities relate through Relationships. Entities experience Events. Events are Observed. Observations are supported by Evidence. Entities make Decisions. Decisions produce Actions. Actions produce Outcomes. Outcomes produce Knowledge. Entities form Memory. Memory and Knowledge create Context. Context lives in Workspaces.

4. **No implementation leakage.** Nothing in this ontology prescribes storage, serialization, APIs, or UI. These are downstream concerns.

5. **Parsimony.** No concept exists unless it is necessary. If two concepts can be unified, they are unified here.

---

## 3. Entity

### 3.1 Definition

An **Entity** is anything that exists as a distinct, independent thing in reality. Entities are the subjects and objects of everything that happens in SHUNYA.

### 3.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Existence** | An Entity either exists or does not. Existence is binary, not gradual. |
| **Persistence** | An Entity continues to exist across time unless it ceases to exist. |
| **Distinctness** | An Entity is distinct from all other Entities. Two Entities are never the same Entity. |
| **Identity** | Every Entity has identity (see §4). Identity is what makes it *this* Entity and not another. |
| **Attributes** | An Entity has attributes that describe it. Attributes can change without the Entity ceasing to be itself. |
| **Relationships** | An Entity can relate to other Entities (see §6). |

### 3.3 Entity vs Non-Entity

| Is an Entity | Is Not an Entity |
|-------------|-----------------|
| A human being | A color |
| An organization | A temperature |
| A document | A relationship (relationships are between Entities, not Entities themselves) |
| A workspace | An event (events happen to Entities, they are not Entities) |
| A commitment | An action (actions are performed by Entities, they are not Entities) |

### 3.4 Canonical Entity Types

These are the fundamental kinds of Entities in SHUNYA:

| Entity Type | Definition |
|-------------|-----------|
| **Human** | A human being |
| **Organization** | A group of Humans organized around a purpose |
| **Workspace** | A bounded context for work (see §17) |
| **Document** | A persistent collection of structured information |
| **FinancialObject** | Any object representing financial value or obligation |

All other concepts in SHUNYA are either non-Entity concepts (Identity, Relationship, State, Event, Observation, Evidence, Decision, Action, Outcome, Knowledge, Memory, Context) or Business Objects that derive from Entity.

---

## 4. Identity

### 4.1 Definition

**Identity** is the property of an Entity that makes it *this* Entity and not any other. Identity is the "thisness" of a thing — the principle of individuation.

### 4.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Uniqueness** | No two distinct Entities share the same identity. |
| **Permanence** | Identity is assigned at an Entity's inception and never changes. An Entity that changes identity becomes a different Entity. |
| **Non-reusability** | An identity, once retired, is never reassigned. |
| **Essentiality** | Identity is essential, not accidental. An Entity can lose all its accidental properties and still be itself; losing identity means ceasing to be that Entity. |

### 4.3 Identity vs Attributes

| Identity | Attributes |
|----------|-----------|
| Makes an Entity *this* Entity | Describe an Entity |
| Cannot change | Can change |
| Is essential | Are accidental |
| One per Entity | Many per Entity |
| Defines "which" | Define "what kind" |

---

## 5. Object

### 5.1 Definition

An **Object** is any thing in SHUNYA's model. All Entities are Objects, but not all Objects are Entities. The Object is the universal category — everything SHUNYA knows about is an Object.

### 5.2 Ontological Classification

```
                        Object
                          │
            ┌─────────────┴─────────────┐
            │                           │
         Entity                    Non-Entity Concept
            │                           │
    ┌───────┼───────┐            ┌──────┼──────┐
    │       │       │            │      │      │
  Human  Org   Workspace      Identity  Relationship  State
  Document  FinObj            Event     Observation  Evidence
                              Decision  Action       Outcome
                              Knowledge Memory       Context
```

### 5.3 Entity Objects

Entity Objects are things that have independent existence in reality.

### 5.4 Non-Entity Objects

Non-Entity Objects are concepts that SHUNYA reasons about but that do not have independent existence. They are always *of* or *about* Entities or other concepts.

### 5.5 Object vs Entity

| Object | Entity |
|--------|--------|
| A Relationship is an Object | A Relationship is not an Entity (it connects Entities) |
| An Event is an Object | An Event is not an Entity (it happens to Entities) |
| A Decision is an Object | A Decision is not a distinct Entity (it is made by an Entity about an Entity) |
| A Human is an Object | A Human IS an Entity |

---

## 6. Relationship

### 6.1 Definition

A **Relationship** is a directed, typed connection between two Objects. Relationships describe how Objects relate to each other.

### 6.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Directionality** | Every Relationship has a source and a target. Even bidirectional Relationships are modeled as two directional Relationships. |
| **Typedness** | Every Relationship has a type that defines its nature (e.g., membership, ownership, reference, derivation). |
| **Time-boundedness** | A Relationship exists for a duration. It can be created and ended. |
| **Strength** | A Relationship has a strength or confidence that indicates how well-established it is. |

### 6.3 Relationship vs Attribute

| Relationship | Attribute |
|-------------|-----------|
| Connects *two* Objects | Describes *one* Object |
| Has a source and target | Inheres in its subject |
| Exists independently | Exists only as a property of its subject |

---

## 7. State

### 7.1 Definition

**State** is the set of all properties of an Object at a point in time. State is what is true about an Object right now.

### 7.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Temporality** | State is always at a point in time. "State without time" is meaningless. |
| **Mutability** | State changes over time. An Object in a different state is still the same Object (identity is preserved). |
| **Totality** | State includes every property of the Object (not just selected ones). |
| **Observability** | State can be observed. An unobserved state is still state — the state of an Object does not depend on being observed. |

### 7.3 State vs Identity

| State | Identity |
|-------|----------|
| Changes over time | Never changes |
| Is accidental | Is essential |
| Includes many properties | Includes only the one property of "thisness" |

---

## 8. Event

### 8.1 Definition

An **Event** is something that happens at a point in time. Events are the atoms of change — everything that changes state does so through Events.

### 8.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Occurrence** | An Event occurs at a specific point in time. Before that point, it has not happened. After, it has. |
| **Immutability** | Once an Event has occurred, it cannot be un-occurred. Events are immutable. |
| **Atomicity** | An Event is a single happening. It cannot be decomposed into smaller Events without losing meaning. |
| **Causality** | An Event is caused by an Action or by another Event. Events form causal chains. |

### 8.3 Event vs State

| Event | State |
|------|-------|
| Happens at a point | Is true at a point |
| Is a change | Is a condition |
| Is immutable | Is mutable |
| Is a "happening" | Is a "being" |

### 8.4 Event Types

| Event Type | Definition | Example |
|-----------|-----------|---------|
| **Creation** | An Object comes into existence | A Human is registered |
| **Modification** | An Object's state changes | A document is edited |
| **Transition** | An Object's lifecycle stage changes | A task moves to "in progress" |
| **Relationship** | A Relationship is created or ended | A Human joins an Organization |
| **Observation** | Something is observed (see §9) | A signal is captured |
| **Decision** | A choice is made (see §11) | A decision is recorded |

---

## 9. Observation

### 9.1 Definition

An **Observation** is an Event that has been captured and recorded by the system. Observations are the raw material of intelligence — they are how reality enters SHUNYA.

### 9.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Derivation** | An Observation derives from an Event. Every Observation is about some Event that happened. |
| **Recording** | An Observation is the act of recording that an Event occurred. Without recording, an Event is not an Observation. |
| **Fallibility** | An Observation can be mistaken. The Event may not have occurred as observed. This is why Evidence exists (see §10). |
| **Timeliness** | An Observation is captured at a specific time. Observation time may differ from Event time (an Event can be observed later). |

### 9.3 Observation vs Event

| Observation | Event |
|------------|-------|
| Is a recording of something that happened | Is the thing that happened |
| Can be mistaken | Cannot be mistaken (it happened) |
| Has a capture time | Has an occurrence time |
| Is always available after capture | May have occurred without being observed |

---

## 10. Evidence

### 10.1 Definition

**Evidence** is information that supports or contradicts an Observation, a Relationship, or a Decision. Evidence is the foundation of confidence — without Evidence, nothing is certain.

### 10.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Supportiveness** | Evidence supports or contradicts. It is directional — it either increases or decreases confidence in its subject. |
| **Gradability** | Evidence can be strong or weak. Not all evidence is equally convincing. |
| **Appendability** | Evidence can be added but never removed. New evidence may contradict old evidence, but the old evidence remains as a record. |
| **Chainability** | Evidence forms chains. Evidence itself can be supported by other Evidence. |
| **Source-dependence** | Every piece of Evidence has a source — an Originator (who or what produced it). |

### 10.3 Evidence vs Observation

| Evidence | Observation |
|----------|------------|
| Supports or contradicts something | Records that something happened |
| Has a direction (for/against) | Is neutral (it just records) |
| Can be strong or weak | Has confidence (correctness likelihood) |
| Can be chained | Is atomic |

---

## 11. Decision

### 11.1 Definition

A **Decision** is a choice made by an Entity among alternatives. Decisions are the central unit of intelligence — they connect Observation to Action to Outcome.

### 11.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Agency** | A Decision requires an Entity that decides. There is no decision without a decider. |
| **Alternatives** | A Decision implies alternatives. If there is no choice, there is no decision. |
| **Intentionality** | A Decision is made for a reason. The reason may be explicit or implicit. |
| **Consequentiality** | A Decision leads to consequences (Actions and Outcomes). |
| **Recordability** | A Decision can be recorded. An unrecorded decision still happened but is not available to SHUNYA. |

### 11.3 Decision vs Event

| Decision | Event |
|----------|-------|
| Involves choice | Just happens |
| Has an agent | May have no agent |
| Could have been otherwise | Could not have been otherwise (it happened) |
| Leads to consequences | Is itself a happening |

---

## 12. Action

### 12.1 Definition

An **Action** is something done by an Entity that has an effect on the world. Actions are the link between Decision and Outcome.

### 12.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Agency** | Every Action has an Actor — the Entity that performs it. |
| **Effect** | Every Action changes the world in some way. An Action with no effect is not an Action. |
| **Intentionality** | An Action may be intentional (following a Decision) or unintentional. |
| **Observability** | An Action can be observed. |
| **Temporality** | An Action has a start and an end. It occupies time. |

### 12.3 Action vs Event

| Action | Event |
|--------|-------|
| Has an Actor | May have no Actor |
| Has duration | Is instantaneous |
| Is done | Happens |
| Is intentional or unintentional | Simply occurs |

---

## 13. Outcome

### 13.1 Definition

An **Outcome** is the state of the world after an Action or set of Actions, measured against the intended state. Outcomes close the loop from Decision to learning.

### 13.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Measurability** | An Outcome can be measured against criteria. |
| **Relationality** | An Outcome is relative to an intended state. Without intention, there is no outcome — only a new state. |
| **Temporality** | An Outcome is measured at a specific time after the Action. |
| **Learning-potential** | An Outcome enables learning. The difference between intended and actual state is information. |

### 13.3 Outcome vs State

| Outcome | State |
|---------|-------|
| Is measured against intention | Just is what it is |
| Implies evaluation | Implies description |
| Enables learning | Enables knowledge |

---

## 14. Knowledge

### 14.1 Definition

**Knowledge** is verified, structured information that the system holds as true. Knowledge is the product of reasoning over Observations and Evidence.

### 14.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Verification** | Knowledge requires verification. Unverified information is hypothesis, not knowledge. |
| **Structure** | Knowledge is organized. It has internal structure — facts relate to other facts. |
| **Confidence** | Knowledge has a confidence level. Absolute certainty is not achievable. |
| **Derivation** | Knowledge is derived from Evidence, Observations, and other Knowledge. |
| **Supersedability** | Knowledge can be superseded by better Knowledge. Old Knowledge is replaced, not destroyed. |

### 14.3 Knowledge vs Observation

| Knowledge | Observation |
|-----------|------------|
| Verified and structured | Raw and unprocessed |
| Has high confidence | Has raw confidence |
| Is derived | Is captured |
| Is organized into relationships | Is atomic |

---

## 15. Memory

### 15.1 Definition

**Memory** is the system's retained experience. While Knowledge is "what is true," Memory is "what happened." Memory is experiential, contextual, and personal.

### 15.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Experience-dependence** | Memory derives from experience (Observations, Events, Outcomes). |
| **Decay** | Memory naturally degrades over time unless reinforced. |
| **Consolidation** | Memory consolidates from ephemeral to durable forms. |
| **Subjectivity** | Memory is from a perspective. Different observers may have different memories of the same Event. |
| **Forgetability** | Memory can be forgotten (deliberately or naturally). |

### 15.3 Memory vs Knowledge

| Memory | Knowledge |
|--------|-----------|
| "What happened" | "What is true" |
| Experiential | Structural |
| Decays over time | Persists until superseded |
| Personal to an observer | Objective (or as objective as possible) |
| Can be forgotten | Is retained |

---

## 16. Context

### 16.1 Definition

**Context** is the set of all Knowledge and Memory relevant to a given situation or Entity at a given time. Context is what the system knows *now* about *this* situation.

### 16.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Situatedness** | Context is always about a specific situation or Entity. There is no context-in-general. |
| **Temporality** | Context is time-bound. The context now is different from the context yesterday. |
| **Relevance** | Context includes only what is relevant. Irrelevant information is noise, not context. |
| **Boundedness** | Context has boundaries. A Workspace defines the boundary of its Context. |
| **Composability** | Context is composed of Knowledge and Memory relevant to the situation. |

### 16.3 Context vs Knowledge

| Context | Knowledge |
|---------|-----------|
| Is about a specific situation | Is general |
| Includes only relevant information | Includes all verified information |
| Is time-bound | Is persistent |
| Is bounded | Is global |

---

## 17. Workspace

### 17.1 Definition

A **Workspace** is a bounded context within which Entities collaborate, make Decisions, and build Knowledge. Workspaces are the primary organizational unit of human-AI collaboration.

### 17.2 Ontological Properties

| Property | Definition |
|----------|------------|
| **Boundary** | A Workspace has boundaries that define what is inside and what is outside. These boundaries determine Context. |
| **Membership** | A Workspace has Members (Entities that participate in it). |
| **Containment** | A Workspace contains other Objects (Documents, Decisions, Conversations, Tasks, etc.). |
| **Persistence** | A Workspace persists across sessions. Its contents persist. |
| **Isolation** | A Workspace isolates its contents from other Workspaces unless explicitly shared. |

### 17.3 Workspace as Entity

A Workspace is an Entity. It has Identity, State, Relationships, and a Lifecycle. It can be created, modified, archived, and deleted. It relates to Humans (as Members), Organizations (as parent), and other Objects (as contents).

---

## 18. Ontological Dependency Graph

```
                     Entity
                       │
            ┌──────────┼──────────┐
            │          │          │
         Identity   State    Relationship
            │          │
            └────┬─────┘
                 │
              ┌──┴──┐
              │     │
           Event  Observation
              │     │
              └──┬──┘
                 │
              Evidence
                 │
              ┌──┴──┐
              │     │
           Decision Action
              │     │
              └──┬──┘
                 │
              Outcome
                 │
            ┌────┴────┐
            │         │
        Knowledge   Memory
            │         │
            └────┬────┘
                 │
              Context
                 │
               Workspace
```

**Dependency direction:** An arrow from A → B means "A depends on B" or "A is defined in terms of B."

- Entity depends on Identity (an Entity is what has Identity)
- State depends on Entity (State is the state of an Entity)
- Relationship depends on Entity (Relationship connects Entities)
- Event depends on Entity + State (Event changes State of Entity)
- Observation depends on Event (Observation records Event)
- Evidence depends on Observation (Evidence supports Observation)
- Decision depends on Entity + Observation + Evidence (Decision is made by Entity, based on Observations and Evidence)
- Action depends on Decision (Action follows Decision) OR Entity (Action can be spontaneous)
- Outcome depends on Action + State (Outcome is State after Action)
- Knowledge depends on Observation + Evidence + Outcome (Knowledge is derived)
- Memory depends on Event + Outcome (Memory is experience retained)
- Context depends on Knowledge + Memory (Context is relevant Knowledge + Memory for a situation)
- Workspace depends on Entity + Context (Workspace contains Entities and provides Context)

---

## 19. Relationship to Other Canonical Documents

| Document | Relationship |
|----------|-------------|
| **01_shunya_vision.md** | The vision of compounding intelligence requires this ontological foundation |
| **02_shunya_constitution.md** | Constitutional rights apply to Entities; ontology defines what Entities are |
| **03_business_canon.md** | **Every Business Object derives from these ontological primitives** |
| **04_universal_object_protocol.md** | The protocol implements the properties defined here for each concept |
| **05_runtime_canon.md** | The runtime manages the lifecycle of Objects through Events, Decisions, and Actions |
| **06_data_canon.md** | Data architecture stores Objects in terms of their ontological categories |
| **07_ai_canon.md** | AI engines operate on these ontological primitives (Observer observes Events, Reasoner derives Knowledge, etc.) |
| **08_experience_canon.md** | Experience surfaces Objects to Humans through Workspaces |
| **09_repository_canon.md** | Repository structure is derived from the ontology: core/ contains Entity primitives, intelligence/ contains engine concepts |
| **10_migration_canon.md** | Migration brings existing models into conformance with the ontology |
| **11_engineering_canon.md** | Engineering standards enforce ontological correctness |
| **12_launch_roadmap.md** | Ontology is the foundation that all milestones build upon |

---

> **This document is the foundation of all other canonical documents.**
> **No downstream document may redefine the concepts defined here.**