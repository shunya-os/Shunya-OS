"""
SHUNYA — Inference Control Plane (Phase 14C, computation-only)

Governs inference placement and execution eligibility.
Does NOT make permanent model placement decisions.
Does NOT call providers.
"""
import hashlib, json, uuid
from datetime import datetime
from typing import Optional

# Control decision states
class ControlDecision:
    PERMITTED = "permitted"
    PROVIDER_PROHIBITED = "provider_prohibited"
    MODEL_PROHIBITED = "model_prohibited"
    PAID_INFERENCE_DENIED = "paid_inference_denied"
    SENSITIVITY_DENIED = "sensitivity_denied"
    FALLBACK_DENIED = "fallback_denied"
    CROSS_PROVIDER_FALLBACK_DENIED = "cross_provider_fallback_denied"
    SUBSTITUTION_DENIED = "substitution_denied"
    POLICY_MISSING = "policy_missing"
    POLICY_AMBIGUOUS = "policy_ambiguous"
    UNKNOWN_PROVIDER = "unknown_provider"
    UNKNOWN_MODEL = "unknown_model"


class InferenceControlPolicy:
    """Versioned inference control policy."""

    def __init__(self, policy_id: str, version: int, capability: str,
                 permitted_providers: Optional[list] = None,
                 forbidden_providers: Optional[list] = None,
                 permitted_models: Optional[list] = None,
                 forbidden_models: Optional[list] = None,
                 paid_inference_allowed: bool = False,
                 fallback_allowed: bool = False,
                 cross_provider_fallback_allowed: bool = False,
                 model_substitution_allowed: bool = False,
                 max_cost_class: str = "free",
                 data_sensitivity_ceiling: str = "public",
                 effective_at: Optional[str] = None,
                 superseded_at: Optional[str] = None,
                 provenance: Optional[str] = None):
        self.policy_id = policy_id
        self.version = version
        self.capability = capability
        self.permitted_providers = set(permitted_providers or [])
        self.forbidden_providers = set(forbidden_providers or [])
        self.permitted_models = set(permitted_models or [])
        self.forbidden_models = set(forbidden_models or [])
        self.paid_inference_allowed = paid_inference_allowed
        self.fallback_allowed = fallback_allowed
        self.cross_provider_fallback_allowed = cross_provider_fallback_allowed
        self.model_substitution_allowed = model_substitution_allowed
        self.max_cost_class = max_cost_class
        self.data_sensitivity_ceiling = data_sensitivity_ceiling
        self.effective_at = effective_at or datetime.utcnow().isoformat()
        self.superseded_at = superseded_at
        self.provenance = provenance

    def to_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "version": self.version,
            "capability": self.capability,
            "permitted_providers": list(self.permitted_providers),
            "forbidden_providers": list(self.forbidden_providers),
            "permitted_models": list(self.permitted_models),
            "forbidden_models": list(self.forbidden_models),
            "paid_inference_allowed": self.paid_inference_allowed,
            "fallback_allowed": self.fallback_allowed,
            "cross_provider_fallback_allowed": self.cross_provider_fallback_allowed,
            "model_substitution_allowed": self.model_substitution_allowed,
            "max_cost_class": self.max_cost_class,
            "data_sensitivity_ceiling": self.data_sensitivity_ceiling,
            "effective_at": self.effective_at,
            "superseded_at": self.superseded_at,
            "provenance": self.provenance,
        }


class InferenceControlPlane:
    """SHUNYA Inference Control Plane.

    Governs inference placement and execution eligibility.
    Policy resolution is deterministic. No LLM chooses policy.
    """

    def __init__(self):
        self._policies: dict[str, list[InferenceControlPolicy]] = {}  # capability → versioned policies
        self._version = "14c.1"

    # ------------------------------------------------------------------
    # Policy management
    # ------------------------------------------------------------------
    def register_policy(self, policy: InferenceControlPolicy) -> dict:
        """Register a policy. Earlier versions are immutable."""
        cap = policy.capability
        if cap not in self._policies:
            self._policies[cap] = []
        # Check for duplicate version
        for existing in self._policies[cap]:
            if existing.version == policy.version:
                return {"error": "duplicate_policy_version", "capability": cap, "version": policy.version}
        self._policies[cap].append(policy)
        # Sort by version descending so latest is first
        self._policies[cap].sort(key=lambda p: p.version, reverse=True)
        return {"registered": True, "capability": cap, "version": policy.version}

    # ------------------------------------------------------------------
    # Policy resolution
    # ------------------------------------------------------------------
    def resolve_policy(self, capability: str, as_of: Optional[str] = None) -> dict:
        """Resolve the applicable policy for a capability deterministically."""
        if capability not in self._policies or not self._policies[capability]:
            return {
                "decision": ControlDecision.POLICY_MISSING,
                "capability": capability,
                "reasons": ["no_policy_registered"],
            }

        # Find the latest policy that was effective at as_of
        if as_of:
            as_of_dt = datetime.fromisoformat(as_of)
            for policy in self._policies[capability]:
                eff = datetime.fromisoformat(policy.effective_at)
                if eff <= as_of_dt:
                    sup = datetime.fromisoformat(policy.superseded_at) if policy.superseded_at else None
                    if sup is None or sup > as_of_dt:
                        return {"decision": ControlDecision.PERMITTED, "policy": policy.to_dict()}
        else:
            # Return latest active (non-superseded) policy
            latest = self._policies[capability][0]
            return {"decision": ControlDecision.PERMITTED, "policy": latest.to_dict()}

        return {
            "decision": ControlDecision.POLICY_AMBIGUOUS,
            "capability": capability,
            "reasons": ["no_effective_policy_found"],
        }

    # ------------------------------------------------------------------
    # Eligibility governance
    # ------------------------------------------------------------------
    def check_eligibility(self, capability: str, provider: str, model: str,
                          cost_class: str = "free", data_sensitivity: str = "public",
                          is_fallback: bool = False, is_cross_provider: bool = False,
                          is_substitution: bool = False,
                          as_of: Optional[str] = None) -> dict:
        """Check whether a provider/model combination is eligible."""
        # Resolve policy
        policy_result = self.resolve_policy(capability, as_of)
        if policy_result["decision"] != ControlDecision.PERMITTED:
            return policy_result

        policy_data = policy_result["policy"]
        evidence = {
            "capability": capability,
            "provider": provider,
            "model": model,
            "cost_class": cost_class,
            "data_sensitivity": data_sensitivity,
            "policy_id": policy_data["policy_id"],
            "policy_version": policy_data["version"],
        }

        # Provider prohibition
        if provider in policy_data.get("forbidden_providers", []):
            return {"decision": ControlDecision.PROVIDER_PROHIBITED, "reasons": [f"provider {provider} prohibited"],
                    "evidence": evidence}

        # Model prohibition
        if model in policy_data.get("forbidden_models", []):
            return {"decision": ControlDecision.MODEL_PROHIBITED, "reasons": [f"model {model} prohibited"],
                    "evidence": evidence}

        # Provider permission (if list exists, must be in it)
        permitted_providers = policy_data.get("permitted_providers", [])
        if permitted_providers and provider not in permitted_providers:
            return {"decision": ControlDecision.PROVIDER_PROHIBITED,
                    "reasons": [f"provider {provider} not in permitted list"], "evidence": evidence}

        # Model permission (if list exists, must be in it)
        permitted_models = policy_data.get("permitted_models", [])
        if permitted_models and model not in permitted_models:
            return {"decision": ControlDecision.MODEL_PROHIBITED,
                    "reasons": [f"model {model} not in permitted list"], "evidence": evidence}

        # Paid inference gate
        if cost_class != "free" and not policy_data.get("paid_inference_allowed", False):
            return {"decision": ControlDecision.PAID_INFERENCE_DENIED,
                    "reasons": ["paid_inference_not_allowed_by_policy"], "evidence": evidence}

        # Data sensitivity
        if data_sensitivity != "public" and data_sensitivity != policy_data.get("data_sensitivity_ceiling", "public"):
            return {"decision": ControlDecision.SENSITIVITY_DENIED,
                    "reasons": [f"data sensitivity {data_sensitivity} exceeds ceiling"], "evidence": evidence}

        # Fallback governance
        if is_fallback and not policy_data.get("fallback_allowed", False):
            return {"decision": ControlDecision.FALLBACK_DENIED,
                    "reasons": ["fallback_not_allowed_by_policy"], "evidence": evidence}

        # Cross-provider fallback
        if is_cross_provider and not policy_data.get("cross_provider_fallback_allowed", False):
            return {"decision": ControlDecision.CROSS_PROVIDER_FALLBACK_DENIED,
                    "reasons": ["cross_provider_fallback_not_allowed"], "evidence": evidence}

        # Substitution
        if is_substitution and not policy_data.get("model_substitution_allowed", False):
            return {"decision": ControlDecision.SUBSTITUTION_DENIED,
                    "reasons": ["model_substitution_not_allowed_by_policy"], "evidence": evidence}

        # All checks passed
        return {"decision": ControlDecision.PERMITTED, "evidence": evidence}

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------
    def inspect_policy(self, capability: str) -> dict:
        """Return the current active policy for a capability."""
        result = self.resolve_policy(capability)
        if result["decision"] == ControlDecision.PERMITTED:
            return result["policy"]
        return {"error": result["decision"], "capability": capability}

    def list_policies(self) -> dict:
        """List all registered policies."""
        return {
            "capabilities": list(self._policies.keys()),
            "policy_count": sum(len(v) for v in self._policies.values()),
        }

    # ------------------------------------------------------------------
    # Default safe policies
    # ------------------------------------------------------------------
    def seed_default_policies(self) -> None:
        """Seed minimum safe policies for deterministic tests."""
        if "general" not in self._policies:
            self.register_policy(InferenceControlPolicy(
                policy_id="default-general",
                version=1,
                capability="general",
                permitted_providers=["fake_provider"],
                permitted_models=["fake_model"],
                paid_inference_allowed=False,
                fallback_allowed=False,
                cross_provider_fallback_allowed=False,
                model_substitution_allowed=False,
                max_cost_class="free",
                data_sensitivity_ceiling="public",
                provenance="default-test-fixture",
            ))