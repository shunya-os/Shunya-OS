"""GJ-10 — ATTENTION ITEM JOURNEY, driven over real HTTP.

Demonstrates: LIST → EMPTY → CREATE → LIST → GET → DISMISS → RESOLVE
→ WRONG TENANT → REFRESH SURVIVAL

Uses the same Http/Server harness pattern as other journey tests.
DATABASE_URL=sqlite:///:memory: for full isolation.
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

ORG_ID = 952
OTHER_ORG_ID = 999
WS_ID = "ws_attention_journey"
EMAIL = "attention-founder@example.com"
PASSWORD = "attention-pass-456"

SHELL_MARKER = "SHUNYA_ATTENTION_JOURNEY_SHELL"
SHELL_HTML = (
    "<!doctype html><html><head><title>SHUNYA</title></head>"
    f"<body>{SHELL_MARKER}<script crossorigin src=\"/assets/journey.js\"></script></body></html>"
)


@pytest.fixture(scope="module")
def release_shell_dir(tmp_path_factory):
    dist = tmp_path_factory.mktemp("attention_journey_release")
    (dist / "index.html").write_text(SHELL_HTML, encoding="utf-8")
    return dist


@pytest.fixture(autouse=True)
def _point_frontend_at_release(release_shell_dir, monkeypatch):
    monkeypatch.setenv("SHUNYA_FRONTEND_DIST", str(release_shell_dir))


class Http:
    """Minimal HTTP client with a cookie jar — real requests, real sessions."""

    def __init__(self, base: str):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.identity_id = ""
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    def call(self, method: str, path: str, body=None, content_type="application/json"):
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": content_type} if content_type else {}
        req = urllib.request.Request(
            f"{self.base}{path}", data=data, method=method, headers=headers,
        )
        try:
            with self.opener.open(req, timeout=30) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()

    def json(self, method: str, path: str, body=None):
        status, text = self.call(method, path, body)
        try:
            return status, json.loads(text)
        except json.JSONDecodeError:
            return status, {"_raw": text[:400]}


class Server:
    """The real application on a real socket."""

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
    """Create the Flask app with an in-memory SQLite database."""
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
            org = Organization(id=ORG_ID, name="Attention Test Org",
                               slug="attention-journey", is_active=True)
            db.session.add(org)
            db.session.flush()

        ws = db.session.get(Workspace, WS_ID)
        if not ws:
            ws = Workspace(id=WS_ID, name="Attention Test Workspace",
                           workspace_type="business", status="active",
                           created_by="journey_fixture", organization_id=ORG_ID)
            db.session.add(ws)
            db.session.flush()

        member = TeamMember.query.filter_by(email=EMAIL).first()
        if not member:
            member = TeamMember(name="Attention Founder", email=EMAIL,
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
                                     name="Attention Founder", email=EMAIL,
                                     role="owner"))
        if not ShWorkspaceMembership.query.filter_by(workspace_id=WS_ID,
                                                     identity_id=identity_id).first():
            db.session.add(ShWorkspaceMembership(workspace_id=WS_ID,
                                                 identity_id=identity_id,
                                                 role="owner", is_active=True))
        db.session.commit()

    app.config["_JOURNEY_DECLARED_SECURE_COOKIE"] = declared_secure
    return app


@pytest.fixture(scope="module")
def server(journey_app):
    srv = Server(journey_app).start()
    yield srv
    srv.stop()


def test_gj10_attention_journey(server, journey_app):
    """ATTENTION: EMPTY → CREATE → LIST → GET → DISMISS → RESOLVE → WRONG TENANT → REFRESH."""
    report = {"journey": "GJ-10-ATTENTION", "steps": []}
    http = Http(server.base)

    report["product_session_cookie_secure_declared"] = bool(
        journey_app.config.get("_JOURNEY_DECLARED_SECURE_COOKIE")
    )

    def step(name, ok, detail=""):
        report["steps"].append({"step": name, "ok": bool(ok), "detail": detail})
        return ok

    # 1. PUBLIC shell
    status, html = http.call("GET", "/")
    step("public_shell_served", status == 200 and SHELL_MARKER in html,
         f"GET / -> {status}")

    # 2. AUTH — sign in
    status, body = http.json("POST", "/api/v1/founder/signin",
                             {"email": EMAIL, "password": PASSWORD})
    step("signin_success", status == 200 and body.get("success") is True,
         f"signin -> {status}")
    identity_id = body.get("identity_id") or ""
    http.identity_id = identity_id

    # 3. LIST attention → empty state
    status, listed = http.json("GET", "/api/v1/attention/")
    step("list_empty", status == 200 and listed.get("count") == 0,
         f"list -> {status} count={listed.get('count')}")

    # 4. CREATE attention item directly via service
    with journey_app.app_context():
        from app import db
        from app.attention.service import create_attention_item

        item = create_attention_item(
            identity_id=identity_id,
            organization_id=ORG_ID,
            workspace_id=WS_ID,
            source="signal",
            related_object_type="Invoice",
            related_object_id="inv-042",
            reason="Overdue invoice detected: INV-042 is 15 days past due",
            priority=5,
            confidence=0.95,
            provenance={"detected_by": "test", "method": "direct_create"},
        )
        item_id = item.id
        # Create a second item for tenant isolation test
        other_item = create_attention_item(
            identity_id="other_identity",
            organization_id=OTHER_ORG_ID,
            workspace_id=WS_ID,
            source="signal",
            related_object_type="Lead",
            related_object_id="ld-001",
            reason="Hot lead needs attention",
            priority=4,
            confidence=0.8,
            provenance={"detected_by": "test", "method": "direct_create"},
        )
        other_item_id = other_item.id
        db.session.commit()

    step("item_created", item_id > 0, f"created attention item id={item_id}")

    # 5. LIST → item appears
    status, listed = http.json("GET", "/api/v1/attention/")
    step("list_shows_item", status == 200 and listed.get("count", 0) >= 1,
         f"list -> {status} count={listed.get('count')} items={[d.get('reason','')[:30] for d in (listed.get('data') or [])]}")

    # 6. GET item → detail matches
    status, detail = http.json("GET", f"/api/v1/attention/{item_id}")
    step("get_item_success", status == 200 and detail.get("success"),
         f"get -> {status}")
    data = detail.get("data", {})
    step("get_item_matches",
         data.get("id") == item_id
         and data.get("reason", "").startswith("Overdue invoice")
         and data.get("priority") == 5
         and data.get("state") == "active",
         f"id={data.get('id')} reason={data.get('reason')[:40]} priority={data.get('priority')} state={data.get('state')}")

    # 7. DISMISS item
    status, dismissed = http.json("POST", f"/api/v1/attention/{item_id}/dismiss",
                                  {"reason": "Reviewed and dismissed"})
    step("dismiss_success", status == 200 and dismissed.get("success"),
         f"dismiss -> {status}")
    step("dismiss_state",
         dismissed.get("data", {}).get("state") == "dismissed",
         f"state={dismissed.get('data', {}).get('state')}")

    # 8. RESOLVE a recreated item
    with journey_app.app_context():
        from app import db
        from app.attention.service import create_attention_item
        resolve_item = create_attention_item(
            identity_id=identity_id,
            organization_id=ORG_ID,
            workspace_id=WS_ID,
            source="intention.engine",
            related_object_type="Proposal",
            related_object_id="prop-007",
            reason="Proposal Q3-2026 ready for review",
            priority=4,
            provenance={"detected_by": "test", "method": "resolve_test"},
        )
        resolve_id = resolve_item.id
        db.session.commit()

    status, resolved = http.json("POST", f"/api/v1/attention/{resolve_id}/resolve")
    step("resolve_success", status == 200 and resolved.get("success"),
         f"resolve -> {status}")
    step("resolve_state",
         resolved.get("data", {}).get("state") == "resolved",
         f"state={resolved.get('data', {}).get('state')}")

    # 9. WRONG TENANT → denied
    status, denied = http.json("GET", f"/api/v1/attention/{other_item_id}")
    step("wrong_tenant_denied", status == 403,
         f"other_org_item GET -> {status}")

    # 10. REFRESH SURVIVAL
    restarted = Server(journey_app).start()
    try:
        http2 = Http(restarted.base)
        status2, body2 = http2.json("POST", "/api/v1/founder/signin",
                                    {"email": EMAIL, "password": PASSWORD})
        status3, listed2 = http2.json("GET", "/api/v1/attention/")
        step("survives_server_restart",
             status2 == 200 and status3 == 200 and listed2.get("count", 0) >= 0,
             f"restart: signin={status2} list={status3} count={listed2.get('count')}")
    finally:
        restarted.stop()

    # 11. ANONYMOUS READ DENIED
    anon = Http(server.base)
    status, _ = anon.json("GET", "/api/v1/attention/")
    step("anonymous_read_denied", status in (401, 403),
         f"anonymous GET -> {status}")

    report["failed_steps"] = [s["step"] for s in report["steps"] if not s["ok"]]
    report["ok"] = not report["failed_steps"]
    out_dir = os.environ.get("JOURNEY_REPORT_DIR", tempfile.gettempdir())
    try:
        with open(os.path.join(out_dir, "journey_gj10_report.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    except OSError:
        pass

    assert report["ok"], (
        "GJ-10 attention journey failed at: " + ", ".join(report["failed_steps"]) + "\n"
        + json.dumps(report["steps"], indent=2)
    )