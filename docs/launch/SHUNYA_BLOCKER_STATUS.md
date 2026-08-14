# SHUNYA FINAL RELEASE CERTIFICATION — STATUS UPDATE

**Date:** 2026-08-14 (late)  
**Git HEAD:** 73d38b5 (== origin/master, working tree clean)

---

## BLOCKER STATUS

| Blocker | Status | Evidence |
|---------|--------|----------|
| 1. Authorization | **CERTIFIED** | `require_permission` decorator wired into CRM (rel.create, proposal.approve) and Execution (task.create). Admin/Manager/Member allowed (201), Viewer denied (403), Anonymous denied (401) — 10/10 HTTP matrix PASS. 22/22 tests. |
| 2. Tenant Isolation | **PARTIAL** | Migration 0008 adds tenant_id to objects/commitments/evidence_records/act_execution_logs. Object creation session-scoped. CRM tenant_id body-override blocked (session-derived). Org 4 created with distinct admin. Founder objects filtered by identity. REMAINING: legacy objects read filtering, identity_id resolution consistency. |
| 3. Age/Safety | **NOT STARTED** | |
| 4. Gmail E2E | **UNVERIFIED** | Requires founder OAuth action |
| 5. Business Workflow | **NOT STARTED** | |

---

## BLOCKER 1 — AUTHORIZATION: CERTIFIED

### Canonical enforcement mechanism
- `app/authz/decorators.py`: `require_permission(permission)` decorator
- Resolution: session user_id → TeamMember.email → OrgMember.identity_id → check_permission(org_id, identity, permission)
- 401 if unauthenticated, 403 if permission missing, 400 if no org

### Enforcement locations
- `POST /api/v1/crm/leads` → `rel.create`
- `POST /api/v1/crm/leads/<id>/won` → `proposal.approve`
- `POST /api/v1/outcomes` → `task.create`

### HTTP authorization matrix (all tested)
| User | Permission | Endpoint | Expected | Actual | Result |
|------|-----------|----------|----------|--------|--------|
| Admin | rel.create | POST /crm/leads | 201 | 201 | ✅ |
| Admin | task.create | POST /outcomes | 201 | 201 | ✅ |
| Manager | rel.create | POST /crm/leads | 201 | 201 | ✅ |
| Manager | task.create | POST /outcomes | 201 | 201 | ✅ |
| Member | rel.create | POST /crm/leads | 201 | 201 | ✅ |
| Member | task.create | POST /outcomes | 201 | 201 | ✅ |
| Viewer | rel.create | POST /crm/leads | 403 | 403 | ✅ |
| Viewer | task.create | POST /outcomes | 403 | 403 | ✅ |
| Anonymous | rel.create | POST /crm/leads | 401 | 401 | ✅ |
| Anonymous | task.create | POST /outcomes | 401 | 401 | ✅ |

## BLOCKER 2 — TENANT ISOLATION: PARTIAL

### Canonical ownership graph
```
User (TeamMember.id, email)
  → OrgMember (organization_id, identity_id=email, role)
    → Organization (id, name, legacy_tenant_id)
      → tenant boundary = organization_id
        → sh_objects (workspace_id isolation, data.tenant_id)
        → objects (tenant_id column, added 0008)
        → commitments (tenant_id column, added 0008)
        → evidence_records (tenant_id column, added 0008)
        → act_execution_logs (tenant_id column, added 0008)
        → leads (tenant_id → legacy tenants table)
        → customer (tenant_id)
        → knowledge_entries / memory_records / outcomes (tenant_id)
```

### Canonical tenant boundary
**Organization (organizations.id) is the canonical tenant boundary.** The legacy `tenants` table remains for team_members.tenant_id back-compat but is NOT the canonical authority. Session resolves `current_org_id` via OrgMember.

### Enforcement locations (wired)
1. `app/objects/routes.py::create` — `_resolve_tenant_id()` from session → OrgMember
2. `app/crm/routes.py::_resolve_tenant_from_session()` — ALL CRM routes now derive tenant from session, NOT request body. Cross-tenant body override blocked.
3. `app/founder/routes.py::api_list_founder_objects` — filtered by identity

### Enforcement gaps (remaining)
1. Legacy `objects` table read filtering (PATCH route at `/api/v1/objects/<id>`) not tenant-scoped
2. `identity_id` resolution inconsistency: founder_objects.created_by uses `sid_xxx` while session sometimes has integer user_id
3. No read filter on sh_objects by tenant (workspace_id is the only boundary)
4. Search endpoint not tenant-filtered
5. AI context retrieval not tenant-filtered

### Adversarial test results (real HTTP)
| Test | Result |
|------|--------|
| Org B create lead targeting Org A (tenant_id=1 body) | ✅ BLOCKED — session resolves to org 4, body override ignored |
| Org B create lead (own) | ⚠️ 500 — org 4 lacks entity_definition (setup gap, not isolation) |
| Org B read founder objects | ⚠️ Returns 200 but filtered by created_by (identity mismatch leaves gap) |
| Org B read legacy objects | ⚠️ 405 (wrong method) — read filtering not wired |

---

## REMAINING WORK

1. **Blocker 2 completion**: wire tenant filter into legacy objects PATCH/read, resolve identity_id consistency, tenant-filter search + AI context.
2. **Blocker 3 — Age/Safety governance**: implement canonical governance boundary.
3. **Blocker 4 — Gmail E2E**: requires founder OAuth consent action.
4. **Blocker 5 — Business workflow**: lead→customer→commitment→work→proof→result end-to-end.
5. **Final certification**: full report with PROVEN/PARTIAL/UNVERIFIED/FAILED classification.

---

*Honest status: Blocker 1 CERTIFIED. Blocker 2 PARTIAL (enforcement wired for writes, read filtering incomplete). Blockers 3-5 pending.*