"""
App factory test — validates the Core App Unit (Unit 1) initialises correctly.
"""
import pytest
from app import create_app, db


@pytest.fixture()
def app():
    app = create_app(config_override={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "DISABLE_RATE_LIMIT": "true",
    })
    with app.app_context():
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
    assert "tables" in data


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
    """API paths should return JSON on 404."""
    r = client.get("/shunya/nonexistent")
    assert r.status_code == 404
    data = r.get_json()
    assert "error" in data
    assert "request_id" in data


def test_404_returns_html_for_ui(client):
    """UI paths should return HTML on 404."""
    r = client.get("/nonexistent-page")
    assert r.status_code == 404
    assert b"404" in r.data or b"Not found" in r.data


def test_context_processor_injects_brand(client):
    """All templates should have AI@panchi.club in the context."""
    r = client.get("/")
    body = r.data.decode("utf-8", "ignore")
    assert "AI@panchi.club" in body or "Panchi Club" in body


def test_request_id_passed_from_header(client):
    """Client-supplied X-Request-Id should be echoed back."""
    r = client.get("/health", headers={"X-Request-Id": "my-custom-trace-id"})
    assert r.headers.get("X-Request-Id") == "my-custom-trace-id"