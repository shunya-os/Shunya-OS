"""add_push_subscription_model

Revision ID: 9dd21cd22a84
Revises: g5_001
Create Date: 2026-08-21 13:19:01.672378

Targeted migration: ONLY PushSubscription table. Schema reconciliation
of legacy tables (api_keys, automations, etc.) deferred — those tables
predate this migration and are not production-active.

See docs/zero_gap/SQL_SCHEMA_RECONCILIATION.md for full schema cleanup.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9dd21cd22a84"
down_revision: Union[str, Sequence[str], None] = "g5_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add PushSubscription table for PWA push notifications.

    This table stores browser push subscription endpoints per identity,
    used by the Web Push API for PWA notifications (CG-10 / D-10).
    """
    op.create_table(
        "shunya_push_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("identity_id", sa.String(length=64), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.Text(), nullable=True),
        sa.Column("auth", sa.Text(), nullable=True),
        sa.Column("subscription_json", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_push_sub_endpoint",
        "shunya_push_subscriptions",
        ["endpoint"],
        unique=True,
    )
    op.create_index(
        "ix_push_sub_identity",
        "shunya_push_subscriptions",
        ["identity_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop PushSubscription table."""
    op.drop_index("ix_push_sub_identity", table_name="shunya_push_subscriptions")
    op.drop_index("ix_push_sub_endpoint", table_name="shunya_push_subscriptions")
    op.drop_table("shunya_push_subscriptions")