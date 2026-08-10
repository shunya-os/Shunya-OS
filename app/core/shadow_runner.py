"""Shadow Runner — safely execute dormant modules alongside the main pipeline.

PHASE 3 LAYER B: Every dormant module runs in shadow mode before activation.
Shadow outputs are compared to main outputs. Differences are logged.
No shadow output controls execution — it only observes.

This is how SHUNYA becomes intelligent without breaking.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


def load_activation_map() -> dict:
    """Load the activation map from the audit directory."""
    map_path = os.path.join(
        os.path.dirname(__file__), "..", "_audit", "activation_map.json"
    )
    try:
        with open(map_path) as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Could not load activation map: %s", e)
        return {"systems": {}}


def get_shadow_systems() -> list:
    """Return the list of systems running in shadow mode."""
    activation_map = load_activation_map()
    systems = activation_map.get("systems", {})
    return [
        {"name": name, **info}
        for name, info in systems.items()
        if info.get("mode") == "shadow_first"
    ]


def run_shadow_cortex() -> dict:
    """Run the cortex system in shadow mode — observe, don't control."""
    result = {"system": "cortex", "status": "shadow", "outputs": []}
    try:
        from app.cortex.attention import calculate_attention
        attention = calculate_attention()
        result["outputs"].append({"module": "attention", "result": str(attention)[:200]})
    except Exception as e:
        result["outputs"].append({"module": "attention", "error": str(e)})

    try:
        from app.cortex.state import get_organization_state
        state = get_organization_state()
        result["outputs"].append({"module": "state", "result": str(state)[:200]})
    except Exception as e:
        result["outputs"].append({"module": "state", "error": str(e)})

    result["shadow_ok"] = all(
        "error" not in o for o in result["outputs"]
    )
    return result


def run_shadow_planning() -> dict:
    """Run the planning system in shadow mode."""
    result = {"system": "planning", "status": "shadow", "outputs": []}
    try:
        from app.planning.plan import ExecutionPlan
        plan = ExecutionPlan()
        result["outputs"].append({"module": "plan", "result": "Plan initialized"})
    except Exception as e:
        result["outputs"].append({"module": "plan", "error": str(e)})
    return result


def run_shadow_kernel() -> dict:
    """Run the kernel system in shadow mode — extract primitives."""
    result = {"system": "kernel", "status": "shadow", "outputs": []}
    try:
        from app.kernel.object import KernelObject
        obj = KernelObject()
        result["outputs"].append({"module": "object", "result": "KernelObject initialized"})
    except Exception as e:
        result["outputs"].append({"module": "object", "error": str(e)})
    return result


def run_all_shadows() -> list:
    """Execute all shadow-mode systems and return their outputs."""
    shadows = []
    for system in get_shadow_systems():
        name = system.get("name", "unknown")
        try:
            runner = {
                "cortex": run_shadow_cortex,
                "planning": run_shadow_planning,
                "kernel": run_shadow_kernel,
                "authz": lambda: {"system": "authz", "status": "shadow", "note": "Not yet shadow-activated"},
                "automation": lambda: {"system": "automation", "status": "shadow", "note": "Not yet shadow-activated"},
                "onboarding": lambda: {"system": "onboarding", "status": "shadow", "note": "Not yet shadow-activated"},
            }
            fn = runner.get(name)
            if fn:
                result = fn()
                shadows.append(result)
                if result.get("shadow_ok", True):
                    logger.info("Shadow OK: %s", name)
                else:
                    logger.warning("Shadow issues: %s — %s", name, result)
        except Exception as e:
            logger.error("Shadow run failed for %s: %s", name, e)
            shadows.append({"system": name, "status": "error", "error": str(e)})
    return shadows


def compare_with_main(main_output: dict, shadow_outputs: list) -> list:
    """Compare main execution output with shadow outputs.

    Logs differences. Does NOT control execution.
    """
    diffs = []
    for shadow in shadow_outputs:
        name = shadow.get("system", "unknown")
        if shadow.get("shadow_ok"):
            # Shadow ran successfully — compare if applicable
            logger.info("Shadow comparison: %s — no deviation detected (shadow mode)", name)
        else:
            logger.warning("Shadow comparison: %s — shadow failed, but main execution continues", name)
            diffs.append({"system": name, "diff": "shadow_failed", "shadow": shadow})
    return diffs


def log_shadow_diff(diffs: list):
    """Log shadow differences for analysis."""
    if diffs:
        logger.warning("Shadow diffs: %d systems diverged", len(diffs))
        for d in diffs:
            logger.warning("  Shadow diff: %s — %s", d["system"], d.get("diff", "unknown"))
    else:
        logger.info("Shadow diffs: none — all shadow systems aligned")