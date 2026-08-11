"""FDA4: Identity schema — source, confidence, metadata_json, tenant_id NOT NULL.

Revision ID: 0005_fda4_identity_schema
Revises: 0004_fda3_memory_schema
Create Date: 2026-08-11

This migration adds:
- person_identities.source, source_id, confidence, metadata_json
- persons.identity_type, metadata_json
- persons.tenant_id set NOT NULL (requires data migration)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_fda4_identity_schema"
down_revision: Union[str, None] = "0004_fda3_memory_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"

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

    def _column_exists(table: str, column: str) -> bool:
        try:
            cols = [c[1] for c in conn.execute(
                sa.text(f"PRAGMA table_info({table})")).fetchall()]
            return column in cols
        except Exception:
            return False

    # === person_identities ===
    if _table_exists("person_identities"):
        for col, col_type in [
            ("source", sa.String(60)),
            ("source_id", sa.String(255)),
            ("confidence", sa.Float()),
            ("metadata_json", sa.Text()),
        ]:
            if not _column_exists("person_identities", col):
                op.add_column("person_identities", sa.Column(col, col_type, nullable=True))

    # === persons ===
    if _table_exists("persons"):
        if not _column_exists("persons", "identity_type"):
            op.add_column("persons",
                sa.Column("identity_type", sa.String(32), nullable=True))
        if not _column_exists("persons", "metadata_json"):
            op.add_column("persons",
                sa.Column("metadata_json", sa.Text(), nullable=True))

        # persons.tenant_id: migrate NULL → default tenant, then set NOT NULL
        # Skip on SQLite which doesn't support ALTER COLUMN SET NOT NULL
        if not is_sqlite:
            op.execute("UPDATE persons SET tenant_id = 1 WHERE tenant_id IS NULL")
            op.alter_column("persons", "tenant_id",
                            existing_type=sa.Integer(),
                            nullable=False)


def downgrade() -> None:
    # persons
    op.alter_column("persons", "tenant_id",
                    existing_type=sa.Integer(),
                    nullable=True)
    op.drop_column("persons", "metadata_json")
    op.drop_column("persons", "identity_type")
    # person_identities
    op.drop_column("person_identities", "metadata_json")
    op.drop_column("person_identities", "confidence")
    op.drop_column("person_identities", "source_id")
    op.drop_column("person_identities", "source")