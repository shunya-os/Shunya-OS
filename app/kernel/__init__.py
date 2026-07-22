"""SHUNYA Kernel — Universal Foundation.

The Kernel contains the frozen primitives that every SHUNYA experience
is built upon. No business logic lives here.

Primitives:
    Identity     — Permanent human identity with multiple auth methods
    Space        — Context containers for all objects
    Object       — Universal object contract
    Relationship — First-class graph-navigable relationships
    Types        — Universal Type System (Ontology §18)
    State        — Universal state machine (CWR §6, Ontology §11)
    Timeline     — Append-only chronological record (Ontology §12)
    Context      — Universal context model (Ontology §13)
"""

from app.kernel.object import (
    UniversalObject, ObjectRegistry, ObjectStatus,
    EvidenceRef, RelationshipRef,
    get_registry as get_object_registry,
    reset_registry as reset_object_registry,
)
from app.kernel.identity import (
    SHUNYAIdentity, IdentityStore, AuthenticationMethod,
    AuthMethodType, LinkingStatus, LinkingSuggestion,
    get_identity_store, reset_identity_store,
)
from app.kernel.space import (
    Space, SpaceStore, SpaceType, SpaceRole, SpaceMembership,
    get_space_store, reset_space_store,
)
from app.kernel.relationship import (
    Relationship, RelationshipEngine, RelationshipType,
    get_relationship_engine, reset_relationship_engine,
)
from app.kernel.types import (
    TypeRegistry, TypeNode, TypeGroup, TypeGroupLifecycle,
    LifecycleState,
    get_registry as get_type_registry,
    reset_registry as reset_type_registry,
)
from app.kernel.state import (
    StateMachine, StateTransition,
)
from app.kernel.timeline import (
    Timeline, TimelineEvent,
)
from app.kernel.context import (
    Context, ContextData, ContextType, ContextResolution,
)

__all__ = [
    # Object
    "UniversalObject", "ObjectRegistry", "ObjectStatus",
    "EvidenceRef", "RelationshipRef",
    "get_object_registry", "reset_object_registry",
    # Identity
    "SHUNYAIdentity", "IdentityStore", "AuthenticationMethod",
    "AuthMethodType", "LinkingStatus", "LinkingSuggestion",
    "get_identity_store", "reset_identity_store",
    # Space
    "Space", "SpaceStore", "SpaceType", "SpaceRole", "SpaceMembership",
    "get_space_store", "reset_space_store",
    # Relationship
    "Relationship", "RelationshipEngine", "RelationshipType",
    "get_relationship_engine", "reset_relationship_engine",
    # Types
    "TypeRegistry", "TypeNode", "TypeGroup", "TypeGroupLifecycle",
    "LifecycleState", "StateTransition",
    "get_type_registry", "reset_type_registry",
    # State
    "StateMachine",
    # Timeline
    "Timeline", "TimelineEvent",
    # Context
    "Context", "ContextData", "ContextType", "ContextResolution",
]