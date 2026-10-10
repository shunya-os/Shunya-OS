"""Learning & Memory — observation → memory ingestion, feedback loop, and
controlled learning.

Phase 5 components:
  5.1: Observation → memory ingestion loop-closing
  5.2: Wire 8 Intelligence Engines into feedback loop
  5.3: Controlled learning loop (background review of completed outcomes)
  5.4: User feedback signals (accepted/rejected recommendation)
  5.5: Connect evidence system to memory + knowledge
  5.6: Execution outcome → memory learning
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from .types import MemoryType, MemoryEntry
from .memory import MemoryEngine
from .learning_loop import ControlledLearningLoop, get_learning_loop

logger = logging.getLogger(__name__)


# ── Feedback Types (Phase 5.4) ────────────────────────────────────────────


@dataclass
class UserFeedback:
    """User feedback on a recommendation or action.

    Stored in the app/feedback/ module persistence layer.
    """
    feedback_id: str = ""
    signal_id: str = ""
    accepted: bool = False
    comment: str = ""
    identity_id: str = ""
    tenant_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "feedback_id": self.feedback_id,
            "signal_id": self.signal_id,
            "accepted": self.accepted,
            "comment": self.comment,
            "identity_id": self.identity_id,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at,
        }


# ── Outcome → Memory ingestion (Phase 5.1 + 5.6) ─────────────────────────


class OutcomeMemoryIngester:
    """Extracts key information from an Outcome and stores it as memory.

    Phase 5.1: When an Outcome is created, extract its intention, state, and
    result, then persist as a memory entry via the MemoryEngine.

    Phase 5.6: Execution outcome → memory learning. Stores the outcome's final
    state as a learning signal in long-term memory so future decisions can
    reference past execution results.
    """

    def __init__(self, memory_engine: MemoryEngine | None = None):
        self._memory = memory_engine

    def set_memory_engine(self, engine: MemoryEngine) -> None:
        self._memory = engine

    def get_memory_engine(self) -> MemoryEngine | None:
        return self._memory

    def ingest_outcome(self, outcome_id: str, intention: str,
                       state: dict | None = None,
                       identity_id: str = "", tenant_id: str = "") -> bool:
        """Store an outcome as a memory entry.

        Called when an Outcome is persisted (e.g. from OutcomeRuntime.accept).
        Extracts the key attributes and stores them in long-term memory for
        future retrieval.
        """
        if not self._memory:
            logger.warning("OutcomeMemoryIngester: no memory engine wired — skipping %s", outcome_id)
            return False

        state = state or {}
        stage = state.get("stage", "pending")
        summary = state.get("final_summary", "")
        error = state.get("last_error", "")

        # Build a rich memory entry from the outcome
        content_parts = [
            f"Outcome: {outcome_id}",
            f"Intention: {intention}",
            f"Stage: {stage}",
        ]
        if summary:
            content_parts.append(f"Summary: {summary}")
        if error:
            content_parts.append(f"Error: {error}")

        content = "\n".join(content_parts)
        key = f"outcome_{outcome_id}"

        try:
            self._memory.store(
                key=key,
                content=content,
                memory_type=MemoryType.LONG_TERM,
                source="execution_outcome",
                confidence=0.8 if stage in ("completed", "fulfilled") else 0.5,
                identity_id=identity_id,
                tenant_id=tenant_id,
            )
            logger.info("Ingested outcome %s into memory (stage=%s)", outcome_id, stage)

            # Phase 5.6: Also feed into the controlled learning loop
            try:
                loop = get_learning_loop()
                if loop:
                    expected = state.get("expected_result", intention)
                    actual = summary or stage
                    loop.process_observation(
                        observation=intention,
                        expected_outcome=expected,
                        actual_outcome=actual,
                        identity_id=identity_id,
                        tenant_id=tenant_id,
                        source="outcome_memory_ingester",
                        metadata={"outcome_id": outcome_id, "stage": stage},
                    )
            except Exception as exc:
                logger.warning("Learning loop processing for %s failed: %s", outcome_id, exc)

            return True
        except Exception as exc:
            logger.warning("Failed to ingest outcome %s into memory: %s", outcome_id, exc)
            return False

    def ingest_execution_result(self, outcome_id: str, result: dict,
                                 identity_id: str = "", tenant_id: str = "") -> bool:
        """Ingest an execution result as a learning memory (Phase 5.6).

        Stores the result summary and outcome as a business memory record
        so future similar executions can reference past performance.
        """
        if not self._memory:
            return False

        status = result.get("status", "unknown")
        result_str = result.get("result", {})
        summary = result_str.get("summary", "") if isinstance(result_str, dict) else str(result_str)

        content = (
            f"Execution Result — Outcome: {outcome_id}\n"
            f"Status: {status}\n"
            f"Summary: {summary}\n"
        )

        key = f"execution_result_{outcome_id}"
        try:
            self._memory.store(
                key=key,
                content=content,
                memory_type=MemoryType.BUSINESS,
                source="execution_result",
                confidence=0.7 if status in ("success", "completed") else 0.4,
                identity_id=identity_id,
                tenant_id=tenant_id,
            )
            return True
        except Exception as exc:
            logger.warning("Failed to ingest execution result %s: %s", outcome_id, exc)
            return False


# ── 8 Intelligence Engines feedback loop (Phase 5.2) ─────────────────────


class IntelligenceFeedbackLoop:
    """Wires the 8 Intelligence Engines into the learning feedback loop.

    Each engine produces observations that feed into the ControlledLearningLoop.
    The feedback loop is: engine → observation → evaluation → learning signal
    → governed memory update → future decision improvement.
    """

    def __init__(self, learning_loop: ControlledLearningLoop | None = None):
        self._loop = learning_loop or get_learning_loop()
        self._engines: dict[str, Callable] = {}

    def register_engine(self, name: str, provider: Callable) -> None:
        """Register an intelligence engine provider.

        The provider receives a query/context and returns observations as
        a list of dicts with keys: observation, expected_outcome, actual_outcome.
        """
        self._engines[name] = provider

    def run_feedback_cycle(self, query: str = "",
                           identity_id: str = "", tenant_id: str = "") -> list[dict]:
        """Run a full feedback cycle across all registered engines.

        Each engine produces observations; each observation becomes a learning
        signal via the ControlledLearningLoop.
        """
        results = []
        for name, provider in self._engines.items():
            try:
                observations = provider(query, identity_id=identity_id, tenant_id=tenant_id)
                if not observations:
                    continue
                for obs in observations:
                    signal = self._loop.process_observation(
                        observation=obs.get("observation", ""),
                        expected_outcome=obs.get("expected_outcome", ""),
                        actual_outcome=obs.get("actual_outcome", ""),
                        identity_id=identity_id,
                        tenant_id=tenant_id,
                        source=f"intelligence_engine/{name}",
                        metadata={"engine": name, **obs.get("metadata", {})},
                    )
                    results.append({
                        "engine": name,
                        "signal_id": signal.signal_id,
                        "evaluation": signal.evaluation,
                        "confidence": signal.confidence,
                    })
            except Exception as exc:
                logger.warning("Feedback cycle engine %s failed: %s", name, exc)
                results.append({"engine": name, "error": str(exc)})

        return results


# ── Controlled Learning Loop — background review (Phase 5.3) ──────────────


class BackgroundLearningReviewer:
    """Periodically reviews completed outcomes and stores learnings.

    Phase 5.3: Runs as a background thread (or via APScheduler) to periodically
    scan for completed outcomes that haven't been reviewed yet, extract key
    patterns, and persist learning signals.

    This is a governed loop — it does NOT modify code, prompts, or model
    weights. It only stores observations as durable memory entries.
    """

    def __init__(self, ingester: OutcomeMemoryIngester | None = None,
                 loop: ControlledLearningLoop | None = None,
                 interval_seconds: int = 3600):
        self._ingester = ingester or OutcomeMemoryIngester()
        self._loop = loop or get_learning_loop()
        self._interval = interval_seconds
        self._thread: threading.Thread | None = None
        self._running = False
        self._reviewed_outcomes: set[str] = set()

    def set_ingester(self, ingester: OutcomeMemoryIngester) -> None:
        self._ingester = ingester

    def set_loop(self, loop: ControlledLearningLoop) -> None:
        self._loop = loop

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background review thread."""
        if self._running:
            logger.warning("BackgroundLearningReviewer already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True,
                                         name="learning-reviewer")
        self._thread.start()
        logger.info("BackgroundLearningReviewer started (interval=%ds)", self._interval)

    def stop(self) -> None:
        """Stop the background review thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("BackgroundLearningReviewer stopped")

    def is_running(self) -> bool:
        return self._running

    # ── Internal loop ─────────────────────────────────────────────────────

    def _run_loop(self) -> None:
        while self._running:
            try:
                self._review_completed_outcomes()
            except Exception as exc:
                logger.warning("Learning review cycle failed: %s", exc)
            # Sleep in 1-second increments so stop() is responsive
            for _ in range(self._interval):
                if not self._running:
                    return
                threading.Event().wait(1)

    def _review_completed_outcomes(self) -> None:
        """Scan for recently completed outcomes and process them.

        Queries the sh_outcomes table for outcomes in a completed/terminal
        state that haven't been reviewed yet.
        """
        try:
            from app import db
            from app.execution.models import Outcome

            # Find outcomes in terminal stages that haven't been reviewed
            outcomes = Outcome.query.order_by(
                Outcome.updated_at.desc()
            ).limit(50).all()

            for outcome in outcomes:
                if outcome.outcome_id in self._reviewed_outcomes:
                    continue

                state = outcome.state or {}
                stage = state.get("stage", "")
                if stage not in ("completed", "fulfilled", "failed", "cancelled"):
                    continue

                # Mark as reviewed immediately (idempotent)
                self._reviewed_outcomes.add(outcome.outcome_id)

                # Ingest as memory
                self._ingester.ingest_outcome(
                    outcome_id=outcome.outcome_id,
                    intention=outcome.intention,
                    state=state,
                    identity_id=outcome.identity_id,
                )

                # Feed into learning loop
                expected = state.get("expected_result", outcome.intention)
                actual = state.get("final_summary", stage)
                self._loop.process_observation(
                    observation=outcome.intention,
                    expected_outcome=expected,
                    actual_outcome=actual,
                    identity_id=outcome.identity_id,
                    source="background_learning_review",
                    metadata={
                        "outcome_id": outcome.outcome_id,
                        "stage": stage,
                    },
                )

                logger.info(
                    "Background review processed outcome %s (stage=%s)",
                    outcome.outcome_id, stage,
                )

            # Keep the reviewed set bounded
            if len(self._reviewed_outcomes) > 1000:
                self._reviewed_outcomes = set(list(self._reviewed_outcomes)[-500:])

        except Exception as exc:
            logger.warning("Background outcome review failed: %s", exc)

    def get_reviewed_count(self) -> int:
        return len(self._reviewed_outcomes)


# ── Evidence → Memory + Knowledge bridge (Phase 5.5) ─────────────────────


class EvidenceMemoryBridge:
    """Connects the evidence system to memory and knowledge.

    Phase 5.5: When evidence is gathered during reasoning, stores high-
    confidence evidence as memory entries so it can be retrieved in future
    sessions without re-fetching from the original source.
    """

    def __init__(self, memory_engine: MemoryEngine | None = None):
        self._memory = memory_engine

    def set_memory_engine(self, engine: MemoryEngine) -> None:
        self._memory = engine

    def persist_evidence_as_memory(self, evidence: list[dict],
                                    query: str = "",
                                    identity_id: str = "",
                                    tenant_id: str = "") -> int:
        """Store evidence items as long-term memory entries.

        Only stores evidence with confidence >= 0.7 and relevance >= 0.6
        to avoid polluting memory with low-quality noise.
        """
        if not self._memory:
            return 0

        stored_count = 0
        for item in evidence:
            confidence = float(item.get("confidence", 0))
            relevance = float(item.get("relevance", 0))

            if confidence < 0.7 or relevance < 0.6:
                continue

            source = item.get("source", "unknown")
            content = item.get("content", "")
            if not content:
                continue

            key = f"evidence_{source}_{hash(content) % 10000000:07d}"

            try:
                self._memory.store(
                    key=key,
                    content=content,
                    memory_type=MemoryType.LONG_TERM,
                    source=f"evidence_bridge/{source}",
                    confidence=confidence,
                    identity_id=identity_id,
                    tenant_id=tenant_id,
                )
                stored_count += 1
            except Exception as exc:
                logger.debug("Failed to persist evidence %s: %s", key, exc)

        if stored_count > 0:
            logger.info("Persisted %d evidence items as memory (query=%s)", stored_count, query[:60])

        return stored_count


# ── Singleton Support ─────────────────────────────────────────────────────

_INGESTER: OutcomeMemoryIngester | None = None
_REVIEWER: BackgroundLearningReviewer | None = None
_FEEDBACK_LOOP: IntelligenceFeedbackLoop | None = None
_EVIDENCE_BRIDGE: EvidenceMemoryBridge | None = None


def get_outcome_ingester() -> OutcomeMemoryIngester:
    global _INGESTER
    if _INGESTER is None:
        _INGESTER = OutcomeMemoryIngester()
    return _INGESTER


def get_background_reviewer() -> BackgroundLearningReviewer:
    global _REVIEWER
    if _REVIEWER is None:
        _REVIEWER = BackgroundLearningReviewer()
    return _REVIEWER


def get_feedback_loop() -> IntelligenceFeedbackLoop:
    global _FEEDBACK_LOOP
    if _FEEDBACK_LOOP is None:
        _FEEDBACK_LOOP = IntelligenceFeedbackLoop()
    return _FEEDBACK_LOOP


def get_evidence_bridge() -> EvidenceMemoryBridge:
    global _EVIDENCE_BRIDGE
    if _EVIDENCE_BRIDGE is None:
        _EVIDENCE_BRIDGE = EvidenceMemoryBridge()
    return _EVIDENCE_BRIDGE


def reset_learning_components() -> None:
    """Reset all learning singletons (testing)."""
    global _INGESTER, _REVIEWER, _FEEDBACK_LOOP, _EVIDENCE_BRIDGE
    if _REVIEWER:
        _REVIEWER.stop()
    _INGESTER = None
    _REVIEWER = None
    _FEEDBACK_LOOP = None
    _EVIDENCE_BRIDGE = None


# ── Wire convenience — called from integration.ensure_runtime() ───────────


def ensure_learning_system(memory_engine: MemoryEngine | None = None) -> dict[str, Any]:
    """Wire all Phase 5 learning components.

    Called once at app startup. Wires the memory engine into all components
    and starts the background reviewer.

    Returns a status dict showing which components were wired.
    """
    from .memory import MemoryEngine as _ME

    memory = memory_engine or _ME()
    status: dict[str, Any] = {"memory_wired": False, "reviewer_started": False}

    # Wire OutcomeMemoryIngester
    ingester = get_outcome_ingester()
    ingester.set_memory_engine(memory)

    # Wire EvidenceMemoryBridge
    bridge = get_evidence_bridge()
    bridge.set_memory_engine(memory)
    status["memory_wired"] = True

    # Wire IntelligenceFeedbackLoop
    loop = get_feedback_loop()
    loop._loop = get_learning_loop()

    # Wire 8 Intelligence Engines as feedback providers
    engines = {
        "perception": _perception_engine_provider,
        "reasoning": _reasoning_engine_provider,
        "planning": _planning_engine_provider,
        "decision": _decision_engine_provider,
        "execution": _execution_engine_provider,
        "memory": _memory_engine_provider,
        "learning": _learning_engine_provider,
        "awareness": _awareness_engine_provider,
    }
    for name, provider in engines.items():
        loop.register_engine(name, provider)

    # Start background reviewer
    reviewer = get_background_reviewer()
    reviewer.set_ingester(ingester)
    reviewer.set_loop(get_learning_loop())
    if not reviewer.is_running():
        reviewer.start()
        status["reviewer_started"] = True

    logger.info("Learning system fully wired: memory=%s, reviewer=%s",
                status["memory_wired"], status["reviewer_started"])

    return status


# ── 8 Intelligence Engine Providers (Phase 5.2) ──────────────────────────


def _perception_engine_provider(query: str, identity_id: str = "",
                                 tenant_id: str = "") -> list[dict]:
    """Perception engine: observes what data exists and its quality."""
    observations = []
    try:
        from app.intelligence.observation import get_store
        store = get_store()
        active = store.get_active() if hasattr(store, "get_active") else []
        observations.append({
            "observation": f"Perception: {len(active)} active observations",
            "expected_outcome": "data_quality_maintained",
            "actual_outcome": f"{len(active)} observations active",
        })
    except Exception:
        observations.append({
            "observation": "Perception engine unavailable",
            "expected_outcome": "observations_accessible",
            "actual_outcome": "unavailable",
        })
    return observations


def _reasoning_engine_provider(query: str, identity_id: str = "",
                                tenant_id: str = "") -> list[dict]:
    """Reasoning engine: evaluates trace quality."""
    observations = []
    try:
        from app.intelligence.models import ReasoningTrace
        recent = ReasoningTrace.query.order_by(
            ReasoningTrace.created_at.desc()
        ).limit(5).all()
        confidence_scores = [t.confidence_score for t in recent if t.confidence_score]
        avg_conf = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        observations.append({
            "observation": f"Reasoning: avg confidence {avg_conf:.2f} over {len(recent)} traces",
            "expected_outcome": "high_quality_reasoning",
            "actual_outcome": "good" if avg_conf >= 0.7 else "needs_improvement",
            "metadata": {"avg_confidence": avg_conf, "trace_count": len(recent)},
        })
    except Exception:
        pass
    return observations


def _planning_engine_provider(query: str, identity_id: str = "",
                               tenant_id: str = "") -> list[dict]:
    """Planning engine: evaluates plan execution quality."""
    observations = []
    try:
        from app.execution.models import Outcome
        recent = Outcome.query.order_by(Outcome.created_at.desc()).limit(10).all()
        error_count = sum(1 for o in recent if (o.state or {}).get("stage") == "error")
        observations.append({
            "observation": f"Planning: {error_count}/{len(recent)} recent outcomes in error",
            "expected_outcome": "error_free_execution",
            "actual_outcome": "errors_detected" if error_count > 0 else "clean",
            "metadata": {"error_count": error_count, "total": len(recent)},
        })
    except Exception:
        pass
    return observations


def _decision_engine_provider(query: str, identity_id: str = "",
                               tenant_id: str = "") -> list[dict]:
    """Decision engine: evaluates decision quality."""
    observations = []
    try:
        from app.intelligence.models import AnomalyRecord
        open_anomalies = AnomalyRecord.query.filter_by(status="open").count()
        observations.append({
            "observation": f"Decision: {open_anomalies} open anomalies requiring decisions",
            "expected_outcome": "timely_decision_making",
            "actual_outcome": "pending_decisions" if open_anomalies > 0 else "current",
            "metadata": {"open_anomalies": open_anomalies},
        })
    except Exception:
        pass
    return observations


def _execution_engine_provider(query: str, identity_id: str = "",
                                tenant_id: str = "") -> list[dict]:
    """Execution engine: evaluates execution success rate."""
    observations = []
    try:
        from app.execution.models import Outcome
        recent = Outcome.query.order_by(Outcome.created_at.desc()).limit(20).all()
        completed = sum(1 for o in recent if (o.state or {}).get("stage") in ("completed", "fulfilled"))
        success_rate = completed / len(recent) if recent else 0
        observations.append({
            "observation": f"Execution: {success_rate:.0%} success rate (last {len(recent)})",
            "expected_outcome": "high_execution_success",
            "actual_outcome": "good" if success_rate >= 0.8 else "needs_improvement",
            "metadata": {"success_rate": success_rate, "total": len(recent), "completed": completed},
        })
    except Exception:
        pass
    return observations


def _memory_engine_provider(query: str, identity_id: str = "",
                             tenant_id: str = "") -> list[dict]:
    """Memory engine: evaluates memory health."""
    observations = []
    try:
        from .memory import InMemoryMemoryRepository
        from .memory_db import DBMemoryRepository
        from . import get_runtime
        runtime = get_runtime()
        count = runtime.memory.count(identity_id=identity_id, tenant_id=tenant_id)
        observations.append({
            "observation": f"Memory: {count} entries for identity",
            "expected_outcome": "healthy_memory_store",
            "actual_outcome": "populated" if count > 0 else "empty",
            "metadata": {"memory_count": count},
        })
    except Exception:
        pass
    return observations


def _learning_engine_provider(query: str, identity_id: str = "",
                               tenant_id: str = "") -> list[dict]:
    """Learning engine: evaluates learning signal quality."""
    observations = []
    try:
        from app.intelligence.models import LearningEvent
        recent = LearningEvent.query.order_by(
            LearningEvent.created_at.desc()
        ).limit(10).all()
        positive = sum(1 for e in recent if e.outcome == "positive")
        total = len(recent)
        observations.append({
            "observation": f"Learning: {positive}/{total} recent learning events positive",
            "expected_outcome": "positive_learning_signals",
            "actual_outcome": "good" if positive >= total * 0.5 else "mixed",
            "metadata": {"positive": positive, "total": total},
        })
    except Exception:
        pass
    return observations


def _awareness_engine_provider(query: str, identity_id: str = "",
                                tenant_id: str = "") -> list[dict]:
    """Awareness engine: evaluates awareness of recent changes."""
    observations = []
    try:
        from app.signals.models import Signal
        from datetime import timedelta
        recent = Signal.query.filter(
            Signal.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).count()
        observations.append({
            "observation": f"Awareness: {recent} signals in the last 24h",
            "expected_outcome": "situational_awareness",
            "actual_outcome": "aware" if recent > 0 else "quiet",
            "metadata": {"signal_count_24h": recent},
        })
    except Exception:
        pass
    return observations

def start_learning_loop() -> None:
    """Start the background learning loop. Called from app factory (G3 Phase 5).

    Initializes all Phase 5 learning components: memory ingester, evidence
    bridge, feedback loop with 8 intelligence engines, and the background
    reviewer thread. Safe to call multiple times (idempotent).
    """
    try:
        ensure_learning_system()
        logger.info("G3 Phase 5: Learning loop started")
    except Exception as e:
        logger.warning("G3 Phase 5: Learning loop start failed: %s", e)
