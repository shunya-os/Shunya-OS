"""
SHUNYA — Context Engine (Phase E).

GATE 2.1 CONSOLIDATION: QUARANTINED — This is a legacy context assembly
module that overlaps with the canonical runtime context assembly at
core/intelligence/context_assembly/.

The canonical persistent memory store is app/memory/ (MemoryService, FDA3).
The canonical runtime context assembly is core/intelligence/context_assembly/.

Kept for backward compatibility only. New code should use
core/intelligence/context_assembly/ for runtime context needs.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.shunya.context.models import ContextRequest, WorkspaceContext
from app.shunya.context.assembly import ContextAssembler
from app.shunya.context.providers import (
    ContextProvider,
    IdentityContextProvider,
    KnowledgeContextProvider,
    RequestContextProvider,
)
from app.shunya.context.budget import BudgetEnforcer
from app.shunya.context.fingerprint import Fingerprinter


class ContextFusionEngine:
    """Context Fusion Engine — assembles canonical workspace context.

    Orchestrates Identity, Knowledge, and Request providers.
    Integrates with Event Bus, Metrics, Logging, and Health.
    """

    def __init__(
        self,
        identity_engine: Any,
        knowledge_store: Any,
        assembler: Optional[ContextAssembler] = None,
        logger: Any = None,
        metrics_registry: Any = None,
        health_registry: Any = None,
        event_bus: Any = None,
    ) -> None:
        self._identity_engine = identity_engine
        self._knowledge_store = knowledge_store

        # Create providers
        providers: List[ContextProvider] = [
            IdentityContextProvider(identity_engine),
            KnowledgeContextProvider(knowledge_store),
            RequestContextProvider(),
        ]

        self._assembler = assembler or ContextAssembler(
            providers=providers,
            budget_enforcer=BudgetEnforcer(),
            fingerprinter=Fingerprinter(),
        )

        self._logger = logger
        self._metrics = metrics_registry
        self._event_bus = event_bus

        # Metrics
        if self._metrics:
            self._assemble_counter = self._metrics.counter(
                "context_assemblies_total", "Context assemblies"
            )
            self._degraded_counter = self._metrics.counter(
                "context_degraded_total", "Degraded context assemblies"
            )
            self._latency_histogram = self._metrics.histogram(
                "context_assembly_latency_ms", "Context assembly latency",
                buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000],
            )

        # Health
        if health_registry:
            health_registry.register("context_fusion_engine", self._health_check)

    def assemble(self, request: ContextRequest) -> WorkspaceContext:
        """Assemble a workspace context for the given request."""
        start = time.time()
        context = self._assembler.assemble(request)

        # Record metrics
        duration = (time.time() - start) * 1000
        if self._metrics:
            self._assemble_counter.inc()
            self._latency_histogram.observe(duration)
            if context.is_degraded:
                self._degraded_counter.inc()

        # Emit event
        if self._event_bus:
            self._emit_event(context)

        return context

    def _health_check(self) -> Any:
        from app.shunya.infrastructure.health import HealthCheckResult, HealthStatus
        return HealthCheckResult(
            component="context_fusion_engine",
            status=HealthStatus.HEALTHY,
            detail="Context Fusion Engine operational",
            metrics={
                "providers": 3,
            },
        )

    def _emit_event(self, context: WorkspaceContext) -> None:
        from app.shunya.infrastructure.event_bus import CanonicalEvent
        event = CanonicalEvent(
            event_type="context.fusion.completed",
            actor_name="context_fusion_engine",
            object_id=context.context_id,
            object_type="workspace_context",
            payload={
                "context_id": context.context_id,
                "tenant_id": context.tenant_id,
                "actor_id": context.actor_id,
                "purpose_code": context.purpose_code,
                "fingerprint": context.fingerprint,
                "is_degraded": context.is_degraded,
                "section_count": len(context.sections),
            },
        )
        self._event_bus.publish(event)


# ---- Module-level convenience -----------------------------------------------

_engine: Optional[ContextFusionEngine] = None


def get_context_engine(**kwargs: Any) -> ContextFusionEngine:
    global _engine
    if _engine is None:
        from app.shunya.knowledge_store.store import get_knowledge_store
        from app.shunya.identity.engine import get_identity_engine

        _engine = ContextFusionEngine(
            identity_engine=get_identity_engine(),
            knowledge_store=get_knowledge_store(),
            **kwargs,
        )
    return _engine


def reset_context_engine() -> None:
    global _engine
    _engine = None