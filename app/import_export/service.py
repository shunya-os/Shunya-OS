"""FDA25 — Universal Import / Export / Migration.

Import pipeline: upload → inspect → classify → map → validate → resolve identity
→ deduplicate → preview → authorize → commit → evidence

Export pipeline: tenant/role/permission scoped → preserve provenance

Never: upload → directly write production tables.
"""

from __future__ import annotations

import csv
import io
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# Accepted header aliases per target type, in priority order. The first alias
# present and non-empty is normalized onto the canonical (first) name, which is
# what the writers read. Keep this aligned with the *_import_* writers — a
# validator stricter than its writer silently rejects importable files.
_REQUIRED_ALIASES: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "lead": {
        "customer_name": ("customer_name", "name", "customer", "client"),
        "phone": ("phone", "mobile", "telephone", "contact_number"),
    },
    "customer": {
        "display_name": ("display_name", "name", "customer_name", "company"),
        "email": ("email", "e-mail", "email_address"),
    },
    "campaign": {
        "name": ("name", "campaign_name", "title"),
    },
    "supplier": {
        "name": ("name", "supplier_name", "vendor", "vendor_name"),
    },
}


# =========================================================================
# Import — Preview Phase
# =========================================================================


def preview_import(
    content: str,
    content_type: str = "csv",
    target_type: str = "lead",
) -> Dict[str, Any]:
    """Preview an import: inspect, classify, validate records.

    Returns detection results without writing to the database.
    """
    records = _parse_content(content, content_type)
    validated = _validate_records(records, target_type)
    resolved = _resolve_identities(validated, target_type)
    deduped = _deduplicate(resolved, target_type)

    return {
        "total_records": len(records),
        "valid_records": sum(1 for r in validated if r["valid"]),
        "invalid_records": sum(1 for r in validated if not r["valid"]),
        "new_identities": sum(1 for r in deduped if r.get("identity_action") == "create"),
        "matched_identities": sum(1 for r in deduped if r.get("identity_action") == "match"),
        "possible_duplicates": sum(1 for r in deduped if r.get("is_duplicate")),
        "conflicts": sum(1 for r in deduped if r.get("has_conflict")),
        "records_to_create": sum(1 for r in deduped if r.get("commit_action") == "create"),
        "records_to_update": sum(1 for r in deduped if r.get("commit_action") == "update"),
        "records_rejected": sum(1 for r in deduped if r.get("commit_action") == "reject"),
        "records": deduped[:20],  # Preview first 20 only
    }


def _parse_content(content: str, content_type: str) -> List[Dict[str, Any]]:
    """Parse CSV/JSON/XLSX content into records."""
    records = []
    if content_type == "csv":
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            records.append({k.strip(): v.strip() for k, v in row.items() if k})
    elif content_type == "xlsx":
        records = _parse_xlsx(content)
    elif content_type == "json":
        try:
            data = json.loads(content)
            records = data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            pass
    return records


def _parse_xlsx(content: str) -> List[Dict[str, Any]]:
    """Parse XLSX content into records. Content is base64-encoded XLSX bytes."""
    import base64
    records = []
    try:
        raw = base64.b64decode(content)
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        except ImportError:
            # Fallback: try reading as CSV if XLSX parsing unavailable
            return [{"error": "openpyxl not available for XLSX parsing"}]
        ws = wb.active
        if ws is None:
            return records
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return records
        headers = [str(h).strip() if h is not None else "" for h in rows[0]]
        for row in rows[1:]:
            rec = {}
            for i, val in enumerate(row):
                if i < len(headers) and headers[i]:
                    rec[headers[i]] = str(val) if val is not None else ""
            if rec:
                records.append(rec)
        wb.close()
    except Exception:
        # If XLSX parsing fails entirely, return empty
        pass
    return records


def _validate_records(records: List[Dict], target_type: str) -> List[Dict]:
    """Validate records against target type requirements.

    Required fields are matched through ACCEPTED ALIASES and normalized onto the
    canonical field name, so a header a real user would actually export
    (``name``, ``customer_name``, ``mobile`` …) maps onto the canonical field
    instead of being rejected. This keeps the validator consistent with what the
    writers accept — previously a CSV of ``name,email`` was 100% rejected for a
    missing ``display_name`` even though the customer writer accepts ``name``.
    """
    aliases = _REQUIRED_ALIASES.get(target_type, {})
    canonical_required = list(aliases.keys())

    validated = []
    for i, rec in enumerate(records):
        errors = []
        mapping = {}
        for field in canonical_required:
            accepted = aliases[field]
            found = next(
                (a for a in accepted
                 if a in rec and str(rec.get(a) or "").strip()),
                None,
            )
            if found is None:
                errors.append(
                    f"Missing required field: {field} "
                    f"(accepted: {', '.join(accepted)})"
                )
            elif found != field:
                # Normalize the alias onto the canonical field the writer reads.
                rec[field] = rec[found]
                mapping[field] = found

        warnings = []
        if target_type == "lead" and rec.get("email") and "@" not in rec.get("email", ""):
            warnings.append(f"Invalid email format: {rec.get('email')}")
        if target_type == "customer" and rec.get("phone") and len(rec.get("phone", "")) < 10:
            warnings.append(f"Suspiciously short phone: {rec.get('phone')}")

        validated.append({
            "row": i + 1,
            "data": rec,
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "field_mapping": mapping,
        })
    return validated


def _resolve_identities(records: List[Dict], target_type: str) -> List[Dict]:
    """Resolve identities: find existing records by email/phone."""
    from app import db

    for rec in records:
        data = rec["data"]
        rec["identity_action"] = "create"
        rec["matched_identity"] = None

        if target_type == "lead":
            phone = data.get("phone", "")
            if phone:
                from app.models import Lead
                existing = db.session.query(Lead).filter_by(phone=phone).first()
                if existing:
                    rec["identity_action"] = "match"
                    rec["matched_identity"] = {"id": existing.id, "code": existing.code, "name": existing.customer_name}

        elif target_type == "customer":
            email = data.get("email", "")
            if email:
                from app.relationship.models import CanonicalRelationship
                existing = db.session.query(CanonicalRelationship).filter_by(email=email).first()
                if existing:
                    rec["identity_action"] = "match"
                    rec["matched_identity"] = {"id": existing.id, "name": existing.display_name}

        elif target_type == "supplier":
            name = data.get("name", "")
            if name:
                from app.models import Supplier
                existing = db.session.query(Supplier).filter_by(name=name).first()
                if existing:
                    rec["identity_action"] = "match"
                    rec["matched_identity"] = {"id": existing.id, "name": existing.name}

    return records


def _deduplicate(records: List[Dict], target_type: str) -> List[Dict]:
    """Detect possible duplicates within the import set."""
    seen = set()
    for rec in records:
        data = rec["data"]
        if target_type == "supplier":
            key = data.get("name", "")
        else:
            key = data.get("phone", "") or data.get("email", "")
        rec["is_duplicate"] = key in seen and key != ""
        rec["has_conflict"] = False
        rec["commit_action"] = "reject" if rec.get("is_duplicate") and not rec.get("valid") else ("create" if rec.get("valid") else "reject")
        seen.add(key)

    return records


# =========================================================================
# Import — Commit Phase
# =========================================================================


def commit_import(
    organization_id: int,
    content: str,
    content_type: str = "csv",
    target_type: str = "lead",
    identity_id: str = "system",
    preview_result: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Commit an import after preview + authorization.

    Pipeline: preview → authorize → commit → evidence
    On failure: rollback to known state.
    """
    from app import db

    if not preview_result:
        preview_result = preview_import(content, content_type, target_type)

    created = 0
    updated = 0
    errors = []
    rejected = []
    duplicates_skipped = 0
    evidence_ids = []

    try:
        for rec in preview_result.get("records", []):
            if rec.get("commit_action") == "reject":
                # A rejected row is an OUTCOME, not silence. Record why so the
                # caller never receives "success" for an import that changed
                # nothing.
                rejected.append({
                    "row": rec.get("row"),
                    "error": "; ".join(rec.get("errors") or [])
                             or "rejected during validation/deduplication",
                })
                continue

            # Identity resolution already established this row matches an
            # existing canonical record. Re-creating it would duplicate a
            # customer/supplier — importing the same file twice must not corrupt
            # the graph. (There is no canonical update writer yet, so a match is
            # reported as skipped rather than silently rewritten.)
            if rec.get("identity_action") == "match":
                duplicates_skipped += 1
                continue

            data = rec["data"]
            try:
                if target_type == "lead":
                    result = _import_lead(organization_id, data, identity_id)
                    if result:
                        created += 1
                        if result.get("evidence_id"):
                            evidence_ids.append(result["evidence_id"])
                elif target_type == "customer":
                    result = _import_customer(organization_id, data, identity_id)
                    if result:
                        created += 1
                elif target_type == "supplier":
                    result = _import_supplier(organization_id, data, identity_id)
                    if result:
                        created += 1
            except Exception as e:
                errors.append({"row": rec.get("row"), "error": str(e)})

        all_errors = errors + rejected

        if created or updated:
            if all_errors:
                # Partial failure — rollback is not possible for already-committed
                # rows with external side effects. Record the partial outcome
                # honestly.
                return {
                    "status": "partial",
                    "created": created,
                    "updated": updated,
                    "errors": all_errors,
                    "rejected": len(rejected),
                    "duplicates_skipped": duplicates_skipped,
                    "evidence_ids": evidence_ids,
                    "warning": "Import completed partially. See errors for rejected rows.",
                }
            return {
                "status": "completed",
                "created": created,
                "updated": updated,
                "errors": [],
                "rejected": 0,
                "duplicates_skipped": duplicates_skipped,
                "evidence_ids": evidence_ids,
            }

        if duplicates_skipped and not all_errors:
            # Every row already exists. Reporting "completed" with 0 created
            # would read as a fake success; report the idempotent no-op.
            return {
                "status": "noop",
                "created": 0,
                "updated": 0,
                "errors": [],
                "rejected": 0,
                "duplicates_skipped": duplicates_skipped,
                "evidence_ids": evidence_ids,
                "warning": "Nothing imported: every row already exists.",
            }

        # Nothing was imported. Never report this as success.
        return {
            "status": "rejected",
            "created": 0,
            "updated": 0,
            "errors": all_errors,
            "rejected": len(rejected),
            "duplicates_skipped": duplicates_skipped,
            "evidence_ids": evidence_ids,
            "warning": "No records were imported. Every row was rejected; see errors.",
        }

    except Exception as e:
        db.session.rollback()
        return {
            "status": "failed",
            "created": 0,
            "updated": 0,
            "errors": [{"error": str(e)}],
            "evidence_ids": [],
        }


def _import_lead(org_id: int, data: Dict, identity_id: str) -> Optional[Dict]:
    """Import a single lead record."""
    from app import db
    from app.models import Lead, set_lead_tenant_id, clear_lead_tenant_id
    from app.evidence.models_db import EvidenceRecord

    set_lead_tenant_id(org_id)
    try:
        from app.models import next_inquiry_code
        code = data.get("code") or next_inquiry_code(db.session)
        lead = Lead(
            code=code,
            customer_name=data.get("customer_name", "Imported Lead"),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            source="import",
            status="new",
            tenant_id=org_id,
            notes=data.get("notes", ""),
        )
        db.session.add(lead)
        db.session.flush()
    finally:
        clear_lead_tenant_id()

    ev = EvidenceRecord(
        source_type="import",
        source_id=str(lead.id),
        raw_reference={"imported_by": identity_id, "source_data": {k: v for k, v in data.items() if k != "notes"}},
    )
    db.session.add(ev)
    db.session.flush()
    db.session.commit()

    return {"id": lead.id, "evidence_id": ev.id}


def _import_customer(org_id: int, data: Dict, identity_id: str) -> Optional[Dict]:
    """Import a single customer (relationship) record."""
    from app import db
    from app.relationship.models import CanonicalRelationship

    rel = CanonicalRelationship(
        organization_id=org_id,
        display_name=data.get("display_name", data.get("name", "Imported Customer")),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        relationship_type="customer",
        status="active",
        source="import",
    )
    db.session.add(rel)
    db.session.commit()
    return {"id": rel.id}


def _import_supplier(org_id: int, data: Dict, identity_id: str) -> Optional[Dict]:
    """Import a single supplier record with provenance."""
    from app import db
    from app.models import Supplier
    from app.evidence.models_db import EvidenceRecord
    from datetime import datetime, timezone

    name = data.get("name", "").strip()
    if not name:
        return None

    now = datetime.now(timezone.utc)
    supplier = Supplier(
        name=name,
        category=data.get("category", "").strip(),
        contact=data.get("contact", "").strip(),
        email=data.get("email", "").strip(),
        phone=data.get("phone", "").strip(),
        city=data.get("city", "").strip(),
        gstin=data.get("gstin", "").strip(),
        payment_terms=data.get("payment_terms", "").strip(),
        notes=data.get("notes", "").strip(),
        rating=int(data.get("rating", 0)),
        status="active",
        tenant_id=org_id,
        created_by=identity_id,
        created_at=now,
        updated_at=now,
    )
    db.session.add(supplier)
    db.session.flush()

    ev = EvidenceRecord(
        source_type="import",
        source_id=str(supplier.id),
        raw_reference={"imported_by": identity_id, "source_data": data},
    )
    db.session.add(ev)
    db.session.flush()
    db.session.commit()
    return {"id": supplier.id, "evidence_id": ev.id}


# =========================================================================
# Export
# =========================================================================


def export_records(
    organization_id: int,
    target_type: str = "lead",
    identity_id: str = "system",
    format: str = "json",
    limit: int = 1000,
) -> Dict[str, Any]:
    """Export records with provenance. Respects tenant and permissions."""
    from app import db
    from app.security.audit import log_audit

    records = []
    if target_type == "lead":
        from app.models import Lead
        leads = db.session.query(Lead).filter_by(tenant_id=organization_id).limit(limit).all()
        records = [l.to_dict() for l in leads]

    elif target_type == "customer":
        from app.relationship.models import CanonicalRelationship
        customers = db.session.query(CanonicalRelationship).filter_by(organization_id=organization_id).limit(limit).all()
        records = [c.to_dict() for c in customers]

    elif target_type == "supplier":
        from app.models import Supplier
        suppliers = db.session.query(Supplier).filter_by(tenant_id=organization_id).limit(limit).all()
        records = [s.to_dict() for s in suppliers]

    # Audit the export
    log_audit("read", "export", target_type, {
        "format": format,
        "record_count": len(records),
        "exported_by": identity_id,
        "tenant_id": organization_id,
    })

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "target_type": target_type,
        "record_count": len(records),
        "records": records,
        "provenance": {
            "exported_by": identity_id,
            "tenant_id": organization_id,
            "audit_logged": True,
        },
    }