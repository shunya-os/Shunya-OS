# SHUNYA OS — COMPLETION LEDGER (v1.0)

**Generated:** 2026-10-19
**Branch:** feat/commandpalette-ai (HEAD de9122f)
**Authority:** G1.2 Master Product Execution Directive
**Status:** Evidence-grounded assessment — NOT a launch-readiness declaration

---

## STATUS VOCABULARY

| Status | Definition |
|--------|------------|
| VERIFIED COMPLETE | Behaviour implemented + supported by appropriate evidence |
| IMPLEMENTED, INCOMPLETELY VERIFIED | Implementation exists, material verification missing |
| PARTIALLY IMPLEMENTED | Some of required journey exists; material parts absent/disconnected |
| NOT IMPLEMENTED | Required functionality absent |
| BLOCKED | Dependency/decision/access constraint prevents progress |
| NEEDS PRODUCT DECISION | Requirements conflict or design/permission decision unresolved |
| NOT REPRODUCED | Observed issue cannot be reliably triggered |
| NOT APPLICABLE | Explicit reason why this is not required |
| OPEN | Incident or issue acknowledged, resolution pending |

---

## 1. PRODUCT CONSTITUTION & NON-NEGOTIABLE PRINCIPLES

*Source: docs/governance/CONSTITUTION_v1.0.md, docs/governance/CANONICAL_PRODUCT_DECLARATION.md*

| Principle | Codified | Current State |
|-----------|----------|---------------|
| One identity across all organizations | Yes (Product Declaration §1.2) | PARTIAL — identity convergence still in progress (TeamMember → SHUNYAIdentityModel migration not complete) |
| Organization isolation | Yes (§1.3) | VERIFIED COMPLETE — cross-tenant read isolation proven with adversarial tests |
| Executive Home as primary landing surface | Yes (§1.4) | IMPLEMENTED, INCOMPLETELY VERIFIED — PrimaryWorkspace renders, but browser-verified content/layout completeness unproven |
| ⌘K Universal Search | Yes (§1.5) | PARTIALLY IMPLEMENTED — CommandPalette exists, fully tested for AI queries. Universal object search completeness not browser-verified |
| Workspace-as-container (not page) | Yes (§1.6-1.7) | PARTIALLY IMPLEMENTED — PrimaryWorkspace with workspace bar exists, but lifecycle (suspend/resume/archive) not implemented |
| AI as embedded operating layer | Yes (§1.8) | IMPLEMENTED, INCOMPLETELY VERIFIED — AI/chat pipeline works in production, but context-aware sidebar not verified in browser |
| No "coming soon" placeholders | Yes | NOT VERIFIED across all surfaces |
| Honest capability disclosure | Yes (§1.8) | NOT VERIFIED — several mock/integration gaps exist (see Section 4) |

---

## 2. R28 DISPOSITION — BOUNDED COMMAND PALETTE CERTIFICATION

**Status per R28 report:** 36/36 validated assertions, exit 0

| Scenario | BROWSER VERIFIED | Evidence |
|----------|-----------------|----------|
| A — Out-of-order success | YES | Controlled hold/release with real Chromium |
| B — Stale error after newer success | YES | Error injection via test-only `__test__/error-ai-response` |
| C — Dismissal while pending | YES | Escape key, stale completion discarded |
| D — Failure and retry | YES | 503 error state rendered; dismiss + retry succeeds |
| E — New request after dismissal | YES | Previous dismissal does not suppress fresh queries |
| F — Duplicate action keys | YES | Zero console warnings across repeated cycles |

**Limitations (NOT certified by R28):**
- Full WCAG accessibility (axe-core not run)
- PostgreSQL schema/migration parity (SQLite-only)
- Multi-role authorization journeys (owner role only)
- VAPID startup-race HTTP 500 (NOT REPRODUCED)
- Public-launch readiness
- Any feature beyond CommandPalette stale-response protection

---

## 3. MASTER FEATURE INVENTORY

### 3.1 Identity & Authentication

| Feature | Status | Evidence | Remaining Work |
|---------|--------|----------|----------------|
| Login (email/password) | VERIFIED COMPLETE | HTTP 200, session cookie set, redirect to workspace | — |
| Login (invalid credentials) | VERIFIED COMPLETE | HTTP 401 returned | — |
| Logout | VERIFIED COMPLETE | Session cleared, redirect | — |
| Session persistence | VERIFIED COMPLETE | Cookie-based, survives requests | — |
| Cookie security (Secure, HttpOnly, SameSite) | VERIFIED COMPLETE | Confirmed in production | — |
|| Signup flow | VERIFIED COMPLETE (browser) | 2026-10-19 Playwright HTTPS journey: public page → Get Started CTA → signup form; client validation blocks short password; honest delivery-status reporting (email_status emitted on response); resend recovery button on delivery failure. Local test stack only. | — |
| OAuth (Google/GitHub) | NOT IMPLEMENTED | Routes exist, no client IDs configured | Decision, configuration, testing |
|| Email verification | VERIFIED COMPLETE (browser, isolated stack) | 2026-10-19: verify token retrieved via isolated test route, POST /api/v1/auth/verify-email → 200, "Email verified successfully!" shown; Secure+HttpOnly session cookie flows (domain=127.0.0.1 path=/ secure=true httpOnly=true). Resend 422 defect FIXED — tag charset violation in email_core._send_via_resend (business_event_id with colons); sanitized via _resend_tag_value(). Signup delivery now reports honest email_status ("accepted" from Resend API, 200). 24h token expiry enforced. Request-verification rate-limited (5/hr, matching signup). Login page shows "Resend verification" on 403-unverified error. | Verify real inbox delivery in a staging environment |
| Password reset | IMPLEMENTED, INCOMPLETELY VERIFIED | Routes exist | End-to-end test |
| MFA | NOT IMPLEMENTED | Path mismatch documented in gap register | Requires product decision |
| Identity convergence (TeamMember → SHUNYAIdentityModel) | PARTIALLY IMPLEMENTED | 0 rows in identity_profiles; session persists email identity for no-org users while workspace ownership uses TeamMember id — bridged at resolver level in app/authz/workspace_context.py | Canonical identity-row convergence, data migration |

### 3.2 Onboarding

| Feature | Status | Evidence | Remaining Work |
|---------|--------|----------|----------------|
| First-use flow (register → workspace) | VERIFIED COMPLETE (browser, isolated stack) | 2026-10-19 real-browser journey (Playwright, HTTPS, isolated backend): public entry → signup (client validation) → email verification (Secure/HttpOnly cookie) → auto-login → onboarding → Executive workspace shell → CommandPalette opens → AI query returns a real answer. 22/22 assertions PASS. Scope resolution for fresh verified users was broken (session email vs numeric TeamMember-id ownership) and fixed in app/authz/workspace_context.py + app/ai/routes.py. | Production login-flow retest after deploy; shell hydration endpoints (reality/events/execution) remain org-scope-only — personal-scope policy decision pending |
| Object creation API | VERIFIED COMPLETE | POST /api/v1/objects/ writes to sh_objects | — |
| Welcome screen | VERIFIED COMPLETE | Step-welcome component renders | — |
| AI intro step | IMPLEMENTED, INCOMPLETELY VERIFIED | Step-ai-intro exists | Verify in browser journey |
| Import step | IMPLEMENTED, INCOMPLETELY VERIFIED | Step-import exists | Verify in browser journey |
| Demo data experience | PARTIALLY IMPLEMENTED | 3 pre-seeded orgs described in product declaration | Verify seeded orgs exist and can be explored |
| Complete step | IMPLEMENTED, INCOMPLETELY VERIFIED | Step-complete exists | Verify in browser journey |

### 3.3 AI & Intelligence

| Feature | Status | Evidence | Remaining Work |
|---------|--------|----------|----------------|
| Chat completion | VERIFIED COMPLETE | Groq, llama-3.3-70b, <200ms in production | — |
| Provider chain (fallback) | VERIFIED COMPLETE | groq → gemini → openrouter → cloudflare → local | — |
| Web search integration | VERIFIED COMPLETE | DuckDuckGo, results injected as context | — |
| CommandPalette AI query | VERIFIED COMPLETE (bounded) | R28 certification, controlled race proof | — |
| Stale-response protection | VERIFIED COMPLETE | requestId tracking, useRef dismissed flag | — |
| Error state rendering | VERIFIED COMPLETE | 503 error renders warning glyph + text | — |
| Retry flow | VERIFIED COMPLETE | Dismiss error → new query → success | — |
| Evidence logging | IMPLEMENTED, INCOMPLETELY VERIFIED | evidence_records table populated | Verify completeness of ALL AI paths |
| Structured output | IMPLEMENTED, INCOMPLETELY VERIFIED | LLMRuntimeService.invoke_structured exists | Integration test |
| AI governance / safety gate | PARTIALLY IMPLEMENTED | check_request_safety exists; policy completeness unverified | Test safety gate edge cases |
| Context-aware AI sidebar | NOT VERIFIED | Product declaration describes AI that knows workspace/object | Major implementation gap |
| Telemetry (model_runs) | DISCONNECTED | model_runs table empty | Wire AI chat to unified telemetry |

### 3.4 Frontend & UI

| Feature | Status | Evidence | Remaining Work |
|---------|--------|----------|----------------|
| Homepage renders | VERIFIED COMPLETE | HTTP 200, SPA renders | — |
| Responsive rendering | VERIFIED COMPLETE | Desktop/tablet/mobile verified | — |
| PWA manifest | VERIFIED COMPLETE | /manifest.json → 200 | — |
| PWA icons | BROKEN | icon-192.png, icon-512.png, favicon.ico → 404 | Generate/distribute icon files |
| CommandPalette (⌘K) | VERIFIED COMPLETE (bounded) | Opens, filters, submits AI queries | — |
| AiResultBanner | VERIFIED COMPLETE (bounded) | Loading/error/success states, dismiss | — |
| Workspace bar | PARTIALLY IMPLEMENTED | Renders in PrimaryWorkspace | Suspend/resume/archive lifecycle |
| Executive Home content | IMPLEMENTED, INCOMPLETELY VERIFIED | Renders metrics, milestones, AI summary | Browser-verify completeness against Product Declaration |
| Universal Search | PARTIALLY IMPLEMENTED | CommandPalette searches actions; full object search not verified | Object search integration |
| Calendar surface | PARTIALLY IMPLEMENTED | Code exists, mounting decision pending | Product decision |
| Notification bell/dropdown | IMPLEMENTED, INCOMPLETELY VERIFIED | Routes exist, UI not fully exercised | Browser journey test |
| Settings pages | PARTIALLY IMPLEMENTED | Profile, team, export exist; completeness unverified | Audit against expected settings |

### 3.5 Backend & API

| Feature | Status | Evidence | Remaining Work |
|---------|--------|----------|----------------|
| Auth session API | VERIFIED COMPLETE | /api/v1/auth/session works | — |
| Object CRUD | VERIFIED COMPLETE | /api/v1/objects/ creates/reads/updates | — |
| Authorization engine | VERIFIED COMPLETE | 43 permission keys, role CRUD, owner bypass | — |
| B16 route-security inventory | VERIFIED COMPLETE | All routes decorated, adversarial suite 32/32 | — |
| VAPID push notifications | VERIFIED COMPLETE (via test) | Returns 200 with valid key, cryptography installed | Startup-race 500 NOT REPRODUCED |
| Rate limiting | VERIFIED COMPLETE | flask-limiter configured, ProxyFix applied | — |

### 3.6 Security

| Feature | Status | Evidence | Remaining Work |
|---------|--------|----------|----------------|
| HSTS | VERIFIED COMPLETE | Header present, CI-enforced | — |
| HTTPS-only | VERIFIED COMPLETE | HTTP→301→HTTPS, tested in CI | — |
| Cross-tenant read isolation | VERIFIED COMPLETE | Adversarial tests + CI | — |
| Route security B16 | VERIFIED COMPLETE | All routes decorated, 32/32 adversarial tests | — |
| Credential exposure (hardcoded DB URL) | OPEN | debug_space_creation.py previously had hardcoded postgresql://...@localhost:5433/shunya_db (NOW REMEDIATED in working tree) | Owner confirmation through approved process |
| Secrets in public Git history | OPEN | Documented as E6 in gap register | Repository history cleanup |
| Input validation safety | IMPLEMENTED, INCOMPLETELY VERIFIED | NUL-byte sanitation added (B3) | Audit remaining endpoints |

---

## 4. KNOWN DEFECTS, GAPS & LAUNCH BLOCKERS

*Consolidated from: MASTER_GAP_PENDING_REGISTER.md, CURRENT_TRUTH_MATRIX.md, LAUNCH_DASHBOARD.md, R28 report*

### 4.1 Critical / P0 (Must Resolve for Launch)

| ID | Issue | Source | Status | Owner |
|----|-------|--------|--------|-------|
| SEC-01 | Credential exposure incident (hardcoded DB URL in debug_space_creation.py) — REMEDIATED in working tree and fail-closed guard verified by subprocess tests (7 pass, G1.11); incident remains OPEN pending owner sign-off and history decision | R26/R27/R28, G1.10, G1.11 | OPEN (remediation verified, closure needs owner) | Owner confirmation |
| SEC-02 | Secrets in public Git history (E6) — scope established G1.10: (a) hardcoded DB URL in commit af3392b/afb7cdc, already an ancestor of origin/master (826 commits deep, i.e. published); (b) connection URLs (user-only shape) in tracked certification logs artifacts/r6b25/*.log + artifacts/r6b27/*.log — present in origin/master despite .gitignore (already-tracked files are not untracked by ignore rules); (c) inline test credential (value redacted) in tracked scripts/validate_m2_postgres.sh, still present in HEAD and working tree. Values NOT reproduced. Local remediation commit 13d33d4 (removes cert logs) exists only on unmerged branch fix/security-remediate-exposed-artifacts. No history rewrite performed | Gap Register, G1.10 | OPEN — history rewrite + credential rotation require owner authorization | Owner + coordinated force-push |
| AUTHZ-01 | Admin has org.edit but NOT org.view — unusual permission design | R26 source inspection | NEEDS PRODUCT DECISION | Founder |
| LB-001 | Founder acceptance walkthrough + sign-off | Gap Register | PREPARED (doc exists) | Founder execution + signature |
|| PWA-01 | PWA icons return 404 | Truth Matrix | CONFIRMED FIXED — all PWA assets exist in frontend/public/ and frontend/dist/, serve HTTP 200 from dev server and production build |

### 4.2 High / P1

| ID | Issue | Source | Status |
|----|-------|--------|--------|
| ONB-01 | Signup flow has no signup link/button in login UI | Truth Matrix | RESOLVED (browser-verified 2026-10-19: public page "Get Started" CTA reaches signup; journey also reaches it via login) |
| ONB-02 | Full onboarding E2E not tested as new user | Truth Matrix | RESOLVED (2026-10-19 browser journey: onboarding steps → complete → shell; 22/22 PASS) |
| JRN-01 | No browser-verified end-to-end user journey (register → login → workspace → first action) | R28 | RESOLVED (2026-10-19: full journey browser-verified; AI first action returns real answer; still never touched production) |
| UI-01 | Profile settings desync with backend | Gap Register | PARTIAL |
| UI-02 | Empty states not systematic | Gap Register | PARTIAL |
| INT-01 | Email inbox has no UI (routes exist) | Gap Register | NOT IMPLEMENTED |
| INT-02 | WhatsApp outbound dead + no UI | Gap Register | NOT IMPLEMENTED |
| VAPID-01 | HTTP 500 on first VAPID call (NOT REPRODUCED) | R25, R26, R28 | NOT REPRODUCED |
| A11Y-01 | axe-core scan | R28, G1.3 | PARTIAL — G1.3 scan: homepage 0 violations; signup surfaced contrast/landmark defects that were fixed and re-checked, but the signup page was not re-scanned to a clean zero; full-app WCAG compliance NOT claimed |
| A11Y-02 | Keyboard focus behavior after CommandPalette operations not traced | R28 | NOT RUN |
| A11Y-03 | Screen reader verification not performed | R28 | NOT RUN |
| INFRA-01 | Backup unscheduled, restore untested | Gap Register, Launch Dashboard | NOT IMPLEMENTED |
| INFRA-02 | No structured error logging (Sentry/Prometheus) | Launch Dashboard | NOT IMPLEMENTED |

### 4.3 Medium / P2

| ID | Issue | Source | Status |
|----|-------|--------|--------|
| AUTHZ-02 | Multi-role browser journeys (admin, manager, member, viewer) not tested | R28 | NOT VERIFIED |
| DB-01 | PostgreSQL migration parity not validated | R28 | NOT VERIFIED |
| DB-02 | Legacy tenants table still has FK references | Launch Dashboard, Arch Map | PARTIAL |
| AI-01 | Context-aware AI sidebar not implemented per Product Declaration | Product Declaration | NOT IMPLEMENTED |
| AI-02 | Telemetry (model_runs) disconnected from AI chat | Truth Matrix | DISCONNECTED |
|| UI-03 | 18 FE gaps documented in gap register (surfaces unmounted) | Gap Register | PARTIAL — 5 of 18 gaps verified resolved (A12 invite, A14 memory surface, A16/A17 empty states, PWA-01 icons). 13 remaining (A1 calendar, A2 living-workspace, A3 command, A4 marketing, A5 notification, A6 awareness, A7 AI insights, A8 dev surfaces, A9 unified-auth, A10 onboarding orphans, A11 UBME, A13 Gmail mock, A18 empty states). G10 Frontend/UX still OPEN. |
| | UX-01 | Pre-seeded demo orgs (Wanderlust, Precision, NovaCare) data not verified | Product Declaration | PARTIAL — seed script scripts/seed_demo_orgs.py verified in isolated SQLite (G1.6): 170 UOP objects total, per-org 57/56/57 across Customer, Invoice, Milestone, Conversation, Note; second run created 0 additional objects (idempotency confirmed); 4-layer safety guard verified fail-closed (G1.11: exit 1, no DB created without SHUNYA_SEED_ALLOWED). NOT verified: browser-observed demo data inside the UI; runtime API read-back against a seeded org (not run this milestone). |

---

## 5. TEST COVERAGE & LIMITATIONS

### 5.1 CommandPalette / AI Chat — COMPREHENSIVE

| Level | Coverage | Status |
|-------|----------|--------|
| Unit (vitest) | 11 files, 88 tests (including command-palette-deterministic.test.ts) | ALL PASS |
| Browser (Playwright) | A-F scenarios, hold/release, error injection, duplicate keys | ALL PASS (36+ assertions) |
| Console errors | Filtered for Push API + intentional 503s | CLEAN |

### 5.2 Remaining Test Gaps

| Level | Coverage | Status |
|-------|----------|--------|
| Python backend (pytest) | 175 test files + 13 journey files | PARTIAL (G1.11): targeted suites run now — tests/test_email_subsystem.py::test_send_via_resend_tags_sanitized (1 pass), tests/test_debug_space_creation_safety.py (7 pass), tests/test_test_server_safety.py (7 pass, new); full suite NOT run this session |
| CI verification tests | 17 verification scripts | NOT RUN this session |
| Vitest (remaining) | 7 existing test files | PASS (from R27; re-confirmed R28-era run: 88/88 across 11 files) |
| E2E full user journey | Real-browser Playwright journey (g13-first-user-journey.cjs, HTTPS isolated stack) | PASS 2026-10-19: 22/22 assertions, signup → verify → login → onboarding → shell → CommandPalette → real AI answer → session persists after reload; zero 5xx |
| Accessibility (axe-core) | Available in devDependencies | NOT RUN |
| Multi-role authorization | Owner only tested | NOT VERIFIED |
| PostgreSQL migrations | SQLite-only testing | NOT VERIFIED |
| Performance / load | Not performed | NOT RUN |

---

## 6. ARCHITECTURAL DUPLICATIONS & LEGACY ITEMS

*Source: CANONICAL_ARCHITECTURE_MAP.md, Constitutional Platform Map*

| ID | Item | Current State | Recommended Action |
|----|------|---------------|-------------------|
| ARCH-01 | Objects store: 5 tables (objects, founder_objects, sh_uop_objects, canonical_objects, sh_objects) | canonical_objects + sh_objects = 0 rows, vestigial | Schedule DROP migration |
| ARCH-02 | Identity: TeamMember (legacy) vs SHUNYAIdentityModel (0 rows) | In migration | Continue migration path |
| ARCH-03 | Memory: memory_records (0 rows) vs founder_objects(type=memory) vs rel_ai_memory | Parallel stores | Converge to memory_records |
| ARCH-04 | AI provider chains: app/ai/provider.py (9 providers) vs orchestrator (5 providers) | Duplicate | Consolidate |
| ARCH-05 | AI routes: /api/v1/ai/chat, /api/v1/intelligence/ask, copilot/ask, commercial ask, cfo ask | Multiple ask endpoints | Consolidate to canonical /api/v1/intelligence/ask |

---

## 7. PRODUCTION & DEPLOYMENT READINESS

| Area | Status | Evidence Needed |
|------|--------|----------------|
| Deployment pipeline | CI/CD exists (ci.yml) with test → build → deploy → verify chain | Verified via GitHub Actions |
| Health checks | /health endpoint returns git_commit, release_type | Verified via CI |
| Systemd service | gunicorn running on 127.0.0.1:5001 | Verified via `ss` |
| Database | PostgreSQL 16, 192 tables | Verified (backup exists) |
| Backup | pg_dump exists, restore UNTESTED | Test restore |
| Monitoring | No structured logging (Sentry/Prometheus) | NOT IMPLEMENTED |
| Rollback | Manual via git checkout + service restart | PARTIAL |
| SSL/TLS termination | nginx handles HTTPS | Verified via CI deploy smoke test |
| HSTS | Configured, CI-enforced | VERIFIED |
| CORS | flask-cors configured | VERIFIED |

---

## 8. RANKED WORKSTREAM BACKLOG

### Priority 1 — Security & Identity Foundation

| Workstream | Dependencies | User Impact | Acceptance Criteria |
|------------|-------------|-------------|-------------------|
| SEC-01: Credential incident closure | Owner confirmation | Data exposure risk | Owner confirms resolution through approved process |
| SEC-02: Git history cleanup | Tooling (BFG/git-filter-repo) | Secrets exposed in public history | All secrets removed from Git history |
| ID-01: Identity convergence (TeamMember → SHUNYAIdentityModel) | Architecture decision | Unified identity model | All auth resolves through canonical identity; TeamMember deprecated |
| AUTHZ-01: org.view permission decision | Product decision | Admin access to org settings | Decision recorded; permissions updated or documented as intentional |

### Priority 2 — Core User Journeys

| Workstream | Dependencies | User Impact | Acceptance Criteria |
|------------|-------------|-------------|-------------------|
| JRN-01: Full new-user E2E journey | Signup UI (P2), Onboarding (P2) | New users cannot complete registration | Browser-verified: register → login → workspace → first action |
| ONB-01: Mount signup link in login UI | None | New users cannot create account | Signup link visible in login UI; signup flow completes |
| ONB-02: Onboarding E2E browser test | ONB-01 | Onboarding reliability | Browser test covering full onboarding flow |
| UI-03: Mount unmounted surfaces (18 FE gaps) | Product priority | Users see "coming soon" or broken screens | All surface components mounted and render without error |

### Priority 3 — AI & Intelligence Completeness

| Workstream | Dependencies | User Impact | Acceptance Criteria |
|------------|-------------|-------------|-------------------|
| AI-01: Context-aware AI sidebar | Workspace runtime | AI doesn't know user context | AI sidebar shows workspace-aware insights |
| AI-02: Wire telemetry (model_runs) | AI-01 | Cannot measure AI performance | model_runs table populated on every AI call |
| ARCH-05: Consolidate AI ask endpoints | Architecture decision | Fragmented AI entry points | Single canonical /api/v1/intelligence/ask |
| VAPID-01: Startup-race diagnosis | None | Intermittent 500 on notifications | Root cause established or resolved |

### Priority 4 — Frontend & UX Completeness

| Workstream | Dependencies | User Impact | Acceptance Criteria |
|------------|-------------|-------------|-------------------|
| A11Y-01: axe-core scan | None | Accessibility compliance | Scan executed; violations documented and fixed |
| UI-02: Systematic empty states | None | User sees blank/confusing screens | Every data surface has meaningful empty state |
| PWA-01: Add icon files | None | PWA icons return 404 | All required icons return 200 |
| UX-01: Seed demo orgs with data | None | No demo data to explore | 3 pre-seeded orgs with 50+ objects each, browser-verified |

### Priority 5 — Integrations & Operations

| Workstream | Dependencies | User Impact | Acceptance Criteria |
|------------|-------------|-------------|-------------------|
| INT-01: Email inbox UI | Backend email routes | Cannot read/send email | Browser journey: receive, read, reply to email |
| INFRA-01: Backup automation + restore test | None | Data loss risk | Scheduled backups; restore procedure tested |
| INFRA-02: Structured logging | None | Cannot debug production issues | Sentry/Prometheus integrated |
| DB-02: Legacy tenants FK cleanup | None | Schema debt | FK references to tenants table removed |

---

## 9. IMPLEMENTATION UNDERTAKEN — R28 CLOSURE + G1.3-R2 FIRST-USER JOURNEY

### R28 Closure (prior)
**Changes to `scripts/test_server.py`** (test-only infrastructure):
1. Added `_test_error_ids` set for controlled error injection
2. Added `__test__/error-ai-response/<request_id>` route (only in `if __name__ == "__main__":`)
3. Modified `_check_ai_hold` to return 503 error for flagged request IDs
4. Fixed type mismatch: `body.get("request_id")` → `str(body.get("request_id", ""))` (JSON sends numbers, hold-queue uses string keys)
5. `drain-holds` now also clears `_test_error_ids`

### G1.3-R2 Changes — Production Code

**1. app/communication/email_core.py** — Resend 422 tag charset fix
   - Added `_resend_tag_value()` helper: sanitizes tag name/value fields to only ASCII letters, numbers, underscores, dashes (`re.sub(r'[^A-Za-z0-9_-]', '_', value)`).
   - All three tags (category, business_event_id, notification_type) are now sanitized, so `business_event_id=verify:5:c8fd5f68` (which contains colons) no longer triggers Resend's `422 Tags should only contain ASCII letters, numbers, underscores, or dashes`.
   - Added regression test: `test_send_via_resend_tags_sanitized` (PASS).

**2. app/auth_routes.py** — Honest delivery + expiry + rate limiting
   - Signup response now includes `email_status` field from the send_email result (acceptable values: accepted/sent/logged/failed). Frontend shows honest message + "Resend verification email" button on delivery failure.
   - Request-verification: added `@limiter.limit("5 per hour")` (consistent with signup). `member.created_at` is reset on token regeneration to serve as 24h expiry clock.
   - Verify-email: enforces 24h token expiry. If `member.created_at` is older than 24 hours, returns `400: Verification link has expired. Request a new one.`

**3. frontend/src/components/auth/signup.tsx** — Honest delivery state + resend recovery
   - `defaultSignup` now returns `email_status` from the API response.
   - Success phase shows either "Check your email" (delivered) or "Account created, but the verification email could not be sent right now" (failed) + a "Resend verification email" button wired to `POST /api/v1/auth/request-verification`.
   - Resend confirmation ("Verification email re-sent!") shown on success.

**4. frontend/src/components/auth/login-page.tsx** — Resend verification on unverified login
   - When login fails with a 403 error containing "verify", a "Resend verification email" link appears below the error message. Calls `POST /api/v1/auth/request-verification` with the current email input.

**5. tests/test_email_subsystem.py** — regression test
   - `test_send_via_resend_tags_sanitized`: asserts that a `business_event_id` with colons results in tag values valid per Resend's charset (`^[A-Za-z0-9_-]+$`).

**No production configuration, credentials, or live provider settings were changed. No migrations, commits, pushes, or deployments.**

**Git operations**: None performed. Working tree remains unstaged.

---

## 10. OUTSTANDING PRODUCT DECISIONS NEEDED

| Decision | Options | Impact | Recommended |
|----------|---------|--------|-------------|
| Admin permission: should admin have org.view? | 1. Add org.view to admin role 2. Keep current (owner-only) | Admin users cannot view org settings via whoami API | Option 1 — org.edit without org.view is unusual |
| Signup flow: should signup be publicly accessible? | 1. Open signup 2. Invite-only 3. Admin-created accounts only | Affects launch model, user acquisition | Product-specific |
| Demo orgs: ship with pre-seeded data? | 1. Yes (Wanderlust, Precision, NovaCare) 2. Empty workspace 3. Optional | First-user experience | Option 1 per Product Declaration |
| Calendar surface: mount or defer? | 1. Mount as-is 2. Complete before mounting 3. Remove | UI completeness | Decision pending in gap register |
| MFA: required for launch? | 1. Yes 2. Post-launch | Security posture | Post-launch recommended |
| Integration push notifications (VAPID): required for launch? | 1. Yes 2. No | Notification capability for PWA | Low priority unless PWA engagement is critical |

---

## 11. FINAL REPOSITORY STATE

| Component | State |
|-----------|-------|
| Branch | feat/commandpalette-ai (unchanged) |
| HEAD | de9122fc105e4c342a0a34232ab8b99db3bc4a2d (unchanged since G1.10) |
| Upstream | NONE configured (`fatal: no upstream configured`) |
| Modified (unstaged) | 15 files — app/ai/routes.py, app/auth_routes.py, app/authz/workspace_context.py, app/communication/email_core.py, core/intelligence_runtime/conversation_bridge.py, frontend/src/api/ai-chat.ts, frontend/src/app.tsx, frontend/src/components/ai/command-palette.tsx, frontend/src/components/auth/auth-styles.ts, frontend/src/components/auth/login-page.tsx, frontend/src/components/auth/signup.tsx, frontend/src/components/home/home-page.tsx, frontend/vite.config.ts, scripts/debug_space_creation.py, tests/test_email_subsystem.py |
| Untracked | 12 entries — docs/launch/SHUNYA_COMPLETION_LEDGER.md, frontend/src/components/__tests__/command-palette-deterministic.test.ts, frontend/test-results/ (generated, excluded), frontend/tests/ (6 .cjs harness scripts, 3 path-corrected in G1.11), scripts/seed_demo_orgs.py, scripts/test_server.py, tests/test_debug_space_creation_safety.py, tests/test_test_server_safety.py (new G1.11) |
| Staged | None |
| Git operations | None performed in G1.10/G1.11 (no add/commit/push/fetch) |
| Production access | None |
| Credential operations | None |

---

## 12. NEXT EXECUTION MILESTONE

**Milestone: G1.12 — PUBLICATION-PREP EVIDENCE GAPS**

G1.3's journey objective is complete (22/22 browser-verified). The remaining work is evidence closure, not new feature breadth:

**Prerequisites / next actions:**
1. Owner decision on historical-secret remediation (rewrite + coordinated force-push + credential rotation) — blocks any public publication.
2. Remove the inline test credential (value redacted) from `scripts/validate_m2_postgres.sh` and re-run its validation against a disposable PostgreSQL instance.
3. Authenticated two-organization adversarial tenant-isolation test (user A denied org B reads/writes).
4. Browser-verified first-object journey: create → list → refresh → open → permission denial.
5. Full-suite pytest run and PostgreSQL migration parity on a disposable database.
6. Re-scan signup with axe to a clean result; screen-reader pass.

**What this unblocks:** A truthful launch-candidate assessment and a safe GitHub publication path.

---

## NEW ADDITIONS IN THIS DIRECTIVE

1. **SHUNYA_COMPLETION_LEDGER.md** — authoritative evidence-grounded completion ledger at `docs/launch/SHUNYA_COMPLETION_LEDGER.md`, consolidating Product Declaration, Truth Matrix, Gap Register, Launch Dashboard, architecture maps, constitution, and R28 evidence.

2. **Grouped execution model** — replacement for the serial R26→R27→R28 certification loop. Work organized into ranked workstreams with clear acceptance criteria, dependencies, and user impact assessment.

3. **R28 error-injection fix** — type-mismatch bug in test server's `_check_ai_hold` function resolved: JSON `request_id` is a number, but hold-queue keys are strings. Required `str()` conversion.

4. **Implementation priority shift** — from "prove existing code is correct" to "complete missing end-to-end journeys," beginning with the First User Journey milestone.

---

## 13. EVIDENCE LOG — G1.5 THROUGH G1.11 (isolated environment only)

*All results below were produced against disposable local stacks (SQLite test server on 127.0.0.1:51999/51998, Vite on 127.0.0.1:3000/3001). Production Gunicorn on :5001 was never contacted. No credentials outside synthetic test accounts were used.*

### 13.1 Runtime-verified evidence

| Evidence | Result | Environment | Verified in |
|---|---|---|---|
| Full first-user journey (signup → email verification → login/session → onboarding → workspace shell → CommandPalette → AI answer → session survives reload) | 22/22 assertions PASS, zero 5xx | HTTPS isolated stack (51998 + 3000), self-signed cert | G1.3 (2026-10-19) |
| Responsive subset checks (layout/overflow/interaction at two viewports) | 768×1024: 6/6 PASS; 375×667: 6/6 PASS; overflow 0 | Same isolated stack | G1.3 |
| CommandPalette deterministic unit tests | 12/12 PASS | vitest (jsdom) | G1.11 (re-run) |
| r19 isolated E2E (AI banner lifecycle, 3 viewports) | 16/16 PASS | HTTP isolated stack (51999 + 3001) | G1.11 (re-run after path fix) |
| r20 race/dismissal E2E | 9/9 PASS | HTTP isolated stack | G1.11 (re-run after path fix) |
| LB-03 CommandPalette browser certification | 19/19 PASS | HTTP isolated stack | G1.11 (re-run after path fix) |
| Duplicate-key regression harness | PASS (3 cycles, no duplicate-key warnings) | HTTP isolated stack | G1.11 |
| Email subsystem: Resend tag sanitization regression | 1/1 PASS | pytest, in-memory SQLite | G1.11 |
| Debug-script credential guard | 7/7 PASS (missing/empty DATABASE_URL refused before app import; URL never printed) | pytest, subprocess | G1.11 |
| Test-server safety guards (opt-in, inherited DATABASE_URL, unsafe path, unrelated-file preservation, stale-DB cleanup, routes confined to `__main__`) | 7/7 PASS | pytest, subprocess | G1.11 (new) |
| Demo seed: three orgs / 170 UOP objects (57/56/57), idempotent | First run 170 created, second run 0 new, exit 0 | Disposable SQLite /tmp/g16_seed_test.sqlite | G1.6 |
| Demo seed guard fails closed without opt-in | Exit 1, no DB created | Disposable path | G1.11 (re-run) |
| TypeScript strict check | 0 errors, exit 0 | frontend | G1.11 (re-run) |
| Production frontend build | Exit 0, built successfully; dist/ is gitignored | frontend | G1.11 (re-run) |
| axe-core scan | Homepage 0 violations; signup defects found, fixed and re-checked but not re-scanned to zero; full-app WCAG NOT claimed | Isolated stack | G1.3 |

### 13.2 Source-inspected / not runtime-proven

| Item | Finding | Status |
|---|---|---|
| Signup does not authenticate | `session["user_id"]` is not set at signup; CSRF middleware still emits a session cookie (Set-Cookie observed over HTTPS with Secure/HttpOnly/SameSite=Lax) | Observed HTTP behavior (G1.3), not a formal authz test |
| Email verification establishes session | Verify-email flow produced an authenticated session on `/api/v1/auth/session` over HTTPS | Observed (G1.3) |
| Tenant isolation | A valid two-organization authenticated adversarial test (user A cannot read org B) remains incomplete | NOT FULLY VERIFIED — do not claim isolation proven |
| First-object UI persistence journey | UOP creation route exists and is permission-gated (`rel.create`); browser-verified create → list → refresh → open → permission-denial journey is not complete | NOT VERIFIED END-TO-END |
| Organization permission semantics | AUTHZ-01 (admin lacks org.view) awaiting founder decision | NEEDS PRODUCT DECISION |
| PostgreSQL migration parity | All testing so far on SQLite; no disposable PostgreSQL parity run | NOT VERIFIED |
| Email inbox delivery | Provider acceptance (`email_status=accepted`) only; no inbox receipt verified | NOT VERIFIED |
| WCAG compliance | Partial axe coverage only; no full WCAG audit or screen-reader pass | NOT CLAIMED |

### 13.3 Open security exposures (no values reproduced)

| Exposure | Location | State |
|---|---|---|
| Hardcoded PostgreSQL URL (user/host/port/db; empty password) | Commits `af3392b` and duplicate `afb7cdc`; ancestor of `origin/master` (826 commits deep) | OPEN — published history; rewrite + rotation unauthorized |
| Connection URLs (user-only shape) in certification logs | `artifacts/r6b25/*.log`, `artifacts/r6b27/*.log`; tracked in HEAD and `origin/master` despite ignore rules | OPEN — removal commit `13d33d4` only on unmerged `fix/security-remediate-exposed-artifacts` |
| Inline test credential (value redacted) | `scripts/validate_m2_postgres.sh`, tracked, unchanged from HEAD | OPEN — low severity test credential; must be removed before publication |
| Certification-account credential handling incident | Prior local certification runs; credential material treated as exposed to local artifacts/logs | OPEN — rotation requires owner authorization |
| `.env` provider key | Untracked, gitignored, mode 0600, never printed | NOT in Git; rotation status unverified |

### 13.4 G1.11 corrections recorded

1. `scripts/test_server.py` — explicit opt-in (`SHUNYA_TEST_SERVER_ALLOWED=true`), validated disposable `TEST_DB_PATH` (absolute, `/tmp/`, `shunya_test_server*.sqlite`, no symlink, regular file), refusal of inherited `DATABASE_URL`, recorded removal of only the validated path plus its `-wal`/`-shm` companions.
2. `tests/test_test_server_safety.py` — new subprocess-based guard tests (7).
3. `frontend/tests/lb03-commandpalette.cjs`, `r19-e2e.cjs` — artifact directory now `TEST_ARTIFACT_DIR` or OS temp dir.
4. `frontend/tests/r20-e2e.cjs` — Playwright resolved relative to `__dirname` instead of a machine-specific absolute path.
5. This ledger — G1.5–G1.11 evidence, corrected SEC/A11Y/UX statuses, explicit not-verified list, current repository state.

### 13.5 Gates (unchanged)

```
PUBLIC_LAUNCH_READY     = FALSE
STAGING_AUTHORIZED      = NONE
COMMIT_AUTHORIZED       = NONE
PUSH_AUTHORIZED         = NONE
HISTORY_REWRITE_AUTHORIZED = NONE
CREDENTIAL_ROTATION_AUTHORIZED = NONE
PRODUCTION_MUTATION_AUTHORIZED = NONE
```

---

## 14. G1.13 — ORGANIZATION LIFECYCLE, POSTGRESQL PARITY & CTA CORRECTION

### 14.1 PostgreSQL migration parity — VERIFIED (disposable cluster)

- Cluster: PG 16.15 at `127.0.0.1:55432`, data dir `/tmp/g112_pg.Q5cST0`; database `shunya_migration_fresh` (created for a clean full-chain run).
- Command: `DATABASE_URL=postgresql://shunya_test@127.0.0.1:55432/shunya_migration_fresh alembic upgrade head` → **exit 0**, head `r6b2_conversation_fk`, 176 tables.
- Four genuine PG-only defects found and fixed in the chain (SQLite had hidden each):
  1. `0001_initial_schema.py` never created `org_members`, so `0010` FK creation failed `UndefinedTable`. Added the base table + indexes.
  2. `0009_org_scoped_workspaces.py` ran unconditional backfill UPDATEs against tables a fresh chain does not create. Guarded by `has_table`.
  3. `r6b27_supplier_drift.py` created `ix_suppliers_tenant(tenant_id,status)` without ever adding `tenant_id`. Added the guarded column.
  4. `0015_remediation_columns.py` dropped a constraint-backed index first (`DependentObjectsStillExist`). Now drops the constraint first; `r6b2_conversation_fk.py` ensures a UNIQUE constraint on `sh_objects.object_id` before the FK (`InvalidForeignKey`).
- Residual: `sh_uop_objects` and `alert_events` are materialised by the boot path (`db.create_all`), not by the chain — schema parity for those two remains boot-dependent, not migration-certified.

### 14.2 Organization lifecycle — IMPLEMENTED & RUNTIME-VERIFIED (no fixture bypass)

- **DEF-02 fixed**: `/orgs` is registered as personal-scope capable (bootstrap only; the route authenticates and assigns ownership itself). A verified org-less user can now create their first organization (HTTP 201).
- **DEF-03 fixed**: invitation acceptance creates/resolves the canonical `sid_*` identity and writes it to `OrgMember.identity_id`; login also repairs legacy numeric membership ids for the same email. Invited user C logs in and reads A's org object with no fixture manipulation.
- **DEF-04 fixed**: `/api/v1/orgs/<id>/users` resolves `Organization` (canonical), not `Tenant`.
- **Role seeding fixed**: org creation now seeds default roles; previously the owner had no permission grants and every permission-gated route returned 403.
- Evidence: `g113_tenant_org.py` (HTTP, isolated 51999) → **26/26 PASS**, covering bootstrap, two independent orgs, own-list isolation, cross-read/archive 404s, no data leakage, query/header/body tenant overrides ignored, unauthenticated 401s, invitation accept + login + authorized read, cross-tenant denial for the invitee.

### 14.3 First-object CTA — CORRECTED & BROWSER-VERIFIED

- `home-page.tsx` now fetches `/api/v1/uop/objects`; CTA shows only when the fetch succeeded and the count is 0. Loading/failure → CTA hidden (unknown ≠ empty). Task counts no longer drive it.
- Journey (`g113-first-object.cjs`, HTTP isolated stack): **13/13 PASS** — CTA on empty workspace → supported import workflow → invalid input shows "Import Failed / Rejected: 1" (no false success) → valid import "Created: 1" → Relationships list → detail panel → full reload persistence → **CTA hidden on populated workspace**.
- Known product behaviour recorded: malformed email in an import is a warning (row still imports), not a rejection; missing required field is a rejection. Warn-vs-reject for email is a product decision, not changed here.

### 14.4 Validation & accessibility

- `pytest tests/test_test_server_safety.py tests/test_debug_space_creation_safety.py tests/test_email_subsystem.py::…` → **18 passed** (10 + 7 + 1).
- `tsc -b --noEmit` → 0; `npm run build` → exit 0 (chunk-size warning only).
- axe-core: homepage, signup, login, import panel, relationships → **0 violations** after fixing import-tab and `.pw-commercial-tag` contrast.
- Responsive 3-viewport re-run of the corrected journey: NOT executed in G1.13 (desktop 1280×800 verified); tablet/mobile remain from G1.3 evidence.

### 14.5 Email

- Startup still logs a provider key rejection (HTTP 401) on some boots; a later signup reported `email_status: accepted`. Provider acceptance is inconsistent; **inbox delivery remains unverified**. No credentials changed. Owner action: verify/rotate the Resend key outside this directive.

### 14.6 Gates

```
PUBLIC_LAUNCH_READY = FALSE
STAGING_AUTHORIZED = NONE
COMMIT_AUTHORIZED = NONE
PUSH_AUTHORIZED = NONE
HISTORY_REWRITE_AUTHORIZED = NONE
CREDENTIAL_ROTATION_AUTHORIZED = NONE
PRODUCTION_MUTATION_AUTHORIZED = NONE
```

---

## 15. G1.14 — DURABLE REGRESSION, RUNTIME PARITY & THREE-VIEWPORT CERTIFICATION

### 15.1 Durable regression tests added (repository, not scratch)

- `tests/test_org_lifecycle.py` — 8 tests (7 pass + 1 parametrized family), exercising the real Flask app, sessions and authorization:
  bootstrap of a first organization (DEF-02), two users with separate org contexts and isolated objects, cross-tenant read/archive denials with no payload leakage, tenant overrides via query/header/body, missing object + unauthenticated denials, invitation acceptance writing the canonical `sid_*` identity and login resolution (DEF-03), org-scoped user administration resolving `Organization` (DEF-04).
  Email side effects suppressed via `monkeypatch` on `send_email` only — authorization is never mocked.
- `frontend/src/components/home/__tests__/home-page-first-object-cta.test.tsx` — 6 vitest tests: CTA on empty (successful fetch), absent when objects exist with zero tasks, absent on fetch failure (unknown ≠ empty), absent while pending, absent after import+reload, refetch on remount (org switch). These pin the G1.13 CTA defect directly.
- Also fixed in support of runtime parity: `app/__init__.py` now registers `AlertEvent` before `db.create_all()` (it was imported after, so `sh_alert_events` never existed on a boot-only database).

### 15.2 PostgreSQL runtime parity — VERIFIED on disposable cluster

- New disposable DB `shunya_runtime_test2` on the verified 127.0.0.1:55432 cluster (existing `shunya_migration_test` / `shunya_migration_fresh` preserved untouched).
- Boot probe (real `create_app` against PostgreSQL): **7/7 PASS** — `sh_uop_objects` and `sh_alert_events` exist after bootstrap; columns match model metadata (0 missing) for both; a real UOP object persists and is tenant-scoped; it is invisible under a foreign tenant filter; an `AlertEvent` persists and is queryable.
- Schema authority recorded: `sh_uop_objects` and `sh_alert_events` are boot-materialised (`db.create_all`), not Alembic-created; the chain still does not create them. Architectural decision remains open: move creation into a migration or keep boot materialisation as documented policy.
- Earlier chain fix remains: `alembic upgrade head` → exit 0 at `r6b2_conversation_fk`, 176 tables (G1.13, four PG-only defects fixed).

### 15.3 First-object journey — THREE VIEWPORTS, all PASS

Each run provisions a fresh synthetic account with its own organization (no fixture repair), then executes: login → empty CTA → supported import panel → invalid input (honest failure) → valid customer import ("Created: 1") → Relationships list → detail → reload persistence → CTA hidden on populated workspace → no 5xx.

| Viewport | Result |
|---|---|
| 1280×800 | 14/14 PASS |
| 768×1024 | 14/14 PASS |
| 375×667 | 14/14 PASS |

Keyboard: login/import controls are native inputs/buttons; the journey drives activation and focus. A dedicated focus-visible trace across the whole flow is still outstanding (see 15.4).

### 15.4 Validation baseline

| Check | Scope | Result |
|---|---|---|
| pytest | `test_org_lifecycle.py`, `test_test_server_safety.py`, `test_debug_space_creation_safety.py`, `test_cookie_auth.py`, `test_email_subsystem.py` | **50 passed, 12 skipped**, exit 0 |
| vitest | CTA contract (6) + CommandPalette deterministic (12) | **18/18 passed**, exit 0 |
| tsc | `tsc -b --noEmit` | 0 errors |
| build | `npm run build` | exit 0 (chunk-size warning) |
| axe-core | homepage, signup, login, import panel, relationships | **0 violations** each |
| full Python suite (175 files) | **NOT run** in G1.14 (budget); not claimed green |
| keyboard focus-visible trace | partial (native activation exercised) | NOT comprehensively verified |

### 15.5 Product inconsistencies recorded (not changed)

- Org-scoped user creation (`/api/v1/orgs/<id>/users`) accepts only the legacy role vocabulary (`admin|agent|manager`) and rejects canonical `member|viewer|owner` — DEF-05, recorded.
- Malformed email in imports is a warning (row imports); missing required fields reject. Warn-vs-reject is an open product decision.
- Org bootstrap is now enabled as self-service; whether that is the intended policy remains a founder decision.

### 15.6 Email

- Isolated server runs show `Email accepted by Resend: id=…` for verification and invitation messages (provider API acceptance with message IDs). One earlier startup logged the integration registry rejecting the key (HTTP 401); that check and the send path read configuration differently.
- **Inbox delivery is NOT verified.** Provider acceptance ≠ delivery. Key not read, printed, rotated, or replaced; owner action pending.

### 15.7 Process closure — VERIFIED

Stopped by re-verified identity: test server :51999 (pid 100530, `scripts/test_server.py`), Vite HTTP :3001 (pid 92177), scratch proxy :3002 (pid 93076). PostgreSQL stopped via `pg_ctl -D /tmp/g112_pg.Q5cST0 stop -m fast` → "server stopped"; `pg_isready` exit 2. Post-stop listeners: only pre-existing Vite HTTPS :3000 (58419) and production Gunicorn :5001 remain, untouched. Disposable databases preserved (not deleted).

### 15.8 Gates (unchanged)

```
PUBLIC_LAUNCH_READY = FALSE
STAGING_AUTHORIZED = NONE
COMMIT_AUTHORIZED = NONE
PUSH_AUTHORIZED = NONE
HISTORY_REWRITE_AUTHORIZED = NONE
CREDENTIAL_ROTATION_AUTHORIZED = NONE
PRODUCTION_MUTATION_AUTHORIZED = NONE
```

---

## 16. G1.15 — TECHNICAL CLOSURE: SCHEMA AUTHORITY, ROLES, KEYBOARD, EMAIL

### 16.1 Permanent engineering rule recorded

`docs/governance/SHUNYA_EXECUTION_INTEGRITY_CONSTITUTION.md` — new **Rule 9 — PRODUCT BEHAVIOUR OVER GREEN CHECKLISTS** (inserted before Enforcement). Extends existing Rule 1 (GREEN IS NOT COMPLETE); no competing constitution created.

### 16.2 Schema authority — RESOLVED (migration-owned)

- New forward-only, guarded revision `migrations/versions/r6b30_boot_tables.py` (down_revision `r6b2_conversation_fk`) creates `sh_uop_objects` and `sh_alert_events` with model-matching columns, indexes and constraints. Additive only; downgrade intentionally a no-op.
- Verified on a NEW disposable database `shunya_migration_closure`: `alembic upgrade head` → exit 0, head `r6b30_boot_tables`; both tables present **after migration and before any boot**.
- Application boot against the migrated database: 7/7 PASS — schema present with zero missing columns, UOP object persists and is tenant-scoped, foreign-tenant filter finds nothing, AlertEvent persists.
- Boot import order remains correct (`AlertEvent` registered before `create_all`), so boot materialisation is now a no-op on migrated databases rather than a hidden substitute.
- Existing databases `shunya_migration_test`, `shunya_migration_fresh`, `shunya_runtime_test2` preserved untouched.

### 16.3 DEF-05 role vocabulary — IMPLEMENTED, AUTHZ-01 still open

- `app/authz/services.py`: `normalize_role()` defines the canonical set (`owner, admin, manager, member, viewer`) and a deterministic legacy mapping for `TeamMember.role` (`owner/admin→admin`, `manager→manager`, `member/viewer→agent`), accepting legacy `agent` as an alias for `member`. Unknown labels raise → HTTP 400. Permissions still come only from the seeded canonical role; no label grants access.
- Applied in `app/production/identity/user_routes.py` (TeamMember gets legacy role, OrgMember gets canonical role) and in `app/production/identity/invitation_routes.py` (same split; grants use canonical name).
- **Security defect found and fixed**: user-administration routes had only `@login_required` and resolved the org by id, so any authenticated user could read or create users in any organization. `_get_org_or_404` now requires an active membership in the target organization (403 otherwise).
- Regression: `tests/test_role_normalization.py` (7 mapping cases, unknown label, member/agent/viewer permission boundaries, cross-tenant denial) — passing.
- AUTHZ-01 (admin `org.view`) explicitly **not** changed.

### 16.4 Email configuration truth — ROOT CAUSE FIXED

- Root cause: the integration registry probed `GET https://api.resend.com/keys` (account-administration endpoint) with the sending key, producing a false HTTP 401, while the send path (`POST /emails`) accepted messages.
- Fix: `app/integration/providers/email_integration.py` no longer probes `/keys`; configuration presence is the honest signal ("acceptance verified on send"). Sending path unchanged.
- Tests: `tests/test_email_config.py` (configured without network probe, no-provider honesty, connect status, acceptance ≠ delivery states) — passing.
- Delivery level: **provider-accepted only** (message IDs in isolated logs). Inbox delivery remains NOT VERIFIED; no real recipients contacted.

### 16.5 Keyboard/focus accessibility — PARTIALLY VERIFIED

- Durable harness `frontend/tests/keyboard-first-object.cjs` (repo) drives real keyboard input at three viewports.
- Fixes: import panel now moves focus into itself on open (`tabIndex=-1` + focus effect); import errors expose `role="alert"`; import result heading is `role="status" aria-live="polite"`; relationship records are keyboard-operable (`role="button"`, `tabIndex=0`, Enter/Space, `aria-expanded`).
- Result per viewport (1280×800 / 768×1024 / 375×667): **11/15 PASS each**. Passing: keyboard-only login, CTA reachable via Tab with visible focus, panel opens via Enter, Paste CSV and textarea reachable, preview via Enter, invalid import announced via alert/status and never claims success. Failing at all three sizes: completing a *valid* import through keyboard-only recovery after the failure, and the relationship steps that depend on that record existing (item reach, detail, persistence). **Open defect KB-01** — keyboard recovery path after a rejected import does not complete; needs focused investigation (state/focus reset, not confirmed a data defect).
- axe-core on homepage, signup, login, import panel, relationships: **0 violations each** (automated only; no WCAG conformance claim).

### 16.6 Full Python suite — COMPLETE (exit 1): 5763 passed, 3 failed, 125 skipped, 45 errors

- Command: `DATABASE_URL=sqlite:///:memory: pytest -q` (full repository suite). Duration **51:24**; exit **1**.
- Totals: **5763 passed, 3 failed, 125 skipped, 45 errors, 28,090 warnings**.
- Classification (verified by rerun, not assumed):
  - **45 errors + 2 of 3 failures = environment/configuration**, not product defects. The failing/erroring files build their own app via `create_app()` without `config_override`, so they hit the production `SECRET_KEY > 20 chars` guard. Rerun with `SECRET_KEY=… FLASK_ENV=testing SHUNYA_ENV=test` made `test_r6b27_db_isolation_guard::test_certification_flag_allows_isolated_db` and `test_fda3_canonical_memory::test_dbmemory_repository_wired_inside_app_context` pass. The 45 errors cluster in `tests/test_fcr02_integration.py`, `tests/convergence/test_learning_loop_orphans.py`, `tests/convergence/test_identity_convergence.py`, and `tests/convergence/test_durable_memory_bridge.py` — all module-scoped `create_app()` fixtures with the same missing SECRET_KEY.
  - **1 genuine failure — AI-ISO-01**: `tests/test_ai_chat_isolation.py::test_missing_workspace_fails_closed` expects HTTP 400 and receives **503**. Reconfirmed under the corrected environment. Root cause not yet traced; recorded as an open product-behaviour defect (missing-workspace chat request is reported as service-unavailable rather than a client-side fail-closed error).
- No test was modified, skipped, weakened, or re-expected to obtain this result.
- Targeted suites (run separately, exit 0): `test_org_lifecycle.py`, `test_role_normalization.py`, `test_email_config.py`, `test_test_server_safety.py`, `test_debug_space_creation_safety.py`, `test_cookie_auth.py`, `test_email_subsystem.py` → **74 passed, 12 skipped**.
- Frontend: `tsc -b --noEmit` → 0 errors; `npm run build` → exit 0 (re-run after the G1.15 UI edits).

### 16.7 First-object journey — historical G1.14 evidence retained

G1.14 three-viewport results (14/14 each) remain valid for the code at that time. G1.15 changed the import panel (focus), relationship items (keyboard) and backend roles/email; the full journey was **not** re-run this directive. The keyboard harness re-exercised login, CTA, panel, invalid path at all three viewports (11/15 each), but a full three-viewport re-certification of the complete journey is outstanding.

### 16.8 Security incidents — unchanged, separate

Historical DB URL (`af3392b`/`afb7cdc`), certification-log connection URLs, inline test credential in `scripts/validate_m2_postgres.sh`, certification-account handling incident, untracked 0600 `.env`. No values printed; no history rewrite, rotation, staging, commit, push, or production mutation. Owner actions unchanged.

### 16.9 Process closure — verified

Stopped by re-verified identity: test server :51999 (pid 109370), Vite :3001 (pid 109389), scratch proxy :3002 (pid 109429). PostgreSQL stopped via `pg_ctl -D /tmp/g112_pg.Q5cST0 stop -m fast` → stopped; `pg_isready` exit 2. Post-stop listeners: only pre-existing Vite HTTPS :3000 (58419) and production Gunicorn :5001 remain. Databases preserved.

### 16.10 Open items after G1.15

1. **KB-01** keyboard recovery after rejected import (blocks keyboard closure).
2. AI-ISO-01 root-cause triage (`test_missing_workspace_fails_closed` expects 400, gets 503); full suite otherwise complete: 5763 passed, 45 env-config errors, 2 env-config failures.
3. Full three-viewport journey re-run on the post-G1.15 tree; tsc/build re-run after final UI edits.
4. AUTHZ-01 decision (admin `org.view`); org bootstrap policy; malformed-email warn vs reject.
5. Historical secret remediation + credential rotation (owner authorization).
6. Resend key verification and actual inbox-delivery evidence (owner-approved test account).

---

## 17. G1.16 — DEFECT CLOSURE: TEST ENV, AI-ISO-01, KB-01

### 17.1 Test-environment configuration — FIXED (canonical conftest)

- Root cause of the 45 setup errors and 2 environment failures: module-scoped fixtures call `create_app()` without `config_override`, so the production `SECRET_KEY > 20 chars` guard rejected the app. The suite had no canonical environment.
- Fix: `tests/conftest.py` now sets, via `setdefault` (never overriding a stronger explicit value): `FLASK_ENV=testing`, `SHUNYA_ENV=test`, `SECRET_KEY=test-secret-key-long-enough-for-guard`, `DISABLE_RATE_LIMIT=true`. Production checks were not weakened or removed; tests declare their environment.
- Verified: the four affected modules (`test_fcr02_integration.py`, `convergence/test_learning_loop_orphans.py`, `convergence/test_identity_convergence.py`, `convergence/test_durable_memory_bridge.py`) plus the two environment-dependent failures and the AI-ISO test → **48 passed, exit 0**. Errors disappeared for the correct reason.
- Full-suite rerun after this change: **NOT executed in G1.16** (budget); G1.15’s full run remains the last complete count (5763 passed / 3 failed / 125 skipped / 45 errors), now superseded for the affected modules only.

### 17.2 AI-ISO-01 — CLOSED (root cause fixed + regression expanded)

- Root cause: an explicitly requested, non-existent `workspace_id` was silently ignored and the handler fell back to an unrelated personal workspace. Persistence then hit `OwnershipContextError`, which the generic handler surfaced as **HTTP 503 “persistence failed”** — an authorization/context contradiction misrepresented as a service outage, after which inference could run.
- Fix in `app/ai/routes.py`: (a) non-string `workspace_id` rejected with 400 before any query; (b) an explicit workspace id that is neither in the caller’s organization nor the caller’s own personal workspace/membership now fails closed with **400 “Workspace not found or not accessible”** before personal fallback and before any AI call.
- Regression: existing missing-workspace test passes; new `test_malformed_workspace_identifier_fails_closed` and `test_foreign_workspace_request_fails_closed` assert 400 and `calls == []` (no inference). `tests/test_ai_chat_isolation.py` → **11 passed**, exit 0.

### 17.3 KB-01 — PARTIALLY FIXED, STILL OPEN

- Fixes landed: import panel moves focus into itself on open and again whenever the flow returns to the input step; `resetFlow` clears the stale CSV text (previously a corrected keyboard entry appended to the rejected text); errors are `role="alert"`, results `role="status" aria-live="polite"`; relationship records are keyboard-operable.
- Current keyboard result, all three viewports: **11/15**. Now passing: keyboard-only login, CTA via Tab with visible focus, panel via Enter, Paste CSV, textarea, Preview, invalid import announced, no false success. Remaining failure: the valid import after a rejected one still returns “Import Failed” under keyboard-only input (target selection via native select is the prime suspect; not yet confirmed), so the dependent relationship steps and reload persistence fail.
- **KB-01 remains open.** No claim of keyboard closure or accessibility conformance.

### 17.4 Current-tree journey — 3 viewports PASS (before the final csvText change)

`g113-first-object.cjs` against the G1.16 tree: **14/14 at 1280×800, 14/14 at 768×1024, 14/14 at 375×667** (fresh synthetic account/org per run, no fixture repair, no 5xx). One subsequent single-line UI change (`resetFlow` clears `csvText`) was made after this run; the journey fills the textarea on a fresh form, so behaviour is unaffected, but a post-change journey rerun is outstanding for strictness.

### 17.5 Validation run in G1.16

- `tsc -b --noEmit` → 0 errors; `npm run build` → exit 0 (after AI/UI edits, before the csvText line).
- axe: not rerun after the last UI edits in G1.16 (G1.15: 0 violations on five surfaces).
- Focused backend: AI isolation 11 passed; org/role/email/safety suites were green in G1.15 and not re-run after the AI-only changes.

### 17.6 Repository state and cleanup

- Final: branch `feat/commandpalette-ai`, HEAD `de9122fc105e4c342a0a34232ab8b99db3bc4a2d`, **34 modified / 0 staged / 19 untracked**. No staging, commit, push, fetch, history rewrite, credential change or production mutation.
- Cleanup verified by identity: test server :51999 (pid 114356), Vite :3001 (pid 114471), proxy :3002 (pid 114513) stopped; post-stop listeners only pre-existing Vite HTTPS :3000 (58419) and production Gunicorn :5001. No PostgreSQL was started in G1.16; the G1.15 cluster remains stopped with databases preserved.

### 17.7 Files changed in G1.16

`tests/conftest.py` (canonical test env); `app/ai/routes.py` (workspace fail-closed + type validation); `tests/test_ai_chat_isolation.py` (2 new tests); `frontend/src/components/import-export/import-export-panel.tsx` (focus on step reset, csvText reset, alert/status roles); `frontend/tests/keyboard-first-object.cjs` (target selection + focus fallback); `docs/launch/SHUNYA_COMPLETION_LEDGER.md`.

### 17.8 Open blockers after G1.16

1. KB-01 keyboard valid-import recovery (product or harness; must be confirmed).
2. Full-suite rerun on the corrected test environment.
3. Post-change three-viewport journey + axe rerun (strict final-tree certification).
4. AUTHZ-01, org-bootstrap policy, email warn-vs-reject decisions.

---

## 18. G1.17 — KB-01 ROOT CAUSE, FULL-SUITE CERTIFICATION, FINAL-TREE VERIFICATION

**Authority:** G1.17 directive (bounded defect closure). No staging, commit, push, merge, rebase, history rewrite, credential change, production mutation or deployment. Branch, HEAD and all pre-existing uncommitted work preserved exactly.

### 18.1 Repository state

| | Branch | HEAD | Modified | Staged | Untracked |
|---|---|---|---|---|---|
| Entry | `feat/commandpalette-ai` | `de9122fc105e4c342a0a34232ab8b99db3bc4a2d` | 34 | 0 | 19 |
| Exit | `feat/commandpalette-ai` | `de9122fc105e4c342a0a34232ab8b99db3bc4a2d` | 35 | 0 | 20 |

The 34 modified files present at entry are untouched by G1.17. The +1 modified / +1 untracked are G1.17's test work (below). No application source or schema file was changed by this directive.

Pre-existing services (untouched, still listening at exit): Vite HTTPS `:3000` (pid 58419, started 2026-10-19), production Gunicorn `:5001` (pids 146260–146263, started 2026-10-21 06:21), PostgreSQL `:5432`.

### 18.2 KB-01 root cause — TEST-HARNESS DEFECT (proven, not assumed)

Reproduced on an isolated local stack (fresh SQLite, fresh synthetic account + organization): **11/15 assertions at 1280×800**, identical failure shape to G1.15/G1.16 — the valid import after a rejected one returned "Import Failed".

Instrumented evidence (sanitized, no payload or personal data):

| Observation | Value |
|---|---|
| Commit payload `target_type`, attempt 1 | `customer` (expected) |
| Commit payload `target_type`, attempt 2 (recovery) | **`campaign` (unexpected)** |
| Commit response 1 | HTTP 400, outcome `rejected`, created 0, rejected 3 |
| Commit response 2 | HTTP 400, outcome `rejected`, created 0, rejected 1 |
| Backend error | customer CSV submitted to the campaign target: required field `name` missing |

Cause: the harness selected the target by pressing `c` on the native select. After the flow reset the select still held **Customers** (correct product behaviour — the choice is sticky), so the second `c` cycled the already-selected option to **Campaigns**. The harness never asserted the selected value, so the product truthfully rejected a customer CSV submitted as a campaign import.

Classification: **test-harness defect**. The product's select binding, focus management, reset, validation and failure messaging were correct throughout (the invalid import was announced via `role="alert"`/`role="status"` and never claimed success).

Two further harness defects were proven in the same run:

1. **Contaminated invalid input** — the paste box opens pre-filled with sample rows, so typing the "malformed CSV" appended to the sample (observed textarea: `email\nonly-an-email@example.com\ncustomer_name,phone,email\nSample,…`). The invalid case was never the intended input.
2. **Unreachable relationship surface** — the harness fell back to `page.goto('/workspace/relationships')` and the relationship workspace calls `/relationships/api/v1/relationships`, which the dev proxy (only `/api` forwarded) answered with the SPA HTML (`200`, HTML body). Production nginx proxies every path to Gunicorn, so this is a harness/environment defect, not a product defect.

### 18.3 Fix and regression coverage

- `frontend/tests/keyboard-first-object.cjs` — rewritten:
  - deterministic keyboard target selection (`Home` + `ArrowDown` until the expected value, asserted **before every submission**);
  - textarea cleared with `Ctrl+A`/`Backspace` before typing, and the typed content asserted;
  - same-origin serving documented and made the default (`FRONTEND_URL` default = `BACKEND_URL`), because the relationship API is not under `/api`;
  - relationships reached through the in-app **Open Relationships** control (keyboard), not URL navigation; record identified by name, detail content asserted;
  - persistence verified through the product API from the browser session, then again after reload;
  - 5xx assertion scoped to the app origin (external font hosts are recorded separately — no egress in this environment);
  - per-assertion groups: `keyboard` (21), `journey` (12), `setup` (1).
- `tests/test_kb01_import_recovery.py` — new, 6 tests: invalid preview reports invalid rows; rejected commit writes nothing; invalid→valid commit creates exactly one canonical customer; relationship list returns it; timeline + AI memory readable; record survives subsequent requests.
- Fail-before / pass-after evidence: the pre-fix harness run was **11/15** (baseline log) and the new assertion *"Target select still holds Customers before valid submission"* fails on the old path (`value=campaign`) and passes on the fixed path. The new pytest tests pin the product chain and pass on both trees — stated explicitly: the product was already correct, so they are regression pins for the product, while the harness assertions are the fail-first coverage for KB-01.
- **KB-01 = CLOSED** (keyboard recovery, persistence, relationship list, detail, reload all verified at three viewports; see 18.6).

### 18.4 Canonical test configuration review (`tests/conftest.py`)

| Requirement | Finding | Evidence |
|---|---|---|
| Defaults available before app creation | Yes — module-level `setdefault` runs at conftest import, before any fixture calls `create_app()` | CODE-INSPECTED (lines 54–62) |
| Explicit caller configuration respected | Yes — `setdefault` never overwrites; fixture passes its own `config_override` | CODE-INSPECTED |
| Tests cannot reach a production database | Yes — missing `DATABASE_URL` and a production-like URL both refuse at conftest import | RUNTIME-PROVEN: `postgresql://…localhost:5432/shunya_os` → `RuntimeError: refusing to use a production-like database`; empty → `RuntimeError: DATABASE_URL is not set` (password masked by the guard) |
| Production configuration guards not weakened | Yes — the SECRET_KEY guard is driven by `SHUNYA_ENVIRONMENT`/`FLASK_ENV`; the production unit sets `FLASK_ENV=production`, tests set `testing` only in the test process | CODE-INSPECTED (`app/__init__.py:531–555`, `shunya.service`) |
| Isolation / cleanup / concurrency | `app` fixture is function-scoped `sqlite:///:memory:` with `drop_all`; the isolated test server uses a validated `/tmp` SQLite path plus an exclusive `flock` per path | CODE-INSPECTED |

Note: `SHUNYA_ENV=test` (conftest line 55) is inert — the application reads `SHUNYA_ENVIRONMENT`, not `SHUNYA_ENV`. `FLASK_ENV=testing` is what exempts test apps; the extra variable is harmless but misleading. Not changed in G1.17.

### 18.5 Full Python suite

Command (canonical, identical both runs): `DATABASE_URL=sqlite:///:memory: .venv/bin/python -m pytest -q`

| Run | Totals | Exit | Duration |
|---|---|---|---|
| 1 — after KB-01 work, before test repair | 5834 passed, **1 failed**, 125 skipped, 0 errors | 1 | 1985.02 s |
| 2 — final tree | **5835 passed, 0 failed, 125 skipped, 0 errors** | **0** | 2449.94 s (40:49) |

Run 1 failure: `tests/test_integration_d8.py::TestEmailIntegrationVerification::test_resend_probe_rejected_is_error`. Classification: **test defect — asserting a superseded implementation.** The test required `connect()` to probe `GET /keys` and report 401; G1.16 removed that probe because `/keys` is an account-administration endpoint that rejects ordinary sending keys (false 401 while `POST /emails` accepts mail). The product was corrected with evidence; the test asserted the removed behaviour.

Repair: the two Resend probe tests were replaced (not deleted) by two tests pinning the corrected contract — `connect()`/`sync()` must report configured→connected/synced **without** any `GET` probe and **without** performing a send to verify; a genuinely rejected credential surfaces at send time (acceptance vocabulary pinned in `tests/test_email_config.py`). No assertion was loosened, no skip added, no expected status widened.

Affected-module rerun after the repair: `test_integration_d8.py`, `test_email_config.py`, `test_kb01_import_recovery.py` → **18 passed**; then the full suite (run 2 above) → **5835 passed, exit 0**.

History: G1.15 recorded 5763 passed / 3 failed / 125 skipped / 45 errors. The 45 setup errors and 3 failures are now green; 6 KB-01 tests were added; the two replaced email tests net to zero. The remaining +18 passes are consistent with module-scoped fixtures that previously collapsed whole modules into a single setup error (inferred, not separately reconciled).

### 18.6 Keyboard-only and first-object journey — three viewports

Harness: `frontend/tests/keyboard-first-object.cjs`, isolated stack, fresh synthetic account + organization per run, `SHUNYA_FRONTEND_DIST=<checkout>/frontend/dist` (production release symlink untouched), no fixture repair, no mouse input.

| Viewport | Keyboard | Journey | Setup | Total |
|---|---|---|---|---|
| 1280×800 | 21/21 | 12/12 | 1/1 | **34/34** |
| 768×1024 | 21/21 | 12/12 | 1/1 | **34/34** |
| 375×667 | 21/21 | 12/12 | 1/1 | **34/34** |

Journey assertions exercised per viewport: CTA backed by a successful empty object list; keyboard panel open; malformed CSV rejected and announced without false success; keyboard recovery; valid import completed; record persisted (product API); relationship panel listed it; record reachable by Tab and identified by name; detail opened by keyboard with timeline/memory; persistence after reload; record reachable after reload; no app-origin 5xx; no horizontal overflow.

**Step 11 of the required journey — FAIL (KB-02, new):** the empty-state CTA does **not** disappear after a successful import in a fresh session — evidence: post-import `GET /api/v1/uop/objects` → `200 {"count":0}` while `GET /relationships/api/v1/relationships` → 1 record and the homepage renders "Create your first business object". The CTA is gated on `UOPObject` rows; the import path writes `CanonicalRelationship` and never a universal object. This is a truthful false empty state, not a harness artefact.

KB-02 requires an owner decision — either the home empty state reads persisted domain records, or the import also creates a canonical universal object (dual-write ≠ convergence). G1.17 does **not** choose between them and does not patch application behaviour.

### 18.7 Frontend validation

| Check | Result | Evidence |
|---|---|---|
| `npx tsc -b --noEmit` | exit 0, 0 errors | final tree |
| `npm run build` | exit 0, `✓ built in 1.63s`, bundle `assets/index-Bffz0e-C.js` (identical hash to the bundle used in the browser runs) | final tree |
| `npm run test:run` (vitest) | 12 files, **94 passed**, exit 0 | final tree |
| axe-core (WCAG 2.0/2.1 A+AA tags), homepage / signup / login / import panel / relationships | **0 violations on each surface** | automated scan only — **no WCAG conformance claim** |

Environment limitation: Google Fonts hosts are unreachable from this host (`503`); the app renders with fallback fonts. Recorded, not attributed to the product.

### 18.8 Files changed by G1.17

| File | Change |
|---|---|
| `frontend/tests/keyboard-first-object.cjs` | KB-01 harness fix (deterministic target selection, input hygiene, same-origin serving, in-app relationship navigation, persistence assertions) |
| `tests/test_kb01_import_recovery.py` | New — 6 durable regression tests for rejected→valid import, persistence, list, detail |
| `tests/test_integration_d8.py` | Two stale Resend `/keys` probe tests replaced with corrected-contract tests (no probe, no send-to-verify) |
| `docs/launch/SHUNYA_COMPLETION_LEDGER.md` | This section |

No `app/`, `frontend/src/`, migration, or configuration file was modified. No file deleted.

### 18.9 Cleanup

Stopped by re-verified identity (PID + listener + command line checked immediately before the kill): isolated test server `:51999` (pid 168790, `scripts/test_server.py`) and Vite dev `:3001` (pid 167420). Post-stop listeners: only pre-existing Vite HTTPS `:3000` (58419), production Gunicorn `:5001` (146260–146263) and PostgreSQL `:5432`. No pre-existing service was stopped or restarted. Test database `/tmp/shunya_test_server_g117.sqlite` and all evidence logs under `.hermes/cache/scratch/g117/` are preserved.

### 18.10 Open items after G1.17

1. **KB-02** — false empty state after a successful import (journey step 11); owner decision on canonical emptiness source. Blocks the first-object journey gate. — **CLOSED in G1.18 (see §19)**.
2. **AUTHZ-01** — admin `org.view`; unchanged, pending owner decision.
3. Org bootstrap policy; malformed-email warn-vs-reject — unchanged, pending owner decision.
4. Historical secret-exposure incidents and credential rotation — unaddressed here; remain OPEN.
5. Resend inbox-delivery evidence — provider acceptance only; NOT VERIFIED.
6. `KB-03` (cosmetic/hygiene): `SHUNYA_ENV` in conftest is inert; the paste box opens with sample rows that a keyboard user must clear before typing (documented in the harness, not changed in product).

---

## 19. G1.18 — KB-02 CANONICAL EMPTY-STATE SEMANTICS CLOSED

**Authority:** G1.18 directive. No staging, commit, push, merge, rebase, history rewrite, credential change, production mutation or deployment. Branch and HEAD unchanged; all pre-existing work preserved.

### 19.1 Repository state

| | Branch | HEAD | Modified | Staged | Untracked |
|---|---|---|---|---|---|
| Entry | `feat/commandpalette-ai` | `de9122fc105e4c342a0a34232ab8b99db3bc4a2d` | 35 | 0 | 20 |
| Exit | `feat/commandpalette-ai` | `de9122fc105e4c342a0a34232ab8b99db3bc4a2d` | 37 | 0 | 22 |

G1.18 added: `app/objects/first_object_state.py` (new), `tests/test_first_object_state.py` (new), and modified `app/objects/routes.py`, `app/adapters/os_adapter.py`, `frontend/src/components/home/home-page.tsx`, `frontend/src/components/home/__tests__/home-page-first-object-cta.test.tsx`, `frontend/tests/keyboard-first-object.cjs`, this ledger.

### 19.2 Root cause (observed on an isolated stack, fresh organization)

| Observation | Pre-fix value |
|---|---|
| `GET /api/v1/uop/objects` (the CTA's source) | `200 {"count": 0, "objects": []}` — before **and** after a successful import |
| Import commit (customer) | `201`, `created: 1`, no error |
| `GET /relationships/api/v1/relationships` | `200`, 1 record (the imported customer) |
| Persisted row | `rel_relationships`, `organization_id` = the caller's organization |
| Fresh session after import | homepage still renders "Create your first business object" |

Cause: the CTA asked a **migration-compatibility store** (`sh_uop_objects`) whether the workspace was empty. New writes go to `sh_objects` (`app/objects/canonical.py` documents UOPObject as compat and states that legacy writes were removed), and the import path writes domain records (`rel_relationships`, `leads`, `suppliers`) — never UOP rows. The predicate was therefore structurally incapable of ever returning "not empty" for an import-only organization, regardless of how much real data it held.

Two adjacent facts found while diagnosing (not caused by this defect): `GET /api/v1/objects` returns `403 no_authorized_workspace` for organizations created via `POST /orgs`, because that route provisions no workspace (onboarding does); the executive-home summary had a *second* emptiness consumer counting canonical objects only.

### 19.3 The domain decision

**Canonical definition (adopted):** an organization has created its first business object when it owns at least one **live** record in any canonical business store — `sh_objects` (universal objects), `rel_relationships` (customers/suppliers/partners), `leads`, or `suppliers`. The empty-state question is a **tenant-scoped existence read over authoritative stores**, answered server-side; it is not an object count and not a legacy-store probe.

Why this and not the alternatives:

| Option | Verdict |
|---|---|
| Keep the CTA on `sh_uop_objects` | Rejected — a compat store new writes never touch; structurally unable to answer |
| Point the CTA at `sh_objects` only | Rejected — imported customers/leads/suppliers are domain records; the CTA would still lie to import-only organizations |
| Make the import also write a UOPObject / canonical object per row | Rejected — a second write for one user action with no convergence contract (dual-write ≠ convergence); the domain record is authoritative for a customer |
| Union existence predicate over the authoritative stores (chosen) | No duplicated state, no new write path, no redefinition of any entity; each store remains sole owner of its rows |

Imported records therefore create **only** their canonical domain records. No projection or dual-write was introduced. Consistency is trivial because nothing is duplicated; tenant isolation comes from each store's own organization/tenant column; idempotency remains the import's existing session-token/duplicate detection, untouched.

Convergence of entry points: manual creation, uploads, media, AI-assisted creation and onboarding all write `sh_objects` (covered by one store); imports write `rel_relationships` / `leads` / `suppliers` (covered by the union). Every supported entry point now satisfies the same predicate.

UI distinction: `200 {has_business_data: true|false}` is the only state that may show or hide the CTA. `401`, `403`, `400 no_organization_context`, `503`, a malformed payload, a rejected request, and "still pending" are all **unknown** — the CTA stays hidden and the workspace is never described as empty.

Lifecycle: soft-deleted objects, archived relationships and archived leads/suppliers do not count — the CTA's claim is about the workspace the user is looking at, not about history.

Known limitation (not fixed here): onboarding seeds ~20 empty placeholder canonical objects, so an onboarded organization is non-empty by construction and never sees the CTA. Making "first object" mean "first *user-originated* object" would require provenance on provisioned objects — a separate product decision.

### 19.4 Implementation

- `app/objects/first_object_state.py` (new) — `business_record_counts()` / `get_first_object_state()`: four tenant-scoped counts, live-only, fails closed on a non-positive organization id; read-only, documented as a read model over authoritative stores.
- `app/objects/routes.py` — `GET /api/v1/objects/first-object-state`, gated by `require_permission("knowledge.view")` and resolved from `g.current_org_id` (organization membership, **not** a workspace, so a workspace-less organization still gets a truthful answer). Explicit status contract: 200 authoritative, 400 no organization context, 401, 403, 503 read failure — a failed read is never reported as empty.
- `app/adapters/os_adapter.py` — the executive home's `getting_started` priority now uses the same predicate instead of canonical-object counts, so no surface contradicts the CTA; a failed read or absent organization never claims emptiness.
- `frontend/src/components/home/home-page.tsx` — CTA source changed to the predicate; `has_business_data` must be a boolean or the state stays unknown (`null`) and the CTA stays hidden.
- `frontend/src/components/home/__tests__/home-page-first-object-cta.test.tsx` — rewritten for the new contract (10 tests), including an explicit assertion that the request goes to the predicate and **not** to `/api/v1/uop/objects`.
- `frontend/tests/keyboard-first-object.cjs` — asserts the CTA is backed by a successful empty predicate; after import asserts the predicate reports business data and that a **fresh session** no longer shows the CTA.

### 19.5 Regression coverage

`tests/test_first_object_state.py` — 15 tests: fresh organization empty; every creation path satisfies the predicate (customer import, lead import, supplier import, canonical object); tenant isolation (another organization's rows do not count); lifecycle (archived relationship, soft-deleted object); authorization (401, 403 that is not "empty", fail-closed on a missing organization id); read-only (three reads change no row counts); executive summary agreement (empty → `getting_started` present; import-only → absent).

### 19.6 Verification (final tree)

| Check | Result |
|---|---|
| Targeted backend: `test_first_object_state.py`, `test_objects_read_routes.py`, `test_b16_blueprint_gates.py`, `test_kb01_import_recovery.py`, `test_integration_d8.py` | **72 passed**, exit 0 |
| `npx tsc -b --noEmit` | exit 0, 0 errors |
| `npm run build` | exit 0, bundle `assets/index-LS8dm7YT.js` |
| `npm run test:run` (vitest) | 12 files, **98 passed**, exit 0 |
| axe-core (WCAG 2.0/2.1 A+AA), homepage / signup / login / import panel / relationships | **0 violations** each (automated only — no conformance claim) |
| Journey + keyboard, 1280×800 / 768×1024 / 375×667 | **36/36 each** (keyboard 21, journey 14, setup 1) |
| Full Python suite | see 19.7 |

Journey per viewport confirms: CTA only with a successful empty predicate; keyboard-only login, panel, malformed CSV rejected truthfully; recovery import completes; record persisted; relationship list and detail; reload persistence; predicate reports business data; **CTA gone in a fresh session**; no application-origin 5xx; no horizontal overflow.

### 19.7 Full Python suite

`DATABASE_URL=sqlite:///:memory: .venv/bin/python -m pytest -q` → **5850 passed, 0 failed, 125 skipped, 0 errors**, exit **0**, duration **2358.65 s (39:18)**.

Reconciliation: G1.17 certified 5835 passed; G1.18 adds 15 tests (`tests/test_first_object_state.py`) → 5850. No test was skipped, removed, or loosened.

### 19.8 Cleanup and preserved state

Isolated test server `:51998` (pid 185264, `scripts/test_server.py`, fresh `/tmp/shunya_test_server_g118.sqlite`) stopped by exact PID after identity re-check. Pre-existing services untouched: Vite HTTPS `:3000` (58419), production Gunicorn `:5001` (146260–146263), PostgreSQL `:5432`. Evidence preserved under `.hermes/cache/scratch/g118/`.

### 19.9 Open items after G1.18

1. **Workspace provisioning gap** — organizations created via `POST /orgs` own no workspace, so `GET /api/v1/objects` returns `403 no_authorized_workspace`. The emptiness predicate deliberately avoids workspace resolution, but the canonical object surface remains unusable for such tenants. Product decision required (auto-provision a workspace at organization creation, or make onboarding mandatory before workspace surfaces are reachable).
2. **Onboarding placeholder objects** — ~20 seeded empty objects make an onboarded organization non-empty by construction (see 19.3 limitation).
3. AUTHZ-01, org-bootstrap policy, email warn-vs-reject — unchanged, pending owner decisions.
4. Historical secret-exposure remediation / credential rotation — unaddressed, remain OPEN.
5. Resend inbox delivery — provider acceptance only, NOT VERIFIED.

---

## 20. G1.19 — ORGANIZATION → WORKSPACE LIFECYCLE CLOSED (KB-04)

**Authority:** G1.19 consolidated directive. No staging, commit, push, merge, rebase, history rewrite, credential change, production mutation or deployment. Branch and HEAD unchanged.

### 20.1 Defect and evidence

Two organization-creation implementations existed, and neither provisioned a canonical workspace:

| Route | Model(s) written | Workspace |
|---|---|---|
| `POST /orgs` (`app/routes.py::api_create_org`, used by the SPA onboarding flow) | Organization, OrgMember(owner), default roles, FounderSpace | **none** |
| `POST /orgs` (`app/production/identity/org_routes.py::create_org`) | Organization, OrgMember(owner), default roles | **none** |
| Onboarding completion (`onboarding_routes.py`) | foundational objects, *if* org + workspace resolve | requires one; creates none |

`sh_objects.workspace_id` is NOT NULL, `ObjectService.create()` refuses to invent a workspace, and `resolve_current_workspace()` fails closed with zero authorized workspaces. Observed consequence for a freshly created organization: `GET /api/v1/objects` → `403 no_authorized_workspace`; onboarding logged "objects_created=0 — nothing was seeded"; uploads, media and AI-assisted creation had no writable workspace. The tenant was unusable for every canonical object surface.

Three further lifecycle duplications were recorded (not changed in G1.19): three workspace models — `sh_workspaces` (canonical, used by object authorization), `workspaces` (org workspace API), `user_workspaces` (personal scope) — with three creation paths; and the system default workspaces `spc_business`/`spc_personal`/`spc_custom` which carry no organization and must never serve as tenant context (the authorization layer already refuses them).

### 20.2 Invariant implemented

**An organization owns at least one active canonical workspace from the moment it is created.** Multiple workspaces remain supported; the invariant only guarantees the first one.

`app/authz/org_provisioning.py::ensure_organization_workspace()`:

* idempotent — returns the existing active workspace and creates nothing (`created: False`) on retry;
* membership-gated — the caller must be an ACTIVE `OrgMember` of that organization with role owner/admin; member/viewer are refused (`insufficient_role`), non-members are refused (`not_a_member`), invalid organization ids fail closed (`invalid_organization`);
* tenant-safe — the workspace is created with the organization id and the `ShWorkspaceMembership` only for that identity/workspace pair; no elevation beyond owner→owner, admin→admin;
* transactional — called with `commit=False` so organization, membership, roles, legacy space and workspace commit together.

Wired into both organization-creation routes (same transaction; `workspace_id` added to the response envelope, additive) and used by onboarding completion as an idempotent repair for organizations that predate the fix.

### 20.3 Regression coverage

`tests/test_org_workspace_lifecycle.py` — 8 tests, real signup → verify → login → `POST /orgs` (no fixture repair): exactly one workspace per created organization with an owner membership; object API usable immediately (list 200, create 200 + persisted, detail 200, predicate true); two organizations never share a workspace; repeated provisioning creates no duplicate; non-member and member-role provisioning refused; invalid organization id fails closed; a legacy workspace-less organization gets a distinguishable `403 no_authorized_workspace` (not 500, not an empty success) while the emptiness predicate still answers truthfully.

### 20.4 Verification (final tree)

| Check | Command | Result |
|---|---|---|
| Targeted domain/API/lifecycle/tenant/authz | `pytest tests/test_org_workspace_lifecycle.py tests/test_first_object_state.py tests/test_org_lifecycle.py tests/test_role_normalization.py tests/test_objects_read_routes.py tests/test_b16_blueprint_gates.py -q` | **86 passed**, exit 0 |
| Frontend unit | `npm run test:run` | 12 files, **98 passed**, exit 0 |
| TypeScript | `npx tsc -b --noEmit` | exit 0, 0 errors |
| Production build | `npm run build` | exit 0, `assets/index-LS8dm7YT.js` |
| Journey + keyboard, 1280×800 / 768×1024 / 375×667 | `node tests/keyboard-first-object.cjs` | **36/36 each** (keyboard 21, journey 14, setup 1) |
| axe-core (WCAG 2.0/2.1 A+AA), 5 surfaces | automated scan | **0 violations** each (no conformance claim) |
| Migration chain, fresh disposable PostgreSQL 16 (port 5445, `/tmp/g119_pg`) | `alembic upgrade head` | exit 0 → head `r6b32_organizations_parity` |
| Model↔migration drift, lifecycle tables | metadata vs live PG schema | **0 missing columns** after the parity migrations |
| Runtime persistence on the migrated PG schema | app boot + API journey + raw SQL | **13/14** — org creation provisioned `ws_…`, object persisted with organization+workspace, predicate saw it; the one FAIL is a 409 on re-signup of an already-created user (script re-run artifact, expected) |
| Full Python suite | `DATABASE_URL=sqlite:///:memory: python -m pytest -q` | **5857 passed, 1 failed, 125 skipped**, exit 1, 37:28 |

The single suite failure — `tests/graph/test_edge.py::TestEdgeStorePerformance::test_1000_edges_under_1s` — is a 1-second wall-clock threshold, not a behaviour assertion. It failed while the isolated test server and the disposable PostgreSQL cluster were running concurrently, and **passes in isolation in 0.25 s** (`1 passed`). Classified: load-sensitive performance test, environment-induced; not caused by G1.19 (which touches no graph code). Recorded as a flake to de-flake separately (e.g., mark as a benchmark), not silently skipped.

### 20.5 Migration findings (new, fixed)

Two model↔migration parity gaps made a migration-only PostgreSQL install unusable:

1. `team_members.identity_id` — declared on the model, written by auth/org creation, absent from the chain → the first signup crashed (`UndefinedColumn`). Fixed by `r6b31_team_member_identity` (guarded, nullable, index-if-absent, no backfill).
2. `organizations` — the migration-created table lacked 26 model columns (`business_type`, `email`, `website`, `timezone`, `currency`, `max_members`, branding fields, `legacy_tenant_id`, …), so organization creation crashed. Fixed by `r6b32_organizations_parity` (metadata-driven, guarded, nullable columns, additive only).

Both are forward-only and converge as no-ops on boot-created databases. No history rewrite, no data transformation, no column dropped or re-typed.

### 20.6 Remaining, deliberately unresolved

1. **Workspace model consolidation** — three workspace tables (`sh_workspaces`, `workspaces`, `user_workspaces`) with three creation paths. Consolidation is a schema/migration decision; G1.19 only guarantees the canonical one exists.
2. **Legacy `FounderSpace` write** on the SPA org-creation route — still created alongside the canonical workspace; removal needs a migration/consumer audit.
3. **Onboarding placeholders** (~20 seeded empty objects) — unchanged, still a separate product decision (see §19.3).
4. **Legacy workspace-less organizations in existing data** — repaired on next onboarding completion or by the same idempotent helper; no bulk backfill was executed (no production mutation authorized).
5. AUTHZ-01, org-bootstrap policy, email policy, secret remediation — unchanged.
6. G1.19 Part IX (§21 onward) arrived truncated mid-sentence ("Preserve and extend existing test coverage … execute."); the verification bar applied was the G1.17/G1.18 standard.

---

## 21. G1.20 — PERFORMANCE-TEST RELIABILITY, MIGRATION PARITY & WORKSPACE ARCHITECTURE

**Authority:** G1.20 consolidated directive. No staging, commit, push, merge, rebase, history rewrite, credential change, production mutation or deployment. Branch and HEAD unchanged.

### 21.1 Repository state

| | Branch | HEAD | Modified | Staged | Untracked |
|---|---|---|---|---|---|
| Entry (verified) | `feat/commandpalette-ai` | `de9122fc105e4c342a0a34232ab8b99db3bc4a2d` | 38 | 0 | 26 |
| Exit | `feat/commandpalette-ai` | `de9122fc105e4c342a0a34232ab8b99db3bc4a2d` | 39 | 0 | 26 |

Correction to the G1.19 report: its final counts (40/23) were stated without a closing verification; the verified entry state for G1.20 is 38 modified / 26 untracked. No file was deleted or reverted by G1.19 or G1.20 — the difference is a reporting error in G1.19, recorded here rather than denied.

### 21.2 Performance-test reliability (Workstream A)

Measured, executed: the benchmark creates 500 nodes outside the timed section, then times 1000 edge creations in an in-memory store asserting `elapsed < 1.0 s`.

| Condition | Samples | min | median | max |
|---|---|---|---|---|
| Isolated | 10 | 6.4 ms | 7.5 ms | 74.8 ms |
| Under 4 CPU burners | 10 | 5.4 ms | 10.8 ms | 83.3 ms |

The budget is ~130× the median, so exceeding 1 s is a scheduling stall, not a throughput regression. The defect was the **measurement methodology**: one wall-clock sample.

Fix (smallest justified): `test_1000_edges_under_1s` now takes three clean samples (stores reset between samples), asserts `count == 1000` on **every** sample (correctness, independent of timing), and asserts the **best** sample is under the 1 s budget with a diagnostic listing all three. A stall can only add time, so best-of-three cannot mask a real slowdown; it removes single-sample noise. Budget unchanged at 1.0 s; no skip, no suppression, no threshold inflation. `time.perf_counter()` replaces `time.time()`.

### 21.3 Migration/model parity (Workstream B)

The G1.19 migration `r6b32_organizations_parity` derived its column list from live ORM metadata at upgrade time — a historical migration whose behaviour would change with the model. **Fixed**: the definition is now a frozen list of 27 (name, type) pairs, no metadata import; guarded per column, nullable as the model declares, no server defaults, no NOT NULL imposed on historical rows. `r6b31_team_member_identity` was already frozen.

Verification on a **fresh disposable PostgreSQL 16 cluster** (`/tmp/g120_pg`, port 5445, never 5432): `alembic upgrade head` exit 0 → head `r6b32_organizations_parity`. Model↔live-schema drift audit across 23 in-scope tables — auth/identity (`team_members`, `shunya_identities`), organizations/membership/roles/invitations, all three workspace representations + memberships + `founder_spaces`, canonical objects + compat stores, relationships + timeline + AI memory + categories + custom fields, leads, suppliers — reported **0 missing columns** (`DRIFT_PROBLEMS=0`).

Runtime against that migrated schema: **14/14** — signup 201, login 200, organization creation 201 with a provisioned `ws_…`, canonical list 200, object creation 200, first-object predicate true, workspace row and object row verified by raw SQL on a new connection with the correct organization/workspace, no phantom relationship rows.

Not audited in G1.20 (explicit): nullability/default/constraint/index/FK semantics beyond missing columns; tables outside the listed scope; SQLite↔PostgreSQL behavioural differences beyond the journey.

### 21.4 Workspace architecture (Workstream C)

| Table | Owner / purpose | Consumers (source inspection) |
|---|---|---|
| `sh_workspaces` (+`sh_workspace_memberships`) | canonical workspace for organization-owned business objects; `sh_objects.workspace_id` NOT NULL references it | `ObjectService`, object routes, `workspace_context` authorization, `org_provisioning`, analytics adapter |
| `workspaces` (`tenant_id`, slug) | organization workspace API record | `production/identity/workspace_routes.py` CRUD only |
| `user_workspaces` (+memberships) | personal-scope workspace for identities without an organization | `app/workspace/models.py` context resolution, personal-scope registry |
| `founder_spaces` | legacy founder space; still written by the SPA org-creation route | founder routes, onboarding |

These are **not equivalent concepts** and were not merged. Recommendation: retain distinct concepts, with `sh_workspaces` canonical for object ownership; treat `workspaces` as the org-API projection and `user_workspaces` as personal scope; retire `founder_spaces` only after a consumer/migration audit. Consolidation is blocked on a schema decision (what happens to existing rows in each representation), so only the safe correction was implemented: **one provisioning implementation** (`ensure_organization_workspace`) used by every organization-creation path, replacing duplicated ad-hoc logic.

### 21.5 Lifecycle, tenant isolation, onboarding

Unchanged from G1.19 and re-verified: exactly one workspace per created organization with an owner membership; retry creates no duplicate; non-member and member/viewer roles refused; invalid organization ids fail closed; two organizations never share a workspace; workspace-less legacy tenants receive a distinguishable 403, never a 500 or an empty success. Onboarding completion uses the same idempotent provisioning as a repair.

Not tested in G1.20 (explicit): injected failure during workspace creation or membership/role creation (transaction-rollback evidence), invitation-acceptance → login end-to-end, and the onboarding questionnaire/resume walkthrough. These remain unverified rather than assumed.

Placeholder semantics remain **unresolved by design**: onboarding seeds ~20 empty canonical objects without provenance metadata, so "business data exists" ≠ "the user created meaningful data". No new field, migration, or backfill was invented; the decision and options are recorded in §19.3.

### 21.6 Verification (final tree)

| Check | Command | Result |
|---|---|---|
| Focused graph/performance + lifecycle + first-object + object API + B16 + roles | `pytest tests/graph/test_edge.py tests/test_org_workspace_lifecycle.py tests/test_first_object_state.py tests/test_objects_read_routes.py tests/test_b16_blueprint_gates.py tests/test_role_normalization.py -q` | **110 passed**, exit 0 |
| Frontend unit | `npm run test:run` | 12 files, **98 passed**, exit 0 |
| TypeScript | `npx tsc -b --noEmit` | exit 0, 0 errors |
| Production build | `npm run build` | exit 0, `assets/index-LS8dm7YT.js` |
| Journeys + keyboard, 1280×800 / 768×1024 / 375×667 | `node tests/keyboard-first-object.cjs` | **36/36 each** (keyboard 21, journey 14, setup 1) |
| axe-core (WCAG 2.0/2.1 A+AA), 5 surfaces | automated scan | **0 violations** each (no conformance claim) |
| Migration chain, fresh PostgreSQL | `alembic upgrade head` | exit 0 → `r6b32_organizations_parity` |
| Migration/runtime parity | drift audit + API journey + raw SQL | 23 tables, 0 drift; runtime **14/14** |
| Full Python suite (quiet host: no PG, no test server, no browser) | `DATABASE_URL=sqlite:///:memory: pytest -q` | see 21.7 |

### 21.7 Full suite — PASS

`DATABASE_URL=sqlite:///:memory: .venv/bin/python -m pytest -q` → **5858 passed, 0 failed, 125 skipped, 0 errors**, exit **0**, duration **2446.00 s (40:45)**, run with the disposable PostgreSQL cluster and the isolated app server stopped so the performance benchmark was not starved.

Reconciliation: G1.19 was 5857 passed + 1 failed = 5858 tests. The same 5858 tests now all pass; the performance test was fixed by methodology (three samples, best-of-three against the unchanged 1 s budget), not by weakening it. No test was skipped, deleted, or had its threshold raised.

### 21.8 Remaining owner decisions and blockers

1. Workspace-table consolidation / retirement of `founder_spaces` and `user_workspaces` — schema decision; plan above, implementation blocked.
2. Placeholder provenance ("first business object" vs "first meaningful object") — product decision.
3. Legacy workspace-less organizations in existing data — no production backfill authorized; the idempotent helper repairs on next onboarding.
4. AUTHZ-01, bootstrap policy, email policy — unchanged.
5. Historical credential/history exposure and Resend inbox delivery — OPEN.
6. Migration parity beyond the audited scope (constraints/indexes/FKs) — not audited.

### 21.9 Cleanup

Stopped by exact PID after identity re-check: isolated app server `:51996` (200727) and the disposable PostgreSQL cluster on 5445 (`pg_ctl stop`, `pg_isready` exit 2). Preserved: `/tmp/shunya_test_server_g120.sqlite`, `/tmp/g120_pg`, logs under `.hermes/cache/scratch/g120/`. Pre-existing production Gunicorn `:5001` (146260–146263, 192510) and PostgreSQL `:5432` untouched. The Vite `:3000` process remains absent as reported in G1.18; still unattributed.

---

## 22. G1.21 — TRANSACTION INTEGRITY, LIFECYCLE CLOSURE & SCHEMA AUTHORITY

**Authority:** G1.21 + G1.21-CLOSE directives. No staging, commit, push, merge,
rebase, history rewrite, credential change, production mutation or deployment.
Branch and HEAD unchanged throughout. Every claim below is marked
**[executed]**, **[source]**, **[inferred]** or **[not tested]**.

### 22.1 Repository state

| | Branch | HEAD | Modified | Staged | Untracked |
|---|---|---|---|---|---|
| Entry | `feat/commandpalette-ai` | `de9122fc105e4c342a0a34232ab8b99db3bc4a2d` | 39 | 0 | 26 |
| Final | `feat/commandpalette-ai` | `de9122fc105e4c342a0a34232ab8b99db3bc4a2d` | **48** | **0** | **35** |

Nothing was reverted, deleted or regenerated. The delta is G1.21's own work: 9
modified files beyond the G1.20 set (incl. the two test files whose fixtures had
to reflect the corrected authorization and the declared test context), and 9 new
files (5 migrations, 4 modules, 5 test files, 3 decision/ledger docs, plus local
audit scripts that live in the scratch directory).

### 22.2 Schema authority — the central finding **[executed]**

Two schema authorities exist and they do **not** produce the same database. Measured
on the disposable cluster (`127.0.0.1:5445`, data dir
`.hermes/cache/scratch/g121/pg`), same source tree:

| Starting point | Tables | Foreign keys | Indexes |
|---|---|---|---|
| Migration-first (`alembic upgrade head`) | 177 | **32** | 302 |
| Boot-first (`create_app()` → `create_all()`) | 160 | **163** | 579 |

`create_app()` runs `db.create_all()` for every non-`:memory:` URI, so a
migration-only install silently gained 7 tables and 4 FKs at boot — and *never*
gained the 28 ORM-declared FKs on tables that already existed, because
`create_all` does not alter existing tables. The chain was also not idempotent
against a boot-created schema (`DuplicateColumn: team_members.birth_date`,
`DuplicateTable: sh_alert_events`).

**Forward migrations added** (all guarded, additive, definitions frozen in the
revision, no metadata import at runtime, no destructive downgrade):

| Revision | Purpose |
|---|---|
| `r6b33_personal_workspace_tables` | `user_workspaces`, `user_workspace_memberships` — existed only via `create_all` |
| `r6b34_identity_integrity` | 20 FKs, 9 unique indexes, 8 supporting indexes (orphan/duplicate-guarded) |
| `r6b35_missing_boot_tables` | the last 8 `create_all`-only tables incl. `execution_idempotency` (retry primitive) |
| `r6b36_onboarding_progress` | `user_profiles.onboarding_step` / `onboarding_completed_steps` (nullable) |
| `r6b37_onboarding_sessions` | `onboarding_sessions` (questionnaire answers + position) |

Guards repaired in `r6b28` and `r6b29` so the chain can run against a boot-created
database. Head: **`r6b37_onboarding_sessions`**.

**Evidence [executed]:** fresh zero→head exit **0**, 188 tables; repeat upgrade exit
**0** (no-op); `alembic downgrade r6b33` → `upgrade head` symmetric (53→33→53 FKs);
boot-first database now migrates to head exit **0**; **ORM tables absent from the
chain = 0**.

**Constraint audit** (403 columns, 33 tables; every missing index re-verified
against `pg_indexes` before being treated as real):

* BLOCKER: **0** (was 2 — the personal-scope tables).
* HIGH: **7** — deliberately deferred: `workspaces.tenant_id` (the writer stores an
  *organization* id, so the ORM's FK to `tenants` would reject valid rows),
  memory `tenant_id` columns (tenancy semantics unresolved; convergence revisions
  intentionally dropped legacy `tenants` FKs), `invitation_tokens` (no writer —
  dead table, retirement candidate), `organizations.legacy_tenant_id` (documented
  bridge; an FK would block legacy cleanup), `rel_relationships.legacy_person_id`,
  `founder_objects.space_id` (retirement candidate).
* MEDIUM: **36** performance-only indexes (no FK behind them) + 1 ondelete
  difference on `sh_objects.organization_id` (PG `SET NULL`, ORM default) —
  deferred pending query-plan evidence, not applied for ORM symmetry.

### 22.3 Transaction integrity — fault injection **[executed]**

`tests/test_g121_provisioning_atomicity.py`, 10 tests. Failures injected with
SQLAlchemy session events inside the live unit of work, then the database is read
with raw SQL on the app's own engine. A control test proves the counter sees
committed rows, and each test asserts the injection actually fired **and** that the
organization was inside the transaction at that moment — otherwise "no rows
afterwards" would prove nothing.

| Boundary | Result |
|---|---|
| after organization insert | rolled back, retry 201, 1 org / 1 workspace / 1 membership |
| after owner membership | same |
| after default roles | same |
| after canonical workspace | same |
| after workspace membership | same |
| immediately before commit | same |

**Defect found:** `seed_default_roles()` committed unconditionally. Injecting a
failure at workspace creation left the organization, owner membership and 5 roles
**persisted with no canonical workspace** — the exact invariant G1.19 closed,
reachable through the error path. Fixed with `commit=False` in all five
in-transaction callers; standalone callers keep historical behaviour.

Also fixed: `POST /orgs` slug generation was unsanitized and non-unique on the SPA
route (a second organization with the same name became `IntegrityError` → HTTP 500).
One shared implementation (`app/authz/org_slug.py`) now serves both creation
routes, and a collision that escapes the pre-flight check returns **409**, not a
stack trace. Verified by test (distinct slugs; forced race → 409, nothing persisted).

### 22.4 Invitation lifecycle **[executed]**

`tests/test_g121_invitation_journey.py`, 8 tests: owner invites → invitee accepts →
canonical identity + membership resolve → login → **authorized resource 200** →
second tenant 403 → token replay 404 → malformed/expired/revoked 404 →
weak password 400 with the invitation still usable.

**Three defects fixed:**

1. `list/create/revoke` were `@login_required` only: **any** authenticated user
   could enumerate another tenant's invitations *including raw acceptance tokens*,
   invite into any organization, and revoke its invitations. Now owner/admin
   membership is required (`_require_org_admin`), and listings no longer
   re-broadcast tokens (`token_present` instead).
2. Acceptance granted no workspace membership, so an invitee could accept, log in,
   and still receive `403 no_authorized_workspace` on every object surface.
   `grant_workspace_access()` now grants the organization's active workspaces in the
   same transaction, with a non-elevating role map (member/viewer never become
   admin — the previous `_ensure_membership` promoted every non-owner to `admin`).
3. `seed_default_roles` committed mid-transaction during acceptance (same class as
   22.3).

**Delivery channel [executed]:** `email_core.send()` blocks every send unless
`is_human_triggered=True`, so no invitation email leaves the process; the token
returned once to the inviting admin is the supported channel in this environment.
The journey asserts this rather than assuming an inbox received it. Inbox
delivery remains **NOT TESTED** and is an open launch blocker (§22.9).

### 22.5 Onboarding: identity, resume, idempotency **[executed]**

`tests/test_g121_onboarding_journey.py`, 4 tests + the PostgreSQL journey (§22.6).

**Defects fixed:**

* Completion resolved the wrong identity (`str(user.id)` / email) while `OrgMember`
  holds the canonical `sid_*`, so a normal signup resolved **no organization** and
  silently seeded **zero** foundational objects. Canonical identity is now resolved
  once, in fixed priority (`TeamMember.identity_id` → email → user id).
* Repeated completion created all 26 placeholders again (52, 78, …). Seeding is now
  idempotent per (workspace, type, name); a repeat returns `objects_created: 0`.
* Onboarding step state lived in a module-level dict, so a reload on another worker
  or any restart restarted the questionnaire. Now persisted in
  `user_profiles.onboarding_step` / `onboarding_completed_steps`.
* The questionnaire engine kept answers in `_sessions` ("In-memory for now");
  now persisted in `onboarding_sessions` (unique per organization+identity).
* `/api/v1/objects` denial returned `(_deny(exc),)` — a 1-tuple — so an ambiguous
  scope produced **HTTP 500** instead of 403. Fixed and regression-pinned.

### 22.6 Fresh PostgreSQL migration + runtime journey **[executed]**

Disposable cluster only (`127.0.0.1:5445`, data dir under
`.hermes/cache/scratch/g121/pg`, owner `shunya-deploy`, mode 700, verified from the
server itself — never from a port number). New database `shunya_g121_final` created
after confirming it did not exist.

| Check | Command | Result |
|---|---|---|
| Full chain from zero | `alembic upgrade head` | exit **0**, head `r6b37_onboarding_sessions`, 188 tables |
| Repeat upgrade | `alembic upgrade head` | exit **0**, no-op |
| Onboarding schema | `information_schema` + `pg_constraint` | 2 nullable columns on `user_profiles`; `onboarding_sessions` PK + `uq_onboarding_session_identity` + 2 indexes |
| Runtime journey | `pg_journey_g121.py` (real app, test client) | **28/28**, exit 0 |

Journey evidence (all verified again with raw SQL on a **separate** connection):
`no_create_all_repair` (188 tables before boot, 188 after), signup → verify → login
(session `sid_…`), organization + `ws_…` + owner membership rows, onboarding step
resume after clearing process memory and re-logging in (`org_setup`, persisted
`["profile"]`), questionnaire resume (`industry`, answers persisted), completion
`objects_created: 26`, repeat `0`, 26 sh_objects rows, object create/list/detail,
raw row carrying the correct organization **and** workspace, cross-tenant detail
404, cross-tenant listing isolated, no duplicate workspaces or memberships.

### 22.7 Accessibility **[executed]**

Two violations found on authenticated surfaces that the G1.20 five-surface scan
missed (it scanned unauthenticated surfaces):

1. `aria-prohibited-attr` — a bare `<div>` carried `aria-label`. Fixed with list
   semantics (`role="list"` / `role="listitem"` + `aria-current="step"`), dot
   marked `aria-hidden`.
2. `color-contrast` on `.sh-onboarding-step-label`.

The contrast failure was **not** a colour-choice problem. Measured in the browser:
the labels' background resolved to the light page (`rgb(251,248,245)`), giving
1.79:1 and 3.16:1. `document.elementFromPoint()` at each label's own centre
returned `.sh-onboarding-content` — i.e. the strip was painted **behind** the
full-screen opaque step surface (`position: fixed; inset: 0; #0a0a0f`). The step
indicator was dead UI: in the DOM (so screen readers announced it), never visible.
The earlier colour change had been tuned for a dark surface it never sat on.

Fix: the strip is pinned above the step surface on the `#0a0a0f` background it was
designed for, with content padding clearing it. Verified in the rendered browser —
`selfHit: true` for all three labels, contrast **10.44:1** (current) and **5.91:1**
(future) against `rgb(10,10,15)` — then axe re-run:

| Surface | axe (WCAG 2.0/2.1 A+AA) |
|---|---|
| `/auth/signup` | **0 violations** |
| `/auth/login` | **0 violations** |
| Executive Home (authenticated) | **0 violations** |
| Workspace first-object CTA | **0 violations** |
| Relationships workspace | **0 violations** |

Zero automated violations is not a WCAG conformance claim.

### 22.8 Frontend, responsive, keyboard **[executed]**

| Check | Command | Result |
|---|---|---|
| Unit | `npm run test:run` | 12 files, **98 passed**, exit 0 |
| TypeScript | `npx tsc -b --noEmit` | exit 0 |
| Production build | `npm run build` | exit 0, `assets/index-Dlm26ysU.js` |
| Served bundle is the final tree | `SHUNYA_FRONTEND_DIST=frontend/dist` + shell read | shell references `index-Dlm26ysU.js` (**not** the published release) |
| Journeys + keyboard 1280×800 / 768×1024 / 375×667 | `node tests/keyboard-first-object.cjs` | **36/36 each** (keyboard 21, journey 14, setup 1) |

Forcing `SHUNYA_FRONTEND_DIST` was necessary: by default the app serves the
immutable published release (`assets/index-DyJRkUmo.js`), so a harness run without
it would have certified an older bundle.

### 22.9 Security incidents **[source + executed checks; remediation NOT performed]**

Verified without reading any secret value: no tracked `.env`, no tracked token
file, `.gitignore` covers `.env`, `.env.audit`, `uploads/`. History still contains
`data/telegram_bot_token.txt` at `4fe3f99` (one line matching a real bot-token
shape; removed from the tree at `5e1fcf2`), `uploads/` PII across 4 commits, and
`.env` blobs (placeholder-era) in 2 commits. **Current-tree cleanliness is not
remediation.**

Isolation guard hardened (endpoint identity **and** execution context): loopback
only, production names refused on any port, port 5432 refused without an isolation
marker, and a PostgreSQL URL refused outside a declared test context. `conftest.py`
ordering fixed — the environment was declared *after* the guard ran, which would
have made every PostgreSQL certification run look like production. 58 tests.

Owner/infra actions still required: rotate the Telegram bot token; purge or make
private the historical PII/token; rotate any key flagged later; Resend inbox
delivery remains unverified (provider acceptance only).

### 22.10 Full Python suite **[executed]**

Canonical configuration: `DATABASE_URL=sqlite:///:memory: .venv/bin/python -m pytest -q`,
run on a quiet host (disposable PostgreSQL cluster stopped, no test server, no
browser). The pytest exit code is written into the log by the run itself, so a
wrapper cannot mask it.

**First run — FAILED (12 failed, 5895 passed, 125 skipped, exit 1, 42:12).**
Recorded here rather than overwritten. Two groups, both diagnosed to root cause:

1. **11 × `tests/production/identity/test_invitation.py`** — the `org` fixture
   returned an organization *unrelated* to the session identity, so every call was
   now a 403. The tests had only ever passed because the endpoints had no
   membership check (the defect fixed in §22.4). Correction: the fixture now
   returns the organization `seed_rbac` provisions for the caller, **and** a new
   test asserts a non-member is refused with nothing persisted — the suite is
   strictly stronger, not weaker.
2. **1 × `tests/test_debug_space_creation_safety.py::…::test_guard_passes_but_no_db_connect`**
   — the subprocess was given `DATABASE_URL` but never declared `SHUNYA_ENV=test`,
   so the hardened guard (§22.9) refused the PostgreSQL URL *before* `create_app`.
   The guard was correct; the harness was silent. Correction: the subprocess now
   declares the test context; every assertion is unchanged.

Focused rerun of both files: **21 passed, exit 0**.

**Final run — PASS:**

    DATABASE_URL=sqlite:///:memory: .venv/bin/python -m pytest -q
    → 5908 passed, 0 failed, 125 skipped, 0 errors, exit 0, 2103.04 s (35:03)
    log: .hermes/cache/scratch/g121/c_fullsuite_final.log

Reconciliation: 5858 (G1.20) → 5895 (first G1.21 run: +37 new tests) → 5908 (final:
+13 from the invitation authorization coverage and the two corrected files' extra
case). The 125 skips are the pre-existing set — PostgreSQL-only, live-network and
environment-gated tests; none is a suppressed failure, and no test was deleted,
weakened or relabelled to obtain this result.

### 22.11 Gate status

| Gate | Status |
|---|---|
| A. Schema authority / migration completeness | **PASS** (7 FKs + 36 indexes deferred with reasons) |
| B. Organization/workspace transaction integrity | **PASS** (6 boundaries + retry) |
| C1. Invitation lifecycle | **PASS** (invitation *email delivery* NOT TESTED) |
| C2. Onboarding resume/idempotency | **PASS** |
| D. First-use provenance | **BLOCKED** on owner decision D-1/D-2 (`G121_PLACEHOLDER_PROVENANCE_DECISION.md`) |
| E. Workspace architecture | **PASS** (decision: retain; 3 owner decisions recorded) |
| F. Security remediation | **FAIL** — historical exposure unremediated (unauthorized) |
| G. UI/UX accessibility + responsive | **PASS** for tested surfaces; WCAG conformance **NOT TESTED** |
| H. Full Python suite | **PASS** — 5908 passed / 0 failed / 125 skipped / exit 0 |
| I. Production deployment verification | **NOT TESTED** (deployment unauthorized) |

### 22.12 Cleanup and preserved artifacts

Stopped by exact PID after identity re-check: G1.21 test server `:51999`
(218420 → confirmed `.venv/bin/python scripts/test_server.py`, port free after).
Disposable cluster `:5445` (PID 205852, data dir `scratch/g121/pg`) stopped at the
end of the milestone; its databases and logs are preserved. Pre-existing production
Gunicorn `:5001` (146260–146263, 192510) and PostgreSQL `:5432` untouched.

Preserved under `.hermes/cache/scratch/g121/`: migration logs, schema snapshots,
`migration_only_schema.sql`, parity/index JSON, probe stage logs, axe JSON,
keyboard/journey logs, full-suite log. Preserved databases on the disposable
cluster: `shunya_g121`, `_probe`, `_bootfirst`, `_boot2`, `_mig`, `_mig2`,
`_final`.

---

## 23. G1.22 — SECURITY INCIDENTS, FIRST-USE SEMANTICS & LAUNCH READINESS

**Authority:** G1.22 directive. No staging, commit, push, merge, rebase, history
rewrite, credential change, production mutation or deployment. Branch and HEAD
unchanged. Every claim is marked **[executed]**, **[source]**, **[inferred]** or
**[not tested]**.

### 23.1 Repository state

| | Branch | HEAD | Modified | Staged | Untracked |
|---|---|---|---|---|---|
| G1.21 exit | `feat/commandpalette-ai` | `de9122fc…` | 48 | 0 | 35 |
| G1.22 exit | `feat/commandpalette-ai` | `de9122fc…` | 48 | 0 | 39 |

The modified count is unchanged from G1.21 because the three files G1.22 edited
(`app/communication/email_core.py`, `app/production/identity/invitation_routes.py`,
`tests/conftest.py`) were already in that set; the four new untracked files are one
test module and three documents.

Reconciled with the G1.21 report before any change: entry state matched exactly
(48 modified / 0 staged / 35 untracked), and no G1.21 service was running.

### 23.2 Security incidents — evidence and plan **[executed checks; remediation NOT performed]**

Full plan: `docs/launch/G122_SECURITY_REMEDIATION_PLAN.md`.

| Incident | State in history | State at HEAD | Validity / action |
|---|---|---|---|
| INC-1 Telegram bot token (`data/telegram_bot_token.txt`, `4fe3f99`, removed `5e1fcf2`) | present | **absent** | validity **unknown** — testing it is unauthorized. Owner must rotate via BotFather |
| INC-1b + INC-2 history content (token blob, `uploads/` PII across 4 commits) | present | **absent** | owner decision: private repo (reversible) or path-scoped purge + force-push (irreversible) |
| INC-3 `.env` blobs (2 commits) | present, placeholder-era | **absent** | none beyond INC-1b |
| INC-4 **tests reached a live email provider** | n/a | n/a | **found and contained in G1.22** — see below |

**INC-4 detail [executed]:** with `RESEND_API_KEY` present in the host environment,
a signup inside the suite issued a real call to `api.resend.com` ("Email accepted by
Resend: id=01a160…", followed by 429 retries) for a synthetic `@g122.test` address.
Cause: `email_service.send_email()` correctly passes `is_human_triggered=True`, and
nothing in the test configuration removed provider credentials. **No recipient
existed, nothing was delivered, and no production account was contacted** — but the
outbound request was real. Containment: `tests/conftest.py` now **forces**
`EMAIL_PROVIDER=smtp` and removes `RESEND_API_KEY`/`EMAIL_USER`/`EMAIL_PASSWORD`
from the test process before the app is imported; a regression test asserts the
non-sending mode and that `status != "accepted"`. Re-ran the email suites: **0**
`api.resend.com` occurrences.

This also corrects a G1.21 statement: §22.4 asserted "no invitation email leaves the
process" — that was true only of `email_core.send()`'s default parameter, not of the
configured environment. The corrected fact: `send_email()` does send, and delivery
depends on provider configuration.

**INC-5 — live provider key surfaced in a test log [executed, contained, needs owner action].**
The first containment attempt (pop the env vars in `conftest`) was **insufficient and
the regression test proved it**: `create_app()` calls `load_dotenv()`, which re-reads
the host `.env` and restores `RESEND_API_KEY` in `os.environ`; `email_core` had
already captured that value at import. The failing assertion therefore printed the
key into the suite log.

* The key is a **live credential**. It was not printed to a console by intent, not
  transmitted anywhere, and not used beyond the provider calls already described —
  but it now existed in a local log file.
* Containment (verified): `conftest` neutralises the **module state**
  (`_PROVIDER`, `_RESEND_API_KEY`, `_USER`, `_PASSWORD`) and re-asserts it in an
  autouse fixture before/after **every** test, so no test can inherit host
  credentials however many times `create_app()` reloads `.env`. Re-ran the delivery
  suite: **6 passed, 8.45 s, 0 provider/network lines** (previously 116 s with real
  429 retries — the timing difference is itself evidence the network path is gone).
* Evidence handling: the original log is **preserved unmodified** (3 key-shaped
  occurrences) and a redacted working copy was written from a stream
  (`f_fullsuite.redacted.log`, 1168 lines, 0 occurrences) so diagnostics survive
  without the secret. No further copies of the log were made.
* **Owner action required:** treat this key as exposed — rotate it in the Resend
  dashboard, update the production environment, then delete the original log file
  through the approved process. `CREDENTIAL_ROTATION_AUTHORIZED = NONE` here, so
  neither rotation nor deletion was performed.
* **Structural cause worth fixing later:** `create_app()` calls `load_dotenv()`
  unconditionally, so every test process inherits production secrets. Skipping
  `load_dotenv()` under `TESTING` would remove the class of defect rather than
  neutralising it downstream. Not changed in G1.22 (it is a production
  configuration change and deserves its own review).

**Additional security fix [executed]:** the `[EMAIL LOG]` line printed the first 200
characters of the message body — which is exactly where verification, invitation and
password-reset tokens live. Both provider branches now log
`Body: <redacted>` plus recipient/subject/type, and the invitation route logs only a
status. `tests/test_g122_invitation_delivery.py` asserts the raw token never appears
in captured logs.

### 23.3 Invitation delivery **[executed to the provider boundary; inbox NOT tested]**

`tests/test_g122_invitation_delivery.py`:

* the composed message targets the intended recipient and contains
  `/auth/invitation?token=…` **exactly once**;
* the durable `EmailRecord` hashes exactly that body (proven by rebuilding it from
  token + recipient + organization name and comparing `body_hash` — the test never
  needs the body at rest);
* the provider boundary is truthful: with no provider configured the record is
  **not** `accepted`, and the API returns
  `delivery: {status: "logged", delivered: false, record_id: …}` instead of
  implying the invitee received anything (this response field is new in G1.22);
* token binding: lookup returns the invited address, the organization id and the
  organization name; acceptance creates the account for that address only; replay
  after acceptance is 404 with an explicit reason;
* listings still expose no token.

**Blocker for inbox delivery:** there is no authorized non-production mail provider
in this environment (no sandbox Resend key; the SMTP path requires STARTTLS against
a certificate-valid host, which a local sink cannot provide without changing
production code). Owner action: provide a Resend sandbox key or an authorized
non-production SMTP relay, then re-run this journey to assert
`delivery.status == "accepted"` and observe the mailbox.

### 23.4 First-use provenance — **BLOCKED on owner decision** **[executed measurement]**

Current behaviour was re-measured, not assumed: immediately after onboarding,
`GET /api/v1/objects` returns 26 rows and
`GET /api/v1/objects/first-object-state` returns `has_business_data: true`, with no
user-entered data. The pinned test in
`tests/test_g121_onboarding_journey.py` fails if this changes silently.

No provenance field was added and no existing record was converted, because D-1
(which semantics) and D-2 (may AI ground on examples) are unresolved owner
decisions. `docs/launch/G121_PLACEHOLDER_PROVENANCE_DECISION.md` remains the
decision record; the recommended default there is unchanged: persist
`provenance` (`user` / `onboarding_seed` / `import` / `ai`), exclude seeds from
first-use counting and from AI grounding, and mark already-edited seeds as user
data rather than backfilling guesses.

**Smallest decision needed:** D-1 (option A/B/C) and D-2 (yes/no).

### 23.5 Database integrity **[source + prior snapshot]**

Reviewed all 7 deferred foreign keys, the one on-delete difference and the 36
non-unique indexes. Full reasoning:
`docs/launch/G122_DATABASE_INTEGRITY_EVIDENCE.md`.

**No constraint was added.** Each candidate fails an evidence test: wrong target
(`workspaces.tenant_id` holds an organization id), unresolved semantics (memory
`tenant_id`), no writer (dead `invitation_tokens`), legacy cleanup path (bridge and
`legacy_person_id`), retirement candidate (`founder_objects.space_id`), or index
justification that requires production query plans that do not exist here.

### 23.6 Journeys, frontend, accessibility **[executed]**

| Check | Command | Result |
|---|---|---|
| Frontend unit | `npm run test:run` | 12 files, **98 passed**, exit 0 |
| TypeScript | `npx tsc -b --noEmit` | exit 0 |
| Production build | `npm run build` | exit 0, `assets/index-Dlm26ysU.js` |
| Served bundle | shell read from the isolated server | `index-Dlm26ysU.js` (**not** the published release; `SHUNYA_FRONTEND_DIST` forced) |
| Journeys + keyboard 1280×800 / 768×1024 / 375×667 | `node tests/keyboard-first-object.cjs` | **36/36 each** (keyboard 21, journey 14, setup 1) |
| axe (WCAG 2.0/2.1 A+AA), 5 surfaces | `node axe-g121.mjs` (loopback-only) | **0 violations** each |

The test server was started with `EMAIL_PROVIDER=smtp` and no credentials so the UI
journeys could not trigger a real send.

**Not tested:** invitation acceptance through the browser UI (`/auth/invitation`
verified by source inspection only) and manual assistive-technology testing.

### 23.7 Full Python suite **[executed]**

`DATABASE_URL=sqlite:///:memory: .venv/bin/python -m pytest -q`, quiet host, exit
code written into the log by the run itself.

**Run 1 — FAILED (1 failed, 5913 passed, 125 skipped, exit 1, 36:03).** The single
failure was the new guard
`test_provider_is_forced_to_non_sending_mode`: it found `RESEND_API_KEY` present
mid-suite and printed it (INC-5). This is the case where a failing security test was
the *correct* outcome — the protection had lapsed because `create_app()` reloads
`.env`. Recorded, not suppressed; the log was preserved and a redacted working copy
made.

**Fix:** neutralise `email_core`'s module state (not just the environment) and
re-assert it in an autouse fixture before/after every test.

**Run 2 — PASS:**

    5914 passed, 0 failed, 125 skipped, 0 errors, exit 0, 2223.04 s (37:03)
    log: .hermes/cache/scratch/g122/h_fullsuite_final.log
    (redacted review copy: f_fullsuite.redacted.log — original preserved for evidence)

Reconciliation: 5908 (G1.21) → 5913 (G1.22 run 1, +5 delivery/binding tests) → 5914
(run 2, +1 guard case). The 125 skips are the pre-existing environment-gated set
(PostgreSQL-only, live-network, provider-gated); none is a suppressed failure.

### 23.8 Gate status

| Gate | Status |
|---|---|
| A. Security incident closure | **FAIL** — INC-1 rotation and INC-1b/INC-2 history decisions require owner authorization; INC-4 contained |
| A3. Recurrence prevention | **PASS** — email transport locked in tests, token bodies redacted, isolation guard + no-fallback tests |
| B. First-use provenance | **BLOCKED** — D-1/D-2 unresolved; current behaviour measured and pinned |
| C. Invitation delivery | **PASS at the provider boundary**; inbox delivery **NOT TESTED** (no authorized provider) |
| D. Deferred DB constraints/indexes | **PASS as a decision** — reviewed with evidence, nothing added, residual risks recorded |
| E. Product journeys (3 viewports, keyboard, axe) | **PASS** for tested journeys; invitation UI journey **NOT TESTED** |
| F. Launch-readiness inventory | **PASS as a document**; verdict `PUBLIC_LAUNCH_READY = FALSE` |
| G. Full Python suite | **PASS** — 5914 passed / 0 failed / 125 skipped / exit 0 |
| H. Production verification | **NOT TESTED** — unauthorized |

### 23.9 Cleanup

G1.22-created test server `:51999` (PID 229359, `.venv/bin/python
scripts/test_server.py`) stopped by exact PID after identity re-check; port freed.
No PostgreSQL cluster was started in G1.22 (the G1.21 cluster remains stopped with
its databases intact). Production Gunicorn `:5001` and PostgreSQL `:5432` untouched.
Artifacts preserved under `.hermes/cache/scratch/g122/` (suite log, axe JSON,
per-viewport harness logs, delivery-test logs, vitest/tsc/build logs).

---

## 24. G1.23 — CREDENTIAL CONTAINMENT, TEST ISOLATION ROOT CAUSE & LAUNCH BLOCKERS

**Authority:** G1.23 directive. No staging, commit, push, merge, rebase, history
rewrite, credential rotation, evidence deletion, production mutation or deployment.
Branch and HEAD unchanged. Claims are marked **[executed]**, **[source]**,
**[inferred]** or **[not tested]**.

### 24.1 Reconciled starting state

| | Branch | HEAD | Modified | Staged | Untracked |
|---|---|---|---|---|---|
| G1.22 exit | `feat/commandpalette-ai` | `de9122fc…` | 48 | 0 | 39 |
| G1.23 exit | `feat/commandpalette-ai` | `de9122fc…` | 48 | 0 | 40 |

Entry matched the G1.22 report exactly; no service was running. Nothing was reset,
cleaned, stashed or discarded. The modified count is unchanged because
`app/__init__.py` was already in the G1.21-modified set; the one new untracked file
is `tests/test_g123_test_env_isolation.py`.

### 24.2 Resend key (INC-5) — containment status **[executed metadata only]**

No secret was printed, copied, tested or transmitted in G1.23; the original log was
not opened.

| Item | State |
|---|---|
| Original evidence | `.hermes/cache/scratch/g122/f_fullsuite.log`, 96,336 bytes, owner `shunya-deploy`, mode **664**, mtime 2026-10-21 23:04 |
| Redacted review copy | `f_fullsuite.redacted.log`, 96,304 bytes, 1,168 lines (identical), 0 key-shaped occurrences |
| Additional copies | None created in G1.23. **Not verified:** host log rotation/backup may hold further copies — requires the owner's operational access, not available here |
| Credential status | **Exposed until the owner says otherwise.** Rotation was not performed (`CREDENTIAL_ROTATION_AUTHORIZED = NONE`) |
| Evidence deletion | Not performed (`EVIDENCE_DELETION_AUTHORIZED = NONE`) |

**Finding worth acting on:** the evidence file is mode `664` — group- and
world-readable on the host. Until rotation and disposition, it should be `600`.
Not changed here (it is owner evidence); recorded as an owner step.

**Owner action sequence (exact):**
1. In the Resend dashboard, identify the key by its `re_…` prefix and creation date
   (do not paste it into any chat or ticket).
2. Revoke it; create a replacement scoped to sending only.
3. Update the production secret store, restart the mail worker/service, confirm a
   test send from the production path.
4. Confirm the application reads the new value from the intended source without
   printing it (`GET /health`-style evidence only; no value disclosure).
5. `chmod 600` then dispose of the original log per the incident-retention policy;
   keep the redacted copy for review.
6. Record residual exposure: any log shipper, backup or shell history that captured
   the line before rotation.

### 24.3 Historical repository exposure (INC-1/2/3) — decision input **[source + prior evidence]**

Incidents remain separate and unresolved; current-tree absence is **not**
remediation. `docs/launch/G122_SECURITY_REMEDIATION_PLAN.md` holds the records.

Repository-remediation decision (owner's, not taken here):

| | Option A — restrict access | Option B — path-scoped history cleanup |
|---|---|---|
| What it fixes | Stops *new* exposure; keeps history intact | Removes the objects from default-branch ancestry |
| Paths/objects affected | none | `data/telegram_bot_token.txt` (1 blob, 2 commits), `uploads/**` (4 commits), `.env` (2 commits) |
| Irreversibility | Reversible | **Irreversible** for every clone/fork; all SHAs after the rewrite change |
| Coordination needed | none | every collaborator re-clones; forks/mirrors/CI caches must be purged; `git bundle` backup of all refs first |
| Residual exposure | existing clones, forks, caches, prior downloads | anything already cloned, forked, or scraped; GitHub-side caches unless Support purges |
| Approval | repository owner | repository owner, explicitly accepting force-push |

These solve different problems and neither eliminates copies that already exist.
**No choice was made on the owner's behalf.**
Telegram token rotation steps are in the same document (BotFather `/revoke` →
update env → restart → verify round-trip) and were **not** performed.

### 24.4 Test-environment isolation — root cause fixed **[executed]**

**Root cause [source]:** `create_app()` called `load_dotenv()` unconditionally as its
first statement. `load_dotenv()` *fills in missing* variables, so a harness that had
removed `RESEND_API_KEY` had it restored from the host `.env` — together with every
other production secret the harness did not override. The G1.22 module-state
neutralisation suppressed the symptom; it did not stop the reload.

**Fix [executed]:** `app/__init__.py` now decides before loading:

```
declared_test_environment(config_override)  # TESTING, or SHUNYA_ENV/FLASK_ENV in
                                            # {test,testing,ci,cert,certification},
                                            # or PYTEST_CURRENT_TEST
create_app(): if declared test run -> do NOT call load_dotenv()
              else                -> load_dotenv()   (unchanged)
```

Production and development behaviour is untouched: a process that declares nothing
still loads `.env`, which a test pins.

**Regression evidence [executed]** — `tests/test_g123_test_env_isolation.py`, 14
tests: the predicate truth table (including production ≠ test), `load_dotenv` never
called in test mode (spy, 1 and 3 sequential `create_app` calls), `load_dotenv`
**is** called when nothing is declared, a synthetic canary key set in the environment
after import never reaches `email_core`, and the provider stays non-sending.
Focused run with the delivery/db-guard suites: **79 passed**, and **0**
provider/network lines in the log.

**Correction to G1.22's framing:** that milestone said the fix was module-state
neutralisation. That was containment; this is the root cause.

### 24.5 Invitation delivery **[executed at the boundary; inbox BLOCKED]**

Unchanged semantics, re-verified by the delivery suite (6 tests): composition to the
intended recipient with `/auth/invitation?token=…` exactly once, `EmailRecord` hash
equality with the composed body, provider boundary truthful
(`delivery.status` + `delivered:false`), token binding to recipient and organization,
replay-after-accept 404, token-free listings.

**Inbox delivery: NOT TESTED — BLOCKED.** Prerequisite: an authorized non-production
provider (Resend sandbox key) or an SMTP relay with a certificate-valid STARTTLS
endpoint. A local sink cannot satisfy the app's `starttls()` + `login()` path without
changing production code, and no such change was made to manufacture evidence.

**Browser acceptance journey: NOT TESTED.** `/auth/invitation` is [source]-verified
only; the harness does not drive it.

### 24.6 First-use provenance — decision text for the owner **[executed measurement]**

Unchanged and still BLOCKED. Re-measured this milestone: 26 provisioned placeholders
⇒ `GET /api/v1/objects` 26 rows and `first-object-state.has_business_data = true`
with zero user input; pinned by test.

**D-1 (one choice):** system-provisioned placeholders —
**A)** count as business data and relabel the CTA; **B)** do not count; persist
`provenance` (`user`/`onboarding_seed`/`import`/`ai`) and exclude seeds (recommended);
**C)** stop seeding placeholders entirely.
**D-2 (yes/no):** may AI treat provisioned examples as organizational knowledge?
(Recommend **no** until they contain real content.)
Sub-questions the decision must also settle, per the directive: whether imported /
AI-created / draft / incomplete records count for first-use; how unknown historical
provenance is represented (recommend: leave unknown, never backfill by guess); how
existing users behave after the change (recommend: already-edited seeds become user
data). Full text: `docs/launch/G121_PLACEHOLDER_PROVENANCE_DECISION.md`.

**No implementation was attempted.** Adding a provenance column without D-1 would
be picking option B for the owner.

### 24.7 Journeys, frontend, accessibility **[executed]**

Re-run after the factory change, against the final-tree bundle served explicitly:

| Check | Result |
|---|---|
| Test server boots **without** `.env` (proves the fix in the running app) | HTTP 200, shell references `index-Dlm26ysU.js` |
| axe (WCAG 2.0/2.1 A+AA), 5 surfaces | **0 violations** each |
| Journeys + keyboard 1280×800 / 768×1024 / 375×667 | **36/36 each** (keyboard 21, journey 14, setup 1) |

Frontend sources were not modified in G1.23, so G1.22's vitest (98), TypeScript (0)
and build (0) results still describe the same bytes; the served bundle hash is
unchanged (`index-Dlm26ysU.js`), which is the observable proof of that.

**Superficial-passes check:** the server that booted *without* `.env` is itself
evidence the factory change took effect — a server that still loaded `.env` would
look identical in the harness results, so the boot condition was verified separately
from the journeys.

### 24.8 Full Python suite **[executed]**

`DATABASE_URL=sqlite:///:memory: .venv/bin/python -m pytest -q`, quiet host (no test
server, no PostgreSQL cluster, no browser), exit code written by the run itself.

    5925 passed, 0 failed, 128 skipped, 0 errors, exit 0, 2407.43 s (40:07)
    log: .hermes/cache/scratch/g123/f_fullsuite.log

Reconciliation: 5914 (G1.22) → 5925, i.e. +11 net (14 new isolation tests, minus the
3 assertions that moved into the new predicate table). Skips moved 125 → 128: the
`-q` summary does not itemise them, so this run does **not** attribute each one —
they are environment-gated (PostgreSQL-only, live-network, venv-dependent) and are
not failures. No test was skipped, deleted or weakened by this milestone.

This run followed the factory change, which touches shared application
configuration — hence a full rerun rather than a focused one.

### 24.9 Gate status

| Gate | Status |
|---|---|
| A. Resend key contained / rotated | Containment **PASS**; rotation **BLOCKED** (authorization) |
| B. Historical token / PII / `.env` | **FAIL / OPEN** — decision and rotation are the owner's |
| C. Test isolation root cause | **PASS** — factory no longer reloads `.env` in declared test runs; 14 regression tests |
| D. Invitation delivery | Boundary **PASS**; inbox **BLOCKED**; browser acceptance **NOT TESTED** |
| E. First-use provenance | **BLOCKED** on D-1/D-2 (decision text supplied) |
| F. Journeys / responsive / accessibility | **PASS** for tested journeys |
| G. Launch inventory | **PASS as a document**; verdict `PUBLIC_LAUNCH_READY = FALSE` |
| H. Full Python suite | see 24.8 |
| I. Production verification | **NOT TESTED** — unauthorized |

### 24.10 Cleanup

G1.23 test server `:51999` (PID 236064) stopped by exact PID after identity
re-check; port freed. No PostgreSQL cluster started. Production Gunicorn `:5001` and
PostgreSQL `:5432` untouched. Artifacts under `.hermes/cache/scratch/g123/`
(isolation/delivery logs, axe JSON, three harness logs, suite log, server log). The
G1.22 evidence files remain untouched per §24.2.
## 25. G1.24 — SECURITY, FIRST-USE PROVENANCE & INVITATION LIFECYCLE

**Authority:** G1.24 master + continuation directives. No staging, commit, push,
merge, rebase, history rewrite, credential rotation, evidence deletion, deployment
or production access. Branch and HEAD unchanged. Claims are marked
**[executed]**, **[browser]**, **[source]**, **[inferred]** or **[not tested]**.

### 25.1 Reconciled state

| | Branch | HEAD | Modified | Staged | Untracked |
|---|---|---|---|---|---|
| G1.24 part 1 entry | `feat/commandpalette-ai` | `de9122fc…` | 48 | 0 | 40 |
| Continuation entry | `feat/commandpalette-ai` | `de9122fc…` | 58 | 0 | 47 |
| G1.24 exit | `feat/commandpalette-ai` | `de9122fc…` | 59 | 0 | 47 |

The continuation entry differed from the G1.24 part-1 exit because part 1 added
code before the process stopped; nothing was reset, cleaned or discarded. Alembic
head at entry and exit: `r6b38_object_provenance` (single head). No test server or
PostgreSQL cluster was running at entry; production Gunicorn `:5001` and
PostgreSQL `:5432` were never touched.

### 25.2 Invitation-delivery harness repair

The part-1 run recorded **1 passed, 3 failed** in
`tests/test_g124_invitation_delivery_smtp.py`. All three were harness defects; the
captured traffic already showed the product path working (TLS, AUTH, correct
recipient). Fixed in the harness only — no product behaviour was weakened:

| Defect | Fix |
|---|---|
| Message-count assertion saw 2 messages | filter by envelope recipient (`_messages_to`); the signup verification email is a different message for a different address, and the count is still asserted **exactly** (1) |
| Body searched on raw MIME (base64) | decode with `email.message_from_string(..., policy=default)` and assert on the decoded `text/plain` part; production sending unchanged |
| Team route has no `token` field | parse the token from the returned `invite_url`, prove it points at the persisted invitation, and prove the emailed link carries the same capability |

Additional assertion added: the invitation token must not appear in any other
captured message.

**Focused result [executed]:** `4 passed, 0 failed, exit 0`
(`pytest tests/test_g124_invitation_delivery_smtp.py -q`, 7.59 s). The earlier
`1 passed / 3 failed` remains the historical record of the first attempt.

**Self-audit finding:** the first axe evidence artifact stored the invitation
surface URL including its query string, i.e. a live (disposable) capability token
in a JSON artifact. Fixed in the harness (`safeUrl` redacts `token=`), and the
artifact was regenerated. No token is printed by any harness; the app's own Flask
access log does log invitation URLs (token in path), which is recorded as a
residual risk rather than a milestone defect.

### 25.3 Invitation lifecycle — browser journey [browser]

`frontend/tests/invitation-journey.cjs`, run against an isolated app
(`scripts/test_server.py`, SQLite file DB, `:51997`) with the local STARTTLS
capture sink, and the **final-tree bundle** (`index-DCEl80dm.js`, served via
`SHUNYA_FRONTEND_DIST=frontend/dist`):

| Viewport | journey | keyboard | total |
|---|---|---|---|
| 1280×800 | 24/24 | 4/4 | **28/28** |
| 768×1024 | 24/24 | 4/4 | **28/28** |
| 375×667 | 24/24 | 4/4 | **28/28** |

What the journey proves, end to end: administrator signs in by keyboard → creates
an invitation through the real route → response reports `accepted:true,
delivered:false` → the message is captured over STARTTLS with AUTH → the harness
decodes MIME → exactly one accept link, same capability the admin received →
recipient opens the page in a clean session, sees the organization and their own
address → client-side password-mismatch error writes nothing (invitation still
pending) → acceptance succeeds → invited identity signs in → reads the authorized
workspace (`organization_id` matches) → a plain member gets 403 on invitation
listing → replay shows "Invitation has already been accepted" and no form →
non-member cross-tenant list/create both 403 → token bound to recipient and
organization, unknown token 404 → no application-origin 5xx, no horizontal
overflow.

**Not claimed:** external inbox delivery. The capture sink is loopback; it proves
the send path and the message, not that a third-party inbox received anything.

### 25.4 Truthfulness fixes found by the journey

1. **`delivered` was set from provider acceptance.** Both invitation routes
   reported `delivered = (status == "accepted")`, collapsing acceptance into
   delivery — contradicting the project's own vocabulary
   (`tests/test_email_config.py`: ACCEPTED ≠ DELIVERED). Both now return
   `accepted` and a permanent `delivered:false`.
2. **The UI path reported nothing.** `/api/v1/team/invite` returned the invitation
   only, so the team page said "Sending…" and closed. It now reports the delivery
   outcome and returns `invite_url`, and the page distinguishes acceptance from
   delivery and offers the link when the email did not leave.
3. **Replay showed "Not found".** The specific 404 reason was in `detail` but the
   page rendered `error`. It now prefers the detail: "Invitation has already been
   accepted."

### 25.5 First-use provenance — independent verification

Implementation is described in `docs/launch/G121_PLACEHOLDER_PROVENANCE_DECISION.md`
§8 (owner decision D-1 = B, D-2 = No). This section records **verification**, not
the design.

| Claim | Evidence |
|---|---|
| Examples are persisted as `onboarding_seed` | [executed] read-only SQLite probe of the disposable server DB: 26 rows, all `onboarding_seed`, all with the empty-content template, all with an organization, 0 orphaned |
| New user object → `user`; import → `import`; AI → `ai`; system → `system` | [executed] pytest (ObjectService defaults + explicit values) |
| Invalid vocabulary rejected | [executed] pytest (`InvalidProvenanceError`) |
| Unknown history stays unknown, no backfill | [executed] disposable PostgreSQL: a row written before the column survives with `provenance = NULL` and counts as business data |
| Editing an example promotes it to `user` | [executed] pytest (data edit → `user`; archive does not) |
| Lifecycle-only writes do not change provenance | [executed] pytest |
| First-use false with only examples, true after a real record | [executed] pytest ×3 paths + [browser] home CTA visible with 26 examples and `has_business_data=false` |
| Example count still available | [executed] `counts.examples = 26` in the predicate response |
| API surfaces agree (list / detail / create) | [executed] pytest `TestApiSurfacesAgree` |
| Frontend distinguishes examples | [browser] 26 "Example" badges, "These are examples" banner, detail note |
| Tenant isolation of the predicate | [executed] pytest (another org's examples irrelevant; unknown org fails closed) |

**Migration [executed]** on a disposable PostgreSQL 16 cluster
(`/tmp/g124_pg`, port 55432; production 5432 never contacted): upgrade from zero to
`r6b37` → legacy row inserted → `upgrade head` → column `varchar(32)`, nullable, no
default; legacy row intact with NULL; grounding predicate counts it and excludes a
seed row; repeat upgrade no-op; `downgrade -1` → `upgrade head` symmetric (the
downgrade is value-lossy by definition). Cluster stopped afterwards; data dir
preserved. Details in `docs/launch/G122_DATABASE_INTEGRITY_EVIDENCE.md` §5.

### 25.6 AI grounding (D-2 = No) [executed]

`core/intelligence/service.py` excludes `onboarding_seed` from the counts it hands
the model as a fact, names the excluded examples in the description, and labels a
placeholder the user is viewing as `[example]` ("NOT organizational data") instead
of `company_data`. Tests assert both the counts and the context classification, and
that a real object is still `company_data`.

Verified with the **local** provider only. Real external model behaviour remains
**not tested**.

### 25.7 Frontend, responsive, keyboard, accessibility

| Check | Result |
|---|---|
| `tsc -b --noEmit` (inside `npm run build`) | exit 0 |
| `vitest run` | 12 files / 98 tests passed, exit 0 |
| `npm run build` | exit 0, `index-DCEl80dm.js` |
| First-use UI harness, 3 viewports | 9/9 each (banner, 26 badges, CTA, no 5xx, no overflow) |
| axe WCAG 2.0/2.1 A+AA, 4 surfaces | 0 violations each, **with content preconditions** so an unrendered shell cannot pass silently |

**Defect found and fixed by the scan:** the knowledge browser's type-filter chips
were clickable `div`s inside a horizontally scrollable strip
(`scrollable-region-focusable`, WCAG 2.1.1) and were not keyboard reachable. They
are now real `button` elements with `aria-pressed`. Re-scan: 0 violations.

Manual assistive-technology testing remains **outstanding**; automated scans are
not a conformance claim.

### 25.8 Security incidents — status unchanged

No credential was opened, printed, copied, tested, transmitted, rotated or
deleted; no evidence was removed; no history was rewritten. The Resend key remains
**exposed until the owner rotates it**; the Telegram token, the founder PII and the
`.env` blobs remain separate, open history incidents. Repository access restriction
(owner decision: Option A first) was recorded and **not executed** — it requires the
repository owner. Exact owner actions are in
`docs/launch/G122_SECURITY_REMEDIATION_PLAN.md` (G1.24 status section).

Structural preventions verified this milestone [executed]: the test predicate now
honours `SHUNYA_ENVIRONMENT` (the same variable the SECRET_KEY guard reads),
`migrations/env.py` refuses to reload `.env` in a declared test run, the factory
refuses a live external mail transport, and the test server scrubs credentials
unless the sink is loopback. 32 isolation tests.

### 25.9 Database integrity decision

One nullable column, no constraint, no index, no backfill. Rationale and rejected
alternatives: `G122_DATABASE_INTEGRITY_EVIDENCE.md` §5. No deferred G1.21/G1.22
item was revisited — none acquired new evidence.

### 25.10 Full Python suite [executed]

    DATABASE_URL=sqlite:///:memory: .venv/bin/python -m pytest -q
    exit 0
    5967 passed, 128 skipped, 0 failed, 0 errors, 2050.40 s (34:10)
    log: .hermes/cache/scratch/g124/fullsuite.log

Reconciliation against G1.23 (5925 passed / 128 skipped): **+42 net**, fully
accounted for — 20 `test_g124_provenance`, 4
`test_g124_invitation_delivery_smtp`, 18 additional isolation tests in
`test_g123_test_env_isolation` (14 → 32). Skips unchanged at 128.

**Disclosure:** three assertions (`TestApiSurfacesAgree`) were added to
`test_g124_provenance.py` *after* this run started, so the suite did not execute
them. They are covered by the focused run below on the final tree; no production
code changed between the two runs.

### 25.11 Focused suites on the final tree [executed]

    pytest tests/test_g124_provenance.py tests/test_g124_invitation_delivery_smtp.py \
           tests/test_g123_test_env_isolation.py tests/test_first_object_state.py \
           tests/test_g121_onboarding_journey.py -q
    exit 0 — 78 passed
    (23 / 4 / 32 / 15 / 4 respectively)

### 25.12 Gate status

| Gate | Status |
|---|---|
| A. Resend key contained / rotated | containment **PASS**; rotation **BLOCKED (authorization)** |
| B. Historical token / PII / `.env` | **OPEN** — owner decision recorded (Option A first), not executed |
| C. Test isolation | **PASS** — factory + alembic + test-server guards, 32 tests |
| D. Invitation local delivery + lifecycle | **PASS** — 4/4 focused, 28/28 × 3 viewports |
| D'. External inbox delivery | **BLOCKED (authorization)** — needs an approved non-production provider |
| E. First-use provenance (D-1 = B) | **PASS** — pytest + disposable PostgreSQL + browser + direct DB probe |
| F. AI grounding (D-2 = No) | **PASS with local provider**; real provider **NOT TESTED** |
| G. Journeys / responsive / keyboard | **PASS** for the tested surfaces |
| H. Automated accessibility | **PASS (automated only)**; manual AT **NOT TESTED** |
| I. Database migration | **PASS** on disposable PostgreSQL |
| J. Full Python suite | **PASS** — 5967 / 128 / 0 |
| K. Frontend build / unit | **PASS** — tsc 0, vitest 98, build 0 |
| L. Production verification | **NOT TESTED** — unauthorized |

```
PUBLIC_LAUNCH_READY = FALSE
STAGING_AUTHORIZED = NONE        COMMIT_AUTHORIZED = NONE
PUSH_AUTHORIZED = NONE           MERGE_AUTHORIZED = NONE
HISTORY_REWRITE_AUTHORIZED = NONE
CREDENTIAL_ROTATION_AUTHORIZED = NONE
EVIDENCE_DELETION_AUTHORIZED = NONE
PRODUCTION_MUTATION_AUTHORIZED = NONE
DEPLOYMENT_AUTHORIZED = NONE
```

### 25.13 Cleanup and preserved state

Test server (`:51997`) and the capture sink (`:2525`) were stopped by their exact
tracked sessions after the journeys; both ports are free. The disposable
PostgreSQL cluster was stopped and its data directory preserved at
`/tmp/g124_pg`. The disposable server databases
(`/tmp/shunya_test_server_g124*.sqlite`) were **not deleted**: ownership was
verified (`fuser` → the single test-server PID; command line carrying
`SHUNYA_TEST_SERVER_ALLOWED=true` and the test path), and a fresh uniquely named
database was used per run instead of deleting state. Production Gunicorn and
PostgreSQL were never touched. Artifacts under
`.hermes/cache/scratch/g124/` (suite log, journey/first-use logs + JSON, axe JSON,
captured messages, probes).

---

## 26. G1.25 — FINAL LAUNCH-BLOCKER PASS: RECONCILIATION, TRUTHFULNESS, DELIVERABILITY

**Authority:** G1.25 master directive. No staging, commit, push, merge, rebase,
history rewrite, credential rotation, evidence deletion, deployment or production
mutation. All gates remain NONE. Claims are marked **[executed]**, **[browser]**,
**[source]**, **[inferred]** or **[not tested]**.

### 26.1 The finding that reclassifies the whole ledger

| | Branch | HEAD | Modified | Stage | Untracked |
|---|---|---|---|---|---|
| G1.25 entry & exit | `feat/commandpalette-ai` | `de9122fc…` | 59 | 0 | 47 |

**None of the artifacts this ledger certifies exist at HEAD.** Verified, not
inferred: `git cat-file -e HEAD:app/objects/provenance.py` → absent;
`git ls-tree -r HEAD migrations/versions` → no `r6b30`…`r6b38`;
`HEAD:tests/test_g123_test_env_isolation.py` → absent;
`HEAD:docs/launch/SHUNYA_COMPLETION_LEDGER.md` → absent.

Consequences, stated plainly:

* Every "PASS" in §§14–25 describes a **working tree**, not a repository state.
  This ledger has been the only record of that work — and it is itself untracked.
* Production gunicorn (:5001, uptime ≈ 50 000 s) runs **from this tree**, so the
  code serving users is not the code its reported commit contains: `/health`
  returns `status=degraded`, `release_type=UNVERIFIED`,
  `build_identity_matches_running_build=false`, `git_commit=de9122f`,
  `backend_release_sha=31a67de` **[executed]**.
* The deploy pre-flight refuses a dirty tree, so this state cannot be deployed;
  and a `git reset --hard` to the reported HEAD would destroy the migrations,
  guards and fixes. The window is live, not theoretical.
* Until this work is committed and CI certifies a real SHA, **no capability gate
  in this document can be closed**, regardless of its local evidence.

### 26.2 Security incidents — scope expanded, nothing remediated

`docs/launch/G125_SECURITY_REMEDIATION_ADDENDUM.md` records the owner sequences.
New, previously unrecorded facts (metadata only — no secret value was read,
printed, hashed for publication, tested or transmitted):

| Finding | Evidence |
|---|---|
| Repository is **PUBLIC** — the G1.24 "Option A: restrict access" decision was never executed | `gh repo view --json visibility` |
| GitHub secret scanning: **OPEN** alert #1 `telegram_bot_token`, created 2026-07-31, `resolution=null` | secret-scanning alerts API (value field never selected) |
| Security settings: scanning **on**, push protection **on**, validity checks **off**, custom patterns **off**, Dependabot security updates **off** | `--jq .security_and_analysis` |
| **A second unredacted suite log** holds 1 key-shaped token (`g123/f_fullsuite.log`); the g122 original holds 3 occurrences / 2 distinct | `grep -oE … \| wc -l` (counts only) |
| Those logs are `0664` inside `0775` directories | `ls -ld`, `ls -l` |
| `~/.env` from the G1.22 plan does not exist; the live file is `<repo>/.env`, `0600` | `ls -l` |

Prepared but **not executed**: the `chmod 700/600` restriction commands. Evidence
handling is gated by the incident procedure and this milestone holds no
authorization for it.

### 26.3 Test-environment isolation — PASS (re-verified)

32 isolation tests passed **[executed]**, covering: the declared-environment
predicate (`SHUNYA_ENVIRONMENT` → `SHUNYA_ENV` → `FLASK_ENV`, explicit name beats
an inherited pytest marker); the factory never calling `load_dotenv` in a declared
test run, repeatedly; a non-test process still loading it; a synthetic canary not
reaching `email_core`; the transport guard refusing Resend-with-key / external
SMTP / unknown providers; subprocess inheritance; and `migrations/env.py` guarding
its single `load_dotenv` call. Focused security/isolation group: **122 passed**.

### 26.4 Defects found and fixed this milestone

| Defect | Fix | Proof |
|---|---|---|
| 11 of 12 command-palette actions dispatched `shunya:action` with **no listener** | `PaletteActionsBridge` in `app.tsx` → `useWorkspaceStore.open`; palette rebuilt to list only surfaces with a render branch | [browser] *Work* → Commitments rendered; direct dispatch → Commitments rendered |
| "Live · updated …" and "Everything is calm." survived a failed poll | footer distinguishes "Not live — last successful update …"; failure state gets its own sentence | [source] + build |
| Fabricated `progress: 0.3` bar for in-flight work | numeric claim and track removed; completion still sets 1.0 | [source] |
| Export panel "Export" downloaded nothing | real JSON download from the returned records | [source] |
| Signup treated `logged` (not sent) as delivered | only `accepted`/`sent` claim "check your email"; resend inspects the response | [source] |
| Forgot-password / Create-account / intro unreachable by keyboard | real link/button; intro is a focusable button | [source] |
| OAuth buttons stranded the user on a JSON 501 | probe-then-navigate with an inline message | [source] |
| MFA claimed "account is protected" while sign-in never challenges | copy now states the truth | [source] |
| Password reset reported "link sent" while discarding the send result | 503 `delivery: unconfigured` when no transport; failure logged; new test + `mail_configured` fixture | [executed] auth 18 passed |
| Search failure collapsed into `200 success:true data:[]` | 503 `degraded`; genuine empty stays 200 | [executed] reliability 151 passed |
| Export job thread had no application context (every job failed) | app object passed and `app_context()` entered | [source] |
| `zip` format advertised, never produced, served as `application/zip` | removed from `FORMATS`; mime map simplified | [source] |
| Alert cooldown compared `last_seen` after setting it to `now` (never re-fired) | reference is now `delivered_at` | [source] |

### 26.5 Verification on the final tree

| Check | Result |
|---|---|
| Full Python suite `DATABASE_URL=sqlite:///:memory: pytest -q` | **5970 passed, 128 skipped, 0 failed, 0 errors**, exit 0, 31:14 (log `g125/fullsuite.log`) — +3 vs G1.24 = the three `TestApiSurfacesAgree` assertions that post-dated that run |
| Focused after the edits | auth **18**; reliability/export/search/alerting **151**; security/isolation **122**; provenance/invitation/onboarding **60** → **351 passed, exit 0** |
| Disposable PostgreSQL 16 :55432 (5432 never contacted) | `r6b37` → legacy row → `head` `r6b38`: `varchar(32)`, nullable, no default; legacy `NULL` preserved; seed excluded from grounding and counted as example; 188 tables; repeat upgrade no-op; `downgrade -1` → `upgrade head` symmetric |
| Frontend | `tsc -b --noEmit` 0 errors; vitest 12 files / **98 passed**; `npm run build` exit 0 (`index-rbrSIPha.js`) |
| Invitation lifecycle, 3 viewports | **28/28 each** (journey 24, keyboard 4) |
| First-use UI, 3 viewports | **9/9 each** |
| Keyboard + first-object, 3 viewports | **36/36 each** |
| axe WCAG 2.0/2.1 A+AA, 4 surfaces | **0 violations each** — automated only, no conformance claim |
| Web-search provider (real call) | 3/3 results with URLs and bodies from this host |

**Disclosure — harness contamination.** The first invitation run resolved
`SHUNYA_BASE_URL` from `.env`, so the emailed accept link pointed at
`127.0.0.1:5001` and the harness issued **one read-only `GET /auth/invitation`**
against the production listener (SPA shell; no state change, no data read). The
run was discarded and re-executed with `SHUNYA_BASE_URL=http://127.0.0.1:51997`;
every result quoted above is from the corrected run. This is recorded, not
minimised.

**Disclosure — suite timing.** The 5970-pass run predates the backend edits in
26.4. The delta is covered only by the 351 focused passes; a second full-suite run
on the final tree was not executed. Signup/panel/palette edits are frontend-only
and are covered by tsc, vitest, the build and the browser journeys.

**Disclosure — probe limits.** The multi-command palette probe could not re-open
the palette for a second command. That is recorded as a harness finding; no
product change was made on the strength of it, and the single-command plus
direct-dispatch proofs stand on their own.

### 26.6 Still open (unchanged or newly classified)

1. **Uncommitted work / uncertified running build** — blocks every gate.
2. **Resend key exposed in two unredacted logs**; **Telegram token with an open platform alert on a public repository**; visibility still PUBLIC.
3. **Invitation external inbox delivery** — BLOCKED (authorization): needs an approved non-production provider.
4. **MFA** — advertised, not enforced; `/mfa/challenge` authenticates on a TOTP alone with no rate limit; recovery code disables MFA.
5. **Gmail** — unreachable UI, placeholder client id, OAuth tokens discarded outside `TESTING`, ingest constructs an unconnected adapter and reports `ok`.
6. **Telegram** — public webhook without secret-token validation; the "reply" is returned in the HTTP body and never sent.
7. **Backup/restore** — pre-deploy dump only; no scheduler, retention, or restore drill (needs authorization).
8. **Alerting** — no `ALERT_EMAIL`, no consumer, no UI; recovery detection is per-process.
9. **No rate limiting** on `/api/v1/search`, `/api/v1/ai/chat`, `/mfa/*`.
10. **`/metrics` JSON fallback hardcodes `shunya_db_up: 1`**; `sentry-sdk` never initialised.
11. **AI answers grounded in web results carry no source labelling** on the reachable surface.
12. **Real AI providers, production verification** — NOT TESTED / unauthorized.

### 26.7 Gate status

| Gate | Status |
|---|---|
| A. Resend key rotated | **BLOCKED (authorization)** — exposure scope now 2 logs |
| B. Historical token / PII / `.env` | **OPEN** — repository still PUBLIC; platform alert open |
| C. Test isolation | **PASS** |
| D. Invitation local delivery + lifecycle | **PASS** (28/28 ×3) |
| D′. External inbox delivery | **BLOCKED (authorization)** |
| E. First-use provenance | **PASS** (pytest + PG + browser) |
| F. AI grounding | **PASS with local provider**; real provider **NOT TESTED** |
| G. Journeys / responsive / keyboard | **PASS** for tested surfaces |
| H. Automated accessibility | **PASS (automated only)**; manual AT **NOT TESTED** |
| I. Migration | **PASS** (disposable PG) |
| J. Full Python suite | **PASS** — 5970 / 128 / 0 (pre-edit tree; delta focused) |
| K. Frontend build / unit | **PASS** |
| L. Production verification | **NOT TESTED** — unauthorized |
| M. Repository / commit integrity | **FAIL** — certified work is uncommitted; running build uncertified |

```
PUBLIC_LAUNCH_READY = FALSE
STAGING_AUTHORIZED = NONE        COMMIT_AUTHORIZED = NONE
PUSH_AUTHORIZED = NONE           MERGE_AUTHORIZED = NONE
HISTORY_REWRITE_AUTHORIZED = NONE
CREDENTIAL_ROTATION_AUTHORIZED = NONE
EVIDENCE_DELETION_AUTHORIZED = NONE
PRODUCTION_MUTATION_AUTHORIZED = NONE
DEPLOYMENT_AUTHORIZED = NONE
```

### 26.8 Artifacts

`.hermes/cache/scratch/g125/` — full suite log, focused logs (auth, reliability,
security, journeys), PG upgrade/downgrade logs, legacy-row and verification
scripts, vitest and build logs, journey/first-use/axe/kb logs and JSON, palette
probes, `invitation_messages.jsonl`. Nothing deleted; no credential value in any
artifact.
