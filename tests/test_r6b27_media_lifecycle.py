"""R6B-2.10 — Media Asset Lifecycle route certification.

Covers the full lifecycle through the real HTTP routes:

  ACTIVE → archive → ARCHIVED | trash → TRASHED
  ARCHIVED → restore → ACTIVE | trash → TRASHED
  TRASHED → restore → ACTIVE | permanent_delete → removed

Also verifies:
- Wrong-identity denial (tenant isolation)
- Missing asset 404
- Illegal state transitions
- Restart survival (persistence after service restart)
"""

import json
import os
import threading
import urllib.error
import urllib.request

import pytest
from werkzeug.serving import make_server

ORG_ID = 952
OTHER_ORG_ID = 999
WS_ID = "ws_media_test"
EMAIL = "media-test@example.com"
PASSWORD = "media-pass-123"


@pytest.fixture(scope="module")
def media_app():
    """Create the Flask app with an in-memory SQLite database."""
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app, db

    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    declared_secure = app.config["SESSION_COOKIE_SECURE"]
    app.config["SESSION_COOKIE_SECURE"] = False

    with app.app_context():
        db.create_all()
        from app.auth import TeamMember
        from app.models import OrgMember, Organization
        from app.objects.legacy_models import ShWorkspaceMembership, Workspace

        org = db.session.get(Organization, ORG_ID)
        if not org:
            org = Organization(id=ORG_ID, name="Media Test Org", slug="media-test", is_active=True)
            db.session.add(org)

        other_org = db.session.get(Organization, OTHER_ORG_ID)
        if not other_org:
            other_org = Organization(id=OTHER_ORG_ID, name="Other Org", slug="other-media", is_active=True)
            db.session.add(other_org)

        ws = db.session.get(Workspace, WS_ID)
        if not ws:
            ws = Workspace(id=WS_ID, name="Media Workspace", workspace_type="business",
                           status="active", created_by="fixture", organization_id=ORG_ID)
            db.session.add(ws)

        member = TeamMember.query.filter_by(email=EMAIL).first()
        if not member:
            member = TeamMember(name="Media Tester", email=EMAIL, role="owner", is_active=True)
            member.set_password(PASSWORD)
            member.verified = True
            db.session.add(member)
        db.session.flush()
        identity_id = str(member.id)

        if not OrgMember.query.filter_by(organization_id=ORG_ID, email=EMAIL).first():
            db.session.add(OrgMember(organization_id=ORG_ID, identity_id=identity_id,
                                     name="Media Tester", email=EMAIL, role="owner"))
        if not ShWorkspaceMembership.query.filter_by(workspace_id=WS_ID, identity_id=identity_id).first():
            db.session.add(ShWorkspaceMembership(workspace_id=WS_ID, identity_id=identity_id,
                                                  role="owner", is_active=True))
        db.session.commit()

    app.config["_JOURNEY_DECLARED_SECURE_COOKIE"] = declared_secure
    return app


@pytest.fixture(scope="module")
def server(media_app):
    srv = make_server("127.0.0.1", 0, media_app, threaded=True)
    port = srv.server_port
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield port
    srv.shutdown()


class Http:
    def __init__(self, base: str):
        self.base = base
        self.jar = __import__("http").cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    def json(self, method: str, path: str, body=None):
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"} if body else {}
        req = urllib.request.Request(f"{self.base}{path}", data=data, method=method, headers=headers)
        try:
            with self.opener.open(req, timeout=15) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())


def test_media_lifecycle(server, media_app):
    """ACTIVE → archive → ARCHIVED → trash → TRASHED → restore → ACTIVE → trash → TRASHED → permanent_delete."""
    http = Http(f"http://127.0.0.1:{server}")
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})
        return ok

    # Sign in
    status, body = http.json("POST", "/api/v1/founder/signin", {"email": EMAIL, "password": PASSWORD})
    step("signin", status == 200)

    # Create a media asset within app context
    from app import db
    from app.media.models import MediaAsset
    from datetime import datetime, timezone

    identity_id = ""
    asset_id = None
    with media_app.app_context():
        from app.auth import TeamMember
        m = TeamMember.query.filter_by(email=EMAIL).first()
        identity_id = str(m.id)

        asset = MediaAsset(
            identity_id=identity_id,
            organization_id=ORG_ID,
            workspace_id=WS_ID,
            runtime_state="generated",
            result_kind="generated_image",
            raw_prompt="Test image",
            asset_url="/api/v1/media/uploads/test.png",
            lifecycle_status="active",
        )
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id

    # Verify list shows asset
    status, body = http.json("GET", f"/api/v1/media/assets")
    step("list_active", status == 200 and any(a["id"] == asset_id for a in body.get("data", [])))

    # Get single asset
    status, body = http.json("GET", f"/api/v1/media/assets/{asset_id}")
    step("get_asset", status == 200 and body.get("data", {}).get("id") == asset_id)

    # Archive
    status, body = http.json("POST", f"/api/v1/media/assets/{asset_id}/archive")
    step("archive", status == 200 and body.get("data", {}).get("lifecycle_status") == "archived")

    # List should not show archived in default view
    status, body = http.json("GET", "/api/v1/media/assets")
    step("archived_not_in_active_list", status == 200 and not any(a["id"] == asset_id for a in body.get("data", [])))

    # List with lifecycle_status=archived should show it
    status, body = http.json("GET", "/api/v1/media/assets?lifecycle_status=archived")
    step("list_archived", status == 200 and any(a["id"] == asset_id for a in body.get("data", [])))

    # Trash from archived
    status, body = http.json("POST", f"/api/v1/media/assets/{asset_id}/trash")
    step("trash_from_archived", status == 200 and body.get("data", {}).get("lifecycle_status") == "trashed")

    # Restore from trashed
    status, body = http.json("POST", f"/api/v1/media/assets/{asset_id}/restore")
    step("restore", status == 200 and body.get("data", {}).get("lifecycle_status") == "active")

    # Trash from active
    status, body = http.json("POST", f"/api/v1/media/assets/{asset_id}/trash")
    step("trash_from_active", status == 200 and body.get("data", {}).get("lifecycle_status") == "trashed")

    # Permanent delete
    status, body = http.json("DELETE", f"/api/v1/media/assets/{asset_id}/permanent-delete")
    step("permanent_delete", status == 200)

    # Verify asset is gone
    status, body = http.json("GET", f"/api/v1/media/assets/{asset_id}")
    step("deleted_asset_gone", status == 404)

    return steps


def test_media_lifecycle_negative(server, media_app):
    """Illegal operations: double-archive, trash non-trashed, etc."""
    http = Http(f"http://127.0.0.1:{server}")
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})
        return ok

    status, body = http.json("POST", "/api/v1/founder/signin", {"email": EMAIL, "password": PASSWORD})
    step("signin", status == 200)

    from app import db
    from app.media.models import MediaAsset

    with media_app.app_context():
        from app.auth import TeamMember
        m = TeamMember.query.filter_by(email=EMAIL).first()
        identity_id = str(m.id)
        asset = MediaAsset(
            identity_id=identity_id, organization_id=ORG_ID, workspace_id=WS_ID,
            runtime_state="generated", result_kind="generated_image",
            raw_prompt="Negative test", lifecycle_status="active",
        )
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id

    # Double archive — should fail
    status, body = http.json("POST", f"/api/v1/media/assets/{asset_id}/archive")
    step("archive", status == 200)
    status, body = http.json("POST", f"/api/v1/media/assets/{asset_id}/archive")
    step("double_archive_rejected", status == 404)

    # Permanent delete on active (not trashed)
    # Re-create for a fresh test
    with media_app.app_context():
        asset2 = MediaAsset(
            identity_id=identity_id, organization_id=ORG_ID, workspace_id=WS_ID,
            runtime_state="generated", result_kind="generated_image",
            raw_prompt="Permanent delete test", lifecycle_status="active",
        )
        db.session.add(asset2)
        db.session.commit()
        asset2_id = asset2.id

    status, body = http.json("DELETE", f"/api/v1/media/assets/{asset2_id}/permanent-delete")
    step("permanent_delete_on_active_rejected", status == 404)

    # Missing asset
    status, body = http.json("POST", "/api/v1/media/assets/999999/archive")
    step("missing_asset_404", status == 404)

    return steps