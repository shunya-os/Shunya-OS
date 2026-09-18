"""Canonical object READ surfaces — GET /api/v1/objects{,/types,/<type>}.

Regression coverage for a real product defect: the frontend has always read
these paths (workspace domain counts, knowledge browser, living store, settings
export, search) but only POST was mounted, so every read failed with 405/404 and
the workspace displayed a FALSE EMPTY STATE — it told the human there was no
data when data existed.

These tests exercise the REAL HTTP routes through the canonical authorization
boundary. Tenancy is built explicitly and minimally — a real Organization, a
real canonical Workspace, real membership rows, real canonical objects. No
synthetic organization, no arbitrary workspace selection, no system_scope.
"""
import pytest

ORG_R1 = 801
ORG_R2 = 802
ORG_R3 = 803

WS_R1 = "ws_read_r1"
WS_R2 = "ws_read_r2"
WS_R3 = "ws_read_r3"

OWNER = "read-owner@example.com"
OTHER = "read-other@example.com"
UNJOINED = "read-unjoined@example.com"


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
        org = Organization(id=oid, name=f"Read Org {oid}",
                           slug=f"read-org-{oid}", is_active=True)
        db.session.add(org)
        db.session.flush()
    return org


def _member(db, oid, identity, role="owner", active=True):
    from app.models import OrgMember
    m = (db.session.query(OrgMember)
         .filter_by(organization_id=oid, identity_id=identity).first())
    if not m:
        m = OrgMember(organization_id=oid, identity_id=identity,
                      role=role, is_active=active)
        db.session.add(m)
    else:
        m.role, m.is_active = role, active
    db.session.flush()
    return m


def _ws(db, oid, ws_id):
    from app.objects.legacy_models import Workspace
    w = db.session.get(Workspace, ws_id)
    if not w:
        w = Workspace(id=ws_id, name=ws_id, workspace_type="business",
                      status="active", created_by="read_fixture",
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
    """Identities: OWNER (org 801/ws_r1), OTHER (org 802/ws_r2),
    UNJOINED (member of org 803 but authorized for no workspace)."""
    from app import db
    with app.app_context():
        _org(db, ORG_R1)
        _org(db, ORG_R2)
        _org(db, ORG_R3)
        _ws(db, ORG_R1, WS_R1)
        _ws(db, ORG_R2, WS_R2)
        _ws(db, ORG_R3, WS_R3)

        _member(db, ORG_R1, OWNER)
        _ws_member(db, WS_R1, OWNER)

        _member(db, ORG_R2, OTHER)
        _ws_member(db, WS_R2, OTHER)

        # UNJOINED belongs to org 803 but holds NO workspace membership
        _member(db, ORG_R3, UNJOINED)

        # Canonical objects — created through the canonical service only.
        # Seeding is idempotent: the fixture is function-scoped (the app is
        # module-scoped), so without this guard each test would add another copy
        # and the exact-count assertions below would be meaningless.
        from core.object_service import get_object_service
        svc = get_object_service()

        if not svc.count_by_type(organization_id=ORG_R1, identity_id=OWNER):
            for object_type, name in (
                ("customer", "Bali Retreat Customer"),
                ("customer", "Second Customer"),
                ("document", "Bali Itinerary PDF"),
            ):
                svc.create(object_type=object_type, name=name,
                           organization_id=ORG_R1,
                           data={"name": name, "type": object_type},
                           created_by=OWNER, workspace_id=WS_R1, identity_id=OWNER)

        if not svc.count_by_type(organization_id=ORG_R2, identity_id=OTHER):
            svc.create(object_type="customer", name="Other Org Customer",
                       organization_id=ORG_R2,
                       data={"name": "Other Org Customer", "type": "customer"},
                       created_by=OTHER, workspace_id=WS_R2, identity_id=OTHER)

        db.session.commit()
    yield


def _session_client(client, identity, org_id):
    with client.session_transaction() as sess:
        sess["identity_id"] = identity
        sess["user_id"] = identity
        sess["current_org_id"] = str(org_id)
        sess["_fresh"] = True
    return client


def _owner_client(client, tenancy):
    return _session_client(client, OWNER, ORG_R1)


# ---------------------------------------------------------------------------
# The defect: these paths answered 405/404
# ---------------------------------------------------------------------------


def test_types_route_answers_get_not_405(client, tenancy):
    resp = _owner_client(client, tenancy).get("/api/v1/objects/types")
    assert resp.status_code == 200, resp.get_data(as_text=True)[:300]
    assert resp.get_json()["success"] is True


def test_collection_route_answers_get_not_404(client, tenancy):
    resp = _owner_client(client, tenancy).get("/api/v1/objects?limit=1000")
    assert resp.status_code == 200, resp.get_data(as_text=True)[:300]


def test_typed_route_answers_get_not_405(client, tenancy):
    resp = _owner_client(client, tenancy).get("/api/v1/objects/customer")
    assert resp.status_code == 200, resp.get_data(as_text=True)[:300]


# ---------------------------------------------------------------------------
# Truthful data (the false empty state)
# ---------------------------------------------------------------------------


def test_types_inventory_reports_real_counts(client, tenancy):
    """The shape the workspace/knowledge-browser/living-store parse: data[type]."""
    body = _owner_client(client, tenancy).get("/api/v1/objects/types").get_json()
    assert body["success"] is True
    data = body["data"]
    assert data.get("customer") == 2, data
    assert data.get("document") == 1, data
    # A domain DOES have data — the defect was reporting none.
    assert body["total"] == 3


def test_list_by_type_returns_objects_with_exact_total(client, tenancy):
    body = _owner_client(client, tenancy).get(
        "/api/v1/objects/customer?limit=100").get_json()
    assert body["success"] is True
    payload = body["data"]
    assert isinstance(payload["objects"], list)
    assert len(payload["objects"]) == 2
    # exact canonical count for the type, not len(page)
    assert payload["total"] == 2
    assert payload["per_page"] == 100
    assert payload["has_more"] is False
    assert {o["name"] for o in payload["objects"]} == {
        "Bali Retreat Customer", "Second Customer"}
    # both shapes the different consumers read
    assert body["objects"] == payload["objects"]
    assert body["total"] == 2


def test_collection_lists_all_authorized_objects(client, tenancy):
    body = _owner_client(client, tenancy).get(
        "/api/v1/objects?limit=1000").get_json()
    # search surface expects data to be an array
    assert isinstance(body["data"], list)
    # export surface expects a top-level objects key
    assert isinstance(body["objects"], list)
    types = {o["object_type"] for o in body["data"]}
    assert types == {"customer", "document"}
    assert len(body["data"]) == 3


def test_collection_search_filters_by_name(client, tenancy):
    body = _owner_client(client, tenancy).get(
        "/api/v1/objects?q=Bali").get_json()
    assert body["success"] is True
    names = {o["name"] for o in body["data"]}
    # name-matched only: both "Bali ..." objects, and the non-matching one excluded
    assert names == {"Bali Itinerary PDF", "Bali Retreat Customer"}, names
    # a query that matches nothing returns an empty list, not everything
    none_body = _owner_client(client, tenancy).get(
        "/api/v1/objects?q=zzz-no-such-object").get_json()
    assert none_body["data"] == []


def test_limit_is_capped(client, tenancy):
    body = _owner_client(client, tenancy).get(
        "/api/v1/objects/customer?limit=99999").get_json()
    assert body["data"]["per_page"] <= 500


# ---------------------------------------------------------------------------
# Authorization (the reason this is a backend concern, not a UI concern)
# ---------------------------------------------------------------------------


def test_other_organization_never_sees_this_workspace(client, tenancy):
    other = _session_client(client, OTHER, ORG_R2)
    types = other.get("/api/v1/objects/types").get_json()["data"]
    assert types.get("customer") == 1, types  # only their own

    listed = other.get("/api/v1/objects/customer").get_json()
    names = [o["name"] for o in listed["data"]["objects"]]
    assert names == ["Other Org Customer"], names

    everything = other.get("/api/v1/objects?limit=1000").get_json()["data"]
    assert {o["name"] for o in everything} == {"Other Org Customer"}


def test_unauthenticated_reads_are_401(client, tenancy):
    for path in ("/api/v1/objects/types", "/api/v1/objects/customer",
                 "/api/v1/objects?limit=10"):
        resp = client.get(path)
        assert resp.status_code == 401, (path, resp.status_code)


def test_membership_without_workspace_fails_closed(client, tenancy):
    """No authorized workspace must NOT read as 'empty data' — it is a denial."""
    unjoined = _session_client(client, UNJOINED, ORG_R3)
    resp = unjoined.get("/api/v1/objects/types")
    assert resp.status_code in (400, 403), resp.get_data(as_text=True)[:200]
    assert resp.status_code != 200
