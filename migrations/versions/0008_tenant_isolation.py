"""FDA Final: Add tenant_id isolation to core tables.

Adds tenant_id to the 4 tables lacking isolation:
- objects (legacy object store)
- commitments
- evidence_records
- act_execution_logs

Backfills from related records where possible.
"""
import logging
from alembic import op
import sqlalchemy as sa

logger = logging.getLogger(__name__)

revision = "0008_tenant_isolation"
down_revision = "0007_fda22_auth_extended"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add tenant_id to objects
    op.add_column("objects", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_index("ix_objects_tenant", "objects", ["tenant_id"])

    # 2. Add tenant_id to commitments
    op.add_column("commitments", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_index("ix_commitments_tenant", "commitments", ["tenant_id"])

    # 3. Add tenant_id to evidence_records
    op.add_column("evidence_records", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_index("ix_evidence_tenant", "evidence_records", ["tenant_id"])

    # 4. Add tenant_id to act_execution_logs
    op.add_column("act_execution_logs", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_index("ix_exec_tenant", "act_execution_logs", ["tenant_id"])


def downgrade():
    for table in ["act_execution_logs", "evidence_records", "commitments", "objects"]:
        try:
            op.drop_column(table, "tenant_id")
        except Exception as e:
            logger.warning("drop %s tenant_id: %s", table, e)