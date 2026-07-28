# SHUNYA Constitutional Platform Map — Dependency Audit & Legacy Boundary

> **Document Type:** Constitutional Architecture  
> **Directive:** FOR-2C.4  
> **Status:** Ratified  
> **Date:** 2026-07-26  

This document establishes the irreversible architectural boundary for SHUNYA. After this phase, every future domain depends exclusively on canonical architecture.

---

## 1. Canonical Platform Map

```
                            ┌──────────────────┐
                            │   SHUNYA Identity │
                            │ (core/identity/)  │
                            └────────┬─────────┘
                                     │ owns
                            ┌────────▼─────────┐
                            │   Organization    │
                            │ (app/models.py)   │
                            └────────┬─────────┘
                                     │ belongs to
                          ┌──────────┴───────────┐
                          │   Org Membership      │
                          │ (OrgMember, Roles)    │
                          └──────────┬───────────┘
                                     │ interacts with
                          ┌──────────▼───────────┐
                          │   Relationship        │◄──────────────┐
                          │ (CanonicalRel, AI    │               │
                          │  Memory, Timeline)   │               │
                          └──────────┬───────────┘               │
                                     │                           │
                 ┌───────────────────┼───────────────────┐       │
                 │                   │                   │       │
        ┌────────▼────────┐ ┌───────▼───────┐ ┌─────────▼────┐  │
        │   Knowledge     │ │   Proposal    │ │ Communication │  │
        │ (app/knowledge/)│ │ (app/for1/ → │ │ (future)      │  │
        │                 │ │  app/proposal)│ │               │  │
        └────────┬────────┘ └───────┬───────┘ └───────────────┘  │
                 │                  │                            │
                 └──────────────────┼────────────────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │    Authorization Engine         │
                    │ (app/authz/ — Roles, Perms)    │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │    Universal Search             │
                    │ (app/relationship/search.py)    │
                    └────────────────────────────────┘
```

**Every future module must consume only this canonical stack.**

---

## 2. Dependency Audit

### 2.1 Canonical Modules (Safe for Future Development)

| Module | Dependencies | Status |
|--------|-------------|--------|
| `app/models.py:Organization` | `db.Model` | ✅ Canonical |
| `app/models.py:OrgMember` | `Organization` | ✅ Canonical |
| `app/models.py:OrgInvitation` | `Organization` | ✅ Canonical |
| `app/models.py:Department` | `Organization` | ✅ Canonical |
| `app/relationship/models.py:CanonicalRelationship` | `Organization` | ✅ Canonical |
| `app/relationship/models.py:TimelineEntry` | `Organization, CanonicalRelationship` | ✅ Canonical |
| `app/relationship/models.py:RelationshipMemory` | `Organization, CanonicalRelationship` | ✅ Canonical |
| `app/relationship/services.py` | Canonical models only | ✅ Canonical |
| `app/relationship/routes_api.py` | Canonical services | ✅ Canonical |
| `app/relationship/search.py` | Canonical models, Proposal | ✅ Canonical |
| `app/relationship/integration.py` | Canonical models | ✅ Canonical |
| `app/authz/models.py:Role` | `Organization` | ✅ Canonical |
| `app/authz/models.py:OrgMemberRole` | `Organization, OrgMember, Role` | ✅ Canonical |
| `app/authz/services.py` | Canonical models | ✅ Canonical |
| `app/for1/models.py` | (empty — re-exports from `app.models`) | ✅ Transitional (re-export) |

### 2.2 Transitional Modules (Being Migrated)

| Module | Canonical Deps | Legacy Deps | Migration Plan |
|--------|---------------|-------------|----------------|
| `app/for1/routes.py` | `app.models.Proposal`, `app.relationship.integration` | `app.tenant.Tenant` | Migrate to `app/proposal/` in FOR-2D |
| `app/for1/engine.py` | `app.models.Proposal` | None | Move to `app/proposal/services.py` |
| `app/for2/routes.py` | `app.models.Organization`, `OrgMember` | `app.tenant.Tenant` | Move to `app/organization/` in FOR-2D |
| `app/relationship/routes_ui.py` | Canonical models | None | Keep, already canonical domain |
| `app/founder/routes.py` | Canonical identity | `app.tenant.Tenant` | Keep as transitional |

### 2.3 Legacy Modules (Not for New Development)

| Module | Reason | Status |
|--------|--------|--------|
| `app/models.py:Lead` | Superseded by Relationship + Opportunity | 🟡 Transitional — not available for new code |
| `app/models.py:Supplier` | Superseded by Relationship(type=supplier) | 🟡 Transitional |
| `app/models.py:Person` | Superseded by Identity + Relationship | 🟡 Transitional |
| `app/tenant.py:Tenant` | Superseded by Organization | 🟡 Legacy — compatibility only |
| `app/auth.py:TeamMember` | Superseded by OrgMember | 🟡 Legacy — compatibility only |
| `app/models.py:Relationship` (legacy) | Superseded by CanonicalRelationship | 🔴 Legacy — do not reference |
| `app/models.py:RelationshipEvent` | Superseded by TimelineEntry | 🔴 Legacy — do not reference |
| `app/models.py:RelationshipCommitment` | Superseded by Timeline AI Memory | 🔴 Legacy — do not reference |

### 2.4 Retired/Cleaned Up

| Module | Retirement Date | Reason |
|--------|----------------|--------|
| `app/for2/models.py` (old content) | FOR-2A | Replaced by `app/models.py` canonical models |
| `app/for1/models.py` (old content) | FOR-2A | Replaced by `app/models.py` canonical models |
| `authz_roles`, `authz_member_roles` tables | FOR-2C.3 | Stale table names, replaced by `auth_roles`, `auth_member_roles` |
| `for2_organizations`, `for2_org_members`, etc. | FOR-2A | Data migrated to canonical tables |

---

## 3. Legacy Isolation Report

### 3.1 Isolation Rules

1. **No new code** may import from `app.tenant.Tenant`, `app.auth.TeamMember`, or `app.models.py` legacy relationship models.
2. **No new foreign keys** may reference `tenants`, `team_members`, or `relationships` tables.
3. **No new routes** may expose legacy models directly.
4. **All legacy modules** are clearly marked with `# TRANSITIONAL` or `# LEGACY — do not reference` comments.
5. **New domain blueprints** must be registered in canonical folder structure (e.g., `app/{domain}/`), not in legacy `app/for*/` namespaces.

### 3.2 Current Legacy References (Acceptable for Transition)

The following legacy tables still have active FK references from canonical tables:

| Legacy Table | Referenced By | Status |
|-------------|---------------|--------|
| `tenants` | `organizations.legacy_tenant_id` | ✅ Acceptable — compatibility FK |
| `tenants` | 44+ other tables (sensitivity_assessments, etc.) | 🟡 Pre-migration — all pre-date FOR-2A |
| `team_members` | 22+ tables (oauth_accounts, user_sessions, etc.) | 🟡 Pre-migration |
| `relationships` (legacy) | 5 tables (experiences, opportunities, etc.) | 🟡 Pre-migration |
| `leads` | 5 tables (celebrations, tasks, proposals) | 🟡 Pre-migration |

These are not blocks for new development. New code must not contribute additional legacy references.

### 3.3 Firewall

The following import guards are in effect:

- ✅ `app.authz/services.py` imports `OrgMember` from `app.models` (canonical), not `app.for2.models`
- ✅ `app/relationship/*` imports models from `app.relationship.models` or `app.models`
- ✅ `app/for1/routes.py` imports `Tenant` only for backward-compat route handlers — new routes use canonical Organization
- ✅ `app/for2/routes.py` imports `Tenant` only for backward-compat — new Organization routes use canonical models

---

## 4. Finance Readiness Certification

Finance Intelligence can be implemented using **only** the canonical architecture:

| Finance Requirement | Canonical Source | Verification |
|--------------------|-----------------|--------------|
| Organization scope | `Organization` model | ✅ All canonical entities have `organization_id` |
| Customer/vendor identity | `CanonicalRelationship` | ✅ Relationship types: customer, supplier, vendor |
| Invoice → Relationship | `Proposal.relationship_id` pattern | ✅ Same FK pattern available for invoices |
| Payment tracking | `Relationship` + `TimelineEntry` | ✅ Payments recorded as timeline events |
| Financial reporting | `Organization` + `Relationship` + `TimelineEntry` | ✅ Query by org + rel + event type |
| Authorization | `authz/*` (Roles, Permissions) | ✅ 43 permission keys including `finance.*` |
| Audit trail | `TimelineEntry` (immutable) | ✅ All financial events logged as timeline entries |
| AI insights | `RelationshipMemory` | ✅ AI memory accumulates financial context |

**No dependency on `Tenant`, legacy `Relationship`, `TeamMember`, or legacy permission systems is required for Finance Intelligence.**

---

## 5. Legacy Register

| # | Component | Type | Why It Exists | Runtime-Critical? | Removal Phase |
|---|-----------|------|---------------|-------------------|---------------|
| 1 | `app/tenant.py:Tenant` | Model | Original org model, data pre-dates canonical Organization | ✅ Data still needed | FOR-2D (migrate data → canonical `Organization`) |
| 2 | `app/auth.py:TeamMember` | Model | Original user model | ✅ Auth relies on it | FOR-2D (migrate → `OrgMember` + `Identity`) |
| 3 | `app/models.py:Relationship` (legacy) | Model | Pre-canonical relationship data | ✅ Data still referenced by legacy tables | FOR-2E |
| 4 | `app/models.py:RelationshipEvent` | Model | Pre-canonical timeline data | ✅ Data exists | FOR-2E |
| 5 | `app/models.py:RelationshipCommitment` | Model | Pre-canonical AI memory | ✅ Data exists | FOR-2E |
| 6 | `app/models.py:Person` | Model | Pre-canonical person profiles | ✅ Used by intake, legacy routes | FOR-2E |
| 7 | `app/models.py:PersonIdentity` | Model | Pre-canonical identity | ✅ Used by intake | FOR-2E |
| 8 | `app/models.py:Lead` | Model | Pre-canonical opportunities | ✅ Active business data | FOR-2D |
| 9 | `app/models.py:Supplier` | Model | Pre-canonical vendor data | ✅ Active business data | FOR-2E |
| 10 | `app/models.py:Invoice` | Model | Active business data | ✅ Critical | FOR-2D (migrate → canonical Finance) |
| 11 | `app/models.py:Payment` | Model | Active business data | ✅ Critical | FOR-2D (migrate → canonical Finance) |
| 12 | `app/models.py:Task` | Model | Active business data | ✅ Used in operations | FOR-2E |
| 13 | `app/for1/routes.py` | Routes | Proposal API routes | ✅ Critical | FOR-2D (move to `app/proposal/`) |
| 14 | `app/for1/engine.py` | Service | Proposal generation logic | ✅ Critical | FOR-2D (move to `app/proposal/`) |
| 15 | `app/for1/templates/` | UI | Proposal templates | ✅ Critical | FOR-2D (move to `app/proposal/templates/`) |
| 16 | `app/for2/routes.py` | Routes | Organization API routes | ✅ Critical | FOR-2D (move to `app/organization/`) |
| 17 | `app/for2/templates/` | UI | Organization templates | ✅ Active | FOR-2D (move to `app/organization/templates/`) |
| 18 | `app/founder/routes.py` | Routes | Founder experience | ✅ Active | Keep (already canonical pattern) |
| 19 | `app/founder/models.py` | Models | Founder-specific data | ✅ Active | Keep (already canonical pattern) |
| 20 | Legacy `tenants` table | Data | Original org data, 44+ FK references | ✅ Active | FOR-2D/2E (migrate, drop table) |
| 21 | Legacy `team_members` table | Data | Original user data | ✅ Active | FOR-2D/2E |
| 22 | Legacy `relationships` table | Data | Original relationship data | ✅ Active | FOR-2E |
| 23 | `app/models.py:Tenant` FK ref | FK | 44 legacy tables reference tenants | ❌ Not critical | FOR-2E (migrate to `organization_id`) |
| 24 | `app/shunya/*/_legacy_*.py` | Code | Legacy engine wrappers | ❌ Not critical | FOR-2E (remove after pipeline wired) |

**Total: 24 legacy items. All documented. All have planned retirement phases.**

---

## 6. Constitutional Verification

### 6.1 New Domain Checklist

Every future module must pass these checks before merging:

```python
# Template for new domains — every new module must answer:
MODULE_ACCEPTANCE = {
    "domain": "finance",  # Must match one of 15 canonical domains
    "organization_scoped": True,  # Must have organization_id
    "relationship_integrated": True,  # Must reference Relationship where applicable
    "event_driven": True,  # Must emit/consume canonical events
    "authorization_consumed": True,  # Must use authz.check_permission()
    "legacy_dependencies": [],  # Must be empty
    "canonical_dependencies": ["organization", "relationship", "authz"],  # Only canonical
}
```

### 6.2 Constitutional Rules

1. **Organization-first.** Every entity MUST have `organization_id`.
2. **Relationship-centric.** Every person/organization interaction MUST use `CanonicalRelationship`.
3. **No legacy imports.** No new code may import from `app.tenant`, `app.auth.models` (legacy), or legacy `app.models.Relationship`.
4. **Authz-gated.** Every permission check MUST use `authz.check_permission()`.
5. **Event-recorded.** Every business event MUST be recorded in `TimelineEntry`.
6. **Canonical folder.** New domains MUST live in `app/{domain_name}/` — never in `app/for*/`.
7. **Industry-agnostic.** New capabilities MUST NOT hardcode travel-specific terminology.

---

*This constitution is effective immediately. All future development shall build exclusively upon canonical architecture. FOR-2D (Finance Intelligence) is authorized to proceed.*