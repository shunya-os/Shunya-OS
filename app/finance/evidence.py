"""FOR-2D.4: Financial Evidence Engine — Models and Services."""

import os, json, uuid, re
from datetime import datetime, timezone
from app import db
from sqlalchemy import Index


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


def _store_file(file_obj, org_id, ref_type, ref_id):
    os.makedirs(STORAGE_ROOT, exist_ok=True)
    ext = os.path.splitext(file_obj.filename or "file.bin")[1].lower()
    uid = uuid.uuid4().hex[:16]
    rel = f"{org_id}/{ref_type}/{ref_id}/{uid}{ext}"
    abs_path = os.path.join(STORAGE_ROOT, rel)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    file_obj.save(abs_path)
    return rel, file_obj.filename or "file", file_obj.content_type or "application/octet-stream"


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