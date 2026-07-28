"""OS Adapter — Flask-friendly wrappers around ShunyaOS.process_intent().

This adapter is the ONLY Flask code that calls ShunyaOS. Founder routes
call these helpers. No route may call ShunyaOS directly or bypass the
pipeline.

The adapter follows the architectural principle:
  Flask transports. ShunyaOS orchestrates. Runtimes execute. Repositories persist.
"""

from __future__ import annotations

from typing import Any

from core.os import get_os


def process_intent(
    intent: str,
    parameters: dict[str, Any] | None = None,
    identity_id: str | None = None,
    object_id: str | None = None,
) -> dict[str, Any]:
    """Process an intent through the canonical OS pipeline.

    This is the single entry point for ALL Founder API actions.
    No Flask route may bypass this function.

    Args:
        intent: Business intent string (e.g. 'create_object', 'sign_in').
        parameters: Structured intent parameters from the request.
        identity_id: Resolved identity ID from session.
        object_id: Target object ID (if applicable).

    Returns:
        A dict with pipeline execution results including:
          - pipeline: full PipelineContext with trace
          - runtime: runtime-specific results merged from stages
    """
    os = get_os()
    ctx = os.process_intent(
        intent=intent,
        parameters=parameters,
        identity_id=identity_id,
        object_id=object_id,
    )
    return {
        "success": ctx.state == "completed",
        "state": ctx.state,
        "intent_id": ctx.intent_id,
        "identity_id": ctx.identity_id,
        "object_id": ctx.object_id,
        "trace": [
            {"stage": s.stage, "runtime": s.runtime, "status": s.status, "error": s.error}
            for s in ctx.trace
        ],
        "runtime_results": {
            s.stage: s.result for s in ctx.trace if s.result and s.status != "noop"
        },
    }


def sign_in(email: str, password: str = "", name: str = "") -> dict[str, Any]:
    """Sign in or create identity.

    Thin wrapper: parses the request, delegates to the pipeline,
    returns pipeline result.
    """
    return process_intent(
        intent="sign_in",
        parameters={
            "email": email,
            "password": password,
            "name": name or email.split("@")[0],
        },
    )


def create_object(
    name: str,
    object_type: str,
    space_id: str,
    identity_id: str,
    content: str = "",
    description: str = "",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Create an object through the OS pipeline."""
    return process_intent(
        intent="create_object",
        parameters={
            "name": name,
            "object_type": object_type,
            "space_id": space_id,
            "content": content,
            "description": description,
            "tags": tags or [],
        },
        identity_id=identity_id,
    )


def view_object(object_id: str, identity_id: str) -> dict[str, Any]:
    """View an object through the OS pipeline."""
    return process_intent(
        intent="view_object",
        parameters={"object_id": object_id},
        identity_id=identity_id,
        object_id=object_id,
    )


def create_space(
    name: str,
    identity_id: str,
    space_type: str = "organization",
    description: str = "",
) -> dict[str, Any]:
    """Create a space through the OS pipeline."""
    return process_intent(
        intent="create_space",
        parameters={
            "name": name,
            "space_type": space_type,
            "description": description,
        },
        identity_id=identity_id,
    )


def talk_to_customer(
    message: str,
    identity_id: str,
    object_id: str | None = None,
) -> dict[str, Any]:
    """Process a conversation message through the OS pipeline."""
    return process_intent(
        intent="talk_to_customer",
        parameters={"message": message},
        identity_id=identity_id,
        object_id=object_id,
    )


def get_pipeline_trace(intent_id: str) -> dict[str, Any] | None:
    """Retrieve a pipeline trace by intent_id.

    Currently a stub — traces are ephemeral. Will be backed by persistent
    storage when the Audit Runtime is wired.
    """
    # TODO(L-03): Wire audit runtime for persistent trace storage
    return None


__all__ = [
    "create_object",
    "create_space",
    "get_pipeline_trace",
    "process_intent",
    "sign_in",
    "talk_to_customer",
    "view_object",
]