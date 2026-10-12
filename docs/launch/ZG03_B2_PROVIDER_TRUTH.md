# ZG-03 B2 — Provider & Model Truth (Evidence, Audit, Fix)

Directive: **B2** — reproduce the Content Studio image-generation failure and
retired text-model failures against the current deployed SHA; audit every
advertised provider and model identifier; implement explicit configuration,
truthful availability/error classification, and a genuinely working image
fallback; verify real output and failure behavior without exposing credentials
or incurring unauthorized paid-provider charges.

## 1. Baseline (reproduced BEFORE any code change)

- Repository: `shunya_os`, branch `master`, HEAD `583598f`
  (`583598ff50ac792f41fb9b751fac1167754c307f`), clean working tree.
- Deployed SHA (production health, 127.0.0.1:5001 / HTTPS): `backend_release_sha`
  = `583598ff50ac792f41fb9b751fac1167754c307f` — matches HEAD.
- CI at this SHA: `gh run list` — completed **success** (CI-CD, 26m23s).
- Production tenant used for authenticated probes: certification tenant
  (`ws_certification`, org 278); login via HTTPS `/login/password`. No
  credentials appear in this document. No paid-provider API call was made.
- Constraint honored: curl → temp file → `jq` local parse (no network piping).

### 1.1 Content Studio image generation — failure reproduced

| Probe | Result @ 583598f | Classification |
|---|---|---|
| `GET /api/v1/content/providers` | 200 `success:true`; Economy tier advertises `huggingface` **available:true** and `dummy` **available:true** | UNTRUTHFUL AVAILABILITY — registration reported as availability |
| `GET /api/v1/media/status` | 200; `huggingface.available = false` | CONTRADICTS `/content/providers` |
| `POST /api/v1/media/generate` ("a sunrise over the ocean", 1:1) | 200 `success:true`, but `asset_url: null`, `runtime_state: "description_only"`, `result_kind: "visual_concept"`; `failure_reason`: **402 Payment Required** from `router.huggingface.co/nscale/v1/images/generations` — "You have no remaining credits. Purchase pre-paid credits…" | SUCCESS-SHAPED PLACEHOLDER — no image generated, response still `success:true` |
| `POST /api/v1/content/generate` `{"tier":"economy"}` | 200 `success:false`; error = **404** `api.groq.com/openai/v1/chat/completions` — the TEXT handler answered (response echoes `output_language`/`output_language_source`, fields the image handler does not emit) | ROUTE SHADOWING — `provider_bp /generate` registered after `content_bp /generate` on the same path (`app/__init__.py` registers `content_bp` at line 978, `provider_bp` at 982); first-registration-wins makes the image endpoint unreachable |

Root-causes (code, BEFORE):
- HF free serverless image inference is dead: HF now routes to
  `router.huggingface.co/nscale` and requires pre-paid credits (402 with key).
- The image "fallback" is a *text description* (`description_only` /
  `_generate_visual_concept`) — useful and honestly labeled in the UI, but it
  is NOT a real image and is packaged in a `success:true` envelope.
- `dummy` (solid-color PNG placeholder) is registered and advertised in
  production as an available image provider.
- `/api/v1/content/generate` image route is shadowed by the text route.

### 1.2 Retired text-model identifiers — audit of every advertised id

Live-catalog verification (2026-10-13, current date context):

| Provider | Advertised model (BEFORE) | Live catalog @ probe | Verdict |
|---|---|---|---|
| Groq | `llama-3.3-70b-versatile` (`.env GROQ_MODEL`, `app/ai/provider.py`, `core/inference_orchestrator/execution.py`, `provider_registry.py`, `core/model_orchestrator.py`, `core/inference_governance.py`) | Groq `/models` returns 11 ids; `llama-3.3-70b-versatile` **absent** (0 matches); current: `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `qwen/qwen3.8-27b`, `allam-2-7b` | **RETIRED — live 404 reproduced** |
| Gemini | `gemini-2.0-flash` | `models list` contains only 2.5.x (`gemini-2.5-flash`, `-lite`, `-pro`, …) | **RETIRED** |
| Cloudflare | `@cf/meta/llama-3.1-8b-instruct` | search result has `-fp8` variants and 3.x/4.x; exact id **absent** | **RETIRED** (renamed to `-fp8`) |
| OpenRouter | `openai/gpt-4o`, `openai/gpt-4o-mini` (`core/inference_orchestrator/...`, `app/llm/__init__.py`, `app/for1/engine.py`) | still listed in OpenRouter catalog (459 ids) but tagged legacy/deprecated (OpenAI retired gpt-4o era 2025-09-29); configured `deepseek/deepseek-chat` IS present | DEPRECATED-LEGACY (avoid advertising); configured default valid |
| HuggingFace (text) | `meta-llama/Llama-3.2-3B-Instruct` via `api-inference.huggingface.co/v1` | model page 200, but HF deprecated the old OpenAI-compatible endpoint (Inference Providers migration) and images already 402 no-credits | **OUTAGE / CREDITS_REQUIRED** (endpoint deprecated) |
| Together AI | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | **present** in Together `/models` | VALID |
| Anthropic | `claude-3-haiku-20240307` | `/v1/models` — **absent**; current: `claude-sonnet-4-5-20250929`, `claude-haiku-4-5-20251001`, … | **RETIRED** |
| OpenAI | `gpt-4o-mini` (paid; no key in env) | n/a (paid, not configured) | OUT_OF_SCOPE (default chain must exclude paid) |
| Local | canned "SHUNYA" replies, `is_available() == True` always | — | FAKE SUCCESS — auto-fallback returns fabricated text on the failure path; constitution forbids canned replies as answers |

### 1.3 Availability flag defects (BEFORE)

- `is_available()` = "API key present" only (OpenAI-derived providers) → reports
  available while the configured model is retired (the live Groq outage).
- `CloudflareAIProvider.is_available()` checks `account_id` but IGNORES the API
  token → "available" while every call 401s.
- Image registry `available` = "registered" (`p.name in self._generators`).
- `get_hf_status()` / `_check_hf_available()` performs a real 1x1 probe — the one
  truthful signal, but it is contradicted by `/api/v1/content/providers`.

### 1.4 Net product impact (BEFORE)

- Content Studio text generation: **broken in production** (Groq 404 → truthful
  error returned, but zero content paths succeed because resolve() picks the
  first *keyed* provider and never failovers on *errors*).
- Content Studio image generation: always `description_only` (no image) while
  reporting `success:true`; the image generation endpoint shadowed; `dummy`
  purple placeholder advertised as a real provider.

## 2. B2 Fix (implemented on branch `zero-gap-03-b2-provider-truth`)

1. **Explicit configuration** — `app/ai/model_catalog.py`: single canonical
   provider/model catalog (base_url, api_key envs, default model, valid models,
   retired models, free/paid, outage notes, chain policy). All provider classes
   and the image registry read defaults from it; `.env` values are honored only
   when still valid (retired env values fall back to the catalog default).
2. **Truthful availability** — `is_available()` requires: required env vars
   present AND model not retired AND provider not in known outage. Image
   registry availability reflects real probes; `dummy` becomes test-only
   (excluded from production listing).
3. **Error classification** — `ErrorClass` enum
   (`MODEL_RETIRED / AUTH_MISSING / CREDITS_REQUIRED / RATE_LIMITED /
   NETWORK_ERROR / PROVIDER_OUTAGE / BAD_REQUEST / UNKNOWN`) added to every
   provider failure result and surfaced in API responses; retryable flag for
   transient classes.
4. **Failover (text)** — `complete_with_failover()` walks the configured chain
   (free-first default: groq, gemini, openrouter, cloudflare, huggingface,
   togetherai; paid providers only when explicitly configured in
   `SHUNYA_AI_PROVIDERS`), skips unavailable/retired providers, moves to the
   next on classified errors, and returns a truthful aggregate failure when all
   fail. `LocalProvider` no longer auto-fallback (canned reply as success is
   forbidden); it remains selectable only explicitly (tests use
   `SHUNYA_AI_PROVIDERS=local`).
5. **Genuine image fallback** — Pollinations (`image.pollinations.ai`, free,
   no key; verified returning a real JPEG) registered as economy image provider;
   media generation tries HF → Pollinations → truthful `provider_unavailable`
   (description_only remains an *explicitly labeled, non-image* last resort).
   `/api/v1/content/generate` image endpoint un-shadowed by moving
   `provider_bp` to `/api/v1/content/image/*` while keeping the old
   `/api/v1/content/providers` listing alias.
6. **Default model updates** — groq→`openai/gpt-oss-20b`, gemini→
   `gemini-2.5-flash`, cloudflare→`@cf/meta/llama-3.1-8b-instruct-fp8`,
   togetherai→`meta-llama/Llama-3.3-70B-Instruct-Turbo` (env stays)
   everywhere retired ids were advertised (provider.py, inference_orchestrator,
   model_orchestrator, inference_governance, llm adapter, for1 engine).
7. **Production env** — `.env` model values updated at deploy time to valid
   catalog ids (GROQ_MODEL, GEMINI_MODEL, CLOUDFLARE_MODEL); not committed.
8. **Regression guards** — `tests/test_provider_catalog_b2.py` + `tests/test_media_fallback_b2.py`.

## 3. AFTER verification (filled post-deploy)

Implementation on branch `zero-gap-03-b2-provider-truth` (PR #6; merge SHA
recorded after merge). Local verification status:

- [x] Backend modules compile (`compileall` clean).
- [x] Frontend builds (`npm run build` clean, 4.67s).
- [x] New B2 tests: `tests/test_provider_catalog_b2.py` +
      `tests/test_media_fallback_b2.py` — **34 passed** (DATABASE_URL=sqlite
      in-memory, all network paths monkeypatched).
- [x] Related suites: test_content_studio, test_r6b27_output_language (25),
      test_media_lifecycle, test_fda7_fda8, test_fda9_fda10, test_communication
      — green (1 r6b27 test adapted to the canonical failover path, contract
      unchanged: truthful failure, single orchestrator call).
- [ ] Full local suite — awaiting background run.
- [ ] CI green on the PR SHA (required check `test`).
- [ ] Production deploy: HEAD == deployed `backend_release_sha`.
- [ ] Production text generation returns real content (provider + model named).
- [ ] Production image generation returns a real image (HF dead → Pollinations).
- [ ] `/api/v1/content/providers` truthful (no `dummy`, HF false, pollinations true).
- [ ] `/api/v1/capabilities/summary` truthful (image_generation AVAILABLE,
      video/embeddings UNAVAILABLE).
- [ ] Failure classification visible on forced failure (invalid provider 400,
      all-fail truth).
