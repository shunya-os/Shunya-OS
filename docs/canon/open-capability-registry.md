# Open Capability Registry — SHUNYA v1.0

> **Status:** Active (Founder Accepted — Constitutional Directive)
> **Version:** 1.0
> **Authority:** Constitutional Directive — Open Capability Acceleration
> **Maintenance:** Reviewed before every major milestone. Updated continuously.

---

## Capability Index — Quick Reference

| # | Capability | Decision | Priority | Status |
|---|------------|----------|----------|--------|
| 1 | AI Inference — Fast | Adopt | P0 | Active |
| 2 | AI Inference — Free Fallback | Adopt | P0 | Active |
| 3 | AI Inference — Local Fallback | Adapt | P1 | Not started |
| 4 | Mixed Intelligence Router | Build | P0 | In design |
| 5 | Internet Search | Adapt | P0 | Active |
| 6 | Vector Search | Adopt | P1 | Not started |
| 7 | Full-Text Search | Adopt | P0 | Active |
| 8 | Speech-to-Text (browser) | Adopt | P0 | Active |
| 9 | Speech-to-Text (recorded) | Adapt | P2 | Not started |
| 10 | Text-to-Speech | Adapt | P2 | Not started |
| 11 | OCR | Adapt | P2 | Not started |
| 12 | Translation | Defer | P3 | — |
| 13 | Geocoding / Maps | Adapt | P2 | Not started |
| 14 | Weather | Adopt | P2 | Not started |
| 15 | Analytics (self-hosted) | Adopt | P2 | Not started |
| 16 | Object Storage | Adopt | P1 | Not started |
| 17 | Caching | Adopt | P1 | Not started |
| 18 | Music Playback | Adapt | P3 | Not started |
| 19 | WhatsApp Bridge | Adapt | P2 | Not started |
| 20 | Email | Defer | P3 | — |
| 21 | File Upload / Storage | Adopt | P0 | Active |
| 22 | Voice Input (browser) | Adopt | P0 | Active |
| 23 | Universal Search | Build | P0 | Active |

---

## Detailed Registry

### 1. AI Inference — Fast Primary

| Field | Value |
|-------|-------|
| **Capability** | Low-latency LLM inference for real-time AI responses |
| **User Value** | Every SHUNYA interaction depends on AI. Fast inference makes the system feel responsive and intelligent |
| **Constitutional Alignment** | Article III (Intelligence) — necessity of intelligent inference |
| **Technologies Evaluated** | Groq, OpenRouter, Together AI, Cloudflare Workers AI |
| **Decision** | **Adopt** — Groq (primary) |
| **Justification** | Groq provides the fastest free inference (llama-3.1-8b-instant, Mixtral). 30 req/min, 14,400 req/day is sufficient for single-founder operations. OpenAI-compatible API means zero provider code changes. |
| **Security Assessment** | Data sent to Groq's API. No PII in inference prompts by design. |
| **Privacy Assessment** | Acceptable for non-sensitive inference. Sensitive business data uses local provider fallback. |
| **Self-hosting Available** | No |
| **Free-tier Available** | Yes (30 req/min, 14,400/day) |
| **Long-term Maintainability** | High — OpenAI-compatible API is industry standard |
| **Implementation Priority** | P0 — Critical path |
| **Current Status** | Active (provider implemented in `app/ai/provider.py`) |

### 2. AI Inference — Free Fallback

| Field | Value |
|-------|-------|
| **Capability** | Secondary free LLM providers when primary is rate-limited or unavailable |
| **User Value** | Ensures AI never goes dark. Fallback chain prevents service interruption |
| **Technologies Evaluated** | Google Gemini Free API, OpenRouter (free models), Cloudflare Workers AI, HuggingFace Inference, Together AI |
| **Decision** | **Adopt** — all five as configurable fallback chain |
| **Justification** | Each provider has different free tier limits, rate limits, and model strengths. Together they form a never-exhausted fallback. Gemini offers 60 req/min and 1M token context for document-heavy tasks. OpenRouter free models cover niche capabilities. |
| **Security Assessment** | Same as #1. No sensitive data in prompts. |
| **Privacy Assessment** | Business data classification determines which providers serve which requests. |
| **Self-hosting Available** | No |
| **Free-tier Available** | Yes (Gemini: 60/min; Cloudflare: 100k/day; HF: 30k chars; Together: 1k/min) |
| **Long-term Maintainability** | High — all OpenAI-compatible or simple HTTP APIs |
| **Implementation Priority** | P0 — Critical path |
| **Current Status** | Partially implemented. Groq → OpenRouter → OpenAI → Anthropic → Local chain exists. Gemini, Cloudflare, Together AI, HF providers need implementation. |

### 3. AI Inference — Local Fallback

| Field | Value |
|-------|-------|
| **Capability** | Fully offline AI inference with no external API dependency |
| **User Value** | Works without internet. Zero cost. Complete privacy. |
| **Technologies Evaluated** | llama.cpp (CPU), Ollama, vLLM (requires GPU) |
| **Decision** | **Adapt** — llama.cpp with 3B-parameter quantized model |
| **Justification** | Server has 7.8GB RAM and no GPU. 3B parameter Q4 models (Phi-3-mini, Qwen2.5-3B) fit in ~2GB RAM and provide useful inference on CPU. llama.cpp is the most mature CPU inference engine. |
| **Security Assessment** | Data never leaves the machine. Highest security tier. |
| **Privacy Assessment** | Complete privacy. Suitable for sensitive business data. |
| **Self-hosting Available** | Yes — fully self-contained |
| **Free-tier Available** | Yes |
| **Long-term Maintainability** | High — llama.cpp is actively maintained, GGUF is stable format |
| **Implementation Priority** | P1 — Important but not blocking |
| **Current Status** | Not started. Need to download GGUF model, implement LlamaCppProvider. |

### 4. Mixed Intelligence Router

| Field | Value |
|-------|-------|
| **Capability** | Route queries to business data, internet, or AI with source-labeled output |
| **User Value** | Users get answers that are grounded in their actual data, enriched by internet knowledge, and clearly labeled by source |
| **Technologies Evaluated** | Custom architecture |
| **Decision** | **Build** |
| **Justification** | This is a core differentiator. No external tool achieves SHUNYA's requirement: business data as primary truth, internet as supporting, mixed intelligence synthesis, source-labeled output. |
| **Security Assessment** | Business data queries restricted to authorized sources. Internet queries go through configured search providers. |
| **Privacy Assessment** | Business data remains within authorization boundaries. |
| **Self-hosting Available** | N/A — built component |
| **Free-tier Available** | N/A — built component |
| **Long-term Maintainability** | Core architectural component |
| **Implementation Priority** | P0 — Critical path |
| **Current Status** | In design. Architecture established in constitutional directive. |

### 5. Internet Search

| Field | Value |
|-------|-------|
| **Capability** | Search the internet from within SHUNYA workspaces |
| **User Value** | Users can research suppliers, markets, competitors, regulations without leaving the OS |
| **Technologies Evaluated** | DuckDuckGo, Brave Search API, SearXNG, Tavily |
| **Decision** | **Adapt** — DuckDuckGo (primary) → Brave Search API (secondary) → SearXNG (self-hosted fallback) |
| **Justification** | DuckDuckGo requires no API key. Brave offers 2k free queries/month for better results. SearXNG is fully self-hosted and uncensorable. Three-tier chain ensures search never fails. |
| **Security Assessment** | Search queries may reveal business intent. Optionally route sensitive searches through SearXNG. |
| **Privacy Assessment** | DuckDuckGo and SearXNG do not track users. Brave claims minimal logging. |
| **Self-hosting Available** | SearXNG (Docker, fully self-hosted) |
| **Free-tier Available** | Yes (DuckDuckGo: unlimited; Brave: 2k/mo; SearXNG: free) |
| **Long-term Maintainability** | High — all three are stable projects |
| **Implementation Priority** | P0 — Critical path |
| **Current Status** | Active. DuckDuckGo → Brave → SearXNG chain specified in Z-22/23. |

### 6. Vector Search

| Field | Value |
|-------|-------|
| **Capability** | Semantic similarity search across business objects, documents, and conversations |
| **User Value** | Find relevant objects by meaning, not just by keyword match |
| **Technologies Evaluated** | Qdrant, ChromaDB, pgvector |
| **Decision** | **Adopt** — Qdrant (self-hosted, Docker) |
| **Justification** | Qdrant is the most mature self-hosted vector DB. REST API, multi-tenant, filtering, and payload support. ChromaDB is simpler but less mature. pgvector is tied to PostgreSQL and lacks dedicated query features. |
| **Security Assessment** | Self-hosted. Data never leaves the server. |
| **Privacy Assessment** | Complete privacy. |
| **Self-hosting Available** | Yes (Docker) |
| **Free-tier Available** | Yes |
| **Long-term Maintainability** | High — Qdrant is actively developed, Open source (Apache 2.0) |
| **Implementation Priority** | P1 — Important for RAG, not blocking core OS |
| **Current Status** | Not started |

### 7. Full-Text Search

| Field | Value |
|-------|-------|
| **Capability** | Fast text search across business objects |
| **User Value** | Universal search across all data types in one command |
| **Technologies Evaluated** | PostgreSQL Full-Text Search, Elasticsearch |
| **Decision** | **Adopt** — PostgreSQL FTS |
| **Justification** | Already in the database. Zero additional infrastructure. Elasticsearch is overkill for single-org scale. PostgreSQL FTS handles 100k+ objects efficiently. |
| **Security Assessment** | Inherits PostgreSQL security. |
| **Privacy Assessment** | Inherits PostgreSQL access controls. |
| **Self-hosting Available** | Already self-hosted |
| **Free-tier Available** | Yes |
| **Long-term Maintainability** | High — built into existing PostgreSQL |
| **Implementation Priority** | P0 — Already active |
| **Current Status** | Active (`/api/v1/search` endpoint exists) |

### 8–23. Additional Entries

*(Full entries for all remaining capabilities follow the same format. Summary table above captures all decisions.)*

---

## Technology Independence Declaration

Every technology listed in this registry is replaceable. No adoption is permanent. Future evaluations may:

- Upgrade to a better free technology
- Replace with a paid service when quality justifies cost
- Switch to a self-hosted alternative for privacy reasons
- Remove capabilities that no longer serve constitutional product priorities

The registry is a living document. It records decisions. It does not lock them.

---

## Provider Architecture (Constitutional Directive §6)

The provider layer SHALL evolve into a **configurable provider registry** with:

```yaml
# config.yaml — AI Provider Registry
ai:
  provider_chain:
    - id: groq
      priority: 1
      models:
        - llama-3.1-8b-instant  # primary
        - mixtral-8x7b           # fallback within provider
    - id: gemini
      priority: 2
      models:
        - gemini-2.0-flash
    - id: openrouter
      priority: 3
      models:
        - deepseek/deepseek-chat
        - qwen/qwen-2.5-72b
    - id: cloudflare
      priority: 4
      models:
        - "@cf/meta/llama-3.1-8b"
    - id: together
      priority: 5
      models:
        - llama-3.3-70b
    - id: huggingface
      priority: 6
      models:
        - meta-llama/Llama-3.2-3B-Instruct
    - id: local
      priority: 7
      models:
        - phi-3-mini-q4  # llama.cpp GGUF
```

**Provider properties (all SHALL):**
- **Health-aware**: Skip unresponsive providers automatically
- **Priority-aware**: Try providers in configured order
- **Independently replaceable**: One provider's failure does not affect others
- **Observable**: All inference requests and responses logged
- **Configurable**: Chain order, models, and keys via config, not code
- **Fault-tolerant**: Chain continues to next provider on any failure

**Data source priority (Mixed Intelligence Router):**
1. **Business Data** (PostgreSQL, Qdrant) — primary source of truth
2. **Internal Knowledge** (embeddings, past conversations) — contextual enrichment
3. **Internet** (DuckDuckGo, Brave, SearXNG) — supporting evidence
4. **AI Synthesis** (provider chain) — final output generation with source labels

---

## Implementation Roadmap

| Phase | Capabilities | Estimated Effort |
|-------|-------------|------------------|
| **P0 — Now** | Gemini provider, Cloudflare provider, configurable provider registry | 4 hours |
| **P1 — This sprint** | Qdrant vector search, MinIO object storage, Redis caching, llama.cpp local provider | 8 hours |
| **P2 — Next sprint** | Whisper STT, Piper TTS, Tesseract OCR, OpenStreetMap, Open-Meteo, SearXNG deployment, WhatsApp bridge | 16 hours |
| **P3 — Future** | Jamendo music, Email integration, Translation, Plausible/Umami analytics | Deferred |

---

> **End of Open Capability Registry v1.0**
> **Authority:** Constitutional Directive — Open Capability Acceleration
> **Next review:** Before next major milestone