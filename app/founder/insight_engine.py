"""Executive Insight Engine — derives understanding from runtime state.

Every insight answers: What happened? Why important? What evidence?
What should happen next? All from persistent data. No fabrications.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

from app import db
from app.founder.models import (
    BusinessRelationship,
    FounderConversation,
    FounderMessage,
)
from core.object_service import get_object_service
from sqlalchemy import text

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ago(**kw) -> datetime:
    return datetime.now(timezone.utc) - timedelta(**kw)


def _time_ago(dt: datetime | None) -> str:
    if not dt:
        return ""
    # Strip tzinfo if present for consistent comparison
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    diff = datetime.now(timezone.utc) - dt
    if diff < timedelta(minutes=1):
        return "just now"
    if diff < timedelta(hours=1):
        return f"{int(diff.total_seconds() // 60)}m ago"
    if diff < timedelta(days=1):
        return f"{int(diff.total_seconds() // 3600)}h ago"
    return f"{diff.days}d ago"


def _days_since(dt: datetime | None) -> float:
    if not dt:
        return float("inf")
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return max(0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400)


def _parse_dt(val: Any) -> datetime | None:
    """Convert isoformat string (from ObjectService) back to datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except (ValueError, TypeError):
            return None
    return None


def _insight_id(prefix: str, key: str) -> str:
    return f"ins_{prefix}_{key[:16]}"


# ---------------------------------------------------------------------------
# Priority scoring (deterministic, no randomness)
# ---------------------------------------------------------------------------

_URGENCY_WEIGHT = 0.35
_IMPACT_WEIGHT = 0.25
_RISK_WEIGHT = 0.25
_ATTENTION_WEIGHT = 0.15


def _priority_score(urgency_days: float, impact_count: int, is_risk: bool,
                    needs_attention: bool) -> tuple[float, str]:
    """Deterministic priority score [0, 1]. Higher = more urgent."""
    # Urgency: decays logarithmically from 1 (today) to 0 (30+ days)
    urgency = max(0, 1.0 - (urgency_days / 30))

    # Impact: 0 items = 0, 1 = 0.3, 3+ = 1.0
    impact = min(1.0, impact_count / 3)

    # Risk
    risk = 1.0 if is_risk else 0.0

    # Attention
    attention = 1.0 if needs_attention else 0.0

    score = (
        _URGENCY_WEIGHT * urgency
        + _IMPACT_WEIGHT * impact
        + _RISK_WEIGHT * risk
        + _ATTENTION_WEIGHT * attention
    )

    if score >= 0.7:
        label = "urgent"
    elif score >= 0.4:
        label = "high"
    elif score >= 0.2:
        label = "medium"
    else:
        label = "low"

    return round(score, 3), label


# ---------------------------------------------------------------------------
# Insight derivation rules
# ---------------------------------------------------------------------------

def _list_objects_in_spaces(space_ids: list[str],
                            organization_id: int = 0) -> list[dict]:
    """List all active sh_objects across the given workspace IDs."""
    results: list[dict] = []
    seen: set[str] = set()
    for ws_id in space_ids:
        objs = get_object_service().list_by_workspace(
            workspace_id=ws_id, organization_id=organization_id, status="active",
            limit=1000
        )
        for o in objs:
            oid = o.get("object_id")
            if oid and oid not in seen:
                seen.add(oid)
                results.append(o)
    return results


def _derive_stalled_objects(identity_id: str, space_ids: list[str],
                            organization_id: int = 0) -> list[dict[str, Any]]:
    """Objects not updated in 7+ days with active conversations = stalled."""
    insights = []
    threshold = _ago(days=7)
    for obj in _list_objects_in_spaces(space_ids, organization_id):
        updated_at = _parse_dt(obj.get("updated_at"))
        if updated_at and updated_at > threshold:
            continue
        conv = FounderConversation.query.filter_by(
            object_id=obj["object_id"], status="active"
        ).first()
        if not conv:
            continue
        msg_count = FounderMessage.query.filter_by(conv_id=conv.conv_id).count()
        if msg_count < 2:
            continue
        days_stalled = round(_days_since(updated_at))
        score, label = _priority_score(days_stalled, 1, False, True)
        insights.append({
            "id": _insight_id("stalled", obj["object_id"]),
            "type": "stalled_work",
            "title": f"Work stalled on {obj.get('name')}",
            "what": f"{obj.get('name')} has not been updated in {days_stalled} days and has an active conversation with no recent progress.",
            "why": "Stalled work blocks momentum. Objects with active conversations that go stale indicate unresolved decisions or forgotten priorities.",
            "evidence": {
                "object_id": obj["object_id"],
                "object_name": obj.get("name"),
                "object_type": obj.get("object_type"),
                "space_id": obj.get("space_id") or obj.get("workspace_id"),
                "conv_id": conv.conv_id,
                "message_count": msg_count,
                "days_since_update": days_stalled,
                "updated_at": obj.get("updated_at"),
            },
            "next_steps": [{"action": "open", "label": "Review and update", "target": f"/founder/object/{obj['object_id']}"}],
            "priority_score": score,
            "priority": label,
            "queue": "urgent" if label == "urgent" else "recommendation",
            "created_at": _now().isoformat(),
            "lifecycle": "active",
        })
    return insights


def _derive_unattended_conversations(identity_id: str, space_ids: list[str],
                                     organization_id: int = 0) -> list[dict[str, Any]]:
    """Conversations where human sent more messages than SHUNYA last responded."""
    insights = []
    for obj in _list_objects_in_spaces(space_ids, organization_id):
        conv = FounderConversation.query.filter_by(
            object_id=obj["object_id"], status="active"
        ).first()
        if not conv:
            continue
        human_msgs = FounderMessage.query.filter_by(
            conv_id=conv.conv_id, role="human"
        ).count()
        assistant_msgs = FounderMessage.query.filter_by(
            conv_id=conv.conv_id, role="assistant"
        ).count()
        if human_msgs <= assistant_msgs:
            continue
        if human_msgs < 2:
            continue
        last_msg = FounderMessage.query.filter_by(
            conv_id=conv.conv_id
        ).order_by(FounderMessage.created_at.desc()).first()
        days_waiting = round(_days_since(last_msg.created_at)) if last_msg else 0
        score, label = _priority_score(days_waiting, 1, False, True)
        insights.append({
            "id": _insight_id("unattend", conv.conv_id),
            "type": "unattended_conversation",
            "title": f"Awaiting response on {obj.get('name')}",
            "what": f"You asked {human_msgs} question{'s' if human_msgs > 1 else ''} about {obj.get('name')}, but the last response was {days_waiting}d ago. SHUNYA is waiting for your next instruction.",
            "why": "Unanswered questions leave decisions open. Following up resolves ambiguity and moves work forward.",
            "evidence": {
                "object_id": obj["object_id"],
                "object_name": obj.get("name"),
                "conv_id": conv.conv_id,
                "human_messages": human_msgs,
                "assistant_messages": assistant_msgs,
                "days_since_last_message": days_waiting,
            },
            "next_steps": [{"action": "open", "label": "Continue conversation", "target": f"/founder/object/{obj['object_id']}"}],
            "priority_score": score,
            "priority": label,
            "queue": "recommendation" if label in ("medium", "high") else "information",
            "created_at": _now().isoformat(),
            "lifecycle": "active",
        })
    return insights


def _derive_inactive_spaces(identity_id: str, space_ids: list[str],
                            organization_id: int = 0) -> list[dict[str, Any]]:
    """Spaces with no object updates in 14+ days."""
    insights = []
    threshold = _ago(days=14)
    for ws_id in space_ids:
        row = db.session.execute(
            text("SELECT id, name, workspace_type, status, created_at FROM sh_workspaces WHERE id = :ws_id AND status = 'active'"),
            {"ws_id": ws_id},
        ).first()
        if not row:
            continue
        # Get latest active object in this workspace
        latest_objs = get_object_service().list_by_workspace(
            workspace_id=ws_id, organization_id=organization_id, status="active",
            limit=1
        )
        latest_obj = latest_objs[0] if latest_objs else None
        latest_updated_at = _parse_dt(latest_obj.get("updated_at")) if latest_obj else None

        if latest_obj and latest_updated_at and latest_updated_at > threshold:
            continue

        obj_count = len(get_object_service().list_by_workspace(
            workspace_id=ws_id, organization_id=organization_id, status="active",
            limit=1000
        ))

        if obj_count == 0:
            created_at = _parse_dt(row.created_at)
            days_idle = round(_days_since(created_at))
        else:
            days_idle = round(_days_since(latest_updated_at)) if latest_updated_at else 999

        score, label = _priority_score(days_idle, obj_count, False, False)
        insights.append({
            "id": _insight_id("inactive", ws_id),
            "type": "inactive_space",
            "title": f"Space '{row.name}' is inactive",
            "what": f"The '{row.name}' space has had no activity in {days_idle} days with {obj_count} object{'s' if obj_count != 1 else ''}.",
            "why": "Inactive spaces can signal abandoned initiatives. Reviewing them helps decide whether to refocus or archive.",
            "evidence": {
                "space_id": ws_id,
                "space_name": row.name,
                "space_type": row.workspace_type,
                "object_count": obj_count,
                "days_since_activity": days_idle,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            },
            "next_steps": [{"action": "open", "label": "Review space", "target": f"/founder/space/{ws_id}"}],
            "priority_score": score,
            "priority": label,
            "queue": "information" if label == "low" else "recommendation",
            "created_at": _now().isoformat(),
            "lifecycle": "active",
        })
    return insights


def _derive_object_type_insights(identity_id: str, space_ids: list[str],
                                 organization_id: int = 0) -> list[dict[str, Any]]:
    """Insights about object type diversity."""
    insights = []
    all_objs = _list_objects_in_spaces(space_ids, organization_id)
    type_counts: dict[str, int] = {}
    for o in all_objs:
        t = o.get("object_type") or "unknown"
        type_counts[t] = type_counts.get(t, 0) + 1
    total = sum(type_counts.values())
    if total < 3:
        return insights

    if len(type_counts) == 1:
        single_type = list(type_counts.keys())[0]
        score, label = _priority_score(0, total, True, False)
        insights.append({
            "id": "ins_type_single_type",
            "type": "low_diversity",
            "title": f"All {total} object{'s' if total != 1 else ''} are '{single_type}' type",
            "what": f"Every object across your spaces is a '{single_type}'. Different object types would help SHUNYA understand different facets of your business.",
            "why": "A business has documents, spreadsheets, designs, leads, projects — each type enriches SHUNYA's understanding of your context.",
            "evidence": {
                "type_counts": type_counts,
                "total_objects": total,
                "dominant_type": single_type,
            },
            "next_steps": [{"action": "navigate", "label": "Create different object type", "target": "/founder/space/create"}],
            "priority_score": score,
            "priority": label,
            "queue": "information",
            "created_at": _now().isoformat(),
            "lifecycle": "active",
        })

    return insights


def _derive_relationship_insights(identity_id: str, space_ids: list[str]) -> list[dict[str, Any]]:
    """Insights from relationship data."""
    from sqlalchemy import func
    insights = []

    if not space_ids:
        return insights

    rel_counts = dict(
        db.session.query(
            BusinessRelationship.rel_type, func.count(BusinessRelationship.id)
        ).filter(
            BusinessRelationship.space_id.in_(space_ids),
            BusinessRelationship.status == "active",
        ).group_by(BusinessRelationship.rel_type).all()
    )

    if "customer" not in rel_counts and sum(rel_counts.values()) > 0:
        # Has some relationships but no customers
        total_rels = sum(rel_counts.values())
        score, label = _priority_score(0, total_rels, True, False)
        insights.append({
            "id": "ins_rel_no_customers",
            "type": "missing_type",
            "title": "No customer relationships tracked",
            "what": f"You have {total_rels} relationship{'s' if total_rels != 1 else ''} but none are customers. Customers are the primary relationship that drives business understanding.",
            "why": "Without customer relationships, SHUNYA cannot track commitments, pipeline, or account health — core business intelligence.",
            "evidence": {
                "relationship_counts": rel_counts,
                "total_relationships": total_rels,
            },
            "next_steps": [{"action": "navigate", "label": "Add a customer", "target": "/founder/relationships/create"}],
            "priority_score": score,
            "priority": label,
            "queue": "recommendation",
            "created_at": _now().isoformat(),
            "lifecycle": "active",
        })

    # Check relationships with extended notes (signal of engagement)
    rels_with_notes = BusinessRelationship.query.filter(
        BusinessRelationship.space_id.in_(space_ids),
        BusinessRelationship.status == "active",
        BusinessRelationship.notes != "",
        BusinessRelationship.notes != None,  # noqa: E711
    ).count()
    total_rels = sum(rel_counts.values())
    if total_rels > 0 and rels_with_notes == 0:
        score, label = _priority_score(0, total_rels, False, False)
        insights.append({
            "id": "ins_rel_no_notes",
            "type": "missing_detail",
            "title": "Add context to your relationships",
            "what": f"None of your {total_rels} relationship{'s' if total_rels != 1 else ''} have notes. Adding context helps SHUNYA track commitments and history.",
            "why": "Relationship notes are where business context lives — past conversations, agreements, next steps.",
            "evidence": {
                "total_relationships": total_rels,
                "with_notes": rels_with_notes,
            },
            "next_steps": [{"action": "navigate", "label": "Browse relationships", "target": "/founder/home"}],
            "priority_score": score,
            "priority": label,
            "queue": "information",
            "created_at": _now().isoformat(),
            "lifecycle": "active",
        })

    return insights


def _derive_recent_completions(identity_id: str, space_ids: list[str],
                               organization_id: int = 0) -> list[dict[str, Any]]:
    """Objects created recently — fresh work to build on."""
    insights = []
    threshold = _ago(hours=48)
    count = 0
    for obj in _list_objects_in_spaces(space_ids, organization_id):
        if count >= 5:
            break
        created_at = _parse_dt(obj.get("created_at"))
        if not created_at or created_at < threshold:
            continue
        conv = FounderConversation.query.filter_by(
            object_id=obj["object_id"], status="active"
        ).first()
        score, label = _priority_score(0, 1, False, False)
        insights.append({
            "id": _insight_id("new", obj["object_id"]),
            "type": "recent_completion",
            "title": f"New object: {obj.get('name')}",
            "what": f"A new {obj.get('object_type', '').lower()} '{obj.get('name')}' was created {_time_ago(created_at)}.",
            "why": "New objects represent fresh business activity. Exploring them early builds SHUNYA's understanding of what matters.",
            "evidence": {
                "object_id": obj["object_id"],
                "object_name": obj.get("name"),
                "object_type": obj.get("object_type"),
                "space_id": obj.get("space_id") or obj.get("workspace_id"),
                "created_at": obj.get("created_at"),
                "has_conversation": conv is not None,
            },
            "next_steps": [{"action": "open", "label": "Explore", "target": f"/founder/object/{obj['object_id']}"}],
            "priority_score": score,
            "priority": label,
            "queue": "information",
            "created_at": _now().isoformat(),
            "lifecycle": "active",
        })
        count += 1
    return insights


def _derive_orphan_objects(identity_id: str, space_ids: list[str],
                           organization_id: int = 0) -> Iterator[dict[str, Any]]:
    """Objects with no conversations and not recently updated."""
    threshold = _ago(days=3)
    creation_threshold = _ago(days=3)
    for obj in _list_objects_in_spaces(space_ids, organization_id):
        updated_at = _parse_dt(obj.get("updated_at"))
        if updated_at and updated_at > threshold:
            continue
        conv = FounderConversation.query.filter_by(
            object_id=obj["object_id"], status="active"
        ).first()
        if conv:
            continue
        created_at = _parse_dt(obj.get("created_at"))
        # Only for objects that have existed > 3 days
        if created_at and created_at > creation_threshold:
            continue
        days_since = round(_days_since(updated_at))
        score, label = _priority_score(days_since, 1, False, False)
        yield {
            "id": _insight_id("orphan", obj["object_id"]),
            "type": "orphan_object",
            "title": f"{obj.get('name')} has never been discussed",
            "what": f"'{obj.get('name')}' was created {_time_ago(created_at)} but has never had a conversation. SHUNYA doesn't know what's important about it.",
            "why": "Objects without conversations are invisible to SHUNYA's understanding. A brief discussion establishes context and intent.",
            "evidence": {
                "object_id": obj["object_id"],
                "object_name": obj.get("name"),
                "object_type": obj.get("object_type"),
                "space_id": obj.get("space_id") or obj.get("workspace_id"),
                "created_at": obj.get("created_at"),
            },
            "next_steps": [{"action": "open", "label": "Start conversation", "target": f"/founder/object/{obj['object_id']}"}],
            "priority_score": score,
            "priority": label,
            "queue": "information",
            "created_at": _now().isoformat(),
            "lifecycle": "active",
        }


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def _collect_insights(identity_id: str, space_ids: list[str],
                      organization_id: int = 0) -> list[dict[str, Any]]:
    """Run all insight derivation rules in priority order."""
    insights: list[dict[str, Any]] = []
    if not space_ids:
        return insights

    rules = [
        _derive_stalled_objects,
        _derive_unattended_conversations,
        _derive_inactive_spaces,
        _derive_object_type_insights,
        _derive_relationship_insights,
        _derive_recent_completions,
        _derive_orphan_objects,
    ]

    for rule in rules:
        try:
            result = rule(identity_id, space_ids, organization_id)
            if isinstance(result, list):
                insights.extend(result)
            elif hasattr(result, "__iter__"):
                insights.extend(result)
        except Exception:
            pass

    return insights


# ---------------------------------------------------------------------------
# Executive Timeline
# ---------------------------------------------------------------------------

def build_timeline(identity_id: str, limit: int = 20,
                   organization_id: int = 0) -> list[dict[str, Any]]:
    """Chronological timeline of business events from persistent state."""
    ws_rows = db.session.execute(
        text("SELECT id, name, workspace_type, created_at FROM sh_workspaces WHERE status = 'active'"),
    ).all()
    space_ids = [r.id for r in ws_rows]
    ws_by_id = {r.id: r for r in ws_rows}
    events: list[dict[str, Any]] = []

    if not space_ids:
        return events

    # Space creation events
    for s in ws_rows:
        events.append({
            "type": "space_created",
            "title": f"Space '{s.name}' created",
            "detail": f"{s.workspace_type} space",
            "timestamp": s.created_at.isoformat() if s.created_at else None,
            "focus": {"space_id": s.id, "type": "space"},
        })

    # Object creation events — collect across all spaces
    for obj in _list_objects_in_spaces(space_ids, organization_id)[:limit]:
        events.append({
            "type": "object_created",
            "title": f"'{obj.get('name')}' created",
            "detail": f"{obj.get('object_type')}",
            "timestamp": obj.get("created_at"),
            "focus": {"object_id": obj["object_id"], "type": "object"},
        })

    # Conversation events
    for conv in FounderConversation.query.filter(
        FounderConversation.identity_id == identity_id,
        FounderConversation.status == "active",
    ).order_by(FounderConversation.updated_at.desc()).limit(limit).all():
        msg_count = FounderMessage.query.filter_by(conv_id=conv.conv_id).count()
        events.append({
            "type": "conversation",
            "title": f"Discussion on '{conv.title}'",
            "detail": f"{msg_count} message{'s' if msg_count != 1 else ''}",
            "timestamp": conv.updated_at.isoformat() if conv.updated_at else None,
            "focus": {"object_id": conv.object_id, "type": "object", "conv_id": conv.conv_id},
        })

    # Sort descending by timestamp, dedup by focus
    seen = set()
    unique = []
    for e in sorted(events, key=lambda x: x.get("timestamp") or "", reverse=True):
        key = str(e.get("focus", {}))
        if key not in seen:
            seen.add(key)
            unique.append(e)
        if len(unique) >= limit:
            break
    return unique


# ---------------------------------------------------------------------------
# Attention Queue
# ---------------------------------------------------------------------------

def build_attention_queue(insights: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Separate insights into: urgent, recommendations, information."""
    urgent: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []
    information: list[dict[str, Any]] = []

    for ins in insights:
        q = ins.get("queue", "information")
        if q == "urgent":
            urgent.append(ins)
        elif q == "recommendation":
            recommendations.append(ins)
        else:
            information.append(ins)

    # Sort each by priority_score descending
    urgent.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
    recommendations.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
    information.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

    return {
        "urgent": urgent,
        "recommendations": recommendations,
        "information": information,
    }


# ---------------------------------------------------------------------------
# Full insight assembly
# ---------------------------------------------------------------------------

def build_insights(identity_id: str, organization_id: int = 0) -> dict[str, Any]:
    """Build complete insight payload for Executive Intelligence."""
    ws_rows = db.session.execute(
        text("SELECT id, name, workspace_type, status FROM sh_workspaces WHERE status = 'active'"),
    ).all()
    space_ids = [r.id for r in ws_rows]

    insights = _collect_insights(identity_id, space_ids, organization_id)
    queue = build_attention_queue(insights)
    timeline = build_timeline(identity_id, organization_id=organization_id)

    return {
        "insights": insights,
        "attention_queue": queue,
        "timeline": timeline,
        "summary": {
            "total_insights": len(insights),
            "urgent_count": len(queue["urgent"]),
            "recommendation_count": len(queue["recommendations"]),
            "information_count": len(queue["information"]),
            "timeline_events": len(timeline),
        },
    }


# ---------------------------------------------------------------------------
# Insight lifecycle
# ---------------------------------------------------------------------------

INSIGHT_LIFECYCLES: dict[str, str] = {}  # insight_id -> state (in-memory, ephemeral per session)


def acknowledge_insight(insight_id: str) -> str:
    """Mark an insight as acknowledged by the founder."""
    INSIGHT_LIFECYCLES[insight_id] = "acknowledged"
    return "acknowledged"


def resolve_insight(insight_id: str) -> str:
    """Mark an insight as resolved (founder took action)."""
    INSIGHT_LIFECYCLES[insight_id] = "resolved"
    return "resolved"


def dismiss_insight(insight_id: str) -> str:
    """Dismiss an insight."""
    INSIGHT_LIFECYCLES[insight_id] = "dismissed"
    return "dismissed"


def get_insight_lifecycle(insight_id: str) -> str:
    """Get an insight's current lifecycle state."""
    return INSIGHT_LIFECYCLES.get(insight_id, "active")


# ---------------------------------------------------------------------------
# Integrate into Executive Home
# ---------------------------------------------------------------------------

def build_executive_intelligence(identity_id: str, organization_id: int = 0) -> dict[str, Any]:
    """Assemble the Executive Intelligence section for Executive Home."""
    return build_insights(identity_id, organization_id)


__all__ = [
    "build_executive_intelligence",
    "build_insights",
    "build_timeline",
    "build_attention_queue",
    "acknowledge_insight",
    "resolve_insight",
    "dismiss_insight",
    "get_insight_lifecycle",
]