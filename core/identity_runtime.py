"""Identity Runtime Adapter — wraps core/identity/IdentityEngine for pipeline.

This adapter orchestrates identity resolution through the shared
IdentityEngine repository. It does NOT own identity persistence — the
engine owns the store, the runtime orchestrates the resolution.

Following the architecture principle:
  Runtimes orchestrate, repositories persist.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.identity import AuthMethod, EntityType, IdentityEngine
from core.runtime_pipeline import (
    PipelineContext,
    PipelineStage,
    RuntimeInterface,
)


class IdentityRuntime(RuntimeInterface):
    """Canonical Identity Runtime — resolves who is acting.

    Responsibilities:
      - Resolve an identity from the pipeline context (identity_id, email)
      - Create identities on sign-up
      - Persist identities via the repository
      - Return resolved identity metadata to the pipeline

    Prohibitions:
      - Must never own identity persistence (delegates to IdentityEngine + repository)
      - Must never execute business actions
      - Must never create/update business objects
    """

    name: str = "identity"
    stages: list[PipelineStage] | None = None

    def __init__(self, engine: IdentityEngine | None = None,
                 repository: Any | None = None) -> None:
        self._engine = engine or IdentityEngine()
        self._repository = repository
        self.stages = [PipelineStage.IDENTITY_RESOLUTION]

    def load_persisted(self) -> None:
        """Load all persisted identities from the repository into the engine.

        Called during system bootstrap. Idempotent.
        """
        if not self._repository:
            return
        try:
            identities = self._repository.all_core()
            for ident in identities:
                if ident.identity_id not in self._engine._identities:
                    self._engine._identities[ident.identity_id] = ident
                    # Rebuild auth index for the loaded identity
                    for am in ident.auth_methods:
                        self._engine._auth_index[(am.method_type, am.identifier)] = ident.identity_id
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "Failed to load persisted identities: %s", exc)

    # ------------------------------------------------------------------
    # Pipeline stage handler
    # ------------------------------------------------------------------

    def process(self, context: PipelineContext, stage: PipelineStage) -> dict[str, Any]:
        """Process the identity_resolution pipeline stage.

        Resolution strategy (in order):
          1. If context.identity_id is set, resolve by ID
          2. If parameters contain 'email', resolve by email
          3. If parameters contain 'identifier', resolve by any identifier
          4. If sign_in intent and no identity, create a new identity
          5. Otherwise, return noop
        """
        if stage != PipelineStage.IDENTITY_RESOLUTION:
            return {"status": "noop", "stage": stage.value}

        params = context.parameters or {}

        # Strategy 1: Resolve by identity_id
        if context.identity_id:
            identity = self._engine.get_identity(context.identity_id)
            if identity is not None:
                return self._identity_result(identity, "resolved_by_id")
            return {
                "status": "completed",
                "found": False,
                "message": f"Identity '{context.identity_id}' not found.",
            }

        # Strategy 2: Resolve by email
        email = params.get("email", "")
        if email:
            identity = self._engine.find_by_email(email)
            if identity is not None:
                context.identity_id = identity.identity_id
                return self._identity_result(identity, "resolved_by_email")
            # Identity not found — may need creation (strategy 4)

        # Strategy 3: Resolve by any identifier
        identifier = params.get("identifier", "")
        if identifier:
            identity = self._engine.resolve_identity(identifier)
            if identity is not None:
                context.identity_id = identity.identity_id
                return self._identity_result(identity, "resolved_by_identifier")

        # Strategy 4: Create identity on sign-up
        if context.intent == "sign_in" and email:
            display_name = params.get("name", email.split("@")[0])
            identity = self._engine.create_identity(
                display_name=display_name,
                entity_type=EntityType.HUMAN,
                auth_methods=[
                                        AuthMethod(method_type="email", identifier=email, verified_at=datetime.now(timezone.utc), is_primary=True),
                                    ],
            )
            context.identity_id = identity.identity_id
            result = self._identity_result(identity, "created")
            result["created"] = True
            # Persist via repository if available
            if self._repository:
                try:
                    self._repository.create_core(
                        display_name=display_name,
                        entity_type="human",
                        auth_methods=[{"method_type": "email", "identifier": email}],
                    )
                except Exception as exc:
                    import logging
                    logging.getLogger(__name__).warning(
                        "Failed to persist identity for %s: %s", email, exc)
            return result

        # Strategy 5: No identity to resolve
        return {
            "status": "noop",
            "message": f"Intent '{context.intent}' does not require identity resolution.",
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _identity_result(self, identity: Any, source: str) -> dict[str, Any]:
        """Build a standard identity resolution result."""
        return {
            "status": "completed",
            "found": True,
            "identity_id": identity.identity_id,
            "display_name": identity.display_name,
            "entity_type": identity.entity_type.value if hasattr(identity.entity_type, "value") else str(identity.entity_type),
            "source": source,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Delegated identity operations (through the shared repository)
    # ------------------------------------------------------------------

    def get_identity(self, identity_id: str) -> Any | None:
        """Resolve identity through the shared engine."""
        return self._engine.get_identity(identity_id)

    def find_by_email(self, email: str) -> Any | None:
        """Find identity by email through the shared engine."""
        return self._engine.find_by_email(email)

    def get_identity_count(self) -> int:
        """Return total identity count from the shared engine."""
        return self._engine.get_identity_count()

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    def health_check(self) -> dict[str, Any]:
        """Return health status. Delegates to the engine for its counts."""
        return {
            "status": "healthy",
            "runtime": "identity",
            "identity_count": self._engine.get_identity_count(),
            "active_count": self._engine.get_active_count(),
            "resolved_via": "shared_identity_engine",
        }


__all__ = ["IdentityRuntime"]