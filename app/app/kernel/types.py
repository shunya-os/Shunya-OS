"""SHUNYA Kernel — Universal Type System.

Implements the canonical type hierarchy defined in UNIVERSAL_ONTOLOGY.md §18.
Every Object in SHUNYA has exactly one type. Type is immutable after creation.
The TypeRegistry is the single source of truth for all valid types.

Constitutional references:
    UNIVERSAL_ONTOLOGY.md §18 — Universal Type System
    UNIVERSAL_ONTOLOGY.md §18.4 — Per-type lifecycle mapping
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Type groups — families of types with shared lifecycle constraints
# ---------------------------------------------------------------------------

class TypeGroup(str, Enum):
    """Canonical type groups from UNIVERSAL_ONTOLOGY.md §18.4.4."""
    ENTITY = "entity"
    EVENT = "event"
    COMMITMENT = "commitment"
    ACTION = "action"
    EVIDENCE = "evidence"
    KNOWLEDGE = "knowledge"
    PREDICTION = "prediction"
    POLICY = "policy"
    CONVERSATION = "conversation"
    MEMORY = "memory"
    CONTEXT = "context"


# ---------------------------------------------------------------------------
# Universal lifecycle states (from CWR §6, Ontology §11)
# ---------------------------------------------------------------------------

class LifecycleState(str, Enum):
    """Canonical lifecycle states from COGNITIVE_WORKSPACE_RUNTIME.md §6."""
    CREATE = "create"
    OBSERVE = "observe"
    ENRICH = "enrich"
    RELATE = "relate"
    PREDICT = "predict"
    EXECUTE = "execute"
    ARCHIVE = "archive"
    RESTORE = "restore"
    DELETE = "delete"


# ---------------------------------------------------------------------------
# Type group lifecycle mapping (from Ontology §18.4.4)
# ---------------------------------------------------------------------------

# States that are restricted for each type group
_TYPE_GROUP_RESTRICTIONS: Dict[TypeGroup, Set[LifecycleState]] = {
    TypeGroup.ENTITY: {LifecycleState.PREDICT, LifecycleState.EXECUTE},
    TypeGroup.EVENT: set(LifecycleState),  # ALL states restricted — events are CREATE only
    TypeGroup.COMMITMENT: set(),           # Full lifecycle — no restrictions
    TypeGroup.ACTION: set(),               # Full lifecycle
    TypeGroup.EVIDENCE: set(LifecycleState),  # CREATE only
    TypeGroup.KNOWLEDGE: {LifecycleState.PREDICT, LifecycleState.EXECUTE},
    TypeGroup.PREDICTION: {LifecycleState.PREDICT},  # predictions aren't predicted about
    TypeGroup.POLICY: {LifecycleState.PREDICT, LifecycleState.EXECUTE},
    TypeGroup.CONVERSATION: {LifecycleState.PREDICT, LifecycleState.EXECUTE},
    TypeGroup.MEMORY: {LifecycleState.PREDICT, LifecycleState.EXECUTE},
    TypeGroup.CONTEXT: {LifecycleState.PREDICT, LifecycleState.EXECUTE},
}


# ---------------------------------------------------------------------------
# Type node — a single type in the inheritance tree
# ---------------------------------------------------------------------------

@dataclass
class TypeNode:
    """A single type in the Universal Type System hierarchy.

    Attributes:
        name: Canonical type name (e.g., "Person", "Document")
        parent: Parent type name, or None for root
        group: The type group this type belongs to
        description: Human-readable description
        abstract: If True, this type cannot be instantiated directly
    """
    name: str
    parent: Optional[str]
    group: TypeGroup
    description: str = ""
    abstract: bool = False


# ---------------------------------------------------------------------------
# Type group lifecycle — which states are valid for a group
# ---------------------------------------------------------------------------

@dataclass
class TypeGroupLifecycle:
    """Lifecycle constraints for a type group.

    Attributes:
        group: The type group
        valid_states: States that are valid for this group
        restricted_states: States that are explicitly forbidden
        transitions: Valid state transitions (source -> [targets])
    """
    group: TypeGroup
    valid_states: Set[LifecycleState]
    restricted_states: Set[LifecycleState]
    transitions: Dict[LifecycleState, List[LifecycleState]]


# ---------------------------------------------------------------------------
# Universal transition map (from CWR §6.3)
# ---------------------------------------------------------------------------

_UNIVERSAL_TRANSITIONS: Dict[LifecycleState, List[LifecycleState]] = {
    LifecycleState.CREATE: [LifecycleState.OBSERVE],
    LifecycleState.OBSERVE: [LifecycleState.ENRICH],
    LifecycleState.ENRICH: [LifecycleState.RELATE],
    LifecycleState.RELATE: [LifecycleState.PREDICT],
    LifecycleState.PREDICT: [LifecycleState.EXECUTE],
    LifecycleState.EXECUTE: [LifecycleState.OBSERVE, LifecycleState.ARCHIVE],
    LifecycleState.ARCHIVE: [LifecycleState.RESTORE, LifecycleState.DELETE],
    LifecycleState.RESTORE: [LifecycleState.OBSERVE],
    LifecycleState.DELETE: [],  # terminal
}


# ---------------------------------------------------------------------------
# Type registry (singleton)
# ---------------------------------------------------------------------------

class TypeRegistry:
    """Canonical type registry. Single source of truth for all valid types.

    Constitutional references:
        UNIVERSAL_ONTOLOGY.md §18.1 — Canonical inheritance tree
        UNIVERSAL_ONTOLOGY.md §18.4 — Per-type lifecycle mapping
    """

    def __init__(self):
        self._types: Dict[str, TypeNode] = {}
        self._initialized = False

    def register(self, node: TypeNode) -> None:
        """Register a type in the hierarchy.

        Raises ValueError if:
            - A type with the same name already exists
            - The parent type does not exist (unless parent is None for root)
        """
        if node.name in self._types:
            raise ValueError(f"Type '{node.name}' is already registered")
        if node.parent is not None and node.parent not in self._types:
            raise ValueError(
                f"Parent type '{node.parent}' for '{node.name}' is not registered"
            )
        self._types[node.name] = node

    def get(self, name: str) -> Optional[TypeNode]:
        """Get a type by name. Returns None if not found."""
        return self._types.get(name)

    def get_group(self, name: str) -> Optional[TypeGroup]:
        """Get the type group for a type name. Returns None if not found."""
        node = self._types.get(name)
        return node.group if node else None

    def get_children(self, parent_name: str) -> List[TypeNode]:
        """Get all direct children of a type."""
        return [
            t for t in self._types.values()
            if t.parent == parent_name
        ]

    def get_descendants(self, type_name: str) -> List[TypeNode]:
        """Get all descendants of a type (recursive)."""
        result: List[TypeNode] = []
        children = self.get_children(type_name)
        for child in children:
            result.append(child)
            result.extend(self.get_descendants(child.name))
        return result

    def get_lifecycle(self, type_name: str) -> Optional[TypeGroupLifecycle]:
        """Get the lifecycle constraints for a type's group."""
        node = self._types.get(type_name)
        if node is None:
            return None
        return self._build_group_lifecycle(node.group)

    def validate_state(self, type_name: str, state: LifecycleState) -> bool:
        """Check if a state is valid for the given type."""
        lifecycle = self.get_lifecycle(type_name)
        if lifecycle is None:
            return False
        return state in lifecycle.valid_states

    def validate_transition(
        self, type_name: str, from_state: LifecycleState, to_state: LifecycleState
    ) -> bool:
        """Check if a transition is valid for the given type."""
        lifecycle = self.get_lifecycle(type_name)
        if lifecycle is None:
            return False
        allowed = lifecycle.transitions.get(from_state, [])
        return to_state in allowed

    def is_terminal(self, state: LifecycleState) -> bool:
        """Check if a state is terminal (absorbing)."""
        return len(_UNIVERSAL_TRANSITIONS.get(state, [])) == 0

    @property
    def all_types(self) -> List[TypeNode]:
        """Get all registered types."""
        return list(self._types.values())

    @property
    def count(self) -> int:
        """Number of registered types."""
        return len(self._types)

    def initialize_defaults(self) -> None:
        """Register the canonical type hierarchy from Ontology §18.1."""
        if self._initialized:
            return

        # Root
        self.register(TypeNode("Object", parent=None, group=TypeGroup.CONTEXT,
                               description="Root of the Universal Type System", abstract=True))

        # Entity group
        self.register(TypeNode("Entity", parent="Object", group=TypeGroup.ENTITY,
                               description="A real-world thing", abstract=True))
        self.register(TypeNode("Person", parent="Entity", group=TypeGroup.ENTITY,
                               description="An individual human"))
        self.register(TypeNode("Organization", parent="Entity", group=TypeGroup.ENTITY,
                               description="A group of people", abstract=True))
        self.register(TypeNode("Company", parent="Organization", group=TypeGroup.ENTITY,
                               description="A business entity"))
        self.register(TypeNode("Team", parent="Organization", group=TypeGroup.ENTITY,
                               description="A team within an organization"))
        self.register(TypeNode("Department", parent="Organization", group=TypeGroup.ENTITY,
                               description="A department within an organization"))
        self.register(TypeNode("Document", parent="Entity", group=TypeGroup.ENTITY,
                               description="A file or record"))
        self.register(TypeNode("Meeting", parent="Entity", group=TypeGroup.ENTITY,
                               description="A scheduled gathering"))
        self.register(TypeNode("Project", parent="Entity", group=TypeGroup.ENTITY,
                               description="A planned endeavour"))
        self.register(TypeNode("Workspace", parent="Entity", group=TypeGroup.ENTITY,
                               description="A context container"))

        # Relationship group
        self.register(TypeNode("Relationship", parent="Object", group=TypeGroup.CONTEXT,
                               description="A connection between two Objects", abstract=True))
        self.register(TypeNode("Employment", parent="Relationship", group=TypeGroup.CONTEXT))
        self.register(TypeNode("Ownership", parent="Relationship", group=TypeGroup.CONTEXT))
        self.register(TypeNode("Membership", parent="Relationship", group=TypeGroup.CONTEXT))
        self.register(TypeNode("Contractual", parent="Relationship", group=TypeGroup.CONTEXT))
        self.register(TypeNode("Social", parent="Relationship", group=TypeGroup.CONTEXT))

        # Event group
        self.register(TypeNode("Event", parent="Object", group=TypeGroup.EVENT,
                               description="Something that changes reality", abstract=True))
        self.register(TypeNode("Creation", parent="Event", group=TypeGroup.EVENT))
        self.register(TypeNode("Modification", parent="Event", group=TypeGroup.EVENT))
        self.register(TypeNode("Communication", parent="Event", group=TypeGroup.EVENT))
        self.register(TypeNode("Decision", parent="Event", group=TypeGroup.EVENT))
        self.register(TypeNode("ExecutionOccurrence", parent="Event", group=TypeGroup.EVENT))
        self.register(TypeNode("Failure", parent="Event", group=TypeGroup.EVENT))
        self.register(TypeNode("Resolution", parent="Event", group=TypeGroup.EVENT))

        # Commitment group
        self.register(TypeNode("Commitment", parent="Object", group=TypeGroup.COMMITMENT,
                               description="An obligation between parties", abstract=True))
        self.register(TypeNode("Promise", parent="Commitment", group=TypeGroup.COMMITMENT))
        self.register(TypeNode("Obligation", parent="Commitment", group=TypeGroup.COMMITMENT))
        self.register(TypeNode("Agreement", parent="Commitment", group=TypeGroup.COMMITMENT))
        self.register(TypeNode("Deadline", parent="Commitment", group=TypeGroup.COMMITMENT))

        # Action group
        self.register(TypeNode("Action", parent="Object", group=TypeGroup.ACTION,
                               description="A unit of work", abstract=True))
        self.register(TypeNode("Task", parent="Action", group=TypeGroup.ACTION))
        self.register(TypeNode("Execution", parent="Action", group=TypeGroup.ACTION))
        self.register(TypeNode("Operation", parent="Action", group=TypeGroup.ACTION))
        self.register(TypeNode("Workflow", parent="Action", group=TypeGroup.ACTION))

        # Evidence group
        self.register(TypeNode("Evidence", parent="Object", group=TypeGroup.EVIDENCE,
                               description="Verified observation", abstract=True))
        self.register(TypeNode("Observation", parent="Evidence", group=TypeGroup.EVIDENCE))
        self.register(TypeNode("Verification", parent="Evidence", group=TypeGroup.EVIDENCE))
        self.register(TypeNode("Source", parent="Evidence", group=TypeGroup.EVIDENCE))

        # Knowledge group
        self.register(TypeNode("Knowledge", parent="Object", group=TypeGroup.KNOWLEDGE,
                               description="Validated understanding", abstract=True))
        self.register(TypeNode("Fact", parent="Knowledge", group=TypeGroup.KNOWLEDGE))
        self.register(TypeNode("Inference", parent="Knowledge", group=TypeGroup.KNOWLEDGE))
        self.register(TypeNode("Rule", parent="Knowledge", group=TypeGroup.KNOWLEDGE))
        self.register(TypeNode("Pattern", parent="Knowledge", group=TypeGroup.KNOWLEDGE))

        # Prediction group
        self.register(TypeNode("Prediction", parent="Object", group=TypeGroup.PREDICTION,
                               description="Estimate of future state", abstract=True))
        self.register(TypeNode("Forecast", parent="Prediction", group=TypeGroup.PREDICTION))
        self.register(TypeNode("Risk", parent="Prediction", group=TypeGroup.PREDICTION))
        self.register(TypeNode("Opportunity", parent="Prediction", group=TypeGroup.PREDICTION))
        self.register(TypeNode("Trend", parent="Prediction", group=TypeGroup.PREDICTION))

        # Policy group
        self.register(TypeNode("Policy", parent="Object", group=TypeGroup.POLICY,
                               description="A rule that governs behaviour", abstract=True))
        self.register(TypeNode("Constitutional", parent="Policy", group=TypeGroup.POLICY))
        self.register(TypeNode("Runtime", parent="Policy", group=TypeGroup.POLICY))
        self.register(TypeNode("Business", parent="Policy", group=TypeGroup.POLICY))
        self.register(TypeNode("Personal", parent="Policy", group=TypeGroup.POLICY))

        # Conversation group
        self.register(TypeNode("Conversation", parent="Object", group=TypeGroup.CONVERSATION,
                               description="An exchange of messages", abstract=True))
        self.register(TypeNode("Message", parent="Conversation", group=TypeGroup.CONVERSATION))
        self.register(TypeNode("Thread", parent="Conversation", group=TypeGroup.CONVERSATION))
        self.register(TypeNode("Transcript", parent="Conversation", group=TypeGroup.CONVERSATION))

        # Context group
        self.register(TypeNode("Context", parent="Object", group=TypeGroup.CONTEXT,
                               description="Circumstances surrounding an Object", abstract=True))
        self.register(TypeNode("WorkspaceContext", parent="Context", group=TypeGroup.CONTEXT,
                               description="The context of a workspace"))
        self.register(TypeNode("ExecutionContext", parent="Context", group=TypeGroup.CONTEXT,
                               description="The context of an execution"))
        self.register(TypeNode("Temporal", parent="Context", group=TypeGroup.CONTEXT,
                               description="Temporal context"))
        self.register(TypeNode("Organisational", parent="Context", group=TypeGroup.CONTEXT,
                               description="Organisational context"))

        self._initialized = True

    def _build_group_lifecycle(self, group: TypeGroup) -> TypeGroupLifecycle:
        """Build the lifecycle constraints for a type group."""
        restricted = _TYPE_GROUP_RESTRICTIONS.get(group, set())
        all_states = set(LifecycleState)

        if group == TypeGroup.EVENT:
            # Events are CREATE only, then immutable
            valid_states = {LifecycleState.CREATE}
        elif group == TypeGroup.EVIDENCE:
            valid_states = {LifecycleState.CREATE}
        else:
            valid_states = all_states - restricted

        # Build transitions — remove restricted target states
        transitions: Dict[LifecycleState, List[LifecycleState]] = {}
        for source, targets in _UNIVERSAL_TRANSITIONS.items():
            if source in valid_states:
                valid_targets = [t for t in targets if t in valid_states]
                if valid_targets:
                    transitions[source] = valid_targets

        return TypeGroupLifecycle(
            group=group,
            valid_states=valid_states,
            restricted_states=restricted,
            transitions=transitions,
        )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_REGISTRY: Optional[TypeRegistry] = None


def get_registry() -> TypeRegistry:
    """Get the global TypeRegistry singleton."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = TypeRegistry()
        _REGISTRY.initialize_defaults()
    return _REGISTRY


def reset_registry() -> None:
    """Reset the TypeRegistry singleton (for testing)."""
    global _REGISTRY
    _REGISTRY = None