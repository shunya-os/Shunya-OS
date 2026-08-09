"""Email communication stub — logs intent, no real send."""

import logging

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str, cc: list = None):
    """Log email intent. No real API integration yet."""
    msg = f"[EMAIL] To: {to} | Subject: {subject} | Body: {body[:200]}"
    logger.info(msg)
    print(msg)
    return {"status": "logged", "to": to, "subject": subject, "channel": "email"}