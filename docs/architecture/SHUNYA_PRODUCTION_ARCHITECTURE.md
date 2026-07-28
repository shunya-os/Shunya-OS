# SHUNYA Production Architecture

> **Document Type:** Constitutional Blueprint  
> **Directive:** FOR-2B  
> **Status:** Ratified  
> **Date:** 2026-07-26  
> **Audience:** Engineering, Product, Future Contributors  

This document is the single source of truth for SHUNYA's permanent production architecture.

Every module, entity, route, and capability implemented in SHUNYA must fit into this structure.

No future work may introduce alternative structures, release-specific namespaces, duplicate models, or parallel business abstractions.

---

## 1. Core Philosophy

SHUNYA is the Operating System for Organizations.

Everything exists to help organizations think, remember, operate, communicate, and grow.

SHUNYA does not sell software. SHUNYA provides the platform on which organizations run.

### 1.1 Principles

- **Organization-first.** The primary object is the Organization. Every entity belongs to an Organization.
- **Identity-independent.** A human Identity exists above Organizations. One identity, unlimited organizations.
- **Business-agnostic.** Industry-specific behaviour lives in Industry Packs, never in Core.
- **Event-driven.** Modules communicate through events, not direct coupling.
- **AI-native.** Every domain has AI capability. AI is not a separate module — it is a layer across all domains.
- **Permanent data.** Relationships, knowledge, and history are never deleted — only archived.

### 1.2 Panchi Club Is Not the Definition

Panchi Club is the first production deployment and validation company.

It is never the architectural definition of SHUNYA.

Capabilities proven at Panchi Club must be generalised before entering Core.

---

## 2. Primary Object Hierarchy

```
Human Identity
    │
    ▼
Organizations
    │
    ├── Relationships (Customers, Suppliers, Employees, Partners...)
    │       │
    │       ├── Knowledge (Documents, SOPs, Contracts, Media...)
    │       ├── Work (Proposals, Projects, Tasks, Approvals...)
    │       ├── Finance (Invoices, Payments, Ledger, P&L...)
    │       └── Communications (Messages, Email, Voice, Notifications...)
    │
    ├── Intelligence (Executive AI, Relationship AI, Knowledge AI, Finance AI...)
    │
    └── Industry Packs (Travel, Healthcare, Manufacturing...)
```

Everything in SHUNYA belongs somewhere in this hierarchy.

### 2.1 Hierarchy Rules

- Every entity MUST have an `organization_id` foreign key (except Identity).
- Every entity MUST have a `created_by` identity reference.
- Every entity MUST have a `created_at` timestamp.
- Every entity SHOULD have an `updated_at` timestamp.
- Entities representing relationships between people MUST reference `org_members.identity_id` or be wrapped in a `Relationship`.
- No entity may exist outside an Organization except the Human Identity itself.

---

## 3. Canonical Domains

### 3.1 Domain Registry

| # | Domain | Purpose | Owner |
|---|--------|---------|-------|
| 1 | `identity` | Human Identity — one per person, unlimited orgs | System |
| 2 | `organization` | Organization profile, branding, members, roles, departments | System + Org Admin |
| 3 | `relationship` | All people the org interacts with (customers, suppliers, employees) | Org Users |
| 4 | `knowledge` | Organizational memory — documents, media, contracts, SOPs | Org Users |
| 5 | `proposal` | Business proposals, quotations, pricing, itineraries | Sales |
| 6 | `work` | Projects, tasks, approvals, executions, automation | Operations |
| 7 | `finance` | Chart of accounts, ledger, invoices, payments, P&L | Finance |
| 8 | `communication` | Email, WhatsApp, voice, SMS, notifications, internal chat | All |
| 9 | `automation` | Event subscriptions, workflow triggers, scheduled tasks | System |
| 10 | `search` | Universal search across all domains | All |
| 11 | `founder` | Executive workspace, founder intelligence, personal AI | Founder |
| 12 | `ai` | AI model routing, memory, prompts, pipelines | System |
| 13 | `platform` | Deployment, monitoring, secrets, scaling, backups | System |
| 14 | `security` | AuthN, AuthZ, audit logs, encryption, rate limiting | System |
| 15 | `administration` | Org settings, branding, industry packs, billing | Org Admin |

### 3.2 Each Domain Defines

**Purpose** — What business problem this domain solves.  
**Ownership** — Who is responsible for this domain's data and decisions.  
**Entities** — Every data model with canonical table name.  
**Services** — Every business service/engine with purpose.  
**Events** — Every event this domain emits or consumes.  
**API** — Every route with HTTP method, path, and purpose.  
**UI** — Every UI component with route and purpose.  
**Storage** — Database tables, file storage paths, cache keys.  
**Future expansion** — Known upcoming capabilities within this domain.

---

## 4. Canonical Folder Structure

Replace release-based thinking (FOR-1, FOR-2, Phase N) with domain-based structure.

### 4.1 Target Layout

```
app/
├── identity/           # Human Identity domain
│   ├── __init__.py
│   ├── models.py       # Identity model
│   ├── services.py     # IdentityEngine, create/find/verify identity
│   ├── routes_api.py   # /api/v1/identity/*
│   └── routes_ui.py    # /auth/*, /login/* UI pages
│
├── organization/       # Organization domain
│   ├── __init__.py
│   ├── models.py       # Organization, OrgMember, OrgInvitation, Department
│   ├── services.py     # org creation, switching, invitations, roles
│   ├── routes_api.py   # /api/v1/organizations/*
│   ├── routes_ui.py    # /org/* UI pages
│   └── templates/
│       ├── org_select.html
│       ├── workspace.html
│       └── settings.html
│
├── relationship/       # Relationship domain (universal CRM)
│   ├── __init__.py
│   ├── models.py       # Relationship, RelationshipType, Timeline, Person
│   ├── services.py     # relationship CRUD, timeline, search
│   ├── routes_api.py   # /api/v1/relationships/*
│   └── routes_ui.py    # /relationships/* UI pages
│
├── knowledge/          # Knowledge domain
│   ├── __init__.py
│   ├── models.py       # KnowledgeDocument
│   ├── services.py     # ingestion, OCR, semantic search, duplicate detection
│   ├── routes_api.py   # /api/v1/knowledge/*
│   └── routes_ui.py    # /knowledge/* UI pages
│
├── proposal/           # Proposal domain
│   ├── __init__.py
│   ├── models.py       # Proposal, ProposalVersion
│   ├── services.py     # generation, pricing, itinerary, PDF, web rendering
│   ├── routes_api.py   # /api/v1/proposals/*
│   └── routes_ui.py    # /proposals/* UI pages
│
├── work/               # Work domain (projects, tasks, approvals)
│   ├── __init__.py
│   ├── models.py       # Project, Task, Approval, Execution
│   ├── services.py     # workflow engine, state machine, notifications
│   ├── routes_api.py   # /api/v1/work/*
│   └── routes_ui.py    # /work/* UI pages
│
├── finance/            # Finance domain
│   ├── __init__.py
│   ├── models.py       # Invoice, Payment, Ledger, ChartOfAccounts
│   ├── services.py     # invoicing, reconciliation, reporting
│   ├── routes_api.py   # /api/v1/finance/*
│   └── routes_ui.py    # /finance/* UI pages
│
├── communication/      # Communication domain
│   ├── __init__.py
│   ├── models.py       # Message, Notification, Conversation
│   ├── services.py     # email, WhatsApp, voice, push
│   ├── routes_api.py   # /api/v1/communications/*
│   └── routes_ui.py    # /communications/* UI pages
│
├── automation/         # Automation domain
│   ├── __init__.py
│   ├── models.py       # EventSubscription, Workflow, ScheduledTask
│   ├── services.py     # event bus, workflow engine, cron
│   ├── routes_api.py   # /api/v1/automation/*
│   └── routes_ui.py    # /automation/* UI pages
│
├── search/             # Universal search domain
│   ├── __init__.py
│   ├── services.py     # indexing, query, ranking
│   └── routes_api.py   # /api/v1/search*
│
├── founder/            # Founder / Executive domain
│   ├── __init__.py
│   ├── models.py       # FounderSpace, FounderConversation
│   ├── services.py     # executive dashboard, founder intelligence
│   ├── routes_api.py   # /api/v1/founder/*
│   └── routes_ui.py    # /workspace, /settings UI pages
│
├── ai/                 # AI infrastructure domain
│   ├── __init__.py
│   ├── models.py       # AIMemory, AIPrompt, ModelConfig
│   ├── services.py     # model routing, prompt management, context assembly
│   └── routes_api.py   # /api/v1/ai/*
│
├── platform/           # Platform domain
│   ├── __init__.py
│   ├── services.py     # health, monitoring, secrets, scaling
│   └── routes_api.py   # /health, /metrics, /config
│
├── security/           # Security domain
│   ├── __init__.py
│   ├── middleware.py    # auth middleware, rate limiting, CORS
│   ├── services.py     # session management, audit logging
│   └── routes_api.py   # /api/v1/security/*
│
├── administration/     # Admin domain
│   ├── __init__.py
│   ├── models.py       # Branding, IndustryPack
│   ├── services.py     # pack management, settings, billing
│   ├── routes_api.py   # /api/v1/admin/*
│   └── routes_ui.py    # /admin/* UI pages
│
├── industry_packs/     # Industry-specific extensions
│   ├── travel/         # Panchi Club industry pack
│   │   ├── __init__.py
│   │   ├── terminology.py   # booking→travel, package→itinerary
│   │   ├── templates/       # travel-specific proposal templates
│   │   └── ai_prompts/      # travel-specific AI prompts
│   └── healthcare/     # (future)
│
├── __init__.py         # App factory — registers all blueprints
├── models.py           # Canonical business models (legacy consolidation)
├── routes.py           # Top-level route registration
└── templates/          # Shared templates
    ├── base.html
    ├── components/
    └── layouts/
```

### 4.2 Migration From Current Structure

| Current | Target | Timeline |
|---------|--------|----------|
| `app/for1/` → Proposal | `app/proposal/` | FOR-2B |
| `app/for2/` → Organization | `app/organization/` | FOR-2B |
| `app/models.py` (Proposal, KnowledgeDocument, Organization, OrgMember, etc.) | Domain-specific `models.py` | FOR-2C+ |
| `app/routes.py` (legacy leads, invoices) | Domain-specific `routes_*` | FOR-2C+ |
| `app/for1/engine.py` | `app/proposal/services.py` | FOR-2B |
| `app/for2/routes.py` | `app/organization/routes_api.py` + `routes_ui.py` | FOR-2B |

---

## 5. Canonical Data Ownership

### 5.1 Entity Ownership Matrix

| Entity | Owner Domain | Parent | Children | Lifecycle |
|--------|-------------|--------|----------|-----------|
| `Identity` | identity | — | OrgMember | Immutable, never deleted |
| `Organization` | organization | Identity | OrgMember, Department, Relationship, Proposal... | Created by owner, suspended by admin, archived never deleted |
| `OrgMember` | organization | Organization, Identity | — | Active/inactive, never deleted |
| `Department` | organization | Organization | OrgMember | Active/inactive |
| `Relationship` | relationship | Organization | Timeline, Proposal, Invoice, Payment | Active/archived, never deleted |
| `Person` | relationship | Organization | Relationship | Merged with Identity on match |
| `KnowledgeDocument` | knowledge | Organization, Relationship | — | Uploaded → indexed → archived |
| `Proposal` | proposal | Organization, Relationship | ProposalVersion | Draft → sent → accepted → booked → archived |
| `Invoice` | finance | Organization, Relationship | Payment | Draft → sent → paid/void |
| `Payment` | finance | Organization, Relationship | — | Initiated → confirmed → reconciled |
| `Task` | work | Organization, Relationship | — | Open → in_progress → completed |
| `Message` | communication | Organization, Relationship, Conversation | — | Sent → delivered → read |

### 5.2 Deletion Rules

- **Identity**: Never deleted. May be deactivated.
- **Organization**: Never deleted. May be suspended or archived.
- **OrgMember**: Never deleted. May be deactivated (leaves org but record remains).
- **Relationship**: Never deleted. May be archived (history preserved).
- **Proposal**: Never deleted. May be superseded by new version.
- **Invoice**: Never deleted. May be voided (with audit trail).
- **Payment**: Never deleted. Immutable once confirmed.
- **Task**: May be deleted if not started (soft-delete).
- **Message**: Never deleted. May be hidden from UI.
- **KnowledgeDocument**: Never deleted. May be archived.

### 5.3 Audit Rules

Every entity mutation must be logged in `activity_logs` with:
- Action (created, updated, deleted, archived, restored)
- Entity type and ID
- Identity who performed the action
- Previous and new state (for critical entities)
- Timestamp

### 5.4 AI Ownership

Every entity may have an associated AI memory:
- **Executive AI**: Owns organization-level context, founder preferences, business strategy
- **Relationship AI**: Owns relationship history, communication patterns, sentiment
- **Knowledge AI**: Owns document embeddings, semantic indices, retrieval context
- **Finance AI**: Owns financial patterns, anomaly detection, forecasting
- **Operational AI**: Owns workflow patterns, bottleneck detection, optimization

---

## 6. Event Architecture

### 6.1 Canonical Events

| Event | Domain | Payload | Consumers |
|-------|--------|---------|-----------|
| `identity.created` | identity | identity_id, name, email | automation (welcome), search (index) |
| `organization.created` | organization | org_id, name, owner_identity_id | ai (create org context), search (index) |
| `organization.member.joined` | organization | org_id, identity_id, role | communication (notify), ai (update context) |
| `organization.switched` | organization | identity_id, from_org_id, to_org_id | ai (load new context) |
| `relationship.created` | relationship | rel_id, org_id, type, display_name | knowledge (create folder), search (index) |
| `relationship.updated` | relationship | rel_id, changes | ai (update memory) |
| `knowledge.imported` | knowledge | doc_id, org_id, summary | ai (index vectors), search (index) |
| `proposal.generated` | proposal | proposal_id, org_id, relationship_id, title | automation (notify sales), search (index) |
| `proposal.sent` | proposal | proposal_id, destination_email | communication (email), automation (schedule followup) |
| `proposal.accepted` | proposal | proposal_id | automation (create project), finance (create invoice) |
| `invoice.issued` | finance | invoice_id, org_id, relationship_id, amount | communication (notify), automation (schedule payment reminder) |
| `payment.received` | finance | payment_id, invoice_id, amount, method | automation (reconcile), ai (update cash position) |
| `task.completed` | work | task_id, org_id, completed_by | automation (next step), ai (update workload) |
| `conversation.recorded` | communication | message_id, conversation_id | ai (update memory), search (index) |

### 6.2 Event Bus Rules

1. Events are published to an internal event bus (not external message queue for v1).
2. Consumers are registered at module startup.
3. Events are fire-and-forget within a request lifecycle.
4. Critical events (payment, invoice) are persisted to an `event_log` table for replay.
5. Automation engine subscribes to events for workflow triggers.

---

## 7. AI Architecture

### 7.1 AI Layer Model

```
User Request
    │
    ▼
Intent Resolution (Identity + Organization Context)
    │
    ├── Executive AI → Business Q&A, Recommendations, Alerts
    ├── Relationship AI → Profile Enrichment, Sentiment, Communication
    ├── Knowledge AI → Document Retrieval, Summarization, Q&A
    ├── Finance AI → Forecast, Anomaly, Cash Position
    ├── Operational AI → Workflow Optimization, Bottleneck Detection
    └── Communication AI → Message Drafting, Translation, Sentiment
    │
    ▼
Response Assembly
    │
    ▼
Output
```

### 7.2 Model Routing

| Request Type | Default Model | Escalation | Purpose |
|-------------|---------------|------------|---------|
| Executive Q&A | `gpt-4o-mini` | `gpt-4o` | Business reasoning, recommendations |
| Proposal Generation | `gpt-4o-mini` | `claude-sonnet-4` | Creative content, structured output |
| Knowledge Retrieval | Embedding model | — | Semantic search, no escalation needed |
| Communication | `gpt-4o-mini` | — | Drafting, quick responses |
| Finance Analysis | `gpt-4o-mini` | `gpt-4o` | Numbers, patterns, forecasts |

### 7.3 Memory Architecture

- **Identity Memory**: Per-person persistent memory (preferences, facts, context).
- **Organization Memory**: Per-org persistent memory (business context, strategy).
- **Relationship Memory**: Per-relationship interaction history.
- **Knowledge Memory**: Vector index of all organizational knowledge.
- **Session Memory**: Ephemeral conversation context within a session.

### 7.4 Free-model-first Policy

The default AI tier is always the free or low-cost model (`gpt-4o-mini`). Escalation to paid models (`claude-sonnet-4`, `gpt-4o`) occurs only when:

1. The free model fails to generate a valid response.
2. The user explicitly requests a higher-quality response.
3. The task requires capabilities not available in the free tier.
4. The organization has configured a paid AI tier.

---

## 8. Organization Switching

### 8.1 Architecture

```
Identity (sid_abc123)
    │
    ├── OrgMember: Panchi Club (role: owner)
    ├── OrgMember: SHUNYA Labs (role: admin)
    └── OrgMember: Future Org (role: member)
```

### 8.2 Switching Flow

1. Identity signs in → `POST /api/v1/founder/signin` → session has `identity_id`.
2. Identity selects org → `POST /api/v1/organizations/{id}/switch` → `session["current_org_id"]` = org_id.
3. All subsequent API calls scoped by `current_org_id`.
4. Identity can switch orgs without re-authentication.

### 8.3 Permissions

Role hierarchy per organization: viewer < member < manager < admin < owner.

- **owner**: Full control, can delete/transfer org, manage billing
- **admin**: Can manage members, settings, all data
- **manager**: Can manage operational data, approve proposals
- **member**: Can create and edit their own data
- **viewer**: Read-only access

### 8.4 Ownership

- An Organization always has exactly one owner.
- Owner can transfer ownership to another org member.
- Owner can delete the organization (soft delete with grace period).

### 8.5 Delegation

- An org member can delegate specific capabilities to a consultant/contractor
- Delegation is time-bound and scope-limited
- Delegated members appear as "Consultant" in the org

### 8.6 Consultant Access

- Consultants can be invited with `role="consultant"` 
- Consultant access is read-only by default, with granular write permissions
- Consultants are visible to admins but not listed in the main team view
- Consultant access expires automatically

### 8.7 Organization Isolation

- Data is isolated by `organization_id` at the query level
- No cross-organization data access is possible through the API
- The `whoami` endpoint lists all orgs the identity belongs to
- Search results are scoped to the current organization

---

## 9. Industry Pack Architecture

### 9.1 Pack Structure

```
industry_packs/{industry}/
├── __init__.py          # Pack registration
├── terminology.py       # Industry-specific terminology mapping
├── templates/           # Industry-specific templates (proposals, invoices)
│   ├── proposal.html
│   ├── invoice.html
│   └── itinerary.html
├── ai_prompts/          # Industry-specific AI prompts
│   ├── proposal_prompt.txt
│   └── knowledge_prompt.txt
├── workflows/           # Industry-specific workflows
│   └── booking.py
├── reports/             # Industry-specific report templates
│   └── itinerary.pdf
├── compliance/          # Industry-specific compliance rules
└── integrations/        # Industry-specific integrations (API connectors)
```

### 9.2 Pack Rules

- Packs may NEVER modify Core entities.
- Packs may add new entity types but must extend from a base entity.
- Packs may override templates but must extend from base templates.
- Packs may add AI prompts but must use Core AI infrastructure.
- Packs may add terminology mappings only.
- Packs must be optional — Core must work without any pack installed.

### 9.3 Industry vs Core Decision

| Concern | Core | Industry Pack |
|---------|------|---------------|
| Relationship types | Customer, Supplier, Employee | Guest, Tour Operator, Hotelier |
| Proposal sections | Header, Itinerary, Pricing, Terms | Day-wise itinerary, Hotel options, Flight details |
| AI prompts | Generic business proposal | Travel destination enrichment |
| Report templates | Standard proposal PDF | Brochure-style travel proposal |
| Terminology | Organization, Relationship, Proposal | Company, Guest, Package |
| Workflows | Create → Approve → Execute | Booking → Payment → Travel → Review |

---

## 10. Deployment Architecture

### 10.1 Production Stack

```
┌─────────────────────────────────────────────────────────┐
│                     Public Website                        │
│              shunyaos.com (Next.js / Flask)               │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS
┌────────────────────────▼────────────────────────────────┐
│                  Reverse Proxy (Nginx)                    │
│          SSL termination, static files, rate limiting     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                  Application (Gunicorn)                   │
│              Workers: 2 (horizontal scale)                │
│              Single Flask process                         │
└─────┬────────────────────┬────────────────────┬──────────┘
      │                    │                    │
┌─────▼──────┐   ┌────────▼───────┐   ┌───────▼────────┐
│ PostgreSQL │   │  Redis (Cache) │   │  File Storage  │
│  Main DB   │   │  Sessions, Q   │   │  Uploads, PDFs │
└────────────┘   └────────────────┘   └────────────────┘
```

### 10.2 Component Requirements

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Web Server | Nginx | latest | Reverse proxy, SSL, static files |
| Application | Gunicorn + Flask | Python 3.12 | API + UI server |
| Database | PostgreSQL 16 | 16.x | Primary data store |
| Vector Search | pgvector | 0.7+ | Semantic search embeddings |
| Cache | Redis | 7.x | Session store, rate limiting, job queue |
| File Storage | Local filesystem | — | Uploads, PDFs, assets (S3 in future) |
| AI Models | OpenRouter API | — | Model routing and inference |
| Monitoring | Prometheus + Grafana | — | Metrics and alerting |

### 10.3 Configuration

All configuration via environment variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Flask session signing key |
| `REDIS_URL` | Redis connection string |
| `STORAGE_PATH` | File storage root |
| `OPENROUTER_API_KEY` | AI model access |
| `SENTRY_DSN` | Error tracking |
| `LOG_LEVEL` | Logging verbosity |

### 10.4 Backup Strategy

- PostgreSQL: Daily `pg_dump` with 30-day retention
- File Storage: Daily rsync with 7-day retention
- Configuration: Git-tracked with `.env` template
- Migration: All migrations tracked via Alembic

### 10.5 Monitoring

- **Application**: Health endpoint (`GET /health`) — database, cache, storage status
- **Errors**: All 500 errors logged with request ID and traceback
- **Performance**: Request duration logged per endpoint
- **Business**: Event counters per domain (proposals created, invoices paid, etc.)
- **AI**: Model usage, token count, latency, cost per request

---

## 11. Module Acceptance Rules

Before any future module is merged, it must answer:

1. **Which domain owns it?** (Must match one of the 15 canonical domains)
2. **What event creates its primary entity?** (Must emit or consume a canonical event)
3. **What organization does it belong to?** (Must have `organization_id` or be cross-org)
4. **What relationship does it serve?** (If people-facing, must reference a Relationship)
5. **What AI capability does it use?** (Must define which AI domain handles it)
6. **What business workflow requires it?** (Must trace to a real user journey)

If these answers cannot be given, the module must not be merged.

### 11.1 Module Template

```python
# Module: {domain}
# Owner: {org_role}
# Events Emitted: {event_list}
# Events Consumed: {event_list}
# AI Domain: {executive|relationship|knowledge|finance|operational|communication}
# Industry Pack: {none|travel|healthcare|...}
```

---

## 12. Panchi Club Mapping

### 12.1 Business Flow → Architecture

| Panchi Club Activity | SHUNYA Domain | Entities | Industry Pack |
|---------------------|---------------|----------|---------------|
| Customer enquiry | relationship | Relationship (type=customer) | travel |
| Trip planning | proposal | Proposal, ProposalVersion | travel |
| Destination research | knowledge | KnowledgeDocument | travel |
| Pricing & quotation | proposal | Proposal.pricing_json | travel |
| Invoice & payment | finance | Invoice, Payment | — |
| Supplier coordination | relationship | Relationship (type=supplier) | travel |
| Itinerary creation | proposal | Proposal.itinerary_json | travel |
| Customer communication | communication | Message, Conversation | travel |
| Travel execution | work | Task, Approval | travel |
| Post-trip follow-up | relationship | Timeline, Task | travel |
| Executive overview | founder | Executive Dashboard | travel |
| Daily operations | founder | Founder Intelligence | travel |

### 12.2 No Architectural Exceptions

Panchi Club requires **zero** architectural exceptions:

- All capabilities fit within the 15 canonical domains.
- Travel-specific terminology lives in the Travel Industry Pack.
- Proposal templates for travel are pack overrides of base templates.
- AI prompts for destination enrichment are pack-specific.
- The Core remains business-agnostic.
- Every workflow maps to the standard entity hierarchy.

### 12.3 What Exists vs What's Needed

| Capability | Status | Architecture |
|-----------|--------|-------------|
| Organization creation | ✅ Live | `app/organization/` (migrating from `app/for2/`) |
| Member invitation | ✅ Live | `app/organization/` |
| Organization switching | ✅ Live | `app/organization/` |
| Customer relationship | ⬜ Needs migration | `app/relationship/` |
| Proposal generation | ✅ Live | `app/proposal/` (migrating from `app/for1/`) |
| Proposal AI generation | ✅ Live | `app/ai/` |
| Proposal PDF | ✅ Live | `app/proposal/` |
| Proposal web preview | ✅ Live | `app/proposal/` |
| Knowledge upload | ⬜ Needs UI | `app/knowledge/` |
| Knowledge search | ⬜ Needs migration | `app/search/` |
| Invoice management | ⬜ Needs UI | `app/finance/` |
| Payment tracking | ⬜ Needs UI | `app/finance/` |
| Task management | ⬜ Needs migration | `app/work/` |
| Executive dashboard | ✅ Live | `app/founder/` |
| Founder intelligence | ⬜ Needs AI wiring | `app/ai/` + `app/founder/` |
| Universal search | ⬜ Needs build | `app/search/` |
| Communication | ⬜ Needs build | `app/communication/` |
| Automation | ⬜ Needs build | `app/automation/` |

---

## 13. Architecture Governance

### 13.1 Change Process

1. Any proposed change to this architecture must be documented as an Architecture Decision Record (ADR).
2. ADRs are reviewed against the Canonical Domain Registry.
3. If the change introduces a new domain or entity, it must pass the Module Acceptance Rules (Section 11).
4. ADRs are committed to `docs/architecture/adr/`.
5. This document is updated atomically with the ADR.

### 13.2 Violation Detection

- CI/CD pipeline must check that no new module imports from a release-specific namespace (e.g., `app.for1`, `app.for2`).
- CI/CD must verify that all new entities have `organization_id`.
- Code review must verify that every new route is documented in the relevant domain's `routes_*` file.

### 13.3 Migration Completion

The current `app/for1/` and `app/for2/` modules are marked as **transitional**.

They will be migrated to the canonical structure in the following order:

| Module | Target | Timeline | Prerequisites |
|--------|--------|----------|---------------|
| `app/for2/` → Organization | `app/organization/` | FOR-2B | None (models already consolidated) |
| `app/for1/` → Proposal | `app/proposal/` | FOR-2B | None (models already consolidated) |
| `app/for1/engine.py` | `app/proposal/services.py` | FOR-2C | Proposal domain stabilization |
| `app/for1/templates/` | `app/proposal/templates/` | FOR-2C | Template refactor |
| `app/for2/templates/` | `app/organization/templates/` | FOR-2C | Template refactor |

---

*This document is the constitutional blueprint of SHUNYA. All future engineering must conform to this architecture. Release namespaces (FOR-1, FOR-2, etc.) are temporary implementation artifacts and must never appear in permanent code.*