# SH-M6→M15 CONTINUE-07 — CHECKPOINT (mid-execution, honestly bounded)

**Campaign**: SH-M6→M15-CONTINUE-07 (directive: CONTINUE-07, "DO NOT CLOSE GAPS PREMATURELY")
**Date**: 2026-10-08
**Deployed/Production SHA at campaign start**: 5e0720e (CI_CERTIFIED, healthy)
**HEAD at this checkpoint**: (set at push time — this file is committed WITH the batch)
**Origin/master**: = HEAD (single push, one CI lifecycle)

---

## STATUS BOARD

### A. Worktree reconciliation — DONE (verified this session)
- `frontend/src/components/content/media-generator.tsx` 26px→44px change is an INTENTIONAL
  WCAG touch-target fix, committed in 73a9d33: `.cs-history-overflow-btn` 26x26 → 44x44
  (+ min-width/min-height, radius 6→8). Not audit residue; kept as pending product work.
  It has NOT yet passed CI/deploy — it rides the current batch.
- `artifacts/SH_M6_M15_CONTINUE04_CHECKPOINT.md` was reconciled in 73a9d33 (granular item-17 breakdown).
- This CONTINUE-07 checkpoint file is the only untracked artifact and is committed with this batch.

### B. /documents — PROVEN RED, FIXED, TESTED (CI + authenticated-runtime proof pending)
- Investigation found THREE overlapping registrations (more than the two the directive named):
  1. `main.documents_page` — GET /documents → had been switched (73a9d33) to `_serve_spa_shell()` (release-aware).
  2. `main.documents_detail` — GET /documents/<id> → `render_template("documents.html")`, a template that
     NEVER existed → **proven RED this session**: a live `TemplateNotFound: documents.html` crash
     (production 500) for every real document deep link, with the stack trace captured in the test run.
  3. `main._legacy_spa_fallback` — DUPLICATED both rules (`/documents`, `/documents/<int:doc_id>`),
     serving the raw checkout dist (non-release-aware). First-registered-wins made this a latent
     order-dependent hazard. Proven by `app.url_map.bind().match()` in the new tests.
- Fix: `documents_detail` serves the SPA shell (like documents_page / /living); both duplicate
  decorators removed from `_legacy_spa_fallback`. Canonical owners are now explicit and single.
- Regression suite: `tests/test_documents_page_route_ownership.py` (6 tests) — proven RED (2 collisions +
  interactive crash), then GREEN (16 passed together with test_documents_authenticated_journey.py
  and test_document_route_ownership.py).
- Legacy surface inventory recorded: of the fallback's visible paths, only `/pipeline` resolves to the
  fallback; the others resolve to dedicated handlers (leads_list, invoices, payments, tasks_list,
  calendar_view, reports, settings, itinerary_builder, auth.team_list).
- REMAINING (not closed): authenticated runtime proof over HTTPS post-deploy; browser deep-link behavior.

### C. Media lifecycle (from 73a9d33, never CI-executed until now) — CI VERIFIED pending
- rename endpoint + 8 lifecycle tests are IN HEAD since 73a9d33, but the two failing runs died at the
  Python suite step, so the frontend gates and these tests have NOT been CI-executed yet.
- REMAINING: browser interaction, restart survival, tenant isolation through the real API, provider
  failure/recovery, frontend refresh — not closed.

### D. GJ-13 — kept as TEST-LEVEL; no PRODUCTION VERIFIED promotion.

### E. Signal→Attention — push bridge in HEAD (emit_signal → attention item); end-to-end
  business-state-change proof NOT YET executed. Not closed.

### F/G/H/I/K — NOT STARTED or not closed (semantic M6 ingestion, document intelligence depth, AI
  operating layer, human-context behavioural proof, browser journeys). Not closed.

### J. Historical credential — previous session recorded an investigation (shunya_test, test-only,
  deleted ci-cd.yml, rotation not needed). Directive requires this be verified independently, not
  inherited. Independent verification PENDING (next block). Not closed.

### L. Full-suite local timeout — investigated: CI full suite = 1122s (5454 passed, 1 DDG failure);
  earlier green run 1093s; local ~2026s (disk/tooling). CI SUCCESS remains the gate; local timeout at
  the 420s tool limit is a tooling limit, and the local run being slower is environmental.
  The DDG failure cause is now understood/fixed (below), not dismissed.

### CI blocker (this batch's core fix) — ROOT-CAUSED
- Run 37770012008 (51e9c9f): **failure** — exactly 1 failed test:
  `test_universal_research.py::TestRealExternalProvider::test_real_provider_returns_results`
  → `DuckDuckGo search failed: No results found.` (raw upstream refusal).
- Evidence: ddgs version identical (9.16.0) in the Sept-green and Oct-failing runs; the same test
  PASSED locally minutes ago (3 passing live tests); same lockfile; upstream rate-limits datacenter
  IPs (GitHub runner). External condition, not a product defect — but it was correctly failing CI.
- Fix (truthful, not weakened): live DDG tests now probe the RAW upstream; on PROVEN refusal they
  SKIP with the reason (external), and if the upstream serves but the provider returns nothing they
  FAIL (product defect). Added offline deterministic normalization/filter/failure tests
  (`TestDuckDuckGoProviderNormalizationContract`) + shared `tests/ddg_probe.py`. Upgraded the two
  vacuous live tests in test_connector_certification.py to the same contract.
- Also: CI now pins Node 22 for the frontend gates (runner-image node drift; local node 26 breaks a
  jsdom test with an identical lockfile — reproducibility requires the pin).

## WHAT IS ACTUALLY PROVEN (this session)
- documents: RED (collisions + 500 crash w/ stack trace) → GREEN (16 passed) locally.
- provider: refusal classification + offline contract (84 passed incl. both search test files).
- frontend gates: eslint governance PASS (459≤460), tsc PASS locally.
- worktree: media-generator change reconciled & intentional.

## WHAT REMAINS UNPROVEN (explicitly)
- CI for this batch (next run), deploy, exact-SHA parity, authenticated /documents runtime proof.
- Everything in F/G/H/I/K + C-remainder + E end-to-end + J independent verification.
- Local vitest: 3 failures in onboarding-url-truth.test.ts under node 26 (env-specific; CI's npm ci
  with identical lockfile passed it in Sept). CI remains the authority; flagged, not dismissed.

## NEXT EXECUTION BLOCK (after CI green)
1. Deploy + SHA chain verification + health.
2. Authenticated /documents runtime proof (cert tenant, HTTPS) + media lifecycle runtime proof.
3. J: independent credential-history verification.
4. E: signal→attention real loop; then F (semantic M6), G (doc intelligence), H (AI layer), K (browser).
