"""G1.19 — organizations table parity with the model (frozen definition).

A database built from the migration chain alone had an `organizations` table
with almost none of the columns the application writes, so creating an
organization crashed on PostgreSQL:

    psycopg2.errors.UndefinedColumn: column "business_type" of relation
    "organizations" does not exist

Boot-created databases were fine because `db.create_all()` materialised the
model; migration-only installs were not. This forward-only, guarded revision
restores parity for the lifecycle columns.

G1.20 — determinism. The first version derived the column list from the live
ORM metadata at upgrade time, which makes a historical migration depend on the
current model (it would silently change behaviour whenever the model changed).
The definition below is frozen: explicit names, explicit types, no metadata
import. A boot-created database converges as a no-op because every column is
added only when absent.

Nullability follows the model at the time of writing: all of these columns are
declared nullable, with defaults applied on the ORM side (no server defaults),
so no historical row is rewritten and no NOT NULL constraint is imposed on data
that predates it.

Revision ID: r6b32_organizations_parity
Revises: r6b31_team_member_identity
"""
import sqlalchemy as sa
from alembic import op

revision = "r6b32_organizations_parity"
down_revision = "r6b31_team_member_identity"
branch_labels = None
depends_on = None

TABLE = "organizations"

# (column name, SQLAlchemy type) — frozen from the model definition.
COLUMNS = [
    ("business_type", sa.String(60)),
    ("logo_url", sa.String(500)),
    ("brand_color", sa.String(20)),
    ("brand_color_secondary", sa.String(20)),
    ("brand_tagline", sa.String(500)),
    ("brand_description", sa.Text()),
    ("tax_id", sa.String(100)),
    ("registration_number", sa.String(100)),
    ("phone", sa.String(60)),
    ("email", sa.String(255)),
    ("website", sa.String(500)),
    ("address", sa.Text()),
    ("city", sa.String(120)),
    ("state", sa.String(120)),
    ("country", sa.String(120)),
    ("postal_code", sa.String(30)),
    ("timezone", sa.String(60)),
    ("currency", sa.String(10)),
    ("date_format", sa.String(20)),
    ("plan", sa.String(30)),
    ("is_active", sa.Boolean()),
    ("max_members", sa.Integer()),
    ("ai_enabled", sa.Boolean()),
    ("ai_config", sa.Text()),
    ("legacy_tenant_id", sa.Integer()),
    ("created_by", sa.String(120)),
    ("updated_at", sa.DateTime()),
]


def upgrade():
    bind = op.get_bind()
    existing = {c["name"] for c in sa.inspect(bind).get_columns(TABLE)}

    for name, column_type in COLUMNS:
        if name in existing:
            continue
        op.add_column(TABLE, sa.Column(name, column_type, nullable=True))


def downgrade():
    # Forward-only by project convention: these columns are model-required, so
    # removing them would break organization creation again.
    pass
