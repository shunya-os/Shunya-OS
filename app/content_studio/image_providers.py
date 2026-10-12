"""
Content Studio — Image Generation Provider Abstraction.

Provides configurable model routing with Economy/Standard/Premium tiers.
This replaces the hardcoded FLUX.1-schnell dependency with a provider registry.

ZG-03 B2: the registry now reports TRUTHFUL availability (key configured AND
provider not in known outage), exposes Pollinations as a genuinely working
free image fallback, keeps the dummy placeholder test-only, and classifies
failures with the shared ErrorClass taxonomy.
"""
import logging
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable

from app.ai.model_catalog import (
    ErrorClass,
    classify_exception,
    classify_http_status,
    provider_outage,
)

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
    error_class: Optional[str] = None
    tier: Optional[str] = None
    retryable: Optional[bool] = None


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
        """Get the default provider for a given quality tier.

        B2: the default must be genuinely available — a provider marked
        ``is_default`` but in outage (HF credits_required) is skipped in
        favour of the first effectively available provider in the tier.
        """
        for config in self._providers.values():
            if config.tier == tier and config.is_default and self._is_effectively_available(config):
                return config
        # Fallback: first effectively available provider in tier
        for config in self._providers.values():
            if config.tier == tier and self._is_effectively_available(config):
                return config
        # Last resort: first provider in tier (no available provider at all)
        for config in self._providers.values():
            if config.tier == tier:
                return config
        return None

    def get_all_for_tier(self, tier: ImageQualityTier) -> list[ProviderConfig]:
        return [c for c in self._providers.values() if c.tier == tier]

    def _is_effectively_available(self, config: ProviderConfig) -> bool:
        """Truthful availability (B2): generator registered AND not in outage.

        Registration alone is NOT availability — a provider whose key is
        missing or whose service is down (HF credits_required) is unavailable
        even though its generator function exists.
        """
        if config.name not in self._generators:
            return False
        if config.name == "dummy":
            # Test-only placeholder: only visible in testing environments.
            return os.getenv("SHUNYA_ENVIRONMENT", "production") == "testing"
        if provider_outage(config.name):
            return False
        # HF additionally requires a configured token.
        if config.name == "huggingface":
            from app.media.service import _get_hf_token
            if not _get_hf_token():
                return False
        return True

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
                            "available": self._is_effectively_available(p),
                        }
                        for p in providers
                        if p.name != "dummy" or os.getenv("SHUNYA_ENVIRONMENT", "production") == "testing"
                    ],
                })
        return tiers

    def generate(self, prompt: str, tier: ImageQualityTier = ImageQualityTier.ECONOMY,
                 provider_name: Optional[str] = None, **kwargs) -> GenerationResult:
        """Generate an image using the specified tier or provider."""
        if provider_name:
            config = self._providers.get(provider_name)
            if not config:
                return GenerationResult(
                    success=False, error=f"Unknown provider: {provider_name}",
                    error_class=ErrorClass.BAD_REQUEST.value,
                )
            fn = self._generators.get(provider_name)
            if not fn:
                return GenerationResult(
                    success=False, error=f"Provider not available: {provider_name}",
                    error_class=ErrorClass.PROVIDER_OUTAGE.value,
                )
            try:
                result = fn(prompt, config, **kwargs)
                return result
            except Exception as e:
                return GenerationResult(
                    success=False, error=str(e), error_class=classify_exception(e).value,
                    provider=provider_name, model=config.model,
                )

        # Route by tier — get_default_for_tier prefers an effectively available
        # provider (B2), so an outage (HF credits) falls through to the next.
        config = self.get_default_for_tier(tier)
        if not config:
            return GenerationResult(
                success=False, error=f"No provider available for tier: {tier.value}",
                error_class=ErrorClass.PROVIDER_OUTAGE.value,
            )

        fn = self._generators.get(config.name)
        if not fn:
            return GenerationResult(
                success=False, error=f"Provider {config.name} not available",
                error_class=ErrorClass.PROVIDER_OUTAGE.value,
                provider=config.name, model=config.model,
            )

        try:
            result = fn(prompt, config, **kwargs)
            return result
        except Exception as e:
            return GenerationResult(
                success=False, error=str(e), error_class=classify_exception(e).value,
                provider=config.name, model=config.model,
            )


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
        from app.ai.model_catalog import classify_exception
        error_class = classify_exception(e)
        return GenerationResult(
            success=False, error=str(e), error_class=error_class.value,
            provider=config.name, model=config.model, tier=config.tier.value,
            retryable=error_class.retryable,
        )


def _generate_pollinations_image(prompt: str, config: ProviderConfig, **kwargs) -> GenerationResult:
    """Generate an image via Pollinations (free, no API key).

    https://image.pollinations.ai/prompt/<prompt>?width=&height=&nologo=true
    Verified 2026-10-13 returning a real JPEG at zero cost.
    """
    import httpx
    from urllib.parse import quote

    width, height = kwargs.get("width", 1024), kwargs.get("height", 1024)
    url = (
        "https://image.pollinations.ai/prompt/"
        f"{quote(prompt[:500])}?width={int(width)}&height={int(height)}&nologo=true"
    )
    try:
        resp = httpx.get(url, timeout=httpx.Timeout(60.0, connect=10.0, read=55.0), follow_redirects=True)
        resp.raise_for_status()
        if not resp.content or resp.content[:2] not in (b"\xff\xd8", b"\x89PN"):
            return GenerationResult(
                success=False, error="Pollinations returned a non-image response",
                error_class=ErrorClass.PROVIDER_OUTAGE.value,
                provider=config.name, model=config.model, tier=config.tier.value,
            )
        return GenerationResult(
            success=True, image_bytes=resp.content,
            provider=config.name, model=config.model, tier=config.tier.value,
        )
    except httpx.HTTPStatusError as e:
        return GenerationResult(
            success=False, error=str(e),
            error_class=classify_http_status(e.response.status_code).value,
            provider=config.name, model=config.model, tier=config.tier.value,
            retryable=classify_http_status(e.response.status_code).retryable,
        )
    except Exception as e:
        return GenerationResult(
            success=False, error=str(e),
            error_class=classify_exception(e).value,
            provider=config.name, model=config.model, tier=config.tier.value,
            retryable=classify_exception(e).retryable,
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

    # Economy tier: Hugging Face FLUX.1-schnell (free — currently in outage:
    # HF requires prepaid credits, 402 reproduced 2026-10-13; remains registered
    # so generation attempts are classified truthfully).
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

    # Economy tier: Pollinations — free, no API key, genuinely working image
    # fallback (verified 2026-10-13). Picked automatically when HF is in
    # outage so image generation never silently degrades to a text concept.
    registry.register(
        ProviderConfig(
            name="pollinations",
            model="pollinations",
            tier=ImageQualityTier.ECONOMY,
            api_key_env="",
            is_default=False,
            max_dimensions=(1024, 1024),
            cost_per_image=0.0,
        ),
        _generate_pollinations_image,
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

    # Register dummy fallback for testing ONLY — never in production. A
    # solid-color placeholder presented as a generated image is a fake
    # success; exposing it to real users is forbidden (ZG-03 B2).
    if os.getenv("SHUNYA_ENVIRONMENT", "") == "testing":
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
