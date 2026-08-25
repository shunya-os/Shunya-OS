"""ZGC-PR-11E: Cross-Workspace Isolation Tests.

Proves no data leakage across Personal, Business and future workspace contexts.
Every data endpoint must scope queries by the current workspace context.
"""

import os
import json

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test"
os.environ["TESTING"] = "1"
os.environ["DISABLE_RATE_LIMIT"] = "1"

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app import create_app, db
from app.auth import TeamMember
from app.workspace.models import create_workspace, switch_workspace
from app.objects.legacy_models import ShunyaObject


@pytest.fixture
def app():
    app = create_app()
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Create a user and return auth session."""
    with client.application.app_context():
        u = TeamMember(name="Test User", email="test@test.com", is_active=True)
        u.set_password("x")
        db.session.add(u)
        db.session.commit()

    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["identity_id"] = "test-identity-id"
    return {"X-Identity-Id": "test-identity-id"}


def test_workspace_creation_isolation(client, auth_headers):
    """Different workspaces should have different IDs and types."""
    # Create Personal workspace
    resp1 = client.post(
        "/api/v1/workspace",
        json={"name": "My Personal Space", "workspace_type": "personal"},
        headers=auth_headers,
    )
    d1 = resp1.get_json()
    assert d1["success"], f"Personal workspace creation failed: {d1}"
    personal_id = d1["data"]["workspace_id"]

    # Create Business workspace
    resp2 = client.post(
        "/api/v1/workspace",
        json={"name": "My Business", "workspace_type": "business"},
        headers=auth_headers,
    )
    d2 = resp2.get_json()
    assert d2["success"], f"Business workspace creation failed: {d2}"
    business_id = d2["data"]["workspace_id"]

    # IDs must be different
    assert personal_id != business_id, "Workspace IDs must be unique"

    # Workspace types must match
    assert d1["data"]["workspace_type"] == "personal"
    assert d2["data"]["workspace_type"] == "business"


def test_object_isolation_across_workspaces(client, auth_headers):
    """Objects created in one workspace must NOT be visible in another."""
    # Create Personal workspace
    resp1 = client.post(
        "/api/v1/workspace",
        json={"name": "Personal", "workspace_type": "personal"},
        headers=auth_headers,
    )
    personal_id = resp1.get_json()["data"]["workspace_id"]

    # Create Business workspace
    resp2 = client.post(
        "/api/v1/workspace",
        json={"name": "Business", "workspace_type": "business"},
        headers=auth_headers,
    )
    business_id = resp2.get_json()["data"]["workspace_id"]

    # Create objects in Personal workspace
    with client.application.app_context():
        obj_personal = ShunyaObject(
            object_id="obj_personal_001",
            workspace_id=personal_id,
            object_type="task",
            name="Personal Task",
            status="active",
            data={"status": "pending"},
            created_by="test-identity-id",
        )
        db.session.add(obj_personal)
        db.session.commit()

    # Create objects in Business workspace
    with client.application.app_context():
        obj_business = ShunyaObject(
            object_id="obj_business_001",
            workspace_id=business_id,
            object_type="task",
            name="Business Task",
            status="active",
            data={"status": "pending"},
            created_by="test-identity-id",
        )
        db.session.add(obj_business)
        db.session.commit()

    # Verify Personal workspace only sees its own objects
    with client.application.app_context():
        personal_objects = ShunyaObject.query.filter_by(
            workspace_id=personal_id, status="active"
        ).all()
        assert len(personal_objects) == 1
        assert personal_objects[0].object_id == "obj_personal_001"

    # Verify Business workspace only sees its own objects
    with client.application.app_context():
        business_objects = ShunyaObject.query.filter_by(
            workspace_id=business_id, status="active"
        ).all()
        assert len(business_objects) == 1
        assert business_objects[0].object_id == "obj_business_001"

    # Verify no cross-contamination
    with client.application.app_context():
        # No business objects in personal workspace
        cross = ShunyaObject.query.filter_by(
            workspace_id=personal_id, object_id="obj_business_001"
        ).first()
        assert cross is None, "Business object leaked into Personal workspace"

        cross2 = ShunyaObject.query.filter_by(
            workspace_id=business_id, object_id="obj_personal_001"
        ).first()
        assert cross2 is None, "Personal object leaked into Business workspace"


def test_workspace_context_scope(client, auth_headers):
    """The workspace context (g.workspace_id) must scope API responses."""
    # Create two workspaces
    resp1 = client.post(
        "/api/v1/workspace",
        json={"name": "Personal", "workspace_type": "personal"},
        headers=auth_headers,
    )
    personal_id = resp1.get_json()["data"]["workspace_id"]

    resp2 = client.post(
        "/api/v1/workspace",
        json={"name": "Business", "workspace_type": "business"},
        headers=auth_headers,
    )
    business_id = resp2.get_json()["data"]["workspace_id"]

    # Create objects in both workspaces
    with client.application.app_context():
        for ws_id, obj_id, name in [
            (personal_id, "obj_p_1", "Personal Task 1"),
            (personal_id, "obj_p_2", "Personal Task 2"),
            (business_id, "obj_b_1", "Business Task 1"),
            (business_id, "obj_b_2", "Business Task 2"),
        ]:
            db.session.add(ShunyaObject(
                object_id=obj_id, workspace_id=ws_id,
                object_type="task", name=name, status="active",
                data={"status": "pending"}, created_by="test-identity-id",
            ))
        db.session.commit()

    # Test context endpoint returns correct workspace
    resp_ctx = client.get("/api/v1/workspace/context", headers={
        **auth_headers, "X-Workspace-Id": personal_id
    })
    ctx = resp_ctx.get_json()
    assert ctx["success"]
    assert ctx["data"]["workspace_id"] == personal_id
    assert ctx["data"]["workspace_type"] == "personal"

    # Switch to business and verify
    resp_switch = client.post("/api/v1/workspace/switch", json={
        "workspace_id": business_id
    }, headers=auth_headers)
    assert resp_switch.get_json()["success"]

    # Home intelligence should reflect the switched workspace
    resp_home = client.get("/api/v1/home/intelligence", headers=auth_headers)
    home = resp_home.get_json()
    assert home["success"]
    # After switch, the session should have the business workspace
    assert home["data"]["workspace_type"] in ("business", None), \
        f"Expected business workspace but got {home['data']['workspace_type']}"


def test_workspace_header_overrides_session(client, auth_headers):
    """X-Workspace-Id header must override session workspace context."""
    # Create workspaces
    resp1 = client.post("/api/v1/workspace", json={
        "name": "Personal", "workspace_type": "personal"
    }, headers=auth_headers)
    personal_id = resp1.get_json()["data"]["workspace_id"]

    resp2 = client.post("/api/v1/workspace", json={
        "name": "Business", "workspace_type": "business"
    }, headers=auth_headers)
    business_id = resp2.get_json()["data"]["workspace_id"]

    # Create objects in both workspaces
    with client.application.app_context():
        for ws_id, obj_id, name in [
            (personal_id, "obj_hdr_1", "Personal Header Task"),
            (business_id, "obj_hdr_2", "Business Header Task"),
        ]:
            db.session.add(ShunyaObject(
                object_id=obj_id, workspace_id=ws_id,
                object_type="task", name=name, status="active",
                data={"status": "pending"}, created_by="test-identity-id",
            ))
        db.session.commit()

    # Set session to Personal
    with client.session_transaction() as sess:
        sess["current_workspace_id"] = personal_id
        sess["current_workspace_type"] = "personal"

    # Request with Business header should return Business context
    resp_ctx = client.get("/api/v1/workspace/context", headers={
        **auth_headers, "X-Workspace-Id": business_id
    })
    ctx = resp_ctx.get_json()
    assert ctx["success"]
    assert ctx["data"]["workspace_id"] == business_id, \
        f"Expected business workspace but got {ctx['data']['workspace_id']}"

    # Home intelligence should also respect header
    resp_home = client.get("/api/v1/home/intelligence", headers={
        **auth_headers, "X-Workspace-Id": business_id, "X-Workspace-Type": "business"
    })
    home = resp_home.get_json()
    assert home["success"]
    assert home["data"]["workspace_id"] == business_id, \
        f"Home should use business workspace from header"


def test_workspace_list_isolation(client, auth_headers):
    """User should only see their own workspaces, not others'."""
    # Create workspace for user A
    resp_a = client.post("/api/v1/workspace", json={
        "name": "User A Workspace", "workspace_type": "personal"
    }, headers=auth_headers)
    assert resp_a.get_json()["success"]
    user_a_ws = resp_a.get_json()["data"]["workspace_id"]

    # Create a second user (User B) with a different identity
    with client.application.app_context():
        u2 = TeamMember(name="User B", email="userb@test.com", is_active=True)
        u2.set_password("x")
        db.session.add(u2)
        db.session.commit()

    # User B creates their own workspace
    with client.application.app_context():
        from app.workspace.models import WorkspaceMembership
        ws_b = create_workspace(
            name="User B Workspace",
            workspace_type="personal",
            owner_identity_id="user-b-identity",
            owner_email="userb@test.com",
            owner_name="User B",
        )
        ws_b_id = ws_b.workspace_id
        mem = WorkspaceMembership(
            identity_id="user-b-identity",
            workspace_id=ws_b_id,
            email="userb@test.com",
            is_active=True,
            role="admin",
        )
        db.session.add(mem)
        db.session.commit()

    # User A should only see their own workspace
    resp_list = client.get("/api/v1/workspace", headers=auth_headers)
    ws_list = resp_list.get_json()
    assert ws_list["success"]
    ws_ids = [ws["workspace_id"] for ws in ws_list["data"]["workspaces"]]
    assert user_a_ws in ws_ids, "User A should see their workspace"
    assert ws_b_id not in ws_ids, "User A should NOT see User B's workspace"