"""SHUNYA Media Generation — abstract provider model for media generation.

Provides the abstract MediaProvider base class and the ProviderRegistry
for discovering and loading registered media generation providers.
"""

from .adapter import MediaProvider, ImageProvider, ProviderRegistry

__all__ = [
    "MediaProvider",
    "ImageProvider",
    "ProviderRegistry",
]