"""G1.1-R5 — Execution spine: execution_runs, execution_state_transitions, task_lifecycle.

Adds the canonical execution tracking tables:

- execution_runs              — one row per execution (lifecycle state machine)
- execution_state_transitions — audit trail of phase transitions
- task_lifecycle              — user-facing task tracking linked to runs

Down revision is the current head: g1_1_r1_fix_org_chain

NOTE: The app factory calls db.create_all() at startup, so these tables may
already exist when this migration runs. Table creation is therefore
defensive — existing tables are skipped.
"""

from alembic import op
import sqlalchemy as sa

revision = "g1_1_r5_execution_spine"
down_revision = "g1_1_r1_fix_org_chain"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # ------------------------------------------------------------------
    # 1. execution_runs — canonical execution run record
    # ------------------------------------------------------------------
    if not inspector.has_table("execution_runs"):
        op.create_table(
            "execution_runs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("execution_id", sa.String(length=36), nullable=False, unique=True),
            sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
            sa.Column("identity_id", sa.Integer(), sa.ForeignKey("shunya_identities.id"), nullable=True),
            sa.Column("workspace_id", sa.Integer(), nullable=True),
            sa.Column("run_type", sa.String(length=50), nullable=False, server_default="task"),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
            sa.Column("current_phase", sa.String(length=50), nullable=True),
            sa.Column("intent", sa.Text(), nullable=False),
            sa.Column("intent_summary", sa.String(length=255), nullable=True),
            sa.Column("used_company_data", sa.Boolean(), server_default=sa.false()),
            sa.Column("used_internet_data", sa.Boolean(), server_default=sa.false()),
            sa.Column("used_ai", sa.Boolean(), server_default=sa.false()),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("duration_seconds", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("result", sa.JSON(), nullable=True),
            sa.Column("result_summary", sa.Text(), nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("error_count", sa.Integer(), server_default="0"),
            sa.Column("correlation_id", sa.String(length=36), nullable=True),
            sa.Column("parent_run_id", sa.String(length=36), nullable=True),
            sa.Column("source", sa.String(length=30), server_default="user"),
            sa.Column("outcome_id", sa.String(length=12), nullable=True),
            sa.Column("commitment_id", sa.String(length=64), nullable=True),
            sa.Column("commitment_type", sa.String(length=64), nullable=True),
        )
        op.create_index("ix_execution_runs_execution_id", "execution_runs", ["execution_id"])
        op.create_index("ix_execution_runs_status", "execution_runs", ["status"])
        op.create_index("ix_execution_runs_correlation_id", "execution_runs", ["correlation_id"])
        op.create_index("ix_execution_runs_parent_run_id", "execution_runs", ["parent_run_id"])
        op.create_index("ix_execution_runs_outcome_id", "execution_runs", ["outcome_id"])
        op.create_index("ix_execution_runs_commitment_id", "execution_runs", ["commitment_id"])
        op.create_index("ix_execution_runs_org_status", "execution_runs", ["organization_id", "status"])
        op.create_index("ix_execution_runs_org_created", "execution_runs", ["organization_id", "created_at"])
        print("  CREATED: execution_runs")
    else:
        print("  SKIP: execution_runs already exists")

    # ------------------------------------------------------------------
    # 2. execution_state_transitions — phase transition audit trail
    # ------------------------------------------------------------------
    if not inspector.has_table("execution_state_transitions"):
        op.create_table(
            "execution_state_transitions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("execution_id", sa.String(length=36),
                      sa.ForeignKey("execution_runs.execution_id"), nullable=False),
            sa.Column("state_before", sa.String(length=50), nullable=False),
            sa.Column("state_after", sa.String(length=50), nullable=False),
            sa.Column("transitioned_at", sa.DateTime(), nullable=True),
            sa.Column("actor", sa.String(length=64), server_default="system"),
            sa.Column("reason", sa.Text(), server_default=""),
            sa.Column("correlation_id", sa.String(length=36), nullable=True),
            sa.Column("extra_metadata", sa.JSON(), nullable=True),
        )
        op.create_index("ix_execution_state_transitions_execution_id",
                        "execution_state_transitions", ["execution_id"])
        op.create_index("ix_execution_state_transitions_exec_phase",
                        "execution_state_transitions", ["execution_id", "state_after"])
        print("  CREATED: execution_state_transitions")
    else:
        print("  SKIP: execution_state_transitions already exists")

    # ------------------------------------------------------------------
    # 3. task_lifecycle — user-facing task tracking
    # ------------------------------------------------------------------
    if not inspector.has_table("task_lifecycle"):
        op.create_table(
            "task_lifecycle",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("task_id", sa.String(length=36), nullable=False, unique=True),
            sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
            sa.Column("identity_id", sa.Integer(), sa.ForeignKey("shunya_identities.id"), nullable=True),
            sa.Column("execution_run_id", sa.String(length=36),
                      sa.ForeignKey("execution_runs.execution_id"), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), server_default=""),
            sa.Column("status", sa.String(length=30), server_default="pending"),
            sa.Column("current_phase", sa.String(length=50), nullable=True),
            sa.Column("phase_history", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("duration_seconds", sa.Float(), nullable=True),
            sa.Column("result_summary", sa.Text(), nullable=True),
            sa.Column("result_detail", sa.JSON(), nullable=True),
            sa.Column("outcome", sa.String(length=30), nullable=True),
            sa.Column("next_action", sa.String(length=255), nullable=True),
            sa.Column("next_action_url", sa.String(length=255), nullable=True),
        )
        op.create_index("ix_task_lifecycle_task_id", "task_lifecycle", ["task_id"])
        op.create_index("ix_task_lifecycle_status", "task_lifecycle", ["status"])
        op.create_index("ix_task_lifecycle_execution_run_id", "task_lifecycle", ["execution_run_id"])
        op.create_index("ix_task_lifecycle_org_status", "task_lifecycle", ["organization_id", "status"])
        op.create_index("ix_task_lifecycle_org_created", "task_lifecycle", ["organization_id", "created_at"])
        print("  CREATED: task_lifecycle")
    else:
        print("  SKIP: task_lifecycle already exists")


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table("task_lifecycle"):
        op.drop_table("task_lifecycle")
    if inspector.has_table("execution_state_transitions"):
        op.drop_table("execution_state_transitions")
    if inspector.has_table("execution_runs"):
        op.drop_table("execution_runs")