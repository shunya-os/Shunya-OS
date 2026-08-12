"""SHUNYA — Initial Schema: Base tables from current model definitions.

Creates the full model-defined schema as the foundation. All subsequent
migrations (0002–0005) reconcile/upgrade this base.

Created: 2026-08-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import datetime

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    is_sqlite = dialect == "sqlite"

    def _table_exists(name: str) -> bool:
        try:
            if is_sqlite:
                r = bind.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
                    {"n": name},
                ).fetchone()
                return r is not None
            r = bind.execute(
                sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name=:n)"),
                {"n": name},
            ).fetchone()
            return r[0] if r else False
        except Exception:
            return False

    # Use the app's model metadata to create the full schema
    import app.models  # noqa: F401
    import app.relationship.models  # noqa: F401
    import app.customers.models  # noqa: F401
    import app.core.entity  # noqa: F401

    from app import db

    # Create all tables defined by the models.
    # SQLAlchemy handles dependency ordering automatically.
    import app.tenant  # noqa: F401
    db.metadata.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    is_sqlite = dialect == "sqlite"

    import app.models  # noqa: F401
    import app.relationship.models  # noqa: F401
    import app.customers.models  # noqa: F401
    import app.core.entity  # noqa: F401

    from app import db

    for table in reversed(db.metadata.sorted_tables):
        try:
            table.drop(bind=bind)
        except Exception:
            pass