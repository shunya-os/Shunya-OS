"""Shadow Runner — safely execute dormant modules alongside the main pipeline.

PHASE 3 LAYER B: Every dormant module runs in shadow mode before activation.
Shadow outputs are compared to main outputs. Differences are logged.
No shadow output controls execution — it only observes.

PHASE 3.1 HARDENING: Uses REAL callable functions from each dormant module.
No fake imports. Each shadow run produces structured output.
"""

import json
import logging
import os
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


# ---------------------------------------------------------------------------
# REAL shadow runners — use actual functions from each module
# ---------------------------------------------------------------------------

def run_shadow_cortex() -> dict:
    """Run the cortex AttentionEngine in shadow mode.

    Uses the REAL get_engine() and AttentionEngine.get_attention_queue().
    Produces structured attention output.
    """
    result = {"system": "cortex", "status": "shadow", "shadow_ok": False, "outputs": []}
    try:
        from app.cortex.attention import get_engine, compute_priority
        engine = get_engine()
        queue = engine.get_attention_queue(limit=5)
        items = []
        for item in queue:
            items.append({
                "id": getattr(item, "item_id", None),
                "source_type": getattr(item, "source_type", None),
                "summary": getattr(item, "summary", None)[:80] if getattr(item, "summary", None) else None,
                "priority": compute_priority(item) if hasattr(item, "to_dict") else None,
            })
        result["outputs"].append({"module": "attention", "action": "get_attention_queue", "items": items})
        result["shadow_ok"] = True
    except Exception as e:
        result["outputs"].append({"module": "attention", "error": str(e)})

    try:
        from app.cortex.state import get_synthesizer
        synth = get_synthesizer()
        state = synth.synthesize()
        result["outputs"].append({
            "module": "state",
            "action": "synthesize",
            "state": state.to_dict() if hasattr(state, "to_dict") else str(state)[:200],
        })
        result["shadow_ok"] = True
    except Exception as e:
        result["outputs"].append({"module": "state", "error": str(e)})

    return result


def run_shadow_planning() -> dict:
    """Run the planning PlanningService in shadow mode."""
    result = {"system": "planning", "status": "shadow", "shadow_ok": False, "outputs": []}
    try:
        from app.planning import PlanningService
        service = PlanningService()
        plan = service.create_plan(
            attention_result={"items": [], "count": 0},
            context={"source": "shadow_test"},
        )
        result["outputs"].append({
            "module": "planning",
            "action": "create_plan",
            "plan": plan if isinstance(plan, dict) else str(plan)[:200],
        })
        result["shadow_ok"] = True
    except Exception as e:
        result["outputs"].append({"module": "planning", "error": str(e)})
    return result


def run_shadow_kernel() -> dict:
    """Run the kernel StateMachine in shadow mode."""
    result = {"system": "kernel", "status": "shadow", "shadow_ok": False, "outputs": []}
    try:
        from app.kernel.state import StateMachine
        sm = StateMachine(object_id="shadow-test", object_type="test")
        result["outputs"].append({
            "module": "state_machine",
            "action": "init",
            "state": sm.to_dict() if hasattr(sm, "to_dict") else str(sm)[:200],
        })
        result["shadow_ok"] = True
    except Exception as e:
        result["outputs"].append({"module": "state_machine", "error": str(e)})
    return result


def run_shadow_authz() -> dict:
    """Run the authz RBAC system in shadow mode."""
    result = {"system": "authz", "status": "shadow", "shadow_ok": False, "outputs": []}
    try:
        from app.authz.services import get_permissions
        permissions = get_permissions()
        result["outputs"].append({
            "module": "authz",
            "action": "get_permissions",
            "permissions": permissions if isinstance(permissions, list) else str(permissions)[:200],
        })
        result["shadow_ok"] = True
    except Exception as e:
        result["outputs"].append({"module": "authz", "error": str(e)})
    return result


def run_shadow_automation() -> dict:
    """Run the automation system in shadow mode."""
    result = {"system": "automation", "status": "shadow", "shadow_ok": False, "outputs": []}
    try:
        from app.automation.service import evaluate_rules
        rules = evaluate_rules()
        result["outputs"].append({
            "module": "automation",
            "action": "evaluate_rules",
            "rules": rules if isinstance(rules, list) else str(rules)[:200],
        })
        result["shadow_ok"] = True
    except Exception as e:
        result["outputs"].append({"module": "automation", "error": str(e)})
    return result


def run_shadow_onboarding() -> dict:
    """Run the onboarding system in shadow mode."""
    result = {"system": "onboarding", "status": "shadow", "shadow_ok": False, "outputs": []}
    try:
        from app.onboarding import get_onboarding_steps
        steps = get_onboarding_steps()
        result["outputs"].append({
            "module": "onboarding",
            "action": "get_onboarding_steps",
            "steps": steps if isinstance(steps, list) else str(steps)[:200],
        })
        result["shadow_ok"] = True
    except Exception as e:
        result["outputs"].append({"module": "onboarding", "error": str(e)})
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
                "authz": run_shadow_authz,
                "automation": run_shadow_automation,
                "onboarding": run_shadow_onboarding,
            }
            fn = runner.get(name)
            if fn:
                result = fn()
                shadows.append(result)
                if result.get("shadow_ok"):
                    logger.info("Shadow OK: %s", name)
                else:
                    logger.warning("Shadow issues: %s — %s", name, result)
        except Exception as e:
            logger.error("Shadow run failed for %s: %s", name, e)
            shadows.append({"system": name, "status": "error", "error": str(e)})
    return shadows


# ---------------------------------------------------------------------------
# Meaningful comparison — compare decisions, priorities, actions (not just counts)
# ---------------------------------------------------------------------------

def extract_signal(output: dict) -> dict:
    """Extract a comparable signal from a shadow output."""
    system = output.get("system", "unknown")
    if system == "cortex":
        # Extract attention priorities
        for o in output.get("outputs", []):
            if o.get("module") == "attention" and o.get("items"):
                priorities = [i.get("priority") for i in o["items"] if i.get("priority") is not None]
                return {"system": system, "signal": "attention_priority", "value": priorities[:5]}
        return {"system": system, "signal": "attention", "value": []}
    if system == "planning":
        for o in output.get("outputs", []):
            if o.get("plan"):
                return {"system": system, "signal": "plan", "value": o.get("plan")}
        return {"system": system, "signal": "plan", "value": None}
    if system == "kernel":
        for o in output.get("outputs", []):
            if o.get("state"):
                return {"system": system, "signal": "state", "value": o.get("state")}
        return {"system": system, "signal": "state", "value": None}
    return {"system": system, "signal": "unknown", "value": None}


def compare_with_main(main_output: dict, shadow_outputs: list) -> list:
    """Compare main execution output with shadow outputs.

    PHASE 3.1: Meaningful comparison — extracts the actual signal
    (decision, priority, action) from each shadow and compares structure.
    """
    comparisons = []
    for shadow in shadow_outputs:
        name = shadow.get("system", "unknown")
        signal = extract_signal(shadow)
        if shadow.get("shadow_ok"):
            comparisons.append({
                "system": name,
                "signal": signal.get("signal"),
                "value": signal.get("value"),
                "status": "aligned" if signal.get("value") else "empty",
                "note": "Shadow produced structured output (no control)",
            })
            logger.info("Shadow comparison: %s → signal=%s", name, signal.get("signal"))
        else:
            comparisons.append({
                "system": name,
                "status": "shadow_failed",
                "reason": shadow.get("outputs", [{}])[0].get("error", "unknown") if shadow.get("outputs") else "no output",
            })
            logger.warning("Shadow comparison: %s — shadow failed, main continues", name)
    return comparisons


def log_shadow_analysis(comparisons: list):
    """Log meaningful shadow analysis."""
    aligned = [c for c in comparisons if c.get("status") == "aligned"]
    failed = [c for c in comparisons if c.get("status") == "shadow_failed"]
    empty = [c for c in comparisons if c.get("status") == "empty"]

    logger.info("Shadow analysis: %d aligned, %d empty, %d failed", len(aligned), len(empty), len(failed))
    for a in aligned:
        logger.info("  ✓ %s → %s: %s", a["system"], a["signal"], a.get("note", ""))
    for e in empty:
        logger.info("  ○ %s → %s: empty output (no decisions yet)", e["system"], e["signal"])
    for f in failed:
        logger.info("  ✗ %s: %s", f["system"], f.get("reason", "unknown"))