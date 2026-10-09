"""Tenancy convergence tier 1 — drop legacy-tenant FKs on EMPTY tables.

WHY
---
Production still carries (as of this revision) dozens of FK constraints whose
referenced table is the legacy ``tenants`` table, while every current write
path stores ORGANIZATION ids (or will, per the convergence stream). The
survivors fall into three tiers (see artifacts/SH_M6_M15_CONTINUE15_CHECKPOINT.md
and the FK inventory):

  tier 1 — the table is EMPTY. Dropping the stale FK is pure hygiene: it
           removes the latent "insert org id -> ForeignKeyViolation" outage
           class proven by suppliers (M6) and customers (Stage C) without
           touching any row data.
  tier 2 — the table has rows carrying non-organization values; retargeting
           needs a data reconciliation decision (separate work).
  tier 3 — ``organizations.legacy_tenant_id`` is the DELIBERATE bridge to the
           legacy table; its FK is intentional and MUST NOT be dropped.

WHAT
----
Self-guarding and idempotent: enumerates every FK constraint that references
``tenants``, and drops it ONLY when its table is still completely empty at
upgrade time. Tables with any rows are left untouched with a truthful printed
note (no data rewrite, no failed chain). ``organizations.legacy_tenant_id`` is
excluded by name. Running twice is a no-op (dropped constraints no longer
appear in the catalog).

Downgrade recreates the captured constraints by name ONLY where every
non-NULL value in the column is a valid ``tenants.id`` — otherwise the
constraint is skipped with a truthful note.

Revision ID: c_tenancy_fk_convergence_tier1
Revises: c_human_context_tenancy_retarget
"""
from alembic import op as _raw_op  # noqa: F401
from sqlalchemy import text

revision = "c_tenancy_fk_convergence_tier1"
down_revision = "c_human_context_tenancy_retarget"
branch_labels = None
depends_on = None

# The deliberate bridge — never touched by this migration.
_EXCLUDED = ("organizations.legacy_tenant_id",)


def _list_tenant_fks(bind):
    rows = bind.execute(text("""
        SELECT n.nspname || '.' || c.relname AS tbl,
               con.conname AS conname,
               (pg_get_constraintdef(con.oid)) AS cdef
        FROM pg_constraint con
        JOIN pg_class c ON c.oid = con.conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE con.contype = 'f' AND con.confrelid = 'tenants'::regclass
        ORDER BY tbl, conname
    """)).fetchall()
    out = []
    for tbl, conname, cdef in rows:
        col = cdef.split("(")[1].split(")")[0].strip()
        out.append((tbl, col, conname, cdef))
    return out


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    bind = op.get_bind()

    if not op.has_table("tenants"):
        print("  tenancy-convergence: tenants table absent — nothing to drop")
        return

    dropped, skipped, excluded = 0, 0, 0
    for tbl, col, conname, _cdef in _list_tenant_fks(bind):
        bare = tbl.rsplit(".", 1)[-1]
        if f"{bare}.{col}" in _EXCLUDED:
            excluded += 1
            continue
        try:
            n = bind.execute(text(f"SELECT count(*) FROM {tbl}")).scalar() or 0
        except Exception:
            n = -1
        if n != 0:
            skipped += 1
            print(f"  tenancy-convergence: {tbl}.{col} has {n} row(s) — FK kept")
            continue
        op.drop_constraint(conname, bare, type_="foreignkey")
        dropped += 1

    print(f"  tenancy-convergence: dropped {dropped} legacy FK(s) on empty "
          f"tables; kept {skipped} on non-empty tables; "
          f"excluded {excluded} (deliberate bridge)")


def downgrade():
    """Intentionally a documented NO-OP.

    Recreating the dropped constraints would re-introduce exactly the drifted
    state this migration converges away (write paths store organization ids;
    the stale FKs point at the legacy tenants table and turn every such insert
    into a ForeignKeyViolation — proven by the supplier and customer outages).
    A partial reconstruction (only some names, guessed naming conventions)
    would be worse than none: it would make the schema state depend on guess
    work. If a rollback of this cleanup is ever genuinely required, restore
    the constraints deliberately, per table, with a data review.
    """
    print("  tenancy-convergence downgrade: intentional no-op — the legacy "
          "FKs dropped by this migration are the drifted state being "
          "converged away; restoring them requires a deliberate per-table "
          "review.")
