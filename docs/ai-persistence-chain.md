# AI Persistence Chain — Workstream H

## Overview

The SHUNYA AI Persistence Chain ensures that every AI-generated artifact
(content, analysis, decisions) flows through a verifiable persistence
pipeline. This guarantees auditability, recoverability, and the ability
to trace any AI output back to its input parameters.

## Chain Architecture

```
User Input → AI Provider Chain → Content Generation → DB Persistence → History API
    │              │                      │                   │
    │              ▼                      ▼                   ▼
    │       /api/v1/ai/chat     /api/v1/content/generate   /api/v1/content/history
    │       (stateless)         (stateful, persists)
    ▼
Prompt + Settings
```

### Components

1. **AI Chat** (`/api/v1/ai/chat` — `app/ai/routes.py`)
   - Stateless conversation endpoint
   - Routes through provider registry (Groq → fallback chain)
   - Returns `{ content, model, usage }`
   - No automatic persistence (chat is ephemeral by design)

2. **Content Generate** (`/api/v1/content/generate` — `app/content_studio/routes.py`)
   - Stateful content generation
   - Accepts: `prompt`, `content_type`, `tone`, `platform`, `target_audience`, `word_count`
   - Calls `app.integration.service.generate_content()` for AI processing
   - Persists result to `ContentGeneration` model automatically
   - Returns generated content with DB-assigned `id`

3. **Content Generation Model** (`app/integration/models.py`)
   - SQLAlchemy model storing every generation
   - Fields: `id`, `identity_id`, `content_type`, `platform`, `prompt`,
     `generated_content`, `tone`, `target_audience`, `word_count`,
     `ai_model`, `is_favorited`, `created_at`, `updated_at`
   - Scoped by `identity_id` for multi-tenant isolation

4. **History API** (`/api/v1/content/history`)
   - `GET` — List recent generations (with optional `content_type` filter)
   - `GET /<id>` — Retrieve a specific generation
   - `POST /<id>/favorite` — Toggle favorite status
   - `DELETE /<id>` — Remove a generation
   - All operations scoped to the authenticated user

## Persistence Flow (detailed)

```
1. User submits POST /api/v1/content/generate { prompt, content_type, tone, ... }
2. Route handler (`api_generate`) validates authentication and input
3. Calls `app.integration.service.generate_content(...)` which:
   a. Routes through the AI provider registry
   b. Returns structured result with `content`, `word_count`, or error
4. On success, the route creates a ContentGeneration record:
   - identity_id from session/g
   - all request parameters
   - generated_content from AI response
   - ai_model = "provider_chain"
5. db.session.commit() ensures atomic persistence
6. Returns response with assigned `id` for immediate client reference
7. Client can retrieve at any time via GET /api/v1/content/history/<id>
```

## SUIL Inhibition Layer

Before persistence, every action can be gated through the Universal
Inhibition Layer (SUIL) at `POST /api/v1/content/inhibit`.

SUIL evaluates actions against deterministic risk levels:

| Level | Label     | Description                              |
|-------|-----------|------------------------------------------|
| 0     | ALLOW     | No restrictions                          |
| 1     | OBSERVE   | Default — log and allow                  |
| 2     | GUARD     | Guardrails apply                         |
| 3     | CONFIRM   | User confirmation required               |
| 4     | RESTRICT  | High risk, restricted action             |
| 5     | BLOCK     | Action denied outright                   |

SUIL also provides an authz-gated endpoint at `/api/v1/content/inhibit/authz`
that requires the `admin.view_audit` permission, integrating with the
canonical authorization engine rather than bypassing it.

## Provider Chain Resilience

The AI provider chain at `app/integration/service.py` implements:

- **Primary provider**: Groq (low latency, high throughput)
- **Fallback chain**: OpenAI → Anthropic → Ollama (local)
- **Cache layer**: Redis-backed response caching for identical prompts
- **Rate limiting**: Token bucket per identity per provider
- **Graceful degradation**: Each failure triggers the next fallback

## Testing Evidence

See `tests/test_workstreams_efgh.py` class `TestAIPersistenceChain`:

- `test_generate_persists_content_generation` — Verifies DB record count
  increases after a generate call
- `test_generated_content_retrievable_via_history` — Verifies generate →
  model query → history API round-trip
- `test_ai_chat_to_content_pipeline` — Verifies both AI chat and
  content generate endpoints respond correctly
- `test_content_generation_model_fields` — Verifies all critical
  model fields are populated correctly

## Verification Command

```bash
cd /home/shunya-deploy/shunya_os
python3 -m pytest tests/test_workstreams_efgh.py::TestAIPersistenceChain -v 2>&1 | head -30
```