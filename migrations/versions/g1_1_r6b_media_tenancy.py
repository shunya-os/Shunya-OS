"""G1.1-R6B — Media asset tenancy: organization_id, workspace_id, sh_object_id.

Adds canonical tenant context columns to m6_media_assets so media records
can be scoped to an organization and workspace, and linked to their
canonical sh_objects entry via sh_object_id.
"""

from alembic import op
import sqlalchemy as sa

revision = "g1_1_r6b_media_tenancy"
down_revision = "g1_1_r6b_object_convergence"
branch_labels = None
depends_on = None


def upgrade():
    # ── Add tenant context columns ────────────────────────────────
    op.add_column(
        "m6_media_assets",
        sa.Column("organization_id", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "m6_media_assets",
        sa.Column("workspace_id", sa.String(64), nullable=False, server_default=""),
    )
    op.add_column(
        "m6_media_assets",
        sa.Column("sh_object_id", sa.String(64), nullable=True),
    )

    # ── Create indexes ────────────────────────────────────────────
    op.create_index(
        "ix_m6_media_assets_org_identity",
        "m6_media_assets",
        ["organization_id", "identity_id"],
    )
    op.create_index(
        "ix_m6_media_assets_sh_object",
        "m6_media_assets",
        ["sh_object_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_m6_media_assets_sh_object", table_name="m6_media_assets")
    op.drop_index("ix_m6_media_assets_org_identity", table_name="m6_media_assets")
    op.drop_column("m6_media_assets", "sh_object_id")
    op.drop_column("m6_media_assets", "workspace_id")
    op.drop_column("m6_media_assets", "organization_id")