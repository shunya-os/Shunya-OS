"""Conversation Persistence Bridge — ConversationRuntime → FounderMessage persistence.

Wires the ConversationRuntime's set_persistence_provider() API to the canonical
FounderConversation/FounderMessage models so conversation history survives
process restarts.

The bridge is intentionally thin — it is a persistence adapter between the
runtime's session_id-based message model and the DB's conv_id-based model.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _ensure_conversation(session_id: str) -> str:
    """Ensure a FounderConversation exists for this session_id (= conv_id).

    Returns the conv_id (same as session_id).
    """
    from app.founder.models import FounderConversation
    from app import db
    from datetime import datetime, timezone

    conv = FounderConversation.query.filter_by(conv_id=session_id).first()
    if conv is None:
        conv = FounderConversation(
            conv_id=session_id,
            object_id=f"conv_{session_id[:12]}",
            title="AI Chat",
            identity_id="",
            status="active",
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(conv)
        db.session.commit()
    return session_id


def save_message(session_id: str, role: str, content: str) -> None:
    """Persist a single conversation message to the founder_messages table.

    Args:
        session_id: Used as conv_id in FounderConversation/FounderMessage.
        role: 'human' or 'assistant'.
        content: The message text.
    """
    from app.founder.models import FounderMessage
    from app import db
    from datetime import datetime, timezone

    try:
        _ensure_conversation(session_id)
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