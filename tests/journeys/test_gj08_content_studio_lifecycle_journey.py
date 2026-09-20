"""GJ-08 — Content Studio Lifecycle journey, driven over real HTTP.

Demonstrates: GENERATE → VERIFY ACTIVE → ARCHIVE → TRASH → RESTORE
→ PERMANENT DELETE with full tenant isolation and restart survival.

Uses the same Http/Server harness pattern as other journey tests.
"""
import http.cookiejar
import json
import os
import tempfile
import threading
import urllib.error
import urllib.request

import pytest
from werkzeug.serving import make_server

ORG_ID = 953
WS_ID = "ws_cs_lifecycle"
EMAIL = "cs-lifecycle-journey@example.com"
PASSWORD = "cs-lifecycle-pass"

SHELL_MARKER = "SHUNYA_CS_LIFECYCLE_SHELL"
SHELL_HTML = (
    "<!doctype html><html><head><title>SHUNYA</title></head>"
    f"<body>{SHELL_MARKER}<script crossorigin src=\"/assets/journey.js\"></script></body></html>"
)

MOCK_CONTENT_RESPONSE = {
    "success": True,
    "content": "This is mock generated content for the Content Studio lifecycle journey.",
    "error": None,
    "model": "groq",
    "provider": "groq",
}


@pytest.fixture(scope="module")
def release_shell_dir(tmp_path_factory):
    dist = tmp_path_factory.mktemp("cs_lifecycle_release")
    (dist / "index.html").write_text(SHELL_HTML, encoding="utf-8")
    return dist


@pytest.fixture(autouse=True)
def _point_frontend_at_release(release_shell_dir, monkeypatch):
    monkeypatch.setenv("SHUNYA_FRONTEND_DIST", str(release_shell_dir))


class Http:
    def __init__(self, base: str):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.identity_id = ""
        self.workspace_id = WS_ID
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    def call(self, method: str, path: str, body=None, headers=None):
        data = json.dumps(body).encode() if body is not None else None
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        req = urllib.request.Request(
            f"{self.base}{path}", data=data, method=method,
            headers=req_headers,
        )
        try:
            with self.opener.open(req, timeout=30) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()

    def json(self, method: str, path: str, body=None, headers=None):
        status, text = self.call(method, path, body, headers=headers)
        try:
            return status, json.loads(text)
        except json.JSONDecodeError:
            return status, {"_raw": text[:400]}


class Server:
    def __init__(self, app):
        self._server = make_server("127.0.0.1", 0, app, threaded=True)
        self.port = self._server.server_port
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._server.shutdown()


@pytest.fixture(scope="module")
def journey_app(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("cs_lifecycle_db") / "journey.db"
    from app import create_app, db

    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
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
            org = Organization(id=ORG_ID, name="CS Lifecycle Org",
                               slug="cs-lifecycle", is_active=True)
            db.session.add(org)
            db.session.flush()

        ws = db.session.get(Workspace, WS_ID)
        if not ws:
            ws = Workspace(id=WS_ID, name="CS Lifecycle Workspace",
                           workspace_type="business", status="active",
                           created_by="journey_fixture", organization_id=ORG_ID)
            db.session.add(ws)
            db.session.flush()

        member = TeamMember.query.filter_by(email=EMAIL).first()
        if not member:
            member = TeamMember(name="CS Lifecycle Founder", email=EMAIL,
                                role="owner", is_active=True)
            member.set_password(PASSWORD)
            member.verified = True
            db.session.add(member)
            db.session.flush()

        identity_id = str(member.id)

        if not OrgMember.query.filter_by(organization_id=ORG_ID,
                                         email=EMAIL).first():
            db.session.add(OrgMember(organization_id=ORG_ID,
                                     identity_id=identity_id,
                                     name="CS Lifecycle Founder", email=EMAIL,
                                     role="owner"))
        if not ShWorkspaceMembership.query.filter_by(workspace_id=WS_ID,
                                                     identity_id=identity_id).first():
            db.session.add(ShWorkspaceMembership(workspace_id=WS_ID,
                                                 identity_id=identity_id,
                                                 role="owner", is_active=True))
        db.session.commit()

    app.config["_JOURNEY_DECLARED_SECURE_COOKIE"] = declared_secure

    # Provision a second user for tenant isolation test
    with app.app_context():
        OTHER_EMAIL = "other-cs-lifecycle@example.com"
        OTHER_PASSWORD = "other-cs-lifecycle-pass"
        other_member = TeamMember.query.filter_by(email=OTHER_EMAIL).first()
        if not other_member:
            other_member = TeamMember(name="Other CS User", email=OTHER_EMAIL,
                                      role="member", is_active=True)
            other_member.set_password(OTHER_PASSWORD)
            other_member.verified = True
            db.session.add(other_member)
            db.session.flush()
        other_identity_id = str(other_member.id)

        if not OrgMember.query.filter_by(organization_id=ORG_ID,
                                         email=OTHER_EMAIL).first():
            db.session.add(OrgMember(organization_id=ORG_ID,
                                     identity_id=other_identity_id,
                                     name="Other CS User",
                                     email=OTHER_EMAIL,
                                     role="member"))
        if not ShWorkspaceMembership.query.filter_by(workspace_id=WS_ID,
                                                     identity_id=other_identity_id).first():
            db.session.add(ShWorkspaceMembership(workspace_id=WS_ID,
                                                 identity_id=other_identity_id,
                                                 role="viewer", is_active=True))
        db.session.commit()

        app.extensions["_other_user_email"] = OTHER_EMAIL
        app.extensions["_other_user_password"] = OTHER_PASSWORD

    # Mock the generate_content function to avoid real AI calls
    import app.integration.service as svc_mod

    _original_generate = svc_mod.generate_content

    def _mock_generate(*args, **kwargs):
        return dict(MOCK_CONTENT_RESPONSE)

    svc_mod.generate_content = _mock_generate
    app.extensions["_mock_generate_original"] = _original_generate

    return app


@pytest.fixture(scope="module")
def server(journey_app):
    srv = Server(journey_app).start()
    yield srv
    srv.stop()


def test_gj08_content_studio_lifecycle_journey(server, journey_app):
    """Full Content Studio lifecycle over real HTTP."""
    report = {"journey": "GJ-08-CONTENT-STUDIO-LIFECYCLE", "steps": []}
    http = Http(server.base)

    def step(name, ok, detail=""):
        report["steps"].append({"step": name, "ok": bool(ok), "detail": detail})
        return ok

    # 1. AUTHENTICATE
    status, body = http.json("POST", "/api/v1/founder/signin",
                             {"email": EMAIL, "password": PASSWORD})
    step("signin_success", status == 200 and body.get("success") is True,
         f"signin -> {status}")
    identity_id = body.get("identity_id") or ""
    http.identity_id = identity_id
    assert identity_id, "No identity_id returned from signin"

    # 2. GENERATE content via API
    gen_payload = {
        "prompt": "Write a blog post about AI content creation",
        "content_type": "blog_post",
        "tone": "professional",
        "word_count": 200,
    }
    status, gen_result = http.json("POST", "/api/v1/content/generate", gen_payload)
    step("content_generated", status == 200 and gen_result.get("success") is True,
         f"generate -> {status}")
    content_id = gen_result.get("id")
    step("content_id_returned", bool(content_id), f"id={content_id}")
    assert content_id, "No id returned from generation"

    # 3. VERIFY ACTIVE lifecycle_status
    lifecycle_status = gen_result.get("lifecycle_status")
    step("lifecycle_status_is_active", lifecycle_status == "active",
         f"lifecycle_status={lifecycle_status}")

    # 4. GET content detail (new endpoint)
    status, detail = http.json("GET", f"/api/v1/content/{content_id}")
    step("get_content_detail", status == 200 and detail.get("success") is True,
         f"GET /content/{content_id} -> {status}")
    data = detail.get("data", {})
    step("detail_has_lifecycle_status",
         data.get("lifecycle_status") == "active",
         f"lifecycle_status={data.get('lifecycle_status')}")
    step("detail_has_identity_id",
         data.get("identity_id") == identity_id,
         f"identity_id={data.get('identity_id')}")

    # 5. PATCH metadata
    status, patch_result = http.json("PATCH", f"/api/v1/content/{content_id}",
                                     {"tone": "casual", "platform": "twitter"})
    step("patch_metadata", status == 200 and patch_result.get("success") is True,
         f"PATCH -> {status}")
    patched_data = patch_result.get("data", {})
    step("patch_tone_updated", patched_data.get("tone") == "casual",
         f"tone={patched_data.get('tone')}")

    # 6. LIST content with lifecycle filter
    status, list_result = http.json("GET", "/api/v1/content/?lifecycle_status=active")
    step("list_active_content", status == 200 and list_result.get("success") is True,
         f"list active -> {status}")
    items = list_result.get("data", [])
    step("list_contains_generated_item",
         any(item.get("id") == content_id for item in items),
         f"found {len(items)} items")

    # 7. ARCHIVE content → verify ARCHIVED
    status, archive_result = http.json("POST",
                                       f"/api/v1/content/{content_id}/archive")
    step("archive_success", status == 200 and archive_result.get("success") is True,
         f"archive -> {status}")
    step("archive_lifecycle_status",
         archive_result.get("lifecycle_status") == "archived",
         f"lifecycle_status={archive_result.get('lifecycle_status')}")

    # Verify content appears in ARCHIVED listing
    status, archived_list = http.json("GET",
                                      "/api/v1/content/?lifecycle_status=archived")
    step("archived_in_list",
         status == 200 and any(item.get("id") == content_id
                               for item in archived_list.get("data", [])),
         "archived content visible in archived list")

    # Verify it does NOT appear in ACTIVE listing
    status, active_list = http.json("GET",
                                    "/api/v1/content/?lifecycle_status=active")
    step("not_in_active_list",
         status == 200 and not any(item.get("id") == content_id
                                    for item in active_list.get("data", [])),
         "archived content excluded from active list")

    # 8. RESTORE from ARCHIVED → verify ACTIVE
    status, restore_from_archived = http.json("POST",
                                              f"/api/v1/content/{content_id}/restore")
    step("restore_from_archived", status == 200
         and restore_from_archived.get("success") is True,
         f"restore -> {status}")
    step("restored_lifecycle_status",
         restore_from_archived.get("lifecycle_status") == "active",
         f"lifecycle_status={restore_from_archived.get('lifecycle_status')}")

    # 9. TRASH content → verify TRASHED
    status, trash_result = http.json("POST", f"/api/v1/content/{content_id}/trash")
    step("trash_success", status == 200 and trash_result.get("success") is True,
         f"trash -> {status}")
    step("trashed_lifecycle_status",
         trash_result.get("lifecycle_status") == "trashed",
         f"lifecycle_status={trash_result.get('lifecycle_status')}")

    # 10. RESTORE from TRASHED → verify ACTIVE
    status, restore_result = http.json("POST",
                                       f"/api/v1/content/{content_id}/restore")
    step("restore_from_trashed", status == 200
         and restore_result.get("success") is True,
         f"restore -> {status}")
    step("restored_from_trashed_status",
         restore_result.get("lifecycle_status") == "active",
         f"lifecycle_status={restore_result.get('lifecycle_status')}")

    # Verify ACTIVE list includes restored item
    status, final_active_list = http.json("GET",
                                          "/api/v1/content/?lifecycle_status=active")
    step("restored_appears_in_active",
         status == 200 and any(item.get("id") == content_id
                               for item in final_active_list.get("data", [])),
         "restored content visible in active list")

    # 11. VERIFY permanent delete only works from TRASHED
    # First attempt: permanent delete on ACTIVE content should fail with 409
    status, pd_result_active = http.json("DELETE",
                                         f"/api/v1/content/{content_id}/permanent-delete")
    step("permanent_delete_fails_on_active",
         status == 409,
         f"permanent-delete on active -> {status}")

    # Trash it first (from active)
    status, trash_for_pd = http.json("POST", f"/api/v1/content/{content_id}/trash")
    step("trash_for_permanent_delete",
         status == 200 and trash_for_pd.get("success") is True,
         f"trash -> {status}")

    # Now permanent delete should succeed from TRASHED
    status, pd_result = http.json("DELETE",
                                  f"/api/v1/content/{content_id}/permanent-delete")
    step("permanent_delete_succeeds_from_trashed",
         status == 200 and pd_result.get("success") is True,
         f"permanent-delete from trashed -> {status}")
    step("permanent_delete_state",
         pd_result.get("state") == "deleted",
         f"state={pd_result.get('state')}")

    # Verify content is gone
    status, gone_detail = http.json("GET", f"/api/v1/content/{content_id}")
    step("permanently_deleted_content_gone",
         status == 404,
         f"GET after permanent-delete -> {status}")

    # 12. TENANT ISOLATION
    # Generate a second piece of content as the first user
    gen_payload2 = {"prompt": "Write about content isolation", "content_type": "blog_post"}
    status, gen2 = http.json("POST", "/api/v1/content/generate", gen_payload2)
    step("second_content_generated", status == 200 and gen2.get("success") is True,
         f"generate -> {status}")
    content2_id = gen2.get("id")

    # Sign in as OTHER user — provisioned in the journey_app fixture
    other_email = journey_app.extensions.get("_other_user_email", "other-cs-lifecycle@example.com")
    other_password = journey_app.extensions.get("_other_user_password", "other-cs-lifecycle-pass")
    status, signin_other = http.json("POST", "/api/v1/founder/signin",
                                     {"email": other_email, "password": other_password})
    step("other_user_signin", status == 200
         and signin_other.get("success") is True,
         f"other signin -> {status}")

    # Other user should NOT see the first user's content
    status, other_list = http.json("GET", "/api/v1/content/?lifecycle_status=active")
    other_items = other_list.get("data", [])
    step("tenant_isolation_denies_other_user",
         status == 200 and not any(item.get("id") == content2_id
                                    for item in other_items),
         f"other user sees {len(other_items)} items, none should be content2")

    # Other user should not be able to access first user's content detail
    status, other_detail = http.json("GET", f"/api/v1/content/{content2_id}")
    step("tenant_isolation_detail_denied",
         status == 404,
         f"other user GET detail -> {status}")

    # 13. RESTART SURVIVAL
    restarted = Server(journey_app).start()
    try:
        http2 = Http(restarted.base)
        s1, _ = http2.json("POST", "/api/v1/founder/signin",
                           {"email": EMAIL, "password": PASSWORD})
        s2, list_after_restart = http2.json("GET",
                                            "/api/v1/content/?lifecycle_status=active")
        items_after = list_after_restart.get("data", [])
        step("survives_server_restart",
             s1 == 200 and s2 == 200
             and any(item.get("id") == content2_id for item in items_after),
             f"restart: signin={s1} list={s2} found={len(items_after)} items")
    finally:
        restarted.stop()

    # 14. ANONYMOUS ACCESS DENIED
    anon = Http(server.base)
    s3, _ = anon.json("GET", "/api/v1/content/?lifecycle_status=active")
    step("anonymous_read_denied", s3 == 401, f"anonymous GET -> {s3}")

    s4, _ = anon.json("GET", f"/api/v1/content/{content2_id}")
    step("anonymous_detail_denied", s4 == 401, f"anonymous GET detail -> {s4}")

    s5, _ = anon.json("POST", "/api/v1/content/generate",
                      {"prompt": "test", "content_type": "blog_post"})
    step("anonymous_generate_denied", s5 == 401,
         f"anonymous generate -> {s5}")

    report["failed_steps"] = [s["step"] for s in report["steps"] if not s["ok"]]
    report["ok"] = not report["failed_steps"]
    out_dir = os.environ.get("JOURNEY_REPORT_DIR", tempfile.gettempdir())
    try:
        with open(os.path.join(out_dir, "journey_gj08_report.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    except OSError:
        pass

    assert report["ok"], (
        "GJ-08 Content Studio lifecycle journey failed at: "
        + ", ".join(report["failed_steps"]) + "\n"
        + json.dumps(report["steps"], indent=2)
    )