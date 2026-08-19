"""
SHUNYA — Explainability Service.

Gate 3.3: Every intelligence output must be able to explain itself.

Given a conclusion (claim, recommendation, signal, or research result),
the explanation service traces back to:
- supporting evidence
- evidence source
- governed vs external origin
- freshness
- fact vs inference
- confidence/uncertainty
- assumptions
- conflicting evidence
- what information is missing

No hidden chain-of-thought exposure.
Structured, concise decision/evidence explanations only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from core.intelligence import (
    EvidenceSource,
    IntelligenceResponse,
    KnowledgeClaim,
    KnowledgeStatus,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Explanation — a single traceable explanation
# ═══════════════════════════════════════════════════════════════════


@dataclass
class Explanation:
    """A structured explanation for a single claim or conclusion.

    Every field is explicit — no hidden chain-of-thought.
    """
    # What is being explained
    claim: str = ""
    status: str = "unknown"         # "fact" | "inference" | "assumption" | "unknown" | "recommendation" | "error"

    # Why SHUNYA says this
    conclusion: str = ""
    supporting_evidence: list[dict] = field(default_factory=list)  # [{source, detail, type, timestamp}]
    evidence_count: int = 0
    governed_evidence_count: int = 0
    external_evidence_count: int = 0

    # How certain
    confidence: Optional[float] = None   # None = unknown
    confidence_known: bool = False

    # How fresh
    freshness_verified: bool = False
    freshness_ok: bool = False
    freshness_note: str = ""

    # Assumptions
    assumptions: list[str] = field(default_factory=list)

    # Conflicts
    conflicts: list[dict] = field(default_factory=list)  # [{claim, company_value, external_value, authoritative}]

    # Missing information
    missing_information: list[str] = field(default_factory=list)

    # Audit
    model_used: str = ""
    provider_used: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        self.evidence_count = len(self.supporting_evidence)
        self.governed_evidence_count = sum(
            1 for e in self.supporting_evidence if e.get("type") == "company_data"
        )
        self.external_evidence_count = sum(
            1 for e in self.supporting_evidence if e.get("type") == "external"
        )
        self.confidence_known = self.confidence is not None


# ═══════════════════════════════════════════════════════════════════
# ExplanationService — produces explanations
# ═══════════════════════════════════════════════════════════════════


class ExplanationService:
    """Produce structured explanations from intelligence responses.

    Given an IntelligenceResponse, produces a concise, structured
    explanation for each claim, including evidence, assumptions,
    conflicts, and missing information.
    """

    def explain_response(self, response: IntelligenceResponse) -> list[Explanation]:
        """Produce explanations for all claims in a response."""
        explanations = []
        for claim in response.claims:
            explanations.append(self._explain_claim(claim, response))
        if not explanations:
            # Explain the overall answer
            explanations.append(self._explain_answer(response))
        return explanations

    def explain_claim_index(self, response: IntelligenceResponse, index: int = 0) -> Optional[Explanation]:
        """Explain a specific claim by index."""
        if index < len(response.claims):
            return self._explain_claim(response.claims[index], response)
        if index == 0 and response.answer:
            return self._explain_answer(response)
        return None

    def _explain_claim(self, claim: KnowledgeClaim, response: IntelligenceResponse) -> Explanation:
        """Produce an explanation for a single claim."""
        evidence = []
        for s in claim.sources:
            evidence.append({
                "source": s.source,
                "type": s.type,
                "detail": s.detail[:200],
                "timestamp": s.timestamp,
                "url": s.url,
            })

        # Add context sources
        for s in response.context_used:
            evidence.append({
                "source": s.source,
                "type": s.type,
                "detail": s.detail[:200],
                "timestamp": s.timestamp,
            })

        # Add external sources
        for s in response.external_sources_used:
            evidence.append({
                "source": s.source,
                "type": s.type,
                "detail": s.detail[:200],
                "url": s.url,
            })

        # Detect conflicts
        conflicts = []
        if response.context_used and response.external_sources_used:
            for ctx in response.context_used:
                for ext in response.external_sources_used:
                    if ctx.detail != ext.detail and any(
                        w in ctx.detail.lower() for w in ext.detail.lower().split()[:3]
                    ):
                        conflicts.append({
                            "claim": claim.statement[:100],
                            "company_value": ctx.detail[:200],
                            "external_value": ext.detail[:200],
                            "authoritative": "company",
                        })

        # Assumptions
        assumptions = []
        if claim.status == KnowledgeStatus.ASSUMPTION:
            assumptions.append(claim.statement)
        if not response.freshness_verified:
            assumptions.append("Freshness could not be verified")

        # Missing information
        missing = []
        if not response.context_used:
            missing.append("No governed company data available")
        if not response.freshness_verified and response.freshness_ok is False:
            missing.append("Current external information could not be verified")
        if response.degraded:
            missing.append("Some intelligence providers were unavailable")

        return Explanation(
            claim=claim.statement,
            status=claim.status.value,
            conclusion=claim.statement,
            supporting_evidence=evidence,
            confidence=claim.confidence,
            freshness_verified=response.freshness_verified,
            freshness_ok=response.freshness_ok,
            freshness_note=response.freshness_note or "",
            assumptions=assumptions,
            conflicts=conflicts,
            missing_information=missing,
            model_used=response.model_used,
            provider_used=response.provider_used,
        )

    def _explain_answer(self, response: IntelligenceResponse) -> Explanation:
        """Produce an explanation for the overall answer."""
        evidence = []
        for s in response.context_used:
            evidence.append({
                "source": s.source,
                "type": s.type,
                "detail": s.detail[:200],
                "timestamp": s.timestamp,
            })
        for s in response.external_sources_used:
            evidence.append({
                "source": s.source,
                "type": s.type,
                "detail": s.detail[:200],
                "url": s.url,
            })

        return Explanation(
            claim=response.summary or response.answer[:200],
            status="inference" if not response.degraded else "error",
            conclusion=response.answer[:300],
            supporting_evidence=evidence,
            confidence=0.5 if not response.degraded else None,
            freshness_verified=response.freshness_verified,
            freshness_ok=response.freshness_ok,
            freshness_note=response.freshness_note or "",
            model_used=response.model_used,
            provider_used=response.provider_used,
        )


__all__ = [
    "Explanation",
    "ExplanationService",
]