"""
SHUNYA — LLM Runtime Service (Phase 9)
"""
import json, hashlib, uuid
from datetime import datetime, timezone
from typing import Optional, Any

from app.llm.models import ModelRun


class LLMRuntimeService:
    """Canonical governed LLM runtime. Provider-adapter-based, computation + lightweight persistence."""

    def __init__(self, provider_adapter=None, session=None, runtime_config=None):
        self._adapter = provider_adapter or FakeProviderAdapter()
        self._session = session
        self._config = runtime_config or {}

    # ------------------------------------------------------------------
    # Core Invocation
    # ------------------------------------------------------------------
    def invoke(self, messages: list[dict], purpose_code: str = "general",
               tenant_id: Optional[int] = None, model_alias: str = "default",
               max_tokens: int = 4096, timeout: int = 30,
               tool_policy: Optional[dict] = None,
               correlation_key: Optional[str] = None) -> dict:
        return self._invoke(messages, purpose_code, tenant_id, model_alias,
                           max_tokens, timeout, 1, tool_policy, correlation_key,
                           None)

    def invoke_structured(self, messages: list[dict], output_schema: dict,
                          purpose_code: str = "general",
                          tenant_id: Optional[int] = None, model_alias: str = "default",
                          max_tokens: int = 4096, timeout: int = 30,
                          tool_policy: Optional[dict] = None,
                          correlation_key: Optional[str] = None) -> dict:
        return self._invoke(messages, purpose_code, tenant_id, model_alias,
                           max_tokens, timeout, 1, tool_policy, correlation_key,
                           output_schema)

    def _invoke(self, messages, purpose_code, tenant_id, model_alias,
                max_tokens, timeout, attempt, tool_policy, correlation_key,
                output_schema) -> dict:
        ck = correlation_key or hashlib.sha256(json.dumps(
            {"msgs": messages, "p": purpose_code, "t": tenant_id, "s": str(output_schema)},
            sort_keys=True).encode()).hexdigest()[:32]

        run = self._create_run(tenant_id, purpose_code, model_alias, output_schema, ck)
        try:
            result = self._adapter.invoke({
                "messages": messages,
                "model": model_alias,
                "max_tokens": max_tokens,
                "timeout": timeout,
                "output_schema": output_schema,
                "tool_policy": tool_policy or {},
                "correlation_key": ck,
            })
            self._update_run(run, result)
            return self._normalize_response(run, result)
        except Exception as e:
            run.status = "failed"
            run.error_class = type(e).__name__
            run.error_reason_code = self._classify_error(e)
            run.completed_at = datetime.now(timezone.utc)
            self._save(run)
            return self._normalize_response(run, None)

    def _create_run(self, tenant_id, purpose_code, model_alias, output_schema, ck):
        run = ModelRun(tenant_id=tenant_id, correlation_key=ck, purpose_code=purpose_code,
                       output_mode="structured" if output_schema else "text",
                       provider="openrouter", provider_model_id=model_alias,
                       status="queued", adapter_mechanism="openrouter_v1", adapter_version="1.0")
        self._save(run)
        return run

    def _update_run(self, run, result):
        if result is None: return
        run.status = "succeeded" if result.get("finish_reason") != "error" else "failed"
        run.finish_reason = result.get("finish_reason", "")
        run.response_text = result.get("text", "")
        run.structured_result = json.dumps(result.get("structured")) if result.get("structured") else ""
        run.usage_prompt_tokens = result.get("usage", {}).get("prompt_tokens")
        run.usage_completion_tokens = result.get("usage", {}).get("completion_tokens")
        run.usage_cost = result.get("usage", {}).get("cost")
        run.completed_at = datetime.now(timezone.utc)
        self._save(run)

    def _normalize_response(self, run, result) -> dict:
        return {
            "run_id": run.id, "tenant_id": run.tenant_id, "status": run.status,
            "purpose_code": run.purpose_code, "provider": run.provider, "model": run.provider_model_id,
            "finish_reason": run.finish_reason, "text": run.response_text,
            "structured": json.loads(run.structured_result) if run.structured_result else None,
            "usage": {"prompt_tokens": run.usage_prompt_tokens,
                      "completion_tokens": run.usage_completion_tokens, "cost": run.usage_cost},
            "error_class": run.error_class, "error_reason_code": run.error_reason_code,
            "tool_requests": json.loads(run.tool_requests) if run.tool_requests else [],
            "correlation_key": run.correlation_key,
        }

    def _save(self, run):
        if self._session is not None:
            self._session.add(run)
            self._session.commit()

    def _classify_error(self, e):
        msg = str(e).lower()
        if "auth" in msg or "key" in msg or "credentials" in msg: return "authentication_failed"
        if "rate" in msg or "limit" in msg: return "rate_limited"
        if "timeout" in msg: return "timeout"
        if "model" in msg or "not found" in msg: return "model_unavailable"
        if "unavailable" in msg or "down" in msg: return "provider_unavailable"
        if "content" in msg or "policy" in msg: return "content_policy_rejected"
        if "invalid" in msg: return "invalid_request"
        if "schema" in msg or "json" in msg: return "structured_output_invalid"
        return "unknown_provider_error"

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------
    def inspect_run(self, run_id: int, tenant_id: Optional[int] = None) -> Optional[dict]:
        if self._session is None: return None
        run = self._session.get(ModelRun, run_id)
        if not run: return None
        if tenant_id is not None and run.tenant_id != tenant_id: return None
        return self._normalize_response(run, None)


class FakeProviderAdapter:
    """Deterministic fake for exhaustive tests."""
    def invoke(self, request: dict) -> dict:
        schema = request.get("output_schema")
        if schema:
            try:
                keys = list(schema.get("properties", {}).keys())
                structured = {k: f"test_{k}" for k in keys} if keys else {"result": "test"}
                return {"text": json.dumps(structured), "structured": structured,
                        "finish_reason": "stop", "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001}}
            except Exception:
                return {"text": "bad", "structured": None, "finish_reason": "error",
                        "usage": None}
        tool_policy = request.get("tool_policy") or {}
        if tool_policy.get("force_tool"):
            return {"text": "", "finish_reason": "tool_calls",
                    "tool_requests": [{"name": tool_policy["force_tool"], "args": {}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 3, "cost": 0.001}}
        return {"text": "Hello, I am a deterministic test response.",
                "finish_reason": "stop",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001}}


class OpenRouterAdapter:
    """Live OpenRouter adapter. Uses environment/provider-configured credentials."""
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key

    def invoke(self, request: dict) -> dict:
        import requests
        key = self._api_key
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        model_map = {"default": "openai/gpt-4o", "fast": "openai/gpt-4o-mini"}
        model = model_map.get(request.get("model", "default"), request.get("model"))
        body = {"model": model, "messages": request["messages"], "max_tokens": request.get("max_tokens", 4096)}
        schema = request.get("output_schema")
        if schema:
            body["response_format"] = {"type": "json_object"}
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers, json=body, timeout=request.get("timeout", 30))
        data = resp.json()
        if resp.status_code != 200:
            err = data.get("error", {}).get("message", str(resp.status_code))
            raise RuntimeError(f"OpenRouter error: {err}")
        choice = data["choices"][0]
        finish = choice["finish_reason"]
        text = choice["message"]["content"] or ""
        structured = json.loads(text) if schema and text else None
        usage = {
            "prompt_tokens": data.get("usage", {}).get("prompt_tokens"),
            "completion_tokens": data.get("usage", {}).get("completion_tokens"),
            "cost": data.get("usage", {}).get("total_cost"),
        }
        return {"text": text, "structured": structured, "finish_reason": finish,
                "usage": usage}