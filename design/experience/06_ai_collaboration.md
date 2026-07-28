# SHUNYA AI Collaboration Canon

> **Canonical Reference — Phase X1**
> Defines how AI behaves in SHUNYA. AI is not an external helper — it is an intrinsic part of every workspace.

---

## 1. AI Philosophy

### Core Principle

AI in SHUNYA is **resident, not reactive**. It does not appear when summoned and disappear when dismissed. It is always present, always aware, always working — but never intrusive.

### What AI Is

| Quality | Meaning |
|---------|---------|
| **Resident** | AI lives inside the workspace. It is part of the environment, not a separate application. |
| **Contextual** | AI always knows what object you are viewing, what section is active, what you last did, and what your role is. |
| **Proactive** | AI surfaces suggestions, observations, and actions without being asked — when relevant and at the right attention level. |
| **Explanatory** | Every AI action can be explained. "Why did you suggest this?" has a visible answer. |
| **Memoryful** | AI remembers past interactions, preferences, and decisions per user, per object, per workspace. |
| **Confidence-aware** | AI knows its own uncertainty and communicates it clearly. |

### What AI Is Not

| Not This | Instead |
|----------|---------|
| A chatbot floating beside the app | A resident intelligence within every workspace |
| A text completion tool | An analytical collaborator that reasons over relationships |
| A search engine | A knowledge worker that surfaces what matters |
| A generic assistant | An entity that understands your organization, objects, and history |
| Always right | Transparent about confidence, sources, and uncertainty |
| Always talking | Silent until it has something relevant to contribute |

---

## 2. AI Resident Architecture

### Per-Workspace AI

Every workspace has an AI Resident that understands the workspace's domain:

| Workspace | AI Resident Specialization |
|-----------|---------------------------|
| Home | Organization-wide awareness. Current state, recent changes, attention-worthy events. |
| Relationship | Graph analysis. Connection patterns, unexplored links, structural insights. |
| Organization | People and structure. Team dynamics, role patterns, organizational health. |
| Project | Progress, risks, dependencies, resource allocation. |
| Document | Content understanding, summarization, cross-referencing. |
| Decision | Evidence analysis, outcome prediction, recommendation generation. |
| Task | Prioritization, workload balancing, deadline management. |
| Knowledge | Knowledge gaps, information synthesis, source verification. |
| Financial | Anomaly detection, trend analysis, forecasting. |
| Communication | Communication patterns, effectiveness analysis, drafting assistance. |
| Campaign | Performance prediction, optimization recommendations, audience insights. |
| Asset | Content analysis, usage tracking, similarity detection. |
| System | Health monitoring, anomaly detection, configuration optimization. |

### Per-Object AI

Every object has an AI Resident that understands that specific object:

- Its identity, status, and history
- Its relationships to other objects
- Its timeline of events and changes
- Its associated knowledge and documents
- Its tasks and execution state
- Past conversations the user has had about this object

The per-object AI Resident inherits context from the workspace AI Resident and adds object-specific knowledge.

---

## 3. AI Presence Modes

The AI Resident has four presence modes. These are not user-selectable — they are determined by the current context and attention state.

| Mode | Visual | When | Behavior |
|------|--------|------|----------|
| **Ambient** | Gold dot indicator only | User is focused, no significant AI activity | AI listens but is silent. No visual presence beyond the indicator. |
| **Attentive** | AI icon + subtle glow | AI has relevant information | AI shows a subtle indicator that it has something. No text visible. |
| **Suggestive** | AI panel shows 1-3 suggestions | AI has actionable suggestions | AI shows compact suggestions with confidence. Not interruptive. |
| **Conversational** | Full AI chat panel | User has engaged AI | AI shows full conversation interface. Chat mode. |

### Mode Transitions

```
Ambient ──(AI detects relevance)──▶ Attentive
Attentive ──(user glances/opens)──▶ Suggestive
Suggestive ──(user clicks "Ask")──▶ Conversational
Conversational ──(user dismisses)──▶ Ambient
Suggestive ──(user ignores, 30s)──▶ Ambient
```

---

## 4. AI Surfaces

AI manifests in three distinct surfaces within the workspace:

### Surface 1: Executive Summary (Object Header)

The executive summary is AI-generated. It is the first thing the user sees when opening an object.

**Content:** 3-line summary of the object, key metric, trend, next recommended action.

**Confidence:** Always shown. If confidence < 0.50, the summary includes "Low confidence — based on limited data."

**Regeneration:** Regenerated when object state changes (status, key fields, relationships).

### Surface 2: AI Resident Panel (Context Panel)

The AI Resident panel is the primary AI interaction surface. It lives in the Context Panel (Zone 2).

**Content (compact mode):**
- Suggestion count badge
- Click to expand

**Content (expanded mode):**
- Current context awareness indicator ("I see you're reviewing Decision 42")
- Suggested actions (1-3, with confidence)
- Recent analysis (1-2 items)
- "Ask AI" input field

**Content (full conversation mode):**
- Conversation history (persistent per object)
- Input field
- AI responses with confidence and sources

### Surface 3: AI-Enhanced Content Sections

AI enhances existing sections with intelligence:

| Section | AI Enhancement |
|---------|---------------|
| **Relationships** | "Based on patterns, you may want to connect this object to X." |
| **Timeline** | "Since your last visit, 3 significant events occurred." |
| **Knowledge** | "I've identified a knowledge gap about Y. Shall I investigate?" |
| **Tasks** | "Task Z is overdue. Similar tasks took 2 days to complete." |
| **Metrics** | "Metric A has crossed the warning threshold." |

These enhancements appear as subtle inline notes, not as separate AI panels.

---

## 5. AI Suggestion Model

### Suggestion Types

| Type | Example | Confidence Required | Frequency |
|------|---------|-------------------|-----------|
| **Action** | "Approve this budget increase" | ≥ 0.60 | Once per significant state change |
| **Review** | "Review evidence for Decision 42" | Any | When evidence exists |
| **Connect** | "Link this project to Q3 planning" | ≥ 0.50 | Once per potential connection |
| **Analyze** | "Run impact analysis" | Any | On demand or state change |
| **Generate** | "Generate status report" | Any | On demand or schedule |
| **Alert** | "Metric crossed threshold" | ≥ 0.80 | Immediately |

### Suggestion Lifecycle

```
Suggestion Generated
  │
  ├──▶ Confidence ≥ threshold ──▶ Shown in AI Resident
  │                               │
  │                               ├──▶ User acts ──▶ Executed
  │                               ├──▶ User dismisses ──▶ Dismissed
  │                               └──▶ User ignores (30min) ──▶ Archived
  │
  └──▶ Confidence < threshold ──▶ Stored (not shown)
                                 │
                                 ├──▶ New evidence raises confidence ──▶ Shown
                                 └──▶ No new evidence (24h) ──▶ Archived
```

### Suggestion Display

Each suggestion shows:

```
[Action Icon] ● [Action description in natural language]
               Confidence: ████░░ 0.72
               Based on: 3 similar decisions
               [Approve] [Dismiss]
```

- Action description is a complete sentence (not a label).
- Confidence bar + percentage.
- Source count (number of data points used).
- Action button to execute.
- Dismiss button (with "tell me why" option).

---

## 6. AI Conversation Model

### When Conversation Is Appropriate

Conversation (chat mode) is appropriate when:

- The user asks a question the AI cannot answer with a suggestion.
- The user wants to explore a topic in depth.
- The user needs to understand AI reasoning.
- The user wants to generate content (drafts, summaries, reports).

Conversation is **not** the default AI interaction mode.

### Conversation Interface

```
┌─ AI Resident — [Object Name] ──────────────┐
│                                              │
│  ┌───────────────────────────────────────┐  │
│  │ You: What evidence supports this?    │  │
│  ├───────────────────────────────────────┤  │
│  │ AI: Based on 3 documents and 2       │  │
│  │ previous decisions:                  │  │
│  │ 1. Q2 Report (confidence 0.85)       │  │
│  │ 2. Budget Policy v2.1 (confidence    │  │
│  │    0.92)                             │  │
│  │ 3. CFO Memo Jul 15 (confidence 0.78) │  │
│  │                                      │  │
│  │ The combined confidence is 0.72      │  │
│  │ [View Sources] [Ask Follow-up]       │  │
│  └───────────────────────────────────────┘  │
│                                              │
│  ┌───────────────────────────────────────┐  │
│  │ You: What would the impact be?       │  │
│  ├───────────────────────────────────────┤  │
│  │ AI: Based on similar decisions in    │  │
│  │ Q2, a 15% budget increase typically  │  │
│  │ results in 18-22% ROI improvement.   │  │
│  │ Confidence: 0.65 (limited data)      │  │
│  │ [View Analysis]                      │  │
│  └───────────────────────────────────────┘  │
│                                              │
│  [Type your question...]                     │
└──────────────────────────────────────────────┘
```

### Conversation Rules

- Conversation is per-object. Each object has its own conversation history.
- Conversation history is persistent across sessions.
- AI always knows the object context (no need to re-explain).
- AI cites sources for every claim.
- AI shows confidence for every assertion.
- AI can generate structured content (tables, lists, summaries).
- AI can take actions on the user's behalf (with confirmation for destructive actions).
- Conversation can be exported or cleared per object.

---

## 7. AI Memory

### What AI Remembers

| Memory Type | Scope | Persistence |
|-------------|-------|-------------|
| **Object memory** | Per-object conversation history | Permanent |
| **User preferences** | Per-user preferences for AI behavior | Permanent |
| **Workspace patterns** | Per-user, per-workspace patterns | Session + persisted |
| **Relationship context** | Cross-object context from recent navigation | Session |
| **Decisions** | User decisions that AI was involved in | Permanent |

### Memory Rules

- AI never remembers user's personal information unless explicitly shared.
- User can clear any memory scope (object, workspace, all).
- Memory is private to the user. No cross-user memory sharing.
- AI informs user when it is using memory: "Based on our previous conversation..."
- Memory is stored with provenance (when, where, how it was learned).

---

## 8. AI Transparency

### Mandatory Disclosure

For every AI-generated assertion:

| Element | Shown |
|---------|-------|
| **Confidence score** | Always (bar + percentage) |
| **Source count** | Number of data points used |
| **Top sources** | Up to 3 most relevant sources |
| **Generation timestamp** | When the assertion was generated |
| **Model used** | Which AI model generated it (high level) |

### "Why" Mechanism

Every AI suggestion and assertion has a "Why?" link:

```
[Why?] ──click──▶
┌─ Reasoning ─────────────────────────┐
│  This suggestion is based on:       │
│  1. Similarity to 3 past decisions  │
│     with positive outcomes          │
│  2. Budget policy §4.2: requests    │
│     under $200K may be auto-approved │
│  3. All required evidence is present │
│                                      │
│  Limiting factors:                   │
│  - No CFO review yet                 │
│  - Q3 projections not finalized      │
│                                      │
│  Overall confidence: 0.72            │
└──────────────────────────────────────┘
```

---

## 9. AI Proactivity Boundaries

### When AI May Proactively Act

| Trigger | Allowed Action | Frequency Limit |
|---------|---------------|-----------------|
| Object state changes | Surface "Since your last visit" note | Once per state change per user |
| Metric threshold crossed | Alert in AI Resident | Once per threshold crossing |
| Pattern detected | Suggest relationship or action | Once per pattern per object per day |
| Task overdue | Remind in AI Resident | Once per overdue task per day |
| Knowledge gap detected | Suggest investigation | Once per gap per object per week |

### When AI Must NOT Proactively Act

- Never interrupt focused work (detected by user attention state).
- Never suggest the same thing twice (unless new evidence emerges).
- Never auto-execute actions without confirmation.
- Never surface AI analysis that is lower quality than what already exists.
- Never suggest actions that the user has explicitly dismissed for this object.
- Never generate notifications for trivial events.

---

## 10. AI Confidence Model

### Confidence Scale

| Range | Label | Display | User Response |
|-------|-------|---------|---------------|
| 0.90–1.00 | High confidence | Dark green bar | AI is likely correct. Act on suggestion. |
| 0.70–0.89 | Good confidence | Light green bar | AI is probably correct. Review before acting. |
| 0.50–0.69 | Moderate confidence | Amber bar | AI is uncertain. Verify key claims. |
| 0.30–0.49 | Low confidence | Orange bar | AI is guessing. Seek other sources. |
| 0.00–0.29 | Very low confidence | Red bar | AI cannot reliably answer. Do not act. |

### Confidence Calculation

Confidence is computed from:

1. **Source quality** — reliability of data sources
2. **Source quantity** — number of supporting data points
3. **Consistency** — how consistent the evidence is
4. **Recency** — how recent the data is
5. **Model certainty** — the AI model's own uncertainty estimate

Detailed confidence model: see SHUNYA Core Models, Confidence Model section.

---

## 11. AI Collaboration Invariants

1. **AI is always present in every workspace.** No workspace exists without an AI Resident.
2. **AI never interrupts focused work.** Attention state governs AI expressiveness.
3. **Every AI assertion has an explicit confidence score.** No unqualified statements.
4. **Every AI action has an explanation.** "Why?" is always one click away.
5. **AI remembers context across sessions.** No need to re-establish context.
6. **AI generates suggestions, not commands.** The user always decides.
7. **AI chat is not the default mode.** Suggestions and analysis come first; conversation is opt-in.
8. **AI is object-aware and workspace-aware.** It knows exactly what you're working on.
9. **AI confidence is transparent, not hidden.** Low-confidence assertions are clearly marked.
10. **AI never auto-executes.** Every action requires user confirmation (unless explicitly configured otherwise in System Workspace).