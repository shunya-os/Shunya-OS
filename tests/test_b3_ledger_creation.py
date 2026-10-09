"""B3 — Ledger record creation (SH-M6→M15 Stage B, Ledger).

The product must offer a real user-facing path to create supported ledger
records and find them again, tenant-safely. The Finance workspace now records
invoices and payments through the canonical finance service.

These tests also guard the two live defects fixed alongside:
  * direct invoice creation previously raised ImportError
    (`from app.models import Relationship` — removed in consolidation) → 500;
  * the invoice list previously 500'd whenever any invoice had a
    relationship_id (same import inside the loop).
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
    from tests.auth_helper import seed_rbac
    from app import db
    org_id = seed_rbac(db, identity_id="b3_user", role_name="owner")
    with client.session_transaction() as s:
        s["identity_id"] = "b3_user"
        s["current_org_id"] = org_id
    return org_id, {"X-Identity-Id": "b3_user"}


class TestInvoiceCreation:

    def test_direct_invoice_creation(self, client, auth):
        """The user-facing creation path records a draft invoice."""
        org_id, _ = auth
        resp = client.post("/api/v1/finance/invoices", json={
            "customer_name": "Taj Travel Co",
            "amount": 1500.50,
            "currency": "INR",
            "description": "Advance for Bali itinerary",
        })
        assert resp.status_code == 201, resp.get_data(as_text=True)
        inv = resp.get_json()["invoice"]
        assert inv["number"].startswith("INV-")
        assert inv["status"] == "draft"
        assert inv["total_amount"] == 1500.5
        assert inv["currency"] == "INR"
        assert inv["relationship_id"], "invoice must link to the (canonical) customer"

    def test_invoice_creates_canonical_customer(self, client, auth):
        """The linked customer is a CanonicalRelationship, not the removed legacy model."""
        org_id, _ = auth
        client.post("/api/v1/finance/invoices", json={
            "customer_name": "Panchi Club", "amount": 100,
        })
        from app.relationship.models import CanonicalRelationship
        rel = CanonicalRelationship.query.filter_by(
            organization_id=org_id, display_name="Panchi Club").first()
        assert rel is not None
        assert rel.relationship_type == "customer"

    def test_invoice_list_populates_relationship_name(self, client, auth):
        """REGRESSION — the list used to raise ImportError (500) for linked invoices."""
        org_id, _ = auth
        client.post("/api/v1/finance/invoices", json={
            "customer_name": "Globex Ltd", "amount": 999,
        })
        resp = client.get("/api/v1/finance/invoices")
        assert resp.status_code == 200, resp.get_data(as_text=True)
        rows = resp.get_json()["invoices"]
        assert len(rows) == 1
        assert rows[0]["relationship_name"] == "Globex Ltd"

    def test_invoice_validation(self, client, auth):
        """Source values preserved; invalid inputs refused clearly."""
        org_id, _ = auth
        r = client.post("/api/v1/finance/invoices", json={"amount": 10})
        assert r.status_code == 400  # customer_name required
        r = client.post("/api/v1/finance/invoices", json={
            "customer_name": "X", "amount": 0,
        })
        assert r.status_code == 400  # amount must be positive

    def test_invoice_unauthenticated(self, client):
        resp = client.post("/api/v1/finance/invoices", json={
            "customer_name": "X", "amount": 10,
        })
        assert resp.status_code == 401


class TestPayment:

    def _invoice(self, client, org_id, amount=1000):
        resp = client.post("/api/v1/finance/invoices", json={
            "customer_name": "Payment Test Co", "amount": amount,
        })
        assert resp.status_code == 201
        return resp.get_json()["invoice"]["id"]

    def test_record_payment(self, client, auth):
        org_id, _ = auth
        inv_id = self._invoice(client, org_id, amount=1000)
        resp = client.post("/api/v1/finance/payments", json={
            "invoice_id": inv_id, "amount": 400, "method": "bank_transfer",
        })
        assert resp.status_code == 201, resp.get_data(as_text=True)
        body = resp.get_json()
        assert body["payment"]["amount"] == 400.0
        assert body["invoice"]["paid_amount"] == 400.0
        assert body["invoice"]["status"] == "draft"  # partially paid

    def test_full_payment_marks_paid(self, client, auth):
        org_id, _ = auth
        inv_id = self._invoice(client, org_id, amount=500)
        resp = client.post("/api/v1/finance/payments", json={
            "invoice_id": inv_id, "amount": 500, "method": "upi",
        })
        assert resp.status_code == 201
        assert resp.get_json()["invoice"]["status"] == "paid"

    def test_payment_exceeding_total_rejected(self, client, auth):
        org_id, _ = auth
        inv_id = self._invoice(client, org_id, amount=100)
        resp = client.post("/api/v1/finance/payments", json={
            "invoice_id": inv_id, "amount": 150,
        })
        assert resp.status_code == 400
        assert "exceed" in resp.get_json()["error"].lower()

    def test_payment_requires_auth(self, client):
        resp = client.post("/api/v1/finance/payments", json={
            "invoice_id": 1, "amount": 10,
        })
        assert resp.status_code == 401


class TestTenantIsolation:

    def test_invoices_scoped_to_org(self, client, auth):
        org_id, _ = auth
        client.post("/api/v1/finance/invoices", json={
            "customer_name": "Org A Customer", "amount": 321,
        })

        from tests.auth_helper import seed_rbac
        from app import db
        other_org = seed_rbac(db, identity_id="b3_other", role_name="owner")
        with client.session_transaction() as s:
            s["identity_id"] = "b3_other"
            s["current_org_id"] = other_org

        resp = client.get("/api/v1/finance/invoices")
        assert resp.status_code == 200
        assert resp.get_json()["invoices"] == []

        # Cross-org payment attempt must not find the invoice
        from app.finance.models import FinInvoice
        inv = FinInvoice.query.filter_by(organization_id=org_id).first()
        assert inv is not None
        resp = client.post("/api/v1/finance/payments", json={
            "invoice_id": inv.id, "amount": 1,
        })
        assert resp.status_code == 400
        assert "not found" in resp.get_json()["error"].lower()
