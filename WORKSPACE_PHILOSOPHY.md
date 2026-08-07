# Workspace Philosophy & Onboarding Redesign

**Directive:** Z-05 Article V-VI
**Purpose:** Redefine the workspace as intent-driven, not object-driven. Remove all object terminology from onboarding.
**Status:** Design Artefact

---

## Article V — Workspace Philosophy

### Current Model
```
Object → Workspace
```
The user creates an object (Customer, Invoice, Task). The workspace organizes around that object.

### New Model
```
Intent → Context → Relationships → Memory → Workspace
```
The user arrives with an intent. SHUNYA establishes context, surfaces relevant relationships and memory, and generates a workspace tailored to what the human is trying to accomplish.

---

### The Five-Layer Workspace Stack

#### Layer 1: Intent
What the human is trying to do right now.

| Intent Class | Example | Workspace Generated |
|-------------|---------|-------------------|
| **Find** | "What's the status of the Acme deal?" | Search + Context panel + Relevant records |
| **Create** | "Add a new customer" | Quick-create form (language layer) |
| **Review** | "Show me this quarter's revenue" | Dashboard with financial aggregation |
| **Act** | "Send the proposal to Beta LLC" | Communication composer + Document attachment |
| **Learn** | "Summarize what happened last month" | AI-generated brief from Events + Communications |
| **Decide** | "Should we approve this budget?" | Decision panel with context + recommendations |
| **Track** | "Monitor inventory levels" | Observation dashboard with alerts |
| **Plan** | "Schedule the project timeline" | Workflow editor + Calendar |

Intent is determined by:
1. What the user says (Language Layer)
2. What they clicked (navigation context)
3. What's pending (Memory — unresolved Commitments, overdue items)
4. Time patterns (Monday morning → review week; End of month → close invoices)

#### Layer 2: Context
What is relevant to this intent right now.

Context is built from:
- **Identity context:** Who the user is (role, permissions, active relationships)
- **Temporal context:** Time of day, day of week, season, fiscal period
- **Relational context:** Whom the user is interacting with (customer, team, family)
- **Domain context:** Which domain is active (business, personal, travel, healthcare)
- **Workflow context:** Where in a process is this (onboarding, closing, reviewing)
- **Historical context:** What happened last time (Memory retrieval)

**Example:**
> User (founder, Monday 9am) says "Review the week ahead"
> Context = { role: founder, time: Monday, domain: consulting, recent: Acme proposal, pending: 3 invoices }

#### Layer 3: Relationships
The connections that matter for this context.

SHUNYA surfaces:
- People involved (Identity relationships)
- Active commitments (what's due, what's pending)
- Recent events (meetings, calls, emails)
- Linked documents and knowledge
- Financial position (invoices, payments)

**Example output:**
> Relationships for "Acme Corp": John(contact, 4 emails last week), Proposal(due Friday), Invoice($12k overdue), Meeting(Tuesday)

#### Layer 4: Memory
What SHUNYA remembers about this context.

Memory types:
- **Episodic:** "We discussed pricing at the last meeting and agreed on a 15% discount"
- **Semantic:** "Acme prefers email communication and always pays net-30"
- **Procedural:** "For consulting engagements, we always start with a kickoff meeting and SOW"

Memory is built from past Events, Communications, Decisions, and Observations. It distinguishes SHUNYA from a passive database.

**Example:**
> Memory: "Acme Corp — last contact was 2 weeks ago. John mentioned they're considering our premium tier. Previous proposals were rejected on pricing. Discount threshold is 20%."

#### Layer 5: Workspace
The generated interface.

Composed from capabilities (Article XI) relevant to the intent + context + relationships + memory:

| Component | Source |
|-----------|--------|
| Executive summary | Memory + Events summary |
| Action items | Pending Commitments |
| Relationship health | Recent Events + Communications frequency |
| Alerts | Observations + Overdue Commitments |
| Quick actions | Capabilities for this context |
| AI suggestions | Language Layer + Memory analysis |
| Timeline | Upcoming Events |
| Documents | Linked Documents + Knowledge |

---

### Workspace Types

#### Intent Workspace (ephemeral)
Generated for a specific task. Disappears when intent is satisfied.
*Example: "Show me Acme's status" → temporary workspace with Acme context*

#### Domain Workspace (persistent)
The default workspace for a domain. Available until user switches domain.
*Example: Consulting workspace with client list, active engagements, pipeline*

#### Object Workspace (focused)
A workspace centered on a specific Record (Person, Commitment, Document).
*Example: Acme Corp workspace showing all linked Records*

#### Home Workspace (default)
The landing workspace. Shows overall status across all active domains.
*Example: Today's agenda, pending items, recent activity across business + personal*

---

## Article VI — Onboarding Redesign

### Current Flow (Z-05)
```
Homepage → Begin → Sign Up → Sign In → Identity → Organization → Team → Import → Workspace
```
Still uses "Create your first object" language in the Complete step.

### New Flow (Z-05 Ontology)

```
Homepage → Begin → Sign Up → Sign In → "How would you like to use SHUNYA?"

                                 ↓
                ┌────────────────┼────────────────┐
           Personal          My Business     Join Existing
           Workspace                        Company / Explore

                ↓                    ↓                    ↓
     Personal Setup          Business Info         Invitation /
     (goals, habits,    (company name,          Explore mode
      journal, etc.)     category, industry)

                ↓                    ↓                    ↓
           Connect / Import    Connect / Import     Optional setup
           (calendar, gmail,   (gmail, files,      (skip to workspace)
            files, skip)        team invite, skip)

                ↓                    ↓                    ↓
           PERSONAL             BUSINESS            JOINED / EXPLORE
           WORKSPACE            WORKSPACE           WORKSPACE
```

### Key Changes

1. **No "object" terminology anywhere.** The word "object" is removed from all onboarding screens.
2. **"Create your first object" → "How would you like to use SHUNYA?"**
3. **Personal Workspace** is a first-class option (not a reduced business workspace).
4. **Explore mode** — for users who want to try SHUNYA without committing to a use case.
5. **Business category** determines domain activation, not object types.
6. **Import/Connect** happens after identity, not after objects.
7. **Workspace arrives immediately** — no "complete" step with object summary.

### Onboarding Step Details

#### Step 1: Welcome + Role
```
"How would you like to use SHUNYA?"

🧑 Personal Workspace — For goals, habits, notes, finances, and personal productivity
🏢 My Business — Run your company with SHUNYA
🤝 Join an Existing Company — I have an invitation
🔍 Explore First — Let me look around
```

#### Step 2a: Personal Setup (if Personal)
```
"Tell SHUNYA about yourself"

First name, Last name
I want to track: [Goals] [Habits] [Finances] [Health] [Learning] [All of the above]
Connect: [Calendar] [Gmail] [Skip]
```

#### Step 2b: Business Info (if Business)
```
"Tell us about your business"

Company Name
Business Category (combobox — same 15 options)
Industry (combobox — same 17 options)
Country / Currency / Timezone
Connect: [Gmail] [Calendar] [Import files] [Skip for now]
```

#### Step 3: Invite / Skip
```
"Would you like to invite anyone?"

[Invite team members] — optional
[Skip — I'll do this later]
```

#### Step 4: Workspace Arrival
No "You're all set!" step with object summary. The workspace IS the arrival.

```
[Workspace loads directly — no intermediate complete screen]
```

---

### Onboarding Copy Changes

| Current (Z-05) | New (Z-05 Ontology) |
|----------------|-------------------|
| "Create your first object" | Removed entirely |
| "Your SHUNYA environment is ready" | "Your workspace is ready" |
| "Here's what we created" | Workspace loads directly |
| "You can always create more objects" | "You can always add more" |
| "Enter SHUNYA" | "Open Workspace" |
| Customer, Supplier, etc. | Never shown to user during onboarding |

---

### Explore Mode

For users who select "Explore First":

```
🔍 Explore Mode

SHUNYA creates a temporary workspace with:
- Sample data relevant to common business scenarios
- Pre-built relationships to demonstrate capabilities
- Active AI that answers "What can you do?"

No data is persisted until the user explicitly signs up.
Explore mode demonstrates the workspace experience without commitment.
```

---

*Next: Article VII-VIII — Department Capability Audit + Marketing Intelligence*