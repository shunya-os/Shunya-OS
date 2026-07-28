"""SHUNYA Perception Engine — In-Memory Implementation.

The PerceptionEngine is the entry point into the Intelligence Runtime. It
receives raw signals from the world (events, messages, state changes) and
transforms them into structured Observations that downstream engines consume.

**Processing Pipeline:**

    Input ──► Perception Engine
                   │
                   ├── 1. Validate input schema
                   ├── 2. Enrich with source metadata
                   ├── 3. Classify input type
                   ├── 4. Assign priority
                   ├── 5. Compute confidence
                   ├── 6. Route to Context Assembly (via event bus)
                   └── 7. Record Observation

**Deterministic Work** (always local):
    - Input schema validation
    - Source metadata extraction
    - Input classification (by type rules)
    - Priority assignment
    - Confidence computation

**AI-Assisted Work** (via escalation):
    - Free-text intent extraction (if input is unstructured)
    - Entity recognition from text

**Integration:**
    - Subscribes to `core/event/` for incoming events
    - Emits observations via the event bus
    - Receives raw signals through `process()` or via event subscription

References:
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §3 (Engine Contract)
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §5 (Perception Engine)
    - docs/canon/07_ai_canon.md §5 (Observer Engine)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from core.intelligence.perception.models import (
    EngineInput,
    EngineOutput,
    EscalationResult,
    InputType,
    Observation,
    ObservationStatus,
    PerceptionPriority,
    SourceMetadata,
    _now_iso,
)

logger = logging.getLogger(__name__)


# ── Intelligence Engine interface ──────────────────────────────────────────────


class IntelligenceEngine:
    """Abstract interface that every Intelligence Engine implements.

    All eight engines (Perception, Context Assembly, Reasoning, Planning,
    Decision, Reflection, Learning, Confidence) conform to this contract.

    Subclasses override ``process()``, ``escalate()``, ``get_capabilities()``,
    and ``health_check()``.
    """

    engine_id: str = ""
    """Unique identifier for this engine instance."""

    engine_type: str = ""
    """Canonical engine type string (e.g., 'perception', 'context_assembly')."""

    async def process(self, input_data: EngineInput) -> EngineOutput:
        """Process an input and return an output.

        This is the primary entry point. The method is always deterministic
        unless escalation is triggered, in which case ``process()`` calls
        ``escalate()`` internally.

        Args:
            input_data: The canonical engine input envelope.

        Returns:
            An ``EngineOutput`` with the processed result.

        Raises:
            NotImplementedError: Subclasses must implement this method.
        """
        raise NotImplementedError

    def escalate(self, input_data: EngineInput) -> EscalationResult:
        """Bridge to external AI inference.

        Called when deterministic computation yields confidence below the
        engine's threshold. The escalation bridge packages the input into
        a prompt suitable for an LLM or other AI provider.

        Args:
            input_data: The input that fell below the confidence threshold.

        Returns:
            An ``EscalationResult`` with the packaged prompt and context.
        """
        raise NotImplementedError

    def get_capabilities(self) -> list[str]:
        """Return a list of capability strings describing this engine.

        Returns:
            A list of strings, each identifying a specific capability.
        """
        raise NotImplementedError

    def health_check(self) -> dict[str, Any]:
        """Return engine health status.

        Returns:
            A dict with at minimum ``status`` ('healthy' | 'degraded' | 'down'),
            ``engine_id``, and ``engine_type``.
        """
        raise NotImplementedError


# ── Input schema (validation rules) ────────────────────────────────────────────


_VALIDATED_FIELDS: dict[str, type] = {
    "input_type": str,
    "payload": dict,
}

_REQUIRED_PAYLOAD_KEYS: list[str] = [
    "value",
    "timestamp",
]

# ── Classification rules ───────────────────────────────────────────────────────


def _classify_by_payload(input_type_str: str, payload: dict[str, Any]) -> str:
    """Apply heuristic rules to classify the input type from payload structure.

    This is the deterministic classification logic. Rules are evaluated in
    order; the first match wins. If no rule matches, the input_type is
    returned as-is (which may be ``UNKNOWN``).

    Args:
        input_type_str: The raw or initial input type string.
        payload: The input payload to analyse.

    Returns:
        A classified ``InputType`` value string.
    """
    # Check for timer/cron triggers
    if "trigger_type" in payload and payload.get("trigger_type") == "timer":
        return InputType.TIMER_TRIGGER.value

    # Check for sensor readings
    if "sensor_id" in payload or "measurement" in payload:
        return InputType.SENSOR_READING.value

    # Check for system alerts
    if payload.get("severity") in ("critical", "warning", "info") and input_type_str == InputType.SYSTEM_EVENT.value:
        return InputType.SYSTEM_ALERT.value

    # Check for external callbacks
    if "callback_url" in payload or "webhook_id" in payload:
        return InputType.EXTERNAL_CALLBACK.value

    # Check for external data ingest
    if "batch_size" in payload or "ingest_source" in payload:
        return InputType.EXTERNAL_DATA_INGEST.value

    # Check for state changes
    if "previous_state" in payload or "state_diff" in payload:
        return InputType.SYSTEM_STATE_CHANGE.value

    # Check for user messages
    if "message" in payload or "text" in payload:
        if "command" in payload and payload.get("command"):
            return InputType.USER_COMMAND.value
        if "query" in payload or payload.get("is_query"):
            return InputType.USER_QUERY.value
        return InputType.USER_MESSAGE.value

    # Return the original if nothing matched
    return input_type_str


# ── Priority rules ─────────────────────────────────────────────────────────────


def _assign_priority(input_type: str, payload: dict[str, Any]) -> str:
    """Assign a priority level based on input type and payload content.

    Priority assignment is deterministic and rule-based.

    Args:
        input_type: The classified InputType value.
        payload: The input payload.

    Returns:
        A ``PerceptionPriority`` value string.
    """
    # Critical priority
    severity = payload.get("severity", "")
    if severity == "critical":
        return PerceptionPriority.CRITICAL.value
    if input_type == InputType.SYSTEM_ALERT.value:
        return PerceptionPriority.HIGH.value

    # High priority
    if input_type in (
        InputType.USER_COMMAND.value,
        InputType.USER_QUERY.value,
    ):
        return PerceptionPriority.HIGH.value

    # Low priority
    if input_type in (
        InputType.TIMER_TRIGGER.value,
        InputType.SENSOR_READING.value,
        InputType.EXTERNAL_DATA_INGEST.value,
    ):
        return PerceptionPriority.LOW.value

    # Default
    return PerceptionPriority.NORMAL.value


# ── Confidence computation ─────────────────────────────────────────────────────


def _compute_observation_confidence(
    source_reliability: float,
    timeliness: float,
    classification_certainty: float = 0.9,
) -> tuple[float, dict[str, float]]:
    """Compute the deterministic confidence score for an observation.

    Formula (from Intelligence Runtime Canon §12.2):
        confidence = W_s * source_reliability + W_t * timeliness + W_c * classification_certainty

    Where:
        W_s = 0.40 (source reliability weight)
        W_t = 0.25 (timeliness weight)
        W_c = 0.35 (classification certainty weight)

    Args:
        source_reliability: Reliability of the data source [0, 1].
        timeliness: How recent/current the input is [0, 1].
        classification_certainty: How certain the classification is [0, 1].
            Defaults to 0.9 for deterministic rule-based classification.

    Returns:
        A tuple of (confidence, confidence_factors dict).
    """
    W_SOURCE = 0.40
    W_TIMELINESS = 0.25
    W_CLASSIFICATION = 0.35

    confidence = (
        W_SOURCE * source_reliability
        + W_TIMELINESS * timeliness
        + W_CLASSIFICATION * classification_certainty
    )
    confidence = max(0.0, min(1.0, confidence))

    factors: dict[str, float] = {
        "source_reliability": source_reliability,
        "timeliness": timeliness,
        "classification_certainty": classification_certainty,
        "source_weight": W_SOURCE,
        "timeliness_weight": W_TIMELINESS,
        "classification_weight": W_CLASSIFICATION,
    }
    return round(confidence, 6), factors


def _compute_timeliness(payload: dict[str, Any]) -> float:
    """Compute the timeliness factor from the payload timestamp.

    Timeliness decays linearly from 1.0 (now) to 0.0 (3600+ seconds old).

    Args:
        payload: The input payload, possibly containing a 'timestamp' key.

    Returns:
        A float in [0, 1] representing how timely the input is.
    """
    if not payload:
        return 1.0
    raw_ts = payload.get("timestamp") or ""
    if not raw_ts:
        return 1.0
    try:
        from datetime import datetime, timezone

        event_time = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_seconds = (now - event_time).total_seconds()
        # Decay from 1.0 at t=0 to 0.0 at t=3600s (1 hour)
        timeliness = max(0.0, 1.0 - (age_seconds / 3600.0))
        return round(timeliness, 6)
    except (ValueError, TypeError):
        return 1.0


# ── PerceptionEngine ────────────────────────────────────────────────────────────


class PerceptionEngine(IntelligenceEngine):
    """In-memory Perception Engine — transforms raw signals into Observations.

    The PerceptionEngine is the first engine in the Intelligence Runtime
    pipeline. It implements the full perception pipeline:

    1. **Validate** — Check input schema and required fields
    2. **Enrich** — Attach source metadata (engine, type, reliability)
    3. **Classify** — Determine input type by rule-based classification
    4. **Prioritise** — Assign priority based on type and payload
    5. **Compute confidence** — Deterministic confidence from reliability,
       timeliness, and classification certainty
    6. **Emit observation** — Record the observation and trigger escalation
       if confidence is below threshold

    The engine is **single-threaded and in-memory** — suitable for prototyping,
    testing, and small-to-medium deployments. Production deployments should
    back observation storage with a persistent store.

    Usage::
        >>> import asyncio
        >>> engine = PerceptionEngine()
        >>> input_data = EngineInput(
        ...     input_type="observation",
        ...     payload={"value": "user_said_hello", "text": "Hello world"},
        ...     trace_id="trace_001",
        ... )
        >>> output = asyncio.run(engine.process(input_data))
        >>> output.deterministic
        True
        >>> output.confidence > 0.0
        True
    """

    engine_id: str = "perception_engine_001"
    """Unique identifier for this engine instance."""

    engine_type: str = "perception"
    """Canonical engine type."""

    # ── Constructor ──────────────────────────────────────────────────────────

    def __init__(self, engine_id: str | None = None) -> None:
        """Initialise the Perception Engine.

        Args:
            engine_id: Optional override for the engine ID. Auto-generated
                if omitted.
        """
        if engine_id:
            self.engine_id = engine_id

        # Observation store: observation_id -> Observation
        self._observations: dict[str, Observation] = {}

        # Index by trace_id for correlation queries
        self._observations_by_trace: dict[str, list[str]] = {}

        # Index by input_type for type-scoped queries
        self._observations_by_type: dict[str, list[str]] = {}

        # Index by status for lifecycle queries
        self._observations_by_status: dict[str, list[str]] = {}

        logger.info(
            "PerceptionEngine initialised [engine_id=%s]",
            self.engine_id,
        )

    # ── IntelligenceEngine contract ──────────────────────────────────────────

    async def process(self, input_data: EngineInput) -> EngineOutput:
        """Process a raw input through the full perception pipeline.

        The pipeline is fully deterministic unless the computed confidence
        falls below the input's confidence threshold, in which case
        ``escalate()`` is called to request AI-assisted interpretation.

        Args:
            input_data: The canonical engine input envelope. The ``payload``
                must be a non-empty dict; ``input_type`` must be a non-empty
                string.

        Returns:
            An ``EngineOutput`` containing the Observation as its payload,
            along with the computed confidence and processing metadata.

        Raises:
            ValueError: If the input payload is empty or missing required keys.
        """
        start_time = time.monotonic()
        trace_id = input_data.trace_id or _now_iso()

        logger.debug(
            "PerceptionEngine processing input [trace_id=%s, type=%s]",
            trace_id,
            input_data.input_type,
        )

        # ── Step 1: Validate ──────────────────────────────────────────────
        payload = self._validate(input_data)

        # ── Step 2: Enrich ────────────────────────────────────────────────
        source_meta = self._enrich(input_data, payload)

        # ── Step 3: Classify ──────────────────────────────────────────────
        classified_type, matched_rules = self._classify(
            input_data.input_type, payload
        )

        # ── Step 4: Prioritise ────────────────────────────────────────────
        priority = _assign_priority(classified_type, payload)

        # ── Step 5: Compute confidence ────────────────────────────────────
        timeliness = _compute_timeliness(payload)
        classification_certainty = 0.9  # Rule-based = high certainty
        confidence, confidence_factors = _compute_observation_confidence(
            source_reliability=source_meta.source_reliability,
            timeliness=timeliness,
            classification_certainty=classification_certainty,
        )

        # ── Step 6: Create Observation ────────────────────────────────────
        observation = Observation(
            input_type=classified_type,
            payload=payload,
            source_metadata=source_meta,
            priority=priority,
            confidence=confidence,
            trace_id=trace_id,
            status=ObservationStatus.CLASSIFIED.value,
            classification_rules=matched_rules,
        )

        # ── Step 7: Check threshold and escalate if needed ───────────────
        threshold = input_data.confidence_threshold
        escalation_used = False
        deterministic = True
        if confidence < threshold:
            logger.info(
                "Confidence %.4f below threshold %.4f — escalating [trace_id=%s]",
                confidence,
                threshold,
                trace_id,
            )
            # The escalation bridge packages the input for an AI provider
            escalation = self.escalate(input_data)
            escalation_used = True
            deterministic = False
            # After escalation, we update the observation metadata
            observation.metadata["escalation_prompt"] = escalation.prompt
            observation.metadata["escalation_context"] = escalation.context

        # ── Step 8: Store observation ────────────────────────────────────
        self._store_observation(observation)

        # ── Step 9: Build output ─────────────────────────────────────────
        processing_time = (time.monotonic() - start_time) * 1000.0

        output = EngineOutput(
            output_type="observation",
            payload=observation.to_dict(),
            confidence=confidence,
            confidence_factors=confidence_factors,
            deterministic=deterministic,
            trace_id=trace_id,
            escalation_used=escalation_used,
            processing_time_ms=round(processing_time, 3),
        )

        logger.info(
            "Observation %s processed (type=%s, conf=%.4f, det=%s, time=%.1fms) "
            "[trace_id=%s]",
            observation.observation_id,
            classified_type,
            confidence,
            deterministic,
            processing_time,
            trace_id,
        )

        return output

    def escalate(self, input_data: EngineInput) -> EscalationResult:
        """Bridge to external AI inference for perception tasks.

        Called when deterministic classification yields confidence below
        threshold. Packages the raw input into a structured prompt suitable
        for an LLM or other AI provider.

        This method is a **bridge** — it constructs the prompt and context.
        The actual invocation of an AI provider is handled by the escalation
        policy layer (outside this engine).

        Args:
            input_data: The input that fell below the confidence threshold.

        Returns:
            An ``EscalationResult`` with the packaged prompt and context.
        """
        trace_id = input_data.trace_id or _now_iso()
        prompt_parts: list[str] = [
            "## Perception Task",
            "",
            "The following input could not be classified with sufficient confidence.",
            "Please analyse the input and determine:",
            "1. The most likely input type (from the InputType taxonomy)",
            "2. The intended meaning of the input",
            "3. Any entities or concepts mentioned",
            "4. The appropriate priority level",
            "",
            f"### Raw Input Type: {input_data.input_type}",
            f"### Payload: {input_data.payload}",
        ]
        if input_data.context:
            prompt_parts.append(f"### Context: {input_data.context}")

        prompt = "\n".join(prompt_parts)

        context: dict[str, Any] = {
            "escalation_reason": "confidence_below_threshold",
            "input_type": input_data.input_type,
            "confidence_threshold": input_data.confidence_threshold,
            "engine_id": self.engine_id,
        }
        if input_data.context:
            context["provided_context"] = input_data.context

        logger.info(
            "Escalation bridge prepared [trace_id=%s, prompt_len=%d]",
            trace_id,
            len(prompt),
        )

        return EscalationResult(
            input_type=input_data.input_type,
            prompt=prompt,
            context=context,
            trace_id=trace_id,
        )

    def get_capabilities(self) -> list[str]:
        """Return a list of capability strings for this engine.

        Returns:
            A list of capability identifiers.
        """
        return [
            "input_validation",
            "source_enrichment",
            "input_classification",
            "priority_assignment",
            "confidence_computation",
            "observation_creation",
            "escalation_bridge",
        ]

    def health_check(self) -> dict[str, Any]:
        """Return engine health status.

        Returns:
            A dict with status, engine_id, engine_type, and store stats.
        """
        total_observations = len(self._observations)
        return {
            "status": "healthy",
            "engine_id": self.engine_id,
            "engine_type": self.engine_type,
            "total_observations": total_observations,
            "observations_by_status": {
                status: len(ids)
                for status, ids in self._observations_by_status.items()
            },
        }

    # ── Pipeline Steps ──────────────────────────────────────────────────────

    def _validate(self, input_data: EngineInput) -> dict[str, Any]:
        """Validate the input schema and payload.

        Args:
            input_data: The engine input to validate.

        Returns:
            The validated payload dict.

        Raises:
            ValueError: If the payload is empty or missing required keys.
        """
        if not isinstance(input_data.payload, dict):
            raise TypeError(
                f"Input payload must be a dict, got {type(input_data.payload).__name__}"
            )
        if not input_data.payload:
            raise ValueError(
                "Input payload is empty. A non-empty payload is required."
            )
        return input_data.payload

    def _enrich(
        self,
        input_data: EngineInput,
        payload: dict[str, Any],
    ) -> SourceMetadata:
        """Enrich the input with source metadata.

        Extracts provenance information from the input envelope and payload
        to build a ``SourceMetadata`` record.

        Args:
            input_data: The engine input being processed.
            payload: The validated payload dict.

        Returns:
            A populated ``SourceMetadata`` instance.
        """
        source_engine = payload.get("source_engine", input_data.context.get("source_engine", "") if input_data.context else "")
        source_type = payload.get("source_type", "")
        source_reliability = float(payload.get("source_reliability", 0.5))
        source_reliability = max(0.0, min(1.0, source_reliability))
        captured_at = payload.get("timestamp", _now_iso())

        return SourceMetadata(
            source_engine=source_engine,
            source_type=source_type,
            source_reliability=source_reliability,
            captured_at=captured_at,
        )

    def _classify(
        self,
        raw_type: str,
        payload: dict[str, Any],
    ) -> tuple[str, list[str]]:
        """Classify the input into an InputType using deterministic rules.

        Applies rule-based classification heuristics on the payload structure
        to determine the most specific InputType.

        Args:
            raw_type: The initial input type string from the envelope.
            payload: The validated payload dict.

        Returns:
            A tuple of (classified_type_string, list_of_matched_rule_names).
        """
        matched_rules: list[str] = []

        # Step 1: Normalise the raw type
        normalised = InputType.from_string(raw_type)

        # Step 2: Apply payload-based classification
        classified = _classify_by_payload(normalised.value, payload)

        # Step 3: Record which rules matched
        if classified != normalised.value:
            matched_rules.append(f"payload_heuristic:{classified}")
        else:
            matched_rules.append(f"direct_type:{classified}")

        return classified, matched_rules

    # ── Storage ────────────────────────────────────────────────────────────

    def _store_observation(self, observation: Observation) -> None:
        """Store an observation in the in-memory store and indexes.

        Args:
            observation: The observation to store.
        """
        oid = observation.observation_id
        self._observations[oid] = observation
        self._observations_by_trace.setdefault(observation.trace_id, []).append(oid)
        self._observations_by_type.setdefault(observation.input_type, []).append(oid)
        self._observations_by_status.setdefault(observation.status, []).append(oid)

    # ── Query Methods ───────────────────────────────────────────────────────

    def get_observation(self, observation_id: str) -> Observation | None:
        """Retrieve a single observation by ID.

        Args:
            observation_id: The UUID v7 of the observation.

        Returns:
            The Observation if found, or None.
        """
        return self._observations.get(observation_id)

    def get_observations_by_trace(self, trace_id: str) -> list[Observation]:
        """Retrieve all observations for a given trace ID.

        Args:
            trace_id: The correlation trace ID.

        Returns:
            List of Observations for that trace, in creation order.
        """
        ids = self._observations_by_trace.get(trace_id, [])
        return [self._observations[oid] for oid in ids if oid in self._observations]

    def get_observations_by_type(
        self,
        input_type: InputType | str,
        limit: int | None = None,
    ) -> list[Observation]:
        """Retrieve observations by classified input type.

        Args:
            input_type: The InputType (enum or string) to filter by.
            limit: Maximum number of results to return.

        Returns:
            List of matching Observations.
        """
        if isinstance(input_type, InputType):
            input_type = input_type.value
        ids = self._observations_by_type.get(input_type, [])
        result = [self._observations[oid] for oid in ids if oid in self._observations]
        if limit is not None:
            result = result[:limit]
        return result

    def get_observations_by_status(
        self,
        status: ObservationStatus | str,
        limit: int | None = None,
    ) -> list[Observation]:
        """Retrieve observations by lifecycle status.

        Args:
            status: The ObservationStatus (enum or string) to filter by.
            limit: Maximum number of results to return.

        Returns:
            List of matching Observations.
        """
        if isinstance(status, ObservationStatus):
            status = status.value
        ids = self._observations_by_status.get(status, [])
        result = [self._observations[oid] for oid in ids if oid in self._observations]
        if limit is not None:
            result = result[:limit]
        return result

    def count_observations(self) -> int:
        """Return the total number of stored observations.

        Returns:
            Observation count.
        """
        return len(self._observations)
