"""SHUNYA M8 — Executive Intelligence Routes.

FDA9+FDA10 integrated: tenant identity continuity, company-first truth,
evidence lineage, execution authority, inference governance, paid governance.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from flask import Blueprint, jsonify, request, session, g

intelligence_bp = Blueprint("intelligence", __name__, url_prefix="/api/v1/intelligence")

logger = logging.getLogger(__name__)


def _resolve_tenant() -> dict:
    """Resolve tenant identity from session or header context."""
    identity_id = (
        session.get("identity_id")
        or session.get("user_id")
        or getattr(g, "identity_id", None)
        or request.headers.get("X-Identity-Id")
    )
    tenant_id = (
        session.get("current_org_id")
        or request.headers.get("X-Tenant-Id")
    )
    return {
        "identity_id": str(identity_id) if identity_id else None,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "authenticated": bool(identity_id and tenant_id),
    }


def _founder_required() -> bool:
    return bool(session.get("user_id") or session.get("identity_id"))


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
# Ask — FDA9+FDA10 integrated canonical intelligence path
# ---------------------------------------------------------------------------

@intelligence_bp.route("/ask", methods=["POST"])
def api_ask():
    """Canonical intelligence query — FDA9+FDA10 integrated.

    Pipeline:
        HTTP request → tenant identity → company-first truth
        → evidence lineage → execution authority → inference governance
        → response

    The existing business data queries (leads, invoices, cash flow, etc.)
    are preserved as COMPANY_TRUTH evidence. Internet results are EXTERNAL_EVIDENCE.
    All paths route through the canonical InferenceOrchestrator.
    """
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"success": False, "error": "Question is required."}), 400

    tenant = _resolve_tenant()
    start = time.monotonic()
    pipeline_stages = []
    evidence_used = []

    # ── Stage 1: Tenant Identity ────────────────────────────────────
    stage_start = time.monotonic()
    if not tenant["authenticated"]:
        return jsonify({
            "success": False, "error": "Tenant identity required",
            "tenant": tenant,
        }), 401
    pipeline_stages.append({
        "stage": "tenant_identity", "status": "verified",
        "tenant_id": tenant["tenant_id"],
        "identity_id": tenant["identity_id"],
        "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
    })

    # ── Stage 2: Company Evidence / Company-First Truth ─────────────
    stage_start = time.monotonic()
    query_lower = question.lower()
    company_evidence = []
    has_company_data = False

    from app import db as _db
    from sqlalchemy import text as _text

    # Gather business context (company-first truth)
    try:
        total_objects = _db.session.execute(
            _text("SELECT COUNT(*) FROM founder_objects WHERE status='active'")
        ).scalar() or 0
        if total_objects > 0:
            company_evidence.append({
                "content": f"Total objects: {total_objects}",
                "source": "company_db/founder_objects",
                "classification": "company_truth",
                "confidence": 0.95,
            })
    except Exception:
        pass

    # Financial data
    try:
        from app.finance.models import FinInvoice as Invoice, FinancePayment as Payment
        invoice_count = _db.session.query(Invoice).count() if hasattr(Invoice, '__table__') else 0
        if invoice_count > 0:
            company_evidence.append({
                "content": f"Invoices: {invoice_count}",
                "source": "company_db/fin_invoices",
                "classification": "company_truth",
                "confidence": 0.95,
            })
    except Exception:
        pass

    try:
        from app.models import Lead
        lead_count = _db.session.query(Lead).count() if hasattr(Lead, '__table__') else 0
        if lead_count > 0:
            company_evidence.append({
                "content": f"Leads: {lead_count}",
                "source": "company_db/leads",
                "classification": "company_truth",
                "confidence": 0.95,
            })
    except Exception:
        pass

    # ── Stage 3: Evidence Assembly ──────────────────────────────────
    stage_start = time.monotonic()
    evidence_used = list(company_evidence)
    has_company_data = len(company_evidence) > 0
    pipeline_stages.append({
        "stage": "evidence_assembly",
        "status": "success",
        "company_evidence_count": len(company_evidence),
        "has_company_data": has_company_data,
        "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
    })

    # ── Stage 4: Intent Classification ──────────────────────────────
    stage_start = time.monotonic()
    from core.inference_governance import CapabilityBasedRouter
    from core.inference_orchestrator import get_orchestrator
    orch = get_orchestrator()
    available_raw = orch.execution_layer.get_available_providers()
    available = [p.get("name", "").lower() for p in available_raw if isinstance(p, dict)]
    available = [n for n in available if n]

    # Check if this is a deterministic-only query (no model needed)
    text = question.lower().strip()
    deterministic_response = None
    simple_greetings = {"hello", "hi", "hey", "good morning", "good evening", "good afternoon"}
    simple_farewells = {"bye", "goodbye", "see you", "see ya"}
    simple_thanks = {"thanks", "thank you", "thank you!"}

    if text in simple_greetings:
        deterministic_response = "Hello! I'm SHUNYA, your business intelligence engine. How can I help you today?"
    elif text in simple_farewells:
        deterministic_response = "Goodbye! Feel free to come back anytime."
    elif text in simple_thanks:
        deterministic_response = "You're welcome! Let me know if you need anything else."

    if deterministic_response:
        pipeline_stages.append({
            "stage": "intent_classification", "status": "deterministic",
            "model_invoked": False,
            "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
        })
        total_latency = round((time.monotonic() - start) * 1000, 1)
        return jsonify({
            "success": True,
            "answer": deterministic_response,
            "deterministic": True,
            "model_invoked": False,
            "tenant": tenant,
            "evidence_used": evidence_used,
            "pipeline": pipeline_stages,
            "latency_ms": total_latency,
        })

    pipeline_stages.append({
        "stage": "intent_classification", "status": "success",
        "model_invoked": True,
        "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
    })

    # ── Stage 5: Inference Governance ───────────────────────────────
    stage_start = time.monotonic()
    from core.inference_governance import InferenceGovernanceService, \
        DeterministicResponseTemplates, ProviderCostRegistry

    # Check deterministic templates for common patterns
    det_templates = DeterministicResponseTemplates()
    det_response = det_templates.get_response("help", question)
    if det_response:
        total_latency = round((time.monotonic() - start) * 1000, 1)
        return jsonify({
            "success": True,
            "answer": det_response,
            "deterministic": True,
            "model_invoked": False,
            "tenant": tenant,
            "evidence_used": evidence_used,
            "pipeline": pipeline_stages,
            "latency_ms": total_latency,
        })

    # Route through capability-based routing
    route = CapabilityBasedRouter.route(
        query=question,
        available_providers=available,
        paid_enabled=True,  # Default: paid enabled for production
    )

    # Check if paid is needed but blocked
    if route.get("paid_blocked"):
        total_latency = round((time.monotonic() - start) * 1000, 1)
        return jsonify({
            "success": False,
            "error": "The requested capability requires paid inference, which is currently disabled.",
            "route": route,
            "tenant": tenant,
            "evidence_used": evidence_used,
            "pipeline": pipeline_stages,
            "latency_ms": total_latency,
        }), 403

    pipeline_stages.append({
        "stage": "inference_governance", "status": "success",
        "capability": route.get("capability", "chat"),
        "suggested_provider": route.get("suggested_provider", ""),
        "cost_class": route.get("required_cost_class", ""),
        "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
    })

    # ── Stage 6: Execute through canonical orchestrator ─────────────
    stage_start = time.monotonic()
    try:
        # Build context from company evidence
        context_parts = [e["content"] for e in company_evidence]
        context = ". ".join(context_parts) if context_parts else "No business data found yet."

        # Use orchestrator with governance hint
        orch = get_orchestrator()
        from core.inference_orchestrator import OrchestratorRequest

        # Build system prompt with company-first context
        system_prompt = (
            f"You are SHUNYA, an AI assistant for a business. "
            f"Current business context: {context}\n\n"
            f"Guidelines:\n"
            f"- Answer business questions using the provided context where possible.\n"
            f"- If company data is insufficient, you may use general knowledge.\n"
            f"- Be honest about what you know and don't know.\n"
            f"- Be concise, helpful, and friendly.\n"
        )

        request_obj = OrchestratorRequest(
            input_text=question,
            session_id=tenant.get("identity_id", ""),
            system_prompt=system_prompt,
            provider_hint=route.get("suggested_provider", ""),
        )
        orch_response = orch.process(request_obj)

        pipeline_stages.append({
            "stage": "inference_execution", "status": "success" if orch_response.success else "error",
            "provider": orch_response.provider or "",
            "model": orch_response.model or "",
            "latency_ms": round(orch_response.latency_ms, 1),
            "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
        })

        answer = orch_response.content or "I don't have sufficient information to answer this."

    except Exception as exc:
        logger.warning("Inference execution failed: %s", exc)
        pipeline_stages.append({
            "stage": "inference_execution", "status": "error",
            "error": str(exc),
            "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
        })
        # Fallback: safe failure with company context
        if company_evidence:
            answer = "I found your business data but couldn't process your question. Please try rephrasing."
        else:
            answer = "I'm having trouble processing your request right now. Please try again."

    total_latency = round((time.monotonic() - start) * 1000, 1)

    return jsonify({
        "success": True,
        "answer": answer,
        "deterministic": False,
        "model_invoked": True,
        "tenant": tenant,
        "evidence_used": evidence_used,
        "routing": route,
        "pipeline": pipeline_stages,
        "latency_ms": total_latency,
    })


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