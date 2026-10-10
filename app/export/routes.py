"""Data Export API — create jobs, poll progress, download results.

Routes:
  POST /api/v1/export                   — create an export job
  GET  /api/v1/export/status/<job_id>   — poll export progress
  GET  /api/v1/export/download/<job_id> — download finished export
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, g, jsonify, request, send_file

from app import db
from app.authz.decorators import require_permission

logger = logging.getLogger(__name__)

export_bp = Blueprint("export", __name__, url_prefix="/api/v1/export")

# ---------------------------------------------------------------------------
# In-memory job store (production would use DB)
# ---------------------------------------------------------------------------

EXPORT_JOBS: dict[str, dict[str, Any]] = {}

SCOPES = ["all", "contacts", "documents", "finance", "commercial", "marketing", "sales", "notifications"]
FORMATS = ["json", "csv", "zip"]

EXPORT_DIR = os.environ.get("EXPORT_DOWNLOAD_DIR", "/tmp/shunya_exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_export_data(identity_id: str, scope: str, fmt: str) -> str:
    """Generate export data and write to a temp file. Returns file path."""
    from app import db

    data: dict[str, Any] = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "identity_id": identity_id,
        "scope": scope,
        "format": fmt,
    }

    if scope in ("all", "contacts"):
        try:
            from app.models import OrgMember, Organization
            orgs = Organization.query.all()
            data["organizations"] = [o.to_dict() if hasattr(o, "to_dict") else {"id": o.id, "name": getattr(o, "name", "")} for o in orgs]
            members = OrgMember.query.filter_by(identity_id=identity_id).all()
            data["memberships"] = [m.to_dict() if hasattr(m, "to_dict") else {"id": m.id} for m in members]
        except Exception as exc:
            data["contacts_error"] = str(exc)

    if scope in ("all", "documents"):
        try:
            from app.document.models import DocumentRecord
            docs = DocumentRecord.query.filter_by(identity_id=identity_id).all()
            data["documents"] = [d.to_dict() if hasattr(d, "to_dict") else {"id": d.id, "title": getattr(d, "title", "")} for d in docs]
        except Exception as exc:
            data["documents_error"] = str(exc)

    if scope in ("all", "finance"):
        try:
            from app.finance.models import Account, LedgerEntry
            accounts = Account.query.all()
            data["accounts"] = [a.to_dict() if hasattr(a, "to_dict") else {"id": a.id, "name": getattr(a, "name", "")} for a in accounts]
            entries = LedgerEntry.query.limit(500).all()
            data["ledger_entries"] = [e.to_dict() if hasattr(e, "to_dict") else {"id": e.id} for e in entries]
        except Exception as exc:
            data["finance_error"] = str(exc)

    if scope in ("all", "commercial"):
        try:
            from app.commercial.models import CommercialRelation
            rels = CommercialRelation.query.limit(500).all()
            data["commercial_relations"] = [r.to_dict() if hasattr(r, "to_dict") else {"id": r.id} for r in rels]
        except Exception as exc:
            data["commercial_error"] = str(exc)

    if scope in ("all", "marketing"):
        try:
            from app.integration.models import ScheduledPost
            posts = ScheduledPost.query.filter_by(identity_id=identity_id).all()
            data["scheduled_posts"] = [p.to_dict() if hasattr(p, "to_dict") else {"id": p.id} for p in posts]
        except Exception as exc:
            data["marketing_error"] = str(exc)

    if scope in ("all", "sales"):
        try:
            from app.customers.models import Customer
            customers = Customer.query.limit(500).all()
            data["customers"] = [c.to_dict() if hasattr(c, "to_dict") else {"id": c.id} for c in customers]
        except Exception as exc:
            data["sales_error"] = str(exc)

    if scope in ("all", "notifications"):
        try:
            from app.integration.models import Notification
            notifs = Notification.query.filter_by(identity_id=identity_id).limit(500).all()
            data["notifications"] = [n.to_dict() if hasattr(n, "to_dict") else {"id": n.id} for n in notifs]
        except Exception as exc:
            data["notifications_error"] = str(exc)

    file_id = uuid.uuid4().hex[:12]
    ext = "csv" if fmt == "csv" else "json"
    file_path = os.path.join(EXPORT_DIR, f"export_{file_id}.{ext}")

    if fmt == "csv":
        import csv
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["section", "key", "value"])
            for section, content in data.items():
                if isinstance(content, list):
                    for item in content:
                        writer.writerow([section, json.dumps(item), ""])
                else:
                    writer.writerow([section, "", str(content)])
    else:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    return file_path


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@export_bp.route("", methods=["POST"])
@require_permission("rel.view")
def create_export():
    """Create a new data export job.

    Expects JSON body:
      { "scope": "all", "format": "json" }

    scope: all | contacts | documents | finance | commercial | marketing | sales | notifications
    format: json | csv | zip
    """
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    scope = data.get("scope", "all")
    fmt = data.get("format", "json")

    if scope not in SCOPES:
        return jsonify({"error": f"Invalid scope. Must be one of: {', '.join(SCOPES)}"}), 400
    if fmt not in FORMATS:
        return jsonify({"error": f"Invalid format. Must be one of: {', '.join(FORMATS)}"}), 400

    job_id = uuid.uuid4().hex[:16]
    EXPORT_JOBS[job_id] = {
        "id": job_id,
        "identity_id": identity_id,
        "scope": scope,
        "format": fmt,
        "status": "processing",
        "progress": 0,
        "file_path": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }

    def _run_export(jid: str, id_: str, sc: str, fm: str):
        try:
            with db.session.no_autoflush:
                path = _generate_export_data(id_, sc, fm)
            EXPORT_JOBS[jid].update({
                "status": "completed",
                "progress": 100,
                "file_path": path,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info("Export %s completed: %s", jid, path)
        except Exception as exc:
            logger.error("Export %s failed: %s", jid, exc)
            EXPORT_JOBS[jid].update({
                "status": "failed",
                "error": str(exc),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })

    t = threading.Thread(
        target=_run_export,
        args=(job_id, identity_id, scope, fmt),
        daemon=True,
    )
    t.start()

    return jsonify({
        "success": True,
        "job": {
            "id": job_id,
            "status": "processing",
            "scope": scope,
            "format": fmt,
        },
    }), 202


@export_bp.route("/status/<job_id>", methods=["GET"])
@require_permission("rel.view")
def get_export_status(job_id: str):
    """Poll the progress of an export job."""
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")

    job = EXPORT_JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Export job not found"}), 404
    if job["identity_id"] != identity_id:
        return jsonify({"error": "Not authorized to view this job"}), 403

    return jsonify({
        "success": True,
        "job": {
            "id": job["id"],
            "status": job["status"],
            "progress": job["progress"],
            "scope": job["scope"],
            "format": job["format"],
            "error": job.get("error"),
            "created_at": job.get("created_at"),
            "completed_at": job.get("completed_at"),
        },
    })


@export_bp.route("/download/<job_id>", methods=["GET"])
@require_permission("rel.view")
def download_export(job_id: str):
    """Download a completed export file."""
    identity_id = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id")

    job = EXPORT_JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Export job not found"}), 404
    if job["identity_id"] != identity_id:
        return jsonify({"error": "Not authorized to download this job"}), 403
    if job["status"] != "completed":
        return jsonify({"error": f"Export is {job['status']}, not yet completed"}), 400
    if not job.get("file_path") or not os.path.isfile(job["file_path"]):
        return jsonify({"error": "Export file not found on disk"}), 404

    ext = job.get("format", "json")
    mime = "application/json" if ext == "json" else "text/csv" if ext == "csv" else "application/zip"
    fname = f"shunya_export_{job_id[:8]}.{ext}"

    return send_file(
        job["file_path"],
        mimetype=mime,
        as_attachment=True,
        download_name=fname,
    )