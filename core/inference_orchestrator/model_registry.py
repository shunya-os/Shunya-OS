"""SHUNYA Inference Orchestrator — Model Registry.

Runtime-discoverable registry of models, decoupled from providers.
Models can be registered directly or discovered through provider
registries.
"""

from __future__ import annotations

from typing import Any

from .models import (
    InferenceRequest,
    ModelCapability,
    ProviderCapability,
    RoutingPriority,
)


class ModelRegistry:
    """Runtime-discoverable registry of models.

    Models are registered independently of providers, enabling the
    orchestrator to search across all available models without being
    tied to a specific provider's registry structure.
    """

    def __init__(self) -> None:
        self._models: dict[str, ModelCapability] = {}

    # ── Registration ────────────────────────────────────────────────────────

    def register(self, model: ModelCapability) -> None:
        """Register a model. Replaces any existing model with the same name.

        The model key is ``provider/name`` to avoid collisions when
        multiple providers offer models with the same name.
        """
        key = f"{model.provider}/{model.name}"
        self._models[key] = model

    def register_many(self, models: list[ModelCapability]) -> None:
        """Register multiple models at once."""
        for m in models:
            self.register(m)

    def unregister(self, provider: str, name: str) -> None:
        """Remove a model from the registry."""
        key = f"{provider}/{name}"
        self._models.pop(key, None)

    # ── Lookup ──────────────────────────────────────────────────────────────

    def get(self, provider: str, name: str) -> ModelCapability | None:
        """Get a model by provider and name. Returns None if not found."""
        return self._models.get(f"{provider}/{name}")

    def list(self) -> list[ModelCapability]:
        """Return all registered models."""
        return list(self._models.values())

    def list_available(self) -> list[ModelCapability]:
        """Return only models marked as available."""
        return [m for m in self._models.values() if m.is_available]

    def list_by_provider(self, provider: str) -> list[ModelCapability]:
        """Return all models belonging to a specific provider."""
        prefix = f"{provider}/"
        return [m for key, m in self._models.items() if key.startswith(prefix)]

    # ── Capability-based discovery ──────────────────────────────────────────

    def find_by_capability(
        self,
        capability: ProviderCapability | set[ProviderCapability],
        *,
        only_available: bool = True,
    ) -> list[ModelCapability]:
        """Find models that offer the given capability (or all of them).

        Parameters
        ----------
        capability : ProviderCapability | set[ProviderCapability]
            Single capability or set of required capabilities.
        only_available : bool
            If True, skip models flagged as unavailable.

        Returns
        -------
        list[ModelCapability]
            Matching models, sorted by cost_per_1k_input ascending.
        """
        required: set[ProviderCapability] = (
            {capability} if isinstance(capability, ProviderCapability)
            else capability
        )

        candidates = [
            m for m in self._models.values()
            if (not only_available or m.is_available)
            and m.has_all_capabilities(required)
        ]

        candidates.sort(key=lambda m: m.cost_per_1k_input)
        return candidates

    # ── Best-model selection ────────────────────────────────────────────────

    def find_best(
        self,
        request: InferenceRequest | None = None,
        *,
        required_capabilities: set[ProviderCapability] | None = None,
        priority: RoutingPriority = RoutingPriority.CAPABILITY,
        only_available: bool = True,
    ) -> ModelCapability | None:
        """Find the best model for the given criteria.

        Selection strategy depends on the priority:
        - COST: lowest cost_per_1k_input + cost_per_1k_output
        - LATENCY: highest max_output_tokens / context_window (proxy for speed)
        - CAPABILITY: most capabilities (largest capability set)
        - RELIABILITY: lowest cost, preferring providers with more models
        - MANUAL: use the explicit model in the request if provided

        When ``request`` is provided, its ``capabilities_required`` and
        ``priority`` fields are used as defaults.

        Parameters
        ----------
        request : InferenceRequest | None
            Optional request context to derive capabilities and priority.
        required_capabilities : set[ProviderCapability] | None
            Override capabilities (takes precedence over request).
        priority : RoutingPriority
            Selection strategy.  Defaults to CAPABILITY.
        only_available : bool
            If True, skip unavailable models.

        Returns
        -------
        ModelCapability | None
            The best matching model, or None if no model matches.
        """
        # Resolve required capabilities
        caps = required_capabilities
        if caps is None and request is not None:
            caps = request.capabilities_required
        if caps is None:
            caps = set()

        # Resolve priority
        if request is not None:
            priority = request.priority

        # If priority is MANUAL and the request specifies a model, try it
        if priority == RoutingPriority.MANUAL and request is not None:
            key = f"{request.provider}/{request.model}" if request.provider else request.model
            model = self._models.get(key) or self._models.get(f"/{request.model}")
            if model and (not only_available or model.is_available):
                if not caps or model.has_all_capabilities(caps):
                    return model
            return None

        # Gather candidates
        candidates = [
            m for m in self._models.values()
            if (not only_available or m.is_available)
            and (not caps or m.has_all_capabilities(caps))
        ]

        if not candidates:
            return None

        # Sort by priority
        if priority == RoutingPriority.COST:
            candidates.sort(key=lambda m: (
                m.cost_per_1k_input + m.cost_per_1k_output,
                -m.context_window,  # tie-break: prefer larger context
            ))
        elif priority == RoutingPriority.LATENCY:
            candidates.sort(key=lambda m: (
                -(m.max_output_tokens / max(m.context_window, 1)),  # "speed" proxy
                m.cost_per_1k_input,
            ), reverse=True)
        elif priority == RoutingPriority.RELIABILITY:
            candidates.sort(key=lambda m: (
                m.cost_per_1k_input + m.cost_per_1k_output,
                -len(m.capabilities),
            ))
        else:  # CAPABILITY (default)
            candidates.sort(key=lambda m: (
                -len(m.capabilities),
                m.cost_per_1k_input,
            ))

        return candidates[0]

    # ── Convenience ─────────────────────────────────────────────────────────

    def count(self) -> int:
        """Number of registered models."""
        return len(self._models)

    def clear(self) -> None:
        """Remove all registered models."""
        self._models.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            key: m.to_dict()
            for key, m in self._models.items()
        }


# ── Default Model Registry ──────────────────────────────────────────────────

_DEFAULT_MODEL_REGISTRY: ModelRegistry | None = None


def get_default_model_registry() -> ModelRegistry:
    """Return the singleton default model registry.

    Initialised empty.  Models are populated by the caller — typically
    by seeding from a ``ProviderRegistry`` via ``seed_from_providers``.
    Safe to call multiple times — the singleton is reused.
    """
    global _DEFAULT_MODEL_REGISTRY
    if _DEFAULT_MODEL_REGISTRY is None:
        _DEFAULT_MODEL_REGISTRY = ModelRegistry()
    return _DEFAULT_MODEL_REGISTRY


def reset_default_model_registry() -> None:
    """Reset the default model registry singleton.

    Useful for testing or re-initialisation.
    """
    global _DEFAULT_MODEL_REGISTRY
    _DEFAULT_MODEL_REGISTRY = None


def seed_model_registry_from_providers(
    model_registry: ModelRegistry | None = None,
    provider_registry: Any = None,
) -> ModelRegistry:
    """Convenience: seed a model registry from a provider registry.

    Iterates every provider's models and registers them.  Uses the
    default model registry if none is given.

    The ``provider_registry`` parameter is duck-typed to avoid circular
    imports — it only needs a ``list()`` method returning
    ``ProviderDefinition`` objects that have a ``models`` attribute.
    """
    from .provider_registry import get_default_provider_registry

    if model_registry is None:
        model_registry = get_default_model_registry()
    if provider_registry is None:
        provider_registry = get_default_provider_registry()

    for provider in provider_registry.list():
        for model in provider.models:
            model_registry.register(model)

    return model_registry