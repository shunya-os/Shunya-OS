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

from app.ai.model_catalog import (
    ErrorClass,
    classify_exception,
    classify_http_status,
    configured_chain,
    is_paid,
    is_retired,
    provider_outage,
    resolve_default_model,
)

logger = logging.getLogger(__name__)

# Public alias so callers/tests can reference the taxonomy without importing
# the catalog module directly.
__all__ = [
    "LLMProvider", "OpenAIProvider", "GroqProvider", "GeminiProvider",
    "OpenRouterProvider", "CloudflareAIProvider", "HuggingFaceProvider",
    "TogetherAIProvider", "AnthropicProvider", "LocalProvider",
    "UnavailableProvider", "ProviderRegistry",
    "PROVIDER_CLASSES", "resolve_provider", "get_provider", "set_provider",
    "get_all_providers", "get_available_providers", "complete_with_failover",
    "ErrorClass",
]


# ---------------------------------------------------------------------------
# Provider interface
# ---------------------------------------------------------------------------

class LLMProvider:
    """Abstract LLM provider. Subclasses implement specific backends."""

    name: str = "abstract"
    model: str = ""

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
    provider_id = "openai"
    required_envs: tuple[str, ...] = ("OPENAI_API_KEY",)

    def __init__(self, api_key: str | None = None,
                 base_url: str | None = None,
                 model: str | None = None):
        self.api_key = api_key or ""
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def is_available(self) -> bool:
        """Truthful availability (B2): key configured AND model not retired.

        Registration or a configured key alone is NOT availability — a retired
        model id makes the provider unusable even with a valid key. Paid
        providers additionally require an explicit SHUNYA_AI_PROVIDERS entry.
        """
        if not self.api_key:
            return False
        if is_retired(self.provider_id, self.model):
            return False
        if is_paid(self.provider_id) and not self._is_configured_explicitly():
            return False
        return provider_outage(self.provider_id) is None

    def _is_configured_explicitly(self) -> bool:
        """Paid providers require an explicit SHUNYA_AI_PROVIDERS entry."""
        raw = os.getenv("SHUNYA_AI_PROVIDERS", "").strip()
        ids = [p.strip() for p in raw.split(",") if p.strip()]
        if not is_paid(self.provider_id):
            return True
        return self.provider_id in ids

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
                "error_class": ErrorClass.AUTH_MISSING.value,
                "provider": self.name,
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
            with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0, read=30.0)) as client:
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
                "provider": self.name,
                "error_class": None,
            }

        except httpx.HTTPStatusError as e:
            error_class = classify_http_status(
                e.response.status_code,
                model=self.model,
                retired_models=getattr(self, "retired_models", ()),
            )
            logger.warning("OpenAI provider (%s) error: %s", self.name, e)
            return {
                "content": "",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "error": str(e),
                "error_class": error_class.value,
                "provider": self.name,
            }
        except Exception as e:
            logger.warning(f"OpenAI provider ({self.name}) error: {e}")
            return {
                "content": "",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "error": str(e),
                "error_class": classify_exception(e).value,
                "provider": self.name,
            }


# ---------------------------------------------------------------------------
# Specific providers
# ---------------------------------------------------------------------------

class GroqProvider(OpenAIProvider):
    """Groq — fastest free inference. 30 req/min, 14,400 req/day."""
    name = "groq"
    provider_id = "groq"
    required_envs = ("GROQ_API_KEY",)
    retired_models = ("llama-3.3-70b-versatile",)

    def __init__(self, api_key: str | None = None,
                 model: str | None = None):
        super().__init__(
            api_key=api_key or os.getenv("GROQ_API_KEY", ""),
            base_url="https://api.groq.com/openai/v1",
            model=resolve_default_model("groq", model or os.getenv("GROQ_MODEL")),
        )


class GeminiProvider(OpenAIProvider):
    """Google Gemini — 60 req/min free, 1M token context, no credit card needed."""
    name = "gemini"
    provider_id = "gemini"
    required_envs = ("GEMINI_API_KEY",)
    retired_models = ("gemini-2.0-flash",)

    def __init__(self, api_key: str | None = None,
                 model: str | None = None):
        super().__init__(
            api_key=api_key or os.getenv("GEMINI_API_KEY", ""),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            model=resolve_default_model("gemini", model or os.getenv("GEMINI_MODEL")),
        )


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter — access to many free and paid models through one API."""
    name = "openrouter"
    provider_id = "openrouter"
    required_envs = ("OPENROUTER_API_KEY",)

    def __init__(self, api_key: str | None = None,
                 model: str | None = None):
        super().__init__(
            api_key=api_key or os.getenv("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
            model=resolve_default_model("openrouter", model or os.getenv("OPENROUTER_MODEL")),
        )


class CloudflareAIProvider(LLMProvider):
    """Cloudflare Workers AI — 100k req/day free with a valid account + token."""
    name = "cloudflare"
    provider_id = "cloudflare"
    required_envs = ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN")
    retired_models = ("@cf/meta/llama-3.1-8b-instruct",)

    def __init__(self, account_id: str | None = None,
                 api_token: str | None = None,
                 model: str | None = None):
        self.account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
        self.api_token = api_token or os.getenv("CLOUDFLARE_API_TOKEN", "")
        self.model = resolve_default_model(
            "cloudflare", model or os.getenv("CLOUDFLARE_MODEL")
        )

    def is_available(self) -> bool:
        """Truthful availability: BOTH account id and token required.

        Previously only account_id was checked — a provider with a token
        missing was reported available while every call returned 401.
        """
        if not (self.account_id and self.api_token):
            return False
        if is_retired("cloudflare", self.model):
            return False
        return True

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
            with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0, read=30.0)) as client:
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
        except httpx.HTTPStatusError as e:
            logger.warning("Cloudflare AI provider error: %s", e)
            return {
                "content": "",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "error": str(e),
                "error_class": classify_http_status(
                    e.response.status_code,
                    model=self.model,
                    retired_models=self.retired_models,
                ).value,
                "provider": self.name,
            }
        except Exception as e:
            logger.warning(f"Cloudflare AI provider error: {e}")
            return {
                "content": "",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "error": str(e),
                "error_class": classify_exception(e).value,
                "provider": self.name,
            }


class HuggingFaceProvider(OpenAIProvider):
    """Hugging Face Inference API — OpenAI-compatible endpoint.

    B2: the old ``api-inference.huggingface.co/v1`` endpoint was deprecated by
    Hugging Face (Inference Providers migration). The current endpoint is
    ``router.huggingface.co/v1`` and requires prepaid credits for inference
    (402 reproduced 2026-10-13) — so the provider is catalog-marked as being
    in outage and reports itself unavailable until credits are restored.
    """
    name = "huggingface"
    provider_id = "huggingface"
    required_envs = ("HF_API_KEY", "HF_TOKEN")

    def __init__(self, api_key: str | None = None,
                 model: str | None = None):
        super().__init__(
            api_key=api_key or os.getenv("HF_API_KEY", "") or os.getenv("HF_TOKEN", ""),
            base_url="https://router.huggingface.co/v1",
            model=resolve_default_model("huggingface", model or os.getenv("HF_MODEL")),
        )


class TogetherAIProvider(OpenAIProvider):
    """Together AI — quality open models, 1k req/min free tier."""
    name = "togetherai"
    provider_id = "togetherai"
    required_envs = ("TOGETHER_API_KEY",)

    def __init__(self, api_key: str | None = None,
                 model: str | None = None):
        super().__init__(
            api_key=api_key or os.getenv("TOGETHER_API_KEY", ""),
            base_url="https://api.together.xyz/v1",
            model=resolve_default_model("togetherai", model or os.getenv("TOGETHER_MODEL")),
        )


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API. PAID — only usable when explicitly configured."""
    name = "anthropic"
    provider_id = "anthropic"
    required_envs = ("ANTHROPIC_API_KEY",)
    retired_models = ("claude-3-haiku-20240307", "claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022")

    def __init__(self, api_key: str | None = None,
                 model: str | None = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = resolve_default_model("anthropic", model or os.getenv("ANTHROPIC_MODEL"))

    def is_available(self) -> bool:
        """Truthful availability: key AND not retired AND explicitly configured.

        Paid providers are never auto-selected from the default chain — an
        explicit ``SHUNYA_AI_PROVIDERS`` entry is required (no silent paid
        spending per ZG-03 B2 / user no-paid-tokens rule).
        """
        if not self.api_key:
            return False
        if is_retired("anthropic", self.model):
            return False
        return self._is_configured_explicitly()

    def _is_configured_explicitly(self) -> bool:
        raw = os.getenv("SHUNYA_AI_PROVIDERS", "").strip()
        ids = [p.strip() for p in raw.split(",") if p.strip()]
        return "anthropic" in ids

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
            with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0, read=30.0)) as client:
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
                "provider": self.name,
                "error_class": None,
            }
        except httpx.HTTPStatusError as e:
            logger.warning("Anthropic provider error: %s", e)
            return {
                "content": "",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "error": str(e),
                "error_class": classify_http_status(
                    e.response.status_code,
                    model=self.model,
                    retired_models=self.retired_models,
                ).value,
                "provider": self.name,
            }
        except Exception as e:
            logger.warning(f"Anthropic provider error: {e}")
            return {
                "content": "",
                "model": self.model,
                "usage": {},
                "finish_reason": "error",
                "error": str(e),
                "error_class": classify_exception(e).value,
                "provider": self.name,
            }


class LocalProvider(LLMProvider):
    """Local deterministic replies — TEST/OFFLINE ONLY (B2).

    Never the automatic fallback. ``resolve()`` will not pick it unless the
    chain explicitly includes ``local`` via ``SHUNYA_AI_PROVIDERS=local``
    (which the test harness does). Canned replies must never be presented as
    real AI output on the failure path.
    """
    name = "local"
    provider_id = "local"

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
            "provider": "local",
            "error_class": None,
        }


class UnavailableProvider(LLMProvider):
    """Truthful placeholder returned when NO provider in the chain is available.

    Its ``complete()`` never fabricates content — it reports the aggregate
    failure with per-provider classifications so callers can surface a truthful
    error instead of a canned reply.
    """

    name = "unavailable"
    provider_id = "unavailable"

    def __init__(self, unavailable: list[dict] | None = None):
        self.model = "none"
        self.unavailable = unavailable or []

    def is_available(self) -> bool:
        return False

    def complete(self, messages: list[dict[str, str]],
                 temperature: float = 0.7,
                 max_tokens: int = 1024) -> dict[str, Any]:
        reasons = "; ".join(
            f"{u.get('provider') or u.get('id', '?')}: {u.get('reason', 'unavailable')}"
            for u in self.unavailable
        ) or "no providers configured"
        return {
            "content": "",
            "model": "none",
            "usage": {},
            "finish_reason": "error",
            "error": f"No AI provider available — {reasons}",
            "error_class": ErrorClass.PROVIDER_OUTAGE.value,
            "provider": "unavailable",
            "unavailable": self.unavailable,
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
        """Build provider chain from catalog config (B2).

        ``SHUNYA_AI_PROVIDERS`` (comma-separated) overrides the default
        free-first chain; otherwise the catalog's ``DEFAULT_TEXT_CHAIN`` is
        used. Paid providers enter only when explicitly configured, and
        ``local`` only when explicitly requested (never as an implicit
        fallback).
        """
        ids = configured_chain()

        chain = []
        for pid in ids:
            cls = PROVIDER_CLASSES.get(pid)
            if cls:
                chain.append(cls())
        return chain

    def resolve(self) -> LLMProvider:
        """Resolve the first genuinely available provider. Caches result.

        B2: availability is truthful (key configured + model not retired +
        provider not in outage). When nothing is available the registry
        returns an ``UnavailableProvider`` — it never falls back to canned
        local replies as if they were AI output.
        """
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

        # Truthful failure instead of a fabricated reply
        unavailable = [
            {"provider": p.name, "model": p.model, "reason": "unavailable"}
            for p in self._chain
        ] or [{"provider": "none", "reason": "no providers configured"}]
        logger.warning("No AI provider available: %s", unavailable)
        placeholder = UnavailableProvider(unavailable)
        self._resolved.append(placeholder)
        return placeholder

    def complete_with_failover(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """Complete a chat request with per-provider failover (B2).

        Walks the configured chain; skips providers that are not genuinely
        available; moves to the next provider when a call fails with a
        classified error; returns the first successful result. When every
        provider fails (or is unavailable), returns a truthful aggregate
        failure — never a canned reply.

        Paid providers are never attempted unless explicitly configured in
        ``SHUNYA_AI_PROVIDERS`` (the chain is built by ``configured_chain()``).
        An explicitly injected ``self._chain`` (tests) is honored.
        """
        chain = self._chain or self._build_chain()
        errors: list[dict[str, Any]] = []

        for provider in chain:
            if not provider.is_available():
                errors.append({
                    "provider": provider.name,
                    "model": provider.model,
                    "error_class": ErrorClass.AUTH_MISSING.value,
                    "reason": "provider not available (missing key, retired model, or outage)",
                })
                continue
            try:
                result = provider.complete(
                    messages=messages, temperature=temperature, max_tokens=max_tokens,
                )
            except Exception as exc:  # providers are expected to return, not raise
                errors.append({
                    "provider": provider.name,
                    "model": provider.model,
                    "error_class": classify_exception(exc).value,
                    "reason": str(exc),
                })
                continue
            if result.get("finish_reason") == "error" or not result.get("content"):
                errors.append({
                    "provider": provider.name,
                    "model": provider.model,
                    "error_class": result.get("error_class") or ErrorClass.UNKNOWN.value,
                    "reason": result.get("error") or "empty response",
                })
                continue
            logger.info("AI completion via %s (%s) after %d attempt(s)",
                        provider.name, provider.model, len(errors) + 1)
            result["attempts"] = len(errors) + 1
            return result

        return {
            "content": "",
            "finish_reason": "error",
            "error_class": ErrorClass.PROVIDER_OUTAGE.value,
            "error": "All AI providers failed",
            "provider": "unavailable",
            "model": "none",
            "errors": errors,
            "attempts": len(chain),
            "success": False,
        }

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


def complete_with_failover(
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """Module-level failover completion (B2) — see ProviderRegistry helper."""
    return _registry.complete_with_failover(
        messages, temperature=temperature, max_tokens=max_tokens,
    )


def get_all_providers() -> list[LLMProvider]:
    """Return all configured providers regardless of availability."""
    return _registry.chain


def get_available_providers() -> list[LLMProvider]:
    """Return only providers that are available right now."""
    return _registry.all_available
