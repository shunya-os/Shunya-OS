"""
SHUNYA — Universal Research Orchestrator.

Gate 3.2: The authoritative pipeline for universal intelligence queries.

Orchestrates the full research pipeline:
    USER QUESTION
    → INTENT UNDERSTANDING
    → GOVERNED CONTEXT RETRIEVAL
    → RESEARCH SUFFICIENCY EVALUATION
    → CONNECTED PROVIDER DATA (when needed)
    → FRESH EXTERNAL RESEARCH (when needed)
    → DETERMINISTIC COMPUTATION (when sufficient)
    → MODEL REASONING (when genuinely needed)
    → SYNTHESIS
    → EXPLAINED OUTPUT
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from core.intelligence import (
    EvidenceSource,
    IntelligenceCapability,
    IntelligenceRequest,
    IntelligenceResponse,
    IntelligenceService,
    KnowledgeClaim,
    KnowledgeStatus,
    FreshnessRequirement,
    get_intelligence_service,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Research Sufficiency — determines whether context is sufficient
# ═══════════════════════════════════════════════════════════════════


class SufficiencyLevel(str, Enum):
    """How sufficient the current evidence is to answer the question."""
    SUFFICIENT = "sufficient"               # Can answer from governed context alone
    PARTIALLY_SUFFICIENT = "partially_sufficient"  # Some context available, but external data needed
    INSUFFICIENT = "insufficient"           # Need fresh external research
    FRESHNESS_REQUIRED = "freshness_required"  # Context exists but may be stale
    DETERMINISTIC_SUFFICIENT = "deterministic_sufficient"  # Can compute deterministically
    UNKNOWN = "unknown"                     # Cannot determine sufficiency


@dataclass
class SufficiencyEvaluation:
    """Result of evaluating whether governed context is sufficient."""
    level: SufficiencyLevel = SufficiencyLevel.UNKNOWN
    reason: str = ""
    context_count: int = 0
    requires_external: bool = False
    requires_deterministic: bool = False
    requires_model: bool = False


# ═══════════════════════════════════════════════════════════════════
# Research Plan — the planned steps to answer
# ═══════════════════════════════════════════════════════════════════


@dataclass
class ResearchPlan:
    """The research plan — what steps are needed to answer the question."""
    steps: list[str] = field(default_factory=list)
    needs_context: bool = True
    needs_external: bool = False
    needs_deterministic: bool = False
    needs_model: bool = False
    sufficiency: SufficiencyEvaluation = field(default_factory=SufficiencyEvaluation)


# ═══════════════════════════════════════════════════════════════════
# Universal Research Orchestrator
# ═══════════════════════════════════════════════════════════════════


class UniversalResearchOrchestrator:
    """The canonical universal research orchestrator.

    Combines governed context, connected providers, external research,
    deterministic computation, and model reasoning into a single
    explained, evidence-backed answer.
    """

    def __init__(self):
        self._intelligence: Optional[IntelligenceService] = None

    @property
    def intelligence(self) -> IntelligenceService:
        if self._intelligence is None:
            self._intelligence = get_intelligence_service()
        return self._intelligence

    # ── Main entry point ──────────────────────────────────────────────

    def research(self, question: str, tenant_id: int = 0,
                 workspace_id: Optional[int] = None,
                 actor_id: str = "",
                 capability: Optional[IntelligenceCapability] = None,
                 freshness_seconds: Optional[int] = None,
                 max_tokens: int = 2048) -> IntelligenceResponse:
        """Perform universal research on a question.

        Pipeline:
            1. Understand intent
            2. Retrieve governed context
            3. Evaluate sufficiency
            4. Deterministic computation (if applicable)
            5. External research (if needed)
            6. Model reasoning (if needed)
            7. Synthesis with provenance
        """
        start = time.time()

        # 1. Understand intent
        question_type = self._classify_question(question)
        resolved_capability = capability or self._map_question_type(question_type)

        # 2. Create request
        request = IntelligenceRequest(
            question=question,
            capability=resolved_capability,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            actor_id=actor_id,
            max_tokens=max_tokens,
            freshness=FreshnessRequirement(
                max_age_seconds=freshness_seconds,
                requires_external_verification=self._needs_freshness(question_type),
            ),
        )

        # 3. Build research plan
        plan = self._build_plan(question_type, request)

        # 4. Retrieve governed context (ALWAYS first)
        context = self.intelligence._retrieve_company_context(request)

        # 5. Evaluate sufficiency
        sufficiency = self._evaluate_sufficiency(context, plan, request)

        # 6. Execute based on sufficiency
        if sufficiency.level == SufficiencyLevel.SUFFICIENT and not plan.needs_model:
            # Answer from context alone — no model needed
            response = self._answer_from_context(request, context, start)
            response.context_used = context
            return response

        # Full pipeline
        response = self._full_pipeline(request, context, plan, sufficiency, start)
        return response

    # ── Question classification ───────────────────────────────────────

    @staticmethod
    def _classify_question(question: str) -> str:
        """Classify a question into a type."""
        q = question.lower().strip()
        if q.startswith("analyze") or "risk" in q.split() or "unusual" in q.split():
            return "analyze"
        if q.startswith("what is") or q.startswith("what are") or q.startswith("what does"):
            return "explain"
        if q.startswith("why") or q.startswith("how did") or q.startswith("how does"):
            return "explain"
        if q.startswith("compare") or " vs " in q or " versus " in q:
            return "compare"
        if q.startswith("summarize") or q.startswith("summary") or "what changed" in q:
            return "summarize"
        if q.startswith("plan") or q.startswith("what should") or q.startswith("what next"):
            return "plan"
        if q.startswith("research") or q.startswith("search") or q.startswith("find"):
            return "research"
        if q.startswith("calculate") or q.startswith("compute") or q.startswith("count"):
            return "calculate"
        if q.startswith("analyze") or q.startswith("what is unusual") or "risk" in q:
            return "analyze"
        if q.startswith("synthesize") or q.startswith("combine"):
            return "synthesize"
        if q.startswith("challenge") or q.startswith("conflict") or "disagree" in q:
            return "challenge"
        return "general"

    @staticmethod
    def _map_question_type(question_type: str) -> IntelligenceCapability:
        mapping = {
            "explain": IntelligenceCapability.EXPLAIN,
            "analyze": IntelligenceCapability.DATA_ANALYSIS,
            "compare": IntelligenceCapability.COMPARE,
            "summarize": IntelligenceCapability.SUMMARIZE,
            "plan": IntelligenceCapability.PLAN,
            "research": IntelligenceCapability.RESEARCH,
            "calculate": IntelligenceCapability.DATA_ANALYSIS,
            "synthesize": IntelligenceCapability.GENERAL,
            "challenge": IntelligenceCapability.GENERAL,
            "general": IntelligenceCapability.GENERAL,
        }
        return mapping.get(question_type, IntelligenceCapability.GENERAL)

    @staticmethod
    def _needs_freshness(question_type: str) -> bool:
        return question_type in ("research",)

    # ── Research Plan ─────────────────────────────────────────────────

    def _build_plan(self, question_type: str, request: IntelligenceRequest) -> ResearchPlan:
        plan = ResearchPlan()
        plan.needs_context = True

        if question_type == "calculate":
            plan.needs_deterministic = True
            plan.needs_model = False
            plan.needs_external = False
        elif question_type == "research":
            plan.needs_context = True
            plan.needs_external = True
            plan.needs_model = True
        elif question_type == "explain":
            plan.needs_context = True
            plan.needs_deterministic = False
            plan.needs_model = True  # May need model to explain
        elif question_type == "compare":
            plan.needs_context = True
            plan.needs_deterministic = True
            plan.needs_model = True
        elif question_type == "synthesize":
            plan.needs_external = True
            plan.needs_model = True
        else:
            plan.needs_context = True
            plan.needs_model = True

        plan.steps = self._build_steps(plan)
        return plan

    @staticmethod
    def _build_steps(plan: ResearchPlan) -> list[str]:
        steps = []
        if plan.needs_context:
            steps.append("Retrieve governed company/workspace context")
        if plan.needs_deterministic:
            steps.append("Perform deterministic computation")
        if plan.needs_external:
            steps.append("Retrieve fresh external information")
        if plan.needs_model:
            steps.append("Apply model reasoning")
        steps.append("Synthesize and present answer")
        return steps

    # ── Sufficiency Evaluation ────────────────────────────────────────

    def _evaluate_sufficiency(self, context: list[EvidenceSource],
                               plan: ResearchPlan,
                               request: IntelligenceRequest) -> SufficiencyEvaluation:
        """Evaluate whether governed context is sufficient to answer."""
        if not context:
            return SufficiencyEvaluation(
                level=SufficiencyLevel.INSUFFICIENT,
                reason="No governed context available",
                context_count=0,
                requires_external=plan.needs_external,
                requires_deterministic=plan.needs_deterministic,
                requires_model=plan.needs_model,
            )

        if plan.needs_deterministic:
            return SufficiencyEvaluation(
                level=SufficiencyLevel.DETERMINISTIC_SUFFICIENT,
                reason="Can be computed deterministically from governed data",
                context_count=len(context),
                requires_deterministic=True,
                requires_model=False,
            )

        if plan.needs_external:
            return SufficiencyEvaluation(
                level=SufficiencyLevel.PARTIALLY_SUFFICIENT,
                reason=f"Context available ({len(context)} sources) but external research required",
                context_count=len(context),
                requires_external=True,
                requires_model=True,
            )

        if plan.needs_model:
            return SufficiencyEvaluation(
                level=SufficiencyLevel.PARTIALLY_SUFFICIENT,
                reason=f"Context available ({len(context)} sources) — model reasoning required",
                context_count=len(context),
                requires_model=True,
            )

        return SufficiencyEvaluation(
            level=SufficiencyLevel.SUFFICIENT,
            reason=f"Context sufficient ({len(context)} sources)",
            context_count=len(context),
            requires_model=False,
        )

    # ── Context-only answer ───────────────────────────────────────────

    def _answer_from_context(self, request: IntelligenceRequest,
                              context: list[EvidenceSource],
                              start: float) -> IntelligenceResponse:
        """Answer directly from context without model."""
        response = IntelligenceResponse(
            request_id=request.request_id,
            question=request.question,
            capability=request.capability,
        )
        response.context_used = context
        # Build a summary from context items
        items = [f"[{c.source}] {c.detail}" for c in context[:5]]
        response.answer = "\n".join(items) if items else "No relevant information found."
        response.summary = f"Found {len(context)} relevant sources in governed context."
        for c in context:
            response.add_claim(c.detail[:200], KnowledgeStatus.FACT, c.confidence, sources=[c])
        response.duration_ms = (time.time() - start) * 1000
        return response

    # ── Full pipeline ─────────────────────────────────────────────────

    def _full_pipeline(self, request: IntelligenceRequest,
                        context: list[EvidenceSource],
                        plan: ResearchPlan,
                        sufficiency: SufficiencyEvaluation,
                        start: float) -> IntelligenceResponse:
        """Execute the full research pipeline."""
        # Pass through the existing IntelligenceService
        response = self.intelligence.process(request)

        # Ensure context is recorded
        if not response.context_used:
            response.context_used = context

        # Add research plan metadata
        response.deterministic_type = plan.needs_deterministic and "calculation" or ""

        # Add sufficiency information
        if sufficiency.level == SufficiencyLevel.INSUFFICIENT:
            response.add_claim(
                "Limited governed context available for this question",
                KnowledgeStatus.UNKNOWN,
                detail=sufficiency.reason,
            )

        # Check for provider failure
        if response.degraded and not response.freshness_verified:
            response.add_claim(
                "Fresh external information could not be verified",
                KnowledgeStatus.UNKNOWN,
                detail="External search provider unavailable — answer uses available governed data only",
            )

        return response

    # ── Health check ──────────────────────────────────────────────────

    def health(self) -> dict:
        """Check the health of the research orchestrator."""
        return {
            "status": "healthy",
            "intelligence_available": self._intelligence is not None,
        }


# ── Module-level singleton ──────────────────────────────────────────

_orchestrator: Optional[UniversalResearchOrchestrator] = None


def get_research_orchestrator() -> UniversalResearchOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = UniversalResearchOrchestrator()
    return _orchestrator


def reset_research_orchestrator() -> None:
    global _orchestrator
    _orchestrator = None


__all__ = [
    "SufficiencyLevel",
    "SufficiencyEvaluation",
    "ResearchPlan",
    "UniversalResearchOrchestrator",
    "get_research_orchestrator",
    "reset_research_orchestrator",
]