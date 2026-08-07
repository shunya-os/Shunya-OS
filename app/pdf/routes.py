"""
WeasyPrint HTML→PDF Generator — free, unlimited PDF generation.

Replaces PandaDoc for PDF generation. Uses WeasyPrint to convert HTML to PDF
with full SHUNYA branding (gold/purple theme, elegant typography).

POST /api/v1/pdf/generate               — Render arbitrary HTML to PDF
GET  /api/v1/pdf/proposal/<proposal_id>  — Generate branded proposal PDF
GET  /api/v1/pdf/invoice/<invoice_id>   — Generate branded invoice PDF
"""
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file
from weasyprint import HTML

from app import db
from app.objects.legacy_models import ShunyaObject

logger = logging.getLogger(__name__)

pdf_bp = Blueprint("pdf", __name__, url_prefix="/api/v1/pdf")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_identity_id() -> str | None:
    """Extract the identity ID from request headers."""
    return request.headers.get("X-Identity-Id") or request.headers.get("X-User-Id")


def _build_proposal_html(proposal: ShunyaObject) -> str:
    """Build a beautifully branded HTML proposal document."""
    data = proposal.data or {}
    client_name = data.get("client_name", "Valued Client")
    title = data.get("proposal_title") or data.get("title") or "Proposal"
    amount = data.get("amount", 0)
    currency = data.get("currency", "USD")
    valid_until = data.get("valid_until", "")
    line_items = data.get("line_items", [])
    notes = data.get("notes", "")
    status = data.get("status", "draft")

    items_html = ""
    if line_items:
        rows = "\n".join(
            f"""<tr>
                <td>{item.get("description", "Item")}</td>
                <td style="text-align:center">{item.get("quantity", 1)}</td>
                <td style="text-align:right">{currency} {float(item.get("unit_price", 0)):,.2f}</td>
                <td style="text-align:right">{currency} {float(item.get("quantity", 1)) * float(item.get("unit_price", 0)):,.2f}</td>
            </tr>"""
            for item in line_items
        )
        items_html = f"""
        <table class="items-table">
            <thead>
                <tr>
                    <th>Description</th>
                    <th style="text-align:center">Qty</th>
                    <th style="text-align:right">Unit Price</th>
                    <th style="text-align:right">Total</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="3" style="text-align:right;font-weight:700">Total Amount</td>
                    <td style="text-align:right;font-weight:700;color:#C8A84E">{currency} {float(amount):,.2f}</td>
                </tr>
            </tfoot>
        </table>"""
    else:
        items_html = f"""
        <div style="text-align:center;padding:20px;background:#F9F7FC;border-radius:8px;margin:16px 0">
            <p style="margin:0;color:#6C4AE2;font-size:18px;font-weight:700">{currency} {float(amount):,.2f}</p>
        </div>"""

    status_badge = f"""<span style="display:inline-block;padding:4px 12px;border-radius:12px;font-size:11px;font-weight:600;text-transform:uppercase;background:#E8F5E9;color:#2E7D32">{status}</span>"""

    valid_until_html = ""
    if valid_until:
        valid_until_html = f"""<p style="margin:4px 0 0 0;font-size:11px;color:rgba(26,28,29,0.5)">Valid until: <strong>{valid_until}</strong></p>"""

    notes_html = ""
    if notes:
        notes_html = f"""<div style="margin-top:20px;padding:12px 16px;background:#F9F7FC;border-radius:8px;border-left:3px solid #C8A84E"><p style="margin:0;font-size:11px;color:rgba(26,28,29,0.6)"><strong>Notes:</strong> {notes}</p></div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
    @page {{
        size: A4;
        margin: 0.75in 0.6in;
        @bottom-center {{
            content: "Page " counter(page) " of " counter(pages);
            font-size: 9px;
            color: rgba(26,28,29,0.3);
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }}
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 11px;
        line-height: 1.5;
        color: #1A1C1D;
    }}
    .header {{
        display: flex; justify-content: space-between; align-items: flex-start;
        padding-bottom: 16px; border-bottom: 2px solid #6C4AE2; margin-bottom: 20px;
    }}
    .brand {{
        font-size: 22px; font-weight: 800; color: #6C4AE2; letter-spacing: -0.02em;
    }}
    .brand span {{ color: #C8A84E; }}
    .doc-meta {{ text-align: right; font-size: 10px; color: rgba(26,28,29,0.5); }}
    .doc-title {{ font-size: 20px; font-weight: 700; color: #1A1C1D; margin-bottom: 4px; }}
    .section {{ margin-bottom: 16px; }}
    .section-title {{ font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #6C4AE2; margin-bottom: 6px; }}
    .info-grid {{ display: flex; gap: 24px; }}
    .info-col {{ flex: 1; }}
    .info-col p {{ margin: 2px 0; font-size: 11px; }}
    .info-col .label {{ font-size: 9px; color: rgba(26,28,29,0.4); text-transform: uppercase; letter-spacing: 0.06em; }}
    .items-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
    .items-table th {{ background: #6C4AE2; color: #fff; padding: 8px 10px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; text-align: left; }}
    .items-table td {{ padding: 8px 10px; border-bottom: 1px solid rgba(26,28,29,0.06); font-size: 11px; }}
    .items-table tbody tr:nth-child(even) {{ background: #F9F7FC; }}
    .footer {{ margin-top: 30px; padding-top: 12px; border-top: 1px solid rgba(26,28,29,0.08); font-size: 9px; color: rgba(26,28,29,0.35); text-align: center; }}
    .qr-placeholder {{ width: 60px; height: 60px; border: 1px dashed rgba(26,28,29,0.15); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 8px; color: rgba(26,28,29,0.25); text-align: center; }}
</style>
</head>
<body>
    <div class="header">
        <div>
            <div class="brand">SHUNYA<span>OS</span></div>
            <div style="font-size:9px;color:rgba(26,28,29,0.35);margin-top:2px">Intelligent Operating System</div>
        </div>
        <div class="doc-meta">
            <div class="doc-title">Proposal</div>
            <p style="margin:2px 0">{title}</p>
            {status_badge}
            {valid_until_html}
        </div>
    </div>

    <div class="section">
        <div class="section-title">Client Information</div>
        <div class="info-grid">
            <div class="info-col">
                <p class="label">Client Name</p>
                <p>{client_name}</p>
            </div>
            <div class="info-col">
                <p class="label">Date</p>
                <p>{datetime.utcnow().strftime('%B %d, %Y')}</p>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Pricing Summary</div>
        {items_html}
    </div>

    {notes_html}

    <div class="section" style="margin-top:16px">
        <div class="section-title">QR Code</div>
        <div class="qr-placeholder">QR Placeholder</div>
    </div>

    <div class="footer">
        <p>SHUNYA OS — Intelligent Operating System</p>
        <p>This proposal was generated electronically and is valid until {valid_until or '30 days from issue'}.</p>
    </div>
</body>
</html>"""


def _build_invoice_html(invoice: ShunyaObject) -> str:
    """Build a beautifully branded HTML invoice document."""
    data = invoice.data or {}
    customer_name = data.get("customer_name", "Valued Customer")
    invoice_number = data.get("invoice_number", f"INV-{invoice.id}")
    amount = data.get("amount", 0)
    currency = data.get("currency", "USD")
    issue_date = data.get("issue_date", datetime.utcnow().strftime("%Y-%m-%d"))
    due_date = data.get("due_date", "")
    status = data.get("status", "draft")
    items = data.get("items", [])
    notes = data.get("notes", "")
    customer_email = data.get("customer_email", "")
    customer_address = data.get("customer_address", "")
    subtotal = data.get("subtotal", amount)
    tax_total = data.get("tax_total", 0)
    shipping = data.get("shipping", 0)
    grand_total = data.get("grand_total", amount)

    items_html = ""
    if items:
        rows = "\n".join(
            f"""<tr>
                <td>{item.get("description", "Item")}</td>
                <td style="text-align:center">{item.get("quantity", 1)}</td>
                <td style="text-align:right">{currency} {float(item.get("unit_price", 0)):,.2f}</td>
                <td style="text-align:right">{currency} {float(item.get("quantity", 1)) * float(item.get("unit_price", 0)):,.2f}</td>
            </tr>"""
            for item in items
        )
    else:
        rows = f"""<tr>
            <td>Services rendered</td>
            <td style="text-align:center">1</td>
            <td style="text-align:right">{currency} {float(amount):,.2f}</td>
            <td style="text-align:right">{currency} {float(amount):,.2f}</td>
        </tr>"""

    status_badge_style = "#E8F5E9;color:#2E7D32"
    if status.lower() in ("overdue", "past due"):
        status_badge_style = "#FFEBEE;color:#C62828"
    elif status.lower() in ("paid", "completed"):
        status_badge_style = "#E8F5E9;color:#2E7D32"
    elif status.lower() in ("draft", "pending"):
        status_badge_style = "#FFF8E1;color:#F57F17"

    notes_html = ""
    if notes:
        notes_html = f"""<div style="margin-top:20px;padding:12px 16px;background:#F9F7FC;border-radius:8px;border-left:3px solid #C8A84E"><p style="margin:0;font-size:11px;color:rgba(26,28,29,0.6)"><strong>Notes:</strong> {notes}</p></div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Invoice {invoice_number}</title>
<style>
    @page {{
        size: A4;
        margin: 0.75in 0.6in;
        @bottom-center {{
            content: "Page " counter(page) " of " counter(pages);
            font-size: 9px;
            color: rgba(26,28,29,0.3);
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }}
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 11px;
        line-height: 1.5;
        color: #1A1C1D;
    }}
    .header {{
        display: flex; justify-content: space-between; align-items: flex-start;
        padding-bottom: 16px; border-bottom: 2px solid #C8A84E; margin-bottom: 20px;
    }}
    .brand {{
        font-size: 22px; font-weight: 800; color: #6C4AE2; letter-spacing: -0.02em;
    }}
    .brand span {{ color: #C8A84E; }}
    .doc-meta {{ text-align: right; font-size: 10px; color: rgba(26,28,29,0.5); }}
    .doc-title {{ font-size: 20px; font-weight: 700; color: #1A1C1D; margin-bottom: 4px; }}
    .section {{ margin-bottom: 16px; }}
    .section-title {{ font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #6C4AE2; margin-bottom: 6px; }}
    .info-grid {{ display: flex; gap: 24px; }}
    .info-col {{ flex: 1; }}
    .info-col p {{ margin: 2px 0; font-size: 11px; }}
    .info-col .label {{ font-size: 9px; color: rgba(26,28,29,0.4); text-transform: uppercase; letter-spacing: 0.06em; }}
    .items-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
    .items-table th {{ background: #6C4AE2; color: #fff; padding: 8px 10px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; text-align: left; }}
    .items-table td {{ padding: 8px 10px; border-bottom: 1px solid rgba(26,28,29,0.06); font-size: 11px; }}
    .items-table tbody tr:nth-child(even) {{ background: #F9F7FC; }}
    .totals-table {{ width: 280px; margin-left: auto; border-collapse: collapse; }}
    .totals-table td {{ padding: 4px 8px; font-size: 11px; }}
    .totals-table .total-row td {{ font-weight: 700; font-size: 13px; color: #C8A84E; border-top: 2px solid #C8A84E; padding-top: 6px; }}
    .footer {{ margin-top: 30px; padding-top: 12px; border-top: 1px solid rgba(26,28,29,0.08); font-size: 9px; color: rgba(26,28,29,0.35); text-align: center; }}
    .bank-details {{ margin-top: 16px; padding: 12px 16px; background: #F9F7FC; border-radius: 8px; font-size: 10px; }}
    .bank-details p {{ margin: 1px 0; }}
</style>
</head>
<body>
    <div class="header">
        <div>
            <div class="brand">SHUNYA<span>OS</span></div>
            <div style="font-size:9px;color:rgba(26,28,29,0.35);margin-top:2px">Intelligent Operating System</div>
        </div>
        <div class="doc-meta">
            <div class="doc-title">INVOICE</div>
            <p style="margin:2px 0;font-size:12px"><strong>{invoice_number}</strong></p>
            <p style="margin:2px 0"><span style="display:inline-block;padding:4px 12px;border-radius:12px;font-size:11px;font-weight:600;text-transform:uppercase;background:{status_badge_style.split(';')[0]};color:{status_badge_style.split(';')[1].split(':')[1]}">{status}</span></p>
        </div>
    </div>

    <div class="section">
        <div class="info-grid">
            <div class="info-col">
                <p class="label">Bill To</p>
                <p style="font-size:12px;font-weight:600">{customer_name}</p>
                {f'<p>{customer_email}</p>' if customer_email else ''}
                {f'<p>{customer_address}</p>' if customer_address else ''}
            </div>
            <div class="info-col">
                <p class="label">Invoice Details</p>
                <p><strong>Issue Date:</strong> {issue_date}</p>
                {f'<p><strong>Due Date:</strong> {due_date}</p>' if due_date else ''}
                <p><strong>Currency:</strong> {currency}</p>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Line Items</div>
        <table class="items-table">
            <thead>
                <tr>
                    <th>Description</th>
                    <th style="text-align:center">Qty</th>
                    <th style="text-align:right">Unit Price</th>
                    <th style="text-align:right">Total</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>

        <table class="totals-table">
            <tr><td>Subtotal</td><td style="text-align:right">{currency} {float(subtotal):,.2f}</td></tr>
            {f'<tr><td>Tax</td><td style="text-align:right">{currency} {float(tax_total):,.2f}</td></tr>' if tax_total else ''}
            {f'<tr><td>Shipping</td><td style="text-align:right">{currency} {float(shipping):,.2f}</td></tr>' if shipping else ''}
            <tr class="total-row"><td>Total Due</td><td style="text-align:right">{currency} {float(grand_total):,.2f}</td></tr>
        </table>
    </div>

    {notes_html}

    <div class="section" style="margin-top:16px">
        <div class="section-title">Payment</div>
        <div style="display:flex;gap:16px;align-items:flex-start">
            <div class="qr-placeholder" style="width:80px;height:80px;border:1px dashed rgba(26,28,29,0.15);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:8px;color:rgba(26,28,29,0.25);text-align:center">Payment<br>QR Code</div>
            {f'<div class="bank-details" style="flex:1"><p><strong>Payment Link:</strong> {data.get("stripe_link", "Pay via payment link")}</p></div>' if not customer_address else '<div class="bank-details" style="flex:1"><p><strong>Online Payment:</strong> Pay via the payment link sent to your email.</p></div>'}
        </div>
    </div>

    <div class="footer">
        <p>SHUNYA OS — Intelligent Operating System</p>
        <p>Thank you for your business. Payment is due within {due_date or '30 days'}.</p>
    </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@pdf_bp.route("/generate", methods=["POST"])
def generate_pdf():
    """Generate a PDF from arbitrary HTML.

    Request JSON:
        html     (str) — Full HTML document string
        filename (str) — Output filename (default: document.pdf)
    """
    data = request.get_json(silent=True) or {}
    html_content = data.get("html")
    filename = data.get("filename", "document.pdf")

    if not html_content:
        return jsonify({"success": False, "error": "Missing required field: html"}), 400

    try:
        pdf_bytes = HTML(string=html_content).write_pdf() or b""
        from io import BytesIO
        pdf_io = BytesIO(pdf_bytes)
        pdf_io.seek(0)

        return send_file(
            pdf_io,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        logger.exception("PDF generation failed")
        return jsonify({"success": False, "error": str(e)}), 500


@pdf_bp.route("/proposal/<int:proposal_id>", methods=["GET"])
def generate_proposal_pdf(proposal_id: int):
    """Look up a proposal by ID, build branded HTML, return as PDF."""
    proposal = ShunyaObject.query.filter_by(
        id=proposal_id,
        object_type="proposal",
        is_deleted=False,
    ).first()

    if not proposal:
        return jsonify({"success": False, "error": "Proposal not found"}), 404

    try:
        html_content = _build_proposal_html(proposal)
        pdf_bytes = HTML(string=html_content).write_pdf() or b""
        from io import BytesIO
        pdf_io = BytesIO(pdf_bytes)
        pdf_io.seek(0)

        data = proposal.data or {}
        filename = f"proposal-{data.get('proposal_title', proposal.name).replace(' ', '-')}.pdf"

        return send_file(
            pdf_io,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        logger.exception("Proposal PDF generation failed")
        return jsonify({"success": False, "error": str(e)}), 500


@pdf_bp.route("/invoice/<int:invoice_id>", methods=["GET"])
def generate_invoice_pdf(invoice_id: int):
    """Look up an invoice by ID, build branded HTML, return as PDF."""
    invoice = ShunyaObject.query.filter_by(
        id=invoice_id,
        object_type="invoice",
        is_deleted=False,
    ).first()

    if not invoice:
        return jsonify({"success": False, "error": "Invoice not found"}), 404

    try:
        html_content = _build_invoice_html(invoice)
        pdf_bytes = HTML(string=html_content).write_pdf() or b""
        from io import BytesIO
        pdf_io = BytesIO(pdf_bytes)
        pdf_io.seek(0)

        data = invoice.data or {}
        inv_num = data.get("invoice_number", f"INV-{invoice.id}")
        filename = f"invoice-{inv_num}.pdf"

        return send_file(
            pdf_io,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        logger.exception("Invoice PDF generation failed")
        return jsonify({"success": False, "error": str(e)}), 500