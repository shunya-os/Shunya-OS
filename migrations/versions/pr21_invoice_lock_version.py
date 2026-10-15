"""PR #21: Add invoice lock identity, version chain columns to fin_invoices

Adds:
  - locked_by (VARCHAR(64), nullable) — identity string of the locking user
  - locked_at (DateTime, nullable) — when the lock was acquired
  - version_number (Integer, default 1) — edit version counter
  - parent_invoice_id (Integer, FK -> fin_invoices.id, nullable) — previous
    version for the version chain (historical snapshots link back here)

Revision ID: pr21_invoice_lock_version
Revises: r6b2_conversation_fk
Create Date: 2026-10-15
"""

import sqlalchemy as sa
from alembic import op

revision = "pr21_invoice_lock_version"
down_revision = "r6b2_conversation_fk"


def upgrade() -> None:
    op.add_column(
        "fin_invoices",
        sa.Column("locked_by", sa.String(64), nullable=True),
    )
    op.add_column(
        "fin_invoices",
        sa.Column("locked_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "fin_invoices",
        sa.Column("version_number", sa.Integer(), server_default="1"),
    )
    op.add_column(
        "fin_invoices",
        sa.Column(
            "parent_invoice_id",
            sa.Integer(),
            sa.ForeignKey("fin_invoices.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("fin_invoices", "parent_invoice_id")
    op.drop_column("fin_invoices", "version_number")
    op.drop_column("fin_invoices", "locked_at")
    op.drop_column("fin_invoices", "locked_by")