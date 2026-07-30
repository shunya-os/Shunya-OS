"""SHUNYA Inference Orchestrator — Data Models and Types.

Every interaction with the inference layer passes through these models.
No provider-specific logic lives here — registries in sibling modules
handle provider discovery and routing.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ── Enums ───────────────────────────────────────────────────────────────────


class ProviderCapability(str, enum.Enum):
    """Capabilities a provider can offer for a given model."""

    TEXT_GENERATION = "text_generation"
    CHAT_COMPLETION = "chat_completion"
    EMBEDDING = "embedding"
    IMAGE_GENERATION = "image_generation"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    VISION = "vision"
    STRUCTURED_OUTPUT = "structured_output"
    CODE_GENERATION = "code_generation"


class ProviderStatus(str, enum.Enum):
    """Operational status of a provider endpoint."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class FinishReason(str, enum.Enum):
    """Why the model stopped generating."""

    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    TOOL_CALLS = "tool_calls"
    ERROR = "error"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class RoutingPriority(str, enum.Enum):
    """Priority criteria for model selection."""

    COST = "cost"
    LATENCY = "latency"
    CAPABILITY = "capability"
    RELIABILITY = "reliability"
    MANUAL = "manual"


# ── Core Data Types ─────────────────────────────────────────────────────────


@dataclass
class InferenceQuota:
    """Rate-limit and quota tracking for a provider."""

    tokens_per_minute: int = 0
    tokens_per_day: int = 0
    requests_per_minute: int = 0
    max_concurrent: int = 10
    remaining_tokens: int = 0
    remaining_requests: int = 0
    reset_at: str = ""

    def __post_init__(self) -> None:
        if not self.reset_at:
            self.reset_at = datetime.now(timezone.utc).isoformat()

    def is_exhausted(self) -> bool:
        return self.remaining_tokens <= 0 or self.remaining_requests <= 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tokens_per_minute": self.tokens_per_minute,
            "tokens_per_day": self.tokens_per_day,
            "requests_per_minute": self.requests_per_minute,
            "max_concurrent": self.max_concurrent,
            "remaining_tokens": self.remaining_tokens,
            "remaining_requests": self.remaining_requests,
            "reset_at": self.reset_at,
        }


@dataclass
class ProviderHealth:
    """Current health snapshot of a provider endpoint."""

    status: ProviderStatus = ProviderStatus.UNKNOWN
    latency_p95_ms: float = 0.0
    error_rate: float = 0.0
    last_check: str = ""
    consecutive_failures: int = 0
    message: str = ""

    def __post_init__(self) -> None:
        if not self.last_check:
            self.last_check = datetime.now(timezone.utc).isoformat()

    def is_available(self) -> bool:
        return self.status in (ProviderStatus.HEALTHY, ProviderStatus.DEGRADED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "latency_p95_ms": round(self.latency_p95_ms, 2),
            "error_rate": round(self.error_rate, 4),
            "last_check": self.last_check,
            "consecutive_failures": self.consecutive_failures,
            "message": self.message,
        }


@dataclass
class ModelCapability:
    """Capabilities and cost information for a specific model."""

    name: str
    provider: str
    capabilities: set[ProviderCapability] = field(default_factory=lambda: {
        ProviderCapability.CHAT_COMPLETION,
        ProviderCapability.TEXT_GENERATION,
    })
    context_window: int = 4096
    max_output_tokens: int = 1024
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_functions: bool = True
    supports_structured_output: bool = False
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    is_available: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_capability(self, capability: ProviderCapability) -> bool:
        return capability in self.capabilities

    def has_all_capabilities(self, capabilities: set[ProviderCapability]) -> bool:
        return capabilities.issubset(self.capabilities)

    def estimated_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (
            (input_tokens / 1000) * self.cost_per_1k_input
            + (output_tokens / 1000) * self.cost_per_1k_output
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "provider": self.provider,
            "capabilities": sorted(c.value for c in self.capabilities),
            "context_window": self.context_window,
            "max_output_tokens": self.max_output_tokens,
            "supports_streaming": self.supports_streaming,
            "supports_vision": self.supports_vision,
            "supports_functions": self.supports_functions,
            "supports_structured_output": self.supports_structured_output,
            "cost_per_1k_input": self.cost_per_1k_input,
            "cost_per_1k_output": self.cost_per_1k_output,
            "is_available": self.is_available,
        }


@dataclass
class ProviderDefinition:
    """Full definition of a model provider."""

    name: str
    base_url: str = ""
    api_key_env: str = ""
    models: list[ModelCapability] = field(default_factory=list)
    default_capabilities: set[ProviderCapability] = field(default_factory=lambda: {
        ProviderCapability.CHAT_COMPLETION,
        ProviderCapability.TEXT_GENERATION,
    })
    default_quota: InferenceQuota = field(default_factory=InferenceQuota)
    health: ProviderHealth = field(default_factory=ProviderHealth)
    is_enabled: bool = True
    priority: int = 100
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_model(self, name: str) -> ModelCapability | None:
        for m in self.models:
            if m.name == name:
                return m
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "base_url": self.base_url,
            "api_key_env": self.api_key_env,
            "models": [m.to_dict() for m in self.models],
            "default_capabilities": sorted(c.value for c in self.default_capabilities),
            "default_quota": self.default_quota.to_dict(),
            "health": self.health.to_dict(),
            "is_enabled": self.is_enabled,
            "priority": self.priority,
        }


@dataclass
class UsageInfo:
    """Token usage for a single inference request."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class InferenceRequest:
    """A request to run inference against a model provider."""

    model: str
    provider: str = ""
    messages: list[dict[str, str]] = field(default_factory=list)
    prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    stream: bool = False
    capabilities_required: set[ProviderCapability] = field(default_factory=set)
    priority: RoutingPriority = RoutingPriority.CAPABILITY
    request_id: str = ""
    stop_sequences: list[str] = field(default_factory=list)
    tools: list[dict[str, Any]] = field(default_factory=list)
    response_format: dict[str, Any] | None = None
    user: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id:
            import uuid
            self.request_id = uuid.uuid4().hex[:12]

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "provider": self.provider,
            "messages": self.messages,
            "prompt": self.prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stream": self.stream,
            "capabilities_required": sorted(c.value for c in self.capabilities_required),
            "priority": self.priority.value,
            "request_id": self.request_id,
            "tools": self.tools,
            "user": self.user,
        }


@dataclass
class InferenceResponse:
    """The result of a single inference request."""

    content: str
    model: str
    provider: str
    finish_reason: FinishReason = FinishReason.STOP
    usage: UsageInfo = field(default_factory=UsageInfo)
    request_id: str = ""
    latency_ms: float = 0.0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    telemetry: InferenceTelemetry | None = None
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id:
            import uuid
            self.request_id = uuid.uuid4().hex[:12]

    def is_success(self) -> bool:
        return self.finish_reason != FinishReason.ERROR and not self.error

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "finish_reason": self.finish_reason.value,
            "usage": self.usage.to_dict(),
            "request_id": self.request_id,
            "latency_ms": round(self.latency_ms, 2),
            "tool_calls": self.tool_calls,
            "error": self.error,
        }


@dataclass
class RoutingDecision:
    """The decision made by the router for which model to use."""

    selected_provider: str
    selected_model: str
    confidence: float = 1.0
    reasoning: str = ""
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    request_id: str = ""
    priority: RoutingPriority = RoutingPriority.CAPABILITY
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.request_id:
            import uuid
            self.request_id = uuid.uuid4().hex[:12]

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_provider": self.selected_provider,
            "selected_model": self.selected_model,
            "confidence": round(self.confidence, 2),
            "reasoning": self.reasoning,
            "alternatives": self.alternatives,
            "request_id": self.request_id,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
        }


@dataclass
class InferenceTelemetry:
    """Per-request telemetry for observability and cost tracking."""

    request_id: str
    provider: str
    model: str
    latency_ms: float = 0.0
    tokens_used: int = 0
    tokens_prompt: int = 0
    tokens_completion: int = 0
    cost: float = 0.0
    error: str = ""
    retry_count: int = 0
    cache_hit: bool = False
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "provider": self.provider,
            "model": self.model,
            "latency_ms": round(self.latency_ms, 2),
            "tokens_used": self.tokens_used,
            "tokens_prompt": self.tokens_prompt,
            "tokens_completion": self.tokens_completion,
            "cost": round(self.cost, 6),
            "error": self.error,
            "retry_count": self.retry_count,
            "cache_hit": self.cache_hit,
            "timestamp": self.timestamp,
        }


@dataclass
class PolicyDefinition:
    """Routing and fallback policy that governs model selection."""

    name: str
    description: str = ""
    priority: RoutingPriority = RoutingPriority.CAPABILITY
    fallback_models: list[str] = field(default_factory=list)
    required_capabilities: set[ProviderCapability] = field(default_factory=set)
    max_retries: int = 3
    timeout_seconds: float = 30.0
    allowed_providers: list[str] = field(default_factory=list)
    blocked_providers: list[str] = field(default_factory=list)
    cost_limit_per_1k_input: float = 0.0
    cost_limit_per_1k_output: float = 0.0
    max_latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def allows_provider(self, provider_name: str) -> bool:
        if self.blocked_providers and provider_name in self.blocked_providers:
            return False
        if self.allowed_providers:
            return provider_name in self.allowed_providers
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "fallback_models": self.fallback_models,
            "required_capabilities": sorted(c.value for c in self.required_capabilities),
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "allowed_providers": self.allowed_providers,
            "blocked_providers": self.blocked_providers,
            "cost_limit_per_1k_input": self.cost_limit_per_1k_input,
            "cost_limit_per_1k_output": self.cost_limit_per_1k_output,
            "max_latency_ms": self.max_latency_ms,
        }