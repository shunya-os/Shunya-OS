# Shunya OS — Philosophy & Architecture Canon (LOCKED)
## July 11, 2026 — Derived from Hermes Master Build Directive

This document defines HOW Shunya thinks, decides, learns, and governs.
It is the architectural counterpart to SHUNYA_OS_ECOSYSTEM_PLAN.md (the module catalog).
Neither document is complete without the other.

---

## 1. CANONICAL DEFINITION

Shunya is a **Compounding Intelligence Operating System for Organizations**.

Not a chatbot.
Not a CRM.
Not an ERP.
Not a workflow automation tool.
Not a collection of AI agents.
Not a SaaS dashboard with AI features.

### The Core Intelligence Loop

```
KNOWLEDGE → CONTEXT → UNDERSTANDING → REASONING → DECISION
    ↓                                                    ↓
    ↓                                              PLAN
    ↓                                                    ↓
    ↓                                              WORKFLOW
    ↓                                                    ↓
    ↓                                              EXECUTION
    ↓                                                    ↓
    ↓                                              OBSERVATION
    ↓                                                    ↓
    ↓                                              LEARNING
    ↓                                                    ↓
    └────────────── BETTER KNOWLEDGE ←──────────────────┘
```

The purpose is not to automate human work. The purpose is to:

1. Understand what is happening
2. Understand what matters
3. Identify what requires a decision
4. Reason about available choices
5. Explain the recommendation
6. Help the authorized human decide
7. Convert the decision into a plan
8. Convert the plan into governed work
9. Execute approved actions
10. Observe the real result
11. Compare intention against outcome
12. Identify learning
13. Improve organizational knowledge
14. Make the next decision better

This is **Compounding Intelligence** — human intelligence + artificial intelligence +
organizational memory + observed outcomes compounding over time.

---

## 2. HUMAN + AI PHILOSOPHY

### Who Owns What

| Humans Own | Shunya Owns |
|-----------|-------------|
| Intent | Remembering |
| Purpose | Retrieving |
| Values | Connecting |
| Ambition | Comparing |
| Emotion | Contextualizing |
| Creativity | Reasoning |
| Accountability | Warning |
| Organizational Authority | Planning |
| | Orchestrating |
| | Observing |
| | Identifying Patterns |
| | Recommending Learning |

### Canonical Principle

**AI proposes. Humans dispose.**

Exception: A human or organizational policy may explicitly delegate authority to the system.

Therefore:

> AI PROPOSES. HUMANS DISPOSE.
> UNLESS GOVERNED AUTHORITY HAS BEEN EXPLICITLY DELEGATED.

### Augmentation-First

Shunya is augmentation-first. The system should make humans wiser.
Every meaningful interaction should leave the user with greater clarity than before.
Shunya must not create learned helplessness where employees blindly follow AI.
The system should progressively develop human judgment.

### The Silent Mentor

Shunya should not only complete work. It should develop the person doing the work.
Training should happen inside live work.

Before a sales call: "Three things matter in this conversation."
Before approving an expense: "This vendor's cost is 18% above the recent median."
Before sending a contract: "One clause differs from the approved template."
Before hiring: "The interview feedback contains conflicting evidence."

Tone: Never humiliating. Never accusatory. Never patronizing.
Preferred pattern:

1. "I noticed one detail that may need attention."
2. WHAT WAS OBSERVED
3. WHY IT MATTERS
4. WHAT CURRENT KNOWLEDGE OR POLICY SAYS
5. WHAT SHUNYA RECOMMENDS
6. WHAT THE USER CAN DO NEXT

---

## 3. DECISION-FIRST ARCHITECTURE

Most AI systems are conversation-first. A user asks a question, the AI generates text.

Shunya is **decision-first**. At every meaningful organizational moment, Shunya should be capable of answering:

| Question | Purpose |
|----------|---------|
| WHAT HAPPENED? | Situation awareness |
| WHAT DOES IT MEAN? | Context |
| WHAT MATTERS NOW? | Priority |
| IS THERE A RISK? | Risk awareness |
| IS A DECISION REQUIRED? | Decision trigger |
| WHAT ARE THE AVAILABLE OPTIONS? | Alternatives |
| WHAT ARE THE TRADE-OFFS? | Analysis |
| WHAT DO I RECOMMEND? | Recommendation |
| WHY DO I RECOMMEND IT? | Reasoning |
| HOW CONFIDENT AM I? | Confidence |
| WHAT EVIDENCE SUPPORTS IT? | Evidence |
| WHO HAS AUTHORITY? | Governance |
| WHAT SHOULD HAPPEN NEXT? | Next action |
| WHAT IS BLOCKING THE NEXT STEP? | Dependency |
| WHAT HAPPENS IF NOTHING IS DONE? | Risk of inaction |

This philosophy must influence the domain model, APIs, event architecture, and frontend.

---

## 4. NEVER LEAVE THE USER WONDERING

This is a canonical Shunya product principle. The system should continuously derive
**NEXT BEST ACTION**. A user should not need to inspect ten dashboards to determine
their priority.

Shunya should understand:
- Active goals
- Active workflows
- Current states
- Blockers
- Dependencies
- Deadlines
- Risk
- Authority
- Business impact
- Prior commitments
- Unresolved decisions

Every screen should answer: **What just happened? What should I do next? Why?**

---

## 5. ADAPTIVE INTELLIGENCE DEPTH

Shunya should not explain everything equally to everyone. The explanation depth
should adapt to the user's role and experience.

| User Type | Response Style |
|-----------|---------------|
| **New User** | Detailed guidance, definitions, reasoning, examples, warnings |
| **Experienced User** | Concise recommendation, relevant exception, material trade-off |
| **Expert User** | Anomaly, novel pattern, strategic implication |
| **Executive** | Business consequence, organizational pattern, decision requirement |

The same intelligence may be communicated differently based on role, authority,
experience, demonstrated skill, context, and urgency.

Do not build static one-size-fits-all AI responses.

---

## 6. ORGANIZATIONAL KNOWLEDGE SYSTEM

Knowledge is not a folder of documents. Shunya Knowledge understands different
knowledge classes with different authority levels.

### Knowledge Classes

| Class | Description | Authority |
|-------|-------------|-----------|
| **Authoritative Policy** | Formally approved organizational rule | 🔴 Highest |
| **Operational Fact** | Currently known business fact | 🟡 Medium |
| **Domain Knowledge** | Knowledge about the organization's industry | 🟡 Medium |
| **User Preference** | A person's stated preference | 🟢 Low |
| **Observation** | Something observed by the system | 🟢 Low |
| **Inference** | A conclusion derived from evidence | 🟢 Low |
| **Learned Pattern** | Repeated relationship from outcomes | 🟠 Variable |
| **Experimental Hypothesis** | Pattern not yet at sufficient confidence | ⚪ Lowest |

### Knowledge Provenance

Every knowledge entry should carry where appropriate:
- Source
- Author
- Authority class
- Creation time
- Effective time
- Expiration
- Supersession
- Confidence
- Evidence
- Version
- Applicable context

### Knowledge Rules

- A learned pattern cannot silently override company policy
- A user preference cannot override a legal control
- An inference cannot masquerade as a verified fact
- Knowledge should be correctable
- Knowledge should be historically traceable
- Knowledge should support supersession

---

## 7. CONTEXT ENGINE

Raw knowledge is not enough. Shunya needs scoped context.

Context answers:
- WHAT ORGANIZATION?
- WHAT USER?
- WHAT ROLE?
- WHAT OBJECT?
- WHAT GOAL?
- WHAT PROCESS?
- WHAT STATE?
- WHAT HAPPENED RECENTLY?
- WHAT DECISIONS ALREADY EXIST?
- WHAT POLICY APPLIES?
- WHAT AUTHORITY DOES THIS USER HAVE?
- WHAT DEADLINE EXISTS?
- WHAT RISK EXISTS?
- WHAT PRIOR OUTCOMES ARE RELEVANT?

### Least-Context Principle

Do not give every AI component unrestricted access to every organizational secret.
Context should be scoped. Reasoning needs decision context — not passwords, payment
secrets, unrestricted credentials, or all employee records.

Apply **least-context principles** where appropriate.

---

## 8. REASONING ENGINE

### Consumes
- Goal
- Facts
- Relevant knowledge
- Context
- Constraints
- Policy
- Evidence

### Produces
A structured **Decision** or **Recommendation** containing:
- id
- subject
- outcome
- recommendation
- confidence
- explanation
- evidence
- alternatives
- trade-offs
- risks
- assumptions
- constraints
- policy references
- required authority
- timestamp
- reasoning version

### Fundamental Boundary

**Reasoning must NOT execute actions.**

Reasoning does not send an email.
Reasoning does not transfer money.
Reasoning does not modify the database as an operational side effect.

Reasoning reasons. This boundary is fundamental.

---

## 9. DECISION INTELLIGENCE

Shunya supports explicit organizational decisions across arbitrary businesses:

- Should this lead receive priority?
- Should we approve this discount?
- Which supplier should we choose?
- Should we hire this candidate?
- Is this project at risk?
- Should this expense be approved?
- Which customer requires intervention?
- Should inventory be reordered?
- Is this transaction anomalous?
- Should this issue be escalated?
- Which operational option is strongest?
- Is this policy exception justified?

### Decision Objects

Decision objects must remain inspectable. The system preserves:

WHAT WAS KNOWN → WHAT WAS RECOMMENDED → WHY → WHAT HUMAN DECIDED
→ WHAT WAS EXECUTED → WHAT ACTUALLY HAPPENED

This is necessary for compounding intelligence.

---

## 10. PLANNER

Planner converts a Decision or Goal into an Ordered Plan.

### What Planner Answers
- What steps are required?
- In what sequence?
- What dependencies exist?
- What prerequisites exist?
- What can happen in parallel?
- What requires approval?
- What should happen if a prerequisite changes?

### Constraints
- Plans should be understandable to humans
- Planner does NOT execute
- Planner creates the intended path
- If context changes, the system should identify that the plan may now be obsolete
- Do not blindly execute stale plans

---

## 11. WORKFLOW

Workflow converts plans into operational state.

### Represents
- Tasks
- States
- Dependencies
- Owners
- Deadlines
- Blockers
- Transitions
- Approvals
- Escalation conditions

### Task States

Possible task states include:
PENDING | READY | ACTIVE | BLOCKED | AWAITING_APPROVAL
COMPLETED | FAILED | CANCELLED

### Semantic Clarity

The system must distinguish:

**PENDING** from **BLOCKED** from **WAITING** from **FAILED** from **NOT YET ELIGIBLE**

Workflow should make explicit:
- WHAT IS PENDING
- WHAT IS READY
- WHAT IS ACTIVE
- WHAT IS BLOCKED
- WHY IT IS BLOCKED
- WHO OWNS IT
- WHAT DEPENDENCY IS MISSING
- WHAT SHOULD HAPPEN NEXT

---

## 12. DEPENDENCY INTELLIGENCE

Shunya should understand dependency causality.

Bad: "Task pending."

Shunya: "Task is blocked because Compliance Approval #81 is incomplete."
Then:
- Owner: Legal Team
- Business consequence: Customer onboarding cannot continue
- Deadline: 6 hours
- Recommended action: Request compliance review

---

## 13. EXECUTOR

Executor performs authorized actions through controlled adapters.

### Examples
- Send message
- Create record
- Update record
- Call API
- Create document
- Schedule event
- Invoke integration
- Execute internal tool
- Initiate approved external operation

### Architecture

```
Executor → Tool Registry → Adapter → External or Internal System
```

### Every Execution Knows

- WHAT IS BEING EXECUTED
- WHY
- WHICH PLAN
- WHICH WORKFLOW
- WHICH TASK
- WHICH DECISION
- WHO AUTHORIZED IT
- WHICH POLICY ALLOWS IT
- WHICH TOOL IS USED
- WHAT INPUT WAS PROVIDED
- WHAT RESULT WAS RETURNED

**The Reasoning engine must not secretly become Executor.**

---

## 14. AUTHORITY & GOVERNANCE

Shunya must be governed by architecture, not by AI prompts saying "Do not do dangerous things."

### Authority Check Chain

```
INTENT → REASONING → PLAN → WORKFLOW
→ AUTHORITY CHECK → POLICY CHECK → APPROVAL CHECK
→ EXECUTOR → ADAPTER
```

### Architectural Separation Principle

No single component should independently own:
KNOWLEDGE + DECISION + AUTHORITY + EXECUTION

This separation is one of Shunya's architectural security principles.

### Security Goals

- **Compromise Containment** — If Reasoning is manipulated, it should not automatically possess execution authority
- **Least Privilege** — Every component has minimum necessary access
- **Explicit Authority** — No implicit trust between layers
- **Traceability** — Every action is linked to its authorization chain
- **Blast-Radius Reduction** — If one adapter is compromised, the system remains functional

### Checking Before Execution

A system action should be checked against:
- Identity
- Role
- Permission
- Policy
- Workflow state
- Required approval
- Execution scope
- Tool capability
- Potentially: Risk level

---

## 15. OBSERVER

Executor reports what it attempted. Observer records what actually happened.
These are different.

### Observation Examples

| Intent | Execution | Observation |
|--------|-----------|-------------|
| Send proposal | Email API accepted request | Email delivered |
| Send proposal | Email API accepted request | Customer opened email |
| Send proposal | Email API accepted request | Customer replied |
| Send proposal | Email API accepted request | Opportunity converted |

**Do not treat "API returned 200" as "Business outcome succeeded."**

### Observation Types
- State changed
- Message delivered
- User responded
- Deadline missed
- Transaction completed / failed
- Customer churned
- Project delayed
- Employee corrected AI
- Approval rejected
- Recommendation ignored
- Target achieved

Every execution should create an observation opportunity.

---

## 16. OUTCOME INTELLIGENCE

Shunya must compare INTENDED OUTCOME against ACTUAL OUTCOME.

### Example

| Case | Decision | Plan | Execution | Intended | Actual |
|------|----------|------|-----------|----------|--------|
| Good | Prioritize Lead A | Contact within 10 min | Call completed | Lead converts | ✅ Converted |
| Bad | Same | Same | Call completed | Lead converts | ❌ Lost |

### What Differed?

Possible causes:
- Timing
- Context
- Communication
- Pricing
- Customer intent
- External condition
- Incorrect assumption

This is where the system moves beyond workflow automation.

---

## 17. LEARNING

### What Learning Consumes

Decisions, plans, executions, observations, outcomes, corrections.

### What Learning Identifies

- Repeated patterns
- Anomalies
- Successful approaches
- Failed approaches
- Stale knowledge
- Skill gaps
- Process bottlenecks
- Policy friction
- Prediction errors

### Learning Proposals

Learning produces structured proposals, not silent rewrites:

```
PATTERN DETECTED
Opportunities contacted within 15 minutes convert 22% better in Segment B.
Evidence: 312 opportunities.
Confidence: 87%.
Recommended knowledge update: Prioritize first response under 15 minutes for Segment B.
```

### The Learning Loop

```
OBSERVATION → PATTERN → LEARNING PROPOSAL → GOVERNANCE → KNOWLEDGE UPDATE
```

The system should NOT silently rewrite authoritative organizational truth.
Learning proposes. Governance evaluates. Authorized humans approve, reject, or
request more evidence. Approved learning may become governed knowledge.

---

## 18. MEMORY ARCHITECTURE

Memory should not be one giant vector database. Design memory in classes.

### Memory Categories

| Class | Description |
|-------|-------------|
| **Working Memory** | Immediate reasoning context |
| **Episodic Memory** | What happened in a specific event or interaction |
| **Semantic Memory** | Known organizational concepts and facts |
| **Procedural Memory** | How the organization performs work |
| **Relationship Memory** | Relevant history about an entity or relationship |
| **Decision Memory** | Past decisions and their reasoning |
| **Outcome Memory** | What happened after decisions |
| **Learning Memory** | Approved organizational learning |

### Memory Properties
- Relevance
- Provenance
- Access control
- Retention rules
- Correction
- Confidence where applicable

Semantic search is a retrieval mechanism. It is not the entire memory architecture.

---

## 19. PROACTIVE INTELLIGENCE

Shunya should eventually operate before a human asks a question.

### Examples
- "I noticed something."
- "Three workflows are repeatedly failing at the same approval step."
- "Customer churn increased in one segment."
- "Supplier costs are rising faster than revenue."
- "Project risk increased because two critical dependencies slipped."
- "An unusual financial pattern requires review."

### Requirements

Proactive intelligence must be:
- **Relevant** — to the user's role and current work
- **Explainable** — why this matters now
- **Role-Aware** — different insights for different roles
- **Prioritized** — not everything is important
- **Non-Spammy** — materiality matters

Shunya must not become a notification machine.

---

## 20. ROLE-AWARE INTELLIGENCE

The same organizational event should produce different intelligence for different roles.

### Example: Project deadline slips

| Role | Intelligence |
|------|-------------|
| Employee | "Task X is now your highest priority." |
| Manager | "Three tasks are blocked because Task X slipped." |
| Finance | "The delay may move ₹18 lakh revenue into next month." |
| CEO | "Project delivery risk increased from Medium to High." |

The frontend should not simply hide menu items based on role.
The intelligence itself should be role-aware.

---

## 21. NEXT BEST ACTION ENGINE

Build toward a generalized priority engine.

### Potential Inputs
- Urgency
- Impact
- Risk
- Deadline
- Workflow state
- Dependency count
- Financial consequence
- Customer consequence
- Strategic importance
- Authority
- Confidence
- Time sensitivity

### Architecture

```
Candidate Actions → Context → Priority Evaluation → Explanation → Next Best Action
```

### Output Contains
- ACTION
- WHY NOW
- EXPECTED IMPACT
- RISK OF DELAY
- CONFIDENCE
- REQUIRED AUTHORITY
- RELATED OBJECT

The scoring model may evolve. Design interfaces that allow priority strategies to evolve.

---

## 22. COMMUNICATION INTELLIGENCE

Shunya should help organizations communicate with context.

### Channel Types
- Email
- Internal messaging
- Customer messaging
- Notification
- Report
- Briefing

### Communication Types
- INFORM
- REQUEST
- WARN
- ESCALATE
- EXPLAIN
- APOLOGIZE
- RECOMMEND
- CONFIRM

### Grounding
Communication should be grounded in: organization tone, recipient, relationship,
active workflow, relevant history, decision state.

Communication generation should not be a disconnected generic LLM call.

---

## 23. NOTIFICATION PHILOSOPHY

Notifications should be **decision-aware**.

Bad: "Task overdue."

Shunya: "Supplier approval is 3 hours overdue. This is blocking 4 downstream tasks.
Customer delivery may slip tomorrow. Recommended action: Escalate to Operations Manager."

Every meaningful notification should answer:
- WHAT HAPPENED
- WHY IT MATTERS
- WHAT TO DO NEXT

### Notification Levels
- INFORMATION
- GUIDANCE
- ATTENTION
- WARNING
- CRITICAL
- APPROVAL REQUIRED

Do not turn Shunya into a noisy notification feed. Materiality matters.

---

## 24. MULTI-AGENT ARCHITECTURE

Do not rush into agents. The system may eventually have specialist agents, but
agents must not become independent uncontrolled AI silos.

### Potential Specialist Agents
- Sales Intelligence Agent
- Finance Intelligence Agent
- Operations Intelligence Agent
- Risk Agent
- Knowledge Agent
- People Intelligence Agent
- Customer Intelligence Agent

### Architecture

```
SHUNYA ORCHESTRATOR
→ SPECIALIST CAPABILITY
→ STRUCTURED RESULT
→ GOVERNANCE
→ WORKFLOW
→ CONTROLLED EXECUTION
```

### Agent Constraints
- Scoped context
- Defined capabilities
- Limited tools
- Explicit authority
- Traceable output

An agent is a reasoning specialization. It is not automatically an authority.

---

## 25. FRONTEND PHILOSOPHY

### Home Experience

Do not imagine Shunya as a wall of dashboards. The home experience should
begin with context.

```
Good morning.
Here is what changed.
3 things require your attention.

1. Critical customer risk.
2. Workflow bottleneck.
3. Approval awaiting your authority.

Recommended first action: Review Customer Risk #82.
```

### Natural Language + Structured UI

Natural language and structured UI must coexist. A user should be able to ask:
- "What needs my attention?"
- "Why is this blocked?"
- "What changed?"
- "What should I do?"
- "Why do you recommend this?"
- "Show me the evidence."
- "What happens if I delay?"
- "Have we seen this before?"
- "What did we learn?"

The response should link directly to the relevant structured object.
Conversation should be able to become structured action when authorized.

---

## 26. EVENT ARCHITECTURE

Build toward event awareness. Domain-neutral Shunya core should use
generalized event contracts.

### Event Examples
- LeadCreated
- TaskBlocked
- ApprovalRequested
- PaymentReceived
- WorkflowCompleted
- ExecutionFailed
- CustomerResponded
- DeadlineMissed
- DecisionOverridden
- ObservationRecorded

### Event Triggers
Events may trigger: context refresh, reasoning, risk evaluation, workflow
transition, notification, observation, learning opportunity.

Do not build an uncontrolled event spaghetti architecture.
Event contracts should be explicit and typed.

---

## 27. SYSTEM SELF-UNDERSTANDING (DOCTOR)

The existing Doctor concept is important. Shunya should eventually understand:
- Installed capabilities
- Package health
- Knowledge health
- Policy health
- Adapter health
- Configuration health

Doctor is not merely a CLI utility. It is the beginning of system introspection.

Shunya should be capable of answering: "What can I currently do?
What is the health of each capability? What is NOT working?"

---

## 28. BUILD ORDER

The agreed engineering direction is:

1. ✅ FINISH WORKFLOW (core workflow engine with semantic clarity)
2. 🔲 BUILD EXECUTOR (controlled adapters with full traceability)
3. 🔲 BUILD OBSERVER (outcome intelligence, not just execution logging)
4. 🔲 COMPLETE THE FIRST CLOSED INTELLIGENCE LOOP
5. 🔲 MEMORY (multi-class memory architecture)
6. 🔲 LEARNING (structured proposals with governance)
7. 🔲 ORCHESTRATION (multi-agent coordination)

---

## 29. LONG-TERM PLATFORM DIRECTION

### TypeScript Monorepo

The long-term platform direction is a TypeScript monorepo with:
- pnpm
- Turborepo
- Vitest
- @shunya/foundation → @shunya/governance → @shunya/knowledge → @shunya/runtime
  → @shunya/reasoning → @shunya/planner → @shunya/workflow → @shunya/doctor → @shunya/cli

### Current Python/Flask Codebase

The current Python/Flask codebase is a **pragmatic prototype** — sufficient for
proving the model, testing the intelligence loop, and serving the first body
(Panchi Club). The TypeScript migration should be handled as a deliberate
platform build pack rather than repeatedly interrupting development.

### Domain Neutrality

**Keep core Shunya domain-neutral.** Travel-specific concepts must not leak into
generic Shunya core packages unless intentionally abstracted.

Panchi Club is the first body/application. Shunya is the brain.
Future bodies may exist in other industries.

---

## 30. CORE EVENT CONTRACTS (Standardized)

Domain-neutral events that the Shunya core publishes and consumes:

| Event | Payload | Triggered By |
|-------|---------|-------------|
| EntityCreated | {tenant_id, entity_type, entity_id, code} | Entity creation |
| EntityUpdated | {tenant_id, entity_type, entity_id, changed_fields} | Entity update |
| EntityStatusChanged | {tenant_id, entity_type, entity_id, from_status, to_status} | Status transition |
| TaskBlocked | {task_id, workflow_id, dependency_id, reason} | Dependency detection |
| ApprovalRequested | {approval_id, entity_id, requested_by, authority} | Workflow trigger |
| PaymentReceived | {payment_id, entity_id, amount, gateway} | Payment webhook |
| WorkflowCompleted | {workflow_id, plan_id, entity_id, outcome} | Final state reached |
| DecisionMade | {decision_id, subject, outcome, authorized_by} | Human decision |
| DeadlineMissed | {entity_id, task_id, deadline, consequence} | Time-based trigger |
| ObservationRecorded | {observation_id, execution_id, outcome} | Observer layer |
| LearningProposed | {proposal_id, pattern, confidence, evidence} | Learning engine |
| AnomalyDetected | {entity_id, metric, expected, actual, severity} | Monitoring |

---

## 31. CUSTOMER RELATIONSHIP ARCHITECTURE

### The Fundamental Distinction

**A customer is not a transaction. A booking is one episode in a lifetime relationship.**

This distinction is architectural — it changes the data model, memory architecture,
reasoning context, and entire CRM philosophy.

### Canonical Principles

| Principle | Statement |
|-----------|-----------|
| **Customer Permanence** | The Customer is permanent. A booking is temporary. An opportunity has a lifecycle. A customer relationship is continuous. |
| **Relationship > Transaction** | The system does not manage bookings. It compounds relationships. |
| **Institutional Memory** | The customer should feel "Panchi Club remembers me," not "Nishesh remembers me." Organizational memory survives employee boundaries. |
| **Memory with Evidence** | Preferences are stored with evidence, confidence, and source — not as unchecked JSONB data. The system distinguishes observation from inference. |
| **Operationally Opportunity-Centric** | Work happens against an Opportunity (current intent), not directly against the Customer. |
| **Relationally Customer-Centric** | Memory lives on the Customer. One customer can have many opportunities over time. The relationship does not close when the booking closes. |

### The Customer Model

```
CUSTOMER (first-class model, not an Entity)
│
├── Relationship metadata (tenure, health, advisor)
├── Traveller Graph (self, spouse, child, parent, company)
├── Preferences (with evidence, confidence, sources)
├── Decision Patterns
├── Communication History
├── Trust History
│
├── Opportunity 001 (Japan Holiday)
│   ├── Enquiry
│   ├── Decisions
│   ├── Quote
│   ├── Booking (commercial commitment)
│   ├── Experience (delivered journey)
│   └── Outcome (what happened, feedback, lessons)
│
├── Opportunity 002 (Dubai Trip)
│   └── ...
│
└── Opportunity 003 (Parents' Europe)
    └── ...
```

### Why Customer Is Not an Entity Type

The generic Entity engine (Entity + EntityDefinition) is designed for operational
modules: HR employees, marketing campaigns, support tickets. These have standard
lifecycles, status flows, and JSONB data.

The Customer is fundamentally different:

1. **Customer carries lifetime relationship memory** — preferences with evidence,
   communication history across years, trust trajectory. This is not temporary data.

2. **Customer has a traveller graph** — the person paying, enquiring, deciding,
   and travelling may all be different people. One person may hold multiple roles
   (customer, contact, traveller, decision maker, payer, beneficiary, referrer).

3. **Customer preferences require provenance** — the system must distinguish:
   - "Observed: Nishesh selected central hotels in 3 of 4 completed trips"
   - "Inferred: Nishesh prefers central locations"
   - "Stated: Nishesh said 'I like walkable areas'"

4. **Customer memory compounds over years** — the value of the relationship
   increases every time the customer engages. After 10 years, the system
   understands decision behaviour, not just preferences.

### The Opportunity Lifecycle

An Opportunity is NOT an Entity. It has a dedicated model with a defined lifecycle:

```
ENQUIRY → DISCOVERY → PLANNING → PROPOSAL → NEGOTIATION
→ BOOKING → EXPERIENCE → OUTCOME → CLOSED
         ↘ LOST at any stage
```

| Stage | Meaning |
|-------|---------|
| **Enquiry** | Customer expressed interest. Intent detected but unqualified. |
| **Discovery** | Understanding customer's actual need. Destination, dates, budget, travellers, pace. |
| **Planning** | Itinerary being built. Supplier coordination, availability checks. |
| **Proposal** | Quote/Itinerary shared with customer. Awaiting decision. |
| **Negotiation** | Active back-and-forth on price, dates, inclusions. |
| **Booking** | Commercial commitment made. Payments, confirmations, tickets. |
| **Experience** | Customer is travelling. Real-time support window. |
| **Outcome** | Trip completed. Feedback, lessons, relationship update. |
| **Closed** | Finalised. Knowledge extracted. Memory updated. |

### Why Opportunity Is Not an Entity

1. **Opportunity has a lifecycle that spans the reasoning loop** — decisions,
   plans, workflows, executions, and outcomes all orbit the Opportunity.

2. **One customer can have simultaneous Opportunities** — personal holiday,
   parents' pilgrimage, corporate offsite, destination wedding. If these were
   Entity types, context would be polluted across them.

3. **Opportunity is the unit of compounding intelligence** — the system learns
   from the gap between PLAN and OUTCOME on each opportunity. This is how
   decision behaviour is understood.

### The Relationship Brief

This is the frontend consequence of lifetime customer architecture.

When an employee opens a customer, the screen should not show a traditional CRM
header (Phone, Email, Lead Source, Last Booking, Total Revenue). It should show:

```
Nishesh Singhal

Relationship with Panchi Club: 6 years · 8 experiences · 3 referrals
Relationship Advisor: Mitesh Yadav
Relationship Health: Strong
Last meaningful interaction: 18 days ago

--- AI Relationship Brief ---

BEFORE YOU SPEAK:
• Prefers concise WhatsApp conversations
• Usually travels with family
• Avoids rushed itineraries
• Has previously rejected hotels far from city centre
• Responds better to 2 strong choices than 6 options
• Last trip had a transfer delay issue

ONE THING TO REMEMBER:
Do not recommend an early-morning departure without explaining airport timing.

--- Suggested Next Action ---
Customer asked about Japan 3 days ago.
Recommended: Have a discovery conversation before sending an itinerary.
Why: Previous trips show destination selection changes after discussing pace.
```

The Relationship Brief is AI-native relationship intelligence — it restores
relationship context to the employee's mind so they feel "I know this customer"
even if they have never spoken to them before.

### Preference Architecture

Preferences must carry:

```json
{
  "preference": "hotel_location",
  "value": "central_walkable",
  "confidence": "high",
  "evidence": [
    {"trip": "Thailand 2022", "action": "selected city centre hotel"},
    {"trip": "Dubai 2023", "action": "selected Downtown hotel"},
    {"trip": "Bali 2025", "action": "selected central Ubud location"}
  ],
  "source": "observed",
  "last_confirmed": "2026-03-15",
  "contradictions": [
    {"trip": "Parents' Europe 2024", "note": "selected outskirts — reason: budget"}
  ]
}
```

Principles:
- **Memory is stated, not assumed.** "Last time you preferred..." not "You always prefer..."
- **Preferences have confidence.** Low-confidence preferences should offer to confirm.
- **Preferences have evidence.** The system can explain WHY it believes something.
- **Preferences can contradict.** Humans change. Memory should support supersession.

### Traveller Roles

A customer may represent multiple people:

| Role | Meaning |
|------|---------|
| **Customer** | The relationship holder. May or may not travel. |
| **Contact** | Reachable person (may be different from customer). |
| **Decision Maker** | Person who makes the final call. |
| **Payer** | Person paying for the trip. |
| **Traveller** | Person actually travelling. |
| **Beneficiary** | Person the trip is for (gift, wedding, etc.). |
| **Referrer** | Person who referred the customer. |

One person may hold multiple roles. This is critical for weddings, MICE,
corporate travel, and family trips where the person enquiring, deciding,
paying, and travelling are different individuals.

### The Lifetime Journey

Not a transaction table. A visual relationship timeline:

```
2022  First enquiry ─→ Thailand honeymoon ✅ Travelled
2023  Dubai family holiday ✅ Travelled ⚠ Transfer issue observed
2024  Referred Sharma Family ✅ Converted
2025  Bali enquiry ❌ Did not travel (dates changed)
2026  Japan family holiday ● Active opportunity
```

The employee understands the story of the relationship, not just the last booking.

### The Compounding Moat

| After | Shunya Knows |
|-------|-------------|
| Booking 1 | Little |
| Booking 3 | Preferences |
| Booking 7 | Decision behaviour |
| 10 years | The relationship |

**Another company can offer the same hotel. Another OTA can offer the same flight.
But they cannot offer 10 years of governed relationship intelligence about how
this family makes travel decisions.**

### Customer-Facing Principle

When a customer returns after months, the system should not say:
"Hello! Where would you like to travel?"

Instead:
"Welcome back, Nishesh sir. Last time we planned Dubai around a comfortable
family pace. Are you imagining something similar this time, or do you want
this trip to feel completely different?"

That one sentence tells the customer: **They remember me.**

But always confirm rather than assume permanence:
"Last time you preferred..." not "You always prefer..."
Because humans change.

### Frontend Representation

The Customer screen should communicate:

1. **Relationship Header** — Who, tenure, health, advisor, last interaction
2. **AI Relationship Brief** — What the advisor needs before speaking
3. **Lifetime Journey** — Visual relationship timeline
4. **Traveller Graph** — All people in the customer's travel ecosystem
5. **Preferences with Evidence** — What we know, why, how confident
6. **Active Opportunities** — Current intents in play

The system is not showing data. It is restoring relationship context to the
employee's mind. This is how founder trust becomes institutional trust.


## 32. COROLLARY: DOMAIN MODEL GOVERNANCE

Generic Entity engine handles operational modules (HR, Marketing, Support,
Supply Chain, Legal, Field Services).

First-class models (Customer, Opportunity) handle relationship-centric and
lifecycle-centric domains.

Both coexist in the same tenant namespace. The distinction is architectural:

| Dimension | Entity Engine | First-Class Model |
|-----------|---------------|-------------------|
| Schema | Configurable at runtime | Fixed schema |
| Lifecycle | Status flow | Defined lifecycle stages |
| Memory | JSONB data | Structured preferences with evidence |
| Relationships | Generic | Typed (traveller_graph, decision_maker, etc.) |
| Intelligence | Module-specific | Cross-opportunity compounding |
| Time horizon | Transactional | Lifetime |


*This document is LOCKED as the architectural companion to SHUNYA_OS_ECOSYSTEM_PLAN.md.
No changes without explicit user direction.*