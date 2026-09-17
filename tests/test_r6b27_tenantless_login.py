"""R6B-2.7 Window 5 — login must not crash for tenant-less accounts.

Production defect found during certification:
``POST /login`` returned HTTP 500 with

    NotNullViolation: null value in column "tenant_id" of relation "persons"

because ``_ensure_person_for_team_member()`` inserted a Person with
``tenant_id=tm.tenant_id``, and accounts created through signup deliberately
have NO tenant ("writing an arbitrary default tenant here would silently place
every new account in tenant 1"). ``persons.tenant_id`` is NOT NULL — set
deliberately by migration 0005 — so the insert always failed.

Consequence: first login was impossible for every account created via signup.

The fix must NOT invent a tenant (that is synthesised ownership). It skips the
CRM projection instead — login must never depend on it.
"""
import pytest


class TestTenantlessLogin:
    def _member(self, app, tenant_id=None, email="tenantless@example.com"):
        from app import db
        from app.auth import TeamMember
        from app.auth_routes import UserRole
        m = TeamMember(name="Tenantless User", email=email,
                       role=UserRole.ADMIN.value, is_active=True,
                       verified=True, tenant_id=tenant_id)
        m.set_password("correct-horse-battery")
        db.session.add(m)
        db.session.commit()
        return m

    def test_ensure_person_skips_without_tenant(self, app):
        """No tenant → no Person, and above all NO exception."""
        from app.auth_routes import _ensure_person_for_team_member
        from app.models import Person

        m = self._member(app)

        result = _ensure_person_for_team_member(m)

        assert result is None
        assert m.person_id is None
        assert Person.query.filter_by(canonical_name=m.email).count() == 0

    def test_ensure_person_still_created_when_tenant_present(self, app):
        """A tenanted account still gets its Person — the fix is not a removal."""
        from app import db
        from app.auth_routes import _ensure_person_for_team_member
        from app.models import Person

        m = self._member(app, tenant_id=None,
                         email="tenanted@example.com")
        m.tenant_id = None
        db.session.commit()

        # Simulate a real tenanted member by pointing at an existing tenant.
        from app.tenant import Tenant
        t = Tenant(company_name="Cert Tenant", slug="cert-tenant-login-test")
        db.session.add(t)
        db.session.commit()
        m.tenant_id = t.id
        db.session.commit()

        result = _ensure_person_for_team_member(m)
        assert result is not None
        assert result.tenant_id == t.id

    def test_login_succeeds_for_tenantless_account(self, app, client):
        """The real journey: a tenant-less account can actually log in."""
        self._member(app)

        resp = client.post("/login", json={
            "email": "tenantless@example.com",
            "password": "correct-horse-battery",
        })

        assert resp.status_code == 200, resp.get_data(as_text=True)[:400]
        assert resp.get_json()["success"] is True

    def test_login_rejects_wrong_password(self, app, client):
        self._member(app)
        resp = client.post("/login", json={
            "email": "tenantless@example.com", "password": "wrong-password",
        })
        assert resp.status_code == 401

    def test_login_rejects_unverified_account(self, app, client):
        from app import db
        m = self._member(app, email="unverified@example.com")
        m.verified = False
        db.session.commit()

        resp = client.post("/login", json={
            "email": "unverified@example.com",
            "password": "correct-horse-battery",
        })
        assert resp.status_code == 403
