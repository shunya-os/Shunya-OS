"""G1.23 — the application factory must not reload production secrets in tests.

Root cause being guarded: ``create_app()`` called ``load_dotenv()``
unconditionally. ``load_dotenv`` *fills in missing* variables, so a harness that had
just removed ``RESEND_API_KEY`` had it silently restored from the host ``.env`` —
along with every other production secret the harness did not override. That is how
a live provider key reached a test log (G1.22 INC-5).

The fix is at the seam, not in the harness: a declared test run must not call
``load_dotenv`` at all. These tests pin that, and pin that a non-declared process
still loads it (development / production behaviour intact).

No real credential is used anywhere here: the canary is a synthetic environment
variable name and value.
"""

import os

import pytest

import app as app_pkg
from app import create_app


_ENV_VARS = ("PYTEST_CURRENT_TEST", "SHUNYA_ENVIRONMENT", "SHUNYA_ENV", "FLASK_ENV")


def _clear_declarations(monkeypatch):
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)


class TestDeclarationPredicate:
    def test_testing_config_override_declares_a_test_run(self, monkeypatch):
        assert app_pkg.declared_test_environment({"TESTING": True}) is True
        # The negative case must be isolated from pytest's own declaration,
        # otherwise it answers "yes" for a reason unrelated to the override.
        _clear_declarations(monkeypatch)
        assert app_pkg.declared_test_environment({"TESTING": False}) is False

    @pytest.mark.parametrize("env", ["test", "testing", "ci", "cert", "certification"])
    def test_environment_names_declare_a_test_run(self, env, monkeypatch):
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        monkeypatch.setenv("SHUNYA_ENV", env)
        assert app_pkg.declared_test_environment(None) is True

    @pytest.mark.parametrize("env", ["test", "testing", "ci", "cert", "certification"])
    def test_shunya_environment_declares_a_test_run(self, env, monkeypatch):
        """G1.24: the name /health and the SECRET_KEY guard read must count.

        Before this, ``SHUNYA_ENVIRONMENT=testing`` exempted a process from the
        SECRET_KEY production guard while still loading the host ``.env`` — the
        two guards disagreed about what a test run is.
        """
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        monkeypatch.delenv("SHUNYA_ENV", raising=False)
        monkeypatch.delenv("FLASK_ENV", raising=False)
        monkeypatch.setenv("SHUNYA_ENVIRONMENT", env)
        assert app_pkg.declared_test_environment(None) is True

    def test_production_is_not_a_test_run(self, monkeypatch):
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        monkeypatch.delenv("SHUNYA_ENVIRONMENT", raising=False)
        monkeypatch.setenv("SHUNYA_ENV", "production")
        assert app_pkg.declared_test_environment(None) is False

    def test_shunya_environment_production_is_not_a_test_run(self, monkeypatch):
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        monkeypatch.setenv("SHUNYA_ENVIRONMENT", "production")
        assert app_pkg.declared_test_environment(None) is False

    def test_pytest_itself_declares_a_test_run(self, monkeypatch):
        monkeypatch.delenv("SHUNYA_ENVIRONMENT", raising=False)
        monkeypatch.delenv("SHUNYA_ENV", raising=False)
        monkeypatch.delenv("FLASK_ENV", raising=False)
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/test_x.py::t (call)")
        assert app_pkg.declared_test_environment(None) is True

    def test_explicit_production_name_beats_inherited_pytest_marker(self, monkeypatch):
        """An explicit environment name wins over an inherited pytest marker."""
        monkeypatch.setenv("SHUNYA_ENVIRONMENT", "production")
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/test_x.py::t (call)")
        assert app_pkg.declared_test_environment(None) is False

    def test_nothing_declared_is_not_a_test_run(self, monkeypatch):
        _clear_declarations(monkeypatch)
        assert app_pkg.declared_test_environment(None) is False


class TestFactoryDoesNotReloadDotenvInTests:
    def test_test_mode_never_calls_load_dotenv(self, monkeypatch):
        calls = []
        monkeypatch.setattr(app_pkg, "load_dotenv",
                            lambda *a, **k: calls.append((a, k)))
        create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
        assert calls == [], (
            "create_app() loaded the host .env during a declared test run — that "
            "path reintroduces production secrets")

    def test_repeated_initialisation_stays_isolated(self, monkeypatch):
        calls = []
        monkeypatch.setattr(app_pkg, "load_dotenv",
                            lambda *a, **k: calls.append((a, k)))
        for _ in range(3):
            create_app({"TESTING": True,
                        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
        assert calls == []

    def test_non_test_process_still_loads_dotenv(self, monkeypatch):
        """The guard must not disable configuration loading for real deployments."""
        calls = []
        monkeypatch.setattr(app_pkg, "load_dotenv",
                            lambda *a, **k: calls.append((a, k)))
        for var in ("PYTEST_CURRENT_TEST", "SHUNYA_ENV", "FLASK_ENV"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("SECRET_KEY", "g123-non-test-secret-key-long-enough")
        try:
            create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
        except Exception:
            # Any later configuration guard may refuse; the loading decision is
            # made before the app object exists, which is what this test is about.
            pass
        assert calls, "a non-declared process must still load .env"


class TestProviderCannotRetainLiveCredentials:
    def test_canary_key_is_not_picked_up_by_the_email_module(self, monkeypatch):
        """Synthetic canary: proves no stale provider credential survives startup.

        The value is invented here and is not a credential. It is placed in the
        environment *after* the module under test was imported, so the only way it
        could reach the provider configuration is a re-read during startup.
        """
        from app.communication import email_core

        canary = "g123-canary-not-a-credential"
        monkeypatch.setenv("RESEND_API_KEY", canary)
        create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
        assert email_core._RESEND_API_KEY != canary
        assert email_core._PROVIDER == "smtp"

    def test_configured_provider_is_non_sending_in_tests(self):
        from app.communication import email_core

        assert email_core._PROVIDER == "smtp"
        assert not email_core._USER and not email_core._PASSWORD
        assert os.environ.get("EMAIL_PROVIDER") == "smtp"


class TestEmailTransportIsolationGuard:
    """G1.24: the factory refuses a live external mail transport in a test run.

    The harness already strips credentials; this pins the *application* boundary
    so a future harness cannot silently reintroduce the G1.22 INC-5 hazard.
    Every credential-shaped value here is synthetic.
    """

    def _verdict(self, **state):
        from app.communication.email_transport_guard import isolation_verdict

        base = {
            "provider": "smtp",
            "host": "127.0.0.1",
            "has_resend_key": False,
            "has_smtp_credentials": False,
            "host_is_loopback": True,
        }
        base.update(state)
        return isolation_verdict(base)

    def test_smtp_without_credentials_is_safe(self):
        safe, reason = self._verdict()
        assert safe is True
        assert reason == "smtp_without_credentials_logs_only"

    def test_resend_without_key_is_safe(self):
        safe, reason = self._verdict(provider="resend", has_resend_key=False)
        assert safe is True
        assert reason == "resend_without_key_logs_only"

    def test_resend_with_key_is_refused(self):
        safe, reason = self._verdict(provider="resend", has_resend_key=True)
        assert safe is False
        assert "resend_api_key_present" in reason

    def test_smtp_external_host_with_credentials_is_refused(self):
        safe, reason = self._verdict(
            host="smtp.example.com", host_is_loopback=False,
            has_smtp_credentials=True,
        )
        assert safe is False
        assert reason == "smtp_external_host_with_credentials"

    def test_smtp_loopback_capture_is_allowed(self):
        """The local STARTTLS capture server is a non-production sink."""
        safe, reason = self._verdict(has_smtp_credentials=True)
        assert safe is True
        assert reason == "smtp_loopback_capture"

    def test_unknown_provider_fails_closed(self):
        safe, reason = self._verdict(provider="telepathy")
        assert safe is False
        assert reason.startswith("unrecognised_email_provider")

    def test_explicit_non_sending_provider_is_allowed(self):
        safe, _reason = self._verdict(provider="log")
        assert safe is True

    def test_factory_refuses_to_boot_with_a_live_transport(self, monkeypatch):
        from app.communication import email_core
        from app.communication.email_transport_guard import (
            EmailTransportIsolationError,
        )

        monkeypatch.setattr(email_core, "_PROVIDER", "resend")
        monkeypatch.setattr(email_core, "_RESEND_API_KEY", "g124-canary-not-a-credential")
        with pytest.raises(EmailTransportIsolationError):
            create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})

    def test_factory_boots_with_the_isolated_transport(self):
        """The negative control: the real test transport must still boot."""
        app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
        assert app is not None


class TestSubprocessInheritance:
    """A child process spawned by a test inherits only the scrubbed environment."""

    def test_child_process_sees_no_email_credentials(self):
        import json
        import subprocess
        import sys

        probe = os.path.join(os.path.dirname(__file__), "_env_probe.py")
        completed = subprocess.run(
            [sys.executable, probe],
            capture_output=True, text=True, timeout=120,
            env=dict(os.environ),
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout.strip().splitlines()[-1])

        assert payload["present"]["RESEND_API_KEY"] is False
        assert payload["present"]["EMAIL_USER"] is False
        assert payload["present"]["EMAIL_PASSWORD"] is False
        assert payload["email_provider"] == "smtp"
        assert payload["declared_test_environment"] is True, payload
        assert payload["error"] == ""


class TestAlembicEntryPointHonoursTheSamePredicate:
    """[source] wiring check — alembic must not reload .env in a declared test run.

    ``migrations/env.py`` cannot be imported outside an alembic run, so this
    asserts the wiring in the source: the ``load_dotenv`` call is guarded by the
    application's own predicate rather than executed unconditionally.
    """

    def test_env_py_guards_load_dotenv(self):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "migrations", "env.py")
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        assert "declared_test_environment" in source
        guarded = source.split("declared_test_environment()", 1)[1]
        assert "load_dotenv()" in guarded
        # No unconditional module-level call: every load_dotenv() must be inside
        # the guarded branch.
        lines = [ln.strip() for ln in source.splitlines()]
        assert lines.count("load_dotenv()") == 1
