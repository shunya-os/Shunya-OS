"""Single DB session wrapper — canonical entry point for all database access.

PHASE 3: Single source of truth enforcement.
All modules MUST use get_db() instead of creating their own connections.
Flask-SQLAlchemy is the single engine. No multiple sessions, no fallback DB.
"""

from app import db as _flask_db

# Flask-SQLAlchemy is the single canonical database instance.
# All queries go through this. No create_engine, no SessionLocal, no fallback.
db = _flask_db


def get_db():
    """Return the canonical database session.

    Usage:
        from app.core.db.session import get_db
        db = get_db()
        db.session.query(Object).all()
    """
    return db


def health_check() -> bool:
    """Verify database connectivity."""
    try:
        db.session.execute(db.text("SELECT 1"))
        return True
    except Exception:
        return False