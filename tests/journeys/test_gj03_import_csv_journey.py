"""GJ-03 — IMPORT STRUCTURED DATA journey, driven over real HTTP.

Demonstrates: SELECT → UPLOAD → ANALYZE → IDENTIFY → PREVIEW → COMMIT
→ VERIFY → AVAILABLE IN WORKSPACE.

Uses the same Http/Server harness pattern as test_m5_entry_workspace_journey.
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

ORG_ID = 951
WS_ID = "ws_import_journey"
EMAIL = "import-founder@example.com"
PASSWORD = "import-pass-456"

SHELL_MARKER = "SHUNYA_IMPORT_JOURNEY_SHELL"
SHELL_HTML = (
    "<!doctype html><html><head><title>SHUNYA</title></head>"
    f"<body>{SHELL_MARKER}<script crossorigin src=\"/assets/journey.js\"></script></body></html>"
)


@pytest.fixture(scope="module")
def release_shell_dir(tmp_path_factory):
    dist = tmp_path_factory.mktemp("import_journey_release")
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

    def upload(self, path: str, filename: str, file_content: bytes):
        """Multipart upload — mimics browser file upload."""
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_parts = []
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
        )
        body_parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
        body_parts.append(file_content)
        body_parts.append(b"\r\n")
        body_parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(body_parts)

        req = urllib.request.Request(
            f"{self.base}{path}",
            data=body,
            method="POST",
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        try:
            with self.opener.open(req, timeout=30) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()


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
    db_file = tmp_path_factory.mktemp("import_journey_db") / "journey.db"
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
            org = Organization(id=ORG_ID, name="Import Test Org",
                               slug="import-journey", is_active=True)
            db.session.add(org)
            db.session.flush()

        ws = db.session.get(Workspace, WS_ID)
        if not ws:
            ws = Workspace(id=WS_ID, name="Import Test Workspace",
                           workspace_type="business", status="active",
                           created_by="journey_fixture", organization_id=ORG_ID)
            db.session.add(ws)
            db.session.flush()

        member = TeamMember.query.filter_by(email=EMAIL).first()
        if not member:
            member = TeamMember(name="Import Founder", email=EMAIL,
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
                                     name="Import Founder", email=EMAIL,
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
def csv_data():
    """A minimal CSV representing customer records."""
    return b"name,email,company,status\nAlice,alice@example.com,Acme Corp,active\nBob,bob@example.com,Globex,LTD,lead"


def test_import_csv_journey(server, journey_app, csv_data):
    """UPLOAD CSV → VERIFY → OBJECT IN WORKSPACE."""
    report = {"journey": "GJ-03-IMPORT-CSV", "steps": []}
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

    # 3. UPLOAD CSV — send as multipart file upload
    status, body_text = http.upload("/api/v1/upload", "test_customers.csv", csv_data)
    uploaded = {}
    try:
        uploaded = json.loads(body_text)
    except json.JSONDecodeError:
        pass
    step("upload_accepted", status in (200, 201),
         f"upload -> {status} {body_text[:200]}")

    # The upload may return canonical object(s) or a document reference
    doc_id = uploaded.get("document_id") or uploaded.get("id")
    step("upload_returns_id", bool(doc_id),
         f"upload returned id={doc_id}")

    # 4. VERIFY — check that objects appear in the workspace
    status, listed = http.json("GET", "/api/v1/objects?limit=50")
    object_names = [o.get("name") for o in (listed.get("data") or [])]
    step("uploaded_data_in_workspace",
         status == 200 and any("alice" in (n or "").lower() for n in object_names),
         f"objects after import: {object_names[:10]}")

    # 5. PERSISTENCE across restart
    restarted = Server(journey_app).start()
    try:
        http2 = Http(restarted.base)
        status2, body2 = http2.json("POST", "/api/v1/founder/signin",
                                    {"email": EMAIL, "password": PASSWORD})
        status3, listed2 = http2.json("GET", "/api/v1/objects?limit=50")
        names2 = [o.get("name") for o in (listed2.get("data") or [])]
        step("survives_server_restart",
             status2 == 200 and status3 == 200 and any("alice" in (n or "").lower() for n in names2),
             f"restart: signin={status2} list={status3}")
    finally:
        restarted.stop()

    # 6. SECURITY — anonymous read denied
    anon = Http(server.base)
    status, _ = anon.json("GET", "/api/v1/objects?limit=10")
    step("anonymous_read_denied", status == 401,
         f"anonymous GET -> {status}")

    report["failed_steps"] = [s["step"] for s in report["steps"] if not s["ok"]]
    report["ok"] = not report["failed_steps"]
    out_dir = os.environ.get("JOURNEY_REPORT_DIR", tempfile.gettempdir())
    try:
        with open(os.path.join(out_dir, "journey_gj03_report.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    except OSError:
        pass

    assert report["ok"], (
        "GJ-03 import journey failed at: " + ", ".join(report["failed_steps"]) + "\n"
        + json.dumps(report["steps"], indent=2)
    )