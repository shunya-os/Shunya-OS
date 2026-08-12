"""FDA13 — Customer Experience tests.

Customer profile, history, commitments, escalations, retention, issues.
"""
import pytest


@pytest.fixture
def seeded_customer_id(app, client):
    """Create a lead and convert to customer. Returns (customer_id, lead_id)."""
    from app.crm.service import create_lead_with_identity, convert_to_customer
    with app.app_context():
        lead = create_lead_with_identity(
            tenant_id=1, name="CX Test", phone="+1-555-CX",
            email="cx@test.com", source="api",
        )
        cust = convert_to_customer(lead, 1)
        return cust.id, lead.id


class TestCustomerProfile:
    def test_profile_returns_customer_context(self, app, seeded_customer_id):
        from app.customer_experience.service import get_customer_profile
        cid, _ = seeded_customer_id
        with app.app_context():
            profile = get_customer_profile(cid)
        assert profile is not None
        assert profile["name"] == "CX Test"
        assert "history" in profile

    def test_profile_unknown_customer(self, app, client):
        from app.customer_experience.service import get_customer_profile
        profile = get_customer_profile(999999)
        assert profile is None


class TestCustomerHistory:
    def test_history_returns_timeline(self, app, seeded_customer_id):
        from app.customer_experience.service import get_customer_history
        cid, _ = seeded_customer_id
        with app.app_context():
            history = get_customer_history(cid)
        assert len(history) >= 1
        assert any(e["event_type"] == "customer.converted" for e in history)


class TestCommitments:
    def test_create_commitment(self, app, client):
        from app.customer_experience.service import create_commitment
        with app.app_context():
            cm = create_commitment(
                title="Test commitment",
                relationship_id=None,
                owner="agent_1",
                issue_type="service",
            )
            assert cm.id is not None
            assert cm.status == "pending"
            assert cm.issue_type == "service"

    def test_resolve_commitment(self, app, client):
        from app.customer_experience.service import create_commitment, resolve_commitment
        with app.app_context():
            cm = create_commitment(title="Resolve me", relationship_id=None)
            result = resolve_commitment(cm.id)
            assert result["status"] == "completed"


class TestEscalations:
    def test_create_escalation(self, app, client):
        from app.customer_experience.service import create_escalation
        with app.app_context():
            cm = create_escalation(relationship_id=1, summary="Urgent issue")
            assert cm.issue_type == "escalation"
            assert "ESCALATION" in cm.title


class TestIssues:
    def test_create_issue(self, app, client):
        from app.customer_experience.service import create_issue
        with app.app_context():
            cm = create_issue(relationship_id=1, title="Bug report", severity="high")
            assert cm.issue_type == "issue"
            assert "[HIGH]" in cm.title


class TestRetention:
    def test_retention_signals_new_customer(self, app, seeded_customer_id):
        from app.customer_experience.service import get_retention_signals
        cid, _ = seeded_customer_id
        with app.app_context():
            signals = get_retention_signals(cid)
        assert "risk" in signals
        assert "signals" in signals
        assert "note" in signals

    def test_retention_unknown_customer(self, app, client):
        from app.customer_experience.service import get_retention_signals
        signals = get_retention_signals(999999)
        assert signals["risk"] == "unknown"


class TestApiRoutes:
    def test_get_customer_profile_route(self, app, client, seeded_customer_id):
        cid, _ = seeded_customer_id
        r = client.get(f"/api/v1/customer/profile/{cid}")
        assert r.status_code == 200
        data = r.get_json()
        assert data["name"] == "CX Test"

    def test_create_commitment_route(self, app, client):
        r = client.post("/api/v1/customer/commitments", json={
            "title": "API commitment", "owner": "agent_1",
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["status"] == "pending"

    def test_create_escalation_route(self, app, client):
        r = client.post("/api/v1/customer/escalations", json={
            "relationship_id": 1, "summary": "API escalation",
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["issue_type"] == "escalation"

    def test_create_issue_route(self, app, client):
        r = client.post("/api/v1/customer/issues", json={
            "relationship_id": 1, "title": "API issue", "severity": "low",
        })
        assert r.status_code == 201
        data = r.get_json()
        assert "[LOW]" in data["title"]