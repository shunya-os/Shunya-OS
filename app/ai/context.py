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
from sqlalchemy import text


def assemble_context(object_id: str | None = None,
                     identity_id: str | None = None,
                     organization_id: int = 0,
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
            from app.authz.workspace_context import OwnershipContextError
            canonical = get_object_service().get_by_object_id(
                object_id, organization_id=organization_id,
                identity_id=identity_id)
        except (OwnershipContextError, ValueError):
            # Denial (or insufficient context) is NOT an error to repair with a
            # legacy read: the canonical absence is authoritative.
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

            # Space context — canonical sh_workspaces (no legacy space store)
            if space_id:
                ws_row = db.session.execute(
                    text("SELECT id, name, workspace_type FROM sh_workspaces WHERE id = :ws_id"),
                    {"ws_id": space_id},
                ).first()
                if ws_row:
                    context["space"] = {
                        "space_id": ws_row.id,
                        "name": ws_row.name,
                        "space_type": ws_row.workspace_type,
                    }
                    # Relationship context for the canonical workspace
                    from app.founder.models import BusinessRelationship
                    rels = BusinessRelationship.query.filter_by(
                        space_id=space_id, status="active"
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

            # Same-space objects via ObjectService (canonical)
            try:
                org_id = canonical.get("organization_id", 0)
                if space_id and org_id > 0 and identity_id:
                    siblings = get_object_service().list_by_workspace(
                        workspace_id=space_id, organization_id=org_id,
                        identity_id=identity_id, limit=5
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
        # Canonical absence is authoritative: there is no legacy object fallback.
        # A missing canonical row yields no object context (fail closed) rather
        # than reading founder_objects, which is not tenant-scoped truth.

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