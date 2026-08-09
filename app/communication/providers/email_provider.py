"""EmailProvider — real SMTP email delivery via CommunicationProvider interface.

Implements CommunicationProvider._do_send() with actual SMTP relay.
When EMAIL_USER/PASSWORD are not configured, falls back to logging.
"""

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.communication.base import CommunicationProvider

logger = logging.getLogger(__name__)


class EmailProvider(CommunicationProvider):
    """Sends email via SMTP. Gracefully degrades to log when unconfigured."""

    def __init__(self):
        self.host = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
        self.port = int(os.environ.get("EMAIL_PORT", "587"))
        self.user = os.environ.get("EMAIL_USER", "")
        self.password = os.environ.get("EMAIL_PASSWORD", "")
        self.from_addr = os.environ.get("EMAIL_FROM", self.user or "shunya@localhost")

    def _do_send(self, to: str, message: str, metadata: dict = None) -> dict:
        """Send email via SMTP. Falls back to log when credentials are missing.

        Args:
            to: Recipient email address.
            message: Email body text.
            metadata: Optional dict with keys:
                - subject: Email subject line (default: "Update from SHUNYA")
                - cc: List of CC recipients

        Returns:
            dict with status (sent|logged|failed), to, channel, error (if any).
        """
        metadata = metadata or {}
        subject = metadata.get("subject", "Update from SHUNYA")
        cc = metadata.get("cc")

        # Check if we have credentials
        if not self.user or not self.password:
            logger.warning("EMAIL_USER/PASSWORD not set — logging email instead of sending")
            msg = f"[EMAIL LOG] To: {to} | Subject: {subject} | Body: {message[:200]}"
            logger.info(msg)
            print(msg)
            return {
                "status": "logged",
                "to": to,
                "subject": subject,
                "channel": "email",
                "note": "no credentials configured",
            }

        # Send via real SMTP
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_addr
            msg["To"] = to
            msg["Subject"] = subject
            if cc:
                msg["Cc"] = ", ".join(cc)
            msg.attach(MIMEText(message, "plain", "utf-8"))

            recipients = [to] + (cc or [])
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_addr, recipients, msg.as_string())

            logger.info("Email sent to %s: %s", to, subject)
            print(f"[EMAIL SENT] To: {to} | Subject: {subject}")
            return {
                "status": "sent",
                "to": to,
                "subject": subject,
                "channel": "email",
            }

        except Exception as e:
            logger.error("Email send failed to %s: %s", to, e)
            print(f"[EMAIL FAILED] To: {to} | Error: {e}")
            return {
                "status": "failed",
                "to": to,
                "error": str(e),
                "channel": "email",
            }