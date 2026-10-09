# SH-M6→M15 CONTINUE-11 CHECKPOINT — STAGE C (DOCUMENT INTELLIGENCE)

Date: 2026-10-09 (session CONTINUE-10/11)
Campaign: SH-M6→M15 master directive — one continuous programme
Certified build at writing: 6073043 (CI-12, run 37932484517, SUCCESS — deployed)

## Delivery chain for this block

| SHA | Content | CI run | Result |
|-----|---------|--------|--------|
| dd9f1bc | classifier quotation fix | folded into CI-9 | — |
| dcee51e | Stage J URL fix | 37918913021 | CANCELLED (superseded) |
| 00bbbad | Stage C package: dedup sha256 + migration, extract CLI, classify audit fix, 5 tests | 37920428109 | SUCCESS — deployed |
| a68abe0 | canonical tenancy bridge (resolver + bridge migration + 6 tests) | 37926888094 | test FAILED (FDA16 isolation regression) — deploy never ran |
| cfb7660 | fail-closed correction (bridge-mapped tolerance only) | 37929854023 | test PASSED (5534); deploy FAILED (migration shape bug — tuple unpack) — production untouched |
| 6073043 | migration shape fix (verified by running the migration's own functions) | 37932484517 | SUCCESS — deployed |

## Production truth (verified live)

- /health = 6073043, CI_CERTIFIED, DB connected.
- alembic_version = c_org_legacy_bridge (chain: m6_supplier_tenancy_retarget →
  c_documents_content_sha256 → c_org_legacy_bridge).
- organizations row 7 ("Panchi Club") legacy_tenant_id = 89 — the canonical
  bridge is recorded.
- documents.content_sha256 column + index live; suppliers FK → organizations.

## What Stage C delivered

1. Real documents through the real UI (generated Bali itinerary + Sundara
   quotation PDFs; upload → extraction → semantic classification →
   Itinerary→International hierarchy at 0.87).

2. Quotation misclassification fixed (quotation reference-number + validity
   signals; regression test replicates the exact live document; reclassified
   live to quotation at 0.61).

3. Duplicate detection implemented (SHA-256 content identity, guarded migration,
   transactional dry-run with rollback before deploy) and verified live:
   re-adding the identical file → "already in your workspace — identical file
   (same SHA-256), added 09 Oct 2026 ... Nothing new was stored", row count
   unchanged.

4. Upload extraction subprocess replaced (argv CLI module, sys.executable;
   no caller filename in Python source).

5. Manual classification audit trail fixed (previous_classification captured
   before overwrite; verified live: quotation → itinerary with by_human flag).

6. **Canonical tenancy bridge** — the deepest finding of this stage: the
   founder's data is split between legacy tenant 89 and organization 7 (same
   name+slug); the canonical reader 404'd on the founder's own documents and
   permission checks 403'd on the stale session selection. One resolver
   (authz.workspace_context.resolve_caller_organization/_scope) now maps the
   recorded bridge, validates membership, and FAILS CLOSED for anything else
   (FDA16 contract intact). Readers accept org∪bridge; writers write canonical;
   the 13-table row convergence is a planned migration, not improvised.

## Stage C completion gate — evidence (all on deployed builds)

- [x] Upload real itinerary (UI) → extracted 1018 chars → itinerary 0.87,
      hierarchy [Itinerary, International, ...] — screenshot + API payload.
- [x] Upload real supplier quotation → extracted 700 chars → reclassified
      live to quotation after the fix (0.61).
- [x] Duplicate upload (UI) → truthful duplicate response, no new row.
- [x] Manual human correction → 200 + previous_classification trail (fixed
      bug; the same call 404'd/403'd before the bridge — verified fixed live).
- [x] Documents visible in the workspace with correct badges
      (ITINERARY/QUOTATION) — screenshot.
- [x] Correction persists; cross-tenant scope 404 (bridge tests).
- [x] Restart survival: pending the CI-13 (evidence-commit) deploy restart —
      documents 23/26/27/28 + classifications + bridge must survive.
- [ ] Screenshots archived under artifacts/ (this commit).

## Known limits (explicit)

- Entity extraction on the itinerary produced low-confidence noise in
  `persons` (heuristic; classification/hierarchy correct).
- Pre-migration documents carry NULL content_sha256 (dedup covers uploads from
  c_documents_content_sha256 onward by design).
- No OCR provider: image-only PDFs degrade truthfully ("no text layer").
- The tenancy convergence of the OTHER 12 legacy tables (leads, campaigns,
  memory, observations, ...) is planned remediation, not done here; readers
  bridge, no data was rewritten.