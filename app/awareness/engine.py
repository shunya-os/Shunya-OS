"""SHUNYA — Autonomous Operational Awareness engine (Phase N+3).

Eight sub-engines coordinated by the RuntimeService, all operating
deterministically on CanonicalObservation events.

No paid-model dependency. Every output traced to originating observation.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from app.awareness.models import (
    ObservationCategory, ObservationPriority, AwarenessLevel,
    PropagationTarget, ImpactType,
    CanonicalObservation, ObservationEnrichment, ImpactAssessment,
    AwarenessSnapshot, OrganizationalAwarenessState,
    PrioritizedObservation, AwarenessMemoryEntry,
    RuntimeConfig, AwarenessFilter, AwarenessStats,
)
from app.execution.constants import ExecState, ObligationState
from app.execution_engine.service import ExecutionService
from app.execution_intelligence import (
    ExecutionIntelligenceEngine, get_execution_intelligence,
    ExecutionHealthEngine, RiskDetectionEngine, NextActionEngine,
    TimelineIntelligenceEngine, DependencyGraphEngine,
    HealthAssessment, HealthStatus, RiskLevel, RiskFactor,
)

# =========================================================================
# Module-level singleton
# =========================================================================

_ENGINE_INSTANCE: Optional[AwarenessEngine] = None


def get_awareness_engine() -> AwarenessEngine:
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = AwarenessEngine()
    return _ENGINE_INSTANCE


def reset_awareness_engine() -> None:
    global _ENGINE_INSTANCE
    _ENGINE_INSTANCE = None


# =========================================================================
# 1. Observation Pipeline
# =========================================================================

class ObservationPipeline:
    """Deterministic pipeline: Ingest → Validate → Enrich → Route.

    Every observation passes through all stages. Idempotent by
    idempotency_key.
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._config = config or RuntimeConfig()
        self._seen_keys: Set[str] = set()

    def process(self, observation: CanonicalObservation) -> CanonicalObservation:
        """Process a raw observation through the full pipeline."""
        # 1. Idempotency check
        if observation.idempotency_key in self._seen_keys:
            observation.payload["_duplicate"] = True
            return observation
        self._seen_keys.add(observation.idempotency_key)

        # 2. Validate
        errors = self._validate(observation)
        if errors:
            observation.payload["_validation_errors"] = errors
            return observation

        # 3. Enrich
        enrichment = self._enrich(observation)
        observation.enrichment = enrichment

        # 4. Compute priority
        priority = self._compute_priority(observation, enrichment)
        observation.priority = priority

        return observation

    def _validate(self, obs: CanonicalObservation) -> List[str]:
        errors: List[str] = []
        if not obs.tenant_id:
            errors.append("missing_tenant_id")
        if not obs.source:
            errors.append("missing_source")
        if obs.category not in [c.value for c in ObservationCategory]:
            errors.append(f"unknown_category: {obs.category}")
        return errors

    def _enrich(self, obs: CanonicalObservation) -> ObservationEnrichment:
        targets = self._determine_targets(obs)
        return ObservationEnrichment(
            propagation_targets=targets,
            awareness_level=AwarenessLevel.PARTIAL.value,
        )

    def _determine_targets(self, obs: CanonicalObservation) -> List[str]:
        """Determine which components need this observation."""
        targets = [PropagationTarget.AWARENESS.value]
        cat = obs.category

        if cat in (ObservationCategory.EXECUTION_STATE_CHANGE.value,
                   ObservationCategory.EXECUTION_HEALTH_CHANGE.value,
                   ObservationCategory.RISK_LEVEL_CHANGE.value):
            targets.append(PropagationTarget.EXECUTION_INTELLIGENCE.value)
        if cat == ObservationCategory.EXCEPTION_OCCURRED.value:
            targets.append(PropagationTarget.MEMORY.value)
        if cat == ObservationCategory.INTELLIGENCE_OUTPUT.value:
            targets.append(PropagationTarget.PLANNER.value)

        return targets

    def _compute_priority(self, obs: CanonicalObservation,
                          enrichment: ObservationEnrichment) -> int:
        """Compute observation priority from category and content."""
        cat = obs.category
        mapping = {
            ObservationCategory.EXCEPTION_OCCURRED.value: ObservationPriority.CRITICAL,
            ObservationCategory.RISK_LEVEL_CHANGE.value: ObservationPriority.HIGH,
            ObservationCategory.EXECUTION_STATE_CHANGE.value: ObservationPriority.MEDIUM,
            ObservationCategory.EXECUTION_HEALTH_CHANGE.value: ObservationPriority.MEDIUM,
            ObservationCategory.OBLIGATION_CHANGE.value: ObservationPriority.MEDIUM,
            ObservationCategory.RESOURCE_CHANGE.value: ObservationPriority.LOW,
            ObservationCategory.INTELLIGENCE_OUTPUT.value: ObservationPriority.LOW,
            ObservationCategory.PORTFOLIO_CHANGE.value: ObservationPriority.LOW,
            ObservationCategory.TIMELINE_EVENT.value: ObservationPriority.INFO,
            ObservationCategory.EXTERNAL_SIGNAL.value: ObservationPriority.INFO,
            ObservationCategory.SYSTEM_EVENT.value: ObservationPriority.INFO,
        }
        return mapping.get(cat, ObservationPriority.INFO.value)

    @property
    def stats(self) -> Dict[str, Any]:
        return {"total_processed": len(self._seen_keys), "idempotency_hits": 0}


# =========================================================================
# 2. Change Impact Analyzer
# =========================================================================

class ChangeImpactAnalyzer:
    """Determines what each observation changes about system understanding.

    Stateless: given an observation + current state, produces an impact
    assessment. No side effects.
    """

    def assess(self, observation: CanonicalObservation,
               exec_intel: Optional[ExecutionIntelligenceEngine] = None,
               exec_service: Optional[ExecutionService] = None) -> ImpactAssessment:
        """Assess the impact of a single observation."""
        impact_types: List[str] = []
        affected_execs: List[str] = []
        description = ""

        cat = observation.category

        if cat == ObservationCategory.EXECUTION_STATE_CHANGE.value:
            impact_types.append(ImpactType.STATE_CHANGE.value)
            if observation.source_id:
                affected_execs.append(observation.source_id)
            prev = observation.previous_state or "unknown"
            curr = observation.current_state or "unknown"
            description = f"Execution {observation.source_id[:12]}: {prev} → {curr}"

        elif cat == ObservationCategory.EXECUTION_HEALTH_CHANGE.value:
            impact_types.append(ImpactType.HEALTH_CHANGE.value)
            if observation.source_id:
                affected_execs.append(observation.source_id)
            description = f"Health change for {observation.source_id[:12]}"

        elif cat == ObservationCategory.RISK_LEVEL_CHANGE.value:
            impact_types.append(ImpactType.RISK_CHANGE.value)
            if observation.source_id:
                affected_execs.append(observation.source_id)
            description = f"Risk level change for {observation.source_id[:12]}"

        elif cat == ObservationCategory.OBLIGATION_CHANGE.value:
            impact_types.append(ImpactType.STATE_CHANGE.value)
            if observation.source_id:
                # Find parent exec_id
                if exec_service:
                    for oid, obl in exec_service._obls.items():
                        if oid == observation.source_id:
                            affected_execs.append(obl.exec_id)
                            break
            description = f"Obligation {observation.source_id[:12]} changed"

        elif cat == ObservationCategory.EXCEPTION_OCCURRED.value:
            impact_types.append(ImpactType.RISK_CHANGE.value)
            impact_types.append(ImpactType.STATE_CHANGE.value)
            if observation.source_id:
                affected_execs.append(observation.source_id)
            description = f"Exception in {observation.source_id[:12]}"

        elif cat == ObservationCategory.INTELLIGENCE_OUTPUT.value:
            impact_types.append(ImpactType.RECOMMENDATION_CHANGE.value)
            description = "Intelligence output generated"

        else:
            impact_types.append(ImpactType.NO_IMPACT.value)
            description = "No significant impact"

        return ImpactAssessment(
            impact_types=impact_types,
            affected_executions=affected_execs,
            affected_tenants=[observation.tenant_id] if observation.tenant_id else [],
            description=description,
            severity=observation.category,
        )


# =========================================================================
# 3. Continuous Risk Monitor
# =========================================================================

class ContinuousRiskMonitor:
    """Background risk monitoring that updates per observation.

    Maintains a risk registry of all monitored executions and re-evaluates
    risk for any execution touched by an observation.
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._config = config or RuntimeConfig()
        self._risk_cache: Dict[str, str] = {}  # exec_id → overall_risk
        self._health_cache: Dict[str, str] = {}  # exec_id → overall_health

    def on_observation(self, observation: CanonicalObservation,
                       exec_intel: ExecutionIntelligenceEngine,
                       exec_service: ExecutionService) -> List[Dict[str, Any]]:
        """Re-evaluate risk for affected executions. Returns risk changes."""
        if not self._config.enable_risk_monitoring:
            return []

        affected = self._find_affected_execs(observation, exec_service)
        changes: List[Dict[str, Any]] = []

        for exec_id in affected:
            inst = exec_service._execs.get(exec_id)
            if not inst:
                continue
            old_risk = self._risk_cache.get(exec_id, RiskLevel.NONE.value)
            new_risk = exec_intel.assess_risk(inst, exec_service).overall_risk
            self._risk_cache[exec_id] = new_risk

            if old_risk != new_risk:
                changes.append({
                    "exec_id": exec_id,
                    "old_risk": old_risk,
                    "new_risk": new_risk,
                    "triggered_by": observation.observation_id,
                })

            # Update health cache too
            old_health = self._health_cache.get(exec_id, HealthStatus.UNKNOWN.value)
            new_health = exec_intel.assess_health(inst, exec_service).overall
            self._health_cache[exec_id] = new_health

        return changes

    def _find_affected_execs(self, obs: CanonicalObservation,
                              exec_service: ExecutionService) -> List[str]:
        """Find all executions affected by this observation.

        Queries outcomes matching the observation's source_id or identity_id.
        """
        if not obs.source_id:
            return []
        # Query outcomes by outcome_id (maps to source_id)
        try:
            from app.execution.models import Outcome
            match = Outcome.query.filter(
                Outcome.outcome_id == obs.source_id
            ).first()
            if match:
                return [match.outcome_id]
            # Fall back to identity_id match
            matches = Outcome.query.filter(
                Outcome.identity_id == obs.source_id
            ).all()
            return [m.outcome_id for m in matches]
        except Exception:
            return []

    def get_risk(self, exec_id: str) -> Optional[str]:
        return self._risk_cache.get(exec_id)

    def get_health(self, exec_id: str) -> Optional[str]:
        return self._health_cache.get(exec_id)

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "monitored_executions": len(self._risk_cache),
            "risk_levels": dict(
                (k, sum(1 for v in self._risk_cache.values() if v == k))
                for k in set(self._risk_cache.values())
            ),
        }


# =========================================================================
# 4. Organizational Awareness
# =========================================================================

class OrganizationalAwareness:
    """Per-tenant aggregated awareness state.

    Tracks which executions are monitored, how recent observations are,
    and computes overall awareness level per tenant.
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._config = config or RuntimeConfig()
        self._snapshots: Dict[str, AwarenessSnapshot] = {}  # key = f"{tenant_id}:{exec_id}"

    def update(self, observation: CanonicalObservation) -> None:
        """Update awareness state from a single observation."""
        key = f"{observation.tenant_id}:{observation.source_id}"
        snap = self._snapshots.get(key)

        if snap:
            snap.last_observation_at = observation.timestamp
            snap.observation_count += 1
            snap.level = self._compute_level(snap)
            if observation.enrichment:
                snap.enrichment = observation.enrichment
        else:
            level = AwarenessLevel.PARTIAL.value
            if observation.enrichment:
                level = observation.enrichment.awareness_level
            self._snapshots[key] = AwarenessSnapshot(
                exec_id=observation.source_id,
                tenant_id=observation.tenant_id,
                level=level,
                last_observation_at=observation.timestamp,
                observation_count=1,
                enrichment=observation.enrichment,
            )

    def get_snapshot(self, exec_id: str, tenant_id: int) -> Optional[AwarenessSnapshot]:
        return self._snapshots.get(f"{tenant_id}:{exec_id}")

    def get_tenant_state(self, tenant_id: int) -> OrganizationalAwarenessState:
        """Compute aggregated awareness for a tenant."""
        tenant_snaps = [
            s for k, s in self._snapshots.items()
            if k.startswith(f"{tenant_id}:")
        ]
        now = datetime.now(timezone.utc)

        total = len(tenant_snaps)
        monitored = sum(1 for s in tenant_snaps if s.level != AwarenessLevel.BLIND.value)
        dist: Dict[str, int] = {}
        stale = 0
        last_activity = ""

        for s in tenant_snaps:
            dist[s.level] = dist.get(s.level, 0) + 1
            if s.last_observation_at:
                try:
                    last = datetime.fromisoformat(s.last_observation_at)
                    if last.tzinfo is None:
                        last = last.replace(tzinfo=timezone.utc)
                    elapsed = (now - last).total_seconds() / 3600
                    if elapsed > self._config.stale_threshold_hours:
                        stale += 1
                except (ValueError, TypeError):
                    pass
                if s.last_observation_at > last_activity:
                    last_activity = s.last_observation_at

        # Overall awareness level
        if total == 0:
            overall = AwarenessLevel.BLIND.value
        elif monitored == 0:
            overall = AwarenessLevel.BLIND.value
        elif dist.get(AwarenessLevel.FULL.value, 0) >= total * 0.5:
            overall = AwarenessLevel.FULL.value
        elif dist.get(AwarenessLevel.STALE.value, 0) > total * 0.5:
            overall = AwarenessLevel.STALE.value
        elif dist.get(AwarenessLevel.PARTIAL.value, 0) > 0:
            overall = AwarenessLevel.PARTIAL.value
        else:
            overall = AwarenessLevel.LIMITED.value

        return OrganizationalAwarenessState(
            tenant_id=tenant_id,
            total_executions=total,
            monitored_executions=monitored,
            awareness_distribution=dist,
            overall_awareness=overall,
            last_activity_at=last_activity,
            stale_execution_count=stale,
        )

    def _compute_level(self, snap: AwarenessSnapshot) -> str:
        """Compute awareness level based on observation count and recency."""
        if snap.observation_count >= 10:
            return AwarenessLevel.FULL.value
        elif snap.observation_count >= 5:
            return AwarenessLevel.PARTIAL.value
        elif snap.observation_count >= 1:
            return AwarenessLevel.LIMITED.value
        return AwarenessLevel.BLIND.value

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "total_snapshots": len(self._snapshots),
            "unique_tenants": len(set(k.split(":")[0] for k in self._snapshots)),
        }


# =========================================================================
# 5. Event Prioritization
# =========================================================================

class EventPrioritization:
    """Priority scoring and ordering for observations.

    Stateless: given an observation, returns a PrioritizedObservation
    with a computed score and reason.
    """

    def prioritize(self, observation: CanonicalObservation) -> PrioritizedObservation:
        """Compute priority score with explanation."""
        score = observation.priority
        reasons: List[str] = []

        # Category-based scoring
        cat = observation.category
        if cat == ObservationCategory.EXCEPTION_OCCURRED.value:
            score = min(score, ObservationPriority.CRITICAL.value)
            reasons.append("exception occurred")
        elif cat == ObservationCategory.RISK_LEVEL_CHANGE.value:
            score = min(score, ObservationPriority.HIGH.value)
            reasons.append("risk level changed")

        # State transition scoring: terminal states are lower priority
        if observation.current_state in (ExecState.FULFILLED, ExecState.FAILED, ExecState.CANCELLED):
            # Terminal state is important but less urgent
            reasons.append("terminal state reached")

        # Previous state scoring: BLOCKED → anything is higher priority
        if observation.previous_state == ExecState.BLOCKED:
            score = min(score, ObservationPriority.HIGH.value)
            reasons.append("blocked execution progressed")

        reason = "; ".join(reasons) if reasons else "routine observation"
        return PrioritizedObservation(
            observation=observation,
            priority_score=score,
            reason=reason,
        )


# =========================================================================
# 6. Awareness Memory
# =========================================================================

class AwarenessMemory:
    """Ring buffer of recent observations for context and recall.

    Bounded by config.max_memory_size. Evicts oldest entries first.
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._config = config or RuntimeConfig()
        self._entries: deque[AwarenessMemoryEntry] = deque(maxlen=self._config.max_memory_size)

    def record(self, observation: CanonicalObservation) -> None:
        """Record an observation in memory."""
        entry = AwarenessMemoryEntry(
            observation_id=observation.observation_id,
            category=observation.category,
            source=observation.source,
            source_id=observation.source_id,
            tenant_id=observation.tenant_id,
            priority=observation.priority,
            timestamp=observation.timestamp,
            payload_summary=self._summarize(observation),
        )
        self._entries.append(entry)

    def recent(self, limit: int = 20, tenant_id: Optional[int] = None,
               min_priority: Optional[int] = None) -> List[AwarenessMemoryEntry]:
        """Return recent observations, filtered."""
        results = list(self._entries)
        if tenant_id is not None:
            results = [e for e in results if e.tenant_id == tenant_id]
        if min_priority is not None:
            results = [e for e in results if e.priority <= min_priority]
        return list(reversed(results))[:limit]

    def find_by_source(self, source_id: str) -> List[AwarenessMemoryEntry]:
        """Find all entries referencing a specific source entity."""
        return [e for e in self._entries if e.source_id == source_id]

    def size(self) -> int:
        return len(self._entries)

    def capacity(self) -> int:
        return self._config.max_memory_size

    def _summarize(self, obs: CanonicalObservation) -> str:
        """Generate a short summary of the observation payload."""
        if obs.previous_state and obs.current_state:
            return f"{obs.previous_state} → {obs.current_state}"
        if obs.payload:
            keys = list(obs.payload.keys())[:3]
            return f"payload: {', '.join(keys)}"
        return obs.category


# =========================================================================
# 7. Runtime Service
# =========================================================================

class RuntimeService:
    """Coordination layer for all Awareness engines.

    Provides unified entry points for observation ingestion, awareness
    queries, and system health.
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._config = config or RuntimeConfig()
        self._pipeline = ObservationPipeline(config)
        self._impact = ChangeImpactAnalyzer()
        self._risk = ContinuousRiskMonitor(config)
        self._org = OrganizationalAwareness(config)
        self._prioritization = EventPrioritization()
        self._memory = AwarenessMemory(config)
        self._event_log: List[Dict[str, Any]] = []
        self._stats = AwarenessStats()

    # --- Properties ---

    @property
    def pipeline(self) -> ObservationPipeline:
        return self._pipeline

    @property
    def impact(self) -> ChangeImpactAnalyzer:
        return self._impact

    @property
    def risk(self) -> ContinuousRiskMonitor:
        return self._risk

    @property
    def org(self) -> OrganizationalAwareness:
        return self._org

    @property
    def prioritization(self) -> EventPrioritization:
        return self._prioritization

    @property
    def memory(self) -> AwarenessMemory:
        return self._memory

    # --- Core operations ---

    def ingest(self, observation: CanonicalObservation,
               exec_intel: Optional[ExecutionIntelligenceEngine] = None,
               exec_service: Optional[ExecutionService] = None) -> Dict[str, Any]:
        """Ingest a raw observation, process it, and propagate.

        This is the main entry point for all system events.
        """
        # 1. Pipeline
        processed = self._pipeline.process(observation)
        if processed.payload.get("_duplicate"):
            return {"observation_id": processed.observation_id, "duplicate": True}

        # 2. Impact analysis
        impact = self._impact.assess(processed, exec_intel, exec_service)
        if processed.enrichment:
            processed.enrichment.impact_assessment = impact

        # 3. Risk monitoring
        risk_changes = []
        if exec_intel and exec_service:
            risk_changes = self._risk.on_observation(processed, exec_intel, exec_service)

        # 4. Organizational awareness
        self._org.update(processed)

        # 5. Priority
        prioritized = self._prioritization.prioritize(processed)

        # 6. Memory
        self._memory.record(processed)

        # 7. Update stats
        self._stats.total_observations += 1
        self._stats.observations_by_category[processed.category] = \
            self._stats.observations_by_category.get(processed.category, 0) + 1
        self._stats.total_propagations += len(processed.enrichment.propagation_targets) if processed.enrichment else 0
        self._stats.unique_executions_monitored = len(self._org._snapshots)
        self._stats.memory_utilization_pct = (self._memory.size() / max(self._memory.capacity(), 1)) * 100
        self._stats.risk_monitoring_active = self._config.enable_risk_monitoring

        # 8. Log
        self._log_event("ingest", processed.observation_id, processed.tenant_id)

        return {
            "observation_id": processed.observation_id,
            "category": processed.category,
            "priority": processed.priority,
            "impact": impact.to_dict(),
            "risk_changes": risk_changes,
            "duplicate": False,
        }

    def get_awareness(self, exec_id: str, tenant_id: int) -> Dict[str, Any]:
        """Get awareness state for a single execution."""
        snap = self._org.get_snapshot(exec_id, tenant_id)
        if not snap:
            return {"exec_id": exec_id, "tenant_id": tenant_id,
                    "level": AwarenessLevel.BLIND.value}
        return snap.to_dict()

    def get_tenant_awareness(self, tenant_id: int) -> Dict[str, Any]:
        """Get aggregated organizational awareness for a tenant."""
        return self._org.get_tenant_state(tenant_id).to_dict()

    def get_risk_status(self, exec_id: str) -> Dict[str, Any]:
        """Get current risk status for an execution."""
        return {
            "exec_id": exec_id,
            "risk_level": self._risk.get_risk(exec_id),
            "health_status": self._risk.get_health(exec_id),
        }

    def get_recent_observations(self, limit: int = 20,
                                tenant_id: Optional[int] = None,
                                min_priority: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent observations from awareness memory."""
        entries = self._memory.recent(limit, tenant_id, min_priority)
        return [e.to_dict() for e in entries]

    def get_event_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(reversed(self._event_log[-limit:]))

    def stats(self) -> Dict[str, Any]:
        """Runtime statistics."""
        base = self._stats.to_dict()
        base["risk_monitor"] = self._risk.stats
        base["awareness"] = self._org.stats
        base["pipeline"] = self._pipeline.stats
        base["config"] = self._config.to_dict()
        return base

    def _log_event(self, event: str, observation_id: str,
                   tenant_id: Optional[int] = None) -> None:
        self._event_log.append({
            "event": event,
            "observation_id": observation_id,
            "tenant_id": tenant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


# =========================================================================
# 8. Awareness Engine — Facade
# =========================================================================

class AwarenessEngine:
    """Facade over all Autonomous Operational Awareness components.

    Usage:
        ae = AwarenessEngine()
        result = ae.ingest(observation, exec_intel, exec_service)
        state = ae.get_awareness(exec_id, tenant_id)
        portfolio = ae.get_tenant_awareness(tenant_id)
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._runtime = RuntimeService(config)

    @property
    def runtime(self) -> RuntimeService:
        return self._runtime

    # --- Observation ingestion ---

    def ingest(self, observation: CanonicalObservation,
               exec_intel: Optional[ExecutionIntelligenceEngine] = None,
               exec_service: Optional[ExecutionService] = None) -> Dict[str, Any]:
        return self._runtime.ingest(observation, exec_intel, exec_service)

    def observe_execution_state(self, exec_id: str, tenant_id: int,
                                 previous_state: str, current_state: str,
                                 exec_service: Optional[ExecutionService] = None) -> Dict[str, Any]:
        """Convenience: create and ingest an execution state change observation."""
        obs = CanonicalObservation(
            category=ObservationCategory.EXECUTION_STATE_CHANGE.value,
            tenant_id=tenant_id,
            source="execution",
            source_id=exec_id,
            previous_state=previous_state,
            current_state=current_state,
            payload={"exec_id": exec_id},
        )
        ei = get_execution_intelligence() if exec_service else None
        return self.ingest(obs, ei, exec_service)

    def observe_exception(self, exec_id: str, tenant_id: int,
                           exc_type: str, severity: str,
                           exec_service: Optional[ExecutionService] = None) -> Dict[str, Any]:
        """Convenience: create and ingest an exception observation."""
        obs = CanonicalObservation(
            category=ObservationCategory.EXCEPTION_OCCURRED.value,
            tenant_id=tenant_id,
            source="execution",
            source_id=exec_id,
            payload={"exc_type": exc_type, "severity": severity},
        )
        ei = get_execution_intelligence() if exec_service else None
        return self.ingest(obs, ei, exec_service)

    def observe_health_change(self, exec_id: str, tenant_id: int,
                               previous_health: str, current_health: str,
                               exec_service: Optional[ExecutionService] = None) -> Dict[str, Any]:
        """Convenience: create and ingest a health change observation."""
        obs = CanonicalObservation(
            category=ObservationCategory.EXECUTION_HEALTH_CHANGE.value,
            tenant_id=tenant_id,
            source="execution_intelligence",
            source_id=exec_id,
            previous_state=previous_health,
            current_state=current_health,
            payload={"exec_id": exec_id},
        )
        ei = get_execution_intelligence() if exec_service else None
        return self.ingest(obs, ei, exec_service)

    # --- Queries ---

    def get_awareness(self, exec_id: str, tenant_id: int) -> Dict[str, Any]:
        return self._runtime.get_awareness(exec_id, tenant_id)

    def get_tenant_awareness(self, tenant_id: int) -> Dict[str, Any]:
        return self._runtime.get_tenant_awareness(tenant_id)

    def get_risk_status(self, exec_id: str) -> Dict[str, Any]:
        return self._runtime.get_risk_status(exec_id)

    def get_recent_observations(self, limit: int = 20,
                                tenant_id: Optional[int] = None,
                                min_priority: Optional[int] = None) -> List[Dict[str, Any]]:
        return self._runtime.get_recent_observations(limit, tenant_id, min_priority)

    def stats(self) -> Dict[str, Any]:
        return self._runtime.stats()