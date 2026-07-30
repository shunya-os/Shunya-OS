"""SHUNYA Inference Orchestrator — Provider Registry.

Runtime-discoverable registry of model providers.
No hardcoded provider assumptions — providers are registered at runtime.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import (
    InferenceQuota,
    ModelCapability,
    ProviderCapability,
    ProviderDefinition,
    ProviderHealth,
    ProviderStatus,
)


class ProviderRegistry:
    """Runtime-discoverable registry of model providers.

    Providers are registered by name and can be looked up, filtered by
    capability, or have their health checked at runtime.
    """

    def __init__(self) -> None:
        self._providers: dict[str, ProviderDefinition] = {}

    # ── Registration ────────────────────────────────────────────────────────

    def register(self, provider: ProviderDefinition) -> None:
        """Register a provider. Replaces any existing provider with the same name."""
        self._providers[provider.name] = provider

    def unregister(self, name: str) -> None:
        """Remove a provider from the registry."""
        self._providers.pop(name, None)

    # ── Lookup ──────────────────────────────────────────────────────────────

    def get(self, name: str) -> ProviderDefinition | None:
        """Get a provider by name. Returns None if not found."""
        return self._providers.get(name)

    def list(self) -> list[ProviderDefinition]:
        """Return all registered providers."""
        return list(self._providers.values())

    def list_enabled(self) -> list[ProviderDefinition]:
        """Return only enabled providers."""
        return [p for p in self._providers.values() if p.is_enabled]

    # ── Capability-based discovery ──────────────────────────────────────────

    def find_by_capability(
        self,
        capability: ProviderCapability | set[ProviderCapability],
        *,
        only_enabled: bool = True,
        only_healthy: bool = False,
    ) -> list[ProviderDefinition]:
        """Find providers that offer the given capability (or all of them).

        Parameters
        ----------
        capability : ProviderCapability | set[ProviderCapability]
            Single capability or set of required capabilities.
        only_enabled : bool
            If True, skip disabled providers.
        only_healthy : bool
            If True, skip providers whose health is not available.

        Returns
        -------
        list[ProviderDefinition]
            Matching providers, sorted by priority (lower = preferred).
        """
        required: set[ProviderCapability] = (
            {capability} if isinstance(capability, ProviderCapability)
            else capability
        )

        candidates: list[ProviderDefinition] = []
        for provider in self._providers.values():
            if only_enabled and not provider.is_enabled:
                continue
            if only_healthy and not provider.health.is_available():
                continue
            if required.issubset(provider.default_capabilities):
                candidates.append(provider)
                continue
            # Check individual model capabilities
            for model in provider.models:
                if model.has_all_capabilities(required):
                    candidates.append(provider)
                    break

        candidates.sort(key=lambda p: p.priority)
        return candidates

    # ── Health ──────────────────────────────────────────────────────────────

    def health_check(self, name: str) -> ProviderHealth | None:
        """Get the current health status of a provider by name.

        Returns None if the provider is not registered.  This is a
        read-only snapshot; callers should update health via
        ``update_health()`` when they have fresh data.
        """
        provider = self._providers.get(name)
        return provider.health if provider else None

    def update_health(self, name: str, health: ProviderHealth) -> None:
        """Update the health snapshot for a provider."""
        provider = self._providers.get(name)
        if provider is not None:
            provider.health = health

    def all_healthy(self) -> list[ProviderDefinition]:
        """Return all providers whose status is HEALTHY or DEGRADED."""
        return [p for p in self._providers.values() if p.health.is_available()]

    # ── Convenience ─────────────────────────────────────────────────────────

    def count(self) -> int:
        """Number of registered providers."""
        return len(self._providers)

    def clear(self) -> None:
        """Remove all registered providers."""
        self._providers.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            name: p.to_dict()
            for name, p in self._providers.items()
        }


# ── Default Provider Registry ───────────────────────────────────────────────

_DEFAULT_REGISTRY: ProviderRegistry | None = None


def _build_default_groq() -> ProviderDefinition:
    """Build the default Groq provider definition."""
    return ProviderDefinition(
        name="Groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        default_capabilities={
            ProviderCapability.CHAT_COMPLETION,
            ProviderCapability.TEXT_GENERATION,
            ProviderCapability.STREAMING,
            ProviderCapability.FUNCTION_CALLING,
        },
        default_quota=InferenceQuota(
            tokens_per_minute=30_000,
            tokens_per_day=1_000_000,
            requests_per_minute=30,
            max_concurrent=6,
        ),
        priority=10,
        models=[
            ModelCapability(
                name="llama-3.1-8b-instant",
                provider="Groq",
                capabilities={
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.STREAMING,
                    ProviderCapability.FUNCTION_CALLING,
                },
                context_window=8192,
                max_output_tokens=8192,
                supports_streaming=True,
                supports_functions=True,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                metadata={"type": "open_source", "family": "llama"},
            ),
            ModelCapability(
                name="llama-3.3-70b-versatile",
                provider="Groq",
                capabilities={
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.STREAMING,
                    ProviderCapability.FUNCTION_CALLING,
                    ProviderCapability.STRUCTURED_OUTPUT,
                },
                context_window=131072,
                max_output_tokens=32768,
                supports_streaming=True,
                supports_functions=True,
                supports_structured_output=True,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                metadata={"type": "open_source", "family": "llama"},
            ),
        ],
        metadata={"docs_url": "https://console.groq.com/docs"},
    )


def _build_default_openrouter() -> ProviderDefinition:
    """Build the default OpenRouter provider definition."""
    return ProviderDefinition(
        name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        default_capabilities={
            ProviderCapability.CHAT_COMPLETION,
            ProviderCapability.TEXT_GENERATION,
            ProviderCapability.STREAMING,
            ProviderCapability.FUNCTION_CALLING,
            ProviderCapability.VISION,
        },
        default_quota=InferenceQuota(
            tokens_per_minute=200_000,
            tokens_per_day=10_000_000,
            requests_per_minute=100,
            max_concurrent=20,
        ),
        priority=20,
        models=[
            ModelCapability(
                name="gpt-4o-mini",
                provider="OpenRouter",
                capabilities={
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.STREAMING,
                    ProviderCapability.FUNCTION_CALLING,
                    ProviderCapability.VISION,
                    ProviderCapability.STRUCTURED_OUTPUT,
                },
                context_window=128000,
                max_output_tokens=16384,
                supports_streaming=True,
                supports_vision=True,
                supports_functions=True,
                supports_structured_output=True,
                cost_per_1k_input=0.00015,
                cost_per_1k_output=0.0006,
                metadata={"type": "proprietary", "family": "gpt-4o"},
            ),
            ModelCapability(
                name="gpt-4o",
                provider="OpenRouter",
                capabilities={
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.STREAMING,
                    ProviderCapability.FUNCTION_CALLING,
                    ProviderCapability.VISION,
                    ProviderCapability.STRUCTURED_OUTPUT,
                    ProviderCapability.CODE_GENERATION,
                },
                context_window=128000,
                max_output_tokens=16384,
                supports_streaming=True,
                supports_vision=True,
                supports_functions=True,
                supports_structured_output=True,
                cost_per_1k_input=0.0025,
                cost_per_1k_output=0.01,
                metadata={"type": "proprietary", "family": "gpt-4o"},
            ),
        ],
        metadata={"docs_url": "https://openrouter.ai/docs"},
    )


def _build_default_local() -> ProviderDefinition:
    """Build the default Local provider definition (always available)."""
    return ProviderDefinition(
        name="Local",
        base_url="http://localhost:11434/v1",
        api_key_env="",
        default_capabilities={
            ProviderCapability.CHAT_COMPLETION,
            ProviderCapability.TEXT_GENERATION,
            ProviderCapability.STREAMING,
            ProviderCapability.FUNCTION_CALLING,
        },
        default_quota=InferenceQuota(
            tokens_per_minute=0,
            tokens_per_day=0,
            requests_per_minute=0,
            max_concurrent=4,
        ),
        priority=30,
        health=ProviderHealth(
            status=ProviderStatus.HEALTHY,
            message="Local provider — always available",
        ),
        models=[
            ModelCapability(
                name="local-model",
                provider="Local",
                capabilities={
                    ProviderCapability.CHAT_COMPLETION,
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.STREAMING,
                    ProviderCapability.FUNCTION_CALLING,
                },
                context_window=8192,
                max_output_tokens=4096,
                supports_streaming=True,
                supports_functions=True,
                is_available=True,
                metadata={"type": "local", "backend": "ollama"},
            ),
        ],
        metadata={"note": "Falls back to Ollama-compatible endpoint at localhost:11434"},
    )


def get_default_provider_registry() -> ProviderRegistry:
    """Return the singleton default provider registry.

    Creates and seeds the registry with Groq, OpenRouter, and Local on
    first call.  Safe to call multiple times — the singleton is reused.
    """
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = ProviderRegistry()
        _DEFAULT_REGISTRY.register(_build_default_groq())
        _DEFAULT_REGISTRY.register(_build_default_openrouter())
        _DEFAULT_REGISTRY.register(_build_default_local())
    return _DEFAULT_REGISTRY


def reset_default_provider_registry() -> None:
    """Reset the default provider registry singleton.

    Useful for testing or re-initialisation.
    """
    global _DEFAULT_REGISTRY
    _DEFAULT_REGISTRY = None