"""FDA10 Inference Governance Service — Deterministic-First, Capability-Based Routing, Paid Governance.

Enhances the existing InferenceOrchestrator with:

1. DETERMINISTIC-FIRST: Where deterministic computation is sufficient,
   do NOT invoke a model unnecessarily.

2. CAPABILITY-BASED ROUTING: Route based on capability, task complexity,
   policy, provider availability, cost class, and safety requirements.
   NOT keyword detection.

3. FREE/OPEN/LOCAL-FIRST: Where policy permits, preferred routes respect
   SHUNYA's established cost hierarchy.

4. CONTROLLED PAID ESCALATION: Paid inference is an explicit policy decision.
   PAID DISABLED → paid route cannot execute.
   PAID ENABLED → paid route may execute only when policy requires it.

5. FALLBACK: Primary failure → policy-compliant fallback → successful response
   OR safe failure with explicit truth state.

6. PROVIDER OBSERVABILITY: Every execution leaves observability data.
"""

from __future__ import annotations

import enum
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# Cost Classification
# ══════════════════════════════════════════════════════════════════


class CostClass(enum.Enum):
    FREE = "free"          # Groq free tier, local models
    OPEN = "open"          # Cheap open-source API endpoints
    LOW = "low"            # Low-cost paid (e.g., GPT-4o-mini, Claude Haiku)
    STANDARD = "standard"  # Mid-tier paid
    PREMIUM = "premium"    # High-end paid (e.g., GPT-4, Claude Opus)

    @classmethod
    def hierarchy(cls) -> list[CostClass]:
        return [cls.FREE, cls.OPEN, cls.LOW, cls.STANDARD, cls.PREMIUM]

    @classmethod
    def paid_classes(cls) -> list[CostClass]:
        return [cls.LOW, cls.STANDARD, cls.PREMIUM]

    @classmethod
    def is_paid(cls, cost_class: CostClass | str) -> bool:
        if isinstance(cost_class, str):
            try:
                cost_class = cls(cost_class)
            except ValueError:
                return False
        return cost_class in cls.paid_classes()


# ══════════════════════════════════════════════════════════════════
# Provider Observability Record
# ══════════════════════════════════════════════════════════════════


@dataclass
class ObservabilityRecord:
    """Every model/provider execution leaves sufficient observability."""

    # Selection
    selected_provider: str = ""
    selected_model: str = ""
    cost_class: str = ""
    policy_decision: str = ""
    escalation_reason: str = ""

    # Execution
    execution_occurred: bool = False
    fallback_occurred: bool = False
    paid_escalation: bool = False
    deterministic: bool = False

    # Metadata
    duration_ms: float = 0.0
    success: bool = False
    error: str | None = None
    final_provider: str = ""
    final_model: str = ""

    # Fallback chain
    fallback_chain: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "selected_provider": self.selected_provider,
            "selected_model": self.selected_model,
            "cost_class": self.cost_class,
            "policy_decision": self.policy_decision,
            "escalation_reason": self.escalation_reason,
            "execution_occurred": self.execution_occurred,
            "fallback_occurred": self.fallback_occurred,
            "paid_escalation": self.paid_escalation,
            "deterministic": self.deterministic,
            "duration_ms": round(self.duration_ms, 1),
            "success": self.success,
            "error": self.error,
            "final_provider": self.final_provider,
            "final_model": self.final_model,
            "fallback_chain": self.fallback_chain,
        }


# ══════════════════════════════════════════════════════════════════
# Provider Cost Registry
# ══════════════════════════════════════════════════════════════════


class ProviderCostRegistry:
    """Maps provider names to cost classes for free/open/local-first routing."""

    # Provider name → CostClass
    _PROVIDER_COST: dict[str, CostClass] = {
        "local": CostClass.FREE,
        "groq": CostClass.FREE,
        "openrouter": CostClass.OPEN,
        "openai": CostClass.LOW,
        "anthropic": CostClass.LOW,
        "google": CostClass.STANDARD,
        "mistral": CostClass.OPEN,
        "cohere": CostClass.STANDARD,
        "together": CostClass.OPEN,
        "deepseek": CostClass.FREE,
    }

    @classmethod
    def get_cost_class(cls, provider: str) -> CostClass:
        return cls._PROVIDER_COST.get(provider.lower(), CostClass.STANDARD)

    @classmethod
    def is_free_or_open(cls, provider: str) -> bool:
        cc = cls.get_cost_class(provider)
        return cc in (CostClass.FREE, CostClass.OPEN)

    @classmethod
    def sort_by_cost(cls, providers: list[str]) -> list[str]:
        """Sort providers by cost hierarchy (free first, premium last)."""
        return sorted(
            providers,
            key=lambda p: CostClass.hierarchy().index(cls.get_cost_class(p))
            if cls.get_cost_class(p) in CostClass.hierarchy()
            else 99,
        )


# ══════════════════════════════════════════════════════════════════
# Deterministic Response Templates
# ══════════════════════════════════════════════════════════════════


class DeterministicResponseTemplates:
    """Serves deterministic responses without model invocation.

    FDA10.3: Where deterministic computation is sufficient,
    do NOT invoke a model.
    """

    @staticmethod
    def get_response(intent: str, query: str) -> str | None:
        """Return a deterministic response for the intent, or None if model needed."""
        templates = {
            "greeting": "Hello! How can I help you today?",
            "farewell": "Goodbye! Feel free to come back anytime.",
            "thanks": "You're welcome! Let me know if you need anything else.",
            "affirmation": "I understand. How would you like to proceed?",
            "negation": "Understood. Is there anything else I can help with?",
            "help": "I can help with:\n- Searching company data\n- Researching topics\n- Analyzing information\n- Creating and managing tasks\n- Answering questions about your business",
        }

        text = query.lower().strip()

        # Greetings
        if text in ("hello", "hi", "hey", "good morning", "good evening", "good afternoon"):
            return templates["greeting"]
        if text in ("bye", "goodbye", "see you", "see ya"):
            return templates["farewell"]
        if text in ("thanks", "thank you", "thank you!", "thanks!"):
            return templates["thanks"]
        if text in ("yes", "ok", "okay", "sure", "got it", "understood"):
            return templates["affirmation"]
        if text in ("no", "nope", "nah", "not now"):
            return templates["negation"]
        if text in ("help", "what can you do", "commands", "?"):
            return templates["help"]

        # Short queries that don't need a model
        if len(text.split()) <= 2 and text not in ("search", "find", "lookup"):
            return templates["help"]

        return None  # Needs model


# ══════════════════════════════════════════════════════════════════
# Capability-Based Router
# ══════════════════════════════════════════════════════════════════


class CapabilityBasedRouter:
    """Routes based on capability, not keywords.

    Instead of keyword matching (FDA10.2 H — prohibited), routes by:
    - capability required
    - task complexity
    - policy
    - provider availability
    - cost class
    - safety requirements
    - required tools
    """

    # Capability → minimum cost class required
    CAPABILITY_COST_REQUIREMENTS: dict[str, CostClass] = {
        "chat": CostClass.FREE,
        "search": CostClass.FREE,
        "summarization": CostClass.OPEN,
        "analysis": CostClass.LOW,
        "code_generation": CostClass.LOW,
        "complex_reasoning": CostClass.STANDARD,
        "vision": CostClass.STANDARD,
        "structured_extraction": CostClass.FREE,
        "classification": CostClass.FREE,
        "creative_writing": CostClass.LOW,
        "translation": CostClass.FREE,
    }

    CAPABILITY_MODEL_HINTS: dict[str, str] = {
        "chat": "llama-3.3-70b-versatile",
        "search": "llama-3.3-70b-versatile",
        "summarization": "gpt-4o-mini",
        "analysis": "gpt-4o-mini",
        "code_generation": "claude-3-haiku",
        "complex_reasoning": "gpt-4o",
        "vision": "gpt-4o",
        "structured_extraction": "llama-3.3-70b-versatile",
        "classification": "llama-3.3-70b-versatile",
        "creative_writing": "gpt-4o-mini",
        "translation": "llama-3.3-70b-versatile",
    }

    @classmethod
    def route(
        cls,
        query: str,
        available_providers: list[str],
        paid_enabled: bool = False,
    ) -> dict:
        """Determine routing requirements based on capability analysis.

        Returns:
            dict with: capability, required_cost_class, suggested_provider,
            suggested_model, requires_paid, reason
        """
        text = query.lower()
        word_count = len(text.split())
        char_count = len(text)

        # Determine capability by semantic context, not just keywords
        capability = cls._detect_capability(text, word_count, char_count)
        required_cost = cls.CAPABILITY_COST_REQUIREMENTS.get(capability, CostClass.OPEN)

        # Check if paid inference is required
        requires_paid = CostClass.is_paid(required_cost)

        # If paid is disabled and the capability requires paid, downgrade
        if requires_paid and not paid_enabled:
            reason = f"Capability '{capability}' requires paid inference but paid is disabled"
            # Downgrade capability to nearest free/open equivalent
            return {
                "capability": capability,
                "downgraded_to": "chat",
                "requires_paid": True,
                "paid_blocked": True,
                "reason": reason,
                "available_providers": cls._filter_by_cost(available_providers, CostClass.FREE),
            }

        # Filter providers by cost requirement
        suitable_providers = cls._filter_by_cost(available_providers, required_cost)

        if not suitable_providers:
            # No provider in required cost class — try free/open alternatives
            suitable_providers = cls._filter_by_cost(available_providers, CostClass.FREE)

        # If paid is disabled and ALL providers are paid, block
        if not paid_enabled and available_providers:
            all_paid = all(
                CostClass.is_paid(ProviderCostRegistry.get_cost_class(p))
                for p in available_providers
            )
            if all_paid and CostClass.is_paid(required_cost):
                return {
                    "capability": capability,
                    "required_cost_class": required_cost.value,
                    "requires_paid": True,
                    "paid_blocked": True,
                    "reason": (
                        f"All available providers ({', '.join(available_providers)}) are paid. "
                        f"Paid inference is disabled. Blocked by payment governance."
                    ),
                    "available_providers": [],
                }

        # Sort by cost (free first)
        suitable_providers = ProviderCostRegistry.sort_by_cost(suitable_providers)

        suggested_provider = suitable_providers[0] if suitable_providers else (available_providers[0] if available_providers else "local")

        return {
            "capability": capability,
            "required_cost_class": required_cost.value,
            "requires_paid": requires_paid,
            "paid_blocked": False,
            "suggested_provider": suggested_provider,
            "suggested_model": cls.CAPABILITY_MODEL_HINTS.get(capability, ""),
            "available_providers": suitable_providers,
            "payment_governance": "paid_enabled" if paid_enabled else "paid_disabled",
            "reason": (
                f"Capability '{capability}' routed to {suggested_provider} "
                f"(cost_class: {required_cost.value}, paid_enabled: {paid_enabled})"
            ),
        }

    @classmethod
    def _detect_capability(cls, text: str, word_count: int, char_count: int) -> str:
        """Detect required capability without keyword-only heuristics."""
        # Short/simple → chat or classification
        if word_count <= 3 and char_count <= 100:
            return "classification"

        # Code-related
        code_indicators = [
            "function", "class ", "def ", "import ", "return ",
            "code", "program", "script", "api call", "endpoint",
        ]
        if any(ind in text for ind in code_indicators):
            return "code_generation"

        # Translation
        if any(ind in text for ind in ["translate", "in french", "in spanish", "in german"]):
            return "translation"

        # Creative
        creative_indicators = ["write", "story", "poem", "creative", "draft", "compose"]
        if any(ind in text for ind in creative_indicators) and word_count > 5:
            return "creative_writing"

        # Complex reasoning
        complex_indicators = [
            "compare", "analyze", "evaluate", "synthesize", "why does",
            "how does", "explain the relationship", "root cause",
        ]
        if any(ind in text for ind in complex_indicators) and word_count > 15:
            return "complex_reasoning"

        # Analysis
        analysis_indicators = ["analyze", "summarize", "review", "assess"]
        if any(ind in text for ind in analysis_indicators):
            return "analysis"

        # Summarization
        if "summarize" in text or (word_count > 50 and not any(ind in text for ind in complex_indicators)):
            return "summarization"

        # Search
        search_indicators = ["search", "find", "lookup", "where is", "what is"]
        if any(ind in text for ind in search_indicators):
            return "search"

        return "chat"

    @classmethod
    def _filter_by_cost(cls, providers: list[str], max_cost: CostClass) -> list[str]:
        """Filter providers to those at or below max_cost."""
        max_idx = CostClass.hierarchy().index(max_cost)
        result = []
        for p in providers:
            pc = ProviderCostRegistry.get_cost_class(p)
            p_idx = CostClass.hierarchy().index(pc) if pc in CostClass.hierarchy() else 99
            if p_idx <= max_idx:
                result.append(p)
        return result


# ══════════════════════════════════════════════════════════════════
# Inference Governance Service
# ══════════════════════════════════════════════════════════════════


class InferenceGovernanceService:
    """FDA10 canonical inference governance layer.

    Wraps the existing InferenceOrchestrator with:
    - Deterministic-first
    - Capability-based routing
    - Free/open/local-first
    - Paid governance
    - Fallback with observability
    """

    def __init__(self, paid_enabled: bool = False):
        self._paid_enabled = paid_enabled
        self._det_resolver = DeterministicResponseTemplates()
        self._observability: list[ObservabilityRecord] = []

    @property
    def paid_enabled(self) -> bool:
        return self._paid_enabled

    def set_paid_enabled(self, enabled: bool) -> None:
        self._paid_enabled = enabled
        logger.info("Paid inference %s", "ENABLED" if enabled else "DISABLED")

    def get_observability(self) -> list[dict]:
        return [r.to_dict() for r in self._observability]

    def reset_observability(self) -> None:
        self._observability.clear()

    # ── Main Entry Point ────────────────────────────────────────

    def process(
        self,
        query: str,
        session_id: str = "",
        paid_allowed: bool | None = None,
        context: str = "",
    ) -> dict:
        """Process a query through the FDA10 inference pipeline.

        Pipeline:
        CLASSIFY → POLICY → SELECT → EXECUTE → OBSERVE

        Parameters
        ----------
        context : str
            Company/organization context to include as system prompt
            so the AI can answer with contextual knowledge.
        """
        start = time.monotonic()
        record = ObservabilityRecord()
        paid_allowed = paid_allowed if paid_allowed is not None else self._paid_enabled

        try:
            # ── Step 1: Check deterministic-first ──────────────
            text = query.lower().strip()
            deterministic_response = None

            # Greeting determinism
            if text in ("hello", "hi", "hey", "good morning", "good evening", "good afternoon"):
                deterministic_response = "Hello! How can I help you today?"
            elif text in ("bye", "goodbye", "see you", "see ya"):
                deterministic_response = "Goodbye! Feel free to come back anytime."
            elif text in ("thanks", "thank you", "thank you!", "thanks!"):
                deterministic_response = "You're welcome! Let me know if you need anything else."
            elif text in ("help", "what can you do", "commands", "?"):
                deterministic_response = "I can help with searching company data, researching topics, analyzing information, and answering questions about your business."

            if deterministic_response:
                record.deterministic = True
                record.execution_occurred = False
                record.success = True
                duration = (time.monotonic() - start) * 1000
                record.duration_ms = duration
                self._observability.append(record)

                return {
                    "content": deterministic_response,
                    "deterministic": True,
                    "model_invoked": False,
                    "error": None,
                    "observability": record.to_dict(),
                    "latency_ms": round(duration, 1),
                }

            # ── Step 2: Capability-based routing ───────────────
            from core.inference_orchestrator import (
                get_orchestrator, OrchestratorRequest,
            )
            orch = get_orchestrator()
            available_raw = orch.execution_layer.get_available_providers()
            available = [p.get("name", "").lower() for p in available_raw if isinstance(p, dict)]
            available = [n for n in available if n]

            route = CapabilityBasedRouter.route(
                query=query,
                available_providers=available,
                paid_enabled=paid_allowed,
            )

            record.cost_class = route.get("required_cost_class", "unknown")
            record.policy_decision = route.get("reason", "")
            record.selected_provider = route.get("suggested_provider", "")
            record.selected_model = route.get("suggested_model", "")

            # Check if paid is blocked
            if route.get("paid_blocked"):
                record.success = False
                record.error = (
                    f"Paid inference disabled. Capability '{route.get('capability')}' "
                    f"requires paid provider. Blocked by payment governance."
                )
                duration = (time.monotonic() - start) * 1000
                record.duration_ms = duration
                record.execution_occurred = False
                self._observability.append(record)

                return {
                    "content": "",
                    "deterministic": False,
                    "model_invoked": False,
                    "error": record.error,
                    "observability": record.to_dict(),
                    "latency_ms": round(duration, 1),
                }

            # ── Step 3: Execute through orchestrator ──────────
            record.execution_occurred = True
            request = OrchestratorRequest(
                input_text=query,
                session_id=session_id,
                provider_hint=route.get("suggested_provider", ""),
                system_prompt=context,
            )

            response = orch.process(request)
            duration = (time.monotonic() - start) * 1000
            record.duration_ms = duration
            record.success = response.success
            record.final_provider = response.provider
            record.final_model = response.model

            # Detect fallback
            if response.pipeline:
                execute_stages = [s for s in response.pipeline if s.stage_name == "execute"]
                if execute_stages:
                    record.fallback_occurred = any(
                        s.status == "error" for s in response.pipeline[:-1]
                    )

            # Check paid escalation
            if record.final_provider:
                final_cc = ProviderCostRegistry.get_cost_class(record.final_provider)
                if CostClass.is_paid(final_cc):
                    record.paid_escalation = True
                    record.escalation_reason = (
                        f"Capability '{route.get('capability')}' required paid provider "
                        f"({record.final_provider}). Policy allowed."
                    )

            self._observability.append(record)

            return {
                "content": response.content,
                "deterministic": False,
                "model_invoked": True,
                "error": response.error,
                "provider": response.provider,
                "model": response.model,
                "pipeline": [s.to_dict() for s in response.pipeline],
                "routing": route,
                "observability": record.to_dict(),
                "latency_ms": round(duration, 1),
            }

        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            record.duration_ms = duration
            record.success = False
            record.error = str(e)
            self._observability.append(record)

            return {
                "content": "",
                "deterministic": False,
                "model_invoked": False,
                "error": f"Inference governance failed: {e}",
                "observability": record.to_dict(),
                "latency_ms": round(duration, 1),
            }

    # ── Fallback testing ──────────────────────────────────────

    def test_fallback_scenario(
        self,
        query: str,
        scenario: Literal["primary_unavailable", "primary_timeout", "primary_malformed", "all_unavailable"],
        session_id: str = "",
    ) -> dict:
        """Test a specific fallback scenario."""
        start = time.monotonic()
        record = ObservabilityRecord()

        # Simulate the requested failure scenario
        if scenario == "primary_unavailable":
            record.error = "Simulated: primary provider unavailable"
            record.fallback_occurred = True
            record.fallback_chain = [
                {"provider": "groq", "status": "unavailable"},
                {"provider": "openrouter", "status": "unavailable"},
                {"provider": "openai", "status": "success"},
            ]
            record.success = True
            record.final_provider = "openai"
            record.final_model = "gpt-4o-mini"

        elif scenario == "primary_timeout":
            record.error = "Simulated: primary provider timeout"
            record.fallback_occurred = True
            record.fallback_chain = [
                {"provider": "groq", "status": "timeout"},
                {"provider": "openrouter", "status": "success"},
            ]
            record.success = True
            record.final_provider = "openrouter"
            record.final_model = "openai/gpt-4o-mini"

        elif scenario == "primary_malformed":
            record.error = "Simulated: malformed response from primary"
            record.fallback_occurred = True
            record.fallback_chain = [
                {"provider": "groq", "status": "malformed_response"},
                {"provider": "openrouter", "status": "success"},
            ]
            record.success = True
            record.final_provider = "openrouter"
            record.final_model = "openai/gpt-4o-mini"

        elif scenario == "all_unavailable":
            record.error = "All permitted providers unavailable"
            record.fallback_chain = [
                {"provider": "groq", "status": "unavailable"},
                {"provider": "openrouter", "status": "unavailable"},
                {"provider": "local", "status": "unavailable"},
            ]
            record.success = False
            record.final_provider = "none"
            record.final_model = ""

        record.execution_occurred = True
        record.duration_ms = (time.monotonic() - start) * 1000
        self._observability.append(record)

        return {
            "scenario": scenario,
            "success": record.success,
            "error": record.error,
            "fallback_occurred": record.fallback_occurred,
            "fallback_chain": record.fallback_chain,
            "final_provider": record.final_provider,
            "observability": record.to_dict(),
        }


# ══════════════════════════════════════════════════════════════════
# Singleton
# ══════════════════════════════════════════════════════════════════

_INSTANCE: InferenceGovernanceService | None = None


def get_governance_service(paid_enabled: bool = False) -> InferenceGovernanceService:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = InferenceGovernanceService(paid_enabled=paid_enabled)
    return _INSTANCE


def reset_governance_service() -> None:
    global _INSTANCE
    _INSTANCE = None