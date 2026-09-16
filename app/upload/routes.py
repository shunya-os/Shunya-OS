"""File Upload API — routes for uploading, listing, and serving files with Job Manager integration."""
import os, hashlib, uuid, json, logging
from flask import Blueprint, jsonify, request, session, g
from app.storage.provider import resolve_storage_provider
from app.jobs.manager import create_job, get_job
from app.authz.decorators import require_permission

logger = logging.getLogger(__name__)
upload_bp = Blueprint("upload", __name__, url_prefix="/api/v1/upload")


def _process_upload(job, file_bytes: bytes, filename: str, content_type: str,
                    organization_id: int = 0, workspace_id: str = "",
                    identity_id: str = ""):
    """Background job: save file with storage intelligence: hash, dedup, metadata.

    Args:
        job: Job tracker for progress.
        file_bytes: Raw file content.
        filename: Original filename.
        content_type: MIME type.
        organization_id: Organization context (passed from authenticated request).
                        Must be a positive integer — 0 will fail closed.
        workspace_id: Workspace context. Must be non-empty — empty will fail closed.
    """
    if not organization_id or organization_id < 1:
        raise ValueError("Upload requires a valid organization context")
    if not workspace_id:
        raise ValueError("Upload requires a valid workspace context")
    from app import create_app, db
    from sqlalchemy import text
    import json

    app = create_app()
    with app.app_context():
        job.update(stage="Hashing file")
        sha256 = hashlib.sha256(file_bytes).hexdigest()

        # Dedup check — canonical path: sh_objects. Scoped to the caller's own
        # organization AND workspace (R6B-2.7 Window 6): an unscoped
        # `data LIKE %sha256%` probe matched another tenant's document, which
        # both disclosed that the file existed elsewhere and suppressed the
        # caller's own upload as a "duplicate" of a file they cannot see.
        job.update(stage="Checking for duplicates")
        existing = db.session.execute(
            text("SELECT object_id FROM sh_objects WHERE data LIKE :hash "
                 "AND object_type='Document' AND is_deleted = false "
                 "AND organization_id = :org AND workspace_id = :ws LIMIT 1"),
            {"hash": f"%{sha256}%", "org": organization_id, "ws": workspace_id}
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
            organization_id=organization_id,
            data={"content": content_data, "sha256": sha256, "storage_meta": meta},
            created_by=identity_id or "system",
            workspace_id=workspace_id,
            identity_id=identity_id or None,
        )
        doc_id = created["object_id"]
        db.session.commit()

        # ── Gate 2.2: Canonical ingestion event emission ──
        try:
            from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus
            from app.authz.decorators import _resolve_org_id
            # Canonical tenant only: when the request carries no organization
            # context the event is emitted with no tenant rather than being
            # attributed to a synthetic organization 0.
            resolved_tenant = _resolve_org_id()
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
    workspace_id = session.get("workspace_id") or g.get("workspace_id") or ""
    # Carry the authenticated identity into the background job: the job runs
    # after the request context is gone, so ownership context must be captured
    # here. The job does not rediscover ownership, and does not fall back to a
    # synthetic identity.
    identity_id = session.get("identity_id") or ""
    job = create_job(f"Upload: {f.filename}", "upload")
    job.run_async(_process_upload, file_bytes, f.filename, f.content_type or "application/octet-stream", org_id, workspace_id, identity_id)

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
    """List uploaded files from the canonical object store, caller-scoped.

    R6B-2.7 Window 6: this previously ran an unscoped
    ``SELECT ... FROM sh_objects WHERE object_type='Document'`` — on an
    authenticated, permission-gated route — and therefore returned the 50 most
    recent documents of EVERY tenant, ``data`` included. It now goes through the
    canonical authorization boundary (``ObjectService.get_by_type``), which is
    restricted to the caller's authorized workspaces in the caller's
    organization and fails closed when no such workspace exists.
    """
    identity_id = session.get("identity_id") or ""
    from app.authz.decorators import _resolve_org_id
    org_id = _resolve_org_id()
    if not identity_id or not org_id:
        return jsonify({"success": False,
                        "error": "No authorized workspace for this identity",
                        "code": "no_authorized_workspace"}), 403

    from core.object_service import get_object_service
    from app.authz.workspace_context import OwnershipContextError
    try:
        rows = get_object_service().get_by_type(
            "Document", int(org_id), identity_id=identity_id, limit=50
        )
    except OwnershipContextError as exc:
        return jsonify({"success": False,
                        "error": getattr(exc, "reason", "Forbidden"),
                        "code": getattr(exc, "code", "no_authorized_workspace")}), 403
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

    return jsonify({
        "success": True,
        "data": [
            {
                "id": r.get("object_id"),
                "name": r.get("name"),
                "data": r.get("data"),
                "created_at": str(r.get("created_at")) if r.get("created_at") else None,
            }
            for r in rows
        ],
    })