"""Evolution Engine — observes operational behavior and suggests business improvements.

After module installation, the engine watches usage patterns and recommends
new object types, automations, workflow improvements, and field refinements.
All suggestions are previewed, explained, and must be explicitly approved.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from app.ubme.ontology import ConfidenceLevel


# ── Observation Store ─────────────────────────────────────────────────────


_observations: dict[str, list[dict[str, Any]]] = defaultdict(list)
_suggestions: dict[str, list[dict[str, Any]]] = defaultdict(list)


def record_action(action: str, module_key: str, object_type: str, details: dict[str, Any] | None = None) -> None:
    """Record an operational action for evolution analysis."""
    _observations[module_key].append({
        "action": action,
        "object_type": object_type,
        "details": details or {},
    })


def get_observations(module_key: str) -> list[dict[str, Any]]:
    return list(_observations.get(module_key, []))


def get_suggestions(module_key: str) -> list[dict[str, Any]]:
    return list(_suggestions.get(module_key, []))


def approve_suggestion(module_key: str, suggestion_key: str) -> bool:
    """Mark a suggestion as approved and applied."""
    for s in _suggestions.get(module_key, []):
        if s.get("key") == suggestion_key:
            s["status"] = "approved"
            return True
    return False


def dismiss_suggestion(module_key: str, suggestion_key: str) -> bool:
    """Mark a suggestion as dismissed."""
    for s in _suggestions.get(module_key, []):
        if s.get("key") == suggestion_key:
            s["status"] = "dismissed"
            return True
    return False


# ── Evolution Rules ──────────────────────────────────────────────────────


def analyze_usage(module_key: str) -> list[dict[str, Any]]:
    """Analyze usage observations and generate improvement suggestions."""
    obs = _observations.get(module_key, [])
    suggestions = []

    # 1. Detect repeated manual object creation patterns
    create_counts = Counter()
    for o in obs:
        if o["action"] == "create":
            create_counts[o["object_type"]] += 1

    for object_type, count in create_counts.items():
        if count >= 3:
            suggestions.append({
                "key": f"new_type_{object_type}",
                "type": "new_object_type",
                "title": f"Repeated {object_type.capitalize()} Creation",
                "description": f"You've created {object_type.capitalize()} manually {count} times. Would you like to create a {object_type.capitalize()} module?",
                "confidence": min(0.5 + count * 0.1, 0.95),
                "status": "pending",
            })

    # 2. Detect frequent status transition patterns
    transition_counts = Counter()
    for o in obs:
        if o["action"] == "transition" and "from" in o.get("details", {}):
            key = f"{o['details']['from']}→{o['details']['to']}"
            transition_counts[key] += 1

    for transition, count in transition_counts.items():
        if count >= 5:
            parts = transition.split("→")
            suggestions.append({
                "key": f"auto_transition_{transition.replace('→', '_')}",
                "type": "automation",
                "title": f"Automate '{transition}' Transition",
                "description": f"'{transition}' happens {count} times. Would you like to automate this transition?",
                "confidence": min(0.5 + count * 0.05, 0.9),
                "status": "pending",
            })

    # 3. Detect repeated field patterns (same custom fields on many records)
    field_combos = Counter()
    for o in obs:
        if o["action"] == "field_update" and "fields" in o.get("details", {}):
            key = tuple(sorted(o["details"]["fields"]))
            field_combos[key] += 1

    for fields, count in field_combos.most_common(3):
        if count >= 3 and len(fields) >= 3:
            suggestions.append({
                "key": f"refactor_fields_{'_'.join(fields[:2])}",
                "type": "field_refinement",
                "title": "Repeated Field Group Found",
                "description": f"These {len(fields)} custom fields appear together on {count} records. They could become a reusable sub-object.",
                "confidence": min(0.5 + count * 0.1, 0.85),
                "status": "pending",
            })

    # 4. Detect creation patterns for related entities
    combined_creates = []
    for o in obs:
        if o["action"] == "create":
            combined_creates.append(o["object_type"])

    for i in range(len(combined_creates) - 1):
        pair = (combined_creates[i], combined_creates[i+1])
        if pair[0] != pair[1]:
            count = 1
            for j in range(i+1, len(combined_creates) - 1):
                if combined_creates[j] == pair[0] and combined_creates[j+1] == pair[1]:
                    count += 1
            if count >= 2:
                suggestions.append({
                    "key": f"auto_relate_{pair[0]}_{pair[1]}",
                    "type": "relationship",
                    "title": f"Linked: {pair[0].capitalize()} → {pair[1].capitalize()}",
                    "description": f"You often create a {pair[0]} and then a {pair[1]}. Should these be automatically linked?",
                    "confidence": min(0.5 + count * 0.15, 0.9),
                    "status": "pending",
                })

    _suggestions[module_key] = suggestions
    return suggestions


def reset_observations(module_key: str | None = None) -> None:
    """Clear observations for testing."""
    if module_key:
        _observations.pop(module_key, None)
        _suggestions.pop(module_key, None)
    else:
        _observations.clear()
        _suggestions.clear()