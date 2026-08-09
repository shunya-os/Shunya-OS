#!/usr/bin/env python3
"""ACT-01 Debug CLI — minimal human interface to the SHUNYA runtime.

Usage:
    python3 scripts/debug_cli.py [--host HOST] [--port PORT]

Requires: requests (pip install requests)
"""

import json
import os
import sys

try:
    import requests
except ImportError:
    print("Missing dependency: requests")
    print("Run: pip install requests")
    sys.exit(1)


BASE = os.environ.get("DEBUG_API", "http://127.0.0.1:5678")


def api(path, method="GET", data=None):
    url = f"{BASE}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=10)
        else:
            resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def cmd_create_lead():
    title = input("  Title/description: ").strip()
    data = {"type": "lead", "data": {"description": title, "stage": "new"}}
    result = api("/debug/entity", method="POST", data=data)
    print(f"  → {json.dumps(result, indent=2)}")


def cmd_run_cycle():
    print("  Running one cycle...")
    result = api("/debug/run-cycle", method="POST")
    summary = result.get("summary", result)
    print(f"  Total objects: {summary.get('total_objects', '?')}")
    print(f"  Actions taken: {summary.get('actions_taken', '?')}")
    print(f"  Noops:         {summary.get('noops', '?')}")
    print(f"  Errors:        {summary.get('errors', [])}")
    print(f"  Signals:       {summary.get('signals_emitted', '?')}")


def cmd_view_state():
    print("  Fetching state...")
    result = api("/debug/state")
    for key in ("entities", "tasks", "observations"):
        items = result.get(key, [])
        print(f"\n  === {key.upper()} ({len(items)}) ===")
        for item in items:
            print(f"    #{item.get('id')}: {json.dumps(item, indent=4)}")


def main():
    print("╔══════════════════════════════════════╗")
    print("║   SHUNYA — ACT-01 Debug Console      ║")
    print("║   API:", BASE + "/debug        ║")
    print("╚══════════════════════════════════════╝")

    actions = {
        "1": ("Create lead", cmd_create_lead),
        "2": ("Run cycle", cmd_run_cycle),
        "3": ("View state", cmd_view_state),
        "4": ("Exit", None),
    }

    while True:
        print()
        for key, (label, _) in actions.items():
            print(f"  [{key}] {label}")
        choice = input("\n  Select: ").strip()

        if choice == "4":
            print("  Bye.")
            break

        action = actions.get(choice)
        if action:
            _, fn = action
            if fn:
                fn()
        else:
            print("  Unknown option.")


if __name__ == "__main__":
    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        BASE = f"http://{sys.argv[idx + 1]}:5678"
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        parts = BASE.split(":")
        BASE = f"{parts[0]}:{parts[1]}:{sys.argv[idx + 1]}"
    main()