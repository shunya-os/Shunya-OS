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
    from migrations.guarded import guarded_op
    op = guarded_op()
    conn = op.get_bind()

    def _org_exists(org_id):
        return conn.execute(
            text("SELECT 1 FROM organizations WHERE id = :i"), {"i": org_id}
        ).scalar() is not None

    # ------------------------------------------------------------------
    # 1. Remap legacy org IDs (89 -> 7, 90 -> 1)
    #    These were tenant_id values from team_members that were never
    #    migrated to real organizations. Org 89 maps to Panchi Club (org 7),
    #    org 90 maps to Test Org (org 1).
    #
    #    These ids exist only in the historical production database. Applying
    #    them unconditionally on a fresh database would create references to
    #    organisations that do not exist, which the FK step below must then
    #    refuse — so each remap is applied only where its target exists.
    # ------------------------------------------------------------------
    for old_id, new_id, name in [(89, 7, "Panchi Club"), (90, 1, "Test Org")]:
        if not _org_exists(new_id):
            print(f"  SKIP: legacy remap org={old_id} -> org={new_id} ({name}) "
                  f"— target organisation absent")
            continue
        result = conn.execute(
            text("UPDATE sh_objects SET organization_id = :new "
                 "WHERE organization_id = :old"),
            {"new": new_id, "old": old_id},
        )
        print(f"  Remapped org={old_id} -> org={new_id} ({name}): {result.rowcount} rows")

    # ------------------------------------------------------------------
    # 2. Fix workspace org assignments
    #    Business workspace (spc_business) -> org 7 (Panchi Club), where that
    #    organisation exists (legacy data only).
    # ------------------------------------------------------------------
    if _org_exists(7):
        result = conn.execute(
            text("UPDATE sh_workspaces SET organization_id = 7 "
                 "WHERE id = 'spc_business' AND organization_id IS DISTINCT FROM 7")
        )
        print(f"  Business workspace -> org 7: {result.rowcount} rows")
    else:
        print("  SKIP: spc_business -> org 7 — target organisation absent")

    # Clear any assignment that cannot resolve to a real organisation. This is
    # the data precondition of the FK below and matches its ON DELETE SET NULL
    # semantics: an unresolvable owner becomes no owner, never a dangling id.
    result = conn.execute(
        text("""
            UPDATE sh_workspaces w SET organization_id = NULL
            WHERE w.organization_id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM organizations o
                              WHERE o.id = w.organization_id)
        """)
    )
    print(f"  Cleared unresolved workspace org assignments: {result.rowcount} rows")

    # ------------------------------------------------------------------
    # 3. Add FK: sh_workspaces.organization_id → organizations.id
    # ------------------------------------------------------------------
    ws_fks = [fk["constrained_columns"]
              for fk in sa.inspect(conn).get_foreign_keys("sh_workspaces")]
    if ["organization_id"] not in ws_fks:
        op.create_foreign_key(
            "sh_workspaces_organization_id_fkey",
            "sh_workspaces", "organizations",
            ["organization_id"], ["id"],
            ondelete="SET NULL",
        )
        print("  ADDED: FK sh_workspaces.organization_id → organizations.id")
    else:
        print("  SKIP: FK sh_workspaces.organization_id already exists")

    # ------------------------------------------------------------------
    # 4. Add FK: sh_objects.organization_id → organizations.id
    #    Same precondition applies to the object store.
    # ------------------------------------------------------------------
    result = conn.execute(
        text("""
            UPDATE sh_objects o SET organization_id = NULL
            WHERE o.organization_id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM organizations org
                              WHERE org.id = o.organization_id)
        """)
    )
    print(f"  Cleared unresolved object org assignments: {result.rowcount} rows")

    obj_fks = [fk["constrained_columns"]
               for fk in sa.inspect(conn).get_foreign_keys("sh_objects")]
    if ["organization_id"] not in obj_fks:
        op.create_foreign_key(
            "sh_objects_organization_id_fkey",
            "sh_objects", "organizations",
            ["organization_id"], ["id"],
            ondelete="SET NULL",
        )
        print("  ADDED: FK sh_objects.organization_id → organizations.id")
    else:
        print("  SKIP: FK sh_objects.organization_id already exists")


def downgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    op.drop_constraint("sh_objects_organization_id_fkey", "sh_objects", type_="foreignkey")
    op.drop_constraint("sh_workspaces_organization_id_fkey", "sh_workspaces", type_="foreignkey")
    print("  DROPPED: FK constraints on sh_objects and sh_workspaces")