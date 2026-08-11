"""
SHUNYA — Model Orchestration Controller (FDA8).

Adds deterministic-first routing, free/open/local priority, and policy
controls to the existing inference orchestrator.

Reuses the existing core/inference_orchestrator pipeline.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Cost Classes (FDA8.7)
# ═══════════════════════════════════════════════════════════════════

class CostClass(Enum):
    FREE = "free"              # No cost, no API key needed
    OPEN = "open"              # Open-source, self-hosted
    LOW = "low"                # Low-cost provider
    STANDARD = "standard"      # Standard paid provider
    PREMIUM = "premium"        # Premium/expensive model


# ═══════════════════════════════════════════════════════════════════
# Routing Policy (FDA8.2, 8.3, 8.5)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ModelRoute:
    """A model route with cost class and capability metadata."""
    provider: str
    model: str
    cost_class: CostClass = CostClass.FREE
    capabilities: list[str] = field(default_factory=list)
    supports_structured_output: bool = False
    supports_tools: bool = False
    supports_vision: bool = False


class ModelOrchestrator:
    """Canonical model orchestration controller.

    Routing order (FDA8.3):
    1. Deterministic (no model needed)
    2. Free/open/local capable model
    3. Alternative free/open route
    4. Optional paid/external escalation
    """

    def __init__(self, orchestrator=None):
        self._orchestrator = orchestrator
        self._paid_escalation_enabled = True

    def set_paid_escalation(self, enabled: bool) -> None:
        """Enable or disable paid model escalation."""
        self._paid_escalation_enabled = enabled

    def is_deterministic_capable(self, task: str) -> bool:
        """Check if a task can be handled deterministically (FDA8.2)."""
        deterministic_tasks = {
            "sorting", "aggregation", "validation", "schema_mapping",
            "deduplication", "state_transition", "permission_check",
            "date_arithmetic", "calculation", "simple_calculation",
            "business_rule", "filter", "count", "formatting",
        }
        return task.lower().strip() in deterministic_tasks

    def get_preferred_routes(self, capability: str) -> list[ModelRoute]:
        """Get model routes ordered by cost class (free-first)."""
        routes = [
            # Free/Open routes (no API key needed)
            ModelRoute(
                provider="local", model="llama.cpp",
                cost_class=CostClass.FREE,
                capabilities=["text_generation", "chat_completion"],
            ),
            ModelRoute(
                provider="local", model="ollama",
                cost_class=CostClass.FREE,
                capabilities=["text_generation", "chat_completion", "vision"],
            ),
            # Low-cost routes
            ModelRoute(
                provider="openrouter", model="openai/gpt-4o-mini",
                cost_class=CostClass.LOW,
                capabilities=["text_generation", "chat_completion",
                              "function_calling", "structured_output", "vision"],
            ),
            # Standard routes
            ModelRoute(
                provider="openrouter", model="openai/gpt-4o",
                cost_class=CostClass.STANDARD,
                capabilities=["text_generation", "chat_completion",
                              "function_calling", "structured_output", "vision"],
            ),
            # Premium routes
            ModelRoute(
                provider="openrouter", model="anthropic/claude-3.5-sonnet",
                cost_class=CostClass.PREMIUM,
                capabilities=["text_generation", "chat_completion",
                              "function_calling", "structured_output", "vision"],
            ),
        ]

        # Filter by capability
        if capability:
            routes = [r for r in routes if capability in r.capabilities]

        # Free-first sort
        cost_order = {c: i for i, c in enumerate(CostClass)}
        routes.sort(key=lambda r: cost_order.get(r.cost_class, 99))

        return routes

    def select_route(self, capability: str, require_structured: bool = False,
                     require_tools: bool = False) -> tuple[Optional[ModelRoute], bool]:
        """Select a route for a given capability.

        Returns (route, used_paid_escalation).
        Free-first: prefers free/open routes before paid escalation.
        """
        routes = self.get_preferred_routes(capability)

        # Additional filtering
        if require_structured:
            routes = [r for r in routes if r.supports_structured_output]
        if require_tools:
            routes = [r for r in routes if r.supports_tools]

        if not routes:
            return None, False

        # Find the first route that matches the cost policy
        for route in routes:
            if route.cost_class in (CostClass.FREE, CostClass.OPEN, CostClass.LOW):
                return route, False
            if self._paid_escalation_enabled:
                return route, True

        # No route matches policy
        return None, False

    def get_selection_metadata(self, route: ModelRoute, used_paid: bool) -> dict:
        """Get metadata about the model selection decision."""
        return {
            "provider": route.provider,
            "model": route.model,
            "cost_class": route.cost_class.value,
            "used_paid_escalation": used_paid,
            "capabilities": route.capabilities,
        }

    def process_request(self, task: str, input_text: str,
                        capability: str = "chat_completion",
                        **kwargs) -> dict:
        """Process a request through the orchestration pipeline.

        Deterministic-first (FDA8.2):
        - If task can be handled deterministically, skip model invocation.
        - Otherwise, select a model route and invoke.
        """
        start_time = datetime.utcnow()

        # Step 1: Check deterministic capability
        if self.is_deterministic_capable(task):
            return {
                "success": True,
                "deterministic": True,
                "task": task,
                "result": f"Task '{task}' handled deterministically (no model needed).",
                "route": {"deterministic": True, "cost_class": "free"},
                "latency_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                "cost_class": "free",
            }

        # Step 2: Select model route (free-first)
        require_structured = kwargs.get("require_structured", False)
        require_tools = kwargs.get("require_tools", False)
        route, used_paid = self.select_route(capability, require_structured, require_tools)

        if not route:
            return {
                "success": False,
                "deterministic": False,
                "task": task,
                "error": "No available model route for this capability.",
                "latency_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
            }

        # Step 3: Invoke model (via existing orchestrator)
        try:
            if self._orchestrator:
                response = self._orchestrator.process({
                    "input_text": input_text,
                    "model": route.model,
                    "provider": route.provider,
                })
                result = response.get("content", "") if isinstance(response, dict) else str(response)
            else:
                result = f"[Simulated] {route.provider}/{route.model} response for: {input_text[:50]}..."

            return {
                "success": True,
                "deterministic": False,
                "task": task,
                "result": result,
                "route": self.get_selection_metadata(route, used_paid),
                "latency_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                "cost_class": route.cost_class.value,
            }

        except Exception as e:
            logger.error(f"Model invocation failed: {e}")
            return {
                "success": False,
                "deterministic": False,
                "task": task,
                "error": str(e),
                "route": self.get_selection_metadata(route, used_paid),
                "latency_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
            }


# ═══════════════════════════════════════════════════════════════════
# Fallback Controller (FDA8.4)
# ═══════════════════════════════════════════════════════════════════

class FallbackController:
    """Controlled fallback for model failures.

    A model failure must not become an application failure.
    """

    def __init__(self, orchestrator: ModelOrchestrator):
        self._orchestrator = orchestrator

    def with_fallback(self, task: str, input_text: str,
                      capability: str = "chat_completion",
                      max_attempts: int = 2) -> dict:
        """Execute with fallback support.

        Primary choice → fallback → safe failure.
        """
        first_result = self._orchestrator.process_request(task, input_text, capability)

        if first_result.get("success"):
            return first_result

        # Try fallback with a different capability/route
        if max_attempts >= 2:
            fallback_cap = "text_generation" if capability != "text_generation" else capability
            fallback = self._orchestrator.process_request(
                task, input_text, fallback_cap,
            )
            if fallback.get("success"):
                fallback["used_fallback"] = True
                return fallback

        # All attempts failed
        return {
            "success": False,
            "deterministic": False,
            "task": task,
            "error": "All model routes unavailable.",
            "safe_failure": True,
            "latency_ms": 0,
        }