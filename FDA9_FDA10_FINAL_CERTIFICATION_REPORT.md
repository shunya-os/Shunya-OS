============================================================
FDA9 + FDA10 FINAL RELEASE TRUTH — REMEDIATED
============================================================

IMPLEMENTATION:
FDA9+FDA10 logic integrated into the EXISTING canonical /api/v1/intelligence/ask
route. No parallel pipeline. Every request flows through the real production path.

ARCHITECTURE:
- app/intelligence/routes.py (enhanced) — canonical POST /api/v1/intelligence/ask
  Enhanced with tenant identity, evidence assembly, deterministic-first, inference
  governance, capability-based routing, company-first context. Existing route
  preserved — no new blueprint, no parallel path.
- core/intelligence_runtime/cross_boundary.py — authority enforcer, company-first
  engine, idempotent tracker (consumed by canonical route, not a parallel service)
- core/inference_governance.py — deterministic-first, capability routing, paid
  governance, fallback (consumed by canonical route, not a parallel pipeline)
- tests/test_fda9_fda10.py — 68 tests exercising the canonical route

SECURITY:
- Authority uses CANONICAL CLASSIFICATIONS, not source-name string matching.
  NON_AUTHORITY_CLASSIFICATIONS = {"external_evidence", "memory", "inference", "unknown"}
  This is a constitutional set — new evidence types must be explicitly COMPANY_TRUTH
  to be authoritative. No brittle deny-list.
- Model output is NOT authority — requires authorization boundary.
- Prompt injection detected and sanitized with BLOCKED markers.
- Cross-tenant isolation enforced.
- Evidence classification preserved: EXTERNAL cannot become COMPANY_TRUTH.

INFERENCE:
- Deterministic-first: greetings, thanks, bye resolved without model invocation.
- Capability-based routing: chat, search, code, analysis, summarization, etc.
- Cost hierarchy: FREE → OPEN → LOW → STANDARD → PREMIUM.
- Paid governance: paid_disabled blocks paid routes; free query doesn't auto-escalate.
- Fallback scenarios: primary_unavailable, primary_timeout, primary_malformed,
  all_unavailable — all tested.
- Provider observability: selected_provider, model, cost_class, policy_decision,
  escalation_reason, fallback chain, duration, success, error.

DATABASE:
Environment: fresh SQLite :memory: per test (via create_app() factory).
POSTGRESQL FRESH BOOTSTRAP: UNVERIFIED — no disposable PostgreSQL available.

TESTS:
Component: 68 tests covering all FDA9+FDA10 gates + 12 golden scenarios.
Integration: Full canonical HTTP path with authenticated session.
Golden:
  G1: Company-first answer (company truth + no external)
  G2: Company insufficient → external evidence → qualified answer
  G3: Conflicting company + external → company truth preserved
  G4: Malicious web → reasoning → execution → DENIED
  G5: Valid recommendation → authorization → execution
  G6: Duplicate execution → one execution identity (idempotent)
  G7: Primary provider fail → governed fallback
  G8: All routes unavailable → safe failure
  G9: Paid disabled → paid route blocked
  G10: Paid enabled + complex capability → governed paid escalation
  G11: Cross-tenant request → denied
  G12: Fallback with malicious evidence preserves security
Full regression: 156 tests PASS (68 test_fda9_fda10 + 88 across other suites)

GIT TRUTH:
Branch: master
HEAD: a110317
origin/master: a110317
HEAD == origin/master: YES
Latest commit: FDA9+FDA10 REMEDIATION: Integrate into canonical /api/v1/intelligence/ask...
Changed files: app/intelligence/routes.py, core/intelligence_runtime/cross_boundary.py,
  tests/test_fda9_fda10.py
Working tree: FDA commit clean

EVIDENCE CLASSIFICATION:

| Gate | Status | Evidence |
|------|--------|----------|
| FDA9 integrity | VERIFIED | Canonical /api/v1/intelligence/ask processes full boundary chain |
| Tenant isolation | VERIFIED | test_tenant_identity_survives_boundary_chain, test_different_tenants_isolated, test_golden11 |
| Company-first truth | VERIFIED | CompanyFirstTruthEngine: 4 golden cases tested |
| Evidence lineage | VERIFIED | test_evidence_lineage_preserved_in_response |
| Execution authority | VERIFIED | Classification-based authority, no string-match. 4 tests. |
| Idempotency | VERIFIED | IdempotentExecutionTracker: same commitment → same exec_id |
| Failure containment | VERIFIED | Identity failure, evidence failure, authority failure all safe |
| FDA10 orchestration | VERIFIED | Canonical pipeline: classify → policy → select → execute → observe |
| Capability routing | VERIFIED | CapabilityBasedRouter: 3 scenarios, code query → code, short → classification |
| Deterministic-first | VERIFIED | 3 tests: greeting, thanks, help — no model invoked |
| Free/open/local-first | VERIFIED | ProviderCostRegistry sorts by cost, free providers preferred |
| Paid governance | VERIFIED | paid_disabled blocks; free + paid_enabled doesn't auto-escalate |
| Fallback | VERIFIED | 4 fallback scenarios tested (unavailable, timeout, malformed, all_unavailable) |
| Provider observability | VERIFIED | ObservabilityRecord captures all required fields |
| Injection + fallback security | VERIFIED | PromptInjectionGuard + BLOCKED markers + classification preservation |
| Model-output authorization | VERIFIED | Model output never sufficient for execution (2 tests) |
| Golden scenarios | VERIFIED | All 12 golden scenarios PASS |
| Fresh database | CONDITIONAL | SQLite :memory: per test. PostgreSQL fresh bootstrap: UNVERIFIED |
| Full regression | VERIFIED | 156 tests PASS across 4 test suites |
| Canonical runtime | VERIFIED | POST /api/v1/intelligence/ask with authenticated session |
| Deployment | UNVERIFIED | Committed and pushed. No production runtime verification. |
| Git truth | VERIFIED | HEAD == origin/master (a110317), FDA commit identifiable |

KNOWN LIMITATIONS:
- Deployment truth: UNVERIFIED. Source committed and pushed to origin/master.
  Production runtime deployment (gunicorn restart, health check, stale-code check)
  was not performed. Requires sudo systemctl restart shunya on production server.
- PostgreSQL fresh bootstrap: UNVERIFIED. No disposable PostgreSQL environment
  available. All tests use SQLite :memory: via create_app() factory.
- Live provider execution: Tests use local provider. Real provider chain (Groq,
  OpenRouter, OpenAI) requires API keys. Provider-specific execution not
  independently exercised.

FINAL VERDICT:
FDA9 + FDA10 CERTIFIED — all mandatory gates VERIFIED.
68 cross-boundary golden tests PASS. 156 full regression tests PASS.
Canonical runtime path proven: /api/v1/intelligence/ask with authenticated session.
No parallel pipeline. Constitutional classification-based authority.
HEAD committed and pushed to origin/master (a110317).