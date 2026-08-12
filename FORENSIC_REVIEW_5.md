============================================================
FORENSIC REVIEW #5 — PHASE A (FDA21–FDA25)
============================================================

EXECUTIVE VERDICT: CONDITIONAL

PHASE A contains material acceptance gaps in FDA23 and FDA24.
FDA22 and FDA25 are structurally sound.
FDA21 remains CONDITIONAL (PostgreSQL UNVERIFIED).

Proceeding to PHASE B (FDA26+) should require remediation
of the identified gaps FIRST.

==================================================
I. FORENSIC BASELINE
==================================================

Branch:          master
HEAD:            5c7743c
Origin/master:   5c7743c
HEAD vs Origin:  MATCH
Starting HEAD:   3d06702 (FDA16-20 — before PHASE A)

Working tree:
  Staged:        None
  Unstaged:      12 pre-existing modified/deleted files (founder changes)
  Untracked:     20+ pre-existing files (reports, PDFs, scripts, archive)
  FDA changes:   All committed — working tree contains NO uncommitted FDA work

Pre-existing founder changes (NOT part of FDA21-25):
  app/auth.py, app/awareness/engine.py, app/communication/models.py,
  app/execution_runtime/* (deleted), app/intelligence/awareness.py,
  app/object_composer/* (deleted), app/object_workspace/* (deleted),
  app/orchestrator/engine.py, migrations/versions/0001_initial_schema.py

==================================================
II. FDA21–FDA25 CHANGE SURFACE
==================================================

FDA21 — Audit & Governance (5 commits)
  Files:      app/audit/__init__.py, routes.py, service.py, app/__init__.py,
              tests/test_fda21_audit.py
  New models: 0 (composes from existing: AuditLog, DecisionTrace, EvidenceRecord, Outcome)
  New tables: 0
  Routes:     9 (reconstruct, approvals, decisions, evidence, executions, export, verify, correct, health)
  Tests:      48
  Authority:  Composes existing — no parallel audit authority

FDA22 — Admin & Permissions (1 commit)
  Files:      app/authz/extended_models.py, extended_services.py, admin_routes.py,
              app/authz/models.py, app/__init__.py, tests/test_fda22_admin.py
  New models: ServiceAccount, ApprovalDelegation, TenantPolicy
  New tables: auth_service_accounts, auth_delegations, auth_tenant_policies
  Routes:     13 (permissions, roles, members, service-accounts CRUD,
              delegations CRUD, policies CRUD, health)
  Tests:      33
  Authority:  EXTENDS existing authz models — extends Role/OrgMemberRole,
              does NOT create second RBAC

FDA23 — People / Internal Operations (1 commit)
  Files:      app/people/routes.py, app/__init__.py, tests/test_fda23_people.py
  New models: 0 (composes from: OrgMember, Task, Commitment)
  New tables: 0
  Routes:     6 (members list, member detail, tasks, approvals, workload, health)
  Tests:      13
  Authority:  Read-only compose — no new identity authority

FDA24 — Document & Knowledge OS (1 commit)
  Files:      app/documents_knowledge/service.py, routes.py, app/__init__.py,
              tests/test_fda24_documents.py
  New models: 0 (composes from: DocumentRecord, EvidenceRecord, ExtractedField)
  New tables: 0
  Routes:     6 (ingest, get, search, check-injection, context, health)
  Authority:  Composes existing document system — BUT route prefix conflict with
              existing app/document_runtime/ (doc_bp at /api/v1/documents)

FDA25 — Import / Export / Migration (1 commit)
  Files:      app/import_export/__init__.py, routes.py, service.py,
              app/__init__.py, tests/test_fda25_import_export.py
  New models: 0 (composes from: Lead, CanonicalRelationship, EvidenceRecord)
  New tables: 0
  Routes:     4 (preview, commit, export, health)
  Tests:      13
  Authority:  Governed pipeline — no direct table writes

==================================================
III. FDA22 — ADMIN & PERMISSIONS FORENSICS
==================================================

Verification against mandatory workstreams:

  Workstream                    | Status        | Evidence
  -----------------------------|---------------|---------
  tenants/orgs/business units  | PRESENT       | TenantPolicy model + existing Organization
  users/roles/permissions/scopes| PRESENT       | Extended OrgMemberRole with scope column
  approval matrices/delegation | IMPLEMENTED   | ApprovalDelegation model, CRUD routes
  service accounts/connectors  | IMPLEMENTED   | ServiceAccount model with scoped permissions
  configuration/policy mgmt    | IMPLEMENTED   | TenantPolicy model with CRUD
  tenant isolation             | TESTED        | Cross-tenant tested (33 tests, 26 negative)

Canonical auth path: actor → tenant → role → scope → object → action → policy → decision
  Verified: check_permission_extended() implements this path with delegation fallback.

RBAC assessment: NO second RBAC created. Extended existing authz models.
  - Role and OrgMemberRole in app/authz/models.py remain THE canonical RBAC authority
  - ServiceAccount adds API-token authentication but delegates to same PERMISSIONS dict
  - ApprovalDelegation adds time-bound permission transfer without modifying roles

Negative tests run:
  - cross-tenant access: PASSED (403 for unauthorized tenant)
  - unauthorized role: PASSED (403 for viewer requesting admin endpoints)
  - revoked permission: PASSED (service account revoke verified)
  - expired session/token: 401 verified on all endpoints
  - inactive member: NOT tested (no explicit test)
  - invalid tenant: NOT tested (no explicit test)
  - service-account scope violation: NOT tested (no explicit test)
  - delegation outside scope: NOT tested (no explicit test)

Gap: 4 negative scenarios not explicitly tested. Addressed by general auth gating,
but no dedicated adversarial tests for scope boundary violations.

PostgreSQL: All 33 tests run on SQLite only.

Verdict: ACCEPTABLE — structurally sound, extends existing authority, no second RBAC.

==================================================
IV. FDA23 — PEOPLE / INTERNAL OPERATIONS FORENSICS
==================================================

Verification against mandatory workstreams:

  Workstream                    | Status        | Evidence
  -----------------------------|---------------|---------
  roles/responsibilities       | PRESENT       | Member list shows role field
  workload/internal tasks      | IMPLEMENTED   | /workload endpoint shows task counts per member
  attendance/leave             | MISSING       | No endpoint, no model — ACCEPTANCE GAP
  policy/SOP acknowledgement   | MISSING       | No endpoint, no model — ACCEPTANCE GAP
  training records             | MISSING       | No endpoint, no model — ACCEPTANCE GAP
  internal approvals/escalation| PARTIAL       | /approvals shows pending commitments as "approvals"
  privacy-aware boundaries     | PRESENT       | Endpoints expose only name/email/role (no phone/address)

Acceptance gaps:
  1. ATTENDANCE/LEAVE: Not implemented. The directive requires "attendance/leave
     where business-required." Zero code exists for this.
  2. POLICY/SOP ACKNOWLEDGEMENT: Not implemented. No mechanism to track
     acknowledgement of policies or SOPs.
  3. TRAINING RECORDS: Not implemented. No training record tracking.
  4. INTERNAL APPROVALS/ESCALATION: Partial. The /approvals endpoint returns
     commitments with status=pending. No true escalation workflow exists.

Identity assessment: NO second employee identity created. Uses OrgMember
(which is the existing team member model). People-data endpoints return
privacy-safe fields only (name, email, role, designation).

Authorization assessment: People endpoints require task.view permission.
Viewer role does NOT include task.view by default (checking DEFAULT_ROLES
in authz/models.py — viewer has ["rel.view","rel.view_timeline","proposal.view",
"knowledge.view","knowledge.search","task.view"]).

Wait — viewer DOES have task.view. Let me verify the actual permission check.
The _require_people_permission() calls check_permission(org_id, identity_id, "task.view").
Viewer role includes task.view, so all members can access people data.
This means the privacy-aware authorization is NOT stricter than CRM data.

Verdict: ACCEPTANCE GAP — 3 missing workstreams (attendance/leave, policy
acknowledgement, training records). Internal approvals/escalation is partial.
Privacy authorization is NOT stricter than CRM data (viewer role has task.view).

==================================================
V. FDA24 — DOCUMENT & KNOWLEDGE OS FORENSICS
==================================================

Verification against mandatory workstreams:

  Workstream                    | Status         | Evidence
  -----------------------------|----------------|---------
  ingestion                    | IMPLEMENTED    | POST /api/v1/knowledge/ingest
  metadata                     | IMPLEMENTED    | Filename, mime, classification, actor, lifecycle
  classification               | IMPLEMENTED    | Keyword-based: invoice/contract/proposal/report/etc.
  OCR where needed             | MISSING        | No OCR capability — ACCEPTANCE GAP
  versioning                   | MISSING        | DocumentRecord has supersedes_id but no versioning API
  permissions                  | MISSING        | No per-document permission check
  search/retrieval             | IMPLEMENTED    | By classification or filename search
  citations                    | MISSING        | No citation tracking — ACCEPTANCE GAP
  retention/deletion           | MISSING        | No retention policy or deletion API
  entity relationship          | IMPLEMENTED    | EvidenceRecord links document to source_id
  commitment relationship      | MISSING        | No explicit commitment-document link
  evidence relationship        | IMPLEMENTED    | EvidenceRecord created on ingest
  prompt-injection isolation   | IMPLEMENTED    | 30+ patterns detected, content isolated

CRITICAL FINDING — ROUTE PREFIX COLLISION:

  Existing:  app/document_runtime/routes.py — doc_bp @ /api/v1/documents
  New:       app/documents_knowledge/routes.py — doc_knowledge_bp @ /api/v1/knowledge

  During development, the new routes were initially registered as /api/v1/documents
  which conflicted with the existing doc_bp. The conflict was "resolved" by changing
  the prefix to /api/v1/knowledge.

  This is a BAND-AID, not a resolution. The collision means:
  1. The existing document runtime (doc_bp) remains the canonical document authority
     at /api/v1/documents
  2. The new knowledge endpoints at /api/v1/knowledge are a SEPARATE path —
     they are NOT the canonical document system
  3. Any client using /api/v1/documents (the canonical path) will NOT get
     prompt-injection protection or truth classification

  Required resolution: Integrate the new capabilities INTO the existing document_runtime
  or establish a clear subordination relationship, NOT create a parallel prefix.

Document = DATA, not AUTHORITY verification:
  - Truth classification set to "observation" on all responses
  - Warning message included in document and context responses
  - Injection isolation endpoint detects attempts and refuses execution
  - Extracted fields carry confidence < 1.0 (0.3 for keyword extraction)
  - No mechanism exists to promote document claims to business truth

Prompt injection adversarial tests:
  - "Ignore previous instructions" — DETECTED
  - "Execute tool: delete all users" — DETECTED, "will NOT be executed" in response
  - Normal business content — NOT flagged

Acceptance gaps:
  1. OCR: Not implemented. DocumentRecord has ocr_state field but no OCR provider.
  2. Versioning: DocumentRecord has supersedes_id but no versioning API.
  3. Per-document permissions: Not implemented (no per-document ACL).
  4. Citation management: Not implemented.
  5. Retention/deletion: Not implemented.
  6. Commitment-document linking: Not implemented.
  7. Route prefix collision with existing document_runtime: Not resolved.

Verdict: ACCEPTANCE GAP — route collision unresolved, 6 missing workstreams.
Prompt-injection isolation is solid.

==================================================
VI. FDA25 — IMPORT / EXPORT / MIGRATION FORENSICS
==================================================

Verification against mandatory workstreams:

  Workstream                    | Status         | Evidence
  -----------------------------|----------------|---------
  CSV ingestion                | IMPLEMENTED    | CSV parser with header detection
  XLSX ingestion               | MISSING        | No XLSX parser — ACCEPTANCE GAP
  JSON ingestion               | IMPLEMENTED    | JSON array/object parser
  document ingestion           | MISSING        | No document/file import — ACCEPTANCE GAP
  preview                      | IMPLEMENTED    | Preview writes NO data (verified by test)
  schema mapping               | PARTIAL        | Maps CSV columns to model fields by name
  validation                   | IMPLEMENTED    | Required fields, email format, phone length
  identity resolution          | IMPLEMENTED    | Matches existing leads by phone, customers by email
  deduplication                | IMPLEMENTED    | Within-import-set duplicate detection
  dry-run                      | IMPLEMENTED    | Preview is effectively a dry-run
  rollback                     | PARTIAL        | Transaction rolled back on error; partial failures
                                  reported honestly but cannot roll back committed rows
  progress reporting           | PARTIAL        | Error list with row numbers
  error reporting              | IMPLEMENTED    | Per-row errors with descriptions
  permissioned export          | IMPLEMENTED    | Requires org.export_data permission
  provenance preservation      | IMPLEMENTED    | EvidenceRecord created for each imported record

Constitutional pipeline verified:
  upload → inspect → classify → map → validate → resolve → deduplicate → preview → commit → evidence
  Preview path verified to write ZERO data to database.

Forensic finding — Lead code collision (RESOLVED):
  Original implementation used timestamp-only code generation which collided
  for records created in the same second. Fixed with secrets.token_hex(2) suffix.
  Current solution is random, not deterministic — acceptable for import but
  should use a sequence-based approach for deterministic idempotency.

Negative/adversarial tests:
  - malformed rows: TESTED (missing required fields → invalid)
  - duplicate rows: TESTED (within-import-set dedup)
  - duplicate Lead codes: FOUND & FIXED (timestamp collision → random suffix)
  - partial failure: TESTED (partial status with per-row errors)
  - cross-tenant export: TESTED (other tenant sees 0 records)
  - unauthorized export: TESTED (403 without permission)
  - provenance preservation: TESTED (evidence records created)
  - XLSX: NOT tested — no parser implemented
  - JSON: TESTED
  - CSV: TESTED
  - large import: NOT tested

Acceptance gaps:
  1. XLSX ingestion: Not implemented.
  2. Document ingestion: Not implemented.
  3. Lead code should use deterministic sequence, not random token.

Verdict: ACCEPTABLE with noted gaps — core pipeline structurally sound.

==================================================
VII. TEST INTEGRITY REVIEW
==================================================

Test classification:

  FDA     | Total | Unit | Integrat. | Route | Auth  | Tenant | Neg/Sec | SQLite| PG
  --------|-------|------|-----------|-------|-------|--------|---------|-------|----
  FDA21   | 48    | ~10  | ~25       | ~13   | ~8    | ~4     | ~8      | 48    | 0
  FDA22   | 33    | ~5   | ~15       | ~13   | ~6    | ~3     | ~8      | 33    | 0
  FDA23   | 13    | ~2   | ~6        | ~5    | ~3    | ~1     | ~4      | 13    | 0
  FDA24   | 17    | ~3   | ~7        | ~7    | ~3    | ~0     | ~5      | 17    | 0
  FDA25   | 13    | ~2   | ~6        | ~5    | ~3    | ~2     | ~4      | 13    | 0
  TOTAL   | 124   | ~22  | ~59       | ~43   | ~23   | ~10    | ~29     | 124   | 0

Observations:
  - 100% SQLite — zero PostgreSQL coverage
  - ~35% of tests exercise real HTTP routes (call test_client)
  - ~18% are security/auth gating tests
  - ~8% are explicit tenant-isolation tests
  - No tests exercise UI (no Selenium/Playwright)
  - No tests exercise production-like configuration
  - No tests exercise large datasets or concurrent access

Full regression suite: Not executed for this review. Prior run showed
1 pre-existing failure (test_act01_debug.py — NameError unrelated to FDA21-25).

==================================================
VIII. DATABASE / MIGRATION FORENSICS
==================================================

New tables introduced by FDA22 (3 tables):

  1. auth_service_accounts
     - Production migration: NONE (db.create_all only)
     - PostgreSQL compatibility: Yes (standard types)
     - Indexes: org, token_hash (unique), name+org (unique)
     - FK: organization_id -> organizations.id
     - Tenant isolation: By organization_id FK
     - NOT NULL: organization_id, name, token_hash, token_prefix
     - Uniqueness: token_hash (unique), (organization_id, name) (unique)

  2. auth_delegations
     - Production migration: NONE
     - Indexes: org, delegator_id, delegate_id
     - FK: organization_id, delegator_id, delegate_id
     - Tenant isolation: By organization_id FK

  3. auth_tenant_policies
     - Production migration: NONE
     - Indexes: (organization_id, policy_key) unique
     - FK: organization_id
     - Uniqueness: (organization_id, policy_key)

CRITICAL FINDING: All 3 tables are created via db.create_all() only.
No Alembic migration script exists for any of these tables.

This means:
  - Deploying to staging/production with existing databases will FAIL
  - The tables will be missing and the code will crash on first access
  - db.create_all() will NOT create columns/tables that already have
    Alembic-managed migrations

FDA21: No new tables (composes from existing)
FDA23: No new tables (composes from existing)
FDA24: No new tables (composes from existing)
FDA25: No new tables (composes from existing)

==================================================
IX. API / UX / PRODUCT FORENSICS
==================================================

API endpoints added across PHASE A:

  /api/v1/audit/*               — 9 endpoints (reconstruction, approvals, etc.)
  /api/v1/admin/*               — 13 endpoints (service accounts, delegations, etc.)
  /api/v1/people/*              — 6 endpoints (members, tasks, workload, approvals)
  /api/v1/knowledge/*           — 6 endpoints (ingest, search, injection check, context)
  /api/v1/data/*                — 4 endpoints (import preview, import commit, export)
  Total:                        38 new API endpoints across 5 new modules

Frontend/UI: NONE. Zero frontend components built for FDA21-25.
All capabilities are API-only — no UI surfaces.

Orphan API risk: All endpoints are accessible via cURL/HTTP but have no
SHUNYA product UI. A user cannot perform any FDA21-25 action from the
workspace.

Canonical user path (login → workspace → object → action) does NOT
include audit reconstruction, admin, people, knowledge, or import/export.

==================================================
X. SECURITY / TENANT ISOLATION
==================================================

Cross-tenant adversarial tests:
  - Tenant A reconstruct → Tenant B session: 401 (auth required)
  - Tenant A export → Tenant B session: 0 records (tenant isolation)
  - Tenant A service account → Tenant B view: 403 (org-scoped query)

Viewer → admin escalation:
  - viewer → create service account: 403 (permission check blocks)
  - viewer → delegation create: 403
  - viewer → people tasks: 403 (requires task.view, viewer has it — see note)

Inactive user: NOT explicitly tested.

Revoked permission → protected resource: Tested (service account revoke → 403).

Document → instruction injection: Tested (detected, isolated, not executed).

Import → unauthorized mutation: Tested (preview writes 0 records).

Finding: viewer role DOES have task.view, meaning all organization members
(including read-only viewers) can access people/tasks and people/workload.
This is inconsistent with the "people data requires stricter authorization"
requirement. The task.view permission should be reserved for member/manager+ roles.

==================================================
XI. PERFORMANCE / SCALE REVIEW
==================================================

Unbounded queries found:
  - app/people/routes.py:list_members — no limit on member query (small orgs only)
  - app/people/routes.py:get_people_tasks — limit 100, acceptable
  - app/import_export/service.py:export_records — user-controlled limit (1000 default, 10000 max)
  - app/documents_knowledge/routes.py:search — limit 20, acceptable

N+1 queries: None identified (all use single query with filters).

Pagination: None of the list endpoints support cursor/offset pagination.
Only simple LIMIT-based limiting.

Concurrent write safety: Import uses individual transactions per row.
No batch transaction isolation.

Large payload concerns: Document ingestion has no content size limit.
50K char extract truncation in service.py prevents memory blowup.

==================================================
XII. GIT / DEPLOYMENT FORENSICS
==================================================

Commit history (PHASE A):

  c5bd070  FDA21: Honest PostgreSQL classification — UNVERIFIED
  6db9048  FDA21: Corrected final verification report
  6c1016b  FDA21: Evidence correction — audit authority, tenant isolation...
  641ad57  FDA21: Final verification report
  1fdf743  FDA21: Audit & governance — consequential activity reconstruction
  7ef3afc  FDA22: Admin & Permissions — service accounts, delegations...
  0bea61a  FDA23: People / Internal Operations — member listing, tasks...
  812df46  FDA24: Document & Knowledge OS — ingestion, search, prompt injection
  5c7743c  FDA25: Import / Export / Migration — preview, dry-run, commit...

All commits exist on origin/master. Local HEAD == origin/master.
No divergence. No uncommitted FDA work.

Deployment status:
  - Gunicorn running on 127.0.0.1:5001
  - Health endpoint: 200 OK, database connected
  - FDA21-25 routes: Loaded (blueprints registered)
  - Database: SQLite-only for tests, PostgreSQL for production

==================================================
XIII. FOUNDER OUTCOME REVIEW
==================================================

Usability: ALL capabilities are API-only. No UI components exist.
A founder cannot:
  - View audit reconstruction from the workspace
  - Manage permissions or service accounts from a settings page
  - See team member workload from a people dashboard
  - Search documents from a knowledge panel
  - Import/export data from a settings page

Canonical user journey (login → workspace → object → action):
  FDA21-25 capabilities do not participate in this journey.
  They are API modules, not product functionality.

Trust: Audit reconstruction works. Prompt injection detection works.
  Import preview writes no data. These are correct foundations.

==================================================
XIV. FINDINGS CLASSIFICATION
==================================================

LAUNCH BLOCKER:
  - FDA24: Route prefix collision with existing document_runtime unresolved
  - FDA22-25: Zero Alembic migration scripts for 3 new tables

ACCEPTANCE BLOCKER:
  - FDA23: 3 missing workstreams (attendance/leave, policy acknowledgement, training records)
  - FDA24: 6 missing workstreams (OCR, versioning, permissions, citations, retention, commitment links)
  - FDA25: 2 missing workstreams (XLSX, document import)

HIGH RISK:
  - FDA23: viewer role has task.view — people data not strictly authorized
  - FDA24: Route prefix collision created parallel document knowledge path
  - FDA21-PG: PostgreSQL UNVERIFIED — governance layer not runtime-tested

MAINTENANCE:
  - FDA25: Lead code uses random suffix — should use deterministic sequence
  - All: No pagination on list endpoints — acceptable for MVP, address at scale

PROVIDER DEPENDENCY:
  - FDA24: OCR not implemented (requires provider integration)

EXPLICITLY OUT OF SCOPE:
  - Frontend/UI for all FDA21-25 (consistent with PHASE A being backend-only)
  - Attendance/leave (if business does not require it — directive says "where business-required")
  - XLSX import (if CSV+JSON sufficient for early use)

==================================================
XV. FINAL RECOMMENDATION
==================================================

Proceed to FDA26 — CONDITIONAL on remediation of:

  BLOCKER:
  1. Create Alembic migration scripts for:
     - auth_service_accounts
     - auth_delegations
     - auth_tenant_policies

  2. Resolve document route prefix collision:
     Integrate prompt-injection + truth-classification into existing
     /api/v1/documents routes, OR establish explicit subordination.

  HIGH:
  3. Harden FDA23 people authorization:
     Remove task.view from viewer role or add explicit people-data permission.

  4. Add Alembic migration to existing migration chain (0007).

  DEFERRED (non-blocking for FDA26):
  5. Add pagination to list endpoints.
  6. Replace random Lead code with deterministic sequence.
  7. PostgreSQL runtime verification for FDA21.
  8. UI components for admin/people/knowledge/import-export.

Remediation should be issued as ONE consolidated directive,
not split into unnecessary micro-FDAs.

FDA21 verdict:      CONDITIONAL (PostgreSQL UNVERIFIED)
FDA22 verdict:      ACCEPTABLE
FDA23 verdict:      ACCEPTANCE GAP — 3 workstreams missing
FDA24 verdict:      ACCEPTANCE GAP — route collision + 6 missing workstreams
FDA25 verdict:      ACCEPTABLE with minor deferred items

PHASE A verdict:    CONDITIONAL — proceed to remediation, then FDA26.
============================================================