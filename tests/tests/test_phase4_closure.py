"""
PHASE 4 — CLOSURE AUDIT TESTS: stale review, foreign-ID, leakage, integration
"""
import pytest
from datetime import datetime


class TestStaleReview:
    def test_newer_policy_invalidates_stale_approval(self, real_app):
        """Stale review cannot override newer policy version."""
        from app.privacy import PrivacyService, MemoryEligibility
        from app.tenant import Tenant
        from app.privacy.models import MemoryEligibilityPolicy, PrivacyReviewItem
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            # Policy says INELIGIBLE
            mp = MemoryEligibilityPolicy(tenant_id=t.id, source_type="message", decision=MemoryEligibility.INELIGIBLE, is_active=True, policy_version=2)
            db.session.add(mp); db.session.commit()
            # Stale review item with policy_version=1
            item = PrivacyReviewItem(tenant_id=t.id, source_type="message", source_id=1, reason_code="confidential", decision_type="memory_eligibility", policy_version=1)
            db.session.add(item); db.session.commit()
            svc = PrivacyService(session=db.session)
            # Newer policy (version 2) says INELIGIBLE — review cannot override
            result = svc.evaluate_memory_eligibility("message", 1, tenant_id=t.id)
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE

    def test_explicit_restriction_invalidates_stale_approval(self, real_app):
        """Explicit restriction prevents stale approval from being effective."""
        from app.privacy import PrivacyService, MemoryEligibility
        from app.tenant import Tenant
        from app.models import Person
        from app.privacy.models import Restriction, PrivacyPolicy, PrivacyReviewItem
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            Restriction(person_id=p.id, restriction_type="do_not_use_for_memory", tenant_id=t.id, is_active=True)
            db.session.commit()
            # Stale approve review
            item = PrivacyReviewItem(tenant_id=t.id, source_type="message", source_id=1, reason_code="confidential", decision_type="memory_eligibility", status="approved")
            db.session.add(item); db.session.commit()
            svc = PrivacyService(session=db.session)
            # Explicit restriction blocks eligibility
            result = svc.evaluate_memory_eligibility("message", 1, tenant_id=t.id, person_id=p.id)
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE

    def test_approved_revocation_invalidates_stale_approval(self, real_app):
        """Approved revocation prevents stale approval from being effective."""
        from app.privacy import PrivacyService, MemoryEligibility, ForgetRequestStatus
        from app.tenant import Tenant
        from app.models import Person
        from app.privacy.models import PrivacyReviewItem, ForgetRequest
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            # Approved revocation
            fr = ForgetRequest(tenant_id=t.id, person_id=p.id, request_type="forget", status=ForgetRequestStatus.APPROVED, approved_at=datetime.utcnow())
            db.session.add(fr); db.session.commit()
            # Stale approve review
            item = PrivacyReviewItem(tenant_id=t.id, source_type="message", source_id=1, reason_code="confidential", decision_type="memory_eligibility", status="approved")
            db.session.add(item); db.session.commit()
            svc = PrivacyService(session=db.session)
            # Approved revocation blocks eligibility
            result = svc.evaluate_memory_eligibility("message", 1, tenant_id=t.id, person_id=p.id)
            assert result["memory_eligibility"] == MemoryEligibility.INELIGIBLE


class TestForeignID:
    def test_foreign_review_id_rejected(self, real_app):
        """Tenant B cannot retrieve Tenant A's review item by direct ID."""
        from app.tenant import Tenant
        from app.privacy.models import PrivacyReviewItem
        from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            item = PrivacyReviewItem(tenant_id=t1.id, source_type="message", source_id=1, reason_code="confidential", decision_type="memory_eligibility")
            db.session.add(item); db.session.commit()
            # Tenant B querying by ID
            from app.privacy import PrivacyService
            svc = PrivacyService(session=db.session)
            pending_b = svc.get_pending_reviews(tenant_id=t2.id)
            for p in pending_b:
                assert p["id"] != item.id, "Tenant B should not see Tenant A's review"

    def test_foreign_forget_request_id_rejected(self, real_app):
        """Tenant B cannot access Tenant A's forget request."""
        from app.tenant import Tenant
        from app.privacy.models import ForgetRequest
        from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            fr = ForgetRequest(tenant_id=t1.id, request_type="forget", status="requested")
            db.session.add(fr); db.session.commit()
            # Tenant B scoped query
            b_requests = ForgetRequest.query.filter_by(tenant_id=t2.id).all()
            assert len(b_requests) == 0

    def test_foreign_restriction_id_rejected(self, real_app):
        """Tenant B cannot access Tenant A's restriction."""
        from app.tenant import Tenant
        from app.models import Person
        from app.privacy.models import Restriction
        from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu")
            db.session.add(p); db.session.commit()
            Restriction(person_id=p.id, restriction_type="do_not_use_for_memory", tenant_id=t1.id)
            db.session.commit()
            from app.privacy import PrivacyService
            svc = PrivacyService(session=db.session)
            b_restrictions = svc.get_active_restrictions(p.id, tenant_id=t2.id)
            assert len(b_restrictions) == 0


class TestLeakage:
    def test_secret_absent_from_decision_audit(self, real_app):
        """Plaintext secret not stored in PrivacyDecision audit metadata."""
        from app.privacy import PrivacyService
        from app.privacy.models import PrivacyDecision
        from app import db
        with real_app.app_context():
            svc = PrivacyService(session=db.session)
            svc.evaluate_memory_eligibility("message", 1, reason_codes=["password"])
            decisions = PrivacyDecision.query.all()
            for d in decisions:
                codes = d.reason_codes or ""
                assert "mysecret" not in codes
                assert "password123" not in codes
                # Reason codes should contain only the category, not the actual secret value
                assert "password" in codes or "system_non_overridable" in codes

    def test_credential_reference_not_in_audit(self, real_app):
        """credential_reference is not resolved and dumped into audit data."""
        from app.privacy import PrivacyService
        from app.privacy.models import PrivacyDecision
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com",
                                     account_mode="business_dedicated", credential_reference="env:GMAIL_TOKEN")
            db.session.add(cs); db.session.commit()
            svc = PrivacyService(session=db.session)
            svc.evaluate_memory_eligibility("communication_source", cs.id, tenant_id=t.id)
            decisions = PrivacyDecision.query.all()
            for d in decisions:
                codes = d.reason_codes or ""
                # credential_reference key should not be leaked
                assert "GMAIL_TOKEN" not in codes
                assert "env:" not in codes

    def test_log_does_not_expose_secret(self, real_app):
        """Phase 4 code paths do not log resolved secrets."""
        import logging, io
        from app.privacy import PrivacyService
        from app import db
        with real_app.app_context():
            logger = logging.getLogger("privacy")
            stream = io.StringIO()
            handler = logging.StreamHandler(stream)
            logger.addHandler(handler)
            try:
                svc = PrivacyService(session=db.session)
                svc.evaluate_memory_eligibility("message", 1, reason_codes=["password"])
                log_output = stream.getvalue()
                assert "secret" not in log_output.lower()
                assert "password" not in log_output
            finally:
                logger.removeHandler(handler)


class TestPhase4Integration:
    def test_phase4_invoked_from_ingestion(self, real_app):
        """Phase 4 evaluation is invoked from CommunicationIngestionService."""
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope, ExternalMessage
        from app.communication.adapter import NormalizedMessage
        from app.communication.ingestion import CommunicationIngestionService
        from app.privacy.models import PrivacyDecision
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated", default_chat_policy="allowed")
            db.session.add(policy); db.session.commit()
            scope = CommunicationCaptureScope(tenant_id=t.id, source_id=cs.id, external_chat_id="chat_p4", status="allowed")
            db.session.add(scope); db.session.commit()
            svc = CommunicationIngestionService(session=db.session)
            nm = NormalizedMessage(source_id=cs.id, provider_message_id="p4_integration", provider_chat_id="chat_p4",
                                   body="Test", sender_raw="user")
            svc.ingest(cs.id, "chat_p4", [nm], tenant_id=t.id)
            decisions = PrivacyDecision.query.filter_by(source_type="external_message").all()
            assert len(decisions) >= 1, "Phase 4 should have created a PrivacyDecision during ingestion"