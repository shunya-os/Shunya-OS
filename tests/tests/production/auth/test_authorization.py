"""Tests for Authorization Middleware (Milestone X, D3).

Tests permission checking, authorization decorators, and org boundary enforcement.
"""

import pytest


@pytest.fixture(scope="function")
def _db(app):
    from app import db
    with app.app_context():
        yield db


@pytest.fixture(scope="function")
def admin_user(app, _db):
    from app.auth import TeamMember
    user = TeamMember(
        name="Admin", email="admin5@test.com",
        role="admin", is_active=True,
    )
    user.set_password("pass123456")
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture(scope="function")
def manager_user(app, _db):
    from app.auth import TeamMember
    user = TeamMember(
        name="Manager", email="manager@test.com",
        role="manager", is_active=True,
    )
    user.set_password("pass123456")
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture(scope="function")
def agent_user(app, _db):
    from app.auth import TeamMember
    user = TeamMember(
        name="Agent", email="agent@test.com",
        role="agent", is_active=True,
    )
    user.set_password("pass123456")
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture(scope="function")
def logged_in_admin(app, client, admin_user):
    with client.session_transaction() as session:
        session["user_id"] = admin_user.id
        session["_fresh"] = True
    return client


@pytest.fixture(scope="function")
def logged_in_agent(app, client, agent_user):
    with client.session_transaction() as session:
        session["user_id"] = agent_user.id
        session["_fresh"] = True
    return client


class TestPermissionChecks:
    """Permission registry and checking."""

    def test_admin_can_do_anything(self, admin_user):
        from app.production.auth.authorization_middleware import check_permission
        assert check_permission(admin_user, "org", "create") is True
        assert check_permission(admin_user, "org", "delete") is True
        assert check_permission(admin_user, "org", "admin") is True
        assert check_permission(admin_user, "user", "admin") is True

    def test_manager_has_restricted_delete(self, manager_user):
        from app.production.auth.authorization_middleware import check_permission
        assert check_permission(manager_user, "org", "read") is True
        assert check_permission(manager_user, "org", "update") is True
        assert check_permission(manager_user, "org", "delete") is False
        assert check_permission(manager_user, "workspace", "create") is True
        assert check_permission(manager_user, "user", "create") is True

    def test_agent_read_only(self, agent_user):
        from app.production.auth.authorization_middleware import check_permission
        assert check_permission(agent_user, "org", "read") is True
        assert check_permission(agent_user, "org", "create") is False
        assert check_permission(agent_user, "org", "update") is False
        assert check_permission(agent_user, "org", "delete") is False
        assert check_permission(agent_user, "workspace", "create") is False
        assert check_permission(agent_user, "user", "create") is False

    def test_agent_can_read_users(self, agent_user):
        from app.production.auth.authorization_middleware import check_permission
        assert check_permission(agent_user, "user", "read") is True

    def test_unknown_resource_fails(self, admin_user):
        from app.production.auth.authorization_middleware import check_permission
        assert check_permission(admin_user, "nonexistent", "read") is False


class TestAuthorizationDecorator:
    """@require_permission decorator behavior."""

    def test_admin_can_access_admin_endpoint(self, logged_in_admin):
        from flask import jsonify
        from app.production.auth.authorization_middleware import require_permission

        @require_permission("org", "admin")
        def admin_endpoint():
            return jsonify({"success": True})

        from flask import g
        from app.auth import TeamMember
        test_admin = TeamMember(name="TestA", email="testa@test.com",
                                role="admin", is_active=True)
        with logged_in_admin.application.test_request_context():
            g.user = test_admin
            result = admin_endpoint()
        status = result[1] if isinstance(result, tuple) else result.status_code
        assert status == 200

    def test_agent_denied_admin_endpoint(self, logged_in_agent):
        from flask import jsonify
        from app.production.auth.authorization_middleware import require_permission

        @require_permission("org", "admin")
        def admin_endpoint():
            return jsonify({"success": True})

        from flask import g
        from app.auth import TeamMember
        test_agent = TeamMember(name="TestAgent", email="testagent@test.com",
                                role="agent", is_active=True)
        with logged_in_agent.application.test_request_context():
            g.user = test_agent
            result = admin_endpoint()
        # Flask views can return (response, status_code) tuples
        status = result[1] if isinstance(result, tuple) else result.status_code
        assert status == 403


class TestGovEvaluator:
    """Governance Engine integration."""

    def test_evaluate_simple_action(self):
        from app.production.auth.authorization_middleware import evaluate_governance
        result = evaluate_governance("read", {"tenant_id": 1})
        assert "approved" in result
        assert "verdict" in result

    def test_evaluate_data_mutation(self):
        from app.production.auth.authorization_middleware import evaluate_governance
        result = evaluate_governance("data_mutation", {
            "tenant_id": 1,
            "resource_type": "workspace",
        })
        assert "approved" in result