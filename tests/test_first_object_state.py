"""G1.18 / KB-02 — the first-object emptiness predicate.

The home page's "Create your first business object" CTA must disappear as soon
as the organization owns any live business record, and must never claim an empty
workspace from a legacy store, a failed read, or an unauthorized caller.

Contract under test (``GET /api/v1/objects/first-object-state``):

* 200 with ``has_business_data`` true|false — authoritative answer computed
  server-side from every canonical business store (``sh_objects``,
  ``rel_relationships``, ``leads``, ``suppliers``).
* 401 unauthenticated, 403 not entitled, 400 no organization context — the UI
  treats all of these as *unknown*, never as empty.
* The predicate only reads: it creates, projects, and repairs nothing.
* Every count is tenant-scoped, and lifecycle state is respected (archived /
  soft-deleted records do not make a workspace non-empty).
"""

import pytest

STATE_URL = "/api/v1/objects/first-object-state"


@pytest.fixture(scope="function")
def org(client, app):
    """Real organization + owner role + workspace for identity ``g118_owner``."""
    from app import db
    from tests.auth_helper import seed_rbac

    org_id = seed_rbac(db, identity_id="g118_owner", role_name="owner")
    with client.session_transaction() as session:
        session["identity_id"] = "g118_owner"
        session["current_org_id"] = org_id
    return org_id


@pytest.fixture(scope="function")
def workspace_id(app, org):
    from app.objects.legacy_models import Workspace

    ws = Workspace.query.filter_by(organization_id=org, status="active").first()
    assert ws is not None, "fixture must provision a real workspace"
    return ws.id


def _state(client):
    response = client.get(STATE_URL)
    return response, (response.get_json() or {})


def _commit_import(client, content, target_type, token):
    return client.post(
        "/api/v1/data/import/commit",
        json={
            "content": content,
            "content_type": "csv",
            "target_type": target_type,
            "column_overrides": {},
            "source_name": "g118-test",
            "session_token": token,
        },
    )


def _row_counts():
    """Live row counts for the four stores the predicate reads."""
    from app import db
    from app.models import Lead, Supplier
    from app.objects.legacy_models import ShunyaObject
    from app.relationship.models import CanonicalRelationship

    return {
        "sh_objects": db.session.query(ShunyaObject).count(),
        "rel_relationships": db.session.query(CanonicalRelationship).count(),
        "leads": db.session.query(Lead).count(),
        "suppliers": db.session.query(Supplier).count(),
    }


class TestEmptyWorkspace:
    def test_fresh_organization_reports_no_business_data(self, client, org):
        response, body = _state(client)
        assert response.status_code == 200
        assert body["success"] is True
        assert body["has_business_data"] is False
        assert body["total"] == 0
        assert body["counts"] == {"objects": 0, "relationships": 0, "leads": 0,
                                  "suppliers": 0, "examples": 0}

    def test_answer_is_scoped_to_the_callers_organization(self, client, org):
        response, body = _state(client)
        assert response.status_code == 200
        assert body["organization_id"] == org


class TestEveryCreationPathSatisfiesThePredicate:
    def test_imported_customer_counts(self, client, org):
        response = _commit_import(
            client,
            "display_name,email\nKB02 Customer,kb02@cert.local\n",
            "customer",
            "g118-customer",
        )
        assert response.status_code == 201

        response, body = _state(client)
        assert response.status_code == 200
        assert body["has_business_data"] is True
        assert body["counts"]["relationships"] == 1
        # The import writes domain records, not universal objects (no dual-write).
        assert body["counts"]["objects"] == 0

    def test_imported_lead_counts(self, client, org):
        response = _commit_import(
            client,
            "customer_name,phone,email\nKB02 Lead,+911111111111,kb02lead@cert.local\n",
            "lead",
            "g118-lead",
        )
        assert response.status_code == 201

        response, body = _state(client)
        assert body["has_business_data"] is True
        assert body["counts"]["leads"] == 1

    def test_imported_supplier_counts(self, client, org):
        response = _commit_import(
            client,
            "name,category,email\nKB02 Supplies,packaging,kb02supplier@cert.local\n",
            "supplier",
            "g118-supplier",
        )
        assert response.status_code == 201

        response, body = _state(client)
        assert body["has_business_data"] is True
        assert body["counts"]["suppliers"] == 1

    def test_canonical_object_counts(self, client, org, workspace_id):
        from core.object_service import get_object_service

        get_object_service().create(
            object_type="note",
            name="KB02 note",
            organization_id=org,
            data={},
            created_by="g118_owner",
            workspace_id=workspace_id,
            identity_id="g118_owner",
        )

        response, body = _state(client)
        assert body["has_business_data"] is True
        assert body["counts"]["objects"] == 1


class TestTenantIsolation:
    def test_other_organization_records_do_not_count(self, client, app, org):
        from app import db
        from app.relationship.models import CanonicalRelationship

        other_org_id = org + 1000
        db.session.add(CanonicalRelationship(
            organization_id=other_org_id,
            display_name="Other tenant customer",
            relationship_type="customer",
            status="active",
        ))
        db.session.commit()

        from app.objects.first_object_state import get_first_object_state

        assert get_first_object_state(other_org_id)["has_business_data"] is True
        assert get_first_object_state(org)["has_business_data"] is False

        response, body = _state(client)
        assert response.status_code == 200
        assert body["has_business_data"] is False
        assert body["counts"]["relationships"] == 0


class TestLifecycleSemantics:
    def test_archived_relationship_does_not_count(self, client, org):
        response = _commit_import(
            client,
            "display_name,email\nKB02 Archived,kb02arch@cert.local\n",
            "customer",
            "g118-archived",
        )
        assert response.status_code == 201

        from app import db
        from app.relationship.models import CanonicalRelationship

        rel = CanonicalRelationship.query.filter_by(organization_id=org).one()
        rel.status = "archived"
        db.session.commit()

        response, body = _state(client)
        assert response.status_code == 200
        assert body["has_business_data"] is False

    def test_soft_deleted_object_does_not_count(self, client, org, workspace_id):
        from app import db
        from core.object_service import get_object_service
        from app.objects.legacy_models import ShunyaObject

        get_object_service().create(
            object_type="note",
            name="KB02 deleted note",
            organization_id=org,
            data={},
            created_by="g118_owner",
            workspace_id=workspace_id,
            identity_id="g118_owner",
        )
        response, body = _state(client)
        assert body["has_business_data"] is True

        obj = db.session.query(ShunyaObject).filter_by(organization_id=org).one()
        obj.is_deleted = True
        db.session.commit()

        response, body = _state(client)
        assert response.status_code == 200
        assert body["has_business_data"] is False


class TestAuthorizationContract:
    def test_unauthenticated_is_401(self, client, app):
        response = client.get(STATE_URL)
        assert response.status_code == 401

    def test_non_member_is_403_not_empty(self, client, app, org):
        with client.session_transaction() as session:
            session["identity_id"] = "g118_stranger"
            session["current_org_id"] = org
        response, body = _state(client)
        assert response.status_code == 403
        assert "has_business_data" not in body

    def test_missing_organization_id_fails_closed(self, app):
        from app.objects.first_object_state import get_first_object_state

        with app.app_context():
            with pytest.raises(ValueError):
                get_first_object_state(0)
            with pytest.raises(ValueError):
                get_first_object_state(None)


class TestExecutiveSummaryUsesTheSameInvariant:
    """The executive home's empty-state priority must not contradict the CTA."""

    def test_import_only_organization_is_not_told_it_has_no_objects(self, client, org, app):
        response = _commit_import(
            client,
            "display_name,email\nKB02 Summary,kb02sum@cert.local\n",
            "customer",
            "g118-summary",
        )
        assert response.status_code == 201

        from app.adapters.os_adapter import get_executive_home

        summary = get_executive_home("g118_owner")
        assert summary["success"] is True
        ids = [p["id"] for p in summary["data"]["priorities"]]
        assert "getting_started" not in ids

    def test_empty_organization_still_gets_the_getting_started_priority(self, client, org, app):
        from app.adapters.os_adapter import get_executive_home

        summary = get_executive_home("g118_owner")
        ids = [p["id"] for p in summary["data"]["priorities"]]
        assert "getting_started" in ids


class TestPredicateIsReadOnly:
    def test_reading_the_state_creates_no_records(self, client, org):
        before = _row_counts()
        for _ in range(3):
            response, _body = _state(client)
            assert response.status_code == 200
        after = _row_counts()
        assert before == after
