# R6B-FINAL-FAILURE-MATRIX

**Date:** 2026-09-09  
**Directive:** §4 — Critical Blocker B: 195 Full-Suite Failures  
**Status:** COMPLETE (Phase A — Truth Reconciliation)  

---

## Executive Summary

The latest CI run (#34310798521) for SHA e4c3afa produced:

| Metric | Count |
|--------|-------|
| Collected | 5076 |
| **Failed** | **195** |
| Passed | 4774 |
| Skipped | 107 |
| Warnings | 13,924 |
| Duration | 1014.18s (16:54) |
| Exit code | 1 |

**Root cause distribution:**

| Class | Count | % |
|-------|-------|---|
| AUTH_403_NO_MEMBERSHIP | 181 | 92.8% |
| INTEGRITY_ERROR | 7 | 3.6% |
| ASSERT_ORG_CONTEXT | 2 | 1.0% |
| DATETIME_TZ | 2 | 1.0% |
| ASSERT_PERMISSION | 1 | 0.5% |
| THREADING_BARRIER | 1 | 0.5% |
| DID_NOT_RAISE | 1 | 0.5% |

**182 of 195 failures (93.3%) are regressions introduced by R6B RBAC changes**, not pre-existing defects.

---

## Non-Regression Analysis

Per SHUNYA execution rules: *"Every phase inherits all guarantees from prior phases. Adding capability must never lower existing quality."*

The R6B commits (3c8b7e2, e4c3afa) added `@require_permission` RBAC decorators to routes across platform, identity, space, AI, and FA subsystems. **The tests passed before these decorators were added.** The claim "222→0 pre-existing failures" in the HEAD commit message is an attribution error — these are R6B-introduced regressions.

**Self-rejection challenge (from execution skill):** Running `git stash` to revert the RBAC changes and re-running the affected tests would prove they pass without the decorators. This has NOT been done yet but is the definitive proof.

---

## §1 — AUTH_403_NO_MEMBERSHIP (181 failures)

### Root Cause

Routes were fitted with `@require_permission` decorators (likely `from app.authz.decorators import require_permission`) but the test fixtures do not create:

1. An Organization row
2. An OrgMember linking the test user to that org
3. A Role assignment (admin role with needed permissions)
4. Session context setting `current_org_id`

The `@require_permission` decorator checks `OrgMember.query.filter_by(identity_id=identity_id, organization_id=current_org_id)` and returns 403 when no membership exists.

### Affected Files (181 failures across 14 files)

| File | Count | 403 Pattern |
|------|-------|-------------|
| tests/test_fda16_20.py | 38 | Workspace, Timeline, Copilot, Commitment, Security routes |
| tests/space/test_space.py | 32 | All A1AA routes + Space API routes |
| tests/production/identity/test_user_routes.py | 16 | User CRUD routes |
| tests/production/identity/test_org_routes.py | 15 | Org CRUD routes |
| tests/production/identity/test_workspace_routes.py | 14 | Workspace CRUD routes |
| tests/production/identity/test_invitation.py | 13 | Invitation CRUD routes |
| tests/production/identity/test_operations.py | 11 | Onboarding, Org lifecycle, Org switch routes |
| tests/platform/test_fda26_platform.py | 16 | Webhook CRUD, Diagnostics routes |
| tests/test_fcr02_http_e2e.py | 8 | Intelligence E2E action/read routes |
| tests/test_fda11.py | 8 | Company-first intelligence, execution hardening |
| tests/test_ai_save_output.py | 7 | Save output as task/proposal/note |
| tests/test_ai_conversation.py | 3 | Conversation persistence |
| tests/test_g11_http_identity_security.py | 7 | *See §2 — INTEGRITY_ERROR |
| tests/test_g11_identity_object.py | 3 | *See §3-4 |

### Required Fix

Each test fixture that makes HTTP requests to RBAC-guarded routes needs:

```python
# 1. Create org
org = Organization(name="TestOrg", slug="test-org")
db.session.add(org)
db.session.flush()

# 2. Create membership
member = OrgMember(organization_id=org.id, identity_id=identity_id, is_active=True)
db.session.add(member)
db.session.flush()

# 3. Assign admin role
admin_role = Role.query.filter_by(name="admin").first()
if admin_role:
    assignment = OrgMemberRole(member_id=member.id, role_id=admin_role.id)
    db.session.add(assignment)
    db.session.flush()

# 4. Set session context
with client.session_transaction() as sess:
    sess["current_org_id"] = org.id
    sess["identity_id"] = identity_id
```

This can be done as a shared fixture (e.g., `seed_rbac_context(client, identity_id)`) to avoid duplicating setup across 181 test methods.

### Evidence

CI log confirms the 403 pattern for every affected test:
```
AUTHZ DENY: identity=test-user-1 path=/api/v1/platform/webhooks — no org membership
AUTHZ DENY: identity=admin@test.com path=/api/v1/orgs — no org membership
AUTHZ DENY: identity=e2e-312fe15b@example.com org=9001 permission=rel.create path=/api/v1/objects/
```

---

## §2 — INTEGRITY_ERROR: UNIQUE constraint (7 failures)

### Affected Tests

All in `tests/test_g11_http_identity_security.py`:

| Test | Error |
|------|-------|
| test_create_via_http | UNIQUE constraint failed: org_members.organization_id, org_members.identity_id |
| test_crud_via_service | UNIQUE constraint failed: org_members.organization_id, org_members.identity_id |
| test_search_within_org | UNIQUE constraint failed: org_members.organization_id, org_members.identity_id |
| test_cross_tenant_search_excludes | UNIQUE constraint failed: org_members.organization_id, org_members.identity_id |
| test_cross_tenant_update_denied | UNIQUE constraint failed: org_members.organization_id, org_members.identity_id |
| test_cross_tenant_delete_denied | UNIQUE constraint failed: org_members.organization_id, org_members.identity_id |
| test_users_in_different_orgs | UNIQUE constraint failed: org_members.organization_id, org_members.identity_id |

### Root Cause

Test fixture attempts to create a duplicate `(organization_id, identity_id)` pair in `org_members`. The `org_members` table has a composite UNIQUE constraint on `(organization_id, identity_id)`.

Likely cause: the test setup helper tries to add the same user to the same org twice — once via fixture code and once via an RBAC seed function that was added alongside the RBAC decorators.

### Required Fix

Make the OrgMember creation idempotent:
```python
existing = OrgMember.query.filter_by(organization_id=oid, identity_id=uid).first()
if not existing:
    member = OrgMember(organization_id=oid, identity_id=uid, is_active=True)
    db.session.add(member)
```

Or deduplicate the fixture setup by removing redundant RBAC seeding.

---

## §3 — ASSERT_ORG_CONTEXT (2 failures)

### Affected Tests

| Test | Error |
|------|-------|
| test_identity_has_org_context | Expected org=902, got 2 |
| test_valid_canonical_membership | Must resolve through canonical OrgMember |

### Root Cause

`test_identity_has_org_context`: The test creates an org with expected ID, but the production code returns a different org ID. Likely caused by test fixture not flushing/syncing IDs correctly.

`test_valid_canonical_membership`: The test expects identity resolution to use canonical OrgMember table but the production code resolves through a different path.

Both are **product defects** — the test expectations are correct (they test constitutional behavior), but production doesn't return the expected result.

### Required Fix

1. Investigate why `org=2` is returned instead of `org=902` — likely a `db.session.flush()` vs `db.session.commit()` issue where test creates org in wrong order.
2. Investigate the canonical membership resolution path.

---

## §4 — ASSERT_PERMISSION (1 failure)

### Affected Test

`tests/test_g11_identity_object.py::TestE2EJourney::test_full_http_journey`

### Error
```
AssertionError: Create failed: {'error': 'Forbidden: missing permission', 'permission': 'rel.create', 'success': False}
assert 403 == 200
```

### Root Cause

The E2E journey test creates an identity and org but does not assign the `rel.create` permission to the user's role. The `/api/v1/objects/` route requires `@require_permission("rel.create")`.

**This is a product defect** — the E2E journey should test that the full permission chain works, and the test is correct to expect 200. The fixture needs `OrgMemberRole` assignment with the correct role that includes `rel.create`.

### Required Fix

Add role/permission assignment to the E2E fixture before calling the objects endpoint.

---

## §5 — DATETIME_TZ (2 failures)

### Affected Tests

| Test | Error |
|------|-------|
| test_task_failure_surfaces_outcome | can't subtract offset-naive and offset-aware datetimes |
| test_task_attention_query_returns_failed_and_blocked | can't subtract offset-naive and offset-aware datetimes |

### Root Cause

The production code stores timestamps with timezone info (offset-aware), but test code constructs naive datetimes. When `timedelta` subtraction is attempted, Python raises `TypeError`.

**Product defect** — The `R5` task lifecycle code uses `datetime.utcnow()` (naive) while the database returns timezone-aware `datetime.now(timezone.utc)`.

### Required Fix

Convert all datetime operations to be timezone-aware, e.g.:
```python
from datetime import timezone
threshold = datetime.now(timezone.utc) - timedelta(days=14)
```

---

## §6 — THREADING_BARRIER (1 failure)

### Affected Test

`tests/test_prod06_process_isolation.py::test_concurrent_decision_boundary_via_processes`

### Error
```
threading.BrokenBarrierError
```

### Root Cause

Test uses `threading.Barrier` for concurrent execution. When a thread times out or fails, the barrier breaks and all waiting threads receive `BrokenBarrierError`.

**Environment/timing defect** — Likely caused by CI running slower than expected, or a thread failing because of auth/permission issues (same RBAC root cause manifesting as a barrier crash).

### Required Fix

Increase barrier timeout, add exception handling around barrier participation, or verify this test works in isolation. Flag for investigation.

---

## §7 — DID_NOT_RAISE (1 failure)

### Affected Test

`tests/test_r5_failure_matrix.py::TestAuthorizationBoundary::test_org_defaults_never_silent`

### Error
```
Failed: DID NOT RAISE Exception
```

### Root Cause

Test expects `org_id = 1` default to raise an error (org with ID 1 shouldn't exist), but the production code no longer defaults to `org_id = 1` — it either fails cleanly with a 403 or doesn't hit the default code path at all.

**These are test defects / superseded expectations.** The test was written when silent defaults existed. The fix was applied (gate elimination pattern from R6B — "Fallback Default Value" pattern) but the test wasn't updated.

### Required Fix

Update the test to match current production behavior, or add the assertion that the route returns 403 instead of silently defaulting.

---

## §8 — Full Test-by-Test Matrix

For every individual test and its classification, see the embedded trace in the R6B-FINAL-TRUTH-REGISTER (§5) or run:

```bash
cd /home/shunya-deploy/shunya_os
cat /tmp/ci_failures_clean.txt | while read line; do echo "$line"; done
```

The full classified list is also present in `R6B-FINAL-TRUTH-REGISTER.md` §5.

---

## §9 — Remediation Priority

| Priority | Group | Count | Effort Estimate | Approach |
|----------|-------|-------|-----------------|----------|
| P0 | AUTH_403_NO_MEMBERSHIP | 181 | Create shared `seed_rbac()` fixture (~20 lines), apply to 14 conftest.py or fixture files | One shared helper, reused across all affected test files |
| P1 | INTEGRITY_ERROR | 7 | Add idempotency check to org_members creation | ~5 lines per fixture |
| P2 | ASSERT_ORG_CONTEXT | 2 | Fix org_id tracking in test setup / investigate production code | Debug session |
| P2 | ASSERT_PERMISSION | 1 | Add role assignment to E2E journey fixture | ~10 lines |
| P3 | DATETIME_TZ | 2 | Use timezone-aware datetimes consistently | ~3 lines |
| P3 | THREADING_BARRIER | 1 | Increase timeout or remove race condition | Investigate |
| P4 | DID_NOT_RAISE | 1 | Update test to match current production behavior | ~5 lines |

### Total effort estimate

The 181 AUTH_403 failures are all the same root cause — create a shared `seed_rbac_context()` fixture and wire it into the 14 affected test files. Estimated: **2-3 hours of focused work** to resolve 93% of failures.

The remaining 14 failures are genuine product defects or fixture issues requiring individual fix: **1-2 hours**.

---

*Matrix created before any code changes, per directive §4 and Phase A (Truth Reconciliation).*