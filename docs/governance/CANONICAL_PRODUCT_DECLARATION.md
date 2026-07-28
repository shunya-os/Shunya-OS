# SHUNYA v1.0 — Canonical Product Declaration

*This is the single authoritative specification of SHUNYA as it should exist at v1.0. Every implementation decision shall be measured against this document. No architectural or implementation detail appears here — only the product.*

---

## Part 1: The Canonical Product

### 1.1 The First Visit

A founder arrives at shunyaos.com.

The page loads slowly — not because of performance, but because the first thing they see is a carefully composed cinematic introduction. The screen is dark. A single word appears in Sanskrit: **शून्य**.

Beneath it, in English: **SHUNYA — One Operating System for Your Business**.

The founder does not see a login form. They see a story. A brief animated sequence communicates the idea: *Your business is not a collection of apps. It is one living system. SHUNYA is that system.*

The word "शून्य" means zero — the void from which everything emerges. The founder's business is not fragmented. It is one. SHUNYA is the operating system that makes that true.

After the introduction, the founder is invited to create their identity. The transition is seamless — no page reload, no new URL. The story continues.

### 1.2 Founder Identity

Every founder is a single identity.

That identity carries:
- A name
- An email address
- A password
- A personal workspace
- Organization memberships
- Preferences (layout, density, theme)

The founder does not create a new account for each organization. They are themselves across all of them. Switching organizations changes the data they see but never changes who they are.

Identity creation asks for:
1. Name
2. Email
3. Password

That is all. No onboarding questionnaire. No credit card. No "tell us about your business." The founder creates their identity and enters their organization immediately.

### 1.3 Organization Lifecycle

An organization is a bounded business context.

Every organization has:
- A name
- An industry (optional, for AI context)
- Objects (customers, invoices, commitments, conversations, notes, milestones)
- Relationships (partners, suppliers, vendors)
- A timeline of events
- AI memory

The founder can create a new organization at any time. Organizations are independent — data never leaks between them. The founder switches organizations with a single click and their workspace transforms to reflect the new context.

The demonstration environment ships with 3 pre-seeded organizations:
- **Wanderlust Expeditions** (Travel & Tourism) — a premium adventure travel company
- **Precision Components Ltd** (Manufacturing) — an industrial components manufacturer
- **NovaCare Health Systems** (Healthcare) — a multi-specialty healthcare network

Each has 50+ objects, months of historical milestones, AI-summarized conversations, and realistic business narratives. The first-time founder explores these to understand what SHUNYA can do, then creates their own organization.

### 1.4 The Executive Home

The first screen after login is the Executive Home.

It is not a dashboard. It is a calm, intelligent overview of the business.

The Executive Home displays:
- **Metrics** — key counts (customers, invoices, commitments, conversations) displayed as simple numbers with labels
- **Recent Milestones** — the most significant historical events, showing that the business has been operating for months
- **Next Best Action** — one clear, prioritized next step (e.g., "Review overdue commitment" or "Explore your 167 business records")
- **AI Context** — a brief summary of the current state of the business

The layout is spacious. 70% of the screen is content. 20% is context (labels, descriptions, AI insights). 10% is controls (buttons, links, actions). No card is crowded. No metric is decorative.

### 1.5 Universal Search

The founder presses ⌘K.

A search overlay opens instantly. The overlay is translucent — the workspace behind it is visible but dimmed. The cursor is already in the search input.

The founder types. Results appear after 200ms of inactivity. Results include every object type: customers, invoices, commitments, conversations, notes, suppliers, milestones. Each result shows the object name, type, and a brief status indicator.

The founder navigates results with arrow keys. They press Enter to open a result. The overlay closes. The workspace transitions to the selected object. The search context is preserved if they return.

### 1.6 Navigation

Navigation is context-based, not page-based.

The workspace bar at the top shows open workspaces as tabs. Tabs are ordered by recency. Each tab shows the workspace name and a status indicator (active, has changes, has errors).

The founder switches workspaces by:
- Clicking a tab
- Pressing ⌘1-⌘9 (first 9 workspaces)
- Using search (⌘K) to find and open any object
- Following a link from AI suggestions

Switching workspaces is instant. The transition is a subtle cross-fade — no jarring cuts, no loading spinners, no blank screens. The founder's focus is preserved: if they were reading a conversation, the scroll position is maintained.

### 1.7 Workspace Philosophy

Every workspace is a composition of panels.

A panel is a visual projection of runtime state. Panels are arranged by the Layout Engine, which answers only "which panels exist" — never "how does a panel look."

Workspace types:
- **Executive Home** — overview metrics, milestones, AI summary, next action
- **Object Workspace** — identity panel, content panel, timeline panel, AI analysis
- **Conversation Workspace** — message log, participant list, linked objects, AI context
- **Commitment Workspace** — progress bar, confidence meter, blocker list, evidence list, next action

Each workspace feels complete. There are no empty panels, no "Coming soon" placeholders, no dead-end interactions. If a capability is unavailable, the panel explains why clearly.

### 1.8 AI Behaviour

AI is an embedded operating layer, not a chatbot.

The AI Copilot appears as a sidebar in every workspace. It knows automatically:
- Which workspace is active
- Which object is selected
- Which conversation is open
- Which commitments are related
- What the timeline shows

The AI does not ask for context. It observes the context and offers insights.

When the founder asks a question, the AI:
1. Answers with confidence if it has reliable data
2. Explains uncertainty if confidence is low ("I can see the records but I'm not confident about the trend")
3. Defers gracefully if it cannot answer ("I don't have enough information about that yet")

The AI never generates responses just to appear intelligent. Silence with an honest explanation is always preferable to a confident-sounding wrong answer.

The AI can:
- Summarize recent activity
- Identify overdue commitments
- Recommend priorities
- Explain customer history
- Answer contextual business questions

### 1.9 Onboarding

The first-time founder experience is guided but not prescriptive.

After creating their identity, the founder enters their first organization. If it is a new organization (no data), the Executive Home shows:
- "Welcome to SHUNYA" — a brief, warm introduction
- "SHUNYA helps you run your business from one operating system."
- Three suggested first actions: "Add your first customer," "Create your first commitment," "Explore the demo data"

The founder can choose any path. If they explore the demo data, they see the pre-seeded organizations and can navigate through them freely. If they create their own data, the system guides them gently — one step at a time — but never forces them through a wizard.

The onboarding experience ends when the founder has completed one meaningful action (created a customer, opened a conversation, made a commitment). After that, SHUNYA treats them as a returning founder.

### 1.10 Daily Operation

A founder's typical day in SHUNYA:

1. **Open browser.** SHUNYA is the tab they never close.
2. **Session is restored.** No login required. The Executive Home of their last organization is already loaded.
3. **Scan the Executive Home.** Metrics show the state of the business. Milestones show what happened since yesterday. The AI highlights anything that needs attention.
4. **Search.** ⌘K, type a customer name, press Enter. The customer's workspace opens.
5. **Work naturally.** The founder reads the customer's details, opens a related conversation, sees linked commitments, checks the timeline, asks the AI a question. None of these require navigation to a different page — they are all panels within the same continuous workspace.
6. **Create.** The founder creates a new commitment directly from the conversation workspace. The timeline updates immediately. The AI acknowledges the new commitment.
7. **Switch organizations.** The founder clicks a different organization. The workspace transforms. The Executive Home now shows that organization's metrics. The AI context shifts.
8. **Return to Executive Home.** One click. The overview is current. Nothing is lost.

Throughout the day, the founder never feels they are switching between apps. They are always inside SHUNYA—one operating system, one continuous experience.

### 1.11 The Demonstration Environment

SHUNYA ships with a permanent Living Demonstration Environment.

This is not a mockup. It is a complete, deterministic seed of 167 objects across 3 organizations, each with months of operational history, realistic business narratives, AI-summarized conversations, and cross-referenced data.

The demonstration environment serves as:
- **Developer environment** — test against consistent data
- **QA environment** — validate every change against the same baseline
- **Onboarding environment** — new founders explore real-looking businesses
- **Demonstration environment** — show SHUNYA's capabilities without empty states
- **Regression environment** — re-run after every change to confirm nothing broke

The seed is deterministic (same input = same output), idempotent (re-running does not duplicate data), and version-controlled with the repository.

### 1.12 Sign Out and Returning Founder

The founder signs out with one click from the profile menu.

On return, they see the cinematic introduction again — but briefly. The animation is shorter, acknowledging they have been here before. The login form is shown immediately.

After login, the session is restored:
- Same organization they were working in
- Same workspace layout
- Same scroll position (approximate)
- AI context that remembers the previous session

The returning founder never feels like a new user. Their workspace is exactly where they left it.

---

## Part 2: Canonical Capability Classification

Every capability discovered during the audit is classified below.

| Capability | Classification | Rationale |
|------------|---------------|-----------|
| Founder signin (POST /api/v1/founder/signin) | ✅ Canonical | Primary auth endpoint |
| Founder session (session cookie) | ✅ Canonical | Flask session-based auth |
| Founder objects list (GET /api/v1/founder/objects) | ✅ Canonical | Generic object discovery API |
| Founder object types (GET /api/v1/founder/objects/types) | ✅ Canonical | Type-aware discovery |
| Founder spaces list (GET /api/v1/founder/spaces) | ✅ Canonical | Organization discovery |
| Founder object CRUD (POST /api/v1/founder/spaces/.../objects) | ✅ Canonical | Object creation |
| Demographic seed (scripts/seed_demo.py) | ✅ Canonical | Deterministic demo environment |
| Business module (frontend/runtimes/modules/business.ts) | ✅ Canonical | Primary module exposing backend data |
| Executive Home composition | ✅ Canonical | Default landing workspace |
| Universal search (⌘K) | ✅ Canonical | Keyboard-first, all-object search |
| AI Copilot (context-aware sidebar) | ✅ Canonical | Embedded AI layer |
| Conversation workspace component | ✅ Canonical | Context assembly for conversations |
| Commitment workspace component | ✅ Canonical | Execution tracking |
| Object workspace component | ✅ Canonical | Generic object rendering |
| Session persistence (sessionStorage) | ✅ Canonical | Survives page refresh |
| Boot timeout + retry | ✅ Canonical | Founder never stuck on infinite spinner |
| Module registry (manifest-based discovery) | ✅ Canonical | Platform extension mechanism |
| CFO Q&A (app/for2/cfo) | 🔄 Merge into Canonical | AI capability, should be consumed by Copilot |
| Financial intelligence (app/for2/) | 🔄 Merge into Canonical | Finance domain, keep as module |
| Relationship API (app/relationship/) | 🔄 Merge into Canonical | Keep as backend module, expose via business module |
| Business onboarding (app/onboarding/) | 🔄 Expose | Routes exist, frontend not wired |
| Workspace policies (app/workspace/) | 🔄 Expose | Context-aware availability, not surfaced |
| Evidence engine (app/evidence/) | 🔄 Expose | Commitment workspace needs it |
| Organizational intelligence (app/organizational/) | 🔄 Expose | Multi-org AI context |
| app/organization/ | 🔄 Merge into organizational | Duplicate of app/organizational/ |
| app/decision/ | 🔄 Merge into decision_runtime | Duplicate decision implementation |
| app/decision_runtime/ | ✅ Keep Internal | Mark as canonical decision runtime |
| app/graph/ | 🔄 Merge into graph_universal | Duplicate graph implementation |
| app/graph_universal/ | ✅ Keep Internal | Mark as canonical graph runtime |
| app/kernel/ | 🔄 Deprecate | Superseded by app/shunya/ |
| app/shunya/ | 🔄 Keep Internal | Legacy kernel, not exposed to frontend |
| app/adapters/ | ✅ Canonical | OS pipeline adapter (sign_in, create_object) |
| app/authz/ | 🔄 Keep Internal | Authorization models, not frontend-facing |
| app/production/ | ✅ Keep Internal | Production identity repository (used by 20 tests) |
| app/temporal/ | 🔄 Keep Internal | Temporal runtime, not frontend-facing |
| app/orchestration/ | 🔄 Keep Internal | Orchestration runtime, not frontend-facing |
| app/intake/ | 🔄 Keep Internal | Data intake pipeline, not frontend-facing |
| app/communication/ | 🔄 Keep Internal | Communication channels, not frontend-facing |
| app/space/ | 🔄 Merge into founder | Space management, overlaps with FounderSpace |
| app/for1/ | 🔄 Keep Internal | Legacy HTML routes, keep for compatibility |
| app/for2/ | 🔄 Keep Internal | Legacy finance routes, keep for CFO Q&A |
| app/finance/ | 🔄 Keep Internal | Finance models, consumed by CFO Q&A |
| app/cognitive/ | 🔄 Keep Internal | Cognitive runtime, not frontend-facing |
| app/execution_intelligence/ | 🔄 Keep Internal | Execution AI, internal |
| app/learning_intelligence/ | 🔄 Keep Internal | Learning AI, internal |
| app/awareness/ | 🔄 Keep Internal | Context awareness, internal |
| app/collaboration/ | 🔄 Keep Internal | Collaboration, internal |
| app/cortex/ | 🔄 Keep Internal | Cortex runtime, internal |
| app/evidence/ | 🔄 Keep Internal | Evidence engine, internal |
| app/executive/ | 🔄 Keep Internal | Executive dashboard, internal |
| app/human_context/ | 🔄 Keep Internal | Human context, internal |
| app/intelligence/ | 🔄 Keep Internal | Intelligence runtime, internal |
| app/llm/ | 🔄 Keep Internal | LLM integration, internal |
| app/memory/ | 🔄 Keep Internal | Memory runtime, internal |
| app/planning/ | 🔄 Keep Internal | Planning runtime, internal |
| app/prediction/ | 🔄 Keep Internal | Prediction runtime, internal |
| app/privacy/ | 🔄 Keep Internal | Privacy controls, internal |
| app/relevance/ | 🔄 Keep Internal | Relevance engine, internal |
| app/watch/ | 🔄 Keep Internal | Watch/monitoring, internal |
| app/world/ | 🔄 Keep Internal | World engine, internal |
| app/acquisition/ | 🔄 Keep Internal | Customer acquisition, internal |
| app/artifact/ | 🔄 Keep Internal | Artifact storage, internal |
| app/assistant/ | 🔄 Keep Internal | Assistant, internal |
| app/automation/ | 🔄 Keep Internal | Automation, internal |
| app/brand/ | 🔄 Keep Internal | Brand, internal |
| app/context/ | 🔄 Keep Internal | Context, internal |
| app/document/ | 🔄 Keep Internal | Document, internal |
| app/execution/ | 🔄 Keep Internal | Execution, internal |
| app/growth/ | 🔄 Keep Internal | Growth, internal |
| app/inference/ | 🔄 Keep Internal | Inference, internal |
| app/knowledge/ | 🔄 Keep Internal | Knowledge, internal |
| app/learning/ | 🔄 Keep Internal | Learning, internal |
| app/runtime/ | 🔄 Keep Internal | Runtime adapter, internal |
| app/data/ | ❌ Remove after validation | Empty directory |

---

## Part 3: Canonical Identity Definitions

There is exactly one definition of each concept.

| Concept | Definition | Canonical Implementation |
|---------|-----------|------------------------|
| **Identity** | A person who uses SHUNYA. Has a name, email, password, and preferences. Belongs to one or more organizations. | `app/authz/models.py` → `Identity` (for auth) + `app/founder/models.py` → `FounderSpace.identity_id` (for space ownership) |
| **Founder** | The primary identity. The person who owns SHUNYA. Has the same attributes as an Identity but is the root user. | Same as Identity. The "founder" concept is a role, not a separate model. |
| **Organization** | A bounded business context. Contains objects, relationships, conversations, commitments, and a timeline. | `FounderSpace` with `space_type="organization"` |
| **Space** | A container for objects. The primary organizational unit. Spaces can be organizations, projects, or personal. | `FounderSpace` |
| **Object** | Any business entity. Generic record with a type, name, and JSON content. | `FounderObject` |
| **Relationship** | A named business connection between the organization and an external entity. | `BusinessRelationship` |
| **Conversation** | A series of messages attached to an object. Has a title, participants, and AI summary. | `FounderConversation` + `FounderMessage` |
| **Commitment** | A promise to complete work. Has progress, confidence, owner, deadline, and risks. | `FounderObject` with `object_type="commitment"` |

Everything else is an implementation detail.

---

## Part 4: Canonical Repository Migration

Every duplicated package has a migration path.

| Old Package | → | Replacement | Migration | Removal Condition |
|-------------|---|-------------|-----------|-------------------|
| `app/organization/` | → | `app/organizational/` | Merge files, update imports | After proving no caller depends on old path |
| `app/decision/` | → | `app/decision_runtime/` | Merge files, update imports | After proving no caller depends on old path |
| `app/graph/` | → | `app/graph_universal/` | Merge files, update imports | After proving no caller depends on old path |
| `app/kernel/` | → | `app/shunya/` | Deprecate, redirect callers | 6 months after v1.0 release |
| `app/space/` | → | `app/founder/` | Merge space routes into founder | After proving no caller depends on old path |
| `app/for1/` (HTML) | → | `app/founder/` (API) | Keep for legacy, no new development | After all HTML routes are replaced by API |
| `app/data/` | → | (delete) | Remove empty directory | Immediately |

No destructive cleanup without a migration path. Every deprecation must be announced with a clear timeline.

---

## Part 5: Canonical Frontend Exposure

Every production-ready backend capability must be exposed through the frontend.

| Backend Capability | Frontend Module | Frontend Component | Exposed? | Action |
|--------------------|-----------------|-------------------|----------|--------|
| Founder objects | business.ts | Executive Home | ✅ Yes | Already wired |
| Founder spaces | business.ts | — | ❌ No | Add workspace switching |
| Finance invoices | business.ts | — | ❌ No | Queried via /founder/objects instead |
| CFO Q&A | ModuleRegistry | AiCopilot | ✅ Yes | Already wired |
| Commitments | business.ts | Executive Home | ✅ Yes | Metrics + milestones panels |
| Conversations | business.ts | Conversation Workspace | ❌ No | Register conversation workspace |
| Timeline milestones | business.ts | InsightCard | ✅ Yes | Milestones panel in Executive Home |
| Onboarding API | — | — | ❌ No | Defer to post-v1.0 |
| Workspace policies | — | — | ❌ No | Defer to post-v1.0 |
| Evidence engine | — | — | ❌ No | Defer to post-v1.0 |

Capabilities intentionally kept internal: All AI runtimes, orchestration, temporal, graph, and kernel packages are internal infrastructure. They are not exposed to the frontend because they serve the backend, not the founder.

---

## Part 6: Canonical Experience — The Founder Journey

This section reconstructs the complete founder journey, faithfully implementing every approved constitutional principle.

### Journey: First Visit

1. Founder opens shunyaos.com
2. Cinematic introduction plays: dark background, "शून्य" appears, brief animation, tagline "One Operating System for Your Business"
3. After 4 seconds (or click), the introduction fades to the identity form
4. Form asks: Name, Email, Password
5. Founder submits → identity created → session saved → organization created (seeded demo data available)
6. Executive Home loads with live metrics from the demonstration environment

**Constitutional principles implemented:**
- Cinematic introduction (✅ Recovered)
- शून्य identity prominent (✅ Recovered)
- Founder-first onboarding (✅ Recovered)
- Calm, spacious design (✅ Recovered)

### Journey: Returning Founder

1. Founder opens shunyaos.com
2. Brief (1-second) shortened introduction animation
3. Login form shown immediately
4. Founder enters email and password
5. Session restored — same organization, same workspace context
6. Executive Home shows updated metrics and AI summary

**Constitutional principles implemented:**
- Session survives refresh (✅ Implemented)
- Returning founder experience (✅ Recovered)
- Continuous operation (✅ Implemented)

### Journey: Daily Operation

1. Executive Home loaded — metrics, milestones, next action, AI summary
2. Founder presses ⌘K → search overlay opens → types customer name → presses Enter
3. Customer workspace opens — identity panel, details panel, AI analysis
4. Founder opens related conversation — conversation workspace with messages, participants, linked objects, AI context
5. Founder creates commitment from conversation — commitment workspace with progress, confidence, blockers
6. Timeline updates automatically
7. Founder switches organization — workspace transforms, AI context shifts
8. Founder returns to Executive Home — overview is current

**Constitutional principles implemented:**
- Object-centric interface (✅ Implemented)
- AI as embedded layer (✅ Implemented)
- Calm workspace (✅ Recovered)
- One continuous OS (✅ Implemented)
- No page transitions (✅ Implemented)

---

## Part 7: Release Validation

SHUNYA v1.0 is complete only when:

1. A founder can arrive at shunyaos.com, understand what SHUNYA is, and create an identity — all without leaving the cinematic experience
2. After login, the Executive Home displays real data from the demonstration environment with no empty states, no placeholders, and no fake metrics
3. The founder can search any object (⌘K), open it, and work with it in a complete workspace
4. AI Copilot understands the workspace context automatically and provides useful insights
5. The founder can switch organizations and the workspace transforms correctly
6. The founder can sign out, return later, and find their session restored
7. Every keyboard shortcut works as advertised (⌘K, ⌘1-⌘9)
8. No constitutional principle is classified as "missing" — all are at least "partially implemented"
9. No duplicate implementations remain in the canonical exposure path
10. The demonstration environment can be re-seeded with a single command and produces identical results

---

*This document is the canonical specification for SHUNYA v1.0. No architectural or implementation detail overrides it. If a choice arises between what is easier to build and what is described here, this document wins.*