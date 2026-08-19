"""
SHUNYA Evidence Engine — In-Memory Implementation

The EvidenceEngine manages the full evidence lifecycle: creation,
verification, supersession, provenance chaining, confidence computation,
integrity verification, and querying.

All evidence is **immutable** after creation — it can be superseded
(marked as ``SUPERSEDED``) but never deleted or modified.  Integrity is
guaranteed by content-addressed SHA-256 hashes.

Evidence chains form a DAG where each piece of evidence may reference a
parent piece of evidence via ``parent_evidence_id``.  Chains are
traversable from any leaf back to the root.

Confidence is **derived**, not asserted.  The base confidence comes from
source reliability, is increased by verification, and is inverted for
contradicting evidence.

References:
    - docs/canon/00_universal_ontology.md §10 (Evidence)
    - docs/canon/04_universal_object_protocol.md §12 (Evidence)
"""

from __future__ import annotations

import fnmatch
import logging
from typing import Any

from core.evidence.models import (
    Evidence,
    EvidenceChain,
    EvidenceDirection,
    EvidenceStatus,
    EvidenceType,
    _now_iso,
)

logger = logging.getLogger(__name__)


# ── Confidence calculation constants ─────────────────────────────────────────


_VERIFICATION_BOOST: float = 0.2
"""Confidence added when evidence is verified (capped at 1.0)."""

_BASE_OFFSET: float = 0.3
"""Baseline confidence added to source_reliability weighting."""

_SOURCE_WEIGHT: float = 0.7
"""Weight applied to source_reliability in the base formula."""

_CHAIN_DECAY: float = 0.9
"""Multiplier per chain hop for chain-depth penalty."""


# ── Company-First Trust Hierarchy (Gate 2.1) ──────────────────────────────────


class SourceReliability:
    """Canonical source reliability values per the company-first trust hierarchy.

    Higher values indicate more trustworthy information sources.
    External or AI-derived information must never silently overwrite
    trusted company data.

    Hierarchy (highest to lowest):
        1. TRUSTED_COMPANY — Canonical company records (DB, CRM, ERP)
        2. CONNECTED_SYSTEM — Connected company systems (Gmail, Calendar, Drive)
        3. USER_PROVIDED — Information provided by the user directly
        4. VERIFIED_EXTERNAL — Verified external information (web research)
        5. MODEL_INFERENCE — Model knowledge or AI inference (lowest trust)
    """
    TRUSTED_COMPANY = 1.0      # Trusted company data
    CONNECTED_SYSTEM = 0.95    # Connected company systems
    USER_PROVIDED = 0.8        # User-provided information
    VERIFIED_EXTERNAL = 0.6    # Verified external information
    MODEL_INFERENCE = 0.3      # Model knowledge/inference


class InformationType:
    """Semantic type of information for distinguishing origin.

    Every piece of evidence must be classified as one of these.
    External or model-derived information must not silently overwrite
    trusted company data of a different type.
    """
    FACT = "fact"                  # Verified company truth
    INFERENCE = "inference"        # Derived from existing data
    RECOMMENDATION = "recommendation"  # Suggested action
    DRAFT = "draft"                # Unverified, in-progress
    ACTION = "action"              # Committed action/decision


# ── EvidenceEngine ────────────────────────────────────────────────────────────


class EvidenceEngine:
    """In-memory engine for managing the SHUNYA evidence lifecycle.

    The engine maintains an in-memory store of evidence records, indexes
    by object, type, source, and full-text search over statements.

    This is a **single-threaded, in-memory** implementation suitable for
    prototyping, testing, and small-to-medium deployments.  Production
    deployments should back this with a persistent store.

    **Rules** (from Universal Ontology §10):
    - Evidence is immutable after creation — superseded, never modified.
    - Superseded evidence is preserved (marked, not deleted).
    - Evidence chains form DAGs (``parent_evidence_id`` points to source).
    - Confidence is computed, never asserted.
    - Source reliability affects confidence calculation.
    - Verification increases confidence by a factor (capped at 1.0).

    **Confidence formula:**

    ``base = source_reliability * 0.7 + 0.3``   (range [0.3, 1.0])

    If verified: ``base = min(1.0, base + 0.2)``

    If contradicting: ``base = 1.0 - base``

    Aggregate for an object:
        mean(supporting confidences) * (1 - mean(contradicting confidences))
    """

    def __init__(self) -> None:
        # Primary store: evidence_id -> Evidence
        self._store: dict[str, Evidence] = {}

        # Index: object_id -> set of evidence_ids
        self._object_index: dict[str, set[str]] = {}

        # Index: evidence_type -> set of evidence_ids
        self._type_index: dict[str, set[str]] = {}

        # Index: source -> set of evidence_ids
        self._source_index: dict[str, set[str]] = {}

    # ------------------------------------------------------------------
    # Lifecycle: Create
    # ------------------------------------------------------------------

    def create_evidence(
        self,
        object_id: str,
        evidence_type: EvidenceType | str,
        statement: str,
        source: str,
        direction: EvidenceDirection | str,
        source_reliability: float,
        captured_at: str | None = None,
        parent_evidence_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Evidence:
        """Create a new evidence record.

        Args:
            object_id: ObjectID of the subject this evidence is about.
            evidence_type: Type of evidence (``EvidenceType`` enum or string).
            statement: What the evidence asserts (free-form text).
            source: Who or what produced this evidence.
            direction: Whether the evidence supports or contradicts
                (``EvidenceDirection`` enum or string).
            source_reliability: Reliability of the source [0, 1].
            captured_at: ISO-8601 string of when data was captured.
                Defaults to the current timestamp.
            parent_evidence_id: Optional UUID v7 of parent evidence for
                chaining.  When provided, the parent must exist.
            metadata: Optional extensible metadata dictionary.

        Returns:
            The newly created ``Evidence``.

        Raises:
            ValueError: If *parent_evidence_id* references a non-existent
                evidence record, or if *source_reliability* is out of range.
        """
        # Normalise enums
        if isinstance(evidence_type, EvidenceType):
            evidence_type = evidence_type.value
        if isinstance(direction, EvidenceDirection):
            direction = direction.value

        # Validate parent
        if parent_evidence_id is not None and parent_evidence_id not in self._store:
            raise ValueError(
                f"parent_evidence_id {parent_evidence_id!r} does not exist. "
                "Parent evidence must be created before a child can reference it."
            )

        # Compute timestamp
        now = _now_iso()
        captured = captured_at or now

        # Build the evidence (the frozen dataclass computes its integrity hash)
        evidence = Evidence(
            object_id=object_id,
            evidence_type=evidence_type,
            statement=statement,
            source=source,
            source_reliability=source_reliability,
            direction=direction,
            timestamp=now,
            captured_at=captured,
            parent_evidence_id=parent_evidence_id,
            metadata=metadata or {},
        )

        # Compute initial confidence
        confidence = self._compute_single_confidence(evidence)
        object.__setattr__(evidence, "confidence", round(confidence, 6))

        # Store
        self._store[evidence.evidence_id] = evidence
        self._object_index.setdefault(object_id, set()).add(evidence.evidence_id)
        self._type_index.setdefault(evidence_type, set()).add(evidence.evidence_id)
        self._source_index.setdefault(source, set()).add(evidence.evidence_id)

        logger.info(
            "Created evidence %s for object %s (type=%s, dir=%s, reliability=%.2f)",
            evidence.evidence_id,
            object_id,
            evidence_type,
            direction,
            source_reliability,
        )

        return evidence

    # ------------------------------------------------------------------
    # Lifecycle: Verify
    # ------------------------------------------------------------------

    def verify_evidence(
        self,
        evidence_id: str,
        verified_by: str,
        metadata: dict[str, Any] | None = None,
    ) -> Evidence:
        """Mark an evidence record as verified.

        Verification increases the evidence's confidence score by 0.2
        (capped at 1.0).  Only ``COLLECTED`` or ``CONTESTED`` evidence
        can be verified.

        Args:
            evidence_id: UUID v7 of the evidence to verify.
            verified_by: Identifier of the entity performing verification.
            metadata: Optional metadata to merge into the record.

        Returns:
            The updated ``Evidence`` (a new frozen instance).

        Raises:
            ValueError: If *evidence_id* is not found, or if the evidence
                is in a terminal state (``SUPERSEDED`` or ``REJECTED``).
        """
        old = self._get_existing(evidence_id)

        if old.status in (EvidenceStatus.SUPERSEDED.value, EvidenceStatus.REJECTED.value):
            raise ValueError(
                f"Cannot verify evidence {evidence_id!r} in status "
                f"{old.status!r}. Only COLLECTED, VERIFIED, or CONTESTED "
                "evidence can be verified."
            )

        # Merge metadata
        merged_meta = {**old.metadata, **(metadata or {})}

        # Build a new instance with updated fields
        updated = Evidence(
            evidence_id=old.evidence_id,
            object_id=old.object_id,
            evidence_type=old.evidence_type,
            statement=old.statement,
            source=old.source,
            source_reliability=old.source_reliability,
            direction=old.direction,
            timestamp=old.timestamp,
            captured_at=old.captured_at,
            verified_at=_now_iso(),
            verified_by=verified_by,
            parent_evidence_id=old.parent_evidence_id,
            status=EvidenceStatus.VERIFIED.value,
            metadata=merged_meta,
        )

        # Recompute confidence with verification boost
        confidence = self._compute_single_confidence(updated)
        object.__setattr__(updated, "confidence", round(confidence, 6))

        # Replace in store (identity is preserved via evidence_id)
        self._store[evidence_id] = updated

        logger.info(
            "Verified evidence %s by %s (confidence: %.4f)",
            evidence_id,
            verified_by,
            confidence,
        )

        return updated

    # ------------------------------------------------------------------
    # Lifecycle: Supersede
    # ------------------------------------------------------------------

    def supersede_evidence(
        self,
        evidence_id: str,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> Evidence:
        """Mark an evidence record as superseded.

        Supersession occurs when evidence is contradicted or replaced by
        newer, more reliable evidence.  The original record is preserved
        for provenance — it is marked, not deleted.

        Args:
            evidence_id: UUID v7 of the evidence to supersede.
            reason: Human-readable explanation of why it is being superseded.
            metadata: Optional metadata to merge (e.g., replacement
                evidence ID as ``superseded_by``).

        Returns:
            The updated ``Evidence`` (a new frozen instance).

        Raises:
            ValueError: If *evidence_id* is not found, or if the evidence
                is already in a terminal state.
        """
        old = self._get_existing(evidence_id)

        if old.status == EvidenceStatus.REJECTED.value:
            raise ValueError(
                f"Cannot supersede evidence {evidence_id!r}: already REJECTED."
            )

        merged_meta = {
            **old.metadata,
            "superseded_at": _now_iso(),
            "superseded_reason": reason,
            **(metadata or {}),
        }

        updated = Evidence(
            evidence_id=old.evidence_id,
            object_id=old.object_id,
            evidence_type=old.evidence_type,
            statement=old.statement,
            source=old.source,
            source_reliability=old.source_reliability,
            direction=old.direction,
            timestamp=old.timestamp,
            captured_at=old.captured_at,
            verified_at=old.verified_at,
            verified_by=old.verified_by,
            parent_evidence_id=old.parent_evidence_id,
            status=EvidenceStatus.SUPERSEDED.value,
            metadata=merged_meta,
        )

        # Confidence remains as-is (supersession records the fact, not a
        # confidence adjustment — the new evidence carries the fresh score).
        object.__setattr__(updated, "confidence", old.confidence)

        self._store[evidence_id] = updated

        logger.info(
            "Superseded evidence %s: %s",
            evidence_id,
            reason,
        )

        return updated

    # ------------------------------------------------------------------
    # Query: Single evidence
    # ------------------------------------------------------------------

    def get_evidence(self, evidence_id: str) -> Evidence | None:
        """Retrieve a single evidence record by ID.

        Args:
            evidence_id: UUID v7 of the evidence.

        Returns:
            The ``Evidence`` instance, or ``None`` if not found.
        """
        return self._store.get(evidence_id)

    # ------------------------------------------------------------------
    # Query: By object
    # ------------------------------------------------------------------

    def get_evidence_for_object(self, object_id: str) -> list[Evidence]:
        """Retrieve all evidence records about a given object.

        Results are returned in chronological order (oldest first).

        Args:
            object_id: ObjectID of the subject.

        Returns:
            List of ``Evidence`` records for the object.
        """
        ids = self._object_index.get(object_id, set())
        result = [self._store[eid] for eid in ids if eid in self._store]
        result.sort(key=lambda e: e.timestamp)
        return result

    # ------------------------------------------------------------------
    # Query: Evidence chain
    # ------------------------------------------------------------------

    def get_evidence_chain(self, evidence_id: str) -> EvidenceChain:
        """Traverse the parent chain from a leaf back to the root.

        The chain is returned ordered from root (oldest) to leaf (newest).

        Args:
            evidence_id: UUID v7 of the evidence to start from (leaf).

        Returns:
            An ``EvidenceChain`` with all ancestors up to the root.

        Raises:
            ValueError: If *evidence_id* is not found.
        """
        evidence = self._get_existing(evidence_id)

        # Walk backwards to root
        chain: list[Evidence] = []
        current: Evidence | None = evidence
        seen: set[str] = set()

        while current is not None:
            if current.evidence_id in seen:
                raise RuntimeError(
                    f"Cycle detected in evidence chain at {current.evidence_id}"
                )
            seen.add(current.evidence_id)
            chain.append(current)
            if current.parent_evidence_id is not None:
                parent = self._store.get(current.parent_evidence_id)
                current = parent
            else:
                current = None

        # Reverse so root is first
        chain.reverse()

        # Compute overall confidence (geometric mean across chain)
        if chain:
            product = 1.0
            for ev in chain:
                product *= ev.confidence
            overall = product ** (1.0 / len(chain))
        else:
            overall = 0.0

        # All verified?
        all_verified = all(
            ev.status == EvidenceStatus.VERIFIED.value for ev in chain
        )

        return EvidenceChain(
            root_evidence_id=chain[0].evidence_id if chain else evidence_id,
            chain=list(chain),
            overall_confidence=round(overall, 6),
        )

    # ------------------------------------------------------------------
    # Query: By type
    # ------------------------------------------------------------------

    def get_evidence_by_type(
        self,
        evidence_type: EvidenceType | str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Evidence]:
        """Retrieve evidence records by type.

        Args:
            evidence_type: Type to filter by (``EvidenceType`` enum or string).
            limit: Maximum number of results to return (``None`` = unlimited).
            offset: Number of results to skip (for pagination).

        Returns:
            List of matching ``Evidence`` records, sorted by timestamp.
        """
        if isinstance(evidence_type, EvidenceType):
            evidence_type = evidence_type.value

        ids = self._type_index.get(evidence_type, set())
        result = sorted(
            [self._store[eid] for eid in ids if eid in self._store],
            key=lambda e: e.timestamp,
        )
        return self._paginate(result, limit, offset)

    # ------------------------------------------------------------------
    # Query: By source
    # ------------------------------------------------------------------

    def get_evidence_by_source(
        self,
        source: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Evidence]:
        """Retrieve evidence records by source.

        Args:
            source: Source identifier to filter by.
            limit: Maximum number of results to return (``None`` = unlimited).
            offset: Number of results to skip (for pagination).

        Returns:
            List of matching ``Evidence`` records, sorted by timestamp.
        """
        ids = self._source_index.get(source, set())
        result = sorted(
            [self._store[eid] for eid in ids if eid in self._store],
            key=lambda e: e.timestamp,
        )
        return self._paginate(result, limit, offset)

    # ------------------------------------------------------------------
    # Query: Search by statement text
    # ------------------------------------------------------------------

    def search_evidence(self, query: str) -> list[Evidence]:
        """Search evidence records by statement text (case-insensitive).

        Supports glob-style wildcards (``*``, ``?``) via ``fnmatch``.
        Simple substring matching is used when no wildcards are present.

        Args:
            query: Search string (e.g., ``"contract signed"`` or
                ``"*sign*"``).

        Returns:
            List of matching ``Evidence`` records, sorted by timestamp.
        """
        result: list[Evidence] = []
        query_lower = query.lower()

        has_wildcard = "*" in query or "?" in query

        for evidence in self._store.values():
            stmt_lower = evidence.statement.lower()
            if has_wildcard:
                if fnmatch.fnmatch(stmt_lower, query_lower):
                    result.append(evidence)
            else:
                if query_lower in stmt_lower:
                    result.append(evidence)

        result.sort(key=lambda e: e.timestamp)
        return result

    # ------------------------------------------------------------------
    # Confidence computation
    # ------------------------------------------------------------------

    def compute_confidence(self, evidence_id: str) -> float:
        """Compute the confidence score for a single evidence record.

        The confidence is **derived** from source reliability, verification
        status, and chain depth.  It is never directly asserted.

        Formula:
            ``base = source_reliability * 0.7 + 0.3``  (range [0.3, 1.0])

            If verified: ``base = min(1.0, base + 0.2)``

            If contradicting: ``base = 1.0 - base``

        Chain depth penalty: confidence is multiplied by ``0.9 ** depth``
        so that evidence further from the root is slightly less certain.

        Args:
            evidence_id: UUID v7 of the evidence.

        Returns:
            Confidence score in [0, 1].

        Raises:
            ValueError: If *evidence_id* is not found.
        """
        evidence = self._get_existing(evidence_id)
        return round(self._compute_single_confidence(evidence), 6)

    def _compute_single_confidence(self, evidence: Evidence) -> float:
        """Core confidence formula applied to a single Evidence instance."""
        # Base from source reliability
        base = evidence.source_reliability * _SOURCE_WEIGHT + _BASE_OFFSET
        base = max(0.0, min(1.0, base))

        # Verification boost
        if evidence.status == EvidenceStatus.VERIFIED.value and evidence.verified_by is not None:
            base = min(1.0, base + _VERIFICATION_BOOST)

        # Invert for contradicting evidence
        if evidence.direction == EvidenceDirection.CONTRADICTING.value:
            base = 1.0 - base

        # Chain depth penalty: walk parents and apply decay
        depth = 0
        current_id = evidence.parent_evidence_id
        while current_id is not None:
            depth += 1
            parent = self._store.get(current_id)
            if parent is None:
                break
            current_id = parent.parent_evidence_id

        base *= _CHAIN_DECAY ** depth

        return max(0.0, min(1.0, base))

    # ------------------------------------------------------------------
    # Integrity verification
    # ------------------------------------------------------------------

    def verify_integrity(self, evidence_id: str) -> bool:
        """Verify that an evidence record's hash matches its content.

        Recomputes the SHA-256 hash over the evidence's content-bearing
        fields and compares it to the stored hash.

        Args:
            evidence_id: UUID v7 of the evidence.

        Returns:
            ``True`` if the hash matches, ``False`` if tampering is detected.

        Raises:
            ValueError: If *evidence_id* is not found.
        """
        evidence = self._get_existing(evidence_id)

        from core.evidence.models import _compute_hash

        expected = _compute_hash(
            evidence_id=evidence.evidence_id,
            object_id=evidence.object_id,
            evidence_type=evidence.evidence_type,
            statement=evidence.statement,
            source=evidence.source,
            source_reliability=evidence.source_reliability,
            direction=evidence.direction,
            timestamp=evidence.timestamp,
            captured_at=evidence.captured_at,
            parent_evidence_id=evidence.parent_evidence_id,
            metadata=evidence.metadata,
        )
        return expected == evidence.hash

    # ------------------------------------------------------------------
    # Contradicting / Supporting queries
    # ------------------------------------------------------------------

    def get_contradicting_evidence(self, object_id: str) -> list[Evidence]:
        """Retrieve all contradicting evidence for an object.

        Args:
            object_id: ObjectID of the subject.

        Returns:
            List of ``Evidence`` records with ``direction == CONTRADICTING``.
        """
        all_ev = self.get_evidence_for_object(object_id)
        return [e for e in all_ev if e.direction == EvidenceDirection.CONTRADICTING.value]

    def get_supporting_evidence(self, object_id: str) -> list[Evidence]:
        """Retrieve all supporting evidence for an object.

        Args:
            object_id: ObjectID of the subject.

        Returns:
            List of ``Evidence`` records with ``direction == SUPPORTING``.
        """
        all_ev = self.get_evidence_for_object(object_id)
        return [e for e in all_ev if e.direction == EvidenceDirection.SUPPORTING.value]

    # ------------------------------------------------------------------
    # Aggregate confidence for an object
    # ------------------------------------------------------------------

    def get_confidence_score(self, object_id: str) -> float:
        """Compute the aggregate confidence score for an object.

        The aggregate combines all supporting and contradicting evidence
        into a single score on [0, 1]:

            mean(supporting confidences) * (1 - mean(contradicting confidences))

        If there is no supporting evidence, the supporting mean defaults
        to 0.5.  If there is no contradicting evidence, the contradicting
        term is 0 (i.e., no penalty).

        Args:
            object_id: ObjectID of the subject.

        Returns:
            Aggregate confidence score in [0, 1].
        """
        supporting = self.get_supporting_evidence(object_id)
        contradicting = self.get_contradicting_evidence(object_id)

        if not supporting and not contradicting:
            return 0.5  # Neutral — no evidence either way

        sup_mean = (
            sum(e.confidence for e in supporting) / len(supporting)
            if supporting
            else 0.5
        )
        con_mean = (
            sum(e.confidence for e in contradicting) / len(contradicting)
            if contradicting
            else 0.0
        )

        return round(sup_mean * (1.0 - con_mean), 6)

    # ------------------------------------------------------------------
    # Testing / Reset
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Reset the engine to its initial state.

        Destroys all stored evidence and indexes.  Intended for testing.
        """
        self._store.clear()
        self._object_index.clear()
        self._type_index.clear()
        self._source_index.clear()
        logger.debug("EvidenceEngine cleared")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_existing(self, evidence_id: str) -> Evidence:
        """Retrieve an evidence record or raise ``ValueError``."""
        evidence = self._store.get(evidence_id)
        if evidence is None:
            raise ValueError(f"Evidence {evidence_id!r} not found")
        return evidence

    @staticmethod
    def _paginate(
        items: list[Evidence],
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Evidence]:
        """Apply offset/limit pagination to a sorted list."""
        if offset > 0:
            items = items[offset:]
        if limit is not None:
            items = items[:limit]
        return items


# ── Singleton factory ────────────────────────────────────────────────────────


_engine_instance: EvidenceEngine | None = None


def get_evidence_engine() -> EvidenceEngine:
    """Return the singleton ``EvidenceEngine`` instance.

    Creates the instance on first call; reuses it thereafter.  This is
    the recommended way to obtain an engine in production code so that
    all callers share the same in-memory store.

    For testing, create a fresh ``EvidenceEngine()`` directly.
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = EvidenceEngine()
    return _engine_instance