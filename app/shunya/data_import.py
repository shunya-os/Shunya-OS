"""Shunya OS — Universal Data Import (simplest form).

Upload CSV/JSON → pick entity type → fuzzy match columns → bulk create entities.
No AI needed — Shunya OS already knows the schema from the vertical template.

Flow:
1. User picks an entity type (Lead, Patient, Case, Booking...)
2. User uploads CSV or pastes JSON array
3. System inspects columns, matches to entity schema fields
4. Shows mapping preview + confidence scores
5. User confirms → bulk create entities
"""
import csv, io, json, re, logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ColumnMatch:
    """A matched column from input data to an entity schema field."""
    column: str           # original column name from input
    field_name: str       # matched entity schema field name
    field_label: str      # matched entity schema field label
    confidence: float     # 0.0 - 1.0


@dataclass
class ImportPreview:
    """Preview of what will be imported."""
    entity_type: str
    entity_label: str
    total_rows: int
    matched_columns: list[ColumnMatch]      # matched fields
    unmatched_columns: list[str]            # columns not matched
    sample_rows: list[dict]                 # first 3 rows for preview
    missing_required: list[str]             # required fields not in input


def _normalize(name: str) -> str:
    """Normalize a name for fuzzy matching: lowercase, strip, remove special chars."""
    return re.sub(r'[^a-z0-9]', '', name.lower().strip())


def _fuzzy_match(column: str, schema_fields: list[dict]) -> Optional[ColumnMatch]:
    """Try to match a column name to a schema field using various strategies."""
    col_norm = _normalize(column)
    if not col_norm:
        return None
    
    best = None
    best_score = 0.0
    
    for field in schema_fields:
        fname = field.get("name", "")
        flabel = field.get("label", "")
        ftype = field.get("type", "text")
        
        field_norms = [_normalize(fname), _normalize(flabel)]
        
        for fn in field_norms:
            if not fn:
                continue
            
            # Strategy 1: exact match
            if col_norm == fn:
                return ColumnMatch(column, fname, flabel, 1.0)
            
            # Strategy 2: starts-with
            if col_norm.startswith(fn) or fn.startswith(col_norm):
                score = 0.9 * (min(len(col_norm), len(fn)) / max(len(col_norm), len(fn)))
                if score > best_score:
                    best_score = score
                    best = ColumnMatch(column, fname, flabel, round(score, 2))
            
            # Strategy 3: substring match
            if fn in col_norm or col_norm in fn:
                ratio = min(len(col_norm), len(fn)) / max(len(col_norm), len(fn))
                score = 0.7 * ratio
                if score > best_score:
                    best_score = score
                    best = ColumnMatch(column, fname, flabel, round(score, 2))
            
            # Strategy 4: partial word match
            col_words = set(col_norm.split())
            field_words = set(fn.split())
            common = col_words & field_words
            if common:
                score = 0.6 * (len(common) / max(len(col_words | field_words), 1))
                if score > best_score:
                    best_score = score
                    best = ColumnMatch(column, fname, flabel, round(score, 2))
    
    return best


def inspect_data(
    data_rows: list[dict],
    entity_type: str,
    schema: list[dict],
    entity_label: str = ""
) -> ImportPreview:
    """Inspect incoming data and match columns to entity schema fields."""
    if not data_rows:
        return ImportPreview(entity_type, entity_label or entity_type, 0, [], [], [], [])
    
    # Get all column names from data
    all_columns = set()
    for row in data_rows:
        all_columns.update(row.keys())
    all_columns = sorted(all_columns)
    
    # Match each column to schema fields
    matched = []
    unmatched = []
    matched_fields = set()
    
    for col in all_columns:
        match = _fuzzy_match(col, schema)
        if match and match.confidence >= 0.3:  # lower threshold, user confirms
            matched.append(match)
            matched_fields.add(match.field_name)
        else:
            unmatched.append(col)
    
    # Find missing required fields
    missing_required = []
    for field in schema:
        if field.get("required") and field["name"] not in matched_fields:
            missing_required.append(f"{field['label']} ({field['name']})")
    
    sample = data_rows[:3]
    
    return ImportPreview(
        entity_type=entity_type,
        entity_label=entity_label or entity_type,
        total_rows=len(data_rows),
        matched_columns=sorted(matched, key=lambda m: m.confidence, reverse=True),
        unmatched_columns=unmatched,
        sample_rows=sample,
        missing_required=missing_required,
    )


def import_data(
    data_rows: list[dict],
    entity_type: str,
    schema: list[dict],
    tenant_id: int,
    definition_id: int,
    field_mapping: dict[str, str],  # {column_name: schema_field_name}
    user_id: int,
    db_session,
) -> dict:
    """Import validated data into entities. Returns import summary."""
    from app.models import Entity, ActivityLog, next_entity_code
    
    imported = 0
    errors = []
    
    for i, row in enumerate(data_rows):
        try:
            # Map columns to schema fields
            entity_data = {}
            for col, fname in field_mapping.items():
                val = row.get(col)
                if val is not None and val != "":
                    entity_data[fname] = val
            
            # Generate entity code
            code = next_entity_code(db_session, tenant_id, entity_type)
            
            # Get status from schema (first status = default)
            statuses = [f.get("options", ["new"])[0] for f in schema if f.get("name") == "status"]
            status = statuses[0] if statuses else "new"
            
            entity = Entity(
                tenant_id=tenant_id,
                definition_id=definition_id,
                code=code,
                status=status,
                data=entity_data,
                created_by=user_id,
            )
            db_session.add(entity)
            db_session.flush()
            
            # Log activity
            activity = ActivityLog(
                tenant_id=tenant_id,
                entity_id=entity.id,
                user_id=user_id,
                action="imported",
                detail=f"Imported via bulk upload ({entity_type})",
            )
            db_session.add(activity)
            imported += 1
            
        except Exception as e:
            errors.append(f"Row {i+1}: {str(e)}")
    
    db_session.commit()
    
    return {
        "imported": imported,
        "errors": errors,
        "entity_type": entity_type,
    }


def parse_csv(text: str) -> list[dict]:
    """Parse CSV text into list of dicts."""
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def parse_json(text: str) -> list[dict]:
    """Parse JSON array string into list of dicts."""
    data = json.loads(text)
    if isinstance(data, dict):
        # Try to find the array
        for v in data.values():
            if isinstance(v, list):
                return v
        return [data]
    return data