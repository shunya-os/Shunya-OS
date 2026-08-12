"""FDA12-15: Campaign, Audience, Content, Experiment + Customer/Lead/Commitment extensions.

Idempotent migration — checks for existing tables/columns before creating.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_fda12_15_marketing_sales"
down_revision = "0005_fda4_identity_schema"
branch_labels = None
depends_on = None


def _table_exists(conn, name):
    r = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name=:n)"
    ), {"n": name}).fetchone()
    return r[0] if r else False


def _column_exists(conn, table, column):
    r = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name=:t AND column_name=:c"
    ), {"t": table, "c": column}).fetchone()
    return r is not None


def upgrade():
    conn = op.get_bind()

    if not _table_exists(conn, "campaigns"):
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

    if not _table_exists(conn, "audience_definitions"):
        op.create_table(
            "audience_definitions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), nullable=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), server_default=""),
            sa.Column("criteria_json", sa.Text(), server_default=sa.text("'{}'")),
            sa.Column("source", sa.String(60), server_default=sa.text("'manual'")),
            sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    if not _table_exists(conn, "campaign_contents"):
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

    if not _table_exists(conn, "experiments"):
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

    # Extend leads
    for col in ("tenant_id", "campaign_id", "utm_source", "utm_campaign", "utm_medium", "utm_term", "utm_content"):
        if not _column_exists(conn, "leads", col):
            if col == "tenant_id":
                op.add_column("leads", sa.Column("tenant_id", sa.Integer(), nullable=True, index=True))
            elif col == "campaign_id":
                op.add_column("leads", sa.Column("campaign_id", sa.Integer(), nullable=True))
            else:
                op.add_column("leads", sa.Column(col, sa.String(255), nullable=True, server_default=""))

    # Extend customer
    for col in ("relationship_id", "lead_id", "tenant_id", "status", "created_at", "updated_at"):
        if not _column_exists(conn, "customer", col):
            if col == "relationship_id":
                op.add_column("customer", sa.Column("relationship_id", sa.Integer(), nullable=True))
            elif col == "lead_id":
                op.add_column("customer", sa.Column("lead_id", sa.Integer(), nullable=True))
            elif col == "tenant_id":
                op.add_column("customer", sa.Column("tenant_id", sa.Integer(), nullable=True))
            elif col == "status":
                op.add_column("customer", sa.Column("status", sa.String(30),
                                                    server_default=sa.text("'active'")))
            elif col == "created_at":
                op.add_column("customer", sa.Column("created_at", sa.DateTime(), nullable=True))
            elif col == "updated_at":
                op.add_column("customer", sa.Column("updated_at", sa.DateTime(), nullable=True))

    # Extend commitments
    for col in ("relationship_id", "campaign_id", "issue_type"):
        if not _column_exists(conn, "commitments", col):
            if col == "relationship_id":
                op.add_column("commitments", sa.Column("relationship_id", sa.Integer(), nullable=True))
            elif col == "campaign_id":
                op.add_column("commitments", sa.Column("campaign_id", sa.Integer(), nullable=True))
            elif col == "issue_type":
                op.add_column("commitments", sa.Column("issue_type", sa.String(60),
                                                       nullable=True, server_default=""))

    # Extend rel_timeline
    for col in ("campaign_id", "source_event"):
        if not _column_exists(conn, "rel_timeline", col):
            if col == "campaign_id":
                op.add_column("rel_timeline", sa.Column("campaign_id", sa.Integer(), nullable=True))
            elif col == "source_event":
                op.add_column("rel_timeline", sa.Column("source_event", sa.String(255),
                                                        nullable=True, server_default=""))

    # Indexes (create if not exists)
    for idx, table, col in (
        ("ix_leads_campaign", "leads", "campaign_id"),
        ("ix_customer_relationship", "customer", "relationship_id"),
        ("ix_commitments_relationship", "commitments", "relationship_id"),
        ("ix_commitments_campaign", "commitments", "campaign_id"),
        ("ix_rel_timeline_campaign", "rel_timeline", "campaign_id"),
    ):
        if _column_exists(conn, table, col):
            try:
                op.create_index(idx, table, [col])
            except Exception:
                pass  # index already exists


def downgrade():
    for idx in ("ix_rel_timeline_campaign", "ix_commitments_campaign",
                "ix_commitments_relationship", "ix_customer_relationship",
                "ix_leads_campaign"):
        try:
            op.drop_index(idx)
        except Exception:
            pass

    for col in ("source_event", "campaign_id"):
        try:
            op.drop_column("rel_timeline", col)
        except Exception:
            pass
    for col in ("issue_type", "campaign_id", "relationship_id"):
        try:
            op.drop_column("commitments", col)
        except Exception:
            pass
    for col in ("updated_at", "created_at", "status", "tenant_id", "lead_id", "relationship_id"):
        try:
            op.drop_column("customer", col)
        except Exception:
            pass
    for col in ("utm_content", "utm_term", "utm_medium", "utm_campaign", "utm_source", "campaign_id", "tenant_id"):
        try:
            op.drop_column("leads", col)
        except Exception:
            pass

    for table in ("experiments", "campaign_contents", "audience_definitions", "campaigns"):
        try:
            op.drop_table(table)
        except Exception:
            pass