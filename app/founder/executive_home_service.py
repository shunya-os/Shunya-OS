"""Executive Home Service — assembles the founder's primary operating surface.

All data comes from real runtime state and persistent storage.
No placeholder data, no hardcoded text, no fabricated metrics.

Every section answers: "What should I know, and what should I do next?"
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app import db
from app.founder.models import (
    BusinessRelationship,
    FounderConversation,
    FounderMessage,
    FounderSpace,
)
from app.models import Organization, OrgMember
from core.os import get_os
from sqlalchemy import text as _sql_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ago(**kwargs) -> datetime:
    return _now() - timedelta(**kwargs)


def _sql_in(wids: list) -> tuple[str, dict]:
    """Build IN clause + params for SQLite/PostgreSQL compat."""
    if not wids:
        return "FALSE", {}
    parts = [f":_w_{i}" for i in range(len(wids))]
    params = {f"_w_{i}": w for i, w in enumerate(wids)}
    return f"IN ({', '.join(parts)})", params

def _time_ago_label(dt) -> str:
    """Human-readable relative time. Accepts datetime or str."""
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except (ValueError, TypeError):
            return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = _now() - dt
    if diff < timedelta(minutes=1):
        return "just now"
    if diff < timedelta(hours=1):
        mins = int(diff.total_seconds() // 60)
        return f"{mins}m ago"
    if diff < timedelta(days=1):
        hours = int(diff.total_seconds() // 3600)
        return f"{hours}h ago"
    days = diff.days
    return f"{days}d ago"


# ---------------------------------------------------------------------------
# 1. Morning Brief
# ---------------------------------------------------------------------------

def build_morning_brief(identity_id: str) -> dict[str, Any]:
    """Generate a live morning brief from real runtime state.

    Includes: recent activity, important changes, pending work,
    commitments requiring attention, execution status, alerts,
    and organization context.
    """
    # --- Organization context ---
    org_context = {}
    member = OrgMember.query.filter_by(identity_id=identity_id).first()
    if member:
        org = Organization.query.get(member.organization_id)
        if org:
            org_context = {
                "org_id": org.id,
                "org_name": org.name,
                "org_type": org.business_type,
                "org_tagline": org.brand_tagline,
                "org_description": org.brand_description,
            }

    spaces = FounderSpace.query.filter_by(
        identity_id=identity_id, status="active"
    ).all()
    space_ids = [s.space_id for s in spaces]

    items: list[dict[str, Any]] = []
    total_objects = 0
    pending_conversations = 0
    recent_activity_count = 0

    # --- Activity in last 24h ---
    since = _ago(hours=24)

    _ic, _ip = _sql_in(space_ids)
    recently_created = db.session.execute(
        _sql_text(f"SELECT * FROM sh_objects WHERE workspace_id {_ic} AND status = 'active' AND is_deleted IS NOT true AND created_at >= :since ORDER BY created_at DESC"),
        {**_ip, 'since': since},
    ).all() if space_ids else []

    _ic2, _ip2 = _sql_in(space_ids)
    recently_updated = db.session.execute(
        _sql_text(f"SELECT * FROM sh_objects WHERE workspace_id {_ic2} AND status = 'active' AND is_deleted IS NOT true AND updated_at >= :since AND (created_at IS NULL OR created_at < :since) ORDER BY updated_at DESC"),
        {**_ip2, 'since': since},
    ).all() if space_ids else []

    for obj in recently_created:
        items.append({
            "title": f"Created: {obj.name}",
            "meta": f"{obj.object_type} · {_time_ago_label(obj.created_at)}",
            "priority": "info",
            "focus": {"object_id": obj.object_id, "type": "object"},
        })
        recent_activity_count += 1

    for obj in recently_updated:
        items.append({
            "title": f"Updated: {obj.name}",
            "meta": f"{obj.object_type} · {_time_ago_label(obj.updated_at)}",
            "priority": "info",
            "focus": {"object_id": obj.object_id, "type": "object"},
        })
        recent_activity_count += 1

    # --- Active conversations (pending work) ---
    for space in spaces:
        objects_rows = db.session.execute(
            _sql_text("SELECT * FROM sh_objects WHERE workspace_id = :wid AND status = 'active' AND is_deleted IS NOT true"),
            {"wid": space.space_id},
        ).all()
        total_objects += len(objects_rows)
        for obj in objects_rows:
            conv = FounderConversation.query.filter_by(
                object_id=obj.object_id, status="active"
            ).first()
            if conv:
                msg_count = FounderMessage.query.filter_by(
                    conv_id=conv.conv_id
                ).count()
                if msg_count > 0:
                    last_msg = FounderMessage.query.filter_by(
                        conv_id=conv.conv_id
                    ).order_by(FounderMessage.created_at.desc()).first()
                    preview = last_msg.content[:100] if last_msg else ""
                    items.append({
                        "title": f"Conversation on {obj.name}",
                        "meta": preview,
                        "priority": "attention" if msg_count > 2 else "info",
                        "focus": {"object_id": obj.object_id, "type": "object", "conv_id": conv.conv_id},
                    })
                    pending_conversations += 1

    # --- Relationship summary ---
    if space_ids:
        rel_count = BusinessRelationship.query.filter(
            BusinessRelationship.space_id.in_(space_ids),
            BusinessRelationship.status == "active",
        ).count()
        if rel_count > 0:
            items.append({
                "title": f"{rel_count} relationship{'s' if rel_count != 1 else ''} in your network",
                "meta": "Customers, suppliers, partners, team",
                "priority": "info",
                "focus": None,
            })

    # --- Pipeline health status ---
    os = get_os()
    health = os.health_check()
    runtime_count = health.get("runtime_count", 0)
    health_status = health.get("status", "unknown")
    if health_status != "healthy":
        items.append({
            "title": "Pipeline health requires attention",
            "meta": f"Status: {health_status}",
            "priority": "warning",
            "focus": None,
        })

    # --- Fallback when nothing is happening ---
    if not items:
        if not spaces:
            if org_context:
                org_name = org_context.get("org_name", "your organization")
                org_tagline = org_context.get("org_tagline", "")
                items.append({
                    "title": f"Welcome, {org_name} is ready — create your first space",
                    "meta": org_tagline or f"Your {org_context.get('org_type', 'business').title()} operating system is listening",
                    "priority": "info",
                    "focus": None,
                })
            else:
                items.append({
                    "title": "Welcome to SHUNYA — create your first space to get started",
                    "meta": "Your operating system is ready and listening",
                    "priority": "info",
                    "focus": None,
                })
        else:
            items.append({
                "title": f"Everything is quiet across {len(spaces)} space{'s' if len(spaces) != 1 else ''}",
                "meta": f"{total_objects} active object{'s' if total_objects != 1 else ''} · all caught up",
                "priority": "info",
                "focus": None,
            })

    return {
        "items": items[:8],
        "summary": {
            "active_spaces": len(spaces),
            "active_objects": total_objects,
            "pending_conversations": pending_conversations,
            "recent_activity": recent_activity_count,
            "runtime_count": runtime_count,
        },
    }


# ---------------------------------------------------------------------------
# 2. SHUNYA Recommendations
# ---------------------------------------------------------------------------

def build_recommendations(identity_id: str) -> list[dict[str, Any]]:
    """Generate recommendations from current business state.

    Every recommendation includes: title, explanation, why SHUNYA recommends it,
    priority, originating runtime, action available.
    """
    spaces = FounderSpace.query.filter_by(
        identity_id=identity_id, status="active"
    ).all()
    space_ids = [s.space_id for s in spaces]

    recommendations: list[dict[str, Any]] = []

    if not spaces:
        # New founder — recommend creating first space
        recommendations.append({
            "id": "rec_create_first_space",
            "title": "Create your first Space",
            "explanation": "Spaces are where your business lives — objects, conversations, and relationships are organized within them.",
            "why": "No spaces exist yet. A space gives SHUNYA context to work within.",
            "priority": "high",
            "originating_runtime": "kernel",
            "action": {"type": "navigate", "target": "/founder/space/create", "label": "Create Space"},
        })
        return recommendations

    _ic4, _ip4 = _sql_in(space_ids)
    total_objects = db.session.execute(
        _sql_text(f"SELECT COUNT(*) FROM sh_objects WHERE workspace_id {_ic4} AND status = 'active' AND is_deleted IS NOT true"),
        _ip4,
    ).scalar() or 0 if space_ids else 0

    # --- No objects yet ---
    if total_objects == 0:
        recommendations.append({
            "id": "rec_create_first_object",
            "title": "Create your first Object",
            "explanation": "Objects represent the things you work on — documents, projects, leads, products, anything.",
            "why": f"You have {len(spaces)} space{'s' if len(spaces) != 1 else ''} but no objects yet. Objects give SHUNYA something to reason about.",
            "priority": "high",
            "originating_runtime": "kernel",
            "action": {"type": "navigate", "target": "/founder/space/create", "label": "Create Object"},
        })
        return recommendations

    # --- Check object type diversity ---
    from sqlalchemy import func
    _ic5, _ip5 = _sql_in(space_ids)
    type_counts = dict(
        db.session.execute(
            _sql_text(f"SELECT object_type, COUNT(*) as cnt FROM sh_objects WHERE workspace_id {_ic5} AND status = 'active' AND is_deleted IS NOT true GROUP BY object_type"),
            _ip5,
        ).all()
    ) if space_ids else {}
    dominant_type = max(type_counts, key=type_counts.get) if type_counts else ""

    if len(type_counts) == 1 and total_objects >= 3:
        recommendations.append({
            "id": "rec_add_object_types",
            "title": f"Add variety to your objects",
            "explanation": f"All {total_objects} object{'s' if total_objects != 1 else ''} are '{dominant_type}' type. Different object types help SHUNYA understand different aspects of your business.",
            "why": "Diverse object types enable richer context assembly and more relevant recommendations.",
            "priority": "medium",
            "originating_runtime": "kernel",
            "action": {"type": "navigate", "target": "/founder/space/create", "label": "Create Different Object Type"},
        })

    # --- Unresolved conversations ---
    pending_convs = 0
    for space in spaces:
        objects = db.session.execute(
            _sql_text("SELECT * FROM sh_objects WHERE workspace_id = :wid AND status = 'active' AND is_deleted IS NOT true"),
            {"wid": space.space_id},
        ).all()
        for obj in objects:
            conv = FounderConversation.query.filter_by(
                object_id=obj.object_id, status="active"
            ).first()
            if conv:
                human_msgs = FounderMessage.query.filter_by(
                    conv_id=conv.conv_id, role="human"
                ).count()
                assistant_msgs = FounderMessage.query.filter_by(
                    conv_id=conv.conv_id, role="assistant"
                ).count()
                if human_msgs > assistant_msgs:
                    pending_convs += 1
                    recommendations.append({
                        "id": f"rec_continue_conv_{conv.conv_id[:8]}",
                        "title": f"Continue discussing {obj.name}",
                        "explanation": f"There are unresponded messages in this conversation.",
                        "why": "You last asked something about this object. SHUNYA can help resolve it.",
                        "priority": "medium",
                        "originating_runtime": "identity",
                        "action": {"type": "navigate", "target": f"/founder/object/{obj.object_id}", "label": "Open Conversation"},
                    })

    # --- Relationship types check ---
    rel_types = dict(
        db.session.query(
            BusinessRelationship.rel_type, func.count(BusinessRelationship.id)
        ).filter(
            BusinessRelationship.space_id.in_(space_ids),
            BusinessRelationship.status == "active",
        ).group_by(BusinessRelationship.rel_type).all()
    )

    identity_runtime = get_os().get_runtime("identity")
    has_identities = False
    if identity_runtime is not None:
        health = identity_runtime.health_check()
        has_identities = health.get("identity_count", 0) > 0
    if "customer" not in rel_types and has_identities:
        recommendations.append({
            "id": "rec_add_customers",
            "title": "Add your first Customer relationship",
            "explanation": "Customers are the most important relationship type. SHUNYA can track interactions, commitments, and history.",
            "why": "No customer relationships exist yet. Tracking customers helps SHUNYA understand your business.",
            "priority": "medium",
            "originating_runtime": "kernel",
            "action": {"type": "navigate", "target": "/founder/relationships/create", "label": "Add Customer"},
        })

    # --- Default if no specific recommendations ---
    if not recommendations:
        recommendations.append({
            "id": "rec_explore_objects",
            "title": f"Explore your {total_objects} object{'s' if total_objects != 1 else ''}",
            "explanation": f"You have {total_objects} active object{'s' if total_objects != 1 else ''} across {len(spaces)} space{'s' if len(spaces) != 1 else ''}. Each one can be discussed, updated, and connected.",
            "why": "Exploring your existing objects gives SHUNYA more context about what matters to you.",
            "priority": "low",
            "originating_runtime": "kernel",
            "action": {"type": "navigate", "target": "/founder/home", "label": "Browse Objects"},
        })

    return recommendations[:5]


# ---------------------------------------------------------------------------
# 3. Business Health
# ---------------------------------------------------------------------------

def build_business_health(identity_id: str) -> dict[str, Any]:
    """Operational health overview from real runtime state."""
    spaces = FounderSpace.query.filter_by(
        identity_id=identity_id, status="active"
    ).all()
    space_ids = [s.space_id for s in spaces]

    _ic7, _ip7 = _sql_in(space_ids)
    total_objects = db.session.execute(
        _sql_text(f"SELECT COUNT(*) FROM sh_objects WHERE workspace_id {_ic7} AND status = 'active' AND is_deleted IS NOT true"),
        _ip7,
    ).scalar() or 0 if space_ids else 0

    total_relationships = BusinessRelationship.query.filter(
        BusinessRelationship.space_id.in_(space_ids),
        BusinessRelationship.status == "active",
    ).count() if space_ids else 0

    _ic8, _ip8 = _sql_in(space_ids)
    active_conversations = 0
    if space_ids:
        obj_rows = db.session.execute(
            _sql_text(f"SELECT object_id FROM sh_objects WHERE workspace_id {_ic8} AND status = 'active' AND is_deleted IS NOT true"),
            _ip8,
        ).all()
        for obj in obj_rows:
            conv = FounderConversation.query.filter_by(
                object_id=obj.object_id, status="active"
            ).first()
            if conv:
                active_conversations += 1

    os = get_os()
    health = os.health_check()
    pipeline = health.get("pipeline", {})

    # Count real vs mock runtimes
    stage_map = os.pipeline.list_runtimes() if hasattr(os.pipeline, 'list_runtimes') else {}
    real_runtime_count = 0
    mock_runtime_count = 0
    for stage, runtimes in stage_map.items():
        for r_name in runtimes:
            if r_name in ("kernel", "identity", "projection"):
                real_runtime_count += 1
            else:
                mock_runtime_count += 1

    # Top-level assessment
    warnings: list[str] = []
    if mock_runtime_count > 0:
        warnings.append(f"{mock_runtime_count} runtime{'s' if mock_runtime_count != 1 else ''} still in mock mode")
    if not space_ids:
        warnings.append("No spaces created yet")
    if active_conversations == 0 and total_objects > 0:
        warnings.append("No active conversations — SHUNYA is waiting")

    assessment = "running" if not warnings else "attention_needed"
    if not space_ids:
        assessment = "cold_start"

    return {
        "assessment": assessment,
        "pipeline_status": health.get("status", "unknown"),
        "spaces": len(spaces),
        "objects": total_objects,
        "relationships": total_relationships,
        "active_conversations": active_conversations,
        "real_runtimes": real_runtime_count,
        "mock_runtimes": mock_runtime_count,
        "warnings": warnings[:3],
    }


# ---------------------------------------------------------------------------
# 4. Recent Activity
# ---------------------------------------------------------------------------

def build_recent_activity(identity_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Recent founder-visible activity from persistent state."""
    spaces = FounderSpace.query.filter_by(
        identity_id=identity_id, status="active"
    ).all()
    space_ids = [s.space_id for s in spaces]

    activities: list[dict[str, Any]] = []

    if not space_ids:
        return activities

    # Recently created objects
    _ic9, _ip9 = _sql_in(space_ids)
    objects = db.session.execute(
        _sql_text(f"SELECT * FROM sh_objects WHERE workspace_id {_ic9} AND status = 'active' AND is_deleted IS NOT true ORDER BY created_at DESC LIMIT :lim"),
        {**_ip9, 'lim': limit},
    ).all()

    for obj in objects:
        activities.append({
            "type": "object_created",
            "title": obj.name,
            "subtitle": f"{obj.object_type} · {_time_ago_label(obj.created_at)}",
            "timestamp": str(obj.created_at) if obj.created_at else None,
            "focus": {"object_id": obj.object_id, "type": "object"},
        })

    # Recently updated objects (not newly created)
    _ic9b, _ip9b = _sql_in(space_ids)
    updated_objects = db.session.execute(
        _sql_text(f"SELECT * FROM sh_objects WHERE workspace_id {_ic9b} AND status = 'active' AND is_deleted IS NOT true ORDER BY updated_at DESC LIMIT :lim"),
        {**_ip9b, 'lim': limit},
    ).all()

    for obj in updated_objects:
        # Skip if object_id already exists in activities (any type)
        if any(a.get("focus", {}).get("object_id") == obj.object_id for a in activities):
            continue
        activities.append({
            "type": "object_updated",
            "title": obj.name,
            "subtitle": f"{obj.object_type} · {_time_ago_label(obj.updated_at)}",
            "timestamp": str(obj.updated_at) if obj.updated_at else None,
            "focus": {"object_id": obj.object_id, "type": "object"},
        })

    # Recent conversations
    conversations = FounderConversation.query.filter(
        FounderConversation.identity_id == identity_id,
        FounderConversation.status == "active",
    ).order_by(FounderConversation.updated_at.desc()).limit(5).all()

    for conv in conversations:
        activities.append({
            "type": "conversation",
            "title": conv.title,
            "subtitle": f"Conversation · {_time_ago_label(conv.updated_at)}",
            "timestamp": conv.updated_at.isoformat() if conv.updated_at else None,
            "focus": {"object_id": conv.object_id, "type": "object", "conv_id": conv.conv_id},
        })

    # Sort by timestamp descending, deduplicate by focus key
    seen = set()
    unique: list[dict[str, Any]] = []
    for a in sorted(activities, key=lambda x: x.get("timestamp") or "", reverse=True):
        key = str(a.get("focus", {}))
        if key not in seen:
            seen.add(key)
            unique.append(a)
        if len(unique) >= limit:
            break

    return unique


# ---------------------------------------------------------------------------
# 5. Continue Working
# ---------------------------------------------------------------------------

def build_continue_working(identity_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """Surface what the founder was previously working on from persisted state."""
    spaces = FounderSpace.query.filter_by(
        identity_id=identity_id, status="active"
    ).all()
    space_ids = [s.space_id for s in spaces]

    items: list[dict[str, Any]] = []

    if not space_ids:
        return items

    # Most recently updated objects (active work)
    _ic10, _ip10 = _sql_in(space_ids)
    recent_objects = db.session.execute(
        _sql_text(f"SELECT * FROM sh_objects WHERE workspace_id {_ic10} AND status = 'active' AND is_deleted IS NOT true ORDER BY updated_at DESC LIMIT :lim"),
        {**_ip10, 'lim': limit},
    ).all()

    for obj in recent_objects:
        conv = FounderConversation.query.filter_by(
            object_id=obj.object_id, status="active"
        ).first()
        has_conversation = conv is not None
        items.append({
            "type": "object",
            "title": obj.name,
            "subtitle": obj.object_type,
            "meta": "Has active conversation" if has_conversation else None,
            "focus": {"object_id": obj.object_id, "type": "object", "conv_id": conv.conv_id if conv else None},
            "updated_at": str(obj.updated_at) if obj.updated_at else None,
        })

    # Active conversations (ongoing work)
    conversations = FounderConversation.query.filter(
        FounderConversation.identity_id == identity_id,
        FounderConversation.status == "active",
    ).order_by(FounderConversation.updated_at.desc()).limit(limit).all()

    for conv in conversations:
        # Skip if the object is already listed
        if any(i.get("focus", {}).get("object_id") == conv.object_id for i in items):
            continue
        msg_count = FounderMessage.query.filter_by(conv_id=conv.conv_id).count()
        items.append({
            "type": "conversation",
            "title": conv.title,
            "subtitle": f"{msg_count} message{'s' if msg_count != 1 else ''}",
            "meta": None,
            "focus": {"object_id": conv.object_id, "type": "object", "conv_id": conv.conv_id},
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        })

    return items[:limit]


# ---------------------------------------------------------------------------
# 6. Assemble Full Executive Home
# ---------------------------------------------------------------------------

def build_executive_home(identity_id: str) -> dict[str, Any]:
    """Assemble the complete Executive Home payload.

    Returns structured data for all seven required capabilities,
    including organization context.
    """
    # --- Organization context ---
    org_context = {}
    member = OrgMember.query.filter_by(identity_id=identity_id).first()
    if member:
        org = Organization.query.get(member.organization_id)
        if org:
            org_context = {
                "org_id": org.id,
                "org_name": org.name,
                "org_type": org.business_type,
                "org_tagline": org.brand_tagline,
                "org_description": org.brand_description,
                "org_logo": org.logo_url or "",
                "org_currency": org.currency,
            }

    return {
        "organization": org_context,
        "morning_brief": build_morning_brief(identity_id),
        "recommendations": build_recommendations(identity_id),
        "business_health": build_business_health(identity_id),
        "recent_activity": build_recent_activity(identity_id),
        "continue_working": build_continue_working(identity_id),
    }


__all__ = [
    "build_executive_home",
    "build_morning_brief",
    "build_recommendations",
    "build_business_health",
    "build_recent_activity",
    "build_continue_working",
]