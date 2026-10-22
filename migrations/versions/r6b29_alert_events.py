"""r6b29 — alert events table (E1 operational alerting).

Creates sh_alert_events, the durable audit trail + cross-worker dedup store
for the alert engine (app/alerting).
"""
from alembic import op
import sqlalchemy as sa

revision = "r6b29_alert_events"
down_revision = "b3_missing_schema_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Guarded: r6b30 also creates this table, and a boot-created schema already
    # has it from ``db.create_all()``. Unguarded, ``alembic upgrade head`` on a
    # boot-created database failed with
    # ``DuplicateTable: relation "sh_alert_events" already exists`` (measured on
    # the G1.21 disposable cluster). Guarding changes nothing on a database that
    # reaches this revision in the normal order.
    from migrations.guarded import guarded_op

    op = guarded_op()
    op.create_table(
        "sh_alert_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule", sa.String(length=50), nullable=False),
        sa.Column("alert_key", sa.String(length=200), nullable=False),
        sa.Column("severity", sa.String(length=10), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("first_seen", sa.DateTime(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.Column("recovered_at", sa.DateTime(), nullable=True),
        sa.Column("occurrences", sa.Integer(), nullable=False),
        sa.Column("delivery_state", sa.String(length=20), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
    )
    op.create_index("ix_sh_alert_events_rule", "sh_alert_events", ["rule"])
    op.create_index("ix_sh_alert_events_alert_key", "sh_alert_events", ["alert_key"])
    op.create_index("ix_sh_alert_events_status", "sh_alert_events", ["status"])


def downgrade() -> None:
    op.drop_index("ix_sh_alert_events_status", table_name="sh_alert_events")
    op.drop_index("ix_sh_alert_events_alert_key", table_name="sh_alert_events")
    op.drop_index("ix_sh_alert_events_rule", table_name="sh_alert_events")
    op.drop_table("sh_alert_events")