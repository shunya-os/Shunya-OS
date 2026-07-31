"""FOR-2 — Blueprint registration."""
from flask import Blueprint

for2_bp = Blueprint("for2", __name__, template_folder="templates")

from app.for2 import routes  # noqa: F401, E402