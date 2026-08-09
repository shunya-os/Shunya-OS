"""Single DB session wrapper — canonical entry point for all database access.

PHASE 3: Single source of truth enforcement.
All modules MUST use from app.core.db import db.
Direct db.session access is BLOCKED by the proxy.
Use db.get_session() for legitimate session access.
"""

import logging

from app import db as _flask_db

logger = logging.getLogger(__name__)


class DBProxy:
    """Proxy that blocks direct .session access while passing through everything else.

    This prevents rogue 'from app import db; db.session.add(...)' calls.
    Use db.get_session() for legitimate session access.
    """

    def __init__(self, original):
        self._original_db = original

    def __getattr__(self, name):
        if name == "session":
            raise RuntimeError(
                "Direct db.session access is FORBIDDEN. "
                "Use from app.core.db import db and call db.get_session() instead."
            )
        return getattr(self._original_db, name)

    def get_session(self):
        """Return the canonical database session.

        This is the ONLY allowed way to access the session.
        """
        session = self._original_db.session
        return session


# Canonical database instance — proxied to block direct .session access
db = DBProxy(_flask_db)


def get_db():
    """Return the canonical database proxy. Use .get_session() for session."""
    return db


def get_session():
    """Return the canonical database session (the only allowed path)."""
    return db.get_session()


def health_check() -> bool:
    """Verify database connectivity."""
    try:
        _flask_db.session.execute(_flask_db.text("SELECT 1"))
        return True
    except Exception:
        return False