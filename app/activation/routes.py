"""ACTIVATION-01 API routes — bridge between UI and engine."""

from datetime import datetime, timezone

from flask import jsonify, request, send_from_directory
import os

from app import db
from app.objects.models import Object
from app.models import Task, TaskList
from app.runtime.loop import run_cycle
from app.runtime.decision_engine import get_next_action
from app.execution_engine.engine import execute_action
from . import activation_bp


_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "app")


@activation_bp.route("/")
def activation_index():
    """Serve the ACTIVATION-01 frontend."""
    return send_from_directory(_FRONTEND_DIR, "index.html")


def _serialize(obj):
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.replace(tzinfo=timezone.utc).isoformat()
        d[col.name] = val
    return d


# ── List all entities ──


@activation_bp.route("/entities", methods=["GET"])
def list_entities():
    entities = Object.query.order_by(Object.id).all()
    return jsonify({
        "entities": [
            {"id": e.id, "type": e.object_type, "state": e.state,
             "last_updated": e.updated_at.replace(tzinfo=timezone.utc).isoformat()
             if e.updated_at else None}
            for e in entities
        ]
    })


# ── Create entity ──


@activation_bp.route("/entities", methods=["POST"])
def create_entity():
    data = request.get_json(silent=True) or {}
    entity = Object(
        object_type=data.get("type", "lead"),
        state=data.get("state", {}),
        context=data.get("context", {}),
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify({"entity": {"id": entity.id, "type": entity.object_type, "state": entity.state}}), 201


# ── Get single entity ──


@activation_bp.route("/entities/<int:entity_id>", methods=["GET"])
def get_entity(entity_id):
    entity = db.session.get(Object, entity_id)
    if not entity:
        return jsonify({"error": "Not found"}), 404
    tasks = Task.query.filter_by(entity_id=entity_id).order_by(Task.id).all()
    return jsonify({
        "entity": _serialize(entity),
        "tasks": [_serialize(t) for t in tasks],
    })


# ── Execute action on entity ──


@activation_bp.route("/entities/<int:entity_id>/action", methods=["POST"])
def entity_action(entity_id):
    data = request.get_json(silent=True) or {}
    action_type = data.get("action", "")
    payload = data.get("payload", {})

    entity = db.session.get(Object, entity_id)
    if not entity:
        return jsonify({"error": "Not found"}), 404

    try:
        if action_type == "run_decision":
            action = get_next_action(entity)
            if action.get("type") != "noop":
                execute_action(entity, action)
                db.session.commit()
            return jsonify({"action": action, "state": entity.state})

        elif action_type == "add_task":
            title = payload.get("title", "Task")
            tl = TaskList.query.filter_by(name="Activation").first()
            if not tl:
                tl = TaskList(name="Activation", created_by="system")
                db.session.add(tl)
                db.session.flush()
            task = Task(task_list_id=tl.id, entity_id=entity_id, title=title,
                        description=payload.get("description", ""), status="pending")
            db.session.add(task)
            db.session.commit()
            return jsonify({"task": _serialize(task)}), 201

        elif action_type == "update_state":
            merged = dict(entity.state or {})
            merged.update(payload)
            entity.state = merged
            db.session.commit()
            return jsonify({"state": entity.state})

        else:
            return jsonify({"error": f"Unknown action: {action_type}"}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ── Run loop ──


@activation_bp.route("/loop/run", methods=["POST"])
def run_loop_once():
    try:
        summary = run_cycle()
        return jsonify({"summary": summary})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500