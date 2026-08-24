"""SHUNYA M5 — AI Copilot Adapter (DEPRECATED).

This module is a thin adapter over the Universal Intelligence Runtime.
All new code should use core.intelligence_runtime.integration.ask() directly.
This adapter exists only for backward compatibility with app/founder/routes.py.

Removal target: when app/founder/routes.py is fully migrated to the UIR.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app import db
from app.founder.models import (
    FounderConversation,
    FounderMessage,
)

logger = logging.getLogger(__name__)


def process_message(conv_id: str, user_message: str, space_id: str | None = None,
                    org_id: str | None = None, identity_id: str | None = None) -> dict[str, Any]:
    """Process a message through the Universal Intelligence Runtime.

    This is a thin adapter. The actual reasoning happens in the UIR.
    """
    try:
        from core.intelligence_runtime.integration import ask, ensure_runtime
        ensure_runtime()

        session_id = f"conv_{conv_id}"
        module_key = ""

        # Detect module from context
        if space_id:
            module_key = "travel"  # default for backward compat

        result = ask(
            query=user_message,
            session_id=session_id,
            module_key=module_key,
            workspace=space_id or "founder",
            explain=False,
        )

        response_text = result.get("content", "I processed your request.")

        # Store conversation in DB for backward compatibility
        try:
            conv = FounderConversation.query.filter_by(conv_id=conv_id).first()
            if conv:
                msg = FounderMessage(
                    conv_id=conv_id,
                    role="user",
                    content=user_message,
                    created_at=datetime.now(timezone.utc),
                )
                db.session.add(msg)
                reply = FounderMessage(
                    conv_id=conv_id,
                    role="assistant",
                    content=response_text,
                    created_at=datetime.now(timezone.utc),
                )
                db.session.add(reply)
                db.session.commit()
        except Exception as e:
            logger.warning("Could not persist conversation: %s", e)

        return {
            "success": True,
            "response": response_text,
            "model": "uir",
            "intent": result.get("trace", {}).get("intent", {}).get("category", "unknown"),
            "confidence": result.get("trace", {}).get("confidence", 0),
        }

    except Exception:
        logger.exception("UIR adapter failed")
        return {
            "success": True,
            "response": "I encountered an issue processing your request. Please try again.",
            "model": "uir_fallback",
            "intent": "unknown",
            "confidence": 0,
        }


def generate_entity_summary(entity_type: str, entity_id: str, space_id: str | None = None) -> str:
    """Generate an AI summary of a business object using the UIR."""
    try:
        from core.intelligence_runtime.integration import ask, ensure_runtime
        ensure_runtime()

        session_id = f"summary_{entity_type}_{entity_id}"
        result = ask(
            query=f"Summarize this {entity_type}: {entity_id}",
            session_id=session_id,
            object_type=entity_type,
            object_id=entity_id,
        )
        return result.get("content", f"No summary available for {entity_type}.")
    except Exception:
        return f"{entity_type} record."


def copilot_health() -> dict[str, Any]:
    """Health check — delegates to UIR health."""
    try:
        from core.intelligence_runtime.integration import health
        h = health()
        return {
            "status": "healthy",
            "model": "uir",
            "memory": h.get("memory_count", 0),
            "requests": h.get("telemetry", {}).get("request_count", 0),
        }
    except Exception:
        return {"status": "degraded", "model": "unavailable"}