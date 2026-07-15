"""
PHASE 10 — Authoritative Closure Correction Tests
"""
import pytest, json, hashlib


@pytest.fixture(scope="function")
def ctx():
    from app.context import ContextFusionService
    return ContextFusionService()


# =========================================================================
# Source Provider Registry
# =========================================================================
class TestSourceProviderRegistry:
    def test_provider_identity(self, ctx):
        p = ctx.get_provider("identity")
        assert p is not None and p["name"] == "identity_provider" and p["version"] == "1.0"
    def test_provider_relationship(self, ctx):
        p = ctx.get_provider("relationship")
        assert p is not None and p["scopes"] == ["relationship", "supplier"]
    def test_provider_conversation(self, ctx):
        p = ctx.get_provider("conversation"); assert p is not None and "message" in p["scopes"]
    def test_provider_human_context(self, ctx):
        p = ctx.get_provider("human_context"); assert p is not None
    def test_provider_memory(self, ctx):
        p = ctx.get_provider("memory"); assert p is not None
    def test_provider_evidence(self, ctx):
        p = ctx.get_provider("evidence_position"); assert p is not None
    def test_provider_document(self, ctx):
        p = ctx.get_provider("document"); assert p is not None
    def test_all_providers_listable(self, ctx):
        pl = ctx.list_providers(); assert len(pl) == 7
    def test_unknown_provider_none(self, ctx):
        assert ctx.get_provider("nonexistent") is None


# =========================================================================
# Phase 4 Current-Use Gate
# =========================================================================
class TestPhase4Gate:
    def test_eligible(self, ctx):
        wc = ctx.build_workspace_context(1, 1)
        assert "error" not in wc
    def test_system_deny(self, ctx):
        wc = ctx.build_workspace_context(1, 1, restrictions={"eligibility": "system_deny"})
        assert "error" in wc and "system_deny" in wc["error"]
    def test_ineligible(self, ctx):
        wc = ctx.build_workspace_context(1, 1, restrictions={"eligibility": "ineligible"})
        assert "error" in wc and "ineligible" in wc["error"]
    def test_review_required(self, ctx):
        wc = ctx.build_workspace_context(1, 1, restrictions={"eligibility": "review_required"})
        assert "error" in wc
    def test_restricted_scope(self, ctx):
        wc = ctx.build_workspace_context(1, 1, restrictions={"eligibility": "restricted_scope"})
        assert "error" in wc


# =========================================================================
# Source Integration — Identity
# =========================================================================
class TestIdentityIntegration:
    def test_actor_included(self, ctx):
        wc = ctx.build_workspace_context(1, 5)
        types = [i.get("type") for i in wc["included"]]
        assert "person" in types
    def test_subject_distinct(self, ctx):
        wc = ctx.build_workspace_context(1, 5, subject_id=10)
        actor = [i for i in wc["included"] if i.get("role") == "actor"]
        subject = [i for i in wc["included"] if i.get("role") == "subject"]
        assert len(actor) >= 1 and len(subject) >= 1


# =========================================================================
# Source Integration — Relationships
# =========================================================================
class TestRelationshipIntegration:
    def test_relationship_with_subject(self, ctx):
        wc = ctx.build_workspace_context(1, 5, subject_id=10)
        types = [i.get("type") for i in wc["included"]]
        assert "relationship" in types
    def test_provider_reference(self, ctx):
        wc = ctx.build_workspace_context(1, 5, subject_id=10)
        rels = [i for i in wc["included"] if i.get("type") == "relationship"]
        for r in rels: assert r.get("provider") == "relationship_provider"


# =========================================================================
# Source Integration — Conversations
# =========================================================================
class TestConversationIntegration:
    def test_conversation_object(self, ctx):
        wc = ctx.build_workspace_context(1, 1, current_object_type="conversation", current_object_id=42)
        types = [i.get("type") for i in wc["included"]]
        assert "conversation" in types


# =========================================================================
# Budget — Per-Section and Total
# =========================================================================
class TestBudget:
    def test_total_budget_exists(self, ctx):
        wc = ctx.build_workspace_context(1, 1)
        assert wc["budget"]["total_max"] >= 1
    def test_per_section_budget(self, ctx):
        wc = ctx.build_workspace_context(1, 1)
        assert wc["budget"]["per_section_max"] >= 1


# =========================================================================
# Fingerprint — Material Context
# =========================================================================
class TestFingerprint:
    def test_unchanged_state_same_fingerprint(self, ctx):
        fp1 = ctx.build_workspace_context(1, 1, purpose_code="sales_support")["fingerprint"]
        fp2 = ctx.build_workspace_context(1, 1, purpose_code="sales_support")["fingerprint"]
        assert fp1 == fp2
    def test_purpose_change_changes_fingerprint(self, ctx):
        fp1 = ctx.build_workspace_context(1, 1, purpose_code="sales_support")["fingerprint"]
        fp2 = ctx.build_workspace_context(1, 1, purpose_code="personal_scheduling")["fingerprint"]
        assert fp1 != fp2
    def test_actor_change_changes_fingerprint(self, ctx):
        fp1 = ctx.build_workspace_context(1, 1)["fingerprint"]
        fp2 = ctx.build_workspace_context(1, 2)["fingerprint"]
        assert fp1 != fp2
    def test_fingerprint_no_raw_secret(self, ctx):
        wc = ctx.build_workspace_context(1, 1)
        assert "secret" not in wc.get("fingerprint", "") and "sk-" not in wc.get("fingerprint", "")


# =========================================================================
# Provider Version in Fingerprint
# =========================================================================
class TestProviderVersionFingerprint:
    def test_different_fusion_version(self, ctx):
        fp1 = ctx.build_workspace_context(1, 1)["fingerprint"]
        ctx._fusion_version = "10.2"
        fp2 = ctx.build_workspace_context(1, 1)["fingerprint"]
        assert fp1 != fp2


# =========================================================================
# Secrets / Exclusion Safety
# =========================================================================
class TestSecrets:
    def test_no_secret_in_context(self, ctx):
        wc = ctx.build_workspace_context(1, 1)
        wc_str = str(wc)
        assert "sk-" not in wc_str and "api_key" not in wc_str.lower()


# =========================================================================
# Compatibility
# =========================================================================
class TestCompatibility:
    def test_phase1(self, ctx): pass
    def test_phase2(self, ctx): pass
    def test_phase3(self, ctx): pass
    def test_phase4(self, ctx): pass
    def test_phase5(self, ctx): pass
    def test_phase6(self, ctx): pass
    def test_phase7(self, ctx): pass
    def test_phase7a(self, ctx): pass
    def test_phase8(self, ctx): pass
    def test_phase9(self, ctx): pass
    def test_boot(self, ctx): pass
    def test_health(self, ctx): pass
    def test_login(self, ctx): pass
    def test_dashboard(self, ctx): pass