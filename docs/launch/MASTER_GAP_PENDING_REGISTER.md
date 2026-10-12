# SHUNYA — MASTER GAP & PENDING REGISTER (SUPERSET, ALL SOURCES)

**Date:** 2026-10-11 (consolidated; baseline refreshed 2026-10-12 — ZG-03 Wave A)
**Repository:** shunya-os/Shunya-OS @ master **26b592e** (CI_CERTIFIED, deployed; prior reference 6b5767f)
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
| H4 | test_universal_research live-provider flake (DDG) | Failed once in CI on docs-only push; rerun green | **Make resilient:** provider-unavailable should skip or assert truthfully, not fail the deploy |
| H5 | alembic offline `--sql` unusable (alembic.ini placeholder; offline path ignores DATABASE_URL) | env.py offline branch | Tooling gap — fix offline URL resolution |
| H6 | Migration verification method | r6b28 verified via live alembic_version + columns post-deploy | Add a deploy-step column assertion for schema-bearing migrations |
| H7 | Certification-tenant credential file stale (server rejects); vault login works | ~/.shunya/certification_login.txt vs vault_67340bf9c378 | Rotate/refresh the file to the vault credential |
| H8 | `gh run watch | tail` masks exit code (watcher discipline) | This session | Use explicit exit-code capture (done in rerun watcher) |

---

## SECTION 6 — LIVE PRODUCTION DEFECTS (observed, not yet fixed)

| # | Defect | Evidence | Sev |
|---|--------|----------|-----|
| L1 | `/api/v1/analytics/dashboard` returns 500: relation `ai_execution_records` does not exist — model/table drift, 12 errors/24h unalerted | journald (Oct 10 20:31–20:37); E1 context | P1 — fix + alerting |
| L2 | "Background outcome review failed: Working outside of application context" recurring in journald | journald (Oct 11) | P2 — background task without app context |
| L3 | Public /health + /metrics expose deployment metadata unauthenticated | live curl; HEALTH_TOKEN unset | P3 (E8) |
| L4 | 8 user files (PII itineraries) git-tracked in uploads/, repo PUBLIC | git ls-files; gh visibility | P1 (E6) |

---

## SECTION 7 — FOUNDER-PENDING DECISIONS (numbered for sign-off)

| # | Decision | Context | Recommendation |
|---|----------|---------|----------------|
| D1 | **LB-001 founder acceptance** — walkthrough + sign-off ceremony | G12 empty | Schedule 1-day walkthrough against Section 1 P1s after remediation wave 1 |
| D2 | **S-006 branch protection** | Verified absent | Enable: require CI status check + PR review on master, disable force-push |
| D3 | **E18 KYC/age-verification method** | Gate records verification outcome only | Decide: documentary KYC provider vs self-attestation; until then policy is admin-attested |
| D4 | **E6 secrets purge / repo privacy** | .env + PII in public history | Options: (a) purge history (filter-repo) + rotate, (b) make repo private; recommend (a)+(b) |
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

*Child-of-record:* this umbrella supersedes nothing; `SHUNYA_100_GAP_REGISTER.md`, `SH_M6_M15_BLOCKER_REGISTER.md`, `SHUNYA_MASTER_MILESTONE_TRACKER.md` remain the detailed authorities. Tracker BLOCKERS section-marked stale entries updated in the tracker on the next governance pass.