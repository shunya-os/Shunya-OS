"""R6B-2.7 Window 6 — production read-bypass remediation: regression + adversarial.

Covers the confirmed LIVE findings from
`artifacts/r6b27/R6B-2.7_WINDOW6_PRODUCTION_READ_CLASSIFICATION.md`:

  A1  GET /api/v1/events (+ /events/stream) — cross-tenant object/event stream
  A2  GET /api/v1/upload                    — unscoped Document listing
  A3  upload dedup probe                    — cross-tenant existence disclosure
  A4  GET /api/v1/files                     — workspace header, no tenant authz
  A5  DELETE /api/v1/files/<id>             — cross-tenant WRITE
  A6  PATCH  /api/v1/files/<id>/rename      — cross-tenant WRITE
  A7  GET /api/v1/pdf/proposal/<id>         — unscoped read, no permission gate
  A8  GET /api/v1/pdf/invoice/<id>          — unscoped read, no permission gate
  A12 POST /api/v1/upload                   — write outside ObjectService, NULL org

Tenancy is built explicitly: two organizations, one workspace each, one
authorized identity each, plus one identity with no membership at all. No
synthetic organization, no `spc_*` workspace, no universal membership, no
`system_scope`.
"""
import pytest
import uuid

ORG_A, ORG_B = 711, 712

WS_A1 = "ws_rb_a1"
WS_B1 = "ws_rb_b1"

ALICE = "readbypass-alice@example.com"
BOB = "readbypass-bob@example.com"
NOBODY = "readbypass-nobody@example.com"
MULTI = "readbypass-multi@example.com"


@pytest.fixture(scope="module")
def app():
    from app import create_app, db
    _app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    with _app.app_context():
        db.create_all()
    return _app


@pytest.fixture
def client(app):
    return app.test_client()


def _org(db, oid):
    from app.models import Organization
    org = db.session.get(Organization, oid)
    if not org:
        org = Organization(id=oid, name=f"ReadBypass Org {oid}",
                           slug=f"readbypass-org-{oid}", is_active=True)
        db.session.add(org)
        db.session.flush()
    return org


def _member(db, oid, identity, role="owner", active=True):
    """`owner` holds all permissions in this product (check_permission bypass)."""
    from app.models import OrgMember
    m = (db.session.query(OrgMember)
         .filter_by(organization_id=oid, identity_id=identity).first())
    if not m:
        m = OrgMember(organization_id=oid, identity_id=identity,
                      role=role, is_active=active)
        db.session.add(m)
    else:
        m.role = role
        m.is_active = active
    db.session.flush()
    return m


def _ws(db, oid, ws_id):
    from app.objects.legacy_models import Workspace
    w = db.session.get(Workspace, ws_id)
    if not w:
        w = Workspace(id=ws_id, name=ws_id, workspace_type="business",
                      status="active", created_by="readbypass_fixture",
                      organization_id=oid)
        db.session.add(w)
        db.session.flush()
    return w


def _ws_member(db, ws_id, identity, active=True):
    from app.objects.legacy_models import ShWorkspaceMembership
    m = (db.session.query(ShWorkspaceMembership)
         .filter_by(workspace_id=ws_id, identity_id=identity).first())
    if not m:
        m = ShWorkspaceMembership(workspace_id=ws_id, identity_id=identity,
                                  role="owner", is_active=active)
        db.session.add(m)
    else:
        m.is_active = active
    db.session.flush()
    return m


@pytest.fixture
def tenancy(app):
    """Idempotent canonical tenancy for the whole module."""
    from app import db
    with app.app_context():
        _org(db, ORG_A)
        _org(db, ORG_B)
        _ws(db, ORG_A, WS_A1)
        _ws(db, ORG_B, WS_B1)

        _member(db, ORG_A, ALICE)
        _ws_member(db, WS_A1, ALICE)

        _member(db, ORG_B, BOB)
        _ws_member(db, WS_B1, BOB)

        # NOBODY deliberately holds no membership rows at all.
        # MULTI is an active member of BOTH organizations (multi-org case).
        _member(db, ORG_A, MULTI)
        _member(db, ORG_B, MULTI)
        _ws_member(db, WS_A1, MULTI)
        _ws_member(db, WS_B1, MULTI)
        db.session.commit()
    yield


def _svc():
    from core.object_service import get_object_service
    return get_object_service()


def _seed_doc(org, ws, identity, name=None, object_type="Document"):
    """Create a canonical object for a tenant."""
    name = name or f"rb-doc-{uuid.uuid4().hex[:8]}.txt"
    return _svc().create(object_type=object_type, name=name,
                         organization_id=org, workspace_id=ws,
                         identity_id=identity, created_by=identity,
                         data={"name": name})


def _login(client, identity, org_id):
    with client.session_transaction() as sess:
        sess["identity_id"] = identity
        sess["user_id"] = identity
        sess["current_org_id"] = str(org_id)
        sess["_fresh"] = True
    return client


# ---------------------------------------------------------------------------
# A1 — events delta stream
# ---------------------------------------------------------------------------

class TestEventsDeltaIsScoped:
    def test_delta_excludes_another_tenant(self, app, tenancy):
        """The delta query returns only rows in the caller's authorized scope."""
        from app.events.routes import _get_delta_objects
        from datetime import datetime, timedelta, timezone
        with app.app_context():
            mine = _seed_doc(ORG_A, WS_A1, ALICE, name="rb-a1-event.txt")
            theirs = _seed_doc(ORG_B, WS_B1, BOB, name="rb-b1-event.txt")

            since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
            created, updated = _get_delta_objects(since, ORG_A, [WS_A1])
            names = {r.name for r in created} | {r.name for r in updated}
            assert "rb-a1-event.txt" in names
            assert "rb-b1-event.txt" not in names
            assert mine["id"] != theirs["id"]

    def test_delta_excludes_another_workspace_in_the_same_org(self, app, tenancy):
        from app.events.routes import _get_delta_objects
        from app import db
        from datetime import datetime, timedelta, timezone
        with app.app_context():
            _ws(db, ORG_A, "ws_rb_a2")
            _ws_member(db, "ws_rb_a2", ALICE)
            db.session.commit()
            _seed_doc(ORG_A, "ws_rb_a2", ALICE, name="rb-a2-event.txt")

            since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
            created, updated = _get_delta_objects(since, ORG_A, [WS_A1])
            names = {r.name for r in created} | {r.name for r in updated}
            assert "rb-a2-event.txt" not in names

    def test_http_events_denied_without_authorized_workspace(self, app, client, tenancy):
        """An identity with no authorized workspace is DENIED, not given a wide read."""
        _login(client, NOBODY, ORG_A)
        resp = client.get("/api/v1/events")
        # Denied by the canonical authorization layer. Which layer refuses first
        # depends on the caller's context: no active organization at all is
        # rejected by the permission gate (`no_active_organization`); an
        # organization with no authorized workspace reaches the route and is
        # refused by `_caller_scope()` (`no_authorized_workspace`). Both are
        # DENIALS; neither may be 200 or 5xx.
        assert resp.status_code == 403, resp.get_json()
        body = resp.get_json()
        assert body["success"] is False
        assert body["code"] in ("no_active_organization", "no_authorized_workspace")

    def test_http_events_denied_for_unauthenticated(self, app, client, tenancy):
        resp = client.get("/api/v1/events")
        assert resp.status_code in (401, 403)

    def test_http_events_owner_reaches_the_route(self, app, client, tenancy):
        """The owner path reaches the handler (so a 403 above is authorization)."""
        _login(client, ALICE, ORG_A)
        resp = client.get("/api/v1/events")
        assert resp.status_code == 200, resp.get_json()
        assert resp.get_json()["success"] is True

    def test_http_events_stream_denied_without_authorized_workspace(self, app, client, tenancy):
        _login(client, NOBODY, ORG_A)
        resp = client.get("/api/v1/events/stream")
        assert resp.status_code in (400, 403), resp.get_json()
        assert resp.get_json()["success"] is False


# ---------------------------------------------------------------------------
# A2 — upload Document listing
# ---------------------------------------------------------------------------

class TestUploadListingIsScoped:
    def test_listing_denied_without_authorized_workspace(self, app, client, tenancy):
        _login(client, NOBODY, ORG_A)
        resp = client.get("/api/v1/upload")
        assert resp.status_code in (400, 403), resp.get_json()
        assert resp.get_json()["success"] is False

    def test_listing_returns_only_the_callers_tenant(self, app, client, tenancy):
        with app.app_context():
            _seed_doc(ORG_A, WS_A1, ALICE, name="rb-list-a.txt")
            _seed_doc(ORG_B, WS_B1, BOB, name="rb-list-b.txt")
        _login(client, ALICE, ORG_A)
        resp = client.get("/api/v1/upload")
        assert resp.status_code == 200, resp.get_json()
        names = {row["name"] for row in resp.get_json()["data"]}
        assert "rb-list-a.txt" in names
        assert "rb-list-b.txt" not in names


# ---------------------------------------------------------------------------
# A4/A5/A6 — file manager: listing, delete and rename
# ---------------------------------------------------------------------------

class TestFileRoutesAuthorization:
    def test_list_requires_workspace_header(self, app, client, tenancy):
        _login(client, ALICE, ORG_A)
        resp = client.get("/api/v1/files")
        assert resp.status_code == 400

    def test_list_denies_another_tenants_workspace(self, app, client, tenancy):
        _login(client, ALICE, ORG_A)
        resp = client.get("/api/v1/files", headers={"X-Workspace-Id": WS_B1})
        assert resp.status_code == 403

    def test_list_returns_only_the_requested_authorized_workspace(self, app, client, tenancy):
        with app.app_context():
            # The file manager's canonical contract is object_type="document"
            # (the lowercase type written by the upload path).
            _seed_doc(ORG_A, WS_A1, ALICE, name="rb-file-a.txt",
                      object_type="document")
            _seed_doc(ORG_B, WS_B1, BOB, name="rb-file-b.txt",
                      object_type="document")
        _login(client, ALICE, ORG_A)
        resp = client.get("/api/v1/files", headers={"X-Workspace-Id": WS_A1})
        assert resp.status_code == 200, resp.get_json()
        names = {row["name"] for row in resp.get_json()["data"]["files"]}
        assert "rb-file-a.txt" in names
        assert "rb-file-b.txt" not in names

    def test_delete_denies_another_tenants_object(self, app, client, tenancy):
        with app.app_context():
            victim = _seed_doc(ORG_B, WS_B1, BOB, name="rb-delete-victim.txt")
            victim_id = victim["id"]
        _login(client, ALICE, ORG_A)
        resp = client.delete(f"/api/v1/files/{victim_id}")
        assert resp.status_code == 404
        with app.app_context():
            from app.objects.legacy_models import ShunyaObject
            row = ShunyaObject.query.get(victim_id)
            assert row is not None and row.is_deleted is False, \
                "an attacker must not be able to soft-delete another tenant's object"

    def test_delete_allows_the_owner(self, app, client, tenancy):
        with app.app_context():
            mine = _seed_doc(ORG_A, WS_A1, ALICE, name="rb-delete-mine.txt")
            mine_id = mine["id"]
        _login(client, ALICE, ORG_A)
        resp = client.delete(f"/api/v1/files/{mine_id}")
        assert resp.status_code == 200, resp.get_json()
        with app.app_context():
            from app.objects.legacy_models import ShunyaObject
            assert ShunyaObject.query.get(mine_id).is_deleted is True

    def test_rename_denies_another_tenants_object(self, app, client, tenancy):
        with app.app_context():
            victim = _seed_doc(ORG_B, WS_B1, BOB, name="rb-rename-victim.txt")
            victim_id = victim["id"]
        _login(client, ALICE, ORG_A)
        resp = client.patch(f"/api/v1/files/{victim_id}/rename",
                            json={"name": "pwned.txt"})
        assert resp.status_code == 404
        with app.app_context():
            from app.objects.legacy_models import ShunyaObject
            assert ShunyaObject.query.get(victim_id).name == "rb-rename-victim.txt"

    def test_identity_with_no_membership_is_denied(self, app, client, tenancy):
        with app.app_context():
            mine = _seed_doc(ORG_A, WS_A1, ALICE, name="rb-nobody.txt")
            mine_id = mine["id"]
        _login(client, NOBODY, ORG_A)
        assert client.get("/api/v1/files",
                          headers={"X-Workspace-Id": WS_A1}).status_code == 403
        # Denied before the object is even loaded (no authorized organization),
        # or 404 if it reached the object layer — never a success.
        assert client.delete(f"/api/v1/files/{mine_id}").status_code in (403, 404)


# ---------------------------------------------------------------------------
# A7/A8 — PDF rendering of another tenant's proposal / invoice
# ---------------------------------------------------------------------------

class TestPdfRoutesAuthorization:
    @staticmethod
    def _seed_typed(org, ws, identity, object_type, name):
        return _svc().create(object_type=object_type, name=name,
                             organization_id=org, workspace_id=ws,
                             identity_id=identity, created_by=identity,
                             data={"name": name})

    def test_proposal_denied_for_another_tenant(self, app, client, tenancy):
        with app.app_context():
            victim = self._seed_typed(ORG_B, WS_B1, BOB, "proposal",
                                      "rb-victim-proposal")
            victim_id = victim["id"]
        _login(client, ALICE, ORG_A)
        resp = client.get(f"/api/v1/pdf/proposal/{victim_id}")
        assert resp.status_code == 404, \
            "another tenant's proposal must not be renderable"

    def test_invoice_denied_for_another_tenant(self, app, client, tenancy):
        with app.app_context():
            victim = self._seed_typed(ORG_B, WS_B1, BOB, "invoice",
                                      "rb-victim-invoice")
            victim_id = victim["id"]
        _login(client, ALICE, ORG_A)
        resp = client.get(f"/api/v1/pdf/invoice/{victim_id}")
        assert resp.status_code == 404

    def test_proposal_denied_for_identity_with_no_membership(self, app, client, tenancy):
        with app.app_context():
            mine = self._seed_typed(ORG_A, WS_A1, ALICE, "proposal",
                                    "rb-alice-proposal")
            mine_id = mine["id"]
        _login(client, NOBODY, ORG_A)
        resp = client.get(f"/api/v1/pdf/proposal/{mine_id}")
        assert resp.status_code == 404

    def test_missing_object_is_404_not_500(self, app, client, tenancy):
        _login(client, ALICE, ORG_A)
        assert client.get("/api/v1/pdf/invoice/99999999").status_code == 404


# ---------------------------------------------------------------------------
# A3 — upload dedup probe must not see another tenant's document
# ---------------------------------------------------------------------------

class _Storage:
    @staticmethod
    def save(file_bytes, filename, content_type):
        return {"url": f"mem://{filename}", "size": len(file_bytes)}


class _Job:
    def __init__(self):
        self.stages = []

    def update(self, **kw):
        self.stages.append(kw)


@pytest.fixture
def upload_worker(app, monkeypatch, tenancy):
    import app.upload.routes as up
    monkeypatch.setattr("app.create_app", lambda *a, **k: app)
    monkeypatch.setattr(up, "resolve_storage_provider", lambda: _Storage())
    return up


class TestUploadDedupIsScoped:
    def test_same_workspace_duplicate_is_detected(self, app, upload_worker, tenancy):
        payload = b"r6b27-readbypass-dedup-bytes-v1"
        upload_worker._process_upload(_Job(), payload, "rb-dedup.txt",
                                      "text/plain", ORG_A, WS_A1, ALICE)
        with app.app_context():
            before = _svc().count_by_type(ORG_A, identity_id=ALICE).get("Document", 0)
        upload_worker._process_upload(_Job(), payload, "rb-dedup.txt",
                                      "text/plain", ORG_A, WS_A1, ALICE)
        with app.app_context():
            after = _svc().count_by_type(ORG_A, identity_id=ALICE).get("Document", 0)
            assert after == before, "a same-tenant, same-workspace duplicate must be skipped"

    def test_identical_bytes_in_another_tenant_are_not_a_duplicate(self, app, upload_worker, tenancy):
        """Existence of another tenant's identical document must not leak, and
        must not suppress this tenant's own upload."""
        payload = b"r6b27-readbypass-dedup-bytes-v2"
        upload_worker._process_upload(_Job(), payload, "rb-dedup-b.txt",
                                      "text/plain", ORG_B, WS_B1, BOB)
        with app.app_context():
            bob_before = _svc().count_by_type(ORG_B, identity_id=BOB).get("Document", 0)

        upload_worker._process_upload(_Job(), payload, "rb-dedup-b.txt",
                                      "text/plain", ORG_A, WS_A1, ALICE)
        with app.app_context():
            alice_docs = _svc().get_by_type("Document", ORG_A, identity_id=ALICE)
            assert any(d["name"] == "rb-dedup-b.txt" for d in alice_docs), \
                "another tenant's identical file must not suppress this upload"
            assert _svc().count_by_type(ORG_B, identity_id=BOB).get("Document", 0) == bob_before


# ---------------------------------------------------------------------------
# A12 — POST /api/v1/upload must write through ObjectService with real ownership
# ---------------------------------------------------------------------------

class TestObjectsUploadWriteBoundary:
    @staticmethod
    def _post(client, identity, ws_id, filename="rb-upload.txt", body=b"rb-bytes"):
        import io
        data = {"file": (io.BytesIO(body), filename)}
        headers = {"X-Identity-Id": identity, "X-Workspace-Id": ws_id}
        return client.post("/api/v1/upload", data=data,
                           headers=headers, content_type="multipart/form-data")

    def test_upload_writes_a_canonical_object_with_organization(self, app, client, tenancy):
        resp = self._post(client, ALICE, WS_A1, filename="rb-upload-ok.txt")
        assert resp.status_code == 201, resp.get_json()
        with app.app_context():
            rows = _svc().list_by_workspace(WS_A1, ORG_A, identity_id=ALICE)
            mine = [r for r in rows if r["name"] == "rb-upload-ok.txt"]
            assert mine, "the upload must appear in the canonical store"
            assert mine[0]["organization_id"] == ORG_A, \
                "the upload must carry its owning organization, never NULL"
            assert mine[0]["workspace_id"] == WS_A1

    def test_upload_into_an_unauthorized_workspace_is_refused(self, app, client, tenancy):
        resp = self._post(client, ALICE, WS_B1, filename="rb-upload-cross.txt")
        assert resp.status_code in (400, 403), resp.get_json()
        with app.app_context():
            from app.objects.legacy_models import ShunyaObject
            assert ShunyaObject.query.filter_by(name="rb-upload-cross.txt").count() == 0

    def test_upload_without_membership_is_refused(self, app, client, tenancy):
        resp = self._post(client, NOBODY, WS_A1, filename="rb-upload-nobody.txt")
        assert resp.status_code in (400, 403), resp.get_json()
        with app.app_context():
            from app.objects.legacy_models import ShunyaObject
            assert ShunyaObject.query.filter_by(name="rb-upload-nobody.txt").count() == 0

    def test_no_sh_objects_row_is_ever_written_without_organization(self, app, client, tenancy):
        """Structural invariant: the legacy NULL-organization write is gone."""
        self._post(client, ALICE, WS_A1, filename="rb-upload-owner.txt")
        with app.app_context():
            from app.objects.legacy_models import ShunyaObject
            orphans = ShunyaObject.query.filter(
                ShunyaObject.name.like("rb-upload-%"),
                ShunyaObject.organization_id == None,  # noqa: E711
            ).count()
            assert orphans == 0


class TestOrgResolutionDenialCodes:
    """The RBAC decorator's organization resolution must distinguish a client
    error from an AUTHORIZATION denial (R6B-2.7 Window 6).

    Before this change the decorator returned `400 No organization selected` in
    every failure case, so a genuine denial looked like a malformed request.
    """

    @staticmethod
    def _resolve(app, identity, session_org=None):
        """(org_id, denial_code) as the decorator would compute it."""
        from flask import session
        from app.authz.decorators import _resolve_org_or_denial
        with app.test_request_context("/api/v1/_probe"):
            if session_org is not None:
                session["current_org_id"] = session_org
            return _resolve_org_or_denial(identity)

    def test_single_active_organization_resolves(self, app, tenancy):
        with app.app_context():
            org_id, denial = self._resolve(app, ALICE)
            assert (org_id, denial) == (ORG_A, None)

    def test_explicit_selection_of_a_real_membership_resolves(self, app, tenancy):
        with app.app_context():
            assert self._resolve(app, MULTI, ORG_A) == (ORG_A, None)
            assert self._resolve(app, MULTI, ORG_B) == (ORG_B, None)

    def test_multiple_organizations_without_selection_is_a_client_error(self, app, tenancy):
        """Ambiguity the client can resolve → 400, not a denial."""
        with app.app_context():
            org_id, denial = self._resolve(app, MULTI)
            assert org_id is None
            assert denial == "organization_selection_required"

    def test_no_active_membership_is_a_denial(self, app, tenancy):
        with app.app_context():
            org_id, denial = self._resolve(app, NOBODY)
            assert org_id is None
            assert denial == "no_active_organization"

    def test_selecting_another_identitys_organization_is_a_denial(self, app, tenancy):
        """alice is a member of ORG_A only; presenting ORG_B must be DENIED."""
        with app.app_context():
            org_id, denial = self._resolve(app, ALICE, ORG_B)
            assert org_id is None
            assert denial == "organization_not_authorized"

    def test_denial_codes_are_not_treated_as_client_errors(self):
        """The selection-required set must never include a denial code."""
        from app.authz.decorators import _SELECTION_REQUIRED_CODES
        assert "no_active_organization" not in _SELECTION_REQUIRED_CODES
        assert "organization_not_authorized" not in _SELECTION_REQUIRED_CODES
        assert _SELECTION_REQUIRED_CODES == {
            "organization_selection_required", "invalid_requested_organization",
        }


# ---------------------------------------------------------------------------
# A9/A10/A11 — intelligence service object read + aggregates
# ---------------------------------------------------------------------------

class TestIntelligenceTenantScoping:
    """`object_id` is not a capability, and an aggregate is not tenant-free."""

    @staticmethod
    def _request(tenant_id, object_id=""):
        from core.intelligence import IntelligenceRequest
        return IntelligenceRequest(
            tenant_id=tenant_id,
            context_object_id=object_id,
            context_object_type="invoice" if object_id else "",
            question="how many objects are there",
        )

    def test_object_context_requires_a_positive_tenant(self, app, tenancy):
        from core.intelligence.service import IntelligenceService
        with app.app_context():
            victim = _seed_doc(ORG_B, WS_B1, BOB, name="rb-intel-victim.txt")
            svc = IntelligenceService()

            # tenant_id=0 must not read the object at all.
            no_tenant = svc._retrieve_company_context(
                self._request(0, victim["object_id"]))
            assert all("rb-intel-victim" not in (s.detail or "")
                       for s in no_tenant), \
                "an object must never be read without a tenant"

            # A positive but WRONG tenant must not see it either.
            wrong_tenant = svc._retrieve_company_context(
                self._request(ORG_A, victim["object_id"]))
            assert all("rb-intel-victim" not in (s.detail or "")
                       for s in wrong_tenant), \
                "another tenant's object must not be readable by object_id"

            # The owning tenant still resolves it.
            owner = svc._retrieve_company_context(
                self._request(ORG_B, victim["object_id"]))
            assert any("rb-intel-victim" in (s.detail or "") for s in owner), \
                "the owning tenant must still see its own object"

    def test_aggregate_fails_closed_without_a_tenant(self, app, tenancy):
        from core.intelligence.service import IntelligenceService
        with app.app_context():
            _seed_doc(ORG_B, WS_B1, BOB, name="rb-intel-count.txt")
            svc = IntelligenceService()
            assert svc._deterministic_compute(self._request(0), []) is None, \
                "an aggregate must not be computed across all tenants"

    def test_aggregate_counts_only_the_requesting_tenant(self, app, tenancy):
        """Another tenant's new object must not change this tenant's aggregate."""
        from core.intelligence.service import IntelligenceService
        with app.app_context():
            svc = IntelligenceService()
            before = svc._deterministic_compute(self._request(ORG_A), [])
            assert before is not None
            before_count = before["result"]["by_type"].get("Document", 0)

            _seed_doc(ORG_B, WS_B1, BOB, name="rb-intel-count-b.txt")

            after = svc._deterministic_compute(self._request(ORG_A), [])
            after_count = after["result"]["by_type"].get("Document", 0)
            assert after_count == before_count, \
                "the aggregate must count only the requesting tenant's objects"
