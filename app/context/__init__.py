"""
SHUNYA — Context Fusion + WORKSPACE_CONTEXT (Phase 10, computation-only)
"""
import hashlib, json
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Purpose registry
# ---------------------------------------------------------------------------
REGISTERED_PURPOSES = {"personal_scheduling", "sales_support", "document_analysis", "relationship_analysis"}

# ---------------------------------------------------------------------------
# Reason codes
# ---------------------------------------------------------------------------
INC_REASON = type("IncReason", (), {
    "DIRECT_OBJECT": "direct_object", "SCOPE_MATCH": "scope_match",
    "RELATED_ENTITY": "related_entity", "CURRENT_EVIDENCE_BASIS": "current_evidence_basis",
    "CONVERSATION_WINDOW": "conversation_window",
})()

EXC_REASON = type("ExcReason", (), {
    "FOREIGN_TENANT": "foreign_tenant", "PURPOSE_RESTRICTED": "purpose_restricted",
    "SYSTEM_DENY": "system_deny", "REVIEW_REQUIRED": "review_required",
    "RESTRICTED_SCOPE": "restricted_scope", "INELIGIBLE_STATE": "ineligible_state",
    "OUT_OF_SCOPE": "out_of_scope", "WRONG_SUBJECT": "wrong_subject",
    "WRONG_OBJECT": "wrong_object", "SUPERSEDED": "superseded",
    "REVOKED": "revoked", "INVALIDATED": "invalidated", "STALE_EXCLUDED": "stale_excluded",
    "DUPLICATE_CANONICAL": "duplicate_canonical", "DUPLICATE_LINEAGE": "duplicate_lineage",
    "SECTION_BUDGET": "section_budget", "TOTAL_BUDGET": "total_budget",
    "UNSUPPORTED_TYPE": "unsupported_type",
})()

# ---------------------------------------------------------------------------
# Source Provider Registry
# ---------------------------------------------------------------------------
SOURCE_DOMAINS = ["identity", "relationship", "conversation", "human_context",
                  "memory", "evidence_position", "document"]

SOURCE_PROVIDERS = {
    "identity": {"name": "identity_provider", "version": "1.0", "scopes": ["person", "client_user"],
                 "contract": "Person/ClientUser references with minimum attributes"},
    "relationship": {"name": "relationship_provider", "version": "1.0", "scopes": ["relationship", "supplier"],
                     "contract": "Phase 2 Relationship records with type, direction, state"},
    "conversation": {"name": "conversation_provider", "version": "1.0", "scopes": ["message", "conversation"],
                     "contract": "Bounded conversation window with message identity/sender/timestamp"},
    "human_context": {"name": "human_context_provider", "version": "1.0", "scopes": ["human_context_item"],
                      "contract": "Eligible HumanContextItem with scope, state, provenance"},
    "memory": {"name": "memory_provider", "version": "1.0", "scopes": ["memory_record"],
               "contract": "Eligible MemoryRecord with type, scope, supersession"},
    "evidence_position": {"name": "evidence_provider", "version": "1.0", "scopes": ["evidence_link", "runtime_position"],
                          "contract": "Phase 7 EvidenceLink + Phase 8 EvidenceRuntimePosition"},
    "document": {"name": "document_provider", "version": "1.0", "scopes": ["document_record", "document_section", "extracted_field"],
                 "contract": "Phase 7A DocumentRecord/section/field with location provenance"},
}


class ContextFusionService:
    def __init__(self, phase7_evidence=None, phase8_runtime=None, phase9_llm=None,
                 phase4_service=None, phase6_memory=None, phase5_human_context=None):
        self._ev_svc = phase7_evidence
        self._rt_svc = phase8_runtime
        self._llm_svc = phase9_llm
        self._p4_svc = phase4_service
        self._mem_svc = phase6_memory
        self._hc_svc = phase5_human_context
        self._fusion_version = "10.1"
        self._providers = SOURCE_PROVIDERS

    # ------------------------------------------------------------------
    # Source provider registry access
    # ------------------------------------------------------------------
    def get_provider(self, domain: str) -> Optional[dict]:
        return self._providers.get(domain)

    def list_providers(self) -> list[dict]:
        return [{"domain": d, **v} for d, v in self._providers.items()]

    # ------------------------------------------------------------------
    # Phase 4 current-use gate
    # ------------------------------------------------------------------
    def _check_eligibility(self, purpose_code: str, restriction: Optional[str] = None) -> dict:
        """Simulated Phase 4 current-use gate."""
        # In production, this calls Phase 4 PrivacyService.check_current_use()
        # For testing, we use the restriction parameter
        if restriction == "system_deny":
            return {"eligible": False, "reason": EXC_REASON.SYSTEM_DENY}
        if restriction == "ineligible":
            return {"eligible": False, "reason": EXC_REASON.INELIGIBLE_STATE}
        if restriction == "review_required":
            return {"eligible": False, "reason": EXC_REASON.REVIEW_REQUIRED}
        if restriction == "restricted_scope":
            return {"eligible": False, "reason": EXC_REASON.RESTRICTED_SCOPE}
        if restriction == "no_marketing" and purpose_code == "marketing":
            return {"eligible": False, "reason": EXC_REASON.PURPOSE_RESTRICTED}
        return {"eligible": True, "reason": None}

    # ------------------------------------------------------------------
    # Source integration methods
    # ------------------------------------------------------------------
    def _integrate_identity(self, tenant_id, actor_id, subject_id, purpose) -> list[dict]:
        items = []
        items.append({"type": "person", "id": actor_id, "role": "actor",
                      "reason": INC_REASON.DIRECT_OBJECT, "provider": "identity_provider"})
        if subject_id and subject_id != actor_id:
            items.append({"type": "person", "id": subject_id, "role": "subject",
                          "reason": INC_REASON.DIRECT_OBJECT, "provider": "identity_provider"})
        return items

    def _integrate_relationships(self, tenant_id, actor_id, subject_id, purpose) -> list[dict]:
        items = []
        if subject_id:
            items.append({"type": "relationship", "from": actor_id, "to": subject_id,
                          "direction": "actor_to_subject", "reason": INC_REASON.SCOPE_MATCH,
                          "provider": "relationship_provider"})
        return items

    def _integrate_conversations(self, tenant_id, actor_id, current_object_type, current_object_id, purpose) -> list[dict]:
        items = []
        if current_object_type == "conversation" and current_object_id:
            items.append({"type": "conversation", "id": current_object_id, "scope": "bounded_window",
                          "reason": INC_REASON.DIRECT_OBJECT, "provider": "conversation_provider"})
        return items

    def _integrate_human_context(self, tenant_id, subject_id, purpose) -> list[dict]:
        items = []
        if self._hc_svc and subject_id:
            try:
                ctx_items = self._hc_svc.get_items_for_person(subject_id, tenant_id=tenant_id)
                for ci in ctx_items:
                    if getattr(ci, "status", "active") == "active" and getattr(ci, "scope", "") != "child":
                        items.append({"type": "human_context_item", "id": ci.id,
                                      "reason": INC_REASON.SCOPE_MATCH, "provider": "human_context_provider"})
            except Exception:
                pass
        return items

    def _integrate_memory(self, tenant_id, subject_id, purpose) -> list[dict]:
        items = []
        if self._mem_svc and subject_id:
            try:
                mems = self._mem_svc.get_memory_for_person(subject_id, tenant_id=tenant_id)
                for m in mems:
                    if getattr(m, "superseded_by_id", None) is None:
                        items.append({"type": "memory_record", "id": m.id,
                                      "reason": INC_REASON.SCOPE_MATCH, "provider": "memory_provider"})
            except Exception:
                pass
        return items

    def _integrate_evidence(self, tenant_id, subject_id, purpose) -> list[dict]:
        items = []
        if self._ev_svc and subject_id:
            try:
                links = self._ev_svc.get_evidence_for_target("person", subject_id, tenant_id=tenant_id)
                for link in links:
                    if link.get("status") == "active":
                        items.append({"type": "evidence_link", "id": link.get("id"),
                                      "reason": INC_REASON.CURRENT_EVIDENCE_BASIS,
                                      "provider": "evidence_provider"})
            except Exception:
                pass
        if self._rt_svc and subject_id:
            try:
                pos = self._rt_svc.resolve_position("person", subject_id, tenant_id=tenant_id)
                items.append({"type": "runtime_position", "category": pos.get("position_category"),
                              "reason": INC_REASON.CURRENT_EVIDENCE_BASIS, "provider": "evidence_provider"})
            except Exception:
                pass
        return items

    def _integrate_documents(self, tenant_id, subject_id, current_object_type, current_object_id, purpose) -> list[dict]:
        items = []
        if current_object_type == "document_record" and current_object_id:
            items.append({"type": "document_record", "id": current_object_id,
                          "reason": INC_REASON.DIRECT_OBJECT, "provider": "document_provider"})
        return items

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
                                 max_items: int = 50,
                                 restrictions: Optional[dict] = None) -> dict:
        if purpose_code not in REGISTERED_PURPOSES:
            return {"error": f"Unknown purpose: {purpose_code}", "fingerprint": ""}

        # Phase 4 current-use check
        p4 = self._check_eligibility(purpose_code, restrictions.get("eligibility") if restrictions else None)
        if not p4["eligible"]:
            return {"error": f"Context blocked by Phase 4: {p4['reason']}", "fingerprint": ""}

        included = []
        excluded = []
        per_section_budget = max_items // 5  # 5 sections max, even distribution
        total_used = 0

        # Build sections from source providers
        sections = {}

        # Identity
        id_items = self._integrate_identity(tenant_id, actor_id, subject_id, purpose_code)
        sections["identity"] = {"provider": "identity_provider", "items": len(id_items)}
        included.extend(id_items)
        total_used += len(id_items)

        # Relationships
        rel_items = self._integrate_relationships(tenant_id, actor_id, subject_id, purpose_code)
        if len(rel_items) <= per_section_budget:
            sections["relationships"] = {"provider": "relationship_provider", "items": len(rel_items)}
            included.extend(rel_items)
        else:
            for item in rel_items[per_section_budget:]:
                excluded.append({**item, "reason": EXC_REASON.SECTION_BUDGET})
            sections["relationships"] = {"provider": "relationship_provider", "items": per_section_budget}
            included.extend(rel_items[:per_section_budget])
        total_used += min(len(rel_items), per_section_budget)

        # Conversations
        conv_items = self._integrate_conversations(tenant_id, actor_id, current_object_type, current_object_id, purpose_code)
        sections["conversations"] = {"provider": "conversation_provider", "items": len(conv_items)}
        included.extend(conv_items)
        total_used += len(conv_items)

        # Human Context
        hc_items = self._integrate_human_context(tenant_id, subject_id, purpose_code)
        if len(hc_items) <= per_section_budget:
            sections["human_context"] = {"provider": "human_context_provider", "items": len(hc_items)}
            included.extend(hc_items)
        else:
            sections["human_context"] = {"provider": "human_context_provider", "items": per_section_budget}
            included.extend(hc_items[:per_section_budget])
            for item in hc_items[per_section_budget:]:
                excluded.append({**item, "reason": EXC_REASON.SECTION_BUDGET})
        total_used += min(len(hc_items), per_section_budget)

        # Memory
        mem_items = self._integrate_memory(tenant_id, subject_id, purpose_code)
        if len(mem_items) <= per_section_budget:
            sections["memory"] = {"provider": "memory_provider", "items": len(mem_items)}
            included.extend(mem_items)
        else:
            sections["memory"] = {"provider": "memory_provider", "items": per_section_budget}
            included.extend(mem_items[:per_section_budget])
            for item in mem_items[per_section_budget:]:
                excluded.append({**item, "reason": EXC_REASON.SECTION_BUDGET})
        total_used += min(len(mem_items), per_section_budget)

        # Evidence
        ev_items = self._integrate_evidence(tenant_id, subject_id, purpose_code)
        sections["evidence"] = {"provider": "evidence_provider", "items": len(ev_items)}
        included.extend(ev_items)
        total_used += len(ev_items)

        # Documents
        doc_items = self._integrate_documents(tenant_id, subject_id, current_object_type, current_object_id, purpose_code)
        sections["documents"] = {"provider": "document_provider", "items": len(doc_items)}
        included.extend(doc_items)
        total_used += len(doc_items)

        # Purpose and policy
        sections["purpose"] = {"code": purpose_code, "items": 1}
        sections["fusion_policy"] = {"version": self._fusion_version}

        result = {
            "tenant_id": tenant_id, "actor_id": actor_id, "operating_context": operating_context,
            "purpose_code": purpose_code, "current_object_type": current_object_type,
            "current_object_id": current_object_id, "subject_id": subject_id,
            "sections": sections, "included": included, "excluded": excluded,
            "total_items": total_used,
            "budget": {"total_max": max_items, "total_used": total_used,
                       "per_section_max": per_section_budget},
            "fingerprint": "", "built_at": datetime.now(timezone.utc).isoformat(),
        }
        result["fingerprint"] = self._compute_fingerprint(result)
        return result

    # ------------------------------------------------------------------
    # Fingerprint (material-context aware)
    # ------------------------------------------------------------------
    def _compute_fingerprint(self, context: dict) -> str:
        # Sort included items by type/id for deterministic order
        included_sorted = sorted(
            [{"t": i.get("type"), "id": i.get("id"),
              "r": i.get("role"), "p": i.get("provider")}
             for i in context.get("included", [])],
            key=lambda x: f"{x['t']}:{x['id']}"
        )
        payload = {
            "tenant": context.get("tenant_id"), "actor": context.get("actor_id"),
            "purpose": context.get("purpose_code"),
            "object_type": context.get("current_object_type"),
            "object_id": context.get("current_object_id"),
            "subject": context.get("subject_id"),
            "fusion_version": self._fusion_version,
            "included": included_sorted,
            "provider_versions": {d: self._providers[d]["version"] for d in SOURCE_DOMAINS},
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:32]

    def compute_context_fingerprint(self, context: dict) -> str:
        return self._compute_fingerprint(context)

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------
    def inspect_context(self, context: dict) -> dict:
        return {
            "tenant_id": context.get("tenant_id"), "purpose": context.get("purpose_code"),
            "sections": list(context.get("sections", {}).keys()),
            "total_items": context.get("total_items"),
            "budget": context.get("budget"), "included_count": len(context.get("included", [])),
            "excluded_count": len(context.get("excluded", [])),
            "fingerprint": context.get("fingerprint"), "built_at": context.get("built_at"),
        }

    def explain_inclusion(self, context: dict, item_type: str, item_id: int) -> dict:
        for item in context.get("included", []):
            if item.get("type") == item_type and item.get("id") == item_id:
                return {"type": item_type, "id": item_id, "reason": item.get("reason"),
                        "provider": item.get("provider"), "included": True}
        return {"type": item_type, "id": item_id, "included": False}

    def explain_exclusion(self, context: dict, candidate_type: str, candidate_id: int,
                          reason: str = "out_of_scope") -> dict:
        if reason == EXC_REASON.FOREIGN_TENANT:
            return {"candidate_type": candidate_type, "excluded": True,
                    "reason": "foreign_tenant", "safe_message": "Item belongs to another tenant."}
        return {"candidate_type": candidate_type, "excluded": True, "reason": reason}