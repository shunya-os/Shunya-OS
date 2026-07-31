"""SHUNYA Evidence Engine — Canonical Evidence Enums.

Defines the architecture-defined lifecycle and classification enums
for the universal evidence model. No reasoning. No business logic.

Architecture references:
    SMS-VOLUME-II-WORLD-MODEL.md §8 — Evidence Contract
    SMS-VOLUME-I_5-CORE-SEMANTICS.md §8 — The Meaning of Evidence
"""

from __future__ import annotations

from enum import Enum


# ---------------------------------------------------------------------------
# EvidenceStatus — architecture-defined lifecycle (§8.4)
# ---------------------------------------------------------------------------

class EvidenceStatus(str, Enum):
    """Lifecycle status of an Evidence record.

    Architecture-defined lifecycle states.
    No destructive deletion — evidence is never destroyed.

    ACTIVE:       Currently valid evidence
    SUPERSEDED:   Replaced by newer evidence (the new evidence references this)
    WITHDRAWN:    Explicitly retracted by the source
    EXPIRED:     No longer relevant due to age or context change
    """
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


# ---------------------------------------------------------------------------
# EvidenceType — canonical evidence classifications (§8.2)
# ---------------------------------------------------------------------------

class EvidenceType(str, Enum):
    """Canonical evidence classifications.

    Architecture-defined categories from SMS-VOLUME-II-WORLD-MODEL.md §8.2
    and SMS-VOLUME-I_5-CORE-SEMANTICS.md §8.

    Do NOT merge categories. Each represents a distinct provenance mode.

    OBSERVED:     Direct sensory or sensor observation (I saw it)
    REPORTED:     Second-hand account (someone told me)
    CALCULATED:   Deterministic computation from known inputs
    INFERRED:     Logical deduction from other evidence
    PREDICTED:    Future estimate based on models or patterns
    GENERATED:    Produced by an automated process or system
    """
    OBSERVED = "observed"
    REPORTED = "reported"
    CALCULATED = "calculated"
    INFERRED = "inferred"
    PREDICTED = "predicted"
    GENERATED = "generated"


# ---------------------------------------------------------------------------
# SourceCategory — canonical origin categories (architecture-defined)
# ---------------------------------------------------------------------------

class SourceCategory(str, Enum):
    """Canonical categories for evidence origin.

    Architecture-defined source categories.
    No business assumptions. Universal.

    HUMAN:        Originated from a human (direct input, testimony, report)
    SYSTEM:       Originated from an automated system or process
    SENSOR:       Originated from a physical or logical sensor
    DOCUMENT:     Originated from a document or record
    DERIVED:      Originated from computation or inference from other sources
    EXTERNAL:     Originated from outside the SHUNYA system
    """
    HUMAN = "human"
    SYSTEM = "system"
    SENSOR = "sensor"
    DOCUMENT = "document"
    DERIVED = "derived"
    EXTERNAL = "external"
