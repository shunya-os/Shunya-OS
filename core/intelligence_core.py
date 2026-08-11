"""
SHUNYA — Intelligence Core (FDA6).

One canonical context assembly pathway.
Company-first, evidence-aware, confidence-aware, deterministic-first.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Truth Classification (G3)
# ═══════════════════════════════════════════════════════════════════

class TruthCategory(Enum):
    """Every meaningful intelligence result must distinguish truth category."""
    FACT = "fact"                       # Known from authoritative source
    MEMORY = "memory"                   # Previously learned contextual info
    INFERENCE = "inference"             # Derived by reasoning
    RECOMMENDATION = "recommendation"   # What SHUNYA suggests
    EXTERNAL = "external"               # Retrieved from outside the business
    UNKNOWN = "unknown"                 # Something SHUNYA does not know


# ═══════════════════════════════════════════════════════════════════
# Evidence + Confidence (G4)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class EvidenceSource:
    """Provenance for an intelligence result."""
    source_type: str  # "memory", "knowledge", "identity", "execution", "external"
    source_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    confidence: float = 1.0  # 0.0 to 1.0
    authority: str = "unknown"  # "canonical", "derived", "external", "ai"


@dataclass
class IntelligenceResult:
    """A single intelligence output with provenance."""
    content: str
    category: TruthCategory = TruthCategory.UNKNOWN
    confidence: float = 1.0
    evidence: list[EvidenceSource] = field(default_factory=list)
    is_stale: bool = False
    requires_review: bool = False


# ═══════════════════════════════════════════════════════════════════
# Canonical Context (G1)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class IntelligenceContext:
    """Authoritative context assembly for intelligence operations.

    Respects FDA3 boundaries: Memory ≠ Knowledge ≠ Events ≠ Execution.
    """
    tenant_id: Optional[str] = None
    actor_id: Optional[str] = None
    identity: Optional[dict] = None
    relevant_memory: list[IntelligenceResult] = field(default_factory=list)
    relevant_knowledge: list[IntelligenceResult] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    execution_state: Optional[dict] = None

    def is_empty(self) -> bool:
        return not any([
            self.identity, self.relevant_memory, self.relevant_knowledge,
            self.relationships, self.events, self.execution_state,
        ])


# ═══════════════════════════════════════════════════════════════════
# Context Assembly Engine (G1)
# ═══════════════════════════════════════════════════════════════════

class ContextAssemblyEngine:
    """Assembles context for intelligence operations.

    Company-first order (G2):
    1. What SHUNYA already knows
    2. Authorized company knowledge
    3. Relevant memory/context
    4. Execution/relationship state
    5. External information (only when necessary)
    """

    def __init__(self, memory_service=None, identity_service=None, knowledge_service=None):
        self._memory_service = memory_service
        self._identity_service = identity_service
        self._knowledge_service = knowledge_service

    def assemble(self, tenant_id: str, actor_id: Optional[str] = None,
                 query: Optional[str] = None) -> IntelligenceContext:
        """Assemble context for an intelligence operation."""
        ctx = IntelligenceContext(tenant_id=tenant_id, actor_id=actor_id)

        # Step 1: Identity resolution
        if self._identity_service and actor_id:
            try:
                identity = self._identity_service.get_identity(actor_id)
                if identity:
                    # IdentityResolution object — convert to dict-like access
                    ctx.identity = {
                        "id": getattr(identity, "identity_id", actor_id),
                        "canonical_name": getattr(identity, "canonical_name", ""),
                        "name": getattr(identity, "canonical_name", ""),
                    }
            except Exception as e:
                logger.debug(f"Identity resolution failed: {e}")

        # Step 2: Relevant memory
        if self._memory_service and query:
            try:
                memories = self._memory_service.retrieve(query, tenant_id=tenant_id)
                for m in memories:
                    ctx.relevant_memory.append(IntelligenceResult(
                        content=str(m.get("value", "")),
                        category=TruthCategory.MEMORY,
                        confidence=float(m.get("confidence", 0.5)),
                        evidence=[EvidenceSource(
                            source_type="memory",
                            source_id=str(m.get("id", "")),
                            confidence=float(m.get("confidence", 0.5)),
                        )],
                    ))
            except Exception:
                pass

        return ctx


# ═══════════════════════════════════════════════════════════════════
# Intelligence Engine (G2, G5, G6, G7)
# ═══════════════════════════════════════════════════════════════════

class IntelligenceEngine:
    """Canonical intelligence engine.

    Produces actionable outcomes from authorized data.
    Deterministic-first (G5): uses rules before AI.
    """

    def __init__(self, memory_service=None, identity_service=None, knowledge_service=None):
        self._context_engine = ContextAssemblyEngine(
            memory_service=memory_service,
            identity_service=identity_service,
            knowledge_service=knowledge_service,
        )

    def answer(self, query: str, tenant_id: str, actor_id: Optional[str] = None) -> IntelligenceResult:
        """Answer a business question using the canonical intelligence pipeline.

        Company-first (G2): uses company data before external information.
        """
        # Step 1: Assemble context
        ctx = self._context_engine.assemble(tenant_id, actor_id, query)

        # Step 2: Try deterministic answers first (G5)
        result = self._try_deterministic(query, ctx)
        if result:
            return result

        # Step 3: If no deterministic answer, try memory/knowledge
        if ctx.relevant_memory:
            best = max(ctx.relevant_memory, key=lambda r: r.confidence)
            return best

        # Step 4: Unknown
        return IntelligenceResult(
            content="I don't have enough information to answer that question.",
            category=TruthCategory.UNKNOWN,
            confidence=0.0,
            requires_review=True,
        )

    def _try_deterministic(self, query: str, ctx: IntelligenceContext) -> Optional[IntelligenceResult]:
        """Try deterministic rules before expensive AI (G5)."""
        q = query.lower().strip()

        # Identity queries
        if "who am i" in q or "who is this" in q:
            if ctx.identity:
                name = ctx.identity.get("canonical_name", ctx.identity.get("name", "Unknown"))
                return IntelligenceResult(
                    content=f"You are {name}.",
                    category=TruthCategory.FACT,
                    confidence=1.0,
                    evidence=[EvidenceSource(
                        source_type="identity",
                        source_id=str(ctx.identity.get("id", "")),
                        confidence=1.0,
                        authority="canonical",
                    )],
                )

        # Time queries
        if "what time is it" in q or "what is the date" in q:
            now = datetime.utcnow()
            return IntelligenceResult(
                content=f"The current time is {now.strftime('%Y-%m-%d %H:%M UTC')}.",
                category=TruthCategory.FACT,
                confidence=1.0,
            )

        # Empty context
        if ctx.is_empty():
            return IntelligenceResult(
                content="No company data is available yet. Start by adding contacts, emails, or business records.",
                category=TruthCategory.UNKNOWN,
                confidence=0.0,
            )

        return None

    def get_context(self, tenant_id: str, actor_id: Optional[str] = None) -> IntelligenceContext:
        """Get assembled context without answering a question."""
        return self._context_engine.assemble(tenant_id, actor_id)


# ═══════════════════════════════════════════════════════════════════
# Safe Failure (G8)
# ═══════════════════════════════════════════════════════════════════

class SafeFailureHandler:
    """Handles intelligence failures safely.

    Never: invent → present confidently → execute.
    """

    @staticmethod
    def handle_missing_data(query: str, context: IntelligenceContext) -> IntelligenceResult:
        return IntelligenceResult(
            content="I don't have enough evidence to answer that question.",
            category=TruthCategory.UNKNOWN,
            confidence=0.0,
            requires_review=True,
        )

    @staticmethod
    def handle_conflicting_data(query: str, results: list[IntelligenceResult]) -> IntelligenceResult:
        """When data conflicts, preserve the conflict and require review."""
        evidence_sources = []
        for r in results:
            evidence_sources.extend(r.evidence)
        return IntelligenceResult(
            content="I found conflicting information and cannot determine which is correct.",
            category=TruthCategory.UNKNOWN,
            confidence=0.0,
            requires_review=True,
            evidence=evidence_sources,
        )

    @staticmethod
    def handle_provider_unavailable(provider: str) -> IntelligenceResult:
        return IntelligenceResult(
            content=f"The {provider} provider is currently unavailable. Please try again later.",
            category=TruthCategory.UNKNOWN,
            confidence=0.0,
            requires_review=True,
        )

    @staticmethod
    def handle_unauthorized() -> IntelligenceResult:
        return IntelligenceResult(
            content="You don't have permission to access that information.",
            category=TruthCategory.UNKNOWN,
            confidence=0.0,
            requires_review=True,
        )