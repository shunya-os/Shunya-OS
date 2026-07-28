# SHUNYA Core Consolidation — Migration Plan

> **Directive:** FOR-2A
> **Status:** Planning Phase
> **Date:** 2026-07-26
> **Objective:** Consolidate all parallel implementations into a single canonical production architecture before expanding business capabilities.

---

## 1. Current Architecture Problem

SHUNYA currently has three parallel implementation layers:

| Layer | Purpose | Status |
|-------|---------|--------|
| **Legacy** (`app/models.py`, `app/tenant.py`, `app/auth.py`) | Original SQLAlchemy business models | **Production** — all live data |
| **Canonical** (`core/`, `app/shunya/`) | OS kernel + engines | **Transitional** — engines exist, pipeline partially wired |
| **FOR-1/FOR-2** (`app/for1/`, `app/for2/`) | Rapid product convergence | **Transitional** — duplicates legacy + canonical concepts |

This three-layer architecture creates:
- Duplicate model definitions (Lead/Proposal, Tenant/Organization)
- Split data (some in legacy tables, some in FOR tables)
- Confusing developer onboarding
- Risk of data inconsistency
- No clear migration path

---

## 2. Target Architecture

Single canonical layer. Every concept exists in exactly one place.

```
app/shunya/           ← Canonical engines (identity, knowledge, reasoning...)
app/models.py         ← Canonical business models (consolidated from legacy + FOR)
app/core_models.py    ← Canonical kernel/persistence models
app/routes.py         ← Canonical business routes (consolidated)
core/                 ← OS kernel, pipeline, runtime adapters
migrations/           ← Alembic migrations
```

---

## 3. Entity Consolidation Map

### 3.1 Organization

| Source | Target | Action |
|--------|--------|--------|
| `app/tenant.py:Tenant` | `app/models.py:Organization` | Merge. Add fields from `for2/models.py:Organization` to `Tenant`. Rename table to `organizations`. |
| `app/for2/models.py:Organization` | `app/models.py:Organization` | Fold into `Tenant`. Drop `for2_organizations` table. |
| `app/for2/models.py:OrgMember` | `app/models.py:OrgMember` | Promote to canonical. Table: `org_members`. |
| `app/for2/models.py:OrgInvitation` | `app/models.py:OrgInvitation` | Promote to canonical. Table: `org_invitations`. |
| `app/for2/models.py:Department` | `app/models.py:Department` | Promote to canonical. Table: `departments`. |

**Migration:** 
1. Add Organization fields to `Tenant` model
2. Create `org_members`, `org_invitations`, `departments` tables
3. Migrate data from `for2_*` tables
4. Rename `Tenant` → `Organization`, `tenants` → `organizations`
5. Drop `for2_*` tables

### 3.2 Identity

| Source | Target | Action |
|--------|--------|--------|
| `core/identity/IdentityEngine` | `core/identity/IdentityEngine` | Keep as canonical in-memory engine. Add persistence layer. |
| `app/kernel/identity.py:IdentityStore` | `core/identity/` | Fold into `IdentityEngine`. Remove duplicate. |
| `app/production/identity_repository.py:IdentityRepository` | `core/identity/IdentityEngine` | Make IdentityEngine use DB-backed store. Remove IdentityRepository. |
| `app/auth.py:TeamMember` | `app/models.py:IdentityMember` | Merge into org_members concept. Table: `org_members`. |
| `app/shunya/identity/` | `app/shunya/identity/` | Keep as canonical engine facade. |

**Migration:**
1. Add DB persistence methods to `IdentityEngine`
2. Replace `IdentityRepository` usage with `IdentityEngine`
3. Create `Identity` table mirroring `core/identity/models.py:Identity`
4. Migrate TeamMember data into org_members + Identity
5. Deprecate `app/kernel/identity.py`, `app/production/identity_repository.py`

### 3.3 Proposals

| Source | Target | Action |
|--------|--------|--------|
| `app/for1/models.py:Proposal` | `app/models.py:Proposal` | Promote to canonical. Table: `proposals`. |
| `app/for1/models.py:ProposalVersion` | `app/models.py:ProposalVersion` | Promote to canonical. Table: `proposal_versions`. |
| `app/for1/engine.py` | `app/engines/proposal_engine.py` | Move to engines directory. |
| `app/for1/routes.py` | `app/routes.py` | Merge route endpoints. |
| `app/for1/templates/` | `app/templates/for1/` | Move under canonical templates directory. |

**Migration:**
1. `proposals` and `proposal_versions` tables already exist — no data migration needed
2. Move engine code, routes, templates to canonical locations
3. Keep backwards-compatible redirects from old `/for1/` routes
4. Drop `app/for1/` module

### 3.4 Knowledge Documents

| Source | Target | Action |
|--------|--------|--------|
| `app/for1/models.py:KnowledgeDocument` | `app/models.py:KnowledgeDocument` | Promote to canonical. Table: `knowledge_documents`. |
| `app/for1/routes.py` (knowledge endpoints) | `app/routes.py` | Merge routes. |

**Migration:**
1. Table already exists — no data migration needed
2. Move routes to canonical locations
3. Keep backwards-compatible redirects

### 3.5 Relationships

| Source | Target | Action |
|--------|--------|--------|
| `app/models.py:Relationship` | `app/models.py:Relationship` | Keep as canonical. |
| `app/models.py:Person` | `app/models.py:Person` | Keep as canonical. Link to Identity. |
| `app/models.py:Lead` | `app/models.py:Opportunity` | Rename to Opportunity. Add relationship_type field. |
| `app/for2/` (future) | `app/models.py:Relationship` | Extend existing Relationship model. |

**Migration:**
1. Add `relationship_type` enum to Relationship model
2. Extend Lead → rename to Opportunity, add stages
3. Keep Person as canonical human profile, link to Identity

### 3.6 Finance

| Source | Target | Action |
|--------|--------|--------|
| `app/models.py:Invoice` | `app/models.py:Invoice` | Keep as canonical. |
| `app/models.py:Payment` | `app/models.py:Payment` | Keep as canonical. |
| `app/models.py:Supplier` | `app/models.py:Supplier` | Keep as canonical. Migrate to Relationship. |

**Migration:**
1. Add chart_of_accounts, general_ledger, journal_entry tables
2. Link all finance objects to organizations and relationships
3. Migrate Supplier → Relationship with type "supplier"
4. Add P&L, Balance Sheet, Cash Flow queries as views/reports

---

## 4. Route Consolidation Map

### 4.1 Production Routes (keep)

| Pattern | Source | Notes |
|---------|--------|-------|
| `/leads/*` | Legacy `app/routes.py` | Rename to `/opportunities/*` |
| `/invoices/*` | Legacy `app/routes.py` | Keep |
| `/payments/*` | Legacy `app/routes.py` | Keep |
| `/suppliers/*` | Legacy `app/routes.py` | Keep |
| `/tasks/*` | Legacy `app/routes.py` | Keep |
| `/auth/*` | Legacy `app/auth_routes.py` | Keep |
| `/api/v1/founder/*` | Founder `app/founder/routes.py` | Keep |
| `/api/v1/for2/*` | FOR-2 `app/for2/routes.py` | Migrate to `/api/v1/org/*`, drop `/for2/` |

### 4.2 Transitional Routes (move/rename)

| Pattern | New Pattern | Action |
|---------|-------------|--------|
| `/for1/*` | `/proposals/*` | Move templates + add redirect |
| `/api/v1/for1/*` | `/api/v1/proposals/*` | Move endpoints |
| `/for2/*` | `/org/*` | Move templates + add redirect |
| `/api/v1/for2/*` | `/api/v1/org/*` | Move endpoints |

### 4.3 Deprecated Routes (remove after migration complete)

| Pattern | Replacement | Removal Phase |
|---------|-------------|---------------|
| `/for1/proposals` | `/proposals` | Post-migration |
| `/for1/dashboard` | `/org/<id>/workspace` | Post-migration |
| `/for2/org/<id>` | `/org/<id>/workspace` | Post-migration |

---

## 5. Database Table Consolidation

### 5.1 Tables to Keep (canonical)

`leads`, `persons`, `person_identities`, `relationships`, `relationship_commitments`, `relationship_events`, `suppliers`, `invoices`, `payments`, `tasks`, `task_lists`, `notifications`, `documents`, `activity_logs`, `celebrations`, `tenants`, `tenant_themes`, `team_members`, `client_users`, `client_messages`, `customer_profiles`, `employee_profiles`, `supplier_contact_profiles`, `client_user_profiles`, `knowledge_facts`, `observations`, `learning_entries`, `proposals`, `proposal_versions`, `knowledge_documents`, `founder_spaces`, `founder_objects`, `founder_conversations`, `founder_messages`, `founder_relationships`

### 5.2 Tables to Add

`organizations` (rename from `tenants`), `org_members`, `org_invitations`, `departments`, `chart_of_accounts`, `general_ledger`, `journal_entries`, `opportunities` (rename from leads after extending)

### 5.3 Tables to Drop (after data migration)

`for2_organizations`, `for2_org_members`, `for2_org_invitations`, `for2_departments` — data migrated to canonical tables

### 5.4 Tables with Unclear Ownership

`ai_feedback`, `api_keys`, `automations`, `brands`, `business_groups`, `businesses`, `entities`, `entity_definitions`, `entity_modules`, `experiences`, `files`, `households`, `knowledge_entries`, `learning_candidates`, `login_codes`, `messages`, `oauth_accounts`, `opportunities`, `opportunity_activities`, `outcomes`, `relationship_preferences`, `user_activity_logs`, `user_daily_summaries`, `user_mood_checkins`, `user_sessions`, `webhook_logs`, `webhooks`

These 27 tables have no corresponding model. Each needs review: add model, add to migration, or drop if unused.

---

## 6. Implementation Sequence

### Phase 1: Model Consolidation (immediate)
1. Move FOR-2 tables to canonical `app/models.py` 
2. Add Organization, OrgMember, OrgInvitation, Department to `app/models.py`
3. Add Proposal, ProposalVersion, KnowledgeDocument to `app/models.py`
4. Create unified `app/routes.py` imports

### Phase 2: Route Consolidation
1. Migrate FOR-2 routes from `/api/v1/for2/*` to `/api/v1/org/*`
2. Migrate FOR-2 HTML routes from `/for2/*` to `/org/*`
3. Add permanent redirects from old to new routes
4. Migrate FOR-1 proposal routes similarly

### Phase 3: Identity Consolidation
1. Add DB persistence to `core/identity/IdentityEngine`
2. Create `identities` table mirroring `Identity` model
3. Replace `IdentityRepository` with persisted `IdentityEngine`
4. Migrate `TeamMember` → `OrgMember` + `Identity`

### Phase 4: Drop Parallel Tables
1. Migrate data from `for2_*` tables to canonical tables
2. Drop `for2_*` tables
3. Drop `app/for1/` module (keep routes until migration complete)
4. Drop `app/for2/` module (keep routes until migration complete)

### Phase 5: Cleanup
1. Remove deprecated route redirects
2. Remove `_legacy_*.py` wrappers
3. Update all tests to use canonical models
4. Update documentation

---

## 7. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data loss during migration | Critical | All migrations additive first. Drop tables only after verification. |
| Route breaking during rename | High | Keep old routes as redirects for one release cycle. |
| Identity data inconsistency | High | `IdentityEngine` currently in-memory. Add persistence before replacing `IdentityRepository`. |
| Schema migration conflicts | Medium | Use Alembic for all schema changes. Test migration against copy of production DB. |
| Developer confusion during transition | Medium | Document deprecated vs canonical clearly. Update all internal references before removing old code. |

---

## 8. Timeline

| Phase | Estimated Effort | Dependencies |
|-------|-----------------|--------------|
| Phase 1: Model Consolidation | 2-3 hours | None |
| Phase 2: Route Consolidation | 2-3 hours | Phase 1 |
| Phase 3: Identity Consolidation | 4-6 hours | Phase 1 |
| Phase 4: Drop Parallel Tables | 1-2 hours | Phases 1-3 |
| Phase 5: Cleanup | 2-3 hours | Phases 1-4 |

**Total estimated effort: 11-17 hours**

---

## 9. Immediate Next Steps

1. ✅ **(DONE)** Create canonical Organization, OrgMember, OrgInvitation, Department models (currently in `app/for2/models.py`)
2. ⬜ Move models to `app/models.py` with proper table names
3. ⬜ Create migration from `for2_*` tables to canonical tables
4. ⬜ Move FOR-2 routes to canonical `/api/v1/org/*` namespace
5. ⬜ Move FOR-1 proposal routes to canonical `/api/v1/proposals/*` namespace
6. ⬜ Add redirects from old routes
7. ⬜ Drop `app/for1/` and `app/for2/` modules
8. ⬜ Begin identity persistence work

---

*This plan will be updated as consolidation progresses. Every change must move toward the single canonical architecture, not add new parallel implementations.*