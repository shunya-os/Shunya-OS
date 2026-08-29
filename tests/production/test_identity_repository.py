"""
Tests for IdentityRepository (kernel bridge) and identity API endpoints.
"""
import os
import tempfile
import pytest


@pytest.fixture(scope="function")
def app():
    """Override conftest's app — use temp SQLite file instead of :memory:.

    SQLite :memory: creates a new database per connection. Flask's
    test client opens a new connection per request, so data written
    in one request is invisible in the next. A file-based SQLite
    avoids this isolation issue.
    """
    from app import create_app

    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    application = create_app(config_override={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SECRET_KEY": "test-secret",
        "DISABLE_RATE_LIMIT": "true",
        "WTF_CSRF_ENABLED": False,
    })
    with application.app_context():
        from app import models  # noqa: F401
        from app.tenant import Tenant  # noqa: F401
        from app.communication import models as _comm_models  # noqa: F401
        from app.privacy import models as _privacy_models  # noqa: F401
        from app.human_context import models as _hc_models  # noqa: F401
        from app.memory import models as _mem_models  # noqa: F401
        from app.evidence import models as _ev_models  # noqa: F401
        from app.execution import models as _exec_models  # noqa: F401
        from app.marketing import models as _mkt_models  # noqa: F401
        from app.document import models as _doc_models  # noqa: F401
        from app.llm import models as _llm_models  # noqa: F401
        from app.auth import TeamMember  # noqa: F401
        from app.production.identity.workspace_model import Workspace  # noqa: F401
        from app.production.identity_repository import SHUNYAIdentityModel  # noqa: F401
        from app.founder.workspace_models import (  # noqa: F401
            MissingContext,
        )
        from app import db
        db.create_all()
        yield application
        db_path_keep = db_path
    # Cleanup
    try:
        os.remove(db_path_keep)
    except OSError:
        pass


@pytest.fixture(scope="function")
def _db(app):
    from app import db
    with app.app_context():
        yield db


@pytest.fixture(scope="function")
def admin_user(app, _db):
    from app.auth import TeamMember
    user = TeamMember(
        name="Identity Test", email="idtest@test.com",
        role="admin", is_active=True,
    )
    user.set_password("pass123456")
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture(scope="function")
def logged_in_client(app, client, admin_user):
    with client.session_transaction() as session:
        session["user_id"] = admin_user.id
        session["identity_id"] = "sid_test123"
        session["_fresh"] = True
    return client


class TestIdentityRepository:
    """IdentityRepository — kernel persistence bridge."""

    def test_create_identity(self, _db):
        from app.production.identity_repository import IdentityRepository
        repo = IdentityRepository()
        identity = repo.create("Alice", "alice@test.com")
        assert identity.identity_id.startswith("sid_")
        assert identity.display_name == "Alice"

        # Verify persisted in DB
        from app.production.identity_repository import SHUNYAIdentityModel
        model = SHUNYAIdentityModel.query.filter_by(
            identity_id=identity.identity_id
        ).first()
        assert model is not None
        assert model.display_name == "Alice"

    def test_find_by_auth(self, _db):
        from app.production.identity_repository import IdentityRepository
        repo = IdentityRepository()
        identity = repo.create("Bob", "bob@test.com")
        repo.add_auth_method(identity.identity_id, "email", "bob@test.com", is_primary=True)

        found = repo.find_by_auth("email", "bob@test.com")
        assert found is not None
        assert found.display_name == "Bob"

    def test_add_auth_method(self, _db):
        from app.production.identity_repository import IdentityRepository
        repo = IdentityRepository()
        identity = repo.create("Charlie")
        result = repo.add_auth_method(identity.identity_id, "email", "c@test.com")
        assert result is True

        methods = repo.get_auth_methods(identity.identity_id)
        assert len(methods) == 1
        assert methods[0]["type"] == "email"

    def test_verify_auth_method(self, _db):
        from app.production.identity_repository import IdentityRepository
        repo = IdentityRepository()
        identity = repo.create("Diana")
        repo.add_auth_method(identity.identity_id, "email", "d@test.com")
        result = repo.verify_auth_method(identity.identity_id, "email", "d@test.com")
        assert result is True

        methods = repo.get_auth_methods(identity.identity_id)
        assert methods[0]["verified"] is True

    def test_remove_auth_method(self, _db):
        from app.production.identity_repository import IdentityRepository
        repo = IdentityRepository()
        identity = repo.create("Eve")
        repo.add_auth_method(identity.identity_id, "email", "e@test.com", is_primary=True)
        repo.add_auth_method(identity.identity_id, "gmail", "e@gmail.com")

        result = repo.remove_auth_method(identity.identity_id, "gmail", "e@gmail.com")
        assert result is True

        methods = repo.get_auth_methods(identity.identity_id)
        assert len(methods) == 1

    def test_get_profile(self, _db):
        from app.production.identity_repository import IdentityRepository
        repo = IdentityRepository()
        identity = repo.create("Frank", "f@test.com")
        repo.add_auth_method(identity.identity_id, "email", "f@test.com", is_primary=True)

        profile = repo.get_profile(identity.identity_id)
        assert profile is not None
        assert profile["display_name"] == "Frank"
        assert profile["identity_id"] == identity.identity_id
        assert len(profile["auth_methods"]) == 1


class TestIdentityAPI:
    """Identity API endpoints — profile, auth methods, linking.

    Uses the same app context for setup and requests to avoid
    SQLite cross-connection isolation issues. Prepares data via
    IdentityRepository directly (not HTTP), then sets the session
    cookie via the test client.
    """

    def _setup(self, app, client, name="API Test", email="api@test.com"):
        """Create identity + TeamMember within app_context, then set session."""
        from app import db
        from app.auth import TeamMember
        from app.production.identity_repository import IdentityRepository

        with app.app_context():
            # Create TeamMember for login_required decorator
            tm = TeamMember(
                name=name, email=email,
                role="admin", is_active=True,
            )
            tm.set_password("secure123")
            db.session.add(tm)
            db.session.commit()
            tm_id = tm.id

            # Create identity via repository directly
            repo = IdentityRepository()
            identity = repo.create(display_name=name, primary_email=email)
            repo.add_auth_method(identity.identity_id, "email", email, is_primary=True)
            iid = identity.identity_id

        # Set session via test client — include current_org_id to prevent
        # _resolve_identity_session middleware from overwriting identity_id
        with client.session_transaction() as s:
            s["user_id"] = tm_id
            s["identity_id"] = iid
            s["current_org_id"] = -1  # sentinel — stops middleware override

        return iid

    def test_identity_create_via_api(self, app, client, _db):
        resp = client.post("/api/v1/identity/create", json={
            "name": "Grace",
            "email": "grace@test.com",
            "password": "secure123",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["identity_id"].startswith("sid_")
        assert data["name"] == "Grace"

        from app.production.identity_repository import IdentityRepository
        repo = IdentityRepository()
        found = repo.find_by_auth("email", "grace@test.com")
        assert found is not None
        assert found.display_name == "Grace"

    def test_identity_profile(self, app, client, _db):
        self._setup(app, client, "Profile Test", "profile@test.com")
        resp = client.get("/api/v1/identity/profile")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_list_auth_methods(self, app, client, _db):
        self._setup(app, client, "Auth Test", "auth@test.com")
        resp = client.get("/api/v1/identity/auth-methods")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_link_auth_method(self, app, client, _db):
        self._setup(app, client, "Link Test", "link@test.com")
        resp = client.post("/api/v1/identity/auth-methods/link", json={
            "method_type": "gmail",
            "identifier": "link@gmail.com",
            "verification_token": "test-token",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["verified"] is True

    def test_unlink_auth_method(self, app, client, _db):
        self._setup(app, client, "Unlink Test", "unlink@test.com")
        # First link a second method
        client.post("/api/v1/identity/auth-methods/link", json={
            "method_type": "gmail",
            "identifier": "unlink@gmail.com",
        })
        resp = client.post("/api/v1/identity/auth-methods/unlink", json={
            "method_type": "gmail",
            "identifier": "unlink@gmail.com",
        })
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_cannot_unlink_last_email(self, app, client, _db):
        self._setup(app, client, "Last Email", "last@test.com")
        resp = client.post("/api/v1/identity/auth-methods/unlink", json={
            "method_type": "email",
            "identifier": "last@test.com",
        })
        assert resp.status_code == 400  # Cannot remove last email method