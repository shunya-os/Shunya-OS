"""
SHUNYA OS — Routing & API

Dashboard CRUD + Telegram webhook + Shunya API + activity logging.
All mutating operations log to ActivityLog for audit trail.
"""

import os
import pdfkit
import logging
from datetime import datetime, date, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, g, session
from app import db
from app.models import (
    Lead, Supplier, TaskList, Task, Document,
    LeadStatus, InvoiceStatus, next_inquiry_code,
)
from app.services import parse_inquiry_text, get_summary, _cached_or_new_code, format_inquiry_reply
from app.runtime_config import uploads_dir
from app.authz.decorators import session_required, require_permission
from app.auth_routes import login_required

logger = logging.getLogger(__name__)

main = Blueprint("main", __name__)
api = Blueprint("api", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _flash_if_error(obj, success_msg="Saved successfully"):
    """Add obj to session, commit, flash. Returns obj or None on error."""
    try:
        db.session.add(obj)
        db.session.commit()
        flash(success_msg, "success")
        return obj
    except Exception as e:
        db.session.rollback()
        flash(str(e), "error")
        return None


def _log_activity(lead_id: int, action: str, detail: str = ""):
    """Create an ActivityLog entry for a lead."""
    from app.models import ActivityLog
    log = ActivityLog(
        lead_id=lead_id,
        action=action,
        detail=detail[:500],
        user=getattr(g, "user", ""),
    )
    db.session.add(log)
    db.session.commit()


# ---------------------------------------------------------------------------
# API — Organization CRUD (Z-03A Articles VII-VIII)
# ---------------------------------------------------------------------------


@api.route("/orgs", methods=["POST"])
@session_required
def api_create_org():
    """Create an organization (used by SPA onboarding flow)."""
    data = request.get_json(silent=True) or {}
    company_name = data.get("company_name", "").strip()
    if not company_name:
        return jsonify({"success": False, "error": "Company name is required."}), 400

    from app.models import Organization, OrgMember
    from app.founder.models import FounderSpace
    import uuid

    # Check auth
    identity_id = session.get("identity_id")
    if not identity_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    # Create the organization
    slug = company_name.lower().replace(" ", "-")[:50]
    org = Organization(
        name=company_name,
        slug=slug,
        business_type=data.get("business_type", "Service Business"),
        email=data.get("company_email", ""),
        website=data.get("website", ""),
        phone=data.get("phone", ""),
        country=data.get("country", "United States"),
        timezone=data.get("timezone", "America/New_York"),
        currency=data.get("currency", "USD"),
    )
    db.session.add(org)
    db.session.flush()

    # Add founder as org member
    member = OrgMember(
        organization_id=org.id,
        identity_id=identity_id,
        role="owner",
    )
    db.session.add(member)

    # Create a FounderSpace for this org
    space = FounderSpace(
        space_id=f"spc_{uuid.uuid4().hex[:16]}",
        name=company_name,
        space_type="organization",
        identity_id=identity_id,
        member_count=1,
    )
    db.session.add(space)
    db.session.commit()

    return jsonify({
        "success": True,
        "org_id": str(org.id),
        "org_name": org.name,
    }), 201


# ---------------------------------------------------------------------------
# SPA helper
# ---------------------------------------------------------------------------

_FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


def _spa_shell_dirs() -> list:
    """Directories to try, in order, when serving the SPA shell.

    Production must serve the **immutable published release**, so a local
    ``npm run build`` inside the checkout can never change what production
    serves. ``resolve_frontend_dist()`` already implements that resolution (and
    falls back to the in-checkout build when no release is published); this
    route simply never used it, so the shell — unlike the assets — was served
    from the mutable worktree. A local build would have replaced the shell with
    one referencing asset hashes absent from the published release: broken
    production with a green health endpoint.

    The in-checkout build directory is retained as the development fallback.
    """
    dirs = []
    try:
        from app.frontend_release import resolve_frontend_dist
        dirs.append(resolve_frontend_dist())
    except Exception:  # never let resolution break shell serving
        pass
    if _FRONTEND_DIST not in dirs:
        dirs.append(_FRONTEND_DIST)
    return dirs


def _serve_spa_shell():
    """Serve the built React SPA shell from the resolved frontend directory.

    Use this for every route where the SPA should handle rendering,
    including root, auth paths, and any client-side-routed path.
    """
    from flask import make_response
    for dist in _spa_shell_dirs():
        idx = os.path.join(dist, "index.html")
        if os.path.exists(idx):
            with open(idx, "r", encoding="utf-8") as f:
                html = f.read()
            # Remove crossorigin from module scripts - no CORS headers needed
            html = html.replace("crossorigin ", "")
            resp = make_response(html)
            resp.headers["Content-Type"] = "text/html; charset=utf-8"
            # CORS handled by Flask-CORS middleware for /api/* routes.
            # No wildcard CORS needed — SPA is served from same origin.
            return resp
    return "Frontend not built. Run `cd frontend && npm run build`", 503


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@main.route("/")
def index():
    # Serve the built React SPA for all visitors — the SPA handles auth,
    # routing, and workspace rendering entirely client-side.
    return _serve_spa_shell()


# Auth SPA shell routes — these paths exist so the Flask router doesn't
# 404 when the React SPA handles client-side routing for auth pages.
# The SPA itself renders login/register content via React Router.
@main.route("/auth/login")
@main.route("/auth/")
@main.route("/auth")
@main.route("/auth/register")
@main.route("/auth/signup")
@main.route("/auth/forgot-password")
@main.route("/auth/reset-password")
@main.route("/auth/invitation")
@main.route("/auth/verify-email")
def auth_spa_shell():
    return _serve_spa_shell()


@main.route("/living")
def living_spa_shell():
    """Serve the SPA shell for the LX-01 Living Workspace."""
    return _serve_spa_shell()


@main.route("/welcome")
@login_required
def welcome():
    """Welcome screen with logo, greeting, voice."""
    from app.companion import CompanionEngine
    c = CompanionEngine()
    employee_name = g.user.name if hasattr(g, "user") and g.user else "there"
    welcome_data = c.greet(employee_name)
    stats = [
        {"value": "4", "label": "Today's Leads"},
        {"value": "₹45K", "label": "Revenue"},
        {"value": "6", "label": "Team Online"},
    ]
    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


# ---------------------------------------------------------------------------
# Calendar View
# ---------------------------------------------------------------------------


@main.route("/calendar")
@login_required
def calendar_view():
    """Full-page calendar view — SPA shell; the React SPA renders the calendar."""
    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


def _feed_tenant_scope():
    """Canonical tenant scope for feed endpoints (ZG-03). Fail closed.

    Returns ``(organization_id, accepted_tenant_ids)``; ``(None, [])`` when
    the caller has no authorized organization context — callers then deny
    the request or render an empty feed, never unfiltered data.
    """
    from app.authz.workspace_context import resolve_tenant_scope
    identity_id = session.get("identity_id", "")
    requested = session.get("current_org_id")
    try:
        return resolve_tenant_scope(identity_id, requested)
    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            "feed tenant scope resolution failed")
        return None, []


@api.route("/calendar/events")
@session_required
def calendar_events():
    """JSON feed of events for the calendar. Requires start= and end= params."""
    from datetime import date as dt_date
    start_str = request.args.get("start", "")
    end_str = request.args.get("end", "")
    import datetime
    try:
        start = datetime.date.fromisoformat(start_str) if start_str else dt_date.today().replace(day=1)
        end = datetime.date.fromisoformat(end_str) if end_str else dt_date.today()
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    from app.calendar_service import CalendarService
    org_id, accepted = _feed_tenant_scope()
    if not org_id:
        return jsonify({"error": "No organization context"}), 403
    svc = CalendarService()
    events = svc.get_events(start, end, tenant_scope=accepted)
    return jsonify(events)


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

@main.route("/leads")
@login_required
def leads_list():
    """Serving SPA — legacy leads list replaced by Universal Space workspace."""
    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


@main.route("/leads/new", methods=["GET", "POST"])
@login_required
def lead_new():
    if request.method == "POST":
        f = request.form
        with db.session.no_autoflush:
            code = _cached_or_new_code(db.session)
        # Canonical tenant for the write: the session's authorized org when
        # resolvable, else the legacy session tenant; never fabricated. The
        # thread-local is REQUIRED by the Lead-Entity bridge and the row must
        # carry the tenant BEFORE its first flush (NOT NULL in prod; ZG-03).
        from app.authz.decorators import _resolve_org_id
        from app.models import clear_lead_tenant_id, set_lead_tenant_id
        try:
            lead_tenant = _resolve_org_id() or int(session.get("tenant_id") or 0) or None
        except Exception:
            lead_tenant = int(session.get("tenant_id") or 0) or None
        if not lead_tenant:
            flash("No organization context — lead not created", "error")
            return redirect(url_for("main.leads_new"))
        try:
            set_lead_tenant_id(lead_tenant)
            lead = Lead(
                code=code,
                tenant_id=lead_tenant,
                source=f.get("source", "telegram"),
                customer_name=f.get("customer_name"),
                phone=f.get("phone"),
                email=f.get("email"),
                destination=f.get("destination"),
                pax=f.get("pax"),
                dates=f.get("dates"),
                budget=float(f.get("budget") or 0),
                assigned_to=f.get("assigned_to"),
                notes=f.get("notes"),
                status=f.get("status", "new"),
            )
        finally:
            clear_lead_tenant_id()
        obj = _flash_if_error(lead)
        if obj:
            _log_activity(obj.id, "created", f"Lead created via {obj.source}")
        return redirect(url_for("main.leads_list"))
    code = _cached_or_new_code(db.session)
    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


@main.route("/leads/<int:lead_id>")
@login_required
def lead_detail(lead_id):
    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


@main.route("/leads/<int:lead_id>/status", methods=["POST"])
@require_permission("rel.edit")
def lead_update_status(lead_id):
    """Update lead status and log the change."""
    lead = Lead.query.get_or_404(lead_id)
    json_data = request.get_json(silent=True)
    if json_data:
        new_status = json_data.get("status", "")
    else:
        new_status = request.form.get("status", "")

    if new_status and new_status in [s.value for s in LeadStatus]:
        old = lead.status
        lead.status = new_status
        db.session.commit()
        _log_activity(lead_id, "status_changed", f"{old} → {new_status}")

        # Auto-celebrate on lead conversion
        if new_status == LeadStatus.CONVERTED.value and old != LeadStatus.CONVERTED.value:
            try:
                from app.celebrations import CelebrationEngine
                ce = CelebrationEngine()
                celeb = ce.celebrate_lead_conversion(lead_id, user=getattr(g, "user", ""))
            except Exception:
                pass

        # Return JSON for API calls (kanban drag-drop), redirect for form posts
        if json_data:
            return jsonify({"success": True, "status": new_status})
        flash(f"Status updated: {new_status}", "success")
    else:
        if json_data:
            return jsonify({"success": False, "error": f"Invalid status: {new_status}"}), 400
        flash(f"Invalid status: {new_status}", "error")
    return redirect(url_for("main.lead_detail", lead_id=lead_id))


# API endpoint for kanban drag-and-drop
@api.route("/leads/<int:lead_id>/status", methods=["POST"])
@session_required
def api_lead_status(lead_id):
    return lead_update_status(lead_id)


# Creative AI — generate content on demand
# ---------------------------------------------------------------------------
# Outcome Engine API (Z-07 Article I-IV)
# ---------------------------------------------------------------------------


@api.route("/outcomes/execute", methods=["POST"])
@session_required
def api_execute_outcome():
    """Execute an outcome by name or by natural language intent.
    
    Request:
        {"name": "create_customer", "data": {...}}
        or
        {"intent": "Create a customer named Acme Corp", "data": {...}}
    
    Returns OutcomeResult with explanation.
    """
    data = request.get_json(silent=True) or {}
    outcome_name = data.get("name", "")
    intent = data.get("intent", "")
    outcome_data = data.get("data", {})
    
    from app.outcome_engine import build_default_registry, OutcomeEngine, OutcomeContext
    from app.production.objects import create_typed_object
    
    registry = build_default_registry()
    engine = OutcomeEngine(registry)
    
    identity_id = session.get("identity_id", "anonymous")
    import asyncio
    
    def _create_object(obj_type: str, obj_data: dict) -> dict:
        """Create an object by calling the raw creation function directly."""
        try:
            from app.production.objects import _create_typed_object_raw
            identity_id = session.get("identity_id", "anonymous")
            return _create_typed_object_raw(obj_type, obj_data, identity_id)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run():
        ctx = OutcomeContext(
            user_id=identity_id,
            workspace_id=data.get("workspace_id", "default"),
            identity_id=identity_id,
            session_data={"data": outcome_data},
            create_object_func=_create_object,
        )
        if outcome_name:
            result = await engine.execute_by_name(outcome_name, ctx)
        elif intent:
            result = await engine.execute_by_intent(intent, ctx)
        else:
            return {"success": False, "error": "Provide 'name' or 'intent'"}
        return {
            "success": result.success,
            "message": result.message,
            "explanation": result.explain(),
            "created": result.created,
            "modified": result.modified,
            "linked": result.linked,
            "requires_approval": result.requires_approval,
            "used": result.used,
            "error": result.error,
        }
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run())
        loop.close()
        return jsonify(result), 200 if result.get("success") else 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/outcomes/workflows", methods=["GET"])
@session_required
def api_list_workflows():
    """List all available business workflows (Z-11 Article III)."""
    from app.outcome_engine import build_default_registry, OutcomeEngine, WorkflowEngine
    registry = build_default_registry()
    engine = OutcomeEngine(registry)
    wf_engine = WorkflowEngine(engine)
    workflows = wf_engine.list_workflows()
    return jsonify({"success": True, "data": workflows, "total": len(workflows)})


@api.route("/outcomes/workflows/execute", methods=["POST"])
@session_required
def api_execute_workflow():
    """Execute a complete workflow by chaining outcomes.
    
    Request:
        {"name": "process_sale", "data": {"company": "Acme Corp", ...}}
    """
    data = request.get_json(silent=True) or {}
    workflow_name = data.get("name", "")
    template_data = data.get("data", {})
    
    from app.outcome_engine import build_default_registry, OutcomeEngine, OutcomeContext, WorkflowEngine
    from app.production.objects import _create_typed_object_raw
    
    registry = build_default_registry()
    engine = OutcomeEngine(registry)
    wf_engine = WorkflowEngine(engine)
    
    identity_id = session.get("identity_id", "anonymous")
    
    def _create_object(obj_type, obj_data):
        try:
            return _create_typed_object_raw(obj_type, obj_data, identity_id)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    import asyncio
    try:
        async def run():
            ctx = OutcomeContext(
                user_id=identity_id,
                workspace_id="default",
                identity_id=identity_id,
                session_data={"data": template_data},
                create_object_func=_create_object,
            )
            result = await wf_engine.execute_workflow(workflow_name, template_data, ctx)
            return {
                "success": result.success,
                "message": result.message,
                "explanation": result.explain(),
                "created": result.created,
                "used": result.used,
                "error": result.error,
            }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run())
        loop.close()
        return jsonify(result), 200 if result.get("success") else 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _outcome_fetch(method: str, path: str, body: dict = None) -> dict:
    """Synchronous fetch function used by outcome engine handlers.
    
    Makes real HTTP requests against the local server."""
    import json as _json
    import urllib.request as _req
    import urllib.error as _err
    
    base = "http://127.0.0.1:5001"
    url = base + path
    data = _json.dumps(body).encode() if body else None
    req = _req.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    # Copy session cookie from current request
    if request.cookies:
        cookie_parts = []
        for key, value in request.cookies.items():
            cookie_parts.append(f"{key}={value}")
        if cookie_parts:
            req.add_header("Cookie", "; ".join(cookie_parts))
    
    try:
        with _req.urlopen(req, timeout=10) as resp:
            resp_body = resp.read().decode()
            return _json.loads(resp_body)
    except _err.HTTPError as e:
        try:
            return _json.loads(e.read().decode())
        except Exception:
            return {"success": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api.route("/outcomes/list", methods=["GET"])
@session_required
def api_list_outcomes():
    """List all available outcomes with categories, descriptions, example phrases."""
    from app.outcome_engine import build_default_registry
    registry = build_default_registry()
    outcomes = []
    for o in registry.all():
        outcomes.append({
            "name": o.name,
            "category": o.category,
            "description": o.description,
            "example_phrases": o.example_phrases[:3],
        })
    return jsonify({"success": True, "data": outcomes, "total": len(outcomes)})



@main.route("/leads/<int:lead_id>/edit", methods=["GET", "POST"])
@login_required
def lead_edit(lead_id):
    if request.method == "POST":
        lead = Lead.query.get_or_404(lead_id)
        f = request.form
        for attr in ("customer_name", "phone", "email", "destination", "pax",
                     "dates", "notes", "source", "assigned_to"):
            val = f.get(attr)
            if val is not None:
                setattr(lead, attr, val)
        if f.get("budget"):
            lead.budget = float(f["budget"])
        lead.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        _log_activity(lead_id, "updated", "Lead details updated")
        flash("Lead updated", "success")
        return redirect(url_for("main.lead_detail", lead_id=lead_id))
    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


@main.route("/itineraries")
@login_required
def itinerary_builder():
    """Itinerary builder — create, edit, share travel plans."""
    lead_id = request.args.get("lead_id", type=int)
    leads = Lead.query.order_by(Lead.created_at.desc()).limit(50).all()
    selected_lead = None
    plan_days = []
    total_cost = 0
    plan_name = ""

    if lead_id:
        selected_lead = Lead.query.get(lead_id)
        if selected_lead:
            plan_name = f"{selected_lead.customer_name or 'Trip'} — {selected_lead.destination or 'Adventure'}"
            # Generate Shunya itinerary if one doesn't exist
            from app.shunya.knowledge import KnowledgeLayer
            from app.shunya._legacy_reasoning import ReasoningLayer
            from app.shunya.planner import PlannerLayer

            k = KnowledgeLayer()
            r = ReasoningLayer(k)
            p = PlannerLayer()
            inquiry = {
                "customer_name": selected_lead.customer_name or "",
                "destination": selected_lead.destination or "",
                "pax": selected_lead.pax or "2",
                "dates": selected_lead.dates or "",
                "notes": selected_lead.notes or "",
            }
            profile = r.analyze_inquiry(inquiry)
            strategy = r.suggest_approach(profile)
            plan = p.create_itinerary(profile, strategy)
            total_cost = plan.total_estimated_cost or 0

            for day in plan.days:
                plan_days.append({
                    "day": day.day_num,
                    "title": day.title or f"Day {day.day_num}",
                    "morning": day.morning or "",
                    "afternoon": day.afternoon or "",
                    "evening": day.evening or "",
                    "accommodation": day.accommodation or "",
                })

    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


@main.route("/leads/<int:lead_id>/delete", methods=["POST"])
@require_permission("rel.edit")
def lead_delete(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    db.session.delete(lead)
    db.session.commit()
    flash("Lead deleted", "success")
    return redirect(url_for("main.leads_list"))


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

@main.route("/payments", methods=["GET", "POST"])
@login_required
def payments():
    # Legacy Payment model removed — the SPA handles payment workflows via API.
    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


@main.route("/payments/<int:payment_id>/delete", methods=["POST"])
@login_required
def payment_delete(payment_id):
    # Legacy Payment model removed — the SPA manages payments through the
    # finance API (/api/v1/finance/payments). No live UI consumer posts to
    # this form route, so it serves the SPA shell instead of a NameError 500.
    logger.warning(
        "Legacy payment_delete called for id %s — legacy Payment model no "
        "longer exists; serving SPA shell (no-op).", payment_id,
    )
    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


# ---------------------------------------------------------------------------
# Payment Gateway — Checkout, Links, Receipts
# ---------------------------------------------------------------------------

@main.route("/payment/link/<int:lead_id>")
def payment_link(lead_id):
    """Generate a payment link page for a lead."""
    lead = Lead.query.get_or_404(lead_id)
    amount = request.args.get("amount", type=float) or float(lead.budget or 0)
    description = request.args.get("description", f"Payment for Lead {lead.code}")
    
    from app.payment_gateway import PaymentGateway
    gw = PaymentGateway()
    link_data = gw.create_payment_link(
        lead_id=lead.id,
        amount=amount,
        description=description,
        currency=request.args.get("currency", "INR"),
    )
    return redirect(url_for("main.payment_checkout", payment_id=link_data["payment_id"]))


@api.route("/payment/create", methods=["POST"])
@session_required
def api_create_payment():
    """API: Create a payment intent."""
    data = request.get_json(silent=True) or {}
    lead_id = data.get("lead_id")
    amount = data.get("amount")
    description = data.get("description", "Payment")
    currency = data.get("currency", "INR")

    if not lead_id or not amount:
        return jsonify({"error": "lead_id and amount are required"}), 400

    lead = Lead.query.get(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    try:
        from app.payment_gateway import PaymentGateway
        gw = PaymentGateway()
        result = gw.create_payment_link(
            lead_id=lead.id,
            amount=float(amount),
            description=description,
            currency=currency,
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api.route("/payment/verify", methods=["POST"])
@session_required
def api_verify_payment():
    """API: Verify a payment."""
    data = request.get_json(silent=True) or {}
    payment_id = data.get("payment_id")
    if not payment_id:
        return jsonify({"error": "payment_id is required"}), 400

    from app.payment_gateway import PaymentGateway
    gw = PaymentGateway()
    result = gw.verify_payment(payment_id)
    return jsonify(result)


@main.route("/payment/checkout/<payment_id>")
def payment_checkout(payment_id):
    """Checkout page — simulated payment form."""
    from app.payment_gateway import PaymentGateway
    gw = PaymentGateway()
    payment = gw.get_payment(payment_id)

    if not payment:
        flash("Payment link invalid or expired.", "error")
        return redirect(url_for("main.payments"))

    lead = Lead.query.get(payment["lead_id"]) if payment.get("lead_id") else None

    return render_template(
        "payment_checkout.html",
        payment=payment,
        lead=lead,
        gateway_provider=gw.PROVIDER,
    )


@main.route("/payment/complete", methods=["POST"])
@session_required
def payment_complete():
    """Legacy simulated checkout — retired (no-fake rule).

    The old handler "processed" payments through the in-memory simulated
    gateway and wrote a legacy (now deleted) Payment row. Real payments are
    captured ONLY through the Razorpay webhook
    (POST /api/v1/payments/razorpay/webhook), which records FinancePayment
    rows keyed by the real razorpay payment_id. This route now refuses
    honestly and redirects to the SPA payments shell.
    """
    payment_id = request.form.get("payment_id", "")
    logger.warning(
        "Legacy /payment/complete called (payment_id=%r) — refused: no real "
        "provider transaction exists; payments are captured via the Razorpay "
        "webhook only.", payment_id,
    )
    flash(
        "This checkout flow has been retired. Payments are confirmed only "
        "through the Razorpay payment gateway.",
        "warning",
    )
    return redirect(url_for("main.payments"))


@main.route("/payment/receipt/<payment_id>")
def payment_receipt(payment_id):
    """View payment receipt page."""
    from app.payment_gateway import PaymentGateway
    gw = PaymentGateway()
    payment = gw.get_payment(payment_id)

    if not payment:
        flash("Receipt not found.", "error")
        return redirect(url_for("main.payments"))

    lead = Lead.query.get(payment["lead_id"]) if payment.get("lead_id") else None

    # Legacy Payment model removed — resolve any real captured payment from
    # the finance module (FinancePayment), keyed by provider transaction id.
    db_payment = None
    if payment.get("transaction_id"):
        from app.finance.models import FinancePayment
        db_payment = FinancePayment.query.filter_by(
            reference_number=payment["transaction_id"]
        ).first()

    return render_template(
        "payment_receipt.html",
        payment=payment,
        lead=lead,
        db_payment=db_payment,
        gateway_provider=gw.PROVIDER,
    )


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------

@main.route("/invoices", methods=["GET", "POST"])
@login_required
def invoices():
    # Legacy Invoice model removed — the SPA handles invoicing via API.
    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


@main.route("/invoices/<int:invoice_id>/pdf")
@login_required
def invoice_pdf(invoice_id):
    inv = Invoice.query.get_or_404(invoice_id)
    if not inv.pdf_path or not os.path.exists(inv.pdf_path):
        try:
            os.makedirs("invoices", exist_ok=True)
            inv.pdf_path = os.path.join("invoices", f"{inv.id}_{inv.invoice_number}.pdf")
            _generate_invoice_pdf(inv.id, inv.pdf_path)
            db.session.commit()
        except Exception as e:
            flash(f"PDF generation failed: {e}", "error")
            return redirect(url_for("main.invoices"))
    return send_from_directory(
        os.path.dirname(os.path.abspath(inv.pdf_path)),
        os.path.basename(inv.pdf_path),
        as_attachment=True,
    )


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@main.route("/reports")
@login_required
def reports():
    from sqlalchemy import func, extract
    current_year = datetime.now(timezone.utc).year

    # Destination counts
    dest_counts = (
        db.session.query(Lead.destination, func.count(Lead.id))
        .filter(Lead.destination != None, Lead.destination != "")
        .group_by(Lead.destination)
        .order_by(func.count(Lead.id).desc())
        .limit(15)
        .all()
    )

    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


# ---------------------------------------------------------------------------
# Tasks & Checklists
# ---------------------------------------------------------------------------

@main.route("/tasks")
@login_required
def tasks_list():
    """Task dashboard — lists on left, tasks on right."""
    from app.tasks import TaskManager
    tm = TaskManager()
    all_lists = tm.get_all_lists()
    list_id = request.args.get("list", type=int)

    # Pre-compute counts for each list
    lists_data = []
    for lst in all_lists:
        total = lst.tasks.count()
        done = Task.query.filter(
            Task.task_list_id == lst.id, Task.status == "completed"
        ).count()
        lists_data.append({"id": lst.id, "name": lst.name,
                           "count": total, "done": done,
                           "created_by": lst.created_by})

    selected_list = None
    tasks = []
    total_count = done_count = pending_count = 0
    progress_pct = 0

    if list_id:
        selected_list = tm.get_list(list_id)
        if selected_list:
            tasks = tm.get_tasks_for_list(list_id)
            total_count = len(tasks)
            done_count = sum(1 for t in tasks if t.status == "completed")
            pending_count = total_count - done_count
            progress_pct = round(done_count / total_count * 100) if total_count else 0

    stats = tm.get_statistics()
    companion_greeting = "Stay on top of your tasks! Mark items done as you go. ✅"
    companion_suggestions = [
        {"icon": "📋", "text": "Review pending tasks", "action": "/tasks"},
        {"icon": "📊", "text": "View reports", "action": "/reports"},
        {"icon": "💰", "text": "Check payments", "action": "/payments"},
    ]

    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


@main.route("/tasks/create", methods=["POST"])
@login_required
def tasks_create_list():
    """Create a new task list."""
    from app.tasks import TaskManager
    name = request.form.get("name", "").strip()
    if not name:
        flash("List name is required", "error")
        return redirect(url_for("main.tasks_list"))
    tm = TaskManager()
    tm.create_list(name=name, created_by=getattr(g, "user", ""))
    flash(f"List '{name}' created", "success")
    return redirect(url_for("main.tasks_list"))


@main.route("/tasks/<int:id>/delete", methods=["POST"])
@login_required
def tasks_delete_list(id):
    """Delete a task list and all its tasks."""
    from app.tasks import TaskManager
    tm = TaskManager()
    if tm.delete_list(id):
        flash("List deleted", "success")
    else:
        flash("List not found", "error")
    return redirect(url_for("main.tasks_list"))


@main.route("/tasks/<int:id>/add", methods=["POST"])
@login_required
def tasks_add_item(id):
    """Add a task to a list."""
    from app.tasks import TaskManager
    title = request.form.get("title", "").strip()
    if not title:
        flash("Task title is required", "error")
        return redirect(url_for("main.tasks_list", list=id))
    tm = TaskManager()
    task = tm.add_task(
        list_id=id,
        title=title,
        description=request.form.get("description", ""),
        assigned_to=request.form.get("assigned_to", ""),
        priority=request.form.get("priority", "medium"),
        due_date=request.form.get("due_date"),
    )
    if task:
        flash(f"Task '{title}' added", "success")
    else:
        flash("Could not add task — list not found", "error")
    return redirect(url_for("main.tasks_list", list=id))


@main.route("/tasks/item/<int:id>/status", methods=["POST"])
@login_required
def tasks_update_status(id):
    """Update task status (checkbox toggle). Accepts JSON."""
    from app.tasks import TaskManager
    json_data = request.get_json(silent=True)
    if json_data:
        new_status = json_data.get("status", "")
    else:
        new_status = request.form.get("status", "")

    tm = TaskManager()
    task = tm.update_status(id, new_status)
    if task:
        if json_data:
            return jsonify({"success": True, "status": task.status})
        flash(f"Task updated: {task.status}", "success")
    else:
        if json_data:
            return jsonify({"success": False, "error": "Task not found or invalid status"}), 400
        flash("Task not found", "error")
    return redirect(url_for("main.tasks_list"))


@main.route("/tasks/item/<int:id>/delete", methods=["POST"])
@login_required
def tasks_delete_item(id):
    """Delete a task. Accepts JSON."""
    from app.tasks import TaskManager
    json_data = request.get_json(silent=True)
    tm = TaskManager()
    if tm.delete_task(id):
        if json_data:
            return jsonify({"success": True})
        flash("Task deleted", "success")
    else:
        if json_data:
            return jsonify({"success": False, "error": "Task not found"}), 400
        flash("Task not found", "error")
    return redirect(url_for("main.tasks_list"))


@main.route("/tasks/reorder", methods=["POST"])
@login_required
def tasks_reorder():
    """Reorder tasks within a list (drag & drop). Accepts JSON."""
    from app.tasks import TaskManager
    data = request.get_json(silent=True) or {}
    order = data.get("order", [])
    tm = TaskManager()
    for idx, task_id in enumerate(order):
        tm.update_task(task_id, sort_order=idx)
    return jsonify({"success": True})


@api.route("/tasks")
@session_required
def api_tasks():
    """JSON endpoint returning all tasks."""
    from app.tasks import TaskManager
    tm = TaskManager()
    all_lists = tm.get_all_lists()
    result = []
    for lst in all_lists:
        tasks = tm.get_tasks_for_list(lst.id)
        result.append({
            "id": lst.id,
            "name": lst.name,
            "tasks": [t.to_dict() for t in tasks],
        })
    return jsonify(result)


# ---------------------------------------------------------------------------
# Settings / Suppliers
# ---------------------------------------------------------------------------

@main.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        f = request.form
        s = Supplier(
            name=f["name"],
            category=f.get("category"),
            contact=f.get("contact"),
            email=f.get("email"),
            phone=f.get("phone"),
            city=f.get("city"),
            gstin=f.get("gstin"),
            payment_terms=f.get("payment_terms"),
            notes=f.get("notes"),
        )
        _flash_if_error(s)
        return redirect(url_for("main.settings"))
    suppliers = Supplier.query.order_by(Supplier.created_at.desc()).limit(200).all()
    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


@main.route("/settings/fields/add", methods=["POST"])
@login_required
def settings_fields_add():
    """Superadmin: create a custom dynamic field."""
    from app.dynamic_fields import DynamicFieldManager
    f = request.form
    field_name = f.get("field_name", "").strip()
    field_label = f.get("field_label", "").strip()
    entity = f.get("entity", "lead")
    field_type = f.get("field_type", "text")
    options_raw = f.get("options", "")
    options = [o.strip() for o in options_raw.split("\n") if o.strip()] if options_raw else None
    searchable = f.get("searchable") == "1"
    try:
        DynamicFieldManager.create_field(
            entity=entity, field_name=field_name, field_label=field_label,
            field_type=field_type, options=options, searchable=searchable,
        )
        flash(f"Field '{field_label}' created for {entity}", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("main.settings"))


# ---------------------------------------------------------------------------
# Telegram webhook & Bot endpoints
# ---------------------------------------------------------------------------

@main.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    from app.services import parse_inquiry_text

    payload = request.get_json(silent=True) or {}
    message = payload.get("message") or {}
    text = str(message.get("text") or payload.get("text") or "")
    chat = message.get("chat") or payload.get("chat") or {}
    sender = str(chat.get("id") or payload.get("from", {}).get("id") or "")

    if not text:
        return jsonify({"status": "ignored"}), 200

    parsed = parse_inquiry_text(text)
    with db.session.no_autoflush:
        code = _cached_or_new_code(db.session)

    # System ingress: only project a Lead when a canonical tenant resolves —
    # undocumented attribution is refused rather than fabricated (ZG-03).
    resolved_tenant = None
    try:
        from app.authz.decorators import _resolve_org_id
        resolved_tenant = _resolve_org_id()
    except Exception:
        resolved_tenant = None
    if resolved_tenant:
        from app.models import clear_lead_tenant_id, set_lead_tenant_id
        try:
            set_lead_tenant_id(int(resolved_tenant))
            lead = Lead(
                code=code,
                source="telegram",
                tenant_id=int(resolved_tenant),
                customer_name=parsed.get("name") or sender,
                phone=sender,
                destination=parsed.get("destination"),
                pax=(
                    f"{parsed.get('adults') or 0} adults, {parsed.get('kids') or 0} kids"
                    if parsed.get("adults") or parsed.get("kids")
                    else None
                ),
                dates=parsed.get("dates"),
                notes=text,
                status="new",
            )
        finally:
            clear_lead_tenant_id()
        db.session.add(lead)
        db.session.commit()
        _log_activity(lead.id, "created", f"Lead created via Telegram inquiry: {text[:200]}")
    else:
        import logging
        logging.getLogger(__name__).warning(
            "Telegram Lead projection skipped: no canonical tenant (sender %s)",
            sender)

    reply = {
        "method": "sendMessage",
        "chat_id": sender,
        "text": format_inquiry_reply(parsed, code),
    }
    return jsonify(reply), 200


@main.route("/telegram/setup", methods=["POST"])
@session_required
def telegram_setup():
    from app.services import save_telegram_token
    token = request.form.get("bot_token")
    if not token:
        flash("Bot token required", "error")
        return redirect(url_for("main.settings"))
    try:
        save_telegram_token(token)
        flash("Telegram bot token saved. Use /telegram/setwebhook to register.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("main.settings"))


@main.route("/telegram/setwebhook", methods=["POST"])
@session_required
def telegram_setwebhook():
    from app.services import get_telegram_token, set_telegram_webhook
    token = get_telegram_token()
    if not token:
        flash("No Telegram bot token configured. Save it in Settings first.", "error")
        return redirect(url_for("main.settings"))
    host = request.host_url.rstrip("/")
    url = f"{host}/telegram/webhook"
    ok, data = set_telegram_webhook(token, url)
    if ok:
        flash(f"Telegram webhook set: {url}", "success")
    else:
        flash(f"Webhook setup failed: {data}", "error")
    return redirect(url_for("main.settings"))


# ---------------------------------------------------------------------------
# WhatsApp Webhook — plug-and-play
# ---------------------------------------------------------------------------

@main.route("/whatsapp/webhook", methods=["GET", "POST"])
def whatsapp_webhook():
    """WhatsApp Business API webhook. GET = verification, POST = incoming msg."""
    if request.method == "GET":
        from app.whatsapp_webhook import handle_whatsapp_verification
        return handle_whatsapp_verification()

    from app.whatsapp_webhook import handle_whatsapp_incoming
    payload = request.get_json(silent=True) or {}
    return handle_whatsapp_incoming(payload)


@main.route("/whatsapp/setup", methods=["POST"])
@session_required
def whatsapp_setup():
    """Configure WhatsApp Business API settings."""
    token = request.form.get("whatsapp_token", "")
    phone_id = request.form.get("phone_number_id", "")
    if token:
        os.environ["WHATSAPP_TOKEN"] = token
    if phone_id:
        os.environ["WHATSAPP_PHONE_ID"] = phone_id
    flash("WhatsApp settings saved. Webhook is ready at /whatsapp/webhook", "success")
    return redirect(url_for("main.settings"))


# ---------------------------------------------------------------------------
# Shunya Pipeline API
# ---------------------------------------------------------------------------

@api.route("/shunya/process", methods=["POST"])
@session_required
def shunya_process():
    data = request.get_json(silent=True) or {}
    fmt = data.get("format", "text")
    inquiry = {
        "customer_name": data.get("customer_name", ""),
        "destination": data.get("destination", ""),
        "pax": data.get("pax", ""),
        "dates": data.get("dates", ""),
        "notes": data.get("notes", ""),
        "phone": data.get("phone", ""),
        "source": data.get("source", "api"),
    }
    from app.shunya import WorkflowLayer
    wf = WorkflowLayer(db.session)
    result = wf.process_inquiry(inquiry, fmt=fmt)
    if result.success() and data.get("create_lead"):
        lead_id = wf.create_lead_from_inquiry(inquiry)
        if lead_id:
            _log_activity(lead_id, "created", "Lead created via Shunya API")
        result.lead_id = lead_id
    resp = result.to_dict()
    if fmt in ("html", "all"):
        resp["proposal_html"] = result.proposal_html
    return jsonify(resp)


@api.route("/shunya/knowledge", methods=["GET"])
@session_required
def shunya_knowledge():
    from app.shunya import KnowledgeLayer
    k = KnowledgeLayer(db.session)
    return jsonify({
        "knowledge_base_length": len(k.get_knowledge_base_text()),
        "past_itineraries": k.get_past_itineraries(limit=5),
    })


@api.route("/shunya/summary", methods=["GET"])
@session_required
def shunya_summary():
    from app.shunya import WorkflowLayer
    wf = WorkflowLayer(db.session)
    return jsonify(wf.get_lead_status_summary(db.session))


@api.route("/shunya/proposal/<int:lead_id>", methods=["GET"])
@session_required
def shunya_proposal(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    fmt = request.args.get("format", "text")
    inquiry = {
        "customer_name": lead.customer_name or "",
        "destination": lead.destination or "",
        "pax": lead.pax or "",
        "dates": lead.dates or "",
        "notes": lead.notes or "",
        "phone": lead.phone or "",
    }
    from app.shunya import WorkflowLayer
    wf = WorkflowLayer(db.session)
    result = wf.process_inquiry(inquiry, fmt=fmt)
    if result.success():
        _log_activity(lead_id, "proposal_sent",
                      f"Proposal generated ({fmt}, {result.plan.days[0].day_num if result.plan else 3}d itinerary)")
        resp = {
            "lead_code": lead.code,
            "format": fmt,
            "proposal": result.proposal_text,
            "itinerary": result.plan.to_dict() if result.plan else None,
        }
        if fmt in ("html", "all"):
            resp["proposal_html"] = result.proposal_html
        return jsonify(resp)
    return jsonify({"error": result.errors}), 400


# ---------------------------------------------------------------------------
# API: Activity log lookup
# ---------------------------------------------------------------------------

@api.route("/leads/<int:lead_id>/activities", methods=["GET"])
@require_permission("rel.view")
def api_lead_activities(lead_id):
    """Return activity log for a lead as JSON (tenant-scoped — ZG-03 B1)."""
    from app.models import ActivityLog
    from app.leads.routes import _lead_tenant_scope

    org_id, accepted = _lead_tenant_scope()
    if not org_id or not accepted:
        return jsonify({"error": "No organization context"}), 403
    lead = Lead.query.filter(
        Lead.id == lead_id, Lead.tenant_id.in_(accepted)
    ).first()
    if not lead:
        return jsonify({"error": "Lead not found"}), 404
    limit = min(int(request.args.get("limit", 50)), 200)
    activities = (
        lead.activities
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify([a.to_dict() for a in activities])


# ---------------------------------------------------------------------------
# API: Notifications
# ---------------------------------------------------------------------------

@api.route("/notifications", methods=["GET"])
@session_required
def api_get_notifications():
    """Get notifications for the current user (or all if no user)."""
    from app.notifications import NotificationManager
    limit = min(int(request.args.get("limit", 20)), 100)
    user_id = g.user.id if hasattr(g, "user") and g.user else None
    nm = NotificationManager()
    notifications = nm.get_for_user(user_id=user_id, limit=limit)
    return jsonify([n.to_dict() for n in notifications])


@api.route("/notifications/unread/count", methods=["GET"])
@session_required
def api_unread_count():
    """Get unread notification count for the current user."""
    from app.notifications import NotificationManager
    user_id = g.user.id if hasattr(g, "user") and g.user else None
    nm = NotificationManager()
    count = nm.get_unread_count(user_id=user_id)
    return jsonify({"count": count})


@api.route("/notifications/<int:notification_id>/read", methods=["POST"])
@session_required
def api_mark_read(notification_id):
    """Mark a single notification as read."""
    from app.notifications import NotificationManager
    nm = NotificationManager()
    success = nm.mark_read(notification_id)
    if not success:
        return jsonify({"error": "Notification not found"}), 404
    return jsonify({"success": True})


@api.route("/notifications/read-all", methods=["POST"])
@session_required
def api_mark_all_read():
    """Mark all notifications as read for the current user."""
    from app.notifications import NotificationManager
    user_id = g.user.id if hasattr(g, "user") and g.user else None
    nm = NotificationManager()
    count = nm.mark_all_read(user_id=user_id)
    return jsonify({"success": True, "marked": count})


@api.route("/notifications/create", methods=["POST"])
@session_required
def api_create_notification():
    """Create a notification (for system events / programmatic use)."""
    from app.notifications import NotificationManager
    data = request.get_json(silent=True) or {}
    required = ["type", "title"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400
    nm = NotificationManager()
    notif = nm.create_notification(
        type=data["type"],
        title=data["title"],
        message=data.get("message", ""),
        user_id=data.get("user_id"),
        lead_id=data.get("lead_id"),
        tenant_id=data.get("tenant_id"),
        icon=data.get("icon"),
        link=data.get("link"),
    )
    return jsonify(notif.to_dict()), 201


# ---------------------------------------------------------------------------
# Celebrations API
# ---------------------------------------------------------------------------

@api.route("/celebrations", methods=["GET"])
@session_required
def api_get_celebrations():
    """Get recent celebrations (tenant-scoped — ZG-03)."""
    from app.celebrations import CelebrationEngine
    limit = min(int(request.args.get("limit", 10)), 50)
    org_id, accepted = _feed_tenant_scope()
    if not org_id:
        return jsonify({"error": "No organization context"}), 403
    ce = CelebrationEngine()
    celebrations = ce.get_recent_celebrations(limit=limit, tenant_scope=accepted)
    count = ce.get_celebration_count_since(tenant_scope=accepted)
    return jsonify({"celebrations": celebrations, "count": count})


@api.route("/celebrations/scan", methods=["GET"])
@session_required
def api_scan_celebrations():
    """Scan for new wins and record any that haven't been recorded yet.

    Tenant-scoped (ZG-03): only the caller's scope is scanned and returned.
    """
    from app.celebrations import CelebrationEngine
    org_id, accepted = _feed_tenant_scope()
    if not org_id:
        return jsonify({"error": "No organization context"}), 403
    ce = CelebrationEngine()
    new_celebrations = ce.scan_and_record(tenant_scope=accepted)
    celebrations = ce.get_recent_celebrations(limit=10, tenant_scope=accepted)
    count = ce.get_celebration_count_since(tenant_scope=accepted)
    return jsonify({
        "new": new_celebrations,
        "celebrations": celebrations,
        "count": count,
    })


@api.route("/celebrations", methods=["POST"])
@session_required
def api_create_celebration():
    """Manually create a celebration."""
    from app.celebrations import CelebrationEngine
    data = request.get_json(silent=True) or {}
    required = ["title"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    ce = CelebrationEngine()
    celebration = ce.record_celebration(
        celebration_type=data.get("type", "manual"),
        title=data["title"],
        message=data.get("message", ""),
        icon=data.get("icon", "🎉"),
        animation=data.get("animation", "woosh"),
        lead_id=data.get("lead_id"),
        created_by=data.get("created_by", ""),
    )
    return jsonify(celebration), 201


# ---------------------------------------------------------------------------
# PDF Generation (inline helper)
# ---------------------------------------------------------------------------

@api.route("/voice/process", methods=["POST"])
@session_required
def voice_process():
    """Process voice input from the browser SpeechRecognition API.

    Accepts: {text: "user speech text", web_search: true}
    Returns: {response: "AI reply", action: "suggestions"|"redirect"|"none"|"info", redirect_url: ""}
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    web_search = data.get("web_search", False)

    if not text:
        return jsonify({"response": "I didn't catch that. Could you say it again?", "action": "none", "redirect_url": ""})

    # Web intelligence for travel/destination/weather queries
    if web_search or any(k in text.lower() for k in ["weather", "visa", "currency", "destination",
                                                       "bali", "thailand", "dubai", "maldives",
                                                       "time", "date", "today", "tell me about"]):
        from app.web_intel import WebIntelligence
        result = WebIntelligence.answer(text)
        if result["action"] == "info":
            return jsonify({"response": result["response"], "action": "none", "redirect_url": ""})
        # Check travel info
        for dest in ["bali", "thailand", "dubai", "maldives", "sri lanka"]:
            if dest in text.lower():
                result = WebIntelligence.search_travel_info(dest)
                return jsonify({"response": result["response"], "action": "none", "redirect_url": ""})

    from app.voice import VoiceProcessor
    user_name = getattr(g, "user", None)
    name = user_name.name if user_name else "there"
    processor = VoiceProcessor(user_name=name)
    result = processor.process(text)
    return jsonify(result)


# ---------------------------------------------------------------------------
# Documents — AI Document Reading
# ---------------------------------------------------------------------------

@main.route("/documents")
@login_required
def documents_page():
    """Document management — served as SPA shell.

    The server-side template (documents.html) was never created. The SPA's
    DocumentBrowser component handles the document surface through
    /api/v1/workspace/documents and the sidebar navigation. This route
    serves the SPA shell (same pattern as /living — see living_spa_shell).
    """
    return _serve_spa_shell()


@main.route("/documents/upload", methods=["POST"])
@session_required
def documents_upload():
    """Upload and process a document — extract text, classify, parse lead info."""
    if "file" not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("main.documents_page"))

    f = request.files["file"]
    if not f or not f.filename:
        flash("No file selected", "error")
        return redirect(url_for("main.documents_page"))

    # Determine file type
    ext = os.path.splitext(f.filename)[1].lower()
    file_type = "text"
    if ext in (".pdf",):
        file_type = "pdf"
    elif ext in (".docx", ".doc"):
        file_type = "docx"
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"):
        file_type = "image"
    elif ext in (".txt", ".csv", ".json", ".xml", ".md", ".log", ".ini", ".cfg"):
        file_type = "text"
    else:
        flash(f"Unsupported file type: {ext}", "error")
        return redirect(url_for("main.documents_page"))

    # Save file to RUNTIME_DATA_ROOT
    upload_dir = os.path.join(uploads_dir(), "documents")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{f.filename}"
    file_path = os.path.join(upload_dir, safe_name)
    try:
        f.save(file_path)
    except Exception as e:
        flash(f"Failed to save file: {e}", "error")
        return redirect(url_for("main.documents_page"))

    # Process document with DocumentReader
    from app.document_reader import DocumentReader
    reader = DocumentReader()
    result = reader.process_document(file_path, file_type)
    structured_json = json.dumps(result.get("structured_data", {}))

    # Optional lead association
    lead_id = request.form.get("lead_id", type=int)
    if not lead_id:
        lead_id = None

    doc = Document(
        lead_id=lead_id,
        filename=f.filename,
        file_path=file_path,
        file_type=file_type,
        extracted_text=result.get("extracted_text", ""),
        structured_data=structured_json,
        classification=result.get("classification", "other"),
        uploaded_by=getattr(g, "user", ""),
        tenant_id=getattr(g, "user", "").tenant_id if hasattr(getattr(g, "user", ""), "tenant_id") else None,
    )
    # Resolve tenant_id from session if not available on g.user
    if doc.tenant_id is None:
        from app.auth import TeamMember
        user_id = session.get("user_id")
        if user_id:
            tm = TeamMember.query.get(int(user_id))
            if tm and tm.tenant_id:
                doc.tenant_id = tm.tenant_id
    try:
        db.session.add(doc)
        db.session.commit()

        # Extract entities → knowledge_facts with provenance
        try:
            from app.document.extraction_pipeline import store_document_facts
            fact_count = store_document_facts(doc.id)
            if fact_count:
                logger.debug("Extracted %d knowledge_facts from document %s", fact_count, doc.id)
        except Exception as ext_err:
            logger.warning("Entity extraction for doc %s failed: %s", doc.id, ext_err)

        if doc.lead_id:
            _log_activity(doc.lead_id, "document_uploaded",
                          f"Document '{doc.filename}' uploaded ({doc.classification})")
        flash(f"✅ Document processed: {doc.filename} — classified as {doc.classification}", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to save document record: {e}", "error")

    return redirect(url_for("main.documents_page"))


@main.route("/documents/<int:doc_id>")
@login_required
def documents_detail(doc_id):
    """Document deep link — served as SPA shell.

    Like documents_page, there is no server-side document surface: the SPA
    resolves the document client-side through /api/v1/workspace/documents.
    The previous implementation rendered the never-created template
    "documents.html", crashing every real document deep link with
    TemplateNotFound (HTTP 500). Serving the shell keeps deep links and
    refreshes working.
    """
    return _serve_spa_shell()


@main.route("/api/documents/extract", methods=["POST"])
@session_required
def api_documents_extract():
    """API: Upload a file, return extracted text + structured data as JSON."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"error": "No file provided"}), 400

    ext = os.path.splitext(f.filename)[1].lower()
    file_type = "text"
    if ext in (".pdf",):
        file_type = "pdf"
    elif ext in (".docx", ".doc"):
        file_type = "docx"
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"):
        file_type = "image"

    upload_dir = os.path.join(uploads_dir(), "documents")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{f.filename}"
    file_path = os.path.join(upload_dir, safe_name)
    try:
        f.save(file_path)
    except Exception as e:
        return jsonify({"error": f"Failed to save file: {e}"}), 500

    from app.document_reader import DocumentReader
    reader = DocumentReader()
    result = reader.process_document(file_path, file_type)

    return jsonify({
        "filename": f.filename,
        "file_type": file_type,
        "extracted_text": result.get("extracted_text", ""),
        "summary": result.get("summary", ""),
        "classification": result.get("classification", "other"),
        "structured_data": result.get("structured_data", {}),
    })


@main.route("/api/documents/classify", methods=["POST"])
@session_required
def api_documents_classify():
    """API: Classify a document (text-based classification)."""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    from app.document_reader import DocumentReader
    reader = DocumentReader()
    classification = reader.classify_document(text)
    summary = reader.summarize_document(text)

    return jsonify({
        "classification": classification,
        "summary": summary,
        "text_length": len(text),
    })


# ---------------------------------------------------------------------------
# PDF Generation (inline helper)
# ---------------------------------------------------------------------------

def _generate_invoice_pdf(invoice_id, path):
    inv = Invoice.query.get(invoice_id)
    lead = inv.lead
    due_str = inv.due_date.strftime("%d-%m-%Y") if inv.due_date else ""
    paid_str = inv.paid_at.strftime("%d-%m-%Y") if inv.paid_at else ""
    due_html = f"<p>Due: {due_str}</p>" if due_str else ""
    paid_html = f"<p>Paid: {paid_str}</p>" if paid_str else ""
    html = f"""<!doctype html><html><head><meta charset='utf-8'><style>
      body{{font-family:Arial,sans-serif;color:#111;padding:40px}}
      h1{{color:#2563eb;border-bottom:2px solid #2563eb;padding-bottom:8px}}
      table{{width:100%;border-collapse:collapse;margin:16px 0}}
      td,th{{border:1px solid #e5e7eb;padding:10px 8px;text-align:left}}
      th{{background:#f9fafb}}
      .grand{{font-size:18px}}
      .meta{{color:#6b7280;font-size:14px}}
    </style></head><body>
      <h1>Invoice {inv.invoice_number}</h1>
      <p class="meta">Raised: {inv.raised_at.strftime('%d-%m-%Y %H:%M')} · Status: {inv.status} · Currency: {inv.currency}</p>
      <h3>Customer</h3>
      <p>{lead.customer_name if lead else '-'}<br>{lead.email or ''}<br>{lead.phone or ''}<br>{lead.destination or ''}</p>
      <h3>Amounts</h3>
      <table>
        <tr><th>Total</th><td>₹{inv.total_amount:.2f}</td></tr>
        <tr><th>Tax ({inv.tax_rate:.1f}%)</th><td>₹{inv.tax:.2f}</td></tr>
        <tr><th>Discount</th><td>₹{inv.discount:.2f}</td></tr>
        <tr class="grand"><th><strong>Grand Total</strong></th><td><strong>₹{inv.grand_total:.2f}</strong></td></tr>
      </table>
      {due_html}
      {paid_html}
    </body></html>"""
    from app.pdf_safe import generate_pdf
    generate_pdf(html, path)


# ---------------------------------------------------------------------------
# Executive Workspace
# ---------------------------------------------------------------------------


@main.route("/executive")
@login_required
def executive_workspace():
    """Redirect to the canonical React SPA workspace (executive view handled client-side)."""
    return redirect(url_for("main.index"))


# ---------------------------------------------------------------------------
# Workspace Runtime API
# ---------------------------------------------------------------------------

from app.workspace_runtime import WorkspaceAPI, get_workspace_runtime, reset_workspace_runtime


@main.route("/api/workspace/object/<obj_type>/<obj_id>")
@login_required
def workspace_focus_object(obj_type, obj_id):
    """Focus the workspace on an object. Returns full object data + intelligence."""
    api = WorkspaceAPI()
    return jsonify(api.focus_object(obj_type, obj_id))


@main.route("/api/workspace/executive")
@login_required
def workspace_executive_data():
    """Get all executive intelligence data for the workspace."""
    api = WorkspaceAPI()
    return jsonify(api.get_executive_data())


@main.route("/api/workspace/conversation/<obj_type>/<obj_id>")
@login_required
def workspace_get_conversation(obj_type, obj_id):
    """Get conversation history for an object."""
    api = WorkspaceAPI()
    return jsonify(api.get_conversation(obj_type, obj_id))


@main.route("/api/workspace/conversation/<obj_type>/<obj_id>/send", methods=["POST"])
@login_required
def workspace_send_message(obj_type, obj_id):
    """Send a message in an object's conversation."""
    data = request.get_json() or {}
    text = data.get("text", "")
    api = WorkspaceAPI()
    return jsonify(api.send_message(obj_type, obj_id, text))


@main.route("/api/workspace/updates")
@login_required
def workspace_updates():
    """Get runtime updates since last check."""
    api = WorkspaceAPI()
    return jsonify(api.get_updates())


@main.route("/api/workspace/graph/<obj_type>/<obj_id>")
@login_required
def workspace_object_graph(obj_type, obj_id):
    """Get the object graph centered on an object."""
    api = WorkspaceAPI()
    return jsonify(api.get_object_graph(obj_type, obj_id))


@main.route("/api/workspace/recent")
@login_required
def workspace_recent():
    """Get recent objects across all types."""
    api = WorkspaceAPI()
    return jsonify(api.get_recent_objects())


@main.route("/api/workspace/types")
@login_required
def workspace_types():
    """Get available object types."""
    api = WorkspaceAPI()
    return jsonify(api.get_available_types())


@main.route("/api/workspace/state")
@login_required
def workspace_state():
    """Get current workspace runtime state."""
    api = WorkspaceAPI()
    return jsonify(api.get_state())


@main.route("/api/workspace/mode/<mode>")
@login_required
def workspace_set_mode(mode):
    """Set the current executive mode."""
    api = WorkspaceAPI()
    return jsonify(api.set_mode(mode))


@main.route("/api/workspace/attention/<layer>")
@login_required
def workspace_set_attention(layer):
    """Set the attention layer (executive, team, personal)."""
    api = WorkspaceAPI()
    return jsonify(api.set_attention_layer(layer))


@main.route("/api/workspace/stats")
@login_required
def workspace_stats():
    """Get workspace runtime statistics."""
    api = WorkspaceAPI()
    return jsonify(api.stats())


# ── Document → Knowledge Fact Extraction API ────────────────────────────


@api.route("/documents/<int:doc_id>/extract-facts", methods=["POST"])
@session_required
def api_extract_document_facts(doc_id: int):
    """Extract entities from a document and store as knowledge_facts."""
    from app.document.extraction_pipeline import store_document_facts

    try:
        count = store_document_facts(doc_id)
        if count == 0:
            doc = Document.query.get(doc_id)
            if not doc:
                return jsonify({"success": False, "error": "Document not found"}), 404
            if not (doc.extracted_text or "").strip():
                return jsonify({
                    "success": False,
                    "error": "Document has no extracted text to process",
                    "document_id": doc_id,
                    "filename": doc.filename,
                }), 400
            return jsonify({
                "success": True,
                "message": "No entities found in document text",
                "document_id": doc_id,
                "facts_stored": 0,
            })
        return jsonify({
            "success": True,
            "message": f"Extracted {count} knowledge facts",
            "document_id": doc_id,
            "facts_stored": count,
        })
    except Exception as e:
        logger.exception("Failed to extract facts from document %s", doc_id)
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/documents/backfill-facts", methods=["POST"])
@session_required
def api_backfill_document_facts():
    """Backfill knowledge_facts from all documents with extracted text."""
    from app.document.extraction_pipeline import backfill_all_documents

    try:
        results = backfill_all_documents()
        return jsonify({
            "success": True,
            "message": (
                f"Processed {results['processed']}/{results['total_docs']} docs, "
                f"stored {results['facts_stored']} facts, "
                f"{results['skipped_no_text']} skipped (no text), "
                f"{len(results['errors'])} errors"
            ),
            **results,
        })
    except Exception as e:
        logger.exception("Backfill failed")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/knowledge-facts", methods=["GET"])
@session_required
def api_list_knowledge_facts():
    """List knowledge facts, optionally filtered by domain or category."""
    from app.shunya.knowledge_store import KnowledgeFact

    domain = request.args.get("domain", "")
    category = request.args.get("category", "")
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = int(request.args.get("offset", 0))

    q = db.session.query(KnowledgeFact).filter(KnowledgeFact.superseded_at.is_(None))
    if domain:
        q = q.filter(KnowledgeFact.domain == domain)
    if category:
        q = q.filter(KnowledgeFact.category == category)
    total = q.count()
    facts = q.order_by(KnowledgeFact.created_at.desc()).offset(offset).limit(limit).all()

    return jsonify({
        "success": True,
        "total": total,
        "facts": [f.to_dict() for f in facts],
    })


@api.route("/knowledge-facts/stats", methods=["GET"])
@session_required
def api_knowledge_facts_stats():
    """Get knowledge_facts statistics."""
    from app.shunya.knowledge_store import ImmutableKnowledgeStore

    store = ImmutableKnowledgeStore()
    return jsonify({
        "success": True,
        **store.stats(),
    })


# ── Z-15: Legacy module routes → serve SPA instead of Jinja2 templates ──
# These routes redirect legacy module pages to the SPA workspace.
# The SPA handles navigation via its own router and command surface.

SPA_INDEX = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "index.html")


@main.route("/leads")
@main.route("/leads/new")
@main.route("/leads/<int:lead_id>")
@main.route("/leads/<int:lead_id>/edit")
@main.route("/invoices")
@main.route("/payments")
@main.route("/tasks")
@main.route("/calendar")
# /documents and /documents/<id> are owned by main.documents_page /
# main.documents_detail (release-aware SPA shell) — not duplicated here.
@main.route("/reports")
@main.route("/team")
@main.route("/pipeline")
@main.route("/settings")
@main.route("/itineraries")
@main.route("/dashboard")
def _legacy_spa_fallback(**kwargs):
    """Serve the SPA for legacy routes — eliminates module switching."""
    return send_from_directory(os.path.dirname(SPA_INDEX), "index.html")


_legacy_spa_fallback._shunya_policy = "spa_shell"
