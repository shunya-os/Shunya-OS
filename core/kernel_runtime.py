"""Kernel Runtime Adapter — wraps core/kernel/ for the canonical pipeline.

This adapter implements the RuntimeInterface contract, registering for
the intent_resolution and object_resolution pipeline stages. It
maintains an in-memory registry of UniversalObjects since core/kernel/
provides the object primitives but not a standalone runtime.

When the real persistence layer is wired, this adapter is replaced.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.kernel import UniversalObject
from core.runtime_pipeline import (
    PipelineContext,
    PipelineStage,
    RuntimeInterface,
)


class KernelRuntime(RuntimeInterface):
    """Canonical Kernel Runtime — the foundation of the SHUNYA OS.

    Responsibilities:
      - Resolve intents into structured object operations
      - Resolve objects by ID or parameters
      - Create UniversalObjects in the in-memory registry

    Prohibitions:
      - Must never execute business actions
      - Must never mutate state outside the kernel registry
      - Must never query external systems
    """

    name: str = "kernel"
    stages: list[PipelineStage] | None = None

    def __init__(self) -> None:
        self._registry: dict[str, UniversalObject] = {}
        self._object_count: int = 0
        self.stages = [
            PipelineStage.INTENT_RESOLUTION,
            PipelineStage.OBJECT_RESOLUTION,
        ]

    # ------------------------------------------------------------------
    # Pipeline stage handlers
    # ------------------------------------------------------------------

    def process(self, context: PipelineContext, stage: PipelineStage) -> dict[str, Any]:
        """Process the given pipeline stage.

        For INTENT_RESOLUTION:
          - Parses the intent string and parameters
          - Returns structured intent metadata

        For OBJECT_RESOLUTION:
          - If object_id is provided, resolves an existing object
          - If parameters contain object creation fields, creates a new object
          - Returns the resolved/created object as a dict
        """
        if stage == PipelineStage.INTENT_RESOLUTION:
            return self._resolve_intent(context)
        if stage == PipelineStage.OBJECT_RESOLUTION:
            return self._resolve_object(context)
        return {"status": "noop", "stage": stage.value}

    def _resolve_intent(self, context: PipelineContext) -> dict[str, Any]:
        """Parse and validate the intent, returning structured metadata."""
        intent = context.intent
        params = context.parameters or {}

        # Canonical intent catalog — maps intents to their expected parameters
        intent_spec: dict[str, dict[str, Any]] = {
            "create_object": {
                "type": "object",
                "required_params": ["name", "object_type"],
                "description": "Create a new universal object",
            },
            "view_object": {
                "type": "object",
                "required_params": ["object_id"],
                "description": "View an existing object",
            },
            "update_object": {
                "type": "object",
                "required_params": ["object_id"],
                "description": "Update an existing object",
            },
            "delete_object": {
                "type": "object",
                "required_params": ["object_id"],
                "description": "Archive an existing object",
            },
            "create_space": {
                "type": "space",
                "required_params": ["name"],
                "description": "Create a new space",
            },
            "sign_in": {
                "type": "auth",
                "required_params": ["email"],
                "description": "Authenticate a user",
            },
            "talk_to_customer": {
                "type": "conversation",
                "required_params": [],
                "description": "Engage with a person or organization",
            },
            "understand_opportunity": {
                "type": "knowledge",
                "required_params": [],
                "description": "Learn about a potential value exchange",
            },
            "execute_work": {
                "type": "execution",
                "required_params": [],
                "description": "Perform a defined action",
            },
        }

        spec = intent_spec.get(intent)
        if spec is None:
            return {
                "status": "completed",
                "intent": intent,
                "valid": False,
                "message": f"Unknown intent '{intent}'. No handler registered.",
                "suggested_intents": list(intent_spec.keys()),
            }

        # Validate required parameters
        missing = [p for p in spec["required_params"] if p not in params]
        if missing:
            return {
                "status": "completed",
                "intent": intent,
                "valid": False,
                "message": f"Missing required parameters: {', '.join(missing)}",
                "required_params": spec["required_params"],
            }

        return {
            "status": "completed",
            "intent": intent,
            "valid": True,
            "intent_type": spec["type"],
            "description": spec["description"],
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }

    def _resolve_object(self, context: PipelineContext) -> dict[str, Any]:
        """Resolve or create an object based on pipeline context."""
        params = context.parameters or {}

        # If object_id is already set, resolve existing object
        if context.object_id:
            obj = self._registry.get(context.object_id)
            if obj is None:
                return {
                    "status": "completed",
                    "object_id": context.object_id,
                    "found": False,
                    "message": f"Object '{context.object_id}' not found in registry.",
                }
            return {
                "status": "completed",
                "object_id": obj.object_id,
                "found": True,
                "object_type": obj.object_type,
                "name": obj.name,
                "obj_status": obj.status.value if hasattr(obj.status, "value") else str(obj.status),
            }

        # If intent is to create, build a UniversalObject
        if context.intent == "create_object":
            obj_type = params.get("object_type", "generic")
            obj_name = params.get("name", "Untitled")
            created_by = context.identity_id or "system"
            owner_id = params.get("owner_id", created_by)

            obj = UniversalObject(
                object_type=obj_type,
                name=obj_name,
                created_by=created_by,
                updated_by=created_by,
                owner_id=owner_id,
                tags=params.get("tags"),
                description=params.get("description", ""),
                tenant_id=params.get("tenant_id"),
                space_id=params.get("space_id"),
            )

            self._registry[obj.object_id] = obj
            self._object_count += 1

            # Update pipeline context with the new object_id
            context.object_id = obj.object_id

            return {
                "status": "completed",
                "object_id": obj.object_id,
                "found": True,
                "object_type": obj.object_type,
                "name": obj.name,
                "obj_status": obj.status.value if hasattr(obj.status, "value") else str(obj.status),
                "created": True,
            }

        # No object to resolve — this is a no-op for non-object intents
        return {
            "status": "noop",
            "message": f"Intent '{context.intent}' does not require object resolution.",
        }

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    def get_object(self, object_id: str) -> UniversalObject | None:
        """Return a UniversalObject by ID."""
        return self._registry.get(object_id)

    def list_objects(self) -> list[dict[str, Any]]:
        """Return a summary of all registered objects."""
        return [
            {
                "object_id": obj.object_id,
                "name": obj.name,
                "object_type": obj.object_type,
                "status": obj.status.value if hasattr(obj.status, "value") else str(obj.status),
            }
            for obj in self._registry.values()
        ]

    def health_check(self) -> dict[str, Any]:
        """Return health status of the kernel runtime."""
        return {
            "status": "healthy",
            "runtime": "kernel",
            "object_count": self._object_count,
            "registry_size": len(self._registry),
            "supported_intents": [
                "create_object", "view_object", "update_object",
                "delete_object", "create_space", "sign_in",
                "talk_to_customer", "understand_opportunity", "execute_work",
            ],
        }


__all__ = ["KernelRuntime"]