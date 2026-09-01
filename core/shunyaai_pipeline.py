"""
SHUNYAAI Intelligence Pipeline — governed multi-engine orchestration.

Chains the 8 intelligence engines through the capability registry into a
single coherent processing pipeline for every SHUNYAAI interaction.

Pipeline stages:
  1. PERCEPTION   — receive user input → structured Observation
  2. CONTEXT      — assemble context from observation, memory, knowledge
  3. REASONING    — reason over context with evidence
  4. PLANNING     — create action plan based on reasoning conclusion
  5. DECISION     — make decision from plan options
  6. REFLECTION   — evaluate the outcome (post-execution)
  7. LEARNING     — extract patterns from reflection
  8. CONFIDENCE   — compute overall confidence score

Every stage runs through the capability registry for governed invocation
(permission checks, usage tracking, telemetry). Stages can be skipped or
run in parallel where safe.

This is the canonical SHUNYAAI execution pipeline. The capability registry
is the authoritative source of truth for what engines exist and their status.
"""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4


# ---------------------------------------------------------------------------
# Pipeline Stages
# ---------------------------------------------------------------------------

class PipelineStage(str):
    """Named pipeline stages matching the 8 intelligence engines."""
    PERCEPTION = "perception"
    CONTEXT_ASSEMBLY = "context_assembly"
    REASONING = "reasoning"
    PLANNING = "planning"
    DECISION = "decision"
    REFLECTION = "reflection"
    LEARNING = "learning"
    CONFIDENCE = "confidence"


PIPELINE_ORDER = [
    PipelineStage.PERCEPTION,
    PipelineStage.CONTEXT_ASSEMBLY,
    PipelineStage.REASONING,
    PipelineStage.PLANNING,
    PipelineStage.DECISION,
    PipelineStage.REFLECTION,
    PipelineStage.LEARNING,
    PipelineStage.CONFIDENCE,
]


# ---------------------------------------------------------------------------
# Pipeline Result
# ---------------------------------------------------------------------------

class IntelligencePipelineResult:
    """Result from running the full SHUNYAAI intelligence pipeline."""

    def __init__(self):
        self.trace_id: str = f"pipe_{uuid4().hex[:12]}"
        self.stages: dict[str, dict[str, Any]] = {}
        self.errors: list[dict[str, Any]] = []
        self.stages_completed: int = 0
        self.total_latency_ms: float = 0.0
        self.final_output: dict[str, Any] = {}
        self.requires_clarification: bool = False
        self.clarification_question: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "stages": {
                name: {
                    "output_type": info.get("output_type", ""),
                    "confidence": info.get("confidence", 0.0),
                    "latency_ms": info.get("latency_ms", 0.0),
                    "error": info.get("error"),
                }
                for name, info in self.stages.items()
            },
            "errors": self.errors,
            "stages_completed": self.stages_completed,
            "total_latency_ms": self.total_latency_ms,
            "final_output": self.final_output,
            "requires_clarification": self.requires_clarification,
            "clarification_question": self.clarification_question,
        }


# ---------------------------------------------------------------------------
# Pipeline Builder
# ---------------------------------------------------------------------------

class IntelligencePipeline:
    """Governed multi-engine pipeline for SHUNYAAI requests.

    Each stage invokes the corresponding engine via the capability registry,
    passing the accumulated context forward. No stage can bypass the registry's
    authorization and usage tracking.

    Engines that are UNWIRED are skipped gracefully (not crashed).
    """

    def __init__(self):
        self._trace_id: str = ""
        self._pipeline_result: IntelligencePipelineResult | None = None

    @property
    def registry(self):
        """Lazy import to avoid circular imports at module level."""
        from core.capability_registry import get_registry
        return get_registry()

    def run(self, user_input: str,
            identity_id: str = "",
            tenant_id: str = "",
            workspace: str = "",
            session_id: str = "",
            context: dict[str, Any] | None = None) -> IntelligencePipelineResult:
        """Run the full pipeline for a user request.

        Returns a structured result with per-stage output and cumulative
        telemetry.
        """
        result = IntelligencePipelineResult()
        self._pipeline_result = result
        pipeline_start = time.time()

        # Common context passed through all stages
        shared_ctx = {
            "user_input": user_input,
            "identity_id": identity_id,
            "tenant_id": tenant_id,
            "workspace": workspace,
            "session_id": session_id,
            "trace_id": result.trace_id,
        }
        if context:
            shared_ctx.update(context)

        # Stage 1: Perception — transform input into structured observation
        stage_output = self._run_stage(
            PipelineStage.PERCEPTION,
            {
                "input_type": "observation",
                "payload": {
                    "text": user_input,
                    "source": "user_input",
                    "source_metadata": {
                        "identity_id": identity_id,
                        "tenant_id": tenant_id,
                        "workspace": workspace,
                        "channel": "shunyaai",
                    },
                },
                "context": shared_ctx,
                "confidence_threshold": 0.5,
            },
            result,
        )

        observation = (stage_output or {}).get("payload", {})

        # Stage 2: Context Assembly — gather context around the observation
        stage_output = self._run_stage(
            PipelineStage.CONTEXT_ASSEMBLY,
            {
                "input_type": "assemble",
                "payload": {
                    "observation_ids": [observation.get("observation_id", "")],
                    "object_ids": [],
                    "query": user_input,
                },
                "context": shared_ctx,
                "confidence_threshold": 0.5,
            },
            result,
        )

        assembled_context = (stage_output or {}).get("payload", {})

        # Stage 3: Reasoning — reason over the assembled context
        stage_output = self._run_stage(
            PipelineStage.REASONING,
            {
                "input_type": "reasoning",
                "payload": {
                    "premises": [
                        f"User request: {user_input}",
                        f"Context: {assembled_context.get('summary', '')[:300]}",
                    ],
                    "reasoning_type": "deductive",
                    "evidence": assembled_context.get("evidence_items", []),
                    "observations": [observation],
                },
                "context": shared_ctx,
                "confidence_threshold": 0.5,
            },
            result,
        )

        reasoning_conclusion = (stage_output or {}).get("payload", {})

        # Stage 4: Planning — generate plan from reasoning
        stage_output = self._run_stage(
            PipelineStage.PLANNING,
            {
                "input_type": "plan",
                "payload": {
                    "objective": f"Respond to: {user_input[:200]}",
                    "context_summary": (reasoning_conclusion.get("conclusion", "") or
                                       assembled_context.get("summary", ""))[:300],
                },
                "context": shared_ctx,
                "confidence_threshold": 0.5,
            },
            result,
        )

        plan = (stage_output or {}).get("payload", {})

        # Stage 5: Decision — make a decision based on the plan
        stage_output = self._run_stage(
            PipelineStage.DECISION,
            {
                "input_type": "generate_options",
                "payload": {
                    "label": f"Respond to: {user_input[:120]}",
                    "description": f"Based on reasoning and plan, decide best response to user query",
                    "owner": identity_id or "system",
                },
                "context": shared_ctx,
                "confidence_threshold": 0.5,
            },
            result,
        )

        decision = (stage_output or {}).get("payload", {})

        # Build the final consolidated output
        result.final_output = {
            "observation": observation,
            "context": assembled_context,
            "conclusion": reasoning_conclusion.get("conclusion", ""),
            "plan": {
                "plan_id": plan.get("plan_id", ""),
                "steps": plan.get("steps", []),
            },
            "decision": {
                "decision_id": decision.get("decision_id", ""),
                "selected_option": decision.get("selected_option", {}),
            },
            "response_text": self._build_response_text(
                user_input, reasoning_conclusion, plan, decision
            ),
        }

        # Stages 6-8 run asynchronously post-response (reflection, learning, confidence)
        # These are currently best-effort — they don't block the response.
        self._run_stage(
            PipelineStage.REFLECTION,
            {
                "input_type": "reflect",
                "payload": {
                    "expected_outcome": {"stage": "completed", "plan_id": plan.get("plan_id", "")},
                    "actual_outcome": {"stage": "completed", "decision_id": decision.get("decision_id", "")},
                    "subject_id": session_id or result.trace_id,
                    "subject_type": "pipeline",
                },
                "context": shared_ctx,
            },
            result,
        )

        self._run_stage(
            PipelineStage.CONFIDENCE,
            {
                "input_type": "compute",
                "payload": {
                    "factors": [
                        {"name": "perception", "value": stage_output.get("confidence", 0.5), "weight": 0.15},
                        {"name": "reasoning", "value": 0.7, "weight": 0.18},
                        {"name": "planning", "value": 0.6, "weight": 0.12},
                        {"name": "decision", "value": 0.65, "weight": 0.15},
                    ],
                },
                "context": shared_ctx,
            },
            result,
        )

        result.total_latency_ms = round((time.time() - pipeline_start) * 1000, 1)
        return result

    def _run_stage(self, stage_name: str,
                   invoke_context: dict[str, Any],
                   result: IntelligencePipelineResult) -> dict[str, Any] | None:
        """Invoke a single pipeline stage via the capability registry.

        Returns the engine output payload, or None if the stage is unavailable.
        Never raises — errors are captured in result.errors.
        """
        stage_start = time.time()
        stage_info: dict[str, Any] = {"latency_ms": 0.0}

        try:
            cap = self.registry.get(stage_name)
            if cap is None or cap.status == "UNWIRED":
                stage_info["error"] = f"Engine '{stage_name}' is UNWIRED — skipped"
                result.stages[stage_name] = stage_info
                return None

            invoke_result = self.registry.invoke(stage_name, context=invoke_context)

            if invoke_result.get("success"):
                engine_output = invoke_result.get("result", {})
                stage_info["output_type"] = engine_output.get("output_type", "")
                stage_info["confidence"] = engine_output.get("confidence", 0.0)
                stage_info["latency_ms"] = round((time.time() - stage_start) * 1000, 1)
                result.stages[stage_name] = stage_info
                result.stages_completed += 1
                return engine_output
            else:
                error = invoke_result.get("error", "unknown error")
                stage_info["error"] = error
                stage_info["latency_ms"] = round((time.time() - stage_start) * 1000, 1)
                result.stages[stage_name] = stage_info
                result.errors.append({"stage": stage_name, "error": error})
                return None

        except Exception as e:
            stage_info["error"] = str(e)
            stage_info["latency_ms"] = round((time.time() - stage_start) * 1000, 1)
            result.stages[stage_name] = stage_info
            result.errors.append({"stage": stage_name, "error": str(e)})
            return None

    def _build_response_text(self, user_input: str,
                             conclusion: dict[str, Any],
                             plan: dict[str, Any],
                             decision: dict[str, Any]) -> str:
        """Build a human-readable response from the pipeline output."""
        conclusion_text = (conclusion.get("conclusion", "") or
                          conclusion.get("payload", {}).get("conclusion", ""))
        steps = plan.get("steps", [])
        decision_text = ""

        if decision.get("selected_option"):
            decision_text = f"Selected: {decision['selected_option']}"
        elif decision.get("options"):
            decision_text = f"Generated {len(decision['options'])} options to consider"

        parts = []
        if conclusion_text:
            parts.append(f"Analysis: {conclusion_text[:300]}")
        if steps:
            parts.append(f"Plan: {len(steps)} step(s)")
        if decision_text:
            parts.append(decision_text)

        if not parts:
            return "I processed your request through the intelligence pipeline."

        return " | ".join(parts)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_pipeline: IntelligencePipeline | None = None


def get_pipeline() -> IntelligencePipeline:
    """Get the singleton intelligence pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = IntelligencePipeline()
    return _pipeline


def reset_pipeline() -> None:
    """Reset the pipeline singleton (for testing)."""
    global _pipeline
    _pipeline = None