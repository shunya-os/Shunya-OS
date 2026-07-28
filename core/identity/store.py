"""
Identity Store — Canonical Persistence Protocol.

The IdentityStore protocol defines the persistence contract for identities.
The IdentityEngine depends on this protocol, never on a concrete store.

Implementations may be in-memory, database-backed, or cached.
The protocol lives in core/ so that domain logic never depends on infrastructure.
"""

from __future__ import annotations

from typing import Protocol

from core.identity.models import AuthMethod, EntityType, Identity


class IdentityStore(Protocol):
    """Contract for identity persistence.

    Every identity store must implement this protocol.
    The core depends on this contract, never on a concrete implementation.
    """

    def create(
        self,
        display_name: str,
        entity_type: EntityType,
        auth_methods: tuple[AuthMethod, ...] = (),
    ) -> Identity:
        """Create a new identity.

        Args:
            display_name: Human-readable name.
            entity_type: The kind of entity (human, organization, etc.).
            auth_methods: Authentication methods to bind to this identity.

        Returns:
            The newly created Identity with assigned identity_id.
        """
        ...

    def get(self, identity_id: str) -> Identity | None:
        """Resolve an identity by its permanent ID.

        Args:
            identity_id: The ``sid_`` + 32 hex chars identifier.

        Returns:
            The Identity if found, or None.
        """
        ...

    def find_by_auth(self, method_type: str, identifier: str) -> Identity | None:
        """Find an identity by an authentication method (e.g., email).

        Args:
            method_type: The auth method type (e.g., 'email').
            identifier: The auth method identifier (e.g., 'user@example.com').

        Returns:
            The Identity if found, or None.
        """
        ...

    def all(self) -> list[Identity]:
        """Return all identities in the store.

        Returns:
            A list of all Identity objects.
        """
        ...