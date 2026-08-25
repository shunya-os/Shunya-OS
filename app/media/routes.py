"""SHUNYA Media Routes — truthful media generation with canonical runtime state.

Endpoints:
  POST /api/v1/media/generate
  GET  /api/v1/media/assets
  GET  /api/v1/media/assets/<id>
  POST /api/v1/media/assets/<id>/attach-campaign
  GET  /api/v1/media/status
"""

import logging
from flask import Blueprint, jsonify, request, session, g, send_from_directory
from pathlib import Path

logger = logging.getLogger(__name__)

media_bp = Blueprint("media", __name__, url_prefix="/api/v1/media")

# Path to uploaded media files — uses RUNTIME_DATA_ROOT
from app.runtime_config import media_uploads_dir


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "")


def _require_auth() -> bool:
    return bool(_identity_id())


def _tenant_id() -> int:
    return session.get("current_org_id") or session.get("tenant_id", 0)


@media_bp.route("/generate", methods=["POST"])
def api_generate():
    """Generate media from intent -> visual brief -> image.

    Request body:
      prompt (str, required): Raw user intent/prompt
      platform (str, optional): Target platform (instagram-square, etc.)
      aspect_ratio (str, optional, default "1:1")
      visual_style (str, optional, default "realistic")
      business_context (dict, optional): Structured business facts

    Returns canonical result contract with explicit runtime_state.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"success": False, "error": "prompt is required"}), 400

    from app.media.service import generate_media

    result = generate_media(
        raw_prompt=prompt,
        identity_id=_identity_id(),
        platform=data.get("platform"),
        aspect_ratio=data.get("aspect_ratio", "1:1"),
        visual_style=data.get("visual_style", "realistic"),
        business_context=data.get("business_context"),
    )

    return jsonify({"success": True, "data": result})


@media_bp.route("/assets", methods=["GET"])
def api_list_assets():
    """List media assets for the authenticated user."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    limit = min(int(request.args.get("limit", 50)), 100)
    offset = int(request.args.get("offset", 0))

    from app.media.service import list_assets

    items, total = list_assets(_identity_id(), limit=limit, offset=offset)

    return jsonify({"success": True, "data": items, "total": total})


@media_bp.route("/assets/<int:asset_id>", methods=["GET"])
def api_get_asset(asset_id: int):
    """Get a specific media asset."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    from app.media.service import get_asset

    asset = get_asset(asset_id, _identity_id())
    if not asset:
        return jsonify({"success": False, "error": "Not found"}), 404

    return jsonify({"success": True, "data": asset})


@media_bp.route("/assets/<int:asset_id>/attach-campaign", methods=["POST"])
def api_attach_campaign(asset_id: int):
    """Attach a media asset to a campaign."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    campaign_id = data.get("campaign_id")
    if not campaign_id:
        return jsonify({"success": False, "error": "campaign_id is required"}), 400

    from app.media.service import attach_to_campaign

    asset = attach_to_campaign(asset_id, campaign_id, _identity_id())
    if not asset:
        return jsonify({"success": False, "error": "Asset or campaign not found"}), 404

    return jsonify({"success": True, "data": asset})


@media_bp.route("/status", methods=["GET"])
def api_status():
    """Check media generation provider status."""
    from app.media.service import get_hf_status

    hf_status = get_hf_status()

    return jsonify({
        "success": True,
        "providers": {
            "huggingface": hf_status,
        },
    })


# ── Serve uploaded media files ──────────────────────────────
@media_bp.route("/uploads/<path:filename>", methods=["GET"])
def serve_media(filename: str):
    """Serve generated media asset files."""
    from pathlib import Path
    media_root = media_uploads_dir()
    file_path = Path(media_root) / filename
    if not file_path.exists():
        return jsonify({"success": False, "error": "File not found"}), 404
    return send_from_directory(media_root, filename)