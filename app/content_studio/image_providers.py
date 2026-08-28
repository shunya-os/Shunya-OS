"""
Content Studio — Image Generation Provider Abstraction.

Provides configurable model routing with Economy/Standard/Premium tiers.
This replaces the hardcoded FLUX.1-schnell dependency with a provider registry.
"""
import os
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class ImageQualityTier(Enum):
    ECONOMY = "economy"
    STANDARD = "standard"
    PREMIUM = "premium"


@dataclass
class ProviderConfig:
    """Configuration for a single image generation provider."""
    name: str
    model: str
    tier: ImageQualityTier
    api_key_env: str
    base_url: Optional[str] = None
    default_params: dict = field(default_factory=dict)
    supports_aspect_ratio: bool = False
    supports_negative_prompt: bool = False
    max_dimensions: tuple = (1024, 1024)
    cost_per_image: float = 0.0  # USD, 0 = free
    is_default: bool = False


@dataclass
class GenerationResult:
    success: bool
    image_bytes: Optional[bytes] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None
    tier: Optional[str] = None


# ── Provider Registry ─────────────────────────────────────────────

class ProviderRegistry:
    """Registry of image generation providers with tier-based routing."""

    def __init__(self):
        self._providers: dict[str, ProviderConfig] = {}
        self._generators: dict[str, Callable] = {}

    def register(self, config: ProviderConfig, generator_fn: Callable) -> None:
        """Register a provider with its generator function."""
        self._providers[config.name] = config
        self._generators[config.name] = generator_fn
        logger.info(f"Image provider registered: {config.name} ({config.model}) [{config.tier.value}]")

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        return self._providers.get(name)

    def get_default_for_tier(self, tier: ImageQualityTier) -> Optional[ProviderConfig]:
        """Get the default provider for a given quality tier."""
        for config in self._providers.values():
            if config.tier == tier and config.is_default:
                return config
        # Fallback: first provider in tier
        for config in self._providers.values():
            if config.tier == tier:
                return config
        return None

    def get_all_for_tier(self, tier: ImageQualityTier) -> list[ProviderConfig]:
        return [c for c in self._providers.values() if c.tier == tier]

    def get_available_tiers(self) -> list[dict]:
        """Return available tiers with their providers for the frontend."""
        tiers = []
        for tier in ImageQualityTier:
            providers = self.get_all_for_tier(tier)
            if providers:
                tiers.append({
                    "tier": tier.value,
                    "label": tier.name.capitalize(),
                    "providers": [
                        {
                            "name": p.name,
                            "model": p.model,
                            "cost_per_image": p.cost_per_image,
                            "is_default": p.is_default,
                            "available": p.name in self._generators,
                        }
                        for p in providers
                    ],
                })
        return tiers

    def generate(self, prompt: str, tier: ImageQualityTier = ImageQualityTier.ECONOMY,
                 provider_name: Optional[str] = None, **kwargs) -> GenerationResult:
        """Generate an image using the specified tier or provider."""
        if provider_name:
            config = self._providers.get(provider_name)
            if not config:
                return GenerationResult(success=False, error=f"Unknown provider: {provider_name}")
            fn = self._generators.get(provider_name)
            if not fn:
                return GenerationResult(success=False, error=f"Provider not available: {provider_name}")
            try:
                result = fn(prompt, config, **kwargs)
                return result
            except Exception as e:
                return GenerationResult(success=False, error=str(e), provider=provider_name, model=config.model)

        # Route by tier
        config = self.get_default_for_tier(tier)
        if not config:
            return GenerationResult(success=False, error=f"No provider available for tier: {tier.value}")

        fn = self._generators.get(config.name)
        if not fn:
            return GenerationResult(success=False, error=f"Provider {config.name} not available")

        try:
            result = fn(prompt, config, **kwargs)
            return result
        except Exception as e:
            return GenerationResult(success=False, error=str(e), provider=config.name, model=config.model)


# ── Singleton ─────────────────────────────────────────────────────

_registry: Optional[ProviderRegistry] = None


def get_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


def reset_registry() -> None:
    """Reset the registry (useful for testing)."""
    global _registry
    _registry = None


# ── Provider Implementations ──────────────────────────────────────

def _generate_hf_image(prompt: str, config: ProviderConfig, **kwargs) -> GenerationResult:
    """Generate image using Hugging Face Inference API (free tier)."""
    from app.media.service import _get_hf_token, _generate_hf_image as _hf_gen

    api_key = _get_hf_token()
    if not api_key:
        return GenerationResult(
            success=False, error="HF_API_KEY not configured",
            provider=config.name, model=config.model, tier=config.tier.value,
        )

    try:
        raw_bytes = _hf_gen(prompt)
        return GenerationResult(
            success=True, image_bytes=raw_bytes,
            provider=config.name, model=config.model, tier=config.tier.value,
        )
    except Exception as e:
        return GenerationResult(
            success=False, error=str(e),
            provider=config.name, model=config.model, tier=config.tier.value,
        )


def _generate_dummy(prompt: str, config: ProviderConfig, **kwargs) -> GenerationResult:
    """Dummy fallback provider that returns a placeholder image (for testing)."""
    from PIL import Image
    import io

    img = Image.new("RGB", config.max_dimensions, (108, 74, 226))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return GenerationResult(
        success=True, image_bytes=buf.getvalue(),
        provider=config.name, model=config.model, tier=config.tier.value,
    )


# ── Initialization ────────────────────────────────────────────────

def init_providers() -> ProviderRegistry:
    """Initialize and register all available image providers."""
    registry = get_registry()

    # Economy tier: Hugging Face FLUX.1-schnell (free)
    registry.register(
        ProviderConfig(
            name="huggingface",
            model="black-forest-labs/FLUX.1-schnell",
            tier=ImageQualityTier.ECONOMY,
            api_key_env="HF_API_KEY",
            is_default=True,
            max_dimensions=(1024, 1024),
            cost_per_image=0.0,
        ),
        _generate_hf_image,
    )

    # Standard tier: placeholder for future provider (e.g., Stable Diffusion 3)
    # registry.register(
    #     ProviderConfig(
    #         name="stabilityai",
    #         model="stabilityai/stable-diffusion-3.5-large",
    #         tier=ImageQualityTier.STANDARD,
    #         api_key_env="STABILITY_API_KEY",
    #         is_default=True,
    #         max_dimensions=(1024, 1024),
    #         cost_per_image=0.04,
    #     ),
    #     _generate_hf_image,
    # )

    # Premium tier: placeholder for future provider
    # registry.register(
    #     ProviderConfig(
    #         name="openai",
    #         model="dall-e-3",
    #         tier=ImageQualityTier.PREMIUM,
    #         api_key_env="OPENAI_API_KEY",
    #         is_default=True,
    #         max_dimensions=(1792, 1024),
    #         cost_per_image=0.08,
    #     ),
    #     _generate_dummy,
    # )

    # Register dummy fallback for testing
    registry.register(
        ProviderConfig(
            name="dummy",
            model="dummy-rgb",
            tier=ImageQualityTier.ECONOMY,
            api_key_env="",
            is_default=False,
            max_dimensions=(512, 512),
            cost_per_image=0.0,
        ),
        _generate_dummy,
    )

    return registry