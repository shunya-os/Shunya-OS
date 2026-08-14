"""Inference Execution Layer — provider-specific API call formatting and dispatch.

Translate abstract inference requests into provider-native payloads
(OpenAI-compatible, Anthropic, Local) and handle response normalization.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

logger = logging.getLogger(__name__)


# ── Data Types ─────────────────────────────────────────────────────────────


@dataclass
class InferenceMessage:
    """A single message in an inference conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


@dataclass
class InferenceRequest:
    """Standardised inference request consumed by the execution layer.

    All providers normalise *to* this shape; the execution layer
    normalises *from* this shape to the provider-native wire format.
    """
    messages: list[InferenceMessage]
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    stop: list[str] | None = None
    stream: bool = False
    provider_hint: str = ""           # "openai" | "anthropic" | "local" | "auto"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "messages": [{"role": m.role, "content": m.content} for m in self.messages],
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stop": self.stop,
            "stream": self.stream,
            "provider_hint": self.provider_hint,
        }


@dataclass
class InferenceResult:
    """Normalised result returned by every provider."""
    content: str
    model: str
    finish_reason: str = "stop"
    usage: dict = field(default_factory=dict)
    provider: str = ""
    latency_ms: float = 0.0
    error: str | None = None
    raw: dict | None = None

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "model": self.model,
            "finish_reason": self.finish_reason,
            "usage": self.usage,
            "provider": self.provider,
            "latency_ms": round(self.latency_ms, 1),
            "error": self.error,
        }

    @property
    def success(self) -> bool:
        return self.error is None and self.finish_reason != "error"


# ── Provider-specific formatters ────────────────────────────────────────────


def format_openai_payload(request: InferenceRequest) -> dict:
    """Format an InferenceRequest into an OpenAI-compatible /chat/completions body."""
    messages = []
    for m in request.messages:
        entry: dict[str, Any] = {"role": m.role, "content": m.content}
        if m.name:
            entry["name"] = m.name
        if m.tool_calls:
            entry["tool_calls"] = m.tool_calls
        if m.tool_call_id:
            entry["tool_call_id"] = m.tool_call_id
        messages.append(entry)

    body: dict[str, Any] = {
        "model": request.model,
        "messages": messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "top_p": request.top_p,
    }
    if request.stop:
        body["stop"] = request.stop
    if request.stream:
        body["stream"] = True
    body.update(request.extra)
    return body


def format_anthropic_payload(request: InferenceRequest) -> dict:
    """Format an InferenceRequest into Anthropic /v1/messages body."""
    system_msg = ""
    anthropic_messages: list[dict] = []
    for m in request.messages:
        if m.role == "system":
            system_msg = m.content
        elif m.role in ("user", "assistant"):
            anthropic_messages.append({"role": m.role, "content": m.content})
        # tool messages are skipped in basic Anthropic format

    body: dict[str, Any] = {
        "model": request.model,
        "max_tokens": request.max_tokens,
        "messages": anthropic_messages,
    }
    if system_msg:
        body["system"] = system_msg
    if request.temperature != 0.7:
        body["temperature"] = request.temperature
    if request.stop:
        body["stop_sequences"] = request.stop
    body.update(request.extra)
    return body


def format_local_payload(request: InferenceRequest) -> dict:
    """Format an InferenceRequest for local/deterministic execution.

    Returns a dict that the local executor can consume directly.
    """
    return {
        "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }


# ── Provider-specific response parsers ──────────────────────────────────────


def parse_openai_response(data: dict, model: str, latency_ms: float) -> InferenceResult:
    """Parse an OpenAI /chat/completions response into InferenceResult."""
    try:
        choice = data["choices"][0]
        return InferenceResult(
            content=choice["message"].get("content", ""),
            model=data.get("model", model),
            finish_reason=choice.get("finish_reason", "stop"),
            usage=data.get("usage", {}),
            provider="openai",
            latency_ms=latency_ms,
            raw=data,
        )
    except (KeyError, IndexError) as e:
        return InferenceResult(
            content="", model=model, finish_reason="error",
            provider="openai", latency_ms=latency_ms,
            error=f"Failed to parse OpenAI response: {e}",
            raw=data,
        )


def parse_anthropic_response(data: dict, model: str, latency_ms: float) -> InferenceResult:
    """Parse an Anthropic /v1/messages response into InferenceResult."""
    try:
        content_blocks = data.get("content", [])
        text = "".join(
            block.get("text", "") for block in content_blocks if block.get("type") == "text"
        )
        usage = {
            "input_tokens": data.get("usage", {}).get("input_tokens", 0),
            "output_tokens": data.get("usage", {}).get("output_tokens", 0),
        }
        return InferenceResult(
            content=text,
            model=data.get("model", model),
            finish_reason=data.get("stop_reason", "stop"),
            usage=usage,
            provider="anthropic",
            latency_ms=latency_ms,
            raw=data,
        )
    except Exception as e:
        return InferenceResult(
            content="", model=model, finish_reason="error",
            provider="anthropic", latency_ms=latency_ms,
            error=f"Failed to parse Anthropic response: {e}",
            raw=data,
        )


def parse_local_response(data: dict, model: str, latency_ms: float) -> InferenceResult:
    """Parse a local executor response into InferenceResult."""
    return InferenceResult(
        content=data.get("content", ""),
        model=model,
        finish_reason=data.get("finish_reason", "stop"),
        usage={"input_tokens": 0, "output_tokens": 0},
        provider="local",
        latency_ms=latency_ms,
        raw=data,
    )


# ── Provider configuration ──────────────────────────────────────────────────


@dataclass
class ProviderConfig:
    """Configuration for a single inference provider."""
    name: str                                          # "openai", "anthropic", "local"
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    priority: int = 10
    max_retries: int = 2
    timeout_seconds: int = 60


def resolve_provider_configs() -> list[ProviderConfig]:
    """Build the provider chain from environment variables.

    Priority order (by priority field, lower = higher priority):
      1. Groq (priority 10, free tier)
      2. OpenRouter (priority 20)
      3. OpenAI (priority 30)
      4. Anthropic (priority 40)
      5. Local (priority 100, always available)
    """
    configs: list[ProviderConfig] = []

    # Groq (free tier, highest priority)
    if os.getenv("GROQ_API_KEY"):
        configs.append(ProviderConfig(
            name="groq",
            api_key=os.getenv("GROQ_API_KEY", ""),
            base_url="https://api.groq.com/openai/v1",
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            priority=10,
        ))

    # OpenRouter
    if os.getenv("OPENROUTER_API_KEY"):
        configs.append(ProviderConfig(
            name="openrouter",
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            priority=20,
        ))

    # OpenAI
    if os.getenv("OPENAI_API_KEY"):
        configs.append(ProviderConfig(
            name="openai",
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            priority=30,
        ))

    # Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        configs.append(ProviderConfig(
            name="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
            priority=40,
        ))

    # Local fallback (always available)
    configs.append(ProviderConfig(
        name="local",
        model="local",
        priority=100,
    ))

    configs.sort(key=lambda c: c.priority)
    return configs


# ── Execution Layer ─────────────────────────────────────────────────────────


class ExecutionLayer:
    """Provider-agnostic execution layer for inference requests.

    Handles provider-specific formatting, dispatch, response parsing,
    and automatic failover across the configured provider chain.
    """

    def __init__(self, provider_configs: list[ProviderConfig] | None = None):
        self._configs = provider_configs or resolve_provider_configs()
        self._current_index = 0

    # ── Public API ──────────────────────────────────────────────────────

    def execute_request(self, request: InferenceRequest) -> InferenceResult:
        """Execute an inference request, selecting the best provider.

        Uses the provider hint if set, otherwise walks the configured chain.
        """
        import time

        if request.provider_hint:
            return self._execute_with_hint(request)

        start = time.monotonic()
        for idx, config in enumerate(self._configs):
            self._current_index = idx
            try:
                result = self._execute_single(request, config)
                result.latency_ms = (time.monotonic() - start) * 1000
                if result.success:
                    return result
                logger.warning(
                    "Provider %s returned error: %s", config.name, result.error
                )
            except Exception as e:
                logger.warning("Provider %s raised exception: %s", config.name, e)
                if idx == len(self._configs) - 1:
                    return InferenceResult(
                        content="", model=config.model,
                        finish_reason="error", provider=config.name,
                        latency_ms=(time.monotonic() - start) * 1000,
                        error=str(e),
                    )

        return InferenceResult(
            content="", model="", finish_reason="error",
            provider="none", latency_ms=(time.monotonic() - start) * 1000,
            error="No provider available",
        )

    def execute_with_provider(
        self, request: InferenceRequest, provider_name: str
    ) -> InferenceResult:
        """Execute with a specific provider by name."""
        import time
        for config in self._configs:
            if config.name == provider_name:
                start = time.monotonic()
                result = self._execute_single(request, config)
                result.latency_ms = (time.monotonic() - start) * 1000
                return result
        return InferenceResult(
            content="", model="", finish_reason="error",
            provider=provider_name, error=f"Provider '{provider_name}' not configured",
        )

    def get_available_providers(self) -> list[dict]:
        """Return metadata about all configured providers."""
        return [
            {
                "name": c.name,
                "model": c.model,
                "priority": c.priority,
                "base_url": c.base_url or "N/A",
            }
            for c in self._configs
        ]

    def reset(self) -> None:
        """Reset provider chain (for testing)."""
        self._configs = resolve_provider_configs()
        self._current_index = 0

    # ── Internal ────────────────────────────────────────────────────────

    def _execute_with_hint(self, request: InferenceRequest) -> InferenceResult:
        """Try the hinted provider first, then fall back."""
        import time
        start = time.monotonic()

        # Try hinted provider first
        for config in self._configs:
            if config.name == request.provider_hint:
                result = self._execute_single(request, config)
                result.latency_ms = (time.monotonic() - start) * 1000
                if result.success:
                    return result
                break

        # Fall through to chain
        for config in self._configs:
            try:
                result = self._execute_single(request, config)
                result.latency_ms = (time.monotonic() - start) * 1000
                if result.success:
                    return result
            except Exception:
                continue

        return InferenceResult(
            content="", model="", finish_reason="error",
            provider="none", latency_ms=(time.monotonic() - start) * 1000,
            error="No provider succeeded",
        )

    def _execute_single(
        self, request: InferenceRequest, config: ProviderConfig
    ) -> InferenceResult:
        """Execute against a single provider configuration."""
        import time

        if config.name == "local":
            return self._execute_local(request, config)

        if config.name == "anthropic":
            return self._execute_anthropic(request, config)

        # Default: OpenAI-compatible (OpenAI, OpenRouter, Groq, etc.)
        return self._execute_openai(request, config)

    # ── Provider-specific dispatch ──────────────────────────────────────

    def _execute_openai(
        self, request: InferenceRequest, config: ProviderConfig
    ) -> InferenceResult:
        """Execute via OpenAI-compatible /chat/completions endpoint."""
        import httpx
        import time

        payload = format_openai_payload(request)
        payload["model"] = config.model

        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{config.base_url.rstrip('/')}/chat/completions"
        start = time.monotonic()

        try:
            with httpx.Client(timeout=config.timeout_seconds) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
            latency = (time.monotonic() - start) * 1000
            result = parse_openai_response(data, config.model, latency)
            result.provider = config.name
            return result
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            return InferenceResult(
                content="", model=config.model, finish_reason="error",
                provider=config.name, latency_ms=latency, error=str(e),
            )

    def _execute_anthropic(
        self, request: InferenceRequest, config: ProviderConfig
    ) -> InferenceResult:
        """Execute via Anthropic /v1/messages endpoint."""
        import httpx
        import time

        payload = format_anthropic_payload(request)
        payload["model"] = config.model

        headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        url = "https://api.anthropic.com/v1/messages"
        start = time.monotonic()

        try:
            with httpx.Client(timeout=config.timeout_seconds) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
            latency = (time.monotonic() - start) * 1000
            result = parse_anthropic_response(data, config.model, latency)
            result.provider = config.name
            return result
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            return InferenceResult(
                content="", model=config.model, finish_reason="error",
                provider=config.name, latency_ms=latency, error=str(e),
            )

    def _execute_local(
        self, request: InferenceRequest, config: ProviderConfig
    ) -> InferenceResult:
        """Execute locally — deterministic template-based responses."""
        import time
        start = time.monotonic()

        last_user = ""
        for m in request.messages:
            if m.role == "user":
                last_user = m.content

        # Build contextual response
        words = set(last_user.lower().split())
        response_parts = []

        if words & {"hello", "hi", "hey", "greetings"}:
            response_parts.append("Hello! I'm SHUNYA, your AI operating system.")
            response_parts.append("I can help you understand your business objects, answer questions about your data, and assist with tasks.")
            response_parts.append("What would you like to explore?")
        elif words & {"help", "capabilities"} or "what can you" in last_user.lower():
            response_parts.append("I can help you with:")
            response_parts.append("- Answer questions about your business objects and relationships")
            response_parts.append("- Generate summaries of any object or conversation")
            response_parts.append("- Create and update objects from our conversation")
            response_parts.append("- Navigate between related business entities")
            response_parts.append("- Identify next actions and missing context")
            response_parts.append("What would you like me to do?")
        elif any(word in last_user.lower() for word in ["summarize", "summary", "summarise"]):
            response_parts.append("I'll generate a summary based on the available information.")
            response_parts.append("The current context includes the object's name, type, content, and conversation history.")
            response_parts.append("For a more detailed summary, please specify what aspect you'd like me to focus on.")
        elif words & {"create", "new"} or last_user.lower().startswith("make"):
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
        latency = (time.monotonic() - start) * 1000

        return InferenceResult(
            content=content,
            model=config.model,
            finish_reason="stop",
            usage={"input_tokens": 0, "output_tokens": 0},
            provider="local",
            latency_ms=latency,
        )