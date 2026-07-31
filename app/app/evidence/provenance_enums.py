"""SHUNYA Evidence Engine — Provenance Enums.

Architecture-defined provenance classifications.
No reasoning. No business logic.

References:
    SMS-VOLUME-II-WORLD-MODEL.md §8 — Evidence Contract
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §4.3 — Evidence chain
"""

from __future__ import annotations

from enum import Enum


# ---------------------------------------------------------------------------
# DerivationType — canonical transformation types (NOT reasoning)
# ---------------------------------------------------------------------------

class DerivationType(str, Enum):
    """Canonical types of deterministic transformations.

    NOT reasoning. NOT inference. These are data transformations only:

    PARSED:     Extracted from raw text (document parsing, message parsing)
    NORMALIZED: Normalized to standard format (timezones, units, canonical forms)
    CONVERTED:  Type conversion (string → int, binary → text)
    MERGED:     Combined from multiple sources (consolidation)
    SPLIT:      Decomposed into parts (segmentation, chunking)
    TRANSLATED: Translated between languages (language translation)
    """
    PARSED = "parsed"
    NORMALIZED = "normalized"
    CONVERTED = "converted"
    MERGED = "merged"
    SPLIT = "split"
    TRANSLATED = "translated"


# ---------------------------------------------------------------------------
# VerificationStatus — canonical verification states
# ---------------------------------------------------------------------------

class VerificationStatus(str, Enum):
    """Canonical verification activity states.

    NOT truth calculation. Only records verification events:

    VERIFIED:   Verification succeeded (evidence checked and confirmed)
    UNVERIFIED: No verification performed yet
    CHALLENGED: Verification challenged (disputed)
    CONFIRMED:  Verification confirmed (independent confirmation)
    """
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    CHALLENGED = "challenged"
    CONFIRMED = "confirmed"


# ---------------------------------------------------------------------------
# ProvenanceRelationType — canonical provenance relationships
# ---------------------------------------------------------------------------

class ProvenanceRelationType(str, Enum):
    """Canonical provenance relationship types.

    Defines how evidence relates to other evidence in the provenance graph:

    ORIGIN:      Source of the evidence
    DERIVATION:  Derived from another evidence
    TRANSFORMATION: Transformed by a process
    AGGREGATION: Aggregated from multiple evidence
    CITATION:    Cites another evidence as support
    VERIFICATION: Verified by another evidence or process
    """
    ORIGIN = "origin"
    DERIVATION = "derivation"
    TRANSFORMATION = "transformation"
    AGGREGATION = "aggregation"
    CITATION = "citation"
    VERIFICATION = "verification"