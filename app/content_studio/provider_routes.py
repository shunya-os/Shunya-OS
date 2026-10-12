"""
Image Provider Routes — API endpoints for provider registry and generation.
"""
import os
from flask import Blueprint, jsonify, request, session
from app.authz.decorators import session_required
from app.content_studio.image_providers import (
    get_registry, init_providers, ImageQualityTier,
)

provider_bp = Blueprint("image_providers", __name__, url_prefix="/api/v1/content")


@provider_bp.route("/providers", methods=["GET"])
@session_required
def list_providers():
    """List available image providers and tiers."""
    registry = get_registry()
    if not registry.get_available_tiers():
        init_providers()
    return jsonify({
        "success": True,
        "tiers": registry.get_available_tiers(),
    })


@provider_bp.route("/generate", methods=["POST"])
@session_required
def generate_image():
    """Generate an image using the specified tier or provider."""
    from app.media.service import _save_image_file

    data = request.get_json() or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"success": False, "error": "Prompt is required"}), 400

    # SHUNYA Safety Governance gate (generation prompts)
    try:
        from flask import g
        from app.shunya.safety_governance import check_request_safety
        _safety_error = check_request_safety(
            prompt,
            identity_id=str(getattr(g, "identity_id", "") or session.get("identity_id", "") or ""),
            tenant_id=getattr(g, "current_org_id", None) or session.get("current_org_id") or 0,
        )
    except Exception:
        _safety_error = (
            {"error": "Safety governance unavailable — request blocked"},
            503,
        )
    if _safety_error:
        return jsonify(_safety_error[0]), _safety_error[1]

    tier_str = data.get("tier", "economy")
    provider_name = data.get("provider")

    try:
        tier = ImageQualityTier(tier_str)
    except ValueError:
        return jsonify({"success": False, "error": f"Invalid tier: {tier_str}"}), 400

    registry = get_registry()
    if not registry.get_available_tiers():
        init_providers()

    # Check if the requested provider is available
    if provider_name:
        provider_config = registry.get_provider(provider_name)
        if not provider_config:
            return jsonify({"success": False, "error": f"Unknown provider: {provider_name}"}), 400
        # Check API key
        if provider_config.api_key_env:
            key = os.environ.get(provider_config.api_key_env)
            if not key:
                return jsonify({
                    "success": False,
                    "error": f"{provider_config.api_key_env} not configured",
                    "provider": provider_name,
                    "requires_credentials": True,
                }), 400

    result = registry.generate(prompt, tier=tier, provider_name=provider_name)

    if not result.success:
        return jsonify({
            "success": False,
            "error": result.error or "Generation failed",
            "provider": result.provider,
            "model": result.model,
        }), 500

    # Save the generated image
    identity_id = session.get("identity_id", "anonymous")
    try:
        file_path = _save_image_file(result.image_bytes, identity_id)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to save image: {e}",
        }), 500

    return jsonify({
        "success": True,
        "image_url": file_path,
        "provider": result.provider,
        "model": result.model,
        "tier": result.tier,
        "size": len(result.image_bytes),
    })
