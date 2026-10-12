"""ZG-03 B2 — Provider catalog, availability, failover, and capability tests.

Monkeypatches network/production state so tests pass in CI without keys.
"""
import os
import pytest

# ── Shared helpers ─────────────────────────────────────────────────────


def _ensure_env(monkeypatch, **kwargs):
    for k, v in kwargs.items():
        monkeypatch.setenv(k, v)


# ── 1. Catalog invariants ─────────────────────────────────────────────


class TestCatalogNoRetiredDefaults:
    """Every advertised default model must be a current valid id."""

    def test_groq_default_not_retired(self):
        from app.ai.model_catalog import resolve_default_model
        model = resolve_default_model("groq", None)
        assert model not in ("llama-3.3-70b-versatile", "llama-3.3-70b-specdec")
        assert model == "openai/gpt-oss-20b"

    def test_gemini_default_not_retired(self):
        from app.ai.model_catalog import resolve_default_model
        model = resolve_default_model("gemini", None)
        assert model not in ("gemini-2.0-flash",)
        assert model.startswith("gemini-2.5")

    def test_cloudflare_default_not_retired(self):
        from app.ai.model_catalog import resolve_default_model
        model = resolve_default_model("cloudflare", None)
        assert model not in ("@cf/meta/llama-3.1-8b-instruct",)

    def test_anthropic_default_not_retired(self):
        from app.ai.model_catalog import resolve_default_model
        model = resolve_default_model("anthropic", None)
        assert model not in ("claude-3-haiku-20240307",)

    def test_openrouter_default_valid(self):
        from app.ai.model_catalog import resolve_default_model
        model = resolve_default_model("openrouter", None)
        assert model in ("deepseek/deepseek-chat",)

    def test_retired_env_falls_back(self, monkeypatch):
        """An env variable set to a retired model id must not be used."""
        _ensure_env(monkeypatch, GROQ_MODEL="llama-3.3-70b-versatile")
        from app.ai.model_catalog import resolve_default_model
        model = resolve_default_model("groq", os.getenv("GROQ_MODEL"))
        assert model not in ("llama-3.3-70b-versatile",)


# ── 2. Availability truthfulness ───────────────────────────────────────


class TestAvailability:
    """is_available() must be true only when key + valid model + no outage."""

    def test_groq_available_with_key(self, monkeypatch):
        _ensure_env(monkeypatch, GROQ_API_KEY="test-key")
        from app.ai.provider import GroqProvider
        p = GroqProvider()
        assert p.is_available() is True

    def test_groq_unavailable_no_key(self):
        from app.ai.provider import GroqProvider
        p = GroqProvider(api_key="")
        assert p.is_available() is False

    def test_groq_key_but_retired_env_is_ok(self, monkeypatch):
        """Retired env reverts to catalog default → still available."""
        _ensure_env(monkeypatch, GROQ_API_KEY="test-key", GROQ_MODEL="llama-3.3-70b-versatile")
        from app.ai.provider import GroqProvider
        p = GroqProvider()
        assert p.is_available() is True  # model falls back to gpt-oss-20b

    def test_huggingface_image_outage(self, monkeypatch):
        _ensure_env(monkeypatch, HF_API_KEY="test-key")
        from app.ai.model_catalog import provider_outage
        assert provider_outage("huggingface_image") is not None
        from app.content_studio.image_providers import ProviderRegistry, init_providers
        reg = ProviderRegistry()
        reg = init_providers()
        tiers = reg.get_available_tiers()
        hf_entry = None
        for t in tiers:
            for p in t["providers"]:
                if p["name"] == "huggingface":
                    hf_entry = p
        assert hf_entry is not None
        assert hf_entry["available"] is False, "huggingface image should be unavailable due to outage"

    def test_pollinations_available_in_tiers(self):
        from app.content_studio.image_providers import ProviderRegistry, init_providers
        reg = ProviderRegistry()
        reg = init_providers()
        tiers = reg.get_available_tiers()
        poll = None
        for t in tiers:
            for p in t["providers"]:
                if p["name"] == "pollinations":
                    poll = p
        assert poll is not None, "pollinations must be registered"
        assert poll["available"] is True

    def test_no_dummy_in_production_tiers(self, monkeypatch):
        _ensure_env(monkeypatch, SHUNYA_ENVIRONMENT="production")
        from app.content_studio.image_providers import reset_registry, init_providers, get_registry
        reset_registry()
        reg = init_providers()
        tiers = reg.get_available_tiers()
        for t in tiers:
            for p in t["providers"]:
                assert p["name"] != "dummy", "dummy must not appear in production"


# ── 3. Failover + UnavailableProvider ──────────────────────────────────


class _BrokenProvider:
    """A provider that claims availability but always returns an error."""
    name = "broken"
    provider_id = "broken"
    model = "none"

    def is_available(self): return True

    def complete(self, messages, temperature=0.7, max_tokens=1024):
        return {"content": "", "finish_reason": "error",
                "error_class": "PROVIDER_OUTAGE", "error": "simulated failure",
                "provider": "broken", "model": "none"}


class TestFailover:

    def test_all_unavailable_returns_unavailable_not_local(self, monkeypatch):
        """When no provider is available resolve() must not return local."""
        from app.ai.provider import reset_provider, resolve_provider
        reset_provider()  # drop singleton cached chain/resolution from other tests
        _ensure_env(monkeypatch, SHUNYA_AI_PROVIDERS="")
        # Artificially clear env keys so none resolve as available.
        for k in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY",
                  "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN",
                  "HF_API_KEY", "TOGETHER_API_KEY", "ANTHROPIC_API_KEY",
                  "OPENAI_API_KEY"):
            monkeypatch.delenv(k, raising=False)
        provider = resolve_provider()
        assert provider.name != "local"
        assert provider.name == "unavailable"
        result = provider.complete([{"role": "user", "content": "hi"}])
        assert result["finish_reason"] == "error"
        assert result["error_class"] == "PROVIDER_OUTAGE"
        # Must NOT contain canned local text
        assert "Hello! I'm SHUNYA" not in result.get("content", "")
        assert "I've registered your input" not in result.get("content", "")

    def test_failover_skips_broken_uses_working(self, monkeypatch):
        """complete_with_failover should skip a broken provider and reach a working one."""
        from app.ai.provider import ProviderRegistry
        reg = ProviderRegistry()
        reg._chain = [_BrokenProvider()]
        # Add local (test-deterministic) as second choice.
        from app.ai.provider import LocalProvider
        reg._chain.append(LocalProvider())
        result = reg.complete_with_failover([{"role": "user", "content": "hello"}])
        assert result["finish_reason"] != "error"
        assert result.get("provider") == "local"
        assert result.get("content") is not None

    def test_all_fail_returns_truthful_failure(self, monkeypatch):
        from app.ai.provider import ProviderRegistry
        reg = ProviderRegistry()
        reg._chain = [_BrokenProvider()]
        result = reg.complete_with_failover([{"role": "user", "content": "hi"}])
        assert result.get("finish_reason") == "error"
        assert result.get("provider") == "unavailable"
        assert len(result.get("errors", [])) >= 1


# ── 4. Error classification ────────────────────────────────────────────


class TestErrorClass:

    def test_402_credits_required(self):
        from app.ai.model_catalog import classify_http_status
        assert classify_http_status(402).value == "CREDITS_REQUIRED"

    def test_404_retired_model(self):
        from app.ai.model_catalog import classify_http_status
        assert classify_http_status(404, model="llama-3.3-70b-versatile", retired_models=("llama-3.3-70b-versatile",)).value == "MODEL_RETIRED"

    def test_429_rate_limited(self):
        from app.ai.model_catalog import classify_http_status
        assert classify_http_status(429).value == "RATE_LIMITED"
        assert classify_http_status(429).retryable is True

    def test_204_unknown(self):
        from app.ai.model_catalog import classify_http_status
        assert classify_http_status(204).value == "UNKNOWN"


# ── 5. Capability registry ─────────────────────────────────────────────


class TestCapabilityRegistry:

    def test_status_structure(self):
        from app.ai import capabilities as caps
        st = caps.status()
        assert "image_generation" in st
        assert "text_chat" in st
        img = st["image_generation"]
        providers = img["providers"]
        poll = [p for p in providers if p["id"] == "pollinations"]
        assert len(poll) == 1
        assert poll[0]["available"] is True

    def test_summary_rows(self):
        from app.ai import capabilities as caps
        rows = caps.summarize()
        capability_values = {r["capability"] for r in rows}
        assert "image_generation" in capability_values
        assert "text_chat" in capability_values
        # video, embeddings, image_editing should be UNAVAILABLE (no providers)
        video = [r for r in rows if r["capability"] == "video_generation"]
        assert video
        assert video[0]["status"] == "UNAVAILABLE"
        assert video[0]["providers"] == []

    def test_execute_text_all_fail_truthful(self, monkeypatch):
        """Even without keys, execute must not fabricate content."""
        from app.ai.provider import reset_provider
        reset_provider()
        for k in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY",
                  "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN",
                  "HF_API_KEY", "TOGETHER_API_KEY"):
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("SHUNYA_AI_PROVIDERS", "")  # empty → free default chain
        from app.ai import capabilities as caps
        result = caps.execute(caps.Capability.TEXT_CHAT, {"prompt": "hello"})
        assert result["success"] is False
        assert result["error_class"] == "PROVIDER_OUTAGE"
        assert "I'm SHUNYA" not in result.get("error", "")
        assert result.get("errors", [])  # must have per-provider details

    def test_execute_image_pollinations_success(self, monkeypatch):
        """Pollinations fallback must produce a real image (bytes)."""
        # Monkeypatch the actual fetch to avoid network.
        from app.media import service as ms
        monkeypatch.setattr(ms, "_fetch_pollinations_bytes", lambda prompt, width=1024, height=1024: b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        monkeypatch.setattr(ms, "_generate_hf_image", lambda prompt, aspect_ratio="1:1": (_ for _ in ()).throw(RuntimeError("HF dead")))
        monkeypatch.setattr(ms, "_get_hf_token", lambda: "fake-token")
        from app.ai import capabilities as caps
        result = caps.execute(caps.Capability.IMAGE_GENERATION, {"prompt": "sunrise", "aspect_ratio": "1:1"})
        assert result["success"] is True
        assert "pollinations" in result.get("provider", "")
        # Service layer returns real bytes; the API ROUTE strips them into
        # image_generated/size flags before JSON serialization.
        assert result.get("image_bytes", b"").startswith(b"\x89PNG")

    def test_execute_video_not_available(self):
        from app.ai import capabilities as caps
        result = caps.execute(caps.Capability.VIDEO_GENERATION, {"prompt": "test"})
        assert result["success"] is False
        assert result["error_class"] == "PROVIDER_OUTAGE"

    def test_execute_research_missing_query(self):
        from app.ai import capabilities as caps
        result = caps.execute(caps.Capability.RESEARCH, {})
        assert result["success"] is False
        assert result["error_class"] == "BAD_REQUEST"