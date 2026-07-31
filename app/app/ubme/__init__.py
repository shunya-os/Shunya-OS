"""Universal Business Model Engine — Public API.

Usage:
    from app.ubme import ubme_bp
    app.register_blueprint(ubme_bp)

All routes are under /api/ubme/
"""

from flask import Blueprint

ubme_bp = Blueprint("ubme", __name__, url_prefix="/api/ubme")

from app.ubme import routes  # noqa: E402, F401