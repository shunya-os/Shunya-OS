"""Universal Knowledge Intelligence — Data Models.

Living Object dataclasses for the universal knowledge capability.
Every model has to_dict() for serialization.

Knowledge Intelligence models how humans and organizations acquire, organize,
validate, connect, reason about and continuously evolve knowledge.

It does NOT model a wiki, document storage, or note taking.
Knowledge are Living Knowledge Objects connected to Reality.

UCP-04 — Universal Knowledge Intelligence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _generate_id() -> str:
    import uuid
    return str(uuid.uuid4())


# ── Enums ─────────────────────────────────────────────────────────────────

class KnowledgeType(str, Enum):
    """Canonical knowledge types — universal, not domain-specific."""
    FACT = "fact"
    CONCEPT = "concept"
    DEFINITION = "definition"
    PROCEDURE = "procedure"
    SOP = "sop"
    POLICY = "policy"
    RESEARCH = "research"
    DECISION = "decision"
    ASSUMPTION = "assumption"
    EVIDENCE = "evidence"
    LESSON_LEARNED = "lesson_learned"
    BEST_PRACTICE = "best_practice"
    OBSERVATION = "observation"
    QUESTION = "question"
    HYPOTHESIS = "hypothesis"
    REFERENCE = "reference"
    PRINCIPLE = "principle"
    GUIDELINE = "guideline"
    TIP = "tip"


class ConfidenceLevel(str, Enum):
    """Confidence in a piece of knowledge."""
    UNVERIFIED = "unverified"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class KnowledgeRelationship(str, Enum):
    """Canonical relationship types between knowledge objects."""
    DERIVED_FROM = "derived_from"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    REFINES = "refines"
    GENERALIZES = "generalizes"
    SPECIALIZES = "specializes"
    PREREQUISITE = "prerequisite"
    EVIDENCE_FOR = "evidence_for"
    EVIDENCE_AGAINST = "evidence_against"
    SOURCE_OF = "source_of"
    REFERENCES = "references"
    RELATED_TO = "related_to"
    CAUSES = "causes"
    REQUIRES = "requires"
    APPLIES_TO = "applies_to"
    EVOLVED_INTO = "evolved_into"
    QUESTIONS = "questions"
    ANSWERS = "answers"


class SourceType(str, Enum):
    """Types of knowledge sources."""
    HUMAN = "human"
    DOCUMENT = "document"
    RESEARCH_PAPER = "research_paper"
    INTERNET = "internet"
    SYSTEM = "system"
    AI_GENERATED = "ai_generated"
    EXPERIMENT = "experiment"
    OBSERVATION = "observation"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    BOOK = "book"
    ARTICLE = "article"
    REPORT = "report"
    CONVERSATION = "conversation"
    MEETING = "meeting"
    INFERENCE = "inference"


class GapSeverity(str, Enum):
    """Severity of a knowledge gap."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ── Data Models ────────────────────────────────────────────────────────────

@dataclass
class KnowledgeSource:
    """Origin of a piece of knowledge."""
    source_id: str = field(default_factory=_generate_id)
    source_type: str = SourceType.HUMAN.value
    name: str = ""
    url: str = ""
    author: str = ""
    published_date: str = ""
    retrieval_date: str = field(default_factory=_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "name": self.name,
            "url": self.url,
            "author": self.author,
            "published_date": self.published_date,
            "retrieval_date": self.retrieval_date,
            "metadata": dict(self.metadata),
        }


@dataclass
class KnowledgeLink:
    """A typed link between two knowledge objects."""
    link_id: str = field(default_factory=_generate_id)
    source_knowledge_id: str = ""
    target_knowledge_id: str = ""
    relationship: str = KnowledgeRelationship.RELATED_TO.value
    strength: float = 1.0
    evidence: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "link_id": self.link_id,
            "source_knowledge_id": self.source_knowledge_id,
            "target_knowledge_id": self.target_knowledge_id,
            "relationship": self.relationship,
            "strength": self.strength,
            "evidence": self.evidence,
            "created_at": self.created_at,
        }


@dataclass
class Knowledge:
    """A Living Knowledge Object — the atomic unit of knowledge.

    Not a wiki page, not a note, not a document.
    A Knowledge object is a self-contained piece of understanding
    with full provenance, confidence, lineage, and connectivity.
    """
    knowledge_id: str = field(default_factory=_generate_id)
    knowledge_type: str = KnowledgeType.FACT.value
    title: str = ""
    statement: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    domain: str = ""
    context: str = ""
    confidence: str = ConfidenceLevel.UNVERIFIED.value
    confidence_score: float = 0.0
    freshness_score: float = 1.0
    sources: list[KnowledgeSource] = field(default_factory=list)
    links: list[KnowledgeLink] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    owner_id: str = ""
    is_active: bool = True
    version: int = 1
    review_by: str = ""
    review_notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def is_due_for_review(self) -> bool:
        from datetime import datetime, timezone, timedelta
        if not self.review_by:
            return False
        try:
            review_dt = datetime.fromisoformat(self.review_by.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > review_dt
        except (ValueError, TypeError):
            return False

    @property
    def has_contradictions(self) -> bool:
        return any(
            link.relationship == KnowledgeRelationship.CONTRADICTS.value
            for link in self.links
        )

    @property
    def confidence_label(self) -> str:
        return self.confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "knowledge_type": self.knowledge_type,
            "title": self.title,
            "statement": self.statement,
            "summary": self.summary,
            "tags": list(self.tags),
            "domain": self.domain,
            "context": self.context,
            "confidence": self.confidence,
            "confidence_score": self.confidence_score,
            "freshness_score": self.freshness_score,
            "sources": [s.to_dict() for s in self.sources],
            "links": [l.to_dict() for l in self.links],
            "evidence_ids": list(self.evidence_ids),
            "owner_id": self.owner_id,
            "is_active": self.is_active,
            "version": self.version,
            "review_by": self.review_by,
            "review_notes": self.review_notes,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_due_for_review": self.is_due_for_review,
            "has_contradictions": self.has_contradictions,
        }


@dataclass
class KnowledgeGraph:
    """A graph of knowledge nodes and their connections."""
    graph_id: str = field(default_factory=_generate_id)
    nodes: list[Knowledge] = field(default_factory=list)
    edges: list[KnowledgeLink] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class KnowledgeGap:
    """A detected gap in knowledge."""
    gap_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    severity: str = GapSeverity.MEDIUM.value
    domain: str = ""
    related_knowledge_ids: list[str] = field(default_factory=list)
    reason: str = ""
    resolution_suggestion: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    detected_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "domain": self.domain,
            "related_knowledge_ids": list(self.related_knowledge_ids),
            "reason": self.reason,
            "resolution_suggestion": self.resolution_suggestion,
            "evidence": list(self.evidence),
            "metadata": dict(self.metadata),
            "detected_at": self.detected_at,
        }


@dataclass
class Contradiction:
    """A detected contradiction between two pieces of knowledge."""
    contradiction_id: str = field(default_factory=_generate_id)
    knowledge_id_a: str = ""
    knowledge_id_b: str = ""
    title_a: str = ""
    title_b: str = ""
    statement_a: str = ""
    statement_b: str = ""
    contradiction_type: str = "direct"  # direct, implied, temporal, contextual
    severity: str = "medium"
    resolution: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    resolved: bool = False
    detected_at: str = field(default_factory=_now_iso)
    resolved_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "contradiction_id": self.contradiction_id,
            "knowledge_id_a": self.knowledge_id_a,
            "knowledge_id_b": self.knowledge_id_b,
            "title_a": self.title_a,
            "title_b": self.title_b,
            "statement_a": self.statement_a,
            "statement_b": self.statement_b,
            "contradiction_type": self.contradiction_type,
            "severity": self.severity,
            "resolution": self.resolution,
            "evidence": list(self.evidence),
            "resolved": self.resolved,
            "detected_at": self.detected_at,
            "resolved_at": self.resolved_at,
        }


@dataclass
class KnowledgeRecommendation:
    """A recommendation for missing or needed knowledge."""
    rec_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    priority: str = "medium"
    reason: str = ""
    related_knowledge: list[str] = field(default_factory=list)
    suggested_source_types: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    is_addressed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rec_id": self.rec_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "reason": self.reason,
            "related_knowledge": list(self.related_knowledge),
            "suggested_source_types": list(self.suggested_source_types),
            "evidence": list(self.evidence),
            "is_addressed": self.is_addressed,
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }


@dataclass
class SearchResult:
    """A semantic search result."""
    result_id: str = field(default_factory=_generate_id)
    knowledge_id: str = ""
    title: str = ""
    summary: str = ""
    knowledge_type: str = ""
    relevance_score: float = 0.0
    confidence_score: float = 0.0
    matched_terms: list[str] = field(default_factory=list)
    context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "knowledge_id": self.knowledge_id,
            "title": self.title,
            "summary": self.summary,
            "knowledge_type": self.knowledge_type,
            "relevance_score": self.relevance_score,
            "confidence_score": self.confidence_score,
            "matched_terms": list(self.matched_terms),
            "context": self.context,
        }


@dataclass
class KnowledgeProfile:
    """A knowledge profile for an entity (person, org, domain).

    The primary accessor — the living intelligence for knowledge.
    """
    profile_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    label: str = ""
    knowledge_objects: list[Knowledge] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    gaps: list[KnowledgeGap] = field(default_factory=list)
    recommendations: list[KnowledgeRecommendation] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def total_knowledge(self) -> int:
        return len(self.knowledge_objects)

    @property
    def active_knowledge(self) -> list[Knowledge]:
        return [k for k in self.knowledge_objects if k.is_active]

    @property
    def knowledge_by_type(self) -> dict[str, list[Knowledge]]:
        result: dict[str, list[Knowledge]] = {}
        for k in self.knowledge_objects:
            result.setdefault(k.knowledge_type, []).append(k)
        return result

    @property
    def average_confidence(self) -> float:
        scores = [k.confidence_score for k in self.knowledge_objects if k.is_active]
        return sum(scores) / len(scores) if scores else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "owner_id": self.owner_id,
            "label": self.label,
            "knowledge_objects": [k.to_dict() for k in self.knowledge_objects],
            "contradictions": [c.to_dict() for c in self.contradictions],
            "gaps": [g.to_dict() for g in self.gaps],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "domains": list(self.domains),
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "total_knowledge": self.total_knowledge,
            "active_knowledge": len(self.active_knowledge),
            "average_confidence": round(self.average_confidence, 2),
        }