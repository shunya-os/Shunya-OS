"""Conversation Persistence Bridge — ConversationRuntime → FounderMessage persistence.

Wires the ConversationRuntime's set_persistence_provider() API to the canonical
FounderConversation/FounderMessage models so conversation history survives
process restarts.

The bridge is intentionally thin — it is a persistence adapter between the
runtime's session_id-based message model and the DB's conv_id-based model.

Canonical arch (R6B-2): founder_conversations.object_id FK → sh_objects.object_id.
No FounderObject writes are permitted outside the model definition (GATE 7).
A ShunyaObject row must exist in sh_objects before the conversation row can be
inserted. This bridge creates one via ObjectService when a real identity context
is available, and skips persistence gracefully when no context exists (background
operations without an authenticated user).

The caller (ConversationRuntime.add_message) wraps the save in try/except, so a
skip or failure is non-fatal — the in-memory conversation continues to work.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


def _resolve_context(identity_id: str = "") -> str | None:
    """Resolve an authenticated identity_id from available context.

    Priority:
      1. Explicit identity_id argument.
      2. Flask request context (g.identity_id).
      3. Flask session (identity_id, user_id).

    Returns the identity_id string, or None when no real context is available.
    Never fabricates synthetic identity values.
    """
    _id = identity_id

    if not _id:
        try:
            from flask import g as _g
            _id = str(getattr(_g, "identity_id", "") or "")
        except (Exception, RuntimeError):
            pass

    if not _id:
        try:
            from flask import session as _sess
            _id = str(_sess.get("identity_id", _sess.get("user_id", "")) or "")
        except (Exception, RuntimeError):
            pass

    if not _id:
        return None  # No identity — cannot create tenant-scoped objects

    return _id


def _find_org_for_identity(identity_id: str) -> tuple[int, str] | None:
    """Find the identity's first active organization membership + workspace.

    Returns (org_id, workspace_id) or None if not found.
    Written with deferred imports to avoid circular imports at module load.
    """
    from app import db
    from sqlalchemy import text as _sql

    try:
        row = db.session.execute(
            _sql(
                "SELECT om.organization_id, wsm.workspace_id "
                "FROM org_members om "
                "JOIN sh_workspace_memberships wsm ON wsm.identity_id = om.identity_id "
                "JOIN sh_workspaces w ON w.id = wsm.workspace_id "
                "WHERE om.identity_id = :id "
                "AND om.is_active = true "
                "AND wsm.is_active = true "
                "AND w.status = 'active' "
                "ORDER BY om.joined_at ASC LIMIT 1"
            ),
            {"id": identity_id},
        ).first()
        if row:
            return int(row[0]), str(row[1])
    except Exception:
        logger.warning("Context resolution for identity %s failed", identity_id, exc_info=True)
    return None


def _ensure_canonical_object(identity_id: str, org_id: int, workspace_id: str,
                              title: str) -> str:
    """Create a ShunyaObject row via ObjectService.

    Returns the object_id string. The row is committed by ObjectService.create().
    """
    from core.object_service import get_object_service

    created = get_object_service().create(
        object_type="conversation",
        name=title or "AI Chat",
        organization_id=org_id,
        workspace_id=workspace_id,
        created_by=identity_id,
        data={},
        identity_id=identity_id,
        # G1.24: created by the AI runtime for this conversation, not typed by
        # the user. Recorded so the origin is never inferred later.
        provenance="ai",
    )
    return created["object_id"]


def _ensure_conversation(session_id: str, identity_id: str = "") -> str:
    """Ensure a FounderConversation exists for this session_id (= conv_id).

    Creates a ShunyaObject in the canonical store first (via ObjectService) so
    the founder_conversations.object_id → sh_objects.object_id FK constraint is
    satisfied.

    When the identity context cannot be resolved (no authenticated user), the
    conversation is NOT persisted — the in-memory conversation continues to work
    via ConversationRuntime's default in-memory store.

    Returns the conv_id (same as session_id), or empty string when skipped.
    """
    from app.founder.models import FounderConversation
    from app import db
    from datetime import datetime, timezone

    conv = FounderConversation.query.filter_by(conv_id=session_id).first()
    if conv is not None:
        return session_id

    # Resolve identity context
    _identity = _resolve_context(identity_id)
    if _identity is None:
        logger.warning(
            "Conversation persistence skipped (no identity context): session=%s",
            session_id,
        )
        return ""

    # Resolve org + workspace from DB memberships
    org_ws = _find_org_for_identity(_identity)
    if org_ws is None:
        logger.warning(
            "Conversation persistence skipped (no org/workspace for %s): session=%s",
            _identity,
            session_id,
        )
        return ""

    org_id, ws_id = org_ws

    try:
        object_id = _ensure_canonical_object(
            identity_id=_identity, org_id=org_id, workspace_id=ws_id,
            title="AI Chat",
        )
    except Exception:
        logger.warning(
            "Conversation persistence skipped (object creation failed): session=%s",
            session_id,
            exc_info=True,
        )
        return ""

    conv = FounderConversation(
        conv_id=session_id,
        object_id=object_id,
        title="AI Chat",
        identity_id=_identity,
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(conv)
    db.session.commit()
    return session_id


def save_message(session_id: str, role: str, content: str, identity_id: str = "") -> None:
    """Persist a single conversation message to the founder_messages table.

    Args:
        session_id: Used as conv_id in FounderConversation/FounderMessage.
        role: 'human' or 'assistant'.
        content: The message text.
        identity_id: Owner identity; if empty, resolved from the request context.
    """
    from app.founder.models import FounderMessage
    from app import db
    from datetime import datetime, timezone

    try:
        conv_id = _ensure_conversation(session_id, identity_id)
        if not conv_id:
            return  # Skipped — in-memory path handles it
        msg = FounderMessage(
            conv_id=session_id,
            role="human" if role == "user" else "assistant",
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(msg)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.warning("Conversation save failed (session=%s): %s", session_id, exc)


def load_history(session_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Load persisted conversation history.

    Args:
        session_id: conv_id in FounderConversation/FounderMessage.
        limit: Max messages to return.

    Returns:
        List of {role, content, timestamp} dicts, newest first.
    """
    from app.founder.models import FounderMessage

    try:
        msgs = (
            FounderMessage.query
            .filter_by(conv_id=session_id)
            .order_by(FounderMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if msg.created_at else "",
            }
            for msg in reversed(msgs)  # reverse so caller sees chronological order
        ]
    except Exception as exc:
        logger.warning("Conversation load failed (session=%s): %s", session_id, exc)
        return []