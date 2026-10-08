# SH-M9 → M6 CONTINUE-08 — REAL SIGNAL → ATTENTION → HUMAN ACTION

**Date**: 2026-10-08 (continues from certified 59b9a55)
**Campaign chain**: 5e0720e → 618b3da → 1772ac4 → 59b9a55 (CONTINUE-07) → dbf74fc (this block's deployed chain)

## THE ARCHITECTURAL FINDING (why the gap existed)

- The runtime loop named in the directive (`app/runtime/loop.py::run_cycle`) is
  **documented as superseded/legacy** (execution-engine working memory over the legacy
  `objects` table) — wiring attention there would have fixed the wrong subsystem.
- The canonical event architecture exists: `app/shunya/infrastructure/event_bus.py`
  (`CanonicalEvent` with tenant/workspace/actor + idempotency, retry, DLQ) with a
  wildcard consumer pattern (`core/awareness/subscriber.py` is the precedent).
- The ONE canonical business-event producer in production is the ingestion pipeline
  (`IngestionService → CanonicalEvent → EventBus.publish`). It was UNCONSUMED for
  attention: no subscriber existed, so no real business event ever created an
  AttentionItem without UI access.

## WHAT WAS BUILT (dbf74fc, deployed 19:57:08Z)

- `core/attention/subscriber.py` — canonical EventBus subscriber bound at GATE 10
  (idempotent). Consumes `ingestion:*` events and creates AttentionItems ONLY for
  deterministic review conditions: outcome `rejected` (priority 4) / `partial` /
  `pending` (priority 3); `accepted` with unknown confidence (priority 3).
  **Canonical-owner gating fails closed**: no `tenant_id` or no `actor_id` → skipped —
  never a synthetic tenant, never an invented watcher. Deduplicated per active item
  (org + source=event + ingestion id). `AttentionSource.EVENT` added.
- `tests/test_attention_event_chain.py` (9 tests): event→item with provenance,
  priority mapping, dedup, no-tenant skip, no-actor skip, non-review passthrough,
  tenant isolation, REAL IngestionService end-to-end, and the persistence-failure
  matrix (ingestion unaffected, error logged, next event recovers).

## RUNTIME PROOF (over HTTPS + production app+DB, deployed dbf74fc)

Raw output: `artifacts/SH_M6_M15_CONTINUE08_ATTENTION_PROOF.txt` (14/15 PASS).

- A1–A5 — a REAL ingestion in the certification tenant produced a canonical event
  (`event=4680b3cb-…`) and the subscriber persisted AttentionItems (ids 3 and 4)
  **without any UI access**, with canonical owner (org 278, identity sid_5ef3…) and
  event-linked provenance. This is the chain the directive demanded.
- B0–B2 — HTTPS: certification session sees the item; **anonymous → 401**.
- B3b/B4/B5 — **cross-tenant isolation**: a REAL second identity (engine founder
  `sid_a3cd…`) in its REAL organization (org 7) gets **403 “Item belongs to a
  different organization”** for BOTH read and resolve (app-level, same production
  app object + database). Tenant B cannot see or resolve Tenant A attention.
- B6–B8 — resolve → the item leaves the active list; remains auditable as `resolved`.
- B3 (FAILED, flagged): the archived `~/.shunya/founder-credential.txt` did NOT
  authenticate over HTTPS (401). Not brute-forced — treated as an archived/rotated
  credential and a hygiene item; the cross-tenant proof was completed via B3b/B4/B5.

## M9 STATUS BY EVIDENCE LAYER (independently tracked)

- EVENT→ATTENTION ARCHITECTURE: IMPLEMENTED ✓ · TESTED ✓ · CI VERIFIED (run 37832940797) ✓
- RUNTIME VERIFIED ✓ (service+DB+bus; HTTPS visibility/resolve) — EXCEPT the UI leg
- TENANCY VERIFIED ✓ (owner gating + 403 cross-tenant detail + anonymous 401)
- FAILURE VERIFIED ✓ (gating skips; persistence failure isolated; dedup; stale truth)
- RECOVERY VERIFIED (unit ✓; runtime = restart survival in flight, below)
- UI VERIFIED ✗ · USER-JOURNEY VERIFIED ✗ — **the Home does not yet consume
  /api/v1/attention** (no frontend consumer exists); the Home’s “WHAT MATTERS NOW”
  reads /api/v1/intention. The wiring (intention response surfacing persisted event
  attention + component rendering + browser proof) is the **remaining M9 gap**.
- RESTART VERIFIED — pending: AttentionItems 2 and 4 left ACTIVE deliberately; the
  deploy restart of this checkpoint’s commit must preserve them (verify → resolve).
- Also noted: attention list filters by workspace when `X-Workspace-Id` is sent;
  event-sourced items are organization-level (workspace_id NULL). The Home wiring
  must decide this filter semantics explicitly (org-level items must not vanish
  when a workspace header is present).

## ITEM 11 — LEGACY ORG-0 MEDIA DATA (read-only forensics; NOTHING touched)

- The media assets table contains **21 rows, ALL organization_id=0** (ids 12–32),
  all identity `sid_a3cd…` (engine founder), workspace `""`, all `runtime_state=generated`
  (real generated images), created **2026-08-28 → 2026-09-09** — i.e., **entirely
  BEFORE the ownership hardening commit 5e0720e (Sep 23)** whose message says
  “All 6 media service functions now filter by organization_id … closing a
  cross-tenant information leak”. No asset has been created since.
- Source/creation path: the pre-hardening server-side default (org 0, no workspace) —
  the founder's own trial generations through the product UI of that era.
- Accessibility today: org-scoped queries (`organization_id == session org`) exclude
  org-0 rows for every real tenant → these rows are **orphaned/unreachable in the
  product** (list/get/lifecycle all scope by org+identity). They do NOT violate the
  current code path (which can no longer produce org-0 rows — fail closed).
- Provenance recoverable: partial — identity, timestamps, generation_job_id, prompts.
  No org/workspace provenance ever existed for them.
- **Proposed remediation (NOT executed — requires founder approval, destructive):**
  `UPDATE m6_media_assets SET organization_id = <founder org 7>, workspace_id = <a
  canonical workspace of org 7> WHERE id IN (12..32)` — attributes the founder's own
  legacy assets to his real tenant. Alternative: leave as-is (orphaned, documented).
  Decision required before any mutation.

## M6 / SEMANTIC INGESTION / DOCUMENTS / AI / HUMAN-CONTEXT

NOT STARTED in this session (M9 primary objective first, per directive §7). No
simplistic-heuristic work was added; the real ingestion contract remains the blueprint
(upload → inspect → understand → identify → map → ambiguity → preview → confirm →
canonical persistence → provenance → result → correction → recovery).

## NEXT EXECUTION BLOCK

1. Verify AttentionItems 2 & 4 survived this push's deploy restart → resolve → record
   (RESTART VERIFIED), leaving zero active cert-tenant attention.
2. Wire the Home leg: surface persisted event attention in the real UI (+ filter
   semantics), then browser proof (login → see item → understand → act → resolved).
3. Then begin semantic M6 (Customer/Supplier first) per directive §7–§10.
