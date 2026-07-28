"""SHUNYA Phase A1 — Space Store.

In-memory storage for UniversalSpace instances.
Provides CRUD, search, and relationship-aware lookups.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from app.space.models import (
    SpaceIdentity, SpaceStatus, SpaceContext,
    SpaceRelationshipRef, SpaceTimelineEvent, SpaceKnowledgeItem,
    SpacePlanRef, SpaceExecutionRef, SpaceCommunicationRef,
    SpaceDocumentRef, SpaceResponsibility, SpaceMetric,
    SpaceAIUnderstanding, UniversalSpace,
)


class SpaceStore:
    """In-memory store for UniversalSpace instances.

    All spaces are backed by the Business Graph (app.graph_universal).
    The store provides a lightweight cache/index for the Space layer.
    """

    def __init__(self):
        self._spaces: Dict[str, UniversalSpace] = {}
        self._entity_to_space: Dict[str, str] = {}
        """entity_id -> space_id mapping"""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, entity_id: str, entity_type: str, name: str,
               aliases: Optional[List[str]] = None,
               parent_space_id: str = "",
               capabilities: Optional[List[str]] = None,
               metadata: Optional[Dict[str, Any]] = None) -> UniversalSpace:
        """Create a new UniversalSpace backed by an entity."""
        space_id = f"spc_{uuid.uuid4().hex[:24]}"
        identity = SpaceIdentity(
            space_id=space_id,
            entity_id=entity_id,
            entity_type=entity_type,
            name=name,
            aliases=aliases or [],
        )
        context = SpaceContext(space_id=space_id)
        ai_understanding = SpaceAIUnderstanding()

        # Resolve capabilities from the capability registry
        from app.space.capabilities import get_registry
        cap_registry = get_registry()
        resolved_caps = capabilities or [
            c.name for c in cap_registry.get_capabilities_for(entity_type)
        ]

        space = UniversalSpace(
            identity=identity,
            context=context,
            parent_space_id=parent_space_id,
            ai_understanding=ai_understanding,
            capabilities=resolved_caps,
            metadata=metadata or {},
        )
        self._spaces[space_id] = space
        self._entity_to_space[entity_id] = space_id
        return space

    def get(self, space_id: str) -> Optional[UniversalSpace]:
        return self._spaces.get(space_id)

    def get_by_entity(self, entity_id: str) -> Optional[UniversalSpace]:
        space_id = self._entity_to_space.get(entity_id)
        if space_id:
            return self._spaces.get(space_id)
        return None

    def update(self, space_id: str, **kwargs) -> Optional[UniversalSpace]:
        space = self._spaces.get(space_id)
        if not space:
            return None
        for key, value in kwargs.items():
            if hasattr(space.identity, key):
                setattr(space.identity, key, value)
            elif key == "name":
                space.identity.name = value
            elif key == "status":
                if isinstance(value, str):
                    value = SpaceStatus(value)
                space.identity.status = value
            elif key == "context" and isinstance(value, dict):
                for ck, cv in value.items():
                    if hasattr(space.context, ck):
                        setattr(space.context, ck, cv)
        space.identity.updated_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat()
        return space

    def delete(self, space_id: str) -> bool:
        space = self._spaces.pop(space_id, None)
        if space:
            self._entity_to_space.pop(space.identity.entity_id, None)
            return True
        return False

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def list_all(self) -> List[UniversalSpace]:
        return list(self._spaces.values())

    def list_by_type(self, entity_type: str) -> List[UniversalSpace]:
        return [s for s in self._spaces.values()
                if s.identity.entity_type == entity_type]

    def list_by_status(self, status: SpaceStatus) -> List[UniversalSpace]:
        return [s for s in self._spaces.values()
                if s.identity.status == status]

    def list_children(self, parent_space_id: str) -> List[UniversalSpace]:
        return [s for s in self._spaces.values()
                if s.parent_space_id == parent_space_id]

    def search(self, query: str) -> List[UniversalSpace]:
        """Search spaces by name, aliases, and entity_type."""
        q = query.lower()
        results = []
        for s in self._spaces.values():
            if q in s.identity.name.lower():
                results.append(s)
                continue
            if q in s.identity.entity_type.lower():
                results.append(s)
                continue
            for alias in s.identity.aliases:
                if q in alias.lower():
                    results.append(s)
                    break
        return results

    # ------------------------------------------------------------------
    # Relationship management
    # ------------------------------------------------------------------

    def add_relationship(self, space_id: str,
                         rel: SpaceRelationshipRef) -> bool:
        space = self._spaces.get(space_id)
        if not space:
            return False
        # Deduplicate by rel_id
        space.relationships = [
            r for r in space.relationships if r.rel_id != rel.rel_id
        ]
        space.relationships.append(rel)
        return True

    def get_relationships(self, space_id: str) -> List[SpaceRelationshipRef]:
        space = self._spaces.get(space_id)
        if not space:
            return []
        return list(space.relationships)

    # ------------------------------------------------------------------
    # Timeline management
    # ------------------------------------------------------------------

    def add_timeline_event(self, space_id: str,
                           event: SpaceTimelineEvent) -> bool:
        space = self._spaces.get(space_id)
        if not space:
            return False
        space.timeline.append(event)
        return True

    def get_timeline(self, space_id: str,
                     limit: int = 50,
                     category: str = "") -> List[SpaceTimelineEvent]:
        space = self._spaces.get(space_id)
        if not space:
            return []
        events = space.timeline
        if category:
            events = [e for e in events if e.category == category]
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    # ------------------------------------------------------------------
    # Knowledge management
    # ------------------------------------------------------------------

    def add_knowledge(self, space_id: str,
                      item: SpaceKnowledgeItem) -> bool:
        space = self._spaces.get(space_id)
        if not space:
            return False
        space.knowledge.append(item)
        return True

    def get_knowledge(self, space_id: str,
                      item_type: str = "") -> List[SpaceKnowledgeItem]:
        space = self._spaces.get(space_id)
        if not space:
            return []
        if item_type:
            return [k for k in space.knowledge if k.item_type == item_type]
        return list(space.knowledge)

    # ------------------------------------------------------------------
    # Plan management
    # ------------------------------------------------------------------

    def add_plan(self, space_id: str, plan: SpacePlanRef) -> bool:
        space = self._spaces.get(space_id)
        if not space:
            return False
        space.plans.append(plan)
        return True

    def get_plans(self, space_id: str) -> List[SpacePlanRef]:
        space = self._spaces.get(space_id)
        if not space:
            return []
        return list(space.plans)

    # ------------------------------------------------------------------
    # Execution management
    # ------------------------------------------------------------------

    def add_execution(self, space_id: str,
                      execution: SpaceExecutionRef) -> bool:
        space = self._spaces.get(space_id)
        if not space:
            return False
        space.executions.append(execution)
        return True

    # ------------------------------------------------------------------
    # Communication management
    # ------------------------------------------------------------------

    def add_communication(self, space_id: str,
                          comm: SpaceCommunicationRef) -> bool:
        space = self._spaces.get(space_id)
        if not space:
            return False
        space.communications.append(comm)
        return True

    # ------------------------------------------------------------------
    # Document management
    # ------------------------------------------------------------------

    def add_document(self, space_id: str,
                     doc: SpaceDocumentRef) -> bool:
        space = self._spaces.get(space_id)
        if not space:
            return False
        space.documents.append(doc)
        return True

    # ------------------------------------------------------------------
    # Responsibility management
    # ------------------------------------------------------------------

    def add_responsibility(self, space_id: str,
                           resp: SpaceResponsibility) -> bool:
        space = self._spaces.get(space_id)
        if not space:
            return False
        space.responsibilities.append(resp)
        return True

    # ------------------------------------------------------------------
    # Metric management
    # ------------------------------------------------------------------

    def add_metric(self, space_id: str, metric: SpaceMetric) -> bool:
        space = self._spaces.get(space_id)
        if not space:
            return False
        # Deduplicate by metric_id
        space.metrics = [m for m in space.metrics
                         if m.metric_id != metric.metric_id]
        space.metrics.append(metric)
        return True

    def get_metrics(self, space_id: str) -> List[SpaceMetric]:
        space = self._spaces.get(space_id)
        if not space:
            return []
        return list(space.metrics)

    # ------------------------------------------------------------------
    # AI Understanding
    # ------------------------------------------------------------------

    def update_ai_understanding(self, space_id: str,
                                understanding: SpaceAIUnderstanding) -> bool:
        space = self._spaces.get(space_id)
        if not space:
            return False
        space.ai_understanding = understanding
        return True

    # ------------------------------------------------------------------
    # Space nesting
    # ------------------------------------------------------------------

    def add_child(self, parent_id: str, child_id: str) -> bool:
        parent = self._spaces.get(parent_id)
        child = self._spaces.get(child_id)
        if not parent or not child:
            return False
        if child_id not in parent.child_space_ids:
            parent.child_space_ids.append(child_id)
        child.parent_space_id = parent_id
        return True

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    def set_permission(self, space_id: str, identity_id: str,
                       roles: List[str]) -> bool:
        space = self._spaces.get(space_id)
        if not space:
            return False
        space.permissions[identity_id] = roles
        return True

    def check_permission(self, space_id: str, identity_id: str,
                         required_role: str) -> bool:
        space = self._spaces.get(space_id)
        if not space:
            return False
        roles = space.permissions.get(identity_id, [])
        return required_role in roles

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def count(self) -> int:
        return len(self._spaces)

    def clear(self) -> None:
        self._spaces.clear()
        self._entity_to_space.clear()


# =========================================================================
# Singleton
# =========================================================================

_store: Optional[SpaceStore] = None


def get_store() -> SpaceStore:
    global _store
    if _store is None:
        _store = SpaceStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None