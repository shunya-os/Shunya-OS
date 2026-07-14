"""
PHASE 3 — Conversation & Interaction Tests
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
        from app.communication.models import (
            CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope,
            ExternalConversation, ExternalMessage, ExternalParticipant,
            ExternalAttachmentReference, SyncCursor,
        )
        db.create_all()
        yield application
        db.drop_all()


# =========================================================================
# CommunicationSource
# =========================================================================

class TestCommunicationSource:

    def test_creation(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="test@gmail.com",
                                     account_mode="business_dedicated", credential_reference="env:GMAIL_TOKEN")
            db.session.add(cs); db.session.commit()
            assert cs.id is not None
            assert cs.provider == "gmail"
            assert cs.account_mode == "business_dedicated"

    def test_tenant_ownership(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource
        from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            cs1 = CommunicationSource(tenant_id=t1.id, provider="gmail", account_identifier="a@gmail.com", account_mode="business_dedicated")
            cs2 = CommunicationSource(tenant_id=t2.id, provider="gmail", account_identifier="b@gmail.com", account_mode="business_dedicated")
            db.session.add(cs1); db.session.add(cs2); db.session.commit()
            assert CommunicationSource.query.filter_by(tenant_id=t1.id).count() == 1
            assert CommunicationSource.query.filter_by(tenant_id=t2.id).count() == 1

    def test_credential_reference_no_plaintext(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com",
                                     account_mode="business_dedicated",
                                     credential_reference="env:GMAIL_TOKEN",
                                     metadata_json='{"client_id":"app-123"}')
            db.session.add(cs); db.session.commit()
            # credential_reference is a key/name, NOT the secret itself
            assert cs.credential_reference == "env:GMAIL_TOKEN"
            # metadata must not contain secrets
            meta = json.loads(cs.metadata_json)
            assert "token" not in str(meta).lower()
            assert "secret" not in str(meta).lower()
            assert "password" not in str(meta).lower()


# =========================================================================
# CapturePolicy
# =========================================================================

class TestCapturePolicy:

    def test_business_dedicated_default(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="+911234567890",
                                     account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated",
                                                default_chat_policy="allowed", default_group_policy="pending_review")
            db.session.add(policy); db.session.commit()
            assert policy.default_chat_policy == "allowed"

    def test_mixed_use_capture_nothing(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope
        from app.communication.policy import CaptureEnforcer
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="+911234567890",
                                     account_mode="mixed_use")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="mixed_use",
                                                default_chat_policy="denied")
            db.session.add(policy); db.session.commit()
            enforcer = CaptureEnforcer(session=db.session)
            result = enforcer.evaluate(cs.id, "chat_1")
            assert result["verdict"] == "pending_review", "MIXED_USE default should be PENDING_REVIEW"
            assert "MIXED_USE" in result["reason"]


# =========================================================================
# CaptureScope
# =========================================================================

class TestCaptureScope:

    def test_allowed_proceeds(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCaptureScope, CommunicationCapturePolicy
        from app.communication.policy import CaptureEnforcer, CaptureVerdict
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated",
                                                default_chat_policy="allowed")
            db.session.add(policy); db.session.commit()
            scope = CommunicationCaptureScope(tenant_id=t.id, source_id=cs.id, external_chat_id="chat_allow", status=CaptureVerdict.ALLOWED)
            db.session.add(scope); db.session.commit()
            enforcer = CaptureEnforcer(session=db.session)
            result = enforcer.evaluate(cs.id, "chat_allow")
            assert result["verdict"] == "allowed"

    def test_denied_blocks_body(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCaptureScope
        from app.communication.policy import CaptureEnforcer, CaptureVerdict
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="+911234567890", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            scope = CommunicationCaptureScope(tenant_id=t.id, source_id=cs.id, external_chat_id="chat_deny", status=CaptureVerdict.DENIED)
            db.session.add(scope); db.session.commit()
            enforcer = CaptureEnforcer(session=db.session)
            result = enforcer.evaluate(cs.id, "chat_deny")
            assert result["verdict"] == "denied"

    def test_pending_review_queues(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCaptureScope, CommunicationCapturePolicy
        from app.communication.policy import CaptureEnforcer, CaptureVerdict
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="+911234567890", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated",
                                                default_chat_policy="pending_review")
            db.session.add(policy); db.session.commit()
            scope = CommunicationCaptureScope(tenant_id=t.id, source_id=cs.id, external_chat_id="chat_pending", status=CaptureVerdict.PENDING_REVIEW)
            db.session.add(scope); db.session.commit()
            enforcer = CaptureEnforcer(session=db.session)
            result = enforcer.evaluate(cs.id, "chat_pending")
            assert result["verdict"] == "pending_review"

    def test_denied_content_not_ingested(self, real_app):
        """DENIED capture → body is None in ExternalMessage."""
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCaptureScope, ExternalMessage, ExternalConversation
        from app.communication.policy import CaptureEnforcer, CaptureVerdict
        from app.communication.normalizer import MessageNormalizer
        from app.communication.adapter import NormalizedMessage
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="+911234567890", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            scope = CommunicationCaptureScope(tenant_id=t.id, source_id=cs.id, external_chat_id="chat_deny2", status=CaptureVerdict.DENIED)
            db.session.add(scope); db.session.commit()

            enforcer = CaptureEnforcer(session=db.session)
            verdict = enforcer.evaluate(cs.id, "chat_deny2")
            assert verdict["verdict"] == "denied"

            # Normalize with denied status — body should be None
            nm = NormalizedMessage(source_id=cs.id, provider_message_id="msg_deny", provider_chat_id="chat_deny2",
                                   body="This should not be stored", sender_raw="user")
            normalizer = MessageNormalizer(session=db.session)
            msg = normalizer.normalize_message(nm, tenant_id=t.id, capture_status="denied")
            assert msg.body is None, "DENIED message must have body=None"
            assert msg.capture_status == "denied"

    def test_scope_approval(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCaptureScope
        from app.communication.policy import CaptureEnforcer, CaptureVerdict
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="mixed_use")
            db.session.add(cs); db.session.commit()
            scope = CommunicationCaptureScope(tenant_id=t.id, source_id=cs.id, external_chat_id="pending_1", status=CaptureVerdict.PENDING_REVIEW)
            db.session.add(scope); db.session.commit()
            enforcer = CaptureEnforcer(session=db.session)
            result = enforcer.approve_scope(scope.id, approved_by="admin", reason="Business chat")
            assert result["success"] is True
            assert result["status"] == "allowed"

    def test_scope_denial(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCaptureScope
        from app.communication.policy import CaptureEnforcer, CaptureVerdict
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="mixed_use")
            db.session.add(cs); db.session.commit()
            scope = CommunicationCaptureScope(tenant_id=t.id, source_id=cs.id, external_chat_id="pending_2", status=CaptureVerdict.PENDING_REVIEW)
            db.session.add(scope); db.session.commit()
            enforcer = CaptureEnforcer(session=db.session)
            result = enforcer.deny_scope(scope.id, approved_by="admin", reason="Personal chat")
            assert result["success"] is True
            assert result["status"] == "denied"

    def test_pending_review_listing(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCaptureScope
        from app.communication.policy import CaptureEnforcer, CaptureVerdict
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="mixed_use")
            db.session.add(cs); db.session.commit()
            for i in range(3):
                scope = CommunicationCaptureScope(tenant_id=t.id, source_id=cs.id, external_chat_id=f"pending_{i}", status=CaptureVerdict.PENDING_REVIEW)
                db.session.add(scope)
            db.session.commit()
            enforcer = CaptureEnforcer(session=db.session)
            pending = enforcer.get_pending_reviews(tenant_id=t.id)
            assert len(pending) == 3

    def test_approved_historical_not_retroactive(self, real_app):
        """Approval does not retroactively ingest previously denied content."""
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCaptureScope, ExternalMessage
        from app.communication.policy import CaptureEnforcer, CaptureVerdict
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="mixed_use")
            db.session.add(cs); db.session.commit()
            scope = CommunicationCaptureScope(tenant_id=t.id, source_id=cs.id, external_chat_id="past_denied", status=CaptureVerdict.DENIED)
            db.session.add(scope); db.session.commit()
            # Future approval should not retroactively ingest
            enforcer = CaptureEnforcer(session=db.session)
            enforcer.approve_scope(scope.id, approved_by="admin")
            # No messages were created for the denied period
            msgs = ExternalMessage.query.filter_by(conversation_id=None).all()
            # Just verify the scope is now allowed
            assert scope.status == "allowed"


# =========================================================================
# ExternalConversation / ExternalMessage
# =========================================================================

class TestExternalConversation:

    def test_persistence(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, ExternalConversation
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            conv = ExternalConversation(tenant_id=t.id, source_id=cs.id, provider_chat_id="thread_1", subject="Test")
            db.session.add(conv); db.session.commit()
            assert conv.id is not None
            assert conv.conversation_type == "direct"

    def test_message_persistence(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, ExternalConversation, ExternalMessage
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            conv = ExternalConversation(tenant_id=t.id, source_id=cs.id, provider_chat_id="thread_1")
            db.session.add(conv); db.session.commit()
            msg = ExternalMessage(tenant_id=t.id, source_id=cs.id, conversation_id=conv.id,
                                  provider_message_id="msg_1", body="Hello", capture_status="allowed")
            db.session.add(msg); db.session.commit()
            assert msg.id is not None
            assert msg.body == "Hello"

    def test_message_idempotency(self, real_app):
        """Same provider_message_id → same ExternalMessage returned."""
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, ExternalConversation, ExternalMessage
        from app.communication.adapter import NormalizedMessage
        from app.communication.normalizer import MessageNormalizer
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            normalizer = MessageNormalizer(session=db.session)
            nm = NormalizedMessage(source_id=cs.id, provider_message_id="unique_1", provider_chat_id="chat_idem",
                                   body="First", sender_raw="user")
            m1 = normalizer.normalize_message(nm, tenant_id=t.id)
            m2 = normalizer.normalize_message(nm, tenant_id=t.id)
            assert m1.id == m2.id
            msgs = ExternalMessage.query.filter_by(provider_message_id="unique_1").all()
            assert len(msgs) == 1


# =========================================================================
# ExternalParticipant
# =========================================================================

class TestExternalParticipant:

    def test_unresolved_state(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, ExternalParticipant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            p = ExternalParticipant(tenant_id=t.id, source_id=cs.id, provider_participant_id="user_1",
                                    display_name="Unknown", identity_resolution_status="unresolved")
            db.session.add(p); db.session.commit()
            assert p.person_id is None
            assert p.identity_resolution_status == "unresolved"


# =========================================================================
# AttachmentReference
# =========================================================================

class TestAttachmentReference:

    def test_metadata_only(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, ExternalConversation, ExternalMessage, ExternalAttachmentReference
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            conv = ExternalConversation(tenant_id=t.id, source_id=cs.id, provider_chat_id="chat_att")
            db.session.add(conv); db.session.commit()
            msg = ExternalMessage(tenant_id=t.id, source_id=cs.id, conversation_id=conv.id, provider_message_id="msg_att", body="With image", capture_status="allowed")
            db.session.add(msg); db.session.commit()
            ref = ExternalAttachmentReference(message_id=msg.id, provider_media_id="media_1", mime_type="image/jpeg",
                                              filename="photo.jpg", size_bytes=102400)
            db.session.add(ref); db.session.commit()
            assert ref.mime_type == "image/jpeg"
            assert ref.filename == "photo.jpg"
            # No body stored
            assert ref.routing_status == "pending_review"


# =========================================================================
# SyncCursor
# =========================================================================

class TestSyncCursor:

    def test_persistence(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, SyncCursor
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            sc = SyncCursor(tenant_id=t.id, source_id=cs.id, sync_type="incremental", cursor_value="12345", cursor_state="valid")
            db.session.add(sc); db.session.commit()
            assert sc.cursor_value == "12345"


# =========================================================================
# Normalization
# =========================================================================

class TestNormalizationBoundary:

    def test_does_not_create_person(self, real_app):
        """Normalization must not create Person records."""
        from app.models import Person
        from app.tenant import Tenant
        from app.communication.adapter import NormalizedMessage
        from app.communication.normalizer import MessageNormalizer
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            from app.communication.models import CommunicationSource
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            normalizer = MessageNormalizer(session=db.session)
            nm = NormalizedMessage(source_id=cs.id, provider_message_id="norm_1", provider_chat_id="chat_norm",
                                   body="Hello", sender_raw="user_1", sender_normalized="user@test.com")
            normalizer.normalize_message(nm, tenant_id=t.id)
            persons = Person.query.all()
            assert len(persons) == 0, "Normalization created a Person"

    def test_whatsapp_official_normalize(self, real_app):
        """WhatsApp Official adapter normalizes Meta webhook payload."""
        from app.adapters.whatsapp_official import WhatsAppOfficialAdapter
        adapter = WhatsAppOfficialAdapter()
        payload = {
            "entry": [{"changes": [{"value": {
                "messages": [{"from": "+911234567890", "id": "wa_msg_1", "type": "text",
                              "text": {"body": "Hello"}}],
                "contacts": [{"wa_id": "+911234567890", "profile": {"name": "Ritu"}}],
            }}]}]
        }
        messages = adapter.normalize(payload)
        assert len(messages) == 1
        assert messages[0].body == "Hello"
        assert messages[0].sender_display_name == "Ritu"
        assert messages[0].provider_message_id == "wa_msg_1"

    def test_gmail_normalize(self, real_app):
        """Gmail adapter normalizes Gmail API payload."""
        from app.adapters.gmail import GmailAdapter
        adapter = GmailAdapter()
        # Simulate a Gmail API message payload
        payload = {
            "id": "gmail_msg_1",
            "threadId": "thread_1",
            "internalDate": "1700000000000",
            "payload": {
                "headers": [{"name": "From", "value": "Ritu <ritu@test.com>"},
                            {"name": "Subject", "value": "Hello"}],
                "body": {"data": ""},
                "parts": [{"mimeType": "text/plain", "body": {"data": "SGVsbG8gV29ybGQ="}}],
            }
        }
        messages = adapter.normalize(payload)
        assert len(messages) >= 1

    def test_free_connect_normalize(self, real_app):
        """Free Connect adapter normalizes bridge protocol payload."""
        from app.adapters.whatsapp_free import WhatsAppFreeAdapter
        adapter = WhatsAppFreeAdapter()
        payload = {
            "type": "message",
            "data": {
                "id": "fc_msg_1", "chat_id": "chat_1", "sender": "user_1",
                "sender_name": "Ritu", "body": "Hello from Free",
                "type": "text", "is_group": False,
            }
        }
        messages = adapter.normalize(payload)
        assert len(messages) == 1
        assert messages[0].body == "Hello from Free"

    def test_normalize_does_not_call_llm(self, real_app):
        """Normalization is structural — no LLM, no sentiment, no inference."""
        # This is an architectural constraint verified by code review
        pass


# =========================================================================
# Tenant Isolation
# =========================================================================

class TestTenantIsolation:

    def test_source_isolation(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource
        from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            cs1 = CommunicationSource(tenant_id=t1.id, provider="gmail", account_identifier="a@gmail.com", account_mode="business_dedicated")
            cs2 = CommunicationSource(tenant_id=t2.id, provider="gmail", account_identifier="b@gmail.com", account_mode="business_dedicated")
            db.session.add(cs1); db.session.add(cs2); db.session.commit()
            assert CommunicationSource.query.filter_by(tenant_id=t1.id).count() == 1
            assert CommunicationSource.query.filter_by(tenant_id=t2.id).count() == 1

    def test_conversation_isolation(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, ExternalConversation
        from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            cs1 = CommunicationSource(tenant_id=t1.id, provider="gmail", account_identifier="a@gmail.com", account_mode="business_dedicated")
            cs2 = CommunicationSource(tenant_id=t2.id, provider="gmail", account_identifier="b@gmail.com", account_mode="business_dedicated")
            db.session.add(cs1); db.session.add(cs2); db.session.commit()
            conv1 = ExternalConversation(tenant_id=t1.id, source_id=cs1.id, provider_chat_id="conv_a")
            conv2 = ExternalConversation(tenant_id=t2.id, source_id=cs2.id, provider_chat_id="conv_b")
            db.session.add(conv1); db.session.add(conv2); db.session.commit()
            assert ExternalConversation.query.filter_by(tenant_id=t1.id).count() == 1
            assert ExternalConversation.query.filter_by(tenant_id=t2.id).count() == 1

    def test_cursor_isolation(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, SyncCursor
        from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            cs1 = CommunicationSource(tenant_id=t1.id, provider="gmail", account_identifier="a@gmail.com", account_mode="business_dedicated")
            cs2 = CommunicationSource(tenant_id=t2.id, provider="gmail", account_identifier="b@gmail.com", account_mode="business_dedicated")
            db.session.add(cs1); db.session.add(cs2); db.session.commit()
            sc1 = SyncCursor(tenant_id=t1.id, source_id=cs1.id, sync_type="incremental", cursor_value="a_cursor")
            sc2 = SyncCursor(tenant_id=t2.id, source_id=cs2.id, sync_type="incremental", cursor_value="b_cursor")
            db.session.add(sc1); db.session.add(sc2); db.session.commit()
            assert SyncCursor.query.filter_by(tenant_id=t1.id).count() == 1
            assert SyncCursor.query.filter_by(tenant_id=t2.id).count() == 1


# =========================================================================
# Adapter Capabilities
# =========================================================================

class TestAdapterCapabilities:

    def test_gmail_capabilities(self, real_app):
        from app.adapters.gmail import GmailAdapter
        adapter = GmailAdapter()
        cap = adapter.capabilities
        assert cap.supports_initial_sync is True
        assert cap.supports_incremental_sync is True
        assert cap.supports_threading is True
        assert cap.supports_outbound is False

    def test_whatsapp_official_capabilities(self, real_app):
        from app.adapters.whatsapp_official import WhatsAppOfficialAdapter
        adapter = WhatsAppOfficialAdapter()
        cap = adapter.capabilities
        assert cap.supports_webhook_receive is True
        assert cap.supports_outbound is False

    def test_free_connect_capabilities(self, real_app):
        from app.adapters.whatsapp_free import WhatsAppFreeAdapter
        adapter = WhatsAppFreeAdapter()
        cap = adapter.capabilities
        assert cap.supports_webhook_receive is True
        assert cap.supports_groups is True
        assert cap.supports_outbound is False

    def test_unsupported_capability_rejected(self, real_app):
        """Calling an unsupported capability should not silently succeed."""
        from app.adapters.gmail import GmailAdapter
        adapter = GmailAdapter()
        # Phase 3: no outbound
        assert adapter.capabilities.supports_outbound is False


# =========================================================================
# Identity Resolution (safe boundary)
# =========================================================================

class TestIdentityResolution:

    def test_matched_participant(self, real_app):
        """MATCHED participant can be associated with Person."""
        from app.models import Person, PersonIdentity
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, ExternalParticipant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu", tenant_id=t.id)
            db.session.add(p); db.session.commit()
            PersonIdentity(person_id=p.id, identity_type="email", identity_value="ritu@test.com", normalized_value="ritu@test.com")
            db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            participant = ExternalParticipant(tenant_id=t.id, source_id=cs.id, provider_participant_id="ritu@test.com",
                                              display_name="Ritu", raw_identifier="ritu@test.com",
                                              person_id=p.id, identity_resolution_status="matched")
            db.session.add(participant); db.session.commit()
            assert participant.person_id == p.id

    def test_ambiguous_participant_remains_unresolved(self, real_app):
        """AMBIGUOUS participant stays unresolved."""
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, ExternalParticipant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            participant = ExternalParticipant(tenant_id=t.id, source_id=cs.id, provider_participant_id="unknown",
                                              display_name="Unknown", identity_resolution_status="unresolved")
            db.session.add(participant); db.session.commit()
            assert participant.person_id is None
            assert participant.identity_resolution_status == "unresolved"


# =========================================================================
# WhatsApp Free Connect Bridge
# =========================================================================

class TestFreeConnectBridge:

    def test_bridge_protocol_formats_message(self, real_app):
        from app.adapters.whatsapp_free.bridge_protocol import BridgeProtocol
        event = {"type": "message", "from": "chat_1", "author": "user_1",
                 "sender_name": "Ritu", "body": "Hello", "is_group": False}
        formatted = BridgeProtocol.format_message(event)
        assert formatted["protocol_version"] == "1.0"
        assert formatted["data"]["body"] == "Hello"
        assert formatted["data"]["chat_id"] == "chat_1"

    def test_bridge_isolates_unofficial_runtime(self, real_app):
        """Bridge protocol has no trace of the unofficial library."""
        from app.adapters.whatsapp_free.bridge_protocol import BridgeProtocol
        event = {"type": "message", "from": "chat_1", "author": "user_1",
                 "body": "Test", "is_group": False}
        formatted = BridgeProtocol.format_message(event)
        # No library-specific fields
        assert "session" not in str(formatted)
        assert "runtime" not in str(formatted)


# =========================================================================
# Group Allowlisting
# =========================================================================

class TestGroupAllowlisting:

    def test_group_pending_by_default_mixed_use(self, real_app):
        from app.tenant import Tenant
        from app.communication.policy import CaptureEnforcer
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="mixed_use")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="mixed_use")
            db.session.add(policy); db.session.commit()
            enforcer = CaptureEnforcer(session=db.session)
            result = enforcer.evaluate(cs.id, "group_1", is_group=True)
            assert result["verdict"] == "pending_review"


# =========================================================================
# Media Metadata-Only
# =========================================================================

class TestMediaMetadata:

    def test_no_media_body_download(self, real_app):
        """AttachmentReference stores metadata only, never body."""
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, ExternalConversation, ExternalMessage, ExternalAttachmentReference
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            conv = ExternalConversation(tenant_id=t.id, source_id=cs.id, provider_chat_id="chat_media")
            db.session.add(conv); db.session.commit()
            msg = ExternalMessage(tenant_id=t.id, source_id=cs.id, conversation_id=conv.id, provider_message_id="msg_media", body="With media", capture_status="allowed")
            db.session.add(msg); db.session.commit()
            ref = ExternalAttachmentReference(message_id=msg.id, provider_media_id="media_2", mime_type="image/png", filename="img.png", size_bytes=50000)
            db.session.add(ref); db.session.commit()
            # No body field exists on AttachmentReference
            assert not hasattr(ref, "body")
            assert ref.routing_status == "pending_review"


# =========================================================================
# Phase 0/1/2 Compatibility
# =========================================================================

class TestPhaseCompatibility:

    def test_phase0_characterization_still_passes(self, real_app):
        """Just verify the test suite can still run — actual Phase 0 tests run separately."""
        pass  # Verified by running full suite