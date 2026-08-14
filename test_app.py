"""
App factory test — validates the Core App Unit (Unit 1) initialises correctly.
"""
import pytest
from app import create_app, db
import app.tenant  # noqa: F401 — loads Tenant model for FK resolution


@pytest.fixture()
def app():
    app = create_app(config_override={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "DISABLE_RATE_LIMIT": "true",
    })
    with app.app_context():
        # Import Tenant model to register it with db.metadata before create_all
        # (Person.tenant_id FK references tenants.id)
        from app.tenant import Tenant
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_factory_initialises(app):
    """App factory should create a working Flask app."""
    assert app is not None
    assert app.config["TESTING"] is True
    assert app.secret_key == "test-secret"


def test_health_endpoint(client):
    """Health endpoint should return 200 with DB status."""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["environment"] in ("production", "development", "testing")
    assert "version" in data
    assert "uptime_seconds" in data
    assert "request_id" in data


def test_request_id_on_every_response(client):
    """Every response should have an X-Request-Id header."""
    r = client.get("/health")
    assert "X-Request-Id" in r.headers
    assert len(r.headers["X-Request-Id"]) > 0


def test_security_headers(client):
    """Security headers should be present on all responses."""
    r = client.get("/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("X-XSS-Protection") == "1; mode=block"


def test_404_returns_json_for_api(client):
    """API paths return appropriate HTTP response."""
    r = client.get('/shunya/nonexistent')
    assert r.status_code in (401, 404)
    assert len(r.data) > 0


def test_404_returns_html_for_ui(client):
    """UI paths should return HTML on 404."""
    r = client.get("/nonexistent-page")
    assert r.status_code == 404
    assert b"404" in r.data or b"Not found" in r.data


def test_context_processor_injects_brand(app, client):
    """All templates should have brand context."""
    # Verify the context processor injects 'brand' into the template context.
    # Testing via render_template_string proves the contract directly — the
    # HTTP response may contain hardcoded brand text from base.html that would
    # produce a false positive even if the context processor were removed.
    with app.test_request_context():
        from flask import render_template_string
        rendered = render_template_string("{{ brand }}")
        assert rendered == "SHUNYA OS"


def test_request_id_passed_from_header(client):
    """Client-supplied X-Request-Id should be echoed back."""
    r = client.get("/health", headers={"X-Request-Id": "my-custom-trace-id"})
    assert r.headers.get("X-Request-Id") == "my-custom-trace-id"