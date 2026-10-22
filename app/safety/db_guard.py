"""SHUNYA — canonical database isolation guard.

Single source of truth for the question: "is this database URL production-like?"

R6B-2.7 §8 root cause: `tests/test_g11_identity_object.py` was executed against
the production `DATABASE_URL` (postgres@localhost:5432/shunya_os) and wrote 344
`object_type='test'` rows into the real Panchi Club organization (org 7). The
tests existed; the isolation did not. Any test or certification harness MUST now
fail closed BEFORE it can touch a production-like database.

G1.21 hardening — the previous predicate was essentially "production database name
on port 5432", which is a port/name heuristic, not endpoint identity:

  * a remote host was allowed as long as its port was not 5432;
  * a production-named database was "assumed isolated" on any other port;
  * nothing checked the *execution context*, so a script could point at a
    production-like instance while claiming to be a test run.

The predicate now decides on three independent facts, all of which must point at
an isolated instance:

  1. **Endpoint identity** — loopback host only (a disposable instance is local),
     the real production names refused on any port, and port 5432 itself refused
     unless the database carries an explicit isolation marker.
  2. **Explicit isolation markers** (`_test`, `_cert`, `test_`, `cert_`) can lift
     the port/name restrictions, because they name the instance as disposable.
  3. **Execution context** — an isolated PostgreSQL URL is only accepted when the
     process has declared itself a test/CI run (`SHUNYA_ENV=test|testing|ci`,
     `PYTEST_CURRENT_TEST`, or the `SHUNYA_REQUIRE_ISOLATED_DB=1` opt-in). A
     production process never gets to call itself a test.

SQLite is always isolated: the production store is PostgreSQL, so SQLite cannot be
it — and it is the canonical test database.
"""

from __future__ import annotations

import os
from urllib.parse import urlsplit

# Exact database names that identify the production store.
_PRODUCTION_DB_NAMES = ("shunya_os", "shunya_db", "shunya")

# Explicitly isolated test/certification database name markers.
_ISOLATED_DB_MARKERS = ("_test", "_cert", "test_", "cert_")

# Hosts that can carry a disposable local instance.
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", "", None}

# Declared test execution contexts.
_TEST_CONTEXTS = {"test", "testing", "ci", "certification", "cert"}


def is_isolated_url(url: str) -> bool:
    """True when the URL is provably an isolated (non-production) database.

    Any SQLite URL is isolated: the production cluster is PostgreSQL
    (`shunya_os` on 5432), so SQLite can never be the production database.
    """
    if not url:
        return False
    if url.startswith("sqlite://"):
        return True
    return False


def _parts(url: str):
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    try:
        port = parts.port
    except ValueError:
        port = None
    dbname = (parts.path or "").lstrip("/").split("?", 1)[0].lower()
    return host, port, dbname


def in_test_context() -> bool:
    """True when this process has declared itself a test / CI run."""
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return True
    if os.environ.get("SHUNYA_REQUIRE_ISOLATED_DB") == "1":
        return True
    env = (os.environ.get("SHUNYA_ENV") or os.environ.get("FLASK_ENV") or "").lower()
    return env in _TEST_CONTEXTS


def is_production_like(url: str, *, context: str | None = None) -> bool:
    """True when the URL could reach production / a shared, non-isolated DB.

    Fails closed: a PostgreSQL URL that is not provably isolated is treated as
    production-like. ``context`` is accepted for call-site compatibility; the
    execution-context decision is made by :func:`assert_isolated_database`.
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

    host, port, dbname = _parts(url)
    marked = any(marker in dbname for marker in _ISOLATED_DB_MARKERS)

    # 1. Endpoint identity: a disposable instance is local to this host.
    if host not in _LOOPBACK_HOSTS:
        return True

    # 2. A production database name is production on any port, unless the name
    #    itself declares the instance disposable (…_cert, …_test).
    if dbname in _PRODUCTION_DB_NAMES and not marked:
        return True

    # 3. The production cluster listens on 5432; anything there must prove
    #    isolation by name.
    if port == 5432 and not marked:
        return True

    return False


def assert_isolated_database(url: str, *, context: str = "test") -> bool:
    """Raise RuntimeError if `url` is production-like OR the process is not a test.

    Returns True when the database is safe to use from `context`.
    """
    if is_production_like(url):
        raise RuntimeError(
            f"[{context}] refusing to use a production-like database: {url!r}. "
            f"Tests/certification must use sqlite:///:memory: or an explicitly "
            f"provisioned isolated database on a loopback host "
            f"(e.g. postgresql://...@127.0.0.1:5433/<name>_cert). "
            f"See app/safety/db_guard.py (R6B-2.7 §8 regression guard)."
        )
    # Execution context: a non-SQLite database is only acceptable when this
    # process has declared itself a test/CI run. Without this, a script could
    # present a disposable-looking URL from a production process.
    if not is_isolated_url(url) and not in_test_context():
        raise RuntimeError(
            f"[{context}] refusing a PostgreSQL URL outside a declared test "
            f"execution context: {url!r}. Set SHUNYA_ENV=test (or run under "
            f"pytest, or SHUNYA_REQUIRE_ISOLATED_DB=1 for certification scripts)."
        )
    return True


def assert_not_production_url(url: str, *, context: str = "certification") -> bool:
    """Alias used by shell/script certification harnesses (same predicate)."""
    return assert_isolated_database(url, context=context)
