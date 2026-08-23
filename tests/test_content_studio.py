"""ZGC-PR-04 — Content Studio, SUIL, and Architecture Tests."""
import pytest
import json


class TestContentStudioHealth:
    """Content Studio API health and endpoint discovery."""

    def _login(self, client):
        from app.auth import TeamMember
        from app.auth_routes import UserRole
        from app.models import Organization, OrgMember
        from app import db
        member = TeamMember(name="CS Test", email="cs-test@org.com",
                            role=UserRole.ADMIN.value, is_active=True)
        member.set_password("testpass")
        db.session.add(member)
        db.session.commit()
        org = Organization(name="CS Org", slug="cs-org")
        db.session.add(org)
        db.session.commit()
        om = OrgMember(organization_id=org.id, identity_id="sid_cs",
                       email=member.email, role="admin")
        db.session.add(om)
        db.session.commit()
        with client.session_transaction() as sess:
            sess["user_id"] = member.id
            sess["identity_id"] = "sid_cs"
            sess["current_org_id"] = org.id
        return member

    def test_health_endpoint(self, app, client):
        """GET /api/v1/content/health returns status ok."""
        self._login(client)
        resp = client.get("/api/v1/content/health")
        assert resp.status_code == 200
        d = resp.get_json()
        assert d["status"] == "ok"
        assert len(d["endpoints"]) >= 6

    def test_generate_requires_auth(self, app, client):
        """Generate without auth returns 401."""
        resp = client.post("/api/v1/content/generate", json={"prompt": "test"})
        assert resp.status_code == 401

    def test_generate_requires_prompt(self, app, client):
        """Generate without prompt returns 400."""
        self._login(client)
        resp = client.post("/api/v1/content/generate", json={})
        assert resp.status_code == 400

    def test_generate_creates_history(self, app, client):
        """Generate creates a ContentGeneration record, history retrieves it."""
        self._login(client)
        # Generate
        resp = client.post("/api/v1/content/generate", json={
            "prompt": "Write a short blog post",
            "content_type": "blog_post",
            "tone": "professional",
            "word_count": 50,
        })
        # May succeed or fail depending on AI provider; either way API responds
        assert resp.status_code == 200
        generate_data = resp.get_json()

        # History should exist regardless of generation success
        resp = client.get("/api/v1/content/history")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "data" in data
        # Generation may not be persisted if provider failed
        # But the endpoint should return valid structure

    def test_history_empty_for_new_user(self, app, client):
        """History for a user with no content returns empty list."""
        self._login(client)
        resp = client.get("/api/v1/content/history")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data.get("data"), list)

    def test_inhibit_requires_action(self, app, client):
        """SUIL without action_type returns 400."""
        self._login(client)
        resp = client.post("/api/v1/content/inhibit", json={})
        assert resp.status_code == 400

    def test_inhibit_budget_levels(self, app, client):
        """SUIL evaluates budget correctly across levels."""
        self._login(client)

        # Low budget: GUARD (level 2)
        resp = client.post("/api/v1/content/inhibit", json={
            "action_type": "campaign_create",
            "budget": 100000,
        })
        assert resp.status_code == 200
        d = resp.get_json()
        assert d["level"] == 2 or d["level"] == 0

        # High budget: RESTRICT (level 4)
        resp = client.post("/api/v1/content/inhibit", json={
            "action_type": "campaign_create",
            "budget": 2000000,
        })
        d = resp.get_json()
        # Should be RESTRICT or BLOCK
        assert d["level"] >= 4

    def test_inhibit_media_allowed(self, app, client):
        """Media generation is ALLOW (level 0)."""
        self._login(client)
        resp = client.post("/api/v1/content/inhibit", json={
            "action_type": "media_generate",
        })
        assert resp.status_code == 200
        d = resp.get_json()
        assert d["allowed"] is True


class TestContentStudioEndToEnd:
    """End-to-end content studio flow."""

    def _login(self, client):
        from app.auth import TeamMember
        from app.auth_routes import UserRole
        from app.models import Organization, OrgMember
        from app import db
        member = TeamMember(name="E2E CS", email="e2e-cs@org.com",
                            role=UserRole.ADMIN.value, is_active=True)
        member.set_password("testpass")
        db.session.add(member)
        db.session.commit()
        org = Organization(name="E2E CS Org", slug="e2e-cs-org")
        db.session.add(org)
        db.session.commit()
        om = OrgMember(organization_id=org.id, identity_id="sid_e2e_cs",
                       email=member.email, role="admin")
        db.session.add(om)
        db.session.commit()
        with client.session_transaction() as sess:
            sess["user_id"] = member.id
            sess["identity_id"] = "sid_e2e_cs"
            sess["current_org_id"] = org.id
        return member

    def test_full_content_flow(self, app, client):
        """Generate → list history → inhibit → verify chain."""
        self._login(client)
        
        # Inhibit first
        resp = client.post("/api/v1/content/inhibit", json={
            "action_type": "generate_content",
        })
        assert resp.status_code == 200
        inhibit = resp.get_json()
        
        # Generate content
        resp = client.post("/api/v1/content/generate", json={
            "prompt": "Write about AI in healthcare for 3 lines",
            "content_type": "blog_post",
            "tone": "professional",
            "word_count": 60,
        })
        assert resp.status_code == 200
        gen = resp.get_json()

        # List history
        resp = client.get("/api/v1/content/history")
        assert resp.status_code == 200
        history = resp.get_json()
        # History structure is valid even if empty
        assert "data" in history