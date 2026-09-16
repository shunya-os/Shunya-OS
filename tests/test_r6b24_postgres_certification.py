"""R6B-2.4 — PostgreSQL certification against a DISPOSABLE cluster.

Runs only when DATABASE_URL points at PostgreSQL (the disposable
certification cluster provisioned for R6B-2.4). Never touches production.

Covers: object creation, canonical reads, update, delete, organization
isolation, workspace isolation, cross-tenant denial, missing/invalid org
denial, AI context isolation through the canonical intelligence route,
execution/evidence persistence, transaction behaviour, concurrent writes,
RBAC, and (optionally) restart persistence via a pre-restart marker.
"""
from __future__ import annotations

import os
import threading
import uuid

import pytest

PG_URL = os.environ.get("DATABASE_URL", "")
IS_PG = PG_URL.startswith("postgresql")

pytestmark = pytest.mark.skipif(
    not IS_PG,
    reason="PostgreSQL certification requires DATABASE_URL=postgresql://... (disposable cluster)",
)

# Two distinct, high, non-production organisation ids for this certification.
ORG_A = 770101
ORG_B = 770202
WS_A = "cert_ws_a"
WS_B = "cert_ws_b"


@pytest.fixture(scope="module")
def app():
    from app import create_app, db

    application = create_app(config_override={
        "TESTING": True,
        "DISABLE_RATE_LIMIT": "true",
        "SECRET_KEY": "r6b24-cert-secret",
        "WTF_CSRF_ENABLED": False,
    })
    # Prove we are on PostgreSQL before any certification assertion.
    with application.app_context():
        assert db.engine.dialect.name == "postgresql", \
            f"certification must run on PostgreSQL, got {db.engine.dialect.name}"
        db.create_all()
    yield application


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture(scope="module", autouse=True)
def _cert_fixtures(app):
    """Canonical organisations, workspaces and memberships for certification."""
    from app import db
    from app.models import Organization, OrgMember
    from app.authz.services import seed_default_roles
    from sqlalchemy import text

    with app.app_context():
        for org_id, slug in ((ORG_A, "cert-org-a"), (ORG_B, "cert-org-b")):
            org = db.session.get(Organization, org_id)
            if not org:
                db.session.add(Organization(id=org_id, name=f"Cert Org {org_id}", slug=slug))
                db.session.commit()
            seed_default_roles(org_id)
            om = OrgMember.query.filter_by(organization_id=org_id,
                                           identity_id=f"cert-user-{org_id}").first()
            if not om:
                db.session.add(OrgMember(organization_id=org_id,
                                         identity_id=f"cert-user-{org_id}",
                                         role="owner", is_active=True))
                db.session.commit()

        # Canonical workspaces owned by each organisation (sh_workspaces).
        for ws_id, org_id in ((WS_A, ORG_A), (WS_B, ORG_B)):
            db.session.execute(
                text("INSERT INTO sh_workspaces (id, name, workspace_type, status, "
                     "created_by, organization_id, created_at, updated_at) "
                     "VALUES (:id, :name, 'business', 'active', 'cert', :org, NOW(), NOW()) "
                     "ON CONFLICT (id) DO UPDATE SET organization_id = EXCLUDED.organization_id"),
                {"id": ws_id, "name": f"Cert Workspace {ws_id}", "org": org_id},
            )
        db.session.commit()
    yield


def _svc():
    from core.object_service import get_object_service
    return get_object_service()


def _raw_scalar(app, sql, params=None):
    from app import db
    from sqlalchemy import text
    with app.app_context():
        return db.session.execute(text(sql), params or {}).scalar()


# ---------------------------------------------------------------------------
# Object lifecycle on PostgreSQL
# ---------------------------------------------------------------------------

def test_object_create_and_canonical_read(app):
    """Created object is readable from sh_objects with exact field values."""
    with app.app_context():
        obj = _svc().create(object_type="cert_doc", name="Cert Object A",
                            organization_id=ORG_A, workspace_id=WS_A,
                            created_by="cert-user-770101")
        assert obj["id"] > 0
        assert obj["organization_id"] == ORG_A

        read = _svc().get(obj["id"], organization_id=ORG_A)
        assert read is not None, "canonical read must find the row in PostgreSQL"
        assert read["name"] == "Cert Object A"
        assert read["object_type"] == "cert_doc"
        assert read["organization_id"] == ORG_A
        assert read["workspace_id"] == WS_A
        assert read["status"] == "active"

        # persisted, not merely returned
        count = _raw_scalar(app, "SELECT count(*) FROM sh_objects WHERE id = :i", {"i": obj["id"]})
        assert count == 1


def test_object_update_persists(app):
    """update() writes through to sh_objects and the change is re-readable."""
    with app.app_context():
        obj = _svc().create(object_type="cert_doc", name="Before Update",
                            organization_id=ORG_A, workspace_id=WS_A)
        assert _svc().update(obj["id"], ORG_A, name="After Update") is True
        read = _svc().get(obj["id"], organization_id=ORG_A)
        assert read["name"] == "After Update"
        persisted = _raw_scalar(app, "SELECT name FROM sh_objects WHERE id = :i", {"i": obj["id"]})
        assert persisted == "After Update"


def test_object_delete_is_soft_and_persisted(app):
    """delete() archives (soft) and the archived state is persisted."""
    with app.app_context():
        obj = _svc().create(object_type="cert_doc", name="To Delete",
                            organization_id=ORG_A, workspace_id=WS_A)
        assert _svc().delete(obj["id"], organization_id=ORG_A) is True
        read = _svc().get(obj["id"], organization_id=ORG_A)
        assert read["status"] == "archived"
        assert _raw_scalar(app, "SELECT status FROM sh_objects WHERE id = :i",
                           {"i": obj["id"]}) == "archived"
        # row retained — soft delete, not a destructive delete
        assert _raw_scalar(app, "SELECT count(*) FROM sh_objects WHERE id = :i",
                           {"i": obj["id"]}) == 1


# ---------------------------------------------------------------------------
# Isolation and denial
# ---------------------------------------------------------------------------

def test_organization_isolation_search_and_read(app):
    """An object owned by ORG_A is invisible to ORG_B."""
    with app.app_context():
        obj = _svc().create(object_type="cert_secret", name=f"OrgA Secret {uuid.uuid4().hex[:6]}",
                            organization_id=ORG_A, workspace_id=WS_A)
        same_org = _svc().search("OrgA Secret", organization_id=ORG_A)
        assert any(r["id"] == obj["id"] for r in same_org), "owner org must find its object"

        other_org = _svc().search("OrgA Secret", organization_id=ORG_B)
        assert not any(r["id"] == obj["id"] for r in other_org), "other org must not find it"

        assert _svc().get(obj["id"], organization_id=ORG_B) is None
        assert _svc().get(obj["id"], organization_id=ORG_A) is not None


def test_workspace_isolation(app):
    """list_by_workspace returns only objects of the requested workspace."""
    with app.app_context():
        a = _svc().create(object_type="cert_doc", name="WS-A Object",
                          organization_id=ORG_A, workspace_id=WS_A)
        b = _svc().create(object_type="cert_doc", name="WS-B Object",
                          organization_id=ORG_B, workspace_id=WS_B)
        rows_a = _svc().list_by_workspace(workspace_id=WS_A, organization_id=ORG_A, status="active")
        ids_a = {r["id"] for r in rows_a}
        assert a["id"] in ids_a
        assert b["id"] not in ids_a, "workspace A must not expose workspace B objects"

        rows_b = _svc().list_by_workspace(workspace_id=WS_B, organization_id=ORG_B, status="active")
        ids_b = {r["id"] for r in rows_b}
        assert b["id"] in ids_b
        assert a["id"] not in ids_b


def test_cross_tenant_update_and_delete_denied(app):
    """Writes scoped to the wrong organisation fail closed."""
    with app.app_context():
        obj = _svc().create(object_type="cert_doc", name="Cross Tenant Target",
                            organization_id=ORG_A, workspace_id=WS_A)
        assert _svc().update(obj["id"], ORG_B, name="hijacked") is False
        assert _svc().delete(obj["id"], organization_id=ORG_B) is False
        read = _svc().get(obj["id"], organization_id=ORG_A)
        assert read["name"] == "Cross Tenant Target"
        assert read["status"] == "active"


def test_missing_org_denial(app):
    """Missing ownership fails closed — no synthetic organisation is invented."""
    with app.app_context():
        with pytest.raises(ValueError):
            _svc().create(object_type="cert_doc", name="No Org", organization_id=0)
        with pytest.raises(ValueError):
            _svc().create(object_type="cert_doc", name="No Org", organization_id=None)

        obj = _svc().create(object_type="cert_doc", name="Org Owned",
                            organization_id=ORG_A, workspace_id=WS_A)
        # An unscoped read cannot manufacture ownership of an org-owned row.
        assert _svc().get(obj["id"]) is None
        assert _svc().get(obj["id"], organization_id=0) is None


def test_invalid_org_denial(app):
    """A non-existent organisation yields no object and no write."""
    with app.app_context():
        obj = _svc().create(object_type="cert_doc", name="Invalid Org Target",
                            organization_id=ORG_A, workspace_id=WS_A)
        assert _svc().get(obj["id"], organization_id=999999) is None
        assert _svc().update(obj["id"], 999999, name="nope") is False
        assert _svc().delete(obj["id"], organization_id=999999) is False
        assert _svc().get(obj["id"], organization_id=ORG_A)["name"] == "Invalid Org Target"


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------

def test_rbac_owner_allowed_nonmember_denied(app):
    from app.authz.services import check_permission
    with app.app_context():
        assert check_permission(ORG_A, f"cert-user-{ORG_A}", "ai.use") is True
        assert check_permission(ORG_A, "cert-outsider", "ai.use") is False
        assert check_permission(ORG_B, f"cert-user-{ORG_A}", "ai.use") is False


# ---------------------------------------------------------------------------
# AI context isolation through the canonical intelligence route
# ---------------------------------------------------------------------------

def _seed_ai_context(app, org_id, identity_id, object_name):
    from app import db
    from app.models import OrgMember
    with app.app_context():
        om = OrgMember.query.filter_by(organization_id=org_id, identity_id=identity_id).first()
        if not om:
            db.session.add(OrgMember(organization_id=org_id, identity_id=identity_id,
                                     role="owner", is_active=True))
            db.session.commit()
        obj = _svc().create(object_type="cert_invoice", name=object_name,
                            organization_id=org_id, workspace_id=WS_A, created_by=identity_id)
        db.session.commit()
        return obj["id"]


def test_ai_context_isolation_through_intelligence_route(app, client):
    """Each tenant's /api/v1/intelligence/ask sees only its own company evidence."""
    identity_a = f"cert-ai-{ORG_A}"
    identity_b = f"cert-ai-{ORG_B}"
    name_a = f"OrgA Invoice {uuid.uuid4().hex[:6]}"
    name_b = f"OrgB Invoice {uuid.uuid4().hex[:6]}"

    _seed_ai_context(app, ORG_A, identity_a, name_a)
    _seed_ai_context(app, ORG_B, identity_b, name_b)

    def _ask(identity_id, org_id):
        with client.session_transaction() as sess:
            sess["user_id"] = identity_id
            sess["identity_id"] = identity_id
            sess["current_org_id"] = org_id
            sess["_fresh"] = True
        resp = client.post("/api/v1/intelligence/ask", json={"question": "What is in our books?"})
        assert resp.status_code == 200, f"ask failed: {resp.status_code} {resp.get_json()}"
        return resp.get_json()

    data_a = _ask(identity_a, ORG_A)
    data_b = _ask(identity_b, ORG_B)

    assert data_a["tenant"]["tenant_id"] == str(ORG_A)
    assert data_b["tenant"]["tenant_id"] == str(ORG_B)

    blob_a = str(data_a.get("evidence_used", []))
    blob_b = str(data_b.get("evidence_used", []))

    assert name_a in blob_a, "tenant A must see its own canonical object evidence"
    assert name_b not in blob_a, "tenant A must NOT see tenant B's object evidence"
    assert name_b in blob_b, "tenant B must see its own canonical object evidence"
    assert name_a not in blob_b, "tenant B must NOT see tenant A's object evidence"

    # no organisation context → no cross-tenant evidence is assembled
    with client.session_transaction() as sess:
        sess["user_id"] = identity_a
        sess["identity_id"] = identity_a
        sess.pop("current_org_id", None)
        sess.pop("tenant_id", None)
        sess["_fresh"] = True
    resp_none = client.post("/api/v1/intelligence/ask",
                            json={"question": "What is in our books?", "action": "create_task"})
    body_none = resp_none.get_json() or {}
    assert resp_none.status_code == 403, (
        "missing canonical org context must fail closed for execution, got "
        f"{resp_none.status_code}"
    )
    assert name_a not in str(body_none.get("evidence_used", []))
    assert name_b not in str(body_none.get("evidence_used", []))


# ---------------------------------------------------------------------------
# Execution / evidence persistence, transactions, concurrency
# ---------------------------------------------------------------------------

def test_execution_evidence_and_outcome_persist(app):
    """Execution-spine rows written through the ORM are persisted in PostgreSQL."""
    from app import db
    from app.evidence.models_db import EvidenceRecord
    from app.execution.models import Outcome

    marker = uuid.uuid4().hex[:8]
    with app.app_context():
        db.session.add(EvidenceRecord(source_type="certification",
                                      source_id=f"r6b24-{marker}",
                                      raw_reference={"cert": True, "org": ORG_A}))
        outcome = Outcome(
            outcome_id=f"cert-outcome-{marker}",
            identity_id=f"cert-user-{ORG_A}",
            intention="R6B-2.4 PostgreSQL certification",
            state={"cert": True, "org": ORG_A},
        )
        db.session.add(outcome)
        db.session.commit()
        outcome_id = getattr(outcome, "id", None)

    assert _raw_scalar(app, "SELECT count(*) FROM evidence_records WHERE source_id = :s",
                       {"s": f"r6b24-{marker}"}) == 1
    assert outcome_id is not None
    assert _raw_scalar(app, "SELECT count(*) FROM sh_outcomes WHERE outcome_id = :o",
                       {"o": f"cert-outcome-{marker}"}) == 1


def test_transaction_rollback_leaves_no_partial_row(app):
    from app import db
    from app.evidence.models_db import EvidenceRecord

    marker = uuid.uuid4().hex[:8]
    with app.app_context():
        try:
            db.session.add(EvidenceRecord(source_type="certification",
                                          source_id=f"rollback-{marker}",
                                          raw_reference={}))
            db.session.flush()
            raise RuntimeError("forced rollback for transaction certification")
        except RuntimeError:
            db.session.rollback()

    assert _raw_scalar(app, "SELECT count(*) FROM evidence_records WHERE source_id = :s",
                       {"s": f"rollback-{marker}"}) == 0


def test_concurrent_object_creation(app):
    """Concurrent writers each persist a distinct row (real PG concurrency)."""
    created = []
    errors = []
    lock = threading.Lock()

    def worker(idx):
        try:
            with app.app_context():
                obj = _svc().create(object_type="cert_concurrent",
                                    name=f"Concurrent {idx}", organization_id=ORG_A,
                                    workspace_id=WS_A)
                with lock:
                    created.append(obj["id"])
        except Exception as exc:  # pragma: no cover - reported below
            with lock:
                errors.append(repr(exc))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert not errors, f"concurrent writers failed: {errors}"
    assert len(created) == 8
    assert len(set(created)) == 8, "concurrent inserts must produce distinct rows"
    count = _raw_scalar(app, "SELECT count(*) FROM sh_objects WHERE id = ANY(:ids)",
                        {"ids": created})
    assert count == 8, "all concurrent rows must be persisted"


# ---------------------------------------------------------------------------
# Restart persistence (marker written before the cluster restart)
# ---------------------------------------------------------------------------

def test_restart_persistence_marker(app):
    """A row written before the cluster restart is still readable after it."""
    marker = os.environ.get("R6B24_RESTART_MARKER")
    if not marker:
        pytest.skip("R6B24_RESTART_MARKER not set — restart persistence verified separately")
    with app.app_context():
        row = _svc().get_by_object_id(marker, organization_id=ORG_A)
        assert row is not None, f"object {marker} did not survive the PostgreSQL restart"
        assert row["name"] == "Restart Survivor"
        assert row["organization_id"] == ORG_A
