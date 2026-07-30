"""SHUNYA Inference Orchestrator — central routing, execution, and coordination layer.

The orchestrator ties together model selection, provider routing, inference
execution, and telemetry learning into a five-stage pipeline:

    classify → policy → select → execute → observe

Quick start:
    from core.inference_orchestrator import (
        get_orchestrator,
        OrchestratorRequest,
    )

    orch = get_orchestrator()
    resp = orch.process(OrchestratorRequest(
        input_text="What are my open invoices?",
        session_id="abc123",
    ))
    print(resp.content)
"""

# ── Orchestrator (pipeline + singleton) ──
from .orchestrator import (
    ClassificationResult,
    InferenceOrchestrator,
    OrchestratorRequest,
    OrchestratorResponse,
    Pipeline,
    PipelineStage,
    PolicyResult,
    SelectionResult,
    get_orchestrator,
    reset_orchestrator,
)

# ── Execution layer (provider-specific formatting & dispatch) ──
from .execution import (
    ExecutionLayer,
    InferenceMessage,
    InferenceResult,
    ProviderConfig,
    resolve_provider_configs,
)
# Renamed to avoid collision with models.InferenceRequest
from .execution import InferenceRequest as ExecutionInferenceRequest

# ── Learning router (telemetry, recommendations, insights) ──
from .learning_router import (
    LearningRouter,
    Recommendation,
    TelemetryRecord,
)

# ── Data models (enums + dataclasses) ──
from .models import (
    FinishReason,
    InferenceQuota,
    InferenceResponse,
    InferenceTelemetry,
    PolicyDefinition,
    ProviderCapability,
    ProviderDefinition,
    ProviderHealth,
    ProviderStatus,
    RoutingPriority,
    UsageInfo,
)
# Renamed to avoid collision with execution.InferenceRequest
from .models import InferenceRequest as ModelInferenceRequest

# ── Provider registry ──
from .provider_registry import (
    ProviderRegistry,
    get_default_provider_registry,
    reset_default_provider_registry,
)

# ── Model registry ──
from .model_registry import (
    ModelRegistry,
    get_default_model_registry,
    reset_default_model_registry,
    seed_model_registry_from_providers,
)

# ── Policy engine ──
from .policy_engine import (
    PolicyEngine,
    PolicyRule,
    RoutingPolicy,
)
# Renamed to avoid collision with models.ModelCapability / models.RoutingDecision
from .policy_engine import ModelCapability as PolicyModelCapability
from .policy_engine import RoutingDecision as PolicyRoutingDecision

# ── Quota manager ──
from .quota_manager import (
    QuotaLevel,
    QuotaManager,
    QuotaStatus,
)

# ── Failover engine ──
from .failover_engine import (
    FailoverCandidate,
    FailoverEngine,
    FailoverLevel,
    FailoverResult,
)

# ── Context manager ──
from .context_manager import (
    ContextManager,
    ContextOverflowError,
    ContextSummary,
    PreparedContext,
    TruncationStrategy,
)

# ── Models re-exports ──
from .models import (
    ModelCapability,
    RoutingDecision,
)

__all__ = [
    # Singleton access
    "get_orchestrator",
    "reset_orchestrator",

    # Orchestrator core
    "InferenceOrchestrator",
    "Pipeline",
    "PipelineStage",
    "OrchestratorRequest",
    "OrchestratorResponse",
    "ClassificationResult",
    "PolicyResult",
    "SelectionResult",

    # Execution
    "ExecutionLayer",
    "InferenceMessage",
    "InferenceResult",
    "ProviderConfig",
    "resolve_provider_configs",
    "ExecutionInferenceRequest",

    # Learning
    "LearningRouter",
    "Recommendation",
    "TelemetryRecord",

    # Models / enums
    "ProviderCapability",
    "ProviderStatus",
    "FinishReason",
    "RoutingPriority",
    "InferenceQuota",
    "ProviderHealth",
    "ModelCapability",
    "ProviderDefinition",
    "UsageInfo",
    "ModelInferenceRequest",
    "InferenceResponse",
    "RoutingDecision",
    "InferenceTelemetry",
    "PolicyDefinition",

    # Provider registry
    "ProviderRegistry",
    "get_default_provider_registry",
    "reset_default_provider_registry",

    # Model registry
    "ModelRegistry",
    "get_default_model_registry",
    "reset_default_model_registry",
    "seed_model_registry_from_providers",

    # Policy
    "PolicyEngine",
    "PolicyRule",
    "PolicyModelCapability",
    "PolicyRoutingDecision",
    "RoutingPolicy",

    # Quota
    "QuotaManager",
    "QuotaLevel",
    "QuotaStatus",

    # Failover
    "FailoverEngine",
    "FailoverCandidate",
    "FailoverLevel",
    "FailoverResult",

    # Context
    "ContextManager",
    "ContextOverflowError",
    "ContextSummary",
    "PreparedContext",
    "TruncationStrategy",
]

__version__ = "1.0.0"