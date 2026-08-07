"""
SHUNYA — Configurable AI Provider Registry

Provider-agnostic interface for LLM inference. Supports multiple backends
with automatic fallback. This is the ONLY module that talks to LLM APIs.

Constitutional Directive — Open Capability Acceleration §6:
Providers SHALL be: health-aware, priority-aware, replaceable,
observable, configurable, fault-tolerant. Chain order, models, and
API keys configured via environment, not hard-coded in source.
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

        Returns:
            {"content": str, "model": str, "usage": {...}, "finish_reason": str}
        """
        raise NotImplementedError

    def is_available(self) -> bool:
        """Check if this provider is configured and reachable."""
        return False


# ---------------------------------------------------------------------------
# OpenAI-compatible provider (reusable base class)
# ---------------------------------------------------------------------------

class OpenAIProvider(LLMProvider):
    """Provider for any OpenAI-compatible API (OpenAI, OpenRouter, local, Groq, etc.)."""

    name = "openai"

    def __init__(self, api_key: str | None = None,
                 base_url: str | None = None,
                 model: str = "gpt-4o-mini"):
        self.api_key = api_key or ""
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model

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
            logger.warning(f"OpenAI provider ({self.name}) error: {e}")
            return {
                "content": "",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "error": str(e),
            }


# ---------------------------------------------------------------------------
# Specific providers
# ---------------------------------------------------------------------------

class GroqProvider(OpenAIProvider):
    """Groq — fastest free inference. 30 req/min, 14,400 req/day."""
    name = "groq"

    def __init__(self, api_key: str | None = None,
                 model: str = "llama-3.1-8b-instant"):
        super().__init__(
            api_key=api_key or os.getenv("GROQ_API_KEY", ""),
            base_url="https://api.groq.com/openai/v1",
            model=model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        )


class GeminiProvider(OpenAIProvider):
    """Google Gemini — 60 req/min free, 1M token context, no credit card needed."""
    name = "gemini"

    def __init__(self, api_key: str | None = None,
                 model: str = "gemini-2.0-flash"):
        super().__init__(
            api_key=api_key or os.getenv("GEMINI_API_KEY", ""),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            model=model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        )


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter — access to many free and paid models through one API."""
    name = "openrouter"

    def __init__(self, api_key: str | None = None,
                 model: str = "deepseek/deepseek-chat"):
        super().__init__(
            api_key=api_key or os.getenv("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
            model=model or os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat"),
        )


class CloudflareAIProvider(LLMProvider):
    """Cloudflare Workers AI — 100k req/day free. No API key needed for Workers."""
    name = "cloudflare"

    def __init__(self, account_id: str | None = None,
                 api_token: str | None = None,
                 model: str = "@cf/meta/llama-3.1-8b-instruct"):
        self.account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
        self.api_token = api_token or os.getenv("CLOUDFLARE_API_TOKEN", "")
        self.model = model or os.getenv("CLOUDFLARE_MODEL", "@cf/meta/llama-3.1-8b-instruct")

    def is_available(self) -> bool:
        return bool(self.account_id) or bool(os.getenv("CLOUDFLARE_ACCOUNT_ID", ""))

    def complete(self, messages: list[dict[str, str]],
                 temperature: float = 0.7,
                 max_tokens: int = 1024) -> dict[str, Any]:
        import httpx

        token = self.api_token or os.getenv("CLOUDFLARE_API_TOKEN", "")
        acct = self.account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID", "")

        # Extract the last user message for the prompt
        prompt = ""
        for m in reversed(messages):
            if m["role"] == "user":
                prompt = m["content"]
                break

        headers = {"Authorization": f"Bearer {token}"}
        body = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{self.model}"

        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()

            result = data.get("result", {})
            response_text = result.get("response", "")

            return {
                "content": response_text,
                "model": self.model,
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "finish_reason": "stop",
            }
        except Exception as e:
            logger.warning(f"Cloudflare AI provider error: {e}")
            return {
                "content": "",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "error": str(e),
            }


class HuggingFaceProvider(OpenAIProvider):
    """Hugging Face Inference API — 30k chars/month free, 150k+ models."""
    name = "huggingface"

    def __init__(self, api_key: str | None = None,
                 model: str = "meta-llama/Llama-3.2-3B-Instruct"):
        super().__init__(
            api_key=api_key or os.getenv("HF_API_KEY", ""),
            base_url="https://api-inference.huggingface.co/v1",
            model=model or os.getenv("HF_MODEL", "meta-llama/Llama-3.2-3B-Instruct"),
        )


class TogetherAIProvider(OpenAIProvider):
    """Together AI — quality open models, 1k req/min free tier."""
    name = "togetherai"

    def __init__(self, api_key: str | None = None,
                 model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"):
        super().__init__(
            api_key=api_key or os.getenv("TOGETHER_API_KEY", ""),
            base_url="https://api.together.xyz/v1",
            model=model or os.getenv("TOGETHER_MODEL", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
        )


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API."""
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


class LocalProvider(LLMProvider):
    """Local deterministic fallback — always available, no API key needed."""
    name = "local"

    def __init__(self, model: str = "local"):
        self.model = model

    def is_available(self) -> bool:
        return True

    def complete(self, messages: list[dict[str, str]],
                 temperature: float = 0.7,
                 max_tokens: int = 1024) -> dict[str, Any]:
        last_user = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user = m["content"]
                break

        response_parts = []
        last_user_lower = last_user.lower()
        words = set(last_user_lower.split())

        if words & {"hello", "hi", "hey", "greetings"}:
            response_parts.append("Hello! I'm SHUNYA, your AI operating system.")
            response_parts.append("What would you like to explore?")
        elif "what can you" in last_user_lower:
            response_parts.append("I can answer questions, summarize objects, create records, navigate related items, and more.")
        elif any(word in last_user_lower for word in ["summarize", "summary"]):
            response_parts.append("I'll generate a summary based on available information.")
        else:
            response_parts.append("Thank you. I've registered your input and can assist further.")

        content = "\n\n".join(response_parts)
        return {
            "content": content,
            "model": self.model,
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "finish_reason": "stop",
        }


# ---------------------------------------------------------------------------
# Configurable Provider Registry
# ---------------------------------------------------------------------------

PROVIDER_CLASSES: dict[str, type[LLMProvider]] = {
    "groq": GroqProvider,
    "gemini": GeminiProvider,
    "openrouter": OpenRouterProvider,
    "cloudflare": CloudflareAIProvider,
    "huggingface": HuggingFaceProvider,
    "togetherai": TogetherAIProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "local": LocalProvider,
}


class ProviderRegistry:
    """Configurable, health-aware, priority-aware provider chain.

    Per Constitutional Directive §6:
    Providers SHALL be: health-aware, priority-aware, replaceable,
    observable, configurable, fault-tolerant.

    Chain order is configured via SHUNYA_AI_PROVIDERS env var
    (comma-separated list of provider IDs) or defaults to the full chain.
    """

    def __init__(self):
        self._chain: list[LLMProvider] = []
        self._resolved: list[LLMProvider] = []
        self._provider_map: dict[str, LLMProvider] = {}

    def _build_chain(self) -> list[LLMProvider]:
        """Build provider chain from config or default."""
        # Parse comma-separated provider IDs from env or use full chain
        config = os.getenv("SHUNYA_AI_PROVIDERS", "")
        if config:
            ids = [p.strip() for p in config.split(",") if p.strip()]
        else:
            # Default chain: highest quality → most available
            ids = ["groq", "gemini", "openrouter", "cloudflare",
                   "huggingface", "togetherai", "anthropic", "openai", "local"]

        chain = []
        for pid in ids:
            cls = PROVIDER_CLASSES.get(pid)
            if cls:
                chain.append(cls())
        return chain

    def resolve(self) -> LLMProvider:
        """Resolve the first available provider. Caches result."""
        if self._resolved:
            return self._resolved[0]

        if not self._chain:
            self._chain = self._build_chain()

        # Find the first available provider
        for provider in self._chain:
            if provider.is_available():
                logger.info(f"AI provider resolved: {provider.name} ({provider.model})")
                self._resolved.append(provider)
                return provider

        # Fallback — LocalProvider always works
        fallback = LocalProvider()
        logger.info("AI provider: local fallback")
        self._resolved.append(fallback)
        return fallback

    def get(self) -> LLMProvider:
        """Get the current provider."""
        if not self._resolved:
            return self.resolve()
        return self._resolved[0]

    def reset(self):
        """Clear cached resolution (e.g., after config change)."""
        self._resolved.clear()
        self._chain.clear()

    @property
    def chain(self) -> list[LLMProvider]:
        if not self._chain:
            self._chain = self._build_chain()
        return list(self._chain)

    @property
    def all_available(self) -> list[LLMProvider]:
        """Return all providers that are currently available."""
        return [p for p in self.chain if p.is_available()]


# Singleton registry
_registry = ProviderRegistry()


# ---------------------------------------------------------------------------
# Backward-compatible API
# ---------------------------------------------------------------------------

def resolve_provider() -> LLMProvider:
    return _registry.resolve()


def get_provider() -> LLMProvider:
    return _registry.get()


def reset_provider() -> None:
    _registry.reset()


def set_provider(provider: LLMProvider) -> None:
    _registry.reset()
    _registry._resolved.clear()
    _registry._resolved.append(provider)


def get_all_providers() -> list[LLMProvider]:
    """Return all configured providers regardless of availability."""
    return _registry.chain


def get_available_providers() -> list[LLMProvider]:
    """Return only providers that are available right now."""
    return _registry.all_available
