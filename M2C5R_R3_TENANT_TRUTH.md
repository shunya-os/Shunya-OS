# M2C.5R — PHASE R3: TENANT/ORGANIZATION TRUTH
## Authority: M2C.5R §5 — Canonical Truth Recovery

---

## FINDING: TENANT IS THE PRODUCTION AUTHORITY

### FK Dependency Comparison

| Dependency | Tenant | Organization |
|------------|--------|-------------|
| Total FK references | 60+ tables | 40+ tables |
| documents | ✅ tenant_id FK | ❌ |
| leads | ✅ tenant_id FK | ❌ |
| persons | ✅ tenant_id FK | ❌ |
| team_members | ✅ tenant_id FK | ❌ |
| relationships | ✅ tenant_id FK | ❌ |
| opportunities | ✅ tenant_id FK | ❌ |
| messages | ✅ tenant_id FK | ❌ |
| notifications | ✅ tenant_id FK | ❌ |
| campaign_contents | ✅ tenant_id FK | ❌ |
| knowledge_entries | ✅ tenant_id FK | ❌ |
| memory_records | ✅ tenant_id FK | ❌ |
| outcomes | ✅ tenant_id FK | ❌ |
| payments | ✅ tenant_id FK | ❌ |
| fin_invoices | ❌ | ✅ organization_id FK |
| org_members | ❌ | ✅ organization_id FK |
| org_invitations | ❌ | ✅ organization_id FK |
| fin_ledger | ❌ | ✅ organization_id FK |
| auth_roles | ❌ | ✅ organization_id FK |
| g4_opportunities | ❌ | ✅ organization_id FK |

### Tenant Data (32 rows)
```
 89 | Panchi Club      | panchi-club      | t
 90 | Panchi.Club      | panchiclub       | t
 ...
```

### Organization Data (2 rows)
```
 7 | Panchi Club | panchi-club | legacy_tenant_id = NULL
 1 | Test Org    | test-org    | legacy_tenant_id = NULL
```

**Critical finding**: Neither Organization row has `legacy_tenant_id` set. There is no link between the 2 Organization records and the 32 Tenant records they purportedly supersede.

---

## VERDICT

| Claim | Status |
|-------|--------|
| Organization is the canonical successor | 🔴 FALSE — no migration path exists |
| All readers migrated | 🔴 FALSE — 60+ tables still read Tenant |
| All writers migrated | 🔴 FALSE — integrations, jobs, auth middleware write Tenant |
| FK paths migrated | 🔴 FALSE — no FK from Tenant→Organization |
| Legacy tenants reconciled | 🔴 FALSE — 32 tenants, 0 linked to Organization |
| Cross-tenant isolation proven | 🔴 NOT PROVEN |

**Tenant remains the sole production authority. Organization is an architectural proposal with no proven migration path.**

---

## REQUIRED ACTIONS

Before Organization can be declared canonical:

1. [ ] Map each of the 32 tenants to Organization records, or establish that Organization replaces Tenant
2. [ ] Set `legacy_tenant_id` on each Organization row
3. [ ] Migrate FKs from `tenant_id` to `organization_id` for at least the critical tables
4. [ ] Update auth middleware to use Organization model
5. [ ] Update integrations to use Organization model
6. [ ] Update background jobs to use Organization model
7. [ ] Prove cross-tenant isolation with Organization model
8. [ ] Only then: deprecate Tenant as read-only

---

## PHASE R3: COMPLETE
Proceeding to R4 — Object Convergence.