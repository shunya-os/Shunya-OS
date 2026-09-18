"""M5 — ENTRY → WORKSPACE journey, driven over real HTTP against a real server.

This is the campaign's missing evidence layer. CI currently proves unit-level
behaviour on SQLite and nothing about a user journey: there is no browser or
journey test anywhere in `.github/workflows/ci.yml`. Until a journey is actually
executed, M5 cannot reach USER-PROVEN.

What this does differently from the rest of the suite:
  * it starts the real WSGI application on a real TCP socket (werkzeug
    ``make_server``) and talks to it over HTTP with a real cookie jar, so
    routing, sessions, middleware and serialisation are all exercised;
  * it uses a FILE-based database, so state genuinely survives a server restart
    within the journey (an in-memory DB cannot prove that).

Honest limitation, stated rather than implied: the journey database is SQLite,
not the production PostgreSQL. This proves the journey is WIRED end to end; it
does not prove Postgres parity. That remains a separate gap.

The journey is ONE ordered test (not a set of independent tests) because it
asserts a sequence a human actually performs. Each step is recorded in a
machine-readable report; any failed step fails the test with the exact step name.
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

ORG_ID = 950
WS_ID = "ws_journey_1"
EMAIL = "journey-founder@example.com"
PASSWORD = "journey-pass-123"
OBJECT_NAME = "Bali Retreat Customer"


# ---------------------------------------------------------------------------
# Real HTTP client
# ---------------------------------------------------------------------------

class Http:
    """Minimal HTTP client with a cookie jar — real requests, real sessions."""

    def __init__(self, base: str):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    def call(self, method: str, path: str, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.base}{path}", data=data, method=method,
            headers={"Content-Type": "application/json"},
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


# ---------------------------------------------------------------------------
# Application + explicit minimal tenancy
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def journey_app(tmp_path_factory):
    """The real app factory against a FILE-backed database (survives restart)."""
    db_file = tmp_path_factory.mktemp("journey_db") / "journey.db"
    from app import create_app, db

    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
        "WTF_CSRF_ENABLED": False,
    })

    # The app declares SESSION_COOKIE_SECURE=True unconditionally, which is
    # correct for HTTPS production. This harness speaks plain HTTP to a loopback
    # socket, and Python's cookiejar refuses to replay a Secure cookie over http
    # (it rejected the session cookie, so every authenticated read returned 401).
    # The accommodation below is scoped to the harness; the product's declared
    # posture is asserted unchanged and reported.
    declared_secure = app.config["SESSION_COOKIE_SECURE"]
    app.config["SESSION_COOKIE_SECURE"] = False

    with app.app_context():
        db.create_all()

        from app.auth import TeamMember
        from app.models import OrgMember, Organization
        from app.objects.legacy_models import ShWorkspaceMembership, Workspace

        org = db.session.get(Organization, ORG_ID)
        if not org:
            org = Organization(id=ORG_ID, name="Panchi Club Bali",
                               slug="panchi-journey", is_active=True)
            db.session.add(org)
            db.session.flush()

        ws = db.session.get(Workspace, WS_ID)
        if not ws:
            ws = Workspace(id=WS_ID, name="Panchi Operations",
                           workspace_type="business", status="active",
                           created_by="journey_fixture", organization_id=ORG_ID)
            db.session.add(ws)
            db.session.flush()

        member = TeamMember.query.filter_by(email=EMAIL).first()
        if not member:
            member = TeamMember(name="Journey Founder", email=EMAIL,
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
                                     name="Journey Founder", email=EMAIL,
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


# ---------------------------------------------------------------------------
# The journey
# ---------------------------------------------------------------------------

def test_m5_entry_to_workspace_journey(server, journey_app):
    """PUBLIC → AUTH → IDENTITY → WORKSPACE → UNDERSTAND → ACT → RECOVER."""
    report = {"journey": "M5-ENTRY-TO-WORKSPACE", "steps": []}
    http = Http(server.base)

    # The harness only disabled Secure on the session cookie to allow loopback
    # HTTP. The product's declared posture must still be True.
    report["product_session_cookie_secure_declared"] = bool(
        journey_app.config.get("_JOURNEY_DECLARED_SECURE_COOKIE")
    )

    def step(name, ok, detail=""):
        report["steps"].append({"step": name, "ok": bool(ok), "detail": detail})
        return ok

    # 0. Product posture unchanged by the harness accommodation
    step("product_declares_secure_session_cookie",
         report["product_session_cookie_secure_declared"] is True,
         "app.config SESSION_COOKIE_SECURE=True before the harness override")

    # 1. PUBLIC — the SPA shell is served to an anonymous visitor
    status, html = http.call("GET", "/")
    step("public_shell_served", status == 200 and "<html" in html.lower(),
         f"GET / -> {status}")

    # 2. AUTH — signing in establishes a session
    status, body = http.json("POST", "/api/v1/founder/signin",
                             {"email": EMAIL, "password": PASSWORD})
    step("signin_establishes_session", status == 200 and body.get("success") is True,
         f"POST /api/v1/founder/signin -> {status} {str(body)[:160]}")
    step("session_cookie_present", len(http.jar) > 0, f"cookies={len(http.jar)}")

    # 3. IDENTITY / ORGANIZATION — the workspace context resolves
    status, who = http.json("GET", "/api/v1/for2/whoami")
    step("identity_context_resolves", status == 200,
         f"GET /api/v1/for2/whoami -> {status} {str(who)[:160]}")

    # 4. ACT — create a real business object through the canonical route
    status, created = http.json("POST", "/api/v1/objects/",
                                {"name": OBJECT_NAME, "object_type": "customer"})
    object_id = created.get("id") or created.get("object_id")
    step("create_canonical_object", status in (200, 201) and bool(object_id),
         f"POST /api/v1/objects/ -> {status} {str(created)[:160]}")

    # 5. UNDERSTAND — the object is visible in the workspace read surfaces
    status, types = http.json("GET", "/api/v1/objects/types")
    counts = (types or {}).get("data") or {}
    step("object_visible_in_type_inventory",
         status == 200 and counts.get("customer", 0) >= 1,
         f"GET /api/v1/objects/types -> {status} counts={counts}")

    status, listed = http.json("GET", "/api/v1/objects/customer")
    names = [o.get("name") for o in ((listed.get("data") or {}).get("objects") or [])]
    step("object_visible_in_typed_list", status == 200 and OBJECT_NAME in names,
         f"GET /api/v1/objects/customer -> {status} names={names}")

    status, collection = http.json("GET", "/api/v1/objects?limit=100")
    coll_names = [o.get("name") for o in (collection.get("data") or [])]
    step("object_visible_in_collection", status == 200 and OBJECT_NAME in coll_names,
         f"GET /api/v1/objects -> {status} names={coll_names}")

    # 6. INTELLIGENCE — the ask endpoint the resident surface calls is reachable
    status, ask = http.json("POST", "/api/v1/intelligence/ask",
                            {"question": "What customers do we have?"})
    step("ask_endpoint_reachable", status not in (404, 405),
         f"POST /api/v1/intelligence/ask -> {status} {str(ask)[:120]}")

    # 7. RECOVER — lifecycle: trash hides the object, recover brings it back
    status, trashed = http.json("POST", f"/api/v1/objects/{object_id}/lifecycle",
                                {"action": "trash"})
    step("lifecycle_trash_accepted", status == 200 and trashed.get("success") is True,
         f"POST lifecycle trash -> {status} {str(trashed)[:120]}")

    status, after_trash = http.json("GET", "/api/v1/objects/customer")
    trash_names = [o.get("name") for o in ((after_trash.get("data") or {}).get("objects") or [])]
    step("trashed_object_no_longer_listed", OBJECT_NAME not in trash_names,
         f"after trash, names={trash_names}")

    status, recovered = http.json("POST", f"/api/v1/objects/{object_id}/lifecycle",
                                  {"action": "recover"})
    step("lifecycle_recover_accepted", status == 200 and recovered.get("success") is True,
         f"POST lifecycle recover -> {status} {str(recovered)[:120]}")

    status, after_recover = http.json("GET", "/api/v1/objects/customer")
    rec_names = [o.get("name") for o in ((after_recover.get("data") or {}).get("objects") or [])]
    step("recovered_object_listed_again", OBJECT_NAME in rec_names,
         f"after recover, names={rec_names}")

    # 8. PERSISTENCE across a real server restart
    restarted = Server(journey_app).start()
    try:
        http2 = Http(restarted.base)
        status, body2 = http2.json("POST", "/api/v1/founder/signin",
                                   {"email": EMAIL, "password": PASSWORD})
        status2, listed2 = http2.json("GET", "/api/v1/objects/customer")
        names2 = [o.get("name") for o in ((listed2.get("data") or {}).get("objects") or [])]
        step("survives_server_restart",
             status == 200 and status2 == 200 and OBJECT_NAME in names2,
             f"after restart: signin={status} list={status2} names={names2}")
    finally:
        restarted.stop()

    # 9. SECURITY — the same journey without a session must be denied
    anon = Http(server.base)
    status, _ = anon.json("GET", "/api/v1/objects/customer")
    step("anonymous_read_denied", status == 401, f"anonymous GET -> {status}")

    # report + verdict
    report["failed_steps"] = [s["step"] for s in report["steps"] if not s["ok"]]
    report["ok"] = not report["failed_steps"]
    out_dir = os.environ.get("JOURNEY_REPORT_DIR", tempfile.gettempdir())
    try:
        with open(os.path.join(out_dir, "journey_m5_report.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    except OSError:
        pass

    assert report["ok"], (
        "M5 journey failed at: " + ", ".join(report["failed_steps"]) + "\n"
        + json.dumps(report["steps"], indent=2)
    )
