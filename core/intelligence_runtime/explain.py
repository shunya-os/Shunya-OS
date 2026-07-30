"""Explainability Engine — produces evidence traces for every response."""

from __future__ import annotations

from typing import Any

from .types import IntelligenceResponse, ReasoningTrace, RetrievedEvidence

_explain_instance = None


class ExplainabilityEngine:
    """Provides explanation for any response the runtime produces."""

    @classmethod
    def summarize_trace(cls, trace: ReasoningTrace | None) -> str:
        """Summarize the reasoning process in natural language."""
        if not trace:
            return "No reasoning trace available."

        parts = []
        parts.append(f"I analyzed your request as a '{trace.intent.category.value}' intent")
        if trace.intent.entities:
            entity_names = [e.get("value", "") for e in trace.intent.entities[:3]]
            parts.append(f"involving: {', '.join(entity_names)}")
        parts.append(f"with {trace.confidence:.0%} confidence.")
        parts.append("")
        parts.append("Steps taken:")
        for i, step in enumerate(trace.steps, 1):
            parts.append(f"  {i}. {step.step_type.title()} — {step.description}")
            if step.evidence:
                parts.append(f"     Used {len(step.evidence)} evidence items")
        if trace.assumptions:
            parts.append("")
            parts.append("Assumptions:")
            for a in trace.assumptions:
                parts.append(f"  • {a}")
        return "\n".join(parts)

    @classmethod
    def list_evidence(cls, evidence: list[RetrievedEvidence]) -> list[dict]:
        """Return structured evidence list for UI display."""
        return [e.to_dict() for e in evidence]

    @classmethod
    def explain_response(cls, response: IntelligenceResponse) -> dict[str, Any]:
        """Produce a full explanation for a response."""
        trace = response.trace
        return {
            "confidence": trace.confidence if trace else 0.0,
            "sources": list(set(e.source for e in (trace.evidence if trace else []))),
            "summary": cls.summarize_trace(response.trace) if response.trace else "No trace available",
            "evidence": cls.list_evidence(trace.evidence if trace else []),
            "assumptions": trace.assumptions if trace else [],
            "alternatives": trace.alternatives if trace else [],
        }


def get_explainer() -> ExplainabilityEngine:
    global _explain_instance
    if _explain_instance is None:
        _explain_instance = ExplainabilityEngine()
    return _explain_instance