# Panchi Club Travel OS — Project Tracker

**Project:** Panchi Club Travel Operating System  
**Launch:** Q3 2026 (Internal) → Q4 2026 (Public)  
**Status:** 🟡 Phase 1 — Internal Testing  
**Repo:** https://github.com/trips-ui/panchi-club-backend

---

## Project Timeline

```
Phase 1: Internal (Jul–Oct 2026) ████████████████████ 100%
Phase 2: Public   (Nov 2026+)     ░░░░░░░░░░░░░░░░  0%
```

---

## Phase 1 — Internal Team Dashboard (3–4 months)

Core stack running on Contabo VPS. Team uses Telegram bot + web dashboard for operations.

### ✅ 1.1 Core App Unit — BUILT (v2)

| Item | Status | Notes |
|------|--------|-------|
| Flask app factory (create_app + config_override) | ✅ Done | Supports test overrides, safe defaults |
| PostgreSQL database init | ✅ Done | pgvector-ready, auto-create tables |
| Database models (6 tables) | ✅ V2 | leads, payments, invoices, suppliers, itinerary_refs, **activity_logs** |
| Enums (LeadStatus, PaymentType, InvoiceStatus, LeadSource) | ✅ V2 | Typed enums for status/type fields |
| Database indexes | ✅ V2 | Composite indexes on status+created, source+created, destination |
| ActivityLog model | ✅ V2 | Audit trail per lead: action, detail, user, timestamp |
| Model helpers | ✅ V2 | to_dict(), __repr__(), total_revenue, profit_margin, log_activity() |
| Inquiry code generator (PC format) | ✅ Done | PC{DD}{MM}{YY}{##} — space-free |
| Dashboard CRUD routes | ✅ V2 | /leads, /payments, /invoices, /reports, /settings + /leads/<id>/edit, /leads/<id>/status |
| Activity logging on all actions | ✅ V2 | Auto-log on lead create, payment, invoice, status change |
| Lead edit + status update | ✅ V2 | Edit form, dropdown status change with audit trail |
| Supplier with GSTIN/terms | ✅ V2 | gstin, payment_terms, rating fields in form + list |
| Reports with real data | ✅ V2 | Destinations count — fixed broken queries |
| Request ID middleware | ✅ V2 | Every request gets X-Request-Id, echo from client |
| JSON structured logging | ✅ V2 | python-json-logger for production, plain for dev |
| Security headers | ✅ V2 | X-Content-Type-Options, X-Frame-Options, X-XSS, Referrer, Permissions |
| CORS support | ✅ V2 | flask-cors enabled for /api/* |
| Rate limiting | ✅ V2 | flask-limiter, memory:// fallback, 10/min on webhook |
| Error handlers (400/403/404/405/500) | ✅ V2 | JSON for API routes, HTML fallback for UI |
| Built-in /health endpoint | ✅ V2 | DB ping + table counts + version |
| Context processor (brand, AI@panchi.club) | ✅ V2 | Injected into all templates |
| Tests (11 passing) | ✅ V2 | 8 new Core App tests + 3 model tests |

### ✅ 1.2 Telegram Integration — BUILT (v2)

| Item | Status | Notes |
|------|--------|-------|
| Webhook receiver | ✅ Done | POST /telegram/webhook — creates lead, logs activity |
| Bot token management (file + env) | ✅ V2 | Env var first, file fallback |
| Token validation | ✅ V2 | getMe API to verify token before saving |
| Webhook status | ✅ V2 | getWebhookInfo to check current state |
| Bot commands menu | ✅ V2 | /start, /lead, /status, /help via setMyCommands |
| Inquiry text parser | ✅ V2 | Extracts destination, nights, adults, kids, dates, **budget**, **occasion** |
| Rich reply formatting | ✅ V2 | Location, nights, dates, pax, budget, occasion in reply |
| Dashboard summary engine | ✅ V2 | today/month/all periods, cached |

### ✅ 1.3 Database — COMPLETE

| Item | Status | Notes |
|------|--------|-------|
| PostgreSQL 16 | ✅ Done | Installed + running on Contabo VPS |
| pgvector 0.6.0 | ✅ Done | Extension loaded for future AI search |
| Data migration (SQLite → PG) | ✅ Done | Existing schema + data preserved |

### ✅ 1.4 Shunya Pipeline — BUILT (v2)

| Item | Status | Notes |
|------|--------|-------|
| KnowledgeLayer with structured data | ✅ V2 | 5 destinations (Sri Lanka, Bali, Maldives, Thailand, India) |
| Destination KB parsing | ✅ V2 | Visa, weather, taxes, venues, transport, wedding requirements |
| ReasoningLayer — occasion detection | ✅ V2 | wedding, honeymoon, family, group, solo detected automatically |
| ReasoningLayer — budget estimation | ✅ V2 | Per-destination daily budget estimate |
| PlannerLayer — occasion templates | ✅ V2 | Wedding, honeymoon, family, destination wedding day templates |
| PlannerLayer — multi-format output | ✅ V2 | Markdown + HTML proposal generation (`?format=html`) |
| WorkflowLayer — orchestration | ✅ V2 | Knowledge → Reasoning → Planner, format selection |
| API endpoints | ✅ Done | /shunya/process, /shunya/knowledge, /shunya/summary, /shunya/proposal/<id> |

### ✅ 1.5 Deployment — COMPLETE

| Item | Status | Notes |
|------|--------|-------|
| systemd service | ✅ Done | panchi.service — auto-restart on boot/crash |
| Gunicorn workers (2) | ✅ Done | Port 5000, access + error logs |
| Local testing verified | ✅ Done | Dashboard, leads, PDFs, Shunya pipeline |

### 🔄 1.6 Infrastructure — IN PROGRESS (75%)

| Item | Status | Notes |
|------|--------|-------|
| Redis cache with fallback | ✅ Done | Graceful memory:// fallback |
| Celery worker scaffold | ✅ Done | Async PDF generation |
| Sentry monitoring | ✅ Done | Optional — no-op when not configured |
| GitHub repo | ✅ Done | https://github.com/trips-ui/panchi-club-backend |
| ARCHITECTURE.md | ✅ Done | Build breakdown by unit |
| Dockerfile | ✅ Done | Python 3.11 + wkhtmltopdf |
| docker-compose.yml | ✅ Done | web + celery + redis + nginx |
| CI pipeline | ✅ Done | GitHub Actions — pytest on push |
| **Public HTTPS (nginx + certbot)** | ❌ Pending | Needed for Telegram webhook in prod |
| **Domain setup** | ❌ Pending | For public-facing endpoints |
| **Telegram webhook live** | ❌ Blocked | Blocked on HTTPS |

### 🔜 1.7 Features — PHASE 2

| Item | Status | Priority |
|------|--------|----------|
| Multi-format proposals (PDF, infographic, clip, movie) | 🟡 Scaffold | High |
| Offline executable itineraries | 🟡 Design | High |
| Local union tax guidance per itinerary | 🟡 KB data | Medium |
| Tally-like supplier accounting | 🟡 Scaffold | High |
| Sales analytics dashboard | 🟡 Partial | Medium |
| Activity history per lead | 🔴 Not started | Medium |
| Customer feedback mapping | 🔴 Not started | Low |
| Follow-up automation | 🔴 Not started | Low |

---

## Build Units — Completion Status

(from ARCHITECTURE.md)

| # | Unit | Status | Coverage |
|---|------|--------|----------|
| 1 | Core App (app/__init__.py) | ✅ Built (v2) | Factory, DB, blueprints, request IDs, JSON logging, security headers, CORS, rate limiting, error handlers, health endpoint, config_override for testing |
| 2 | Data Layer (app/models.py) | ✅ Built (v2) | 6 tables (new: activity_logs), enums, indexes, to_dict, __repr__, helper properties |
| 3 | Routing & API (app/routes.py) | ✅ Built (v2) | 20+ routes, activity logging, status updates, lead edit, supplier gstin/terms, API activity log, fixed reports |
| 4 | Shunya Pipeline (app/shunya/) | ✅ Built (v2) | 4 layers, 5 destinations KB, occasion detection, wedding templates, HTML proposals, structured venue data |
| 5 | Telegram Integration (app/services.py) | ✅ Built (v2) | Token validation, webhook info, send_message, bot commands, occasion/budget extraction, better reply formatting, env var + file fallback |
| 6 | Cache & Async (app/cache.py, celery_worker.py) | ✅ Built (v2) | Redis + mem fallback, stats, Celery tasks for PDF + activity logging, lazy init |
| 7 | Deployment (systemd, Docker, CI) | ✅ Built (v2) | Fixed Dockerfile (wsgi:app), docker-compose with pgvector/postgres, nginx.conf, CI pipeline, Procfile |
| 8 | Presentation (templates/) | ✅ Built (v2) | Enhanced base.html (nav icons, flash, brand), CSS (stat cards, responsive, themed buttons), JS (auto-highlight, flash dismiss) |
| 9 | PDF Generation (app/cache.py + routes.py) | ✅ Built (v2) | Consolidated in cache.py with Celery async + inline fallback, company-branded template, proper tax_rate/due_date/paid_at |
| 10 | Testing (tests/ + test_app.py) | ✅ Built (v2) | 36 tests total: 8 Core App, 3 Models, 25 Routes/Services/Pipeline — covers routes, webhook, API, services, pipeline, settings, 404s |

---

## Known Issues & Bugs

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | python-dotenv version conflict (system 1.0.1 vs hermes 1.2.2) | Low | 🟡 Not blocking |
| 2 | Public here.now page expired (24h from Jul 2) | Low | 🔴 Needs email sign-in for permanent |
| 3 | Telegram webhook needs public HTTPS | High | 🔴 Blocked on nginx + certbot setup |
| 4 | KB still plain markdown (no vector search) | Low | 🟡 Phase 2 |
| 5 | Plotly/pandas not in dependencies (for reports) | Low | 🟡 Phase 2 |

---

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary intake | Telegram | Team preference, webhook-based, lightweight |
| Database | PostgreSQL 16 | Production-ready, pgvector for AI search |
| AI pipeline | Shunya (4-layer) | Clean separation: Knowledge → Reasoning → Planner → Workflow |
| Inquiry codes | PC{DD}{MM}{YY}{##} | No spaces, auto-sequential per day, globally unique |
| Assistant identity | AI@panchi.club | Consistent brand across dashboard, Telegram, proposals |
| Deployment | systemd + gunicorn | Direct VPS control, no container overhead for internal phase |
| Caching | Redis + memory fallback | Zero-crash on Redis failure |
| PDF generation | wkhtmltopdf | Simple, no browser dependency |

---

## Phase 2 — Public Launch Checklist

- [ ] Public HTTPS — nginx + certbot + domain
- [ ] Live Telegram webhook (requires HTTPS)
- [ ] Multi-format delivery: real infographic, short video, short movie
- [ ] LLM integration — wire API into Reasoning & Planner
- [ ] pgvector semantic search for knowledge base
- [ ] Redis + Celery in production
- [ ] Sales analytics — conversion funnels, trend reports
- [ ] Customer feedback loop — automated follow-up
- [ ] Public landing page with self-service
- [ ] Supplier payment reconciliation (Tally-like)
- [ ] Multi-destination wedding support
- [ ] Payment gateway integration

---

## Current Sprint

```
Focus: Phase 1 hardening
  1. Set up nginx + certbot → HTTPS → Telegram webhook live
  2. Fill knowledge base with destination data
  3. Test end-to-end Telegram → lead → proposal flow
```

## Key Contacts

| Role | Name |
|------|------|
| Owner | Rajat |
| Team | Chaya |
| AI Identity | AI@panchi.club |
| Bot Account | trips-ui (GitHub) |