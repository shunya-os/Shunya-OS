"""SHUNYA — Identity resolver (Phase D).

Identity lookup, registration, merge, duplicate detection, and alias handling.
Persists via Knowledge Store.

Architectural authority: ES-010, SHUNYA_CORE_MODELS.md §3
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.shunya.identity.models import (
    Identity, IdentityClaim, ResolutionResult, ResolutionStatus,
    IdentityType, IdentityStatus,
)
from app.shunya.identity.normalizer import normalize_for_type


class IdentityResolver:
    """Resolves identity claims against stored identities.

    Deterministic. Never silently merges uncertain identities.
    """

    def __init__(self, knowledge_store: Any) -> None:
        self._ks = knowledge_store

    # ---- Resolution --------------------------------------------------------

    def resolve(self, claim: IdentityClaim) -> ResolutionResult:
        """Resolve an identity claim to a canonical identity.

        Returns MATCHED, NO_MATCH, or AMBIGUOUS.
        """
        normalized = normalize_for_type(claim.identity_type, claim.identity_value)
        if not normalized:
            return ResolutionResult(
                status=ResolutionStatus.NO_MATCH,
                reason="Empty identity value after normalization",
            )

        matches = self._find_matches(
            identity_type=claim.identity_type,
            normalized_value=normalized,
            tenant_id=claim.tenant_id,
        )

        if len(matches) == 1:
            identity = matches[0]
            return ResolutionResult(
                status=ResolutionStatus.MATCHED,
                identity=identity,
                confidence=identity.confidence,
                reason="Single identity match",
            )

        if len(matches) > 1:
            return ResolutionResult(
                status=ResolutionStatus.AMBIGUOUS,
                candidates=matches,
                confidence=min(i.confidence for i in matches),
                reason=f"Multiple matches ({len(matches)} candidates)",
            )

        return ResolutionResult(
            status=ResolutionStatus.NO_MATCH,
            reason="No matching identity found",
        )

    def resolve_by_email(self, email: str, tenant_id: int) -> ResolutionResult:
        """Convenience: resolve by email."""
        return self.resolve(IdentityClaim(
            identity_type=IdentityType.EMAIL.value,
            identity_value=email,
            tenant_id=tenant_id,
        ))

    def resolve_by_phone(self, phone: str, tenant_id: int) -> ResolutionResult:
        """Convenience: resolve by phone."""
        return self.resolve(IdentityClaim(
            identity_type=IdentityType.PHONE.value,
            identity_value=phone,
            tenant_id=tenant_id,
        ))

    def resolve_by_channel(self, channel: str, channel_id: str, tenant_id: int) -> ResolutionResult:
        """Convenience: resolve by channel identity."""
        return self.resolve(IdentityClaim(
            identity_type=f"channel:{channel}",
            identity_value=channel_id,
            tenant_id=tenant_id,
        ))

    def resolve_multi(
        self,
        email: str = "",
        phone: str = "",
        channel: str = "",
        channel_id: str = "",
        tenant_id: int = 0,
    ) -> ResolutionResult:
        """Multi-strategy resolution. Tries strongest identifier first."""
        if email:
            result = self.resolve_by_email(email, tenant_id)
            if result.status in (ResolutionStatus.MATCHED, ResolutionStatus.AMBIGUOUS):
                return result
        if phone:
            result = self.resolve_by_phone(phone, tenant_id)
            if result.status in (ResolutionStatus.MATCHED, ResolutionStatus.AMBIGUOUS):
                return result
        if channel and channel_id:
            result = self.resolve_by_channel(channel, channel_id, tenant_id)
            if result.status in (ResolutionStatus.MATCHED, ResolutionStatus.AMBIGUOUS):
                return result
        return ResolutionResult(status=ResolutionStatus.NO_MATCH, reason="No strong identifier matched")

    # ---- Registration ------------------------------------------------------

    def register(
        self,
        identity_type: str,
        identity_value: str,
        tenant_id: int,
        person_id: str = "",
        verification_state: str = "unverified",
        confidence: float = 0.5,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> Identity:
        """Register a new identity.

        If an identity with the same normalized value already exists and
        belongs to the same person, returns the existing identity.
        If it belongs to a different person, the registration is skipped
        (duplicate detected — returns None semantics via ResolutionResult).
        """
        normalized = normalize_for_type(identity_type, identity_value)

        # Check for existing identity with same normalized value
        existing = self._find_matches(identity_type, normalized, tenant_id)
        if existing:
            # Same normalized value exists — return None to indicate
            # that a manual merge review is required
            return None  # type: ignore

        identity = Identity(
            identity_type=identity_type,
            identity_value=identity_value,
            normalized_value=normalized,
            tenant_id=tenant_id,
            person_id=person_id,
            status=IdentityStatus.ACTIVE.value,
            verification_state="unverified",
            confidence=0.5,
            provenance=provenance or {},
        )

        self._ks.create(
            key=f"identity:{identity_type}:{normalized}",
            payload=identity.to_dict(),
            namespace=f"identity:{tenant_id}",
            object_type="identity",
            metadata={
                "identity_type": identity_type,
                "normalized_value": normalized,
                "identity_id": identity.identity_id,
                "tenant_id": tenant_id,
            },
            created_by="identity_engine",
        )

        return identity

    def register_with_person(
        self,
        identity_type: str,
        identity_value: str,
        tenant_id: int,
        person_id: str,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> Identity:
        """Register an identity linked to a canonical person ID."""
        normalized = normalize_for_type(identity_type, identity_value)

        identity = Identity(
            identity_type=identity_type,
            identity_value=identity_value,
            normalized_value=normalized,
            tenant_id=tenant_id,
            person_id=person_id,
            status=IdentityStatus.ACTIVE.value,
            verification_state="unverified",
            confidence=0.5,
            provenance=provenance or {},
        )

        self._ks.create(
            key=f"identity:{identity_type}:{normalized}",
            payload=identity.to_dict(),
            namespace=f"identity:{tenant_id}",
            object_type="identity",
            metadata={
                "identity_type": identity_type,
                "normalized_value": normalized,
                "identity_id": identity.identity_id,
                "tenant_id": tenant_id,
            },
            created_by="identity_engine",
        )

        return identity

    # ---- Merge -------------------------------------------------------------

    def merge(self, primary_id: str, secondary_id: str, tenant_id: int) -> bool:
        """Merge a secondary identity into a primary identity.

        The secondary identity is marked as MERGED.
        The primary identity's merged_from_ids is updated.
        """
        primary = self._find_by_id(primary_id, tenant_id)
        secondary = self._find_by_id(secondary_id, tenant_id)

        if not primary or not secondary:
            return False

        # Mark secondary as merged
        secondary.status = IdentityStatus.MERGED.value
        secondary.merged_into_id = primary_id
        secondary.updated_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )

        # Update primary's merged_from_ids
        if not primary.merged_from_ids:
            primary.merged_from_ids = []
        if secondary_id not in primary.merged_from_ids:
            primary.merged_from_ids.append(secondary_id)

        # Persist both
        self._update_identity(secondary)
        self._update_identity(primary)

        return True

    # ---- Internal helpers --------------------------------------------------

    def _find_matches(
        self, identity_type: str, normalized_value: str, tenant_id: int
    ) -> List[Identity]:
        """Find identities matching a normalized value within a tenant."""
        namespace = f"identity:{tenant_id}"
        key = f"identity:{identity_type}:{normalized_value}"
        obj = self._ks.get_by_key(namespace, key)
        if obj is not None:
            return [Identity.from_dict(obj.payload)]
        return []

    def _find_by_id(self, identity_id: str, tenant_id: int) -> Optional[Identity]:
        """Find an identity by its ID within a tenant."""
        from app.shunya.knowledge_store.models import SearchQuery, SearchFilter

        # Search metadata.identity_id in the identity namespace
        query = SearchQuery(
            namespace=f"identity:{tenant_id}",
            object_type="identity",
            limit=20,
        )
        result = self._ks.search(query)
        for obj in result.items:
            meta = obj.metadata or {}
            if meta.get("identity_id") == identity_id:
                return Identity.from_dict(obj.payload)
        return None

    def _update_identity(self, identity: Identity) -> None:
        """Persist an updated identity."""
        existing = self._find_by_id(identity.identity_id, identity.tenant_id)
        if existing is None:
            return
        # Find the KnowledgeObject by key
        namespace = f"identity:{identity.tenant_id}"
        key = f"identity:{identity.identity_type}:{identity.normalized_value}"
        obj = self._ks.get_by_key(namespace, key)
        if obj is not None:
            self._ks.update(obj.object_id, payload=identity.to_dict())