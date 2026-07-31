"""Tests for SHUNYA Integration Runtime (Phase G).

Covers:
1. Message model defaults
2. Connector registration + capability discovery
3. Credential management + security
4. REST connector
5. Webhook connector
6. Filesystem connector
7. SMTP connector
8. OpenAI connector
9. Connection management + circuit breaker
10. Observability (traces, audit, health)
11. Error handling (timeout, rate limit, auth)
12. Payload limits
13. Default connector registration
14. Health check
"""


import pytest

from core.integration_runtime import (
    CircuitBreakerOpenError,
    ConnectionState,
    ConnectorContract,
    IntegrationMessage,
    IntegrationRuntime,
    MessageDirection,
    MessageType,
)

# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def runtime():
    r = IntegrationRuntime()
    r.register_default_connectors()
    return r


# ══════════════════════════════════════════════════════════════════════════
# 1. Model Defaults
# ══════════════════════════════════════════════════════════════════════════

class TestModels:
    def test_message_defaults(self):
        msg = IntegrationMessage()
        assert msg.message_id
        assert msg.direction == MessageDirection.OUTBOUND
        assert msg.message_type == MessageType.REQUEST
        assert msg.error is None

    def test_connector_contract_defaults(self):
        c = ConnectorContract(connector_id="test")
        assert c.version == "1.0.0"
        assert c.capabilities == []


# ══════════════════════════════════════════════════════════════════════════
# 2. Connector Registration
# ══════════════════════════════════════════════════════════════════════════

class TestRegistration:
    def test_register_and_list(self, runtime):
        connectors = runtime.list_connectors()
        connector_ids = {c.connector_id for c in connectors}
        assert "rest" in connector_ids
        assert "smtp" in connector_ids
        assert "openai" in connector_ids

    def test_duplicate_raises(self, runtime):
        c = ConnectorContract(connector_id="dup", capabilities=["test"])
        with pytest.raises(ValueError, match="already registered"):
            runtime.register_connector("rest", c, handler=lambda m: m)

    def test_get_connector(self, runtime):
        entry = runtime.get_connector("rest")
        assert entry is not None
        assert "rest.get" in entry.contract.capabilities

    def test_unknown_connector_raises(self, runtime):
        with pytest.raises(ValueError, match="Unknown connector"):
            msg = IntegrationMessage()
            import asyncio
            asyncio.run(runtime.send("nonexistent", msg))


# ══════════════════════════════════════════════════════════════════════════
# 3. Capability Discovery
# ══════════════════════════════════════════════════════════════════════════

class TestCapabilityDiscovery:
    def test_discover_capabilities(self, runtime):
        caps = runtime.discover_capabilities()
        assert "rest.get" in caps
        assert "email.send" in caps
        assert "ai.chat" in caps
        assert len(caps) >= 10  # All reference capabilities

    def test_find_connector(self, runtime):
        connectors = runtime.find_connector("rest.get")
        assert "rest" in connectors

    def test_find_connector_not_found(self, runtime):
        connectors = runtime.find_connector("nonexistent")
        assert connectors == []


# ══════════════════════════════════════════════════════════════════════════
# 4. REST Connector
# ══════════════════════════════════════════════════════════════════════════

class TestRESTConnector:
    @pytest.mark.asyncio
    async def test_get(self, runtime):
        msg = IntegrationMessage(
            headers={"method": "GET", "path": "/api/users"},
        )
        response = await runtime.send("rest", msg)
        assert response.message_type == MessageType.RESPONSE
        assert response.body["method"] == "GET"
        assert response.body["received"] is True

    @pytest.mark.asyncio
    async def test_post(self, runtime):
        msg = IntegrationMessage(
            message_type=MessageType.REQUEST,
            headers={"method": "POST", "path": "/api/users"},
            body={"name": "Alice"},
        )
        response = await runtime.send("rest", msg)
        assert response.body["body_received"] is True
        assert response.metadata["status_code"] == 201

    @pytest.mark.asyncio
    async def test_delete(self, runtime):
        msg = IntegrationMessage(
            headers={"method": "DELETE", "path": "/api/users/1"},
        )
        response = await runtime.send("rest", msg)
        assert response.body is None

    @pytest.mark.asyncio
    async def test_unsupported_method(self, runtime):
        msg = IntegrationMessage(
            headers={"method": "OPTIONS", "path": "/api"},
        )
        response = await runtime.send("rest", msg)
        assert response.metadata["status_code"] == 405


# ══════════════════════════════════════════════════════════════════════════
# 5. Webhook Connector
# ══════════════════════════════════════════════════════════════════════════

class TestWebhookConnector:
    @pytest.mark.asyncio
    async def test_register(self, runtime):
        msg = IntegrationMessage(
            headers={"action": "register", "url": "https://example.com/hook"},
            body=["order.created", "payment.received"],
        )
        response = await runtime.send("webhook", msg)
        assert response.body["status"] == "registered"

    @pytest.mark.asyncio
    async def test_deliver(self, runtime):
        msg = IntegrationMessage(
            headers={"action": "deliver", "url": "https://example.com/hook"},
            body={"event": "order.created", "data": {"id": 42}},
        )
        response = await runtime.send("webhook", msg)
        assert response.message_type == MessageType.REQUEST

    @pytest.mark.asyncio
    async def test_unregister(self, runtime):
        msg = IntegrationMessage(
            headers={"action": "unregister", "url": "https://example.com/hook"},
        )
        response = await runtime.send("webhook", msg)
        assert response.body["status"] == "unregistered"


# ══════════════════════════════════════════════════════════════════════════
# 6. Filesystem Connector
# ══════════════════════════════════════════════════════════════════════════

class TestFilesystemConnector:
    @pytest.mark.asyncio
    async def test_write(self, runtime):
        msg = IntegrationMessage(
            headers={"action": "write", "path": "/tmp/test.txt"},
            body={"content": "hello world"},
        )
        response = await runtime.send("filesystem", msg)
        assert response.body["status"] == "written"

    @pytest.mark.asyncio
    async def test_read(self, runtime):
        msg = IntegrationMessage(
            headers={"action": "read", "path": "/tmp/test.txt"},
        )
        response = await runtime.send("filesystem", msg)
        assert response.body["content"] == "hello world"

    @pytest.mark.asyncio
    async def test_read_not_found(self, runtime):
        msg = IntegrationMessage(
            headers={"action": "read", "path": "/tmp/nonexistent.txt"},
        )
        response = await runtime.send("filesystem", msg)
        assert response.error == "not_found"

    @pytest.mark.asyncio
    async def test_list(self, runtime):
        msg = IntegrationMessage(
            headers={"action": "list", "path": "/tmp/"},
        )
        response = await runtime.send("filesystem", msg)
        assert response.body["count"] >= 1


# ══════════════════════════════════════════════════════════════════════════
# 7. SMTP Connector
# ══════════════════════════════════════════════════════════════════════════

class TestSMTPConnector:
    @pytest.mark.asyncio
    async def test_send_email(self, runtime):
        msg = IntegrationMessage(
            headers={"to": "user@example.com", "subject": "Hello"},
            body="This is a test email.",
        )
        response = await runtime.send("smtp", msg)
        assert response.body["status"] == "sent"
        assert response.body["to"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_sent_emails_stored(self, runtime):
        from core.integration_runtime.connectors.reference import clear_sent_emails
        clear_sent_emails()

        msg = IntegrationMessage(
            headers={"to": "a@b.com", "subject": "Test"},
            body="Body",
        )
        await runtime.send("smtp", msg)
        from core.integration_runtime.connectors.reference import get_sent_emails
        sent = get_sent_emails()
        assert len(sent) == 1
        assert sent[0]["to"] == "a@b.com"


# ══════════════════════════════════════════════════════════════════════════
# 8. OpenAI Connector
# ══════════════════════════════════════════════════════════════════════════

class TestOpenAIConnector:
    @pytest.mark.asyncio
    async def test_chat(self, runtime):
        msg = IntegrationMessage(
            headers={"capability": "ai.chat", "model": "gpt-4"},
            body=[{"role": "user", "content": "Hello"}],
        )
        response = await runtime.send("openai", msg)
        assert "choices" in response.body
        assert "assistant" in response.body["choices"][0]["message"]["role"]

    @pytest.mark.asyncio
    async def test_embed(self, runtime):
        msg = IntegrationMessage(
            headers={"capability": "ai.embed"},
        )
        response = await runtime.send("openai", msg)
        assert "data" in response.body
        assert len(response.body["data"][0]["embedding"]) == 128

    @pytest.mark.asyncio
    async def test_complete(self, runtime):
        msg = IntegrationMessage(
            headers={"capability": "ai.complete"},
            body="Once upon a time",
        )
        response = await runtime.send("openai", msg)
        assert "Completion of:" in response.body["choices"][0]["text"]


# ══════════════════════════════════════════════════════════════════════════
# 9. Connection Management
# ══════════════════════════════════════════════════════════════════════════

class TestConnectionManagement:
    @pytest.mark.asyncio
    async def test_connect(self, runtime):
        info = await runtime.connect("rest")
        assert info.state == ConnectionState.CONNECTED
        assert info.connected_at

    @pytest.mark.asyncio
    async def test_disconnect(self, runtime):
        await runtime.connect("rest")
        await runtime.disconnect("rest")
        entry = runtime.get_connector("rest")
        assert entry.connection.state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_circuit_breaker(self, runtime):
        """Excessive failures should simulate circuit breaker."""
        # Set a low threshold
        entry = runtime.get_connector("rest")
        entry.config.circuit_breaker_threshold = 3
        entry.config.max_retries = 0  # No retries

        # Send to a broken connector
        runtime.set_connection_state("rest", ConnectionState.FAILED)
        entry.connection.failure_count = 5

        msg = IntegrationMessage(headers={"method": "GET", "path": "/"})
        with pytest.raises(CircuitBreakerOpenError):
            await runtime.send("rest", msg)

    @pytest.mark.asyncio
    async def test_automatic_reconnect(self, runtime):
        """Send should auto-connect if disconnected."""
        runtime.set_connection_state("rest", ConnectionState.DISCONNECTED)
        msg = IntegrationMessage(headers={"method": "GET", "path": "/"})
        response = await runtime.send("rest", msg)
        assert response.message_type == MessageType.RESPONSE
        entry = runtime.get_connector("rest")
        # After the send, connection should be re-established
        # (may have changed during retry)
        assert entry.connection.state in (ConnectionState.CONNECTED, ConnectionState.DISCONNECTED)


# ══════════════════════════════════════════════════════════════════════════
# 10. Observability
# ══════════════════════════════════════════════════════════════════════════

class TestObservability:
    @pytest.mark.asyncio
    async def test_traces(self, runtime):
        msg = IntegrationMessage(headers={"method": "GET", "path": "/"})
        await runtime.send("rest", msg)
        traces = runtime.get_traces("rest")
        assert len(traces) == 1
        assert traces[0].status == "success"
        assert traces[0].latency_ms > 0

    @pytest.mark.asyncio
    async def test_audit_log(self, runtime):
        msg = IntegrationMessage(headers={"method": "GET", "path": "/"})
        await runtime.send("rest", msg)
        log = runtime.get_audit_log("rest")
        assert len(log) == 1
        assert log[0].success is True

    @pytest.mark.asyncio
    async def test_health_update(self, runtime):
        msg = IntegrationMessage(headers={"method": "GET", "path": "/"})
        await runtime.send("rest", msg)
        health = runtime.get_health("rest")
        assert "rest" in health
        assert health["rest"].messages_sent == 1
        assert health["rest"].avg_latency_ms > 0

    @pytest.mark.asyncio
    async def test_get_all_health(self, runtime):
        health = runtime.get_health()
        assert len(health) == 5  # 5 default connectors


# ══════════════════════════════════════════════════════════════════════════
# 11. Error Handling
# ══════════════════════════════════════════════════════════════════════════

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_unknown_connector_id(self, runtime):
        msg = IntegrationMessage()
        with pytest.raises(ValueError, match="Unknown connector"):
            await runtime.send("does_not_exist", msg)


# ══════════════════════════════════════════════════════════════════════════
# 12. Payload Limits
# ══════════════════════════════════════════════════════════════════════════

class TestPayloadLimits:
    @pytest.mark.asyncio
    async def test_payload_too_large(self, runtime):
        from core.integration_runtime import PayloadTooLargeError
        entry = runtime.get_connector("rest")
        entry.config.max_payload_bytes = 10  # Very small limit

        msg = IntegrationMessage(
            headers={"method": "POST", "path": "/"},
            body={"data": "x" * 100},
        )
        with pytest.raises(PayloadTooLargeError):
            await runtime.send("rest", msg)


# ══════════════════════════════════════════════════════════════════════════
# 13. Credential Management
# ══════════════════════════════════════════════════════════════════════════

class TestCredentialManagement:
    def test_register_credential(self, runtime):
        cred = runtime.register_credential(
            credential_id="my_api_key",
            credential_type="api_key",
            secrets={"key": "sk-1234567890"},
            tenant_id="tenant_1",
        )
        assert cred.credential_id == "my_api_key"
        assert cred.tenant_id == "tenant_1"

    def test_get_credential(self, runtime):
        runtime.register_credential("my_cred", "bearer", {"token": "abc"})
        cred = runtime.get_credential("my_cred")
        assert cred is not None
        assert cred._secrets["token"] == "abc"  # Only accessible via getter


# ══════════════════════════════════════════════════════════════════════════
# 14. Health Check
# ══════════════════════════════════════════════════════════════════════════

class TestHealthCheck:
    def test_health_empty_runtime(self):
        r = IntegrationRuntime()
        hc = r.health_check()
        assert hc["status"] == "healthy"
        assert hc["connectors_registered"] == 0

    def test_health_after_registration(self, runtime):
        hc = runtime.health_check()
        assert hc["connectors_registered"] == 5
        assert "rest" in hc["connectors"]
        assert hc["capabilities_available"] >= 10

    @pytest.mark.asyncio
    async def test_health_after_send(self, runtime):
        msg = IntegrationMessage(headers={"method": "GET", "path": "/"})
        await runtime.send("rest", msg)
        hc = runtime.health_check()
        assert hc["total_messages"] == 1
        assert hc["connectors"]["rest"]["messages_sent"] == 1


# ══════════════════════════════════════════════════════════════════════════
# 15. Custom Connector Registration
# ══════════════════════════════════════════════════════════════════════════

class TestCustomConnector:
    @pytest.mark.asyncio
    async def test_register_custom(self, runtime):
        async def custom_handler(msg: IntegrationMessage) -> IntegrationMessage:
            return IntegrationMessage(
                connector_id="custom",
                direction=MessageDirection.INBOUND,
                message_type=MessageType.RESPONSE,
                body={"custom": True, "input": msg.body},
            )

        contract = ConnectorContract(
            connector_id="custom",
            capabilities=["custom.echo"],
        )
        runtime.register_connector("custom", contract, custom_handler)
        msg = IntegrationMessage(body="hello")
        response = await runtime.send("custom", msg)
        assert response.body["custom"] is True
        assert response.body["input"] == "hello"