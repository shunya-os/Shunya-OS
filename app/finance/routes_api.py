"""FOR-2D: Finance Intelligence — API Routes."""
from datetime import date
from decimal import Decimal
import json, os
from flask import jsonify, request, session, send_file
from app import db
from app.finance import finance_bp
from app.finance.models import Account, FinInvoice as Invoice, InvoiceItem
from app.finance.models import FinancePayment as Payment, TaxProfile
from app.finance.models import JournalEntry, LedgerEntry, Budget
from app.finance.accounting import seed_default_accounts, create_journal_entry, get_trial_balance
from app.finance.services import create_invoice_from_proposal, record_payment
from app.finance.services import get_receivables_aging, get_financial_summary
from app.finance.governance import transition_invoice, create_credit_note, validate_transition, INVOICE_STATES
from app.finance.controls import (
    ApprovalRequest, ApprovalAction, Delegation, FinancialPeriod,
    request_approval, resolve_approval, create_delegation, revoke_delegation,
    transition_period, get_audit_dashboard, get_ai_governance_insights,
    find_approval_policy, DEFAULT_APPROVAL_POLICIES, SOD_RULES,
)
from app.finance.intelligence import (
    executive_cfo_workspace, cash_flow_forecast, overall_profitability,
    profitability_by_relationship, profitability_by_proposal, lifetime_value,
    risk_engine, opportunity_engine, scenario_model, cfo_explain,
)
from app.finance.evidence import (
    FinancialEvidence, EvidencePolicy, EVIDENCE_STATUS,
    check_evidence_policy, transition_evidence, extract_evidence_intelligence,
    _store_file, STORAGE_ROOT,
)
def _get_file_path(rel_path):
    import os
    return os.path.join(STORAGE_ROOT, rel_path)

from app.finance.models import LedgerEntry


def _identity():
    return session.get("identity_id") or session.get("user_id") or ""

def _require_auth():
    uid = _identity()
    if not uid: return jsonify({"error": "Auth required"}), 401
    return None

def _org():
    return session.get("current_org_id")

@finance_bp.route("/seed", methods=["POST"])
def api_seed_accounts():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    seed_default_accounts(org_id)
    accounts = Account.query.filter_by(organization_id=org_id).all()
    return jsonify({"success": True, "accounts": [a.to_dict() for a in accounts]})

@finance_bp.route("/accounts", methods=["GET"])
def api_list_accounts():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    accounts = Account.query.filter_by(organization_id=org_id).order_by(Account.code).all()
    return jsonify({"accounts": [a.to_dict() for a in accounts]})

@finance_bp.route("/invoices", methods=["POST"])
def api_create_invoice():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    data = request.get_json(silent=True) or {}
    proposal_id = data.get("proposal_id")
    if proposal_id:
        result = create_invoice_from_proposal(org_id, proposal_id, created_by=_identity())
        if "error" in result: return jsonify(result), 400
        return jsonify(result), 201
    return jsonify({"error": "proposal_id required"}), 400

@finance_bp.route("/invoices", methods=["GET"])
def api_list_invoices():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    status = request.args.get("status", "")
    q = Invoice.query.filter_by(organization_id=org_id)
    if status: q = q.filter_by(status=status)
    return jsonify({"invoices": [inv.to_dict() for inv in q.order_by(Invoice.created_at.desc()).all()]})

@finance_bp.route("/invoices/<int:inv_id>", methods=["GET"])
def api_get_invoice(inv_id):
    auth = _require_auth()
    if auth: return auth
    inv = db.session.get(Invoice, inv_id)
    if not inv or inv.organization_id != _org(): return jsonify({"error": "Not found"}), 404
    items = InvoiceItem.query.filter_by(invoice_id=inv_id).all()
    return jsonify({"invoice": inv.to_dict(), "items": [i.to_dict() for i in items]})

@finance_bp.route("/payments", methods=["GET"])
def api_payment_list():
    """List recent payments (JSON API)."""
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    limit = request.args.get("limit", 20, type=int)
    payments = Payment.query.order_by(Payment.created_at.desc()).limit(limit).all()
    return jsonify({"payments": [{
        "id": p.id, "invoice_id": p.invoice_id, "amount": float(p.amount),
        "method": p.payment_method or p.method or "bank_transfer",
        "created_at": p.created_at.isoformat() if p.created_at else None,
    } for p in payments]})


@finance_bp.route("/payments", methods=["POST"])
def api_record_payment():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    data = request.get_json(silent=True) or {}
    result = record_payment(org_id, data.get("invoice_id"),
        Decimal(str(data.get("amount", 0))),
        date.fromisoformat(data.get("payment_date", date.today().isoformat())),
        method=data.get("method", ""), reference=data.get("reference", ""), created_by=_identity())
    if "error" in result: return jsonify(result), 400
    return jsonify(result), 201

@finance_bp.route("/trial-balance", methods=["GET"])
def api_trial_balance():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    as_of = request.args.get("as_of")
    as_of_date = date.fromisoformat(as_of) if as_of else None
    return jsonify({"trial_balance": get_trial_balance(org_id, as_of_date)})

@finance_bp.route("/summary", methods=["GET"])
def api_financial_summary():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    summary = get_financial_summary(org_id)
    aging = get_receivables_aging(org_id)
    return jsonify({"summary": summary, "aging": aging})

@finance_bp.route("/journal-entries", methods=["POST"])
def api_create_journal():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    data = request.get_json(silent=True) or {}
    result = create_journal_entry(org_id,
        date.fromisoformat(data.get("entry_date", date.today().isoformat())),
        data.get("lines", []), description=data.get("description", ""),
        type=data.get("type", "general"), created_by=_identity())
    if "error" in result: return jsonify(result), 400
    return jsonify(result), 201

# ── Governance Routes ──────────────────────────────────────────────────

@finance_bp.route("/invoices/<int:inv_id>/transition", methods=["POST"])
def api_transition_invoice(inv_id):
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    data = request.get_json(silent=True) or {}
    result = transition_invoice(inv_id, data.get("status", ""), org_id, _identity(), reason=data.get("reason", ""))
    if "error" in result: return jsonify(result), 400
    return jsonify(result)

@finance_bp.route("/invoices/<int:inv_id>/credit-note", methods=["POST"])
def api_create_credit_note(inv_id):
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    data = request.get_json(silent=True) or {}
    result = create_credit_note(org_id, inv_id, data.get("reason", ""), created_by=_identity())
    if "error" in result: return jsonify(result), 400
    return jsonify(result), 201

@finance_bp.route("/states/<obj_type>", methods=["GET"])
def api_list_states(obj_type):
    """List valid states and transitions for an object type."""
    if obj_type == "invoice":
        return jsonify({"states": {k: {"label": v["label"], "transitions": v["next"]} for k, v in INVOICE_STATES.items()}})
    return jsonify({"error": "Unknown type"}), 400

@finance_bp.route("/invoices/<int:inv_id>/history", methods=["GET"])
def api_invoice_history(inv_id):
    """Get full correction history for an invoice."""
    auth = _require_auth()
    if auth: return auth
    inv = db.session.get(Invoice, inv_id)
    if not inv or inv.organization_id != _org(): return jsonify({"error": "Not found"}), 404
    # Find related credit notes and replacement invoices
    cn = Invoice.query.filter_by(organization_id=inv.organization_id,
        proposal_id=inv.proposal_id, type="credit_note").all()
    replacements = Invoice.query.filter_by(organization_id=inv.organization_id,
        proposal_id=inv.proposal_id).filter(Invoice.id != inv_id).all()
    ledger = LedgerEntry.query.filter_by(reference_type="invoice", reference_id=inv_id).all()
    return jsonify({
        "invoice": inv.to_dict(),
        "credit_notes": [c.to_dict() for c in cn],
        "related_invoices": [r.to_dict() for r in replacements],
        "ledger_entries": [l.to_dict() for l in ledger],
    })

# ── Governance Control Routes ──────────────────────────────────────────

@finance_bp.route("/approval-policies", methods=["GET"])
def api_approval_policies():
    return jsonify({"policies": DEFAULT_APPROVAL_POLICIES, "sod_rules": SOD_RULES})

@finance_bp.route("/approval-requests", methods=["POST"])
def api_request_approval():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    data = request.get_json(silent=True) or {}
    result = request_approval(org_id, data.get("doc_type",""), data.get("doc_id"), data.get("amount",0), _identity(), data.get("reason",""))
    return jsonify(result), (400 if "error" in result else 201)

@finance_bp.route("/approval-requests", methods=["GET"])
def api_list_approvals():
    auth = _require_auth()
    if auth: return auth
    status = request.args.get("status", "")
    q = ApprovalRequest.query.filter_by(organization_id=_org())
    if status: q = q.filter_by(status=status)
    return jsonify({"approval_requests": [ar.to_dict() for ar in q.order_by(ApprovalRequest.requested_at.desc()).limit(20).all()]})

@finance_bp.route("/approval-requests/<int:ar_id>/resolve", methods=["POST"])
def api_resolve_approval(ar_id):
    auth = _require_auth()
    if auth: return auth
    data = request.get_json(silent=True) or {}
    result = resolve_approval(ar_id, _org(), _identity(), data.get("action",""), data.get("note",""))
    if "error" in result: return jsonify(result), 400
    return jsonify(result)

@finance_bp.route("/delegations", methods=["POST"])
def api_create_delegation():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    data = request.get_json(silent=True) or {}
    import datetime
    sd = datetime.date.fromisoformat(data.get("start_date", datetime.date.today().isoformat()))
    ed = datetime.date.fromisoformat(data.get("end_date", datetime.date.today().isoformat()))
    result = create_delegation(org_id, data.get("delegator",""), data.get("delegate",""),
        data.get("role",""), sd, ed, data.get("scope","all"), data.get("reason",""))
    return jsonify(result), (400 if "error" in result else 201)

@finance_bp.route("/delegations", methods=["GET"])
def api_list_delegations():
    q = Delegation.query.filter_by(organization_id=_org())
    return jsonify({"delegations": [d.to_dict() for d in q.order_by(Delegation.created_at.desc()).limit(20).all()]})

@finance_bp.route("/delegations/<int:d_id>/revoke", methods=["POST"])
def api_revoke_delegation(d_id):
    result = revoke_delegation(d_id, _org(), _identity())
    if "error" in result: return jsonify(result), 400
    return jsonify(result)

@finance_bp.route("/periods", methods=["POST"])
def api_create_period():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    data = request.get_json(silent=True) or {}
    import datetime
    p = FinancialPeriod(organization_id=org_id, name=data["name"], year=data.get("year", datetime.date.today().year),
        start_date=datetime.date.fromisoformat(data["start_date"]), end_date=datetime.date.fromisoformat(data["end_date"]))
    db.session.add(p); db.session.commit()
    return jsonify({"period": p.to_dict()}), 201

@finance_bp.route("/periods", methods=["GET"])
def api_list_periods():
    q = FinancialPeriod.query.filter_by(organization_id=_org()).order_by(FinancialPeriod.start_date.desc())
    return jsonify({"periods": [p.to_dict() for p in q.all()]})

@finance_bp.route("/periods/<int:p_id>/transition", methods=["POST"])
def api_transition_period(p_id):
    data = request.get_json(silent=True) or {}
    result = transition_period(p_id, _org(), data.get("status",""), _identity(), data.get("reason",""))
    if "error" in result: return jsonify(result), 400
    return jsonify(result)

@finance_bp.route("/audit-dashboard", methods=["GET"])
def api_audit_dashboard():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    return jsonify({"dashboard": get_audit_dashboard(org_id)})

@finance_bp.route("/audit-insights", methods=["GET"])
def api_audit_insights():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    return jsonify(get_ai_governance_insights(org_id))

# ── CFO Intelligence Routes ────────────────────────────────────────────

@finance_bp.route("/cfo/dashboard", methods=["GET"])
def api_cfo_dashboard():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    return jsonify({"cfo": executive_cfo_workspace(org_id)})

@finance_bp.route("/cfo/cash-flow", methods=["GET"])
def api_cfo_cash_flow():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    days = int(request.args.get("days", 180))
    return jsonify(cash_flow_forecast(org_id, days))

@finance_bp.route("/cfo/profitability", methods=["GET"])
def api_cfo_profitability():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    return jsonify({"overall": overall_profitability(org_id),
        "by_relationship": profitability_by_relationship(org_id),
        "by_proposal": profitability_by_proposal(org_id)})

@finance_bp.route("/cfo/lifetime-value", methods=["GET"])
def api_cfo_lifetime_value():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    rid = request.args.get("relationship_id")
    return jsonify({"lifetime_values": lifetime_value(org_id, int(rid) if rid else None)})

@finance_bp.route("/cfo/risks", methods=["GET"])
def api_cfo_risks():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    return jsonify(risk_engine(org_id))

@finance_bp.route("/cfo/opportunities", methods=["GET"])
def api_cfo_opportunities():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    return jsonify(opportunity_engine(org_id))

@finance_bp.route("/cfo/scenario", methods=["POST"])
def api_cfo_scenario():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    data = request.get_json(silent=True) or {}
    return jsonify(scenario_model(org_id, data.get("type",""), data.get("params",{})))

@finance_bp.route("/cfo/ask", methods=["POST"])
def api_cfo_ask():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    data = request.get_json(silent=True) or {}
    return jsonify(cfo_explain(org_id, data.get("question","")))

@finance_bp.route("/cfo/working-capital", methods=["GET"])
def api_cfo_working_capital():
    auth = _require_auth()
    if auth: return auth
    org_id = _org()
    if not org_id: return jsonify({"error": "No org"}), 400
    from app.finance.intelligence import compute_working_capital
    return jsonify(compute_working_capital(org_id))

# ── Evidence Routes ────────────────────────────────────────────────────

@finance_bp.route("/evidence/policies", methods=["POST"])
def api_create_evidence_policy():
    auth = _require_auth(); org_id = _org()
    if auth: return auth
    if not org_id: return jsonify({"error": "No org"}), 400
    data = request.get_json(silent=True) or {}
    p = EvidencePolicy(organization_id=org_id, doc_type=data["doc_type"],
        requirement=data.get("requirement", "optional"),
        condition=data.get("condition", ""), min_count=data.get("min_count", 0),
        allowed_types=json.dumps(data.get("allowed_types", [])),
        require_ocr=data.get("require_ocr", False))
    db.session.add(p); db.session.commit()
    return jsonify({"policy": p.to_dict()}), 201

@finance_bp.route("/evidence/policies", methods=["GET"])
def api_list_evidence_policies():
    org_id = _org()
    return jsonify({"policies": [p.to_dict() for p in EvidencePolicy.query.filter_by(organization_id=org_id).all()]})

@finance_bp.route("/evidence/upload/<ref_type>/<int:ref_id>", methods=["POST"])
def api_upload_evidence(ref_type, ref_id):
    auth = _require_auth(); org_id = _org()
    if auth: return auth
    if not org_id: return jsonify({"error": "No org"}), 400
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    rel_path, orig_name, mime = _store_file(f, org_id, ref_type, ref_id)
    ev = FinancialEvidence(organization_id=org_id, reference_type=ref_type,
        reference_id=ref_id, evidence_type="image" if mime.startswith("image/") else "pdf" if mime == "application/pdf" else "document",
        file_path=rel_path, original_filename=orig_name, mime_type=mime,
        file_size_bytes=os.path.getsize(os.path.join(STORAGE_ROOT, rel_path)),
        status="uploaded", notes=request.form.get("notes", ""), created_by=_identity())
    db.session.add(ev); db.session.flush()
    # AI intelligence extraction
    intelligence = extract_evidence_intelligence(orig_name, mime)
    ev.extracted_data = json.dumps(intelligence)
    ev.status = "ai_processed"
    from app.relationship.integration import record_event
    from app.finance.controls import get_system_rel
    sys_rel = get_system_rel(org_id)
    record_event(relationship_id=sys_rel.id, organization_id=org_id,
        event_type=f"evidence.uploaded",
        title=f"Evidence #{ev.id} uploaded for {ref_type}#{ref_id}",
        description=f"File: {orig_name}", reference_type="evidence", reference_id=ev.id, created_by=_identity())
    db.session.commit()
    return jsonify({"evidence": ev.to_dict(), "intelligence": intelligence}), 201

@finance_bp.route("/evidence/<int:ev_id>", methods=["GET"])
def api_get_evidence(ev_id):
    ev = db.session.get(FinancialEvidence, ev_id)
    if not ev or ev.organization_id != _org():
        return jsonify({"error": "Not found"}), 404
    return jsonify({"evidence": ev.to_dict()})

@finance_bp.route("/evidence/<int:ev_id>/file", methods=["GET"])
def api_get_evidence_file(ev_id):
    ev = db.session.get(FinancialEvidence, ev_id)
    if not ev or ev.organization_id != _org():
        return jsonify({"error": "Not found"}), 404
    return send_file(_get_file_path(ev.file_path), mimetype=ev.mime_type,
        as_attachment=False, download_name=ev.original_filename)

@finance_bp.route("/evidence/<int:ev_id>/transition", methods=["POST"])
def api_transition_evidence(ev_id):
    auth = _require_auth(); org_id = _org()
    if auth: return auth
    if not org_id: return jsonify({"error": "No org"}), 400
    data = request.get_json(silent=True) or {}
    result = transition_evidence(ev_id, org_id, _identity(), data.get("status",""), data.get("note",""))
    if "error" in result: return jsonify(result), 400
    return jsonify(result)

@finance_bp.route("/evidence/<ref_type>/<int:ref_id>", methods=["GET"])
def api_list_evidence(ref_type, ref_id):
    org_id = _org(); status = request.args.get("status","")
    q = FinancialEvidence.query.filter_by(organization_id=org_id, reference_type=ref_type, reference_id=ref_id)
    if status: q = q.filter_by(status=status)
    return jsonify({"evidence": [e.to_dict() for e in q.order_by(FinancialEvidence.created_at.desc()).all()]})

@finance_bp.route("/evidence/check/<ref_type>/<int:ref_id>", methods=["GET"])
def api_check_evidence_policy(ref_type, ref_id):
    amount = float(request.args.get("amount", 0))
    return jsonify(check_evidence_policy(_org(), ref_type, ref_id, amount))