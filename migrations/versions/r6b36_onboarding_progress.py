"""r6b36 — persist onboarding step progress (G1.21).

WHY
---
``/api/v1/orgs/onboarding/step/<step>`` kept in-progress state in a module-level
dict (``_ONBOARDING``) and only the terminal "complete" flag was written to the
database. Consequences, reproduced against the real app:

  * a page reload in a *different worker process* reported step "profile" again;
  * a restart discarded the whole questionnaire position;
  * the client had no durable way to resume, so "save and resume" was not a
    product behaviour — it was process affinity.

WHAT
----
Two nullable columns on ``user_profiles`` (identity-keyed, the natural home for
per-identity state — no new table):

    onboarding_step             VARCHAR(30)   current step key
    onboarding_completed_steps  TEXT          JSON array of finished step keys

Additive and guarded: existing rows stay NULL, which the API reads as "not
started"; no backfill is invented, no default is imposed on historical data. The
terminal completion flag remains ``team_members.onboarding_completed`` — this
revision does not duplicate or reinterpret it.

Revision ID: r6b36_onboarding_progress
Revises: r6b35_missing_boot_tables
"""
import sqlalchemy as sa
from alembic import op  # noqa: F401

revision = "r6b36_onboarding_progress"
down_revision = "r6b35_missing_boot_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from migrations.guarded import guarded_op

    gop = guarded_op()
    gop.add_column("user_profiles", sa.Column("onboarding_step", sa.String(30), nullable=True))
    gop.add_column(
        "user_profiles",
        sa.Column("onboarding_completed_steps", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    from migrations.guarded import guarded_op

    gop = guarded_op()
    gop.drop_column("user_profiles", "onboarding_completed_steps")
    gop.drop_column("user_profiles", "onboarding_step")
