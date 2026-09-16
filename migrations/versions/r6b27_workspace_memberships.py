"""R6B-2.7 — canonical workspace authorization for sh_workspaces.

Creates ``sh_workspace_memberships``: the single authorization relationship for
canonical objects. It completes the chain

    identity → organization → authorized sh_workspace → sh_objects

``organization_id`` is intentionally absent: organization is derived through
``sh_workspaces.organization_id``, so a membership can never contradict the
workspace's ownership.

Additive and guarded: on a database whose model baseline already materialises
the table (db.create_all) this is a no-op, and the unique constraint / index
are only created when absent.

NOTE: the revision id must stay within 32 characters — Alembic stores it in
alembic_version.version_num, which is character varying(32).

Revision ID: r6b27_workspace_memberships
Revises: r6b25_member_tenant_nullable
"""
import sqlalchemy as sa
from alembic import op

revision = "r6b27_workspace_memberships"
down_revision = "r6b25_member_tenant_nullable"
branch_labels = None
depends_on = None


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    if not op.has_table("sh_workspace_memberships"):
        op.create_table(
            "sh_workspace_memberships",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("workspace_id", sa.String(20), nullable=False),
            sa.Column("identity_id", sa.String(64), nullable=False),
            sa.Column("role", sa.String(30), nullable=False,
                      server_default="member"),
            sa.Column("is_active", sa.Boolean(), nullable=False,
                      server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["workspace_id"], ["sh_workspaces.id"],
                name="sh_workspace_memberships_workspace_id_fkey",
                ondelete="CASCADE",
            ),
            sa.UniqueConstraint("workspace_id", "identity_id",
                                name="uq_sh_workspace_member"),
        )
        print("  CREATED: sh_workspace_memberships")

    op.create_index("ix_sh_ws_member_workspace", "sh_workspace_memberships",
                    ["workspace_id"])
    op.create_index("ix_sh_ws_member_identity", "sh_workspace_memberships",
                    ["identity_id"])
    op.create_unique_constraint("uq_sh_workspace_member",
                                "sh_workspace_memberships",
                                ["workspace_id", "identity_id"])
    op.create_foreign_key(
        "sh_workspace_memberships_workspace_id_fkey",
        "sh_workspace_memberships", "sh_workspaces",
        ["workspace_id"], ["id"], ondelete="CASCADE",
    )


def downgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    op.drop_constraint("sh_workspace_memberships_workspace_id_fkey",
                       "sh_workspace_memberships", type_="foreignkey")
    op.drop_constraint("uq_sh_workspace_member", "sh_workspace_memberships",
                       type_="unique")
    op.drop_index("ix_sh_ws_member_identity",
                  table_name="sh_workspace_memberships")
    op.drop_index("ix_sh_ws_member_workspace",
                  table_name="sh_workspace_memberships")
    op.drop_table("sh_workspace_memberships")
