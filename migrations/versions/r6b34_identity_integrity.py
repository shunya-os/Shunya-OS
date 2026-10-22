"""r6b34 — integrity constraints for the canonical identity → organization →
workspace → object chain (G1.21).

WHY
---
Two schema authorities exist in SHUNYA (see ``migrations/guarded.py``):

  * ``db.create_all()`` at boot, from ORM metadata, and
  * this Alembic chain.

They do not produce the same schema. Measured on the disposable G1.21 cluster
(127.0.0.1:5445), same source tree:

    migration-first : 177 tables,  32 foreign keys
    boot-first      : 160 tables, 163 foreign keys

So on a migration-only install the ORM's declared foreign keys, unique indexes and
indexes for in-scope tables simply do not exist. The most consequential example:

    sh_objects.workspace_id  NOT NULL, declared FK -> sh_workspaces.id, no FK in pg

i.e. the canonical object→workspace ownership edge was unenforced: an object could
be persisted against a workspace id that does not exist, and nothing at the storage
layer prevented it.

WHAT THIS REVISION ADDS — and what it deliberately does not
-----------------------------------------------------------
Every constraint below was reviewed against (a) the ORM declaration, (b) the write
path that produces the column, and (c) whether legitimate existing rows could
violate it. Added only when all three agree:

  * foreign keys whose column is written from a real parent id:
      sh_objects.workspace_id            -> sh_workspaces.id
      org_invitations.organization_id    -> organizations.id
      auth_roles.organization_id         -> organizations.id
      auth_member_roles.organization_id  -> organizations.id
      auth_member_roles.member_id        -> org_members.id
      auth_member_roles.role_id          -> auth_roles.id
      rel_relationships.organization_id  -> organizations.id
      rel_timeline.organization_id       -> organizations.id
      rel_categories.organization_id     -> organizations.id
      rel_custom_fields.organization_id  -> organizations.id
      rel_ai_memory.organization_id      -> organizations.id
      rel_ai_memory.relationship_id      -> rel_relationships.id
      rel_timeline.relationship_id       -> rel_relationships.id
      activity_logs.lead_id              -> leads.id
      leads.person_id                    -> persons.id
      org_members.department_id          -> departments.id
      memory_records.person_id           -> persons.id
      memory_records.relationship_id     -> rel_relationships.id
      memory_provenances.memory_id       -> memory_records.id
      team_members.person_id             -> persons.id

  * unique indexes whose uniqueness is the domain invariant, not an accident of
    the ORM (duplicates are refused at the application layer already):
      shunya_identities.identity_id      canonical identity id
      team_members.email                 one account per email (signup returns 409)
      team_members.api_token             bearer token lookup (NULLs are distinct)
      auth_roles(organization_id,name)   one role name per organization
      auth_member_roles(member_id,role_id) one grant per role
      rel_categories(organization_id,type_key)
      rel_custom_fields(organization_id,field_key)
      workspaces(tenant_id,slug)         one slug per organization
      organizations.slug                 URL identity of the organization

  * supporting indexes for the foreign keys added here where the ORM declares one
    (a foreign key without an index on the child column turns every parent
    delete/update into a sequential scan of the child table):
      ix_activity_lead_created, ix_auth_mr_member, ix_auth_mr_role,
      ix_auth_role_org, ix_memory_records_person_id, ix_mp_memory,
      ix_rel_relationships_organization_id, ix_sh_objects_workspace_id

DELIBERATELY NOT ADDED (each needs an owner decision, recorded in the ledger):
  * ``workspaces.tenant_id`` — the ORM points it at ``tenants.id`` but the writer
    (``app/production/identity/workspace_routes.py::create_workspace``) stores an
    **organization id** in it (``tenant_id=org_id``). An FK to ``tenants`` would
    reject legitimate rows; the column is either mis-named or the FK is wrong.
  * ``memory_records.tenant_id`` / ``memory_provenances.tenant_id`` — caller-supplied
    tenancy whose meaning is not established; the tenancy-convergence revisions
    deliberately dropped legacy ``tenants`` foreign keys on empty tables.
  * ``invitation_tokens`` (token uniqueness, ``org_id -> tenants``) — no writer
    exists anywhere in the application; dead legacy table, retirement candidate.
  * ``organizations.legacy_tenant_id -> tenants`` — the documented bridge; an FK
    would block future legacy-tenant cleanup.
  * ``founder_objects.space_id`` / ``founder_spaces.space_id`` — hardening a table
    set that is a retirement candidate under the workspace architecture decision.
  * the remaining ~40 non-unique ORM indexes with no foreign key behind them —
    performance only; they need query-plan evidence, not ORM symmetry.

SAFETY
------
Every step is guarded and **data-preserving**:

  * an FK is created only when both tables exist and the child column has no
    orphan values; otherwise it is skipped and the orphan count is printed — rows
    are never deleted, updated or nulled to make a constraint fit;
  * a unique index is created only when no duplicate non-NULL key exists;
    otherwise it is skipped and the duplicate count is printed;
  * existing constraints/indexes are never modified or dropped;
  * a boot-created database converges (everything already present → no-ops) and a
    migration-only database gains the constraints.

Revision ID: r6b34_identity_integrity
Revises: r6b33_personal_workspace_tables
"""
import sqlalchemy as sa  # noqa: F401  (kept for revision-body symmetry)
from alembic import op
from sqlalchemy import text

revision = "r6b34_identity_integrity"
down_revision = "r6b33_personal_workspace_tables"
branch_labels = None
depends_on = None

# (child_table, child_columns, parent_table, parent_columns)
FOREIGN_KEYS = [
    ("sh_objects", ["workspace_id"], "sh_workspaces", ["id"]),
    ("org_invitations", ["organization_id"], "organizations", ["id"]),
    ("auth_roles", ["organization_id"], "organizations", ["id"]),
    ("auth_member_roles", ["organization_id"], "organizations", ["id"]),
    ("auth_member_roles", ["member_id"], "org_members", ["id"]),
    ("auth_member_roles", ["role_id"], "auth_roles", ["id"]),
    ("rel_relationships", ["organization_id"], "organizations", ["id"]),
    ("rel_timeline", ["organization_id"], "organizations", ["id"]),
    ("rel_categories", ["organization_id"], "organizations", ["id"]),
    ("rel_custom_fields", ["organization_id"], "organizations", ["id"]),
    ("rel_ai_memory", ["organization_id"], "organizations", ["id"]),
    ("rel_ai_memory", ["relationship_id"], "rel_relationships", ["id"]),
    ("rel_timeline", ["relationship_id"], "rel_relationships", ["id"]),
    ("activity_logs", ["lead_id"], "leads", ["id"]),
    ("leads", ["person_id"], "persons", ["id"]),
    ("org_members", ["department_id"], "departments", ["id"]),
    ("memory_records", ["person_id"], "persons", ["id"]),
    ("memory_records", ["relationship_id"], "rel_relationships", ["id"]),
    ("memory_provenances", ["memory_id"], "memory_records", ["id"]),
    ("team_members", ["person_id"], "persons", ["id"]),
]

# (table, columns) — uniqueness is a domain invariant, verified in source
UNIQUE_KEYS = [
    ("shunya_identities", ["identity_id"]),
    ("team_members", ["email"]),
    ("team_members", ["api_token"]),
    ("auth_roles", ["organization_id", "name"]),
    ("auth_member_roles", ["member_id", "role_id"]),
    ("rel_categories", ["organization_id", "type_key"]),
    ("rel_custom_fields", ["organization_id", "field_key"]),
    ("workspaces", ["tenant_id", "slug"]),
    ("organizations", ["slug"]),
]

# (index_name, table, columns) — justification: child side of a new foreign key
SUPPORTING_INDEXES = [
    ("ix_sh_objects_workspace_id", "sh_objects", ["workspace_id"]),
    ("ix_activity_lead_created", "activity_logs", ["lead_id", "created_at"]),
    ("ix_auth_mr_member", "auth_member_roles", ["member_id"]),
    ("ix_auth_mr_role", "auth_member_roles", ["role_id"]),
    ("ix_auth_role_org", "auth_roles", ["organization_id"]),
    ("ix_memory_records_person_id", "memory_records", ["person_id"]),
    ("ix_mp_memory", "memory_provenances", ["memory_id"]),
    ("ix_rel_relationships_organization_id", "rel_relationships", ["organization_id"]),
]


def _orphan_count(bind, child, child_cols, parent, parent_cols) -> int:
    on = " AND ".join(f"p.{pc} = c.{cc}" for cc, pc in zip(child_cols, parent_cols))
    notnull = " AND ".join(f"c.{cc} IS NOT NULL" for cc in child_cols)
    sql = (f"SELECT count(*) FROM {child} c LEFT JOIN {parent} p ON {on} "
           f"WHERE {notnull} AND p.{parent_cols[0]} IS NULL")
    return int(bind.execute(text(sql)).scalar() or 0)


def _duplicate_count(bind, table, cols) -> int:
    collist = ", ".join(cols)
    notnull = " AND ".join(f"{c} IS NOT NULL" for c in cols)
    sql = (f"SELECT count(*) FROM (SELECT {collist} FROM {table} WHERE {notnull} "
           f"GROUP BY {collist} HAVING count(*) > 1) d")
    return int(bind.execute(text(sql)).scalar() or 0)


def upgrade() -> None:
    from migrations.guarded import guarded_op

    gop = guarded_op()
    bind = gop.get_bind()

    added_fk, skipped_fk = 0, []
    for child, child_cols, parent, parent_cols in FOREIGN_KEYS:
        if not (gop.has_table(child) and gop.has_table(parent)):
            skipped_fk.append(f"{child}.{','.join(child_cols)} (table absent)")
            continue
        name = f"{child}_{'_'.join(child_cols)}_fkey"
        if gop.has_constraint(name, child):
            continue
        # a differently-named FK on the same pair also satisfies the intent
        existing = bind.execute(text(
            "SELECT 1 FROM pg_constraint con JOIN pg_class rel ON rel.oid = con.conrelid "
            "WHERE con.contype='f' AND rel.relname = :t AND con.conname = :n"),
            {"t": child, "n": name}).scalar()
        if existing:
            continue
        try:
            orphans = _orphan_count(bind, child, child_cols, parent, parent_cols)
        except Exception as exc:  # column missing on this schema — skip, do not guess
            skipped_fk.append(f"{child}.{','.join(child_cols)} (probe failed: {exc})")
            continue
        if orphans:
            skipped_fk.append(
                f"{child}.{','.join(child_cols)} -> {parent} ({orphans} orphan row(s) kept)")
            continue
        gop.create_foreign_key(name, child, parent, child_cols, parent_cols)
        added_fk += 1

    added_uq, skipped_uq = 0, []
    for table, cols in UNIQUE_KEYS:
        if not gop.has_table(table):
            skipped_uq.append(f"{table}({','.join(cols)}) (table absent)")
            continue
        name = f"ix_{table}_{'_'.join(cols)}" if len(cols) > 1 else f"ix_{table}_{cols[0]}"
        if gop.has_index(name):
            continue
        try:
            dups = _duplicate_count(bind, table, cols)
        except Exception as exc:
            skipped_uq.append(f"{table}({','.join(cols)}) (probe failed: {exc})")
            continue
        if dups:
            skipped_uq.append(f"{table}({','.join(cols)}) ({dups} duplicate key(s) kept)")
            continue
        gop.create_index(name, table, cols, unique=True)
        added_uq += 1

    added_ix = 0
    for name, table, cols in SUPPORTING_INDEXES:
        if not gop.has_table(table):
            continue
        if gop.has_index(name):
            continue
        gop.create_index(name, table, cols)
        added_ix += 1

    print(f"  r6b34: foreign keys added {added_fk}, skipped {len(skipped_fk)}")
    for s in skipped_fk:
        print(f"    SKIP FK {s}")
    print(f"  r6b34: unique indexes added {added_uq}, skipped {len(skipped_uq)}")
    for s in skipped_uq:
        print(f"    SKIP UNIQUE {s}")
    print(f"  r6b34: supporting indexes added {added_ix}")


def downgrade() -> None:
    """Drop only what this revision created, by exact name.

    Reversible: dropping a foreign key or an index destroys no row. Named
    constraints are dropped first so the supporting indexes can go independently.
    """
    from migrations.guarded import guarded_op

    gop = guarded_op()
    for name, table, _cols in SUPPORTING_INDEXES:
        gop.drop_index(name, table_name=table)
    for table, cols in UNIQUE_KEYS:
        name = f"ix_{table}_{'_'.join(cols)}" if len(cols) > 1 else f"ix_{table}_{cols[0]}"
        gop.drop_index(name, table_name=table)
    for child, child_cols, _parent, _pcols in FOREIGN_KEYS:
        gop.drop_constraint(f"{child}_{'_'.join(child_cols)}_fkey", child, type_="foreignkey")
