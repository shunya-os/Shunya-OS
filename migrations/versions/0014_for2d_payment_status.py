"""FOR-2D: Add status lifecycle column to fin_payments.

FinancePayment lifecycle (PAYMENT_STATES in app/finance/governance.py):
pending → confirmed → allocated → reconciled, with cancelled/reversed exits.
Adds `status` (default 'pending') to fin_payments so payment state is
persisted and survives restarts.

Additive, idempotent: safe to run multiple times (column + index guarded).

Revision ID: for2d_payment_status
Revises: r6b28_age_verification_fields
Create Date: 2026-10-12 09:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "for2d_payment_status"
down_revision = "r6b28_age_verification_fields"


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("fin_payments")]
    if "status" not in cols:
        op.add_column(
            "fin_payments",
            sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        )


def downgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    pass  # additive only — no destructive downgrade