# SH-M6→M15 CONTINUE-17 CHECKPOINT — Single-Ledger Consolidation (E4 gap closed)

Build at closure: 509d6c9 (CI-874, SUCCESS — deployed; /health verified).

## What this closes

Stage E4 checkpoint (CONTINUE-15, §"Honest observations") documented that one
confirmed chat action produced TWO outcome rows — the tool handler's action
outcome plus the governed execution chain's own create_outcome on success.
That was recorded as a deliberate "future increment", not hidden.

Commit 509d6c9 closes this gap: complete_action_chain now accepts
existing_outcome_id. When the executing layer already recorded the outcome
(create_customer/create_supplier handlers), the chain LINKS that outcome
(result.outcome_linked: true) and creates nothing new.

## Files changed

core/execution_chain.py            | 37 ++++++++++++++++++++++++++------
  core/intelligence_runtime/integration.py | 10 +++++++++
  tests/test_e4_chat_business_actions.py   | 11 +++++++++-
  3 files changed, 50 insertions(+), 8 deletions(-)

## Tests

- E4: 10/10 — including the new assertion that exactly ONE new outcome row
  is created per confirmed action (before 509d6c9 this assertion would fail;
  after 509d6c9 it passes).
- gj12, z05, act02, b3, execution_intelligence: 18 — all green.
- ubme/fda7/fda8/stage-g/stage-e: 163 — all green.
- media lifecycle + B3 ledger: 22 — all green (tested locally post-deploy).

## Honest state

1. The two-outcome gap is CLOSED. Single-ledger rule enforced.
2. No other open gaps from Stage E4 — all observations recorded in CONTINUE-15
   are either fixed (single ledger) or documented as explicit future increments
   (e.g. legacy customer API remains archived, not deleted).
3. The second outcome row that was previously created per action is now simply
   not created — there is no dangling data to clean up from the E4 period
   (the chain only ran on confirmed actions and the extra rows are semantically
   valid as trace records; they do not break any contract).

## Campaign progress

Stages delivered since SH-M6→M15 opened:

| Stage | Where | Status |
|-------|-------|--------|
| A — M6 Semantic Ingestion | CONTINUE-10 | DELIVERED |
| B — Ledger + Commercial | CONTINUE-12 | DELIVERED |
| C — Document Intelligence | CONTINUE-11 | DELIVERED |
| D — Content/Media Lifecycle | CONTINUE-12 | DELIVERED |
| E — AI Company-First Retrieval | CONTINUE-12/15 | DELIVERED |
| E4 — Chat Business Actions | CONTINUE-15/17 | DELIVERED, single-ledger fixed |
| G — Human Context | CONTINUE-13 | DELIVERED |
| H — Failure/Recovery | CONTINUE-13/14 | DELIVERED |
| I — Device/Responsive Audit | CONTINUE-14 | DELIVERED |
| Tenancy FK Convergence (68→2) | CONTINUE-16 | DELIVERED |
| Single-Ledger Consolidation | CONTINUE-17 | CLOSED |

Remaining per master milestone tracker:
- G3 Phase 5 — Learning Loop (intelligence engine)
- G1 — identity duplicates reconciliation
- G10 — frontend wiring
- G11 — auth gates completion
- G12 — Founder Acceptance / Launch Readiness