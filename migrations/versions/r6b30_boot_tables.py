"""G1.15 — Bring boot-materialised tables under Alembic authority.

`sh_uop_objects` (Universal Object Protocol persistence) and `sh_alert_events`
(alert lifecycle) were materialised only by SQLAlchemy `db.create_all()` at
application boot, so a migration-only database lacked them. This forward-only,
guarded revision makes the migration chain authoritative:

  - every step is skipped when the table/index already exists
  - no column is altered or dropped; boot-created databases converge
  - a fresh database gets both tables from the chain alone

Revision ID: r6b30_boot_tables
Revises: r6b2_conversation_fk
"""
import sqlalchemy as sa
from alembic import op

revision = "r6b30_boot_tables"
down_revision = "r6b2_conversation_fk"
branch_labels = None
depends_on = None


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    op.create_table(
        "sh_uop_objects",
        sa.Column("object_id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("space_id", sa.String(64), nullable=False, server_default=""),
        sa.Column("object_type", sa.String(128), nullable=False, server_default=""),
        sa.Column("name", sa.String(512), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.String(64), nullable=False, server_default=""),
        sa.Column("updated_at", sa.String(64), nullable=False, server_default=""),
        sa.Column("created_by", sa.String(128), nullable=False, server_default=""),
        sa.Column("updated_by", sa.String(128), nullable=False, server_default=""),
        sa.Column("evidence_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("relationships_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_sh_uop_objects_tenant", "sh_uop_objects", ["tenant_id"])
    op.create_index("ix_sh_uop_objects_type", "sh_uop_objects", ["object_type"])

    op.create_table(
        "sh_alert_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule", sa.String(50), nullable=False),
        sa.Column("alert_key", sa.String(200), nullable=False),
        sa.Column("severity", sa.String(10), server_default="P2"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), server_default=""),
        sa.Column("first_seen", sa.DateTime(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.Column("recovered_at", sa.DateTime(), nullable=True),
        sa.Column("occurrences", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delivery_state", sa.String(20), server_default="pending"),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
    )
    op.create_index("ix_sh_alert_events_rule", "sh_alert_events", ["rule"])
    op.create_index("ix_sh_alert_events_alert_key", "sh_alert_events", ["alert_key"])
    op.create_index("ix_sh_alert_events_status", "sh_alert_events", ["status"])


def downgrade():
    # Intentionally additive-only: dropping these tables could destroy live
    # object and alert history. A destructive downgrade requires an explicit,
    # separately authorized migration.
    pass