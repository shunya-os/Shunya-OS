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
    IntelligenceResponse,
    MemoryType,
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

    # ── Processing Pipeline ──────────────────────────────────────────────

    def process(self, user_input: str, session_id: str = "",
                module_key: str = "", **context_kw: Any) -> IntelligenceResponse:
        """Full processing pipeline: intent → context → retrieval → reason → respond."""
        # 1. Classify intent
        intent = self.intent.classify(user_input, context_kw.get("workspace", ""))

        # 2. Update context
        ctx = self.context.update(session_id, **context_kw)
        self.context.push_history(session_id, user_input)

        # 3. Store in short-term memory
        self.memory.store(
            key=f"query_{len(self.memory.recall_recent())}",
            content=user_input,
            memory_type=MemoryType.SHORT_TERM,
            source="user",
            confidence=intent.confidence,
            ttl_seconds=3600,
        )

        # 4. Retrieve evidence
        evidence = self.retrieval.retrieve(user_input, module_key=module_key)

        # 5. Reason over evidence
        response = self.reasoning.reason(intent, ctx, evidence)

        # 6. Plan actions
        plan = self.planner.decide(intent, response)

        # 7. Execute actions
        results = self.executor.execute_all(plan)

        # 8. Store response in memory
        self.memory.store(
            key=f"response_{len(self.memory.recall_recent())}",
            content=response.content,
            memory_type=MemoryType.SHORT_TERM,
            source="runtime",
            confidence=response.trace.confidence if response.trace else 0.5,
            ttl_seconds=3600,
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
        """Wire DB persistence for conversation survival across restarts."""
        self.conversation.set_persistence_provider(save_fn, load_fn)

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
    global _INSTANCE
    if _INSTANCE:
        _INSTANCE.reset()
    _INSTANCE = None