"""r6b33 — personal-scope workspace tables come under Alembic authority (G1.21).

WHY
---
``app.workspace.models.Workspace`` (``user_workspaces``) and
``WorkspaceMembership`` (``user_workspace_memberships``) were materialised **only**
by ``db.create_all()`` at application boot. No revision in the chain creates them
(``grep -rn user_workspace migrations/versions/*.py`` → no source hit before this
one), so a migration-only PostgreSQL install had no personal-scope tables at all.

Observed on the disposable G1.21 cluster (127.0.0.1:5445, database
``shunya_g121_probe``) after ``alembic upgrade head``:

    tables=177  fks=32  user_workspace_tables=NONE

and after ``create_app()`` booted against the same database:

    tables=184  fks=36  user_workspace_tables=user_workspace_memberships,user_workspaces

The two tables appearing only after boot is the masking this revision removes: a
deployment that runs migrations with a role that cannot CREATE tables (or that
never boots the app before serving) has no personal scope.

WHAT
----
Forward-only, additive, guarded (``migrations.guarded.guarded_op``):

  - every step is skipped when the table/index already exists, so a boot-created
    database converges and no data is touched;
  - column definitions are FROZEN here (not imported from mutable ORM metadata);
  - no column is dropped, re-typed or made stricter for existing rows;
  - the FK ``user_workspace_memberships.workspace_id → user_workspaces.id`` is
    created together with its parent table, so it can never hit orphan rows.

Revision ID: r6b33_personal_workspace_tables
Revises: r6b32_organizations_parity
"""
import sqlalchemy as sa
from alembic import op

revision = "r6b33_personal_workspace_tables"
down_revision = "r6b32_organizations_parity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from migrations.guarded import guarded_op

    gop = guarded_op()

    # ── user_workspaces (personal scope; app.workspace.models.Workspace) ──
    gop.create_table(
        "user_workspaces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("workspace_type", sa.String(30), nullable=False,
                  server_default="personal"),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("owner_identity_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(30), server_default="active"),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    if gop.has_table("user_workspaces"):
        gop.create_index("ix_user_workspaces_workspace_id", "user_workspaces",
                         ["workspace_id"], unique=True)
        gop.create_index("ix_user_workspaces_owner_identity_id", "user_workspaces",
                         ["owner_identity_id"])

    # ── user_workspace_memberships (app.workspace.models.WorkspaceMembership) ──
    gop.create_table(
        "user_workspace_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.Integer(),
                  sa.ForeignKey("user_workspaces.id", name="user_workspace_memberships_workspace_id_fkey"),
                  nullable=False),
        sa.Column("identity_id", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), server_default=""),
        sa.Column("role", sa.String(30), server_default="owner"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
    )
    if gop.has_table("user_workspace_memberships"):
        gop.create_index("ix_user_workspace_memberships_identity_id",
                         "user_workspace_memberships", ["identity_id"])
        gop.create_index("ix_user_workspace_memberships_workspace_id",
                         "user_workspace_memberships", ["workspace_id"])


def downgrade() -> None:
    """Intentionally additive-only.

    Dropping these tables would destroy every personal-scope workspace and its
    memberships. A destructive downgrade requires a separately authorized,
    reviewed migration with an explicit data-export step; it is not provided
    here and is not reversible from this revision.
    """
    pass
