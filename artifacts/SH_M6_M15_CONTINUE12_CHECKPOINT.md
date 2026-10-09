# SH-M6→M15 CONTINUE-12 CHECKPOINT — STAGES B, D, E (first slice)

Date: 2026-10-09
Campaign: SH-M6→M15 master directive
Certified build at closure: 302da15 (CI-15, SUCCESS — deployed; /health verified).

## Delivery chain for this block

| SHA | Content | CI run | Result |
|-----|---------|--------|--------|
| dc8aa3d | Stage E company-first retrieval (canonical provider, shared search core, context propagation, knowledge scoping) | 37937739453 | test FAILED: 2 g11_e2e search tests (org-scoping hid NULL-org rows on CI's shared postgres) — deploy never ran, production untouched |
| 302da15 | NULL-org legacy rows stay searchable (fix) | 37940854630 | SUCCESS — deployed; restart survival + E2 re-test verified below |

Also superseded: 5e8122d (Stage C evidence docs — carried by CI-14/15 trees).

## What was verified / built since CONTINUE-11

### Stage B (business reality coverage) — evidence in browsers
- B4 Sales/commercial: created "Bali Honeymoon Opportunity — Oct 2026"
  (INR 2,50,000) through the Commercial workspace UI; empty state guided the
  action ("No opportunities yet. + Create Opportunity"); the object renders
  with commercial state (Confidence 50%, Discovered) and is API-confirmed
  (/api/v1/commercial/opportunities, id 8).
- B5 empty states observed: Commercial ("+ Create Opportunity"), Trash
  ("Items you trash appear here until you recover or permanently delete
  them."), Archived ("Archived items are hidden from your working set but
  never lost.").
- B3 Ledger creation UI + fixes: shipped earlier in this campaign (commit
  0837926/6b68d92 chain — see CONTINUE-10 checkpoint).

### Stage D (content/media lifecycle) — evidence in browser
- Full lifecycle round-trip on real content items (Content Studio → History):
  Active 2 → Archive → Archived 1 → Restore → Active 2; Move to trash →
  Trash 1 (with "Recover from trash" + "Delete permanently" controls) →
  Recover → Trash 0. Counters updated live; truthful empty states confirmed.
- Media tab: "Media generation provider unavailable. Generation may fail." —
  the truthful D2 provider-unavailable surface (no fabricated assets).
- D3 (org-0 historical assets 12–32): untouched (frozen, as directed).

### Stage E (AI operating layer) — defect found + fixed + tests
- Live probe 1 (company data): asked about the just-created opportunity →
  "insufficient evidence" — company-first retrieval GAP. Root cause chain:
  (a) universal search config listed non-existent columns for
  CommercialOpportunity → the object type was silently skipped;
  (b) the AI retrieval had NO canonical-objects provider at all;
  (c) the chat path dropped identity/org context before retrieval;
  (d) the knowledge provider loaded documents unscoped (cross-tenant risk).
- Fixed in dc8aa3d: shared search core + canonical provider (relevance 0.85,
  above objects/memory/internet, below business graph) + authenticated
  context propagation + knowledge scoping + 4 tests.
- Live probe 2 (external): "What is the capital of Mongolia?" → "The capital
  of Mongolia is Ulaanbaatar. However, based on the available evidence in
  your workspace, there is no information related to Mongolia..." — the
  internal/external distinction and uncertainty handling work.
- E2 re-test on the 302da15 deploy (CI-15) — **VERIFIED FIXED**: the same
  question now answers "The Bali Honeymoon Opportunity was created today
  during the Stage B certification walkthrough and is currently in the
  discovered stage. The related commitment, Bali Eco Honeymoon, is confirmed
  and active. No further details or updates on the opportunity are available
  at this time." — canonical retrieval (name/status/description from the real
  object) + related evidence + honest gaps. Screenshot:
  STAGE_E_RETRIEVAL_FIXED.png.

## Restart survival (verified across the CI-15 deploy restart)

- doc 23 "Raj Sir Bali Itinerary" → classification itinerary (manual
  correction persisted).
- doc 26/28 panchi_bali_itinerary → itinerary; doc 27 sundara_resorts_quote →
  quotation (reclassification persisted).
- Opportunity id 8 "Bali Honeymoon Opportunity — Oct 2026" — discovered,
  INR 2,50,000 (Stage B object persisted).
- Legacy bridge org 7 ↔ tenant 89 persisted (migration-recorded).

## Known limits

- Stage E evidence above is only the first slice (E6 needs: confirmed action
  with observable outcome, failure recovery — next rounds).
- Stage B/D/E rounds use the cert/founder workspace; object coverage for
  every B category continues in the next rounds (contacts/ledger/sales
  surfaces individually re-verified).
- Media generation remains provider-unavailable (truthful path verified; no
  fabricated success).