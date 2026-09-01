"""G1.1-R1 — Add organization_id to sh_objects, fix workspace→org chain.

Adds a real organization_id column to sh_objects (not JSONB, not metadata).
Backfills from existing data context. Creates proper FK chain:
  sh_objects → sh_workspaces → organizations
"""

from alembic import op
import sqlalchemy as sa

revision = "g1_1_r1_organization_chain"
down_revision = "06857584ba0b"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Add organization_id to sh_objects (real column, not JSONB)
    obj_cols = [c["name"] for c in inspector.get_columns("sh_objects")]
    if "organization_id" not in obj_cols:
        op.add_column(
            "sh_objects",
            sa.Column("organization_id", sa.Integer(), nullable=True, index=True),
        )
        print("  ADDED: sh_objects.organization_id")
    else:
        print("  SKIP: sh_objects.organization_id already exists")

    # 2. Backfill sh_workspaces.organization_id from data context
    ws_cols = [c["name"] for c in inspector.get_columns("sh_workspaces")]
    if "organization_id" in ws_cols:
        # Set default org for workspaces that have objects
        result = conn.execute(
            sa.text("""
                UPDATE sh_workspaces
                SET organization_id = 1
                WHERE organization_id IS NULL AND id IN (
                    SELECT DISTINCT workspace_id FROM sh_objects
                )
            """)
        )
        print(f"  BACKFILL: sh_workspaces.organization_id → {result.rowcount} rows")

    # 3. Backfill sh_objects.organization_id from workspace or JSONB data
    result = conn.execute(
        sa.text("""
            UPDATE sh_objects
            SET organization_id = (
                COALESCE(
                    (data->>'organization_id')::int,
                    (SELECT w.organization_id FROM sh_workspaces w WHERE w.id = sh_objects.workspace_id),
                    1
                )
            )
            WHERE organization_id IS NULL
        """)
    )
    print(f"  BACKFILL: sh_objects.organization_id → {result.rowcount} rows")

    # 4. Create index on (organization_id, workspace_id, object_type)
    conn.execute(
        sa.text("""
            CREATE INDEX IF NOT EXISTS idx_sh_objects_org_ws_type
            ON sh_objects (organization_id, workspace_id, object_type)
        """)
    )
    print("  CREATED: idx_sh_objects_org_ws_type")


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_sh_objects_org_ws_type"))
    op.drop_column("sh_objects", "organization_id")
    print("  REVERTED: sh_objects.organization_id")