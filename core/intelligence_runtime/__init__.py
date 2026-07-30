"""Universal Intelligence Runtime — kernel service for all SHUNYA interactions.

Import the runtime singleton and use it directly:
    from core.intelligence_runtime import get_runtime
    runtime = get_runtime()
    response = runtime.process("What are my open invoices?", session_id="abc", module_key="travel")
"""

from .runtime import IntelligenceRuntime, get_runtime, reset_runtime
from .types import (
    ActionType, IntentCategory, IntelligenceResponse, MemoryType,
    PlanStep, ReasoningStrategy, ReasoningTrace, UniversalSuggestion, UrgencyLevel,
    UserIntent,
)

__all__ = [
    "get_runtime", "reset_runtime", "IntelligenceRuntime",
    "IntelligenceResponse", "UserIntent", "PlanStep", "ReasoningTrace",
    "UniversalSuggestion",
    "IntentCategory", "UrgencyLevel", "ReasoningStrategy", "ActionType", "MemoryType",
]