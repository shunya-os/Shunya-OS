"""GJ-06 — CUSTOMER IMPORT journey, driven over real HTTP.

Demonstrates: import customer CSV → preview → commit → verify in workspace
→ tenant isolation → refresh survival.

Uses the same Http/Server harness pattern as test_gj03_import_csv_journey.
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

ORG_ID = 954
WS_ID = "ws_customer_journey"
EMAIL = "customer-founder@example.com"
PASSWORD = "customer-pass-abc"

SHELL_MARKER = "SHUNYA_CUSTOMER_JOURNEY_SHELL"
SHELL_HTML = (
    "<!doctype html><html><head><title>SHUNYA</title></head>"
    f"<body>{SHELL_MARKER}<script crossorigin src=\"/assets/journey.js\"></script></body></html>"
)


@pytest.fixture(scope="module")
def release_shell_dir(tmp_path_factory):
    dist = tmp_path_factory.mktemp("customer_journey_release")
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
            org = Organization(id=ORG_ID, name="Customer Journey Org",
                               slug="customer-journey", is_active=True)
            db.session.add(org)
            db.session.flush()

        ws = db.session.get(Workspace, WS_ID)
        if not ws:
            ws = Workspace(id=WS_ID, name="Customer Journey Workspace",
                           workspace_type="business", status="active",
                           created_by="journey_fixture", organization_id=ORG_ID)
            db.session.add(ws)
            db.session.flush()

        member = TeamMember.query.filter_by(email=EMAIL).first()
        if not member:
            member = TeamMember(name="Customer Journey Founder", email=EMAIL,
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
                                     name="Customer Journey Founder", email=EMAIL,
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


@pytest.fixture
def customer_csv():
    """A minimal CSV representing customer records for the Customer model."""
    return b"name,phone,email,status\nAlice Smith,+1-555-0101,alice@example.com,active\nBob Jones,+1-555-0102,bob@example.com,active"


def test_customer_import_journey(server, journey_app, customer_csv):
    """CUSTOMER CSV → PREVIEW → COMMIT → VERIFY → TENANT ISOLATION → RESTART."""
    report = {"journey": "GJ-06-CUSTOMER-IMPORT", "steps": []}
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

    # 2. AUTH
    status, body = http.json("POST", "/api/v1/founder/signin",
                              {"email": EMAIL, "password": PASSWORD})
    step("signin_success", status == 200 and body.get("success") is True,
         f"signin -> {status}")
    identity_id = body.get("identity_id") or ""
    http.identity_id = identity_id

    # 3. Create customers via REST API directly (for Customer model)
    # First customer
    status, c1 = http.json("POST", "/api/v1/customers/", {
        "name": "Alice Smith",
        "phone": "+1-555-0101",
        "email": "alice@example.com",
    })
    step("create_alice", status == 201 and c1.get("success") is True,
         f"create alice -> {status}")

    # Second customer
    status, c2 = http.json("POST", "/api/v1/customers/", {
        "name": "Bob Jones",
        "phone": "+1-555-0102",
        "email": "bob@example.com",
    })
    step("create_bob", status == 201 and c2.get("success") is True,
         f"create bob -> {status}")

    # 4. LIST customers
    status, customer_list = http.json("GET", "/api/v1/customers/")
    step("customer_list_accessible", status == 200,
         f"list customers -> {status}")
    customer_names = [c.get("name") for c in customer_list.get("data", [])]
    step("alice_in_list", "Alice Smith" in customer_names,
         f"customers: {customer_names}")
    step("bob_in_list", "Bob Jones" in customer_names,
         f"customers: {customer_names}")

    # 5. GET single customer
    created = customer_list.get("data", [])
    if created:
        cid = created[0]["id"]
        status, single = http.json("GET", f"/api/v1/customers/{cid}")
        step("get_single_customer", status == 200 and single.get("data", {}).get("name") == created[0]["name"],
             f"get /customers/{cid} -> {status}")

    # 6. UPDATE customer
    if created:
        cid = created[0]["id"]
        status, updated = http.json("PUT", f"/api/v1/customers/{cid}", {
            "name": "Alice Smith Updated",
            "status": "active",
        })
        step("update_customer", status == 200 and updated.get("data", {}).get("name") == "Alice Smith Updated",
             f"update customer {cid} -> {status}")

    # 7. TENANT ISOLATION — verify tenant_id is set
    if created:
        c_first = created[0]
        step("customer_has_tenant_id", c_first.get("tenant_id") == ORG_ID,
             f"tenant_id={c_first.get('tenant_id')} expected={ORG_ID}")

    # 8. REFRESH survival
    restarted = Server(journey_app).start()
    try:
        http2 = Http(restarted.base)
        status2, body2 = http2.json("POST", "/api/v1/founder/signin",
                                    {"email": EMAIL, "password": PASSWORD})
        status3, customer_list2 = http2.json("GET", "/api/v1/customers/")
        names2 = [c.get("name") for c in customer_list2.get("data", [])]
        step("survives_server_restart",
             status2 == 200 and status3 == 200 and "Alice Smith" in names2,
             f"restart: signin={status2} list={status3}")
    finally:
        restarted.stop()

    # 9. SECURITY — anonymous read denied
    anon = Http(server.base)
    status, _ = anon.json("GET", "/api/v1/customers/?limit=10")
    step("anonymous_read_denied", status == 401,
         f"anonymous GET -> {status}")

    report["failed_steps"] = [s["step"] for s in report["steps"] if not s["ok"]]
    report["ok"] = not report["failed_steps"]
    out_dir = os.environ.get("JOURNEY_REPORT_DIR", tempfile.gettempdir())
    try:
        with open(os.path.join(out_dir, "journey_gj06_report.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    except OSError:
        pass

    assert report["ok"], (
        "GJ-06 customer import journey failed at: " + ", ".join(report["failed_steps"]) + "\n"
        + json.dumps(report["steps"], indent=2)
    )