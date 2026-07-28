"""SHUNYA — Credential Store (ADR-003).

Secure credential abstraction with:
  - Provider interface (local dev, env var)
  - Encryption abstraction (AES-256-GCM)
  - Secret rotation support
  - Audit logging
  - Access policy enforcement (only Executor can resolve)
  - Phase 4 eligibility gate integration
  - Tenant isolation
  - Health reporting
  - Metrics integration

Architectural authority: ADR-003, ES-005 §3
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class CredentialType(Enum):
    API_TOKEN = "api_token"
    PASSWORD = "password"
    OAUTH_TOKEN = "oauth_token"
    SSH_KEY = "ssh_key"
    BASIC_AUTH = "basic_auth"


class CredentialStatus(Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class CredentialRef:
    credential_id: Optional[str] = None
    alias: Optional[str] = None
    tenant_id: int = 0


@dataclass
class ResolvedCredential:
    value: str
    type: str
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CredentialMetadata:
    credential_id: str
    alias: str
    type: str
    tenant_id: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    status: str = "active"
    last_resolved_at: Optional[datetime] = None
    version: int = 1


class AccessDeniedError(Exception):
    """Raised when caller is not authorized to resolve credentials."""


class CredentialNotFoundError(Exception):
    """Raised when credential reference does not match any stored credential."""


class EligibilityDeniedError(Exception):
    """Raised when Phase 4 eligibility gate blocks credential release."""


class CredentialExpiredError(Exception):
    """Raised when credential has expired."""


# ---------------------------------------------------------------------------
# Encryption abstraction
# ---------------------------------------------------------------------------

_ENCRYPTION_KEY_ENV = "SHUNYA_CREDENTIAL_ENCRYPTION_KEY"


def _get_encryption_key() -> bytes:
    """Get the encryption key from environment or generate a dev key."""
    key = os.environ.get(_ENCRYPTION_KEY_ENV)
    if key:
        return base64.b64decode(key)
    # Dev default: SHA-256 of a known string (NOT for production)
    return hashlib.sha256(b"shunya-dev-key-change-in-production").digest()


def encrypt_value(value: str, key: Optional[bytes] = None) -> str:
    """Encrypt a credential value using AES-256-GCM-like construction.

    Uses HMAC-SHA256 + XOR for simplicity (avoids pycryptodome dependency).
    For production, replace with pycryptodome AES-256-GCM.

    Returns base64-encoded ciphertext.
    """
    if key is None:
        key = _get_encryption_key()
    # Derive per-value key
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", key, salt, 100000, dklen=32)
    # Encrypt with XOR (placeholder for real AES-GCM)
    value_bytes = value.encode("utf-8")
    cipher = bytes(a ^ b for a, b in zip(value_bytes, derived[:len(value_bytes)]))
    # Prepend salt
    combined = salt + cipher
    return base64.b64encode(combined).decode("ascii")


def decrypt_value(encrypted: str, key: Optional[bytes] = None) -> str:
    """Decrypt a credential value.

    Returns the original plaintext string.
    """
    if key is None:
        key = _get_encryption_key()
    combined = base64.b64decode(encrypted)
    salt = combined[:16]
    cipher = combined[16:]
    derived = hashlib.pbkdf2_hmac("sha256", key, salt, 100000, dklen=32)
    value_bytes = bytes(a ^ b for a, b in zip(cipher, derived[:len(cipher)]))
    return value_bytes.decode("utf-8")


# ---------------------------------------------------------------------------
# Provider interface
# ---------------------------------------------------------------------------


class CredentialProvider(ABC):
    """Abstract credential provider.

    Implementations:
      - LocalCredentialProvider (in-memory, for testing/dev)
      - EnvVarCredentialProvider (from environment variables)
      - (Future) VaultCredentialProvider (from HashiCorp Vault)
    """

    @abstractmethod
    def resolve(self, ref: CredentialRef) -> ResolvedCredential:
        """Resolve a credential reference to its value."""
        ...

    @abstractmethod
    def store(self, ref: CredentialRef, value: str,
              credential_type: str, metadata: Optional[Dict[str, Any]] = None) -> CredentialMetadata:
        """Store a credential."""
        ...

    @abstractmethod
    def revoke(self, credential_id: str, tenant_id: int, reason: str) -> bool:
        """Revoke a credential."""
        ...

    @abstractmethod
    def list(self, tenant_id: int, credential_type: Optional[str] = None) -> List[CredentialMetadata]:
        """List credential metadata for a tenant."""
        ...


class LocalCredentialProvider(CredentialProvider):
    """In-memory credential provider for development and testing.

    Credentials are stored in memory, encrypted at rest.
    """

    def __init__(self, encryption_key: Optional[bytes] = None) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._encryption_key = encryption_key

    def resolve(self, ref: CredentialRef) -> ResolvedCredential:
        with self._lock:
            entry = self._find(ref)
            if entry is None:
                raise CredentialNotFoundError(
                    f"Credential not found: {ref.alias or ref.credential_id}"
                )
            if entry["status"] == CredentialStatus.REVOKED.value:
                raise CredentialExpiredError("Credential has been revoked")
            if entry["status"] == CredentialStatus.EXPIRED.value:
                raise CredentialExpiredError("Credential has expired")
            if entry["expires_at"] and datetime.now(timezone.utc) > entry["expires_at"]:
                entry["status"] = CredentialStatus.EXPIRED.value
                raise CredentialExpiredError("Credential has expired")

            decrypted = decrypt_value(entry["encrypted_value"], self._encryption_key)
            entry["last_resolved_at"] = datetime.now(timezone.utc)

            return ResolvedCredential(
                value=decrypted,
                type=entry["type"],
                expires_at=entry["expires_at"],
                metadata=entry.get("metadata", {}),
            )

    def store(self, ref: CredentialRef, value: str,
              credential_type: str, metadata: Optional[Dict[str, Any]] = None) -> CredentialMetadata:
        encrypted = encrypt_value(value, self._encryption_key)
        now = datetime.now(timezone.utc)
        credential_id = ref.credential_id or str(uuid.uuid4())
        entry = {
            "credential_id": credential_id,
            "alias": ref.alias or credential_id,
            "type": credential_type,
            "tenant_id": ref.tenant_id,
            "encrypted_value": encrypted,
            "status": CredentialStatus.ACTIVE.value,
            "created_at": now,
            "expires_at": metadata.get("expires_at") if metadata else None,
            "last_resolved_at": None,
            "metadata": metadata or {},
            "version": 1,
        }
        with self._lock:
            existing = self._find(ref)
            if existing:
                entry["version"] = existing["version"] + 1
                entry["created_at"] = existing["created_at"]
                self._delete(existing["credential_id"])
            self._store[credential_id] = entry

        return CredentialMetadata(
            credential_id=credential_id,
            alias=entry["alias"],
            type=credential_type,
            tenant_id=ref.tenant_id,
            created_at=now,
            expires_at=entry["expires_at"],
            status=entry["status"],
            version=entry["version"],
        )

    def revoke(self, credential_id: str, tenant_id: int, reason: str) -> bool:
        with self._lock:
            entry = self._store.get(credential_id)
            if entry is None or entry["tenant_id"] != tenant_id:
                return False
            entry["status"] = CredentialStatus.REVOKED.value
            entry["revoked_at"] = datetime.now(timezone.utc)
            entry["revoke_reason"] = reason
        return True

    def list(self, tenant_id: int, credential_type: Optional[str] = None) -> List[CredentialMetadata]:
        results = []
        with self._lock:
            for entry in self._store.values():
                if entry["tenant_id"] != tenant_id:
                    continue
                if credential_type and entry["type"] != credential_type:
                    continue
                results.append(CredentialMetadata(
                    credential_id=entry["credential_id"],
                    alias=entry["alias"],
                    type=entry["type"],
                    tenant_id=entry["tenant_id"],
                    created_at=entry["created_at"],
                    expires_at=entry["expires_at"],
                    status=entry["status"],
                    last_resolved_at=entry.get("last_resolved_at"),
                    version=entry["version"],
                ))
        return results

    def _find(self, ref: CredentialRef) -> Optional[Dict[str, Any]]:
        if ref.credential_id and ref.credential_id in self._store:
            entry = self._store[ref.credential_id]
            if entry["tenant_id"] == ref.tenant_id:
                return entry
        if ref.alias:
            for entry in self._store.values():
                if entry["alias"] == ref.alias and entry["tenant_id"] == ref.tenant_id:
                    return entry
        return None

    def _delete(self, credential_id: str) -> None:
        self._store.pop(credential_id, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


class EnvVarCredentialProvider(CredentialProvider):
    """Credential provider that reads from environment variables.

    Convention: ``SHUNYA_CREDENTIAL_{ALIAS_UPPER}``
    This provider is read-only (no store/revoke).
    """

    _PREFIX = "SHUNYA_CREDENTIAL_"

    def resolve(self, ref: CredentialRef) -> ResolvedCredential:
        alias = ref.alias or ref.credential_id or ""
        env_key = f"{self._PREFIX}{alias.upper().replace('-', '_')}"
        value = os.environ.get(env_key)
        if value is None:
            raise CredentialNotFoundError(
                f"Environment variable {env_key} not found"
            )
        return ResolvedCredential(
            value=value,
            type="api_token",
            metadata={"source": "environment"},
        )

    def store(self, ref: CredentialRef, value: str,
              credential_type: str, metadata: Optional[Dict[str, Any]] = None) -> CredentialMetadata:
        raise NotImplementedError("EnvVarCredentialProvider is read-only")

    def revoke(self, credential_id: str, tenant_id: int, reason: str) -> bool:
        return False

    def list(self, tenant_id: int, credential_type: Optional[str] = None) -> List[CredentialMetadata]:
        results = []
        for key, value in os.environ.items():
            if key.startswith(self._PREFIX):
                alias = key[len(self._PREFIX):].lower()
                results.append(CredentialMetadata(
                    credential_id=alias,
                    alias=alias,
                    type="api_token",
                    tenant_id=tenant_id,
                    created_at=datetime.now(timezone.utc),
                    status="active",
                ))
        return results


# ---------------------------------------------------------------------------
# Access policy
# ---------------------------------------------------------------------------


class AccessPolicy:
    """Enforces that only authorized callers may resolve credentials.

    By default, only the Executor Engine may resolve.
    """

    def __init__(self, authorized_callers: Optional[List[str]] = None) -> None:
        self._authorized = set(authorized_callers or ["executor_engine"])
        self._lock = Lock()

    def authorize(self, caller_name: str) -> None:
        """Raise AccessDeniedError if caller is not authorized."""
        with self._lock:
            if caller_name not in self._authorized:
                raise AccessDeniedError(
                    f"Caller '{caller_name}' not authorized to resolve credentials. "
                    f"Authorized callers: {', '.join(sorted(self._authorized))}"
                )

    def add_caller(self, caller_name: str) -> None:
        with self._lock:
            self._authorized.add(caller_name)

    def remove_caller(self, caller_name: str) -> None:
        with self._lock:
            self._authorized.discard(caller_name)


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------


@dataclass
class CredentialAuditEntry:
    entry_id: str
    credential_id: str
    alias: str
    operation: str  # "resolve" | "store" | "revoke"
    caller_name: str
    tenant_id: int
    timestamp: datetime
    success: bool
    error: Optional[str] = None


class AuditLog:
    """In-memory audit log for credential operations.

    Credential values are NEVER stored in the audit log.
    """

    def __init__(self) -> None:
        self._entries: List[CredentialAuditEntry] = []
        self._lock = Lock()

    def record(self, credential_id: str, alias: str, operation: str,
               caller_name: str, tenant_id: int, success: bool,
               error: Optional[str] = None) -> None:
        entry = CredentialAuditEntry(
            entry_id=str(uuid.uuid4()),
            credential_id=credential_id,
            alias=alias,
            operation=operation,
            caller_name=caller_name,
            tenant_id=tenant_id,
            timestamp=datetime.now(timezone.utc),
            success=success,
            error=error,
        )
        with self._lock:
            self._entries.append(entry)

    def query(self, tenant_id: Optional[int] = None,
              operation: Optional[str] = None,
              limit: int = 100) -> List[CredentialAuditEntry]:
        results = list(self._entries)
        if tenant_id is not None:
            results = [e for e in results if e.tenant_id == tenant_id]
        if operation is not None:
            results = [e for e in results if e.operation == operation]
        return results[-limit:]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


# ---------------------------------------------------------------------------
# Eligibility gate (Phase 4)
# ---------------------------------------------------------------------------


class EligibilityGate:
    """Phase 4 eligibility gate for credential release.

    Checks whether a given purpose_code is authorized for credential access.
    """

    def __init__(self, gate_fn: Optional[Callable[[str, str], bool]] = None) -> None:
        self._gate_fn = gate_fn or self._default_gate

    @staticmethod
    def _default_gate(purpose_code: str, credential_type: str) -> bool:
        """Default gate: allow all purposes."""
        return True

    def check(self, purpose_code: str, credential_type: str) -> bool:
        """Check if a purpose_code is eligible.

        Returns True if eligible. If the gate function is unavailable,
        returns False (safe failure — deny access).
        """
        try:
            return self._gate_fn(purpose_code, credential_type)
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Credential Store
# ---------------------------------------------------------------------------


class CredentialStore:
    """Central credential store.

    Integrates:
      - Provider (local dev or env var)
      - Encryption
      - Access policy
      - Audit logging
      - Phase 4 eligibility gate
      - Tenant isolation
    """

    def __init__(
        self,
        provider: Optional[CredentialProvider] = None,
        access_policy: Optional[AccessPolicy] = None,
        audit_log: Optional[AuditLog] = None,
        eligibility_gate: Optional[EligibilityGate] = None,
        logger: Any = None,
        metrics_registry: Any = None,
        health_registry: Any = None,
    ) -> None:
        self._provider = provider or LocalCredentialProvider()
        self._access_policy = access_policy or AccessPolicy()
        self._audit_log = audit_log or AuditLog()
        self._eligibility_gate = eligibility_gate or EligibilityGate()
        self._logger = logger
        self._metrics = metrics_registry
        self._health = health_registry

        if self._health:
            self._health.register("credential_store", self._health_check)

        if self._metrics:
            self._resolve_counter = self._metrics.counter(
                "credential_store_resolves_total", "Total credential resolve attempts"
            )
            self._resolve_errors = self._metrics.counter(
                "credential_store_resolve_errors_total", "Failed credential resolves"
            )

    def resolve(
        self,
        ref: CredentialRef,
        caller_name: str = "executor_engine",
        purpose_code: str = "execution",
    ) -> ResolvedCredential:
        """Resolve a credential.

        Enforces access policy, Phase 4 eligibility, and tenant isolation.
        """
        # Access policy
        try:
            self._access_policy.authorize(caller_name)
        except AccessDeniedError as e:
            self._audit_log.record(
                ref.credential_id or "", ref.alias or "",
                "resolve", caller_name, ref.tenant_id,
                success=False, error=str(e),
            )
            raise

        # Phase 4 eligibility gate
        if not self._eligibility_gate.check(purpose_code, "credential"):
            self._audit_log.record(
                ref.credential_id or "", ref.alias or "",
                "resolve", caller_name, ref.tenant_id,
                success=False, error="Eligibility denied",
            )
            if self._metrics:
                self._resolve_errors.inc()
            raise EligibilityDeniedError(
                f"Purpose code '{purpose_code}' not authorized for credential access"
            )

        # Resolve
        try:
            resolved = self._provider.resolve(ref)
            self._audit_log.record(
                ref.credential_id or resolved.metadata.get("credential_id", ""),
                ref.alias or "",
                "resolve", caller_name, ref.tenant_id,
                success=True,
            )
            if self._metrics:
                self._resolve_counter.inc()
            if self._logger:
                self._logger.info(
                    "Credential resolved",
                    extra={
                        "credential_id": ref.credential_id or resolved.metadata.get("credential_id", ""),
                        "alias": ref.alias,
                        "caller": caller_name,
                        "tenant_id": ref.tenant_id,
                    },
                )
            return resolved
        except (CredentialNotFoundError, CredentialExpiredError) as e:
            self._audit_log.record(
                ref.credential_id or "", ref.alias or "",
                "resolve", caller_name, ref.tenant_id,
                success=False, error=str(e),
            )
            if self._metrics:
                self._resolve_errors.inc()
            raise

    def store(
        self,
        ref: CredentialRef,
        value: str,
        credential_type: str = "api_token",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CredentialMetadata:
        """Store a credential."""
        meta = self._provider.store(ref, value, credential_type, metadata)
        self._audit_log.record(
            meta.credential_id, meta.alias,
            "store", "credential_store_admin", ref.tenant_id,
            success=True,
        )
        if self._logger:
            self._logger.info(
                "Credential stored",
                extra={
                    "credential_id": meta.credential_id,
                    "alias": meta.alias,
                    "type": credential_type,
                    "tenant_id": ref.tenant_id,
                },
            )
        return meta

    def revoke(self, credential_id: str, tenant_id: int, reason: str) -> bool:
        """Revoke a credential."""
        result = self._provider.revoke(credential_id, tenant_id, reason)
        self._audit_log.record(
            credential_id, "",
            "revoke", "credential_store_admin", tenant_id,
            success=result, error=None if result else "Credential not found",
        )
        if result and self._logger:
            self._logger.info(
                "Credential revoked",
                extra={"credential_id": credential_id, "tenant_id": tenant_id},
            )
        return result

    def list(self, tenant_id: int,
             credential_type: Optional[str] = None) -> List[CredentialMetadata]:
        return self._provider.list(tenant_id, credential_type)

    def rotate(self, credential_id: str, tenant_id: int,
               new_value: str, reason: str = "rotation") -> bool:
        """Rotate a credential (revoke old, store new)."""
        # Capture old metadata before any mutation
        existing = self._provider.list(tenant_id)
        old_meta = None
        for m in existing:
            if m.credential_id == credential_id:
                old_meta = m
                break
        if not old_meta:
            return False

        # Revoke old credential (sets status to revoked, keeps entry)
        if not self._provider.revoke(credential_id, tenant_id, reason):
            return False

        # Store new value under same alias
        ref = CredentialRef(alias=old_meta.alias, tenant_id=tenant_id)
        self._provider.store(ref, new_value, old_meta.type)

        self._audit_log.record(
            credential_id, old_meta.alias,
            "revoke", "credential_store_admin", tenant_id,
            success=True, error=None,
        )
        if self._logger:
            self._logger.info(
                "Credential rotated",
                extra={"credential_id": credential_id, "tenant_id": tenant_id},
            )
        return True

    # ---- Health -----------------------------------------------------------

    def _health_check(self) -> Any:
        from app.shunya.infrastructure.health import HealthCheckResult, HealthStatus

        provider_type = type(self._provider).__name__
        return HealthCheckResult(
            component="credential_store",
            status=HealthStatus.HEALTHY,
            detail=f"Provider: {provider_type}",
            metrics={
                "provider": provider_type,
                "access_policy_callers": len(self._access_policy._authorized),
                "audit_entries": len(self._audit_log._entries),
            },
        )

    def clear(self) -> None:
        """Clear all state. Useful for testing."""
        if isinstance(self._provider, LocalCredentialProvider):
            self._provider.clear()
        self._audit_log.clear()


# ---- Module-level convenience -----------------------------------------------

_store: Optional[CredentialStore] = None


def get_credential_store(**kwargs: Any) -> CredentialStore:
    """Return the application-wide CredentialStore (lazily created)."""
    global _store
    if _store is None:
        from app.shunya.config import get_config
        cfg = get_config()
        cs_cfg = cfg.get_section("credential_store")

        provider: CredentialProvider
        env_provider = os.environ.get("SHUNYA_CREDENTIAL_PROVIDER", "local")
        if env_provider == "env":
            provider = EnvVarCredentialProvider()
        else:
            provider = LocalCredentialProvider()

        _store = CredentialStore(
            provider=provider,
            access_policy=AccessPolicy(),
            audit_log=AuditLog(),
            eligibility_gate=EligibilityGate(),
            **kwargs,
        )
    return _store


def reset_credential_store() -> None:
    """Reset the global CredentialStore. Useful for testing."""
    global _store
    if _store:
        _store.clear()
    _store = None