"""
SHUNYA OS — Extended Test Suite (Unit 10)

Covers: routes, services, pipeline, Telegram webhook.
"""
import jinja2
import pytest
from app.models import Lead, Payment, Invoice, Supplier, ActivityLog
from app.services import parse_inquiry_text, format_inquiry_reply


# ---- Services ----

class TestParseInquiry:
    def test_honeymoon(self):
        r = parse_inquiry_text("3 nights Bali for 2 adults 15 Dec honeymoon")
        assert r["destination"] == "Bali"
        assert r["nights"] == 3
        assert r["adults"] == 2
        assert r["occasion"] == "honeymoon"

    def test_family_with_budget(self):
        r = parse_inquiry_text("family trip Sri Lanka 4 nights 2 adults 2 kids budget 1.5 lakh")
        assert r["destination"] == "Sri Lanka"
        assert r["kids"] == 2
        assert r["budget"] is not None

    def test_goa_short(self):
        r = parse_inquiry_text("Goa for 2 adults")
        assert r["destination"] == "Goa"

    def test_empty(self):
        r = parse_inquiry_text("")
        assert r["destination"] is None


class TestFormatReply:
    def test_rich_reply(self):
        reply = format_inquiry_reply(
            {"destination": "Bali", "nights": 3, "adults": 2, "occasion": "honeymoon"},
            "PC10072601",
        )
        assert "PC10072601" in reply
        assert "Bali" in reply
        assert "3 nights" in reply

    def test_minimal_reply(self):
        reply = format_inquiry_reply({}, "PC10072602")
        assert "PC10072602" in reply


# ---- Routes ----

class TestDashboard:
    def test_dashboard_loads(self, client):
        r = client.get("/")
        # TESTING=True bypasses auth middleware deterministically — always 200
        assert r.status_code == 200
        assert b"SHUNYA" in r.data


class TestLeads:
    def test_list(self, client):
        r = client.get("/leads")
        assert r.status_code == 200

    def test_create_via_form(self, client):
        r = client.post("/leads/new", data={
            "customer_name": "Test", "destination": "Goa",
            "phone": "+919999", "budget": "50000",
        }, follow_redirects=True)
        assert r.status_code == 200

    def test_status_update(self, client):
        # Create lead first
        client.post("/leads/new", data={"customer_name": "T", "destination": "D"}, follow_redirects=True)
        lead = Lead.query.first()
        r = client.post(f"/leads/{lead.id}/status", data={"status": "in_progress"}, follow_redirects=True)
        assert r.status_code == 200
        lead = Lead.query.get(lead.id)
        assert lead.status == "in_progress"

    def test_activity_logged_on_create(self, client):
        client.post("/leads/new", data={"customer_name": "A", "destination": "B"}, follow_redirects=True)
        assert ActivityLog.query.count() >= 1


class TestPayments:
    def test_create_payment(self, client):
        client.post("/leads/new", data={"customer_name": "T", "destination": "D"}, follow_redirects=True)
        lead = Lead.query.first()
        r = client.post("/payments", data={
            "lead_id": str(lead.id), "amount": "50000",
            "type": "guest_payment", "method": "bank",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert Payment.query.count() == 1


class TestInvoices:
    def test_create_invoice(self, client):
        client.post("/leads/new", data={"customer_name": "T", "destination": "D"}, follow_redirects=True)
        lead = Lead.query.first()
        r = client.post("/invoices", data={
            "lead_id": str(lead.id), "invoice_number": "INV-001",
            "total_amount": "10000", "tax": "1800", "discount": "0",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert Invoice.query.count() >= 1


class TestTelegramWebhook:
    def test_happy_path(self, client):
        r = client.post("/telegram/webhook", json={
            "message": {"text": "3 nights Bali for 2 adults honeymoon", "chat": {"id": "12345"}},
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["method"] == "sendMessage"
        assert "PC" in data["text"]
        assert "Bali" in data["text"]

    def test_empty(self, client):
        r = client.post("/telegram/webhook", json={
            "message": {"text": "", "chat": {"id": "1"}},
        })
        assert r.status_code == 200
        assert r.get_json()["status"] == "ignored"

    def test_lead_created(self, client):
        client.post("/telegram/webhook", json={
            "message": {"text": "Kerala 5 nights 2 adults", "chat": {"id": "999"}},
        })
        lead = Lead.query.filter_by(phone="999").first()
        assert lead is not None
        assert "Kerala" in (lead.destination or "")

    def test_activity_logged(self, client):
        client.post("/telegram/webhook", json={
            "message": {"text": "Goa 3 nights", "chat": {"id": "777"}},
        })
        assert ActivityLog.query.filter_by(action="created").count() >= 1


class TestSettings:
    def test_page_loads(self, client):
        # Settings is an open route — no auth in test mode, template handles None user gracefully
        r = client.get("/settings")
        assert r.status_code == 200

    def test_add_supplier(self, client):
        r = client.post("/settings", data={
            "name": "Test Hotel", "category": "hotel",
            "city": "Goa", "gstin": "22AAAAA0000A1Z5",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert Supplier.query.count() == 1


class TestAPI:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_shunya_knowledge(self, client):
        r = client.get("/shunya/knowledge")
        assert r.status_code == 200
        assert "knowledge_base_length" in r.get_json()

    def test_shunya_process(self, client):
        r = client.post("/shunya/process", json={
            "customer_name": "Test", "destination": "Bali",
            "pax": "2", "dates": "15-20 Dec",
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True
        assert data["destination"] == "Bali"


class TestActivitiesAPI:
    def test_activities_endpoint(self, client):
        client.post("/telegram/webhook", json={
            "message": {"text": "test", "chat": {"id": "1"}},
        })
        lead = Lead.query.first()
        r = client.get(f"/leads/{lead.id}/activities")
        assert r.status_code == 200
        data = r.get_json()
        assert len(data) >= 1


class Test404:
    def test_api_404_returns_json(self, client):
        r = client.get("/shunya/nonexistent")
        # custom_404 delegates API paths to JSON response
        assert r.status_code == 404
        data = r.get_json()
        assert data is not None
        assert "error" in data

    def test_ui_404_returns_html(self, client):
        r = client.get("/nonexistent-ui-route")
        assert r.status_code == 404