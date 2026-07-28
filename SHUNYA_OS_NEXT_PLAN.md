# Shunya OS — Next Build Plan

> Universal Business Operating System. AI-Native. Compounding Intelligence.
> One platform. Any business. Endless possibilities.

---

## Table of Contents

1. [Universal Entity Model](#1-universal-entity-model)
2. [AI Assistant — Primary Interface](#2-ai-assistant--primary-interface)
3. [Internal Data First Knowledge Pipeline](#3-internal-data-first-knowledge-pipeline)
4. [Governance & Real AI Powers](#4-governance--real-ai-powers)
5. [Module Builder — Self-Extending Platform](#5-module-builder--self-extending-platform)
6. [Voice + 37 Languages Layer](#6-voice--37-languages-layer)
7. [Client Portal](#7-client-portal)
8. [Multi-Brand / Parent Account](#8-multi-brand--parent-account)
9. [Notifications Ecosystem](#9-notifications-ecosystem)
10. [Payment Ecosystem](#10-payment-ecosystem)
11. [Supplier Ecosystem](#11-supplier-ecosystem)
12. [Analytics & Intelligence Layer](#12-analytics--intelligence-layer)
13. [Team Collaboration & Activity Feed](#13-team-collaboration--activity-feed)
14. [Offline / Progressive Web App](#14-offline--progressive-web-app)
15. [Emergency & Exception Handling](#15-emergency--exception-handling)
16. [Multi-Tenancy & Data Isolation](#16-multi-tenancy--data-isolation)
17. [The Onboarding Experience](#17-the-onboarding-experience)
18. [The Compounding Intelligence Loop](#18-the-compounding-intelligence-loop)
19. [Internationalization](#19-internationalization)
20. [Security & Compliance](#20-security--compliance)
21. [API & Extensibility](#21-api--extensibility)
22. [Universal Data Ingestion — The Platform as Data Sink](#22-universal-data-ingestion--the-platform-as-data-sink)
23. [Auto-Collection — Proactive Data Gathering](#23-auto-collection--proactive-data-gathering)
24. [Integration Ecosystem — Embed, Don't Replace](#24-integration-ecosystem--embed-dont-replace)
25. [Multi-Session — One Login, Every Device](#25-multi-session--one-login-every-device)
26. [Authentication Matrix — Solved Login](#26-authentication-matrix--solved-login)
27. [Perspectives — Thinking From Every Role](#27-perspectives--thinking-from-every-role)
28. [Implementation Roadmap](#28-implementation-roadmap)

---

# 1. Universal Entity Model

## Problem

Current system has fixed tables: `leads`, `payments`, `invoices`, `suppliers`. Each with fixed columns. A hospital needs `patients` with `blood_group`, `symptoms`, `assigned_doctor`. A school needs `students` with `class`, `parent_name`, `attendance`. Adding a new business type requires schema changes, migrations, and code deploys.

## Solution

One generic entity system driven by ontology configuration.

### Data Architecture

```
tenants table
  │
  ├── entity_definitions
  │   ├── id, tenant_id
  │   ├── type: "lead" | "patient" | "student" | "order" | "vendor_payment" | ...
  │   ├── label: "Lead" | "Patient" | "Student" | ...
  │   ├── schema: JSONB (all fields this entity type has)
  │   │   └── [{name, label, type, required, options, searchable}, ...]
  │   ├── statuses: JSONB ["new", "proposal", "booked", ...]
  │   ├── layout: "kanban" | "table" | "calendar" | "cards"
  │   ├── primary_metric: string
  │   └── is_active: boolean
  │
  ├── entities (one row per record — lead, patient, student, order...)
  │   ├── id, tenant_id
  │   ├── entity_type_id → entity_definitions
  │   ├── code: string (auto-generated: PC11072601)
  │   ├── status: string
  │   ├── assigned_to: user_id
  │   ├── data: JSONB ← ALL custom field values live here
  │   ├── ai_summary: TEXT (AI generates 1-line summary)
  │   ├── tags: JSONB
  │   ├── is_archived: boolean
  │   ├── created_at, updated_at
  │   └── created_by: user_id
  │
  ├── entity_activities (cross-entity audit log)
  ├── entity_files (documents attached to any entity)
  ├── entity_messages (conversations tied to any entity)
  └── entity_notes (internal notes per entity)
```

### Generic CRUD — One Set of Templates

The same templates render ALL entity types:

| Template | Renders |
|---|---|
| `entity_list.html` | Table, Kanban, or Cards — chosen by ontology |
| `entity_detail.html` | Dynamic fields from JSONB schema |
| `entity_form.html` | Auto-generated form from schema |
| `entity_pipeline.html` | Kanban view for any pipeline |

The template never knows if it's showing a lead, patient, or student. It reads the ontology, reads the schema, and renders.

### Example

**Travel agency creates entity_definitions for "lead" with fields:**
`customer_name`, `destination`, `pax`, `dates`, `budget`, `phone`, `email`

**Hospital creates entity_definitions for "patient" with fields:**
`patient_name`, `age`, `blood_group`, `symptoms`, `doctor_assigned`, `phone`, `admission_date`

**Same code. Same templates. Different ontology. Different business.**

---

# 2. AI Assistant — Primary Interface

## Design Principle

The AI is not a chat widget in the corner. It is **how the user interacts with the system.**

## Intent-to-Action Pipeline

```
User input (text/voice)
       │
       ▼
┌─── PARSE ───────────────────────────────────────┐
│  NLU classifier determines:                     │
│  - Intent: create_entity | query | send_message │
│           | execute_action | create_module      │
│  - Entity type: lead | patient | student | ...  │
│  - Parameters: extracted from natural language  │
│  - Confidence score                             │
└──────────────────┬──────────────────────────────┘
                   ▼
┌─── VERIFY ───────────────────────────────────────┐
│  - Permission check (can user do this?)          │
│  - Data validation (are params valid?)            │
│  - Governance level: draft | auto | govern       │
│  - Conflict check (does this contradict rules?)  │
└──────────────────┬──────────────────────────────┘
                   ▼
┌─── EXECUTE ──────────────────────────────────────┐
│  - Creates/updates/deletes records               │
│  - Sends messages (WhatsApp, Email, Telegram)     │
│  - Generates documents (proposals, invoices)      │
│  - Triggers automations (reminders, notifications)│
│  - Logs activity                                  │
│  - Stores in memory                               │
└──────────────────┬──────────────────────────────┘
                   ▼
┌─── RESPOND ──────────────────────────────────────┐
│  - Clear confirmation of what was done           │
│  - Summary of result                             │
│  - Suggested next steps                          │
│  - Undo option (within timeout)                  │
└──────────────────────────────────────────────────┘
```

### Proactive Intelligence

The AI doesn't wait to be asked:

```
🧠 "You haven't checked on the Patel lead in 5 days.
    They were interested in Bali. Want me to draft a
    check-in message for WhatsApp?"

🧠 "Your team's conversion rate is up 12% this week.
    Key factor: faster response time. Breakdown?"

🧠 "Flight UK-815 to Bangkok is delayed by 3 hours.
    The Sharma family is affected. I've notified the
    client. Want me to rebook the airport transfer?"
```

### Conversational Form-Filling

```
User: "Create a lead for the Sharma family, Bali trip, 2 adults 1 kid, budget 2.5L"

AI:
  ┌────────────────────────────────────────────────┐
  │  📋 New Lead — Review & Confirm                │
  │                                                │
  │  Customer: Sharma Family                       │
  │  Destination: Bali                             │
  │  Pax: 2 Adults, 1 Kid                          │
  │  Budget: ₹2,50,000                             │
  │  Status: New                                   │
  │  Assigned: You                                 │
  │                                                │
  │  [✓ Confirm]  [Edit]  [Cancel]                │
  └────────────────────────────────────────────────┘

User: "Looks good"

AI: ✅ Lead created (PC11072601). Anything else?"
```

---

# 3. Internal Data First Knowledge Pipeline

## Architecture

```
User asks a question
    │
    ▼
┌─── Step 1: Internal Search ──────────────────────┐
│  Search priority order:                          │
│  1. Entity records (leads, patients, students...) │
│  2. Past AI conversations (Honcho memory)        │
│  3. Company documents (uploaded files, PDFs)      │
│  4. Business rules (ontology, approval config)    │
│  5. Activity log (past team actions)              │
│                                                  │
│  → Found relevant data? → Answer with citations  │
│  → Not found? → Go to Step 2                     │
└──────────────────┬──────────────────────────────┘
                   ▼ (if not found internally)
┌─── Step 2: Web Search ───────────────────────────┐
│  - Web search for current info                   │
│  - Synthesize with business context              │
│  - Answer with source attribution                │
│  - Store new knowledge back into internal KB     │
└──────────────────────────────────────────────────┘
```

### Knowledge Base Schema

```
knowledge_entries table:
├── id, tenant_id
├── question: TEXT (normalized)
├── answer: TEXT
├── source: "internal" | "web" | "ai_generated"
├── source_url: string (for web sources)
├── confidence: float (0-1)
├── verified_by: user_id (null = unverified)
├── used_count: int (how often this was retrieved)
├── created_at, updated_at
└── embedding: vector (for semantic search)
```

### Compounding Knowledge

- Every AI answer is stored as a knowledge entry
- Frequently used knowledge gets higher confidence
- Contradicting knowledge is flagged for human review
- The system tells users when knowledge is unverified

---

# 4. Governance & Real AI Powers

## Three Tiers of AI Authority

| Tier | What AI Can Do | Guardrail |
|---|---|---|
| **Draft** | Fill forms, create proposals, generate itineraries, compose messages | User must confirm before save/execute |
| **Auto** | Create leads, update statuses, send routine messages, generate invoices within user's scope | Logged. Reversible within 5 minutes. |
| **Govern** | Approve team actions, modify business rules, change ontology, delete records | Needs second approver or admin |

## Execution Flow

```
User action via AI
    │
    ▼
Determines governance tier (based on action type + user role)
    │
    ├── Draft: Show user → Confirm → Execute → Log → Remember
    ├── Auto: Execute → Log → Notify → Remember
    └── Govern: Draft → Notify approver → (Approve → Execute) or (Reject → Explain)
```

## Approval Workflow

- Approvals are AI-suggested, human-decided
- Approver sees full context: who, what, when, why
- Decisions are logged and learnable
- "Rajat always approves proposals below ₹2L" → AI learns → Auto-tier expands

---

# 5. Module Builder — Self-Extending Platform

## User Flow

```
1. User describes workflow
   "I need to track equipment rentals — item name, customer,
    rental period, return date, deposit amount. And send a
    reminder 2 days before return."

2. AI generates entity definition
   - Creates entity_definitions entry with schema
   - Configures statuses: active, overdue, returned
   - Sets up automation: daily check → send reminder
   - Generates forms, list view, detail view

3. User reviews
   - Sees preview of the module
   - Can edit fields, statuses, labels
   - Can add/remove fields

4. User approves
   - Entity definition is saved
   - Module is active immediately
   - No code change. No deploy. No developer.
```

## What Module Builder Creates

| Component | Auto-generated |
|---|---|
| Entity definition | ✓ Schema, statuses, layout |
| List view | ✓ Table with dynamic columns |
| Form | ✓ Auto-generated from schema |
| Detail view | ✓ All fields displayed |
| Automation | ✓ Based on user description |
| Permission rules | ✓ Default (owner can edit, others read) |

---

# 6. Voice + 37 Languages Layer

## Pipeline

```
User speaks in their language
    │
    ▼
Speech-to-Text (STT) — 37 languages supported
    │
    ▼
Intent pipeline (language-agnostic — intent is intent)
    │
    ▼
Execute action (same pipeline as text input)
    │
    ▼
Text-to-Speech (TTS) — in user's language
    │
    ▼
Response delivered as voice + text fallback
```

## Key Behaviors

- Code-switching support: *"Yeh Sharma family ka Bali trip hai, inko airport pickup chahiye"* → understood
- Language persistence: once a user speaks Hindi, the AI responds in Hindi
- Voice is not a separate mode — it's a parallel input channel
- Works for both commands and queries
- Visual feedback during voice processing (transcript overlay, waveform animation)

## When Voice Wins

- Driving, walking, cooking
- Older users, low-literacy users
- Inputting long text without typing
- Quick actions ("Remind me tomorrow at 9am")
- Accessibility (visually impaired users)

---

# 7. Client Portal

## The Client Experience

Each client gets a unique, secure link:
```
app.shunyaos.com/client/PC11072601
```

## Client Portal Features

| Feature | Description |
|---|---|
| **Trip/Service Overview** | See what they booked, status, timeline |
| **Itinerary View** | Read-only itinerary with all details |
| **Payment Status** | What's paid, what's due, pay online |
| **Documents** | Invoices, receipts, visa docs, contracts |
| **Chat** | Message their agent directly |
| **Approve** | Approve proposals, changes, add-ons |
| **Feedback** | Post-trip review + Google Review link |

## Client Auth

- Passwordless: OTP to phone/email
- Magic link from agent (no account creation needed)
- Session lasts 30 days
- One-click re-auth

## Client Portal Design

- Mobile-first (most clients will use on phone)
- Clean, minimal, no internal clutter
- Branded with the business's logo/colors
- AI-powered: "Your flight departs in 3 days. Need to arrange airport pickup?"

---

# 8. Multi-Brand / Parent Account

## Architecture

```
Super Admin (Platform Owner)
    │
    ├── Brand A (SHUNYA OS — Travel)
    │   ├── Team, clients, entities, data
    │   ├── Brand theme (logo, colors, domain)
    │   └── AI trained on Brand A's data
    │
    ├── Brand B (SHUNYA Events)
    │   ├── Team, clients, entities, data
    │   ├── Brand theme
    │   └── AI trained on Brand B's data
    │
    └── Brand C (New Business)
        ├── Completely isolated
        └── Its own ontology, data, team
```

## Parent Account Features

- Single login, switch between brands
- Cross-brand analytics dashboard
- Share team members across brands (optional)
- Each brand is completely data-isolated
- Each brand has its own domain (travel.shunyaos.com, events.shunyaos.com)

## Multi-Brand Use Cases

- A person running multiple businesses
- A franchise with multiple locations
- A holding company with subsidiaries
- An agency managing multiple brand verticals

---

# 9. Notifications Ecosystem

## Channels

| Channel | Use For | Status |
|---|---|---|
| **In-app** | Toast/bell notifications | ✅ Built |
| **WhatsApp** | Client communication | 🚧 Needs API key |
| **Telegram** | Team alerts | ✅ Built |
| **Email** | Formal notifications, invoices | 🚧 Needs setup |
| **SMS** | Urgent alerts, OTPs | 🔲 Future |

## Notification Types

| Type | Trigger | Channel |
|---|---|---|
| Lead created | New inquiry | In-app + Telegram |
| Payment received | Payment confirmed | In-app + WhatsApp (client) |
| Status changed | Lead moves to new stage | In-app + Telegram |
| Task assigned | Team member gets task | In-app + Telegram |
| Proposal sent | Proposal shared with client | In-app |
| Celebration | Deal closed / milestone | In-app (confetti) |
| Reminder | Follow-up due | In-app + Telegram |
| System alert | Error, downtime, webhook fail | Telegram |

## Notification Preferences

Per-user: which channels for which notification types
Per-tenant: default channel config
Override: client gets WhatsApp, team gets Telegram

---

# 10. Payment Ecosystem

## Features

| Feature | Description |
|---|---|
| **Multiple gateways** | Razorpay, Stripe, PayPal — configurable per tenant |
| **Multi-currency** | INR, USD, EUR, GBP, AED... |
| **Invoice generation** | Auto from booking, manual, recurring |
| **Payment reminders** | Auto-send at D-7, D-3, D-1, D-day |
| **Receipts** | Auto-generated and sent on payment |
| **Partial payments** | Deposit + balance, installment plans |
| **Reconciliation** | Match payments to invoices, flag discrepancies |
| **Supplier payments** | Track what we paid vs what client paid (margin) |

## Payment Flow

```
Lead → Booking → Invoice generated → Payment link sent
                                            │
                                   Client pays online
                                            │
                                   Webhook confirms
                                            │
                                   Invoice marked paid
                                            │
                                   Receipt sent to client
                                            │
                                   Notification sent to team
                                            │
                                   Logged in activity
```

---

# 11. Supplier Ecosystem

## Supplier Model

Each supplier has:
- Name, category (hotel, flight, transport, venue, visa, activity...)
- Contact person, email, phone
- City, country
- GSTIN, PAN
- Payment terms
- Rate contracts (seasonal pricing)
- Performance rating (internal)
- Notes

## Supplier Payment Tracking

```
Booking amount: ₹2,50,000 (from client)
Supplier cost:  ₹1,80,000 (to hotel)
Margin:         ₹70,000

Track:
- What's paid to supplier? ₹90,000 (advance)
- What's due?             ₹90,000 (on check-in)
- What client paid?       ₹1,25,000 (50% advance)
- What client owes?       ₹1,25,000 (on check-in)
```

This is the Tally-like accounting layer — tracks both client money and supplier money with running balances.

---

# 12. Analytics & Intelligence Layer

## Built-in Analytics

| Metric | Source |
|---|---|
| Lead conversion rate | Lead status changes / time |
| Revenue by destination | Payments linked to leads |
| Revenue by team member | Leads grouped by assigned_to |
| Average deal size | Budget across all leads |
| Pipeline value | Sum of budgets by stage |
| Time to close | Lead created → booked |
| Seasonal patterns | Bookings by month |
| Team performance | Leads handled, conversion rate, revenue |

## AI-Powered Insights

- "Your conversion rate for Bali leads is 40% higher than Maldives"
- "October is your strongest month — start marketing in August"
- "Riya closes 2x faster than the team average — what's she doing differently?"
- "Leads that get a response within 1 hour convert at 60% vs 20% for 24+ hours"
- "You typically give 10% discount for groups above 10 people"

---

# 13. Team Collaboration & Activity Feed

## Activity Feed

Every action across the entire system is logged and visible:

```
Riya created lead PC11072601 (Sharma Family — Bali)
Amit sent proposal to Patel Family — ₹3,50,000
Riya marked status: Verma Family → Booked 🎉
System: Payment received ₹1,25,000 from Sharma Family
Amit assigned task to Riya: Get visa docs for Singh Family
Riya messaged client: "Your Bali itinerary is ready!"
```

## Team Features

- Role-based access (admin, manager, agent, viewer)
- Task assignment with due dates
- Notes on any entity (internal, not client-visible)
- @mentions in notes
- Handoff: transfer lead/patient/student between team members
- Who's online/offline indicator

---

# 14. Offline / Progressive Web App

## Why

Travel agents work in airports, remote locations, client sites — internet is unreliable.

## Offline Capabilities

| Tier 1 (Essential) | Tier 2 (Better) | Tier 3 (Full) |
|---|---|---|
| View assigned leads | Search cached entities | Full entity CRUD |
| View itineraries | View documents | Message queue |
| View client info | View activity log | Sync when online |
| Take notes | | |

## Implementation

- Service Worker caches recent entities and templates
- IndexedDB for local data store
- Sync queue: actions taken offline → executed when online
- Conflict resolution: last-write-wins with notification

---

# 15. Emergency & Exception Handling

## Proactive Disruption Management

```
Flight cancelled at 2am (detected via email/webhook/API)
    │
    ▼
AI identifies affected clients (entity records + bookings)
    │
    ▼
AI generates rebooking options (from supplier data)
    │
    ▼
Agent notified: "UK-815 cancelled. 3 clients affected.
  → Option A: Rebook on next flight (UK-817, 6am)
  → Option B: Full refund
  → Approve or handle manually?"
    │
    ▼
If approved → AI executes rebooking
    → Notifies client via WhatsApp
    → Updates itinerary
    → Logs everything
```

## Other Emergency Scenarios

- Payment gateway down → queue payments, retry, notify
- WhatsApp API down → fallback to email/SMS
- Server overload → graceful degradation (read-only mode)
- Data inconsistency → flag for admin review

---

# 16. Multi-Tenancy & Data Isolation

## Isolation Model

```
Tenant A sees:
  → Their entities, their clients, their team
  → Their AI, their memory, their knowledge base
  → Their settings, their ontology, their theme

Tenant B sees:
  → Completely different data
  → Completely different AI (trained on B's data)
  → Completely different ontology

Super Admin sees:
  → Across all tenants (aggregate, no PII)
  → Usage stats, adoption metrics
  → Can't read tenant data without permission
```

## Implementation

- All tables have `tenant_id` column
- SQLAlchemy query filter middleware auto-applies tenant scope
- Tenant-scoped AI memory (Honcho per tenant)
- Tenant-scoped knowledge base

---

# 17. The Onboarding Experience

## First-Time User Flow

```
1. User visits app.shunyaos.com
   → Clicks "Get Started"

2. AI: "Welcome to Shunya! What kind of business do you run?"
   → Options: Travel, Healthcare, Education, Retail, 
              Real Estate, Hospitality, Freelancer, Other
   → Or: "Tell me in your own words"

3. User selects / describes their business
   → AI configures ontology:
   → Entity definitions, statuses, fields, layout, theme

4. User is asked:
   "How many team members do you have?"
   "What's your company name?"
   "Upload your logo if you have one"

5. Dashboard appears — personalized, branded, ready
   → AI: "Your dashboard is ready! Want a quick tour?"
   → Or: "You have no leads yet. Want to create your first one?"
```

## Zero-to-Value Time

Target: **Under 2 minutes** from signup to seeing a useful dashboard.

---

# 18. The Compounding Intelligence Loop

## The Engine

```
Every interaction (query, command, action, feedback)
       │
       ▼
┌──────────────────────────────┐
│  1. CAPTURE                  │
│  Store raw interaction       │
│  (input, output, action,     │
│   user, timestamp)           │
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│  2. EXTRACT                  │
│  What can we learn?          │
│  - Facts: "Bali visa on      │
│    arrival for Indians"      │
│  - Preferences: "Rajat       │
│    prefers 3-night minimum"  │
│  - Patterns: "This client    │
│    said no to adventure"     │
│  - Rules: "Proposals > ₹5L  │
│    need manager approval"    │
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│  3. STORE                    │
│  → Knowledge base            │
│  → User preference profile   │
│  → Business pattern log      │
│  → Governance rules          │
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│  4. APPLY                    │
│  Next interaction uses:      │
│  - Relevant knowledge        │
│  - User's past preferences   │
│  - Business patterns         │
│  - Learned rules             │
└──────────┬───────────────────┘
           ▼
    (loop — every interaction improves the next)
```

## What Makes It Compounding

- **Day 1:** AI is generic (useful but not special)
- **Day 30:** AI has learned your business patterns, your team, your preferences
- **Day 90:** AI anticipates needs, catches errors, suggests improvements
- **Day 365:** The system is drastically smarter than day 1 — without a single code change

This is the moat. No other business software does this.

---

# 19. Internationalization

## Language Support

- UI: Full i18n with translation files
- AI: Responds in user's language (via LLM)
- Voice: 37 languages STT/TTS
- RTL support for Arabic, Urdu, Hebrew

## Regional Features

| Region | Requirements |
|---|---|
| India | GST, HSN codes, PAN, INR, UPI |
| UAE | VAT, TRN, AED |
| UK | VAT, Companies House |
| US | Sales tax per state, EIN |
| EU | VAT, GDPR |
| Saudi | Zakat, VAT, SAR |

## Currency

- Multi-currency support: INR, USD, EUR, AED, GBP, SAR, etc.
- Exchange rate tracking
- Invoice in any currency
- Payment gateway handles conversion

---

# 20. Security & Compliance

## Data Privacy

- All data encrypted at rest (AES-256)
- All traffic encrypted in transit (TLS 1.3)
- Tenant data completely isolated
- PII marked and protected
- Data export per tenant (GDPR right to data portability)
- Data deletion per tenant (GDPR right to be forgotten)

## Authentication

- Passwordless OTP option
- Session management with expiry
- Rate limiting on auth endpoints
- Audit log of all auth events

## Compliance Targets

| Regulation | Relevance |
|---|---|
| Indian IT Act | Primary market (India) |
| GDPR | EU clients |
| CCPA | California clients |
| PCI-DSS | Payment data (handled by payment gateway) |

---

# 21. API & Extensibility

## Public API

| Endpoint | Purpose |
|---|---|
| `POST /api/entities` | Create any entity type |
| `GET /api/entities/{type}` | List entities by type |
| `GET /api/entities/{type}/{id}` | Get single entity |
| `PUT /api/entities/{type}/{id}` | Update entity |
| `DELETE /api/entities/{type}/{id}` | Delete entity |
| `POST /api/ai/query` | Ask the AI anything |
| `POST /api/ai/execute` | Execute action via AI |
| `POST /api/files/upload` | Upload file |
| `GET /api/files/{id}` | Download file |
| `POST /api/messages/send` | Send via preferred channel |

## Webhooks

| Event | Payload |
|---|---|
| `entity.created` | { type, id, tenant_id, data } |
| `entity.updated` | { type, id, changes } |
| `entity.status_changed` | { from, to, entity_id } |
| `payment.received` | { amount, entity_id, gateway } |
| `message.sent` | { channel, to, content } |

Events are sent to tenant-configured webhook URLs.

## Plugin System

- Module builder is the primary extensibility mechanism
- Custom plugins for advanced cases (Python scripts)
- Webhook-based integrations for external systems

---

# 22. Universal Data Ingestion — The Platform as Data Sink

## Philosophy

The user should be able to feed **anything** into the system. The platform is not an app you enter data into — it is a **data sink** that accepts information from anywhere and structures it automatically.

## Input Channels

```
ANYTHING the user has:
    │
    ├── 📄 File upload: PDF, image, DOCX, XLSX, CSV, TXT, audio, video
    │     → OCR → classify → extract → structure → link → store
    │
    ├── 📧 Email forward: send to ingest@company.com
    │     → Parse email body + attachments → auto-create entities
    │
    ├── 💬 WhatsApp forward: forward message to bot
    │     → Extract booking details, confirmations, receipts
    │
    ├── 📸 Camera snap: take photo of document
    │     → OCR → auto-fill form
    │
    ├── 🌐 URL/Web scrape: paste a link
    │     → Extract structured data from the page
    │
    ├── 🎤 Voice memo: speak it
    │     → Transcribe → extract action items → execute
    │
    ├── 🔗 API webhook: integrate external services
    │     → Auto-create/update entities in real-time
    │
    ├── 📱 Social DM: forward Instagram/Twitter inquiry
    │     → Log as lead with source attribution
    │
    └── 📋 Manual: type or speak directly
          → Conversational form-filling
```

## The Ingestion Pipeline

```
Raw input arrives
    │
    ▼
┌── 1. CLASSIFY ─────────────────────────────────┐
│  What is this?                                  │
│  - Invoice? Booking confirmation? Client query? │
│  - Internal note? Supplier contract?            │
│  - Determined by: content analysis + AI         │
└──────────────────┬──────────────────────────────┘
                   ▼
┌── 2. EXTRACT ──────────────────────────────────┐
│  Pull structured data:                          │
│  - Names, dates, amounts, phone numbers         │
│  - Booking references, addresses                │
│  - Key terms, conditions, deadlines             │
└──────────────────┬──────────────────────────────┘
                   ▼
┌── 3. LINK ─────────────────────────────────────┐
│  Connect to what already exists:                │
│  - Match to existing lead/client (by name/phone)│
│  - Or create new entity if no match             │
│  - Link to related entities (booking → supplier)│
└──────────────────┬──────────────────────────────┘
                   ▼
┌── 4. STORE ────────────────────────────────────┐
│  - Create/update entity record                  │
│  - Save original file as attachment             │
│  - Index text for search                        │
│  - Store extracted data as structured fields    │
└──────────────────┬──────────────────────────────┘
                   ▼
┌── 5. NOTIFY ───────────────────────────────────┐
│  - Log activity                                 │
│  - Notify assigned team member                  │
│  - AI reviews for conflicts/anomalies           │
│  - Suggest next action                          │
└─────────────────────────────────────────────────┘
```

**Example:** Agent receives a hotel confirmation PDF via WhatsApp → forwards to Shunya bot → AI extracts booking number, dates, amount, hotel name → finds matching lead → attaches document to lead → updates itinerary → logs activity → done. Zero manual data entry.

---

# 23. Auto-Collection — Proactive Data Gathering

The system doesn't wait for the user to feed it. It proactively hunts for relevant data.

## Collectors

| Collector | What it does | Trigger |
|---|---|---|
| **Email monitor** | Scans connected inbox for booking confirmations, payment receipts, client emails | Periodic + real-time webhook |
| **WhatsApp listener** | Monitors incoming messages for data-rich content | Real-time |
| **Bank feed** | Matches bank transactions to invoices/payments | Daily |
| **Flight API** | Tracks flight status, delays, cancellations | Real-time per booking |
| **Social monitor** | Watches brand mentions, creates leads from inquiries | Periodic |
| **Price tracker** | Monitors competitor/supplier pricing | Configurable |
| **Calendar sync** | Pulls events, meetings, deadlines | Periodic |

## User Control

Each collector has three modes:
| Mode | Behavior |
|---|---|
| **Auto** | Runs silently, stores results, no user intervention |
| **Suggest** | Runs, shows user what it found, asks to import before storing |
| **Manual** | User triggers on demand |

---

# 24. Integration Ecosystem — Embed, Don't Replace

## Philosophy

We don't want users to "shift to Shunya." We want Shunya to work where they already are.

## Integration Matrix

| Where user works | How Shunya integrates | What happens |
|---|---|---|
| **WhatsApp** | Chat with Shunya bot | Create leads, check status, send proposals — all via chat |
| **Gmail / Outlook** | Forward email → auto-ingest | Email becomes entity, attachments become documents |
| **Telegram** | Team chat with bot | Team communication + system actions in one place |
| **Google Drive / Dropbox** | Connect account → watch folders | New files auto-imported, OCR'd, linked to entities |
| **Google Calendar** | Sync events → auto-log | Meetings become activities, deadlines become tasks |
| **Instagram / Facebook** | Forward inquiry DM | Social lead created with source attribution |
| **Razorpay / Stripe / PayPal** | Webhook → auto-reconcile | Payments matched to invoices automatically |
| **Tally / QuickBooks / Zoho Books** | Export/import | Accounting sync (bidirectional) |
| **Slack** | Shunya bot in workspace | Team can manage without leaving Slack |
| **Browser** | Bookmarklet / extension | "Send to Shunya" from any webpage |
| **Phone Camera** | Scan document directly | OCR → structured data → entity |

## Integration Architecture

- **Connectors** — modular adapter per integration
- **Webhooks** — real-time data push from external services
- **API polling** — periodic sync for services without webhooks
- **Email parsing** — structured extraction from email content
- **OAuth** — secure auth for each connected service

## Key Principle

The user should never think "I need to log into Shunya to do this." They work in their tool of choice. Shunya works silently in the background, collecting, structuring, and connecting everything.

---

# 25. Multi-Session — One Login, Every Device

## Session Model

- One user account → multiple simultaneous sessions
- Each device/browser gets its own independent session
- Sessions are visible and manageable from any device
- Force-logout specific sessions remotely

## Session Types

| Type | Expiry | Use |
|---|---|---|
| **Web session** | 24h (sliding) | Desktop browser |
| **Mobile session** | 7d (sliding) | Phone browser / future native app |
| **API token** | Configurable (30d–1y) | Programmatic access |
| **Magic link token** | 15 minutes | One-time auth |
| **Remember me** | 30d | "Keep me logged in" across restarts |

## Session Management UI

```
Settings → Sessions

Active Sessions:
  ● Chrome on Mac (San Francisco) — Current session
  ○ Safari on iPhone (Mumbai) — Last active 2h ago
  ○ Chrome on Windows (Delhi office) — Last active 1d ago

  [Logout All Other Sessions]  [Logout Specific...]
```

---

# 26. Authentication Matrix — Solved Login

## Auth Methods — Complete Coverage

| Method | UX | Security | Status |
|---|---|---|---|
| **Email + Password** | Standard login form | Bcrypt + rate limiting | 🟡 Exists, basic |
| **Phone + OTP** | Enter phone → receive SMS OTP → login | OTP, 5-min expiry | 🔲 Not built |
| **Magic Link (Email)** | Enter email → click link → logged in | Token, 15-min expiry | 🔲 Not built |
| **Magic Link (WhatsApp)** | Enter phone → WhatsApp message → tap to login | Token, 15-min expiry | 🔲 Not built |
| **Google OAuth** | "Sign in with Google" | OAuth 2.0 | 🔲 Not built |
| **Apple OAuth** | "Sign in with Apple" | OAuth 2.0, private relay | 🔲 Not built |
| **SSO / SAML** | Enterprise single sign-on | SAML 2.0, OIDC | 🔲 Not built |
| **Passkeys / WebAuthn** | Face/Touch/Fingerprint | FIDO2, phishing-resistant | 🔲 Future |
| **Biometric** | Fingerprint/Face on mobile | Platform-level | 🔲 Future |

## Signup Flow

```
1. User visits app.shunyaos.com
2. Clicks "Get Started" or "Sign Up"
3. Options:
   a. "Continue with Google" → OAuth → account created → done
   b. "Continue with Email" → enter email → magic link → account created → done
   c. "Continue with Phone" → enter phone → WhatsApp OTP → account created → done
4. Post-auth: AI onboarding flow (what business, configure dashboard)
```

## Why Coverage Matters

Every auth method removed is a barrier lowered:
- Magic links: zero password friction
- OAuth: one tap, no typing
- OTP: works for users who don't remember passwords
- SSO: enterprise adoption requirement
- Passkeys: future-proof, phishing-proof

## Current Gaps

- No signup flow at all (currently admin creates users)
- No password reset flow
- No OTP auth
- No social OAuth
- No session management UI

---

# 27. Perspectives — Thinking From Every Role

## 27.1 The Business Owner

*Runs a travel agency, hospital, or school. Wants to run their business, not learn software.*

- "What needs my attention today?" should be the first thing they see
- They never navigate menus — the AI is the navigation
- They approve actions, they don't fill forms
- They want to say what they need, not search for features

## 27.2 The Team Member

*Travel agent, nurse, teacher, sales rep. Wants to do their job faster with less friction.*

- AI handles data entry, they handle relationships
- They ask questions in natural language, get answers instantly
- They never lose a client's context — AI remembers everything
- They get proactive reminders so nothing falls through cracks

## 27.3 The Client

*The end customer. Wants a seamless, transparent experience.*

- One link shows everything about their booking
- They can chat, pay, view, approve — all from their phone
- They never need to call or email for basic info
- They feel taken care of, not managed

## 27.4 The Super Admin (Platform Owner)

*Rajat. Wants the platform to grow, be valuable, and win.*

- Sees across all tenants without seeing their data
- Knows which features are used, which are ignored
- Can approve/deny tenant module requests
- Pushes updates that don't break existing tenants
- The platform compounds — more usage = smarter system = lock-in

## 27.5 The Developer / Integrator

*Wants to build on top of Shunya or connect existing systems.*

- Clear REST API for everything
- Webhooks for real-time events
- Module builder for custom workflows
- Plugin system for deeper extensions

## 27.6 The Investor

*Why should I bet on Shunya vs Salesforce/Zoho/Notion?*

- **Moat #1:** Compounding intelligence — the system gets smarter without code changes, making it harder to leave over time
- **Moat #2:** Universal by design — not a vertical SaaS that needs to be rebuilt for each industry
- **Moat #3:** AI-native — not a CRM with a chat widget bolted on, but an OS where AI is the interface
- **Moat #4:** Free white-label model — anyone can rebrand and resell, creating network effects

## 27.7 The Competitor

*What would it take to copy this?*

- The entity model is easy to copy (it's just JSONB)
- The UI is easy to copy (it's just components)
- The compounding intelligence is **hard** — it requires years of data, trust, and habitual usage
- The module builder is **hard** — robust enough to handle any workflow without code
- The AI training per tenant is **hard** — running thousands of personalized AI instances

## 27.8 The Regulator / Compliance Officer

*Data privacy, audit trails, retention policies.*

- Every action is logged and non-repudiable
- Data is tenant-isolated with no cross-contamination
- PII is marked and protected
- Data can be exported or deleted on request
- Audit trails are exportable for regulatory review

## 27.9 The Non-Profit / Government

*Free tier, public accountability, transparency.*

- Free for non-profits and small government units
- Public transparency dashboard for government use (optional)
- Subsidized by revenue from commercial tenants
- API-first for integration with government systems

## 27.10 The Franchise / Multi-Location

*Same brand, multiple locations, centralized + local control.*

- Parent brand sets base ontology and theme
- Each location can customize within limits
- Centralized reporting across all locations
- Localized AI (trained on each location's data)

## 27.11 The Accidental User

*Someone using Shunya for something we never imagined.*

- The generic entity model means any workflow can be created
- If a user builds something novel, we study it and improve defaults
- The module builder allows infinite extension without forking
- The platform should be flexible enough that the most innovative use cases come from users, not us

## 27.12 The International User

*Different country, different language, different regulations.*

- 37 languages for the AI
- Regional compliance built in (GST, VAT, Zakat...)
- Multi-currency with live exchange rates
- RTL support for Arabic/Urdu

---

---

# 28. AI Self-Evolution

## Philosophy

The compounding intelligence loop learns from user interactions. Self-evolution is the higher order — the AI improves itself proactively.

## The Self-Evolution Loop

```
AI observes patterns across ALL interactions
       │
       ▼
┌── 1. DETECT ───────────────────────────────────┐
│  "Users correct me on supplier payment terms   │
│  30% of the time. I'm getting this wrong."     │
│                                                 │
│  "3 different users asked for the same feature │
│   this week: 'track vendor contracts'"          │
│                                                 │
│  "Your team spends 2h/day on invoice follow-   │
│   ups. I can automate this."                    │
└──────────────────┬──────────────────────────────┘
                   ▼
┌── 2. SUGGEST ──────────────────────────────────┐
│  AI proposes changes:                           │
│  - "I need more training data on supplier       │
│     payment terms. Can you verify 5 examples?"  │
│  - "Want me to build a 'contract tracking'      │
│     module? It'll be ready in 2 minutes."       │
│  - "I've automated invoice reminders. Check     │
│     your Settings → Automations to enable."     │
└──────────────────┬──────────────────────────────┘
                   ▼
┌── 3. IMPROVE ──────────────────────────────────┐
│  User approves → AI implements:                 │
│  - Updates its knowledge base                   │
│  - Creates new module/automation                │
│  - Adjusts its behavior for future queries      │
└──────────────────┬──────────────────────────────┘
                   ▼
┌── 4. CONFIRM ──────────────────────────────────┐
│  "✅ I've updated my understanding of           │
│   supplier payment terms. I'll handle           │
│   this correctly going forward."                │
│                                                  │
│  "✅ Contract tracking module is ready.          │
│   Check your dashboard."                         │
└──────────────────────────────────────────────────┘
```

## What Self-Evolution Detects

| Pattern | AI Action |
|---|---|
| Frequent user corrections | Flag knowledge gap, request verification |
| Repeated feature requests | Propose module creation |
| Manual repetitive workflows | Suggest automation |
| Common user errors | Proactive validation |
| Underused features | Proactive tips ("Did you know...") |
| Performance bottlenecks | Suggest workflow optimization |

## Self-Diagnosis

The AI should also introspect:
- "I've been wrong about X recently. Let me learn from those corrections."
- "My confidence on this topic is low because I lack data."
- "I'm being asked the same question repeatedly — I should remember this permanently."

---

# 29. Community & Module Marketplace

## Architecture

```
Module Marketplace (community.shunya.com / in-app)
    │
    ├── Official Modules (maintained by us)
    │   ├── Travel (lead, booking, itinerary, supplier)
    │   ├── Healthcare (patient, appointment, prescription)
    │   ├── Education (student, class, exam, fee)
    │   ├── Retail (order, product, inventory)
    │   └── More built-in ontologies
    │
    ├── Community Modules (built by users)
    │   ├── Vendor Contract Tracker ★4.5 (230 installs)
    │   ├── Wedding Planner ★4.8 (150 installs)
    │   ├── Fleet Management ★4.2 (89 installs)
    │   └── More...
    │
    └── Your Modules (your custom modules)
        └── [Publish to Community] [Export]
```

## Marketplace Flow

```
Browse marketplace → Find module → Preview schema/fields
    → One-click Install → AI activates it → Ready to use

To publish:
Build via Module Builder → [Publish] → AI reviews (quality, security)
    → User writes description, sets category
    → Submitted for moderation → Approved → Live
```

## Moderation

- AI auto-review: checks for schema validity, field naming, security
- Human review for first-time publishers
- Automated scanning for malicious patterns
- Rating and reporting system

## Network Effect

More users → more modules → more value → more users.
This is the flywheel that makes Shunya hard to compete with.

---

# 30. Data Portability

## Philosophy

"You should be able to leave Shunya as easily as you joined. We'll make staying the obvious choice — not the only choice."

## Export

| Format | What's included |
|---|---|
| **CSV** | Entities (one file per entity type), activities |
| **JSON** | Full data dump with relationships |
| **PDF** | Individual records, itineraries, invoices |
| **ZIP** | All of the above + attached files in organized folders |

Export triggers:
- One-click from Settings
- Automated: daily/weekly to Google Drive, Dropbox, S3, or email
- API: programmatic bulk export

## Import

| Source | How |
|---|---|
| **CSV upload** | Upload file → AI maps columns to fields → confirm → import |
| **Google Sheets** | Connect → select sheet → map → import |
| **Excel (.xlsx)** | Upload → parse → map → import |
| **API** | Programmatic bulk import |
| **Direct paste** | Paste table → AI parses → map → import |

## Migration Assistant

AI helps with import:
- "I see columns: Name, Phone, Destination, Amount. I'll map them to: customer_name, phone, destination, budget. Correct?"
- Detects duplicates before importing
- Reports rows that couldn't be mapped

---

# 31. Deployment & Operations

## Current State → Target

| Area | Current | Target |
|---|---|---|
| **Deploy** | Manual restart on VPS | GitHub Actions CI/CD |
| **Environment** | Single VPS (production) | Staging + Production |
| **Database** | PostgreSQL, no automated backup | Auto daily backups + WAL archiving |
| **Monitoring** | None | Uptime checks, error tracking (Sentry), performance |
| **Alerts** | None | Telegram/email for downtime, errors, high load |
| **Scaling** | 2 gunicorn workers | Auto-scaling + multi-server support |
| **Migrations** | db.create_all() on startup | Alembic with rollback |
| **SSL** | Certbot auto-renew | ✅ Already done |

## CI/CD Pipeline

```
GitHub: push to main
    │
    ▼
GitHub Actions:
    1. Run tests (pytest suite)
    2. Lint check
    3. Build Docker image
    4. Push to container registry
    │
    ▼
Production server:
    5. Pull new image
    6. Run database migrations (Alembic)
    7. Restart service
    8. Health check (wait for 200)
    9. Rollback on failure (restore previous image + revert migration)

    │
    ▼
Notify: "Deploy complete (commit abc1234) — 28/28 tests passing"
```

## Backup Strategy

| What | Frequency | Retention |
|---|---|---|
| Database (full pg_dump) | Daily | 30 days |
| Database (WAL archive) | Continuous | 7 days |
| Uploaded files (media/) | Daily rsync | 30 days |
| Configuration (env, nginx) | Every deploy | Git history |

## Disaster Recovery

- Recovery Time Objective: < 1 hour
- Recovery Point Objective: < 5 minutes (with WAL)
- Runbook: documented restore procedure (tested quarterly)

---

# 32. AI Feedback Loop — Learning from Mistakes

## The Correction Mechanism

```
AI gives a response
    │
    ├── 👍 User thumbs up
    │     → Reinforce this knowledge (store as good example)
    │
    ├── 👎 User thumbs down
    │     │
    │     ├── AI asks: "What should the correct answer be?"
    │     │
    │     ├── User corrects
    │     │
    │     └── AI:
    │          1. Stores correction in knowledge base
    │          2. Updates its understanding
    │          3. Logs the correction pattern
    │          4. If same mistake repeats → self-evolution trigger
    │
    └── "That's wrong" (no correction given)
          → AI suggests alternatives
          → Asks clarifying questions
          → Flags for human review
```

## Confidence Scoring

When confidence is low, the AI explicitly communicates uncertainty:

```
User: "What's the cancellation policy for Hotel Grand?"

AI: "Based on the booking records, Hotel Grand (Sharma family,
     PC11072601) has free cancellation up to 7 days before
     check-in."

     [Confidence: High — sourced from actual booking data]

vs

User: "What's the weather like in Bali next week?"

AI: "I couldn't find this in your company data. Based on
     external sources, Bali's forecast shows..."

     [Confidence: Medium — sourced from web, not internal data]
```

Low confidence behaviors:
- AI explicitly says "I'm not sure"
- Offers alternatives to verify
- Never fabricates data
- Tags response as "unverified"

## Feedback Analytics Dashboard

For super admin / tenant admin:

| Metric | What it shows |
|---|---|
| Accuracy rate | 👍 / (👍 + 👎) over time |
| Correction categories | What the AI gets wrong most often |
| Knowledge gaps | Frequently asked, poorly answered |
| Trending | Is accuracy improving or declining? |
| Top corrections | User: "X is wrong, here's Y" — most valuable inputs |

---

# 33. On-Premise / Self-Hosted

## Who Needs This

| Sector | Reason |
|---|---|
| Hospitals / Healthcare | Patient data cannot leave their network |
| Government / Public sector | Data sovereignty laws |
| Banks / Fintech | Regulatory compliance |
| Defense / Security | Classification requirements |
| Large enterprises | Internal policy against cloud |
| Rural / low-connectivity | Cloud dependency not feasible |

## Self-Hosted Offering

```
A single-tenant Docker image containing:
  - Flask application (Shunya OS)
  - PostgreSQL 16 (database)
  - Redis (cache + sessions)
  - AI engine (with optional bring-your-own-LLM)
  - File storage (local or S3-compatible)

Requirements:
  - 4 GB RAM minimum (8 GB recommended)
  - 2 CPU cores
  - 50 GB storage (more for files)
  - Docker + Docker Compose

Optional:
  - Bring your own LLM via Ollama (local, no external AI API)
  - Or use Shunya cloud AI API (if internet available)
  - External PostgreSQL (if they have managed DB)
```

## Self-Hosted Features

| Feature | Cloud | Self-Hosted |
|---|---|---|
| All core features | ✅ | ✅ |
| Multi-tenant | ✅ | Single-tenant only |
| Auto-updates | ✅ | Pull-based (they control when) |
| Telemetry | Anonymized usage stats | Opt-in, can disable |
| AI model | Shunya-managed API | Bring your own or use ours |
| Support | Email + chat | Email + documentation |
| Backup | Built-in | They manage their own |
| Data location | Our servers | Their infrastructure |

## Self-Hosted Licensing

- Annual per-instance license
- Includes: software, security patches, documentation updates
- Support: email + knowledge base
- Premium support: 4-hour SLA (additional cost)

---

# 34. Implementation Roadmap

## Phase 1 — Foundation (Current → Next)

| Priority | Item | Depends On |
|---|---|---|
| P0 | Generic Entity Model (entity_definitions + entities tables) | — |
| P0 | Generic CRUD templates (list, detail, form, pipeline) | Entity Model |
| P0 | Multi-tenancy (tenant_id on all tables + middleware) | — |
| P0 | AI Memory Pipeline (Honcho integration for compounding intelligence) | — |
| P0 | Governance Tiers (Draft/Auto/Govern) | — |
| P0 | Authentication Matrix (OTP, magic links, OAuth, signup flow) | — |
| P0 | Multi-Session Management | Auth |

## Phase 2 — Intelligence

| Priority | Item | Depends On |
|---|---|---|
| P1 | Internal Data First Knowledge Pipeline | AI Memory |
| P1 | Proactive Intelligence Engine | AI Memory + Governance |
| P1 | Conversational Form-Filling | Generic CRUD |
| P1 | Module Builder (v1 — basic) | Entity Model |
| P1 | AI Self-Evolution Engine | AI Memory + Knowledge Pipeline |
| P1 | AI Feedback Loop (thumbs, corrections, confidence scoring) | AI Memory |
| P1 | Data Portability (export/import) | Generic CRUD |
| P1 | CI/CD Pipeline + Automated Backups | — |

## Phase 3 — Channels

| Priority | Item | Depends On |
|---|---|---|
| P2 | Voice Pipeline (37 languages) | — |
| P2 | Client Portal | Entity Model |
| P2 | Email Integration | — |
| P2 | Payment Gateway Integration | Client Portal |
| P2 | Multi-Brand / Parent Account | Multi-tenancy |
| P2 | Universal Data Ingestion Pipeline | Entity Model |
| P2 | Auto-Collection (email monitor, webhooks, listeners) | Data Ingestion |
| P2 | Integration Ecosystem (WhatsApp, Google, Slack connectors) | API |

## Phase 4 — Scale & Ecosystem

| Priority | Item | Depends On |
|---|---|---|
| P3 | Offline / PWA | — |
| P3 | Emergency Handler | Proactive Intelligence |
| P3 | Analytics Dashboard | Entity Model |
| P3 | Module Marketplace | Module Builder |
| P3 | On-Premise / Self-Hosted Docker Image | CI/CD + Multi-tenancy |
| P3 | Plugin System | Module Builder |
| P3 | Full i18n | — |

---

*This is a living document. Updated as of July 11, 2026.*
*Next step: Review → Prioritize → Build.*