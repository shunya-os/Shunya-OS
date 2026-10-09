"""G-stage — emotional/human context tenant_id: legacy tenants FK → organizations.

WHY
---
Both ``emotional_context_items`` and ``human_context_items`` carry
``tenant_id -> tenants(id)`` from the pre-organizations schema, while the only
route that writes them (app/human_context/routes.py) resolves the tenant from
the caller's canonical organization (``g.current_org_id``, e.g. 7 or 278).
Nothing creates ``tenants`` rows anymore, so recording human context for any
canonical organization fails with a ForeignKeyViolation — the same drift class
fixed for ``suppliers`` in m6_supplier_tenancy_retarget. Both tables are
verified EMPTY in production (2026-10-09 probe: 0 rows), so no data is touched.

WHAT
----
Idempotent, guarded, data-preserving per table:
  1. drop the stale ``*_tenant_id_fkey`` (no-op if absent);
  2. create ``*_tenant_id_fkey`` -> organizations(id) ONLY when every existing
     tenant_id is NULL or a real organization id — otherwise skip with a
     truthful warning (no silent rewrite).

Revision ID: c_human_context_tenancy_retarget
Revises: c_org_legacy_bridge
"""
from alembic import op as _raw_op  # noqa: F401
from sqlalchemy import text

revision = "c_human_context_tenancy_retarget"
down_revision = "c_org_legacy_bridge"
branch_labels = None
depends_on = None

TABLES = ("emotional_context_items", "human_context_items")


def _violations(bind, table: str) -> int:
    return bind.execute(text(
        f"SELECT count(*) FROM {table} t "
        f"WHERE t.tenant_id IS NOT NULL "
        f"AND NOT EXISTS (SELECT 1 FROM organizations o WHERE o.id = t.tenant_id)"
    )).scalar() or 0


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    bind = op.get_bind()

    for table in TABLES:
        if not op.has_table(table):
            print(f"  {table}: table absent — nothing to retarget")
            continue

        op.drop_constraint(f"{table}_tenant_id_fkey", table, type_="foreignkey")

        if _violations(bind, table):
            print(f"  {table}: rows reference tenant ids that are not "
                  f"organization ids — FK NOT created; reconcile and re-run")
            continue

        op.create_foreign_key(
            f"{table}_tenant_id_fkey", table, "organizations",
            ["tenant_id"], ["id"],
        )
        print(f"  {table}: tenant_id FK retargeted to organizations(id)")


def downgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    for table in TABLES:
        if not op.has_table(table):
            continue
        op.drop_constraint(f"{table}_tenant_id_fkey", table, type_="foreignkey")
        print(f"  {table}: canonical FK dropped (legacy FK NOT recreated — "
              f"tenants rows no longer exist for new organizations)")