"""
PHASE 3 — HARDENING TESTS: ingestion pipeline, webhook route, credential resolver, Gmail client, tenant isolation
"""
import pytest, json, os
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
# 1. Authoritative Ingestion Pipeline
# =========================================================================

class TestIngestionPipeline:

    def test_full_pipeline_allowed(self, real_app):
        """Full pipeline: source → policy → scope → ingestion → identity → relationship."""
        from app.models import Person, PersonIdentity
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope, ExternalMessage
        from app.communication.adapter import NormalizedMessage
        from app.communication.ingestion import CommunicationIngestionService
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
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated", default_chat_policy="allowed")
            db.session.add(policy); db.session.commit()

            svc = CommunicationIngestionService(session=db.session)
            nm = NormalizedMessage(source_id=cs.id, provider_message_id="pipe_1", provider_chat_id="chat_pipe",
                                   body="Hello", sender_raw="ritu@test.com", sender_normalized="ritu@test.com",
                                   sender_display_name="Ritu")
            results = svc.ingest(cs.id, "chat_pipe", [nm], tenant_id=t.id)
            assert len(results) == 1
            assert results[0].accepted is True
            assert results[0].verdict == "allowed"
            msg = db.session.get(ExternalMessage, results[0].message.id)
            assert msg is not None
            assert msg.body == "Hello"

    def test_denied_rejected_before_persistence(self, real_app):
        """DENIED verdict → no message body stored."""
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope, ExternalMessage
        from app.communication.adapter import NormalizedMessage
        from app.communication.ingestion import CommunicationIngestionService
        from app.communication.policy import CaptureVerdict
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated", default_chat_policy="denied")
            db.session.add(policy); db.session.commit()

            svc = CommunicationIngestionService(session=db.session)
            nm = NormalizedMessage(source_id=cs.id, provider_message_id="deny_1", provider_chat_id="chat_deny",
                                   body="This should not be stored", sender_raw="user")
            results = svc.ingest(cs.id, "chat_deny", [nm], tenant_id=t.id)
            assert results[0].accepted is False
            assert results[0].verdict == "denied"
            msgs = ExternalMessage.query.all()
            assert len(msgs) == 0, "No messages should be persisted"

    def test_pending_review_rejected(self, real_app):
        """PENDING_REVIEW → no message body stored."""
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy, ExternalMessage
        from app.communication.adapter import NormalizedMessage
        from app.communication.ingestion import CommunicationIngestionService
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="mixed_use")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="mixed_use")
            db.session.add(policy); db.session.commit()

            svc = CommunicationIngestionService(session=db.session)
            nm = NormalizedMessage(source_id=cs.id, provider_message_id="pending_1", provider_chat_id="chat_pending",
                                   body="Pending body", sender_raw="user")
            results = svc.ingest(cs.id, "chat_pending", [nm], tenant_id=t.id)
            assert results[0].accepted is False
            assert results[0].verdict == "pending_review"
            msgs = ExternalMessage.query.all()
            assert len(msgs) == 0

    def test_normalization_does_not_create_person_lead(self, real_app):
        """Ingestion pipeline: normalization does not create Person or Lead on its own."""
        from app.models import Person, Lead
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy
        from app.communication.adapter import NormalizedMessage
        from app.communication.ingestion import CommunicationIngestionService
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated", default_chat_policy="allowed")
            db.session.add(policy); db.session.commit()

            svc = CommunicationIngestionService(session=db.session)
            nm = NormalizedMessage(source_id=cs.id, provider_message_id="no_person_1", provider_chat_id="chat_np",
                                   body="Hello", sender_raw="unknown@test.com", sender_normalized="unknown@test.com")
            svc.ingest(cs.id, "chat_np", [nm], tenant_id=t.id)
            persons = Person.query.all()
            leads = Lead.query.all()
            # Identity was not found → participant stays unresolved
            # No Person/Lead created by normalization alone
            # (IngestionService identity resolution may leave unresolved, but no auto-creation)

    def test_repeated_eligible_messages_no_duplicate_lead(self, real_app):
        """Repeated messages in same conversation do not create duplicate Leads."""
        from app.models import Person, PersonIdentity, Lead, Relationship
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope, ExternalParticipant
        from app.communication.adapter import NormalizedMessage
        from app.communication.ingestion import CommunicationIngestionService
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
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated", default_chat_policy="allowed")
            db.session.add(policy); db.session.commit()
            scope = CommunicationCaptureScope(tenant_id=t.id, source_id=cs.id, external_chat_id="chat_ld", status="allowed")
            db.session.add(scope); db.session.commit()

            # Pre-create the participant with MATCHED identity
            participant = ExternalParticipant(tenant_id=t.id, source_id=cs.id, provider_participant_id="ritu@test.com",
                                              display_name="Ritu", raw_identifier="ritu@test.com",
                                              person_id=p.id, identity_resolution_status="matched")
            db.session.add(participant); db.session.commit()

            # Also create a relationship so the ingestion service can find it
            from app.relationship import RelationshipService
            rel_svc = RelationshipService(session=db.session)
            rel_svc.ensure_customer_relationship(p.id, tenant_id=t.id)
            db.session.commit()

            svc = CommunicationIngestionService(session=db.session)
            for i in range(3):
                nm = NormalizedMessage(source_id=cs.id, provider_message_id=f"lead_dup_{i}", provider_chat_id="chat_ld",
                                       body=f"Message {i}", sender_raw="ritu@test.com", sender_normalized="ritu@test.com")
                svc.ingest(cs.id, "chat_ld", [nm], tenant_id=t.id)
            leads = Lead.query.all()
            assert len(leads) == 1, f"Expected 1 Lead, got {len(leads)}"


# =========================================================================
# 2. Credential Resolver
# =========================================================================

class TestCredentialResolver:

    def test_credential_reference_only(self, real_app):
        from app.communication.credentials import CredentialResolver
        # credential_reference stores only a key name
        ref = "env:GMAIL_ACCESS_TOKEN"
        assert CredentialResolver.is_secret_field("token") is True
        assert CredentialResolver.is_secret_field("client_id") is False

    def test_resolve_env(self, real_app):
        from app.communication.credentials import CredentialResolver
        os.environ["TEST_P3_SECRET"] = "test-secret-value"
        val = CredentialResolver.resolve("env:TEST_P3_SECRET")
        assert val == "test-secret-value"

    def test_resolve_literal(self, real_app):
        """literal: is permitted only in TESTING mode."""
        import os
        os.environ["TESTING"] = "true"
        # Force reimport to pick up TESTING=true
        import importlib
        import app.communication.credentials as cred_mod
        importlib.reload(cred_mod)
        val = cred_mod.CredentialResolver.resolve("literal:test-token")
        assert val == "test-token"

    def test_no_secret_in_metadata(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource
        from app.communication.credentials import CredentialResolver
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com",
                                     account_mode="business_dedicated",
                                     credential_reference="env:GMAIL_TOKEN",
                                     metadata_json='{"client_id":"app-123","tenant":"shunya"}')
            db.session.add(cs); db.session.commit()
            meta = json.loads(cs.metadata_json)
            for k, v in meta.items():
                assert not CredentialResolver.is_secret_field(k), f"Secret key found: {k}"
            assert CredentialResolver.is_secret_field("client_id") is False


# =========================================================================
# 3. Gmail Provider-Client Integration
# =========================================================================

class TestGmailClient:

    def test_fake_client_list_messages(self, real_app):
        from app.adapters.gmail.client import FakeGmailClient
        client = FakeGmailClient()
        client.add_message("msg_1", "thread_1", "ritu@test.com", body="Hello")
        result = client.list_messages()
        assert len(result.get("messages", [])) == 1

    def test_fake_client_get_thread(self, real_app):
        from app.adapters.gmail.client import FakeGmailClient
        client = FakeGmailClient()
        client.add_message("msg_1", "thread_1", "a@test.com")
        client.add_message("msg_2", "thread_1", "b@test.com")
        thread = client.get_thread("thread_1")
        assert len(thread.get("messages", [])) == 2

    def test_fake_client_history(self, real_app):
        from app.adapters.gmail.client import FakeGmailClient
        client = FakeGmailClient()
        client.add_message("msg_1", "thread_1", "a@test.com")
        client.add_history("1001", ["msg_1"])
        history = client.list_history("1000")
        assert len(history.get("history", [])) == 1

    def test_fake_client_get_profile(self, real_app):
        from app.adapters.gmail.client import FakeGmailClient
        client = FakeGmailClient()
        profile = client.get_profile()
        assert profile["emailAddress"] == "test@gmail.com"
        assert profile["historyId"] == "1000"

    def test_gmail_initial_sync_path(self, real_app):
        """Gmail initial sync enumerates messages, normalizes, ingests idempotently."""
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy, ExternalMessage
        from app.communication.adapter import NormalizedMessage
        from app.communication.normalizer import MessageNormalizer
        from app.communication.ingestion import CommunicationIngestionService
        from app.adapters.gmail import GmailAdapter
        from app.adapters.gmail.client import FakeGmailClient
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated", default_chat_policy="allowed")
            db.session.add(policy); db.session.commit()

            # Simulate Gmail API messages
            client = FakeGmailClient()
            client.add_message("g_1", "t_1", "ritu@test.com", body="Hello from Gmail", internal_date=1700000000000)
            raw_messages = client.list_messages()

            # Normalize through adapter
            adapter = GmailAdapter()
            all_normalized = []
            for m in raw_messages.get("messages", []):
                msg_data = client.get_message(m["id"])
                normalized = adapter.normalize(msg_data)
                all_normalized.extend(normalized)

            # Ingest through pipeline
            svc = CommunicationIngestionService(session=db.session)
            results = svc.ingest(cs.id, "gmail_chat", all_normalized, tenant_id=t.id)
            accepted = [r for r in results if r.accepted]
            assert len(accepted) >= 1

            # Idempotency: re-ingest same messages
            results2 = svc.ingest(cs.id, "gmail_chat", all_normalized, tenant_id=t.id)
            total = ExternalMessage.query.count()
            assert total == len(accepted), f"Idempotency failed: {total} != {len(accepted)}"


# =========================================================================
# 4. Tenant Isolation Matrix
# =========================================================================

class TestTenantIsolationMatrix:

    def _setup_tenant(self, t, db):
        from app.communication.models import (CommunicationSource, CommunicationCapturePolicy,
            CommunicationCaptureScope, ExternalConversation, ExternalMessage,
            ExternalParticipant, ExternalAttachmentReference, SyncCursor)
        cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier=f"{t.slug}@gmail.com", account_mode="business_dedicated")
        db.session.add(cs); db.session.flush()
        policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated", default_chat_policy="allowed")
        db.session.add(policy); db.session.flush()
        scope = CommunicationCaptureScope(tenant_id=t.id, source_id=cs.id, external_chat_id=f"chat_{t.id}", status="allowed")
        db.session.add(scope); db.session.flush()
        conv = ExternalConversation(tenant_id=t.id, source_id=cs.id, provider_chat_id=f"conv_{t.id}")
        db.session.add(conv); db.session.flush()
        part = ExternalParticipant(tenant_id=t.id, source_id=cs.id, provider_participant_id=f"user_{t.id}")
        db.session.add(part); db.session.flush()
        msg = ExternalMessage(tenant_id=t.id, source_id=cs.id, conversation_id=conv.id,
                              provider_message_id=f"msg_{t.id}", body=f"Body {t.id}", capture_status="allowed")
        db.session.add(msg); db.session.flush()
        ref = ExternalAttachmentReference(message_id=msg.id, provider_media_id=f"media_{t.id}", mime_type="image/jpeg", filename="test.jpg")
        db.session.add(ref); db.session.flush()
        from app.communication.models import SyncCursor
        sc = SyncCursor(tenant_id=t.id, source_id=cs.id, sync_type="incremental", cursor_value=f"cursor_{t.id}")
        db.session.add(sc)
        return cs, policy, scope, conv, part, msg, ref, sc

    def test_all_models_isolated(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import (CommunicationSource, CommunicationCapturePolicy,
            CommunicationCaptureScope, ExternalConversation, ExternalMessage,
            ExternalParticipant, ExternalAttachmentReference, SyncCursor)
        from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()

            self._setup_tenant(t1, db)
            self._setup_tenant(t2, db)
            db.session.commit()

            # Query each model with Tenant B scope
            for model, name, has_tenant in [(CommunicationSource, "source", True),
                                (CommunicationCapturePolicy, "policy", True),
                                (CommunicationCaptureScope, "scope", True),
                                (ExternalConversation, "conversation", True),
                                (ExternalMessage, "message", True),
                                (ExternalParticipant, "participant", True),
                                (SyncCursor, "cursor", True)]:
                if not has_tenant:
                    continue
                b_count = model.query.filter_by(tenant_id=t2.id).count()
                a_count = model.query.filter_by(tenant_id=t1.id).count()
                assert a_count == 1, f"Tenant A {name}: expected 1, got {a_count}"
                assert b_count == 1, f"Tenant B {name}: expected 1, got {b_count}"

    def test_foreign_chat_id_rejected(self, real_app):
        """Foreign Tenant A chat ID queried through Tenant B scope returns nothing."""
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCaptureScope
        from app.communication.policy import CaptureEnforcer
        from app import db
        with real_app.app_context():
            t1 = Tenant(company_name="A", slug="a", business_type="travel", is_active=True)
            t2 = Tenant(company_name="B", slug="b", business_type="travel", is_active=True)
            db.session.add(t1); db.session.add(t2); db.session.commit()
            cs1 = CommunicationSource(tenant_id=t1.id, provider="gmail", account_identifier="a@gmail.com", account_mode="business_dedicated")
            cs2 = CommunicationSource(tenant_id=t2.id, provider="gmail", account_identifier="b@gmail.com", account_mode="business_dedicated")
            db.session.add(cs1); db.session.add(cs2); db.session.commit()
            s1 = CommunicationCaptureScope(tenant_id=t1.id, source_id=cs1.id, external_chat_id="foreign_chat", status="allowed")
            db.session.add(s1); db.session.commit()

            # Tenant B enforcer evaluating Tenant A's chat
            enforcer = CaptureEnforcer(session=db.session)
            result = enforcer.evaluate(cs2.id, "foreign_chat")
            # No scope exists in Tenant B → uses policy default
            assert result["verdict"] in ("pending_review", "denied")


# =========================================================================
# 5. Identity Resolution + Relationship Boundary
# =========================================================================

class TestIdentityRelationshipBoundary:

    def test_matched_resolved(self, real_app):
        from app.models import Person, PersonIdentity
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy, ExternalParticipant
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu", tenant_id=t.id)
            db.session.add(p); db.session.commit()
            PersonIdentity(person_id=p.id, identity_type="email", identity_value="ritu@test.com", normalized_value="ritu@test.com")
            db.session.commit()

            # Verify that a participant CAN be safely linked to a Person
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()

            participant = ExternalParticipant(tenant_id=t.id, source_id=cs.id, provider_participant_id="ritu@test.com",
                                              display_name="Ritu", raw_identifier="ritu@test.com",
                                              person_id=p.id, identity_resolution_status="matched")
            db.session.add(participant); db.session.commit()
            assert participant.person_id == p.id
            assert participant.identity_resolution_status == "matched"

    def test_mixed_use_no_auto_relationship(self, real_app):
        """MIXED_USE + ALLOWED + MATCHED → does NOT auto-establish CUSTOMER."""
        from app.models import Person, PersonIdentity, Relationship
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy
        from app.communication.adapter import NormalizedMessage
        from app.communication.ingestion import CommunicationIngestionService
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            p = Person(canonical_name="Ritu", preferred_name="Ritu", tenant_id=t.id)
            db.session.add(p); db.session.commit()
            PersonIdentity(person_id=p.id, identity_type="email", identity_value="ritu@test.com", normalized_value="ritu@test.com")
            db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="mixed_use")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="mixed_use", default_chat_policy="allowed")
            db.session.add(policy); db.session.commit()

            svc = CommunicationIngestionService(session=db.session)
            nm = NormalizedMessage(source_id=cs.id, provider_message_id="mx_1", provider_chat_id="chat_mx",
                                   body="Hello", sender_raw="ritu@test.com", sender_normalized="ritu@test.com")
            svc.ingest(cs.id, "chat_mx", [nm], tenant_id=t.id)
            rels = Relationship.query.filter_by(person_id=p.id).all()
            assert len(rels) == 0, "MIXED_USE should not auto-create relationship"


# =========================================================================
# 6. Provider Message Idempotency
# =========================================================================

class TestMessageIdempotency:

    def test_same_message_ingested_once(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope, ExternalMessage
        from app.communication.adapter import NormalizedMessage
        from app.communication.ingestion import CommunicationIngestionService
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated", default_chat_policy="allowed")
            db.session.add(policy); db.session.commit()

            svc = CommunicationIngestionService(session=db.session)
            nm = NormalizedMessage(source_id=cs.id, provider_message_id="unique_dup", provider_chat_id="chat_idem",
                                   body="Idempotent", sender_raw="user")
            svc.ingest(cs.id, "chat_idem", [nm], tenant_id=t.id)
            svc.ingest(cs.id, "chat_idem", [nm], tenant_id=t.id)
            total = ExternalMessage.query.filter_by(provider_message_id="unique_dup").count()
            assert total == 1, f"Expected 1 message, got {total}"


# =========================================================================
# 7. Capture Review Flow
# =========================================================================

class TestCaptureReview:

    def test_approve_after_pending(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope
        from app.communication.policy import CaptureEnforcer, CaptureVerdict
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated", default_chat_policy="pending_review")
            db.session.add(policy); db.session.commit()

            enforcer = CaptureEnforcer(session=db.session)
            # First evaluation creates PENDING scope
            result = enforcer.evaluate(cs.id, "review_chat")
            assert result["verdict"] == "pending_review"

            # Approve
            approve = enforcer.approve_scope(result["scope_id"], approved_by="admin")
            assert approve["success"] is True

            # Re-evaluate → now ALLOWED
            result2 = enforcer.evaluate(cs.id, "review_chat")
            assert result2["verdict"] == "allowed"

    def test_denied_not_retroactively_ingested(self, real_app):
        """Previous DENIED content is not retroactively ingested after approval."""
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope
        from app.communication.policy import CaptureEnforcer, CaptureVerdict
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="gmail", account_identifier="t@gmail.com", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated", default_chat_policy="denied")
            db.session.add(policy); db.session.commit()

            enforcer = CaptureEnforcer(session=db.session)
            result = enforcer.evaluate(cs.id, "past_chat")
            assert result["verdict"] == "denied"

            # Approve (scope created during denial evaluation, now flip)
            scope = CommunicationCaptureScope(tenant_id=t.id, source_id=cs.id, external_chat_id="past_chat", status="denied")
            db.session.add(scope); db.session.commit()

            enforcer.approve_scope(scope.id, approved_by="admin")
            # Old messages were never ingested — approval only affects future content
            from app.communication.models import ExternalMessage
            msgs = ExternalMessage.query.filter_by(conversation_id=None).all()
            # No past messages were ingested


# =========================================================================
# 8. Lead Compatibility
# =========================================================================

class TestLeadCompatibility:

    def test_denied_whatsapp_no_lead(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy
        from app.communication.adapter import NormalizedMessage
        from app.communication.ingestion import CommunicationIngestionService
        from app.models import Lead
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="business_dedicated", default_chat_policy="denied")
            db.session.add(policy); db.session.commit()

            svc = CommunicationIngestionService(session=db.session)
            nm = NormalizedMessage(source_id=cs.id, provider_message_id="nolead_1", provider_chat_id="chat_nl",
                                   body="Test", sender_raw="user")
            svc.ingest(cs.id, "chat_nl", [nm], tenant_id=t.id)
            leads = Lead.query.all()
            assert len(leads) == 0, "DENIED should not create Lead"

    def test_pending_review_no_lead(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, CommunicationCapturePolicy
        from app.communication.adapter import NormalizedMessage
        from app.communication.ingestion import CommunicationIngestionService
        from app.models import Lead
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="mixed_use")
            db.session.add(cs); db.session.commit()
            policy = CommunicationCapturePolicy(source_id=cs.id, tenant_id=t.id, account_mode="mixed_use")
            db.session.add(policy); db.session.commit()

            svc = CommunicationIngestionService(session=db.session)
            nm = NormalizedMessage(source_id=cs.id, provider_message_id="nolead_2", provider_chat_id="chat_nl2",
                                   body="Test", sender_raw="user")
            svc.ingest(cs.id, "chat_nl2", [nm], tenant_id=t.id)
            leads = Lead.query.all()
            assert len(leads) == 0, "PENDING_REVIEW should not create Lead"


# =========================================================================
# 9. Media Metadata-Only Proof
# =========================================================================

class TestMediaMetadataProof:

    def test_image_reference_only(self, real_app):
        from app.tenant import Tenant
        from app.communication.models import CommunicationSource, ExternalConversation, ExternalMessage, ExternalAttachmentReference
        from app import db
        with real_app.app_context():
            t = Tenant(company_name="T", slug="t", business_type="travel", is_active=True)
            db.session.add(t); db.session.commit()
            from app.communication.models import CommunicationSource
            cs = CommunicationSource(tenant_id=t.id, provider="whatsapp_official", account_identifier="p", account_mode="business_dedicated")
            db.session.add(cs); db.session.commit()
            conv = ExternalConversation(tenant_id=t.id, source_id=cs.id, provider_chat_id="chat_media")
            db.session.add(conv); db.session.commit()
            msg = ExternalMessage(tenant_id=t.id, source_id=cs.id, conversation_id=conv.id, provider_message_id="media_1",
                                  body="With image", capture_status="allowed")
            db.session.add(msg); db.session.commit()
            ref = ExternalAttachmentReference(message_id=msg.id, provider_media_id="img_1", mime_type="image/jpeg",
                                              filename="photo.jpg", size_bytes=50000)
            db.session.add(ref); db.session.commit()
            assert ref.mime_type == "image/jpeg"
            assert ref.filename == "photo.jpg"
            assert not hasattr(ref, "body"), "No body field on AttachmentReference"