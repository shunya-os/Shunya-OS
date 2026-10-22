"""r6b37 — durable onboarding questionnaire sessions (G1.21).

See app/onboarding/models.py for the defect: questionnaire state lived in a
process-local dict, so a reload on another worker or any restart restarted the
questionnaire at question one.

Additive and guarded: no existing table or row is modified, and a boot-created
database converges (the table already exists from ``db.create_all()``).

Revision ID: r6b37_onboarding_sessions
Revises: r6b36_onboarding_progress
"""
import sqlalchemy as sa
from alembic import op  # noqa: F401

revision = "r6b37_onboarding_sessions"
down_revision = "r6b36_onboarding_progress"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from migrations.guarded import guarded_op

    gop = guarded_op()
    gop.create_table(
        "onboarding_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("identity_id", sa.String(128), nullable=False),
        sa.Column("stage", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("question_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("answers_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("completed_stages_json", sa.Text(), nullable=False,
                  server_default="[]"),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
    )
    if gop.has_table("onboarding_sessions"):
        gop.create_index("ix_onboarding_sessions_organization_id",
                         "onboarding_sessions", ["organization_id"])
        gop.create_index("ix_onboarding_sessions_identity_id",
                         "onboarding_sessions", ["identity_id"])
        gop.create_unique_constraint(
            "uq_onboarding_session_identity", "onboarding_sessions",
            ["organization_id", "identity_id"])


def downgrade() -> None:
    from migrations.guarded import guarded_op

    gop = guarded_op()
    gop.drop_table("onboarding_sessions")
