"""GATE 16 — Behavioral tenancy for new capabilities.

Creates real org/member context within app.app_context() so session-based
authorization resolves correctly. Uses owner role (grants all perms).
"""

import pytest

ORG_A, ORG_B = 800, 801
ALICE = "g16-alice@example.com"
BOB = "g16-bob@example.com"


@pytest.fixture(scope="module")
def app():
    from app import create_app, db
    _app = create_app({
        "TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    with _app.app_context():
        db.create_all()
        from app.models import Organization, OrgMember
        for oid, name in ((ORG_A, ALICE), (ORG_B, BOB)):
            org = Organization(id=oid, name=f"G16 Org {oid}",
                               slug=f"g16-org-{oid}", is_active=True)
            db.session.add(org)
            db.session.flush()
            member = OrgMember(organization_id=oid, identity_id=name,
                               role="owner", is_active=True)
            db.session.add(member)
        db.session.commit()
    return _app


@pytest.fixture
def client(app):
    return app.test_client()


# =========================================================================
# 1. CUSTOMER
# =========================================================================

class TestCustomerTenancy:

    def test_alice_gets_own(self, app, client):
        with app.app_context():
            from app import db
            from app.customers.models import Customer
            c = Customer(name="Alice Cust", email="alice@test.com", tenant_id=ORG_A)
            db.session.add(c)
            db.session.commit()
            cid = c.id
        with client.session_transaction() as sess:
            sess["identity_id"] = ALICE
            sess["current_org_id"] = ORG_A
        r = client.get(f"/api/v1/customers/{cid}")
        assert r.status_code == 200, r.get_json()

    def test_bob_denied_on_alice(self, app, client):
        with app.app_context():
            from app import db
            from app.customers.models import Customer
            c = Customer(name="Alice Secret", email="secret@test.com", tenant_id=ORG_A)
            db.session.add(c)
            db.session.commit()
            cid = c.id
        with client.session_transaction() as sess:
            sess["identity_id"] = BOB
            sess["current_org_id"] = ORG_B
        r = client.get(f"/api/v1/customers/{cid}")
        assert r.status_code == 404, f"Cross-tenant should 404, got {r.status_code}"

    def test_anonymous_denied(self, client):
        r = client.post("/api/v1/customers/", json={"name": "anon"})
        assert r.status_code in (401, 403, 404)


# =========================================================================
# 2. SUPPLIER
# =========================================================================

class TestSupplierTenancy:

    def test_alice_gets_own(self, app, client):
        with app.app_context():
            from app import db
            from app.models import Supplier
            s = Supplier(name="Alice Supp", category="hotel", tenant_id=ORG_A)
            db.session.add(s)
            db.session.commit()
            sid = s.id
        with client.session_transaction() as sess:
            sess["identity_id"] = ALICE
            sess["current_org_id"] = ORG_A
        r = client.get(f"/api/v1/suppliers/{sid}")
        assert r.status_code == 200, r.get_json()

    def test_bob_denied_on_alice(self, app, client):
        with app.app_context():
            from app import db
            from app.models import Supplier
            s = Supplier(name="Alice Secret Supp", category="hotel", tenant_id=ORG_A)
            db.session.add(s)
            db.session.commit()
            sid = s.id
        with client.session_transaction() as sess:
            sess["identity_id"] = BOB
            sess["current_org_id"] = ORG_B
        r = client.get(f"/api/v1/suppliers/{sid}")
        assert r.status_code == 404, f"Cross-tenant should 404, got {r.status_code}"


# =========================================================================
# 3. DOCUMENT
# =========================================================================

class TestDocumentTenancy:

    def test_alice_gets_own(self, app, client):
        with app.app_context():
            from app import db
            from app.models import Document
            d = Document(filename="test.txt", file_path="/tmp/test.txt",
                         file_type="text/plain", extracted_text="hello",
                         tenant_id=ORG_A, uploaded_by=ALICE, classification="text")
            db.session.add(d)
            db.session.commit()
            did = d.id
        with client.session_transaction() as sess:
            sess["identity_id"] = ALICE
            sess["current_org_id"] = ORG_A
        r = client.get(f"/api/v1/documents/{did}")
        assert r.status_code == 200, r.get_json()

    def test_bob_denied_on_alice(self, app, client):
        with app.app_context():
            from app import db
            from app.models import Document
            d = Document(filename="secret.txt", file_path="/tmp/secret.txt",
                         file_type="text/plain", extracted_text="secret",
                         tenant_id=ORG_A, uploaded_by=ALICE, classification="text")
            db.session.add(d)
            db.session.commit()
            did = d.id
        with client.session_transaction() as sess:
            sess["identity_id"] = BOB
            sess["current_org_id"] = ORG_B
        r = client.get(f"/api/v1/documents/{did}")
        assert r.status_code in (404, 403), f"Cross-tenant should be denied, got {r.status_code}"


# =========================================================================
# 4. CONTENT
# =========================================================================

class TestContentTenancy:

    def test_cross_identity_denied(self, app, client):
        with app.app_context():
            from app import db
            from app.integration.models import ContentGeneration
            c = ContentGeneration(identity_id=ALICE, content_type="blog_post",
                                   prompt="test", generated_content="body",
                                   lifecycle_status="active")
            db.session.add(c)
            db.session.commit()
            cid = c.id
        with client.session_transaction() as sess:
            sess["identity_id"] = BOB
            sess["current_org_id"] = ORG_B
        r = client.get(f"/api/v1/content/history/{cid}")
        assert r.status_code == 404, f"Cross-identity should 404, got {r.status_code}"


# =========================================================================
# 5. EMOTIONAL
# =========================================================================

class TestEmotionalTenancy:

    def test_anonymous_denied(self, client):
        r = client.post("/api/v1/emotional/",
                        json={"expression_type": "frustration", "context": "test"})
        assert r.status_code in (401, 403), f"Expected 401/403 for anonymous, got {r.status_code}"


# =========================================================================
# 6. OUTCOME
# =========================================================================

class TestOutcomeTenancy:

    def test_anonymous_cannot_create(self, client):
        r = client.post("/api/v1/outcomes/", json={"intention": "test"})
        assert r.status_code in (401, 403, 404)