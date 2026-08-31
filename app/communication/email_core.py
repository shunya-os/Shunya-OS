"""
email_core.py — Canonical email send + read module.

Consolidated from:
- adapters/email_adapter.py (guardrailed stub)
- communication/email.py (legacy SMTP with print())
- communication/providers/email_provider.py (active EmailProvider)

All email operations go through this module.
Direct sends always require is_human_triggered=True.

Providers (in priority order):
  1. Resend (EMAIL_PROVIDER=resend + RESEND_API_KEY) — transactional API
  2. SMTP (EMAIL_USER/EMAIL_PASSWORD/EMAIL_HOST/EMAIL_PORT)
  3. Log-only fallback (never silently swallows)
"""

import json
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests

logger = logging.getLogger(__name__)

_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
_PORT = int(os.environ.get("EMAIL_PORT", "587"))
_USER = os.environ.get("EMAIL_USER", "")
_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
_FROM = os.environ.get("EMAIL_FROM", _USER or "shunya@localhost")
_PROVIDER = os.environ.get("EMAIL_PROVIDER", "smtp").lower()
_RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
_RESEND_FROM = os.environ.get("RESEND_FROM", "SHUNYA <onboarding@resend.dev>")


def _send_via_resend(to: str, subject: str, body: str) -> dict:
    """Send via Resend transactional API. Returns (status, error)."""
    if not _RESEND_API_KEY:
        return {"status": "unconfigured", "error": "RESEND_API_KEY not set"}
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {_RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": _RESEND_FROM,
                "to": [to],
                "subject": subject,
                "text": body,
            },
            timeout=15,
        )
        if resp.status_code >= 400:
            detail = resp.text[:300]
            logger.error("Resend API error %s: %s", resp.status_code, detail)
            return {"status": "failed", "error": f"Resend API {resp.status_code}: {detail}"}
        logger.info("Email sent via Resend to %s: %s", to, subject)
        return {"status": "sent"}
    except Exception as e:
        logger.error("Resend send failed to %s: %s", to, e)
        return {"status": "failed", "error": str(e)}


def send(
    to: str,
    subject: str,
    body: str,
    cc: list = None,
    is_human_triggered: bool = False,
) -> dict:
    """Send email via the configured provider. Falls back to log when credentials are missing.

    REQUIRES is_human_triggered=True to actually send.
    Without it, the message is logged and blocked (guardrail).

    Returns dict with status (sent|logged|failed|blocked|unconfigured).
    """
    if not is_human_triggered:
        logger.warning("Email send blocked: is_human_triggered=False. Logging instead.")
        logger.info("[EMAIL BLOCKED] To: %s | Subject: %s", to, subject)
        return {
            "status": "blocked",
            "to": to,
            "reason": "Human approval required (is_human_triggered=False)",
            "channel": "email",
        }

    # ── Provider 1: Resend (transactional API) ──
    if _PROVIDER == "resend":
        if _RESEND_API_KEY:
            result = _send_via_resend(to, subject, body)
            if result["status"] == "sent":
                result.update({"to": to, "subject": subject, "channel": "email"})
                return result
            # Resend configured but failed — DO NOT silently fall back to log.
            # The caller must see delivery failure (truthful state).
            logger.error("Resend delivery failed for %s: %s", to, result.get("error"))
            result.update({"to": to, "subject": subject, "channel": "email"})
            return result
        logger.warning("EMAIL_PROVIDER=resend but RESEND_API_KEY not set — logging instead of sending")
        logger.info("[EMAIL LOG] To: %s | Subject: %s | Body: %s", to, subject, body[:200])
        return {
            "status": "logged",
            "to": to,
            "subject": subject,
            "channel": "email",
            "note": "RESEND_API_KEY not configured",
        }

    # ── Provider 2: SMTP ──
    if not _USER or not _PASSWORD:
        logger.warning("EMAIL_USER/PASSWORD not set — logging instead of sending")
        logger.info("[EMAIL LOG] To: %s | Subject: %s | Body: %s", to, subject, body[:200])
        return {
            "status": "logged",
            "to": to,
            "subject": subject,
            "channel": "email",
            "note": "no credentials configured",
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = _FROM
        msg["To"] = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg.attach(MIMEText(body, "plain", "utf-8"))

        recipients = [to] + (cc or [])
        with smtplib.SMTP(_HOST, _PORT, timeout=15) as server:
            server.starttls()
            server.login(_USER, _PASSWORD)
            server.sendmail(_FROM, recipients, msg.as_string())

        logger.info("Email sent to %s: %s", to, subject)
        return {
            "status": "sent",
            "to": to,
            "subject": subject,
            "channel": "email",
        }

    except Exception as e:
        logger.error("Email send failed to %s: %s", to, e)
        return {
            "status": "failed",
            "to": to,
            "error": str(e),
            "channel": "email",
        }