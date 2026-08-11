"""
SHUNYA — Canonical Memory Service (FDA3)
=========================================

ONE canonical Memory & Knowledge authority.

Memory is CONTEXT, NOT canonical truth.

Memory must NOT silently promote:
  INFERENCE → FACT
  MEMORY → FACT
  DECISION → OUTCOME
  INTENTION → OUTCOME

Architecture:
  REAL SOURCE/EVENT → OBSERVATION → AWARENESS/CONTEXT → DECISION
  → EXECUTION → OUTCOME/EVIDENCE → MEMORY/LEARNING → FUTURE CONTEXT
"""
import json
from datetime import datetime
from typing import Any, Optional

from app import db
from app.memory.models import (
    MemoryRecord, MemoryCandidate, MemoryProvenance, MemoryConcept,
    MemoryType, MemoryScope, MemoryStatus, CandidateStatus,
    MemoryCreationMechanism, TruthClassification,
)
from app.privacy import PrivacyService
from app.privacy.models import MemoryEligibility, SensitivityLevel

# ── Truth promotion guard ─────────────────────────────────────────────

_PROMOTION_BLACKLIST = {
    (TruthClassification.INFERENCE, TruthClassification.FACT),
    (TruthClassification.MEMORY, TruthClassification.FACT),
    (TruthClassification.DECISION, TruthClassification.OUTCOME),
    (TruthClassification.INTENTION, TruthClassification.OUTCOME),
}

_INJECTION_KEYWORDS = [
    "ignore all security",
    "ignore security rules",
    "override security",
    "disable security",
    "bypass auth",
    "bypass authentication",
    "skip authorization",
    "ignore all rules",
    "you are now",
    "system override",
]


def _check_truth_promotion(source: str, target: str) -> None:
    """Raise if a forbidden truth promotion would occur.

    FDA3: Memory must NEVER silently promote:
      INFERENCE → FACT
      MEMORY → FACT
      DECISION → OUTCOME
      INTENTION → OUTCOME
    """
    if (source, target) in _PROMOTION_BLACKLIST:
        raise ValueError(
            f"Forbidden truth promotion: {source} → {target}. "
            "Memory is CONTEXT, not canonical truth."
        )


def _check_contamination(value: str) -> None:
    """Check memory value for known injection/override patterns.

    Stored content must remain DATA, not executable instructions.
    """
    v = value.lower()
    for kw in _INJECTION_KEYWORDS:
        if kw in v:
            raise ValueError(
                f"Memory value rejected: contains prohibited pattern '{kw}'. "
                "Stored content must remain DATA, not executable instructions."
            )


def _check_write_eligibility(value: str, memory_type: str,
                              creation_mechanism: str) -> None:
    """Transient/conversation noise must not become durable memory.

    Only qualifying information passes through.
    """
    # Short, generic values without structure are not durable
    if not value or len(value.strip()) < 5:
        raise ValueError(
            "Memory value too short (<5 chars): not eligible for durable storage."
        )
    # Trivial auto-generated context markers
    trivial = {"", "none", "null", "undefined", "n/a", "-"}
    if value.strip().lower() in trivial:
        raise ValueError(
            "Memory value is a trivial/noop marker: not eligible for durable storage."
        )


class MemoryService:
    """FDA3 canonical memory service.

    ONE authority for all SHUNYA memory operations.
    Consumers must NOT manipulate memory tables directly.
    """

    def __init__(self, session=None):
        self._session = session or db.session
        self._privacy = PrivacyService(session)

    # ------------------------------------------------------------------
    # Candidate lifecycle
    # ------------------------------------------------------------------

    def propose_memory(self, person_id: Optional[int], memory_key: str, value: str,
                       memory_type: str = "other", scope_type: str = "person",
                       tenant_id: Optional[int] = None,
                       truth_classification: str = "memory",
                       **kw) -> dict:
        """Propose a memory candidate. Goes through eligibility gates."""
        _check_contamination(value)
        _check_write_eligibility(value, memory_type, "explicit")
        _check_truth_promotion("memory", truth_classification)

        cand = MemoryCandidate(
            tenant_id=tenant_id, person_id=person_id,
            memory_key=memory_key, value=value,
            memory_type=memory_type, scope_type=scope_type,
            truth_classification=truth_classification,
            **kw,
        )
        self._session.add(cand)
        self._session.commit()
        return {
            "success": True, "candidate_id": cand.id,
            "status": CandidateStatus.PROPOSED,
            "truth_classification": truth_classification,
        }

    def approve_candidate(self, candidate_id: int,
                          tenant_id: Optional[int] = None,
                          approved_by: str = "") -> dict:
        cand = self._session.get(MemoryCandidate, candidate_id)
        if not cand:
            return {"success": False, "error": "Not found"}
        if tenant_id is not None and cand.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}
        # Phase 4 gate
        privacy = self._privacy.evaluate_memory_eligibility(
            "memory_candidate", cand.id,
            tenant_id=tenant_id, person_id=cand.person_id)
        if privacy.get("memory_eligibility") == MemoryEligibility.INELIGIBLE:
            return {"success": False, "error": "Blocked by privacy",
                    "privacy": privacy}
        cand.status = CandidateStatus.APPROVED
        cand.approved_by = approved_by
        cand.approved_at = datetime.utcnow()
        self._session.commit()
        return {"success": True, "status": CandidateStatus.APPROVED}

    def commit_candidate(self, candidate_id: int,
                         tenant_id: Optional[int] = None) -> dict:
        cand = self._session.get(MemoryCandidate, candidate_id)
        if not cand:
            return {"success": False, "error": "Not found"}
        if tenant_id is not None and cand.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}
        if cand.status == CandidateStatus.COMMITTED:
            return {"success": False, "error": "Already committed"}
        # Re-check Phase 4
        privacy = self._privacy.evaluate_memory_eligibility(
            "memory_candidate", cand.id,
            tenant_id=tenant_id, person_id=cand.person_id)
        if privacy.get("memory_eligibility") == MemoryEligibility.INELIGIBLE:
            return {"success": False, "error": "Blocked by privacy at commit time"}
        # Create memory record
        mem = MemoryRecord(
            tenant_id=cand.tenant_id, person_id=cand.person_id,
            memory_type=cand.memory_type, memory_key=cand.memory_key,
            value=cand.value, value_type=cand.value_type,
            scope_type=cand.scope_type,
            source_object_type=cand.source_object_type,
            source_object_id=cand.source_object_id,
            creation_mechanism=cand.creation_mechanism,
            truth_classification=cand.truth_classification or "memory",
            status=MemoryStatus.ACTIVE,
            effective_from=datetime.utcnow(),
        )
        self._session.add(mem)
        self._session.flush()
        cand.status = CandidateStatus.COMMITTED
        self._session.commit()
        return {
            "success": True, "memory_id": mem.id,
            "status": MemoryStatus.ACTIVE,
            "truth_classification": mem.truth_classification,
        }

    # ------------------------------------------------------------------
    # Direct creation (FDA3 canonical write path)
    # ------------------------------------------------------------------

    def create_memory(
        self, person_id: Optional[int], memory_key: str, value: str,
        memory_type: str = "other", scope_type: str = "person",
        tenant_id: Optional[int] = None,
        truth_classification: str = "memory",
        provenance_source: Optional[str] = None,
        provenance_source_id: Optional[str] = None,
        source_object_type: Optional[str] = None,
        source_object_id: Optional[int] = None,
        creation_mechanism: str = "explicit",
        **kw,
    ) -> MemoryRecord:
        """FDA3 canonical memory write.

        Every write goes through:
        1. Contamination/injection check
        2. Write-eligibility check
        3. Truth-promotion guard
        4. Contradiction detection (supersede conflicting active)
        5. Provenance recording
        """
        # Gate 1: injection defense
        _check_contamination(value)
        # Gate 2: write eligibility
        _check_write_eligibility(value, memory_type, creation_mechanism)
        # Gate 3: truth promotion guard
        _check_truth_promotion(truth_classification, truth_classification)

        # Gate 4: contradiction detection — supersede existing active
        self._resolve_contradictions(
            person_id=person_id, memory_key=memory_key,
            scope_type=scope_type, tenant_id=tenant_id,
            memory_type=memory_type, value=value,
        )

        # Create memory record
        mem = MemoryRecord(
            tenant_id=tenant_id, person_id=person_id,
            memory_type=memory_type, memory_key=memory_key,
            value=value, scope_type=scope_type,
            source_object_type=source_object_type or "",
            source_object_id=source_object_id,
            creation_mechanism=creation_mechanism,
            truth_classification=truth_classification,
            status=MemoryStatus.ACTIVE,
            effective_from=datetime.utcnow(),
            injection_checked=True,
            **kw,
        )
        self._session.add(mem)
        self._session.flush()

        # Gate 5: provenance recording (idempotent — skip duplicate)
        if provenance_source and provenance_source_id:
            self._add_provenance(
                memory_id=mem.id,
                source_object_type=source_object_type or "",
                source_object_id=source_object_id or 0,
                provenance_source=provenance_source,
                provenance_source_id=provenance_source_id,
                provenance_role="source",
                creation_mechanism=creation_mechanism,
                tenant_id=tenant_id,
            )

        self._session.commit()
        return mem

    def _resolve_contradictions(
        self, person_id: Optional[int], memory_key: str,
        scope_type: str, tenant_id: Optional[int],
        memory_type: str, value: str,
    ) -> None:
        """FDA3 contradiction handling.

        Deterministic approach:
        - If explicit user correction (same key+scope, different value):
          supersede active with resolution_type='user_correction'
        - If conflicting memory_type with same key: supersede
        - Resolution is deterministic, explainable, and provenance-preserving.
        """
        active = self._session.query(MemoryRecord).filter_by(
            person_id=person_id,
            memory_key=memory_key,
            scope_type=scope_type,
            tenant_id=tenant_id,
            status=MemoryStatus.ACTIVE,
        ).first()

        if active and active.value != value:
            # Contradiction detected
            active.resolution_type = "user_correction"
            active.resolution_reason = (
                f"Contradiction: value changed from "
                f"'{active.value[:100]}' to '{value[:100]}'. "
                f"New value has higher recency authority."
            )
            active.status = MemoryStatus.SUPERSEDED

    def _add_provenance(self, memory_id: int,
                        source_object_type: str,
                        source_object_id: int,
                        provenance_source: str,
                        provenance_source_id: str,
                        provenance_role: str = "source",
                        creation_mechanism: str = "explicit",
                        tenant_id: Optional[int] = None) -> Optional[MemoryProvenance]:
        """Record provenance (idempotent via unique constraint).

        If the same (provenance_source, provenance_source_id) already exists,
        silently skip — this is the idempotency guarantee for replay.
        """
        # Check if provenance already exists (idempotency guard)
        existing = self._session.query(MemoryProvenance).filter_by(
            provenance_source=provenance_source,
            provenance_source_id=provenance_source_id,
        ).first()
        if existing:
            return None

        prov = MemoryProvenance(
            tenant_id=tenant_id,
            memory_id=memory_id,
            source_object_type=source_object_type,
            source_object_id=source_object_id,
            provenance_source=provenance_source,
            provenance_source_id=provenance_source_id,
            provenance_role=provenance_role,
            creation_mechanism=creation_mechanism,
            observed_at=datetime.utcnow(),
        )
        self._session.add(prov)
        return prov

    # ------------------------------------------------------------------
    # Contradiction (explicit API)
    # ------------------------------------------------------------------

    def resolve_contradiction(self,
                               memory_id: int,
                               resolution_type: str,
                               resolution_reason: str,
                               tenant_id: Optional[int] = None) -> dict:
        """Explicitly resolve a contradiction on an active memory."""
        m = self._session.get(MemoryRecord, memory_id)
        if not m:
            return {"success": False, "error": "Not found"}
        if tenant_id is not None and m.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}
        if m.status != MemoryStatus.ACTIVE:
            return {"success": False, "error": "Only active memories can be resolved"}

        m.status = MemoryStatus.SUPERSEDED
        m.resolution_type = resolution_type
        m.resolution_reason = resolution_reason
        self._session.commit()
        return {"success": True, "status": MemoryStatus.SUPERSEDED,
                "resolution_type": resolution_type}

    # ------------------------------------------------------------------
    # User correction (FDA3 WS8)
    # ------------------------------------------------------------------

    def correct_memory(self, memory_id: int, new_value: str,
                       correction_reason: str = "user correction",
                       tenant_id: Optional[int] = None,
                       provenance_source: Optional[str] = None,
                       provenance_source_id: Optional[str] = None) -> dict:
        """FDA3 user correction path.

        A correction must:
        - identify the memory
        - preserve audit/provenance
        - invalidate/supersede the old memory
        - create the corrected truth
        - prevent retrieval of invalidated value as current truth
        """
        m = self._session.get(MemoryRecord, memory_id)
        if not m:
            return {"success": False, "error": "Not found"}
        if tenant_id is not None and m.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}

        # Gate: injection defense on new value
        _check_contamination(new_value)

        # Create corrected memory
        corrected = self.create_memory(
            person_id=m.person_id,
            memory_key=m.memory_key,
            value=new_value,
            memory_type=m.memory_type,
            scope_type=m.scope_type,
            tenant_id=tenant_id,
            truth_classification=m.truth_classification,
            creation_mechanism="explicit",
            provenance_source=provenance_source or f"correction:{memory_id}",
            provenance_source_id=provenance_source_id or str(memory_id),
        )

        # Supersede old memory with explanation
        m.status = MemoryStatus.SUPERSEDED
        m.resolution_type = "user_correction"
        m.resolution_reason = correction_reason
        m.superseded_by_id = corrected.id
        corrected.supersedes_id = m.id
        self._session.commit()

        return {
            "success": True,
            "old_memory_id": m.id,
            "new_memory_id": corrected.id,
            "status": MemoryStatus.ACTIVE,
        }

    # ------------------------------------------------------------------
    # Retrieval (FDA3 canonical)
    # ------------------------------------------------------------------

    def get_effective_memories(
        self, person_id: Optional[int] = None,
        memory_key: Optional[str] = None,
        scope_type: Optional[str] = None,
        tenant_id: Optional[int] = None,
        status_filter: Optional[str] = MemoryStatus.ACTIVE,
        truth_classification: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """FDA3 canonical retrieval.

        Returns lifecycle-aware results.
        By default returns only ACTIVE memories (current truth).
        """
        q = self._session.query(MemoryRecord)
        if status_filter:
            q = q.filter(MemoryRecord.status == status_filter)
        if tenant_id is not None:
            q = q.filter(MemoryRecord.tenant_id == tenant_id)
        if person_id is not None:
            q = q.filter(MemoryRecord.person_id == person_id)
        if memory_key is not None:
            q = q.filter(MemoryRecord.memory_key == memory_key)
        if scope_type is not None:
            q = q.filter(MemoryRecord.scope_type == scope_type)
        if truth_classification is not None:
            q = q.filter(
                MemoryRecord.truth_classification == truth_classification)
        return [
            self._item_to_dict(m)
            for m in q.order_by(MemoryRecord.created_at.desc()).limit(limit).all()
        ]

    def get_memory_with_provenance(self, memory_id: int) -> Optional[dict]:
        """Retrieve a memory with its full provenance chain."""
        m = self._session.get(MemoryRecord, memory_id)
        if not m:
            return None
        result = self._item_to_dict(m)
        provenance = self._session.query(MemoryProvenance).filter_by(
            memory_id=memory_id).all()
        result["provenance"] = [
            {
                "id": p.id,
                "source_object_type": p.source_object_type,
                "source_object_id": p.source_object_id,
                "provenance_source": p.provenance_source,
                "provenance_source_id": p.provenance_source_id,
                "provenance_role": p.provenance_role,
                "observed_at": (
                    p.observed_at.isoformat() if p.observed_at else None
                ),
            }
            for p in provenance
        ]
        return result

    def get_memory_history(self, memory_key: str,
                            person_id: Optional[int] = None,
                            scope_type: Optional[str] = None,
                            tenant_id: Optional[int] = None) -> list[dict]:
        """Get full version history for a memory key.

        Returns ACTIVE, SUPERSEDED, INVALIDATED records to support
        provenance reconstruction.
        """
        q = self._session.query(MemoryRecord).filter(
            MemoryRecord.memory_key == memory_key)
        if tenant_id is not None:
            q = q.filter(MemoryRecord.tenant_id == tenant_id)
        if person_id is not None:
            q = q.filter(MemoryRecord.person_id == person_id)
        if scope_type is not None:
            q = q.filter(MemoryRecord.scope_type == scope_type)
        return [
            self._item_to_dict(m)
            for m in q.order_by(MemoryRecord.created_at.desc()).all()
        ]

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def invalidate_memory(self, memory_id: int,
                           tenant_id: Optional[int] = None,
                           reason: str = "") -> dict:
        m = self._session.get(MemoryRecord, memory_id)
        if not m:
            return {"success": False, "error": "Not found"}
        if tenant_id is not None and m.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}
        m.status = MemoryStatus.INVALIDATED
        m.resolution_reason = reason or "Invalidated by system"
        self._session.commit()
        return {"success": True, "status": MemoryStatus.INVALIDATED}

    def archive_memory(self, memory_id: int,
                        tenant_id: Optional[int] = None) -> dict:
        m = self._session.get(MemoryRecord, memory_id)
        if not m:
            return {"success": False, "error": "Not found"}
        if tenant_id is not None and m.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}
        m.status = MemoryStatus.ARCHIVED
        self._session.commit()
        return {"success": True, "status": MemoryStatus.ARCHIVED}

    def revoke_memory(self, memory_id: int,
                       tenant_id: Optional[int] = None) -> dict:
        m = self._session.get(MemoryRecord, memory_id)
        if not m:
            return {"success": False, "error": "Not found"}
        if tenant_id is not None and m.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}
        m.status = MemoryStatus.REVOKED
        self._session.commit()
        return {"success": True, "status": MemoryStatus.REVOKED}

    # ------------------------------------------------------------------
    # Query (legacy compat)
    # ------------------------------------------------------------------

    def create_explicit_memory(self, *args: Any, **kwargs: Any) -> MemoryRecord:
        """Legacy-compat alias for create_memory."""
        return self.create_memory(*args, **kwargs)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _item_to_dict(self, m: MemoryRecord) -> dict:
        return {
            "id": m.id,
            "memory_key": m.memory_key,
            "value": m.value,
            "memory_type": m.memory_type,
            "scope_type": m.scope_type,
            "status": m.status,
            "truth_classification": m.truth_classification,
            "creation_mechanism": m.creation_mechanism,
            "supersedes_id": m.supersedes_id,
            "superseded_by_id": m.superseded_by_id,
            "resolution_type": m.resolution_type,
            "resolution_reason": m.resolution_reason,
            "injection_checked": m.injection_checked,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }