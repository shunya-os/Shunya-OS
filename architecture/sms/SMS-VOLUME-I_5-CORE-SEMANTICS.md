# SHUNYA Master Specification — Volume I.5: Core Semantics

**Status:** Draft — Awaiting Founder Review
**Version:** 1.5.0
**Date:** 2026-07-22
**Authority:** SHUNYA Constitution, GENESIS Directive, GENESIS II Directive, GENESIS III Directive

---

## Preamble

Before the contracts come the meanings.

This volume defines the philosophical semantics of every kernel primitive. It answers not *what fields an object has* but *what it means for something to be an object in SHUNYA*.

These semantics are constitutional. They do not change with implementation decisions. If a line of code violates a semantic meaning, the code is wrong — not the meaning.

---

## Table of Contents

1. The Meaning of Object
2. The Meaning of Identity
3. The Meaning of Space
4. The Meaning of Relationship
5. The Meaning of Conversation
6. The Meaning of Permission
7. The Meaning of Timeline
8. The Meaning of Evidence
9. The Meaning of Context
10. The Meaning of Intent
11. The Meaning of Commitment
12. The Meaning of Execution
13. The Meaning of Outcome
14. The Meaning of Knowledge
15. The Meaning of Memory
16. The Meaning of Delegation
17. The Meaning of Governance

---

## 1. The Meaning of Object

### Purpose

An Object is the atomic unit of existence in SHUNYA. Everything that can be named, referenced, discussed, or decided upon is an Object. There is nothing in the system that is not an Object.

### Philosophical Meaning

Object is the answer to the question "what is this thing?"

In human cognition, we segment reality into discrete things: a person, a document, a decision, a conversation, a relationship. Each of these things has identity, state, and history. An Object in SHUNYA is the same: a persistent thing with an identity that persists across state changes.

An Object is not a database row. A database row is one implementation of an Object. An Object is a conceptual unit that may span multiple storage mechanisms.

### Invariants

- **Every Object has exactly one identity.** That identity never changes.
- **An Object's type is fixed at creation.** A Document cannot become a Person.
- **An Object's past is immutable.** What happened cannot unhappen. Only interpretations can change.
- **An Object exists in exactly one Space.** It may be visible to other Spaces through relationships.

### Anti-goals

- An Object is NOT a database table.
- An Object is NOT a REST resource.
- An Object is NOT a class in an object-oriented programming language.
- An Object is NOT defined by its fields. Fields are an implementation detail.

### Evolution Rules

- New Object types may be added without changing existing types.
- Object contracts may gain new mandatory fields only through constitutional amendment.
- Optional fields may be added at any time. Existing Objects that lack them are valid.
- Object deletion is always policy-aware (see The Meaning of Governance).

---

## 2. The Meaning of Identity

### Purpose

Identity is the answer to the question "who are you?" in a way that persists across sessions, devices, authentication methods, and lifetimes.

### Philosophical Meaning

A human being is not an email address. A human being is not a user account. A human being is not a row in a database. A human being is an ongoing presence that exists independently of any system, organization, or technology.

SHUNYA Identity is the system's acknowledgment of that presence. It is not something the system grants. It is something the system recognizes.

The identity is permanent because the human is permanent. The system may outlive any particular authentication method, but the identity persists.

### Invariants

- **Every human has exactly one SHUNYA Identity.** There are no duplicates.
- **Identity exists independently of any Space.** An identity exists before it joins any Space.
- **Identity exists independently of any authentication method.** If all methods are lost, the identity persists and new methods can be added.
- **Identity is never deleted.** At most, it is deactivated.
- **Organizations never own identities.** An organization is a Space with members, not an identity with subordinates.

### Anti-goals

- Identity is NOT a username.
- Identity is NOT an account. Accounts are Space-level membership records.
- Identity is NOT an email address. An email is one possible authentication method.
- Identity is NOT a profile. A profile is a collection of metadata attached to an identity.
- Identity is NOT created by an organization. An organization may verify identity, but does not create it.
- Identities are NEVER automatically merged. The human must explicitly link authentication methods.

### Evolution Rules

- New authentication method types may be added at any time.
- Identity verification requirements may increase, but must never lose existing verified methods.
- The identity_id format is an implementation detail. It must be unique, permanent, and opaque.

---

## 3. The Meaning of Space

### Purpose

Space is the answer to the question "where does this belong?"

### Philosophical Meaning

Humans organize their lives into contexts: personal, family, work, community, projects. Each context has its own boundaries, its own participants, its own rules, its own privacy. A Space is that context.

A Space is not a folder. A folder implies hierarchy (one thing inside another). A Space is a boundary with its own sovereignty. Things inside a Space belong to that Space. They may be shared with other Spaces, but their home Space never changes.

A Personal Space is sovereign. No organization can see inside it. An Organization Space is sovereign. No individual can see inside it unless they are a member.

### Invariants

- **Every Object belongs to exactly one Space.**
- **An Object's home Space never changes.** It may be visible in other Spaces, but its ownership is fixed.
- **Space membership is explicit.** Being a member of a parent Space does not grant membership in a child Space.
- **Permissions are scoped to Spaces.** A permission in one Space does not apply in another.

### Anti-goals

- A Space is NOT a folder or directory.
- A Space is NOT a database schema or table prefix.
- A Space is NOT a tenant in a multi-tenant architecture. Tenancy is an implementation concern.
- A Space is NOT a project management construct. Project Spaces are one type of Space.

### Evolution Rules

- New Space types may be added without changing existing Spaces.
- Space membership rules may evolve, but existing memberships must be preserved.
- Space nesting depth has no architectural limit, but practical limits may be implementation-defined.

---

## 4. The Meaning of Relationship

### Purpose

Relationship is the answer to the question "how are these things connected?"

### Philosophical Meaning

Reality is not a set of independent things. It is a web of connections. A person works at a company. A document belongs to a project. A decision was made based on evidence. A conversation is about an invoice. These connections are not incidental — they are constitutive of what these things are.

Relationships are first-class because they are the structure of reality. Removing relationships from the model is like removing edges from a graph: you lose the ability to navigate, to understand context, to answer "why" and "how."

Every relationship has a direction, but reality is bidirectional. If Alice reports to Bob, then Bob manages Alice. Both directions are true simultaneously.

### Invariants

- **Every relationship connects exactly two Objects.**
- **Every relationship has exactly one type.** Relationship types are not hierarchical.
- **Every relationship is stored bidirectionally.** It must be navigable from both ends.
- **A relationship does not imply permission.** Alice may be related to Bob's document without having permission to read it.

### Anti-goals

- A relationship is NOT a foreign key. A foreign key is a database implementation. A relationship is a semantic connection.
- A relationship is NOT a permission. A relationship and a permission are separate primitives that may reference each other.
- A relationship is NOT ownership. An ownership relationship is one type of relationship.

### Evolution Rules

- New relationship types may be added without changing existing relationships.
- Relationship types may be deprecated but never removed while instances exist.
- Relationship queries must always support type filtering and depth limiting.

---

## 5. The Meaning of Conversation

### Purpose

Conversation is the answer to the question "what has been said about this?"

### Philosophical Meaning

Conversation is how humans collaborate. Every meaningful object in SHUNYA is something that humans might discuss. A conversation attached to an object is the record of that discussion.

A conversation is not a chat. A chat is free-form, often ephemeral. A conversation attached to an object is structured, purposeful, and persistent. It is part of the object's history.

Conversation is the primary interface through which humans interact with SHUNYA. It is not an add-on feature. It is the default mode of engagement.

### Invariants

- **Every Conversation is attached to exactly one Object.**
- **Messages are append-only.** They cannot be edited or deleted. Corrections are new messages.
- **A Conversation exists in the same Space as its parent Object.**
- **A Conversation's participants are a subset of the Space's members with explicit access.**

### Anti-goals

- A Conversation is NOT a chat system. Chat is a communication pattern. Conversation is an attachment to an Object.
- A Conversation is NOT notification history. Notifications are a separate concern.
- A Conversation is NOT a comment thread. Comments are one type of message. Conversations may contain decisions, suggestions, and structured inputs.

### Evolution Rules

- New message types may be added without changing existing messages.
- Conversation access control follows the parent Object's permission model.
- Conversations may be archived with their parent Object.

---

## 6. The Meaning of Permission

### Purpose

Permission is the answer to the question "is this allowed?"

### Philosophical Meaning

Permission is the boundary between "can" and "should." It defines what actions are possible for a given identity in a given space. It is not a recommendation, not a guideline — it is a hard boundary enforced by the system.

Permission exists because not everything should be available to everyone. A personal thought should not be visible to an employer. A financial record should not be deletable by a casual viewer. An organizational policy should not be changeable by a single person.

Permissions are explicit. There is no implied permission. If a permission is not granted, the action is denied. This is the principle of least privilege applied architecturally.

### Invariants

- **Every action requires explicit permission.**
- **Permission is scoped to (Identity, Space, Resource Type, Action).**
- **No frontend may enforce permissions.** Permissions are enforced server-side only.
- **Deletion always requires governance evaluation.** No entity may delete what they cannot justify deleting.

### Anti-goals

- Permission is NOT authentication. Authentication proves who you are. Permission determines what you can do.
- Permission is NOT a role. A role is a collection of permissions. The permission is the atomic unit.
- Permission is NOT a recommendation. If denied, the system must refuse, not suggest.
- Permission is NOT optional. All actions pass through permission evaluation.

### Evolution Rules

- New permission types may be added without changing existing permissions.
- Permission granularity may increase (more specific resource types) but never decrease.
- Permission evaluation must be observable for audit purposes.

---

## 7. The Meaning of Timeline

### Purpose

Timeline is the answer to the question "what happened and when?"

### Philosophical Meaning

Every Object has a history. That history is not optional — it is constitutive of what the Object is. An Object without a history is an abstraction, not a real thing. Real things exist in time.

The Timeline is that history made explicit and immutable. It is the record of every state transition, every decision, every action taken on or by an Object.

The Timeline exists because humans need to understand not just what is true now, but how it became true. Trust requires transparency. Transparency requires history.

### Invariants

- **Every Object has exactly one Timeline.**
- **Timeline events are append-only.** They can never be deleted, modified, or reordered.
- **Events are ordered within a single Timeline.**
- **Every state-changing action produces at least one Timeline event.**

### Anti-goals

- A Timeline is NOT a log. Logs are for debugging. Timelines are for understanding.
- A Timeline is NOT a database transaction log. A single transaction may produce multiple events.
- A Timeline is NOT a notification feed. Notifications are derived from Timelines, not the reverse.

### Evolution Rules

- New event types may be added without changing existing events.
- Timeline queries must support time-range filtering and pagination.
- Timeline compaction may occur only for events older than a constitutional minimum retention period.

---

## 8. The Meaning of Evidence

### Purpose

Evidence is the answer to the question "why should I believe this?"

### Philosophical Meaning

In a deterministic system, every output has inputs. Evidence is the chain from output back to input. It is the provenance of belief.

Evidence exists because SHUNYA claims to be explainable. An explainable system must be able to answer "why" for every conclusion it produces. Evidence is that answer.

Evidence is not metadata. It is not optional. If a conclusion exists, the evidence for it exists — whether or not it is explicitly recorded. The system's job is to make that evidence explicit and traceable.

Evidence can be direct (I saw it) or indirect (I inferred it from other evidence). Both are valid, but the chain must be transparent.

### Invariants

- **Every computed conclusion carries at least one Evidence reference.**
- **Evidence references are resolvable.** Every evidence ID leads to an Object.
- **Evidence chains are acyclic.** A conclusion cannot be evidence for itself.
- **Confidence propagates through chains.** Confidence(A → C) ≤ Confidence(A → B) × Confidence(B → C).

### Anti-goals

- Evidence is NOT a citation. Citations are one form of evidence. Evidence also includes observations, derivations, computations.
- Evidence is NOT logging. Logging records events. Evidence records why a conclusion was reached.
- Evidence is NOT a guarantee of truth. Evidence indicates provenance, not correctness. High-confidence evidence can still be wrong.

### Evolution Rules

- New evidence types may be added without changing existing evidence.
- Evidence may be superseded by new evidence, but never deleted.
- Evidence confidence is a function of the system at capture time. Re-evaluation may change a current assessment but does not change historical evidence.

---

## 9. The Meaning of Context

### Purpose

Context is the answer to the question "what is relevant right now?"

### Philosophical Meaning

No Object exists in isolation. Every Object is surrounded by its relationships, its Space, its conversation, its timeline, its evidence. Context is the aggregate of all these things that are relevant to understanding or acting upon an Object at a given moment.

Context is dynamic. What is relevant changes with time, with the identity of the observer, with the action being considered. A manager reviewing an invoice sees different context than a customer reviewing the same invoice.

Context is not a primitive in the same sense as Object or Identity. It is a derived concept — the set of primitives relevant to a situation. But it is essential enough to warrant its own semantic definition.

### Invariants

- **Context is derived, not stored.** It is computed from relationships, permissions, and state at query time.
- **Context respects permissions.** An identity never sees context they lack permission for.
- **Context is bounded.** It does not include the entire graph — only what is relevant.

### Anti-goals

- Context is NOT a cache. Caches are implementation mechanisms. Context is a semantic concept.
- Context is NOT the entire knowledge graph. The knowledge graph is everything. Context is what matters now.

---

## 10. The Meaning of Intent

### Purpose

Intent is the answer to the question "what is someone trying to do?"

### Philosophical Meaning

Humans act with purpose. They intend to do things before they do them. Intent is that purpose captured before execution.

Intent exists because SHUNYA does not execute silently. Before anything happens, the system must understand what the human is trying to accomplish. This understanding is not mind-reading — it is the human explicitly stating their intent, and the system confirming its understanding.

Intent bridges the gap between a human's desire and the system's action. It is the moment of shared understanding before execution.

### Invariants

- **Every execution is preceded by an Intent.**
- **Intent is explicit, not inferred.**
- **Intent may be withdrawn before execution begins.**
- **Intent carries the human's permission for the action.**

### Anti-goals

- Intent is NOT a prediction. Predictions are about what will happen. Intent is about what someone wants to happen.
- Intent is NOT a command. A command says "do this." Intent says "I want to do this."

---

## 11. The Meaning of Commitment

### Purpose

Commitment is the answer to the question "what has been promised?"

### Philosophical Meaning

A commitment is an obligation entered into by an identity. It is a promise that the system records on behalf of the human. It may be a promise to do something, to deliver something, to pay something, or to refrain from something.

Commitments are serious. They are not the same as plans or intentions. A plan is what you intend to do. A commitment is what you have agreed to do.

### Invariants

- **Commitments are created by explicit human action, not inferred.**
- **Commitments have a lifecycle:** proposed → accepted → fulfilled | breached | withdrawn.
- **Fulfilled commitments are immutable.** They become part of the timeline.
- **Breached commitments require explanation.**

---

## 12. The Meaning of Execution

### Purpose

Execution is the answer to the question "what happened when the system acted?"

### Philosophical Meaning

Execution is the system carrying out an action. It is the moment between intent and outcome. Execution is deterministic: given the same intent and the same state, the same execution will occur.

Execution is not the same as outcome. Execution is the action taken. Outcome is the result of that action. They are separate because the same execution can have different outcomes depending on external factors.

### Invariants

- **Every execution is authorized by Intent.**
- **Every execution is governed by Governance.**
- **Every execution produces at least one Timeline event.**
- **Executions are deterministic.** Same inputs → same execution.

---

## 13. The Meaning of Outcome

### Purpose

Outcome is the answer to the question "what happened as a result?"

### Philosophical Meaning

Outcome is the actual result of an execution. It is reality's response to the system's action. Unlike execution, outcome is not fully deterministic — external factors, timing, and other actors may influence the result.

Outcome matters because intentions are not results. A payment execution may succeed (the money moved) but the outcome may be a failure (the recipient's account was frozen). Both are true simultaneously.

### Invariants

- **Every execution has exactly one outcome.**
- **Outcomes are observed, not predicted.** Prediction is an intelligence function. Outcome is an observation.
- **Outcomes are added to the Timeline.**

---

## 14. The Meaning of Knowledge

### Purpose

Knowledge is the answer to the question "what does SHUNYA know?"

### Philosophical Meaning

Knowledge is persistently stored information that the system can reference across sessions and contexts. It is distinct from memory (which is personal) and evidence (which is specific to conclusions).

Knowledge is the system's accumulated understanding of the world. It grows over time through ingestion, observation, and learning. It is the basis for reasoning and recommendations.

Knowledge is not truth. It is the best available understanding at a given time.

### Invariants

- **Knowledge is referenced by Object ID.**
- **Knowledge has provenance.** The system knows how it knows something.
- **Knowledge may be superseded but not deleted.**

---

## 15. The Meaning of Memory

### Purpose

Memory is the answer to the question "what does this identity remember?"

### Philosophical Meaning

Memory is knowledge scoped to an Identity. It is what a particular person has experienced, learned, or chosen to remember. It is distinct from general Knowledge because it is personal.

Memory gives SHUNYA the ability to know an individual across time. It enables the system to recognize patterns, recall preferences, and build relationship.

Memory is never stored without permission (Article 3: Permission Before Action).

### Invariants

- **Memory is scoped to exactly one Identity.**
- **Memory is not shared across Identities without explicit permission.**
- **Memory may be forgotten (deleted) by the Identity at any time.**
- **Memory is distinct from Knowledge.** Knowledge is universal. Memory is personal.

---

## 16. The Meaning of Delegation

### Purpose

Delegation is the answer to the question "who can act on my behalf?"

### Philosophical Meaning

No human can do everything themselves. Delegation is the mechanism by which an Identity grants another Identity the authority to act in their stead. It is temporary, specific, and revocable.

Delegation is not the same as role assignment. A role grants standing permissions. A delegation grants temporary authority that can be withdrawn while the role remains unchanged.

### Invariants

- **Delegation is always revocable by the delegator.**
- **Delegation is always temporary.** It has an explicit expiry.
- **Delegation is specific to actions and spaces.**
- **Delegation does not transfer ownership.** Ownership remains with the original Identity.

---

## 17. The Meaning of Governance

### Purpose

Governance is the answer to the question "is this action permitted by policy?"

### Philosophical Meaning

Governance is the layer between intent and execution. It evaluates whether a proposed action is allowed — not just by permission (which is coarse-grained) but by policy (which is fine-grained and context-aware).

A permission says "you may edit this document." Governance asks "are you allowed to edit financial documents with amounts over $10,000 without a second approval?"

Governance is deterministic and transparent. It produces a verdict with traceable reasoning.

### Invariants

- **Governance sits between Intent and Execution.**
- **Governance evaluates every action against policies.**
- **Governance verdicts are deterministic.** Same action, same context → same verdict.
- **Governance verdicts include evidence for the decision.**
- **Governance may be bypassed only by constitutional override, not by policy.**

### Anti-goals

- Governance is NOT permission. Permission is a simpler check (role-based). Governance is policy-based evaluation.
- Governance is NOT a suggestion. If Governance blocks an action, the action must not execute.
- Governance is NOT optional. Every action passes through Governance before Execution.



---

## World Graph

The following diagram shows how every kernel primitive relates to every other primitive.

```
                        ┌─────────────────────────────────────────────────────────┐
                        │                      GOVERNANCE                         │
                        │    (evaluates every action against policy)              │
                        └──────────┬──────────────────────────────────┬───────────┘
                                   │                                  │
                                   ▼                                  ▼
 ┌──────────────┐          ┌──────────────┐                   ┌──────────────┐
 │   IDENTITY   │◄────────►│   INTENT     │────────────►      │  EXECUTION   │
 │ (who)        │  owns    │ (what I want │    authorized      │ (action taken)│
 └──────┬───────┘          │  to do)      │                   └──────┬───────┘
        │                  └──────────────┘                          │
        │                         │                                  │
        │                         ▼                                  ▼
        │                  ┌──────────────┐                   ┌──────────────┐
        │                  │ COMMITMENT   │                   │   OUTCOME    │
        │                  │ (what I      │                   │ (what        │
        │                  │  promised)   │                   │  happened)   │
        │                  └──────────────┘                   └──────┬───────┘
        │                                                           │
        ▼                                                           ▼
 ┌──────────────┐                                          ┌──────────────┐
 │    SPACE     │                                          │   TIMELINE   │
 │ (where)      │◄───────────────── ALL OBJECTS ──────────►│ (when)       │
 └──────────────┘         belong to / exist in              └──────────────┘
                                                                    │
        ▼                                                           ▼
 ┌──────────────┐                                          ┌──────────────┐
 │ RELATIONSHIP │                                          │   EVIDENCE   │
 │ (how things  │◄────────  EVIDENCE ↔ OBJECTS ──────────►│ (why to      │
 │  connect)    │           (evidence supports objects)    │  believe)    │
 └──────────────┘                                          └──────────────┘
                                                                    │
        ▼                                                           ▼
 ┌──────────────┐                                          ┌──────────────┐
 │ CONVERSATION │                                          │  KNOWLEDGE   │
 │ (what has    │─── attached to Objects ──────────────────►│ (what the    │
 │  been said)  │                                           │  system      │
 └──────────────┘                                           │  knows)      │
                                                            └──────────────┘
        ▼                                                           ▲
 ┌──────────────┐                                           ┌──────────────┐
 │ PERMISSION   │                                           │   MEMORY     │
 │ (is this     │─── scoped to Identity × Space ───────────►│ (what this   │
 │  allowed?)   │                                           │  identity    │
 └──────────────┘                                           │  remembers)  │
                                                            └──────────────┘
        ▼
 ┌──────────────┐
 │   CONTEXT    │
 │ (what is     │─── derived from all primitives at query time
 │  relevant?)  │
 └──────────────┘

        ▼
 ┌──────────────┐
 │ DELEGATION   │
 │ (who can act │─── Identity delegates to Identity (temporary, revocable)
 │  for me?)    │
 └──────────────┘
```

### Flow Summary

```
IDENTITY enters SPACE
  → IDENTITY forms INTENT
    → GOVERNANCE evaluates INTENT against policy
      → PERMISSION confirms authorization
        → EXECUTION performs the action
          → OUTCOME is observed
            → TIMELINE records the event
              → EVIDENCE is captured for the conclusion
                → KNOWLEDGE is updated (if systemic)
                  → MEMORY is updated (if personal)

IDENTITY forms COMMITMENT
  → COMMITMENT is recorded in TIMELINE
    → EXECUTION fulfills or breaches COMMITMENT
      → OUTCOME is observed

OBJECT exists in SPACE
  → CONVERSATION is attached to OBJECT
    → RELATIONSHIPS connect OBJECT to other OBJECTS
      → TIMELINE records OBJECT's history
        → EVIDENCE supports OBJECT's conclusions

IDENTITY delegates to IDENTITY
  → DELEGATION creates temporary PERMISSION
    → GOVERNANCE evaluates delegated actions
      → EXECUTION respects delegation boundaries

CONTEXT is derived at query time:
  CONTEXT = OBJECT
          + RELATIONSHIPS (1-2 hops)
          + CONVERSATION (recent messages)
          + TIMELINE (recent events)
          + EVIDENCE (most relevant)
          + PERMISSION (what the querying identity can see)
```

---

*End of SMS Volume I.5 — Core Semantics*
