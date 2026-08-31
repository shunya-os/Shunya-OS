# ZGC-PR-15 — FORMAL RECONCILIATION GATE
## Before Any Code Mutation

**Date:** 2026-08-31  
**Author:** Hermes Agent  
**Status:** RECONCILIATION COMPLETE — AWAITING APPROVAL FOR IMPLEMENTATION

---

## 1. GIT GRAPH — COMPLETE REFERENCE

| Ref | SHA | Role | Reachability |
|-----|-----|------|-------------|
| HEAD (detached) | d22cc07 | Current checkout | origin/master |
| origin/master | d22cc07 | Remote canonical | All branches |
| origin/main | 16a73ce | Remote second line | Ancestor of origin/master (16 commits behind) |
| local main | a19f1e8 | Stale local | In origin/master history, NOT in origin/main |
| local master | bdcf942 | Stale local | Behind everything |
| **Production** | **a19f1e8** | **Deployed** | In origin/master history (9 commits behind HEAD) |
| merge-base (origin/main ↔ origin/master) | 16a73ce | Common ancestor | Both refs contain this SHA |

### Topology
```
origin/main (16a73ce)
  → d293001 → a32cd63 → c5a28ca → 01197fd → 27599dd
  → 1786113 → 0931d1e → a19f1e8 [PRODUCTION]
  → 41580a0 → ed37fe7 → 8aeecc2 → 1450d7f
  → 030583f → 3b4324a → f2219df → d22cc07 (origin/master, HEAD)
```

**Conclusion:** origin/main ⟂ origin/master is a LINEAR chain, not a fork. origin/main is 16 commits behind origin/master. The earlier "33-commit divergence" was an artifact of comparing against stale local refs. No merge/rebase is needed for convergence — origin/main needs to catch up.

---

## 2. AUTHORIZATION ARCHITECTURE — FULL SURFACE MAP

### 7 Independent check_permission Implementations

| # | File | Canonical? | Bypass | Consumers |
|---|------|-----------|--------|-----------|
| 1 | `app/authz/services.py:check_permission` | **YES — canonical org-level** | owner+admin (Phase B, WRONG) | require_permission decorator, SUIL inhibit/authz, people routes |
| 2 | `app/authz/decorators.py:require_permission` | **YES — canonical decorator** | N/A (delegates to #1) | CRM routes, commercial routes, execution routes |
| 3 | `app/people/routes.py:_require_people_permission` | **Duplicate bypass** | owner+admin | People endpoints |
| 4 | `app/auth.py:Permission.check_permission` | Legacy platform-level | admin only (UserRole-based) | permission_required decorator |
| 5 | `app/enterprise/service.py:check_permission` | Enterprise domain | None (pure RBAC) | Enterprise module |
| 6 | `app/production/auth/authorization_middleware.py:check_permission` | Production/modern domain | None (role map RBAC) | Middleware |
| 7 | `app/graph/security.py:_check_permission` | Graph domain | None (policy-based) | Graph engine |
| 8 | `app/space/store.py:check_permission` | Space domain | None (identity→role list) | Space store |

### DEFAULT_ROLES Permission Counts

| Role | Permissions Count | Has all? | Description |
|------|------------------|---------|-------------|
| owner | ~50 (all PERMISSIONS + extras) | YES | Full control |
| admin | 24 (curated subset) | NO | Manage settings, members, data |
| manager | 14 | NO | Operations, approvals |
| member | 10 | NO | Create and edit own data |
| viewer | 4 | NO | Read-only |

### Authorization Contract Decision

**OWNER**: Correct to bypass. Owner has all permissions in DEFAULT_ROLES.  
**ADMIN**: **Incorrect to bypass.** Admin's DEFAULT_ROLES entry has 24/50 permissions. Admin should NOT have `org.delete`, `org.manage_billing`, `finance.reconcile`, `proposal.delete`, etc.

**The bypass was written to work around a real problem**: `seed_default_roles()` creates Role records but NO creation path auto-assigns OrgMemberRole to the new member. An admin OrgMember has `role="admin"` but zero OrgMemberRole entries. Without the bypass, they are denied everything.

**Correct fix**: Remove admin bypass. Add auto-assignment logic: when an OrgMember has `role` set but zero OrgMemberRole entries, find/create the matching default Role and auto-assign.

---

## 3. CI FAILURE — ROOT CAUSE

**Failing test**: `tests/test_workstreams_efgh.py::TestSUILGovernance::test_inhibit_authz_requires_permission`

**Root cause**: The test creates `OrgMember(role="admin")` without seeding default roles or assigning OrgMemberRole. This expects 403. Phase B's admin bypass returns 200 instead (admin = all permissions).

**This test is semantically correct** — it verifies that an admin without explicit permission assignment is denied access. The implementation (admin bypass) is wrong.

**The earlier fixture fix** (role="owner" or role="member") was a workaround. The correct fix is changing the implementation, not the test.

---

## 4. OPEN TASK DISCOVERY — SECTION 2 COMPLETE

### L1: Status files found
- `SHUNYA_ZERO_GAP_REGISTER.md` — M2C.4, out of date (references fd757d8 SHA)
- `M2C5_RESIDUAL_GAP_REGISTER.md` — M2C.5, references fd757d8 SHA
- `M2C5R_*` files — Phase R3 (tenant truth), R4 (object convergence), R5 (migration safety)
- `M2C5_CONVERGENCE_MATRIX.md` — convergence tracking
- `SHUNYA_M2C2_FINAL_REPORT.md` — historical

### L2: Code gaps discovered
- `app/data_migration/engine.py:162,275,370,376` — TODO for migration ledger, backup, reconcile, rollback
- `app/integration/registry.py:43,52` — NotImplementedError on list/register methods
- `app/shunya/executor.py:109-117` — NotImplementedError on execute/cancel/status methods
- `app/graph/edge.py:275-303` — 7 NotImplementedError for edge CRUD
- `app/adapters/os_adapter.py:151` — TODO for audit runtime wiring

### L3: Adapter stubs found (12 files)
- `app/graph_universal/` — entire directory is a compatibility stub
- `app/execution_intelligence/__init__.py` — stub
- `app/execution_runtime/__init__.py` — stub
- `app/evidence/models.py` — legacy compatibility stubs for Phase 7 models

### L5: Existing gap registers show 19 stubs, 12 launch blockers as of M2C.5

### Tasks 01-12 confirmed: all remain open and valid
- Task 01: Auth bypass — analyzed and resolved in this document
- Tasks 02-05: Described in origin/master commits (Phase A, Docs, CI fixes, Actions upgrade)
- Tasks 06-09: Described in origin/main commits (R9 fixture, account enum, migration engine, org session)
- Task 10: Comprehensive assessment — origin/main 16a73ce
- Task 11: Upload→Knowledge→Identity pipeline — origin/main fd757d8
- Task 12: Object convergence — origin/main 8907010

### Newly discovered launch-relevant tasks (auto-enter register)
1. **Auto-assignment gap**: No production code path creates OrgMemberRole after OrgMember creation
2. **Duplicate bypass**: `people/routes.py:_require_people_permission` has its own owner+admin bypass
3. **5 stale implementation files in evidence/models.py**: Legacy compatibility stubs with real table names
4. **Integration registry empty**: `integration/registry.py` has NotImplementedError on core methods

---

## 5. DEPLOYMENT TRUTH

| Property | Value |
|----------|-------|
| Running SHA | a19f1e8 (green CI run, 4926 pass 0 fail) |
| Running SHA date | 2026-08-31 06:54:24 |
| Deployment type | CI_CERTIFIED |
| Release type | Normal deployment via CI pipeline |
| Systemd | OK — 3 gunicorn workers, 380MB |
| DB | PostgreSQL 16, connected |
| migrations | Alembic present, in repo |
| Health | OK — git_commit matches a19f1e8 |
| 9 commits behind HEAD | YES (HEAD d22cc07 SHA mismatches deployed) |

---

## 6. CORRECT IMPLEMENTATION ORDER

Following founder's correction (dependency-based, not CI-first):

1. **Fix authorization contract** — Remove admin bypass, add auto-assignment (1 file: services.py)
2. **Fix duplicate bypass** — Remove admin bypass in people/routes.py
3. **Verify tests** — Run SUIL authz tests, CRM/commercial tests, auth tests
4. **Full test suite** — Run full CI-mirror suite
5. **Reconcile git** — Point origin/main to catch up with origin/master
6. **Deploy** — Push to origin/master, CI picks up

---

## STATUS

✅ Git graph — RECORDED  
✅ Authorization architecture audit — RECORDED  
✅ CI failure root cause — IDENTIFIED  
✅ Full open-task surface — DISCOVERED  
✅ Deployment truth — RECORDED  
🟡 **Implementation** — AWAITING FOUNDER APPROVAL

Next action: founder reviews this reconciliation. If approved, implement fix in this order:
1. `app/authz/services.py:check_permission` — owner-only bypass
2. `app/people/routes.py:_require_people_permission` — owner-only bypass
3. Add auto-assignment in `check_permission` for admin/member roles without OrgMemberRole
4. `pytest tests/test_workstreams_efgh.py -k "TestSUIL" -v --tb=short`
5. `pytest tests/test_fda11_crm.py tests/test_fda5_auth_security.py -v --tb=short`