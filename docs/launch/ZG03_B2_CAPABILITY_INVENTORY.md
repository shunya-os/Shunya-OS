# ZG-03 B2 — Universal AI & Media Capability Inventory (baseline, pre-implementation)

Add-on directive baseline, recorded BEFORE wiring the provider-neutral
capability layer. Repository SHA at capture: `583598f` (branch
`zero-gap-03-b2-provider-truth`). No packages were installed, no models
downloaded, no configuration changed, no paid API called during this
inventory.

## 1. Installed vs declared packages (venv, `pip show`)

| Package | Version | Status |
|---|---|---|
| huggingface_hub | 1.28.0 | installed |
| Pillow | 12.3.0 | installed |
| httpx | 0.28.1 | installed |
| openai (SDK) | 2.48.0 | installed (used by for1 engine + LLM adapter) |
| edge-tts | — | NOT installed |
| sentence-transformers | — | NOT installed |
| groq SDK | — | NOT installed (Groq called via OpenAI-compatible HTTP in app/ai/provider.py) |
| anthropic SDK | — | NOT installed (called via raw HTTP in provider.py) |
| together SDK | — | NOT installed (OpenAI-compatible HTTP) |
| torch / transformers / accelerate | — | NOT in requirements.txt (no local model runtime) |

requirements.txt declares only `requests`, `httpx`, `openai>=1.0` for the AI
surface — everything else (Groq, Gemini, OpenRouter, Anthropic, HF) is driven
with plain HTTP, no vendor SDKs. No dependency declares TTS/STT/embeddings/
video/model-runner support.

## 2. Existing adapters (adapters/ package — real, honest implementations)

| Adapter | File | Capability | Runtime basis | Works today? |
|---|---|---|---|---|
| `FluxAdapter` | adapters/image/flux.py | image generation | HF serverless (`api-inference.huggingface.co/models/...`) | UNVERIFIED — HF serverless now requires prepaid credits (402 reproduced for image generation); classic model endpoint may still serve some models |
| `ComfyUIAdapter` | adapters/image/comfyui.py | image gen/edit | self-hosted ComfyUI (`COMFYUI_URL`) | CONFIG-DEPENDENT — only when a ComfyUI server is running; none verified |
| `WhisperAdapter` | adapters/speech/whisper.py | STT | HF serverless whisper-large-v3/v2 + retries | UNVERIFIED — same HF credits concern; raises honestly when unavailable |
| `PiperAdapter` | adapters/speech/piper.py | TTS | local piper-tts OR HF serverless `rhasspy/piper-voices` | CONFIG-DEPENDENT — local piper not installed; HF path unverified |
| `KokoroAdapter` | adapters/speech/kokoro.py | TTS | self-hosted Kokoro FastAPI (`KOKORO_API_URL`) or HF serverless `hexgrad/Kokoro-82M` | UNVERIFIED — no local server; HF path unverified |
| `LibreOffice/OnlyOfficeAdapter` | adapters/document/ | documents | system binaries | UNVERIFIED (installed binaries not probed) |
| `SearXNGAdapter` | adapters/search/searxng.py | search | SearXNG endpoint | CONFIG-DEPENDENT |
| `PGVectorAdapter` | adapters/search/pgvector.py | vector search | PostgreSQL | INSTALLED-db dependent (psycopg2) |
| `OpenSearchAdapter` | adapters/search/opensearch.py | search | OpenSearch | CONFIG-DEPENDENT |
| Infra adapters | adapters/infra/ | redis/rabbitmq/prometheus/grafana/posthog | running services | CONFIG-DEPENDENT (instantiated, connection unproven) |

All adapters share the same honest contract: missing credentials/config raise
`RuntimeError` — no placeholder/audio/image fabricated. `adapters/_hf.py`
retries 503 cold-starts with backoff and treats 400/401/402/403/404/422 as
terminal.

## 3. Existing orchestration surfaces (unwired canonical architecture)

- `core/personal_os/providers.py` — `ProviderOrchestrator`: universal-provider
  registry declaring documents/image_gen/speech/browser/search/visualization/
  ocr/search_engine/storage/vector_db/cache/messaging/monitoring/analytics.
  **UNTRUTHFUL today:** every entry is hardcoded `status: "available"` with
  `adapter_key: None`; nothing probes ComfyUI/Whisper/Piper/Kokoro/
  Playwright/SearXNG/MinIO. `is_available()` = "name in dict". No callers in
  `app/` (unwired → under-delivery, per FCR-02 classification: CANONICAL +
  MUST CONNECT).
- `core/inference_orchestrator/` — `ProviderRegistry`/`ModelRegistry`/
  `ExecutionLayer`: capability-based discovery (CHAT_COMPLETION, TEXT_GENERATION,
  STREAMING, FUNCTION_CALLING, VISION, STRUCTURED_OUTPUT, CODE_GENERATION) with
  quota + health. No callers in `app/` (unwired).
- `app/ai/provider.py` — the LIVE text chain (fixed in B2: catalog-driven
  defaults, truthful availability, classified errors, failover, no canned
  auto-fallback).
- `app/ai/model_catalog.py` — NEW canonical catalog (B2): provider specs,
  valid/retired model ids verified against live provider catalogs, ErrorClass
  taxonomy, chain policy (free-first; paid only explicit).
- `app/content_studio/image_providers.py` + `app/media/service.py` — image
  registry + HF→Pollinations fallback chain (fixed in B2; Pollinations
  verified returning a real JPEG free of charge).
- `docs/canon/open-capability-registry.md` — constitutional registry doc
  (decisions only; provider ids in it are now stale — refresh with the audit).

## 4. Capability gaps at baseline

| Capability | Free provider ready today? | Baseline status |
|---|---|---|
| TEXT_CHAT / TEXT_GENERATION | Groq (key present, model retired → fixed to gpt-oss-20b), OpenRouter (configured), Gemini (retired id → fixed), Together, Cloudflare | BROKEN pre-B2 (Groq 404), now fixed with failover |
| IMAGE_GENERATION | Pollinations (verified real JPEG) | BROKEN pre-B2 (HF 402, description-only "success"), now falls back to Pollinations |
| IMAGE_EDITING | none free/verified (ComfyUI self-hostable, unproven; HF credits-gated) | GAP — register capability with truthful unavailable status |
| VIDEO_GENERATION | none (Wan / LTX-Video self-hostable, GPU-required; Pollinations video unverified) | GAP — evaluate + document; truthful unavailable |
| SPEECH_TO_TEXT | WhisperAdapter (HF serverless — credit-gated at baseline; Groq `whisper-large-v3` present in catalog, free) | REGISTERED-UNVERIFIED |
| TEXT_TO_SPEECH | Piper/Kokoro adapters (HF/self-host, credit-gated); edge-tts NOT installed (free, no key, MS Edge online) | GAP — adapter exists, provider unverified |
| EMBEDDINGS | sentence-transformers NOT installed (self-hostable); HF credit-gated | GAP — truthful unavailable |
| RESEARCH | DuckDuckGo/SEarXNG adapters exist (search surface live in app/search) | AVAILABLE (existing) |

## 5. Licensing / free-tier notes (evaluated candidates)

- **Qwen (Qwen2.5/3)** — Apache-2.0 weights; commercial-use OK. Served free via
  OpenRouter/Groq(27b)/Together. No local runtime installed (would need
  transformers/ollama).
- **Llama (3.x/4)** — Llama community license; free for ≤700M MAU; commercial
  OK under license. Served free via Groq (retired 70b-versatile; gpt-oss now),
  Cloudflare (fp8), Together.
- **Mistral (small 3.1 24B)** — Apache-2.0; served on Cloudflare/Together.
- **Z-Image** — open-weight, FLUX-architecture (QwenNV team, Apache-2.0);
  self-hostable GPU; no free hosted API verified.
- **Stable Diffusion (SD3.5/SDXL)** — Stability AI community license (free
  <1M MAU); self-hostable GPU; no free hosted API verified.
- **Wan (2.1 video)** — Apache-2.0, self-hostable GPU (24GB+); no free hosted
  API verified.
- **LTX-Video** — Apache-2.0, self-hostable GPU; no free hosted API verified.
- Pollinations — free public image endpoint, no key; **verified working**.
- Hugging Face Inference Providers — requires prepaid credits (402), free tier
  ended for image generation; text/STT/TTS unchanged until re-verified.

## 6. Reuse opportunities (smallest provider-neutral layer)

1. `app/ai/model_catalog.py` → single model-id authority (no hardcoding).
2. `app/ai/provider.py` failover → text capability adapter.
3. `app/media/service.py` HF→Pollinations chain → image capability adapter.
4. `adapters/` package (whisper/piper/kokoro/flux/comfyui) → STT/TTS/image
   adapters, made truthful + probed through the capability registry.
5. `core/personal_os/providers.py` → the universal provider surface to be made
   TRUTHFUL (computed status, not dict claims) and wired to a diagnostics
   endpoint; retain as canonical (never delete unwired architecture).
6. `docs/canon/open-capability-registry.md` → refresh verified statuses.

## 7. Recommended layer (implemented next)

`app/ai/capabilities.py` — CapabilityRegistry: `Capability` enum (TEXT_CHAT,
TEXT_GENERATION, IMAGE_GENERATION, IMAGE_EDITING, VIDEO_GENERATION,
SPEECH_TO_TEXT, TEXT_TO_SPEECH, EMBEDDINGS, RESEARCH), per-capability provider
chains resolved from the catalog, `execute()` with timeout + one retry on
retryable classes + failover, truthful `status()` per provider (probe-based),
and `diagnostics()` for the `/api/v1/capabilities*` endpoints. `ProviderOrchestrator`
gains truthful availability reporting computed from this registry. No new
chat UI; Content Studio + SHUNYA AI reuse the same adapters.