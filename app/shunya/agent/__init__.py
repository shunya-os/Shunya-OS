"""Shunya Personal Agent — Core Loop.

The think-act-observe loop that powers every user's personal agent.
"""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json, uuid, time, logging
from flask import g

from app.shunya.agent.tools import get_registry, ToolResult, SafeTool
from app.shunya.agent.user import ProfileStore, UserProfile, CorrectionEngine
from app.shunya.agent.search import DualSourceMerger, SourceDecisionTree, DualSourceResult

logger = logging.getLogger("app.shunya.agent.loop")


# ---------------------------------------------------------------------------
# Personality Engine
# ---------------------------------------------------------------------------

PERSONAS = {
    "assistant": {
        "tone": "neutral, efficient, minimal. Get the job done.",
        "phrases": ["Done.", "Here you go.", "What's next?", "Got it.", "Here's what I found:"],
    },
    "friend": {
        "tone": "warm, remembers personal context, casual. Like a trusted colleague.",
        "phrases": ["Hey! Here's what I've got.", "Quick update for you —", "I took care of that."],
    },
    "coach": {
        "tone": "encouraging, asks questions back, teaches as it answers.",
        "phrases": ["Great question!", "Here's what I'd recommend...", "Let me suggest an approach..."],
    },
    "guardian": {
        "tone": "protective, flags risks proactively, cautious but helpful.",
        "phrases": ["Heads up —", "I'd recommend a second look.", "Flagging this for your attention."],
    },
}

PERSONA_NAMES = list(PERSONAS.keys())


class PersonalityEngine:
    """Determines the agent's tone and style per user."""

    @staticmethod
    def get_persona(profile: UserProfile) -> dict:
        base = profile.preferred_persona
        if base not in PERSONAS:
            if profile.trust_score >= 0.7:
                base = "friend"
            elif profile.role == "admin":
                base = "guardian"
            else:
                base = "assistant"
        return PERSONAS.get(base, PERSONAS["assistant"])

    @staticmethod
    def adjust_persona(profile: UserProfile) -> str:
        """Dynamically adjust persona based on trust and relationship."""
        if profile.correction_count > 5:
            return "assistant"  # Be more careful with users who correct often
        if profile.trust_score >= 0.8 and profile.session_count > 10:
            return "friend"  # High trust, long relationship
        if profile.role == "admin":
            return "guardian"
        return profile.preferred_persona


# ---------------------------------------------------------------------------
# Clarification Protocol
# ---------------------------------------------------------------------------

class ClarificationProtocol:
    """Handles uncertainty gracefully."""

    CONFIDENCE_HIGH = 0.9    # Execute
    CONFIDENCE_MEDIUM = 0.7  # Propose with confirmation
    CONFIDENCE_LOW = 0.4     # Ask clarifying question

    @staticmethod
    def handle_intent(intent: dict, confidence: float) -> dict:
        """Return the action to take based on confidence."""
        if confidence >= ClarificationProtocol.CONFIDENCE_HIGH:
            return {"action": "execute", "intent": intent}
        elif confidence >= ClarificationProtocol.CONFIDENCE_MEDIUM:
            return {
                "action": "propose",
                "intent": intent,
                "question": f"I think you want to {intent.get('description', 'do this')}. Shall I proceed?",
            }
        elif confidence >= ClarificationProtocol.CONFIDENCE_LOW:
            return {
                "action": "clarify",
                "intent": intent,
                "question": f"Did you mean to {intent.get('description', 'do this')}, or something else?",
            }
        else:
            return {
                "action": "fallback",
                "question": "I'm not sure what you need. I can create records, search your data, search the web, or generate reports. What would you like?",
            }


# ---------------------------------------------------------------------------
# Context Manager
# ---------------------------------------------------------------------------

@dataclass
class Turn:
    query: str
    response: str
    intent: dict
    tools_called: list = field(default_factory=list)  # list[ToolCallTrace]
    confidence: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_correction: bool = False


class ContextManager:
    """Manages conversation history with intelligent compression."""

    MAX_TURNS = 30
    COMPRESS_AT = 20

    def __init__(self, user_id: int, tenant_id: int):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.turns: list[Turn] = []
        self.summary: str = ""

    def add_turn(self, turn: Turn):
        self.turns.append(turn)
        if len(self.turns) > self.MAX_TURNS:
            self._compress()

    def get_recent(self, n: int = 5) -> list[Turn]:
        return self.turns[-n:]

    def build_context(self, profile: UserProfile, correction_context: str = "") -> str:
        """Build context string for LLM injection."""
        parts = []

        # User profile
        parts.append(profile.to_prompt())

        # Summary of older conversation
        if self.summary:
            parts.append(f"Earlier conversation summary: {self.summary}")

        # Recent turns (last 3)
        recent = self.get_recent(3)
        if recent:
            turns_text = []
            for t in recent:
                label = "CORRECTION" if t.is_correction else "TURN"
                turns_text.append(f"{label}: user='{t.query}' → agent: {t.response[:100]}")
            parts.append("Recent: " + " | ".join(turns_text))

        # Corrections
        if correction_context:
            parts.append(correction_context)

        return "\n".join(parts)

    def _compress(self):
        """Summarize older turns."""
        old = self.turns[:-10]
        if not old:
            return
        summaries = [f"{'C:' if t.is_correction else 'Q:'} {t.query[:50]}" for t in old]
        self.summary = "; ".join(summaries[-5:])
        self.turns = self.turns[-10:]

    def to_dict(self) -> dict:
        return {
            "turn_count": len(self.turns),
            "summary": self.summary,
            "recent": [{"query": t.query, "timestamp": t.timestamp} for t in self.get_recent(3)],
        }


# ---------------------------------------------------------------------------
# Agent Trace (Observability)
# ---------------------------------------------------------------------------

@dataclass
class ToolCallTrace:
    tool: str
    params: dict
    result: dict
    duration_ms: int
    error: str = ""


@dataclass
class AgentTrace:
    turn_id: str
    user_id: int
    tenant_id: int
    channel: str
    query: str
    domain: str
    intent: dict
    confidence: float
    tool_calls: list[ToolCallTrace] = field(default_factory=list)
    tokens_used: int = 0
    latency_ms: int = 0
    corrections: list[str] = field(default_factory=list)
    verification_badge: str = ""
    response: str = ""
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def complete(self, response: str):
        self.response = response
        self.latency_ms = int((datetime.utcnow() - datetime.fromisoformat(self.started_at)).total_seconds() * 1000)

    def to_dict(self) -> dict:
        return asdict(self)


class TraceStore:
    """Stores agent traces for observability."""

    def __init__(self):
        self._traces: list[AgentTrace] = []

    def add(self, trace: AgentTrace):
        self._traces.append(trace)
        # Keep last 1000 in memory
        if len(self._traces) > 1000:
            self._traces = self._traces[-1000:]

    def get_recent(self, limit: int = 20) -> list[dict]:
        return [t.to_dict() for t in self._traces[-limit:]]

    def get_by_user(self, user_id: int, limit: int = 10) -> list[dict]:
        return [t.to_dict() for t in self._traces if t.user_id == user_id][-limit:]


_trace_store = TraceStore()


def get_trace_store() -> TraceStore:
    return _trace_store


# ---------------------------------------------------------------------------
# Intent Detection (simple keyword-based for now — LLM-powered in future)
# ---------------------------------------------------------------------------

class IntentDetector:
    """Detects user intent from query text."""

    CREATE_KW = ["create", "add", "new", "make", "register", "record", "track", "log"]
    LIST_KW = ["show", "list", "display", "view", "find", "my", "all"]
    UPDATE_KW = ["update", "change", "edit", "modify", "set", "mark"]
    DELETE_KW = ["delete", "remove", "archive", "trash"]
    SEARCH_KW = ["search", "find", "look up", "tell me"]
    SEND_KW = ["send", "message", "notify", "email", "whatsapp"]
    REPORT_KW = ["report", "analytics", "dashboard", "revenue", "overview"]

    def detect(self, query: str) -> dict:
        q = query.lower().strip()

        # Question patterns (must be checked before search)
        if q.startswith(("what is", "what are", "what's", "how do", "how does", "why", "when", "can you", "tell me about")):
            return {"type": "question", "description": "answer a question"}
        if q.startswith("what") and " " in q:
            return {"type": "question", "description": "answer a question"}

        if any(q.startswith(k) for k in ["show", "list", "display", "view", "find"]):
            return {"type": "list", "description": "list records"}
        if any(q.startswith(k) for k in ["create", "add", "new", "make", "register", "track", "log"]):
            return {"type": "create", "description": "create a record"}
        if any(q.startswith(k) for k in ["update", "change", "edit", "modify"]):
            return {"type": "update", "description": "update a record"}
        if any(k in q for k in ["send", "message", "notify"]):
            return {"type": "send", "description": "send a message"}
        if any(k in q for k in ["report", "analytics", "revenue"]):
            return {"type": "report", "description": "generate a report"}
        if any(q.startswith(k) for k in ["search", "look up"]):
            return {"type": "search", "description": "search for information"}
        if any(k in q for k in ["delete", "remove", "archive"]):
            return {"type": "delete", "description": "delete a record"}

        return {"type": "question", "description": "answer a question"}


# ---------------------------------------------------------------------------
# Agent Loop — The Core
# ---------------------------------------------------------------------------

class AgentLoop:
    """The think-act-observe loop. Every user's personal agent."""

    def __init__(self, user_id: int, tenant_id: int, channel: str = "web"):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.channel = channel

        # Load profile
        self.profile = ProfileStore.load(user_id, tenant_id)
        self.profile.session_count += 1
        ProfileStore.save(self.profile)

        # Init context
        self.context = ContextManager(user_id, tenant_id)
        self.personality = PersonalityEngine.get_persona(self.profile)
        self.tools = get_registry()
        self.merger = DualSourceMerger()
        self.intent = IntentDetector()

    def process(self, query: str) -> dict:
        """Process a query through the agent loop."""
        trace = AgentTrace(
            turn_id=uuid.uuid4().hex[:12],
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            channel=self.channel,
            query=query,
            domain="",
            intent={},
            confidence=0,
        )

        try:
            # 1. THINK — Classify intent
            intent = self.intent.detect(query)
            trace.intent = intent
            trace.domain = SourceDecisionTree.classify(query)

            # 2. THINK — Build context
            correction_ctx = CorrectionEngine.get_correction_context(self.user_id, self.tenant_id)
            ctx = self.context.build_context(self.profile, correction_ctx)
            _ = ctx  # Available for LLM integration

            result = None

            # 3. PICK TOOL + EXECUTE
            if intent["type"] in ("create", "list", "update", "send", "report"):
                result = self._handle_tool_intent(intent, query, trace)
            else:
                # 4. SEARCH (internal + web)
                result = self._handle_search(query, trace)

            # 5. OBSERVE — Process result
            response_text, badge = self._format_response(result, intent)

            # 6. LEARN — Store turn
            turn = Turn(query=query, response=response_text, intent=intent,
                        tools_called=trace.tool_calls, confidence=trace.confidence)
            self.context.add_turn(turn)

            # Complete trace
            trace.verification_badge = badge
            trace.complete(response_text)
            get_trace_store().add(trace)

            return {
                "response": response_text,
                "intent": intent,
                "domain": trace.domain,
                "confidence": trace.confidence,
                "verification_badge": badge,
                "tool_calls": [{"tool": tc.tool, "duration_ms": tc.duration_ms} for tc in trace.tool_calls],
                "profile": self.profile.to_dict(),
            }

        except Exception as e:
            logger.error("Agent loop error: %s", e, exc_info=True)
            return {
                "response": "I hit an unexpected error. Let me try again — what were you looking for?",
                "intent": {"type": "error"},
                "domain": "unknown",
                "confidence": 0,
                "verification_badge": "low_confidence",
                "tool_calls": [],
                "profile": self.profile.to_dict(),
            }

    def _handle_tool_intent(self, intent: dict, query: str, trace: AgentTrace) -> dict:
        """Handle tool-based intents (create, list, update, etc.)."""
        keywords = query.lower().split()

        # Find matching tools
        tool_names = self.tools.find_tools(intent["type"], keywords)
        if not tool_names:
            return self._handle_search(query, trace)

        tool = self.tools.get(tool_names[0])
        if not tool:
            return self._handle_search(query, trace)

        # Extract params (simple extraction)
        params = self._extract_params(tool, query)

        # Execute
        t0 = time.time()
        result = tool.execute(params, self.profile.role)
        duration = int((time.time() - t0) * 1000)

        trace.tool_calls.append(ToolCallTrace(
            tool=tool.spec.name, params=params,
            result=asdict(result) if hasattr(result, '__dataclass_fields__') else {"success": result.success},
            duration_ms=duration,
        ))

        trace.confidence = 0.85 if result.success else 0.4

        return {
            "type": "tool_result",
            "success": result.success,
            "data": result.data,
            "message": result.message,
            "suggested_fix": result.suggested_fix,
        }

    def _handle_search(self, query: str, trace: AgentTrace) -> dict:
        """Handle search-based intents (questions, search, ambiguous)."""
        # Use DualSourceMerger for comprehensive search
        search_result = self.merger.answer(query, self.tenant_id, self.user_id)
        trace.confidence = search_result.confidence

        return {
            "type": "search_result",
            "success": search_result.badge != "not_found",
            "answer": search_result.answer,
            "badge": search_result.badge,
            "needs_verification": search_result.needs_verification,
            "verification_reason": search_result.verification_reason,
            "is_cached": search_result.is_cached,
        }

    def _extract_params(self, tool: SafeTool, query: str) -> dict:
        """Extract tool parameters from the query string."""
        params = {}
        for p in tool.spec.parameters:
            if p.name == "query":
                params["query"] = query  # Search tools take the full query
            elif p.name == "limit":
                params["limit"] = 20
            elif p.name == "entity_type":
                # Try to extract entity type from query
                from app.models import EntityDefinition
                q = query.lower()
                defs = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, is_active=True).all()
                for d in defs:
                    if d.type in q or d.label.lower() in q:
                        params["entity_type"] = d.type
                        break
                if "entity_type" not in params:
                    params["entity_type"] = ""
            elif p.name == "depth":
                params["depth"] = "normal"
            elif p.name == "status":
                params["status"] = ""
        return params

    def _format_response(self, result: dict, intent: dict) -> tuple[str, str]:
        """Format the agent's response."""
        rtype = result.get("type", "")

        if rtype == "tool_result":
            if result["success"]:
                data = result.get("data", {})
                if "code" in data:
                    return (f"✅ **{data.get('label', 'Record')} created** ({data.get('code', '')})\n\n"
                            f"View it here → [{data.get('type', 'record')}/{data.get('id', '')}]"
                            f"(/entities/{data.get('type', '')}/{data.get('id', '')})", "verified")
                if "count" in data:
                    count = data.get("count", 0)
                    return (f"Found **{count}** records.\n"
                            f"{self.personality.get('phrases', ['Here you go.'])[0]}", "company")
                return ("Done. " + self.personality.get('phrases', [''])[0], "verified")
            else:
                fix = result.get("suggested_fix", {})
                if fix and fix.get("action") == "ask_user":
                    return (result.get("message", "I need more info.") + f"\n\n{fix.get('question', '')}", "low_confidence")
                if fix and fix.get("action") == "queue_for_approval":
                    return ("This needs higher permissions. I've noted it for review.", "low_confidence")
                return (result.get("message", "I couldn't complete that. Let me try a different approach."), "low_confidence")

        if rtype == "search_result":
            return (result.get("answer", ""), result.get("badge", "company"))

        # Fallback
        return ("Here's what I found.", "company")