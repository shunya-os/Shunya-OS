# SHUNYA CANONICAL ARCHITECTURE — Phase A Decisions
## M2C.5 §4 — One Canonical System
**Date:** 2026-08-29 | **Git SHA:** 74722a5

## Canonical Ownership Lock

Every concept has exactly one canonical production authority. All competing implementations are classified.

| Concept | Canonical Owner | Status | Competing Systems | Action |
|---|---|---|---|---|
| Organization | `app.models.Organization` (tablename: organizations) | ✅ ACTIVE | tenants (LEGACY — 32 rows, 5 distinct orgs) | Mark tenants as LEGACY_READ_ONLY |
| Auth Identity | `app.auth.TeamMember` (tablename: team_members) | ✅ ACTIVE (8 rows) | — | Keep |
| Kernel Identity | `app.production.identity_repository.SHUNYAIdentityModel` (shunya_identities) | ✅ ACTIVE (2 rows) | — | Keep (sid_ format, different purpose) |
| Business Person | `app.models.Person` (tablename: persons) | ❌ EMPTY (0 rows) | — | MUST SEED — wire into signup/onboarding |
| Object | `app.models.Object` (tablename: objects) | ✅ ACTIVE (41 rows) | founder_objects (TRANSITIONAL — 44 rows), canonical_objects (DEPRECATED — 0 rows), sh_objects (TRANSITIONAL — 4 rows), sh_uop_objects (DEPRECATED — 0 rows) | Deprecate empty. Migrate founder_objects → objects. |
| Document | `app.models.Document` (tablename: documents) | ✅ ACTIVE (15 rows) | DocumentRecord (EMPTY), knowledge_documents (EMPTY) | Deprecate empty |
| Commitment | `app.commitments.models.Commitment` (tablename: commitments) | ✅ ACTIVE (5 rows) | — | Wire to UI |
| Invoice | `app.finance.models.FinInvoice` (fin_invoices) | ✅ ACTIVE (20 rows, NO API) | invoices (LEGACY — 0 rows) | Build finance API. Drop legacy invoices. |
| Evidence | evidence_records | ✅ ACTIVE (1 row) | — | Wire into more actions |
| Memory | memory_records | ❌ EMPTY (0 rows) | knowledge_entries (EMPTY), knowledge_documents (EMPTY) | Wire memory pipeline |
| Relationship | relationships (tablename: TBD) | ❌ EMPTY (0 rows) | rel_relationships (EMPTY), object_relations (EMPTY) | Pick ONE canonical store |
| Campaign | campaigns (tablename: campaigns) | ✅ ACTIVE (5 rows) | — | Keep |
| Lead | leads (tablename: leads) | ✅ ACTIVE (6 rows) | Lead (tablename: lead — 0 rows) | Wire to SalesPipeline UI |
| Event | wksp_events | ✅ ACTIVE (unknown rows) | — | Keep |

## Deprecation Actions (Level 4 — Permanent)

| Table | Rows | Status | Action | Method |
|---|---|---|---|---|
| canonical_objects | 0 | DEPRECATED | Add `__deprecated__ = True` marker. Remove model import from app.__init__.py if safe. | #1 |
| sh_uop_objects | 0 | DEPRECATED | Same as above | #1 |
| invoices (legacy) | 0 | LEGACY | Add DeprecationWarning at class level | #1 |
| rel_relationships | 0 | DUPLICATE | Add DeprecationWarning. Route commitments FK to canonical relationships table. | #1 |
| tenants | 32 | LEGACY_READ_ONLY | Keep table intact. No new writes. All new writes go to organizations. | #2 (next phase) |
| knowledge_documents | 0 | SEPARATE PURPOSE | Keep as-is — used for extracted knowledge (different from memory_records) | No action |

## Immediate Fixes (from Phase A execution)

| Fix | Status | Component |
|---|---|---|
| Commitment API works (200, 5 rows) | ✅ VERIFIED | app/commitments/routes.py |
| Sales pipeline API returns data | ✅ VERIFIED | app/sales_intelligence/routes.py |
| Deprecation markers on 4 empty tables | 🔄 SUBAGENT | app/models.py, app/relationship/ |
| Wire memory_records from AI pipeline | 🔄 SUBAGENT | app/memory_api/, app/intelligence/routes.py |
| Wire commitment data to UI | 🔄 SUBAGENT | frontend/src/components/commitment/ |

## SHUNYA SYSTEM TRUTH MANIFEST

Created: `SHUNYA_SYSTEM_TRUTH_MANIFEST.yaml` — machine-readable YAML inventory of every capability, canonical owner, duplicates, status, and action. This supersedes all prior manifest/architecture documents as the single source of truth for completion tracking.