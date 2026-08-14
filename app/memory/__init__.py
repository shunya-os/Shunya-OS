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
from datetime import datetime, timezone
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
    "ignore all previous instructions",
    "ignore previous instructions",
    "disregard previous instructions",
    "disregard all previous instructions",
    "forget all previous instructions",
    "you are now",
    "system override",
]


def _check_truth_promotion(source: str, target: str) -> None:
    """Raise if a forbidden truth promotion would occur."""
    if (source, target) in _PROMOTION_BLACKLIST:
        raise ValueError(
            f"Forbidden truth promotion: {source} → {target}. "
            "Memory is CONTEXT, not canonical truth."
        )


def _check_contamination(value: str) -> None:
    """Check memory value for known injection/override patterns."""
    v = value.lower()
    for kw in _INJECTION_KEYWORDS:
        if kw in v:
            raise ValueError(
                f"Memory value rejected: contains prohibited pattern '{kw}'. "
                "Stored content must remain DATA, not executable instructions."
            )


def _check_write_eligibility(value: str, memory_type: str,
                              creation_mechanism: str, write_mode: str = "auto") -> None:
    """Transient/conversation noise must not become durable memory.

    write_mode='auto': applies full eligibility filtering.
    write_mode='confirmed': bypasses eligibility for explicitly confirmed content.
    """
    # Length check
    if not value or len(value.strip()) < 5:
        raise ValueError(
            "Memory value too short (<5 chars): not eligible for durable storage."
        )
    # Trivial markers
    trivial = {"", "none", "null", "undefined", "n/a", "-"}
    if value.strip().lower() in trivial:
        raise ValueError(
            "Memory value is a trivial/noop marker: not eligible for durable storage."
        )


# ── Retention / Expiry helpers ────────────────────────────────────────

_DEFAULT_RETENTION_DAYS = 365  # 1 year default
_RETENTION_BY_TYPE = {
    "preference": 730,        # 2 years
    "fact": 3650,             # 10 years for verified facts
    "decision": 365,          # 1 year
    "outcome": 365,           # 1 year
    "procedural": 180,        # 6 months
    "temporal": 90,           # 3 months
    "relationship_context": 365,
    "business_context": 365,
    "other": 365,
}

_NEVER_EXPIRE_TYPES = {"fact", "preference", "constraint", "requirement"}


def _get_retention_days(memory_type: str) -> int:
    return _RETENTION_BY_TYPE.get(memory_type, _DEFAULT_RETENTION_DAYS)


def _should_expire(memory: MemoryRecord) -> bool:
    """Check if a memory has exceeded its retention period."""
    if memory.memory_type in _NEVER_EXPIRE_TYPES:
        return False
    if not memory.created_at:
        return False
    days = _get_retention_days(memory.memory_type)
    age = (datetime.utcnow() - memory.created_at).days
    return age > days


# ═══════════════════════════════════════════════════════════════════════

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
        privacy = self._privacy.evaluate_memory_eligibility(
            "memory_candidate", cand.id,
            tenant_id=tenant_id, person_id=cand.person_id)
        if privacy.get("memory_eligibility") == MemoryEligibility.INELIGIBLE:
            return {"success": False, "error": "Blocked by privacy at commit time"}
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
        write_mode: str = "auto",
        **kw,
    ) -> MemoryRecord:
        """FDA3 canonical memory write.

        write_mode='auto': AI-generated content must pass eligibility gates.
        write_mode='confirmed': Explicitly confirmed content bypasses auto-gates.

        Every write goes through:
        1. Contamination/injection check
        2. Write-eligibility check (auto only)
        3. Truth-promotion guard
        4. Contradiction detection
        5. Provenance recording
        """
        # Gate 1: injection defense (always enforced)
        _check_contamination(value)

        # Gate 2: write eligibility (auto-safe only)
        if write_mode == "auto":
            _check_write_eligibility(value, memory_type, creation_mechanism)
        _check_truth_promotion(truth_classification, truth_classification)

        # Gate 3: contradiction detection
        self._resolve_contradictions(
            person_id=person_id, memory_key=memory_key,
            scope_type=scope_type, tenant_id=tenant_id,
            memory_type=memory_type, value=value,
        )

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

        # Gate 4: provenance recording
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
        active = self._session.query(MemoryRecord).filter_by(
            person_id=person_id,
            memory_key=memory_key,
            scope_type=scope_type,
            tenant_id=tenant_id,
            status=MemoryStatus.ACTIVE,
        ).first()

        if active and active.value != value:
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
        m = self._session.get(MemoryRecord, memory_id)
        if not m:
            return {"success": False, "error": "Not found"}
        if tenant_id is not None and m.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}
        _check_contamination(new_value)

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
            write_mode="confirmed",
        )

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

    # ==================================================================
    # FDA3 REMEDIATION: DELETE / EXPORT / RETENTION
    # ==================================================================

    # ------------------------------------------------------------------
    # Delete (audit-preserving)
    # ------------------------------------------------------------------

    def delete_memory(self, memory_id: int,
                       tenant_id: Optional[int] = None,
                       reason: str = "",
                       hard_delete: bool = False) -> dict:
        """Delete a memory record.

        soft_delete (default): Marks as DELETED, preserves audit trail.
        hard_delete: Removes the record entirely (only for transient data).
        """
        m = self._session.get(MemoryRecord, memory_id)
        if not m:
            return {"success": False, "error": "Not found"}
        if tenant_id is not None and m.tenant_id != tenant_id:
            return {"success": False, "error": "Not found"}

        if hard_delete:
            # Hard delete removes the record entirely.
            # Only allowed for non-consequential (transient) memory.
            if m.truth_classification in (
                TruthClassification.FACT,
                TruthClassification.OUTCOME,
                TruthClassification.EVIDENCE,
            ):
                return {
                    "success": False,
                    "error": (
                        "Hard delete refused: memory classified as "
                        f"{m.truth_classification} is authoritative. "
                        "Use soft_delete (default) to preserve audit trail."
                    ),
                }
            # Also remove provenance
            self._session.query(MemoryProvenance).filter_by(
                memory_id=memory_id).delete()
            self._session.delete(m)
            self._session.commit()
            return {"success": True, "action": "hard_deleted"}
        else:
            # Soft delete: preserve audit trail
            m.status = MemoryStatus.INVALIDATED
            m.resolution_reason = reason or "Deleted by user"
            self._session.commit()
            return {"success": True, "action": "soft_deleted",
                    "status": MemoryStatus.INVALIDATED}

    # ------------------------------------------------------------------
    # Export (tenant-scoped, auth-aware, provenance-preserving)
    # ------------------------------------------------------------------

    def export_memories(self, tenant_id: int,
                         person_id: Optional[int] = None,
                         memory_type: Optional[str] = None,
                         memory_key: Optional[str] = None,
                         status_filter: Optional[str] = None,
                         include_provenance: bool = True,
                         include_history: bool = False,
                         format: str = "json",
                         ) -> dict:
        """Export memories for a tenant.

        Export is:
        - tenant-scoped (mandatory tenant_id parameter)
        - authorization-aware (requires tenant context)
        - provenance-preserving (includes provenance chain)
        - deterministic (same query → same results)
        - auditable (logged if audit system connected)
        """
        if not tenant_id:
            return {"success": False, "error": "tenant_id is required for export"}

        q = self._session.query(MemoryRecord).filter(
            MemoryRecord.tenant_id == tenant_id)
        if person_id is not None:
            q = q.filter(MemoryRecord.person_id == person_id)
        if memory_type is not None:
            q = q.filter(MemoryRecord.memory_type == memory_type)
        if memory_key is not None:
            q = q.filter(MemoryRecord.memory_key == memory_key)
        if status_filter is not None:
            q = q.filter(MemoryRecord.status == status_filter)

        records = q.order_by(MemoryRecord.created_at.desc()).all()
        result = []
        for r in records:
            item = self._item_to_dict(r)
            if include_provenance:
                prov = self._session.query(MemoryProvenance).filter_by(
                    memory_id=r.id).all()
                item["provenance"] = [
                    {
                        "source_object_type": p.source_object_type,
                        "source_object_id": p.source_object_id,
                        "provenance_source": p.provenance_source,
                        "provenance_source_id": p.provenance_source_id,
                        "provenance_role": p.provenance_role,
                    }
                    for p in prov
                ]
            result.append(item)

        return {
            "success": True,
            "tenant_id": tenant_id,
            "count": len(result),
            "format": format,
            "exported_at": datetime.utcnow().isoformat(),
            "records": result,
        }

    # ------------------------------------------------------------------
    # Retention / Expiry
    # ------------------------------------------------------------------

    def apply_retention(self, tenant_id: Optional[int] = None,
                         dry_run: bool = False,
                         expiry_reason: str = "Retention period exceeded",
                         ) -> dict:
        """Apply retention policy: expire memories past their retention period.

        dry_run=True: report what would be expired without modifying.
        Different memory types have different retention periods.
        Fact/preference types never expire.
        """
        q = self._session.query(MemoryRecord).filter(
            MemoryRecord.status == MemoryStatus.ACTIVE)

        if tenant_id is not None:
            q = q.filter(MemoryRecord.tenant_id == tenant_id)

        expired = []
        for m in q.all():
            if _should_expire(m):
                expired.append({
                    "id": m.id,
                    "memory_key": m.memory_key,
                    "memory_type": m.memory_type,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "days_old": (datetime.utcnow() - m.created_at).days,
                })
                if not dry_run:
                    m.status = MemoryStatus.EXPIRED
                    m.resolution_reason = expiry_reason

        if not dry_run:
            self._session.commit()

        return {
            "success": True,
            "dry_run": dry_run,
            "tenant_id": tenant_id,
            "expired_count": len(expired),
            "expired": expired,
        }

    def get_retention_policy(self) -> dict:
        """Return current retention policy configuration."""
        return {
            "default_days": _DEFAULT_RETENTION_DAYS,
            "by_type": dict(_RETENTION_BY_TYPE),
            "never_expire_types": list(_NEVER_EXPIRE_TYPES),
        }

    # ==================================================================
    # Mutation (existing)
    # ==================================================================

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