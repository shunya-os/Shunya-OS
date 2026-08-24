"""SHUNYA M5 — Context Window Assembly.

Builds a structured context window from pipeline state for the AI Copilot.
The context provides the LLM with all relevant information about the current
conversation, object, space, relationships, and recent activity.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app import db
from app.founder.models import (
    BusinessRelationship,
    FounderConversation,
    FounderMessage,
    FounderObject,
    FounderSpace,
)


def assemble_context(object_id: str | None = None,
                     identity_id: str | None = None,
                     include_messages: int = 10) -> dict[str, Any]:
    """Assemble the current context from pipeline state.

    Returns a structured dict with all information the AI needs to
    generate grounded, context-aware responses.

    Args:
        object_id: Currently focused object (if any).
        identity_id: Current user identity.
        include_messages: Number of recent conversation messages to include.

    Returns:
        A dict with keys: object, space, relationships, conversation,
        recent_activity, identity_summary.
    """
    context: dict[str, Any] = {
        "object": None,
        "space": None,
        "relationships": [],
        "conversation": None,
        "recent_activity": [],
        "identity_summary": "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Object context
    if object_id:
        obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
        if obj:
            context["object"] = {
                "object_id": obj.object_id,
                "name": obj.name,
                "object_type": obj.object_type or "unknown",
                "status": obj.status,
                "content": obj.content[:1000] if obj.content else "",
                "created_by": obj.created_by,
                "created_at": obj.created_at.isoformat() if obj.created_at else None,
                "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
            }

            # Space context
            space = FounderSpace.query.filter_by(space_id=obj.space_id).first()
            if space:
                context["space"] = {
                    "space_id": space.space_id,
                    "name": space.name,
                    "space_type": space.space_type,
                }

            # Relationship context
            if space:
                rels = BusinessRelationship.query.filter_by(
                    space_id=space.space_id, status="active"
                ).all()
                context["relationships"] = [
                    {
                        "rel_id": r.rel_id,
                        "rel_type": r.rel_type,
                        "name": r.name,
                        "company": r.company,
                        "email": r.email,
                        "phone": r.phone,
                    }
                    for r in rels[:10]
                ]

            # Same-space objects
            siblings = FounderObject.query.filter(
                FounderObject.space_id == obj.space_id,
                FounderObject.status == "active",
                FounderObject.object_id != object_id,
            ).order_by(FounderObject.updated_at.desc()).limit(5).all()
            if siblings:
                context["same_space_objects"] = [
                    {
                        "object_id": s.object_id,
                        "name": s.name,
                        "object_type": s.object_type,
                    }
                    for s in siblings
                ]

    # Conversation context
    if object_id:
        conv = FounderConversation.query.filter_by(
            object_id=object_id, status="active"
        ).first()
        if conv:
            messages = FounderMessage.query.filter_by(
                conv_id=conv.conv_id
            ).order_by(FounderMessage.created_at.desc()).limit(include_messages).all()
            messages.reverse()  # chronological order
            context["conversation"] = {
                "conv_id": conv.conv_id,
                "title": conv.title,
                "message_count": len(messages),
                "recent_messages": [
                    {"role": m.role, "content": m.content[:500]}
                    for m in messages
                ],
            }

    # Recent activity for this identity
    if identity_id:
        spaces = FounderSpace.query.filter_by(
            identity_id=identity_id, status="active"
        ).all()
        space_ids = [s.space_id for s in spaces]
        if space_ids:
            recent_objs = FounderObject.query.filter(
                FounderObject.space_id.in_(space_ids),
                FounderObject.status == "active",
            ).order_by(FounderObject.updated_at.desc()).limit(5).all()
            context["recent_activity"] = [
                {
                    "name": o.name,
                    "object_type": o.object_type,
                    "updated_at": o.updated_at.isoformat() if o.updated_at else None,
                }
                for o in recent_objs
            ]

    return context


def format_context_for_prompt(context: dict[str, Any]) -> str:
    """Format the assembled context into a human-readable prompt section.

    This is the string that gets injected into the AI Copilot's system prompt.
    """
    parts = ["## Current SHUNYA Context\n"]

    if context.get("object"):
        o = context["object"]
        parts.append(f"### Active Object")
        parts.append(f"- Name: {o['name']}")
        parts.append(f"- Type: {o['object_type']}")
        parts.append(f"- Status: {o['status']}")
        if o.get("content"):
            parts.append(f"- Content: {o['content'][:300]}")
        if o.get("created_by"):
            parts.append(f"- Owner: {o['created_by'][:20]}")
        parts.append("")

    if context.get("space"):
        s = context["space"]
        parts.append(f"### Space: {s['name']} ({s['space_type']})")

    if context.get("relationships"):
        parts.append(f"\n### Relationships ({len(context['relationships'])})")
        for r in context["relationships"][:8]:
            company_part = f' — {r["company"]}' if r.get("company") else ""
            parts.append(f"- {r['name']} ({r['rel_type']}){company_part}")

    if context.get("same_space_objects"):
        parts.append(f"\n### Other Objects in Space")
        for sib in context["same_space_objects"]:
            parts.append(f"- {sib['name']} ({sib['object_type']})")

    if context.get("conversation"):
        conv = context["conversation"]
        parts.append(f"\n### Recent Conversation ({conv['message_count']} messages)")
        for msg in conv.get("recent_messages", []):
            role_label = "Human" if msg["role"] == "human" else "Assistant"
            content_preview = msg["content"][:200]
            parts.append(f"\n**{role_label}:** {content_preview}")

    if context.get("recent_activity"):
        parts.append(f"\n### Recent Activity")
        for act in context["recent_activity"][:3]:
            parts.append(f"- {act['name']} ({act['object_type']})")

    return "\n".join(parts)