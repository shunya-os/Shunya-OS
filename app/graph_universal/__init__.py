"""Compatibility stub — graph_universal archived during Phase 1 consolidation.

Original files: _archive/graph_variants/graph_universal/
This stub provides no-op fallbacks for reality_engine and other dormant modules.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Entity:
    def __init__(self, **kw):
        self.id = kw.get("id", "")
        self.type = kw.get("type", "unknown")
        self.properties = kw.get("properties", {})


class Relationship:
    def __init__(self, **kw):
        self.source_id = kw.get("source_id", "")
        self.target_id = kw.get("target_id", "")
        self.type = kw.get("type", "unknown")


class InMemoryStore:
    def __init__(self):
        self._items = {}

    def get(self, key, default=None):
        return self._items.get(key, default)

    def put(self, key, value):
        self._items[key] = value

    def all(self):
        return list(self._items.values())

    def search(self, **kw):
        return []


_store = InMemoryStore()


def get_store():
    return _store


class GraphQueryEngine:
    def query(self, *a, **kw):
        return {"nodes": [], "edges": []}


class PropertyVersion:
    """Compatibility stub — original archived."""
    def __init__(self, **kw):
        self.id = kw.get("id", "")
        self.property_name = kw.get("property_name", "")
        self.value = kw.get("value")
        self.version = kw.get("version", 1)


class GraphEvent:
    """Compatibility stub — original archived."""
    def __init__(self, **kw):
        self.id = kw.get("id", "")
        self.event_type = kw.get("event_type", "unknown")
        self.object_id = kw.get("object_id", "")
        self.payload = kw.get("payload", {})


def get_engine():
    return GraphQueryEngine()


class IdentityResolver:
    """Compatibility stub — original archived."""
    def resolve(self, identifier, **kw):
        return {"id": identifier, "type": "unknown"}


def get_resolver():
    return lambda x: x


def reset_store():
    """Compatibility stub — no-op. Original store is archived."""
    global _store
    _store = InMemoryStore()
    logger.debug("graph_universal stub: reset_store (no-op)")


def reset_resolver():
    """Compatibility stub — no-op. Original resolver is archived."""
    logger.debug("graph_universal stub: reset_resolver (no-op)")


def reset_engine():
    """Compatibility stub — no-op. Original engine is archived."""
    logger.debug("graph_universal stub: reset_engine (no-op)")