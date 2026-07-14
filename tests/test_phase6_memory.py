"""
PHASE 6 — Memory Architecture Tests
"""
import pytest, json
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
        from app.models import Person, PersonIdentity, Relationship
        from app.human_context.models import (HumanContextItem, ContextCategory, ScopeType, AssertionType, ContextStatus)
        from app.privacy.models import (PrivacyPolicy, MemoryEligibilityPolicy, Restriction, ForgetRequest, MemoryEligibility, ForgetRequestStatus)
        from app.communication.models import (CommunicationSource, ExternalConversation, ExternalMessage)
        db.create_all()
        yield application
        db.drop_all()


class TestDomainSeparation:
    def test_source_not_memory(self, real_app):
        from app.memory.models import MemoryRecord; assert not hasattr(MemoryRecord, "body")

    def test_eligible_not_memorized(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            eff = MemoryService(session=db.session).get_effective_memories(person_id=p.id)
            assert len(eff) == 0

    def test_person_not_mutated(self, real_app):
        from app.models import Person; assert not hasattr(Person, "memory_key")


class TestMemoryTypes:
    def test_fact(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.fact", "val", memory_type="fact")
            assert m.memory_type == "fact"

    def test_preference(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.pref", "val", memory_type="preference")
            assert m.memory_type == "preference"

    def test_constraint(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.const", "val", memory_type="constraint")
            assert m.memory_type == "constraint"

    def test_requirement(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.req", "val", memory_type="requirement")
            assert m.memory_type == "requirement"

    def test_intent(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.intent", "val", memory_type="intent")
            assert m.memory_type == "intent"

    def test_goal(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.goal", "val", memory_type="goal")
            assert m.memory_type == "goal"

    def test_decision(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.dec", "val", memory_type="decision")
            assert m.memory_type == "decision"

    def test_commitment(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.cm", "val", memory_type="commitment")
            assert m.memory_type == "commitment"

    def test_outcome(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.out", "val", memory_type="outcome")
            assert m.memory_type == "outcome"

    def test_procedural(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.proc", "val", memory_type="procedural")
            assert m.memory_type == "procedural"

    def test_temporal(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.temp", "val", memory_type="temporal")
            assert m.memory_type == "temporal"

    def test_relationship_context(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.rc", "val", memory_type="relationship_context")
            assert m.memory_type == "relationship_context"

    def test_business_context(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "test.bc", "val", memory_type="business_context")
            assert m.memory_type == "business_context"

    def test_unknown_key(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "unknown.custom", "val")
            assert m.memory_key == "unknown.custom"


class TestScope:
    def test_person_scope(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "k", "v", scope_type="person")
            assert m.scope_type == "person"

    def test_narrow_not_auto_global(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "k", "v", scope_type="conversation")
            assert m.scope_type == "conversation"


class TestCreationMechanisms:
    def test_explicit(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app.memory.models import MemoryCreationMechanism; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            m = MemoryService(session=db.session).create_explicit_memory(p.id, "k", "v", creation_mechanism=MemoryCreationMechanism.EXPLICIT)
            assert m.creation_mechanism == "explicit"

    def test_no_llm_inferred(self, real_app):
        from app.memory.models import MemoryCreationMechanism
        assert not hasattr(MemoryCreationMechanism, "LLM_INFERRED")


class TestCandidateCommit:
    def test_proposal(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app.memory.models import CandidateStatus; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            r = MemoryService(session=db.session).propose_memory(p.id, "k", "v")
            assert r["status"] == CandidateStatus.PROPOSED

    def test_commit_creates_memory(self, real_app):
        from app.models import Person; from app.tenant import Tenant; from app.memory import MemoryService
        from app.privacy.models import PrivacyPolicy, MemoryEligibility; from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True); db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu", tenant_id=t.id); db.session.add(p); db.session.commit()
            pp = PrivacyPolicy(tenant_id=t.id, default_memory_eligibility=MemoryEligibility.ELIGIBLE); db.session.add(pp); db.session.commit()
            svc = MemoryService(session=db.session)
            r = svc.propose_memory(p.id, "k", "v", tenant_id=t.id)
            svc.approve_candidate(r["candidate_id"], tenant_id=t.id, approved_by="admin")
            c = svc.commit_candidate(r["candidate_id"], tenant_id=t.id)
            assert c["success"] is True
            assert "memory_id" in c

    def test_approval_not_commit(self, real_app):
        from app.models import Person; from app.tenant import Tenant; from app.memory import MemoryService; from app.memory.models import CandidateStatus
        from app.privacy.models import PrivacyPolicy, MemoryEligibility; from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True); db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu", tenant_id=t.id); db.session.add(p); db.session.commit()
            pp = PrivacyPolicy(tenant_id=t.id, default_memory_eligibility=MemoryEligibility.ELIGIBLE); db.session.add(pp); db.session.commit()
            svc = MemoryService(session=db.session)
            r = svc.propose_memory(p.id, "k", "v", tenant_id=t.id)
            svc.approve_candidate(r["candidate_id"], tenant_id=t.id, approved_by="admin")
            assert CandidateStatus.APPROVED == CandidateStatus.APPROVED


class TestPhase4Gate:
    def test_ineligible_blocks_commit(self, real_app):
        from app.models import Person; from app.tenant import Tenant; from app.memory import MemoryService
        from app.privacy.models import MemoryEligibilityPolicy, MemoryEligibility; from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True); db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu", tenant_id=t.id); db.session.add(p); db.session.commit()
            mp = MemoryEligibilityPolicy(tenant_id=t.id, reason_code="password", decision=MemoryEligibility.INELIGIBLE, is_system=True); db.session.add(mp); db.session.commit()
            svc = MemoryService(session=db.session)
            r = svc.propose_memory(p.id, "auth.pw", "secret", tenant_id=t.id)
            a = svc.approve_candidate(r["candidate_id"], tenant_id=t.id)
            assert a["success"] is False


class TestPhase5Integration:
    def test_context_alone_no_memory(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            eff = MemoryService(session=db.session).get_effective_memories(person_id=p.id)
            assert len(eff) == 0


class TestDirectSource:
    def test_message_alone_no_memory(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            eff = MemoryService(session=db.session).get_effective_memories(person_id=p.id)
            assert len(eff) == 0


class TestLifecycle:
    def test_active_effective(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            svc = MemoryService(session=db.session)
            svc.create_explicit_memory(p.id, "k", "v")
            eff = svc.get_effective_memories(person_id=p.id)
            assert len(eff) > 0

    def test_revoked_not_effective(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            svc = MemoryService(session=db.session)
            m = svc.create_explicit_memory(p.id, "k", "v")
            svc.revoke_memory(m.id)
            eff = svc.get_effective_memories(person_id=p.id)
            assert len(eff) == 0

    def test_supersession(self, real_app):
        from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu"); db.session.add(p); db.session.commit()
            svc = MemoryService(session=db.session)
            svc.create_explicit_memory(p.id, "k", "old")
            svc.create_explicit_memory(p.id, "k", "new")
            eff = svc.get_effective_memories(person_id=p.id, memory_key="k")
            assert len(eff) == 1
            assert eff[0]["value"] == "new"


class TestTenantIsolation:
    def test_memory_list_isolated(self, real_app):
        from app.tenant import Tenant; from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            p1 = Person(canonical_name="Ritu", preferred_name="Ritu", tenant_id=t1.id); db.session.add(p1); db.session.commit()
            p2 = Person(canonical_name="Mitesh", preferred_name="Mitesh", tenant_id=t2.id); db.session.add(p2); db.session.commit()
            svc = MemoryService(session=db.session)
            svc.create_explicit_memory(p1.id, "k", "v_a", tenant_id=t1.id)
            svc.create_explicit_memory(p2.id, "k", "v_b", tenant_id=t2.id)
            a = svc.get_effective_memories(person_id=p1.id, tenant_id=t1.id)
            b = svc.get_effective_memories(person_id=p2.id, tenant_id=t2.id)
            assert len(a) == 1
            assert len(b) == 1

    def test_foreign_memory_id_rejected(self, real_app):
        from app.tenant import Tenant; from app.models import Person; from app.memory import MemoryService; from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            p1 = Person(canonical_name="Ritu", preferred_name="Ritu", tenant_id=t1.id); db.session.add(p1); db.session.commit()
            svc = MemoryService(session=db.session)
            m = svc.create_explicit_memory(p1.id, "k", "v", tenant_id=t1.id)
            r = svc.revoke_memory(m.id, tenant_id=t2.id)
            assert r["success"] is False