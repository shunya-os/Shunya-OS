"""
SHUNYA — Memory Service (Phase 6)
"""
import json
from datetime import datetime
from typing import Optional
from app import db
from app.memory.models import (
    MemoryRecord, MemoryCandidate, MemoryProvenance, MemoryConcept,
    MemoryType, MemoryScope, MemoryStatus, CandidateStatus, MemoryCreationMechanism,
)
from app.privacy import PrivacyService
from app.privacy.models import MemoryEligibility, SensitivityLevel


class MemoryService:
    def __init__(self, session=None):
        self._session = session or db.session
        self._privacy = PrivacyService(session)

    # ------------------------------------------------------------------
    # Candidate
    # ------------------------------------------------------------------
    def propose_memory(self, person_id: Optional[int], memory_key: str, value: str,
                       memory_type: str = "other", scope_type: str = "person",
                       tenant_id: Optional[int] = None, **kw) -> dict:
        cand = MemoryCandidate(tenant_id=tenant_id, person_id=person_id,
            memory_key=memory_key, value=value, memory_type=memory_type,
            scope_type=scope_type, **kw)
        self._session.add(cand); self._session.commit()
        return {"success": True, "candidate_id": cand.id, "status": CandidateStatus.PROPOSED}

    def approve_candidate(self, candidate_id: int, tenant_id: Optional[int] = None,
                          approved_by: str = "") -> dict:
        cand = self._session.get(MemoryCandidate, candidate_id)
        if not cand: return {"success": False, "error": "Not found"}
        if tenant_id is not None and cand.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}
        # Phase 4 gate
        privacy = self._privacy.evaluate_memory_eligibility(
            "memory_candidate", cand.id, tenant_id=tenant_id, person_id=cand.person_id)
        if privacy.get("memory_eligibility") == MemoryEligibility.INELIGIBLE:
            return {"success": False, "error": "Blocked by privacy", "privacy": privacy}
        cand.status = CandidateStatus.APPROVED
        cand.approved_by = approved_by; cand.approved_at = datetime.utcnow()
        self._session.commit()
        return {"success": True, "status": CandidateStatus.APPROVED}

    def commit_candidate(self, candidate_id: int, tenant_id: Optional[int] = None) -> dict:
        cand = self._session.get(MemoryCandidate, candidate_id)
        if not cand: return {"success": False, "error": "Not found"}
        if tenant_id is not None and cand.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}
        if cand.status == CandidateStatus.COMMITTED:
            return {"success": False, "error": "Already committed"}
        # Re-check Phase 4
        privacy = self._privacy.evaluate_memory_eligibility(
            "memory_candidate", cand.id, tenant_id=tenant_id, person_id=cand.person_id)
        if privacy.get("memory_eligibility") == MemoryEligibility.INELIGIBLE:
            return {"success": False, "error": "Blocked by privacy at commit time"}
        # Create memory
        mem = MemoryRecord(tenant_id=cand.tenant_id, person_id=cand.person_id,
            memory_type=cand.memory_type, memory_key=cand.memory_key, value=cand.value,
            scope_type=cand.scope_type, source_object_type=cand.source_object_type,
            source_object_id=cand.source_object_id, creation_mechanism=cand.creation_mechanism,
            status=MemoryStatus.ACTIVE, effective_from=datetime.utcnow())
        self._session.add(mem); self._session.flush()
        cand.status = CandidateStatus.COMMITTED
        self._session.commit()
        return {"success": True, "memory_id": mem.id, "status": MemoryStatus.ACTIVE}

    # ------------------------------------------------------------------
    # Direct creation (supersedes existing active for same key/scope)
    # ------------------------------------------------------------------
    def create_explicit_memory(self, person_id: Optional[int], memory_key: str, value: str,
                                memory_type: str = "other", scope_type: str = "person",
                                tenant_id: Optional[int] = None, **kw) -> MemoryRecord:
        existing = self._session.query(MemoryRecord).filter_by(
            person_id=person_id, memory_key=memory_key, scope_type=scope_type,
            status=MemoryStatus.ACTIVE).first()
        if existing:
            existing.status = MemoryStatus.SUPERSEDED
        mem = MemoryRecord(tenant_id=tenant_id, person_id=person_id,
            memory_key=memory_key, value=value, memory_type=memory_type,
            scope_type=scope_type, status=MemoryStatus.ACTIVE,
            effective_from=datetime.utcnow(), **kw)
        self._session.add(mem); self._session.flush()
        if existing:
            existing.superseded_by_id = mem.id; mem.supersedes_id = existing.id
        self._session.commit()
        return mem

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------
    def get_effective_memories(self, person_id: Optional[int] = None,
                                memory_key: Optional[str] = None,
                                scope_type: Optional[str] = None,
                                tenant_id: Optional[int] = None) -> list[dict]:
        q = self._session.query(MemoryRecord).filter_by(status=MemoryStatus.ACTIVE)
        if tenant_id: q = q.filter(MemoryRecord.tenant_id == tenant_id)
        if person_id: q = q.filter(MemoryRecord.person_id == person_id)
        if memory_key: q = q.filter(MemoryRecord.memory_key == memory_key)
        if scope_type: q = q.filter(MemoryRecord.scope_type == scope_type)
        return [self._item_to_dict(m) for m in q.order_by(MemoryRecord.created_at.desc()).all()]

    def _item_to_dict(self, m: MemoryRecord) -> dict:
        return {"id": m.id, "memory_key": m.memory_key, "value": m.value,
            "memory_type": m.memory_type, "scope_type": m.scope_type,
            "status": m.status, "creation_mechanism": m.creation_mechanism,
            "supersedes_id": m.supersedes_id, "superseded_by_id": m.superseded_by_id,
            "created_at": m.created_at.isoformat() if m.created_at else None}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------
    def revoke_memory(self, memory_id: int, tenant_id: Optional[int] = None) -> dict:
        m = self._session.get(MemoryRecord, memory_id)
        if not m: return {"success": False, "error": "Not found"}
        if tenant_id is not None and m.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}
        m.status = MemoryStatus.REVOKED; self._session.commit()
        return {"success": True, "status": MemoryStatus.REVOKED}

    def supersede_memory(self, memory_id: int, new_value: str,
                          tenant_id: Optional[int] = None, **kw) -> dict:
        m = self._session.get(MemoryRecord, memory_id)
        if not m: return {"success": False, "error": "Not found"}
        if tenant_id is not None and m.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}
        new_m = self.create_explicit_memory(m.person_id, m.memory_key, new_value,
            memory_type=m.memory_type, scope_type=m.scope_type, tenant_id=tenant_id, **kw)
        return {"success": True, "memory_id": new_m.id, "status": MemoryStatus.ACTIVE}