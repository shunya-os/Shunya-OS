"""G4 — Universal Revenue, Relationship & Commercial Execution Tests.

Tests the full commercial lifecycle with production-style test infrastructure.
Uses the app/client fixtures from conftest.py.
"""

import json
from datetime import datetime, timedelta, timezone

from app import db
from app.commercial.models import (
    CommercialOpportunity,
    CommercialProposal,
    CommercialTransition,
    OPPORTUNITY_STATES,
    VALID_TRANSITIONS,
    is_valid_lifecycle_transition,
)
from app.commercial.service import (
    create_opportunity,
    transition_opportunity,
    create_proposal,
    transition_proposal,
    get_commercial_context,
    get_commercial_intelligence,
    get_opportunities_needing_attention,
    get_upcoming_follow_ups,
)
from app.commitments.models import Commitment


# ══════════════════════════════════════════════════════════════════════
# 1. Lifecycle State Machine
# ══════════════════════════════════════════════════════════════════════


class TestLifecycleTransitions:
    """Verify the state machine rules (no DB needed)."""

    def test_valid_transition(self):
        assert is_valid_lifecycle_transition("discovered", "active")

    def test_invalid_transition(self):
        assert not is_valid_lifecycle_transition("discovered", "completed")

    def test_terminal_states(self):
        assert VALID_TRANSITIONS["completed"] == []

    def test_all_states_covered(self):
        for state in OPPORTUNITY_STATES:
            assert state in VALID_TRANSITIONS, f"Missing transition map for {state}"


# ══════════════════════════════════════════════════════════════════════
# 2. Service Layer: Create & Transition
# ══════════════════════════════════════════════════════════════════════


class TestOpportunityService:
    """Test the opportunity service layer with real DB."""

    def test_create_opportunity(self, app):
        with app.app_context():
            opp = create_opportunity(
                organization_id=1,
                title="Test Opportunity",
                description="Test",
                estimated_value=100000,
                source="email",
                created_by="test_user",
            )
            assert opp.id is not None
            assert opp.lifecycle_state == "discovered"

            # Verify transition audit
            t = CommercialTransition.query.filter_by(
                entity_type="opportunity", entity_id=opp.id
            ).first()
            assert t is not None
            assert t.to_state == "discovered"

    def test_transition_opportunity(self, app):
        with app.app_context():
            opp = create_opportunity(
                organization_id=1, title="Transitions", created_by="user",
            )
            success, error = transition_opportunity(
                opp, "active", "Qualified", triggered_by="user"
            )
            assert success
            assert opp.lifecycle_state == "active"

            success, error = transition_opportunity(
                opp, "proposal_pending", "Sent", triggered_by="user"
            )
            assert success
            assert opp.lifecycle_state == "proposal_pending"

    def test_invalid_transition_rejected(self, app):
        with app.app_context():
            opp = create_opportunity(
                organization_id=1, title="Invalid", created_by="user",
            )
            success, error = transition_opportunity(opp, "completed")
            assert not success
            assert "Invalid transition" in error

    def test_correction_requires_reason(self, app):
        with app.app_context():
            opp = create_opportunity(
                organization_id=1, title="Correction", created_by="user",
            )
            transition_opportunity(opp, "active", triggered_by="user")
            success, error = transition_opportunity(
                opp, "discovered", is_correction=True, correction_reason=""
            )
            assert not success
            assert "Correction requires a reason" in error

    def test_idempotent_transition(self, app):
        with app.app_context():
            opp = create_opportunity(
                organization_id=1, title="Idempotent", created_by="user",
            )
            success, _ = transition_opportunity(opp, "discovered")
            assert success  # Same state should be idempotent

    def test_lifecycle_history(self, app):
        with app.app_context():
            opp = create_opportunity(
                organization_id=1, title="History", created_by="user",
            )
            transition_opportunity(opp, "active", triggered_by="u1")
            transition_opportunity(opp, "waiting", triggered_by="u1")
            transition_opportunity(opp, "active", triggered_by="u2")
            history = json.loads(opp.lifecycle_history)
            assert len(history) == 4  # create + 3 transitions


# ══════════════════════════════════════════════════════════════════════
# 3. Proposal Tests
# ══════════════════════════════════════════════════════════════════════


class TestProposalService:
    """Test proposal creation and lifecycle."""

    def test_create_proposal(self, app):
        with app.app_context():
            p = create_proposal(
                organization_id=1, title="Test Proposal",
                total_value=50000, created_by="user",
            )
            assert p.id is not None
            assert p.status == "draft"
            assert p.total_value == 50000

    def test_proposal_sent(self, app):
        with app.app_context():
            p = create_proposal(
                organization_id=1, title="Send", created_by="user",
            )
            success, error, _ = transition_proposal(p, "sent", triggered_by="user")
            assert success
            assert p.status == "sent"
            assert p.sent_at is not None

    def test_proposal_accept_triggers_commitment(self, app):
        with app.app_context():
            p = create_proposal(
                organization_id=1, title="Accept ✦ Commit",
                total_value=75000, created_by="user",
            )
            transition_proposal(p, "sent", triggered_by="user")
            success, error, decision = transition_proposal(
                p, "accepted", triggered_by="client"
            )
            assert success
            assert p.status == "accepted"
            assert decision["commitment_created"]
            assert decision["execution_started"]
            c = db.session.get(Commitment, int(decision["commitment_id"]))
            assert c is not None

    def test_proposal_invalid_transition(self, app):
        with app.app_context():
            p = create_proposal(
                organization_id=1, title="Bad Trans", created_by="user",
            )
            success, error, _ = transition_proposal(p, "accepted", triggered_by="user")
            assert not success

    def test_proposal_decline(self, app):
        with app.app_context():
            p = create_proposal(
                organization_id=1, title="Declined", created_by="user",
            )
            transition_proposal(p, "sent", triggered_by="user")
            transition_proposal(p, "declined", reason="No budget", triggered_by="user")
            assert p.status == "declined"
            assert "No budget" in p.rejection_reason


# ══════════════════════════════════════════════════════════════════════
# 4. Commercial Context
# ══════════════════════════════════════════════════════════════════════


class TestCommercialContext:
    """Test commercial context integration."""

    def test_context_created_with_opportunity(self, app):
        with app.app_context():
            # Use valid org_id=1 and rel_id=1 (seeded by app initialization)
            # First, ensure they exist
            from app.relationship.models import CanonicalRelationship as Rel
            from app.models import Organization
            org = Organization.query.first()
            if not org:
                org = Organization(name="Test Org", slug="test-org")
                db.session.add(org)
                db.session.flush()
            rel = Rel(
                organization_id=org.id,
                display_name="Test Person",
                relationship_type="customer",
            )
            db.session.add(rel)
            db.session.flush()

            opp = create_opportunity(
                organization_id=org.id, title="Ctx Test",
                relationship_id=rel.id, created_by="user",
            )
            ctx = get_commercial_context(org.id, rel.id)
            assert ctx is not None
            assert ctx["active_opportunity"]["id"] == opp.id

    def test_context_returns_none_for_nonexistent(self, app):
        with app.app_context():
            ctx = get_commercial_context(99999, 99999)
            assert ctx is None


# ══════════════════════════════════════════════════════════════════════
# 5. Follow-up / Awareness
# ══════════════════════════════════════════════════════════════════════


class TestFollowUpAwareness:
    """Test awareness integration."""

    def test_stale_opportunity_flagged(self, app):
        with app.app_context():
            opp = create_opportunity(
                organization_id=1, title="Stale", created_by="u",
            )
            opp.state_changed_at = datetime.now(timezone.utc) - timedelta(days=5)
            opp.lifecycle_state = "waiting"
            db.session.flush()
            needs = get_opportunities_needing_attention(1)
            assert any(n["title"] == "Stale" for n in needs)

    def test_overdue_action_flagged(self, app):
        with app.app_context():
            opp = create_opportunity(
                organization_id=1, title="Late", created_by="u",
            )
            opp.next_action = "Call"
            opp.next_action_due_at = datetime.now(timezone.utc) - timedelta(hours=3)
            db.session.flush()
            needs = get_opportunities_needing_attention(1)
            assert any(n["title"] == "Late" for n in needs)

    def test_upcoming_followups(self, app):
        with app.app_context():
            opp = create_opportunity(
                organization_id=1, title="Soon", created_by="u",
            )
            opp.next_action = "Send docs"
            opp.next_action_due_at = datetime.now(timezone.utc) + timedelta(hours=6)
            db.session.flush()
            upcoming = get_upcoming_follow_ups(1, within_hours=48)
            assert any(u["title"] == "Soon" for u in upcoming)


# ══════════════════════════════════════════════════════════════════════
# 6. Commercial Intelligence
# ══════════════════════════════════════════════════════════════════════


class TestCommercialIntelligence:
    """Test intelligence aggregation."""

    def test_empty_intelligence(self, app):
        with app.app_context():
            info = get_commercial_intelligence(1)
            assert info["total_opportunities"] == 0
            assert info["total_active_value"] == 0.0

    def test_intelligence_with_data(self, app):
        with app.app_context():
            create_opportunity(organization_id=1, title="Active 1", estimated_value=50000, created_by="u")
            opp2 = create_opportunity(organization_id=1, title="Active 2", estimated_value=100000, created_by="u")
            transition_opportunity(opp2, "active", triggered_by="u")

            info = get_commercial_intelligence(1)
            assert info["total_opportunities"] >= 2
            assert info["total_active_value"] >= 100000

    def test_urgent_count(self, app):
        with app.app_context():
            for i in range(3):
                create_opportunity(organization_id=1, title=f"Urgent {i}", urgency=90, created_by="u")
            info = get_commercial_intelligence(1)
            assert info["urgent_opportunities"] >= 3


# ══════════════════════════════════════════════════════════════════════
# 7. Tenant Isolation
# ══════════════════════════════════════════════════════════════════════


class TestTenantIsolation:
    """Verify data isolation between organizations."""

    def test_opportunity_isolation(self, app):
        with app.app_context():
            create_opportunity(organization_id=1, title="Org1", created_by="u")
            create_opportunity(organization_id=2, title="Org2", created_by="u")
            assert CommercialOpportunity.query.filter_by(organization_id=1).count() == 1
            assert CommercialOpportunity.query.filter_by(organization_id=2).count() == 1

    def test_proposal_isolation(self, app):
        with app.app_context():
            create_proposal(organization_id=1, title="P1", created_by="u")
            create_proposal(organization_id=2, title="P2", created_by="u")
            assert CommercialProposal.query.filter_by(organization_id=1).count() == 1
            assert CommercialProposal.query.filter_by(organization_id=2).count() == 1

    def test_transition_isolation(self, app):
        with app.app_context():
            o1 = create_opportunity(organization_id=1, title="T1", created_by="u")
            o2 = create_opportunity(organization_id=2, title="T2", created_by="u")
            transition_opportunity(o1, "active", triggered_by="u")
            transition_opportunity(o2, "active", triggered_by="u")
            assert CommercialTransition.query.filter_by(organization_id=1).count() >= 1


# ══════════════════════════════════════════════════════════════════════
# 8. End-to-End Scenario
# ══════════════════════════════════════════════════════════════════════


class TestEndToEnd:
    """Full commercial lifecycle end-to-end."""

    def test_full_commercial_path(self, app):
        with app.app_context():
            from app.relationship.models import CanonicalRelationship as Rel
            from app.models import Organization
            org = Organization.query.first()
            if not org:
                org = Organization(name="E2E Org", slug="e2e-org")
                db.session.add(org)
                db.session.flush()
            rel = Rel(
                organization_id=org.id, display_name="Client",
                relationship_type="customer",
            )
            db.session.add(rel)
            db.session.flush()

            # 1. Create opportunity
            opp = create_opportunity(
                organization_id=org.id, title="E2E Deal",
                relationship_id=rel.id, estimated_value=200000,
                currency="USD", source="referral", created_by="founder",
            )
            assert opp.lifecycle_state == "discovered"

            # 2. Qualify → active
            transition_opportunity(opp, "active", "Qualified", triggered_by="founder")
            assert opp.lifecycle_state == "active"

            # 3. Create & send proposal
            prop = create_proposal(
                organization_id=org.id, relationship_id=rel.id,
                opportunity_id=opp.id, title="Enterprise Deal Proposal",
                total_value=200000, created_by="founder",
            )
            transition_proposal(prop, "sent", triggered_by="founder")
            assert prop.status == "sent"

            # 4. Accept → commitment + execution
            transition_opportunity(opp, "proposal_pending", "Proposal sent", triggered_by="founder")
            success, error, decision = transition_proposal(
                prop, "accepted", triggered_by="client"
            )
            assert success
            assert decision["commitment_created"]
            assert decision["execution_id"] is not None

            # 5. Verify commercial context
            ctx = get_commercial_context(org.id, rel.id)
            assert ctx is not None


# ══════════════════════════════════════════════════════════════════════
# 9. API Route Tests
# ══════════════════════════════════════════════════════════════════════


class TestApiRoutes:
    """Test commercial API endpoints."""

    def _seed_org(self):
        """Seed an org with owner role and member."""
        from app.models import Organization, OrgMember
        from app.authz.services import seed_default_roles
        from app.authz.models import Role, OrgMemberRole

        org = Organization(id=1, name="Test Org", slug="test-org")
        db.session.add(org)
        db.session.flush()
        seed_default_roles(1)
        owner_role = db.session.query(Role).filter_by(organization_id=1, name="owner").first()
        member = OrgMember(
            organization_id=1, identity_id="admin@test.com",
            email="admin@test.com", role="owner", is_active=True,
        )
        db.session.add(member)
        db.session.flush()
        if owner_role:
            assignment = OrgMemberRole(
                organization_id=1, member_id=member.id,
                role_id=owner_role.id, scope="organization",
                granted_by="system",
            )
            db.session.add(assignment)
        db.session.commit()

    def test_list_unauthorized(self, client):
        resp = client.get("/api/v1/commercial/opportunities")
        assert resp.status_code == 401

    def test_create_opportunity_api(self, app, client):
        with app.app_context():
            self._seed_org()
            from app.auth import TeamMember
            admin = TeamMember(name="Admin", email="admin@test.com", role="admin", is_active=True)
            admin.set_password("x")
            admin.generate_token()
            db.session.add(admin)
            db.session.commit()
            admin_id = admin.id
            with client.session_transaction() as s:
                s["current_org_id"] = 1
                s["user_id"] = admin_id
                s["identity_id"] = "admin@test.com"
            resp = client.post(
                "/api/v1/commercial/opportunities",
                json={"title": "API Opp", "estimated_value": 50000},
            )
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["success"]
            assert data["opportunity"]["title"] == "API Opp"

    def test_get_intelligence_api(self, app, client):
        with app.app_context():
            self._seed_org()
            from app.auth import TeamMember
            admin = TeamMember(name="Admin", email="admin@test.com", role="admin", is_active=True)
            admin.set_password("x")
            admin.generate_token()
            db.session.add(admin)
            db.session.commit()
            admin_id = admin.id
            with client.session_transaction() as s:
                s["current_org_id"] = 1
                s["user_id"] = admin_id
                s["identity_id"] = "admin@test.com"
            resp = client.get("/api/v1/commercial/intelligence")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"]
            assert "intelligence" in data

    def test_list_opportunities_authorized(self, app, client):
        with app.app_context():
            self._seed_org()
            from app.auth import TeamMember
            admin = TeamMember(name="Admin", email="admin@test.com", role="admin", is_active=True)
            admin.set_password("x")
            admin.generate_token()
            db.session.add(admin)
            db.session.commit()
            admin_id = admin.id
            with client.session_transaction() as s:
                s["current_org_id"] = 1
                s["user_id"] = admin_id
                s["identity_id"] = "admin@test.com"
            resp = client.get("/api/v1/commercial/opportunities")
            assert resp.status_code == 200
            assert resp.get_json()["success"]


# ══════════════════════════════════════════════════════════════════════
# 10. Serialization Tests
# ══════════════════════════════════════════════════════════════════════


class TestSerialization:
    """Verify model serializations are complete."""

    def test_opportunity_dict_keys(self, app):
        with app.app_context():
            opp = create_opportunity(organization_id=1, title="Ser", created_by="u")
            d = opp.to_dict()
            for k in ["id", "title", "lifecycle_state", "created_at"]:
                assert k in d

    def test_proposal_dict_keys(self, app):
        with app.app_context():
            p = create_proposal(organization_id=1, title="Ser", created_by="u")
            d = p.to_dict()
            for k in ["id", "title", "status", "can_accept"]:
                assert k in d

    def test_transition_dict_keys(self, app):
        with app.app_context():
            opp = create_opportunity(organization_id=1, title="TSer", created_by="u")
            transition_opportunity(opp, "active", triggered_by="u")
            t = CommercialTransition.query.filter_by(entity_id=opp.id).first()
            d = t.to_dict()
            for k in ["from_state", "to_state", "triggered_by"]:
                assert k in d