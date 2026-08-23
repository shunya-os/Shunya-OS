"""ZGC-05 Workstream B — Organisation Persistence Tests.

Required behaviour:
  Create organisation → upload/import/connect data → log out → log in →
  refresh → open a new browser session.
  The same organisation, data, relationships, memory and activity must
  still be present.
"""

import pytest
from app import db
from app.models import Organization, OrgMember


class TestOrgCreatePersistence:
    """Verify organisation creation, membership, and session restoration."""

    def test_org_creation_minimal(self, app, client):
        """Create org with minimal fields → stored with default values."""
        from app.models import Organization as Org
        org = Org(name="Test Corp", slug="test-corp-persist")
        db.session.add(org)
        db.session.commit()
        assert org.id is not None
        assert org.is_active is True
        assert org.currency == "INR"
        assert org.timezone == "UTC"

    def test_org_create_then_read(self, app, client):
        """Org created → queryable by id."""
        from app.models import Organization as Org
        org = Org(name="Read Test", slug="read-test-org")
        db.session.add(org)
        db.session.commit()
        fetched = db.session.get(Org, org.id)
        assert fetched is not None
        assert fetched.name == "Read Test"

    def test_org_slug_uniqueness(self, app, client):
        """Duplicate slug raises IntegrityError."""
        from app.models import Organization as Org
        from sqlalchemy.exc import IntegrityError
        org1 = Org(name="First", slug="dup-slug")
        db.session.add(org1)
        db.session.commit()
        org2 = Org(name="Second", slug="dup-slug")
        db.session.add(org2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_org_member_creation(self, app, client):
        """Create org + member → member belongs to org."""
        from app.models import Organization as Org, OrgMember
        org = Org(name="Member Test", slug="member-test")
        db.session.add(org)
        db.session.commit()
        om = OrgMember(
            organization_id=org.id,
            identity_id="sid_member_test",
            name="Test User",
            email="test@member.org",
            role="admin",
        )
        db.session.add(om)
        db.session.commit()
        assert om.id is not None
        assert om.organization_id == org.id

    def test_org_member_unique_constraint(self, app, client):
        """Same identity_id + organization_id raises IntegrityError."""
        from app.models import Organization as Org, OrgMember
        from sqlalchemy.exc import IntegrityError
        org = Org(name="Unique Test", slug="unique-test")
        db.session.add(org)
        db.session.commit()
        om1 = OrgMember(
            organization_id=org.id,
            identity_id="sid_unique",
            email="u1@test.org",
        )
        db.session.add(om1)
        db.session.commit()
        om2 = OrgMember(
            organization_id=org.id,
            identity_id="sid_unique",
            email="u2@test.org",
        )
        db.session.add(om2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_org_no_automatic_duplicate(self, app, client):
        """Creating org with same name/slug explicitly does not auto-dedup."""
        from app.models import Organization as Org
        from sqlalchemy.exc import IntegrityError
        org1 = Org(name="Dedup Test", slug="dedup-test")
        db.session.add(org1)
        db.session.commit()
        # Without explicit slug change, second create with same slug fails
        with pytest.raises(IntegrityError):
            org2 = Org(name="Dedup Test", slug="dedup-test")
            db.session.add(org2)
            db.session.commit()
        db.session.rollback()

    def test_session_restore_endpoint_no_auth(self, app, client):
        """GET /api/v1/auth/session without auth returns 401."""
        resp = client.get("/api/v1/auth/session")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data.get("authenticated") is False

    def test_session_restore_with_auth(self, app, client):
        """GET /api/v1/auth/session with valid session returns identity."""
        from app.auth import TeamMember
        from app.auth_routes import UserRole

        # Create a team member and log them in via session
        member = TeamMember(
            name="Session Test",
            email="session@test.org",
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        member.set_password("testpass123")
        db.session.add(member)
        db.session.commit()

        with client.session_transaction() as sess:
            sess["user_id"] = member.id

        resp = client.get("/api/v1/auth/session")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("authenticated") is True
        assert data.get("email") == "session@test.org"

    def test_session_persists_across_requests(self, app, client):
        """Flask session cookie persists across multiple requests."""
        from app.auth import TeamMember
        from app.auth_routes import UserRole

        member = TeamMember(
            name="Persist Test",
            email="persist@test.org",
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        member.set_password("testpass123")
        db.session.add(member)
        db.session.commit()

        # Login
        with client.session_transaction() as sess:
            sess["user_id"] = member.id

        # First request
        resp1 = client.get("/api/v1/auth/session")
        assert resp1.status_code == 200

        # Second request (no explicit login) — cookie should persist
        # The Flask test client preserves cookies across requests
        resp2 = client.get("/api/v1/auth/session")
        assert resp2.status_code == 200
        data2 = resp2.get_json()
        assert data2.get("authenticated") is True
        assert data2.get("user_id") == member.id