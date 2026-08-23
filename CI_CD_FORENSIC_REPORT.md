# CI/CD ROOT REMEDIATION FORENSIC TABLE

| Workflow | Trigger | Tests Run | Excluded | Build | Deploy | Exact Commit |
|----------|---------|-----------|----------|-------|--------|-------------|
| ci.yml | push/PR to main/master | compile + UCP verify + tests/ | **exit code swallowed by pipe** (`pytest | tail -10`) | ❌ not in CI | N/A | N/A |
| ci-cd.yml | CI success on main/master | none | N/A | N/A | deploy.sh production | ❌ deploys mutable `head_branch`, not certified SHA |

## ROOT CAUSE LOG

| # | Failure | Root Cause | Fix | Status |
|---|---------|------------|-----|--------|
| RC-01 | CI always green despite failures | `pytest tests/ -q --tb=short 2>&1 \| tail-10` — exit code = tail (0), not pytest | Added `set -o pipefail` + removed `tail -10` | ✅ VERIFIED |
| RC-02 | Deploy workflow uses mutable branch ref | ci-cd.yml checks out `head_branch` instead of `head_sha`; deploy.sh does `git pull origin master` | ci-cd.yml passes `${{ github.event.workflow_run.head_sha }}`; deploy.sh accepts SHA arg and checks out exact commit | ✅ VERIFIED |
| RC-03 | 27 test errors from cascade pollution | `test_fda5_auth_security.py`, `test_fda5_api_contract.py`, `test_webhook_ingestion.py` fixtures don't set `SQLALCHEMY_DATABASE_URI` — hit production PostgreSQL; `test_z05_completion_lifecycle.py` module-level code pollutes global app state | All 3 fixtures now use `sqlite:///:memory:`; lifecycle test wrapped in `if __name__ == "__main__":` with `__test__ = False` | ✅ VERIFIED |
| RC-04 | CORS test fails in same-origin deployment | test_fda5_auth_security.py app fixture tests CORS but CORS is disabled when same-origin | Set `CORS_ALLOWED_ORIGINS` in test fixture so CORS is correctly enabled under test | ✅ VERIFIED |
| RC-05 | Canonical owner file missing | `app/execution_runtime/__init__.py` never created as architecture required | Created compatibility stub loading from canonical locations | ✅ VERIFIED |
| RC-06 | No frontend build in CI | ci.yml had only backend tests | Added `npm install --legacy-peer-deps` + `npm run build` step | ✅ VERIFIED |
| RC-07 | Deployment migration failures silenced | deploy.sh used `\|\| echo "WARNING"` — migration errors swallowed | Removed silent swallow; migration failure now properly exits | ✅ VERIFIED |
| RC-08 | No deployment rollback record | deploy.sh didn't record previous SHA | Added `PREVIOUS_SHA` capture, rollback command in failure messages | ✅ VERIFIED |
| RC-09 | 7 pre-existing test_fda2_core_runtime failures | Tests written for superseded Outcome model interface (stage as direct column vs state.stage JSON field) | Pre-existing — not CI/CD scope | ⚡ DOCUMENTED |