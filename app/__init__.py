"""
SHUNYA OS — Core App Unit
Flask application factory with production scaffolding.

Unit 1 of 10 — foundation layer.
"""

import os
import uuid
import logging
from datetime import datetime
from flask import Flask, g, request, jsonify, session, redirect, url_for, current_app, send_from_directory
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
# Health endpoint (built in, consolidates standalone healthcheck.py)
# ---------------------------------------------------------------------------

def _register_health(app: Flask):
    """Built-in health check — DB, table counts, uptime."""

    @app.route("/health")
    def health():
        from sqlalchemy import text
        from app.models import Lead, Payment, Supplier, Invoice, ItineraryRef

        checks = {"status": "ok"}
        try:
            db.session.execute(text("SELECT 1"))
            checks["database"] = "connected"
            checks["tables"] = {
                "leads": db.session.query(Lead).count(),
                "payments": db.session.query(Payment).count(),
                "suppliers": db.session.query(Supplier).count(),
                "invoices": db.session.query(Invoice).count(),
                "itinerary_refs": db.session.query(ItineraryRef).count(),
            }
        except Exception as e:
            checks["database"] = f"error: {e}"
            checks["status"] = "degraded"

        checks["version"] = "1.0.0"
        checks["request_id"] = getattr(g, "request_id", "")
        status_code = 200 if checks["status"] == "ok" else 503
        return jsonify(checks), status_code


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

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

    # ---- Auto-create tables (safe for first run) --------------------------
    with app.app_context():
        from sqlalchemy.exc import OperationalError, ProgrammingError
        try:
            db.create_all()
            app.logger.info("Database tables created/verified")
        except (OperationalError, ProgrammingError) as e:
            app.logger.warning(f"Tables may already exist or DB not ready: {e}")

    # ---- Middleware stack --------------------------------------------------
    _setup_logging(app)
    _request_id_middleware(app)
    _security_headers_middleware(app)
    _cors_setup(app)
    _rate_limiter_setup(app)
    _register_error_handlers(app)
    _register_health(app)

    # ---- Blueprints -------------------------------------------------------
    from app.auth_routes import auth_bp, login_required, inject_auth_globals
    from app.routes import main, api
    from app.client_portal import client_bp
    from app.production import production_bp
    from app.shunya_public import shunya_bp
    from app.production.auth import (  # noqa: F401 — registers auth routes on auth_bp
        password_reset_routes, email_verification_routes,
        mfa_routes, session_routes,
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(main)
    app.register_blueprint(client_bp)
    # Keep API at /shunya/* for backward compat (routes.py defines @api.route('/shunya/...'))
    app.register_blueprint(api)
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

    # ---- Serve screenshots for coherence board ----
    @app.route("/screenshots/<path:filename>")
    def serve_screenshot(filename):
        return send_from_directory(
            os.path.join(os.path.dirname(__file__), "..", "screenshots"),
            filename
        )

    # ---- Explainable Intelligence Runtime (Phase Z3) ----
    from app.intelligence.runtime import load_scenario_data, register_explainability_middleware
    with app.app_context():
        load_scenario_data()
    register_explainability_middleware(app)

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
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body class="bg-[#0f172a] text-white font-sans min-h-screen flex items-center justify-center p-4">
  <div class="text-center">
    <span class="text-6xl block mb-4">🧭</span>
    <h1 class="text-2xl font-bold mb-2">Page not found</h1>
    <p class="text-slate-400 text-sm mb-6">The page you are looking for does not exist or has been moved.</p>
    <a href="/" class="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors">Back to Dashboard</a>
  </div>
</body>
</html>'''
        return html, 404

    # ---- Auth Middleware ----------------------------------------------------
    @app.before_request
    def _check_auth():
        """Protect all routes by default. Public paths are exempt."""
        if app.config.get("TESTING"):
            return None
        path = request.path
        if path.startswith("/static/") or path.startswith("/health") or path.startswith("/screenshots/"):
            return None
        if path.startswith("/telegram/webhook") or path.startswith("/login") or path.startswith("/logout") or path.startswith("/api/") or path == "/voice/process" or path.startswith("/client/") or path.startswith("/auth/") or path.startswith("/identity/") or path.startswith("/space/") or path.startswith("/founder/") or path.startswith("/workspace") or path == "/":
            return None
        user_id = session.get("user_id")
        if not user_id:
            if path.startswith("/shunya/") or path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("auth.login_page", next=path))
        from app.auth import TeamMember
        user = db.session.get(TeamMember, user_id)
        if not user or not user.is_active:
            session.clear()
            return redirect(url_for("auth.login_page"))
        from flask import g
        g.user = user

    @app.context_processor
    def inject_globals():
        user = getattr(g, "user", None)
        # Load ontology for navigation
        from app.ontology import registry
        from app.tenant import Tenant
        from app.communication.models import (
            CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope,
            ExternalConversation, ExternalMessage, ExternalParticipant,
            ExternalAttachmentReference, SyncCursor,
        )
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
    return app