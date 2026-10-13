"""
SHUNYA — Canonical Provider & Model Catalog (ZG-03 B2).

Single source of truth for every advertised AI provider and model identifier.
Provider classes, the image-provider registry, orchestration defaults and
documentation all read from this catalog so a retired model or a dead provider
is never advertised as available.

Rules enforced here (constitutional):
- A provider is AVAILABLE only when its required env vars are configured AND
  its effective model id is not retired AND the provider is not in a known
  outage state. Registration is not availability.
- Paid providers (OpenAI, Anthropic) are never part of the default free chain;
  they may only be used when explicitly listed in SHUNYA_AI_PROVIDERS.
- Local deterministic replies are test/offline-only and must never be the
  automatic fallback when real providers fail (canned replies as "success" are
  fake activity — constitution "never invent an answer on the failure path").
- No advertised model id may be retired ("retired" verified against live
  provider catalogs on 2026-10-13; see docs/launch/ZG03_B2_PROVIDER_TRUTH.md).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Error classification (truthful failure taxonomy)
# ---------------------------------------------------------------------------

class ErrorClass(str, Enum):
    """Machine-readable classification of a provider failure."""

    MODEL_RETIRED = "MODEL_RETIRED"          # model id no longer served
    AUTH_MISSING = "AUTH_MISSING"            # required key not configured
    AUTH_REJECTED = "AUTH_REJECTED"          # 401/403 — key invalid/revoked
    CREDITS_REQUIRED = "CREDITS_REQUIRED"    # 402 — payment/prepaid credits needed
    RATE_LIMITED = "RATE_LIMITED"            # 429
    NETWORK_ERROR = "NETWORK_ERROR"          # connection/timeout/DNS
    PROVIDER_OUTAGE = "PROVIDER_OUTAGE"      # 5xx or provider-side failure
    BAD_REQUEST = "BAD_REQUEST"              # 400/422 — malformed request
    UNKNOWN = "UNKNOWN"

    @property
    def retryable(self) -> bool:
        return self in (
            ErrorClass.RATE_LIMITED,
            ErrorClass.NETWORK_ERROR,
            ErrorClass.PROVIDER_OUTAGE,
            ErrorClass.UNKNOWN,
        )


def classify_http_status(status: int, *, model: str = "", retired_models: tuple[str, ...] = ()) -> ErrorClass:
    """Map an HTTP status + model context to an ErrorClass."""
    if status == 401 or status == 403:
        return ErrorClass.AUTH_REJECTED
    if status == 402:
        return ErrorClass.CREDITS_REQUIRED
    if status == 429:
        return ErrorClass.RATE_LIMITED
    if status == 404:
        return ErrorClass.MODEL_RETIRED if not retired_models or model in retired_models else ErrorClass.BAD_REQUEST
    if status in (400, 422):
        return ErrorClass.BAD_REQUEST
    if 500 <= status <= 599:
        return ErrorClass.PROVIDER_OUTAGE
    return ErrorClass.UNKNOWN


def classify_exception(exc: BaseException) -> ErrorClass:
    """Classify a transport-level exception (httpx/requests/HF client).

    Works across all HTTP clients: if the exception carries a ``response``
    object with a ``status_code`` (httpx.HTTPStatusError, requests.HTTPError
    subclasses like huggingface_hub's HfHubHTTPError), classify by status.
    Otherwise fall back to message fingerprints and connection-error names.
    """
    name = type(exc).__name__
    if name in ("ConnectError", "ConnectTimeout", "ReadTimeout", "Timeout",
                "RemoteProtocolError", "ConnectionError", "TimeoutError"):
        return ErrorClass.NETWORK_ERROR

    # Generic status-carrying exceptions (any HTTP client).
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int):
        return classify_http_status(status_code)

    msg = str(exc)
    if "402" in msg and ("Payment Required" in msg or "credits" in msg.lower()):
        return ErrorClass.CREDITS_REQUIRED
    if "429" in msg:
        return ErrorClass.RATE_LIMITED
    if "404" in msg:
        return ErrorClass.BAD_REQUEST
    return ErrorClass.UNKNOWN


# ---------------------------------------------------------------------------
# Provider specifications
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProviderSpec:
    id: str
    label: str
    category: str                              # "text" | "image"
    api_key_envs: tuple[str, ...]              # env vars required to be usable
    optional_envs: tuple[str, ...] = ()        # env vars read but not required
    base_url: str = ""
    default_model: str = ""
    valid_models: tuple[str, ...] = ()
    retired_models: tuple[str, ...] = ()
    deprecated_models: tuple[str, ...] = ()    # still listed but legacy; not advertised
    free: bool = True
    paid: bool = False
    outage: Optional[str] = None               # e.g. "credits_required"
    test_only: bool = False                    # dummy provider
    chain_eligible: bool = True                # may appear in the default chain
    default_chain_eligible: bool = True        # appears in DEFAULT_TEXT_CHAIN
    supports_vision: bool = False
    note: str = ""


def _spec(pid: str) -> Optional[ProviderSpec]:
    return PROVIDERS.get(pid)


# ---------------------------------------------------------------------------
# The catalog
# ---------------------------------------------------------------------------

PROVIDERS: dict[str, ProviderSpec] = {
    "groq": ProviderSpec(
        id="groq",
        label="Groq AI",
        category="text",
        api_key_envs=("GROQ_API_KEY",),
        base_url="https://api.groq.com/openai/v1",
        default_model="openai/gpt-oss-20b",
        valid_models=(
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "qwen/qwen3.8-27b",
            "allam-2-7b",
        ),
        retired_models=(
            "llama-3.3-70b-versatile",
            "llama-3.3-70b-specdec",
            "llama-3.1-8b-instant",
            "llama-3.2-3b-preview",
            "mixtral-8x7b-32768",
            "llama2-70b-4096",
            "gemma2-9b-it",
        ),
        free=True,
        note="Verified live 2026-10-13: llama-3.3-70b-versatile absent from /models (retired).",
    ),
    "gemini": ProviderSpec(
        id="gemini",
        label="Google Gemini",
        category="text",
        api_key_envs=("GEMINI_API_KEY",),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        default_model="gemini-2.5-flash",
        valid_models=("gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"),
        retired_models=("gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-pro"),
        free=True,
        note="Verified live 2026-10-13: only 2.5.x present in models list.",
    ),
    "openrouter": ProviderSpec(
        id="openrouter",
        label="OpenRouter",
        category="text",
        api_key_envs=("OPENROUTER_API_KEY",),
        base_url="https://openrouter.ai/api/v1",
        default_model="deepseek/deepseek-chat",
        valid_models=(
            "deepseek/deepseek-chat",
            "deepseek/deepseek-r1",
            "deepseek/deepseek-v3.2",
            "qwen/qwen-2.5-72b-instruct",
            "meta-llama/llama-3.3-70b-instruct",
            "mistralai/mistral-small-3.1-24b-instruct",
        ),
        retired_models=(),
        deprecated_models=("openai/gpt-4o", "openai/gpt-4o-mini", "openai/gpt-4-turbo", "openai/gpt-3.5-turbo"),
        free=True,
        note="deepseek/deepseek-chat present in live catalog. gpt-4o era removed from default advertising (OpenAI retired 2025-09-29).",
    ),
    "cloudflare": ProviderSpec(
        id="cloudflare",
        label="Cloudflare Workers AI",
        category="text",
        api_key_envs=("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"),
        base_url="https://api.cloudflare.com/client/v4",
        default_model="@cf/meta/llama-3.1-8b-instruct-fp8",
        valid_models=(
            "@cf/meta/llama-3.1-8b-instruct-fp8",
            "@cf/meta/llama-3.2-3b-instruct",
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
            "@cf/meta/llama-3.2-1b-instruct",
            "@cf/meta/llama-4-scout-17b-16e-instruct",
            "@cf/mistralai/mistral-small-3.1-24b-instruct",
        ),
        retired_models=("@cf/meta/llama-3.1-8b-instruct",),
        free=True,
        note="Verified live 2026-10-13: plain llama-3.1-8b-instruct absent; -fp8 variant present.",
    ),
    "huggingface": ProviderSpec(
        id="huggingface",
        label="Hugging Face",
        category="text",
        api_key_envs=("HF_API_KEY", "HF_TOKEN"),
        base_url="https://router.huggingface.co/v1",
        default_model="meta-llama/Llama-3.2-3B-Instruct",
        valid_models=("meta-llama/Llama-3.2-3B-Instruct", "microsoft/Phi-3.5-mini-instruct"),
        retired_models=(),
        free=True,
        outage="credits_required",
        note="Old api-inference.huggingface.co/v1 OpenAI-compatible endpoint deprecated; HF now routes via router.huggingface.co and requires prepaid credits (402 reproduced 2026-10-13).",
    ),
    "togetherai": ProviderSpec(
        id="togetherai",
        label="Together AI",
        category="text",
        api_key_envs=("TOGETHER_API_KEY",),
        base_url="https://api.together.xyz/v1",
        default_model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        valid_models=(
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "meta-llama/Llama-3.3-70B-Instruct",
            "meta-llama/Llama-3.1-8B-Instruct-Turbo",
        ),
        retired_models=(),
        free=True,
        note="Verified live 2026-10-13: Llama-3.3-70B-Instruct-Turbo present in /models.",
    ),
    "anthropic": ProviderSpec(
        id="anthropic",
        label="Anthropic Claude",
        category="text",
        api_key_envs=("ANTHROPIC_API_KEY",),
        base_url="https://api.anthropic.com/v1",
        default_model="claude-sonnet-4-5-20250929",
        valid_models=(
            "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
            "claude-opus-4-5-20251101",
        ),
        retired_models=("claude-3-haiku-20240307", "claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022"),
        free=False,
        paid=True,
        default_chain_eligible=False,
        note="PAID — excluded from default chain; explicit SHUNYA_AI_PROVIDERS entry required.",
    ),
    "openai": ProviderSpec(
        id="openai",
        label="OpenAI",
        category="text",
        api_key_envs=("OPENAI_API_KEY",),
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        valid_models=("gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"),
        retired_models=("gpt-4o", "gpt-4-turbo", "text-davinci-003", "gpt-3.5-turbo"),
        free=False,
        paid=True,
        default_chain_eligible=False,
        note="PAID — excluded from default chain; explicit SHUNYA_AI_PROVIDERS entry required.",
    ),
    "local": ProviderSpec(
        id="local",
        label="Local (deterministic)",
        category="text",
        api_key_envs=(),
        base_url="",
        default_model="local",
        valid_models=("local",),
        retired_models=(),
        free=True,
        chain_eligible=True,
        default_chain_eligible=False,
        note="Deterministic replies — test/offline only. Never the automatic fallback; canned replies as success are forbidden on the failure path.",
    ),
    # ── Image providers ──────────────────────────────────────────────────
    "huggingface_image": ProviderSpec(
        id="huggingface",
        label="Hugging Face FLUX",
        category="image",
        api_key_envs=("HF_API_KEY", "HF_TOKEN"),
        base_url="",
        default_model="black-forest-labs/FLUX.1-schnell",
        valid_models=("black-forest-labs/FLUX.1-schnell",),
        retired_models=(),
        free=True,
        outage="credits_required",
        note="402 reproduced 2026-10-13 — free serverless image inference requires prepaid credits.",
    ),
    "pollinations": ProviderSpec(
        id="pollinations",
        label="Pollinations",
        category="image",
        api_key_envs=(),
        base_url="https://image.pollinations.ai",
        default_model="pollinations",
        valid_models=("pollinations",),
        retired_models=(),
        free=True,
        note="Free, no key. Verified 2026-10-13 returning a real JPEG (256x256 probe).",
    ),
    "dummy": ProviderSpec(
        id="dummy",
        label="Dummy (placeholder)",
        category="image",
        api_key_envs=(),
        base_url="",
        default_model="dummy-rgb",
        valid_models=("dummy-rgb",),
        retired_models=(),
        free=True,
        test_only=True,
        chain_eligible=False,
        default_chain_eligible=False,
        note="Solid-color PNG for tests only — never advertised in production.",
    ),
}

# Default (free-first) text chain, in resolve order. Paid providers and local
# are NOT auto-members; they join only when SHUNYA_AI_PROVIDERS lists them.
DEFAULT_TEXT_CHAIN = ["groq", "gemini", "openrouter", "cloudflare", "huggingface", "togetherai"]

# Default image chain (tried in order by media generation).
DEFAULT_IMAGE_CHAIN = ["huggingface", "pollinations"]

PAID_PROVIDER_IDS = {"openai", "anthropic"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_default_model(provider_id: str, env_value: Optional[str]) -> str:
    """Pick the effective model for a provider.

    An env override is honored only while it is still valid (not retired and
    not deprecated); otherwise the catalog default is used. This is the B2
    rule: a retired identifier in .env must not silently steer traffic.
    """
    spec = PROVIDERS.get(provider_id)
    if spec is None:
        return env_value or ""
    if env_value:
        if env_value in spec.valid_models or env_value == spec.default_model:
            return env_value
    return spec.default_model


def is_retired(provider_id: str, model: str) -> bool:
    spec = PROVIDERS.get(provider_id)
    if spec is None:
        return False
    return model in spec.retired_models


def is_deprecated(provider_id: str, model: str) -> bool:
    spec = PROVIDERS.get(provider_id)
    if spec is None:
        return False
    return model in spec.deprecated_models


def is_paid(provider_id: str) -> bool:
    spec = PROVIDERS.get(provider_id)
    return bool(spec and spec.paid)


def configured_chain() -> list[str]:
    """Return the effective text provider chain.

    SHUNYA_AI_PROVIDERS (comma-separated) overrides the default; every id must
    exist in the catalog. Paid/local providers are honored when explicitly
    configured; unknown ids are ignored (never silently invented).
    """
    raw = os.getenv("SHUNYA_AI_PROVIDERS", "").strip()
    if raw:
        ids = [p.strip() for p in raw.split(",") if p.strip()]
        return [pid for pid in ids if pid in PROVIDERS and PROVIDERS[pid].category == "text"]
    return list(DEFAULT_TEXT_CHAIN)


def provider_outage(provider_id: str) -> Optional[str]:
    spec = PROVIDERS.get(provider_id)
    return spec.outage if spec else None


def is_test_only(provider_id: str) -> bool:
    spec = PROVIDERS.get(provider_id)
    return bool(spec and spec.test_only)


def describe_config(provider_id: str) -> dict[str, Any]:
    """Public, credential-free description of a provider (for listings/docs)."""
    spec = PROVIDERS.get(provider_id)
    if spec is None:
        return {"id": provider_id, "found": False}
    return {
        "id": spec.id,
        "label": spec.label,
        "category": spec.category,
        "free": spec.free,
        "paid": spec.paid,
        "default_model": spec.default_model,
        "valid_models": list(spec.valid_models),
        "retired_models": list(spec.retired_models),
        "outage": spec.outage,
        "test_only": spec.test_only,
        "chain_eligible": spec.chain_eligible,
        "default_chain_eligible": spec.default_chain_eligible,
        "note": spec.note,
    }
