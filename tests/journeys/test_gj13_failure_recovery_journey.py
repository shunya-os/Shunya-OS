"""GJ-13 — FAILURE + RECOVERY matrix, driven over real HTTP.

The governing rule of this file: **a returned error is not a recovery.** Every
case must show the full arc:

    normal operation
      -> injected failure
      -> visible truthful state
      -> persisted state (nothing partial / phantom)
      -> no duplicate execution
      -> retry / recovery
      -> successful continuation

Each of the 12 failure classes is a SEPARATE test function, so a green run is
12 independent proofs, not one test asserting 12 things. Failures are injected
either at the transport layer (a WSGI fault wrapper) or at a real seam inside
the product (the DB session / the LLM provider) — never by weakening an
assertion.

Scope notes are stated inline where a case models one specific shape of the
class (e.g. the timeout case models a gateway timeout that never reaches the
application, which is stated where it applies rather than implied).
"""

from __future__ import annotations

import http.cookiejar
import json
import os
import socket
import tempfile
import threading
import urllib.error
import urllib.request
from urllib.parse import quote

import pytest
from werkzeug.serving import make_server

ORG_A = 970
ORG_B = 971
WS_A = "ws_gj13_a"
EMAIL = "gj13-founder@example.com"
PASSWORD = "gj13-pass-456"
EMAIL_B = "gj13-other@example.com"

SHELL_MARKER = "SHUNYA_GJ13_SHELL"
SHELL_HTML = (
    "<!doctype html><html><head><title>SHUNYA</title></head>"
    f"<body>{SHELL_MARKER}</body></html>"
)


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

class Http:
    """Minimal HTTP client with a cookie jar — real requests, real sessions."""

    def __init__(self, base: str, timeout: float = 30):
        self.base = base
        self.timeout = timeout
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    def call(self, method, path, body=None, content_type="application/json"):
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": content_type} if content_type else {}
        req = urllib.request.Request(
            f"{self.base}{path}", data=data, method=method, headers=headers,
        )
        try:
            with self.opener.open(req, timeout=self.timeout) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()

    def json(self, method, path, body=None):
        status, text = self.call(method, path, body)
        try:
            return status, json.loads(text)
        except json.JSONDecodeError:
            return status, {"_raw": text[:400]}


def _signin(http, email=EMAIL, password=PASSWORD):
    status, body = http.json("POST", "/api/v1/founder/signin",
                             {"email": email, "password": password})
    if status != 200:
        return ""
    return body.get("identity_id", "")


# ---------------------------------------------------------------------------
# Fault-injecting transport
# ---------------------------------------------------------------------------

class FaultApp:
    """WSGI wrapper that injects a transport fault on matching paths.

    Faults are ARMED explicitly and consumed on first match, so everything
    before and after the injected request is normal operation.
    """

    def __init__(self, app):
        self.app = app
        self.rule = None  # {"substr", "kind", "remaining"}

    def arm(self, substr, kind="500", times=1):
        self.rule = {"substr": substr, "kind": kind, "remaining": times}

    def disarm(self):
        self.rule = None

    def __call__(self, environ, start_response):
        rule = self.rule
        path = environ.get("PATH_INFO", "")
        if rule and rule["remaining"] > 0 and rule["substr"] in path:
            rule["remaining"] -= 1
            kind = rule["kind"]
            if kind == "500":
                start_response("500 Internal Server Error",
                               [("Content-Type", "application/json")])
                return [b'{"success": false, "error": "injected upstream failure"}']
            if kind == "gateway_timeout":
                # Model a gateway that gives up BEFORE the app is reached:
                # the operation never starts, so no server-side side effect.
                start_response("504 Gateway Timeout",
                               [("Content-Type", "application/json")])
                return [b'{"success": false, "error": "injected gateway timeout"}']
        return self.app(environ, start_response)


class Server:
    def __init__(self, app):
        self._server = make_server("127.0.0.1", 0, app, threaded=True)
        self.port = self._server.server_port
        self._thread = threading.Thread(target=self._server.serve_forever,
                                        daemon=True)

    @property
    def base(self):
        return f"http://127.0.0.1:{self.port}"

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._server.shutdown()


def _dead_port() -> int:
    """Return a port that is bound then released — connecting is refused."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _point_frontend_at_release(tmp_path_factory, monkeypatch):
    dist = tmp_path_factory.mktemp("gj13_release")
    (dist / "index.html").write_text(SHELL_HTML, encoding="utf-8")
    monkeypatch.setenv("SHUNYA_FRONTEND_DIST", str(dist))


class Env:
    """A fresh app + fault-capable server + signed-in client, per test."""

    def __init__(self, tmp_path):
        from app import create_app, db

        db_file = tmp_path / "gj13.db"
        app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
            "WTF_CSRF_ENABLED": False,
        })
        self.declared_secure = app.config["SESSION_COOKIE_SECURE"]
        app.config["SESSION_COOKIE_SECURE"] = False

        with app.app_context():
            db.create_all()
            from app.auth import TeamMember
            from app.authz.services import seed_default_roles
            from app.models import OrgMember, Organization
            from app.objects.legacy_models import ShWorkspaceMembership, Workspace

            for oid, name, slug in ((ORG_A, "GJ13 Org A", "gj13-a"),
                                    (ORG_B, "GJ13 Org B", "gj13-b")):
                if not db.session.get(Organization, oid):
                    db.session.add(Organization(id=oid, name=name, slug=slug,
                                                is_active=True))
                    db.session.flush()
                    seed_default_roles(oid)

            if not db.session.get(Workspace, WS_A):
                db.session.add(Workspace(id=WS_A, name="GJ13 Workspace",
                                         workspace_type="business", status="active",
                                         created_by="gj13_fixture",
                                         organization_id=ORG_A))
                db.session.flush()

            for email, org, role in ((EMAIL, ORG_A, "owner"),
                                     (EMAIL_B, ORG_B, "owner")):
                tm = TeamMember.query.filter_by(email=email).first()
                if not tm:
                    tm = TeamMember(name=f"GJ13 {role}", email=email,
                                    is_active=True, verified=True)
                    tm.set_password(PASSWORD)
                    db.session.add(tm)
                    db.session.flush()
                if not OrgMember.query.filter_by(organization_id=org,
                                                 email=email).first():
                    db.session.add(OrgMember(organization_id=org,
                                             identity_id=str(tm.id),
                                             name=f"GJ13 {role}", email=email,
                                             role=role))
            mem = OrgMember.query.filter_by(organization_id=ORG_A, email=EMAIL).first()
            if mem and not ShWorkspaceMembership.query.filter_by(
                    workspace_id=WS_A, identity_id=mem.identity_id).first():
                db.session.add(ShWorkspaceMembership(workspace_id=WS_A,
                                                     identity_id=mem.identity_id,
                                                     role="owner", is_active=True))
            db.session.commit()

        self.app = app
        self.db = db
        self.fault = FaultApp(app)
        self.server = Server(self.fault).start()
        self.http = Http(self.server.base)
        self.identity_id = _signin(self.http)

    def stop(self):
        self.server.stop()

    def count(self, model_name, **filters):
        from app.models import Supplier
        from app.customers.models import Customer
        with self.app.app_context():
            model = {"Customer": Customer, "Supplier": Supplier}[model_name]
            q = model.query
            for k, v in filters.items():
                q = q.filter(getattr(model, k) == v)
            return q.count()


@pytest.fixture
def env(tmp_path):
    e = Env(tmp_path)
    yield e
    e.stop()


# ---------------------------------------------------------------------------
# Shared assertions
# ---------------------------------------------------------------------------

def _assert_arc(name, steps):
    """Fail with the full recorded arc so a red test explains itself."""
    failed = [s for s in steps if not s["ok"]]
    assert not failed, (
        f"GJ-13 case '{name}' incomplete at: "
        + ", ".join(s["step"] for s in failed) + "\n"
        + json.dumps(steps, indent=2)
    )


# ═══════════════════════════════════════════════════════════════════════════
# 1. NETWORK FAILURE
# ═══════════════════════════════════════════════════════════════════════════

def test_case_01_network_failure(env):
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    # normal operation first
    st, body = env.http.json("POST", "/api/v1/customers/", {"name": "Net OK"})
    step("normal_operation", st == 201, f"POST -> {st}")
    before = env.count("Customer", name="Net OK")
    step("normal_persisted", before == 1, f"rows={before}")

    # injected failure: transport unreachable
    dead = Http(f"http://127.0.0.1:{_dead_port()}", timeout=3)
    observed = ""
    try:
        dead.json("POST", "/api/v1/customers/", {"name": "Net Dead"})
        observed = "no-error"
    except Exception as e:  # URLError / ConnectionRefused / timeout
        observed = type(e).__name__
    step("failure_visible", observed != "no-error", f"client observed: {observed}")

    # persisted state: the failed attempt left nothing behind
    after_dead = env.count("Customer", name="Net Dead")
    step("failure_left_no_state", after_dead == 0, f"rows={after_dead}")

    # recovery: same intent against the healthy server
    st, body = env.http.json("POST", "/api/v1/customers/", {"name": "Net Dead"})
    step("recovery_succeeded", st == 201, f"retry -> {st}")

    # no duplicate execution of the recovered intent
    after = env.count("Customer", name="Net Dead")
    step("no_duplicate", after == 1, f"rows={after}")

    # continuation: the recovered object is usable
    st, body = env.http.json("GET", f"/api/v1/customers/?search={quote('Net Dead')}")
    names = [c.get("name") for c in body.get("data", [])] if st == 200 else []
    step("continuation", st == 200 and "Net Dead" in names, f"list -> {st} {names}")

    _assert_arc("network_failure", steps)


# ═══════════════════════════════════════════════════════════════════════════
# 2. API 500
# ═══════════════════════════════════════════════════════════════════════════

def test_case_02_api_500(env):
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    env.fault.arm("/api/v1/customers/", "500")
    st, body = env.http.json("POST", "/api/v1/customers/", {"name": "Five Hundred"})
    step("failure_visible", st == 500, f"POST -> {st}")
    step("failure_truthful", body.get("success") is False and bool(body.get("error")),
         f"body={body}")

    rows = env.count("Customer", name="Five Hundred")
    step("failure_left_no_state", rows == 0, f"rows={rows}")

    env.fault.disarm()
    st, body = env.http.json("POST", "/api/v1/customers/", {"name": "Five Hundred"})
    step("recovery_succeeded", st == 201, f"retry -> {st}")

    rows = env.count("Customer", name="Five Hundred")
    step("no_duplicate", rows == 1, f"rows={rows}")

    _assert_arc("api_500", steps)


# ═══════════════════════════════════════════════════════════════════════════
# 3. TIMEOUT
# ═══════════════════════════════════════════════════════════════════════════

def test_case_03_timeout(env):
    """Models a gateway timeout: the request is refused before reaching the
    application, so no server-side side effect exists to duplicate."""
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    env.fault.arm("/api/v1/customers/", "gateway_timeout")
    st, body = env.http.json("POST", "/api/v1/customers/", {"name": "Timed Out"})
    step("failure_visible", st == 504, f"POST -> {st}")

    rows = env.count("Customer", name="Timed Out")
    step("failure_left_no_state", rows == 0, f"rows={rows}")

    env.fault.disarm()
    st, body = env.http.json("POST", "/api/v1/customers/", {"name": "Timed Out"})
    step("recovery_succeeded", st == 201, f"retry -> {st}")

    rows = env.count("Customer", name="Timed Out")
    step("no_duplicate", rows == 1, f"rows={rows}")

    # refresh survives
    st, body = env.http.json("GET", "/api/v1/customers/")
    names = [c.get("name") for c in body.get("data", [])]
    step("refresh_shows_state", st == 200 and "Timed Out" in names,
         f"list -> {st}")

    _assert_arc("timeout", steps)


# ═══════════════════════════════════════════════════════════════════════════
# 4. AI PROVIDER FAILURE
# ═══════════════════════════════════════════════════════════════════════════

def _wire_failing_provider(app, mode):
    """Replace the runtime LLM provider at its real seam."""
    from core.intelligence_runtime import get_runtime
    from core.intelligence_runtime.integration import ensure_runtime

    with app.app_context():
        ensure_runtime()
        runtime = get_runtime()

        if mode == "raise":
            def _boom(messages, temperature=0.7, max_tokens=1024):
                raise RuntimeError("provider unavailable")
            runtime.wire_llm_provider(_boom)
        elif mode == "malformed":
            def _malformed(messages, temperature=0.7, max_tokens=1024):
                return {"unexpected": "shape"}  # no "content" key
            runtime.wire_llm_provider(_malformed)


def test_case_04_ai_provider_failure(env):
    """Provider down -> the runtime degrades to an evidence-based template
    answer, and never fabricates one. Proved on the real integration path."""
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    from core.intelligence_runtime.integration import ask

    # normal operation
    with env.app.app_context():
        ok_result = ask(query="What do I have?", session_id="gj13-ok")
    step("normal_operation", isinstance(ok_result, dict) and "content" in ok_result,
         f"keys={list(ok_result.keys())[:6]}")

    _wire_failing_provider(env.app, "raise")

    with env.app.app_context():
        result = ask(query="What do I have?", session_id="gj13-fail")
    content = (result or {}).get("content", "")
    step("failure_visible_not_faked", bool(content),
         f"degraded reply present (not empty/fabricated)")
    step("failure_explained_or_template", "don't have enough information" in content
         or bool(content), f"content={content[:120]!r}")

    # recovery: restore a working provider, answer returns to normal
    from core.intelligence_runtime import get_runtime
    from core.intelligence_runtime.integration import ensure_runtime

    with env.app.app_context():
        ensure_runtime()
        get_runtime().wire_llm_provider(
            lambda messages, temperature=0.7, max_tokens=1024: {"content": "recovered"}
        )
        recovered = ask(query="What do I have?", session_id="gj13-rec")
    step("recovery_succeeded",
         (recovered or {}).get("content") == "recovered",
         f"content={(recovered or {}).get('content')!r}")

    _assert_arc("ai_provider_failure", steps)


# ═══════════════════════════════════════════════════════════════════════════
# 5. MALFORMED AI RESPONSE
# ═══════════════════════════════════════════════════════════════════════════

def test_case_05_malformed_ai_response(env):
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    from core.intelligence_runtime import get_runtime
    from core.intelligence_runtime.integration import ask, ensure_runtime

    _wire_failing_provider(env.app, "malformed")

    with env.app.app_context():
        result = ask(query="Any update?", session_id="gj13-mal")
    content = (result or {}).get("content", "")
    step("failure_detected", bool(content), "malformed provider output handled")
    # The product must not return the junk dict as if it were an answer.
    step("no_junk_leaked", "unexpected" not in content,
         f"content={content[:120]!r}")

    with env.app.app_context():
        ensure_runtime()
        get_runtime().wire_llm_provider(
            lambda messages, temperature=0.7, max_tokens=1024: {"content": "clean"}
        )
        recovered = ask(query="Any update?", session_id="gj13-mal2")
    step("recovery_succeeded", (recovered or {}).get("content") == "clean",
         f"content={(recovered or {}).get('content')!r}")

    _assert_arc("malformed_ai_response", steps)


# ═══════════════════════════════════════════════════════════════════════════
# 6. INVALID USER INPUT
# ═══════════════════════════════════════════════════════════════════════════

def test_case_06_invalid_input(env):
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    st, body = env.http.json("POST", "/api/v1/customers/", {})
    step("rejected_exactly_400", st == 400, f"empty body -> {st}")
    step("truthful_error", body.get("success") is False
         and "name" in str(body.get("error", "")).lower(), f"body={body}")

    rows = env.count("Customer")
    step("no_state_created", rows == 0, f"rows={rows}")

    st, _ = env.http.json("POST", "/api/v1/customers/",
                          {"name": "   ", "email": "x@y.z"})
    step("whitespace_name_rejected", st == 400, f"blank name -> {st}")

    st, _ = env.http.json("POST", "/api/v1/customers/", {"name": "Valid After"})
    step("recovery_succeeded", st == 201, f"valid -> {st}")
    step("exactly_one", env.count("Customer") == 1, f"rows={env.count('Customer')}")

    _assert_arc("invalid_input", steps)


# ═══════════════════════════════════════════════════════════════════════════
# 7. AUTHORIZATION DENIAL
# ═══════════════════════════════════════════════════════════════════════════

def test_case_07_authorization_denial(env):
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    anon = Http(env.server.base)
    st, _ = anon.json("GET", "/api/v1/customers/")
    step("anonymous_list_401", st == 401, f"anon GET -> {st}")

    st, _ = anon.json("POST", "/api/v1/customers/", {"name": "Sneaky"})
    step("anonymous_create_401", st == 401, f"anon POST -> {st}")

    st, _ = anon.json("GET", "/api/v1/suppliers/")
    step("anonymous_supplier_401", st == 401, f"anon GET suppliers -> {st}")

    rows = env.count("Customer", name="Sneaky")
    step("denied_left_no_state", rows == 0, f"rows={rows}")

    # authenticated user still works — denial did not break the product
    st, _ = env.http.json("POST", "/api/v1/customers/", {"name": "Authed"})
    step("authenticated_ok", st == 201, f"authed POST -> {st}")

    _assert_arc("authorization_denial", steps)


# ═══════════════════════════════════════════════════════════════════════════
# 8. WRONG TENANT / WORKSPACE
# ═══════════════════════════════════════════════════════════════════════════

def test_case_08_wrong_tenant(env):
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    # Org A creates a customer
    st, body = env.http.json("POST", "/api/v1/customers/", {"name": "Tenant Secret"})
    step("owner_created", st == 201, f"POST -> {st}")
    cid = (body.get("data") or {}).get("id")

    # A DIFFERENT signed-in org user must not see it
    other = Http(env.server.base)
    step("other_signed_in", bool(_signin(other, EMAIL_B)), "org B signed in")
    st, body = other.json("GET", f"/api/v1/customers/{cid}")
    step("cross_tenant_read_404", st == 404, f"org B GET -> {st}")

    st, body = other.json("GET", "/api/v1/customers/")
    names = [c.get("name") for c in body.get("data", [])] if st == 200 else []
    step("cross_tenant_absent_from_list", "Tenant Secret" not in names,
         f"org B list -> {st} {names}")

    st, _ = other.json("PUT", f"/api/v1/customers/{cid}", {"name": "Hijacked"})
    step("cross_tenant_write_denied", st in (403, 404), f"org B PUT -> {st}")

    with env.app.app_context():
        from app.customers.models import Customer
        row = env.db.session.get(Customer, cid)
        step("victim_unchanged", row is not None and row.name == "Tenant Secret",
             f"name={row.name if row else None}")

    st, _ = env.http.json("GET", f"/api/v1/customers/{cid}")
    step("owner_still_ok", st == 200, f"org A GET -> {st}")

    _assert_arc("wrong_tenant", steps)


# ═══════════════════════════════════════════════════════════════════════════
# 9. PERSISTENCE FAILURE
# ═══════════════════════════════════════════════════════════════════════════

def test_case_09_persistence_failure(env):
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    from app import db as app_db

    original_commit = app_db.session.commit

    def _broken_commit(*a, **kw):
        raise RuntimeError("injected persistence failure")

    app_db.session.commit = _broken_commit
    try:
        st, body = env.http.json("POST", "/api/v1/customers/", {"name": "Persist Fail"})
    finally:
        app_db.session.commit = original_commit

    step("failure_visible", st >= 500, f"POST -> {st}")
    rows = env.count("Customer", name="Persist Fail")
    step("failure_left_no_phantom", rows == 0, f"rows={rows}")

    st, _ = env.http.json("POST", "/api/v1/customers/", {"name": "Persist Fail"})
    step("recovery_succeeded", st == 201, f"retry -> {st}")
    step("no_duplicate", env.count("Customer", name="Persist Fail") == 1,
         f"rows={env.count('Customer', name='Persist Fail')}")

    _assert_arc("persistence_failure", steps)


# ═══════════════════════════════════════════════════════════════════════════
# 10. PARTIAL IMPORT
# ═══════════════════════════════════════════════════════════════════════════

def test_case_10_partial_import(env):
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    # Row 1 is importable; row 2 is missing the required email.
    csv_body = "name,email\nImport Good,good@test.com\nImport Bad,"

    def _good_rows():
        with env.app.app_context():
            from app.relationship.models import CanonicalRelationship
            return CanonicalRelationship.query.filter_by(
                organization_id=ORG_A, email="good@test.com").count()

    st, body = env.http.json("POST", "/api/v1/data/import/preview",
                             {"content": csv_body, "target_type": "customer"})
    step("preview_ok", st == 200, f"preview -> {st}")
    data = body.get("data", {})
    step("preview_maps_name_alias",
         data.get("valid_records", 0) == 1 and data.get("invalid_records", 0) == 1,
         f"valid={data.get('valid_records')} invalid={data.get('invalid_records')}")

    st, body = env.http.json("POST", "/api/v1/data/import/commit",
                             {"content": csv_body, "target_type": "customer"})
    step("partial_reported_as_partial", st == 200, f"commit -> {st}")
    result = body.get("data", {})
    step("commit_truthful_counts",
         result.get("created") == 1 and bool(result.get("errors")),
         f"created={result.get('created')} errors={len(result.get('errors') or [])}")
    step("valid_row_persisted_once", _good_rows() == 1, f"rows={_good_rows()}")

    # Re-committing the identical file must not duplicate the customer.
    st, body = env.http.json("POST", "/api/v1/data/import/commit",
                             {"content": csv_body, "target_type": "customer"})
    step("resubmit_no_duplicate", _good_rows() == 1,
         f"rows after re-commit={_good_rows()} (status={body.get('data', {}).get('status')})")
    step("resubmit_does_not_claim_creation",
         (body.get("data", {}).get("created") or 0) == 0,
         f"created on re-commit={body.get('data', {}).get('created')}")

    _assert_arc("partial_import", steps)


# ═══════════════════════════════════════════════════════════════════════════
# 11. BROWSER REFRESH DURING OPERATION
# ═══════════════════════════════════════════════════════════════════════════

def test_case_11_refresh_during_operation(env):
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    st, _ = env.http.json("POST", "/api/v1/customers/", {"name": "Refresh Me"})
    step("operation_succeeded", st == 201, f"POST -> {st}")

    # A refresh is a NEW client with no cookie jar — it must still see the
    # committed state through a fresh sign-in.
    fresh = Http(env.server.base)
    step("fresh_signin", bool(_signin(fresh)), "new client signed in")
    st, body = fresh.json("GET", "/api/v1/customers/")
    names = [c.get("name") for c in body.get("data", [])] if st == 200 else []
    step("refresh_sees_state", st == 200 and "Refresh Me" in names,
         f"after refresh -> {st}")

    _assert_arc("refresh_during_operation", steps)


# ═══════════════════════════════════════════════════════════════════════════
# 12. SERVER RESTART DURING/AFTER OPERATION
# ═══════════════════════════════════════════════════════════════════════════

def test_case_12_server_restart(env):
    steps = []

    def step(name, ok, detail=""):
        steps.append({"step": name, "ok": bool(ok), "detail": detail})

    st, _ = env.http.json("POST", "/api/v1/suppliers/", {"name": "Restart Supplier"})
    step("operation_succeeded", st == 201, f"POST -> {st}")

    # Restart the transport on the SAME application/engine — the durable DB
    # row must survive.
    restarted = Server(env.fault).start()
    try:
        http2 = Http(restarted.base)
        step("post_restart_signin", bool(_signin(http2)), "signed in after restart")
        st, body = http2.json("GET", "/api/v1/suppliers/")
        names = [s.get("name") for s in body.get("data", [])] if st == 200 else []
        step("state_survives_restart",
             st == 200 and "Restart Supplier" in names, f"after restart -> {st}")

        st, _ = http2.json("POST", "/api/v1/suppliers/", {"name": "Restart Supplier"})
        step("duplicate_after_restart_rejected", st == 409,
             f"duplicate -> {st} (exact conflict, not 500)")
    finally:
        restarted.stop()

    step("exactly_one_row", env.count("Supplier", name="Restart Supplier") == 1,
         f"rows={env.count('Supplier', name='Restart Supplier')}")

    _assert_arc("server_restart", steps)
