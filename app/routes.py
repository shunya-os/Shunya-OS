from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from app import db
from app.models import Lead, Payment, Supplier, Invoice, ItineraryRef, next_inquiry_code
from app.services import parse_inquiry_text, get_summary, _cached_or_new_code
from datetime import datetime
import os, pdfkit

main = Blueprint('main', __name__)
api = Blueprint('api', __name__)

def _flash_if_error(obj):
    try:
        db.session.add(obj)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(str(e), 'error')
        return None
    flash('Saved successfully', 'success')
    return obj

# -------------------- Dashboard --------------------

@main.route('/')
def index():
    s = get_summary('today')
    from app.models import Lead
    recent = Lead.query.order_by(Lead.created_at.desc()).limit(8).all()
    return render_template('dashboard.html', summary=s, recent=recent)

# -------------------- Leads --------------------

@main.route('/leads')
def leads_list():
    q = request.args.get('q','')
    from app.models import Lead
    query = Lead.query
    if q:
        query = query.filter((Lead.code.contains(q)) | (Lead.destination.contains(q)) | (Lead.customer_name.contains(q)))
    leads = query.order_by(Lead.created_at.desc()).limit(200).all()
    return render_template('leads.html', leads=leads, q=q)

@main.route('/leads/new', methods=['GET','POST'])
def lead_new():
    if request.method == 'POST':
        f = request.form
        with db.session.no_autoflush:
            code = _cached_or_new_code(db.session)
        lead = Lead(
            code=code,
            source=f.get('source','telegram'),
            customer_name=f.get('customer_name'),
            phone=f.get('phone'),
            destination=f.get('destination'),
            pax=f.get('pax'),
            dates=f.get('dates'),
            notes=f.get('notes'),
            status=f.get('status','new')
        )
        _flash_if_error(lead)
        return redirect(url_for('main.leads_list'))
    code = _cached_or_new_code(db.session)
    return render_template('lead_form.html', code=code)

@main.route('/leads/<int:lead_id>')
def lead_detail(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    return render_template('lead_detail.html', lead=lead)

@main.route('/leads/<int:lead_id>/delete', methods=['POST'])
def lead_delete(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    db.session.delete(lead)
    db.session.commit()
    flash('Lead deleted', 'success')
    return redirect(url_for('main.leads_list'))

# -------------------- Payments --------------------

@main.route('/payments', methods=['GET','POST'])
def payments():
    if request.method == 'POST':
        f = request.form
        p = Payment(
            lead_id=int(f['lead_id']) if f.get('lead_id') else None,
            type=f.get('type','guest_payment'),
            amount=f.get('amount') or 0,
            method=f.get('method'),
            ref_number=f.get('ref_number'),
            notes=f.get('notes')
        )
        _flash_if_error(p)
        return redirect(url_for('main.payments'))
    from app.models import Lead
    payments = Payment.query.order_by(Payment.paid_at.desc()).limit(200).all()
    leads = Lead.query.order_by(Lead.created_at.desc()).limit(300).all()
    return render_template('payments.html', payments=payments, leads=leads)

@main.route('/payments/<int:payment_id>/delete', methods=['POST'])
def payment_delete(payment_id):
    p = Payment.query.get_or_404(payment_id)
    db.session.delete(p)
    db.session.commit()
    flash('Payment deleted', 'success')
    return redirect(url_for('main.payments'))

# -------------------- Invoices --------------------

@main.route('/invoices', methods=['GET','POST'])
def invoices():
    if request.method == 'POST':
        f = request.form
        total = float(f.get('total_amount') or 0)
        tax = float(f.get('tax') or 0)
        discount = float(f.get('discount') or 0)
        grand_total = total + tax - discount
        inv = Invoice(
            lead_id=int(f.get('lead_id')) if f.get('lead_id') else None,
            invoice_number=f.get('invoice_number'),
            total_amount=total,
            tax=tax,
            discount=discount,
            grand_total=grand_total,
            status=f.get('status','draft'),
            currency=f.get('currency','INR')
        )
        db.session.add(inv)
        db.session.commit()
        try:
            os.makedirs('invoices', exist_ok=True)
            inv.pdf_path = os.path.join('invoices', f"{inv.id}_{inv.invoice_number}.pdf")
            _generate_invoice_pdf(inv.id, inv.pdf_path)
            db.session.commit()
            flash(f'Invoice {inv.invoice_number} created with PDF', 'success')
        except Exception as e:
            flash(f'Invoice saved but PDF failed: {e}', 'error')
        return redirect(url_for('main.invoices'))
    from app.models import Lead
    invoices = Invoice.query.order_by(Invoice.raised_at.desc()).limit(200).all()
    leads = Lead.query.order_by(Lead.created_at.desc()).limit(300).all()
    return render_template('invoices.html', invoices=invoices, leads=leads)

@main.route('/invoices/<int:invoice_id>/pdf')
def invoice_pdf(invoice_id):
    inv = Invoice.query.get_or_404(invoice_id)
    if not inv.pdf_path or not os.path.exists(inv.pdf_path):
        try:
            os.makedirs('invoices', exist_ok=True)
            inv.pdf_path = os.path.join('invoices', f"{inv.id}_{inv.invoice_number}.pdf")
            _generate_invoice_pdf(inv.id, inv.pdf_path)
            db.session.commit()
        except Exception as e:
            flash(f'PDF generation failed: {e}', 'error')
            return redirect(url_for('main.invoices'))
    return send_from_directory(os.path.dirname(os.path.abspath(inv.pdf_path)), os.path.basename(inv.pdf_path), as_attachment=True)

def _generate_invoice_pdf(invoice_id, path):
    inv = Invoice.query.get(invoice_id)
    lead = inv.lead
    html = f"""
    <html><head><meta charset='utf-8'><style>
      body{{font-family:Arial,sans-serif;color:#111}}
      h1{{color:#2563eb}}
      table{{width:100%;border-collapse:collapse}}
      td,th{{border:1px solid #e5e7eb;padding:8px}}
    </style></head><body>
      <h1>Invoice {inv.invoice_number}</h1>
      <p>Raised At: {inv.raised_at.strftime('%d-%m-%Y %H:%M')}</p>
      <p>Status: {inv.status} | Currency: {inv.currency}</p>
      <h3>Customer</h3>
      <p>{lead.customer_name if lead else '-'}<br>{lead.phone if lead else ''}<br>{lead.destination if lead else ''}</p>
      <h3>Amounts</h3>
      <table><tr><th>Total</th><td>₹{inv.total_amount:.2f}</td></tr><tr><th>Tax</th><td>₹{inv.tax:.2f}</td></tr><tr><th>Discount</th><td>₹{inv.discount:.2f}</td></tr><tr><th>Grand Total</th><td><strong>₹{inv.grand_total:.2f}</strong></td></tr></table>
    </body></html>
    """
    pdfkit.from_string(html, path)

# -------------------- Reports --------------------

@main.route('/reports')
def reports():
    from app.models import Lead, Payment
    from sqlalchemy import func, extract
    # Monthly lead counts for current year
    current_year = datetime.utcnow().year
    monthly_leads = db.session.query(extract('month', Lead.created_at).label('m'), func.count(Lead.id)).\
        filter(extract('year', Lead.created_at) == current_year).\
        group_by('m').all() if False else []
    # destination counts
    dest_counts = db.session.query(Lead.destination, func.count(Lead.id)).\
        filter(Lead.destination != None, Lead.destination != '').\
        group_by(Lead.destination).order_by(func.count(Lead.id).desc()).limit(15).all()
    # month totals
    month_revenue = db.session.query(extract('month', Payment.paid_at).label('m'), func.sum(Payment.amount)).\
        filter(Payment.type=='guest_payment', extract('year', Payment.paid_at) == current_year).group_by('m').all() if False else []
    return render_template('reports.html',
                           dest_counts=dest_counts,
                           monthly_leads=monthly_leads,
                           month_revenue=month_revenue,
                           year=current_year)

# -------------------- Settings / Suppliers --------------------

@main.route('/settings', methods=['GET','POST'])
def settings():
    if request.method == 'POST':
        f = request.form
        s = Supplier(
            name=f['name'],
            category=f.get('category'),
            contact=f.get('contact'),
            email=f.get('email'),
            phone=f.get('phone'),
            city=f.get('city'),
            notes=f.get('notes')
        )
        _flash_if_error(s)
        return redirect(url_for('main.settings'))
    suppliers = Supplier.query.order_by(Supplier.created_at.desc()).limit(200).all()
    return render_template('settings.html', suppliers=suppliers)

# -------------------- Telegram webhook & Bot endpoints --------------------

@main.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    from app.services import parse_inquiry_text
    payload = request.get_json(silent=True) or {}
    message = payload.get('message') or {}
    text = str(message.get('text') or payload.get('text') or '')
    chat = message.get('chat') or payload.get('chat') or {}
    sender = str(chat.get('id') or payload.get('from', {}).get('id') or '')
    if not text:
        return jsonify({'status':'ignored'}), 200
    parsed = parse_inquiry_text(text)
    with db.session.no_autoflush:
        code = _cached_or_new_code(db.session)
    lead = Lead(
        code=code,
        source='telegram',
        customer_name=parsed.get('name') or sender,
        phone=sender,
        destination=parsed.get('destination'),
        pax=f"{parsed.get('adults') or 0} adults, {parsed.get('kids') or 0} kids" if parsed.get('adults') or parsed.get('kids') else None,
        dates=parsed.get('dates'),
        notes=text,
        status='new'
    )
    db.session.add(lead)
    db.session.commit()
    # Minimal confirmation back to Telegram
    reply = {
        'method': 'sendMessage',
        'chat_id': sender,
        'text': f"✅ Inquiry logged: {code}\nDestination: {parsed.get('destination') or 'N/A'}\nDates: {parsed.get('dates') or 'N/A'}"
    }
    return jsonify(reply), 200

@main.route('/telegram/setup', methods=['POST'])
def telegram_setup():
    f = request.form
    token = f.get('bot_token')
    if not token:
        flash('Bot token required', 'error')
        return redirect(url_for('main.settings'))
    # Store token safely in environment/config for webhook registration
    try:
        from app.services import save_telegram_token
        save_telegram_token(token)
        flash('Telegram bot token saved. Use /telegram/setwebhook to register.', 'success')
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('main.settings'))

@main.route('/telegram/setwebhook', methods=['POST'])
def telegram_setwebhook():
    from app.services import get_telegram_token, set_telegram_webhook
    token = get_telegram_token()
    if not token:
        flash('No Telegram bot token configured. Save it in Settings first.', 'error')
        return redirect(url_for('main.settings'))
    host = request.host_url.rstrip('/')
    url = f"{host}/telegram/webhook"
    ok, data = set_telegram_webhook(token, url)
    if ok:
        flash(f'Telegram webhook set: {url}', 'success')
    else:
        flash(f'Webhook setup failed: {data}', 'error')
    return redirect(url_for('main.settings'))

# -------------------- Shunya Pipeline API --------------------

@api.route('/shunya/process', methods=['POST'])
def shunya_process():
    """Process a customer inquiry through Knowledge → Reasoning → Planner → Workflow."""
    data = request.get_json(silent=True) or {}
    inquiry = {
        "customer_name": data.get("customer_name", ""),
        "destination": data.get("destination", ""),
        "pax": data.get("pax", ""),
        "dates": data.get("dates", ""),
        "notes": data.get("notes", ""),
        "phone": data.get("phone", ""),
        "source": data.get("source", "api"),
    }
    from app.shunya import WorkflowLayer
    wf = WorkflowLayer(db.session)
    result = wf.process_inquiry(inquiry)
    if result.success() and data.get("create_lead"):
        lead_id = wf.create_lead_from_inquiry(inquiry)
        result.lead_id = lead_id
    return jsonify(result.to_dict())

@api.route('/shunya/knowledge', methods=['GET'])
def shunya_knowledge():
    """Get knowledge base summary."""
    from app.shunya import KnowledgeLayer
    k = KnowledgeLayer(db.session)
    return jsonify({
        "knowledge_base_length": len(k.get_knowledge_base_text()),
        "past_itineraries": k.get_past_itineraries(limit=5),
    })

@api.route('/shunya/summary', methods=['GET'])
def shunya_summary():
    """Get pipeline summary for dashboard."""
    from app.shunya import WorkflowLayer
    wf = WorkflowLayer(db.session)
    summary = wf.get_lead_status_summary(db.session)
    return jsonify(summary)

@api.route('/shunya/proposal/<int:lead_id>', methods=['GET'])
def shunya_proposal(lead_id):
    """Generate a proposal for an existing lead."""
    lead = Lead.query.get_or_404(lead_id)
    inquiry = {
        "customer_name": lead.customer_name or "",
        "destination": lead.destination or "",
        "pax": lead.pax or "",
        "dates": lead.dates or "",
        "notes": lead.notes or "",
        "phone": lead.phone or "",
    }
    from app.shunya import WorkflowLayer
    wf = WorkflowLayer(db.session)
    result = wf.process_inquiry(inquiry)
    if result.success():
        return jsonify({
            "lead_code": lead.code,
            "proposal": result.proposal_text,
            "itinerary": result.plan.to_dict() if result.plan else None,
        })
    return jsonify({"error": result.errors}), 400
