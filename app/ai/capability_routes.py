"""SHUNYA — Capability API Routes (ZG-03 B2 add-on).

Exposes the provider-neutral capability registry:
  GET  /api/v1/capabilities            — per-capability provider status
  GET  /api/v1/capabilities/summary    — one row per capability
  POST /api/v1/capabilities/execute    — run a capability (text/image/speech/…)
  GET  /api/v1/capabilities/diagnostics— deep provider probes (opt-in)

All responses are truthful: availability is computed (key + model validity +
outage), failures carry ErrorClass, and paid providers never run unless the
caller explicitly passes paid_ok (default off).

No secrets are ever returned — only booleans, classification and non-secret
model ids.
"""
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, session, g

from app.authz.decorators import session_required
from app.ai import capabilities as caps

capability_bp = Blueprint("capabilities", __name__, url_prefix="/api/v1/capabilities")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "")


def _authorized() -> bool:
    return bool(_identity_id())


@capability_bp.route("", methods=["GET"])
@capability_bp.route("/", methods=["GET"])
@session_required
def api_status():
    """Detailed per-capability provider status."""
    if not _authorized():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    return jsonify({"success": True, "capabilities": caps.status()})


@capability_bp.route("/summary", methods=["GET"])
@session_required
def api_summary():
    """One row per capability (AVAILABLE / UNAVAILABLE + ready providers)."""
    if not _authorized():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    return jsonify({"success": True, "capabilities": caps.summarize()})


@capability_bp.route("/execute", methods=["POST"])
@session_required
def api_execute():
    """Execute a capability with failover and truthful classification."""
    if not _authorized():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    cap_name = data.get("capability", "").strip()
    try:
        capability = caps.Capability(cap_name)
    except ValueError:
        return jsonify({
            "success": False,
            "error": f"Unknown capability: {cap_name}",
            "error_class": "BAD_REQUEST",
            "known": [c.value for c in caps.Capability],
        }), 400

    # Safety gate for generative prompts (image/text).
    prompt = data.get("prompt") or data.get("text") or data.get("query")
    if prompt:
        try:
            from app.shunya.safety_governance import check_request_safety
            tenant_id = session.get("current_org_id") or 0
            err = check_request_safety(
                prompt,
                identity_id=_identity_id(),
                tenant_id=tenant_id,
            )
        except Exception:
            err = ({"error": "Safety governance unavailable — request blocked"}, 503)
        if err:
            return jsonify(err[0]), err[1]

    paid_ok = bool(data.get("paid_ok", False))
    params = data.get("params") or data
    result = caps.execute(capability, params, paid_ok=paid_ok)

    # Image bytes must not be serialized into JSON — strip and mark.
    if result.get("image_bytes") is not None:
        result["image_generated"] = True
        result["size"] = len(result["image_bytes"])
        result.pop("image_bytes", None)
    return jsonify(result), 200


@capability_bp.route("/diagnostics", methods=["GET"])
@session_required
def api_diagnostics():
    """Deep diagnostics: computed availability for every capability/provider.

    Does NOT perform paid calls. Live probes are limited to free endpoints;
    the text/image availability shown is the truthful computed state plus a
    note of any known outage.
    """
    if not _authorized():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    status_map = caps.status()
    summary = caps.summarize()
    return jsonify({
        "success": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "capabilities": status_map,
        "summary": summary,
    })