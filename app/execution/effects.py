"""ACTIVATION-08B: Effect Execution Engine — creates proposals, never sends directly.

ACTIVATION-04 → ACTIVATION-08B migration:
Every outbound effect (whatsapp, email) creates a MessageProposal instead of
sending directly. The human must approve before any message goes out.

Constitutional rule: Shunya proposes. Only human disposes.
NO EXCEPTIONS.

Task and log effects remain internal (no human approval needed).
"""

import json
import logging
from app.core.time import now

from app import db
from app.communication.models import MessageProposal
from app.communication.logger import log_communication
from app.execution_log.models import log_execution

logger = logging.getLogger(__name__)


def _proposal_exists(entity_id: int, message_snippet: str) -> bool:
    """Check if a pending proposal already exists for this entity + message intent.

    Prevents duplicate proposals across loop cycles for the same entity.
    Only checks pending proposals — already-approved/sent/rejected proposals
    are considered consumed and do not block new ones.
    """
    if not entity_id:
        return False
    existing = (
        MessageProposal.query
        .filter_by(entity_id=entity_id, status="pending")
        .order_by(MessageProposal.id.desc())
        .first()
    )
    if existing and message_snippet and existing.message == message_snippet:
        return True
    # Also flag if ANY pending proposal exists for this entity — prevents
    # stacking multiple pending proposals for the same entity in one cycle
    if existing:
        return True
    return False


def create_proposal(
    to: str,
    message: str,
    entity_id: int = None,
    entity_type: str = None,
    entity_name: str = None,
    context_reason: str = "AI-generated proposal",
    context_source: str = "effect_engine",
    context_priority: str = "high",
    context_confidence: str = "high",
) -> MessageProposal:
    """Create a MessageProposal. This is the ONLY path for outbound messages.

    Args:
        to: Recipient identifier (phone number, email address).
        message: Message content.
        entity_id: Optional entity/object ID for association.
        entity_type: Optional entity type.
        entity_name: Optional human-readable entity name.
        context_reason: Why this proposal exists (shown to human).
        context_source: Origin of the proposal.
        context_priority: Priority level for the human inbox.
        context_confidence: Confidence level.

    Returns:
        The created MessageProposal, or None if a duplicate was prevented.
    """
    # Deduplicate: skip if pending proposal already exists for this entity
    if entity_id and _proposal_exists(entity_id, message):
        logger.info("Duplicate proposal prevented for entity_id=%d", entity_id)
        return None

    proposal = MessageProposal(
        to=to,
        message=message,
        entity_id=entity_id,
        entity_type=entity_type,
        entity_name=entity_name,
        context_reason=context_reason,
        context_source=context_source,
        context_priority=context_priority,
        context_confidence=context_confidence,
    )
    db.session.add(proposal)
    db.session.flush()

    log_execution(
        entity_id or 0,
        "PROPOSAL_CREATED",
        {
            "to": to,
            "message_preview": message[:100],
            "reason": context_reason,
            "proposal_id": proposal.id,
        },
    )

    logger.info("Proposal #%d created: -> %s", proposal.id, to)
    print(f"[PROPOSAL] #{proposal.id} -> {to}: {message[:80]}...")

    # PHASE 2A: Evidence log for proposal creation
    try:
        from app.evidence.service import log_evidence
        log_evidence(
            action="create_proposal",
            source=context_source,
            confidence=0.92 if context_confidence == "high" else (0.65 if context_confidence == "medium" else 0.35),
            evidence_type="proposal",
            entity_id=entity_id,
            inputs={
                "to": to,
                "reason": context_reason,
                "message_preview": message[:100],
            },
            outputs={
                "proposal_id": proposal.id,
                "status": "pending",
            },
        )
    except Exception:
        pass

    # PHASE 2C: Cortex observation for proposal
    try:
        from app.intelligence.cortex_bridge import observe_proposal
        observe_proposal(
            proposal_id=proposal.id,
            entity_id=entity_id,
            source=context_source,
            reason=context_reason,
        )
    except Exception:
        pass

    return proposal


def execute_effect(effect: dict, entity_id: int = None) -> dict:
    """Execute a single effect. Outbound types create proposals; internal types dispatch.

    Returns result dict with status (proposal_created|created|logged|skipped|failed).
    """
    etype = effect.get("type", "")

    handlers = {
        "whatsapp": _handle_proposal_whatsapp,
        "email": _handle_proposal_email,
        "task": _handle_task,
        "log": _handle_log,
    }

    handler = handlers.get(etype)
    if not handler:
        logger.warning("Unknown effect type: %s", etype)
        result = {"status": "skipped", "type": etype, "reason": "unknown_type"}
    else:
        try:
            result = handler(effect, entity_id)
        except Exception as e:
            logger.error("Effect handler crashed: %s — %s", etype, e)
            result = {"status": "failed", "type": etype, "error": str(e)}

    # Persist execution trace
    log_execution(
        entity_id or 0,
        "EFFECT",
        {
            "type": etype,
            "effect": effect,
            "result": result,
            "timestamp": now().isoformat(),
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


# ── Proposal-based handlers (outbound communication) ──


def _handle_proposal_whatsapp(effect: dict, entity_id: int = None) -> dict:
    """Convert a WhatsApp effect into a MessageProposal — NEVER sends directly."""
    to = effect.get("to", "")
    message = effect.get("message", "")
    if not to or not message:
        return {"status": "skipped", "reason": "missing to/message"}

    # Use decision metadata from action if available
    decision_source = effect.get("decision_source", "effect_engine")
    decision_confidence = effect.get("decision_confidence", "high")

    proposal = create_proposal(
        to=to,
        message=message,
        entity_id=entity_id,
        entity_type="entity",
        entity_name=effect.get("name", ""),
        context_reason="Proposed outreach via WhatsApp",
        context_source=decision_source,
        context_priority="high",
        context_confidence=decision_confidence,
    )

    if proposal is None:
        return {"status": "duplicate_prevented", "reason": "pending proposal exists"}
    return {"status": "proposal_created", "proposal_id": proposal.id, "channel": "whatsapp"}


def _handle_proposal_email(effect: dict, entity_id: int = None) -> dict:
    """Convert an Email effect into a MessageProposal — NEVER sends directly."""
    to = effect.get("to", "")
    subject = effect.get("subject", "Update from SHUNYA")
    body = effect.get("body", effect.get("message", ""))
    message = f"Subject: {subject}\n\n{body}"

    if not to or not body:
        return {"status": "skipped", "reason": "missing to/body"}

    # Use decision metadata from action if available
    decision_source = effect.get("decision_source", "effect_engine")
    decision_confidence = effect.get("decision_confidence", "high")

    proposal = create_proposal(
        to=to,
        message=message,
        entity_id=entity_id,
        entity_type="entity",
        entity_name=effect.get("name", ""),
        context_reason=f"Email outreach: {subject}",
        context_source=decision_source,
        context_priority="high",
        context_confidence=decision_confidence,
    )

    if proposal is None:
        return {"status": "duplicate_prevented", "reason": "pending proposal exists"}
    return {"status": "proposal_created", "proposal_id": proposal.id, "channel": "email"}


# ── Internal handlers (no human approval needed) ──


def _handle_task(effect: dict, entity_id: int = None) -> dict:
    """Create a task from an effect dict — internal operation, no proposal needed.

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
        db.session.flush()
        logger.info("Task created: %s (#%d)", title, task.id)
        print(f"[TASK CREATED] #{task.id}: {title}")
        return {"status": "created", "task_id": task.id, "title": title}
    except Exception as e:
        db.session.rollback()
        logger.error("Task creation failed: %s", e)
        return {"status": "failed", "error": str(e)}


def _handle_log(effect: dict, entity_id: int = None) -> dict:
    """Record a log communication entry — internal only."""
    channel = effect.get("channel", "system")
    message = effect.get("message", "")
    log_communication(channel, "system", message)
    print(f"[EFFECT LOG] {channel}: {message}")
    return {"status": "logged", "channel": channel, "message": message}