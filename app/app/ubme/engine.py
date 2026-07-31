"""Universal Business Model Engine — core engine for metadata-driven business modules.

Supports:
- Module Registry: store, retrieve, update business module definitions
- Object Instance Store: CRUD for object instances (any type)
- Field Processor: validate and process field values by type
- View Generator: auto-generate views from object type metadata
- Template Loader: install and configure business templates
"""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from app.ubme.models import (
    BusinessTemplate, FieldDef, FieldType, ModuleDef, ObjectTypeDef,
    ViewDef, ViewType, WorkflowDef, WorkflowStateDef, WorkflowStateType,
    WorkflowTransitionDef, NavigationEntry,
)
from app.ubme.events import EventType, get_bus

# ── UUID v4 helper (for object instance IDs) ──────────────────────────────

def _generate_id() -> str:
    return f"obj_{uuid.uuid4().hex[:24]}"


# ── Module Registry ──────────────────────────────────────────────────────

_MODULES: dict[str, ModuleDef] = {}
_TEMPLATES: dict[str, BusinessTemplate] = {}


def register_module(module: ModuleDef) -> None:
    """Register or update a module definition."""
    module.updated_at = datetime.now(timezone.utc).isoformat()
    _MODULES[module.key] = module


def get_module(key: str) -> ModuleDef | None:
    return _MODULES.get(key)


def list_modules() -> list[ModuleDef]:
    return list(_MODULES.values())


def delete_module(key: str) -> bool:
    if key in _MODULES:
        del _MODULES[key]
        # Also clean up object instances for this module
        _clear_module_instances(key)
        return True
    return False


def register_template(template: BusinessTemplate) -> None:
    _TEMPLATES[template.id] = template


def list_templates() -> list[BusinessTemplate]:
    return list(_TEMPLATES.values())


def get_template(template_id: str) -> BusinessTemplate | None:
    return _TEMPLATES.get(template_id)


def install_template(template_id: str, org_id: str | None = None) -> ModuleDef | None:
    """Install a template — creates a new module from the template definition."""
    template = _TEMPLATES.get(template_id)
    if not template:
        return None
    module = deepcopy(template.module)
    module.template_source = template_id
    # Ensure unique key if module key already exists
    base_key = module.key
    counter = 1
    while base_key in _MODULES:
        base_key = f"{module.key}_{counter}"
        counter += 1
    if base_key != module.key:
        module.key = base_key
        module.name = f"{template.name} ({counter})"
    register_module(module)
    return module


# ── Object Instance Store ─────────────────────────────────────────────────

# Stores instances by (module_key, object_type) -> {id: data}
_INSTANCES: dict[str, dict[str, dict[str, Any]]] = {}
# Quick lookup by instance ID across all types
_INSTANCE_BY_ID: dict[str, dict[str, Any]] = {}


def _instance_store_key(module_key: str, object_type: str) -> str:
    return f"{module_key}:{object_type}"


def create_instance(module_key: str, object_type: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Create a new object instance. Returns the stored instance or None if type doesn't exist."""
    module = _MODULES.get(module_key)
    if not module:
        return None
    type_def = _find_object_type(module, object_type)
    if not type_def:
        return None

    instance_id = data.get("id") or _generate_id()
    now = datetime.now(timezone.utc).isoformat()

    # Process and validate fields
    processed = _process_fields(type_def, data)

    instance = {
        "id": instance_id,
        "object_type": object_type,
        "module_key": module_key,
        "name": processed.get("name", processed.get("title", "")),
        "status": processed.get("status", "active"),
        "created_at": now,
        "updated_at": now,
        "data": processed,
    }

    sk = _instance_store_key(module_key, object_type)
    if sk not in _INSTANCES:
        _INSTANCES[sk] = {}
    _INSTANCES[sk][instance_id] = instance
    _INSTANCE_BY_ID[instance_id] = instance
    
    # Emit event
    get_bus().emit(EventType.OBJECT_CREATED, module_key=module_key, object_type=object_type, instance_id=instance_id, data=instance)
    
    return instance


def get_instance(module_key: str, object_type: str, instance_id: str) -> dict[str, Any] | None:
    sk = _instance_store_key(module_key, object_type)
    store = _INSTANCES.get(sk, {})
    return store.get(instance_id)


def get_instance_by_id(instance_id: str) -> dict[str, Any] | None:
    return _INSTANCE_BY_ID.get(instance_id)


def list_instances(module_key: str, object_type: str) -> list[dict[str, Any]]:
    sk = _instance_store_key(module_key, object_type)
    store = _INSTANCES.get(sk, {})
    return list(store.values())


def update_instance(module_key: str, object_type: str, instance_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    sk = _instance_store_key(module_key, object_type)
    store = _INSTANCES.get(sk, {})
    existing = store.get(instance_id)
    if not existing:
        return None

    now = datetime.now(timezone.utc).isoformat()
    merged = {**existing["data"], **data}
    existing["data"] = merged
    existing["name"] = merged.get("name", merged.get("title", existing["name"]))
    existing["status"] = merged.get("status", existing["status"])
    existing["updated_at"] = now
    _INSTANCE_BY_ID[instance_id] = existing
    
    # Emit event
    get_bus().emit(EventType.OBJECT_UPDATED, module_key=module_key, object_type=object_type, instance_id=instance_id, data=existing, changes=list(data.keys()))
    
    return existing


def delete_instance(module_key: str, object_type: str, instance_id: str) -> bool:
    sk = _instance_store_key(module_key, object_type)
    store = _INSTANCES.get(sk, {})
    if instance_id in store:
        del store[instance_id]
        _INSTANCE_BY_ID.pop(instance_id, None)
        
        # Emit event
        get_bus().emit(EventType.OBJECT_DELETED, module_key=module_key, object_type=object_type, instance_id=instance_id)
        
        return True
    return False


def _clear_module_instances(module_key: str) -> None:
    """Remove all instances for a given module."""
    keys_to_remove = [k for k in _INSTANCES if k.startswith(f"{module_key}:")]
    for k in keys_to_remove:
        for iid in _INSTANCES.get(k, {}):
            _INSTANCE_BY_ID.pop(iid, None)
        _INSTANCES.pop(k, None)


# ── Object Type Lookup ───────────────────────────────────────────────────

def _find_object_type(module: ModuleDef, type_key: str) -> ObjectTypeDef | None:
    for ot in (module.object_types or []):
        if ot.key == type_key:
            return ot
    return None


def get_all_object_types() -> list[tuple[str, ObjectTypeDef]]:
    """Returns (module_key, ObjectTypeDef) for all registered types."""
    result = []
    for mod_key, mod in _MODULES.items():
        for ot in (mod.object_types or []):
            result.append((mod_key, ot))
    return result


def find_type_for_object_type(type_key: str) -> tuple[str, ObjectTypeDef] | None:
    """Find which module an object type belongs to."""
    for mod_key, mod in _MODULES.items():
        for ot in (mod.object_types or []):
            if ot.key == type_key:
                return (mod_key, ot)
    return None


# ── Field Processor ──────────────────────────────────────────────────────

def _process_fields(type_def: ObjectTypeDef, data: dict[str, Any]) -> dict[str, Any]:
    """Validate and process field values according to their type definitions."""
    result = {}
    fields = type_def.fields or []

    for field in fields:
        value = data.get(field.key)

        if value is None and field.required:
            # Skip validation for required fields — let the caller handle
            pass

        if value is not None:
            value = _validate_field_type(field, value)

        if value is not None:
            result[field.key] = value
        elif field.default is not None:
            result[field.key] = field.default

    # Also include any extra fields not in definition
    for key in data:
        if key not in [f.key for f in fields]:
            result[key] = data[key]

    return result


def _validate_field_type(field: FieldDef, value: Any) -> Any:
    """Basic type validation/conversion."""
    if value is None:
        return None

    ft = field.field_type

    if ft == FieldType.NUMBER:
        try:
            return float(value)
        except (ValueError, TypeError):
            return value

    if ft == FieldType.INTEGER:
        try:
            return int(value)
        except (ValueError, TypeError):
            return value

    if ft == FieldType.CURRENCY:
        try:
            return float(value)
        except (ValueError, TypeError):
            return value

    if ft == FieldType.PERCENTAGE:
        try:
            v = float(value.rstrip("%")) if isinstance(value, str) and value.endswith("%") else float(value)
            return v
        except (ValueError, TypeError):
            return value

    if ft == FieldType.BOOLEAN:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "y")
        return bool(value)

    if ft == FieldType.SELECT and field.options:
        if value not in field.options:
            # Try case-insensitive match
            for opt in field.options:
                if opt.lower() == value.lower():
                    return opt
            return value  # Accept anyway
        return value

    if ft in (FieldType.JSON, FieldType.COMPUTED, FieldType.FORMULA, FieldType.LOOKUP):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value

    return value


# ── View Generator ───────────────────────────────────────────────────────

def generate_views(object_type: ObjectTypeDef, module_key: str) -> list[ViewDef]:
    """Auto-generate compatible views for an object type based on its fields."""
    views = []
    ot = object_type
    fields = ot.fields or []

    if not fields:
        return views

    field_keys = [f.key for f in fields]
    list_fields = [f.key for f in fields if f.display_in_list][:8] or field_keys[:5]

    # List view (always available)
    views.append(ViewDef(
        key=f"{ot.key}_list",
        label=f"{ot.plural_name}",
        view_type=ViewType.LIST,
        object_type=ot.key,
        fields=list_fields,
        is_default=ot.default_view == "list",
    ))

    # Table view
    views.append(ViewDef(
        key=f"{ot.key}_table",
        label=ot.plural_name,
        view_type=ViewType.TABLE,
        object_type=ot.key,
        fields=field_keys[:10],
    ))

    # Detail view
    views.append(ViewDef(
        key=f"{ot.key}_detail",
        label=f"{ot.name} Detail",
        view_type=ViewType.DETAIL,
        object_type=ot.key,
        fields=field_keys,
    ))

    # Calendar view — if there's a date field
    date_field = ot.calendar_field or _find_date_field(fields)
    if date_field:
        views.append(ViewDef(
            key=f"{ot.key}_calendar",
            label="Calendar",
            view_type=ViewType.CALENDAR,
            object_type=ot.key,
            fields=list_fields,
        ))

    # Kanban view — if status or select field exists
    status_field = next((f for f in fields if f.key in ("status", "stage", "state")), None)
    if status_field:
        views.append(ViewDef(
            key=f"{ot.key}_kanban",
            label="Kanban",
            view_type=ViewType.KANBAN,
            object_type=ot.key,
            fields=list_fields,
            group_by=status_field.key,
        ))

    # Map view — if location or address field exists
    if any(f.field_type in (FieldType.LOCATION, FieldType.ADDRESS) for f in fields):
        views.append(ViewDef(
            key=f"{ot.key}_map",
            label="Map",
            view_type=ViewType.MAP,
            object_type=ot.key,
            fields=list_fields,
        ))

    # Timeline view
    if _find_date_field(fields):
        views.append(ViewDef(
            key=f"{ot.key}_timeline",
            label="Timeline",
            view_type=ViewType.TIMELINE,
            object_type=ot.key,
            fields=list_fields,
            sort_by=_find_date_field(fields) or "created_at",
        ))

    return views


def _find_date_field(fields: list[FieldDef]) -> str | None:
    date_types = {FieldType.DATE, FieldType.DATETIME}
    for f in fields:
        if f.field_type in date_types:
            return f.key
    return None


# ── Navigation Generator ─────────────────────────────────────────────────

def generate_navigation(module: ModuleDef) -> list[NavigationEntry]:
    """Generate navigation entries for a module."""
    entries = []
    for ot in (module.object_types or []):
        entries.append(NavigationEntry(
            label=ot.plural_name or ot.name + "s",
            object_type=ot.key,
            icon=ot.icon,
        ))
    return entries


# ── Reset (for testing) ──────────────────────────────────────────────────

def reset() -> None:
    """Clear all state. Used for testing."""
    _MODULES.clear()
    _TEMPLATES.clear()
    _INSTANCES.clear()
    _INSTANCE_BY_ID.clear()