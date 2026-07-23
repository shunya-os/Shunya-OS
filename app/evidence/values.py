"""SHUNYA Evidence Engine — Immutable Value Objects.

All value objects are frozen dataclasses (immutable by construction).
No reasoning. No business logic. No persistence.

Architecture references:
    SMS-VOLUME-II-WORLD-MODEL.md §8 — Evidence Contract
    SMS-VOLUME-I_5-CORE-SEMANTICS.md §8 — The Meaning of Evidence
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


# ---------------------------------------------------------------------------
# Confidence — canonical confidence score
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Confidence:
    """Canonical confidence score.

    Always in the range 0.0–1.0. Never outside this range.
    Confidence is not truth. Confidence is the system's assessment
    of reliability at the time of capture.

    Attributes:
        score:    The confidence score (0.0–1.0)
        label:    Optional human-readable label (e.g., "high", "low")
        reason:   Optional explanation of how this confidence was determined
    """
    score: float
    label: str = ""
    reason: str = ""

    def __post_init__(self) -> None:
        """Validate confidence range at construction time."""
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(
                f"Confidence score must be in range [0.0, 1.0], got {self.score}"
            )


# ---------------------------------------------------------------------------
# Freshness — temporal relevance indicator
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Freshness:
    """Temporal relevance of an evidence record.

    Captures when the evidence was captured and its expected validity period.

    Attributes:
        captured_at:  ISO 8601 timestamp of when the evidence was captured
        valid_until:  ISO 8601 timestamp after which the evidence expires,
                      or None if it does not expire
    """
    captured_at: str
    valid_until: str | None = None


# ---------------------------------------------------------------------------
# VersionReference — reference to a specific version
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VersionReference:
    """Reference to a specific version of an evidence record.

    Evidence version history is append-only. This reference points to
    exactly one version in that append-only chain.

    Attributes:
        evidence_id:  The evidence record identifier
        version:      The specific version number
    """
    evidence_id: str
    version: int


# ---------------------------------------------------------------------------
# EvidenceReference — reference to evidence supporting a claim
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceReference:
    """A reference from a conclusion or object back to supporting evidence.

    This is the link between "what we believe" and "why we believe it."
    Every computed conclusion must carry at least one EvidenceReference.

    Attributes:
        evidence_id:  The evidence record identifier
        target_id:    The object or conclusion this evidence supports
        target_type:  The type of the target object or conclusion
        confidence:   Confidence in this specific link
        role:         Optional description of how this evidence supports
                      the target (e.g., "direct", "supporting", "contradicting")
    """
    evidence_id: str
    target_id: str
    target_type: str
    confidence: Confidence | None = None
    role: str = ""
