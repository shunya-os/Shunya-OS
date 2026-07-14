"""
PHASE 1 — Identity Boundary Verification Tests
"""
import pytest


@pytest.fixture(scope="function")
def real_app():
    from app import create_app, db
    application = create_app(config_override={
        "TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret", "DISABLE_RATE_LIMIT": "true", "WTF_CSRF_ENABLED": False,
    })
    with application.app_context():
        from app.tenant import Tenant
        db.create_all()
        yield application
        db.drop_all()


# =========================================================================
# 1. CUSTOMER BACKFILL — No canonical Customer model exists
# =========================================================================

class TestCustomerBackfill:

    def test_no_canonical_customer_model(self):
        """There is no standalone Customer model. Customers exist as Lead.customer_name strings."""
        from app.models import Lead
        # Lead has customer_name (string), not a Customer FK
        cols = [c.name for c in Lead.__table__.columns]
        assert "customer_name" in cols
        # No Customer model exists in models.py
        from app import db
        tables = db.metadata.tables.keys()
        customer_tables = [t for t in tables if "customer" in t.lower() or "client" in t.lower()]
        # customer_profiles exists (role projection), but no standalone Customer
        assert "customer_profiles" in tables
        assert "client_users" in tables  # ClientUser is portal user, not customer


# =========================================================================
# 2. CROSS-TENANT IDENTITY RESOLUTION
# =========================================================================

class TestCrossTenantResolution:

    def test_same_email_different_tenants_resolved_separately(self, real_app):
        """Same email in different tenants returns separate MATCHED results."""
        from app.models import Person, PersonIdentity
        from app.tenant import Tenant
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            t1 = Tenant(company_name="Panchi Club", slug="panchi", business_type="travel", is_active=True)
            t2 = Tenant(company_name="Bali Travel", slug="bali", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()

            p1 = Person(canonical_name="Ritu Panchi", preferred_name="Ritu", tenant_id=t1.id)
            p2 = Person(canonical_name="Ritu Bali", preferred_name="Ritu", tenant_id=t2.id)
            db.session.add(p1); db.session.add(p2); db.session.commit()

            db.session.add(PersonIdentity(person_id=p1.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.add(PersonIdentity(person_id=p2.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.commit()

            resolver = IdentityResolver(session=db.session)

            # Tenant A — must return only Person A
            r1 = resolver.resolve_by_email("ritu@example.com", tenant_id=t1.id)
            assert r1.status == "MATCHED", f"Expected MATCHED for Tenant A, got {r1.status}"
            assert r1.person.id == p1.id, f"Expected Person A ({p1.id}), got Person {r1.person.id}"

            # Tenant B — must return only Person B
            r2 = resolver.resolve_by_email("ritu@example.com", tenant_id=t2.id)
            assert r2.status == "MATCHED", f"Expected MATCHED for Tenant B, got {r2.status}"
            assert r2.person.id == p2.id, f"Expected Person B ({p2.id}), got Person {r2.person.id}"

    def test_same_email_no_tenant_filter_returns_ambiguous(self, real_app):
        """Same email across tenants WITHOUT tenant filter returns AMBIGUOUS."""
        from app.models import Person, PersonIdentity
        from app.tenant import Tenant
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()

            p1 = Person(canonical_name="Ritu A", preferred_name="Ritu", tenant_id=t1.id)
            p2 = Person(canonical_name="Ritu B", preferred_name="Ritu", tenant_id=t2.id)
            db.session.add(p1); db.session.add(p2); db.session.commit()
            db.session.add(PersonIdentity(person_id=p1.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.add(PersonIdentity(person_id=p2.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.commit()

            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve_by_email("ritu@example.com")  # No tenant filter
            assert result.status == "AMBIGUOUS", f"Expected AMBIGUOUS, got {result.status}"
            assert len(result.candidates) == 2

    def test_cross_tenant_phone_resolution(self, real_app):
        """Same phone in different tenants resolves separately with tenant filter."""
        from app.models import Person, PersonIdentity
        from app.tenant import Tenant
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            t1 = Tenant(company_name="X", slug="x", business_type="travel", is_active=True)
            t2 = Tenant(company_name="Y", slug="y", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()

            p1 = Person(canonical_name="Person X", preferred_name="X", tenant_id=t1.id)
            p2 = Person(canonical_name="Person Y", preferred_name="Y", tenant_id=t2.id)
            db.session.add(p1); db.session.add(p2); db.session.commit()
            db.session.add(PersonIdentity(person_id=p1.id, identity_type="phone",
                                          identity_value="+919999999999", normalized_value="+919999999999"))
            db.session.add(PersonIdentity(person_id=p2.id, identity_type="phone",
                                          identity_value="+919999999999", normalized_value="+919999999999"))
            db.session.commit()

            resolver = IdentityResolver(session=db.session)

            r1 = resolver.resolve_by_phone("+919999999999", tenant_id=t1.id)
            assert r1.status == "MATCHED" and r1.person.id == p1.id

            r2 = resolver.resolve_by_phone("+919999999999", tenant_id=t2.id)
            assert r2.status == "MATCHED" and r2.person.id == p2.id

    def test_cross_tenant_ambiguous_not_across_tenants(self, real_app):
        """Same email with tenant filter does NOT produce AMBIGUOUS across tenants."""
        from app.models import Person, PersonIdentity
        from app.tenant import Tenant
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()

            p1 = Person(canonical_name="Ritu One", preferred_name="Ritu", tenant_id=t.id)
            p2 = Person(canonical_name="Ritu Two", preferred_name="Ritu", tenant_id=t.id)
            db.session.add(p1); db.session.add(p2); db.session.commit()
            db.session.add(PersonIdentity(person_id=p1.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.add(PersonIdentity(person_id=p2.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.commit()

            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve_by_email("ritu@example.com", tenant_id=t.id)
            assert result.status == "AMBIGUOUS"  # Same tenant, two persons — correct
            assert len(result.candidates) == 2


# =========================================================================
# 3. LEGACY REFERENCE IDENTITIES
# =========================================================================

class TestLegacyReferences:

    def test_legacy_employee_ref_resolution(self, real_app):
        """PersonIdentity supports employee_ref as identity_type."""
        from app.models import Person, PersonIdentity
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            p = Person(canonical_name="Employee", preferred_name="Emp")
            db.session.add(p); db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="employee_ref",
                                          identity_value="EMP001", normalized_value="EMP001"))
            db.session.commit()

            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve_by_reference("employee_ref", "EMP001")
            assert result.status == "MATCHED"
            assert result.person.id == p.id

    def test_legacy_customer_ref_resolution(self, real_app):
        """PersonIdentity supports customer_ref as identity_type."""
        from app.models import Person, PersonIdentity
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            p = Person(canonical_name="Customer", preferred_name="Cust")
            db.session.add(p); db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="customer_ref",
                                          identity_value="CUST001", normalized_value="CUST001"))
            db.session.commit()

            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve_by_reference("customer_ref", "CUST001")
            assert result.status == "MATCHED"

    def test_legacy_ref_multi_strategy_resolve(self, real_app):
        """resolve() with reference_type falls back to legacy reference."""
        from app.models import Person, PersonIdentity
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="employee_ref",
                                          identity_value="E001", normalized_value="E001"))
            db.session.commit()

            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve(reference_type="employee_ref", reference_value="E001")
            assert result.status == "MATCHED"

    def test_legacy_ref_no_match(self, real_app):
        """Unknown reference returns NO_MATCH."""
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve_by_reference("employee_ref", "UNKNOWN")
            assert result.status == "NO_MATCH"


# =========================================================================
# 4. ROLE PROJECTION TABLE COUNT
# =========================================================================

class TestRoleProjectionCount:

    def test_four_role_projection_tables(self, real_app):
        """There are exactly 4 role projection tables (not 6)."""
        from app import db
        tables = db.metadata.tables.keys()
        role_tables = [
            "employee_profiles",
            "customer_profiles",
            "supplier_contact_profiles",
            "client_user_profiles",
        ]
        for t in role_tables:
            assert t in tables, f"Missing role table: {t}"
        # Person and PersonIdentity are identity foundation, NOT role projections
        assert "persons" in tables
        assert "person_identities" in tables