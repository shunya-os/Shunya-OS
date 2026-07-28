"""
SHUNYA Identity Engine

Manages the full identity lifecycle: create, resolve, merge, split,
lookup, and retire.  Identity is the permanent, unique designation of
any entity in SHUNYA — the fundamental "who" or "what" that everything
else attaches to.

Usage:
    from core.identity import IdentityEngine, Identity, IdentityStatus

    engine = IdentityEngine()
    ident = engine.create_identity("Alice", "human", auth_methods=[...])
    resolved = engine.resolve_identity("alice@example.com")
"""

from core.identity.engine import IdentityEngine, get_identity_engine
from core.identity.models import (
    AuthMethod,
    EntityType,
    Identity,
    IdentityStatus,
    MergeRecord,
    Provenance,
    SplitRecord,
    _generate_identity_id,
    is_valid_identity_id,
)

__all__ = [
    "AuthMethod",
    "EntityType",
    "Identity",
    "IdentityEngine",
    "IdentityStatus",
    "MergeRecord",
    "Provenance",
    "SplitRecord",
    "get_identity_engine",
    "is_valid_identity_id",
]