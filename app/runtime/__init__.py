"""
SHUNYA — Evidence Runtime Distinction Service (Phase 8, computation-only)
"""
from datetime import datetime
from typing import Optional


class PositionCategory:
    INTERNAL_DATA = "internal_data"; EXTERNAL_INFORMATION = "external_information"
    MIXED_EVIDENCE = "mixed_evidence"; ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"; UNKNOWN_INSUFFICIENT = "unknown_insufficient"


class OriginClass:
    INTERNAL_TENANT = "internal_tenant"; EXTERNAL_WORLD = "external_world"
    HUMAN_ASSERTION = "human_assertion"; SYSTEM_DERIVATION = "system_derivation"; UNKNOWN = "unknown"


class EvidenceRuntimeService:
    def __init__(self, evidence_service=None):
        self._ev_svc = evidence_service

    def _classify_origin(self, source_reference):
        if source_reference is None:
            return OriginClass.UNKNOWN
        producer = getattr(source_reference, "producer_type", None) or "unknown"
        kind = getattr(source_reference, "source_kind", None) or ""
        if producer in ("system", "system_derivation"):
            return OriginClass.SYSTEM_DERIVATION
        if kind in ("manual_assertion", "import"):
            return OriginClass.INTERNAL_TENANT
        if producer in ("person", "tenant_user"):
            if kind in ("internal_memo", "employee_note", "internal_message"):
                return OriginClass.INTERNAL_TENANT
            return OriginClass.HUMAN_ASSERTION
        if producer in ("external_party", "provider"):
            return OriginClass.EXTERNAL_WORLD
        if kind == "external_message":
            return OriginClass.EXTERNAL_WORLD
        return OriginClass.UNKNOWN

    def resolve_position(self, target_type: str, target_id: int,
                         tenant_id: Optional[int] = None) -> dict:
        if self._ev_svc is None:
            return self._default_position()
        evidence = self._ev_svc.resolve_evidence(target_type, target_id, tenant_id)
        links = self._ev_svc.get_evidence_for_target(target_type, target_id, tenant_id)
        if not links:
            return self._position(PositionCategory.UNKNOWN_INSUFFICIENT, "no_evidence")
        origins = set(); supporting_count = 0; contradicting_count = 0
        for link in links:
            sr = self._ev_svc.get_source(link["source_reference_id"], tenant_id)
            if sr and getattr(sr, "status", "active") in ("revoked", "invalidated", "superseded"):
                continue
            origin = self._classify_origin(sr)
            origins.add(origin)
            if link["relation_type"] == "supports" and link["status"] == "active":
                supporting_count += 1
            elif link["relation_type"] == "contradicts" and link["status"] == "active":
                contradicting_count += 1
        has_internal = OriginClass.INTERNAL_TENANT in origins or OriginClass.HUMAN_ASSERTION in origins or OriginClass.SYSTEM_DERIVATION in origins
        has_external = OriginClass.EXTERNAL_WORLD in origins
        resolution = evidence.get("resolution_state", "no_evidence")
        if supporting_count > 0 and contradicting_count > 0:
            return self._position(PositionCategory.MIXED_EVIDENCE, resolution, supporting_count, contradicting_count)
        if has_internal and has_external and supporting_count > 0:
            return self._position(PositionCategory.MIXED_EVIDENCE, resolution, supporting_count, contradicting_count)
        if has_internal and supporting_count > 0:
            return self._position(PositionCategory.INTERNAL_DATA, resolution, supporting_count, contradicting_count)
        if has_external and supporting_count > 0:
            return self._position(PositionCategory.EXTERNAL_INFORMATION, resolution, supporting_count, contradicting_count)
        if contradicting_count > 0:
            return self._position(PositionCategory.UNKNOWN_INSUFFICIENT, resolution, supporting_count, contradicting_count)
        return self._position(PositionCategory.UNKNOWN_INSUFFICIENT, resolution, supporting_count, contradicting_count)

    def _position(self, category, resolution, supporting=0, contradicting=0, explanation=""):
        if not explanation:
            if category == PositionCategory.INTERNAL_DATA:
                explanation = "Supported by internal/tenant data"
            elif category == PositionCategory.EXTERNAL_INFORMATION:
                explanation = "Supported by external information"
            elif category == PositionCategory.MIXED_EVIDENCE:
                explanation = "Conflicting evidence exists"
            elif category == PositionCategory.ANALYSIS:
                explanation = "Derived analysis"
            elif category == PositionCategory.RECOMMENDATION:
                explanation = "Recommendation"
            else:
                explanation = "Insufficient evidence to determine position"
        return {"position_category": category, "resolution_state": resolution,
                "explanation": explanation, "supporting_count": supporting,
                "contradicting_count": contradicting, "evaluated_at": datetime.utcnow().isoformat()}

    def _default_position(self):
        return self._position(PositionCategory.UNKNOWN_INSUFFICIENT, "no_service")

    def resolve_many(self, targets, tenant_id=None):
        return [self.resolve_position(tt, ti, tenant_id) for tt, ti in targets]

    def explain_position(self, target_type, target_id, tenant_id=None):
        pos = self.resolve_position(target_type, target_id, tenant_id)
        return {"position": pos, "explanation": pos["explanation"], "reason_codes": [pos["resolution_state"]]}

    def get_basis(self, target_type, target_id, tenant_id=None):
        if self._ev_svc is None: return []
        links = self._ev_svc.get_evidence_for_target(target_type, target_id, tenant_id)
        return [l for l in links if l["relation_type"] == "supports" and l["status"] == "active"]

    def get_contradictions(self, target_type, target_id, tenant_id=None):
        if self._ev_svc is None: return []
        links = self._ev_svc.get_evidence_for_target(target_type, target_id, tenant_id)
        return [l for l in links if l["relation_type"] == "contradicts" and l["status"] == "active"]

    def present_position(self, target_type, target_id, tenant_id=None):
        pos = self.resolve_position(target_type, target_id, tenant_id)
        cat = pos["position_category"]
        wording_map = {
            PositionCategory.INTERNAL_DATA: "According to your company data",
            PositionCategory.EXTERNAL_INFORMATION: "According to external information",
            PositionCategory.ANALYSIS: "My analysis is",
            PositionCategory.RECOMMENDATION: "My recommendation is",
        }
        safe = {"category": cat, "explanation": pos["explanation"],
                "supporting_count": pos["supporting_count"],
                "contradicting_count": pos["contradicting_count"],
                "wording": wording_map.get(cat, "I don't have enough evidence to say")}
        return safe