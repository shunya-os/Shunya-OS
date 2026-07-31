"""SHUNYA Kernel — Space Architecture.

Everything exists inside one or more Spaces.
Spaces provide context, isolation, and permission boundaries.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.kernel.object import UniversalObject, ObjectMeta


class SpaceType(str, Enum):
    PERSONAL = "personal"
    FAMILY = "family"
    ORGANIZATION = "organization"
    COMMUNITY = "community"
    PROJECT = "project"
    RESEARCH = "research"


class SpaceRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"


@dataclass
class SpaceMembership:
    """A human's membership in a Space."""
    identity_id: str
    space_id: str
    role: str = SpaceRole.MEMBER.value
    joined_at: str = ""
    invited_by: str = ""

    def __post_init__(self):
        if not self.joined_at:
            self.joined_at = datetime.now(timezone.utc).isoformat()


class Space(UniversalObject, metaclass=ObjectMeta):
    """A Space — context for a collection of Objects.

    Everything in SHUNYA exists inside one or more Spaces.
    """

    def __init__(
        self,
        name: str = "",
        space_type: str = SpaceType.PERSONAL.value,
        description: str = "",
        parent_space_id: str = "",
        **kwargs,
    ):
        kwargs.setdefault("object_type", "Space")
        kwargs.setdefault("name", name or "Untitled Space")
        super().__init__(**kwargs)

        self.space_type: str = space_type
        self.description: str = description
        self.parent_space_id: str = parent_space_id
        self.members: List[SpaceMembership] = []
        self._space_id = f"spc_{uuid.uuid4().hex[:24]}"

    @property
    def space_id(self) -> str:
        return self._space_id

    @space_id.setter
    def space_id(self, value: str) -> None:
        self._space_id = value

    def add_member(self, identity_id: str, role: str = SpaceRole.MEMBER.value,
                   invited_by: str = "") -> SpaceMembership:
        membership = SpaceMembership(
            identity_id=identity_id,
            space_id=self._space_id,
            role=role,
            invited_by=invited_by,
        )
        self.members.append(membership)
        return membership

    def remove_member(self, identity_id: str) -> bool:
        before = len(self.members)
        self.members = [m for m in self.members
                        if m.identity_id != identity_id]
        return len(self.members) < before

    def get_member(self, identity_id: str) -> Optional[SpaceMembership]:
        for m in self.members:
            if m.identity_id == identity_id:
                return m
        return None

    def has_member(self, identity_id: str) -> bool:
        return self.get_member(identity_id) is not None

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "space_id": self._space_id,
            "space_type": self.space_type,
            "description": self.description,
            "parent_space_id": self.parent_space_id,
            "member_count": len(self.members),
            "members": [
                {
                    "identity_id": m.identity_id[:12],
                    "role": m.role,
                    "joined_at": m.joined_at,
                }
                for m in self.members
            ],
        })
        return base


# ---------------------------------------------------------------------------
# Space Store
# ---------------------------------------------------------------------------

class SpaceStore:
    """In-memory store for Spaces."""

    def __init__(self):
        self._spaces: Dict[str, Space] = {}

    def create(self, name: str, space_type: str = SpaceType.PERSONAL.value,
               owner_id: str = "", **kwargs) -> Space:
        space = Space(name=name, space_type=space_type, **kwargs)
        if owner_id:
            space.add_member(owner_id, role=SpaceRole.OWNER.value)
        self._spaces[space._space_id] = space
        return space

    def get(self, space_id: str) -> Optional[Space]:
        return self._spaces.get(space_id)

    def get_for_identity(self, identity_id: str) -> List[Space]:
        return [s for s in self._spaces.values() if s.has_member(identity_id)]

    def all(self) -> List[Space]:
        return list(self._spaces.values())

    def delete(self, space_id: str) -> bool:
        if space_id in self._spaces:
            del self._spaces[space_id]
            return True
        return False


_GLOBAL_SPACE_STORE: Optional[SpaceStore] = None


def get_space_store() -> SpaceStore:
    global _GLOBAL_SPACE_STORE
    if _GLOBAL_SPACE_STORE is None:
        _GLOBAL_SPACE_STORE = SpaceStore()
    return _GLOBAL_SPACE_STORE


def reset_space_store() -> None:
    global _GLOBAL_SPACE_STORE
    _GLOBAL_SPACE_STORE = None