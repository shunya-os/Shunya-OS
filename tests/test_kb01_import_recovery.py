"""KB-01 — first-object import: rejected submission, keyboard recovery, persistence.

G1.17 root cause: the keyboard-only recovery failure was a *harness* defect.
The regression harness selected the import target by pressing "c" on the native
select; because the select keeps the previous choice across the flow reset, the
second "c" cycled the already-selected "Customers" to "Campaigns", so the valid
customer CSV was submitted as a campaign import and the backend truthfully
rejected it ("Missing required field: name").

These tests pin the product behaviour the journey depends on — independent of
the browser — so a real product regression cannot hide behind a harness fix:

  1. An invalid import is rejected and writes nothing.
  2. A valid import submitted afterwards persists a canonical customer.
  3. The persisted customer is returned by the relationships list the workspace
     renders.
  4. Its detail (timeline + AI memory) is readable.
  5. The record survives subsequent requests (persistence, not request state).

They exercise the real HTTP surface with a real organization/workspace and the
canonical relationship store; no mocks.
"""

import pytest


@pytest.fixture(scope="function")
def kb01_org(client, app):
    """Real organization + owner role + canonical workspace for this identity."""
    from app import db
    from tests.auth_helper import seed_rbac

    org_id = seed_rbac(db, identity_id="kb01_identity", role_name="owner")
    with client.session_transaction() as session:
        session["identity_id"] = "kb01_identity"
        session["current_org_id"] = org_id
    return org_id


INVALID_CSV = "email\nonly-an-email@example.com\n"
RECORD_NAME = "KB Recovery Customer"
VALID_CSV = f"display_name,email\n{RECORD_NAME},kb-recovery@cert.local\n"


def _preview(client, content, target_type="customer"):
    response = client.post(
        "/api/v1/data/import/preview",
        json={
            "content": content,
            "content_type": "csv",
            "target_type": target_type,
            "column_overrides": {},
        },
    )
    return response, response.get_json() or {}


def _commit(client, content, target_type="customer", session_token="kb01"):
    response = client.post(
        "/api/v1/data/import/commit",
        json={
            "content": content,
            "content_type": "csv",
            "target_type": target_type,
            "column_overrides": {},
            "source_name": "kb01-test",
            "session_token": session_token,
        },
    )
    return response, response.get_json() or {}


def _customers(org_id):
    from app.relationship.models import CanonicalRelationship

    return (
        CanonicalRelationship.query.filter_by(organization_id=org_id)
        .filter(CanonicalRelationship.relationship_type == "customer")
        .all()
    )


class TestRejectedImport:
    def test_invalid_rows_are_reported_invalid(self, client, kb01_org):
        response, body = _preview(client, INVALID_CSV)
        assert response.status_code == 200
        data = body["data"]
        assert data["valid_records"] == 0
        assert data["invalid_records"] >= 1
        assert data["records_to_create"] == 0

    def test_rejected_commit_writes_nothing(self, client, kb01_org):
        response, body = _commit(client, INVALID_CSV, session_token="kb01-invalid")
        assert response.status_code == 400
        assert body["success"] is False
        data = body["data"]
        assert data["status"] == "rejected"
        assert data["created"] == 0
        assert data["rejected"] >= 1
        assert _customers(kb01_org) == []

    def test_recovery_after_rejection_is_a_real_import(self, client, kb01_org):
        """Invalid submission followed by a valid one — the KB-01 journey order."""
        invalid_response, invalid_body = _commit(client, INVALID_CSV, session_token="kb01-first")
        assert invalid_response.status_code == 400
        assert (invalid_body.get("data") or {}).get("created") == 0

        preview_response, preview_body = _preview(client, VALID_CSV)
        assert preview_response.status_code == 200
        assert preview_body["data"]["valid_records"] == 1

        commit_response, commit_body = _commit(client, VALID_CSV, session_token="kb01-second")
        assert commit_response.status_code == 201
        assert commit_body["success"] is True
        data = commit_body["data"]
        assert data["status"] == "completed"
        assert data["created"] == 1
        assert data["records_created"][0]["name"] == RECORD_NAME

        rows = _customers(kb01_org)
        assert len(rows) == 1
        assert rows[0].display_name == RECORD_NAME
        assert rows[0].email == "kb-recovery@cert.local"


class TestPersistedRecordIsReachable:
    def _import_valid(self, client):
        response, body = _commit(client, VALID_CSV, session_token="kb01-reachable")
        assert response.status_code == 201
        return body["data"]

    def test_relationship_list_returns_the_record(self, client, kb01_org):
        created = self._import_valid(client)
        response = client.get("/relationships/api/v1/relationships?limit=100")
        assert response.status_code == 200
        names = [r.get("display_name") for r in response.get_json().get("relationships", [])]
        assert RECORD_NAME in names
        assert created["records_created"][0]["name"] in names

    def test_relationship_detail_is_readable(self, client, kb01_org):
        self._import_valid(client)
        from app.relationship.models import CanonicalRelationship

        rel = CanonicalRelationship.query.filter_by(
            organization_id=kb01_org, display_name=RECORD_NAME
        ).one()

        timeline = client.get(f"/relationships/api/v1/relationships/{rel.id}/timeline")
        assert timeline.status_code == 200
        assert "timeline" in timeline.get_json()

        memory = client.get(f"/relationships/api/v1/relationships/{rel.id}/memory")
        assert memory.status_code == 200

    def test_record_survives_subsequent_requests(self, client, kb01_org):
        self._import_valid(client)
        first = client.get("/relationships/api/v1/relationships?limit=100").get_json()
        second = client.get("/relationships/api/v1/relationships?limit=100").get_json()
        for payload in (first, second):
            assert RECORD_NAME in [r.get("display_name") for r in payload.get("relationships", [])]
        assert len(_customers(kb01_org)) == 1
