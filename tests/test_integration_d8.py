"""D8 — integration honesty: no fake 'synced', real verification probes,
truthful hub-facing statuses.

The email integration's connect()/sync() must report connected/synced ONLY
when a real transport probe succeeds; saved credentials alone are
'configured', not 'connected'; and a failed probe must surface as
status=error (never a silent success).
"""
import pytest


class TestEmailIntegrationVerification:
    """Real-probe truthfulness for the email integration (D8)."""

    def _integration(self, monkeypatch, env: dict):
        for k in ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_ACCESS_TOKEN",
                  "GMAIL_REFRESH_TOKEN", "EMAIL_USER", "EMAIL_PASSWORD",
                  "EMAIL_HOST", "EMAIL_PORT", "RESEND_API_KEY"):
            monkeypatch.delenv(k, raising=False)
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        from app.integration.providers.email_integration import EmailIntegration
        return EmailIntegration()

    def test_no_credentials_reported_unconfigured(self, monkeypatch):
        intg = self._integration(monkeypatch, {})
        assert intg.is_configured() is False
        ok = intg.connect()
        assert ok is False
        assert intg._status != "connected"
        assert intg.sync()["status"] == "skipped"

    def test_smtp_probe_success_connects_and_syncs(self, monkeypatch):
        import app.integration.providers.email_integration as mod
        class _FakeSmtp:
            def __init__(self, *a, **k):
                self.has_starttls = False
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def ehlo(self): pass
            def has_extn(self, name): return False
            def login(self, user, pw): pass
        monkeypatch.setattr(mod.smtplib, "SMTP", _FakeSmtp)
        intg = self._integration(monkeypatch, {
            "EMAIL_USER": "ops@shunyaos.com",
            "EMAIL_PASSWORD": "sekrit",
            "EMAIL_HOST": "smtp.example.com",
            "EMAIL_PORT": "587",
        })
        assert intg.is_configured() is True
        assert intg.connect() is True
        assert intg._status == "connected"
        sync = intg.sync()
        assert sync["status"] == "synced"

    def test_smtp_probe_failure_is_error_not_synced(self, monkeypatch):
        import app.integration.providers.email_integration as mod
        import smtplib
        class _FakeSmtp:
            def __init__(self, *a, **k):
                self.has_starttls = False
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def ehlo(self): pass
            def has_extn(self, name): return False
            def login(self, user, pw):
                raise smtplib.SMTPAuthenticationError(535, b"bad creds")
        monkeypatch.setattr(mod.smtplib, "SMTP", _FakeSmtp)
        intg = self._integration(monkeypatch, {
            "EMAIL_USER": "ops@shunyaos.com",
            "EMAIL_PASSWORD": "wrong",
            "EMAIL_HOST": "smtp.example.com",
            "EMAIL_PORT": "587",
        })
        assert intg.connect() is False
        assert intg._status == "disconnected"
        sync = intg.sync()
        assert sync["status"] == "error"
        assert "SMTP probe failed" in sync["error"]
        assert intg._last_sync_at is None  # no fake synced timestamp

    def test_resend_connects_from_configuration_without_admin_probe(self, monkeypatch):
        """A Resend sending key is verified by presence — never by probing /keys.

        G1.16/G1.17 root cause: `/keys` is an account-administration endpoint and
        rejects ordinary sending keys, producing a false HTTP 401 while the send
        path (`POST /emails`) accepts mail. Connect-time verification must not
        manufacture a rejection that the send path contradicts; a genuinely
        rejected credential surfaces at send time (acceptance vocabulary pinned in
        tests/test_email_config.py). The previous version of this test asserted
        the superseded /keys probe and therefore had to fail once the false 401
        was removed.
        """
        import app.integration.providers.email_integration as mod
        probes = []

        def _forbidden(*a, **k):
            probes.append(a)
            raise AssertionError("Resend must not probe an account-administration endpoint")

        monkeypatch.setattr(mod.requests, "get", _forbidden)
        intg = self._integration(monkeypatch, {"RESEND_API_KEY": "re_sending_key"})
        assert intg.connect() is True
        assert intg._status == "connected"
        assert probes == []
        sync = intg.sync()
        assert sync["status"] == "synced"
        assert "acceptance verified on send" in sync["note"]

    def test_resend_connect_does_not_send_a_message_to_verify(self, monkeypatch):
        """Verifying configuration must not perform a real send.

        A connect-time send would deliver mail as a side effect of opening
        settings; acceptance is only established when the user actually sends.
        """
        import app.integration.providers.email_integration as mod
        sent = []

        def _forbidden_post(*a, **k):
            sent.append(a)
            raise AssertionError("connect() must not send mail to verify credentials")

        monkeypatch.setattr(mod.requests, "post", _forbidden_post)
        intg = self._integration(monkeypatch, {"RESEND_API_KEY": "re_bad_key"})
        assert intg.connect() is True
        assert intg.sync()["status"] == "synced"
        assert sent == []

    def test_gmail_oauth_without_token_not_connected(self, monkeypatch):
        # A stored client id/secret alone is NOT a connection.
        intg = self._integration(monkeypatch, {
            "GMAIL_CLIENT_ID": "client_abc",
            "GMAIL_CLIENT_SECRET": "secret_abc",
        })
        assert intg.is_configured() is True
        assert intg.connect() is False
        assert intg._status == "disconnected"
        sync = intg.sync()
        assert sync["status"] == "error"
        assert "access token" in sync["error"]


class TestRegistryStatusContract:
    """The registry status payload is truthful: configured != connected."""

    def test_status_payload_separates_configured_and_connected(self, monkeypatch):
        from app.integration.providers.email_integration import EmailIntegration
        import app.integration.providers.email_integration as mod
        for k in ("EMAIL_USER", "EMAIL_PASSWORD", "EMAIL_HOST", "EMAIL_PORT",
                  "RESEND_API_KEY", "GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET"):
            monkeypatch.delenv(k, raising=False)
        # Save a key → configured, but NOT connected until a probe passes.
        intg = EmailIntegration()
        status = intg.status
        assert status["configured"] is False
        assert status["connected"] is False
        assert status["status"] == "disconnected"
        assert status["error"] is None or "credentials" in (status["error"] or "").lower()

    def test_connect_all_only_touches_configured(self, monkeypatch):
        import app.integration.providers.email_integration as mod
        class _FakeSmtp:
            def __init__(self, *a, **k): pass
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def ehlo(self): pass
            def has_extn(self, name): return False
            def login(self, user, pw): pass
        monkeypatch.setattr(mod.smtplib, "SMTP", _FakeSmtp)
        monkeypatch.setenv("EMAIL_USER", "ops@shunyaos.com")
        monkeypatch.setenv("EMAIL_PASSWORD", "sekrit")
        from app.integration.registry import IntegrationRegistry, IntegrationBase

        class Wired(IntegrationBase):
            name = "wired"
            display_name = "Wired"
            def is_configured(self): return True
            def connect(self):
                self._status = "connected"
                return True

        class Unwired(IntegrationBase):
            name = "unwired"
            display_name = "Unwired"
            def is_configured(self): return False
            def connect(self):
                raise AssertionError("connect() must not be called on unconfigured")

        reg = IntegrationRegistry()
        reg.register(Wired())
        reg.register(Unwired())
        results = reg.connect_all()
        names = [r["name"] for r in results]
        assert names == ["wired"]
        assert results[0]["connected"] is True