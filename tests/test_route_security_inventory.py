"""B16 — Route/blueprint security inventory gate.

Fails when any registered route has no EXPLICIT security policy:

  * serve-only asset (static, SPA shell, icons)          → PASS
  * entry in the central public allowlist (with reason)  → PASS
  * authz decorator marker on the view function          → PASS
  * anything else (middleware-only protection)           → FAIL

Also enforces allowlist hygiene: every public route must have a documented
reason, and every allowlist entry must actually exist as a route.

This is the automated inventory the B16 directive requires; it also produces
the authoritative count of affected blueprints (reconciling the register's
"nine" vs B17–B24's eight — the real number comes from here, per module).
"""
from __future__ import annotations

import pytest

from app import create_app
from app.security import public_routes
from app.security.public_routes import PUBLIC_ROUTES, PUBLIC_PREFIXES, PUBLIC_ROUTES_REASONS


@pytest.fixture(scope="module")
def inventory_app():
    application = create_app(config_override={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "inventory",
    })
    return application


def _classify(app, rule):
    methods = sorted(m for m in (rule.methods or []) if m not in {"HEAD", "OPTIONS"})
    view = app.view_functions.get(rule.endpoint)
    marker = getattr(view, "_shunya_policy", None) if view else None
    path = rule.rule
    if public_routes.is_serve_only(path):
        return "SERVE_ONLY", marker
    if methods and all(public_routes.is_public(m, path) for m in methods):
        return "PUBLIC", marker
    if marker:
        return "MARKED", marker
    return "UNPROTECTED", marker


def _iter_rules(app):
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, r.endpoint)):
        methods = sorted(m for m in (rule.methods or []) if m not in {"HEAD", "OPTIONS"})
        if not methods:
            continue
        yield rule, methods


def test_every_route_has_explicit_security_policy(inventory_app):
    unprotected = []
    seen_modules: dict[str, set[str]] = {}
    for rule, methods in _iter_rules(inventory_app):
        kind, marker = _classify(inventory_app, rule)
        if kind == "UNPROTECTED":
            view = inventory_app.view_functions.get(rule.endpoint)
            mod = view.__module__ if view else "?"
            seen_modules.setdefault(mod, set()).add(rule.rule)
            unprotected.append((rule.endpoint, ",".join(methods), rule.rule, mod))
    assert not unprotected, (
        "Routes with no explicit security policy (B16):\n"
        + "\n".join(f"  {m:<12} {p:<45} {e}" for e, m, p, _ in unprotected[:200])
        + f"\n... total {len(unprotected)} unprotected across "
        + f"{len(seen_modules)} modules: "
        + ", ".join(f"{m}({len(r)})" for m, r in sorted(seen_modules.items()))
    )


def test_public_allowlist_is_documented(inventory_app):
    undocumented = [r for r in PUBLIC_ROUTES if r not in PUBLIC_ROUTES_REASONS]
    assert not undocumented, f"Public routes missing documented reasons: {undocumented}"
    for m, prefix in PUBLIC_PREFIXES:
        key = (m, prefix)
        assert key in PUBLIC_ROUTES_REASONS or prefix in PUBLIC_ROUTES_REASONS, (
            f"Public prefix missing documented reason: {key}"
        )


def test_public_allowlist_entries_exist(inventory_app):
    existing = {(m, rule.rule) for rule, methods in _iter_rules(inventory_app) for m in methods}
    dead = [r for r in PUBLIC_ROUTES if r not in existing]
    assert not dead, f"Public allowlist entries that match no route: {dead}"


def test_public_prefixes_have_routes(inventory_app):
    paths = {rule.rule for rule, _ in _iter_rules(inventory_app)}
    for m, prefix in PUBLIC_PREFIXES:
        assert any(p.startswith(prefix) for p in paths), (
            f"Public prefix {m} {prefix} matches no registered route"
        )