"""SHUNYA M8 — Executive Intelligence Routes.

Reasoning traces, learning feedback, anomaly detection, confidence scoring.
"""
from flask import Blueprint, jsonify, request, session

intelligence_bp = Blueprint("intelligence", __name__, url_prefix="/api/v1/intelligence")


def _founder_required() -> bool:
    user_id = session.get("user_id")
    identity_id = session.get("identity_id")
    return bool(user_id and identity_id)


# ---------------------------------------------------------------------------
# Reasoning Traces
# ---------------------------------------------------------------------------

@intelligence_bp.route("/traces", methods=["GET"])
def api_list_traces():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    object_id = request.args.get("object_id")
    from app.intelligence.service import get_traces
    traces = get_traces(identity_id=identity_id, object_id=object_id)
    return jsonify({"success": True, "data": traces})


@intelligence_bp.route("/traces/<trace_id>", methods=["GET"])
def api_get_trace(trace_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.intelligence.service import get_trace
    trace = get_trace(trace_id=trace_id)
    if not trace:
        return jsonify({"success": False, "error": "Trace not found"}), 404
    return jsonify({"success": True, "data": trace})


@intelligence_bp.route("/traces/<trace_id>/correct", methods=["POST"])
def api_correct_trace(trace_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    corrected = data.get("corrected_response", "").strip()
    if not corrected:
        return jsonify({"success": False, "error": "corrected_response required"}), 400
    from app.intelligence.service import correct_trace
    result = correct_trace(trace_id=trace_id, corrected_response=corrected)
    return jsonify({"success": result})


# ---------------------------------------------------------------------------
# Learning
# ---------------------------------------------------------------------------

@intelligence_bp.route("/learning", methods=["GET"])
def api_learning_history():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.intelligence.service import get_learning_history
    history = get_learning_history(identity_id=identity_id)
    return jsonify({"success": True, "data": history})


@intelligence_bp.route("/learning/summary", methods=["GET"])
def api_learning_summary():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.intelligence.service import get_learning_summary
    summary = get_learning_summary(identity_id=identity_id)
    return jsonify({"success": True, "data": summary})


# ---------------------------------------------------------------------------
# Anomalies
# ---------------------------------------------------------------------------

@intelligence_bp.route("/anomalies", methods=["GET"])
def api_list_anomalies():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    status = request.args.get("status", "open")
    from app.intelligence.service import get_anomalies
    anomalies = get_anomalies(identity_id=identity_id, status=status)
    return jsonify({"success": True, "data": anomalies})


@intelligence_bp.route("/anomalies/detect", methods=["POST"])
def api_detect_anomalies():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.intelligence.service import detect_anomalies
    anomalies = detect_anomalies(identity_id=identity_id)
    return jsonify({"success": True, "data": anomalies, "count": len(anomalies)})


@intelligence_bp.route("/anomalies/<int:anomaly_id>/resolve", methods=["POST"])
def api_resolve_anomaly(anomaly_id: int):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.intelligence.service import resolve_anomaly
    result = resolve_anomaly(anomaly_id=anomaly_id)
    return jsonify({"success": result})


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

@intelligence_bp.route("/confidence", methods=["POST"])
def api_confidence():
    """Compute confidence score from provided context."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    from app.intelligence.service import compute_confidence
    result = compute_confidence(data)
    return jsonify({"success": True, "data": result})


# ---------------------------------------------------------------------------
# Ask — natural language queries about the business
# ---------------------------------------------------------------------------


@intelligence_bp.route("/ask", methods=["POST"])
def api_ask():
    """Answer a natural language question about the user's business data."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"success": False, "error": "Question is required."}), 400

    identity_id = session.get("identity_id")
    org_id = session.get("current_org_id")

    # Gather business context for the AI
    from app import db as _db
    from sqlalchemy import text as _text, func
    from app.models import Lead, Organization, Proposal
    from app.finance.models import FinInvoice as Invoice, FinancePayment as Payment
    from datetime import datetime, timedelta

    summary_parts = []

    # Object counts
    try:
        total_objects = _db.session.execute(
            _text("SELECT COUNT(*) FROM founder_objects WHERE status='active'")
        ).scalar() or 0
        summary_parts.append(f"Total objects: {total_objects}")
    except Exception:
        pass

    # Lead count
    try:
        lead_count = _db.session.query(Lead).count() if hasattr(Lead, '__table__') else 0
        summary_parts.append(f"Leads: {lead_count}")
    except Exception:
        pass

    # Proposal count
    try:
        proposal_count = _db.session.query(Proposal).count() if hasattr(Proposal, '__table__') else 0
        summary_parts.append(f"Proposals: {proposal_count}")
    except Exception:
        pass

    # Invoice count
    try:
        invoice_count = _db.session.query(Invoice).count() if hasattr(Invoice, '__table__') else 0
        summary_parts.append(f"Invoices: {invoice_count}")
    except Exception:
        pass

    # Payment count
    try:
        payment_count = _db.session.query(Payment).count() if hasattr(Payment, '__table__') else 0
        summary_parts.append(f"Payments: {payment_count}")
    except Exception:
        pass

    context = ". ".join(summary_parts) if summary_parts else "No business data found yet."

    # Formulate answer based on question keywords
    query_lower = question.lower()

    # ── Financial Aggregation ──
    if "cash flow" in query_lower or "cashflow" in query_lower:
        try:
            total_invoiced = _db.session.execute(
                _text("SELECT COALESCE(SUM(total_amount),0) FROM fin_invoices WHERE status IN ('posted','paid')")
            ).scalar() or 0
            total_paid = _db.session.execute(
                _text("SELECT COALESCE(SUM(amount),0) FROM fin_payments WHERE type='receipt'")
            ).scalar() or 0
            total_spent = _db.session.execute(
                _text("SELECT COALESCE(SUM(amount),0) FROM fin_payments WHERE type='supplier_payment'")
            ).scalar() or 0
            outstanding = total_invoiced - total_paid
            answer = f"Your cash flow: ${total_paid:,.2f} collected (${total_invoiced:,.2f} invoiced), ${total_spent:,.2f} spent, ${outstanding:,.2f} outstanding."
        except Exception:
            answer = f"Your system has {invoice_count if 'invoice_count' in dir() else 0} invoice(s) and {payment_count if 'payment_count' in dir() else 0} payment(s)."

    elif "expense" in query_lower or "spending" in query_lower:
        try:
            expense_count = _db.session.execute(
                _text("SELECT COUNT(*) FROM founder_objects WHERE object_type IN ('expense','Expense') AND status='active'")
            ).scalar() or 0
            total_expense = _db.session.execute(
                _text("SELECT COALESCE(SUM(amount),0) FROM fin_payments WHERE type='supplier_payment'")
            ).scalar() or 0
            answer = f"Your total expenses: ${total_expense:,.2f} across {expense_count} expense record(s)."
        except Exception:
            answer = f"Found expense data in your system."

    elif "profit" in query_lower or "revenue" in query_lower or "income" in query_lower:
        try:
            total_revenue = _db.session.execute(
                _text("SELECT COALESCE(SUM(amount),0) FROM fin_payments WHERE type='receipt'")
            ).scalar() or 0
            total_expense_calc = _db.session.execute(
                _text("SELECT COALESCE(SUM(amount),0) FROM fin_payments WHERE type='supplier_payment'")
            ).scalar() or 0
            profit = total_revenue - total_expense_calc
            answer = f"Your profit: ${profit:,.2f} (${total_revenue:,.2f} revenue - ${total_expense_calc:,.2f} expenses)."
        except Exception:
            answer = f"Revenue: Your system has payments recorded."

    elif "conversation" in query_lower or "interaction" in query_lower or "timeline" in query_lower:
        try:
            convs = _db.session.execute(
                _text("SELECT name, created_at FROM founder_objects WHERE object_type IN ('conversation','Conversation') AND status='active' ORDER BY created_at DESC LIMIT 10")
            ).fetchall()
            if convs:
                details = "; ".join([f"{r[0]} ({r[1].strftime('%b %d') if r[1] else 'unknown'})" for r in convs])
                answer = f"Recent conversations: {details}."
            else:
                answer = "No conversations found in your workspace."
        except Exception:
            answer = "I could not retrieve conversation data."

    elif "lead" in query_lower and "customer" not in query_lower or "prospect" in query_lower:
        try:
            leads = _db.session.query(Lead).order_by(Lead.created_at.desc()).limit(5).all() if hasattr(Lead, '__table__') else []
            if leads:
                lead_details = "; ".join([f"{l.customer_name} (ID {l.id})" for l in leads])
                answer = f"You have {len(leads)} recent leads: {lead_details}."
            else:
                answer = "You don't have any leads yet. Try creating one with the /create command."
        except Exception:
            answer = f"I found {lead_count if 'lead_count' in dir() else 0} lead(s) in your system."
    elif "invoice" in query_lower or "bill" in query_lower:
        try:
            invoices = _db.session.query(Invoice).order_by(Invoice.created_at.desc()).limit(5).all() if hasattr(Invoice, '__table__') else []
            if invoices:
                inv_details = "; ".join([f"{i.client_name} — ${i.amount}" for i in invoices])
                answer = f"Recent invoices: {inv_details}."
            else:
                answer = "No invoices found."
        except Exception:
            answer = f"Your system has {invoice_count if 'invoice_count' in dir() else 0} invoice(s)."
    elif "proposal" in query_lower or "quote" in query_lower:
        try:
            proposals = _db.session.query(Proposal).order_by(Proposal.created_at.desc()).limit(5).all() if hasattr(Proposal, '__table__') else []
            if proposals:
                prop_details = "; ".join([f"{p.title} ({p.status})" for p in proposals])
                answer = f"Recent proposals: {prop_details}."
            else:
                answer = "No proposals found."
        except Exception:
            answer = f"Found {proposal_count if 'proposal_count' in dir() else 0} proposal(s)."
    elif "hello" in query_lower or "hi" in query_lower or "hey" in query_lower:
        answer = f"Hello! I'm SHUNYA, your business intelligence engine. {context} How can I help you today?"
    elif "help" in query_lower or "what can you" in query_lower:
        answer = f"I can help you understand your business data. {context} Try asking about your leads, invoices, proposals, or use /create to make new objects."
    else:
            # Determine if query needs internet (real-time / current info)
            internet_keywords = ['weather', 'movie', 'restaurant', 'hotel', 'flight', 'news', 'today',
                                 'current', 'playing now', 'near me', 'forecast', 'traffic', 'price',
                                 'stock', 'cricket', 'score', 'election', 'covid', 'booking', 'open now']
            needs_internet = any(kw in query_lower for kw in internet_keywords) or \
                             any(kw in question.lower() for kw in ['today', 'now', 'latest', 'trending'])

            # Try internet search first if needed
            internet_result = None
            if needs_internet:
                try:
                    from app.search.provider import resolve_search_provider
                    search_provider = resolve_search_provider()
                    results = search_provider.search(question, max_results=5)
                    if results:
                        internet_result = "\n".join([
                            f"- {r.get('title','')}: {r.get('body','')[:200]}"
                            for r in results if r.get('body')
                        ])
                except Exception:
                    pass

            # Use AI provider — with internet context if available
            try:
                from app.ai.provider import resolve_provider
                provider = resolve_provider()
                if provider:
                    if internet_result:
                        system_prompt = f"""You are a helpful AI assistant integrated into SHUNYA. You help founders with both business and general questions.

Current business context: {context}

I searched the internet and found this relevant information:
{internet_result}

Answer the user's question using this internet-sourced information where relevant. Cite sources briefly. Be concise and friendly."""
                    else:
                        system_prompt = f"""You are a helpful AI assistant integrated into SHUNYA. You help founders with both business and general questions.

Current business context: {context}

Guidelines:
- Answer business questions using the provided context where possible
- Answer general knowledge questions based on your training data up to your knowledge cutoff
- Be honest about what you know and don't know
- Be concise, helpful, and friendly"""

                    resp = provider.complete([
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ], temperature=0.3, max_tokens=600)
                    answer = resp.get("content", "").strip()
                    if not answer:
                        answer = f"I see {context}. For specific details, try asking about your leads, invoices, proposals, or recent activity."
                else:
                    answer = f"I see {context}. For specific details, try asking about your leads, invoices, proposals, or recent activity."
            except Exception:
                answer = f"I see {context}. For specific details, try asking about your leads, invoices, proposals, or recent activity."

    return jsonify({"success": True, "answer": answer})


# ---------------------------------------------------------------------------
# AI Image Generation — forward to OpenRouter image model
# ---------------------------------------------------------------------------


@intelligence_bp.route("/generate-image", methods=["POST"])
def api_generate_image():
    """Generate an image from a text prompt using OpenRouter's image model."""
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"success": False, "error": "Prompt is required."}), 400

    import os, requests

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        return jsonify({"success": False, "error": "OpenRouter API key not configured."}), 500

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("APP_URL", "https://shunyaos.app"),
        "X-Title": "SHUNYA OS",
    }

    body = {
        "model": "openai/gpt-5.4-image-2",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=120,
        )
        data = resp.json()

        if resp.status_code != 200:
            err = data.get("error", {}).get("message", str(resp.status_code))
            return jsonify({"success": False, "error": f"OpenRouter error: {err}"}), resp.status_code

        choices = data.get("choices", [])
        if not choices:
            return jsonify({"success": False, "error": "No choices returned from OpenRouter."}), 502

        message = choices[0].get("message", {})
        content = message.get("content", "")

        # The image URL may be in content or in the message's attachments
        image_url = content.strip() if content else ""

        # Fallback: check for image_url in the assistant message structure
        if not image_url:
            for part in message.get("content_parts") or []:
                if isinstance(part, dict) and part.get("type") == "image_url":
                    image_url = part.get("image_url", {}).get("url", "")
                    break

        if not image_url:
            return jsonify({"success": False, "error": "No image URL in the response."}), 502

        return jsonify({
            "success": True,
            "data": {
                "image_url": image_url,
                "prompt": prompt,
            },
        })

    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "OpenRouter request timed out."}), 504
    except Exception as e:
        return jsonify({"success": False, "error": f"Image generation failed: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# Mixed Intelligence Router
# ---------------------------------------------------------------------------

@intelligence_bp.route("/mixed", methods=["POST"])
def api_mixed_intelligence():
    """Answer using business data → internet → AI synthesis with source labels."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"success": False, "error": "Question is required."}), 400

    identity_id = session.get("identity_id")
    org_id = data.get("org_id") or session.get("current_org_id")

    from app.intelligence.mixed_router import get_router
    router = get_router()
    response = router.answer(question, identity_id=identity_id, org_id=org_id)
    return jsonify({"success": True, "data": response.to_dict()})