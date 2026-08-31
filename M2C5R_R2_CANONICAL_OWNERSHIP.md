# M2C.5R — PHASE R2: CONSTITUTIONAL CANONICAL OWNERSHIP MAP
## Authority: M2C.5R §4 — Canonical Truth Recovery
## Rule: One authoritative production owner per core concept. No second "temporary" production architecture.

---

## METHODOLOGY

For each concept, the canonical owner is determined by:

1. **Architecture**: Which model is named in the FDA/constitutional architecture docs
2. **Runtime dependency**: Which model has the most production readers/writers
3. **Business contract**: Which model matches the promised product capability
4. **Tenant model**: Which model correctly implements tenant isolation

Not by: schema richness, column count, or "which one Hermes likes best."

---

## CANONICAL OWNERSHIP TABLE

### TENANT

| Aspect | Decision |
|--------|----------|
| **Canonical owner** | **Tenant** (app/tenant.py, tenants table) |
| Rationale | 32 rows, used by integrations, auth middleware, background jobs, legacy routes. Organization has 1 row. Tenant is the production authority. |
| Non-canonical | Organization (organizations table) — proposed successor |
| Allowed relationship | Organization.legacy_tenant_id → Tenant.id |
| Migration status | ⚠️ NOT CONVERGED — org_routes were rewritten to use Organization, but all integrations, FK paths, and background jobs still use Tenant |
| **Verdict** | **Tenant remains canonical until Organization proves full read/write/FK/API/integration migration** |

### ORGANIZATION

| Aspect | Decision |
|--------|----------|
| **Canonical owner** | **Organization** (app/models.py, organizations table) |
| Rationale | Named successor to Tenant in FDA architecture. OrgMember, OrgInvitation, Department all reference it. Tests use it. |
| Non-canonical | Tenant — but Tenant is still the production authority for most paths |
| Allowed relationship | Organization.legacy_tenant_id → Tenant.id |
| Migration status | ⚠️ PARTIAL — org_routes rewritten, but integrations, auth middleware, and FK paths not migrated |
| **Verdict** | **Canonical destination, but not yet production authority. Tenant is still the real authority.** |

### WORKSPACE

| Aspect | Decision |
|--------|----------|
| **Canonical owner** | **FounderSpace** (app/founder/models.py, founder_spaces table) |
| Rationale | 3 rows (active), linked to identity_id, used by Executive Home, AI context, and the personal workspace flow. Has the most complete schema. |
| Non-canonical | Workspace (app/models.py, 1 row), sh_workspaces (3 rows), workspace_memberships (empty) |
| Allowed relationship | Workspace.tenant_id → Tenant.id via legacy; FounderSpace.identity_id → identity |
| Migration status | ⚠️ NOT CONVERGED — 3 workspace systems coexist, auto-creation only covers FounderSpace |
| **Verdict** | **Provisional canonical. Must prove all workspace paths converge.** |

### OBJECT

| Aspect | Decision |
|--------|----------|
| **Canonical owner** | **UNDECIDED** |
| Rationale | 5 competing systems. No single system has proven production authority. |
| Candidates | objects (41 rows, oldest), founder_objects (44 rows, most readers), sh_uop_objects (85 rows, richest schema but migration artifacts) |
| Required action | Architecture governance decision needed. Cannot be selected by schema richness. |
| **Verdict** | **🔴 UNDECIDED — no production authority until governance decides** |

### PERSON

| Aspect | Decision |
|--------|----------|
| **Canonical owner** | **persons** (app/models.py, persons table) |
| Rationale | 11 rows, linked to team_members via name/email. Used by documentation enrichment, AI context. |
| Non-canonical | None — no competing Person system |
| Migration status | ⚠️ PARTIAL — person_identities table exists but empty (0 rows). Persons are not linked to TeamMember or SHUNYAIdentity. |
| **Verdict** | **Canonical, but incomplete. Identity graph needs wiring.** |

### IDENTITY

| Aspect | Decision |
|--------|----------|
| **Canonical owner** | **SHUNYAIdentity** (app/production/identity_repository.py, shunya_identities table) |
| Rationale | 11 rows. Created by signup, linked to TeamMember.identity_id. Is the kernel identity system. |
| Non-canonical | TeamMember (auth), Person (persons) — both have identity-like fields |
| Allowed relationship | TeamMember.identity_id → shunya_identities; Person linked via person_identities |
| Migration status | ⚠️ PARTIAL — TeamMember.identity_id FK exists (commit efda28e), but Person→identity link missing |
| **Verdict** | **Canonical. Must wire Person→identity and close duplicate identity paths.** |

### RELATIONSHIP

| Aspect | Decision |
|--------|----------|
| **Canonical owner** | **relationships** (app/models.py, relationships table) |
| Rationale | Linked to persons, has tenant_id, used by commercial routes. |
| Non-canonical | rel_relationships (richer schema but 0 rows), founder_relationships (0 rows) |
| Migration status | ⚠️ ALL EMPTY (0 rows in all systems) |
| **Verdict** | **Canonical by default (only populated system). No real data to converge.** |

### DOCUMENT

| Aspect | Decision |
|--------|----------|
| **Canonical owner** | **documents** (app/models.py, documents table) |
| Rationale | 15 rows, used by extraction pipeline, knowledge_facts. |
| Non-canonical | knowledge_documents (0 rows), document_records (0 rows) |
| Migration status | ⚠️ PARTIAL — knowledge_entries=0, knowledge_documents=0. Pipeline stops at knowledge_facts. |
| **Verdict** | **Canonical. Pipeline needs to continue to knowledge_entries.** |

### MEMORY

| Aspect | Decision |
|--------|----------|
| **Canonical owner** | **memory_records** (app/memory/, memory_records table) |
| Rationale | 3 rows. Is the named memory system. |
| Non-canonical | knowledge_entries (0 rows), memory_candidates (0 rows) |
| Migration status | ⚠️ EMPTY — no real memory data |
| **Verdict** | **Canonical by naming. No real data to converge.** |

---

## DUPLICATE SYSTEM REGISTER

| Concept | Competing Systems | Canonical | Status |
|---------|------------------|-----------|--------|
| Tenant/Organization | 2 (Tenant, Organization) | Tenant (current), Organization (target) | 🔴 PARTIAL |
| Workspace | 3 (FounderSpace, Workspace, sh_workspaces) | FounderSpace (provisional) | 🔴 PARTIAL |
| Object | 5 (objects, founder_objects, sh_objects, canonical_objects, sh_uop_objects) | UNDECIDED | 🔴 UNDECIDED |
| Identity | 3 (SHUNYAIdentity, TeamMember, Person) | SHUNYAIdentity | 🟡 PARTIAL |
| Relationship | 2 (relationships, rel_relationships, founder_relationships) | relationships | 🟡 EMPTY |
| Document | 2 (documents, knowledge_documents, document_records) | documents | 🟡 PARTIAL |
| Memory | 2 (memory_records, knowledge_entries, memory_candidates) | memory_records | 🟡 EMPTY |
| Invoice | 2 (fin_invoices, invoices) | fin_invoices | 🟡 PARTIAL |

---

## PHASE R2: COMPLETE

Proceeding to R3 — Tenant/Organization Truth.