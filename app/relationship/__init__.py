"""FOR-2C Relationship Intelligence Operating System — Blueprint registration."""
from flask import Blueprint

relationship_bp = Blueprint("relationship", __name__, template_folder="templates", url_prefix="/relationships")


def register_routes():
    """Import and register all route files. Called after blueprint is available."""
    from app.relationship import routes_api  # noqa: F401
    from app.relationship import routes_ui  # noqa: F401
    from app.relationship import search  # noqa: F401


register_routes()