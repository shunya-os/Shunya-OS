"""FDA25 — Universal Import / Export / Migration Routes.  [M6 semantic ingestion]

Endpoints:
  POST /api/v1/data/import/preview        — inspect + understand + map + validate
  POST /api/v1/data/import/commit         — confirm + canonical write + provenance
  POST /api/v1/data/import/correct        — auditable correction of imported records
  GET  /api/v1/data/provenance/<t>/<id>   — where did SHUNYA get this information?
  POST /api/v1/data/export                — export with provenance
"""

from flask import Blueprint, g, jsonify, request, session
from app.authz.decorators import require_permission

from app.authz.decorators import _resolve_org_id

import_bp = Blueprint("import_export", __name__, url_prefix="/api/v1/data")

_ALLOWED_TARGETS = ("lead", "customer", "supplier", "campaign")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "anonymous")


def _tenant_id() -> int | None:
    return _resolve_org_id()


def _require_auth() -> bool:
    return bool(_identity_id() and _tenant_id())


def _valid_target(t: str) -> bool:
    return t in _ALLOWED_TARGETS


@import_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", "service": "import-export", "version": "1.1.0",
        "endpoints": [
            "POST /api/v1/data/import/preview",
            "POST /api/v1/data/import/commit",
            "POST /api/v1/data/import/correct",
            "GET /api/v1/data/provenance/<target_type>/<record_id>",
            "POST /api/v1/data/export",
        ],
    })


@import_bp.route("/import/preview", methods=["POST"])
@require_permission("org.export_data")
def preview():
    """Preview an import before committing. No data written.

    Returns SHUNYA's full interpretation: per-column mapping explanation,
    surfaced ambiguities, identity match bases, and similar-entity candidates.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"success": False, "error": "content is required"}), 400

    target_type = data.get("target_type", "lead")
    if not _valid_target(target_type):
        return jsonify({"success": False, "error": f"unsupported target_type '{target_type}'"}), 400

    column_overrides = data.get("column_overrides") or None
    if column_overrides is not None and not isinstance(column_overrides, dict):
        return jsonify({"success": False, "error": "column_overrides must be an object"}), 400

    try:
        from app.import_export.service import preview_import
        result = preview_import(
            content=content,
            content_type=data.get("content_type", "csv"),
            target_type=target_type,
            column_overrides=column_overrides,
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@import_bp.route("/import/commit", methods=["POST"])
@require_permission("org.export_data")
def commit():
    """Commit an import after preview. Creates records with provenance.

    Accepts optional ``source_name`` (file name), ``session_token`` (stable id
    for a logical import), and ``column_overrides`` (human mapping decisions
    that must match what was previewed/confirmed).
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return jsonify({"success": False, "error": "content is required"}), 400

    target_type = body.get("target_type", "lead")
    if not _valid_target(target_type):
        return jsonify({"success": False, "error": f"unsupported target_type '{target_type}'"}), 400

    column_overrides = body.get("column_overrides") or None
    if column_overrides is not None and not isinstance(column_overrides, dict):
        return jsonify({"success": False, "error": "column_overrides must be an object"}), 400

    try:
        from app.import_export.service import commit_import
        result = commit_import(
            organization_id=_tenant_id(),
            content=content,
            content_type=body.get("content_type", "csv"),
            target_type=target_type,
            identity_id=_identity_id(),
            source_name=body.get("source_name", ""),
            session_token=body.get("session_token", ""),
            column_overrides=column_overrides,
        )
        #   completed -> 201 (records written)
        #   partial   -> 200 (some written, some rejected)
        #   noop      -> 200 (nothing to do: every row already exists)
        #   rejected  -> 400 (nothing written: the data was invalid)
        #   failed    -> 500 (server-side failure)
        status_by_outcome = {
            "completed": 201,
            "partial": 200,
            "noop": 200,
            "rejected": 400,
            "failed": 500,
        }
        outcome = str(result.get("status") or "")
        status = status_by_outcome[outcome] if outcome in status_by_outcome else 500
        return jsonify({
            "success": outcome in ("completed", "partial", "noop"),
            "data": result,
        }), status
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@import_bp.route("/import/correct", methods=["POST"])
@require_permission("org.export_data")
def correct():
    """Correct a field on an imported record.

    Updates canonical state and appends auditable correction evidence —
    nothing is silently overwritten. The record must belong to the caller's
    organization (fail closed otherwise).
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    body = request.get_json(silent=True) or {}
    target_type = body.get("target_type", "")
    if not _valid_target(target_type):
        return jsonify({"success": False, "error": f"unsupported target_type '{target_type}'"}), 400

    record_id = body.get("record_id")
    try:
        record_id = int(record_id)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "record_id must be an integer"}), 400

    field = str(body.get("field") or "").strip()
    if not field:
        return jsonify({"success": False, "error": "field is required"}), 400
    if "new_value" not in body:
        return jsonify({"success": False, "error": "new_value is required"}), 400

    try:
        from app.import_export.service import correct_record
        result = correct_record(
            target_type=target_type,
            record_id=record_id,
            field=field,
            new_value=body.get("new_value", ""),
            organization_id=_tenant_id(),
            identity_id=_identity_id(),
            reason=str(body.get("reason") or ""),
        )
        if not result.get("ok"):
            code = 404 if result.get("error") == "record not found" else 400
            return jsonify({"success": False, "error": result.get("error", "correction failed")}), code
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@import_bp.route("/provenance/<target_type>/<int:record_id>", methods=["GET"])
@require_permission("org.export_data")
def provenance(target_type: str, record_id: int):
    """Where did SHUNYA get this information, and why does it believe it?

    Returns the record's provenance trail: origin (source file, row, session,
    mapping decision, author, timestamp), transformations, and corrections.
    Scoped to the caller's organization; cross-tenant reads return 404.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    if not _valid_target(target_type):
        return jsonify({"success": False, "error": f"unsupported target_type '{target_type}'"}), 400

    try:
        from app.import_export.service import get_record_provenance
        result = get_record_provenance(target_type, record_id, _tenant_id())
        if result is None:
            return jsonify({"success": False, "error": "record not found"}), 404
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@import_bp.route("/export", methods=["POST"])
@require_permission("org.export_data")
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
