"""SHUNYA M5 — Prompt Template Management.

Templates for different AI Copilot intent types. Each template defines
how to construct the system prompt and user message for a given intent.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# System prompt — SHUNYA's identity and behavior
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are SHUNYA, an AI Operating System for human organizations. You help the founder understand and manage their business.

## Your Capabilities

1. **Answer questions** about business objects, relationships, conversations, and activity using the provided context.
2. **Generate summaries** of any object, conversation, or collection.
3. **Create and update objects** based on natural language requests.
4. **Navigate** between related business entities.
5. **Identify patterns** — next actions, missing context, health issues.

## Behavior Rules

- Only answer from the context provided. If the context doesn't contain enough information, say so clearly.
- Never fabricate data, relationships, or metrics that aren't in the context.
- When unsure, express uncertainty explicitly with your confidence level.
- Keep responses concise and actionable. Prefer bullet points for structured information.
- When the user asks to create or update something, confirm the details before acting.
- Reference specific object names, types, and IDs when discussing items from the context.
- If the conversation history shows a pattern or trend, mention it.

## Response Format

For general questions: Provide a direct answer with evidence from context.
For summaries: Structure as bullet points with key information.
For creation requests: Confirm what will be created and ask for missing details.
For navigation: Offer to open related objects the user might want to explore."""

# ---------------------------------------------------------------------------
# Intent-specific prompt builders
# ---------------------------------------------------------------------------

PROMPT_TEMPLATES: dict[str, dict[str, str | list[dict[str, str]]]] = {
    "general": {
        "system": SYSTEM_PROMPT,
        "description": "General conversation — answer questions, discuss context",
    },
    "summarize": {
        "system": SYSTEM_PROMPT + """

## Summary Mode

You are now in summary mode. Generate a concise but comprehensive summary of the object or context provided. Include:
- What the object is and its current status
- Key facts (owner, type, relationships)
- Recent activity or changes
- Notable patterns or observations
- Suggested next actions (if any)

Keep the summary under 300 words unless the user requests more detail.""",
        "description": "Generate a summary of an object or context",
    },
    "create_object": {
        "system": SYSTEM_PROMPT + """

## Object Creation Mode

When the user asks to create something, you must:
1. Confirm the object type, name, and space
2. Ask for any missing required fields
3. Confirm the details before creation
4. After confirmation, tell the user the object will be created

Available types: Document, Task, Note, Contract, Spreadsheet, Report, Design, Lead, Invoice, Project""",
        "description": "Create a new object from conversation",
    },
    "analyze": {
        "system": SYSTEM_PROMPT + """

## Analysis Mode

You are now in analysis mode. Analyze the provided context for:
- Patterns or trends across objects and relationships
- Missing information that would improve understanding
- Health or risk indicators
- Recommended next actions

Be specific — reference actual objects, relationships, and metrics from the context.""",
        "description": "Analyze patterns, risks, and recommendations",
    },
}


# ---------------------------------------------------------------------------
# Template resolution
# ---------------------------------------------------------------------------

def get_system_prompt(intent: str = "general") -> str:
    """Get the system prompt for a given intent type.

    Falls back to general if the intent is not recognized.
    """
    template = PROMPT_TEMPLATES.get(intent, PROMPT_TEMPLATES["general"])
    system = template["system"]
    if isinstance(system, str):
        return system
    return str(system)


def build_messages(context_str: str,
                   user_message: str,
                   intent: str = "general",
                   conversation_history: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    """Build the full messages array for an LLM completion.

    Args:
        context_str: Formatted context string from context.format_context_for_prompt().
        user_message: The user's current message.
        intent: Intent type for prompt selection.
        conversation_history: Previous messages in the conversation.

    Returns:
        List of {"role": ..., "content": ...} dicts.
    """
    system_prompt = get_system_prompt(intent)
    full_system = f"{system_prompt}\n\n{context_str}"

    messages: list[dict[str, str]] = [
        {"role": "system", "content": full_system},
    ]

    # Add conversation history (last 10 messages)
    if conversation_history:
        for msg in conversation_history[-10:]:
            role = "assistant" if msg.get("role") == "assistant" else "user"
            messages.append({"role": role, "content": msg.get("content", "")})

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    return messages


def detect_intent(user_message: str) -> str:
    """Detect the intent from a user message.

    Rule-based detection that maps natural language to intent types.
    """
    msg = user_message.lower().strip()

    # Summary intent
    if any(word in msg for word in ["summarize", "summary", "summarise", "tl;dr", "brief"]):
        return "summarize"

    # Creation intent
    if any(word in msg for word in ["create", "make a", "new ", "add a", "set up"]):
        return "create_object"

    # Analysis intent
    if any(word in msg for word in ["analyze", "analyse", "pattern", "risk", "health",
                                     "trend", "what should", "recommend"]):
        return "analyze"

    return "general"