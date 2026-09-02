"""SHUNYA Campaign Routes — Provider Connection, Discovery, and Campaign Creation.

Provides the REST API surface for the campaign adapter system (Workstream F).
Follows the same patterns as other SHUNYA route modules:
- POST /api/v1/campaign/providers/connect — connect to a campaign provider
- GET /api/v1/campaign/providers — list available providers
- POST /api/v1/campaign/create — create a campaign via a provider
"""
import logging
from flask import Blueprint, jsonify, request, session, g
from app.authz.decorators import _resolve_org_id

logger = logging.getLogger(__name__)

campaign_bp = Blueprint("campaign", __name__, url_prefix="/api/v1/campaign")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "")


def _require_auth() -> bool:
    return bool(_identity_id())


def _tenant_id() -> int | None:
    return _resolve_org_id()


@campaign_bp.route("/providers/connect", methods=["POST"])
def api_campaign_connect():
    """Connect to a campaign provider.

    Accepts provider name and optional config, validates credentials,
    and returns the connection status.

    Request:
        {"provider": "meta"|"google", "config": {...}}
    Response:
        {"success": true, "provider": "...", "status": "ok"|"credentials_missing"|...}
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    provider_name = data.get("provider", "").strip().lower()
    if not provider_name:
        return jsonify({"success": False, "error": "provider is required"}), 400

    from app.campaign.adapter import get_registry

    registry = get_registry()
    provider = registry.get(provider_name)
    if not provider:
        return jsonify({
            "success": False,
            "error": f"Unknown provider: {provider_name}",
            "available": registry.list_providers(),
        }), 404

    credential_status = provider.check_credentials()

    return jsonify({
        "success": credential_status == "ok",
        "provider": provider_name,
        "status": credential_status,
        "detail": f"Provider '{provider_name}' credential check: {credential_status}",
    })


@campaign_bp.route("/providers", methods=["GET"])
def api_campaign_providers():
    """List registered and available campaign providers.

    Returns all known providers and indicates which have valid credentials.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    from app.campaign.adapter import get_registry

    registry = get_registry()
    providers = registry.list_providers()
    available = registry.available_providers()

    result = []
    for name in providers:
        p = registry.get(name)
        if p:
            cred_status = p.check_credentials()
            result.append({
                "name": name,
                "connected": cred_status == "ok",
                "credential_status": cred_status,
            })

    return jsonify({
        "success": True,
        "providers": result,
        "default": registry._default_provider or "meta",
    })


@campaign_bp.route("/create", methods=["POST"])
def api_campaign_create():
    """Create a campaign through a specified provider.

    Request:
        {"provider": "meta"|"google", "name": "...",
         "objective": "...", "budget": 100000, ...}
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    provider_name = data.get("provider", "").strip().lower()
    if not provider_name:
        return jsonify({"success": False, "error": "provider is required"}), 400

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "error": "name is required"}), 400

    from app.campaign.adapter import get_registry

    registry = get_registry()
    provider = registry.resolve(provider_name)
    if not provider:
        return jsonify({
            "success": False,
            "error": f"Provider not found: {provider_name}",
            "available": registry.list_providers(),
        }), 404

    # Check inhibition via SUIL for budget-sensitive actions
    budget = data.get("budget", 0)
    from app.content_studio.routes import evaluate_inhibition

    inhibition = evaluate_inhibition("campaign_create", {
        "tenant_id": _tenant_id(),
        "identity_id": _identity_id(),
        "budget": budget,
    })
    if not inhibition.get("allowed", True):
        return jsonify({
            "success": False,
            "error": "Campaign creation blocked by policy",
            "inhibition": inhibition,
        }), 403

    # Build config for provider
    config = {k: v for k, v in data.items() if k not in ("provider",)}
    result = provider.create_campaign(config)

    return jsonify(result)


@campaign_bp.route("/health", methods=["GET"])
def api_campaign_health():
    """Health check for campaign service."""
    from app.campaign.adapter import get_registry

    registry = get_registry()
    return jsonify({
        "status": "ok",
        "service": "campaign",
        "providers": registry.list_providers(),
    })