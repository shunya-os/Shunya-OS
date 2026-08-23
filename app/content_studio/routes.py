"""SHUNYA Content Studio API — Content Generation, History, and Media Pipeline.

Wires Content Studio 4.0 frontend to canonical persistence.
"""
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, session, g

logger = logging.getLogger(__name__)

content_bp = Blueprint("content_studio", __name__, url_prefix="/api/v1/content")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "")


def _require_auth() -> bool:
    return bool(_identity_id())


def _tenant_id() -> int:
    return session.get("current_org_id") or session.get("tenant_id", 0)


@content_bp.route("/generate", methods=["POST"])
def api_generate():
    """Generate content via AI provider chain."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"success": False, "error": "prompt is required"}), 400

    content_type = data.get("content_type", "blog_post")
    tone = data.get("tone", "professional")
    platform = data.get("platform")
    target_audience = data.get("target_audience")
    word_count = int(data.get("word_count", 300))
    additional_instructions = data.get("additional_instructions", "")

    from app.integration.service import generate_content
    result = generate_content(
        prompt=prompt,
        content_type=content_type,
        tone=tone,
        platform=platform,
        target_audience=target_audience,
        word_count=word_count,
        additional_instructions=additional_instructions,
    )

    # Persist the generation
    if result.get("success"):
        try:
            from app.integration.models import ContentGeneration
            from app import db
            cg = ContentGeneration(
                identity_id=_identity_id(),
                content_type=content_type,
                platform=platform or "",
                prompt=prompt,
                generated_content=result.get("content", ""),
                tone=tone,
                target_audience=target_audience,
                word_count=word_count,
                ai_model="provider_chain",
            )
            db.session.add(cg)
            db.session.commit()
            result["id"] = cg.id
        except Exception as e:
            logger.warning("Content persistence error: %s", e)

    return jsonify(result)


@content_bp.route("/history", methods=["GET"])
def api_history():
    """List recent content generations."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    limit = min(int(request.args.get("limit", 50)), 100)
    content_type = request.args.get("content_type")

    try:
        from app.integration.models import ContentGeneration
        from app import db

        q = ContentGeneration.query.filter_by(identity_id=_identity_id())
        if content_type:
            q = q.filter_by(content_type=content_type)
        items = q.order_by(ContentGeneration.created_at.desc()).limit(limit).all()

        return jsonify({
            "success": True,
            "data": [item.to_dict() for item in items],
            "total": len(items),
        })
    except Exception as e:
        logger.warning("Content history error: %s", e)
        return jsonify({"success": True, "data": [], "total": 0})


@content_bp.route("/history/<int:item_id>", methods=["GET"])
def api_get_item(item_id: int):
    """Get a specific content generation."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.integration.models import ContentGeneration
        item = ContentGeneration.query.get(item_id)
        if not item or item.identity_id != _identity_id():
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "data": item.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@content_bp.route("/history/<int:item_id>/favorite", methods=["POST"])
def api_toggle_favorite(item_id: int):
    """Toggle favorite status."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.integration.models import ContentGeneration
        from app import db
        item = ContentGeneration.query.get(item_id)
        if not item or item.identity_id != _identity_id():
            return jsonify({"success": False, "error": "Not found"}), 404
        item.is_favorited = not item.is_favorited
        db.session.commit()
        return jsonify({"success": True, "is_favorited": item.is_favorited})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@content_bp.route("/history/<int:item_id>", methods=["DELETE"])
def api_delete_item(item_id: int):
    """Delete a content generation."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.integration.models import ContentGeneration
        from app import db
        item = ContentGeneration.query.get(item_id)
        if not item or item.identity_id != _identity_id():
            return jsonify({"success": False, "error": "Not found"}), 404
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── Universal Inhibition Layer (SUIL) Endpoint ──

LEVELS = {
    0: "ALLOW",
    1: "OBSERVE",
    2: "GUARD",
    3: "CONFIRM",
    4: "RESTRICT",
    5: "BLOCK",
}


def evaluate_inhibition(action_type: str, context: dict) -> dict:
    """Universal inhibition evaluation.

    Returns deterministic risk level for any action type.
    """
    tenant_id = context.get("tenant_id", 0)
    identity = context.get("identity_id", "")
    action = action_type

    # Tenant boundary
    if not tenant_id:
        return {"allowed": False, "level": 5, "reason": "No tenant context"}

    # Budget protection (campaign spend)
    if "spend" in action or "campaign" in action:
        budget = context.get("budget", 0)
        if budget > 1000000:
            return {"allowed": False, "level": 4, "reason": "Budget exceeds limit, requires approval"}
        if budget > 500000:
            return {"allowed": True, "level": 3, "reason": "High budget, confirm required"}

    # Media generation checks
    if "media" in action or "generate" in action:
        if not identity:
            return {"allowed": False, "level": 5, "reason": "Authentication required"}
        return {"allowed": True, "level": 0, "reason": "Safe action"}

    # Publication checks
    if "publish" in action or "execute" in action:
        return {"allowed": True, "level": 3, "reason": "Requires confirmation before execution"}

    # AI command execution
    if "ai" in action and ("execute" in action or "create" in action):
        return {"allowed": True, "level": 2, "reason": "Guardrails apply"}

    # Default: allow with observe
    return {"allowed": True, "level": 1, "reason": "Observe"}


@content_bp.route("/inhibit", methods=["POST"])
def api_inhibit():
    """Evaluate a proposed action via the Universal Inhibition Layer.

    Can be called with basic session auth or, for higher-sensitivity actions,
    with canonical permission checks.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    action_type = data.get("action_type", "")
    if not action_type:
        return jsonify({"success": False, "error": "action_type is required"}), 400

    context = {
        "tenant_id": _tenant_id(),
        "identity_id": _identity_id(),
        **{k: v for k, v in data.items() if k not in ("action_type",)},
    }

    decision = evaluate_inhibition(action_type, context)

    return jsonify({
        "success": True,
        "action_type": action_type,
        "allowed": decision["allowed"],
        "level": decision["level"],
        "level_label": LEVELS.get(decision["level"], "UNKNOWN"),
        "reason": decision["reason"],
    })


@content_bp.route("/inhibit/authz", methods=["POST"])
def api_inhibit_authz():
    """Evaluate inhibition via canonical permission-based auth.

    Uses the `authz.decorators.require_permission` chain so that SUIL
    integrates with the canonical authorization engine rather than
    bypassing it. Requires the 'admin.view_audit' permission.
    """
    from app.authz.decorators import require_permission, _resolve_identity, _resolve_org_id

    # Apply the canonical permission check inline
    identity = _resolve_identity()
    if not identity:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"success": False, "error": "No organization selected"}), 400

    from app.authz.services import check_permission
    if not check_permission(org_id, identity, "admin.view_audit"):
        return jsonify({
            "success": False,
            "error": "Forbidden: admin.view_audit permission required",
        }), 403

    data = request.get_json(silent=True) or {}
    action_type = data.get("action_type", "")
    if not action_type:
        return jsonify({"success": False, "error": "action_type is required"}), 400

    context = {
        "tenant_id": org_id,
        "identity_id": identity,
        **{k: v for k, v in data.items() if k not in ("action_type",)},
    }

    decision = evaluate_inhibition(action_type, context)

    return jsonify({
        "success": True,
        "action_type": action_type,
        "allowed": decision["allowed"],
        "level": decision["level"],
        "level_label": LEVELS.get(decision["level"], "UNKNOWN"),
        "reason": decision["reason"],
        "authz_gate": "admin.view_audit",
    })


@content_bp.route("/health", methods=["GET"])
def api_health():
    """Health check."""
    return jsonify({
        "status": "ok",
        "service": "content-studio",
        "endpoints": [
            "POST /api/v1/content/generate",
            "GET /api/v1/content/history",
            "GET /api/v1/content/history/<id>",
            "POST /api/v1/content/history/<id>/favorite",
            "DELETE /api/v1/content/history/<id>",
            "POST /api/v1/content/inhibit",
            "POST /api/v1/content/inhibit/authz",
        ],
    })