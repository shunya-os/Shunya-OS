"""ZG-03 B3 — create model-declared tables missing from live databases

Reproduced against production (2026-10-13): these tables are declared by
live models but absent from the deployed schema (model <-> migration drift —
the L1 analytics-dashboard 500 is caused by ``ai_execution_records``):

- ai_execution_records  (app/observability/models.py, live observability + analytics)
- user_profiles         (app/profile/models.py, live profile routes)
- feedback_signals      (app/feedback/models.py, live feedback route)

NOT created: the plain-class compatibility stubs in app/evidence/models.py
(SourceReference / EvidenceLink / AssertionRecord / SourceAssessment) are not
``db.Model`` subclasses — ``db.create_all()`` never created them, no query
touches them, and a table without model columns would be a false artifact.

Safe additive migration, guarded by ``has_table`` (same pattern as
``activity_logs_tenant``), so re-running against any database state is a
no-op. Downgrade drops only the tables this migration created.
"""
from alembic import op
import sqlalchemy as sa

revision = "b3_missing_schema_tables"
down_revision = "activity_logs_tenant"

branch_labels = None
depends_on = None


def _table_exists(bind, table: str) -> bool:
    insp = sa.inspect(bind)
    return insp.has_table(table)


def upgrade() -> None:
    bind = op.get_bind()

    # ── ai_execution_records (app/observability/models.py) ────────────────
    if not _table_exists(bind, "ai_execution_records"):
        op.create_table(
            "ai_execution_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("request_id", sa.String(64), nullable=False),
            sa.Column("session_id", sa.String(128), nullable=True),
            sa.Column("query", sa.Text(), nullable=False),
            sa.Column("action_class", sa.String(64), nullable=True),
            sa.Column("provider", sa.String(64), nullable=True),
            sa.Column("model", sa.String(128), nullable=True),
            sa.Column("latency_ms", sa.Float(), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("evidence_count", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_ai_execution_records_request_id", "ai_execution_records", ["request_id"])
        op.create_index("ix_ai_execution_records_session_id", "ai_execution_records", ["session_id"])

    # ── user_profiles (app/profile/models.py) ─────────────────────────────
    if not _table_exists(bind, "user_profiles"):
        op.create_table(
            "user_profiles",
            sa.Column("identity_id", sa.String(128), primary_key=True),
            sa.Column("display_name", sa.String(256), nullable=False, server_default=""),
            sa.Column("email", sa.String(320), nullable=False, server_default=""),
            sa.Column("phone", sa.String(64), nullable=False, server_default=""),
            sa.Column("avatar_url", sa.String(512), nullable=False, server_default=""),
            sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
            sa.Column("locale", sa.String(16), nullable=False, server_default="en-US"),
            sa.Column("date_format", sa.String(16), nullable=False, server_default="YYYY-MM-DD"),
            sa.Column("bio", sa.Text(), nullable=False, server_default=""),
            sa.Column("theme_preference", sa.String(16), nullable=False, server_default="system"),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    # ── feedback_signals (app/feedback/models.py) ─────────────────────────
    if not _table_exists(bind, "feedback_signals"):
        op.create_table(
            "feedback_signals",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("signal_id", sa.String(128), nullable=False),
            sa.Column("accepted", sa.Boolean(), nullable=False),
            sa.Column("comment", sa.Text(), server_default=""),
            sa.Column("identity_id", sa.String(64), server_default=""),
            sa.Column("tenant_id", sa.String(64), server_default=""),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_feedback_signals_signal_id", "feedback_signals", ["signal_id"])
        op.create_index("ix_feedback_signals_identity_id", "feedback_signals", ["identity_id"])


def downgrade() -> None:
    bind = op.get_bind()
    for table in ("feedback_signals", "user_profiles", "ai_execution_records"):
        if _table_exists(bind, table):
            op.drop_table(table)