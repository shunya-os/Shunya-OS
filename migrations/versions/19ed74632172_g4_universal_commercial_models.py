"""G4 Universal Commercial models

Revision ID: 19ed74632172
Revises: 0011_purify_execution_model
Create Date: 2026-08-20 06:05:59.871516

WARNING: This manual migration REPLACES the auto-generated version.
Only creates the 5 G4 tables. No destructive operations.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '19ed74632172'
down_revision: Union[str, Sequence[str], None] = '0011_purify_execution_model'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create G4 commercial tables only."""

    # ── g4_opportunities ────────────────────────────────────────────
    op.create_table(
        'g4_opportunities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('relationship_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('opportunity_type', sa.String(length=60), nullable=True, server_default='opportunity'),
        sa.Column('lifecycle_state', sa.String(length=40), nullable=False, server_default='discovered'),
        sa.Column('previous_state', sa.String(length=40), nullable=True, server_default=''),
        sa.Column('state_changed_at', sa.DateTime(), nullable=True),
        sa.Column('state_change_reason', sa.Text(), nullable=True, server_default=''),
        sa.Column('estimated_value', sa.Numeric(15, 2), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True, server_default=''),
        sa.Column('confidence', sa.Integer(), nullable=True, server_default='50'),
        sa.Column('urgency', sa.Integer(), nullable=True, server_default='50'),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('source', sa.String(length=255), nullable=True, server_default=''),
        sa.Column('source_reference', sa.String(length=255), nullable=True, server_default=''),
        sa.Column('owner_identity_id', sa.String(length=64), nullable=True, server_default=''),
        sa.Column('next_action', sa.Text(), nullable=True, server_default=''),
        sa.Column('next_action_due_at', sa.DateTime(), nullable=True),
        sa.Column('risks', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('evidence', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('custom_attributes', sa.Text(), nullable=True, server_default='{}'),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('conversation_ref', sa.String(length=255), nullable=True, server_default=''),
        sa.Column('created_by', sa.String(length=64), nullable=True, server_default=''),
        sa.Column('updated_by', sa.String(length=64), nullable=True, server_default=''),
        sa.Column('lifecycle_history', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['relationship_id'], ['rel_relationships.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_g4_opp_org', 'g4_opportunities', ['organization_id'])
    op.create_index('ix_g4_opp_rel', 'g4_opportunities', ['relationship_id'])
    op.create_index('ix_g4_opp_state', 'g4_opportunities', ['organization_id', 'lifecycle_state'])
    op.create_index('ix_g4_opp_owner', 'g4_opportunities', ['owner_identity_id'])
    op.create_index('ix_g4_opportunities_campaign_id', 'g4_opportunities', ['campaign_id'])

    # ── g4_contexts ─────────────────────────────────────────────────
    op.create_table(
        'g4_contexts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('relationship_id', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True, server_default=''),
        sa.Column('active_opportunity_id', sa.Integer(), nullable=True),
        sa.Column('engagement_level', sa.Integer(), nullable=True, server_default='50'),
        sa.Column('relationship_health', sa.Integer(), nullable=True, server_default='50'),
        sa.Column('lifetime_value_estimate', sa.Numeric(15, 2), nullable=True, server_default='0'),
        sa.Column('retention_risk', sa.Integer(), nullable=True, server_default='50'),
        sa.Column('suggested_next_action', sa.Text(), nullable=True, server_default=''),
        sa.Column('suggested_action_reason', sa.Text(), nullable=True, server_default=''),
        sa.Column('suggested_at', sa.DateTime(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('signals_json', sa.Text(), nullable=True, server_default='{}'),
        sa.Column('last_interaction_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['relationship_id'], ['rel_relationships.id'], ),
        sa.ForeignKeyConstraint(['active_opportunity_id'], ['g4_opportunities.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('relationship_id', name='uq_g4_ctx_rel'),
    )
    op.create_index('ix_g4_ctx_org', 'g4_contexts', ['organization_id'])
    op.create_index('ix_g4_ctx_rel', 'g4_contexts', ['relationship_id'], unique=True)

    # ── g4_proposals ────────────────────────────────────────────────
    op.create_table(
        'g4_proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('relationship_id', sa.Integer(), nullable=True),
        sa.Column('opportunity_id', sa.Integer(), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='draft'),
        sa.Column('proposal_type', sa.String(length=60), nullable=True, server_default='proposal'),
        sa.Column('scope_description', sa.Text(), nullable=True, server_default=''),
        sa.Column('assumptions', sa.Text(), nullable=True, server_default=''),
        sa.Column('exclusions', sa.Text(), nullable=True, server_default=''),
        sa.Column('currency', sa.String(length=10), nullable=True, server_default='INR'),
        sa.Column('subtotal', sa.Numeric(15, 2), nullable=True, server_default='0'),
        sa.Column('tax_amount', sa.Numeric(15, 2), nullable=True, server_default='0'),
        sa.Column('discount_amount', sa.Numeric(15, 2), nullable=True, server_default='0'),
        sa.Column('total_value', sa.Numeric(15, 2), nullable=True, server_default='0'),
        sa.Column('pricing_structure', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('delivery_timeline', sa.Text(), nullable=True, server_default=''),
        sa.Column('terms', sa.Text(), nullable=True, server_default=''),
        sa.Column('conditions', sa.Text(), nullable=True, server_default=''),
        sa.Column('decisions_required', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('source_context', sa.Text(), nullable=True, server_default=''),
        sa.Column('ai_generated', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('ai_model', sa.String(length=100), nullable=True, server_default=''),
        sa.Column('ai_prompt', sa.Text(), nullable=True, server_default=''),
        sa.Column('evidence_refs', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('rendered_html', sa.Text(), nullable=True, server_default=''),
        sa.Column('rendered_pdf_path', sa.String(length=500), nullable=True, server_default=''),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('sent_via', sa.String(length=30), nullable=True, server_default=''),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('decision_id', sa.String(length=64), nullable=True),
        sa.Column('commitment_id', sa.String(length=64), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True, server_default=''),
        sa.Column('created_by', sa.String(length=64), nullable=True, server_default=''),
        sa.Column('updated_by', sa.String(length=64), nullable=True, server_default=''),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['relationship_id'], ['rel_relationships.id'], ),
        sa.ForeignKeyConstraint(['opportunity_id'], ['g4_opportunities.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_g4_prop_org', 'g4_proposals', ['organization_id'])
    op.create_index('ix_g4_prop_opp', 'g4_proposals', ['opportunity_id'])
    op.create_index('ix_g4_prop_status', 'g4_proposals', ['status'])

    # ── g4_transitions ──────────────────────────────────────────────
    op.create_table(
        'g4_transitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=30), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('from_state', sa.String(length=40), nullable=False),
        sa.Column('to_state', sa.String(length=40), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True, server_default=''),
        sa.Column('is_correction', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('correction_reason', sa.Text(), nullable=True, server_default=''),
        sa.Column('triggered_by', sa.String(length=64), nullable=True, server_default=''),
        sa.Column('transitioned_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_g4_tr_entity', 'g4_transitions', ['organization_id', 'entity_type', 'entity_id'])
    op.create_index('ix_g4_tr_time', 'g4_transitions', ['organization_id', 'transitioned_at'])
    op.create_index('ix_g4_transitions_entity_id', 'g4_transitions', ['entity_id'])

    # ── g4_types ────────────────────────────────────────────────────
    op.create_table(
        'g4_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('domain', sa.String(length=30), nullable=False),
        sa.Column('type_key', sa.String(length=60), nullable=False),
        sa.Column('display_label', sa.String(length=255), nullable=False),
        sa.Column('icon', sa.String(length=60), nullable=True, server_default='trending-up'),
        sa.Column('color', sa.String(length=20), nullable=True, server_default='#6366f1'),
        sa.Column('is_default', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_system', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_g4_type_org', 'g4_types', ['organization_id'])
    op.create_index('ix_g4_type_org_key', 'g4_types', ['organization_id', 'type_key'], unique=True)


def downgrade() -> None:
    """Remove G4 tables."""
    op.drop_table('g4_transitions')
    op.drop_table('g4_proposals')
    op.drop_table('g4_contexts')
    op.drop_table('g4_opportunities')
    op.drop_table('g4_types')