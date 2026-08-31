# M2C.5R — CONTAINMENT CERTIFICATE
## Date: 2026-08-30 | Authority: M2C.5 Remediation Directive (§20)
## Status: CONTAINMENT IN PROGRESS — MUTATIONS FROZEN

---

## 1. GIT TRUTH

| Field | Value |
|-------|-------|
| BRANCH | main |
| HEAD | 16a73ce |
| ORIGIN/MAIN | 16a73ce |
| AHEAD/BEHIND | 0/0 |
| WORKING TREE | 1 untracked file (this report) |
| STAGED | None |

### M2C.5 Commits (newest first)

| SHA | Date | Purpose | Files Changed |
|-----|------|---------|--------------|
| 16a73ce | 2026-08-30 | Register update | M2C5_RESIDUAL_GAP_REGISTER.md |
| fd757d8 | 2026-08-30 | §5 Doc enrichment | enrichment_pipeline.py, enrich_documents.py, register |
| 8907010 | 2026-08-30 | §4 Object migration | migrate_objects_v4.py, canonical.py, register |
| e82e7c2 | 2026-08-30 | Register/convergence update | M2C5_*.md |
| e0216b2 | 2026-08-30 | §3 Org/tenant rewrite | 7 files (org_routes, invitation_routes, workspace_routes, tests, auth) |

### Git Discipline Audit
- e0216b2: `git add -A` — violation of surgical Git rule
- fd757d8: `git add -A` — violation
- 16a73ce: `git add -A` — violation
- Result: All commits are narrow in changed files (only intended files modified), but the method violated the governance rule.

---

## 2. DEPLOYMENT TRUTH

| Field | Value | Source |
|-------|-------|--------|
| Repository HEAD | 16a73ce | `git rev-parse HEAD` |
| Origin HEAD | 16a73ce | `git rev-parse origin/main` |
| **Running PRODUCTION** | **5776cf6** | `/health` endpoint **NOT** 16a73ce |
| Build ID | 5776cf6 | `/health` response |
| Health | ok, DB connected | `/health` |
| Alembic version | f5429b50dbc6 | PG query |
| Service | Running | HTTP 200 |

**The register incorrectly claimed SHA fd757d8 as deployed. Production is actually running 5776cf6 — 4 commits behind HEAD.**

---

## 3. BACKUP

| Field | Value |
|-------|-------|
| Path | /tmp/shunya_backup_20260830.sqlc |
| Format | pg_dump custom (-F c) |
| Size | 795K |
| Timestamp | 2026-08-30 08:55 UTC |
| Checksum | Not computed (file available for md5sum) |
| **Status** | **POST-MUTATION backup.** Pre-mutation backup was not taken before enrichment ran. |

**WARNING**: This backup captures the post-M2C.5 state, including contaminated data. A pre-mutation state can be reconstructed from the reverse SQL below but does not exist as an independent dump.

---

## 4. MUTATION LEDGER

### 4a. Object Migration (scripts/migrate_objects_v4.py at commit 8907010)

| Field | Value |
|-------|-------|
| Timestamp | ~2026-08-30 08:35 UTC |
| Table | sh_uop_objects |
| Rows inserted | 85 (44 from founder_objects + 41 from objects) |
| Rows in source | founder_objects=44, objects=41 (unchanged) |
| Rows before | 0 |
| Rows after | 85 |
| Tenant | 1 (hardcoded) and legacy stored tenant_id from source |
| Provenance | metadata_json includes `migrated_from` |
| **Repeatable?** | **NO** — migration generates `uuid.uuid4()` per row, idempotency check compares against the just-generated UUID, guarantee duplicate on rerun |
| Reversibility | DELETE FROM sh_uop_objects WHERE metadata_json->>'migrated_from' IS NOT NULL |

**Critical bug**: Idempotency check is:
```
object_id = f"obj_{uuid.uuid4().hex[:16]}"
existing = UOPObject.query.filter_by(object_id=object_id).first()
```
This generates a new random ID, then checks if that random ID exists. It will never find a duplicate, so re-running creates 85 more rows every time.

### 4b. Document Enrichment (scripts/enrich_documents.py at commit fd757d8)

| Table | Rows Before | Rows Inserted | Rows After |
|-------|------------|---------------|------------|
| persons | 10 | 5 | 15 |
| person_identities | 0 | 5 | 5 |
| relationships | 0 | 5 | 5 |

**Rows created:**

| # | Table | ID | Value | Classification |
|---|-------|----|-------|---------------|
| 1 | persons | 403 | Patrick Sarracin | POSSIBLY VALID — name may be a real document entity |
| 2 | persons | 404 | "as the lead guest on the booking" | FALSE POSITIVE — sentence fragment |
| 3 | persons | 405 | "Booking Confirmation" | FALSE POSITIVE — document heading |
| 4 | persons | 406 | "Booking Reference" | FALSE POSITIVE — document field label |
| 5 | persons | 407 | "Visa Card" | FALSE POSITIVE — payment method label |
| 6 | person_identities | 5-9 | identity_type='document', identity_value='doc_15' | ALL WRONG — documents are provenance, not identity |
| 7 | relationships | 11-15 | type='document_mention', tenant_id=89 | ALL SUSPECT — tenant not verified |

### 4c. Tenant Contamination

| Rows | Assigned Tenant | Actual Owner Document | Issue |
|------|----------------|----------------------|-------|
| All 5 persons | tenant_id=89 | Document 15 (no tenant metadata) | First-tenant fallback — no proven relationship |
| All 5 relationships | tenant_id=89 | Document 15 | Same |
| All 85 objects | tenant_id=1 (hardcoded in code) | Varies by source | **Wrong** — tenant_id=1 does not exist in tenants table |

---

## 5. CONTAMINATED DATA QUARANTINE

### Classification of enrichment-created Persons

| ID | Name | Confidence | Ruling |
|----|------|-----------|--------|
| 403 | Patrick Sarracin | 0.7 (regex) | AMBIGUOUS — could be real but needs verification |
| 404 | as the lead guest on the booking | 0.5 | FALSE POSITIVE — sentence fragment, not a person |
| 405 | Booking Confirmation | 0.5 | FALSE POSITIVE — document element name |
| 406 | Booking Reference | 0.5 | FALSE POSITIVE — document field label |
| 407 | Visa Card | 0.5 | FALSE POSITIVE — payment method |

### Classification of enrichment-created person_identities

| ID | Person | Identity Type | Ruling |
|----|--------|--------------|--------|
| 5-9 | All 403-407 | 'document' | ALL WRONG — document is not an identity type |

### Classification of enrichment-created relationships

| ID | Person | Type | Ruling |
|----|--------|------|--------|
| 11 | Patrick Sarracin | document_mention | AMBIGUOUS — valid concept, wrong arch (document mentions are provenance, not relationship) |
| 12-15 | False positives | document_mention | FALSE POSITIVE — source records are not valid |

### Recommended Reversible Cleanup

```sql
-- Quarantine enrichment-created records (reverse the enrichment)
-- Step 1: Delete person_identities from enrichment
DELETE FROM person_identities WHERE created_at > '2026-08-30T08:40:00' AND identity_type = 'document';
-- Expected: 5 rows

-- Step 2: Delete relationships from enrichment
DELETE FROM relationships WHERE created_at > '2026-08-30T08:40:00' AND relationship_type = 'document_mention';
-- Expected: 5 rows

-- Step 3: Delete false-positive persons
DELETE FROM persons WHERE id IN (404, 405, 406, 407);
-- Expected: 4 rows

-- Step 4: Retain Patrick Sarracin (id=403) pending verification but remove tenant contamination
UPDATE persons SET tenant_id = NULL WHERE id = 403;
```

---

## 6. RE-OPENED CLASSIFICATIONS

### Organization/Tenant (was: RESOLVED → must be PARTIAL/TRANSITIONAL)

| Evidence | Status |
|----------|--------|
| org_routes use Organization model | Good — but reads still use Tenant internally |
| 32 legacy tenants still active, 1 canonical org | Not resolved |
| No FK migration from Tenant→Organization | Not complete |
| No integration check (Gmail, etc. use Tenant?) | Unknown |
| No workspace/object FK convergence | Not done |

### Personal Workspace (was: IMPLEMENTED → must be PARTIAL)

| Evidence | Status |
|----------|--------|
| Auto-creation on login wired | Works for new users |
| identity_id vs TeamMember.id fallback | identity_id may be empty string, creating duplicates |
| 3 workspace systems coexist | FounderSpace, Workspace, sh_workspaces — no canonical chosen |
| Multiple existing users may have unlinked personal workspaces | Unknown |

### Object Ownership (was: PARTIAL → must be UNDECIDED)

| System | Rows | Schema | Writers | Status |
|--------|------|--------|---------|--------|
| objects | 41 | Minimal (type, state, context) | Genesis, onboard | LEGACY |
| founder_objects | 44 | Rich (space, content, type) | Upload, AI, founder routes | PRIMARY CREATION |
| sh_uop_objects | 85 | Full (evidence, relationships, metadata) | Migration only | NEWLY POPULATED |
| canonical_objects | 0 | Medium | None | EMPTY |
| sh_objects | 4 | Medium | Minimal | EMPTY |

**No canonical owner selected.** The migration to sh_uop_objects was premature.

### False-Capability Count (was: 19 remaining → still 18 unresolved)

F-06 (KnowledgeStore) was correctly fixed. No other false capability was addressed.

---

## 7. TEST CHANGE AUDIT

| Test File | Change | Classification |
|-----------|--------|---------------|
| test_org_routes.py | Fixture: Tenant → Organization | LEGITIMATE — architecture convergence |
| test_org_routes.py | Removed `plan` assertion | **PROBLEMATIC** — test weakened without contract review. Plan may still be a required field. |
| test_org_routes.py | Updated field names (company_name→name mapping) | LEGITIMATE — backward-compat serialization |
| test_invitation.py | Fixture: Tenant → Organization | LEGITIMATE |
| test_invitation.py | Duplicate check: TeamMember → OrgMember | LEGITIMATE — invitation model changed |
| test_workspace_routes.py | Fixture: Tenant → Organization | LEGITIMATE |

**Restore required**: The `plan` assertion in `test_update_org_partial` was removed because Organization model lacks a plan field. If Plan is a required product capability, the field must be added to Organization, not removed from the test.

---

## 8. DATETIME POLICY

Application currently uses mixed datetime styles:
- `datetime.utcnow()` — naive UTC (deprecated)
- `datetime.now(timezone.utc)` — timezone-aware UTC
- SQLite tests accept naive timestamps

Current approach: converting to naive UTC for SQLite compat is wrong. **Resolution deferred** — use `datetime.now(timezone.utc)` everywhere, SQLite handles aware datetimes natively.

---

## 9. CI STATE

| Suite | Result | Notes |
|-------|--------|-------|
| production/identity | 71/71 pass | Pre-existing identity 3-failure issue: RESOLVED |
| production/auth | 110/110 pass | |
| organization + organizational | 9/9 pass | |
| **Total** | **190/190 pass** | No new failures from M2C.5 changes |
| Full suite (4996 tests) | **UNTESTED** | Known timeout issue — needs investigation |

---

## 10. RESOLVED vs CURRENT FINDINGS

Old register said: 85 findings, 12 launch blockers.
Register at 16a73ce said: 91 findings, 11 launch blockers (2 crossed out).

**Corrected state**:

| Category | Count |
|----------|-------|
| Historical findings | 85 |
| Resolved during M2C.5 | 6 |
| Currently active findings | 79 |
| — Launch blockers | 11 |
| — Environment blocked | 2 |
| — High priority | 48 |
| — Medium | 11 |
| — Not proven | 6 |
| — Degraded | 1 |

---

## 11. REMAINING ACTIONS

1. Run cleanup SQL to quarantine enrichment-created false positives
2. Fix object migration idempotency (`migrate_objects_v4.py`)
3. Restore test plan requirement or add plan field to Organization
4. Select canonical object owner constitutionally
5. Complete Tenant→Organization convergence
6. Resolve Workspace canonical owner
7. Take pre-mutation backup before any future data mutation
8. Re-archive contaminated UOPObject data pending canonical decision

---

## 12. CERTIFICATION STATUS

**NOT CERTIFIED — CONTAINMENT IN PROGRESS**

All mutations frozen until the above remediation steps are complete and independently verified.

Next: execute cleanup SQL, then fix migration idempotency, then present for Founder review before resuming M2C.5.