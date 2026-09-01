"""0012: Add plan column to organizations table

The Organization model was extended with a plan field but no migration
was created. Running gunicorn workers auto-restart from --max-requests
and pick up the new model attribute, causing 500 on any Organization
query (SELECT ... organizations.plan does not exist).

Migration: ALTER TABLE organizations ADD COLUMN plan
"""

import sqlalchemy as sa
from alembic import op

revision = "0012_add_organization_plan"
down_revision = "f5429b50dbc6"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("organizations")]
    if "plan" not in columns:
        op.add_column(
            "organizations",
            sa.Column("plan", sa.String(30), server_default="free", nullable=True),
        )
    else:
        print("  SKIP: organizations.plan already exists")


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("organizations")]
    if "plan" in columns:
        op.drop_column("organizations", "plan")