"""Email Adapter — simple SMTP relay with print fallback.

ACTIVATION-04: Outbound email adapter. When EMAIL_USER/PASSWORD are
configured, delegates to real SMTP; otherwise logs to console.
"""

import logging
import os
import smtplib
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send(effect: dict) -> dict:
    """Send an email. Uses SMTP when credentials exist, logs otherwise."""
    to = effect.get("to", "")
    subject = effect.get("subject", "Update from SHUNYA")
    body = effect.get("body", effect.get("message", ""))

    if not to:
        return {"status": "skipped", "reason": "missing to"}

    user = os.environ.get("EMAIL_USER", "")
    password = os.environ.get("EMAIL_PASSWORD", "")

    if user and password:
        return _send_smtp(to, subject, body, user, password)
    else:
        return _send_log(to, subject, body)


def _send_smtp(to: str, subject: str, body: str, user: str, password: str) -> dict:
    """Send via real SMTP relay."""
    host = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    port = int(os.environ.get("EMAIL_PORT", "587"))
    from_addr = os.environ.get("EMAIL_FROM", user)

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = from_addr
        msg["To"] = to
        msg["Subject"] = subject

        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(from_addr, [to], msg.as_string())

        logger.info("[Email SMTP] -> %s: %s", to, subject)
        print(f"[Email SMTP] -> {to}: {subject}")
        return {"status": "sent", "channel": "email_smtp"}

    except Exception as e:
        logger.error("[Email SMTP] failed -> %s: %s", to, e)
        return {"status": "failed", "channel": "email_smtp", "error": str(e)}


def _send_log(to: str, subject: str, body: str) -> dict:
    """Log fallback when no SMTP credentials."""
    logger.info("[Email Log] -> %s: %s", to, subject)
    print(f"[Email Log] -> {to}: {subject}")
    return {"status": "sent", "channel": "email_log"}