"""
SHUNYA — Core Kernel

Foundational types and the UniversalObject base class implementing
the Universal Object Protocol (docs/canon/04_universal_object_protocol.md).

Every object in the SHUNYA system derives from UniversalObject, which
provides all 15 mandatory protocol sections:
    §4  Identity         §9  Status           §14 AI Context
    §5  Metadata         §10 Ownership        §15 Search
    §6  Relationships    §11 Permissions      §16 Audit
    §7  Timeline         §12 Evidence         §17 Actions
    §8  Lifecycle        §13 Memory (OPT)     §18 Versioning
"""

from core.kernel.object import (
    ActionDefinition,
    ActionResult,
    SearchResult,
    UniversalObject,
)
from core.kernel.types import (
    AccessControlEntry,
    AccessControlList,
    ActionEffect,
    AuditEntry,
    DiffResult,
    EvidenceRef,
    IdentityAuthority,
    IdentityType,
    InteractionRecord,
    ObjectStatus,
    OwnershipRecord,
    OwnerType,
    RelationshipDirection,
    RelationshipRef,
    SourceType,
    StageTransition,
    TimelineEvent,
    VersionRecord,
    _now_iso,
    generate_uuid7,
)

__all__ = [
    # Main class
    "UniversalObject",
    # Action types
    "ActionDefinition",
    "ActionResult",
    # Enums
    "ObjectStatus",
    "IdentityType",
    "IdentityAuthority",
    "SourceType",
    "RelationshipDirection",
    "OwnerType",
    "ActionEffect",
    # Data types
    "AccessControlEntry",
    "AccessControlList",
    "AuditEntry",
    "DiffResult",
    "EvidenceRef",
    "InteractionRecord",
    "OwnershipRecord",
    "RelationshipRef",
    "SearchResult",
    "StageTransition",
    "TimelineEvent",
    "VersionRecord",
    # Utilities
    "generate_uuid7",
    "_now_iso",
]