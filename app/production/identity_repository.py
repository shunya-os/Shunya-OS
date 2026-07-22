"""SHUNYA — Identity Persistence Bridge (Production).

Bridges the kernel's SHUNYAIdentity contract with SQLAlchemy persistence.
The kernel classes remain frozen — this is a storage adapter, not a kernel change.
"""

import json
from datetime import datetime

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
        """Find an identity by auth method."""
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
        model = SHUNYAIdentityModel.query.filter_by(identity_id=identity_id).first()
        if not model:
            return None
        return model.to_dict()

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