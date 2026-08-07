# SHUNYA Universal Behavior Constitution

**Directive:** Z-06
**Classification:** Constitutional
**Priority:** CRITICAL — Blocks Genesis Reset
**Status:** Ratified — Active

---

## Preamble

Z-05 defined what exists — the Universal Ontology of 18 concepts.

Z-06 defines how everything behaves.

No object, capability, workspace, AI, runtime, or future feature may invent its own behaviour.

All behaviour shall emerge from this constitution.

---

## Article I — Universal Object Behaviour

Every ontology object SHALL inherit one identical behavioural contract.

Regardless of whether the object is a Person, Commitment, Asset, Event, Document, Financial Record, Knowledge, Observation, Decision, Memory, Place, Capability, Workflow, Communication, or any future universal object, the behavioural engine remains identical.

### The Constitutional Contract

Every object therefore supports:

| Behaviour | Description |
|-----------|-------------|
| **Creation** | Objects are created with a type, owner, and initial state. Creation emits an event. |
| **Discovery** | Objects are findable by identity, relationship, search, or observation. |
| **Ownership** | Objects know their owner, creator, modifier, viewers, executors, and delegated authorities. |
| **Relationships** | Objects participate in a graph of connections. No hardcoded relationship chains. |
| **History** | Objects preserve every previous value, relationship change, and version. |
| **Search** | Objects are searchable by meaning — not by module or table. |
| **Observation** | Objects expose health, activity, risk, confidence, dependencies, AI insights, and suggested actions. |
| **Permissions** | Access is graph-based, not folder-based. Permissions traverse relationships. |
| **Versioning** | Every mutation creates a version. Objects are reconstructable to any prior state. |
| **Timeline** | Every object owns its timeline — all events belong to the object's timeline. |
| **Execution** | Objects perform work. Execution is attached to the object, not external workflows. |
| **AI Understanding** | AI observes, understands, predicts, suggests, summarizes, plans, generates, explains — but never owns business logic. |
| **Audit** | Every mutation is audited with identity, timestamp, previous value, and reason. |
| **Deletion Policy** | Objects are never truly deleted. They progress through: active → archived → recoverable → (eventually) purged. |
| **Recovery** | Deleted or corrupted objects are recoverable within the retention window. |

**No exceptions.** No object type may omit or override these behaviours.

---

## Article II — Universal Lifecycle

Every object SHALL expose the identical lifecycle.

### Standard States

```
                     ┌─────────────┐
                     │   Created   │
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │ Identified  │  ← AI or user assigns meaning/type
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │ Understood  │  ← AI analyzes, extracts entities, links knowledge
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │   Related   │  ← Relationships established
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │   Active    │  ← Object is in use
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │  Observed   │  ← System monitors object
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │   Updated   │  ← Mutations occur
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │  Executed   │  ← Object performs its work
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │  Completed  │  ← Object's primary purpose fulfilled
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │  Archived   │  ← Preserved but inactive
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │ Recoverable │  ← Restorable if needed
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │   Deleted   │  ← Soft-deleted, eventually purged
                     └─────────────┘
```

### Transition Rules

| Transition | Trigger | AI Role |
|------------|---------|---------|
| Created → Identified | AI classification or user assignment | Required: determines object type, domain |
| Identified → Understood | AI analysis completes | Required: extracts entities, links knowledge |
| Understood → Related | Relationships are established | Suggested: AI proposes relevant relationships |
| Related → Active | Object enters productive use | Observes |
| Active → Observed | System monitoring begins | Continuous: health, risk, confidence |
| Observed → Updated | Mutation occurs | May suggest updates |
| Updated → Executed | Action taken on object | May execute if automated |
| Executed → Completed | Primary purpose achieved | Verifies completion |
| Completed → Archived | Retention timer or manual action | May suggest archival |
| Archived → Recoverable | Deletion requested | Validates recovery context |
| Recoverable → Deleted | Retention period expires | May flag for purge review |

### Extension Rules

Business-specific states MAY extend the lifecycle by adding sub-states.

They MUST NOT replace the standard states.

*Example: A Proposal may have "Negotiating" as a sub-state of Active.  
The standard lifecycle remains unchanged — Active still means "in use."*

### State Machine Contract

```
type LifecycleState = 
  | "created" | "identified" | "understood" | "related" 
  | "active" | "observed" | "updated" | "executed" 
  | "completed" | "archived" | "recoverable" | "deleted"

interface LifecycleTransition {
  from: LifecycleState
  to: LifecycleState
  triggered_by: Identity | AI | System
  timestamp: DateTime
  reason: string
  metadata: Record<string, any>
}

Every object exposes:
  lifecycle.current_state: LifecycleState
  lifecycle.history: LifecycleTransition[]
  lifecycle.transition(to: LifecycleState, reason: string): void
```

---

## Article III — Universal Relationships

Every object SHALL support graph-based relationships.

### Prohibited: Hardcoded Chains

```
❌ customer.proposals[0].invoice.payment  — hardcoded path traversal
❌ Lead has relationship to Quote only
❌ Invoice belongs_to Customer only
```

### Required: Graph-Based

```
✅ object.relationships(type) → Relationship[]
✅ object.linked(type, direction) → Record[]
✅ graph.query(start, end, max_depth) → path[]
✅ graph.traverse(id, type, direction, depth) → Record[]
```

### Relationship Contract

```
interface Relationship {
  id: string
  source_id: string      // the "from" object
  target_id: string      // the "to" object
  type: string           // relationship type (owns, produces, receives, contains, etc.)
  direction: "directed" | "undirected"
  strength: number       // 0.0 to 1.0
  metadata: Record<string, any>
  created_at: DateTime
  updated_at: DateTime
  created_by: Identity
}
```

### Universal Relationship Types

| Type | Description | Direction |
|------|-------------|-----------|
| `owns` | Ownership (creator/owner) | Directed (owner → owned) |
| `belongs_to` | Inverse of owns | Directed (owned → owner) |
| `produces` | Output/result | Directed (producer → output) |
| `produced_by` | Inverse of produces | Directed |
| `receives` | Target of delivery | Directed |
| `contains` | Composition (container → contained) | Directed |
| `part_of` | Inverse of contains | Directed |
| `references` | Mentions/cites | Directed |
| `follows` | Temporal or logical succession | Directed |
| `precedes` | Inverse of follows | Directed |
| `delegates_to` | Authority delegation | Directed |
| `delegated_by` | Inverse | Directed |
| `assigned_to` | Responsibility assignment | Directed |
| `associated_with` | Undirected connection | Undirected |
| `observes` | Monitoring relationship | Directed |
| `requires` | Dependency | Directed |
| `depended_by` | Inverse dependency | Directed |
| `communicates_with` | Communication channel | Undirected |
| `acted_on` | Execution target | Directed |
| `resulted_in` | Outcome/result | Directed |

### Composition Rule

Customer and Proposal are not linked by a custom field `customer_id` on the Proposal table.

They are linked by a Relationship record: `{source: customer_id, target: proposal_id, type: "owns", direction: "directed"}`.

This makes the graph queryable in any direction without hardcoded joins.

---

## Article IV — Universal Events

Every object emits immutable events.

### Minimum Event Contract

```
type EventType =
  | "created" | "viewed" | "edited" | "commented" | "shared"
  | "assigned" | "mentioned" | "moved" | "approved" | "rejected"
  | "executed" | "completed" | "archived" | "deleted"
```

### Event Structure

```
interface Event {
  id: string
  object_id: string
  type: EventType | string  // may be extended with domain-specific events
  actor: Identity
  timestamp: DateTime
  data: Record<string, any>    // the payload
  previous_state?: Record<string, any>  // snapshot before, for audit
  metadata: {
    source: "user" | "ai" | "system" | "integration"
    correlation_id?: string     // for linking related events
    session_id?: string
    client?: string             // browser, api, webhook, etc.
  }
}
```

### Event Properties

| Property | Rule |
|----------|------|
| **Immutability** | Events are append-only. Once committed, never modified. |
| **Ordering** | Events are strictly ordered per object (sequence number). |
| **Timeliness** | Events are timestamped at source time, not server receipt time. |
| **Completeness** | Every event carries enough context to reconstruct what happened without external queries. |
| **Chainability** | Events carry a `correlation_id` to link causally related events across objects. |

### Memory Formation

Events are immutable → Events become Memory → Memory becomes Intelligence.

```
Events → consolidate() → Memory (patterns, significance, frequency)
Memory → analyze() → Knowledge (general truths, preferences, heuristics)
Knowledge → reason() → Intelligence (predictions, suggestions, decisions)
```

---

## Article V — Universal Timeline

Every object owns its own timeline.

### Timelines Are the Storage Primitive

Nothing is stored outside timelines.

```
interface Timeline {
  object_id: string
  events: Event[]
  observations: Observation[]
  communications: Communication[]  // emails, messages, calls about this object
  mutations: Version[]             // every state change
  ai_insights: AIInsight[]         // AI observations about this object
  human_activity: Activity[]       // what humans did with this object
  external_integrations: IntegrationEvent[]  // webhooks, API calls
}
```

### What Belongs on the Timeline

| Type | Source |
|------|--------|
| AI observations | AI engine |
| Human activity | User interactions |
| External integrations | Webhook, email, WhatsApp, calendar, payments, location |
| Files | Uploads, generated documents |
| Emails | Sent/received about this object |
| WhatsApp messages | Sent/received about this object |
| Calendar events | Meetings, appointments |
| Phone calls | Call logs |
| Payments | Financial transactions |
| Generated proposals | Proposal commits |
| Approvals | Decision events |
| Executions | Workflow completions |
| Location | Place check-ins |

### Timeline Operations

```
interface TimelineOperations {
  append(event: Event): void
  query(filters: TimelineFilter): Event[]
  replay(from: DateTime, to: DateTime): Event[]  // reconstruct state at any point
  branch(at: DateTime): Timeline  // for "what-if" analysis
  merge(timeline: Timeline): void  // combine related timelines
}
```

---

## Article VI — Universal Ownership

Every object must know:

| Dimension | Determined By |
|-----------|---------------|
| Who owns it | Owner Identity (create_identity relationship) |
| Who created it | Created_by field on Record base |
| Who modified it | Each version records modifier identity |
| Who may view it | Graph-based permissions: viewer if within N relationship hops |
| Who may execute it | Execution permissions: owner, delegated, or role-based |
| Who inherited access | Relationship traversal: if A owns B and B relates to C, A may access C |
| Who delegated authority | Delegation relationship: A delegates_to B for object scope |

### Permission Model

Permissions are graph-based. Not folder-based.

```
Permission = traverse(identity, target, max_hops=3)
```

Access is granted if the identity is within N relationship hops of the target object.

*Example: If Alice created Org → Org owns Project → Project contains Task, then Alice automatically accesses the Task without explicit permission.*

### Delegation

```
interface Delegation {
  delegator: Identity
  delegate: Identity
  scope: "all" | "type[]" | "object[]"
  permissions: ("view" | "execute" | "admin")[]
  expires_at?: DateTime
  reason: string
}
```

---

## Article VII — Universal Search

Everything shall be searchable.

### Constitutional Rules

1. **Search is by meaning, not by module.**
   - "Proposal customer accepted yesterday" — searches across Commitments + Persons + Events
   - "Payment received from Amit" — searches across Financial Records + Persons + Communications
   - "Hotel booked for Goa" — searches across Commitments + Places + Events
   - "Marketing campaign last month" — searches across Commitments + Assets + Events
   - "Conversation about pricing" — searches across Communications + Knowledge

2. **One search engine. Entire OS.**
   - No per-module search configurations
   - No per-type search settings
   - Semantic search (embedding-based) for meaning
   - Full-text search for exact matches
   - Relationship-aware ranking

3. **Search results include context.**
   - Each result shows: object type, name, summary, relevance, related objects
   - AI can explain why a result matched

### Search Contract

```
interface SearchQuery {
  text: string
  types?: ("identity" | "commitment" | "event" | "document" | ...)[]
  filters?: Record<string, any>
  sort?: "relevance" | "date" | "type"
  limit: number
  include_context: boolean  // include related objects
}

interface SearchResult {
  object: Record
  type: string
  relevance: number
  summary: string           // AI-generated
  context: {                // related objects
    relationships: Relationship[]
    recent_events: Event[]
    key_communications: Communication[]
  }
  matched_by: "semantic" | "fulltext" | "relationship"
}
```

---

## Article VIII — Universal Observation

Everything is observable.

### Observation Contract

Every object exposes:

| Observable | Description |
|------------|-------------|
| **Health** | Is the object in a valid state? Are all required relationships present? |
| **Activity** | How frequently is this object interacted with? When was last mutation? |
| **Risk** | Is the object overdue, abandoned, unusual, or failing? |
| **Confidence** | How confident is AI about its understanding of this object? |
| **Dependencies** | What other objects does this depend on? Are any blocked? |
| **AI Insights** | What has AI observed about this object recently? |
| **Suggested Actions** | What should be done with this object next? |

### Observation Engine

```
interface Observation {
  subject_id: string      // the object being observed
  predicate: string       // what was observed (health, activity, risk, etc.)
  value: any              // the observation value
  confidence: number      // 0.0 to 1.0
  source: "ai" | "system" | "human"
  timestamp: DateTime
  expires_at?: DateTime   // when this observation becomes stale
}
```

### AI Observation Types

| Observation | Example |
|-------------|---------|
| Health | "This Proposal has been in 'draft' for 30 days — may be abandoned." |
| Activity | "This Customer has not been contacted in 14 days." |
| Risk | "Invoice INV-003 is 30 days overdue — escalate." |
| Confidence | "85% confident this Document is a contract for the Smith engagement." |
| Dependencies | "This Task depends on Approval from Alice — Alice is on leave." |
| Pattern | "This Customer always pays net-30. Current invoice is net-60 — anomaly." |

---

## Article IX — Universal Execution

Objects do not merely store information. They perform work.

### Execution Model

Execution is attached to the object, not external workflows.

```
Example: Proposal

Proposal.execution_plan = [
  { action: "approve", by: Identity, condition: "amount < $50k" },
  { action: "send", channel: "email", template: "proposal_email" },
  { action: "negotiate", AI_assist: true, max_rounds: 3 },
  { action: "accept", condition: "signature_received" },
  { action: "invoice", creates: Commitment(type: invoice, from: proposal) },
  { action: "collect_payment", gateway: "stripe", auto: true },
  { action: "strengthen_relationship", notify: Identity(owner), message: "Proposal accepted by {customer}" }
]
```

### Execution Contract

```
interface ExecutionPlan {
  object_id: string
  steps: ExecutionStep[]
  status: "pending" | "running" | "paused" | "completed" | "failed"
}

interface ExecutionStep {
  action: string
  conditions?: Condition[]
  creates?: string[]     // object types this step creates
  requires?: string[]    // capabilities needed
  AI_assist?: boolean    // AI helps but doesn't decide
  auto?: boolean         // fully automated
  notify_on_complete?: Identity[]
}
```

### Execution Rules

| Rule | Description |
|------|-------------|
| **Deterministic** | Given the same object state, execution produces the same result. |
| **Observable** | Every execution step emits an Event. |
| **Recoverable** | Failed executions are retried or rolled back. |
| **Auditable** | Every execution decision is recorded with rationale. |
| **AI role** | AI may assist, suggest, predict — but never make final execution decisions unless explicitly authorized. |

---

## Article X — Universal Intelligence

AI never owns business logic.

### AI Contributions

| Contribution | Description | Always Allowed? |
|-------------|-------------|-----------------|
| **Understanding** | Classify, extract entities, determine intent | ✅ Always |
| **Prediction** | Forecast outcomes, estimate probabilities | ✅ Always |
| **Suggestions** | Recommend next actions, propose relationships | ✅ Always |
| **Summaries** | Condense timelines, histories, documents | ✅ Always |
| **Planning** | Generate execution plans for human approval | ✅ With human review |
| **Generation** | Create documents, proposals, communications | ✅ With human review |
| **Explanations** | Explain why something happened or was recommended | ✅ Always |

### AI Limitations

| Limitation | Reason |
|------------|--------|
| **Never owns business logic** | Business rules must be deterministic, testable, auditable |
| **Never makes final decisions** | Decisions require human authority or explicit delegation |
| **Never bypasses permissions** | AI operates within the same permission boundaries as the requesting identity |
| **Never deletes data** | AI may suggest archival, never execute deletion |
| **Never modifies financial records** | Financial mutations require explicit human action |

### AI Observation Model

```
interface AIInsight {
  object_id: string
  type: "understanding" | "prediction" | "suggestion" | "summary" | "explanation" | "anomaly"
  content: any
  confidence: number
  supporting_evidence: Record[]  // what data supports this insight
  requires_review: boolean       // true if human should verify
  created_at: DateTime
  expires_at?: DateTime
}
```

---

## Article XI — Universal History

Nothing disappears.

### Preservation Contract

Every object preserves:

| Artifact | Retention |
|----------|-----------|
| Previous values | Every mutation creates a version record with previous state |
| Relationship history | Every relationship addition/removal is recorded |
| Ownership history | Every owner change, delegation, permission grant |
| Versions | Full version tree, reconstructable |
| AI reasoning | Every AI insight, the evidence that produced it |
| Execution trail | Every execution step, its inputs, outputs, and decisions |
| Event log | Immutable, append-only, ordered |

### Reconstruction

```
Timeline.replay(from, to) → returns state at any point in time
Version.restore(version_id) → restores object to that version
Event.reconstruct(object_id, event_sequence) → builds state from events
```

### Purging Policy

Objects progress: Active → Archived → Recoverable → (after retention period) → Purged.

Purged objects are truly gone — but their events and audit trail remain.

---

## Article XII — Universal Composition

Objects combine naturally.

### Composition Is Not Hardcoded

Customer + Proposal + Meeting + Email + Payment → Opportunity workspace

No custom "Opportunity" module. The workspace emerges from the relationships between these objects.

### Composition Examples

| Composition | Objects | Emergent Property |
|-------------|---------|-------------------|
| Customer + Proposal + Meeting + Email + Payment | Identity + Commitment + Event + Communication + Financial Record | Opportunity/Sales Workspace |
| Student + Course + Attendance + Assignment | Identity + Commitment + Event + Document | Education Workspace |
| Patient + Prescription + Appointment + Invoice | Identity + Commitment + Event + Financial Record | Healthcare Workspace |
| Traveller + Booking + Trip + Payment | Identity + Commitment + Event + Financial Record + Place | Travel Workspace |
| Campaign + Creative + Audience + Analytics | Commitment + Asset + Identity + Event + Observation | Marketing Workspace |

### Composition Rule

SHUNYA never creates industry-specific engines.

It composes workspaces from ontology.

---

## Article XIII — Universal Runtime Contract

Every runtime SHALL guarantee:

| Guarantee | Description |
|-----------|-------------|
| **Deterministic behaviour** | Same inputs → same outputs. No randomness in business logic. |
| **Stateless reconstruction** | Runtime state can be reconstructed from events alone. |
| **Replayability** | Any prior state can be replayed from the event log. |
| **Persistence** | All state is persisted. No in-memory-only business data. |
| **Observability** | Runtime exposes health, activity, performance metrics. |
| **Crash recovery** | Runtime recovers to last consistent state after crash. |
| **AI independence** | Runtime functions without AI. AI is additive, not required. |
| **Provider independence** | No runtime depends on a specific AI provider, database provider, or cloud provider. |

### Prohibited Dependencies

| Dependency | Why |
|------------|-----|
| Browser session state | Runtime must work identically across any client |
| AI provider availability | Runtime must function without AI |
| In-memory-only state | All business state must be durable |

---

## Article XIV — Constitutional Compliance

### Compliance Audit

Every runtime, module, and component SHALL be audited against this constitution.

### Deviation Rules

| Classification | Meaning | Action Required |
|----------------|---------|-----------------|
| **Compliant** | Follows constitutional contract | None |
| **Extension** | Adds domain-specific behavior on top of constitutional contract | Document extension |
| **Deviation** | Replaces or bypasses constitutional contract with custom behavior | Refactor to constitutional contract |
| **Violation** | Contradicts constitutional requirement | Immediate fix required |

### Enforcement

The Governance capability SHALL enforce constitutional compliance.

New code that introduces custom behaviour where constitutional behaviour exists SHALL be rejected.

---

## Ratification

This constitution is ratified and active as of the date below.

All existing SHUNYA runtimes, modules, and components SHALL be audited for compliance.

Deviations SHALL be documented and scheduled for refactoring.

Genesis Reset may not commence until constitutional compliance is achieved.

---

**Ratified:** August 1, 2026
**Directive:** Z-06
**Authority:** SHUNYA Constitution → Product Constitution → Technical Constitution → Z-06