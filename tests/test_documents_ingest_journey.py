"""Documents "add to workspace" journey — regression for the reported 500.

The Add-to-SHUNYA panel posts to POST /api/v1/founder/ingest (session-cookie
auth only — no X-Identity-Id in the browser flow). A 500 there is an
"Internal server error" to the user. This pins the journey end-to-end:

- authenticated org member ingests a file → 201/200, document created
- the same document appears in the workspace document list
- tenant B never sees tenant A's ingested document
"""
import io

import pytest

from app import db
from app.auth import TeamMember
from app.models import Organization, OrgMember
from app.authz.services import seed_default_roles


@pytest.fixture()
def ingest_scope(app, client):
    org = Organization(name="Panchi Club", slug="panchi-club")
    db.session.add(org)
    db.session.commit()
    seed_default_roles(org.id)
    tm = TeamMember(name="Owner", email="panchi@test.invalid", role="owner",
                    is_active=True, identity_id="sid_panchi")
    db.session.add(tm)
    db.session.flush()
    db.session.add(OrgMember(organization_id=org.id, identity_id="sid_panchi",
                             email=tm.email, role="owner", is_active=True))
    db.session.commit()
    with client.session_transaction() as sess:
        sess["user_id"] = tm.id
        sess["identity_id"] = "sid_panchi"
        sess["current_org_id"] = org.id
    return org


def _text_file(name="notes.csv", content="title,amount\nQ3 plan,1200\n"):
    return (io.BytesIO(content.encode("utf-8")), name)


def test_ingest_does_not_500_and_creates_document(client, ingest_scope):
    data = {"file": _text_file("notes.csv", "title,amount\nQ3 plan,1200\n")}
    resp = client.post("/api/v1/founder/ingest", data=data,
                       content_type="multipart/form-data")
    assert resp.status_code in (200, 201), resp.get_data(as_text=True)[:500]
    body = resp.get_json()
    assert body.get("success") is True
    assert body.get("document_id")
    assert body.get("summary")


def test_ingested_document_appears_in_workspace_list(client, ingest_scope):
    data = {"file": _text_file("notes.txt", "travel itinerary for Goa")}
    client.post("/api/v1/founder/ingest", data=data,
                content_type="multipart/form-data")
    resp = client.get("/api/v1/workspace/documents")
    assert resp.status_code == 200, resp.get_data(as_text=True)[:500]
    body = resp.get_json()
    names = [d.get("filename") for d in body.get("documents", [])]
    assert "notes.txt" in names


def test_duplicate_ingest_is_truthfully_reported(client, ingest_scope):
    fname, content = "dup.csv", "a,b\n1,2\n"
    # Fresh stream objects per request — Werkzeug consumes the BytesIO.
    first = client.post("/api/v1/founder/ingest",
                        data={"file": _text_file(fname, content)},
                        content_type="multipart/form-data")
    second = client.post("/api/v1/founder/ingest",
                         data={"file": _text_file(fname, content)},
                         content_type="multipart/form-data")
    assert first.status_code in (200, 201)
    assert second.status_code == 200
    body = second.get_json()
    assert body.get("duplicate") is True
    assert body.get("document_id") == first.get_json().get("document_id")


def test_other_tenant_cannot_see_ingested_document(client, ingest_scope):
    data = {"file": _text_file("secret.txt", "SECRET TENANT-A CONTENT")}
    client.post("/api/v1/founder/ingest", data=data,
                content_type="multipart/form-data")

    org_b = Organization(name="Other Co", slug="other-co")
    db.session.add(org_b)
    db.session.commit()
    seed_default_roles(org_b.id)
    tm_b = TeamMember(name="B", email="b2@test.invalid", role="owner",
                      is_active=True, identity_id="sid_b2")
    db.session.add(tm_b)
    db.session.flush()
    db.session.add(OrgMember(organization_id=org_b.id, identity_id="sid_b2",
                             email=tm_b.email, role="owner", is_active=True))
    db.session.commit()
    with client.session_transaction() as sess:
        sess["user_id"] = tm_b.id
        sess["identity_id"] = "sid_b2"
        sess["current_org_id"] = org_b.id

    resp = client.get("/api/v1/workspace/documents")
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "secret.txt" not in text
    assert "SECRET TENANT-A CONTENT" not in text