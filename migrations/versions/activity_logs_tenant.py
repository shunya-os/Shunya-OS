"""activity_logs: tenant_id column parity for audit writers (ZG-03 B1).

Production's activity_logs carries ``tenant_id`` NOT NULL (enterprise
lineage); fresh installs materialised by 0010 lack the column entirely, so
audit writers could not attribute entries to a tenant consistently — on
production, every audit insert without tenant_id fails the NOT NULL
constraint (the ZG-03 B1 verification caught exactly this).

Additive + idempotent: adds the column and its index when missing; a no-op
on the production lineage where both already exist.

Revision ID: activity_logs_tenant
Revises: remediation_columns
"""

from alembic import op
import sqlalchemy as sa

revision = "activity_logs_tenant"
down_revision = "remediation_columns"
branch_labels = None
depends_on = None


def _columns(bind, table: str) -> set:
    insp = sa.inspect(bind)
    if not insp.has_table(table):
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def _indexes(bind, table: str) -> set:
    insp = sa.inspect(bind)
    if not insp.has_table(table):
        return set()
    return {i["name"] for i in insp.get_indexes(table)}


def upgrade():
    bind = op.get_bind()
    if not _columns(bind, "activity_logs"):
        return  # table itself absent (unexpected) — nothing to reconcile
    if "tenant_id" not in _columns(bind, "activity_logs"):
        op.add_column("activity_logs",
                      sa.Column("tenant_id", sa.Integer(), nullable=True))
    if "ix_activity_logs_tenant" not in _indexes(bind, "activity_logs"):
        op.create_index("ix_activity_logs_tenant", "activity_logs", ["tenant_id"])


def downgrade():
    bind = op.get_bind()
    if "ix_activity_logs_tenant" in _indexes(bind, "activity_logs"):
        op.drop_index("ix_activity_logs_tenant", table_name="activity_logs")
    if "tenant_id" in _columns(bind, "activity_logs"):
        op.drop_column("activity_logs", "tenant_id")
