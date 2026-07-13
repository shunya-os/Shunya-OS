"""
Panchi Club — Data Import Engine

Supports CSV/JSON ingestion, fuzzy column matching, data inspection,
and batch Lead creation with activity logging.
"""

import csv
import io
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app import db
from app.models import ActivityLog, Lead, LeadSource, next_inquiry_code


# ---------------------------------------------------------------------------
# ColumnMatch — output of fuzzy matching
# ---------------------------------------------------------------------------

@dataclass
class ColumnMatch:
    """Describes how a source column was matched to a target field."""
    source_column: str
    target_field: str
    strategy: str  # exact / label / substring / non_match
    confidence: float = 1.0


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_csv(content: str) -> list[dict[str, str]]:
    """
    Parse CSV string content into a list of dicts.
    Handles leading/trailing whitespace in headers and values.
    Returns empty list for empty content.
    """
    if not content or not content.strip():
        return []

    reader = csv.DictReader(io.StringIO(content.strip()))
    rows = []
    for row in reader:
        cleaned = {k.strip(): v.strip() if v else "" for k, v in row.items()}
        rows.append(cleaned)

    return rows


def parse_json(content: str) -> list[dict[str, str]]:
    """
    Parse JSON string content into a list of dicts.
    Accepts either a JSON array or a JSON object (single record wrapped).
    Returns empty list for empty or non-dict/list content.
    """
    if not content or not content.strip():
        return []

    data = json.loads(content)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []


# ---------------------------------------------------------------------------
# Fuzzy column matching
# ---------------------------------------------------------------------------

# Known target fields → list of aliases
_TARGET_ALIASES: dict[str, list[str]] = {
    "customer_name": ["name", "customer name", "client name", "guest name", "full name", "traveller name", "traveler name"],
    "phone": ["mobile", "phone number", "contact", "contact number", "tel", "telephone", "whatsapp"],
    "email": ["e-mail", "email address", "mail"],
    "destination": ["dest", "place", "city", "location", "travel destination", "going to", "to"],
    "pax": ["guests", "adults", "passengers", "travellers", "travelers", "people", "persons", "number of guests"],
    "dates": ["date", "travel dates", "trip dates", "start date", "when", "period"],
    "budget": ["price", "cost", "amount", "spend", "max budget", "budget range", "estimated budget"],
    "notes": ["note", "comments", "remarks", "special requests", "requirements", "additional info", "extra"],
}

# Fields considered "required" for a valid import
_REQUIRED_FIELDS = ["customer_name", "destination"]


def _normalise(s: str) -> str:
    """Lower-case and collapse whitespace."""
    return re.sub(r"\s+", " ", s.strip().lower())


def _fuzzy_match(source_columns: list[str], target_fields: list[str] | None = None) -> list[ColumnMatch]:
    """
    Match source CSV/JSON column names to known target fields.

    Strategies tried in order:
      1. exact       — source column equals target field name
      2. label       — source column matches an alias in _TARGET_ALIASES
      3. substring   — normalised alias is a substring of source column or vice versa
      4. non_match   — no match found

    Returns one ColumnMatch per source column.
    """
    if target_fields is None:
        target_fields = list(_TARGET_ALIASES.keys())

    results: list[ColumnMatch] = []
    remaining_targets = set(target_fields)

    for source_col in source_columns:
        norm_source = _normalise(source_col)
        match = None

        # 1. Exact match (case-insensitive)
        for tf in target_fields:
            if _normalise(tf) == norm_source and tf in remaining_targets:
                match = ColumnMatch(source_col, tf, "exact", 1.0)
                remaining_targets.discard(tf)
                break

        # 2. Label match — check aliases
        if match is None:
            for tf in target_fields:
                if tf not in remaining_targets:
                    continue
                aliases = _TARGET_ALIASES.get(tf, [])
                if norm_source in (_normalise(a) for a in aliases):
                    match = ColumnMatch(source_col, tf, "label", 0.9)
                    remaining_targets.discard(tf)
                    break

        # 3. Substring match
        if match is None:
            for tf in target_fields:
                if tf not in remaining_targets:
                    continue
                aliases = _TARGET_ALIASES.get(tf, [])
                for alias in aliases + [tf]:
                    norm_alias = _normalise(alias)
                    if norm_alias and (norm_alias in norm_source or norm_source in norm_alias):
                        match = ColumnMatch(source_col, tf, "substring", 0.7)
                        remaining_targets.discard(tf)
                        break
                if match:
                    break

        # 4. No match
        if match is None:
            match = ColumnMatch(source_col, "", "non_match", 0.0)

        results.append(match)

    return results


# ---------------------------------------------------------------------------
# Data inspection
# ---------------------------------------------------------------------------

def inspect_data(rows: list[dict[str, str]]) -> dict[str, Any]:
    """
    Inspect a list of dicts and return a report useful for import UI.

    Returns:
        {
            "total_rows": int,
            "matched_columns": [ColumnMatch, ...],       # matched only
            "unmatched_columns": [ColumnMatch, ...],      # non_match only
            "missing_required": [str],                    # required fields with no match
            "sample_rows": [dict, ...]                    # first 3 rows
        }
    """
    if not rows:
        return {
            "total_rows": 0,
            "matched_columns": [],
            "unmatched_columns": [],
            "missing_required": _REQUIRED_FIELDS.copy(),
            "sample_rows": [],
        }

    # Get all source columns from first row
    source_columns = list(rows[0].keys())
    matches = _fuzzy_match(source_columns)

    matched = [m for m in matches if m.strategy != "non_match"]
    unmatched = [m for m in matches if m.strategy == "non_match"]

    matched_targets = {m.target_field for m in matched}
    missing_required = [f for f in _REQUIRED_FIELDS if f not in matched_targets]

    return {
        "total_rows": len(rows),
        "matched_columns": matched,
        "unmatched_columns": unmatched,
        "missing_required": missing_required,
        "sample_rows": rows[:3],
    }


# ---------------------------------------------------------------------------
# Import execution
# ---------------------------------------------------------------------------

def import_data(
    rows: list[dict[str, str]],
    tenant_id: int | None = None,
    user: str = "system",
) -> dict[str, Any]:
    """
    Import data rows as Lead records.

    Steps:
      1. Inspect data to determine column mapping
      2. For each row, build a Lead and log an activity
      3. Commit all to DB

    Returns:
        {
            "imported": int,
            "errors": [str],
            "lead_ids": [int],
        }
    """
    report = inspect_data(rows)

    imported = 0
    errors: list[str] = []
    lead_ids: list[int] = []

    for idx, row in enumerate(rows):
        try:
            lead = Lead(
                source=LeadSource.API.value if tenant_id else LeadSource.MANUAL.value,
                code=next_inquiry_code(db.session),
                status="new",
                created_at=datetime.utcnow(),
            )

            # Apply matched columns
            for match in report["matched_columns"]:
                value = row.get(match.source_column, "").strip()
                if value:
                    setattr(lead, match.target_field, value)

            db.session.add(lead)
            db.session.flush()  # get lead.id

            # Log activity
            log = ActivityLog(
                lead_id=lead.id,
                action="imported",
                detail=f"Imported via data import from {'tenant' if tenant_id else 'manual'} source",
                user=user,
            )
            db.session.add(log)
            lead_ids.append(lead.id)
            imported += 1

        except Exception as exc:
            db.session.rollback()
            errors.append(f"Row {idx}: {exc}")

    if not errors:
        db.session.commit()

    return {
        "imported": imported,
        "errors": errors,
        "lead_ids": lead_ids,
    }