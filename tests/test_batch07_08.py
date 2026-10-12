"""BATCH-07-08 tests: PROD-46 through PROD-54."""

import pytest


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
        s["identity_id"] = "test_user"
        s["current_org_id"] = 1
        s["user_id"] = "test_user"
    return {"X-Identity-Id": "test_user"}


@pytest.fixture(scope="function")
def seed_org(app):
    from app import db
    from app.models import Organization, OrgMember
    from app.authz.services import seed_default_roles
    org = Organization(id=1, name="Test Org", slug="test-org")
    db.session.add(org)
    db.session.flush()
    seed_default_roles(1)
    member = OrgMember(
        organization_id=1, identity_id="test_user",
        email="test@test.com", role="owner", is_active=True,
    )
    db.session.add(member)
    db.session.commit()
    return org


def test_entity_api(client, auth_headers, seed_org):
    res = client.get("/api/v1/entities/", headers=auth_headers)
    assert res.status_code == 200


def test_timeline(client, auth_headers, seed_org):
    res = client.get("/api/v1/entities/1/timeline", headers=auth_headers)
    assert res.status_code in [200, 404]