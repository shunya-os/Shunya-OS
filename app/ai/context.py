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
    FounderConversation,
    FounderMessage,
)
from core.object_service import get_object_service


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

    # Object context — canonical first (sh_objects), legacy fallback (compat)
    space_id = None

    if object_id:
        canonical = None
        try:
            canonical = get_object_service().get_by_object_id(object_id)
        except Exception:
            canonical = None

        if canonical:
            space_id = canonical.get("workspace_id") or canonical.get("space_id")
            context["object"] = {
                "object_id": canonical.get("object_id", object_id),
                "name": canonical.get("name", ""),
                "object_type": canonical.get("object_type") or "unknown",
                "status": canonical.get("status", "active"),
                "content": (canonical.get("content") or canonical.get("data") or {}).get("content", "") if isinstance(canonical.get("data") or canonical.get("content"), dict) else str(canonical.get("content") or "")[:1000],
                "created_by": canonical.get("created_by", ""),
                "created_at": canonical.get("created_at"),
                "updated_at": canonical.get("updated_at"),
            }

            # Space context via FounderSpace (compat boundary — sh_objects has workspace_id)
            if space_id:
                from app.founder.models import FounderSpace
                space = FounderSpace.query.filter_by(space_id=space_id).first()
                if space:
                    context["space"] = {
                        "space_id": space.space_id,
                        "name": space.name,
                        "space_type": space.space_type,
                    }

            # Same-space objects via ObjectService (canonical)
            try:
                org_id = canonical.get("organization_id", 0)
                if space_id and org_id > 0:
                    siblings = get_object_service().list_by_workspace(
                        workspace_id=space_id, organization_id=org_id, limit=5
                    )
                    if siblings:
                        context["same_space_objects"] = [
                            {
                                "object_id": s.get("object_id", ""),
                                "name": s.get("name", ""),
                                "object_type": s.get("object_type", ""),
                            }
                            for s in siblings if s.get("object_id") != object_id
                        ]
            except Exception:
                pass
        else:
            # Legacy fallback — founder_objects
            from app.founder.models import FounderObject, FounderSpace
            from app.founder.models import BusinessRelationship

            obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
            if obj:
                space_id = obj.space_id
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
                space = FounderSpace.query.filter_by(space_id=space_id).first()
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

                # Same-space objects (legacy compat)
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

    # Conversation context (shared — not object-scoped)
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
                "object_id": conv.object_id,
                "title": conv.title,
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content[:2000] if m.content else "",
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in messages
                ],
            }

    return context