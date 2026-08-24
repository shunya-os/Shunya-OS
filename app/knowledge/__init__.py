"""
SHUNYA — Internal-First Knowledge Resolution (Phase 11, computation-only)
"""
import hashlib, json
from datetime import datetime, timezone
from typing import Optional

# Resolution categories
class ResCat:
    INTERNAL_ONLY = "internal_only"
    INTERNAL_PLUS_EXTERNAL_REQUIRED = "internal_plus_external_required"
    EXTERNAL_REQUIRED = "external_required"
    INSUFFICIENT_AND_EXTERNAL_UNAVAILABLE = "insufficient_and_external_unavailable"
    BLOCKED_OR_REVIEW_REQUIRED = "blocked_or_review_required"
    UNKNOWN = "unknown"

# Freshness levels
class FreshnessLevel:
    STABLE = "stable"
    TIME_SENSITIVE = "time_sensitive"
    HIGH_FRESHNESS = "high_freshness"

# Freshness-sensitive topics (registry)
FRESHNESS_SENSITIVE_TOPICS = {
    "entry_rules", "visa_rules", "travel_advisory", "price", "availability",
    "schedule", "disruption", "weather", "live_status", "news", "regulation", "policy",
}

# Stable company-internal question patterns
STABLE_INTERNAL_TOPICS = {
    "approved_margin", "booking_state", "customer_preference", "payment_state",
    "supplier_response", "document_state", "commitment", "decision",
}


class KnowledgeSufficiencyEvaluator:
    """Deterministic evaluator for whether internal knowledge is sufficient."""

    def evaluate(self, workspace_context: dict, request: dict,
                 basis_states: Optional[dict] = None) -> dict:
        purpose = request.get("purpose_code", "general")
        topics = set(request.get("knowledge_topics", []))
        wc_included = {i.get("type") for i in workspace_context.get("included", [])}
        phase4 = request.get("_phase4", {})
        bs = basis_states or {}

        missing = []
        if phase4.get("ineligible_basis"):
            missing.append("ineligible_basis_blocked")
        if phase4.get("system_deny"):
            return {"sufficient": False, "partial": False,
                    "missing_dimensions": ["system_deny"],
                    "total_requested": len(topics), "covered": 0,
                    "reason_code": "basis_blocked_by_phase_4"}

        if topics:
            for t in topics:
                if t in STABLE_INTERNAL_TOPICS:
                    has_basis = self._has_basis_for_topic(t, wc_included, bs)
                    if has_basis is False and not phase4.get("ineligible_basis"):
                        missing.append(t)
                    elif has_basis == "contradicted":
                        missing.append(f"{t}_contradicted")
                    elif has_basis == "ambiguous":
                        missing.append(f"{t}_ambiguous")

        is_sufficient = len(missing) == 0
        partial = len(missing) < len(topics) if topics else False
        return {
            "sufficient": is_sufficient,
            "partial": partial and not is_sufficient,
            "missing_dimensions": missing,
            "total_requested": len(topics),
            "covered": len(topics) - len([m for m in missing if not m.endswith("_contradicted") and not m.endswith("_ambiguous")]),
            "reason_code": "all_dimensions_covered" if is_sufficient else "missing_dimensions",
        }

    def _has_basis_for_topic(self, topic, wc_included, basis_states):
        """Check if topic has basis, returning True/False or 'contradicted'/'ambiguous'."""
        base = self._base_topic(topic)
        state = basis_states.get(base, "active")
        if state == "revoked" or state == "invalidated" or state == "superseded":
            return False
        if state == "contradicted":
            return "contradicted"
        if state == "ambiguous":
            return "ambiguous"
        if base == "approved_margin" and "runtime_position" not in wc_included:
            return False
        if base == "supplier_response" and "conversation" not in wc_included:
            return False
        if base == "booking_state" and "conversation" not in wc_included and "document_record" not in wc_included:
            return False
        if base == "customer_preference" and "memory_record" not in wc_included and "human_context_item" not in wc_included:
            return False
        if base == "payment_state" and "evidence_link" not in wc_included:
            return False
        if base == "document_state" and "document_record" not in wc_included:
            return False
        if base == "commitment" and "relationship" not in wc_included:
            return False
        if base == "decision" and "evidence_link" not in wc_included:
            return False
        return True

    @staticmethod
    def _base_topic(topic):
        return topic.replace("_contradicted", "").replace("_ambiguous", "")


class FreshnessRequirementEvaluator:
    """Deterministic evaluator for freshness requirements."""

    def evaluate(self, request: dict) -> dict:
        purpose = request.get("purpose_code", "general")
        topics = set(request.get("knowledge_topics", []))
        query_text = (request.get("query_text") or "").lower()
        as_of = request.get("as_of")

        # Check for freshness-sensitive words
        freshness_words = {"current", "today", "latest", "now", "live", "real-time", "fresh", "recent", "latest"}
        has_freshness_word = any(w in query_text for w in freshness_words)
        has_freshness_topic = bool(topics & FRESHNESS_SENSITIVE_TOPICS)

        # Historical as_of preserves historical context
        if as_of and as_of < datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0):
            return {
                "freshness_required": False,
                "level": FreshnessLevel.STABLE,
                "reason_code": "historical_as_of",
                "as_of": as_of.isoformat() if isinstance(as_of, datetime) else str(as_of),
            }

        if has_freshness_word or has_freshness_topic:
            return {
                "freshness_required": True,
                "level": FreshnessLevel.HIGH_FRESHNESS if has_freshness_word else FreshnessLevel.TIME_SENSITIVE,
                "reason_code": "freshness_word" if has_freshness_word else "freshness_topic",
                "as_of": None,
            }

        return {
            "freshness_required": False,
            "level": FreshnessLevel.STABLE,
            "reason_code": "stable_question",
            "as_of": None,
        }


class KnowledgeResolutionService:
    """Computation-only knowledge resolution. Consumes Phase 10 WC, produces resolution decisions."""

    def __init__(self, sufficiency_evaluator=None, freshness_evaluator=None,
                 phase10_context=None, phase8_runtime=None, phase4_service=None):
        self._sufficiency = sufficiency_evaluator or KnowledgeSufficiencyEvaluator()
        self._freshness = freshness_evaluator or FreshnessRequirementEvaluator()
        self._wc_svc = phase10_context
        self._rt_svc = phase8_runtime
        self._p4_svc = phase4_service
        self._resolution_version = "11.0"

    def resolve(self, tenant_id: int, actor_id: int,
                purpose_code: str = "general",
                query_text: str = "",
                knowledge_topics: Optional[list] = None,
                workspace_context: Optional[dict] = None,
                current_object_type: str = "",
                current_object_id: Optional[int] = None,
                subject_id: Optional[int] = None,
                as_of: Optional[datetime] = None) -> dict:
        topics = knowledge_topics or []
        wc = workspace_context or {}

        # Phase 4 gate
        p4_check = self._p4_svc.check_eligibility(purpose_code) if self._p4_svc else {"eligible": True}
        phase4 = {"eligible": p4_check.get("eligible", True)}
        if not p4_check.get("eligible", True):
            return self._result(ResCat.BLOCKED_OR_REVIEW_REQUIRED, wc, topics, [], as_of,
                                "purpose_blocked", "blocked_by_phase_4")

        # Build request with Phase 4 state
        request = {
            "purpose_code": purpose_code, "query_text": query_text,
            "knowledge_topics": topics, "as_of": as_of,
            "tenant_id": tenant_id, "actor_id": actor_id,
            "current_object_type": current_object_type, "current_object_id": current_object_id,
            "subject_id": subject_id,
            "_phase4": phase4,
        }

        # Determine basis states from WC content
        basis_states = {}
        for item in wc.get("included", []):
            i_type = item.get("type", "")
            i_state = item.get("state", "active")
            if i_type == "runtime_position":
                for t in topics:
                    b = KnowledgeSufficiencyEvaluator._base_topic(t)
                    if b not in basis_states:
                        basis_states[b] = i_state
            if i_type == "memory_record":
                for t in topics:
                    b = KnowledgeSufficiencyEvaluator._base_topic(t)
                    if b == "customer_preference":
                        basis_states.setdefault(b, i_state)
            if i_type == "evidence_link":
                for t in topics:
                    b = KnowledgeSufficiencyEvaluator._base_topic(t)
                    if b in ("payment_state", "decision"):
                        basis_states.setdefault(b, i_state)

        # Evaluate sufficiency
        suff = self._sufficiency.evaluate(wc, request, basis_states=basis_states)

        # Evaluate freshness
        fresh = self._freshness.evaluate(request)

        # Determine resolution category
        if suff["sufficient"] and not fresh["freshness_required"]:
            cat = ResCat.INTERNAL_ONLY
        elif suff["sufficient"] and fresh["freshness_required"]:
            cat = ResCat.INTERNAL_PLUS_EXTERNAL_REQUIRED
        elif not suff["sufficient"] and fresh["freshness_required"]:
            cat = ResCat.EXTERNAL_REQUIRED
        elif not suff["sufficient"]:
            cat = ResCat.INSUFFICIENT_AND_EXTERNAL_UNAVAILABLE
        else:
            cat = ResCat.UNKNOWN

        # Build external requirement
        ext_req = None
        if cat in (ResCat.EXTERNAL_REQUIRED, ResCat.INTERNAL_PLUS_EXTERNAL_REQUIRED):
            ext_req = self._build_external_requirement(topics, fresh, suff, tenant_id)

        return self._result(cat, wc, topics, suff["missing_dimensions"], as_of,
                            suff["reason_code"], fresh["reason_code"], ext_req, suff, fresh)

    def _result(self, category, wc, topics, missing, as_of, suff_reason, fresh_reason,
                ext_req=None, suff=None, fresh=None):
        return {
            "resolution_category": category,
            "sufficiency": {"sufficient": suff["sufficient"] if suff else False,
                            "partial": suff["partial"] if suff else False,
                            "missing_dimensions": suff["missing_dimensions"] if suff else [],
                            "reason_code": suff["reason_code"] if suff else ""} if suff else {},
            "freshness": {"required": fresh["freshness_required"] if fresh else False,
                          "level": fresh["level"] if fresh else "stable",
                          "reason_code": fresh["reason_code"] if fresh else ""} if fresh else {},
            "external_requirement": ext_req,
            "context_fingerprint": wc.get("fingerprint", ""),
            "policy_version": self._resolution_version,
            "as_of": as_of.isoformat() if isinstance(as_of, datetime) else None,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _build_external_requirement(self, topics, fresh, suff, tenant_id):
        """Build privacy-safe external requirement descriptors."""
        desc = []
        for t in topics:
            # Only include world-knowledge-safe topics, never private identifiers
            if t in FRESHNESS_SENSITIVE_TOPICS or t in STABLE_INTERNAL_TOPICS:
                desc.append(t)
        return {
            "topics": desc,
            "freshness_level": fresh.get("level"),
            "reason_code": fresh.get("reason_code"),
            "missing_dimensions": suff.get("missing_dimensions", []),
            "safety_note": "No private customer or tenant identifiers included",
        }

    def inspect(self, result: dict) -> dict:
        return {
            "resolution_category": result.get("resolution_category"),
            "sufficient": result.get("sufficiency", {}).get("sufficient"),
            "freshness_required": result.get("freshness", {}).get("required"),
            "missing_dimensions": result.get("sufficiency", {}).get("missing_dimensions"),
            "external_requirement": result.get("external_requirement"),
            "policy_version": result.get("policy_version"),
        }

    def explain_sufficiency(self, result: dict) -> dict:
        return {"missing_dimensions": result.get("sufficiency", {}).get("missing_dimensions"),
                "reason_code": result.get("sufficiency", {}).get("reason_code")}

    def explain_freshness(self, result: dict) -> dict:
        return {"required": result.get("freshness", {}).get("required"),
                "level": result.get("freshness", {}).get("level"),
                "reason_code": result.get("freshness", {}).get("reason_code")}

    def explain_resolution(self, result: dict) -> dict:
        return {"category": result.get("resolution_category"),
                "sufficiency": self.explain_sufficiency(result),
                "freshness": self.explain_freshness(result)}