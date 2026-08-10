"""Usage Guard — tracks which modules are actually used by the runtime.

PHASE 3 LAYER E: If a module exists but is not called, it's reported.
Generates weekly report at /system/unused-intelligence.

This ensures we don't build things we don't use.
"""

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Registry of known modules and their usage status
_module_usage: dict[str, bool] = {}


def register(module_name: str):
    """Register a module for usage tracking.

    Call this at the top of each module's entry point:
        from app.core.usage_guard import register
        register(__name__)
    """
    _module_usage[module_name] = False


def mark_used(module_name: str):
    """Mark a module as used."""
    _module_usage[module_name] = True


def report() -> list:
    """Return a list of modules that are registered but never marked used."""
    return [
        {"module": name, "used": used}
        for name, used in _module_usage.items()
        if not used
    ]


def check_dormant_modules() -> list:
    """Check dormant gold modules against the activation map.

    Returns list of dormant modules that exist but are never called.
    """
    unused = []
    # Load activation map
    map_path = os.path.join(
        os.path.dirname(__file__), "..", "_audit", "activation_map.json"
    )
    try:
        with open(map_path) as f:
            activation_map = json.load(f)
    except Exception:
        return []

    systems = activation_map.get("systems", {})
    for name, info in systems.items():
        if info.get("classification") in ("SHADOW", "CONNECT"):
            module_path = f"app.{name}"
            if module_path not in _module_usage or not _module_usage.get(module_path):
                unused.append({
                    "module": name,
                    "classification": info.get("classification"),
                    "value": info.get("value", "unknown"),
                    "status": "unused" if module_path not in _module_usage else "registered_but_unused",
                })
    return unused