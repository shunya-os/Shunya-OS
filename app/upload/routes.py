"""File Upload API — routes for uploading, listing, and serving files with Job Manager integration."""
import os, hashlib, uuid, json, logging
from flask import Blueprint, jsonify, request, session
from app.storage.provider import resolve_storage_provider
from app.jobs.manager import create_job, get_job
from app.authz.decorators import require_permission

logger = logging.getLogger(__name__)
upload_bp = Blueprint("upload", __name__, url_prefix="/api/v1/upload")


def _process_upload(job, file_bytes: bytes, filename: str, content_type: str,
                    organization_id: int = 0):
    """Background job: save file with storage intelligence: hash, dedup, metadata.

    Args:
        job: Job tracker for progress.
        file_bytes: Raw file content.
        filename: Original filename.
        content_type: MIME type.
        organization_id: Organization context (passed from authenticated request).
    """
    from app import create_app, db
    from sqlalchemy import text
    import json

    app = create_app()
    with app.app_context():
        job.update(stage="Hashing file")
        sha256 = hashlib.sha256(file_bytes).hexdigest()

        # Dedup check - canonical path: sh_objects
        job.update(stage="Checking for duplicates")
        existing = db.session.execute(
            text("SELECT object_id FROM sh_objects WHERE data LIKE :hash AND object_type='Document' AND is_deleted = false LIMIT 1"),
            {"hash": f"%{sha256}%"}
        ).fetchone()

        if existing:
            job.update(stage="Duplicate detected", step=50,
                       result={"duplicate": True, "existing_id": existing[0], "sha256": sha256})
            logger.info(f"Duplicate upload skipped: {sha256[:12]} for {filename}")
            return

        # Save with compression
        job.update(stage="Compressing and storing")
        storage = resolve_storage_provider()
        meta = storage.save(file_bytes, filename, content_type)
        meta["sha256"] = sha256

        # Create canonical object via ObjectService (single production write path)
        job.update(stage="Indexing in workspace", step=70)
        from core.object_service import get_object_service
        svc = get_object_service()
        content_data = json.dumps({
            "filename": filename,
            "url": meta["url"],
            "size": meta["size"],
            "original_size": meta.get("compression", {}).get("original_size", meta["size"]),
            "sha256": sha256,
            "compression": meta.get("compression", {}).get("compression", "none"),
            "content_type": content_type,
        })
        created = svc.create(
            object_type="Document",
            name=filename,
            organization_id=organization_id or 0,
            data={"content": content_data, "sha256": sha256, "storage_meta": meta},
            created_by="system",
            workspace_id="onb_system",
        )
        doc_id = created["object_id"]
        db.session.commit()

        # ── Gate 2.2: Canonical ingestion event emission ──
        try:
            from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus
            from app.authz.decorators import _resolve_org_id
            resolved_tenant = _resolve_org_id() or 0
            event = CanonicalEvent(
                event_type="ingestion:file_upload",
                tenant_id=resolved_tenant,
                workspace_id=None,
                actor_id="system",
                actor_type="upload",
                actor_name="file_upload",
                object_id=doc_id,
                object_type="Document",
                payload={
                    "filename": filename,
                    "content_type": content_type,
                    "sha256": sha256,
                    "source": "file_upload",
                },
                confidence=1.0,
            )
            get_event_bus().publish(event)
            logger.info(f"Canonical ingestion event emitted for upload: {filename}")
        except Exception as e:
            logger.warning(f"Ingestion event emission failed (non-blocking): {e}")

        job.update(stage="Complete", step=100, result=meta)


@upload_bp.route("", methods=["POST"])
@require_permission("knowledge.upload")
def api_upload():
    """Upload a file. Returns immediately with a job ID for tracking."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"success": False, "error": "Empty filename"}), 400

    file_bytes = f.read()

    # Capture organization context before it's lost in the background job
    from app.authz.decorators import _resolve_org_id
    org_id = _resolve_org_id()
    job = create_job(f"Upload: {f.filename}", "upload")
    job.run_async(_process_upload, file_bytes, f.filename, f.content_type or "application/octet-stream", org_id)

    return jsonify({
        "success": True,
        "job_id": job.id,
        "data": {
            "filename": f.filename,
            "size": len(file_bytes),
            "status": "processing",
        }
    })


@upload_bp.route("/<job_id>/status", methods=["GET"])
@require_permission("knowledge.view")
def api_upload_status(job_id: str):
    """Poll upload job status."""
    job = get_job(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404
    return jsonify({"success": True, "data": job.to_dict()})


@upload_bp.route("", methods=["GET"])
@require_permission("knowledge.view")
def api_list_uploads():
    """List uploaded files from canonical object store (sh_objects)."""
    try:
        from app import db
        from sqlalchemy import text
        identity_id = session.get("identity_id")
        files = db.session.execute(
            text("SELECT object_id, name, data, created_at FROM sh_objects WHERE object_type='Document' AND is_deleted = false ORDER BY created_at DESC LIMIT 50")
        ).fetchall()
        return jsonify({
            "success": True,
            "data": [
                {"id": r[0], "name": r[1], "data": r[2], "created_at": str(r[3]) if r[3] else None}
                for r in files
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500