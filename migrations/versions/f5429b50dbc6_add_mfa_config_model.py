"""add_mfa_config_model

Revision ID: f5429b50dbc6
Revises: 9dd21cd22a84
Create Date: 2026-08-21 13:57:57.197425

Targeted migration: ONLY shunya_mfa_configs table. No DROP TABLE operations.
Schema reconciliation of legacy tables deferred (see docs/zero_gap/CANONICAL_COUNT_FREEZE.md).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f5429b50dbc6"
down_revision: Union[str, Sequence[str], None] = "9dd21cd22a84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add MFAConfig table for persistent TOTP two-factor auth."""
    op.create_table(
        "shunya_mfa_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("secret", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("recovery_codes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["team_members.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_shunya_mfa_configs_user_id"),
        "shunya_mfa_configs",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    """Drop MFAConfig table."""
    op.drop_index(
        op.f("ix_shunya_mfa_configs_user_id"),
        table_name="shunya_mfa_configs",
    )
    op.drop_table("shunya_mfa_configs")