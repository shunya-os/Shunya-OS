"""Tests for API routes."""
import json
import io


class TestHealth:
    def test_health_endpoint(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.get_json()
        assert "status" in data
        assert "database" in data

    def test_health_diagnostics(self, client):
        r = client.get("/health")
        data = r.get_json()
        assert "response_ms" in data
        assert "version" in data


class TestBrandAPI:
    def test_get_brand(self, logged_in_client):
        r = logged_in_client.get("/admin/api/brand")
        assert r.status_code == 200
        data = r.get_json()
        assert "company_name" in data

    def test_update_brand(self, logged_in_client):
        r = logged_in_client.post("/admin/api/brand", json={
            "company_name": "Updated Name",
            "brand_tagline": "New tagline",
            "brand_color": "#ff0000",
            "brand_color_secondary": "#00ff00",
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data.get("success") is True

    def test_get_brand_unauthenticated(self, client):
        r = client.get("/admin/api/brand")
        assert r.status_code == 302  # redirect to login


class TestThemeAPI:
    def test_get_default_theme(self, logged_in_client):
        r = logged_in_client.get("/admin/api/theme/default")
        assert r.status_code == 200

    def test_set_default_theme(self, logged_in_client):
        r = logged_in_client.post("/admin/api/theme/default", json={
            "theme": "playful"
        })
        assert r.status_code == 200


class TestTeamAPI:
    def test_list_team(self, logged_in_client):
        r = logged_in_client.get("/admin/api/team")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)


class TestEntityAPI:
    def test_list_entities_empty(self, logged_in_client):
        r = logged_in_client.get("/api/entities/lead")
        assert r.status_code == 200
        data = r.get_json()
        assert "data" in data or "entities" in data or isinstance(data, dict)

    def test_create_entity(self, logged_in_client, lead_definition):
        r = logged_in_client.post("/api/entities/lead", json={
            "name": "API Lead",
            "email": "api@test.com",
        })
        assert r.status_code in (200, 201)
        data = r.get_json()
        assert data is not None


class TestImportAPI:
    def test_import_page(self, logged_in_client):
        r = logged_in_client.get("/admin/import")
        assert r.status_code == 200

    def test_import_inspect_csv(self, logged_in_client):
        data = {"entity_type": "lead", "json_data": '[{"name":"Test","email":"t@t.com"}]'}
        r = logged_in_client.post("/admin/api/import/inspect", data=data)
        assert r.status_code == 200
        result = r.get_json()
        assert result["total_rows"] >= 1

    def test_import_inspect_no_data(self, logged_in_client):
        r = logged_in_client.post("/admin/api/import/inspect", data={"entity_type": "lead"})
        assert r.status_code == 400


class TestOwnerDashboard:
    def test_owner_page(self, logged_in_client):
        r = logged_in_client.get("/owner")
        assert r.status_code == 200


class TestOnboarding:
    def test_onboarding_page(self, logged_in_client):
        r = logged_in_client.get("/onboarding")
        assert r.status_code == 200