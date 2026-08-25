"""
SHUNYA Email Service — notification delivery for verification, reset, onboarding.

Architecture:
  - In development: prints verification URLs to logs (user can click the printed link)
  - In production: sends via SMTP (env SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS)
  - Fallback: logs the URL to stdout for demo/testing environments

All email rendering uses plain-text templates.
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)

BASE_URL = os.environ.get("SHUNYA_BASE_URL", os.environ.get("PUBLIC_URL", "http://127.0.0.1:5001"))


def _get_smtp_config() -> Optional[dict]:
    """Read SMTP config from environment. Returns None if not configured."""
    host = os.environ.get("SMTP_HOST") or os.environ.get("MAIL_HOST") or os.environ.get("EMAIL_HOST")
    if not host:
        return None
    return {
        "host": host,
        "port": int(os.environ.get("SMTP_PORT") or os.environ.get("MAIL_PORT", "587")),
        "user": os.environ.get("SMTP_USER") or os.environ.get("MAIL_USER", ""),
        "password": os.environ.get("SMTP_PASS") or os.environ.get("MAIL_PASSWORD", ""),
        "from": os.environ.get("SMTP_FROM") or "shunya@shunyaos.com",
        "tls": os.environ.get("SMTP_TLS", "true").lower() == "true",
    }


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email. Logs the content if SMTP not configured."""
    smtp = _get_smtp_config()
    if smtp:
        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = smtp["from"]
            msg["To"] = to
            with smtplib.SMTP(smtp["host"], smtp["port"], timeout=15) as server:
                if smtp["tls"]:
                    server.starttls()
                if smtp["user"] and smtp["password"]:
                    server.login(smtp["user"], smtp["password"])
                server.send_message(msg)
            logger.info("Email sent to %s: %s", to, subject)
            return True
        except Exception as e:
            logger.warning("Failed to send email to %s: %s", to, e)
            # Fall through to logging
    # Fallback: log the email content (works for dev/demo)
    logger.info("=== EMAIL TO: %s ===", to)
    logger.info("Subject: %s", subject)
    logger.info("Body:\n%s", body)
    logger.info("=== END EMAIL ===")
    return True


# ── Template Builders ──────────────────────────────────────────────────


def build_verification_email(to: str, token: str) -> tuple:
    """Build verification email. Returns (subject, body)."""
    verify_url = f"{BASE_URL}/auth/verify-email?token={token}"
    subject = "Verify your SHUNYA email address"
    body = f"""Hello,

Thank you for creating your SHUNYA account.

To verify your email address and activate your workspace, click the link below:

{verify_url}

This link expires in 24 hours and can only be used once.

If you did not create a SHUNYA account, please ignore this email.

— SHUNYA
"""
    return subject, body


def build_reset_email(to: str, token: str) -> tuple:
    """Build password reset email. Returns (subject, body)."""
    reset_url = f"{BASE_URL}/auth/reset-password?token={token}"
    subject = "Reset your SHUNYA password"
    body = f"""Hello,

A password reset was requested for your SHUNYA account.

To reset your password, click the link below:

{reset_url}

This link expires in 1 hour and can only be used once.

If you did not request this reset, please ignore this email. Your password will remain unchanged.

— SHUNYA
"""
    return subject, body


def build_onboarding_complete_email(email: str, workspace_name: str) -> tuple:
    """Build onboarding completion confirmation. Returns (subject, body)."""
    subject = "Your SHUNYA is ready"
    body = f"""Hello,

Your SHUNYA workspace is ready.

Workspace: {workspace_name}

You can now access SHUNYA at:
{BASE_URL}

Your workspace includes:
- AI-powered conversations and memory
- Personal tasks, files, and knowledge
- Finance, outputs, and reports
- Full SHUNYA intelligence

If you need help getting started, visit:
{BASE_URL}/support

— SHUNYA
"""
    return subject, body