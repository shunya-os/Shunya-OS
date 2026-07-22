# SHUNYA OS — Architecture

**Brand:** SHUNYA OS · **AI Identity:** AI@shunyaos.com  
**Stack:** Python 3.11 · Flask · PostgreSQL 16 · Gunicorn · systemd  
**Primary Intake:** Telegram Bot  
**Pipeline:** Shunya — Knowledge → Reasoning → Planner → Workflow

---

## Build Breakdown by Unit

### 1. Core App Unit (`app/__init__.py`)

Flask application factory. Entry point for the entire system.

```
app/
  __init__.py       ← App factory, DB init, blueprints, context processors
  routes.py         ← All HTTP routes and API endpoints
  models.py         ← SQLAlchemy ORM models + inquiry code generator
  services.py       ← Telegram helpers, inquiry parser, summary engine
  cache.py          ← Redis wrapper with in-memory fallback
  celery_worker.py  ← Async task queue (PDF generation, email)
  monitoring.py     ← Sentry integration (optional)
  shunya/           ← AI pipeline package
```

**Responsibilities:**
- `create_app()` factory pattern — avoids circular imports
- Registers `main` and `api` blueprints
- Injects `assistant_identity="AI@shunyaos.com"` into all templates
- `db.create_all()` on startup with graceful failure

**Env config:**
```
SECRET_KEY          — Flask session key
DATABASE_URL        — PostgreSQL connection string
REDIS_URL           — Optional Redis connection
CELERY_BROKER_URL   — Optional Celery broker
SENTRY_DSN          — Optional error tracking
TELEGRAM_BOT_TOKEN  — Bot token (also stored in data/ file)
```

---

### 2. Data Layer Unit (`app/models.py`)

Five PostgreSQL tables with SQLAlchemy ORM.

| Table | Model | Purpose |
|-------|-------|---------|
| `leads` | `Lead` | Customer inquiries, auto-coded with PC prefix |
| `payments` | `Payment` | Guest receipts + supplier payouts (dual ledger) |
| `invoices` | `Invoice` | PDF invoices with tax/discount/currency |
| `suppliers` | `Supplier` | Vendor catalog (hotels, transport, activities) |
| `itinerary_refs` | `ItineraryRef` | Past executed trips for reference |

**Key design decisions:**
- `Lead.code` format: `PC{DD}{MM}{YY}{##}` — space-free, sequential per day
- `Payment.type` dual ledger: `guest_payment` (revenue) vs `supplier_payment` (expense)
- `Invoice.status` lifecycle: `draft` → `paid` → `void`
- `next_inquiry_code()` — counts today's leads + 1, resets daily
- All tables use `created_at` + `updated_at` timestamps
- Shared primary source IDs via Telegrams chat_id

**Relationships:**
- Lead 1→N Payments
- Lead 1→N Invoices
- Payments & Invoices are soft-linked to leads (nullable FK for flexibility)

---

### 3. Routing & API Unit (`app/routes.py`)

Two Flask blueprints: `main` (HTML) and `api` (JSON).

#### Dashboard & CRUD Routes (Blueprint: `main`)

| Route | Methods | Purpose |
|-------|---------|---------|
| `/` | GET | Dashboard — today's stats, recent leads |
| `/leads` | GET | Lead list with search |
| `/leads/new` | GET/POST | Create lead (manual entry) |
| `/leads/<id>` | GET | Lead detail with payments/invoices |
| `/leads/<id>/delete` | POST | Delete lead + cascade |
| `/payments` | GET/POST | Payment list + create |
| `/payments/<id>/delete` | POST | Delete payment |
| `/invoices` | GET/POST | Invoice list + create |
| `/invoices/<id>/pdf` | GET | Download invoice PDF |
| `/reports` | GET | Report dashboard |
| `/settings` | GET/POST | Settings + supplier CRUD |

#### Telegram Bot Routes (Blueprint: `main`)

| Route | Methods | Purpose |
|-------|---------|---------|
| `/telegram/webhook` | POST | Receive Telegram messages, parse → create lead |
| `/telegram/setup` | POST | Save bot token |
| `/telegram/setwebhook` | POST | Register webhook with Telegram API |

#### Shunya Pipeline API (Blueprint: `api`)

| Route | Methods | Purpose |
|-------|---------|---------|
| `/shunya/process` | POST | Full pipeline: inquiry → itinerary → proposal |
| `/shunya/knowledge` | GET | Knowledge base stats + past itineraries |
| `/shunya/summary` | GET | Lead dashboard summary JSON |
| `/shunya/proposal/<id>` | GET | Generate proposal for existing lead |

---

### 4. Shunya Pipeline Unit (`app/shunya/`)

Four-layer AI pipeline. Ordered: Knowledge → Reasoning → Planner → Workflow.

```
shunya/
  __init__.py   ← Package exports all layers
  knowledge.py  ← KnowledgeLayer — destination DB, suppliers, past trips
  reasoning.py  ← ReasoningLayer — customer profiling, risk analysis, strategy
  planner.py    ← PlannerLayer — day-by-day itineraries, proposal text
  workflow.py   ← WorkflowLayer — orchestrator, lead lifecycle, pipeline result
```

**KnowledgeLayer** (`knowledge.py`):
- Loads knowledge base from `data/knowledge-base.md`
- `search_destination(query)` — keyword search over KB, returns `Destination` object
- `get_past_itineraries(destination)` — queries `ItineraryRef` table
- `get_suppliers_by_destination(destination)` — queries `Supplier` table
- Phase 2 target: upgrade to pgvector semantic search

**ReasoningLayer** (`reasoning.py`):
- `analyze_inquiry(inquiry)` → `CustomerProfile` with inferred group type, interests, risks
- `suggest_approach(profile)` → strategy dict (visa needs, lead time, tax notes)
- Destination-specific logic: visa requirements, local taxes, reference pricing
- Pattern matching for group type: couple/family/solo/group from pax text

**PlannerLayer** (`planner.py`):
- `create_itinerary(profile, strategy)` → `ItineraryPlan` with structured days
- `generate_proposal_text(plan)` → markdown proposal body
- `ItineraryDay` — morning/afternoon/evening/accommodation/meals/transport
- `ItineraryPlan` — full plan with cost estimates, tax notes, disclaimers
- Multi-format ready: data structure supports PDF, infographic, video, email

**WorkflowLayer** (`workflow.py`):
- Chains Knowledge → Reasoning → Planner → Output
- `process_inquiry(inquiry)` → `WorkflowResult` with profile, strategy, plan, proposal
- `create_lead_from_inquiry(inquiry)` — auto-generates lead with PC code
- `get_lead_status_summary()` — dashboard data with payment totals

**Pipeline flow:**
```
Inquiry → [Knowledge: fetch KB + past trips + suppliers]
        → [Reasoning: profile customer, assess risks, build strategy]
        → [Planner: structure days, generate proposal text]
        → [Workflow: package result, optionally create lead]
        → Output: proposal JSON + HTML dashboard + API response
```

---

### 5. Telegram Integration Unit (`app/services.py`)

Bot infrastructure for team intake.

**Functions:**
- `save_telegram_token(token)` — persists to `data/telegram_bot_token.txt`
- `get_telegram_token()` — reads saved token
- `set_telegram_webhook(token, url)` — calls Telegram Bot API `setWebhook`
- `parse_inquiry_text(text)` — regex extraction of destination, nights, adults, kids, dates
- `_cached_or_new_code(session)` — cached inquiry code generation
- `get_summary(period)` — aggregate dashboard stats with caching

**Inquiry parsing example:**
Input: `"3 nights Bali for 2 adults 15 Dec"`
Output: `{destination: "Bali", nights: 3, adults: 2, kids: None, dates: "15/12/2026"}`

**Webhook contract:**
```
POST /telegram/webhook  ← Telegram sends this
Body: {"message": {"text": "...", "chat": {"id": 123456789}}}
Response: {"method": "sendMessage", "chat_id": "123456789", "text": "✅ Inquiry logged: PC10072601"}
```

---

### 6. Cache & Async Unit

**Redis Cache** (`app/cache.py`):
- Redis with `memory://` fallback for dev
- `get(key)`, `set(key, value, ttl)`, `delete(key)`
- Used by: inquiry code cache, summary cache
- Graceful degradation — no Redis failure breaks the app

**Celery Worker** (`app/celery_worker.py`):
- Async task queue for PDF generation, email, heavy operations
- `generate_invoice_pdf(invoice_id, path)` — offloads PDF generation
- Requires Redis broker (optional — PDFs fall back to inline generation)

**Monitoring** (`app/monitoring.py`):
- Optional Sentry integration
- `init_monitoring(app)` — safe no-op if `SENTRY_DSN` is not set
- Tags each request with `request_id` and Telegram chat ID

---

### 7. Deployment Unit

#### Production (systemd — Contabo VPS)
```
/var/log/shunya/       ← Logs (access.log, error.log)
/etc/systemd/system/shunya.service  ← systemd unit
Workers: 2 gunicorn    ← port 5000
Auto-restart: yes      ← on boot and crash
Database: PostgreSQL 16 + pgvector
```

#### Container (Docker)
- `Dockerfile` — Python 3.11-bookworm + wkhtmltopdf
- `docker-compose.yml` — web + celery + redis + nginx
- Volume mounts for `data/` (persistent) and `invoices/`

#### CI (GitHub Actions)
- `.github/workflows/ci.yml` — pytest on push/PR

#### Config
- `.env` / `.env.example` — environment variables
- `.gitignore` — excludes data/, .env, token files

---

### 8. Presentation Unit

**Templates** (`templates/`):

| Template | Purpose |
|----------|---------|
| `base.html` | Layout — AI@shunyaos.com branding, nav, sidebar |
| `dashboard.html` | Today's stats, recent leads grid |
| `leads.html` | Lead list with search + create button |
| `lead_form.html` | New lead form (source, name, destination, pax, dates) |
| `lead_detail.html` | Lead view with payments/invoices + action buttons |
| `payments.html` | Payment list + create form |
| `invoices.html` | Invoice list + create form |
| `reports.html` | Sales analytics, destination counts |
| `settings.html` | Telegram bot setup + supplier CRUD |

**Static Assets** (`static/`):
- `css/app.css` — App styles
- `js/app.js` — Frontend interactivity

**Public Site** (`public_site/`):
- `index.html` — Marketing landing page with Telegram intake

---

### 9. PDF Generation

Inline in `_generate_invoice_pdf()` within routes.py:
- Uses `pdfkit` (wkhtmltopdf wrapper)
- Generates A4 invoice with customer details, amounts, tax, discount
- Stored at `invoices/{id}_{invoice_number}.pdf`
- Downloadable via `/invoices/<id>/pdf`

---

### 10. Testing Unit (`tests/`)

| Test File | Coverage |
|-----------|----------|
| `tests/test_models.py` | Model creation, inquiry code format |
| `test_app.py` | App factory initialization |

CI runs via GitHub Actions on push to main.

---

## Dependency Graph

```
Core App (__init__.py)
    ├── Models (models.py) — no deps
    ├── Routes (routes.py) ──→ Models, Services, Shunya
    ├── Services (services.py) ──→ Models, Cache
    ├── Cache (cache.py) — no deps
    ├── Shunya (shunya/)
    │   ├── Knowledge ──→ Models (ItineraryRef, Supplier)
    │   ├── Reasoning ──→ Knowledge
    │   ├── Planner ──→ Reasoning
    │   └── Workflow ──→ Knowledge → Reasoning → Planner, Models (Lead)
    ├── Celery Worker (celery_worker.py) ──→ Services
    └── Monitoring (monitoring.py) — optional Sentry

Deployment:
    ├── Dockerfile + docker-compose.yml
    ├── systemd (shunya.service)
    └── CI (.github/workflows/ci.yml)
```

## Phase 2 Targets

- [ ] **pgvector semantic search** — replace keyword KB lookup with embeddings
- [ ] **LLM integration** — wire OpenAI/Claude into Reasoning & Planner layers
- [ ] **Multi-format delivery** — actual infographic, short clip, movie generation
- [ ] **Public HTTPS** — nginx + certbot for Telegram webhook
- [ ] **Redis/Celery** — production async task queue
- [ ] **Sales analytics** — trend reports, conversion funnels
- [ ] **Customer feedback loop** — automated follow-up campaigns