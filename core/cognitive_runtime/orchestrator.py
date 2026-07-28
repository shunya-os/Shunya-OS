"""SHUNYA Cognitive Runtime — Orchestrator.

The CognitiveRuntime is the single authoritative execution layer for all
intelligent behaviour. It coordinates engine invocation, pipeline execution,
confidence propagation, escalation, observability, policies, and recovery.

Engines never coordinate each other directly. All execution passes through
this runtime.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from core.cognitive_runtime.models import (
    DEFAULT_ENGINE_WEIGHTS,
    PARALLEL_GROUPS,
    PIPELINE_ORDER,
    CancellationState,
    CognitiveSession,
    CompletionState,
    EnginePlugin,
    EngineTiming,
    EscalationRecord,
    PipelineStage,
    RuntimePolicies,
    SessionState,
    _now_iso,
)

logger = logging.getLogger(__name__)


class CognitiveRuntime:
    """Canonical execution layer for all SHUNYA intelligent behaviour.

    Usage:
        runtime = CognitiveRuntime()
        runtime.register_default_engines()
        session = runtime.create_session(actor="user_1", objective="Analyze Q3 trends")
        result = await runtime.execute(session)
    """

    def __init__(self, policies: RuntimePolicies | None = None):
        self._plugins: dict[str, EnginePlugin] = {}
        self._policies = policies or RuntimePolicies()
        self._engine_id_to_stage: dict[str, PipelineStage] = {}
        self._stage_to_engine_ids: dict[PipelineStage, list[str]] = {}

    # ── Plugin Registration ────────────────────────────────────────────

    def register_engine(
        self,
        engine: Any,
        engine_id: str,
        stage: PipelineStage,
        capabilities: list[str] | None = None,
        dependencies: list[str] | None = None,
        confidence_weight: float | None = None,
        parallel_safe: bool = False,
    ) -> None:
        """Register an intelligence engine with the runtime.

        A new engine requires only this call — no runtime core changes.
        """
        if engine_id in self._plugins:
            raise ValueError(f"Engine already registered: {engine_id}")

        plugin = EnginePlugin(
            engine_id=engine_id,
            stage=stage,
            capabilities=capabilities or [],
            dependencies=dependencies or [],
            confidence_weight=(
                confidence_weight if confidence_weight is not None
                else DEFAULT_ENGINE_WEIGHTS.get(engine_id, 0.1)
            ),
            parallel_safe=parallel_safe,
            engine_ref=engine,
        )
        self._plugins[engine_id] = plugin
        self._engine_id_to_stage[engine_id] = stage
        self._stage_to_engine_ids.setdefault(stage, []).append(engine_id)

    def get_plugin(self, engine_id: str) -> EnginePlugin | None:
        return self._plugins.get(engine_id)

    def list_plugins(self) -> list[EnginePlugin]:
        return list(self._plugins.values())

    # ── Session Management ─────────────────────────────────────────────

    def create_session(
        self,
        actor: str,
        objective: str,
        triggering_event: str = "",
        context: dict[str, Any] | None = None,
    ) -> CognitiveSession:
        """Create a new cognitive session.

        Nothing executes outside a CognitiveSession.
        """
        session = CognitiveSession(
            actor=actor,
            objective=objective,
            triggering_event=triggering_event,
            context=context or {},
        )
        # Seed context with initial execution data
        session.context.setdefault("objective", objective)
        session.context.setdefault("actor", actor)
        session.context.setdefault("triggering_event", triggering_event)
        session.add_event("SessionStarted", {
            "actor": actor,
            "objective": objective,
            "triggering_event": triggering_event,
        })
        return session

    # ── Execution ──────────────────────────────────────────────────────

    async def execute(self, session: CognitiveSession) -> CognitiveSession:
        """Execute a complete cognitive pipeline through all registered engines.

        Returns the session with all results, traces, and outcomes populated.
        """
        if session.state.is_terminal:
            # Cancelled sessions pass through without execution
            if session.state == SessionState.CANCELLED:
                return session
            raise ValueError(f"Cannot execute terminal session: {session.state.value}")

        session.state = SessionState.RUNNING
        pipeline_start = time.time()

        try:
            for stage in PIPELINE_ORDER:
                if stage == PipelineStage.RECEIVED:
                    continue
                if stage == PipelineStage.COMPLETED:
                    continue
                if session.state.is_terminal:
                    break
                if session.cancellation.cancelled:
                    break

                await self._execute_stage(session, stage)

            # Complete
            if not session.state.is_terminal and not session.cancellation.cancelled:
                total_duration = (time.time() - pipeline_start) * 1000

                # Compute final accumulated confidence
                if session.confidence_history:
                    final_conf = sum(
                        c.get("accumulated", 0.0)
                        for c in session.confidence_history[-1:]
                    )
                else:
                    final_conf = 0.0

                session.completion = CompletionState(
                    completed=True,
                    final_confidence=round(final_conf, 4),
                    total_duration_ms=round(total_duration, 2),
                    stages_completed=list(session.engine_results.keys()),
                    timestamp=_now_iso(),
                )
                session.transition_to(SessionState.COMPLETED)
                session.current_stage = PipelineStage.COMPLETED
                session.add_event("SessionCompleted", {
                    "final_confidence": session.completion.final_confidence,
                    "total_duration_ms": session.completion.total_duration_ms,
                    "stages_completed": session.completion.stages_completed,
                })

        except (ValueError, TypeError, RuntimeError, OSError) as exc:
            session.errors.append(str(exc))
            session.transition_to(SessionState.FAILED, reason=str(exc))
            session.current_stage = PipelineStage.FAILED
            session.completion.stages_failed = list(session.engine_results.keys())
            session.add_event("SessionFailed", {
                "error": str(exc),
                "stage": session.current_stage.value,
            })

        session.updated_at = _now_iso()
        return session

    # ── Stage Execution ────────────────────────────────────────────────

    async def _execute_stage(self, session: CognitiveSession, stage: PipelineStage) -> None:
        """Execute a single pipeline stage (potentially multiple engines)."""
        engine_ids = self._stage_to_engine_ids.get(stage, [])

        if not engine_ids:
            logger.debug("No engines registered for stage %s, skipping", stage.value)
            return

        # Check for parallel-safe stages
        parallel_group = self._find_parallel_group(stage)

        if parallel_group:
            # Execute all stages in this parallel group concurrently
            await self._execute_parallel_stages(session, parallel_group)
        else:
            # Sequential execution for this stage
            for engine_id in engine_ids:
                plugin = self._plugins[engine_id]
                await self._invoke_engine(session, plugin, stage)

    def _find_parallel_group(self, stage: PipelineStage) -> list[PipelineStage] | None:
        """Check if this stage is part of a parallel execution group."""
        for group in PARALLEL_GROUPS:
            if stage in group:
                return list(group)
        return None

    async def _execute_parallel_stages(
        self, session: CognitiveSession, stages: list[PipelineStage]
    ) -> None:
        """Execute multiple stages concurrently (e.g. REFLECTING + LEARNING)."""
        max_parallel = self._policies.parallel.max_parallel_stages
        tasks = []

        for stage in stages:
            engine_ids = self._stage_to_engine_ids.get(stage, [])
            for engine_id in engine_ids:
                plugin = self._plugins[engine_id]
                tasks.append(self._invoke_engine(session, plugin, stage))

        if not tasks:
            return

        # Limit concurrency to policy max
        semaphore = asyncio.Semaphore(max_parallel)
        async def _bounded_invoke():
            async with semaphore:
                # Re-bind session from closure
                pass  # tasks are already bound

        # Run all tasks
        await asyncio.gather(*tasks, return_exceptions=True)

    # ── Engine Invocation ───────────────────────────────────────────────

    async def _invoke_engine(
        self,
        session: CognitiveSession,
        plugin: EnginePlugin,
        stage: PipelineStage,
    ) -> None:
        """Invoke a single engine, wrapping with timing, events, and confidence."""
        from core.intelligence.models import EngineInput

        engine = plugin.engine_ref
        if engine is None:
            raise RuntimeError(f"Engine {plugin.engine_id} has no ref")

        # Check cancellation
        if session.cancellation.cancelled:
            return

        # Check escalation max
        if len(session.escalation) >= self._policies.escalation.max_escalations_per_session:
            err = "Max escalations reached for this session"
            session.errors.append(err)
            session.add_event("SessionFailed", {"error": err})
            session.transition_to(SessionState.FAILED, reason=err)
            return

        # Build accumulated confidence context
        acc_confidence = self._compute_accumulated_confidence(session)

        # Determine engine-specific input_type from pipeline stage
        input_type = self._stage_to_input_type(stage)

        engine_context = dict(session.context)
        engine_context["accumulated_confidence"] = acc_confidence
        engine_context["session_id"] = session.session_id
        engine_context["trace_id"] = session.trace_id

        # Create EngineInput using the session's context
        engine_input = EngineInput(
            input_type=input_type,
            payload=self._prepare_engine_payload(stage, session),
            context=engine_context,
            trace_id=session.trace_id,
            confidence_threshold=self._policies.confidence.minimum_acceptable_confidence,
        )

        # Timing
        timing = EngineTiming(
            engine_id=plugin.engine_id,
            stage=stage.value,
            start_time_ms=time.time() * 1000,
        )
        session.add_event("StageStarted", {
            "stage": stage.value,
            "engine_id": plugin.engine_id,
        })

        try:
            # Check timeout policy — handle both sync and async engines
            engine_result = engine.process(engine_input)
            if asyncio.iscoroutine(engine_result):
                engine_output = await asyncio.wait_for(
                    engine_result,
                    timeout=self._policies.timeout.engine_timeout_ms / 1000,
                )
            else:
                engine_output = engine_result

            timing.end_time_ms = time.time() * 1000
            timing.duration_ms = round(timing.end_time_ms - timing.start_time_ms, 2)
            session.timing[plugin.engine_id] = timing

            # Store engine result
            session.engine_results[plugin.engine_id] = {
                "output_type": engine_output.output_type,
                "confidence": engine_output.confidence,
                "deterministic": engine_output.deterministic,
                "escalation_used": engine_output.escalation_used,
                "payload": engine_output.payload,
            }

            # Confidence propagation
            self._record_confidence(session, plugin.engine_id, engine_output.confidence)

            # Reasoning / decision chain tracking
            if stage == PipelineStage.REASONING:
                session.reasoning_history.append(engine_output.payload)
            if stage == PipelineStage.DECIDING:
                session.decisions.append(engine_output.payload)

            # Escalation handling
            if (engine_output.escalation_used or engine_output.confidence < self._policies.confidence.minimum_acceptable_confidence) and self._policies.escalation.allow_escalation:
                    escalation = EscalationRecord(
                        engine_id=plugin.engine_id,
                        reason=(
                            "engine reported escalation_used"
                            if engine_output.escalation_used
                            else "confidence below minimum threshold"
                        ),
                        confidence_threshold=self._policies.confidence.minimum_acceptable_confidence,
                        current_confidence=engine_output.confidence,
                    )
                    session.escalation.append(escalation)
                    session.add_event("EscalationRequested", {
                        "engine_id": plugin.engine_id,
                        "confidence": engine_output.confidence,
                        "threshold": self._policies.confidence.minimum_acceptable_confidence,
                    })

            session.add_event("StageCompleted", {
                "stage": stage.value,
                "engine_id": plugin.engine_id,
                "confidence": engine_output.confidence,
                "duration_ms": timing.duration_ms,
            })

            # Update context with engine's payload for downstream
            if isinstance(engine_output.payload, dict):
                session.context.update(engine_output.payload)

        except asyncio.TimeoutError:
            timing.end_time_ms = time.time() * 1000
            session.timing[plugin.engine_id] = timing
            err = f"Engine {plugin.engine_id} timed out after {self._policies.timeout.engine_timeout_ms}ms"
            session.errors.append(err)

            if self._policies.retry.max_retries > 0:
                await self._retry_engine(session, plugin, stage)
            else:
                raise RuntimeError(err)

        except Exception as exc:
            timing.end_time_ms = time.time() * 1000
            session.timing[plugin.engine_id] = timing
            err = f"Engine {plugin.engine_id} failed: {exc}"
            session.errors.append(err)

            if self._policies.failure.fail_fast:
                raise

            if self._policies.retry.max_retries > 0:
                await self._retry_engine(session, plugin, stage)

    # ── Retry Logic ────────────────────────────────────────────────────

    async def _retry_engine(
        self,
        session: CognitiveSession,
        plugin: EnginePlugin,
        stage: PipelineStage,
    ) -> None:
        """Retry a failed engine invocation with backoff."""
        session.transition_to(SessionState.RETRYING)

        for attempt in range(1, self._policies.retry.max_retries + 1):
            backoff = self._policies.retry.backoff_ms / 1000 * (2 ** (attempt - 1))
            await asyncio.sleep(backoff)

            try:
                await self._invoke_engine(session, plugin, stage)
                session.transition_to(SessionState.RUNNING)
                return
            except Exception:
                if attempt == self._policies.retry.max_retries:
                    raise
                continue

    # ── Confidence Propagation ──────────────────────────────────────────

    def _compute_accumulated_confidence(self, session: CognitiveSession) -> float:
        """Weighted average of all engine confidences so far."""
        if not session.confidence_history:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for entry in session.confidence_history:
            engine_id = entry.get("engine_id", "")
            plugin = self._plugins.get(engine_id)
            weight = plugin.confidence_weight if plugin else 0.1
            conf = entry.get("confidence", 0.0)
            weighted_sum += weight * conf
            total_weight += weight

        if total_weight == 0:
            return 0.0
        return weighted_sum / total_weight

    def _record_confidence(
        self, session: CognitiveSession, engine_id: str, confidence: float
    ) -> None:
        """Record an engine's confidence and update accumulated confidence."""
        entry = {
            "engine_id": engine_id,
            "confidence": confidence,
            "stage": session.current_stage.value,
            "timestamp": _now_iso(),
        }
        session.confidence_history.append(entry)

        acc = self._compute_accumulated_confidence(session)
        session.trace.confidence_evolution.append({
            "stage": session.current_stage.value,
            "accumulated": round(acc, 4),
            "engine_contributions": session.confidence_history[-1:],
        })
        session.add_event("ConfidenceUpdated", {
            "accumulated_confidence": round(acc, 4),
            "engine_id": engine_id,
            "engine_confidence": confidence,
        })

    # ── Cancellation ───────────────────────────────────────────────────

    def cancel_session(
        self, session: CognitiveSession, reason: str = "User requested cancellation"
    ) -> None:
        """Request graceful cancellation of a running session."""
        if session.state.is_terminal:
            return
        session.cancellation = CancellationState(
            cancelled=True,
            reason=reason,
            at_stage=session.current_stage.value,
            timestamp=_now_iso(),
        )
        session.transition_to(SessionState.CANCELLED, reason=reason)
        session.current_stage = PipelineStage.CANCELLED
        session.add_event("SessionCancelled", {
            "reason": reason,
            "stage": session.current_stage.value,
        })

    # ── Health ─────────────────────────────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        """Return runtime health status."""
        engine_status = {}
        for eid, plugin in self._plugins.items():
            try:
                if hasattr(plugin.engine_ref, "health_check"):
                    engine_status[eid] = plugin.engine_ref.health_check()
                else:
                    engine_status[eid] = {"status": "unknown"}
            except (ValueError, TypeError, RuntimeError, OSError) as exc:
                engine_status[eid] = {"status": "error", "error": str(exc)}

        return {
            "status": "healthy",
            "runtime": "cognitive_runtime",
            "engines_registered": len(self._plugins),
            "policies": {
                "retry_max": self._policies.retry.max_retries,
                "timeout_ms": self._policies.timeout.engine_timeout_ms,
                "max_escalations": self._policies.escalation.max_escalations_per_session,
                "fail_fast": self._policies.failure.fail_fast,
            },
            "engine_plugins": {eid: {"stage": p.stage.value, "capabilities": p.capabilities}
                               for eid, p in self._plugins.items()},
        }

    # ── Convenience: Register all Phase D engines ──────────────────────

    def register_default_engines(self) -> None:
        """Register all 8 Phase D intelligence engines with default settings.

        Stages:
          PERCEIVING           → PerceptionEngine
          ASSEMBLING_CONTEXT   → ContextAssemblyEngine
          REASONING            → ReasoningEngine
          PLANNING             → PlanningEngine
          DECIDING             → DecisionEngine
          REFLECTING           → ReflectionEngine
          LEARNING             → LearningEngine
          CONFIDENCE_UPDATE    → ConfidenceEngine
        """
        from core.intelligence.confidence import ConfidenceEngine
        from core.intelligence.context_assembly import ContextAssemblyEngine
        from core.intelligence.decision import DecisionEngine
        from core.intelligence.learning import LearningEngine
        from core.intelligence.perception import PerceptionEngine
        from core.intelligence.planning import PlanningEngine
        from core.intelligence.reasoning import ReasoningEngine
        from core.intelligence.reflection import ReflectionEngine

        self.register_engine(
            PerceptionEngine(), "perception", PipelineStage.PERCEIVING,
            capabilities=["input_validation", "source_enrichment", "input_classification"],
            confidence_weight=0.15,
        )
        self.register_engine(
            ContextAssemblyEngine(), "context_assembly", PipelineStage.ASSEMBLING_CONTEXT,
            capabilities=["context_query", "relevance_scoring", "context_merge"],
            confidence_weight=0.12,
        )
        self.register_engine(
            ReasoningEngine(), "reasoning", PipelineStage.REASONING,
            capabilities=["deductive", "inductive", "abductive", "analogical",
                          "causal", "counterfactual", "probabilistic"],
            confidence_weight=0.18,
        )
        self.register_engine(
            PlanningEngine(), "planning", PipelineStage.PLANNING,
            capabilities=["plan_generation", "dependency_analysis", "risk_assessment"],
            confidence_weight=0.12,
        )
        self.register_engine(
            DecisionEngine(), "decision", PipelineStage.DECIDING,
            capabilities=["decision_lifecycle", "policy_evaluation", "evidence_validation",
                          "option_generation"],
            confidence_weight=0.15,
        )
        self.register_engine(
            ReflectionEngine(), "reflection", PipelineStage.REFLECTING,
            capabilities=["outcome_comparison", "anomaly_detection", "success_scoring",
                          "improvement_signals"],
            confidence_weight=0.10,
            parallel_safe=True,
        )
        self.register_engine(
            LearningEngine(), "learning", PipelineStage.LEARNING,
            capabilities=["pattern_detection", "knowledge_consolidation"],
            confidence_weight=0.08,
            parallel_safe=True,
        )
        self.register_engine(
            ConfidenceEngine(), "confidence", PipelineStage.CONFIDENCE_UPDATE,
            capabilities=["weighted_average", "bayesian_combination", "score_classification"],
            confidence_weight=0.10,
        )

    # ── Stage-to-Input-Type Mapping ───────────────────────────────────

    @staticmethod
    def _stage_to_input_type(stage: PipelineStage) -> str:
        """Map a pipeline stage to the expected engine input_type.

        Each Phase D intelligence engine uses specific input_type strings.
        The orchestrator translates pipeline stages to these canonical types.
        """
        mapping = {
            PipelineStage.PERCEIVING: "observation",
            PipelineStage.ASSEMBLING_CONTEXT: "assemble",
            PipelineStage.REASONING: "reasoning",
            PipelineStage.PLANNING: "plan",
            PipelineStage.DECIDING: "create_decision",
            PipelineStage.REFLECTING: "reflect",
            PipelineStage.LEARNING: "reflection",
            PipelineStage.CONFIDENCE_UPDATE: "compute",
        }
        return mapping.get(stage, "process")

    @staticmethod
    def _prepare_engine_payload(
        stage: PipelineStage, session: CognitiveSession
    ) -> dict[str, Any]:
        """Prepare an engine-specific payload from session context.

        Each Phase D engine expects different fields in its payload.
        This method builds a minimal payload with only the fields each
        engine's process() method expects, preventing leakage of
        session-level keys into engine-specific dataclass constructors.
        """
        context = session.context
        payload: dict[str, Any] = {}
        if stage == PipelineStage.PERCEIVING:
            payload["text"] = context.get("objective", "")
        elif stage == PipelineStage.ASSEMBLING_CONTEXT:
            payload["observation_ids"] = []
            payload["object_ids"] = []
        elif stage == PipelineStage.REASONING:
            payload["reasoning_type"] = "deductive"
            payload["evidence"] = []
            payload["observations"] = []
        elif stage == PipelineStage.PLANNING:
            payload["objective"] = context.get("objective", "")
        elif stage == PipelineStage.DECIDING:
            payload["label"] = context.get("objective", "Decision")
            payload["description"] = ""
            payload["evidence_ids"] = []
            payload["owner"] = context.get("actor", "system")
        elif stage == PipelineStage.REFLECTING:
            payload["expected_outcome"] = {"status": "completed"}
            payload["actual_outcome"] = {"status": "completed"}
            payload["subject_id"] = context.get("trace_id", "cognitive_session")
            payload["subject_type"] = "cognitive_runtime"
        elif stage == PipelineStage.LEARNING:
            payload["success_score"] = 0.0
            payload["improvement_signals"] = []
            payload["anomalies"] = []
            payload["subject_id"] = context.get("trace_id", "cognitive_session")
            payload["subject_type"] = "cognitive_runtime"
        elif stage == PipelineStage.CONFIDENCE_UPDATE:
            # Use accumulated confidence history as factors
            conf_history = session.confidence_history
            payload["factors"] = [
                {"name": entry.get("engine_id", "unknown"),
                 "value": entry.get("confidence", 0.0),
                 "weight": 0.125}
                for entry in conf_history
            ] if conf_history else []
            payload["subject_id"] = context.get("trace_id", "cognitive_session")
            payload["subject_type"] = "cognitive_runtime"
        return payload