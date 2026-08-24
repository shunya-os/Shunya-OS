"""
SHUNYA — Closed Learning Loop (Phase 15, computation-only)
"""
import hashlib, json
from datetime import datetime, timezone
from typing import Optional

# Learning target states
class TargetState:
    ACTIVE = "active"
    DISABLED = "disabled"

# Outcome types
class OutcomeType:
    QUANTITATIVE = "quantitative"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    TEMPORAL = "temporal"
    STATE_TRANSITION = "state_transition"

# Attribution states
class AttributionState:
    DIRECT_WORKFLOW = "directly_linked_by_workflow"
    STRONG = "strongly_attributable"
    PLAUSIBLE = "plausibly_attributable"
    CORRELATED = "correlated"
    DISPUTED = "disputed"
    UNKNOWN = "unknown"
    NOT_ATTRIBUTABLE = "not_attributable"

# Evaluation status
class EvalStatus:
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"

# Learning signal states
class SignalState:
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    INVALIDATED = "invalidated"


class LearningTarget:
    def __init__(self, target_id: str, tenant_id: int, name: str,
                 outcome_types: Optional[list] = None,
                 status: str = TargetState.ACTIVE,
                 provenance: Optional[str] = None):
        self.target_id = target_id
        self.tenant_id = tenant_id
        self.name = name
        self.outcome_types = set(outcome_types or [])
        self.status = status
        self.provenance = provenance

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "outcome_types": list(self.outcome_types),
            "status": self.status,
        }


class OutcomeObservation:
    def __init__(self, observation_id: str, target_id: str, tenant_id: int,
                 outcome_type: str, value, observed_at: str,
                 evidence_source: str, evidence_id: str,
                 trust: str = "verified",
                 recorded_at: Optional[str] = None,
                 sensitivity: str = "public",
                 provenance: Optional[str] = None):
        self.observation_id = observation_id
        self.target_id = target_id
        self.tenant_id = tenant_id
        self.outcome_type = outcome_type
        self.value = value
        self.observed_at = observed_at
        self.recorded_at = recorded_at or datetime.now(timezone.utc).isoformat()
        self.evidence_source = evidence_source
        self.evidence_id = evidence_id
        self.trust = trust
        self.sensitivity = sensitivity
        self.provenance = provenance
        self.superseded_at = None

    def to_dict(self) -> dict:
        return {
            "observation_id": self.observation_id,
            "target_id": self.target_id,
            "tenant_id": self.tenant_id,
            "outcome_type": self.outcome_type,
            "value": self.value,
            "observed_at": self.observed_at,
            "recorded_at": self.recorded_at,
            "evidence_source": self.evidence_source,
            "evidence_id": self.evidence_id,
            "trust": self.trust,
            "sensitivity": self.sensitivity,
        }


class ExpectationCriterion:
    def __init__(self, criterion_id: str, version: int, target_id: str,
                 metric_type: str, operator: str, threshold,
                 evaluation_class: str = "deterministic",
                 provenance: Optional[str] = None):
        self.criterion_id = criterion_id
        self.version = version
        self.target_id = target_id
        self.metric_type = metric_type
        self.operator = operator
        self.threshold = threshold
        self.evaluation_class = evaluation_class
        self.provenance = provenance

    def to_dict(self) -> dict:
        return {
            "criterion_id": self.criterion_id,
            "version": self.version,
            "target_id": self.target_id,
            "metric_type": self.metric_type,
            "operator": self.operator,
            "threshold": self.threshold,
            "evaluation_class": self.evaluation_class,
        }


class LearningSignal:
    def __init__(self, signal_id: str, target_id: str, tenant_id: int,
                 direction: str, strength: float, confidence: float,
                 sample_count: int, observation_window: str,
                 condition_signature: str,
                 state: str = SignalState.ACTIVE,
                 provenance: Optional[str] = None,
                 sensitivity: str = "public"):
        self.signal_id = signal_id
        self.target_id = target_id
        self.tenant_id = tenant_id
        self.direction = direction
        self.strength = strength
        self.confidence = confidence
        self.sample_count = sample_count
        self.observation_window = observation_window
        self.condition_signature = condition_signature
        self.state = state
        self.provenance = provenance
        self.sensitivity = sensitivity
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.superseded_at = None

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "target_id": self.target_id,
            "tenant_id": self.tenant_id,
            "direction": self.direction,
            "strength": self.strength,
            "confidence": self.confidence,
            "sample_count": self.sample_count,
            "observation_window": self.observation_window,
            "condition_signature": self.condition_signature,
            "state": self.state,
            "generated_at": self.generated_at,
        }


class ClosedLearningLoop:
    """Phase 15 — Closed Learning Loop.

    SHUNYA learns from evidenced outcomes.
    SHUNYA does not silently rewrite truth, policy, code, permissions, or model placement.
    """

    def __init__(self):
        self._targets: dict[str, LearningTarget] = {}
        self._observations: dict[str, OutcomeObservation] = {}
        self._criteria: dict[str, list[ExpectationCriterion]] = {}  # target_id → versioned criteria
        self._signals: dict[str, LearningSignal] = {}
        self._idempotency: set[str] = set()
        self._evaluation_history: list[dict] = []
        self._version = "15.1"

    # ------------------------------------------------------------------
    # Learning Target
    # ------------------------------------------------------------------
    def register_target(self, target: LearningTarget) -> dict:
        self._targets[target.target_id] = target
        return {"registered": True, "target_id": target.target_id}

    def get_target(self, target_id: str) -> Optional[LearningTarget]:
        return self._targets.get(target_id)

    # ------------------------------------------------------------------
    # Outcome Observation
    # ------------------------------------------------------------------
    def record_outcome(self, target_id: str, tenant_id: int,
                       outcome_type: str, value,
                       evidence_source: str, evidence_id: str,
                       observed_at: Optional[str] = None,
                       trust: str = "verified",
                       idempotency_key: Optional[str] = None,
                       provenance: Optional[str] = None) -> dict:
        # Target validation
        target = self._targets.get(target_id)
        if target is None:
            return self._error("learning_target_unknown", tenant_id)
        if target.status != TargetState.ACTIVE:
            return self._error("learning_target_disabled", tenant_id)
        if target.tenant_id != tenant_id:
            return self._error("tenant_mismatch", tenant_id)

        # Idempotency
        idem = idempotency_key or hashlib.sha256(
            f"{tenant_id}:{target_id}:{evidence_id}".encode()
        ).hexdigest()[:16]
        if idem in self._idempotency:
            return {"duplicate": True, "observation_id": None, "idempotency_key": idem}
        self._idempotency.add(idem)

        obs_id = hashlib.sha256(
            f"{tenant_id}:{target_id}:{evidence_id}:{idem}".encode()
        ).hexdigest()[:16]

        obs = OutcomeObservation(
            observation_id=obs_id,
            target_id=target_id,
            tenant_id=tenant_id,
            outcome_type=outcome_type,
            value=value,
            observed_at=observed_at or datetime.now(timezone.utc).isoformat(),
            evidence_source=evidence_source,
            evidence_id=evidence_id,
            trust=trust,
            provenance=provenance,
        )
        self._observations[obs_id] = obs
        return {"observation_id": obs_id, "target_id": target_id, "idempotency_key": idem}

    # ------------------------------------------------------------------
    # Expectation Criterion
    # ------------------------------------------------------------------
    def register_criterion(self, criterion: ExpectationCriterion) -> dict:
        tid = criterion.target_id
        if tid not in self._criteria:
            self._criteria[tid] = []
        # Check duplicate version
        for existing in self._criteria[tid]:
            if existing.version == criterion.version:
                return self._error("duplicate_criterion_version", criterion.target_id)
        self._criteria[tid].append(criterion)
        self._criteria[tid].sort(key=lambda c: c.version, reverse=True)
        return {"registered": True, "criterion_id": criterion.criterion_id, "version": criterion.version}

    # ------------------------------------------------------------------
    # Evaluation Engine (deterministic)
    # ------------------------------------------------------------------
    def evaluate(self, target_id: str, criterion_version: int,
                 observations: list[str],
                 tenant_id: int = 1) -> dict:
        target = self._targets.get(target_id)
        if target is None:
            return self._error("learning_target_unknown", tenant_id)

        # Find the requested criterion version
        criterion = None
        criteria_list = self._criteria.get(target_id, [])
        for c in criteria_list:
            if c.version == criterion_version:
                criterion = c
                break
        if criterion is None:
            return self._error("criterion_version_not_found", tenant_id)

        # Collect observations
        obs_list = []
        for oid in observations:
            obs = self._observations.get(oid)
            if obs and obs.tenant_id == tenant_id:
                obs_list.append(obs)

        if not obs_list:
            return self._error("no_observations_for_evaluation", tenant_id)

        # Deterministic evaluation
        if criterion.evaluation_class == "deterministic":
            result = self._deterministic_eval(criterion, obs_list)
        else:
            return self._error("evaluation_unsupported", tenant_id)

        eval_record = {
            "evaluation_id": hashlib.sha256(
                f"{tenant_id}:{target_id}:{criterion_version}:{len(obs_list)}:{datetime.now(timezone.utc).isoformat()}".encode()
            ).hexdigest()[:16],
            "target_id": target_id,
            "criterion_id": criterion.criterion_id,
            "criterion_version": criterion.version,
            "observations_count": len(obs_list),
            "result": result,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
        }
        self._evaluation_history.append(eval_record)
        return eval_record

    def _deterministic_eval(self, criterion: ExpectationCriterion, obs_list: list) -> dict:
        """Deterministic evaluation — no LLM involved."""
        operator = criterion.operator
        threshold = criterion.threshold
        metric_type = criterion.metric_type

        # Collect values based on metric type
        values = []
        for obs in obs_list:
            if obs.outcome_type == OutcomeType.QUANTITATIVE:
                values.append(float(obs.value))
            elif obs.outcome_type == OutcomeType.BOOLEAN:
                values.append(obs.value)
            elif obs.outcome_type == OutcomeType.TEMPORAL:
                values.append(obs.value)
            elif obs.outcome_type == OutcomeType.CATEGORICAL:
                pass  # Handled per-case

        if metric_type == "count":
            if operator == "gte":
                passed = len(values) >= int(threshold)
            elif operator == "lte":
                passed = len(values) <= int(threshold)
            elif operator == "eq":
                passed = len(values) == int(threshold)
            else:
                return {"status": EvalStatus.ERROR, "reason": f"unsupported_operator:{operator}"}
            return {"status": EvalStatus.PASS if passed else EvalStatus.FAIL,
                    "value": len(values), "threshold": threshold}

        elif metric_type == "average":
            if not values:
                return {"status": EvalStatus.INCONCLUSIVE, "reason": "no_values"}
            avg = sum(values) / len(values)
            if operator == "gte":
                passed = avg >= float(threshold)
            elif operator == "lte":
                passed = avg <= float(threshold)
            else:
                return {"status": EvalStatus.ERROR, "reason": f"unsupported_operator:{operator}"}
            return {"status": EvalStatus.PASS if passed else EvalStatus.FAIL,
                    "value": avg, "threshold": threshold}

        elif metric_type == "boolean":
            true_count = sum(1 for v in values if v is True)
            false_count = sum(1 for v in values if v is False)
            if operator == "gte":  # At least threshold true
                passed = true_count >= int(threshold)
            else:
                passed = true_count > false_count
            return {"status": EvalStatus.PASS if passed else EvalStatus.FAIL,
                    "true_count": true_count, "false_count": false_count}

        return {"status": EvalStatus.ERROR, "reason": "unsupported_metric"}

    # ------------------------------------------------------------------
    # Learning Signal
    # ------------------------------------------------------------------
    def generate_signal(self, target_id: str, tenant_id: int,
                        condition_signature: str,
                        evaluation_ids: Optional[list] = None,
                        provenance: Optional[str] = None) -> dict:
        # Collect relevant evaluations
        evals = [e for e in self._evaluation_history
                 if e["target_id"] == target_id and e["tenant_id"] == tenant_id]
        if evaluation_ids:
            evals = [e for e in evals if e["evaluation_id"] in evaluation_ids]

        if not evals:
            return self._error("no_evaluations_for_signal", tenant_id)

        # Compute signal from evaluations
        total_observations = 0
        pass_count = 0
        for e in evals:
            total_observations += e.get("observations_count", 0)
            result = e.get("result", {})
            if result.get("status") == EvalStatus.PASS:
                pass_count += 1
        fail_count = len(evals) - pass_count
        total = total_observations or len(evals)

        if total < 2:
            return self._error("insufficient_evidence", tenant_id)
        if pass_count > fail_count:
            direction = "positive"
        elif fail_count > pass_count:
            direction = "negative"
        else:
            direction = "mixed"

        strength = pass_count / total if total > 0 else 0.0
        # Confidence: more samples = higher confidence, but bounded
        confidence = min(0.95, max(0.1, (total / 10) * 0.5 + 0.5))

        signal_id = hashlib.sha256(
            f"{tenant_id}:{target_id}:{condition_signature}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]

        signal = LearningSignal(
            signal_id=signal_id,
            target_id=target_id,
            tenant_id=tenant_id,
            direction=direction,
            strength=strength,
            confidence=confidence,
            sample_count=total,
            observation_window=f"{total}_samples",
            condition_signature=condition_signature,
            state=SignalState.ACTIVE,
            provenance=provenance,
        )
        self._signals[signal_id] = signal
        return signal.to_dict()

    # ------------------------------------------------------------------
    # Correction / Invalidation
    # ------------------------------------------------------------------
    def invalidate_observation(self, observation_id: str, tenant_id: int) -> dict:
        obs = self._observations.get(observation_id)
        if obs is None:
            return self._error("observation_not_found", tenant_id)
        if obs.tenant_id != tenant_id:
            return self._error("tenant_mismatch", tenant_id)
        obs.superseded_at = datetime.now(timezone.utc).isoformat()
        return {"invalidated": True, "observation_id": observation_id}

    # ------------------------------------------------------------------
    # Learning Policy
    # ------------------------------------------------------------------
    def check_policy(self, target_id: str, tenant_id: int,
                     min_evidence: int = 2) -> dict:
        target = self._targets.get(target_id)
        if target is None:
            return {"eligible": False, "reason": "target_unknown"}
        if target.status != TargetState.ACTIVE:
            return {"eligible": False, "reason": "target_disabled"}
        if target.tenant_id != tenant_id:
            return {"eligible": False, "reason": "tenant_mismatch"}

        # Count valid (non-superseded) observations
        valid_count = sum(1 for o in self._observations.values()
                         if o.target_id == target_id and o.tenant_id == tenant_id
                         and o.superseded_at is None)
        if valid_count < min_evidence:
            return {"eligible": True, "insufficient_evidence": True,
                    "valid_count": valid_count, "min_required": min_evidence}
        return {"eligible": True, "insufficient_evidence": False, "valid_count": valid_count}

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------
    def inspect_signal(self, signal_id: str) -> dict:
        s = self._signals.get(signal_id)
        if s is None:
            return {"error": "signal_not_found"}
        return s.to_dict()

    def list_signals(self, tenant_id: int) -> list:
        return [s.to_dict() for s in self._signals.values() if s.tenant_id == tenant_id]

    def _error(self, reason: str, tenant_id: int = 1) -> dict:
        return {"error": reason, "tenant_id": tenant_id, "timestamp": datetime.now(timezone.utc).isoformat()}