# SUPPRESSION REGISTER — ZERO-GAP-FORENSIC-RECONCILIATION-05

## 8 Module-Level Skip Files (155 tests total)

| ID | File | Tests Skipped | Mechanism | Introduced (earliest) | Reason Given | Actual Root Cause | Current State |
|----|------|---------------|-----------|-----------------------|--------------|-------------------|---------------|
| S-01 | test_batch05_06.py | 7 | `pytestmark.skip` | Unknown (pre-dates audit) | "flaky — requires DB isolation fixture" | 5/7 fail (DB issues), 2 pass | 🚫 SUPPRESSED — OPEN |
| S-02 | test_prod34_closed.py | 1 | `pytestmark.skip` | Unknown | "requires infra" | Uses `run_cycle()` — needs runtime loop infra | 🚫 SUPPRESSED — OPEN |
| S-03 | test_prod33_quoted.py | 1 | `pytestmark.skip` | Unknown | "requires infra" | Uses `run_cycle()` — needs runtime loop infra | 🚫 SUPPRESSED — OPEN |
| S-04 | test_workspace_experience_validation.py | 57 | `pytestmark.skip` | Unknown | "requires infra" | 10/57 fail, 47 pass (M3 report) | 🚫 SUPPRESSED — OPEN |
| S-05 | test_cookie_auth.py | 12 | `pytestmark.skip` | Unknown | "requires infra" | 4/12 fail: `_signin_success_response` removed | 🚫 SUPPRESSED — OPEN |
| S-06 | test_routes.py | 25 | `pytestmark.skip` | Unknown | "requires infra" | 13/25 fail (M3 report) | 🚫 SUPPRESSED — OPEN |
| S-07 | test_characterization.py | 51 | `pytestmark.skip` | Unknown | "requires infra" | 9/51 fail, 41 pass, 1 skip (M3 report) | 🚫 SUPPRESSED — OPEN |
| S-08 | test_planner_engine.py (1 class) | 1 | `@pytest.mark.skip` | Unknown | "Requires Event Bus infrastructure" | TestPlannerIntegration — needs EventBus | 🚫 SUPPRESSED — OPEN |

## Historical CI Exclusions (all removed in current config)

| ID | Test | Excluded From | Commit | Reason Given | Current State |
|----|------|--------------|--------|-------------|---------------|
| CI-E1 | test_golden_lead_to_customer | CI-CI | 5a003f7 | "401 vs 201 — missing auth setup" | FIXED: D-04 (83103e6) added auth setup. Test passes. |
| CI-E2 | loads_with_app tests | CI-CI | cf7d1ab | "pre-existing" | REMOVED: CI config no longer filters tests (WORKSTREAM A) |
| CI-E3 | test_orch_loads_with_app | CI-CI | cceec84 | "503 vs 200 — orchestration not running in CI" | REMOVED: CI config no longer filters tests |
| CI-E4 | test_cortex tests | CI-CI | 608c1fa | "503 vs 200 — cortex not running in CI" | REMOVED: CI config no longer filters tests |

## Dependency Integrity

| Change | Commit | What Broke | Root Cause | Status |
|--------|--------|-----------|-------------|--------|
| Loosen version pins + add flask-wtf | eab4998 | CI couldn't install exact pinned versions | Flask 3.1.3 not available in CI pip index | Fixed — versions now use range constraints |
| CI/CD dedup | ffb7c83 | Two workflows running duplicate checks | ci-cd.yml and ci.yml both ran tests | CI canonicalized to ci.yml |