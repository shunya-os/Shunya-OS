"""FDA14 — Marketing OS tests.

Campaign CRUD, audience definitions, content planning, lead capture, approvals.
"""
import pytest


class TestCampaigns:
    def test_create_campaign(self, app, client):
        r = client.post("/api/v1/marketing/campaigns", json={
            "name": "Summer Campaign", "tenant_id": 1,
            "objective": "leads", "budget": 5000,
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["name"] == "Summer Campaign"
        assert data["status"] == "draft"

    def test_list_campaigns(self, app, client):
        r = client.get("/api/v1/marketing/campaigns?tenant_id=1")
        assert r.status_code == 200
        data = r.get_json()
        assert "campaigns" in data

    def test_get_campaign(self, app, client):
        r = client.post("/api/v1/marketing/campaigns", json={
            "name": "Get Test", "tenant_id": 1,
        })
        cid = r.get_json()["id"]
        r = client.get(f"/api/v1/marketing/campaigns/{cid}?tenant_id=1")
        assert r.status_code == 200
        assert r.get_json()["name"] == "Get Test"

    def test_update_campaign(self, app, client):
        r = client.post("/api/v1/marketing/campaigns", json={
            "name": "Update Test", "tenant_id": 1,
        })
        cid = r.get_json()["id"]
        r = client.patch(f"/api/v1/marketing/campaigns/{cid}?tenant_id=1", json={
            "status": "active",
        })
        assert r.status_code == 200
        assert r.get_json()["status"] == "active"

    def test_delete_campaign(self, app, client):
        r = client.post("/api/v1/marketing/campaigns", json={
            "name": "Delete Me", "tenant_id": 1,
        })
        cid = r.get_json()["id"]
        r = client.delete(f"/api/v1/marketing/campaigns/{cid}?tenant_id=1")
        assert r.status_code == 200
        assert r.get_json()["deleted"] is True


class TestAudiences:
    def test_create_audience(self, app, client):
        r = client.post("/api/v1/marketing/campaigns", json={
            "name": "Audience Campaign", "tenant_id": 1,
        })
        cid = r.get_json()["id"]
        r = client.post("/api/v1/marketing/audiences", json={
            "campaign_id": cid, "name": "Travel Enthusiasts",
            "tenant_id": 1,
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["name"] == "Travel Enthusiasts"

    def test_list_audiences(self, app, client):
        r = client.get("/api/v1/marketing/audiences?tenant_id=1")
        assert r.status_code == 200
        data = r.get_json()
        assert "audiences" in data


class TestContent:
    def test_create_content(self, app, client):
        r = client.post("/api/v1/marketing/campaigns", json={
            "name": "Content Campaign", "tenant_id": 1,
        })
        cid = r.get_json()["id"]
        r = client.post("/api/v1/marketing/content", json={
            "campaign_id": cid, "title": "Ad Post",
            "content_type": "post", "tenant_id": 1,
        })
        assert r.status_code == 201
        assert r.get_json()["status"] == "draft"

    def test_approve_content(self, app, client):
        r = client.post("/api/v1/marketing/campaigns", json={
            "name": "Approve Campaign", "tenant_id": 1,
        })
        cid = r.get_json()["id"]
        r = client.post("/api/v1/marketing/content", json={
            "campaign_id": cid, "title": "Approve Me",
            "tenant_id": 1,
        })
        cid2 = r.get_json()["id"]
        r = client.post(f"/api/v1/marketing/content/{cid2}/approve?tenant_id=1", json={
            "approver": "manager_1",
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["content_status"] == "pending_review"


class TestLeadCapture:
    def test_capture_lead_from_campaign(self, app, client):
        r = client.post("/api/v1/marketing/campaigns", json={
            "name": "Lead Campaign", "tenant_id": 1,
        })
        cid = r.get_json()["id"]
        r = client.post("/api/v1/marketing/capture-lead", json={
            "tenant_id": 1, "name": "Campaign Lead",
            "phone": "+1-555-CAMP", "email": "camp@test.com",
            "campaign_id": cid, "utm_source": "google",
            "utm_campaign": "summer",
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["success"] is True
        assert data["code"] is not None

    def test_capture_lead_without_campaign(self, app, client):
        r = client.post("/api/v1/marketing/capture-lead", json={
            "tenant_id": 1, "name": "Direct Lead",
            "phone": "+1-555-DIRECT", "email": "direct@test.com",
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["success"] is True


class TestTenantIsolation:
    def test_campaign_tenant_isolation(self, app, client):
        r = client.post("/api/v1/marketing/campaigns", json={
            "name": "Tenant A Campaign", "tenant_id": 1,
        })
        cid = r.get_json()["id"]
        # Tenant 2 should not see it
        r = client.get(f"/api/v1/marketing/campaigns/{cid}?tenant_id=2")
        assert r.status_code == 404