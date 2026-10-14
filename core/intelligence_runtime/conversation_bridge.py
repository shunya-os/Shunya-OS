"""Conversation Persistence Bridge — ConversationRuntime → FounderMessage persistence.

Wires the ConversationRuntime's set_persistence_provider() API to the canonical
FounderConversation/FounderMessage models so conversation history survives
process restarts.

The bridge is intentionally thin — it is a persistence adapter between the
runtime's session_id-based message model and the DB's conv_id-based model.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


def _ensure_founder_object(object_id: str, title: str, identity_id: str = "") -> None:
    """Ensure a FounderObject exists so the FounderConversation FK is satisfied.

    founder_conversations.object_id carries a FK constraint to
    founder_objects.object_id — an object row MUST exist before the
    conversation row can be inserted. This helper creates one when
    missing, attaching it to the identity's first space (fallback:
    the system space).
    """
    from app.founder.models import FounderObject, FounderSpace
    from app import db
    from datetime import datetime, timezone

    if FounderObject.query.filter_by(object_id=object_id).first():
        return  # already exists

    space_id: str | None = None
    if identity_id:
        sp = FounderSpace.query.filter_by(identity_id=identity_id).order_by(
            FounderSpace.created_at.asc()
        ).first()
        if sp:
            space_id = sp.space_id
    if not space_id:
        system = FounderSpace.query.filter_by(space_id="space_system").first()
        if system:
            space_id = system.space_id
        else:
            system = FounderSpace(
                space_id="space_system",
                name="System Space",
                space_type="system",
                identity_id=identity_id or "system",
                status="active",
            )
            db.session.add(system)
            db.session.flush()
            space_id = system.space_id

    obj = FounderObject(
        object_id=object_id,
        space_id=space_id,
        object_type="conversation",
        name=title or "AI Chat",
        status="active",
        created_by=identity_id or "",
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(obj)


def _ensure_conversation(session_id: str, identity_id: str = "") -> str:
    """Ensure a FounderConversation exists for this session_id (= conv_id).

    A FounderObject is created first (via _ensure_founder_object) so the
    founder_conversations.object_id → founder_objects.object_id FK constraint
    is satisfied. Previously the object_id was a synthetic "conv_<session>"
    string with NO matching founder_objects row — that is exactly the FK
    violation seen in production ("conv_conv_convers..." / object not found).

    Returns the conv_id (same as session_id).
    """
    from app.founder.models import FounderConversation
    from app import db
    from datetime import datetime, timezone

    conv = FounderConversation.query.filter_by(conv_id=session_id).first()
    if conv is None:
        object_id = str(uuid.uuid4())
        _ensure_founder_object(object_id=object_id, title="AI Chat", identity_id=identity_id)
        conv = FounderConversation(
            conv_id=session_id,
            object_id=object_id,
            title="AI Chat",
            identity_id=identity_id or "",
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
        identity_id: Owner identity, threaded through to FounderObject so
                     the row is attributed (and space-resolved) correctly.
    """
    from app.founder.models import FounderMessage
    from app import db
    from datetime import datetime, timezone

    try:
        _ensure_conversation(session_id, identity_id)
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