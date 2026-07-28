# Governed Knowledge Framework — Specification GKF-000

**Program:** Governed Knowledge Framework
**Classification:** Constitutional Architecture — Representation Specification
**Status:** PROPOSED
**Version:** 1.0

---

## Preamble

### Authority

This document defines the Governed Knowledge Framework (GKF). It is authorized by Founder directive. It defines a universal representation for governed knowledge collections — the canonical form of structured, versioned, principled knowledge that governs system behavior.

### Founding principle

Markdown is not canonical. The canonical representation of governed knowledge is structured knowledge stored inside SHUNYA's universal knowledge architecture. Markdown, HTML, PDF — all are generated views of the canonical structured form.

### What is a Governed Collection

A Governed Collection is any body of knowledge that:
- Governs behaviour (constitutional, regulatory, policy, contractual)
- Has versions and amendments (immutable history)
- Contains principles that are referenced by implementation
- Requires traceable evidence of origin
- Must be queryable at runtime

GKF-000 defines the representation. It does not define runtime enforcement, compliance checking, or policy execution — those are future programs.

### First governed collection

The SHUNYA Constitution is the first Governed Collection. The framework must support future collections (regulatory frameworks, organizational policies, contractual agreements) without modification.

---

## 1. Framework Scope

### 1.1 What GKF-000 defines

The representation of governed knowledge:
- The structural hierarchy of a Governed Collection
- The identity scheme for every structural element
- The node types, edge types, and evidence types
- The relationship rules between elements

### 1.2 What GKF-000 does NOT define

- Runtime compliance checking
- Invariant enforcement
- Policy execution
- Governance engine
- Query interface beyond structural retrieval
- Any mechanism that evaluates or enforces governed knowledge

GKF-000 is pure representation. Nothing more.

### 1.3 What the framework must support

The framework must represent any Governed Collection, not just the SHUNYA Constitution. Future collections may include:
- Regulatory compliance frameworks (GDPR, HIPAA, SOC2)
- Organizational policy collections
- Contractual agreement frameworks
- Industry standard frameworks
- Custom enterprise governance collections

All must be representable without modifying GKF-000.

---

## 2. Structural Hierarchy

### 2.1 Dual hierarchy

The framework defines two independent hierarchies:

**Structural hierarchy** — describes document organization:
```
Governed Collection
  └── Volume
       └── Chapter
            └── Article
```

**Semantic hierarchy** — describes governing meaning:
```
Principle ──── Interpretation
    │
    └─────── Implementation Link
```

The hierarchies are independently extensible:
- A new structural level (e.g., Part, Section) can be added without changing semantic types.
- A new semantic type (e.g., Exception, Guideline) can be added without changing structural types.
- Structural and semantic elements connect via edges (contains, expressed_in), not inheritance.

Evidence, Reference, Amendment, and Version span both hierarchies.

| Element | Hierarchy | Purpose |
|---------|-----------|---------|
| Governed Collection | Structural | Root container |
| Volume | Structural | Major division |
| Chapter | Structural | Sub-division |
| Article | Structural | Document container |
| Principle | **Semantic** | Governing meaning |
| Interpretation | **Semantic** | Authoritative clarification |
| Implementation Link | **Semantic** | Code reference |
| Reference | Both | Cross-link between any elements |
| Evidence | Both | Source evidence for any element |
| Amendment | Both | Change record for any element |
| Version | Both | Immutable snapshot of any element |

### 2.2 Principles as governing objects

Principles are the primary semantic objects in the framework. Implementation, reasoning, and future governance shall reference Principles rather than Articles whenever possible.

Articles are document containers — they organize principles into a readable structure. A single Article may contain multiple Principles. A single Principle belongs to exactly one Article.

Principles are what the rest of the system references. When a runtime module asks "does this violate the Constitution?", the answer traces to Principles, not Articles.

### 2.3 Articles as document containers

Articles exist for human readability and document structure. They are numbered, titled, and contain body text. Their primary purpose is to organize Principles into the documented form that humans read.

An Article's body text is the written expression of the Principles it contains. When the body and the Principles conflict, the Principle governs.

---

## 3. Element Definitions

### 3.1 GovernedCollection

The root container for a complete body of governed knowledge.

| Property | Type | Description |
|----------|------|-------------|
| `collection_id` | str | Permanent, unique identity |
| `name` | str | Short name (e.g., "SHUNYA Constitution") |
| `description` | str | Brief description of purpose |
| `jurisdiction` | str | Domain of authority (e.g., "SHUNYA OS") |
| `established` | str | ISO 8601 date of establishment |
| `status` | str | `active`, `superseded`, `draft` |

**Identity:** `gkc_<name>` (e.g., `gkc_shunya_constitution`)

**Rules:**
- Every GovernedCollection must have at least one Volume.
- A GovernedCollection's identity is permanent and never reused.
- Amendments to a collection create new Versions of affected elements, never modifications.

### 3.2 Volume

A major division within a Governed Collection.

| Property | Type | Description |
|----------|------|-------------|
| `volume_id` | str | Permanent identity within collection |
| `number` | int | Ordinal position within collection |
| `title` | str | Short title |
| `description` | str | Purpose of this volume |

**Identity:** `<collection_id>:vol_<number>` (e.g., `gkc_shunya_constitution:vol_1`)

### 3.3 Chapter

A sub-division within a Volume.

| Property | Type | Description |
|----------|------|-------------|
| `chapter_id` | str | Permanent identity within volume |
| `number` | int | Ordinal position within volume |
| `title` | str | Short title |

**Identity:** `<volume_id>:ch_<number>` (e.g., `gkc_shunya_constitution:vol_1:ch_1`)

### 3.4 Article

A numbered document container that organizes principles for human readability.

| Property | Type | Description |
|----------|------|-------------|
| `article_id` | str | Permanent identity |
| `number` | int | Article number |
| `title` | str | Short title |
| `body` | str | Document body text |
| `status` | str | `ratified`, `amended`, `superseded` |
| `version` | int | Amendment version (starts at 1) |

**Identity:** `<collection_id>:art_<number>` (e.g., `gkc_shunya_constitution:art_1`)

**Rules:**
- An Article contains one or more Principles.
- The Article body expresses the Principles for human reading.
- If the body and a Principle conflict, the Principle governs.

### 3.5 Principle

The primary governing semantic object. Principles are what implementation, reasoning, and governance reference.

| Property | Type | Description |
|----------|------|-------------|
| `principle_id` | str | Permanent identity |
| `name` | str | Short, referenceable name |
| `statement` | str | The governing principle statement |
| `category` | str | Semantic category (collection-specific) |
| `priority` | int | Relative priority (lower = higher) |
| `status` | str | `active`, `superseded`, `pending` |

**Identity:** `<collection_id>:pr_<name>` (e.g., `gkc_shunya_constitution:pr_human_first`)

This identity is **stable** — it does NOT encode the principle's position in the document hierarchy. A principle's identity never changes, even if it moves to a different Article, Chapter, or Volume. The name component is a short, human-readable slug that is unique within the collection.

**Rules:**
- Principle identity is permanent and location-independent.
- Principle identity does NOT include article number, chapter, or volume.
- A Principle's canonical identity is the semantic identifier for all external references.
- Implementation, reasoning, and governance reference Principles by `principle_id`, never by document location.

### 3.6 Interpretation

An authoritative explanation or clarification of a Principle.

| Property | Type | Description |
|----------|------|-------------|
| `interpretation_id` | str | Permanent identity |
| `statement` | str | The interpretation text |
| `authority` | str | Who issued the interpretation |
| `established` | str | ISO 8601 date |

**Identity:** `<principle_id>:int_<number>` (e.g., `gkc_shunya_constitution:pr_human_first:int_1`)

### 3.7 Reference

A cross-reference from one governed element to another.

| Property | Type | Description |
|----------|------|-------------|
| `reference_id` | str | Permanent identity |
| `source_id` | str | The element making the reference |
| `target_id` | str | The element being referenced |
| `relationship` | str | Nature of reference (e.g., `depends_on`, `supports`, `contradicts`, `amplifies`) |

**Identity:** `<source_id>:ref_<target_id>`

### 3.8 Evidence

Source evidence that establishes a Principle or Article.

| Property | Type | Description |
|----------|------|-------------|
| `evidence_id` | str | Permanent identity |
| `source_type` | str | Category of evidence source |
| `source_path` | str | Path or identifier of the source |
| `title` | str | Title of the evidence |
| `authority` | str | Who issued the evidence |
| `established` | str | ISO 8601 date |
| `body` | str | The evidence text or excerpt |

**Identity:** `<collection_id>:ev_<source_type>_<id>`

**Evidence source types (collection-specific):**
- `founder_directive` — A directive from the Founder
- `constitutional_document` — A constitutional document or specification
- `adr` — An Architectural Decision Record
- `statute` — A legal or regulatory statute
- `policy` — An organizational policy
- `contract` — A contractual agreement

### 3.9 ImplementationLink

A link from a Principle to the code that implements or enforces it.

| Property | Type | Description |
|----------|------|-------------|
| `link_id` | str | Permanent identity |
| `principle_id` | str | The principle being implemented |
| `module_path` | str | Path to the implementing module |
| `code_reference` | str | Specific code location (file, class, function) |
| `status` | str | `implemented`, `partial`, `planned`, `not_applicable` |

**Identity:** `<principle_id>:impl_<module_path>`

**Rules:**
- Implementation Links are reference-only. They do NOT imply enforcement.
- Multiple Implementation Links may point to the same Principle.
- A Principle may have zero Implementation Links (deferred implementation).

### 3.10 Amendment

A record of a change to any governed element.

| Property | Type | Description |
|----------|------|-------------|
| `amendment_id` | str | Permanent identity |
| `target_id` | str | The element being amended |
| `type` | str | `addition`, `modification`, `supersession`, `repeal` |
| `reason` | str | Why the amendment was made |
| `authority` | str | Who authorized the amendment |
| `established` | str | ISO 8601 date |

**Identity:** `<target_id>:amd_<number>`

### 3.11 Version

An immutable snapshot of any governed element at a point in time.

| Property | Type | Description |
|----------|------|-------------|
| `version_id` | str | Permanent identity |
| `element_id` | str | The element this version snapshots |
| `number` | int | Version number (starts at 1) |
| `content` | dict | Frozen snapshot of the element's properties at version time |
| `established` | str | ISO 8601 timestamp |

**Identity:** `<element_id>:v<number>` (e.g., `gkc_shunya_constitution:art_1:v1`)

**Rules:**
- Every element has at least one Version (v1).
- Versions are immutable once created.
- The latest Version represents the current state of the element.
- Old Versions are preserved forever — nothing is ever deleted.

---

## 4. Node Types

### 4.1 GKF node types

Every structural element in the hierarchy is a Node in the universal knowledge graph. The canonical node types for the framework:

| Node Type | Element | Description |
|-----------|---------|-------------|
| `GOVERNED_COLLECTION` | GovernedCollection | Root of a governed knowledge body |
| `VOLUME` | Volume | Major division |
| `CHAPTER` | Chapter | Sub-division |
| `ARTICLE` | Article | Document container for principles |
| `PRINCIPLE` | Principle | Primary governing semantic object |
| `INTERPRETATION` | Interpretation | Authoritative clarification |
| `GKF_REFERENCE` | Reference | Cross-reference between elements |
| `GKF_EVIDENCE` | Evidence | Source evidence |
| `IMPLEMENTATION_LINK` | ImplementationLink | Link from principle to code |
| `AMENDMENT` | Amendment | Record of change |
| `GKF_VERSION` | Version | Immutable snapshot |

### 4.2 Edge types

| Edge Type | Source | Target | Description |
|-----------|--------|--------|-------------|
| `contains` | GovernedCollection | Volume | Volume belongs to collection |
| `contains` | Volume | Chapter | Chapter belongs to volume |
| `contains` | Chapter | Article | Article belongs to chapter |
| `contains` | Article | Principle | Principle belongs to article |
| `clarifies` | Principle | Interpretation | Interpretation clarifies principle |
| `cross_references` | Any | Any | Reference between elements |
| `established_by` | Any | GKF_EVIDENCE | Element established by evidence |
| `is_implemented_by` | Principle | ImplementationLink | Principle has implementation |
| `amended_by` | Any | Amendment | Element amended by amendment |
| `has_version` | Any | GKF_VERSION | Element has version snapshot |

### 4.3 Generic naming

All node and edge type names are framework-generic. The prefix `GKF_` distinguishes framework types from domain-specific types. This allows the framework to represent any governed collection without name conflicts.

---

## 5. Evidence Model

### 5.1 Every element must have evidence

Every governed element — from a Governed Collection down to a single Principle — must be established by at least one piece of Evidence. This is the constitutional invariant of GKF-000:

**No element exists without evidence of origin.**

### 5.2 Evidence chain

Evidence forms an append-only chain:
1. Evidence is created from a source (founder directive, document, ADR).
2. An element references Evidence to establish its authority.
3. Amendments create new Evidence that supersedes old Evidence.
4. Old Evidence is preserved — nothing is ever deleted.

### 5.3 Source types

Evidence source types are collection-specific. GKF-000 does not constrain them. Examples from the SHUNYA Constitution collection:
- `founder_directive` — Authorized by the Founder
- `constitutional_document` — From a constitutional document
- `adr` — From an Architectural Decision Record

---

## 6. Canonical Source of Truth

### 6.1 Structured knowledge is canonical

The canonical representation of governed knowledge is structured nodes and edges in the universal knowledge graph. Markdown files, HTML pages, and PDF documents are all generated views of the canonical structured form.

### 6.2 Generation from canonical form

Any representation of governed knowledge must be generated from the canonical graph representation, not the other way around:

```
Canonical (graph nodes + edges)
     │
     ├──→ Markdown (human-readable view)
     ├──→ HTML (web view)
     ├──→ PDF (printable view)
     └──→ API (machine-readable view)
```

### 6.3 Import path

Initial ingestion of existing governed documents creates nodes and edges from the document content. Once created, the canonical representation is the nodes and edges. The original document becomes one of potentially many generated views.

```
Existing document (Markdown)
     │
     v
Structured knowledge (nodes + edges) ← CANONICAL
     │
     ├──→ Markdown (regenerated view)
     ├──→ HTML (generated view)
     └──→ (future views)
```

---

## 7. Identity Scheme

### 7.1 Identity format

All GKF identities follow a hierarchical scheme:

```
<collection_id>:[<volume_id>:[<chapter_id>:]]<element_type>_<local_id>
```

| Component | Example |
|-----------|---------|
| Collection | `gkc_shunya_constitution` |
| Volume | `vol_1` |
| Chapter | `ch_1` |
| Article | `art_1` |
| Principle | `pr_human_first` |

**Full identity examples:**
- `gkc_shunya_constitution:vol_1` — Volume 1
- `gkc_shunya_constitution:art_1` — Article 1
- `gkc_shunya_constitution:pr_human_first` — Human First principle
- `gkc_shunya_constitution:ev_constitution` — Constitution evidence
- `gkc_shunya_constitution:art_1:v1` — Article 1 version 1
- `gkc_shunya_constitution:pr_human_first:int_1` — Interpretation 1 of Human First

### 7.2 Identity rules

1. Every element has exactly one identity. That identity never changes.
2. Identity is permanent — even after an element is superseded, its identity remains.
3. Identity is unique within its namespace — no two elements may share an identity.
4. Identity is not a database key — it is a semantic concept.

---

## 8. Version Model

### 8.1 Immutable snapshots

Every governed element has an immutable version history:
- Version 1 is created when the element is first established.
- Versions 2+ are created by Amendments.
- Old versions are preserved forever.
- The latest version represents the current state.

### 8.2 Version graph

```
Element (identity permanent)
  ├── Version 1 (established at T1)
  ├── Version 2 (amended at T2) ── Amendment 1
  └── Version 3 (amended at T3) ── Amendment 2
```

### 8.3 Amendment types

| Type | Effect on element |
|------|-------------------|
| `addition` | New content added (body grows, principles added) |
| `modification` | Existing content changed (body edited) |
| `supersession` | Element replaced by another (old element archived) |
| `repeal` | Element removed (never to be reinstated) |

---

## 9. Module Architecture

### 9.1 Module layout

```
app/gkf/
  __init__.py       — Package exports
  enums.py          — GKFNodeType, GKFEdgeType, AmendmentType
  models.py         — All governed element data models
  identity.py       — Identity generation and validation
```

### 9.2 Dependency graph

```
app/gkf/
  depends on:
    app.kernel          — Type system, identity, Object contract
    app.graph           — NodeStore, EdgeStore
    app.evidence        — Evidence, EvidenceStore, provenance

  does NOT depend on:
    Any production module
    Any business logic
    Any external library
    Any runtime enforcement
    Any compliance checking
```

### 9.3 Naming

The module is `app.gkf` (not `app.constitution` or `app.governance`). This is framework-generic. The SHUNYA Constitution is a collection within GKF, not a separate module.

---

## 10. Extension Points

### 10.1 Adding a new Governed Collection

To add a new governed collection:
1. Create a GovernedCollection node with the collection's identity.
2. Create Volume, Chapter, Article, and Principle nodes for its content.
3. Create Evidence nodes for its sources.
4. Create Version nodes for all created elements.
5. Link everything with the appropriate edges.

No GKF-000 changes needed.

### 10.2 Adding collection-specific categories

Principle categories are collection-specific. GKF-000 provides the category field as a free-form string. Each collection defines its own categories.

### 10.3 Adding evidence source types

Evidence source types are collection-specific. GKF-000 provides the source_type field as a free-form string.

### 10.4 Adding reference relationship types

Cross-reference relationship types are collection-specific. The Reference element's relationship field is a free-form string.

---

## 11. Verification

### 11.1 GKF-000 verification

1. Every element defined in GKF-000 is representable as a Node in the universal graph.
2. Every element identity follows the GKF identity scheme.
3. Every element has at least one Evidence reference.
4. Every element has at least one Version.
5. All node and edge type names are framework-generic.

### 11.2 SHUNYA Constitution verification (first collection)

1. All 10 articles of the Constitution are represented as Article nodes.
2. All constitutional principles are represented as Principle nodes.
3. Every Article contains at least one Principle.
4. Every Principle has at least one Evidence reference (the Constitution document).
5. Every Principle has a Version 1 snapshot.

---

## 12. Implementation Plan

### 12.1 Phase 1: Architecture (GKF-000)

- Define the GKF schema, types, and element definitions
- ❌ No code

### 12.2 Phase 2: Core Module

- Implement `app/gkf/__init__.py`
- Implement `app/gkf/enums.py` — GKFNodeType, GKFEdgeType, AmendmentType
- Implement `app/gkf/models.py` — All 11 element data models
- Implement `app/gkf/identity.py` — Identity generation and validation
- Tests: 60+ tests

### 12.3 Phase 3: Collection Ingestion

- Seed the SHUNYA Constitution as the first governed collection
- Create all constitutional nodes and edges
- Tests: 30+ tests

### 12.4 Phase 4: Framework Validation

- Verify GKF-000 can represent a second governed collection without modification
- Tests: 10+ framework validation tests

---

*Established 2026-07-23. Authorized by Founder directive.*