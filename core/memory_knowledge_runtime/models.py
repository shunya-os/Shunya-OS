"""SHUNYA Memory & Knowledge Runtime — data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _generate_id() -> str:
    from core.kernel.types import generate_uuid7
    return generate_uuid7()


# ── Memory Types ─────────────────────────────────────────────────────────

class MemoryType(str, Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    OBJECT = "object"


class MemoryLifecycleState(str, Enum):
    CREATED = "created"
    INDEXED = "indexed"
    LINKED = "linked"
    EVOLVED = "evolved"
    ARCHIVED = "archived"


# ── Memory Object ────────────────────────────────────────────────────────

@dataclass
class MemoryObject:
    """A single memory entry — typed, versioned, provenance-tracked."""

    memory_id: str = field(default_factory=_generate_id)
    memory_type: MemoryType = MemoryType.OBJECT
    namespace: str = "default"
    key: str = ""
    value: Any = None
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    provenance: str = ""  # who/what created this memory
    version: int = 1
    lifecycle: MemoryLifecycleState = MemoryLifecycleState.CREATED
    tenant_id: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)


# ── Relationship Edge ────────────────────────────────────────────────────

@dataclass
class RelationshipEdge:
    """A typed edge between two memory objects."""

    edge_id: str = field(default_factory=_generate_id)
    source_id: str = ""
    target_id: str = ""
    relationship_type: str = ""
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)


# ── Evidence Record ──────────────────────────────────────────────────────

@dataclass
class EvidenceRecord:
    """A piece of evidence linked to a memory object."""

    evidence_id: str = field(default_factory=_generate_id)
    memory_id: str = ""
    source: str = ""
    content: Any = None
    confidence: float = 1.0
    verified: bool = False
    created_at: str = field(default_factory=_now_iso)


# ── Timeline Event ───────────────────────────────────────────────────────

@dataclass
class TimelineEvent:
    """A temporal event in the timeline engine."""

    event_id: str = field(default_factory=_generate_id)
    memory_id: str = ""
    event_type: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now_iso)


# ── Search Result ────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    memory_id: str = ""
    key: str = ""
    memory_type: MemoryType = MemoryType.OBJECT
    score: float = 0.0
    snippet: str = ""
    source: str = ""  # "graph" | "semantic" | "keyword" | "hybrid"


# ── Retrieval Query ──────────────────────────────────────────────────────

@dataclass
class RetrievalQuery:
    query: str = ""
    namespace: str = "default"
    memory_types: list[MemoryType] | None = None
    top_k: int = 10
    min_score: float = 0.0
    include_embeddings: bool = False
    tenant_id: str = ""


# ── Embedding Provider Contract ──────────────────────────────────────────

@dataclass
class EmbeddingProvider:
    provider_id: str = ""
    model: str = "default"
    dimensions: int = 128

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts. Override in subclasses."""
        # Simulated: returns random-ish vectors
        import hashlib
        import math
        results = []
        for text in texts:
            h = hashlib.sha256(text.encode()).digest()
            vec = [b / 255.0 for b in h[:self.dimensions]]
            # Normalise
            norm = math.sqrt(sum(v*v for v in vec))
            vec = [v/norm for v in vec] if norm > 0 else vec
            results.append(vec)
        return results


# ── Memory Runtime State ────────────────────────────────────────────────

@dataclass
class MemoryStats:
    total_objects: int = 0
    total_relationships: int = 0
    total_evidence: int = 0
    total_timeline_events: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    avg_latency_ms: float = 0.0


# ── Memory Trace ─────────────────────────────────────────────────────────

@dataclass
class MemoryTrace:
    operation: str = ""
    memory_id: str = ""
    namespace: str = ""
    latency_ms: float = 0.0
    hit: bool = True
    source: str = ""
    timestamp: str = field(default_factory=_now_iso)