"""Reasoning Engine — produces answers, plans, explanations, and recommendations.

Now wired to the LLM provider chain for real AI responses, with
rule-based template fallback when no provider is available.
"""

from __future__ import annotations

import logging
from typing import Any

from .types import (
    ActionType,
    ContextFrame,
    IntelligenceResponse,
    PlanStep,
    ReasoningStep,
    ReasoningStrategy,
    ReasoningTrace,
    RetrievedEvidence,
    UserIntent,
)

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """Multi-strategy reasoning over fused evidence.

    Uses the LLM provider chain for response generation when available,
    with template-based fallback. This is the single canonical path
    for every AI response in SHUNYA.
    """

    def __init__(self):
        self._max_steps = 20
        self._llm_provider = None

    def wire_llm_provider(self, provider_fn: Any) -> None:
        """Wire the LLM provider for real AI response generation.

        Args:
            provider_fn: A callable that takes (messages, temperature, max_tokens)
                and returns a dict with 'content', 'model', 'finish_reason', 'usage'.
        """
        self._llm_provider = provider_fn

    def reason(self, intent: UserIntent, context: ContextFrame,
               evidence: list[RetrievedEvidence]) -> IntelligenceResponse:
        """Produce a response by reasoning over available evidence."""
        trace = ReasoningTrace(
            intent=intent, context=context,
            strategy=self._select_strategy(intent, evidence),
            evidence=evidence,
        )

        # Step 1: Gather — analyze what evidence is available
        gather_step = ReasoningStep(step_type="gather", description="Gathering evidence from available sources")
        gather_step.inputs = [e.source for e in evidence[:5]]
        gather_step.output = f"Found {len(evidence)} relevant evidence items"
        gather_step.evidence = evidence[:3]
        trace.steps.append(gather_step)

        # Step 2: Analyze — determine what the evidence tells us
        analyze_step = ReasoningStep(step_type="analyze", description="Analyzing evidence relevance")
        high_rel = [e for e in evidence if e.relevance >= 0.7]
        analyze_step.output = f"{len(high_rel)} items have high relevance"
        trace.steps.append(analyze_step)

        # Step 3: Infer — draw conclusions using LLM or template
        infer_step = ReasoningStep(step_type="infer", description="Drawing conclusions from evidence")
        answer = self._generate_response(intent, evidence, context)
        infer_step.output = answer[:200]
        trace.steps.append(infer_step)

        # Step 4: Verify — check confidence
        verify_step = ReasoningStep(step_type="verify", description="Verifying conclusion confidence")
        trace.confidence = self._calculate_confidence(evidence)
        verify_step.output = f"Overall confidence: {trace.confidence:.0%}"
        verify_step.confidence = trace.confidence
        trace.steps.append(verify_step)

        # Build plan
        actions = self._plan_actions(intent, trace)

        response = IntelligenceResponse(
            content=answer,
            actions=actions,
            trace=trace,
            requires_clarification=trace.confidence < 0.3 and intent.ambiguity > 0.5,
        )

        if response.requires_clarification:
            response.clarification_question = "I'm not sure I understood. Could you rephrase or provide more detail?"

        return response

    def _select_strategy(self, intent: UserIntent, evidence: list[RetrievedEvidence]) -> ReasoningStrategy:
        """Select the best reasoning strategy based on intent and evidence."""
        if any(e.source == "object" for e in evidence) and any(e.relevance >= 0.8 for e in evidence):
            return ReasoningStrategy.DIRECT_ANSWER
        if any(e.source == "business_graph" for e in evidence):
            return ReasoningStrategy.BUSINESS_GRAPH
        if any(e.source == "internet" for e in evidence):
            return ReasoningStrategy.INTERNET
        if len(evidence) >= 3:
            return ReasoningStrategy.MULTI_SOURCE
        return ReasoningStrategy.DEFER

    def _generate_response(self, intent: UserIntent, evidence: list[RetrievedEvidence],
                           context: ContextFrame | None = None) -> str:
        """Generate a response — tries LLM provider first, falls back to templates.

        Args:
            intent: The classified user intent with raw_input, category, etc.
            evidence: Retrieved evidence from all sources.
            context: The current context frame with workspace, module, etc.
        """
        # Try LLM provider first
        if self._llm_provider is not None:
            try:
                return self._generate_via_llm(intent, evidence, context)
            except Exception as e:
                logger.warning(f"LLM provider failed, falling back to template: {e}")

        # Fallback: template-based response
        return self._generate_template_response(intent, evidence)

    def _generate_via_llm(self, intent: UserIntent, evidence: list[RetrievedEvidence],
                          context: ContextFrame | None = None) -> str:
        """Generate a response using the wired LLM provider."""
        # Build a system prompt
        system_prompt = (
            "You are SHUNYA, an intelligent operating system for organizations. "
            "You help founders and team members understand their business, "
            "answer questions about their data, and assist with tasks. "
            "Be concise, helpful, and accurate. Base your answers on the "
            "evidence provided. If the evidence is insufficient, say so."
        )

        # Build user message with context and evidence
        user_parts = []

        if context and context.active_workspace:
            user_parts.append(f"Current workspace: {context.active_workspace}")
        if context and context.active_module:
            user_parts.append(f"Active module: {context.active_module}")

        if evidence:
            user_parts.append("\nAvailable evidence:")
            for i, e in enumerate(evidence[:5], 1):
                source = e.source or "unknown"
                snippet = (e.content[:300] + "...") if len(e.content or "") > 300 else (e.content or "")
                user_parts.append(f"  [{i}] ({source}, relevance={e.relevance:.1f}): {snippet}")

        user_parts.append(f"\nUser query: {intent.raw_input}")

        user_message = "\n".join(user_parts)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        result = self._llm_provider(messages, temperature=0.7, max_tokens=1024)
        content = result.get("content", "").strip()

        if content:
            return content

        raise ValueError("LLM returned empty content")

    def _generate_template_response(self, intent: UserIntent, evidence: list[RetrievedEvidence]) -> str:
        """Fallback template-based response when no LLM provider is available."""
        if not evidence:
            return "I don't have enough information to answer that yet."

        # Build response from evidence
        sources = set(e.source for e in evidence[:5])
        source_str = ", ".join(sorted(sources))

        top_evidence = [e for e in evidence[:3] if e.content]

        if not top_evidence:
            return "I found related context but no direct answers. Try a more specific question."

        items = []
        for e in top_evidence:
            items.append(e.content)

        response = "Based on the available information"
        if source_str:
            response += f" (from {source_str})"
        response += ":\n\n"
        response += "\n".join(f"• {item}" for item in items[:5])

        # Add action guidance
        if intent.category.value in ("command", "automate"):
            response += "\n\nI can help you with that. Would you like me to proceed?"

        return response

    def _calculate_confidence(self, evidence: list[RetrievedEvidence]) -> float:
        """Calculate overall confidence from evidence."""
        if not evidence:
            return 0.0
        weighted = sum(e.relevance * e.confidence for e in evidence)
        total_weight = sum(e.relevance for e in evidence) if evidence else 1
        return weighted / total_weight if total_weight > 0 else 0.0

    def _plan_actions(self, intent: UserIntent, trace: ReasoningTrace) -> list[PlanStep]:
        """Plan appropriate actions based on intent and reasoning."""
        actions = []
        if intent.category.value == "command" and trace.confidence >= 0.6:
            actions.append(PlanStep(action=ActionType.EXECUTE, description=f"Execute requested action: {intent.requested_outcome}",
                                    parameters={"intent": intent.raw_input}))
        elif intent.category.value == "automate" and trace.confidence >= 0.5:
            actions.append(PlanStep(action=ActionType.AUTOMATE, description="Set up automation",
                                    parameters={"suggestion": intent.requested_outcome}))
        elif intent.ambiguity > 0.5:
            actions.append(PlanStep(action=ActionType.CLARIFY, description="Ask for clarification"))
        return actions