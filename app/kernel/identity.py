"""SHUNYA Kernel — Universal Identity.

SHUNYA Identity is a permanent human identity that owns multiple
authentication methods. Identity is not an email address, not an account.

Linking flow: Detect → Suggest → Verify → Link → Maintain
Never merge identities automatically.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.kernel.object import UniversalObject, ObjectMeta


# ---------------------------------------------------------------------------
# Authentication Method Types
# ---------------------------------------------------------------------------

class AuthMethodType(str, Enum):
    EMAIL = "email"
    GMAIL = "gmail"
    MICROSOFT = "microsoft"
    COMPANY_EMAIL = "company_email"
    PHONE = "phone"
    PASSKEY = "passkey"
    APPLE_LOGIN = "apple_login"
    OAUTH_GOOGLE = "oauth:google"
    OAUTH_GITHUB = "oauth:github"
    OAUTH_LINKEDIN = "oauth:linkedin"


# ---------------------------------------------------------------------------
# Identity Linking Status
# ---------------------------------------------------------------------------

class LinkingStatus(str, Enum):
    DETECTED = "detected"       # Potential match found
    SUGGESTED = "suggested"     # User shown the suggestion
    VERIFYING = "verifying"     # Ownership verification in progress
    LINKED = "linked"           # Successfully linked
    REJECTED = "rejected"       # User declined the link


# ---------------------------------------------------------------------------
# Authentication Method
# ---------------------------------------------------------------------------

@dataclass
class AuthenticationMethod:
    """A single authentication method belonging to an identity."""
    method_type: str
    identifier: str             # email address, phone number, oauth sub, etc.
    is_primary: bool = False
    verified_at: Optional[str] = None
    display_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.identifier


# ---------------------------------------------------------------------------
# Linking Suggestion
# ---------------------------------------------------------------------------

@dataclass
class LinkingSuggestion:
    """A suggestion to link two identities."""
    source_method: AuthenticationMethod
    target_identity_id: str
    status: str = LinkingStatus.DETECTED.value
    confidence: float = 0.0
    reason: str = ""
    suggested_at: str = ""
    verified_at: Optional[str] = None

    def __post_init__(self):
        if not self.suggested_at:
            self.suggested_at = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# SHUNYA Identity — the kernel primitive
# ---------------------------------------------------------------------------

class SHUNYAIdentity(UniversalObject, metaclass=ObjectMeta):
    """A permanent human identity.

    Not an account. Not an email address.
    Owns multiple authentication methods.
    Belongs to a human, never to an organization.
    """

    def __init__(
        self,
        display_name: str = "",
        primary_email: str = "",
        **kwargs,
    ):
        # Initialize _identity_id before super().__init__ so __post_init__ can use it
        if "_identity_id" not in kwargs:
            kwargs.setdefault("object_type", "SHUNYAIdentity")
            kwargs.setdefault("name", display_name or "Unknown")
        super().__init__(**kwargs)

        self.display_name: str = display_name
        self.primary_email: str = primary_email
        self.auth_methods: List[AuthenticationMethod] = []
        self.linking_suggestions: List[LinkingSuggestion] = []
        self._identity_id = f"sid_{uuid.uuid4().hex[:24]}"

    def __post_init__(self):
        super().__post_init__()
        # No-op: identity_id is set in __init__

    @property
    def identity_id(self) -> str:
        return self._identity_id

    def add_auth_method(self, method: AuthenticationMethod) -> None:
        """Add an authentication method to this identity."""
        # Check for duplicate
        for existing in self.auth_methods:
            if (existing.method_type == method.method_type
                    and existing.identifier == method.identifier):
                return  # Already registered
        self.auth_methods.append(method)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def remove_auth_method(self, method_type: str, identifier: str) -> bool:
        """Remove an authentication method."""
        before = len(self.auth_methods)
        self.auth_methods = [
            m for m in self.auth_methods
            if not (m.method_type == method_type and m.identifier == identifier)
        ]
        changed = len(self.auth_methods) < before
        if changed:
            self.updated_at = datetime.now(timezone.utc).isoformat()
        return changed

    def has_auth_method(self, method_type: str, identifier: str) -> bool:
        """Check if an authentication method exists."""
        return any(
            m.method_type == method_type and m.identifier == identifier
            for m in self.auth_methods
        )

    def get_primary_email(self) -> Optional[str]:
        """Get the primary email address."""
        for m in self.auth_methods:
            if m.method_type in (AuthMethodType.EMAIL.value,
                                 AuthMethodType.GMAIL.value,
                                 AuthMethodType.COMPANY_EMAIL.value):
                if m.is_primary:
                    return m.identifier
        # Fall back to first email-type method
        for m in self.auth_methods:
            if m.method_type in (AuthMethodType.EMAIL.value,
                                 AuthMethodType.GMAIL.value,
                                 AuthMethodType.COMPANY_EMAIL.value):
                return m.identifier
        return self.primary_email or None

    # ---- Linking -----------------------------------------------------------

    def suggest_link(self, method: AuthenticationMethod, reason: str = "",
                     confidence: float = 0.0) -> LinkingSuggestion:
        """Create a linking suggestion for an auth method.

        Returns the suggestion. Does NOT link automatically.
        """
        suggestion = LinkingSuggestion(
            source_method=method,
            target_identity_id=self._identity_id,
            status=LinkingStatus.SUGGESTED.value,
            reason=reason or f"Match found for {method.identifier}",
            confidence=confidence,
        )
        self.linking_suggestions.append(suggestion)
        return suggestion

    def verify_and_link(self, method: AuthenticationMethod,
                        verification_token: str = "") -> bool:
        """Verify ownership and link an auth method.

        In production, verification_token is validated against
        an out-of-band verification (email confirmation, OAuth callback).
        """
        if verification_token:
            # Verification successful — link the method
            self.add_auth_method(method)
            # Update any matching suggestion
            for s in self.linking_suggestions:
                if (s.source_method.identifier == method.identifier
                        and s.status == LinkingStatus.SUGGESTED.value):
                    s.status = LinkingStatus.LINKED.value
                    s.verified_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def reject_link(self, method: AuthenticationMethod) -> None:
        """Reject a linking suggestion."""
        for s in self.linking_suggestions:
            if (s.source_method.identifier == method.identifier
                    and s.status == LinkingStatus.SUGGESTED.value):
                s.status = LinkingStatus.REJECTED.value

    # ---- Detection ---------------------------------------------------------

    def detect_potential_links(self, known_identities: List[SHUNYAIdentity]
                               ) -> List[Dict[str, Any]]:
        """Detect potential links to other identities.

        Args:
            known_identities: List of all known identities.

        Returns:
            List of {target_id, method, confidence, reason} dicts.
        """
        results = []
        my_identifiers = {m.identifier for m in self.auth_methods}

        for other in known_identities:
            if other._identity_id == self._identity_id:
                continue
            for method in other.auth_methods:
                if method.identifier in my_identifiers:
                    results.append({
                        "target_identity_id": other._identity_id,
                        "method": method,
                        "confidence": 0.9,
                        "reason": f"Shared identifier: {method.identifier}",
                    })
        return results

    # ---- Serialization -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "identity_id": self._identity_id,
            "display_name": self.display_name,
            "primary_email": self.primary_email,
            "auth_methods": [
                {
                    "type": m.method_type,
                    "identifier": m.identifier,
                    "is_primary": m.is_primary,
                    "verified": m.verified_at is not None,
                }
                for m in self.auth_methods
            ],
            "linking_suggestions": [
                {
                    "method": s.source_method.identifier,
                    "status": s.status,
                    "confidence": s.confidence,
                    "reason": s.reason,
                }
                for s in self.linking_suggestions
            ],
        })
        return base


# ---------------------------------------------------------------------------
# Identity Store (in-memory for now; migrate to persistent when needed)
# ---------------------------------------------------------------------------

class IdentityStore:
    """In-memory store for SHUNYA Identities."""

    def __init__(self):
        self._identities: Dict[str, SHUNYAIdentity] = {}

    def create(self, display_name: str, primary_email: str = ""
               ) -> SHUNYAIdentity:
        identity = SHUNYAIdentity(
            display_name=display_name,
            primary_email=primary_email,
        )
        if primary_email:
            identity.add_auth_method(AuthenticationMethod(
                method_type=AuthMethodType.EMAIL.value,
                identifier=primary_email,
                is_primary=True,
            ))
        self._identities[identity._identity_id] = identity
        return identity

    def get(self, identity_id: str) -> Optional[SHUNYAIdentity]:
        return self._identities.get(identity_id)

    def find_by_auth(self, method_type: str, identifier: str
                     ) -> Optional[SHUNYAIdentity]:
        for identity in self._identities.values():
            if identity.has_auth_method(method_type, identifier):
                return identity
        return None

    def all(self) -> List[SHUNYAIdentity]:
        return list(self._identities.values())

    def delete(self, identity_id: str) -> bool:
        if identity_id in self._identities:
            del self._identities[identity_id]
            return True
        return False


# Global identity store
_IDENTITY_STORE: Optional[IdentityStore] = None


def get_identity_store() -> IdentityStore:
    global _IDENTITY_STORE
    if _IDENTITY_STORE is None:
        _IDENTITY_STORE = IdentityStore()
    return _IDENTITY_STORE


def reset_identity_store() -> None:
    global _IDENTITY_STORE
    _IDENTITY_STORE = None