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
from app.authz.decorators import require_permission


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "")


def _require_auth() -> bool:
    return bool(_identity_id())


def _tenant_id() -> int:
    return session.get("current_org_id") or session.get("tenant_id", 0)


def _organization_id() -> int:
    """Resolve the current organization ID from session or flask.g.

    Returns the real org ID or 0. Callers MUST reject 0 as missing ownership.
    """
    return (
        session.get("current_org_id")
        or g.get("current_org_id")
        or session.get("tenant_id", 0)
    )


def _workspace_id() -> str:
    """Resolve the current workspace ID from session or flask.g.

    Returns the real workspace ID or empty string. Returns empty string
    instead of a synthetic default like 'spc_business'.
    """
    return (
        session.get("workspace_id")
        or g.get("workspace_id")
        or ""
    )


@media_bp.route("/generate", methods=["POST"])
@require_permission("knowledge.upload")
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
        organization_id=_organization_id(),
        workspace_id=_workspace_id(),
        platform=data.get("platform"),
        aspect_ratio=data.get("aspect_ratio", "1:1"),
        visual_style=data.get("visual_style", "realistic"),
        business_context=data.get("business_context"),
    )

    return jsonify({"success": True, "data": result})


@media_bp.route("/assets", methods=["GET"])
@require_permission("knowledge.view")
def api_list_assets():
    """List media assets for the authenticated user.

    Query params:
        lifecycle_status: Filter by lifecycle status (active, archived, trashed).
                          Default: active assets only.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    limit = min(int(request.args.get("limit", 50)), 100)
    offset = int(request.args.get("offset", 0))
    lifecycle_status = request.args.get("lifecycle_status") or None

    from app.media.service import list_assets

    items, total = list_assets(_identity_id(), limit=limit, offset=offset, lifecycle_status=lifecycle_status)

    return jsonify({"success": True, "data": items, "total": total})


@media_bp.route("/assets/<int:asset_id>", methods=["GET"])
@require_permission("knowledge.view")
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
@require_permission("knowledge.upload")
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
@require_permission("knowledge.view")
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


# ── Media Lifecycle (Directive 08 §E) ──────────────────────────


@media_bp.route("/assets/<int:asset_id>/archive", methods=["POST"])
@require_permission("knowledge.upload")
def api_archive_asset(asset_id: int):
    """Archive an active media asset."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    from app.media.service import archive_asset
    asset = archive_asset(asset_id, _identity_id())
    if not asset:
        return jsonify({"success": False, "error": "Asset not found or not in active state"}), 404
    return jsonify({"success": True, "data": asset})


@media_bp.route("/assets/<int:asset_id>/trash", methods=["POST"])
@require_permission("knowledge.upload")
def api_trash_asset(asset_id: int):
    """Move an asset to trash (recoverable deletion)."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    from app.media.service import trash_asset
    asset = trash_asset(asset_id, _identity_id())
    if not asset:
        return jsonify({"success": False, "error": "Asset not found or cannot be trashed"}), 404
    return jsonify({"success": True, "data": asset})


@media_bp.route("/assets/<int:asset_id>/restore", methods=["POST"])
@require_permission("knowledge.upload")
def api_restore_asset(asset_id: int):
    """Restore an asset from trash or archive back to active."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    from app.media.service import restore_asset
    asset = restore_asset(asset_id, _identity_id())
    if not asset:
        return jsonify({"success": False, "error": "Asset not found or not in recoverable state"}), 404
    return jsonify({"success": True, "data": asset})


@media_bp.route("/assets/<int:asset_id>/permanent-delete", methods=["DELETE"])
@require_permission("knowledge.upload")
def api_permanent_delete_asset(asset_id: int):
    """Permanently delete a trashed asset (irreversible)."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    from app.media.service import permanently_delete_asset
    if not permanently_delete_asset(asset_id, _identity_id()):
        return jsonify({"success": False, "error": "Asset not found, not in trashed state, or not authorized"}), 404
    return jsonify({"success": True})


# ── Serve uploaded media files ──────────────────────────────
@media_bp.route("/uploads/<path:filename>", methods=["GET"])
@require_permission("knowledge.view")
def serve_media(filename: str):
    """Serve generated media asset files."""
    from pathlib import Path
    media_root = media_uploads_dir()
    file_path = Path(media_root) / filename
    if not file_path.exists():
        return jsonify({"success": False, "error": "File not found"}), 404
    return send_from_directory(media_root, filename)