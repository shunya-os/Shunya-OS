"""
SHUNYA — Context Fusion + WORKSPACE_CONTEXT (Phase 10, computation-only)
"""
import hashlib, json
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Purpose registry
# ---------------------------------------------------------------------------
REGISTERED_PURPOSES = {"personal_scheduling", "sales_support", "document_analysis", "relationship_analysis"}

# ---------------------------------------------------------------------------
# Inclusion/Exclusion reason codes
# ---------------------------------------------------------------------------
INC_REASON = type("IncReason", (), {
    "DIRECT_OBJECT": "direct_object",
    "SCOPE_MATCH": "scope_match",
    "RELATED_ENTITY": "related_entity",
    "CURRENT_EVIDENCE_BASIS": "current_evidence_basis",
    "CONVERSATION_WINDOW": "conversation_window",
})()

EXC_REASON = type("ExcReason", (), {
    "FOREIGN_TENANT": "foreign_tenant",
    "PURPOSE_RESTRICTED": "purpose_restricted",
    "SYSTEM_DENY": "system_deny",
    "REVIEW_REQUIRED": "review_required",
    "RESTRICTED_SCOPE": "restricted_scope",
    "INELIGIBLE_STATE": "ineligible_state",
    "OUT_OF_SCOPE": "out_of_scope",
    "WRONG_SUBJECT": "wrong_subject",
    "WRONG_OBJECT": "wrong_object",
    "SUPERSEDED": "superseded",
    "REVOKED": "revoked",
    "INVALIDATED": "invalidated",
    "STALE_EXCLUDED": "stale_excluded",
    "DUPLICATE_CANONICAL": "duplicate_canonical",
    "DUPLICATE_LINEAGE": "duplicate_lineage",
    "SECTION_BUDGET": "section_budget",
    "TOTAL_BUDGET": "total_budget",
    "UNSUPPORTED_TYPE": "unsupported_type",
})()

# ---------------------------------------------------------------------------
# Source provider definitions
# ---------------------------------------------------------------------------
SOURCE_DOMAINS = ["identity", "relationship", "conversation", "human_context", "memory", "evidence_position", "document"]


class ContextFusionService:
    """Deterministic computation-only fusion runtime. No persistence, no cache."""

    def __init__(self, phase7_evidence=None, phase8_runtime=None, phase9_llm=None):
        self._ev_svc = phase7_evidence
        self._rt_svc = phase8_runtime
        self._llm_svc = phase9_llm
        self._fusion_version = "10.0"

    # ------------------------------------------------------------------
    # Build workspace context
    # ------------------------------------------------------------------
    def build_workspace_context(self, tenant_id: int, actor_id: int,
                                 purpose_code: str = "personal_scheduling",
                                 operating_context: Optional[int] = None,
                                 current_object_type: str = "",
                                 current_object_id: Optional[int] = None,
                                 subject_id: Optional[int] = None,
                                 as_of: Optional[datetime] = None,
                                 max_items: int = 50) -> dict:
        if purpose_code not in REGISTERED_PURPOSES:
            return {"error": f"Unknown purpose: {purpose_code}", "fingerprint": ""}

        included = []
        excluded = []
        sections = {}

        # Actor information
        sections["actor"] = {"ref": {"type": "person", "id": actor_id}, "items": 1}
        included.append({"type": "actor", "id": actor_id, "reason": INC_REASON.DIRECT_OBJECT})
        if subject_id and subject_id != actor_id:
            sections["subject"] = {"ref": {"type": "person", "id": subject_id}, "items": 1}
            included.append({"type": "subject", "id": subject_id, "reason": INC_REASON.DIRECT_OBJECT})

        # Current object
        if current_object_type and current_object_id:
            sections["current_object"] = {"ref": {"type": current_object_type, "id": current_object_id}, "items": 1}
            included.append({"type": "current_object", "id": current_object_id, "reason": INC_REASON.DIRECT_OBJECT})

        # Purpose info
        sections["purpose"] = {"code": purpose_code, "items": 1}
        sections["fusion_policy"] = {"version": self._fusion_version}

        result = {
            "tenant_id": tenant_id,
            "actor_id": actor_id,
            "operating_context": operating_context,
            "purpose_code": purpose_code,
            "current_object_type": current_object_type,
            "current_object_id": current_object_id,
            "subject_id": subject_id,
            "sections": sections,
            "included": included,
            "excluded": excluded,
            "total_items": sum(s.get("items", 0) for s in sections.values()),
            "budget": {"total_max": max_items, "total_used": sum(s.get("items", 0) for s in sections.values())},
            "fingerprint": "",
            "built_at": datetime.utcnow().isoformat(),
        }
        result["fingerprint"] = self._compute_fingerprint(result)
        return result

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------
    def inspect_context(self, context: dict) -> dict:
        return {
            "tenant_id": context.get("tenant_id"),
            "purpose": context.get("purpose_code"),
            "sections": list(context.get("sections", {}).keys()),
            "total_items": context.get("total_items"),
            "budget": context.get("budget"),
            "included_count": len(context.get("included", [])),
            "excluded_count": len(context.get("excluded", [])),
            "fingerprint": context.get("fingerprint"),
            "built_at": context.get("built_at"),
        }

    def explain_inclusion(self, context: dict, item_type: str, item_id: int) -> dict:
        for item in context.get("included", []):
            if item["type"] == item_type and item["id"] == item_id:
                return {"type": item_type, "id": item_id, "reason": item.get("reason"), "included": True}
        return {"type": item_type, "id": item_id, "included": False}

    def explain_exclusion(self, context: dict, candidate_type: str, candidate_id: int,
                          reason: str = "out_of_scope") -> dict:
        if reason == EXC_REASON.FOREIGN_TENANT:
            return {"candidate_type": candidate_type, "excluded": True,
                    "reason": "foreign_tenant", "safe_message": "Item belongs to another tenant."}
        return {"candidate_type": candidate_type, "excluded": True, "reason": reason}

    # ------------------------------------------------------------------
    # Fingerprint
    # ------------------------------------------------------------------
    def _compute_fingerprint(self, context: dict) -> str:
        payload = {
            "tenant": context.get("tenant_id"),
            "actor": context.get("actor_id"),
            "purpose": context.get("purpose_code"),
            "object_type": context.get("current_object_type"),
            "object_id": context.get("current_object_id"),
            "subject": context.get("subject_id"),
            "fusion_version": self._fusion_version,
            "sections": {k: v.get("items", 0) for k, v in context.get("sections", {}).items()},
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:32]

    def compute_context_fingerprint(self, context: dict) -> str:
        return self._compute_fingerprint(context)