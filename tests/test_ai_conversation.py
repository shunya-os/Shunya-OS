"""ZGC-05 Workstream F — AI Conversation Persistence Tests.

Tests the conversation persistence layer directly without depending
on the AI provider. Also verifies the API endpoints work.
"""

import pytest
import uuid
from app import db


class TestConversationPersistence:
    """Test conversation CRUD via API and direct DB."""

    def _login(self, client):
        from app.auth import TeamMember
        from app.auth_routes import UserRole
        from app.models import Organization, OrgMember
        member = TeamMember(
            name="Conv Test",
            email="conv-persist@test.org",
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        member.set_password("testpass123")
        db.session.add(member)
        db.session.commit()
        org = Organization(name="Conv Persist Org", slug="conv-persist-org")
        db.session.add(org)
        db.session.commit()
        om = OrgMember(organization_id=org.id, identity_id="sid_conv_persist",
                       email=member.email, role="admin")
        db.session.add(om)
        db.session.commit()
        with client.session_transaction() as sess:
            sess["user_id"] = member.id
            sess["identity_id"] = "sid_conv_persist"
            sess["current_org_id"] = org.id
        return member

    def test_write_and_read_conversation(self, app, client):
        """Direct create and read of FounderConversation + FounderMessage."""
        from app.founder.models import FounderConversation, FounderMessage
        conv_id = f"conv_test_{uuid.uuid4().hex[:8]}"
        conv = FounderConversation(
            conv_id=conv_id,
            object_id="tenant_1",
            title="Test conversation",
            identity_id="sid_conv_persist",
            status="active",
        )
        db.session.add(conv)
        db.session.commit()
        msg = FounderMessage(
            conv_id=conv_id,
            role="human",
            content="Hello from test",
        )
        db.session.add(msg)
        db.session.commit()
        # Read back
        fetched = FounderConversation.query.filter_by(conv_id=conv_id).first()
        assert fetched is not None
        assert fetched.title == "Test conversation"
        msgs = FounderMessage.query.filter_by(conv_id=conv_id).all()
        assert len(msgs) == 1
        assert msgs[0].content == "Hello from test"

    def test_conversation_get_endpoint(self, app, client):
        """GET /api/v1/ai/conversations/<conv_id> returns stored conversation."""
        self._login(client)
        from app.founder.models import FounderConversation, FounderMessage
        conv_id = f"conv_api_{uuid.uuid4().hex[:8]}"
        conv = FounderConversation(
            conv_id=conv_id, object_id="tenant_1",
            title="API conv", identity_id="sid_conv_persist", status="active",
        )
        db.session.add(conv)
        db.session.commit()
        msg = FounderMessage(conv_id=conv_id, role="human", content="API test message")
        db.session.add(msg)
        db.session.commit()
        resp = client.get(f"/api/v1/ai/conversations/{conv_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["conversation"]["conv_id"] == conv_id
        assert len(data["data"]["messages"]) == 1

    def test_conversation_list_endpoint(self, app, client):
        """GET /api/v1/ai/conversations returns list."""
        self._login(client)
        from app.founder.models import FounderConversation
        conv_id = f"conv_list_{uuid.uuid4().hex[:8]}"
        conv = FounderConversation(
            conv_id=conv_id, object_id="tenant_1",
            title="List conv", identity_id="sid_conv_persist", status="active",
        )
        db.session.add(conv)
        db.session.commit()
        resp = client.get("/api/v1/ai/conversations")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        found = any(c["conv_id"] == conv_id for c in data["data"])
        assert found, f"Conversation {conv_id} not found in list"

    def test_conversation_not_found(self, app, client):
        """Nonexistent conv_id returns 404."""
        resp = client.get("/api/v1/ai/conversations/nonexistent_conv_id")
        assert resp.status_code == 404

    def test_multiple_messages_per_conversation(self, app, client):
        """Conversation with multiple messages returns all."""
        from app.founder.models import FounderConversation, FounderMessage
        conv_id = f"conv_multi_{uuid.uuid4().hex[:8]}"
        conv = FounderConversation(
            conv_id=conv_id, object_id="tenant_1",
            title="Multi msg", identity_id="sid_conv_persist", status="active",
        )
        db.session.add(conv)
        db.session.commit()
        for i in range(3):
            db.session.add(FounderMessage(conv_id=conv_id, role="human", content=f"Msg {i}"))
        db.session.commit()
        msgs = FounderMessage.query.filter_by(conv_id=conv_id).order_by(
            FounderMessage.created_at.asc()).all()
        assert len(msgs) == 3
        assert msgs[0].content == "Msg 0"
        assert msgs[2].content == "Msg 2"

    def test_conversation_messages_ordered_by_created_at(self, app, client):
        """Messages are returned in chronological order."""
        from app.founder.models import FounderConversation, FounderMessage
        from datetime import datetime, timedelta, timezone
        conv_id = f"conv_order_{uuid.uuid4().hex[:8]}"
        conv = FounderConversation(
            conv_id=conv_id, object_id="tenant_1",
            title="Order test", identity_id="sid_conv_persist", status="active",
        )
        db.session.add(conv)
        db.session.commit()
        # Add messages with explicit timestamps
        for i, delay in enumerate([5, 2, 8, 1]):
            msg = FounderMessage(
                conv_id=conv_id, role="human" if i % 2 == 0 else "assistant",
                content=f"Order msg {i}",
            )
            # Override created_at to test ordering
            msg.created_at = datetime.now(timezone.utc) + timedelta(hours=delay)
            db.session.add(msg)
        db.session.commit()
        msgs = FounderMessage.query.filter_by(conv_id=conv_id).order_by(
            FounderMessage.created_at.asc()).all()
        # Should be in order 3, 1, 0, 2 (by delay value)
        actual_order = [m.content for m in msgs]
        assert actual_order == ["Order msg 3", "Order msg 1", "Order msg 0", "Order msg 2"], actual_order

    def test_chat_endpoint_returns_conversation_id(self, app, client):
        """POST /api/v1/ai/chat returns conversation_id (if provider available)."""
        self._login(client)
        resp = client.post("/api/v1/ai/chat", json={
            "messages": [{"role": "user", "content": "Hi"}],
        })
        data = resp.get_json()
        if resp.status_code == 200:
            assert "conversation_id" in data, f"Missing conversation_id in {data}"