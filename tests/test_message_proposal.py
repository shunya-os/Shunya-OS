from datetime import datetime, timezone
import json

from app.communication.models import MessageProposal
from app import db


def test_proposal_created(app):
    with app.app_context():
        proposal = MessageProposal(to="9999999999", message="hi")
        db.session.add(proposal)
        db.session.flush()
        assert proposal.status == "pending"
        assert proposal.approved_by is None
        assert proposal.approved_at is None
        assert proposal.sent_at is None
        assert proposal.edited_message is None


def test_proposal_with_context(app):
    with app.app_context():
        proposal = MessageProposal(
            to="9999999999",
            message="Hi Rahul, sharing your Bali plan...",
            entity_id=42,
            entity_type="lead",
            entity_name="Rahul Trip Lead",
            context_reason="Lead contacted but not quoted",
            context_priority="high",
            context_source="decision_engine",
            context_confidence="high",
        )
        db.session.add(proposal)
        db.session.flush()

        assert proposal.status == "pending"
        assert proposal.entity_id == 42
        assert proposal.entity_type == "lead"
        assert proposal.entity_name == "Rahul Trip Lead"
        assert proposal.context_reason == "Lead contacted but not quoted"
        assert proposal.context_priority == "high"
        assert proposal.context_source == "decision_engine"
        assert proposal.context_confidence == "high"


def test_proposal_serialized_with_entity(app):
    with app.app_context():
        proposal = MessageProposal(
            to="9999999999",
            message="Hi Rahul, sharing your Bali plan...",
            entity_id=1,
            entity_type="lead",
            entity_name="Rahul Trip Lead",
            context_reason="Lead contacted but not quoted",
            context_priority="high",
        )
        db.session.add(proposal)
        db.session.flush()

        from app.communication.proposal_routes import _serialize
        data = _serialize(proposal)

        assert data["type"] == "message"
        assert data["entity"] is None  # entity_id=1 doesn't exist in DB
        assert data["message"] == "Hi Rahul, sharing your Bali plan..."
        assert data["context"]["reason"] == "Lead contacted but not quoted"
        assert data["context"]["priority"] == "high"
        assert data["context"]["source"] == "decision_engine"
        assert data["context"]["confidence"] == "high"


def test_proposal_enriched_endpoint_returns_enriched_shape(app):
    """Verify GET /proposals returns enriched shape via the real Flask app."""
    with app.app_context():
        # Seed a proposal with context and commit so test_client can see it
        proposal = MessageProposal(
            to="9876543210",
            message="Test enriched message",
            entity_id=99,
            entity_type="lead",
            entity_name="Test Lead",
            context_reason="Testing enrichment",
            context_priority="high",
            context_source="decision_engine",
            context_confidence="high",
        )
        db.session.add(proposal)
        db.session.commit()

    with app.test_client() as client:
        resp = client.get("/proposals")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "proposals" in data
        assert len(data["proposals"]) >= 1
        p = data["proposals"][-1]
        assert p["type"] == "message"
        assert "entity" in p
        assert "context" in p
        assert p["context"]["reason"] == "Testing enrichment"
        assert p["context"]["priority"] == "high"
        assert p["context"]["source"] == "decision_engine"
        assert p["context"]["confidence"] == "high"


# ── ACTIVATION-08B: Guardrail enforcement tests ──


def test_effect_whatsapp_creates_proposal_not_direct_send(app):
    """WhatsApp effect must create a proposal, never send directly."""
    with app.app_context():
        from app.execution.effects import execute_effect

        # Simulate a WhatsApp effect from the decision engine
        effect = {"type": "whatsapp", "to": "9999999999", "message": "Hi Test, your quote is ready!"}
        result = execute_effect(effect, entity_id=1)

        assert result["status"] == "proposal_created", f"Expected proposal, got: {result}"
        assert result["channel"] == "whatsapp"
        assert result["proposal_id"] > 0

        # Verify no direct send happened — adapter returns blocked
        from app.adapters import whatsapp_adapter
        direct_result = whatsapp_adapter.send(effect)
        assert direct_result["status"] == "blocked", f"Adapter should be blocked, got: {direct_result}"

        # Verify proposal exists in DB with correct data
        proposal = db.session.get(MessageProposal, result["proposal_id"])
        assert proposal is not None
        assert proposal.to == "9999999999"
        assert proposal.status == "pending"
        assert proposal.entity_id == 1


def test_effect_email_creates_proposal_not_direct_send(app):
    """Email effect must create a proposal, never send directly."""
    with app.app_context():
        from app.execution.effects import execute_effect

        effect = {"type": "email", "to": "test@example.com", "subject": "Your Quote", "body": "Dear Test, here is your quote."}
        result = execute_effect(effect, entity_id=2)

        assert result["status"] == "proposal_created", f"Expected proposal, got: {result}"
        assert result["channel"] == "email"

        # Verify adapter is blocked
        from app.adapters import email_adapter
        direct_result = email_adapter.send(effect)
        assert direct_result["status"] == "blocked"

        # Verify proposal in DB
        proposal = db.session.get(MessageProposal, result["proposal_id"])
        assert proposal is not None
        assert proposal.to == "test@example.com"
        assert proposal.status == "pending"


def test_effect_duplicate_prevented(app):
    """Same entity + same intent should not create duplicate proposals."""
    with app.app_context():
        from app.execution.effects import execute_effect

        effect = {"type": "whatsapp", "to": "9999999999", "message": "Duplicate test message"}

        # First call creates proposal
        first = execute_effect(effect, entity_id=100)
        assert first["status"] == "proposal_created"

        # Second call for same entity should be prevented
        second = execute_effect(effect, entity_id=100)
        assert second["status"] == "duplicate_prevented", f"Expected duplicate prevention, got: {second}"


def test_adapter_guardrails_block_direct_send(app):
    """Both email and WhatsApp adapters must block direct sends."""
    with app.app_context():
        from app.adapters import email_adapter, whatsapp_adapter

        email_result = email_adapter.send({"to": "test@test.com", "subject": "Test", "body": "Test"})
        assert email_result["status"] == "blocked"
        assert "DISABLED" in email_result["reason"]
        assert email_result["channel"] == "email"

        wa_result = whatsapp_adapter.send({"to": "9999999999", "message": "Test"})
        assert wa_result["status"] == "blocked"
        assert "DISABLED" in wa_result["reason"]
        assert wa_result["channel"] == "whatsapp"


def test_effect_log_still_works(app):
    """Log and task effects should still work as internal operations."""
    with app.app_context():
        from app.execution.effects import execute_effect

        log_result = execute_effect({"type": "log", "channel": "system", "message": "Test log"})
        assert log_result["status"] == "logged"