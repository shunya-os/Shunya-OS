"""
FDA23 — People / Internal Operations Tests.

Tests people operations with privacy-aware boundaries.
All data from existing canonical models — no separate employee identity.
"""

import pytest
from datetime import date, timedelta


@pytest.fixture(scope="function")
def app():
    from app import create_app, db
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
        "DISABLE_RATE_LIMIT": True,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def auth_headers(app, client):
    with client.session_transaction() as s:
        s["identity_id"] = "test_manager"
        s["current_org_id"] = 1
        s["user_id"] = "test_manager"
    return {"X-Identity-Id": "test_manager"}


@pytest.fixture(autouse=True)
def reset_fda23_stores():
    """Clear in-memory FDA23 stores between tests to prevent cross-test leakage."""
    from app.people import routes as people_routes
    people_routes._attendance_store.clear()
    people_routes._policy_store.clear()
    people_routes._training_store.clear()
    people_routes._acknowledgement_store.clear()
    people_routes._completion_store.clear()
    people_routes._leave_id_counter = 0
    yield


@pytest.fixture(scope="function")
def seed_org(app):
    """Seed org with members, roles, and sample tasks."""
    from app import db
    from app.models import Organization, OrgMember, Task, TaskList
    from app.authz.models import Role, OrgMemberRole
    from app.authz.services import seed_default_roles

    org = Organization(id=1, name="Test Org", slug="test-org")
    db.session.add(org)
    db.session.flush()
    seed_default_roles(1)

    # Add people.manage to the manager role for FDA23 workstream tests
    manager_role = db.session.query(Role).filter_by(organization_id=1, name="manager").first()
    if manager_role:
        import json
        perms = json.loads(manager_role.permissions or "[]")
        if "people.manage" not in perms:
            perms.append("people.manage")
            manager_role.permissions = json.dumps(perms)
            db.session.flush()

    manager_role = db.session.query(Role).filter_by(organization_id=1, name="manager").first()
    viewer_role = db.session.query(Role).filter_by(organization_id=1, name="viewer").first()

    members = []
    for i, (mid, name, email, role_obj) in enumerate([
        ("test_manager", "Alice Manager", "alice@test.com", manager_role),
        ("worker_1", "Bob Worker", "bob@test.com", viewer_role),
        ("worker_2", "Carol Worker", "carol@test.com", viewer_role),
    ]):
        m = OrgMember(organization_id=1, identity_id=mid, name=name,
                       email=email, role=role_obj.name if role_obj else "viewer",
                       is_active=True)
        db.session.add(m)
        db.session.flush()
        if role_obj:
            db.session.add(OrgMemberRole(
                organization_id=1, member_id=m.id,
                role_id=role_obj.id, scope="organization", granted_by="system"))
        members.append(m)

    # Task list
    tl = TaskList(tenant_id=1, name="Team Tasks", created_by="test_manager")
    db.session.add(tl)
    db.session.flush()

    # Tasks
    db.session.add(Task(task_list_id=tl.id, title="Complete onboarding",
                         assigned_to="test_manager", status="pending",
                         due_date=date.today() - timedelta(days=2)))
    db.session.add(Task(task_list_id=tl.id, title="Review proposal",
                         assigned_to="worker_1", status="in_progress"))
    db.session.add(Task(task_list_id=tl.id, title="Update documentation",
                         assigned_to="worker_2", status="completed"))
    db.session.add(Task(task_list_id=tl.id, title="Client follow-up",
                         assigned_to="worker_1", status="pending",
                         due_date=date.today() + timedelta(days=5)))

    # Commitments
    from app.commitments.models import Commitment
    db.session.add(Commitment(
        title="Approve budget extension", owner="test_manager", status="pending"))
    db.session.add(Commitment(
        title="Review Q3 report", owner="test_manager", status="in_progress"))
    db.session.add(Commitment(
        title="Onboarding completed", owner="worker_1", status="completed"))

    db.session.commit()
    return {"org": org, "members": members, "task_list": tl}


class TestPeopleMembers:
    """FDA23: People member listing and detail."""

    def test_list_members(self, client, auth_headers, seed_org):
        """List members with privacy-safe data."""
        resp = client.get("/api/v1/people/members", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) >= 3
        # Privacy: no phone or address in response
        for m in data["data"]:
            assert "phone" not in m
            assert "address" not in m

    def test_get_member(self, client, auth_headers, seed_org):
        """Get a specific member."""
        member_id = seed_org["members"][0].id
        resp = client.get(f"/api/v1/people/members/{member_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["email"] == "alice@test.com"

    def test_get_member_not_found(self, client, auth_headers, seed_org):
        """Non-existent member returns 404."""
        resp = client.get("/api/v1/people/members/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_members_requires_auth(self, client):
        """Unauthenticated returns 401."""
        resp = client.get("/api/v1/people/members")
        assert resp.status_code == 401


class TestPeopleTasks:
    """FDA23: People task overview."""

    def test_get_tasks(self, client, auth_headers, seed_org):
        """Get tasks grouped by status."""
        resp = client.get("/api/v1/people/tasks", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["total"] >= 4
        assert len(data["data"]["pending"]) >= 1
        assert len(data["data"]["completed"]) >= 1

    def test_tasks_requires_auth(self, client):
        """Unauthenticated returns 401."""
        resp = client.get("/api/v1/people/tasks")
        assert resp.status_code == 401

    def test_tasks_requires_people_permission(self, client, seed_org):
        """Viewer without people permission gets 403."""
        from app import db
        from app.models import OrgMember
        from app.authz.models import OrgMemberRole
        # Create a member with no task.view permission
        org_member = OrgMember(
            organization_id=1, identity_id="no_perm_user",
            email="noperm@test.com", role="none", is_active=True,
        )
        db.session.add(org_member)
        db.session.commit()

        with client.session_transaction() as s:
            s["identity_id"] = "no_perm_user"
            s["current_org_id"] = 1
        resp = client.get("/api/v1/people/tasks", headers={"X-Identity-Id": "no_perm_user"})
        assert resp.status_code in (401, 403)


class TestPeopleApprovals:
    """FDA23: People approval overview."""

    def test_get_approvals(self, client, auth_headers, seed_org):
        """Get pending approvals."""
        resp = client.get("/api/v1/people/approvals", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        # test_manager has 1 pending commitment
        assert len(data["data"]) >= 1

    def test_approvals_requires_auth(self, client):
        """Unauthenticated returns 401."""
        resp = client.get("/api/v1/people/approvals")
        assert resp.status_code == 401


class TestPeopleWorkload:
    """FDA23: Workload overview."""

    def test_get_workload(self, client, auth_headers, seed_org):
        """Get workload overview."""
        resp = client.get("/api/v1/people/workload", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["total_members"] >= 3
        # At least one overdue task exists
        assert data["data"]["total_overdue"] >= 1

    def test_workload_requires_auth(self, client):
        """Unauthenticated returns 401."""
        resp = client.get("/api/v1/people/workload")
        assert resp.status_code == 401

    def test_workload_requires_people_permission(self, client, seed_org):
        """Workload requires people permission."""
        with client.session_transaction() as s:
            s["identity_id"] = "no_perm_user"
            s["current_org_id"] = 1
        resp = client.get("/api/v1/people/workload", headers={"X-Identity-Id": "no_perm_user"})
        assert resp.status_code in (401, 403)


class TestPeopleHealth:
    """FDA23: Health endpoint."""

    def test_health(self, client):
        resp = client.get("/api/v1/people/health")
        assert resp.status_code == 200
        assert resp.get_json()["service"] == "people-operations"


class TestPeopleAttendance:
    """FDA23: Attendance and leave workstream."""

    def test_list_attendance_empty(self, client, auth_headers, seed_org):
        """List attendance returns no records initially."""
        resp = client.get("/api/v1/people/attendance", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["summary"]["total_requests"] == 0

    def test_submit_attendance(self, client, auth_headers, seed_org):
        """Submit a leave request."""
        resp = client.post("/api/v1/people/attendance", headers=auth_headers, json={
            "member_id": "test_manager",
            "type": "leave",
            "date": "2026-08-15",
            "reason": "Personal leave",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "pending"
        assert data["data"]["type"] == "leave"
        assert data["data"]["member_id"] == "test_manager"
        assert data["data"]["id"].startswith("ATT-")

    def test_submit_attendance_missing_fields(self, client, auth_headers, seed_org):
        """Submit without required fields returns 400."""
        resp = client.post("/api/v1/people/attendance", headers=auth_headers, json={
            "member_id": "test_manager",
        })
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

    def test_submit_attendance_invalid_type(self, client, auth_headers, seed_org):
        """Submit with invalid type returns 400."""
        resp = client.post("/api/v1/people/attendance", headers=auth_headers, json={
            "member_id": "test_manager",
            "type": "vacation",
            "date": "2026-08-15",
        })
        assert resp.status_code == 400
        assert "Invalid type" in resp.get_json()["error"]

    def test_attendance_shows_submitted(self, client, auth_headers, seed_org):
        """Submitted record appears in listing."""
        client.post("/api/v1/people/attendance", headers=auth_headers, json={
            "member_id": "worker_1", "type": "sick", "date": "2026-08-10", "reason": "Flu",
        })
        resp = client.get("/api/v1/people/attendance", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["summary"]["total_requests"] == 1
        assert data["data"]["summary"]["pending"] == 1

    def test_attendance_requires_auth(self, client):
        """Unauthenticated returns 401."""
        resp = client.get("/api/v1/people/attendance")
        assert resp.status_code == 401

    def test_attendance_post_requires_auth(self, client):
        """Unauthenticated POST returns 401."""
        resp = client.post("/api/v1/people/attendance", json={"member_id": "x", "type": "leave", "date": "2026-01-01"})
        assert resp.status_code == 401

    def test_attendance_requires_manage_permission(self, client, seed_org):
        """User without people.manage gets 401/403."""
        with client.session_transaction() as s:
            s["identity_id"] = "no_perm_user"
            s["current_org_id"] = 1
        resp = client.get("/api/v1/people/attendance", headers={"X-Identity-Id": "no_perm_user"})
        assert resp.status_code in (401, 403)


class TestPeoplePolicies:
    """FDA23: Policy/SOP acknowledgement workstream."""

    def test_list_policies(self, client, auth_headers, seed_org):
        """List seeded policies."""
        resp = client.get("/api/v1/people/policies", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["total"] == 3
        # No policies acknowledged yet
        assert data["data"]["acknowledged_count"] == 0

    def test_acknowledge_policy(self, client, auth_headers, seed_org):
        """Acknowledge a specific policy."""
        resp = client.post("/api/v1/people/policies/p1/acknowledge", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["acknowledged"] is True
        assert data["data"]["version"] == "1.2"

    def test_acknowledged_policy_reflects_in_listing(self, client, auth_headers, seed_org):
        """After acknowledging a policy, list shows it as acknowledged."""
        client.post("/api/v1/people/policies/p1/acknowledge", headers=auth_headers)
        resp = client.get("/api/v1/people/policies", headers=auth_headers)
        data = resp.get_json()
        assert data["data"]["acknowledged_count"] == 1
        p1 = next(p for p in data["data"]["policies"] if p["id"] == "p1")
        assert p1["acknowledged"] is True
        p2 = next(p for p in data["data"]["policies"] if p["id"] == "p2")
        assert p2["acknowledged"] is False

    def test_acknowledge_nonexistent_policy(self, client, auth_headers, seed_org):
        """Acknowledging a non-existent policy returns 404."""
        resp = client.post("/api/v1/people/policies/nonexistent/acknowledge", headers=auth_headers)
        assert resp.status_code == 404

    def test_policies_requires_auth(self, client):
        """Unauthenticated returns 401."""
        resp = client.get("/api/v1/people/policies")
        assert resp.status_code == 401

    def test_policies_acknowledge_requires_auth(self, client):
        """Unauthenticated policy acknowledge returns 401."""
        resp = client.post("/api/v1/people/policies/p1/acknowledge")
        assert resp.status_code == 401

    def test_policies_requires_manage_permission(self, client, seed_org):
        """User without people.manage gets 401/403."""
        with client.session_transaction() as s:
            s["identity_id"] = "no_perm_user"
            s["current_org_id"] = 1
        resp = client.get("/api/v1/people/policies", headers={"X-Identity-Id": "no_perm_user"})
        assert resp.status_code in (401, 403)


class TestPeopleTraining:
    """FDA23: Training records workstream."""

    def test_list_training(self, client, auth_headers, seed_org):
        """List seeded training records."""
        resp = client.get("/api/v1/people/training", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["total"] == 3
        assert data["data"]["completed_count"] == 0

    def test_complete_training(self, client, auth_headers, seed_org):
        """Mark a training as complete."""
        resp = client.post("/api/v1/people/training/t1/complete", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["completed"] is True
        assert data["data"]["training_id"] == "t1"

    def test_completed_training_reflects_in_listing(self, client, auth_headers, seed_org):
        """After completing training, list shows it as completed."""
        client.post("/api/v1/people/training/t1/complete", headers=auth_headers)
        resp = client.get("/api/v1/people/training", headers=auth_headers)
        data = resp.get_json()
        assert data["data"]["completed_count"] == 1
        t1 = next(t for t in data["data"]["trainings"] if t["id"] == "t1")
        assert t1["completed"] is True
        t2 = next(t for t in data["data"]["trainings"] if t["id"] == "t2")
        assert t2["completed"] is False

    def test_complete_nonexistent_training(self, client, auth_headers, seed_org):
        """Completing a non-existent training returns 404."""
        resp = client.post("/api/v1/people/training/nonexistent/complete", headers=auth_headers)
        assert resp.status_code == 404

    def test_training_requires_auth(self, client):
        """Unauthenticated returns 401."""
        resp = client.get("/api/v1/people/training")
        assert resp.status_code == 401

    def test_training_complete_requires_auth(self, client):
        """Unauthenticated training complete returns 401."""
        resp = client.post("/api/v1/people/training/t1/complete")
        assert resp.status_code == 401

    def test_training_requires_manage_permission(self, client, seed_org):
        """User without people.manage gets 401/403."""
        with client.session_transaction() as s:
            s["identity_id"] = "no_perm_user"
            s["current_org_id"] = 1
        resp = client.get("/api/v1/people/training", headers={"X-Identity-Id": "no_perm_user"})
        assert resp.status_code in (401, 403)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])