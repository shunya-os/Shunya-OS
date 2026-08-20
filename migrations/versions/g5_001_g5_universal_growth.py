"""G5 — Universal Marketing, Growth, Attribution & Learning tables.

Creates canonical G5 tables:
- g5_campaign_events: Campaign lifecycle event stream
- g5_interactions: Multi-touch interaction records
- g5_attributions: Canonical attribution with confidence/evidence
- g5_learnings: Growth learning/insight grounded in actual outcomes

Revision ID: g5_001
Revises: 19ed74632172
Create Date: 2026-08-20
"""

from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Integer, String, Text, Numeric, Boolean, DateTime, Index


revision = "g5_001"
down_revision = "19ed74632172"
branch_labels = None
depends_on = None


def upgrade():
    # ── Campaign Events ──────────────────────────────────────────────
    op.create_table(
        "g5_campaign_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False, index=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("previous_state", sa.String(30), default=""),
        sa.Column("new_state", sa.String(30), default=""),
        sa.Column("description", sa.Text(), default=""),
        sa.Column("trigger_source", sa.String(60), default="system"),
        sa.Column("evidence_ref", sa.String(255), default=""),
        sa.Column("payload_json", sa.Text(), default="{}"),
        sa.Column("created_by", sa.String(64), default=""),
        sa.Column("occurred_at", sa.DateTime(),
                  default=lambda: datetime.now(timezone.utc), nullable=False),
        sa.Column("recorded_at", sa.DateTime(),
                  default=lambda: datetime.now(timezone.utc), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_g5_ce_campaign", "g5_campaign_events", ["campaign_id"])
    op.create_index("ix_g5_ce_time", "g5_campaign_events", ["campaign_id", "occurred_at"])
    op.create_index("ix_g5_ce_type", "g5_campaign_events", ["campaign_id", "event_type"])
    op.create_index("ix_g5_ce_tenant", "g5_campaign_events", ["tenant_id"])

    # ── Touchpoint Interactions ──────────────────────────────────────
    op.create_table(
        "g5_interactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=True, index=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("identity_ref", sa.String(255), default=""),
        sa.Column("person_name", sa.String(255), default=""),
        sa.Column("person_email", sa.String(255), default=""),
        sa.Column("relationship_id", sa.Integer(), nullable=True, index=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("interaction_type", sa.String(40), default="first_discovery"),
        sa.Column("description", sa.Text(), default=""),
        sa.Column("source", sa.String(255), default=""),
        sa.Column("channel", sa.String(255), default=""),
        sa.Column("referrer", sa.String(500), default=""),
        sa.Column("utm_source", sa.String(255), default=""),
        sa.Column("utm_medium", sa.String(255), default=""),
        sa.Column("utm_campaign", sa.String(255), default=""),
        sa.Column("utm_term", sa.String(255), default=""),
        sa.Column("utm_content", sa.String(255), default=""),
        sa.Column("session_ref", sa.String(255), default=""),
        sa.Column("tracking_id", sa.String(255), default=""),
        sa.Column("engagement_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("engagement_depth", sa.Integer(), default=0),
        sa.Column("content_ref", sa.String(500), default=""),
        sa.Column("evidence_json", sa.Text(), default="{}"),
        sa.Column("source_confidence", sa.Integer(), default=50),
        sa.Column("recorded_by", sa.String(64), default=""),
        sa.Column("occurred_at", sa.DateTime(),
                  default=lambda: datetime.now(timezone.utc), nullable=False),
        sa.Column("recorded_at", sa.DateTime(),
                  default=lambda: datetime.now(timezone.utc), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_g5_int_campaign", "g5_interactions", ["campaign_id"])
    op.create_index("ix_g5_int_identity", "g5_interactions", ["identity_ref"])
    op.create_index("ix_g5_int_relationship", "g5_interactions", ["relationship_id"])
    op.create_index("ix_g5_int_tenant", "g5_interactions", ["tenant_id"])
    op.create_index("ix_g5_int_type", "g5_interactions", ["campaign_id", "interaction_type"])
    op.create_index("ix_g5_int_time", "g5_interactions", ["identity_ref", "occurred_at"])

    # ── Canonical Attribution ────────────────────────────────────────
    op.create_table(
        "g5_attributions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=True, index=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False, index=True),
        sa.Column("target_description", sa.String(500), default=""),
        sa.Column("source", sa.String(255), default=""),
        sa.Column("source_ref", sa.String(255), default=""),
        sa.Column("channel", sa.String(255), default=""),
        sa.Column("content_ref", sa.String(500), default=""),
        sa.Column("utm_source", sa.String(255), default=""),
        sa.Column("utm_medium", sa.String(255), default=""),
        sa.Column("utm_campaign", sa.String(255), default=""),
        sa.Column("utm_term", sa.String(255), default=""),
        sa.Column("utm_content", sa.String(255), default=""),
        sa.Column("attribution_state", sa.String(30), default="unknown", nullable=False),
        sa.Column("confidence", sa.Integer(), default=50),
        sa.Column("evidence_summary", sa.Text(), default=""),
        sa.Column("identity_ref", sa.String(255), default=""),
        sa.Column("relationship_id", sa.Integer(), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("opportunity_id", sa.Integer(), nullable=True, index=True),
        sa.Column("proposal_id", sa.Integer(), nullable=True),
        sa.Column("outcome_id", sa.Integer(), nullable=True),
        sa.Column("revenue_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("is_revenue_outcome", sa.Boolean(), default=False),
        sa.Column("evidence_json", sa.Text(), default="{}"),
        sa.Column("interaction_id", sa.Integer(), nullable=True),
        sa.Column("is_first_known", sa.Boolean(), default=False),
        sa.Column("attribution_policy", sa.String(40), default="evidenced"),
        sa.Column("created_by", sa.String(64), default=""),
        sa.Column("attributed_at", sa.DateTime(),
                  default=lambda: datetime.now(timezone.utc), nullable=False),
        sa.Column("created_at", sa.DateTime(),
                  default=lambda: datetime.now(timezone.utc), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_g5_attr_campaign", "g5_attributions", ["campaign_id"])
    op.create_index("ix_g5_attr_source", "g5_attributions", ["source", "source_ref"])
    op.create_index("ix_g5_attr_target", "g5_attributions", ["target_type", "target_id"])
    op.create_index("ix_g5_attr_identity", "g5_attributions", ["identity_ref"])
    op.create_index("ix_g5_attr_tenant", "g5_attributions", ["tenant_id"])

    # ── Growth Learning ──────────────────────────────────────────────
    op.create_table(
        "g5_learnings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=True, index=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(40), default="campaign_performance"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("observation", sa.Text(), default=""),
        sa.Column("significance", sa.String(20), default="normal"),
        sa.Column("evidence_summary", sa.Text(), default=""),
        sa.Column("evidence_refs", sa.Text(), default="[]"),
        sa.Column("confidence", sa.Integer(), default=50),
        sa.Column("data_source", sa.String(60), default="shunya_internal"),
        sa.Column("attribution_id", sa.Integer(), nullable=True),
        sa.Column("interaction_id", sa.Integer(), nullable=True),
        sa.Column("outcome_id", sa.Integer(), nullable=True),
        sa.Column("opportunity_id", sa.Integer(), nullable=True),
        sa.Column("recommendation", sa.Text(), default=""),
        sa.Column("recommendation_confidence", sa.Integer(), default=50),
        sa.Column("recommendation_action", sa.String(255), default=""),
        sa.Column("is_actionable", sa.Boolean(), default=False),
        sa.Column("external_source", sa.String(255), default=""),
        sa.Column("external_retrieved_at", sa.DateTime(), nullable=True),
        sa.Column("external_context", sa.Text(), default=""),
        sa.Column("created_by", sa.String(64), default=""),
        sa.Column("observed_at", sa.DateTime(),
                  default=lambda: datetime.now(timezone.utc), nullable=False),
        sa.Column("created_at", sa.DateTime(),
                  default=lambda: datetime.now(timezone.utc), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_g5_lrn_campaign", "g5_learnings", ["campaign_id"])
    op.create_index("ix_g5_lrn_tenant", "g5_learnings", ["tenant_id"])
    op.create_index("ix_g5_lrn_category", "g5_learnings", ["campaign_id", "category"])
    op.create_index("ix_g5_lrn_time", "g5_learnings", ["tenant_id", "observed_at"])


def downgrade():
    op.drop_table("g5_learnings")
    op.drop_table("g5_attributions")
    op.drop_table("g5_interactions")
    op.drop_table("g5_campaign_events")