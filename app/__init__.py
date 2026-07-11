"""Shunya OS — Application Factory."""
import os, logging, uuid
from flask import Flask, g, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from app.extensions import db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper())


def create_app(config_name: str = "development"):
    app = Flask(__name__,
                template_folder=os.path.join(BASE_DIR, "templates"),
                static_folder=os.path.join(BASE_DIR, "static"))

    # Load config
    import config as cfg
    cfg_obj = cfg.config_by_name.get(config_name, cfg.Config)
    app.config.from_object(cfg_obj)

    # Ensure upload dir
    os.makedirs(app.config.get("UPLOAD_DIR", "media"), exist_ok=True)

    # Init extensions
    db.init_app(app)
    CORS(app, origins="*", supports_credentials=True)

    # Middleware
    _setup_logging(app)
    _request_id_middleware(app)

    # Register everything
    with app.app_context():
        _register_blueprints(app)
        _register_error_handlers(app)
        _register_health(app)
        _register_context_processors(app)
        db.create_all()

    app.logger.info("Shunya OS initialised")
    return app


# ---------------------------------------------------------------------------
# Blueprints
# ---------------------------------------------------------------------------

def _register_blueprints(app):
    from app.routes.auth import auth_bp, login_redirect_bp
    from app.routes.entities import entities_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.settings import settings_bp
    from app.routes.client_portal import client_bp
    from app.routes.api import api_bp
    from app.routes.voice import voice_bp
    from app.shunya.whatsapp import whatsapp_bp
    from app.shunya.ingestion import ingestion_bp
    from app.shunya.finance import finance_bp
    from app.shunya.operations import ops_bp
    from app.shunya.onboarding import onboarding_bp
    from app.shunya.ai_settings import ai_settings_bp
    from app.shunya.module_builder_routes import module_builder_bp
    from app.shunya.governance_routes import governance_bp
    from app.shunya.agent_routes import agent_bp
    from app.shunya.theme_routes import theme_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(login_redirect_bp)
    app.register_blueprint(entities_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(client_bp, url_prefix="/client")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(voice_bp)
    app.register_blueprint(whatsapp_bp)
    app.register_blueprint(ingestion_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(ops_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(ai_settings_bp)
    app.register_blueprint(module_builder_bp)
    app.register_blueprint(governance_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(theme_bp)


# ---------------------------------------------------------------------------
# Auth middleware — protect all routes by default
# ---------------------------------------------------------------------------

PUBLIC_PATHS = ("/auth/", "/health", "/static/", "/client/")


def _register_context_processors(app):
    @app.context_processor
    def inject_globals():
        user = getattr(g, "user", None)
        tenant = getattr(g, "tenant", None)
        brand_colors = None
        if tenant:
            from app.shunya.theme import get_brand_colors
            brand_colors = get_brand_colors(tenant)
        return {
            "current_user": user,
            "current_tenant": tenant,
            "brand_colors": brand_colors,
            "year": __import__("datetime").datetime.utcnow().year,
            "app_name": "Shunya OS",
        }


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        return "<h1>404</h1><p>Page not found</p>", 404

    @app.errorhandler(500)
    def server_error(e):
        rid = getattr(g, "request_id", "")
        app.logger.error("Internal server error", extra={"request_id": rid, "error": str(e)})
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal error", "request_id": rid}), 500
        return "<h1>500</h1><p>Internal server error. Contact support.</p>", 500


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def _register_health(app):
    @app.route("/health")
    def health():
        try:
            db.session.execute(db.text("SELECT 1"))
            return jsonify({"status": "ok", "database": "connected"})
        except Exception as e:
            return jsonify({"status": "degraded", "database": str(e)}), 503


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _setup_logging(app):
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s"
    ))
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(LOG_LEVEL)


def _request_id_middleware(app):
    @app.before_request
    def _set_request_id():
        g.request_id = request.headers.get("X-Request-Id", uuid.uuid4().hex[:12])
