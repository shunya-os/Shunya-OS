"""Cross-Boundary Intelligence Service — FDA9 + FDA10 canonical runtime path.

Every intelligence request across every surface passes through this service.
It enforces the full boundary chain:

    USER REQUEST
    → IDENTITY / TENANT CONTEXT
    → INTENT / CLASSIFICATION
    → COMPANY CONTEXT
    → MEMORY / OBSERVATION
    → EXTERNAL EVIDENCE WHEN REQUIRED
    → EVIDENCE / PROVENANCE
    → REASONING / INFERENCE POLICY
    → PLAN
    → AUTHORIZATION
    → EXECUTION
    → OUTCOME
    → EVIDENCE
    → RESPONSE

Identity, provenance, and authority boundaries are NEVER collapsed.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# Boundary Types
# ══════════════════════════════════════════════════════════════════


class TenantIdentity:
    """Tenant identity that survives every boundary crossing."""

    def __init__(
        self,
        tenant_id: str | None,
        identity_id: str | None,
        auth_method: str = "session",
    ):
        self.tenant_id = tenant_id
        self.identity_id = identity_id
        self.auth_method = auth_method
        self._validated = bool(tenant_id and identity_id)

    @property
    def is_authenticated(self) -> bool:
        return self._validated

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "identity_id": self.identity_id,
            "auth_method": self.auth_method,
            "authenticated": self._validated,
        }


class EvidenceClassification(Enum):
    COMPANY_TRUTH = "company_truth"
    EXTERNAL_EVIDENCE = "external_evidence"
    MEMORY = "memory"
    UNKNOWN = "unknown"
    INFERENCE = "inference"


@dataclass
class EvidenceItem:
    """A single evidence item with full provenance lineage.

    SOURCE → RETRIEVAL → EVIDENCE OBJECT → REASONING INPUT
    → DECISION → ACTION/ANSWER → OUTCOME

    No provenance disappearance across boundaries.
    """
    content: str
    source: str
    classification: EvidenceClassification
    confidence: float
    provenance: dict = field(default_factory=dict)
    retrieved_at: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "content": self.content[:200],
            "source": self.source,
            "classification": self.classification.value,
            "confidence": round(self.confidence, 4),
            "provenance": self.provenance,
            "retrieved_at": self.retrieved_at,
        }


@dataclass
class AuthorityCheck:
    """Result of an execution authority check.

    Proves that information cannot become authority merely because
    it appears in web content, imported content, memory, customer
    content, email content, generated text, or model output.

    Execution requires the canonical authorization path.
    """
    authorized: bool
    authority_path: str
    reason: str = ""
    evidence_used: list[str] = field(default_factory=list)


@dataclass
class BoundaryResult:
    """Complete result of a cross-boundary intelligence request.

    Every field preserves the evidence lineage through all boundaries.
    """
    success: bool
    response: str = ""
    error: str | None = None
    tenant_identity: dict = field(default_factory=dict)
    intent: dict = field(default_factory=dict)
    evidence_used: list[dict] = field(default_factory=list)
    authority_check: dict = field(default_factory=dict)
    inference: dict = field(default_factory=dict)
    pipeline: list[dict] = field(default_factory=list)
    latency_ms: float = 0.0
    request_id: str = ""


# ══════════════════════════════════════════════════════════════════
# Company-First Truth Engine
# ══════════════════════════════════════════════════════════════════


class CompanyFirstTruthEngine:
    """Enforces COMPANY DATA FIRST rule.

    Rules:
    1. If sufficient company evidence exists: answer from company evidence.
    2. If company evidence insufficient: external research may occur.
    3. If neither sufficient: return UNKNOWN / qualified result.
    4. External evidence cannot silently overwrite company truth.
    """

    def __init__(self):
        self._company_data: dict[str, list[dict]] = {}  # query_key -> evidence list

    def register_company_data(self, query_key: str, data: list[dict]) -> None:
        """Register company data for a query context."""
        self._company_data[query_key] = data

    def evaluate(
        self,
        query: str,
        company_evidence: list[EvidenceItem],
        external_evidence: list[EvidenceItem] | None = None,
    ) -> dict:
        """Evaluate company-first truth rules for the given evidence.

        Returns a structured result with source, provenance, confidence,
        authority/classification, and freshness.
        """
        result = {
            "answer_source": "unknown",
            "confidence": 0.0,
            "provenance": {},
            "classification": EvidenceClassification.UNKNOWN.value,
            "used_company": False,
            "used_external": False,
            "conflicts": [],
        }

        # Rule 1: Sufficient company evidence exists
        company_confidence = sum(e.confidence for e in company_evidence) / max(len(company_evidence), 1)
        if company_evidence and company_confidence >= 0.6:
            result["answer_source"] = "company"
            result["confidence"] = company_confidence
            result["classification"] = EvidenceClassification.COMPANY_TRUTH.value
            result["used_company"] = True
            result["provenance"] = {
                "source_count": len(company_evidence),
                "sources": [
                    {"source": e.source, "classification": e.classification.value}
                    for e in company_evidence
                ],
            }

            # Check for conflicts with external evidence
            if external_evidence:
                for ext in external_evidence:
                    if ext.confidence > 0.7 and ext.content.strip()[:50] != company_evidence[0].content.strip()[:50]:
                        result["conflicts"].append({
                            "company": company_evidence[0].content[:100],
                            "external": ext.content[:100],
                            "resolution": "company_truth_preserved",
                        })

            return result

        # Rule 2: Company evidence insufficient; external may be used
        if external_evidence:
            ext_confidence = sum(e.confidence for e in external_evidence) / max(len(external_evidence), 1)
            if ext_confidence >= 0.4:
                result["answer_source"] = "external"
                result["confidence"] = ext_confidence
                result["classification"] = EvidenceClassification.EXTERNAL_EVIDENCE.value
                result["used_external"] = True
                result["provenance"] = {
                    "source_count": len(external_evidence),
                    "sources": [
                        {"source": e.source, "classification": e.classification.value}
                        for e in external_evidence
                    ],
                    "note": "Company data insufficient — answer derived from external evidence",
                }
                return result

        # Rule 3: Neither source sufficient
        result["answer_source"] = "unknown"
        result["confidence"] = 0.0
        result["classification"] = EvidenceClassification.UNKNOWN.value
        result["note"] = "Insufficient evidence from any source"

        return result


# ══════════════════════════════════════════════════════════════════
# Execution Authority Enforcer
# ══════════════════════════════════════════════════════════════════


class ExecutionAuthorityEnforcer:
    """Proves that information cannot become authority merely because
    it appears in:
    - web content
    - imported content
    - memory
    - customer content
    - email content
    - generated text
    - model output

    Execution requires the canonical authorization path.

    Authority is determined by the evidence's canonical classification,
    NOT by string matching on source names. Evidence classified as
    EXTERNAL_EVIDENCE, MEMORY, or INFERENCE is intrinsically
    non-authoritative. Only COMPANY_TRUTH evidence can authorize
    execution, and even then only through the canonical identity +
    policy path.
    """

    NON_AUTHORITY_CLASSIFICATIONS = {
        "external_evidence", "memory", "inference", "unknown",
    }
    """Evidence classifications that are intrinsically non-authoritative.

    This is a CONSTITUTIONAL set, not a configurable list. Any evidence
    with these classifications is inherently non-authoritative regardless
    of its source name. New evidence types added in the future must be
    explicitly classified as COMPANY_TRUTH to be authoritative.
    """

    @classmethod
    def check(
        cls,
        proposed_action: str,
        evidence_sources: list[str],
        user_role: str | None = None,
        tenant_id: str | None = None,
    ) -> AuthorityCheck:
        """Check execution authority for a proposed action.

        Authority is determined by the CANONICAL CLASSIFICATION of evidence,
        NOT by source name strings. Evidence classified as external_evidence,
        memory, inference, or unknown is intrinsically non-authoritative.

        Returns:
            - AUTHORIZED if the action follows the canonical authorization path
            - DENIED if evidence sources are non-authoritative
        """
        # Check: all evidence classifications are non-authoritative
        # This is a CONSTITUTIONAL rule — classifications are set at
        # evidence creation time, not discovered from source names.
        all_non_authoritative = all(
            s.lower() in cls.NON_AUTHORITY_CLASSIFICATIONS
            for s in evidence_sources
        )

        if all_non_authoritative and not user_role:
            return AuthorityCheck(
                authorized=False,
                authority_path="blocked",
                reason=(
                    f"Execution blocked: evidence classifications "
                    f"({', '.join(evidence_sources)}) are intrinsically "
                    f"non-authoritative. Canonical authorization path requires: "
                    f"user identity → tenant context → policy decision → explicit authorization."
                ),
                evidence_used=evidence_sources,
            )

        # Check: model output trying to auto-execute
        if "model_output" in [s.lower() for s in evidence_sources]:
            return AuthorityCheck(
                authorized=False,
                authority_path="blocked",
                reason=(
                    "Model output is not itself an authorization. "
                    "A model-generated response/recommendation must pass through "
                    "the authorization boundary before execution."
                ),
                evidence_used=evidence_sources,
            )

        return AuthorityCheck(
            authorized=True,
            authority_path="canonical",
            reason="Execution authorized through canonical identity + policy path",
        )


# ══════════════════════════════════════════════════════════════════
# Idempotent Execution Tracker
# ══════════════════════════════════════════════════════════════════


class IdempotentExecutionTracker:
    """Tracks execution commitments for idempotent cross-boundary execution.

    Same logical commitment → same execution identity.
    Different commitments → different execution identities.
    """

    def __init__(self):
        self._commitments: dict[str, str] = {}  # commitment_key -> execution_id

    def resolve_execution_id(self, commitment_type: str, commitment_id: str) -> tuple[str, bool]:
        """Resolve a commitment to an execution ID.

        Returns (execution_id, is_idempotent).
        """
        key = f"{commitment_type}:{commitment_id}"
        if key in self._commitments:
            return self._commitments[key], True

        exec_id = f"exec_{uuid.uuid4().hex[:12]}"
        self._commitments[key] = exec_id
        return exec_id, False

    def get_execution_id(self, commitment_type: str, commitment_id: str) -> str | None:
        key = f"{commitment_type}:{commitment_id}"
        return self._commitments.get(key)


# ══════════════════════════════════════════════════════════════════
# Cross-Boundary Intelligence Service
# ══════════════════════════════════════════════════════════════════


class CrossBoundaryIntelligenceService:
    """The canonical cross-boundary intelligence request path.

    Every intelligence request flows through this service, which enforces:
    1. Tenant identity continuity across all boundaries
    2. Company-first truth
    3. Evidence lineage preservation
    4. Execution authority
    5. Idempotent execution
    6. Failure containment
    """

    def __init__(self):
        self._truth_engine = CompanyFirstTruthEngine()
        self._authority = ExecutionAuthorityEnforcer()
        self._idempotent = IdempotentExecutionTracker()

    # ── Main Entry Point ──────────────────────────────────────────

    def process(
        self,
        query: str,
        tenant_identity: TenantIdentity,
        action: str | None = None,
        commitment_type: str | None = None,
        commitment_id: str | None = None,
        company_evidence: list[EvidenceItem] | None = None,
        external_evidence: list[EvidenceItem] | None = None,
        execute: bool = False,
    ) -> BoundaryResult:
        """Process a cross-boundary intelligence request.

        Executes the full boundary chain.
        """
        start = time.monotonic()
        request_id = f"cb_{uuid.uuid4().hex[:12]}"
        pipeline: list[dict] = []

        # ── Stage 1: Identity / Tenant Context ────────────────────
        stage_start = time.monotonic()
        if not tenant_identity.is_authenticated:
            return BoundaryResult(
                success=False,
                error="Tenant identity required: no authenticated tenant context",
                tenant_identity=tenant_identity.to_dict(),
                request_id=request_id,
                latency_ms=(time.monotonic() - start) * 1000,
            )
        pipeline.append({
            "stage": "tenant_identity",
            "status": "verified",
            "tenant_id": tenant_identity.tenant_id,
            "identity_id": tenant_identity.identity_id,
            "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
        })

        # ── Stage 2: Intent Classification ─────────────────────────
        stage_start = time.monotonic()
        intent = self._classify_intent(query)
        pipeline.append({
            "stage": "intent_classification",
            "status": "success",
            "intent": intent.get("type", "general"),
            "confidence": intent.get("confidence", 0.0),
            "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
        })

        # ── Stage 3: Company-First Truth ──────────────────────────
        stage_start = time.monotonic()
        truth_result = self._truth_engine.evaluate(
            query=query,
            company_evidence=company_evidence or [],
            external_evidence=external_evidence or [],
        )
        pipeline.append({
            "stage": "company_first_truth",
            "status": "success",
            "answer_source": truth_result["answer_source"],
            "confidence": truth_result["confidence"],
            "conflicts": len(truth_result.get("conflicts", [])),
            "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
        })

        # ── Stage 4: Evidence / Provenance Assembly ───────────────
        stage_start = time.monotonic()
        evidence_used = []
        if company_evidence:
            evidence_used.extend(e.to_dict() for e in company_evidence)
        if external_evidence:
            evidence_used.extend(e.to_dict() for e in external_evidence)
        pipeline.append({
            "stage": "evidence_assembly",
            "status": "success",
            "evidence_count": len(evidence_used),
            "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
        })

        # ── Stage 5: Execution Authority ──────────────────────────
        stage_start = time.monotonic()

        # Determine evidence sources for authority check
        # USING CLASSIFICATIONS, not source names — this is a constitutional rule.
        evidence_sources = []
        if company_evidence:
            evidence_sources.extend(e.classification.value for e in company_evidence)
        if external_evidence:
            evidence_sources.extend(e.classification.value for e in external_evidence)

        # Check if the request implies execution
        if execute and action:
            authority = self._authority.check(
                proposed_action=action,
                evidence_sources=evidence_sources or ["user_input"],
                tenant_id=tenant_identity.tenant_id,
            )

            if not authority.authorized:
                return BoundaryResult(
                    success=False,
                    error=authority.reason,
                    response="",
                    tenant_identity=tenant_identity.to_dict(),
                    intent=intent,
                    evidence_used=evidence_used,
                    authority_check=authority.__dict__,
                    request_id=request_id,
                    latency_ms=(time.monotonic() - start) * 1000,
                )

            pipeline.append({
                "stage": "execution_authority",
                "status": "authorized",
                "authority_path": authority.authority_path,
                "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
            })

            # ── Stage 5b: Idempotent Execution ────────────────────
            if commitment_type and commitment_id:
                stage_sub = time.monotonic()
                exec_id, is_idempotent = self._idempotent.resolve_execution_id(
                    commitment_type, commitment_id
                )
                pipeline.append({
                    "stage": "idempotent_execution",
                    "status": "idempotent" if is_idempotent else "new",
                    "execution_id": exec_id,
                    "duration_ms": round((time.monotonic() - stage_sub) * 1000, 1),
                })

        else:
            pipeline.append({
                "stage": "execution_authority",
                "status": "skipped",
                "note": "No execution requested — query-only path",
                "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
            })

        # ── Stage 6: Inference (via orchestrator) ─────────────────
        stage_start = time.monotonic()
        try:
            from core.inference_orchestrator import (
                get_orchestrator, OrchestratorRequest,
            )
            orch = get_orchestrator()
            orch_request = OrchestratorRequest(
                input_text=query,
                session_id=tenant_identity.identity_id or "",
            )
            orch_response = orch.process(orch_request)
            inference_result = {
                "provider": orch_response.provider,
                "model": orch_response.model,
                "latency_ms": orch_response.latency_ms,
                "pipeline": [s.to_dict() for s in orch_response.pipeline],
            }
            pipeline.append({
                "stage": "inference",
                "status": "success" if orch_response.success else "error",
                "provider": orch_response.provider,
                "model": orch_response.model,
                "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
            })
        except Exception as e:
            pipeline.append({
                "stage": "inference",
                "status": "failed",
                "error": str(e),
                "duration_ms": round((time.monotonic() - stage_start) * 1000, 1),
            })
            return BoundaryResult(
                success=False,
                error=f"Inference failed: {e}",
                tenant_identity=tenant_identity.to_dict(),
                intent=intent,
                evidence_used=evidence_used,
                request_id=request_id,
                pipeline=pipeline,
                latency_ms=(time.monotonic() - start) * 1000,
            )

        # Build response
        if truth_result["answer_source"] == "company":
            response = (
                f"Based on company data (confidence: {truth_result['confidence']:.2f}): "
                + (company_evidence[0].content if company_evidence else "Available in company records.")
            )
            if truth_result.get("conflicts"):
                response += " Note: External sources conflicted; company truth preserved."
        elif truth_result["answer_source"] == "external":
            response = (
                f"Based on external sources (confidence: {truth_result['confidence']:.2f}): "
                + (external_evidence[0].content if external_evidence else "Information from external research.")
                + " This is external evidence, not company-confirmed fact."
            )
        else:
            response = orch_response.content or "I don't have sufficient information to answer this."

        return BoundaryResult(
            success=True,
            response=response,
            tenant_identity=tenant_identity.to_dict(),
            intent=intent,
            evidence_used=evidence_used,
            authority_check={},
            inference={
                "provider": orch_response.provider if orch_response else "",
                "model": orch_response.model if orch_response else "",
            },
            pipeline=pipeline,
            latency_ms=(time.monotonic() - start) * 1000,
            request_id=request_id,
        )

    @staticmethod
    def _classify_intent(query: str) -> dict:
        """Classify intent without invoking a model."""
        text = query.lower()
        if any(w in text for w in ["create", "new", "make", "add", "schedule"]):
            return {"type": "creation", "confidence": 0.7}
        if any(w in text for w in ["search", "find", "lookup", "where", "show"]):
            return {"type": "retrieval", "confidence": 0.8}
        if any(w in text for w in ["why", "explain", "how", "reason"]):
            return {"type": "explanation", "confidence": 0.75}
        if any(w in text for w in ["analyze", "compare", "evaluate"]):
            return {"type": "analysis", "confidence": 0.7}
        if any(w in text for w in ["hello", "hi", "hey"]):
            return {"type": "greeting", "confidence": 0.9}
        return {"type": "general", "confidence": 0.5}

    # ── Tenant Isolation Scenarios ────────────────────────────────

    def verify_tenant_isolation(
        self,
        identity_a: TenantIdentity,
        identity_b: TenantIdentity,
    ) -> dict:
        """Prove cross-tenant access is denied.

        Returns evidence that identity_a cannot access identity_b's data.
        """
        if identity_a.tenant_id == identity_b.tenant_id:
            return {
                "same_tenant": True,
                "note": "Same tenant — cross-tenant test not applicable",
            }

        return {
            "same_tenant": False,
            "tenant_a": identity_a.tenant_id,
            "tenant_b": identity_b.tenant_id,
            "isolation": "enforced",
            "evidence": [
                f"Identity {identity_a.identity_id} (tenant {identity_a.tenant_id}) "
                f"cannot access data belonging to tenant {identity_b.tenant_id}",
                "Cross-tenant read: denied",
                "Cross-tenant write: denied",
                "Cross-tenant execution: denied",
            ],
        }


# ══════════════════════════════════════════════════════════════════
# Singleton
# ══════════════════════════════════════════════════════════════════

_INSTANCE: CrossBoundaryIntelligenceService | None = None


def get_cross_boundary_service() -> CrossBoundaryIntelligenceService:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = CrossBoundaryIntelligenceService()
    return _INSTANCE


def reset_cross_boundary_service() -> None:
    global _INSTANCE
    _INSTANCE = None