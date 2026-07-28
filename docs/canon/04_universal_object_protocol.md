# Universal Object Protocol

> **Canonical Document · Phase C1**
> **Status: CANONICAL — Implementation-Independent Contract**
> **Version: 1.0**
> **Supersedes: architecture/adr/ADR-004-UNIVERSAL-OBJECT-CONTRACT.md, architecture/SHUNYA_CORE_MODELS.md §2**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Contract Definition](#2-contract-definition)
3. [Mandatory Fields](#3-mandatory-fields)
4. [Identity](#4-identity)
5. [Metadata](#5-metadata)
6. [Relationships](#6-relationships)
7. [Timeline](#7-timeline)
8. [Lifecycle](#8-lifecycle)
9. [Status](#9-status)
10. [Ownership](#10-ownership)
11. [Permissions](#11-permissions)
12. [Evidence](#12-evidence)
13. [Memory](#13-memory)
14. [AI Context](#14-ai-context)
15. [Search](#15-search)
16. [Audit](#16-audit)
17. [Actions](#17-actions)
18. [Versioning](#18-versioning)
19. [Implementation Requirements](#19-implementation-requirements)
20. [Future Extensibility](#20-future-extensibility)
21. [Relationship to Other Canonical Documents](#21-relationship-to-other-canonical-documents)

---

## 1. Purpose

This document defines the mandatory contract that every UniversalObject must implement. The contract is the interface — not the implementation. Any object that does not implement this contract is not a SHUNYA object.

### 1.1 Why a Protocol?

A protocol (not a class hierarchy) is used because:
- Objects may be implemented in different languages, frameworks, or storage backends
- Legacy objects must be able to conform without changing their core identity
- The protocol defines behavior, not structure
- Multiple implementations can coexist

### 1.2 Conformance

An object conforms to the Universal Object Protocol if it implements all mandatory sections. Conformance is verified by the protocol checker, not by documentation.

---

## 2. Contract Definition

### 2.1 Protocol Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                   UNIVERSAL OBJECT PROTOCOL                       │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Identity │  │ Metadata │  │ Relationships │  │   Timeline   │  │
│  │ (MAND)   │  │ (MAND)   │  │ (MAND)       │  │ (MAND)       │  │
│  └──────────┘  └──────────┘  └──────────────┘  └──────────────┘  │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Lifecycle│  │  Status  │  │  Ownership   │  │ Permissions  │  │
│  │ (MAND)   │  │ (MAND)   │  │ (MAND)       │  │ (MAND)       │  │
│  └──────────┘  └──────────┘  └──────────────┘  └──────────────┘  │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Evidence │  │  Memory  │  │  AI Context  │  │   Search     │  │
│  │ (MAND)   │  │ (OPT)    │  │ (MAND)       │  │ (MAND)       │  │
│  └──────────┘  └──────────┘  └──────────────┘  └──────────────┘  │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐                    │
│  │  Audit   │  │ Actions  │  │  Versioning  │                    │
│  │ (MAND)   │  │ (MAND)   │  │ (MAND)       │                    │
│  └──────────┘  └──────────┘  └──────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Mandatory vs Optional

| Section | Requirement | Rationale |
|---------|------------|-----------|
| **Identity** | MANDATORY | Every object must be uniquely identifiable |
| **Metadata** | MANDATORY | Every object must describe itself |
| **Relationships** | MANDATORY | Isolated objects are useless |
| **Timeline** | MANDATORY | Immutable history is the foundation of trust |
| **Lifecycle** | MANDATORY | Every object must have defined life stages |
| **Status** | MANDATORY | Current state must be queryable |
| **Ownership** | MANDATORY | Every object must be accountable |
| **Permissions** | MANDATORY | Access control is non-negotiable |
| **Evidence** | MANDATORY | Truth requires supporting evidence |
| **Memory** | OPTIONAL | Not all objects retain experiential memory |
| **AI Context** | MANDATORY | AI must understand every object it interacts with |
| **Search** | MANDATORY | Objects must be findable |
| **Audit** | MANDATORY | All actions must be traceable |
| **Actions** | MANDATORY | Objects must define what can be done to them |
| **Versioning** | MANDATORY | Change tracking is essential for trust |

---

## 3. Mandatory Fields

Every UniversalObject must expose the following fields. These fields are the minimum — domain objects may add more.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `object_id` | String (UUID) | Yes | Globally unique, immutable identifier |
| `object_type` | String | Yes | Canonical type from Business Canon |
| `name` | String | Yes | Human-readable name |
| `description` | String | No | Human-readable description |
| `status` | String | Yes | Current lifecycle status |
| `version` | Integer | Yes | Monotonically increasing version |
| `created_at` | ISO-8601 | Yes | Creation timestamp |
| `updated_at` | ISO-8601 | Yes | Last modification timestamp |
| `created_by` | ObjectID | Yes | Identity of creator |
| `updated_by` | ObjectID | Yes | Identity of last modifier |
| `owner_id` | ObjectID | Yes | Current owner |
| `tenant_id` | ObjectID | No | Multi-tenant isolation |
| `space_id` | ObjectID | No | Workspace/space membership |
| `confidence` | Float [0,1] | Yes | Confidence in object's current state |
| `metadata` | Map | Yes | Extensible metadata container |
| `tags` | String[] | No | Free-form categorization |

---

## 4. Identity

### 4.1 Protocol Contract

```
Identity {
    object_id: String (UUID v7)  // Globally unique, immutable
    external_ids: Map<String, String>  // Identity from external systems
    aliases: String[]  // Alternative names/labels
    identity_type: Enum  // Permanent, External, Derived, Temporary, Merged, Split, Deleted
    identity_authority: String  // Identity Engine, Object Factory, Founder, Governance, External
}
```

### 4.2 Rules

- `object_id` is assigned at creation and never changes
- `object_id` is never reused after deletion
- `external_ids` are contextual — two external IDs from different systems may refer to the same entity
- Identity resolution is handled by the Identity Engine, not by individual objects

### 4.3 Example

```json
{
    "object_id": "01J8X2R4K5M7N9Q0T2V4W6Y8Z",
    "external_ids": { "crm": "CRM-12345", "email": "user@example.com" },
    "aliases": ["John Doe", "Johnathan Doe"],
    "identity_type": "permanent",
    "identity_authority": "identity_engine"
}
```

---

## 5. Metadata

### 5.1 Protocol Contract

```
Metadata {
    created_at: ISO-8601  // When the object was created
    updated_at: ISO-8601  // When the object was last modified
    created_by: ObjectID  // Who or what created the object
    updated_by: ObjectID  // Who or what last modified the object
    source: String  // How the object entered the system (api, human, import, system)
    source_detail: String  // Specific source context
    custom: Map<String, Any>  // Extensible metadata
}
```

### 5.2 Rules

- `created_at` and `created_by` are immutable after creation
- `source` is classified: `api`, `human`, `import`, `system`, `external`, `derived`
- `updated_at` is automatically set on every modification
- `custom` is free-form but must not duplicate mandatory fields

### 5.3 Example

```json
{
    "created_at": "2026-07-24T10:30:00Z",
    "updated_at": "2026-07-24T14:15:00Z",
    "created_by": "obj_human_a1b2c3d4",
    "updated_by": "obj_human_a1b2c3d4",
    "source": "human",
    "source_detail": "workspace_import",
    "custom": { "import_batch_id": "batch_20260724_001" }
}
```

---

## 6. Relationships

### 6.1 Protocol Contract

```
Relationships {
    relationships: Relationship[]  // List of typed connections
    add_relationship(target_id, type, metadata): RelationshipID
    remove_relationship(relationship_id): void
    get_relationships(type?, direction?): Relationship[]
    get_related_objects(type?, direction?): UniversalObject[]
}
```

### 6.2 Relationship Structure

```
Relationship {
    relationship_id: String (UUID)
    source_id: ObjectID
    target_id: ObjectID
    relationship_type: String  // From canonical relationship types
    direction: Enum  // Directional, Bidirectional, Hierarchical, Temporal, Contextual, Inherited
    strength: Float [0, 1]
    label: String
    metadata: Map
    created_at: ISO-8601
    evidence_ids: String[]
}
```

### 6.3 Rules

- Relationships are always between two objects
- Relationship types are defined in the Relationship Canon
- A relationship can be directional or bidirectional
- Evidence can support a relationship
- Relationships can be time-bound (temporal)

### 6.4 Example

```json
{
    "relationships": [
        {
            "relationship_id": "rel_abc123",
            "source_id": "obj_human_a1b2c3d4",
            "target_id": "obj_org_x9y8z7",
            "relationship_type": "member_of",
            "direction": "directional",
            "strength": 1.0,
            "label": "Employee",
            "created_at": "2026-01-15T09:00:00Z",
            "evidence_ids": ["ev_contract_001"]
        }
    ]
}
```

---

## 7. Timeline

### 7.1 Protocol Contract

```
Timeline {
    events: TimelineEvent[]  // Chronological list of events
    add_event(event_type, data, source): EventID
    get_events(from?, to?, type?, limit?, offset?): TimelineEvent[]
    get_latest_events(count): TimelineEvent[]
    get_timeline_summary(): TimelineSummary
}
```

### 7.2 Timeline Event Structure

```
TimelineEvent {
    event_id: String (UUID)
    object_id: ObjectID
    event_type: String  // Created, Modified, StatusChanged, RelationshipChanged, etc.
    timestamp: ISO-8601
    actor_id: ObjectID
    data: Map  // Event-specific payload
    evidence_ids: String[]
    previous_state: Map?  // Snapshot of state before the event
    new_state: Map?  // Snapshot of state after the event
}
```

### 7.3 Rules

- Timeline is append-only — events cannot be deleted or modified
- Timeline events are immutable after creation
- Every status change must produce a timeline event
- Every evidence attachment must produce a timeline event
- Timeline is ordered by `timestamp` (ascending)

### 7.4 Example

```json
{
    "timeline": {
        "events": [
            {
                "event_id": "evt_001",
                "object_id": "obj_human_a1b2c3d4",
                "event_type": "object_created",
                "timestamp": "2026-01-15T09:00:00Z",
                "actor_id": "system",
                "data": { "source": "import" }
            },
            {
                "event_id": "evt_002",
                "object_id": "obj_human_a1b2c3d4",
                "event_type": "status_changed",
                "timestamp": "2026-03-20T11:30:00Z",
                "actor_id": "obj_human_a1b2c3d4",
                "data": { "old_status": "observed", "new_status": "recognized" },
                "evidence_ids": ["ev_verification_001"]
            }
        ]
    }
}
```

---

## 8. Lifecycle

### 8.1 Protocol Contract

```
Lifecycle {
    current_stage: String  // Current lifecycle stage
    valid_transitions: Map<String, String[]>  // Valid transitions from each stage
    transition(new_stage, evidence?, reason?): void
    get_lifecycle_history(): StageTransition[]
    can_transition_to(stage): Boolean
}
```

### 8.2 Rules

- Every object has exactly one lifecycle
- Lifecycle stages are defined per object type in the Business Canon
- Transitions must be valid (defined in `valid_transitions`)
- Invalid transitions are rejected
- Each transition requires an evidence reference (for significant transitions)

### 8.3 Example

```json
{
    "current_stage": "active",
    "valid_transitions": {
        "draft": ["active"],
        "active": ["dormant", "archived"],
        "dormant": ["active", "archived"],
        "archived": ["historical", "active"],
        "historical": []
    }
}
```

---

## 9. Status

### 9.1 Protocol Contract

```
Status {
    status: String  // Current status value
    status_detail: String  // Optional detailed status
    status_updated_at: ISO-8601  // When status last changed
    status_updated_by: ObjectID  // Who changed the status
    is_active: Boolean  // Convenience: is the object in an active state?
}
```

### 9.2 Rules

- Status is a subset of lifecycle — it represents the current operational state
- Status must be a valid value within the current lifecycle stage
- Status changes are recorded as timeline events
- `is_active` is derived from the status value

### 9.3 Example

```json
{
    "status": "active",
    "status_detail": "verified",
    "status_updated_at": "2026-03-20T11:30:00Z",
    "status_updated_by": "obj_human_a1b2c3d4",
    "is_active": true
}
```

---

## 10. Ownership

### 10.1 Protocol Contract

```
Ownership {
    owner_id: ObjectID  // Current owner
    owner_type: Enum  // Human, Organization, System, Shared
    owner_history: OwnershipRecord[]  // History of ownership changes
    transfer(new_owner_id, reason?, evidence?): void
    is_owned_by(actor_id): Boolean
}
```

### 10.2 Rules

- Every object has exactly one owner at any time
- Ownership transfer requires consent from current owner
- Ownership history is immutable
- System objects cannot be transferred

### 10.3 Example

```json
{
    "owner_id": "obj_org_x9y8z7",
    "owner_type": "organization",
    "owner_history": [
        {
            "owner_id": "obj_human_a1b2c3d4",
            "from": "2026-01-15T09:00:00Z",
            "to": "2026-06-01T00:00:00Z",
            "reason": "initial_creation"
        },
        {
            "owner_id": "obj_org_x9y8z7",
            "from": "2026-06-01T00:00:00Z",
            "to": null,
            "reason": "org_transfer"
        }
    ]
}
```

---

## 11. Permissions

### 11.1 Protocol Contract

```
Permissions {
    acl: AccessControlList  // List of access control entries
    check_permission(actor_id, action): Boolean
    grant(actor_id, role, scope): void
    revoke(actor_id, role, scope): void
    get_effective_permissions(actor_id): Permission[]
}
```

### 11.2 Rules

- Permissions are role-based at minimum
- Permissions can be overridden with finer-grained ACLs
- Permission checks always return boolean (allow/deny)
- Deny always overrides allow
- Permission changes are recorded as audit events

### 11.3 Example

```json
{
    "acl": {
        "owner": { "actor_id": "obj_human_a1b2c3d4", "role": "owner" },
        "entries": [
            { "actor_id": "obj_human_c5d6e7f8", "role": "editor" },
            { "actor_id": "obj_org_x9y8z7", "role": "viewer" }
        ]
    }
}
```

---

## 12. Evidence

### 12.1 Protocol Contract

```
Evidence {
    evidence_ids: String[]  // References to supporting evidence
    add_evidence(evidence_id): void
    remove_evidence(evidence_id): void
    get_evidence(): Evidence[]
    get_evidence_chain(): EvidenceChain  // Full provenance chain
    get_confidence(): Float  // Confidence derived from evidence
}
```

### 12.2 Rules

- Evidence is append-only — evidence can be added but never removed
- Evidence that is contradicted is marked as superseded, not deleted
- Evidence chains are traversable from object to origin
- Confidence is derived from evidence quality, not asserted

### 12.3 Example

```json
{
    "evidence_ids": ["ev_contract_001", "ev_verification_001"],
    "confidence": 0.92
}
```

---

## 13. Memory

### 13.1 Protocol Contract

```
Memory (OPTIONAL) {
    memory_ids: String[]  // References to memory records
    associate_memory(memory_id): void
    get_memories(type?, from?, to?): Memory[]
    get_relevant_memories(context): Memory[]
}
```

### 13.2 Rules

- Memory is optional — not all objects require experiential memory
- Memory is distinct from evidence (memory is experiential, evidence is factual)
- Memory can decay over time

---

## 14. AI Context

### 14.1 Protocol Contract

```
AIContext {
    ai_summary: String  // Brief summary of what this object is
    ai_understanding: String  // How the AI should understand this object
    relevant_objects: ObjectID[]  // Related objects the AI should consider
    interaction_history: Interaction[]  // Past AI interactions with this object
    get_ai_context(): String  // Full context string for AI prompt
}
```

### 14.2 Rules

- Every object must provide AI context
- AI context must be concise enough for prompt inclusion
- AI context must include enough information for the AI to make decisions
- AI context is generated from the object's current state, not hardcoded

### 14.3 Example

```json
{
    "ai_summary": "Human: John Doe, Member of Acme Corp",
    "ai_understanding": "This is a Human with full agency rights. Treat with respect and obtain consent before actions.",
    "relevant_objects": ["obj_org_x9y8z7", "obj_workspace_m1n2o3"],
    "interaction_history": [
        { "interaction_id": "int_001", "timestamp": "2026-07-23T15:00:00Z", "type": "query", "summary": "Asked about project status" }
    ]
}
```

---

## 15. Search

### 15.1 Protocol Contract

```
Search {
    search_index: String  // Full-text search index of the object
    search_terms: String[]  // Keywords for search
    searchable_fields: String[]  // Which fields are searchable
    search(query): SearchResult[]
    search_by_field(field, value): SearchResult[]
}
```

### 15.2 Rules

- Every object must be searchable
- Search index is derived from the object's fields
- Search respects permissions (results are filtered by actor's access)
- Full-text search is the minimum requirement

---

## 16. Audit

### 16.1 Protocol Contract

```
Audit {
    audit_log: AuditEntry[]  // Immutable audit trail
    log_action(action, actor_id, detail, evidence?): void
    get_audit_log(from?, to?, actor_id?, action?): AuditEntry[]
    verify_integrity(): Boolean  // Verify audit log hasn't been tampered
}
```

### 16.2 Rules

- Audit log is append-only and immutable
- Every action on the object is logged
- Audit entries include: action, actor, timestamp, detail, and optional evidence
- Audit log must be integrity-verifiable (e.g., hash chain)

### 16.3 Example

```json
{
    "audit_log": [
        {
            "entry_id": "aud_001",
            "action": "object_created",
            "actor_id": "system",
            "timestamp": "2026-01-15T09:00:00Z",
            "detail": "Object created via import batch_20260724_001"
        },
        {
            "entry_id": "aud_002",
            "action": "status_changed",
            "actor_id": "obj_human_a1b2c3d4",
            "timestamp": "2026-03-20T11:30:00Z",
            "detail": "Status changed from 'observed' to 'recognized'"
        }
    ]
}
```

---

## 17. Actions

### 17.1 Protocol Contract

```
Actions {
    available_actions: Action[]  // List of actions available for this object
    execute_action(action_name, params, actor_id): ActionResult
    get_available_actions(actor_id): Action[]  // Filtered by actor's permissions
    is_action_available(action_name, actor_id): Boolean
}
```

### 17.2 Action Structure

```
Action {
    name: String  // Canonical action name
    display_name: String  // Human-readable name
    description: String  // What the action does
    required_permission: String  // Permission required
    parameters: Parameter[]  // Action parameters
    effect: String  // Description of what the action does
}
```

### 17.3 Required Actions

Every object must support at least these actions:

| Action | Description |
|--------|-------------|
| `view` | View the object's current state |
| `update` | Modify the object's mutable fields |
| `delete` | Delete (retire) the object |
| `add_evidence` | Attach evidence to the object |
| `add_relationship` | Create a relationship to another object |
| `get_timeline` | View the object's timeline |
| `get_audit_log` | View the object's audit trail |

---

## 18. Versioning

### 18.1 Protocol Contract

```
Versioning {
    version: Integer  // Current version number
    version_history: VersionRecord[]  // History of versions
    get_version(version_number): UniversalObject  // Snapshot at version
    get_latest_version(): UniversalObject
    compare_versions(v1, v2): Diff
}
```

### 18.2 Rules

- Version numbers are monotonically increasing integers
- Every modification creates a new version
- Previous versions are immutable snapshots
- Version history is retained for audit purposes
- Version garbage collection is governed by retention policy

### 18.3 Example

```json
{
    "version": 7,
    "version_history": [
        { "version": 1, "timestamp": "2026-01-15T09:00:00Z", "modified_by": "system" },
        { "version": 2, "timestamp": "2026-02-01T10:00:00Z", "modified_by": "obj_human_a1b2c3d4" },
        { "version": 3, "timestamp": "2026-03-15T11:00:00Z", "modified_by": "obj_human_a1b2c3d4" },
        { "version": 4, "timestamp": "2026-04-10T09:30:00Z", "modified_by": "obj_human_c5d6e7f8" },
        { "version": 5, "timestamp": "2026-05-20T14:00:00Z", "modified_by": "obj_human_a1b2c3d4" },
        { "version": 6, "timestamp": "2026-06-01T08:00:00Z", "modified_by": "system" },
        { "version": 7, "timestamp": "2026-07-24T10:30:00Z", "modified_by": "obj_human_a1b2c3d4" }
    ]
}
```

---

## 19. Implementation Requirements

### 19.1 Minimum Viable Conformance

An implementation conforms to the protocol if it satisfies:

1. Every object has a unique `object_id` that is immutable
2. Every object provides the mandatory fields (§3)
3. Every object supports the required actions (§17.3)
4. Every object maintains an immutable timeline (§7)
5. Every object maintains an immutable audit log (§16)
6. Every object supports permission checks (§11)
7. Every object provides AI context (§14)

### 19.2 Conformance Testing

Each implementation must provide:
- A conformance test suite that verifies all mandatory sections
- A protocol compliance report
- Evidence of passing all conformance tests before deployment

---

## 20. Future Extensibility

### 20.1 Protocol Extensions

The protocol can be extended by:
1. Adding new optional sections (not modifying mandatory ones)
2. Adding new fields to existing sections (not changing existing field semantics)
3. Adding new required actions (not removing existing ones)

### 20.2 Versioning the Protocol

The protocol itself is versioned. Protocol version changes are:
- **Minor** — adding optional sections or fields (backward compatible)
- **Major** — changing mandatory sections (requires migration)

---

## 21. Relationship to Other Canonical Documents

| Document | Relationship |
|----------|-------------|
| **00_universal_ontology.md** | The protocol implements the ontological properties of every concept — Identity (§4), Relationship (§6), State (§7), Event (§8), Evidence (§10), Decision (§11), Action (§12), Outcome (§13) |
| **02_shunya_constitution.md** | Protocol enforces Constitutional requirements (evidence, audit, consent) |
| **03_business_canon.md** | Business objects implement this protocol |
| **05_runtime_canon.md** | Runtime manages objects through this protocol |
| **06_data_canon.md** | Data architecture must support all protocol sections |
| **07_ai_canon.md** | AI uses the protocol's AI Context section |
| **08_experience_canon.md** | Experience surfaces protocol actions to humans |
| **09_repository_canon.md** | Protocol implementation is a core module |
| **10_migration_canon.md** | Migration converts existing objects to protocol conformance |
| **11_engineering_canon.md** | Engineering standards enforce protocol compliance |
| **12_launch_roadmap.md** | Protocol implementation is a foundational milestone |

---

> **Next:** [05_runtime_canon.md](05_runtime_canon.md)