"""Universal Intelligence Runtime — the cognitive kernel of SHUNYA.

Every interaction across every surface passes through this runtime.
It consumes the Business Graph and UBME object model exclusively.
No business-specific logic exists here.

Architecture:
    User Input → Intent Engine → Context Engine → Retrieval Layer
        → Reasoning Engine → Action Planner → Tool Execution
        → Response (explained + suggestioned)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .context import ContextEngine
from .conversation import ConversationRuntime
from .execution import ToolExecutionLayer
from .explain import ExplainabilityEngine
from .intent import IntentEngine
from .memory import MemoryEngine
from .planner import ActionPlanner
from .reasoning import ReasoningEngine
from .retrieval import RetrievalLayer
from .suggestions import SuggestionsEngine
from .types import (
    ActionType,
    IntelligenceResponse,
    MemoryType,
    PlanStep,
    UniversalSuggestion,
)

# Singleton
_INSTANCE: IntelligenceRuntime | None = None


class IntelligenceRuntime:
    """The single Intelligence Runtime powering every SHUNYA interaction."""

    def __init__(self):
        self.intent = IntentEngine()
        self.context = ContextEngine()
        self.memory = MemoryEngine()
        self.retrieval = RetrievalLayer()
        self.reasoning = ReasoningEngine()
        self.planner = ActionPlanner()
        self.executor = ToolExecutionLayer()
        self.conversation = ConversationRuntime()
        self.suggestions = SuggestionsEngine()
        self.explain = ExplainabilityEngine()
        self._identity_profile_provider: Callable | None = None
        self.learning_loop = None

    # ── Processing Pipeline ──────────────────────────────────────────────

    def process(self, user_input: str, session_id: str = "",
                module_key: str = "", **context_kw: Any) -> IntelligenceResponse:
        """Full processing pipeline: intent → context → retrieval → reason → respond."""
        # 1. Classify intent
        intent = self.intent.classify(user_input, context_kw.get("workspace", ""))

        # 2. Update context
        ctx = self.context.update(session_id, **context_kw)
        self.context.push_history(session_id, user_input)

        # Identity & tenant scoping — every memory write is owned by the
        # authenticated identity inside its workspace/tenant (identity convergence).
        scope_identity = getattr(ctx, "identity_id", "") or context_kw.get("identity_id", "")
        scope_tenant = getattr(ctx, "tenant_id", "") or context_kw.get("tenant_id", "")

        # Identity profile enrichment — when an identity profile provider is
        # wired, the context frame carries the decision/communication style,
        # goals, and preferences of the authenticated identity so reasoning
        # is identity-aware (source: core.identity_engine.IdentityEngine).
        if scope_identity and self._identity_profile_provider:
            try:
                profile = self._identity_profile_provider(scope_identity)
                if profile:
                    self.context.update(session_id, identity_profile=profile)
            except Exception:
                import logging
                logging.getLogger(__name__).warning(
                    "Identity profile provider failed for %s", scope_identity
                )

        # 3. Store in short-term memory
        self.memory.store(
            key=f"query_{len(self.memory.recall_recent(identity_id=scope_identity, tenant_id=scope_tenant))}",
            content=user_input,
            memory_type=MemoryType.SHORT_TERM,
            source="user",
            confidence=intent.confidence,
            ttl_seconds=3600,
            identity_id=scope_identity,
            tenant_id=scope_tenant,
        )

        # 4. Retrieve evidence
        evidence = self.retrieval.retrieve(user_input, module_key=module_key)

        # 5. Reason over evidence
        response = self.reasoning.reason(intent, ctx, evidence)

        # 6. Plan actions
        plan = self.planner.decide(intent, response)

        # 6a. Business-action confirmation gate (E4). Create-requests carry the
        # authenticated organization and identity scope; unless the user's
        # message explicitly confirmed, they become a truthful preview and
        # nothing executes (create-requests have real side effects).
        gated_plan: list[PlanStep] = []
        for step in plan:
            if step.action in (ActionType.CREATE_CUSTOMER, ActionType.CREATE_SUPPLIER):
                if scope_identity:
                    step.parameters.setdefault("_identity_id", scope_identity)
                if scope_tenant:
                    try:
                        step.parameters.setdefault("organization_id", int(scope_tenant))
                    except (TypeError, ValueError):
                        pass
                if not step.parameters.get("confirmed"):
                    response.content = step.parameters.get("preview", "")
                    # Nothing was executed: strip any reasoning-planned
                    # actions so the governed execution chain does NOT report
                    # a completed business action (ledger truth).
                    response.actions = []
                    # Replace the create-step with a no-op answer: an
                    # unconfirmed create-request MUST NOT execute.
                    gated_plan.append(
                        PlanStep(action=ActionType.ANSWER, description=step.description)
                    )
                    continue
            gated_plan.append(step)
        plan = gated_plan

        # 7. Execute actions
        results = self.executor.execute_all(plan)

        # 7a. A business action that actually ran replaces the (unrelated)
        # reasoning text with its truthful report.
        for r in results:
            if not isinstance(r, dict) or r.get("action") not in ("create_customer", "create_supplier"):
                continue
            kind = "customer" if r["action"] == "create_customer" else "supplier"
            if r.get("status") == "error":
                response.content = f"The {kind} could not be created: {r.get('error')}"
                continue
            inner = r.get("result") or {}
            if not isinstance(inner, dict):
                continue
            if inner.get("status") == "success":
                res = inner.get("result") or {}
                oid = res.get("customer_id") or res.get("supplier_id")
                response.content = (
                    f"Created {kind} \u201c{res.get('name', '')}\u201d (id {oid}). "
                    f"Recorded as outcome {inner.get('outcome_id')} and emitted to your event history."
                )
                # The action really ran: record it on the response so the
                # governed execution chain completes truthfully.
                try:
                    response.actions.append(PlanStep(
                        action=ActionType(r["action"]),
                        description=f"Created {kind} \u201c{res.get('name', '')}\u201d",
                        parameters={"object_id": oid, "outcome_id": inner.get("outcome_id")},
                    ))
                except ValueError:
                    pass
            elif inner.get("status") == "duplicate":
                res = inner.get("result") or {}
                oid = res.get("customer_id") or res.get("supplier_id")
                response.content = (
                    f"A {kind} named \u201c{res.get('name', '')}\u201d already exists (id {oid}) "
                    f"\u2014 nothing new was created."
                )
            elif inner.get("status") == "error":
                response.content = f"The {kind} was not created: {inner.get('error')}"

        # 8. Store response in memory
        self.memory.store(
            key=f"response_{len(self.memory.recall_recent(identity_id=scope_identity, tenant_id=scope_tenant))}",
            content=response.content,
            memory_type=MemoryType.SHORT_TERM,
            source="runtime",
            confidence=response.trace.confidence if response.trace else 0.5,
            ttl_seconds=3600,
            identity_id=scope_identity,
            tenant_id=scope_tenant,
        )

        # 9. Add to conversation
        self.conversation.add_message(session_id, "user", user_input, ctx)
        self.conversation.add_message(session_id, "assistant", response.content, ctx)

        return response

    # ── Wired Queries ────────────────────────────────────────────────────

    def ask(self, question: str, session_id: str = "", module_key: str = "") -> str:
        """Quick question → answer. Returns just the text."""
        response = self.process(question, session_id, module_key)
        return response.content

    def explain_last(self, session_id: str) -> dict[str, Any]:
        """Get explanation for the last response."""
        history = self.conversation.get_history(session_id, 2)
        return {"history": history, "note": "Full trace available on the last IntelligenceResponse object"}

    def get_suggestions(self, session_id: str) -> list[UniversalSuggestion]:
        """Get context-aware suggestions."""
        ctx = self.context.get(session_id)
        return self.suggestions.suggest(ctx)

    # ── Wiring ───────────────────────────────────────────────────────────

    def wire_graph_provider(self, fn: Callable) -> None:
        self.retrieval.set_graph_provider(fn)

    def wire_object_provider(self, fn: Callable) -> None:
        self.retrieval.set_object_provider(fn)

    def wire_internet_provider(self, fn: Callable) -> None:
        self.retrieval.set_internet_provider(fn)

    def wire_memory_provider(self, fn: Callable) -> None:
        self.retrieval.set_memory_provider(fn)

    def wire_llm_provider(self, fn: Callable) -> None:
        """Wire the LLM provider into the reasoning engine."""
        self.reasoning.wire_llm_provider(fn)

    def wire_conversation_persistence(self, save_fn: Callable, load_fn: Callable) -> None:
        """Wire a DB persistence provider for conversation history."""
        self.conversation.set_persistence_provider(save_fn, load_fn)

    def wire_knowledge_provider(self, fn: Callable) -> None:
        """Wire a knowledge search provider."""
        self.retrieval.set_knowledge_provider(fn)

    def wire_canonical_provider(self, fn: Callable) -> None:
        """Wire the canonical business-objects search provider (company data)."""
        self.retrieval.set_canonical_provider(fn)

    def wire_identity_profile_provider(self, fn: Callable) -> None:
        """Wire an identity profile provider (identity intelligence).

        The provider receives identity_id and returns a profile dict with
        decision_style, communication_style, goals, preferences, etc.
        The runtime enriches the ContextFrame with the profile so reasoning
        is identity-aware. Source: core.identity_engine.IdentityEngine.
        """
        self._identity_profile_provider = fn

    def wire_action(self, action_key: str, handler: Callable) -> None:
        self.executor.register(action_key, handler)

    # ── Lifecycle ────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset all state (testing)."""
        self.context.clear()
        self.memory.clear()
        self.retrieval.clear()
        self.conversation.clear()
        self.executor.clear()

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "memory_count": self.memory.count(),
            "active_sessions": len(self.context._frames),
            "intent_engine": "ready",
            "reasoning_engine": "ready",
        }


def get_runtime() -> IntelligenceRuntime:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = IntelligenceRuntime()
    return _INSTANCE


def reset_runtime() -> None:
    """Drop the singleton and clear its state.

    Also clears the integration wiring guard (``ensure_runtime()``) so the next
    ``get_runtime()`` can be fully re-wired. Without that, resetting the runtime
    would permanently strip its base action handlers and make behaviour depend
    on call order.
    """
    global _INSTANCE
    if _INSTANCE:
        _INSTANCE.reset()
    _INSTANCE = None
    try:
        from .integration import reset_runtime_wiring
        reset_runtime_wiring()
    except Exception:  # pragma: no cover — integration is always importable
        pass