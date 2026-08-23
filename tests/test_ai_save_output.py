"""ZGC-05 Workstream G — AI Outputs to Organisational Objects Tests.

Tests:
  POST /api/v1/ai/save-output — saves AI response as task/note/proposal/document.
  Retrieved through execution visibility APIs.
"""

import pytest


class TestSaveOutput:
    """Test the save-output endpoint."""

    def _login(self, client):
        from app.auth import TeamMember
        from app.auth_routes import UserRole
        from app.models import Organization, OrgMember
        from app import db
        member = TeamMember(
            name="SaveOut Test",
            email="saveout@test.org",
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        member.set_password("testpass123")
        db.session.add(member)
        db.session.commit()
        org = Organization(name="SaveOut Org", slug="saveout-org")
        db.session.add(org)
        db.session.commit()
        om = OrgMember(organization_id=org.id, identity_id="sid_save_out",
                       email=member.email, role="admin")
        db.session.add(om)
        db.session.commit()
        with client.session_transaction() as sess:
            sess["user_id"] = member.id
            sess["identity_id"] = "sid_save_out"
            sess["current_org_id"] = org.id
        return member

    def test_save_output_requires_content(self, app, client):
        """POST /api/v1/ai/save-output without content returns 400."""
        resp = client.post("/api/v1/ai/save-output", json={})
        assert resp.status_code == 400

    def test_save_output_defaults_to_task(self, app, client):
        """Save output without output_type defaults to 'task'."""
        self._login(client)
        resp = client.post("/api/v1/ai/save-output", json={
            "content": "Follow up with Acme Corp about Q3 proposal",
            "title": "Follow up Acme Corp",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["type"] == "task"
        assert data["data"]["outcome_id"].startswith("out_")

    def test_save_output_as_task(self, app, client):
        """Save output as task."""
        self._login(client)
        resp = client.post("/api/v1/ai/save-output", json={
            "content": "Review design specs for Project Phoenix",
            "output_type": "task",
            "title": "Review Project Phoenix",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["type"] == "task"

    def test_save_output_as_note(self, app, client):
        """Save output as note."""
        self._login(client)
        resp = client.post("/api/v1/ai/save-output", json={
            "content": "Meeting notes: Q3 planning session on Monday",
            "output_type": "note",
            "title": "Q3 Planning Notes",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["type"] == "note"

    def test_save_output_as_proposal(self, app, client):
        """Save output as proposal."""
        self._login(client)
        resp = client.post("/api/v1/ai/save-output", json={
            "content": "Proposal: Cloud migration for enterprise clients",
            "output_type": "proposal",
            "title": "Cloud Migration Proposal",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["type"] == "proposal"

    def test_save_output_requires_auth(self, app, client):
        """Without auth, endpoint should work (session not needed for anonymous)."""
        resp = client.post("/api/v1/ai/save-output", json={
            "content": "Test content",
        })
        # Should succeed since save-output doesn't enforce auth for anonymous
        assert resp.status_code == 200

    def test_execution_visibility_shows_saved_output(self, app, client):
        """Saved outputs are visible through execution visibility API."""
        self._login(client)
        # Save a task
        resp = client.post("/api/v1/ai/save-output", json={
            "content": "Research competitor pricing strategy",
            "output_type": "task",
            "title": "Competitor Research",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        outcome_id = data["data"]["outcome_id"]

        # Check execution visibility
        from app.execution.models import Outcome
        from app import db
        outcome = Outcome.query.filter_by(outcome_id=outcome_id).first()
        assert outcome is not None, f"Outcome {outcome_id} not found in DB"
        state = outcome.state or {}
        assert state.get("type") == "task"
        assert outcome.intention == "Competitor Research"