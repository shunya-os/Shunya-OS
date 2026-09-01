"""Universal Intelligence Runtime — Types and Data Models.

Every interaction inside SHUNYA passes through this runtime.
It consumes the Business Graph and shared object model exclusively.
No business-specific logic lives here.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ── Enums ─────────────────────────────────────────────────────────────────


class IntentCategory(str, enum.Enum):
    QUESTION = "question"               # "What are my open invoices?"
    COMMAND = "command"                 # "Create a new customer"
    SEARCH = "search"                   # "Find bookings for Paris"
    EXPLAIN = "explain"                 # "Why did you recommend this?"
    SUGGEST = "suggest"                 # "What should I do next?"
    AUTOMATE = "automate"               # "Automate this process"
    NAVIGATE = "navigate"               # "Show me my dashboard"
    UNKNOWN = "unknown"                 # Unclear intent


class UrgencyLevel(str, enum.Enum):
    CRITICAL = "critical"               # Needs immediate action
    HIGH = "high"                       # Important, time-sensitive
    NORMAL = "normal"                   # Standard
    LOW = "low"                         # Can wait


class ReasoningStrategy(str, enum.Enum):
    DIRECT_ANSWER = "direct_answer"     # From known data
    BUSINESS_GRAPH = "business_graph"   # Traverse relationships
    MULTI_SOURCE = "multi_source"       # Combine multiple sources
    INTERNET = "internet"               # Needs external knowledge
    DEFER = "defer"                     # Can't answer, suggest escalation


class ActionType(str, enum.Enum):
    ANSWER = "answer"                   # Provide information
    CLARIFY = "clarify"                 # Ask a clarifying question
    EXECUTE = "execute"                 # Perform an action
    AUTOMATE = "automate"               # Set up automation
    DEFER = "defer"                     # Escalate to human
    ROUTE = "route"                     # Redirect to appropriate handler


class MemoryType(str, enum.Enum):
    SHORT_TERM = "short_term"           # Current conversation
    LONG_TERM = "long_term"             # User preferences, facts
    ORGANIZATION = "organization"       # Shared organizational knowledge
    BUSINESS = "business"              # Business-specific knowledge


# ── Core Data Types ───────────────────────────────────────────────────────


@dataclass
class UserIntent:
    """Classified user intent with confidence."""
    raw_input: str
    category: IntentCategory = IntentCategory.UNKNOWN
    urgency: UrgencyLevel = UrgencyLevel.NORMAL
    confidence: float = 0.0
    ambiguity: float = 0.0
    entities: list[dict] = field(default_factory=list)
    requested_outcome: str = ""

    def is_certain(self) -> bool:
        return self.confidence >= 0.7 and self.ambiguity < 0.3

    def to_dict(self) -> dict:
        return {
            "raw_input": self.raw_input,
            "category": self.category.value,
            "urgency": self.urgency.value,
            "confidence": round(self.confidence, 2),
            "ambiguity": round(self.ambiguity, 2),
            "entities": self.entities,
            "requested_outcome": self.requested_outcome,
        }


@dataclass
class ContextFrame:
    """Current context snapshot — what the user is doing and where."""
    active_workspace: str = ""
    active_object_type: str = ""
    active_object_id: str = ""
    active_module: str = ""
    conversation_id: str = ""
    recent_history: list[str] = field(default_factory=list)
    current_task: str = ""
    query_params: dict = field(default_factory=dict)
    # Identity & authorization context (G3 convergence)
    identity_id: str = ""
    tenant_id: str = ""
    user_role: str = ""
    workspace_type: str = ""  # "personal" or "organization"
    identity_profile: dict = field(default_factory=dict)  # Decision style, goals, preferences

    def to_dict(self) -> dict:
        return {
            "active_workspace": self.active_workspace,
            "active_object_type": self.active_object_type,
            "active_object_id": self.active_object_id,
            "active_module": self.active_module,
            "conversation_id": self.conversation_id,
            "recent_history": self.recent_history[-5:],
            "current_task": self.current_task,
            "identity_id": self.identity_id,
            "tenant_id": self.tenant_id,
            "user_role": self.user_role,
            "workspace_type": self.workspace_type,
        }


@dataclass
class MemoryEntry:
    """A single memory entry from any memory type."""
    key: str
    content: str
    memory_type: MemoryType = MemoryType.SHORT_TERM
    source: str = ""
    confidence: float = 1.0
    timestamp: str = ""
    ttl_seconds: int = 0  # 0 = permanent

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def is_expired(self) -> bool:
        if self.ttl_seconds <= 0:
            return False
        created = datetime.fromisoformat(self.timestamp)
        elapsed = (datetime.now(timezone.utc) - created).total_seconds()
        return elapsed > self.ttl_seconds

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "content": self.content,
            "type": self.memory_type.value,
            "source": self.source,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


@dataclass
class RetrievedEvidence:
    """A piece of evidence from any source used during reasoning."""
    source: str  # "business_graph", "object", "internet", "conversation", "memory"
    content: str
    relevance: float = 0.0
    confidence: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "content": self.content[:200],
            "relevance": round(self.relevance, 2),
            "confidence": round(self.confidence, 2),
            "metadata": self.metadata,
        }


@dataclass
class ReasoningStep:
    """A single step in the reasoning process."""
    step_type: str  # "gather", "analyze", "infer", "verify", "decide"
    description: str
    inputs: list[str] = field(default_factory=list)
    output: str = ""
    evidence: list[RetrievedEvidence] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "step_type": self.step_type,
            "description": self.description,
            "output": self.output[:200],
            "evidence": [e.to_dict() for e in self.evidence],
            "confidence": round(self.confidence, 2),
        }


@dataclass
class PlanStep:
    """A step in the action plan."""
    action: ActionType
    description: str
    parameters: dict = field(default_factory=dict)
    depends_on: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "action": self.action.value,
            "description": self.description,
            "parameters": self.parameters,
        }


@dataclass
class ReasoningTrace:
    """Full reasoning trace for explainability."""
    intent: UserIntent
    context: ContextFrame
    strategy: ReasoningStrategy
    steps: list[ReasoningStep] = field(default_factory=list)
    evidence: list[RetrievedEvidence] = field(default_factory=list)
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "intent": self.intent.to_dict(),
            "context": self.context.to_dict(),
            "strategy": self.strategy.value,
            "steps": [s.to_dict() for s in self.steps],
            "evidence": [e.to_dict() for e in self.evidence],
            "confidence": round(self.confidence, 2),
            "assumptions": self.assumptions,
            "alternatives": self.alternatives,
            "timestamp": self.timestamp,
        }


@dataclass
class IntelligenceResponse:
    """Final response from the Intelligence Runtime."""
    content: str
    actions: list[PlanStep] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    trace: ReasoningTrace | None = None
    requires_clarification: bool = False
    clarification_question: str = ""

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "actions": [a.to_dict() for a in self.actions],
            "suggestions": self.suggestions,
            "trace": self.trace.to_dict() if self.trace else None,
            "requires_clarification": self.requires_clarification,
            "clarification_question": self.clarification_question,
        }


@dataclass
class UniversalSuggestion:
    """A proactive suggestion from the runtime."""
    key: str
    title: str
    description: str
    suggestion_type: str  # automation, reminder, improvement, action
    confidence: float = 0.0
    context: ContextFrame | None = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "title": self.title,
            "description": self.description,
            "type": self.suggestion_type,
            "confidence": round(self.confidence, 2),
        }