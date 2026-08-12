"""FDA12-15: Campaign, Audience, Content, Experiment + Customer/Lead/Commitment extensions.

Creates the new models and extends existing owners with campaign/UTM/commitment fields.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_fda12_15_marketing_sales"
down_revision = "0005_fda4_identity_schema"
branch_labels = None
depends_on = None


def upgrade():
    # ── campaigns ──
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("objective", sa.String(80), server_default=sa.text("'awareness'")),
        sa.Column("owner", sa.String(120), nullable=True),
        sa.Column("status", sa.String(30), server_default=sa.text("'draft'")),
        sa.Column("budget", sa.Numeric(12, 2), server_default=sa.text("'0'")),
        sa.Column("budget_type", sa.String(20), server_default=sa.text("'total'")),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("utm_source", sa.String(255), server_default=""),
        sa.Column("utm_campaign", sa.String(255), server_default=""),
        sa.Column("utm_medium", sa.String(255), server_default=""),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("created_by", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── audience_definitions ──
    op.create_table(
        "audience_definitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("criteria_json", sa.Text(), server_default="'{}'"),
        sa.Column("source", sa.String(60), server_default=sa.text("'manual'")),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── campaign_contents ──
    op.create_table(
        "campaign_contents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(60), server_default=sa.text("'post'")),
        sa.Column("body", sa.Text(), server_default=""),
        sa.Column("status", sa.String(30), server_default=sa.text("'draft'")),
        sa.Column("asset_url", sa.String(500), server_default=""),
        sa.Column("owner", sa.String(120), nullable=True),
        sa.Column("approval_commitment_id", sa.Integer(), nullable=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── experiments ──
    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hypothesis", sa.Text(), server_default=""),
        sa.Column("variant", sa.String(60), server_default=sa.text("'A'")),
        sa.Column("status", sa.String(30), server_default=sa.text("'planned'")),
        sa.Column("metric", sa.String(60), server_default=sa.text("'conversion'")),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── Extend leads with campaign fields ──
    op.add_column("leads", sa.Column("campaign_id", sa.Integer(),
                  sa.ForeignKey("campaigns.id"), nullable=True))
    op.add_column("leads", sa.Column("utm_source", sa.String(255), nullable=True,
                  server_default=""))
    op.add_column("leads", sa.Column("utm_campaign", sa.String(255), nullable=True,
                  server_default=""))
    op.add_column("leads", sa.Column("utm_medium", sa.String(255), nullable=True,
                  server_default=""))
    op.add_column("leads", sa.Column("utm_term", sa.String(255), nullable=True,
                  server_default=""))
    op.add_column("leads", sa.Column("utm_content", sa.String(255), nullable=True,
                  server_default=""))

    # ── Extend customer with FDA13 fields ──
    op.add_column("customer", sa.Column("relationship_id", sa.Integer(),
                  sa.ForeignKey("rel_relationships.id"), nullable=True))
    op.add_column("customer", sa.Column("lead_id", sa.Integer(),
                  sa.ForeignKey("leads.id"), nullable=True))
    op.add_column("customer", sa.Column("tenant_id", sa.Integer(),
                  sa.ForeignKey("tenants.id"), nullable=True))
    op.add_column("customer", sa.Column("status", sa.String(30),
                  server_default=sa.text("'active'")))
    op.add_column("customer", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("customer", sa.Column("updated_at", sa.DateTime(), nullable=True))

    # ── Extend commitments with FDA13 fields ──
    op.add_column("commitments", sa.Column("relationship_id", sa.Integer(),
                  sa.ForeignKey("rel_relationships.id"), nullable=True))
    op.add_column("commitments", sa.Column("campaign_id", sa.Integer(),
                  sa.ForeignKey("campaigns.id"), nullable=True))
    op.add_column("commitments", sa.Column("issue_type", sa.String(60), nullable=True,
                  server_default=""))

    # ── Extend rel_timeline with FDA15 fields ──
    op.add_column("rel_timeline", sa.Column("campaign_id", sa.Integer(),
                  sa.ForeignKey("campaigns.id"), nullable=True))
    op.add_column("rel_timeline", sa.Column("source_event", sa.String(255),
                  nullable=True, server_default=""))

    # ── Indexes ──
    op.create_index("ix_leads_campaign", "leads", ["campaign_id"])
    op.create_index("ix_customer_relationship", "customer", ["relationship_id"])
    op.create_index("ix_commitments_relationship", "commitments", ["relationship_id"])
    op.create_index("ix_commitments_campaign", "commitments", ["campaign_id"])
    op.create_index("ix_rel_timeline_campaign", "rel_timeline", ["campaign_id"])


def downgrade():
    op.drop_index("ix_rel_timeline_campaign", table_name="rel_timeline")
    op.drop_index("ix_commitments_campaign", table_name="commitments")
    op.drop_index("ix_commitments_relationship", table_name="commitments")
    op.drop_index("ix_customer_relationship", table_name="customer")
    op.drop_index("ix_leads_campaign", table_name="leads")

    op.drop_column("rel_timeline", "source_event")
    op.drop_column("rel_timeline", "campaign_id")
    op.drop_column("commitments", "issue_type")
    op.drop_column("commitments", "campaign_id")
    op.drop_column("commitments", "relationship_id")
    op.drop_column("customer", "updated_at")
    op.drop_column("customer", "created_at")
    op.drop_column("customer", "status")
    op.drop_column("customer", "tenant_id")
    op.drop_column("customer", "lead_id")
    op.drop_column("customer", "relationship_id")
    op.drop_column("leads", "utm_content")
    op.drop_column("leads", "utm_term")
    op.drop_column("leads", "utm_medium")
    op.drop_column("leads", "utm_campaign")
    op.drop_column("leads", "utm_source")
    op.drop_column("leads", "campaign_id")

    op.drop_table("experiments")
    op.drop_table("campaign_contents")
    op.drop_table("audience_definitions")
    op.drop_table("campaigns")