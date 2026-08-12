"""FDA15 — Marketing Intelligence tests.

Attribution, conversion, channel comparison, revenue trace, experiments.
"""
import pytest


class TestAttribution:
    def test_attribution_returns_chain(self, app, client):
        """Campaign → lead → customer chain is traceable."""
        from app.marketing_os.service import capture_lead, create_campaign
        from app.crm.service import convert_to_customer
        from app.marketing_intelligence.service import get_attribution
        with app.app_context():
            camp = create_campaign(name="Attribution Test", tenant_id=1)
            result = capture_lead(tenant_id=1, name="Attr Lead",
                                  phone="+1-555-ATTR", email="attr@test.com",
                                  campaign_id=camp.id, utm_source="facebook")
            from app.models import Lead
            lead = Lead.query.get(result["lead_id"])
            convert_to_customer(lead, 1)
            attr = get_attribution(camp.id, 1)
            assert attr["leads_count"] >= 1
            assert attr["campaign"] == "Attribution Test"

    def test_attribution_unknown_campaign(self, app, client):
        from app.marketing_intelligence.service import get_attribution
        result = get_attribution(999999, 1)
        assert "error" in result


class TestConversion:
    def test_conversion_rates(self, app, client):
        from app.marketing_intelligence.service import get_conversion
        result = get_conversion(1)
        assert "total_leads" in result
        assert "won_rate" in result


class TestChannelComparison:
    def test_compare_channels(self, app, client):
        from app.marketing_intelligence.service import compare_channels
        result = compare_channels(1)
        assert isinstance(result, list)


class TestRevenueTrace:
    def test_revenue_trace_from_customer(self, app, client):
        from app.marketing_os.service import capture_lead, create_campaign
        from app.crm.service import convert_to_customer
        from app.marketing_intelligence.service import revenue_trace
        with app.app_context():
            camp = create_campaign(name="Revenue Trace", tenant_id=1)
            result = capture_lead(tenant_id=1, name="Rev Lead",
                                  phone="+1-555-REV", email="rev@test.com",
                                  campaign_id=camp.id)
            from app.models import Lead
            lead = Lead.query.get(result["lead_id"])
            cust = convert_to_customer(lead, 1)
            trace = revenue_trace(cust.id, 1)
            assert trace is not None
            assert trace.get("lead") is not None
            assert trace["lead"]["code"] == lead.code
            assert trace["campaign"]["name"] == "Revenue Trace"

    def test_revenue_trace_unknown_customer(self, app, client):
        from app.marketing_intelligence.service import revenue_trace
        trace = revenue_trace(999999, 1)
        assert trace is None


class TestWasteDetection:
    def test_waste_detection(self, app, client):
        from app.marketing_os.service import create_campaign
        from app.marketing_intelligence.service import get_waste
        with app.app_context():
            camp = create_campaign(name="Waste Test", tenant_id=1, budget=1000)
            result = get_waste(camp.id, 1)
            assert "campaign" in result
            assert "recommendation" in result


class TestCAC:
    def test_cac_calculation(self, app, client):
        from app.marketing_intelligence.service import get_cac
        result = get_cac(1)
        assert "cac" in result
        assert "note" in result


class TestExperiments:
    def test_create_experiment(self, app, client):
        from app.marketing_os.service import create_campaign
        with app.app_context():
            camp = create_campaign(name="Exp Campaign", tenant_id=1)
            cid = camp.id
        r = client.post("/api/v1/analytics/experiments", json={
            "campaign_id": cid, "name": "A/B Test",
            "hypothesis": "New design converts better",
            "variant": "A", "metric": "conversion",
            "tenant_id": 1,
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["name"] == "A/B Test"

    def test_list_experiments(self, app, client):
        r = client.get("/api/v1/analytics/experiments?tenant_id=1")
        assert r.status_code == 200
        data = r.get_json()
        assert "experiments" in data

    def test_update_experiment(self, app, client):
        from app.marketing_os.service import create_campaign
        with app.app_context():
            camp = create_campaign(name="Exp Update", tenant_id=1)
            cid = camp.id
        r = client.post("/api/v1/analytics/experiments", json={
            "campaign_id": cid, "name": "Update Experiment",
            "tenant_id": 1,
        })
        eid = r.get_json()["id"]
        r = client.patch(f"/api/v1/analytics/experiments/{eid}", json={
            "status": "running", "confidence": 0.85,
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "running"