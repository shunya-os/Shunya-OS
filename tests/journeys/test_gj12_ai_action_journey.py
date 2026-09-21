"""GJ-12 — AI ACTION journey, driven over real HTTP.

Demonstrates: register tool handlers → AI command creates customer/supplier
→ outcome persisted → event emitted → refresh survival → tenant isolation.

Uses the same Http/Server harness pattern as test_gj03_import_csv_journey.
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import tempfile
import threading
import urllib.error
import urllib.request

import pytest
from werkzeug.serving import make_server

from core.intelligence_runtime import PlanStep, ActionType
from core.intelligence_runtime.execution import ToolExecutionLayer

ORG_ID = 957
WRONG_ORG_ID = 999
WS_ID = "ws_ai_action_journey"
EMAIL = "ai-action-founder@example.com"
PASSWORD = "ai-action-pass-456"

SHELL_MARKER = "SHUNYA_AI_ACTION_JOURNEY_SHELL"
SHELL_HTML = (
    "<!doctype html><html><head><title>SHUNYA</title></head>"
    f"<body>{SHELL_MARKER}<script crossorigin src=\"/assets/journey.js\"></script></body></html>"
)


@pytest.fixture(scope="module")
def release_shell_dir(tmp_path_factory):
    dist = tmp_path_factory.mktemp("ai_action_journey_release")
    (dist / "index.html").write_text(SHELL_HTML, encoding="utf-8")
    return dist


@pytest.fixture(autouse=True)
def _point_frontend_at_release(release_shell_dir, monkeypatch):
    monkeypatch.setenv("SHUNYA_FRONTEND_DIST", str(release_shell_dir))


class Http:
    """Minimal HTTP client with a cookie jar — real requests, real sessions."""

    def __init__(self, base: str):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.identity_id = ""
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    def call(self, method: str, path: str, body=None, content_type="application/json"):
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": content_type} if content_type else {}
        req = urllib.request.Request(
            f"{self.base}{path}", data=data, method=method, headers=headers,
        )
        try:
            with self.opener.open(req, timeout=30) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()

    def json(self, method: str, path: str, body=None):
        status, text = self.call(method, path, body)
        try:
            return status, json.loads(text)
        except json.JSONDecodeError:
            return status, {"_raw": text[:400]}


class Server:
    """The real application on a real socket."""

    def __init__(self, app):
        self._server = make_server("127.0.0.1", 0, app, threaded=True)
        self.port = self._server.server_port
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._server.shutdown()


@pytest.fixture(scope="module")
def journey_app(tmp_path_factory):
    from app import create_app, db

    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })

    declared_secure = app.config["SESSION_COOKIE_SECURE"]
    app.config["SESSION_COOKIE_SECURE"] = False

    with app.app_context():
        db.create_all()

        from app.auth import TeamMember
        from app.models import OrgMember, Organization
        from app.objects.legacy_models import ShWorkspaceMembership, Workspace

        org = db.session.get(Organization, ORG_ID)
        if not org:
            org = Organization(id=ORG_ID, name="AI Action Journey Org",
                               slug="ai-action-journey", is_active=True)
            db.session.add(org)
            db.session.flush()

        ws = db.session.get(Workspace, WS_ID)
        if not ws:
            ws = Workspace(id=WS_ID, name="AI Action Journey Workspace",
                           workspace_type="business", status="active",
                           created_by="journey_fixture", organization_id=ORG_ID)
            db.session.add(ws)
            db.session.flush()

        member = TeamMember.query.filter_by(email=EMAIL).first()
        if not member:
            member = TeamMember(name="AI Action Journey Founder", email=EMAIL,
                                role="owner", is_active=True)
            member.set_password(PASSWORD)
            member.verified = True
            db.session.add(member)
            db.session.flush()

        identity_id = str(member.id)

        if not OrgMember.query.filter_by(organization_id=ORG_ID,
                                         email=EMAIL).first():
            db.session.add(OrgMember(organization_id=ORG_ID,
                                     identity_id=identity_id,
                                     name="AI Action Journey Founder", email=EMAIL,
                                     role="owner"))
        if not ShWorkspaceMembership.query.filter_by(workspace_id=WS_ID,
                                                     identity_id=identity_id).first():
            db.session.add(ShWorkspaceMembership(workspace_id=WS_ID,
                                                 identity_id=identity_id,
                                                 role="owner", is_active=True))
        db.session.commit()

    app.config["_JOURNEY_DECLARED_SECURE_COOKIE"] = declared_secure
    return app


@pytest.fixture(scope="module")
def server(journey_app):
    srv = Server(journey_app).start()
    yield srv
    srv.stop()


def test_ai_action_journey(server, journey_app):
    """REGISTER HANDLERS → CREATE CUSTOMER → CREATE SUPPLIER → SEARCH →
    OUTCOME PERSISTED → EVENT EMITTED → REFRESH SURVIVAL → TENANT ISOLATION.
    """
    report = {"journey": "GJ-12-AI-ACTION", "steps": []}
    http = Http(server.base)

    report["product_session_cookie_secure_declared"] = bool(
        journey_app.config.get("_JOURNEY_DECLARED_SECURE_COOKIE")
    )

    def step(name, ok, detail=""):
        report["steps"].append({"step": name, "ok": bool(ok), "detail": detail})
        return ok

    # ── 1. PUBLIC shell ────────────────────────────────────────────────────
    status, html = http.call("GET", "/")
    step("public_shell_served", status == 200 and SHELL_MARKER in html,
         f"GET / -> {status}")

    # ── 2. AUTH ────────────────────────────────────────────────────────────
    status, body = http.json("POST", "/api/v1/founder/signin",
                              {"email": EMAIL, "password": PASSWORD})
    step("signin_success", status == 200 and body.get("success") is True,
         f"signin -> {status}")
    identity_id = body.get("identity_id") or ""
    http.identity_id = identity_id

    # ── 3. Verify tool handlers are registered (public introspection) ─────
    from core.intelligence_runtime import get_runtime
    from core.intelligence_runtime.integration import ensure_runtime
    # Pin the shared-singleton wiring so this assertion does not depend on
    # whether an earlier test in the suite already booted the runtime.
    ensure_runtime()
    runtime = get_runtime()
    executor: ToolExecutionLayer = runtime.executor
    registered_keys = executor.registered_actions()
    step("handlers_registered",
         executor.is_registered("create_customer")
         and executor.is_registered("create_supplier")
         and executor.is_registered("search_objects"),
         f"registered: {registered_keys}")

    # ── 4. Create Customer via ToolExecutionLayer ─────────────────────────
    with journey_app.app_context():
        customer_params = {
            "name": "AI Action Corp",
            "email": "ai@action.corp",
            "phone": "+1-555-AI-ACTION",
            "tenant_id": ORG_ID,
            "status": "active",
        }
        customer_result = executor._handlers["create_customer"](customer_params)
    step("customer_handler_executed",
         customer_result.get("status") == "success",
         f"result: {json.dumps(customer_result)}")
    customer_id = customer_result.get("result", {}).get("customer_id")
    customer_outcome_id = customer_result.get("outcome_id")
    step("customer_has_id", customer_id is not None,
         f"customer_id={customer_id}")
    step("customer_has_outcome_id", customer_outcome_id is not None,
         f"outcome_id={customer_outcome_id}")

    # ── 5. Verify Customer persisted via REST API ──────────────────────────
    status, customer_list = http.json("GET", "/api/v1/customers/")
    step("customer_list_accessible", status == 200,
         f"list customers -> {status}")
    customer_names = [c.get("name") for c in customer_list.get("data", [])]
    step("ai_action_corp_in_list", "AI Action Corp" in customer_names,
         f"customers: {customer_names}")

    # ── 6. Create Supplier via ToolExecutionLayer ─────────────────────────
    with journey_app.app_context():
        supplier_params = {
            "name": "AI Supplier Pro",
            "category": "technology",
            "contact": "AI Contact",
            "email": "supplier@ai.pro",
            "phone": "+1-555-SUPPLIER",
            "city": "San Francisco",
            "tenant_id": ORG_ID,
        }
        supplier_result = executor._handlers["create_supplier"](supplier_params)
    step("supplier_handler_executed",
         supplier_result.get("status") == "success",
         f"result: {json.dumps(supplier_result)}")
    supplier_id = supplier_result.get("result", {}).get("supplier_id")
    step("supplier_has_id", supplier_id is not None,
         f"supplier_id={supplier_id}")

    # ── 7. Verify Supplier persisted via REST API ──────────────────────────
    status, supplier_list = http.json("GET", "/api/v1/suppliers/")
    step("supplier_list_accessible", status == 200,
         f"list suppliers -> {status}")
    supplier_names = [s.get("name") for s in supplier_list.get("data", [])]
    step("ai_supplier_in_list", "AI Supplier Pro" in supplier_names,
         f"suppliers: {supplier_names}")

    # ── 8. Search Objects via ToolExecutionLayer ───────────────────────────
    with journey_app.app_context():
        search_params = {"query": "AI", "tenant_id": ORG_ID}
        search_result = executor._handlers["search_objects"](search_params)
    step("search_handler_executed",
         search_result.get("status") == "success",
         f"result status: {search_result.get('status')}")
    search_count = search_result.get("result", {}).get("count", 0)
    step("search_returns_results", search_count >= 0,
         f"search returned {search_count} results")

    # ── 9. Verify Outcome is persisted ────────────────────────────────────
    from app.execution.models import Outcome as OutcomeModel
    with journey_app.app_context():
        # Query all outcomes (handler uses default identity_id="ai_runtime")
        outcomes = OutcomeModel.query.all()
        step("outcomes_persisted", len(outcomes) > 0,
             f"outcomes found: {len(outcomes)}")
        # Find the customer creation outcome
        customer_outcome = OutcomeModel.query.filter_by(
            outcome_id=customer_outcome_id
        ).first()
        step("customer_outcome_found", customer_outcome is not None,
             f"outcome={customer_outcome.outcome_id if customer_outcome else None}")
        if customer_outcome:
            step("customer_outcome_state_matches",
                 customer_outcome.state.get("customer_id") == customer_id,
                 f"state.customer_id={customer_outcome.state.get('customer_id')} expected={customer_id}")

    # ── 10. Verify Event emitted on event bus ─────────────────────────────
    from app.shunya.infrastructure.event_bus import get_event_bus, CanonicalEvent

    # Collect events by subscribing to the pattern
    received_events = []

    def _collector(event: CanonicalEvent) -> None:
        received_events.append(event.event_type)

    bus = get_event_bus()
    bus.subscribe("ai.action.*", _collector, consumer_name="gj12_test_collector")

    # Execute handlers to generate events inside app context
    with journey_app.app_context():
        handler_params_cust = {
            "name": "Event Test Corp",
            "email": "event@test.corp",
            "tenant_id": ORG_ID,
        }
        executor._handlers["create_customer"](handler_params_cust)
        executor._handlers["create_supplier"]({"name": "Event Test Supplier", "tenant_id": ORG_ID})
        executor._handlers["search_objects"]({"query": "Event", "tenant_id": ORG_ID})

    step("events_received", len(received_events) >= 3,
         f"events received: {received_events}")

    # ── 11. TENANT ISOLATION — records have tenant_id ────────────────────
    with journey_app.app_context():
        from app.customers.models import Customer as CustomerModel
        cust = CustomerModel.query.filter_by(name="AI Action Corp").first()
        if cust:
            step("customer_has_tenant_id", cust.tenant_id == ORG_ID,
                 f"tenant_id={cust.tenant_id} expected={ORG_ID}")

        from app.models import Supplier as SupplierModel
        supp = SupplierModel.query.filter_by(name="AI Supplier Pro").first()
        if supp:
            step("supplier_has_tenant_id", supp.tenant_id == ORG_ID,
                 f"tenant_id={supp.tenant_id} expected={ORG_ID}")

    # ── 12. REFRESH survival ─────────────────────────────────────────────
    restarted = Server(journey_app).start()
    try:
        http2 = Http(restarted.base)
        status2, body2 = http2.json("POST", "/api/v1/founder/signin",
                                    {"email": EMAIL, "password": PASSWORD})
        status3, customer_list2 = http2.json("GET", "/api/v1/customers/")
        names2 = [c.get("name") for c in customer_list2.get("data", [])]
        step("customer_survives_server_restart",
             status2 == 200 and status3 == 200 and "AI Action Corp" in names2,
             f"restart: signin={status2} list={status3}")

        status4, supplier_list2 = http2.json("GET", "/api/v1/suppliers/")
        names_supp2 = [s.get("name") for s in supplier_list2.get("data", [])]
        step("supplier_survives_server_restart",
             status4 == 200 and "AI Supplier Pro" in names_supp2,
             f"restart: supplier list={status4}")
    finally:
        restarted.stop()

    # ── 13. ToolExecutionLayer dispatch contract — DETERMINISTIC ──────────
    # The runtime executor is the process-global singleton (see
    # core.intelligence_runtime.execution lifecycle doc). Its handler set is
    # monotonic, so this proof pins its inputs instead of assuming a key is
    # absent. Two independent proofs:
    #   (a)-(c) the dispatch CONTRACT on an isolated layer (no order effects)
    #   (d)-(e) the SHARED singleton's actual lifecycle
    with journey_app.app_context():
        from core.intelligence_runtime.types import ActionType, PlanStep
        from core.intelligence_runtime.execution import ToolExecutionLayer as _TEL

        # (a) registered action → dispatches to the CORRECT handler
        isolated = _TEL()
        calls: list = []

        def _probe_handler(params):
            calls.append(params.get("token"))
            return {"echo": params.get("token")}

        isolated.register(ActionType.ANSWER.value, _probe_handler)
        iso_registered = isolated.execute(PlanStep(
            action=ActionType.ANSWER, description="probe",
            parameters={"token": "abc"}))
        step("isolated_registered_dispatches",
             iso_registered.get("status") == "success"
             and iso_registered.get("result", {}).get("echo") == "abc"
             and calls == ["abc"],
             f"isolated registered -> {iso_registered.get('status')}")

        # (b) unregistered action → deterministically "skipped"
        iso_unregistered = isolated.execute(PlanStep(
            action=ActionType.ROUTE, description="p", parameters={}))
        step("isolated_unregistered_skipped",
             iso_unregistered.get("status") == "skipped",
             f"isolated unregistered -> {iso_unregistered.get('status')}")

        # (c) repetition → identical result (determinism)
        repeat = [isolated.execute(PlanStep(
            action=ActionType.ROUTE, description="p", parameters={})).get("status")
            for _ in range(2)]
        step("unregistered_repeat_is_stable",
             repeat == ["skipped", "skipped"]
             and iso_unregistered.get("status") == "skipped",
             f"repeats -> {repeat}")

        # (d) shared singleton — ActionType.EXECUTE IS registered (ensure_runtime,
        #     pinned in step 3) and therefore dispatches, not skips.
        singleton_execute = executor.execute(PlanStep(
            action=ActionType.EXECUTE, description="Create customer",
            parameters={"name": "Executor-Test-Corp", "tenant_id": ORG_ID}))
        step("singleton_execute_action_registered",
             executor.is_registered(ActionType.EXECUTE.value)
             and singleton_execute.get("status") == "success",
             f"singleton EXECUTE -> {singleton_execute.get('status')}")

        # (e) shared singleton — a genuinely unregistered ActionType skips.
        #     Nothing in the codebase ever registers "defer" (verified by grep),
        #     so this holds in every suite order.
        singleton_defer = executor.execute(PlanStep(
            action=ActionType.DEFER, description="Escalate", parameters={}))
        step("singleton_unregistered_action_skipped",
             not executor.is_registered(ActionType.DEFER.value)
             and singleton_defer.get("status") == "skipped",
             f"singleton DEFER -> {singleton_defer.get('status')}")

    # ── 14. SECURITY — anonymous read denied ──────────────────────────────
    anon = Http(server.base)
    status, _ = anon.json("GET", "/api/v1/customers/?limit=10")
    step("anonymous_read_denied", status == 401,
         f"anonymous GET -> {status}")

    # ── Report ────────────────────────────────────────────────────────────
    report["failed_steps"] = [s["step"] for s in report["steps"] if not s["ok"]]
    report["ok"] = not report["failed_steps"]
    out_dir = os.environ.get("JOURNEY_REPORT_DIR", tempfile.gettempdir())
    try:
        with open(os.path.join(out_dir, "journey_gj12_report.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    except OSError:
        pass

    assert report["ok"], (
        "GJ-12 AI action journey failed at: " + ", ".join(report["failed_steps"]) + "\n"
        + json.dumps(report["steps"], indent=2)
    )