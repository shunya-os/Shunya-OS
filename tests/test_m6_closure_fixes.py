"""M6 closure — regression tests for defects found by the browser journey.

1. /api/v1/awareness returned HTTP 200 with an error body on EVERY call:
   `now = now().isoformat()` shadowed the imported `now` function and raised
   UnboundLocalError, caught by the handler's broad except. The endpoint must
   return its real payload (signals list, zero or more), never an `error` key
   caused by that shadowing.
"""

import pytest


@pytest.fixture(scope="function")
def app():
    from app import create_app, db
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
        "DISABLE_RATE_LIMIT": True,
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


def test_awareness_endpoint_has_no_shadowing_error(client):
    resp = client.get("/api/v1/awareness")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "signals" in body and isinstance(body["signals"], list)
    assert "total" in body
    # The old UnboundLocalError surfaced as this exact error string:
    err = body.get("error")
    assert not err or "now" not in err, (
        f"the `now` shadowing bug is back: {err!r}")
    assert "priorities" in body


def test_awareness_signals_have_timestamps_when_present(client):
    """When signals exist, every one carries a timestamp (the line that broke)."""
    resp = client.get("/api/v1/awareness")
    body = resp.get_json()
    for s in body.get("signals", []):
        assert "timestamp" in s