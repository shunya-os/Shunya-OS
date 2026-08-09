"""
email_core.py — Canonical email send + read module.

Consolidated from:
- adapters/email_adapter.py (guardrailed stub)
- communication/email.py (legacy SMTP with print())
- communication/providers/email_provider.py (active EmailProvider)

All email operations go through this module.
Direct sends always require is_human_triggered=True.
"""

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
_PORT = int(os.environ.get("EMAIL_PORT", "587"))
_USER = os.environ.get("EMAIL_USER", "")
_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
_FROM = os.environ.get("EMAIL_FROM", _USER or "shunya@localhost")


def send(
    to: str,
    subject: str,
    body: str,
    cc: list = None,
    is_human_triggered: bool = False,
) -> dict:
    """Send email via SMTP. Falls back to log when credentials are missing.

    REQUIRES is_human_triggered=True to actually send.
    Without it, the message is logged and blocked (guardrail).

    Returns dict with status (sent|logged|failed|blocked).
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