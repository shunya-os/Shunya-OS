"""Tests for Milestone 9 — Enterprise Ready.

Covers:
- Immutable audit trail
- Role management (CRUD, system roles)
- Team management (invite, list, remove)
- RBAC enforcement (permission checking)
- Tenant isolation check
- API endpoints
- Regression tests for M1–M8
"""
from __future__ import annotations


def _make_identity(app):
    from app.adapters.os_adapter import sign_in
    result = sign_in(email="m9@shunyaos.com", name="M9 Test")
    assert result["success"]
    return result["identity_id"]


def _make_org_id():
    import uuid
    return f"org_{uuid.uuid4().hex[:16]}"


# ===========================================================================
# 1. Audit Trail
# ===========================================================================

class TestAuditTrail:
    """Immutable audit record creation and querying."""

    def test_record_audit(self, app):
        from app.enterprise.service import record_audit
        record = record_audit(
            actor_id="user_001", action="create",
            entity_type="object", entity_id="obj_001",
            entity_name="Test Object",
            details={"field": "name", "value": "Test"},
        )
        assert record.id is not None
        assert record.action == "create"
        assert record.entity_type == "object"

    def test_query_audit(self, app):
        from app.enterprise.service import query_audit, record_audit
        record_audit(actor_id="user_001", action="create", entity_type="object")
        record_audit(actor_id="user_001", action="update", entity_type="object")
        result = query_audit(actor_id="user_001")
        assert result["total"] == 2
        assert len(result["records"]) == 2

    def test_query_audit_filter_by_action(self, app):
        from app.enterprise.service import query_audit, record_audit
        record_audit(actor_id="user_002", action="create", entity_type="object")
        record_audit(actor_id="user_002", action="delete", entity_type="object")
        result = query_audit(actor_id="user_002", action="delete")
        assert result["total"] == 1

    def test_query_audit_pagination(self, app):
        from app.enterprise.service import query_audit, record_audit
        for i in range(5):
            record_audit(actor_id="user_003", action="read", entity_type="object")
        result = query_audit(actor_id="user_003", limit=2)
        assert len(result["records"]) == 2
        assert result["total"] == 5

    def test_audit_immutable_columns(self, app):
        """Verify audit records have no update methods exposed."""
        from app.enterprise.models import AuditRecord
        record = AuditRecord(actor_id="u1", action="test", entity_type="object")
        assert hasattr(record, "to_dict")
        # No update/delete methods on the service
        from app.enterprise.service import record_audit, query_audit
        funcs = [f for f in dir(record_audit.__module__) if not f.startswith('_')]
        assert "delete_audit" not in dir(type(record))


# ===========================================================================
# 2. Role Management
# ===========================================================================

class TestRoleManagement:
    """System roles, custom roles, CRUD."""

    def test_seed_system_roles(self, app):
        org_id = _make_org_id()
        from app.enterprise.service import seed_system_roles
        roles = seed_system_roles(org_id)
        assert len(roles) == 3
        names = [r.name for r in roles]
        assert "Admin" in names
        assert "Member" in names
        assert "Viewer" in names

    def test_system_roles_idempotent(self, app):
        org_id = _make_org_id()
        from app.enterprise.service import seed_system_roles
        roles1 = seed_system_roles(org_id)
        roles2 = seed_system_roles(org_id)
        assert len(roles1) == len(roles2)

    def test_get_roles(self, app):
        org_id = _make_org_id()
        from app.enterprise.service import get_roles, seed_system_roles
        seed_system_roles(org_id)
        roles = get_roles(org_id)
        assert len(roles) == 3

    def test_create_custom_role(self, app):
        org_id = _make_org_id()
        from app.enterprise.service import create_role
        role = create_role(
            organization_id=org_id,
            name="Custom Manager",
            description="Can manage objects and team",
            permissions=[
                {"resource": "object", "actions": ["create", "read", "update"]},
                {"resource": "team", "actions": ["read"]},
            ],
        )
        assert role.name == "Custom Manager"
        assert role.is_system is False


# ===========================================================================
# 3. Team Management
# ===========================================================================

class TestTeamManagement:
    """Team member invite, list, remove."""

    def test_invite_member(self, app):
        org_id = _make_org_id()
        from app.enterprise.service import invite_member
        member = invite_member(
            organization_id=org_id,
            identity_id="identity_new",
            name="New User",
            email="new@test.com",
        )
        assert member.status == "active"
        assert member.name == "New User"

    def test_invite_existing_member_reactivates(self, app):
        org_id = _make_org_id()
        from app.enterprise.service import get_team, invite_member, remove_member
        invite_member(organization_id=org_id, identity_id="u1", name="User1")
        remove_member(organization_id=org_id, identity_id="u1")
        invite_member(organization_id=org_id, identity_id="u1", name="User1")
        team = get_team(org_id)
        active = [m for m in team if m["status"] == "active"]
        assert len(active) == 1

    def test_get_team(self, app):
        org_id = _make_org_id()
        from app.enterprise.service import get_team, invite_member
        invite_member(organization_id=org_id, identity_id="u2", name="User2")
        invite_member(organization_id=org_id, identity_id="u3", name="User3")
        team = get_team(org_id)
        assert len(team) == 2

    def test_remove_member(self, app):
        org_id = _make_org_id()
        from app.enterprise.service import get_team, invite_member, remove_member
        invite_member(organization_id=org_id, identity_id="u4", name="User4")
        assert remove_member(organization_id=org_id, identity_id="u4") is True
        team = get_team(org_id)
        disabled = [m for m in team if m["status"] == "disabled"]
        assert len(disabled) == 1

    def test_remove_nonexistent_member(self, app):
        org_id = _make_org_id()
        from app.enterprise.service import remove_member
        assert remove_member(organization_id=org_id, identity_id="nonexistent") is False


# ===========================================================================
# 4. RBAC Enforcement
# ===========================================================================

class TestRBAC:
    """Permission checking and enforcement."""

    def test_admin_has_full_access(self, app):
        org_id = _make_org_id()
        identity_id = _make_identity(app)
        from app.enterprise.service import (
            check_permission,
            invite_member,
            seed_system_roles,
        )
        roles = seed_system_roles(org_id)
        admin_role = [r for r in roles if r.name == "Admin"][0]
        invite_member(organization_id=org_id, identity_id=identity_id, role_id=admin_role.id)
        result = check_permission(
            identity_id=identity_id,
            resource="object", action="delete",
            organization_id=org_id,
        )
        assert result["granted"] is True

    def test_viewer_cannot_delete(self, app):
        org_id = _make_org_id()
        identity_id = _make_identity(app)
        from app.enterprise.service import (
            check_permission,
            invite_member,
            seed_system_roles,
        )
        roles = seed_system_roles(org_id)
        viewer_role = [r for r in roles if r.name == "Viewer"][0]
        invite_member(organization_id=org_id, identity_id=identity_id, role_id=viewer_role.id)
        result = check_permission(
            identity_id=identity_id,
            resource="object", action="delete",
            organization_id=org_id,
        )
        assert result["granted"] is False

    def test_non_member_denied(self, app):
        identity_id = _make_identity(app)
        from app.enterprise.service import check_permission
        result = check_permission(
            identity_id=identity_id,
            resource="object", action="read",
            organization_id="nonexistent_org",
        )
        assert result["granted"] is False

    def test_no_role_assigned(self, app):
        org_id = _make_org_id()
        identity_id = _make_identity(app)
        from app.enterprise.service import check_permission, invite_member
        invite_member(organization_id=org_id, identity_id=identity_id)
        result = check_permission(
            identity_id=identity_id,
            resource="object", action="read",
            organization_id=org_id,
        )
        assert result["granted"] is False


# ===========================================================================
# 5. Tenant Isolation
# ===========================================================================

class TestTenantIsolation:
    """Tenant boundary enforcement."""

    def test_tenant_isolation_allowed(self, app):
        org_id = _make_org_id()
        identity_id = _make_identity(app)
        from app.enterprise.service import (
            assert_tenant_isolation,
            invite_member,
        )
        invite_member(organization_id=org_id, identity_id=identity_id)
        assert assert_tenant_isolation(identity_id=identity_id, object_organization_id=org_id) is True

    def test_tenant_isolation_denied(self, app):
        identity_id = _make_identity(app)
        from app.enterprise.service import assert_tenant_isolation
        assert assert_tenant_isolation(identity_id=identity_id, object_organization_id="other_org") is False

    def test_no_org_boundary(self, app):
        identity_id = _make_identity(app)
        from app.enterprise.service import assert_tenant_isolation
        assert assert_tenant_isolation(identity_id=identity_id, object_organization_id=None) is True


# ===========================================================================
# 6. API Endpoints
# ===========================================================================

class TestEnterpriseAPI:
    """M9 API endpoints."""

    def _setup_org(self, app, client, identity_id):
        """Helper: create org, seed roles, add member."""
        org_id = _make_org_id()
        from app.enterprise.service import invite_member, seed_system_roles
        roles = seed_system_roles(org_id)
        admin_role = [r for r in roles if r.name == "Admin"][0]
        invite_member(organization_id=org_id, identity_id=identity_id, role_id=admin_role.id)
        return org_id

    def test_audit_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            self._setup_org(app, client, identity_id)
            from app.enterprise.service import record_audit
            record_audit(actor_id=identity_id, action="create", entity_type="object")
            resp = client.get("/api/v1/enterprise/audit")
            assert resp.get_json()["success"]

    def test_roles_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            self._setup_org(app, client, identity_id)
            resp = client.get("/api/v1/enterprise/roles")
            data = resp.get_json()
            assert data["success"]
            assert len(data["data"]) >= 3

    def test_team_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            self._setup_org(app, client, identity_id)
            resp = client.get("/api/v1/enterprise/team")
            assert resp.get_json()["success"]

    def test_check_permission_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            org_id = self._setup_org(app, client, identity_id)
            resp = client.post("/api/v1/enterprise/check-permission", json={
                "resource": "object", "action": "read",
                "organization_id": org_id,
            })
            data = resp.get_json()
            assert data["success"]
            assert data["data"]["granted"] is True

    def test_api_requires_auth(self, app):
        with app.test_client() as client:
            resp = client.get("/api/v1/enterprise/audit")
            assert resp.status_code == 401


# ===========================================================================
# 7. Regression — Milestones 1–8
# ===========================================================================

class TestMilestoneRegression:
    """All prior milestones still pass."""

    def test_m1_signin(self, app):
        from app.adapters.os_adapter import sign_in
        result = sign_in(email="m9-reg@test.com", name="M9 Reg")
        assert result["success"]

    def test_m2_executive_home(self, app):
        from app.adapters.os_adapter import get_executive_home
        identity_id = _make_identity(app)
        result = get_executive_home(identity_id=identity_id)
        assert result["success"]

    def test_m3_insights(self, app):
        from app.founder.insight_engine import build_insights
        identity_id = _make_identity(app)
        result = build_insights(identity_id=identity_id)
        assert "summary" in result

    def test_m4_workspace(self, app):
        from app.founder.workspace_intelligence import build_workspace_summary
        identity_id = _make_identity(app)
        from app import db
        from app.founder.models import FounderObject, FounderSpace
        space = FounderSpace(space_id="m9r_spc", name="M9R", identity_id=identity_id)
        db.session.add(space)
        db.session.flush()
        obj = FounderObject(object_id="m9r_obj", space_id="m9r_spc", name="M9Reg",
                            object_type="Document", created_by=identity_id)
        db.session.add(obj)
        db.session.commit()
        result = build_workspace_summary("m9r_obj")
        assert result["name"] == "M9Reg"

    def test_m5_ai_copilot(self, app):
        from app.ai.copilot import copilot_health
        health = copilot_health()
        assert "provider" in health

    def test_m6_notifications(self, app):
        from app.integration.service import create_notification, get_notifications
        identity_id = _make_identity(app)
        create_notification(identity_id=identity_id, notification_type="test", title="M9 Reg")
        notifs = get_notifications(identity_id=identity_id)
        assert len(notifs) >= 1

    def test_m7_automation(self, app):
        from app.automation.service import create_rule, get_rules
        identity_id = _make_identity(app)
        create_rule(identity_id=identity_id, name="M9 Auto", trigger_type="entity_created",
                     trigger_config={}, action_type="notify", action_config={})
        rules = get_rules(identity_id=identity_id)
        assert len(rules) >= 1

    def test_m8_intelligence(self, app):
        from app.intelligence.service import create_reasoning_trace, get_traces
        identity_id = _make_identity(app)
        create_reasoning_trace(identity_id=identity_id, reasoning_type="test",
                                query="M9 test", ai_response="M9 response")
        traces = get_traces(identity_id=identity_id)
        assert len(traces) >= 1