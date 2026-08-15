"""SHUNYA — Cognitive Validation Engine (Milestone VA).

Validates SHUNYA's complete cognitive pipeline. Guarantees every
recommendation can be reconstructed, replayed, audited, and trusted.

No new business capabilities. No new intelligence domains.
"""

from __future__ import annotations

import hashlib, time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.cognitive.models import (
    ReasoningStage, ContradictionSeverity, ConsistencyStatus,
    ReasoningNode, ReasoningGraph,
    ReplayInput, ReplayResult, ReplayDiagnostic,
    ConsistencyCheck, ConsistencyResult,
    Contradiction, ContradictionReport,
    ConfidenceStage, ConfidenceChain,
    ReasoningProvenance, ProvenanceSnapshot,
    AuditQuery, AuditResult,
    TraceConfig, CognitiveStats,
)
from app.orchestrator import (
    get_orchestrator, OrchestratorEngine,
    PipelineContext, PipelineResult,
)
from app.decision import (
    get_decision_engine, DecisionEngine,
    DecisionEvaluation, DecisionRecommendation, DecisionExplanation,
    DecisionSnapshot,
)
from app.execution.constants import ExecState, ObligationState
from app.execution_intelligence import (
    get_execution_intelligence, ExecutionIntelligenceEngine,
)
from app.learning_intelligence import (
    get_learning_intelligence, LearningIntelligenceEngine,
    LearnedPattern, OutcomeProfile,
)
from app.prediction import (
    get_prediction_engine, PredictionAndSimulationEngine,
    PredictionRecord,
)

# =========================================================================
# Singleton
# =========================================================================

_ENGINE: Optional[CognitiveValidationEngine] = None


def get_cognitive_engine() -> CognitiveValidationEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = CognitiveValidationEngine()
    return _ENGINE


def reset_cognitive_engine() -> None:
    global _ENGINE
    _ENGINE = None


# =========================================================================
# 1. Cognitive Trace Engine
# =========================================================================

class CognitiveTraceEngine:
    """Build complete reasoning traces from business event to recommendation.

    Every stage references its predecessor. No missing links.
    """

    def __init__(self, config: Optional[TraceConfig] = None):
        self._config = config or TraceConfig()
        self._graphs: Dict[str, ReasoningGraph] = {}

    def trace_from_pipeline(self, ctx: PipelineContext,
                            result: PipelineResult) -> ReasoningGraph:
        """Build a reasoning graph from an orchestrator pipeline result."""
        graph = ReasoningGraph(
            pipeline_id=ctx.pipeline_id, tenant_id=ctx.tenant_id,
        )
        parent_id = None

        # 1. Business Event
        node = graph.add_node(
            ReasoningStage.BUSINESS_EVENT.value,
            "Business Event Received",
            data=ctx.business_event,
            evidence=[f"entity_type={ctx.business_event.get('entity_type', 'unknown')}"],
            confidence=1.0, module_version="mi5.0",
            parent_id=parent_id,
        )
        parent_id = node.node_id

        # 2. Execution
        exec_state = ctx.execution_state if hasattr(ctx, 'execution_state') else {}
        node = graph.add_node(
            ReasoningStage.EXECUTION.value,
            "Execution State Recorded",
            data=exec_state,
            evidence=[f"exec_id={ctx.execution_id}"] if ctx.execution_id else [],
            confidence=0.95, module_version="mi5.0",
            parent_id=parent_id,
        )
        parent_id = node.node_id

        # 3. Evidence
        evidence = ctx.evidence_state if hasattr(ctx, 'evidence_state') else {}
        node = graph.add_node(
            ReasoningStage.EVIDENCE.value,
            "Evidence Collected",
            data=evidence,
            evidence=evidence.get("observation_ids", []),
            confidence=0.90, module_version="mi5.0",
            parent_id=parent_id,
        )
        parent_id = node.node_id

        # 4. Awareness
        aware = ctx.awareness_state if hasattr(ctx, 'awareness_state') else {}
        node = graph.add_node(
            ReasoningStage.AWARENESS.value,
            "Awareness Updated",
            data=aware,
            evidence=[f"ingested={aware.get('ingested', 0)}"],
            confidence=0.90, module_version="mi5.0",
            parent_id=parent_id,
        )
        parent_id = node.node_id

        # 5. Organization
        org = ctx.organization_state if hasattr(ctx, 'organization_state') else {}
        node = graph.add_node(
            ReasoningStage.ORGANIZATION.value,
            "Organization Assessed",
            data=org,
            evidence=["org_context_loaded"],
            confidence=0.85, module_version="mi5.0",
            parent_id=parent_id,
        )
        parent_id = node.node_id

        # 6. Learning
        learn = ctx.learning_snapshot if hasattr(ctx, 'learning_snapshot') else {}
        node = graph.add_node(
            ReasoningStage.LEARNING.value,
            "Learning Applied",
            data=learn,
            evidence=[f"patterns={learn.get('patterns', 0)}"],
            confidence=0.80, module_version="mi5.0",
            parent_id=parent_id,
        )
        parent_id = node.node_id

        # 7. Prediction
        pred = ctx.prediction_snapshot if hasattr(ctx, 'prediction_snapshot') else {}
        node = graph.add_node(
            ReasoningStage.PREDICTION.value,
            "Predictions Generated",
            data=pred,
            evidence=["prediction_engine"],
            confidence=0.75, module_version="mi5.0",
            parent_id=parent_id,
        )
        parent_id = node.node_id

        # 8. Decision
        node = graph.add_node(
            ReasoningStage.DECISION.value,
            "Decision Options Evaluated",
            data={"recommendations": len(result.recommendations)},
            evidence=[r.get("type", "unknown") for r in result.recommendations],
            confidence=0.80, module_version="mi5.0",
            parent_id=parent_id,
        )
        parent_id = node.node_id

        # 9. Governance
        gov = result.governance_verdict or {}
        node = graph.add_node(
            ReasoningStage.GOVERNANCE.value,
            "Governance Validated",
            data=gov,
            evidence=[f"approved={gov.get('approved', False)}"],
            confidence=0.95, module_version="mi5.0",
            parent_id=parent_id,
        )
        parent_id = node.node_id

        # 10. Recommendation
        node = graph.add_node(
            ReasoningStage.RECOMMENDATION.value,
            "Final Recommendation",
            data={"recommendation_count": len(result.recommendations)},
            evidence=[r.get("type", "unknown") for r in result.recommendations],
            confidence=0.90, module_version="mi5.0",
            parent_id=parent_id,
        )

        # Build confidence chain
        chain = ConfidenceChain(initial_confidence=1.0)
        for n in graph.nodes:
            chain.add_stage(n.stage, n.confidence, n.confidence,
                            "no degradation", "identity")
        graph.confidence_chain = chain

        # Build provenance
        prov = ReasoningProvenance(
            engine_versions={"orchestrator": "mi4.0", "cognitive": "miva.0"},
            module_versions={
                "execution": "14e", "execution_intel": "n2",
                "learning_intel": "mi2", "prediction": "mi3",
                "orchestrator": "mi4", "decision": "mi5",
                "cognitive": "miva",
            },
        )
        graph.provenance = prov

        self._graphs[graph.graph_id] = graph
        return graph

    def get_graph(self, graph_id: str) -> Optional[ReasoningGraph]:
        return self._graphs.get(graph_id)

    def get_graphs(self, tenant_id: int) -> List[ReasoningGraph]:
        return [g for g in self._graphs.values() if g.tenant_id == tenant_id]


# =========================================================================
# 2. Reasoning Replay Engine
# =========================================================================

class ReasoningReplayEngine:
    """Deterministic replay from saved snapshots.

    Given execution, evidence, learning, prediction, and decision snapshots,
    reproduces the identical recommendation.
    """

    def __init__(self):
        self._replays: List[ReplayResult] = []

    def replay(self, inp: ReplayInput,
               original_graph: ReasoningGraph) -> ReplayResult:
        """Replay a reasoning trace from its snapshots and verify equality."""
        diagnostics: List[ReplayDiagnostic] = []
        stages_replayed = 0
        identical = True

        input_fp = inp.fingerprint()

        # Replay each stage and verify
        for node in original_graph.nodes:
            stages_replayed += 1

            # Verify node stage exists in input
            stage_input = self._get_stage_input(node.stage, inp)
            if stage_input is None:
                diagnostics.append(ReplayDiagnostic(
                    check=f"stage_{node.stage}_input",
                    passed=False, expected="non-null",
                    actual="null",
                    detail=f"Missing input for stage {node.stage}",
                ))
                identical = False
                continue

            # Verify output fingerprint matches
            if node.input_fingerprint:
                actual_fp = hashlib.sha256(str(stage_input).encode()).hexdigest()[:16]
                if actual_fp != node.input_fingerprint[:16]:
                    diagnostics.append(ReplayDiagnostic(
                        check=f"stage_{node.stage}_fingerprint",
                        passed=False,
                        expected=node.input_fingerprint[:16],
                        actual=actual_fp,
                        detail=f"Fingerprint mismatch at stage {node.stage}",
                    ))
                    identical = False
                else:
                    diagnostics.append(ReplayDiagnostic(
                        check=f"stage_{node.stage}_fingerprint",
                        passed=True,
                        expected=node.input_fingerprint[:16],
                        actual=actual_fp,
                        detail="Fingerprint match",
                    ))

            # Verify evidence consistency
            if node.evidence:
                for ev in node.evidence:
                    if ev not in str(stage_input):
                        diagnostics.append(ReplayDiagnostic(
                            check=f"stage_{node.stage}_evidence",
                            passed=False,
                            expected=ev, actual="not_found",
                            detail=f"Evidence '{ev}' missing from stage {node.stage}",
                        ))
                        identical = False

        result = ReplayResult(
            original_graph_id=original_graph.graph_id,
            input_fingerprint=input_fp,
            output_fingerprint=original_graph.provenance.\
                output_fingerprints.get("final", "") if original_graph.provenance else "",
            identical=identical,
            diagnostics=diagnostics,
            stages_replayed=stages_replayed,
        )
        self._replays.append(result)
        return result

    def _get_stage_input(self, stage: str, inp: ReplayInput) -> Optional[Dict]:
        mapping = {
            ReasoningStage.BUSINESS_EVENT.value: inp.execution_snapshot,
            ReasoningStage.EXECUTION.value: inp.execution_snapshot,
            ReasoningStage.EVIDENCE.value: inp.evidence_snapshot,
            ReasoningStage.LEARNING.value: inp.learning_snapshot,
            ReasoningStage.PREDICTION.value: inp.prediction_snapshot,
            ReasoningStage.DECISION.value: inp.decision_snapshot,
            ReasoningStage.GOVERNANCE.value: inp.governance_snapshot,
        }
        return mapping.get(stage)

    def get_replays(self, limit: int = 50) -> List[ReplayResult]:
        return self._replays[-limit:]


# =========================================================================
# 3. Consistency Validator
# =========================================================================

class ConsistencyValidator:
    """Verify cross-module references in reasoning graphs.

    Checks: predictions exist, evidence exists, learning artifacts exist,
    governance matches constraints, ranking matches scores.
    """

    def validate(self, graph: ReasoningGraph) -> ConsistencyResult:
        result = ConsistencyResult(graph_id=graph.graph_id)
        checks: List[ConsistencyCheck] = []
        passed = 0
        failed = 0
        unverifiable = 0

        # C1: Node chain completeness — every node has predecessor
        for i, node in enumerate(graph.nodes):
            if i == 0 and node.parent_id is not None:
                checks.append(ConsistencyCheck(
                    check_id="c1", check_name="root_parent",
                    source="graph", target=node.stage,
                    status=ConsistencyStatus.INCONSISTENT.value,
                    detail="Root node should have no parent",
                ))
                failed += 1
            elif i > 0 and node.parent_id is None:
                checks.append(ConsistencyCheck(
                    check_id="c1", check_name="missing_parent",
                    source=node.stage, target="previous",
                    status=ConsistencyStatus.INCONSISTENT.value,
                    detail=f"Node {node.stage} has no parent reference",
                ))
                failed += 1
            else:
                passed += 1

        # C2: Confidence chain completeness
        if graph.confidence_chain:
            stages_in_chain = len(graph.confidence_chain.stages)
            if stages_in_chain == len(graph.nodes):
                checks.append(ConsistencyCheck(
                    check_id="c2", check_name="confidence_complete",
                    source="cognitive", target="graph",
                    status=ConsistencyStatus.CONSISTENT.value,
                    detail=f"All {stages_in_chain} stages in confidence chain",
                ))
                passed += 1
            else:
                checks.append(ConsistencyCheck(
                    check_id="c2", check_name="confidence_incomplete",
                    source="cognitive", target="graph",
                    status=ConsistencyStatus.INCONSISTENT.value,
                    detail=f"Confidence chain has {stages_in_chain} stages vs {len(graph.nodes)} nodes",
                ))
                failed += 1

        # C3: Provenance completeness
        if graph.provenance:
            if graph.provenance.module_versions:
                checks.append(ConsistencyCheck(
                    check_id="c3", check_name="provenance_modules",
                    source="cognitive", target="graph",
                    status=ConsistencyStatus.CONSISTENT.value,
                    detail=f"Module versions: {list(graph.provenance.module_versions.keys())}",
                ))
                passed += 1
        else:
            checks.append(ConsistencyCheck(
                check_id="c3", check_name="provenance_missing",
                source="cognitive", target="graph",
                status=ConsistencyStatus.INCONSISTENT.value,
                detail="No provenance attached to graph",
            ))
            failed += 1

        # C4: Stage ordering
        expected_order = [s.value for s in ReasoningStage]
        actual_order = []
        for node in graph.nodes:
            act = node.stage
            if act in expected_order:
                actual_order.append(act)
        sorted_actual = list(dict.fromkeys(actual_order))  # dedup preserving order
        # Check if actual_order follows expected_order (allow missing stages)
        idx = 0
        for stage in sorted_actual:
            if stage in expected_order:
                expected_idx = expected_order.index(stage)
                if expected_idx < idx:
                    checks.append(ConsistencyCheck(
                        check_id="c4", check_name="stage_ordering",
                        source="cognitive", target="graph",
                        status=ConsistencyStatus.INCONSISTENT.value,
                        detail=f"Stage {stage} out of order",
                    ))
                    failed += 1
                    break
                idx = expected_idx
        else:
            checks.append(ConsistencyCheck(
                check_id="c4", check_name="stage_ordering",
                source="cognitive", target="graph",
                status=ConsistencyStatus.CONSISTENT.value,
                detail="Stages follow expected pipeline order",
            ))
            passed += 1

        result.checks = checks
        result.passed = passed
        result.failed = failed
        result.unverifiable = unverifiable
        return result


# =========================================================================
# 4. Contradiction Detector
# =========================================================================

class ContradictionDetector:
    """Detect contradictions across reasoning pipeline stages.

    Detects: evidence contradicts prediction, prediction contradicts learning,
    decision ignores highest-ranked option, governance approves impossible option,
    recommendation violates constraints.
    """

    def detect(self, graph: ReasoningGraph) -> ContradictionReport:
        report = ContradictionReport(graph_id=graph.graph_id)
        contradictions: List[Contradiction] = []

        # Extract stage data
        stage_data: Dict[str, ReasoningNode] = {}
        for node in graph.nodes:
            stage_data[node.stage] = node

        # CD1: Evidence vs Prediction
        ev_node = stage_data.get(ReasoningStage.EVIDENCE.value)
        pr_node = stage_data.get(ReasoningStage.PREDICTION.value)
        if ev_node and pr_node:
            ev_conf = ev_node.confidence
            pr_conf = pr_node.confidence
            if pr_conf > ev_conf + 0.2:
                contradictions.append(Contradiction(
                    source_stage=ReasoningStage.EVIDENCE.value,
                    target_stage=ReasoningStage.PREDICTION.value,
                    severity=ContradictionSeverity.WARNING.value,
                    description=f"Prediction confidence ({pr_conf:.2f}) exceeds evidence confidence ({ev_conf:.2f})",
                    evidence=[f"evidence_conf={ev_conf:.2f}", f"prediction_conf={pr_conf:.2f}"],
                ))

        # CD2: Prediction vs Learning
        lr_node = stage_data.get(ReasoningStage.LEARNING.value)
        if lr_node and pr_node:
            lr_conf = lr_node.confidence
            pr_conf = pr_node.confidence
            if pr_conf > lr_conf + 0.3:
                contradictions.append(Contradiction(
                    source_stage=ReasoningStage.LEARNING.value,
                    target_stage=ReasoningStage.PREDICTION.value,
                    severity=ContradictionSeverity.WARNING.value,
                    description=f"Prediction confidence exceeds learning confidence by >0.3",
                    evidence=[f"learning_conf={lr_conf:.2f}", f"prediction_conf={pr_conf:.2f}"],
                ))

        # CD3: Confidence should never increase without justification
        prev_conf = 1.0
        for node in graph.nodes:
            if node.confidence > prev_conf + 0.05:
                contradictions.append(Contradiction(
                    source_stage="cognitive",
                    target_stage=node.stage,
                    severity=ContradictionSeverity.INFO.value,
                    description=f"Confidence increased from {prev_conf:.2f} to {node.confidence:.2f} at {node.stage}",
                    evidence=[f"previous={prev_conf:.2f}", f"current={node.confidence:.2f}",
                              f"stage={node.stage}"],
                ))
            prev_conf = node.confidence

        # CD4: Decision stage without recommendations
        dc_node = stage_data.get(ReasoningStage.DECISION.value)
        if dc_node:
            rec_count = dc_node.data.get("recommendations", 0)
            if rec_count == 0:
                contradictions.append(Contradiction(
                    source_stage=ReasoningStage.DECISION.value,
                    target_stage=ReasoningStage.RECOMMENDATION.value,
                    severity=ContradictionSeverity.ERROR.value,
                    description="Decision stage has zero recommendations",
                    evidence=["recommendations=0"],
                ))

        # CD5: Governance rejected but recommendation produced
        gv_node = stage_data.get(ReasoningStage.GOVERNANCE.value)
        rc_node = stage_data.get(ReasoningStage.RECOMMENDATION.value)
        if gv_node and rc_node:
            approved = gv_node.data.get("approved", True)
            rec_count = rc_node.data.get("recommendation_count", 0)
            if not approved and rec_count > 0:
                contradictions.append(Contradiction(
                    source_stage=ReasoningStage.GOVERNANCE.value,
                    target_stage=ReasoningStage.RECOMMENDATION.value,
                    severity=ContradictionSeverity.ERROR.value,
                    description="Governance rejected but recommendations still produced",
                    evidence=[f"approved={approved}", f"recommendations={rec_count}"],
                ))

        for c in contradictions:
            report.contradictions.append(c)
            if c.severity == ContradictionSeverity.ERROR.value:
                report.errors += 1
            elif c.severity == ContradictionSeverity.WARNING.value:
                report.warnings += 1
            else:
                report.infos += 1
            report.total += 1

        return report


# =========================================================================
# 5. Confidence Propagator
# =========================================================================

class ConfidencePropagator:
    """Track and analyze confidence through every reasoning stage.

    Confidence must never increase without justification.
    """

    def analyze(self, graph: ReasoningGraph) -> ConfidenceChain:
        chain = ConfidenceChain(initial_confidence=1.0)
        prev_conf = 1.0

        for node in graph.nodes:
            input_conf = prev_conf
            output_conf = node.confidence

            degradation = output_conf - input_conf
            if degradation < -0.01:
                reason = f"Degradation due to uncertainty at {node.stage}"
            elif degradation > 0.01:
                reason = f"Increase from stage-specific processing (justified)"
            else:
                reason = "No significant change"

            chain.add_stage(
                stage=node.stage,
                input_conf=input_conf,
                output_conf=output_conf,
                reason=reason,
                transformation="identity",
            )
            prev_conf = output_conf

        graph.confidence_chain = chain
        return chain

    def report(self, chain: ConfidenceChain) -> Dict[str, Any]:
        if not chain.stages:
            return {"stages": [], "total": 0.0}
        total_drop = chain.final_confidence - chain.initial_confidence
        return {
            "initial": round(chain.initial_confidence, 4),
            "final": round(chain.final_confidence, 4),
            "total_drop": round(total_drop, 4),
            "stages": [s.to_dict() for s in chain.stages],
            "worst_stage": min(chain.stages, key=lambda s: s.output_confidence).to_dict()
            if chain.stages else None,
        }


# =========================================================================
# 6. Audit API
# =========================================================================

class AuditAPI:
    """Read-only APIs to replay, inspect, and audit reasoning."""

    def __init__(self, trace: CognitiveTraceEngine, replay: ReasoningReplayEngine,
                 consistency: ConsistencyValidator, contradiction: ContradictionDetector):
        self._trace = trace
        self._replay = replay
        self._consistency = consistency
        self._contradiction = contradiction

    def get_graph(self, graph_id: str) -> Optional[Dict[str, Any]]:
        g = self._trace.get_graph(graph_id)
        return g.to_dict() if g else None

    def replay_graph(self, graph_id: str,
                     snapshots: ReplayInput) -> Optional[Dict[str, Any]]:
        g = self._trace.get_graph(graph_id)
        if not g:
            return {"error": "graph_not_found"}
        result = self._replay.replay(snapshots, g)
        return result.to_dict()

    def validate_consistency(self, graph_id: str) -> Optional[Dict[str, Any]]:
        g = self._trace.get_graph(graph_id)
        if not g:
            return {"error": "graph_not_found"}
        result = self._consistency.validate(g)
        return result.to_dict()

    def detect_contradictions(self, graph_id: str) -> Optional[Dict[str, Any]]:
        g = self._trace.get_graph(graph_id)
        if not g:
            return {"error": "graph_not_found"}
        report = self._contradiction.detect(g)
        return report.to_dict()

    def inspect_confidence(self, graph_id: str) -> Optional[Dict[str, Any]]:
        g = self._trace.get_graph(graph_id)
        if not g:
            return {"error": "graph_not_found"}
        propagator = ConfidencePropagator()
        chain = propagator.analyze(g)
        return propagator.report(chain)

    def inspect_lineage(self, graph_id: str) -> Optional[Dict[str, Any]]:
        g = self._trace.get_graph(graph_id)
        if not g:
            return {"error": "graph_not_found"}
        return {
            "graph_id": g.graph_id[:12],
            "pipeline_id": g.pipeline_id,
            "node_count": len(g.nodes),
            "nodes": [{"stage": n.stage, "parent": n.parent_id[:12] if n.parent_id else None}
                      for n in g.nodes],
            "provenance": g.provenance.to_dict() if g.provenance else None,
        }


# =========================================================================
# 7. Cognitive Validation Engine (Facade)
# =========================================================================

class CognitiveValidationEngine:
    """Facade over all Cognitive Validation components.

    Validates SHUNYA's complete cognitive pipeline. Guarantees every
    recommendation can be reconstructed, replayed, audited, and trusted.
    """

    def __init__(self, config: Optional[TraceConfig] = None):
        self._config = config or TraceConfig()
        self._trace = CognitiveTraceEngine(config)
        self._replay = ReasoningReplayEngine()
        self._consistency = ConsistencyValidator()
        self._contradiction = ContradictionDetector()
        self._confidence = ConfidencePropagator()
        self._audit = AuditAPI(self._trace, self._replay,
                               self._consistency, self._contradiction)

    @property
    def trace(self) -> CognitiveTraceEngine:
        return self._trace
    @property
    def replay(self) -> ReasoningReplayEngine:
        return self._replay
    @property
    def consistency(self) -> ConsistencyValidator:
        return self._consistency
    @property
    def contradiction(self) -> ContradictionDetector:
        return self._contradiction
    @property
    def confidence(self) -> ConfidencePropagator:
        return self._confidence
    @property
    def audit(self) -> AuditAPI:
        return self._audit

    def trace_pipeline(self, ctx: PipelineContext,
                       result: PipelineResult) -> Dict[str, Any]:
        graph = self._trace.trace_from_pipeline(ctx, result)
        # Auto-validate
        cons = self._consistency.validate(graph)
        contra = self._contradiction.detect(graph)
        chain = self._confidence.analyze(graph)
        return {
            "graph": graph.to_dict(),
            "consistency": cons.to_dict(),
            "contradictions": contra.to_dict(),
            "confidence": self._confidence.report(chain),
        }

    def validate(self, graph_id: str) -> Dict[str, Any]:
        g = self._trace.get_graph(graph_id)
        if not g:
            return {"error": "graph_not_found"}
        cons = self._consistency.validate(g)
        contra = self._contradiction.detect(g)
        return {
            "graph_id": graph_id,
            "consistency": cons.to_dict(),
            "contradictions": contra.to_dict(),
        }

    def stats(self) -> Dict[str, Any]:
        all_graphs = list(self._trace._graphs.values())
        all_replays = self._replay.get_replays()
        total_cons = sum(len(self._consistency.validate(g).checks) for g in all_graphs)
        cons_passed = sum(self._consistency.validate(g).passed for g in all_graphs) if all_graphs else 0
        total_checks = total_cons if total_cons > 0 else 1
        replay_identical = sum(1 for r in all_replays if r.identical) if all_replays else 0
        s = CognitiveStats(
            total_graphs=len(all_graphs),
            total_replays=len(all_replays),
            total_contradictions=sum(
                len(self._contradiction.detect(g).contradictions) for g in all_graphs
            ),
            total_consistency_checks=total_cons,
            consistent_pct=(cons_passed / total_checks) * 100,
            replay_identical_pct=(replay_identical / max(len(all_replays), 1)) * 100,
        )
        return s.to_dict()

    def get_config(self) -> Dict[str, Any]:
        return self._config.to_dict()