============================================================
FORENSIC REVIEW #2 — FDA1–FDA10 PRE-FDA11 GATE
============================================================

EXECUTIVE VERDICT:
NOT CLEAR FOR FDA11

The review found 2 P0 constitutional violations, 3 P1 functional
blockers, and 8 P2/P3 quality issues. The most critical finding is
that the FDA9+FDA10 remediation was INCOMPLETE: the parallel pipeline
was NOT removed from the source tree, the deployed runtime is serving
pre-FDA9 code, and the canonical intelligence path does not use the
execution authority mechanism that was built.

FDA9+FDA10 certification is REJECTED. Seven of ten prior FDA
certifications must be downgraded to CONDITIONAL due to deployment
and runtime verification gaps.

============================================================
1. EXECUTIVE VERDICT
============================================================

FINAL: NOT CLEAR FOR FDA11

The following must be resolved before FDA11:

1. Remove the parallel cb_bp route registration from app/__init__.py
2. Wire ExecutionAuthorityEnforcer into the canonical /api/v1/intelligence/ask route
3. Deploy the certified commit to production and verify
4. Remove the duplicate app/intelligence_routes.py blueprint registration
5. Verify PostgreSQL bootstrap (currently UNVERIFIED)

============================================================
2. EVIDENCE METHODOLOGY
============================================================

Method: Read-only inspection of:
  - Source code (app/, core/, tests/)
  - Git history (HEAD → origin/master, FDA commits)
  - Running deployment (port 5001 gunicorn health endpoints)
  - Blueprint registration (app/__init__.py)
  - Test fixtures and quality (tests/conftest.py, test_fda*.py)

No code, config, test, database, or deployment modifications made.

============================================================
3. FDA1–FDA10 MATRIX
============================================================

| FDA | Capability | Implementation | Test | Runtime | Deployment | Status | Risk |
|-----|-----------|----------------|------|---------|------------|--------|------|
| FDA1 | Canonical Architecture | app/__init__.py, 50+ blueprints | test_fda1_canonical_architecture.py | YES — app factory creates 50+ routes | NOT DEPLOYED | CONDITIONAL | P2 |
| FDA2 | Core Runtime + Idempotency | app/execution/, core/execution_engine/ | test_fda2_core_runtime.py, test_fda2_concurrent_idempotency.py | SQLite-only test proof | NOT DEPLOYED | CONDITIONAL | P2 |
| FDA3 | Canonical Memory & Knowledge | app/memory/, core/memory_knowledge_runtime/ | test_fda3_canonical_memory.py (1047 lines) | SQLite-only test proof | NOT DEPLOYED | CONDITIONAL | P2 |
| FDA4 | Canonical Identity | core/identity/, migrations/0005 | test_fda4_identity.py (559 lines) | SQLite-only test proof, PG migrations exist | NOT DEPLOYED | CONDITIONAL | P2 |
| FDA5 | Integration Fabric, API, Auth, Gmail, Reliability | core/integration_fabric.py, core/reliability_fabric.py, app/auth.py | test_fda5_*.py (6 files, 773 lines) | SQLite-only test proof | NOT DEPLOYED | CONDITIONAL | P2 |
| FDA6 | Intelligence Core | core/intelligence/, core/model_orchestrator.py | test_fda6_intelligence_core.py | SQLite-only test proof | NOT DEPLOYED | CONDITIONAL | P2 |
| FDA7 | Web Intelligence | core/web_intelligence.py | test_fda7_fda8.py (801 lines) | SQLite-only test proof | NOT DEPLOYED | VERIFIED* | P2 |
| FDA8 | Model Orchestration | core/model_orchestrator.py | test_fda7_fda8.py | SQLite-only test proof | NOT DEPLOYED | VERIFIED* | P2 |
| FDA9 | Cross-Boundary Intelligence | app/intelligence/routes.py (enhanced), core/intelligence_runtime/cross_boundary.py | test_fda9_fda10.py (1346 lines) | SQLite-only test proof, canonical route DOES NOT use authority | NOT DEPLOYED | FAIL | P0 |
| FDA10 | Inference Governance | core/inference_governance.py | test_fda9_fda10.py | SQLite-only test proof, governance NOT wired into canonical orchestrator | NOT DEPLOYED | CONDITIONAL | P1 |

*FDA7/FDA8: Test proof is SQLite-only and deployment is pre-certification commit.

============================================================
4. ARCHITECTURE FINDINGS
============================================================

P0 — PARALLEL PIPELINE STILL ACTIVE
  app/__init__.py lines 804-805 register cb_bp at /api/v1/cross-boundary/.
  This was added in commit 42ccb0a but NOT removed in the remediation
  commit a110317. The git checkout -- app/__init__.py reverted to the
  commit-42ccb0a state, which has the parallel registration.
  The cross_boundary_routes.py still exists with its own blueprint.
  Impact: Constitutional violation. Parallel pipeline still registered.

P1 — DUPLICATE INTELLIGENCE BLUEPRINTS
  app/__init__.py registers TWO intelligence blueprints:
    Line 655: from app.intelligence.routes import intelligence_bp
    Line 667: from app.intelligence_routes import intelligence_bp
  The first is /api/v1/intelligence (enhanced with FDA9+FDA10).
  The second is /api/intelligence (old, pre-FDA9).
  Both are actively registered. Two intelligence paths = bypass risk.

P1 — CROSS-BOUNDARY SERVICE (cross_boundary.py) HAS NO CONSUMER IN CANONICAL PATH
  The canonical /api/v1/intelligence/ask route (app/intelligence/routes.py)
  imports CapabilityBasedRouter, DeterministicResponseTemplates,
  ProviderCostRegistry, and InferenceGovernanceService directly, but:
    - Does NOT import ExecutionAuthorityEnforcer
    - Does NOT import CrossBoundaryIntelligenceService
    - Does NOT import TenantIdentity
    - Does NOT use NON_AUTHORITY_CLASSIFICATIONS
  These classes exist only in cross_boundary.py which has zero callers
  in the canonical path. Dead code.

P1 — INFERENCE GOVERNANCE NOT WIRED INTO ORCHESTRATOR
  core/inference_governance.py provides:
    - Deterministic-first routing
    - Capability-based routing
    - Cost hierarchy
    - Paid governance
    - Fallback scenarios
  But none of these are wired into the InferenceOrchestrator itself.
  The canonical orchestrator pipeline (classify → policy → select →
  execute → observe) does NOT use InferenceGovernanceService. The
  enhanced route calls CapabilityBasedRouter.route() directly, bypassing
  the orchestrator's own classification stage.

P2 — APP.__INIT__.py STRUCTURE CONCERNS
  The file is 1053 lines with 60+ blueprint registrations.
  Auth middleware (861-900) uses path matching to exempt 30+ prefixes.
  Multiple model import blocks (lines 420, 691-697) with broad
  Exception catching that could hide import failures.

P2 — ARCHIVE DEBRIS
  4 _archive/ directories (communication_legacy, execution_variants,
  graph_variants, object_variants) contain legacy code with git history
  but no current importers. Safe dead code.

============================================================
5. RUNTIME FINDINGS
============================================================

P0 — DEPLOYED RUNTIME IS PRE-FDA9+FDA10
  Running gunicorn on port 5001 serves code that:
    - Returns {"error":"Not authenticated","success":false} for POST /api/v1/intelligence/ask
    - Does NOT have the /api/v1/intelligence/health endpoint (404)
    - Does NOT have the cross-boundary intelligence endpoints (404)
  The running workers were started at 11:11, 11:23, 12:06 (Aug 11)
  but are running code from commit unknown (pre-42ccb0a).
  Zero FDA9+FDA10 code is deployed.

P3 — HEALTH ENDPOINTS
  /health returns 200 with database connected, uptime 33,936 seconds.
  /system/health returns 200 with DB latency 2.24ms, event queue
  backlog 0, integrations: email=false.
  These are separate from the /api/v1/intelligence/health endpoint
  which returns 404 (not deployed).

============================================================
6. SECURITY FINDINGS
============================================================

P0 — EXECUTION AUTHORITY NOT IN CANONICAL PATH
  The ExecutionAuthorityEnforcer (with NON_AUTHORITY_CLASSIFICATIONS)
  only exists in cross_boundary.py. The canonical /api/v1/intelligence/ask
  route does NOT call it. None of the FDA9/FDA10 execution authority
  proofs actually protect the production intelligence path.

P1 — TENANT ISOLATION NOT PROVEN ON RUNNING INSTANCE
  The deployed /api/v1/intelligence/ask checks session.get("user_id")
  or session.get("identity_id") → returns 401 if missing. Cross-tenant
  access can only be tested by creating multiple sessions, which requires
  auth tokens. No runtime cross-tenant isolation evidence.

P2 — TWO INTELLIGENCE PATHS = BYPASS RISK
  The old /api/intelligence/ask route (from app/intelligence_routes.py)
  does NOT use FDA9+FDA10 tenant identity, evidence classification,
  or execution authority. Applications that call /api/intelligence/ask
  bypass ALL FDA9+FDA10 security boundaries.

P2 — BROAD AUTH EXEMPTIONS
  The auth middleware at app/__init__.py:878-881 exempts 30+ path
  prefixes including /api/*, /debug, /app, /x/, /workspace, etc.
  Any of these could bypass auth if they expose sensitive operations.

============================================================
7. DATA FINDINGS
============================================================

P2 — PostgreSQL NOT PROVEN
  Database config reads: "postgresql://shunya:***@localhost:5432/shunya_db"
  PostgreSQL is running (pid 1774690, started Jul 29).
  Migration head: 0005_fda4_identity_schema.
  But all FDA tests use sqlite:///:memory:.
  No test exercises the real PostgreSQL migration chain or schema.

P2 — TEST FIXTURES USE BROKEN DEPENDENCIES
  tests/conftest.py:
    Line 104: def tenant(app, db): — references 'db' as fixture that doesn't exist
    Line 125: def admin_user(app, db): — same issue
  These fixtures cannot be used. Tests that need them must work around
  by setting up sessions manually (as test_fda9_fda10.py does with
  _setup_session).

============================================================
8. AI/INFERENCE FINDINGS
============================================================

P1 — INFERENCE GOVERNANCE NOT IN ORCHESTRATOR PIPELINE
  The InferenceGovernanceService provides deterministic-first routing,
  capability-based routing, cost hierarchy, paid governance, and
  fallback logic, but none of this is in the canonical
  InferenceOrchestrator pipeline. The enhanced route calls
  CapabilityBasedRouter.route() directly as a pre-orchestrator step,
  not through the orchestrator's classify stage.

P2 — DETERMINISTIC-FIRST IS ROUTE-LEVEL, NOT ORCHESTRATOR-LEVEL
  The deterministic-first check (simple greetings/thanks/farewells)
  happens in the route handler before calling the orchestrator. If
  any consumer calls the InferenceOrchestrator directly (bypassing
  /api/v1/intelligence/ask), they get a model invocation for greetings.
  Not a constitutional violation but a governance gap.

P3 — LOCAL PROVIDER IN TESTS
  All inference tests use the "local" provider which returns static
  responses. No test exercises the full provider chain (Groq →
  OpenRouter → OpenAI → etc.) because no API keys are set in the
  test environment.

============================================================
9. TEST-QUALITY FINDINGS
============================================================

P2 — test_fda9_fda10.py: TESTS CANONICAL ROUTE BUT DOES NOT TEST AUTHORITY
  The API tests (TestCanonicalRuntimePath) exercise POST /api/v1/intelligence/ask
  but the route itself doesn't call ExecutionAuthorityEnforcer.
  The authority tests exist only in unit tests against the
  ExecutionAuthorityEnforcer class directly, not through the canonical path.

P2 — test_evidence_failure_graceful: WEAKENED ACCEPTANCE CRITERIA
  Originally expected "don't have sufficient information" in response.
  Changed to check pipeline truth_stage["answer_source"] == "unknown".
  The inference provider still returns a generic chat response when
  no company evidence exists. The assertion was structurally weakened.

P2 — test_api_ask_with_session: BROAD ACCEPTANCE
  Uses assert resp.status_code in (200, 400). This means 400 errors
  are silently accepted as "pass." A 400 means the request was rejected
  — this should be a failure, not an accepted outcome.

P3 — 6459 LINES OF FDA TESTS BUT ZERO DEPLOYMENT SMOKE TESTS
  No test verifies the running gunicorn instance. No test proves the
  deployed code matches the certified commit. All tests are pre-deployment.

P3 — FIXTURE ISSUE: admin_user REQUIRES 'db' FIXTURE THAT DOESN'T EXIST
  conftest.py line 125: def admin_user(app, db):
  There is no 'db' fixture in conftest.py. The 'db' in app.py is a
  SQLAlchemy instance, not a pytest fixture. Tests using admin_user
  fail with "fixture 'db' not found."

============================================================
10. DEPLOYMENT FINDINGS
============================================================

P0 — NONE OF FDA1–FDA10 IS DEPLOYED
  Running gunicorn on port 5001 serves pre-FDA9 code. The FDA commits
  (42ccb0a, a110317) have been pushed to origin/master but NOT deployed.
  The gunicorn workers were started after code changes but the running
  code does not reflect the HEAD commit.

P3 — GUNICORN IS RUNNING
  4 gunicorn worker processes:
    PID 3525992 (master, Aug 09)
    PID 3690448 (worker, Aug 11 11:11)
    PID 3693663 (worker, Aug 11 11:23)
    PID 3700553 (worker, Aug 11 12:06)
  Workers are from .venv/bin/gunicorn with --workers 3.
  Health endpoint returns database: connected.

P3 — NO POSTGRESQL MIGRATION VERIFIED ON DEPLOYED INSTANCE
  Migration head is 0005_fda4_identity_schema but this was verified
  only on the development database, not proven on the running instance.

============================================================
11. PRODUCT/UX FINDINGS
============================================================

P3 — UI RUNTIME: UNVERIFIED
  No browser-based verification was performed. All FDA1–FDA10 product
  and UX claims are based on backend tests and architecture documentation.
  The frontend SPA workspace may or may not reflect the new capabilities.

P3 — NO END-TO-END FOUNDER JOURNEY TEST
  No test exercises the full founder flow (login → workspace → AI query →
  command → logout) through the deployed instance. All evidence is
  at the API/test level.

============================================================
12. PERFORMANCE/RELIABILITY FINDINGS
============================================================

P3 — NO PERFORMANCE BENCHMARKS
  No latency measurements beyond individual test assertions.
  No memory profiling. No load testing. No concurrency testing
  of the inference orchestrator.

P3 — CIRCUIT BREAKER EXISTS BUT NOT TESTED ON DEPLOYMENT
  core/reliability_fabric.py has circuit breaker logic tested in
  test_fda5_reliability.py but not verified on the deployed instance.

============================================================
13. GIT TRUTH
============================================================

  HEAD:          a110317cebbfef4f046ab80ee4d640338deee7ae
  Branch:        master
  origin/master: a110317cebbfef4f046ab80ee4d640338deee7ae
  HEAD==origin:  YES

  Recent FDA commits (newest first):
    a110317 — FDA9+FDA10 REMEDIATION (3 files)
    42ccb0a — FDA9+FDA10 initial (5 files + cb_bp)
    000e1d0 — FDA7-FDA8 evidence correction
    ... (30+ FDA commits total)

  Uncommitted changes:
    app/auth.py, app/awareness/engine.py, app/communication/models.py,
    app/intelligence/awareness.py, app/orchestrator/engine.py (modified)
    app/execution_runtime/, app/object_composer/, app/object_workspace/ (deleted)
    Various untracked files (docs, scripts, archives)

  GIT TRUTH: VERIFIED (HEAD == origin/master)
  But this does NOT equal deployment truth.

============================================================
14. DEPLOYMENT TRUTH
============================================================

  DEPLOYMENT TRUTH: UNVERIFIED

  Running instance on port 5001 does NOT serve HEAD (a110317).
  The /api/v1/intelligence/health endpoint returns 404.
  The /api/v1/intelligence/ask returns old-style error format.
  Zero FDA9+FDA10 code is live.

  Evidence: curl http://127.0.0.1:5001/api/v1/intelligence/ask returns
  {"error":"Not authenticated","success":false} — pre-FDA9 format.

============================================================
15. DEFECT REGISTER
============================================================

| ID | Sev | Area | Finding | Impact | Affected FDA | Launch Impact |
|----|-----|------|---------|--------|-------------|---------------|
| F01 | P0 | Architecture | Parallel cb_bp route still registered | Constitutional violation — parallel pipeline | FDA9 | BLOCKER — parallel bypass path exists |
| F02 | P0 | Execution Authority | ExecutionAuthorityEnforcer not in canonical route | Security boundary not enforced on production | FDA9 | BLOCKER — model output can authorize execution |
| F03 | P0 | Deployment | Running instance is pre-FDA9 code | All FDA1–FDA10 work is not live | ALL | BLOCKER — nothing is deployed |
| F04 | P1 | Architecture | Two intelligence blueprints registered (new + old) | Bypass risk via old /api/intelligence path | FDA9 | HIGH — old route bypasses all FDA9 security |
| F05 | P1 | Architecture | Cross-boundary service dead code — no consumer | Wasted architecture, not protecting anything | FDA9 | HIGH — security model exists but unused |
| F06 | P1 | Inference | InferenceGovernanceService not in orchestrator pipeline | Governance not enforced on orchestrator calls | FDA10 | HIGH — governance bypassable |
| F07 | P2 | Data | All FDA tests use SQLite :memory: | PostgreSQL migration chain unverified | ALL | MEDIUM — PG compatibility risk |
| F08 | P2 | Tests | test_evidence_failure_graceful weakened assertion | Acceptance criteria eroded | FDA9 | MEDIUM — fabricated answers possible |
| F09 | P2 | Tests | test_api_ask_with_session accepts 200 or 400 | 400 errors silently pass | FDA9 | MEDIUM — false positives |
| F10 | P2 | Tests | conftest.py fixtures reference non-existent 'db' fixture | Fixtures unusable, tests manually set up sessions | ALL | MEDIUM — test infrastructure brittle |
| F11 | P2 | Tests | Authority tests call class directly, not via canonical route | Security proof does not exercise production path | FDA9 | MEDIUM — security not end-to-end |
| F12 | P3 | UI | No browser verification | UX claims unsubstantiated | ALL | LOW — backend-focused audit |

============================================================
16. FDA CLOSURE REASSESSMENT
============================================================

| FDA | Original Status | Reassessed Status | Reason |
|-----|----------------|-------------------|--------|
| FDA1 | CERTIFIED | CONDITIONAL | Architecture exists, deployed runtime not verified |
| FDA2 | CERTIFIED | CONDITIONAL | SQLite-only, deployment unverified |
| FDA3 | CERTIFIED | CONDITIONAL | SQLite-only, deployment unverified |
| FDA4 | CERTIFIED | CONDITIONAL | PG migrations exist, deployment unverified |
| FDA5 | CERTIFIED | CONDITIONAL | SQLite-only, deployment unverified |
| FDA6 | CERTIFIED | CONDITIONAL | SQLite-only, deployment unverified |
| FDA7 | CERTIFIED | VERIFIED* | Unit/integration test proof solid, no live provider exercise |
| FDA8 | CERTIFIED | VERIFIED* | Same as FDA7 |
| FDA9 | CERTIFIED | FAIL | Parallel pipeline active, authority not in canonical route, remediation incomplete |
| FDA10 | CERTIFIED | CONDITIONAL | Governance not wired into orchestrator pipeline, deployment unverified |

*FDA7/FDA8 remain VERIFIED at the test/architecture level but not at deployment level.

============================================================
17. CONSOLIDATED REMEDIATION SCOPE (required before FDA11)
============================================================

The following scope addresses ALL P0 and P1 findings. Execute in order:

GATE 1 — Remove parallel pipeline
  - Remove cb_bp registration from app/__init__.py (lines 804-805)
  - Verify /api/v1/cross-boundary/ask returns 404
  - Keep cross_boundary.py for its utility classes (used by tests)

GATE 2 — Wire execution authority into canonical route
  - Import ExecutionAuthorityEnforcer in app/intelligence/routes.py
  - Add authority check before inference execution for execute-type requests
  - Add NON_AUTHORITY_CLASSIFICATIONS check at the evidence assembly stage
  - Verify existing authority tests exercise the canonical HTTP path

GATE 3 — Remove duplicate intelligence blueprint
  - Remove from app.intelligence_routes import intelligence_bp at line 667
  - Remove app.register_blueprint(intelligence_bp) at line 668
  - Verify /api/v1/intelligence/ask still works (the correct one is at line 655)

GATE 4 — Deploy and verify
  - git checkout a110317
  - Restart gunicorn: sudo systemctl restart shunya (or kill -HUP)
  - Verify: curl /api/v1/intelligence/health → 200
  - Verify: curl /api/v1/intelligence/ask with auth → enhanced response format
  - Verify: curl /api/v1/cross-boundary/ask → 404 (gone)

GATE 5 — Restore weakened test assertions
  - test_evidence_failure_graceful: assert response does not fabricate data
  - test_api_ask_with_session: assert 200 only, not 200/400

GATE 6 — (Optional) PostgreSQL fresh bootstrap
  - Run alembic upgrade head on a fresh disposable PostgreSQL database
  - Verify all migrations apply cleanly

After all 6 gates: re-certify FDA9+FDA10, then clear for FDA11.

============================================================
18. PRE-FDA11 DECISION
============================================================

B) NOT CLEAR FOR FDA11

The six-gate remediation scope above (Sections 17, lines G1-G6)
must be executed before FDA11 can begin. Estimated effort: 2-3
engineering sessions.

The most critical gates are:
1. Remove parallel pipeline (constitutional violation)
2. Wire authority into canonical route (security gap)
3. Deploy and verify (zero FDA code is live)

Without these, FDA11 would build on an architecture with active
constitutional violations and unenforced security boundaries.