"""GJ-04 — UPLOAD DOCUMENT journey, driven over real HTTP.

Demonstrates: SELECT → UPLOAD → ANALYZE → VERIFY → AVAILABLE IN WORKSPACE.

Uses the same Http/Server harness pattern as other journey tests.
"""
import json
import os
import tempfile
import threading
import urllib.error
import urllib.request

import pytest
from werkzeug.serving import make_server

ORG_ID = 952
WS_ID = "ws_doc_journey"
EMAIL = "doc-journey@example.com"
PASSWORD = "doc-journey-pass"

SHELL_MARKER = "SHUNYA_DOC_JOURNEY_SHELL"
SHELL_HTML = (
    "<!doctype html><html><head><title>SHUNYA</title></head>"
    f"<body>{SHELL_MARKER}<script crossorigin src=\"/assets/journey.js\"></script></body></html>"
)


@pytest.fixture(scope="module")
def release_shell_dir(tmp_path_factory):
    dist = tmp_path_factory.mktemp("doc_journey_release")
    (dist / "index.html").write_text(SHELL_HTML, encoding="utf-8")
    return dist


@pytest.fixture(autouse=True)
def _point_frontend_at_release(release_shell_dir, monkeypatch):
    monkeypatch.setenv("SHUNYA_FRONTEND_DIST", str(release_shell_dir))


class Http:
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

    def upload_multipart(self, path: str, filename: str, file_content: bytes):
        """Send a file as multipart/form-data."""
        boundary = "----DocJourneyBoundary"
        body_parts = []
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
        )
        body_parts.append(b"Content-Type: application/pdf\r\n\r\n")
        body_parts.append(file_content)
        body_parts.append(b"\r\n")
        body_parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(body_parts)

        req = urllib.request.Request(
            f"{self.base}{path}", data=body, method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        try:
            with self.opener.open(req, timeout=30) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()


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
    db_file = tmp_path_factory.mktemp("doc_journey_db") / "journey.db"
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
            org = Organization(id=ORG_ID, name="Doc Journey Org",
                               slug="doc-journey", is_active=True)
            db.session.add(org)
            db.session.flush()

        ws = db.session.get(Workspace, WS_ID)
        if not ws:
            ws = Workspace(id=WS_ID, name="Doc Journey Workspace",
                           workspace_type="business", status="active",
                           created_by="journey_fixture", organization_id=ORG_ID)
            db.session.add(ws)
            db.session.flush()

        member = TeamMember.query.filter_by(email=EMAIL).first()
        if not member:
            member = TeamMember(name="Doc Journey Founder", email=EMAIL,
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
                                     name="Doc Journey Founder", email=EMAIL,
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
def sample_pdf():
    """A minimal valid PDF (just enough to be identified as a PDF)."""
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"


def test_upload_document_journey(server, journey_app, sample_pdf):
    """UPLOAD PDF → VERIFY → PERSISTENCE → SECURITY."""
    report = {"journey": "GJ-04-UPLOAD-DOCUMENT", "steps": []}
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

    # 3. UPLOAD PDF
    status, body_text = http.upload_multipart("/api/v1/upload",
                                               "panchi_itinerary.pdf", sample_pdf)
    uploaded = {}
    try:
        uploaded = json.loads(body_text)
    except json.JSONDecodeError:
        pass
    step("upload_accepted", status in (200, 201),
         f"upload -> {status} {body_text[:200]}")

    doc_id = uploaded.get("document_id") or uploaded.get("id")
    step("upload_returns_document_id", bool(doc_id),
         f"doc_id={doc_id}")

    # 4. VERIFY document appears in workspace objects
    status, listed = http.json("GET", "/api/v1/objects?limit=50")
    object_names = [o.get("name") for o in (listed.get("data") or [])]
    step("upload_visible_in_workspace",
         status == 200 and any("panchi" in (n or "").lower() for n in object_names),
         f"objects after upload: {object_names[:10]}")

    # 5. PERSISTENCE across restart
    restarted = Server(journey_app).start()
    try:
        http2 = Http(restarted.base)
        s1, _ = http2.json("POST", "/api/v1/founder/signin",
                           {"email": EMAIL, "password": PASSWORD})
        s2, listed2 = http2.json("GET", "/api/v1/objects?limit=50")
        names2 = [o.get("name") for o in (listed2.get("data") or [])]
        step("survives_server_restart",
             s1 == 200 and s2 == 200 and any("panchi" in (n or "").lower() for n in names2),
             f"restart: signin={s1} list={s2}")
    finally:
        restarted.stop()

    # 6. SECURITY
    anon = Http(server.base)
    s3, _ = anon.json("GET", "/api/v1/objects?limit=10")
    step("anonymous_read_denied", s3 == 401, f"anonymous GET -> {s3}")

    report["failed_steps"] = [s["step"] for s in report["steps"] if not s["ok"]]
    report["ok"] = not report["failed_steps"]
    out_dir = os.environ.get("JOURNEY_REPORT_DIR", tempfile.gettempdir())
    try:
        with open(os.path.join(out_dir, "journey_gj04_report.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    except OSError:
        pass

    assert report["ok"], (
        "GJ-04 upload document journey failed at: "
        + ", ".join(report["failed_steps"]) + "\n"
        + json.dumps(report["steps"], indent=2)
    )