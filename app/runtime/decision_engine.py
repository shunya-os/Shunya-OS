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