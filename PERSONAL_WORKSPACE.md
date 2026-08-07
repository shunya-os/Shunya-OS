# Personal Workspace Specification

**Directive:** Z-05 Article IX
**Purpose:** Personal workspace as a first-class operating system — not a reduced Business Workspace.
**Status:** Design Artefact

---

## Design Principles

1. **Personal first.** Designed for a single human. No organizational hierarchy, no departments, no employees.
2. **Life-centric.** Covers goals, habits, health, learning, finances, relationships, travel, home, projects, ideas.
3. **No business framing.** No "customers", "invoices", "deals". The user is a person, not a company.
4. **Memory-driven.** The workspace gets better as SHUNYA learns the person's patterns, preferences, and priorities.
5. **Private by default.** Personal data is isolated. Sharing is opt-in, per-item, with explicit identity.

---

## User Persona

"The user is an individual who wants to organize their life, not run a business. They may also use SHUNYA for business — but the personal workspace is independent."

**Example users:**
- A professional managing career, learning, health, and finances
- A parent tracking family activities, children's schedules, home maintenance
- A student managing courses, assignments, research, and social life
- A creative tracking ideas, projects, inspirations, and collaborations

---

## Ontology Mapping for Personal

| Personal Concept | Universal Ontology |
|-----------------|-------------------|
| Me | Identity(Person, type=self) |
| Goals | Commitment(promise about future state) |
| Habits | Commitment(recurring) + Events |
| Journal | Document + Memory |
| Notes | Document (note) |
| Reading list | Knowledge + Commitment(reading) |
| Learning | Knowledge + Events(courses) + Commitments(certification) |
| Health | Observations(vitals, mood) + Events(workouts, appointments) |
| Fitness | Events(workouts) + Observations(metrics) + Commitments(goals) |
| Family | Organization(family) + Relationships(spouse, parent, child) |
| Finances | Financial Records(income, expenses, budget, savings) + Assets |
| Home | Place + Assets(home, appliances, vehicles) + Events(maintenance) |
| Travel | Events(trips) + Commitments(bookings) + Place(destinations) |
| Projects | Commitment(project) + Events + Documents + Tasks |
| Ideas | Knowledge(idea) + Document |
| Reminders | Commitment(reminder) with Event(alert) |
| Calendar | Events(scheduled) + Commitments(appointments) |
| Documents | Document(files, photos, records) |
| Contacts | Person + Relationships |

---

## Personal Workspace Dashboard

```
┌──────────────────────────────────────────────────┐
│  Good morning, [Name]  │  ☀ 72°  │  Jul 15      │
│──────────────────────────────────────────────────│
│  TODAY                                                │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │
│  │ 3    │ │ 2    │ │ 1    │ │ Done │ │ 87% │      │
│  │Tasks │ │Events│ │Habits│ │ 5/6  │ │Goals│      │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘      │
│──────────────────────────────────────────────────│
│  SCHEDULE                                           │
│  09:00  Yoga (habit)                                │
│  10:30  Dentist appointment (health)                │
│  14:00  Review Q2 learning goals                    │
│  18:00  Dinner with Sarah (family)                  │
│──────────────────────────────────────────────────│
│  RECENT NOTES                                       │
│  📝 Book ideas for summer reading list  │ 2h ago   │
│  💡 App concept for habit tracking      │ 1d ago   │
│  🏠 Need to fix the kitchen faucet      │ 3d ago   │
│──────────────────────────────────────────────────│
│  AI SUGGESTIONS                                     │
│  "You haven't journaled in 3 days. Want to          │
│   reflect on this week?"                            │
│  "Your reading goal is at 40%. 3 books left         │
│   this month. Here are recommendations based        │
│   on your interests."                               │
└──────────────────────────────────────────────────┘
```

---

## Personal Modules (Composed from Capabilities)

### Goals
- Life goals (long-term: "Run a marathon", "Learn Spanish")
- Quarterly objectives (medium-term: "Save $5k", "Read 12 books")
- Weekly targets (short-term: "Exercise 3x", "Finish chapter 5")
- Connected to Habits, Events, and Observations for progress tracking

### Habits
- Daily/weekly recurring Commitments
- Streak tracking, completion rate, reminders
- Categories: Health, Learning, Productivity, Relationships, Creativity

### Journal
- Daily entries (Document with date)
- Prompts: "What went well?", "What could I improve?", "What am I grateful for?"
- AI summaries: "This month you focused on fitness and career growth"

### Finance
- Income tracking (Financial Record)
- Expenses by category (Food, Transport, Housing, Entertainment, Savings)
- Budget goals (Commitment)
- Net worth tracking (Assets - Financial Records)
- Bill reminders (Commitment + Event)

### Health
- Workout log (Events + Observations)
- Sleep tracking (Observations)
- Mood journal (Observations)
- Medical appointments (Events)
- Medication reminders (Commitments)

### Learning
- Courses (Knowledge + Events)
- Reading list (Knowledge + Commitment)
- Skills tracking (Capabilities acquired)
- Certifications (Commitments + Documents)

### Projects
- Personal projects (Commitment + Events + Documents)
- Home improvement, creative projects, side ventures
- Milestones, tasks, materials, notes

### Ideas
- Idea capture (Knowledge + Document)
- Tagging and categorization
- Development pipeline (Workflow: idea → explore → plan → execute)

---

## Personal vs. Business: Key Differences

| Dimension | Personal Workspace | Business Workspace |
|-----------|-------------------|-------------------|
| Identity | Single person (self) | Organization + multiple persons |
| Primary relationship | To self, family, friends | To customers, employees, partners |
| Financial | Income/expense/budget | Invoicing/payroll/tax/accounting |
| Timeline | Life stages, seasons, years | Quarters, fiscal years, projects |
| Language | "My goals", "my health", "my learning" | "Revenue", "pipeline", "employees" |
| Sharing | Selective, opt-in | Role-based, by default |
| Memory | Personal history, preferences, habits | Customer history, org knowledge |
| AI focus | Personal growth, wellbeing, productivity | Revenue, efficiency, growth |

---

## Personal Workspace Evolution

### Phase 1 — Foundation (Current)
- Basic personal workspace with goals, habits, notes, journal
- Financial tracking (income/expenses)
- Calendar integration

### Phase 2 — Intelligence (Next)
- AI learns personal patterns and makes proactive suggestions
- Habit streak analysis, journal sentiment tracking
- Automated financial categorization

### Phase 3 — Connected (Future)
- Shared family workspace (household goals, shared calendar)
- Professional network integration (LinkedIn, calendar)
- Cross-workspace identity (same person across personal + business)

---

*Next: Article X-XI — Business-Agnostic Proof + Capability Catalog*