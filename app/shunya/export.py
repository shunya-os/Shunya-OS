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


def export_pdf(entities, schema, entity_label="Entity"):
    """Generate a PDF from entity data using wkhtmltopdf."""
    # Build HTML table
    field_names = [f["name"] for f in schema]
    field_labels = [f.get("label", f["name"]) for f in schema]

    rows_html = ""
    for e in entities:
        data = (
            e.get("data", {})
            if isinstance(e, dict)
            else (e.data if hasattr(e, "data") else {})
        )
        if data is None:
            data = {}
        code = e.get("code", "") if isinstance(e, dict) else getattr(e, "code", "")
        status = (
            e.get("status", "")
            if isinstance(e, dict)
            else getattr(e, "status", "")
        )
        rows_html += "<tr>"
        rows_html += f'<td style="padding:8px;border:1px solid #ddd;font-family:monospace;font-size:12px;">{code}</td>'
        rows_html += f'<td style="padding:8px;border:1px solid #ddd;font-size:12px;">{status}</td>'
        for fn in field_names:
            val = data.get(fn, "")
            rows_html += f'<td style="padding:8px;border:1px solid #ddd;font-size:12px;">{val}</td>'
        rows_html += "</tr>"

    headers_html = "".join(
        f'<th style="padding:8px;border:1px solid #ddd;background:#1e293b;color:white;font-size:12px;text-align:left;">{l}</th>'
        for l in ["Code", "Status"] + field_labels
    )

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      body {{ font-family: Inter, sans-serif; padding: 32px; }}
      h1 {{ color: #0f172a; font-size: 20px; margin-bottom: 4px; }}
      .meta {{ color: #64748b; font-size: 12px; margin-bottom: 24px; }}
      table {{ width: 100%; border-collapse: collapse; }}
    </style></head><body>
    <h1>{entity_label} Report</h1>
    <p class="meta">{len(entities)} records · Generated {__import__("datetime").datetime.utcnow().strftime("%d %b %Y")}</p>
    <table><thead><tr>{headers_html}</tr></thead><tbody>{rows_html}</tbody></table>
    </body></html>"""

    options = {
        "page-size": "A4",
        "margin-top": "15mm",
        "margin-right": "15mm",
        "margin-bottom": "15mm",
        "margin-left": "15mm",
        "encoding": "UTF-8",
        "enable-local-file-access": "",
    }

    try:
        import pdfkit

        pdf = pdfkit.from_string(html, False, options=options)
        return pdf
    except Exception:
        # Fallback: return simple PDF with fpdf2
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"{entity_label} Report", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, f"{len(entities)} records", ln=True)
        pdf.ln(10)
        for e in entities:
            data = (
                e.get("data", {})
                if isinstance(e, dict)
                else (e.data if hasattr(e, "data") else {})
            )
            if data is None:
                data = {}
            code = e.get("code", "") if isinstance(e, dict) else getattr(e, "code", "")
            pdf.cell(
                0,
                6,
                f'{code}: {" | ".join(str(data.get(fn, "")) for fn in field_names[:4])}',
                ln=True,
            )
        result = pdf.output(dest="S")
        return bytes(result)