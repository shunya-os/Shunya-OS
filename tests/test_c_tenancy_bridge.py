"""C-stage — canonical tenancy bridge: readers accept organization + legacy id.

Observed live on 2026-10-09: the founder's documents carried tenant_id = 89
(legacy tenants row "Panchi Club") while the canonical organization is 7
(organizations row "Panchi Club"). The workspace Documents list (legacy-first
resolution) showed them; manual classification through the canonical document
API returned 404 for a document the same human could see. The fix: one scope
resolver (authz.workspace_context.resolve_tenant_scope) returns the canonical
organization plus the recorded legacy bridge (organizations.legacy_tenant_id),
and every document reader accepts the union while writers move toward the
canonical id.
"""

import io

import pytest


@pytest.fixture(scope="function")
def app():
    from app import create_app, db
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
        "DISABLE_RATE_LIMIT": True,
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def seeded(client):
    """Org 989 (bridge legacy 9898), identity owner, TeamMember carries the
    LEGACY tenant 9898; session still selects the stale legacy id."""
    from app import db
    from app.models import Organization, OrgMember, Document
    from app.auth import TeamMember
    from app.authz.services import seed_default_roles

    org_id, legacy_id = 989, 9898
    identity, user_id = "bridge_tester", 5151

    org = Organization(id=org_id, name="Bridge Org", slug="bridge-org",
                       is_active=True, legacy_tenant_id=legacy_id)
    db.session.add(org)
    db.session.flush()
    seed_default_roles(org_id)
    db.session.add(OrgMember(organization_id=org_id, identity_id=identity,
                             role="owner", is_active=True))
    db.session.add(TeamMember(id=user_id, tenant_id=legacy_id,
                              name="Bridge", email="bridge@example.com"))
    # one legacy-era document (tenant 9898) + one canonical document (tenant 989)
    db.session.add(Document(filename="legacy_doc.pdf", file_path="/tmp/x",
                            file_type="pdf", tenant_id=legacy_id,
                            classification="quotation",
                            extracted_text="QUOTATION Ref SR-1. Unit price 500.",
                            uploaded_by=identity))
    db.session.add(Document(filename="canonical_doc.pdf", file_path="/tmp/y",
                            file_type="pdf", tenant_id=org_id,
                            classification="itinerary",
                            extracted_text="Itinerary: flight, hotel, check-in.",
                            uploaded_by=identity))
    # another organization's document — must never be visible
    db.session.add(Document(filename="other_org.pdf", file_path="/tmp/z",
                            file_type="pdf", tenant_id=777,
                            classification="invoice", extracted_text="INVOICE",
                            uploaded_by="someone_else"))
    db.session.commit()

    with client.session_transaction() as s:
        s["identity_id"] = identity
        s["user_id"] = user_id
        s["current_org_id"] = legacy_id  # stale legacy selection
    return {"org_id": org_id, "legacy_id": legacy_id, "identity": identity}


def test_scope_resolution_returns_org_plus_bridge(app, seeded):
    from app.authz.workspace_context import resolve_tenant_scope
    org_id, accepted = resolve_tenant_scope(seeded["identity"], seeded["legacy_id"])
    assert org_id == seeded["org_id"]
    assert set(accepted) == {seeded["org_id"], seeded["legacy_id"]}


def test_stale_legacy_selection_no_longer_breaks_the_list(app, client, seeded):
    r = client.get("/api/v1/workspace/documents?limit=50")
    assert r.status_code == 200
    names = {d["filename"] for d in r.get_json()["documents"]}
    assert {"legacy_doc.pdf", "canonical_doc.pdf"} <= names
    assert "other_org.pdf" not in names, "cross-tenant leak"


def test_manual_classification_works_on_legacy_era_document(app, client, seeded):
    """The exact live defect: canonical classify returned 404 for a legacy row."""
    from app import db
    from app.models import Document

    doc = Document.query.filter_by(filename="legacy_doc.pdf").first()
    r = client.post(f"/api/v1/documents/{doc.id}/classify",
                    json={"classification": "quotation"})
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["success"] is True
    db.session.refresh(doc)
    assert doc.classification == "quotation"


def test_other_org_document_stays_invisible(app, client, seeded):
    from app import db
    from app.models import Document

    doc = Document.query.filter_by(filename="other_org.pdf").first()
    r = client.post(f"/api/v1/documents/{doc.id}/classify",
                    json={"classification": "invoice"})
    assert r.status_code == 404


def test_new_uploads_write_the_canonical_tenant(app, client, seeded):
    from app import db
    from app.models import Document

    r = client.post(
        "/api/v1/founder/ingest",
        data={"file": (io.BytesIO(b"%PDF-1.4\nbridge test"), "new_doc.pdf")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 200
    doc = Document.query.filter_by(filename="new_doc.pdf").first()
    assert doc is not None
    assert doc.tenant_id == seeded["org_id"], (
        "new writes must move toward the canonical organization id")


def test_multi_membership_identity_with_stale_selection_fails_closed(app):
    """A stale legacy selection must never silently pick one of several orgs."""
    from app import db
    from app.models import Organization, OrgMember
    from app.authz.services import seed_default_roles
    from app.authz.workspace_context import resolve_tenant_scope

    for oid in (991, 992):
        db.session.add(Organization(id=oid, name=f"Org {oid}", slug=f"org-{oid}",
                                    is_active=True))
        db.session.flush()
        seed_default_roles(oid)
    db.session.add(OrgMember(organization_id=991, identity_id="multi",
                             role="owner", is_active=True))
    db.session.add(OrgMember(organization_id=992, identity_id="multi",
                             role="owner", is_active=True))
    db.session.commit()

    org_id, accepted = resolve_tenant_scope("multi", 9898)  # stale value
    assert org_id is None and accepted == [], (
        "multi-org identity must not auto-resolve from a stale selection")