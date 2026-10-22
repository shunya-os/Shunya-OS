"""r6b35 — close the last create_all-only tables in the chain (G1.21).

WHY
---
After r6b33 (personal-scope workspaces) and r6b34 (identity/organization
integrity), a comparison of SQLAlchemy metadata against the migration-only
schema still found eight ORM tables that no revision creates:

    attention_items          emotional_context_items   execution_idempotency
    m6_media_assets          notif_event_preferences   taxation_business_rules
    taxation_refresh_log     taxation_rules

They exist only because ``app/__init__.py`` calls ``db.create_all()`` at boot.
That is a hidden dependency: any deployment that runs the migration chain but
boots with a role that cannot CREATE TABLE — or serves before the app process
has booted — is missing these tables, and the first request that touches them
raises ``UndefinedTable``.

``execution_idempotency`` is the sharpest example: ``app/execution/idempotency.py``
uses it as the DB-level unique idempotency store, i.e. the primitive that makes an
interrupted execution safe to retry. A missing table there is not a degraded
feature, it is a broken retry guarantee.

WHAT
----
Forward-only, additive, guarded. Every definition is FROZEN here, matching
``app/*/models.py`` at the time of writing — no metadata import, so a change to a
model cannot retroactively change what this revision does. Existing rows are
never touched; a boot-created database converges (all eight tables already exist →
no-ops).

No foreign keys are added on these tables: none is declared in the ORM, and their
tenancy columns (``organization_id``, ``tenant_id``) carry the same unresolved
semantics documented in r6b34.

Revision ID: r6b35_missing_boot_tables
Revises: r6b34_identity_integrity
"""
import sqlalchemy as sa
from alembic import op  # noqa: F401  (revision signature symmetry)

revision = "r6b35_missing_boot_tables"
down_revision = "r6b34_identity_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from migrations.guarded import guarded_op

    gop = guarded_op()

    gop.create_table(
        "attention_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(64), nullable=True),
        sa.Column("identity_id", sa.String(64), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("related_object_type", sa.String(64), nullable=True),
        sa.Column("related_object_id", sa.String(128), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("dismissed_at", sa.DateTime(), nullable=True),
        sa.Column("dismissed_by", sa.String(64), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.String(64), nullable=True),
    )
    for name, cols in [
        ("ix_attention_created", ["created_at"]),
        ("ix_attention_identity", ["identity_id", "state"]),
        ("ix_attention_items_identity_id", ["identity_id"]),
        ("ix_attention_items_organization_id", ["organization_id"]),
        ("ix_attention_items_workspace_id", ["workspace_id"]),
        ("ix_attention_org_state", ["organization_id", "state"]),
        ("ix_attention_source", ["source"]),
        ("ix_attention_workspace", ["workspace_id", "state"]),
    ]:
        gop.create_index(name, "attention_items", cols)

    gop.create_table(
        "emotional_context_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("workspace_id", sa.String(64), nullable=True),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("expression_type", sa.String(30), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("source", sa.String(120), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("retention", sa.String(30), nullable=True),
        sa.Column("related_object_type", sa.String(60), nullable=True),
        sa.Column("related_object_id", sa.Integer(), nullable=True),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(120), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("provenance", sa.Text(), nullable=True),
        sa.Column("correction_id", sa.Integer(), nullable=True),
        sa.Column("corrected_at", sa.DateTime(), nullable=True),
        sa.Column("corrected_by", sa.String(120), nullable=True),
        sa.Column("correction_note", sa.Text(), nullable=True),
    )
    for name, cols in [
        ("ix_eci_correction", ["correction_id"]),
        ("ix_eci_expression", ["expression_type"]),
        ("ix_eci_person", ["person_id"]),
        ("ix_eci_status", ["status"]),
        ("ix_eci_tenant", ["tenant_id"]),
        ("ix_eci_timestamp", ["observed_at"]),
        ("ix_emotional_context_items_expression_type", ["expression_type"]),
        ("ix_emotional_context_items_person_id", ["person_id"]),
        ("ix_emotional_context_items_tenant_id", ["tenant_id"]),
        ("ix_emotional_context_items_workspace_id", ["workspace_id"]),
    ]:
        gop.create_index(name, "emotional_context_items", cols)

    gop.create_table(
        "execution_idempotency",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("outcome_id", sa.String(12), nullable=False),
        sa.Column("identity_id", sa.String(64), nullable=False),
        sa.Column("commitment_type", sa.String(64), nullable=True),
        sa.Column("commitment_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    gop.create_index("ix_execution_idempotency_idempotency_key",
                     "execution_idempotency", ["idempotency_key"], unique=True)

    gop.create_table(
        "m6_media_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(64), nullable=False),
        sa.Column("identity_id", sa.String(64), nullable=False),
        sa.Column("raw_prompt", sa.Text(), nullable=False),
        sa.Column("visual_brief", sa.Text(), nullable=True),
        sa.Column("visual_style", sa.String(30), nullable=True),
        sa.Column("result_kind", sa.String(30), nullable=True),
        sa.Column("provider", sa.String(40), nullable=True),
        sa.Column("asset_url", sa.Text(), nullable=True),
        sa.Column("aspect_ratio", sa.String(10), nullable=True),
        sa.Column("platform", sa.String(40), nullable=True),
        sa.Column("campaign_id", sa.Integer(), nullable=True),
        sa.Column("generation_job_id", sa.String(80), nullable=True),
        sa.Column("business_context", sa.JSON(), nullable=True),
        sa.Column("lifecycle_status", sa.String(20), nullable=False),
        sa.Column("runtime_state", sa.String(30), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("sh_object_id", sa.String(64), nullable=True),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("archived_by", sa.String(64), nullable=True),
        sa.Column("restored_at", sa.DateTime(), nullable=True),
        sa.Column("restored_by", sa.String(64), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    gop.create_index("ix_m6_media_assets_identity_id", "m6_media_assets", ["identity_id"])

    gop.create_table(
        "notif_event_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("identity_id", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.String(64), nullable=True),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    gop.create_index("ix_notif_event_preferences_identity_id",
                     "notif_event_preferences", ["identity_id"])
    gop.create_index("ix_notif_pref_identity", "notif_event_preferences",
                     ["identity_id", "tenant_id"])
    gop.create_index("ix_notif_pref_lookup", "notif_event_preferences",
                     ["identity_id", "event_type", "channel"], unique=True)

    gop.create_table(
        "taxation_business_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("jurisdiction", sa.String(60), nullable=True),
        sa.Column("business_type", sa.String(60), nullable=True),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("section", sa.String(100), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("deadline_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    gop.create_table(
        "taxation_refresh_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("sources_attempted", sa.Integer(), nullable=True),
        sa.Column("sources_success", sa.Integer(), nullable=True),
        sa.Column("rules_created", sa.Integer(), nullable=True),
        sa.Column("error", sa.String(500), nullable=True),
    )

    gop.create_table(
        "taxation_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("jurisdiction", sa.String(60), nullable=True),
        sa.Column("business_type", sa.String(60), nullable=True),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("section", sa.String(100), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rate", sa.Float(), nullable=True),
        sa.Column("threshold_min", sa.Float(), nullable=True),
        sa.Column("threshold_max", sa.Float(), nullable=True),
        sa.Column("threshold_unit", sa.String(30), nullable=True),
        sa.Column("applicability", sa.String(100), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("etag", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("superseded_by", sa.Integer(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for name, cols in [
        ("ix_tax_rule_category", ["category"]),
        ("ix_tax_rule_org", ["organization_id"]),
        ("ix_tax_rule_source", ["source"]),
    ]:
        gop.create_index(name, "taxation_rules", cols)


def downgrade() -> None:
    """Intentionally additive-only: these tables hold user-facing records
    (attention items, emotional context, media assets, notification
    preferences, tax rules) and an idempotency ledger. Dropping them destroys
    data, so no automatic downgrade is provided."""
    pass
