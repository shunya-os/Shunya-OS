"""Fail-closed email-transport isolation for declared test / CI runs.

Why this exists
---------------
G1.22 INC-5: a test process inherited the production Resend key and issued a
real send to ``api.resend.com`` (observed as ``Email accepted by Resend`` plus
429 retries). The harness fix removes the key before the app is imported, and
G1.23 stopped the factory from reloading the host ``.env``. Both are necessary
but neither is a boundary the *application* can enforce: any future harness,
script or certification runner that boots the factory with ambient credentials
would send real mail again.

This module is that boundary. ``create_app()`` calls it whenever the process has
declared itself a test / CI run; an unsafe transport raises rather than silently
sending.

What is "unsafe"
----------------
* ``EMAIL_PROVIDER=resend`` **with** an API key — reaches the public Resend API.
* ``EMAIL_PROVIDER=smtp`` with credentials **and** a non-loopback host — reaches
  an external SMTP server.
* An unrecognised provider name — the guard cannot reason about it, so it fails
  closed instead of assuming it is harmless.

What is safe
------------
* A provider with no credentials configured: the send path returns ``logged``
  and performs no network I/O (the project's documented non-sending mode).
* ``EMAIL_PROVIDER=smtp`` pointed at a **loopback** host with credentials: this
  is the local STARTTLS capture server used to verify the delivery journey. It
  is a non-production sink on the same machine and cannot reach the internet.
* An explicit non-sending provider name (``log`` / ``console`` / ``none``).

No secret value is ever read, formatted or logged here — only whether a
credential is present and which host would be contacted.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})
NON_SENDING_PROVIDERS = frozenset({"log", "console", "none", "disabled", "null"})
NETWORK_PROVIDERS = frozenset({"resend", "smtp"})


class EmailTransportIsolationError(RuntimeError):
    """Raised when a declared test run would use a live external mail transport."""


def _email_core():
    """Import the canonical send module lazily (it imports ``app``)."""
    from app.communication import email_core

    return email_core


def email_transport_state(core: Any | None = None) -> dict:
    """Non-secret description of the configured transport.

    Reports *presence* of credentials, never their value, and the destination
    host — which is exactly what an evidence log needs to prove isolation.
    """
    core = core or _email_core()
    provider = str(getattr(core, "_PROVIDER", "") or "").strip().lower()
    host = str(getattr(core, "_HOST", "") or "").strip()
    return {
        "provider": provider,
        "host": host,
        "has_resend_key": bool(getattr(core, "_RESEND_API_KEY", "") or ""),
        "has_smtp_credentials": bool(
            getattr(core, "_USER", "") and getattr(core, "_PASSWORD", "")
        ),
        "host_is_loopback": host.lower() in LOOPBACK_HOSTS,
    }


def isolation_verdict(state: dict) -> tuple[bool, str]:
    """Return ``(safe, reason)`` for a transport state. Pure and testable."""
    provider = state.get("provider", "")

    if provider in NON_SENDING_PROVIDERS:
        return True, "provider_explicitly_non_sending"

    if provider == "resend":
        if state.get("has_resend_key"):
            return False, "resend_api_key_present_in_declared_test_run"
        return True, "resend_without_key_logs_only"

    if provider == "smtp":
        if not state.get("has_smtp_credentials"):
            return True, "smtp_without_credentials_logs_only"
        if state.get("host_is_loopback"):
            return True, "smtp_loopback_capture"
        return False, "smtp_external_host_with_credentials"

    return False, f"unrecognised_email_provider:{provider or 'unset'}"


def assert_isolated_email_transport(core: Any | None = None) -> dict:
    """Raise unless the configured transport cannot reach an external provider.

    Returns the (non-secret) state plus the verdict reason so a caller can log
    the *decision* without logging any credential.
    """
    state = email_transport_state(core)
    safe, reason = isolation_verdict(state)
    if not safe:
        logger.error(
            "Refusing to start a declared test run with a live email transport: "
            "provider=%s host=%s reason=%s",
            state["provider"], state["host"], reason,
        )
        raise EmailTransportIsolationError(
            "A declared test run may not use a live external email transport "
            f"({reason}). Configure EMAIL_PROVIDER=smtp with no credentials, or a "
            "loopback capture server, or set an explicit non-sending provider."
        )
    state["isolation"] = reason
    return state
