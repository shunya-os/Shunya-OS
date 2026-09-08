"""G1.1-R5 follow-through — provider/model/cost telemetry on execution_runs.

Adds nullable columns to execution_runs so the AI pipeline can record
which provider/model was used and whether cost is measurable.

§30 rule: never invent costs. If cost cannot be measured, it stays NULL.
NULL = "not measured", not "free".
"""

from alembic import op
import sqlalchemy as sa

revision = "g1_1_r5_provider_cost"
down_revision = "g1_1_r5_tz_aware_spine"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("execution_runs", sa.Column("provider_used", sa.String(80), nullable=True))
    op.add_column("execution_runs", sa.Column("model_used", sa.String(120), nullable=True))
    op.add_column("execution_runs", sa.Column("est_cost_currency", sa.String(8), nullable=True))
    op.add_column("execution_runs", sa.Column("est_cost_amount", sa.Float(), nullable=True))
    op.add_column("execution_runs", sa.Column("cost_is_estimate", sa.Boolean(), nullable=True))


def downgrade():
    for col in ("provider_used", "model_used", "est_cost_currency", "est_cost_amount", "cost_is_estimate"):
        op.drop_column("execution_runs", col)