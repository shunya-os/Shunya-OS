"""Add unique constraint on evidence_records (source_type, source_id).

This enables database-level idempotency enforcement.
FDA2 — Core Runtime Consolidation.
"""

import sqlalchemy as sa
from alembic import op

revision = '0003_evidence_unique_constr'
down_revision = '0002_schema_reconciliation'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    def _table_exists(name: str) -> bool:
        dialect = conn.dialect.name
        if dialect == "sqlite":
            result = conn.execute(
                sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
                {"name": name},
            ).fetchone()
            return result is not None
        else:
            result = conn.execute(
                sa.text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_name = :name)"
                ),
                {"name": name},
            ).fetchone()
            return result[0] if result else False

    if not _table_exists("evidence_records"):
        return

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