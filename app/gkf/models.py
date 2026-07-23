"""GKF — Data models for the Governed Knowledge Framework.

All models are frozen dataclasses (immutable by construction).
All models implement to_dict() for serialization.

Framework-generic — supports any governed collection.

11 element types:
  GovernedCollection, Volume, Chapter, Article, Principle,
  Interpretation, Reference, GKFEvidence, ImplementationLink,
  Amendment, GKFVersion
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.gkf.enums import AmendmentType, ElementStatus, GKFEdgeType, GKFNodeType
from app.gkf.identity import (
    generate_amendment_id,
    generate_article_id,
    generate_chapter_id,
    generate_collection_id,
    generate_evidence_id,
    generate_implementation_link_id,
    generate_interpretation_id,
    generate_principle_id,
    generate_reference_id,
    generate_version_id,
    generate_volume_id,
    parse_gkf_identity,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# GovernedCollection — root container (§3.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GovernedCollection:
    """Root container for a complete body of governed knowledge.

    A collection is the top-level organizational unit. Examples:
    - SHUNYA Constitution (first governed collection)
    - GDPR Compliance Framework (future)
    - Enterprise Policy Manual (future)
    """
    collection_id: str = ""
    name: str = ""
    description: str = ""
    jurisdiction: str = ""
    status: str = ElementStatus.DRAFT.value
    established: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.collection_id:
            object.__setattr__(self, "collection_id", generate_collection_id(self.name or "unnamed"))
        if not self.established:
            object.__setattr__(self, "established", _now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.COLLECTION.value,
            "collection_id": self.collection_id,
            "name": self.name,
            "description": self.description,
            "jurisdiction": self.jurisdiction,
            "status": self.status,
            "established": self.established,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.COLLECTION.value


# ---------------------------------------------------------------------------
# Volume — major division (§3.2)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Volume:
    """A major division within a Governed Collection."""
    volume_id: str = ""
    collection_id: str = ""
    number: int = 0
    title: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.volume_id and self.collection_id:
            object.__setattr__(self, "volume_id", generate_volume_id(self.collection_id, self.number))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.VOLUME.value,
            "volume_id": self.volume_id,
            "collection_id": self.collection_id,
            "number": self.number,
            "title": self.title,
            "description": self.description,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.VOLUME.value


# ---------------------------------------------------------------------------
# Chapter — sub-division (§3.3)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Chapter:
    """A sub-division within a Volume."""
    chapter_id: str = ""
    volume_id: str = ""
    number: int = 0
    title: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.chapter_id and self.volume_id:
            object.__setattr__(self, "chapter_id", generate_chapter_id(self.volume_id, self.number))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.CHAPTER.value,
            "chapter_id": self.chapter_id,
            "volume_id": self.volume_id,
            "number": self.number,
            "title": self.title,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.CHAPTER.value


# ---------------------------------------------------------------------------
# Article — document container (§3.4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Article:
    """A numbered document container that organizes principles.

    Articles exist for human readability and document structure.
    They are numbered, titled, and contain body text.

    When the body and a Principle conflict, the Principle governs.
    """
    article_id: str = ""
    collection_id: str = ""
    number: int = 0
    title: str = ""
    body: str = ""
    status: str = ElementStatus.DRAFT.value
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.article_id and self.collection_id:
            object.__setattr__(self, "article_id", generate_article_id(self.collection_id, self.number))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.ARTICLE.value,
            "article_id": self.article_id,
            "collection_id": self.collection_id,
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "status": self.status,
            "version": self.version,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.ARTICLE.value


# ---------------------------------------------------------------------------
# Principle — primary governing semantic object (§3.5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Principle:
    """The primary governing semantic object.

    Principles are what implementation, reasoning, and governance reference.
    A principle's identity is STABLE — it does NOT encode document location.

    If an Article body and a Principle conflict, the Principle governs.
    """
    principle_id: str = ""
    collection_id: str = ""
    name: str = ""
    statement: str = ""
    category: str = ""
    status: str = ElementStatus.ACTIVE.value
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.principle_id and self.collection_id and self.name:
            object.__setattr__(self, "principle_id", generate_principle_id(self.collection_id, self.name))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.PRINCIPLE.value,
            "principle_id": self.principle_id,
            "collection_id": self.collection_id,
            "name": self.name,
            "statement": self.statement,
            "category": self.category,
            "status": self.status,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.PRINCIPLE.value

    @property
    def is_active(self) -> bool:
        return self.status == ElementStatus.ACTIVE.value

    @property
    def is_superseded(self) -> bool:
        return self.status == ElementStatus.SUPERSEDED.value


# ---------------------------------------------------------------------------
# Interpretation — authoritative clarification (§3.6)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Interpretation:
    """An authoritative explanation or clarification of a Principle."""
    interpretation_id: str = ""
    principle_id: str = ""
    number: int = 0
    statement: str = ""
    authority: str = ""
    established: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.interpretation_id and self.principle_id:
            object.__setattr__(self, "interpretation_id", generate_interpretation_id(self.principle_id, self.number))
        if not self.established:
            object.__setattr__(self, "established", _now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.INTERPRETATION.value,
            "interpretation_id": self.interpretation_id,
            "principle_id": self.principle_id,
            "number": self.number,
            "statement": self.statement,
            "authority": self.authority,
            "established": self.established,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.INTERPRETATION.value


# ---------------------------------------------------------------------------
# Reference — cross-reference (§3.7)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Reference:
    """A cross-reference from one governed element to another."""
    reference_id: str = ""
    source_id: str = ""
    target_id: str = ""
    relationship: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.reference_id and self.source_id and self.target_id:
            object.__setattr__(self, "reference_id", generate_reference_id(self.source_id, self.target_id))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.REFERENCE.value,
            "reference_id": self.reference_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship": self.relationship,
            "description": self.description,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.REFERENCE.value


# ---------------------------------------------------------------------------
# GKFEvidence — source evidence (§3.8)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GKFEvidence:
    """Source evidence that establishes a Principle, Article, or Collection."""
    evidence_id: str = ""
    collection_id: str = ""
    source_type: str = ""
    source_path: str = ""
    title: str = ""
    authority: str = ""
    body: str = ""
    local_id: str = ""
    established: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.evidence_id and self.collection_id and self.source_type:
            lid = self.local_id or self.source_type
            object.__setattr__(self, "evidence_id", generate_evidence_id(self.collection_id, self.source_type, lid))
        if not self.established:
            object.__setattr__(self, "established", _now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.EVIDENCE.value,
            "evidence_id": self.evidence_id,
            "collection_id": self.collection_id,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "title": self.title,
            "authority": self.authority,
            "body": self.body,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.EVIDENCE.value


# ---------------------------------------------------------------------------
# ImplementationLink — principle to code (§3.9)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImplementationLink:
    """A link from a Principle to the code that implements it.

    Implementation Links are reference-only — they do NOT imply enforcement.
    """
    link_id: str = ""
    principle_id: str = ""
    module_path: str = ""
    code_reference: str = ""
    status: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.link_id and self.principle_id and self.module_path:
            object.__setattr__(self, "link_id", generate_implementation_link_id(self.principle_id, self.module_path))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.IMPLEMENTATION_LINK.value,
            "link_id": self.link_id,
            "principle_id": self.principle_id,
            "module_path": self.module_path,
            "code_reference": self.code_reference,
            "status": self.status,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.IMPLEMENTATION_LINK.value


# ---------------------------------------------------------------------------
# Amendment — change record (§3.10)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Amendment:
    """A record of a change to any governed element."""
    amendment_id: str = ""
    target_id: str = ""
    number: int = 1
    amendment_type: str = AmendmentType.MODIFICATION.value
    reason: str = ""
    authority: str = ""
    established: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.amendment_id and self.target_id:
            object.__setattr__(self, "amendment_id", generate_amendment_id(self.target_id, self.number))
        if not self.established:
            object.__setattr__(self, "established", _now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.AMENDMENT.value,
            "amendment_id": self.amendment_id,
            "target_id": self.target_id,
            "number": self.number,
            "amendment_type": self.amendment_type,
            "reason": self.reason,
            "authority": self.authority,
            "established": self.established,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.AMENDMENT.value


# ---------------------------------------------------------------------------
# GKFVersion — immutable snapshot (§3.11)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GKFVersion:
    """An immutable snapshot of any governed element at a point in time."""
    version_id: str = ""
    element_id: str = ""
    number: int = 1
    content: Dict[str, Any] = field(default_factory=dict)
    established: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.version_id and self.element_id:
            object.__setattr__(self, "version_id", generate_version_id(self.element_id, self.number))
        if not self.established:
            object.__setattr__(self, "established", _now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.VERSION.value,
            "version_id": self.version_id,
            "element_id": self.element_id,
            "number": self.number,
            "content": self.content,
            "established": self.established,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.VERSION.value