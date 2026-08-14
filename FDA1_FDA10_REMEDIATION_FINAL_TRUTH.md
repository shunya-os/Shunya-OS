============================================================
FDA1–FDA10 REMEDIATION FINAL TRUTH
============================================================

GIT TRUTH:
  HEAD: 16c3aacc9aebbf03531b75a8be530c3c79de378f
  origin/master: 16c3aacc9aebbf03531b75a8be530c3c79de378f
  HEAD == origin/master: YES
  Latest commit: FDA1-FDA10 FORENSIC REMEDIATION: Remove parallel paths,
    wire authority + governance into canonical route, fix fixtures
  Working tree: FDA remediation commit clean

DEPLOYMENT TRUTH: VERIFIED
  Running gunicorn on port 5001 with new PIDs (3742516-3742525).
  Confirmed:
    - /api/v1/cross-boundary/ask → 404 (parallel route removed)
    - /api/v1/intelligence/traces → 405 on POST (route exists, method enforced)
    - /api/v1/intelligence/ask with session → 200, deterministic response
    - Pipeline stages: tenant_identity → evidence_assembly → execution_authority → inference_governance

DATABASE TRUTH:
  Environment: PostgreSQL (postgresql://shunya:***@localhost:5432/shunya_db)
  Migration head: 0005_fda4_identity_schema (verified via migration files)
  POSTGRESQL FRESH BOOTSTRAP: UNVERIFIED — no disposable PostgreSQL available
  All FDA tests use sqlite:///:memory: via create_app() factory

CANONICAL ROUTE TRUTH: VERIFIED
  ONLY canonical intelligence route: /api/v1/intelligence/ask
  Parallel /api/v1/cross-boundary/ask route: REMOVED from app/__init__.py
  Duplicate legacy /api/intelligence blueprint: REMOVED from app/__init__.py
  Single intelligence path, no alternative routes.

AUTHORITY TRUTH: VERIFIED
  ExecutionAuthorityEnforcer wired into canonical /api/v1/intelligence/ask route
  Authority uses NON_AUTHORITY_CLASSIFICATIONS (constitutional classification set):
    {"external_evidence", "memory", "inference", "unknown"}
  No source-name string matching. No configurable deny-list.
  Authority stage present in pipeline: execution_authority
  Evidence classifications checked at every request.

INFERENCE GOVERNANCE TRUTH: VERIFIED
  InferenceGovernanceService.process() is the canonical inference entry point
  Pipeline: deterministic-first → capability routing → orchestrator execution
  Deterministic-first: greetings, thanks, farewells resolve without model
  Capability-based routing: chat, search, code, analysis, etc. via CapabilityBasedRouter
  Cost hierarchy: FREE → OPEN → LOW → STANDARD → PREMIUM
  Paid governance: enabled/disabled, free-capable requests don't auto-escalate
  Fallback: primary → fallback → safe failure (tested via scenarios)
  Provider observability: selected_provider, model, cost_class, policy_decision,
    escalation_reason, fallback_chain, duration, success, error

TENANT ISOLATION TRUTH: CONDITIONAL
  Tenant identity resolved from session (user_id, identity_id, current_org_id)
  Cross-tenant verification tests exist (test_golden11)
  No deployed cross-tenant access test on running instance
  Legacy /api/intelligence blueprint removed — no bypass path

TEST TRUTH:
  FDA9+FDA10: 68 tests PASS
  Full regression: 192 tests PASS across 6 test suites
  Test assertions RESTORED: test_api_ask_with_session expects 200 only
  Conftest fixtures FIXED: admin_user, tenant no longer reference non-existent 'db' fixture
  All tests exercise canonical /api/v1/intelligence/ask route
  Authority tests: classification-based (not source-name string matching)

SECURITY TRUTH:
  Prompt injection: detected via PromptInjectionGuard, sanitized with [BLOCKED:] markers
  Model output: NOT authority — requires authorization boundary
  Execution authority: classification-based, wired into canonical route
  No parallel intelligence path (removed in this remediation)
  Cross-tenant: verified in tests, deployed but not independently tested

KNOWN LIMITATIONS:
  - PostgreSQL fresh bootstrap: UNVERIFIED — no disposable PostgreSQL available
  - Live provider execution: UNVERIFIED — tests use local provider (no API keys)
  - UI verification: UNVERIFIED — no browser-based end-to-end journey test
  - Performance benchmarks: UNVERIFIED — no latency/memory/load testing

FDA1–FDA10 REASSESSMENT:
  FDA1 VERIFIED (Constitutional architecture — canonical routes, no parallel paths)
  FDA2 CONDITIONAL (Core runtime — SQLite-only, Pg unverified)
  FDA3 CONDITIONAL (Memory & knowledge — SQLite-only)
  FDA4 CONDITIONAL (Identity — migrations exist, Pg unverified)
  FDA5 CONDITIONAL (Integration fabric — SQLite-only)
  FDA6 CONDITIONAL (Intelligence core — SQLite-only)
  FDA7 VERIFIED (Web intelligence — prompt injection, provenance)
  FDA8 VERIFIED (Model orchestration — 5-stage pipeline)
  FDA9 VERIFIED (Cross-boundary intelligence — authority wired, parallel path removed)
  FDA10 VERIFIED (Inference governance — deterministic-first, capability routing, paid governance)

FINAL CERTIFICATION:
  FDA9 + FDA10: CERTIFIED
  All mandatory gates VERIFIED.
  No parallel pipeline. Authority is classification-based, wired into canonical route.
  InferenceGovernanceService is the canonical inference entry point.
  Deployment verified on port 5001 (commit 16c3aac).
  Known limitations: PostgreSQL fresh bootstrap UNVERIFIED; live provider execution UNVERIFIED.