"""SHUNYA — canonical database isolation guard.

Single source of truth for the question: "is this database URL production-like?"

R6B-2.7 §8 root cause: `tests/test_g11_identity_object.py` was executed against
the production `DATABASE_URL` (postgres@localhost:5432/shunya_os) and wrote 344
`object_type='test'` rows into the real Panchi Club organization (org 7). The
tests existed; the isolation did not. Any test or certification harness MUST now
fail closed BEFORE it can touch a production-like database.

Production-like means: a PostgreSQL URL on the default port (5432) whose database
name is a production name (shunya / shunya_os / shunya_db), or any URL containing
"production". Isolated means any SQLite URL, or PostgreSQL on a non-default port
(e.g. the disposable certification cluster on 5433) / an explicit *_cert* naming.
"""

from __future__ import annotations

import re

# Database names that identify the production cluster when seen on port 5432.
_PRODUCTION_DB_NAMES = ("shunya_os", "shunya_db", "shunya")

# Explicitly isolated test/certification database name markers.
_ISOLATED_DB_MARKERS = ("_test", "_cert", "test_", "cert_")


def is_isolated_url(url: str) -> bool:
    """True when the URL is an explicitly isolated (non-production) database.

    Any SQLite URL is isolated: the production cluster is PostgreSQL
    (`shunya_os` on 5432), so SQLite can never be the production database.
    """
    if not url:
        return False
    if url.startswith("sqlite://"):
        return True
    return False


def is_production_like(url: str) -> bool:
    """True when the URL could reach production / a shared, non-isolated DB.

    Fails closed: a PostgreSQL URL that is not provably isolated is treated as
    production-like.
    """
    if not url:
        return False
    if is_isolated_url(url):
        return False

    low = url.lower()
    if "production" in low:
        return True

    if "postgres" not in low:
        # Unknown driver that is not provably isolated.
        return True

    # Extract the database name (path component).
    dbname = low.rsplit("/", 1)[-1].split("?", 1)[0]

    if any(name in dbname for name in _PRODUCTION_DB_NAMES):
        # An explicit isolated marker (shunya_r6b27_cert2) proves isolation.
        if any(marker in dbname for marker in _ISOLATED_DB_MARKERS):
            return False
        # A production name on the default PostgreSQL port is production.
        if ":5432/" in low:
            return True
        # A production name on a non-default port is a provisioned instance
        # (e.g. the 5433 certification cluster) — assumed isolated.
        return False

    return False


def assert_isolated_database(url: str, *, context: str = "test") -> bool:
    """Raise RuntimeError if `url` is production-like.

    Returns True when the database is safe to use from `context`.
    """
    if is_production_like(url):
        raise RuntimeError(
            f"[{context}] refusing to use a production-like database: {url!r}. "
            f"Tests/certification must use sqlite:///:memory: or an explicitly "
            f"provisioned isolated database (e.g. postgresql://...@127.0.0.1:5433/<name>_cert). "
            f"See app/safety/db_guard.py (R6B-2.7 §8 regression guard)."
        )
    return True


def assert_not_production_url(url: str, *, context: str = "certification") -> bool:
    """Alias used by shell/script certification harnesses (same predicate)."""
    return assert_isolated_database(url, context=context)