"""FOR-2C.2: Authorization Engine — Blueprint registration."""
from flask import Blueprint

authz_bp = Blueprint('authz', __name__)


def register_routes():
    """Import all route files. Called after blueprint is available."""
    from app.authz import routes as authz_routes  # noqa: F401


register_routes()