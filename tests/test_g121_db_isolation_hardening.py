"""G1.21 — database isolation guard: endpoint identity AND execution context.

The predicate used to be a port/name heuristic. These tests pin the hardened
rules and, in particular, the two cases that were previously allowed:

  * a remote host on a non-5432 port (never a disposable local instance);
  * a production-named database on a non-5432 port ("assumed isolated").

They also pin that a PostgreSQL URL is refused when the process has not declared
itself a test/CI run — i.e. a script cannot present a production-looking endpoint
from a production context and be believed.
"""

import os

import pytest

from app.safety import db_guard
from app.safety.db_guard import (
    assert_isolated_database,
    in_test_context,
    is_production_like,
)

PRODUCTION_URLS = [
    "postgresql://shunya:***@localhost:5432/shunya_os",
    "postgresql://shunya:***@127.0.0.1:5432/shunya",
    "postgresql://shunya:***@127.0.0.1:5432/anything",       # production port
    "postgresql://shunya:***@127.0.0.1:5433/shunya_os",      # prod name, other port
    "postgresql://shunya:***@127.0.0.1:5433/shunya",         # prod name, other port
    "postgresql://shunya:***@db.internal:5433/shunya_cert",  # remote host
    "postgresql://shunya:***@10.0.0.5:5433/app_db",          # remote host
    "postgresql://shunya:***@localhost:9999/production",
]

ISOLATED_URLS = [
    "sqlite:///:memory:",
    "sqlite:////tmp/shunya_test.db",
    "postgresql://shunya-deploy@127.0.0.1:5433/shunya_r6b27_cert2",
    "postgresql://user@127.0.0.1:5433/shunya_r6b25_cert",
    "postgresql://postgres@127.0.0.1:5445/shunya_g121",       # disposable cluster
    "postgresql://postgres@localhost:5445/shunya_g121_mig",
]


class TestEndpointIdentity:
    @pytest.mark.parametrize("url", PRODUCTION_URLS)
    def test_production_endpoints_are_flagged(self, url):
        assert is_production_like(url) is True

    @pytest.mark.parametrize("url", ISOLATED_URLS)
    def test_isolated_endpoints_are_permitted(self, url):
        assert is_production_like(url) is False

    def test_remote_host_is_always_production_like(self):
        # The previous heuristic allowed this: non-5432 port, non-production name.
        assert is_production_like(
            "postgresql://u@db.example.com:6000/some_db") is True

    def test_production_name_on_any_port_is_production_like(self):
        # The previous heuristic "assumed isolated" for non-5432 ports.
        assert is_production_like(
            "postgresql://u@127.0.0.1:6000/shunya_os") is True

    def test_isolated_marker_lifts_port_restriction(self):
        assert is_production_like(
            "postgresql://u@127.0.0.1:5432/shunya_ci_test") is False


class TestExecutionContext:
    def test_postgres_url_outside_test_context_is_refused(self, monkeypatch):
        for var in ("PYTEST_CURRENT_TEST", "SHUNYA_REQUIRE_ISOLATED_DB",
                    "SHUNYA_ENV", "FLASK_ENV"):
            monkeypatch.delenv(var, raising=False)
        assert in_test_context() is False
        with pytest.raises(RuntimeError, match="execution context"):
            assert_isolated_database(
                "postgresql://u@127.0.0.1:5445/shunya_g121", context="script")

    def test_sqlite_never_needs_a_declared_context(self, monkeypatch):
        for var in ("PYTEST_CURRENT_TEST", "SHUNYA_REQUIRE_ISOLATED_DB",
                    "SHUNYA_ENV", "FLASK_ENV"):
            monkeypatch.delenv(var, raising=False)
        assert assert_isolated_database("sqlite:///:memory:", context="script") is True

    def test_declared_test_context_is_accepted(self, monkeypatch):
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        monkeypatch.setenv("SHUNYA_ENV", "test")
        assert in_test_context() is True
        assert assert_isolated_database(
            "postgresql://u@127.0.0.1:5445/shunya_g121", context="script") is True

    def test_certification_opt_in_is_accepted(self, monkeypatch):
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        monkeypatch.delenv("SHUNYA_ENV", raising=False)
        monkeypatch.setenv("SHUNYA_REQUIRE_ISOLATED_DB", "1")
        assert in_test_context() is True

    def test_production_context_is_refused_even_with_marker(self, monkeypatch):
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        monkeypatch.delenv("SHUNYA_REQUIRE_ISOLATED_DB", raising=False)
        monkeypatch.setenv("SHUNYA_ENV", "production")
        assert in_test_context() is False
        with pytest.raises(RuntimeError):
            assert_isolated_database(
                "postgresql://u@127.0.0.1:5433/shunya_cert", context="script")

    def test_production_url_beats_a_declared_test_context(self, monkeypatch):
        monkeypatch.setenv("SHUNYA_ENV", "test")
        with pytest.raises(RuntimeError, match="production-like"):
            assert_isolated_database(
                "postgresql://u@127.0.0.1:5432/shunya_os", context="test")


class TestNoSilentProductionFallback:
    def test_conftest_requires_an_explicit_database_url(self):
        """The suite must never inherit a DATABASE_URL implicitly."""
        import pathlib

        conftest = pathlib.Path(__file__).parent / "conftest.py"
        source = conftest.read_text(encoding="utf-8")
        assert "DATABASE_URL is not set" in source, (
            "conftest must fail closed when DATABASE_URL is absent")
        assert 'os.environ.get("DATABASE_URL", "")' in source
        # no default is substituted before the guard runs
        guard_at = source.index("_assert_isolated(_DATABASE_URL")
        assignment_at = source.index('_DATABASE_URL = os.environ.get')
        assert assignment_at < guard_at

    def test_guard_module_defines_no_default_url(self):
        """The guard must not supply a connection string of its own.

        It may mention an example URL inside an error message; what it must never
        do is read DATABASE_URL with a fallback, or assign a default.
        """
        text = open(db_guard.__file__, encoding="utf-8").read()
        assert 'os.environ.get("DATABASE_URL"' not in text
        assert "os.environ.get('DATABASE_URL'" not in text
        assert "DATABASE_URL =" not in text
        # No module-level constant holding a connection string.
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("DEFAULT_", "FALLBACK_")) and "=" in stripped:
                assert "://" not in stripped, f"fallback URL defined: {stripped}"


class TestIsolatedClusterSemantics:
    """The disposable instances used by certification must stay usable."""

    def test_disposable_loopback_ports_are_allowed(self):
        for port in (5433, 5445, 5446):
            url = f"postgresql://postgres@127.0.0.1:{port}/shunya_g121"
            assert is_production_like(url) is False, url

    def test_unknown_driver_fails_closed(self):
        assert is_production_like("mysql://u@127.0.0.1:3306/db") is True
        assert is_production_like("") is False
