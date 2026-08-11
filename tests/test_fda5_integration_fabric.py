"""FDA5-G4: Provider-Neutral Integration Fabric tests."""
import pytest
from datetime import datetime


class TestIntegrationFabric:
    """Verify the provider-neutral interfaces work."""

    def test_email_provider_interface_abstract(self):
        """EmailProvider cannot be instantiated directly."""
        from core.integration_fabric import EmailProvider
        with pytest.raises(TypeError):
            EmailProvider()

    def test_calendar_provider_interface_abstract(self):
        """CalendarProvider cannot be instantiated directly."""
        from core.integration_fabric import CalendarProvider
        with pytest.raises(TypeError):
            CalendarProvider()

    def test_concrete_email_provider(self):
        """A concrete provider implementing EmailProvider works."""
        from core.integration_fabric import EmailProvider, IntegrationConfig, ProviderStatus, ConnectionStatus, ProviderHealth

        class TestEmailProvider(EmailProvider):
            def connect(self, config): return True
            def disconnect(self): return True
            def fetch_emails(self, since=None, limit=50): return []
            def send_email(self, to, subject, body, **kwargs): return {"id": "test"}
            def get_status(self): return ProviderStatus(provider="test", status=ConnectionStatus.CONFIGURED, health=ProviderHealth.HEALTHY)
            def refresh_auth(self): return True

        provider = TestEmailProvider()
        assert provider.connect(IntegrationConfig(provider_name="test", tenant_id="1"))
        assert provider.send_email(["test@test.com"], "Test", "Body")["id"] == "test"

    def test_integration_registry(self):
        """IntegrationRegistry stores and retrieves providers."""
        from core.integration_fabric import IntegrationRegistry
        from core.integration_fabric import EmailProvider, IntegrationConfig, ProviderStatus, ConnectionStatus, ProviderHealth

        class MockProvider(EmailProvider):
            def connect(self, config): return True
            def disconnect(self): return True
            def fetch_emails(self, since=None, limit=50): return []
            def send_email(self, to, subject, body, **kwargs): return {"id": "mock"}
            def get_status(self): return ProviderStatus(provider="mock", status=ConnectionStatus.CONFIGURED, health=ProviderHealth.HEALTHY)
            def refresh_auth(self): return True

        IntegrationRegistry.register("mock_email", MockProvider())
        assert "mock_email" in IntegrationRegistry.list_providers()
        provider = IntegrationRegistry.get("mock_email")
        assert provider is not None
        assert provider.send_email(["a@b.com"], "S", "B")["id"] == "mock"

    def test_provider_status_enum(self):
        """ProviderHealth and ConnectionStatus enums are defined."""
        from core.integration_fabric import ProviderHealth, ConnectionStatus
        assert ProviderHealth.HEALTHY.value == "healthy"
        assert ProviderHealth.UNAVAILABLE.value == "unavailable"
        assert ConnectionStatus.AUTHENTICATED.value == "authenticated"
        assert ConnectionStatus.EXPIRED.value == "expired"

    def test_ai_model_provider_interface(self):
        """AIModelProvider interface works."""
        from core.integration_fabric import AIModelProvider, ProviderStatus

        class MockAI(AIModelProvider):
            def generate(self, prompt, **kwargs): return "response"
            def generate_structured(self, prompt, schema): return {"result": "ok"}
            def is_available(self): return True
            def get_status(self): return ProviderStatus(provider="ai", status=None, health=None)

        ai = MockAI()
        assert ai.generate("hello") == "response"
        assert ai.is_available() is True
        assert ai.generate_structured("x", {})["result"] == "ok"

    def test_webhook_provider_interface(self):
        """WebhookProvider interface works."""
        from core.integration_fabric import WebhookProvider, ProviderStatus

        class MockWebhook(WebhookProvider):
            def verify_signature(self, payload, sig, secret): return True
            def handle_event(self, data): return {"status": "ok"}
            def get_status(self): return ProviderStatus(provider="webhook", status=None, health=None)

        wh = MockWebhook()
        assert wh.verify_signature(b"test", "sig", "secret") is True
        assert wh.handle_event({"event": "test"})["status"] == "ok"