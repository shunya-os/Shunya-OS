"""SHUNYA route/blueprint security inventory (B16).

Walks the Flask url_map of a freshly-created application and classifies every
route by its explicit security policy:

  PUBLIC          — rule matches the central PUBLIC_ROUTES allowlist
  SPA/STATIC      — SPA shell, static assets, icons, manifest (serve-only)
  POLICY_MARKED   — view function carries an authz marker set by an
                    authentication/authorization decorator
  UNPROTECTED     — no marker, no allowlist entry  (B16 FAIL)

Usage:  PYTHONPATH=$PWD python3 scripts/route_inventory.py [--json]
Output: one line per rule plus a summary; exits 1 when UNPROTECTED routes exist.
"""
from __future__ import annotations

import json
import logging
import sys

# The app's JSON logger writes NDJSON lines to stdout — silence it so the
# inventory output stays valid JSON when --json is used.
logging.disable(logging.INFO)

from app import create_app
from app.security import public_routes
from app.security.public_routes import PUBLIC_ROUTES, SPA_SHELL_PATHS


def classify(app) -> list[dict]:
    rows = []
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, sorted(r.methods or []))):
        methods = sorted(m for m in (rule.methods or []) if m not in {"HEAD", "OPTIONS"})
        view = app.view_functions.get(rule.endpoint)
        marker = getattr(view, "_shunya_policy", None) if view else None
        path = rule.rule
        if public_routes.is_serve_only(path):
            kind = "SPA/STATIC"
        elif methods and all(public_routes.is_public(m, path) for m in methods):
            kind = "PUBLIC"
        elif marker:
            kind = f"MARKED({marker})"
        else:
            kind = "UNPROTECTED"
        rows.append({
            "endpoint": rule.endpoint,
            "methods": ",".join(methods) or "*",
            "path": path,
            "kind": kind,
            "module": (view.__module__ if view else "?"),
        })
    return rows


def main() -> int:
    app = create_app(config_override={"TESTING": True,
                                      "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                                      "SECRET_KEY": "inventory"})
    rows = classify(app)
    unprotected = [r for r in rows if r["kind"] == "UNPROTECTED"]
    if "--json" in sys.argv:
        print(json.dumps({"total": len(rows), "unprotected": len(unprotected), "rows": rows},
                         indent=1))
    else:
        for r in rows:
            print(f"{r['kind']:<46} {r['methods']:<8} {r['path']:<60} {r['endpoint']}")
        print(f"\nTOTAL={len(rows)}  UNPROTECTED={len(unprotected)}")
    return 1 if unprotected else 0


if __name__ == "__main__":
    raise SystemExit(main())