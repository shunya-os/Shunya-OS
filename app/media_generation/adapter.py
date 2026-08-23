"""SHUNYA Media Generation Adapter — abstract provider pattern.

MediaProvider is the abstract base class. ProviderRegistry discovers and
loads registered providers. ImageProvider is a concrete subclass.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class MediaProvider(ABC):
    """Abstract base for media generation providers."""

    name: str = "base"

    @abstractmethod
    def generate(self, config: dict[str, Any]) -> dict[str, Any]:
        """Generate media from the given configuration.

        Returns a result dict with keys:
            success (bool)    — True if generation succeeded
            url (str)         — URL or path to the generated media
            metadata (dict)   — provider-specific metadata (e.g. dimensions, duration)
            provider (str)    — provider name that generated the media
            error (str)       — error message if success is False
        """
        ...


class ImageProvider(MediaProvider):
    """Concrete image generation provider.

    Expects config keys:
        - prompt (str): the image generation prompt
        - size (str, optional): e.g. "1024x1024"
        - model (str, optional): model name override
        - provider_key (str, optional): API key when required
    """

    name = "image_provider"

    def __init__(self, api_key: Optional[str] = None, model: str = "default-image-model"):
        self.api_key = api_key
        self.model = model

    def generate(self, config: dict[str, Any]) -> dict[str, Any]:
        prompt = config.get("prompt", "")
        if not prompt:
            return {
                "success": False,
                "url": "",
                "metadata": {},
                "provider": self.name,
                "error": "prompt is required",
            }

        try:
            # Placeholder — real integration would call an image API
            # e.g. OpenAI DALL-E, Stability AI, or local diffusion model.
            logger.info(
                "ImageProvider.generate called — prompt=%.60s model=%s",
                prompt,
                config.get("model", self.model),
            )

            # Simulated success result
            result = {
                "success": True,
                "url": f"generated://images/{hash(prompt)}",
                "metadata": {
                    "prompt": prompt[:200],
                    "model": config.get("model", self.model),
                    "size": config.get("size", "1024x1024"),
                },
                "provider": self.name,
                "error": "",
            }
            return result

        except Exception as exc:
            logger.error("ImageProvider.generate failed: %s", exc)
            return {
                "success": False,
                "url": "",
                "metadata": {},
                "provider": self.name,
                "error": str(exc),
            }


class ProviderRegistry:
    """Registry that discovers and loads registered media providers.

    Providers are registered by name. The registry supports lazy resolution
    and a fallback chain similar to the search provider pattern.
    """

    def __init__(self):
        self._providers: dict[str, MediaProvider] = {}
        self._default_provider: Optional[str] = None

    def register(self, name: str, provider: MediaProvider, set_default: bool = False) -> None:
        """Register a provider under the given name."""
        self._providers[name] = provider
        if set_default or self._default_provider is None:
            self._default_provider = name
        logger.info("Media provider registered: %s", name)

    def get(self, name: str) -> Optional[MediaProvider]:
        """Get a provider by name."""
        return self._providers.get(name)

    def get_default(self) -> Optional[MediaProvider]:
        """Get the default (first registered or explicitly set) provider."""
        if self._default_provider:
            return self._providers.get(self._default_provider)
        return None

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._providers.keys())

    def resolve(self, preferred: Optional[str] = None) -> Optional[MediaProvider]:
        """Resolve a provider, falling back to the default.

        Args:
            preferred: Optional preferred provider name. If available, returns it.
                       Otherwise falls back to the default.
        """
        if preferred and preferred in self._providers:
            return self._providers[preferred]
        return self.get_default()

    def load_all(self) -> list[MediaProvider]:
        """Load and return all registered providers (triggers import resolution)."""
        from importlib import import_module

        registered = []
        for name, provider in self._providers.items():
            try:
                _ = provider.generate({"prompt": "__probe__", "_probe": True})
            except Exception:
                pass
            registered.append(provider)
        return registered


# Module-level singleton
_registry = ProviderRegistry()

# Register default providers
_registry.register("image", ImageProvider(), set_default=True)


def get_registry() -> ProviderRegistry:
    """Get the global media provider registry."""
    return _registry