"""Canonical tenant model: scope workspaces/spaces/documents to organizations.

- sh_workspaces.organization_id
- founder_spaces.organization_id
- documents.tenant_id

Backfills: existing workspaces/spaces/documents assigned to org 1 (Panchi Club),
the only production business with real data.
"""
import logging
from alembic import op
import sqlalchemy as sa

logger = logging.getLogger(__name__)

revision = "0009_org_scoped_workspaces"
down_revision = "0008_tenant_isolation"
branch_labels = None
depends_on = None


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    conn = op.get_bind()

    # 1. sh_workspaces.organization_id
    op.add_column("sh_workspaces", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.create_index("ix_sw_org", "sh_workspaces", ["organization_id"])
    # Data backfills must skip tables that this chain does not create: on a
    # genuinely fresh database those tables are materialised later by the
    # canonical boot path (guarded convergence), so an unconditional UPDATE
    # fails with UndefinedTable on PostgreSQL.
    if op.has_table("sh_workspaces"):
        conn.execute(sa.text("UPDATE sh_workspaces SET organization_id = 1"))

    # 2. founder_spaces.organization_id
    op.add_column("founder_spaces", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.create_index("ix_fs_org", "founder_spaces", ["organization_id"])
    if op.has_table("founder_spaces"):
        conn.execute(sa.text("UPDATE founder_spaces SET organization_id = 1"))

    # 3. documents.tenant_id
    op.add_column("documents", sa.Column("tenant_id", sa.Integer(), nullable=True))
    if op.has_table("documents"):
        conn.execute(sa.text("UPDATE documents SET tenant_id = 1"))

    logger.info("0009 applied: workspaces/spaces/documents org-scoped")


def downgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    for table in ["documents", "founder_spaces", "sh_workspaces"]:
        try:
            op.drop_column(table, "organization_id" if table != "documents" else "tenant_id")
        except Exception as e:
            logger.warning("drop %s: %s", table, e)