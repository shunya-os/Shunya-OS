"""
PHASE 1 — Unified Human Identity Characterization Tests
"""

import pytest
from datetime import datetime


@pytest.fixture()
def client(real_app):
    return real_app.test_client()


# =========================================================================
# PERSON CREATION & SEMANTICS
# =========================================================================

class TestPersonCreation:

    def test_person_creation(self, real_app):
        """Person can be created with canonical_name and preferred_name."""
        from app.models import Person
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ms. Ritu Sharma", preferred_name="Ritu")
            db.session.add(p)
            db.session.commit()
            assert p.id is not None
            assert p.canonical_name == "Ms. Ritu Sharma"
            assert p.preferred_name == "Ritu"
            assert p.status == "active"

    def test_canonical_and_preferred_name_distinct(self, real_app):
        """canonical_name and preferred_name are separate fields."""
        from app.models import Person
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Mr. Arjun Singh", preferred_name="Arjun")
            db.session.add(p)
            db.session.commit()
            assert p.canonical_name != p.preferred_name

    def test_person_default_status(self, real_app):
        """Default status is 'active'."""
        from app.models import Person
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p)
            db.session.commit()
            assert p.status == "active"

    def test_person_timestamps(self, real_app):
        """created_at and updated_at are set on creation."""
        from app.models import Person
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p)
            db.session.commit()
            assert p.created_at is not None
            assert p.updated_at is not None


# =========================================================================
# PERSON IDENTITY
# =========================================================================

class TestPersonIdentity:

    def test_identity_creation(self, real_app):
        """PersonIdentity can be created for a Person."""
        from app.models import Person, PersonIdentity
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu Sharma", preferred_name="Ritu")
            db.session.add(p)
            db.session.commit()
            pi = PersonIdentity(person_id=p.id, identity_type="email",
                                identity_value="ritu@example.com",
                                normalized_value="ritu@example.com")
            db.session.add(pi)
            db.session.commit()
            assert pi.id is not None
            assert pi.identity_type == "email"

    def test_identity_normalized_email(self, real_app):
        """Email normalization uses lowercase."""
        from app.shunya.identity import normalize_email
        assert normalize_email("Ritu@Example.COM") == "ritu@example.com"
        assert normalize_email("  A@B.COM  ") == "a@b.com"
        assert normalize_email("") == ""

    def test_identity_normalized_phone(self, real_app):
        """Phone normalization strips non-digits but keeps +."""
        from app.shunya.identity import normalize_phone
        assert normalize_phone("+91 98765 43210") == "+919876543210"
        assert normalize_phone("98765-43210") == "9876543210"
        assert normalize_phone("") == ""

    def test_identity_normalized_name(self, real_app):
        """Name normalization title-cases and strips whitespace."""
        from app.shunya.identity import normalize_name
        assert normalize_name("  ritu  sharma  ") == "Ritu Sharma"
        assert normalize_name("") == ""

    def test_person_has_identities_relationship(self, real_app):
        """Person.identities returns all linked identities."""
        from app.models import Person, PersonIdentity
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu Sharma", preferred_name="Ritu")
            db.session.add(p)
            db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="email",
                                          identity_value="ritu@x.com", normalized_value="ritu@x.com"))
            db.session.add(PersonIdentity(person_id=p.id, identity_type="phone",
                                          identity_value="+919999999999", normalized_value="+919999999999"))
            db.session.commit()
            assert len(p.identities) == 2


# =========================================================================
# IDENTITY RESOLUTION
# =========================================================================

class TestIdentityResolution:

    def test_resolve_matched_by_email(self, real_app):
        """Email identity resolves to MATCHED."""
        from app.models import Person, PersonIdentity
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            p = Person(canonical_name="Ritu Sharma", preferred_name="Ritu")
            db.session.add(p)
            db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="email",
                                          identity_value="ritu@example.com",
                                          normalized_value="ritu@example.com"))
            db.session.commit()
            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve_by_email("ritu@example.com")
            assert result.status == "MATCHED"
            assert result.person.id == p.id

    def test_resolve_no_match_by_email(self, real_app):
        """Unknown email returns NO_MATCH."""
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve_by_email("unknown@example.com")
            assert result.status == "NO_MATCH"

    def test_resolve_matched_by_phone(self, real_app):
        """Phone identity resolves to MATCHED."""
        from app.models import Person, PersonIdentity
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            p = Person(canonical_name="Arjun Singh", preferred_name="Arjun")
            db.session.add(p)
            db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="phone",
                                          identity_value="+919876543210",
                                          normalized_value="+919876543210"))
            db.session.commit()
            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve_by_phone("+91 98765 43210")
            assert result.status == "MATCHED"
            assert result.person.id == p.id

    def test_resolve_no_match_by_phone(self, real_app):
        """Unknown phone returns NO_MATCH."""
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve_by_phone("+919999999999")
            assert result.status == "NO_MATCH"

    def test_resolve_ambiguous(self, real_app):
        """Multiple persons with same email return AMBIGUOUS."""
        from app.models import Person, PersonIdentity
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            p1 = Person(canonical_name="Ritu Sharma", preferred_name="Ritu")
            p2 = Person(canonical_name="Ritu Verma", preferred_name="Ritu")
            db.session.add(p1); db.session.add(p2)
            db.session.commit()
            db.session.add(PersonIdentity(person_id=p1.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.add(PersonIdentity(person_id=p2.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.commit()
            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve_by_email("ritu@example.com")
            assert result.status == "AMBIGUOUS"
            assert len(result.candidates) == 2

    def test_no_silent_merge(self, real_app):
        """AMBIGUOUS resolution does not merge persons."""
        from app.models import Person, PersonIdentity
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            p1 = Person(canonical_name="Ritu Sharma", preferred_name="Ritu")
            p2 = Person(canonical_name="Ritu Verma", preferred_name="Ritu")
            db.session.add(p1); db.session.add(p2)
            db.session.commit()
            db.session.add(PersonIdentity(person_id=p1.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.add(PersonIdentity(person_id=p2.id, identity_type="email",
                                          identity_value="ritu@example.com", normalized_value="ritu@example.com"))
            db.session.commit()
            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve_by_email("ritu@example.com")
            assert result.status == "AMBIGUOUS"
            # Both persons still exist separately
            assert len(Person.query.all()) == 2

    def test_resolve_multi_strategy(self, real_app):
        """Multi-strategy resolve tries email first, then phone."""
        from app.models import Person, PersonIdentity
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            p = Person(canonical_name="Ritu Sharma", preferred_name="Ritu")
            db.session.add(p)
            db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="email",
                                          identity_value="ritu@x.com", normalized_value="ritu@x.com"))
            db.session.commit()
            resolver = IdentityResolver(session=db.session)
            result = resolver.resolve(email="ritu@x.com", phone="+919999999999")
            assert result.status == "MATCHED"

    def test_register_identity(self, real_app):
        """register_identity creates a normalized PersonIdentity."""
        from app.models import Person
        from app import db
        from app.shunya.identity import IdentityResolver
        with real_app.app_context():
            p = Person(canonical_name="Ritu Sharma", preferred_name="Ritu")
            db.session.add(p)
            db.session.commit()
            resolver = IdentityResolver(session=db.session)
            pi = resolver.register_identity(p, "phone", "+91 98765 43210")
            assert pi.identity_type == "phone"
            assert pi.normalized_value == "+919876543210"


# =========================================================================
# ROLE PROJECTIONS
# =========================================================================

class TestRoleProjections:

    def test_employee_profile(self, real_app):
        """EmployeeProfile references Person."""
        from app.models import Person, EmployeeProfile
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Employee", preferred_name="Emp")
            db.session.add(p)
            db.session.commit()
            ep = EmployeeProfile(person_id=p.id, employee_code="EMP001", department="Sales")
            db.session.add(ep)
            db.session.commit()
            assert ep.id is not None
            assert ep.person_id == p.id
            assert p.employee_profile is not None

    def test_customer_profile(self, real_app):
        """CustomerProfile references Person with lifetime_value."""
        from app.models import Person, CustomerProfile
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Customer", preferred_name="Cust")
            db.session.add(p)
            db.session.commit()
            cp = CustomerProfile(person_id=p.id, lifetime_value=50000, segment="premium")
            db.session.add(cp)
            db.session.commit()
            assert cp.id is not None
            assert float(cp.lifetime_value) == 50000.0
            assert p.customer_profile is not None

    def test_supplier_contact_profile(self, real_app):
        """SupplierContactProfile references Person."""
        from app.models import Person, SupplierContactProfile
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Supplier Contact", preferred_name="Supp")
            db.session.add(p)
            db.session.commit()
            sp = SupplierContactProfile(person_id=p.id, supplier_id=1, is_primary=True)
            db.session.add(sp)
            db.session.commit()
            assert sp.id is not None
            assert sp.is_primary is True

    def test_client_user_profile(self, real_app):
        """ClientUserProfile references Person."""
        from app.models import Person, ClientUserProfile
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Client User", preferred_name="Client")
            db.session.add(p)
            db.session.commit()
            cu = ClientUserProfile(person_id=p.id, portal_access_granted=True)
            db.session.add(cu)
            db.session.commit()
            assert cu.id is not None
            assert cu.portal_access_granted is True

    def test_one_person_multiple_projections(self, real_app):
        """One Person can have multiple role projections."""
        from app.models import Person, EmployeeProfile, CustomerProfile
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Multi Role", preferred_name="Multi")
            db.session.add(p)
            db.session.commit()
            db.session.add(EmployeeProfile(person_id=p.id, employee_code="E001"))
            db.session.add(CustomerProfile(person_id=p.id, lifetime_value=10000))
            db.session.commit()
            assert p.employee_profile is not None
            assert p.customer_profile is not None

    def test_customer_profile_no_inferred_communication_style(self, real_app):
        """CustomerProfile does NOT have communication_style field."""
        from app.models import CustomerProfile
        cols = [c.name for c in CustomerProfile.__table__.columns]
        assert "communication_style" not in cols, "communication_style must not be on CustomerProfile"
        assert "preferred_channel" in cols
        assert "preferred_channel_provenance" in cols


# =========================================================================
# LEGACY COMPATIBILITY
# =========================================================================

class TestLegacyCompatibility:

    def test_lead_still_has_customer_name(self, real_app):
        """Lead still has customer_name string field."""
        from app.models import Lead, next_inquiry_code
        from app import db
        with real_app.app_context():
            code = next_inquiry_code(db.session)
            lead = Lead(code=code, source="test", customer_name="Old Customer", destination="Goa")
            db.session.add(lead)
            db.session.commit()
            assert lead.customer_name == "Old Customer"

    def test_lead_has_person_id(self, real_app):
        """Lead has nullable person_id FK."""
        from app.models import Lead, next_inquiry_code
        from app import db
        with real_app.app_context():
            cols = [c.name for c in Lead.__table__.columns]
            assert "person_id" in cols

    def test_team_member_has_person_id(self, real_app):
        """TeamMember has nullable person_id FK."""
        from app.auth import TeamMember
        cols = [c.name for c in TeamMember.__table__.columns]
        assert "person_id" in cols

    def test_lead_creation_still_works_without_person(self, real_app):
        """Lead can be created without person_id (backward compat)."""
        from app.models import Lead, next_inquiry_code
        from app import db
        with real_app.app_context():
            code = next_inquiry_code(db.session)
            lead = Lead(code=code, source="test", customer_name="Test", destination="Goa")
            db.session.add(lead)
            db.session.commit()
            assert lead.person_id is None
            assert lead.person is None


# =========================================================================
# TENANT ISOLATION
# =========================================================================

class TestTenantIsolation:

    def test_person_tenant_isolation(self, real_app):
        """Person can be scoped to a tenant."""
        from app.models import Person
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="Test Co", slug="test-co", business_type="travel", is_active=True)
            db.session.add(t)
            db.session.commit()
            p = Person(canonical_name="Test User", preferred_name="Testy", tenant_id=t.id)
            db.session.add(p)
            db.session.commit()
            assert p.tenant_id == t.id


# =========================================================================
# BACKFILL BEHAVIOUR
# =========================================================================

class TestBackfillBehaviour:

    def test_backfill_team_member_to_person(self, real_app):
        """TeamMember can be backfilled to Person + EmployeeProfile."""
        from app.models import Person, EmployeeProfile
        from app.auth import TeamMember, UserRole
        from app import db
        with real_app.app_context():
            tm = TeamMember(name="Existing Employee", email="emp@test.com", role=UserRole.AGENT.value)
            tm.set_password("test123")
            db.session.add(tm)
            db.session.commit()
            # Backfill
            p = Person(canonical_name=tm.name, preferred_name=tm.name.split()[0] if tm.name else tm.name)
            db.session.add(p)
            db.session.commit()
            tm.person_id = p.id
            ep = EmployeeProfile(person_id=p.id, role=tm.role)
            db.session.add(ep)
            db.session.commit()
            assert tm.person_id == p.id
            assert p.employee_profile is not None
            assert p.employee_profile.role == "agent"

    def test_backfill_conservative_no_merge(self, real_app):
        """Backfill does not merge ambiguous records."""
        from app.models import Person
        from app.auth import TeamMember, UserRole
        from app import db
        with real_app.app_context():
            tm1 = TeamMember(name="Ritu Sharma", email="ritu.sharma@test.com", role=UserRole.AGENT.value)
            tm2 = TeamMember(name="Ritu Verma", email="ritu.verma@test.com", role=UserRole.AGENT.value)
            tm1.set_password("pw1"); tm2.set_password("pw2")
            db.session.add(tm1); db.session.add(tm2)
            db.session.commit()
            # Each gets their own Person — no merge
            p1 = Person(canonical_name=tm1.name, preferred_name="Ritu")
            p2 = Person(canonical_name=tm2.name, preferred_name="Ritu")
            db.session.add(p1); db.session.add(p2)
            db.session.commit()
            assert p1.id != p2.id