# M2C.5R — PHASE R1: REPOSITORY AND SYSTEM FORENSICS
## Authority: M2C.5R — Canonical Truth Recovery Directive
## Status: COMPLETE — Baseline established, no mutations

---

## 1. GIT TRUTH

| Field | Value |
|-------|-------|
| BRANCH | main |
| HEAD | 16a73ceda30acc66583d2fc6657a1db6df13c42d |
| HEAD_SHORT | 16a73ce |
| ORIGIN_MAIN | 16a73ce (ahead/behind: 0/0) |
| ORIGIN_MASTER | bdcf942 |
| WORKING TREE | 4 dirty files (3 untracked reports, 1 uncommitted test fix) |
| STAGED | None |

### Untracked files
- M2C5R_CONTAINMENT_CERTIFICATE.md (V1 — superseded)
- M2C5R_CONTAINMENT_CERTIFICATE_V2.md (V2 — current)
- M2C5_CLOSURE_REPORT_SESSION2.md (superseded by directives)

### M2C.5 Commits (newest → oldest)

| SHA | Date | Purpose | Files Changed |
|-----|------|---------|--------------|
| 16a73ce | 2026-08-30 | Register update + session summary | 1 file |
| fd757d8 | 2026-08-30 | §5 Doc enrichment (⚠️ CONTAMINATED) | 3 files |
| 8907010 | 2026-08-30 | §4 Object migration (⚠️ UNSAFE) | 3 files |
| e82e7c2 | 2026-08-30 | Register/convergence update | 2 files |
| e0216b2 | 2026-08-30 | §3 Org/tenant rewrite | 7 files |
| 5776cf6 | 2026-08-29 | Convergence matrix update | 1 file |
| 3d63d9b | 2026-08-29 | M2C.5 closure report | 1 file |
| a157edf | 2026-08-29 | F-06 KnowledgeStore fix | 1 file |
| 3403972 | 2026-08-29 | KnowledgeStore production-default | 1 file |
| 6986950 | 2026-08-29 | Convergence matrix + false-capability audit | 1 file |

---

## 2. DEPLOYMENT TRUTH

| Field | Value | Note |
|-------|-------|------|
| **Repository HEAD** | 16a73ce | — |
| **Origin/main** | 16a73ce | In sync |
| **Production SHA** | 5776cf6 | **4 commits behind HEAD** |
| Production status | ok, db=connected | — |
| Production uptime | 8411s (~2.3h) | — |
| Alembic version | f5429b50dbc6 | — |
| **Backup exists** | /tmp/shunya_backup_20260830.sqlc (795K) | MD5: 3ef86c49... |
| **Backup pre-mutation?** | NO | Post-mutation |
| **Restore verified?** | NO | shunya user lacks CREATEDB permission |

---

## 3. DATABASE TRUTH

| Table | Rows | Notes |
|-------|------|-------|
| organizations | 2 | Canonical org model |
| tenants | 32 | Legacy — still active |
| team_members | 11 | Auth users |
| shunya_identities | 11 | Canonical identity records |
| persons | 11 | 10 original + 1 (Patrick Sarracin, id=403, tenant=89 — AMBIGUOUS) |
| person_identities | 0 | Was 5, all deleted by cleanup |
| relationships | 0 | Was 5, all deleted by cleanup |
| documents | 15 | Uploaded documents |
| knowledge_facts | 53 | Extracted entities |
| knowledge_entries | 0 | Empty — pipeline broken |
| founder_objects | 44 | Legacy object store |
| objects | 41 | Legacy object store |
| sh_uop_objects | 85 | Migration target — QUARANTINE PENDING |
| sh_objects | 4 | Legacy object store |
| workspaces | 1 | General workspace |
| founder_spaces | 3 | Personal workspace |

---

## 4. TEST TRUTH

| Suite | Result | Evidence |
|-------|--------|----------|
| g4_commercial (34 tests) | 34/34 PASS | Verified this session |
| production/identity (71 tests) | 71/71 PASS | Verified prior session |
| production/auth (110 tests) | 110/110 PASS | Verified prior session |
| Full suite (4996 tests) | UNTESTED | Known timeout issue |

**CI failure fixed this session**: 3 tests in `test_g4_commercial.py::TestApiRoutes` were failing with 403 due to `_resolve_identity_session` middleware setting `identity_id="1"` while OrgMember expected `identity_id="admin@test.com"`. Root cause: test fixture gap — `s["identity_id"]` not set in session. Fixed by adding `s["identity_id"] = "admin@test.com"`.

---

## 5. KNOWN DATA CONTAMINATION

| Issue | Severity | Status |
|-------|----------|--------|
| 85 UOP objects from unsafe migration | 🔴 HIGH | Quarantine pending |
| Patrick Sarracin (id=403) with wrong tenant (89) | 🔴 HIGH | Unresolved |
| 4 false-positive Persons deleted — provenance caveat | 🟡 MEDIUM | Documented |
| 5 person_identities deleted — proxy predicate | 🟡 MEDIUM | Documented |
| 5 relationships deleted — proxy predicate | 🟡 MEDIUM | Documented |
| Document enrichment pipeline bypasses identity resolution | 🔴 HIGH | New rule needed |
| Migration idempotency broken (random UUIDs) | 🔴 HIGH | Must be fixed |

---

## PHASE R1: COMPLETE
Proceeding to R2 — Constitutional Canonical Ownership Map.