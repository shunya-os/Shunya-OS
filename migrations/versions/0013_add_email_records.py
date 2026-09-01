"""0013: Create email_records table for durable email lifecycle tracking

Creates the email_records table that stores the full lifecycle state
of every transactional email send: requested → accepted → delivered →
bounced → complained → failed → exhausted.

This is a safe, additive migration. The table is new and has no
dependencies on existing data. Rollback is a DROP TABLE.
"""

import sqlalchemy as sa
from alembic import op

revision = "0013_add_email_records"
down_revision = "0012_add_organization_plan"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()
    if "email_records" not in table_names:
        op.create_table(
            "email_records",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("business_event_id", sa.String(128), nullable=False, index=True),
            sa.Column("notification_type", sa.String(64), nullable=False),
            sa.Column("recipient", sa.String(255), nullable=False, index=True),
            sa.Column("subject", sa.String(255), nullable=False),
            sa.Column("body_hash", sa.String(64), nullable=False),
            sa.Column("category", sa.String(32), nullable=False, server_default="operational"),
            sa.Column("provider", sa.String(32), nullable=False, server_default="resend"),
            sa.Column("provider_message_id", sa.String(128), nullable=True, index=True),
            sa.Column("state", sa.String(32), nullable=False, server_default="requested"),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("max_retries", sa.Integer(), nullable=False, server_default=sa.text("2")),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("tenant_id", sa.Integer(), nullable=True, index=True),
            sa.Column("identity_id", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("webhook_verified_at", sa.DateTime(), nullable=True),
            sa.Column("webhook_event_id", sa.String(128), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        print("  SKIP: email_records table already exists")


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()
    if "email_records" in table_names:
        op.drop_table("email_records")