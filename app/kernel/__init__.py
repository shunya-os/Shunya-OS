"""SHUNYA Kernel — Universal Foundation.

The Kernel contains the frozen primitives that every SHUNYA experience
is built upon. No business logic lives here.

Primitives:
    Identity     — Permanent human identity with multiple auth methods
    Space        — Context containers for all objects
    Object       — Universal object contract
    Relationship — First-class graph-navigable relationships
"""

from app.kernel.object import (
    UniversalObject, ObjectRegistry, ObjectStatus,
    EvidenceRef, RelationshipRef,
    get_registry, reset_registry,
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

__all__ = [
    "UniversalObject", "ObjectRegistry", "ObjectStatus",
    "EvidenceRef", "RelationshipRef",
    "get_registry", "reset_registry",
    "SHUNYAIdentity", "IdentityStore", "AuthenticationMethod",
    "AuthMethodType", "LinkingStatus", "LinkingSuggestion",
    "get_identity_store", "reset_identity_store",
    "Space", "SpaceStore", "SpaceType", "SpaceRole", "SpaceMembership",
    "get_space_store", "reset_space_store",
    "Relationship", "RelationshipEngine", "RelationshipType",
    "get_relationship_engine", "reset_relationship_engine",
]