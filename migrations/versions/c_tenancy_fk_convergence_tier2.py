"""Tenancy convergence tier 2 — drop legacy-tenant FKs on the remaining tables.

WHY
---
Tier 1 (c_tenancy_fk_convergence_tier1) removed the stale FKs on empty
tables. The survivors with rows fall into two groups, both verified against
the live inventory (2026-10-09):

- Datasets whose non-organization values are LEGACY but historically valid
  and deliberately preserved (no rewrite): campaigns(5), outcomes(3),
  workspaces(1), and the memory engine tables (memory_records 778,
  memory_provenances 669, observations 130) whose values are a MIX of
  current organization ids (7, 187, 276, 277, ...) and the founder's legacy
  tenant 89 (= organization 7 via the recorded bridge). New writes already
  use organization ids; the FK only turns them into errors. Drop it.
- tenant_themes: mixed legacy demo values (91, 97, 113, ...) with no
  corresponding organization — preserved as historical markers, FK dropped.

NOT TOUCHED (deliberately):
- organizations.legacy_tenant_id — the intentional bridge (org 7 <-> 89).
- tenants.parent_id — self-referential, intentional.

This migration does NOT rewrite any row. The optional 89 -> 7 historical
rewrite for the memory engine is a separate, founder-reviewed decision
(recorded in the CONTINUE-16 checkpoint).

Revision ID: c_tenancy_fk_convergence_tier2
Revises: c_tenancy_fk_convergence_tier1
"""
from alembic import op as _raw_op  # noqa: F401
from sqlalchemy import text

revision = "c_tenancy_fk_convergence_tier2"
down_revision = "c_tenancy_fk_convergence_tier1"
branch_labels = None
depends_on = None

# (bare table, column, constraint name) — from the live inventory.
_TARGETS = (
    ("campaigns", "tenant_id", "campaigns_tenant_id_fkey"),
    ("memory_provenances", "tenant_id", "memory_provenances_tenant_id_fkey"),
    ("memory_records", "tenant_id", "memory_records_tenant_id_fkey"),
    ("observations", "tenant_id", "fk_observations_tenant_id_tenants"),
    ("outcomes", "tenant_id", "fk_outcomes_tenant_id_tenants"),
    ("tenant_themes", "tenant_id", "tenant_themes_tenant_id_fkey"),
    ("workspaces", "tenant_id", "workspaces_tenant_id_fkey"),
)


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    bind = op.get_bind()

    if not op.has_table("tenants"):
        print("  tenancy-convergence tier2: tenants table absent — nothing to drop")
        return

    dropped, gone, missing_tbl = 0, 0, 0
    for bare, col, conname in _TARGETS:
        if not op.has_table(bare):
            missing_tbl += 1
            print(f"  tenancy-convergence tier2: {bare} absent — skipped")
            continue
        exists = bind.execute(text("""
            SELECT count(*) FROM pg_constraint con
            JOIN pg_class c ON c.oid = con.conrelid
            WHERE con.conname = :n AND c.relname = :t AND con.contype = 'f'
              AND con.confrelid = 'tenants'::regclass
        """), {"n": conname, "t": bare}).scalar()
        if not exists:
            gone += 1
            print(f"  tenancy-convergence tier2: {bare}.{col} FK already absent — no-op")
            continue
        n_rows = bind.execute(text(f"SELECT count(*) FROM {bare}")).scalar() or 0
        op.drop_constraint(conname, bare, type_="foreignkey")
        dropped += 1
        print(f"  tenancy-convergence tier2: dropped {conname} on {bare} "
              f"({n_rows} row(s) preserved, no data change)")
    print(f"  tenancy-convergence tier2: dropped {dropped}, already-absent {gone}, "
          f"missing-table {missing_tbl}")


def downgrade():
    """Documented NO-OP — same reasoning as tier 1.

    Recreating these FKs re-introduces the outage class (write paths store
    organization ids; the constraints point at the legacy tenants table).
    Restoring any of them requires a deliberate per-table data review.
    """
    print("  tenancy-convergence tier2 downgrade: intentional no-op — see the "
          "module docstring for the reasoning (dropped FKs are the drifted "
          "state being converged away).")
