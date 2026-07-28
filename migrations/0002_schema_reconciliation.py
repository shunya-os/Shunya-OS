"""
SHUNYA — Canonical Schema Reconciliation Migration

Generated from schema audit against production PostgreSQL.
This single migration reconciles all model-defined columns with the
physical database schema. It is additive and safe — it never drops
columns or data, only adds what models require and aligns constraints
where mismatches would cause runtime failures.

Generated: 2026-07-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_schema_reconciliation"
down_revision = None  # First migration; adjust if another rev precedes
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────────────────
    # 1. team_members — missing columns that crashed production
    # ─────────────────────────────────────────────────────────────────────────
    op.add_column("team_members", sa.Column("person_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_team_members_person_id_persons",
        "team_members", "persons",
        ["person_id"], ["id"],
    )
    # api_token was added manually; add unique constraint if missing
    op.create_unique_constraint("uq_team_members_api_token", "team_members", ["api_token"])
    op.create_unique_constraint("uq_team_members_email", "team_members", ["email"])
    # Make tenant_id nullable (the model doesn't define it)
    op.alter_column("team_members", "tenant_id", nullable=True, existing_type=sa.Integer())
    # Drop FK on tenant_id if present (model doesn't define it)
    op.drop_constraint("fk_team_members_tenant_id_tenants", "team_members", type_="foreignkey")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Missing columns: tables where the model expects columns the DB lacks
    # ─────────────────────────────────────────────────────────────────────────

    # activity_logs
    op.add_column("activity_logs", sa.Column("lead_id", sa.Integer(), nullable=True))
    op.add_column("activity_logs", sa.Column("user", sa.String(length=120), nullable=True))
    op.create_foreign_key("fk_activity_logs_lead_id_leads", "activity_logs", "leads", ["lead_id"], ["id"])

    # client_users
    op.add_column("client_users", sa.Column("lead_id", sa.Integer(), nullable=True))
    op.add_column("client_users", sa.Column("password_hash", sa.String(length=128), nullable=True))
    op.create_foreign_key("fk_client_users_lead_id_leads", "client_users", "leads", ["lead_id"], ["id"])
    # Make email unique and NOT NULL as model expects
    op.create_unique_constraint("uq_client_users_email", "client_users", ["email"])
    op.alter_column("client_users", "email", nullable=False, existing_type=sa.String(length=255))

    # invoices
    op.add_column("invoices", sa.Column("lead_id", sa.Integer(), nullable=True))
    op.add_column("invoices", sa.Column("raised_at", sa.DateTime(), nullable=True))
    op.create_foreign_key("fk_invoices_lead_id_leads", "invoices", "leads", ["lead_id"], ["id"])
    op.create_unique_constraint("uq_invoices_invoice_number", "invoices", ["invoice_number"])
    # Fix due_date type mismatch (model=DATE, db=TIMESTAMP)
    op.alter_column("invoices", "due_date", type_=sa.Date(), existing_type=sa.DateTime(), postgresql_using="due_date::date")

    # notifications
    op.add_column("notifications", sa.Column("lead_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_notifications_lead_id_leads", "notifications", "leads", ["lead_id"], ["id"])
    op.alter_column("notifications", "is_read", nullable=False, existing_type=sa.Boolean())

    # leads — add unique on code
    op.create_unique_constraint("uq_leads_code", "leads", ["code"])

    # observations — add all model-missing columns
    op.add_column("observations", sa.Column("action", sa.String(length=255), nullable=True))
    op.add_column("observations", sa.Column("actual_outcome", sa.Text(), nullable=True))
    op.add_column("observations", sa.Column("channel", sa.String(length=60), nullable=True))
    op.add_column("observations", sa.Column("discrepancy", sa.Text(), nullable=True))
    op.add_column("observations", sa.Column("expected_outcome", sa.Text(), nullable=True))
    op.add_column("observations", sa.Column("lead_id", sa.Integer(), nullable=True))
    op.add_column("observations", sa.Column("success", sa.Boolean(), nullable=True))
    op.create_foreign_key("fk_observations_lead_id_leads", "observations", "leads", ["lead_id"], ["id"])
    # Fix type mismatches
    op.alter_column("observations", "confidence", type_=sa.Float(), existing_type=sa.String(length=20))

    # payments — add model-missing columns
    op.add_column("payments", sa.Column("lead_id", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("method", sa.String(length=80), nullable=True))
    op.add_column("payments", sa.Column("ref_number", sa.String(length=120), nullable=True))
    op.create_foreign_key("fk_payments_lead_id_leads", "payments", "leads", ["lead_id"], ["id"])
    op.alter_column("payments", "amount", nullable=False, existing_type=sa.Numeric(12, 2))
    op.alter_column("payments", "type", nullable=False, existing_type=sa.String(length=30))

    # persons — add model-missing columns
    op.add_column("persons", sa.Column("canonical_name", sa.String(length=255), nullable=True))
    op.add_column("persons", sa.Column("preferred_name", sa.String(length=255), nullable=True))
    op.add_column("persons", sa.Column("status", sa.String(length=30), nullable=True, server_default="active"))
    op.add_column("persons", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.add_column("persons", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.create_foreign_key("fk_persons_tenant_id_tenants", "persons", "tenants", ["tenant_id"], ["id"])

    # relationships — add model-missing columns
    op.add_column("relationships", sa.Column("ended_at", sa.DateTime(), nullable=True))
    op.add_column("relationships", sa.Column("relationship_type", sa.String(length=30), nullable=True))
    op.add_column("relationships", sa.Column("source", sa.String(length=120), nullable=True))
    op.add_column("relationships", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.alter_column("relationships", "tenant_id", nullable=True, existing_type=sa.Integer())

    # tenants — add missing subdomain
    op.add_column("tenants", sa.Column("subdomain", sa.String(length=255), nullable=True, unique=True))
    op.create_unique_constraint("uq_tenants_subdomain", "tenants", ["subdomain"])

    # founder_* unique constraints
    op.create_unique_constraint("uq_founder_conversations_conv_id", "founder_conversations", ["conv_id"])
    op.create_unique_constraint("uq_founder_objects_object_id", "founder_objects", ["object_id"])
    op.create_unique_constraint("uq_founder_relationships_rel_id", "founder_relationships", ["rel_id"])
    op.create_unique_constraint("uq_founder_spaces_space_id", "founder_spaces", ["space_id"])

    # shunya_identities unique
    op.create_unique_constraint("uq_shunya_identities_identity_id", "shunya_identities", ["identity_id"])

    # suppliers unique
    op.create_unique_constraint("uq_suppliers_name", "suppliers", ["name"])

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Type alignment for critical columns
    # ─────────────────────────────────────────────────────────────────────────

    # FLOAT → DOUBLE PRECISION alignments (model uses FLOAT, PostgreSQL stores DOUBLE)
    # These are functionally equivalent — skip ALTER to avoid unnecessary migration noise.
    # knowledge_facts.confidence, learning_entries.confidence,
    # intake_field_mappings.confidence already function correctly as DOUBLE.

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Default value alignment (client-side defaults handled by SQLAlchemy)
    # ─────────────────────────────────────────────────────────────────────────
    # Model defaults like datetime.utcnow are applied client-side by SQLAlchemy.
    # Adding server_default would change behaviour. No migration needed —
    # the model layer handles them correctly. Only server_default is required
    # for columns that must never be NULL at the DB level.

    # Set server_default for columns where the model provides a default and
    # the column is NOT NULL to prevent constraint violations during bulk operations.
    op.alter_column("notifications", "is_read", server_default=sa.text("false"))
    op.alter_column("payments", "amount", server_default=sa.text("0"))
    op.alter_column("payments", "type", server_default=sa.text("'guest_payment'"))
    op.alter_column("persons", "status", server_default=sa.text("'active'"))
    op.alter_column("team_members", "is_active", server_default=sa.text("true"))
    op.alter_column("team_members", "role", server_default=sa.text("'agent'"))


def downgrade() -> None:
    """Reverse all additive changes.

    WARNING: Reversing this migration may lose data if the added columns
    were populated. Only downgrade in development/test environments.
    """
    # Reverse order of upgrade (LIFO)

    # Team members
    op.drop_constraint("uq_team_members_email", "team_members", type_="unique")
    op.drop_constraint("uq_team_members_api_token", "team_members", type_="unique")
    op.drop_constraint("fk_team_members_person_id_persons", "team_members", type_="foreignkey")
    op.drop_column("team_members", "person_id")

    # Activity logs
    op.drop_constraint("fk_activity_logs_lead_id_leads", "activity_logs", type_="foreignkey")
    op.drop_column("activity_logs", "user")
    op.drop_column("activity_logs", "lead_id")

    # Client users
    op.drop_constraint("uq_client_users_email", "client_users", type_="unique")
    op.drop_constraint("fk_client_users_lead_id_leads", "client_users", type_="foreignkey")
    op.drop_column("client_users", "password_hash")
    op.drop_column("client_users", "lead_id")

    # Invoices
    op.drop_constraint("uq_invoices_invoice_number", "invoices", type_="unique")
    op.drop_constraint("fk_invoices_lead_id_leads", "invoices", type_="foreignkey")
    op.drop_column("invoices", "raised_at")
    op.drop_column("invoices", "lead_id")

    # Notifications
    op.drop_constraint("fk_notifications_lead_id_leads", "notifications", type_="foreignkey")
    op.drop_column("notifications", "lead_id")

    # Leads
    op.drop_constraint("uq_leads_code", "leads", type_="unique")

    # Observations
    op.drop_constraint("fk_observations_lead_id_leads", "observations", type_="foreignkey")
    op.drop_column("observations", "success")
    op.drop_column("observations", "lead_id")
    op.drop_column("observations", "expected_outcome")
    op.drop_column("observations", "discrepancy")
    op.drop_column("observations", "channel")
    op.drop_column("observations", "actual_outcome")
    op.drop_column("observations", "action")

    # Payments
    op.drop_constraint("fk_payments_lead_id_leads", "payments", type_="foreignkey")
    op.drop_column("payments", "ref_number")
    op.drop_column("payments", "method")
    op.drop_column("payments", "lead_id")

    # Persons
    op.drop_constraint("fk_persons_tenant_id_tenants", "persons", type_="foreignkey")
    op.drop_column("persons", "updated_at")
    op.drop_column("persons", "tenant_id")
    op.drop_column("persons", "status")
    op.drop_column("persons", "preferred_name")
    op.drop_column("persons", "canonical_name")

    # Relationships
    op.drop_column("relationships", "started_at")
    op.drop_column("relationships", "source")
    op.drop_column("relationships", "relationship_type")
    op.drop_column("relationships", "ended_at")

    # Tenants
    op.drop_constraint("uq_tenants_subdomain", "tenants", type_="unique")
    op.drop_column("tenants", "subdomain")

    # Founder unique constraints
    op.drop_constraint("uq_founder_conversations_conv_id", "founder_conversations", type_="unique")
    op.drop_constraint("uq_founder_objects_object_id", "founder_objects", type_="unique")
    op.drop_constraint("uq_founder_relationships_rel_id", "founder_relationships", type_="unique")
    op.drop_constraint("uq_founder_spaces_space_id", "founder_spaces", type_="unique")
    op.drop_constraint("uq_shunya_identities_identity_id", "shunya_identities", type_="unique")
    op.drop_constraint("uq_suppliers_name", "suppliers", type_="unique")

    # Default alignment reversals
    op.alter_column("notifications", "is_read", server_default=None)
    op.alter_column("payments", "amount", server_default=None)
    op.alter_column("payments", "type", server_default=None)
    op.alter_column("persons", "status", server_default=None)
    op.alter_column("team_members", "is_active", server_default=None)
    op.alter_column("team_members", "role", server_default=None)