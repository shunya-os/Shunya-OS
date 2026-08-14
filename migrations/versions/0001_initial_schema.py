"""SHUNYA — Initial Schema: All base tables from model definitions.

Immutable static migration. Creates all application tables plus
entity_definitions (production-only). Uses explicit op.create_table()
statements — no dynamic model reflection.

Subsequent migrations (0002+) reconcile/upgrade as model schemas evolve.

Created: 2026-08-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ── tenants ──
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(120), unique=True, nullable=False),
        sa.Column("business_type", sa.String(60), server_default=sa.text("'other'")),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("'true'")),
        sa.Column("plan", sa.String(50), nullable=True),
        sa.Column("max_team_members", sa.Integer(), nullable=True),
        sa.Column("max_storage_mb", sa.Integer(), nullable=True),
        sa.Column("max_ai_calls_daily", sa.Integer(), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("theme_config", postgresql.JSONB(), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), server_default=sa.text("'false'")),
        sa.Column("ai_config", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("brand_tagline", sa.String(255), server_default=""),
        sa.Column("brand_description", sa.Text(), server_default=""),
        sa.Column("brand_color", sa.String(50), server_default=sa.text("'#2563eb'")),
        sa.Column("brand_color_secondary", sa.String(50), server_default=sa.text("'#7c3aed'")),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("brand_id", sa.Integer(), nullable=True),
        sa.Column("business_id", sa.Integer(), nullable=True),
        sa.Column("vertical_config", postgresql.JSONB(), nullable=True),
        sa.Column("subdomain", sa.String(255), nullable=True),
        sa.Column("business_category", sa.String(100), server_default=""),
        sa.Column("company_email", sa.String(255), server_default=""),
        sa.Column("website", sa.String(255), server_default=""),
        sa.Column("phone", sa.String(50), server_default=""),
        sa.Column("industry", sa.String(100), server_default=""),
        sa.Column("country", sa.String(100), server_default=""),
        sa.Column("timezone", sa.String(50), server_default=sa.text("'UTC'")),
        sa.Column("currency", sa.String(10), server_default=sa.text("'USD'")),
        sa.Column("preferences", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── organizations ──
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── team_members ──
    op.create_table(
        "team_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("role", sa.String(30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("preferences", postgresql.JSONB(), nullable=True),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("secondary_phone", sa.String(50), nullable=True),
        sa.Column("whatsapp_phone", sa.String(50), nullable=True),
        sa.Column("whatsapp_verified", sa.Boolean(), server_default=sa.text("'false'")),
        sa.Column("api_token", sa.String(255), nullable=True),
        sa.Column("person_id", sa.Integer(), nullable=True),
        sa.Column("verified", sa.Boolean(), server_default=sa.text("'false'")),
        sa.Column("verify_token", sa.String(255), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), server_default=sa.text("'false'")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── leads ──
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(20), unique=True, nullable=False),
        sa.Column("source", sa.String(30), server_default=sa.text("'telegram'")),
        sa.Column("customer_name", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("destination", sa.String(255), nullable=True),
        sa.Column("pax", sa.String(100), nullable=True),
        sa.Column("dates", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("budget", sa.Numeric(12, 2), server_default=sa.text("'0'")),
        sa.Column("status", sa.String(30), server_default=sa.text("'new'")),
        sa.Column("assigned_to", sa.String(120), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("outcome", sa.String(255), nullable=True),
        sa.Column("stage", sa.String(50), server_default=sa.text("'new'")),
        sa.Column("person_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── proposals ──
    op.create_table(
        "proposals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version_number", sa.Integer(), server_default=sa.text("'1'")),
        sa.Column("status", sa.String(30), server_default=sa.text("'draft'")),
        sa.Column("title", sa.String(500), server_default=""),
        sa.Column("destination", sa.String(255), server_default=""),
        sa.Column("duration_days", sa.Integer(), server_default=sa.text("'0'")),
        sa.Column("pax", sa.String(100), server_default=""),
        sa.Column("budget", sa.Numeric(12, 2), server_default=sa.text("'0'")),
        sa.Column("currency", sa.String(10), server_default=sa.text("'INR'")),
        sa.Column("itinerary_json", sa.Text(), server_default=sa.text("'[]'")),
        sa.Column("pricing_json", sa.Text(), server_default=sa.text("'{}'")),
        sa.Column("inclusions", sa.Text(), server_default=""),
        sa.Column("exclusions", sa.Text(), server_default=""),
        sa.Column("terms", sa.Text(), server_default=""),
        sa.Column("brand_color", sa.String(50), server_default=""),
        sa.Column("brand_logo_url", sa.String(500), server_default=""),
        sa.Column("cover_image_url", sa.String(500), server_default=""),
        sa.Column("ai_generated", sa.Boolean(), server_default=sa.text("'false'")),
        sa.Column("ai_model", sa.String(100), server_default=""),
        sa.Column("ai_prompt", sa.Text(), server_default=""),
        sa.Column("generation_notes", sa.Text(), server_default=""),
        sa.Column("web_html", sa.Text(), server_default=""),
        sa.Column("web_url", sa.String(500), server_default=""),
        sa.Column("pdf_path", sa.String(500), server_default=""),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("sent_via", sa.String(50), server_default=""),
        sa.Column("viewed_at", sa.DateTime(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(255), server_default=""),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("opportunity_id", sa.Integer(), nullable=True),
        sa.Column("relationship_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )

    # ── task_lists ──
    op.create_table(
        "task_lists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── tasks ──
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_list_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assigned_to", sa.String(120), nullable=True),
        sa.Column("priority", sa.String(30), nullable=True),
        sa.Column("status", sa.String(30), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── persons ──
    op.create_table(
        "persons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("alternate_phone", sa.String(50), nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column("birthdate", sa.String(50), nullable=True),
        sa.Column("passport", sa.String(50), nullable=True),
        sa.Column("govt_id", sa.String(50), nullable=True),
        sa.Column("nationality", sa.String(100), nullable=True),
        sa.Column("preferred_language", sa.String(50), nullable=True),
        sa.Column("is_test", sa.Boolean(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column("canonical_name", sa.String(255), nullable=True),
        sa.Column("preferred_name", sa.String(255), nullable=True),
        sa.Column("status", sa.String(30), server_default=sa.text("'active'")),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("identity_type", sa.String(50), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── person_identities ──
    op.create_table(
        "person_identities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("identity_type", sa.String(32), nullable=False),
        sa.Column("identity_value", sa.String(255), nullable=False),
        sa.Column("normalized_value", sa.String(255), nullable=False),
        sa.Column("verification_state", sa.String(32), server_default=sa.text("'unverified'")),
        sa.Column("source", sa.String(60), nullable=True),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("confidence", sa.Float(), server_default=sa.text("'1.0'")),
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )

    # ── entities ──
    op.create_table(
        "entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("definition_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("data", postgresql.JSONB(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("code_prefix", sa.String(10), nullable=True),
        sa.Column("type", sa.String(50), nullable=True),
        sa.Column("state", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── entity_definitions ──
    op.create_table(
        "entity_definitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("label_plural", sa.String(255), nullable=True),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("schema", postgresql.JSONB(), nullable=True),
        sa.Column("statuses", postgresql.JSONB(), nullable=True),
        sa.Column("layout", sa.String(50), nullable=True),
        sa.Column("primary_field", sa.String(100), nullable=True),
        sa.Column("searchable_fields", postgresql.JSONB(), nullable=True),
        sa.Column("default_sort", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("'true'")),
        sa.Column("code_prefix", sa.String(10), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── rel_relationships ──
    op.create_table(
        "rel_relationships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("legal_name", sa.String(255), server_default=""),
        sa.Column("preferred_name", sa.String(255), server_default=""),
        sa.Column("relationship_type", sa.String(60), nullable=False, server_default=sa.text("'customer'")),
        sa.Column("is_organization", sa.Boolean(), server_default=sa.text("'false'")),
        sa.Column("company_name", sa.String(255), server_default=""),
        sa.Column("designation", sa.String(255), server_default=""),
        sa.Column("email", sa.String(255), server_default=""),
        sa.Column("email2", sa.String(255), server_default=""),
        sa.Column("email3", sa.String(255), server_default=""),
        sa.Column("phone", sa.String(60), server_default=""),
        sa.Column("phone2", sa.String(60), server_default=""),
        sa.Column("phone3", sa.String(60), server_default=""),
        sa.Column("address_line1", sa.String(255), server_default=""),
        sa.Column("address_line2", sa.String(255), server_default=""),
        sa.Column("city", sa.String(100), server_default=""),
        sa.Column("state", sa.String(100), server_default=""),
        sa.Column("postal_code", sa.String(50), server_default=""),
        sa.Column("country", sa.String(100), server_default=""),
        sa.Column("website", sa.String(255), server_default=""),
        sa.Column("social_linkedin", sa.String(255), server_default=""),
        sa.Column("social_twitter", sa.String(255), server_default=""),
        sa.Column("social_instagram", sa.String(255), server_default=""),
        sa.Column("social_facebook", sa.String(255), server_default=""),
        sa.Column("timezone", sa.String(50), server_default=""),
        sa.Column("preferred_language", sa.String(50), server_default=sa.text("'en'")),
        sa.Column("preferred_currency", sa.String(10), server_default=""),
        sa.Column("tags", sa.Text(), server_default=""),
        sa.Column("segments", sa.Text(), server_default=""),
        sa.Column("industries", sa.Text(), server_default=""),
        sa.Column("source", sa.String(100), server_default=""),
        sa.Column("referral_info", sa.Text(), server_default=""),
        sa.Column("risk_level", sa.String(30), server_default=sa.text("'medium'")),
        sa.Column("priority", sa.Integer(), server_default=sa.text("'0'")),
        sa.Column("internal_owner", sa.String(64), server_default=""),
        sa.Column("status", sa.String(30), server_default=sa.text("'active'")),
        sa.Column("notes", sa.Text(), server_default=""),
        sa.Column("custom_attributes", sa.Text(), server_default=sa.text("'{}'")),
        sa.Column("legacy_person_id", sa.Integer(), nullable=True),
        sa.Column("legacy_relationship_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.String(255), server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )

    # ── rel_timeline ──
    op.create_table(
        "rel_timeline",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("relationship_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("event_time", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("title", sa.String(500), server_default=""),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("reference_type", sa.String(60), server_default=""),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.Text(), server_default=sa.text("'{}'")),
        sa.Column("created_by", sa.String(255), server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── rel_ai_memory ──
    op.create_table(
        "rel_ai_memory",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("relationship_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("memory_json", sa.Text(), server_default=sa.text("'{}'")),
        sa.Column("summary", sa.Text(), server_default=""),
        sa.Column("health_score", sa.Integer(), server_default=sa.text("'50'")),
        sa.Column("engagement_score", sa.Integer(), server_default=sa.text("'50'")),
        sa.Column("lifetime_value", sa.Numeric(15, 2), server_default=sa.text("'0'")),
        sa.Column("retention_risk", sa.Integer(), server_default=sa.text("'50'")),
        sa.Column("last_ai_update", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )

    # ── customer ──
    op.create_table(
        "customer",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("relationship_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(30), server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── customer_profiles ──
    op.create_table(
        "customer_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("lifetime_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("segment", sa.String(50), nullable=True),
        sa.Column("preferred_channel", sa.String(50), nullable=True),
        sa.Column("preferred_channel_provenance", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── auth_roles ──
    op.create_table(
        "auth_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default=sa.text("''")),
        sa.Column("permissions", sa.Text(), server_default=sa.text("'[]'")),
        sa.Column("is_system", sa.Boolean(), server_default=sa.text("'false'")),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )

    # ── auth_member_roles ──
    op.create_table(
        "auth_member_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("scope", sa.String(50), server_default=sa.text("'organization'")),
        sa.Column("scope_id", sa.Integer(), nullable=True),
        sa.Column("granted_by", sa.String(255), server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )

    # ── user_sessions ──
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("device_info", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── api_keys ──
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        sa.Column("scopes", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
    )

    # ── sh_objects ──
    op.create_table(
        "sh_objects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("object_id", sa.String(255), nullable=False),
        sa.Column("workspace_id", sa.String(255), nullable=False),
        sa.Column("object_type", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("data", postgresql.JSONB(), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("'false'")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── sh_workspaces ──
    op.create_table(
        "sh_workspaces",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("workspace_type", sa.String(100), nullable=False),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("color", sa.String(50), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── workspaces ──
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("settings", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── shunya_identities ──
    op.create_table(
        "shunya_identities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("identity_id", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("primary_email", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("auth_methods_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("shunya_identities")
    op.drop_table("workspaces")
    op.drop_table("sh_workspaces")
    op.drop_table("sh_objects")
    op.drop_table("api_keys")
    op.drop_table("user_sessions")
    op.drop_table("auth_member_roles")
    op.drop_table("auth_roles")
    op.drop_table("customer_profiles")
    op.drop_table("customer")
    op.drop_table("rel_ai_memory")
    op.drop_table("rel_timeline")
    op.drop_table("rel_relationships")
    op.drop_table("entity_definitions")
    op.drop_table("entities")
    op.drop_table("person_identities")
    op.drop_table("persons")
    op.drop_table("tasks")
    op.drop_table("task_lists")
    op.drop_table("proposals")
    op.drop_table("leads")
    op.drop_table("team_members")
    op.drop_table("organizations")
    op.drop_table("tenants")