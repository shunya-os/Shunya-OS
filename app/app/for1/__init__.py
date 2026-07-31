"""FOR-1 — Blueprint registration and init."""
from flask import Blueprint

for1_bp = Blueprint("for1", __name__, template_folder="templates")

from app.for1 import routes  # noqa: F401, E402 — register routes