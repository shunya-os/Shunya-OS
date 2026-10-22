# G1.21 — Workspace architecture decision record

**Status:** decision made — **retain four distinct representations, do not
consolidate**; `founder_spaces` retirement is deferred to an owner-authorized
migration plan. No consolidation, no drops, no backfill was performed in G1.21.
**Authority:** G1.21 Workstream E. Builds on the G1.20 inventory (§21.4) and adds
read/write-authority evidence from source.

---

## 1. Canonical ownership and scope (per representation)

| Representation | Table(s) | Scope it represents | Authoritative for |
|---|---|---|---|
| Canonical workspace | `sh_workspaces` + `sh_workspace_memberships` | An **organization-owned** container for business objects | Object ownership and object authorization. `sh_objects.workspace_id` is NOT NULL and now has an enforced FK to `sh_workspaces.id` (r6b34) |
| Organization workspace API record | `workspaces` (`tenant_id`, `slug`) | A named sub-space of an organization, exposed by `/api/v1/orgs/<id>/workspaces` | Only that API projection; it is not consulted by object authorization |
| Personal scope | `user_workspaces` + `user_workspace_memberships` | A **personal** (no-organization) container for one identity | Personal-scope resolution only (`WorkspaceScope.PERSONAL`) |
| Legacy founder space | `founder_spaces` | A founder-era container (personal or organization typed) | Legacy compatibility for older accounts; not an ownership authority |

**They are not equivalent concepts.** The decisive difference is *what identifier
the object layer accepts*: `resolve_current_workspace()` returns only an
`sh_workspaces.id`, and explicitly documents that it never returns a
`user_workspaces.workspace_id` or a `FounderSpace.space_id`
(`app/authz/workspace_context.py:139-155`).

## 2. Read / write authority (source evidence)

| Table | Writers | Readers | Authority |
|---|---|---|---|
| `sh_workspaces` | `org_provisioning.ensure_organization_workspace()` (org creation, onboarding repair); `workspace_routes` does **not** write it; migrations seed `spc_*` system rows | `ObjectService`, `app/objects/routes.py`, `authz/workspace_context.py`, `authz/workspace_membership.py`, `founder/routes.py` (reads `sh_workspaces` for space views), `intelligence/service.py` (raw SQL by `created_by`) | **AUTHORITATIVE** for object ownership |
| `sh_workspace_memberships` | `org_provisioning._ensure_membership()` + `grant_workspace_access()` (org creation, invitation acceptance) | the authorization predicate (`authorized_workspace_ids`) | **AUTHORITATIVE** for object authorization |
| `workspaces` | `production/identity/workspace_routes.py::create_workspace` — writes `tenant_id=org_id` (an **organization id** in a column named `tenant_id`) | same module (CRUD only) | PROJECTION. No other module imports `workspace_model.Workspace` |
| `user_workspaces` | `auth_routes._ensure_personal_workspace()` at email verification (`owner_identity_id = str(member.id)`, i.e. the numeric TeamMember id) | `authz/workspace_context.resolve_workspace_scope()` (personal detection, with identity reconciliation), `app/workspace/routes.py` (`resolve_context`), `app/ai/routes.py` | AUTHORITATIVE only for personal scope |
| `user_workspace_memberships` | same signup path | same readers | personal-scope authorization |
| `founder_spaces` | `app/routes.py` (`POST /orgs`, org-typed), `auth_routes._ensure_personal_workspace_for_user()` (personal-typed, `identity_id = str(user.identity_id or user.id)`) | `workspace_context.resolve_workspace_scope()` (legacy personal fallback), `founder/*`, `intelligence/service.py` | COMPATIBILITY. Removal would break older accounts' personal scope |

## 3. Consistency guarantees (what is actually guaranteed)

1. **One canonical workspace per organization at creation** — guaranteed by
   `ensure_organization_workspace()` inside the organization transaction, and
   re-verified after G1.21 removed the implicit commit from `seed_default_roles`
   (before that fix, a workspace-provisioning failure could persist an organization
   with **no** workspace).
2. **Workspace ↔ organization ownership is enforced by the database** for objects:
   `sh_objects.workspace_id` FK → `sh_workspaces.id` (r6b34), plus
   `ObjectService.create()`'s own workspace-ownership check.
3. **Membership is per (workspace, identity)** and role-derived from the
   organization role (`owner→owner, admin→admin, manager/member→member,
   viewer→viewer`); no upward mapping.
4. **No consistency guarantee exists between the four representations.** Nothing
   keeps `workspaces`, `user_workspaces` and `founder_spaces` in step with
   `sh_workspaces`; they are independent rows with independent lifecycles and
   independent identity keying. This is a known, accepted boundary — not a bug
   being hidden.
5. `POST /orgs` writes a `founder_spaces` row *and* the canonical workspace in the
   same transaction (dual-write, not convergence). `founder_spaces` is therefore a
   compatibility record, never a source of truth.

## 4. Consolidation decision

**Decision: retain.** Consolidating would require deciding, for each of the three
non-canonical tables, whether existing rows are migrated, projected, or abandoned —
and each choice changes the personal-scope and founder-era behaviour of existing
accounts. The current code already fails closed when tenant context is wrong, so
distinct models are the safer architecture: fewer irreversible steps, no data
movement, no cross-tenant risk.

What *was* consolidated in G1.19–G1.21 is the **provisioning implementation**: one
function (`ensure_organization_workspace`) and one access-grant function
(`grant_workspace_access`) serve every path that creates or joins a tenant. That is
the part where duplication caused real defects.

## 5. Retirement requirements (`founder_spaces`), if ever selected

Not authorized now. A retirement plan would have to:

1. Enumerate every consumer (at minimum: `authz/workspace_context.py` personal
   fallback, `app/routes.py`, `auth_routes.py`, `founder/*`, `intelligence/service.py`).
2. Provide an equivalent personal-scope record for every legacy account before the
   table stops being written (otherwise older accounts lose PERSONAL scope and every
   API call is denied).
3. Backfill `user_workspaces` for accounts whose only personal record is a
   `FounderSpace` — including resolving the two incompatible identity keys
   (`str(member.id)` vs `canonical identity_id`).
4. Keep a read-only compatibility window; no drop in the same release.

## 6. Validation / rollback / recovery

* Validation available today: `tests/test_org_workspace_lifecycle.py` (8 tests),
  `tests/test_g121_provisioning_atomicity.py` (10 tests, incl. 6 fault-injection
  boundaries), `tests/test_g121_invitation_journey.py` (workspace access granted on
  acceptance), `tests/test_g121_onboarding_journey.py`.
* Recovery for a workspace-less organization: `ensure_organization_workspace()` is
  idempotent and is invoked on onboarding completion, so a legacy tenant is repaired
  on its next completion — no bulk backfill required, none performed.
* Rollback of the new constraints: `alembic downgrade r6b33_personal_workspace_tables`
  drops exactly the constraints/indexes added by r6b34 (verified: 53 → 33 FKs, then
  back to 53) and destroys no row. r6b33/r6b35/r6b36/r6b37 are additive-only and
  document that their downgrade is intentionally not data-destructive.

## 7. Owner decisions

1. **E-1 — Accept "retain distinct models" as the architecture of record?**
   Recommendation: yes (this record). No code change results from accepting it.
2. **E-2 — Personal-scope identity keying.** `user_workspaces.owner_identity_id`
   holds the numeric TeamMember id while organization scope uses the canonical
   `sid_*`. Resolution compensates for both forms, but the storage is ambiguous.
   Recommendation: converge on the canonical identity id in a future migration with
   a reconciliation step. Not performed now (it would rewrite personal-scope rows).
3. **E-3 — `workspaces.tenant_id` semantics.** The column is written with an
   **organization id** while the ORM declares a FK to `tenants.id`. Recommendation:
   retarget to `organizations.id` and rename to `organization_id`. Deliberately not
   changed in G1.21 — no FK was added, precisely because the current declaration
   would reject legitimate rows.
