"""Inference Orchestrator — the central routing and execution coordinator.

The orchestrator ties together the classification, policy, selection,
execution, and observation pipeline. Every inference request enters
through the orchestrator, flows through the five-stage pipeline, and
returns a structured response with full observability.

Pipeline:
    classify → policy → select → execute → observe
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from .execution import (
    ExecutionLayer,
    InferenceMessage,
    InferenceRequest,
    InferenceResult,
    ProviderConfig,
    resolve_provider_configs,
)
from .learning_router import LearningRouter, Recommendation, TelemetryRecord

logger = logging.getLogger(__name__)


# ── Orchestrator Data Types ─────────────────────────────────────────────────


@dataclass
class OrchestratorRequest:
    """A request entering the orchestrator pipeline."""
    input_text: str
    session_id: str = ""
    model: str = ""
    provider_hint: str = ""
    request_type: Literal["chat", "embedding", "tool_call"] = "chat"
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: str = ""
    conversation_history: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "input_text": self.input_text[:200],
            "session_id": self.session_id,
            "model": self.model,
            "provider_hint": self.provider_hint,
            "request_type": self.request_type,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "has_system_prompt": bool(self.system_prompt),
            "history_length": len(self.conversation_history),
        }


@dataclass
class PipelineStage:
    """Result of a single pipeline stage."""
    stage_name: str
    status: Literal["success", "skip", "error"]
    output: dict = field(default_factory=dict)
    duration_ms: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "stage": self.stage_name,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 1),
            "error": self.error,
        }


@dataclass
class OrchestratorResponse:
    """Structured response from the orchestrator pipeline."""
    request_id: str
    content: str
    model: str = ""
    provider: str = ""
    finish_reason: str = "stop"
    usage: dict = field(default_factory=dict)
    latency_ms: float = 0.0
    error: str | None = None
    pipeline: list[PipelineStage] = field(default_factory=list)
    recommendation: Recommendation | None = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "finish_reason": self.finish_reason,
            "usage": self.usage,
            "latency_ms": round(self.latency_ms, 1),
            "error": self.error,
            "pipeline": [s.to_dict() for s in self.pipeline],
            "recommendation": self.recommendation.to_dict() if self.recommendation else None,
            "timestamp": self.timestamp,
        }

    @property
    def success(self) -> bool:
        return self.error is None


# ── Classification Models ───────────────────────────────────────────────────


@dataclass
class ClassificationResult:
    """Result of the classify stage."""
    request_type: str = "chat"
    complexity: Literal["simple", "moderate", "complex"] = "simple"
    requires_tools: bool = False
    requires_streaming: bool = False
    confidence: float = 0.0
    detected_intent: str = ""

    def to_dict(self) -> dict:
        return {
            "request_type": self.request_type,
            "complexity": self.complexity,
            "requires_tools": self.requires_tools,
            "requires_streaming": self.requires_streaming,
            "confidence": round(self.confidence, 2),
            "detected_intent": self.detected_intent,
        }


@dataclass
class PolicyResult:
    """Result of the policy stage."""
    allowed_providers: list[str] = field(default_factory=list)
    max_cost: float = 0.0
    requires_audit: bool = False
    timeout_seconds: int = 60
    constraints: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "allowed_providers": self.allowed_providers,
            "max_cost": self.max_cost,
            "requires_audit": self.requires_audit,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class SelectionResult:
    """Result of the select stage."""
    provider: str = ""
    model: str = ""
    confidence: float = 0.0
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "confidence": round(self.confidence, 2),
            "reason": self.reason,
        }


# ── Pipeline ────────────────────────────────────────────────────────────────


class Pipeline:
    """The five-stage inference pipeline: classify → policy → select → execute → observe.

    Each stage is a discrete step that produces a structured result.
    Stages can be overridden or extended by subclassing.
    """

    def __init__(self, execution_layer: ExecutionLayer, learning_router: LearningRouter):
        self._execution = execution_layer
        self._router = learning_router

    def run(self, request: OrchestratorRequest) -> OrchestratorResponse:
        """Execute the full five-stage pipeline.

        Returns an OrchestratorResponse with per-stage timing and errors.
        """
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        stages: list[PipelineStage] = []
        overall_start = time.monotonic()

        # ── Stage 1: Classify ───────────────────────────────────────────
        stage_start = time.monotonic()
        try:
            classification = self._classify(request)
            stages.append(PipelineStage(
                stage_name="classify", status="success",
                output=classification.to_dict(),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            stages.append(PipelineStage(
                stage_name="classify", status="error",
                duration_ms=(time.monotonic() - stage_start) * 1000,
                error=str(e),
            ))
            return OrchestratorResponse(
                request_id=request_id, content="",
                error=f"Classification failed: {e}",
                pipeline=stages, latency_ms=(time.monotonic() - overall_start) * 1000,
            )

        # ── Stage 2: Policy ─────────────────────────────────────────────
        stage_start = time.monotonic()
        try:
            policy = self._apply_policy(request, classification)
            stages.append(PipelineStage(
                stage_name="policy", status="success",
                output=policy.to_dict(),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            stages.append(PipelineStage(
                stage_name="policy", status="error",
                duration_ms=(time.monotonic() - stage_start) * 1000,
                error=str(e),
            ))
            return OrchestratorResponse(
                request_id=request_id, content="",
                error=f"Policy application failed: {e}",
                pipeline=stages, latency_ms=(time.monotonic() - overall_start) * 1000,
            )

        # ── Stage 3: Select ─────────────────────────────────────────────
        stage_start = time.monotonic()
        try:
            recommendation = self._select(request, classification, policy)
            stages.append(PipelineStage(
                stage_name="select", status="success",
                output=recommendation.to_dict(),
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            stages.append(PipelineStage(
                stage_name="select", status="error",
                duration_ms=(time.monotonic() - stage_start) * 1000,
                error=str(e),
            ))
            return OrchestratorResponse(
                request_id=request_id, content="",
                error=f"Selection failed: {e}",
                pipeline=stages, latency_ms=(time.monotonic() - overall_start) * 1000,
            )

        # ── Stage 4: Execute ────────────────────────────────────────────
        stage_start = time.monotonic()
        try:
            inference_request = self._build_inference_request(request, recommendation)
            result = self._execution.execute_request(inference_request)
            stages.append(PipelineStage(
                stage_name="execute", status="success" if result.success else "error",
                output={
                    "provider": result.provider,
                    "model": result.model,
                    "finish_reason": result.finish_reason,
                    "latency_ms": round(result.latency_ms, 1),
                    "error": result.error,
                },
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            stages.append(PipelineStage(
                stage_name="execute", status="error",
                duration_ms=(time.monotonic() - stage_start) * 1000,
                error=str(e),
            ))
            return OrchestratorResponse(
                request_id=request_id, content="",
                error=f"Execution failed: {e}",
                pipeline=stages, latency_ms=(time.monotonic() - overall_start) * 1000,
            )

        # ── Stage 5: Observe ────────────────────────────────────────────
        stage_start = time.monotonic()
        try:
            self._observe(request, result, recommendation)
            stages.append(PipelineStage(
                stage_name="observe", status="success",
                duration_ms=(time.monotonic() - stage_start) * 1000,
            ))
        except Exception as e:
            logger.warning("Observation stage failed (non-fatal): %s", e)
            stages.append(PipelineStage(
                stage_name="observe", status="error",
                duration_ms=(time.monotonic() - stage_start) * 1000,
                error=str(e),
            ))

        total_latency = (time.monotonic() - overall_start) * 1000

        return OrchestratorResponse(
            request_id=request_id,
            content=result.content,
            model=result.model,
            provider=result.provider,
            finish_reason=result.finish_reason,
            usage=result.usage,
            latency_ms=total_latency,
            error=result.error,
            pipeline=stages,
            recommendation=recommendation,
        )

    # ── Stage implementations ───────────────────────────────────────────

    def _classify(self, request: OrchestratorRequest) -> ClassificationResult:
        """Classify the incoming request for routing decisions.

        Uses heuristic signals to determine request type, complexity,
        tool requirements, and streaming needs.
        """
        text = request.input_text.lower()
        result = ClassificationResult(
            request_type=request.request_type,
            confidence=0.6,
        )

        # Detect intent from text patterns
        if any(word in text for word in ["create", "new", "make", "add", "schedule"]):
            result.detected_intent = "creation"
            result.requires_tools = True
        elif any(word in text for word in ["search", "find", "lookup", "where", "show"]):
            result.detected_intent = "retrieval"
        elif any(word in text for word in ["why", "explain", "how", "reason", "because"]):
            result.detected_intent = "explanation"
            result.complexity = "moderate"
        elif any(word in text for word in ["analyze", "compare", "evaluate", "summarize"]):
            result.detected_intent = "analysis"
            result.complexity = "complex"
        elif any(word in text for word in ["hello", "hi", "hey", "thanks"]):
            result.detected_intent = "greeting"
            result.complexity = "simple"
        else:
            result.detected_intent = "general"

        # Estimate complexity by length and structure
        word_count = len(text.split())
        if word_count > 50:
            result.complexity = "complex"
        elif word_count > 20:
            result.complexity = "moderate"

        # Detect streaming suitability
        result.requires_streaming = (
            result.complexity == "complex" or word_count > 100
        )

        result.confidence = 0.8 if result.detected_intent else 0.5
        return result

    def _apply_policy(
        self, request: OrchestratorRequest, classification: ClassificationResult
    ) -> PolicyResult:
        """Apply routing policy based on request properties and classification.

        Determines which providers are allowed, cost constraints, and
        auditing requirements. Uses provider names from the registry.
        """
        policy = PolicyResult(
            allowed_providers=[],
            timeout_seconds=60,
        )

        # Get available providers from execution layer
        available_raw = self._execution.get_available_providers()
        available = [p.get("name", "").lower() for p in available_raw if isinstance(p, dict)]
        available = [n for n in available if n]
        # Order by preference: groq, openrouter, openai, anthropic, local
        preferred = ["groq", "openrouter", "openai", "anthropic", "local"]
        ordered = [p for p in preferred if p in available] + \
                  [p for p in available if p not in preferred]

        # Simple requests: cheapest available, fast timeout
        if classification.complexity == "simple":
            policy.allowed_providers = ordered[:3] if len(ordered) >= 3 else ordered
            policy.timeout_seconds = 30

        # Moderate requests: higher quality providers
        elif classification.complexity == "moderate":
            policy.allowed_providers = [p for p in ordered if p != "local"]
            policy.timeout_seconds = 60

        # Complex requests: premium providers, audit
        elif classification.complexity == "complex":
            policy.allowed_providers = [p for p in ordered if p != "local"]
            policy.timeout_seconds = 120
            policy.requires_audit = True

        # Tool calls: must support tool calling
        if classification.requires_tools:
            policy.allowed_providers = [
                p for p in policy.allowed_providers
                if p != "local"
            ]

        # Apply provider hint from request
        if request.provider_hint:
            policy.allowed_providers = [
                p for p in policy.allowed_providers
                if p == request.provider_hint
            ] or [request.provider_hint]

        return policy

    def _select(
        self,
        request: OrchestratorRequest,
        classification: ClassificationResult,
        policy: PolicyResult,
    ) -> Recommendation:
        """Select the best provider+model using the Learning Router.

        Consults the router for a recommendation filtered by policy,
        then falls back to a reasonable default if no data exists.
        """
        context = {
            "request_type": classification.request_type,
            "complexity": classification.complexity,
            "requires_tools": classification.requires_tools,
        }

        recommendation = self._router.get_recommendation(
            context=context,
            preferred_providers=policy.allowed_providers or None,
        )

        # Use defaults if the learning router doesn't have data for ALL
        # allowed providers (cold-start). Otherwise router may recommend
        # providers with seeded default data over real available providers.
        pref_set = set(policy.allowed_providers or [])
        router_providers = set(
            r.get("provider", "") for r in self._router.get_records()
        )
        missing = pref_set - router_providers
        needs_default = (
            recommendation.confidence == 0.0
            or missing
        )
        if needs_default:
            recommendation = self._default_recommendation(
                request, classification, policy
            )

        return recommendation

    def _default_recommendation(
        self,
        request: OrchestratorRequest,
        classification: ClassificationResult,
        policy: PolicyResult,
    ) -> Recommendation:
        """Fallback recommendation when no telemetry data exists."""
        # Use provider hint if specified
        if request.provider_hint:
            return Recommendation(
                provider=request.provider_hint,
                model=request.model or "",
                confidence=0.5,
                reason=f"Using requested provider: {request.provider_hint}",
            )

        # Use model if specified
        if request.model:
            return Recommendation(
                provider="openai",
                model=request.model,
                confidence=0.5,
                reason=f"Using requested model: {request.model}",
            )

        # Default based on complexity — use first available provider from policy
        preferred = policy.allowed_providers or ["groq", "openrouter", "openai", "anthropic", "local"]
        cheap = [p for p in preferred if p not in ("openai", "anthropic")]
        premium = [p for p in preferred if p in ("openai", "anthropic")]
        primary = cheap[0] if cheap else preferred[0]
        secondary = premium[0] if premium else preferred[0]

        if classification.complexity == "complex":
            return Recommendation(
                provider=secondary,
                model="",
                confidence=0.5,
                reason=f"Default: premium model for complex request ({secondary})",
            )
        elif classification.complexity == "moderate":
            return Recommendation(
                provider=primary,
                model="",
                confidence=0.5,
                reason=f"Default: balanced model for moderate request ({primary})",
            )
        else:
            return Recommendation(
                provider=primary,
                model="",
                confidence=0.5,
                reason=f"Default: efficient model for simple request ({primary})",
            )

    def _build_inference_request(
        self, request: OrchestratorRequest, recommendation: Recommendation
    ) -> InferenceRequest:
        """Build an InferenceRequest from the orchestrator request and selection."""
        messages = []

        # System prompt
        if request.system_prompt:
            messages.append(InferenceMessage(role="system", content=request.system_prompt))

        # Conversation history
        for msg in request.conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            messages.append(InferenceMessage(role=role, content=content))

        # Current input
        messages.append(InferenceMessage(role="user", content=request.input_text))

        inference_request = InferenceRequest(
            messages=messages,
            model=recommendation.model or request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            provider_hint=recommendation.provider,
        )

        # Apply request-level overrides
        if request.model:
            inference_request.model = request.model
        if request.provider_hint:
            inference_request.provider_hint = request.provider_hint

        return inference_request

    def _observe(
        self,
        request: OrchestratorRequest,
        result: InferenceResult,
        recommendation: Recommendation,
    ) -> None:
        """Record telemetry from the completed pipeline execution."""
        record = TelemetryRecord(
            session_id=request.session_id,
            provider=result.provider,
            model=result.model,
            request_type=request.request_type,
            input_tokens=result.usage.get("input_tokens", 0) or result.usage.get("prompt_tokens", 0),
            output_tokens=result.usage.get("output_tokens", 0) or result.usage.get("completion_tokens", 0),
            latency_ms=result.latency_ms,
            success=result.success,
            error=result.error,
            finish_reason=result.finish_reason,
            metadata={
                "request_id": getattr(request, "request_id", ""),
                "complexity": getattr(request, "complexity", "simple"),
            },
        )
        self._router.record(record)


# ── Inference Orchestrator ──────────────────────────────────────────────────


class InferenceOrchestrator:
    """Central coordinator for all inference operations.

    The orchestrator owns the five-stage pipeline, manages the execution
    layer and learning router, and exposes the public API for processing
    requests, health checks, and dashboard metrics.
    """

    def __init__(
        self,
        provider_configs: list[ProviderConfig] | None = None,
        execution_layer: ExecutionLayer | None = None,
        learning_router: LearningRouter | None = None,
    ):
        self._execution = execution_layer or ExecutionLayer(
            provider_configs or resolve_provider_configs()
        )
        self._router = learning_router or LearningRouter()
        self._pipeline = Pipeline(
            execution_layer=self._execution,
            learning_router=self._router,
        )
        self._started_at = datetime.now(timezone.utc).isoformat()
        self._total_requests = 0

        logger.info(
            "InferenceOrchestrator initialized with %d provider(s)",
            len(self._execution.get_available_providers()),
        )

    # ── Public API ──────────────────────────────────────────────────────

    def process(self, request: OrchestratorRequest) -> OrchestratorResponse:
        """Process a request through the full inference pipeline.

        Args:
            request: The incoming request with input text, session context,
                     and optional provider/model hints.

        Returns:
            OrchestratorResponse with the generated content, provider info,
            per-stage pipeline timing, and recommendations.
        """
        self._total_requests += 1
        logger.info(
            "Processing request: type=%s session=%s text_len=%d",
            request.request_type, request.session_id[:8] if request.session_id else "none",
            len(request.input_text),
        )
        return self._pipeline.run(request)

    def health_check(self) -> dict[str, Any]:
        """Return the current health status of the orchestrator and its components.

        Returns:
            Dict with overall status, provider availability, router health,
            and request count.
        """
        providers = self._execution.get_available_providers()
        router_count = self._router.get_record_count()

        return {
            "status": "healthy",
            "started_at": self._started_at,
            "uptime_seconds": (
                datetime.now(timezone.utc) - datetime.fromisoformat(self._started_at)
            ).total_seconds(),
            "total_requests_processed": self._total_requests,
            "providers": {
                "available": len(providers),
                "list": providers,
            },
            "learning_router": {
                "status": "ready",
                "telemetry_records": router_count,
            },
            "pipeline": {
                "stages": ["classify", "policy", "select", "execute", "observe"],
                "status": "ready",
            },
        }

    def get_dashboard(self) -> dict[str, Any]:
        """Return a comprehensive dashboard view of orchestrator state.

        Includes health, provider stats, recent telemetry insights, and
        current routing recommendations.
        """
        health = self.health_check()
        insights = self._router.get_insights(time_range_hours=24)
        recommendation = self._router.get_recommendation()

        return {
            "health": health,
            "insights": insights,
            "recommendation": recommendation.to_dict(),
            "providers": self._execution.get_available_providers(),
        }

    # ── Component access ────────────────────────────────────────────────

    @property
    def execution_layer(self) -> ExecutionLayer:
        """Access the execution layer (for wiring advanced configs)."""
        return self._execution

    @property
    def learning_router(self) -> LearningRouter:
        """Access the learning router (for direct telemetry queries)."""
        return self._router

    @property
    def pipeline(self) -> Pipeline:
        """Access the pipeline (for stage overrides in subclasses)."""
        return self._pipeline

    # ── Lifecycle ───────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset all state (for testing)."""
        self._execution.reset()
        self._router.reset()
        self._started_at = datetime.now(timezone.utc).isoformat()
        self._total_requests = 0
        logger.info("InferenceOrchestrator reset complete")


# ── Singleton ───────────────────────────────────────────────────────────────

_INSTANCE: InferenceOrchestrator | None = None


def get_orchestrator() -> InferenceOrchestrator:
    """Get or create the singleton InferenceOrchestrator."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = InferenceOrchestrator()
    return _INSTANCE


def reset_orchestrator() -> None:
    """Reset the singleton (for testing)."""
    global _INSTANCE
    if _INSTANCE:
        _INSTANCE.reset()
    _INSTANCE = None