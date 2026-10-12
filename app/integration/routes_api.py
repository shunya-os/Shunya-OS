"""Integration API Routes — status, connect, sync, list.

GET  /api/v1/integrations     — List all integrations with status
POST /api/v1/integrations/sync — Trigger sync on all connected integrations
GET  /api/v1/integrations/{name} — Get integration details
"""

from flask import Blueprint, jsonify
from app.authz.decorators import session_required

from app.integration.registry import registry

integration_bp = Blueprint("integrations_v2", __name__, url_prefix="/api/v1/integrations")


@integration_bp.route("", methods=["GET"])
@session_required
def list_integrations():
    """List all registered integrations with their status."""
    return jsonify({"integrations": registry.list()})


@integration_bp.route("/sync", methods=["POST"])
@session_required
def sync_all():
    """Trigger sync on all connected integrations."""
    results = registry.sync_all()
    return jsonify({"results": results})


@integration_bp.route("/connect-all", methods=["POST"])
@session_required
def connect_all():
    """Attempt to connect all configured integrations."""
    results = registry.connect_all()
    return jsonify({"results": results})