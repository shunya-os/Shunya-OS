"""
SHUNYA Relationship Engine

Manages typed, directed connections between UniversalObjects in SHUNYA.
Relationships are the structural fabric — they describe how entities,
objects, and concepts relate to each other, with full support for
traversal, path finding, subgraph extraction, and validation.

Usage:
    from core.relationship import RelationshipEngine, Relationship, RelationshipType

    engine = RelationshipEngine()
    rel = engine.add_relationship("obj_a", "obj_b", "member_of", strength=1.0)
    path = engine.find_path("obj_a", "obj_c", max_depth=3)
    subgraph = engine.get_subgraph("obj_a", depth=2)
"""

from core.relationship.engine import RelationshipEngine, get_relationship_engine
from core.relationship.models import (
    Relationship,
    RelationshipDirection,
    RelationshipStatus,
    RelationshipType,
    matches_strength,
    matches_type,
)

__all__ = [
    "Relationship",
    "RelationshipDirection",
    "RelationshipEngine",
    "RelationshipStatus",
    "RelationshipType",
    "get_relationship_engine",
    "matches_strength",
    "matches_type",
]