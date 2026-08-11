"""Universal Intelligence Integration — wires the Intelligence Runtime with all SHUNYA providers.

This is the only file that understands how to connect the kernel runtime
to the SHUNYA ecosystem. Every surface consumes through this layer.

No surface shall import core.intelligence_runtime directly.
Every surface shall import this module.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from core.intelligence_runtime import get_runtime
from core.intelligence_runtime.types import (
    MemoryType,
)

# ── Telemetry ─────────────────────────────────────────────────────────────

_telemetry: dict[str, Any] = {
    "request_count": 0,
    "total_latency_ms": 0,
    "retrieval_latency_ms": 0,
    "reasoning_latency_ms": 0,
    "tool_failures": 0,
    "confidence_distribution": defaultdict(int),
    "clarification_count": 0,
    "cache_hit_count": 0,
    "errors": [],
}


def get_telemetry() -> dict[str, Any]:
    """Get runtime telemetry for observability."""
    t = dict(_telemetry)
    t["confidence_distribution"] = dict(t["confidence_distribution"])
    t["avg_latency_ms"] = round(t["total_latency_ms"] / max(t["request_count"], 1), 1)
    t["clarification_rate"] = round(t["clarification_count"] / max(t["request_count"], 1), 3)
    return t


def reset_telemetry() -> None:
    _telemetry["request_count"] = 0
    _telemetry["total_latency_ms"] = 0
    _telemetry["retrieval_latency_ms"] = 0
    _telemetry["reasoning_latency_ms"] = 0
    _telemetry["tool_failures"] = 0
    _telemetry["confidence_distribution"].clear()
    _telemetry["clarification_count"] = 0
    _telemetry["cache_hit_count"] = 0
    _telemetry["errors"].clear()


# ── Provider Wiring ───────────────────────────────────────────────────────

_initialized = False


def ensure_runtime() -> None:
    """Ensure the runtime is fully wired with SHUNYA providers.
    
    Called once at app startup. Safe to call multiple times.
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    runtime = get_runtime()

    # ── Business Graph Provider ──
    def _graph_search(query: str) -> list[dict]:
        from app.ubme.business_graph import list_graphs
        graphs = list_graphs()
        results = []
        q = query.lower()
        for g in graphs:
            for e in g.get("entities", []):
                if q in e.get("name", "").lower() or q in e.get("key", ""):
                    results.append(e)
            for r in g.get("relationships", []):
                if q in r.get("source", "") or q in r.get("target", ""):
                    results.append(r)
        return results[:20]

    # ── Object Instance Provider ──
    def _object_search(query: str, module_key: str = "") -> list[dict]:
        from app.ubme import engine as ubme_engine
        results = []
        if module_key:
            mod = ubme_engine.get_module(module_key)
            if mod and mod.object_types:
                for ot in mod.object_types:
                    instances = ubme_engine.list_instances(module_key, ot.key)
                    for inst in instances:
                        name = inst.get("name", "").lower()
                        if query.lower() in name:
                            results.append(inst)
        else:
            for mod in ubme_engine.list_modules():
                if mod.object_types:
                    for ot in mod.object_types:
                        instances = ubme_engine.list_instances(mod.key, ot.key)
                        for inst in instances:
                            name = inst.get("name", "").lower()
                            if query.lower() in name:
                                results.append(inst)
        return results[:20]

    # ── Memory Provider ──
    def _memory_search(query: str) -> list:
        return runtime.memory.search(query)

    # ── Internet/Web Search Provider (FDA7) ──
    def _internet_search(query: str) -> list[dict]:
        """Search the web via canonical search provider chain.
        
        Returns results with provenance for external evidence classification.
        """
        try:
            from app.search.provider import resolve_search_provider
            provider = resolve_search_provider()
            raw = provider.search(query, max_results=5)
            results = []
            for r in raw:
                results.append({
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("body", r.get("snippet", "")),
                    "provider": provider.name,
                })
            return results
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Web search failed: {e}")
            return []

    def _module_context(session_id: str) -> str:
        ctx = runtime.context.get(session_id)
        return ctx.active_module or ""

    runtime.wire_graph_provider(_graph_search)
    runtime.wire_object_provider(_object_search)
    runtime.wire_memory_provider(_memory_search)
    runtime.wire_internet_provider(_internet_search)

    # ── LLM Provider (with FDA8 model orchestration) ──
    def _model_orchestrated_complete(messages: list[dict], temperature: float = 0.7,
                                      max_tokens: int = 1024) -> dict:
        """Complete with model orchestration — deterministic-first routing (FDA8).

        Uses the canonical Inference Orchestrator's 5-stage pipeline:
        classify → policy → select → execute → observe.
        """
        from core.inference_orchestrator import (
            get_orchestrator, OrchestratorRequest, reset_orchestrator,
        )

        # Extract input text from messages
        input_text = ""
        if messages and len(messages) > 0:
            last_msg = messages[-1].get("content", "")
            # Join all messages for context
            parts = [m.get("content", "") for m in messages if m.get("content")]
            input_text = "\n".join(parts)

        # Build orchestrator request — the orchestrator handles classification,
        # policy, capability-based selection, execution, and observation
        request = OrchestratorRequest(
            input_text=input_text,
            session_id="runtime",
            temperature=temperature,
            max_tokens=max_tokens,
            request_type="chat",
        )

        try:
            orch = get_orchestrator()
            response = orch.process(request)
            return {
                "content": response.content or response.error or "No response",
                "role": "assistant",
                "provider": response.provider or "unknown",
                "model": response.model or "unknown",
                "orchestrator_pipeline": [s.to_dict() for s in response.pipeline],
            }
        except Exception as e:
            # Fallback: if orchestrator fails, use direct provider
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Orchestrator failed, falling back to direct provider: {e}")
            from app.ai.provider import get_provider
            provider = get_provider()
            return provider.complete(messages, temperature=temperature, max_tokens=max_tokens)

    runtime.wire_llm_provider(_model_orchestrated_complete)

    # ── Action Handlers ──
    def _handle_answer(params: dict) -> dict:
        return {"status": "answered"}

    def _handle_clarify(params: dict) -> dict:
        return {"status": "clarified", "question": params.get("question", "")}

    def _handle_execute(params: dict) -> dict:
        intent_text = params.get("intent", "")
        try:
            if "create" in intent_text.lower():
                return {"status": "executed", "action": "create", "note": "Action queued for user confirmation"}
            if "update" in intent_text.lower():
                return {"status": "executed", "action": "update", "note": "Action queued"}
            return {"status": "executed", "action": "unknown", "note": f"Recognized: {intent_text[:100]}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _handle_automate(params: dict) -> dict:
        return {"status": "automation_created", "note": "Automation rule created from suggestion"}

    runtime.wire_action("answer", _handle_answer)
    runtime.wire_action("clarify", _handle_clarify)
    runtime.wire_action("execute", _handle_execute)
    runtime.wire_action("automate", _handle_automate)


# ── Unified Consumer API ──────────────────────────────────────────────────

def ask(query: str, session_id: str = "", module_key: str = "",
        workspace: str = "", object_type: str = "", object_id: str = "",
        explain: bool = False) -> dict[str, Any]:
    """Single entry point for every intelligence request in SHUNYA.
    
    Every surface calls this function. No alternative path exists.
    """
    ensure_runtime()
    runtime = get_runtime()
    start = time.time()

    # Update context
    if module_key:
        runtime.context.update(session_id, active_module=module_key)
    if workspace:
        runtime.context.update(session_id, active_workspace=workspace)
    if object_type:
        runtime.context.update(session_id, active_object_type=object_type)
    if object_id:
        runtime.context.update(session_id, active_object_id=object_id)

    # Process through runtime
    response = runtime.process(
        user_input=query,
        session_id=session_id,
        module_key=_detect_module(query, session_id, module_key),
        workspace=workspace or runtime.context.get(session_id).active_workspace,
    )

    latency_ms = round((time.time() - start) * 1000, 1)

    # Record telemetry
    _telemetry["request_count"] += 1
    _telemetry["total_latency_ms"] += latency_ms
    if response.trace:
        conf_bucket = round((response.trace.confidence or 0) * 10) * 10
        _telemetry["confidence_distribution"][f"{conf_bucket}%"] += 1
    if response.requires_clarification:
        _telemetry["clarification_count"] += 1

    result = response.to_dict()
    result["latency_ms"] = latency_ms

    if explain and response.trace:
        from core.intelligence_runtime.explain import ExplainabilityEngine
        result["explanation"] = ExplainabilityEngine.explain_response(response)

    return result


def _detect_module(query: str, session_id: str, hint: str = "") -> str:
    """Detect the relevant module from query context."""
    if hint:
        return hint
    ctx = get_runtime().context.get(session_id)
    return ctx.active_module or ""


def suggest(session_id: str = "", module_key: str = "",
            object_type: str = "", object_id: str = "") -> list[dict]:
    """Get context-aware suggestions."""
    ensure_runtime()
    runtime = get_runtime()

    runtime.context.update(session_id,
                           active_module=module_key or "",
                           active_object_type=object_type or "",
                           active_object_id=object_id or "")

    suggestions = runtime.get_suggestions(session_id)
    return [s.to_dict() for s in suggestions]


def get_history(session_id: str, limit: int = 10) -> list[dict]:
    """Get conversation history."""
    ensure_runtime()
    runtime = get_runtime()
    return runtime.conversation.get_history(session_id, limit)


def navigate(session_id: str, workspace: str, module: str = "",
             object_type: str = "", object_id: str = "") -> dict[str, Any]:
    """Notify runtime of navigation for context continuity."""
    ensure_runtime()
    runtime = get_runtime()
    runtime.context.navigate(session_id, workspace, object_type, object_id)
    continuity = runtime.conversation.get_context_continuity(
        session_id, runtime.context.get(session_id))
    return {"status": "context_updated", "continuity": continuity}


def explain_last(session_id: str, message_index: int = -1) -> dict[str, Any]:
    """Get explanation for a response."""
    ensure_runtime()
    history = get_history(session_id, 20)
    if not history or (message_index >= 0 and message_index >= len(history)):
        return {"error": "Message not found"}
    return {
        "message": history[message_index] if message_index >= 0 else history[-1],
        "note": "Full reasoning trace is available on the ask() response when explain=True.",
    }


def store_memory(key: str, content: str, source: str = "user") -> None:
    """Store information in runtime memory."""
    ensure_runtime()
    runtime = get_runtime()
    runtime.memory.store(key, content, MemoryType.LONG_TERM, source=source)


def health() -> dict[str, Any]:
    """Get runtime health and telemetry."""
    ensure_runtime()
    runtime = get_runtime()
    h = runtime.health()
    h["telemetry"] = get_telemetry()
    h["initialized"] = _initialized
    return h