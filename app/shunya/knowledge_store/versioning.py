"""SHUNYA — Knowledge Store versioning (Phase C).

Version management with optimistic concurrency control.
No destructive updates — version history is always recoverable.

Architectural authority: Phase C — Knowledge Store Foundation
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional, Tuple


class VersionConflictError(Exception):
    """Raised when an optimistic concurrency check fails."""


class VersionHistory:
    """Tracks version history for a knowledge object.

    Thread-safe. Supports:
      - Version creation (new version from current)
      - Latest version lookup
      - Historical lookup by version number
      - Rollback to a previous version
      - Optimistic concurrency via expected_version
    """

    def __init__(self) -> None:
        self._versions: Dict[str, Dict[int, Any]] = {}
        self._latest: Dict[str, int] = {}
        self._lock = threading.RLock()

    def create_version(
        self,
        object_id: str,
        current_version: int,
        expected_version: int,
        snapshot: Any,
    ) -> Tuple[int, Any]:
        """Create a new version with optimistic concurrency control.

        Args:
            object_id: The object's unique identifier.
            current_version: The version number the caller expects to be current.
            expected_version: The version the caller computed from.
            snapshot: The data to store for this version.

        Returns:
            Tuple of (new_version_number, snapshot).

        Raises:
            VersionConflictError: If expected_version != latest version.
        """
        with self._lock:
            latest = self._latest.get(object_id, 0)
            if expected_version != latest:
                raise VersionConflictError(
                    f"Version conflict for {object_id}: "
                    f"expected version {expected_version}, "
                    f"latest is {latest}"
                )
            new_version = latest + 1
            if object_id not in self._versions:
                self._versions[object_id] = {}
            self._versions[object_id][new_version] = snapshot
            self._latest[object_id] = new_version
            return new_version, snapshot

    def get_latest_version(self, object_id: str) -> Optional[int]:
        """Return the latest version number for an object."""
        with self._lock:
            return self._latest.get(object_id)

    def get_version(self, object_id: str, version: int) -> Optional[Any]:
        """Retrieve a specific version of an object."""
        with self._lock:
            return self._versions.get(object_id, {}).get(version)

    def get_all_versions(self, object_id: str) -> List[int]:
        """Return all version numbers for an object, sorted ascending."""
        with self._lock:
            return sorted(self._versions.get(object_id, {}).keys())

    def get_history(self, object_id: str) -> List[Tuple[int, Any]]:
        """Return all versions for an object as (version, snapshot) pairs."""
        with self._lock:
            versions = self._versions.get(object_id, {})
            return [(v, versions[v]) for v in sorted(versions.keys())]

    def rollback(self, object_id: str, target_version: int) -> Optional[int]:
        """Rollback to a previous version.

        Creates a new version that is a copy of the target version.
        Does NOT delete or modify previous versions.

        Args:
            object_id: The object's unique identifier.
            target_version: The version to rollback to.

        Returns:
            The new version number, or None if target_version doesn't exist.
        """
        with self._lock:
            target = self._versions.get(object_id, {}).get(target_version)
            if target is None:
                return None
            latest = self._latest.get(object_id, 0)
            new_version = latest + 1
            self._versions[object_id][new_version] = target
            self._latest[object_id] = new_version
            return new_version

    def has_object(self, object_id: str) -> bool:
        """Check if an object exists in the version history."""
        with self._lock:
            return object_id in self._versions

    def all_object_ids(self) -> List[str]:
        """Return all object IDs that have version history."""
        with self._lock:
            return list(self._versions.keys())

    def clear(self) -> None:
        """Clear all version history. Useful for testing."""
        with self._lock:
            self._versions.clear()
            self._latest.clear()