# SHUNYA Founder Experience Roadmap v1.0

> **Status: GOVERNING — This roadmap is the definitive execution plan for SHUNYA 1.0.**
> **Date: 2026-07-28**
> **Supersedes: MASTER_EXECUTION_ROADMAP_v1.0.md, shunya-production-roadmap.html, DNA-01.9-implementation-roadmap.md, 12_launch_roadmap.md**
> **Authority: Directive 04A — Founder Experience Roadmap (Final Refinement)**
> **Baseline: Constitutional Baseline v1.0 Frozen. Canonical Architecture Frozen. No architectural changes introduced.**

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Guiding Principle](#2-guiding-principle)
3. [Founder Experience Journey — The Story of SHUNYA](#3-founder-experience-journey)
4. [Final Milestone Sequence](#4-final-milestone-sequence)
5. [Milestone Deep-Dive](#5-milestone-deep-dive)
6. [Internal Engineering Work by Milestone](#6-internal-engineering-work-by-milestone)
7. [Dependency Graph](#7-dependency-graph)
8. [Acceptance Criteria & Demonstration Scenarios](#8-acceptance-criteria--demonstration-scenarios)
9. [Production Readiness Stages](#9-production-readiness-stages)
10. [Business Understanding Milestone — A Note](#10-business-understanding-milestone--a-note)
11. [Executive Home Placement — Rationale](#11-executive-home-placement--rationale)
12. [Applicable Roadmap Governance Rules](#12-applicable-roadmap-governance-rules)

---

## 1. Executive Summary

### 1.1 Current Reality

SHUNYA has all 8 intelligence engines built (Perception, Context Assembly, Reasoning, Planning, Decision, Reflection, Learning, Confidence). The Universal Object Protocol exists. The canonical pipeline is architected. The AI runtime runs, but the OS pipeline remains 80% mock — real engines exist but are not wired. The frontend shows beautiful demo data. The system works when observed in isolation but cannot yet be given to a founder as a daily tool.

**What a founder experiences today:** Sign up, log in, see a workspace with no real data, see no meaningful AI responses, see no connection to their actual business. SHUNYA is a collection of impressive technology that does nothing useful together.

**What a founder must experience at 1.0:** An AI Operating System that knows their business, answers their questions, creates and manages their objects, connects their tools, automates their workflows, learns from outcomes, and becomes more valuable every day.

### 1.2 Transformation Principle

This roadmap is the journey from technology to product. Every milestone is defined by a single question:

> **What can the founder accomplish after this milestone that was impossible before?**

Infrastructure appears only as the implementation required to achieve the experience. No milestone delivers only infrastructure.

### 1.3 Roadmap at a Glance

| # | Milestone | Founder Capability | Est. Duration | Foundational Work |
|---|-----------|-------------------|:-------------:|-------------------|
| 1 | **The OS Comes Alive** | Sign in and see the operating system process their actions through the canonical pipeline | 3-4 weeks | Wire kernel, identity, projection into pipeline; Flask routes through OS |
| 2 | **Executive Home — The Founder's Primary Surface** | See their entire business at a glance — real metrics, commitments, AI daily brief | 2-3 weeks | Executive Home dashboard, commitment tracker, AI brief component |
| 3 | **SHUNYA Knows Your Business** | SHUNYA understands people, customers, relationships, conversations, documents | 3-4 weeks | Wire memory/knowledge graph, planning runtime; business context assembly |
| 4 | **Create Any Business Object** | Define any entity type, create records, see them in list/kanban/calendar | 3-4 weeks | JSONB entity system, generic CRUD, list/detail/form/kanban views |
| 5 | **AI Copilot — Talk to Your OS** | Ask questions about their business in natural language, get real AI answers | 2-3 weeks | LLM provider layer, AI Copilot component, conversation workspace |
| 6 | **Connected Business** | Connect email and calendar, receive notifications, import existing data | 3-4 weeks | Integration runtime, email/calendar connectors, notification system |
| 7 | **Automation — SHUNYA Works for You** | Create "when X happens, do Y" rules, delegate work automatically | 3-4 weeks | Wire execution runtime, automation runtime, rule engine UI |
| 8 | **Executive Intelligence** | SHUNYA reasons, explains its reasoning, learns from outcomes, improves over time | 3-4 weeks | Wire reasoning runtime, learning loop, explainability traces |
| 9 | **Enterprise Ready** | Multi-tenant isolation, role-based access, immutable audit trail | 3-4 weeks | Tenant isolation, RBAC enforcement, immutable audit |
| 10 | **Production Launch** | Polished onboarding, first customer runs their business on SHUNYA | 2-3 weeks | Onboarding flow, security audit, CI/CD, monitoring, launch checklist |

**Total estimated duration: 27-38 weeks (6-9 months) with 5 parallel workstreams.**

---

## 2. Guiding Principle

This roadmap no longer answers:
> "What should engineers build next?"

It answers:
> **"What can the founder accomplish after each milestone that was impossible before?"**

Every milestone must satisfy the **User-Visible Value Test**:

1. **Produces a visible improvement** — The founder immediately sees something changed
2. **Produces a demonstrable capability** — A concrete new thing the founder can do
3. **Can be shown in a product demo** — A 5-minute demonstration proves it
4. **Can be tested by a founder without reading documentation** — Intuitive, discoverable
5. **Builds naturally upon the previous milestone** — No gaps in the journey

If a phase produces only infrastructure, it is merged into the nearest milestone that delivers visible value.

---

## 3. Founder Experience Journey — The Story of SHUNYA

This is the evolution of SHUNYA from the founder's perspective. It reads like the maturation of a living operating system.

### Week 0: Before the Roadmap

The founder signs up and sees a workspace. It looks professional. There are panels, navigation, a place for objects. But nothing has data. The AI responds with canned answers. It feels like a demo — because it is.

**The founder cannot yet:** Use SHUNYA for anything real.

---

### Milestone 1: The OS Comes Alive (Weeks 1-4)

**What the founder sees:** The login screen, the workspace — it looks the same as before. But now, when they create a space or an object, something different happens. There's a subtle indicator in the interface showing pipeline activity. Actions feel responsive because the canonical pipeline is processing every intent in real time.

**What the founder can do:**
- Sign in and see a workspace that acknowledges their existence
- Create and name a space
- Create objects within that space
- Open and view objects
- See a pipeline trace showing exactly how their action was processed
- Know that SHUNYA's operating system is alive and processing their actions

**What SHUNYA understands:**
- Who the founder is (identity resolved)
- What objects exist and their types
- Which spaces contain which objects
- That actions have been taken and recorded

**What the AI can now accomplish:**
- The OS pipeline processes real intents through real runtimes
- No mock data — every action creates real state
- The projection engine renders real OS data into workspace views

**Why this milestone matters:** Before this, SHUNYA was a demo. After this, SHUNYA is a running OS. Every subsequent capability depends on this foundation. The founder can trust that the system processes their actions, not just displays mock responses.

---

### Milestone 2: Executive Home — The Founder's Primary Surface (Weeks 4-7)

**What the founder sees:** Upon logging in, they no longer land on a generic workspace. They land on **Executive Home** — a dashboard that shows:
- A greeting with their name and organization
- Key metrics: spaces count, objects count, recent activity
- Open commitments and their status
- An AI-generated daily brief (even if brief) summarizing what happened
- Quick actions: create object, search, start conversation

**What the founder can do:**
- Log in and immediately understand the state of their business on SHUNYA
- See what's changed since their last login
- Click through to any object or space from the dashboard
- See commitments that need their attention
- Understand at a glance how SHUNYA is being used

**What SHUNYA understands:**
- What the founder considers important (commitments, frequent actions)
- The cadence of activity
- What needs attention and what doesn't

**What the AI can now accomplish:**
- Generate a daily brief from pipeline activity
- Identify commitments from actions
- Surface what changed since last login

**Why this milestone matters:** Executive Home becomes the founder's daily home. It transforms SHUNYA from "a tool I open when I need something" to "the place I start my day." The daily brief creates a relationship — SHUNYA begins to feel attentive.

---

### Milestone 3: SHUNYA Knows Your Business (Weeks 7-11)

**What the founder sees:** SHUNYA starts to feel like it knows who they work with. When they open an object, related people, companies, and past interactions appear in a context panel. The knowledge graph is visible — the founder can explore relationships between objects. Conversations are remembered. When the founder mentions "the Smith deal," SHUNYA knows what they're talking about.

**What the founder can do:**
- See who their business connects to (people, customers, suppliers, partners)
- Explore the relationship graph between objects
- See past conversations, emails, and documents linked to each object
- Have SHUNYA surface related information they might have forgotten
- Create commitments and see them tracked in context

**What SHUNYA understands:**
- **People** — who the founder works with, their roles, their connections
- **Customers** — the founder's customer base, relationships, history
- **Suppliers / partners** — external relationships
- **Organizations** — companies, teams, departments
- **Relationships** — who knows whom, what depends on what
- **Conversations** — what was discussed, decisions made, commitments created
- **Documents** — knowledge stored, references shared
- **Emails and meetings** — external communications in business context
- **Commitments** — promises made, deadlines, next actions
- **Timelines** — when things happened, sequences, dependencies

**What the AI can now accomplish:**
- Answer "What do I know about this person?" with actual context
- Surface related objects the founder might need
- Maintain coherent context across sessions
- Track commitments and their relationships to objects

**Why this milestone matters:** An AI Operating System that doesn't understand the founder's business is a generic tool. This milestone gives SHUNYA **context** — the difference between "a search engine for your data" and "an OS that understands your world." It enables everything that follows: AI responses that reference real people and real deals, automation that acts on real relationships, reasoning that considers real constraints.

---

### Milestone 4: Create Any Business Object (Weeks 11-15)

**What the founder sees:** A new "Entity Types" section in settings. Here, the founder can define any type of business object — Lead, Deal, Project, Invoice, Task, Client, Patient, Case, whatever their business uses. Each type can have custom fields with different types (text, number, date, select, relation). Once defined, they can create records of that type, see them in list, kanban, or calendar views, and click through to detail views with forms.

**What the founder can do:**
- Define a new entity type without writing code or requesting a schema change
- Create records of any defined type
- View records in a configurable list with sortable columns
- View records in a kanban pipeline organized by status
- View records on a calendar if they have date fields
- Open a detail view with auto-generated form
- Relate objects to each other
- Search across all entity types

**What SHUNYA understands:**
- The founder's information model — what kinds of things they track
- How each entity type relates to people, organizations, and other entities
- The pipeline state of each object (status, stage, lifecycle)

**What the AI can now accomplish:**
- Answer questions about specific entities with real field data
- Create new entities from natural language requests
- Navigate entity relationships

**Why this milestone matters:** This is where SHUNYA becomes useful for the founder's actual work. Before this, the founder could only interact with a fixed schema. After this, SHUNYA adapts to their business model — not the other way around. The entity system is the data foundation for every AI interaction.

---

### Milestone 5: AI Copilot — Talk to Your OS (Weeks 15-18)

**What the founder sees:** A persistent chat sidebar that follows them across the workspace. They can ask questions in natural language:
- "What's the status of the Smith deal?"
- "Show me all leads that haven't been contacted this week"
- "Summarize my meeting with Acme Corp"
- "What commitments do I have due this week?"
- "Create a new task for onboarding the Johnson account"

SHUNYA responds with accurate information from their actual data. Responses are grounded, explainable, and actionable.

**What the founder can do:**
- Ask questions about any entity, relationship, or commitment
- Get AI-generated summaries of objects, conversations, or dashboards
- Create objects, commitments, and tasks via conversation
- Navigate the system through natural language
- Have SHUNYA proactively suggest actions based on context

**What SHUNYA understands:**
- How to map natural language to pipeline intents
- Which data to retrieve for which question types
- How to generate accurate, grounded responses
- When to ask for clarification vs. when to answer

**What the AI can now accomplish:**
- Respond to arbitrary business questions from real data
- Generate contextual summaries
- Execute intents from natural language (create, update, search)
- Provide explainable responses with data provenance

**Why this milestone matters:** The Copilot makes SHUNYA accessible through natural language — the most intuitive interface. It transforms SHUNYA from "a tool you click through" to "a tool you talk to." It's the core differentiator that distinguishes an AI OS from a conventional CRM or ERP.

---

### Milestone 6: Connected Business (Weeks 18-22)

**What the founder sees:** A new "Integrations" section in settings. They can connect their email (Gmail, Outlook) and calendar. Emails automatically link to relevant objects (people, deals, projects). Calendar events appear in context. Notifications arrive in-app and by email when something changes — a commitment status updates, an entity is shared with them, an automation fires.

**What the founder can do:**
- Connect their email account via OAuth
- See emails linked to the objects they reference (people, deals, customers)
- Send emails from SHUNYA with context attached
- Connect their calendar and see events in context
- Receive notifications about important changes
- Import existing data via CSV with a column-mapping wizard

**What SHUNYA understands:**
- External communication patterns — who emails whom, how often, about what
- Calendar commitments — meetings, deadlines, events
- How external data maps to internal entities

**What the AI can now accomplish:**
- Answer "What did they say in the last email about this deal?" with real email content
- Suggest email responses based on conversation history
- Create calendar events from commitments
- Detect when an important email arrives and surface it

**Why this milestone matters:** A founder's business lives in their email and calendar. If SHUNYA doesn't connect to these, it's an island. This milestone makes SHUNYA the center of the founder's daily operations rather than yet another app to check.

---

### Milestone 7: Automation — SHUNYA Works for You (Weeks 22-26)

**What the founder sees:** A new "Automation" section where they can create rules:
- "When a lead status changes to 'Qualified,' notify the sales team"
- "When an invoice is overdue by 7 days, send a reminder email"
- "When a customer reaches 10 support tickets, escalate to senior team"
- "Every Monday at 9am, create a weekly summary task"

Rules fire automatically. The founder receives notifications when automation executes. A log shows every rule trigger and its outcome.

**What the founder can do:**
- Create if-this-then-that rules without code
- Choose from workflow templates
- See automation history and outcomes
- Pause, modify, or delete rules
- Delegate repetitive work to SHUNYA

**What SHUNYA understands:**
- Trigger conditions across entity lifecycle events
- Action sequences and their dependencies
- Which actions require human approval vs. auto-execute
- SLA breaches and escalation conditions

**What the AI can now accomplish:**
- Execute multi-step workflows autonomously
- Evaluate trigger conditions in real time
- Coordinate across entities, people, and external systems
- Report on automation outcomes

**Why this milestone matters:** Automation multiplies the founder's leverage. Before this, every action was manual. After this, routine work happens automatically. This is where SHUNYA transitions from "a tool that helps you work" to "a system that works for you."

---

### Milestone 8: Executive Intelligence (Weeks 26-30)

**What the founder sees:** SHUNYA's responses are now visibly smarter. It doesn't just retrieve data — it reasons about it. Every AI response includes an **explainability trace** showing how SHUNYA arrived at its conclusion. The system learns from outcomes: if the founder corrects SHUNYA, it remembers and improves. Confidence scores show how sure SHUNYA is about each response or suggestion.

**What the founder can do:**
- Ask "Why does SHUNYA think this deal is at risk?" and get a reasoned analysis
- See explainability traces for every AI action
- Correct SHUNYA's understanding and see it improve
- View confidence scores for predictions and recommendations
- Trust that SHUNYA's reasoning is transparent and verifiable

**What SHUNYA understands:**
- Risk patterns — which deals, customers, or projects need attention
- Outcome correlation — what actions lead to what results
- Confidence calibration — when to be certain and when to express uncertainty
- Learning from feedback — corrections improve future performance

**What the AI can now accomplish:**
- Perform reasoning across multiple data sources and relationships
- Generate explainable conclusions with confidence scores
- Learn from outcomes and improve predictions
- Provide traceable, auditable reasoning chains
- Detect anomalies and patterns the founder might miss

**Why this milestone matters:** Before this, SHUNYA could retrieve and organize information. After this, SHUNYA can think, explain, and learn. This is the difference between an AI that's a tool and an AI that's a partner. The founder can trust SHUNYA with increasingly complex decisions because every conclusion is transparent and improvable.

---

### Milestone 9: Enterprise Ready (Weeks 30-34)

**What the founder sees:** New sections for team management, roles, and audit. The founder can invite team members, assign roles (Admin, Member, Viewer, Custom), and see an immutable audit log of every action taken in the system. Every action has a complete trace: who did what, when, and through which pipeline stages.

**What the founder can do:**
- Invite team members to their organization
- Assign roles and permissions per entity type
- View the immutable audit trail
- Verify tenant isolation (their data is their data)
- Trust that SHUNYA meets enterprise compliance requirements

**What SHUNYA understands:**
- Organizational hierarchy — who has access to what
- Permission boundaries — which actions each role can perform
- Audit obligations — every action recorded immutably
- Tenant boundaries — absolute isolation between organizations

**What the AI can now accomplish:**
- Enforce permissions at every pipeline stage
- Produce immutable audit records for every action
- Operate in multi-tenant environments without data leakage
- Support enterprise compliance and governance requirements

**Why this milestone matters:** Without enterprise readiness, SHUNYA is a single-player tool. With it, SHUNYA becomes an organizational OS. The founder can now bring their team into the system, trust that data is secure, and meet compliance requirements for regulated industries.

---

### Milestone 10: Production Launch (Weeks 34-37)

**What the founder sees:** A polished, production-quality experience. Onboarding guides them from sign-up to first meaningful action in under 5 minutes. Error messages are human-readable. The system is fast, reliable, and monitored. SHUNYA is live at shunyaos.com and the first customer can sign up and run their business.

**What the founder can do:**
- Complete onboarding in under 5 minutes
- Invite their first customer to use SHUNYA
- Trust that the system is secure, backed up, and monitored
- Report issues through proper channels
- Expect SLAs on uptime and performance

**What SHUNYA understands:**
- First-run experience — it knows when a founder is new and guides them accordingly
- System health — it monitors itself and alerts when something is wrong
- Incident response — it knows how to fail gracefully and recover

**What the AI can now accomplish:**
- Guide new founders through their first actions
- Detect and report system health issues
- Degrade gracefully when subsystems are unavailable
- Provide human-readable error messages with recovery steps

**Why this milestone matters:** Everything before this built capability. This milestone makes SHUNYA a product. A founder can point someone at shunyaos.com and say "try this." The system is polished enough that the first experience is delightful, not confusing.

---

## 4. Final Milestone Sequence

### 4.1 The Ten Milestones

```
M1: The OS Comes Alive       ◄── Foundation. Pipeline is real. Processing actions.
M2: Executive Home           ◄── The daily surface. Dashboard with real data.
M3: SHUNYA Knows Your Biz    ◄── Business context. People, relationships, knowledge.
M4: Create Any Object        ◄── Entity system. Define and manage any record.
M5: AI Copilot               ◄── Natural language. Ask questions, get real answers.
M6: Connected Business       ◄── Email, calendar, notifications, import.
M7: Automation               ◄── Rules, workflows, delegation.
M8: Executive Intelligence   ◄── Reasoning, learning, explainability.
M9: Enterprise Ready         ◄── Multi-tenant, RBAC, audit, compliance.
M10: Production Launch       ◄── Onboarding, polish, beta, public launch.
```

### 4.2 Why This Sequence

The sequence is optimized for **founder value accumulation**, not engineering convenience:

1. **OS Comes Alive first** because nothing else works without a real pipeline. But it's only 3-4 weeks — the founder sees progress quickly.
2. **Executive Home second** because the founder needs a primary surface. Every subsequent milestone feeds data into this surface.
3. **Business Understanding third** because it provides context for everything that follows. AI Copilot is useless without business context. Automation is dangerous without understanding relationships.
4. **Entity System fourth** because the founder needs to input their data. Business understanding gives the OS framework; entity system gives the OS data.
5. **AI Copilot fifth** because now it has both context and data to work with.
6. **Connected Business sixth** because external integration requires understanding of internal objects and relationships.
7. **Automation seventh** because it requires execution runtime, entity understanding, and integration capabilities.
8. **Executive Intelligence eighth** because it requires all data, reasoning, and execution capabilities to learn from.
9. **Enterprise Ready ninth** because it's an overlay on all capabilities — doesn't add new founder features, enables organizational use.
10. **Production Launch last** because it's polish and scale on top of complete capabilities.

### 4.3 Rationale for Merges and Moves

| Change | Reason |
|--------|--------|
| **Merged:** Pipeline Activation + OS Foundation (from L-01 through L-04) | Pipeline wiring is invisible to the founder. It becomes visible only when actions process through it. Merging all pipeline wiring into one milestone creates a clean "the OS is alive" moment. |
| **Moved earlier:** Executive Home (was Phase 4 @ week 10, now M2 @ week 4-7) | The founder needs a primary daily surface from the beginning. Waiting 10 weeks for a dashboard means 10 weeks with no orientation. A basic Executive Home can be built as soon as the pipeline is real. |
| **Created:** SHUNYA Knows Your Business (was distributed across M-01, M-02, O-01) | Business understanding is the single most important AI capability for a founder. Scattering it across milestones dilutes its impact. A dedicated milestone creates a clear "before and after" moment. |
| **Reordered:** Entity System after Business Understanding (was Phase 2 @ week 2, now M4) | Entity system without business context produces isolated objects. Business understanding first gives entities meaning — relationships, people, conversations. The entity system fills in the data. |
| **Merged:** Executive Intelligence + Learning + Explainability (was O-01 through O-04) | Reasoning, learning, and explainability are three facets of the same capability. A founder doesn't care about the engineering distinction. They care that SHUNYA is smart, transparent, and improving. |
| **Merged:** Enterprise + Infrastructure + Security (was P, Q, R) | These are all "production readiness" from the founder's perspective. Splitting them into three milestones would show no founder-visible progress for 6+ weeks. |

---

## 5. Milestone Deep-Dive

### Milestone 1: The OS Comes Alive

**Founder Outcome:**
SHUNYA processes the founder's actions through a real operating system pipeline. Every create, read, update, delete flows through the canonical 11-stage pipeline with real runtimes. The workspace reflects actual OS state.

**AI Outcome:**
The canonical pipeline processes intents through real Kernel, Identity, and Projection runtimes. The Observation stage begins recording founder actions. The context for future AI interactions starts accumulating.

**Technical Outcome:**
- Kernel Runtime wired into pipeline (replaces MockRuntime for intent_resolution, object_resolution)
- Identity Runtime wired (replaces MockRuntime for identity_resolution)
- Flask routes converted to call `os.process_intent()` instead of direct model operations
- Projection Runtime wired (replaces MockRuntime for projection_assembly)
- Pipeline trace operational and queryable

**Internal Foundation:**
- `app/adapters/kernel_adapter.py`, `app/adapters/identity_adapter.py`, `app/adapters/projection_adapter.py`
- Pipeline context propagation through all 11 stages (most stages still no-op)
- Flask founder route conversion

**Demonstration Scenario (5 minutes):**
1. Start SHUNYA application
2. Navigate to login page
3. Sign in with founder credentials
4. Create a new space
5. Create an object inside the space
6. Open the object
7. View the pipeline health endpoint showing all stages with `status: "completed"` for the real runtimes

**Exit Criteria:**
- [ ] `process_intent()` flows through pipeline with real Kernel, Identity, Projection runtimes
- [ ] Pipeline trace shows intent_resolution, identity_resolution, object_resolution, projection_assembly as "completed" with real engine IDs
- [ ] Creating an object in the UI creates a UniversalObject in the kernel registry
- [ ] All existing tests pass (zero regressions)
- [ ] Pipeline health endpoint returns runtime status for all 11 stages

---

### Milestone 2: Executive Home — The Founder's Primary Surface

**Founder Outcome:**
Upon signing in, the founder lands on a dashboard showing their business state — metrics, recent activity, commitments, AI daily brief. This becomes the default surface from which they navigate all of SHUNYA.

**AI Outcome:**
The AI can generate a daily brief from pipeline activity. It can identify commitments from actions. It understands what changed since last login.

**Technical Outcome:**
- Executive Home dashboard component rendering real pipeline data
- Commitment Tracker with progress visualization
- AI daily brief component (basic — uses pipeline data, not yet full LLM)
- Quick action buttons (create object, search, start conversation)

**Internal Foundation:**
- Dashboard data aggregation from pipeline context
- Commitment extraction from pipeline intents
- Activity timeline component

**Demonstration Scenario (5 minutes):**
1. Sign in to SHUNYA
2. Land on Executive Home dashboard
3. See personal greeting with name and organization
4. See metrics: spaces count, objects count, recent activity
5. See open commitments and their status
6. See AI daily brief referencing actual actions taken
7. Click through to an object from the dashboard

**Exit Criteria:**
- [ ] Executive Home is the default post-login surface
- [ ] Dashboard shows 3+ real metrics from pipeline data
- [ ] Commitment Tracker shows 2+ real commitments
- [ ] AI daily brief references specific user actions (not generic text)
- [ ] All objects on dashboard are clickable and navigate to correct detail views
- [ ] All existing tests pass (zero regressions)

---

### Milestone 3: SHUNYA Knows Your Business

**Founder Outcome:**
SHUNYA demonstrates understanding of the founder's business context — people, their relationships, conversations, commitments, knowledge. Opening an object shows related people, past interactions, and relevant documents. Exploring relationships through the knowledge graph reveals connections the founder might not have noticed.

**AI Outcome:**
Memory Knowledge Runtime and Planning Runtime wired into the pipeline. Business context is assembled from knowledge graph, memory, and timeline. The system maintains coherent context across sessions and objects.

**Technical Outcome:**
- Memory/Knowledge Graph Runtime wired into pipeline (replaces MockRuntime for knowledge_graph_update, memory_update)
- Planning Runtime wired (replaces MockRuntime for planning_update)
- Context panel showing relationships, past interactions, documents
- Knowledge graph exploration UI
- Commitment-to-object linking

**Internal Foundation:**
- `app/adapters/memory_adapter.py`, `app/adapters/planning_adapter.py`
- Knowledge graph update from pipeline events
- Memory layer selection (which memory layer to write for which intent type)
- Planning update from commitment creation

**Demonstration Scenario (5 minutes):**
1. Sign in to Executive Home
2. Create a person object ("Jane Smith — Acme Corp")
3. Create a deal object and link it to Jane
4. Create a conversation with Jane
5. Create a commitment in that conversation
6. Open the deal object — see Jane linked, conversation linked, commitment visible
7. Explore the knowledge graph — see Jane → Deal → Commitment relationship
8. Note that SHUNYA now "knows" who Jane is, what the deal is, and what was promised

**Exit Criteria:**
- [ ] Pipeline trace shows knowledge_graph_update and memory_update as "completed" with real runtime output
- [ ] Creating an object and linking it updates the knowledge graph
- [ ] Opening an object shows linked people, conversations, commitments
- [ ] Knowledge graph exploration UI is functional
- [ ] Creating a commitment triggers plan creation in the planning runtime
- [ ] All existing tests pass (zero regressions)

---

### Milestone 4: Create Any Business Object

**Founder Outcome:**
The founder can define any business entity type (Lead, Deal, Invoice, Task, Patient, Case, etc.) with custom fields, then create, view, and manage records of that type in list, kanban, or calendar views — all without writing code or requesting schema changes.

**AI Outcome:**
The entity system stores and retrieves objects through the pipeline. AI can search, filter, and relate entities. Entity definition is a first-class pipeline intent.

**Technical Outcome:**
- Entity type definition CRUD (JSONB schema per tenant)
- Entity CRUD with generic storage
- Entity list view with configurable columns
- Entity detail view with dynamic schema rendering
- Entity form auto-generated from schema
- Kanban pipeline view for any entity type
- Calendar view for entities with date fields
- Search indexing for entity data fields

**Internal Foundation:**
- JSONB storage schema and migrations
- Dynamic form rendering engine
- Generic column configuration system
- Pipeline integration for entity intents

**Demonstration Scenario (5 minutes):**
1. Navigate to Entity Types
2. Define a new type: "Client" with fields (name, email, phone, status, value)
3. Create 3 Client records
4. View them in list view with sortable columns
5. Switch to kanban view grouped by status
6. Open a client detail view — auto-generated form shows all fields
7. Search for a client by name
8. Edit a client record

**Exit Criteria:**
- [ ] Admin can define a custom entity type with 5+ field types
- [ ] Creating records of a custom type stores and retrieves correctly
- [ ] List, detail, form, kanban views render for any entity type
- [ ] Search finds entities across all types
- [ ] Entity operations flow through the pipeline
- [ ] All existing tests pass (zero regressions)

---

### Milestone 5: AI Copilot — Talk to Your OS

**Founder Outcome:**
A persistent chat sidebar where the founder can ask natural language questions and get accurate, grounded answers from their actual data. The Copilot can also create objects, commitments, and tasks via conversation.

**AI Outcome:**
LLM provider abstraction layer operational. The AI Copilot receives pipeline context and generates responses grounded in real data. Conversation workspace stores interactions linked to objects.

**Technical Outcome:**
- LLM provider abstraction layer (provider-agnostic)
- AI Copilot component — persistent chat sidebar
- Copilot connected to pipeline context for context-aware answers
- AI summary generation for any entity
- Conversation workspace with linked objects

**Internal Foundation:**
- Provider abstraction (supports OpenAI, Anthropic, local) with fallback
- Context window assembly from pipeline state
- Prompt template management per intent type
- Streaming response handling

**Demonstration Scenario (5 minutes):**
1. Create 5 entity records across 2 types
2. Open the AI Copilot sidebar
3. Ask: "What's the status of all my active clients?"
4. Receive an accurate AI-generated summary from actual data
5. Ask: "Create a new task to follow up with Acme Corp next week"
6. Verify the task was created in the system
7. Ask: "Who is my highest-value client?"
8. Receive a reasoned answer with specific data reference

**Exit Criteria:**
- [ ] AI Copilot responds from real data (not hardcoded/demo responses)
- [ ] Natural language questions map to correct pipeline intents
- [ ] AI can create objects from conversation
- [ ] Conversation history is linked to referenced objects
- [ ] Entity summary generation works for any entity type
- [ ] Graceful degradation when AI provider is unavailable
- [ ] All existing tests pass (zero regressions)

---

### Milestone 6: Connected Business

**Founder Outcome:**
The founder connects their email (Gmail/Outlook) and calendar to SHUNYA. Emails and events are automatically linked to relevant objects. Notifications keep them informed of important changes. They can import existing data from other tools.

**AI Outcome:**
Integration Runtime wired into pipeline. External data (emails, calendar events) flows through the pipeline and updates knowledge graph, memory, and entity relationships. Integration traces are logged.

**Technical Outcome:**
- Email connector (IMAP sync, SMTP send)
- Calendar connector (read/write)
- In-app notification system
- Email notification dispatch
- Data import pipeline (CSV, contacts)
- Integration settings UI

**Internal Foundation:**
- `app/adapters/integration_adapter.py`
- OAuth flow for email/calendar providers
- Email-to-entity linking heuristics
- Notification dispatch engine
- CSV column mapper

**Demonstration Scenario (5 minutes):**
1. Navigate to Integrations settings
2. Connect Gmail account via OAuth
3. See emails synced, linked to relevant entities (people, deals)
4. Open an entity — see linked emails in context
5. Connect calendar — see events in context
6. Create a notification rule
7. Trigger the notification by changing an entity
8. Receive notification in-app and by email

**Exit Criteria:**
- [ ] Email sync works (IMAP) — inbox appears in SHUNYA
- [ ] Emails are linked to known entities (people, organizations, deals)
- [ ] Calendar sync works — events appear in context
- [ ] In-app notifications fire on entity changes
- [ ] Email notifications are delivered
- [ ] CSV import works with column mapping
- [ ] Pipeline trace shows integration_update as "completed"
- [ ] All existing tests pass (zero regressions)

---

### Milestone 7: Automation — SHUNYA Works for You

**Founder Outcome:**
The founder can create "when X happens, do Y" rules that fire automatically. Repetitive work — status change notifications, welcome emails, SLA breach alerts, weekly summaries — happens without manual intervention.

**AI Outcome:**
Execution Runtime and Automation Runtime wired into pipeline. Automation rules evaluate triggers and execute actions through the pipeline. Execution state is tracked end-to-end.

**Technical Outcome:**
- Execution Runtime wired (replaces MockRuntime for execution_update)
- Automation Runtime wired (replaces MockRuntime for automation_evaluation)
- Rule engine UI (when/if → then/do)
- Workflow templates library
- Automation history and logs

**Internal Foundation:**
- `app/adapters/execution_adapter.py`, `app/adapters/automation_adapter.py`
- Execution lifecycle (12 states, DAG scheduler, batch, rollback)
- Trigger evaluation engine
- Action dispatch to pipeline intents
- Automation governance (approval gates)

**Demonstration Scenario (5 minutes):**
1. Navigate to Automation
2. Create rule: "When lead status changes to 'Booked', send welcome email and create onboarding task"
3. Change a lead's status to "Booked"
4. Verify:
   - Welcome email was sent (check integration log)
   - Onboarding task was created
   - Automation log shows rule fired with status "completed"
5. View automation history showing all rule executions
6. Pause the rule — verify it no longer fires

**Exit Criteria:**
- [ ] Pipeline trace shows execution_update and automation_evaluation as "completed"
- [ ] Creating a rule and triggering it executes all actions
- [ ] Rule evaluation is real-time (not batch/polling)
- [ ] Automation history is queryable by rule, object, and time
- [ ] Rules can trigger across entities (lead update → email → task creation)
- [ ] All existing tests pass (zero regressions)

---

### Milestone 8: Executive Intelligence

**Founder Outcome:**
SHUNYA now reasons about the founder's business, not just retrieves data. It explains its thinking with traceable evidence. It learns from outcomes — corrections improve future performance. Confidence scores help the founder gauge reliability.

**AI Outcome:**
Reasoning Runtime wired with real LLM inference. Learning loop closes: observation → decision → outcome → learning. Explainability traces render for every action. Confidence engine integrated.

**Technical Outcome:**
- Reasoning Runtime wired (replaces MockRuntime for reasoning_update)
- LLM inference provider operational (via abstraction layer from M5)
- Learning from outcomes — knowledge graph updates from execution results
- Explainability traces — every action traceable: intent → workspace
- Confidence scores on AI responses
- Anomaly detection from pattern analysis

**Internal Foundation:**
- `app/adapters/reasoning_adapter.py`
- Prompt engineering per reasoning type (7 reasoning types)
- Learning adapter — outcome processing into knowledge updates
- Trace persistence and query API
- Trace viewer UI component

**Demonstration Scenario (5 minutes):**
1. Create a deal with $50k value, status "Negotiation", linked to a client
2. Ask the AI Copilot: "Is this deal at risk?"
3. SHUNYA provides a reasoned analysis referencing:
   - Deal value, stage, age
   - Recent communications with the client
   - Similar past deals that succeeded/failed
   - Confidence score on the assessment
4. Click "Show reasoning" — view the complete trace:
   - Intent → Identity → Knowledge → Memory → Reasoning → Response
5. Correct a detail in the analysis
6. Ask a similar question — SHUNYA incorporates the correction
7. View learning progress: "Learned from 3 interactions today"

**Exit Criteria:**
- [ ] Pipeline trace shows reasoning_update as "completed" with real inference
- [ ] AI responses include confidence scores
- [ ] Explainability traces are viewable and human-readable
- [ ] Correcting AI responses improves future responses
- [ ] Learning feedback loop is operational (observe → decide → act → learn)
- [ ] Anomaly detection surfaces deviations from patterns
- [ ] All existing tests pass (zero regressions)

---

### Milestone 9: Enterprise Ready

**Founder Outcome:**
The founder can invite team members, assign roles, and trust that data is isolated and auditable. SHUNYA meets enterprise compliance requirements. Every action is recorded in an immutable audit trail.

**AI Outcome:**
Tenant isolation enforced at every pipeline stage. RBAC gates every action. Audit runtime records every pipeline execution immutably.

**Technical Outcome:**
- Tenant isolation in all runtimes
- RBAC enforcement (role/permission resolution per action)
- Immutable audit trail (every pipeline execution recorded)
- Invite and team management UI
- Audit query API and viewer
- Performance optimization pass

**Internal Foundation:**
- Tenant context propagation through all pipeline stages
- Permission resolution adapter
- Audit runtime wiring
- Audit storage (immutable append-only)
- Performance benchmarking and optimization

**Demonstration Scenario (5 minutes):**
1. Invite a team member with "Viewer" role
2. Sign in as the viewer
3. Verify viewer can view objects but cannot edit or delete
4. Try a destructive action — verify rejection with authorization trace
5. Sign in as admin — view the audit trail
6. Verify every action (create, edit, delete, permission change) is recorded immutably
7. Verify viewer cannot see admin's personal objects (tenant isolation)

**Exit Criteria:**
- [ ] Organization A cannot access Organization B's data through any pipeline stage
- [ ] RBAC enforcement: unauthorized actions are rejected with explainable trace
- [ ] Audit trail contains every pipeline execution with intent, actor, object, timestamp
- [ ] Audit trail is immutable (no deletion or modification)
- [ ] Team management UI functional
- [ ] All existing tests pass (zero regressions)

---

### Milestone 10: Production Launch

**Founder Outcome:**
SHUNYA is a polished production product. A new founder can sign up and complete their first meaningful action in under 5 minutes. The system is fast, secure, monitored, and backed up. SHUNYA is live at shunyaos.com.

**AI Outcome:**
First-run onboarding flows through the pipeline. Error messages are generated contextually. System health monitoring alerts the team when subsystems degrade.

**Technical Outcome:**
- Onboarding flow (sign-up → first object in < 5 minutes)
- Error recovery UI (human-readable errors with recovery actions)
- Security audit (OWASP Top 10, dependency scan)
- CI/CD pipeline operational
- Backup & recovery verified
- Monitoring and alerting (health checks, error tracking, performance)
- Load testing (50 concurrent users)
- Error monitoring (Sentry or equivalent)
- Launch checklist complete

**Internal Foundation:**
- Onboarding wizard with guided steps
- Sample data seeding for first-run experience
- Security remediation from audit findings
- Deployment pipeline automation
- Backup rotation and restore testing

**Demonstration Scenario (5 minutes):**
1. Sign out and create a new account
2. Complete onboarding:
   - Enter organization name
   - Define a first entity type
   - Create first entity record
   - View Executive Home with real data
   - Ask AI Copilot a question and get a real answer
3. Verify total time from sign-up to first meaningful action: < 5 minutes
4. Verify error recovery: attempt an invalid action → see human-readable error
5. Verify system health dashboard shows green

**Exit Criteria:**
- [ ] New founder creates first object within 5 minutes of sign-up
- [ ] Every pipeline error produces human-readable error with recovery action
- [ ] Security audit: zero critical or high findings
- [ ] CI/CD pipeline: automated tests on push, deploy on merge to main
- [ ] Backup & recovery verified (RTO < 1 hour, RPO < 5 minutes)
- [ ] Load test: 50 concurrent users with < 1% error rate
- [ ] Monitoring and alerting functional
- [ ] All existing tests pass (zero regressions)
- [ ] Founder confirms: "SHUNYA is ready for its first customer"

---

## 6. Internal Engineering Work by Milestone

Every milestone has Internal Foundation work (invisible to the founder) and Founder Capability work (visible to the founder). This section documents the internal work so it is explicit rather than hidden.

### Milestone 1: The OS Comes Alive

| Internal Foundation | Founder Capability |
|---------------------|-------------------|
| `app/adapters/kernel_adapter.py` | Pipeline health indicator in UI |
| `app/adapters/identity_adapter.py` | Workspace reflects real OS state |
| Flask route conversion to `os.process_intent()` | Pipeline trace viewer |
| Pipeline context propagation | |
| `app/adapters/projection_adapter.py` | |

### Milestone 2: Executive Home

| Internal Foundation | Founder Capability |
|---------------------|-------------------|
| Dashboard data aggregation from pipeline | Executive Home dashboard |
| Commitment extraction from pipeline intents | Commitment Tracker |
| Activity timeline component | AI daily brief |

### Milestone 3: SHUNYA Knows Your Business

| Internal Foundation | Founder Capability |
|---------------------|-------------------|
| `app/adapters/memory_adapter.py` | Context panel with relationships |
| `app/adapters/planning_adapter.py` | Knowledge graph exploration UI |
| Knowledge graph update from pipeline events | Commitment-to-object linking |
| Memory layer selection logic | |
| Planning update from commitment creation | |

### Milestone 4: Create Any Business Object

| Internal Foundation | Founder Capability |
|---------------------|-------------------|
| JSONB storage schema and migrations | Entity type definition UI |
| Dynamic form rendering engine | Entity CRUD UI |
| Generic column configuration system | List, detail, form, kanban, calendar views |
| Pipeline integration for entity intents | Search across entity types |

### Milestone 5: AI Copilot

| Internal Foundation | Founder Capability |
|---------------------|-------------------|
| LLM provider abstraction layer | AI Copilot chat sidebar |
| Context window assembly from pipeline state | Entity summary generation |
| Prompt template management | Conversation workspace |
| Streaming response handling | |

### Milestone 6: Connected Business

| Internal Foundation | Founder Capability |
|---------------------|-------------------|
| `app/adapters/integration_adapter.py` | Email connector UI |
| OAuth flow for email/calendar | Calendar connector UI |
| Email-to-entity linking heuristics | Notification preferences |
| Notification dispatch engine | Integration settings UI |
| CSV column mapper | Data import wizard |

### Milestone 7: Automation

| Internal Foundation | Founder Capability |
|---------------------|-------------------|
| `app/adapters/execution_adapter.py` | Rule engine UI (when/if → then/do) |
| `app/adapters/automation_adapter.py` | Workflow templates library |
| Execution lifecycle (12 states, DAG scheduler) | Automation history UI |
| Trigger evaluation engine | Rule pause/modify/delete |
| Action dispatch to pipeline intents | |
| Automation governance (approval gates) | |

### Milestone 8: Executive Intelligence

| Internal Foundation | Founder Capability |
|---------------------|-------------------|
| `app/adapters/reasoning_adapter.py` | Reasoned AI analysis |
| Prompt engineering per reasoning type | Explainability trace viewer |
| Learning adapter — outcome processing | Confidence scores on responses |
| Trace persistence and query API | Anomaly detection surfacing |
| Trace viewer UI component | Learning progress indicator |

### Milestone 9: Enterprise Ready

| Internal Foundation | Founder Capability |
|---------------------|-------------------|
| Tenant context propagation through pipeline | Team invite UI |
| Permission resolution adapter | Role assignment UI |
| Audit runtime wiring | Audit trail viewer |
| Audit storage (immutable append-only) | |
| Performance benchmarking and optimization | |

### Milestone 10: Production Launch

| Internal Foundation | Founder Capability |
|---------------------|-------------------|
| Security remediation from audit findings | Onboarding wizard |
| Deployment pipeline automation | Human-readable error messages |
| Backup rotation and restore testing | System health dashboard |
| Monitoring and alerting configuration | Launch checklist |
| Load testing infrastructure | |

---

## 7. Dependency Graph

### 7.1 Milestone Dependencies

```
M1: OS Comes Alive
 │
 ├──► M2: Executive Home ───► depends on M1 (needs real pipeline data)
 │
 ├──► M3: Business Understanding ───► depends on M1 (needs pipeline)
 │                                depends on M2 (Executive Home is surface)
 │
 ├──► M4: Entity System ───► depends on M1 (needs pipeline)
 │                        depends on M3 (entities need business context)
 │
 ├──► M5: AI Copilot ───► depends on M1 (needs pipeline)
 │                     depends on M3 (needs business context)
 │                     depends on M4 (needs entity data)
 │
 ├──► M6: Connected Business ───► depends on M1 (needs pipeline)
 │                            depends on M3 (needs entity recognition)
 │                            depends on M4 (needs entities to link)
 │
 ├──► M7: Automation ───► depends on M1 (needs pipeline)
 │                     depends on M3 (needs business context)
 │                     depends on M4 (needs entity triggers)
 │                     depends on M6 (needs integration actions)
 │
 ├──► M8: Executive Intelligence ───► depends on M1 (needs pipeline)
 │                                 depends on M3 (needs business context)
 │                                 depends on M4 (needs entity data)
 │                                 depends on M5 (needs LLM provider)
 │                                 depends on M7 (needs execution outcomes)
 │
 ├──► M9: Enterprise Ready ───► depends on M1 (needs pipeline)
 │                           depends on M2 (Executive Home surface)
 │                           depends on M4 (entities need isolation)
 │
 └──► M10: Production Launch ───► depends on all M1-M9
```

### 7.2 Critical Path

```
M1 → M2 → M3 → M4 → M5 → M8 → M10
```

This is the minimum path to Version 1.0. It is 7 milestones long. All other milestones (M6, M7, M9) can be parallelized or deferred relative to their dependency positions.

**Critical path timeline:** M1 (3-4) + M2 (2-3) + M3 (3-4) + M4 (3-4) + M5 (2-3) + M8 (3-4) + M10 (2-3) = **18-25 weeks** to v1.0 minimum.

### 7.3 Parallel Workstreams

```
Stream A (Core Pipeline):      M1 ──► M2 ──► M3 ──► M4 ──► M5 ──► M8 ──► M10
Stream B (Connected Business):                                              ──► M6 ──►
Stream C (Automation):                                                            ──► M7
Stream D (Enterprise):                                                                  ──► M9
Stream E (Infrastructure):                                                                    ──► M10 (shared)
```

Stream A is the critical path. Streams B, C, and D can begin once their respective dependencies in Stream A are met and can run in parallel with later Stream A milestones.

### 7.4 Capability Evolution

Each milestone advances capabilities through 6 states:

```
Designed → Implemented → Integrated → Operational → Founder Validated → Production Ready
```

| Capability | Current State | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10 |
|-----------|:------------:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Canonical Pipeline | Designed | **P Ready** | | | | | | | | | |
| Kernel Runtime | Implemented | **P Ready** | | | | | | | | | |
| Identity Runtime | Implemented | **P Ready** | | | | | | | | | |
| Projection Runtime | Implemented | **P Ready** | | | | | | | | | |
| Executive Home | Designed | | **P Ready** | | | | | | | | |
| Commitment Tracker | Designed | | **P Ready** | | | | | | | | |
| Knowledge Graph Runtime | Implemented | | | **P Ready** | | | | | | | |
| Memory Runtime | Implemented | | | **P Ready** | | | | | | | |
| Planning Runtime | Implemented | | | **P Ready** | | | | | | | |
| Entity System (JSONB) | Partial | | | | **P Ready** | | | | | | |
| Entity List/Detail/Form | Partial | | | | **P Ready** | | | | | | |
| LLM Provider Layer | Partial | | | | | **P Ready** | | | | | |
| AI Copilot | Partial | | | | | **P Ready** | | | | | |
| Conversation Workspace | Partial | | | | | **P Ready** | | | | | |
| Integration Runtime | Implemented | | | | | | **P Ready** | | | | |
| Email Connector | Partial | | | | | | **P Ready** | | | | |
| Calendar Connector | Missing | | | | | | **P Ready** | | | | |
| Notifications | Missing | | | | | | **P Ready** | | | | |
| Execution Runtime | Implemented | | | | | | | **P Ready** | | | |
| Automation Runtime | Implemented | | | | | | | **P Ready** | | | |
| Reasoning Runtime | Implemented | | | | | | | | **P Ready** | | |
| Learning | Implemented | | | | | | | | **P Ready** | | |
| Explainability | Integrated | | | | | | | | **P Ready** | | |
| Multi-Tenancy | Partial | | | | | | | | | **P Ready** | |
| RBAC | Implemented | | | | | | | | | **P Ready** | |
| Audit Trail | Partial | | | | | | | | | **P Ready** | |
| Onboarding | Missing | | | | | | | | | | **P Ready** |
| Error Recovery | Missing | | | | | | | | | | **P Ready** |
| CI/CD Pipeline | Missing | | | | | | | | | | **P Ready** |
| Backup & Recovery | Missing | | | | | | | | | | **P Ready** |
| Monitoring | Partial | | | | | | | | | | **P Ready** |
| Security Hardening | Partial | | | | | | | | | | **P Ready** |

---

## 8. Acceptance Criteria & Demonstration Scenarios

### 8.1 Summary Table

| Milestone | Acceptance Test | Evidence Required | Demo Time |
|-----------|----------------|-------------------|:---------:|
| M1: OS Comes Alive | `process_intent()` flows through 4+ real runtimes | Pipeline trace shows real engine IDs | 5 min |
| M2: Executive Home | Login → see 3+ real metrics, 2+ commitments, AI brief | Browser screenshot | 3 min |
| M3: Knows Your Business | Create linked objects → see relationships in context | Screenshot of context panel + knowledge graph | 5 min |
| M4: Entity System | Define custom type → create 3 records → see in kanban | Browser walkthrough | 4 min |
| M5: AI Copilot | Ask question → get accurate answer from real data | Conversation screenshot | 3 min |
| M6: Connected Business | Connect email → see linked entities → receive notification | Screenshot of email in context | 5 min |
| M7: Automation | Create rule → trigger it → verify all actions executed | Automation log + proof of actions | 4 min |
| M8: Executive Intelligence | Ask "why" → get reasoned analysis with trace | Explainability trace + confidence scores | 5 min |
| M9: Enterprise Ready | Cross-tenant isolation + RBAC rejection + audit trail | Test output + audit query result | 5 min |
| M10: Production Launch | New user → first object in < 5 min → error recovery | Timed walkthrough | 5 min |

### 8.2 Founder Acceptance Protocol

Every milestone completes as **Candidate for Founder Review**, not "Complete." The founder must observe and accept each milestone before the next begins.

**Gates (from Founder Acceptance Protocol):**

| Gate | Description | Who Verifies |
|------|-------------|-------------|
| Compiled | Code exists, builds pass | CI/CD |
| Tested | All tests pass at >90% coverage | CI/CD |
| Observed | Demo scenario runs end-to-end | Engineer |
| Demonstrated | Founder watches the demo | Founder |
| **Accepted** | Founder confirms milestone complete | Founder |

---

## 9. Production Readiness Stages

### 9.1 Stage Definitions

| Stage | Definition | Minimum Capability Required |
|-------|-----------|---------------------------|
| **Alpha** | Internal-only testing. SHUNYA is usable by the founder and core team. Data is not persistent (may be reset). Pipeline is real but AI responses may be preliminary. | M1 + M2 + M3 + M4 |
| **Founder Daily Driver** | The founder can use SHUNYA as their primary business system. Data is persistent. Core workflows work end-to-end. The founder should feel comfortable migrating real work to SHUNYA. | M5 + M6 (AI Copilot + Email/Calendar) |
| **Private Beta** | First external customers can sign up and use SHUNYA. Invitation-only. Feedback collected. Rapid iteration. No public marketing yet. | M7 + M8 (Automation + Executive Intelligence) |
| **Public Beta** | Open sign-up. SHUNYA is publicly listed and available to any business. Focus on reliability, performance, and onboarding. Limited support (email + docs). | M9 (Enterprise Ready — multi-tenant, RBAC, audit) |
| **Version 1.0** | SHUNYA is a production product. Public launch complete. Paid plans available. Support, SLAs, and compliance documentation in place. | M10 (Production Launch — onboarding, security, CI/CD, monitoring, backup) |

### 9.2 Stage Readiness Matrix

| Requirement | Alpha | Founder Daily Driver | Private Beta | Public Beta | v1.0 |
|-------------|:-----:|:-------------------:|:------------:|:-----------:|:----:|
| Pipeline operational | ✅ | ✅ | ✅ | ✅ | ✅ |
| Executive Home | ✅ | ✅ | ✅ | ✅ | ✅ |
| Business understanding | ✅ | ✅ | ✅ | ✅ | ✅ |
| Entity system | ✅ | ✅ | ✅ | ✅ | ✅ |
| AI Copilot | | ✅ | ✅ | ✅ | ✅ |
| Email/Calendar integration | | ✅ | ✅ | ✅ | ✅ |
| Automation | | | ✅ | ✅ | ✅ |
| Executive Intelligence | | | ✅ | ✅ | ✅ |
| Multi-tenant isolation | | | | ✅ | ✅ |
| RBAC | | | | ✅ | ✅ |
| Audit trail | | | | ✅ | ✅ |
| Onboarding flow | | | | ✅ | ✅ |
| Error recovery | | | | ✅ | ✅ |
| CI/CD pipeline | | | | ✅ | ✅ |
| Backup & recovery | | | | ✅ | ✅ |
| Monitoring & alerting | | | | ✅ | ✅ |
| Security audit (zero critical) | | | | | ✅ |
| Load testing (50 concurrent) | | | | | ✅ |
| Compliance docs | | | | | ✅ |
| Launch marketing | | | | | ✅ |

### 9.3 Estimated Timeline to Each Stage

| Stage | Milestones Complete | Est. Weeks from Start |
|-------|-------------------|:--------------------:|
| **Alpha** | M1 + M2 + M3 + M4 | 11-15 weeks |
| **Founder Daily Driver** | M5 + M6 | 18-22 weeks |
| **Private Beta** | M7 + M8 | 26-30 weeks |
| **Public Beta** | M9 | 30-34 weeks |
| **Version 1.0** | M10 | 34-37 weeks |

---

## 10. Business Understanding Milestone — A Note

### 10.1 Evaluation

Directive 04A Section 5 asked:

> Does the roadmap require a dedicated milestone focused on SHUNYA developing a coherent understanding of the business?

**Result: Yes — Milestone 3 (SHUNYA Knows Your Business) is that milestone.**

### 10.2 Rationale

The existing roadmaps scatter business understanding across:
- Memory/Knowledge Graph wiring (M-01)
- Planning wiring (M-02)  
- Integration runtime wiring (N-03)
- Reasoning runtime wiring (O-01)
- Learning from outcomes (O-03)

This scattering means SHUNYA never has a "moment" where it demonstrates business understanding. The capability accumulates invisibly. The founder never feels "SHUNYA now knows my business."

A **dedicated Business Understanding milestone** creates:
1. **A clear before/after moment** — The founder can point to "before this milestone, SHUNYA didn't know who Jane was" vs. "after this milestone, SHUNYA knows Jane is my client at Acme Corp with a $50k deal and a commitment to close by Friday."
2. **A unified set of capabilities** — Knowledge graph, memory, planning, and identity converge around a single purpose: understanding the founder's business. They are not three separate engineering tasks.
3. **Correct sequencing** — Business understanding must come before AI Copilot. An AI that doesn't understand the business can only give generic answers. Placing it after Executive Home but before Entity System and AI Copilot ensures every AI interaction from M5 onward is grounded in real business context.
4. **Founder-visible progress** — The milestone produces an observable change: the context panel shows relationships, conversations are remembered, commitments are tracked in context. The founder can verify that SHUNYA "gets it."

### 10.3 What It Unifies

The Business Understanding milestone gathers:

| Domain | Components | Current State |
|--------|-----------|:-------------:|
| **People** | Identity resolution, role tracking, relationship edges | Implemented but not wired |
| **Customers** | Entity recognition from knowledge graph | Implemented but not wired |
| **Suppliers / partners** | Organization identity and relationship tracking | Partial |
| **Relationships** | Knowledge graph edge traversal, hop depth | Implemented but not wired |
| **Conversations** | Memory storage with object linking | Implemented but not wired |
| **Documents** | Knowledge store references | Implemented but not wired |
| **Emails and meetings** | External communication integration | M6 (Connected Business) |
| **Commitments** | Planning runtime commitment creation and tracking | Implemented but not wired |
| **Timelines** | Sequence tracking, dependency detection | Partial |

**Emails and meetings** are intentionally deferred to M6 (Connected Business). The Business Understanding milestone provides the framework and internal data. External data integration is a separate capability that depends on this framework being in place.

---

## 11. Executive Home Placement — Rationale

### 11.1 Recommendation

**Executive Home moves from Phase 4 (week 10 under prior roadmap) to Milestone 2 (weeks 4-7).**

### 11.2 Reasoning

**1. The founder needs a daily surface from day one.**

Under the prior roadmap, the founder would sign in after M1 (Pipeline Activation) and see a generic workspace with no dashboard, no metrics, no orientation. They'd have to navigate to find anything. This undermines the "operating system" feel — an OS without a desktop is just a kernel.

**2. Executive Home is the surface that all subsequent milestones feed into.**

Every milestone produces data that should appear on Executive Home:
- M3 (Business Understanding) → relationship context in the dashboard
- M4 (Entity System) → entity metrics and quick-create
- M5 (AI Copilot) → AI brief and chat surface
- M6 (Connected Business) → notification preview
- M7 (Automation) → automation status and history
- M8 (Executive Intelligence) → confidence scores and learning progress

If Executive Home arrives late, each milestone's output has no natural home. The founder must navigate to individual tools to see results.

**3. A basic Executive Home is achievable in 2-3 weeks after M1.**

The initial version needs only:
- Pipeline health indicator (from M1)
- Recent activity list (from pipeline trace)
- Quick action buttons (navigation shortcuts)
- Basic AI brief (template-driven, from pipeline data)

This is not a heavy lift. It does not require M4 (Entity System) or M5 (AI Copilot) — those enhance Executive Home later.

**4. User psychology matters.**

The first 10 seconds after login determine whether the founder feels oriented or lost. Executive Home provides orientation: "Here's your business state. Here's what changed. Here's what needs attention." Without it, every login feels like arriving in an empty room.

**5. Implementation convenience is not the deciding factor.**

The prior roadmap placed Executive Home at Phase 4 because it was convenient to build it after the Entity System (more data to display) and AI Copilot (more sophisticated briefs). But from the founder's perspective, waiting 10 weeks for a dashboard is unacceptable. A simpler dashboard delivered earlier is better than a sophisticated dashboard delivered later. Executive Home can be iteratively enhanced.

### 11.3 What Gets Built First (M2) vs. Later (M4, M5, M8)

| Feature | M2 (Week 4-7) | Enhanced by M4 | Enhanced by M5 | Enhanced by M8 |
|---------|:-------------:|:--------------:|:--------------:|:--------------:|
| Pipeline health | ✅ Basic | | | |
| Recent activity | ✅ From pipeline | | | |
| Quick actions | ✅ Navigate | ✅ Create entity | ✅ AI create | |
| Metrics | ✅ Counts | ✅ Entity metrics | | |
| Commitments | ✅ Basic | ✅ Per entity | | |
| AI daily brief | ✅ Template-driven | ✅ Entity-rich | ✅ LLM-generated | ✅ With reasoning |
| AI Copilot surface | | | ✅ Chat panel | |
| Confidence scores | | | | ✅ |
| Learning progress | | | | ✅ |

---

## 12. Applicable Roadmap Governance Rules

### 12.1 How to Use This Roadmap

1. **Every sprint begins with** selecting the next available milestone from the roadmap.
2. **Every milestone must satisfy all exit criteria** before the next milestone in its dependency chain begins.
3. **Parallel workstreams** may be worked on simultaneously if their dependency chains do not overlap.
4. **Completed milestones** are marked "Accepted" in the capability matrix (Section 7.4).
5. **Roadmap changes** require a documented CAP (Change Approval Proposal) and must preserve dependency integrity.

### 12.2 Change Rules

| Operation | Rule |
|-----------|------|
| **Adding a milestone** | Must be inserted after all dependencies are met. Must not break existing dependency chains. Requires CAP + Founder approval. |
| **Splitting a milestone** | The new milestones must collectively satisfy the original acceptance criteria. |
| **Merging milestones** | Dependencies of both originals must be met. The merged milestone must satisfy all original acceptance criteria. |
| **Reordering** | Dependency order must be preserved. Non-dependent milestones may be reordered freely. |
| **Changing priority** | Priority changes do not affect dependency ordering. They affect scheduling order among non-dependent milestones. |

### 12.3 Completion Verification

Every milestone, when completed, must have:

- [ ] All exit criteria satisfied
- [ ] All internal foundation work documented
- [ ] Demonstration scenario executed and witnessed
- [ ] Capability matrix updated
- [ ] Founder acceptance obtained (Candidate for Founder Review)
- [ ] No regression in existing tests

### 12.4 Relationship to Other Documents

| Document | Relationship |
|----------|-------------|
| **SHUNYA Constitution (02)** | Every milestone includes Constitutional compliance. Article 9 (Calm Before Complexity) is preserved. |
| **OS Constitution** | The pipeline invariants and architecture are unchanged. Milestones wire existing runtimes, not redesign. |
| **Universal Object Protocol (04)** | Protocol implementation is foundational to M1 and refined through M4. |
| **Runtime Canon (05)** | Runtime wiring follows the Canon sequence. No new runtimes created. |
| **AI Canon (07)** | AI capabilities mature across M3, M5, M8. No new AI architecture. |
| **Experience Canon (08)** | Experience principles are preserved. Executive Home aligns with Object-First and Workspace-First principles. |
| **DNA-01 (Device-Native Architecture)** | Device-native adaptation is a parallel workstream. Not modified by this roadmap. |
| **Capability Matrix** | Single source of truth for progress tracking. Updated after every milestone. |

---

> **End of SHUNYA Founder Experience Roadmap v1.0**
>
> This roadmap is the definitive execution plan for SHUNYA 1.0.
> No further planning directives are required.
> All subsequent directives shall result in working product increments.
>
> **[Return to INDEX](INDEX.md)**