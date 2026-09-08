"""G1.1-R5 fix — timezone-aware timestamps for execution spine tables.

The execution_runs / execution_state_transitions / task_lifecycle tables
were created with `timestamp without time zone` columns. With a non-UTC
session timezone (Europe/Berlin), aware UTC datetimes were stored as
local wall-clock and read back as naive — breaking duration arithmetic
and producing timestamps the frontend would misread as local time.

This migration converts all DateTime columns in the three R5 spine tables
to `timestamp with time zone` so UTC round-trips correctly.
"""

from alembic import op
import sqlalchemy as sa

revision = "g1_1_r5_tz_aware_spine"
down_revision = "g1_1_r5_execution_spine"
branch_labels = None
depends_on = None


def upgrade():
    # execution_runs — timing columns
    for col in ("started_at", "completed_at", "created_at", "updated_at"):
        op.alter_column(
            "execution_runs", col,
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=True,
        )
    # execution_state_transitions
    op.alter_column(
        "execution_state_transitions", "transitioned_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    # task_lifecycle — timing columns
    for col in ("created_at", "started_at", "completed_at"):
        op.alter_column(
            "task_lifecycle", col,
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=True,
        )


def downgrade():
    for col in ("started_at", "completed_at", "created_at", "updated_at"):
        op.alter_column(
            "execution_runs", col,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=True,
        )
    op.alter_column(
        "execution_state_transitions", "transitioned_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
    for col in ("created_at", "started_at", "completed_at"):
        op.alter_column(
            "task_lifecycle", col,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=True,
        )