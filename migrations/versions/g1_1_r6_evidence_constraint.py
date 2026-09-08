"""G1.1-R6 — Relax evidence_records unique constraint for execution-run evidence.

The uq_evidence_source constraint (source_type, source_id) prevents multiple
evidence records from being linked to the same execution run. This means
company-data evidence, internet-data evidence, and AI-reasoning evidence
cannot all coexist for the same execution.

Fix: Drop the unique constraint and add a simple index instead.
"""

from alembic import op

revision = "g1_1_r6_evidence_constraint"
down_revision = "g1_1_r5_provider_cost"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("uq_evidence_source", "evidence_records", type_="unique")
    op.create_index("ix_evidence_source_type_id", "evidence_records", ["source_type", "source_id"])


def downgrade():
    op.drop_index("ix_evidence_source_type_id", table_name="evidence_records")
    op.create_unique_constraint("uq_evidence_source", "evidence_records", ["source_type", "source_id"])