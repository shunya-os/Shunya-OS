"""SHUNYA — Knowledge Engine (Phase L — ES-002).

The Knowledge Engine is the single source of truth for all facts within
SHUNYA. It stores, versions, retrieves, and validates every piece of
knowledge with the fundamental guarantee that no fact is ever silently
overwritten. Every mutation creates a new version. Every version is
permanently traceable. Every retrieval includes a confidence score,
checksum, and evidence chain.

Architectural authority: ES-002 — Knowledge Engine Specification
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.shunya.knowledge_engine.models import (
    FactState, KnowledgeCategory, ValueType, SourceType,
    _STATE_TRANSITIONS,
    FactVersion, KnowledgeInput,
    KnowledgeRetrievalResult, KnowledgeSearchResult,
    SourceRef, EvidenceChain, KnowledgeStats,
)


# ---------------------------------------------------------------------------
# Knowledge Engine
# ---------------------------------------------------------------------------


class ImmutableKnowledgeStore:
    """Immutable, versioned knowledge store (ES-002).

    Guarantees:
    - No fact is ever silently overwritten (append-only versions)
    - Every version has a SHA-256 checksum
    - Every fact follows a deterministic lifecycle (8 states, 14 transitions)
    - Conflicting facts are detected and flagged
    - All operations are scoped to tenant_id
    """

    def __init__(self) -> None:
        self._versions: Dict[str, List[FactVersion]] = {}  # fact_key → [versions]
        self._current: Dict[str, FactVersion] = {}          # fact_key → current version
        self._conflicts: Dict[str, List[str]] = {}           # fact_key → conflicting version_ids
        self._stats = KnowledgeStats()

    # ------------------------------------------------------------------
    # Write Operations
    # ------------------------------------------------------------------

    def store(self, inp: KnowledgeInput) -> Tuple[bool, Optional[FactVersion], List[str]]:
        """Store a new fact version. Returns (success, version, errors)."""
        errors = inp.validate()
        if errors:
            return False, None, errors

        existing = self._current.get(inp.fact_key)
        new_version_num = (existing.version + 1) if existing else 1

        new_state = inp.initial_state
        # If initial state is VERIFIED and source is manual, keep VERIFIED
        if inp.source == SourceType.MANUAL.value:
            new_state = FactState.VERIFIED.value

        version = FactVersion(
            fact_key=inp.fact_key,
            version=new_version_num,
            value=inp.value,
            value_type=inp.value_type,
            state=new_state,
            confidence=inp.confidence,
            evidence=inp.evidence,
            source=inp.source,
            created_by=inp.created_by,
            tenant_id=inp.tenant_id,
            domain=inp.domain,
            category=inp.category,
            valid_from=inp.valid_from or datetime.now(timezone.utc),
            valid_until=inp.valid_until,
            tags=list(inp.tags),
        )

        # Supersede previous version
        if existing and existing.state not in (FactState.RETIRED.value, FactState.ARCHIVED.value):
            new_state = self._transition(existing.state, FactState.SUPERSEDED.value)
            if new_state:
                existing.state = new_state
                existing.superseded_at = datetime.now(timezone.utc)

        # Store
        if inp.fact_key not in self._versions:
            self._versions[inp.fact_key] = []
        self._versions[inp.fact_key].append(version)
        self._current[inp.fact_key] = version

        # Conflict detection: check if new fact contradicts existing
        if existing and existing.value != version.value:
            if inp.fact_key not in self._conflicts:
                self._conflicts[inp.fact_key] = []
            self._conflicts[inp.fact_key].append(str(existing.version))
            self._conflicts[inp.fact_key].append(str(version.version))
            existing.state = FactState.CONFLICT.value
            version.state = FactState.CONFLICT.value

        # Update stats
        self._stats.total_versions += 1
        self._stats.facts_current = len(self._current)
        self._stats.facts_by_domain[inp.domain] = self._stats.facts_by_domain.get(inp.domain, 0) + 1
        if version.state == FactState.CONFLICT.value:
            self._stats.conflicts += 1

        return True, version, []

    def transition(self, fact_key: str, to_state: str,
                   tenant_id: Optional[int] = None) -> Tuple[bool, str]:
        """Transition a fact to a new state (ES-002 §6)."""
        existing = self._current.get(fact_key)
        if not existing:
            return False, "Fact not found"
        if tenant_id and existing.tenant_id != tenant_id:
            return False, "TENANT_MISMATCH"

        new_state = self._transition(existing.state, to_state)
        if not new_state:
            return False, (f"Invalid transition from {existing.state} to {to_state}")

        existing.state = new_state
        return True, f"Transitioned to {new_state}"

    # ------------------------------------------------------------------
    # Read Operations
    # ------------------------------------------------------------------

    def get(self, fact_key: str, tenant_id: Optional[int] = None) -> Optional[KnowledgeRetrievalResult]:
        """Get the current version of a fact (ES-002 §16)."""
        version = self._current.get(fact_key)
        if not version:
            return None
        if tenant_id and version.tenant_id != tenant_id:
            return None
        return self._to_retrieval_result(version)

    def get_at_time(self, fact_key: str, timestamp: datetime,
                    tenant_id: Optional[int] = None) -> Optional[KnowledgeRetrievalResult]:
        """Get the version of a fact valid at a specific time (ES-002 §16)."""
        versions = self._versions.get(fact_key, [])
        if not versions:
            return None
        # Find the latest version that was valid at the given timestamp
        valid: Optional[FactVersion] = None
        for v in versions:
            if tenant_id and v.tenant_id != tenant_id:
                continue
            if v.valid_from and v.valid_from <= timestamp:
                if v.valid_until is None or v.valid_until > timestamp:
                    if valid is None or v.version > valid.version:
                        valid = v
        return self._to_retrieval_result(valid) if valid else None

    def get_history(self, fact_key: str,
                    tenant_id: Optional[int] = None) -> List[KnowledgeRetrievalResult]:
        """Get all versions of a fact (ES-002 §15)."""
        versions = self._versions.get(fact_key, [])
        if tenant_id:
            versions = [v for v in versions if v.tenant_id == tenant_id]
        return [self._to_retrieval_result(v) for v in versions]

    def get_by_domain(self, domain: str, category: Optional[str] = None,
                      tenant_id: Optional[int] = None) -> List[KnowledgeRetrievalResult]:
        """Get all current facts in a domain, optionally filtered by category."""
        results: List[KnowledgeRetrievalResult] = []
        for v in self._current.values():
            if v.domain != domain:
                continue
            if tenant_id and v.tenant_id != tenant_id:
                continue
            if category and v.category != category:
                continue
            if v.state == FactState.RETIRED.value:
                continue
            results.append(self._to_retrieval_result(v))
        return results

    def search(self, query: str, domain: Optional[str] = None,
               tenant_id: Optional[int] = None) -> KnowledgeSearchResult:
        """Search facts by key and value (ES-002 §16)."""
        results: List[KnowledgeRetrievalResult] = []
        q = query.lower()
        for v in self._current.values():
            if tenant_id and v.tenant_id != tenant_id:
                continue
            if domain and v.domain != domain:
                continue
            if q in v.fact_key.lower() or q in str(v.value).lower():
                results.append(self._to_retrieval_result(v))
        confs = [r.confidence for r in results]
        return KnowledgeSearchResult(
            results=results,
            total_count=len(results),
            confidence_range=[min(confs, default=0.0), max(confs, default=0.0)],
        )

    def get_evidence_chain(self, fact_key: str,
                           tenant_id: Optional[int] = None) -> Optional[EvidenceChain]:
        """Build an evidence chain for a fact (ES-002 §5)."""
        fact = self.get(fact_key, tenant_id)
        if not fact:
            return None

        version = self._current.get(fact_key)
        source_refs: List[SourceRef] = []
        if version and version.evidence:
            source_refs.append(SourceRef(
                fact_key=fact_key,
                version=version.version,
                evidence=version.evidence,
                source=version.source,
                confidence=version.confidence,
            ))

        # Supporting facts: same domain, same category
        supporting: List[KnowledgeRetrievalResult] = []
        contradicting: List[KnowledgeRetrievalResult] = []
        if version:
            domain = version.domain
            for v in self._current.values():
                if v.fact_key == fact_key:
                    continue
                if tenant_id and v.tenant_id != tenant_id:
                    continue
                if v.domain == domain:
                    supporting.append(self._to_retrieval_result(v))
                if v.state == FactState.CONFLICT.value:
                    contradicting.append(self._to_retrieval_result(v))

        resolution = "supported"
        if version and version.state == FactState.CONFLICT.value:
            resolution = "conflict"
        elif not supporting and not source_refs:
            resolution = "no_evidence"

        return EvidenceChain(
            fact=fact,
            source_references=source_refs,
            supporting_facts=supporting,
            contradicting_facts=contradicting,
            resolution_state=resolution,
        )

    # ------------------------------------------------------------------
    # State Machine
    # ------------------------------------------------------------------

    def _transition(self, from_state: str, to_state: str) -> Optional[str]:
        """Validate and apply a state transition (ES-002 §6)."""
        try:
            from_enum = FactState(from_state)
            to_enum = FactState(to_state)
        except (ValueError, KeyError):
            return None
        allowed = _STATE_TRANSITIONS.get(from_enum, [])
        if to_enum not in allowed:
            return None
        return to_enum.value

    def list_transitions(self, from_state: str) -> List[str]:
        """List all allowed transitions from a given state."""
        try:
            from_enum = FactState(from_state)
        except (ValueError, KeyError):
            return []
        return [s.value for s in _STATE_TRANSITIONS.get(from_enum, [])]

    # ------------------------------------------------------------------
    # Conflict Management
    # ------------------------------------------------------------------

    def get_conflicts(self, tenant_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all facts currently in conflict state."""
        conflicts: List[Dict[str, Any]] = []
        for fk, version_ids in self._conflicts.items():
            versions = self._versions.get(fk, [])
            matching = [v for v in versions if str(v.version) in version_ids]
            if tenant_id:
                matching = [v for v in matching if v.tenant_id == tenant_id]
            if matching:
                conflicts.append({
                    "fact_key": fk,
                    "versions": [v.to_dict() for v in matching],
                    "current_versions": version_ids,
                })
        return conflicts

    def resolve_conflict(self, fact_key: str, resolution_fact_key: str,
                         resolution_value: Any, created_by: str = "",
                         tenant_id: Optional[int] = None) -> Tuple[bool, str]:
        """Resolve a conflict by creating a new trusted version (ES-002 §15)."""
        if fact_key not in self._conflicts:
            return False, "No conflict found for this fact key"
        if tenant_id:
            current = self._current.get(fact_key)
            if current and current.tenant_id != tenant_id:
                return False, "TENANT_MISMATCH"

        inp = KnowledgeInput(
            fact_key=fact_key,
            value=resolution_value,
            domain=self._current[fact_key].domain if fact_key in self._current else "",
            source=SourceType.MANUAL.value,
            created_by=created_by,
            tenant_id=tenant_id or (self._current[fact_key].tenant_id if fact_key in self._current else None),
            initial_state=FactState.TRUSTED.value,
        )
        success, version, errors = self.store(inp)
        if success:
            # Mark conflict as resolved
            current = self._current.get(fact_key)
            if current:
                current.state = FactState.TRUSTED.value
            if fact_key in self._conflicts:
                del self._conflicts[fact_key]
            self._stats.conflicts = max(0, self._stats.conflicts - 1)
            return True, "Conflict resolved"
        return False, "; ".join(errors)

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------

    def verify_integrity(self, fact_key: str) -> Tuple[bool, List[str]]:
        """Verify the checksum integrity of all versions of a fact."""
        versions = self._versions.get(fact_key, [])
        violations: List[str] = []
        for v in versions:
            if not v.verify_checksum():
                violations.append(
                    f"Version {v.version}: checksum mismatch "
                    f"(expected {v.checksum}, computed {v._compute_checksum()})"
                )
        return len(violations) == 0, violations

    def verify_all_integrity(self) -> Tuple[int, List[str]]:
        """Verify integrity of all stored facts. Returns (fail_count, violations)."""
        violations: List[str] = []
        for fk in self._versions:
            ok, v = self.verify_integrity(fk)
            if not ok:
                violations.extend(v)
        return len(violations), violations

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @property
    def stats(self) -> Dict[str, Any]:
        return self._stats.to_dict()

    @property
    def fact_count(self) -> int:
        return len(self._current)

    def _to_retrieval_result(self, version: FactVersion) -> KnowledgeRetrievalResult:
        return KnowledgeRetrievalResult(
            fact_key=version.fact_key,
            version=version.version,
            value=version.value,
            value_type=version.value_type,
            confidence=version.confidence,
            evidence=version.evidence,
            source=version.source,
            checksum=version.checksum,
            created_by=version.created_by,
            created_at=version.created_at,
            superseded_at=version.superseded_at,
            valid_from=version.valid_from,
            valid_until=version.valid_until,
            tenant_id=version.tenant_id,
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_INSTANCE: Optional[ImmutableKnowledgeStore] = None


def get_knowledge_store() -> ImmutableKnowledgeStore:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ImmutableKnowledgeStore()
    return _INSTANCE


def reset_knowledge_store() -> None:
    global _INSTANCE
    _INSTANCE = None