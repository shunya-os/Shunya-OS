"""R6B-2.7 Window 6 — Batch F: anti-bypass regression guard.

SEMANTIC, not textual. This is the direct remediation of the Batch C incident
where a naive patch script matched the literal text ``svc.create(`` inside a
source-scanning assertion string and corrupted a test. Every check here parses
the source with ``ast``, so a token appearing inside a string literal or a
comment is never mistaken for an executable invocation.

What is pinned
--------------
* No identity-less ObjectService invocation anywhere in production, except the
  ONE audited offline migration helper.
* ``system_scope=True`` exists in exactly one audited, non-request-reachable
  production location.
* Tests may assert that identity+system_scope is REJECTED but may never use
  ``system_scope=True`` on its own to obtain access.
* No authorization path defaults to a synthetic ``spc_*`` workspace.
* No production code writes or depends on the legacy ``FounderObject``.
* The canonical resolver never selects an organization/workspace membership
  arbitrarily with ``.first()``.
"""
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRODUCTION_DIRS = ("app", "core")
METHODS = {"create", "get", "update", "delete"}

# The ONLY audited production system-scope caller: tenant provisioning /
# state seeding, not a user request path.
AUDITED_SYSTEM_SCOPE_FILES = {"app/onboard.py"}
# The ONLY identity-less create: ObjectService.migrate_from(), an OFFLINE
# migration helper with no production callers, which fails closed per row.
AUDITED_IDENTITYLESS_FILES = {"core/object_service.py"}


def _py_files(*dirs):
    out = []
    for d in dirs:
        target = ROOT / d
        if target.is_file():
            out.append(target)
            continue
        out.extend(sorted(target.rglob("*.py")))
    return [p for p in out if "__pycache__" not in p.parts]


def _parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _rel(path):
    return str(path.relative_to(ROOT))


def _object_service_calls(tree, in_service_module=False):
    """(lineno, method, kwargs, inside_expected_denial) for real invocations."""
    found = []

    def visit(node, in_raises=False):
        if isinstance(node, ast.With):
            inner = in_raises or any(
                isinstance(i.context_expr, ast.Call)
                and ast.unparse(i.context_expr.func).endswith("raises")
                for i in node.items
            )
            for child in ast.iter_child_nodes(node):
                visit(child, inner)
            return
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            meth = node.func.attr
            base = node.func.value
            recv = None
            if isinstance(base, ast.Name):
                recv = base.id
            elif isinstance(base, ast.Call):
                try:
                    recv = ast.unparse(base.func)
                except Exception:
                    recv = None
            if meth in METHODS and recv is not None:
                tail = recv.split(".")[-1]
                if (tail == "svc" or "get_object_service" in recv
                        or (tail == "self" and in_service_module)):
                    found.append((
                        node.lineno, meth,
                        {k.arg for k in node.keywords if k.arg},
                        in_raises,
                    ))
        for child in ast.iter_child_nodes(node):
            visit(child, in_raises)

    visit(tree)
    return found


def _system_scope_true_sites(tree):
    """(lineno, has_identity_id) for every keyword `system_scope=True`.

    ``actor_identity_id`` counts as the identity-bearing keyword: the canonical
    membership service (``app/authz/workspace_membership.py``) names its actor
    parameter that way, and it rejects ``system_scope`` combined with an actor.
    A bare ``system_scope=True`` — the actual bypass — is still flagged.
    """
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        kwargs = {k.arg for k in node.keywords if k.arg}
        has_identity = bool(kwargs & {"identity_id", "actor_identity_id"})
        for k in node.keywords:
            if (k.arg == "system_scope" and isinstance(k.value, ast.Constant)
                    and k.value.value is True):
                out.append((node.lineno, has_identity))
    return out


# ---------------------------------------------------------------------------
# The guard must not be foolable by string literals (the Batch C incident)
# ---------------------------------------------------------------------------

def test_guard_ignores_invocations_inside_string_literals_and_comments():
    src = (
        'x = "svc.create("\n'
        '# svc.update(obj_id, 1)\n'
        'y = "svc.get(" in x\n'
        'z = """svc.delete("""\n'
    )
    assert _object_service_calls(ast.parse(src)) == []


# ---------------------------------------------------------------------------
# Identity-less production CRUD
# ---------------------------------------------------------------------------

def test_no_identity_less_objectservice_invocation_in_production():
    offenders = []
    for p in _py_files(*PRODUCTION_DIRS):
        for lineno, meth, kwargs, _ in _object_service_calls(
                _parse(p), in_service_module=(p.name == "object_service.py")):
            if kwargs & {"identity_id", "system_scope"}:
                continue
            if _rel(p) in AUDITED_IDENTITYLESS_FILES:
                continue
            offenders.append(f"{_rel(p)}:{lineno}: {meth}(...)")
    assert offenders == [], (
        "identity-less ObjectService invocation in production — identity is "
        f"mandatory for every user-scoped operation: {offenders}"
    )


def test_exactly_one_audited_identity_less_site_remains():
    hits = []
    for p in _py_files(*PRODUCTION_DIRS):
        for lineno, meth, kwargs, _ in _object_service_calls(
                _parse(p), in_service_module=(p.name == "object_service.py")):
            if not (kwargs & {"identity_id", "system_scope"}):
                hits.append((_rel(p), lineno, meth))
    assert len(hits) == 1, (
        "expected exactly ONE audited identity-less site (the offline "
        f"migration helper); found {hits}"
    )
    assert hits[0][0] in AUDITED_IDENTITYLESS_FILES, hits


# ---------------------------------------------------------------------------
# system_scope containment
# ---------------------------------------------------------------------------

def test_system_scope_true_in_exactly_one_audited_production_file():
    sites = []
    for p in _py_files(*PRODUCTION_DIRS):
        for lineno, _ in _system_scope_true_sites(_parse(p)):
            sites.append(f"{_rel(p)}:{lineno}")
    assert len(sites) == 1, f"unexpected system_scope=True sites: {sites}"
    assert sites[0].split(":")[0] in AUDITED_SYSTEM_SCOPE_FILES, sites


def test_audited_system_scope_is_not_request_reachable():
    """The single audited system-scope site must NOT sit in a request handler:
    it must not read the HTTP request or the session, and the enclosing function
    must not be a Flask route."""
    path = ROOT / sorted(AUDITED_SYSTEM_SCOPE_FILES)[0]
    tree = _parse(path)

    call_lines = [ln for ln, _ in _system_scope_true_sites(tree)]
    assert call_lines, "audited system-scope call no longer found"

    enclosing = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            if any(node.lineno <= ln <= end for ln in call_lines):
                enclosing.append(node)
    assert enclosing, "system-scope call is not inside a named function"

    for fn in enclosing:
        decorators = [ast.unparse(d) for d in fn.decorator_list]
        assert not any("route" in d for d in decorators), \
            f"{path.name}:{fn.name} is a route — system scope must not be request-reachable"
        names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
        assert "request" not in names and "session" not in names, (
            f"{path.name}:{fn.name} touches request/session — system scope must "
            "not be reachable from a user request"
        )


def test_tests_never_use_system_scope_to_grant_access():
    """A test may only mention system_scope=True as a CONTRADICTORY probe
    (identity_id present) that must be rejected — never as a way in."""
    offenders = []
    for p in _py_files("tests"):
        for lineno, has_identity in _system_scope_true_sites(_parse(p)):
            if not has_identity:
                offenders.append(f"{_rel(p)}:{lineno}")
    assert offenders == [], (
        "system_scope=True used WITHOUT identity_id in tests — that is an "
        f"authorization bypass, not a probe: {offenders}"
    )


def test_guard_still_flags_a_bare_system_scope():
    """Guard self-test: widening the identity keyword must NOT weaken it.

    A bare ``system_scope=True`` — identity_id or actor_identity_id absent —
    is exactly the bypass this guard exists to catch.
    """
    src_bare = "grant(WS, T, 'member', system_scope=True)\n"
    assert _system_scope_true_sites(ast.parse(src_bare)) == [(1, False)]

    src_probe = ("grant(WS, T, 'member', actor_identity_id=OWNER, "
                 "system_scope=True)\n")
    assert _system_scope_true_sites(ast.parse(src_probe)) == [(1, True)]


# ---------------------------------------------------------------------------
# Synthetic ownership containment
# ---------------------------------------------------------------------------

SYNTHETIC_WORKSPACE_PREFIX = "spc"
AUTHORIZATION_PATHS = ("app/authz", "app/objects", "core/object_service.py")


def test_no_synthetic_workspace_default_in_an_authorization_path():
    """No authorization path may fall back to a synthetic ``spc_*`` workspace
    (spc_default / spc_business / spc_personal / spc_custom), either as an ``or``
    fallback or as a default argument value."""
    offenders = []
    for target in AUTHORIZATION_PATHS:
        for p in _py_files(target):
            for node in ast.walk(_parse(p)):
                if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
                    for v in node.values:
                        if (isinstance(v, ast.Constant)
                                and isinstance(v.value, str)
                                and v.value.startswith(SYNTHETIC_WORKSPACE_PREFIX)):
                            offenders.append(f"{_rel(p)}:{node.lineno} or-fallback")
                if isinstance(node, ast.arguments):
                    defaults = list(node.defaults) + [
                        d for d in node.kw_defaults if d is not None]
                    for d in defaults:
                        if (isinstance(d, ast.Constant)
                                and isinstance(d.value, str)
                                and d.value.startswith(SYNTHETIC_WORKSPACE_PREFIX)):
                            offenders.append(
                                f"{_rel(p)}:{getattr(d, 'lineno', '?')} default-arg")
    assert offenders == [], (
        f"synthetic workspace used as an authorization default: {offenders}"
    )


def test_no_production_founderobject_write():
    """founder_objects is legacy: it must never regain a production write path."""
    offenders = []
    for p in _py_files(*PRODUCTION_DIRS):
        if p.name == "models.py" and "founder" in p.parts:
            continue  # the model definition itself is allowed
        for node in ast.walk(_parse(p)):
            if not isinstance(node, ast.Call):
                continue
            try:
                name = ast.unparse(node.func)
            except Exception:
                continue
            if name == "FounderObject" or name.endswith(".FounderObject"):
                offenders.append(f"{_rel(p)}:{node.lineno}")
    assert offenders == [], (
        f"production constructs FounderObject — legacy write path re-entering: {offenders}"
    )


def test_canonical_resolver_never_picks_a_membership_arbitrarily():
    """No authorization path may use ``.first()`` / ``.one_or_none()`` to CHOOSE
    an organization or workspace membership — neither in the canonical resolver
    nor in the RBAC decorator that every permission-gated route depends on."""
    offenders = []
    for rel in ("app/authz/workspace_context.py", "app/authz/decorators.py"):
        tree = _parse(ROOT / rel)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("first", "one_or_none")):
                try:
                    src = ast.unparse(node)
                except Exception:
                    continue
                if "OrgMember" in src or "ShWorkspaceMembership" in src:
                    offenders.append(f"{rel}:{node.lineno}: {src}")
    assert offenders == [], (
        f"authorization path selects a membership arbitrarily: {offenders}"
    )


# ---------------------------------------------------------------------------
# Batch E — the non-CRUD READ surfaces are authorization-gated too
# ---------------------------------------------------------------------------

READ_METHODS = {
    "get_by_object_id", "get_by_type", "list_by_workspace",
    "list_by_creator", "search", "count_by_type",
}


def _read_surface_calls(tree, in_service_module=False):
    """(lineno, method, kwargs) for real ObjectService read-surface calls."""
    found = []
    svc_names = {"svc"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            try:
                src = ast.unparse(node.value.func)
            except Exception:
                continue
            if "get_object_service" in src:
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        svc_names.add(t.id)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if not isinstance(f, ast.Attribute) or f.attr not in READ_METHODS:
            continue
        base = f.value
        ok = False
        if isinstance(base, ast.Name):
            ok = base.id in svc_names
            if base.id == "self" and in_service_module:
                ok = True
        elif isinstance(base, ast.Call):
            try:
                ok = "get_object_service" in ast.unparse(base.func)
            except Exception:
                ok = False
        if not ok:
            continue
        found.append((node.lineno, f.attr,
                      {k.arg for k in node.keywords if k.arg}))
    return found


def test_no_identity_less_read_surface_in_production():
    """Every production read surface must carry the caller's identity, so a
    read can never be wider than the CRUD write gate."""
    offenders = []
    for p in _py_files(*PRODUCTION_DIRS):
        for lineno, meth, kwargs in _read_surface_calls(
                _parse(p), in_service_module=(p.name == "object_service.py")):
            if p.name == "object_service.py":
                continue  # the service module is where the gate lives
            if "identity_id" not in kwargs:
                offenders.append(f"{_rel(p)}:{lineno}: {meth}(...)")
    assert offenders == [], (
        "identity-less ObjectService read surface in production: "
        f"{offenders}"
    )


def test_service_read_surfaces_require_identity():
    """Structurally: each read surface must consult the identity gate, and must
    never fall back to an unscoped query when the identity is absent."""
    tree = _parse(ROOT / "core/object_service.py")
    required = {
        "get_by_object_id", "get_by_type", "list_by_workspace",
        "list_by_creator", "search", "count_by_type",
    }
    seen = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in required:
            seen[node.name] = ast.unparse(node)
    assert set(seen) == required, f"missing read surfaces: {required - set(seen)}"
    for name, body in seen.items():
        assert "_authorized_scope(" in body, (
            f"ObjectService.{name}() does not consult the canonical identity gate"
        )
    # And the gate itself must fail closed on a missing identity/organization.
    gate = next(n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == "_authorized_scope")
    gate_src = ast.unparse(gate)
    assert "raise ValueError" in gate_src
    assert "authorized_workspace_ids" in gate_src
    assert "OwnershipContextError" in gate_src
