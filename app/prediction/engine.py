"""SHUNYA — Prediction & Simulation Engine (Milestone III).

Deterministic predictions and isolated simulations. Reads from Execution,
Execution Intelligence, Learning Intelligence, Organizational Intelligence,
and Operational Awareness — never writes to canonical state.

Predictions stored as LearningArtifacts in Learning Memory.
Simulations execute on forked (copied) execution state.

Architectural authority: Prediction Philosophy v1.0
"""

from __future__ import annotations

import hashlib, copy
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from app.prediction.models import (
    PredictionCategory, SimulationType, PredictionStatus,
    ConfidenceFactorName,
    PredictionRecord, PredictionParameters,
    ConfidenceDecomposition, ConfidenceFactor as CFModel,
    EvidenceTrace, Assumption, Uncertainty,
    PredictionExplanation, PredictionRefusal,
    SimulationInput, SimulationResult, SimulationFork,
    ScenarioBranch, ScenarioComparison,
    PredictionAuditEntry, PredictionStats,
    PredictionConfig, PredictionFilter,
)
from app.execution.constants import ExecState, ObligationState
from app.execution_engine.service import ExecutionService
from app.execution_intelligence import (
    get_execution_intelligence, ExecutionIntelligenceEngine,
)
from app.learning_intelligence import (
    get_learning_intelligence, LearningIntelligenceEngine,
    LearnedPattern, OutcomeProfile, RefinedRecommendation,
    LearningArtifact, ConfidenceAssessment,
)

# =========================================================================
# Singleton
# =========================================================================

_ENGINE: Optional[PredictionAndSimulationEngine] = None


def get_prediction_engine() -> PredictionAndSimulationEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = PredictionAndSimulationEngine()
    return _ENGINE


def reset_prediction_engine() -> None:
    global _ENGINE
    _ENGINE = None


# =========================================================================
# 1. Prediction Engine
# =========================================================================

class PredictionEngine:
    """Deterministic prediction engine for 9 prediction categories.

    Each prediction is a pure function: (current_state, historical_patterns,
    learning_profiles) → prediction_output.

    Reads from execution state, execution intelligence, and learning
    intelligence — never writes to any of them.
    """

    def __init__(self, config: Optional[PredictionConfig] = None):
        self._config = config or PredictionConfig()

    def predict(self, params: PredictionParameters,
                exec_service: ExecutionService,
                exec_intel: ExecutionIntelligenceEngine,
                learn_intel: LearningIntelligenceEngine) -> PredictionRecord:
        """Generate a prediction for the given parameters.

        Returns either a PredictionRecord with output+confidence or
        a PredictionRecord with refusal information.
        """
        cat = params.category
        handler = self._get_handler(cat)
        if not handler:
            return self._refuse(params, "unknown_category", f"No handler for {cat}")

        result = handler(params, exec_service, exec_intel, learn_intel)

        # Compute input fingerprint
        fp_raw = f"{params.to_dict()}:{len(exec_service._execs)}:{datetime.now(timezone.utc).isoformat()}"
        input_fp = hashlib.sha256(fp_raw.encode()).hexdigest()

        # Compute confidence with 5-factor decomposition
        confidence = self._compute_confidence(result, params)

        # Compute output fingerprint
        output_fp = hashlib.sha256(str(result.get("output", {})).encode()).hexdigest()

        record = PredictionRecord(
            params=params,
            output=result["output"],
            confidence=confidence,
            input_fingerprint=input_fp,
            output_fingerprint=output_fp,
            evidence_traces=result.get("evidence_traces", []),
            assumptions=result.get("assumptions", []),
            uncertainties=result.get("uncertainties", []),
        )

        # Check if refusal conditions apply
        refusal = self._check_refusal(result, params)
        if refusal:
            record.output = refusal.to_dict()
            record.status = PredictionStatus.PENDING.value
            record.output["_refused"] = True
        elif confidence.overall < params.min_confidence_threshold:
            record.output = PredictionRefusal(
                reason="insufficient_confidence",
                detail=f"Confidence {confidence.overall:.4f} below threshold {params.min_confidence_threshold}",
                confidence_if_computed=confidence.overall,
                threshold=params.min_confidence_threshold,
            ).to_dict()
            record.status = PredictionStatus.PENDING.value
            record.output["_refused"] = True

        return record

    def _get_handler(self, category: str):
        handlers = {
            PredictionCategory.COMPLETION.value: self._predict_completion,
            PredictionCategory.DELAY.value: self._predict_delay,
            PredictionCategory.WORKLOAD.value: self._predict_workload,
            PredictionCategory.CAPACITY.value: self._predict_capacity,
            PredictionCategory.BOTTLENECK.value: self._predict_bottleneck,
            PredictionCategory.DEPENDENCY.value: self._predict_dependency,
            PredictionCategory.ORG_IMPACT.value: self._predict_org_impact,
            PredictionCategory.OPPORTUNITY.value: self._predict_opportunity,
            PredictionCategory.RECOMMENDATION_OUTCOME.value: self._predict_recommendation,
        }
        return handlers.get(category)

    # --- Individual prediction methods ---

    def _predict_completion(self, params, svc, exec_intel, learn_intel):
        inst = svc._execs.get(params.entity_id)
        if not inst:
            return {"output": {"error": "execution_not_found"}, "evidence_traces": []}
        if inst.state in (ExecState.FULFILLED, ExecState.FAILED, ExecState.CANCELLED):
            return {"output": {"completed": True, "final_state": inst.state},
                    "evidence_traces": [EvidenceTrace("execution", "terminal_state", inst.state)]}
        obls = [o for o in svc._obls.values() if o.exec_id == inst.exec_id]
        now = datetime.now(timezone.utc)
        started = self._parse_dt(inst.started_at)
        elapsed = 0.0
        if started:
            elapsed = (now - started).total_seconds()
        satisfied = sum(1 for o in obls if o.state == ObligationState.SATISFIED)
        ratio = satisfied / len(obls) if obls else 0.0
        predicted_remaining = None
        if ratio > 0.0 and elapsed > 0:
            estimated_total = elapsed / ratio
            predicted_remaining = estimated_total - elapsed
        predicted_dt = now + timedelta(seconds=predicted_remaining or 86400)
        optimistic_dt = now + timedelta(seconds=(predicted_remaining or 86400) * 0.7)
        pessimistic_dt = now + timedelta(seconds=(predicted_remaining or 86400) * 1.5)
        profile = learn_intel.runtime.outcomes.get_profile(
            inst.commitment_type, inst.state, inst.tenant_id) if learn_intel else None
        hist_avg = profile.avg_duration_seconds if profile else None
        traces = [EvidenceTrace("execution", f"completion_ratio={ratio:.2f}", f"{satisfied}/{len(obls)} obligations")]
        if hist_avg:
            traces.append(EvidenceTrace("learning", "historical_avg_duration", f"{hist_avg:.0f}s"))
        return {
            "output": {
                "predicted_at": predicted_dt.isoformat(),
                "optimistic_at": optimistic_dt.isoformat(),
                "pessimistic_at": pessimistic_dt.isoformat(),
                "completion_ratio": round(ratio, 4),
                "elapsed_seconds": round(elapsed, 1),
                "predicted_remaining_seconds": round(predicted_remaining, 1) if predicted_remaining else None,
                "historical_avg_seconds": round(hist_avg, 1) if hist_avg else None,
            },
            "evidence_traces": traces,
            "assumptions": [Assumption("No new blocked obligations",
                                       "Blocked obligations increase completion time", 0.85)],
            "uncertainties": [Uncertainty("prediction_horizon",
                                          f"Forecast extends {params.horizon_hours}h",
                                          "confidence decreases with horizon")],
        }

    def _predict_delay(self, params, svc, exec_intel, learn_intel):
        inst = svc._execs.get(params.entity_id)
        if not inst:
            return {"output": {"error": "execution_not_found"}, "evidence_traces": []}
        obls = [o for o in svc._obls.values() if o.exec_id == inst.exec_id]
        now = datetime.now(timezone.utc)
        overdue = []
        for o in obls:
            if o.due_at and o.state not in (ObligationState.SATISFIED, ObligationState.WAIVED):
                due = self._parse_dt(o.due_at)
                if due and due < now:
                    overdue.append(o)
        has_exceptions = any(True for _ in svc._excs.values() if _.exec_id == inst.exec_id)
        delay_prob = min(1.0, len(overdue) * 0.25 + (0.3 if has_exceptions else 0))
        expected_hours = len(overdue) * 12.0 + (24 if has_exceptions else 0)
        traces = [EvidenceTrace("obligations", f"overdue={len(overdue)}", f"{len(overdue)} overdue obligations")]
        if has_exceptions:
            traces.append(EvidenceTrace("exceptions", "active_exceptions", "Unknown"))
        return {
            "output": {
                "delay_probability": round(delay_prob, 4),
                "expected_delay_hours": round(expected_hours, 1),
                "overdue_count": len(overdue),
                "has_critical_exceptions": has_exceptions,
            },
            "evidence_traces": traces,
            "assumptions": [Assumption("Overdue obligations will complete eventually",
                                       "Unresolved obligations increase delay probability", 0.8)],
            "uncertainties": [],
        }

    def _predict_workload(self, params, svc, exec_intel, learn_intel):
        tenant_id = params.tenant_id
        all_execs = [e for e in svc._execs.values() if e.tenant_id == tenant_id]
        active = [e for e in all_execs if e.state == ExecState.ACTIVE]
        blocked = [e for e in all_execs if e.state == ExecState.BLOCKED]
        future = len(all_execs) - len(active) - len(blocked)
        return {
            "output": {
                "current_active": len(active),
                "current_blocked": len(blocked),
                "total_executions": len(all_execs),
                "estimated_peak": max(len(active), len(active) + future // 2),
            },
            "evidence_traces": [
                EvidenceTrace("execution", f"active={len(active)}", "ExecutionService"),
                EvidenceTrace("execution", f"blocked={len(blocked)}", "ExecutionService"),
            ],
            "assumptions": [Assumption("Current execution rate is representative",
                                       "Workload may increase with new commitments", 0.7)],
            "uncertainties": [],
        }

    def _predict_capacity(self, params, svc, exec_intel, learn_intel):
        tenant_id = params.tenant_id
        all_execs = [e for e in svc._execs.values() if e.tenant_id == tenant_id]
        allocs = list(svc._allocs.values())
        cons = list(svc._cons.values())
        total_budget = sum(a.quantity for a in allocs if a.unit == "USD")
        total_spent = sum(c.quantity for c in cons if c.unit == "USD")
        utilization = total_spent / total_budget if total_budget > 0 else 0.0
        return {
            "output": {
                "resource_utilization_pct": round(utilization * 100, 1),
                "total_allocated": round(total_budget, 2),
                "total_consumed": round(total_spent, 2),
                "remaining": round(total_budget - total_spent, 2),
                "active_executions": len(all_execs),
                "capacity_status": "available" if utilization < 0.8 else "limited" if utilization < 0.95 else "exhausted",
            },
            "evidence_traces": [
                EvidenceTrace("resources", f"utilization={utilization:.1%}", f"{total_spent:.0f}/{total_budget:.0f}"),
            ],
            "assumptions": [Assumption("Resource consumption rate is stable",
                                       "Sudden spikes may exceed predictions", 0.75)],
            "uncertainties": [],
        }

    def _predict_bottleneck(self, params, svc, exec_intel, learn_intel):
        inst = svc._execs.get(params.entity_id)
        if not inst:
            return {"output": {"error": "execution_not_found"}, "evidence_traces": []}
        obls = [o for o in svc._obls.values() if o.exec_id == inst.exec_id]
        blocked = [o for o in obls if o.state == ObligationState.BLOCKED]
        pending = [o for o in obls if o.state == ObligationState.PENDING]
        bottleneck = None
        if blocked:
            bottleneck = blocked[0]
        elif pending:
            bottleneck = pending[0]
        return {
            "output": {
                "bottleneck_obl_id": bottleneck.obl_id[:16] if bottleneck else None,
                "bottleneck_type": bottleneck.obl_type if bottleneck else None,
                "blocked_count": len(blocked),
                "pending_count": len(pending),
                "total_obligations": len(obls),
            },
            "evidence_traces": [
                EvidenceTrace("dependencies", f"blocked={len(blocked)}", f"{len(blocked)} blocked obligations"),
            ],
            "assumptions": [],
            "uncertainties": [],
        }

    def _predict_dependency(self, params, svc, exec_intel, learn_intel):
        inst = svc._execs.get(params.entity_id)
        if not inst:
            return {"output": {"error": "execution_not_found"}, "evidence_traces": []}
        obls = [o for o in svc._obls.values() if o.exec_id == inst.exec_id]
        total_deps = sum(len(o.dependencies) for o in obls)
        satisfied_deps = 0
        for o in obls:
            for dep_id in o.dependencies:
                dep = svc._obls.get(dep_id)
                if dep and dep.state == ObligationState.SATISFIED:
                    satisfied_deps += 1
        sat_prob = satisfied_deps / total_deps if total_deps > 0 else 1.0
        return {
            "output": {
                "satisfaction_probability": round(sat_prob, 4),
                "total_dependencies": total_deps,
                "satisfied_dependencies": satisfied_deps,
                "unsatisfied_dependencies": total_deps - satisfied_deps,
                "critical_chain_length": len([o for o in obls if o.dependencies]),
            },
            "evidence_traces": [
                EvidenceTrace("dependencies", f"sat={satisfied_deps}/{total_deps}", "DependencyGraph"),
            ],
            "assumptions": [],
            "uncertainties": [],
        }

    def _predict_org_impact(self, params, svc, exec_intel, learn_intel):
        inst = svc._execs.get(params.entity_id)
        if not inst:
            return {"output": {"error": "execution_not_found"}, "evidence_traces": []}
        obls = [o for o in svc._obls.values() if o.exec_id == inst.exec_id]
        failed_obls = [o for o in obls if o.state == ObligationState.FAILED]
        resource_impact = "low"
        if inst.state == ExecState.BLOCKED:
            resource_impact = "medium"
        elif inst.state == ExecState.FAILED or len(failed_obls) > 0:
            resource_impact = "high"
        return {
            "output": {
                "organizational_impact": resource_impact,
                "failed_obligations": len(failed_obls),
                "total_obligations": len(obls),
                "execution_state": inst.state,
            },
            "evidence_traces": [
                EvidenceTrace("execution", f"state={inst.state}", "BusinessExecutionInstance"),
            ],
            "assumptions": [],
            "uncertainties": [],
        }

    def _predict_opportunity(self, params, svc, exec_intel, learn_intel):
        patterns = learn_intel.get_patterns(params.tenant_id) if learn_intel else []
        high_patterns = [p for p in patterns if p.strength in ("strong", "moderate")]
        opportunities = []
        for p in high_patterns[:5]:
            opportunities.append({
                "pattern_id": p.pattern_id[:16],
                "name": p.name,
                "success_rate": round(p.frequency / max(p.frequency, 1), 4),
                "confidence": round(p.confidence, 4),
            })
        return {
            "output": {
                "opportunities": opportunities,
                "total_patterns_available": len(high_patterns),
            },
            "evidence_traces": [
                EvidenceTrace("learning", f"patterns={len(high_patterns)}", "PatternRecognitionEngine"),
            ],
            "assumptions": [Assumption("Historical patterns are representative",
                                       "Past success does not guarantee future results", 0.8)],
            "uncertainties": [],
        }

    def _predict_recommendation(self, params, svc, exec_intel, learn_intel):
        inst = svc._execs.get(params.entity_id)
        if not inst:
            return {"output": {"error": "execution_not_found"}, "evidence_traces": []}
        actions = exec_intel.next_actions(inst, svc) if exec_intel else []
        recs = []
        for a in actions[:5]:
            ref = learn_intel.runtime.recommendations.get_recommendation(
                a.action_type, a.exec_id, inst.tenant_id) if learn_intel else None
            hist_rate = ref.historical_success_rate if ref else None
            recs.append({
                "action_type": a.action_type,
                "description": a.description[:60],
                "predicted_success_rate": round(hist_rate, 4) if hist_rate else None,
                "historical_count": ref.historical_count if ref else 0,
                "priority": a.priority,
            })
        return {
            "output": {
                "recommended_actions": recs,
                "total_actions_available": len(actions),
            },
            "evidence_traces": [
                EvidenceTrace("intelligence", f"actions={len(actions)}", "NextActionEngine"),
            ],
            "assumptions": [],
            "uncertainties": [],
        }

    # --- Confidence computation (5-factor decomposition) ---

    def _compute_confidence(self, result: dict,
                            params: PredictionParameters) -> ConfidenceDecomposition:
        hist = result.get("output", {}).get("historical_avg_seconds")
        sample_count = min(50, abs(hist or 0) // 3600) if hist else 0
        patterns = result.get("output", {}).get("opportunities", [])
        pattern_count = len(patterns) if isinstance(patterns, list) else 0
        consistency_val = min(1.0, pattern_count * 0.2) if pattern_count else 0.5

        factors = [
            CFModel(name=ConfidenceFactorName.SAMPLE_SIZE.value,
                    value=min(1.0, sample_count / 50), weight=0.25,
                    contribution=0.0, detail=f"{sample_count} samples"),
            CFModel(name=ConfidenceFactorName.CONSISTENCY.value,
                    value=consistency_val, weight=0.25, contribution=0.0,
                    detail=f"consistency={consistency_val:.2f}"),
            CFModel(name=ConfidenceFactorName.FRESHNESS.value,
                    value=1.0, weight=0.20, contribution=0.0,
                    detail="inputs current"),
            CFModel(name=ConfidenceFactorName.EVIDENCE_QUALITY.value,
                    value=0.8, weight=0.15, contribution=0.0,
                    detail="evidence quality 0.80"),
            CFModel(name=ConfidenceFactorName.TEMPORAL_PROXIMITY.value,
                    value=max(0.1, 1.0 - params.horizon_hours / params.max_horizon_hours),
                    weight=0.15, contribution=0.0,
                    detail=f"horizon {params.horizon_hours}h"),
        ]
        for f in factors:
            f.contribution = f.value * f.weight
        overall = sum(f.contribution for f in factors)
        return ConfidenceDecomposition(overall=round(overall, 4), factors=factors)

    def _check_refusal(self, result: dict, params: PredictionParameters
                       ) -> Optional[PredictionRefusal]:
        output = result.get("output", {})
        if output.get("error") == "execution_not_found":
            return PredictionRefusal(reason="execution_not_found",
                                     detail=f"Entity {params.entity_id} not found")
        return None

    def _refuse(self, params, reason, detail) -> PredictionRecord:
        refusal = PredictionRefusal(reason=reason, detail=detail)
        d = refusal.to_dict()
        d["_refused"] = True
        return PredictionRecord(
            params=params, output=d,
            status=PredictionStatus.PENDING.value,
        )

    def _parse_dt(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None


# =========================================================================
# 2. Simulation Engine
# =========================================================================

class SimulationEngine:
    """Isolated simulation runtime.

    Simulations execute on forked (deep-copied) execution state.
    No simulation may modify canonical runtime state.
    """

    def __init__(self, config: Optional[PredictionConfig] = None):
        self._config = config or PredictionConfig()
        self._forks: Dict[str, SimulationFork] = {}
        self._results: Dict[str, SimulationResult] = {}

    def simulate(self, inp: SimulationInput,
                 exec_service: ExecutionService,
                 exec_intel: ExecutionIntelligenceEngine,
                 learn_intel: LearningIntelligenceEngine,
                 pred_engine: PredictionEngine) -> SimulationResult:
        """Run a simulation on forked execution state."""
        fork = self._create_fork(inp, exec_service)
        fork_svc = copy.deepcopy(exec_service)

        # Apply modifications to forked state
        for exec_id, mods in inp.modifications.items():
            inst = fork_svc._execs.get(exec_id)
            if inst:
                for field, value in mods.items():
                    if hasattr(inst, field):
                        setattr(inst, field, value)

        # Run predictions on forked state
        predictions = {}
        for exec_id in inp.query_exec_ids or list(fork_svc._execs.keys())[:10]:
            for cat in [PredictionCategory.COMPLETION, PredictionCategory.DELAY,
                        PredictionCategory.BOTTLENECK, PredictionCategory.DEPENDENCY]:
                params = PredictionParameters(
                    category=cat.value, entity_type="execution",
                    entity_id=exec_id, tenant_id=inp.tenant_id,
                )
                record = pred_engine.predict(params, fork_svc, exec_intel, learn_intel)
                if record.output and not record.output.get("_refused"):
                    predictions[f"{cat.value}_{exec_id[:8]}"] = record.output

        result = SimulationResult(
            simulation_type=inp.simulation_type,
            tenant_id=inp.tenant_id, label=inp.label,
            forks=[fork], predictions=predictions,
            assumptions=inp.assumptions,
            execution_count=len(fork_svc._execs),
        )
        self._results[result.simulation_id] = result
        return result

    def _create_fork(self, inp: SimulationInput,
                     exec_service: ExecutionService) -> SimulationFork:
        """Create a simulation fork (records which execs are modified)."""
        modified = list(inp.modifications.keys())
        fork = SimulationFork(
            tenant_id=inp.tenant_id, label=inp.label or "simulation",
            modified_exec_ids=modified,
        )
        self._forks[fork.fork_id] = fork
        return fork

    def get_result(self, simulation_id: str) -> Optional[SimulationResult]:
        return self._results.get(simulation_id)


# =========================================================================
# 3. Scenario Comparator
# =========================================================================

class ScenarioComparator:
    """Compare multiple simulation scenarios and rank them."""

    def compare(self, branches: List[ScenarioBranch]) -> ScenarioComparison:
        if not branches:
            return ScenarioComparison()
        tenant_id = branches[0].tenant_id if hasattr(branches[0], 'tenant_id') else 0
        rankings = []
        for b in branches:
            score = 0.0
            reasons = []
            for ptype, pdata in b.predictions.items():
                if "completion_ratio" in pdata:
                    score += pdata.get("completion_ratio", 0) * 10
                if "delay_probability" in pdata:
                    score -= pdata.get("delay_probability", 0) * 10
                if "predicted_remaining_seconds" in pdata:
                    remaining = pdata["predicted_remaining_seconds"]
                    if remaining:
                        score -= remaining / 3600
            rankings.append({
                "branch_id": b.branch_id,
                "label": b.label,
                "score": round(score, 2),
                "reasons": reasons,
                "prediction_count": len(b.predictions),
            })
        rankings.sort(key=lambda r: r["score"], reverse=True)
        return ScenarioComparison(
            branches=branches, rankings=rankings,
        )


# =========================================================================
# 4. Prediction Lifecycle
# =========================================================================

class PredictionLifecycle:
    """Manage prediction lifecycle: creation, revision, expiration,
    supersession, withdrawal, and historical lookup."""

    def __init__(self, config: Optional[PredictionConfig] = None):
        self._config = config or PredictionConfig()
        self._records: Dict[str, PredictionRecord] = {}

    def store(self, record: PredictionRecord) -> PredictionRecord:
        existing = self._find_active(record.params)
        if existing:
            existing.status = PredictionStatus.SUPERSEDED.value
            existing.superseded_by = record.prediction_id
            record.version = existing.version + 1
        self._records[record.prediction_id] = record
        return record

    def get(self, prediction_id: str) -> Optional[PredictionRecord]:
        return self._records.get(prediction_id)

    def get_active(self, params: PredictionParameters) -> Optional[PredictionRecord]:
        return self._find_active(params)

    def get_history(self, entity_type: str, entity_id: str,
                    tenant_id: int) -> List[PredictionRecord]:
        return [r for r in self._records.values()
                if r.params and r.params.entity_type == entity_type
                and r.params.entity_id == entity_id
                and r.params.tenant_id == tenant_id]

    def withdraw(self, prediction_id: str, reason: str) -> bool:
        rec = self._records.get(prediction_id)
        if rec and rec.status == PredictionStatus.ACTIVE.value:
            rec.status = PredictionStatus.WITHDRAWN.value
            rec.withdrawn_reason = reason
            return True
        return False

    def expire_all(self) -> int:
        now = datetime.now(timezone.utc)
        count = 0
        for rec in self._records.values():
            if rec.status == PredictionStatus.ACTIVE.value and rec.valid_until:
                try:
                    vu = datetime.fromisoformat(rec.valid_until)
                    if vu.tzinfo is None:
                        vu = vu.replace(tzinfo=timezone.utc)
                    if vu < now:
                        rec.status = PredictionStatus.EXPIRED.value
                        count += 1
                except (ValueError, TypeError):
                    pass
        return count

    def _find_active(self, params) -> Optional[PredictionRecord]:
        if not params:
            return None
        for rec in self._records.values():
            if rec.status == PredictionStatus.ACTIVE.value and rec.params:
                if (rec.params.category == params.category
                        and rec.params.entity_id == params.entity_id
                        and rec.params.tenant_id == params.tenant_id):
                    return rec
        return None

    def get_all(self, tenant_id: Optional[int] = None,
                category: Optional[str] = None,
                status: Optional[str] = None,
                limit: int = 50) -> List[PredictionRecord]:
        results = list(self._records.values())
        if tenant_id is not None:
            results = [r for r in results if r.params and r.params.tenant_id == tenant_id]
        if category:
            results = [r for r in results if r.params and r.params.category == category]
        if status:
            results = [r for r in results if r.status == status]
        return sorted(results, key=lambda r: r.created_at, reverse=True)[:limit]


# =========================================================================
# 5. Prediction Explainability
# =========================================================================

class PredictionExplainability:
    """Generate structured explanations for predictions."""

    def explain(self, record: PredictionRecord) -> PredictionExplanation:
        conclusion = self._build_conclusion(record)
        return PredictionExplanation(
            prediction_id=record.prediction_id,
            type=record.params.category if record.params else "",
            conclusion=conclusion,
            why=self._build_why(record),
            evidence_traces=record.evidence_traces,
            assumptions=record.assumptions,
            uncertainties=record.uncertainties,
            confidence_decomposition=record.confidence,
        )

    def _build_conclusion(self, record: PredictionRecord) -> str:
        output = record.output
        cat = record.params.category if record.params else ""
        if cat == PredictionCategory.COMPLETION.value and "predicted_at" in output:
            return f"Predicted completion by {output['predicted_at'][:19]}"
        if cat == PredictionCategory.DELAY.value and "delay_probability" in output:
            pct = output.get("delay_probability", 0) * 100
            hrs = output.get("expected_delay_hours", 0)
            return f"Delay probability: {pct:.0f}%, expected {hrs:.0f}h"
        if cat == PredictionCategory.WORKLOAD.value:
            return f"Predicted peak workload: {output.get('estimated_peak', '?')} active executions"
        if cat == PredictionCategory.CAPACITY.value:
            return f"Resource utilization: {output.get('resource_utilization_pct', '?')}%"
        return f"Prediction: {cat}"

    def _build_why(self, record: PredictionRecord) -> str:
        traces = record.evidence_traces
        if not traces:
            return "Based on current execution state"
        return "; ".join(f"{t.claim}" for t in traces[:3])


# =========================================================================
# 6. Prediction Audit
# =========================================================================

class PredictionAudit:
    """Immutable audit trail for prediction lifecycle events."""

    def __init__(self):
        self._entries: List[PredictionAuditEntry] = []

    def record(self, prediction_id: str, event: str,
               snapshot: dict, reason: str = "") -> PredictionAuditEntry:
        entry = PredictionAuditEntry(
            prediction_id=prediction_id, event=event,
            snapshot=snapshot, reason=reason,
        )
        self._entries.append(entry)
        return entry

    def get_history(self, prediction_id: str) -> List[PredictionAuditEntry]:
        return [e for e in self._entries if e.prediction_id == prediction_id]

    def get_all(self, limit: int = 100) -> List[PredictionAuditEntry]:
        return list(reversed(self._entries))[:limit]

    @property
    def size(self) -> int:
        return len(self._entries)


# =========================================================================
# 7. Runtime Service
# =========================================================================

class RuntimeService:
    """Coordination layer for all Prediction & Simulation engines."""

    def __init__(self, config: Optional[PredictionConfig] = None):
        self._config = config or PredictionConfig()
        self._prediction_eng = PredictionEngine(config)
        self._simulation_eng = SimulationEngine(config)
        self._comparator = ScenarioComparator()
        self._lifecycle = PredictionLifecycle(config)
        self._explain = PredictionExplainability()
        self._audit = PredictionAudit()

    @property
    def prediction(self) -> PredictionEngine:
        return self._prediction_eng
    @property
    def simulation(self) -> SimulationEngine:
        return self._simulation_eng
    @property
    def comparator(self) -> ScenarioComparator:
        return self._comparator
    @property
    def lifecycle(self) -> PredictionLifecycle:
        return self._lifecycle
    @property
    def explainability(self) -> PredictionExplainability:
        return self._explain
    @property
    def audit(self) -> PredictionAudit:
        return self._audit

    def predict(self, category: str, entity_type: str, entity_id: str,
                tenant_id: int, horizon_hours: float = 72.0,
                exec_service: Optional[ExecutionService] = None,
                exec_intel: Optional[ExecutionIntelligenceEngine] = None,
                learn_intel: Optional[LearningIntelligenceEngine] = None) -> Dict[str, Any]:
        _svc = exec_service or ExecutionService()
        _ei = exec_intel or get_execution_intelligence()
        _li = learn_intel or get_learning_intelligence()
        params = PredictionParameters(
            category=category, entity_type=entity_type,
            entity_id=entity_id, tenant_id=tenant_id,
            horizon_hours=horizon_hours,
        )
        record = self._prediction_eng.predict(params, _svc, _ei, _li)
        stored = self._lifecycle.store(record)
        ref = self._audit.record(record.prediction_id, "created", record.to_dict())
        return record.to_dict()

    def simulate(self, label: str, modifications: dict,
                 tenant_id: int, query_ids: Optional[List[str]] = None,
                 exec_service=None, exec_intel=None, learn_intel=None) -> Dict[str, Any]:
        inp = SimulationInput(tenant_id=tenant_id, label=label,
                              modifications=modifications,
                              query_exec_ids=query_ids or [])
        _svc = exec_service or ExecutionService()
        _ei = exec_intel or get_execution_intelligence()
        _li = learn_intel or get_learning_intelligence()
        result = self._simulation_eng.simulate(inp, _svc, _ei, _li, self._prediction_eng)
        return result.to_dict()

    def compare_scenarios(self, branches: List[ScenarioBranch]) -> Dict[str, Any]:
        return self._comparator.compare(branches).to_dict()

    def get_prediction(self, prediction_id: str) -> Optional[Dict[str, Any]]:
        rec = self._lifecycle.get(prediction_id)
        return rec.to_dict() if rec else None

    def get_active_prediction(self, category: str, entity_id: str,
                               tenant_id: int) -> Optional[Dict[str, Any]]:
        p = PredictionParameters(category=category, entity_type="execution",
                                 entity_id=entity_id, tenant_id=tenant_id)
        rec = self._lifecycle.get_active(p)
        return rec.to_dict() if rec else None

    def get_prediction_history(self, entity_id: str, tenant_id: int) -> List[Dict[str, Any]]:
        recs = self._lifecycle.get_history("execution", entity_id, tenant_id)
        return [r.to_dict() for r in recs]

    def withdraw_prediction(self, prediction_id: str, reason: str) -> bool:
        ok = self._lifecycle.withdraw(prediction_id, reason)
        if ok:
            self._audit.record(prediction_id, "withdrawn",
                               {"reason": reason}, reason)
        return ok

    def explain_prediction(self, prediction_id: str) -> Dict[str, Any]:
        rec = self._lifecycle.get(prediction_id)
        if not rec:
            return {"error": "not_found"}
        return self._explain.explain(rec).to_dict()

    def expire_predictions(self) -> int:
        return self._lifecycle.expire_all()

    def get_history(self, tenant_id: Optional[int] = None,
                    category: Optional[str] = None,
                    status: Optional[str] = None,
                    limit: int = 50) -> List[Dict[str, Any]]:
        recs = self._lifecycle.get_all(tenant_id, category, status, limit)
        return [r.to_dict() for r in recs]

    def stats(self) -> Dict[str, Any]:
        all_recs = self._lifecycle.get_all()
        stats = PredictionStats(
            total_predictions=len(all_recs),
            active_predictions=sum(1 for r in all_recs if r.status == PredictionStatus.ACTIVE.value),
            expired_predictions=sum(1 for r in all_recs if r.status == PredictionStatus.EXPIRED.value),
            superseded_predictions=sum(1 for r in all_recs if r.status == PredictionStatus.SUPERSEDED.value),
            withdrawn_predictions=sum(1 for r in all_recs if r.status == PredictionStatus.WITHDRAWN.value),
            total_simulations=len(self._simulation_eng._results),
            audit_log_size=self._audit.size,
            predictions_by_category=defaultdict(int, **{
                r.params.category: sum(1 for r2 in all_recs if r2.params and r2.params.category == r.params.category)
                for r in all_recs if r.params
            }),
        )
        return stats.to_dict()


# =========================================================================
# Facade
# =========================================================================

class PredictionAndSimulationEngine:
    """Facade over all Prediction & Simulation components.

    Usage:
        ps = PredictionAndSimulationEngine()
        result = ps.predict("completion", "execution", "e1", 1)
        sim = ps.simulate("what_if", {"e1": {"state": "active"}}, 1)
    """

    def __init__(self, config: Optional[PredictionConfig] = None):
        self._runtime = RuntimeService(config)

    @property
    def runtime(self) -> RuntimeService:
        return self._runtime

    def predict(self, category: str, entity_type: str, entity_id: str,
                tenant_id: int, **kw) -> Dict[str, Any]:
        return self._runtime.predict(category, entity_type, entity_id, tenant_id, **kw)

    def simulate(self, label: str, modifications: dict,
                 tenant_id: int, **kw) -> Dict[str, Any]:
        return self._runtime.simulate(label, modifications, tenant_id, **kw)

    def compare_scenarios(self, branches: List[ScenarioBranch]) -> Dict[str, Any]:
        return self._runtime.compare_scenarios(branches)

    def get_prediction(self, prediction_id: str) -> Optional[Dict[str, Any]]:
        return self._runtime.get_prediction(prediction_id)

    def get_active_prediction(self, category: str, entity_id: str,
                               tenant_id: int) -> Optional[Dict[str, Any]]:
        return self._runtime.get_active_prediction(category, entity_id, tenant_id)

    def get_prediction_history(self, entity_id: str, tenant_id: int) -> List[Dict[str, Any]]:
        return self._runtime.get_prediction_history(entity_id, tenant_id)

    def withdraw_prediction(self, prediction_id: str, reason: str) -> bool:
        return self._runtime.withdraw_prediction(prediction_id, reason)

    def explain_prediction(self, prediction_id: str) -> Dict[str, Any]:
        return self._runtime.explain_prediction(prediction_id)

    def expire_predictions(self) -> int:
        return self._runtime.expire_predictions()

    def get_history(self, **kw) -> List[Dict[str, Any]]:
        return self._runtime.get_history(**kw)

    def stats(self) -> Dict[str, Any]:
        return self._runtime.stats()