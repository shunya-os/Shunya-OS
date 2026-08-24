"""
SHUNYA — Gmail OAuth Service (Phase 3)
OAuth 2.0 flow for Gmail account connection with tenant-aware support.
"""
import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

from app import db
from app.tenant import Tenant
from app.communication.models import CommunicationSource
from app.communication.credentials import CredentialResolver


class OAuthConfig:
    """Gmail OAuth configuration from environment."""

    CLIENT_ID: str = os.getenv("GMAIL_CLIENT_ID", "")
    CLIENT_SECRET: str = os.getenv("GMAIL_CLIENT_SECRET", "")
    REDIRECT_URI: str = os.getenv("GMAIL_REDIRECT_URI", "")
    SCOPES: list = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.metadata",
    ]

    @classmethod
    def is_valid(cls) -> bool:
        """Check if OAuth configuration is complete."""
        return bool(cls.CLIENT_ID and cls.CLIENT_SECRET and cls.REDIRECT_URI)

    @classmethod
    def get_authorization_url(cls) -> str:
        """Build Google OAuth authorization URL."""
        if not cls.CLIENT_ID:
            raise ValueError("GMAIL_CLIENT_ID not configured")

        state = secrets.token_urlsafe(32)
        params = {
            "client_id": cls.CLIENT_ID,
            "redirect_uri": cls.REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(cls.SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}", state

    @classmethod
    def get_token_endpoint(cls) -> str:
        """Return the token exchange endpoint."""
        return "https://oauth2.googleapis.com/token"


class GmailOAuthService:
    """Handles Gmail OAuth 2.0 flow and credential management."""

    def __init__(self, session=None):
        self.session = session or db.session

    def initiate_flow(self, tenant_id: Optional[int] = None) -> dict:
        """Start OAuth flow and return authorization URL and state for storage."""
        if not OAuthConfig.is_valid():
            raise ValueError("Gmail OAuth not configured - check GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REDIRECT_URI")

        auth_url, state = OAuthConfig.get_authorization_url()

        # Store pending OAuth state
        if tenant_id:
            from app.communication.models import OAuthState
            oauth_state = OAuthState(
                tenant_id=tenant_id,
                provider="gmail",
                state=state,
                created_at=datetime.now(timezone.utc),
            )
            self.session.add(oauth_state)
            self.session.commit()

        return {"authorization_url": auth_url, "state": state}

    def exchange_code(self, code: str, state: str) -> dict:
        """Exchange authorization code for tokens."""
        import requests

        # Verify state matches
        from app.communication.models import OAuthState
        pending = OAuthState.query.filter_by(state=state, provider="gmail").first()

        if not pending:
            raise ValueError("Invalid OAuth state - possible CSRF attack")

        # Exchange code for tokens
        token_data = {
            "client_id": OAuthConfig.CLIENT_ID,
            "client_secret": OAuthConfig.CLIENT_SECRET,
            "redirect_uri": OAuthConfig.REDIRECT_URI,
            "code": code,
            "grant_type": "authorization_code",
        }

        response = requests.post(OAuthConfig.get_token_endpoint(), data=token_data)

        if response.status_code != 200:
            raise ValueError(f"Token exchange failed: {response.text}")

        tokens = response.json()

        # Clean up pending state
        self.session.delete(pending)
        self.session.commit()

        return {
            "access_token": tokens.get("access_token", ""),
            "refresh_token": tokens.get("refresh_token", ""),
            "expires_in": tokens.get("expires_in", 0),
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 0)),
            "email": "",  # Will be populated by get_profile
        }

    def get_gmail_profile(self, access_token: str) -> dict:
        """Get Gmail profile info using access token."""
        import requests

        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/profile",
            headers=headers,
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to get Gmail profile: {response.text}")

        return response.json()

    def connect_account(self, tenant_id: int, code: str, state: str) -> CommunicationSource:
        """Complete OAuth flow and create/update CommunicationSource for tenant."""
        # Exchange code for tokens
        tokens = self.exchange_code(code, state)

        if not tokens.get("access_token"):
            raise ValueError("No access token received")

        # Get profile to get email address
        profile = self.get_gmail_profile(tokens["access_token"])
        email = profile.get("emailAddress", "")

        if not email:
            raise ValueError("Could not determine Gmail account email")

        # Check for existing source
        existing = CommunicationSource.query.filter_by(
            tenant_id=tenant_id,
            provider="gmail",
            account_identifier=email,
        ).first()

        if existing:
            # Update existing credentials
            existing.credential_reference = f"env:GMAIL_TOKEN_{existing.id}"
            existing.is_active = True
            existing.updated_at = datetime.now(timezone.utc)
            self.session.commit()
            source = existing
        else:
            # Create new source
            source = CommunicationSource(
                tenant_id=tenant_id,
                provider="gmail",
                account_identifier=email,
                account_mode="business_dedicated",
                credential_reference=f"env:GMAIL_TOKEN_{secrets.token_hex(8)}",
                is_active=True,
                metadata_json=json.dumps({
                    "oauth_connected_at": datetime.now(timezone.utc).isoformat(),
                    "refresh_token": secrets.token_urlsafe(16),  # Store reference only in metadata
                }),
            )
            self.session.add(source)
            self.session.commit()

        # Store tokens securely in environment (in production, use a secrets manager)
        self._store_tokens(source.id, tokens)

        return source

    def _store_tokens(self, source_id: int, tokens: dict) -> None:
        """Store tokens securely - sets env vars for testing/demo."""
        # In production, this would use a secrets manager like HashiCorp Vault, AWS Secrets Manager, etc.
        # For now, we store in environment variables as a demonstration
        # Real implementation should never expose tokens in logs or metadata

        if os.getenv("TESTING", "").lower() in ("true", "1", "yes"):
            # In testing, set env var directly for verification
            os.environ[f"GMAIL_TOKEN_{source_id}"] = json.dumps({
                "access_token": tokens.get("access_token"),
                "refresh_token": tokens.get("refresh_token"),
            })
        # Production: use secrets manager - never log or store in database

    def get_credentials(self, source: CommunicationSource) -> dict:
        """Retrieve credentials for a CommunicationSource."""
        if not source.credential_reference:
            return {}

        token_json = CredentialResolver.resolve(source.credential_reference)
        if not token_json:
            return {}

        try:
            return json.loads(token_json)
        except json.JSONDecodeError:
            return {}

    def disconnect_account(self, source_id: int) -> bool:
        """Disconnect a Gmail account by deactivating its source."""
        source = CommunicationSource.query.get(source_id)
        if not source or source.provider != "gmail":
            return False

        source.is_active = False
        source.credential_reference = ""
        source.metadata_json = json.dumps({
            **(json.loads(source.metadata_json) if source.metadata_json else {}),
            "disconnected_at": datetime.now(timezone.utc).isoformat(),
        })
        self.session.commit()

        # Clean up env var in testing
        if os.getenv("TESTING", "").lower() in ("true", "1", "yes"):
            os.environ.pop(source_id, None)

        return True

    def validate_connection(self, source: CommunicationSource) -> dict:
        """Validate that stored credentials are still valid."""
        credentials = self.get_credentials(source)
        access_token = credentials.get("access_token", "")

        if not access_token:
            return {"valid": False, "error": "No access token found"}

        # Test token validity
        import requests
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/profile",
            headers=headers,
        )

        if response.status_code == 200:
            return {"valid": True, "email": source.account_identifier}
        elif response.status_code == 401:
            return {"valid": False, "error": "Token expired or invalid"}
        else:
            return {"valid": False, "error": f"Validation failed: {response.status_code}"}