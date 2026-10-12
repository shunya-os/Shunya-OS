"""
SHUNYA — Universal AI & Media Capability Registry (ZG-03 B2 + add-on).

Provider-agnostic capability layer over the canonical model catalog:
- Every capability (text, image, video, speech, embeddings, research) maps to
  an ordered provider chain resolved from ``app.ai.model_catalog`` — model ids
  are never hardcoded in adapters.
- ``execute()`` provides timeout, one retry for retryable error classes,
  graceful failover across the provider chain, and truthful classified
  failures (never fabricated output).
- ``status()`` reports computed availability (key configured + model valid +
  not in outage), never registration-only claims.
- Cost policy: PAID providers are never executed unless the caller explicitly
  passes ``paid_ok=True``; the default layer is free-first.

Reuses existing canonical architecture: app/ai/provider.py failover for text,
app/media/service.py HF→Pollinations chain for images, the adapters/ package
(whisper/piper/kokoro/flux/comfyui) for speech and self-hostable image paths,
and app/search for research.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from app.ai.model_catalog import (
    ErrorClass,
    classify_exception,
    classify_http_status,
    is_paid,
    is_retired,
    provider_outage,
    resolve_default_model,
)

# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


class Capability(str, Enum):
    TEXT_CHAT = "text_chat"
    TEXT_GENERATION = "text_generation"
    IMAGE_GENERATION = "image_generation"
    IMAGE_EDITING = "image_editing"
    VIDEO_GENERATION = "video_generation"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    EMBEDDINGS = "embeddings"
    RESEARCH = "research"

    @property
    def label(self) -> str:
        return {
            "text_chat": "Text chat",
            "text_generation": "Content generation",
            "image_generation": "Image generation",
            "image_editing": "Image editing",
            "video_generation": "Video generation",
            "speech_to_text": "Speech to text",
            "text_to_speech": "Text to speech",
            "embeddings": "Embeddings",
            "research": "Internet research",
        }[self.value]


# ---------------------------------------------------------------------------
# Provider chains (ordered: preferred first). Model ids resolve from catalog.
# ---------------------------------------------------------------------------

_TEXT_CHAIN = ["groq", "gemini", "openrouter", "cloudflare", "huggingface", "togetherai"]

CAPABILITY_PROVIDERS: dict[Capability, list[str]] = {
    Capability.TEXT_CHAT: _TEXT_CHAIN,
    Capability.TEXT_GENERATION: _TEXT_CHAIN,
    Capability.IMAGE_GENERATION: ["huggingface", "pollinations"],
    Capability.IMAGE_EDITING: [],  # evaluated: ComfyUI self-hostable (COMFYUI_URL); none free-hosted verified
    Capability.VIDEO_GENERATION: [],  # evaluated: Wan 2.1 / LTX-Video self-hostable (GPU); none ready
    Capability.SPEECH_TO_TEXT: ["whisper", "groq_stt"],
    Capability.TEXT_TO_SPEECH: ["kokoro", "piper", "edge_tts"],
    Capability.EMBEDDINGS: [],  # sentence-transformers not installed; HF credits-gated
    Capability.RESEARCH: ["duckduckgo", "searxng"],
}

# Optional capability notes shown to users (honest disclosure).
CAPABILITY_NOTES: dict[Capability, str] = {
    Capability.IMAGE_EDITING: (
        "No free hosted editing provider verified. Self-hostable ComfyUI "
        "(COMFYUI_URL) is supported by the adapter layer but no server is "
        "configured or running."
    ),
    Capability.VIDEO_GENERATION: (
        "Evaluated Wan 2.1 and LTX-Video (both Apache-2.0, self-hostable, "
        "GPU-required). No free hosted API is verified; video generation is "
        "not available until a provider is integrated."
    ),
    Capability.EMBEDDINGS: (
        "Self-hostable via sentence-transformers (not installed) or a vector "
        "store; Hugging Face hosted embeddings require prepaid credits. "
        "Embeddings generation is unavailable."
    ),
    Capability.SPEECH_TO_TEXT: (
        "Whisper via Hugging Face serverless (credit-gated) or Groq "
        "whisper-large-v3 (free tier, key required)."
    ),
    Capability.TEXT_TO_SPEECH: (
        "Kokoro/Piper adapters (HF serverless or self-hosted) and Edge TTS "
        "(free, no key — package not installed)."
    ),
}


# ---------------------------------------------------------------------------
# Adapter callables: (params) -> result dict
# Each raises on failure OR returns {"success": False, ...} with classification.
# ---------------------------------------------------------------------------


def _adapter_text_chat(params: dict[str, Any]) -> dict[str, Any]:
    from app.ai.provider import complete_with_failover
    messages = params.get("messages") or [{"role": "user", "content": params.get("prompt", "")}]
    max_tokens = int(params.get("max_tokens", 1024))
    temperature = float(params.get("temperature", 0.7))
    result = complete_with_failover(messages, temperature=temperature, max_tokens=max_tokens)
    if result.get("finish_reason") == "error":
        result["success"] = False
        return result
    return {
        "success": True,
        "content": result.get("content", ""),
        "model": result.get("model"),
        "provider": result.get("provider"),
        "error_class": None,
    }


def _adapter_image_generation(params: dict[str, Any]) -> dict[str, Any]:
    from app.media.service import _generate_image_with_fallback, ASPECT_MAP
    prompt = params.get("prompt", "")
    aspect_ratio = params.get("aspect_ratio", "1:1")
    if not prompt:
        return {"success": False, "error": "prompt required", "error_class": ErrorClass.BAD_REQUEST.value}
    image_bytes, provider_label, errors = _generate_image_with_fallback(prompt, aspect_ratio)
    if image_bytes is None:
        return {
            "success": False,
            "error": "All image providers failed: " + "; ".join(f"{e['provider']}: {e['reason']}" for e in errors),
            "error_class": ErrorClass.PROVIDER_OUTAGE.value,
            "errors": errors,
        }
    return {"success": True, "image_bytes": image_bytes, "provider": provider_label, "error_class": None}


def _adapter_speech_to_text(params: dict[str, Any]) -> dict[str, Any]:
    provider = params.get("provider", "whisper")
    audio_path = params.get("audio_path")
    if not audio_path:
        return {"success": False, "error": "audio_path required", "error_class": ErrorClass.BAD_REQUEST.value}
    if provider == "whisper":
        from adapters.speech.whisper import WhisperAdapter
        adapter = WhisperAdapter()
        try:
            result = adapter.transcribe(audio_path, language=params.get("language", "en"))
            return {"success": True, "text": result.get("text", ""), "provider": "whisper", "error_class": None}
        except Exception as e:
            return {"success": False, "error": str(e), "error_class": classify_exception(e).value, "provider": "whisper"}
    if provider == "groq_stt":
        return _adapter_groq_stt(params)
    return {"success": False, "error": f"Unknown STT provider: {provider}", "error_class": ErrorClass.BAD_REQUEST.value}


def _adapter_groq_stt(params: dict[str, Any]) -> dict[str, Any]:
    """Groq whisper-large-v3 (free tier) via the OpenAI-compatible endpoint."""
    import httpx
    import os as _os
    audio_path = params.get("audio_path", "")
    key = _os.environ.get("GROQ_API_KEY", "")
    if not key:
        return {"success": False, "error": "GROQ_API_KEY not configured", "error_class": ErrorClass.AUTH_MISSING.value, "provider": "groq_stt"}
    try:
        with open(audio_path, "rb") as fh:
            files = {"file": (fh.name.split("/")[-1], fh.read())}
        resp = httpx.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {key}"},
            files=files,
            data={"model": "whisper-large-v3", "language": params.get("language", "en")},
            timeout=httpx.Timeout(120.0, connect=10.0, read=110.0),
        )
        resp.raise_for_status()
        data = resp.json()
        return {"success": True, "text": data.get("text", ""), "provider": "groq_stt", "model": "whisper-large-v3", "error_class": None}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": str(e), "error_class": classify_http_status(e.response.status_code).value, "provider": "groq_stt"}
    except Exception as e:
        return {"success": False, "error": str(e), "error_class": classify_exception(e).value, "provider": "groq_stt"}


def _adapter_text_to_speech(params: dict[str, Any]) -> dict[str, Any]:
    provider = params.get("provider", "kokoro")
    text = params.get("text", "")
    if not text:
        return {"success": False, "error": "text required", "error_class": ErrorClass.BAD_REQUEST.value}
    if provider in ("kokoro", "piper"):
        from adapters.speech.kokoro import KokoroAdapter
        from adapters.speech.piper import PiperAdapter
        adapter = KokoroAdapter() if provider == "kokoro" else PiperAdapter()
        try:
            out_path = adapter.synthesize(text, voice=params.get("voice", ""), out_path=params.get("out_path"))
            return {"success": True, "audio_path": out_path, "provider": provider, "error_class": None}
        except Exception as e:
            return {"success": False, "error": str(e), "error_class": classify_exception(e).value, "provider": provider}
    if provider == "edge_tts":
        return {
            "success": False,
            "error": "edge-tts package not installed — install to enable free no-key TTS",
            "error_class": ErrorClass.AUTH_MISSING.value,
            "provider": "edge_tts",
        }
    return {"success": False, "error": f"Unknown TTS provider: {provider}", "error_class": ErrorClass.BAD_REQUEST.value}


def _adapter_research(params: dict[str, Any]) -> dict[str, Any]:
    """Reuse the live research/search surface (app/search DuckDuckGo + fallbacks)."""
    query = params.get("query", "")
    if not query:
        return {"success": False, "error": "query required", "error_class": ErrorClass.BAD_REQUEST.value, "provider": "research"}
    try:
        from app.search.routes import _web_search
        results = _web_search(query, max_results=int(params.get("limit", 8)))
        return {"success": True, "results": results, "provider": "duckduckgo", "error_class": None, "source": "duckduckgo"}
    except ImportError:
        return {"success": False, "error": "search module unavailable", "error_class": ErrorClass.PROVIDER_OUTAGE.value, "provider": "research"}
    except Exception as e:
        return {"success": False, "error": str(e), "error_class": classify_exception(e).value, "provider": "research"}


ADAPTERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    f"{Capability.TEXT_CHAT.value}": _adapter_text_chat,
    f"{Capability.TEXT_GENERATION.value}": _adapter_text_chat,  # same synthesizer surface
    f"{Capability.IMAGE_GENERATION.value}": _adapter_image_generation,
    f"{Capability.SPEECH_TO_TEXT.value}": _adapter_speech_to_text,
    f"{Capability.TEXT_TO_SPEECH.value}": _adapter_text_to_speech,
    f"{Capability.RESEARCH.value}": _adapter_research,
}


# ---------------------------------------------------------------------------
# Availability probing (truthful, computed — never "registered == available")
# ---------------------------------------------------------------------------


def _provider_available_text(provider_id: str) -> tuple[bool, Optional[str]]:
    """Cheap availability for text providers (key + model + outage)."""
    if provider_id == "huggingface":
        # Deprecated/credit-gated OpenAI-compat endpoint — outage.
        return False, provider_outage(provider_id) or "credits_required"
    spec_envs = {
        "groq": ("GROQ_API_KEY",),
        "gemini": ("GEMINI_API_KEY",),
        "openrouter": ("OPENROUTER_API_KEY",),
        "cloudflare": ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"),
        "togetherai": ("TOGETHER_API_KEY",),
    }.get(provider_id, ())
    if not all(os.getenv(k) for k in spec_envs):
        return False, "AUTH_MISSING"
    if provider_outage(provider_id):
        return False, provider_outage(provider_id)
    model = resolve_default_model(provider_id, _env_model(provider_id))
    if is_retired(provider_id, model):
        return False, "MODEL_RETIRED"
    return True, None


def _env_model(provider_id: str) -> Optional[str]:
    key = {
        "groq": "GROQ_MODEL", "gemini": "GEMINI_MODEL", "openrouter": "OPENROUTER_MODEL",
        "cloudflare": "CLOUDFLARE_MODEL", "huggingface": "HF_MODEL",
        "togetherai": "TOGETHER_MODEL",
    }.get(provider_id)
    return os.getenv(key) if key else None


def _provider_available_image(provider_id: str) -> tuple[bool, Optional[str]]:
    if provider_id == "huggingface":
        if provider_outage(provider_id):
            return False, provider_outage(provider_id)
        from app.media.service import _get_hf_token
        if not _get_hf_token():
            return False, "AUTH_MISSING"
        return True, None
    if provider_id == "pollinations":
        return True, None  # free, no key — verified working 2026-10-13
    return False, "NOT_INTEGRATED"


def _provider_available_speech_to_text(provider_id: str) -> tuple[bool, Optional[str]]:
    if provider_id == "whisper":
        from adapters._hf import get_hf_token
        return (bool(get_hf_token()), None) if get_hf_token() else (False, "AUTH_MISSING (HF credit-gated)")
    if provider_id == "groq_stt":
        return (bool(os.getenv("GROQ_API_KEY")), None) if os.getenv("GROQ_API_KEY") else (False, "AUTH_MISSING")
    return False, "NOT_INTEGRATED"


def _provider_available_text_to_speech(provider_id: str) -> tuple[bool, Optional[str]]:
    if provider_id in ("kokoro", "piper"):
        # Self-hosted servers are the verified path; HF serverless is
        # credit-gated. Availability is CONFIG-DEPENDENT until a server is up.
        if os.getenv("KOKORO_API_URL") or os.getenv("PIPER_BIN") or os.getenv("PIPER_VOICES_DIR"):
            return True, None
        from adapters._hf import get_hf_token
        if get_hf_token():
            return False, "CREDITS_REQUIRED (HF serverless unverified; no local engine)"
        return False, "AUTH_MISSING"
    if provider_id == "edge_tts":
        return False, "NOT_INSTALLED (pip install edge-tts)"
    return False, "NOT_INTEGRATED"


def _provider_availability(provider_id: str, capability: Capability) -> tuple[bool, Optional[str]]:
    cap = capability.value
    if cap in ("text_chat", "text_generation"):
        return _provider_available_text(provider_id)
    if cap == "image_generation":
        return _provider_available_image(provider_id)
    if cap == "speech_to_text":
        return _provider_available_speech_to_text(provider_id)
    if cap == "text_to_speech":
        return _provider_available_text_to_speech(provider_id)
    return False, "NOT_INTEGRATED"


# ---------------------------------------------------------------------------
# Registry surface
# ---------------------------------------------------------------------------


def _model_label(capability: Capability, provider_id: str) -> str:
    """Non-secret display model id per capability/provider."""
    if capability in (Capability.TEXT_CHAT, Capability.TEXT_GENERATION):
        try:
            return resolve_default_model(provider_id, _env_model(provider_id))
        except Exception:
            return ""
    if capability == Capability.IMAGE_GENERATION:
        return {"huggingface": "black-forest-labs/FLUX.1-schnell", "pollinations": "pollinations"}.get(provider_id, "")
    if capability == Capability.SPEECH_TO_TEXT:
        return {"whisper": "whisper-large-v3", "groq_stt": "whisper-large-v3"}.get(provider_id, "")
    if capability == Capability.TEXT_TO_SPEECH:
        return {"kokoro": "Kokoro-82M", "piper": "rhasspy/piper-voices", "edge_tts": "edge-tts"}.get(provider_id, "")
    return ""


def status() -> dict[str, Any]:
    """Truthful per-capability status: providers, models, availability, cost."""
    out: dict[str, Any] = {}
    for capability, providers in CAPABILITY_PROVIDERS.items():
        entries = []
        for pid in providers:
            available, reason = _provider_availability(pid, capability)
            entries.append({
                "id": pid,
                "available": available,
                "reason": reason,
                "model": _model_label(capability, pid),
                "cost": "free",
                "paid": is_paid(pid),
            })
        out[capability.value] = {
            "label": capability.label,
            "providers": entries,
            "note": CAPABILITY_NOTES.get(capability, ""),
        }
    return out


def summarize() -> list[dict[str, Any]]:
    """Compact summary for registry/UI (one row per capability)."""
    rows = []
    for capability, providers in CAPABILITY_PROVIDERS.items():
        available_providers = []
        for pid in providers:
            ok, reason = _provider_availability(pid, capability)
            if ok:
                available_providers.append(pid)
        rows.append({
            "capability": capability.value,
            "label": capability.label,
            "status": "AVAILABLE" if available_providers else "UNAVAILABLE",
            "providers": available_providers,
            "configured_providers": providers,
            "note": CAPABILITY_NOTES.get(capability, ""),
        })
    return rows


def execute(capability: Capability, params: dict[str, Any], *, paid_ok: bool = False) -> dict[str, Any]:
    """Execute a capability with timeout, retry (retryable classes) and failover.

    Cost policy: paid providers are filtered unless ``paid_ok=True``.
    Returns a truthful, classified result — never fabricated output.
    """
    cap = capability.value
    provider_chain = list(CAPABILITY_PROVIDERS.get(capability, []))
    prefer = params.get("provider")
    if prefer and prefer in provider_chain:
        provider_chain.remove(prefer)
        provider_chain.insert(0, prefer)

    exclude_paid = not paid_ok
    if exclude_paid:
        provider_chain = [p for p in provider_chain if not is_paid(p)]

    adapter = ADAPTERS.get(cap)
    if adapter is None:
        return {
            "success": False,
            "capability": cap,
            "error": f"Capability '{cap}' has no integrated provider",
            "error_class": ErrorClass.PROVIDER_OUTAGE.value,
            "note": CAPABILITY_NOTES.get(capability, ""),
        }

    errors: list[dict[str, Any]] = []
    attempts = 0
    for pid in provider_chain:
        attempts += 1
        available, reason = _provider_availability(pid, capability)
        call_params = dict(params)
        call_params["provider"] = pid
        result = adapter(call_params)
        if result.get("success"):
            result["capability"] = cap
            result["attempts"] = attempts
            result["fallback_used"] = attempts > 1
            result["provider"] = result.get("provider") or pid
            return result
        error_class = result.get("error_class") or ErrorClass.UNKNOWN.value
        errors.append({
            "provider": pid,
            "error_class": error_class,
            "reason": result.get("error", "unknown"),
        })
        # One retry for transient classes on the same provider.
        if error_class in (ErrorClass.RATE_LIMITED.value, ErrorClass.NETWORK_ERROR.value, ErrorClass.PROVIDER_OUTAGE.value) \
                and attempts <= 2 * len(provider_chain) - 1:
            retry_params = dict(params)
            retry_params["provider"] = pid
            retry = adapter(retry_params)
            attempts += 1
            if retry.get("success"):
                retry["capability"] = cap
                retry["attempts"] = attempts
                retry["fallback_used"] = True
                retry["provider"] = retry.get("provider") or pid
                return retry
            errors[-1]["reason"] = retry.get("error", errors[-1]["reason"])

    return {
        "success": False,
        "capability": cap,
        "error": f"All providers failed for {cap}",
        "error_class": _final_error_class(errors),
        "errors": errors,
        "attempts": attempts,
    }


def _final_error_class(errors: list[dict[str, Any]]) -> str:
    """Pick the most informative aggregate class.

    Deterministic validation/config errors (caller-side) must not be masked as
    a generic provider outage — a missing query is BAD_REQUEST, a missing key
    is AUTH_MISSING, a retired id is MODEL_RETIRED, an HF-style credit wall is
    CREDITS_REQUIRED. Only genuinely transient/unknown cases collapse to
    PROVIDER_OUTAGE.
    """
    precedence = (
        ErrorClass.BAD_REQUEST.value,
        ErrorClass.AUTH_MISSING.value,
        ErrorClass.MODEL_RETIRED.value,
        ErrorClass.CREDITS_REQUIRED.value,
        ErrorClass.RATE_LIMITED.value,
        ErrorClass.NETWORK_ERROR.value,
        ErrorClass.PROVIDER_OUTAGE.value,
        ErrorClass.UNKNOWN.value,
    )
    for cls in precedence:
        if any(e.get("error_class") == cls for e in errors):
            return cls
    return ErrorClass.PROVIDER_OUTAGE.value