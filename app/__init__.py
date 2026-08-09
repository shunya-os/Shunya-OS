"""
SHUNYA OS — Core App Unit
Flask application factory with production scaffolding.

Unit 1 of 10 — foundation layer.
"""

import os
import uuid
import logging
from datetime import datetime
from flask import Flask, g, request, jsonify, session, redirect, url_for, current_app, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from jinja2 import FileSystemLoader, ChoiceLoader

# ---------------------------------------------------------------------------
# Extensions (initialized without app, bound in create_app)
# ---------------------------------------------------------------------------
db = SQLAlchemy()

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def _setup_logging(app: Flask):
    """Configure structured JSON logging for production, plain for dev."""
    is_dev = os.getenv("FLASK_ENV", "production") == "development"

    if not is_dev:
        try:
            from pythonjsonlogger import jsonlogger

            handler = logging.StreamHandler()
            fmt = jsonlogger.JsonFormatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s"
            )
            handler.setFormatter(fmt)
            app.logger.handlers.clear()
            app.logger.addHandler(handler)
            app.logger.setLevel(LOG_LEVEL)
        except ImportError:
            pass  # fallback to default Flask logger

    app.logger.info("Logging initialised", extra={"request_id": "bootstrap"})


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

def _request_id_middleware(app: Flask):
    """Attach a unique request_id to every request for tracing."""

    @app.before_request
    def _attach_request_id():
        rid = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        g.request_id = rid

    @app.after_request
    def _tag_response(response):
        rid = getattr(g, "request_id", "")
        response.headers["X-Request-Id"] = rid
        return response


def _security_headers_middleware(app: Flask):
    """Apply standard security headers to every response."""

    @app.after_request
    def _add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(self), camera=()")
        return response


def _cors_setup(app: Flask):
    """Enable CORS for API routes (Shunya endpoints)."""
    try:
        from flask_cors import CORS

        CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
        app.logger.info("CORS enabled for /api/*")
    except ImportError:
        app.logger.warning("flask-cors not available — CORS disabled")


def _rate_limiter_setup(app: Flask):
    """Rate-limit webhook and API endpoints."""
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        store = os.getenv("REDIS_URL") or "memory://"
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=store,
            default_limits=["200 per day", "50 per hour"],
            enabled=not os.getenv("DISABLE_RATE_LIMIT", ""),
        )

        # Tighten limits on Telegram webhook
        limiter.limit("10 per minute")(lambda: None)  # applied per-route in routes.py

        app.logger.info("Rate limiter initialised (storage: %s)", store)
    except ImportError:
        app.logger.warning("flask-limiter not available — rate limiting disabled")


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

def _register_error_handlers(app: Flask):
    """Return JSON for API errors, HTML for UI errors."""

    @app.errorhandler(400)
    def bad_request(e):
        return _error_response(400, "Bad request", str(e))

    @app.errorhandler(403)
    def forbidden(e):
        return _error_response(403, "Forbidden", str(e))

    @app.errorhandler(404)
    def not_found(e):
        return _error_response(404, "Not found", str(e))

    @app.errorhandler(405)
    def method_not_allowed(e):
        return _error_response(405, "Method not allowed", str(e))

    @app.errorhandler(500)
    def server_error(e):
        rid = getattr(g, "request_id", "")
        app.logger.error("Internal server error", extra={
            "request_id": rid,
            "error": str(e),
        })
        return _error_response(500, "Internal server error", "Contact support with request ID")

    def _error_response(code, message, detail=""):
        is_api = request.path.startswith("/api/") or request.path.startswith("/shunya/")
        if is_api or request.accept_mimetypes.best == "application/json":
            return jsonify({
                "error": message,
                "detail": str(detail),
                "request_id": getattr(g, "request_id", ""),
            }), code
        # HTML fallback for browser routes
        return (
            f"<!doctype html><title>{code} {message}</title>"
            f"<h1>{code}</h1><p>{message}</p>",
            code,
        )


# ---------------------------------------------------------------------------
# Health endpoints — /health, /ready, /live
# ---------------------------------------------------------------------------

# Track application startup time
_APP_START_TIME = __import__("time").time()


def _health_check(app: Flask) -> dict:
    """Run a full health check against runtime dependencies."""
    from sqlalchemy import text

    checks = {"status": "ok", "version": "1.0.0"}
    checks["uptime_seconds"] = int(__import__("time").time() - _APP_START_TIME)
    checks["environment"] = os.getenv("SHUNYA_ENVIRONMENT", os.getenv("FLASK_ENV", "production"))
    checks["request_id"] = getattr(g, "request_id", "")

    # Database check
    from app import db as _db
    try:
        _db.session.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {e}"
        checks["status"] = "degraded"

    return checks


def _register_health(app: Flask):
    """Register /health, /ready, /live endpoints.

    /health — full runtime check (DB, services, versions)
    /ready  — application readiness (dependencies available)
    /live   — process liveness (simple 200)
    """

    @app.route("/health")
    def health():
        checks = _health_check(app)
        status_code = 200 if checks["status"] == "ok" else 503
        return jsonify(checks), status_code

    @app.route("/ready")
    def ready():
        """Readiness probe — verifies the app can serve traffic."""
        result = {"status": "ok", "service": "shunya"}
        try:
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            result["database"] = "ready"
        except Exception as e:
            result["database"] = f"not_ready: {e}"
            result["status"] = "not_ready"
            return jsonify(result), 503

        result["uptime_seconds"] = int(__import__("time").time() - _APP_START_TIME)
        result["environment"] = os.getenv("SHUNYA_ENVIRONMENT", os.getenv("FLASK_ENV", "production"))
        return jsonify(result), 200

    @app.route("/live")
    def live():
        """Liveness probe — lightweight process health check."""
        return jsonify({
            "status": "alive",
            "service": "shunya",
            "uptime_seconds": int(__import__("time").time() - _APP_START_TIME),
        }), 200


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def _seed_default_workspaces():
    """Seed 3 default workspaces if they don't already exist."""
    from app.objects.legacy_models import Workspace
    defaults = [
        {"id": "spc_business", "name": "Business", "workspace_type": "business", "icon": "🏢", "color": "#6C4AE2", "description": "Business operations workspace"},
        {"id": "spc_personal", "name": "Personal", "workspace_type": "personal", "icon": "👤", "color": "#10B981", "description": "Personal workspace"},
        {"id": "spc_custom", "name": "Custom", "workspace_type": "custom", "icon": "⭐", "color": "#F59E0B", "description": "Custom project workspace"},
    ]
    for ws_data in defaults:
        existing = Workspace.query.get(ws_data["id"])
        if not existing:
            ws = Workspace(
                id=ws_data["id"],
                name=ws_data["name"],
                workspace_type=ws_data["workspace_type"],
                icon=ws_data["icon"],
                color=ws_data["color"],
                description=ws_data["description"],
                created_by="system",
            )
            db.session.add(ws)
    db.session.commit()


def create_app(config_override: dict | None = None):
    """
    Flask application factory.

    Usage:
        app = create_app()
        app.run()

    For testing, pass config_override to override DATABASE_URL etc.
    """
    load_dotenv()

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )

    # ---- Shunya OS primary template path with fallback to old templates ----
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(templates_dir),
        FileSystemLoader(templates_dir),
    ])

    # ---- Config -----------------------------------------------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "postgresql://shunya:***@localhost:5432/shunya_db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_SORT_KEYS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit

    # Apply test/config overrides
    if config_override:
        app.config.update(config_override)

    # ---- Extensions -------------------------------------------------------
    db.init_app(app)

    # ---- Register models with metadata ------------------------------------
    # Ensure all models are registered with db.Model.metadata before
    # db.create_all() is called, so their tables are created.
    # Import KnowledgeFact from the legacy knowledge_store module.
    from app.shunya.knowledge_store import KnowledgeFact  # noqa: F401
    from app.privacy.models import MemoryEligibilityPolicy  # noqa: F401
    from app.production.identity.workspace_model import Workspace  # noqa: F401
    from app.production.identity_repository import SHUNYAIdentityModel  # noqa: F401
    from app.founder.models import (  # noqa: F401
        FounderSpace, FounderObject, FounderConversation, FounderMessage, BusinessRelationship,
    )
    from app.authz.models import (  # noqa: F401
        Role, OrgMemberRole,
    )
    # Genesis Protection — Audit Log
    from app.genesis_protection import AuditLog  # noqa: F401

    # Enterprise Security — CRUD Audit Log
    from app.security.audit import AuditLog as SecurityAuditLog  # noqa: F401

    # Intake System — PROD-04
    from app.intake.models import IntakeSignal  # noqa: F401

    # Object System — PROD-05
    from app.objects.models import Object  # noqa: F401

    # Execution Engine — PROD-06
    from app.execution_engine.models import Execution  # noqa: F401

    # Intelligence Layer — PROD-07
    from app.intelligence.models import Pattern  # noqa: F401

    # Signals System — PROD-08
    from app.signals.models import Signal  # noqa: F401

    # Execution Graph — PROD-13
    from app.graph.models import ObjectRelation  # noqa: F401

    # Commitments — PROD-14
    from app.commitments.models import Commitment  # noqa: F401

    # Observations — PROD-15
    from app.observations.models import Observation  # noqa: F401

    # Generic Entity — PROD-41
    from app.core.entity import Entity  # noqa: F401

    # Customer/Lead entities — PROD-21/22
    from app.customers.models import Customer  # noqa: F401

    # Canonical consolidated models (from FOR-1/2)
    from app.models import (  # noqa: F401
        Organization, OrgMember, OrgInvitation, Department,
    )
    # Authorization engine models
    from app.authz.models import (  # noqa: F401
        Role, OrgMemberRole,
    )
    # Finance domain models
    from app.finance.models import (  # noqa: F401
        Account, LedgerEntry, JournalEntry,
        FinInvoice as Invoice, InvoiceItem, FinancePayment as Payment,
        TaxProfile, PurchaseOrder, Budget,
    )
    # Financial governance models
    from app.finance.controls import (  # noqa: F401
        ApprovalRequest, ApprovalAction, Delegation, FinancialPeriod,
    )
    # Financial evidence models
    from app.finance.evidence import (  # noqa: F401
        FinancialEvidence, EvidencePolicy,
    )

    # Phase 0 — Foundation: Workspace + Universal Object
    from app.objects.legacy_models import Workspace, ShunyaObject  # noqa: F401

    # Integration models — ContentGeneration, CachedMedia, etc.
    from app.integration.models import (  # noqa: F401
        ContentGeneration, CachedMedia, CachedEmail,
        Notification, NotificationPreference, IntegrationConfig,
        IntegrationConnection, SocialAccount, ScheduledPost, AdCampaign,
    )

    # ---- Auto-create tables (safe for first run) --------------------------
    with app.app_context():
        from sqlalchemy.exc import OperationalError, ProgrammingError
        try:
            db.create_all()
            app.logger.info("Database tables created/verified")
        except (OperationalError, ProgrammingError) as e:
            app.logger.warning(f"Tables may already exist or DB not ready: {e}")

        # ---- Seed default workspaces (Phase 0) ----------------------------
        _seed_default_workspaces()

    # ---- Middleware stack --------------------------------------------------
    _setup_logging(app)
    _request_id_middleware(app)
    _security_headers_middleware(app)
    _cors_setup(app)
    _rate_limiter_setup(app)
    _register_error_handlers(app)
    _register_health(app)

# ---- Session Resolution + Unified Auth Middleware -----------------------
    # Bridge between Flask session user_id (TeamMember) and identity_id (OrgMember)
    # Ensures session["identity_id"] and session["current_org_id"] are set
    # whenever session["user_id"] is present.
    @app.before_request
    def _resolve_identity_session():
        if session.get("identity_id"):
            return  # Already resolved
        user_id = session.get("user_id")
        if not user_id:
            return
        try:
            from app.auth import TeamMember
            from app.models import OrgMember, Organization
            tm = db.session.get(TeamMember, user_id)
            if tm:
                # Find org membership by email, preferring the primary org (most members)
                org_members = OrgMember.query.filter_by(email=tm.email, is_active=True).all()
                if org_members:
                    # Count members per org
                    org_counts = {}
                    for om in org_members:
                        cnt = OrgMember.query.filter_by(organization_id=om.organization_id, is_active=True).count()
                        org_counts[om.organization_id] = cnt
                    best_org_id = max(org_counts, key=org_counts.get)
                    org_member = next(om for om in org_members if om.organization_id == best_org_id)
                    session["identity_id"] = org_member.identity_id
                    session["current_org_id"] = org_member.organization_id
        except Exception:
            pass

    # ---- Unified Auth Middleware --------------------------------------------
    # Sets g.identity_id from Flask session cookie or X-Identity-Id header
    # so ALL routes (objects API, founder API, etc.) use the same auth source.
    @app.before_request
    def _unify_auth():
        from flask import g
        g.identity_id = (
            session.get("identity_id")
            or session.get("user_id")
            or request.headers.get("X-Identity-Id")
        )

    # ---- Enterprise Security -----------------------------------------------
    # CSRF protection (Flask-WTF) — initialized here so before_request ordering is correct
    from app.security.csrf import init_csrf
    init_csrf(app)

    # ---- Blueprints -------------------------------------------------------
    from app.auth_routes import auth_bp, login_required, inject_auth_globals
    from app.routes import main, api
    from app.production import production_bp
    from app.shunya_public import shunya_bp
    from app.production.auth import (  # noqa: F401 — registers auth routes on auth_bp
        password_reset_routes, email_verification_routes,
        mfa_routes, session_routes,
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(main)
    # Keep API at /shunya/* for backward compat (routes.py defines @api.route('/shunya/...'))
    app.register_blueprint(api)
    # Phase 0 — Foundation: Workspace + Universal Object API (registered before production_bp to avoid route conflicts)
    from app.objects.routes import objects_bp
    app.register_blueprint(objects_bp)
    # Execution Engine — PROD-06
    from app.execution_engine.routes import execution_bp
    app.register_blueprint(execution_bp)
    # Entity API — PROD-49
    from app.api.entity_routes import entity_bp
    app.register_blueprint(entity_bp)
    # Webhook API — PROD-56
    from app.api.webhook_routes import webhook_bp
    app.register_blueprint(webhook_bp)
    # Intelligence Layer — PROD-07
    from app.intelligence.pattern_routes import pattern_bp
    app.register_blueprint(pattern_bp)
    # EP-02 — Living Object Composer (single canonical creation endpoint)
    from app.object_composer.routes import composer_bp
    app.register_blueprint(composer_bp)
    # EP-03 — Universal Living Object Workspace
    from app.object_workspace.routes import workspace_bp
    app.register_blueprint(workspace_bp)
    # EP-04 — Universal Communication Runtime
    from app.communication.routes import comm_bp
    app.register_blueprint(comm_bp)
    # EP-05 — Universal Document Runtime
    from app.document_runtime.routes import doc_bp
    app.register_blueprint(doc_bp)
    # EP-06 — Universal Creative Runtime
    from app.creative_runtime.routes import creative_bp
    app.register_blueprint(creative_bp)
    # EP-07 — Universal Execution Runtime
    from app.execution_runtime.routes import exec_bp
    app.register_blueprint(exec_bp)
    # DCP-01 — Universal Travel Intelligence
    from app.travel_intelligence.routes import travel_bp
    app.register_blueprint(travel_bp)
    # Phase 0 — Foundation: File Upload API
    from app.objects.upload import upload_bp as objects_upload_bp
    app.register_blueprint(objects_upload_bp)
    # Production API v1 — Milestone X
    app.register_blueprint(production_bp)
    # SHUNYA Public — Milestone E1
    app.register_blueprint(shunya_bp)

    # SHUNYA Workspace — Phase Z1
    from app.workspace_routes import workspace_bp
    app.register_blueprint(workspace_bp)

    # Founder Experience — Sprint 1
    from app.founder import founder_bp
    app.register_blueprint(founder_bp)

    from app.upload.routes import upload_bp
    app.register_blueprint(upload_bp)

    from app.search.routes import search_bp
    app.register_blueprint(search_bp)

    from app.jobs.routes import jobs_bp
    app.register_blueprint(jobs_bp)

    from app.intention.routes import intention_bp
    app.register_blueprint(intention_bp)

    # File Manager API
    from app.objects.file_routes import file_bp
    app.register_blueprint(file_bp)

    # SHUNYA UI — first visible brain
    from app.ui import ui_bp
    app.register_blueprint(ui_bp)

    # ACT-01 — Debug control API
    from app.debug import debug_bp
    app.register_blueprint(debug_bp)

    # PRODUCT-01 — Operator API
    from app.operator import operator_bp
    app.register_blueprint(operator_bp)

    # SPA route — serves the SHUNYA operating system at root
    @app.route("/x/")
    @app.route("/x/<path:subpath>")
    def genesis_experience(subpath=""):
        # Redirect /x/ to / — the SPA now lives at root
        return redirect(url_for("main.index"))

    # FOR-1 — First Operational Release
    from app.for1 import for1_bp
    app.register_blueprint(for1_bp)

    # FOR-2 — Business Operational Readiness
    from app.for2 import for2_bp
    app.register_blueprint(for2_bp)

    # LX-02 — Canonical Reality Engine
    from app.reality_engine.routes import reality_bp
    app.register_blueprint(reality_bp)

    # FOR-2C — Relationship Intelligence Operating System
    from app.relationship import relationship_bp
    app.register_blueprint(relationship_bp)

    # FOR-2C.2 — Authorization Engine
    from app.authz import authz_bp
    app.register_blueprint(authz_bp)

    # FOR-2D — Finance Intelligence
    from app.finance import finance_bp
    app.register_blueprint(finance_bp)

    # Universal Business Discovery — Onboarding
    from app.onboarding import onboarding_bp
    app.register_blueprint(onboarding_bp)

    # Workspace Experience Framework — served by app.workspace_routes
    # (app.workspace has been superseded by the SPA workspace blueprint)

    # M6 — Connected Business
    # OAuth — Google & GitHub Sign-In
    from app.auth_oauth import oauth_bp
    app.register_blueprint(oauth_bp)

    from app.integration.routes import integration_bp
    app.register_blueprint(integration_bp)

    # Cloudinary — File uploads auto-optimized through CDN
    from app.cloudinary.routes import cloudinary_bp
    app.register_blueprint(cloudinary_bp)

    # WeasyPrint — Free unlimited PDF generation
    from app.pdf.routes import pdf_bp
    app.register_blueprint(pdf_bp)

    # Razorpay — Payment links (users configure their own keys)
    from app.razorpay.routes import razorpay_bp
    app.register_blueprint(razorpay_bp)

    # Execution Runtime — business execution, outcome ownership, recovery
    from app.execution.models import Outcome  # noqa: F401
    from app.execution.routes import execution_bp
    app.register_blueprint(execution_bp)

    # M7 — Automation
    from app.automation.routes import automation_bp
    app.register_blueprint(automation_bp)

    # Continuous Intelligence Runtime — Delta Events
    from app.events.routes import events_bp
    app.register_blueprint(events_bp)

    # Intake System — PROD-04
    from app.intake.routes import intake_bp
    app.register_blueprint(intake_bp)

    # M8 — Executive Intelligence
    from app.intelligence.routes import intelligence_bp
    app.register_blueprint(intelligence_bp)

    # M9 — Enterprise Ready
    from app.enterprise.routes import enterprise_bp
    app.register_blueprint(enterprise_bp)

# PLP Cycle 2B — Universal Business Model Engine
    from app.ubme import ubme_bp
    app.register_blueprint(ubme_bp)

    # PLP Cycle 2C — Universal Intelligence Runtime
    from app.intelligence_routes import intelligence_bp
    app.register_blueprint(intelligence_bp)

    # AI Chat — Provider Registry (Groq → fallback chain)
    from app.ai.routes import ai_bp
    app.register_blueprint(ai_bp)

    # ---- Serve screenshots for coherence board ----
    @app.route("/screenshots/<path:filename>")
    def serve_screenshot(filename):
        return send_from_directory(
            os.path.join(os.path.dirname(__file__), "..", "screenshots"),
            filename
        )

    # ---- Serve generated reports as PDFs ----
    @app.route("/reports/<path:filename>")
    def serve_report(filename):
        return send_from_directory(
            os.path.join(os.path.dirname(__file__), ".."),
            filename
        )

    # ---- Serve production frontend build ----
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

    @app.route("/assets/<path:filename>")
    def serve_frontend_asset(filename):
        """Serve built frontend assets (JS, CSS, images from the Vite build)."""
        full = os.path.join(frontend_dist, "assets", filename)
        if os.path.isfile(full):
            return send_from_directory(os.path.join(frontend_dist, "assets"), filename)
        abort(404)

    # ---- Explainable Intelligence Runtime (Phase Z3) ----
    from app.intelligence.runtime import load_scenario_data, register_explainability_middleware
    with app.app_context():
        load_scenario_data()
    register_explainability_middleware(app)

    # ---- Decision Runtime (Phase Z4) ----
    from app.decision_runtime.runtime import load_demo_decisions, register_decision_middleware
    with app.app_context():
        load_demo_decisions()
    register_decision_middleware(app)

    # ---- Organizational Cortex (Phase Z5) ----
    from app.cortex.runtime import load_cortex_data, register_cortex_middleware
    with app.app_context():
        load_cortex_data()
    register_cortex_middleware(app)

    # ---- Temporal Intelligence (Phase Z6) ----
    from app.temporal.runtime import load_temporal_data, register_temporal_middleware
    with app.app_context():
        load_temporal_data()
    register_temporal_middleware(app)

    # ---- Autonomous Organization Runtime (Phase Z7) ----
    from app.organization.runtime import load_organization_data, register_organization_middleware
    with app.app_context():
        load_organization_data()
    register_organization_middleware(app)

    # ---- Universal Planning Runtime (Phase Z8) ----
    from app.planning.runtime import load_planning_data, register_planning_middleware
    with app.app_context():
        load_planning_data()
    register_planning_middleware(app)

    # ---- Orchestration Runtime (Phase Z9) ----
    from app.orchestration.runtime import load_orchestration_data, register_orchestration_middleware
    with app.app_context():
        load_orchestration_data()
    register_orchestration_middleware(app)

    # ---- Universal Business Graph (Phase Z10) ----
    from app.graph_universal.runtime import load_graph_data, register_graph_middleware
    with app.app_context():
        load_graph_data()
    register_graph_middleware(app)

    # ---- Universal SHUNYA Space (Phase A1) ----
    from app.space.runtime import load_space_data, register_space_middleware
    with app.app_context():
        load_space_data()
    register_space_middleware(app)

    # ---- Genesis Protection — Auditing & Safeguards (Preparation) ----
    from app.genesis_routes import genesis_bp
    app.register_blueprint(genesis_bp)

    # ---- Commitments — PROD-14 ----
    from app.commitments.routes import commitments_bp
    app.register_blueprint(commitments_bp)

    # ---- Observations — PROD-15 ----
    from app.observations.routes import observations_bp
    app.register_blueprint(observations_bp)

    # ---- Leads — PROD-24 ----
    from app.leads.routes import leads_bp
    app.register_blueprint(leads_bp)

    # ---- 404 catch-all: redirect admin routes to settings ----
    @app.route("/admin/")
    @app.route("/admin/<path:subpath>")
    def admin_catchall(subpath=""):
        return redirect(url_for("main.settings"))
    
    @app.route("/ai-settings")
    def ai_settings_redirect():
        return redirect(url_for("main.settings"))

    @app.route("/relationships")
    def relationships_redirect():
        return redirect(url_for("main.index"))

    @app.route("/financial")
    @app.route("/finance")
    def finance_redirect():
        return redirect(url_for("main.index"))

    @app.errorhandler(404)
    def custom_404(e):
        # API paths return JSON; browser paths get styled HTML
        if request.path.startswith("/api/") or request.path.startswith("/shunya/"):
            from flask import jsonify
            return jsonify({
                "error": "Not found",
                "detail": str(e),
                "request_id": getattr(g, "request_id", ""),
            }), 404
        from flask import render_template_string
        html = '''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>404 | Shunya OS</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f172a;color:#fff;font-family:Inter,system-ui,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:1rem}
.container{text-align:center}
.icon{font-size:4rem;display:block;margin-bottom:1rem}
h1{font-size:1.5rem;font-weight:700;margin-bottom:.5rem}
p{color:#94a3b8;font-size:.875rem;margin-bottom:1.5rem}
a{display:inline-flex;align-items:center;gap:.5rem;padding:.625rem 1.25rem;background:#4f46e5;color:#fff;font-size:.875rem;font-weight:500;border-radius:.5rem;text-decoration:none;transition:background .2s}
a:hover{background:#4338ca}
</style>
</head>
<body>
<div class="container">
<span class="icon">🧭</span>
<h1>Page not found</h1>
<p>The page you are looking for does not exist or has been moved.</p>
<a href="/">Back to Dashboard</a>
</div>
</body>
</html>'''
        return html, 404

    # ---- Auth Middleware ----------------------------------------------------
    @app.before_request
    def _check_auth():
        """Protect all routes by default. Public paths are exempt."""
        # Bridge auth to Flask session — check HTTP-only cookie FIRST (enterprise),
        # then fall back to the legacy X-Identity-Id header (backward compat).
        identity_id = request.cookies.get("shunya_session")
        if not identity_id:
            identity_id = request.headers.get("X-Identity-Id")
        if identity_id:
            g.identity_id = identity_id
            if not session.get("user_id"):
                session["user_id"] = identity_id
                session["identity_id"] = identity_id
        
        if app.config.get("TESTING"):
            return None
        
        path = request.path
        if path.startswith("/static/") or path.startswith("/health") or path.startswith("/screenshots/") or path.startswith("/reports/") or path.startswith("/outcomes/") or path.startswith("/x/") or path.startswith("/calendar/events") or path.startswith("/audit/") or path.startswith("/app") or path.startswith("/debug") or path.startswith("/operator"):
            return None
        if path.startswith("/telegram/webhook") or path.startswith("/login") or path.startswith("/logout") or path.startswith("/api/") or path == "/voice/process" or path.startswith("/client/") or path.startswith("/auth/") or path.startswith("/identity/") or path.startswith("/space/") or path.startswith("/founder/") or path.startswith("/workspace") or path == "/" or path.startswith("/for1/") or path.startswith("/for2/") or path.startswith("/relationships/") or path.startswith("/finance/") or path.startswith("/api/v1/onboarding/") or path.startswith("/assets/") or path.startswith("/forgot-password") or path.startswith("/reset-password") or path.startswith("/request-verification") or path.startswith("/verify-email") or path.startswith("/change-password") or path == "/living":
            return None
        user_id = session.get("user_id")
        if not user_id:
            if path.startswith("/shunya/") or path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("auth.login_page", next=path))
        from app.auth import TeamMember
        # Legacy auth uses integer IDs; OS identity uses string sid_xxx
        # Only look up TeamMember for integer IDs
        user = None
        if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()):
            user = db.session.get(TeamMember, int(user_id))
        elif not path.startswith("/for1/"):
            # For non-FOR-1 routes, require a valid TeamMember
            session.clear()
            return redirect(url_for("auth.login_page"))
        if user is not None and not user.is_active:
            session.clear()
            return redirect(url_for("auth.login_page"))
        g.user = user

    @app.context_processor
    def inject_globals():
        user = getattr(g, "user", None)
        # Load ontology for navigation
        from app.ontology import registry
        from app.tenant import Tenant
        from app.communication.models import (  # noqa: F401
            CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope,
            ExternalConversation, ExternalMessage, ExternalParticipant,
            ExternalAttachmentReference, SyncCursor,
        )
        from app.communication.models import Message  # noqa: F401
        from app.communication.inbound import InboundEvent  # noqa: F401
        from app.privacy.models import (
            PrivacyPolicy, SensitivityPolicy, RetentionPolicy, MemoryEligibilityPolicy,
            SensitivityAssessment, PrivacyDecision, Restriction, ForgetRequest, PrivacyReviewItem,
        )
        from app.human_context.models import (
            HumanContextItem, ContextProposal, ContextConcept,
        )
        from app.memory.models import (
            MemoryRecord, MemoryCandidate, MemoryConcept as MemConcept,
            MemoryProvenance,
        )
        from app.evidence.models import (
            SourceReference, EvidenceLink, AssertionRecord, SourceAssessment,
        )
        from app.document.models import (
            DocumentRecord, DocumentSection, ExtractedField, DocumentComparison, ComparisonItem,
        )
        from app.llm.models import ModelRun
        ont = registry.get("travel")
        nav_modules = [m for m in ont.modules if m.enabled] if ont else []

        # Notification context
        from app.notifications import NotificationManager
        nm = NotificationManager()
        user_id = user.id if user else None
        unread_count = 0
        recent_notifications = []
        try:
            unread_count = nm.get_unread_count(user_id=user_id)
            recent_notifications = nm.get_recent_unread(user_id=user_id, limit=10)
        except Exception:
            pass
        # Celebration context
        celebration_count = 0
        try:
            from app.celebrations import CelebrationEngine
            ce = CelebrationEngine()
            celebration_count = ce.get_celebration_count_since()
        except Exception:
            pass
        return {
            "brand": "SHUNYA OS",
            "assistant_identity": "AI@shunyaos.com",
            "year": datetime.utcnow().year,
            "current_user": user,
            "is_admin": user and user.role == "admin",
            "is_manager": user and user.role == "manager",
            "current_tenant": None,
            "nav_modules": nav_modules,
            "companion_greeting": "Hey! Ready to make today productive? 🚀",
            "current_lang": "en",
            "ui_labels": {},
            "companion_suggestions": [
                {"icon": "📋", "text": "Review pending leads", "action": "/leads"},
                {"icon": "💰", "text": "Check payments", "action": "/payments"},
                {"icon": "📊", "text": "View reports", "action": "/reports"},
            ],
            # Notification context
            "unread_count": unread_count,
            "recent_notifications": recent_notifications,
            # Celebration context
            "celebration_count": celebration_count,
            "datetime": datetime,
        }

    # ---- Auto-create tables (safe for first run) --------------------------
        with app.app_context():
            from sqlalchemy.exc import OperationalError, ProgrammingError
            from app.tenant import Tenant

            # Skip create_all for :memory: test databases — test fixtures handle it
            if "sqlite:///:memory:" in str(app.config.get("SQLALCHEMY_DATABASE_URI", "")):
                pass
            else:
                try:
                    db.create_all()
                    app.logger.info("Database tables verified")
                except (OperationalError, ProgrammingError) as e:
                    app.logger.warning(f"Tables may already exist or DB not ready: {e}")

    app.logger.info(
        "SHUNYA OS initialised",
        extra={"request_id": "bootstrap", "db": app.config["SQLALCHEMY_DATABASE_URI"][:30]},
    )

    # Load persisted identities into the identity engine
    try:
        from core.os import get_os as get_shunya_os
        shunya_os = get_shunya_os()
        with app.app_context():
            from app.production.identity_repository import IdentityRepository
            repo = IdentityRepository()
            shunya_os.bootstrap()
            if hasattr(shunya_os, '_identity_runtime') and hasattr(shunya_os._identity_runtime, 'load_persisted'):
                shunya_os._identity_runtime._repository = repo
                shunya_os._identity_runtime.load_persisted()
                cnt = len(shunya_os._identity_runtime._engine._identities) if hasattr(shunya_os._identity_runtime._engine, '_identities') else 0
                app.logger.info("Loaded %d persisted identities", cnt)
    except Exception as exc:
        app.logger.warning("Could not load persisted identities: %s", exc)

    return app