"""Email — real SMTP send via env-configured relay."""

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
_FROM = os.environ.get("EMAIL_FROM", _USER)


def send_email(to: str, subject: str, body: str, cc: list = None):
    """Send email via SMTP. Falls back to log when credentials are missing."""
    if not _USER or not _PASSWORD:
        logger.warning("EMAIL_USER/PASSWORD not set — logging instead of sending")
        msg = f"[EMAIL] To: {to} | Subject: {subject} | Body: {body[:200]}"
        logger.info(msg)
        print(msg)
        return {"status": "logged", "to": to, "channel": "email", "note": "no credentials"}

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
        print(f"[EMAIL SENT] To: {to} | Subject: {subject}")
        return {"status": "sent", "to": to, "subject": subject, "channel": "email"}

    except Exception as e:
        logger.error("Email send failed to %s: %s", to, e)
        print(f"[EMAIL FAILED] To: {to} | Error: {e}")
        return {"status": "failed", "to": to, "error": str(e), "channel": "email"}