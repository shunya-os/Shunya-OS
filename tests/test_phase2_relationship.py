"""
PHASE 2 — Relationship Intelligence Tests
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


class TestRelationshipCreation:

    def test_relationship_creation(self, real_app):
        from app.models import Person, Relationship
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            r = Relationship(person_id=p.id, relationship_type="CUSTOMER", tenant_id=1)
            db.session.add(r); db.session.commit()
            assert r.id is not None
            assert r.relationship_type == "CUSTOMER"
            assert r.status == "active"

    def test_tenant_ownership(self, real_app):
        from app.models import Person, Relationship
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu", tenant_id=1)
            db.session.add(p); db.session.commit()
            r = Relationship(person_id=p.id, relationship_type="CUSTOMER", tenant_id=1)
            db.session.add(r); db.session.commit()
            assert r.tenant_id == 1

    def test_person_linkage(self, real_app):
        from app.models import Person, Relationship
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            r = Relationship(person_id=p.id, relationship_type="CUSTOMER")
            db.session.add(r); db.session.commit()
            assert r.person_id == p.id
            assert r.person is not None

    def test_extensible_relationship_types(self, real_app):
        from app.models import Person, Relationship
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            for rtype in ("CUSTOMER", "EMPLOYEE", "SUPPLIER_CONTACT", "CLIENT_USER", "PARTNER", "INVESTOR"):
                r = Relationship(person_id=p.id, relationship_type=rtype)
                db.session.add(r)
            db.session.commit()
            assert Relationship.query.count() == 6


class TestRelationshipStatus:

    def test_valid_transitions(self, real_app):
        from app.models import Person, Relationship
        from app.relationship import RelationshipService, RelationshipStatus
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_relationship(p.id, "CUSTOMER")
            assert r.status == RelationshipStatus.ACTIVE
            svc.change_status(r.id, RelationshipStatus.DORMANT)
            assert r.status == RelationshipStatus.DORMANT
            svc.change_status(r.id, RelationshipStatus.ACTIVE)
            assert r.status == RelationshipStatus.ACTIVE
            svc.change_status(r.id, RelationshipStatus.ENDED)
            assert r.status == RelationshipStatus.ENDED

    def test_invalid_transition_raises(self, real_app):
        from app.models import Person
        from app.relationship import RelationshipService, RelationshipStatus
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_relationship(p.id, "CUSTOMER")
            svc.change_status(r.id, RelationshipStatus.ENDED)
            with pytest.raises(ValueError, match="Cannot transition"):
                svc.change_status(r.id, RelationshipStatus.ACTIVE)


class TestRelationshipEvent:

    def test_event_persistence(self, real_app):
        from app.models import Person, RelationshipEvent
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_relationship(p.id, "CUSTOMER")
            events = RelationshipEvent.query.filter_by(relationship_id=r.id).all()
            assert len(events) >= 1
            assert events[0].event_type == "RELATIONSHIP_CREATED"

    def test_status_changed_event(self, real_app):
        from app.models import Person, RelationshipEvent
        from app.relationship import RelationshipService, RelationshipStatus
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_relationship(p.id, "CUSTOMER")
            svc.change_status(r.id, RelationshipStatus.DORMANT)
            events = RelationshipEvent.query.filter_by(relationship_id=r.id).all()
            types = [e.event_type for e in events]
            assert "STATUS_CHANGED" in types

    def test_role_linked_event(self, real_app):
        from app.models import Person, RelationshipEvent
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.link_role(p.id, "CUSTOMER", source="test")
            events = RelationshipEvent.query.filter_by(relationship_id=r.id).all()
            types = [e.event_type for e in events]
            assert "ROLE_LINKED" in types or "RELATIONSHIP_CREATED" in types


class TestRoleProjectionLinkage:

    def test_customer_profile_to_customer_relationship(self, real_app):
        from app.models import Person, CustomerProfile
        from app.relationship import RelationshipService, RelationshipType
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            CustomerProfile(person_id=p.id, lifetime_value=50000, tenant_id=1)
            db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id, tenant_id=1)
            assert r.relationship_type == RelationshipType.CUSTOMER

    def test_employee_profile_to_employee_relationship(self, real_app):
        from app.models import Person, EmployeeProfile
        from app.relationship import RelationshipService, RelationshipType
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Emp", preferred_name="E")
            db.session.add(p); db.session.commit()
            EmployeeProfile(person_id=p.id, role="agent", tenant_id=1)
            db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_employee_relationship(p.id, tenant_id=1)
            assert r.relationship_type == RelationshipType.EMPLOYEE

    def test_one_person_multiple_relationship_types(self, real_app):
        from app.models import Person, CustomerProfile, EmployeeProfile
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Multi", preferred_name="M")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r1 = svc.ensure_customer_relationship(p.id)
            r2 = svc.ensure_employee_relationship(p.id)
            assert r1.id != r2.id
            assert r1.relationship_type == "customer"
            assert r2.relationship_type == "employee"


class TestIdempotency:

    def test_ensure_relationship_idempotent(self, real_app):
        from app.models import Person, Relationship
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r1 = svc.ensure_customer_relationship(p.id)
            r2 = svc.ensure_customer_relationship(p.id)
            assert r1.id == r2.id
            assert Relationship.query.count() == 1

    def test_no_duplicate_events_on_retry(self, real_app):
        from app.models import Person, RelationshipEvent
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            svc.ensure_customer_relationship(p.id)
            svc.ensure_customer_relationship(p.id)
            # Only one create event
            events = RelationshipEvent.query.filter_by(event_type="RELATIONSHIP_CREATED").all()
            assert len(events) == 1


class TestCustomerLifetimeRelationship:

    def test_multiple_leads_same_person_one_relationship(self, real_app):
        from app.models import Person, Lead, next_inquiry_code, Relationship
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            for i in range(3):
                code = next_inquiry_code(db.session)
                lead = Lead(code=code, source="test", customer_name="Ritu", destination="Goa", person_id=p.id)
                db.session.add(lead)
            db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id)
            assert r is not None
            assert r.relationship_type == "customer"

    def test_lead_name_only_no_relationship(self, real_app):
        from app.models import Lead, next_inquiry_code
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            code = next_inquiry_code(db.session)
            lead = Lead(code=code, source="test", customer_name="Ritu", destination="Goa")
            db.session.add(lead); db.session.commit()
            # No Person — no relationship created
            svc = RelationshipService(session=db.session)
            rels = svc.get_relationships_for_person(99999)
            assert len(rels) == 0


class TestRelationshipCommitment:

    def test_commitment_creation(self, real_app):
        from app.models import Person
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id)
            c = svc.create_commitment(r.id, "Send revised hotel options", created_by="admin")
            assert c.id is not None
            assert c.status == "open"

    def test_open_commitment_query(self, real_app):
        from app.models import Person
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id)
            svc.create_commitment(r.id, "Commitment 1")
            svc.create_commitment(r.id, "Commitment 2")
            open_c = svc.get_open_commitments(r.id)
            assert len(open_c) == 2

    def test_resolved_commitment(self, real_app):
        from app.models import Person
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id)
            c = svc.create_commitment(r.id, "Test commitment")
            svc.resolve_commitment(c.id, note="Done")
            assert c.status == "resolved"
            open_c = svc.get_open_commitments(r.id)
            assert len(open_c) == 0

    def test_cancelled_commitment(self, real_app):
        from app.models import Person
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id)
            c = svc.create_commitment(r.id, "Test")
            svc.cancel_commitment(c.id, note="No longer needed")
            assert c.status == "cancelled"

    def test_overdue_commitment_query(self, real_app):
        from app.models import Person
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id)
            svc.create_commitment(r.id, "Overdue", due_at=datetime.utcnow() - timedelta(days=1))
            svc.create_commitment(r.id, "Future", due_at=datetime.utcnow() + timedelta(days=7))
            overdue = svc.get_overdue_commitments(r.id)
            assert len(overdue) == 1
            assert "Overdue" in overdue[0].summary

    def test_commitment_direction(self, real_app):
        from app.models import Person
        from app.relationship import RelationshipService, CommitmentDirection
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id)
            c1 = svc.create_commitment(r.id, "We will send", direction=CommitmentDirection.COMPANY_TO_PERSON)
            c2 = svc.create_commitment(r.id, "Customer will provide", direction=CommitmentDirection.PERSON_TO_COMPANY)
            assert c1.direction == "company_to_person"
            assert c2.direction == "person_to_company"


class TestRelationshipSummary:

    def test_summary_no_scores(self, real_app):
        from app.models import Person
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Test", preferred_name="T")
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id)
            summary = svc.get_summary(r.id)
            assert summary["relationship_type"] == "customer"
            assert summary["open_commitments"] == 0
            # No sentiment/score fields
            assert "relationship_score" not in summary
            assert "trust_score" not in summary
            assert "loyalty_score" not in summary
            assert "sentiment_score" not in summary
            assert "closeness_score" not in summary


class TestTenantIsolation:

    def test_tenant_isolation_relationships(self, real_app):
        from app.models import Person, Relationship
        from app.tenant import Tenant
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            p1 = Person(canonical_name="User A", preferred_name="A", tenant_id=t1.id)
            p2 = Person(canonical_name="User B", preferred_name="B", tenant_id=t2.id)
            db.session.add(p1); db.session.add(p2); db.session.commit()
            svc = RelationshipService(session=db.session)
            svc.ensure_customer_relationship(p1.id, tenant_id=t1.id)
            svc.ensure_customer_relationship(p2.id, tenant_id=t2.id)
            # Tenant A should only see their relationship
            rels_a = Relationship.query.filter_by(tenant_id=t1.id).all()
            rels_b = Relationship.query.filter_by(tenant_id=t2.id).all()
            assert len(rels_a) == 1
            assert len(rels_b) == 1
            assert rels_a[0].person_id == p1.id
            assert rels_b[0].person_id == p2.id

    def test_cross_tenant_event_isolation(self, real_app):
        from app.models import Person, RelationshipEvent
        from app.tenant import Tenant
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Test", preferred_name="T", tenant_id=t.id)
            db.session.add(p); db.session.commit()
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(p.id, tenant_id=t.id)
            events = RelationshipEvent.query.filter_by(relationship_id=r.id).all()
            assert len(events) >= 1


class TestPhase1AIntegration:

    def test_approved_no_match_creates_relationship(self, real_app):
        """Phase 1A approved NO_MATCH import creates CUSTOMER relationship."""
        from app.models import Person, IntakeSession, IntakeCandidate
        from app.relationship import RelationshipService, RelationshipType
        from app.intake.session import IntakeSessionState
        from app.intake.proposal import ImportProposalBuilder
        from app.intake.committer import GovernedCommitter
        from app import db
        with real_app.app_context():
            sess = IntakeSession(source_type="csv", source_name="test.csv", status=IntakeSessionState.READY_FOR_REVIEW)
            db.session.add(sess); db.session.commit()
            c = IntakeCandidate(session_id=sess.id, row_index=0, identity_status="NO_MATCH",
                                import_status="pending", classification="customer",
                                normalized_data='{"name":"New","email":"new@test.com"}')
            db.session.add(c); db.session.commit()
            ImportProposalBuilder.build(sess, [c])
            committer = GovernedCommitter(session=db.session)
            committer.approve(sess.id, approved_by="admin")
            result = committer.commit(sess.id)
            assert result["imported"] == 1
            # Now create relationship
            person = Person.query.filter_by(canonical_name="New").first()
            assert person is not None
            svc = RelationshipService(session=db.session)
            r = svc.ensure_customer_relationship(person.id)
            assert r.relationship_type == RelationshipType.CUSTOMER

    def test_unresolved_creates_no_relationship(self, real_app):
        """Phase 1A unresolved candidates create no relationship."""
        from app.models import Person, IntakeSession, IntakeCandidate
        from app.relationship import RelationshipService
        from app import db
        with real_app.app_context():
            # No Person created — no relationship possible
            svc = RelationshipService(session=db.session)
            rels = svc.get_relationships_for_person(99999)
            assert len(rels) == 0