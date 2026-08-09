from flask import Blueprint

operator_bp = Blueprint("operator", __name__, url_prefix="/operator")

from app.operator import routes  # noqa: F401 E402