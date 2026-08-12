"""FDA22: create auth_service_accounts, auth_delegations, auth_tenant_policies

Revision ID: 0007_fda22_auth_extended
Revises: 0006_fda12_15_marketing_sales
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime


revision = "0007_fda22_auth_extended"
down_revision = "0006_fda12_15_marketing_sales"
branch_labels = None
depends_on = None


def upgrade():
    # auth_service_accounts
    op.create_table(
        "auth_service_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), default=""),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("token_prefix", sa.String(8), nullable=False),
        sa.Column("permissions", sa.Text(), default="[]"),
        sa.Column("allowed_scopes", sa.Text(), default='["organization"]'),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(64), default=""),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_sa_org", "auth_service_accounts", ["organization_id"])
    op.create_index("ix_sa_token", "auth_service_accounts", ["token_hash"], unique=True)
    op.create_index("ix_sa_name_org", "auth_service_accounts", ["organization_id", "name"], unique=True)

    # auth_delegations
    op.create_table(
        "auth_delegations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("delegator_id", sa.Integer(), sa.ForeignKey("org_members.id"), nullable=False),
        sa.Column("delegate_id", sa.Integer(), sa.ForeignKey("org_members.id"), nullable=False),
        sa.Column("permission_keys", sa.Text(), default="[]"),
        sa.Column("scope", sa.String(30), default="organization"),
        sa.Column("scope_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), default=""),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("valid_from", sa.DateTime(), default=datetime.utcnow),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("revoked_by", sa.String(64), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(64), default=""),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
    )
    op.create_index("ix_ad_org", "auth_delegations", ["organization_id"])
    op.create_index("ix_ad_delegator", "auth_delegations", ["delegator_id"])
    op.create_index("ix_ad_delegate", "auth_delegations", ["delegate_id"])

    # auth_tenant_policies
    op.create_table(
        "auth_tenant_policies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("policy_key", sa.String(120), nullable=False),
        sa.Column("policy_value", sa.Text(), nullable=False),
        sa.Column("policy_type", sa.String(30), default="string"),
        sa.Column("description", sa.Text(), default=""),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_by", sa.String(64), default=""),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
    )
    op.create_index("ix_tp_org_key", "auth_tenant_policies", ["organization_id", "policy_key"], unique=True)


def downgrade():
    op.drop_table("auth_tenant_policies")
    op.drop_table("auth_delegations")
    op.drop_table("auth_service_accounts")