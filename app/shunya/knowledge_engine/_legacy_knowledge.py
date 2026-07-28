"""SHUNYA — Legacy backward compatibility for Knowledge Engine.

Wraps the canonical ImmutableKnowledgeStore for existing call sites.
"""

from typing import Any
from app.shunya.knowledge_engine.engine import ImmutableKnowledgeStore, get_knowledge_store


class KnowledgeLayer:
    """Legacy wrapper — delegates to ImmutableKnowledgeStore."""

    def __init__(self):
        self._store = ImmutableKnowledgeStore()

    @property
    def store(self) -> ImmutableKnowledgeStore:
        return self._store

    def get(self, key: str) -> Any:
        r = self._store.get(key)
        return r.value if r else None

    def set(self, key: str, value: Any, **kwargs) -> bool:
        from app.shunya.knowledge_engine.models import KnowledgeInput
        inp = KnowledgeInput(
            fact_key=key, value=value,
            domain=kwargs.get("domain", "general"),
            source=kwargs.get("source", "manual"),
            created_by=kwargs.get("created_by", "legacy"),
            tenant_id=kwargs.get("tenant_id", 1),
        )
        ok, _, _ = self._store.store(inp)
        return ok