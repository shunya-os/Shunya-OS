"""SHUNYA Memory & Knowledge Runtime — Orchestrator."""

from __future__ import annotations

import logging
import time
from typing import Any

from core.memory_knowledge_runtime.models import (
    EmbeddingProvider,
    EvidenceRecord,
    MemoryLifecycleState,
    MemoryObject,
    MemoryStats,
    MemoryTrace,
    MemoryType,
    RelationshipEdge,
    RetrievalQuery,
    SearchResult,
    TimelineEvent,
    _now_iso,
)

logger = logging.getLogger(__name__)


class MemoryKnowledgeRuntime:
    """Universal memory and knowledge layer for all SHUNYA data."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None):
        self._objects: dict[str, MemoryObject] = {}
        self._relationships: list[RelationshipEdge] = []
        self._evidence: list[EvidenceRecord] = []
        self._timeline: list[TimelineEvent] = []
        self._traces: list[MemoryTrace] = []
        self._embedder = embedding_provider or EmbeddingProvider()
        self._key_index: dict[str, dict[str, str]] = {}  # namespace → key → memory_id

    # ── Store ─────────────────────────────────────────────────────────

    def store(
        self,
        key: str,
        value: Any,
        memory_type: MemoryType = MemoryType.OBJECT,
        namespace: str = "default",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        provenance: str = "",
        tenant_id: str = "",
        auto_embed: bool = True,
    ) -> MemoryObject:
        """Store a memory object. Creates or updates by (namespace, key)."""
        start = time.time()
        ns_index = self._key_index.setdefault(namespace, {})
        existing_id = ns_index.get(key)

        if existing_id and existing_id in self._objects:
            obj = self._objects[existing_id]
            obj.value = value
            obj.version += 1
            obj.metadata = metadata or {}
            obj.tags = tags or []
            obj.provenance = provenance or obj.provenance
            obj.updated_at = _now_iso()
        else:
            obj = MemoryObject(
                memory_type=memory_type,
                namespace=namespace,
                key=key,
                value=value,
                metadata=metadata or {},
                tags=tags or [],
                provenance=provenance,
                tenant_id=tenant_id,
            )
            self._objects[obj.memory_id] = obj
            ns_index[key] = obj.memory_id

        # Auto-embed
        if auto_embed and isinstance(value, str):
            obj.embedding = self._embed(value)
        elif auto_embed and isinstance(value, dict):
            text = " ".join(str(v) for v in value.values())
            obj.embedding = self._embed(text)

        obj.lifecycle = MemoryLifecycleState.INDEXED
        self._timeline.append(TimelineEvent(
            memory_id=obj.memory_id,
            event_type="stored",
            payload={"key": key, "memory_type": memory_type.value},
        ))
        latency = (time.time() - start) * 1000
        self._traces.append(MemoryTrace(operation="store", memory_id=obj.memory_id,
                                        namespace=namespace, latency_ms=round(latency, 2)))
        return obj

    def get(self, memory_id: str) -> MemoryObject | None:
        start = time.time()
        obj = self._objects.get(memory_id)
        latency = (time.time() - start) * 1000
        self._traces.append(MemoryTrace(operation="get", memory_id=memory_id,
                                        hit=obj is not None, latency_ms=round(latency, 2)))
        return obj

    def get_by_key(self, key: str, namespace: str = "default") -> MemoryObject | None:
        ns_index = self._key_index.get(namespace, {})
        memory_id = ns_index.get(key)
        return self.get(memory_id) if memory_id else None

    def delete(self, memory_id: str) -> bool:
        obj = self._objects.pop(memory_id, None)
        if obj is None:
            return False
        ns_index = self._key_index.get(obj.namespace, {})
        if ns_index.get(obj.key) == memory_id:
            del ns_index[obj.key]
        self._relationships = [e for e in self._relationships
                               if e.source_id != memory_id and e.target_id != memory_id]
        obj.lifecycle = MemoryLifecycleState.ARCHIVED
        self._timeline.append(TimelineEvent(memory_id=memory_id, event_type="deleted"))
        return True

    # ── Knowledge Graph ───────────────────────────────────────────────

    def relate(self, source_id: str, target_id: str, relationship_type: str,
               weight: float = 1.0, metadata: dict | None = None) -> RelationshipEdge:
        edge = RelationshipEdge(
            source_id=source_id, target_id=target_id,
            relationship_type=relationship_type, weight=weight,
            metadata=metadata or {},
        )
        self._relationships.append(edge)
        for mid in (source_id, target_id):
            obj = self._objects.get(mid)
            if obj and obj.lifecycle == MemoryLifecycleState.INDEXED:
                obj.lifecycle = MemoryLifecycleState.LINKED
        self._timeline.append(TimelineEvent(
            memory_id=source_id, event_type="related",
            payload={"target": target_id, "type": relationship_type},
        ))
        return edge

    def get_relationships(self, memory_id: str) -> list[RelationshipEdge]:
        return [e for e in self._relationships
                if e.source_id == memory_id or e.target_id == memory_id]

    def traverse(self, memory_id: str, relationship_type: str | None = None,
                 max_depth: int = 3) -> list[MemoryObject]:
        """BFS traversal from a memory node."""
        visited: set[str] = set()
        results: list[MemoryObject] = []
        queue = [(memory_id, 0)]
        while queue:
            current, depth = queue.pop(0)
            if current in visited or depth > max_depth:
                continue
            visited.add(current)
            obj = self._objects.get(current)
            if obj and current != memory_id:
                results.append(obj)
            for edge in self._relationships:
                neighbor = None
                if edge.source_id == current:
                    neighbor = edge.target_id
                elif edge.target_id == current:
                    neighbor = edge.source_id
                if neighbor and (relationship_type is None or edge.relationship_type == relationship_type):
                    queue.append((neighbor, depth + 1))
        return results

    # ── Evidence ──────────────────────────────────────────────────────

    def add_evidence(self, memory_id: str, source: str, content: Any,
                     confidence: float = 1.0) -> EvidenceRecord:
        rec = EvidenceRecord(memory_id=memory_id, source=source, content=content, confidence=confidence)
        self._evidence.append(rec)
        return rec

    def get_evidence(self, memory_id: str) -> list[EvidenceRecord]:
        return [e for e in self._evidence if e.memory_id == memory_id]

    # ── Retrieval ─────────────────────────────────────────────────────

    def search(self, query: RetrievalQuery) -> list[SearchResult]:
        """Hybrid search: keyword + semantic."""
        start = time.time()
        results: dict[str, SearchResult] = {}

        # Keyword matching
        q = query.query.lower().split()
        for obj in self._objects.values():
            if query.memory_types is not None and obj.memory_type not in query.memory_types:
                continue
            if query.namespace and obj.namespace != query.namespace:
                continue
            if query.tenant_id and obj.tenant_id != query.tenant_id:
                continue

            text = f"{obj.key} {obj.value}"
            if isinstance(text, str):
                text_lower = text.lower()
                keyword_score = sum(1 for term in q if term in text_lower) / max(len(q), 1)
            else:
                keyword_score = 0.0

            if keyword_score > 0:
                s = results.get(obj.memory_id)
                if s:
                    s.score = max(s.score, keyword_score)
                else:
                    results[obj.memory_id] = SearchResult(
                        memory_id=obj.memory_id, key=obj.key,
                        memory_type=obj.memory_type, score=keyword_score,
                        snippet=str(obj.value)[:200] if obj.value else "",
                        source="keyword",
                    )

        # Semantic similarity (embedding-based)
        if query.query:
            query_emb = self._embed(query.query)
            for obj in self._objects.values():
                if query.memory_types is not None and obj.memory_type not in query.memory_types:
                    continue
                if query.namespace and obj.namespace != query.namespace:
                    continue
                if query.tenant_id and obj.tenant_id != query.tenant_id:
                    continue
                if obj.embedding and query_emb:
                    sim = self._cosine_similarity(query_emb, obj.embedding)
                    if sim >= query.min_score:
                        s = results.get(obj.memory_id)
                        if s:
                            s.score = max(s.score, sim)
                            s.source = "hybrid" if s.source != "keyword" else "keyword"
                        else:
                            results[obj.memory_id] = SearchResult(
                                memory_id=obj.memory_id, key=obj.key,
                                memory_type=obj.memory_type, score=sim,
                                snippet=str(obj.value)[:200] if obj.value else "",
                                source="semantic",
                            )

        # Sort and limit
        sorted_results = sorted(results.values(), key=lambda r: r.score, reverse=True)
        latency = (time.time() - start) * 1000
        self._traces.append(MemoryTrace(operation="search", latency_ms=round(latency, 2)))
        return sorted_results[:query.top_k]

    # ── Timeline ──────────────────────────────────────────────────────

    def get_timeline(self, memory_id: str | None = None,
                     limit: int = 100) -> list[TimelineEvent]:
        events = self._timeline
        if memory_id:
            events = [e for e in events if e.memory_id == memory_id]
        return events[-limit:]

    # ── Stats ─────────────────────────────────────────────────────────

    def get_stats(self) -> MemoryStats:
        by_type: dict[str, int] = {}
        for obj in self._objects.values():
            by_type[obj.memory_type.value] = by_type.get(obj.memory_type.value, 0) + 1
        traces = self._traces
        avg_lat = sum(t.latency_ms for t in traces) / len(traces) if traces else 0
        return MemoryStats(
            total_objects=len(self._objects),
            total_relationships=len(self._relationships),
            total_evidence=len(self._evidence),
            total_timeline_events=len(self._timeline),
            by_type=by_type,
            avg_latency_ms=round(avg_lat, 2),
        )

    # ── Observability ─────────────────────────────────────────────────

    def get_traces(self, limit: int = 100) -> list[MemoryTrace]:
        return self._traces[-limit:]

    def health_check(self) -> dict[str, Any]:
        stats = self.get_stats()
        return {
            "status": "healthy",
            "runtime": "memory_knowledge_runtime",
            "total_objects": stats.total_objects,
            "total_relationships": stats.total_relationships,
            "total_evidence": stats.total_evidence,
            "total_timeline_events": stats.total_timeline_events,
            "by_type": stats.by_type,
            "avg_latency_ms": stats.avg_latency_ms,
        }

    # ── Embedding ─────────────────────────────────────────────────────

    def _embed(self, text: str) -> list[float]:
        """Embed a single text."""
        import asyncio
        return asyncio.run(self._embedder.embed([text]))[0]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        import math
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)