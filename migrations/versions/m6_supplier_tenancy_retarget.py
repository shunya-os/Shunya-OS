"""M6 — suppliers.tenant_id: legacy tenants FK → canonical organizations FK.

WHY
---
The production ``suppliers`` table carries ``fk_suppliers_tenant_id_tenants``
(tenant_id → tenants(id)) from the pre-organizations schema. Every current
write path stores the ORGANIZATION id in ``suppliers.tenant_id`` (supplier
routes, import pipeline, AI tool handler), and the SQLAlchemy model declares
no FK at all. Consequence, reproduced over HTTPS against production on
2026-10-09 with the certification tenant (org 278):

    POST /api/v1/data/import/commit (target=supplier) -> 400
    psycopg2.errors.ForeignKeyViolation: Key (tenant_id)=(278) is not present
    in table "tenants".

The ``tenants`` table is legacy: nothing in the application creates tenant
rows anymore, and organizations carry only a read-only ``legacy_tenant_id``
bridge that no code populates. Any organization without a legacy tenants row
can therefore never create a supplier while every SQLite test passes
(``db.create_all()`` materialises the model; SQLite does not enforce the
legacy FK). Production ``suppliers`` is empty, so no row data is touched.

WHAT
----
Idempotent, guarded, data-preserving:
  1. drop the stale ``fk_suppliers_tenant_id_tenants`` (no-op if absent);
  2. create ``fk_suppliers_tenant_id_organizations`` (tenant_id →
     organizations.id) ONLY when every existing ``suppliers.tenant_id`` is
     NULL or a real organization id — otherwise the constraint is skipped and
     a truthful warning is printed (no silent data rewrite, no failed chain).

Revision ID: m6_supplier_tenancy_retarget
Revises: r6b27_content_schema_drift
"""
from alembic import op as _raw_op  # noqa: F401
from sqlalchemy import text

revision = "m6_supplier_tenancy_retarget"
down_revision = "r6b27_content_schema_drift"
branch_labels = None
depends_on = None


def _violations(bind, sql: str) -> int:
    return bind.execute(text(sql)).scalar() or 0


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    if not op.has_table("suppliers"):
        print("  suppliers: table absent — nothing to retarget")
        return

    op.drop_constraint("fk_suppliers_tenant_id_tenants", "suppliers",
                       type_="foreignkey")

    violations = _violations(op.get_bind(), (
        "SELECT count(*) FROM suppliers s "
        "WHERE s.tenant_id IS NOT NULL "
        "AND NOT EXISTS (SELECT 1 FROM organizations o WHERE o.id = s.tenant_id)"
    ))
    if violations:
        print(f"  suppliers: {violations} row(s) reference tenant ids that are "
              f"not organization ids — fk_suppliers_tenant_id_organizations NOT "
              f"created; reconcile those rows and re-run `alembic upgrade head`")
        return

    op.create_foreign_key(
        "fk_suppliers_tenant_id_organizations", "suppliers", "organizations",
        ["tenant_id"], ["id"],
    )
    print("  suppliers: tenant_id FK retargeted to organizations(id)")


def downgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    if not op.has_table("suppliers"):
        return

    op.drop_constraint("fk_suppliers_tenant_id_organizations", "suppliers",
                       type_="foreignkey")

    violations = _violations(op.get_bind(), (
        "SELECT count(*) FROM suppliers s "
        "WHERE s.tenant_id IS NOT NULL "
        "AND NOT EXISTS (SELECT 1 FROM tenants t WHERE t.id = s.tenant_id)"
    ))
    if violations:
        print(f"  suppliers: {violations} row(s) would violate the legacy tenants "
              f"FK — it was NOT recreated")
        return

    op.create_foreign_key(
        "fk_suppliers_tenant_id_tenants", "suppliers", "tenants",
        ["tenant_id"], ["id"],
    )
    print("  suppliers: tenant_id FK restored to tenants(id)")
