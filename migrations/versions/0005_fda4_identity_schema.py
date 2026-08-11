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
    # === person_identities ===
    op.add_column("person_identities",
        sa.Column("source", sa.String(60), nullable=True))
    op.add_column("person_identities",
        sa.Column("source_id", sa.String(255), nullable=True))
    op.add_column("person_identities",
        sa.Column("confidence", sa.Float(), nullable=True,
                  server_default=sa.text("1.0")))
    op.add_column("person_identities",
        sa.Column("metadata_json", sa.Text(), nullable=True))

    # === persons ===
    op.add_column("persons",
        sa.Column("identity_type", sa.String(32), nullable=True))
    op.add_column("persons",
        sa.Column("metadata_json", sa.Text(), nullable=True))

    # === persons.tenant_id: migrate NULL → default tenant, then set NOT NULL ===
    # Step 1: assign any NULL tenant_id to 1 (default)
    op.execute("UPDATE persons SET tenant_id = 1 WHERE tenant_id IS NULL")
    # Step 2: alter column to NOT NULL
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