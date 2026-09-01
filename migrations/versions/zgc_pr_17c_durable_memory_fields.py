"""ZGC-PR-17C — Add durable memory fields to memory_records.

Additive migration: confidence, owner_identity_id, source columns on
memory_records — required by the MemoryEngine → MemoryRecord durable bridge.
Idempotent: safe to run multiple times.

Revision ID: zgc_pr_17c_durable_memory
Revises: f5429b50dbc6
Create Date: 2026-09-01 08:40:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "zgc_pr_17c_durable_memory"
down_revision = "f5429b50dbc6"


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("memory_records")]
    if "confidence" not in cols:
        op.add_column("memory_records", sa.Column("confidence", sa.Float(), server_default="1.0"))
    if "owner_identity_id" not in cols:
        op.add_column("memory_records", sa.Column("owner_identity_id", sa.String(64)))
        op.create_index("ix_mr_owner_identity", "memory_records", ["owner_identity_id"])
    if "source" not in cols:
        op.add_column("memory_records", sa.Column("source", sa.String(255)))


def downgrade():
    pass  # additive only — no destructive downgrade
