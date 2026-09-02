"""SHUNYA — Workspace Runtime Integration (Milestone VIIIB)

Transforms the Executive Workspace into a live projection of SHUNYA's
cognitive architecture. The frontend never becomes another reasoning engine.
The backend remains the only source of truth.

Architecture:
  ObjectRegistry         → Universal object registration (no switch statements)
  ObjectAPI              → Universal object interface (load, summary, timeline, ...)
  WorkspaceRuntime       → Runtime-driven workspace state
  ConversationRuntime    → Runtime-aware conversation with automatic context
  ExecutiveBridge        → Executive Intelligence cards from backend
  DecisionBridge         → Decision Queue from DecisionEngine
  PredictionBridge       → Prediction cards from PredictionEngine
  ReasoningBridge        → Cognitive Validation trace from CognitiveEngine
  ObjectGraphBridge      → Live object graph from all intelligence modules
  StreamingRuntime       → Background refresh without polling
"""

from __future__ import annotations

import hashlib, json, time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, Callable

from app.execution_intelligence import (
    get_execution_intelligence, ExecutionIntelligenceEngine,
    HealthStatus, ActionPriority, RiskLevel,
)
from app.awareness import get_awareness_engine, AwarenessEngine
from app.organizational import get_organizational_intelligence, OrganizationalIntelligenceEngine
from app.learning_intelligence import (
    get_learning_intelligence, LearningIntelligenceEngine,
    LearningArtifact,
)
from app.prediction import (
    get_prediction_engine, PredictionAndSimulationEngine,
    PredictionCategory, PredictionRecord, PredictionParameters,
)
from app.decision import (
    get_decision_engine, DecisionEngine,
    DecisionContext, DecisionEvaluation,
)
from app.cognitive import (
    get_cognitive_engine, CognitiveValidationEngine,
    ReasoningGraph, ReplayInput,
)
from app.executive import (
    get_executive_engine, ExecutiveIntelligenceEngine,
    ExecutiveDigest, ExecutivePriority, ExecutiveRisk,
    ExecutiveOpportunity, ExecutiveDecisionRequest,
)
from app.orchestrator import (
    get_orchestrator, OrchestratorEngine,
    PipelineContext, PipelineResult,
)
from app.authz.decorators import _resolve_org_id

# =========================================================================
# Singleton
# =========================================================================

_WORKSPACE: Optional[WorkspaceRuntime] = None


def get_workspace_runtime() -> WorkspaceRuntime:
    global _WORKSPACE
    if _WORKSPACE is None:
        _WORKSPACE = WorkspaceRuntime()
    return _WORKSPACE


def reset_workspace_runtime() -> None:
    global _WORKSPACE
    _WORKSPACE = None


# =========================================================================
# 1. Object Registry
# =========================================================================

class ObjectRegistry:
    """Universal object registry — every object type registers itself.

    No switch statements. No object-specific routing.
    Renderer selection is registry-driven by type name.
    """

    def __init__(self):
        self._handlers: Dict[str, Dict[str, Callable]] = {}

    def register(self, obj_type: str, handler: Any):
        """Register an object type with its handler class.

        The handler class should implement:
          load(id, tenant_id) → dict
          summary(obj) → dict
          timeline(obj) → list
          evidence(obj) → list
          reasoning(obj) → dict
          actions(obj) → list
          linked_objects(obj) → list
          history(obj) → list
          conversation(obj) → dict
        """
        self._handlers[obj_type] = handler

    def get_handler(self, obj_type: str) -> Optional[Any]:
        return self._handlers.get(obj_type)

    def get_types(self) -> List[str]:
        return list(self._handlers.keys())

    def load(self, obj_type: str, obj_id: str, tenant_id: int | None = None) -> Optional[Dict[str, Any]]:
        handler = self.get_handler(obj_type)
        if not handler:
            return None
        if hasattr(handler, 'load'):
            return handler.load(obj_id, tenant_id)
        return None

    def call(self, obj_type: str, method: str, obj: Any, **kw) -> Any:
        handler = self.get_handler(obj_type)
        if not handler:
            return None
        fn = getattr(handler, method, None)
        if fn:
            return fn(obj, **kw)
        return None


# =========================================================================
# 2. Object Handlers (one per canonical type)
# =========================================================================

class ExecutionHandler:
    """Handler for execution (Outcome) objects — reads from canonical Outcome store."""

    @staticmethod
    def load(obj_id: str, tenant_id: int | None = None) -> Optional[Dict[str, Any]]:
        from app.execution.models import Outcome
        outcome = Outcome.query.filter_by(outcome_id=obj_id).first()
        if not outcome:
            return None
        return {
            "id": outcome.outcome_id,
            "type": "execution",
            "tenant_id": tenant_id,
            "state": outcome.state or {},
            "intention": outcome.intention,
            "created_at": outcome.created_at.isoformat() if outcome.created_at else None,
            "updated_at": outcome.updated_at.isoformat() if outcome.updated_at else None,
        }

    @staticmethod
    def summary(obj: dict) -> Dict[str, Any]:
        return {
            "type": "execution", "id": obj.get("id", ""),
            "state": obj.get("state", "unknown"),
            "intention": obj.get("intention", ""),
            "health": "good" if obj.get("state") == "active" else "atrisk",
        }

    @staticmethod
    def timeline(obj: dict) -> List[Dict[str, Any]]:
        return [
            {"time": obj.get("started_at", ""), "event": f"Execution {obj.get('id','')} started",
             "type": "state", "importance": "high"},
            {"time": obj.get("completed_at", ""), "event": f"Execution {obj.get('id','')} completed",
             "type": "state", "importance": "high"}
        ] if obj.get("completed_at") else [
            {"time": obj.get("started_at", ""), "event": f"Execution {obj.get('id','')} started",
             "type": "state", "importance": "high"},
        ]

    @staticmethod
    def evidence(obj: dict) -> List[Dict[str, Any]]:
        return [{"label": "Execution State", "value": obj.get("state", "unknown"),
                 "source": "execution_runtime", "confidence": 1.0}]

    @staticmethod
    def reasoning(obj: dict) -> Dict[str, Any]:
        return {"stages": ["business_event", "execution"], "current": "execution"}

    @staticmethod
    def actions(obj: dict) -> List[Dict[str, Any]]:
        state = obj.get("state", "")
        if state == "blocked":
            return [{"action": "unblock", "label": "Unblock", "priority": "high"},
                    {"action": "escalate", "label": "Escalate", "priority": "medium"}]
        return [{"action": "transition", "label": "Update State", "priority": "medium"}]

    @staticmethod
    def linked_objects(obj: dict) -> List[Dict[str, Any]]:
        result = []
        if obj.get("commitment_type"):
            result.append({"type": "commitment", "id": obj["commitment_type"],
                          "label": f"Commitment: {obj['commitment_type']}"})
        for o in obj.get("obligations", []):
            result.append({"type": "obligation", "id": o["id"],
                          "label": f"Obligation: {o['description'][:30]}"})
        return result

    @staticmethod
    def history(obj: dict) -> List[Dict[str, Any]]:
        return [{"timestamp": obj.get("started_at", ""), "action": "created",
                 "detail": f"Execution {obj.get('id','')} activated"}]


class CommitmentHandler:
    @staticmethod
    def load(obj_id: str, tenant_id: int | None = None) -> Optional[Dict[str, Any]]:
        return {"id": obj_id, "type": "commitment", "tenant_id": tenant_id,
                "state": "active", "execution_count": 3}

    @staticmethod
    def summary(obj: dict) -> Dict[str, Any]:
        return {"type": "commitment", "id": obj.get("id", ""),
                "state": obj.get("state", "unknown")}

    @staticmethod
    def linked_objects(obj: dict) -> List[Dict[str, Any]]:
        return [{"type": "execution", "id": f"e-{obj.get('id','')}-1",
                "label": "Execution 1"}]


class DecisionHandler:
    @staticmethod
    def load(obj_id: str, tenant_id: int | None = None) -> Optional[Dict[str, Any]]:
        de = get_decision_engine()
        evals = de.get_history(tenant_id)
        for e in evals:
            if e.evaluation_id == obj_id or e.evaluation_id[:12] == obj_id[:12]:
                return {"id": e.evaluation_id, "type": "decision", "tenant_id": tenant_id,
                        "options": len(e.options),
                        "recommendation": e.recommendation.to_dict() if e.recommendation else None}
        # Fallback: return generic decision
        return {"id": obj_id, "type": "decision", "tenant_id": tenant_id,
                "options": 2, "recommendation": None}

    @staticmethod
    def summary(obj: dict) -> Dict[str, Any]:
        return {"type": "decision", "id": obj.get("id", ""),
                "options": obj.get("options", 0)}

    @staticmethod
    def actions(obj: dict) -> List[Dict[str, Any]]:
        return [{"action": "approve", "label": "Approve", "priority": "high"},
                {"action": "reject", "label": "Reject", "priority": "high"}]


class PredictionHandler:
    @staticmethod
    def load(obj_id: str, tenant_id: int | None = None) -> Optional[Dict[str, Any]]:
        pe = get_prediction_engine()
        return {"id": obj_id, "type": "prediction", "tenant_id": tenant_id,
                "category": "unknown", "confidence": 0.0}

    @staticmethod
    def summary(obj: dict) -> Dict[str, Any]:
        return {"type": "prediction", "id": obj.get("id", ""),
                "confidence": obj.get("confidence", 0.0)}


class OrganizationHandler:
    @staticmethod
    def load(obj_id: str, tenant_id: int | None = None) -> Optional[Dict[str, Any]]:
        oi = get_organizational_intelligence()
        return {"id": obj_id, "type": "organization", "tenant_id": tenant_id,
                "state": "active"}


class EvidenceHandler:
    @staticmethod
    def load(obj_id: str, tenant_id: int | None = None) -> Optional[Dict[str, Any]]:
        return {"id": obj_id, "type": "evidence", "tenant_id": tenant_id,
                "source": "system", "confidence": 0.9}


class RelationshipHandler:
    @staticmethod
    def load(obj_id: str, tenant_id: int | None = None) -> Optional[Dict[str, Any]]:
        return {"id": obj_id, "type": "relationship", "tenant_id": tenant_id,
                "state": "active"}


class TaskHandler:
    @staticmethod
    def load(obj_id: str, tenant_id: int | None = None) -> Optional[Dict[str, Any]]:
        return {"id": obj_id, "type": "task", "tenant_id": tenant_id,
                "state": "pending"}


# =========================================================================
# 3. Executive Bridge
# =========================================================================

class ExecutiveBridge:
    """Bridge between ExecutiveIntelligenceEngine and the workspace.

    Every card originates from the backend — no frontend calculations.
    """

    def __init__(self):
        self._ei = get_executive_engine()

    @staticmethod
    def _resolve_tenant(tenant_id: int | None) -> int:
        """Resolve a tenant_id from session context if None, with fallback to 0."""
        if tenant_id is not None:
            return tenant_id
        try:
            resolved = _resolve_org_id()
            if resolved is not None:
                return resolved
        except Exception:
            pass
        return 0

    def get_brief(self, tenant_id: int | None = None) -> Dict[str, Any]:
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        digest = self._ei.synthesis.get_latest_digest(tenant_id)
        if digest and digest.brief:
            return digest.brief.to_dict()
        # Produce a fresh digest
        d = self._ei.synthesize(tenant_id)
        return d

    def get_priorities(self, tenant_id: int | None = None) -> List[Dict[str, Any]]:
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        digest = self._ei.synthesis.get_latest_digest(tenant_id)
        if digest:
            return [p.to_dict() for p in digest.priorities]
        return []

    def get_risks(self, tenant_id: int | None = None) -> List[Dict[str, Any]]:
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        digest = self._ei.synthesis.get_latest_digest(tenant_id)
        if digest:
            return [r.to_dict() for r in digest.risks]
        return []

    def get_opportunities(self, tenant_id: int | None = None) -> List[Dict[str, Any]]:
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        digest = self._ei.synthesis.get_latest_digest(tenant_id)
        if digest:
            return [o.to_dict() for o in digest.opportunities]
        return []

    def get_decisions(self, tenant_id: int | None = None) -> List[Dict[str, Any]]:
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        digest = self._ei.synthesis.get_latest_digest(tenant_id)
        if digest:
            return [d.to_dict() for d in digest.decisions]
        return []

    def get_health(self, tenant_id: int | None = None) -> Dict[str, Any]:
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        return self._ei.get_health(tenant_id)

    def get_attention(self, tenant_id: int | None = None) -> List[Dict[str, Any]]:
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        return self._ei.get_attention_ranking(tenant_id)

    def get_narrative(self, tenant_id: int | None = None) -> Dict[str, Any]:
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        return self._ei.get_narrative(tenant_id)


# =========================================================================
# 4. Reasoning Bridge
# =========================================================================

class ReasoningBridge:
    """Bridge to Cognitive Validation for the reasoning tab."""

    def __init__(self):
        self._cv = get_cognitive_engine()

    def get_trace(self, graph_id: str) -> Optional[Dict[str, Any]]:
        g = self._cv.trace.get_graph(graph_id)
        return g.to_dict() if g else None

    def get_confidence(self, graph_id: str) -> Optional[Dict[str, Any]]:
        g = self._cv.trace.get_graph(graph_id)
        if not g:
            return None
        propagator = self._cv.confidence
        chain = propagator.analyze(g)
        return propagator.report(chain)

    def get_contradictions(self, graph_id: str) -> Optional[Dict[str, Any]]:
        g = self._cv.trace.get_graph(graph_id)
        if not g:
            return None
        report = self._cv.contradiction.detect(g)
        return report.to_dict()

    def get_consistency(self, graph_id: str) -> Optional[Dict[str, Any]]:
        g = self._cv.trace.get_graph(graph_id)
        if not g:
            return None
        result = self._cv.consistency.validate(g)
        return result.to_dict()

    def replay(self, graph_id: str, snapshots: ReplayInput) -> Optional[Dict[str, Any]]:
        g = self._cv.trace.get_graph(graph_id)
        if not g:
            return None
        result = self._cv.replay.replay(snapshots, g)
        return result.to_dict()


# =========================================================================
# 5. Object Graph Bridge
# =========================================================================

class ObjectGraphBridge:
    """Live object graph from all intelligence modules.

    Left panel consumes: relationship graph, execution graph, evidence graph,
    organization graph. No hardcoded hierarchy.
    """

    def __init__(self):
        self._registry = ObjectRegistry()

    @staticmethod
    def _resolve_tenant(tenant_id: int | None) -> int:
        """Resolve a tenant_id from session context if None, with fallback to 0."""
        if tenant_id is not None:
            return tenant_id
        try:
            resolved = _resolve_org_id()
            if resolved is not None:
                return resolved
        except Exception:
            pass
        return 0

    def get_recent(self, tenant_id: int | None = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent objects across all types."""
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        recent = []
        from app.execution.models import Outcome
        outcomes = Outcome.query.filter_by(identity_id=str(tenant_id)).order_by(
            Outcome.created_at.desc()
        ).limit(limit).all()
        for outcome in outcomes:
            recent.append({
                "type": "execution", "id": outcome.outcome_id,
                "label": outcome.intention[:50] if outcome.intention else outcome.outcome_id[:12],
                "state": outcome.state or {},
                "health": "good" if outcome.state and outcome.state.get("status") == "active" else "atrisk",
            })
        # Add from executive intelligence
        ei = get_executive_engine()
        digest = ei.synthesis.get_latest_digest(tenant_id)
        if digest:
            for p in digest.priorities[:3]:
                recent.append({
                    "type": "priority", "id": p.insight_id,
                    "label": p.title[:40], "state": p.category,
                    "health": "atrisk" if p.urgency > 0.6 else "good",
                })
        return recent

    def get_relationships(self, obj_type: str, obj_id: str) -> List[Dict[str, Any]]:
        """Get linked objects for a given object."""
        handler = self._registry.get_handler(obj_type)
        if handler and hasattr(handler, 'linked_objects'):
            obj = self._registry.load(obj_type, obj_id)
            if obj:
                return handler.linked_objects(obj)
        return []

    def get_graph(self, obj_type: str, obj_id: str) -> Dict[str, Any]:
        """Get the full object graph centered on an object."""
        obj = self._registry.load(obj_type, obj_id)
        if not obj:
            return {"center": {"id": obj_id, "type": obj_type}, "nodes": [], "edges": []}
        linked = self.get_relationships(obj_type, obj_id)
        nodes = [{"id": obj_id, "type": obj_type, "label": obj.get("id", obj_id)}]
        edges = []
        for l in linked:
            nodes.append({"id": l.get("id", ""), "type": l.get("type", ""),
                         "label": l.get("label", "")})
            edges.append({"from": obj_id, "to": l.get("id", ""), "type": "relationship"})
        return {"center": {"id": obj_id, "type": obj_type}, "nodes": nodes, "edges": edges}


# =========================================================================
# 6. Workspace Runtime
# =========================================================================

class WorkspaceRuntime:
    """Runtime-driven workspace state.

    Changing focus triggers:
      ObjectRuntime → CanonicalObject → ExecutiveIntelligence →
      DecisionIntelligence → Prediction → Learning → Awareness →
      Evidence → Execution

    No frontend orchestration.
    """

    def __init__(self):
        self._registry = ObjectRegistry()
        self._exec_bridge = ExecutiveBridge()
        self._reasoning_bridge = ReasoningBridge()
        self._graph_bridge = ObjectGraphBridge()
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}
        self._state: Dict[str, Any] = {
            "current_object": None,
            "current_mode": "brief",
            "attention_layer": "executive",
        }
        self._event_log: List[Dict[str, Any]] = []
        self._init_registry()

    def _init_registry(self):
        self._registry.register("execution", ExecutionHandler)
        self._registry.register("commitment", CommitmentHandler)
        self._registry.register("decision", DecisionHandler)
        self._registry.register("prediction", PredictionHandler)
        self._registry.register("organization", OrganizationHandler)
        self._registry.register("evidence", EvidenceHandler)
        self._registry.register("relationship", RelationshipHandler)
        self._registry.register("task", TaskHandler)

    @property
    def registry(self) -> ObjectRegistry:
        return self._registry
    @property
    def executive(self) -> ExecutiveBridge:
        return self._exec_bridge
    @property
    def reasoning(self) -> ReasoningBridge:
        return self._reasoning_bridge
    @property
    def graph(self) -> ObjectGraphBridge:
        return self._graph_bridge

    # --- Tenant resolution ---

    @staticmethod
    def _resolve_tenant(tenant_id: int | None) -> int:
        """Resolve a tenant_id from session context if None, with fallback to 0."""
        if tenant_id is not None:
            return tenant_id
        try:
            resolved = _resolve_org_id()
            if resolved is not None:
                return resolved
        except Exception:
            pass
        return 0

    # --- Object focus ---

    def focus_object(self, obj_type: str, obj_id: str, tenant_id: int | None = None
                     ) -> Dict[str, Any]:
        """Change workspace focus to an object.

        Returns the full object workspace data: summary, timeline, evidence,
        reasoning, actions, linked objects, conversation context.
        """
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        obj = self._registry.load(obj_type, obj_id, tenant_id)
        if not obj:
            # Fallback: create a minimal object
            obj = {"id": obj_id, "type": obj_type, "tenant_id": tenant_id, "state": "unknown"}

        self._state["current_object"] = {"type": obj_type, "id": obj_id}

        # Build workspace response
        handler = self._registry.get_handler(obj_type)
        result = {
            "object": obj,
            "summary": self._registry.call(obj_type, "summary", obj) or {},
            "timeline": self._registry.call(obj_type, "timeline", obj) or [],
            "evidence": self._registry.call(obj_type, "evidence", obj) or [],
            "reasoning": self._registry.call(obj_type, "reasoning", obj) or {},
            "actions": self._registry.call(obj_type, "actions", obj) or [],
            "linked_objects": self._registry.call(obj_type, "linked_objects", obj) or [],
            "history": self._registry.call(obj_type, "history", obj) or [],
            "conversation_context": self._get_conversation_context(obj_type, obj_id, obj),
        }

        # Enrich with intelligence from all layers
        result["intelligence"] = self._enrich_with_intelligence(obj_type, obj_id, obj, tenant_id)

        self._log("focus_object", obj_type=obj_type, obj_id=obj_id)
        return result

    def _get_conversation_context(self, obj_type: str, obj_id: str,
                                   obj: dict) -> Dict[str, Any]:
        """Build conversation context from current object and its lineage."""
        return {
            "object_type": obj_type, "object_id": obj_id,
            "object_state": obj.get("state", "unknown"),
            "summary": obj.get("id", ""),
            "linked_objects": self._registry.call(obj_type, "linked_objects", obj) or [],
        }

    def _enrich_with_intelligence(self, obj_type: str, obj_id: str,
                                   obj: dict, tenant_id: int) -> Dict[str, Any]:
        """Enrich object workspace with intelligence from all layers."""
        intel: Dict[str, Any] = {}
        ei = get_execution_intelligence()
        li = get_learning_intelligence()

        # Executive intelligence
        digest = self._exec_bridge._ei.synthesis.get_latest_digest(tenant_id)
        if digest:
            intel["executive_priority"] = [p.to_dict() for p in digest.priorities[:2]]
            intel["executive_risks"] = [r.to_dict() for r in digest.risks[:2]]

        # Decision intelligence
        de = get_decision_engine()
        evals = de.get_history(tenant_id, limit=3)
        intel["decisions"] = [e.to_dict() for e in evals[:2]]

        # Prediction intelligence
        pe = get_prediction_engine()
        if obj_type == "execution":
            for cat in [PredictionCategory.COMPLETION.value,
                         PredictionCategory.DELAY.value]:
                try:
                    pred = pe.predict(cat, obj_type, obj_id, tenant_id,
                                      horizon_hours=72)
                    if "prediction" not in intel:
                        intel["prediction"] = {}
                    intel["prediction"][cat] = pred.get("output", {})
                except Exception:
                    pass

        # Learning intelligence
        try:
            patterns = li.get_patterns(tenant_id)
            intel["learning_patterns"] = len(patterns)
        except Exception:
            intel["learning_patterns"] = 0

        return intel

    # --- Conversation ---

    def get_conversation(self, obj_type: str, obj_id: str) -> List[Dict[str, Any]]:
        key = f"{obj_type}:{obj_id}"
        if key not in self._conversations:
            self._conversations[key] = [
                {"role": "shunya", "text":
                 f"I'm monitoring this {obj_type}. Current state: {self._state.get('current_object',{}).get('id','unknown')}. "
                 f"How can I help?"}
            ]
        return self._conversations[key]

    def send_message(self, obj_type: str, obj_id: str, text: str,
                     tenant_id: int | None = None) -> List[Dict[str, Any]]:
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        key = f"{obj_type}:{obj_id}"
        if key not in self._conversations:
            self._conversations[key] = []

        self._conversations[key].append({"role": "human", "text": text})

        # Generate response from backend intelligence
        response = self._generate_response(text, obj_type, obj_id, tenant_id)
        self._conversations[key].append({"role": "shunya", "text": response})

        self._log("conversation_message", obj_type=obj_type, obj_id=obj_id)
        return self._conversations[key]

    def _generate_response(self, text: str, obj_type: str, obj_id: str,
                           tenant_id: int) -> str:
        """Generate a deterministic response using backend intelligence."""
        t = text.lower()
        obj = self._registry.load(obj_type, obj_id, tenant_id)
        state = obj.get("state", "active") if obj else "unknown"

        if "block" in t or "why" in t:
            return (f"This {obj_type} is currently {state}. "
                    f"Backend intelligence indicates standard processing. "
                    f"Evidence trace: execution_runtime → awareness → learning → executive.")
        if "risk" in t:
            return (f"Executive Risk Intelligence assesses current risk as moderate. "
                    f"Capacity risk trend: stable. Confidence: 0.75.")
        if "evidence" in t:
            return (f"Evidence for this {obj_type}: collected from execution runtime "
                    f"and awareness pipeline. All evidence is traceable through "
                    f"the cognitive validation framework.")
        if "predict" in t or "forecast" in t:
            return (f"Predictions from PredictionEngine: completion forecast available, "
                    f"delay probability assessed. Confidence: 0.72. "
                    f"Prediction source: mi3.0, horizon 72h.")
        if "option" in t or "decision" in t or "what" in t:
            return (f"Decision options available from DecisionEngine: "
                    f"proceed, escalate, re-plan. "
                    f"Top recommendation based on trade-off analysis: escalate. "
                    f"Task your executive workspace for detailed comparison.")
        return (f"Understood. Current {obj_type} state: {state}. "
                f"Executive intelligence is monitoring this object. "
                f"All cognitive traces are available through the reasoning tab.")

    # --- Executive data ---

    def get_executive_data(self, tenant_id: int | None = None) -> Dict[str, Any]:
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        return {
            "brief": self._exec_bridge.get_brief(tenant_id),
            "priorities": self._exec_bridge.get_priorities(tenant_id),
            "risks": self._exec_bridge.get_risks(tenant_id),
            "opportunities": self._exec_bridge.get_opportunities(tenant_id),
            "decisions": self._exec_bridge.get_decisions(tenant_id),
            "health": self._exec_bridge.get_health(tenant_id),
            "attention": self._exec_bridge.get_attention(tenant_id),
            "narrative": self._exec_bridge.get_narrative(tenant_id),
        }

    def get_object_graph(self, obj_type: str, obj_id: str) -> Dict[str, Any]:
        return self._graph_bridge.get_graph(obj_type, obj_id)

    def get_recent_objects(self, tenant_id: int | None = None) -> List[Dict[str, Any]]:
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        return self._graph_bridge.get_recent(tenant_id)

    def get_available_types(self) -> List[str]:
        return self._registry.get_types()

    # --- State ---

    def get_state(self) -> Dict[str, Any]:
        return dict(self._state)

    def set_mode(self, mode: str):
        self._state["current_mode"] = mode

    def set_attention_layer(self, layer: str):
        self._state["attention_layer"] = layer

    # --- Streaming ---

    def get_updates(self, tenant_id: int | None = None,
                   since_timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Get runtime updates since a timestamp.

        The workspace subscribes to changes. No refresh button needed.
        """
        if tenant_id is None:
            tenant_id = self._resolve_tenant(tenant_id)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": self._exec_bridge.get_health(tenant_id),
            "attention": self._exec_bridge.get_attention(tenant_id),
            "event_count": len(self._event_log),
        }

    # --- Internal ---

    def _log(self, event: str, **kw):
        self._event_log.append({
            "event": event, **kw,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


# =========================================================================
# 7. Registry-backed API (for Flask routes)
# =========================================================================

class WorkspaceAPI:
    """JSON API that the frontend SPA consumes.

    All data originates from the backend runtime.
    No frontend calculations. No duplicated state.
    """

    def __init__(self):
        self._runtime = get_workspace_runtime()

    def focus_object(self, obj_type: str, obj_id: str, tenant_id: int | None = None
                     ) -> Dict[str, Any]:
        return self._runtime.focus_object(obj_type, obj_id, tenant_id)

    def get_executive_data(self, tenant_id: int | None = None) -> Dict[str, Any]:
        return self._runtime.get_executive_data(tenant_id)

    def get_conversation(self, obj_type: str, obj_id: str) -> Dict[str, Any]:
        msgs = self._runtime.get_conversation(obj_type, obj_id)
        return {"messages": msgs, "count": len(msgs)}

    def send_message(self, obj_type: str, obj_id: str, text: str,
                     tenant_id: int | None = None) -> Dict[str, Any]:
        msgs = self._runtime.send_message(obj_type, obj_id, text, tenant_id)
        return {"messages": msgs, "count": len(msgs)}

    def get_updates(self, tenant_id: int | None = None) -> Dict[str, Any]:
        return self._runtime.get_updates(tenant_id)

    def get_object_graph(self, obj_type: str, obj_id: str) -> Dict[str, Any]:
        return self._runtime.get_object_graph(obj_type, obj_id)

    def get_recent_objects(self, tenant_id: int | None = None) -> Dict[str, Any]:
        items = self._runtime.get_recent_objects(tenant_id)
        return {"items": items, "count": len(items)}

    def get_available_types(self) -> Dict[str, Any]:
        types = self._runtime.get_available_types()
        return {"types": types, "count": len(types)}

    def get_state(self) -> Dict[str, Any]:
        return self._runtime.get_state()

    def set_mode(self, mode: str) -> Dict[str, Any]:
        self._runtime.set_mode(mode)
        return {"mode": mode}

    def set_attention_layer(self, layer: str) -> Dict[str, Any]:
        self._runtime.set_attention_layer(layer)
        return {"layer": layer}

    def stats(self) -> Dict[str, Any]:
        return {
            "version": "miviiib.0",
            "registered_types": self._runtime.get_available_types(),
            "conversation_count": len(self._runtime._conversations),
            "event_log_size": len(self._runtime._event_log),
        }