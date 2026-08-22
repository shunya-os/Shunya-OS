"""
AI Command Lifecycle — bridges AI chat to durable execution state.

When a user submits a meaningful command through AI chat (not just a question),
this module creates canonical Outcome, Task, and ExecutionLog records so the
work is discoverable through /api/v1/execution/outputs and /api/v1/execution/work.

Architecture:

USER MESSAGE (via /api/v1/ai/chat)
    ↓
AI INTERPRETATION (via provider chain)
    ↓
COMMAND DETECTION (heuristic — keywords vs question patterns)
    ↓
IF COMMAND:
    ├─ Outcome created with user intention
    ├─ ExecutionLog entry recorded
    ├─ Task created where applicable
    └─ Response includes command_id, outcome_id, execution_link
ELSE (question):
    └─ Normal AI response without execution linkage
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Keywords that suggest a command rather than a question
_COMMAND_KEYWORDS = {
    "create", "make", "build", "generate", "write", "send", "schedule",
    "assign", "update", "change", "set", "start", "stop", "cancel",
    "delete", "remove", "archive", "approve", "reject", "submit",
    "prepare", "draft", "compose", "order", "purchase", "book",
    "register", "invite", "add", "pay", "transfer", "download",
    "upload", "export", "import", "deploy", "publish", "launch",
}

_QUESTION_INDICATORS = {"?", "what", "who", "where", "when", "why", "how", "is", "are", "can", "do", "does", "did", "will", "would", "could", "should", "may", "might", "tell me", "explain", "show me", "list", "find", "search"}


def _is_command_message(user_message: str) -> tuple[bool, str]:
    """Determine if a user message is a command (requiring execution) vs a question.

    Returns:
        (is_command, action_type): whether this is a command and the action type.
    """
    if not user_message:
        return False, ""
    lower = user_message.lower().strip()
    first_word = lower.split()[0] if lower.split() else ""
    
    # Questions: starts with question word or ends with ?
    if lower.endswith("?"):
        return False, "question"
    if first_word in {"what", "who", "where", "when", "why", "how", "is", "are", "can", "could", "would", "do", "does", "did", "will"}:
        return False, "question"
    # "tell me", "explain", "show me" = questions
    for q in ["tell me", "explain", "show me", "list", "find", "search"]:
        if lower.startswith(q):
            return False, "question"
    
    # Commands: start with a command keyword
    if first_word in _COMMAND_KEYWORDS:
        return True, first_word
    
    # Greetings = not commands
    if first_word in {"hello", "hi", "hey", "greetings", "thanks", "thank"}:
        return False, "greeting"
    
    # Short general phrases treated as conversational
    if len(lower.split()) <= 2:
        return False, "conversational"
    
    return False, "unknown"


def create_execution_for_command(
    user_message: str,
    ai_response: str,
    conversation_id: Optional[str] = None,
    message_id: Optional[str] = None,
    tenant_id: int = 0,
    identity_id: str = "",
) -> dict:
    """Create Outcome + ExecutionLog for a meaningful AI command.

    Returns a dict with outcome_id, execution_id, and task_id (or None).
    """
    from app import db
    from app.execution.models import Outcome
    from app.execution_log.models import log_execution

    outcome_id = f"out_{uuid.uuid4().hex[:12]}"
    
    now = datetime.now(timezone.utc)
    state = {
        "stage": "accepted",
        "context": {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "tenant_id": tenant_id,
            "identity_id": identity_id,
        },
        "ai_response": user_message[:80],
        "source": "ai_chat",
    }
    
    outcome = Outcome(
        outcome_id=outcome_id,
        identity_id=str(identity_id or tenant_id or 0),
        intention=user_message[:500],
        state=state,
        created_at=now,
        updated_at=now,
    )
    db.session.add(outcome)
    db.session.flush()
    
    # Log execution
    log_execution(
        object_id=outcome.id,
        event_type="command_created",
        payload={
            "outcome_id": outcome_id,
            "intention": user_message[:200],
            "conversation_id": conversation_id,
            "message_id": message_id,
            "tenant_id": tenant_id,
            "source": "ai_chat",
        },
    )
    
    # Try to create a task
    task_id = None
    try:
        from app.models import Task
        intent_preview = user_message[:80]
        task = Task(
            title=intent_preview,
            description=user_message[:500],
            status="in_progress",
            assigned_to=str(identity_id) if identity_id else None,
            source="ai_chat",
            source_id=outcome_id,
        )
        db.session.add(task)
        db.session.flush()
        task_id = task.id
        
        # Log task creation
        log_execution(
            object_id=task.id,
            event_type="task_created",
            payload={
                "outcome_id": outcome_id,
                "task_id": task_id,
                "conversation_id": conversation_id,
            },
        )
    except Exception as e:
        logger.warning(f"Could not create task for command: {e}")
    
    db.session.commit()
    
    # Store in runtime memory for later retrieval
    try:
        from core.intelligence_runtime.integration import store_memory
        from core.intelligence_runtime.types import MemoryType
        store_memory(
            key=f"command_{outcome_id}",
            content=f"AI command: {user_message[:200]}",
            source="ai_chat",
        )
        # Also store in short-term so memory API (which reads short_term by default) can find it
        try:
            from core.intelligence_runtime import get_runtime
            runtime = get_runtime()
            runtime.memory.store(
                key=f"command_{outcome_id}",
                content=f"AI command: {user_message[:200]}",
                memory_type=MemoryType.SHORT_TERM,
                source="ai_chat",
            )
            runtime.memory.store(
                key=f"outcome_{outcome_id}",
                content=f"Outcome: {user_message[:100]} → Status: accepted",
                memory_type=MemoryType.SHORT_TERM,
                source="execution",
            )
            if task_id:
                runtime.memory.store(
                    key=f"task_{task_id}",
                    content=f"Task created: {user_message[:100]}",
                    memory_type=MemoryType.SHORT_TERM,
                    source="execution",
                )
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"Could not store in runtime memory: {e}")
    
    return {
        "outcome_id": outcome_id,
        "execution_id": outcome_id,
        "task_id": task_id,
        "drilldown": f"/api/v1/outcomes/{outcome_id}",
    }