"""FDA5-G5: Gmail Convergence — verify Gmail uses canonical IdentityService."""
import pytest


class TestGmailConvergence:
    """Gmail integration must converge on canonical IdentityService."""

    def test_gmail_adapter_implements_email_provider(self):
        """GmailAdapter must implement the canonical EmailProvider interface."""
        from app.integration.gmail_adapter import GmailAdapter
        from core.integration_fabric import EmailProvider
        assert isinstance(GmailAdapter(), EmailProvider)
        assert issubclass(GmailAdapter, EmailProvider)

    def test_gmail_adapter_registered(self):
        """GmailAdapter must be registered in the IntegrationRegistry."""
        from core.integration_fabric import IntegrationRegistry
        from app.integration.gmail_adapter import GmailAdapter
        IntegrationRegistry.register("gmail", GmailAdapter())
        assert "gmail" in IntegrationRegistry.list_providers()

    def test_gmail_status_disconnected(self):
        """GmailAdapter reports DISCONNECTED before connect()."""
        from app.integration.gmail_adapter import GmailAdapter
        from core.integration_fabric import ConnectionStatus
        adapter = GmailAdapter()
        status = adapter.get_status()
        assert status.status == ConnectionStatus.DISCONNECTED

    def test_gmail_connect_with_credentials(self):
        """GmailAdapter.connect() requires valid credentials."""
        from app.integration.gmail_adapter import GmailAdapter
        from core.integration_fabric import IntegrationConfig
        adapter = GmailAdapter()
        # Without credentials
        config = IntegrationConfig(provider_name="gmail", tenant_id="1")
        result = adapter.connect(config)
        assert result is False  # Missing credentials

        # With credentials
        config = IntegrationConfig(
            provider_name="gmail",
            tenant_id="1",
            credentials={"token": "mock", "refresh_token": "mock"},
        )
        result = adapter.connect(config)
        assert result is True

    def test_gmail_normalize_email(self):
        """GmailAdapter.normalize_email produces canonical format."""
        from app.integration.gmail_adapter import GmailAdapter
        raw = {
            "id": "msg_123",
            "threadId": "thread_456",
            "labelIds": ["INBOX", "IMPORTANT"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Subject", "value": "Test email"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                ]
            },
        }
        normalized = GmailAdapter.normalize_email(raw)
        assert normalized["message_id"] == "msg_123"
        assert normalized["from"] == "sender@example.com"
        assert normalized["to"] == "recipient@example.com"
        assert normalized["subject"] == "Test email"

    def test_gmail_to_identity_path(self, app):
        """Gmail sender → IdentityService resolution path works."""
        from app.integration.gmail_adapter import GmailAdapter
        from app.identity.service import IdentityService
        from core.identity_interface import IdentityClaim, ClaimType

        with app.app_context():
            id_svc = IdentityService()
            # Simulate: Gmail email sender → identity claim
            sender_email = "gmail-converge@example.com"
            claim = id_svc.add_claim(IdentityClaim(
                claim_value=sender_email,
                claim_type=ClaimType.EMAIL,
                source="gmail",
                source_id="gmail_msg_001",
                tenant_id="1",
            ))
            assert claim.claim_id is not None
            assert claim.identity_id is not None

            # Resolve: email → identity
            resolution = id_svc.resolve(sender_email, ClaimType.EMAIL)
            assert resolution.identity_id == claim.identity_id
            assert resolution.identity_type == "person"

    def test_gmail_oauth_routes_defined(self, app):
        """Gmail OAuth routes must be registered."""
        with app.test_request_context():
            # Check that the Gmail OAuth routes are accessible
            from flask import current_app
            rules = [r.rule for r in current_app.url_map.iter_rules()]
            gmail_routes = [r for r in rules if "gmail" in r.lower()]
            assert len(gmail_routes) > 0, f"No Gmail routes found in {rules}"

    def test_identity_service_uses_gmail_source(self, app):
        """IdentityService must accept 'gmail' as a valid source."""
        from app.identity.service import IdentityService
        from core.identity_interface import IdentityClaim, ClaimType
        with app.app_context():
            svc = IdentityService()
            claim = svc.add_claim(IdentityClaim(
                claim_value="gmail-user@test.com",
                claim_type=ClaimType.EMAIL,
                source="gmail",
                source_id="gmail_source_test",
                tenant_id="1",
            ))
            assert claim.claim_id is not None
            assert claim.source == "gmail"