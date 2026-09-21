"""R6B-2.8 — Supplier schema drift: 4 model columns never migrated.

WHY
---
`Supplier` (app/models.py) declares 17 columns, but the production PostgreSQL
`suppliers` table has only 13. Verified read-only against the live database
(`information_schema.columns`) on 2026-09-21:

    MISSING IN LIVE: created_by, status, updated_at, workspace_id

Consequence, reproduced over HTTPS against production with the sanctioned
certification session and confirmed in the serving worker's log:

    GET /api/v1/suppliers/  ->  HTTP 500
    psycopg2.errors.UndefinedColumn: column suppliers.status does not exist
      app/suppliers/routes.py:56 list_suppliers -> _paginate -> query.count()

So the WHOLE Supplier capability is broken in production, while every test
passes: the test suite builds schema from the model via `db.create_all()`
(SQLite), whereas production runs the Alembic chain — and no revision in the
chain ever added these columns. A full drift scan of all 45 model tables
against the live database found this to be the ONLY drifted table.

This is the same defect class as `r6b27_content_lifecycle`, hence the same
guarded, additive treatment.

Idempotent: every step is a no-op where the column/index already exists, and a
missing table is skipped (the canonical boot path materialises it from the
model), so the chain converges from any starting point.

Revision ID: r6b27_supplier_drift
Revises: r6b27_content_lifecycle
"""
import sqlalchemy as sa
from alembic import op

revision = "r6b27_supplier_drift"
down_revision = "r6b27_content_lifecycle"
branch_labels = None
depends_on = None


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    # status: nullable to match the model, with a server default so existing
    # rows are populated ('active') and inserts may omit it.
    op.add_column(
        "suppliers",
        sa.Column("status", sa.String(30), nullable=True,
                  server_default="active"),
    )
    op.add_column(
        "suppliers",
        sa.Column("workspace_id", sa.String(64), nullable=True),
    )
    op.add_column(
        "suppliers",
        sa.Column("created_by", sa.String(120), nullable=True),
    )
    op.add_column(
        "suppliers",
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    # The model declares Index("ix_suppliers_tenant", "tenant_id", "status");
    # it could not have been created while `status` was absent.
    op.create_index(
        "ix_suppliers_tenant",
        "suppliers",
        ["tenant_id", "status"],
    )
    print("  suppliers: status, workspace_id, created_by, updated_at ensured")


def downgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    op.drop_index("ix_suppliers_tenant", table_name="suppliers")
    op.drop_column("suppliers", "updated_at")
    op.drop_column("suppliers", "created_by")
    op.drop_column("suppliers", "workspace_id")
    op.drop_column("suppliers", "status")