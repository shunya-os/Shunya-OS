"""FOR-2D: Finance Intelligence — Blueprint registration."""
from flask import Blueprint

finance_bp = Blueprint("finance", __name__, template_folder="templates",
                       url_prefix="/api/v1/finance")


def register_routes():
    """Import all route files after blueprint is available."""
    from app.finance import routes_api  # noqa: F401


register_routes()