# SH-M6→M15 CONTINUE-13 CHECKPOINT — STAGES G, H, I (first slice)

Certified build at closure: c12ffaf (CI-20, SUCCESS — deployed; /health verified).
Also in this block's chain: 9f76d74 (CI-19; test failed on the sign-out route
contract — deploy never ran, production untouched), fixed by c12ffaf.

## Stage E follow-up (found while auditing E4)

app/ai/tool_registry.py registers REAL business tools (create_customer,
create_supplier, search_objects: validate → service → Outcome → canonical
event) at app startup — but the planner only emits ANSWER/CLARIFY steps, so no
chat path can currently SELECT those tools, and the registered keys cannot be
produced by ActionType. Recorded as the next Stage E increment: planner→tool
selection WITH a confirmation gate. Until then the honest execute handler
(not_executed) is correct, and the E6 "confirmed action" evidence remains the
import pipeline's real preview→confirm→commit→provenance loop (M6/C proofs).

## Stage G — human context (evidence on the c12ffaf deploy)

Implemented + unit-proven (8/8):
- guidance chain: ACTIVE explicit context → guidance lines → ContextFrame →
  reasoning prompt (delivery guidance only).
- corrections change guidance; expirations remove it; max two lines;
  email-scoped via PersonIdentity; silent when absent; never blocks chat.
- tenancy retarget migration for emotional_context_items + human_context_items
  (dry-run against production: functions + DDL + rollback verified).

Live demo (verified on the c12ffaf deploy):
- founder person 389 + email identity linked; explicit "frustration (waiting on
  overdue reports)" recorded via the canonical service (item 1, ACTIVE;
  tenant 7 — possible only because the retarget migration shipped).
- guidance builds: "The user recently expressed frustration. Be patient and
  direct: short, concrete answers, confirm understanding, no lecturing."
- chat probe: "What should I focus on today?" → "Based on your active
  outcomes..., prioritize the highest-impact task from the most urgent
  outcome. Pick one—execution beats planning here. Confirm if you'd like me to
  narrow it down further." — short, direct, confirmatory: the delivery
  guidance is visibly in effect (earlier answers this session were markedly
  more verbose). Screenshot: STAGE_G_BEHAVIOR_LIVE.png.
- Sign out control: visible on Home (identity + control), clicked live →
  landed on the public page; /api/v1/auth/session then reports
  authenticated:false (server session actually cleared). Screenshot:
  STAGE_I_SIGNOUT_HOME.png.
- CI-19's contract test caught the sign-out calling a nonexistent route
  (/api/v1/founder/logout); fixed to /founder/logout in c12ffaf (CI-20) and
  re-verified live.

## Stage H — failure & recovery audit matrix (evidence inventory)

| Failure class | Mechanism | Evidence |
|---|---|---|
| Network (app side) | Home offline banner: truthful + retryable; polling stops | code path + capture |
| Authentication | wrong credential → truthful rejection (no session) | live probe |
| Authorization | anonymous 401; cross-tenant 404; decorated denials with codes | runtime X1–X4 + bridge tests |
| Database | /health database:"connected"; fail-closed tenant resolution | health + resolver tests |
| Ingestion | induced failure → status "rejected", created 0; retry does not duplicate; partial is truthful | runtime C14/C15/C13 |
| Semantic extraction | broken PDF → "[extraction limited]" / "no text layer" markers; empty text stored; truthful summary | extract CLI tests + live uploads |
| Model provider | orchestrator failover chain; deterministic-first gate; fallback templates | skill + provider chain code |
| Internet retrieval | provider chain (free-first); internet vs company evidence distinction shown live | Mongolia probe |
| Event publication | non-fatal by design ("import is already committed"); attention observed | code + attention counts |
| Attention persistence | persisted items; refresh-based visibility (known limit) | sidebar counts + attention API |
| Background jobs | learning loop / telemetry non-blocking | code review |
| File handling | missing file → 404 "File not found on disk"; duplicate upload → truthful refusal | code + live duplicate probe |
| Partial execution | import partial status w/ per-row errors | service + tests |
| Deployment/restart | every deploy this campaign; restart survival verified for C/G/B objects | /health + probes |
| Model provider (live failover) | to probe: orchestrator with bad key falls through | pending probe |

Regression protection: canonical suite (5534+) every deploy; journey tests
GJ-05/06/13; bridge/dedup/G/E suites added this campaign.

## Stage I — device/responsive/accessibility (pending)

- Logout gap CLOSED (visible Sign out on Home; ships in CI-19).
- URL-after-sign-in quirk CLOSED (dcee51e; verified live: / after sign-in).
- Known limits from M9: accessibility measurements ≠ WCAG certification;
  attention visibility refresh-based.
- To audit: viewports (desktop/laptop/tablet/mobile), keyboard nav, touch,
  contrast measurements on the changed surfaces.