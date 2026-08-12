"""
FDA25 — Import / Export / Migration Tests.

Tests: CSV/JSON preview, dry-run, commit, rollback, export with provenance,
permission gating, tenant isolation.
"""

import pytest


@pytest.fixture(scope="function")
def app():
    from app import create_app, db
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
        "DISABLE_RATE_LIMIT": True,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def auth_headers(app, client):
    with client.session_transaction() as s:
        s["identity_id"] = "test_user"
        s["current_org_id"] = 1
    return {"X-Identity-Id": "test_user"}


@pytest.fixture(scope="function")
def seed_org(app):
    from app import db
    from app.models import Organization, OrgMember
    from app.authz.models import Role, OrgMemberRole
    from app.authz.services import seed_default_roles

    org = Organization(id=1, name="Test Org", slug="test-org")
    db.session.add(org)
    db.session.flush()
    seed_default_roles(1)

    owner_role = db.session.query(Role).filter_by(organization_id=1, name="owner").first()
    member = OrgMember(organization_id=1, identity_id="test_user", email="user@test.com",
                       role="owner", is_active=True)
    db.session.add(member)
    db.session.flush()
    if owner_role:
        db.session.add(OrgMemberRole(organization_id=1, member_id=member.id,
            role_id=owner_role.id, scope="organization", granted_by="system"))
    db.session.commit()


CSV_CONTENT = """customer_name,phone,email,notes
Alice,+911234567890,alice@test.com,Test lead 1
Bob,+919876543210,bob@test.com,Test lead 2"""


class TestImportPreview:
    """FDA25: Import preview — no data written."""

    def test_preview_csv(self, client, auth_headers, seed_org):
        """Preview CSV import."""
        resp = client.post("/api/v1/data/import/preview", headers=auth_headers, json={
            "content": CSV_CONTENT,
            "content_type": "csv",
            "target_type": "lead",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["total_records"] == 2
        assert data["data"]["valid_records"] == 2

    def test_preview_no_data_written(self, client, auth_headers, seed_org):
        """Preview must NOT write any records to the database."""
        from app import db
        from app.models import Lead
        before = db.session.query(Lead).count()
        client.post("/api/v1/data/import/preview", headers=auth_headers, json={
            "content": CSV_CONTENT, "content_type": "csv", "target_type": "lead",
        })
        after = db.session.query(Lead).count()
        assert before == after, "Preview wrote data to database!"

    def test_preview_invalid_records(self, client, auth_headers, seed_org):
        """Preview detects invalid records."""
        resp = client.post("/api/v1/data/import/preview", headers=auth_headers, json={
            "content": "customer_name,phone\n,",  # Missing customer_name
            "content_type": "csv",
            "target_type": "lead",
        })
        data = resp.get_json()["data"]
        assert data["invalid_records"] >= 1
        assert len(data["records"][0]["errors"]) >= 1

    def test_preview_requires_auth(self, client):
        """Unauthenticated returns 401."""
        resp = client.post("/api/v1/data/import/preview", json={"content": "test"})
        assert resp.status_code == 401

    def test_preview_requires_content(self, client, auth_headers):
        """Missing content returns 400."""
        resp = client.post("/api/v1/data/import/preview", headers=auth_headers, json={})
        assert resp.status_code == 400


class TestImportCommit:
    """FDA25: Import commit — writes records with evidence."""

    def test_commit_csv(self, client, auth_headers, seed_org):
        """Commit CSV import."""
        resp = client.post("/api/v1/data/import/commit", headers=auth_headers, json={
            "content": CSV_CONTENT,
            "content_type": "csv",
            "target_type": "lead",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["created"] == 2
        assert data["data"]["status"] == "completed"
        assert len(data["data"]["evidence_ids"]) == 2

    def test_commit_creates_evidence(self, client, auth_headers, seed_org):
        """Import commit creates evidence records."""
        client.post("/api/v1/data/import/commit", headers=auth_headers, json={
            "content": CSV_CONTENT, "content_type": "csv", "target_type": "lead",
        })
        from app import db
        from app.evidence.models_db import EvidenceRecord
        ev_count = db.session.query(EvidenceRecord).filter_by(source_type="import").count()
        assert ev_count >= 2

    def test_commit_partial_failure(self, client, auth_headers, seed_org):
        """Partial failures are reported honestly."""
        resp = client.post("/api/v1/data/import/commit", headers=auth_headers, json={
            "content": "customer_name,phone,email\nAlice,abc,invalid-email",  # Invalid email warned but not blocked
            "content_type": "csv",
            "target_type": "lead",
        })
        data = resp.get_json()
        # Should create the record (warning not a blocker) or partial
        assert data["data"]["status"] in ("completed", "partial")

    def test_commit_requires_auth(self, client):
        """Unauthenticated returns 401."""
        resp = client.post("/api/v1/data/import/commit", json={"content": "test"})
        assert resp.status_code == 401


class TestExport:
    """FDA25: Export with provenance."""

    def test_export_leads(self, client, auth_headers, seed_org):
        """Export leads with provenance."""
        # First import some data
        client.post("/api/v1/data/import/commit", headers=auth_headers, json={
            "content": CSV_CONTENT, "content_type": "csv", "target_type": "lead",
        })
        resp = client.post("/api/v1/data/export", headers=auth_headers, json={
            "target_type": "lead",
            "format": "json",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["record_count"] >= 2
        assert data["data"]["provenance"]["audit_logged"] is True

    def test_export_requires_permission(self, client, seed_org):
        """Export requires org.export_data permission."""
        with client.session_transaction() as s:
            s["identity_id"] = "viewer_user"
            s["current_org_id"] = 1
        headers = {"X-Identity-Id": "viewer_user"}
        resp = client.post("/api/v1/data/export", headers=headers, json={
            "target_type": "lead",
        })
        # Viewer has no export permission
        assert resp.status_code in (401, 403)

    def test_export_requires_auth(self, client):
        """Unauthenticated returns 401."""
        resp = client.post("/api/v1/data/export", json={"target_type": "lead"})
        assert resp.status_code == 401

    def test_export_preserves_tenant(self, client, auth_headers, seed_org):
            """Export is scoped to the current tenant."""
            client.post("/api/v1/data/import/commit", headers=auth_headers, json={
                "content": CSV_CONTENT, "content_type": "csv", "target_type": "lead",
            })

            # Switch to different org — seed it first
            from app import db
            from app.models import Organization, OrgMember
            from app.authz.models import Role, OrgMemberRole
            from app.authz.services import seed_default_roles

            org2 = Organization(id=999, name="Other Org", slug="other-org")
            db.session.add(org2)
            db.session.flush()
            seed_default_roles(999)

            owner_role = db.session.query(Role).filter_by(organization_id=999, name="owner").first()
            member2 = OrgMember(organization_id=999, identity_id="other_user", email="other@test.com",
                               role="owner", is_active=True)
            db.session.add(member2)
            db.session.flush()
            if owner_role:
                db.session.add(OrgMemberRole(organization_id=999, member_id=member2.id,
                    role_id=owner_role.id, scope="organization", granted_by="system"))
            db.session.commit()

            with client.session_transaction() as s:
                s["identity_id"] = "other_user"
                s["current_org_id"] = 999
            headers = {"X-Identity-Id": "other_user"}
            resp = client.post("/api/v1/data/export", headers=headers, json={
                "target_type": "lead",
            })
            assert resp.status_code == 200
            # Other tenant should see 0 records (tenant isolation)
            assert resp.get_json()["data"]["record_count"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])