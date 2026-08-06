"""EP-06 — Universal Creative Runtime API."""

from flask import Blueprint, jsonify, request, g

from .runtime import get_creative_runtime, CREATIVE_TYPES, COMMUNICATION_INTENTS

creative_bp = Blueprint("creative", __name__, url_prefix="/api/v1/creative")


def _require_identity():
    identity_id = getattr(g, 'identity_id', None)
    if identity_id:
        return identity_id
    return request.headers.get("X-Identity-Id")


@creative_bp.route("/types", methods=["GET"])
def list_creative_types():
    return jsonify({"success": True, "data": {
        "creative_types": CREATIVE_TYPES,
        "intents": {k: {"label": v["label"], "description": v["description"],
                         "suggested_types": v["suggested_types"]}
                    for k, v in COMMUNICATION_INTENTS.items()},
    }})


@creative_bp.route("", methods=["POST"])
def create_asset():
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"success": False, "error": "title is required"}), 400
    rt = get_creative_runtime()
    asset = rt.create_asset(title=title, intent=data.get("intent", "inform"),
                            creative_type=data.get("creative_type", "presentation"),
                            purpose=data.get("purpose", ""), content=data.get("content", ""),
                            format=data.get("format", "svg"))
    return jsonify({"success": True, "data": asset.to_dict()}), 201


@creative_bp.route("", methods=["GET"])
def list_assets():
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    creative_type = request.args.get("type")
    rt = get_creative_runtime()
    assets = [a.to_dict() for a in rt.list_assets(creative_type=creative_type)]
    return jsonify({"success": True, "data": assets})


@creative_bp.route("/<asset_id>", methods=["GET"])
def get_asset(asset_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_creative_runtime()
    asset = rt.get_asset(asset_id)
    if not asset:
        return jsonify({"success": False, "error": "Asset not found"}), 404
    return jsonify({"success": True, "data": asset.to_dict()})


@creative_bp.route("/<asset_id>/render", methods=["GET"])
def render_asset(asset_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    target_format = request.args.get("format", "svg")
    rt = get_creative_runtime()
    result = rt.render_asset(asset_id, target_format)
    if result is None:
        return jsonify({"success": False, "error": "Asset not found"}), 404
    return jsonify({"success": True, "data": {"content": result, "format": target_format}})


@creative_bp.route("/generate", methods=["POST"])
def generate_representations():
    """Generate multiple creative representations from one intent.

    POST /api/v1/creative/generate
    { "title": "...", "intent": "launch_campaign" }
    → creates one asset per suggested creative type, all sharing the same intent.
    Intent drives representation selection — this is the canonical generate endpoint.
    """
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    intent = data.get("intent", "inform").strip()
    if not title:
        return jsonify({"success": False, "error": "title is required"}), 400
    rt = get_creative_runtime()
    assets = rt.generate_representations(title=title, intent=intent, content=data.get("content", ""))
    return jsonify({"success": True, "data": [a.to_dict() for a in assets],
                    "message": f"Generated {len(assets)} representations from intent '{intent}'"}), 201


@creative_bp.route("/search", methods=["GET"])
def search_assets():
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"success": False, "error": "q parameter required"}), 400
    rt = get_creative_runtime()
    results = rt.search(query)
    return jsonify({"success": True, "data": results})


@creative_bp.route("/brands", methods=["GET", "POST"])
def brands():
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_creative_runtime()
    if request.method == "GET":
        return jsonify({"success": True, "data": [b.to_dict() for b in rt.list_brands()]})
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "error": "name is required"}), 400
    brand = rt.create_brand(name=name, primary_color=data.get("primary_color", "#BFAC8B"),
                            secondary_color=data.get("secondary_color", "#2A2626"),
                            tone=data.get("tone", "professional"), voice=data.get("voice", ""))
    return jsonify({"success": True, "data": brand.to_dict()}), 201


@creative_bp.route("/templates", methods=["GET", "POST"])
def templates():
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_creative_runtime()
    if request.method == "GET":
        creative_type = request.args.get("type")
        return jsonify({"success": True, "data": [t.to_dict() for t in rt.list_templates(creative_type)]})
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "error": "name is required"}), 400
    tpl = rt.create_template(name=name, creative_type=data.get("creative_type", "presentation"),
                             content=data.get("content", ""), brand_id=data.get("brand_id", ""))
    return jsonify({"success": True, "data": tpl.to_dict()}), 201


@creative_bp.route("/<asset_id>/summary", methods=["GET"])
def asset_summary(asset_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_creative_runtime()
    return jsonify({"success": True, "data": {"summary": rt.generate_summary(asset_id)}})


@creative_bp.route("/<asset_id>/variant", methods=["GET"])
def suggest_variant(asset_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_creative_runtime()
    return jsonify({"success": True, "data": {"suggestion": rt.suggest_variant(asset_id)}})


@creative_bp.route("/<asset_id>/brand", methods=["GET"])
def brand_consistency(asset_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_creative_runtime()
    return jsonify({"success": True, "data": {"analysis": rt.analyze_brand_consistency(asset_id)}})