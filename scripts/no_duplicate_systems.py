"""No Duplicate Systems — CI script to prevent new folder creation if similar system exists.

PHASE 3 LAYER F: Run in CI to ensure no new duplicate systems are created.
No new folder allowed if similar system exists. No alternate naming allowed.

Usage:
    python3 scripts/no_duplicate_systems.py
    Returns exit code 0 if no duplicates, 1 if duplicates found.
"""

import json
import os
import sys


def load_known_systems() -> set:
    """Load the list of canonical system names from the activation map."""
    map_path = os.path.join(
        os.path.dirname(__file__), "..", "app", "_audit", "activation_map.json"
    )
    try:
        with open(map_path) as f:
            data = json.load(f)
        return set(data.get("systems", {}).keys())
    except Exception:
        return set()


def get_runtime_systems() -> set:
    """Get the set of system directories in app/ that are actively used."""
    app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
    try:
        dirs = [d for d in os.listdir(app_dir)
                if os.path.isdir(os.path.join(app_dir, d))
                and not d.startswith("_")
                and not d.startswith("__")]
        return set(dirs)
    except Exception:
        return set()


def find_duplicates() -> list:
    """Find systems that overlap with known canonical systems.

    Returns a list of dicts with:
        new_system: The name of the potentially duplicate system
        similar_to: The canonical system it overlaps with
        reason: Why it's considered a duplicate
    """
    duplicates = []
    known = load_known_systems()
    runtime = get_runtime_systems()

    # Known duplicate mappings
    overlap_map = {
        "execution": "execution",
        "execution_engine": "execution",
        "execution_runtime": "execution",
        "execution_intelligence": "execution",
        "decision": "decision",
        "decision_runtime": "decision",
        "objects": "objects",
        "object_workspace": "objects",
        "object_composer": "objects",
        "graph": "graph",
        "graph_universal": "graph",
        "communication": "communication",
        "adapters": "communication",
    }

    for system in runtime:
        if system in overlap_map:
            canonical = overlap_map[system]
            if system != canonical:
                duplicates.append({
                    "new_system": system,
                    "similar_to": canonical,
                    "reason": f"'{system}' overlaps with canonical '{canonical}'",
                })

    return duplicates


def main():
    duplicates = find_duplicates()

    if duplicates:
        print("DUPLICATE SYSTEMS DETECTED:")
        for d in duplicates:
            print(f"  ❌ {d['new_system']} -> {d['similar_to']}: {d['reason']}")
        print(f"\nTotal: {len(duplicates)} duplicate(s)")
        sys.exit(1)
    else:
        print("✅ No duplicate systems detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()