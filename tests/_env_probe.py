"""Subprocess probe for test-environment inheritance (G1.24).

Run as a FILE (never through an interpreter pipe). Prints one JSON object
describing what the child process actually inherited and what the application's
own declaration predicate answers in that child.

Deliberately reports PRESENCE, never a value — the probe is part of the evidence
that no credential reaches a subprocess, so it must not become a leak itself.
"""

import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_WATCHED = ("RESEND_API_KEY", "EMAIL_USER", "EMAIL_PASSWORD", "EMAIL_HOST",
            "DATABASE_URL", "EMAIL_PROVIDER", "FLASK_ENV", "SHUNYA_ENV",
            "SHUNYA_ENVIRONMENT")


def main() -> int:
    present = {name: bool(os.environ.get(name)) for name in _WATCHED}
    payload = {
        "present": present,
        "email_provider": os.environ.get("EMAIL_PROVIDER", ""),
        "declared_test_environment": None,
        "error": "",
    }
    try:
        from app import declared_test_environment

        payload["declared_test_environment"] = bool(declared_test_environment())
    except Exception as exc:  # noqa: BLE001 — report, do not mask
        payload["error"] = f"{type(exc).__name__}: {exc}"
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
