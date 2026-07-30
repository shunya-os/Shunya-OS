# Free LLM Routing & Failover Audit — SHUNYA OS

**Date:** 2026-07-30  
**Auditor:** Hermes Agent  
**System:** SHUNYA OS (Flask, shunyaos.com)  
**Repository:** `/home/shunya-deploy/shunya_os/`

---

## Executive Summary

SHUNYA has **two independent LLM routing systems** — an older `app/ai/provider.py` abstraction layer and a newer `app/llm/` (LLMRuntimeService) — plus a **third independent path** in `app/for1/engine.py` and a **fourth** in `app/ubme/discovery.py`. These systems do not share a common routing strategy, failover chain, or provider configuration. The primary routing layer (`app/ai/provider.py`) has a **static, single-evaluation** provider resolution with no dynamic failover, and the default models are **paid** (gpt-4o-mini, claude-3-haiku) — no free providers are configured or preferred.

**No API keys are currently set** on the production server. All LLM calls fall through to the `LocalProvider` — a rule-based, deterministic response generator that produces hardcoded, context-free replies. The system is running entirely without any actual LLM capability.

---

## 1. Architecture Overview

### 1.1 LLM Routing Layers

There are **four distinct LLM invocation paths**:

| Layer | Module | Purpose | Provider Resolution |
|-------|--------|---------|-------------------|
| A | `app/ai/provider.py` | General AI copilot, context-aware responses | Static chain (resolved once) |
| B | `app/llm/__init__.py` (LLMRuntimeService) | Structured, governed LLM calls with persistence | OpenRouter-only, no fallback |
| C | `app/for1/engine.py` | Travel proposal generation | OpenRouter → OpenAI, mock fallback |
| D | `app/ubme/discovery.py` | Business module generation from NL | Delegates to Layer A, then rule-based |

### 1.2 Data Flow Diagram

```
User Message
    │
    ├──→ app/ai/copilot.py (DEPRECATED adapter)
    │       │
    │       └──→ core/intelligence_runtime/integration.py
    │               │
    │               └──→ IntelligenceRuntime.process()
    │                       ├── IntentEngine (rule-based)
    │                       ├── ContextEngine (in-memory)
    │                       ├── RetrievalLayer (business graph, objects, memory)
    │                       ├── ReasoningEngine (rule-based, NOT LLM)
    │                       └── Returns IntelligenceResponse
    │
    └──→ app/ai/provider.py (direct LLM calls — not used by UIR)
            │
            └──→ Layer A Provider Chain
```

**Critical finding:** The Universal Intelligence Runtime (`core/intelligence_runtime/`) does **NOT** use the LLM provider at all. The `ReasoningEngine` is entirely rule-based — it generates responses from evidence strings using template patterns. The LLM provider in `app/ai/provider.py` is only used by the deprecated `app/ai/copilot.py` adapter and `app/ubme/discovery.py`.

---

## 2. Provider Resolution Chain (Layer A — `app/ai/provider.py`)

### 2.1 Resolution Logic

```python
def resolve_provider() -> LLMProvider:
    chain = [
        OpenRouterProvider(),      # 1st priority
        OpenAIProvider(),          # 2nd priority
        AnthropicProvider(),       # 3rd priority
        LocalProvider(),           # 4th priority (always available)
    ]
    for provider in chain:
        if provider.is_available():
            _PROVIDERS.append(provider)
            return provider
```

### 2.2 Availability Checks

| Provider | `is_available()` logic | Default Model |
|----------|----------------------|---------------|
| OpenRouter | `bool(OPENROUTER_API_KEY or OPENAI_API_KEY)` ⚠️ | `openai/gpt-4o-mini` |
| OpenAI | `bool(OPENAI_API_KEY)` | `gpt-4o-mini` |
| Anthropic | `bool(ANTHROPIC_API_KEY)` | `claude-3-haiku-20240307` |
| Local | Always `True` | `local` |

### 2.3 Default Models

| Provider | Default Model | Cost | Free Alternative Available? |
|----------|--------------|------|---------------------------|
| OpenRouter | `openai/gpt-4o-mini` | Paid ($0.15/M input, $0.60/M output) | No — `gpt-4o-mini` is the cheapest paid model |
| OpenAI | `gpt-4o-mini` | Paid ($0.15/M input, $0.60/M output) | No — no free tier configured |
| Anthropic | `claude-3-haiku-20240307` | Paid ($0.25/M input, $1.25/M output) | No — no free tier configured |
| Local | `local` | Free | N/A — rule-based, no actual LLM |

**Finding:** No free LLM providers (e.g., Google Gemini free tier, Llama 3 via Groq free tier, Claude 3 Haiku free on some platforms) are configured. The default models are all paid. Free models are **not preferred** — they are not even considered.

### 2.4 Provider Preference (Cost Priority)

The resolution chain prioritizes **OpenRouter** over **OpenAI** and **Anthropic**. This is a pragmatic choice — OpenRouter provides access to multiple models with a single API key and typically offers competitive pricing. However, there is no cost-based model selection logic — the system always uses the default model for the highest-priority available provider.

---

## 3. Failover Chain Analysis

### 3.1 Layer A (`app/ai/provider.py`)

**Failover chain:**
```
OpenRouter → OpenAI → Anthropic → Local (rule-based)
```

**CRITICAL WEAKNESS — Static cache, no dynamic failover:**
```python
_PROVIDERS: list[LLMProvider] = []

def get_provider() -> LLMProvider:
    if not _PROVIDERS:
        return resolve_provider()
    return _PROVIDERS[0]  # ← NEVER RE-EVALUATED
```

Once resolved, the provider is cached in `_PROVIDERS[0]` and **never re-evaluated**. If the resolved provider becomes unavailable mid-session (e.g., OpenRouter returns 503 errors), the system will continue to return errors from the cached provider — it will **not** fall back to the next provider in the chain.

**Impact:** A provider outage during a conversation causes all subsequent LLM calls to fail until the application is restarted or `reset_provider()` is called (which is only used in tests).

### 3.2 Layer B (`app/llm/__init__.py` — LLMRuntimeService)

**No failover chain at all.**
```python
def _create_run(self, ...):
    run = ModelRun(..., provider="openrouter", ...)
```

- Hardcoded to `provider="openrouter"` with `adapter_mechanism="openrouter_v1"`
- Uses `OpenRouterAdapter` which only talks to OpenRouter
- On error, records the failure in the database but **does not retry or fall back**
- Error classification is excellent (8 categories) but unused for routing decisions

### 3.3 Layer C (`app/for1/engine.py`)

```
OpenRouter → OpenAI (same key) → mock fallback (no real LLM)
```

- Uses the OpenAI Python SDK directly
- Falls back: `OPENROUTER_API_KEY` → `OPENAI_API_KEY` → `None` (mock data)
- Model hardcoded to `openai/gpt-4o-mini`
- No Anthropic or other provider fallback

### 3.4 Layer D (`app/ubme/discovery.py`)

```
LLM Provider (from app/ai/provider.py) → Rule-based templates
```

- Delegates to Layer A for LLM
- If LLM generation fails, falls back to industry-specific template matching
- Templates exist for: clinic, dental, manufacturing, legal, retail, restaurant, real estate

---

## 4. Conversation Continuity Analysis

### 4.1 Conversation Runtime (`core/intelligence_runtime/conversation.py`)

- **In-memory only** — conversations are lost on server restart
- **No provider tracking** — messages store `role`, `content`, and `timestamp` but NOT the provider/model that generated them
- **No context shift for provider switches** — if the provider changes mid-conversation, there is no indication in the history

### 4.2 ModelRun Database Persistence (`app/llm/models.py`)

The `ModelRun` table does track:
- `provider` (e.g., "openrouter")
- `provider_model_id` (e.g., "default")
- `status` ("succeeded", "failed")
- `error_class` and `error_reason_code`

However, this is only used by Layer B (LLMRuntimeService), not by Layer A.

---

## 5. Free vs. Paid Model Analysis

### 5.1 Current Configuration

| Aspect | Current State |
|--------|--------------|
| Free providers configured? | **No** |
| Cost-based model selection? | **No** |
| Default model cost | Paid (gpt-4o-mini at ~$0.15/M input tokens) |
| API keys set on server? | **None** |
| Actual LLM capability? | **None** — running on LocalProvider fallback |

### 5.2 Available Free Alternatives (Not Configured)

| Provider | Free Model | Free Tier Limits |
|----------|-----------|-----------------|
| Google AI | Gemini 1.5 Flash | 60 requests/minute, 1M tokens |
| Groq | Llama 3 / Mixtral | 30 requests/minute, 14,400/day |
| OpenRouter | Llama 3, Mistral variants | PAYG but cheap models exist |
| HuggingFace | Various open models | Rate-limited |

---

## 6. Identified Weaknesses

### 6.1 CRITICAL: No Dynamic Failover
The provider cache in `_PROVIDERS[0]` is never re-evaluated. A runtime provider outage causes cascading failures for all subsequent requests.

### 6.2 CRITICAL: No Free LLM Providers Configured
The system defaults to paid models even when free alternatives exist. No cost-awareness or budget constraints are implemented.

### 6.3 HIGH: OpenRouter Key Inheritance Bug
```python
class OpenRouterProvider(OpenAIProvider):
    def __init__(self, ...):
        super().__init__(
            api_key=api_key or os.getenv("OPENROUTER_API_KEY", ""),
            ...
        )
# In OpenAIProvider.__init__:
self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
```
If only `OPENAI_API_KEY` is set, `OpenRouterProvider` will still be available because the parent class falls back to `OPENAI_API_KEY`. This means requests will be routed through OpenRouter's API endpoint with an OpenAI key, which may or may not work depending on OpenRouter's key forwarding.

### 6.4 HIGH: Fragmented Routing Architecture
Four independent LLM invocation paths with different:
- Provider selection logic
- Failover strategies
- Error handling
- Model defaults

### 6.5 HIGH: LocalProvider Is Not a Real LLM
The `LocalProvider` is a keyword-matching, template-based response generator. It cannot:
- Answer questions about business data
- Generate meaningful summaries
- Analyze patterns or trends
- Provide any intelligent response

### 6.6 MEDIUM: Conversation Runtime Is In-Memory
`ConversationRuntime._conversations` is a plain dict — conversations are lost on restart. No persistence to database.

### 6.7 MEDIUM: No Provider Transparency in Conversations
The conversation history does not record which provider or model generated each response. Users cannot tell if the system switched providers.

### 6.8 MEDIUM: LLMRuntimeService Has No Fallback at All
Layer B hardcodes `provider="openrouter"` and has zero failover. If OpenRouter is unavailable, all governed LLM calls through this path fail.

### 6.9 LOW: Model Names Are Hardcoded
Models are hardcoded in default parameters:
- `provider.py`: `"gpt-4o-mini"`, `"openai/gpt-4o-mini"`, `"claude-3-haiku-20240307"`
- `for1/engine.py`: `"openai/gpt-4o-mini"`
- `llm/__init__.py`: `{"default": "openai/gpt-4o", "fast": "openai/gpt-4o-mini"}`

These should be configurable via environment variables or config.

### 6.10 LOW: No Rate Limiting Awareness
None of the providers implement rate-limit detection or backoff. The `_classify_error` method categorizes rate limits but doesn't trigger retry logic.

---

## 7. Test Results

### 7.1 Provider Resolution Tests (11/11 Passed)

| Test | Result |
|------|--------|
| LocalProvider is always available | ✅ |
| LocalProvider returns response | ✅ |
| LocalProvider contextual response | ✅ |
| OpenAI unavailable without key | ✅ |
| OpenRouter unavailable without key | ✅ |
| Anthropic unavailable without key | ✅ |
| Provider resolve returns local fallback | ✅ |
| Provider override for testing | ✅ |
| Provider implements interface | ✅ |
| LocalProvider greeting | ✅ |
| LocalProvider help request | ✅ |

### 7.2 Live Resolution Test

```
No API keys configured → LocalProvider selected
Provider: local
Model: local
Available: True
```

### 7.3 All-Keys Scenario Test

```
OPENROUTER_API_KEY set → OpenRouter (priority #1)
Only OPENAI_API_KEY set → OpenRouter (BUG: inherits OPENAI_API_KEY)
Only ANTHROPIC_API_KEY set → Anthropic
No keys → Local
```

---

## 8. Recommendations

### 8.1 Immediate (Critical)

1. **Add dynamic failover to provider resolution** — When `get_provider()` catches an error from the cached provider, it should iterate through the remaining chain and try the next available provider.

2. **Configure at least one free LLM provider** — Add Google Gemini or Groq as a fallback to reduce costs and ensure LLM availability.

### 8.2 Short-term (High)

3. **Fix OpenRouter key inheritance bug** — `OpenRouterProvider` should not inherit `OPENAI_API_KEY` as a fallback. Use separate key checks.

4. **Unify LLM routing** — Consolidate all four LLM invocation paths into a single routing layer with consistent failover.

5. **Add provider tracking to conversation history** — Record which provider/model generated each response in the conversation log.

### 8.3 Medium-term

6. **Persist conversations to database** — Move `ConversationRuntime` to use database-backed storage.

7. **Add cost-based model selection** — Implement a tiered system: free models for general queries, paid models for complex reasoning.

8. **Add retry with backoff** — Implement exponential backoff for rate-limited requests.

9. **Make models configurable** — Move all model names to environment variables or config.yaml.

---

## 9. Key Files Examined

| File | Lines | Role |
|------|-------|------|
| `app/ai/provider.py` | 349 | Primary LLM provider abstraction + failover chain |
| `app/ai/copilot.py` | 129 | Deprecated adapter over UIR |
| `app/ai/context.py` | 196 | Context window assembly |
| `app/ai/prompts.py` | 166 | Prompt templates + intent detection |
| `app/llm/__init__.py` | 183 | Governed LLM runtime service (Layer B) |
| `app/llm/models.py` | 35 | ModelRun database model |
| `core/intelligence_runtime/` | 7 files | Universal Intelligence Runtime |
| `core/intelligence_runtime/runtime.py` | 164 | Runtime orchestrator (no LLM calls) |
| `core/intelligence_runtime/reasoning.py` | 127 | Rule-based reasoning engine |
| `core/intelligence_runtime/conversation.py` | 98 | In-memory conversation management |
| `core/intelligence_runtime/integration.py` | 271 | UIR-SHUNYA integration layer |
| `app/for1/engine.py` | 455 | Proposal engine (Layer C) |
| `app/ubme/discovery.py` | 535 | Business discovery engine (Layer D) |
| `config.yaml` | 62 | App config (no LLM settings) |
| `app/__init__.py` | 725 | Flask app factory |

---

## 10. Appendix: Provider Cost Comparison

### Current Default Models

| Model | Provider | Input Cost | Output Cost | Cost/1M Tokens |
|-------|----------|-----------|------------|----------------|
| gpt-4o-mini | OpenAI | $0.15/M | $0.60/M | $0.15-0.60 |
| gpt-4o-mini | OpenRouter | $0.15/M | $0.60/M | $0.15-0.60 |
| claude-3-haiku | Anthropic | $0.25/M | $1.25/M | $0.25-1.25 |

### Free Alternatives (Not Configured)

| Model | Provider | Cost | Notes |
|-------|----------|------|-------|
| Gemini 1.5 Flash | Google AI | Free (60 rpm) | Up to 1M token context |
| Llama 3 70B | Groq | Free (30 rpm) | Very fast inference |
| Mixtral 8x7B | Groq | Free (30 rpm) | Good for reasoning |
| Llama 3.1 8B | OpenRouter | ~$0.02/M | Near-free |

---

*Report generated by Hermes Agent. All tests executed against live production environment at shunyaos.com:5001.*