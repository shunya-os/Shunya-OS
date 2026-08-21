"""B-P01: Universal Object Protocol HTTP API integration tests.

Verifies the UOP HTTP API works end-to-end through the canonical
object protocol path: REQUEST → API → PROTOCOL → PERSISTENCE → RETRIEVAL → RESPONSE.
"""
import json

import pytest


@pytest.fixture
def uop_client(app, client):
    """Return a client with auth session for UOP tests."""
    from app import db as _db
    from app.models import Organization, OrgMember
    from app.authz.models import Role, OrgMemberRole
    from app.authz.services import seed_default_roles

    org = Organization(name="UOP-Test", slug="uop-test")
    _db.session.add(org)
    _db.session.commit()
    seed_default_roles(org.id)
    role = Role.query.filter_by(organization_id=org.id, name="admin").first()
    member = OrgMember(
        organization_id=org.id, identity_id="uop-tester",
        email="uop@test.com", name="UOP Tester", is_active=True,
    )
    _db.session.add(member)
    _db.session.commit()
    _db.session.add(OrgMemberRole(
        organization_id=org.id, member_id=member.id, role_id=role.id,
    ))
    _db.session.commit()
    with client.session_transaction() as sess:
        sess["user_id"] = "uop-tester"
        sess["identity_id"] = "uop-tester"
        sess["current_org_id"] = org.id
    return client


class TestUOPAPI:
    """Universal Object Protocol HTTP API tests."""

    def test_create_object(self, uop_client):
        """POST /api/v1/uop/objects creates a UniversalObject."""
        resp = uop_client.post("/api/v1/uop/objects", json={
            "object_type": "document",
            "name": "Protocol Test Doc",
            "metadata": {"author": "tester", "tags": ["test"]},
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        obj = data["object"]
        assert obj["object_id"]
        assert obj["object_type"] == "document"
        assert obj["name"] == "Protocol Test Doc"
        assert obj["status"] == "active"
        assert obj["version"] == 1

    def test_get_object(self, uop_client):
        """GET /api/v1/uop/objects/<id> retrieves by protocol ID."""
        create = uop_client.post("/api/v1/uop/objects", json={
            "object_type": "human", "name": "Jane Doe",
        })
        oid = create.get_json()["object"]["object_id"]

        resp = uop_client.get(f"/api/v1/uop/objects/{oid}")
        assert resp.status_code == 200
        obj = resp.get_json()["object"]
        assert obj["object_id"] == oid
        assert obj["name"] == "Jane Doe"

    def test_get_object_not_found(self, uop_client):
        """GET returns 404 for unknown object_id."""
        resp = uop_client.get("/api/v1/uop/objects/nonexistent-id")
        assert resp.status_code == 404

    def test_list_objects(self, uop_client):
        """GET /api/v1/uop/objects returns all non-archived objects."""
        uop_client.post("/api/v1/uop/objects", json={"object_type": "deal", "name": "Deal A"})
        uop_client.post("/api/v1/uop/objects", json={"object_type": "deal", "name": "Deal B"})

        resp = uop_client.get("/api/v1/uop/objects")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] >= 2
        assert data["success"] is True

    def test_list_filter_by_type(self, uop_client):
        """GET /api/v1/uop/objects?object_type= filters correctly."""
        uop_client.post("/api/v1/uop/objects", json={"object_type": "invoice", "name": "INV-001"})
        uop_client.post("/api/v1/uop/objects", json={"object_type": "note", "name": "Note-001"})

        resp = uop_client.get("/api/v1/uop/objects?object_type=invoice")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] >= 1
        for o in data["objects"]:
            assert o["object_type"] == "invoice"

    def test_archive_object(self, uop_client):
        """POST /api/v1/uop/objects/<id>/archive soft-deletes."""
        create = uop_client.post("/api/v1/uop/objects", json={
            "object_type": "task", "name": "Archivable Task",
        })
        oid = create.get_json()["object"]["object_id"]

        resp = uop_client.post(f"/api/v1/uop/objects/{oid}/archive")
        assert resp.status_code == 200
        obj = resp.get_json()["object"]
        assert obj["status"] == "archived"

        # Should not appear in list
        listed = uop_client.get("/api/v1/uop/objects")
        assert oid not in [o["object_id"] for o in listed.get_json()["objects"]]

    def test_add_evidence(self, uop_client):
        """POST /api/v1/uop/objects/<id>/evidence adds reference."""
        create = uop_client.post("/api/v1/uop/objects", json={
            "object_type": "claim", "name": "Evidence Test",
        })
        oid = create.get_json()["object"]["object_id"]

        resp = uop_client.post(f"/api/v1/uop/objects/{oid}/evidence", json={
            "evidence_id": "ev-abc-123",
            "evidence_type": "document",
        })
        assert resp.status_code == 200
        obj = resp.get_json()["object"]
        ev_list = obj.get("evidence", [])
        assert len(ev_list) >= 1
        assert ev_list[0]["evidence_id"] == "ev-abc-123"

    def test_full_protocol_lifecycle(self, uop_client):
        """End-to-end: CREATE → GET → EVIDENCE → ARCHIVE → LIST absence."""
        # CREATE
        r = uop_client.post("/api/v1/uop/objects", json={
            "object_type": "project", "name": "Lifecycle Project",
        })
        assert r.status_code == 201
        oid = r.get_json()["object"]["object_id"]

        # GET
        r = uop_client.get(f"/api/v1/uop/objects/{oid}")
        assert r.status_code == 200
        assert r.get_json()["object"]["name"] == "Lifecycle Project"

        # EVIDENCE
        r = uop_client.post(f"/api/v1/uop/objects/{oid}/evidence", json={
            "evidence_id": "ev-cycle-001",
        })
        assert r.status_code == 200
        assert len(r.get_json()["object"].get("evidence", [])) == 1

        # ARCHIVE
        r = uop_client.post(f"/api/v1/uop/objects/{oid}/archive")
        assert r.status_code == 200
        assert r.get_json()["object"]["status"] == "archived"

        # LIST absence
        r = uop_client.get("/api/v1/uop/objects")
        assert oid not in [o["object_id"] for o in r.get_json()["objects"]]