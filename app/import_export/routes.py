"""FDA25 — Universal Import / Export / Migration Routes."""

from flask import Blueprint, g, jsonify, request, session

from app.authz.decorators import _resolve_org_id

import_bp = Blueprint("import_export", __name__, url_prefix="/api/v1/data")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "anonymous")


def _tenant_id() -> int | None:
    return _resolve_org_id()


def _require_auth() -> bool:
    return bool(_identity_id() and _tenant_id())


@import_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", "service": "import-export", "version": "1.0.0",
        "endpoints": [
            "POST /api/v1/data/import/preview",
            "POST /api/v1/data/import/commit",
            "POST /api/v1/data/export",
        ],
    })


@import_bp.route("/import/preview", methods=["POST"])
def preview():
    """Preview an import before committing. No data written."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"success": False, "error": "content is required"}), 400

    try:
        from app.import_export.service import preview_import
        result = preview_import(
            content=content,
            content_type=data.get("content_type", "csv"),
            target_type=data.get("target_type", "lead"),
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@import_bp.route("/import/commit", methods=["POST"])
def commit():
    """Commit an import after preview. Creates records with evidence."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return jsonify({"success": False, "error": "content is required"}), 400

    try:
        from app.import_export.service import commit_import
        result = commit_import(
            organization_id=_tenant_id(),
            content=content,
            content_type=body.get("content_type", "csv"),
            target_type=body.get("target_type", "lead"),
            identity_id=_identity_id(),
        )
        status = 201 if result["status"] == "completed" else (200 if result["status"] == "partial" else 500)
        return jsonify({"success": True if result["status"] != "failed" else False, "data": result}), status
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@import_bp.route("/export", methods=["POST"])
def export_data():
    """Export records with provenance. Respects tenant isolation."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    body = request.get_json(silent=True) or {}
    target_type = body.get("target_type", "lead")
    fmt = body.get("format", "json")
    limit = min(int(body.get("limit", 1000)), 10000)

    try:
        from app.authz.services import check_permission
        from app.import_export.service import export_records

        # Check export permission
        if not check_permission(_tenant_id(), _identity_id(), "org.export_data"):
            return jsonify({"success": False, "error": "Insufficient permissions"}), 403

        result = export_records(
            organization_id=_tenant_id(),
            target_type=target_type,
            identity_id=_identity_id(),
            format=fmt,
            limit=limit,
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500