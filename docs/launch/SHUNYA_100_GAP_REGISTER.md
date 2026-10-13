# SHUNYA — 100-GAP REGISTER (5-PERSPECTIVE FORENSIC SWOT)

> **Umbrella register:** this file is one of three child registers under
> `docs/launch/MASTER_GAP_PENDING_REGISTER.md` (all session + tracker gaps,
> live defects, CI hygiene, founder-pending decisions).

**Date:** 2026-10-11
**Repository:** shunya-os/Shunya-OS @ master (3a2d3d3)
**Method:** Five parallel read-only sweeps (frontend UI, backend/API, integrations, product journeys, operations/security) + independent verification of every P1 claim against source. 126 candidate findings deduplicated to exactly 100.
**Scope:** Analysis only — no code changed. Every row cites file:line or observed live behavior.
**Status legend:** UNWIRED = exists but never mounted/called; MOCK = fake data/success; BROKEN = wired but fails; MISSING = absent entirely; PARTIAL = works only sometimes; UNGUARDED = no auth/tenant scoping; OPEN = decision required.

Legend for severity: P1 = fixes before founder acceptance; P2 = before public launch; P3 = maintenance/growth.

---

## PERSPECTIVE A — FRONTEND / UI (18)

| # | Gap | Evidence | Sev | Status |
|---|-----|----------|-----|--------|
| A1 | Calendar surface unmounted — full month-grid + AI-create UI exported but imported nowhere; no calendar in DomainWorkspaceRouter | `frontend/src/components/calendar/calendar-panel.tsx:64` (0 imports repo-wide) | P2 | UNWIRED |
| A2 | Living-workspace shell archived — executive briefing, AI presence, invitations all unmounted ("archived" marker in index) | `frontend/src/components/living-workspace/living-workspace.tsx:204`, `living-workspace/index.ts:2` | P2 | UNWIRED |
| A3 | Command surface archived — `/create`, `/open` slash-commands never mounted; Home re-implements commands | `frontend/src/components/executive-home/command-surface.tsx:24`, `executive-home/index.ts:2` | P2 | UNWIRED |
| A4 | Marketing module dead — MarketingWorkspace + MarketingDashboard exported, zero imports; router mounts only MarketingChannels | `frontend/src/components/marketing/marketing-workspace.tsx:242`, `marketing-dashboard.tsx:46`, `executive-home.tsx:1163` | P2 | UNWIRED |
| A5 | Notification surface absent — no unread bell, no history list; only toasts + preferences wired | `notification-bell.tsx:9`, `notification-history.tsx:23` (0 imports); `executive-home.tsx:73` | P2 | UNWIRED |
| A6 | AwarenessPanel duplicate dead — Home re-implements attention as WhatMattersNow | `living-workspace/awareness-panel.tsx:139` (0 imports); `executive-home.tsx:223` | P3 | UNWIRED |
| A7 | AI insights + file-assistant panels dead | `components/ai/ai-insights.tsx:139`, `components/ai/file-assistant.tsx:122` (0 imports) | P3 | UNWIRED |
| A8 | Dev surfaces unmounted — runtime console, live execution viewer never wired | `runtime-console.tsx:20`, `execution/LiveExecutionPanel.tsx:110` (0 imports) | P3 | UNWIRED |
| A9 | UnifiedAuth page dead — app.tsx builds an inline login instead; combined sign-in/sign-up never used | `components/auth/unified-auth.tsx:44` (0 imports); `app.tsx:358` | P2 | UNWIRED |
| A10 | Onboarding dismantled to 3 steps — org setup, team invite, import, identity, first-object, AI intro, auto-objects steps orphaned (Welcome→Purpose→Complete only) | `onboarding-flow.tsx:9-11` vs `step-organization.tsx:31`, `step-team.tsx:20`, `step-import.tsx:269`, `step-identity.tsx:44`, `step-first-object.tsx:29`, `step-auto-objects.tsx:23`, `step-ai-intro.tsx:22` (0 imports) | P2 | UNWIRED |
| A11 | UBME module UI stranded — module builder, business discovery, dashboard generator, view renderer never mounted | `runtimes/modules/ubme/module-builder.tsx:30`, `business-discovery.tsx:13`, `dashboard-generator.tsx:12`, `view-renderer.tsx:15`; `ubme/index.ts:15` imports only `./api` | P2 | UNWIRED |
| A12 | Invite "Continue" button is a no-op — email-entered invitation submits to an empty handler, zero feedback | `living-workspace.tsx:115` → `:320 <Invitation onAccept={() => {}} />` | P2 | BROKEN |
| A13 | Gmail connect is fake — placeholder `YOUR_GOOGLE_CLIENT_ID` + empty completion callback; Google rejects the ID every time | `step-import.tsx:89`, `step-import.tsx:322` | P2 | MOCK |
| A14 | Memory domain surface unbuilt — empty state tells the user "Memory features are being built" | `executive-home.tsx:965` | P3 | PLACEHOLDER |
| A15 | Homepage hero artwork is a stub — hero renders empty divs, real SVG art never imported | `public/homepage.tsx:25-31` | P3 | PLACEHOLDER |
| A16 | Active-sessions list blank when empty — no empty-state branch | `active-sessions.tsx:122-123` | P3 | MISSING |
| A17 | Analytics tables header-only when empty — revenue/invoice/task/proposal tabs no empty-row branch | `analytics-panel.tsx:191-201, 308, 413, 518` | P3 | MISSING |
| A18 | Empty-state coverage not systematic — several list panels render blank (calendar/docs/knowledge not all verified) | P-003 register; `workspace` panels partial coverage | P2 | PARTIAL |

## PERSPECTIVE B — BACKEND / API / SECURITY (24)

| # | Gap | Evidence | Sev | Status |
|---|-----|----------|-----|--------|
| B1 | execution_log blueprint never registered — any route added to it 404s | `app/execution_log/__init__.py:3` (0 register_blueprint hits) | P3 | UNREGISTERED |
| B2 | Legacy `/api/intelligence/*` route file still ships 11 live handlers despite "removed" comment; blueprint never registered → all 404 | `app/intelligence_routes.py:15`; `app/__init__.py:1175-1177` | P2 | UNREGISTERED |
| B3 | Universal search 404s — mounted SearchBar fetches `/api/v1/search?q=` but backend serves `/api/v1/search/search` | `universal-search.tsx:66` vs `app/search/routes.py:132` | P1 | BROKEN |
| B4 | Knowledge AI-analysis endpoint missing — frontend calls POST `/api/v1/ai/analyze`, no such route | `knowledge/ai-analysis.tsx:60` vs `app/ai/routes.py` | P2 | MISSING |
| B5 | Composer endpoint missing — living-workspace composer posts `/api/v1/composer`, no backend route | `living-workspace.tsx:34` vs backend route table | P2 | MISSING |
| B6 | Generic PDF preview missing — frontend fetches `/api/v1/pdf/<type>/<id>`, backend only has generate/proposal/invoice | `pdf-preview.tsx:40` vs `app/pdf/routes.py:414,446,478` | P2 | MISSING |
| B7 | Team-invite route missing — onboarding posts `/api/v1/orgs/invite`, backend only has `/orgs/<org_id>/invitations` | `step-team.tsx:42` vs `invitation_routes.py:82-96` | P2 | MISSING |
| B8 | Email channel reports success without sending — SMTP placeholder returns DeliveryResult(True) | `app/shunya/executor.py:297-300` | P1 | MOCK |
| B9 | Search action fakes success — outcome engine returns `"Searched for 'query'"` placeholder | `app/outcome_engine.py:417-421` | P2 | MOCK |
| B10 | Execution-intelligence stub wired into production — next-actions/portfolio always empty | `app/execution_intelligence/__init__.py:148,175` used by `app/decision/engine.py:360`, `app/orchestrator/engine.py:28` | P2 | MOCK |
| B11 | Demo seeder exposed in production — POST `/api/v1/for2/seed` hardcodes Panchi Club + Nishesh | `app/for2/routes.py:481-495` | P2 | STUB |
| B12 | Awareness API swallows failures into 200 with raw error strings, no logging | `app/intelligence/awareness_api.py:55-57, 153-157` | P2 | STUB |
| B13 | CRM + knowledge-doc handlers return 500 with zero logging — failures untraceable | `app/crm/routes.py:52-53,79-80`; `app/documents_knowledge/routes.py:96-97` (no logging import) | P2 | STUB |
| B14 | Import/export + admin handlers return 500 with zero logging | `app/import_export/routes.py:83-85,143,191`; `app/authz/admin_routes.py:104-105,142,219,289` | P2 | STUB |
| B15 | Privacy/retention policy tables never written — gates evaluate vacuously | `app/privacy/models.py` (MemoryEligibilityPolicy) — zero instantiation, only queries | P2 | ORPHAN |
| B16 | Global auth middleware exempts ALL `/api/*` and trusts unverified `X-Identity-Id` header — unguarded blueprints are directly exploitable | app/__init__.py:1574-1576 whitelist, :1561-1568 header identity | P1 | FIXED 2026-10-13 (wave B16): no /api/* exemption; authz decorators session-only; adversarial suite test_b16_blueprint_gates.py 32/32 + route-security inventory gate green; reality org-claim validation |
| B17 | Customer-experience routes unauthenticated and unscoped — profile/history/commitments of any customer | `app/customer_experience/routes.py:10-58` (no auth, no tenant filter) | P1 | FIXED 2026-10-13 (wave B16): require_permission + org-scoped lookup, fail-closed 404; B16 suite green |
| B18 | Marketing-intelligence reads cross-tenant by query param `tenant_id` | `app/marketing_intelligence/routes.py:13-16` (8 endpoints, no auth) | P1 | FIXED 2026-10-13 (wave B16): org context session-only; B16 suite green |
| B19 | Sales-intelligence routes expose lead/salesperson data without auth | `app/sales_intelligence/routes.py:8-22` | P1 | FIXED 2026-10-13 (wave B16): 7/7 handlers permission-decorated + org-scoped; B16 suite green |
| B20 | Marketing-OS CRUD/content/lead-capture without authentication | `app/marketing_os/routes.py:11-18` (7 handlers) | P1 | FIXED 2026-10-13 (wave B16): 7/7 handlers decorated + org-scoped; B16 suite green |
| B21 | Entity API returns ALL tenants' entities — `Entity.query.all()`, no auth | `app/api/entity_routes.py:60-67` | P1 | FIXED 2026-10-13 (wave B16): require_permission + org-filtered `_scoped_entity`; B16 suite green |
| B22 | UOP kernel routes read/create by arbitrary tenant_id with no ownership check | `app/kernel/routes.py:82-110` | P1 | FIXED 2026-10-13 (wave B16): scoped object access + decorators; B16 suite green |
| B23 | Reality engine returns any identity's snapshot — falls back to spoofable header or DEMO_IDENTITY | `app/reality_engine/routes.py:34-37, 62-64` | P1 | FIXED 2026-10-13 (wave B16): session-only identity + org-claim validation; B16 suite green |
| B24 | Export all-scope dumps every tenant's data — `Organization.query.all()`, header identity | `app/export/routes.py:62, 71-73, 92-94, 145-146` | P1 | FIXED 2026-10-13 (wave B16): org-scoped export data; B16 suite green |

## PERSPECTIVE C — INTEGRATIONS: EMAIL / WHATSAPP / CONNECTORS (20)

| # | Gap | Evidence | Sev | Status |
|---|-----|----------|-----|--------|
| C1 | Email inbox invisible — backend lists CachedEmail but zero frontend consumes it; received mail unviewable | `app/integration/routes.py:838-894` vs `frontend/src/api/integrations.ts` (no email endpoints) | P1 | UNWIRED |
| C2 | No read/unread semantics — `is_processed` aliased read; no mark-read endpoint or unread count | `routes.py:862,893`; `integration/models.py:409` | P2 | MISSING |
| C3 | No email search/filter or thread grouping — flat paginated rows only | `routes.py:845-857`; `models.py:400` (thread_id stored, unused) | P3 | MISSING |
| C4 | Inbound attachments dropped — Gmail ingestion extracts body only | `gmail_ingest.py:164-194`; `models.py:397-410` (no attachment column) | P2 | MISSING |
| C5 | Compose crippled — cc-only, plain text, no attachments/bcc/HTML/schedule/signature/reply/forward in any send path | `email_core.py:209-338`; `gmail_adapter.py:140-158` (MIMEText only) | P2 | MISSING |
| C6 | No user-facing send surface — send_email wired only to auth/onboarding emails | `auth_routes.py:430,470,591`; `onboarding/routes.py:99` | P1 | MISSING |
| C7 | Templates fixed — exactly 3 hardcoded plain-text builders, no HTML, no template table/UI | `email_service.py:71-136` | P2 | MISSING |
| C8 | No operational inbound path — webhook handles delivery events only; Gmail ingest deprecated (needs local token file); integration sync is a stub | `email_webhook.py:177-181`; `gmail_ingest.py:14-18,50-53`; `providers/email_integration.py:52-58` | P1 | UNWIRED |
| C9 | Delivery status invisible — bounce/complaint/opened state not exposed by any route/UI | `email_models.py:9-33`; `email_webhook.py:108-147` (no consumer) | P2 | MISSING |
| C10 | WhatsApp outbound dead — send_whatsapp called nowhere; adapter declares supports_outbound=False; webhook auto-reply returned in HTTP body Meta never delivers | `communication/whatsapp.py:17-52` (0 callers); `adapters/whatsapp_official/__init__.py:30`; `adapters/whatsapp_adapter.py:22-28`; `whatsapp_webhook.py:133-137` | P1 | UNWIRED |
| C11 | WhatsApp has no user surface — inbound lands only in a Lead + one activity line; no chat/thread, no reply UI | `whatsapp_webhook.py:119-131`; `app/routes.py:_log_activity`; frontend has no WhatsApp component | P1 | MISSING |
| C12 | WhatsApp setup non-persistent — writes tokens to os.environ (process-local); creds cached at import time so setup never takes effect | `app/routes.py:1367-1377`; `communication/whatsapp.py:11-13` | P1 | PARTIAL |
| C13 | WhatsApp media/templates/opt-in unsupported — image/video/audio messages silently ignored | `whatsapp_webhook.py:65-73` | P2 | MISSING |
| C14 | WhatsApp replay idempotency in-memory — webhook replay after restart duplicates leads | `whatsapp_webhook.py:36-62` (`_CACHED_IDS`) | P3 | PARTIAL |
| C15 | Integration Hub "Connect" is fake — saves dummy `connected_via_hub` config; no credential input, no OAuth dialog; every card shows Connected | `integration-hub.tsx:73-85`; `routes.py:646-648` (API key errors after) | P1 | DISPLAY_ONLY |
| C16 | 24 of 33 hub connectors are catalog-only — only 9 have real backend proxies; Slack/Drive/Discord/Telegram/Twilio/SendGrid/Mailchimp/HubSpot/Stripe/GitLab/Notion exist as strings | `service.py:213-330` catalog vs `routes.py:636-823` proxies; "notion" 0 matches in app/ | P1 | DISPLAY_ONLY |
| C17 | Social publish returns 501 — scheduled posts can never reach a platform | `routes.py:366-402` | P2 | MISSING |
| C18 | Integration sync is theater — only EmailIntegration registered; sync() updates timestamps without any API call | `routes_api.py:21-25`; `registry.py:102-113`; `email_integration.py:46-58` | P2 | PARTIAL |
| C19 | Webhook retry never runs in production — run_retry_cycle invoked nowhere; no manual retry in UI | `platform/webhook.py:165-194`; `webhook-config.tsx:22-120` | P2 | PARTIAL |
| C20 | Connector OAuth unusable — Gmail tokens env-only (TESTING), readonly scope only, wrong-key disconnect; no per-connector OAuth for Drive/Slack/365 | `communication/oauth.py:190-202, 24-27, 233-234`; `integration/routes.py:214-229` (API-key strings only) | P1 | PARTIAL |

## PERSPECTIVE D — PRODUCT JOURNEYS (20)

| # | Gap | Evidence | Sev | Status |
|---|-----|----------|-----|--------|
| D1 | Profile save writes a parallel UserProfile row — TeamMember (what auth/team actually render) never updated; display name/email edits desync | `app/profile/routes.py:83-87` vs `app/auth_routes.py:756-757` | P2 | BROKEN |
| D2 | Saved profile renders nowhere — UserProfile consumed only by its own page | `app/__init__.py:1101`; `app/profile/*` | P2 | PARTIAL |
| D3 | Notification preferences never enforced — send paths push to all subscribers regardless; prefs matrix + flat table divergent, UI writes the dead table | `preferences_routes.py:99-157`; `notifications/routes.py:185-277`; `integration/service.py:104-113`; `integration/models.py:471-485` | P1 | BROKEN |
| D4 | No notification history UI — "history" is in-memory toasts; bell fetches only unread count; no mark-read calls | `notification-context.tsx:8,41`; `notification-bell.tsx:16` | P2 | PARTIAL |
| D5 | Export jobs in-memory → 404 after restart/other worker; "zip" accepted but never produced | `app/export/routes.py:32, 35, 118-119` | P2 | PARTIAL |
| D6 | Sessions list fabricated — returns the current request as the whole list; no session store; revoke is a no-op (only session → 400; DELETE log-only) | `app/sessions/routes.py:25-54, 97-109` | P2 | BROKEN |
| D7 | Team invite sends no email — OrgInvitation row + token created, zero email dispatch; token never reaches invitee; accept UI 404s for `/auth`-style links | `app/team/routes.py:94-116` (no email call); `invitation-accept.tsx:34`; `invitation_routes.py:96-131,154` | P1 | BROKEN |
| D8 | Analytics fabricates metrics — Math.random for % change and task hours; revenue/invoice/task reports read seed-only object types, not real finance rows | `analytics-panel.tsx:128, 344`; `analytics-panel.tsx:115,213,333,439` vs `app/objects/seed.py:49-53` | P2 | PARTIAL |
| D9 | Commitment lifecycle gaps — overdue/retry functions never scheduled; typed notes without a status change are dropped (PATCH ignores them) | `commitments/service.py:35-52`; `commitment-workspace.tsx:251-258`; `commitments/routes.py:104-124` | P2 | PARTIAL |
| D10 | Leads cannot advance — UI is read-only lists; zero frontend calls to CRM qualify/assign/sla/follow-up/opportunity/won/lost; POST drops most fields | `lead-management.tsx`/`sales-pipeline.tsx` (0 `/api/v1/crm/*` refs); `app/leads/routes.py:43-47` | P1 | BROKEN |
| D11 | Object delete impossible — no DELETE route anywhere; FE deleteObject 404s | `app/objects/routes.py` (POST/PATCH/GET/lifecycle only); `api/objects.ts:251-261` | P2 | MISSING |
| D12 | Workspace switcher broken — client calls `/api/v1/workspace` (HTML page), `/switch|types|context` have no routes; createWorkspace hits typed-create → "Unknown object type: workspaces" | `client.ts:7`; `workspace_routes.py:30-34`; `objects.ts:182-198`; `app/production/objects.py:129-130` | P2 | BROKEN |
| D13 | Memory can be viewed/deleted but never edited — no PUT/PATCH; UI has no edit/delete controls | `app/memory_api/routes.py:78,196,263,326` (no PUT); `memory-browser.tsx:22,52` | P2 | MISSING |
| D14 | Onboarding completion provisions nothing — bootstrap is client-side only; no org/workspace seeding; new users land on an empty shell | `app.tsx:212-258`; `seed_all_workspaces` (0 callers) | P2 | UNFINISHED |
| D15 | MFA UI 404s — frontend calls `/auth/mfa/*`; backend routes exist at root `/mfa/*` (auth_bp has no prefix); no MFA enforcement for admins | `mfa-setup.tsx:41,53,71` vs `app/production/auth/mfa_routes.py:61-172`; `mfa_challenge:186` | P2 | MISSING |
| D16 | AI model selector decorative — writes localStorage `shunya_ai_model`, nothing reads it | `settings-panel.tsx:503-509` | P3 | BROKEN |
| D17 | Invoice cannot reach the customer — no send route, no FE action, invoice PDF route reads a different object store | `app/finance/routes_api.py` (no send); `governance.py:59-104` (ledger only); `app/pdf/routes.py:478-498`; finance-workspace (0 hits) | P1 | MISSING |
| D18 | Living insights fetch 404s — `/api/v1/ai/insights` vs actual `/api/v1/search/ai/insights` | `living-store.ts:279` vs `search/routes.py:569` | P2 | BROKEN |
| D19 | Home insights/attention data absent — FE-022 failure cascades into Home; no sender for WhatMattersNow/insights | D18 chain; `executive-home.tsx:223` | P2 | PARTIAL |
| D20 | No continuation actions after key creates — leads/invoices/objects lack next-action affordances (audit result: several create flows end with a bare toast) | Journey audit (JR-014..026 related); e.g. `finance-workspace.tsx` create paths | P2 | PARTIAL |

## PERSPECTIVE E — OPERATIONS / INFRASTRUCTURE / SECURITY-OPS (18)

| # | Gap | Evidence | Sev | Status |
|---|-----|----------|-----|--------|
| E1 | No production error alerting — 500 handler logs only; sentry-sdk installed but init only in run.py (never wsgi.py); journald shows repeated unalerted 500s (ai_execution_records table missing on /analytics/dashboard) | `app/__init__.py:180-187`; `run.py:4` vs wsgi; journald 2026-10-11 | P1 | MISSING |
| E2 | No scheduled DB backups — empty crontab; only deploy-time dumps | `crontab` empty; `backups/` (deploy dumps only) | P1 | MISSING |
| E3 | Restore never tested — backup validates via pg_restore --list only; no restore script path; DB user lacks CREATEDB | `backup_database.py:44`; `docs/launch/LAUNCH_BLOCKER_REGISTER.md LB-014` | P1 | MISSING |
| E4 | Uploads/media excluded from every backup — uploads/, media, screenshots, reports unbacked | backup scripts cover PG only; `~/shunya_data/media` 32M, uploads 2.2M | P2 | MISSING |
| E5 | Observability black hole — /metrics exists, nothing scrapes it; no rate-limit telemetry; no dashboards | `app/__init__.py:384-426`; 0 monitoring processes on host | P2 | UNCONFIGURED |
| E6 | Production secrets committed to PUBLIC repo history — .env with SECRET_KEY/DB_PASSWORD added 2026-07-12; repo is public; current keys rotated but history is not purged; uploads incl. PII itineraries tracked in git | `git log --all -- .env` (6b02ac5, 80b60b2); `gh repo view` = PUBLIC; `git ls-files uploads/` | P1 | OPEN |
| E7 | .env.example incomplete/stale — 18 live keys missing from example, 28 example keys absent from live env; GUNICORN_* ignored by unit | `.env.example` vs `.env` diff; systemd unit ExecStart | P3 | PARTIAL |
| E8 | /health and /metrics public — deployment metadata (SHA, rollback SHA, provenance) and uptime/RSS readable by anyone | `HEALTH_TOKEN` absent; live curl of /health | P3 | UNCONFIGURED |
| E9 | Rate limits keyed on the proxy IP — no ProxyFix, all clients share 127.0.0.1; login 10/min and signup 5/hour are site-global; per-account brute force unlimited; no lockout | `app/__init__.py:28`; `auth_routes.py:140,392`; nginx upstream localhost | P1 | PARTIAL |
| E10 | CSRF token emitted but never validated — WTF_CSRF_CHECK_DEFAULT=False; protection rests on JSON content-type + SameSite=Lax | `app/security/csrf.py:32-37`; `app/__init__.py:494` | P2 | PARTIAL |
| E11 | No account lockout / failed-login backoff; password policy is min-6 only; legacy auth path hashes SHA-256 salt+password | `auth_routes.py:140,297` (IP-only); `password_change_routes.py:37`; `app/auth.py:81` | P2 | MISSING |
| E12 | No session expiry — no PERMANENT_SESSION_LIFETIME, no idle timeout, no server-side revocation; stolen cookie lives until browser close; MFA optional even for admins | `app/__init__.py:493-495`; `mfa_routes.py:186` | P2 | MISSING |
| E13 | Audit logs unbounded — sh_audit_logs + genesis_audit_log never purged; RetentionPolicy has no executor; DB growth unmanaged, no logrotate for app logs (err.log 44MB since Aug), no tmp cleanup | `app/security/audit.py:18-36`; `app/privacy/models.py:98-111`; no `/etc/logrotate.d/shunya` | P3 | MISSING |
| E14 | Single point of failure — one VM, one gunicorn (3 workers), no nginx upstream health check, no standby, no external uptime monitor; no feature flags (canon mandates them) | systemd unit; `/etc/nginx/sites-enabled/shunya`; `docs/canon/11_engineering_canon.md:209` | P2 | MISSING |
| E15 | Rollback degrades release identity — rollback.sh never republishes the frontend release or build_identity; post-rollback health flips mismatch flags; requirements check runs after reset (dead) | `infrastructure/scripts/rollback.sh:51-73`; `app/__init__.py:290-318` | P2 | PARTIAL |
| E16 | Stale/inconsistent infra artifacts — repo nginx conf targets docker-era `web:8000` vs live 127.0.0.1:5001; duplicate security headers app+nginx with divergent HSTS | `infrastructure/nginx/production.conf:18` vs `/etc/nginx/sites-enabled/shunya`; `app/__init__.py:91-117` | P3 | PARTIAL |
| E17 | No branded error pages — unknown routes 302→/login?next=...; bare unstyled 500 HTML | live curl `/does-not-exist-xyz` → 302; `app/__init__.py:202-215` | P3 | MISSING |
| E18 | KYC/age-verification method undecided — the only path is admin-attested self-declaration; no documentary KYC provider, no user self-service | `app/authz/admin_routes.py:297-335`; LB-002 residual | P2 | OPEN |

---

## SUMMARY

| Perspective | Rows | P1 | P2 | P3 |
|-------------|------|----|----|----|
| A — Frontend/UI | 18 | 0 | 11 | 7 |
| B — Backend/API/Security | 24 | 10 | 11 | 3 |
| C — Integrations (email/WhatsApp/connectors) | 20 | 8 | 10 | 2 |
| D — Product journeys | 20 | 4 | 14 | 2 |
| E — Operations/Security-ops | 18 | 5 | 6 | 7 |
| **Total** | **100** | **27** | **52** | **21** |

**Cross-cutting themes (top remediation leverage):**
1. **B16 auth middleware** — `/api/*` exempt + spoofable header identity makes B17-B24 (nine unguarded blueprints) exploitable today. This is the single highest-leverage security fix.
2. **E6 secrets in public history** — rotate-and-purge or repo-privacy decision is time-critical (public repo).
3. **Integration honesty (C15/C16/C17/C18/C10)** — hub displays 33 connectors, nine work; "Connected" without credentials; WhatsApp/E-mail outbound dead. Mock surfaces must be truthfully labelled or wired.
4. **D10/D17 — primary business loops (leads→customer, invoice→customer) cannot complete from the UI.**
5. **E9 rate-limit + E11 lockout** — brute-force exposure behind a shared proxy IP.

**Method note:** compiled by five parallel read-only agents from the forensic-capability-inventory methodology; every P1/P0-adjacent claim independently re-verified against source (approval-gated commands, terminal/skills discipline honoured). No files outside this register were modified by this analysis.