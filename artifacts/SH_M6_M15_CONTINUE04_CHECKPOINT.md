# SH-M6→M15 CONTINUE-04 — TRUTHFUL COMPLETION LEDGER

**Campaign**: SH-M6→M15-CONTINUE-04
**Status vocabulary**: NOT STARTED / IMPLEMENTED / PARTIALLY VERIFIED / FULLY VERIFIED /
CI VERIFIED / PRODUCTION VERIFIED / CERTIFIED. No other words are used.

This artifact SUPERSEDES `SH_M6_M15_CONTINUE02_CHECKPOINT.md` and
`SH_M6_M15_PRODUCT_LEDGER.md` for status purposes. Those files are preserved, not edited.

---

## A. STARTING TRUTH (CONTINUE-04 entry, measured)

| Item | Value |
|---|---|
| HEAD | `d679fd2b752d2a5a13546a35dce7520c91a6c783` |
| origin/master | `d679fd2…` (equal) |
| Working tree | clean |
| CI for `d679fd2` | run `35548918567` — **FAILURE** (1 failed, 5405 passed, 1018s) |
| Failing test | `tests/journeys/test_gj12_ai_action_journey.py::test_ai_action_journey` at step `executor_skipped_nonregistered` |
| `7012da4`, `8225aec` | **CANCELLED** — not evidence |
| Production | `backend_release_sha=48f6eb7`, `git_commit=d679fd2`, `release_type=UNVERIFIED`, `status=degraded`, **HTTP 503** (local and public) |

`d679fd2` was UNCERTIFIED and UNDEPLOYED. Recorded, not assumed.

---

## B. CLOSING TRUTH (what this session delivered)

| Item | Value |
|---|---|
| Closing commit | `37697ac70f5df4a1232508364c48b1148ddf286b` |
| CI run | `35585003509` — **OVERALL SUCCESS** (test SUCCESS, Deploy to Production SUCCESS) |
| Deployed SHA | `37697ac…` (production parity confirmed) |
| `release_type` | `CI_CERTIFIED` |
| Local `/health` | HTTP 200, `status=ok`, `release_health_verified=true`, `build_identity_matches_running_build=true` |
| Public `/health` (https://shunyaos.com) | HTTP 200 in 0.13s, same SHA, `CI_CERTIFIED` |
| Frontend/backend parity | `frontend_release_matches_backend=true` |
| Restart survival | service restarted 2026-09-21T10:08:51Z by the deploy; health uptime 219s, reports exact SHA |
| Worker parity | 3 × gthread (`--workers 3 --worker-class gthread --threads 8 --timeout 120`), identical argv |
| Public SPA | HTTP 200 |

The 503/degraded production state that existed at entry is **RESOLVED**.

---

## C. ITEM LEDGER

| # | Capability / item | Status | Evidence | Remaining gap |
|---|---|---|---|---|
| 1 | GJ-12 `executor_skipped_nonregistered` root cause | **CERTIFIED** | Root cause proven deterministic (isolation PASS vs full-suite FAIL). `ensure_runtime()` wires base action `execute`, so `ActionType.EXECUTE` IS registered; the old assertion encoded a false premise. Repaired; CI run `35585003509` SUCCESS; deployed | none |
| 2 | Runtime reset lifecycle defect | **CERTIFIED** | `reset_runtime()` left the wiring guard set → runtime permanently unwired. Fixed; guard proven RED pre-fix, GREEN post-fix; in CI + production | none |
| 3 | MemoryEngine clear outside app context | **CERTIFIED** | `Working outside of application context` on reset with DB repo bound. Fixed; covered by CI | none |
| 4 | GJ-13 failure/recovery depth | **CI VERIFIED** | Rewritten from 1 test with status-code SETS into **12 separate tests**, one per failure class, real fault injection (WSGI/DB-commit/LLM-provider). 12/12 pass; in CI run `35585003509` | production-runtime failure drills not run |
| 5 | Import ingestion truthfulness | **CI VERIFIED** | (a) validator/writer alias divergence made a real `name,email` customer CSV 100% rejected; (b) `commit_import` returned 201 "completed" with created=0/errors=[]; (c) re-import duplicated records. All three fixed; 66 import tests pass; in CI | PostgreSQL parity not run |
| 6 | G14 device + accessibility mechanism | **PARTIALLY VERIFIED** | **Real mechanism built and run**: Playwright 1.62.1 + Chromium + axe-core against production, 7 viewports (1920/1280/1366/1024/768/844/390). All HTTP 200, **no horizontal overflow**, **0 axe WCAG 2.0/2.1 A+AA violations**, 0 page errors. Only sub-44px target is the skip-link (34px) | authenticated surfaces NOT audited (workspace, empty states, dense business data); needs a credential |
| 7 | §9 `/api/v1/documents` blueprint collision | **IMPLEMENTED + guard RED-proven** | Evidence: exactly ONE colliding rule, `GET /api/v1/documents`, owned by `document_intel.api_list` (RBAC, `knowledge.view`, tenant-scoped) vs `documents.list_documents` (identity header only) — resolved silently by registration order. A THIRD surface `/api/v1/workspace/documents` (`documents_api`) is the real frontend contract. **RESOLVED**: `doc_bp` no longer registers the collection rule (implementation retained unrouted, not deleted); the ownership contract is documented in `app/document_runtime/routes.py`; `tests/test_document_route_ownership.py` pins it and was proven **RED** against the pre-fix code (2 failures) then GREEN (6 passed). 27 document tests pass | needs its own certified CI+deploy run |
| 8 | §5 empty states | **PARTIALLY VERIFIED — earlier finding RETRACTED** | The `document-browser.tsx` empty state says 'Use "Add to My SHUNYA" to upload files'. That affordance EXISTS: `<AddToShunya/>` is imported from `components/ingestion/add-to-shunya` and rendered UNCONDITIONALLY at line 359, directly above the empty state, with the label "Add to My SHUNYA" (`Add to {isOrg ? 'Panchi Club' : 'My SHUNYA'}`). An earlier claim in this session that it was a dead end referencing a non-existent control was **WRONG** — it came from grepping the literal string and missing the constructed label — and is retracted. No fix was warranted (adding a second continuation would be the clutter §5 forbids) | full empty-state audit across all surfaces still not done |
| 9 | G6 document intelligence with real documents | **NOT STARTED** | — | Bali itinerary hierarchy, supplier quote, invoice, PDF/DOCX/image, semantic organisation |
| 10 | §23 credential/history/CI-log exposure audit | **NOT STARTED** | — | — |
| 11 | §25 PostgreSQL parity | **NOT STARTED** | — | — |
| 12 | §16 G12 emotional continuity | **NOT STARTED** | — | — |
| 13 | §13/§14 G9 AI action depth | **NOT STARTED** | — | — |
| 14 | §12 M9 attention from real signals | **NOT STARTED** | — | — |
| 15 | §20 G19 human walkthrough | **NOT STARTED** | — | — |
| 16 | M5 entry → workspace | **PARTIALLY VERIFIED** | Journey test passes in CI (shell, signin, session, identity, create, visibility, trash/recover, restart, anonymous denied) | "understands what SHUNYA is / what to do next" and empty-state continuations not proven; item 8 is a concrete defect |
| 17 | M6 bring business reality | **PARTIALLY VERIFIED** | Customer + Supplier CRUD, CSV/XLSX import (now truthful), tenant isolation, journeys in CI | document intelligence with real content; semantic ingestion beyond alias mapping |

---

## D. CLASSIFICATION OF THE 9 LOCAL FULL-SUITE FAILURES (deterministic)

Full local suite: **9 failed, 5419 passed, 125 skipped (2026s)**.

All nine fail **identically on the pristine tree with this session's changes stashed**
(`git stash` A/B) → **PRE-EXISTING + ENVIRONMENTAL**, none introduced by `37697ac`.

They fail because they assert `GET /health == 200` and this host's release record was
legitimately `UNVERIFIED`/`degraded` (503). They pass in CI because CI's checkout has no
degraded release record. **This is a real test-design defect: those tests are not
hermetic — they read host deployment state.** With `37697ac` deployed the host is now
healthy, so the coupling is currently invisible — which is exactly why it must be
fixed rather than forgotten.

Affected: `tests/cortex`, `tests/decision`, `tests/orchestration`, `tests/organization`,
`tests/planning`, `tests/temporal` (all `*_loads_with_app`), `tests/test_models.py::
test_title_contains_identity`, `tests/test_rbac_enforcement.py::
test_unauthenticated_public_ok`, `tests/test_release_governance.py::
test_health_never_certifies_failed_record_read`.

---

## E. FINAL REPORT

- **A. Repository truth**: HEAD = origin/master = `37697ac…`; working tree clean at close.
- **B. CI truth**: exact SHA `37697ac…`, run `35585003509`, test SUCCESS, deploy SUCCESS, overall SUCCESS.
- **C. Production truth**: backend SHA = frontend SHA = `37697ac…`; `build_id=37697ac`; `CI_CERTIFIED`; local + public health 200; restart survived; 3 identical gthread workers.
- **D. Product truth**: only items 1–6 above have real evidence. Items 7–17 are open.
- **E. Golden journeys**: GJ-12, GJ-13 and the existing GJ set are CI VERIFIED. GJ-13 is now 12 independent proofs. Others per §27 remain unwritten.
- **F. Security**: no secrets read/printed; no production write, restart, migration or rotation performed by this session; 66 import + 127 ubme/convergence + 27/39 journey tests green.
- **G. Device**: public surface verified across 7 viewports with 0 axe violations; authenticated surfaces NOT audited (blocked on a credential).
- **H. Blockers**: (1) authenticated browser credential for device/walkthrough gates; (2) document intelligence with real documents; (3) PostgreSQL parity.

No optimistic language. Nothing above is claimed beyond its stated evidence.
