# G1.22 — Public-Launch Readiness Matrix

**Question this answers:** for each advertised capability, what is actually proven,
what is not, and what blocks a public launch.

Evidence classes: **[executed]** = a real run was observed in this environment;
**[source]** = read in code, not exercised; **[inferred]** = reasoned from executed
results elsewhere; **[not tested]** = no evidence.

Every row is a *local, isolated-environment* result. Nothing here is production
evidence: no deployment, no production database access, and no external customer
data were involved (deployment unauthorized).

---

## A. Authentication & identity

| Capability | Status | Evidence |
|---|---|---|
| Signup (JSON API) | Implemented + verified | [executed] tests + PostgreSQL journey (201, canonical `sid_…`) |
| Email verification | Implemented + verified | [executed] token from the DB (the established test mechanism) → 200 |
| Login / session | Implemented + verified | [executed] 200, session `identity_id` = canonical id |
| Logout | Implemented + verified | [executed] GET `/logout` (POST is 405 — method is GET by design) |
| Duplicate-email protection | Implemented + verified | [executed] 409 at signup; unique index `ix_team_members_email` |
| Password reset / MFA | Implemented, **not verified** | [source] routes and `shunya_mfa_configs` exist; no G1.21/G1.22 journey |

## B. Authorization & tenant isolation

| Capability | Status | Evidence |
|---|---|---|
| Organization membership gate | Implemented + verified | [executed] non-member 403 on invitations; ambiguity → truthful 403 with a machine-readable code |
| Cross-tenant object access | Blocked + verified | [executed] detail 404 and listing isolation on PostgreSQL |
| Invitation administration | Implemented + verified | [executed] owner/admin only; tokens not re-broadcast; non-member cannot list/invite/revoke |
| Workspace membership on join | Implemented + verified | [executed] acceptance grants the org's workspaces, non-elevating role map |
| Role vocabulary normalization | Implemented + verified | [executed] `tests/test_role_normalization.py` |

## C. Business-object lifecycle & persistence

| Capability | Status | Evidence |
|---|---|---|
| Create / list / detail | Implemented + verified | [executed] API + raw SQL row with correct org **and** workspace |
| Empty/first-use state | Implemented; **semantics BLOCKED** | [executed] predicate answers truthfully about *rows*, but provisioned placeholders are counted as business data — owner decisions D-1/D-2 |
| Import (CSV) + error recovery | Implemented + verified | [executed] keyboard/journey harness (14 journey checks × 3 viewports) |
| Soft delete / archive | Implemented | [source] `is_deleted`, lifecycle route; not part of the verified journey |

## D. AI capabilities

| Capability | Status | Evidence |
|---|---|---|
| Chat surface + persistence | Implemented; verified only with the **local** provider | [executed] tests run with `SHUNYA_AI_PROVIDERS=local` (deterministic, no network) |
| Real external model providers | **Not tested** | [source] routing exists; no authorized provider call in this environment |
| Truthful capability disclosure | **Not verified** | [inferred] cannot be asserted without exercising real providers |
| AI grounding over provisioned examples | **Blocked** | depends on D-2 (may AI treat examples as organizational facts?) |

## E. Search & internet retrieval

| Capability | Status | Evidence |
|---|---|---|
| DuckDuckGo-backed retrieval | Implemented; **not tested** | [source] live-network tests are skipped unless `SHUNYA_LIVE_NET_TEST=1`; no network authorization here |

## F. Integrations & external providers

| Capability | Status | Evidence |
|---|---|---|
| Email delivery (Resend/SMTP) | Implemented; **inbox delivery not tested** | [executed] message composed for the right recipient with the accept URL; provider boundary reached; no authorized provider in test config — see §G2 |
| Gmail integration | Registered, **not verified** | [source] `Integration registered: email (Gmail)`; no OAuth journey run |
| Telegram bot | Implemented; **not tested** | [source] webhook route exists; token incident open (INC-1) |

## G. Onboarding, invitations, delivery

| Capability | Status | Evidence |
|---|---|---|
| Onboarding step progress + resume | Implemented + verified | [executed] survives losing process memory, re-login, and a fresh PostgreSQL connection |
| Questionnaire answers + resume | Implemented + verified | [executed] `onboarding_sessions` row, resume at `industry` |
| Completion seeding + idempotency | Implemented + verified | [executed] 26 then 0, no duplicates |
| Invitation create/accept/login/access | Implemented + verified | [executed] 8 application tests + delivery-boundary tests |
| Invitation **inbox delivery** | **Not tested** | no authorized non-production provider; the API now reports `delivery.status` / `delivered:false` truthfully instead of implying delivery |
| Invitation acceptance **UI** | **Not tested** | the SPA route `/auth/invitation` is [source]-verified only; the browser harness does not drive it |

## H. UI, responsive, keyboard, accessibility

| Capability | Status | Evidence |
|---|---|---|
| Unit tests | Verified | [executed] 12 files / 98 tests, exit 0 |
| TypeScript / build | Verified | [executed] `tsc -b --noEmit` exit 0; `vite build` exit 0, `index-Dlm26ysU.js` |
| Journeys + keyboard at 1280×800 / 768×1024 / 375×667 | Verified | [executed] 36/36 each (keyboard 21, journey 14, setup 1) |
| Automated accessibility (5 surfaces) | Verified, 0 violations | [executed] axe WCAG 2.0/2.1 A+AA; **not** a conformance claim |
| Manual assistive-tech testing | **Not tested** | no screen-reader run in this environment |

## I. Database, migration, backup

| Capability | Status | Evidence |
|---|---|---|
| Migration chain from zero | Verified | [executed] head `r6b37_onboarding_sessions`, exit 0, 188 tables |
| Idempotent re-run / reversible constraint revision | Verified | [executed] repeat upgrade no-op; downgrade/upgrade symmetric |
| Schema-constraint parity (in-scope) | Verified | [executed] 0 blockers; 7 FKs deliberately deferred with reasons |
| Backup / restore drill | **Not tested** | no authorization to touch backup infrastructure |

## J. Observability & operations

| Capability | Status | Evidence |
|---|---|---|
| Health endpoint | Implemented; reports **degraded** locally | [executed] `GET /health` → 503 with `release_type: UNVERIFIED`, `frontend_release_matches_backend: false` — the release-evidence gate working as designed against a local build, not a product failure |
| Structured logs + redaction | Implemented + verified | [executed] token bodies no longer logged; `tests/test_log_secret_redaction.py` |
| Alert engine | Implemented | [source] `sh_alert_events`; fired during fault injection without breaking the request |
| `/metrics` | Implemented, token-gated | [source] verified in earlier milestones; not re-run here |

## K. Security posture

| Item | Status |
|---|---|
| Historical token in Git history (INC-1) | **OPEN** — rotation + history decision required |
| Founder PII in history (INC-2) | **OPEN** — owner decision |
| `.env` history (INC-3) | LOW, placeholder-era; remains in history |
| Tests reaching a live email provider (INC-4) | **CONTAINED** + regression-tested in G1.22 |
| Current tree contains no tracked secret | [executed] |

## L. Production readiness

| Item | Status |
|---|---|
| Production deployment | **NOT TESTED** — unauthorized |
| Production configuration review | **NOT TESTED** |
| Production data integrity | **NOT TESTED** |

---

## Verdict

**PUBLIC_LAUNCH_READY = FALSE.**

Blocking, in order of severity:

1. **INC-1 credential rotation** — one Telegram bot token may still be live; it is
   in public history. Owner action, minutes to perform.
2. **First-use semantics (D-1/D-2)** — the product currently reports business data
   exists before the user has entered any, and AI can ground on placeholder
   examples. Owner decision required; implementation follows immediately.
3. **Invitation inbox delivery** — an invited person cannot receive their link in
   this environment; needs an authorized non-production provider to verify.
4. **Production verification** — no deployment or production-data evidence exists,
   and none is authorized.
5. **Real AI provider behaviour** — unverified; do not advertise model-backed
   answers as certified.

Everything in sections A–I except the named gaps is verified locally and repeatable
from the documented commands.

---

# G1.24 — capability inventory (continuation)

Evidence classes: **[executed]** real run observed in this environment;
**[browser]** observed in a real browser journey; **[source]** read, not exercised;
**[inferred]** reasoned from executed results; **[not tested]** no evidence.

Every row is local and isolated. No production system was accessed.

| Capability | Classification | Evidence |
|---|---|---|
| Secrets: no live credential literal in the tracked tree | IMPLEMENTED AND VERIFIED | [executed] shape-only scan of tracked files: 0 standalone `re_`-shaped literals (17 matches inside vendored identifiers), 0 bot-token-shaped literals |
| Secrets: test/CI processes cannot inherit production mail credentials | IMPLEMENTED AND VERIFIED | [executed] 32 isolation tests; factory refuses a live transport; alembic honours the same predicate ([source] for the alembic branch) |
| Secrets: exposed Resend key rotated | BLOCKED ON AUTHORIZATION | [executed metadata] still exposed; owner sequence recorded |
| Secrets: Telegram token rotation | BLOCKED ON AUTHORIZATION | [source] validity unknown, never tested |
| Secrets: historical PII / `.env` / token in Git history | BLOCKED ON OWNER DECISION | [source+prior evidence] Option A (access restriction) chosen, not executed; clones/forks unaffected |
| Authentication: signup, verify, login, logout, session | IMPLEMENTED AND VERIFIED | [executed] pytest + [browser] keyboard-only login in every journey |
| Authentication: password reset, MFA | IMPLEMENTED BUT INCOMPLETELY VERIFIED | [source] routes exist; no G1.24 journey |
| Authorization: org membership gate, role gate | IMPLEMENTED AND VERIFIED | [browser] member 403 on invitation listing; owner/admin 201 |
| Tenant isolation: invitations across tenants | IMPLEMENTED AND VERIFIED | [browser] non-member list/create → 403; [executed] pytest |
| Tenant isolation: objects/workspaces | IMPLEMENTED AND VERIFIED | [executed] G1.21–G1.24 suites |
| First-use semantics (examples ≠ business data) | IMPLEMENTED AND VERIFIED | [executed] pytest + disposable PostgreSQL + [browser] CTA visible with 26 examples and `has_business_data=false` |
| First-use UX (examples labelled, useful, not hidden) | IMPLEMENTED AND VERIFIED | [browser] 26 "Example" badges, banner, 3 viewports |
| AI grounding excludes provisioned examples | IMPLEMENTED AND VERIFIED (local provider) | [executed] counts/context tests; real external model **not tested** |
| AI real-provider behaviour | NOT TESTED | [source] routing exists; no authorized provider call |
| Advertised internet search | NOT TESTED | [source] live-network tests gated by `SHUNYA_LIVE_NET_TEST` |
| Invitation creation → message composition → local capture | IMPLEMENTED AND VERIFIED | [browser] captured over STARTTLS+AUTH, MIME-decoded, one accept URL |
| Invitation acceptance → membership → login → workspace access | IMPLEMENTED AND VERIFIED | [browser] 28/28 at 1280×800, 768×1024, 375×667 |
| Invitation replay / expiry / unknown token | IMPLEMENTED AND VERIFIED | [browser] 404 + "already been accepted"; [executed] pytest |
| Invitation external inbox delivery | BLOCKED ON AUTHORIZATION | [not tested] needs an approved non-production provider |
| Import (CSV) with validation and recovery | IMPLEMENTED AND VERIFIED | [browser] prior harness (14 journey checks × 3 viewports) |
| Export | IMPLEMENTED, INCOMPLETELY VERIFIED | [source] surface exists; not re-run in G1.24 |
| External integrations (Gmail, Telegram) | NOT TESTED | [source] registered; no OAuth/webhook journey |
| Responsive UI (invitation + first-use surfaces) | IMPLEMENTED AND VERIFIED | [browser] no horizontal overflow at 3 viewports |
| Keyboard-only critical paths | IMPLEMENTED AND VERIFIED | [browser] 4 keyboard checks per viewport + prior 21-check harness |
| Automated accessibility (changed surfaces) | IMPLEMENTED AND VERIFIED (automated only) | [executed] axe WCAG 2.0/2.1 A+AA: 0 violations on 4 surfaces with content preconditions |
| Manual assistive-technology testing | NOT TESTED | no screen-reader run available |
| Logging and secret redaction | IMPLEMENTED AND VERIFIED | [executed] redaction tests; bodies never logged |
| Observability: `/health`, `/metrics`, alert engine | IMPLEMENTED, INCOMPLETELY VERIFIED | [source] token-gated metrics; local health reports degraded by design |
| Database migrations (incl. `r6b38`) | IMPLEMENTED AND VERIFIED | [executed] disposable PostgreSQL 16: upgrade/downgrade/idempotency + legacy-row compatibility |
| Backup / restore drill | NOT TESTED | no authorization to touch backup infrastructure |
| Production deployment / production data / production verification | BLOCKED ON AUTHORIZATION | [not tested] not accessed |

**What the local result does not mean.** External inbox delivery, real model
behaviour, third-party integrations, backup recovery and production readiness have
no evidence. A green local suite is not a launch certificate.

---

# G1.25 — closure pass: reconciliation, truthfulness fixes, and a deliverability finding

Evidence classes unchanged: **[executed]**, **[browser]**, **[source]**,
**[inferred]**, **[not tested]**. Nothing here is production evidence.

## Z. The reconciliation finding that outranks every row below

| Check | Result |
|---|---|
| Branch / HEAD | `feat/commandpalette-ai` / `de9122fc…` **[executed]** |
| Working tree | 59 modified / 47 untracked, 0 staged **[executed]** |
| G1.21–G1.24 artifacts at HEAD | **absent** — `app/objects/provenance.py`, `migrations/versions/r6b30…r6b38`, `tests/test_g123_test_env_isolation.py`, `docs/launch/SHUNYA_COMPLETION_LEDGER.md` all fail `git cat-file -e HEAD:<path>` **[executed]** |
| Live `/health` | `status=degraded`, `release_type=UNVERIFIED`, `build_identity_matches_running_build=false` **[executed]** |

**Status: BLOCKED.** Every "IMPLEMENTED AND VERIFIED" row in this matrix describes
a working tree that no commit contains. The certified migrations, guards and
evidence documents exist only as local files; production is running code its own
reported commit does not contain. A deploy cannot proceed from this tree
(`deploy_preflight.sh` refuses a dirty tree) and a `git reset --hard` would erase
the entire body of work. No gate can be closed until this work is committed and
certified by CI on a real SHA.

## AA. Capability deltas found by this pass

| Capability | Status | Evidence |
|---|---|---|
| Command palette navigation commands | **WAS DEAD, NOW IMPLEMENTED AND VERIFIED (browser)** | [browser] before: `shunya:action` had no listener (2 matches, both in the palette) → 11 of 12 commands did nothing. [browser] after: clicking *Work* renders the Commitments surface; a direct dispatch renders it too. Removing/adding commands is recorded in `command-palette.tsx`. |
| Multi-command palette sequence | **INCOMPLETELY VERIFIED** | The probe could not re-open the palette for a second command; that is a harness finding, not yet a product one — **unconfirmed**, do not fix blind. |
| Password reset when mail is unconfigured | **FIXED + TESTED** | [executed] now 503 with `delivery: unconfigured` (was: 200 "link has been sent" with the send result discarded); new test + documented `mail_configured` fixture for the token-lifecycle tests. |
| Web search provider failure | **FIXED + TESTED** | [executed] route returns 503 `degraded` instead of `200 success:false data:[]`; a genuine empty result stays 200. Provider itself returns real results from this host ([executed] 3/3 with URLs). |
| AI answers grounded in web results | **PARTIAL — untruthful labelling** | [source] `/api/v1/ai/chat` injects DDG snippets but returns no sources field; the banner renders text only, so a web-grounded answer is indistinguishable from model knowledge. |
| Alert re-delivery | **FIXED (logic) / channel still unconfigured** | [source] cooldown compared `last_seen` after setting it to `now` (never re-fired); now uses `delivered_at`. `ALERT_EMAIL` is absent → every alert records `unconfigured`. |
| Data export (job API) | **FIXED (context) / format honesty** | [source] background thread had no app context, so every job failed; app object now passed and entered. `zip` removed from `FORMATS` (it was advertised and never produced). Panel now downloads the file it previews. |
| MFA | **IMPLEMENTED BUT NOT ENFORCEABLE — launch blocker if advertised** | [source] login never challenges; `/mfa/challenge` sets a session on a TOTP alone, no password, **no rate limit**; recovery code disables MFA. UI copy corrected to stop claiming "protected". |
| Gmail integration | **NOT IMPLEMENTED (reachable)** | [source] onboarding import step unmounted with a placeholder client id; OAuth tokens discarded outside `TESTING`; `/ingest/gmail` builds an unconnected adapter and reports `ok` with 0 emails. |
| Telegram | **PARTIAL / security gap** | [source] webhook is public with no secret-token validation; its "reply" is returned in the HTTP body and never sent. GitHub secret scanning shows an **OPEN** `telegram_bot_token` alert on a **PUBLIC** repository. |
| Backup / restore | **NOT TESTED** | [source] pre-deploy dump only, no scheduler, no retention, no documented restore; a restore drill needs authorization this milestone does not hold. |
| Search / AI rate limiting | **NOT IMPLEMENTED** | [source] no limiter on `/api/v1/search`, `/api/v1/ai/chat`, or `/mfa/*`. |
| Export job store | **PARTIAL** | [source] in-memory per worker — status/download 404 across gunicorn workers; jobs lost on restart. |
| Observability truthfulness | **PARTIAL** | [source] `/metrics` JSON fallback hardcodes `shunya_db_up: 1` (found, **not fixed**); `sentry-sdk` installed but never initialised. |

## BB. Verification executed on this tree

| Check | Result |
|---|---|
| Full Python suite | **5970 passed, 128 skipped, 0 failed, 0 errors**, exit 0, 31:14 — describes the tree *before* the edits above |
| Focused after the edits | auth 18 · reliability/export/search/alerting 151 · security/isolation 122 · provenance/invitation/onboarding 60 — **351 passed, exit 0** |
| PostgreSQL 16 disposable :55432 | upgrade→`r6b37`→legacy row→`head`→`r6b38`: column `varchar(32)` nullable, no default; legacy `NULL` preserved; seed excluded from grounding; 188 tables; repeat upgrade no-op; downgrade/upgrade symmetric |
| Frontend | `tsc -b --noEmit` 0 errors; vitest 12 files/98 passed; build exit 0 (`index-rbrSIPha.js`) |
| Browser, current bundle | invitation 28/28 ×3 viewports; first-use 9/9 ×3; keyboard+first-object 36/36 ×3; axe 0 violations on 4 surfaces (automated only) |
| Palette navigation | [browser] *Work* → Commitments rendered; direct dispatch → Commitments rendered |

**Contamination disclosed:** the first invitation run resolved `SHUNYA_BASE_URL`
from `.env`, so the accept link pointed at `127.0.0.1:5001` and the harness issued
one **read-only** `GET /auth/invitation?token=…` against the production listener
(SPA shell only, no state change). The run was discarded; all quoted results come
from the corrected run with `SHUNYA_BASE_URL=http://127.0.0.1:51997`.

## CC. Verdict

**PUBLIC_LAUNCH_READY = FALSE.** Ranked:

1. **Uncommitted, uncertified work** (above) — nothing else can be certified first.
2. **Credential exposure** — Resend key in two unredacted logs; Telegram token with an open platform alert on a public repository; repository visibility still PUBLIC.
3. **Invitation inbox delivery** — unverified; needs an approved non-production provider.
4. **MFA** — advertised, not enforced, and its challenge endpoint authenticates on one factor.
5. **Integrations** — Gmail unreachable/broken; Telegram unauthenticated webhook and no reply path.
6. **Operational readiness** — no restore drill, alerting unconfigured, no rate limiting on search/AI/MFA.
7. **Production verification** — unauthorized, therefore NOT TESTED.
