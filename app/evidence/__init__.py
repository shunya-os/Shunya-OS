"""SHUNYA Evidence Engine — Package Init.

Exports only stable interfaces. No helper internals.
No persistence implementation. No repositories. No storage engine.

Architecture references:
    SMS-VOLUME-II-WORLD-MODEL.md §8 — Evidence Contract
    SMS-VOLUME-I_5-CORE-SEMANTICS.md §8 — The Meaning of Evidence
"""

from app.evidence.enums import (
    EvidenceStatus,
    EvidenceType,
    SourceCategory,
)
from app.evidence.values import (
    Confidence,
    Freshness,
    VersionReference,
    EvidenceReference,
)
from app.evidence.models import (
    Evidence,
    Observation,
    EvidenceSource,
    Provenance,
    EvidenceStore,
    InMemoryEvidenceStore,
)

__all__ = [
    # Enums
    "EvidenceStatus",
    "EvidenceType",
    "SourceCategory",
    # Value Objects
    "Confidence",
    "Freshness",
    "VersionReference",
    "EvidenceReference",
    # Models
    "Evidence",
    "Observation",
    "EvidenceSource",
    "Provenance",
    "EvidenceStore",
    "InMemoryEvidenceStore",
]
