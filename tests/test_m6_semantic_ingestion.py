"""M6 — Semantic Ingestion contract tests (SH-M6→M15 directive, Stage A).

Required behaviour (A1/A3/A4/A5/A6/A7):
  INSPECT → UNDERSTAND → MAP → DETECT AMBIGUITY → DETECT DUPLICATES →
  PREVIEW → CONFIRM → PERSIST → PROVENANCE → CORRECT → RECOVER → OBSERVE

Covers:
  * explainable column mapping (alias / manual / fallback / unmapped + hints)
  * ambiguity surfaces (multiple candidates, name-like unmapped, conflicts)
  * human mapping decisions via column_overrides (preview + commit agree)
  * customer ingestion with flexible column names (Guest, Party Name, Client)
  * supplier ingestion; similar-name candidates are surfaced, never merged
  * identity match basis explanations
  * provenance: source file, row, session, mapping, author, timestamp
  * correction: canonical update + auditable correction evidence
  * recovery: partial failure retry is idempotent, no duplicates
  * tenant isolation on provenance reads and corrections
"""

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
def auth(app, client):
    """Seed an owner org and authenticate the test client. Returns (org_id, headers)."""
    from tests.auth_helper import seed_rbac
    from app import db
    org_id = seed_rbac(db, identity_id="m6_user", role_name="owner")
    with client.session_transaction() as s:
        s["identity_id"] = "m6_user"
        s["current_org_id"] = org_id
    return org_id, {"X-Identity-Id": "m6_user"}


CUSTOMER_CSV = (
    "Client Name,Mobile,Email,Company,City,Notes\n"
    "Asha Menon,+91 98450 12345,asha@example.com,Panchi Club,Mumbai,Prefers morning calls\n"
    "Ravi Kumar,+91 98450 67890,ravi@example.com,,Bengaluru,\n"
)

SUPPLIER_CSV = (
    "Vendor Name,Type,Contact Person,Email,Phone,City,Payment Terms\n"
    "ACME Hotels,hotel,John Smith,john@acme.com,+1-555-0100,New York,Net 30\n"
    "Globex Logistics,transport,Jane Doe,jane@globex.com,+1-555-0200,Chicago,Net 15\n"
)


# =========================================================================
# 1. Column mapping explanation (A1/A3)
# =========================================================================


class TestExplainableMapping:

    def test_preview_explains_every_column(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/preview", headers=headers, json={
            "content": CUSTOMER_CSV, "content_type": "csv", "target_type": "customer",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]

        mapping = {m["source_column"]: m for m in data["column_mapping"]}
        assert mapping["Client Name"]["target_field"] == "display_name"
        assert mapping["Client Name"]["method"] == "alias"
        assert "alias" in mapping["Client Name"]["reason"]
        assert mapping["Mobile"]["target_field"] == "phone"
        assert mapping["Email"]["target_field"] == "email"
        assert mapping["Company"]["target_field"] == "company_name"
        assert mapping["City"]["target_field"] == "city"
        assert mapping["Notes"]["target_field"] == "notes"
        # every column has a reason (nothing silent)
        for m in data["column_mapping"]:
            assert m["reason"], f"column {m['source_column']} has no explanation"

    def test_unmapped_name_like_column_is_surfaced(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/preview", headers=headers, json={
            "content": "Name,Product Name,Phone\nAlice,Umbrella Stand,+1-555-0101\n",
            "content_type": "csv", "target_type": "customer",
        })
        data = resp.get_json()["data"]
        codes = [a["code"] for a in data["ambiguities"]]
        assert "unmapped_name_like" in codes
        amb = next(a for a in data["ambiguities"] if a["code"] == "unmapped_name_like")
        assert amb["column"] == "Product Name"
        assert data["requires_review"] is True

    def test_multiple_candidates_ambiguity(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/preview", headers=headers, json={
            "content": "Name,Guest Name,Phone\nAlice,Bob,+1-555-0101\n",
            "content_type": "csv", "target_type": "customer",
        })
        data = resp.get_json()["data"]
        amb = next(a for a in data["ambiguities"] if a["code"] == "multiple_candidates")
        assert amb["field"] == "display_name"
        assert set(amb["columns"]) == {"Name", "Guest Name"}
        assert amb["chosen"] == "Name"
        # The non-chosen column is marked conflicted and NOT applied
        mapping = {m["source_column"]: m for m in data["column_mapping"]}
        assert mapping["Guest Name"].get("conflict") is True

    def test_manual_override_decides_the_mapping(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/preview", headers=headers, json={
            "content": "Name,Guest Name,Phone\nAlice,Bob,+1-555-0101\n",
            "content_type": "csv", "target_type": "customer",
            "column_overrides": {"Guest Name": "display_name"},
        })
        data = resp.get_json()["data"]
        mapping = {m["source_column"]: m for m in data["column_mapping"]}
        # Human decision reversed the default choice
        assert mapping["Guest Name"]["method"] == "manual"
        assert mapping["Guest Name"].get("conflict") is not True
        assert mapping["Name"].get("conflict") is True
        amb = next(a for a in data["ambiguities"] if a["code"] == "multiple_candidates")
        assert amb["chosen"] == "Guest Name"

    def test_override_can_exclude_column(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/preview", headers=headers, json={
            "content": CUSTOMER_CSV, "content_type": "csv", "target_type": "customer",
            "column_overrides": {"Notes": ""},
        })
        data = resp.get_json()["data"]
        mapping = {m["source_column"]: m for m in data["column_mapping"]}
        assert mapping["Notes"]["target_field"] == ""
        assert mapping["Notes"]["method"] == "manual"
        assert "not" in mapping["Notes"]["reason"]

    def test_fallback_company_as_display_name_is_explained(self, client, auth):
        """A B2B file with only a Company column: explained fallback, not silence."""
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/preview", headers=headers, json={
            "content": "Company,Email\nTaj Travel,taj@example.com\n",
            "content_type": "csv", "target_type": "customer",
        })
        data = resp.get_json()["data"]
        mapping = {m["source_column"]: m for m in data["column_mapping"]}
        assert mapping["Company"]["target_field"] == "display_name"
        assert mapping["Company"]["method"] == "alias_fallback"
        assert "no 'display_name' column" in mapping["Company"]["reason"]


# =========================================================================
# 2. Customer ingestion — realistic column names (A3)
# =========================================================================


class TestCustomerIngestion:

    def test_guest_and_party_name_columns_import(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": "Guest,Party Name,Phone\nAsha Menon,Panchi Club,+91 98450 12345\n",
            "content_type": "csv", "target_type": "customer",
            "column_overrides": {"Guest": "display_name", "Party Name": "company_name"},
            "source_name": "guests.csv",
        })
        assert resp.status_code == 201, resp.get_json()
        body = resp.get_json()
        assert body["data"]["created"] == 1

        from app.relationship.models import CanonicalRelationship
        rel = CanonicalRelationship.query.filter_by(organization_id=org_id).first()
        assert rel is not None
        assert rel.display_name == "Asha Menon"
        assert rel.company_name == "Panchi Club"
        assert rel.relationship_type == "customer"

    def test_customer_import_records_provenance(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": CUSTOMER_CSV, "content_type": "csv", "target_type": "customer",
            "source_name": "customers_q3.csv",
        })
        assert resp.status_code == 201
        data = resp.get_json()["data"]
        assert data["created"] == 2
        assert data["import_session"]

        prov = data["provenance"]
        assert len(prov) == 2
        rec = prov[0]
        assert rec["target_type"] == "customer"
        assert rec["record_id"] and rec["evidence_id"]

    def test_weak_identity_flagged_not_hidden(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/preview", headers=headers, json={
            "content": "Name\nOrphan Row\n",
            "content_type": "csv", "target_type": "customer",
        })
        data = resp.get_json()["data"]
        assert data["weak_identity_rows"] == [1]
        assert data["requires_review"] is True
        rec = data["records"][0]
        assert rec["weak_identity"] is True
        assert any("weak identity" in w for w in rec["warnings"])


# =========================================================================
# 3. Supplier ingestion — similar names never merged (A4/A5)
# =========================================================================


class TestSupplierIngestion:

    def test_supplier_import_with_flexible_columns(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": SUPPLIER_CSV, "content_type": "csv", "target_type": "supplier",
            "source_name": "suppliers.csv",
        })
        assert resp.status_code == 201
        assert resp.get_json()["data"]["created"] == 2

        from app.models import Supplier
        acme = Supplier.query.filter_by(tenant_id=org_id, name="ACME Hotels").first()
        assert acme is not None
        assert acme.category == "hotel"
        assert acme.contact == "John Smith"
        assert acme.payment_terms == "Net 30"

    def test_similar_supplier_name_surfaced_not_merged(self, client, auth):
        org_id, headers = auth
        from app import db
        from app.models import Supplier
        db.session.add(Supplier(name="ACME Hotels", category="hotel",
                                tenant_id=org_id, status="active"))
        db.session.commit()

        resp = client.post("/api/v1/data/import/preview", headers=headers, json={
            "content": "name,category\nACME Hotel,hotel\n",
            "content_type": "csv", "target_type": "supplier",
        })
        data = resp.get_json()["data"]
        rec = data["records"][0]
        # NOT an exact match → create; similar candidate surfaced
        assert rec["identity_action"] == "create"
        assert rec["similar_candidates"], "similar name must be surfaced"
        cand = rec["similar_candidates"][0]
        assert cand["name"] == "ACME Hotels"
        assert cand["similarity"] >= 0.82
        codes = [a["code"] for a in data["ambiguities"]]
        assert "similar_existing_entity" in codes

    def test_exact_supplier_name_matches_with_basis(self, client, auth):
        org_id, headers = auth
        from app import db
        from app.models import Supplier
        db.session.add(Supplier(name="ACME Hotels", category="hotel",
                                tenant_id=org_id, status="active"))
        db.session.commit()

        resp = client.post("/api/v1/data/import/preview", headers=headers, json={
            "content": "name,category\nACME Hotels,hotel\n",
            "content_type": "csv", "target_type": "supplier",
        })
        rec = resp.get_json()["data"]["records"][0]
        assert rec["identity_action"] == "match"
        assert "already exists" in rec["match_basis"]

    def test_similar_but_separate_entities_stay_separate_on_commit(self, client, auth):
        org_id, headers = auth
        from app import db
        from app.models import Supplier
        db.session.add(Supplier(name="ACME Hotels", category="hotel",
                                tenant_id=org_id, status="active"))
        db.session.commit()

        resp = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": "name,category\nACME Hotel,hotel\n",
            "content_type": "csv", "target_type": "supplier",
        })
        assert resp.status_code == 201
        assert resp.get_json()["data"]["created"] == 1
        # Both exist — no silent merge
        assert Supplier.query.filter_by(tenant_id=org_id).count() == 2


# =========================================================================
# 4. Duplicates & conflicts inside one file (A5)
# =========================================================================


class TestDuplicateDetection:

    def test_within_file_duplicate_rejected_with_pointer(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/preview", headers=headers, json={
            "content": "name,email\nAlice,alice@example.com\nAlice Copy,alice@example.com\n",
            "content_type": "csv", "target_type": "customer",
        })
        data = resp.get_json()["data"]
        assert data["possible_duplicates"] == 1
        second = data["records"][1]
        assert second["commit_action"] == "reject"
        assert any("row 1" in e for e in second["errors"])

    def test_conflicting_duplicate_flagged_for_human(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": "name,phone\nAlice Smith,+1-555-0101\nAlice Jones,+1-555-0101\n",
            "content_type": "csv", "target_type": "customer",
        })
        body = resp.get_json()
        data = body["data"]
        # One created; the conflict row rejected — never silently merged
        assert data["created"] == 1
        assert data["rejected"] == 1
        assert any("conflict" in (e.get("error") or "").lower() for e in data["errors"])

    def test_existing_customer_match_basis_explained(self, client, auth):
        org_id, headers = auth
        from app import db
        from app.relationship.models import CanonicalRelationship
        db.session.add(CanonicalRelationship(
            organization_id=org_id, display_name="Asha Menon",
            email="asha@example.com", relationship_type="customer",
            created_by="seed",
        ))
        db.session.commit()

        resp = client.post("/api/v1/data/import/preview", headers=headers, json={
            "content": "Client Name,Email\nAsha M,asha@example.com\n",
            "content_type": "csv", "target_type": "customer",
        })
        rec = resp.get_json()["data"]["records"][0]
        assert rec["identity_action"] == "match"
        assert "asha@example.com" in rec["match_basis"]
        assert "Asha Menon" in rec["match_basis"]


# =========================================================================
# 5. Provenance read surface (A6)
# =========================================================================


class TestProvenance:

    def _import_customer(self, client, headers, source_name="customers.csv"):
        resp = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": "Client Name,Email,City\nAsha Menon,asha@example.com,Mumbai\n",
            "content_type": "csv", "target_type": "customer",
            "source_name": source_name,
        })
        assert resp.status_code == 201
        return resp.get_json()["data"]

    def test_provenance_read_full_chain(self, client, auth):
        org_id, headers = auth
        data = self._import_customer(client, headers, "customers_q3.csv")
        rec = data["provenance"][0]

        resp = client.get(
            f"/api/v1/data/provenance/customer/{rec['record_id']}", headers=headers,
        )
        assert resp.status_code == 200
        prov = resp.get_json()["data"]
        assert prov["has_provenance"] is True
        origin = prov["origin"]
        assert origin["source_name"] == "customers_q3.csv"
        assert origin["source_type"] == "csv"
        assert origin["row"] == 1
        assert origin["import_session"] == data["import_session"]
        assert origin["imported_by"] == "m6_user"
        assert origin["imported_at"]
        assert origin["field_mapping"]["display_name"] == "Client Name"

    def test_provenance_cross_tenant_404(self, client, auth):
        org_id, headers = auth
        data = self._import_customer(client, headers)
        rec = data["provenance"][0]

        from tests.auth_helper import seed_rbac
        from app import db
        other_org = seed_rbac(db, identity_id="m6_other", role_name="owner")
        with client.session_transaction() as s:
            s["identity_id"] = "m6_other"
            s["current_org_id"] = other_org

        resp = client.get(
            f"/api/v1/data/provenance/customer/{rec['record_id']}",
            headers={"X-Identity-Id": "m6_other"},
        )
        assert resp.status_code == 404

    def test_provenance_requires_auth(self, client):
        resp = client.get("/api/v1/data/provenance/customer/1")
        assert resp.status_code == 401


# =========================================================================
# 6. Correction (A7)
# =========================================================================


class TestCorrection:

    def _import_and_get_id(self, client, headers):
        resp = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": "Client Name,Email\nAsha Menon,asha@example.com\n",
            "content_type": "csv", "target_type": "customer",
        })
        return resp.get_json()["data"]["provenance"][0]["record_id"]

    def test_correction_updates_canonical_and_records_audit(self, client, auth):
        org_id, headers = auth
        rid = self._import_and_get_id(client, headers)

        resp = client.post("/api/v1/data/import/correct", headers=headers, json={
            "target_type": "customer", "record_id": rid,
            "field": "display_name", "new_value": "Asha Menon-Rao",
            "reason": "Marriage name change confirmed by the client",
        })
        assert resp.status_code == 200, resp.get_json()
        body = resp.get_json()["data"]
        assert body["ok"] is True
        assert body["correction"]["old_value"] == "Asha Menon"
        assert body["correction"]["new_value"] == "Asha Menon-Rao"
        assert body["correction"]["corrected_by"] == "m6_user"

        from app.relationship.models import CanonicalRelationship
        rel = CanonicalRelationship.query.get(rid)
        assert rel.display_name == "Asha Menon-Rao"

        # Correction appears in the provenance trail
        prov = client.get(
            f"/api/v1/data/provenance/customer/{rid}", headers=headers,
        ).get_json()["data"]
        assert len(prov["corrections"]) == 1
        assert prov["corrections"][0]["field"] == "display_name"
        assert "Marriage" in prov["corrections"][0]["reason"]

    def test_correction_rejects_unknown_field(self, client, auth):
        org_id, headers = auth
        rid = self._import_and_get_id(client, headers)
        resp = client.post("/api/v1/data/import/correct", headers=headers, json={
            "target_type": "customer", "record_id": rid,
            "field": "organization_id", "new_value": "999",
        })
        assert resp.status_code == 400

    def test_correction_cross_tenant_404(self, client, auth):
        org_id, headers = auth
        rid = self._import_and_get_id(client, headers)

        from tests.auth_helper import seed_rbac
        from app import db
        other_org = seed_rbac(db, identity_id="m6_other2", role_name="owner")
        with client.session_transaction() as s:
            s["identity_id"] = "m6_other2"
            s["current_org_id"] = other_org

        resp = client.post("/api/v1/data/import/correct", headers={
            "X-Identity-Id": "m6_other2",
        }, json={
            "target_type": "customer", "record_id": rid,
            "field": "display_name", "new_value": "Hijacked",
        })
        assert resp.status_code == 404

    def test_supplier_correction(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": "name,category\nGlobex Logistics,transport\n",
            "content_type": "csv", "target_type": "supplier",
        })
        rid = resp.get_json()["data"]["provenance"][0]["record_id"]

        resp = client.post("/api/v1/data/import/correct", headers=headers, json={
            "target_type": "supplier", "record_id": rid,
            "field": "category", "new_value": "logistics",
            "reason": "category refined",
        })
        assert resp.status_code == 200

        from app.models import Supplier
        assert Supplier.query.get(rid).category == "logistics"


# =========================================================================
# 7. Recovery — retry idempotency, partial failures (A7)
# =========================================================================


class TestRecovery:

    def test_recommit_is_idempotent_noop(self, client, auth):
        org_id, headers = auth
        payload = {
            "content": CUSTOMER_CSV, "content_type": "csv", "target_type": "customer",
            "source_name": "customers.csv",
        }
        first = client.post("/api/v1/data/import/commit", headers=headers, json=payload)
        assert first.status_code == 201
        assert first.get_json()["data"]["created"] == 2

        second = client.post("/api/v1/data/import/commit", headers=headers, json=payload)
        body = second.get_json()
        assert body["data"]["status"] == "noop"
        assert body["data"]["created"] == 0
        assert body["data"]["duplicates_skipped"] == 2
        assert all(s["basis"] for s in body["data"]["skipped_details"])

        from app.relationship.models import CanonicalRelationship
        assert CanonicalRelationship.query.filter_by(organization_id=org_id).count() == 2

    def test_partial_failure_then_recovery_retry(self, client, auth):
        org_id, headers = auth
        # Row 2 is invalid (no name) → partial
        first = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": "name,email\nGood Row,good@example.com\n,broken@example.com\n",
            "content_type": "csv", "target_type": "customer",
        })
        body = first.get_json()["data"]
        assert body["status"] == "partial"
        assert body["created"] == 1
        assert body["rejected"] == 1

        # Recovery: fix the file (valid row + fixed row), re-commit.
        second = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": "name,email\nGood Row,good@example.com\nFixed Row,broken@example.com\n",
            "content_type": "csv", "target_type": "customer",
        })
        body2 = second.get_json()["data"]
        # Good Row matched (skipped); Fixed Row created. No duplicates.
        assert body2["duplicates_skipped"] == 1
        assert body2["created"] == 1

        from app.relationship.models import CanonicalRelationship
        names = sorted(r.display_name for r in CanonicalRelationship.query.filter_by(
            organization_id=org_id).all())
        assert names == ["Fixed Row", "Good Row"]

    def test_zero_parse_is_not_fake_success(self, client, auth):
        org_id, headers = auth
        resp = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": "this is not parseable json at all", "content_type": "json",
            "target_type": "customer",
        })
        body = resp.get_json()
        assert body["success"] is False
        assert body["data"]["status"] == "rejected"
        assert "zero rows" in body["data"]["warning"] or "check the file format" in body["data"]["warning"]

    def test_commit_requires_column_overrides_to_match_preview(self, client, auth):
        """A commit with overrides produces the SAME interpretation a preview showed."""
        org_id, headers = auth
        overrides = {"Guest": "display_name", "Party Name": "company_name"}
        preview = client.post("/api/v1/data/import/preview", headers=headers, json={
            "content": "Guest,Party Name,Phone\nAsha,Panchi Club,+91 98450 12345\n",
            "content_type": "csv", "target_type": "customer",
            "column_overrides": overrides,
        }).get_json()["data"]
        assert preview["valid_records"] == 1

        commit = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": "Guest,Party Name,Phone\nAsha,Panchi Club,+91 98450 12345\n",
            "content_type": "csv", "target_type": "customer",
            "column_overrides": overrides,
        })
        assert commit.status_code == 201

        from app.relationship.models import CanonicalRelationship
        rel = CanonicalRelationship.query.filter_by(organization_id=org_id).first()
        assert rel.display_name == "Asha"
        assert rel.company_name == "Panchi Club"


# =========================================================================
# 8. Observable outcome — canonical event (A1)
# =========================================================================


class TestObservableOutcome:

    def test_commit_emits_canonical_event(self, client, auth, monkeypatch):
        org_id, headers = auth
        captured = []

        import app.import_export.service as svc

        def fake_emit(**kwargs):
            captured.append(kwargs)

        monkeypatch.setattr(svc, "_emit_import_event", fake_emit)

        resp = client.post("/api/v1/data/import/commit", headers=headers, json={
            "content": "name,email\nAlice,alice@example.com\n",
            "content_type": "csv", "target_type": "customer",
            "source_name": "alice.csv",
        })
        assert resp.status_code == 201
        assert captured, "commit must emit an observable outcome"
        assert captured[0]["target_type"] == "customer"
        assert captured[0]["result"]["created"] == 1
