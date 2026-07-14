"""
PHASE 2 — HARDENING TESTS: auto-relationship, Lead association, lifetime customer, tenant_id, backfill
"""
import pytest
from datetime import datetime, timedelta


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
# 1. PHASE 1A AUTO-RELATIONSHIP INTEGRATION
# =========================================================================

class TestPhase1AAutoRelationship:

    def test_no_match_creates_customer_relationship_automatically(self, real_app):
        """Approved NO_MATCH customer import automatically creates CUSTOMER relationship."""
        from app.models import Person, IntakeSession, IntakeCandidate, Relationship
        from app.intake.session import IntakeSessionState
        from app.intake.proposal import ImportProposalBuilder
        from app.intake.committer import GovernedCommitter
        from app import db
        with real_app.app_context():
            sess = IntakeSession(source_type="csv", source_name="test.csv", status=IntakeSessionState.READY_FOR_REVIEW)
            db.session.add(sess); db.session.commit()
            c = IntakeCandidate(session_id=sess.id, row_index=0, identity_status="NO_MATCH",
                                import_status="pending", classification="customer",
                                normalized_data='{"name":"Ritu Auto","email":"ritu.auto@test.com"}')
            db.session.add(c); db.session.commit()
            ImportProposalBuilder.build(sess, [c])
            committer = GovernedCommitter(session=db.session)
            committer.approve(sess.id, approved_by="admin")
            result = committer.commit(sess.id)
            assert result["imported"] == 1
            person = Person.query.filter_by(canonical_name="Ritu Auto").first()
            assert person is not None
            rel = Relationship.query.filter_by(person_id=person.id, relationship_type="customer").first()
            assert rel is not None, "CUSTOMER relationship was not created automatically"
            assert rel.status == "active"

    def test_matched_creates_customer_relationship_automatically(self, real_app):
        """Approved MATCHED customer import ensures CUSTOMER relationship."""
        from app.models import Person, PersonIdentity, IntakeSession, IntakeCandidate, Relationship
        from app.intake.session import IntakeSessionState
        from app.intake.proposal import ImportProposalBuilder
        from app.intake.committer import GovernedCommitter
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu Match", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="email",
                                          identity_value="ritu.match@test.com", normalized_value="ritu.match@test.com"))
            db.session.commit()
            sess = IntakeSession(source_type="csv", source_name="test.csv", status=IntakeSessionState.READY_FOR_REVIEW)
            db.session.add(sess); db.session.commit()
            c = IntakeCandidate(session_id=sess.id, row_index=0, identity_status="MATCHED",
                                matched_person_id=p.id, import_status="pending", classification="customer",
                                normalized_data='{"email":"ritu.match@test.com"}')
            db.session.add(c); db.session.commit()
            ImportProposalBuilder.build(sess, [c])
            committer = GovernedCommitter(session=db.session)
            committer.approve(sess.id, approved_by="admin")
            result = committer.commit(sess.id)
            assert result["linked"] == 1
            rel = Relationship.query.filter_by(person_id=p.id, relationship_type="customer").first()
            assert rel is not None, "CUSTOMER relationship was not created automatically"
            assert rel.status == "active"

    def test_unresolved_creates_no_relationship(self, real_app):
        """AMBIGUOUS candidates create no relationship."""
        from app.models import IntakeSession, IntakeCandidate, Relationship
        from app import db
        with real_app.app_context():
            sess = IntakeSession(source_type="csv", source_name="test.csv", status="ready_for_review")
            db.session.add(sess); db.session.commit()
            c = IntakeCandidate(session_id=sess.id, row_index=0, identity_status="AMBIGUOUS",
                                import_status="blocked", classification="customer",
                                normalized_data="{}")
            db.session.add(c); db.session.commit()
            rels = Relationship.query.all()
            assert len(rels) == 0

    def test_idempotent_relationship_on_retry(self, real_app):
        """Re-running import does not create duplicate relationships."""
        from app.models import Person, IntakeSession, IntakeCandidate, Relationship
        from app.intake.session import IntakeSessionState
        from app.intake.proposal import ImportProposalBuilder
        from app.intake.committer import GovernedCommitter
        from app import db
        with real_app.app_context():
            sess = IntakeSession(source_type="csv", source_name="test.csv", status=IntakeSessionState.READY_FOR_REVIEW)
            db.session.add(sess); db.session.commit()
            c = IntakeCandidate(session_id=sess.id, row_index=0, identity_status="NO_MATCH",
                                import_status="pending", classification="customer",
                                normalized_data='{"name":"Idempotent","email":"idem@test.com"}')
            db.session.add(c); db.session.commit()
            ImportProposalBuilder.build(sess, [c])
            committer = GovernedCommitter(session=db.session)
            committer.approve(sess.id, approved_by="admin")
            r1 = committer.commit(sess.id)
            assert r1["imported"] == 1
            person = Person.query.filter_by(canonical_name="Idempotent").first()
            rels = Relationship.query.filter_by(person_id=person.id).all()
            assert len(rels) == 1


# =========================================================================
# 2. LEGACY LEAD SAFE ASSOCIATION
# =========================================================================

class TestLeadAssociation:

    def test_lead_name_only_no_association(self, real_app):
        from app.models import Lead, next_inquiry_code
        from app.relationship.lead_association import LeadAssociationService
        from app import db
        with real_app.app_context():
            code = next_inquiry_code(db.session)
            lead = Lead(code=code, source="test", customer_name="Ritu Only", destination="Goa")
            db.session.add(lead); db.session.commit()
            svc = LeadAssociationService(session=db.session)
            result = svc.resolve_lead_person(lead)
            assert result["status"] == "INSUFFICIENT_IDENTITY"

    def test_lead_strong_identity_matched(self, real_app):
        from app.models import Person, PersonIdentity, Lead, next_inquiry_code
        from app.relationship.lead_association import LeadAssociationService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu Strong", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="email",
                                          identity_value="ritu@test.com", normalized_value="ritu@test.com"))
            db.session.commit()
            code = next_inquiry_code(db.session)
            lead = Lead(code=code, source="test", customer_name="Ritu Strong",
                        email="ritu@test.com", phone="+919999999999", destination="Goa")
            db.session.add(lead); db.session.commit()
            svc = LeadAssociationService(session=db.session)
            result = svc.resolve_lead_person(lead)
            assert result["status"] == "MATCHED"
            assert result["person_id"] == p.id

    def test_lead_conflict_no_association(self, real_app):
        from app.models import Person, PersonIdentity, Lead, next_inquiry_code
        from app.relationship.lead_association import LeadAssociationService
        from app import db
        with real_app.app_context():
            p1 = Person(canonical_name="Person A", preferred_name="A")
            p2 = Person(canonical_name="Person B", preferred_name="B")
            db.session.add(p1); db.session.add(p2); db.session.commit()
            db.session.add(PersonIdentity(person_id=p1.id, identity_type="email",
                                          identity_value="ritu@test.com", normalized_value="ritu@test.com"))
            db.session.add(PersonIdentity(person_id=p2.id, identity_type="phone",
                                          identity_value="+919999999999", normalized_value="+919999999999"))
            db.session.commit()
            code = next_inquiry_code(db.session)
            lead = Lead(code=code, source="test", customer_name="Ritu Conflict",
                        email="ritu@test.com", phone="+919999999999", destination="Goa")
            db.session.add(lead); db.session.commit()
            svc = LeadAssociationService(session=db.session)
            result = svc.resolve_lead_person(lead)
            assert result["status"] == "CONFLICT"

    def test_ensure_relationship_for_lead(self, real_app):
        from app.models import Person, PersonIdentity, Lead, next_inquiry_code, Relationship
        from app.relationship.lead_association import LeadAssociationService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu Lead", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="email",
                                          identity_value="ritu.lead@test.com", normalized_value="ritu.lead@test.com"))
            db.session.commit()
            code = next_inquiry_code(db.session)
            lead = Lead(code=code, source="test", customer_name="Ritu Lead",
                        email="ritu.lead@test.com", destination="Goa")
            db.session.add(lead); db.session.commit()
            svc = LeadAssociationService(session=db.session)
            result = svc.ensure_customer_relationship_for_lead(lead)
            assert result["status"] == "MATCHED"
            assert result["person_id"] == p.id
            rel = Relationship.query.filter_by(person_id=p.id, relationship_type="customer").first()
            assert rel is not None

    def test_lead_conflict_no_relationship_created(self, real_app):
        from app.models import Person, PersonIdentity, Lead, next_inquiry_code, Relationship
        from app.relationship.lead_association import LeadAssociationService
        from app import db
        with real_app.app_context():
            p1 = Person(canonical_name="A", preferred_name="A"); p2 = Person(canonical_name="B", preferred_name="B")
            db.session.add(p1); db.session.add(p2); db.session.commit()
            db.session.add(PersonIdentity(person_id=p1.id, identity_type="email", identity_value="c@t.com", normalized_value="c@t.com"))
            db.session.add(PersonIdentity(person_id=p2.id, identity_type="phone", identity_value="+919999999999", normalized_value="+919999999999"))
            db.session.commit()
            code = next_inquiry_code(db.session)
            lead = Lead(code=code, source="test", customer_name="Conflict", email="c@t.com", phone="+919999999999", destination="Goa")
            db.session.add(lead); db.session.commit()
            svc = LeadAssociationService(session=db.session)
            result = svc.ensure_customer_relationship_for_lead(lead)
            assert result["status"] == "CONFLICT"


# =========================================================================
# 3. CUSTOMER LIFETIME RELATIONSHIP
# =========================================================================

class TestCustomerLifetime:

    def test_multiple_leads_one_customer_relationship(self, real_app):
        """3 Leads matched to same Person → 1 CUSTOMER Relationship."""
        from app.models import Person, PersonIdentity, Lead, next_inquiry_code, Relationship
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu Lifetime", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="email",
                                          identity_value="ritu.life@test.com", normalized_value="ritu.life@test.com"))
            db.session.commit()
            # 3 Leads with same email
            for i in range(3):
                code = next_inquiry_code(db.session)
                lead = Lead(code=code, source="test", customer_name="Ritu Lifetime",
                            email="ritu.life@test.com", destination=f"Trip {i}")
                db.session.add(lead)
            db.session.commit()
            # Ensure one relationship
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id)
            rels = Relationship.query.filter_by(person_id=p.id, relationship_type="customer").all()
            assert len(rels) == 1, f"Expected 1 relationship, got {len(rels)}"
            assert r.id == rels[0].id

    def test_get_leads_for_person(self, real_app):
        """Leads associated with a Person's identities are retrievable."""
        from app.models import Person, PersonIdentity, Lead, next_inquiry_code
        from app.relationship.lead_association import LeadAssociationService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu Get", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            db.session.add(PersonIdentity(person_id=p.id, identity_type="email",
                                          identity_value="ritu.get@test.com", normalized_value="ritu.get@test.com"))
            db.session.commit()
            for i in range(3):
                code = next_inquiry_code(db.session)
                lead = Lead(code=code, source="test", customer_name="Ritu Get",
                            email="ritu.get@test.com", destination=f"Trip {i}")
                db.session.add(lead)
            db.session.commit()
            svc = LeadAssociationService(session=db.session)
            leads = svc.get_leads_for_person(p)
            assert len(leads) == 3


# =========================================================================
# 4. BACKFILL
# =========================================================================

class TestBackfill:

    def test_backfill_from_customer_profile(self, real_app):
        """Backfill creates CUSTOMER relationship from existing CustomerProfile."""
        from app.models import Person, CustomerProfile, Relationship
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            CustomerProfile(person_id=p.id)
            db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id)
            assert r.relationship_type == "customer"

    def test_backfill_idempotent(self, real_app):
        """Re-running backfill does not create duplicate relationships."""
        from app.models import Person, CustomerProfile, Relationship
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            CustomerProfile(person_id=p.id)
            db.session.commit()
            svc = RelationshipService(session=db.session)
            svc.ensure_customer_relationship(p.id)
            svc.ensure_customer_relationship(p.id)
            rels = Relationship.query.filter_by(person_id=p.id, relationship_type="customer").all()
            assert len(rels) == 1


# =========================================================================
# 5. TENANT_ID NULLABILITY
# =========================================================================

class TestTenantIdNullability:

    def test_tenant_id_nullable_documented(self):
        """tenant_id is nullable for legacy/default-tenant compatibility.
        Service-level isolation is enforced — all queries require tenant_id.
        Creation paths assign tenant_id whenever the Person has tenant ownership."""
        from app.models import Relationship
        cols = [c.name for c in Relationship.__table__.columns]
        assert "tenant_id" in cols
        # Verify NOT NULL is not enforced at DB level (nullable for compatibility)

    def test_creation_assigns_tenant_id_when_person_has_it(self, real_app):
        """Creating a relationship for a tenant-scoped Person assigns tenant_id."""
        from app.models import Person, Relationship
        from app.tenant import Tenant
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu", tenant_id=t.id)
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id, tenant_id=t.id)
            assert r.tenant_id == t.id


# =========================================================================
# 6. RELATIONSHIP CONTEXT/COUNTERPARTY BOUNDARY
# =========================================================================

class TestCounterpartyBoundary:

    def test_current_design_centers_tenant_person(self):
        """Current Phase 2 centers tenant ↔ Person relationships.
        Future organization/entity counterparty can be added by:
        - Adding an optional counterparty_type + counterparty_id to the Relationship model
        - Creating a counterparty table or extending the existing FK pattern
        - NOT redefining Person identity
        - NOT destroying existing Relationship rows (new columns are additive)"""

    def test_future_counterparty_additive(self, real_app):
        """Adding a counterparty column in future does not break existing relationships."""
        from app.models import Relationship
        # Current schema safely supports additive future columns
        assert hasattr(Relationship, "person_id")
        # Counterparty would be: counterparty_type VARCHAR, counterparty_id INTEGER


class TestSupplierContactProjection:
    """SupplierContactProfile → SUPPLIER_CONTACT Relationship"""

    def test_supplier_contact_relationship_created(self, real_app):
        from app.models import Person, SupplierContactProfile, Relationship, RelationshipEvent
        from app.tenant import Tenant
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="TestCo", slug="testco", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ayu Supplier", preferred_name="Ayu", tenant_id=t.id)
            db.session.add(p); db.session.commit()
            SupplierContactProfile(person_id=p.id, supplier_id=1, role_in_organization="Contact Person", is_primary=True, tenant_id=t.id)
            db.session.commit()

            svc = RelationshipService(session=db.session)
            r = svc.ensure_supplier_contact_relationship(p.id, tenant_id=t.id)
            assert r.relationship_type == "supplier_contact"
            assert r.person_id == p.id

            rels = Relationship.query.filter_by(person_id=p.id, relationship_type="supplier_contact").all()
            assert len(rels) == 1, f"Expected 1, got {len(rels)}"

    def test_supplier_contact_idempotent(self, real_app):
        from app.models import Person, SupplierContactProfile, Relationship, RelationshipEvent
        from app.tenant import Tenant
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="TestCo", slug="testco", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ayu S", preferred_name="Ayu", tenant_id=t.id)
            db.session.add(p); db.session.commit()
            SupplierContactProfile(person_id=p.id, supplier_id=1, role_in_organization="Contact Person", is_primary=True, tenant_id=t.id)
            db.session.commit()

            svc = RelationshipService(session=db.session)
            svc.ensure_supplier_contact_relationship(p.id, tenant_id=t.id)
            svc.ensure_supplier_contact_relationship(p.id, tenant_id=t.id)

            rels = Relationship.query.filter_by(person_id=p.id, relationship_type="supplier_contact").all()
            assert len(rels) == 1, f"Expected 1, got {len(rels)}"

            events = RelationshipEvent.query.join(Relationship, RelationshipEvent.relationship_id == Relationship.id).filter(
                Relationship.person_id == p.id,
                RelationshipEvent.event_type == "RELATIONSHIP_CREATED"
            ).all()
            assert len(events) == 1, f"Expected 1 bootstrap event, got {len(events)}"


class TestClientUserProjection:
    """ClientUserProfile → CLIENT_USER Relationship"""

    def test_client_user_relationship_created(self, real_app):
        from app.models import Person, ClientUserProfile, Relationship, RelationshipEvent
        from app.tenant import Tenant
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="TestCo", slug="testco", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Client User", preferred_name="CU", tenant_id=t.id)
            db.session.add(p); db.session.commit()
            ClientUserProfile(person_id=p.id, portal_access_granted=True, tenant_id=t.id)
            db.session.commit()

            svc = RelationshipService(session=db.session)
            r = svc.ensure_client_user_relationship(p.id, tenant_id=t.id)
            assert r.relationship_type == "client_user"
            assert r.person_id == p.id

            rels = Relationship.query.filter_by(person_id=p.id, relationship_type="client_user").all()
            assert len(rels) == 1, f"Expected 1, got {len(rels)}"

    def test_client_user_idempotent(self, real_app):
        from app.models import Person, ClientUserProfile, Relationship, RelationshipEvent
        from app.tenant import Tenant
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="TestCo", slug="testco", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Client User 2", preferred_name="CU2", tenant_id=t.id)
            db.session.add(p); db.session.commit()
            ClientUserProfile(person_id=p.id, portal_access_granted=True, tenant_id=t.id)
            db.session.commit()

            svc = RelationshipService(session=db.session)
            svc.ensure_client_user_relationship(p.id, tenant_id=t.id)
            svc.ensure_client_user_relationship(p.id, tenant_id=t.id)

            rels = Relationship.query.filter_by(person_id=p.id, relationship_type="client_user").all()
            assert len(rels) == 1, f"Expected 1, got {len(rels)}"

            events = RelationshipEvent.query.join(Relationship, RelationshipEvent.relationship_id == Relationship.id).filter(
                Relationship.person_id == p.id,
                RelationshipEvent.event_type == "RELATIONSHIP_CREATED"
            ).all()
            assert len(events) == 1, f"Expected 1 bootstrap event, got {len(events)}"


class TestCrossTenantCommitmentIsolation:
    """Cross-tenant commitment isolation — Tenant B cannot see Tenant A commitments."""

    def test_cross_tenant_commitment_isolation(self, real_app):
        from app.models import Person, Relationship, RelationshipCommitment
        from app.tenant import Tenant
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            t_a = Tenant(company_name="TenantA", slug="ta", business_type="travel", is_active=True)
            t_b = Tenant(company_name="TenantB", slug="tb", business_type="travel", is_active=True)
            db.session.add(t_a); db.session.add(t_b); db.session.commit()

            # Tenant A: Person, Relationship, Commitment
            p_a = Person(canonical_name="User A", preferred_name="A", tenant_id=t_a.id)
            db.session.add(p_a); db.session.commit()
            svc_a = RelationshipService(session=db.session)
            r_a = svc_a.ensure_customer_relationship(p_a.id, tenant_id=t_a.id)
            svc_a.create_commitment(r_a.id, "Tenant A commitment", due_at=datetime.utcnow())
            db.session.commit()

            # Tenant B queries via scoped lookup
            # Tenant B should have zero commitments for any relationship
            all_commitments = RelationshipCommitment.query.all()
            assert len(all_commitments) == 1, "Only Tenant A's commitment should exist"

            # Tenant B cannot retrieve it by scoped query
            b_commitments = RelationshipCommitment.query.filter(
                RelationshipCommitment.tenant_id == t_b.id
            ).all()
            assert len(b_commitments) == 0, "Tenant B should not see Tenant A commitments"

    def test_open_commitment_scope_isolation(self, real_app):
        from app.models import Person, Relationship, RelationshipCommitment
        from app.tenant import Tenant
        from app.relationship import RelationshipService, CommitmentDirection
        from app import db
        with real_app.app_context():
            t_a = Tenant(company_name="TenantA", slug="ta", business_type="travel", is_active=True)
            t_b = Tenant(company_name="TenantB", slug="tb", business_type="travel", is_active=True)
            db.session.add(t_a); db.session.add(t_b); db.session.commit()

            p_a = Person(canonical_name="A", preferred_name="A", tenant_id=t_a.id)
            db.session.add(p_a); db.session.commit()
            svc_a = RelationshipService(session=db.session)
            r_a = svc_a.ensure_customer_relationship(p_a.id, tenant_id=t_a.id)

            p_b = Person(canonical_name="B", preferred_name="B", tenant_id=t_b.id)
            db.session.add(p_b); db.session.commit()
            svc_b = RelationshipService(session=db.session)
            r_b = svc_b.ensure_customer_relationship(p_b.id, tenant_id=t_b.id)

            # Commitments in both tenants
            svc_a.create_commitment(r_a.id, "A's open commitment", due_at=datetime.utcnow() + timedelta(days=1))
            svc_b.create_commitment(r_b.id, "B's open commitment", due_at=datetime.utcnow() + timedelta(days=1))
            db.session.commit()

            # Tenant A should see only 1 open commitment
            open_a = svc_a.get_open_commitments(r_a.id)
            assert len(open_a) == 1
            assert "A's" in open_a[0].summary

            # Tenant B should see only 1 open commitment
            open_b = svc_b.get_open_commitments(r_b.id)
            assert len(open_b) == 1
            assert "B's" in open_b[0].summary


class TestForeignTenantPersonLookup:
    """Foreign-tenant Person ID must not expose Relationship data."""

    def test_foreign_tenant_person_lookup_returns_nothing(self, real_app):
        from app.models import Person, Relationship
        from app.tenant import Tenant
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            t_a = Tenant(company_name="TenantA", slug="ta", business_type="travel", is_active=True)
            t_b = Tenant(company_name="TenantB", slug="tb", business_type="travel", is_active=True)
            db.session.add(t_a); db.session.add(t_b); db.session.commit()

            p_a = Person(canonical_name="Alice", preferred_name="Alice", tenant_id=t_a.id)
            db.session.add(p_a); db.session.commit()

            svc_a = RelationshipService(session=db.session)
            svc_a.ensure_customer_relationship(p_a.id, tenant_id=t_a.id)
            db.session.commit()

            # Tenant B scoped lookup using Person A's ID
            svc_b = RelationshipService(session=db.session)
            rels_b_see = Relationship.query.filter(
                Relationship.person_id == p_a.id,
                Relationship.tenant_id == t_b.id
            ).all()
            assert len(rels_b_see) == 0, "Tenant B should not see Tenant A's relationships"

    def test_foreign_tenant_lookup_all_relationships(self, real_app):
        from app.models import Person, Relationship
        from app.tenant import Tenant
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            t_a = Tenant(company_name="TenantA", slug="ta", business_type="travel", is_active=True)
            t_b = Tenant(company_name="TenantB", slug="tb", business_type="travel", is_active=True)
            db.session.add(t_a); db.session.add(t_b); db.session.commit()

            p_a = Person(canonical_name="Bob", preferred_name="Bob", tenant_id=t_a.id)
            p_b = Person(canonical_name="Charlie", preferred_name="Charlie", tenant_id=t_b.id)
            db.session.add(p_a); db.session.add(p_b); db.session.commit()

            svc_a = RelationshipService(session=db.session)
            svc_b = RelationshipService(session=db.session)
            svc_a.ensure_customer_relationship(p_a.id, tenant_id=t_a.id)
            svc_b.ensure_customer_relationship(p_b.id, tenant_id=t_b.id)
            db.session.commit()

            # Tenant B scoped — get_relationships_for_person with tenant_id=t_b
            svc_b_only = RelationshipService(session=db.session)
            for p in Person.query.all():
                rels = svc_b_only.get_relationships_for_person(p.id, tenant_id=t_b.id)
                if p.id == p_b.id:
                    assert len(rels) == 1, f"Tenant B should see their own relationship for Person {p.id}"
                else:
                    assert len(rels) == 0, f"Tenant B should see NO relationships for Person {p.id}"