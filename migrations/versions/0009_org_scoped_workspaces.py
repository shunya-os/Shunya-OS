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
    conn = op.get_bind()

    # 1. sh_workspaces.organization_id
    op.add_column("sh_workspaces", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.create_index("ix_sw_org", "sh_workspaces", ["organization_id"])
    conn.execute(sa.text("UPDATE sh_workspaces SET organization_id = 1"))

    # 2. founder_spaces.organization_id
    op.add_column("founder_spaces", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.create_index("ix_fs_org", "founder_spaces", ["organization_id"])
    conn.execute(sa.text("UPDATE founder_spaces SET organization_id = 1"))

    # 3. documents.tenant_id
    op.add_column("documents", sa.Column("tenant_id", sa.Integer(), nullable=True))
    conn.execute(sa.text("UPDATE documents SET tenant_id = 1"))

    logger.info("0009 applied: workspaces/spaces/documents org-scoped")


def downgrade():
    for table in ["documents", "founder_spaces", "sh_workspaces"]:
        try:
            op.drop_column(table, "organization_id" if table != "documents" else "tenant_id")
        except Exception as e:
            logger.warning("drop %s: %s", table, e)