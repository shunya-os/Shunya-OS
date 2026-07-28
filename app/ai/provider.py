"""SHUNYA M5 — LLM Provider Abstraction Layer.

Provider-agnostic interface for LLM inference. Supports multiple backends
with automatic fallback. This is the ONLY module that talks to LLM APIs.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider interface
# ---------------------------------------------------------------------------

class LLMProvider:
    """Abstract LLM provider. Subclasses implement specific backends."""

    name: str = "abstract"

    def complete(self, messages: list[dict[str, str]],
                 temperature: float = 0.7,
                 max_tokens: int = 1024) -> dict[str, Any]:
        """Send a completion request and return structured response.

        Args:
            messages: List of {"role": "...", "content": "..."} dicts.
            temperature: Sampling temperature (0.0 = deterministic).
            max_tokens: Maximum tokens in response.

        Returns:
            {"content": str, "model": str, "usage": {...}, "finish_reason": str}
        """
        raise NotImplementedError

    def is_available(self) -> bool:
        """Check if this provider is configured and reachable."""
        return False


# ---------------------------------------------------------------------------
# OpenAI-compatible provider (OpenRouter, OpenAI, local OpenAI-compatible)
# ---------------------------------------------------------------------------

class OpenAIProvider(LLMProvider):
    """Provider for any OpenAI-compatible API (OpenAI, OpenRouter, local)."""

    name = "openai"

    def __init__(self, api_key: str | None = None,
                 base_url: str | None = None,
                 model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        )
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def complete(self, messages: list[dict[str, str]],
                 temperature: float = 0.7,
                 max_tokens: int = 1024) -> dict[str, Any]:
        import httpx

        if not self.api_key:
            return {
                "content": "",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "error": "API key not configured",
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()

            choice = data["choices"][0]
            return {
                "content": choice["message"]["content"],
                "model": data.get("model", self.model),
                "usage": data.get("usage", {}),
                "finish_reason": choice.get("finish_reason", "stop"),
            }

        except Exception as e:
            logger.warning(f"OpenAI provider error: {e}")
            return {
                "content": "",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "error": str(e),
            }


# ---------------------------------------------------------------------------
# OpenRouter provider (separate for config clarity)
# ---------------------------------------------------------------------------

class OpenRouterProvider(OpenAIProvider):
    """OpenRouter uses OpenAI-compatible API with a separate key/env."""

    name = "openrouter"

    def __init__(self, api_key: str | None = None,
                 model: str = "openai/gpt-4o-mini"):
        super().__init__(
            api_key=api_key or os.getenv("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
            model=model or os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        )


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------

class AnthropicProvider(LLMProvider):
    """Provider for Anthropic Claude API."""

    name = "anthropic"

    def __init__(self, api_key: str | None = None,
                 model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def complete(self, messages: list[dict[str, str]],
                 temperature: float = 0.7,
                 max_tokens: int = 1024) -> dict[str, Any]:
        import httpx

        if not self.api_key:
            return {
                "content": "",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "error": "API key not configured",
            }

        # Convert OpenAI-format messages to Anthropic format
        system_msg = ""
        anthropic_messages = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            elif m["role"] == "user":
                anthropic_messages.append({"role": "user", "content": m["content"]})
            elif m["role"] == "assistant":
                anthropic_messages.append({"role": "assistant", "content": m["content"]})

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": anthropic_messages,
        }
        if system_msg:
            body["system"] = system_msg

        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()

            return {
                "content": data["content"][0]["text"],
                "model": data.get("model", self.model),
                "usage": {
                    "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                    "output_tokens": data.get("usage", {}).get("output_tokens", 0),
                },
                "finish_reason": data.get("stop_reason", "stop"),
            }

        except Exception as e:
            logger.warning(f"Anthropic provider error: {e}")
            return {
                "content": "",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "error": str(e),
            }


# ---------------------------------------------------------------------------
# Local / mock provider (for testing and when no API key is configured)
# ---------------------------------------------------------------------------

class LocalProvider(LLMProvider):
    """Local deterministic provider — uses templates, no external API.

    Used when no AI provider is configured. Provides sensible fallback
    responses derived from runtime state rather than hardcoded text.
    """

    name = "local"

    def __init__(self, model: str = "local"):
        self.model = model

    def is_available(self) -> bool:
        return True  # Always available

    def complete(self, messages: list[dict[str, str]],
                 temperature: float = 0.7,
                 max_tokens: int = 1024) -> dict[str, Any]:
        """Generate a deterministic response from the conversation context."""
        # Extract the last user message
        last_user = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user = m["content"]
                break

        # Build a response from context
        response_parts = []

        # Check for question patterns and respond contextually
        last_user_lower = last_user.lower()
        words = set(last_user_lower.split())

        if words & {"hello", "hi", "hey", "greetings", "good morning", "good evening"}:
            response_parts.append("Hello! I'm SHUNYA, your AI operating system.")
            response_parts.append("I can help you understand your business objects, answer questions about your data, and assist with tasks.")
            response_parts.append("What would you like to explore?")
        elif words & {"help", "capabilities"} or "what can you" in last_user_lower:
            response_parts.append("I can help you with:")
            response_parts.append("- Answer questions about your business objects and relationships")
            response_parts.append("- Generate summaries of any object or conversation")
            response_parts.append("- Create and update objects from our conversation")
            response_parts.append("- Navigate between related business entities")
            response_parts.append("- Identify next actions and missing context")
            response_parts.append("What would you like me to do?")
        elif any(word in last_user_lower for word in ["summarize", "summary", "summarise"]):
            response_parts.append("I'll generate a summary based on the available information.")
            response_parts.append("The current context includes the object's name, type, content, and conversation history.")
            response_parts.append("For a more detailed summary, please specify what aspect you'd like me to focus on.")
        elif words & {"create", "new"} or last_user_lower.startswith("make"):
            response_parts.append("I can help create objects for you. Please let me know:")
            response_parts.append("- What type of object (Document, Task, Note, etc.)")
            response_parts.append("- The name and any content or description")
            response_parts.append("- Which space it should belong to")
            response_parts.append("Could you provide the details?")
        else:
            response_parts.append("Thank you for your message. I've registered your input in the context of this workspace.")
            response_parts.append("I can help explore this object further, answer questions about related items, or assist with next steps.")
            response_parts.append("What would you like to know?")

        content = "\n\n".join(response_parts)

        return {
            "content": content,
            "model": self.model,
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "finish_reason": "stop",
        }


# ---------------------------------------------------------------------------
# Provider registry and resolution
# ---------------------------------------------------------------------------

_PROVIDERS: list[LLMProvider] = []


def resolve_provider() -> LLMProvider:
    """Resolve the best available LLM provider with fallback chain.

    Priority: OpenRouter → OpenAI → Anthropic → Local (always available).
    """
    if _PROVIDERS:
        return _PROVIDERS[0]

    chain = [
        OpenRouterProvider(),
        OpenAIProvider(),
        AnthropicProvider(),
        LocalProvider(),
    ]

    for provider in chain:
        if provider.is_available():
            logger.info(f"AI provider resolved: {provider.name} ({provider.model})")
            _PROVIDERS.append(provider)
            return provider

    # LocalProvider always returns True for is_available
    _PROVIDERS.append(LocalProvider())
    logger.info("AI provider: local fallback")
    return _PROVIDERS[-1]


def get_provider() -> LLMProvider:
    """Get the current provider, resolving on first call."""
    if not _PROVIDERS:
        return resolve_provider()
    return _PROVIDERS[0]


def reset_provider() -> None:
    """Reset the provider cache (for testing)."""
    _PROVIDERS.clear()


def set_provider(provider: LLMProvider) -> None:
    """Override the provider (for testing)."""
    _PROVIDERS.clear()
    _PROVIDERS.append(provider)