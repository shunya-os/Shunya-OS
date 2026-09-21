"""§21 — no fake success, no state that misrepresents reality.

`POST /api/v1/integration/social/posts/<id>/publish` used to call
`simulate_platform_post()` (no external call) and then persist
``status="published"`` + ``published_at`` while returning ``{"success": True}``.
A caller got a success response and the database recorded a publication that
never happened.

These tests pin the truthful contract:
  * the endpoint must NOT report success;
  * the row must be UNCHANGED after the attempt (re-read, not assumed);
  * when no connector is configured it must say so rather than imply delivery.
"""
from __future__ import annotations

import pytest

from app import db

ORG_ID = 88001
WS_ID = "ws_publish_probe"


@pytest.fixture
def seeded(app):
    with app.app_context():
        from app.auth import TeamMember
        from app.authz.services import seed_default_roles
        from app.models import OrgMember, Organization
        from app.objects.legacy_models import ShWorkspaceMembership, Workspace

        seed_default_roles(ORG_ID)

        org = Organization(id=ORG_ID, name="Publish Org", slug="publish-org", is_active=True)
        db.session.add(org)
        db.session.flush()

        member = TeamMember(name="Publisher", email="pub@t.com", role="owner", is_active=True)
        member.set_password("testpass")
        member.verified = True
        db.session.add(member)
        db.session.flush()
        identity_id = str(member.id)

        db.session.add(OrgMember(organization_id=ORG_ID, identity_id=identity_id,
                                 name="Publisher", email="pub@t.com", role="owner"))
        db.session.add(Workspace(id=WS_ID, name="Publish WS", workspace_type="business",
                                 status="active", created_by="probe", organization_id=ORG_ID))
        db.session.flush()
        db.session.add(ShWorkspaceMembership(workspace_id=WS_ID, identity_id=identity_id,
                                             role="owner", is_active=True))
        db.session.commit()

        from app.integration.models import ScheduledPost
        post = ScheduledPost(
            platform="twitter",
            content="This must never be recorded as published.",
            status="scheduled",
            identity_id=identity_id,
        )
        db.session.add(post)
        db.session.commit()

        return {"post_id": post.id, "identity_id": identity_id}


def _session_client(app, identity_id):
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["identity_id"] = identity_id
        sess["user_id"] = identity_id
        sess["current_org_id"] = ORG_ID
    return client


def test_publish_does_not_fabricate_success_or_persist_published(app, seeded):
    """The endpoint must not claim success and must not invent a publication."""
    with app.app_context():
        from app.integration.models import ScheduledPost

        before = db.session.get(ScheduledPost, seeded["post_id"])
        assert before.status == "scheduled"
        assert before.published_at is None

        client = _session_client(app, seeded["identity_id"])
        resp = client.post(f"/api/v1/integration/social/posts/{seeded['post_id']}/publish")

        body = resp.get_json() or {}
        # The endpoint must refuse, not fabricate. Verified behaviour: 501.
        assert resp.status_code == 501, f"expected a truthful refusal, got {resp.status_code}: {body}"
        assert body.get("success") is False
        assert "NOT published" in body.get("error", "")
        assert body.get("published") is False
        assert body.get("status") == "scheduled", "response must report the real status"

        # The decisive invariant: the row is untouched. Re-read it, do not assume.
        db.session.expire_all()
        after = db.session.get(ScheduledPost, seeded["post_id"])
        assert after.status == "scheduled", "a refused publish must not mark the post published"
        assert after.published_at is None, "a refused publish must not set published_at"


def test_no_production_route_calls_simulate_platform_post():
    """The simulator must not be CALLED from any reachable production route.

    Checked with AST rather than a text search: the route's own docstring names
    `simulate_platform_post()`, and a substring scan would match that prose.
    Only real Call nodes in executable code count.
    """
    import ast
    import inspect

    from app.integration import routes as integration_routes

    tree = ast.parse(inspect.getsource(integration_routes))
    calls = [
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert "simulate_platform_post" not in calls, (
        "simulate_platform_post is called from a production route again"
    )