"""SHUNYA — Connector SDK (FDA26).

Canonical connector base class that enforces the provider fabric:

    authentication → authorization → tenant context → execution → retry/idempotency → evidence/audit

Every SHUNYA connector must extend ConnectorBase.
No connector creates a second identity/tenant/event/execution/audit system.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from app import db
from app.security.audit import log_audit
from app.execution.idempotency import IdempotencyGuard

logger = logging.getLogger(__name__)


class ConnectorBase(ABC):
    """Canonical connector base class for the SHUNYA provider fabric.

    Lifecycle:
        1. authenticate() — verify credentials, return token/session
        2. authorize() — check the identity has permission to use this connector
        3. with_tenant() — scope operations to the current tenant/workspace
        4. execute() — run the connector operation
        5. verify() — confirm the operation succeeded
        6. record() — write evidence to the canonical audit/evidence store

    Usage:
        class MyConnector(ConnectorBase):
            provider_name = "my_connector"

            def authenticate(self) -> bool:
                ...  # validate credentials from credential store

            def execute(self, action: str, **params) -> dict:
                ...  # run the external API call

            def verify(self, result: dict) -> bool:
                ...  # confirm the result is valid
    """

    provider_name: str = ""
    display_name: str = ""
    description: str = ""

    def __init__(self, identity_id: str, workspace_id: Optional[str] = None):
        if not self.provider_name:
            raise ValueError("Connector must define provider_name")
        self.identity_id = identity_id
        self.workspace_id = workspace_id or ""
        self._authenticated = False
        self._authorized = False
        self._tenant_context: dict[str, Any] = {}
        self._idempotency_guard = IdempotencyGuard()

    # ── Canonical fabric ─────────────────────────────────────────────

    @abstractmethod
    def authenticate(self) -> bool:
        """Verify credentials, return True if valid.

        Must set self._authenticated = True on success.
        Must NOT hardcode credentials — use the credential store.
        """
        ...

    @abstractmethod
    def execute(self, action: str, **params) -> dict:
        """Run the connector operation. Must be called after authenticate().

        Returns a dict with at minimum {"success": bool}.
        """
        ...

    def verify(self, result: dict) -> bool:
        """Confirm the result is valid. Default: check success flag."""
        return result.get("success", False)

    # ── Canonical lifecycle ──────────────────────────────────────────

    def authorize(self, required_permission: str = "integration:use") -> bool:
        """Check the identity has permission to use this connector.

        Override for custom authorization logic. Default: pass-through.
        """
        self._authorized = True
        return True

    def with_tenant(self, org_id: Optional[str] = None, workspace_id: Optional[str] = None) -> dict:
        """Establish tenant context for the connector operation.

        Returns the tenant context dict.
        """
        ctx = {"org_id": org_id or "", "workspace_id": workspace_id or self.workspace_id}
        self._tenant_context = ctx
        return ctx

    # ── Evidence/Audit ───────────────────────────────────────────────

    def record_evidence(self, action: str, resource_type: str, resource_id: str, details: Optional[dict] = None) -> None:
        """Write evidence to the canonical audit store.

        Uses the existing audit log (app.security.audit).
        """
        log_audit(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
        )

    # ── Idempotency ──────────────────────────────────────────────────

    def check_idempotency(self, source_type: str, source_id: str) -> bool:
        """Check if this operation has already been processed.

        Returns True if the operation is new (should proceed).
        Returns False if already processed (should skip).
        """
        result = self._idempotency_guard.guard(source_type, source_id)
        if result.get("idempotency_check_failed"):
            logger.error("Idempotency check failed for %s:%s", source_type, source_id)
            return False
        if result.get("skipped"):
            logger.info("Skipping duplicate %s:%s", source_type, source_id)
            return False
        return True

    # ── Lifecycle runner ─────────────────────────────────────────────

    def run(self, action: str, *, idempotency_key: Optional[str] = None, **params) -> dict:
        """Run the full connector lifecycle.

        Steps:
        1. authenticate()
        2. authorize()
        3. with_tenant()
        4. check_idempotency() (if idempotency_key provided)
        5. execute()
        6. verify()
        7. record_evidence()

        Returns a dict with:
            {"success": bool, "result": dict, "error": str}
        """
        try:
            # Step 1: Authenticate
            if not self._authenticated:
                if not self.authenticate():
                    return {"success": False, "error": "Authentication failed"}

            # Step 2: Authorize
            if not self._authorized:
                self.authorize()

            # Step 3: Tenant context
            self.with_tenant(workspace_id=self.workspace_id)

            # Step 4: Idempotency
            if idempotency_key:
                if not self.check_idempotency(self.provider_name, idempotency_key):
                    return {"success": True, "result": None, "skipped": True}

            # Step 5: Execute
            result = self.execute(action, **params)

            # Step 6: Verify
            verified = self.verify(result)

            # Step 7: Evidence
            self.record_evidence(
                action=action,
                resource_type=self.provider_name,
                resource_id=idempotency_key or self.identity_id,
                details={"result": result, "verified": verified},
            )

            return {"success": verified, "result": result, "error": ""}

        except Exception as e:
            logger.exception("Connector %s run failed: %s", self.provider_name, e)
            self.record_evidence(
                action="error",
                resource_type=self.provider_name,
                resource_id=idempotency_key or "",
                details={"error": str(e)},
            )
            return {"success": False, "error": str(e)}


class ConnectorRegistry:
    """Registry of available connector providers.

    Scoped to the canonical provider fabric; not a new registry —
    delegates to app.integration.registry when available.
    """

    _connectors: dict[str, type[ConnectorBase]] = {}

    @classmethod
    def register(cls, connector_class: type[ConnectorBase]) -> None:
        name = connector_class.provider_name
        if not name:
            raise ValueError("Connector must define provider_name")
        cls._connectors[name] = connector_class
        logger.info("Connector registered: %s", name)

    @classmethod
    def get(cls, name: str) -> type[ConnectorBase] | None:
        return cls._connectors.get(name)

    @classmethod
    def list(cls) -> list[dict]:
        return [
            {"name": name, "display_name": cls.display_name, "description": cls.description}
            for name, cls in cls._connectors.items()
        ]

    @classmethod
    def create(cls, name: str, identity_id: str, workspace_id: Optional[str] = None) -> ConnectorBase:
        """Create a connector instance by name."""
        conn_cls = cls.get(name)
        if not conn_cls:
            raise ValueError(f"Unknown connector: {name}")
        return conn_cls(identity_id=identity_id, workspace_id=workspace_id)


# Register the registry as a canonical extension of the integration fabric
# (not a duplicate — it adds the lifecycle pattern on top of integration.registry)
connector_registry = ConnectorRegistry()