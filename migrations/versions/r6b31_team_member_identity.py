"""G1.19 — team_members.identity_id parity.

`TeamMember.identity_id` (the canonical identity used by organization
membership, invitations and session resolution) is declared on the model and
written by the authentication/org-creation flows, but no migration ever added
the column. Boot-created databases had it; a database built from the migration
chain alone did not, so the first signup/login crashed with

    psycopg2.errors.UndefinedColumn: column team_members.identity_id does not exist

This forward-only, guarded revision restores model↔migration parity without
touching existing data or rewriting history:

  - the column is added only when it is absent (boot-created databases converge
    as a no-op);
  - the index is created only when absent;
  - no column is altered, dropped, or backfilled — existing identity values are
    left exactly as they are.

Revision ID: r6b31_team_member_identity
Revises: r6b30_boot_tables
"""
import sqlalchemy as sa
from alembic import op

revision = "r6b31_team_member_identity"
down_revision = "r6b30_boot_tables"
branch_labels = None
depends_on = None

_INDEX_NAME = "ix_team_members_identity_id"


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {c["name"] for c in inspector.get_columns("team_members")}
    if "identity_id" not in columns:
        op.add_column(
            "team_members",
            sa.Column("identity_id", sa.String(length=64), nullable=True),
        )

    indexes = {i["name"] for i in inspector.get_indexes("team_members")}
    if _INDEX_NAME not in indexes:
        op.create_index(_INDEX_NAME, "team_members", ["identity_id"])


def downgrade():
    # Forward-only by project convention: the column is model-required, so
    # removing it would break every authentication path. Downgrade is a no-op.
    pass
