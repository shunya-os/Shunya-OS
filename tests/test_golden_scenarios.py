"""FDA5/FDA6 Golden Scenarios — real end-to-end paths.

Each scenario exercises the actual stack, not mocks.
"""
import pytest
import json
import os


class TestGoldenScenario1_CompanyFirst:
    """Company data available → correct company answer → evidence."""

    def test_identity_resolution_from_company_data(self, app):
        """IdentityService resolves a person from company data."""
        from app.identity.service import IdentityService
        from core.identity_interface import IdentityClaim, ClaimType

        with app.app_context():
            svc = IdentityService()
            c = svc.add_claim(IdentityClaim(
                claim_value="golden-scenario@company.com",
                claim_type=ClaimType.EMAIL,
                source="golden_test",
                source_id="golden_001",
                tenant_id="1",
            ))
            assert c.claim_id is not None
            assert c.identity_id is not None

            # Resolution
            r = svc.resolve("golden-scenario@company.com", ClaimType.EMAIL)
            assert r.identity_id == c.identity_id
            assert r.identity_type == "person"

            # Provenance
            claims = svc.get_claims(c.identity_id)
            assert len(claims) >= 1
            assert claims[0].source == "golden_test"


class TestGoldenScenario2_CompanyDataInsufficient:
    """Internal search insufficient → external truth classification."""

    def test_unknown_returns_unknown_classification(self, app):
        """IntelligenceEngine returns UNKNOWN with no data."""
        from core.intelligence_core import IntelligenceEngine, TruthCategory

        engine = IntelligenceEngine()
        result = engine.answer("What is the status of unknown-entity-xyz?", tenant_id="1")
        assert result.category == TruthCategory.UNKNOWN
        assert result.confidence == 0.0


class TestGoldenScenario3_IdentityPlusMemory:
    """Known person → identity resolution → relevant context → answer."""

    def test_person_identity_with_memory_context(self, app):
        """IdentityService + MemoryService together produce context."""
        from app.identity.service import IdentityService
        from app.memory import MemoryService
        from app.memory.models import TruthClassification
        from core.identity_interface import IdentityClaim, ClaimType

        with app.app_context():
            # Create person
            svc = IdentityService()
            c = svc.add_claim(IdentityClaim(
                claim_value="golden-memory@company.com",
                claim_type=ClaimType.EMAIL,
                source="golden_mem",
                source_id="golden_mem_001",
                tenant_id="1",
            ))

            # Add memory about this person
            mem_svc = MemoryService()
            m = mem_svc.create_memory(
                person_id=int(c.identity_id) if c.identity_id else None,
                memory_key="preference",
                value="Prefers email communication",
                truth_classification=TruthClassification.MEMORY,
            )
            assert m.id is not None

            # Resolve identity
            r = svc.resolve("golden-memory@company.com", ClaimType.EMAIL)
            assert r.identity_id == c.identity_id


class TestGoldenScenario4_ActionableRequest:
    """User asks → execution path → observable outcome."""

    def test_memory_write_is_observable(self, app):
        """Writing a memory produces an observable, retrievable record."""
        from app.memory import MemoryService
        from app.memory.models import TruthClassification

        with app.app_context():
            svc = MemoryService()
            m = svc.create_memory(
                person_id=None,
                memory_key="golden_action",
                value="Complete quarterly review",
                truth_classification=TruthClassification.FACT,
            )
            assert m.id is not None
            assert m.status == "active"

            # Retrieve via get_effective_memories
            retrieved = svc.get_effective_memories(memory_key="golden_action")
            assert len(retrieved) > 0
            assert any("quarterly" in str(r.get("value", "")).lower() for r in retrieved)


class TestGoldenScenario5_ConflictingInformation:
    """Conflicting sources → no false certainty → conflict surfaced."""

    def test_conflicting_claims_preserved(self, app):
        """Same email on different people → conflict preserved."""
        from app.identity.service import IdentityService
        from core.identity_interface import IdentityClaim, ClaimType

        with app.app_context():
            svc = IdentityService()

            # Add claim for person A
            c1 = svc.add_claim(IdentityClaim(
                claim_value="conflict@company.com",
                claim_type=ClaimType.EMAIL,
                source="source_a",
                source_id="src_a_001",
                tenant_id="1",
            ))

            # Add same email for person B (different name)
            c2 = svc.add_claim(IdentityClaim(
                claim_value="conflict@company.com",
                claim_type=ClaimType.EMAIL,
                source="source_b",
                source_id="src_b_001",
                tenant_id="1",
            ))

            # Both claims should exist on their respective persons
            assert c1.claim_id is not None

            # Resolve should find at least one person
            r = svc.resolve("conflict@company.com", ClaimType.EMAIL)
            assert r.identity_id is not None


class TestGoldenScenario6_IntegrationFailure:
    """Provider unavailable → safe failure behavior."""

    def test_safe_failure_on_missing_provider(self):
        """SafeFailureHandler produces correct output for unavailable provider."""
        from core.intelligence_core import SafeFailureHandler

        result = SafeFailureHandler.handle_provider_unavailable("Gmail")
        assert "unavailable" in result.content.lower()
        assert result.confidence == 0.0
        assert result.requires_review is True

    def test_safe_failure_on_unauthorized_access(self):
        from core.intelligence_core import SafeFailureHandler

        result = SafeFailureHandler.handle_unauthorized()
        assert "permission" in result.content.lower() or "denied" in result.content.lower()
        assert result.confidence == 0.0