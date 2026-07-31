"""GKF — Data models for the Governed Knowledge Framework.

All models are frozen dataclasses (immutable by construction).
All models implement to_dict() for serialization.

Framework-generic — supports any governed collection.

Elements:
  GovernedCollection, Volume, Chapter, Article,
  GoverningPrinciple, Interpretation, Reference,
  GKFEvidence, ImplementationLink, Amendment, GKFVersion,
  — GKF-001A: Authority, Citation, Commentary, Example,
    ImplementationGuidance
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.gkf.enums import (
    AmendmentType, AuthorityType, ElementStatus, GKFEdgeType, GKFNodeType,
    SemanticCategory,
)
from app.gkf.identity import (
    generate_amendment_id, generate_article_id, generate_authority_id,
    generate_chapter_id, generate_citation_id, generate_collection_id,
    generate_commentary_id, generate_evidence_id, generate_example_id,
    generate_governing_principle_id, generate_implementation_guidance_id,
    generate_implementation_link_id, generate_interpretation_id,
    generate_reference_id, generate_version_id, generate_volume_id,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# GovernedCollection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GovernedCollection:
    """Root container for a complete body of governed knowledge."""
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
# Volume
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Volume:
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
# Chapter
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Chapter:
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
# Article
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Article:
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
# GoverningPrinciple (GKF-001A: renamed from Principle)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GoverningPrinciple:
    """The primary governing semantic object.

    Governing Principles are what implementation, reasoning, and governance
    reference. A principle's identity is STABLE — it does NOT encode
    document location.

    If an Article body and a Governing Principle conflict,
    the Governing Principle governs.
    """
    governing_principle_id: str = ""
    collection_id: str = ""
    name: str = ""
    statement: str = ""
    category: str = ""
    authority_id: str = ""  # GKF-001A authoritative attribution
    status: str = ElementStatus.ACTIVE.value
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.governing_principle_id and self.collection_id and self.name:
            object.__setattr__(
                self, "governing_principle_id",
                generate_governing_principle_id(self.collection_id, self.name),
            )

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "node_type": GKFNodeType.GOVERNING_PRINCIPLE.value,
            "governing_principle_id": self.governing_principle_id,
            "collection_id": self.collection_id,
            "name": self.name,
            "statement": self.statement,
            "category": self.category,
            "status": self.status,
        }
        if self.authority_id:
            d["authority_id"] = self.authority_id
        return d

    @property
    def node_type(self) -> str:
        return GKFNodeType.GOVERNING_PRINCIPLE.value

    @property
    def is_active(self) -> bool:
        return self.status == ElementStatus.ACTIVE.value

    @property
    def is_superseded(self) -> bool:
        return self.status == ElementStatus.SUPERSEDED.value


# ---------------------------------------------------------------------------
# Interpretation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Interpretation:
    interpretation_id: str = ""
    governing_principle_id: str = ""
    number: int = 0
    statement: str = ""
    authority: str = ""
    established: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.interpretation_id and self.governing_principle_id:
            object.__setattr__(self, "interpretation_id", generate_interpretation_id(self.governing_principle_id, self.number))
        if not self.established:
            object.__setattr__(self, "established", _now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.INTERPRETATION.value,
            "interpretation_id": self.interpretation_id,
            "governing_principle_id": self.governing_principle_id,
            "number": self.number,
            "statement": self.statement,
            "authority": self.authority,
            "established": self.established,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.INTERPRETATION.value


# ---------------------------------------------------------------------------
# Reference — internal relationship between governed elements
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Reference:
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
# Citation — reference to an external authoritative source (GKF-001A)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Citation:
    """Reference to an external authoritative source.

    Distinct from Reference. Citation points outside the governed collection;
    Reference points inside.
    """
    citation_id: str = ""
    source_id: str = ""
    external_source: str = ""
    external_url: str = ""
    title: str = ""
    authority: str = ""
    excerpt: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.citation_id and self.source_id and self.external_source:
            object.__setattr__(self, "citation_id", generate_citation_id(self.source_id, self.external_source))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.CITATION.value,
            "citation_id": self.citation_id,
            "source_id": self.source_id,
            "external_source": self.external_source,
            "external_url": self.external_url,
            "title": self.title,
            "authority": self.authority,
            "excerpt": self.excerpt,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.CITATION.value


# ---------------------------------------------------------------------------
# Authority — first-class semantic object (GKF-001A)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Authority:
    """A governing authority that establishes or endorses governed knowledge.

    Examples: Founder, Organization, Standards Body, Government, Court.
    """
    authority_id: str = ""
    collection_id: str = ""
    name: str = ""
    authority_type: str = ""
    description: str = ""
    jurisdiction: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.authority_id and self.collection_id and self.name:
            object.__setattr__(self, "authority_id", generate_authority_id(self.collection_id, self.name))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.AUTHORITY.value,
            "authority_id": self.authority_id,
            "collection_id": self.collection_id,
            "name": self.name,
            "authority_type": self.authority_type,
            "description": self.description,
            "jurisdiction": self.jurisdiction,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.AUTHORITY.value


# ---------------------------------------------------------------------------
# Commentary — human explanation, non-binding (GKF-001A)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Commentary:
    """Human explanation of governed knowledge.

    Non-binding. Cannot override a Governing Principle.
    """
    commentary_id: str = ""
    governing_principle_id: str = ""
    number: int = 0
    body: str = ""
    author: str = ""
    established: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.commentary_id and self.governing_principle_id:
            object.__setattr__(self, "commentary_id", generate_commentary_id(self.governing_principle_id, self.number))
        if not self.established:
            object.__setattr__(self, "established", _now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.COMMENTARY.value,
            "commentary_id": self.commentary_id,
            "governing_principle_id": self.governing_principle_id,
            "number": self.number,
            "body": self.body,
            "author": self.author,
            "established": self.established,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.COMMENTARY.value


# ---------------------------------------------------------------------------
# Example — illustrates a Governing Principle (GKF-001A)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Example:
    """Illustrates a Governing Principle.

    Examples never become governing knowledge. They are illustrative only.
    """
    example_id: str = ""
    governing_principle_id: str = ""
    number: int = 0
    body: str = ""
    scenario: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.example_id and self.governing_principle_id:
            object.__setattr__(self, "example_id", generate_example_id(self.governing_principle_id, self.number))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.EXAMPLE.value,
            "example_id": self.example_id,
            "governing_principle_id": self.governing_principle_id,
            "number": self.number,
            "body": self.body,
            "scenario": self.scenario,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.EXAMPLE.value


# ---------------------------------------------------------------------------
# GKFEvidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GKFEvidence:
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
# ImplementationLink — where implemented
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImplementationLink:
    link_id: str = ""
    governing_principle_id: str = ""
    module_path: str = ""
    code_reference: str = ""
    status: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.link_id and self.governing_principle_id and self.module_path:
            object.__setattr__(self, "link_id", generate_implementation_link_id(self.governing_principle_id, self.module_path))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.IMPLEMENTATION_LINK.value,
            "link_id": self.link_id,
            "governing_principle_id": self.governing_principle_id,
            "module_path": self.module_path,
            "code_reference": self.code_reference,
            "status": self.status,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.IMPLEMENTATION_LINK.value


# ---------------------------------------------------------------------------
# ImplementationGuidance — how to satisfy (GKF-001A)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImplementationGuidance:
    """Guidance on how an implementation should satisfy a Governing Principle.

    Implementation Link = WHERE.
    Implementation Guidance = HOW.
    """
    guidance_id: str = ""
    governing_principle_id: str = ""
    name: str = ""
    body: str = ""
    category: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.guidance_id and self.governing_principle_id and self.name:
            object.__setattr__(
                self, "guidance_id",
                generate_implementation_guidance_id(self.governing_principle_id, self.name),
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": GKFNodeType.IMPLEMENTATION_GUIDANCE.value,
            "guidance_id": self.guidance_id,
            "governing_principle_id": self.governing_principle_id,
            "name": self.name,
            "body": self.body,
            "category": self.category,
        }

    @property
    def node_type(self) -> str:
        return GKFNodeType.IMPLEMENTATION_GUIDANCE.value


# ---------------------------------------------------------------------------
# Amendment
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Amendment:
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
# GKFVersion
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GKFVersion:
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