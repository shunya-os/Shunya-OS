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
        or session.get("tenant_id")
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

    action = data.get("action", "").strip()
    execute = data.get("execute", False) or bool(action)

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
    evidence_semantic_states = set()

    # ── Stage 2.5: Safety Governance (age + explicit + injection) ────
    safety_start = time.monotonic()
    try:
        from app.shunya.safety_governance import check_safety_governance
        safety = check_safety_governance(
            text=question,
            identity_id=tenant.get("identity_id", ""),
            tenant_id=tenant.get("tenant_id", 0),
        )
        if not safety.allowed:
            total_latency = round((time.monotonic() - start) * 1000, 1)
            return jsonify({
                "success": False,
                "error": "Request blocked by SHUNYA safety policy",
                "safety": safety.to_dict(),
                "answer": "",
                "tenant": tenant,
                "pipeline": pipeline_stages + [{
                    "stage": "safety_governance",
                    "status": "blocked",
                    "reason": safety.reason,
                    "duration_ms": round((time.monotonic() - safety_start) * 1000, 1),
                }],
                "latency_ms": total_latency,
            }), 403
        pipeline_stages.append({
            "stage": "safety_governance",
            "status": "passed",
            "level": safety.level,
            "duration_ms": round((time.monotonic() - safety_start) * 1000, 1),
        })
    except Exception as exc:
        logger.warning("Safety governance check failed (fail-open disabled, blocking): %s", exc)
        total_latency = round((time.monotonic() - start) * 1000, 1)
        return jsonify({
            "success": False,
            "error": "Safety governance unavailable — request blocked",
            "answer": "",
            "tenant": tenant,
            "pipeline": pipeline_stages + [{
                "stage": "safety_governance",
                "status": "unavailable",
                "reason": str(exc),
                "duration_ms": round((time.monotonic() - safety_start) * 1000, 1),
            }],
            "latency_ms": total_latency,
        }), 503

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
                "semantic": "FACT",
                "classification": "company_truth",
                "confidence": 0.95,
            })
            evidence_semantic_states.add("FACT")
    except Exception as exc:
        logger.warning("Failed to query founder_objects: %s", exc)

    # Financial data
    try:
        from app.finance.models import FinInvoice as Invoice, FinancePayment as Payment
        invoice_count = _db.session.query(Invoice).count() if hasattr(Invoice, '__table__') else 0
        if invoice_count > 0:
            company_evidence.append({
                "content": f"Invoices: {invoice_count}",
                "source": "company_db/fin_invoices",
                "semantic": "FACT",
                "classification": "company_truth",
                "confidence": 0.95,
            })
            evidence_semantic_states.add("FACT")
    except Exception as exc:
        logger.warning("Failed to query invoices: %s", exc)

    try:
        from app.models import Lead
        lead_count = _db.session.query(Lead).count() if hasattr(Lead, '__table__') else 0
        if lead_count > 0:
            company_evidence.append({
                "content": f"Leads: {lead_count}",
                "source": "company_db/leads",
                "semantic": "FACT",
                "classification": "company_truth",
                "confidence": 0.95,
            })
            evidence_semantic_states.add("FACT")
    except Exception as exc:
        logger.warning("Failed to query leads: %s", exc)

    # If no company evidence found, mark semantic state as UNKNOWN
    if not has_company_data:
        evidence_semantic_states.add("UNKNOWN")

    # ── Stage 3: Evidence Assembly ──────────────────────────────────
    stage_start = time.monotonic()
    evidence_used = list(company_evidence)
    has_company_data = len(company_evidence) > 0
    pipeline_stages.append({
        "stage": "evidence_assembly",
        "status": "success",
        "company_evidence_count": len(company_evidence),
        "has_company_data": has_company_data,
        "semantic_states": sorted(evidence_semantic_states),
        "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
    })

    # ── Stage 4: Execution Authority — Active Enforcement ──────────
    stage_start = time.monotonic()
    from core.intelligence_runtime.cross_boundary import ExecutionAuthorityEnforcer

    # Classify evidence sources for authority check
    evidence_classifications = [e["classification"] for e in evidence_used]
    has_company_data = len(company_evidence) > 0

    # Check if evidence is from non-authoritative sources
    if evidence_classifications:
        all_non_auth = all(
            c in ExecutionAuthorityEnforcer.NON_AUTHORITY_CLASSIFICATIONS
            for c in evidence_classifications
        )

        if all_non_auth and not has_company_data:
            # Only non-authoritative evidence — execution authority denied
            if execute:
                total_latency = round((time.monotonic() - start) * 1000, 1)
                return jsonify({
                    "success": False,
                    "error": (
                        "Execution blocked: evidence only from non-authoritative "
                        "classifications. Execution requires company-confirmed "
                        "evidence through the canonical authorization path."
                    ),
                    "answer": "",
                    "tenant": tenant,
                    "evidence_used": evidence_used,
                    "pipeline": pipeline_stages + [{
                        "stage": "execution_authority",
                        "status": "denied",
                        "classification": "external_only",
                        "reason": "No authoritative evidence to authorize execution",
                        "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
                    }],
                    "latency_ms": total_latency,
                }), 403

            pipeline_stages.append({
                "stage": "execution_authority",
                "status": "note_only_external_evidence",
                "classification": "external_only",
                "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
            })
        else:
            pipeline_stages.append({
                "stage": "execution_authority",
                "status": "authorized",
                "company_evidence_present": has_company_data,
                "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
            })
    else:
        if execute:
            total_latency = round((time.monotonic() - start) * 1000, 1)
            return jsonify({
                "success": False,
                "error": (
                    "Execution blocked: no evidence available to authorize "
                    "execution. Provide company-confirmed evidence."
                ),
                "answer": "",
                "tenant": tenant,
                "evidence_used": evidence_used,
                "pipeline": pipeline_stages + [{
                    "stage": "execution_authority",
                    "status": "denied",
                    "reason": "No evidence to authorize execution",
                    "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
                }],
                "latency_ms": total_latency,
            }), 403

        pipeline_stages.append({
            "stage": "execution_authority",
            "status": "no_evidence",
            "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
        })

    # ── Stage 5: Inference Governance (deterministic-first + capability routing + orchestrator) ──
    stage_start = time.monotonic()
    from core.inference_governance import InferenceGovernanceService, reset_governance_service

    # Build company context for the system prompt
    context_parts = [e["content"] for e in company_evidence]
    context = ". ".join(context_parts) if context_parts else "No business data found yet."

    # Use InferenceGovernanceService as the canonical inference entry point
    gov_service = InferenceGovernanceService(paid_enabled=True)
    gov_result = gov_service.process(
        query=question,
        session_id=tenant.get("identity_id", ""),
        paid_allowed=True,
    )

    pipeline_stages.append({
        "stage": "inference_governance",
        "status": "deterministic" if gov_result.get("deterministic") else "model_invoked",
        "model_invoked": gov_result.get("model_invoked", False),
        "provider": gov_result.get("provider", ""),
        "model": gov_result.get("model", ""),
        "observability": gov_result.get("observability", {}),
        "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
    })

    total_latency = round((time.monotonic() - start) * 1000, 1)

    if gov_result.get("error"):
        return jsonify({
            "success": False,
            "error": gov_result["error"],
            "answer": "",
            "deterministic": gov_result.get("deterministic", False),
            "model_invoked": gov_result.get("model_invoked", False),
            "tenant": tenant,
            "evidence_used": evidence_used,
            "pipeline": pipeline_stages,
            "latency_ms": total_latency,
        }), 500 if gov_result.get("paid_blocked") else 200

    return jsonify({
        "success": True,
        "answer": gov_result.get("content", ""),
        "deterministic": gov_result.get("deterministic", False),
        "model_invoked": gov_result.get("model_invoked", False),
        "tenant": tenant,
        "evidence_used": evidence_used,
        "routing": gov_result.get("routing", {}),
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