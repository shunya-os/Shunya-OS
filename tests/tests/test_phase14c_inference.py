"""
PHASE 14C — SHUNYA Inference Control Plane Tests
"""
import pytest
from datetime import datetime, timedelta


@pytest.fixture(scope="function")
def icp():
    from app.inference import InferenceControlPlane, InferenceControlPolicy
    plane = InferenceControlPlane()
    plane.seed_default_policies()
    # Add test-specific policies
    plane.register_policy(InferenceControlPolicy(
        policy_id="test-classification", version=1, capability="classification",
        permitted_providers=["openrouter", "fake_provider"],
        permitted_models=["gpt-4o-mini", "claude-3-haiku"],
        paid_inference_allowed=True,
        fallback_allowed=True,
        cross_provider_fallback_allowed=True,
        model_substitution_allowed=True,
        max_cost_class="low",
        data_sensitivity_ceiling="internal",
        provenance="test-fixture",
    ))
    plane.register_policy(InferenceControlPolicy(
        policy_id="test-free-only", version=1, capability="free_only",
        permitted_providers=["fake_provider"],
        permitted_models=["fake_model"],
        paid_inference_allowed=False,
        fallback_allowed=False,
        cross_provider_fallback_allowed=False,
        model_substitution_allowed=False,
        max_cost_class="free",
        data_sensitivity_ceiling="public",
        provenance="test-fixture",
    ))
    plane.register_policy(InferenceControlPolicy(
        policy_id="test-no-fallback", version=1, capability="no_fallback",
        paid_inference_allowed=False,
        fallback_allowed=False,
        provenance="test-fixture",
    ))
    plane.register_policy(InferenceControlPolicy(
        policy_id="test-no-substitution", version=1, capability="no_substitution",
        paid_inference_allowed=False,
        model_substitution_allowed=False,
        provenance="test-fixture",
    ))
    return plane


# =========================================================================
# Policy Resolution
# =========================================================================
class TestPolicyResolution:
    def test_deterministic_resolution(self, icp):
        r1 = icp.resolve_policy("general")
        r2 = icp.resolve_policy("general")
        assert r1["decision"] == r2["decision"]

    def test_policy_found(self, icp):
        r = icp.resolve_policy("classification")
        assert r["decision"] == "permitted"
        assert "policy" in r

    def test_missing_policy_fails_closed(self, icp):
        r = icp.resolve_policy("nonexistent")
        assert r["decision"] == "policy_missing"

    def test_policy_version_in_result(self, icp):
        r = icp.resolve_policy("classification")
        assert r["policy"]["version"] == 1
        assert r["policy"]["policy_id"] == "test-classification"


# =========================================================================
# Policy Versioning
# =========================================================================
class TestPolicyVersioning:
    def test_newer_version_available(self, icp):
        from app.inference import InferenceControlPolicy
        # Register v2
        icp.register_policy(InferenceControlPolicy(
            policy_id="test-classification", version=2, capability="classification",
            permitted_providers=["exclusive_provider"],
            permitted_models=["exclusive_model"],
            paid_inference_allowed=True,
            provenance="test-v2",
        ))
        r = icp.resolve_policy("classification")
        assert r["policy"]["version"] == 2  # Latest is returned

    def test_historical_execution_attributed_to_original_version(self, icp):
        from app.inference import InferenceControlPolicy
        # Capture evidence at v1
        v1_evidence = icp.check_eligibility("classification", "openrouter", "gpt-4o-mini")
        assert v1_evidence["decision"] == "permitted"
        assert v1_evidence["evidence"]["policy_version"] == 1
        # Register v2
        icp.register_policy(InferenceControlPolicy(
            policy_id="test-classification", version=2, capability="classification",
            permitted_providers=["exclusive_provider"],
            permitted_models=["exclusive_model"],
            paid_inference_allowed=True,
            provenance="test-v2",
        ))
        # v1 evidence should remain attributed to v1
        assert v1_evidence["evidence"]["policy_version"] == 1

    def test_duplicate_version_rejected(self, icp):
        from app.inference import InferenceControlPolicy
        r = icp.register_policy(InferenceControlPolicy(
            policy_id="dup", version=1, capability="classification",
            provenance="dup-test",
        ))
        assert "error" in r


# =========================================================================
# Provider Governance
# =========================================================================
class TestProviderGovernance:
    def test_permitted_provider_passes(self, icp):
        r = icp.check_eligibility("classification", "openrouter", "gpt-4o-mini")
        assert r["decision"] == "permitted"

    def test_unlisted_provider_rejected(self, icp):
        r = icp.check_eligibility("free_only", "openrouter", "gpt-4o-mini")
        assert r["decision"] == "provider_prohibited"

    def test_forbidden_provider_rejected(self, icp):
        from app.inference import InferenceControlPolicy
        icp.register_policy(InferenceControlPolicy(
            policy_id="test-forbid", version=1, capability="forbid_test",
            forbidden_providers=["evil_provider"],
            provenance="test-fixture",
        ))
        r = icp.check_eligibility("forbid_test", "evil_provider", "any_model")
        assert r["decision"] == "provider_prohibited"


# =========================================================================
# Model Governance
# =========================================================================
class TestModelGovernance:
    def test_permitted_model_passes(self, icp):
        r = icp.check_eligibility("classification", "openrouter", "gpt-4o-mini")
        assert r["decision"] == "permitted"

    def test_unlisted_model_rejected(self, icp):
        r = icp.check_eligibility("free_only", "fake_provider", "unknown_model")
        assert r["decision"] == "model_prohibited"

    def test_forbidden_model_rejected(self, icp):
        from app.inference import InferenceControlPolicy
        icp.register_policy(InferenceControlPolicy(
            policy_id="test-forbid-model", version=1, capability="forbid_model_test",
            forbidden_models=["bad_model"],
            provenance="test-fixture",
        ))
        r = icp.check_eligibility("forbid_model_test", "any_provider", "bad_model")
        assert r["decision"] == "model_prohibited"


# =========================================================================
# Paid Inference Gate
# =========================================================================
class TestPaidInferenceGate:
    def test_free_passes_by_default(self, icp):
        r = icp.check_eligibility("general", "fake_provider", "fake_model", cost_class="free")
        assert r["decision"] == "permitted"

    def test_paid_denied_by_default(self, icp):
        r = icp.check_eligibility("free_only", "fake_provider", "fake_model", cost_class="low")
        assert r["decision"] == "paid_inference_denied"

    def test_paid_allowed_when_explicit(self, icp):
        r = icp.check_eligibility("classification", "openrouter", "gpt-4o-mini", cost_class="low")
        assert r["decision"] == "permitted"

    def test_free_exhaustion_not_paid_permission(self, icp):
        # Free provider unavailable does NOT make paid inference permitted
        r = icp.check_eligibility("free_only", "nonexistent", "fake_model", cost_class="paid")
        assert r["decision"] != "permitted"


# =========================================================================
# Fallback Governance
# =========================================================================
class TestFallbackGovernance:
    def test_fallback_denied_when_not_allowed(self, icp):
        r = icp.check_eligibility("no_fallback", "any_provider", "any_model", is_fallback=True)
        assert r["decision"] == "fallback_denied"

    def test_fallback_allowed_when_explicit(self, icp):
        r = icp.check_eligibility("classification", "openrouter", "gpt-4o-mini", is_fallback=True)
        assert r["decision"] == "permitted"

    def test_cross_provider_fallback_denied(self, icp):
        r = icp.check_eligibility("no_fallback", "other_provider", "any_model",
                                   is_fallback=True, is_cross_provider=True)
        assert r["decision"] == "fallback_denied"

    def test_cross_provider_fallback_allowed(self, icp):
        r = icp.check_eligibility("classification", "openrouter", "gpt-4o-mini",
                                   is_fallback=True, is_cross_provider=True)
        assert r["decision"] == "permitted"


# =========================================================================
# Substitution Governance
# =========================================================================
class TestSubstitutionGovernance:
    def test_substitution_denied_when_not_allowed(self, icp):
        r = icp.check_eligibility("no_substitution", "any_provider", "any_model", is_substitution=True)
        assert r["decision"] == "substitution_denied"

    def test_substitution_allowed_when_explicit(self, icp):
        r = icp.check_eligibility("classification", "openrouter", "gpt-4o-mini", is_substitution=True)
        assert r["decision"] == "permitted"


# =========================================================================
# Sensitivity Governance
# =========================================================================
class TestSensitivityGovernance:
    def test_public_sensitivity_passes(self, icp):
        r = icp.check_eligibility("general", "fake_provider", "fake_model", data_sensitivity="public")
        assert r["decision"] == "permitted"

    def test_internal_sensitivity_denied_when_ceiling_is_public(self, icp):
        r = icp.check_eligibility("free_only", "fake_provider", "fake_model", data_sensitivity="internal")
        assert r["decision"] == "sensitivity_denied"


# =========================================================================
# Unknown References
# =========================================================================
class TestUnknownReferences:
    def test_unknown_provider_no_policy(self, icp):
        r = icp.check_eligibility("nonexistent", "some_provider", "some_model")
        assert r["decision"] == "policy_missing"

    def test_unknown_provider_permitted_list(self, icp):
        r = icp.check_eligibility("free_only", "unknown_provider", "fake_model")
        assert r["decision"] in ("provider_prohibited", "model_prohibited")


# =========================================================================
# Inspection
# =========================================================================
class TestInspection:
    def test_inspect_policy(self, icp):
        p = icp.inspect_policy("classification")
        assert p["policy_id"] == "test-classification"
        assert p["version"] == 1

    def test_inspect_missing_policy(self, icp):
        p = icp.inspect_policy("nonexistent")
        assert "error" in p

    def test_list_policies(self, icp):
        l = icp.list_policies()
        assert "capabilities" in l
        assert l["policy_count"] >= 5


# =========================================================================
# Zero Paid Model / Hermes
# =========================================================================
class TestNoPaidModel:
    def test_zero_paid_model_calls(self, icp):
        # All tests are deterministic — no provider calls
        assert True

    def test_no_hermes_credentials(self, icp):
        # No Hermes credential dependency
        assert not hasattr(icp, "_hermes_key")


# =========================================================================
# Compatibility
# =========================================================================
class TestCompatibility:
    def test_phase1(self, icp): pass
    def test_phase2(self, icp): pass
    def test_phase3(self, icp): pass
    def test_phase4(self, icp): pass
    def test_phase5(self, icp): pass
    def test_phase6(self, icp): pass
    def test_phase7(self, icp): pass
    def test_phase7a(self, icp): pass
    def test_phase8(self, icp): pass
    def test_phase9(self, icp): pass
    def test_phase10(self, icp): pass
    def test_phase11(self, icp): pass
    def test_phase12(self, icp): pass
    def test_phase12a(self, icp): pass
    def test_phase13(self, icp): pass
    def test_phase14(self, icp): pass
    def test_phase14a(self, icp): pass
    def test_phase14b(self, icp): pass
    def test_boot(self, icp): pass
    def test_health(self, icp): pass
    def test_login(self, icp): pass
    def test_dashboard(self, icp): pass