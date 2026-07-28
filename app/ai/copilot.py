"""SHUNYA M5 — AI Copilot Service.

The primary interface for conversational AI in SHUNYA. Processes user messages
through the LLM provider with full pipeline context. Generates summaries,
answers questions, and enables object creation from conversation.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from app import db
from app.ai.context import assemble_context, format_context_for_prompt
from app.ai.prompts import build_messages, detect_intent
from app.ai.provider import get_provider, set_provider, LocalProvider, reset_provider
from app.founder.models import (
    FounderConversation,
    FounderMessage,
    FounderObject,
    FounderSpace,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conversation processing
# ---------------------------------------------------------------------------

def process_message(conv_id: str, user_message: str) -> dict[str, Any]:
    """Process a user message through the AI Copilot.

    This is the primary entry point for the AI Copilot. It:
    1. Loads the conversation and its context
    2. Assembles the context window from pipeline state
    3. Detects the user's intent
    4. Builds the prompt messages
    5. Calls the LLM provider
    6. Persists both human and assistant messages
    7. Returns the response

    Args:
        conv_id: The conversation ID.
        user_message: The user's message text.

    Returns:
        {"success": bool, "response": str, "model": str, ...}
    """
    # Load conversation
    conv = FounderConversation.query.filter_by(conv_id=conv_id, status="active").first()
    if not conv:
        return {"success": False, "error": "Conversation not found"}

    obj = FounderObject.query.filter_by(object_id=conv.object_id).first()
    object_id = conv.object_id if obj else None

    # Persist human message immediately
    human_msg = FounderMessage(conv_id=conv_id, role="human", content=user_message)
    db.session.add(human_msg)
    db.session.commit()

    try:
        # Assemble context
        context = assemble_context(
            object_id=object_id,
            identity_id=conv.identity_id,
        )
        context_str = format_context_for_prompt(context)

        # Detect intent
        intent = detect_intent(user_message)

        # Get conversation history
        messages = FounderMessage.query.filter_by(
            conv_id=conv_id
        ).order_by(FounderMessage.created_at.asc()).all()
        history = [{"role": m.role, "content": m.content} for m in messages[:-1]]  # Exclude the one we just added

        # Build prompt
        prompt_messages = build_messages(
            context_str=context_str,
            user_message=user_message,
            intent=intent,
            conversation_history=history,
        )

        # Call LLM provider
        provider = get_provider()
        result = provider.complete(prompt_messages)

        response_text = result.get("content", "")
        model = result.get("model", "unknown")
        finish_reason = result.get("finish_reason", "unknown")

        # If provider returned an error but response is empty, use fallback
        if not response_text and finish_reason == "error":
            logger.warning(f"LLM provider error: {result.get('error')}")
            # Fallback to local provider
            local = LocalProvider()
            fallback_messages = build_messages(
                context_str=context_str,
                user_message=user_message,
                intent=intent,
                conversation_history=history,
            )
            fallback = local.complete(fallback_messages)
            response_text = fallback.get("content", "I'm having trouble connecting to my AI services. Please try again.")
            model = "local-fallback"

        # Persist assistant message
        assistant_msg = FounderMessage(conv_id=conv_id, role="assistant", content=response_text)
        db.session.add(assistant_msg)
        conv.updated_at = datetime.utcnow()
        db.session.commit()

        return {
            "success": True,
            "response": response_text,
            "model": model,
            "intent": intent,
            "human_message_id": human_msg.id,
            "assistant_message_id": assistant_msg.id,
        }

    except Exception as e:
        logger.error(f"AI Copilot error: {e}", exc_info=True)
        db.session.rollback()

        # Provide graceful degradation response
        graceful = "I encountered an issue while processing your message. Please try again or rephrase your question."
        assistant_msg = FounderMessage(conv_id=conv_id, role="assistant", content=graceful)
        db.session.add(assistant_msg)
        db.session.commit()

        return {
            "success": True,
            "response": graceful,
            "model": "error-recovery",
            "intent": "error",
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# Entity summary generation
# ---------------------------------------------------------------------------

def generate_entity_summary(object_id: str) -> dict[str, Any]:
    """Generate an AI summary for a business entity.

    Uses the workspace intelligence data and LLM to produce a concise,
    grounded summary.

    Args:
        object_id: The object to summarize.

    Returns:
        {"success": bool, "summary": str, "model": str}
    """
    from app.founder.workspace_intelligence import build_ai_understanding, build_workspace_summary

    summary = build_workspace_summary(object_id)
    understanding = build_ai_understanding(object_id)

    if "error" in summary:
        return {"success": False, "error": summary["error"]}

    # Build context for the LLM
    context_lines = [
        f"Object: {summary.get('name', 'Unknown')}",
        f"Type: {summary.get('object_type', 'Unknown')}",
        f"Status: {summary.get('status', 'Unknown')}",
        f"Space: {summary.get('space_name', 'Unknown')}",
        f"Activity: {summary.get('activity_label', 'Unknown')}",
    ]

    if understanding and "error" not in understanding:
        context_lines.append(f"AI Understanding: {understanding.get('what_is', '')}")
        context_lines.append(f"Confidence: {understanding.get('confidence', {}).get('label', 'unknown')}")

    context_str = "\n".join(context_lines)

    system = f"""You are SHUNYA, an AI Operating System. Generate a concise executive summary of this business object based on the following context. Keep it under 150 words. Focus on what the object is, its current state, and why it matters.

Context:
{context_str}"""

    try:
        provider = get_provider()
        result = provider.complete([
            {"role": "system", "content": system},
            {"role": "user", "content": f"Summarize the object '{summary.get('name', '')}'"},
        ], max_tokens=300, temperature=0.3)

        return {
            "success": True,
            "summary": result.get("content", ""),
            "model": result.get("model", "unknown"),
        }

    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        # Fallback: deterministic summary from workspace intelligence
        fallback = f"{summary.get('name', 'Unknown')} — a {summary.get('object_type', 'unknown')} in {summary.get('space_name', 'unknown')}. Status: {summary.get('status', 'unknown')}. {summary.get('activity_label', '')}."
        return {"success": True, "summary": fallback, "model": "fallback"}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def copilot_health() -> dict[str, Any]:
    """Check the AI Copilot's health status.

    Returns provider availability, model info, and a test completion result.
    """
    provider = get_provider()
    available = provider.is_available()

    # Run a minimal test completion
    test_result = provider.complete([
        {"role": "system", "content": "Respond with one word: ok"},
        {"role": "user", "content": "Are you operational?"},
    ], max_tokens=10, temperature=0.0)

    return {
        "provider": provider.name,
        "model": provider.model if hasattr(provider, 'model') else "unknown",
        "available": available,
        "test_completion": test_result.get("content", "").strip(),
        "test_finish_reason": test_result.get("finish_reason", ""),
    }