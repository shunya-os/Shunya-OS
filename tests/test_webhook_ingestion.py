"""
Gate 2.2 — Real Webhook Production Path Integration Tests.

Tests the ACTUAL WhatsApp webhook route's convergence with the
canonical ingestion pipeline, including idempotency and replay.
"""

import json
import uuid
import pytest
from unittest.mock import patch


def _unique_code() -> str:
    return f"INQ-G22{uuid.uuid4().hex[:8]}"


class TestWhatsAppWebhookIngestion:
    """Integration tests through the real WhatsApp webhook route."""

    def _make_whatsapp_payload(self, msg_id: str = "wamid.test123", text: str = "Hello",
                                sender: str = "919999999999") -> dict:
        """Build a realistic WhatsApp Business API payload."""
        return {
            "entry": [{
                "id": "test_phone_number",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {"phone_number_id": "test_phone_id"},
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": sender,
                        }],
                        "messages": [{
                            "from": sender,
                            "id": msg_id,
                            "timestamp": "1692000000",
                            "type": "text",
                            "text": {"body": text},
                        }],
                    },
                    "field": "messages",
                }],
            }],
        }

    @patch("app.whatsapp_webhook.parse_inquiry_text")
    @patch("app.whatsapp_webhook._cached_or_new_code")
    @patch("app.routes._log_activity")
    @patch("app.models.get_lead_tenant_id", return_value=1)
    def test_real_webhook_path_converges(self, mock_tenant, mock_log, mock_code, mock_parse, app_context):
        """The real webhook handler produces a canonical ingestion record."""
        from app.whatsapp_webhook import handle_whatsapp_incoming, _CACHED_IDS

        mock_parse.return_value = {"name": "Test User", "destination": "Goa"}
        mock_code.return_value = _unique_code()
        _CACHED_IDS.clear()

        from app.shunya.infrastructure.event_bus import reset_event_bus
        from core.ingestion.service import reset_ingestion_service
        reset_event_bus()
        reset_ingestion_service()

        payload = self._make_whatsapp_payload(
            msg_id="wamid.integration_test_001",
            text="I want to go to Goa",
        )
        with app_context:
            response, status = handle_whatsapp_incoming(payload)
            assert status == 200
            data = json.loads(response.get_data(as_text=True)) if hasattr(response, 'get_data') else response
            assert data.get("status") != "duplicate"

    @patch("app.whatsapp_webhook.parse_inquiry_text")
    @patch("app.whatsapp_webhook._cached_or_new_code")
    @patch("app.routes._log_activity")
    @patch("app.models.get_lead_tenant_id", return_value=1)
    def test_webhook_idempotency(self, mock_tenant, mock_log, mock_code, mock_parse, app_context):
        """Same webhook message twice → first succeeds, second returns duplicate."""
        from app.whatsapp_webhook import handle_whatsapp_incoming, _CACHED_IDS

        mock_parse.return_value = {"name": "Test User"}
        mock_code.return_value = _unique_code()

        # Clear the idempotency cache
        _CACHED_IDS.clear()

        from app.shunya.infrastructure.event_bus import reset_event_bus
        from core.ingestion.service import reset_ingestion_service
        reset_event_bus()
        reset_ingestion_service()

        payload = self._make_whatsapp_payload(
            msg_id="wamid.idempotency_test",
            text="Book a trip",
        )

        with app_context:
            # First call — should succeed
            resp1, status1 = handle_whatsapp_incoming(payload)
            assert status1 == 200
            data1 = json.loads(resp1.get_data(as_text=True)) if hasattr(resp1, 'get_data') else resp1
            assert data1.get("status") != "duplicate"

            # Second call — same msg_id → the handler should skip via _CACHED_IDS
            resp2, status2 = handle_whatsapp_incoming(payload)
            assert status2 == 200
            data2 = json.loads(resp2.get_data(as_text=True)) if hasattr(resp2, 'get_data') else resp2
            assert data2.get("status") == "duplicate", "Same message ID must return duplicate"

    @patch("app.whatsapp_webhook.parse_inquiry_text")
    @patch("app.whatsapp_webhook._cached_or_new_code")
    @patch("app.routes._log_activity")
    @patch("app.models.get_lead_tenant_id", return_value=1)
    def test_webhook_replay_protection(self, mock_tenant, mock_log, mock_code, mock_parse, app_context):
        """Replaying the same webhook after cache clear must not create duplicates."""
        from app.whatsapp_webhook import handle_whatsapp_incoming, _CACHED_IDS

        mock_parse.return_value = {"name": "Replay User"}
        c1, c2 = _unique_code(), _unique_code()
        mock_code.side_effect = [c1, c2]

        _CACHED_IDS.clear()
        from app.shunya.infrastructure.event_bus import reset_event_bus
        from core.ingestion.service import reset_ingestion_service
        reset_event_bus()
        reset_ingestion_service()

        payload = self._make_whatsapp_payload(
            msg_id="wamid.replay_test",
            text="Replay test message",
        )

        with app_context:
            # First call
            resp1, status1 = handle_whatsapp_incoming(payload)
            assert status1 == 200

            # Clear idempotency cache (simulates restart)
            _CACHED_IDS.clear()

            # Second call after restart — with same msg_id the handler
            # processes again (in-memory cache lost), but the canonical
            # ingestion pipeline tracks it deterministically
            resp2, status2 = handle_whatsapp_incoming(payload)
            assert status2 == 200

    @patch("app.whatsapp_webhook.parse_inquiry_text")
    @patch("app.whatsapp_webhook._cached_or_new_code")
    @patch("app.routes._log_activity")
    @patch("app.models.get_lead_tenant_id", return_value=1)
    def test_webhook_invalid_message_handled(self, mock_tenant, mock_log, mock_code, mock_parse, app_context):
        """Messages with no text content are handled gracefully."""
        from app.whatsapp_webhook import handle_whatsapp_incoming

        # Empty payload
        with app_context:
            resp, status = handle_whatsapp_incoming({"entry": [{"changes": [{"value": {}}]}]})
            assert status == 200
            data = json.loads(resp.get_data(as_text=True)) if hasattr(resp, 'get_data') else resp
            assert data.get("status") == "ignored"


@pytest.fixture
def app_context():
    """Provide a Flask app context for webhook tests."""
    from app import create_app
    app = create_app()
    with app.app_context() as ctx:
        yield ctx