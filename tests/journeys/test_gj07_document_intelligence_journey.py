"""GJ-07 — GATE 6 DOCUMENT INTELLIGENCE journey, driven over real HTTP.

Tests:
    - Upload a CSV file
    - Classification happens
    - Hierarchy is detected where applicable
    - Human correction is accepted
    - Re-analysis works
    - Tenant isolation
    - Refresh survival (server restart)
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
ALT_ORG_ID = 954
WS_ID = "ws_doc_intel_journey"
EMAIL = "doc-intel-journey@example.com"
ALT_EMAIL = "doc-intel-alt@example.com"
PASSWORD = "doc-intel-journey-pass"

SHELL_MARKER = "SHUNYA_DOC_INTEL_JOURNEY_SHELL"
SHELL_HTML = (
    "<!doctype html><html><head><title>SHUNYA</title></head>"
    f"<body>{SHELL_MARKER}<script crossorigin src=\"/assets/journey.js\"></script></body></html>"
)

# A CSV sample with travel itinerary data — hierarchy should detect Itinerary → International
SAMPLE_CSV_CONTENT = (
    "Name,Destination,CheckIn,CheckOut,Amount,Balance\n"
    "John Doe,Bali,2026-10-01,2026-10-05,1500.00,500.00\n"
    "Jane Smith,Thailand,2026-11-15,2026-11-20,2000.00,750.00\n"
)


@pytest.fixture(scope="module")
def release_shell_dir(tmp_path_factory):
    dist = tmp_path_factory.mktemp("doc_intel_journey_release")
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
        self.org_id = ORG_ID
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

    def upload_multipart_intel(self, path: str, filename: str,
                                file_content: bytes, content_type: str = "text/csv"):
        """Send a file as multipart/form-data to the intel upload endpoint."""
        boundary = "----DocIntelJourneyBoundary"
        body_parts = []
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(
            f'Content-Disposition: form-data; name="file"; '
            f'filename="{filename}"\r\n'.encode()
        )
        body_parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
        body_parts.append(file_content)
        body_parts.append(b"\r\n")
        body_parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(body_parts)

        req = urllib.request.Request(
            f"{self.base}{path}", data=body, method="POST",
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "X-Workspace-Id": WS_ID,
                "X-Identity-Id": self.identity_id,
            },
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


def _signin(http, email, password):
    """Sign in and return identity_id."""
    status, body = http.json(
        "POST", "/api/v1/founder/signin",
        {"email": email, "password": password},
    )
    if status == 200 and body.get("success") is True:
        return body.get("identity_id", "")
    return ""


def _create_org_and_user(org_id, email):
    from app import db
    from app.auth import TeamMember
    from app.models import OrgMember, Organization
    from app.objects.legacy_models import ShWorkspaceMembership, Workspace

    org = db.session.get(Organization, org_id)
    if not org:
        org = Organization(id=org_id, name=f"Doc Intel Org {org_id}",
                           slug=f"doc-intel-{org_id}", is_active=True)
        db.session.add(org)
        db.session.flush()

    ws = db.session.get(Workspace, WS_ID)
    if not ws:
        ws = Workspace(id=WS_ID, name="Doc Intel Workspace",
                       workspace_type="business", status="active",
                       created_by="journey_fixture", organization_id=org_id)
        db.session.add(ws)
        db.session.flush()

    member = TeamMember.query.filter_by(email=email).first()
    if not member:
        member = TeamMember(name=f"Doc Intel User {org_id}", email=email,
                            role="owner", is_active=True)
        member.set_password(PASSWORD)
        member.verified = True
        db.session.add(member)
        db.session.flush()

    identity_id = str(member.id)

    if not OrgMember.query.filter_by(organization_id=org_id,
                                     email=email).first():
        db.session.add(OrgMember(organization_id=org_id,
                                 identity_id=identity_id,
                                 name=f"Doc Intel User {org_id}", email=email,
                                 role="owner"))
    if not ShWorkspaceMembership.query.filter_by(workspace_id=WS_ID,
                                                 identity_id=identity_id).first():
        db.session.add(ShWorkspaceMembership(workspace_id=WS_ID,
                                             identity_id=identity_id,
                                             role="owner", is_active=True))
    db.session.commit()
    return identity_id


@pytest.fixture(scope="module")
def journey_app(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("doc_intel_journey_db") / "journey.db"
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

        _create_org_and_user(ORG_ID, EMAIL)
        _create_org_and_user(ALT_ORG_ID, ALT_EMAIL)

    app.config["_JOURNEY_DECLARED_SECURE_COOKIE"] = declared_secure
    return app


@pytest.fixture(scope="module")
def server(journey_app):
    srv = Server(journey_app).start()
    yield srv
    srv.stop()


def test_gj07_document_intelligence_journey(server, journey_app):
    """GATE 6: Upload CSV → classify → hierarchy → correct → reclassify → tenant isolation → refresh."""
    report = {"journey": "GJ-07-DOCUMENT-INTELLIGENCE", "steps": []}
    http = Http(server.base)

    def step(name, ok, detail=""):
        report["steps"].append({"step": name, "ok": bool(ok), "detail": detail})
        return ok

    # ── 1. Sign in ──────────────────────────────────────────────────
    identity_id = _signin(http, EMAIL, PASSWORD)
    step("signin_success", bool(identity_id),
         f"identity_id={identity_id[:16]}")
    http.identity_id = identity_id

    # ── 2. Upload CSV — document intelligence endpoint ──────────────
    csv_bytes = SAMPLE_CSV_CONTENT.encode("utf-8")
    status, body_text = http.upload_multipart_intel(
        "/api/v1/documents/upload",
        "travel_bookings.csv",
        csv_bytes,
    )
    uploaded = {}
    try:
        uploaded = json.loads(body_text)
    except json.JSONDecodeError:
        pass
    step("upload_accepted", status == 201,
         f"upload -> {status}")

    doc = (uploaded.get("document") or {})
    doc_id = doc.get("id")
    step("upload_returns_document_id", bool(doc_id),
         f"doc_id={doc_id}")

    # ── 3. Verify classification happened ───────────────────────────
    classification = doc.get("classification", "")
    intelligence = doc.get("intelligence", {})
    has_classification = bool(intelligence.get("classification")) or bool(classification)
    step("classification_happened", has_classification,
         f"classification={classification}, intelligence={json.dumps(intelligence)[:200]}")

    # ── 4. Verify hierarchy detected ────────────────────────────────
    hierarchy = doc.get("hierarchy", intelligence.get("hierarchy", []))
    has_hierarchy = len(hierarchy) >= 1
    step("hierarchy_detected", has_hierarchy,
         f"hierarchy={hierarchy}")

    # ── 5. Verify entities extracted ────────────────────────────────
    entities = intelligence.get("entities", {})
    has_entities = len(entities) > 0
    step("entities_extracted", has_entities,
         f"entity_types={list(entities.keys())}")

    # ── 6. Get document via GET endpoint ────────────────────────────
    status, detail = http.json("GET", f"/api/v1/documents/{doc_id}")
    step("get_document_works", status == 200,
         f"GET /api/v1/documents/{doc_id} -> {status}")
    detail_doc = (detail.get("document") or {})
    detail_intel = detail_doc.get("intelligence", {})
    step("get_returns_intelligence",
         detail_intel.get("classification") is not None,
         f"classification from GET={detail_intel.get('classification')}")

    # ── 7. List documents ───────────────────────────────────────────
    status, doclist = http.json("GET", "/api/v1/documents/")
    step("list_documents_works", status == 200,
         f"list -> {status}, count={len(doclist.get('documents', []))}")
    docs_found = any(d.get("id") == doc_id for d in doclist.get("documents", []))
    step("uploaded_doc_in_list", docs_found,
         f"doc_id={doc_id} found in list")

    # ── 8. Human correction ─────────────────────────────────────────
    correction_payload = {"classification": "invoice"}
    status, corrected = http.json(
        "POST", f"/api/v1/documents/{doc_id}/classify", correction_payload,
    )
    step("human_correction_accepted", status == 200,
         f"classify -> {status}")
    corrected_doc = (corrected.get("document") or {})
    corrected_intel = corrected_doc.get("intelligence", {})
    step("correction_persists", corrected_doc.get("classification") == "invoice",
         f"classification after correction={corrected_doc.get('classification')}")
    step("correction_flagged", corrected_intel.get("corrected_by_human") is True,
         f"corrected_by_human={corrected_intel.get('corrected_by_human')}")

    # ── 9. Re-analysis (reclassify) preserves human correction ──────
    status, reanalysed = http.json(
        "POST", f"/api/v1/documents/{doc_id}/reclassify",
    )
    step("reanalysis_works", status == 200,
         f"reclassify -> {status}")
    re_doc = (reanalysed.get("document") or {})
    re_intel = re_doc.get("intelligence", {})
    step("reanalysis_preserves_human_correction",
         re_doc.get("classification") == "invoice",
         f"classification after reclassify={re_doc.get('classification')}")
    step("reanalysis_still_flagged_human",
         re_intel.get("corrected_by_human") is True,
         f"corrected_by_human after reclassify={re_intel.get('corrected_by_human')}")

    # ── 10. Tenant isolation: alt org cannot see doc ────────────────
    alt_http = Http(server.base)
    alt_identity = _signin(alt_http, ALT_EMAIL, PASSWORD)
    alt_http.identity_id = alt_identity
    alt_http.org_id = ALT_ORG_ID

    status_alt_get, alt_detail = alt_http.json(
        "GET", f"/api/v1/documents/{doc_id}",
    )
    step("tenant_isolation_get", status_alt_get == 404,
         f"alt org GET -> {status_alt_get}")

    status_alt_list, alt_list = alt_http.json(
        "GET", "/api/v1/documents/",
    )
    alt_docs = alt_list.get("documents", [])
    alt_doc_ids = [d.get("id") for d in alt_docs]
    step("tenant_isolation_list", doc_id not in alt_doc_ids,
         f"alt org docs={alt_doc_ids}")

    # ── 11. Refresh survival (server restart) ───────────────────────
    restarted = Server(journey_app).start()
    try:
        http2 = Http(restarted.base)
        id2 = _signin(http2, EMAIL, PASSWORD)
        http2.org_id = ORG_ID
        http2.identity_id = id2

        status2, detail2 = http2.json(
            "GET", f"/api/v1/documents/{doc_id}",
        )
        step("refresh_survival_get", status2 == 200,
             f"restart GET -> {status2}")

        detail2_doc = (detail2.get("document") or {})
        step("classification_survives_restart",
             detail2_doc.get("classification") == "invoice",
             f"classification after restart={detail2_doc.get('classification')}")

        intel2 = detail2_doc.get("intelligence", {})
        step("correction_survives_restart",
             intel2.get("corrected_by_human") is True,
             f"corrected_by_human after restart={intel2.get('corrected_by_human')}")

        # Verify hierarchy still present
        h2 = intel2.get("hierarchy", [])
        step("hierarchy_survives_restart", len(h2) >= 1,
             f"hierarchy after restart={h2}")

        status2_list, list2 = http2.json("GET", "/api/v1/documents/")
        step("list_survives_restart", status2_list == 200,
             f"list after restart -> {status2_list}")
    finally:
        restarted.stop()

    # ── 12. Delete (trash) document ─────────────────────────────────
    status_del, deleted = http.json(
        "DELETE", f"/api/v1/documents/{doc_id}",
    )
    step("delete_works", status_del == 200,
         f"DELETE -> {status_del}")
    deleted_status = (deleted.get("document") or {}).get("status", "")
    step("delete_removes_document",
         deleted_status == "deleted",
         f"status after delete={deleted_status}")

    # ── Report ──────────────────────────────────────────────────────
    report["failed_steps"] = [s["step"] for s in report["steps"] if not s["ok"]]
    report["ok"] = not report["failed_steps"]
    out_dir = os.environ.get("JOURNEY_REPORT_DIR", tempfile.gettempdir())
    try:
        with open(
            os.path.join(out_dir, "journey_gj07_report.json"), "w", encoding="utf-8"
        ) as fh:
            json.dump(report, fh, indent=2)
    except OSError:
        pass

    assert report["ok"], (
        "GJ-07 document intelligence journey failed at: "
        + ", ".join(report["failed_steps"]) + "\n"
        + json.dumps(report["steps"], indent=2)
    )