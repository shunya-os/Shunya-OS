"""R6B-2 ownership reconciliation: inherit organization_id from workspace.

Evidence: sh_objects.workspace_id -> sh_workspaces.organization_id is the
authoritative ownership chain. This migration:

1. Backfills NULL organization_id from the owning sh_workspace
   (safe — workspace organization is authoritative evidence).
2. Fixes organization_id mismatches where object.org != workspace.org
   (safe — workspace precedent wins).

Revision ID: g1_1_r6b_ownership_reconciliation
Revises: g1_1_r6b_media_tenancy
Create Date: 2026-09-11

The migration reads the workspace's parent organization and updates
the object to match. If the workspace has no organization either, the
object stays NULL (is owned by nobody — authorization will reject it).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "g1_1_r6b_ownership"
down_revision = "g1_1_r6b_media_tenancy"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Step 1: Backfill NULL organization_id from workspace
    result = conn.execute(sa.text("""
        UPDATE sh_objects s
        SET organization_id = w.organization_id
        FROM sh_workspaces w
        WHERE s.organization_id IS NULL
        AND w.id = s.workspace_id
        AND w.organization_id IS NOT NULL
    """))
    backfilled = result.rowcount if result else 0
    print(f"  Backfilled {backfilled} NULL organization_id from workspace")

    # Step 2: Fix organization_id mismatches (workspace org is authoritative)
    result = conn.execute(sa.text("""
        UPDATE sh_objects s
        SET organization_id = w.organization_id
        FROM sh_workspaces w
        WHERE s.organization_id IS NOT NULL
        AND w.id = s.workspace_id
        AND w.organization_id IS NOT NULL
        AND s.organization_id <> w.organization_id
    """))
    fixed = result.rowcount if result else 0
    print(f"  Fixed {fixed} organization_id mismatches (workspace org authoritative)")

    # Step 3: Log remaining NULL org_ids (these are orphaned — should be SAML/auth-gated)
    remaining = conn.execute(
        sa.text("SELECT count(*) FROM sh_objects WHERE organization_id IS NULL")
    ).scalar() or 0
    print(f"  Remaining NULL organization_id: {remaining} (orphaned — auth will reject)")


def downgrade():
    # The backfill cannot be reversed automatically. The previous state
    # is preserved in the database backup; no revert is provided.
    pass