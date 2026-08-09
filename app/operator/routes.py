"""Operator API — human-facing control surface for the SHUNYA runtime."""

from datetime import datetime, timezone

from flask import jsonify, request, send_from_directory
import os

from app import db
from app.objects.models import Object
from app.models import Task, TaskList
from app.observations.models import Observation
from app.execution.models import Outcome
from app.runtime.loop import run_cycle
from app.runtime.decision_engine import get_next_action
from app.execution_engine.engine import execute_action
from . import operator_bp


_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "operator")


@operator_bp.route("/")
def operator_index():
    """Serve the operator frontend."""
    return send_from_directory(_FRONTEND_DIR, "index.html")


def _serialize(obj):
    """Convert a SQLAlchemy model to a plain dict."""
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.replace(tzinfo=timezone.utc).isoformat()
        d[col.name] = val
    return d


# ---------------------------------------------------------------------------
# 1. List all entities
# ---------------------------------------------------------------------------


@operator_bp.route("/entities", methods=["GET"])
def list_entities():
    """Return all entities with id, type, state, last_updated."""
    entities = Object.query.order_by(Object.id).all()
    return jsonify({
        "entities": [
            {
                "id": e.id,
                "type": e.object_type,
                "state": e.state,
                "last_updated": e.updated_at.replace(tzinfo=timezone.utc).isoformat()
                if e.updated_at else None,
            }
            for e in entities
        ]
    })


# ---------------------------------------------------------------------------
# 2. Single entity detail
# ---------------------------------------------------------------------------


@operator_bp.route("/entity/<int:entity_id>", methods=["GET"])
def entity_detail(entity_id):
    """Return entity + related tasks + observations + outcomes."""
    entity = db.session.get(Object, entity_id)
    if entity is None:
        return jsonify({"error": "Entity not found"}), 404

    # Tasks linked by entity_id or lead_id
    tasks = Task.query.filter_by(entity_id=entity_id).order_by(Task.id).all()

    # Observations by entity_id
    observations = Observation.query.filter_by(entity_id=entity_id).order_by(Observation.id).all()

    # Outcomes
    outcomes = Outcome.query.order_by(Outcome.id).all()

    return jsonify({
        "entity": _serialize(entity),
        "tasks": [_serialize(t) for t in tasks],
        "observations": [_serialize(o) for o in observations],
        "outcomes": [o.to_dict() for o in outcomes],
    })


# ---------------------------------------------------------------------------
# 3. Execute action
# ---------------------------------------------------------------------------


@operator_bp.route("/action", methods=["POST"])
def execute_operator_action():
    """Execute a manual action on an entity."""
    data = request.get_json(silent=True) or {}
    entity_id = data.get("entity_id")
    action_type = data.get("action_type", "")
    payload = data.get("payload", {})

    if not entity_id:
        return jsonify({"error": "entity_id is required"}), 400

    entity = db.session.get(Object, entity_id)
    if entity is None:
        return jsonify({"error": "Entity not found"}), 404

    try:
        result = None

        if action_type == "run_decision":
            action = get_next_action(entity)
            if action.get("type") != "noop":
                execute_action(entity, action)
                db.session.commit()
                result = {"action_taken": action, "state": entity.state}
            else:
                result = {"action_taken": None, "note": "noop", "state": entity.state}

        elif action_type == "create_task":
            title = payload.get("title", f"Task for entity #{entity_id}")
            tl = TaskList.query.filter_by(name="Operator").first()
            if not tl:
                tl = TaskList(name="Operator", created_by="operator")
                db.session.add(tl)
                db.session.flush()
            task = Task(
                task_list_id=tl.id,
                entity_id=entity_id,
                title=title,
                description=payload.get("description", ""),
                status=payload.get("status", "pending"),
            )
            db.session.add(task)
            db.session.commit()
            result = {"task": _serialize(task)}

        elif action_type == "mark_done":
            state = dict(entity.state or {})
            state["status"] = "completed"
            state["completed_at"] = datetime.now(timezone.utc).isoformat()
            if payload:
                state.update(payload)
            entity.state = state
            db.session.commit()
            result = {"state": entity.state}

        elif action_type == "run_cycle":
            summary = run_cycle()
            result = {"summary": summary}

        else:
            return jsonify({"error": f"Unknown action_type: {action_type}"}), 400

        return jsonify({"success": True, "result": result})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500