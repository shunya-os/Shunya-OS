"""r6b-2: re-point founder_conversations FK from founder_objects to sh_objects

Background: the canonical model (R6B-2) changed founder_conversations.object_id
FK target from founder_objects(object_id) to sh_objects(object_id), but the
production DB migration was never created. This was discovered because commit
07a1fae (taxation engine) added workaround code that creates FounderObject rows
to satisfy the still-old FK — triggering GATE 7 regression guards.

This migration:
 1. Creates sh_objects rows for the ~12 orphan founder_conversations that have
    no matching sh_objects row (using the identity's first workspace/org when
    available, or a placeholder workspace otherwise).
 2. Drops the old FK (founder_conversations → founder_objects).
 3. Adds the new FK (founder_conversations → sh_objects).

After this migration, all three FounderObject-creation blocks removed in
the companion code change (PR #22) become correct — the FK target is sh_objects
and the ObjectService.create() call in routes.py and context-resolved path in
conversation_bridge.py already create canonical rows there.

Revision ID: r6b2_conversation_fk
Revises: r6b29_alert_events
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "r6b2_conversation_fk"
down_revision: Union[str, None] = "r6b29_alert_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── Step 1: Backfill sh_objects rows for orphan conversations ──
    # Each orphan (founder_conversations row with no matching sh_objects row)
    # needs a canonical row to satisfy the coming FK.
    # We use the identity's first authorised workspace. For truly orphan
    # conversations (no identity, no workspace), create a minimal system
    # workspace placeholder so the sh_objects.workspace_id NOT NULL
    # constraint is satisfied.
    conn.execute(sa.text("""
        INSERT INTO sh_workspaces (id, name, workspace_type, created_by,
                                   created_at, status, organization_id)
        SELECT 'ws_migration_fallback', 'Migration Fallback', 'system',
               'system', now(), 'active', NULL
        WHERE NOT EXISTS (
            SELECT 1 FROM sh_workspaces WHERE id = 'ws_migration_fallback'
        )
    """))
    conn.execute(sa.text("""
        INSERT INTO sh_objects (object_id, workspace_id, organization_id,
                                object_type, name, status, created_by, created_at,
                                updated_at, is_deleted)
        SELECT fc.object_id,
               COALESCE(ws.id, 'ws_migration_fallback'),
               COALESCE(om.organization_id, ws.organization_id),
               'conversation',
               COALESCE(fc.title, 'AI Chat'),
               'active',
               COALESCE(fc.identity_id, 'system'),
               fc.created_at, fc.created_at, false
        FROM founder_conversations fc
        LEFT JOIN sh_objects o ON o.object_id = fc.object_id
        LEFT JOIN org_members om ON om.identity_id = fc.identity_id
            AND om.is_active = true
        LEFT JOIN sh_workspace_memberships wsm
            ON wsm.identity_id = fc.identity_id AND wsm.is_active = true
        LEFT JOIN sh_workspaces ws
            ON ws.id = wsm.workspace_id AND ws.status = 'active'
            AND (om.organization_id IS NULL
                 OR ws.organization_id = om.organization_id)
        WHERE o.object_id IS NULL
    """))
    orphan_count = conn.execute(sa.text(
        "SELECT count(*) FROM founder_conversations fc "
        "LEFT JOIN sh_objects o ON o.object_id = fc.object_id "
        "WHERE o.object_id IS NULL"
    )).scalar()
    assert orphan_count == 0, (
        f"{orphan_count} orphan founder_conversations remain — migration is blocked"
    )

    # ── Step 2: Drop old FK (founder_conversations → founder_objects) ──
    # PostgreSQL names the FK constraint automatically from the model
    # definition. We use the standard naming convention.
    conn.execute(sa.text(
        "ALTER TABLE founder_conversations "
        "DROP CONSTRAINT IF EXISTS founder_conversations_object_id_fkey"
    ))

    # ── Step 3: Add new FK (founder_conversations → sh_objects) ──
    conn.execute(sa.text(
        "ALTER TABLE founder_conversations "
        "ADD CONSTRAINT founder_conversations_object_id_fkey "
        "FOREIGN KEY (object_id) REFERENCES sh_objects(object_id)"
    ))

    # ── Verification ──
    fk_target = conn.execute(sa.text(
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE conrelid = 'founder_conversations'::regclass "
        "AND contype = 'f'"
    )).scalar()
    assert fk_target and "sh_objects" in fk_target, (
        f"FK target is NOT sh_objects after migration: {fk_target}"
    )


def downgrade() -> None:
    conn = op.get_bind()
    # Restore old FK
    conn.execute(sa.text(
        "ALTER TABLE founder_conversations "
        "DROP CONSTRAINT IF EXISTS founder_conversations_object_id_fkey"
    ))
    conn.execute(sa.text(
        "ALTER TABLE founder_conversations "
        "ADD CONSTRAINT founder_conversations_object_id_fkey "
        "FOREIGN KEY (object_id) REFERENCES founder_objects(object_id)"
    ))
    # Don't delete the backfilled sh_objects rows — they're now part of the
    # canonical store. The FK can point to either table.