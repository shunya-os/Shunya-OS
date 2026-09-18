"""The resident AI surface must call a route that exists.

`frontend/src/components/ui/ai-resident-panel.tsx` — the canonical AI Resident
Panel — was orphaned (mounted nowhere) and posted to
`/api/v1/founder/ai/chat/ambient`, which does not exist anywhere in the backend.
Its failure path ALSO fabricated an assistant reply ("I understand. Let me think
about that."), which is fake AI activity.

The panel now posts to the canonical company-first ask pipeline and reports
truthful failures. This test pins the backend side of that contract: the route
must be mounted and must be authorization-gated.
"""
import pytest


@pytest.fixture(scope="module")
def app():
    from app import create_app, db
    _app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    with _app.app_context():
        db.create_all()
    return _app


@pytest.fixture
def client(app):
    return app.test_client()


def test_ask_route_is_mounted(app):
    rules = {(str(r.rule), m) for r in app.url_map.iter_rules()
             for m in (r.methods or ())}
    assert ("/api/v1/intelligence/ask", "POST") in rules


def test_ask_route_requires_authentication(client):
    """An anonymous caller gets 401 — the route exists AND is gated."""
    resp = client.post("/api/v1/intelligence/ask", json={"question": "What needs attention?"})
    assert resp.status_code == 401, resp.get_data(as_text=True)[:200]
    body = resp.get_json()
    assert body["success"] is False


def test_orphaned_ambient_route_does_not_exist(app):
    """Guards against re-introducing the route the panel used to call."""
    rules = {str(r.rule) for r in app.url_map.iter_rules()}
    assert "/api/v1/founder/ai/chat/ambient" not in rules
