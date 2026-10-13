# SHUNYA — MASTER GAP & PENDING REGISTER (SUPERSET, ALL SOURCES)

**Date:** 2026-10-13 (consolidated; B2 wave 2026-10-13; B3/B4/B5 + L-gate wave 2026-10-13)
**Repository:** shunya-os/Shunya-OS @ master **9a5a37e** (releases: 583598f B1 baseline → ec0b691 B2 → 3b78e13 B3 → 9f3ed5a B4/B5/L2/L3 → 9a5a37e L3 hotfix; prior baselines 26b592e (Wave A), 6b5767f) — CI_CERTIFIED per release, deployed, live-verified
**Sources merged:** (1) `docs/launch/SHUNYA_100_GAP_REGISTER.md` (session sweep, 5 perspectives), (2) `artifacts/SH_M6_M15_BLOCKER_REGISTER.md` (LB/S/P/F), (3) `SHUNYA_MASTER_MILESTONE_TRACKER.md` (G-gates, FDA gates, orphans, capability registry), (4) live production/host findings this session, (5) founder-pending decisions.
**Rule:** this document is the single umbrella register. Child registers stay authoritative for their own detail; nothing here is closed without evidence.

---

## SECTION 1 — SESSION-DISCOVERED GAPS (100) — condensed

Full detail + evidence: `docs/launch/SHUNYA_100_GAP_REGISTER.md`. Counts: 27 P1 / 52 P2 / 21 P3.

| Range | Perspective | Count | Headline |
|-------|-------------|-------|----------|
| A1–A18 | Frontend/UI | 18 | Calendar + marketing + notification + onboarding(4–10) + UBME surfaces unmounted; invite no-op; fake Gmail connect; analytics/empty-state holes |
| B1–B24 | Backend/API/Security | 24 | 9 unguarded blueprints (auth whitelist + header identity = **B16** highest leverage); SMTP/outcome/execution stubs; 5 missing routes; 2 unregistered blueprints |
| C1–C20 | Integrations (email/WhatsApp/connectors) | 20 | Email inbox no UI; no read/search/threads/attachments; 3 templates; WhatsApp outbound dead + no UI; hub 24/33 display-only; OAuth unusable |
| D1–D20 | Product journeys | 20 | Profile desync; prefs not enforced; sessions fabricated; invites never emailed; analytics Math.random; leads/invoices cannot complete; object delete missing; MFA path mismatch |
| E1–E18 | Ops/Security-ops | 18 | No alerting; backups unscheduled/restore untested/uploads unbacked; **secrets in public history (E6)**; rate-limit on proxy IP; no lockout/expiry; rollback degrades release; KYC undecided |

---

## SECTION 2 — LAUNCH BLOCKER REGISTER (tracked items, current status)

| ID | Item | Status (evidence-backed) |
|----|------|--------------------------|
| LB-001 | Founder acceptance walkthrough + sign-off | NOT STARTED — founder-gated |
| LB-002 | Age/safety governance | CI-CERTIFIED on c6b0fa0 + runtime-proven; residual = KYC method (E18/§7-D3) |
| LB-003 | Production behind master / CI red | RESOLVED (prod == master == 26b592e, run 38296092034 SUCCESS, 2026-10-12) |
| LB-004 | PUBLIC_LAUNCH_READY flag | CONFIRMED FALSE (by design) |
| S-001 | HSTS | FIXED + live-verified + CI-enforced |
| S-002 | Knowledge API 403 no-org | FIXED |
| S-003 | HTTPS-only test in CI | FIXED (contract tests + deploy smoke step) |
| S-004 | Cross-tenant read isolation | FIXED + 20 adversarial tests + CI; ZG-03 extension (26b592e): leads API, CRM lead surface, celebration/calendar feeds tenant-scoped — live-verified 0 exposed rows |
| S-005 | knowledge.edit admin-only | PARTIAL — role-policy decision (§7-D6) |
| S-006 | Branch protection absent | FIXED — enabled 2026-10-12: required check 'test' + ≥1 approving review, admin bypass kept, force-push/deletion blocked; read-back validated. Note: CI's milestone validator needed a PR-ref fix so the required check can go green on PRs |
| P-001 | Provider-unavailable truthful surface | NOT A BUG |
| P-002 | GracefulDegradationHandler retrieval-only | PARTIAL (§7-D9) |
| P-003 | Empty states not systematic | PARTIAL (§7-D7) |
| P-004 | Documents 500 (add-to-workspace) | NOT REPRODUCIBLE + 4 journey tests guard |
| P-005 | Calendar surface | IMPLEMENTED BUT NOT CERTIFIED — mounting decision (§7-D5) |
| P-006 | Integration Hub mock | STALE — real API; honesty gaps remain (C15/C16, §7-D8) |
| P-007 | Keyboard/WCAG verification | PARTIAL (§7-D10) |
| F-001 | Billing/subscription | DEFERRED per founder — re-affirm (§7-D11) |
| F-002 | Customer-specific CRM page | PARTIAL (entity-type only) |
| F-003…F-012 | Profile/team/notifications/export/sessions/workspace-settings/api-explorer/shortcuts/help/analytics | DELIVERED (certification-level status per perspective A/B/D findings — most are PARTIAL in practice; see Section 1) |

---

## SECTION 3 — MILESTONE / FDA GATES (from tracker, re-assessed with session evidence)

| Gate | Tracker status | Session evidence → current verdict |
|------|---------------|-------------------------------------|
| G0 Forensic baseline | VERIFIED | Stays VERIFIED |
| G1 Core OS convergence | REMEDIATION_IN_PROGRESS | Identity 6+ implementations, memory/planning/decision/execution duals remain (orphans §4). UNCHANGED |
| G2 Data/Integration fabric | SUBSTANTIALLY BUILT, E2E cert open | E2E browser certification not performed. UNCHANGED |
| G3 SHUNYAAI | FCR-02 COMPLETE | Ask pipeline runtime-proven in production. IMPROVED → CERTIFIED for the canonical path |
| G4–G9 Vertical domains | NOT_CERTIFIED ×6 | Finance/Operations frontends exist + real APIs (G10 claims stale); domain E2E browser certification still open. mostly UNCHANGED |
| G10 Frontend/UX | OPEN | 18 FE gaps (§1-A) — still OPEN |
| G11 Security/Reliability | NOT_CERTIFIED | P0/P1 security gates closed; 9 unguarded blueprints (B17–B24) keep it NOT_CERTIFIED |
| G12 Founder acceptance | NOT_STARTED | LB-001 pending — NOT_STARTED |
| FDA-3,4,5,11,24,28,30,31 | PARTIAL | Unchanged (no new certification effort this session) |
| FDA-34 | NOT_PROVEN | Unchanged |
| FDA-35,36 | NOT_STARTED | Unchanged — NOT_STARTED (real-time/recovery gates) |
| Tracker BLOCKERS list | G1-02, G1-03, G1-06, G1-07, G1-08, G1-09, P-01, P-02, P-03 | **STALE ENTRIES MARKED:** G1-08 (finance frontend BUILT+mounted), G1-09 (operations frontend BUILT+mounted), G1-06 (knowledge API exists, PARTIAL), G1-07 (memory API exists, PARTIAL), P-01 WhatsApp → re-scoped to C10–C14, P-03 payment flow (razorpay wired — verify), P-02 client portal (unverified this session — KEEP OPEN) |

---

## SECTION 4 — ORPHANS & DUPLICATES (from tracker; unchanged unless noted)

| ID | Item | Verdict |
|----|------|---------|
| O-01 | app/intelligence_routes.py (UIR blueprint) | LEGACY — now also physically unregistered (BE-002) |
| O-02 | cross_boundary_routes.py | LEGACY — not registered |
| O-03 | /api/v1/ai/chat provider bypass | DUPLICATE — active route; orchestrator consolidation recommended |
| O-04 | /search/ai/analyze | DUPLICATE — active |
| O-07…O-18 | engine runtimes (cognitive, planning, automation, financial, knowledge, decision, agreement, asset, initiative, operations, health, learning intelligence) | No consumer — CANONICAL+MUST-CONNECT or INTERNAL ONLY per engine-spec review (never delete) |
| O-19, O-20 | app/learning_intelligence/, execution_intelligence | Archived stubs (O-20 confirmed MOCK in B10) |
| D-01…D-05 | memory/evidence/communication/intelligence_runtime stores | Legacy/duplicate stores — convergence pending (G1) |
| Route duplicates | mixed router, ai/chat, copilot/ask, commercial ask, cfo ask | DUPLICATE — canonical ask is /api/v1/intelligence/ask; others remain active (now safety-gated) |
| Capability registry | relationships, finance, operations = UNWIRED | UNCHANGED — MUST-CONNECT (G3-related) |
| Provider chains | app/ai/provider.py 9-provider vs orchestrator 5-provider | DUPLICATE — consolidation candidate |

---

## SECTION 5 — CI / RELEASE / VERIFICATION HYGIENE (session findings)

| # | Item | Evidence | Status |
|---|------|----------|--------|
| H1 | fda30_security 2 local failures (invalid-session 403-vs-401; cross-tenant webhooks) | Pre-existing at HEAD (stash-proven); CI green both runs | Resolve test intent vs actual 403 semantics — treats unknown X-Identity-Id as forbidden; reconciliation task |
| H2 | GJ-06 real-document journey fails on host, passes CI | pdfplumber/env divergence (stash-proven) | Host-only; CI is authority |
| H3 | 3 vitest onboarding tests fail under node 26, pass under pinned node 22 | Documented in ci.yml | Host-only |
| H4 | test_universal_research live-provider flake (DDG) | Failed once in CI on docs-only push; rerun green | FIXED (9f3ed5a): upstream refusal → truthful skip by default; strict provider-parity FAIL only under `SHUNYA_LIVE_NET_TEST=1`; offline normalization contract unchanged |
| H5 | alembic offline `--sql` unusable (alembic.ini placeholder; offline path ignores DATABASE_URL) | env.py offline branch | Tooling gap — fix offline URL resolution |
| H6 | Migration verification method | r6b28 verified via live alembic_version + columns post-deploy | Add a deploy-step column assertion for schema-bearing migrations |
| H7 | Certification-tenant credential file stale (server rejects); vault login works | ~/.shunya/certification_login.txt vs vault_67340bf9c378 | Rotate/refresh the file to the vault credential |
| H8 | `gh run watch | tail` masks exit code (watcher discipline) | This session | Use explicit exit-code capture (done in rerun watcher) |

---

## SECTION 6 — LIVE PRODUCTION DEFECTS (observed, not yet fixed)

| # | Defect | Evidence | Sev |
|---|--------|----------|-----|
| L1 | `/api/v1/analytics/dashboard` returns 500: relation `ai_execution_records` does not exist — model/table drift, 12 errors/24h unalerted | CLOSED (3b78e13): migration `b3_missing_schema_tables` created `ai_execution_records`/`user_profiles`/`feedback_signals`; live 500→200; alembic head verified — alerting remains E1 |
| L2 | "Background outcome review failed: Working outside of application context" recurring in journald | FIXED (9f3ed5a): reviewer runs inside `current_app.app_context()` (nested-safe); journald 214 occurrences before, 0 since deploy |
| L3 | Public /health + /metrics expose deployment metadata unauthenticated | FIXED (9f3ed5a + hotfix 9a5a37e): /metrics gated by HEALTH_TOKEN (403 no/wrong token, 200 with; live-verified); /health stays public per deploy smoke contract (status + git_commit); HEALTH_TOKEN set in prod .env (0600, random, never in git) |
| L4 | 8 user files (PII itineraries) git-tracked in uploads/, repo PUBLIC | FIXED (9f3ed5a, index-only): 15 artifacts untracked via verified manifest; sha256-matched backup `/home/shunya-deploy/backups/legacy_repo_uploads_20261013/`; files on disk preserved; no rewrite/force-push/visibility change — history purge + repo privacy remain founder-pending (D4) |

---

## SECTION 7 — FOUNDER-PENDING DECISIONS (numbered for sign-off)

| # | Decision | Context | Recommendation |
|---|----------|---------|----------------|
| D1 | **LB-001 founder acceptance** — walkthrough + sign-off ceremony | G12 empty | Schedule 1-day walkthrough against Section 1 P1s after remediation wave 1 |
| D2 | **S-006 branch protection** | Verified absent | Enable: require CI status check + PR review on master, disable force-push |
| D3 | **E18 KYC/age-verification method** | Gate records verification outcome only | Decide: documentary KYC provider vs self-attestation; until then policy is admin-attested |
| D4 | **E6 secrets purge / repo privacy** | VERIFIED NO LIVE CREDS IN HISTORY (all `.env` blobs placeholder; credentials.py clean); **REAL TELEGRAM TOKEN in initial commit**; PII (itineraries/audit) in history | Reversible containment applied 2026-10-13 (secret scanning + push protection ENABLED, read-back verified; `.env` untracked at HEAD). Remaining are founder-authorized: F-1 rotate telegram token, F-2 purge-or-private (recommend both), F-3 rotate flagged keys. Evidence: `docs/launch/D4_EXPOSURE_INVENTORY.md` |
| D5 | **P-005 calendar mounting** | Component+API exist | Confirm navigation placement; then finish wiring (POST create + month/year params) |
| D6 | **S-005 knowledge.edit roles** | admin-only today | Grant to manager/member or keep restricted |
| D7 | **P-003 empty-state systematics** | PARTIAL | Adopt one empty-state pattern across all list panels |
| D8 | **Integration honesty vs wiring (C10/C15/C16/C17)** | 24/33 connectors display-only; WhatsApp/email outbound dead | Decide: truthfully label "not configured" (quick) and pick 3 connectors to fully wire (email+WhatsApp are the founder's asks) |
| D9 | **P-002 degradation scope** | retrieval-only | Extend wrapper to reasoning/planning or accept residual |
| D10 | **P-007 keyboard/WCAG audit** | unverified | Schedule browser-level WCAG pass |
| D11 | **F-001 billing deferral** | deferred | Re-affirm for public launch scope |
| D12 | **P-02 client portal / P-03 payment flow priority** | tracker BLOCKERS, unverified this session | Verify current state; set priority or formally out-of-scope |

---

## SECTION 8 — RECOMMENDED EXECUTION ORDER (single next actions)

**Wave 0 — stop-the-bleed (needs D2/D3/D4 sign-off):**
1. B16 auth middleware (9 unguarded blueprints) + move the 5 missing-route gaps (B3–B7) into the same hardening pass
2. L1 analytics dashboard 500 → schema drift fix + E1 alerting hook (webhook/email on 500)
3. E6 secrets: purge/rotate + repo privacy (D4)

**Wave 1 — founder-ask integrations (D8):**
4. Email: inbound UI (C1–C4) + compose v1 (C5–C7) + real send path (B8)
5. WhatsApp: outbound wiring (C10) + minimal reply surface (C11) + persistent setup (C12)

**Wave 2 — journey completion (D1 prep):**
6. D10 lead lifecycle UI + D17 invoice-to-customer + D11 object delete + D12 workspace switcher
7. D7 invites (real email), D6 sessions truth, D3 notifications enforcement

**Wave 3 — founder acceptance (D1) and G12.**

**Never auto-delete any orphan** — archive-only per constitution; classification per engine-spec review (Section 4).

---

## SECTION 9 — ZG-03 WAVE B2 — PROVIDER & MODEL TRUTH (2026-10-13)

**SHA reconciliation:** baseline released `583598f` (PR #5, CI SUCCESS run
38311203988). Wave B2 released as **`ec0b691`** (Merge PR #6
`zero-gap-03-b2-provider-truth`, CI SUCCESS run 38323907898, deployed; PR
head `5204c5a` = c36d50b + fda25 lead-code fix). Evidence doc:
`docs/launch/ZG03_B2_PROVIDER_TRUTH.md` (reproductions at 583598f before any
change) + `docs/launch/ZG03_B2_CAPABILITY_INVENTORY.md` (add-on baseline).

**B2 items (status):**

| # | Item | Status |
|---|------|--------|
| B2-1 | Reproduced: Content Studio image generation broken (HF 402 no credits; success-shaped description_only; `dummy` purple placeholder advertised; image `/generate` route shadowed by text route) | REPRODUCED at 583598f |
| B2-2 | Reproduced: retired text models — Groq `llama-3.3-70b-versatile` RETIRED (live 404), Gemini `gemini-2.0-flash` RETIRED, Cloudflare `@cf/meta/llama-3.1-8b-instruct` RETIRED, Anthropic `claude-3-haiku-20240307` RETIRED; HF text endpoint deprecated | REPRODUCED (live catalogs) |
| B2-3 | Explicit configuration: `app/ai/model_catalog.py` canonical catalog (defaults, valid/retired sets verified live 2026-10-13, ErrorClass taxonomy, free-first chain policy) | IMPLEMENTED |
| B2-4 | Truthful availability: provider `is_available()` = key + valid model + no outage; image registry availability computed; `dummy` test-only | IMPLEMENTED |
| B2-5 | Error classification: ErrorClass surfaced in provider results, content/media/capability API responses | IMPLEMENTED |
| B2-6 | Text failover: `complete_with_failover` (skip unavailable, advance on classified errors, truthful aggregate failure; local canned fallback REMOVED from auto-path) | IMPLEMENTED |
| B2-7 | Genuine image fallback: Pollinations (free, no key — verified real JPEG) as HF→Pollinations chain in media + image registry | IMPLEMENTED |
| B2-8 | Route shadow fixed: image endpoints → `/api/v1/content/image/*`; legacy `/api/v1/content/providers` alias kept | IMPLEMENTED |
| B2-9 | Retired ids purged from app/ai/provider.py, inference_orchestrator, model_orchestrator, inference_governance, llm adapter, for1 engine | IMPLEMENTED |
| B2-10 | Add-on: universal capability registry `app/ai/capabilities.py` + `/api/v1/capabilities*` routes (status/summary/execute/diagnostics), ProviderOrchestrator truthful | IMPLEMENTED |
| B2-11 | Tests: `test_provider_catalog_b2.py` + `test_media_fallback_b2.py` (34 tests) + adapted r6b27 | IMPLEMENTED — green local |
| B2-12 | Production env model values (GROQ_MODEL→openai/gpt-oss-20b, GEMINI_MODEL→gemini-2.5-flash, CLOUDFLARE_MODEL→-fp8) | APPLIED 2026-10-13 pre-deploy (`.env` keys untouched) |
| B2-13 | fda25 lead-code collision (UNIQUE leads.code duplicate in import batches when local date ≠ UTC date) — root-caused + fixed in `next_inquiry_code` (UTC clock + max-suffix sequence) | FIXED (5204c5a) — baseline scrubbed run reproduced at 583598f; 13/13 pass post-fix |
| B2-14 | Full-suite regression (scrubbed/CI-equivalent): baseline 583598f = 5665 passed / 4 failed (fda25 only) ; branch 5204c5a = all green | VERIFIED |
| B2-15 | Full-suite 45 errors in host run = production `.env` leakage via create_app→load_dotenv (host-only; zero in CI and scrubbed runs) | CLASSIFIED — host divergence, not product |

**Known negatives / remaining:**
- Hugging Face: PRODUCTION OUTAGE (credits required) for images AND text —
  classified truthfully; only becomes available again when credits restored
  (PROVIDER DEPENDENCY).
- Video generation (Wan/LTX evaluated): no free hosted provider verified —
  capability registered, status UNAVAILABLE, no fake surface.
- Embeddings: self-hostable (sentence-transformers NOT installed) / HF
  credit-gated — capability registered, status UNAVAILABLE.
- Image editing: ComfyUI adapter exists, no server configured — evaluated.
- STT/TTS adapters exist (whisper/piper/kokoro) but HF serverless is
  credit-gated; Groq whisper-large-v3 STT registered (free, key present).
- `core/personal_os/providers.py` was advertising every universal provider as
  `available` with no evidence — corrected to computed statuses (B2-10).
- Section 4 "Provider chains duplicate" row: app/ai/provider.py remains the
  single live chain; inference_orchestrator/provider_registry now catalog-fed
  (no retired ids) but is still unwired (CANONICAL + MUST CONNECT — G3).

**ZG-03 Waves B3/B4/B5 + L1–L4 (2026-10-13, all merged + deployed + live-verified):**

| # | Item | Status |
|---|------|--------|
| B3-1 | Missing schemas: `ai_execution_records`, `user_profiles`, `feedback_signals` declared by models, absent live (L1 root cause) → migration `b3_missing_schema_tables` (idempotent, alembic chain head verified live) | IMPLEMENTED — 3b78e13, tables exist, analytics 200 |
| B3-2 | NUL-byte ingestion: centralized sanitizer `app/common/text_safety.py` applied at import/documents/profile/gmail/webhook ingest (rejects NUL in text payloads) | IMPLEMENTED — tests green |
| B4-1 | Workspace listing is membership-scoped; legacy tenant-scoped views hardened: `/api/v1/orgs/<org_id>/workspaces` CRUD gated by canonical OrgMember membership (was login-only → cross-tenant read/write) + reads scoped to canonical tenant union (org id + legacy_tenant_id bridge) | IMPLEMENTED — 9f3ed5a; live: org7 200→403, org278 200 |
| B5-1 | Live-provider test flake (H4): upstream refusal → truthful skip; strict parity under `SHUNYA_LIVE_NET_TEST=1`; offline normalization contract retained | IMPLEMENTED — 9f3ed5a; CI stable |
| L1–L4 | see Section 6 (all CLOSED/FIXED; remaining: E1 alerting, D4 history purge) | VERIFIED live 9a5a37e |

**Full-suite regression (scrubbed, CI-equivalent, master):** 5723 passed / 128 skipped / 0 failed (30:09, output `/tmp/logs/b3b4b5_full_suite_master_final.log`); B2 branch was 5703/128/0; baseline 583598f was 5665/128/4 (fda25, fixed).

**Next action (wave-complete):** founder walkthrough + LB-001 sign-off (D1) against Section 1 P1s (B16 auth middleware, D8 integration honesty, E1 alerting, D4 purge/privacy), then remaining Section 2 blockers. `PUBLIC_LAUNCH_READY = FALSE` until LB-001 + all mandatory gates verified.

**L4 remediation (2026-10-13, narrowly scoped, index-only):**
15 legacy artifacts were git-tracked under `uploads/`, `static/uploads/`,
`app/static/uploads/` (3 founder itinerary PDFs, 1 audit PDF, 11 test/probe
files; 699,867 bytes). Root cause: pre-ignore-era additions; the app's runtime
storage root is `RUNTIME_DATA_ROOT` (shunya_data — outside the repo), so no
live code path reads or writes these tracked files. Remediation on branch
`zero-gap-03-b4-b5` (PR #9): index-untracked the exact 15 paths via a
verified manifest (15 unique, tracked, intended dirs, 0 malformed); full
backup snapshot with per-file sha256 verified before staging
(`/home/shunya-deploy/backups/legacy_repo_uploads_20261013/`); after staging:
0 files missing, 0 checksum mismatches, staged diff = exactly 15 deletions +
register row, no unrelated changes. `.gitignore` already covers `uploads/`
(any level) and `static/uploads/`. No file deleted, no history rewrite, no
force-push, no visibility change. History purge + repo privacy remain
founder-pending (D4).

---

*Child-of-record:* this umbrella supersedes nothing; `SHUNYA_100_GAP_REGISTER.md`, `SH_M6_M15_BLOCKER_REGISTER.md`, `SHUNYA_MASTER_MILESTONE_TRACKER.md` remain the detailed authorities. Tracker BLOCKERS section-marked stale entries updated in the tracker on the next governance pass.