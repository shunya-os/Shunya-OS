"""Canonical Cross-Boundary Intelligence API — FDA9 + FDA10.

This is THE canonical HTTP path for every cross-boundary intelligence request.

Pipeline:
    HTTP/API request
    → authentication (session/X-Identity-Id)
    → canonical route
    → CrossBoundaryIntelligenceService
    → retrieval
    → inference
    → response

No alternative path exists for cross-boundary intelligence.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, g, jsonify, request, session

from core.intelligence_runtime.cross_boundary import (
    TenantIdentity,
    EvidenceItem,
    EvidenceClassification,
    get_cross_boundary_service,
    reset_cross_boundary_service,
)

logger = logging.getLogger(__name__)

# Blueprint registered at /api/v1/intelligence
cb_bp = Blueprint("cross_boundary_intelligence", __name__, url_prefix="/api/v1/cross-boundary")


def _resolve_tenant_identity() -> TenantIdentity:
    """Resolve tenant identity from the current request context.

    Uses the unified auth middleware (g.identity_id) set by app/__init__.py.
    Falls back to session or header.
    """
    identity_id = (
        getattr(g, "identity_id", None)
        or session.get("identity_id")
        or session.get("user_id")
        or request.headers.get("X-Identity-Id")
    )
    tenant_id = (
        session.get("current_org_id")
        or request.headers.get("X-Tenant-Id")
    )

    return TenantIdentity(
        tenant_id=str(tenant_id) if tenant_id else None,
        identity_id=str(identity_id) if identity_id else None,
        auth_method="session" if session.get("user_id") else "header",
    )


def _validate_tenant_required() -> TenantIdentity | tuple:
    """Validate tenant identity is present. Returns TenantIdentity or error tuple."""
    identity = _resolve_tenant_identity()
    if not identity.is_authenticated:
        return jsonify({
            "error": "Tenant identity is required",
            "detail": "Provide X-Identity-Id header or X-Tenant-Id header, or be logged in",
            "code": "TENANT_REQUIRED",
        }), 401
    return identity


# ── Primary Query Endpoint ──────────────────────────────────────


@cb_bp.route("/ask", methods=["POST"])
def api_ask():
    """Canonical cross-boundary intelligence query.

    Exercises the full boundary chain:
    USER REQUEST → TENANT CONTEXT → COMPANY-FIRST TRUTH → EVIDENCE
    → REASONING → AUTHORIZATION → EXECUTION → OUTCOME → EVIDENCE → RESPONSE
    """
    # Validate tenant identity
    identity = _validate_tenant_required()
    if isinstance(identity, tuple):
        return identity

    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400

    # Extract optional parameters
    action = data.get("action")
    execute = data.get("execute", False)
    commitment_type = data.get("commitment_type")
    commitment_id = data.get("commitment_id")

    # Build evidence items from request
    company_evidence_raw = data.get("company_evidence", [])
    external_evidence_raw = data.get("external_evidence", [])

    company_evidence = []
    for ev in company_evidence_raw:
        company_evidence.append(EvidenceItem(
            content=ev.get("content", ""),
            source=ev.get("source", "company_db"),
            classification=EvidenceClassification.COMPANY_TRUTH,
            confidence=ev.get("confidence", 0.85),
            provenance=ev.get("provenance", {}),
        ))

    external_evidence = []
    for ev in external_evidence_raw:
        external_evidence.append(EvidenceItem(
            content=ev.get("content", ""),
            source=ev.get("source", "web_research"),
            classification=EvidenceClassification.EXTERNAL_EVIDENCE,
            confidence=ev.get("confidence", 0.4),
            provenance=ev.get("provenance", {"source": "web", "provider": ev.get("provider", "unknown")}),
        ))

    # Process through the cross-boundary service
    service = get_cross_boundary_service()
    result = service.process(
        query=query,
        tenant_identity=identity,
        action=action,
        commitment_type=commitment_type,
        commitment_id=commitment_id,
        company_evidence=company_evidence or None,
        external_evidence=external_evidence or None,
        execute=execute,
    )

    status_code = 200 if result.success else (403 if "authority" in (result.error or "").lower() or "blocked" in (result.error or "").lower() else 400)

    return jsonify({
        "success": result.success,
        "response": result.response,
        "error": result.error,
        "tenant_identity": result.tenant_identity,
        "intent": result.intent,
        "evidence_used": result.evidence_used,
        "authority_check": result.authority_check,
        "inference": result.inference,
        "pipeline": result.pipeline,
        "latency_ms": result.latency_ms,
        "request_id": result.request_id,
    }), status_code


# ── Tenant Verification Endpoint ────────────────────────────────


@cb_bp.route("/tenant-verify", methods=["POST"])
def api_tenant_verify():
    """Verify tenant isolation — prove cross-tenant access is denied."""
    identity = _validate_tenant_required()
    if isinstance(identity, tuple):
        return identity

    data = request.get_json(silent=True) or {}
    other_tenant_id = data.get("other_tenant_id")
    if not other_tenant_id:
        return jsonify({"error": "other_tenant_id is required"}), 400

    other_identity = TenantIdentity(
        tenant_id=other_tenant_id,
        identity_id="other_user",
        auth_method="test",
    )

    service = get_cross_boundary_service()
    result = service.verify_tenant_isolation(identity, other_identity)

    return jsonify(result)


# ── Health ──────────────────────────────────────────────────────


@cb_bp.route("/health", methods=["GET"])
def api_health():
    """Cross-boundary intelligence health check."""
    return jsonify({
        "status": "healthy",
        "service": "cross_boundary_intelligence",
        "version": "1.0.0",
    })


# ── Tenant Identity Helper ──────────────────────────────────────


@cb_bp.route("/identity", methods=["GET"])
def api_identity():
    """Return current tenant identity for debugging."""
    identity = _resolve_tenant_identity()
    return jsonify({
        "identity": identity.to_dict(),
        "authenticated": identity.is_authenticated,
    })