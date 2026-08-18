"""Remove workflow artifacts from sh_outcomes, drop orphan execution tables.

Changes:
1. sh_outcomes: add state JSON column, migrate stage->state, drop workflow columns
2. execution_instances: drop (orphan, no model, 3 rows, no references)
3. execution_tasks: drop (orphan, no model, 6 rows, no references)

Reversibility: SCHEMA-REVERSIBLE, DATA-DESTRUCTIVE.
- Schema shape is fully restored on downgrade (all columns + tables recreated).
- Historical data is NOT restored: 9 dropped columns (steps, stage->state,
  progress, expected/actual completion seconds, recovery_history,
  final_summary, last_error, error_count) plus 2 dropped tables
  (execution_instances, execution_tasks) lose their row-level data.
- Exception: 'stage' values were migrated into state JSON and are
  restored to their column on downgrade (TRANSFORMED, not lost).
- The downgrade comment stating data cannot be restored is accurate.

Revision ID: 0011_purify_execution_model
Revises: 0010_schema_reconciliation
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0011_purify_execution_model"
down_revision: Union[str, Sequence[str], None] = "0010_schema_reconciliation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === sh_outcomes: add state JSON column ===
    op.add_column("sh_outcomes", sa.Column("state", postgresql.JSONB, nullable=True))

    # Migrate existing stage values into state JSON
    op.execute("""
        UPDATE sh_outcomes
        SET state = jsonb_build_object('stage', stage)
        WHERE state IS NULL
    """)

    # Drop workflow artifact columns
    op.drop_column("sh_outcomes", "steps")
    op.drop_column("sh_outcomes", "stage")
    op.drop_column("sh_outcomes", "progress")
    op.drop_column("sh_outcomes", "expected_completion_seconds")
    op.drop_column("sh_outcomes", "actual_completion_seconds")
    op.drop_column("sh_outcomes", "recovery_history")
    op.drop_column("sh_outcomes", "final_summary")
    op.drop_column("sh_outcomes", "last_error")
    op.drop_column("sh_outcomes", "error_count")

    # === Drop orphan execution tables ===
    # Drop execution_tasks first (has FK to execution_instances)
    op.execute("DROP TABLE IF EXISTS execution_tasks CASCADE")
    op.execute("DROP TABLE IF EXISTS execution_instances CASCADE")


def downgrade() -> None:
    # Can't restore dropped data, but we can recreate the columns
    op.create_table("execution_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("execution_id", sa.Integer(), nullable=True),
        sa.Column("step_order", sa.Integer(), nullable=True),
        sa.Column("action_type", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table("execution_instances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("object_id", sa.Integer(), nullable=False),
        sa.Column("execution_type", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("result", postgresql.JSONB, nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    # Restore sh_outcomes columns
    op.add_column("sh_outcomes", sa.Column("error_count", sa.Integer(), server_default="0"))
    op.add_column("sh_outcomes", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("sh_outcomes", sa.Column("final_summary", postgresql.JSONB, nullable=True))
    op.add_column("sh_outcomes", sa.Column("recovery_history", postgresql.JSONB, server_default="[]"))
    op.add_column("sh_outcomes", sa.Column("actual_completion_seconds", sa.Integer(), nullable=True))
    op.add_column("sh_outcomes", sa.Column("expected_completion_seconds", sa.Integer(), server_default="30"))
    op.add_column("sh_outcomes", sa.Column("progress", sa.String(200), server_default="Received"))
    op.add_column("sh_outcomes", sa.Column("stage", sa.String(20), server_default="accepted"))
    op.add_column("sh_outcomes", sa.Column("steps", postgresql.JSONB, server_default="[]"))

    # Restore stage from state JSON
    op.execute("""
        UPDATE sh_outcomes
        SET stage = state->>'stage'
        WHERE state IS NOT NULL AND state->>'stage' IS NOT NULL
    """)

    op.drop_column("sh_outcomes", "state")