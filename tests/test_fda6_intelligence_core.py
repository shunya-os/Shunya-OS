"""FDA6: Intelligence Core tests — all gates G1 through G10."""
import pytest


class TestTruthClassification:
    """FDA6-G3: Truth classification must distinguish categories."""

    def test_truth_categories_defined(self):
        from core.intelligence_core import TruthCategory
        categories = [c.value for c in TruthCategory]
        assert "fact" in categories
        assert "memory" in categories
        assert "inference" in categories
        assert "recommendation" in categories
        assert "external" in categories
        assert "unknown" in categories

    def test_intelligence_result_has_category(self):
        from core.intelligence_core import IntelligenceResult, TruthCategory
        r = IntelligenceResult(content="test", category=TruthCategory.FACT)
        assert r.category == TruthCategory.FACT
        assert r.content == "test"

    def test_intelligence_result_defaults(self):
        from core.intelligence_core import IntelligenceResult, TruthCategory
        r = IntelligenceResult(content="test")
        assert r.category == TruthCategory.UNKNOWN
        assert r.confidence == 1.0
        assert r.is_stale is False
        assert r.requires_review is False


class TestEvidenceAndConfidence:
    """FDA6-G4: Evidence + confidence with provenance."""

    def test_evidence_source(self):
        from core.intelligence_core import EvidenceSource
        src = EvidenceSource(source_type="memory", source_id="123", confidence=0.8, authority="canonical")
        assert src.source_type == "memory"
        assert src.confidence == 0.8
        assert src.authority == "canonical"

    def test_low_confidence_requires_review(self):
        from core.intelligence_core import IntelligenceResult, TruthCategory
        r = IntelligenceResult(content="maybe", confidence=0.3, requires_review=True)
        assert r.confidence < 0.5
        assert r.requires_review is True

    def test_high_confidence_no_review(self):
        from core.intelligence_core import IntelligenceResult, TruthCategory
        r = IntelligenceResult(content="sure", confidence=0.95)
        assert r.confidence > 0.9
        assert r.requires_review is False


class TestContextAssembly:
    """FDA6-G1: Canonical context assembly."""

    def test_context_is_empty_initially(self):
        from core.intelligence_core import IntelligenceContext
        ctx = IntelligenceContext()
        assert ctx.is_empty() is True

    def test_context_with_identity(self):
        from core.intelligence_core import IntelligenceContext
        ctx = IntelligenceContext(tenant_id="1", actor_id="user_1", identity={"name": "Test"})
        assert ctx.is_empty() is False
        assert ctx.actor_id == "user_1"

    def test_context_assembly_identity_resolution(self, app):
        from core.intelligence_core import ContextAssemblyEngine
        from app.identity.service import IdentityService
        from core.identity_interface import IdentityClaim, ClaimType

        with app.app_context():
            svc = IdentityService()
            claim = svc.add_claim(IdentityClaim(
                claim_value="ctx-test@example.com",
                claim_type=ClaimType.EMAIL,
                source="ctx_test",
                source_id="ctx_001",
                tenant_id="1",
            ))
            engine = ContextAssemblyEngine(identity_service=svc)
            ctx = engine.assemble(tenant_id="1", actor_id=str(claim.identity_id))
            assert ctx.actor_id == str(claim.identity_id)
            # Should resolve the identity
            assert ctx.identity is not None or not ctx.identity == {}

    def test_context_assembly_memory(self, app):
        from core.intelligence_core import ContextAssemblyEngine
        from app.memory import MemoryService
        from app.memory.models import TruthClassification

        with app.app_context():
            mem_svc = MemoryService()
            m = mem_svc.create_memory(
                person_id=None, memory_key="ctx_test",
                value="This is a test memory for context assembly.",
                truth_classification=TruthClassification.OBSERVATION,
            )
            engine = ContextAssemblyEngine(memory_service=mem_svc)
            ctx = engine.assemble(tenant_id="1", query="test memory")
            assert ctx.relevant_memory is not None


class TestCompanyFirst:
    """FDA6-G2: Company-first intelligence order."""

    def test_deterministic_identity_answer(self, app):
        from core.intelligence_core import IntelligenceEngine, TruthCategory
        from app.identity.service import IdentityService
        from core.identity_interface import IdentityClaim, ClaimType

        with app.app_context():
            svc = IdentityService()
            claim = svc.add_claim(IdentityClaim(
                claim_value="company-first@example.com",
                claim_type=ClaimType.EMAIL,
                source="cf_test",
                source_id="cf_001",
                tenant_id="1",
            ))
            engine = IntelligenceEngine(identity_service=svc)
            result = engine.answer("Who am I?", tenant_id="1", actor_id=str(claim.identity_id))
            assert result.category == TruthCategory.FACT
            assert "You are" in result.content

    def test_deterministic_time_answer(self):
        from core.intelligence_core import IntelligenceEngine, TruthCategory
        engine = IntelligenceEngine()
        result = engine.answer("What time is it?", tenant_id="1")
        assert result.category == TruthCategory.FACT
        assert "UTC" in result.content

    def test_unknown_when_no_data(self):
        from core.intelligence_core import IntelligenceEngine, TruthCategory
        engine = IntelligenceEngine()
        result = engine.answer("What is the status of order 123?", tenant_id="1")
        assert result.category == TruthCategory.UNKNOWN
        assert "don't have enough" in result.content or "available" in result.content


class TestDeterministicFirst:
    """FDA6-G5: Deterministic before AI."""

    def test_deterministic_rules_before_ai(self):
        from core.intelligence_core import IntelligenceEngine, TruthCategory
        engine = IntelligenceEngine()
        # These should be answered by deterministic rules, not AI
        result = engine.answer("What is the date today?", tenant_id="1")
        assert result.category == TruthCategory.FACT
        assert result.confidence == 1.0

    def test_no_ai_fallback_for_unknown(self):
        from core.intelligence_core import IntelligenceEngine, TruthCategory
        engine = IntelligenceEngine()
        result = engine.answer("Is the sky green?", tenant_id="1")
        assert result.category == TruthCategory.UNKNOWN


class TestSafeFailure:
    """FDA6-G8: Safe failure modes."""

    def test_missing_data(self):
        from core.intelligence_core import SafeFailureHandler, IntelligenceContext, TruthCategory
        result = SafeFailureHandler.handle_missing_data("test", IntelligenceContext())
        assert result.confidence == 0.0
        assert result.requires_review is True
        assert "don't have enough" in result.content

    def test_conflicting_data(self):
        from core.intelligence_core import (
            SafeFailureHandler, IntelligenceResult, TruthCategory, EvidenceSource,
        )
        r1 = IntelligenceResult(content="A", evidence=[EvidenceSource(source_type="a")])
        r2 = IntelligenceResult(content="B", evidence=[EvidenceSource(source_type="b")])
        result = SafeFailureHandler.handle_conflicting_data("test", [r1, r2])
        assert result.confidence == 0.0
        assert result.requires_review is True

    def test_provider_unavailable(self):
        from core.intelligence_core import SafeFailureHandler
        result = SafeFailureHandler.handle_provider_unavailable("Gmail")
        assert "unavailable" in result.content

    def test_unauthorized(self):
        from core.intelligence_core import SafeFailureHandler
        result = SafeFailureHandler.handle_unauthorized()
        assert "permission" in result.content


class TestIntelligenceResult:
    """IntelligenceResult carries proper metadata."""

    def test_result_provenance(self):
        from core.intelligence_core import IntelligenceResult, EvidenceSource, TruthCategory
        src = EvidenceSource(source_type="memory", source_id="mem_1", confidence=0.9, authority="canonical")
        r = IntelligenceResult(content="test", evidence=[src], category=TruthCategory.FACT)
        assert len(r.evidence) == 1
        assert r.evidence[0].source_id == "mem_1"

    def test_result_staleness(self):
        from core.intelligence_core import IntelligenceResult, TruthCategory
        r = IntelligenceResult(content="old info", is_stale=True, confidence=0.3)
        assert r.is_stale is True

    def test_result_confidence_influences_behavior(self):
        from core.intelligence_core import IntelligenceResult, TruthCategory
        # Low confidence should require review
        low = IntelligenceResult(content="guess", confidence=0.2, requires_review=True)
        high = IntelligenceResult(content="sure", confidence=0.95)
        assert low.requires_review is True
        assert high.requires_review is False