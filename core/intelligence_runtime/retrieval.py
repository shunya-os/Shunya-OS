"""Retrieval Layer — gathers evidence from multiple sources for reasoning."""

from __future__ import annotations

from typing import Any, Callable
from datetime import datetime

from .types import RetrievedEvidence


class RetrievalLayer:
    """Multi-source evidence retrieval. Consumes Business Graph, objects, internet."""

    def __init__(self):
        self._graph_provider = None
        self._object_provider = None
        self._internet_provider = None
        self._memory_provider = None
        self._knowledge_provider = None

    def set_graph_provider(self, fn: Callable) -> None:
        self._graph_provider = fn

    def set_object_provider(self, fn: Callable) -> None:
        self._object_provider = fn

    def set_internet_provider(self, fn: Callable) -> None:
        self._internet_provider = fn

    def set_memory_provider(self, fn: Callable) -> None:
        self._memory_provider = fn

    def set_knowledge_provider(self, fn: Callable) -> None:
        self._knowledge_provider = fn

    def retrieve(self, query: str, module_key: str = "",
                 max_results: int = 10) -> list[RetrievedEvidence]:
        """Retrieve evidence from all available sources."""
        evidence = []

        # 1. Business Graph
        if self._graph_provider and module_key:
            for item in self._graph_provider(query):
                evidence.append(RetrievedEvidence(
                    source="business_graph",
                    content=str(item.get("name", item.get("key", ""))),
                    relevance=0.9,
                    confidence=0.85,
                    metadata=item,
                ))

        # 2. Object instances
        if self._object_provider:
            for item in self._object_provider(query, module_key):
                evidence.append(RetrievedEvidence(
                    source="object",
                    content=str(item.get("name", "")),
                    relevance=0.8,
                    confidence=0.75,
                    metadata=item,
                ))

        # 3. Memory
        if self._memory_provider:
            for item in self._memory_provider(query):
                evidence.append(RetrievedEvidence(
                    source="memory",
                    content=item.content if hasattr(item, 'content') else str(item),
                    relevance=0.7,
                    confidence=item.confidence if hasattr(item, 'confidence') else 0.6,
                    metadata={"key": item.key} if hasattr(item, 'key') else {},
                ))

        # 4. Internet (optional — via canonical WebResearchEngine with provenance)
        if self._internet_provider:
            try:
                safe_results = []
                raw_results = self._internet_provider(query)
                for r in (raw_results or []):
                    # Prompt injection scan
                    from core.web_intelligence import PromptInjectionGuard
                    combined_text = f"{r.get('title', '')} {r.get('snippet', r.get('body', ''))}"
                    injection = PromptInjectionGuard.scan(combined_text)
                    safe_text = PromptInjectionGuard.sanitize(combined_text) if injection else combined_text

                    evidence_item = RetrievedEvidence(
                        source="internet",
                        content=safe_text,
                        relevance=0.5,
                        confidence=0.4,
                        metadata={
                            "url": r.get("url", ""),
                            "title": r.get("title", ""),
                            "provider": r.get("provider", "web"),
                            "retrieved_at": datetime.utcnow().isoformat(),
                            "injection_detected": len(injection) > 0,
                            "injection_patterns": [f["pattern"] for f in injection],
                            "classification": "external",
                        },
                    )
                    safe_results.append(evidence_item)
                evidence.extend(safe_results[:3])
            except Exception:
                pass

        # 5. Knowledge (UCP-04 — canonical knowledge intelligence)
        if self._knowledge_provider:
            for item in self._knowledge_provider(query):
                evidence.append(RetrievedEvidence(
                    source="knowledge",
                    content=str(item.get("content", item.get("summary", ""))),
                    relevance=item.get("relevance", 0.6),
                    confidence=item.get("confidence", 0.7),
                    metadata=item.get("metadata", {}),
                ))

        # Sort by relevance and limit
        evidence.sort(key=lambda e: -e.relevance)
        return evidence[:max_results]

    def clear(self) -> None:
        self._graph_provider = None
        self._object_provider = None
        self._internet_provider = None
        self._memory_provider = None
        self._knowledge_provider = None