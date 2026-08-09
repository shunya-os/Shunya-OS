"""ACTIVATION-04: Effect Execution Engine.

Pure dispatch layer — every effect type routes to its adapter,
result is persisted for traceability.

Architecture:
    decision_engine → effects list  →  execute_effect(effect)  →  adapter.send()
                                      →  result stored in Observation / logs
"""

import json
import logging
from datetime import datetime, timezone

from app import db
from app.adapters import whatsapp_adapter
from app.adapters import email_adapter
from app.communication.logger import log_communication
from app.execution_log.models import log_execution

logger = logging.getLogger(__name__)


def execute_effect(effect: dict, entity_id: int = None) -> dict:
    """Execute a single effect via the correct adapter.

    Returns result dict with status (sent|created|logged|skipped|failed).
    Results are persisted to ExecutionLog for traceability.
    """
    etype = effect.get("type", "")

    handlers = {
        "whatsapp": _handle_whatsapp,
        "email": _handle_email,
        "task": _handle_task,
        "log": _handle_log,
    }

    handler = handlers.get(etype)
    if not handler:
        logger.warning("Unknown effect type: %s", etype)
        result = {"status": "skipped", "type": etype, "reason": "unknown_type"}
    else:
        try:
            result = handler(effect)
        except Exception as e:
            logger.error("Effect handler crashed: %s — %s", etype, e)
            result = {"status": "failed", "type": etype, "error": str(e)}

    # Persist execution trace (ACTIVATION-04: mandatory traceability)
    log_execution(
        entity_id or 0,
        "EFFECT",
        {
            "type": etype,
            "effect": effect,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    print(f"[EFFECT] {etype}: {json.dumps({'status': result.get('status'), 'entity_id': entity_id})}")

    return result


def execute_effects(effects: list, entity_id: int = None) -> list:
    """Execute a batch of effects. Each is independent — one failure never blocks another."""
    results = []
    for effect in effects:
        result = execute_effect(effect, entity_id)
        results.append(result)
    return results


# ── Handler implementations ──


def _handle_whatsapp(effect: dict) -> dict:
    """Route WhatsApp effects to the WhatsApp adapter."""
    return whatsapp_adapter.send(effect)


def _handle_email(effect: dict) -> dict:
    """Route email effects to the Email adapter."""
    return email_adapter.send(effect)


def _handle_task(effect: dict) -> dict:
    """Create a task from an effect dict.

    Effect format: {"type": "task", "title": "...", "description": "..."}
    """
    from app.models import Task

    title = effect.get("title", effect.get("task", "Auto Task"))
    description = effect.get("description", "")

    try:
        task = Task(title=title, status="pending")
        if description:
            task.description = description
        db.session.add(task)
        db.session.commit()
        logger.info("Task created: %s (#%d)", title, task.id)
        print(f"[TASK CREATED] #{task.id}: {title}")
        return {"status": "created", "task_id": task.id, "title": title}
    except Exception as e:
        db.session.rollback()
        logger.error("Task creation failed: %s", e)
        return {"status": "failed", "error": str(e)}


def _handle_log(effect: dict) -> dict:
    """Record a log communication entry."""
    channel = effect.get("channel", "system")
    message = effect.get("message", "")
    log_communication(channel, "system", message)
    print(f"[EFFECT LOG] {channel}: {message}")
    return {"status": "logged", "channel": channel, "message": message}