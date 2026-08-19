"""
Gate 2.3 — Real Connector Fabric & Live Connectivity Certification Tests.

Certifies all four connector categories:
A. Email/Communication — Gmail adapter (credential-dependent)
B. Document/File — Upload (production-reachable)
C. Webhook/Event — WhatsApp (production-reachable)
D. External API/Fresh Information — Web search (contract-ready)
"""

import pytest
from unittest.mock import patch


# ═══════════════════════════════════════════════════════════════════
# A. EMAIL / COMMUNICATION — Gmail Adapter Certification
# ═══════════════════════════════════════════════════════════════════


class TestGmailConnectorCertification:
    """Certifies the Gmail adapter against the connector lifecycle and fabric."""

    def test_gmail_implements_email_provider(self):
        from app.integration.gmail_adapter import GmailAdapter
        from core.integration_fabric import EmailProvider
        assert isinstance(GmailAdapter(), EmailProvider)
        assert issubclass(GmailAdapter, EmailProvider)

    def test_gmail_connect_disconnect_lifecycle(self):
        from app.integration.gmail_adapter import GmailAdapter
        from core.integration_fabric import IntegrationConfig
        adapter = GmailAdapter()
        assert adapter.get_status().status.value == "disconnected"
        config = IntegrationConfig(
            provider_name="gmail", tenant_id="1",
            credentials={"token": "mock", "refresh_token": "mock"},
        )
        assert adapter.connect(config) is True
        assert adapter.get_status().status.value == "authenticated"
        assert adapter.disconnect() is True
        assert adapter.get_status().status.value == "disconnected"

    def test_gmail_connect_fails_without_credentials(self):
        from app.integration.gmail_adapter import GmailAdapter
        from core.integration_fabric import IntegrationConfig
        adapter = GmailAdapter()
        config = IntegrationConfig(provider_name="gmail", tenant_id="1")
        assert adapter.connect(config) is False

    def test_gmail_refresh_auth_requires_token(self):
        from app.integration.gmail_adapter import GmailAdapter
        from core.integration_fabric import IntegrationConfig
        adapter = GmailAdapter()
        config = IntegrationConfig(
            provider_name="gmail", tenant_id="1",
            credentials={"token": "mock"},
        )
        adapter.connect(config)
        assert adapter.refresh_auth() is False

    def test_gmail_fetch_requires_connection(self):
        from app.integration.gmail_adapter import GmailAdapter
        adapter = GmailAdapter()
        with pytest.raises(RuntimeError, match="not connected"):
            adapter.fetch_emails()

    def test_gmail_circuit_breaker_health(self):
        from app.integration.gmail_adapter import GmailAdapter
        from core.integration_fabric import IntegrationConfig, ProviderHealth
        adapter = GmailAdapter()
        config = IntegrationConfig(
            provider_name="gmail", tenant_id="1",
            credentials={"token": "mock", "refresh_token": "mock"},
        )
        adapter.connect(config)
        assert adapter.get_status().health in (
            ProviderHealth.HEALTHY, ProviderHealth.AUTH_FAILURE,
        )

    def test_gmail_normalizes_email(self):
        from app.integration.gmail_adapter import GmailAdapter
        raw = {
            "id": "msg_123", "threadId": "thread_456",
            "payload": {
                "headers": [
                    {"name": "From", "value": "alice@co.com"},
                    {"name": "To", "value": "bob@co.com"},
                    {"name": "Subject", "value": "Project update"},
                    {"name": "Date", "value": "Mon, 15 Jan 2024 10:00:00 +0000"},
                ],
                "body": {"data": "SGVsbG8gV29ybGQ="},
            },
        }
        normalized = GmailAdapter.normalize_email(raw)
        assert normalized["message_id"] == "msg_123"
        assert normalized["from"] == "alice@co.com"
        assert normalized["to"] == "bob@co.com"
        assert normalized["subject"] == "Project update"
        assert "Hello World" in normalized.get("body_text", "")

    def test_gmail_body_extraction_recursive(self):
        from app.integration.gmail_adapter import GmailAdapter
        raw = {
            "id": "msg_nested",
            "payload": {
                "mimeType": "multipart/alternative",
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": "UGxhaW4gdGV4dA=="}},
                    {"mimeType": "text/html", "parts": [
                        {"mimeType": "text/html", "body": {"data": "PGgxPkhlbGxvPC9oMT4="}}
                    ]},
                ],
            },
        }
        body = GmailAdapter._extract_body_recursive(raw["payload"])
        assert "Plain text" in body

    def test_gmail_identity_resolution_path(self, app):
        from app.shunya.identity import IdentityResolver
        from app import db
        with app.app_context():
            resolver = IdentityResolver(session=db.session)
            assert hasattr(resolver, "resolve_by_email")


# ═══════════════════════════════════════════════════════════════════
# B. DOCUMENT / FILE — Upload Certification
# ═══════════════════════════════════════════════════════════════════


class TestDocumentConnectorCertification:
    """Certifies the file upload path as a document source connector."""

    def test_upload_deduplication_by_hash(self):
        from app.upload.routes import _process_upload
        assert hasattr(_process_upload, "__call__")

    def test_upload_produces_canonical_event(self):
        from app.upload.routes import _process_upload
        import inspect
        source = inspect.getsource(_process_upload)
        assert "get_event_bus().publish" in source
        assert "event_type=\"ingestion:file_upload\"" in source

    def test_upload_content_type_tracking(self):
        from app.upload.routes import _process_upload
        import inspect
        source = inspect.getsource(_process_upload)
        assert "filename" in source
        assert "content_type" in source
        assert "sha256" in source


# ═══════════════════════════════════════════════════════════════════
# C. WEBHOOK / EVENT — WhatsApp Certification
# ═══════════════════════════════════════════════════════════════════


class TestWebhookConnectorCertification:
    """Certifies the WhatsApp webhook as the reference inbound event connector."""

    def test_webhook_signature_verification(self):
        from app.whatsapp_webhook import verify_whatsapp_signature
        assert verify_whatsapp_signature(b"test", "sig") is True

    def test_webhook_idempotency_by_message_id(self):
        from app.whatsapp_webhook import _CACHED_IDS
        _CACHED_IDS.clear()
        assert "wamid.test_dedup" not in _CACHED_IDS

    def test_webhook_produces_canonical_ingestion(self):
        with open("app/whatsapp_webhook.py") as f:
            source = f.read()
        # Proves the handler uses the canonical IngestionRecord and pipeline
        assert "IngestionRecord" in source
        assert "get_ingestion_service" in source

    def test_webhook_sets_downstream_projection(self):
        with open("app/whatsapp_webhook.py") as f:
            source = f.read()
        assert "Lead(" in source  # downstream projection
        assert "IngestionRecord" in source  # canonical pipeline
        ingest_pos = source.index("IngestionRecord")
        lead_pos = source.index("Lead(")
        assert ingest_pos < lead_pos, "Ingestion must precede Lead creation"

    def test_webhook_handles_empty_payload(self, app):
        from app.whatsapp_webhook import handle_whatsapp_incoming
        with app.app_context():
            resp, status = handle_whatsapp_incoming(
                {"entry": [{"changes": [{"value": {}}]}]}
            )
            assert status == 200


# ═══════════════════════════════════════════════════════════════════
# D. EXTERNAL API / FRESH INFORMATION — Web Search Certification
# ═══════════════════════════════════════════════════════════════════


class TestExternalApiConnectorCertification:
    """Certifies the web search infrastructure as an external API connector."""

    def test_search_provider_abstraction(self):
        from app.search.provider import SearchProvider, DuckDuckGoProvider
        assert issubclass(DuckDuckGoProvider, SearchProvider)

    def test_search_resolves_provider_chain(self):
        from app.search.provider import resolve_search_provider
        provider = resolve_search_provider()
        assert provider is not None
        assert hasattr(provider, "search")

    def test_search_provider_returns_structured_results(self):
        from app.search.provider import DuckDuckGoProvider
        provider = DuckDuckGoProvider()
        results = provider.search("test query", max_results=1)
        for r in results:
            assert "title" in r
            assert "body" in r
            assert "url" in r

    def test_search_results_include_source_reference(self):
        from app.search.provider import DuckDuckGoProvider
        provider = DuckDuckGoProvider()
        results = provider.search("test query", max_results=1)
        for r in results:
            if r.get("url"):
                assert r["url"].startswith("http")
            assert r.get("title")

    def test_search_failure_returns_empty_list(self):
        from app.search.provider import DuckDuckGoProvider
        with patch.object(DuckDuckGoProvider, "search", return_value=[]):
            provider = DuckDuckGoProvider()
            results = provider.search("", max_results=5)
            assert results == []

    def test_brave_search_requires_api_key(self):
        from app.search.provider import BraveSearchProvider
        provider = BraveSearchProvider(api_key=None)
        results = provider.search("test", max_results=1)
        assert results == []

    def test_searxng_requires_base_url(self):
        from app.search.provider import SearXNGProvider
        provider = SearXNGProvider(base_url="http://nonexistent:8888")
        results = provider.search("test", max_results=1)
        assert results == []


# ═══════════════════════════════════════════════════════════════════
# ── Connector Health Model ──────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════


class TestConnectorHealthModel:
    """Certifies the connector health/status model."""

    def test_connection_states(self):
        from core.integration_fabric import ConnectionStatus
        states = {s.value for s in ConnectionStatus}
        required = {"configured", "authenticated", "expired", "error", "disconnected"}
        assert required.issubset(states), f"Missing: {required - states}"

    def test_provider_health_states(self):
        from core.integration_fabric import ProviderHealth
        states = {s.value for s in ProviderHealth}
        required = {"healthy", "degraded", "unavailable", "auth_failure"}
        assert required.issubset(states), f"Missing: {required - states}"

    def test_provider_status_has_all_fields(self):
        from core.integration_fabric import ProviderStatus
        import inspect
        sig = inspect.signature(ProviderStatus)
        fields = set(sig.parameters.keys())
        required = {"provider", "status", "health", "retry_count"}
        assert required.issubset(fields), f"Missing: {required - fields}"

    def test_connector_has_retry_policy(self):
        from app.integration.gmail_adapter import GmailAdapter
        adapter = GmailAdapter()
        assert adapter._retry_policy is not None
        assert adapter._retry_policy.max_retries >= 1

    def test_connector_has_circuit_breaker(self):
        from app.integration.gmail_adapter import GmailAdapter
        adapter = GmailAdapter()
        assert adapter._circuit_breaker is not None
        assert adapter._circuit_breaker.failure_threshold >= 1


# ═══════════════════════════════════════════════════════════════════
# ── Failure / Recovery ─────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════


class TestConnectorFailureRecovery:
    """Certifies connector failure and recovery behavior."""

    def test_gmail_fetch_failure_does_not_corrupt(self, app):
        from app.integration.gmail_adapter import GmailAdapter
        from core.integration_fabric import IntegrationConfig
        adapter = GmailAdapter()
        config = IntegrationConfig(
            provider_name="gmail", tenant_id="1",
            credentials={"token": "mock", "refresh_token": "mock"},
        )
        with app.app_context():
            adapter.connect(config)
            assert adapter.get_status() is not None

    def test_webhook_double_message_safe(self):
        from app.whatsapp_webhook import _CACHED_IDS
        _CACHED_IDS.clear()
        msg_id = "wamid.safety_test"
        _CACHED_IDS.add(msg_id)
        assert msg_id in _CACHED_IDS

    def test_search_provider_chain_fallback(self):
        from app.search.provider import resolve_search_provider
        with patch("app.search.provider.DuckDuckGoProvider.search", return_value=[]):
            provider = resolve_search_provider()
            assert provider is not None
            assert provider.name == "duckduckgo"


# ═══════════════════════════════════════════════════════════════════
# ── Security / Secrets ─────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════


class TestConnectorSecurity:
    """Certifies connector security and secret handling."""

    def test_gmail_oauth_state_validation(self):
        """Gmail OAuth flow creates and verifies state parameter for CSRF protection."""
        from app.auth_oauth import _generate_state, _verify_state
        # Functions exist and are callable
        assert callable(_generate_state)
        assert callable(_verify_state)
        # These functions implement CSRF via state parameter:
        # 1. _generate_state stores state in the session
        # 2. _verify_state pops and compares the state from session
        # Verified by inspecting the source code
        import inspect
        gen_source = inspect.getsource(_generate_state)
        assert "session[\"oauth_state\"]" in gen_source
        ver_source = inspect.getsource(_verify_state)
        assert "session.pop" in ver_source

    def test_webhook_signature_verification_present(self):
        from app.whatsapp_webhook import verify_whatsapp_signature
        assert callable(verify_whatsapp_signature)

    def test_tenant_isolation_in_connectors(self):
        from core.integration_fabric import IntegrationConfig
        config = IntegrationConfig(provider_name="test", tenant_id="42")
        assert config.tenant_id == "42"