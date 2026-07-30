"""UBME API Routes — REST endpoints for module management and universal object CRUD.

No business-specific logic exists here — all routes operate on metadata.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone

from flask import jsonify, request, session

from app.ubme import ubme_bp
from app.ubme import engine as ubme_engine

logger = logging.getLogger(__name__)
from app.ubme.models import (
    BusinessTemplate, FieldDef, FieldType, ModuleDef, NavigationEntry,
    ObjectTypeDef, ViewDef, ViewType, WorkflowDef, WorkflowStateDef,
    WorkflowStateType, WorkflowTransitionDef,
)

# ── Load built-in templates on module import ──────────────────────────────

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


def _load_builtin_templates() -> None:
    """Load all JSON template files from the templates directory."""
    if not os.path.isdir(_TEMPLATES_DIR):
        return
    for fname in sorted(os.listdir(_TEMPLATES_DIR)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(_TEMPLATES_DIR, fname)
        try:
            with open(fpath) as f:
                data = json.load(f)
            template = BusinessTemplate.from_dict(data)
            ubme_engine.register_template(template)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "Failed to load template %s: %s", fname, exc
            )


_load_builtin_templates()


# ── Helpers ────────────────────────────────────────────────────────────────

def _auth_org_id() -> str | None:
    """Get the current organization ID from session."""
    return session.get("current_org_id") or session.get("org_id")


def _require_auth():
    """Ensure user is authenticated. Returns error response or None."""
    user_id = session.get("user_id") or session.get("identity_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401
    return None


# ── Module Management ──────────────────────────────────────────────────────


@ubme_bp.route("/modules", methods=["GET"])
def list_modules():
    """List all installed modules with basic info."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    modules = ubme_engine.list_modules()
    return jsonify({
        "data": [m.to_dict() for m in modules],
        "count": len(modules),
    })


@ubme_bp.route("/modules", methods=["POST"])
def create_module():
    """Create a new module from Module Builder data."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    if not data.get("key") or not data.get("name"):
        return jsonify({"error": "key and name are required"}), 400

    module = ModuleDef.from_dict(data)
    ubme_engine.register_module(module)

    # Auto-generate navigation
    if not module.navigation:
        module.navigation = ubme_engine.generate_navigation(module)

    return jsonify({"status": "created", "module": module.to_dict()}), 201


@ubme_bp.route("/modules/<module_key>", methods=["GET"])
def get_module(module_key: str):
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    module = ubme_engine.get_module(module_key)
    if not module:
        return jsonify({"error": "Module not found"}), 404
    return jsonify({"data": module.to_dict()})


@ubme_bp.route("/modules/<module_key>", methods=["PUT"])
def update_module(module_key: str):
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    module = ubme_engine.get_module(module_key)
    if not module:
        return jsonify({"error": "Module not found"}), 404

    data = request.get_json(silent=True) or {}
    updated = ModuleDef.from_dict({**module.to_dict(), **data})
    updated.key = module_key  # preserve key
    ubme_engine.register_module(updated)
    return jsonify({"status": "updated", "module": updated.to_dict()})


@ubme_bp.route("/modules/<module_key>", methods=["DELETE"])
def delete_module(module_key: str):
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    ok = ubme_engine.delete_module(module_key)
    if not ok:
        return jsonify({"error": "Module not found"}), 404
    return jsonify({"status": "deleted"})


# ── Template Management ────────────────────────────────────────────────────


@ubme_bp.route("/templates", methods=["GET"])
def list_templates():
    """List available business templates for installation."""
    templates = ubme_engine.list_templates()
    return jsonify({
        "data": [t.to_dict() for t in templates],
        "count": len(templates),
    })


@ubme_bp.route("/modules/<module_key>/install", methods=["POST"])
def install_template(module_key: str):
    """Install a template — create a new module from predefined template."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    template_id = data.get("template_id", module_key)
    module = ubme_engine.install_template(template_id)
    if not module:
        return jsonify({"error": f"Template '{template_id}' not found"}), 404

    # Regenerate navigation
    module.navigation = ubme_engine.generate_navigation(module)
    ubme_engine.register_module(module)

    return jsonify({"status": "installed", "module": module.to_dict()}), 201


# ── Object Type Registry ───────────────────────────────────────────────────


@ubme_bp.route("/types", methods=["GET"])
def list_types():
    """List all registered object types across all modules."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    types = ubme_engine.get_all_object_types()
    result = {}
    for mod_key, ot in types:
        if mod_key not in result:
            result[mod_key] = []
        result[mod_key].append(ot.to_dict())
    return jsonify({"data": result})


@ubme_bp.route("/types/<type_key>", methods=["GET"])
def get_type(type_key: str):
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    found = ubme_engine.find_type_for_object_type(type_key)
    if not found:
        return jsonify({"error": "Object type not found"}), 404

    mod_key, ot = found
    return jsonify({"data": ot.to_dict(), "module_key": mod_key})


# ── Object Instance CRUD ───────────────────────────────────────────────────


@ubme_bp.route("/data/<object_type>", methods=["GET"])
def list_objects(object_type: str):
    """List all instances of a given object type."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    found = ubme_engine.find_type_for_object_type(object_type)
    if not found:
        return jsonify({"error": f"Object type '{object_type}' not found"}), 404

    mod_key, _ot = found
    instances = ubme_engine.list_instances(mod_key, object_type)
    return jsonify({
        "data": instances,
        "count": len(instances),
        "module_key": mod_key,
    })


@ubme_bp.route("/data/<object_type>", methods=["POST"])
def create_object(object_type: str):
    """Create a new object instance."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    found = ubme_engine.find_type_for_object_type(object_type)
    if not found:
        return jsonify({"error": f"Object type '{object_type}' not found"}), 404

    mod_key, _ot = found
    data = request.get_json(silent=True) or {}
    instance = ubme_engine.create_instance(mod_key, object_type, data)
    if not instance:
        return jsonify({"error": "Failed to create instance"}), 500

    return jsonify({"status": "created", "data": instance}), 201


@ubme_bp.route("/data/<object_type>/<instance_id>", methods=["GET"])
def get_object(object_type: str, instance_id: str):
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    found = ubme_engine.find_type_for_object_type(object_type)
    if not found:
        return jsonify({"error": f"Object type '{object_type}' not found"}), 404

    mod_key, _ot = found
    instance = ubme_engine.get_instance(mod_key, object_type, instance_id)
    if not instance:
        return jsonify({"error": "Instance not found"}), 404

    return jsonify({"data": instance})


@ubme_bp.route("/data/<object_type>/<instance_id>", methods=["PUT"])
def update_object(object_type: str, instance_id: str):
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    found = ubme_engine.find_type_for_object_type(object_type)
    if not found:
        return jsonify({"error": f"Object type '{object_type}' not found"}), 404

    mod_key, _ot = found
    data = request.get_json(silent=True) or {}
    instance = ubme_engine.update_instance(mod_key, object_type, instance_id, data)
    if not instance:
        return jsonify({"error": "Instance not found"}), 404

    return jsonify({"status": "updated", "data": instance})


@ubme_bp.route("/data/<object_type>/<instance_id>", methods=["DELETE"])
def delete_object(object_type: str, instance_id: str):
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    found = ubme_engine.find_type_for_object_type(object_type)
    if not found:
        return jsonify({"error": f"Object type '{object_type}' not found"}), 404

    mod_key, _ot = found
    ok = ubme_engine.delete_instance(mod_key, object_type, instance_id)
    if not ok:
        return jsonify({"error": "Instance not found"}), 404

    return jsonify({"status": "deleted"})


# ── Actions ──────────────────────────────────────────────────────────────────


@ubme_bp.route("/actions/<object_type>", methods=["GET"])
def get_actions(object_type: str):
    """Get available actions for an object type."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    found = ubme_engine.find_type_for_object_type(object_type)
    if not found:
        return jsonify({"error": f"Object type '{object_type}' not found"}), 404

    _mod_key, ot = found
    actions = ot.actions or []
    return jsonify({
        "data": [a.to_dict() for a in actions],
        "count": len(actions),
    })


# ── Dashboard ────────────────────────────────────────────────────────────────


@ubme_bp.route("/dashboard/<module_key>", methods=["GET"])
def get_dashboard(module_key: str):
    """Get generated dashboard cards for a module."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    module = ubme_engine.get_module(module_key)
    if not module:
        return jsonify({"error": "Module not found"}), 404

    cards = module.dashboard_cards or []
    card_data = []
    for card in cards:
        result = _resolve_dashboard_card(card, module.key)
        card_data.append(result)

    return jsonify({"data": card_data, "count": len(card_data)})


def _resolve_dashboard_card(card, module_key: str) -> dict:
    """Resolve a dashboard card against live instance data."""
    base = card.to_dict()
    try:
        instances = ubme_engine.list_instances(module_key, card.object_type)
        if card.card_type == "count":
            if card.filter_criteria:
                m = re.match(r"(\w+)\s*==\s*['\"]?(.+?)['\"]?\s*$", card.filter_criteria)
                if m:
                    field, val = m.groups()
                    filtered = [i for i in instances if i.get("data", {}).get(field) == val]
                    base["value"] = len(filtered)
                else:
                    base["value"] = len(instances)
            else:
                base["value"] = len(instances)
        elif card.card_type == "sum" and card.field:
            total = sum(i.get("data", {}).get(card.field, 0) or 0 for i in instances)
            base["value"] = round(total, 2)
        elif card.card_type == "recent":
            sorted_instances = sorted(instances, key=lambda i: i.get("created_at", ""), reverse=True)
            base["value"] = [{"id": i["id"], "name": i.get("name", ""), "status": i.get("status", "")} for i in sorted_instances[:5]]
        elif card.card_type == "alert":
            if card.filter_criteria:
                m = re.match(r"(\w+)\s*==\s*['\"]?(.+?)['\"]?\s*$", card.filter_criteria)
                if m:
                    field, val = m.groups()
                    filtered = [i for i in instances if i.get("data", {}).get(field) == val]
                    base["value"] = len(filtered)
                else:
                    base["value"] = len(instances)
            else:
                base["value"] = len(instances)
        else:
            base["value"] = len(instances)
    except Exception:
        base["value"] = 0
    return base


# ── Views ───────────────────────────────────────────────────────────────────


@ubme_bp.route("/views/<object_type>", methods=["GET"])
def get_views(object_type: str):
    """Get compatible views for an object type."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    found = ubme_engine.find_type_for_object_type(object_type)
    if not found:
        return jsonify({"error": f"Object type '{object_type}' not found"}), 404

    _mod_key, ot = found
    views = ubme_engine.generate_views(ot, _mod_key)
    return jsonify({
        "data": [v.to_dict() for v in views],
        "count": len(views),
    })


# ── Navigation ──────────────────────────────────────────────────────────────


@ubme_bp.route("/navigation", methods=["GET"])
def get_navigation():
    """Get dynamic navigation from all installed modules."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    modules = ubme_engine.list_modules()
    nav = {}
    for module in modules:
        entries = module.navigation or ubme_engine.generate_navigation(module)
        nav[module.key] = {
            "name": module.name,
            "icon": module.icon,
            "color": module.color,
            "entries": [n.to_dict() for n in entries],
        }
    return jsonify({"data": nav})


# ── Business Discovery ──────────────────────────────────────────────────────


@ubme_bp.route("/discover", methods=["POST"])
def discover_business():
    """Generate a complete business module from a natural language description.

    Body: {"description": "I run a dental clinic", "business_name": "My Clinic"}
    Returns: {"status": "generated", "module": {...}}
    """
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    description = data.get("description", "")
    business_name = data.get("business_name", "")

    if not description:
        return jsonify({"error": "description is required"}), 400

    try:
        from app.ubme.discovery import generate_module_from_description
        result = generate_module_from_description(description, business_name)
        return jsonify({
            "status": "generated",
            "module": result,
            "generated_type": "ai" if "via_lm" in str(type(result)) else "rule",
        })
    except Exception as e:
        logger.exception("Discovery failed")
        return jsonify({"error": f"Discovery failed: {e}"}), 500


@ubme_bp.route("/discover/confirm", methods=["POST"])
def confirm_discovered_module():
    """Confirm the generated module and install it.

    Body: {"module": {...}  (the ModuleDef dict from discover)}
    Returns: {"status": "installed", "module": {...}}
    """
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    module_data = data.get("module")
    if not module_data:
        return jsonify({"error": "module data required"}), 400

    try:
        from app.ubme.models import ModuleDef
        module = ModuleDef.from_dict(module_data)
        if not module.navigation:
            module.navigation = ubme_engine.generate_navigation(module)
        ubme_engine.register_module(module)
        return jsonify({"status": "installed", "module": module.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": f"Installation failed: {e}"}), 500


# ── AI Semantics ────────────────────────────────────────────────────────────


@ubme_bp.route("/semantics", methods=["GET"])
def get_ai_semantics():
    """Expose all object type semantics for the Intelligence Runtime."""
    auth_err = _require_auth()
    if auth_err:
        return auth_err

    types = ubme_engine.get_all_object_types()
    semantics = []
    for mod_key, ot in types:
        semantics.append({
            "module": mod_key,
            "object_type": ot.key,
            "name": ot.name,
            "plural_name": ot.plural_name,
            "description": ot.description,
            "fields": [
                {
                    "key": f.key,
                    "label": f.label,
                    "type": f.field_type.value if hasattr(f.field_type, 'value') else str(f.field_type),
                    "searchable": f.searchable,
                }
                for f in (ot.fields or [])
            ],
            "ai_semantics": ot.ai_semantics or {},
        })
    return jsonify({"data": semantics})