"""R6B-2.7 — Content Studio lifecycle schema for m6_content_generations.

WHY
---
`ContentGeneration` (app/integration/models.py) declares two lifecycle columns
that NO migration ever created:

    status      varchar(20) NOT NULL default 'active'   (active | archived)
    is_deleted  boolean     default false               (trashed)

`0010_schema_reconciliation.py` only CREATEs the table without them, and
`db.create_all()` adds tables — never columns — so a production database that
already had `m6_content_generations` never received the columns. Verified on the
live database: the ORM query `SELECT id, status, is_deleted ...` raises
`UndefinedColumn`, and the history endpoint masked it as an empty success.

This revision closes that divergence. It is additive and guarded: on a database
whose model baseline already materialises the columns via `db.create_all()` the
ADD COLUMN steps are no-ops, so the chain converges from any starting point.

NOTE: the revision id must stay within 32 characters — Alembic stores it in
alembic_version.version_num, which is character varying(32).

Revision ID: r6b27_content_lifecycle
Revises: r6b27_workspace_memberships
"""
import sqlalchemy as sa
from alembic import op

revision = "r6b27_content_lifecycle"
down_revision = "r6b27_workspace_memberships"
branch_labels = None
depends_on = None


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    op.add_column(
        "m6_content_generations",
        sa.Column("status", sa.String(20), nullable=False,
                  server_default="active"),
    )
    op.add_column(
        "m6_content_generations",
        sa.Column("is_deleted", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
    )
    op.create_index(
        "ix_m6_content_gen_identity_status",
        "m6_content_generations",
        ["identity_id", "status"],
    )
    print("  m6_content_generations: status + is_deleted ensured")


def downgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    op.drop_index("ix_m6_content_gen_identity_status",
                  table_name="m6_content_generations")
    op.drop_column("m6_content_generations", "is_deleted")
    op.drop_column("m6_content_generations", "status")
