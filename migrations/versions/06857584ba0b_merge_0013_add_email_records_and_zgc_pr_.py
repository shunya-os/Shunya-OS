"""Merge 0013_add_email_records and zgc_pr_17c_durable_memory

Revision ID: 06857584ba0b
Revises: zgc_pr_17c_durable_memory, 0013_add_email_records
Create Date: 2026-09-01 16:12:48.772773

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06857584ba0b'
down_revision: Union[str, Sequence[str], None] = ('zgc_pr_17c_durable_memory', '0013_add_email_records')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
