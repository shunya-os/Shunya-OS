"""Decision Comparator — compares main decisions with shadow outputs.

PHASE 3.2: Converts shadow intelligence into decision-influencing intelligence.
Cortex priority influences ranking, planning validates decisions, kernel validates state.
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def extract_decision_confidence(main_decision: dict) -> float:
    """Extract a numeric confidence from the main decision."""
    conf = main_decision.get("decision_confidence", "medium")
    mapping = {"high": 0.85, "medium": 0.60, "low": 0.35}
    return mapping.get(conf, 0.60)


def extract_shadow_signals(shadow_outputs: list, context: dict = None) -> dict:
    """Extract meaningful signals from shadow outputs.

    Returns:
        cortex_priority: float (0-1) — attention priority from cortex
        planning_valid: bool — whether planning validates the decision
        kernel_state_valid: bool — whether kernel approves state transition
        shadow_count: int — how many shadows produced output
        shadow_agreement: float (0-1) — fraction of shadows that agree
    """
    result = {
        "cortex_priority": 0.5,
        "planning_valid": True,
        "kernel_state_valid": True,
        "shadow_count": 0,
        "shadow_ok_count": 0,
        "shadow_agreement": 0.5,
    }

    for shadow in shadow_outputs:
        if not shadow.get("shadow_ok"):
            continue
        result["shadow_ok_count"] += 1
        system = shadow.get("system", "")

        for o in shadow.get("outputs", []):
            if system == "cortex" and o.get("module") == "attention":
                items = o.get("items", [])
                if items:
                    priorities = [i.get("priority", 0.5) for i in items if i.get("priority") is not None]
                    if priorities:
                        result["cortex_priority"] = max(priorities)
        # Boost if context shows this object is a priority
        if context and context.get("entity_id"):
            result["cortex_priority"] = max(result["cortex_priority"], 0.65)
            if system == "kernel" and o.get("module") == "state_machine":
                if o.get("state"):
                    result["kernel_state_valid"] = True
            if system == "planning" and o.get("plan"):
                result["planning_valid"] = True

    result["shadow_count"] = len(shadow_outputs)
    if result["shadow_count"] > 0:
        result["shadow_agreement"] = result["shadow_ok_count"] / result["shadow_count"]

    return result


def compare(main_decision: dict, shadow_outputs: list, context: dict = None) -> dict:
    """Compare main decision with shadow outputs.

    Args:
        main_decision: The decision dict from the main execution path
        shadow_outputs: List of shadow system outputs

    Returns:
        dict with:
            agreement: bool
            confidence_delta: float
            recommended_override: optional dict
            reasoning: str
            shadow_confidence: float
            main_confidence: float
            enhanced_confidence: float
    """
    main_conf = extract_decision_confidence(main_decision)
    shadow_sigs = extract_shadow_signals(shadow_outputs, context=context)

    # Compute shadow confidence from cortex priority and agreement
    shadow_conf = (
        shadow_sigs["cortex_priority"] * 0.4
        + shadow_sigs["shadow_agreement"] * 0.4
        + (0.2 if shadow_sigs["planning_valid"] and shadow_sigs["kernel_state_valid"] else 0.0)
    )
    shadow_conf = max(0.0, min(1.0, shadow_conf))

    confidence_delta = shadow_conf - main_conf
    agreement = abs(confidence_delta) < 0.2  # within 20% is agreement

    # Build reasoning
    reasoning_parts = []
    reasoning_parts.append(f"Main confidence: {main_conf:.2f}")
    reasoning_parts.append(f"Shadow confidence: {shadow_conf:.2f}")
    reasoning_parts.append(f"Cortex priority: {shadow_sigs['cortex_priority']:.2f}")
    reasoning_parts.append(f"Shadow agreement: {shadow_sigs['shadow_ok_count']}/{shadow_sigs['shadow_count']} systems")
    reasoning_parts.append(f"Kernel state valid: {shadow_sigs['kernel_state_valid']}")
    reasoning_parts.append(f"Planning valid: {shadow_sigs['planning_valid']}")
    reasoning = " | ".join(reasoning_parts)

    # Recommended override
    recommended_override = None
    if confidence_delta > 0.2:
        # Shadow confidence is significantly higher — recommend enhancement
        recommended_override = {
            "type": "enhance",
            "reason": f"Shadow confidence ({shadow_conf:.2f}) exceeds main ({main_conf:.2f}) by {confidence_delta:.2f}",
        }
    elif confidence_delta < -0.3:
        # Main confidence is significantly higher — keep original
        recommended_override = {
            "type": "keep",
            "reason": f"Main confidence ({main_conf:.2f}) is significantly higher than shadow ({shadow_conf:.2f})",
        }

    enhanced_confidence = max(main_conf, shadow_conf) if confidence_delta > 0 else main_conf

    return {
        "agreement": agreement,
        "confidence_delta": round(confidence_delta, 3),
        "recommended_override": recommended_override,
        "reasoning": reasoning,
        "shadow_confidence": round(shadow_conf, 3),
        "main_confidence": round(main_conf, 3),
        "enhanced_confidence": round(enhanced_confidence, 3),
        "shadow_signals": shadow_sigs,
    }