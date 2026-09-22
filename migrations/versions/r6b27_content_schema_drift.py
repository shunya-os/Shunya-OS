"""R6B-2.9 — Content & Media schema drift: lifecycle/tenant columns never migrated.

WHY
---
A cross-table drift scan of all 164 model tables against the live production
PostgreSQL database on 2026-09-22 found 3 tables where the SQLAlchemy model
declares columns that NO migration in the Alembic chain ever created:

  m6_content_generations  (15 columns) — ContentGeneration.model
  m6_media_assets          (7 columns) — MediaAsset.model
  message_proposals        (7 columns) — MessageProposal.model

The columns actively used in production code paths:

  content_studio/routes.py:          lifecycle_status, archived_at, archived_by,
                                     deleted_at, deleted_by, restored_at,
                                     restored_by, organization_id, workspace_id
  integration/gmail_ingest.py:       entity_id, entity_type, entity_name
  intelligence/decision_engine.py:   context_reason, context_priority,
                                     context_source, context_confidence

Without these columns, every create/archive/trash/restore operation on content
generations and every message proposal write hits UndefinedColumn — the same
defect class as r6b27_content_lifecycle and r6b27_supplier_drift.

The 0010_schema_reconciliation migration (which declares message_proposals
entity/context columns) lives on an unmerged branch and was never applied.

Idempotent: every step is a no-op where the column/index already exists, and a
missing table is skipped, so the chain converges from any starting point.

Revision ID: r6b27_content_schema_drift
Revises: r6b27_supplier_drift
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "r6b27_content_schema_drift"
down_revision = "r6b27_supplier_drift"
branch_labels = None
depends_on = None


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    # =========================================================================
    # 1. m6_content_generations — ContentGeneration
    # =========================================================================
    # Tenant / ownership context
    op.add_column("m6_content_generations", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("m6_content_generations", sa.Column("workspace_id", sa.String(64), nullable=True))

    # Lifecycle columns
    op.add_column("m6_content_generations", sa.Column("lifecycle_status", sa.String(20),
                  nullable=False, server_default="active"))
    op.add_column("m6_content_generations", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column("m6_content_generations", sa.Column("deleted_by", sa.String(64), nullable=True))
    op.add_column("m6_content_generations", sa.Column("archived_at", sa.DateTime(), nullable=True))
    op.add_column("m6_content_generations", sa.Column("archived_by", sa.String(64), nullable=True))
    op.add_column("m6_content_generations", sa.Column("restored_at", sa.DateTime(), nullable=True))
    op.add_column("m6_content_generations", sa.Column("restored_by", sa.String(64), nullable=True))

    # Provenance / metadata
    op.add_column("m6_content_generations", sa.Column("provider", sa.String(60), nullable=True))
    op.add_column("m6_content_generations", sa.Column("generation_cost", sa.Float(), nullable=True))
    op.add_column("m6_content_generations", sa.Column("generation_metadata", postgresql.JSONB(), nullable=True))
    op.add_column("m6_content_generations", sa.Column("provenance", sa.String(120), nullable=True))
    op.add_column("m6_content_generations", sa.Column("source", sa.String(120), nullable=True))

    # Updated timestamp
    op.add_column("m6_content_generations", sa.Column("updated_at", sa.DateTime(), nullable=True))

    print("  m6_content_generations: 15 lifecycle/tenant/provenance columns ensured")

    # =========================================================================
    # 2. m6_media_assets — MediaAsset
    # =========================================================================
    op.add_column("m6_media_assets", sa.Column("lifecycle_status", sa.String(20),
                  nullable=False, server_default="active"))
    op.add_column("m6_media_assets", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column("m6_media_assets", sa.Column("deleted_by", sa.String(64), nullable=True))
    op.add_column("m6_media_assets", sa.Column("archived_at", sa.DateTime(), nullable=True))
    op.add_column("m6_media_assets", sa.Column("archived_by", sa.String(64), nullable=True))
    op.add_column("m6_media_assets", sa.Column("restored_at", sa.DateTime(), nullable=True))
    op.add_column("m6_media_assets", sa.Column("restored_by", sa.String(64), nullable=True))

    print("  m6_media_assets: 7 lifecycle columns ensured")

    # =========================================================================
    # 3. message_proposals — MessageProposal
    # =========================================================================
    op.add_column("message_proposals", sa.Column("entity_id", sa.Integer(), nullable=True))
    op.create_index("ix_message_proposals_entity_id", "message_proposals", ["entity_id"])
    op.add_column("message_proposals", sa.Column("entity_type", sa.String(64), nullable=True))
    op.add_column("message_proposals", sa.Column("entity_name", sa.String(128), nullable=True))
    op.add_column("message_proposals", sa.Column("context_reason", sa.Text(), nullable=True))
    op.add_column("message_proposals", sa.Column("context_priority", sa.String(16), nullable=True,
                  server_default="medium"))
    op.add_column("message_proposals", sa.Column("context_source", sa.String(64), nullable=True,
                  server_default="decision_engine"))
    op.add_column("message_proposals", sa.Column("context_confidence", sa.String(16), nullable=True,
                  server_default="high"))

    print("  message_proposals: 7 entity/context columns + index ensured")


def downgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()

    # m6_content_generations
    op.drop_column("m6_content_generations", "organization_id")
    op.drop_column("m6_content_generations", "workspace_id")
    op.drop_column("m6_content_generations", "lifecycle_status")
    op.drop_column("m6_content_generations", "deleted_at")
    op.drop_column("m6_content_generations", "deleted_by")
    op.drop_column("m6_content_generations", "archived_at")
    op.drop_column("m6_content_generations", "archived_by")
    op.drop_column("m6_content_generations", "restored_at")
    op.drop_column("m6_content_generations", "restored_by")
    op.drop_column("m6_content_generations", "provider")
    op.drop_column("m6_content_generations", "generation_cost")
    op.drop_column("m6_content_generations", "generation_metadata")
    op.drop_column("m6_content_generations", "provenance")
    op.drop_column("m6_content_generations", "source")
    op.drop_column("m6_content_generations", "updated_at")

    # m6_media_assets
    op.drop_column("m6_media_assets", "lifecycle_status")
    op.drop_column("m6_media_assets", "deleted_at")
    op.drop_column("m6_media_assets", "deleted_by")
    op.drop_column("m6_media_assets", "archived_at")
    op.drop_column("m6_media_assets", "archived_by")
    op.drop_column("m6_media_assets", "restored_at")
    op.drop_column("m6_media_assets", "restored_by")

    # message_proposals
    op.drop_index("ix_message_proposals_entity_id", table_name="message_proposals")
    op.drop_column("message_proposals", "entity_id")
    op.drop_column("message_proposals", "entity_type")
    op.drop_column("message_proposals", "entity_name")
    op.drop_column("message_proposals", "context_reason")
    op.drop_column("message_proposals", "context_priority")
    op.drop_column("message_proposals", "context_source")
    op.drop_column("message_proposals", "context_confidence")

    print("  r6b27_content_schema_drift rolled back")