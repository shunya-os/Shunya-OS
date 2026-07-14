"""
SHUNYA — Evidence Service (Phase 7)
"""
from datetime import datetime
from typing import Optional
from app import db
from app.evidence.models import (
    SourceReference, EvidenceLink, AssertionRecord, SourceAssessment,
    SourceKind, ProducerType, SourceLifecycle, RelationType, ResolutionState, CreationMechanism,
)


class EvidenceService:
    def __init__(self, session=None):
        self._session = session or db.session

    # --- SourceReference ---
    def register_source(self, source_kind: str, source_object_type: str, source_object_id: int,
                         tenant_id: Optional[int] = None, **kw) -> SourceReference:
        sr = SourceReference(tenant_id=tenant_id, source_kind=source_kind,
            source_object_type=source_object_type, source_object_id=source_object_id, **kw)
        self._session.add(sr); self._session.commit()
        return sr

    def get_source(self, source_id: int, tenant_id: Optional[int] = None) -> Optional[SourceReference]:
        sr = self._session.get(SourceReference, source_id)
        if not sr: return None
        if tenant_id is not None and sr.tenant_id != tenant_id: return None
        return sr

    def list_sources(self, tenant_id: Optional[int] = None, **filters) -> list[SourceReference]:
        q = self._session.query(SourceReference)
        if tenant_id: q = q.filter(SourceReference.tenant_id == tenant_id)
        return q.order_by(SourceReference.created_at.desc()).all()

    # --- EvidenceLink ---
    def create_evidence_link(self, source_reference_id: int, target_type: str, target_id: int,
                              relation_type: str = "references", tenant_id: Optional[int] = None, **kw) -> dict:
        src = self._session.get(SourceReference, source_reference_id)
        if not src: return {"success": False, "error": "Source not found"}
        if tenant_id is not None and src.tenant_id != tenant_id:
            return {"success": False, "error": "Source not found"}
        el = EvidenceLink(tenant_id=tenant_id, source_reference_id=source_reference_id,
            target_type=target_type, target_id=target_id, relation_type=relation_type, **kw)
        self._session.add(el); self._session.commit()
        return {"success": True, "evidence_link_id": el.id, "relation_type": relation_type}

    def get_evidence_for_target(self, target_type: str, target_id: int,
                                 tenant_id: Optional[int] = None) -> list[dict]:
        q = self._session.query(EvidenceLink).filter_by(target_type=target_type, target_id=target_id)
        if tenant_id: q = q.filter(EvidenceLink.tenant_id == tenant_id)
        return [{"id": e.id, "relation_type": e.relation_type, "source_reference_id": e.source_reference_id,
                 "status": e.status, "created_at": e.created_at.isoformat() if e.created_at else None}
                for e in q.order_by(EvidenceLink.created_at.desc()).all()]

    def resolve_evidence(self, target_type: str, target_id: int,
                          tenant_id: Optional[int] = None) -> dict:
        links = self.get_evidence_for_target(target_type, target_id, tenant_id)
        supporting = [l for l in links if l["relation_type"] == "supports" and l["status"] == "active"]
        contradicting = [l for l in links if l["relation_type"] == "contradicts" and l["status"] == "active"]
        if not links:
            return {"resolution_state": ResolutionState.NO_EVIDENCE, "supporting": [], "contradicting": []}
        if not supporting and not contradicting:
            return {"resolution_state": ResolutionState.NO_EVIDENCE, "supporting": [], "contradicting": []}
        if supporting and contradicting:
            return {"resolution_state": ResolutionState.CONTRADICTED, "supporting": supporting, "contradicting": contradicting}
        if supporting:
            return {"resolution_state": ResolutionState.SUPPORTED, "supporting": supporting, "contradicting": []}
        return {"resolution_state": ResolutionState.UNSUPPORTED, "supporting": [], "contradicting": contradicting}

    # --- Provenance ---
    def get_provenance_chain(self, target_type: str, target_id: int,
                              tenant_id: Optional[int] = None, max_depth: int = 5) -> list[dict]:
        visited = set()
        chain = []
        def _traverse(tt: str, ti: int, depth: int):
            if depth > max_depth: return
            key = f"{tt}:{ti}"
            if key in visited: return
            visited.add(key)
            links = self._session.query(EvidenceLink).filter_by(
                target_type=tt, target_id=ti, relation_type="derived_from")
            if tenant_id: links = links.filter(EvidenceLink.tenant_id == tenant_id)
            for link in links.order_by(EvidenceLink.created_at.desc()).all():
                sr = self._session.get(SourceReference, link.source_reference_id)
                if sr and (tenant_id is None or sr.tenant_id == tenant_id):
                    chain.append({"source_kind": sr.source_kind, "source_object_type": sr.source_object_type,
                                  "source_object_id": sr.source_object_id, "depth": depth})
                    _traverse(sr.source_object_type, sr.source_object_id, depth + 1)
        _traverse(target_type, target_id, 0)
        return chain

    # --- Lifecycle ---
    def revoke_source(self, source_id: int, tenant_id: Optional[int] = None) -> dict:
        sr = self._session.get(SourceReference, source_id)
        if not sr: return {"success": False, "error": "Not found"}
        if tenant_id is not None and sr.tenant_id != tenant_id: return {"success": False, "error": "Not found"}
        sr.status = SourceLifecycle.REVOKED; self._session.commit()
        return {"success": True, "status": SourceLifecycle.REVOKED}