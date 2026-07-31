"""SHUNYA Kernel — Universal Context.

Implements the context model defined in:
    UNIVERSAL_ONTOLOGY.md §13 — Context
    COGNITIVE_WORKSPACE_RUNTIME.md §8 — Context Transition Model

Context is the set of circumstances surrounding an Object, Event, or
Interaction. Context determines meaning. Context is never destroyed
(O-09). Context is always traceable to its source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Context types (from Ontology §13.2)
# ---------------------------------------------------------------------------

class ContextType(str, Enum):
    """Canonical context types from UNIVERSAL_ONTOLOGY.md §13.2."""
    WORKSPACE = "workspace"
    CONVERSATION = "conversation"
    EXECUTION = "execution"
    RELATIONSHIP = "relationship"
    TEMPORAL = "temporal"
    ORGANISATIONAL = "organisational"
    INHERITED = "inherited"


# ---------------------------------------------------------------------------
# Context data
# ---------------------------------------------------------------------------

@dataclass
class ContextData:
    """The data payload for a context entry.

    Attributes:
        type: The context type
        scope: The scope of this context (object_id, conversation_id, etc.)
        data: Arbitrary key-value data
        source: Where this context was resolved from
        confidence: How reliable this context is (0.0 – 1.0)
    """
    type: ContextType
    scope: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    confidence: float = 1.0


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

class Context:
    """The context surrounding an Object, Event, or Interaction.

    Constitutional invariants enforced:
        O-09: Context is never destroyed (may be archived but never deleted)
        O-04: Context is always traceable to its source
        O-21: Inherited context can be overridden but not ignored (CWR §7 I-01)
    """

    def __init__(self, context_id: str, object_id: str):
        self._context_id = context_id
        self._object_id = object_id
        self._entries: Dict[ContextType, ContextData] = {}
        self._parent: Optional[Context] = None
        self._created_at = datetime.now(timezone.utc)
        self._archived = False

    @property
    def context_id(self) -> str:
        return self._context_id

    @property
    def object_id(self) -> str:
        return self._object_id

    @property
    def is_archived(self) -> bool:
        """Whether this context has been archived (O-09: never destroyed)."""
        return self._archived

    def set_parent(self, parent: Context) -> None:
        """Set the parent context for inheritance (Ontology §13.3)."""
        self._parent = parent

    def set(self, data: ContextData) -> None:
        """Set a context entry."""
        self._entries[data.type] = data

    def get(self, context_type: ContextType) -> Optional[ContextData]:
        """Get a context entry, checking inheritance if not found.

        Narrower contexts can override broader contexts (Ontology §13.3).
        """
        entry = self._entries.get(context_type)
        if entry is not None:
            return entry
        # Inherit from parent if not overridden (O-21)
        if self._parent is not None:
            return self._parent.get(context_type)
        return None

    def get_all(self) -> Dict[ContextType, ContextData]:
        """Get all context entries, including inherited ones."""
        result: Dict[ContextType, ContextData] = {}
        if self._parent is not None:
            result.update(self._parent.get_all())
        result.update(self._entries)
        return result

    def archive(self) -> None:
        """Archive this context (O-09: context is never destroyed)."""
        self._archived = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the context for projection."""
        return {
            "context_id": self._context_id,
            "object_id": self._object_id,
            "archived": self._archived,
            "created_at": self._created_at.isoformat(),
            "entries": {
                ct.value: {
                    "scope": cd.scope,
                    "data": cd.data,
                    "source": cd.source,
                    "confidence": cd.confidence,
                }
                for ct, cd in self.get_all().items()
            },
        }


# ---------------------------------------------------------------------------
# Context resolution (from CWR §8, KG §6)
# ---------------------------------------------------------------------------

class ContextResolution:
    """Resolves context for a given object.

    The Context Resolution Engine determines what the founder is currently
    looking at, what surrounds it, and what is relevant — without loading
    the entire graph (KG §6).
    """

    def __init__(self):
        self._contexts: Dict[str, Context] = {}

    def register(self, context: Context) -> None:
        """Register a context for resolution."""
        self._contexts[context.context_id] = context

    def resolve(self, object_id: str) -> Optional[Context]:
        """Resolve the context for a given object.

        Returns the most specific context for the object, or None if
        no context is registered.
        """
        # Find the most specific context for this object
        candidates = [
            ctx for ctx in self._contexts.values()
            if ctx.object_id == object_id and not ctx.is_archived
        ]
        if not candidates:
            return None
        # Return the most recently created context
        return max(candidates, key=lambda ctx: ctx._created_at)

    def resolve_with_depth(
        self, object_id: str, depth: int = 1
    ) -> Dict[str, Any]:
        """Resolve context with neighbourhood depth.

        Returns the object's context plus related contexts up to `depth` hops.
        """
        context = self.resolve(object_id)
        if context is None:
            return {"object_id": object_id, "contexts": {}}

        result = {
            "object_id": object_id,
            "contexts": {context.context_id: context.to_dict()},
        }

        # Add parent contexts (inheritance chain)
        current = context
        for _ in range(depth):
            if current._parent is not None:
                parent = current._parent
                result["contexts"][parent.context_id] = parent.to_dict()
                current = parent
            else:
                break

        return result

    def clear(self) -> None:
        """Clear all registered contexts (for testing)."""
        self._contexts.clear()