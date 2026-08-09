"""Decision Engine — pure intelligence, returns next action for an object.

Supports multi-field payload evolution and structural multi-object intelligence.
No business assumptions — only structure, not meaning.

PROD-12: Single-link interaction (foundation).
An object may reference one other object via its `linked_to` state field.
When the referenced object reaches version 2, the linking object is synced.

PROD-13: Full object graph awareness.
An object may declare multiple structural relations:
    {
        "relations": [
            {"type": "depends_on", "target_id": 12},
            {"type": "blocks", "target_id": 15}
        ]
    }
Each relation is resolved when its target object reaches version 2.
Resolved relations accumulate in `resolved_relations` (non-destructive).
Once all declared relations are resolved, the object itself progresses to
version 2 so downstream objects can depend on it — graph propagation.

Relations are pure structure: {type, target_id}. No business meaning.
"""

from app.objects.models import Object
from app.commitments.models import Commitment
from app.observations.models import Observation
from app.models import Task
from app.communication.email import send_email
from app.communication.whatsapp import send_whatsapp
from app.communication.logger import log_communication


def build_context(entity):
    """Build a decision context dict for a lead/entity."""
    return {
        "state": getattr(entity, "stage", None),
        "outcome": getattr(entity, "outcome", None),
        "tasks": [],
        "observations": []
    }


def get_next_action(obj) -> dict:
    """Decide the next action for an object based purely on its state.

    Args:
        obj: Object instance with .state dict.

    Returns:
        update with payload if state progression needed.
        noop if state is fully evolved.
    """
    state = obj.state or {}

    if not state:
        return {
            "type": "update",
            "payload": {
                "initialized": True,
                "version": 1
            }
        }

    # PROD-13 — structural multi-object graph awareness.
    # Resolve every declared relation whose target has reached version 2.
    # resolved_relations accumulates across cycles (non-destructive).
    if state.get("relations"):
        resolved = set(state.get("resolved_relations") or [])
        newly = []
        for rel in state["relations"]:
            if not isinstance(rel, dict):
                continue
            target_id = rel.get("target_id")
            if target_id is None or target_id in resolved:
                continue
            target = Object.query.get(target_id)
            if target is not None and (target.state or {}).get("version") == 2:
                newly.append(target_id)

        if newly:
            accumulated = sorted(resolved | set(newly))
            return {
                "type": "update",
                "payload": {
                    "resolved_relations": accumulated
                }
            }

        # All declared relations resolved → progress this object to version 2
        # so downstream objects can depend on it (graph propagation).
        if not state.get("initialized"):
            return {
                "type": "update",
                "payload": {
                    "initialized": True,
                    "version": 1
                }
            }
        if state.get("version") == 1:
            return {
                "type": "update",
                "payload": {
                    "version": 2
                }
            }

    # PROD-12 — structural single-link interaction (preserved).
    # If this object references another object, and that object has reached
    # version 2, bring this object into sync. No business logic.
    if state.get("linked_to"):
        linked = Object.query.get(state["linked_to"])
        if linked is not None and (linked.state or {}).get("version") == 2:
            return {
                "type": "update",
                "payload": {
                    "synced": True
                }
            }

    if state.get("initialized") and state.get("version") == 1:
        return {
            "type": "update",
            "payload": {
                "version": 2
            }
        }

    # ACTIVATION-01: Lead flow — new → contacted → quoted → closed
    if obj.object_type == "lead":
        stage = state.get("stage", "new")
        status = state.get("status")
        phone = state.get("phone", "")
        email = state.get("email", "")
        name = state.get("name", "Customer")

        if stage == "new" and status != "contacted":
            return {
                "type": "update",
                "payload": {"stage": "contacted", "task": f"Contact {name}"},
                "effects": [
                    {"type": "log", "channel": "system", "message": f"Lead {name} moved to contacted"}
                ],
            }

        if stage == "contacted":
            task_count = Task.query.filter_by(entity_id=obj.id).count()
            if task_count == 0:
                effects = [
                    {"type": "log", "channel": "system", "message": f"Quote sent to {name}"},
                ]
                if phone:
                    effects.insert(0, {
                        "type": "whatsapp", "to": phone,
                        "message": f"Hi {name}, here is your quote! Let me know if you have questions.",
                    })
                if email:
                    effects.insert(0 if not phone else 1, {
                        "type": "email", "to": email,
                        "subject": f"Your quote, {name}",
                        "body": f"Dear {name},\n\nPlease find your quote attached.\n\nBest regards,\nSHUNYA",
                    })
                return {
                    "type": "update",
                    "payload": {"task": f"Send quote to {name}", "stage": "quoted"},
                    "effects": effects,
                }

        if stage == "quoted" and status != "closed":
            effects = [
                {"type": "log", "channel": "system", "message": f"Follow-up sent to {name}"},
            ]
            if email:
                effects.insert(0, {
                    "type": "email", "to": email,
                    "subject": f"Follow up, {name}",
                    "body": f"Hi {name},\n\nJust checking in on your quote. Let me know if you need anything.\n\nBest,\nSHUNYA",
                })
            if phone:
                effects.insert(0, {
                    "type": "whatsapp", "to": phone,
                    "message": f"Hi {name}, just following up on your quote. Let me know!",
                })
            return {
                "type": "update",
                "payload": {"task": f"Follow up with {name}", "status": "closed"},
                "effects": effects,
            }

        if stage == "closed" or status == "closed":
            return {"type": "noop"}

    return {"type": "noop"}


def decide_next_from_commitment(commitment: Commitment):
    """
    Decision based on latest observation.

    Returns:
        update_commitment with status=completed if latest observation
        is matched; noop otherwise.
    """
    # fetch latest observation
    obs = (
        Observation.query
        .filter_by(commitment_id=commitment.id)
        .order_by(Observation.id.desc())
        .first()
    )

    # no observation yet
    if not obs:
        return {"type": "noop"}

    # if matched → complete commitment
    if obs.status == "matched":
        return {
            "type": "update_commitment",
            "payload": {"status": "completed"}
        }

    # if deviated → mark failure
    if obs.status == "deviated":
        return {
            "type": "update_commitment",
            "payload": {"status": "failed"}
        }

    return {"type": "noop"}


def decide_lead_task(lead):
    """If a lead has no tasks, return a task creation action."""
    task_count = Task.query.filter_by(lead_id=lead.id).count()
    if task_count == 0:
        return {
            "type": "update",
            "payload": {"task": "Call customer"}
        }
    return {"type": "noop"}


def decide_lead_stage(lead):
    """Progress lead through lifecycle stages based on outcome.

    Uses build_context for unified context access.
    """
    context = build_context(lead)

    # PROD-39: multi-step decision for quoted leads
    if context["state"] == "quoted" and context["outcome"] != "closed":
        return [
            {"type": "update", "payload": {"task": "Follow up"}},
            {"type": "update", "payload": {"priority": "high"}}
        ]

    # RULE: contacted with no tasks → create "Send quote"
    if context["state"] == "contacted":
        task_count = Task.query.filter_by(lead_id=lead.id).count()
        if task_count == 0:
            return {
                "type": "update",
                "payload": {"task": "Send quote"}
            }

    if not context["outcome"]:
        return {"type": "noop"}

    if context["outcome"] == "attempted":
        if context["state"] == "new":
            return {
                "type": "update",
                "payload": {"stage": "contacted"}
            }

        if context["state"] == "contacted":
            return {
                "type": "update",
                "payload": {"stage": "quoted"}
            }

        if context["state"] == "quoted":
            return {
                "type": "update",
                "payload": {"stage": "closed"}
            }

    return {"type": "noop"}


def decide_entity(entity):
    """Generic decision for an Entity based on its state."""
    if entity.state == "new":
        return {"type": "update", "payload": {"state": "in_progress"}}
    return {"type": "noop"}


def explain_decision(entity, decision):
    return {
        "entity_id": entity.id,
        "decision": decision,
        "reason": "Derived from current state and context",
        "state": entity.state
    }
