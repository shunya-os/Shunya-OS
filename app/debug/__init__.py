from flask import Blueprint

debug_bp = Blueprint("debug", __name__, url_prefix="/debug")

from app.debug import routes  # noqa: F401