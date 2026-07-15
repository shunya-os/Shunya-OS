"""
SHUNYA — Relevance / Attention (Phase 13, computation-only)
"""
from datetime import datetime
from typing import Optional

# Attention categories
class Attn:
    NOT_RELEVANT = "not_relevant"
    RELEVANT = "relevant"
    ATTENTION_WORTHY = "attention_worthy"
    IMMEDIATE_ATTENTION = "immediate_attention"

# Precedence weights
_PRECEDENCE = {
    Attn.IMMEDIATE_ATTENTION: 5,
    Attn.ATTENTION_WORTHY: 4,
    Attn.RELEVANT: 3,
    Attn.NOT_RELEVANT: 2,
    "insufficient_evidence": 1,
    "failed": 0,
}


class RelevanceService:
    """Deterministic, tenant-isolated attention computation.

    Phase 13 answers: 'Does this matter here and now, and why?'
    It does NOT deliver notifications, create tasks, or execute actions.
    """

    def __init__(self, phase4_service=None, phase10_service=None,
                 phase11_service=None, phase12_service=None, phase12a_service=None):
        self._p4 = phase4_service
        self._p10 = phase10_service
        self._p11 = phase11_service
        self._p12 = phase12_service
        self._p12a = phase12a_service
        self._version = "13.1"

    # ------------------------------------------------------------------
    # Core evaluation
    # ------------------------------------------------------------------
    def evaluate(self, context: dict, signal: dict,
                 tenant_id: Optional[int] = None,
                 principal_id: Optional[str] = None) -> dict:
        """Evaluate whether a signal matters in the given context.

        Args:
            context: Workspace context (from Phase 10 or similar)
            signal: The signal to evaluate (watch observation, world intel result, etc.)
            tenant_id: Tenant for isolation
            principal_id: Machine principal for attribution

        Returns:
            Dict with attention_category, reasons, evidence, precedence
        """
        reasons = []
        evidence = []
        precedence = 0

        # Phase 4 current-use revalidation
        if self._p4:
            p4 = self._p4.check_eligibility(signal.get("purpose_code", "relevance"))
            if not p4.get("eligible", True):
                return self._result(
                    Attn.NOT_RELEVANT,
                    ["blocked_by_current_use"],
                    {"reason": p4.get("reason", "denied")},
                    precedence=0,
                    principal_id=principal_id,
                    tenant_id=tenant_id,
                )

        # Tenant isolation
        sig_tenant = signal.get("tenant_id")
        ctx_tenant = context.get("tenant_id") if isinstance(context, dict) else None
        if sig_tenant is not None and ctx_tenant is not None and sig_tenant != ctx_tenant:
            return self._result(
                Attn.NOT_RELEVANT,
                ["tenant_mismatch"],
                {},
                precedence=0,
                principal_id=principal_id,
                tenant_id=tenant_id,
            )

        # Evaluate each dimension
        results = []
        dims = [
            ("workspace_relevance", self._eval_workspace_relevance, 3),
            ("human_role_relevance", self._eval_human_role_relevance, 3),
            ("business_tenant_relevance", self._eval_business_relevance, 2),
            ("relationship_relevance", self._eval_relationship_relevance, 2),
            ("temporal_relevance", self._eval_temporal_relevance, 3),
            ("consequence_materiality", self._eval_consequence_materiality, 4),
            ("decision_proximity", self._eval_decision_proximity, 4),
            ("user_interest", self._eval_user_interest, 5),
        ]

        for name, fn, weight in dims:
            try:
                r = fn(context, signal)
                results.append(r)
                weight = r.get("weight", weight)
                if r.get("contributing", False):
                    reasons.append(r["reason"])
                    for e in r.get("evidence", []):
                        evidence.append(e)
                    precedence += weight
            except Exception:
                reasons.append(f"{name}: evaluation_failed")
                precedence += 0

        # Determine final category
        category = self._classify(precedence, results, context, signal)

        return self._result(
            category,
            reasons,
            evidence,
            precedence=precedence,
            principal_id=principal_id,
            tenant_id=tenant_id,
        )

    # ------------------------------------------------------------------
    # Dimension evaluators
    # ------------------------------------------------------------------
    def _eval_workspace_relevance(self, context: dict, signal: dict) -> dict:
        """Does the signal relate to the current workspace/object?"""
        workspace_topics = set(context.get("topics", [])) if isinstance(context, dict) else set()
        signal_topics = set(signal.get("topics", [])) if isinstance(signal, dict) else set()
        if not workspace_topics or not signal_topics:
            return {"contributing": False, "reason": "workspace_relevance: no_topics", "weight": 0}
        overlap = workspace_topics & signal_topics
        if overlap:
            return {"contributing": True, "reason": f"workspace_relevance: topics_in_scope {overlap}",
                    "evidence": list(overlap), "weight": 3}
        return {"contributing": False, "reason": "workspace_relevance: no_overlap", "weight": 0}

    def _eval_human_role_relevance(self, context: dict, signal: dict) -> dict:
        """Does the signal matter to the human/role?"""
        roles = set(context.get("roles", [])) if isinstance(context, dict) else set()
        sig_roles = set(signal.get("relevant_roles", [])) if isinstance(signal, dict) else set()
        if not roles or not sig_roles:
            return {"contributing": False, "reason": "human_role_relevance: no_roles", "weight": 0}
        match = roles & sig_roles
        if match:
            return {"contributing": True, "reason": f"human_role_relevance: role_match {match}",
                    "evidence": list(match), "weight": 3}
        return {"contributing": False, "reason": "human_role_relevance: no_match", "weight": 0}

    def _eval_business_relevance(self, context: dict, signal: dict) -> dict:
        """Does the signal matter to the business/tenant?"""
        biz_topics = set(context.get("business_topics", [])) if isinstance(context, dict) else set()
        sig_biz = set(signal.get("business_topics", [])) if isinstance(signal, dict) else set()
        if not biz_topics or not sig_biz:
            return {"contributing": False, "reason": "business_relevance: no_topics", "weight": 0}
        match = biz_topics & sig_biz
        if match:
            return {"contributing": True, "reason": f"business_relevance: match {match}",
                    "evidence": list(match), "weight": 2}
        return {"contributing": False, "reason": "business_relevance: no_match", "weight": 0}

    def _eval_relationship_relevance(self, context: dict, signal: dict) -> dict:
        """Does the signal relate to a known relationship?"""
        rels = set(context.get("relationships", [])) if isinstance(context, dict) else set()
        sig_rels = set(signal.get("related_entities", [])) if isinstance(signal, dict) else set()
        if not rels or not sig_rels:
            return {"contributing": False, "reason": "relationship_relevance: no_relations", "weight": 0}
        match = rels & sig_rels
        if match:
            return {"contributing": True, "reason": f"relationship_relevance: entity_match {match}",
                    "evidence": list(match), "weight": 2}
        return {"contributing": False, "reason": "relationship_relevance: no_match", "weight": 0}

    def _eval_temporal_relevance(self, context: dict, signal: dict) -> dict:
        """Is the signal timely?"""
        now = datetime.utcnow()
        signal_time = signal.get("observed_at")
        if signal_time is None:
            return {"contributing": False, "reason": "temporal_relevance: no_timestamp", "weight": 0}
        try:
            sig_dt = datetime.fromisoformat(signal_time) if isinstance(signal_time, str) else signal_time
            delta_hours = (now - sig_dt).total_seconds() / 3600
            if delta_hours < 1:
                return {"contributing": True, "reason": "temporal_relevance: within_1h",
                        "evidence": [f"delta_hours={delta_hours:.1f}"], "weight": 3}
            elif delta_hours < 24:
                return {"contributing": True, "reason": "temporal_relevance: within_24h",
                        "evidence": [f"delta_hours={delta_hours:.1f}"], "weight": 2}
            elif delta_hours < 168:
                return {"contributing": False, "reason": "temporal_relevance: within_week", "weight": 1}
            else:
                return {"contributing": False, "reason": "temporal_relevance: stale", "weight": 0}
        except (ValueError, TypeError):
            return {"contributing": False, "reason": "temporal_relevance: parse_error", "weight": 0}

    def _eval_consequence_materiality(self, context: dict, signal: dict) -> dict:
        """Does the signal have material consequence?"""
        material = signal.get("material_change", signal.get("change"))
        if material in ("material_change", "conflict_changed", "coverage_changed"):
            return {"contributing": True, "reason": f"consequence: {material}",
                    "evidence": [material], "weight": 4}
        if material and "changed" in str(material):
            return {"contributing": True, "reason": f"consequence: {material}",
                    "evidence": [material], "weight": 3}
        return {"contributing": False, "reason": "consequence: no_material_change", "weight": 0}

    def _eval_decision_proximity(self, context: dict, signal: dict) -> dict:
        """Is there an active decision/commitment the signal affects?"""
        decisions = set(context.get("active_decisions", [])) if isinstance(context, dict) else set()
        sig_topics = set(signal.get("topics", [])) if isinstance(signal, dict) else set()
        if not decisions or not sig_topics:
            return {"contributing": False, "reason": "decision_proximity: no_decisions", "weight": 0}
        match = decisions & sig_topics
        if match:
            return {"contributing": True, "reason": f"decision_proximity: affects {match}",
                    "evidence": list(match), "weight": 4}
        return {"contributing": False, "reason": "decision_proximity: no_match", "weight": 0}

    def _eval_user_interest(self, context: dict, signal: dict) -> dict:
        """Has the user explicitly expressed interest?"""
        interests = set(context.get("user_interests", [])) if isinstance(context, dict) else set()
        sig_topics = set(signal.get("topics", [])) if isinstance(signal, dict) else set()
        if not interests or not sig_topics:
            return {"contributing": False, "reason": "user_interest: no_interests", "weight": 0}
        match = interests & sig_topics
        if match:
            return {"contributing": True, "reason": f"user_interest: explicit {match}",
                    "evidence": list(match), "weight": 5}
        return {"contributing": False, "reason": "user_interest: no_match", "weight": 0}

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    def _classify(self, precedence: int, results: list, context: dict, signal: dict) -> str:
        """Classify into attention category based on precedence and signal state."""
        # Insufficient evidence
        if not results:
            return Attn.NOT_RELEVANT

        # Stale/insufficient evidence
        signal_state = signal.get("state", "") if isinstance(signal, dict) else ""
        if signal_state in ("stale_only", "no_results", "failed"):
            # A failed computation never means "does not matter" — note it
            return Attn.RELEVANT  # It matters that it failed

        # Conflicting signal
        if signal_state == "conflicted":
            return Attn.ATTENTION_WORTHY

        # Precedence-based classification
        if precedence >= 16:
            return Attn.IMMEDIATE_ATTENTION
        elif precedence >= 10:
            return Attn.ATTENTION_WORTHY
        elif precedence >= 4:
            return Attn.RELEVANT
        else:
            return Attn.NOT_RELEVANT

    # ------------------------------------------------------------------
    # Result builder
    # ------------------------------------------------------------------
    def _result(self, category: str, reasons: list, evidence: list,
                precedence: int = 0, principal_id: str = None,
                tenant_id: int = None) -> dict:
        return {
            "attention_category": category,
            "reasons": reasons,
            "evidence": evidence,
            "precedence_score": precedence,
            "computed_at": datetime.utcnow().isoformat(),
            "version": self._version,
            "principal_id": principal_id,
            "tenant_id": tenant_id,
        }

    # ------------------------------------------------------------------
    # Inspect / Explain
    # ------------------------------------------------------------------
    def inspect(self, result: dict) -> dict:
        """Return a safe summary of an attention evaluation result."""
        return {
            "attention_category": result.get("attention_category"),
            "reasons": result.get("reasons", [])[:5],
            "precedence_score": result.get("precedence_score"),
            "computed_at": result.get("computed_at"),
        }

    def explain(self, result: dict) -> dict:
        """Explain the reasoning behind an attention evaluation."""
        return {
            "attention_category": result.get("attention_category"),
            "reasons": result.get("reasons", []),
            "evidence": result.get("evidence", []),
            "precedence_score": result.get("precedence_score"),
            "why": self._generate_explanation(result),
        }

    def _generate_explanation(self, result: dict) -> str:
        category = result.get("attention_category", "unknown")
        reasons = result.get("reasons", [])
        if category == "immediate_attention":
            return f"Immediate attention required because: {'; '.join(reasons[:3])}"
        elif category == "attention_worthy":
            return f"Attention worthy because: {'; '.join(reasons[:3])}"
        elif category == "relevant":
            return f"Relevant because: {'; '.join(reasons[:3])}"
        else:
            return f"Not relevant: {'; '.join(reasons[:3])}" if reasons else "Not relevant: no contributing factors"