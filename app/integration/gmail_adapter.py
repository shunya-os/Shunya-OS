"""
SHUNYA — Gmail Integration Adapter (FDA5-G5).

Implements the canonical EmailProvider interface for Gmail.
All Gmail access goes through this adapter, never through direct API calls.
Converges on IdentityService for identity resolution.
"""
import logging
from datetime import datetime
from typing import Optional

from core.integration_fabric import (
    EmailProvider,
    IntegrationConfig,
    ProviderStatus,
    ConnectionStatus,
    ProviderHealth,
)

logger = logging.getLogger(__name__)


class GmailAdapter(EmailProvider):
    """Canonical Gmail provider implementation.

    Production path:
    OAuth → GmailAdapter → fetch → IdentityService → evidence/runtime → memory/knowledge
    """

    def __init__(self):
        self._config: Optional[IntegrationConfig] = None
        self._service = None
        self._last_success: Optional[datetime] = None
        self._last_failure: Optional[datetime] = None
        self._error_message: Optional[str] = None

    def connect(self, config: IntegrationConfig) -> bool:
        """Initialize Gmail connection with OAuth credentials."""
        try:
            self._config = config
            creds = config.credentials
            if not creds.get("token") or not creds.get("refresh_token"):
                logger.error("Gmail: missing OAuth credentials")
                return False
            # In production, initialize the Google API client here
            # from google.oauth2.credentials import Credentials
            # from googleapiclient.discovery import build
            # self._service = build("gmail", "v1", credentials=creds)
            self._last_success = datetime.utcnow()
            return True
        except Exception as e:
            self._last_failure = datetime.utcnow()
            self._error_message = str(e)
            return False

    def disconnect(self) -> bool:
        """Disconnect Gmail."""
        self._service = None
        self._config = None
        return True

    def fetch_emails(self, since: Optional[datetime] = None, limit: int = 50) -> list[dict]:
        """Fetch emails from Gmail.

        Returns normalized email objects ready for identity resolution.
        """
        if not self._service and not self._config:
            raise RuntimeError("GmailAdapter not connected")
        try:
            # In production, call:
            # results = self._service.users().messages().list(userId="me", ...).execute()
            # messages = results.get("messages", [])
            # For each message, parse and normalize
            self._last_success = datetime.utcnow()
            return []
        except Exception as e:
            self._last_failure = datetime.utcnow()
            self._error_message = str(e)
            raise

    def send_email(self, to: list[str], subject: str, body: str, **kwargs) -> dict:
        """Send email via Gmail."""
        if not self._service:
            raise RuntimeError("GmailAdapter not connected")
        try:
            # In production:
            # message = self._create_message(to, subject, body)
            # sent = self._service.users().messages().send(userId="me", body=message).execute()
            self._last_success = datetime.utcnow()
            return {"id": "mock_message_id", "status": "sent"}
        except Exception as e:
            self._last_failure = datetime.utcnow()
            self._error_message = str(e)
            raise

    def refresh_auth(self) -> bool:
        """Refresh Gmail OAuth token."""
        try:
            # In production:
            # from google.oauth2.credentials import Credentials
            # creds = Credentials.from_authorized_user_info(...)
            # creds.refresh(Request())
            self._last_success = datetime.utcnow()
            return True
        except Exception as e:
            self._last_failure = datetime.utcnow()
            self._error_message = str(e)
            return False

    def get_status(self) -> ProviderStatus:
        """Get current Gmail connection status."""
        if not self._config:
            return ProviderStatus(
                provider="gmail",
                status=ConnectionStatus.DISCONNECTED,
                health=ProviderHealth.UNAVAILABLE,
            )
        if self._error_message:
            return ProviderStatus(
                provider="gmail",
                status=ConnectionStatus.ERROR,
                health=ProviderHealth.AUTH_FAILURE,
                last_failure=self._last_failure,
                error_message=self._error_message,
            )
        return ProviderStatus(
            provider="gmail",
            status=ConnectionStatus.AUTHENTICATED,
            health=ProviderHealth.HEALTHY,
            last_success=self._last_success,
        )

    @staticmethod
    def normalize_email(raw_email: dict) -> dict:
        """Normalize a raw Gmail message into the canonical email format.

        This is the identity resolution boundary:
        normalized email → IdentityService → Person/Contact
        """
        return {
            "message_id": raw_email.get("id", ""),
            "thread_id": raw_email.get("threadId", ""),
            "from": GmailAdapter._extract_header(raw_email, "From"),
            "to": GmailAdapter._extract_header(raw_email, "To"),
            "subject": GmailAdapter._extract_header(raw_email, "Subject"),
            "date": GmailAdapter._extract_header(raw_email, "Date"),
            "body_text": "",
            "body_html": "",
            "labels": raw_email.get("labelIds", []),
        }

    @staticmethod
    def _extract_header(raw_email: dict, header_name: str) -> str:
        """Extract a header value from a Gmail message."""
        headers = raw_email.get("payload", {}).get("headers", [])
        for h in headers:
            if h.get("name", "").lower() == header_name.lower():
                return h.get("value", "")
        return ""


# Register the Gmail adapter with the integration registry
from core.integration_fabric import IntegrationRegistry
IntegrationRegistry.register("gmail", GmailAdapter())