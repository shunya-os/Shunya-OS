"""G1.1-R6B — Business object convergence migration: sh_objects gains content column.

FounderObject has a 'content' (Text) column that ShunyaObject does not.
This migration adds the column to support migrating writes away from founder_objects.
"""
from alembic import op
import sqlalchemy as sa

revision = "g1_1_r6b_object_convergence"
down_revision = "g1_1_r6_evidence_constraint"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sh_objects", sa.Column("content", sa.Text(), nullable=True))
    op.add_column("sh_objects", sa.Column("space_id", sa.String(64), nullable=True))
    op.create_index("ix_sh_objects_space_id", "sh_objects", ["space_id"])


def downgrade():
    op.drop_index("ix_sh_objects_space_id", table_name="sh_objects")
    op.drop_column("sh_objects", "space_id")
    op.drop_column("sh_objects", "content")