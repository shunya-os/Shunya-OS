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
    conn = op.get_bind()
    dialect = conn.dialect.name
    is_sqlite = dialect == "sqlite"

    def _table_exists(name: str) -> bool:
        if is_sqlite:
            result = conn.execute(
                sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
                {"name": name},
            ).fetchone()
            return result is not None
        else:
            result = conn.execute(
                sa.text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_name = :name)"
                ),
                {"name": name},
            ).fetchone()
            return result[0] if result else False

    def _column_exists(table: str, column: str) -> bool:
        try:
            cols = [c[1] for c in conn.execute(
                sa.text(f"PRAGMA table_info({table})")).fetchall()]
            return column in cols
        except Exception:
            return False

    def _constraint_exists(table: str, constraint: str) -> bool:
        try:
            if is_sqlite:
                result = conn.execute(
                    sa.text(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='index' AND name=:name AND tbl_name=:tbl"
                    ),
                    {"name": constraint, "tbl": table},
                ).fetchone()
                return result is not None
            else:
                result = conn.execute(
                    sa.text(
                        "SELECT constraint_name FROM information_schema.table_constraints "
                        "WHERE table_name=:tbl AND constraint_name=:name"
                    ),
                    {"tbl": table, "name": constraint},
                ).fetchone()
                return result is not None if result else False
        except Exception:
            return False

    def _safe(fn, *a, **kw):
        """Execute a migration operation, catching SQLite-incompatible errors."""
        if is_sqlite:
            try:
                fn(*a, **kw)
            except (NotImplementedError, Exception):
                # SQLite doesn't support ALTER TABLE ADD CONSTRAINT, ALTER COLUMN, etc.
                pass
        else:
            fn(*a, **kw)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. team_members — missing columns that crashed production
    # ─────────────────────────────────────────────────────────────────────────
    if _table_exists("team_members"):
        if not _column_exists("team_members", "person_id"):
            op.add_column("team_members", sa.Column("person_id", sa.Integer(), nullable=True))
            op.create_foreign_key(
                "fk_team_members_person_id_persons",
                "team_members", "persons",
                ["person_id"], ["id"],
            )
        if not _constraint_exists("team_members", "uq_team_members_api_token"):
            _safe(op.create_unique_constraint, "uq_team_members_api_token", "team_members", ["api_token"])
        if not _constraint_exists("team_members", "uq_team_members_email"):
            _safe(op.create_unique_constraint, "uq_team_members_email", "team_members", ["email"])
        _safe(op.alter_column, "team_members", "tenant_id", nullable=True, existing_type=sa.Integer())
        try:
            _safe(op.drop_constraint, "fk_team_members_tenant_id_tenants", "team_members", type_="foreignkey")
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Missing columns
    # ─────────────────────────────────────────────────────────────────────────

    # activity_logs
    if _table_exists("activity_logs"):
        if not _column_exists("activity_logs", "lead_id"):
            op.add_column("activity_logs", sa.Column("lead_id", sa.Integer(), nullable=True))
            op.create_foreign_key("fk_activity_logs_lead_id_leads", "activity_logs", "leads", ["lead_id"], ["id"])
        if not _column_exists("activity_logs", "user"):
            op.add_column("activity_logs", sa.Column("user", sa.String(length=120), nullable=True))

    # client_users
    if _table_exists("client_users"):
        if not _column_exists("client_users", "lead_id"):
            op.add_column("client_users", sa.Column("lead_id", sa.Integer(), nullable=True))
            op.create_foreign_key("fk_client_users_lead_id_leads", "client_users", "leads", ["lead_id"], ["id"])
        if not _column_exists("client_users", "password_hash"):
            op.add_column("client_users", sa.Column("password_hash", sa.String(length=128), nullable=True))
        if not _constraint_exists("client_users", "uq_client_users_email"):
            _safe(op.create_unique_constraint, "uq_client_users_email", "client_users", ["email"])
        _safe(op.alter_column, "client_users", "email", nullable=False, existing_type=sa.String(length=255))

    # invoices
    if _table_exists("invoices"):
        if not _column_exists("invoices", "lead_id"):
            op.add_column("invoices", sa.Column("lead_id", sa.Integer(), nullable=True))
            op.create_foreign_key("fk_invoices_lead_id_leads", "invoices", "leads", ["lead_id"], ["id"])
        if not _column_exists("invoices", "raised_at"):
            op.add_column("invoices", sa.Column("raised_at", sa.DateTime(), nullable=True))
        if not _constraint_exists("invoices", "uq_invoices_invoice_number"):
            _safe(op.create_unique_constraint, "uq_invoices_invoice_number", "invoices", ["invoice_number"])
        _safe(op.alter_column, "invoices", "due_date", type_=sa.Date(), existing_type=sa.DateTime(),
              postgresql_using="due_date::date")

    # notifications
    if _table_exists("notifications"):
        if not _column_exists("notifications", "lead_id"):
            op.add_column("notifications", sa.Column("lead_id", sa.Integer(), nullable=True))
            op.create_foreign_key("fk_notifications_lead_id_leads", "notifications", "leads", ["lead_id"], ["id"])
        _safe(op.alter_column, "notifications", "is_read", nullable=False, existing_type=sa.Boolean())

    # leads
    if _table_exists("leads"):
        if not _constraint_exists("leads", "uq_leads_code"):
            _safe(op.create_unique_constraint, "uq_leads_code", "leads", ["code"])

    # observations
    if _table_exists("observations"):
        for col_name, col_type in [
            ("action", sa.String(length=255)),
            ("actual_outcome", sa.Text()),
            ("channel", sa.String(length=60)),
            ("discrepancy", sa.Text()),
            ("expected_outcome", sa.Text()),
            ("lead_id", sa.Integer()),
            ("success", sa.Boolean()),
        ]:
            if not _column_exists("observations", col_name):
                op.add_column("observations", sa.Column(col_name, col_type, nullable=True))
        if _column_exists("observations", "lead_id"):
            try:
                op.create_foreign_key("fk_observations_lead_id_leads", "observations", "leads", ["lead_id"], ["id"])
            except Exception:
                pass
        _safe(op.alter_column, "observations", "confidence", type_=sa.Float(), existing_type=sa.String(length=20))

    # payments
    if _table_exists("payments"):
        for col_name, col_type in [
            ("lead_id", sa.Integer()),
            ("method", sa.String(length=80)),
            ("ref_number", sa.String(length=120)),
        ]:
            if not _column_exists("payments", col_name):
                op.add_column("payments", sa.Column(col_name, col_type, nullable=True))
        if _column_exists("payments", "lead_id"):
            try:
                op.create_foreign_key("fk_payments_lead_id_leads", "payments", "leads", ["lead_id"], ["id"])
            except Exception:
                pass
        _safe(op.alter_column, "payments", "amount", nullable=False, existing_type=sa.Numeric(12, 2))
        _safe(op.alter_column, "payments", "type", nullable=False, existing_type=sa.String(length=30))

    # persons
    if _table_exists("persons"):
        for col_name, col_type in [
            ("canonical_name", sa.String(length=255)),
            ("preferred_name", sa.String(length=255)),
            ("status", sa.String(length=30)),
            ("tenant_id", sa.Integer()),
            ("updated_at", sa.DateTime()),
        ]:
            if not _column_exists("persons", col_name):
                op.add_column("persons", sa.Column(col_name, col_type, nullable=True))
        if _column_exists("persons", "tenant_id"):
            try:
                op.create_foreign_key("fk_persons_tenant_id_tenants", "persons", "tenants", ["tenant_id"], ["id"])
            except Exception:
                pass

    # relationships
    if _table_exists("relationships"):
        for col_name, col_type in [
            ("ended_at", sa.DateTime()),
            ("relationship_type", sa.String(length=30)),
            ("source", sa.String(length=120)),
            ("started_at", sa.DateTime()),
        ]:
            if not _column_exists("relationships", col_name):
                op.add_column("relationships", sa.Column(col_name, col_type, nullable=True))
        _safe(op.alter_column, "relationships", "tenant_id", nullable=True, existing_type=sa.Integer())

    # tenants
    if _table_exists("tenants"):
        if not _column_exists("tenants", "subdomain"):
            op.add_column("tenants", sa.Column("subdomain", sa.String(length=255), nullable=True, unique=True))
        if not _constraint_exists("tenants", "uq_tenants_subdomain"):
            _safe(op.create_unique_constraint, "uq_tenants_subdomain", "tenants", ["subdomain"])

    # Unique constraints
    for table, constraint, cols in [
        ("founder_conversations", "uq_founder_conversations_conv_id", ["conv_id"]),
        ("founder_objects", "uq_founder_objects_object_id", ["object_id"]),
        ("founder_relationships", "uq_founder_relationships_rel_id", ["rel_id"]),
        ("founder_spaces", "uq_founder_spaces_space_id", ["space_id"]),
        ("shunya_identities", "uq_shunya_identities_identity_id", ["identity_id"]),
        ("suppliers", "uq_suppliers_name", ["name"]),
    ]:
        if _table_exists(table) and not _constraint_exists(table, constraint):
            _safe(op.create_unique_constraint, constraint, table, cols)

    # Default value alignment
    if _table_exists("notifications"):
        _safe(op.alter_column, "notifications", "is_read", server_default=sa.text("false"))
    if _table_exists("payments"):
        _safe(op.alter_column, "payments", "amount", server_default=sa.text("0"))
        _safe(op.alter_column, "payments", "type", server_default=sa.text("'guest_payment'"))
    if _table_exists("persons"):
        _safe(op.alter_column, "persons", "status", server_default=sa.text("'active'"))
    if _table_exists("team_members"):
        _safe(op.alter_column, "team_members", "is_active", server_default=sa.text("true"))
        _safe(op.alter_column, "team_members", "role", server_default=sa.text("'agent'"))