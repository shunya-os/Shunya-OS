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


def get_executive_home(identity_id: str) -> dict[str, Any]:
    """Assemble Executive Home data from the OS pipeline.

    Returns:
      - health: pipeline health summary
      - priorities: dynamically generated priorities from runtime state
      - recent_activity: chronological timeline of events
      - active_commitments: current commitments from the runtime
      - object_summary: counts and type breakdown
      - generated_at: timestamp
    """
    os = get_os()
    health = os.health_check()

    # Gather data from registered runtimes
    runtimes = os.runtimes
    runtime_summary = {}
    for name, runtime in runtimes.items():
        try:
            h = runtime.health_check()
            runtime_summary[name] = {"status": h.get("status", "unknown")}
            for key in ("object_count", "identity_count", "supported_intents",
                        "supported_projections", "runtime_count"):
                if key in h:
                    runtime_summary[name][key] = h[key]
        except Exception:
            runtime_summary[name] = {"status": "error"}

    # ── Recent Activity Timeline ─────────────────────────────────
    recent_activity = []
    try:
        from core.object_service import get_object_service
        svc = get_object_service()

        # Query recent canonical objects as activity events (org_id=0 covers all)
        objects = svc.search(query="", organization_id=0, limit=20)
        for obj in objects:
            recent_activity.append({
                "type": "object_updated",
                "title": f"Object modified: {obj.get('name', 'Unknown')}",
                "description": f"{obj.get('object_type', 'unknown')} was updated",
                "object_type": obj.get("object_type", ""),
                "object_id": obj.get("object_id", ""),
                "timestamp": obj.get("updated_at", ""),
                "actor": obj.get("created_by", "system"),
            })

        # Query recent conversations
        from app.founder.models import FounderConversation
        convs = FounderConversation.query.filter_by(
            status="active"
        ).order_by(
            FounderConversation.updated_at.desc()
        ).limit(10).all()

        for conv in convs:
            recent_activity.append({
                "type": "conversation",
                "title": f"Conversation: {conv.title}",
                "description": f"Active conversation on {conv.object_id}",
                "object_type": "conversation",
                "object_id": conv.conv_id,
                "timestamp": conv.updated_at.isoformat() if conv.updated_at else "",
                "actor": conv.identity_id or "system",
            })

        # Sort all activity by timestamp descending
        recent_activity.sort(
            key=lambda x: x.get("timestamp", ""),
            reverse=True,
        )
        recent_activity = recent_activity[:20]

    except Exception:
        recent_activity = []

    # ── Active Commitments ───────────────────────────────────────
    active_commitments = []
    try:
        from core.object_service import get_object_service
        svc = get_object_service()
        objects = svc.search(query="", organization_id=0, limit=10)

        for obj in objects:
            active_commitments.append({
                "id": obj.get("object_id", ""),
                "title": obj.get("name", ""),
                "type": obj.get("object_type", ""),
                "status": obj.get("status", "active"),
                "owner": obj.get("created_by", ""),
                "due_date": None,
                "progress": 0,
                "related_objects": [],
            })
    except Exception:
        pass

    # ── Object Summary ──────────────────────────────────────────
    object_summary = {"total": 0, "by_type": {}, "at_risk": 0}
    try:
        from core.object_service import get_object_service
        svc = get_object_service()
        type_counts = svc.count_by_type(organization_id=0)
        object_summary["total"] = sum(type_counts.values())
        object_summary["by_type"] = type_counts
    except Exception:
        pass

    # ── Priorities (dynamically generated from runtime state) ────
    priorities = []
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)

    # Priority 1: At-risk objects
    if object_summary.get("at_risk", 0) > 0:
        priorities.append({
            "id": "at_risk_objects",
            "title": f"{object_summary['at_risk']} object(s) at risk",
            "reason": "Objects marked at-risk require immediate attention",
            "affected_objects": object_summary.get("at_risk", 0),
            "urgency": "high",
            "recommended_action": "Review and update at-risk objects",
        })

    # Priority 2: Pipeline health
    health_status = health.get("status", "unknown")
    if health_status not in ("ok", "healthy"):
        priorities.append({
            "id": "pipeline_health",
            "title": "System pipeline health check",
            "reason": f"Pipeline status: {health_status}",
            "affected_objects": 0,
            "urgency": "high" if health_status == "error" else "medium",
            "recommended_action": "Inspect pipeline health and runtime status",
        })

    # Priority 3: Recent activity
    if recent_activity:
        priorities.append({
            "id": "recent_activity",
            "title": f"{len(recent_activity)} recent events",
            "reason": "System has been active since your last visit",
            "affected_objects": len(recent_activity),
            "urgency": "medium",
            "recommended_action": "Review recent activity timeline",
        })

    # Priority 4: Active commitments
    if active_commitments:
        priorities.append({
            "id": "active_commitments",
            "title": f"{len(active_commitments)} active commitment(s)",
            "reason": "These commitments require your attention or follow-up",
            "affected_objects": len(active_commitments),
            "urgency": "medium",
            "recommended_action": "Review and update commitment status",
        })

    # Priority 5: Empty state guidance
    if object_summary["total"] == 0:
        priorities.append({
            "id": "getting_started",
            "title": "Welcome to SHUNYA",
            "reason": "Your organization has no business objects yet",
            "affected_objects": 0,
            "urgency": "low",
            "recommended_action": "Create your first business object to begin",
        })

    return {
        "success": True,
        "data": {
            "health": {
                "status": health_status,
                "bootstrapped": health.get("bootstrapped", False),
                "runtime_count": health.get("runtime_count", 0),
                "pipeline": health.get("pipeline", {}),
            },
            "priorities": priorities,
            "recent_activity": recent_activity,
            "active_commitments": active_commitments,
            "object_summary": object_summary,
            "runtimes": runtime_summary,
            "generated_at": now.isoformat(),
        },
    }


def get_identity_name(identity_id: str) -> str | None:
    """Resolve an identity's display name from the canonical OS Identity model.

    Args:
        identity_id: The canonical identity ID (sid_ + hex).

    Returns:
        The display name, or None if the identity is not found.
    """
    os = get_os()
    identity_runtime = os.get_runtime("identity")
    if identity_runtime:
        identity = identity_runtime.get_identity(identity_id)
        if identity:
            return identity.display_name
    return None


__all__ = [
    "create_object",
    "create_space",
    "get_executive_home",
    "get_identity_name",
    "get_pipeline_trace",
    "process_intent",
    "sign_in",
    "talk_to_customer",
    "view_object",
]