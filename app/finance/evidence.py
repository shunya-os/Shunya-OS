"""FOR-2D.4: Financial Evidence Engine — Models and Services."""

import os, json, uuid, re, logging
from datetime import datetime, timezone
from io import BytesIO
from app import db
from sqlalchemy import Index

logger = logging.getLogger(__name__)

EVIDENCE_STATUS = ["uploaded", "ai_processing", "ai_processed", "matched",
                   "verified", "accepted", "rejected", "archived"]
EVIDENCE_TYPES = ["image", "pdf", "document", "spreadsheet", "voice", "video", "text", "other"]


class EvidencePolicy(db.Model):
    __tablename__ = "fin_evidence_policies"
    __table_args__ = (Index("ix_fin_ep_org", "organization_id"),)
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    doc_type = db.Column(db.String(60), nullable=False)
    requirement = db.Column(db.String(30), default="optional")
    condition = db.Column(db.Text, default="")
    min_count = db.Column(db.Integer, default=0)
    allowed_types = db.Column(db.Text, default="[]")
    require_ocr = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "doc_type": self.doc_type, "requirement": self.requirement,
            "condition": (self.condition or "")[:200], "min_count": self.min_count,
            "allowed_types": json.loads(self.allowed_types or "[]"),
            "require_ocr": self.require_ocr}


class FinancialEvidence(db.Model):
    __tablename__ = "fin_evidence"
    __table_args__ = (Index("ix_fin_ev_org", "organization_id"),
        Index("ix_fin_ev_ref", "reference_type", "reference_id"),
        Index("ix_fin_ev_status", "status"))
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    reference_type = db.Column(db.String(60), nullable=False)
    reference_id = db.Column(db.Integer, nullable=False)
    evidence_type = db.Column(db.String(30), default="image")
    file_path = db.Column(db.String(500), default="")
    original_filename = db.Column(db.String(500), default="")
    mime_type = db.Column(db.String(100), default="")
    file_size_bytes = db.Column(db.BigInteger, default=0)
    status = db.Column(db.String(30), default="uploaded")
    notes = db.Column(db.Text, default="")
    extracted_data = db.Column(db.Text, default="{}")
    matched_reference = db.Column(db.String(60), default="")
    matched_id = db.Column(db.Integer, nullable=True)
    verified_by = db.Column(db.String(64), default="")
    verified_at = db.Column(db.DateTime, nullable=True)
    rejected_reason = db.Column(db.Text, default="")
    created_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        d = {"id": self.id, "reference_type": self.reference_type, "reference_id": self.reference_id,
            "evidence_type": self.evidence_type, "original_filename": self.original_filename,
            "mime_type": self.mime_type, "file_size_bytes": self.file_size_bytes,
            "status": self.status, "notes": (self.notes or "")[:200],
            "extracted_data": json.loads(self.extracted_data or "{}"),
            "matched_reference": self.matched_reference, "matched_id": self.matched_id,
            "verified_by": self.verified_by, "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None}
        if self.verified_at: d["verified_at"] = self.verified_at.isoformat()
        if self.rejected_reason: d["rejected_reason"] = (self.rejected_reason or "")[:200]
        return d


STORAGE_ROOT = os.path.expanduser("~/shunya_data/evidence")

# --- Allowed file types with signatures and extensions ---
# Maps canonical MIME type -> (server-safe extension, validation function)
ALLOWED_FILE_TYPES = {
    "image/jpeg": (".jpg", lambda data: data[:3] in (b"\xff\xd8\xff",)),
    "image/png": (".png", lambda data: data[:8] == b"\x89PNG\r\n\x1a\n"),
    "image/webp": (".webp", lambda data: data[:4] == b"RIFF" and data[8:12] == b"WEBP"),
    "image/gif": (".gif", lambda data: data[:6] in (b"GIF87a", b"GIF89a")),
    "application/pdf": (".pdf", lambda data: data[:5] == b"%PDF-"),
}

# Per-file size limit (bytes). App-level MAX_CONTENT_LENGTH (16 MB) catches
# oversized request bodies; this catches individual files within multipart.
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB


def _validate_file_content(file_obj):
    """Validate uploaded file content and return (safe_mime, safe_ext, error).

    Returns (None, None, error_msg) on failure.
    Does NOT trust Content-Type header or client filename.
    Only the first ~512 bytes are read for signature detection.
    """
    # Read the first 4 KB for signature detection
    header = file_obj.read(4096)
    file_obj.seek(0)

    if not header or len(header) < 4:
        return None, None, "Empty or truncated file"

    # Detect type by magic bytes
    for mime, (ext, validator) in ALLOWED_FILE_TYPES.items():
        try:
            if validator(header):
                # For PDF: additional well-formedness check
                if mime == "application/pdf":
                    # Ensure the header has enough structure
                    header_str = header.decode("latin-1", errors="replace")
                    if "%" not in header_str[:20]:
                        continue
                # For images: attempt to verify with PIL where possible
                if mime.startswith("image/") and mime != "application/pdf":
                    try:
                        from PIL import Image
                        img = Image.open(BytesIO(header + file_obj.read(65536)))
                        img.verify()
                        file_obj.seek(0)
                    except Exception as exc:
                        file_obj.seek(0)
                        logger.warning("PIL verification failed for %s: %s", mime, exc)
                        return None, None, "Corrupt or invalid image file"
                return mime, ext, None
        except Exception:
            continue

    return None, None, (
        "Unsupported file type. Only JPEG, PNG, WebP, GIF images and PDF "
        "documents are accepted."
    )


def _sanitize_filename(filename):
    """Strip path separators and dangerous characters from a filename.

    Returns a safe display name (extension preserved) or 'file.bin'.
    Removes: / \\ .. NULL bytes and trims to 200 chars.
    """
    if not filename:
        return "file.bin"
    # Remove null bytes
    filename = filename.replace("\x00", "")
    # Strip path separators (Windows and Unix)
    filename = os.path.basename(filename)
    # Remove leading dots, spaces, and hidden file markers
    filename = filename.lstrip(". \t")
    if not filename:
        return "file.bin"
    # Truncate to safe length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:196] + ext[:4]
    return filename


def _store_file(file_obj, org_id, ref_type, ref_id):
    """Validate and store an evidence file.

    Performs content-based validation (not header-trusted). Generates an
    opaque server-side filename to prevent path traversal and injection.

    Returns (rel_path, safe_display_name, validated_mime_type) on success,
    or raises ValueError with a user-facing error message on failure.
    """
    # --- 1. Size check (individual file) ---
    file_obj.seek(0, os.SEEK_END)
    actual_size = file_obj.tell()
    file_obj.seek(0)
    if actual_size == 0:
        raise ValueError("Uploaded file is empty")
    if actual_size > MAX_FILE_SIZE:
        raise ValueError(f"File exceeds maximum size of {MAX_FILE_SIZE // (1024*1024)} MB")

    # --- 2. Content validation (magic bytes + PIL verify) ---
    validated_mime, safe_ext, error = _validate_file_content(file_obj)
    if error:
        raise ValueError(error)

    # --- 3. Safe display name ---
    display_name = _sanitize_filename(file_obj.filename or "file")

    # --- 4. Server-generated opaque filename ---
    uid = uuid.uuid4().hex[:16]
    rel = f"{org_id}/{ref_type}/{ref_id}/{uid}{safe_ext}"
    abs_path = os.path.join(STORAGE_ROOT, rel)

    # --- 5. Path containment check ---
    abs_real = os.path.realpath(abs_path)
    store_real = os.path.realpath(STORAGE_ROOT)
    if not abs_real.startswith(store_real + os.sep) and abs_real != store_real:
        os.remove(abs_path) if os.path.exists(abs_path) else None
        raise ValueError("Storage path violation — file rejected")

    # --- 6. Save ---
    os.makedirs(os.path.dirname(abs_real), exist_ok=True)
    file_obj.seek(0)
    file_obj.save(abs_real)

    # --- 7. Verify the saved file is readable and not empty ---
    if not os.path.exists(abs_real) or os.path.getsize(abs_real) == 0:
        raise ValueError("File could not be saved — storage error")

    return rel, display_name, validated_mime


def extract_evidence_intelligence(filename, mime_type):
    """Extract structured data from evidence filename using heuristics."""
    result = {"source": "heuristic"}
    name = (filename or "").lower()
    for p in [r'(?:utr|ref|txn|id)[:\s]*([A-Z0-9]{8,30})', r'([A-Z0-9]{8,30})\.(?:png|jpg|jpeg|pdf)$']:
        m = re.search(p, filename or "")
        if m: result["utr"] = m.group(1); break
    for p in [r'(?:amount|amt|rs|inr)[:\s]*([\d,]+(?:\.\d{2})?)', r'([\d,]+(?:\.\d{2})?)\s*(?:rs|inr|paid)']:
        m = re.search(p, name)
        if m:
            try: result["amount"] = float(m.group(1).replace(",", ""))
            except ValueError: pass
            break
    for p in [r'(\d{2}[-/]\d{2}[-/]\d{4})', r'(\d{4}[-/]\d{2}[-/]\d{2})']:
        m = re.search(p, filename or "")
        if m: result["date"] = m.group(1); break
    result["confidence"] = "medium"
    result["has_ocr"] = mime_type.startswith("image/") or mime_type == "application/pdf"
    return result


def transition_evidence(evidence_id, org_id, actor, target_status, note=""):
    """Transition evidence through its lifecycle."""
    ev = db.session.get(FinancialEvidence, evidence_id)
    if not ev or ev.organization_id != org_id:
        return {"error": "Evidence not found"}
    transitions = {"uploaded": ["ai_processing"], "ai_processing": ["ai_processed"],
        "ai_processed": ["matched"], "matched": ["verified"],
        "verified": ["accepted", "rejected", "matched"],
        "accepted": ["archived"], "rejected": ["archived", "uploaded"]}
    allowed = transitions.get(ev.status, [])
    if target_status not in allowed:
        return {"error": f"Cannot transition from {ev.status} to {target_status}"}
    old = ev.status; ev.status = target_status
    if target_status == "verified":
        ev.verified_by = actor; ev.verified_at = datetime.now(timezone.utc)
    if target_status == "rejected":
        ev.rejected_reason = note
    from app.relationship.integration import record_event
    from app.finance.controls import get_system_rel
    sys_rel = get_system_rel(org_id)
    record_event(relationship_id=sys_rel.id, organization_id=org_id,
        event_type=f"evidence.{target_status}",
        title=f"Evidence #{ev.id} {target_status}",
        description=f"Reference: {ev.reference_type}#{ev.reference_id}. Note: {note[:200]}",
        reference_type="evidence", reference_id=ev.id, created_by=actor)
    db.session.commit()
    return {"evidence": ev.to_dict()}


def check_evidence_policy(org_id, ref_type, ref_id, amount=0):
    """Check if evidence policy is satisfied for a reference."""
    policy = EvidencePolicy.query.filter_by(organization_id=org_id, doc_type=ref_type).first()
    if not policy: return {"satisfied": True, "policy": None}
    count = FinancialEvidence.query.filter_by(organization_id=org_id, reference_type=ref_type, reference_id=ref_id).count()
    if policy.requirement == "optional": return {"satisfied": True, "policy": policy.to_dict(), "count": count}
    if policy.requirement == "required" and count < policy.min_count:
        return {"satisfied": False, "policy": policy.to_dict(), "count": count,
            "required": policy.min_count, "error": f"Requires at least {policy.min_count} evidence item(s)"}
    if policy.requirement == "conditional" and policy.condition:
        try:
            cond = json.loads(policy.condition)
            if cond.get("min_amount") and amount > cond["min_amount"] and count < policy.min_count:
                return {"satisfied": False, "policy": policy.to_dict(), "count": count,
                    "required": policy.min_count, "error": f"Amount > {cond['min_amount']} requires evidence"}
        except (json.JSONDecodeError, TypeError): pass
    return {"satisfied": True, "policy": policy.to_dict(), "count": count}