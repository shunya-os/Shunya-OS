"""Entity export utilities — CSV and JSON (PDF placeholder)."""

import csv
import io
from datetime import datetime


def export_csv(entity_type: str, entities: list, schema: list) -> str:
    """Generate CSV string for a list of entities.

    Headers: Code, Status, Created, [schema field labels...]
    Rows:    entity.code, entity.status, entity.created_at, entity.data[field.name] for each field
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Build headers — fixed columns first, then dynamic schema fields
    headers = ["Code", "Status", "Created"]
    field_names = []
    for field in (schema or []):
        name = field.get("name", "")
        label = field.get("label", name)
        headers.append(label)
        field_names.append(name)

    writer.writerow(headers)

    # Write rows
    for entity in entities:
        created = ""
        if entity.created_at:
            if isinstance(entity.created_at, datetime):
                created = entity.created_at.isoformat()
            else:
                created = str(entity.created_at)

        row = [
            entity.code or "",
            entity.status or "",
            created,
        ]
        data = entity.data or {}
        for fname in field_names:
            val = data.get(fname, "")
            # Ensure string representation
            if val is None:
                val = ""
            elif not isinstance(val, str):
                val = str(val)
            row.append(val)

        writer.writerow(row)

    return output.getvalue()


def export_json(entity_type: str, entities: list, schema: list) -> list:
    """Return entities as a list of dicts suitable for JSON serialization.

    This is the lightweight alternative to PDF generation — the caller
    can jsonify this list directly.
    """
    field_names = [f.get("name", "") for f in (schema or [])]
    field_labels = [f.get("label", f.get("name", "")) for f in (schema or [])]

    rows = []
    for entity in entities:
        created = ""
        if entity.created_at:
            if isinstance(entity.created_at, datetime):
                created = entity.created_at.isoformat()
            else:
                created = str(entity.created_at)

        data = entity.data or {}
        row = {
            "code": entity.code or "",
            "status": entity.status or "",
            "created_at": created,
        }
        # Add schema fields under their labels for readability
        for fname, flabel in zip(field_names, field_labels):
            val = data.get(fname, "")
            if val is None:
                val = ""
            elif not isinstance(val, str):
                val = str(val)
            row[flabel] = val
        rows.append(row)

    return rows