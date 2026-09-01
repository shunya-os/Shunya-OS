"""SHUNYA — Identity Persistence Bridge (Production).

ZGC-PR-17C DEPRECATION NOTICE (identity convergence):
  This module is a STORAGE ADAPTER for the kernel SHUNYAIdentity protocol.
  It is NOT an identity authority and it is NOT an authentication path.
  The canonical identity authority chain is:
    TeamMember (app/auth.py)      → authentication (password, session)
    OrgMember  (app/models.py)    → organization membership + authorization
    session identity_id           → carried through every layer as the
                                    canonical identity string
  Authentication MUST be performed through TeamMember (app/auth.py).
  Identity creation for login MAY use this repository as a persistence
  adapter (dual-write bridge) — it creates shunya_identities rows that
  back TeamMember.identity_id. Nothing here authenticates.
  core.identity_engine (Stream D) provides identity PROFILE intelligence
  (decision style, goals, preferences) — wired as the runtime identity
  profile provider; also not an authority.
"""

import json
from datetime import datetime, timezone

from app import db
from app.kernel.identity import (
    SHUNYAIdentity, AuthenticationMethod, AuthMethodType,
    IdentityStore, get_identity_store,
)


class SHUNYAIdentityModel(db.Model):
    """SQLAlchemy persistence for SHUNYA Identity.

    This is a storage adapter, NOT a kernel primitive.
    The kernel's SHUNYAIdentity class is the canonical contract.
    """

    __tablename__ = "shunya_identities"

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(255), nullable=False)
    primary_email = db.Column(db.String(255), default="")
    status = db.Column(db.String(30), default="active")
    auth_methods_json = db.Column(db.Text, default="[]")  # JSON array of {type, identifier, is_primary, verified_at}
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_kernel(self) -> SHUNYAIdentity:
        """Convert this persisted model to a kernel SHUNYAIdentity."""
        identity = SHUNYAIdentity(
            display_name=self.display_name,
            primary_email=self.primary_email or "",
        )
        identity._identity_id = self.identity_id
        identity.status = self.status

        # Restore auth methods
        methods = json.loads(self.auth_methods_json or "[]")
        for m in methods:
            identity.add_auth_method(AuthenticationMethod(
                method_type=m["type"],
                identifier=m["identifier"],
                is_primary=m.get("is_primary", False),
                verified_at=m.get("verified_at"),
            ))

        return identity

    @classmethod
    def from_kernel(cls, identity: SHUNYAIdentity) -> "SHUNYAIdentityModel":
        """Create a persisted model from a kernel SHUNYAIdentity."""
        methods = [
            {
                "type": m.method_type,
                "identifier": m.identifier,
                "is_primary": m.is_primary,
                "verified_at": m.verified_at,
            }
            for m in identity.auth_methods
        ]
        return cls(
            identity_id=identity.identity_id,
            display_name=identity.display_name,
            primary_email=identity.primary_email,
            status=identity.status,
            auth_methods_json=json.dumps(methods),
        )

    def to_dict(self) -> dict:
        """Serialize to API response format."""
        methods = json.loads(self.auth_methods_json or "[]")
        return {
            "identity_id": self.identity_id,
            "display_name": self.display_name,
            "primary_email": self.primary_email,
            "status": self.status,
            "auth_methods": [
                {
                    "type": m["type"],
                    "identifier": m["identifier"][:3] + "***" + m["identifier"][-4:] if "@" in m.get("identifier", "") else "***",
                    "is_primary": m.get("is_primary", False),
                    "verified": m.get("verified_at") is not None,
                }
                for m in methods
            ],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Identity Repository — bridges kernel IdentityStore with DB persistence
# ---------------------------------------------------------------------------

class IdentityRepository:
    """Persistence-aware Identity Repository.

    Implements the Identity Repository contract (SMS §2).
    Wraps the kernel's IdentityStore with SQLAlchemy persistence.
    """

    def __init__(self):
        self._store = get_identity_store()

    def create(self, display_name: str, primary_email: str = "") -> SHUNYAIdentity:
        """Create a new identity — persists to both kernel store and DB."""
        # Create in kernel
        identity = self._store.create(display_name, primary_email)

        # Persist to DB
        model = SHUNYAIdentityModel.from_kernel(identity)
        db.session.add(model)
        db.session.commit()

        return identity

    def get(self, identity_id: str) -> SHUNYAIdentity | None:
        """Get an identity by ID — tries DB first, falls back to kernel store."""
        model = SHUNYAIdentityModel.query.filter_by(identity_id=identity_id).first()
        if model:
            identity = model.to_kernel()
            # Sync to kernel store
            self._store._identities[identity_id] = identity
            return identity
        return self._store.get(identity_id)

    def find_by_auth(self, method_type: str, identifier: str) -> SHUNYAIdentity | None:
        """Find an identity by auth method (legacy, returns SHUNYAIdentity)."""
        # Try in-memory first
        identity = self._store.find_by_auth(method_type, identifier)
        if identity:
            return identity

        # Query DB
        all_models = SHUNYAIdentityModel.query.all()
        for model in all_models:
            methods = json.loads(model.auth_methods_json or "[]")
            for m in methods:
                if m["type"] == method_type and m["identifier"] == identifier:
                    identity = model.to_kernel()
                    self._store._identities[identity.identity_id] = identity
                    return identity
        return None

    # ------------------------------------------------------------------
    # Canonical Identity API (returns core Identity model)
    # ------------------------------------------------------------------

    def create_core(
        self,
        display_name: str,
        entity_type: str = "human",
        auth_methods: list[dict] | None = None,
    ) -> "Identity":
        """Create a new canonical Identity and persist it.

        If an identity with the same email already exists, returns it instead
        of creating a duplicate. Idempotent.
        """
        from core.identity.models import Identity as CoreIdentity, EntityType, AuthMethod, IdentityStatus

        # Check for existing identity by email
        for am in (auth_methods or []):
            existing = self.find_by_auth_core(am.get("method_type", "email"), am.get("identifier", ""))
            if existing:
                return existing

        # Normalize entity type
        try:
            etype = EntityType(entity_type)
        except ValueError:
            etype = EntityType.HUMAN

        # Build auth methods
        methods: list[AuthMethod] = []
        for am in (auth_methods or []):
            methods.append(AuthMethod(
                method_type=am.get("method_type", "email"),
                identifier=am.get("identifier", ""),
                is_primary=am.get("is_primary", True),
            ))

        ident = CoreIdentity(
            display_name=display_name,
            entity_type=etype,
            auth_methods=tuple(methods),
            status=IdentityStatus.ACTIVE,
        )

        # Persist to DB via SHUNYAIdentityModel
        model = self._model_from_core(ident)
        db.session.add(model)
        db.session.commit()

        # Also sync to legacy kernel store for backward compat
        self._sync_core_to_legacy(ident)

        return ident

    def get_core(self, identity_id: str) -> "Identity | None":
        """Resolve an identity by ID, returning a canonical Identity."""
        model = SHUNYAIdentityModel.query.filter_by(identity_id=identity_id).first()
        if model:
            return self._model_to_core(model)
        return None

    def find_by_auth_core(self, method_type: str, identifier: str) -> "Identity | None":
        """Find an identity by auth method, returning a canonical Identity."""
        all_models = SHUNYAIdentityModel.query.all()
        for model in all_models:
            methods = json.loads(model.auth_methods_json or "[]")
            for m in methods:
                if m["type"] == method_type and m["identifier"] == identifier:
                    return self._model_to_core(model)
        return None

    def all_core(self) -> list["Identity"]:
        """Return all identities as canonical Identity objects."""
        models = SHUNYAIdentityModel.query.all()
        return [self._model_to_core(m) for m in models]

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _model_to_core(model: SHUNYAIdentityModel) -> "Identity":
        """Convert a SHUNYAIdentityModel to a core Identity."""
        from core.identity.models import Identity as CoreIdentity, AuthMethod, EntityType, IdentityStatus

        entity_type = EntityType.HUMAN
        try:
            if model.display_name:
                entity_type = EntityType.HUMAN
        except ValueError:
            pass

        methods = json.loads(model.auth_methods_json or "[]")
        auth_methods = tuple(
            AuthMethod(
                method_type=m.get("type", "email"),
                identifier=m.get("identifier", ""),
                is_primary=m.get("is_primary", False),
                verified_at=m.get("verified_at"),
            )
            for m in methods
        )

        return CoreIdentity(
            identity_id=model.identity_id,
            display_name=model.display_name,
            entity_type=entity_type,
            auth_methods=auth_methods,
            status=IdentityStatus.ACTIVE,
            created_at=model.created_at,
            updated_at=model.updated_at or model.created_at,
        )

    @staticmethod
    def _model_from_core(identity: "Identity") -> SHUNYAIdentityModel:
        """Convert a core Identity to a SHUNYAIdentityModel for persistence."""
        methods = [
            {
                "type": am.method_type,
                "identifier": am.identifier,
                "is_primary": am.is_primary,
                "verified_at": am.verified_at,
            }
            for am in identity.auth_methods
        ]
        return SHUNYAIdentityModel(
            identity_id=identity.identity_id,
            display_name=identity.display_name,
            primary_email="",
            status=identity.status.value if hasattr(identity.status, "value") else identity.status,
            auth_methods_json=json.dumps(methods),
        )

    @staticmethod
    def _sync_core_to_legacy(identity: "Identity") -> None:
        """Sync a core Identity to the legacy kernel IdentityStore for backward compat."""
        from app.kernel.identity import SHUNYAIdentity, AuthenticationMethod, AuthMethodType, get_identity_store

        store = get_identity_store()
        existing = store.get(identity.identity_id)
        if existing:
            return

        legacy = SHUNYAIdentity(
            display_name=identity.display_name,
            primary_email="",
        )
        legacy._identity_id = identity.identity_id
        for am in identity.auth_methods:
            legacy.add_auth_method(AuthenticationMethod(
                method_type=am.method_type,
                identifier=am.identifier,
                is_primary=am.is_primary,
            ))
        store._identities[legacy.identity_id] = legacy

    def add_auth_method(self, identity_id: str, method_type: str,
                        identifier: str, is_primary: bool = False) -> bool:
        """Add an authentication method to an identity."""
        identity = self.get(identity_id)
        if not identity:
            return False

        method = AuthenticationMethod(
            method_type=method_type,
            identifier=identifier,
            is_primary=is_primary,
        )
        identity.add_auth_method(method)
        self._sync_to_db(identity)
        return True

    def verify_auth_method(self, identity_id: str, method_type: str,
                           identifier: str) -> bool:
        """Mark an auth method as verified."""
        identity = self.get(identity_id)
        if not identity:
            return False

        for m in identity.auth_methods:
            if m.method_type == method_type and m.identifier == identifier:
                m.verified_at = datetime.utcnow().isoformat()
                self._sync_to_db(identity)
                return True
        return False

    def remove_auth_method(self, identity_id: str, method_type: str,
                           identifier: str) -> bool:
        """Remove an authentication method."""
        identity = self.get(identity_id)
        if not identity:
            return False

        result = identity.remove_auth_method(method_type, identifier)
        if result:
            self._sync_to_db(identity)
        return result

    def get_auth_methods(self, identity_id: str) -> list:
        """Get all auth methods for an identity."""
        identity = self.get(identity_id)
        if not identity:
            return []

        return [
            {
                "type": m.method_type,
                "identifier": m.identifier[:3] + "***" + m.identifier[-4:] if "@" in m.identifier else "***",
                "is_primary": m.is_primary,
                "verified": m.verified_at is not None,
            }
            for m in identity.auth_methods
        ]

    def get_profile(self, identity_id: str) -> dict | None:
        """Get public profile for an identity."""
        # Use self.get() which falls back to kernel store —
        # same pattern as get_auth_methods()
        identity = self.get(identity_id)
        if not identity:
            return None
        return {
            "identity_id": identity.identity_id,
            "display_name": identity.display_name,
            "primary_email": identity.primary_email,
            "status": identity.status,
            "auth_methods": [
                {
                    "type": m.method_type,
                    "identifier": m.identifier[:3] + "***" + m.identifier[-4:] if "@" in m.identifier else "***",
                    "is_primary": m.is_primary,
                    "verified": m.verified_at is not None,
                }
                for m in identity.auth_methods
            ],
        }

    def _sync_to_db(self, identity: SHUNYAIdentity) -> None:
        """Sync a kernel identity back to the database."""
        model = SHUNYAIdentityModel.query.filter_by(
            identity_id=identity.identity_id
        ).first()
        if model:
            model.display_name = identity.display_name
            model.primary_email = identity.primary_email or ""
            model.status = identity.status
            methods = [
                {
                    "type": m.method_type,
                    "identifier": m.identifier,
                    "is_primary": m.is_primary,
                    "verified_at": m.verified_at,
                }
                for m in identity.auth_methods
            ]
            model.auth_methods_json = json.dumps(methods)
            model.updated_at = datetime.utcnow()
        else:
            model = SHUNYAIdentityModel.from_kernel(identity)
            db.session.add(model)
        db.session.commit()