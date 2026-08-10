"""Add unique constraint on evidence_records (source_type, source_id).

This enables database-level idempotency enforcement.
FDA2 — Core Runtime Consolidation.
"""

import sqlalchemy as sa
from alembic import op

revision = '0003_add_evidence_unique_constraint'
down_revision = '0002_schema_reconciliation'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    constraints = inspector.get_unique_constraints('evidence_records')
    existing = [c['name'] for c in constraints]

    if 'uq_evidence_source' not in existing:
        op.create_unique_constraint(
            'uq_evidence_source',
            'evidence_records',
            ['source_type', 'source_id'],
        )


def downgrade():
    op.drop_constraint('uq_evidence_source', 'evidence_records', type_='unique')