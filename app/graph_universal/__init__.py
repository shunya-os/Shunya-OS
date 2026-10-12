"""Compatibility layer — graph_universal consolidated into this package.

Original files: _archive/graph_variants/graph_universal/
This module provides the in-memory graph store and query engine used by
reality_engine and other consumers. Submodules (entity, relationship,
traversal, identity, property, event) hold the real implementations.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Entity:
    def __init__(self, **kw):
        self.id = kw.get("id", "")
        self.type = kw.get("type", "unknown")
        self.properties = kw.get("properties", {})
        for k, v in kw.items():
            if k not in ("id", "type", "properties"):
                setattr(self, k, v)


class Relationship:
    def __init__(self, **kw):
        self.source_id = kw.get("source_id", "")
        self.target_id = kw.get("target_id", "")
        self.type = kw.get("type", "unknown")


class InMemoryStore:
    """In-memory graph store with put/get/all and real search support."""

    def __init__(self):
        self._items = {}

    def get(self, key, default=None):
        return self._items.get(key, default)

    def put(self, key, value):
        self._items[key] = value

    def all(self):
        return list(self._items.values())

    def search(self, **kw):
        """Search stored items by attribute/dict-key filters or free text.

        Behavior:
          - ``q`` or ``query`` kwarg  → case-insensitive substring match
            against the item's string form / id / type / name / properties.
          - Other kwargs are treated as exact filters: an item matches when it
            is a dict containing the key with an equal (or string-equal) value,
            OR the item exposes a matching attribute, OR its ``properties``
            dict contains a matching value.

        Returns a list of matching stored items (possibly empty).
        """
        text_query = str(kw.pop("q", kw.pop("query", "")) or "").strip().lower()
        filters = {k: v for k, v in kw.items() if v is not None}

        results = []
        for item in self._items.values():
            if self._matches(item, filters, text_query):
                results.append(item)
        return results

    def _matches(self, item, filters: dict, text_query: str) -> bool:
        # Free-text match
        if text_query:
            haystack = self._to_text(item).lower()
            if all(part in haystack for part in text_query.split()):
                return True
            return False  # no other filter can rescue a missed text query
        # Exact attribute/dict-key filters
        for key, expected in filters.items():
            actual = self._get_value(item, key)
            if actual is None:
                return False
            if actual != expected and str(actual) != str(expected):
                return False
        return True

    @staticmethod
    def _get_value(item, key):
        """Resolve a value from a dict-like, an object, or its properties map."""
        if isinstance(item, dict):
            if key in item:
                return item[key]
        else:
            if hasattr(item, key):
                try:
                    return getattr(item, key)
                except Exception:
                    pass
            props = getattr(item, "properties", None)
            if isinstance(props, dict) and key in props:
                return props[key]
        return None

    @staticmethod
    def _to_text(item) -> str:
        parts = []
        if isinstance(item, dict):
            parts.append(str(item))
        else:
            for attr in ("id", "type", "name", "title", "description"):
                val = getattr(item, attr, None)
                if val:
                    parts.append(str(val))
            props = getattr(item, "properties", None)
            if isinstance(props, dict):
                parts.append(str(props))
            if not parts:
                parts.append(str(item))
        return " ".join(parts)


_store = InMemoryStore()


def get_store():
    return _store


class GraphQueryEngine:
    """Query the in-memory graph store for nodes and edges."""

    def query(self, *a, **kw):
        """Return nodes/edges from the store.

        Accepts optional ``entity_type`` / ``type`` filters; with no filters,
        returns all stored items as nodes (edges grouped by relationship type).
        """
        store = get_store()
        entity_type = kw.get("entity_type") or kw.get("type")
        nodes = []
        edges = []
        for item in store.all():
            if entity_type:
                t = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)
                if t and t != entity_type:
                    continue
            if isinstance(item, Relationship) or (
                    isinstance(item, dict) and "source_id" in item and "target_id" in item):
                edges.append(item)
            else:
                nodes.append(item)
        return {"nodes": nodes, "edges": edges}


def get_engine():
    return GraphQueryEngine()


def get_resolver():
    return lambda x: x