# FRONTEND EXECUTION CONSTITUTION — PHASE 2: COMMITMENT & EXECUTION RUNTIME

> **Status:** Architectural Blueprint — Ready for Implementation
> **Authority:** Extends Phase 1 (Living Workspace Architecture). This runtime binds Objects, Timelines, Conversations, AI, Tasks, Approvals, Evidence, and Outcomes into one living execution model. It does not replace anything from Phase 1 — it orchestrates what Phase 1 provides.
> **Constitutional Principle:** Objects are static. Commitments are alive. The frontend shall understand *why* work exists, not merely *what* records exist.

---

## CHAPTER 1 — COMMITMENT RUNTIME ARCHITECTURE

### 1.1 What Is a Commitment?

A commitment is a **living runtime entity representing business execution toward a specific outcome**. It is not a task list. It is not a project. It is a unified execution model that binds objects, conversations, AI observations, evidence, timelines, and outcomes into one coherent narrative.

A commitment answers: *What are we trying to accomplish? How close are we? What is blocking us? What should happen next?*

### 1.2 Commitment vs Object

| Dimension | Object (Phase 1) | Commitment (Phase 2) |
|-----------|-----------------|----------------------|
| Nature | Static record | Living execution |
| Identity | "Invoice #1024" | "Recover ₹4,50,000 from Priya Ventures" |
| State | Posted, paid, overdue | On track, at risk, blocked, completed |
| Relationships | FK to customer, proposal | Execution graph (objects + people + evidence) |
| AI role | Describe | Reason about fulfilment |
| Timeline | Chronological events | Progress narrative |
| Success | Record exists | Outcome achieved |

### 1.3 Commitment Runtime Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Commitment Runtime                          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Execution     │  │ Graph        │  │ Progress             │  │
│  │ State Machine│  │ Engine       │  │ Calculator           │  │
│  │ (active →     │  │ (object +    │  │ (confidence,         │  │
│  │  at_risk →    │  │  participant │  │  momentum, velocity, │  │
│  │  blocked →    │  │  resolution) │  │  risk)               │  │
│  │  completed)   │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Outcome      │  │ Blocker      │  │ Next Best            │  │
│  │ Resolver     │  │ Detector     │  │ Action Engine        │  │
│  │ (what        │  │ (what is     │  │ (what should         │  │
│  │  constitutes │  │  preventing  │  │  happen next?)       │  │
│  │  completion) │  │  progress?)  │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Integration Layer                             │   │
│  │  Object Runtime │ Timeline Runtime │ Conversation Runtime │   │
│  │  Intelligence Runtime │ Layout Engine │ Component Runtime │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.4 Commitment Lifecycle

```
Identify ──→ Define ──→ Active ──→ At Risk ──→ Blocked ──→ Resolved ──→ Closed
                │           │          │          │            │
                │           ├──→ On Track ──→ Completed ──→ Verified ──→ Closed
                │           │                                                
                │           └──→ Abandoned ──→ Closed                          
                │                                                             
                └──→ Rejected ──→ Closed                                      
```

**Identify:** A commitment is recognised (AI detects an overdue invoice pattern, user explicitly creates a commitment, system generates from proposal acceptance).

**Define:** Outcome, owner, participants, success criteria, deadline (if applicable). This is the minimum viable definition — commitments can be defined with as little as a name and an outcome.

**Active:** The commitment is being worked on. Progress is being made. Confidence is above 70%.

**At Risk:** Progress has stalled. Confidence dropped below 70%. The commitment may not meet its deadline. AI surfaces observations.

**Blocked:** Something external is preventing progress. A blocker is identified. The commitment cannot proceed without resolution.

**Resolved:** The outcome has been achieved (or a decision has been made to accept the current state). Pending verification.

**Completed:** Verified. Outcome confirmed. Evidence attached.

**Abandoned:** Work stopped without achieving the outcome. Reason captured.

**Closed:** Terminal state. The commitment enters the historical record.

### 1.5 Commitment State Model

```typescript
interface CommitmentState {
  identity: {
    id: string;
    name: string;           // "Recover ₹4,50,000 from Priya Ventures"
    outcome: string;        // "Full payment received"
    owner: string;          // User ID
    participants: string[]; // User IDs
    created: timestamp;
    deadline?: timestamp;
  };
  execution: {
    status: 'active' | 'on_track' | 'at_risk' | 'blocked' | 'completed' | 'abandoned' | 'closed';
    confidence: number;     // 0-100
    momentum: number;       // -1 to 1 (regressing vs progressing)
    velocity: number;       // Events per day
    waiting_on?: string;    // What is blocking
  };
  graph: {
    objects: CommitmentObject[];
    participants: CommitmentParticipant[];
    evidence: CommitmentEvidence[];
    blockers: CommitmentBlocker[];
  };
  outcomes: {
    definition: string;     // What success looks like
    verified?: boolean;
    verified_at?: timestamp;
    notes?: string;
  };
}
```

---

## CHAPTER 2 — EXECUTION GRAPH

### 2.1 Graph Structure

Every commitment maintains an execution graph — a directed graph of objects, participants, evidence, blockers, and outcomes that collectively represent the state of execution.

```
                    ┌─────────────────────┐
                    │    Commitment        │
                    │ "Recover ₹4,50,000"  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼────────┐ ┌────▼────┐ ┌─────────▼─────────┐
     │   Objects        │ │ People  │ │    Evidence        │
     │  ┌──────────┐   │ │ ┌─────┐ │ │  ┌──────────────┐ │
     │  │ Invoice  │◄──│ │ │Owner│ │ │  │Payment SS    │ │
     │  │ #1024    │   │ │ ├─────┤ │ │  ├──────────────┤ │
     │  ├──────────┤   │ │ │Team │ │ │  │Email thread  │ │
     │  │ Proposal │   │ │ └─────┘ │ │  ├──────────────┤ │
     │  │ #45      │   │ │         │ │  │Approval docs │ │
     │  └──────────┘   │ │         │ │  └──────────────┘ │
     └─────────────────┘ └─────────┘ └────────────────────┘
              │
              ├────────────────────┐
              │                    │
     ┌────────▼────────┐ ┌─────────▼─────────┐
     │   AI Observations│ │    Blockers        │
     │  ┌──────────────┐│ │  ┌──────────────┐ │
     │  │Payment       ││ │  │Customer not  │ │
     │  │pattern       ││ │  │responding    │ │
     │  │shifted       ││ │  └──────────────┘ │
     │  └──────────────┘│ │                   │
     └─────────────────┘ └───────────────────┘
```

### 2.2 Graph Rules

🟢 Objects in the graph are references — they are not owned by the commitment. The same invoice can participate in multiple commitments (collection commitment + revenue recognition commitment).

🟢 Participants are users with roles: owner, contributor, observer, approver.

🟢 Evidence items are references to the Evidence Engine (from FOR-2D.4). A payment screenshot is evidence. A signed contract is evidence. An email confirmation is evidence.

🟢 AI observations are generated by the Intelligence Runtime and attached to the commitment. They update as new data arrives.

🟢 Blockers are explicit. A blocker must have: what is blocked, why, who can unblock it, expected resolution time.

### 2.3 Graph Mutations

When an object in the graph changes (invoice status updates, payment arrives), the Commitment Runtime receives a notification from the Object Runtime and updates the execution state. The user sees the graph update in real time.

---

## CHAPTER 3 — COMMITMENT WORKSPACE

### 3.1 Workspace Layout

The Commitment Workspace uses a custom layout from the Layout Engine:

```
┌─────────────────────────────────────────────────────────────┐
│  Commitment: Recover ₹4,50,000 from Priya Ventures          │
│  Status: At Risk  │  Confidence: 65%  │  Owner: Anjali      │
├──────────────────────┬──────────────────────────────────────┤
│  Execution Graph     │  Progress Narrative                   │
│  ┌──────┐ ┌──────┐   │  Mar 12: Invoice sent               │
│  │Inv   │ │Pay   │   │  Mar 15: Follow-up sent             │
│  │#1024 │ │Pending│  │  Mar 20: Customer promised payment  │
│  └──────┘ └──────┘   │  Mar 25: ⚠️ Payment not received    │
│  ┌──────┐ ┌──────┐   │  Mar 26: Escalated to finance      │
│  │AI    │ │Blocker│   │                                      │
│  │Obs   │ │:No    │   │  Next: Call customer today         │
│  │      │ │Response│  │                                      │
│  └──────┘ └──────┘   │                                      │
├──────────────────────┴──────────────────────────────────────┤
│  AI Insight: Payment pattern has shifted from 7 days to 25  │
│  days. This commitment is at risk of missing the 30-day     │
│  target. Recommended action: Escalate to relationship owner.│
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Workspace Sections

🟢 **Header:** Commitment name, status badge, confidence meter, owner avatar.

🟢 **Execution Graph:** Visual graph of objects, participants, evidence, blockers. Interactive — click an object to open its workspace.

🟢 **Progress Narrative:** Timeline events filtered and ordered by relevance to this commitment. Each event includes a note about how it moved the commitment forward.

🟢 **Next Best Action:** AI-generated suggestion based on current state. "Call customer today" + one-click action button.

🟢 **AI Insight Panel:** Full AI analysis of the commitment's health, risks, and recommendations.

🟡 **Blocker Panel:** Only visible when blockers exist. Shows what is blocked, why, who can unblock, and escalation options.

🟡 **Evidence Feed:** Only visible when evidence has been attached. Shows payment proofs, signed documents, communication logs.

---

## CHAPTER 4 — EXECUTION TIMELINE

### 4.1 Timeline Mode

The Timeline Runtime (Phase 1) gains an execution mode. In this mode, events are not merely chronological — they are narrative. Each event includes a "commitment impact" indicator:

| Impact | Visual | Meaning |
|--------|--------|---------|
| Positive | Green dot | This event advanced the commitment |
| Neutral | Grey dot | This event maintained the current state |
| Negative | Red dot | This event regressed the commitment |
| Critical | Red dot + pulse | This event threatens the commitment outcome |

### 4.2 Event Attribution

Every event in the execution timeline includes:

- **What happened:** "Payment of ₹4,50,000 received"
- **Commitment impact:** "Positive — commitment moved from At Risk to Completed"
- **Evidence reference:** Link to payment screenshot (if evidence was uploaded)
- **AI observation:** "Payment received within the expected window. Confidence restored to 95%."

---

## CHAPTER 5 — AI EXECUTION LAYER

### 5.1 Execution-Aware Intelligence

The Intelligence Runtime (Phase 1) gains execution awareness. Instead of isolated observations about individual records, AI reasons about fulfilment.

### 5.2 AI Commitment Insights

| Situation | AI Says | Confidence |
|-----------|---------|------------|
| Invoice overdue | "Invoice #1024 is 5 days overdue. This has reduced commitment confidence from 85% to 65%. The commitment is now At Risk." | High |
| Customer responded | "Customer acknowledged the invoice. Confidence restored to 75%. Commitment remains At Risk until payment clears." | Medium |
| Payment received | "Payment of ₹4,50,000 received. Commitment confidence is 100%. Ready for verification." | High |
| No activity for 7 days | "No progress on this commitment in 7 days. Momentum is negative. Recommended: assign a new owner or reassess the approach." | Medium |
| Multiple commitments affected | "Three commitments involving Priya Ventures are now At Risk. The common blocker appears to be unresolved invoice #1022. Resolving that may unblock all three." | Medium |

### 5.3 Proactive Notifications

The Intelligence Runtime generates notifications when:

- A commitment's confidence drops below 70%
- A commitment has no activity for 5+ days
- A commitment is approaching its deadline with <50% confidence
- A blocker has been unresolved for 3+ days
- A commitment's outcome has been achieved (ready for verification)

---

## CHAPTER 6 — PROGRESS RUNTIME

### 6.1 Constitutional Progress States

Progress is not percentage complete. Progress is a multidimensional evaluation:

| Dimension | Range | Meaning |
|-----------|-------|---------|
| Confidence | 0-100 | How likely is the commitment to succeed? |
| Momentum | -1 to 1 | Is progress accelerating (positive) or stalling (negative)? |
| Velocity | Events/day | How much activity is happening? |
| Risk | 0-10 | How much is at stake if this commitment fails? |
| Waiting | boolean | Is the commitment waiting on an external party? |
| Blocked | boolean | Is there an active blocker? |
| Completed | boolean | Has the outcome been achieved? |

### 6.2 State Classification

The Progress Runtime classifies commitments into one of these states based on the constitutional dimensions:

| State | Confidence | Momentum | Blocked | Waiting |
|-------|-----------|----------|---------|---------|
| On Track | ≥70% | ≥0 | No | No |
| At Risk | <70% | Any | No | No |
| Stalled | Any | <0 for 5+ days | No | Any |
| Blocked | Any | Any | Yes | Any |
| Completed | 100% | Any | No | No |
| Abandoned | 0% | 0 | No | No |

### 6.3 Progress Visualization

Progress is visualized as a **confidence meter** — a simple horizontal bar from 0-100 with colour coding (green ≥70%, amber 40-69%, red <40%). Below it, a momentum indicator (upward/downward arrow + number of days trending).

No pie charts. No donut charts. No percentage circles.

---

## CHAPTER 7 — CROSS-WORKSPACE AWARENESS

### 7.1 Commitment Awareness in Object Workspaces

Every object workspace (Phase 1) gains a **Commitments** panel. This panel shows:

- Which commitments include this object
- The status of those commitments
- Whether this object is a blocker for any commitment
- One-click navigation to the commitment workspace

**Example (Invoice workspace):**
```
Commitments:
  Recover ₹4,50,000 from Priya Ventures  → At Risk (confidence: 65%)
  Q1 Revenue recognition                  → On Track (confidence: 85%)
```

### 7.2 Commitment Awareness in Conversation

When discussing an object that participates in a commitment, the conversation runtime surfaces commitment context:

User: "What's the status of invoice #1024?"
SHUNYA: "Invoice #1024 is overdue by 5 days. This is affecting the commitment 'Recover ₹4,50,000 from Priya Ventures' which is now At Risk (confidence: 65%). Would you like to escalate?"

### 7.3 Commitment Awareness in Timeline

Timeline events from objects that participate in commitments are tagged with commitment IDs. The user can filter timeline by commitment to see all events relevant to a specific execution.

---

## CHAPTER 8 — EXECUTIVE VIEW

### 8.1 Executive Commitment Dashboard

The executive view aggregates commitments across the organisation:

```
┌────────────────────────────────────────────────────────────┐
│  Executive Commitment Summary                               │
├────────────────────────────────────────────────────────────┤
│  ● On Track: 12    ● At Risk: 5    ● Blocked: 2           │
│  ⚠ Completed this week: 3  ▲ Confidence: 72% (stable)     │
├────────────────────────────────────────────────────────────┤
│  Commitments at Risk                                        │
│  ├── Recover ₹4,50,000 — Priya Ventures (65%, 5d overdue)  │
│  ├── Onboard new hire — (40%, waiting on IT)               │
│  ├── Q1 campaign launch — (55%, blocked by budget)         │
│  └── Resolve support ticket #892 — (30%, no response)      │
├────────────────────────────────────────────────────────────┤
│  Recently Completed                                         │
│  ├── Vendor contract renewal — Completed yesterday         │
│  ├── Q4 financial close — Completed, verified              │
│  └── Customer onboarding — Completed, 3 new deals          │
├────────────────────────────────────────────────────────────┤
│  AI Insight: Two commitments involving Priya Ventures are  │
│  at risk. Consider consolidating ownership under one       │
│  relationship manager.                                     │
└────────────────────────────────────────────────────────────┘
```

### 8.2 Executive Actions

From the executive view, the user can:
- Click any commitment to open its workspace
- Reassign ownership
- Escalate blocked commitments
- View trend (confidence over time)
- Export commitment summary

---

## CHAPTER 9 — RELATIONSHIP TO EXISTING RUNTIMES

### 9.1 Integration Points

| Phase 1 Runtime | Role in Phase 2 |
|-----------------|-----------------|
| **Workspace Runtime** | Hosts commitment workspaces as a new workspace type. Commitment workspaces follow the same lifecycle (create, load, hydrate, active, suspend, resume, destroy). |
| **Object Runtime** | Supplies objects that participate in commitments. The Commitment Runtime subscribes to object changes. When an object updates, the graph updates. |
| **Timeline Runtime** | Supplies chronological evidence. Execution mode adds commitment-impact indicators. |
| **Conversation Runtime** | Supplies contextual discussions. Commitment-aware conversation surfaces execution context. |
| **Intelligence Runtime** | Gains execution awareness. AI reasons about fulfilment, not isolated records. Generates commitment insights. |
| **Layout Engine** | Gains a commitment layout (Chapter 3). |
| **Component Runtime** | Gains commitment components (Chapter 11). |
| **Animation Runtime** | No changes — commitment components use the existing animation intent model. |
| **Design Token Runtime** | No changes — commitment components use existing tokens. |

### 9.2 No Duplication

🟢 The Commitment Runtime does not store objects, timelines, conversations, or AI state. It references them. When an object is updated, the Object Runtime notifies the Commitment Runtime. The Commitment Runtime updates its graph reference and recalculates progress. Data ownership remains in the Phase 1 runtimes.

---

## CHAPTER 10 — UNIVERSAL COMMITMENT MODEL

### 10.1 Business-Agnostic Design

The Commitment Runtime contains zero business-specific logic. The same runtime handles:

- Collect a payment (Finance)
- Close a sale (CRM)
- Onboard an employee (HR)
- Fulfil an order (Operations)
- Launch a campaign (Marketing)
- Implement a project (PM)
- Resolve a support ticket (Support)
- Renew a contract (Legal)
- Complete a procurement (Procurement)

The runtime represents **execution itself** — not any specific industry, department, or workflow.

### 0. Commitment Template

```typescript
interface CommitmentTemplate {
  name: string;
  outcome: string;
  defaultConfidence: number;    // Initial confidence when created
  suggestedParticipants: string[];
  requiredEvidence?: string[];  // What evidence constitutes completion
  aiPrompt?: string;           // How AI should reason about this type
}
```

Templates are declarative. They are not code. New commitment types are added via configuration.

---

## CHAPTER 11 — COMPONENT LIBRARY ADDITIONS

### 11.1 New Components

| Component | Purpose | Appears In |
|-----------|---------|------------|
| CommitmentSummary | Name + status + confidence + owner | Commitment workspace, executive view, object workspace |
| ProgressBar | Horizontal confidence meter (0-100, colour-coded) | Commitment workspace, executive view, sidebar |
| MomentumIndicator | Up/down arrow + days trending | Commitment workspace, executive view |
| ExecutionGraph | Interactive visual graph of objects + participants + blockers | Commitment workspace |
| BlockerList | List of active blockers with resolution info | Commitment workspace, executive view |
| RiskPanel | Risk assessment + factors | Commitment workspace |
| EvidenceFeed | Chronological evidence items | Commitment workspace |
| NextBestAction | AI-suggested action + one-click button | Commitment workspace, dashboard |
| CommitmentTimeline | Timeline in execution mode (events with commitment impact) | Commitment workspace |
| OutcomeSummary | What was achieved, verified, evidence | Commitment workspace (completed) |
| ConfidenceTrend | Sparkline of confidence over time | Executive view |
| CommitmentCard | Compact card for commitment lists | Executive view, sidebar, search results |

### 11.2 Component States

All commitment components implement the 6-state lifecycle from Phase 1: skeleton, empty, content, error, loading more, updating.

---

## CHAPTER 12 — FRONTEND GOVERNANCE

### 12.1 Directory Additions

```
src/runtimes/
├── commitment/          # NEW — Commitment Runtime
│   ├── engine.ts        # State machine, lifecycle
│   ├── graph.ts         # Execution graph management
│   ├── progress.ts      # Confidence, momentum, velocity calculation
│   ├── integration.ts   # Subscriptions to Object, Timeline, Intelligence runtimes
│   └── types.ts         # Commitment types
├── ... (existing runtimes unchanged)
src/layouts/
├── commitment.ts        # NEW — Commitment layout
src/components/
├── commitment/          # NEW — 12 commitment components
│   ├── summary.tsx
│   ├── progress-bar.tsx
│   ├── momentum.tsx
│   ├── execution-graph.tsx
│   ├── blocker-list.tsx
│   ├── risk-panel.tsx
│   ├── evidence-feed.tsx
│   ├── next-best-action.tsx
│   ├── timeline.tsx
│   ├── outcome-summary.tsx
│   ├── confidence-trend.tsx
│   └── commitment-card.tsx
```

### 12.2 No Parallel State

🟢 The Commitment Runtime does not introduce a new state management system. It integrates with the existing runtime architecture. State flows: Commitment Runtime → shared state layer → components. No Redux store. No context-based state.

### 12.3 Performance

Commitment workspaces follow the same performance targets as Phase 1:
- Identity frame: 0ms (cached)
- Graph load: <200ms
- Progress calculation: <50ms
- AI insight: <100ms (cached) or <3s (generated)

---

## RATIFICATION STATEMENT

This Frontend Execution Constitution — Phase 2 introduces the Commitment Runtime as a first-class frontend entity.

Commitments are now living runtime entities.
Every object can participate in one or more commitments.
AI reasons about fulfilment instead of isolated records.
Executives can understand organisational execution without inspecting individual objects.
The runtime remains completely business-agnostic.
The architecture integrates seamlessly with Phase 1 — no runtimes were replaced, no state was duplicated, no responsibility was moved.

The frontend architecture now fully mirrors SHUNYA's execution-centric backend.

Implementation may proceed.

---

*Frontend Execution Constitution — Phase 2: Ready for ratification and implementation.*