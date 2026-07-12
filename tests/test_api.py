"""Tests for Shunya OS API routes — health, admin, entities, import, owner."""
import io
import json
import csv

import pytest
from flask import session

# ---------------------------------------------------------------------------
# Override the conftest app fixture so each test gets an isolated temp SQLite
# database.  The conftest fixture tries to change the URI after init_app(),
# which doesn't actually take effect in Flask-SQLAlchemy 3.x.
# ---------------------------------------------------------------------------

import config as _cfg


@pytest.fixture(scope="function")
def app():
    import tempfile
    import os as _os

    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    _os.close(db_fd)

    # Override the config class *before* create_app so the engine is
    # born pointing at the temp file.
    original_uri = _cfg.TestConfig.SQLALCHEMY_DATABASE_URI
    _cfg.TestConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    from app import create_app, db as _db

    app = create_app("test")

    with app.app_context():
        # UserMoodCheckin is defined twice in models.py, producing a duplicate
        # index (ix_mood_user_date) in the metadata.  Remove one before DDL.
        _tbl = _db.metadata.tables.get("user_mood_checkins")
        if _tbl:
            seen = set()
            for idx in list(_tbl.indexes):
                sig = (idx.name, tuple(c.name for c in idx.columns))
                if sig in seen:
                    _tbl.indexes.discard(idx)
                else:
                    seen.add(sig)
        _db.create_all()

    yield app

    with app.app_context():
        _db.session.close()
        _db.engine.dispose()

    # Remove cached engine so the next test's app doesn't reuse it
    if app in _db.engines:
        del _db.engines[app]

    _os.unlink(db_path)
    _cfg.TestConfig.SQLALCHEMY_DATABASE_URI = original_uri


# ---------------------------------------------------------------------------
# Authenticated client helper
# ---------------------------------------------------------------------------

def _authenticate(client, db, admin_user):
    """Create a real UserSession so login_required succeeds."""
    from app.models import UserSession
    from app.utils import generate_token, hash_token
    from datetime import datetime, timedelta

    token = generate_token(48)
    token_hash = hash_token(token)
    sess = UserSession(
        user_id=admin_user.id,
        token=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.session.add(sess)
    db.session.commit()

    with client.session_transaction() as sess_:
        sess_["session_token"] = token
        sess_["user_id"] = admin_user.id
        sess_["tenant_id"] = admin_user.tenant_id
        sess_["role"] = admin_user.role
        sess_["name"] = admin_user.name

    return client


# ===========================================================================
# Tests
# ===========================================================================


class TestHealth:
    """GET /health — no auth required."""

    def test_health_returns_200_with_keys(self, client, app):
        """/health returns 200 and contains status + database keys."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "status" in data
        assert "database" in data
        assert data["status"] == "ok"
        assert data["database"] == "connected"


class TestAdminBrand:
    """GET/POST /admin/brand and /admin/api/brand."""

    def test_get_admin_brand_returns_200(self, client, db, tenant, admin_user):
        """GET /admin/brand renders the brand page for an admin."""
        _authenticate(client, db, admin_user)
        resp = client.get("/admin/brand")
        assert resp.status_code == 200
        # HTML page — check for expected template content
        assert resp.data

    def test_post_admin_api_brand_updates_company_name(self, client, db, tenant, admin_user):
        """POST /admin/api/brand updates the tenant's brand fields."""
        _authenticate(client, db, admin_user)
        resp = client.post(
            "/admin/api/brand",
            json={"company_name": "Updated Travel Co", "tagline": "Go further"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

        # Verify the tenant was actually updated
        from app.models import Tenant
        t = db.session.get(Tenant, tenant.id)
        assert t.company_name == "Updated Travel Co"
        assert t.brand_tagline == "Go further"


class TestAdminTeam:
    """GET /admin/api/team."""

    def test_list_team_returns_members(self, client, db, tenant, admin_user):
        """GET /admin/api/team returns a JSON list of team members."""
        _authenticate(client, db, admin_user)
        resp = client.get("/admin/api/team")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        # Our admin_user should be in the list
        emails = [m["email"] for m in data]
        assert admin_user.email in emails

    def test_list_team_returns_401_without_auth(self, client):
        """GET /admin/api/team returns 401 when not logged in."""
        resp = client.get("/admin/api/team")
        assert resp.status_code == 401


class TestEntitiesAPI:
    """GET/POST /api/entities/<entity_type> via the api_bp."""

    def test_get_api_entities_lead_returns_empty_list(self, client, db, tenant, admin_user, lead_definition):
        """GET /api/entities/lead returns an empty entities list."""
        _authenticate(client, db, admin_user)
        resp = client.get("/api/entities/lead")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "entities" in data
        assert data["entities"] == []

    def test_get_api_entities_lead_returns_created_lead(self, client, db, tenant, admin_user, lead_definition):
        """GET /api/entities/lead returns entities after one is created."""
        _authenticate(client, db, admin_user)
        # Create a lead via POST first
        resp = client.post(
            "/api/entities/lead",
            json={"name": "Alice", "status": "new"},
        )
        assert resp.status_code == 201

        # Now list
        resp = client.get("/api/entities/lead")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["entities"]) == 1
        assert data["entities"][0]["data"]["name"] == "Alice"

    def test_post_api_entities_lead_creates_entity(self, client, db, tenant, admin_user, lead_definition):
        """POST /api/entities/lead creates a lead and returns 201."""
        _authenticate(client, db, admin_user)
        resp = client.post(
            "/api/entities/lead",
            json={"name": "Bob Builder", "status": "new"},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        entity = data["entity"]
        assert entity["data"]["name"] == "Bob Builder"
        assert entity["status"] == "new"
        assert entity["entity_type"] == "lead"
        assert entity["code"].startswith("PC")

    def test_post_api_entities_unknown_type_returns_404(self, client, db, tenant, admin_user):
        """POST /api/entities/bogus returns 404."""
        _authenticate(client, db, admin_user)
        resp = client.post("/api/entities/bogus", json={"name": "Nope"})
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data


class TestOwner:
    """GET /owner — dashboard_bp route."""

    def test_owner_dashboard_returns_200(self, client, db, tenant, admin_user, business):
        """GET /owner returns the owner dashboard page."""
        _authenticate(client, db, admin_user)
        resp = client.get("/owner")
        assert resp.status_code == 200
        assert resp.data


class TestAdminImport:
    """GET /admin/import and POST /admin/api/import/inspect."""

    def test_get_admin_import_returns_200(self, client, db, tenant, admin_user, lead_definition):
        """GET /admin/import renders the data import page."""
        _authenticate(client, db, admin_user)
        resp = client.get("/admin/import")
        assert resp.status_code == 200
        assert resp.data

    def test_post_import_inspect_with_csv(self, client, db, tenant, admin_user, lead_definition):
        """POST /admin/api/import/inspect with CSV data returns column matches."""
        _authenticate(client, db, admin_user)

        # Build a CSV in-memory
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["name", "email", "budget"])
        writer.writerow(["Alice", "alice@test.com", "50000"])
        writer.writerow(["Bob", "bob@test.com", "75000"])
        csv_buffer.seek(0)

        resp = client.post(
            "/admin/api/import/inspect",
            data={
                "entity_type": "lead",
                "file": (io.BytesIO(csv_buffer.getvalue().encode("utf-8")), "leads.csv"),
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["entity_type"] == "lead"
        assert data["total_rows"] == 2
        # The column "name" should match the schema field "name"
        matched_names = [m["field_name"] for m in data["matched_columns"]]
        assert "name" in matched_names

    def test_post_import_inspect_without_data_returns_400(self, client, db, tenant, admin_user, lead_definition):
        """POST /admin/api/import/inspect with no data returns 400."""
        _authenticate(client, db, admin_user)
        resp = client.post(
            "/admin/api/import/inspect",
            data={"entity_type": "lead"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_post_import_inspect_unknown_entity_returns_400(self, client, db, tenant, admin_user):
        """POST /admin/api/import/inspect with unknown entity type returns 400."""
        _authenticate(client, db, admin_user)
        csv_buffer = io.StringIO()
        csv_buffer.write("name,age\nAlice,30\n")
        csv_buffer.seek(0)
        resp = client.post(
            "/admin/api/import/inspect",
            data={
                "entity_type": "nonexistent",
                "file": (io.BytesIO(csv_buffer.getvalue().encode("utf-8")), "data.csv"),
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400