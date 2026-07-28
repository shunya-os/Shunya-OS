"""
SHUNYA Intelligence Layer — Engine Registry

All intelligence engines are registered here and discovered by the
RuntimeKernel. Each engine implements the Engine ABC from core/runtime.
"""

from __future__ import annotations

from typing import Dict, List, Type

from core.runtime.models import Engine

# Import all engine classes
from intelligence.observation.engine import ObservationEngine
from intelligence.knowledge.engine import KnowledgeEngine
from intelligence.reasoning.engine import ReasoningEngine
from intelligence.planning.engine import PlanningEngine
from intelligence.governance.engine import GovernanceEngine
from intelligence.execution.engine import ExecutionEngine
from intelligence.decisions.engine import DecisionsEngine
from intelligence.learning.engine import LearningEngine
from intelligence.memory.engine import MemoryEngine
from intelligence.temporal.engine import TemporalEngine
from intelligence.prediction.engine import PredictionEngine
from intelligence.context.engine import ContextEngine

# Registry: engine_id -> engine class
ENGINE_REGISTRY: Dict[str, Type[Engine]] = {
    "observation": ObservationEngine,
    "knowledge": KnowledgeEngine,
    "reasoning": ReasoningEngine,
    "planning": PlanningEngine,
    "governance": GovernanceEngine,
    "execution": ExecutionEngine,
    "decisions": DecisionsEngine,
    "learning": LearningEngine,
    "memory": MemoryEngine,
    "temporal": TemporalEngine,
    "prediction": PredictionEngine,
    "context": ContextEngine,
}

# Ordered startup sequence (dependency order)
ENGINE_STARTUP_ORDER: List[str] = [
    "memory",       # Foundation: memory must be available first
    "observation",  # Input: observations feed the intelligence loop
    "knowledge",    # Resolution: knowledge depends on memory + observations
    "context",      # Fusion: context depends on knowledge
    "reasoning",    # Reasoning depends on context
    "planning",     # Planning depends on reasoning
    "prediction",   # Prediction depends on planning + reasoning
    "temporal",     # Temporal depends on everything that creates timelines
    "governance",   # Governance runs after reasoning, before decisions
    "decisions",    # Decisions depend on reasoning + planning + governance
    "execution",    # Execution depends on decisions
    "learning",     # Learning depends on execution outcomes
]


def get_engine_classes() -> List[Type[Engine]]:
    """Return all engine classes in startup order."""
    return [ENGINE_REGISTRY[name] for name in ENGINE_STARTUP_ORDER]


def get_engine_class(engine_id: str) -> Type[Engine]:
    """Return a specific engine class by ID."""
    if engine_id not in ENGINE_REGISTRY:
        raise KeyError(
            f"Unknown engine '{engine_id}'. "
            f"Available: {', '.join(sorted(ENGINE_REGISTRY))}"
        )
    return ENGINE_REGISTRY[engine_id]


__all__ = [
    "ENGINE_REGISTRY",
    "ENGINE_STARTUP_ORDER",
    "get_engine_classes",
    "get_engine_class",
    "ObservationEngine",
    "KnowledgeEngine",
    "ReasoningEngine",
    "PlanningEngine",
    "GovernanceEngine",
    "ExecutionEngine",
    "DecisionsEngine",
    "LearningEngine",
    "MemoryEngine",
    "TemporalEngine",
    "PredictionEngine",
    "ContextEngine",
]