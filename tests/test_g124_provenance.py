"""G1.24 — first-use provenance semantics (decision D-1 = Option B).

The defect being closed: onboarding provisioned 26 placeholder objects, so a
brand-new organization reported ``has_business_data: true`` before the user had
entered a single fact. Rows could not be classified afterwards, so origin is now
recorded at creation and only rows *known* to be examples are excluded.

These tests pin the whole contract, not just the happy path:

* zero user input → no business data, examples reported separately;
* a provisioned example never satisfies the predicate, even when archived;
* editing an example promotes it to user data (the user supplied content);
* user / import / AI creations all count;
* unknown historical provenance counts (never hide real data on a guess);
* tenant isolation: another organization's examples are irrelevant;
* the AI grounding boundary excludes examples and says so truthfully.
"""

import pytest

from app import db
from core.object_service import get_object_service

STATE_URL = "/api/v1/objects/first-object-state"


@pytest.fixture(scope="function")
def org(client, app):
    from tests.auth_helper import seed_rbac

    org_id = seed_rbac(db, identity_id="g124_owner", role_name="owner")
    with client.session_transaction() as session:
        session["identity_id"] = "g124_owner"
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


def _create(org, workspace_id, *, name, object_type="customer",
            provenance=None, identity_id: "str | None" = "g124_owner", system_scope=False):
    return get_object_service().create(
        object_type=object_type,
        name=name,
        organization_id=org,
        data={"content": ""} if provenance == "onboarding_seed" else {"content": "real"},
        created_by=(identity_id or "system")[:12],
        workspace_id=workspace_id,
        identity_id=identity_id,
        system_scope=system_scope,
        provenance=provenance,
    )


def _seed_examples(org, workspace_id, count=3, identity_id="g124_owner"):
    types = ["customer", "invoice", "proposal", "task", "note"]
    for index in range(count):
        _create(org, workspace_id, object_type=types[index % len(types)],
                name=f"Example {index}", provenance="onboarding_seed",
                identity_id=identity_id)


class TestZeroInputIsEmpty:
    def test_no_records_at_all(self, client, org):
        response, body = _state(client)
        assert response.status_code == 200
        assert body["has_business_data"] is False
        assert body["total"] == 0

    def test_provisioned_examples_do_not_count_as_business_data(
            self, client, org, workspace_id):
        """The exact reported defect: seeded placeholders must not read as data."""
        _seed_examples(org, workspace_id, count=3)

        response, body = _state(client)
        assert response.status_code == 200
        assert body["has_business_data"] is False, (
            "system-provisioned examples were counted as user business data")
        assert body["total"] == 0
        assert body["counts"]["examples"] == 3
        assert body["counts"]["objects"] == 0

    def test_examples_are_still_listed_with_their_label(
            self, client, org, workspace_id):
        """C3: examples stay useful — they are labelled, not hidden."""
        _seed_examples(org, workspace_id, count=2)

        listing = client.get("/api/v1/objects").get_json()
        assert listing["total"] == 2, listing
        for row in listing["objects"]:
            assert row["is_example"] is True
            assert row["provenance"] == "onboarding_seed"
            assert row["provenance_label"] == "Example"


class TestEveryRealCreationPathCounts:
    def test_user_created_object_counts(self, client, org, workspace_id):
        _create(org, workspace_id, name="Real customer")

        response, body = _state(client)
        assert body["has_business_data"] is True
        assert body["counts"]["objects"] == 1
        assert body["counts"]["examples"] == 0

    def test_import_created_object_counts(self, client, org, workspace_id):
        _create(org, workspace_id, name="Imported supplier",
                object_type="supplier", provenance="import")

        _response, body = _state(client)
        assert body["has_business_data"] is True

    def test_ai_created_object_counts(self, client, org, workspace_id):
        _create(org, workspace_id, name="AI drafted task",
                object_type="task", provenance="ai")

        _response, body = _state(client)
        assert body["has_business_data"] is True

    def test_unknown_historical_provenance_counts(self, client, app, org, workspace_id):
        """NULL means unknown, not 'example'. Real legacy rows must never hide."""
        from app.objects.legacy_models import ShunyaObject

        db.session.add(ShunyaObject(
            object_id="g124-legacy-row",
            workspace_id=workspace_id,
            organization_id=org,
            object_type="customer",
            name="Legacy customer",
            status="active",
            data={"content": "recorded before provenance existed"},
            created_by="legacy",
            provenance=None,
        ))
        db.session.commit()

        _response, body = _state(client)
        assert body["has_business_data"] is True
        assert body["counts"]["objects"] == 1


class TestEditingAnExampleMakesItUserData:
    def test_content_edit_promotes_the_row(self, client, org, workspace_id):
        _create(org, workspace_id, object_type="customer",
                name="Customer", provenance="onboarding_seed")

        _response, before = _state(client)
        assert before["has_business_data"] is False

        from app.objects.legacy_models import ShunyaObject

        row = ShunyaObject.query.filter_by(organization_id=org).one()
        assert get_object_service().update(
            row.id, organization_id=org, identity_id="g124_owner",
            data={"company_name": "Acme Pvt Ltd", "contact_person": "Asha"},
        )

        refreshed = db.session.get(ShunyaObject, row.id)
        db.session.refresh(refreshed)
        assert refreshed.provenance == "user", (
            "a placeholder the user filled in is user-supplied content")

        _response, after = _state(client)
        assert after["has_business_data"] is True
        assert after["counts"]["examples"] == 0

    def test_lifecycle_only_write_does_not_promote(self, client, org, workspace_id):
        """Archiving an untouched example must not fabricate user data."""
        _create(org, workspace_id, object_type="customer",
                name="Customer", provenance="onboarding_seed")
        from app.objects.legacy_models import ShunyaObject

        row = ShunyaObject.query.filter_by(organization_id=org).one()
        assert get_object_service().archive(
            row.id, organization_id=org, identity_id="g124_owner")

        refreshed = db.session.get(ShunyaObject, row.id)
        db.session.refresh(refreshed)
        assert refreshed.provenance == "onboarding_seed"

        _response, body = _state(client)
        assert body["has_business_data"] is False


class TestTenantIsolation:
    def test_another_organizations_examples_are_irrelevant(
            self, client, app, org, workspace_id):
        from app.objects.legacy_models import Workspace
        from tests.auth_helper import seed_rbac

        other_org = seed_rbac(db, identity_id="g124_other", role_name="owner")
        other_ws = Workspace.query.filter_by(organization_id=other_org).first()
        _seed_examples(other_org, other_ws.id, count=2, identity_id="g124_other")

        _response, body = _state(client)
        assert body["organization_id"] == org
        assert body["has_business_data"] is False
        assert body["counts"]["examples"] == 0

    def test_predicate_fails_closed_without_an_organization(self, app):
        from app.objects.first_object_state import get_first_object_state

        with app.app_context():
            with pytest.raises(ValueError):
                get_first_object_state(0)


class TestProvenanceIsPersistedAtCreation:
    def test_identity_call_defaults_to_user(self, org, workspace_id):
        created = _create(org, workspace_id, name="Defaulted user row")
        assert created["provenance"] == "user"

    def test_system_scope_defaults_to_system(self, org, workspace_id):
        created = _create(org, workspace_id, name="Bootstrapped row",
                          identity_id=None, system_scope=True)
        assert created["provenance"] == "system"

    def test_explicit_value_wins(self, org, workspace_id):
        created = _create(org, workspace_id, name="Imported row",
                          provenance="import")
        assert created["provenance"] == "import"

    def test_unknown_vocabulary_is_rejected(self, org, workspace_id):
        from app.objects.provenance import InvalidProvenanceError

        with pytest.raises(InvalidProvenanceError):
            _create(org, workspace_id, name="Typo row",
                    provenance="onboardingseed")

    def test_vocabulary_predicates(self):
        from app.objects import provenance as prov

        assert prov.is_example("onboarding_seed") is True
        assert prov.is_example("user") is False
        assert prov.is_example(None) is False
        assert prov.counts_as_business_data(None) is True
        assert prov.counts_as_business_data("onboarding_seed") is False


class TestApiSurfacesAgree:
    """List, detail and create must tell the same story about a row."""

    def test_create_response_carries_provenance(self, client, org, workspace_id):
        response = client.post("/api/v1/objects/",
                               json={"name": "API created", "object_type": "customer"})
        assert response.status_code == 200, response.get_data(as_text=True)
        body = response.get_json()
        assert body["provenance"] == "user"

    def test_detail_labels_match_the_stored_provenance(self, client, org, workspace_id):
        created = _create(org, workspace_id, object_type="customer",
                          name="Customer", provenance="onboarding_seed")

        example = client.get(f"/api/v1/objects/by-id/{created['object_id']}").get_json()["data"]
        assert example["provenance"] == "onboarding_seed"
        assert example["is_example"] is True
        assert example["provenance_label"] == "Example"

        real = client.post("/api/v1/objects/",
                           json={"name": "Real row", "object_type": "note"})
        real_id = real.get_json()["object_id"]
        detail = client.get(f"/api/v1/objects/by-id/{real_id}").get_json()["data"]
        assert detail["provenance"] == "user"
        assert detail["is_example"] is False
        assert detail["provenance_label"] == "Created by you"

    def test_listing_marks_examples_consistently(self, client, org, workspace_id):
        _seed_examples(org, workspace_id, count=2)
        _create(org, workspace_id, name="Real row", object_type="note")

        listing = client.get("/api/v1/objects").get_json()["objects"]
        assert len(listing) == 3
        for row in listing:
            assert row["is_example"] is (row["provenance"] == "onboarding_seed")
            assert row["provenance_label"]


class TestAIGroundingExcludesExamples:
    """D-2 = No: examples are never presented to the model as company facts."""

    def _ask_count(self, org):
        from core.intelligence import IntelligenceRequest
        from core.intelligence.service import IntelligenceService

        service = IntelligenceService()
        request = IntelligenceRequest(
            tenant_id=org,
            question="how many objects do we have?",
            request_id="g124-test",
        )
        return service._deterministic_compute(request, [])

    def test_counts_exclude_examples_and_say_so(self, org, workspace_id):
        _seed_examples(org, workspace_id, count=4)

        result = self._ask_count(org)
        assert result is not None
        assert result["result"]["total_objects"] == 0, (
            "the model was told the organization has business objects it never created")
        assert result["result"]["by_type"] == {}
        assert "4 provisioned example" in result["description"]
        assert "Total user-supplied objects: 0" in result["description"]

    def test_real_objects_are_counted_alongside_examples(self, org, workspace_id):
        _seed_examples(org, workspace_id, count=2)
        _create(org, workspace_id, name="Real customer")

        result = self._ask_count(org)
        assert result["result"]["total_objects"] == 1
        assert result["result"]["by_type"] == {"customer": 1}
        assert "2 provisioned example" in result["description"]

    def test_current_example_object_is_labelled_not_asserted(self, org, workspace_id):
        created = _create(org, workspace_id, object_type="customer",
                          name="Customer", provenance="onboarding_seed")
        from core.intelligence import IntelligenceRequest
        from core.intelligence.service import IntelligenceService

        service = IntelligenceService()
        request = IntelligenceRequest(
            tenant_id=org,
            question="what is this?",
            request_id="g124-context",
            context_object_id=created["object_id"],
            context_object_type="customer",
        )
        sources = service._retrieve_company_context(request)
        assert sources, "the context object should still be offered to the model"
        assert all(s.type == "example" for s in sources), (
            "a provisioned placeholder was offered as company_data")
        assert "NOT organizational" in sources[0].detail

    def test_real_object_is_company_data(self, org, workspace_id):
        created = _create(org, workspace_id, name="Real customer")
        from core.intelligence import IntelligenceRequest
        from core.intelligence.service import IntelligenceService

        service = IntelligenceService()
        request = IntelligenceRequest(
            tenant_id=org,
            question="what is this?",
            request_id="g124-context-real",
            context_object_id=created["object_id"],
            context_object_type="customer",
        )
        sources = service._retrieve_company_context(request)
        assert [s.type for s in sources] == ["company_data"]
