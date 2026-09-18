# SHUNYA PRODUCT EXECUTION LEDGER — M5 → M15 (+ human feeling context)

**Campaign:** one connected product campaign. Milestone boundaries exist for
governance and certification only — the user must never experience them.
**M4:** CLOSED (`e04473c9f1abd32e3a4c1c631eec89b462b7f9d0`, CI run 35319490917).
Reopened only on a genuine M4 regression.
**Ledger republish rule:** this is a tracked artifact. Each commit that changes
it creates a new SHA; every such commit is re-certified by its own exact-SHA CI
run. The deployed/current SHA is therefore always *the SHA of the commit
carrying this file* — never a value hard-coded here.
**LAST UPDATED:** 2026-09-18 (campaign opened)

Allowed status vocabulary: `NOT STARTED` · `IN PROGRESS` · `BLOCKED` · `COMPLETE`.
Evidence levels: `IMPLEMENTED` → `TESTED` → `RUNTIME-PROVEN` → `INTEGRATED` →
`USER-PROVEN` → `ARCHITECTURALLY-PROVEN` → `SECURITY-PROVEN` →
`RECOVERY-PROVEN` → `CERTIFIED`. A capability can be implemented and still not
complete.

---

## 0. EVIDENCE STANDARD — corrected before any milestone work

Reconnaissance established what CI actually proves, and it is less than the
campaign requires. Stated plainly so no closure claim can lean on it:

| Claim | Truth (verified by reconnaissance) |
|---|---|
| CI test job green = system works | **No.** It is a Python unit + build gate: 5,429 tests on **SQLite in-memory** plus a Vite build. |
| CI proves persistence | **No.** Tests run on `sqlite:///:memory:` (`tests/conftest.py`), no migrations, no Postgres constraints/indexes/defaults. A SQLite-compatible but Postgres-incompatible defect passes. |
| CI proves a user journey | **No.** No Playwright/Selenium/browser test runs in `.github/workflows/ci.yml`. `npx vitest run` covers exactly 2 frontend unit files. |
| CI proves the product looks right | **No.** All visual/a11y artifacts (`screenshots/`, `frontend/axe-results/`, `frontend/screenshots/`, `scripts/fda28-browser-qa.js`) are manual, un-gated snapshots. |
| Auth is proven | **Partly.** `tests/test_r6b27_*` verify guard *logic*; DB-enforced isolation is not exercised end to end. |

Consequences adopted for this campaign:
1. **Journey proof requires an explicit, runnable journey harness** exercising HTTP
   routes against a real server (and, where the constitution requires visual
   judgement, real rendered screens). Until that exists, milestones cannot reach
   `USER-PROVEN`.
2. Milestone status will never be advanced on a green CI run alone (`§13` of the
   M4 directive already forbids this pattern for delivery).
3. ~12 test files mock the exact layer that would prove persistence
   (`tests/test_intelligence_service.py`, `tests/test_universal_research.py`,
   `tests/test_email_subsystem.py`, `tests/test_webhook_ingestion.py`,
   `tests/test_release_governance.py`, …). Their green result is *logic* evidence only.

---

## 1. RECONNAISSANCE BASELINE (verified 2026-09-18, read-only)

### 1.1 Frontend ↔ backend contract is genuinely broken in six places
These are not cosmetic; each makes a surface lie to the human.

| # | Defect | Evidence | Effect on the human |
|---|---|---|---|
| F-01 | `GET /api/v1/objects/types` returns **405** (route is POST-only). Callers: `frontend/src/components/executive-home/executive-home.tsx:784`, `frontend/src/runtimes/living-store.ts:306` | `app/production/objects.py:217`; correct route is `/api/v1/founder/objects/types` (`app/founder/routes.py:1001`) | Object counts never load → `DomainOverview` permanently claims "no data exists yet" (a **false empty state**), and living objects never populate |
| F-02 | `GET /api/v1/objects/<type>` returns **405**. Callers: `knowledge-browser-panel.tsx:293`, `src/api/objects.ts:203`, `living-store.ts:414` | same | Knowledge Browser permanently lands on "No knowledge entities found." |
| F-03 | `GET /api/v1/objects?limit=` / `?q=` return **404** | `settings-panel.tsx:189`, `living-workspace.tsx:226` | Settings and living workspace silently get nothing |
| F-04 | Doubled API path: `client.ts:92` posts `/api/v1/intelligence/ask` through `req()` which already prefixes `/api/v1` → `POST /api/v1/api/v1/intelligence/ask` = **404** | real route `app/intelligence/routes.py:171` | "Ask SHUNYA" in onboarding cannot work |
| F-05 | Invitation flow is a dead end: `GET /api/v1/auth/invitation/<token>` and `POST /api/v1/auth/accept-invitation` **do not exist (404)** | used at `src/app.tsx:93,143`; no backend route found | A user following an invitation lands on "Could not connect…" |
| F-06 | "Ask SHUNYA" navigates to itself: `home-page.tsx:186` opens type `'home'`, which renders `HomePage` again | `executive-home.tsx:892-898` | A primary affordance is a no-op — a button that does nothing |

### 1.2 Unreachable product surface (build-then-lose)
`executive-home.tsx:1049` `PrimaryFocusArea` is the router fallback, but every
`ORGANIZATIONAL_DOMAINS` workspace type is handled by an earlier branch, so the
entire surface is dead — taking with it `CompanionGreeting` (:229),
`WhatMattersNow` (:168), `NarrativeStream` (:268), `WorkVisibility` (:346),
`CalmState` (:322), `OperatingContextSelector` (:730), `MobileDomainNav` (:648)
and its `GET /api/v1/intention` fetch (:713). Also orphaned with no importer:
`command-surface.tsx`, `living-workspace.tsx`, `workspace-switcher.tsx`, both
`command-palette.tsx`, `useCommandPalette`. Orphaned onboarding steps:
`step-ai-intro`, `step-first-object`, `step-import`, `step-identity`,
`step-organization`, `step-team`, `step-auto-objects`.

### 1.3 Canonical memory vs legacy islands (the central integration problem)
- **Canonical authority:** `ObjectService` (`core/object_service.py:18`) writing
  `sh_objects` (`app/objects/legacy_models.py:62`), tenant + workspace +
  identity enforced (`:43,:48,:60-70,:76-89`), workspace membership via
  `ShWorkspaceMembership` (`sh_workspace_memberships`).
- **Written to canonical `sh_objects`:** `/api/v1/objects/*` (`app/objects/routes.py:23,71,109,130`), `/api/v1/upload` (`app/upload/routes.py:122`; `app/objects/upload.py:52`).
- **Islands (their own tables, not canonical memory):** CRM leads
  (`app/crm/routes.py:32`), commitments (`app/commitments/routes.py:10`),
  observations (`app/observations/routes.py:9`), documents/knowledge
  (`app/documents_knowledge/routes.py:40`), content generation
  (`app/content_studio/routes.py:113` → `ContentGeneration`), tasks
  (`app/execution/run_routes.py:176` → `TaskLifecycle`), UOP objects
  (`app/kernel/routes.py:40` → `sh_uop_objects`), a divergent legacy
  `app/objects/service.py` (`Object` → table `objects`, **no tenant, no authz**).
- **Consequence:** "one canonical object truth" (§22 of the directive) does not
  hold today. The same business reality can exist as a lead, a commitment, a
  document record, a content item, a task and a canonical object with no
  relationship between them.

### 1.4 Ingestion, documents, content lifecycle
- `app/ingestion/` is **empty** — there is no ingestion module.
- CSV/JSON import writes **identity claims / legacy `Lead`**, not canonical
  objects (`core/import_export.py:96,183,260,297`).
- XLSX parsing exists (`core/import_export.py:73`, `app/intake/profiler.py:90`)
  but its commit path is the legacy one above.
- PDF text extraction exists (`app/document_reader.py:24,51`); **no route turns
  extracted text into canonical objects or semantic classification.**
- Content lifecycle endpoints **do** exist
  (`app/content_studio/routes.py:221`, transition table `:273`) and media
  lifecycle (`app/media/routes.py:193,206,219`) — but they persist to
  `ContentGeneration`, not canonical memory, and are not surfaced as the
  content lifecycle the directive requires.

### 1.5 AI, realtime, feeling
- **AI:** POST `/api/v1/ai/chat` (`app/ai/routes.py:302`) with a real 3-tier
  fallback (`:427-530`), provider registry (`app/ai/provider.py:393`),
  deterministic `LocalProvider` (`:334`), per-provider timeouts (`:93,203,305`),
  internet retrieval via DuckDuckGo (`app/search/routes.py:33`), evidence
  written per turn (`app/ai/routes.py:542`).
- **AI context is single-object focused** (`app/ai/context.py:22`, canonical
  focused object at `:57`). There is **no aggregate company-state context** —
  so "company data first" (§9 of the directive) is not yet satisfiable.
- **Realtime:** SSE `/api/v1/events/stream` (`app/events/routes.py:146`) polls
  `sh_objects` every 5s; tenant/workspace enforced (`:76,:122`). The `EventBus`
  (`app/shunya/infrastructure/event_bus.py:175`) has a cross-worker Redis relay
  (`:737`) but **no browser bridge** — bus events never reach the UI.
- **Presence is real, not decorative** — verified: SSE
  (`src/runtimes/sse-runtime.ts:51`), `system.heartbeat` every 10s
  (`app/reality_engine/routes.py:149-154`), mode derived from transport state and
  real signals (`src/components/living-workspace/living-presence.tsx:107-115`).
  The only timer refreshes an age label (`:83-86`). M10 starts from a truthful base.
- **Feeling:** **NOT FOUND** as a first-class product concept. Incidental
  mentions only: `core/health_intelligence/engine.py:193,258-307`
  (`MENTAL_WELLBEING`, `MOOD_SCORE` — health domain), `app/companion.py:97`
  (`detect_mood`), `app/coach.py:92,145`, `app/media/service.py:171`,
  `core/capability_registry.py:282`. No feeling object, table, field or endpoint.
  This is a clean slate for the emotional-context layer — build it on
  Observation/Evidence/Conversation, not on new parallel structures.

### 1.6 Release integrity gap (production risk)
The SPA **shell** is served from the mutable worktree for `/` and `/auth/*`
(`app/routes.py:125-144`) and `/workspace/*` (`app/founder/routes.py:171`), both
hard-coding `frontend/dist` and bypassing `resolve_frontend_dist()`
(`app/frontend_release.py:44-72`). Assets are release-pinned via
`/home/shunya-deploy/releases/current`. A local `npm run build` would therefore
change the served shell to reference asset hashes that are absent from the
published release → broken production, with health still green.

### 1.7 Production secrets in logs — FIXED, rotation outstanding
The production DSN including its password was written to the journal on every
worker boot (`app/__init__.py` logged `str(SQLALCHEMY_DATABASE_URI)[:30]`).
Removed in commit `7848f09` (source-level safe descriptor + a handler-level
redaction filter covering messages, args, `extra=` fields, `stack_info` and
exception tracebacks, with over-redaction guarded by tests).
**Outstanding:** the credential has already been written to logs and should be
rotated — a production credential change requiring founder approval.

### 1.8 Constitutional conflicts — flagged, NOT silently resolved
Per `§39`, these are reported rather than decided unilaterally:
1. **Accent colour:** `SHUNYA_PRODUCT_EXPERIENCE_CONSTITUTION.md §16` specifies
   purple `#6C4AE2` as the single interaction colour; the live token source
   `frontend/src/tokens/definitions.ts` states the opposite — "Purple removed as
   brand colour. Gold is the only accent. Light mode only." — and the Visual
   Design Bible and Presence Canon agree with gold. **No redesign will be made
   either way.** Current rendering follows the live tokens.
2. **Component library version:** installed `@mantine/core ^9.5.1`
   (`frontend/package.json`) vs Mantine v7 in
   `docs/frontend/FRONTEND_ENGINEERING_GUIDE.md`. Building continues on the
   installed v9; the documentation drift is recorded, not "fixed" by editing docs.
3. **Mobile orientation:** the M4/M5 directive says "portrait-locked where
   established by constitution"; the constitution actually specifies
   **portrait-first**, and contains **no orientation lock**
   (`design/experience/10_mobile_canon.md §1`). Building to portrait-first;
   nothing will be locked to portrait on the basis of a mis-remembered rule.
4. **Token naming/scale:** prose docs use `--sh-*` with a longer spacing ramp;
   `frontend/src/tokens/definitions.ts` self-declares canonical (`shunya-`
   prefix, 4px grid, spacing `xs 4 … 6xl 128`). Code file is treated as
   canonical; prose drift recorded.
5. **Breakpoints:** Mobile Canon (`<640 / 640–1024 / 1024–1440 / >1440`) vs
   Product Experience Constitution §12.1 (`<480 / 480–767 / 768–1023 / ≥1024`).
   Recorded as a conflict; responsive work will consume the existing adaptive
   runtime rather than invent a third scale.

---

## 1.9 DELIVERY RECORD (exact-SHA chain)

| Commit | Content | CI run | Result |
|---|---|---|---|
| `7848f09` | credential removed from logs (source + handler filter) | 35327920807 | **CANCELLED** (superseded by a later push; the suite had already passed — 5312 passed, 128 skipped — before cancellation). Cancelled ≠ failed; the change is certified as an ancestor of `f680a41`. |
| `3a78255` | this campaign ledger + M5/M6 truth correction | 35328439860 | **CANCELLED** (same cause; suite passed first) |
| `f680a41` | canonical object read routes + `list_authorized()` + `api.ask` path fix | **35329653199** | **OVERALL SUCCESS** — test 19m21s; deploy 3m50s; latency 0.024366s (attempt 1/12, limit 5s); certified == deployed local == public SHA; `release_type=CI_CERTIFIED`; public health + final provenance verified |

**Runtime proof on production (deployed `f680a41`, verified over HTTPS):**

| Probe | Before | After |
|---|---|---|
| `GET /api/v1/objects/types` | 405 | **401 Authentication required** |
| `GET /api/v1/objects/customer` | 405 | **401 Authentication required** |
| `GET /api/v1/objects?limit=10` | 404 | **401 Authentication required** |

401 (not 200, not 405) is the correct proof: the route now exists **and** the
authorization boundary is enforced. An unauthenticated caller cannot read tenant
data; a signed-in member gets real data (proven by the 11 HTTP tests).

**Credential defect closed in production:** the post-deploy worker boot log now
reads `"db": "postgresql://localhost:5432/shunya_os"` — scheme, host, port and
database, **no userinfo, no password**. Previously the full DSN including the
credential was written on every boot. Rotation of the already-exposed credential
is still outstanding (needs founder approval).

---

## 2. MILESTONE REGISTER

Every milestone carries: STATUS · CURRENT SHA · built · integrated · tested ·
runtime-proven · user-proven · remains · risks · next exact action.

### M5 — ENTRY → WORKSPACE — `IN PROGRESS`

- **CURRENT SHA:** the commit carrying this ledger.
- **WHAT WAS BUILT:** (pre-campaign) phase state machine
  `public → login → onboarding → booting → ready` (`frontend/src/app.tsx:23`),
  public homepage (`src/components/public/homepage.tsx:21`), 3-step onboarding
  (`src/components/onboarding/onboarding-flow.tsx:17`), workspace routing
  (`DomainWorkspaceRouter`, `frontend/src/components/executive-home/executive-home.tsx:854-1050`).
- **WHAT IS INTEGRATED:** auth sign-in → `POST /api/v1/founder/signin` →
  `bootstrap()` → `GET /api/v1/for2/whoami` (`frontend/src/hooks/use-active-context.ts:23`;
  `app/for2/routes.py:108`) → authenticated workspace.
- **WHAT IS TESTED:** no journey test exists. 5,429 backend tests (SQLite) and
  2 frontend unit files; **zero** coverage of this journey.
- **WHAT IS RUNTIME-PROVEN:** the shell renders and `/health` is green; the
  authenticated workspace has **not** been driven end to end in this campaign.
- **WHAT IS USER-PROVEN:** nothing.
- **WHAT REMAINS:** **F-01, F-02, F-03, F-04 are FIXED and runtime-proven**
  (commit `f680a41`, production probes above) — the workspace now receives real
  object counts, typed object lists and collection/search results instead of a
  false empty state, and `api.ask` reaches its real endpoint. Still open:
  **F-05** invitation flow (`GET /api/v1/auth/invitation/<token>`,
  `POST /api/v1/auth/accept-invitation` do not exist — a user following an
  invitation still hits a dead end); **F-06** the "Ask SHUNYA" affordance is
  still a no-op and needs a real resident AI surface rather than a route to
  itself; no object-aware empty state on the authenticated home (only
  task-based text at `home-page.tsx:290,300,319,338`); onboarding completion is
  still a client-side localStorage flag (`onboarding-flow.tsx:46-51`) so the
  identity/organization gate is skippable; no journey harness and no 10-minute
  fresh-user test has been run. Cause of the false empty state is now recorded
  and regression-guarded: `tests/test_objects_read_routes.py`.
- **KNOWN RISKS:** the "false empty state" (F-01) is fixed, but the same class of
  defect can recur anywhere a surface trusts a route that was never mounted — the
  contract matrix (§27 of the directive) is the systematic guard and is still to
  be produced.
- **NEXT EXACT ACTION:** fix **F-05** (invitation endpoints — the last dead end
  in the entry journey) and **F-06** (a real resident AI surface for "Ask
  SHUNYA"), then build the journey harness that can prove the whole M5 journey.

### M6 — BRING YOUR BUSINESS INTO SHUNYA — `IN PROGRESS` (foundation only)

- **WHAT WAS BUILT:** canonical `ObjectService` + `sh_objects`; two upload
  routes that create canonical documents; legacy CSV/XLSX import pipeline;
  content generation.
- **WHAT IS INTEGRATED:** upload → canonical object → event
  (`app/upload/routes.py:97`). Import → **identity claims / legacy leads**, not
  canonical memory.
- **WHAT IS TESTED:** unit/integration level only; no ingestion journey.
- **WHAT IS RUNTIME-PROVEN:** nothing for ingestion.
- **WHAT REMAINS:** the whole ingestion journey
  `SELECT → UPLOAD → ANALYZE → IDENTIFY → PREVIEW → CLASSIFY → CONFIRM/CORRECT
  → COMMIT → VERIFY → AVAILABLE IN WORKSPACE → AVAILABLE TO AI`; semantic
  document classification with uncertainty; canonical customer/supplier/
  engagement objects; content lifecycle on canonical memory; route collision
  between the two blueprints mounting `/api/v1/upload`
  (`app/__init__.py:831,850`) must be resolved.
- **KNOWN RISKS:** two blueprints share one URL prefix — behaviour is
  mount-order dependent.
- **NEXT EXACT ACTION:** define the canonical vertical nerve for **Customer**
  (create → authorize → canonical object → persistence → evidence → event →
  home → AI context → attention → archive/restore → refresh/restart → security),
  then reuse it for Supplier, Document, Content.

### M7 — SHUNYA UNDERSTANDS — `NOT STARTED`
Remains: aggregate **company-state** AI context (`app/ai/context.py:22` is
single-object only); explicit company-first / internet-second ordering with
provenance separation. Exists and reusable: 3-tier provider fallback, evidence
logging per turn, DuckDuckGo retrieval.

### M8 — SHUNYA OPERATES — `NOT STARTED`
Remains: state-driven operation (`FUNCTION(state, intent, evidence, time)`), not
pipelines; canonical edit/assign/relate/execute/complete/defer/archive/restore.

### M9 — SHUNYA NOTICES — `NOT STARTED`
Remains: attention items with reason, context, evidence, object, action,
dismissal, persistence, auditability. Bases that exist: `Observation`
(`app/observations/routes.py:9`), attention routes
(`app/execution/run_routes.py:199`, `app/commercial/routes.py:428`).

### M10 — SHUNYA IS ALIVE — `NOT STARTED` (truthful base already present)
Presence/heartbeat verified as evidence-bound (see §1.5). Remains: bridge the
`EventBus` to the browser so presence and surfaces reflect bus activity, not
only a 5s `sh_objects` poll.

### M11 — SHUNYA RECOVERS — `NOT STARTED`
Remains: the full failure matrix (network, API, validation, authz, stale object,
concurrent modification, AI provider, internet, upload, partial ingestion, DB,
Redis, realtime disconnect, refresh, restart) and the explicit outcome states
`NOT STARTED / PROCESSING / SUCCEEDED / FAILED / PARTIALLY COMPLETED / NEEDS
ATTENTION / RECOVERABLE`.

### M12 — SHUNYA WORKS EVERYWHERE — `NOT STARTED`
Remains: responsive/a11y certification across the device matrix. Portrait-first
(not locked). Touch ≥44px, focus visible, reduced-motion collapse 0ms.

### M13 — END-TO-END CERTIFICATION — `NOT STARTED`
Remains: **the journey harness itself** (currently absent from CI), GJ-01…GJ-16
and EGJ-01…EGJ-10 proven end to end, plus the full contract matrix.

### M14 — RELEASE CANDIDATE — `NOT STARTED`
### M15 — PUBLIC LAUNCH READINESS — `NOT STARTED`
Blockers already known: rotated DB credential (§1.7 approval), release-integrity
shell serving (§1.6), journey harness, and the constitutional conflicts in §1.8.

---

## 3. HUMAN FEELING / EMOTIONAL CONTEXT — `NOT STARTED`

- **MODEL (binding):** a business is operated by humans; human feeling is
  first-class **context**, never a SHUNYA emotion and never a psychological
  assertion. Signal → observation → context → interpretation *with uncertainty*
  → appropriate response → memory only with authority/consent → future context.
- **MUST NOT:** label the human ("you are angry"), argue with a correction,
  treat a past feeling as current, retain every emotional statement, or use
  feeling for pressure, guilt, fear-based urgency, engagement scoring or
  dependency.
- **SOURCES:** explicit statements (strongest), explicit mood input,
  conversational signals (uncertain), interaction friction (product signal, not
  diagnosis), business events with human significance.
- **REPRESENTATION:** a *feeling signal* with source, expression, confidence,
  timestamp, context, related object/event, user correction, retention policy and
  provenance — related to Identity, Organization, Workspace, Conversation,
  Object, Event, Action, Outcome, Time. **Reuse Observation/Evidence/Conversation
  structures**; introduce a new canonical structure only if genuinely necessary
  (§20 of the continuity command forbids emotional technical debt).
- **TEMPORAL:** feelings expire; a resolved concern must stop being the current
  context.
- **RETENTION:** EPHEMERAL · CONTEXTUAL · PERSISTENT USER-PROVIDED · RESOLVED.
- **PRIVACY:** strict authorization and tenant isolation; never expose one
  user's feeling context to another user in the same organization without
  explicit product authorization; never log sensitive conversation unnecessarily.
- **UI:** expressed through timing, language, attention, recovery, clarity and
  prioritisation — not mood trackers, emoji, therapy UI or sentimental animation.
- **BEHAVIOUR MUST CHANGE:** frustration → reduce complexity, explain, surface
  recovery; uncertainty → show evidence and alternatives, avoid false certainty;
  excitement → convert to concrete grounded action; "not now" → defer, snooze,
  reduce attention, persisted.
- **NEXT EXACT ACTION:** after the Customer nerve is proven, define the feeling
  signal on top of `Observation` with a failing EGJ test first (TDD), so the
  layer is built only where it changes behaviour.

---

## 4. CAMPAIGN-LEVEL RISKS

1. **False empty states** (F-01) tell the human their workspace is empty when it is
   not — the most damaging class of defect for trust and for M5.
2. **No journey harness** — every "complete" claim above the unit level is
   currently unprovable. This is the single biggest evidence gap.
3. **Canonical/legacy split** — the directive's "one canonical object truth"
   cannot hold while six subsystems own their own tables.
4. **Release-integrity gap** — a local frontend build can break production while
   health stays green.
5. **Unrotated exposed credential.**
6. **Five constitutional conflicts** (§1.8) that must not be silently "fixed".

## 5. NEXT EXACT ACTION (campaign cursor)

1. Land and certify the credential fix (`7848f09`) — CI in flight.
2. Fix F-01…F-06 so no surface lies to the human, each with a regression test.
3. Build the journey harness (HTTP-first, against a real server, runnable in CI)
   so M5/M6 can reach `USER-PROVEN`.
4. Close the M5 journey: entry → workspace with a truthful, object-aware empty
   state and a working first meaningful action; run the 10-minute fresh-user test.
5. Then the Customer vertical nerve, end to end, reused for Supplier → Document →
   Content.
