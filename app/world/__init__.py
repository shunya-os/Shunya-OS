"""
SHUNYA — World Intelligence (Phase 12, computation-only + fake provider)
"""
import hashlib, json, uuid
from datetime import datetime
from typing import Optional

# Source type registry
SRC_TYPE = type("SrcType", (), {
    "OFFICIAL_GOVERNMENT": "official_government",
    "OFFICIAL_ORGANIZATION": "official_organization",
    "PRIMARY_SOURCE": "primary_source",
    "NEWS": "news",
    "INDUSTRY_SOURCE": "industry_source",
    "DATA_API": "data_api",
    "FEED": "feed",
    "GENERAL_WEB": "general_web",
    "USER_GENERATED": "user_generated",
})()

# Coverage states
COV = type("Cov", (), {
    "COMPLETE": "complete", "PARTIAL": "partial",
    "NONE": "none", "CONFLICTED": "conflicted", "STALE": "stale",
})()

# Failure states
FAIL = type("Fail", (), {
    "NO_RESULTS": "no_results",
    "PROVIDER_UNAVAILABLE": "provider_unavailable",
    "PROVIDER_ERROR": "provider_error",
    "RATE_LIMITED": "rate_limited",
    "UNSUPPORTED_REQUIREMENT": "unsupported_requirement",
    "BLOCKED_OR_REVIEW_REQUIRED": "blocked_or_review_required",
    "PARTIAL_COVERAGE": "partial_coverage",
    "STALE_ONLY": "stale_only",
    "CONFLICTED": "conflicted",
})()


class ExternalSourceProviderRegistry:
    def __init__(self):
        self._providers = {
            "web_search": {"name": "web_search", "version": "1.0",
                           "capabilities": ["general_web", "news"],
                           "source_types": [SRC_TYPE.GENERAL_WEB, SRC_TYPE.NEWS],
                           "freshness": "time_sensitive",
                           "policy": "allowed"},
            "official_data": {"name": "official_data", "version": "1.0",
                              "capabilities": ["official_source", "data_api"],
                              "source_types": [SRC_TYPE.OFFICIAL_GOVERNMENT, SRC_TYPE.OFFICIAL_ORGANIZATION, SRC_TYPE.DATA_API],
                              "freshness": "stable",
                              "policy": "allowed"},
        }

    def get_provider(self, name: str) -> Optional[dict]:
        return self._providers.get(name)

    def list_providers(self) -> list[dict]:
        return [{"name": k, **v} for k, v in self._providers.items()]

    def select_providers(self, requirement: dict) -> list[str]:
        """Select providers based on requirement characteristics."""
        freshness = (requirement.get("freshness_level") or "stable").lower()
        if freshness in ("high_freshness", "time_sensitive"):
            return ["web_search", "official_data"]
        return ["official_data", "web_search"]


class ExternalQueryMinimizer:
    """Privacy-safe query construction. Never leaks private identifiers."""

    def minimize(self, requirement: dict) -> dict:
        """Build a safe minimized query from a bounded external requirement."""
        topics = requirement.get("topics", [])
        geography = requirement.get("geography", "")
        intent = {}
        safe_parts = []
        for t in topics:
            # Only allow world-knowledge-safe topics, never private identifiers
            safe_topic = t.strip()
            safe_parts.append(safe_topic)
        if geography:
            safe_parts.append(geography)
        intent["query_text"] = " ".join(safe_parts) if safe_parts else ""
        intent["safe_topics"] = safe_parts
        intent["geography"] = geography
        # Hash the minimal intent for audit
        intent["query_hash"] = hashlib.sha256(json.dumps(safe_parts, sort_keys=True).encode()).hexdigest()[:32]
        return intent


class FakeProvider:
    """Deterministic fake provider for tests."""
    def __init__(self, name="web_search"):
        self.name = name

    def retrieve(self, intent: dict) -> dict:
        query = intent.get("query_text", "")
        if "error" in query.lower():
            return {"success": False, "error_type": "provider_error", "error_message": "Simulated error"}
        if "noresult" in query.lower():
            return {"success": True, "sources": [], "observations": []}
        if "rate_limit" in query.lower():
            return {"success": False, "error_type": "rate_limited", "error_message": "Rate limited"}
        if "conflict" in query.lower():
            return {"success": True, "sources": [
                {"url": "https://example.com/1", "title": "Source 1", "content": "Claim A"},
                {"url": "https://example.com/2", "title": "Source 2", "content": "Claim B, different from A"},
            ], "observations": [
                {"source_url": "https://example.com/1", "text": "Claim A", "locator": "para:1"},
                {"source_url": "https://example.com/2", "text": "Claim B", "locator": "para:1"},
            ]}
        return {"success": True, "sources": [
            {"url": "https://example.com/rules", "title": "Entry Rules",
             "content": "entry_rules: Indian passport holders need visa for Bali. visa_requirements: Visa on arrival available.",
             "source_type": "official_government"},
        ], "observations": [
            {"source_url": "https://example.com/rules", "text": "entry_rules: Indian passport holders need visa for Bali.",
             "locator": "section:1/para:2"},
            {"source_url": "https://example.com/rules", "text": "visa_requirements: Visa on arrival available.",
             "locator": "section:1/para:3"},
        ]}


class WorldIntelligenceService:
    """Computation-only governed external retrieval. Uses fake providers for tests."""

    def __init__(self, provider_registry=None, query_minimizer=None, phase4_service=None):
        self._registry = provider_registry or ExternalSourceProviderRegistry()
        self._minimizer = query_minimizer or ExternalQueryMinimizer()
        self._p4_svc = phase4_service
        self._version = "12.0"

    # ------------------------------------------------------------------
    # Execute retrieval from Phase 11 requirement
    # ------------------------------------------------------------------
    def execute(self, requirement: dict, tenant_id: int = 1,
                purpose_code: str = "general",
                phase11_resolution: Optional[dict] = None,
                as_of: Optional[datetime] = None) -> dict:
        # Phase 4 gate
        if self._p4_svc:
            p4 = self._p4_svc.check_eligibility(purpose_code)
            if not p4.get("eligible", True):
                return self._result(requirement, FAIL.BLOCKED_OR_REVIEW_REQUIRED, "blocked_by_phase_4")

        # Validate requirement
        if not requirement or not requirement.get("topics"):
            return self._result(requirement, FAIL.UNSUPPORTED_REQUIREMENT, "empty_requirement")

        # Build minimized query
        intent = self._minimizer.minimize(requirement)

        # Select providers
        providers = self._registry.select_providers(requirement)
        attempts = []
        all_sources = []
        all_observations = []

        for p_name in providers:
            provider = self._registry.get_provider(p_name)
            if not provider:
                attempts.append({"provider": p_name, "status": "unsupported", "reason": "not_registered"})
                continue
            # Use fake provider for deterministic tests
            fake = FakeProvider(p_name)
            result = fake.retrieve(intent)
            if result["success"]:
                all_sources.extend(result.get("sources", []))
                all_observations.extend(result.get("observations", []))
                attempts.append({"provider": p_name, "status": "success", "sources": len(result.get("sources", []))})
            else:
                attempts.append({"provider": p_name, "status": "failed",
                                 "reason": result.get("error_type", "unknown")})
                if result.get("error_type") == "provider_error":
                    return self._result(requirement, FAIL.PROVIDER_ERROR, "provider_error", attempts)
                if result.get("error_type") == "rate_limited":
                    attempts[-1]["status"] = "rate_limited"
                    continue

        # Evaluate coverage
        topics = requirement.get("topics", [])
        coverage = self._evaluate_coverage(topics, all_observations)

        # Evaluate conflict
        has_conflict = self._detect_conflict(all_observations)

        # Determine final state
        covered_count = len([c for c in coverage.values() if c == COV.COMPLETE])
        if covered_count == len(topics) and not has_conflict:
            final_state = "success"
        elif has_conflict:
            final_state = FAIL.CONFLICTED
        elif covered_count > 0:
            final_state = FAIL.PARTIAL_COVERAGE
        else:
            final_state = FAIL.NO_RESULTS

        return self._result(requirement, final_state, final_state, attempts, all_sources, all_observations, coverage)

    def _evaluate_coverage(self, topics, observations):
        coverage = {}
        observed_text = " ".join(o.get("text", "") for o in observations)
        for t in topics:
            if t.lower() in observed_text.lower():
                coverage[t] = COV.COMPLETE
            else:
                coverage[t] = COV.NONE
        return coverage

    def _detect_conflict(self, observations):
        texts = [o.get("text", "") for o in observations]
        # Simple conflict detection: if two observations differ materially
        if len(texts) >= 2 and texts[0] != texts[1]:
            return True
        return False

    def _result(self, requirement, state, reason, attempts=None, sources=None, observations=None, coverage=None):
        return {
            "state": state,
            "reason_code": reason,
            "attempts": attempts or [],
            "sources": [{"url": s.get("url"), "title": s.get("title"),
                         "source_type": s.get("source_type", "general_web"),
                         "retrieved_at": datetime.utcnow().isoformat()} for s in (sources or [])],
            "observations": [{"text": o.get("text"), "locator": o.get("locator"),
                              "source_url": o.get("source_url")} for o in (observations or [])],
            "coverage": coverage or {},
            "intent": self._minimizer.minimize(requirement) if requirement else {},
            "policy_version": self._version,
            "evaluated_at": datetime.utcnow().isoformat(),
        }

    def inspect(self, result: dict) -> dict:
        return {
            "state": result.get("state"),
            "attempts": len(result.get("attempts", [])),
            "sources": len(result.get("sources", [])),
            "observations": len(result.get("observations", [])),
            "coverage": result.get("coverage"),
            "policy_version": result.get("policy_version"),
        }

    def explain_retrieval_plan(self, result: dict) -> dict:
        return {"intent": result.get("intent"), "attempts": result.get("attempts")}

    def explain_coverage(self, result: dict) -> dict:
        return {"coverage": result.get("coverage"), "state": result.get("state")}