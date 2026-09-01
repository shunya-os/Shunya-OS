"""G1.1-R1 fix — org chain FK constraints and data remap.

Adds FK constraints on:
- sh_workspaces.organization_id → organizations.id
- sh_objects.organization_id → organizations.id

Remaps legacy tenant_id values (89, 90) to real organization IDs.
Fixes sh_workspaces org assignment.
This migration is safe to run even if constraints already exist.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "g1_1_r1_fix_org_chain"
down_revision = "g1_1_r1_organization_chain"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # ------------------------------------------------------------------
    # 1. Remap legacy org IDs (89 -> 7, 90 -> 1)
    #    These were tenant_id values from team_members that were never
    #    migrated to real organizations. Org 89 maps to Panchi Club (org 7),
    #    org 90 maps to Test Org (org 1).
    # ------------------------------------------------------------------
    for old_id, new_id, name in [(89, 7, "Panchi Club"), (90, 1, "Test Org")]:
        result = conn.execute(
            text(f"UPDATE sh_objects SET organization_id = {new_id} WHERE organization_id = {old_id}")
        )
        print(f"  Remapped org={old_id} -> org={new_id} ({name}): {result.rowcount} rows")

    # ------------------------------------------------------------------
    # 2. Fix workspace org assignments
    #    Business workspace (spc_business) -> org 7 (Panchi Club)
    # ------------------------------------------------------------------
    result = conn.execute(
        text("""UPDATE sh_workspaces SET organization_id = 7 
                WHERE id = 'spc_business' AND organization_id IS DISTINCT FROM 7""")
    )
    print(f"  Business workspace -> org 7: {result.rowcount} rows")

    # Null workspaces -> default org 1
    result = conn.execute(
        text("UPDATE sh_workspaces SET organization_id = 1 WHERE organization_id IS NULL")
    )
    print(f"  NULL workspace org -> org 1: {result.rowcount} rows")

    # ------------------------------------------------------------------
    # 3. Add FK: sh_workspaces.organization_id → organizations.id
    # ------------------------------------------------------------------
    ws_fks = [fk["constrained_columns"] for fk in inspector.get_foreign_keys("sh_workspaces")]
    if ["organization_id"] not in ws_fks:
        try:
            op.create_foreign_key(
                "sh_workspaces_organization_id_fkey",
                "sh_workspaces", "organizations",
                ["organization_id"], ["id"],
                ondelete="SET NULL",
            )
            print("  ADDED: FK sh_workspaces.organization_id → organizations.id")
        except Exception as e:
            print(f"  WARNING (non-fatal): {e}")
    else:
        print("  SKIP: FK sh_workspaces.organization_id already exists")

    # ------------------------------------------------------------------
    # 4. Add FK: sh_objects.organization_id → organizations.id
    # ------------------------------------------------------------------
    obj_fks = [fk["constrained_columns"] for fk in inspector.get_foreign_keys("sh_objects")]
    if ["organization_id"] not in obj_fks:
        try:
            op.create_foreign_key(
                "sh_objects_organization_id_fkey",
                "sh_objects", "organizations",
                ["organization_id"], ["id"],
                ondelete="SET NULL",
            )
            print("  ADDED: FK sh_objects.organization_id → organizations.id")
        except Exception as e:
            print(f"  WARNING (non-fatal): {e}")
    else:
        print("  SKIP: FK sh_objects.organization_id already exists")


def downgrade():
    op.drop_constraint("sh_objects_organization_id_fkey", "sh_objects", type_="foreignkey")
    op.drop_constraint("sh_workspaces_organization_id_fkey", "sh_workspaces", type_="foreignkey")
    print("  DROPPED: FK constraints on sh_objects and sh_workspaces")