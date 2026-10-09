"""FDA25 — Universal Import / Export / Migration.  [M6 semantic ingestion]

Import pipeline: upload → inspect → understand → map fields → detect ambiguity
→ resolve identity → detect duplicates → preview → human confirmation (when
required) → commit → provenance → correction → recovery → observable outcome

Export pipeline: tenant/role/permission scoped → preserve provenance

M6 contract notes (SH-M6→M15 directive, Stage A):
  * Column mapping is deterministic and EXPLAINABLE — every source column gets
    a mapping entry saying what SHUNYA understood, by which method, and why.
  * Ambiguity is surfaced explicitly (multiple columns for one field, name-like
    columns unmapped, conflicting duplicate rows) — never resolved silently.
  * Similar-but-not-equal supplier names are surfaced as candidates for a human
    and never auto-merged.
  * Every committed record carries provenance (source, file, row, session,
    mapping decision, method, author, timestamp) as an EvidenceRecord.
  * Corrections update canonical state and append auditable correction evidence.
  * Retry is idempotent: re-committing a file skips rows that already exist and
    never duplicates accepted records.

Never: upload → directly write production tables.
"""

from __future__ import annotations

import csv
import difflib
import io
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =========================================================================
# Canonical field registry — aliases per target type, in priority order.
#
# The first alias present and non-empty in a row is normalized onto the
# canonical (first listed) name, which is what the writers read. Keep this
# aligned with the *_import_* writers — a validator stricter than its writer
# silently rejects importable files.
#
# Each entry: canonical_field -> {aliases: (...), required: bool}
# =========================================================================

_FIELD_REGISTRY: Dict[str, Dict[str, Dict[str, Any]]] = {
    "lead": {
        "customer_name": {"aliases": ("customer_name", "name", "customer", "client"), "required": True},
        "phone": {"aliases": ("phone", "mobile", "telephone", "contact_number"), "required": True},
        "email": {"aliases": ("email", "e_mail", "mail", "email_address"), "required": False},
        "notes": {"aliases": ("notes", "note", "remarks", "comment", "comments"), "required": False},
    },
    "customer": {
        "display_name": {"aliases": (
            "display_name", "name", "customer_name", "customer", "client",
            "client_name", "guest", "guest_name", "party_name", "party",
            "full_name", "contact_name", "traveller", "traveler",
            "passenger_name",
        ), "required": True},
        "email": {"aliases": ("email", "e_mail", "mail", "email_address", "email_id"), "required": False},
        "phone": {"aliases": (
            "phone", "mobile", "mobile_number", "contact_number",
            "phone_number", "telephone", "cell", "cell_phone", "whatsapp",
            "contact_no", "mobile_no", "phone_no",
        ), "required": False},
        "company_name": {"aliases": (
            "company", "company_name", "organisation", "organization", "org",
            "firm", "business_name", "employer",
        ), "required": False},
        "address_line1": {"aliases": ("address", "address_line1", "address_line_1", "street", "full_address"), "required": False},
        "city": {"aliases": ("city", "town"), "required": False},
        "state": {"aliases": ("state", "province", "region"), "required": False},
        "postal_code": {"aliases": ("postal_code", "pincode", "pin_code", "zip", "zip_code"), "required": False},
        "country": {"aliases": ("country", "nation"), "required": False},
        "gstin": {"aliases": ("gstin", "gst", "gst_number", "gst_no", "tax_id", "vat"), "required": False},
        "source": {"aliases": ("source", "source_channel", "lead_source", "channel"), "required": False},
        "notes": {"aliases": (
            "notes", "note", "remarks", "comment", "comments", "description",
            "special_requests", "requests",
        ), "required": False},
    },
    "supplier": {
        "name": {"aliases": (
            "name", "supplier_name", "supplier", "vendor", "vendor_name",
            "hotel", "hotel_name", "dmc", "operator", "partner", "party_name",
            "company", "company_name",
        ), "required": True},
        "category": {"aliases": ("category", "type", "supplier_type", "vendor_type", "service_type", "segment"), "required": False},
        "contact": {"aliases": (
            "contact", "contact_person", "contact_name", "contact_person_name",
            "representative", "rep", "person",
        ), "required": False},
        "email": {"aliases": ("email", "e_mail", "mail", "email_address", "email_id"), "required": False},
        "phone": {"aliases": (
            "phone", "mobile", "mobile_number", "contact_number",
            "phone_number", "telephone", "cell", "contact_no", "mobile_no",
            "phone_no",
        ), "required": False},
        "city": {"aliases": ("city", "town", "destination"), "required": False},
        "gstin": {"aliases": ("gstin", "gst", "gst_number", "gst_no", "tax_id", "vat"), "required": False},
        "payment_terms": {"aliases": ("payment_terms", "payment_term", "terms", "credit_terms"), "required": False},
        "rating": {"aliases": ("rating", "score", "stars"), "required": False},
        "notes": {"aliases": ("notes", "note", "remarks", "comment", "comments"), "required": False},
    },
    "campaign": {
        "name": {"aliases": ("name", "campaign_name", "title"), "required": True},
    },
}


def _norm_col(name: str) -> str:
    """Normalize a column name: trim, lowercase, spaces/hyphens → underscore."""
    return str(name or "").strip().lower().replace(" ", "_").replace("-", "_")


def _alias_index(target_type: str) -> Dict[str, str]:
    """normalized alias → canonical field, for one target type."""
    index: Dict[str, str] = {}
    for field, spec in _FIELD_REGISTRY.get(target_type, {}).items():
        for alias in spec["aliases"]:
            index.setdefault(_norm_col(alias), field)
    return index


def _alias_priority(target_type: str, field: str, column: str) -> int:
    """Position of a column's normalized name within a field's alias list."""
    spec = _FIELD_REGISTRY.get(target_type, {}).get(field)
    if not spec:
        return 999
    normalized = _norm_col(column)
    for i, alias in enumerate(spec["aliases"]):
        if _norm_col(alias) == normalized:
            return i
    return 998  # not a listed alias (e.g. manual override)


# =========================================================================
# Import — Inspect / Understand (preview phase)
# =========================================================================


def preview_import(
    content: str,
    content_type: str = "csv",
    target_type: str = "lead",
    column_overrides: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Preview an import: inspect, understand, map, validate, resolve, dedupe.

    Returns the full interpretation — per-column mapping explanation with
    method and reasoning, surfaced ambiguities, per-record identity match
    basis and similar-entity candidates — without writing to the database.

    ``column_overrides``: optional human mapping decisions,
    ``{source_column: canonical_field}``. An empty-string target means
    "do not import this column".
    """
    records = _parse_content(content, content_type)
    columns = _extract_columns(records)

    mapping, ambiguities = explain_columns(
        columns, target_type, column_overrides=column_overrides,
        sample_rows=records[:20],
    )

    validated = _validate_records(records, target_type, mapping)
    resolved = _resolve_identities(validated, target_type)
    deduped = _deduplicate(resolved, target_type)
    ambiguities.extend(_detect_row_ambiguities(deduped, target_type))

    weak_rows = [r["row"] for r in deduped if r.get("weak_identity")]

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
        "weak_identity_rows": weak_rows,
        "column_mapping": mapping,
        "ambiguities": ambiguities,
        "requires_review": bool(ambiguities) or bool(weak_rows),
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


def _extract_columns(records: List[Dict]) -> List[str]:
    """Column names in source order, from the first record."""
    if not records:
        return []
    return list(records[0].keys())


# ── Column explanation ────────────────────────────────────────────────────


def _sample_does_look_like(samples: List[str], kind: str) -> bool:
    if not samples:
        return False
    if kind == "email":
        return any("@" in s and "." in s.split("@")[-1] for s in samples)
    if kind == "phone":
        digit_heavy = 0
        for s in samples:
            digits = re.sub(r"[^\d]", "", s)
            if len(digits) >= 7 and len(re.sub(r"[\d+\-() .]", "", s)) <= 2:
                digit_heavy += 1
        return digit_heavy >= max(1, len(samples) // 2)
    return False


def _name_like_tokens() -> Tuple[str, ...]:
    return ("name", "guest", "party", "client", "customer", "lead", "contact")


def explain_columns(
    columns: List[str],
    target_type: str,
    column_overrides: Optional[Dict[str, str]] = None,
    sample_rows: Optional[List[Dict]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Explain SHUNYA's interpretation of every source column.

    Returns ``(mapping, ambiguities)``.

    mapping entry: ``{source_column, target_field, method, confidence, reason}``
      method: ``alias`` (deterministic dictionary), ``manual`` (human decision),
      ``alias_fallback`` (only candidate for a required field), ``unmapped``.

    ambiguity entries carry a ``code``:
      * ``multiple_candidates`` — several columns could serve one canonical
        field; the chosen one is stated and overridable.
      * ``unmapped_name_like`` — a name-like column is not mapped; a human must
        decide (SHUNYA must not silently treat every name-like column as the
        entity name).
      * ``unmapped_email_like`` / ``unmapped_phone_like`` — same for contact
        identifiers.
    """
    overrides = {_norm_col(k): str(v) for k, v in (column_overrides or {}).items()}
    index = _alias_index(target_type)
    registry = _FIELD_REGISTRY.get(target_type, {})

    samples_by_col: Dict[str, List[str]] = {}
    for row in (sample_rows or []):
        for col in columns:
            v = row.get(col, "")
            if v is not None and str(v).strip():
                samples_by_col.setdefault(col, []).append(str(v).strip())

    mapping: List[Dict[str, Any]] = []
    candidates: Dict[str, List[str]] = {}

    for col in columns:
        ncol = _norm_col(col)
        entry = {
            "source_column": col,
            "target_field": "",
            "method": "unmapped",
            "confidence": 0.0,
            "reason": "",
        }
        if ncol in overrides:
            target = overrides[ncol]
            if target == "":
                entry.update(
                    target_field="", method="manual", confidence=1.0,
                    reason="you chose not to import this column",
                )
            elif target in registry:
                entry.update(
                    target_field=target, method="manual", confidence=1.0,
                    reason=f"your mapping decision: '{col}' → {target}",
                )
            else:
                entry.update(
                    target_field=target, method="manual", confidence=1.0,
                    reason=f"your mapping decision: '{col}' → {target} (custom target)",
                )
                candidates.setdefault(target, []).append(col)
            if entry["target_field"]:
                candidates.setdefault(entry["target_field"], []).append(col)
        elif ncol in index:
            target = index[ncol]
            entry.update(
                target_field=target, method="alias", confidence=1.0,
                reason=f"column name matches a known alias of '{target}'",
            )
            candidates.setdefault(target, []).append(col)
        else:
            entry["reason"] = "no known alias for this column — it will not be imported"
            nhint = ncol.replace("_", " ")
            samples = samples_by_col.get(col, [])
            if _sample_does_look_like(samples, "email"):
                entry["hint_code"] = "email_like"
                entry["reason"] = "values look like email addresses but the column is not mapped"
            elif _sample_does_look_like(samples, "phone"):
                entry["hint_code"] = "phone_like"
                entry["reason"] = "values look like phone numbers but the column is not mapped"
            elif any(tok in ncol for tok in _name_like_tokens()):
                entry["hint_code"] = "name_like"
                entry["reason"] = f"name-like column ('{col}') is not mapped — decide what it is"
        mapping.append(entry)

    # Fallback: a required field with no direct candidate may borrow the
    # company/name-like column available — explained, never silent.
    for field, spec in registry.items():
        if not spec.get("required"):
            continue
        if candidates.get(field):
            continue
        for col in columns:
            ncol = _norm_col(col)
            if ncol in overrides:
                continue
            borrowed = index.get(ncol)
            if borrowed and borrowed in ("company_name", "name"):
                candidates.setdefault(field, []).append(col)
                for e in mapping:
                    if e["source_column"] == col:
                        e["target_field"] = field
                        e["method"] = "alias_fallback"
                        e["confidence"] = 0.8
                        e["reason"] = (
                            f"no '{field}' column found; using '{col}' "
                            f"(a {borrowed} column) as the {field}"
                        )
                break

    ambiguities: List[Dict[str, Any]] = []
    for field, cols in candidates.items():
        if len(cols) > 1:
            def _pick(c: str) -> Tuple[int, int]:
                entry = next((e for e in mapping if e["source_column"] == c), None)
                if entry is not None and entry.get("method") == "manual":
                    return (0, cols.index(c))  # human decision wins
                return (_alias_priority(target_type, field, c), cols.index(c))

            chosen = sorted(cols, key=_pick)[0]
            others = [c for c in cols if c != chosen]
            # The chosen column is the ONE used by validation; alternatives are
            # marked as conflicted so the explanation and the applied mapping
            # can never disagree.
            for e in mapping:
                if e["source_column"] in others and e.get("target_field") == field:
                    e["conflict"] = True
                    e["conflict_note"] = (
                        f"not used for '{field}' — '{chosen}' was chosen "
                        f"(override to change)"
                    )
            ambiguities.append({
                "code": "multiple_candidates",
                "field": field,
                "columns": cols,
                "chosen": chosen,
                "message": (
                    f"{len(cols)} columns could serve '{field}': {', '.join(cols)}. "
                    f"SHUNYA will use '{chosen}'. If that is wrong, map the columns "
                    f"explicitly before importing."
                ),
            })

    for e in mapping:
        if e["method"] == "unmapped" and e.get("hint_code") == "name_like":
            ambiguities.append({
                "code": "unmapped_name_like",
                "column": e["source_column"],
                "message": (
                    f"'{e['source_column']}' looks like a name column but was not mapped. "
                    f"SHUNYA does not guess: decide whether it is the entity name or "
                    f"leave it unimported."
                ),
            })
        elif e["method"] == "unmapped" and e.get("hint_code") in ("email_like", "phone_like"):
            ambiguities.append({
                "code": f"unmapped_{e['hint_code']}",
                "column": e["source_column"],
                "message": (
                    f"'{e['source_column']}' looks like contact data but was not mapped; "
                    f"map it explicitly to import it."
                ),
            })

    return mapping, ambiguities


# ── Validation ────────────────────────────────────────────────────────────


def _validate_records(
    records: List[Dict],
    target_type: str,
    column_mapping: Optional[List[Dict]] = None,
) -> List[Dict]:
    """Validate records against the target registry.

    Required fields are matched through their ACCEPTED ALIASES and normalized
    onto the canonical field name. The effective mapping (alias or manual
    override) is preserved per record so provenance can explain which source
    column supplied each canonical field.
    """
    registry = _FIELD_REGISTRY.get(target_type, {})
    if not registry:
        return []

    columns = _extract_columns(records)
    # Source column → canonical field chosen for this import (last entry wins
    # for the fallback case where two fields borrow the same column).
    # Conflicted entries (ambiguity alternatives) are never applied.
    col_target: Dict[str, str] = {}
    col_method: Dict[str, str] = {}
    for e in (column_mapping or []):
        if e.get("target_field") and not e.get("conflict"):
            col_target[e["source_column"]] = e["target_field"]
            col_method[e["source_column"]] = e.get("method", "")

    validated = []
    for i, rec in enumerate(records):
        errors = []
        warnings = []
        effective_mapping: Dict[str, str] = {}  # canonical field → source column

        # 1. Apply explicit mappings (aliases resolved, overrides enforced).
        for col in columns:
            target = col_target.get(col)
            if not target or target not in registry:
                continue
            if col in rec and str(rec.get(col) or "").strip():
                if target not in effective_mapping:
                    rec[target] = rec[col]
                    effective_mapping[target] = col
                # A required field borrowed from a company/name column is ALSO
                # the company value — recorded explicitly, never silently.
                if col_method.get(col) == "alias_fallback" and target == "display_name":
                    if not str(rec.get("company_name") or "").strip():
                        rec["company_name"] = rec[col]
                        effective_mapping["company_name"] = col

        # 2. Required-field checks on the canonical names.
        for field, spec in registry.items():
            if spec.get("required") and not str(rec.get(field) or "").strip():
                errors.append(
                    f"Missing required field: {field} "
                    f"(accepted: {', '.join(spec['aliases'])})"
                )

        # 3. Format warnings (never silent).
        if rec.get("email") and "@" not in str(rec.get("email", "")):
            warnings.append(f"Invalid email format: {rec.get('email')}")
        if target_type == "customer" and rec.get("phone") and len(re.sub(r"[^\d]", "", str(rec.get("phone", "")))) < 7:
            warnings.append(f"Suspiciously short phone: {rec.get('phone')}")

        # 4. Weak identity — no email AND no phone. Importable, but flagged.
        weak_identity = False
        if target_type in ("customer", "supplier"):
            has_email = bool(str(rec.get("email") or "").strip())
            has_phone = bool(str(rec.get("phone") or "").strip())
            if not has_email and not has_phone:
                weak_identity = True
                warnings.append(
                    "no email or phone — will be imported with a weak identity "
                    "(harder to match or correct later)"
                )

        validated.append({
            "row": i + 1,
            "data": rec,
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "weak_identity": weak_identity,
            "field_mapping": effective_mapping,
        })
    return validated


# ── Identity resolution ───────────────────────────────────────────────────


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()


def find_similar_entities(
    name: str,
    target_type: str,
    organization_id: int,
    threshold: float = 0.82,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Deterministic similar-name candidates (never auto-merged).

    Exact matches are NOT returned here — they are handled by identity
    resolution. This surfaces *similar but not equal* names so a human can
    decide whether the row is the same entity or a genuinely separate one.
    """
    from app import db

    name_n = (name or "").strip()
    if not name_n:
        return []

    pool = []
    if target_type == "supplier":
        from app.models import Supplier
        pool = [
            {"id": s.id, "name": s.name}
            for s in db.session.query(Supplier)
            .filter(Supplier.tenant_id == organization_id)
            .order_by(Supplier.id.desc()).limit(500).all()
        ]
        key = "name"
    elif target_type == "customer":
        from app.relationship.models import CanonicalRelationship
        pool = [
            {"id": r.id, "name": r.display_name}
            for r in db.session.query(CanonicalRelationship)
            .filter(CanonicalRelationship.organization_id == organization_id)
            .order_by(CanonicalRelationship.id.desc()).limit(500).all()
        ]
        key = "name"
    else:
        return []

    out = []
    for cand in pool:
        other = cand[key] or ""
        if other.strip().lower() == name_n.lower():
            continue  # exact match → identity resolution handles it
        ratio = _similarity(name_n, other)
        if ratio >= threshold:
            out.append({
                "id": cand["id"],
                "name": other,
                "similarity": round(ratio, 2),
                "basis": f"name is {round(ratio * 100)}% similar to existing '{other}' — not merged, your call",
            })
    out.sort(key=lambda c: -c["similarity"])
    return out[:limit]


def _resolve_identities(records: List[Dict], target_type: str) -> List[Dict]:
    """Resolve identities: find existing records by the strongest identifiers.

    Every match carries an explicit ``match_basis`` explaining WHY it matched —
    the human can audit the proposal. Similar-but-not-equal names become
    ``similar_candidates``, not matches.
    """
    from app import db

    for rec in records:
        data = rec["data"]
        rec["identity_action"] = "create"
        rec["matched_identity"] = None
        rec["match_basis"] = ""
        rec["similar_candidates"] = []

        if target_type == "lead":
            phone = str(data.get("phone", "") or "").strip()
            email = str(data.get("email", "") or "").strip().lower()
            if phone:
                from app.models import Lead
                existing = db.session.query(Lead).filter_by(phone=phone).first()
                if existing:
                    rec["identity_action"] = "match"
                    rec["matched_identity"] = {"id": existing.id, "code": existing.code, "name": existing.customer_name}
                    rec["match_basis"] = f"phone {phone} already belongs to lead {existing.code}"

        elif target_type == "customer":
            from app.relationship.models import CanonicalRelationship
            email = str(data.get("email", "") or "").strip().lower()
            phone = str(data.get("phone", "") or "").strip()
            existing = None
            basis = ""
            org_id = _org_of(rec)
            if email:
                existing = (
                    db.session.query(CanonicalRelationship)
                    .filter(CanonicalRelationship.organization_id == org_id)
                    .filter(CanonicalRelationship.email == email)
                    .first()
                )
                if existing:
                    basis = f"email {email} already belongs to customer #{existing.id} ({existing.display_name})"
            if existing is None and phone:
                phone_digits = re.sub(r"[^\d]", "", phone)
                if len(phone_digits) >= 7:
                    candidates_q = (
                        db.session.query(CanonicalRelationship)
                        .filter(CanonicalRelationship.organization_id == org_id)
                        .filter(CanonicalRelationship.phone != "")
                        .limit(500)
                    )
                    for cand in candidates_q:
                        if re.sub(r"[^\d]", "", str(cand.phone or "")) == phone_digits:
                            existing = cand
                            basis = f"phone {phone} matches customer #{cand.id} ({cand.display_name})"
                            break
            if existing:
                rec["identity_action"] = "match"
                rec["matched_identity"] = {"id": existing.id, "name": existing.display_name}
                rec["match_basis"] = basis
            elif phone or email:
                rec["match_basis"] = (
                    f"no existing customer with this email/phone in the organization — "
                    f"row will create a new customer"
                )
            if str(data.get("display_name", "") or "").strip():
                rec["similar_candidates"] = find_similar_entities(
                    data.get("display_name", ""), "customer", _org_of(rec)
                )

        elif target_type == "supplier":
            from app.models import Supplier
            name = str(data.get("name", "") or "").strip()
            org_id = _org_of(rec)
            existing = None
            if name:
                existing = (
                    db.session.query(Supplier)
                    .filter(Supplier.tenant_id == org_id)
                    .filter(Supplier.name == name)
                    .first()
                )
            if existing:
                rec["identity_action"] = "match"
                rec["matched_identity"] = {"id": existing.id, "name": existing.name}
                rec["match_basis"] = f"supplier name '{name}' already exists as #{existing.id}"
            elif name:
                rec["similar_candidates"] = find_similar_entities(name, "supplier", org_id)
                if rec["similar_candidates"]:
                    rec["match_basis"] = (
                        "no exact match — similar suppliers surfaced as candidates; "
                        "SHUNYA does not merge similar names"
                    )
                else:
                    rec["match_basis"] = "no existing supplier with this name — row will create a new supplier"

    return records


# Organization context is attached to the preview/commit call (single org per
# operation); records carry it for identity resolution.
_CURRENT_ORG: Optional[int] = None


def _org_of(rec: Dict) -> int:
    if rec.get("_org_id") is not None:
        return rec["_org_id"]
    if _CURRENT_ORG is not None:
        return _CURRENT_ORG
    try:
        from app.authz.decorators import _resolve_org_id
        return _resolve_org_id() or 0
    except Exception:
        return 0


def _deduplicate(records: List[Dict], target_type: str) -> List[Dict]:
    """Detect duplicates and conflicts within the import set itself.

    * Same strong identifier twice in one file → the later row is rejected as a
      within-file duplicate (with the first row's number stated).
    * Same identifier but a DIFFERENT name → conflict; rejected for human
      review. SHUNYA never silently merges conflicting rows.
    """
    seen: Dict[str, Dict[str, Any]] = {}
    for rec in records:
        data = rec["data"]
        if target_type == "supplier":
            key = str(data.get("name", "") or "").strip().lower()
            name_val = str(data.get("name", "") or "").strip()
        else:
            key = (
                str(data.get("phone", "") or "").strip()
                or str(data.get("email", "") or "").strip().lower()
                or str(data.get("customer_name", "") or data.get("display_name", "") or "").strip().lower()
            )
            name_val = str(
                data.get("customer_name", "") or data.get("display_name", "") or ""
            ).strip()

        rec["is_duplicate"] = False
        rec["has_conflict"] = False

        if key and key in seen:
            first = seen[key]
            rec["is_duplicate"] = True
            same_name = (first["name"].lower() == name_val.lower()) if name_val else True
            if not same_name:
                rec["has_conflict"] = True
                rec["errors"].append(
                    f"conflicts with row {first['row']}: same identifier but different name "
                    f"('{first['name']}' vs '{name_val}') — needs a human decision"
                )
                if rec["valid"]:
                    rec["valid"] = False
            else:
                rec["errors"].append(
                    f"duplicate within this file: same identifier as row {first['row']}"
                )
                if rec["valid"]:
                    rec["valid"] = False
            rec["commit_action"] = "reject"
        else:
            rec["commit_action"] = "create" if rec.get("valid") else "reject"
            if key:
                seen[key] = {"row": rec["row"], "name": name_val}

    return records


def _detect_row_ambiguities(records: List[Dict], target_type: str) -> List[Dict[str, Any]]:
    """Row-level ambiguity entries surfaced for human review."""
    out = []
    for rec in records:
        if rec.get("has_conflict"):
            out.append({
                "code": "conflicting_duplicate",
                "row": rec["row"],
                "message": "; ".join(rec.get("errors") or []),
            })
        for cand in rec.get("similar_candidates") or []:
            out.append({
                "code": "similar_existing_entity",
                "row": rec["row"],
                "candidate": cand,
                "message": (
                    f"Row {rec['row']}: '{rec['data'].get('name') or rec['data'].get('display_name')}' "
                    f"resembles existing '{cand['name']}' (#{cand['id']}, {int(cand['similarity'] * 100)}% similar). "
                    f"It will be created as a SEPARATE record unless you decide otherwise."
                ),
            })
    return out


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
    source_name: str = "",
    session_token: str = "",
    column_overrides: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Commit an import after preview + authorization + human confirmation.

    Pipeline: preview → authorize → commit → provenance → canonical event.

    Every created record writes an EvidenceRecord carrying full provenance:
    source type/file, row number, effective field mapping, mapping method,
    import session, author, timestamp. ``evidence_ids`` and a per-row
    ``provenance`` list are returned so the outcome is observable.

    Retry safety: rows whose identifiers already exist are matched and
    skipped (``duplicates_skipped`` + ``skipped_details``); a re-commit after
    a partial failure never duplicates accepted records.
    """
    from app import db

    global _CURRENT_ORG
    _CURRENT_ORG = organization_id
    try:
        if not preview_result:
            preview_result = preview_import(
                content, content_type, target_type,
                column_overrides=column_overrides,
            )

        import_session = (session_token or "").strip() or uuid.uuid4().hex
        imported_at = datetime.now(timezone.utc).isoformat()
        safe_source_name = (source_name or "").strip()[:200] or "pasted content"

        created = 0
        updated = 0
        errors = []
        rejected = []
        duplicates_skipped = 0
        evidence_ids = []
        provenance = []
        skipped_details = []
        records_created = []

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
                # customer/supplier — importing the same file twice must not
                # corrupt the graph. The skip is reported, with its basis.
                if rec.get("identity_action") == "match":
                    duplicates_skipped += 1
                    skipped_details.append({
                        "row": rec.get("row"),
                        "matched": rec.get("matched_identity"),
                        "basis": rec.get("match_basis", ""),
                    })
                    continue

                data = rec["data"]
                field_mapping = dict(rec.get("field_mapping") or {})
                try:
                    result = None
                    if target_type == "lead":
                        result = _import_lead(organization_id, data, identity_id)
                    elif target_type == "customer":
                        result = _import_customer(organization_id, data, identity_id)
                    elif target_type == "supplier":
                        result = _import_supplier(organization_id, data, identity_id)

                    if result:
                        created += 1
                        record_id = result.get("id")
                        # Enrich the evidence with the full M6 provenance.
                        ev_id = result.get("evidence_id")
                        if ev_id is not None:
                            _attach_provenance(
                                ev_id,
                                target_type=target_type,
                                record_id=record_id,
                                row=rec.get("row"),
                                import_session=import_session,
                                source_type=content_type,
                                source_name=safe_source_name,
                                field_mapping=field_mapping,
                                data=data,
                                identity_id=identity_id,
                                imported_at=imported_at,
                            )
                            evidence_ids.append(ev_id)
                        provenance.append({
                            "row": rec.get("row"),
                            "target_type": target_type,
                            "record_id": record_id,
                            "evidence_id": ev_id,
                        })
                        records_created.append({
                            "row": rec.get("row"),
                            "id": record_id,
                            "name": data.get("display_name") or data.get("name") or data.get("customer_name") or "",
                        })
                except Exception as e:
                    errors.append({"row": rec.get("row"), "error": str(e)})

            all_errors = errors + rejected

            if created or updated:
                status = "partial" if all_errors else "completed"
            elif duplicates_skipped and not all_errors:
                # Every row already exists. Reporting "completed" with 0 created
                # would read as a fake success; report the idempotent no-op.
                status = "noop"
            elif duplicates_skipped and all_errors:
                status = "partial"
            else:
                status = "rejected"

            result = {
                "status": status,
                "created": created,
                "updated": updated,
                "errors": all_errors,
                "rejected": len(rejected),
                "duplicates_skipped": duplicates_skipped,
                "skipped_details": skipped_details,
                "evidence_ids": evidence_ids,
                "provenance": provenance,
                "records_created": records_created,
                "import_session": import_session,
                "source_name": safe_source_name,
            }
            if status == "partial":
                result["warning"] = "Import completed partially. See errors for rejected rows."
            elif status == "noop":
                result["warning"] = "Nothing imported: every row already exists."
            elif status == "rejected":
                result["warning"] = (
                    "No records were imported. Every row was rejected; see errors."
                    if all_errors else
                    "No records were imported. The content parsed to zero rows — check the file format."
                )

            # Observable outcome: emit a canonical event for the batch
            # (non-fatal — the import is already committed).
            _emit_import_event(
                organization_id=organization_id,
                import_session=import_session,
                target_type=target_type,
                identity_id=identity_id,
                source_name=safe_source_name,
                result=result,
            )
            return result

        except Exception as e:
            db.session.rollback()
            return {
                "status": "failed",
                "created": 0,
                "updated": 0,
                "errors": [{"error": str(e)}],
                "rejected": 0,
                "duplicates_skipped": 0,
                "skipped_details": [],
                "evidence_ids": [],
                "provenance": [],
                "records_created": [],
                "import_session": import_session,
                "source_name": safe_source_name,
                "warning": "Import failed; no records were written in this attempt.",
            }
    finally:
        _CURRENT_ORG = None


def _attach_provenance(
    evidence_id: int,
    *,
    target_type: str,
    record_id: Any,
    row: Any,
    import_session: str,
    source_type: str,
    source_name: str,
    field_mapping: Dict[str, str],
    data: Dict,
    identity_id: str,
    imported_at: str,
) -> None:
    """Rewrite the evidence record with the full M6 provenance payload.

    The evidence row is the persisted answer to "Where did SHUNYA get this,
    and why does it believe the record means what it means?"
    """
    from app import db
    from app.evidence.models_db import EvidenceRecord

    ev = db.session.get(EvidenceRecord, evidence_id)
    if ev is None:
        return

    raw = dict(ev.raw_reference or {})
    raw.update({
        "target_type": target_type,
        "record_id": record_id,
        "row": row,
        "import_session": import_session,
        "source_type": source_type,
        "source_name": source_name,
        "field_mapping": field_mapping,
        "mapping_method": "alias_or_manual",
        "imported_by": identity_id,
        "imported_at": imported_at,
        "transformations": [
            "parsed",
            "column_mapping",
            "identity_resolution",
            "deduplication",
            "canonical_write",
            "provenance_recorded",
        ],
    })
    # Keep the raw source data for audit (bounded).
    raw["source_data"] = {k: (str(v)[:200] if not isinstance(v, (int, float, bool, type(None))) else v)
                          for k, v in list(data.items())[:60]}
    ev.source_id = f"{target_type}:{record_id}"
    ev.raw_reference = raw
    db.session.commit()


def _emit_import_event(
    *,
    organization_id: int,
    import_session: str,
    target_type: str,
    identity_id: str,
    source_name: str,
    result: Dict[str, Any],
) -> None:
    """Publish a canonical ingestion event for the batch (non-fatal)."""
    try:
        from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus

        event = CanonicalEvent(
            event_type="ingestion:import",
            tenant_id=organization_id,
            workspace_id=None,
            actor_id=identity_id or "system",
            actor_type="import",
            actor_name=source_name,
            object_id=import_session,
            object_type="ingestion",
            payload={
                "target_type": target_type,
                "created": result.get("created"),
                "updated": result.get("updated"),
                "rejected": result.get("rejected"),
                "duplicates_skipped": result.get("duplicates_skipped"),
                "status": result.get("status"),
                "import_session": import_session,
                "source_name": source_name,
            },
            confidence=1.0,
        )
        get_event_bus().publish(event)
    except Exception as e:  # pragma: no cover — event emission is advisory
        logger.warning("Import canonical event emission failed (non-blocking): %s", e)


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
    """Import a single customer as a canonical relationship (type=customer)."""
    from app import db
    from app.relationship.models import CanonicalRelationship
    from app.relationship.services import create_relationship
    from app.evidence.models_db import EvidenceRecord

    custom = {}
    if str(data.get("gstin", "") or "").strip():
        custom["gstin"] = str(data.get("gstin")).strip()

    payload = {
        "display_name": data.get("display_name", data.get("name", "Imported Customer")),
        "email": data.get("email", ""),
        "phone": data.get("phone", ""),
        "company_name": data.get("company_name", ""),
        "address_line1": data.get("address_line1", ""),
        "city": data.get("city", ""),
        "state": data.get("state", ""),
        "postal_code": data.get("postal_code", ""),
        "country": data.get("country", ""),
        "notes": data.get("notes", ""),
        "source": data.get("source", "import"),
        "relationship_type": "customer",
        "status": "active",
        "custom_attributes": custom,
    }
    rel = create_relationship(org_id, payload, created_by=identity_id)
    db.session.flush()

    ev = EvidenceRecord(
        source_type="import",
        source_id=str(rel.id),
        raw_reference={"imported_by": identity_id, "source_data": {k: v for k, v in data.items() if k != "notes"}},
    )
    db.session.add(ev)
    db.session.flush()
    db.session.commit()
    return {"id": rel.id, "evidence_id": ev.id}


def _import_supplier(org_id: int, data: Dict, identity_id: str) -> Optional[Dict]:
    """Import a single supplier record with provenance."""
    from app import db
    from app.models import Supplier
    from app.evidence.models_db import EvidenceRecord

    name = str(data.get("name", "")).strip()
    if not name:
        return None

    now = datetime.now(timezone.utc)
    try:
        rating = int(data.get("rating", 0) or 0)
    except (TypeError, ValueError):
        rating = 0

    supplier = Supplier(
        name=name,
        category=str(data.get("category", "") or "").strip(),
        contact=str(data.get("contact", "") or "").strip(),
        email=str(data.get("email", "") or "").strip(),
        phone=str(data.get("phone", "") or "").strip(),
        city=str(data.get("city", "") or "").strip(),
        gstin=str(data.get("gstin", "") or "").strip(),
        payment_terms=str(data.get("payment_terms", "") or "").strip(),
        notes=str(data.get("notes", "") or "").strip(),
        rating=rating,
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
# Provenance read — "Where did SHUNYA get this information?"
# =========================================================================


def _fetch_scoped_record(target_type: str, record_id: int, organization_id: int):
    """Fetch a record ONLY within the caller's organization. Fail closed."""
    from app import db

    if target_type == "customer":
        from app.relationship.models import CanonicalRelationship
        return (
            db.session.query(CanonicalRelationship)
            .filter(CanonicalRelationship.id == record_id)
            .filter(CanonicalRelationship.organization_id == organization_id)
            .first()
        )
    if target_type == "supplier":
        from app.models import Supplier
        return (
            db.session.query(Supplier)
            .filter(Supplier.id == record_id)
            .filter(Supplier.tenant_id == organization_id)
            .first()
        )
    if target_type == "lead":
        from app.models import Lead
        return (
            db.session.query(Lead)
            .filter(Lead.id == record_id)
            .filter(Lead.tenant_id == organization_id)
            .first()
        )
    return None


def get_record_provenance(
    target_type: str,
    record_id: int,
    organization_id: int,
) -> Optional[Dict[str, Any]]:
    """Full provenance trail for a record — origin, mapping, corrections.

    Returns None when the record does not exist in this organization
    (fail closed — provenance is not a cross-tenant read surface).
    """
    from app import db
    from app.evidence.models_db import EvidenceRecord

    record = _fetch_scoped_record(target_type, record_id, organization_id)
    if record is None:
        return None

    scoped_ids = [f"{target_type}:{record_id}"]
    if target_type == "lead":
        # Legacy format wrote the bare id as source_id for leads.
        scoped_ids.append(str(record_id))

    rows = (
        db.session.query(EvidenceRecord)
        .filter(EvidenceRecord.source_type.in_(("import", "import_correction")))
        .filter(EvidenceRecord.source_id.in_(scoped_ids))
        .order_by(EvidenceRecord.id.asc())
        .all()
    )

    entries = []
    origin = None
    corrections = []
    for ev in rows:
        raw = ev.raw_reference or {}
        if ev.source_type == "import":
            entry = {
                "kind": "import",
                "evidence_id": ev.id,
                "source_type": raw.get("source_type", ""),
                "source_name": raw.get("source_name", ""),
                "row": raw.get("row"),
                "import_session": raw.get("import_session", ""),
                "field_mapping": raw.get("field_mapping", {}),
                "mapping_method": raw.get("mapping_method", ""),
                "imported_by": raw.get("imported_by", ""),
                "imported_at": raw.get("imported_at", ""),
                "transformations": raw.get("transformations", []),
                "legacy": not raw.get("import_session"),
            }
            entries.append(entry)
            if origin is None:
                origin = entry
        else:
            correction = {
                "kind": "correction",
                "evidence_id": ev.id,
                "field": raw.get("field", ""),
                "old_value": raw.get("old_value", ""),
                "new_value": raw.get("new_value", ""),
                "reason": raw.get("reason", ""),
                "corrected_by": raw.get("corrected_by", ""),
                "corrected_at": raw.get("corrected_at", ""),
            }
            entries.append(correction)
            corrections.append(correction)

    summary = {}
    try:
        summary = record.to_dict()
    except Exception:
        summary = {"id": getattr(record, "id", None)}

    return {
        "target_type": target_type,
        "record_id": record_id,
        "record": summary,
        "origin": origin,
        "corrections": corrections,
        "entries": entries,
        "has_provenance": origin is not None,
    }


# =========================================================================
# Correction — auditable, never silent
# =========================================================================

_CORRECTABLE_FIELDS: Dict[str, set] = {
    "customer": {
        "display_name", "email", "phone", "company_name", "address_line1",
        "city", "state", "postal_code", "country", "notes", "status",
    },
    "supplier": {
        "name", "category", "contact", "email", "phone", "city", "gstin",
        "payment_terms", "notes", "rating", "status",
    },
    "lead": {"customer_name", "phone", "email", "notes", "status"},
}


def correct_record(
    target_type: str,
    record_id: int,
    field: str,
    new_value: Any,
    organization_id: int,
    identity_id: str,
    reason: str = "",
) -> Dict[str, Any]:
    """Correct a field on an imported record; append auditable correction evidence.

    Corrections update canonical state in place and record who changed what,
    from which value to which value, when, and why — the provenance trail
    gains a correction entry; nothing is silently overwritten.
    """
    from app import db
    from app.evidence.models_db import EvidenceRecord

    allowed = _CORRECTABLE_FIELDS.get(target_type)
    if allowed is None:
        return {"ok": False, "error": f"corrections are not supported for '{target_type}'"}
    if field not in allowed:
        return {"ok": False, "error": f"field '{field}' is not correctable for {target_type}"}

    record = _fetch_scoped_record(target_type, record_id, organization_id)
    if record is None:
        return {"ok": False, "error": "record not found"}

    old_value = getattr(record, field, None)
    value: Any = new_value
    if isinstance(value, str):
        value = value.strip()
    if field == "rating":
        try:
            value = int(value or 0)
        except (TypeError, ValueError):
            return {"ok": False, "error": "rating must be a number"}
    if field in ("display_name", "name", "customer_name") and not str(value or "").strip():
        return {"ok": False, "error": f"{field} cannot be empty"}

    try:
        setattr(record, field, value)
        if hasattr(record, "updated_at"):
            record.updated_at = datetime.now(timezone.utc)
        db.session.flush()

        corrected_at = datetime.now(timezone.utc).isoformat()
        ev = EvidenceRecord(
            source_type="import_correction",
            source_id=f"{target_type}:{record_id}",
            raw_reference={
                "field": field,
                "old_value": str(old_value)[:500] if old_value is not None else "",
                "new_value": str(value)[:500],
                "reason": (reason or "").strip()[:500],
                "corrected_by": identity_id,
                "corrected_at": corrected_at,
            },
        )
        db.session.add(ev)
        db.session.flush()
        db.session.commit()

        # Relationship timeline entry (canonical, best-effort).
        if target_type == "customer":
            try:
                from app.relationship.services import _add_timeline_entry
                _add_timeline_entry(
                    organization_id=organization_id,
                    relationship_id=record_id,
                    event_type="relationship.corrected",
                    title=f"Corrected {field}",
                    description=f"{field}: '{str(old_value)[:120]}' → '{str(value)[:120]}'",
                    created_by=identity_id,
                )
                db.session.commit()
            except Exception as e:  # pragma: no cover — timeline is advisory
                logger.warning("Correction timeline entry failed (non-blocking): %s", e)
    except Exception as e:
        db.session.rollback()
        return {"ok": False, "error": f"correction failed: {e}"}

    try:
        record_dict = record.to_dict()
    except Exception:
        record_dict = {"id": record_id}

    return {
        "ok": True,
        "target_type": target_type,
        "record_id": record_id,
        "record": record_dict,
        "correction": {
            "field": field,
            "old_value": str(old_value)[:500] if old_value is not None else "",
            "new_value": str(value)[:500],
            "reason": (reason or "").strip()[:500],
            "corrected_by": identity_id,
            "corrected_at": corrected_at,
        },
        "evidence_id": ev.id,
    }


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
