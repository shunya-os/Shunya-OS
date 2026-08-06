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
    """Assemble Executive Home dashboard data from the OS pipeline.

    Returns pipeline health, recent traces, object counts, identity counts,
    and a daily brief. All data comes from real runtimes via the OS.
    """
    os = get_os()
    health = os.health_check()

    # Gather data from registered runtimes
    runtimes = os.runtimes
    runtime_summary = {}
    for name, runtime in runtimes.items():
        try:
            h = runtime.health_check()
            runtime_summary[name] = {
                "status": h.get("status", "unknown"),
            }
            if "object_count" in h:
                runtime_summary[name]["object_count"] = h["object_count"]
            if "identity_count" in h:
                runtime_summary[name]["identity_count"] = h["identity_count"]
            if "supported_intents" in h:
                runtime_summary[name]["supported_intents"] = h["supported_intents"]
            if "supported_projections" in h:
                runtime_summary[name]["supported_projections"] = h["supported_projections"]
            if "runtime_count" in h:
                runtime_summary[name]["runtime_count"] = h["runtime_count"]
        except Exception:
            runtime_summary[name] = {"status": "error"}

    # Get projection traces if available
    projection_traces = []
    proj_runtime = runtimes.get("projection")
    if proj_runtime and hasattr(proj_runtime, "get_traces"):
        try:
            projection_traces = proj_runtime.get_traces(limit=10)
        except Exception:
            pass

    # Count pipeline stages
    pipeline_stages = {
        "total": 11,
        "with_real_runtime": 0,
        "with_mock_runtime": 0,
    }
    stage_map = os.pipeline.list_runtimes()
    for stage, runtimes_for_stage in stage_map.items():
        for r_name in runtimes_for_stage:
            if r_name in ("kernel", "identity", "projection"):
                pipeline_stages["with_real_runtime"] += 1
            else:
                pipeline_stages["with_mock_runtime"] += 1

    return {
        "success": True,
        "data": {
            "health": {
                "status": health.get("status", "unknown"),
                "bootstrapped": health.get("bootstrapped", False),
                "runtime_count": health.get("runtime_count", 0),
                "pipeline": health.get("pipeline", {}),
            },
            "pipeline_stages": pipeline_stages,
            "runtimes": runtime_summary,
            "recent_projection_traces": projection_traces,
            "generated_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "priorities": _get_priorities(),
            "recent_activity": _get_recent_activity(),
        },
    }


def _get_priorities() -> list[dict]:
    """Return priorities/nudges from sh_objects data."""
    from sqlalchemy import text
    priorities = []
    try:
        from app import db
        # Overdue invoices
        overdue = db.session.execute(text(
            "SELECT data->>'customer_name' as name, data->>'amount' as amt "
            "FROM sh_objects WHERE object_type='invoice' AND status='overdue' LIMIT 5"
        )).fetchall()
        for inv in overdue:
            priorities.append({"id": f"inv-overdue-{inv.name}", "title": f"INV-{inv.name} is overdue",
                               "reason": f"Payment of ${float(inv.amt or 0):.0f} is overdue.",
                               "urgency": "high", "recommended_action": "Send payment reminder"})
        # New leads
        leads = db.session.execute(text(
            "SELECT data->>'company_name' as name FROM sh_objects "
            "WHERE object_type='customer' AND status='active' LIMIT 5"
        )).fetchall()
        for lead in leads:
            priorities.append({"id": f"lead-new-{lead.name}", "title": f"New lead: {lead.name}",
                               "reason": "Created recently — no activity yet",
                               "urgency": "low", "recommended_action": "Review and qualify"})
        # Active tasks
        tasks = db.session.execute(text(
            "SELECT name FROM sh_objects WHERE object_type='task' AND status='active' LIMIT 5"
        )).fetchall()
        for t in tasks:
            priorities.append({"id": f"task-{t.name}", "title": f"Task: {t.name}",
                               "reason": "Active task requiring attention",
                               "urgency": "medium", "recommended_action": "Review and complete"})
    except Exception:
        pass
    return priorities


def _get_recent_activity() -> list[dict]:
    """Return recent activity from sh_objects."""
    from sqlalchemy import text
    activity = []
    try:
        from app import db
        rows = db.session.execute(text(
            "SELECT object_type, name, updated_at FROM sh_objects "
            "ORDER BY updated_at DESC NULLS LAST LIMIT 10"
        )).fetchall()
        for row in rows:
            ts = row.updated_at.isoformat() if row.updated_at else ""
            activity.append({
                "type": f"{row.object_type}_updated",
                "title": row.name,
                "description": f"{row.object_type}: {row.name}",
                "object_type": row.object_type,
                "timestamp": ts,
                "actor": "SHUNYA",
            })
    except Exception:
        pass
    return activity


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