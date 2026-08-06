"""SHUNYA OS — File Manager API.

GET    /api/v1/files          — list files in workspace
DELETE /api/v1/files/<id>     — soft-delete a file
PATCH  /api/v1/files/<id>/rename — rename a file
"""
from flask import Blueprint, jsonify, request

from app import db
from app.objects.models import ShunyaObject

file_bp = Blueprint("files", __name__, url_prefix="/api/v1/files")


def _ok(data, code: int = 200):
    return jsonify({"success": True, "data": data}), code


def _error(msg: str, code: int = 400):
    return jsonify({"success": False, "error": msg}), code


@file_bp.route("", methods=["GET"])
def list_files():
    """List all uploaded files for the current workspace."""
    ws_id = request.headers.get("X-Workspace-Id")
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)

    files = (
        ShunyaObject.query.filter_by(
            workspace_id=ws_id,
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
def delete_file(file_id: int):
    """Soft-delete a file by its integer primary key."""
    file = ShunyaObject.query.get(file_id)
    if not file:
        return _error("File not found", 404)

    file.is_deleted = True
    db.session.commit()
    return _ok({"message": "File deleted"})


@file_bp.route("/<int:file_id>/rename", methods=["PATCH"])
def rename_file(file_id: int):
    """Rename a file."""
    body = request.get_json() or {}
    new_name = body.get("name", "").strip()
    if not new_name:
        return _error("Name required", 400)

    file = ShunyaObject.query.get(file_id)
    if not file:
        return _error("File not found", 404)

    file_data = file.data or {}
    file_data["name"] = new_name
    file.data = file_data
    file.name = new_name
    db.session.commit()
    return _ok({"message": f"Renamed to {new_name}"})