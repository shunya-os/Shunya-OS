# SHUNYA Master Specification — Volume II: World Model

**Status:** Draft — Awaiting Founder Review
**Version:** 2.0.0
**Date:** 2026-07-22
**Author:** Hermes Agent (Nous Research)
**Authority:** SHUNYA Constitution, GENESIS Directive, GENESIS II Directive

---

## Preamble

This specification defines the SHUNYA World Model — the canonical contracts that every implementation, regardless of language or platform, must satisfy.

The World Model is **language-agnostic**. It describes *what* must be true, not *how* to achieve it. Code is one implementation of these contracts. If the code and the contract disagree, the contract is authoritative.

**Status:** This is Volume II. Volume I (SHUNYA Core Models, `architecture/SHUNYA_CORE_MODELS.md`) defined the foundational architecture standard. This volume supersedes and extends it with formal contracts.

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
9. Object Registry
10. SHUNYA OS Validation

---

## 1. Universal Object Contract

### 1.1 Purpose

Every meaningful entity in SHUNYA inherits from the Universal Object Contract. No entity may bypass this contract without explicit architectural approval.

### 1.2 Contract

| Field | Type | Required | Immutable | Description |
|-------|------|----------|-----------|-------------|
| `object_id` | UUID (time-ordered) | Yes | Yes | Globally unique identifier. Never reused. |
| `space_id` | SpaceID | Yes | Yes | Owning space at creation. |
| `object_type` | String | Yes | Yes | Canonical type name. Must be registered in the Object Registry. |
| `name` | String | Yes | No | Human-readable display name. |
| `status` | Enum(active, superseded, archived, pending, deleted) | Yes | No | Lifecycle state. |
| `version` | Positive Integer | Yes | No | Monotonically increasing. Starts at 1. |
| `created_at` | Timestamp (UTC) | Yes | Yes | When the object was first created. |
| `updated_at` | Timestamp (UTC) | Yes | No | When the object was last modified. |
| `created_by` | IdentityID | Yes | Yes | Who or what created this object. |
| `updated_by` | IdentityID | Yes | No | Who or what last modified this object. |
| `confidence` | Float [0.0, 1.0] | Yes | No | Canonical confidence score. |
| `evidence` | EvidenceRef[] | No | No | Evidence chain supporting this object. |
| `relationships` | RelationshipRef[] | No | No | Typed links to other objects. |
| `metadata` | JSON | No | No | Arbitrary key-value metadata. |

### 1.3 Lifecycle States

```
ACTIVE ↔ SUPERSEDED (new version exists)
ACTIVE → ARCHIVED (no longer active, preserved for history)
ACTIVE → PENDING (awaiting confirmation)
ACTIVE → DELETED (policy-aware deletion, see Permission Contract)
SUPERSEDED → ARCHIVED
```

### 1.4 Serialization

Every Object must support a canonical `to_dict()` serialization that includes all contract fields. Implementations may add platform-specific serialization formats, but the canonical form must always be present.

### 1.5 Behavioral Requirements

- **Deterministic ID generation:** Given the same creation context, the same ID must be generated (time-ordered UUIDs satisfy this).
- **Immutable fields:** `object_id`, `space_id`, `object_type`, `created_at`, `created_by` must never change after creation.
- **Version increments:** Every mutation that changes the object's meaningful state must increment `version`.

---

## 2. Identity Contract

### 2.1 Purpose

SHUNYA Identity is a permanent human identity. It is not an email address, not an account, not a user record. An identity owns multiple authentication methods. A human always has exactly one SHUNYA Identity. Organizations never own identities.

### 2.2 Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `identity_id` | IdentityID (`sid_` prefix) | Yes | Immutable internal identifier. Never changes. |
| `display_name` | String | Yes | Human-readable name the identity chose. |
| `auth_methods` | AuthenticationMethod[] | Yes | All authentication methods linked to this identity. |
| `status` | Enum(active, suspended, deactivated) | Yes | Identity lifecycle state. |
| `created_at` | Timestamp (UTC) | Yes | When the identity was created. |
| `updated_at` | Timestamp (UTC) | Yes | When the identity was last modified. |

### 2.3 Authentication Method Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `method_type` | Enum(email, gmail, microsoft, company_email, phone, passkey, apple_login, oauth:*) | Yes | The type of authentication method. |
| `identifier` | String | Yes | The value that identifies the user for this method (email address, phone number, OAuth sub, etc.). |
| `is_primary` | Boolean | No | Whether this is the primary method. At most one primary. |
| `verified_at` | Timestamp | No | When this method was verified. Null means unverified. |

### 2.4 Identity Linking Flow

Identity linking must follow this sequence:

```
DETECT → SUGGEST → VERIFY → LINK → MAINTAIN
```

**DETECT:** The system identifies that two authentication methods may belong to the same human (shared email, shared phone, OAuth email match, etc.).

**SUGGEST:** The system presents the potential link to the human. The human must be shown exactly what will be linked. The system never links automatically.

**VERIFY:** The human must prove ownership of both methods. Verification methods include:
- Email confirmation (code sent to the email address)
- OAuth callback (re-authenticate via the identity provider)
- Cryptographic challenge (for passkeys)
- In-person verification (for high-security contexts)

**LINK:** Upon successful verification, the authentication methods become linked to the same SHUNYA Identity.

**MAINTAIN:** The system maintains the linked identity. If a conflict is detected (e.g., two identities claim the same email), the system returns to DETECT — never merges silently.

### 2.5 Non-Goals

- Identity is NOT a user account. Accounts are Space-level membership records.
- Identity is NOT an email address. Email is one possible authentication method.
- Identity is NOT tied to any organization. An identity exists independently.
- Identity is NEVER automatically merged. Always detect → suggest → verify → link.

---

## 3. Space Contract

### 3.1 Purpose

Everything in SHUNYA exists inside one or more Spaces. Spaces provide context, isolation, permission boundaries, and membership. A Space is the universal container primitive.

### 3.2 Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `space_id` | SpaceID (`spc_` prefix) | Yes | Immutable identifier. |
| `name` | String | Yes | Human-readable name. |
| `space_type` | Enum(personal, family, organization, community, project, research) | Yes | The type of space. |
| `parent_space_id` | SpaceID | No | Parent space for nesting. |
| `members` | Membership[] | Yes | Identities with roles in this space. |
| `status` | Enum(active, archived, deleted) | Yes | Lifecycle state. |
| `created_at` | Timestamp | Yes | Creation time. |
| `updated_at` | Timestamp | Yes | Last modification time. |

### 3.3 Membership Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `identity_id` | IdentityID | Yes | The identity that is a member. |
| `space_id` | SpaceID | Yes | The space they belong to. |
| `role` | Enum(owner, admin, member, guest) | Yes | The role in this space. |
| `joined_at` | Timestamp | Yes | When they joined. |
| `invited_by` | IdentityID | No | Who invited them. |

### 3.4 Space Types

| Type | Owner | Visibility | Typical Use |
|------|-------|------------|-------------|
| `personal` | Individual identity | Private | Personal thinking, notes, documents |
| `family` | Group of identities | Members only | Family planning, shared documents |
| `organization` | Organization identity | Members only | Business operations |
| `community` | Group of identities | Members only | Shared interest groups |
| `project` | Identity or group | Members only | Time-bounded collaborative work |
| `research` | Identity or group | Members only | Long-term investigation |

### 3.5 Nesting

A Space MAY have a `parent_space_id`. When a Space has a parent:
- Members of the parent are NOT automatically members of the child (unless explicitly added).
- Permissions flow from parent to child by default, but can be overridden.
- Objects in a child Space are visible to parent Space members only if explicitly shared.

### 3.6 Implementation Guidance

- Every object references its containing Space's `space_id`.
- Queries SHOULD always be scoped by `space_id` for isolation.
- The existing `Tenant`/`Organization` model maps to a Space of type `organization`.
- The existing `Workspace` model maps to a Space of type `project` with a parent Space.

---

## 4. Relationship Contract

### 4.1 Purpose

Relationships are first-class citizens in SHUNYA. They are not foreign keys. They are graph-navigable, typed, and bidirectional. The relationship layer enables reality to be navigated as a connected graph.

### 4.2 Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `relationship_id` | UUID | Yes | Unique identifier for this relationship instance. |
| `source_id` | ObjectID | Yes | The source object. |
| `target_id` | ObjectID | Yes | The target object. |
| `relationship_type` | Enum(owns, member_of, works_at, reports_to, created_by, references, derived_from, supports, contradicts, attached_to, contains, part_of, follows, precedes, related_to) | Yes | The type of relationship. |
| `label` | String | No | Human-readable label for this relationship. |
| `confidence` | Float [0.0, 1.0] | Yes | Confidence in this relationship. |
| `created_at` | Timestamp | Yes | When the relationship was established. |
| `created_by` | IdentityID | Yes | Who or what established the relationship. |
| `metadata` | JSON | No | Additional context. |

### 4.3 Behavioral Requirements

- **Bidirectional tracking:** Every relationship MUST be queryable from both the source and target side.
- **Graph traversal:** The system MUST support BFS/DFS traversal from any starting object.
- **Type filtering:** Traversal MUST support filtering by relationship type.
- **Depth limiting:** Traversal MUST support a maximum depth parameter.
- **No silent cycles:** The system SHOULD detect and report relationship cycles.

### 4.4 Relationship Types

```
owns          — Object A owns Object B
member_of     — Identity A is a member of Space B
works_at      — Identity A works at Organization B
reports_to    — Identity A reports to Identity B
created_by    — Object A was created by Actor B
references    — Object A references Object B
derived_from  — Object A was derived from Object B
supports      — Object A supports Object B (evidence)
contradicts   — Object A contradicts Object B
attached_to   — Object A is attached to Object B (conversation, document)
contains      — Space A contains Object B
part_of       — Object A is part of Object B
follows       — Event A follows Event B (temporal)
precedes      — Event A precedes Event B (temporal)
related_to    — Generic association
```

### 4.5 Implementation Guidance

- The Relationship Service (formerly RelationshipEngine) maintains an in-memory or persistent graph.
- Adding a relationship automatically tracks it bidirectionally.
- The `remove` operation must clean up both directions.
- Consider an adjacency list or graph database for large-scale deployments.

---

## 5. Conversation Contract

### 5.1 Purpose

Conversation belongs to Objects. There is no isolated chat system. Every Object that can be discussed has a conversation attached to it. Conversation is the universal collaboration primitive.

### 5.2 Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conversation_id` | UUID | Yes | Unique identifier for this conversation. |
| `object_id` | ObjectID | Yes | The object this conversation is attached to. |
| `messages` | Message[] | Yes | Ordered sequence of messages. |
| `participants` | IdentityID[] | Yes | Identities participating in this conversation. |
| `status` | Enum(active, archived, locked) | Yes | Conversation state. |
| `created_at` | Timestamp | Yes | When the conversation started. |
| `updated_at` | Timestamp | Yes | When the last message was added. |

### 5.3 Message Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message_id` | UUID | Yes | Unique identifier. |
| `author_id` | IdentityID | Yes | Who wrote this message. |
| `body` | String | Yes | The message content. |
| `message_type` | Enum(human, system, suggestion, decision) | Yes | The type of message. |
| `linked_objects` | ObjectID[] | No | Objects referenced in this message. |
| `created_at` | Timestamp | Yes | When the message was sent. |

### 5.4 Behavioral Requirements

- **Object attachment:** Every conversation is attached to exactly one object.
- **Immutability:** Messages are append-only. Editing is prohibited (new message for corrections).
- **Participation:** Only participants can read and write to a conversation.
- **Linking:** Messages may link to evidence, decisions, predictions, or other objects.

### 5.5 Implementation Guidance

- The existing `app/collaboration/` modules contain conversation primitives that should be adapted to this contract.
- Conversation should be a relationship type (`attached_to`) between a Conversation object and its parent object.
- Pre-auth conversations (E1) are temporary conversations attached to a session, not a persistent object.

---

## 6. Permission Contract

### 6.1 Purpose

Every action in SHUNYA requires explicit permission. Permissions are evaluated at the Space level, with inheritance from parent Spaces. No authorization logic exists in the frontend.

### 6.2 Permission Model

```
Identity → Role → Space → Permission Set
```

- An Identity has a **Role** in a **Space**.
- A Role grants a **Permission Set** (set of actions on resource types).
- Permission Sets are evaluated at the Space boundary.
- Child Spaces inherit base permissions from parent Spaces, with optional overrides.

### 6.3 Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `permission_id` | UUID | Yes | Unique identifier. |
| `space_id` | SpaceID | Yes | The space this permission applies to. |
| `role` | String | Yes | The role name (owner, admin, member, guest, or custom). |
| `resource_type` | String | Yes | The type of resource this permission governs. |
| `actions` | String[] | Yes | Allowed actions (create, read, update, delete, approve, admin). |
| `inherited` | Boolean | Yes | Whether this permission is inherited from a parent space. |

### 6.4 Deletion Governance

Deletion is policy-aware, not hardcoded. The permission system must support:

- **Personal objects:** Identity may delete without additional approval.
- **Shared objects:** Deletion requires Space admin approval.
- **Organizational objects:** Deletion requires governance policy evaluation.
- **Audit trail:** All deletions are recorded in the Timeline.

### 6.5 Behavioral Requirements

- **No frontend authorization:** The server is the sole authority on permissions.
- **Explicit by default:** No action is permitted without an explicit permission.
- **Governance hooks:** Sensitive actions (deletion, financial, data mutation) must pass through the Governance Engine.
- **Caching:** Permission evaluations may be cached per session with a configurable TTL.

---

## 7. Timeline Contract

### 7.1 Purpose

Every Object has an immutable timeline of events. The timeline is the source of truth for what happened, when, and why. State transitions are recorded, never overwritten.

### 7.2 Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | UUID | Yes | Unique identifier. |
| `object_id` | ObjectID | Yes | The object this event belongs to. |
| `event_type` | String | Yes | The type of event (created, updated, archived, permission_changed, etc.). |
| `actor_id` | IdentityID | Yes | Who or what caused this event. |
| `previous_state` | JSON | No | The object state before this event. |
| `new_state` | JSON | No | The object state after this event. |
| `timestamp` | Timestamp | Yes | When the event occurred. |
| `metadata` | JSON | No | Additional context. |

### 7.3 Behavioral Requirements

- **Append-only:** Events are never deleted or modified.
- **Ordered:** Events within a single object's timeline are ordered by timestamp.
- **Replayable:** The complete state of an object at any point in time can be reconstructed by replaying its timeline.
- **Evidence linkage:** Timeline events may reference evidence that supports the state change.

---

## 8. Evidence Contract

### 8.1 Purpose

Every computed conclusion in SHUNNY carries traceable evidence. No output exists without provenance. Evidence is the foundation of explainability.

### 8.2 Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `evidence_id` | UUID | Yes | Unique identifier. |
| `object_id` | ObjectID | Yes | The object this evidence supports. |
| `source_object_id` | ObjectID | Yes | The object that provides the evidence. |
| `source_field` | String | No | The specific field in the source object. |
| `evidence_type` | Enum(observation, derivation, computation, assertion, reference) | Yes | How the evidence was produced. |
| `confidence` | Float [0.0, 1.0] | Yes | Confidence in this evidence. |
| `captured_at` | Timestamp | Yes | When the evidence was captured. |
| `metadata` | JSON | No | Additional context. |

### 8.3 Evidence Chain

Evidence can form chains: Object A is evidence for Object B, which is evidence for Object C. The system must support:

- **Direct evidence:** A single source supporting a conclusion.
- **Chained evidence:** A → B → C where each link is a separate evidence record.
- **Convergent evidence:** Multiple independent sources supporting the same conclusion.

### 8.4 Behavioral Requirements

- **Traceable:** Every evidence reference can be resolved to the source object.
- **Confidence propagation:** Confidence in chained evidence is the product of confidence at each link.
- **Immutable:** Evidence records are never deleted.

---

## 9. Object Registry

### 9.1 Purpose

The Object Registry is the central authority for all object types in the system. Every object type must register itself with the registry. No object-specific code should bypass this registry.

### 9.2 Registration Contract

Every object type registers:

| Registration Field | Required | Description |
|-------------------|----------|-------------|
| `type_name` | Yes | Canonical type name (e.g., "SHUNYAIdentity", "Space", "Conversation"). |
| `schema` | Yes | Canonical schema defining all fields, types, and constraints. |
| `lifecycle` | Yes | Valid state transitions for this object type. |
| `relationships` | Yes | Allowed relationship types to/from other object types. |
| `capabilities` | Yes | What this object type can do (CRUD, approve, execute, etc.). |
| `search_behavior` | Yes | How this object type is indexed and searched. |
| `ai_behavior` | No | How AI engines interact with this object type. |
| `renderers` | No | How this object type is displayed in various contexts. |

### 9.3 Registry Operations

```
register(type_name, schema, lifecycle, relationships, capabilities, search_behavior, ai_behavior, renderers)
get_type(type_name) → Registration
list_types() → Registration[]
resolve_handler(type_name, capability) → Handler
```

### 9.4 Handler Resolution

The registry supports capability-based handler resolution:

```python
# Pseudocode
handler = registry.resolve_handler("Invoice", "approve")
handler.execute(invoice_id)
```

This eliminates switch statements and object-specific routing. Every capability is looked up dynamically.

### 9.5 Implementation Guidance

- The existing `ObjectRegistry` in `app/kernel/object.py` is a starting point and should be extended to include all registration fields.
- Registration should happen at module import time via a metaclass or decorator.
- The registry should be queryable at runtime for introspection, documentation generation, and API routing.

---

# Tenant Validation Example

### 10.1 Purpose

An example tenant (e.g., a travel business) validates the architecture without compromising business-agnostic design. All capabilities must be demonstrable through tenant scenarios.

### 10.2 Validation Scenario: Customer Journey

```
1. Identity: Alice creates her SHUNYA Identity (sid_...)
   → She authenticates via email + Google OAuth
   → Both methods link to the same identity

2. Space: Alice creates a Personal Space
   → She then joins an Organization Space (e.g., a travel company)

3. Object: A "Booking Inquiry" is created as an Object
   → It has a conversation attached
   → It has relationships to: Alice, the trip, the offer
   → It has a timeline of events
   → It has evidence (Alice's message, the offer document)

4. Relationship: The Inquiry is related to the Trip, the Offer, Alice
   → The system can traverse: Inquiry → Trip → Offer → Approval

5. Conversation: The Inquiry has a conversation
   → Alice, the agent, and the manager participate
   → Messages are linked to evidence (quotes, documents)

6. Permission: Only Alice and tenant agents can view the Inquiry
   → Deletion requires agent approval
   → Financial changes require manager approval

7. Timeline: Every state change is recorded
   → Created → Offer Sent → Negotiating → Approved → Booked
   → Each transition has evidence

8. Evidence: Every decision has provenance
   → "Approved because price within policy" → policy document
   → "Rejected because unavailable" → supplier response
```

### 10.3 Business-Agnostic Verification

The contracts above contain zero travel-specific logic. The word "booking" appears only in the validation scenario. The implementation must:

- Store travel data as Object metadata, not as domain-specific fields.
- Define travel-specific behavior as Space-level policies, not kernel changes.
- Map tenant's concepts to universal primitives (Inquiry → Object, Agent → Identity with Role, etc.).

---

## Appendix A: Terminology Mapping

| Implementation (v1.x) | Specification (v2.0) |
|----------------------|---------------------|
| `IdentityStore` | Identity Repository |
| `RelationshipEngine` | Relationship Service |
| `UniversalObject` class | Universal Object Contract |
| `SpaceStore` | Space Repository |
| `ObjectRegistry` | Object Registry (extended) |
| `TeamMember` | Legacy authentication wrapper |
| `Tenant` | Organization-type Space |
| `Workspace` | Project-type Space (child of Organization) |

## Appendix B: Required ADRs

The following ADRs are required before implementation proceeds:

1. ADR-004: Universal Object Contract ✅ (drafted)
2. ADR-005: SHUNYA Universal Identity ✅ (drafted)
3. ADR-006: Space Architecture ✅ (drafted)
4. ADR-007: Relationship Contract (pending)
5. ADR-008: Conversation Contract (pending)
6. ADR-009: Permission Contract (pending)
7. ADR-010: Timeline Contract (pending)
8. ADR-011: Evidence Contract (pending)
9. ADR-012: Object Registry (pending)

---

*End of SMS Volume II — World Model*