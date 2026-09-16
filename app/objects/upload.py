"""
SHUNYA OS — Phase 0 Foundation File Upload.

POST /api/v1/upload — upload files, creates a 'document' ShunyaObject.
Files stored in /home/shunya-deploy/shunya_os/uploads/{workspace_id}/{object_id}/
"""
import os
import uuid
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request, g

logger = logging.getLogger(__name__)

upload_bp = Blueprint("objects_upload", __name__, url_prefix="/api/v1/upload")

UPLOAD_BASE = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
UPLOAD_BASE = os.path.abspath(UPLOAD_BASE)

ALLOWED_EXTENSIONS = {
    '.pdf': 'application/pdf',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.txt': 'text/plain',
    '.csv': 'text/csv',
}


def _require_identity() -> str | None:
    # Check g.identity_id first (set by cookie middleware)
    identity_id = getattr(g, 'identity_id', None)
    if identity_id:
        return identity_id
    # Fall back to header (backward compat)
    identity_id = request.headers.get("X-Identity-Id")
    if not identity_id:
        return None
    return identity_id


def _error(msg: str, code: int = 400):
    return jsonify({"success": False, "error": msg}), code


def _ok(data, code: int = 200):
    return jsonify({"success": True, "data": data}), code


@upload_bp.route("", methods=["POST"])
def api_upload():
    """Upload a file. Creates a 'document' ShunyaObject for each file."""
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)

    ws_id = request.headers.get("X-Workspace-Id")
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)

    if "file" not in request.files:
        return _error("No file provided", 400)

    files = request.files.getlist("file") if len(request.files) > 1 else [request.files["file"]]
    results = []

    for f in files:
        if not f.filename:
            continue

        # Validate extension
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return _error(f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS.keys())}", 400)

        file_bytes = f.read()
        if not file_bytes:
            continue

        # Generate unique object id
        obj_uuid = uuid.uuid4().hex[:24]
        obj_id = f"doc_{obj_uuid}"

        # Create storage directory
        storage_dir = os.path.join(UPLOAD_BASE, ws_id, obj_id)
        os.makedirs(storage_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(storage_dir, f.filename)
        with open(file_path, "wb") as out:
            out.write(file_bytes)

        file_size = len(file_bytes)
        content_type = ALLOWED_EXTENSIONS.get(ext, "application/octet-stream")
        relative_path = f"uploads/{ws_id}/{obj_id}/{f.filename}"

        # Create the canonical object through ObjectService (R6B-2.7 Window 6).
        # This route previously constructed a ShunyaObject directly, with no
        # organization_id at all, i.e. it wrote `sh_objects` rows outside the
        # canonical write path with NULL ownership — bypassing every Batch C/D
        # gate. The workspace's owning organization is now resolved explicitly,
        # ObjectService re-validates that the workspace belongs to it, and the
        # caller's identity must be actively authorized for that pair.
        from app.objects.legacy_models import Workspace
        from core.object_service import get_object_service
        from app.authz.workspace_context import OwnershipContextError

        workspace = Workspace.query.filter_by(id=ws_id, status="active").first()
        if workspace is None or not workspace.organization_id:
            return _error("Unknown or unowned workspace", 400)

        try:
            get_object_service().create(
                object_type="document",
                name=f.filename,
                organization_id=int(workspace.organization_id),
                workspace_id=ws_id,
                data={
                    "title": f.filename,
                    "file_path": relative_path,
                    "file_type": ext,
                    "file_size": file_size,
                    "content_type": content_type,
                    "description": "",
                    "tags": [],
                    "name": f.filename,
                },
                created_by=identity_id,
                object_id=obj_id,
                identity_id=identity_id,
            )
        except OwnershipContextError as exc:
            return _error(getattr(exc, "reason", "Forbidden"), 403)
        except ValueError as exc:
            return _error(str(exc), 400)

        meta = {
            "object_id": obj_id,
            "filename": f.filename,
            "file_path": relative_path,
            "file_size": file_size,
            "file_type": ext,
            "content_type": content_type,
        }
        results.append(meta)
        logger.info("File uploaded: %s (%d bytes) to workspace=%s", f.filename, file_size, ws_id)

    return _ok({"files": results}, 201)