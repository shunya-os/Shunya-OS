"""Universal Personal Operating System — Orchestrator.

Compiles and composes every frozen UCP into a unified Living Context.
No new Runtime. No duplicate Living Objects. Pure composition.
"""

from __future__ import annotations

import logging
from typing import Any

from core.personal_os.attention import AttentionEngine
from core.personal_os.execution import ExecutionOrchestrator
from core.personal_os.memory import MemoryEngine
from core.personal_os.models import (
    AttentionSignal,
    ExecutableRecommendation,
    LivingContextSnapshot,
    MemoryRecord,
)
from core.personal_os.providers import ProviderOrchestrator
from core.personal_os.workspace import WorkspaceEngine

logger = logging.getLogger(__name__)


def _safe_import(module_path: str, class_name: str):
    """Safely import a frozen UCP runtime — handles missing imports gracefully."""
    try:
        mod = __import__(module_path, fromlist=[class_name])
        return getattr(mod, class_name)()
    except (ImportError, AttributeError) as e:
        logger.debug(f"UCP not available: {module_path}.{class_name}: {e}")
        return None


class PersonalOSOrchestrator:
    """The core orchestration layer — composes every frozen UCP."""

    def __init__(self) -> None:
        self._owner_id: str = ""
        self._composed_runtimes: dict[str, Any] = {}
        self._context: LivingContextSnapshot | None = None
        self._attention = AttentionEngine()
        self._execution = ExecutionOrchestrator()
        self._memory = MemoryEngine()
        self._workspace = WorkspaceEngine()
        self._providers = ProviderOrchestrator()

    # ── Initialization ──────────────────────────────────────────────────

    def initialize(self) -> dict[str, list[str]]:
        """Initialize and compose every frozen UCP."""
        ucps = {
            "relationship": ("core.relationship_intelligence", "RelationshipIntelligenceRuntime"),
            "financial": ("core.financial_intelligence", "FinancialIntelligenceRuntime"),
            "knowledge": ("core.knowledge_intelligence", "KnowledgeIntelligenceRuntime"),
            "decision": ("core.decision_intelligence", "DecisionIntelligenceRuntime"),
            "agreement": ("core.agreement_intelligence", "AgreementIntelligenceRuntime"),
            "asset": ("core.asset_intelligence", "AssetIntelligenceRuntime"),
            "initiative": ("core.initiative_intelligence", "InitiativeIntelligenceRuntime"),
            "operations": ("core.operations_intelligence", "OperationsIntelligenceRuntime"),
            "health": ("core.health_intelligence", "HealthIntelligenceRuntime"),
            "learning": ("core.learning_intelligence", "LearningIntelligenceRuntime"),
        }

        available = []
        unavailable = []
        for name, (mod_path, cls_name) in ucps.items():
            runtime = _safe_import(mod_path, cls_name)
            if runtime:
                self._composed_runtimes[name] = runtime
                available.append(name)
            else:
                unavailable.append(name)

        return {"available": available, "unavailable": unavailable}

    def set_owner(self, owner_id: str) -> None:
        self._owner_id = owner_id
        # Propagate to all sub-engines
        self._memory.set_owner(owner_id)
        self._workspace.set_owner(owner_id)

    # ── Living Context ──────────────────────────────────────────────────

    def build_context(self, objective: str = "") -> LivingContextSnapshot:
        """Build a composite Living Context from ALL frozen UCPs.

        The user never manually chooses capabilities — this method
        automatically determines which Living Objects participate.
        """
        snap = LivingContextSnapshot(owner_id=self._owner_id)

        # Compose from every available UCP
        for name, runtime in self._composed_runtimes.items():
            try:
                self._compose_ucp(name, runtime, snap, objective)
            except Exception as e:
                logger.debug(f"Composition error for {name}: {e}")

        self._context = snap
        return snap

    def _compose_ucp(self, name: str, runtime: Any, snap: LivingContextSnapshot,
                     objective: str) -> None:
        """Compose one UCP into the Living Context."""
        caps = getattr(runtime, 'get_capabilities', lambda: [])()
        if not caps:
            return

        if name == "initiative":
            pid = self._owner_id
            # Use _resolve pattern common across UCPs
            profile = getattr(runtime, '_resolve', lambda _: None)(pid)
            if profile:
                snap.active_initiatives = [i.initiative_id for i in getattr(profile, 'active_initiatives', [])]

        elif name == "agreement":
            profile = getattr(runtime, '_resolve', lambda _: None)(self._owner_id)
            if profile:
                # Agreements with obligations pending or breached
                for a in getattr(profile, 'agreements', []):
                    breaches = getattr(runtime, '_engine', None) and \
                        runtime._engine.detect_breaches(a)
                    if breaches:
                        snap.active_agreements.append(a.agreement_id)

        elif name == "asset":
            profile = getattr(runtime, '_resolve', lambda _: None)(self._owner_id)
            if profile:
                snap.active_assets = [a.asset_id for a in getattr(profile, 'active_assets', [])]

        elif name == "financial":
            profile = getattr(runtime, '_resolve', lambda _: None)(self._owner_id)
            if profile:
                snap.financial_commitments = [
                    {"account": a.name, "balance": a.balance.to_dict() if hasattr(a.balance, 'to_dict') else {}}
                    for a in getattr(profile, 'accounts', [])
                ]

        elif name == "health":
            profile = getattr(runtime, '_resolve', lambda _: None)(self._owner_id)
            if profile:
                snap.health_concerns = [
                    c.get('name', '') for c in getattr(profile, 'conditions', [])
                    if hasattr(c, 'get') and c.get('severity', '') == 'high'
                ]

        elif name == "learning":
            profile = getattr(runtime, '_resolve', lambda _: None)(self._owner_id)
            if profile:
                snap.learning_paths = [g.get('title', '') for g in getattr(profile, 'goals', [])
                                       if hasattr(g, 'get') and g.get('status') == 'in_progress']

        elif name == "operations":
            profile = getattr(runtime, '_resolve', lambda _: None)(self._owner_id)
            if profile:
                snap.operations_issues = [
                    p.title for p in getattr(profile, 'processes', [])
                    if getattr(p, 'status', '') == 'failing'
                ]

        elif name == "decision":
            profile = getattr(runtime, '_resolve', lambda _: None)(self._owner_id)
            if profile:
                snap.recent_decisions = [
                    d.decision_id for d in getattr(profile, 'decisions', [])[-5:]
                ]

        elif name == "knowledge":
            profile = getattr(runtime, '_resolve', lambda _: None)(self._owner_id)
            if profile:
                snap.knowledge_items = [
                    k.knowledge_id for k in getattr(profile, 'knowledge_list', [])
                ]

        elif name == "relationship":
            profile = getattr(runtime, '_resolve', lambda _: None)(self._owner_id)
            if profile:
                snap.relevant_relationships = [
                    p.profile_id for p in getattr(profile, 'profiles', [])
                ]

    def get_context(self) -> LivingContextSnapshot | None:
        return self._context

    # ── Attention ───────────────────────────────────────────────────────

    def assess_attention(self) -> list[AttentionSignal]:
        """Determine what matters right now across all UCPs."""
        context = self._context or self.build_context()
        signals = self._attention.scan(context, self._composed_runtimes)
        return signals

    # ── Memory ──────────────────────────────────────────────────────────

    def store(self, content: str, source: str = "", tags: list[str] | None = None,
              memory_type: str = "short_term") -> MemoryRecord:
        return self._memory.store(content, source, tags or [], memory_type)

    def recall(self, query: str, limit: int = 10) -> list[MemoryRecord]:
        return self._memory.recall(query, limit)

    # ── Workspace ───────────────────────────────────────────────────────

    def build_workspace(self, objective: str = "") -> dict[str, Any]:
        context = self._context or self.build_context(objective)
        signals = self.assess_attention()
        return self._workspace.render(context, signals)

    # ── Execution ───────────────────────────────────────────────────────

    def recommend(self, objective: str = "") -> list[ExecutableRecommendation]:
        context = self._context or self.build_context(objective)
        signals = self.assess_attention()
        return self._execution.formulate(context, signals)

    def execute(self, rec: ExecutableRecommendation) -> dict[str, Any]:
        return self._execution.execute(rec, self._composed_runtimes)

    # ── Providers ───────────────────────────────────────────────────────

    def list_providers(self) -> dict[str, Any]:
        return self._providers.list_available()

    # ── Lifecycle ───────────────────────────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        return {"status": "healthy", "composed_ucps": list(self._composed_runtimes.keys()),
                "workspace": self._workspace.get_state(),
                "memory_count": self._memory.count()}

    def shutdown(self) -> None:
        self._composed_runtimes.clear()
        self._memory.clear()
        self._context = None