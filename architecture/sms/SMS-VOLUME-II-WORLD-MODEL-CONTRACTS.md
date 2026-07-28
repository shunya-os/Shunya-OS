# SHUNYA Master Specification — Volume II: World Model Contracts

**Status:** Draft — Awaiting Founder Review
**Version:** 2.1.0
**Date:** 2026-07-22
**Authority:** SHUNYA Constitution, SMS Volume I.5: Core Semantics

---

## Preamble

This volume defines the canonical contracts for every kernel primitive in SHUNYA. Each contract specifies what must be true, not how to achieve it. Implementation details (identifiers, serialization, repositories, API patterns) belong in engineering guidance, not in constitutional contracts.

**Language-agnostic:** These contracts contain no programming language constructs, no database specifics, no UUID schemas, no serialization formats. They are as true for a Python implementation as for a Go, Rust, or Haskell implementation.

**Relation to Volume I.5:** Volume I.5 defines *what each primitive means*. This volume defines *what each primitive requires*. The contracts are the enforceable expression of the semantics.

---

## Table of Contents

1. Universal Object Contract
2. Identity Contract
3. Space Contract
4. Relationship Contract
5. Conversation Contract
6. Permission Contract
7. Timeline Contract
8. Evidence Contract
9. World Graph (referenced from I.5)

---

## 1. Universal Object Contract

### Purpose

Every entity in the system conforms to this contract. No entity may bypass it.

### Philosophical Meaning

See SMS Volume I.5 §1 — The Meaning of Object.

### Invariants

- Every Object has exactly one identifier that never changes.
- Every Object has exactly one type that is fixed at creation.
- Every Object has a lifecycle state that transitions according to defined rules.
- Every Object has a creation timestamp that never changes.
- Every Object has a last-modified timestamp that updates on each mutation.
- Every Object's state history is preserved and replayable.

### Contract

| Aspect | Requirement |
|--------|-------------|
| **Identity** | Every Object possesses a single, immutable, unique identifier. This identifier must be globally unique (within the system) and must never be reassigned. |
| **Type** | Every Object declares its type at creation. The type is immutable. The type must be registered in the Object Registry. |
| **Lifecycle** | Every Object exists in one of these states: `active`, `superseded`, `archived`, `pending`, `deleted`. Transitions are: active↔superseded, active→archived, active→pending, active→deleted, superseded→archived. Deletion requires governance evaluation. |
| **Version** | Every Object carries a version that increments on each mutation that changes meaningful state. Versions are monotonically increasing and non-negative. |
| **Temporality** | Every Object records its creation time and last modification time. Both are expressed in a standard temporal format (UTC). Creation time is immutable. |
| **Provenance** | Every Object records who or what created it and who or what last modified it. These references point to an Identity or system component. |
| **Confidence** | Every Object carries a confidence score in the range [0, 1], where 0 represents no confidence and 1 represents certainty. The scale is linear. |
| **Evidence** | Every Object may carry references to evidence that supports its state. Evidence references are resolvable to other Objects. |
| **Relationships** | Every Object may carry references to relationships connecting it to other Objects. Relationship references are resolvable. |
| **Extensibility** | Every Object may carry additional metadata that is not covered by the contract. This metadata does not alter the contractual fields. |

### Anti-goals

- The contract does NOT specify identifier format. The system may use UUIDs, hashes, or any scheme that satisfies the identity requirements.
- The contract does NOT specify serialization format. JSON, Protocol Buffers, Avro, or any interchange format that preserves the contract is acceptable.
- The contract does NOT specify storage mechanism. Relational databases, document stores, graph databases, or in-memory structures are all valid implementations.

### Evolution Rules

- New Object types may be added without modifying existing types.
- The contract may gain new fields only through constitutional amendment.
- Optional fields may be added at any time.
- Existing Objects that lack optional fields are valid.
- Field types must be backwards-compatible across versions.

---

## 2. Identity Contract

### Purpose

Every human using SHUNYA possesses exactly one Identity. The Identity Contract defines what that Identity must provide.

### Philosophical Meaning

See SMS Volume I.5 §2 — The Meaning of Identity.

### Invariants

- Every human has exactly one Identity. There are no duplicates.
- Identity exists independently of any Space.
- Identity exists independently of any authentication method.
- Identity is never deleted. It may be deactivated.
- Identities are never automatically merged. Linking requires explicit human action.

### Contract

| Aspect | Requirement |
|--------|-------------|
| **Identity Identifier** | Every Identity possesses a single, immutable, globally unique identifier. This identifier is created with the Identity and never changes. It must not encode personal information. |
| **Display Name** | Every Identity has a human-readable name chosen by the individual. This name may change. |
| **Authentication Methods** | Every Identity may have zero or more authentication methods linked to it. Each method has a type (email, OAuth provider, phone, passkey, etc.) and an identifier (the value that identifies the human for that method). At most one method may be designated as primary. |
| **Linking** | Authentication methods may be linked to an Identity only through explicit human action. The linking flow is: Detect → Suggest → Verify → Link → Maintain. Detection identifies potential matches. Suggestion presents them to the human. Verification proves ownership. Link associates the method. Maintain preserves the association. |
| **Verification** | Before an authentication method is linked, ownership must be verified. Verification methods include email confirmation, OAuth callback, cryptographic challenge, or in-person verification. The system must support at least two verification methods. |
| **Status** | Every Identity has a status: `active`, `suspended`, or `deactivated`. An active Identity can authenticate and access Spaces. A suspended Identity can authenticate but has restricted access. A deactivated Identity cannot authenticate. |
| **Temporality** | Every Identity records its creation time and last modification time. |

### Anti-goals

- The Identity Contract does NOT define what authentication looks like. Authentication is an implementation concern.
- The Identity Contract does NOT define how identities are stored.
- The Identity Contract does NOT define account creation flows. Account creation is an Identity → Space membership operation.
- The Identity Contract does NOT define what happens after authentication. That is the Permission Contract's domain.

### Evolution Rules

- New authentication method types (new OAuth providers, new passkey standards, etc.) may be added without changing the contract.
- Verification requirements may increase over time. Existing verified methods remain valid.
- The identity identifier format is an implementation detail.

---

## 3. Space Contract

### Purpose

Every Object belongs to exactly one Space. Spaces define boundaries of context, membership, and permission.

### Philosophical Meaning

See SMS Volume I.5 §3 — The Meaning of Space.

### Invariants

- Every Object belongs to exactly one Space.
- An Object's home Space never changes.
- Space membership is explicit. Parent Space membership does not imply child Space membership.
- Permissions are scoped to Spaces.

### Contract

| Aspect | Requirement |
|--------|-------------|
| **Identity** | Every Space has a single, immutable identifier. |
| **Name** | Every Space has a human-readable name. |
| **Type** | Every Space has a type drawn from the set: `personal`, `family`, `organization`, `community`, `project`, `research`. Additional types may be added. |
| **Membership** | Every Space maintains a set of member Identities, each with a role: `owner`, `admin`, `member`, `guest`. An Identity may have different roles in different Spaces. |
| **Nesting** | A Space may have a parent Space. Nesting creates a hierarchy. Parent Space membership does not grant child Space membership. |
| **Status** | Every Space has a lifecycle state: `active`, `archived`, `deleted`. |
| **Temporality** | Every Space records its creation time and last modification time. |

### Anti-goals

- A Space is not a folder or directory.
- A Space is not a database schema or table prefix.
- A Space is not a tenant in a multi-tenant architecture.
- The contract does not specify how Spaces are stored, indexed, or queried.

### Evolution Rules

- New Space types may be added without modifying existing Spaces.
- Membership roles may be extended with custom roles.
- Nesting depth is not architecturally bounded.

---

## 4. Relationship Contract

### Purpose

Relationships are the connections between Objects. They are first-class, graph-navigable, and bidirectional.

### Philosophical Meaning

See SMS Volume I.5 §4 — The Meaning of Relationship.

### Invariants

- Every Relationship connects exactly two Objects.
- Every Relationship has exactly one type.
- Every Relationship is navigable from both endpoints.
- A Relationship does not imply Permission.

### Contract

| Aspect | Requirement |
|--------|-------------|
| **Endpoints** | Every Relationship connects two Objects, designated as source and target. The direction is meaningful but both directions are queryable. |
| **Type** | Every Relationship has exactly one type drawn from the set: `owns`, `member_of`, `works_at`, `reports_to`, `created_by`, `references`, `derived_from`, `supports`, `contradicts`, `attached_to`, `contains`, `part_of`, `follows`, `precedes`, `related_to`. Additional types may be registered. |
| **Bidirectionality** | Every Relationship must be discoverable from both the source and the target. Querying from either side returns the Relationship. |
| **Traversal** | The Relationship system must support traversal from any Object to its connected Objects. Traversal must support type filtering and depth limiting. |
| **Confidence** | Every Relationship carries a confidence score in the range [0, 1]. |
| **Provenance** | Every Relationship records who or what created it. |
| **Temporality** | Every Relationship records its creation time. |

### Anti-goals

- A Relationship is not a foreign key. It is a semantic connection.
- A Relationship is not a Permission.
- The contract does not specify graph traversal algorithms. BFS and DFS are both acceptable.
- The contract does not specify storage for the graph.

### Evolution Rules

- New Relationship types may be registered without modifying existing Relationships.
- Relationship types may be deprecated but instances are preserved.

---

## 5. Conversation Contract

### Purpose

Conversation is how humans discuss Objects. Every Object may have a Conversation attached to it.

### Philosophical Meaning

See SMS Volume I.5 §5 — The Meaning of Conversation.

### Invariants

- Every Conversation is attached to exactly one Object.
- Messages are append-only. They cannot be edited or deleted.
- A Conversation exists in the same Space as its parent Object.
- Participants are a subset of the Space's members.

### Contract

| Aspect | Requirement |
|--------|-------------|
| **Attachment** | A Conversation is attached to exactly one parent Object. That attachment is a Relationship of type `attached_to`. |
| **Messages** | A Conversation contains an ordered sequence of Messages. Each Message has: an author (Identity), a body (text), a type (human, system, suggestion, decision), a timestamp, and optional references to linked Objects. |
| **Immutability** | Messages are append-only. They may not be edited, deleted, or reordered. Corrections are new Messages. |
| **Participants** | A Conversation has a set of participant Identities. Only participants can read or write. Participantship may be derived from the parent Object's Permission model. |
| **Status** | A Conversation has a lifecycle: `active`, `archived`, or `locked`. |

### Anti-goals

- A Conversation is not a chat system. Chat is a communication pattern. Conversation is an attachment to an Object.
- A Conversation is not a notification history.
- A Conversation is not a comment thread. Comments are one type of Message.

### Evolution Rules

- New Message types may be added without modifying existing Messages.
- Conversations may be archived with their parent Object.

---

## 6. Permission Contract

### Purpose

Every action in SHUNYA requires explicit Permission. Permissions are scoped to Identity, Space, Resource Type, and Action.

### Philosophical Meaning

See SMS Volume I.5 §6 — The Meaning of Permission.

### Invariants

- Every action requires explicit Permission.
- Permission is evaluated server-side only.
- Deletion always requires governance evaluation.
- No action is permitted by default.

### Contract

| Aspect | Requirement |
|--------|-------------|
| **Scope** | Every Permission is scoped to a tuple of (Identity, Space, Resource Type, Action). A Permission grants the Identity the ability to perform the Action on Resources of the specified Type within the specified Space. |
| **Actions** | Actions are drawn from the set: `create`, `read`, `update`, `delete`, `approve`, `admin`. Additional actions may be defined by specific Object types. |
| **Evaluation** | Permission evaluation must be deterministic and verifiable. The result of evaluation is either `permitted` or `denied`. There is no intermediate state. |
| **Inheritance** | Permissions may be inherited from parent Spaces. A child Space inherits its parent's Permissions unless explicitly overridden. |
| **Governance** | Sensitive actions (deletion, financial mutations, data exports) require evaluation by the Governance Engine in addition to Permission evaluation. |
| **Observability** | Every Permission evaluation must be observable for audit purposes. |

### Anti-goals

- Permission is not Authentication.
- Permission is not a Role. A Role is a collection of Permissions.
- Permission is not a suggestion.
- The contract does not specify how Permissions are stored or cached.

### Evolution Rules

- Permission granularity may increase (more specific Resource Types) but never decrease.
- Permission evaluation may be cached, but cache TTL must be configurable.

---

## 7. Timeline Contract

### Purpose

Every Object has an immutable Timeline of events. The Timeline is the source of truth for what happened, when, and why.

### Philosophical Meaning

See SMS Volume I.5 §7 — The Meaning of Timeline.

### Invariants

- Every Object has exactly one Timeline.
- Timeline events are append-only.
- Events are ordered within a single Timeline.
- Every state-changing action produces at least one event.

### Contract

| Aspect | Requirement |
|--------|-------------|
| **Attachment** | A Timeline is attached to exactly one parent Object. Every Object has a Timeline. |
| **Events** | A Timeline contains an ordered sequence of Events. Each Event has: an event type, an actor (Identity or system component), a timestamp, the Object's previous state, the Object's new state, and optional metadata. |
| **Immutability** | Events are append-only. They may not be deleted, modified, or reordered. |
| **Ordering** | Events within a single Timeline are ordered by their timestamp. Timestamps are monotonically increasing. |
| **Replayability** | The complete state of an Object at any point in time can be reconstructed by replaying its Timeline. |
| **Evidence** | Events may reference Evidence that supports the state change. |

### Anti-goals

- A Timeline is not a log.
- A Timeline is not a database transaction log.
- A Timeline is not a notification feed.

### Evolution Rules

- New Event types may be added without modifying existing Events.
- Timeline queries must support time-range filtering.
- Timeline events may be compacted only for events older than a defined retention period.

---

## 8. Evidence Contract

### Purpose

Every computed conclusion in SHUNYA carries traceable Evidence. No output exists without provenance.

### Philosophical Meaning

See SMS Volume I.5 §8 — The Meaning of Evidence.

### Invariants

- Every computed conclusion carries at least one Evidence reference.
- Evidence references are resolvable to an Object.
- Evidence chains are acyclic.
- Confidence propagates through chains.

### Contract

| Aspect | Requirement |
|--------|-------------|
| **Attachment** | Evidence references are attached to the Object they support. An Object may have zero or more Evidence references. |
| **Source** | Every Evidence reference points to a source Object that provides the Evidence. The source Object must exist and be resolvable. |
| **Type** | Every Evidence reference has a type: `observation`, `derivation`, `computation`, `assertion`, or `reference`. Additional types may be defined. |
| **Confidence** | Every Evidence reference carries a confidence score in the range [0, 1], representing the system's confidence that the Evidence is correct and relevant. |
| **Chaining** | Evidence may form chains: Object A is Evidence for Object B, which is Evidence for Object C. Chains must be acyclic (no Object may be Evidence for itself, directly or transitively). |
| **Confidence Propagation** | In a chain Object A → Object B → Object C, the confidence that A supports C is at most Confidence(A→B) × Confidence(B→C). |
| **Temporality** | Every Evidence reference records when the Evidence was captured. |

### Anti-goals

- Evidence is not a citation.
- Evidence is not logging.
- Evidence is not a guarantee of truth.
- The contract does not specify how Evidence is stored, indexed, or queried.

### Evolution Rules

- New Evidence types may be added without modifying existing Evidence.
- Evidence may be superseded by new Evidence, but never deleted.
- Historical Evidence preserves the confidence at capture time.

---

*End of SMS Volume II — World Model Contracts*

## Engineering Guidance

Engineering guidance — identifier formats, repository interfaces, serialization schemas, API patterns — is maintained in a separate volume to preserve the constitutional purity of these contracts. See architecture/engineering/ENGINEERING_GUIDANCE.md.
