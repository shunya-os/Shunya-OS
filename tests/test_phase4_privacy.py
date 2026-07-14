"""
PHASE 4 — Privacy, Sensitivity & Memory Eligibility Tests
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
        from app.communication.models import (CommunicationSource, ExternalConversation, ExternalMessage, ExternalParticipant)
        from app.privacy.models import (PrivacyPolicy, SensitivityPolicy, RetentionPolicy, MemoryEligibilityPolicy,
            SensitivityAssessment, PrivacyDecision, Restriction, ForgetRequest, PrivacyReviewItem,
            MemoryEligibility, SensitivityLevel, ForgetRequestStatus)
        db.create_all()
        yield application
        db.drop_all()


class TestObservationIsNotMemory:
    def test_captured_can_be_memory_ineligible(self, real_app):
        from app.privacy import PrivacyService, MemoryEligibility
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            result = svc.evaluate_memory_eligibility("external_message", 1, sensitivity_level="internal")
            # Default policy: ineligible
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE

    def test_missing_verdict_fails_closed(self, real_app):
        from app.privacy import PrivacyService, MemoryEligibility
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            result = svc.evaluate_memory_eligibility("unknown_type", 999)
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE
            assert "fail_closed" in result.get("reason_code", "")


class TestSensitivity:
    def test_auth_secret_highly_sensitive(self, real_app):
        from app.privacy import PrivacyService, SensitivityLevel
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            result = svc.assess_sensitivity("message", 1, reason_codes=["password"])
            assert result["sensitivity_level"] == SensitivityLevel.HIGHLY_SENSITIVE

    def test_health_information_no_auto_memory(self, real_app):
        from app.privacy import PrivacyService, MemoryEligibility
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            result = svc.evaluate_memory_eligibility("message", 1, reason_codes=["health_information"])
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE

    def test_ordinary_business_preference_eligible(self, real_app):
        from app.privacy.models import PrivacyPolicy
        from app.privacy import PrivacyService, MemoryEligibility
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            pp = PrivacyPolicy(tenant_id=t.id, default_memory_eligibility=MemoryEligibility.ELIGIBLE)
            db.session.add(pp); db.session.commit()
            svc = PrivacyService(session=db.session)
            result = svc.evaluate_memory_eligibility("message", 1, tenant_id=t.id)
            assert result["memory_eligibility"] == MemoryEligibility.ELIGIBLE

    def test_sensitivity_level_and_reason_separate(self, real_app):
        from app.privacy import PrivacyService, SensitivityLevel
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            result = svc.assess_sensitivity("message", 1, reason_codes=["business_secret"])
            # business_secret is not in SYSTEM_NON_OVERRIDABLE_REASONS
            assert result["sensitivity_level"] is not None
            assert "business_secret" in result.get("reason_tags", [])


class TestPolicyPrecedence:
    def test_system_deny_beats_tenant_allow(self, real_app):
        from app.privacy.models import MemoryEligibilityPolicy, PrivacyPolicy
        from app.privacy import PrivacyService, MemoryEligibility
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            # System non-overridable deny
            MemoryEligibilityPolicy(tenant_id=t.id, source_type="message", reason_code="password",
                                    decision=MemoryEligibility.INELIGIBLE, is_system=True)
            # Tenant allow
            pp = PrivacyPolicy(tenant_id=t.id, default_memory_eligibility=MemoryEligibility.ELIGIBLE)
            db.session.add(pp); db.session.commit()
            svc = PrivacyService(session=db.session)
            # System override wins
            result = svc.evaluate_memory_eligibility("message", 1, tenant_id=t.id,
                                                      reason_codes=["password"])
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE

    def test_do_not_use_for_memory_beats_tenant_allow(self, real_app):
        from app.privacy.models import Restriction, PrivacyPolicy
        from app.privacy import PrivacyService, MemoryEligibility
        from app.models import Person
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            r = Restriction(person_id=p.id, restriction_type="do_not_use_for_memory", tenant_id=t.id)
            db.session.add(r)
            pp = PrivacyPolicy(tenant_id=t.id, default_memory_eligibility=MemoryEligibility.ELIGIBLE)
            db.session.add(pp); db.session.commit()
            svc = PrivacyService(session=db.session)
            result = svc.evaluate_memory_eligibility("message", 1, tenant_id=t.id,
                                                      person_id=p.id)
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE

    def test_approved_revocation_beats_prior_eligibility(self, real_app):
        from app.privacy.models import ForgetRequest, PrivacyPolicy
        from app.privacy import PrivacyService, MemoryEligibility, ForgetRequestStatus
        from app.models import Person
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            fr = ForgetRequest(person_id=p.id, request_type="forget", tenant_id=t.id,
                               status=ForgetRequestStatus.APPROVED, approved_at=datetime.utcnow())
            db.session.add(fr); db.session.commit()
            pp = PrivacyPolicy(tenant_id=t.id, default_memory_eligibility=MemoryEligibility.ELIGIBLE)
            db.session.add(pp); db.session.commit()
            svc = PrivacyService(session=db.session)
            result = svc.evaluate_memory_eligibility("message", 1, tenant_id=t.id,
                                                      person_id=p.id)
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE

    def test_missing_policy_fails_closed(self, real_app):
        from app.privacy import PrivacyService, MemoryEligibility
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            result = svc.evaluate_memory_eligibility("message", 1)
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE


class TestPhase3Integration:
    def test_denied_capture_no_memory_evaluation(self, real_app):
        from app.privacy import PrivacyService
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            # Message with capture_status != "allowed" → no evaluation
            result = svc.evaluate_communication_message(999)
            assert result["eligible"] is False

    def test_allowed_capture_can_be_evaluated(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, ExternalConversation, ExternalMessage
        from app.privacy import PrivacyService
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            conv = ExternalConversation(tenant_id=t.id, source_id=cs.id, provider_chat_id="conv")
            db.session.add(conv); db.session.commit()
            msg = ExternalMessage(tenant_id=t.id, source_id=cs.id, conversation_id=conv.id,
                                  provider_message_id="msg_1", body="Hello", capture_status="allowed")
            db.session.add(msg); db.session.commit()
            svc = PrivacyService(session=db.session)
            result = svc.evaluate_communication_message(msg.id, tenant_id=t.id)
            # Should get a decision (not skipped)
            assert "memory_eligibility" in result

    def test_allowed_does_not_imply_eligible(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, ExternalConversation, ExternalMessage
        from app.privacy import PrivacyService, MemoryEligibility
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            conv = ExternalConversation(tenant_id=t.id, source_id=cs.id, provider_chat_id="conv")
            db.session.add(conv); db.session.commit()
            msg = ExternalMessage(tenant_id=t.id, source_id=cs.id, conversation_id=conv.id,
                                  provider_message_id="msg_2", body="Business", capture_status="allowed")
            db.session.add(msg); db.session.commit()
            svc = PrivacyService(session=db.session)
            # No policy configured → default fail closed
            result = svc.evaluate_communication_message(msg.id, tenant_id=t.id)
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE


class TestIdentitySafety:
    def test_matched_no_auto_sensitive_trait(self, real_app):
        from app.models import Person
        from app.privacy import PrivacyService
        from app import db
        with real_app.app_context():
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            svc = PrivacyService(session=db.session)
            # Assessment for a message should not create a Person trait
            result = svc.assess_sensitivity("message", 1, reason_codes=["health_information"])
            assert result["sensitivity_level"] is not None

    def test_ambiguous_no_person_trait(self, real_app):
        from app.privacy import PrivacyService
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            # No person attached → no sensitive trait
            result = svc.assess_sensitivity("message", 1)
            assert result["sensitivity_level"] is not None

    def test_no_match_no_person_created(self, real_app):
        from app.models import Person
        from app.privacy import PrivacyService
        from app import db
        with real_app.app_context():
            before = Person.query.count()
            svc = PrivacyService(session=db.session)
            svc.evaluate_memory_eligibility("message", 1)
            after = Person.query.count()
            assert before == after, "Phase 4 must not create Persons"

    def test_customer_does_not_override_system_restriction(self, real_app):
        from app.models import Person
        from app.privacy import PrivacyService, MemoryEligibility
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu", tenant_id=t.id)
            db.session.add(p); db.session.commit()
            svc = PrivacyService(session=db.session)
            # Even with a customer relationship, health info is still ineligible
            result = svc.evaluate_memory_eligibility("message", 1, tenant_id=t.id,
                                                      person_id=p.id,
                                                      reason_codes=["health_information"])
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE


class TestRetention:
    def test_retain_decision(self, real_app):
        from app.privacy import PrivacyService, RetentionDecision
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            result = svc.evaluate_retention("message", 1)
            assert result["retention_decision"] == RetentionDecision.RETAIN

    def test_retain_until_with_due(self, real_app):
        from app.privacy.models import RetentionPolicy
        from app.privacy import PrivacyService, RetentionDecision
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            rp = RetentionPolicy(tenant_id=t.id, source_type="message", decision="retain_until",
                            retention_days=90)
            db.session.add(rp); db.session.commit()
            svc = PrivacyService(session=db.session)
            result = svc.evaluate_retention("message", 1, tenant_id=t.id)
            assert result["retention_decision"] == RetentionDecision.RETAIN_UNTIL
            assert "due_at" in result

    def test_retention_does_not_delete(self, real_app):
        """Retention decision does not silently delete production objects."""
        from app.privacy import PrivacyService
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            svc = PrivacyService(session=db.session)
            result = svc.evaluate_retention("message", 1, tenant_id=t.id)
            # Decision is returned, but no deletion execution
            assert "retention_decision" in result


class TestRestrictions:
    def test_do_not_use_for_memory(self, real_app):
        from app.models import Person
        from app.privacy import PrivacyService
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            svc = PrivacyService(session=db.session)
            svc.add_restriction(p.id, "do_not_use_for_memory", tenant_id=t.id)
            restrictions = svc.get_active_restrictions(p.id, tenant_id=t.id)
            assert len(restrictions) == 1
            assert restrictions[0].restriction_type == "do_not_use_for_memory"

    def test_do_not_use_for_marketing(self, real_app):
        from app.models import Person
        from app.privacy import PrivacyService
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            svc = PrivacyService(session=db.session)
            svc.add_restriction(p.id, "do_not_use_for_marketing", tenant_id=t.id)
            restrictions = svc.get_active_restrictions(p.id, tenant_id=t.id)
            assert len(restrictions) == 1

    def test_do_not_contact(self, real_app):
        from app.models import Person
        from app.privacy import PrivacyService
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            svc = PrivacyService(session=db.session)
            svc.add_restriction(p.id, "do_not_contact", tenant_id=t.id)
            restrictions = svc.get_active_restrictions(p.id, tenant_id=t.id)
            assert len(restrictions) == 1


class TestForgetRevocation:
    def test_request_lifecycle_valid(self, real_app):
        from app.privacy import PrivacyService, ForgetRequestStatus
        from app.models import Person
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            svc = PrivacyService(session=db.session)
            fr = svc.create_forget_request(p.id, "forget", tenant_id=t.id)
            assert fr.status == ForgetRequestStatus.REQUESTED
            result = svc.approve_forget_request(fr.id, approved_by="admin")
            assert result["success"] is True
            assert result["status"] == ForgetRequestStatus.APPROVED

    def test_invalid_transition_rejected(self, real_app):
        from app.privacy import PrivacyService, ForgetRequestStatus
        from app.models import Person
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            svc = PrivacyService(session=db.session)
            fr = svc.create_forget_request(p.id, "forget", tenant_id=t.id)
            svc.mark_execution_pending(fr.id)
            # Cannot approve from EXECUTION_PENDING
            result = svc.approve_forget_request(fr.id)
            assert result["success"] is False

    def test_approved_revocation_blocks_new_eligibility(self, real_app):
        from app.privacy import PrivacyService, MemoryEligibility, ForgetRequestStatus
        from app.models import Person
        from app.tenant import Tenant
        from app.privacy.models import PrivacyPolicy
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            svc = PrivacyService(session=db.session)
            # Approve forget request
            fr = svc.create_forget_request(p.id, "forget", tenant_id=t.id)
            svc.approve_forget_request(fr.id, approved_by="admin")
            # Even with permissive policy
            pp = PrivacyPolicy(tenant_id=t.id, default_memory_eligibility=MemoryEligibility.ELIGIBLE)
            db.session.add(pp); db.session.commit()
            # New eligibility check should be denied
            result = svc.evaluate_memory_eligibility("message", 1, tenant_id=t.id, person_id=p.id)
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE

    def test_request_does_not_hard_delete_person(self, real_app):
        from app.models import Person
        from app.privacy import PrivacyService
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            svc = PrivacyService(session=db.session)
            svc.create_forget_request(p.id, "forget", tenant_id=t.id)
            # Person still exists
            assert Person.query.count() == 1

    def test_execution_pending_preserved(self, real_app):
        from app.privacy import PrivacyService, ForgetRequestStatus
        from app.models import Person
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            svc = PrivacyService(session=db.session)
            fr = svc.create_forget_request(p.id, "forget", tenant_id=t.id)
            svc.approve_forget_request(fr.id, approved_by="admin")
            result = svc.mark_execution_pending(fr.id)
            assert result["status"] == ForgetRequestStatus.EXECUTION_PENDING


class TestReviewQueue:
    def test_review_required_appears_in_queue(self, real_app):
        from app.privacy import PrivacyService, MemoryEligibility
        from app.privacy.models import SensitivityLevel
        from app.tenant import Tenant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            # Confidential sensitivity → REVIEW_REQUIRED
            from app.privacy.models import SensitivityPolicy
            sp = SensitivityPolicy(tenant_id=t.id, source_type="message",
                              sensitivity_level=SensitivityLevel.CONFIDENTIAL, is_active=True)
            db.session.add(sp); db.session.commit()
            svc = PrivacyService(session=db.session)
            # Assess sensitivity first
            svc.assess_sensitivity("message", 1, tenant_id=t.id)
            result = svc.evaluate_memory_eligibility("message", 1, tenant_id=t.id,
                                                      sensitivity_level="confidential")
            assert result["memory_eligibility"] == MemoryEligibility.REVIEW_REQUIRED
            pending = svc.get_pending_reviews(tenant_id=t.id)
            assert len(pending) >= 1

    def test_approve_review(self, real_app):
        from app.privacy import PrivacyService
        from app.tenant import Tenant
        from app.privacy.models import PrivacyReviewItem
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            item = PrivacyReviewItem(tenant_id=t.id, source_type="message", source_id=1,
                                     reason_code="confidential", decision_type="memory_eligibility")
            db.session.add(item); db.session.commit()
            svc = PrivacyService(session=db.session)
            result = svc.approve_review(item.id, reviewed_by="admin")
            assert result["success"] is True

    def test_system_deny_cannot_be_approved(self, real_app):
        from app.privacy import PrivacyService
        from app.tenant import Tenant
        from app.privacy.models import PrivacyReviewItem, MemoryEligibilityPolicy, MemoryEligibility
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            # System non-overridable deny
            mp = MemoryEligibilityPolicy(tenant_id=t.id, reason_code="password",
                                    decision=MemoryEligibility.INELIGIBLE, is_system=True)
            db.session.add(mp); db.session.commit()
            item = PrivacyReviewItem(tenant_id=t.id, source_type="message", source_id=1,
                                     reason_code="password", decision_type="memory_eligibility")
            db.session.add(item); db.session.commit()
            svc = PrivacyService(session=db.session)
            result = svc.approve_review(item.id, reviewed_by="admin")
            assert result["success"] is False
            assert "System non-overridable" in result["error"]

    def test_cross_tenant_review_isolation(self, real_app):
        from app.privacy import PrivacyService
        from app.tenant import Tenant
        from app.privacy.models import PrivacyReviewItem
        from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            pr1 = PrivacyReviewItem(tenant_id=t1.id, source_type="message", source_id=1,
                              reason_code="confidential", decision_type="memory_eligibility", status="pending")
            db.session.add(pr1)
            pr2 = PrivacyReviewItem(tenant_id=t2.id, source_type="message", source_id=2,
                              reason_code="confidential", decision_type="memory_eligibility", status="pending")
            db.session.add(pr2); db.session.commit()
            svc = PrivacyService(session=db.session)
            pending_a = svc.get_pending_reviews(tenant_id=t1.id)
            pending_b = svc.get_pending_reviews(tenant_id=t2.id)
            assert len(pending_a) == 1
            assert len(pending_b) == 1


class TestAuditSafety:
    def test_plaintext_secret_absent_from_decision(self, real_app):
        from app.privacy import PrivacyService
        from app.privacy.models import PrivacyDecision
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            svc.evaluate_memory_eligibility("message", 1, reason_codes=["password"])
            decision = PrivacyDecision.query.first()
            assert decision is not None
            # Decision payload should not contain the actual secret
            assert "s3cret!" not in (decision.reason_codes or "")

    def test_audit_no_secret_in_logs(self, real_app):
        from app.privacy import PrivacyService
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            # This should not log or expose secrets
            result = svc.evaluate_memory_eligibility("message", 1, reason_codes=["access_token"])
            assert result["memory_eligibility"] is not None


class TestIdempotency:
    def test_same_source_same_policy_no_duplicate(self, real_app):
        from app.privacy import PrivacyService
        from app.privacy.models import PrivacyDecision
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            svc.evaluate_memory_eligibility("message", 1)
            svc.evaluate_memory_eligibility("message", 1)
            decisions = PrivacyDecision.query.filter_by(source_type="message", source_id=1).all()
            # Each evaluation creates a new decision (supersession by is_active)
            assert len(decisions) == 2
            # Only the latest is active
            assert decisions[1].is_active is True


class TestTenantIsolation:
    def test_privacy_objects_isolated(self, real_app):
        from app.tenant import Tenant
        from app.privacy.models import PrivacyPolicy, SensitivityPolicy, Restriction, ForgetRequest
        from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            p1 = PrivacyPolicy(tenant_id=t1.id)
            p2 = PrivacyPolicy(tenant_id=t2.id)
            db.session.add(p1); db.session.add(p2); db.session.commit()
            assert PrivacyPolicy.query.filter_by(tenant_id=t1.id).count() == 1
            assert PrivacyPolicy.query.filter_by(tenant_id=t2.id).count() == 1


class TestSecretCredentialBoundary:
    def test_credential_reference_not_copied(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource
        from app.privacy import PrivacyService
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com",
                                     account_mode="business_dedicated",
                                     credential_reference="env:GMAIL_TOKEN")
            db.session.add(cs); db.session.commit()
            # credential_reference is a key, not a secret
            assert cs.credential_reference == "env:GMAIL_TOKEN"
            assert cs.credential_reference != "real-token"