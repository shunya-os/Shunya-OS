"""Email configuration truth: configured ≠ accepted ≠ delivered.

G1.15 root cause: the integration registry probed `GET /keys` (an account
administration endpoint) and reported HTTP 401 for a valid sending key, while
the send path (`POST /emails`) accepted messages. The probe no longer calls a
network endpoint; acceptance is asserted only from the send response, and
delivery is never claimed.
"""
from __future__ import annotations

import pytest

from app.integration.providers import email_integration as mod


def _clear_provider_env(monkeypatch):
    for key in ("RESEND_API_KEY", "EMAIL_USER", "EMAIL_PASSWORD",
                "GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN"):
        monkeypatch.delenv(key, raising=False)


def test_resend_configuration_is_recognised_without_network_probe(monkeypatch):
    _clear_provider_env(monkeypatch)
    monkeypatch.setenv("RESEND_API_KEY", "test-key-not-real")

    def _forbidden(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("configuration check must not call the provider network")

    monkeypatch.setattr(mod.requests, "get", _forbidden)
    provider = mod.EmailIntegration()
    ok, detail = provider._probe_result()
    assert ok is True
    assert "configured" in detail.lower()


def test_no_provider_configuration_is_reported_honestly(monkeypatch):
    _clear_provider_env(monkeypatch)
    provider = mod.EmailIntegration()
    ok, detail = provider._probe_result()
    assert ok is False
    assert "no " in detail.lower() and "configured" in detail.lower()


def test_connect_marks_configured_provider_connected(monkeypatch):
    _clear_provider_env(monkeypatch)
    monkeypatch.setenv("RESEND_API_KEY", "test-key-not-real")
    provider = mod.EmailIntegration()
    assert provider.connect() is True
    assert provider.status["connected"] is True


def test_provider_acceptance_is_not_delivery(monkeypatch):
    """The delivery state vocabulary must not collapse acceptance into delivery."""
    from app.communication.email_core import EmailDeliveryState
    # Acceptance and delivery are distinct states; a provider 2xx may only
    # ever record ACCEPTED. DELIVERED requires separate delivery evidence.
    assert EmailDeliveryState.ACCEPTED.value == "accepted"
    assert EmailDeliveryState.DELIVERED.value == "delivered"
    assert EmailDeliveryState.ACCEPTED is not EmailDeliveryState.DELIVERED
