"""EmailProvider — real SMTP email delivery via CommunicationProvider interface.

Implements CommunicationProvider._do_send() using email_core (canonical email module).
When EMAIL_USER/PASSWORD are not configured, falls back to logging.
"""

import logging
import os

from app.communication.base import CommunicationProvider
from app.communication.email_core import send as core_send

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
        """Send email via SMTP using email_core.

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

        # Override env vars with instance settings
        import os as _os
        orig = {}
        for k, v in [("EMAIL_HOST", self.host), ("EMAIL_PORT", str(self.port)),
                     ("EMAIL_USER", self.user), ("EMAIL_PASSWORD", self.password),
                     ("EMAIL_FROM", self.from_addr)]:
            orig[k] = _os.environ.get(k)
            _os.environ[k] = v

        try:
            result = core_send(to, subject, message, cc=cc, is_human_triggered=True)
            return result
        finally:
            # Restore original env vars
            for k, v in orig.items():
                if v is not None:
                    _os.environ[k] = v
                else:
                    _os.environ.pop(k, None)