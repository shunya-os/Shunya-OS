# Universal Ontology v1 — SHUNYA Constitutional Foundation

**Directive:** Z-05 Article I-II
**Purpose:** Smallest complete set of universal concepts capable of expressing every business, team, and personal workspace through contextual intelligence.
**Status:** Design Artefact — No Implementation Required

---

## Ontology Design Principles

1. **Minimality** — Every concept exists because it cannot be expressed as a composition of others.
2. **Composition** — Complexity emerges through relationships between fundamentals, not through new types.
3. **Universality** — No concept is specific to a domain, industry, or business model.
4. **Contextuality** — Meaning is determined by context, not by type hierarchy.
5. **Humans First** — Ontology exists for SHUNYA, not for the founder. Users never see these terms.
6. **Temporal** — Every concept has a lifecycle: emergence, state transitions, archival.
7. **Relational** — The value of any concept is primarily in its connections to others.

---

## The Universal Ontology — 18 Concepts

### 1. Identity
The atomic unit of existence in SHUNYA. Every subject — human, organization, AI agent, system — is an Identity.

```
Properties:
  - id (universal, immutable)
  - type (person, organization, agent, system)
  - name(s) (one or more labels)
  - attributes (extensible key-value)
  - status (active, dormant, archived, merged)

Lifecycle:
  Created → Verified → Active → Dormant → Archived → (Merged)
```

**Covers:** Users, companies, bots, employees, freelancers, family members, departments as identities with type=organization.

### 2. Person
A specialization of Identity where type=person. A human being.

```
Extends: Identity
Properties:
  - legal_name, preferred_name
  - contact_channels (email, phone, whatsapp, etc.)
  - roles (contextual — employee, founder, parent, member)
  - preferences
  - capabilities (skills, permissions, knowledge areas)
```

**Covers:** Founders, employees, customers, suppliers, contacts, team members, family, patients, students, travellers.

### 3. Organization
A specialization of Identity where type=organization. A structured group of persons with shared purpose.

```
Extends: Identity
Properties:
  - industry, business_category, sub_category
  - size (employees, revenue range)
  - metadata (country, timezone, currency, language)
  - structure (departments, teams, divisions — recursive)
```

**Covers:** Companies, non-profits, departments, teams, families, clubs, institutions, agencies.

### 4. Relationship
The foundational connection between two Identities. No entity exists in isolation.

```
Properties:
  - source (Identity A)
  - target (Identity B)
  - type (employment, ownership, membership, service, partnership, family, friendship)
  - direction (directed, undirected)
  - strength (quantitative or qualitative)
  - start_date, end_date (if bounded)
  - context (what the relationship is about)

Lifecycle:
  Formed → Active → Renewed → Ended
```

**Covers:** Employee-of, customer-of, supplier-of, partner-with, parent-of, member-of, owns. Every tag, group, and team is a relationship set.

### 5. Place
A spatial or virtual location where things happen.

```
Properties:
  - address (structured, unstructured)
  - coordinates (lat/lng)
  - type (physical, virtual, hybrid)
  - capabilities (what can happen here)
  - parent (containing place, hierarchical)
```

**Covers:** Offices, venues, cities, countries, meeting rooms, warehouses, stores, virtual spaces, URLs.

### 6. Asset
Something of value owned, controlled, or referenced by an Identity.

```
Properties:
  - type (physical, digital, financial, intellectual)
  - value (monetary, utility)
  - owner (Identity)
  - custodian (Identity — may differ from owner)
  - lifecycle (acquired, deployed, maintained, disposed)
  - metadata (brand, model, identifier, warranty)
```

**Covers:** Products, equipment, inventory, software licenses, IP, brand assets, content, vehicles, real estate.

### 7. Commitment
A binding agreement between Identities to act or deliver.

```
Properties:
  - parties (source Identity, target Identity)
  - type (promise, contract, SLA, agreement, law)
  - terms (structured: what, when, where, how)
  - status (proposed, accepted, active, fulfilled, breached, cancelled)
  - value (monetary or non-monetary)
  - linked_assets (assets the commitment concerns)
  - linked_decisions (decisions that produced this commitment)

Lifecycle:
  Proposed → Negotiated → Accepted → Active → Fulfilled (or Breached or Cancelled)
```

**Covers:** Contracts, invoices, proposals, quotes, SLAs, terms of service, purchase orders, employment agreements, NDAs, promises, tasks, follow-ups, todos.

### 8. Event
Something that happens at a point in time, involving Identities.

```
Properties:
  - timestamp (start, end, or point)
  - participants (Identities involved)
  - type (meeting, call, transaction, delivery, observation, occurrence)
  - associated_commitments, assets, places
  - outcome (what resulted)
  - source (how SHUNYA learned about it — observation, import, user input, API)
```

**Covers:** Meetings, calls, transactions, deliveries, log entries, system events, calendar items, signups, purchases, milestones.

### 9. Communication
An exchange of information between Identities.

```
Properties:
  - channel (email, SMS, WhatsApp, voice, in-app, letter)
  - participants (sender, recipients, CC, BCC)
  - subject, body, attachments
  - thread_id (grouping related communications)
  - direction (outbound, inbound, internal)
  - linked_events, commitments

Lifecycle:
  Draft → Sent → Delivered → Read → Replied → Archived
```

**Covers:** Emails, messages, notifications, broadcasts, campaigns, conversations, comments, notes shared between identities.

### 10. Knowledge
Structured or unstructured information that SHUNYA learns or is taught.

```
Properties:
  - format (document, FAQ, SOP, policy, article, guide)
  - source (uploaded, imported, AI-generated, observed)
  - domain (subject area)
  - embeddings (for semantic retrieval)
  - linked_identities (who contributed, who can access)
  - version, status (draft, reviewed, published, archived)
```

**Covers:** Documents, manuals, knowledge base articles, SOPs, policies, research, notes, references, training materials.

### 11. Financial Record
A representation of monetary movement or position.

```
Properties:
  - type (transaction, balance, budget, valuation)
  - amount, currency
  - counterparty (Identity)
  - linked_commitment (the invoice/order/contract)
  - category (revenue, expense, asset, liability, equity)
  - tax_metadata
  - timestamp

Lifecycle:
  Pending → Settled → Reconciled → Audited
```

**Covers:** Invoices, payments, receipts, expenses, budgets, payroll, taxes, P&L, balance sheet items.

### 12. Document
A persistent record with content, structure, and provenance.

```
Properties:
  - format (pdf, docx, spreadsheet, image, video, plain text)
  - content (text, binary, structured data)
  - version (sequence of revisions)
  - signatures (Identities who approved or authored)
  - classification (public, confidential, restricted)
  - metadata (title, description, tags, category)
  - source (generated, uploaded, imported, linked)

Lifecycle:
  Created → Draft → Reviewed → Approved → Published → Archived → (Deleted)
```

**Covers:** All files, reports, generated PDFs, spreadsheets, images, recordings, legal documents, specifications.

### 13. Workflow
A sequence of steps or states through which something progresses.

```
Properties:
  - states (the nodes: pending → in_progress → review → done)
  - transitions (allowed moves between states)
  - assignees (Identities responsible at each step)
  - triggers (what starts the workflow)
  - linked_commitments, assets, decisions

Lifecycle:
  Defined → Active → Paused → Completed → (Archived)
```

**Covers:** Processes, pipelines, sales funnels, approval chains, project phases, onboarding flows, automation rules.

### 14. Observation
A fact that SHUNYA perceives about the world.

```
Properties:
  - subject (Identity or concept being observed)
  - predicate (what was observed — health, behavior, change, state)
  - value (the observation)
  - source (system, sensor, AI inference, human report)
  - confidence (how certain is this observation)
  - timestamp

Lifecycle:
  Sensed → Validated → Recorded → (Refuted by later observation)
```

**Covers:** System health checks, customer behavior, market signals, usage patterns, anomalies, AI inferences, sensor readings.

### 15. Decision
A choice made by an Identity or AI, recorded with context and rationale.

```
Properties:
  - subject (what the decision is about)
  - options (alternatives considered)
  - outcome (what was chosen)
  - rationale (why)
  - authority (Identity who decided — human, AI, system)
  - linked_observations (what informed this decision)
  - linked_commitments (what commitments resulted)
  - quality_score (ex-post evaluation)

Lifecycle:
  Candidate → Evaluated → Decided → Executed → Measured → (Revised)
```

**Covers:** Approvals, rejections, selections, prioritization, strategic choices, routing decisions, AI recommendations.

### 16. Memory
SHUNYA's persistent understanding built from past events, communications, decisions, and observations.

```
Properties:
  - type (episodic — specific past event, semantic — general knowledge, procedural — how to do things)
  - source_events, communications, decisions
  - significance (importance weighting)
  - last_accessed, access_frequency
  - consolidated (has been distilled into knowledge?)

Lifecycle:
  Formed → Consolidated → Retrieved → (Forgotten — aged out)
```

**Covers:** Customer history, project retrospectives, past preferences, learned patterns, organizational history, relationship memory.

### 17. Capability
Something SHUNYA or an Identity can do.

```
Properties:
  - subject (Identity with the capability)
  - action (what can be done)
  - context (when this capability applies)
  - readiness (available, needs setup, requires upgrade)

Lifecycle:
  Defined → Acquired → Ready → Active → (Deprecated)
```

**Covers:** Skills, permissions, features, AI abilities, integrations, automation triggers.

### 18. Record
The base abstraction. Everything that exists in SHUNYA is a Record with an id, type, and lifecycle. Identity, Commitment, Event, Communication — all are Records.

```
Base Properties:
  - id (universal, immutable)
  - type (the concept class)
  - created_at, updated_at
  - status (active, archived, deleted)
  - owner (Identity)
  - tags (extensible labels)
  - links (relationships to other Records)

Operations:
  Create, Read, Update, Archive, Delete (soft), Search, Relate
```

**Covers:** Every other concept inherits from Record. The base guarantees consistency.

---

## Composition Rules

### A Record MUST have exactly one primary type.
A given record is an Identity or an Event or a Commitment — never both.

### A Record MAY have multiple secondary relationships.
A Commitment (invoice) is linked to an Identity (customer), an Asset (product), Financial Records (payments), Events (delivery), Communications (email thread).

### Records are composed through relationships, not inheritance beyond Identity.
Customer is not a subtype of Identity. It is an Identity with a Relationship "customer-of" pointing to another Identity (the company).

### Capabilities are not objects.
A user does not "have a CRM module." They have capabilities: create_person, link_relationship, record_commitment, track_communication. The workspace is composed from these capabilities.

---

## Ontology Coverage — Current Object Types Mapped

| Current Object | Universal Concept(s) | Notes |
|---------------|---------------------|-------|
| Customer | Identity(Person) + Relationship(customer-of) | The customer IS a person. The relationship to the org is the differentiator. |
| Supplier | Identity(Person or Organization) + Relationship(supplier-of) | Same pattern as customer. |
| Lead | Identity(Person) + Relationship + Commitment(potential) + Workflow(pipeline) | Lead is a temporary framing — a person with intent. |
| Invoice | Commitment + Financial Record | Invoice IS a commitment to pay. The financial record tracks its monetary dimension. |
| Proposal | Commitment (proposed) + Document | Proposal IS a commitment being negotiated. The document is its representation. |
| Task | Commitment (promise to act) + Workflow | A task IS a commitment with a workflow. |
| Employee | Identity(Person) + Relationship(employed-by) | Same as customer pattern. |
| Document | Document | Direct 1:1 mapping. |
| Product | Asset | A product is an asset owned or offered. |
| Contact | Identity(Person) | A contact IS a person. |

**Key insight:** The current 10+ object types collapse to 6 universal concepts (Identity, Relationship, Commitment, Financial Record, Document, Asset) plus two structural ones (Workflow, Person as Identity specialization). This is the power of the universal ontology.

---

## Excluded Concepts (and Why)

| Candidate | Reason for Exclusion |
|-----------|---------------------|
| Activity | Captured by Event. |
| Notification | Captured by Communication with type=notification. |
| Report | Captured by Document with format=report. |
| Dashboard | A View (not a Record) — composed from queries against other Records. |
| Settings | Attributes on Identity or Organization. |
| Tag | A lightweight Relationship (tag-of) without lifecycle. |
| Template | A prototype Document used to create other Documents. |
| Role | A set of Capabilities grouped by a Relationship type. |
| Subscription | A Commitment with recurring terms. |
| Goal | A Commitment (promise to self or org about future state). |
| Invoice Line Item | An Asset (what was sold) + Financial Record (what it costs) within an Invoice commitment. |

---

## Ontology Cardinality

| Concept | Can Exist Without Others? | Typically Created Per |
|---------|--------------------------|----------------------|
| Identity | Yes (root concept) | Per person/organization |
| Person | Yes (specialization) | Per human |
| Organization | Yes (specialization) | Per company/team |
| Relationship | No — requires 2 Identities | Per connection |
| Place | Yes | Per location |
| Asset | Yes (may be unattached) | Per item of value |
| Commitment | Yes (requires at least 1 Identity) | Per agreement |
| Event | Yes | Per occurrence |
| Communication | Yes (requires at least 1 Identity) | Per exchange |
| Knowledge | Yes | Per information unit |
| Financial Record | Yes (may reference Commitment) | Per monetary event |
| Document | Yes | Per file |
| Workflow | Yes | Per process |
| Observation | Yes (requires a subject) | Per perception |
| Decision | Yes (requires authority Identity) | Per choice |
| Memory | No — derived from other Records | Per consolidation |
| Capability | Yes (may reference Identity) | Per ability |
| Record | Abstract base — no standalone instances | N/A |

---

## Validation: Can This Model Everything?

**Yes — because every business domain is a different pattern of the same fundamentals:**

- A **customer** is Person + Relationship(customer-of) + Communications + Events(meetings) + Commitments(orders)
- A **lead** is Person + Relationship(prospect) + Events(website visit) + Communication(email) + Workflow(pipeline)
- A **patient** is Person + Relationship(patient-of) + Events(appointments) + Documents(records) + Knowledge(conditions)
- A **student** is Person + Relationship(student-of) + Events(classes) + Commitments(courses)
- A **traveller** is Person + Events(trips) + Commitments(bookings) + Place(destinations) + Asset(luggage)
- An **employee** is Person + Relationship(employed-by) + Commitments(salary) + Capabilities(skills) + Workflow(onboarding)
- A **project** is Commitment(deliverable) + Events(milestones) + Persons(team) + Documents(plans) + Financial Records(budget)
- A **deal** is Commitment(proposed) + Persons(stakeholders) + Relationships + Events(meetings) + Workflow(pipeline)
- A **family** is Organization(family) + Relationships(parent-child, spouse) + Events + Place(home) + Assets + Commitments

Every real-world entity is a cluster of universal Records connected by Relationships. No new object types needed.

---

## What Changes in SHUNYA

1. **Storage:** All records use the same table (founder_objects) with a `universal_type` column.
2. **API:** `POST /api/v1/records` with `type`, `properties`, `links[]`
3. **AI:** The Language Layer maps user phrases to universal types + relationships
4. **Workspace:** Generated dynamically from capability composition, not from hardcoded panels
5. **Onboarding:** "How would you like to use SHUNYA?" → domain chosen → ontology subset activated
6. **Import:** External data maps to universal types via AI transformation layer

---

*This ontology replaces the current CRM-oriented object model. No new object types shall be added. All future domain expansion happens through ontology composition, not new type creation.*