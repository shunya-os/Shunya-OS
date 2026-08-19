"""
SHUNYA — Canonical Intelligence Service.

Gate 2.4: The authoritative intelligence pipeline for all SHUNYA
intelligence operations.

Implements the company-first intelligence hierarchy:
    COMPANY/USER CONTEXT FIRST
    → CANONICAL OBJECTS/EVIDENCE/MEMORY
    → DETERMINISTIC COMPUTATION
    → EXTERNAL CURRENT INFORMATION WHEN NEEDED
    → MODEL REASONING WHEN ACTUALLY USEFUL
    → EVIDENCE-BACKED ANSWER
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from core.intelligence import (
    EvidenceSource,
    IntelligenceCapability,
    IntelligenceRequest,
    IntelligenceResponse,
    KnowledgeClaim,
    KnowledgeStatus,
    FreshnessRequirement,
)

logger = logging.getLogger(__name__)


class IntelligenceService:
    """Canonical intelligence service — the single authoritative pipeline
    for all SHUNYA intelligence operations.

    Pipeline:
        1. Company context retrieval (objects, evidence, memory)
        2. Deterministic computation (calculations, aggregations)
        3. External research (web search, only when needed)
        4. Model reasoning (controlled, with provenance)
        5. Evidence-backed answer with fact/inference separation
    """

    def __init__(self) -> None:
        self._company_context_cache: dict[str, list[EvidenceSource]] = {}

    # ── Main entry point ──────────────────────────────────────────────

    def process(self, request: IntelligenceRequest) -> IntelligenceResponse:
        """Process an intelligence request through the full pipeline."""
        start = time.time()
        response = IntelligenceResponse(
            request_id=request.request_id,
            question=request.question,
            capability=request.capability,
        )

        try:
            # 1. Retrieve company context
            logger.info("IQ[%s] Step 1: Retrieving company context", request.request_id[:12])
            context = self._retrieve_company_context(request)
            response.context_used = context

            # 2. Deterministic computation (if applicable)
            logger.info("IQ[%s] Step 2: Deterministic computation", request.request_id[:12])
            det_result = self._deterministic_compute(request, context)
            if det_result:
                response.deterministic_result = det_result["result"]
                response.deterministic_type = det_result["type"]
                response.add_claim(
                    statement=det_result["description"],
                    status=KnowledgeStatus.FACT,
                    confidence=1.0,
                    sources=[EvidenceSource(
                        type="deterministic",
                        source=det_result["type"],
                        detail=det_result["description"],
                    )],
                )

            # 3. External research (only if needed and freshness required)
            logger.info("IQ[%s] Step 3: External research check", request.request_id[:12])
            needs_external = self._needs_external_research(request, context, det_result)
            if needs_external:
                ext_sources = self._external_research(request)
                response.external_sources_used = ext_sources
                response.freshness_verified = bool(ext_sources)
                response.freshness_ok = bool(ext_sources)
                if not ext_sources:
                    response.freshness_note = "External research unavailable — cannot verify current information"
                    response.add_claim(
                        statement="Unable to verify current external information",
                        status=KnowledgeStatus.UNKNOWN,
                        detail="External search provider unavailable or returned no results",
                    )
            else:
                response.freshness_note = "Company context sufficient — no external research needed"

            # 4. Model reasoning (controlled, with provenance)
            logger.info("IQ[%s] Step 4: Model reasoning", request.request_id[:12])
            model_result = self._model_reason(request, context, det_result, ext_sources if needs_external else None)
            if model_result:
                response.answer = model_result.get("answer", "")
                response.summary = model_result.get("summary", "")
                response.model_used = model_result.get("model", "")
                response.provider_used = model_result.get("provider", "")
                response.model_provenance = model_result.get("provenance", "unknown")

                # Add claims from model output
                for claim in model_result.get("claims", []):
                    response.add_claim(
                        statement=claim.get("statement", ""),
                        status=KnowledgeStatus(claim.get("status", "inference")),
                        confidence=claim.get("confidence"),
                        detail=claim.get("detail", ""),
                    )
            else:
                response.degraded = True
                response.error = "Model provider unavailable — intelligence degraded"
                response.add_claim(
                    statement="Model reasoning unavailable",
                    status=KnowledgeStatus.ERROR,
                    detail="No AI provider available in the configured chain",
                )

        except Exception as e:
            logger.error("IQ[%s] Pipeline error: %s", request.request_id[:12], e)
            response.degraded = True
            response.error = str(e)
            response.add_claim(
                statement="Intelligence pipeline encountered an error",
                status=KnowledgeStatus.ERROR,
                detail=str(e),
            )

        response.duration_ms = (time.time() - start) * 1000
        return response

    # ── Step 1: Company Context Retrieval ─────────────────────────────

    def _retrieve_company_context(self, request: IntelligenceRequest) -> list[EvidenceSource]:
        """Retrieve company context first — this is always the first step."""
        sources: list[EvidenceSource] = []

        # 1a. Current object context
        if request.context_object_id and request.context_object_type:
            try:
                from app import db
                from sqlalchemy import text
                result = db.session.execute(
                    text("SELECT name, content, status, created_at FROM sh_objects WHERE object_id = :oid"),
                    {"oid": request.context_object_id},
                ).fetchone()
                if result:
                    sources.append(EvidenceSource(
                        type="company_data",
                        source="sh_objects",
                        timestamp=str(result.created_at) if result.created_at else "",
                        detail=f"Current object: {result.name} ({result.status})",
                    ))
            except Exception as e:
                logger.warning("Context retrieval failed: %s", e)

        # 1b. Tenant/company data
        if request.tenant_id:
            try:
                from app.tenant import Tenant
                tenant = Tenant.query.get(request.tenant_id)
                if tenant:
                    sources.append(EvidenceSource(
                        type="company_data",
                        source="tenant",
                        detail=f"Company: {tenant.name} ({tenant.domain})",
                    ))
            except Exception:
                pass

        # 1c. Evidence records
        try:
            from core.evidence.engine import EvidenceEngine
            engine = EvidenceEngine()
            # Query for recent evidence
            evidence_list = engine.get_events(limit=5)
            for ev in evidence_list[:3]:
                sources.append(EvidenceSource(
                    type="company_data",
                    source="evidence",
                    timestamp=ev.timestamp,
                    confidence=ev.confidence,
                    detail=ev.statement[:200],
                ))
        except Exception:
            pass

        # 1d. Memory records
        try:
            from app import db
            from sqlalchemy import text
            memories = db.session.execute(
                text("SELECT content, source, confidence, created_at FROM memory_records WHERE tenant_id = :tid ORDER BY created_at DESC LIMIT 5"),
                {"tid": request.tenant_id},
            ).fetchall()
            for mem in memories:
                sources.append(EvidenceSource(
                    type="company_data",
                    source="memory",
                    timestamp=str(mem.created_at) if mem.created_at else "",
                    confidence=mem.confidence,
                    detail=str(mem.content)[:200],
                ))
        except Exception:
            pass

        return sources

    # ── Step 2: Deterministic Computation ─────────────────────────────

    def _deterministic_compute(self, request: IntelligenceRequest,
                                context: list[EvidenceSource]) -> Optional[dict]:
        """Perform deterministic computation if the request is a
        calculation, aggregation, or similar deterministic operation."""
        question_lower = request.question.lower().strip()

        # Check for calculation patterns
        calc_patterns = ["how many", "count", "total", "sum", "average", "mean",
                         "calculate", "compute", "what is the number"]
        is_calculation = any(p in question_lower for p in calc_patterns)

        if not is_calculation:
            # Check for comparison patterns
            comp_patterns = ["compare", "difference", "versus", "vs", "which is better"]
            is_comparison = any(p in question_lower for p in comp_patterns)
            if not is_comparison:
                return None

            # Comparison of objects
            if is_comparison:
                try:
                    from app import db
                    from sqlalchemy import text
                    # Get object counts by type
                    rows = db.session.execute(
                        text("SELECT object_type, COUNT(*) as cnt FROM sh_objects WHERE is_deleted = false GROUP BY object_type ORDER BY cnt DESC LIMIT 10")
                    ).fetchall()
                    counts = {r.object_type: r.cnt for r in rows}
                    return {
                        "type": "comparison",
                        "result": counts,
                        "description": f"Object counts: {counts}",
                    }
                except Exception:
                    return None

        # Calculation/aggregation
        try:
            from app import db
            from sqlalchemy import text
            # Count objects
            total = db.session.execute(
                text("SELECT COUNT(*) FROM sh_objects WHERE is_deleted = false")
            ).scalar() or 0
            by_type = db.session.execute(
                text("SELECT object_type, COUNT(*) as cnt FROM sh_objects WHERE is_deleted = false GROUP BY object_type ORDER BY cnt DESC")
            ).fetchall()
            type_counts = {r.object_type: r.cnt for r in by_type}
            return {
                "type": "calculation",
                "result": {"total_objects": total, "by_type": type_counts},
                "description": f"Total objects: {total}. Types: {type_counts}",
            }
        except Exception:
            return None

    # ── Step 3: External Research ─────────────────────────────────────

    def _needs_external_research(self, request: IntelligenceRequest,
                                  context: list[EvidenceSource],
                                  det_result: Optional[dict]) -> bool:
        """Determine if external research is needed."""
        # If freshness explicitly requires it
        if request.freshness.requires_external_verification:
            return True

        # If capability explicitly requires it
        if request.capability in (IntelligenceCapability.RESEARCH,
                                   IntelligenceCapability.FORECAST):
            return True

        # If no company context found
        if not context:
            return True

        return False

    def _external_research(self, request: IntelligenceRequest) -> list[EvidenceSource]:
        """Perform external web research using the Gate 2.3 connector fabric."""
        sources: list[EvidenceSource] = []
        try:
            from app.search.routes import _web_search
            results = _web_search(request.question, max_results=5)
            for r in results:
                sources.append(EvidenceSource(
                    type="external",
                    source="web_search",
                    url=r.get("url", ""),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    detail=f"{r.get('title', '')}: {r.get('snippet', '')[:200]}",
                ))
        except Exception as e:
            logger.warning("External research failed: %s", e)
        return sources

    # ── Step 4: Model Reasoning ───────────────────────────────────────

    def _model_reason(self, request: IntelligenceRequest,
                       context: list[EvidenceSource],
                       det_result: Optional[dict] = None,
                       ext_sources: Optional[list[EvidenceSource]] = None) -> Optional[dict]:
        """Perform controlled model reasoning with company-first context."""
        # Build system prompt with company-first context
        system_parts = [
            "You are SHUNYA, an intelligent business analysis assistant.",
            "You answer questions based on the user's company data first.",
            "Company data is always more authoritative than external information.",
            "You must distinguish facts from inferences in your answer.",
            "",
            "=== COMPANY DATA ===",
        ]

        if context:
            for c in context:
                system_parts.append(f"[{c.type}] {c.detail} (source: {c.source})")
        else:
            system_parts.append("No company data available for this query.")

        if det_result:
            system_parts.append("")
            system_parts.append("=== DETERMINISTIC COMPUTATION ===")
            system_parts.append(json.dumps(det_result, default=str))

        if ext_sources:
            system_parts.append("")
            system_parts.append("=== EXTERNAL RESEARCH ===")
            for s in ext_sources:
                system_parts.append(f"- {s.detail} ({s.url})")

        system_parts.append("")
        system_parts.append("When answering, use this format:")
        system_parts.append("[FACT] ... for claims supported by company data")
        system_parts.append("[INFERENCE] ... for derived conclusions")
        system_parts.append("[ASSUMPTION] ... for unproven but reasonable assumptions")
        system_parts.append("[UNKNOWN] ... for information you cannot determine")
        system_parts.append("[RECOMMENDATION] ... for suggested actions")

        system_prompt = "\n".join(system_parts)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.question},
        ]

        # Try the provider chain
        try:
            from app.ai.provider import _registry
            chain = _registry.chain
            last_error = ""
            for provider in chain:
                if not provider.is_available():
                    continue
                try:
                    result = provider.complete(
                        messages,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                    )
                    if result.get("finish_reason") == "error":
                        last_error = result.get("error", "Provider error")
                        logger.warning("Provider %s failed: %s", provider.name, last_error)
                        continue
                    content = result.get("content", "")
                    model = result.get("model", provider.name)
                    provider_name = provider.name

                    return {
                        "answer": content,
                        "summary": content[:200],
                        "model": model,
                        "provider": provider_name,
                        "provenance": "free" if provider_name in ("openai", "groq") else "paid",
                        "claims": self._parse_claims(content),
                    }
                except Exception as e:
                    last_error = str(e)
                    logger.warning("Provider %s exception: %s", provider.name, last_error)
                    continue

            logger.warning("All providers failed; last: %s", last_error)
            return None

        except ImportError:
            logger.warning("AI provider registry not available")
            return None

    @staticmethod
    def _parse_claims(content: str) -> list[dict]:
        """Parse knowledge claims from model output."""
        claims = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("[FACT]"):
                claims.append({"statement": line[6:].strip(), "status": "fact", "confidence": 0.9})
            elif line.startswith("[INFERENCE]"):
                claims.append({"statement": line[11:].strip(), "status": "inference", "confidence": 0.6})
            elif line.startswith("[ASSUMPTION]"):
                claims.append({"statement": line[12:].strip(), "status": "assumption", "confidence": 0.3})
            elif line.startswith("[UNKNOWN]"):
                claims.append({"statement": line[9:].strip(), "status": "unknown", "confidence": None})
            elif line.startswith("[RECOMMENDATION]"):
                claims.append({"statement": line[16:].strip(), "status": "recommendation", "confidence": 0.5})
        return claims


# ── Module-level convenience ──────────────────────────────────────────

_service: Optional[IntelligenceService] = None


def get_intelligence_service() -> IntelligenceService:
    global _service
    if _service is None:
        _service = IntelligenceService()
    return _service


def reset_intelligence_service() -> None:
    global _service
    _service = None


__all__ = [
    "IntelligenceService",
    "get_intelligence_service",
    "reset_intelligence_service",
]