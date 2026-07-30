# Inference Orchestrator Canon

> **Phase J · SHUNYA OS**
> **Status: CANONICAL — Implementation Specification**
> **Version: 1.0**

---

## 1. Purpose

The Inference Orchestrator is the central routing and execution coordinator for all SHUNYA inference operations. It decouples *what* to ask from *where* to ask, enabling provider-agnostic inference with automatic fallback, performance-aware routing, and full observability.

### 1.1 Dependency chain

```
Application Layer (routes, copilots, agents)
    ↓
Inference Orchestrator (routing, execution, telemetry)
    ↓
Execution Layer (provider-specific formatting & dispatch)
    ↓
External Providers (OpenAI, Anthropic, OpenRouter, Local)
```

### 1.2 Principles

1. **Provider-agnostic interface.** Every inference request uses the same structured format regardless of backend provider.
2. **Automatic failover.** If a provider fails, the chain falls through to the next available provider.
3. **Learning over time.** Telemetry from every request feeds the Learning Router, which evolves routing recommendations.
4. **Observable pipeline.** Every stage of the pipeline is timed, logged, and returned in the response.
5. **No hardcoded provider logic.** Provider-specific formatting is isolated in the execution layer.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     INFERENCE ORCHESTRATOR                           │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     Five-Stage Pipeline                        │  │
│  │                                                               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │  │
│  │  │Classify  │→ │  Policy  │→ │  Select  │→ │ Execute  │──┐  │  │
│  │  │          │  │          │  │          │  │          │  │  │  │
│  │  │ Intent   │  │ Prov.    │  │ Router   │  │ OpenAI   │  │  │  │
│  │  │ Type     │  │ Allowed  │  │ Recom.   │  │ Anthropic│  │  │  │
│  │  │ Complex. │  │ Timeout  │  │ Fallback │  │ Local    │  │  │  │
│  │  │ Tools    │  │ Audit    │  │          │  │          │  │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │  │
│  │                                                           │  │  │
│  │                                                     ┌────┘  │  │
│  │                                                     │       │  │
│  │                                                     ↓       │  │
│  │                                               ┌──────────┐  │  │
│  │                                               │ Observe  │←─┘  │
│  │                                               │          │     │
│  │                                               │ Record   │     │
│  │                                               │ Telemetry│     │
│  │                                               └──────────┘     │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────────┐  ┌──────────────────────────────────────┐  │
│  │                    │  │                                      │  │
│  │  Execution Layer   │  │        Learning Router               │  │
│  │                    │  │                                      │  │
│  │  ┌──────────────┐  │  │  ┌──────────────┐ ┌──────────────┐ │  │
│  │  │ OpenAI Fmt   │  │  │  │ Telemetry    │ │ Provider     │ │  │
│  │  │ Anthropic Fmt│  │  │  │ Store        │ │ Scores       │ │  │
│  │  │ Local Fmt    │  │  │  │ (JSONL)      │ │ (Composite)  │ │  │
│  │  │ Response     │  │  │  └──────────────┘ └──────────────┘ │  │
│  │  │ Parsers      │  │  │                                     │  │
│  │  └──────────────┘  │  │  ┌──────────────┐ ┌──────────────┐ │  │
│  │  ┌──────────────┐  │  │  │ Insights     │ │ Recommenda-  │ │  │
│  │  │ Provider     │  │  │  │ Aggregation  │ │ tion Engine  │ │  │
│  │  │ Chain        │  │  │  └──────────────┘ └──────────────┘ │  │
│  │  └──────────────┘  │  └──────────────────────────────────────┘  │
│  └────────────────────┘                                            │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1 Component responsibilities

| Component | Responsibility |
|---|---|
| **InferenceOrchestrator** | Singleton entry point. Owns pipeline, execution layer, and learning router. Exposes `process()`, `health_check()`, `get_dashboard()`. |
| **Pipeline** | Five-stage execution: classify → policy → select → execute → observe. Each stage is a discrete method with structured output. |
| **ExecutionLayer** | Provider-agnostic dispatch. Formats requests into provider-native payloads, sends HTTP calls, parses responses. |
| **LearningRouter** | Telemetry storage, provider performance scoring, routing recommendations, and insights aggregation. |

---

## 3. Pipeline Stages

### 3.1 Classify

Analyzes the incoming request to determine routing-relevant attributes.

**Input:** `OrchestratorRequest`
**Output:** `ClassificationResult`

| Attribute | Values | How determined |
|---|---|---|
| `request_type` | `chat`, `embedding`, `tool_call` | From request or heuristic |
| `complexity` | `simple`, `moderate`, `complex` | Word count, detected intent keywords |
| `requires_tools` | `true`, `false` | Keywords like "create", "schedule", "update" |
| `requires_streaming` | `true`, `false` | Complex requests and long inputs |
| `detected_intent` | `greeting`, `retrieval`, `creation`, `explanation`, `analysis`, `general` | Keyword/pattern matching |

### 3.2 Policy

Applies routing constraints based on request classification and system configuration.

**Input:** `OrchestratorRequest`, `ClassificationResult`
**Output:** `PolicyResult`

| Attribute | Behaviour |
|---|---|
| `allowed_providers` | Filtered by complexity: simple→all, moderate→openai+anthropic, complex→openai+anthropic+audit |
| `timeout_seconds` | 30s (simple), 60s (moderate), 120s (complex) |
| `requires_audit` | True for complex requests |
| `max_cost` | Reserved for future cost-based routing |

### 3.3 Select

Consults the Learning Router to choose the best provider+model for this request.

**Input:** `OrchestratorRequest`, `ClassificationResult`, `PolicyResult`
**Output:** `Recommendation`

Fallback logic when no telemetry exists:
- Use `provider_hint` if specified in request
- Use `model` if specified in request
- Default: `gpt-4o` (complex), `gpt-4o-mini` (moderate/simple)

### 3.4 Execute

Builds an `InferenceRequest` from the orchestrator request and dispatches it through the Execution Layer.

**Input:** `OrchestratorRequest`, `Recommendation`
**Output:** `InferenceResult`

The Execution Layer:
1. Formats the request into the provider-native payload
2. Sends the HTTP request (with circuit-breaking)
3. Parses the response into a normalized `InferenceResult`
4. Falls through the provider chain on failure

### 3.5 Observe

Records telemetry from the completed execution into the Learning Router.

**Input:** `OrchestratorRequest`, `InferenceResult`, `Recommendation`
**Output:** None (side effect: telemetry stored)

Records: provider, model, latency, token usage, success/failure, finish reason.

---

## 4. Execution Layer

### 4.1 Provider chain

The Execution Layer maintains a priority-ordered list of provider configurations:

| Priority | Provider | Source | Fallback |
|----------|----------|--------|----------|
| 10 | OpenRouter | `OPENROUTER_API_KEY` env | → priority 20 |
| 20 | OpenAI | `OPENAI_API_KEY` env | → priority 30 |
| 30 | Anthropic | `ANTHROPIC_API_KEY` env | → priority 100 |
| 100 | Local | Always available | Terminal |

### 4.2 Provider-specific formatting

Each provider has a dedicated formatter and response parser:

- **OpenAI-compatible** (OpenAI, OpenRouter, Groq): `format_openai_payload()` → `/chat/completions` → `parse_openai_response()`
- **Anthropic**: `format_anthropic_payload()` → `/v1/messages` → `parse_anthropic_response()`
- **Local**: `format_local_payload()` → deterministic template engine → `parse_local_response()`

### 4.3 Normalized response

Every provider returns an `InferenceResult`:

```python
InferenceResult {
    content: str          # Generated text
    model: str            # Model used
    finish_reason: str    # stop | length | error
    usage: dict           # token counts
    provider: str         # Provider name
    latency_ms: float     # Round-trip time
    error: str | None     # Error message if failed
}
```

---

## 5. Learning Router

### 5.1 Telemetry storage

Records are stored in-memory and persisted to `~/.shunya/inference_router_telemetry.jsonl` (append-only JSONL).

```
TelemetryRecord {
    session_id, provider, model, request_type,
    input_tokens, output_tokens, latency_ms,
    success, error, finish_reason, timestamp
}
```

### 5.2 Provider scoring

Composite score formula (higher = better):

```
score = (success_rate × 50) + (max(0, 1 - latency_ratio) × 30) + (throughput_ratio × 20)
```

| Component | Weight | Description |
|---|---|---|
| Success rate | 50% | successful_requests / total_requests |
| Latency efficiency | 30% | 1 - (avg_latency / max_latency_across_all_providers) |
| Throughput | 20% | avg_output_tokens / max_output_tokens_across_all_providers |

### 5.3 Insights

The `get_insights()` method aggregates telemetry over a configurable time window:

- Per-provider breakdown: total requests, success rate, avg/p50/p95 latency, avg tokens
- Error rate tracking
- Summary string

### 5.4 Recommendations

`get_recommendation()` returns the highest-scoring provider, filtered by preferred providers when specified. Returns confidence score and reasoning string.

---

## 6. Public API

### 6.1 InferenceOrchestrator

```python
class InferenceOrchestrator:
    def process(request: OrchestratorRequest) -> OrchestratorResponse
    def health_check() -> dict
    def get_dashboard() -> dict
    def reset()
```

### 6.2 OrchestratorRequest

```python
@dataclass
class OrchestratorRequest:
    input_text: str
    session_id: str = ""
    model: str = ""
    provider_hint: str = ""
    request_type: str = "chat"
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: str = ""
    conversation_history: list[dict] = []
    metadata: dict = {}
```

### 6.3 OrchestratorResponse

```python
@dataclass
class OrchestratorResponse:
    request_id: str
    content: str
    model: str
    provider: str
    finish_reason: str
    usage: dict
    latency_ms: float
    error: str | None
    pipeline: list[PipelineStage]
    recommendation: Recommendation | None
    timestamp: str
```

### 6.4 Singleton access

```python
from core.inference_orchestrator import get_orchestrator, reset_orchestrator

orchestrator = get_orchestrator()
response = orchestrator.process(request)
```

---

## 7. Error Handling

### 7.1 Provider failure

When a provider returns an error:
1. Log the failure with provider name and error details
2. Fall through to the next provider in the chain
3. If all providers fail, return `InferenceResult` with `finish_reason="error"` and the last error message

### 7.2 Pipeline stage failure

Each pipeline stage is wrapped in try/except:
- If a stage fails, the pipeline short-circuits and returns an `OrchestratorResponse` with the error attached to the failed stage
- The `observe` stage is non-fatal — failures are logged but do not block the response

### 7.3 Circuit-breaking

The Execution Layer respects per-provider `max_retries` (default: 2) and `timeout_seconds` (default: 60). Future: add sliding-window circuit breaker.

---

## 8. Usage Examples

### 8.1 Basic inference

```python
from core.inference_orchestrator import get_orchestrator, OrchestratorRequest

orchestrator = get_orchestrator()
request = OrchestratorRequest(
    input_text="What are my open invoices?",
    session_id="session_abc123",
    system_prompt="You are a helpful financial assistant.",
)
response = orchestrator.process(request)
print(response.content)
# → "Let me look up your open invoices..."
```

### 8.2 With provider hint

```python
request = OrchestratorRequest(
    input_text="Write a complex SQL query",
    provider_hint="anthropic",     # Use Claude for this request
    temperature=0.3,
    max_tokens=4096,
)
response = orchestrator.process(request)
```

### 8.3 Health check

```python
status = orchestrator.health_check()
# → {"status": "healthy", "total_requests_processed": 42, ...}
```

### 8.4 Dashboard

```python
dashboard = orchestrator.get_dashboard()
# → {"health": {...}, "insights": {...}, "recommendation": {...}, "providers": [...]}
```

---

*End of Inference Orchestrator Canon*