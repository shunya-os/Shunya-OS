# Data Canon

> **Canonical Document · Phase C1**
> **Status: CANONICAL — Derivation from Business Canon + Protocol**
> **Version: 1.0**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Data Architecture Principles](#2-data-architecture-principles)
3. [Canonical Data Architecture](#3-canonical-data-architecture)
4. [Object Storage Model](#4-object-storage-model)
5. [Timeline Storage Model](#5-timeline-storage-model)
6. [Relationship Storage Model](#6-relationship-storage-model)
7. [Event Storage Model](#7-event-storage-model)
8. [Search Index](#8-search-index)
9. [Existing Model Classification](#9-existing-model-classification)
10. [Data Security and Privacy](#10-data-security-and-privacy)
11. [Future Extensibility](#11-future-extensibility)
12. [Relationship to Other Canonical Documents](#12-relationship-to-other-canonical-documents)

---

## 1. Purpose

This document derives the canonical data architecture from the Business Canon (what objects exist), the Universal Object Protocol (what contracts they implement), and the Runtime Canon (how they behave). It classifies every existing SQLAlchemy model and defines the target data architecture.

**Documentation only.** No code changes. No schema changes. No migrations.

---

## 2. Data Architecture Principles

### 2.1 Principles

| Principle | Rationale |
|-----------|-----------|
| **Objects, not tables** | The data architecture mirrors the object model, not the database engine |
| **Timeline is sacred** | Immutable event sourcing is the foundation of trust |
| **Evidence before fact** | All data must be traceable to its evidential origins |
| **Domain independence** | Core data stores have no domain-specific knowledge |
| **Separation of concerns** | Object store, event store, timeline store, search index are distinct |
| **Version is truth** | Every object modification creates a new version; no destructive updates |
| **Privacy by design** | Data classification determines storage, access, and retention |
| **Append-only for trust** | Immutability prevents tampering and enables audit |

### 2.2 Storage Tiers

| Tier | Purpose | Characteristics |
|------|---------|----------------|
| **Hot** | Active objects, recent timeline | Fast read/write, full search, indexed |
| **Warm** | Archived objects, older timeline | Slower read, indexed, compressed |
| **Cold** | Historical data, audit logs | Infrequent read, compressed, minimal index |
| **Audit** | Immutable audit trail | Write-once, read-never (except for audit) |

---

## 3. Canonical Data Architecture

### 3.1 Store Types

```
┌──────────────────────────────────────────────────────────────────┐
│                    SHUNYA DATA ARCHITECTURE                       │
│                                                                   │
│  ┌──────────────────┐    ┌──────────────────┐                    │
│  │   Object Store   │    │   Event Store    │                    │
│  │                  │    │                  │                    │
│  │  - Current state │    │  - Immutable     │                    │
│  │  - Versioned     │    │  - Append-only   │                    │
│  │  - Indexed       │    │  - Ordered       │                    │
│  └──────────────────┘    └──────────────────┘                    │
│         │                         │                               │
│         │                         │                               │
│         ▼                         ▼                               │
│  ┌──────────────────┐    ┌──────────────────┐                    │
│  │ Timeline Store   │    │  Search Index    │                    │
│  │                  │    │                  │                    │
│  │  - Object events │    │  - Full-text     │                    │
│  │  - Chronological │    │  - Vector (AI)   │                    │
│  │  - Immutable     │    │  - Faceted       │                    │
│  └──────────────────┘    └──────────────────┘                    │
│                                                                   │
│  ┌──────────────────┐    ┌──────────────────┐                    │
│  │  Audit Store     │    │ Relationship    │                    │
│  │                  │    │    Graph        │                    │
│  │  - Immutable     │    │                  │                    │
│  │  - Integrity     │    │  - Edge store    │                    │
│  │  - Tamper-proof  │    │  - Traversable   │                    │
│  └──────────────────┘    └──────────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Store Responsibilities

| Store | Primary Purpose | Canonical Reference |
|-------|----------------|---------------------|
| **Object Store** | Current state + version history of all objects | 04 §3, §18 |
| **Event Store** | Immutable record of all events | 04 §7, 05 §4 |
| **Timeline Store** | Per-object chronological event views | 04 §7, 05 §6 |
| **Search Index** | Full-text and vector search | 04 §15 |
| **Audit Store** | Immutable, integrity-verified audit trail | 04 §16 |
| **Relationship Graph** | Traversable graph of all relationships | 04 §6 |

### 3.3 Storage Backend Independence

Each store may use any backend:
- **Object Store**: SQL (PostgreSQL), NoSQL (MongoDB), or hybrid
- **Event Store**: Event store (EventStoreDB), Kafka, or SQL with append-only tables
- **Timeline Store**: Same as Object Store or separate time-series DB
- **Search Index**: Elasticsearch, Meilisearch, or PostgreSQL full-text
- **Audit Store**: Append-only SQL, blockchain, or immutable log
- **Relationship Graph**: SQL (adjacency lists), graph DB (Neo4j, Dgraph)

The architecture describes *what* each store does, not *how* it does it.

---

## 4. Object Storage Model

### 4.1 Canonical Object Schema

Every stored object has this logical schema:

```
ObjectRecord {
    object_id: UUID v7 (PK)
    object_type: String (indexed)
    tenant_id: UUID (indexed, shard key)
    space_id: UUID (indexed)
    
    -- Mandatory fields (04 §3)
    name: String
    description: Text?
    status: String (indexed)
    version: Integer
    confidence: Float
    owner_id: UUID (indexed)
    created_by: UUID
    updated_by: UUID
    
    -- Timestamps
    created_at: Timestamp (indexed)
    updated_at: Timestamp
    
    -- Flexible payload
    attributes: JSONB   -- Domain-specific attributes
    metadata: JSONB     -- Extensible metadata
    tags: String[]      -- Categorization tags
    
    -- Relationship references
    evidence_ids: UUID[]
    relationship_ids: UUID[]
    
    -- AI context
    ai_summary: Text?
    search_index: TSVector?
}
```

### 4.2 Versioning Strategy

Objects use versioning, not destructive updates:

| Version | Schema | Use Case |
|---------|--------|----------|
| Current | ObjectRecord (latest) | Fast reads, updates |
| History | ObjectVersion (object_id, version, state, timestamp) | Audit, rollback, temporal queries |
| Snapshot | ObjectSnapshot (object_id, version, full_state, captured_at) | Point-in-time queries, temporal intelligence |

### 4.3 Storage Strategies

| Strategy | Description | When to Use |
|----------|-------------|-------------|
| **Current + History** | Current state in main table, history in version table | Most objects |
| **Snapshot** | Full state snapshots at intervals + event log rebuild | High-volume objects |
| **Event Sourcing** | Only events stored; current state is derived | Audit-critical objects |
| **Hybrid** | Current state cached, authoritative from event store | Maximum audit requirements |

---

## 5. Timeline Storage Model

### 5.1 Logical Schema

```
TimelineEvent {
    event_id: UUID v7 (PK)
    object_id: UUID (FK, indexed)
    event_type: String (indexed)
    timestamp: Timestamp (indexed, sort key)
    actor_id: UUID (indexed)
    
    -- Event payload
    previous_state: JSONB?
    new_state: JSONB?
    data: JSONB
    
    -- Evidence
    evidence_ids: UUID[]
    
    -- Audit
    audit_hash: String  -- Hash for chain integrity
    previous_event_hash: String  -- Pointer to previous event in chain
}
```

### 5.2 Integrity Chain

```
Event 1 (hash_1 = H(data_1 || "0"))
    │
    ▼
Event 2 (hash_2 = H(data_2 || hash_1))
    │
    ▼
Event 3 (hash_3 = H(data_3 || hash_2))
    │
    ▼
...
```

Each event's hash includes the previous event's hash, creating an integrity chain. Tampering with any event breaks all subsequent hashes.

---

## 6. Relationship Storage Model

### 6.1 Edge Schema

```
RelationshipEdge {
    relationship_id: UUID v7 (PK)
    source_id: UUID (FK, indexed)
    target_id: UUID (FK, indexed)
    relationship_type: String (indexed)
    
    -- Direction
    direction: Enum (directional, bidirectional, hierarchical, temporal, contextual, inherited)
    
    -- Properties
    strength: Float [0, 1]
    label: String
    metadata: JSONB
    
    -- Time bounds
    valid_from: Timestamp
    valid_until: Timestamp?
    
    -- Evidence
    evidence_ids: UUID[]
    
    -- Audit
    created_at: Timestamp
    created_by: UUID
    updated_at: Timestamp
}
```

### 6.2 Traversal Operations

The Relationship Graph must support:

| Operation | Description |
|-----------|-------------|
| **Get neighbors** | All objects connected to a given object |
| **Get by type** | All relationships of a specific type |
| **Path finding** | Find a path between two objects |
| **Subgraph** | Get all objects within N hops of a given object |
| **BFS/DFS** | Standard graph traversal algorithms |
| **Filtered traversal** | Traverse with type/strength/time constraints |

---

## 7. Event Storage Model

### 7.1 Logical Schema

```
SystemEvent {
    event_id: UUID v7 (PK)
    event_type: String (indexed)
    event_version: Integer
    
    timestamp: Timestamp (sort key)
    source: String
    
    actor_id: UUID
    object_id: UUID (indexed)
    related_object_ids: UUID[]
    
    payload: JSONB
    
    evidence_ids: UUID[]
    priority: Enum
    ttl: Duration?
    
    metadata: JSONB
    
    -- Indexed for search
    searchable_text: Text?
    
    -- Integrity
    integrity_hash: String
}
```

### 7.2 Event Retention

| Priority | Hot Retention | Warm Retention | Total Retention |
|----------|---------------|----------------|-----------------|
| Critical | 90 days | 2 years | 10 years |
| High | 30 days | 1 year | 7 years |
| Normal | 7 days | 6 months | 3 years |
| Low | 1 day | 30 days | 1 year |

---

## 8. Search Index

### 8.1 Indexed Fields

Every object's searchable fields include:

| Field | Index Type | Weight |
|-------|-----------|--------|
| `name` | Full-text | High |
| `description` | Full-text | Medium |
| `ai_summary` | Full-text | High |
| `tags` | Keyword | Medium |
| `object_type` | Filter | — |
| `status` | Filter | — |
| `created_at` | Range | — |
| `owner_id` | Filter | — |
| `attributes` | Full-text (domain) | Low |
| **Embedding** | Vector (cosine) | For AI similarity search |

### 8.2 Search Features

| Feature | Description |
|---------|-------------|
| Full-text search | Across all text fields |
| Vector search | Semantic similarity (AI embedding) |
| Faceted search | Filter by type, status, owner, tags |
| Boolean search | AND, OR, NOT operators |
| Fuzzy search | Typo-tolerant |
| Permission-aware | Results filtered by actor's access |
| Cross-object search | Search across all object types |

---

## 9. Existing Model Classification

### 9.1 Classification Schema

| Category | Definition | Action |
|----------|-----------|--------|
| **Canonical** | Already implements or is close to the Universal Object Protocol | Minor adaptations only |
| **Refactor** | Has the right concept but wrong shape | Restructure to match canonical |
| **Merge** | Duplicates functionality with another model | Combine into one canonical model |
| **Split** | Combines multiple concerns in one model | Separate into distinct objects |
| **Legacy** | Functional but uses outdated patterns | Replace with canonical implementation |
| **Remove** | No longer needed; functionality superseded | Delete after migration |
| **Missing** | Concept exists in Business Canon but no model exists | Create new canonical model |

### 9.2 Classification: app/models.py (Core CRM)

| Model | Classification | Rationale | Target |
|-------|---------------|-----------|--------|
| `Lead` | **Refactor** | Travel-specific concept. Should become a domain extension of a universal object (e.g., Relationship + Commitment) | Domain extension of Commitment |
| `Payment` | **Refactor** | Financial concept, but implementation is travel-specific | Universal FinancialObject |
| `Supplier` | **Refactor** | Travel-specific. Domain extension of Organization | Domain extension of Organization |
| `Invoice` | **Refactor** | Financial concept, travel-specific fields | Universal FinancialObject |
| `ItineraryRef` | **Legacy** | Travel-specific reference data. Should be Knowledge records | Knowledge object |
| `TaskList` | **Refactor** | Conceptually a lightweight container. Should be Workspace or Workflow | Workspace/Workflow |
| `Task` | **Canonical** | Core concept maps to universal Task. Needs protocol compliance | Universal Task |
| `Notification` | **Merge** | Should be part of the Event system | Timeline Event |
| `ClientUser` | **Refactor** | Conceptually a Human + Relationship | Human object |
| `ClientMessage` | **Merge** | Should be part of Conversation | Conversation object |
| `Document` | **Canonical** | Core concept maps to universal Document | Universal Document |
| `ActivityLog` | **Merge** | Should be subsumed by Timeline | Timeline |
| `Celebration` | **Remove** | UI-only concept, not a business object | Phase out |
| `Person` | **Refactor** | Should be universal Human object | Universal Human |
| `PersonIdentity` | **Canonical** | Maps to universal Identity concept | Universal Identity |
| `EmployeeProfile` | **Split** | Part Human, part Relationship (employment) | Human attributes + Relationship |
| `CustomerProfile` | **Split** | Part Human, part Relationship (customer) | Human attributes + Relationship |
| `SupplierContactProfile` | **Split** | Part Human, part Relationship (supplier contact) | Human attributes + Relationship |
| `ClientUserProfile` | **Split** | Part Human, part Relationship (client user) | Human attributes + Relationship |
| `Relationship` | **Refactor** | Has the right concept but needs protocol compliance | Universal Relationship |
| `RelationshipEvent` | **Merge** | Should be part of Relationship timeline | Relationship timeline |
| `RelationshipCommitment` | **Merge** | Should be part of Commitment | Universal Commitment |
| `IntakeSession` | **Refactor** | Conceptually a Conversation + Workflow | Conversation + Workflow |
| `IntakeCandidate` | **Refactor** | Conceptually a Human + Decision candidate | Human + Decision |
| `IntakeFieldMapping` | **Legacy** | Implementation detail. Should be domain adapter config | Domain adapter |

### 9.3 Classification: Other Models

| Model (file) | Classification | Rationale |
|-------------|---------------|-----------|
| `MemoryConcept` (memory/models.py) | **Canonical** | Core concept aligns with universal Memory |
| `MemoryRecord` (memory/models.py) | **Canonical** | Core concept aligns with universal Memory |
| `MemoryProvenance` (memory/models.py) | **Canonical** | Core concept, maps to Evidence/Provenance |
| `DocumentRecord` (document/models.py) | **Canonical** | Aligns with universal Document |
| `DocumentSection` (document/models.py) | **Refactor** | Should be sub-object of Document |
| `Decision` (decision_runtime/models.py) | **Canonical** | Core concept aligns with universal Decision |
| `FounderSpace` (founder/models.py) | **Canonical** | Maps to Workspace/Space concept |
| `FounderObject` (founder/models.py) | **Canonical** | Should implement UniversalObject protocol |
| `FounderConversation` (founder/models.py) | **Canonical** | Maps to universal Conversation |
| `GovernedCollection` (gkf/models.py) | **Refactor** | Knowledge governance, maps to Knowledge |
| `Volume`/`Chapter`/`Article` (gkf/models.py) | **Split** | Knowledge hierarchy — separate into Knowledge + Document |
| `OrganizationState` (cortex/state.py) | **Canonical** | Derived aggregate — correct pattern |
| `Observation`/`Insight` (intelligence/) | **Canonical** | Core intelligence objects, maps to Observation + Decision |
| `Space models` (space/models.py) | **Canonical** | Core space architecture, close to canonical |
| `Outcome` (decision_runtime/models.py) | **Canonical** | Maps to universal Outcome |
| `Snapshot`/`Trajectory`/`Trend`/`Forecast` (temporal/) | **Canonical** | Temporal intelligence models are well-structured |
| `Objective`/`Plan`/`Milestone` (planning/) | **Canonical** | Maps to universal Workflow/Decision/Task |

### 9.4 Classification Summary

| Category | Count | Action |
|----------|-------|--------|
| **Canonical** | ~20 | Minor protocol adaptations needed |
| **Refactor** | ~12 | Restructure to match canonical shape |
| **Merge** | ~6 | Combine into canonical model |
| **Split** | ~4 | Separate concerns into distinct objects |
| **Legacy** | ~3 | Replace with canonical implementation |
| **Remove** | ~1 | Phase out |
| **Missing** | ~4 | Create: Workspace, Commitment, Evidence (root) |

### 9.5 Missing Models

The following Business Canon objects (from 03_business_canon.md) have no existing SQLAlchemy model:

| Missing Object | Notable Existing Code | Action |
|---------------|---------------------|--------|
| **Workspace** | Found in `app/space/` as RuntimeSpace | Needs database model |
| **Commitment** | Found in `app/decision_runtime/commitment.py` as in-memory | Needs persistent model |
| **Evidence (root)** | Found in `app/evidence/` | Needs unification with protocol |
| **Knowledge** | Found in `app/gkf/` and `app/knowledge/` | Needs canonical model |

---

## 10. Data Security and Privacy

### 10.1 Data Classification

| Classification | Examples | Storage Requirements | Access Requirements |
|---------------|----------|---------------------|-------------------|
| **Public** | Published documents, public profiles | Standard | No auth required |
| **Internal** | Organization info, non-sensitive | Standard encryption | Org member auth |
| **Sensitive** | Personal contact info, financial | Encryption at rest + transit | Role-based access, audit logging |
| **Confidential** | Private notes, internal decisions | Strong encryption, limited access | Named access only, full audit |
| **Regulated** | PII, financial records, legal | Encryption + compliance controls | Compliance-based, full audit |

### 10.2 Data Retention

| Data Type | Retention | Deletion Policy |
|-----------|-----------|-----------------|
| Object state | Indefinite (versions are immutable) | Right to deletion for personal data |
| Timeline events | Per event type (see §7.2) | Anonymization preferred over deletion |
| Audit log | Permanent | Never deleted |
| Personal data | Per privacy policy | Right to be forgotten |
| Evidence | Indefinite (foundation of truth) | Superseded, never deleted |
| Memory | Per subject preference | Right to be forgotten |

---

## 11. Future Extensibility

### 11.1 New Object Types

A new object type can be added by:
1. Defining it in the Business Canon (03_business_canon.md)
2. Creating a new store schema or extending the object store with a new type
3. Implementing the Universal Object Protocol
4. Adding search indexing
5. Adding to the existing model classification

### 11.2 Storage Backend Migration

The data architecture is backend-agnostic. Migration between backends:
- Object Store: SQL ↔ NoSQL (use abstract repository pattern)
- Event Store: Kafka ↔ EventStoreDB ↔ SQL (use event interface)
- Search: Elasticsearch ↔ Meilisearch ↔ PostgreSQL FTS (use search interface)

---

## 12. Relationship to Other Canonical Documents

| Document | Relationship |
|----------|-------------|
| **00_universal_ontology.md** | Data architecture stores Objects according to their ontological categories — Entity, Identity, Relationship, Event, Evidence — each with distinct storage semantics |
| **02_shunya_constitution.md** | Data classification enforces Constitutional privacy rights |
| **03_business_canon.md** | Data architecture stores all business objects defined here |
| **04_universal_object_protocol.md** | Data schemas derive from protocol requirements |
| **05_runtime_canon.md** | Data stores support all runtime engines |
| **07_ai_canon.md** | AI uses search and timeline data stores |
| **08_experience_canon.md** | Experience layer queries data stores |
| **09_repository_canon.md** | Code organization maps to store boundaries |
| **10_migration_canon.md** | This classification is the migration blueprint |
| **11_engineering_canon.md** | Data standards enforce integrity and privacy |
| **12_launch_roadmap.md** | Data migration is a core milestone |

---

> **Next:** [07_ai_canon.md](07_ai_canon.md)