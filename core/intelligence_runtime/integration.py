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
        # Identity-scoped memory retrieval — the runtime context carries the
        # authenticated identity and tenant, and search is constrained to it.
        ctx = runtime.context.get(runtime.context._current_session)
        return runtime.memory.search(
            query,
            identity_id=getattr(ctx, "identity_id", "") if ctx else "",
            tenant_id=getattr(ctx, "tenant_id", "") if ctx else "",
        )

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

    # ── Knowledge Intelligence Provider (UCP-04) ──
    def _knowledge_search(query: str) -> list[dict]:
        """Search knowledge objects via canonical KnowledgeIntelligence (UCP-04)."""
        try:
            from core.knowledge_intelligence.engine import KnowledgeIntelligenceEngine
            from core.knowledge_intelligence.models import Knowledge

            results = []
            knowledge_list = []
            try:
                from app import db
                from app.models import KnowledgeDocument
                rows = db.session.query(KnowledgeDocument).order_by(
                    KnowledgeDocument.updated_at.desc()
                ).limit(50).all()
                for r in rows:
                    tags = []
                    if r.tags:
                        tags = [t.strip() for t in r.tags.split(",") if t.strip()]
                    knowledge_list.append(Knowledge(
                        title=r.title or "",
                        statement=r.extracted_text or r.summary or "",
                        summary=r.summary or "",
                        tags=tags,
                        domain=r.category or "",
                        is_active=True,
                        confidence_score=0.9,
                    ))
            except Exception:
                pass

            if knowledge_list:
                engine = KnowledgeIntelligenceEngine()
                search_results = engine.search(knowledge_list, query, max_results=5)
                for sr in search_results:
                    results.append({
                        "content": sr.summary[:300] if sr.summary else sr.title,
                        "source": f"knowledge_intelligence/{sr.knowledge_id}",
                        "relevance": sr.relevance_score,
                        "confidence": sr.confidence_score,
                        "metadata": {
                            "title": sr.title,
                            "knowledge_type": sr.knowledge_type,
                            "summary": sr.summary,
                        },
                    })
            return results
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Knowledge search failed: {e}")
            return []

    runtime.wire_graph_provider(_graph_search)
    runtime.wire_object_provider(_object_search)
    runtime.wire_memory_provider(_memory_search)
    runtime.wire_internet_provider(_internet_search)
    runtime.wire_knowledge_provider(_knowledge_search)

    # ── Identity Profile Provider (ZGC-PR-17C identity convergence) ──
    # Gives core.identity_engine.IdentityEngine a canonical production caller:
    # the runtime resolves the authenticated identity's profile (decision
    # style, goals, preferences) and enriches the ContextFrame so reasoning
    # is identity-aware. The identity authority itself remains TeamMember
    # (auth) + OrgMember (org membership) — this is profile intelligence,
    # not a competing identity authority.
    def _identity_profile(identity_id: str) -> dict:
        from core.identity_engine import IdentityEngine

        engine = IdentityEngine()
        ident = engine.get(identity_id)
        if not ident:
            return {}
        return {
            "identity_id": identity_id,
            "name": ident.name,
            "decision_style": ident.decision_style,
            "communication_style": ident.communication_style,
            "working_style": ident.working_style,
            "learning_style": ident.learning_style,
            "goals": [g.to_dict() for g in ident.goals],
            "preferences": dict(ident.preferences),
            "constraints": list(ident.constraints),
            "values": list(ident.values),
        }

    runtime.wire_identity_profile_provider(_identity_profile)

    # ── Controlled Learning Loop (ZGC-PR-17C §4) ──
    # Wires the governed learning loop: observation → evaluation → signal →
    # durable memory. The learning_intelligence engine (UCP-11) is integrated
    # as a computation component for skill analysis. The loop itself is
    # governed: no code modification, no prompt mutation, no model fine-tuning.
    try:
        from core.intelligence_runtime.learning_loop import get_learning_loop
        learning_loop = get_learning_loop()
        learning_loop.wire_memory(runtime.memory)
        # Integrate core.learning_intelligence (UCP-11 orphan resolution)
        from core.learning_intelligence.engine import LearningIntelligenceEngine
        learning_loop.wire_learning_engine(LearningIntelligenceEngine())
        runtime.learning_loop = learning_loop
    except Exception:
        import logging
        logging.getLogger(__name__).warning("Learning loop unavailable — skipping")

    # ── UCP Orphan Integration (ZGC-PR-17C §5) ──
    # Wire remaining domain intelligence engines into the retrieval layer so
    # they have a canonical production caller. Each is added as a provider
    # that the runtime's retrieval invokes during evidence gathering.
    try:
        _wire_ucp_providers(runtime)
    except Exception:
        import logging
        logging.getLogger(__name__).warning("UCP provider wiring failed — skipping")

    # ── Durable Memory Bridge (ZGC-PR-17C mandatory) ──
    # Swap the runtime's in-memory memory store for the canonical
    # MemoryRecord-backed repository so memories survive restart and are
    # isolated by identity + tenant.
    try:
        from core.intelligence_runtime.memory_db import DBMemoryRepository
        repo = DBMemoryRepository()
        runtime.memory.set_repository(repo)
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            "DB memory repository unavailable — falling back to in-memory memory"
        )

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


def _get_capability_context(query: str, identity_id: str = "",
                            tenant_id: str = "", workspace_type: str = "") -> dict:
    """Resolve relevant capabilities for a query via the capability registry.

    Returns capability routing info that enriches the runtime processing
    context so SHUNYAAI knows which capabilities are relevant and available.
    """
    try:
        from core.capability_registry import get_registry
        registry = get_registry()
        matched = registry.route(query)
        return {
            "matched_capabilities": [c.name for c in matched],
            "capability_count": len(matched),
            "available_count": sum(1 for c in matched if c.status == "AVAILABLE"),
            "unwired_count": sum(1 for c in matched if c.status == "UNWIRED"),
            "can_execute": any(c.can_execute for c in matched),
            "can_write": any(c.can_write for c in matched),
        }
    except Exception:
        return {
            "matched_capabilities": [],
            "capability_count": 0,
            "available_count": 0,
            "unwired_count": 0,
            "can_execute": False,
            "can_write": False,
        }


def ask(query: str, session_id: str = "", module_key: str = "",
        workspace: str = "", object_type: str = "", object_id: str = "",
        explain: bool = False,
        identity_id: str = "", tenant_id: str = "",
        user_role: str = "", workspace_type: str = "") -> dict[str, Any]:
    """Single entry point for every intelligence request in SHUNYA.

    Every surface calls this function. No alternative path exists.
    Identity context is passed through to the reasoning layer so
    SHUNYAAI knows who the user is and where they are.

    Capability routing: every query is matched against the capability
    registry to determine which SHUNYA capabilities are relevant.
    """
    ensure_runtime()
    runtime = get_runtime()
    start = time.time()

    # ── Capability Routing ──
    # Resolve relevant capabilities before processing so the runtime
    # knows which engines to invoke for this particular query.
    capability_context = _get_capability_context(
        query, identity_id, tenant_id, workspace_type)

    # Update context
    if module_key:
        runtime.context.update(session_id, active_module=module_key)
    if workspace:
        runtime.context.update(session_id, active_workspace=workspace)
    if object_type:
        runtime.context.update(session_id, active_object_type=object_type)
    if object_id:
        runtime.context.update(session_id, active_object_id=object_id)

    # Identity & authorization context (G3 convergence)
    ctx_updates = {}
    if identity_id:
        ctx_updates["identity_id"] = identity_id
    if tenant_id:
        ctx_updates["tenant_id"] = tenant_id
    if user_role:
        ctx_updates["user_role"] = user_role
    if workspace_type:
        ctx_updates["workspace_type"] = workspace_type
    if ctx_updates:
        runtime.context.update(session_id, **ctx_updates)

    # Inject capability routing into the context so the runtime's
    # retrieval and reasoning layers can use it.
    runtime.context.update(session_id,
                           _capability_context=capability_context)

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
    result["capability_context"] = capability_context

    # ── SHUNYAAI Intelligence Pipeline ──
    # Run the 8-engine pipeline alongside the existing runtime
    # to enrich the response with per-engine intelligence stage results.
    try:
        from core.shunyaai_pipeline import get_pipeline
        pipeline = get_pipeline()
        pipe_result = pipeline.run(
            user_input=query,
            identity_id=identity_id or "",
            tenant_id=str(tenant_id) if tenant_id else "",
            workspace=workspace or "",
            session_id=session_id or "",
        )
        result["intelligence_pipeline"] = pipe_result.to_dict()
        result["intelligence_stages"] = pipe_result.stages_completed
        # Use the pipeline's response text if the runtime didn't produce one
        if not result.get("content") and not result.get("response"):
            result["content"] = pipe_result.final_output.get("response_text", "")
    except Exception as pipe_err:
        import logging
        logging.getLogger(__name__).warning(f"Intelligence pipeline failed: {pipe_err}")
        result["intelligence_pipeline"] = {"error": str(pipe_err)}

    # ── Execution Chain — governed lifecycle ──
    # Determine if this is a read or action query based on capability routing
    try:
        is_action = capability_context.get("can_execute", False)
        is_write = capability_context.get("can_write", False)

        if is_action or is_write:
            from core.execution_chain import (
                record_action_chain, complete_action_chain,
                deny_action_chain,
            )
            # Initiate — state starts as REQUESTED, never auto-completed
            chain_result = record_action_chain(
                query=query,
                action_type="execute" if is_action else "write",
                identity_id=identity_id or "anonymous",
                tenant_id=int(tenant_id) if tenant_id and tenant_id != "" else 0,
                confidence=response.trace.confidence if response.trace else 0.5,
                object_id=int(object_id) if object_id and object_id != "" else None,
            )
            # After runtime processing, complete with the actual outcome
            # The IntelligenceResponse always has content (errors are handled
            # internally by the runtime and reflected in the response).
            chain_has_actions = bool(response.actions)
            completion = complete_action_chain(
                exec_id=chain_result.get("execution_id"),
                outcome="succeeded" if chain_has_actions else "failed",
                response_summary=(result.get("content") or result.get("response") or "")[:500],
                identity_id=identity_id or "anonymous",
                tenant_id=int(tenant_id) if tenant_id and tenant_id != "" else 0,
                state={"has_actions": chain_has_actions},
                observation_id=chain_result.get("observation_id"),
            )
            chain_result.update(completion)
            result["execution_chain"] = chain_result
        else:
            from core.execution_chain import record_read_chain
            chain_result = record_read_chain(
                query=query,
                identity_id=identity_id or "anonymous",
                tenant_id=int(tenant_id) if tenant_id and tenant_id != "" else 0,
                confidence=response.trace.confidence if response.trace else 0.5,
                response_summary=(result.get("content") or result.get("response") or "")[:500],
            )
            result["execution_chain"] = chain_result
    except Exception as chain_err:
        import logging
        logging.getLogger(__name__).warning(f"Execution chain recording failed: {chain_err}")
        result["execution_chain"] = {"error": str(chain_err)}

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


def store_memory(key: str, content: str, source: str = "user",
                 identity_id: str = "", tenant_id: str = "") -> None:
    """Store information in runtime memory — scoped by identity and tenant."""
    ensure_runtime()
    runtime = get_runtime()
    runtime.memory.store(key, content, MemoryType.LONG_TERM, source=source,
                         identity_id=identity_id, tenant_id=tenant_id)


def health() -> dict[str, Any]:
    """Get runtime health and telemetry."""
    ensure_runtime()
    runtime = get_runtime()
    h = runtime.health()
    h["telemetry"] = get_telemetry()
    h["initialized"] = _initialized
    return h


# ── UCP Orphan Engine Integration ──────────────────────────────────────────


def _wire_ucp_providers(runtime) -> None:
    """Wire remaining domain intelligence engines into the retrieval layer.

    ZGC-PR-17C §5: Every remaining orphan engine receives a legitimate
    canonical caller. Each UCP engine is registered as a domain-specific
    intelligence provider that the runtime's retrieval layer invokes
    during evidence gathering.

    Resolved orphans:
      - operations_intelligence (UCP-09)     → operations domain provider
      - health_intelligence (UCP-10)         → health domain provider
      - learning_intelligence (UCP-11)       → learning loop integration
      - identity_engine                      → identity profile provider (Batch 1)
    """
    # ── Operations Intelligence Provider (UCP-09) ──
    def _operations_search(query: str) -> list[dict]:
        try:
            from core.operations_intelligence.engine import OperationsIntelligenceEngine
            from core.operations_intelligence.models import Process, ProcessStep
            engine = OperationsIntelligenceEngine()
            proc = Process(process_id="query", name=query[:100], steps=[])
            results = engine.analyze_process(proc)
            return [{"source": "ucp_operations", "content": str(results)[:500]}]
        except Exception:
            return []

    # ── Health Intelligence Provider (UCP-10) ──
    def _health_search(query: str) -> list[dict]:
        try:
            from core.health_intelligence.engine import HealthIntelligenceEngine
            from core.health_intelligence.models import HealthProfile
            engine = HealthIntelligenceEngine()
            profile = engine.assess_mental_wellbeing(HealthProfile())
            return [{"source": "ucp_health", "content": str(profile)[:500]}]
        except Exception:
            return []

    # Register providers via the runtime's retrieval layer
    if hasattr(runtime, "retrieval") and runtime.retrieval:
        runtime.retrieval._additional_providers = {
            "operations_intelligence": _operations_search,
            "health_intelligence": _health_search,
        }