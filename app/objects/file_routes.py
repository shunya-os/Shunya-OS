"""SHUNYA OS — File Manager API.

GET    /api/v1/files              — list files in the caller's authorized workspace
DELETE /api/v1/files/<id>         — soft-delete a file
PATCH  /api/v1/files/<id>/rename  — rename a file

Authorization boundary (R6B-2.7 Window 6)
-----------------------------------------
Every route here is tenant-scoped through the canonical resolver in
``app/authz/workspace_context.py``:

* the organization comes from the authenticated session (``g.current_org_id``,
  set by ``require_permission``), never from a caller-supplied header;
* the workspace must belong to that organization AND the identity must hold an
  active membership in it (``resolve_current_workspace`` /
  ``assert_object_access``);
* per-object operations (delete/rename) are authorized against the row's
  PERSISTED ``organization_id`` + ``workspace_id``, so an integer primary key
  from another tenant can never be reached.

Denials return 404 (not 403) for object-specific operations so that object
existence is not disclosed, matching ``ObjectService.get`` semantics.
"""
from flask import Blueprint, g, jsonify, request

from app import db
from app.objects.legacy_models import ShunyaObject
from app.authz.decorators import require_permission
from app.authz.workspace_context import (
    OwnershipContextError,
    assert_object_access,
    resolve_current_workspace,
)

file_bp = Blueprint("files", __name__, url_prefix="/api/v1/files")


def _ok(data, code: int = 200):
    return jsonify({"success": True, "data": data}), code


def _error(msg: str, code: int = 400):
    return jsonify({"success": False, "error": msg}), code


def _denied(msg: str = "Forbidden"):
    return jsonify({"success": False, "error": msg}), 403


def _caller() -> tuple[str | None, int | None]:
    """The authenticated identity and its resolved organization, fail closed."""
    return getattr(g, "identity_id", None), getattr(g, "current_org_id", None)


def _identity_authorized_for(row) -> bool:
    """True only when the caller is canonically authorized for this row.

    Authorizes against the row's PERSISTED ownership — never against a
    caller-supplied organization or workspace.
    """
    identity, _ = _caller()
    if not identity or row is None:
        return False
    if not row.organization_id:
        return False
    try:
        assert_object_access(identity, row.organization_id, row.workspace_id)
    except OwnershipContextError:
        return False
    return True


@file_bp.route("", methods=["GET"])
@require_permission("knowledge.view")
def list_files():
    """List the uploaded files of one AUTHORIZED workspace."""
    ws_id = request.headers.get("X-Workspace-Id")
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)

    identity, org_id = _caller()
    if not identity or not org_id:
        return _denied("Authorization context missing")

    # The requested workspace must belong to the caller's organization AND the
    # caller must be actively authorized for it. No synthetic fallback.
    try:
        resolve_current_workspace(identity, int(org_id), ws_id)
    except OwnershipContextError as exc:
        return _denied(getattr(exc, "reason", "Forbidden"))

    files = (
        ShunyaObject.query.filter_by(
            workspace_id=ws_id,
            organization_id=int(org_id),
            object_type="document",
            is_deleted=False,
        )
        .order_by(ShunyaObject.created_at.desc())
        .limit(100)
        .all()
    )

    results = []
    for f in files:
        data = f.data or {}
        results.append(
            {
                "id": f.id,
                "object_id": f.object_id,
                "name": data.get("name", f.name),
                "file_type": data.get("file_type", "unknown"),
                "file_size": data.get("file_size", 0),
                "file_path": data.get("file_path", ""),
                "created_at": f.created_at.isoformat() if f.created_at else "",
            }
        )

    return _ok({"files": results, "total": len(results)})


@file_bp.route("/<int:file_id>", methods=["DELETE"])
@require_permission("knowledge.delete")
def delete_file(file_id: int):
    """Soft-delete a file by its integer primary key, inside the caller's tenant."""
    file = ShunyaObject.query.get(file_id)
    if not file or not _identity_authorized_for(file):
        # Same response for "absent" and "not yours": existence is not disclosed.
        return _error("File not found", 404)

    file.is_deleted = True
    db.session.commit()
    return _ok({"message": "File deleted"})


@file_bp.route("/<int:file_id>/rename", methods=["PATCH"])
@require_permission("knowledge.edit")
def rename_file(file_id: int):
    """Rename a file, inside the caller's tenant."""
    body = request.get_json() or {}
    new_name = body.get("name", "").strip()
    if not new_name:
        return _error("Name required", 400)

    file = ShunyaObject.query.get(file_id)
    if not file or not _identity_authorized_for(file):
        return _error("File not found", 404)

    file_data = file.data or {}
    file_data["name"] = new_name
    file.data = file_data
    file.name = new_name
    db.session.commit()
    return _ok({"message": f"Renamed to {new_name}"})
