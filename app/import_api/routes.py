"""
SHUNYA — Import API route (FDA5-G7 closure).

Real production path for importing contacts via CSV/JSON through the
canonical import/export fabric.
"""
import logging

from flask import Blueprint, request, jsonify

from core.api_contract import (
    success_response,
    error_response,
    require_auth,
    require_tenant,
)
from core.import_export import CSVContactImporter, JSONDataImporter

logger = logging.getLogger(__name__)

import_bp = Blueprint("import_api", __name__, url_prefix="/api/v1/import")


@import_bp.route("/contacts/csv", methods=["POST"])
@require_auth
@require_tenant
def import_contacts_csv():
    """Import contacts from CSV via the canonical CSVContactImporter."""
    from app.identity.service import IdentityService

    if "file" not in request.files:
        return error_response(message="CSV file required", status=400, error_code="VALIDATION_ERROR")

    file = request.files["file"]
    if not file.filename or not file.filename.endswith(".csv"):
        return error_response(message="File must be CSV", status=400, error_code="VALIDATION_ERROR")

    try:
        content = file.read().decode("utf-8")
    except Exception as e:
        return error_response(message=f"Failed to read file: {e}", status=400, error_code="VALIDATION_ERROR")

    svc = IdentityService()
    importer = CSVContactImporter(identity_service=svc)
    result = importer.import_data(content, tenant_id=getattr(request, "tenant_id", "1"))

    return success_response(
        data={
            "total": result.total,
            "imported": result.imported,
            "skipped": result.skipped,
            "errors": result.errors[:10],  # Limit error detail
        },
        message="Import completed",
        status=200 if result.status.value in ("completed", "partial") else 422,
    )


@import_bp.route("/contacts/json", methods=["POST"])
@require_auth
@require_tenant
def import_contacts_json():
    """Import contacts from JSON via the canonical JSONDataImporter."""
    from app.identity.service import IdentityService

    data = request.get_json(silent=True)
    if not data:
        return error_response(message="JSON body required", status=400, error_code="VALIDATION_ERROR")

    svc = IdentityService()
    importer = JSONDataImporter(identity_service=svc)
    result = importer.import_data(data, tenant_id=getattr(request, "tenant_id", "1"))

    return success_response(
        data={
            "total": result.total,
            "imported": result.imported,
            "skipped": result.skipped,
            "errors": result.errors[:10],
        },
        message="Import completed",
        status=200 if result.status.value in ("completed", "partial") else 422,
    )