"""FDA3: Add truth_classification, provenance_idempotency, resolution fields.

Revision ID: 0004_fda3_memory_schema
Revises: 0003_add_evidence_unique_constraint
Create Date: 2026-08-11

This migration adds:
- memory_records.truth_classification, resolution_type, resolution_reason, injection_checked
- memory_candidates.truth_classification
- memory_provenances.provenance_source, provenance_source_id
- memory_provenances unique constraint uq_mp_source_idempotency
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_fda3_memory_schema"
down_revision: Union[str, None] = "0003_add_evidence_unique_constraint"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === memory_records ===
    # add truth_classification (default 'memory')
    op.add_column("memory_records",
        sa.Column("truth_classification", sa.String(20),
                  nullable=False, server_default="memory"))
    # add resolution fields
    op.add_column("memory_records",
        sa.Column("resolution_type", sa.String(30), nullable=True))
    op.add_column("memory_records",
        sa.Column("resolution_reason", sa.Text(), nullable=True))
    op.add_column("memory_records",
        sa.Column("injection_checked", sa.Boolean(),
                  nullable=False, server_default=sa.text("0")))

    # === memory_candidates ===
    op.add_column("memory_candidates",
        sa.Column("truth_classification", sa.String(20),
                  nullable=False, server_default="memory"))

    # === memory_provenances ===
    op.add_column("memory_provenances",
        sa.Column("provenance_source", sa.String(255), nullable=True))
    op.add_column("memory_provenances",
        sa.Column("provenance_source_id", sa.String(255), nullable=True))
    # unique constraint for idempotency
    op.create_unique_constraint(
        "uq_mp_source_idempotency", "memory_provenances",
        ["provenance_source", "provenance_source_id"],
    )


def downgrade() -> None:
    # memory_provenances
    op.drop_constraint("uq_mp_source_idempotency", "memory_provenances",
                       type_="unique")
    op.drop_column("memory_provenances", "provenance_source_id")
    op.drop_column("memory_provenances", "provenance_source")
    # memory_candidates
    op.drop_column("memory_candidates", "truth_classification")
    # memory_records
    op.drop_column("memory_records", "injection_checked")
    op.drop_column("memory_records", "resolution_reason")
    op.drop_column("memory_records", "resolution_type")
    op.drop_column("memory_records", "truth_classification")