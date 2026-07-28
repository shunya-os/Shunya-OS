"""
Identity Engine — In-Memory Implementation

The IdentityEngine manages the full identity lifecycle within SHUNYA:
creation, resolution, merge, split, lookup, and retirement.

All identity operations are logged via merge/split history records.
Identities are immutable after creation — status changes produce new
Identity instances with updated ``updated_at`` timestamps.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.identity.models import (
    AuthMethod,
    EntityType,
    Identity,
    IdentityStatus,
    MergeRecord,
    Provenance,
    SplitRecord,
    _generate_identity_id,
)


class IdentityEngine:
    """In-memory engine for managing the SHUNYA identity lifecycle.

    The engine maintains an in-memory store of identities, merge/split
    history, and an index by auth method for fast resolution.

    This is a **single-threaded, in-memory** implementation suitable for
    prototyping, testing, and small-to-medium deployments.  Production
    deployments should back this with a persistent store (see
    ``IdentityStore`` interface).

    **Rules** (from Business Canon §3.1):
    - Identity is immutable after creation.
    - Merged identities are marked ``MERGED``, never deleted.
    - Split identities get new IDs; original is marked ``SPLIT``.
    - Retired identity IDs are never reused.
    - All identity operations are logged.
    """

    def __init__(self) -> None:
        # Primary identity store: identity_id -> Identity
        self._identities: dict[str, Identity] = {}
        # Auth method index: (method_type, identifier) -> identity_id
        self._auth_index: dict[tuple[str, str], str] = {}
        # Merge history: primary_identity_id -> list of MergeRecord
        self._merge_history: dict[str, list[MergeRecord]] = {}
        # Split history: original_identity_id -> list of SplitRecord
        self._split_history: dict[str, list[SplitRecord]] = {}
        # Retired identity IDs (set for O(1) lookup)
        self._retired_ids: set[str] = set()
        # Operational log for traceability
        self._operation_log: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Identity CRUD
    # ------------------------------------------------------------------

    def create_identity(
        self,
        display_name: str,
        entity_type: EntityType | str,
        auth_methods: list[AuthMethod] | None = None,
        metadata: dict[str, Any] | None = None,
        provenance: Provenance | None = None,
    ) -> Identity:
        """Create a new identity with the given attributes.

        Args:
            display_name: Human-readable name for the identity.
            entity_type: Entity type (``EntityType`` enum or string).
            auth_methods: Optional list of authentication methods to bind.
            metadata: Optional extensible metadata dictionary.
            provenance: Optional provenance record of creation.

        Returns:
            The newly created ``Identity``.

        Raises:
            ValueError: If *entity_type* is invalid, or if auth methods
                contain duplicates or conflicts.
        """
        # Normalize entity_type
        if isinstance(entity_type, str):
            try:
                entity_type = EntityType(entity_type)
            except ValueError:
                valid = [e.value for e in EntityType]
                raise ValueError(
                    f"Invalid entity_type {entity_type!r}. "
                    f"Valid values: {valid}"
                )

        # Normalize auth methods
        methods: tuple[AuthMethod, ...] = ()
        if auth_methods:
            self._validate_auth_methods(auth_methods)
            methods = tuple(auth_methods)

        ident = Identity(
            display_name=display_name,
            entity_type=entity_type,
            auth_methods=methods,
            status=IdentityStatus.ACTIVE,
            metadata=metadata or {},
            provenance=provenance or Provenance(),
        )

        self._identities[ident.identity_id] = ident
        self._index_auth_methods(ident.identity_id, methods)
        self._log("create_identity", {
            "identity_id": ident.identity_id,
            "display_name": display_name,
            "entity_type": entity_type.value,
        })
        return ident

    def get_identity(self, identity_id: str) -> Identity | None:
        """Retrieve an identity by its permanent ID.

        Args:
            identity_id: The permanent identity ID (``sid_`` + hex).

        Returns:
            The ``Identity`` if found, or ``None``.
        """
        return self._identities.get(identity_id)

    def delete_identity(self, identity_id: str) -> bool:
        """Mark an identity as ``RETIRED``.

        The identity ID is permanently recorded and will never be reused.
        The identity remains in the store for historical reference.

        Args:
            identity_id: The identity ID to retire.

        Returns:
            ``True`` if the identity was retired, ``False`` if it was
            already retired or does not exist.
        """
        ident = self._identities.get(identity_id)
        if ident is None or ident.status == IdentityStatus.RETIRED:
            return False

        updated = ident.with_status(IdentityStatus.RETIRED)
        self._identities[identity_id] = updated
        self._retired_ids.add(identity_id)
        self._log("delete_identity", {"identity_id": identity_id})
        return True

    # ------------------------------------------------------------------
    # Identity Resolution
    # ------------------------------------------------------------------

    def resolve_identity(self, identifier: str) -> Identity | None:
        """Find an identity by **any** auth method identifier.

        Searches the auth method index for the given identifier across
        all method types.

        Args:
            identifier: An auth method identifier (email, phone, etc.).

        Returns:
            The matching ``Identity``, or ``None``.
        """
        for (_, ident_val), ident_id in self._auth_index.items():
            if ident_val == identifier:
                return self._identities.get(ident_id)
        return None

    def find_by_auth(
        self,
        method_type: str,
        identifier: str,
    ) -> Identity | None:
        """Find an identity by a specific auth method type and identifier.

        Args:
            method_type: The auth method type (``email``, ``phone``, etc.).
            identifier: The identifier value.

        Returns:
            The matching ``Identity``, or ``None``.
        """
        ident_id = self._auth_index.get((method_type, identifier))
        if ident_id is None:
            return None
        return self._identities.get(ident_id)

    def find_by_email(self, email: str) -> Identity | None:
        """Convenience: find an identity by email address.

        Args:
            email: The email address to look up.

        Returns:
            The matching ``Identity``, or ``None``.
        """
        return self.find_by_auth("email", email)

    def search_identities(self, query: str) -> list[Identity]:
        """Search identities by display name (case-insensitive substring).

        .. note::
            Identity search should be precise per the Business Canon (§3.1).
            This provides a basic substring search; production systems
            should use a dedicated search index.

        Args:
            query: Search string to match against display names.

        Returns:
            List of matching identities.
        """
        if not query:
            return list(self._identities.values())
        q = query.lower()
        return [
            ident
            for ident in self._identities.values()
            if q in ident.display_name.lower()
        ]

    def get_identities_by_status(self, status: IdentityStatus) -> list[Identity]:
        """Return all identities with the given status.

        Args:
            status: The ``IdentityStatus`` to filter by.

        Returns:
            List of identities with matching status.
        """
        return [
            ident
            for ident in self._identities.values()
            if ident.status == status
        ]

    # ------------------------------------------------------------------
    # Identity Merge
    # ------------------------------------------------------------------

    def merge_identities(
        self,
        primary_id: str,
        secondary_id: str,
        reason: str = "",
        evidence_id: str | None = None,
        performed_by: str = "system",
    ) -> Identity:
        """Merge a secondary identity into a primary identity.

        After merge:
        - The secondary identity is marked ``MERGED``.
        - The primary identity absorbs the secondary's auth methods.
        - A ``MergeRecord`` is appended to the merge history.

        Args:
            primary_id: The identity that will survive the merge.
            secondary_id: The identity that will be absorbed.
            reason: Why the merge is being performed.
            evidence_id: Optional reference to supporting evidence.
            performed_by: Who or what performed the merge.

        Returns:
            The updated primary ``Identity``.

        Raises:
            ValueError: If either identity does not exist, if they are
                the same identity, or if the secondary is already merged
                or retired.
        """
        primary = self._identities.get(primary_id)
        secondary = self._identities.get(secondary_id)

        if primary is None:
            raise ValueError(f"Primary identity not found: {primary_id}")
        if secondary is None:
            raise ValueError(f"Secondary identity not found: {secondary_id}")
        if primary_id == secondary_id:
            raise ValueError("Cannot merge an identity into itself")
        if secondary.status in (IdentityStatus.MERGED, IdentityStatus.RETIRED):
            raise ValueError(
                f"Secondary identity {secondary_id} is already "
                f"{secondary.status.value}"
            )

        # Mark secondary as MERGED
        merged_secondary = secondary.with_status(IdentityStatus.MERGED)
        self._identities[secondary_id] = merged_secondary

        # Absorb secondary's auth methods into primary
        existing_methods = list(primary.auth_methods)
        existing_ids = {(m.method_type, m.identifier) for m in existing_methods}
        for m in secondary.auth_methods:
            if (m.method_type, m.identifier) not in existing_ids:
                # Demote secondary's primary method — only one primary allowed
                absorbed = AuthMethod(
                    method_type=m.method_type,
                    identifier=m.identifier,
                    is_primary=False,  # demote; primary keeps its primary
                    verified_at=m.verified_at,
                    confidence=m.confidence,
                )
                existing_methods.append(absorbed)
                existing_ids.add((m.method_type, m.identifier))
            else:
                # Update confidence if the existing one is lower
                for i, em in enumerate(existing_methods):
                    if em.method_type == m.method_type and em.identifier == m.identifier:
                        if m.confidence > em.confidence:
                            existing_methods[i] = AuthMethod(
                                method_type=em.method_type,
                                identifier=em.identifier,
                                is_primary=em.is_primary,
                                verified_at=em.verified_at or m.verified_at,
                                confidence=m.confidence,
                            )
                        break

        # Update primary's auth index
        for m in secondary.auth_methods:
            self._auth_index[(m.method_type, m.identifier)] = primary_id

        updated_primary = primary.with_auth_methods(tuple(existing_methods))
        self._identities[primary_id] = updated_primary

        # Record merge
        record = MergeRecord(
            primary_identity_id=primary_id,
            secondary_identity_id=secondary_id,
            reason=reason,
            evidence_id=evidence_id,
            performed_by=performed_by,
        )
        self._merge_history.setdefault(primary_id, []).append(record)

        self._log("merge_identities", {
            "primary_id": primary_id,
            "secondary_id": secondary_id,
            "reason": reason,
        })
        return updated_primary

    def get_merge_history(self, identity_id: str) -> list[MergeRecord]:
        """Return merge history for a given identity (as primary).

        Args:
            identity_id: The identity ID to query.

        Returns:
            List of ``MergeRecord`` entries, newest first.
        """
        records = self._merge_history.get(identity_id, [])
        return sorted(records, key=lambda r: r.timestamp, reverse=True)

    # ------------------------------------------------------------------
    # Identity Split
    # ------------------------------------------------------------------

    def split_identity(
        self,
        identity_id: str,
        method_ids_to_split: list[str],
        reason: str = "",
        performed_by: str = "system",
    ) -> tuple[Identity, Identity]:
        """Split an identity, creating a new identity from selected methods.

        After split:
        - The original identity is marked ``SPLIT``.
        - A new identity is created with the transferred auth methods.
        - A ``SplitRecord`` is appended to the split history.

        Args:
            identity_id: The identity to split.
            method_ids_to_split: List of auth method **identifiers**
                to transfer to the new identity.
            reason: Why the split is being performed.
            performed_by: Who or what performed the split.

        Returns:
            Tuple of ``(original_identity, new_identity)``.

        Raises:
            ValueError: If the identity does not exist, is already split
                or retired, if no methods to split are provided, or if
                a method identifier is not found.
        """
        original = self._identities.get(identity_id)
        if original is None:
            raise ValueError(f"Identity not found: {identity_id}")
        if original.status in (IdentityStatus.SPLIT, IdentityStatus.RETIRED):
            raise ValueError(
                f"Identity {identity_id} is already {original.status.value}"
            )
        if not method_ids_to_split:
            raise ValueError("At least one method identifier must be provided to split")

        # Separate methods to keep vs transfer
        method_ids_set = set(method_ids_to_split)
        keep_methods: list[AuthMethod] = []
        transfer_methods: list[AuthMethod] = []
        transferred_identifiers: list[str] = []

        for m in original.auth_methods:
            if m.identifier in method_ids_set:
                transfer_methods.append(m)
                transferred_identifiers.append(m.identifier)
                method_ids_set.discard(m.identifier)
            else:
                keep_methods.append(m)

        if method_ids_set:
            raise ValueError(
                f"Auth method(s) not found on identity {identity_id}: "
                f"{sorted(method_ids_set)}"
            )

        # Mark original as SPLIT
        original_updated = Identity(
            identity_id=original.identity_id,
            display_name=original.display_name,
            entity_type=original.entity_type,
            auth_methods=tuple(keep_methods),
            status=IdentityStatus.SPLIT,
            created_at=original.created_at,
            updated_at=datetime.now(timezone.utc),
            metadata=original.metadata,
            provenance=original.provenance,
        )
        self._identities[identity_id] = original_updated

        # Remove transferred methods from auth index for original
        for m in transfer_methods:
            self._auth_index.pop((m.method_type, m.identifier), None)

        # Create new identity with transferred methods
        new_identity = Identity(
            identity_id=_generate_identity_id(),
            display_name=f"{original.display_name} (split)",
            entity_type=original.entity_type,
            auth_methods=tuple(transfer_methods),
            status=IdentityStatus.ACTIVE,
            metadata={
                "split_from": identity_id,
                "split_reason": reason,
                **original.metadata,
            },
            provenance=Provenance(
                source="identity_engine",
                source_detail=f"split from {identity_id}: {reason}",
                performed_by=performed_by,
            ),
        )
        self._identities[new_identity.identity_id] = new_identity
        self._index_auth_methods(new_identity.identity_id, tuple(transfer_methods))

        # Record split
        record = SplitRecord(
            original_identity_id=identity_id,
            new_identity_id=new_identity.identity_id,
            reason=reason,
            transferred_methods=tuple(transferred_identifiers),
            performed_by=performed_by,
        )
        self._split_history.setdefault(identity_id, []).append(record)

        self._log("split_identity", {
            "original_id": identity_id,
            "new_id": new_identity.identity_id,
            "transferred_methods": transferred_identifiers,
            "reason": reason,
        })
        return original_updated, new_identity

    def get_split_history(self, identity_id: str) -> list[SplitRecord]:
        """Return split history for a given identity (as original).

        Args:
            identity_id: The original identity ID to query.

        Returns:
            List of ``SplitRecord`` entries, newest first.
        """
        records = self._split_history.get(identity_id, [])
        return sorted(records, key=lambda r: r.timestamp, reverse=True)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_identity_count(self) -> int:
        """Return the total number of identities in the store."""
        return len(self._identities)

    def get_active_count(self) -> int:
        """Return the number of identities with ``ACTIVE`` status."""
        return len(self.get_identities_by_status(IdentityStatus.ACTIVE))

    def is_retired(self, identity_id: str) -> bool:
        """Check whether an identity ID has been retired.

        Retired IDs are never reused.
        """
        return identity_id in self._retired_ids

    def clear(self) -> None:
        """Reset the engine to its initial state (useful for testing)."""
        self._identities.clear()
        self._auth_index.clear()
        self._merge_history.clear()
        self._split_history.clear()
        self._retired_ids.clear()
        self._operation_log.clear()

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _index_auth_methods(
        self,
        identity_id: str,
        methods: tuple[AuthMethod, ...],
    ) -> None:
        """Register auth methods in the lookup index."""
        for m in methods:
            self._auth_index[(m.method_type, m.identifier)] = identity_id

    def _validate_auth_methods(self, methods: list[AuthMethod]) -> None:
        """Validate auth method list for duplicates and conflicts."""
        seen: set[tuple[str, str]] = set()
        primary_count = 0
        for m in methods:
            key = (m.method_type, m.identifier)
            if key in seen:
                raise ValueError(
                    f"Duplicate auth method: {m.method_type}:{m.identifier}"
                )
            seen.add(key)
            if m.is_primary:
                primary_count += 1
        if primary_count > 1:
            raise ValueError(
                f"At most one primary auth method allowed; got {primary_count}"
            )

    def _log(self, operation: str, details: dict[str, Any]) -> None:
        """Append an entry to the internal operation log."""
        self._operation_log.append({
            "operation": operation,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


# ---------------------------------------------------------------------------
# Convenience: create a default engine
# ---------------------------------------------------------------------------

_default_engine: IdentityEngine | None = None


def get_identity_engine() -> IdentityEngine:
    """Return the default singleton ``IdentityEngine`` instance.

    This is a convenience for simple use cases.  For production or
    testing, instantiate ``IdentityEngine()`` directly.
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = IdentityEngine()
    return _default_engine