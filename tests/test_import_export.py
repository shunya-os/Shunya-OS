"""ZGC-05 Workstream C — Real Data Entry (Import) Tests.

Required behaviour:
  Upload CSV/XLSX/JSON → preview → validate → deduplicate → import
  → see records grouped into canonical people/companies/work.
"""

import pytest
from app import db


class TestImportPreview:
    """Test the import preview API (/api/v1/data/import/preview)."""

    CSV_VALID = "customer_name,phone,email\nTest User,+911234567890,test@example.com\nSecond User,+919876543210,second@example.com"

    def _login(self, client):
        """Helper: create team member and set session."""
        from app.auth import TeamMember
        from app.auth_routes import UserRole
        from app.models import Organization, OrgMember
        member = TeamMember(
            name="Import Test",
            email="import-preview@shunya.org",
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        member.set_password("testpass123")
        db.session.add(member)
        db.session.commit()
        # Create an org + membership for the auth check
        org = Organization(name="Import Org", slug="import-org-preview")
        db.session.add(org)
        db.session.commit()
        om = OrgMember(
            organization_id=org.id,
            identity_id="sid_import_preview",
            email=member.email,
            role="admin",
        )
        db.session.add(om)
        db.session.commit()
        with client.session_transaction() as sess:
            sess["user_id"] = member.id
            sess["identity_id"] = "sid_import_preview"
            sess["current_org_id"] = org.id
        return member

    def test_import_preview_valid_csv(self, app, client):
        """Valid CSV returns preview without writing."""
        self._login(client)
        resp = client.post("/api/v1/data/import/preview", json={
            "content": self.CSV_VALID,
            "content_type": "csv",
            "target_type": "lead",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        preview = data["data"]
        assert preview["total_records"] == 2
        assert preview["valid_records"] == 2
        assert preview["invalid_records"] == 0

    def test_import_preview_empty_content(self, app, client):
        """Empty content returns 400."""
        self._login(client)
        resp = client.post("/api/v1/data/import/preview", json={
            "content": "",
            "content_type": "csv",
            "target_type": "lead",
        })
        assert resp.status_code == 400

    def test_import_preview_malformed_csv(self, app, client):
        """Malformed CSV returns preview with invalid records marked."""
        self._login(client)
        resp = client.post("/api/v1/data/import/preview", json={
            "content": "customer_name,phone,email\n,,\nBad,NoPhone,",
            "content_type": "csv",
            "target_type": "lead",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        preview = data["data"]
        assert preview["total_records"] == 2
        assert preview["valid_records"] < 2  # At least one should be invalid

    def test_import_preview_json_content(self, app, client):
        """JSON content is accepted."""
        self._login(client)
        resp = client.post("/api/v1/data/import/preview", json={
            "content": '[{"customer_name": "JSON Test", "phone": "+911111111111", "email": "json@test.com"}]',
            "content_type": "json",
            "target_type": "lead",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["total_records"] == 1

    def test_import_preview_requires_auth(self, app, client):
        """Without auth, the endpoint returns 401."""
        resp = client.post("/api/v1/data/import/preview", json={
            "content": self.CSV_VALID,
            "content_type": "csv",
            "target_type": "lead",
        })
        assert resp.status_code == 401


class TestImportCommit:
    """Test the import commit API (/api/v1/data/import/commit)."""

    CSV_VALID = "customer_name,phone,email\nImport Test,+911111111111,import@test.com"

    def _login(self, client):
        """Helper: create team member and set session."""
        from app.auth import TeamMember
        from app.auth_routes import UserRole
        member = TeamMember(
            name="Import Test",
            email="import-test@shunya.org",
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        member.set_password("testpass123")
        db.session.add(member)
        db.session.commit()
        with client.session_transaction() as sess:
            sess["user_id"] = member.id
        return member

    def test_import_commit_success(self, app, client):
        """Valid CSV commit returns success with created count."""
        self._login(client)
        with app.app_context():
            from app.models import Organization
            org = Organization(name="Import Org", slug="import-org-c")
            db.session.add(org)
            db.session.commit()
            with client.session_transaction() as sess:
                sess["current_org_id"] = org.id
                sess["identity_id"] = "sid_import_test"

        resp = client.post("/api/v1/data/import/commit", json={
            "content": self.CSV_VALID,
            "content_type": "csv",
            "target_type": "lead",
        })
        assert resp.status_code in (200, 201)
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["status"] in ("completed", "partial")

    def test_import_commit_requires_auth(self, app, client):
        """Without auth, commit returns 401."""
        resp = client.post("/api/v1/data/import/commit", json={
            "content": self.CSV_VALID,
            "content_type": "csv",
            "target_type": "lead",
        })
        assert resp.status_code == 401


class TestExport:
    """Test the export API (/api/v1/data/export)."""

    def test_export_requires_auth(self, app, client):
        """Without auth, export returns 401."""
        resp = client.post("/api/v1/data/export", json={
            "target_type": "lead",
            "format": "json",
        })
        assert resp.status_code == 401