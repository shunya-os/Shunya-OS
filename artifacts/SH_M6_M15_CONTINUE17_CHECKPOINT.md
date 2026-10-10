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
- G3 Phase 6 — Frontend integration (6 items)
- G3 Phase 7 — Observability (remaining)
- G10 — Frontend wiring
- G11 — Auth gates completion
- G12 — Founder Acceptance / Launch Readiness

## G3 Phase 1 — Critical Connectivity (ALL DELIVERED)

| Item | Status |
|------|--------|
| 1.1 — cross_boundary_routes blueprint | ALREADY DONE (registered in app factory) |
| 1.2 — intelligence_routes blueprint | INTENTIONALLY ARCHIVED (single canonical path) |
| 1.3 — Provider chain consolidation | DELIVERED (commit 05d543f) |
| 1.4 — Context enrichment | DELIVERED (commit d06b87f) |
| 1.5 — Durable memory bridge | DELIVERED (commit 25e27db) |
| 1.6 — Conversation persistence | DELIVERED (commit c8b7d48) |

## G3 Phase 2 — Context & Security Foundation (ALL DELIVERED)

| Item | Status |
|------|--------|
| 2.1 — Enrich ContextFrame with permissions | DELIVERED (commit e8f2ae1) |
| 2.2 — PERSONAL vs ORGANIZATION types | DELIVERED (workspace_type in ContextFrame) |
| 2.3 — workspace_type filter in retrieval | DELIVERED (commit 2f2280c) |
| 2.4 — Cross-boundary authority in ask() | DELIVERED (wired in cross_boundary.py + routes) |
| 2.5 — Action classification registry | DELIVERED (commit e8f2ae1) |
| 2.6 — RBAC gate on _handle_execute | DELIVERED (commit 0dd96b6) |
| 2.7 — ExecutionAuthorityEnforcer wiring | DELIVERED (tool_registry permission checks) |
| 2.8 — Evidence transformation enforcement | DELIVERED (EvidenceTransformationGuard) |

## G3 Phase 3 — Knowledge Graph Wiring (ALL DELIVERED)

| Item | Status |
|------|--------|
| 3.1 — RelationshipIntelligence | DELIVERED (provider_wiring.py) |
| 3.2 — KnowledgeIntelligence (UCP-04) | DELIVERED |
| 3.3 — FinancialIntelligence | DELIVERED |
| 3.4 — OperationsIntelligence | DELIVERED |
| 3.5 — SalesIntelligence | DELIVERED |
| 3.6 — MarketingIntelligence | DELIVERED |
| 3.7 — Cross-object relationship search | DELIVERED |
| 3.8 — Universal search → AI integration | DELIVERED |

## G3 Phase 4 — Proactive Intelligence (ALL DELIVERED)

| Item | Status |
|------|--------|
| 4.1 — SignalBridge to SuggestionsEngine | DELIVERED (proactive.py) |
| 4.2 — Overdue commitment suggestions | DELIVERED |
| 4.3 — Unusual sales change alerts | DELIVERED |
| 4.4 — Financial anomaly alerts | DELIVERED |
| 4.5 — Operational exception alerts | DELIVERED |
| 4.6 — Observations in suggestion pipeline | DELIVERED |
| 4.7 — Evidence-based recommendations | DELIVERED |
| 4.8 — Confidence/source/timestamp per signal | DELIVERED |

## G3 Phase 5 — Learning & Memory (ALL DELIVERED)

| Item | Status |
|------|--------|
| 5.1 — Observation → memory ingestion | DELIVERED (learning.py) |
| 5.2 — 8 engines in feedback loop | DELIVERED |
| 5.3 — Controlled learning loop | DELIVERED |
| 5.4 — User feedback signals (API) | DELIVERED (POST /api/v1/feedback) |
| 5.5 — Evidence → memory + knowledge | DELIVERED |
| 5.6 — Execution outcome → memory | DELIVERED |