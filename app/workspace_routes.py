"""SHUNYA Phase B1 -- Universal Workspace Routes.

All `/workspace/*` routes now serve the React SPA shell,
which is the canonical workspace runtime.
"""
import os
from flask import Blueprint, send_from_directory

workspace_bp = Blueprint("workspace", __name__, template_folder="../templates")

_FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


def _serve_spa():
    idx = os.path.join(_FRONTEND_DIST, "index.html")
    if os.path.exists(idx):
        return send_from_directory(_FRONTEND_DIST, "index.html")
    return "Frontend not built. Run `cd frontend && npm run build`", 503


@workspace_bp.route("/")
def workspace_home():
    """Serve the SPA shell -- the React SPA handles workspace routing."""
    return _serve_spa()


@workspace_bp.route("/object/<object_id>")
def workspace_object(object_id):
    """Serve the SPA shell -- the React SPA handles object views."""
    return _serve_spa()