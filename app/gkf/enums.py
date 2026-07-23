"""GKF — Enumerations for the Governed Knowledge Framework.

Defines the canonical types for governed knowledge representation.
Framework-generic — supports any governed collection.
"""

from __future__ import annotations

from enum import Enum


class GKFNodeType(str, Enum):
    """Canonical node types in the Governed Knowledge Framework.

    These types are framework-generic and support any governed collection.
    The GKF_ prefix distinguishes framework types from domain-specific types.
    """
    COLLECTION = "gkf_collection"
    VOLUME = "gkf_volume"
    CHAPTER = "gkf_chapter"
    ARTICLE = "gkf_article"
    PRINCIPLE = "gkf_principle"
    INTERPRETATION = "gkf_interpretation"
    REFERENCE = "gkf_reference"
    EVIDENCE = "gkf_evidence"
    IMPLEMENTATION_LINK = "gkf_implementation_link"
    AMENDMENT = "gkf_amendment"
    VERSION = "gkf_version"


class GKFEdgeType(str, Enum):
    """Canonical edge types in the Governed Knowledge Framework.

    Structural edges connect document hierarchy.
    Semantic edges connect governing meaning.
    Cross-cutting edges span both hierarchies.
    """
    # Structural edges
    CONTAINS = "gkf_contains"

    # Semantic edges
    CLARIFIES = "gkf_clarifies"
    IS_IMPLEMENTED_BY = "gkf_is_implemented_by"
    EXPRESSED_IN = "gkf_expressed_in"  # links structural element to semantic element

    # Cross-cutting edges
    CROSS_REFERENCES = "gkf_cross_references"
    ESTABLISHED_BY = "gkf_established_by"
    AMENDED_BY = "gkf_amended_by"
    HAS_VERSION = "gkf_has_version"


class AmendmentType(str, Enum):
    """Types of amendments to governed elements.

    ADDITION:     New content added
    MODIFICATION: Existing content changed
    SUPERSESSION: Element replaced by another
    REPEAL:       Element removed, never to be reinstated
    """
    ADDITION = "addition"
    MODIFICATION = "modification"
    SUPERSESSION = "supersession"
    REPEAL = "repeal"


class ElementStatus(str, Enum):
    """Lifecycle status of a governed element.

    ACTIVE:      Currently in effect
    SUPERSEDED:  Replaced by a newer version or element
    DRAFT:       Not yet ratified
    """
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    DRAFT = "draft"