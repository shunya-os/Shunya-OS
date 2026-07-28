# Universal Ontology

**Phase 8D — SHUNYA OS**
**Classification: Constitutional Architecture — Canonical Language**
**Status: PROPOSED**
**Version: 1.0**

---

## Preamble

### Authority

This document defines the canonical meaning of every fundamental concept inside SHUNYA. Every engineer, every AI, every module, every runtime, every workflow, every prediction, every execution must derive from these definitions. Nothing may redefine these concepts later.

### First principles

1. **Software does not invent reality. Software represents reality.**
2. **Reality already contains** People, Organizations, Objects, Relationships, Events, Evidence, Commitments, Knowledge, Intentions, Actions, Outcomes, Time. SHUNYA merely models them faithfully.
3. **Every future object must derive from this ontology.** The Universal Type System is the single inheritance hierarchy.
4. **Future constitutional documents must reference this ontology** rather than redefine concepts.
5. **Nothing may violate the Ontology Dependency Graph.**

### Ontology vs Implementation

This document defines what things ARE, not how they are STORED or MANIPULATED. Implementations may choose any storage mechanism, any API style, any programming language — but they must conform to these definitions. Conformance means:

- Every implemented concept must be traceable to its ontological definition.
- Every implemented concept must satisfy the invariants of its ontological definition.
- No implemented concept may contradict its ontological definition.

---

## 1. Object

### 1.1 Definition

An **Object** is the fundamental unit of reality inside SHUNYA. Everything SHUNYA knows about is an Object.

### 1.2 Canonical properties

| Property | Definition | Mutability |
|----------|------------|------------|
| **Identity** | A permanent, unique, non-reusable identifier | Immutable |
| **Type** | The canonical type from the Universal Type System | Immutable |
| **State** | The current lifecycle state | Mutable (via valid transitions) |
| **Attributes** | The set of properties describing the object | Mutable |
| **Relationships** | The set of connections to other objects | Mutable |
| **Timeline** | The chronological record of all events involving this object | Append-only |
| **Evidence** | The set of observations that support the object's existence | Append-only |
| **Provenance** | The record of origin: how, when, and by whom the object was created | Immutable |

### 1.3 Object identity

- Every object has exactly one identity.
- Identity is assigned at creation and never changes.
- Identity is never reused after deletion.
- Identity is globally unique within the system.

### 1.4 Object lifecycle

Every object follows exactly one lifecycle. The lifecycle is defined by the object's type (see §18 — Universal Type System).

### 1.5 Object persistence

- Objects persist until explicitly deleted.
- Deletion is a state, not destruction. Deleted objects retain their identity, provenance, and timeline.
- Objects can be archived (removed from active attention) without deletion.

### 1.6 Object ownership

- Every object has exactly one owner at any time.
- Ownership can be transferred.
- Ownership determines who can modify the object.
- Ownership does not affect visibility (see §1.7).

### 1.7 Object visibility

- Objects are visible to their owner and to anyone the owner grants access.
- Visibility is orthogonal to ownership.
- Certain object types have system-level visibility (e.g., constitutional objects).

### 1.8 Object mutability rules

| Change | Allowed? | Condition |
|--------|----------|-----------|
| Change identity | NEVER | Identity is permanent |
| Change type | NEVER | Type is permanent |
| Change state | YES | Only via valid state transitions |
| Modify attributes | YES | Subject to attribute-level mutability rules |
| Add relationship | YES | Relationship must be valid for the object type |
| Add evidence | YES | Evidence is always append-only |
| Delete object | YES | Only by owner or system governance |

---

## 2. Entity

### 2.1 Definition

An **Entity** is an Object that represents a distinct, real-world thing. Entities are the primary subjects of SHUNYA's understanding.

### 2.2 Entity classification

| Classification | Definition | Example | Persistence |
|----------------|------------|---------|-------------|
| **Object** | Any unit of reality inside SHUNYA | Everything below | Permanent |
| **Entity** | A real-world thing | A person, a company | Permanent |
| **Representation** | A specific view or projection of an Entity | "Ritu as a contact", "Ritu as a lead" | Derived |
| **Instance** | A single occurrence of a type | "This specific meeting" | Permanent |
| **Reference** | A pointer to an Object from another context | "Mention of Ritu in a document" | Ephemeral |
| **Alias** | An alternative name for the same Entity | "Ritu Sharma" vs "Ritu Shunya" | Contextual |
| **Duplicate** | An Object incorrectly representing the same Entity as another | Two Person objects for the same person | Must be merged |
| **Virtual Entity** | An Entity that exists only within SHUNYA's model | A computed relationship, a derived insight | Until refined |
| **Composite Entity** | An Entity composed of other Entities | A Project containing Tasks and People | Permanent |

### 2.3 Object vs Entity

- **All Entities are Objects.** Not all Objects are Entities.
- Events are Objects but not Entities (they do not persist as distinct real-world things).
- Commitments are Objects but not Entities (they describe relationships, not things).

### 2.4 Duplicate resolution

When a duplicate is detected:

1. Both Objects are preserved (evidence is never destroyed).
2. A superior identity is assigned to the primary Object.
3. The duplicate Object is marked as MERGED.
4. All relationships from the duplicate are transferred to the primary.
5. The duplicate's identity is retired (never reused).

### 2.5 Virtual entities

A Virtual Entity:

- Has no direct real-world counterpart.
- Is derived from analysis of real Entities.
- Has lower confidence than the Entities it derives from.
- May be promoted to a real Entity if independently verified.

---

## 3. Identity

### 3.1 Definition

**Identity** is the permanent, unique, non-reusable designation of an Object.

### 3.2 Identity types

| Type | Definition | Scope | Example |
|------|------------|-------|---------|
| **Permanent identity** | The system-assigned internal identity | System-wide | `obj_person_a1b2c3d4` |
| **External identity** | An identity from an external system | External system scope | `user_12345` from external CRM |
| **Derived identity** | An identity computed from other identities | System-wide | Hash of email + name |
| **Temporary identity** | An identity valid for a limited time | Session or workflow | `temp_conv_abc123` |
| **Merged identity** | An identity that absorbed another | System-wide | Primary after merge |
| **Split identity** | An identity that was divided into two | System-wide | Both resulting identities |
| **Deleted identity** | An identity that is permanently retired | Never reused | Identity marked DELETED |

### 3.3 Identity rules

1. **Permanent identity is immutable.** It is assigned at creation and never changes.
2. **External identity is contextual.** Two external identities from different systems may refer to the same Entity.
3. **Derived identity is stable.** Same inputs always produce the same derived identity.
4. **Temporary identity expires.** After expiration, the identity is released.
5. **Merged identity is terminal.** The absorbed identity is retired.
6. **Split identity creates two new permanent identities.** The original identity is retired.
7. **Deleted identity is never reused.** Deletion does not free the identity for reuse.

### 3.4 Identity resolution

Identity resolution is the process of determining whether two identities refer to the same Entity:

1. Permanent identity match → YES (same Object)
2. External identity match → YES (same Entity, different Object — requires merge)
3. Derived identity match → PROBABLE (requires additional evidence)
4. Attribute overlap → POSSIBLE (requires investigation)
5. No match → NO (different Entities)

### 3.5 Identity governance

#### 3.5.1 Identity authority

Identity assignment is governed by the following authorities:

| Authority | Can assign | Validation required |
|-----------|------------|---------------------|
| **Reality Runtime** | Permanent identities for newly observed entities | Automatic — identity must be unique |
| **Object Factory** | Permanent identities for derived objects | Identity must reference parent object's evidence |
| **Founder** | Temporary identities, aliases | Founder confirmation is sufficient |
| **Governance Engine** | Merged identities, split identities | Must follow §3.5.2 and §3.5.3 |
| **External system** | External identities only | Must be mapped through Identity Resolution (§3.4) |

No subsystem may create an identity without authorization from one of these authorities.

#### 3.5.2 Merge rules

When two identities refer to the same Entity:

1. The superior identity is determined by: (a) earlier creation timestamp, or (b) higher accumulated evidence confidence, or (c) founder designation
2. The superior identity becomes the permanent identity
3. The inferior identity is marked as MERGED
4. All relationships from the inferior identity are transferred to the superior
5. The inferior identity is retired (never reused)
6. All evidence is preserved for both identities

#### 3.5.3 Split rules

When one identity is discovered to represent two distinct Entities:

1. A new identity is created for the second Entity
2. Evidence is partitioned between the two identities based on which evidence belongs to which Entity
3. Relationships are partitioned similarly
4. The original identity retains evidence and relationships that cannot be confidently assigned
5. Both identities record the split in their provenance
6. The split is logged as an auditable governance action

#### 3.5.4 Retirement

An identity is retired when:

1. It is merged into a superior identity
2. It is split and both resulting identities are new
3. The Object is deleted (terminal state)
4. Governance explicitly retires it

Retired identities are never reused. A retired identity maintains its provenance record permanently.

#### 3.5.5 Conflict resolution

When identity resolution produces conflicting results:

1. Both resolutions are presented with their evidence chains
2. If one resolution has confidence ≥ 0.7 higher than the other, the higher-confidence resolution is accepted
3. If confidences are within 0.3 of each other, the resolution is escalated to the founder
4. All conflicting resolutions are recorded in the audit trail

#### 3.5.6 Identity auditability

Every identity operation is auditable:

| Operation | Audit record |
|-----------|-------------|
| Identity creation | Authority, timestamp, Object type |
| Identity merge | Inferior identity, superior identity, rationale |
| Identity split | Original identity, new identity, evidence partition |
| Identity retirement | Identity, reason, authority |
| Identity resolution | Input identities, result, confidence, evidence references |

#### 3.5.7 Identity invariants

1. Every identity is assigned by exactly one authority.
2. Identity is immutable after assignment.
3. Merged identities retain their provenance.
4. Split identities record the split in both resulting identities.
5. Retired identities are never reused.
6. All identity operations are auditable.

## 4. Attribute

### 4.1 Definition

An **Attribute** is a property of an Object that describes some aspect of it.

### 4.2 Attribute types

| Type | Definition | Mutability | Example |
|------|------------|------------|---------|
| **Required** | Must be present for the Object to exist | Immutable after creation | Object type, identity |
| **Optional** | May be present or absent | Mutable | Description, notes |
| **Derived** | Computed from other attributes | Read-only | Age from birth date |
| **Computed** | Result of an algorithm or reasoning | Read-only | Risk score |
| **Observed** | Directly observed by a human or system | Append-only | Phone number |
| **Predicted** | Estimated by the Prediction Engine | Read-only, decaying | Expected close date |
| **Confidential** | Requires special access to view | Mutable (access level) | Salary, private notes |
| **Immutable** | Set once, never modified | Immutable | Created timestamp |

### 4.3 Attribute inheritance

When an Object is derived from another Object:

| Inheritance type | Behaviour |
|------------------|-----------|
| **Direct** | Child Object copies parent attribute value at creation |
| **Computed** | Child Object inherits a formula, not a value |
| **Overridden** | Child Object may override the inherited value |
| **Blocked** | Child Object does not inherit certain attributes |
| **Transformed** | Child Object inherits a transformed version of the value |

### 4.4 Attribute validation rules

1. Required attributes must be present at creation.
2. Immutable attributes must not change after creation.
3. Derived attributes are never directly set — they are computed.
4. Confidential attributes are never included in default projections.
5. Predicted attributes always carry a confidence score.

---

## 5. Relationship

### 5.1 Definition

A **Relationship** is a connection between two Objects. Relationships are the second fundamental structure of reality — they describe how Objects relate to each other.

### 5.2 Relationship properties

| Property | Definition | Mutability |
|----------|------------|------------|
| **Source** | The Object the relationship originates from | Immutable |
| **Target** | The Object the relationship points to | Immutable |
| **Type** | The canonical relationship type | Immutable |
| **Direction** | The direction of the relationship | Immutable |
| **Strength** | The confidence or intensity of the relationship | Mutable |
| **Timeline** | When the relationship was active | Append-only |
| **Evidence** | What observations support this relationship | Append-only |

### 5.3 Relationship types

| Type | Direction | Definition | Example |
|------|-----------|------------|---------|
| **Directional** | Source → Target | One-way connection | Person → Company (EMPLOYED_BY) |
| **Bidirectional** | Source ↔ Target | Mutual connection | Person ↔ Person (KNOWS) |
| **Hierarchical** | Parent → Child | Containment or reporting | Company → Person (WORKS_AT) |
| **Temporal** | Source —[time]→ Target | Time-bound connection | Person → Event (ATTENDED) |
| **Contextual** | Source —[context]→ Target | Context-dependent | Person → Document (AUTHORED_IN_CAPACITY) |
| **Inherited** | Source → Target via chain | Transitive | Person → Department → Company |
| **Predicted** | Source → Target (inferred) | Low confidence | Person → Person (MAY_KNOW) |
| **Evidence-backed** | Source → Target + Evidence | Requires evidence | Person → Company (SIGNED_CONTRACT) |

### 5.4 Relationship lifecycle

```
PROPOSED (predicted, unconfirmed)
  ↓
ACTIVE (confirmed, evidence present)
  ↓
STALE (no recent interaction, decaying)
  ↓
ARCHIVED (no longer relevant, history preserved)
  ↓
REMOVED (determined incorrect)
```

| State | Visibility | Effect on scoring |
|-------|------------|-------------------|
| PROPOSED | Low visibility | Not used in relationship scoring |
| ACTIVE | Normal visibility | Full contribution to relationship graph |
| STALE | Reduced visibility | Lower weight in attention scoring |
| ARCHIVED | Historical only | Preserved but not active |
| REMOVED | Hidden | No contribution |

### 5.5 Relationship invariants

1. A relationship is uniquely identified by (source, target, type).
2. A relationship cannot duplicate another relationship with the same (source, target, type).
3. A relationship cannot have a null source or target.
4. A relationship can exist between any two Objects regardless of type.
5. Self-relationships (source = target) are valid for certain types.
6. Relationships are traceable to their originating evidence.

---

## 6. Observation

### 6.1 Definition

An **Observation** is the atomic unit of learning. Everything SHUNYA learns begins as an observation.

### 6.2 Observation hierarchy

```
┌──────────────────────────────────────────────────────────────────────┐
│  KNOWLEDGE                                                           │
│  Validated, structured, and integrated understanding                 │
│  ↑                                                                   │
│  EVIDENCE                                                            │
│  Observations interpreted in context, with confidence                │
│  ↑                                                                   │
│  INFERENCE                                                           │
│  A conclusion drawn from one or more observations                    │
│  ↑                                                                   │
│  INTERPRETATION                                                      │
│  An observation placed in context but not yet validated              │
│  ↑                                                                   │
│  ASSUMPTION                                                          │
│  An unverified claim accepted as true for reasoning                  │
│  ↑                                                                   │
│  OBSERVATION                                                         │
│  Raw data: "X happened at time T"                                    │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.3 Observation properties

| Property | Definition |
|----------|------------|
| **Content** | What was observed |
| **Observer** | Who or what made the observation |
| **Timestamp** | When the observation was made |
| **Source** | Where the observation came from |
| **Confidence** | How reliable the observation is (0.0 – 1.0) |
| **Context** | The circumstances of the observation |

### 6.4 Observation vs derived types

| Type | How created | Can it be modified? |
|------|-------------|---------------------|
| **Observation** | Direct sensing | No (immutable) |
| **Interpretation** | Observation + context | No (once recorded) |
| **Assumption** | Reasoning without observation | Yes (can be replaced) |
| **Inference** | Observation + rule | Yes (if rule changes) |
| **Prediction** | Inference + time | Yes (decays, updates) |
| **Knowledge** | Validation + promotion | No (constitutional) |
| **Evidence** | Observation + verification | No (immutable) |

---

## 7. Evidence

### 7.1 Definition

**Evidence** is an Observation that has been verified and placed in context. Evidence is the constitutional foundation of all knowledge.

### 7.2 Evidence types

| Type | Definition | Confidence base | Example |
|------|------------|-----------------|---------|
| **Primary** | Direct, firsthand evidence | 0.9 | Founder says "Rahul is the CEO" |
| **Secondary** | Reported by a reliable intermediary | 0.7 | System logs show rahul@company.com |
| **External** | From an external, verified source | 0.8 | Official company registry |
| **Human** | Provided by a person | Variable (0.3 – 1.0) | Founder input (1.0), third-party (0.3) |
| **Machine** | Collected by an automated system | 0.8 | Parsed document, detected pattern |
| **Verified** | Cross-checked against another source | 0.9 | Two independent sources agree |
| **Unverified** | Single source, not yet checked | 0.5 | Single observation |
| **Historical** | Evidence that is no longer current | Decaying | Past address |
| **Live** | Evidence that is currently valid | Full confidence | Current phone number |

### 7.3 Evidence confidence

```
evidence_confidence = source_reliability × verification_factor × recency_factor
```

| Factor | Definition | Range |
|--------|------------|-------|
| Source reliability | Trustworthiness of the source | 0.3 – 1.0 |
| Verification factor | Whether cross-checked against other sources | 0.5 (unverified) – 0.9 (verified) |
| Recency factor | How recently the evidence was gathered | 0.5 (old) – 1.0 (fresh) |

### 7.4 Evidence invariants

1. Evidence is immutable once recorded.
2. Evidence is append-only. New evidence can be added; old evidence cannot be removed.
3. Evidence is always traceable to its source.
4. Evidence always carries a confidence score.
5. Conflicting evidence is preserved (SHUNYA holds both positions until resolution).

---

## 8. Event

### 8.1 Definition

An **Event** is something that changes reality. Events are the atomic units of change inside SHUNYA.

### 8.2 Event properties

| Property | Definition | Mutability |
|----------|------------|------------|
| **Identity** | Unique event identifier | Immutable |
| **Type** | Canonical event type | Immutable |
| **Timestamp** | When the event occurred | Immutable |
| **Actor** | Who or what caused the event | Immutable |
| **Target** | The Object(s) affected by the event | Immutable |
| **Payload** | The data associated with the event | Immutable |
| **Causation** | The event that caused this event | Immutable |
| **Correlation** | Related events sharing a context | Immutable |

### 8.3 Canonical event types

| Type | Definition | Impact |
|------|------------|--------|
| **Creation** | An Object comes into existence | New Object added to graph |
| **Modification** | An Object's attributes change | Object version updated |
| **Deletion** | An Object is marked as deleted | Object state = DELETED |
| **Communication** | Information is exchanged | Conversation Object updated |
| **Decision** | A choice is made | Decision Object created |
| **Execution** | An action is performed | Execution Object created |
| **Failure** | An execution does not complete as intended | Execution Object updated |
| **Success** | An execution completes as intended | Execution Object updated |
| **Discovery** | New information is found | Evidence Object created |
| **Escalation** | An issue is raised to higher authority | Escalation Object created |
| **Resolution** | An issue is resolved | Related Objects updated |

### 8.4 Event immutability

Events are the most immutable structure in SHUNYA. An event, once recorded, can never be:

- Modified
- Deleted
- Reordered
- Superseded (a correction is a new event, not a modification)

---

## 9. Commitment

### 9.1 Definition

A **Commitment** is a constitutional Object that represents an obligation between parties.

### 9.2 Commitment properties

| Property | Definition |
|----------|------------|
| **Promise** | What was promised |
| **Responsible party** | Who made the commitment |
| **Beneficiary** | Who the commitment benefits |
| **Deadline** | When the commitment must be fulfilled |
| **Dependency** | What must happen before fulfilment |
| **Owner** | Who is responsible for tracking |
| **Evidence** | The observations that establish the commitment |
| **Status** | Current state of the commitment |

### 9.3 Commitment lifecycle

```
PROPOSED (commitment identified but not accepted)
  ↓
ACTIVE (commitment accepted, deadline set)
  ↓
IN_PROGRESS (work toward fulfilment underway)
  ↓
FULFILLED (commitment met)
  ↓
VERIFIED (fulfilment confirmed by beneficiary)
```

Alternative paths:

```
ACTIVE → VIOLATED (deadline passed without fulfilment)
ACTIVE → CANCELLED (commitment revoked by either party)
PROPOSED → REJECTED (commitment not accepted)
```

### 9.4 Commitment invariants

1. Every commitment has exactly one responsible party.
2. Every commitment has exactly one beneficiary.
3. Every commitment has exactly one owner.
4. Every commitment has a deadline (may be indefinite).
5. Every commitment is supported by evidence.
6. Commitments are traceable to their originating events.

---

## 10. Action

### 10.1 Definition

An **Action** is an atomic unit of work. Actions are distinguished from Tasks, Executions, and other related concepts by their scope and granularity.

### 10.2 Action hierarchy

```
┌──────────────────────────────────────────────────────────────────────┐
│  WORKFLOW                                                            │
│  A sequence of related actions with conditional branching            │
│  ↑                                                                   │
│  EXECUTION                                                           │
│  A single run of an action or workflow, with context and outcome     │
│  ↑                                                                   │
│  TASK                                                                 │
│  A unit of work assigned to a person or system, with a deadline      │
│  ↑                                                                   │
│  ACTION                                                              │
│  A discrete, indivisible unit of work                                │
│  ↑                                                                   │
│  OPERATION                                                           │
│  A system-level atomic transformation (create, update, delete)       │
└──────────────────────────────────────────────────────────────────────┘
```

### 10.3 Distinctions

| Concept | Definition | Has deadline? | Has assignee? | Has state? |
|---------|------------|---------------|---------------|------------|
| **Action** | Discrete, indivisible unit of work | No | No | No (instantaneous) |
| **Task** | Assigned unit of work with deadline | Yes | Yes | Yes |
| **Execution** | A run of an action or workflow | No | System | Yes |
| **Operation** | System-level atomic transformation | No | System | No (instantaneous) |
| **Automation** | An action triggered by a condition | May have | System | Yes |
| **Workflow** | Sequence of actions with branching | Composite | Per task | Yes |
| **Command** | An instruction from a user | No | System | No |
| **Suggestion** | A recommendation without obligation | No | No | No |
| **Recommendation** | A suggested action with rationale | No | No | No |

---

## 11. State

### 11.1 Definition

**State** is the current condition of an Object within its lifecycle. Every Object possesses state.

### 11.2 State properties

| Property | Definition |
|----------|------------|
| **Current state** | The state the Object is in now |
| **Valid transitions** | The set of states reachable from the current state |
| **Invalid transitions** | States that cannot be reached from the current state |
| **Terminal states** | States from which no transition is possible |

### 11.3 State categories

| Category | Definition | Example |
|----------|------------|---------|
| **Active** | The Object is in use | ACTIVE, IN_PROGRESS, PENDING |
| **Inactive** | The Object exists but is not in use | ARCHIVED, STALE, DORMANT |
| **Terminal** | The Object's lifecycle is complete | DELETED, COMPLETED, FULFILLED |
| **Error** | The Object encountered an unexpected condition | FAILED, VIOLATED, CANCELLED |
| **Transitional** | The Object is moving between states | PROPOSED, PENDING_APPROVAL |

### 11.4 State invariants

1. Every Object has exactly one current state at any time.
2. An Object can only move to a state reachable via valid transitions.
3. Terminal states are absorbing — no transition out.
4. State transitions are recorded on the Object's timeline.
5. State transitions are events (see §8).

---

## 12. Timeline

### 12.1 Definition

A **Timeline** is the chronological record of all events involving an Object. Every Object has exactly one timeline.

### 12.2 Timeline structure

```
Past (immutable, recorded)
  │
  ▼
Present (the current moment)
  │
  ▼
Expected Future (projected based on existing knowledge)
  │
  ▼
Alternative Future (what-if scenarios, predictions)
```

### 12.3 Timeline components

| Component | Definition | Mutability |
|-----------|------------|------------|
| **Past** | All events that have occurred | Immutable |
| **Present** | The current state and context | Mutable (now) |
| **Expected future** | Projected events based on knowledge | Mutable (updates with new knowledge) |
| **Alternative future** | What-if scenarios and counterfactual predictions | Mutable |

### 12.4 Timeline types

| Type | What it contains | Update frequency |
|------|------------------|------------------|
| **Historical truth** | Events that actually happened | Append-only |
| **Projected truth** | Events that are predicted to happen | Continuous |
| **Expected future** | The most likely sequence of future events | On new knowledge |
| **Alternative future** | Other possible sequences | On request |

---

## 13. Context

### 13.1 Definition

**Context** is the set of circumstances surrounding an Object, Event, or Interaction. Context determines meaning.

### 13.2 Context types

| Type | Definition | Scope | Lifetime |
|------|------------|-------|----------|
| **Workspace Context** | The current focus of the workspace | The active Object | Session |
| **Conversation Context** | The history and purpose of a conversation | The conversation | Until conversation ends |
| **Execution Context** | The circumstances of an execution | The execution | Until execution completes |
| **Relationship Context** | The nature of a connection between Objects | The relationship | As long as relationship is active |
| **Temporal Context** | The time period relevant to an Object or Event | Time-bounded | Until the period ends |
| **Organisational Context** | The organisational structure surrounding an Object | Organisation | Permanent |
| **Inherited Context** | Context passed from a parent Object to a child | Child Object | Until overridden |

### 13.3 Context inheritance

Context flows from broader to narrower scope:

```
Organisational Context
  ↓
Workspace Context
  ↓
Conversation Context
  ↓
Execution Context
```

Narrower contexts can override broader contexts for their scope.

### 13.4 Context invariants

1. Context is never destroyed. It may be archived or superseded.
2. Context is always traceable to its source.
3. Inherited context can be overridden but not ignored.
4. Context changes are events (see §8).

---

## 14. Knowledge

### 14.1 Definition

**Knowledge** is validated, structured understanding. It is what SHUNYA knows to be true (with quantifiable confidence).

### 14.2 Knowledge hierarchy

```
┌──────────────────────────────────────────────────────────────────────┐
│  WISDOM                                                              │
│  Knowledge applied with judgement over time                          │
│  ↑                                                                   │
│  REASONING                                                           │
│  The process of deriving new understanding from existing knowledge   │
│  ↑                                                                   │
│  UNDERSTANDING                                                       │
│  Integrated knowledge that enables explanation and prediction        │
│  ↑                                                                   │
│  KNOWLEDGE                                                           │
│  Validated, structured, evidence-backed understanding               │
│  ↑                                                                   │
│  INFORMATION                                                         │
│  Structured observations without validation                          │
│  ↑                                                                   │
│  DATA                                                                │
│  Raw, unprocessed observations                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 14.3 Knowledge types

| Type | Definition | Confidence | Can be modified? |
|------|------------|------------|------------------|
| **Information** | Structured but unvalidated observations | < 0.6 | Yes |
| **Knowledge** | Validated, evidence-backed understanding | ≥ 0.6 | Yes (with new evidence) |
| **Understanding** | Integrated knowledge enabling prediction | ≥ 0.8 | Yes (with new evidence) |
| **Reasoning** | The process of deriving understanding | N/A | Yes (improves with calibration) |
| **Wisdom** | Knowledge applied with judgement over time | ≥ 0.95 | No (constitutional) |
| **Prediction** | An estimate of future state | Variable | Yes (decays, updates) |
| **Belief** | An accepted proposition without full validation | < 0.5 | Yes |
| **Confidence** | The quantified reliability of knowledge | 0.0 – 1.0 | Yes (updates with evidence) |

### 14.4 Knowledge invariants

1. All knowledge references evidence. No evidence → no knowledge.
2. Knowledge is promoted through defined stages (§14.2).
3. Knowledge can be demoted if contradicted by stronger evidence.
4. Knowledge never loses its evidence chain.
5. Predictions are never facts. They are always labelled as predictions.

---

## 15. Prediction

### 15.1 Definition

A **Prediction** is an estimate of a future state or outcome, based on existing knowledge and evidence.

### 15.2 Prediction properties

| Property | Definition |
|----------|------------|
| **Prediction Object** | The Object being predicted about |
| **Predicted value** | What is predicted to happen |
| **Confidence** | The estimated reliability of the prediction (0.0 – 1.0) |
| **Horizon** | The time period the prediction covers |
| **Evidence** | The observations and knowledge supporting the prediction |
| **Assumptions** | The assumptions underlying the prediction |

### 15.3 Prediction lifecycle

```
CREATED (prediction generated)
  ↓
MONITORED (compared against unfolding reality)
  ↓
VALIDATED (compared against outcome)
  ↓
SUCCESS (prediction matched reality) → reinforced
  ↓
FAILURE (prediction did not match reality) → analysed
  ↓
RETIRED (prediction removed from active use)
```

### 15.4 Prediction invariants

1. Every prediction carries an evidence chain.
2. Every prediction has a confidence score.
3. Every prediction has a defined horizon.
4. Predictions are never facts. They are always labelled as predictions.
5. Prediction failure is analysed, not ignored.

---

## 16. Policy

### 16.1 Definition

A **Policy** is a rule that governs behaviour inside SHUNYA.

### 16.2 Policy types

| Type | Definition | Scope | Can be overridden? |
|------|------------|-------|-------------------|
| **Constitutional policy** | Immutable system rule | System-wide | No (constitutional amendment required) |
| **Runtime policy** | Operational behaviour rule | System-wide | Yes (by Governance) |
| **Business policy** | Domain-specific rule | Organisation | Yes (by Founder or delegate) |
| **Personal policy** | Individual preference | Single user | Yes (by the user) |
| **Temporary policy** | Time-limited rule | Defined scope | Yes (by issuer) |
| **Inherited policy** | Policy derived from a parent scope | Child scope | Yes (by child scope) |

### 16.3 Policy hierarchy

```
Constitutional Policy (system-wide, immutable)
  ↓
Runtime Policy (system-wide, mutable by Governance)
  ↓
Business Policy (organisation-wide, mutable by Founder)
  ↓
Personal Policy (user-specific, mutable by user)
```

### 16.4 Policy invariants

1. Policies higher in the hierarchy override lower policies.
2. Constitutional policies cannot be overridden.
3. All policy changes are versioned.
4. All policy changes are auditable.
5. Policy rollback restores the previous version.

---

## 17. Memory

### 17.1 Definition

**Memory** is the storage and retrieval system for all knowledge, experience, and context.

### 17.2 Memory types

| Type | Content | Lifetime | Retrieval |
|------|---------|----------|-----------|
| **Working Memory** | Current focus + 1-hop relationships | Session (minutes) | Instant |
| **Conversation Memory** | Active conversation history | Conversation duration | Linear |
| **Relationship Memory** | Connection strengths, interaction patterns | Days to months | Graph traversal |
| **Knowledge Memory** | Validated facts and understanding | Months to years | Semantic query |
| **Historical Memory** | All past events and archived Objects | Permanent | Search |
| **Constitutional Memory** | Immutable system rules and invariants | Permanent | Direct reference |

### 17.3 Memory promotion

```
Working Memory (minutes)
  ↓ Rehearsal
Conversation Memory (hours)
  ↓ Pattern detection
Relationship Memory (days)
  ↓ Validation
Knowledge Memory (months)
  ↓ Constitutional review
Constitutional Memory (permanent)
```

---

## 18. Universal Type System

### 18.1 Canonical inheritance tree

```
Object (root)
├── Entity
│   ├── Person
│   ├── Organization
│   │   ├── Company
│   │   ├── Team
│   │   └── Department
│   ├── Document
│   ├── Meeting
│   ├── Project
│   └── Workspace
├── Relationship
│   ├── Employment
│   ├── Ownership
│   ├── Membership
│   ├── Contractual
│   └── Social
├── Event
│   ├── Creation
│   ├── Modification
│   ├── Communication
│   ├── Decision
│   ├── Execution
│   ├── Failure
│   └── Resolution
├── Commitment
│   ├── Promise
│   ├── Obligation
│   ├── Agreement
│   └── Deadline
├── Action
│   ├── Task
│   ├── Execution
│   ├── Operation
│   └── Workflow
├── Evidence
│   ├── Observation
│   ├── Verification
│   └── Source
├── Knowledge
│   ├── Fact
│   ├── Inference
│   ├── Rule
│   └── Pattern
├── Prediction
│   ├── Forecast
│   ├── Risk
│   ├── Opportunity
│   └── Trend
├── Policy
│   ├── Constitutional
│   ├── Runtime
│   ├── Business
│   └── Personal
├── Conversation
│   ├── Message
│   ├── Thread
│   └── Transcript
└── Context
    ├── Workspace
    ├── Execution
    ├── Temporal
    └── Organisational
```

### 18.2 Type properties

Every type in the inheritance tree inherits:
- The Object's canonical properties (§1.2)
- All invariants of its parent type
- The ability to have Relationships (§5)
- A Timeline (§12)
- A lifecycle defined by valid state transitions (§11)

### 18.3 Type rules

1. Every Object has exactly one type.
2. Type is immutable after creation.
3. Types form a strict hierarchy (no multiple inheritance).
4. Subtypes inherit all properties and invariants of their parent.
5. Subtypes may add properties and invariants but may not remove them.

### 18.4 Per-type lifecycle mapping

#### 18.4.1 Universal lifecycle

Every Object follows the universal lifecycle defined in COGNITIVE_WORKSPACE_RUNTIME.md §6:

```
CREATE → OBSERVE → ENRICH → RELATE → PREDICT → EXECUTE → ARCHIVE → RESTORE
```

Alternative path: `ARCHIVE → DELETE` (terminal state).

#### 18.4.2 Type-specific lifecycle mapping

The universal lifecycle is the canonical lifecycle for all types. Type-specific behaviour is achieved by:

1. **Constraining which states are valid** for a given type (e.g., a Document may not enter EXECUTE state)
2. **Adding type-specific sub-states** that refine a universal state (e.g., Commitment.FULFILLED is a sub-state of ARCHIVE)
3. **Defining type-specific transition rules** (e.g., a Task cannot go from OBSERVE directly to EXECUTE without going through PREDICT first)

#### 18.4.3 Lifecycle inheritance hierarchy

```
Universal Lifecycle (§6 of CWR)
  ↓
Type Group Lifecycle (e.g., Entity lifecycle, Event lifecycle)
  ↓
Specific Type Lifecycle (e.g., Person lifecycle, Document lifecycle)
  ↓
Implementation Lifecycle (code-level state machine)
```

Each layer constrains the layer above it:
- The Universal Lifecycle defines the maximum set of valid states.
- The Type Group Lifecycle restricts which states are applicable to a family of types.
- The Specific Type Lifecycle defines exact transitions for a single type.
- The Implementation Lifecycle is the code-level state machine that enforces the Specific Type Lifecycle.

#### 18.4.4 Type group lifecycles

| Type group | Applicable universal states | Restricted states |
|------------|----------------------------|-------------------|
| **Entity** (Person, Organization, Document, Meeting, Project, Workspace) | CREATE, OBSERVE, ENRICH, RELATE, ARCHIVE, RESTORE, DELETE | PREDICT, EXECUTE — entities are predicted about and executed upon, but do not enter these states themselves |
| **Event** | CREATE only (then becomes immutable) | All states after CREATE — events are immutable once created |
| **Commitment** | CREATE, OBSERVE, ENRICH, RELATE, PREDICT, EXECUTE, ARCHIVE, RESTORE | Full lifecycle |
| **Action** (Task, Execution, Operation, Workflow) | CREATE, OBSERVE, ENRICH, RELATE, PREDICT, EXECUTE, ARCHIVE | Full lifecycle |
| **Evidence** | CREATE (then immutable) | All states after CREATE |
| **Knowledge** | CREATE, OBSERVE, ENRICH, RELATE, ARCHIVE, RESTORE, DELETE | PREDICT, EXECUTE — knowledge is used for prediction and execution but does not enter those states |
| **Prediction** | CREATE, OBSERVE, ENRICH, RELATE, EXECUTE, ARCHIVE | PREDICT — predictions are not predicted about |
| **Policy** | CREATE, OBSERVE, ENRICH, RELATE, ARCHIVE, RESTORE, DELETE | PREDICT, EXECUTE |
| **Conversation** | CREATE, OBSERVE, ENRICH, RELATE, ARCHIVE | PREDICT, EXECUTE |
| **Memory** | CREATE, OBSERVE, ENRICH, RELATE, ARCHIVE, RESTORE | PREDICT, EXECUTE |

#### 18.4.5 Lifecycle invariants

1. Every Object follows exactly one lifecycle (the universal lifecycle).
2. Type group lifecycles may restrict but never extend the universal lifecycle.
3. Specific type lifecycles may add sub-states but never add new top-level states.
4. Implementation lifecycles must conform to the specific type lifecycle.

---

## 19. Constitutional Invariants

### 19.1 Foundational invariants

| ID | Invariant | Rationale |
|----|-----------|-----------|
| O-01 | Identity never changes | Objects are permanently identifiable |
| O-02 | History is immutable | Past events cannot be modified |
| O-03 | Evidence is append-only | Evidence can be added but never removed |
| O-04 | Relationships remain traceable | Every relationship references its originating evidence |
| O-05 | Objects never silently disappear | Deletion is a state, not destruction |
| O-06 | Knowledge always references evidence | No evidence → no knowledge |
| O-07 | Predictions are never facts | Predictions are always labelled with confidence |
| O-08 | Reality outranks assumptions | Direct observation supersedes inference |
| O-09 | Context is never destroyed | Context may be archived but never deleted |
| O-10 | Events are immutable | Once recorded, events cannot be modified |
| O-11 | Type is permanent | An Object's type never changes |
| O-12 | State transitions are valid | Only defined transitions are permitted |
| O-13 | Ownership is singular | Every Object has exactly one owner |
| O-14 | Commitments are traceable | Every commitment references its originating event |

### 19.2 Structural invariants

| ID | Invariant | Rationale |
|----|-----------|-----------|
| O-15 | The Ontology Dependency Graph is never violated | Reality → Observation → Evidence → Object → Relationship → Knowledge → Reasoning → Prediction → Execution → Workspace |
| O-16 | Every concept derives from the Universal Type System | No concept exists outside the hierarchy |
| O-17 | Relationships are uniquely defined by (source, target, type) | No duplicate relationships |
| O-18 | State is singular | Every Object has exactly one current state |
| O-19 | Timelines are append-only | Events can be added but never removed |
| O-20 | Policies are hierarchical | Higher-scope policies override lower |

### 19.3 Consolidated invariants

The following invariants are defined in downstream documents. They are consolidated here for a single authoritative index. The owning document is listed for each.

| ID | Invariant | Owner | Source document |
|----|-----------|-------|----------------|
| O-21 | The current object always exists | COGNITIVE_WORKSPACE_RUNTIME | CWR §7 (I-01) |
| O-22 | Conversation never loses context | COGNITIVE_WORKSPACE_RUNTIME | CWR §7 (I-02) |
| O-23 | UI cannot mutate cognition directly | COGNITIVE_WORKSPACE_RUNTIME | CWR §7 (I-05) |
| O-24 | Reasoning is reproducible | COGNITIVE_WORKSPACE_RUNTIME | CWR §7 (I-06) |
| O-25 | Execution is observable | COGNITIVE_WORKSPACE_RUNTIME | CWR §7 (I-08) |
| O-26 | Every projection is a snapshot | COGNITIVE_WORKSPACE_RUNTIME | CWR §7 (I-10) |
| O-27 | The workspace is read-only projection | COGNITIVE_WORKSPACE_RUNTIME | CWR §7 (I-11) |
| O-28 | Memory decays deterministically | COGNITIVE_WORKSPACE_RUNTIME | CWR §7 (I-12) |
| O-29 | Object lifecycle is event-sourced | COGNITIVE_WORKSPACE_RUNTIME | CWR §7 (I-13) |
| O-30 | Attention is computed, not configured | COGNITIVE_WORKSPACE_RUNTIME | CWR §7 (I-14) |
| O-31 | The composer is the single input channel | COGNITIVE_WORKSPACE_RUNTIME | CWR §7 (I-15) |
| O-32 | Confidence is always explainable | ADAPTIVE_INTELLIGENCE_RUNTIME | Adaptive §14 (AI-03) |
| O-33 | Every adaptation is auditable | ADAPTIVE_INTELLIGENCE_RUNTIME | Adaptive §14 (AI-05) |
| O-34 | Knowledge evolution is reversible | ADAPTIVE_INTELLIGENCE_RUNTIME | Adaptive §14 (AI-06) |
| O-35 | Silent behavioural drift is prohibited | ADAPTIVE_INTELLIGENCE_RUNTIME | Adaptive §14 (AI-07) |
| O-36 | The founder remains sovereign | ADAPTIVE_INTELLIGENCE_RUNTIME | Adaptive §14 (AI-08) |
| O-37 | Policies are versioned | ADAPTIVE_INTELLIGENCE_RUNTIME | Adaptive §14 (AI-09) |
| O-38 | Calibration is periodic | ADAPTIVE_INTELLIGENCE_RUNTIME | Adaptive §14 (AI-10) |
| O-39 | Recovery is deterministic | ADAPTIVE_INTELLIGENCE_RUNTIME | Adaptive §14 (AI-11) |
| O-40 | Experience is typed | ADAPTIVE_INTELLIGENCE_RUNTIME | Adaptive §14 (AI-12) |
| O-41 | The deterministic boundary is explicit | ADAPTIVE_INTELLIGENCE_RUNTIME | Adaptive §14 (AI-13) |
| O-42 | Promotion is gated | ADAPTIVE_INTELLIGENCE_RUNTIME | Adaptive §14 (AI-14) |
| O-43 | Governance is recorded | ADAPTIVE_INTELLIGENCE_RUNTIME | Adaptive §14 (AI-15) |

---

## 20. Ontology Dependency Graph

### 20.1 The constitutional flow of reality

```
REALITY
  │
  ▼
OBSERVATION (raw data enters the system)
  │
  ▼
EVIDENCE (observations are verified and contextualized)
  │
  ▼
OBJECT (entities and concepts are created from evidence)
  │
  ▼
RELATIONSHIP (connections between objects are established)
  │
  ▼
KNOWLEDGE (validated understanding emerges from evidence + relationships)
  │
  ▼
REASONING (new understanding is derived from knowledge)
  │
  ▼
PREDICTION (future states are projected from reasoning)
  │
  ▼
EXECUTION (actions are performed based on predictions)
  │
  ▼
WORKSPACE (reality is projected to the founder)
```

### 20.2 Graph rules

1. **Nothing may skip a layer.** Every concept must pass through each stage of the dependency graph.
2. **Nothing may reverse the flow.** Workspace does not drive Observation. Execution does not drive Reality.
3. **Nothing may bypass Evidence.** No knowledge exists without underlying evidence.
4. **Nothing may bypass Relationship.** No object exists in isolation; every object has at least one relationship.
5. **Nothing may bypass Knowledge.** Predictions require knowledge; they do not emerge directly from evidence.
6. **Nothing may bypass Reasoning.** Executions require reasoning; they are not triggered directly by observations.

### 20.3 Layer responsibilities

| Layer | Owns | Produces | Consumes |
|-------|------|----------|----------|
| **Reality** | The external world | Observations | Nothing |
| **Observation** | Raw data intake | Observations | Reality |
| **Evidence** | Verification, contextualization | Evidence | Observations |
| **Object** | Identity, lifecycle, state | Objects | Evidence |
| **Relationship** | Connections, graph traversal | Relationships | Objects |
| **Knowledge** | Validation, storage, retrieval | Knowledge | Evidence + Relationships |
| **Reasoning** | Derivation, calibration | Reasoning traces | Knowledge |
| **Prediction** | Future state estimation | Predictions | Reasoning |
| **Execution** | Action performance | Execution results | Predictions |
| **Workspace** | Projection to founder | Projections | All layers |

### 20.4 Violation consequences

| Violation | Consequence | Recovery |
|-----------|------------|----------|
| Layer skipped | Data lacks provenance | Trace back to nearest upstream layer |
| Flow reversed | Workspace corrupts cognition | Reject, log, alert |
| Evidence bypassed | Knowledge is unfounded | Demote to belief |
| Relationship bypassed | Object is isolated | Flag for relationship discovery |
| Knowledge bypassed | Prediction is unsupported | Reduce confidence to 0.3 |

---

## Appendix A: Ontology Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           UNIVERSAL ONTOLOGY MAP                              │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │  OBJECT (root)                                                        │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │   │
│  │  │ENTITY │ │RELAT.│ │EVENT │ │COMMIT│ │ACTION│ │EVID. │ │KNOWL.│   │   │
│  │  ├──────┤ ├──────┤ ├──────┤ ├──────┤ ├──────┤ ├──────┤ ├──────┤   │   │
│  │  │Person│ │Empl. │ │Create│ │Prom. │ │Task  │ │Obs.  │ │Fact  │   │   │
│  │  │Org   │ │Own.  │ │Mod.  │ │Oblig.│ │Exec. │ │Verif.│ │Inf.  │   │   │
│  │  │Doc   │ │Memb. │ │Comm. │ │Agree │ │Oper. │ │Source│ │Rule  │   │   │
│  │  │Meet. │ │Contr.│ │Dec.  │ │Deadl.│ │Wflow │ │      │ │Pat.  │   │   │
│  │  │Proj. │ │Social│ │Exec. │ │      │ │      │ │      │ │      │   │   │
│  │  │Work. │ │      │ │Fail  │ │      │ │      │ │      │ │      │   │   │
│  │  │      │ │      │ │Res.  │ │      │ │      │ │      │ │      │   │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │   │
│  │                                                                       │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │   │
│  │  │PRED. │ │POLICY│ │CONV. │ │MEMORY│ │STATE │ │CONTXT│             │   │
│  │  ├──────┤ ├──────┤ ├──────┤ ├──────┤ ├──────┤ ├──────┤             │   │
│  │  │Fore. │ │Const.│ │Msg   │ │Work. │ │Active│ │Work. │             │   │
│  │  │Risk  │ │Run.  │ │Thr.  │ │Conv. │ │Inact.│ │Exec. │             │   │
│  │  │Opp.  │ │Bus.  │ │Trans.│ │Relat.│ │Term. │ │Temp. │             │   │
│  │  │Trend │ │Pers. │ │      │ │Knowl.│ │Error │ │Org.  │             │   │
│  │  │      │ │      │ │      │ │Hist. │ │Trans.│ │      │             │   │
│  │  │      │ │      │ │      │ │Const.│ │      │ │      │             │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘             │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Appendix B: Glossary

| Term | Definition | Defined in § |
|------|------------|-------------|
| **Action** | Discrete, indivisible unit of work | 10 |
| **Alias** | Alternative name for the same Entity | 2 |
| **Attribute** | A property of an Object | 4 |
| **Commitment** | An obligation between parties | 9 |
| **Composite Entity** | Entity composed of other Entities | 2 |
| **Context** | Circumstances surrounding an Object, Event, or Interaction | 13 |
| **Duplicate** | Object incorrectly representing the same Entity as another | 2 |
| **Entity** | Object representing a distinct real-world thing | 2 |
| **Event** | Something that changes reality | 8 |
| **Evidence** | Verified observation placed in context | 7 |
| **Identity** | Permanent, unique, non-reusable designation | 3 |
| **Knowledge** | Validated, structured, evidence-backed understanding | 14 |
| **Memory** | Storage and retrieval system for knowledge and experience | 17 |
| **Object** | The fundamental unit of reality inside SHUNYA | 1 |
| **Observation** | The atomic unit of learning | 6 |
| **Policy** | A rule that governs behaviour | 16 |
| **Prediction** | An estimate of a future state or outcome | 15 |
| **Relationship** | A connection between two Objects | 5 |
| **Representation** | A specific view or projection of an Entity | 2 |
| **State** | The current condition of an Object within its lifecycle | 11 |
| **Timeline** | The chronological record of all events involving an Object | 12 |
| **Virtual Entity** | Entity that exists only within SHUNYA's model | 2 |

## Appendix C: Cross-References

| Document | How this ontology is referenced |
|----------|--------------------------------|
| Founder Workspace Specification | The workspace projects Objects defined here |
| Cognitive Workspace Runtime | Attention Engine operates on Objects, Memory stores Knowledge |
| Adaptive Intelligence Runtime | Learning Engine promotes Observations to Knowledge |
| ES-002 (Knowledge Engine) | Knowledge lifecycle conforms to §14 definitions |
| ES-005 (Executor Engine) | Actions, Executions, Workflows conform to §10 definitions |
| ES-006 (Observer Engine) | Observations conform to §6 definitions |
| ES-007 (Learning Engine) | Learning stages map to §6 — §14 promotion path |
|| SHUNYA Core Models | Identity Model, Evidence Model, Confidence Model expand on §3, §7, and §14.3 |

---

## Appendix D: Canonical Vocabulary

### Canonical terms and aliases

Every concept in SHUNYA has exactly one canonical term. All other terms are aliases and must reference the canonical term.

| Canonical term | Aliases | Deprecated terms | Defined in |
|----------------|---------|------------------|------------|
| **Object** | Node (Knowledge Graph), Record | — | §1 |
| **Entity** | — | — | §2 |
| **Identity** | — | — | §3 |
| **Attribute** | Property, Field | — | §4 |
| **Relationship** | Edge (Knowledge Graph), Connection, Link | — | §5 |
| **Observation** | Raw data point, Signal | — | §6 |
| **Evidence** | — | — | §7 |
| **Event** | — | — | §8 |
| **Commitment** | Obligation, Agreement | — | §9 |
| **Action** | — | — | §10 |
| **Task** | ToDo, Assignment | — | §10 |
| **Execution** | Run, Operation instance | — | §10 |
| **Workflow** | Process, Pipeline | — | §10 |
| **State** | Status | — | §11 |
| **Timeline** | History, Chronology | — | §12 |
| **Context** | — | — | §13 |
| **Knowledge** | — | — | §14 |
| **Information** | — | Structured data (distinct from Knowledge) | §14 |
| **Understanding** | — | — | §14 |
| **Reasoning** | — | — | §14 |
| **Wisdom** | — | — | §14 |
| **Prediction** | Forecast, Projection | — | §15 |
| **Policy** | Rule, Regulation | — | §16 |
| **Memory** | — | — | §17 |
| **Projection** | View Model, Workspace Projection | — | CWR §3 |
| **Attention** | Focus | — | CWR §2 |
| **Intent** | — | — | CWR §4 |
| **Confidence** | Certainty score | — | Adaptive §2 |
| **Calibration** | — | — | Adaptive §6 |
| **Governance** | — | — | Adaptive §13 |

### Vocabulary rules

1. Every document must use the canonical term. Aliases may be used in implementation code but must be documented.
2. No document may introduce a new term for a concept that already has a canonical term.
3. Deprecated terms must not appear in new documents.
4. The canonical glossary is owned by UNIVERSAL_ONTOLOGY.md.

---

## Appendix E: Ownership Matrix

### Constitutional ownership

Every constitutional concern has exactly one owner. No concern may be owned by multiple documents.

| Concern | Owner | Rationale | Other documents that reference |
|---------|-------|-----------|-------------------------------|
| **Identity** | UNIVERSAL_ONTOLOGY.md §3 | Identity is a fundamental concept. Defines what identity IS. | CWR (§1.4), KG (§1.4) |
| **Memory** | UNIVERSAL_ONTOLOGY.md §17 | Memory is a constitutional concept. Defines the hierarchy and layers. | CWR (§5 — runtime promotion), Adaptive (§10 — promotion rules) |
| **Object** | UNIVERSAL_ONTOLOGY.md §1 | Object is the root of the type system. | CWR (§6 — lifecycle), KG (§1 — nodes) |
| **Relationship** | UNIVERSAL_ONTOLOGY.md §5 | Relationship is a fundamental structure. | CWR (§2 — attention), KG (§3 — edges) |
| **Evidence** | UNIVERSAL_ONTOLOGY.md §7 | Evidence is the foundation of all knowledge. | CWR (§1.5), KG (§4 — evidence graph), Adaptive (§12) |
| **Event** | UNIVERSAL_ONTOLOGY.md §8 | Events are the atomic units of change. | CWR (§9 — event bus), KG (§10 — graph events) |
| **Context** | UNIVERSAL_ONTOLOGY.md §13 | Context determines meaning. | CWR (§8 — context transition), KG (§6 — context resolution) |
| **Knowledge** | UNIVERSAL_ONTOLOGY.md §14 | Knowledge is the constitutional definition. | Adaptive (§5 — evolution), KG (§2 — node family) |
| **Prediction** | UNIVERSAL_ONTOLOGY.md §15 | Prediction is a constitutional object. | Adaptive (§3 — evolution), KG (§2 — node family) |
| **Policy** | UNIVERSAL_ONTOLOGY.md §16 | Policy governs behaviour. | Adaptive (§7 — evolution) |
| **State** | UNIVERSAL_ONTOLOGY.md §11 | State is universal across all Objects. | CWR (§6 — lifecycle) |
| **Timeline** | UNIVERSAL_ONTOLOGY.md §12 | Timeline is universal across all Objects. | KG (§5 — temporal graph) |
| **Action** | UNIVERSAL_ONTOLOGY.md §10 | Action is a constitutional object. | Adaptive (§4 — execution learning) |
| **Commitment** | UNIVERSAL_ONTOLOGY.md §9 | Commitment is a constitutional object. | KG (§2 — node family) |
| **Attention** | COGNITIVE_WORKSPACE_RUNTIME.md §2 | Attention is a cognitive concept. Determines focus. | — |
| **Projection** | COGNITIVE_WORKSPACE_RUNTIME.md §3 | Projection is the bridge between cognition and UI. | KG (§8 — graph projections) |
| **Intent Pipeline** | COGNITIVE_WORKSPACE_RUNTIME.md §4 | Intent Pipeline is the single path for founder intent. | — |
| **Event Bus** | COGNITIVE_WORKSPACE_RUNTIME.md §9 | Event Bus is the nervous system of the runtime. | KG (§10 — graph events) |
| **Confidence** | ADAPTIVE_INTELLIGENCE_RUNTIME.md §2 | Confidence is an adaptive concept. Governs scoring. | KG (§1.9), Ontology (§14.3) |
| **Learning** | ADAPTIVE_INTELLIGENCE_RUNTIME.md §1 | Learning is the process of improvement. | — |
| **Calibration** | ADAPTIVE_INTELLIGENCE_RUNTIME.md §6 | Calibration ensures reasoning quality. | — |
| **Governance** | ADAPTIVE_INTELLIGENCE_RUNTIME.md §13 | Governance ensures founder sovereignty. | — |
| **Evolution Timeline** | ADAPTIVE_INTELLIGENCE_RUNTIME.md §15 | Evolution defines how SHUNYA changes over time. | — |
| **Graph Architecture** | UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1 | Graph primitives, nodes, edges, identity. | Ontology (§1, §5) |
| **Graph Projections** | UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §8 | Projections from the graph to the workspace. | CWR (§3) |
| **Traversal** | UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §7 | Navigation strategies across the graph. | — |
| **Workspace Layout** | FOUNDER_WORKSPACE_SPECIFICATION.md §2 | The three-zone workspace layout. | CWR (§3) |
| **Universal Object Model** | FOUNDER_WORKSPACE_SPECIFICATION.md §3 | The workspace's object interface. | Ontology (§1) |

### Ownership rules

1. Every concern has exactly one owner.
2. The owner defines the concept. Other documents may reference but not redefine it.
3. If a concern is not listed, the UNIVERSAL_ONTOLOGY.md is the default owner.
4. Ownership disputes are resolved by the Governance Engine.