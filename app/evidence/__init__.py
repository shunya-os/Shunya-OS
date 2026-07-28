"""SHUNYA Evidence Engine — Package Init.

Exports only stable interfaces. No helper internals.
No persistence implementation. No repositories. No storage engine.

Architecture references:
    SMS-VOLUME-II-WORLD-MODEL.md §8 — Evidence Contract
    SMS-VOLUME-I_5-CORE-SEMANTICS.md §8 — The Meaning of Evidence
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §4.3 — Evidence chain
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
from app.evidence.provenance_enums import (
    DerivationType,
    VerificationStatus,
    ProvenanceRelationType,
)
from app.evidence.provenance_models import (
    SourceIdentity,
    SourceMetadata,
    DerivationRecord,
    VerificationRecord,
    Citation,
    EvidenceChainLink,
    EvidenceChain,
    ProvenanceGraph,
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
    # Provenance
    "DerivationType",
    "VerificationStatus",
    "ProvenanceRelationType",
    "SourceIdentity",
    "SourceMetadata",
    "DerivationRecord",
    "VerificationRecord",
    "Citation",
    "EvidenceChainLink",
    "EvidenceChain",
    "ProvenanceGraph",
]
