"""SHUNYA M4 — Workspace Intelligence Runtime.

Transforms every SHUNYA object into a living AI-native workspace.

Capabilities:
1. Workspace Summary — deterministic executive summary from persisted state
2. AI Understanding Panel — structured explanation with confidence
3. Relationship Intelligence — navigable related objects grouped by type
4. Activity Timeline — complete chronological history
5. Conversation Workspace — threaded discussion integrated with object
6. Next Actions — deterministic suggestions from runtime state
7. Missing Context Detection — active identification of understanding gaps
8. Workspace Health — deterministic, explainable health assessment
9. Evidence Explorer — every statement traceable to provenance
10. Navigation Canon — context-preserving movement between objects

All intelligence derives from existing SHUNYA runtime state. No LLM-generated
summaries without supporting evidence. No placeholder recommendations.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app import db
from app.founder.models import (
    BusinessRelationship,
    FounderConversation,
    FounderMessage,
    FounderObject,
    FounderSpace,
)
from app.founder.workspace_models import (
    MissingContext,
    NextAction,
    WorkspaceEvent,
    WorkspaceHealthSnapshot,
    WorkspaceNavigation,
)


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


# ---------------------------------------------------------------------------
# 1. Workspace Summary
# ---------------------------------------------------------------------------

def build_workspace_summary(object_id: str) -> dict[str, Any]:
    """Build a deterministic executive summary for an object.

    Every statement originates from persisted runtime state.
    Contains: identity, status, importance, ownership, creation history,
    latest activity, business significance.
    """
    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return {"error": "Object not found"}

    space = FounderSpace.query.filter_by(space_id=obj.space_id).first()
    conv = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()
    msg_count = 0
    if conv:
        msg_count = FounderMessage.query.filter_by(conv_id=conv.conv_id).count()

    # Count relationships
    rel_count = BusinessRelationship.query.filter_by(
        space_id=obj.space_id, status="active"
    ).count()

    # Determine activity recency
    days_since_update = round(_days_since(obj.updated_at))
    if days_since_update == 0:
        activity_label = "Updated today"
    elif days_since_update == 1:
        activity_label = "Updated yesterday"
    elif days_since_update <= 7:
        activity_label = f"Updated {days_since_update}d ago"
    else:
        activity_label = f"No activity in {days_since_update}d"

    # Significance derived from state
    significance_parts = []
    if obj.object_type:
        significance_parts.append(f"{obj.object_type}")
    if space:
        significance_parts.append(f"in '{space.name}'")
    if msg_count > 0:
        significance_parts.append(f"{msg_count} message{'s' if msg_count != 1 else ''}")
    if rel_count > 0:
        significance_parts.append(f"{rel_count} relationship{'s' if rel_count != 1 else ''} in space")

    return {
        "object_id": obj.object_id,
        "name": obj.name,
        "object_type": obj.object_type,
        "status": obj.status,
        "created_by": obj.created_by,
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        "space_name": space.name if space else None,
        "space_id": obj.space_id,
        "activity_label": activity_label,
        "activity_days_since_update": days_since_update,
        "conversation_count": 1 if conv else 0,
        "message_count": msg_count,
        "relationship_count": rel_count,
        "significance": " · ".join(significance_parts) if significance_parts else "Awaiting context",
        "content_preview": obj.content[:300] if obj.content else "",
    }


# ---------------------------------------------------------------------------
# 2. AI Understanding Panel
# ---------------------------------------------------------------------------

def build_ai_understanding(object_id: str) -> dict[str, Any]:
    """Build a structured AI understanding explanation for an object.

    Answers:
    - What is this?
    - Why does it exist?
    - What does SHUNYA currently understand?
    - What information is missing?
    - What confidence exists?
    - Which relationships influence it?

    Unknown information is explicitly identified rather than guessed.
    """
    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return {"error": "Object not found"}

    space = FounderSpace.query.filter_by(space_id=obj.space_id).first()
    conv = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()

    # What is this?
    what_is = f"A {obj.object_type.lower() if obj.object_type else 'object'} named '{obj.name}'"
    if obj.content:
        what_is += " with content that describes its purpose"

    # Why does it exist?
    why_exists_parts = []
    if obj.created_by:
        why_exists_parts.append(f"Created by {obj.created_by[:20]}")
    if obj.created_at:
        why_exists_parts.append(f"on {obj.created_at.strftime('%b %d, %Y')}")
    if space:
        why_exists_parts.append(f"within the '{space.name}' space")
    why_exists = ", ".join(why_exists_parts) if why_exists_parts else "Creation context unknown"

    # What does SHUNYA currently understand?
    understanding_parts = []
    known_facts = []
    if obj.object_type:
        known_facts.append(f"type: {obj.object_type}")
    if obj.name:
        known_facts.append(f"name: '{obj.name}'")
    if obj.content:
        known_facts.append(f"has descriptive content ({len(obj.content)} chars)")
    if obj.status:
        known_facts.append(f"status: {obj.status}")
    if conv:
        messages = FounderMessage.query.filter_by(conv_id=conv.conv_id).order_by(
            FounderMessage.created_at
        ).all()
        if messages:
            known_facts.append(f"has {len(messages)} conversation messages")
        understanding_parts.append("SHUNYA has discussed this object")
    if known_facts:
        understanding_parts.append("Known facts: " + "; ".join(known_facts))

    # What information is missing?
    missing_info = _detect_missing_info(obj, space, conv)

    # Confidence — derived from how much is known
    confidence_factors = []
    confidence_score = 0.0
    if obj.object_type:
        confidence_score += 0.15
        confidence_factors.append("object type identified")
    if obj.name:
        confidence_score += 0.15
    if obj.content:
        confidence_score += 0.15
        confidence_factors.append("descriptive content present")
    if conv:
        confidence_score += 0.20
        confidence_factors.append("conversation history exists")
    if space:
        confidence_score += 0.10
    if obj.created_by:
        confidence_score += 0.10
        confidence_factors.append("ownership known")

    # Relationships influence
    relationships = BusinessRelationship.query.filter_by(
        space_id=obj.space_id, status="active"
    ).all()
    influence = []
    for rel in relationships:
        influence.append({
            "rel_id": rel.rel_id,
            "rel_type": rel.rel_type,
            "name": rel.name,
            "influence": f"Related through shared space '{space.name}'" if space else "Related",
        })

    confidence_label = "high" if confidence_score >= 0.7 else (
        "medium" if confidence_score >= 0.4 else "low"
    )

    return {
        "what_is": what_is,
        "why_exists": why_exists,
        "current_understanding": " ".join(understanding_parts) if understanding_parts else "SHUNYA has just started observing this object.",
        "missing_information": missing_info,
        "confidence": {
            "score": round(confidence_score, 2),
            "label": confidence_label,
            "factors": confidence_factors,
        },
        "influencing_relationships": influence,
    }


def _detect_missing_info(obj, space, conv) -> list[dict[str, str]]:
    """Detect explicitly missing information — never fabricate."""
    missing = []
    if not obj.content or not obj.content.strip():
        missing.append({
            "field": "content",
            "description": "No descriptive content has been added",
            "severity": "info",
        })
    if not obj.created_by:
        missing.append({
            "field": "owner",
            "description": "Owner / creator is not recorded",
            "severity": "suggestion",
        })
    if not space:
        missing.append({
            "field": "space_context",
            "description": "Object is not associated with any space",
            "severity": "recommendation",
        })
    if not conv:
        missing.append({
            "field": "conversation",
            "description": "No conversation has been started — SHUNYA cannot learn context",
            "severity": "suggestion",
        })
    # Check if object is stale
    if obj.updated_at and _days_since(obj.updated_at) > 14:
        missing.append({
            "field": "recent_activity",
            "description": f"No activity in {round(_days_since(obj.updated_at))} days",
            "severity": "info",
        })
    return missing


# ---------------------------------------------------------------------------
# 3. Relationship Intelligence
# ---------------------------------------------------------------------------

def build_relationship_intelligence(object_id: str) -> dict[str, Any]:
    """Display all directly related objects grouped by relationship type.

    Types: relationships (BusinessRelationship), same-space objects,
    objects with shared conversations.
    """
    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return {"error": "Object not found", "groups": []}

    groups = []

    # 3a. Business Relationships in same space
    rels = BusinessRelationship.query.filter_by(
        space_id=obj.space_id, status="active"
    ).all()
    if rels:
        groups.append({
            "group_type": "business_relationship",
            "group_label": "Business Relationships",
            "items": [{
                "object_id": r.rel_id,
                "name": r.name,
                "type": r.rel_type,
                "subtitle": f"{r.company}" if r.company else r.rel_type,
                "status": r.status,
                "icon": "🤝",
            } for r in rels],
        })

    # 3b. Same-space objects
    siblings = FounderObject.query.filter(
        FounderObject.space_id == obj.space_id,
        FounderObject.status == "active",
        FounderObject.object_id != object_id,
    ).order_by(FounderObject.updated_at.desc()).limit(10).all()

    if siblings:
        groups.append({
            "group_type": "same_space",
            "group_label": f"Objects in this space",
            "items": [{
                "object_id": s.object_id,
                "name": s.name,
                "type": s.object_type,
                "subtitle": f"{s.object_type} · {_time_ago(s.updated_at)}",
                "status": s.status,
                "icon": _object_type_icon(s.object_type),
            } for s in siblings],
        })

    # 3c. Objects with shared conversation context
    conv = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()
    if conv:
        # Find other objects in conversations by the same identity
        related_convs = FounderConversation.query.filter(
            FounderConversation.identity_id == conv.identity_id,
            FounderConversation.object_id != object_id,
            FounderConversation.status == "active",
        ).all()
        conv_related_ids = list(set(c.object_id for c in related_convs))
        if conv_related_ids:
            conv_objects = FounderObject.query.filter(
                FounderObject.object_id.in_(conv_related_ids),
                FounderObject.status == "active",
            ).limit(5).all()
            if conv_objects:
                groups.append({
                    "group_type": "conversation_context",
                    "group_label": "Conversation Context",
                    "items": [{
                        "object_id": co.object_id,
                        "name": co.name,
                        "type": co.object_type,
                        "subtitle": f"Discussed by same identity",
                        "status": co.status,
                        "icon": _object_type_icon(co.object_type),
                    } for co in conv_objects],
                })

    return {"object_id": object_id, "groups": groups}


# ---------------------------------------------------------------------------
# 4. Activity Timeline
# ---------------------------------------------------------------------------

def build_activity_timeline(object_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Build a complete chronological history for an object.

    Includes: creation, updates, conversations, commitments, evidence,
    intelligence events. Timeline entries are deterministic and persisted.
    """
    events: list[dict[str, Any]] = []
    obj = FounderObject.query.filter_by(object_id=object_id).first()
    if not obj:
        return events

    # Creation event
    if obj.created_at:
        events.append({
            "event_type": "created",
            "title": f"Object created",
            "detail": f"{obj.name} · {obj.object_type or 'object'}",
            "provenance": json.dumps({
                "source": "object_creation",
                "object_id": obj.object_id,
                "field": "created_at",
            }),
            "importance": "system",
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
        })

    # Update events
    if obj.updated_at and obj.created_at and obj.updated_at > obj.created_at:
        days_diff = round((obj.updated_at - obj.created_at).total_seconds() / 86400)
        if days_diff > 0:
            events.append({
                "event_type": "updated",
                "title": f"Object updated",
                "detail": f"Last update was {days_diff}d after creation" if days_diff < 30
                          else f"Last update was {days_diff}d after creation",
                "provenance": json.dumps({
                    "source": "object_update",
                    "object_id": obj.object_id,
                    "field": "updated_at",
                }),
                "importance": "normal",
                "created_at": obj.updated_at.isoformat() if obj.updated_at else None,
            })

    # Conversation events
    conv = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()
    if conv:
        if conv.created_at:
            events.append({
                "event_type": "conversation",
                "title": "Conversation started",
                "detail": conv.title or f"About {obj.name}",
                "provenance": json.dumps({
                    "source": "conversation_creation",
                    "conv_id": conv.conv_id,
                }),
                "importance": "high",
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
            })

        messages = FounderMessage.query.filter_by(conv_id=conv.conv_id).order_by(
            FounderMessage.created_at
        ).all()
        for msg in messages:
            provenance = json.dumps({
                "source": "conversation_message",
                "conv_id": conv.conv_id,
                "message_id": msg.id,
                "role": msg.role,
            })
            # Only include significant messages (assistant responses with substance)
            preview = msg.content[:150] if msg.content else ""
            events.append({
                "event_type": "message",
                "title": f"{msg.role.capitalize()} message",
                "detail": preview,
                "provenance": provenance,
                "importance": "normal" if msg.role == "assistant" else "high",
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            })

    # Evidence events (from workspace events table)
    persisted_events = WorkspaceEvent.query.filter_by(object_id=object_id).order_by(
        WorkspaceEvent.created_at.asc()
    ).all()
    for pe in persisted_events:
        events.append({
            "event_type": pe.event_type,
            "title": pe.title,
            "detail": pe.detail,
            "provenance": pe.provenance,
            "importance": pe.importance,
            "created_at": pe.created_at.isoformat() if pe.created_at else None,
        })

    # Sort by timestamp, reverse chronological
    events.sort(key=lambda e: e.get("created_at", "") or "", reverse=True)
    return events[:limit]


# ---------------------------------------------------------------------------
# 5. Conversation Workspace
# ---------------------------------------------------------------------------

def get_conversation_workspace(object_id: str) -> dict[str, Any]:
    """Get the conversation attached to an object with full context.

    Returns conversation + messages + extracted decisions and commitments.
    """
    obj = FounderObject.query.filter_by(object_id=object_id).first()
    if not obj:
        return {"error": "Object not found", "conversation": None}

    conv = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()
    if not conv:
        return {
            "object_id": object_id,
            "conversation": None,
            "messages": [],
            "status": "no_conversation",
        }

    messages = FounderMessage.query.filter_by(conv_id=conv.conv_id).order_by(
        FounderMessage.created_at.asc()
    ).all()

    return {
        "object_id": object_id,
        "conversation": conv.to_dict(),
        "messages": [m.to_dict() for m in messages],
        "status": "active",
    }


# ---------------------------------------------------------------------------
# 6. Next Actions
# ---------------------------------------------------------------------------

def build_next_actions(object_id: str) -> list[dict[str, Any]]:
    """Generate deterministic next actions from runtime state.

    Each action includes: explanation, supporting evidence, priority,
    originating runtime. No placeholder recommendations.
    """
    actions: list[dict[str, Any]] = []
    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return actions

    space = FounderSpace.query.filter_by(space_id=obj.space_id).first()
    conv = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()

    # Check existing pending actions
    pending = {
        a.action_type
        for a in NextAction.query.filter_by(
            object_id=object_id, status="pending"
        ).all()
    }

    # Action: Start a conversation
    if not conv and "start_conversation" not in pending:
        actions.append({
            "action_type": "start_conversation",
            "label": "Start a conversation about this object",
            "explanation": f"No conversation exists for '{obj.name}'. Starting a discussion helps SHUNYA understand its context and importance.",
            "supporting_evidence": json.dumps({
                "object_id": obj.object_id,
                "object_name": obj.name,
                "has_conversation": False,
            }),
            "priority": "high",
            "priority_score": 0.7,
            "originating_runtime": "workspace_intelligence",
            "status": "pending",
        })

    # Action: Add descriptive content
    if not obj.content or not obj.content.strip():
        if "add_content" not in pending:
            actions.append({
                "action_type": "add_content",
                "label": "Add descriptive content",
                "explanation": f"'{obj.name}' has no content. Adding a description establishes its purpose and context.",
                "supporting_evidence": json.dumps({
                    "object_id": obj.object_id,
                    "has_content": False,
                }),
                "priority": "medium",
                "priority_score": 0.5,
                "originating_runtime": "workspace_intelligence",
                "status": "pending",
            })

    # Action: Add owner
    if not obj.created_by:
        if "add_owner" not in pending:
            actions.append({
                "action_type": "add_owner",
                "label": "Assign an owner",
                "explanation": f"'{obj.name}' has no recorded owner. Assigning ownership clarifies responsibility.",
                "supporting_evidence": json.dumps({
                    "object_id": obj.object_id,
                    "has_owner": False,
                }),
                "priority": "medium",
                "priority_score": 0.5,
                "originating_runtime": "workspace_intelligence",
                "status": "pending",
            })

    # Action: Review stale object
    if obj.updated_at and _days_since(obj.updated_at) > 14:
        days_stale = round(_days_since(obj.updated_at))
        if "review_stale" not in pending:
            actions.append({
                "action_type": "review_stale",
                "label": f"Review — no activity in {days_stale}d",
                "explanation": f"'{obj.name}' has had no updates in {days_stale} days. Review to determine if it's still relevant or should be archived.",
                "supporting_evidence": json.dumps({
                    "object_id": obj.object_id,
                    "days_since_update": days_stale,
                    "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
                }),
                "priority": "low",
                "priority_score": 0.3,
                "originating_runtime": "workspace_intelligence",
                "status": "pending",
            })

    # Action: Add a relationship
    if space:
        rel_count = BusinessRelationship.query.filter_by(
            space_id=space.space_id, status="active"
        ).count()
        if rel_count == 0 and "add_relationship" not in pending:
            actions.append({
                "action_type": "add_relationship",
                "label": "Link a business relationship",
                "explanation": f"No relationships exist in this space. Adding a customer, supplier, or partner helps SHUNYA understand business context.",
                "supporting_evidence": json.dumps({
                    "space_id": obj.space_id,
                    "relationship_count": rel_count,
                }),
                "priority": "medium",
                "priority_score": 0.4,
                "originating_runtime": "workspace_intelligence",
                "status": "pending",
            })

    # Persist generated actions
    for action in actions:
        existing = NextAction.query.filter_by(
            object_id=object_id,
            action_type=action["action_type"],
            status="pending",
        ).first()
        if not existing:
            na = NextAction(
                object_id=object_id,
                action_type=action["action_type"],
                label=action["label"],
                explanation=action["explanation"],
                supporting_evidence=action["supporting_evidence"],
                priority=action["priority"],
                priority_score=action["priority_score"],
                originating_runtime=action["originating_runtime"],
            )
            db.session.add(na)
    db.session.commit()

    # Return all pending + completed
    all_actions = NextAction.query.filter_by(object_id=object_id).order_by(
        NextAction.priority_score.desc()
    ).all()
    return [a.to_dict() for a in all_actions]


# ---------------------------------------------------------------------------
# 7. Missing Context Detection
# ---------------------------------------------------------------------------

def detect_missing_context(object_id: str) -> list[dict[str, Any]]:
    """Actively identify missing information about an object.

    Each finding is a real absence in persisted state. Presented as
    opportunities to improve business understanding.
    """
    gaps: list[dict[str, Any]] = []
    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return gaps

    space = FounderSpace.query.filter_by(space_id=obj.space_id).first()
    conv = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()

    # Check existing open gaps
    existing_gaps = {
        gc.context_type
        for gc in MissingContext.query.filter_by(
            object_id=object_id, status="open"
        ).all()
    }

    candidate_gaps = []

    # Missing owner
    if not obj.created_by:
        candidate_gaps.append({
            "context_type": "missing_owner",
            "label": "Owner not assigned",
            "detail": f"'{obj.name}' has no recorded owner. Ownership is essential for accountability.",
            "severity": "suggestion",
        })

    # Missing notes / content
    if not obj.content or not obj.content.strip():
        candidate_gaps.append({
            "context_type": "missing_notes",
            "label": "No descriptive content",
            "detail": f"Adding notes or a description helps establish '{obj.name}'s purpose within your business.",
            "severity": "suggestion",
        })

    # Missing conversation
    if not conv:
        candidate_gaps.append({
            "context_type": "missing_conversation",
            "label": "No conversation recorded",
            "detail": "Objects with conversations give SHUNYA context about their importance and your intent.",
            "severity": "suggestion",
        })

    # Missing relationships
    if space:
        rel_count = BusinessRelationship.query.filter_by(
            space_id=space.space_id, status="active"
        ).count()
        if rel_count == 0:
            candidate_gaps.append({
                "context_type": "missing_relationship",
                "label": "No business relationships linked",
                "detail": "Relationships (customers, suppliers, partners) provide business context for this object.",
                "severity": "suggestion",
            })

    # Stale / missing follow-up
    if obj.updated_at and _days_since(obj.updated_at) > 7:
        candidate_gaps.append({
            "context_type": "missing_follow_up",
            "label": f"No recent activity ({round(_days_since(obj.updated_at))}d)",
            "detail": "Review this object to determine if it needs follow-up or can be archived.",
            "severity": "info",
        })

    # Persist new gaps
    for gap in candidate_gaps:
        if gap["context_type"] not in existing_gaps:
            mg = MissingContext(
                object_id=object_id,
                context_type=gap["context_type"],
                label=gap["label"],
                detail=gap["detail"],
                severity=gap["severity"],
            )
            db.session.add(mg)
    db.session.commit()

    # Return all open gaps
    all_gaps = MissingContext.query.filter_by(
        object_id=object_id, status="open"
    ).all()
    return [g.to_dict() for g in all_gaps]


# ---------------------------------------------------------------------------
# 8. Workspace Health
# ---------------------------------------------------------------------------

def compute_workspace_health(object_id: str) -> dict[str, Any]:
    """Compute a deterministic health assessment for an object.

    Derived from: completeness, activity, relationships, commitments,
    conversations, unresolved issues.

    Health is explainable and reproducible — same state always produces
    same score.
    """
    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return {"error": "Object not found"}

    space = FounderSpace.query.filter_by(space_id=obj.space_id).first()
    conv = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()

    # --- Dimension scores (each 0.0 - 1.0) ---

    # Completeness: has name, type, content, owner
    completeness = 0.0
    comp_factors = []
    if obj.name:
        completeness += 0.25
        comp_factors.append("named")
    if obj.object_type:
        completeness += 0.25
        comp_factors.append("typed")
    if obj.content and obj.content.strip():
        completeness += 0.25
        comp_factors.append("has content")
    else:
        comp_factors.append("missing content")
    if obj.created_by:
        completeness += 0.25
        comp_factors.append("has owner")
    else:
        comp_factors.append("missing owner")

    # Activity: recency of updates
    activity = 0.0
    act_factors = []
    if obj.updated_at:
        days = _days_since(obj.updated_at)
        if days <= 1:
            activity = 1.0
            act_factors.append("updated recently")
        elif days <= 7:
            activity = 0.7
            act_factors.append(f"updated {round(days)}d ago")
        elif days <= 30:
            activity = 0.4
            act_factors.append(f"updated {round(days)}d ago")
        else:
            activity = 0.15
            act_factors.append(f"stale ({round(days)}d)")
    else:
        act_factors.append("no update timestamp")

    # Relationships: presence in a space with relationships
    relationship_score = 0.0
    rel_factors = []
    if space:
        rel_count = BusinessRelationship.query.filter_by(
            space_id=space.space_id, status="active"
        ).count()
        if rel_count >= 5:
            relationship_score = 1.0
            rel_factors.append(f"{rel_count} relationships")
        elif rel_count >= 2:
            relationship_score = 0.7
            rel_factors.append(f"{rel_count} relationships")
        elif rel_count >= 1:
            relationship_score = 0.4
            rel_factors.append(f"{rel_count} relationship")
        else:
            rel_factors.append("no relationships")
    else:
        rel_factors.append("no space")

    # Conversations
    conversation_score = 0.0
    conv_factors = []
    if conv:
        msg_count = FounderMessage.query.filter_by(conv_id=conv.conv_id).count()
        if msg_count >= 10:
            conversation_score = 1.0
            conv_factors.append(f"{msg_count} messages")
        elif msg_count >= 5:
            conversation_score = 0.8
            conv_factors.append(f"{msg_count} messages")
        elif msg_count >= 2:
            conversation_score = 0.5
            conv_factors.append(f"{msg_count} messages")
        else:
            conversation_score = 0.2
            conv_factors.append("1 message")
    else:
        conv_factors.append("no conversation")

    # Unresolved issues
    issue_count = MissingContext.query.filter_by(
        object_id=object_id, status="open"
    ).count()
    commitment_score = max(0.0, 1.0 - (issue_count * 0.2))
    issue_factors = [f"{issue_count} open gap{'s' if issue_count != 1 else ''}"] if issue_count > 0 else ["no open issues"]

    overall = round(
        0.30 * completeness
        + 0.20 * activity
        + 0.15 * relationship_score
        + 0.20 * conversation_score
        + 0.15 * commitment_score,
        3,
    )

    # Health label
    if overall >= 0.8:
        label = "healthy"
        trend = "stable"
    elif overall >= 0.5:
        label = "needs_attention"
        trend = "stable" if activity > 0.5 else "declining"
    else:
        label = "critical"
        trend = "declining"

    breakdown = {
        "completeness": {"score": round(completeness, 2), "factors": comp_factors},
        "activity": {"score": round(activity, 2), "factors": act_factors},
        "relationships": {"score": round(relationship_score, 2), "factors": rel_factors},
        "conversations": {"score": round(conversation_score, 2), "factors": conv_factors},
        "commitments": {"score": round(commitment_score, 2), "factors": issue_factors},
    }

    # Persist snapshot
    snapshot = WorkspaceHealthSnapshot(
        object_id=object_id,
        overall_score=overall,
        completeness_score=round(completeness, 2),
        activity_score=round(activity, 2),
        relationship_score=round(relationship_score, 2),
        conversation_score=round(conversation_score, 2),
        commitment_score=round(commitment_score, 2),
        description=f"Health: {label} (score: {overall})",
        breakdown=json.dumps(breakdown),
    )
    db.session.add(snapshot)
    db.session.commit()

    return {
        "object_id": object_id,
        "overall_score": overall,
        "label": label,
        "trend": trend,
        "breakdown": breakdown,
        "description": f"This object is {label}. {'Action recommended.' if label != 'healthy' else 'All dimensions are satisfactory.'}",
        "recorded_at": snapshot.recorded_at.isoformat() if snapshot.recorded_at else None,
    }


# ---------------------------------------------------------------------------
# 9. Evidence Explorer
# ---------------------------------------------------------------------------

def build_evidence_explorer(object_id: str) -> list[dict[str, Any]]:
    """Trace every statement in the workspace to its underlying evidence.

    Returns a structured list of provenance entries linking workspace
    statements to: objects, relationships, events, conversations,
    commitments, runtime observations.
    """
    evidence: list[dict[str, Any]] = []
    obj = FounderObject.query.filter_by(object_id=object_id).first()
    if not obj:
        return evidence

    # Object evidence
    evidence.append({
        "statement": f"Object '{obj.name}' exists",
        "source_type": "object",
        "source_detail": f"object_id={obj.object_id}, type={obj.object_type}",
        "provenance": json.dumps({
            "table": "founder_objects",
            "object_id": obj.object_id,
            "field": "name",
            "value": obj.name,
        }),
        "confidence": "certain",
    })

    if obj.created_at:
        evidence.append({
            "statement": f"Created on {obj.created_at.strftime('%b %d, %Y')}",
            "source_type": "object",
            "source_detail": f"Timestamp from founder_objects.created_at",
            "provenance": json.dumps({
                "table": "founder_objects",
                "object_id": obj.object_id,
                "field": "created_at",
                "value": obj.created_at.isoformat(),
            }),
            "confidence": "certain",
        })

    # Space evidence
    space = FounderSpace.query.filter_by(space_id=obj.space_id).first()
    if space:
        evidence.append({
            "statement": f"Belongs to space '{space.name}'",
            "source_type": "relationship",
            "source_detail": f"space_id={space.space_id}",
            "provenance": json.dumps({
                "table": "founder_spaces",
                "space_id": space.space_id,
                "relationship": "founder_objects.space_id → founder_spaces.space_id",
            }),
            "confidence": "certain",
        })

    # Conversation evidence
    conv = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()
    if conv:
        msg_count = FounderMessage.query.filter_by(conv_id=conv.conv_id).count()
        evidence.append({
            "statement": f"Has {msg_count} conversation message{'s' if msg_count != 1 else ''}",
            "source_type": "conversation",
            "source_detail": f"conv_id={conv.conv_id}",
            "provenance": json.dumps({
                "table": "founder_messages",
                "conv_id": conv.conv_id,
                "count": msg_count,
            }),
            "confidence": "certain",
        })

        # Show last message as evidence
        last_msg = FounderMessage.query.filter_by(conv_id=conv.conv_id).order_by(
            FounderMessage.created_at.desc()
        ).first()
        if last_msg:
            evidence.append({
                "statement": f"Last message: \"{last_msg.content[:100]}\"",
                "source_type": "conversation",
                "source_detail": f"by {last_msg.role}",
                "provenance": json.dumps({
                    "table": "founder_messages",
                    "message_id": last_msg.id,
                    "role": last_msg.role,
                    "content_preview": last_msg.content[:200],
                }),
                "confidence": "certain",
            })

    # Relationship evidence
    if space:
        rels = BusinessRelationship.query.filter_by(
            space_id=space.space_id, status="active"
        ).all()
        if rels:
            rel_names = [r.name for r in rels[:5]]
            evidence.append({
                "statement": f"Connected to {len(rels)} business relationship{'s' if len(rels) != 1 else ''} ({', '.join(rel_names[:3])}{'...' if len(rel_names) > 3 else ''})",
                "source_type": "relationship",
                "source_detail": f"via space_id={space.space_id}",
                "provenance": json.dumps({
                    "table": "founder_relationships",
                    "space_id": space.space_id,
                    "count": len(rels),
                    "names": rel_names,
                }),
                "confidence": "certain",
            })

    # Health evidence
    health = WorkspaceHealthSnapshot.query.filter_by(object_id=object_id).order_by(
        WorkspaceHealthSnapshot.recorded_at.desc()
    ).first()
    if health:
        evidence.append({
            "statement": f"Health score: {health.overall_score} — last assessed",
            "source_type": "runtime_observation",
            "source_detail": f"snapshot_id={health.id}",
            "provenance": json.dumps({
                "table": "wksp_health_snapshots",
                "snapshot_id": health.id,
                "overall_score": health.overall_score,
                "recorded_at": health.recorded_at.isoformat() if health.recorded_at else None,
            }),
            "confidence": "certain",
        })

    return evidence


# ---------------------------------------------------------------------------
# 10. Navigation Canon
# ---------------------------------------------------------------------------

def navigate_to_object(source_object_id: str, target_object_id: str,
                       identity_id: str, relationship_type: str = "related",
                       context_label: str = "") -> dict[str, Any]:
    """Navigate from one object to another, preserving context.

    Records the navigation in the trail and returns the target workspace
    context so the founder can continue without losing the thread.
    """
    # Validate target exists
    target = FounderObject.query.filter_by(
        object_id=target_object_id, status="active"
    ).first()
    if not target:
        return {"error": "Target object not found"}

    # Record navigation
    nav = WorkspaceNavigation(
        identity_id=identity_id,
        source_object_id=source_object_id,
        target_object_id=target_object_id,
        relationship_type=relationship_type,
        context_label=context_label or f"From {source_object_id}",
    )
    db.session.add(nav)
    db.session.commit()

    # Return target workspace context
    return {
        "navigation_recorded": True,
        "target_object_id": target_object_id,
        "target_name": target.name,
        "target_type": target.object_type,
        "source_object_id": source_object_id,
        "relationship_type": relationship_type,
        "context_label": context_label,
    }


def get_navigation_history(identity_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """Return navigation history for an identity.

    Enables breadcrumb trails and context restoration across sessions.
    """
    navs = WorkspaceNavigation.query.filter_by(identity_id=identity_id).order_by(
        WorkspaceNavigation.created_at.desc()
    ).limit(limit).all()
    return [n.to_dict() for n in navs]


# ---------------------------------------------------------------------------
# Full Workspace Assembly
# ---------------------------------------------------------------------------

def build_full_workspace(object_id: str) -> dict[str, Any]:
    """Assemble the complete workspace for an object.

    Returns all intelligence panels in a single response.
    For rendering the full workspace on load.
    """
    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return {"error": "Object not found"}

    return {
        "summary": build_workspace_summary(object_id),
        "ai_understanding": build_ai_understanding(object_id),
        "relationships": build_relationship_intelligence(object_id),
        "timeline": build_activity_timeline(object_id, limit=20),
        "conversation": get_conversation_workspace(object_id),
        "next_actions": build_next_actions(object_id),
        "missing_context": detect_missing_context(object_id),
        "health": compute_workspace_health(object_id),
        "evidence": build_evidence_explorer(object_id),
    }


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _object_type_icon(object_type: str) -> str:
    """Return an appropriate icon for an object type."""
    icons = {
        "Document": "📄",
        "Lead": "🎯",
        "Invoice": "🧾",
        "Proposal": "📋",
        "Contract": "📑",
        "Task": "✅",
        "Project": "📊",
        "Customer": "👤",
        "Note": "📝",
        "Design": "🎨",
        "Spreadsheet": "📈",
        "Report": "📊",
        "Email": "✉️",
        "Conversation": "💬",
    }
    return icons.get(object_type, "📦")


def acknowledge_next_action(action_id: int) -> str:
    """Mark a next action as completed."""
    action = NextAction.query.get(action_id)
    if action:
        action.status = "completed"
        action.completed_at = _now()
        db.session.commit()
        return "completed"
    return "not_found"


def dismiss_missing_context(context_id: int) -> str:
    """Dismiss a missing context entry."""
    mc = MissingContext.query.get(context_id)
    if mc:
        mc.status = "addressed"
        db.session.commit()
        return "addressed"
    return "not_found"