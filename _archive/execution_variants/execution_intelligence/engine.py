"""SHUNYA — Execution Intelligence Engine core implementation (Phase N+2).

Seven intelligence engines coordinated by the RuntimeService, all operating
deterministically on BusinessExecutionInstance data.

No paid-model dependency. Every output traced to underlying evidence.
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from app.execution_intelligence.models import (
    HealthAssessment, HealthDimension, HealthStatus,
    TimelineSnapshot, CompletionPrediction,
    DependencyNode, DependencyEdge, CriticalPath,
    RiskAssessment, RiskLevel, RiskFactor,
    NextAction, ActionPriority,
    PortfolioSummary, PortfolioBreakdown,
    EvidenceTrace, Explanation,
    RuntimeConfig, QueryFilter,
)
from app.execution import (
    BusinessExecutionInstance, ExecutionObligation,
    ExecutionResourceAllocation, ExecutionResourceConsumption,
    ExecutionResourceRequirement, ExecutionException,
    ExecState, ObligationState, ResourcePositionState,
    ExecutionService,
)

# =========================================================================
# Module-level singleton management
# =========================================================================

_ENGINE_INSTANCE: Optional[ExecutionIntelligenceEngine] = None


def get_execution_intelligence() -> ExecutionIntelligenceEngine:
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = ExecutionIntelligenceEngine()
    return _ENGINE_INSTANCE


def reset_execution_intelligence() -> None:
    global _ENGINE_INSTANCE
    _ENGINE_INSTANCE = None


# =========================================================================
# 1. Execution Health Engine
# =========================================================================

class ExecutionHealthEngine:
    """Deterministic execution health assessment.

    Evaluates six dimensions: state validity, progress, timeliness,
    resource position, exception burden, obligation health.
    Each produces a score [0,1] mapped to HEALTHY/WARNING/AT_RISK/CRITICAL.
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._config = config or RuntimeConfig()

    def assess(self, inst: BusinessExecutionInstance,
               obls: List[ExecutionObligation],
               excs: List[ExecutionException],
               service: ExecutionService) -> HealthAssessment:
        """Assess health of a single execution instance with full evidence."""
        scores: Dict[str, float] = {}
        dimensions: Dict[str, str] = {}
        evidence: Dict[str, List[str]] = {}

        # 1. State health — terminal states get fixed scores
        state_score, state_status, state_ev = self._assess_state(inst.state)
        scores[HealthDimension.STATE.value] = state_score
        dimensions[HealthDimension.STATE.value] = state_status
        evidence[HealthDimension.STATE.value] = state_ev

        if inst.state in (ExecState.FULFILLED, ExecState.CANCELLED, ExecState.FAILED, ExecState.BLOCKED):
            overall = state_status if inst.state == ExecState.FULFILLED else state_status
            return HealthAssessment(
                exec_id=inst.exec_id, tenant_id=inst.tenant_id,
                overall=overall, dimensions=dimensions,
                scores=scores, evidence=evidence,
            )

        # 2. Progress health — ratio of satisfied to total obligations
        if obls:
            satisfied = sum(1 for o in obls if o.state == ObligationState.SATISFIED)
            ratio = satisfied / len(obls)
            progress_status = self._score_to_status(ratio)
            scores[HealthDimension.PROGRESS.value] = ratio
            dimensions[HealthDimension.PROGRESS.value] = progress_status
            evidence[HealthDimension.PROGRESS.value] = [
                f"satisfied={satisfied}/{len(obls)} obligations",
            ]

        # 3. Timeliness — check if obligations are overdue
        timeliness_score, timeliness_status, timeliness_ev = self._assess_timeliness(obls)
        scores[HealthDimension.TIMELINESS.value] = timeliness_score
        dimensions[HealthDimension.TIMELINESS.value] = timeliness_status
        evidence[HealthDimension.TIMELINESS.value] = timeliness_ev

        # 4. Resource position
        resource_score = 1.0
        try:
            pos = service.compute_resource_position(inst.exec_id, inst.tenant_id)
            ov = pos.get("overall", ResourcePositionState.SUFFICIENT)
            resource_score = {
                ResourcePositionState.SUFFICIENT: 1.0,
                ResourcePositionState.NEAR_THRESHOLD: 0.6,
                ResourcePositionState.SHORTFALL: 0.2,
                ResourcePositionState.NON_COMPARABLE: 0.5,
            }.get(ov, 0.5)
            resource_status = {
                ResourcePositionState.SUFFICIENT: HealthStatus.HEALTHY.value,
                ResourcePositionState.NEAR_THRESHOLD: HealthStatus.WARNING.value,
                ResourcePositionState.SHORTFALL: HealthStatus.CRITICAL.value,
            }.get(ov, HealthStatus.WARNING.value)
        except Exception:
            resource_score = 0.5
            resource_status = HealthStatus.UNKNOWN.value
        scores[HealthDimension.RESOURCE_POSITION.value] = resource_score
        dimensions[HealthDimension.RESOURCE_POSITION.value] = resource_status
        evidence[HealthDimension.RESOURCE_POSITION.value] = [
            f"overall_position={resource_status}",
        ]

        # 5. Exception burden
        exc_score = max(0.0, 1.0 - len(excs) * 0.15)
        exc_status = self._score_to_status(exc_score)
        scores[HealthDimension.EXCEPTION_BURDEN.value] = exc_score
        dimensions[HealthDimension.EXCEPTION_BURDEN.value] = exc_status
        evidence[HealthDimension.EXCEPTION_BURDEN.value] = [
            f"exception_count={len(excs)}",
        ]

        # 6. Dependency health — check for blocked obligations
        blocked = sum(1 for o in obls if o.state == ObligationState.BLOCKED)
        dep_score = max(0.0, 1.0 - blocked * 0.2)
        dep_status = self._score_to_status(dep_score)
        scores[HealthDimension.DEPENDENCY_HEALTH.value] = dep_score
        dimensions[HealthDimension.DEPENDENCY_HEALTH.value] = dep_status
        evidence[HealthDimension.DEPENDENCY_HEALTH.value] = [
            f"blocked_obligations={blocked}/{len(obls)}" if obls else "no obligations",
        ]

        # Overall = weighted average
        weights = {
            HealthDimension.STATE.value: 0.25,
            HealthDimension.PROGRESS.value: 0.20,
            HealthDimension.TIMELINESS.value: 0.15,
            HealthDimension.RESOURCE_POSITION.value: 0.15,
            HealthDimension.EXCEPTION_BURDEN.value: 0.10,
            HealthDimension.DEPENDENCY_HEALTH.value: 0.15,
        }
        weighted = sum(scores.get(d, 0.5) * weights.get(d, 0.1) for d in scores)
        overall_status = self._score_to_status(weighted)

        return HealthAssessment(
            exec_id=inst.exec_id, tenant_id=inst.tenant_id,
            overall=overall_status, dimensions=dimensions,
            scores=scores, evidence=evidence,
        )

    def _assess_state(self, state: str) -> Tuple[float, str, List[str]]:
        mapping = {
            ExecState.ACTIVE: (0.9, HealthStatus.HEALTHY.value, ["execution is active"]),
            ExecState.PENDING: (0.7, HealthStatus.WARNING.value, ["execution has not started"]),
            ExecState.BLOCKED: (0.3, HealthStatus.CRITICAL.value, ["execution is blocked"]),
            ExecState.AT_RISK: (0.4, HealthStatus.AT_RISK.value, ["execution at risk"]),
            ExecState.PARTIALLY_FULFILLED: (0.6, HealthStatus.WARNING.value, ["partially fulfilled"]),
            ExecState.FULFILLED: (1.0, HealthStatus.HEALTHY.value, ["execution fulfilled"]),
            ExecState.FAILED: (0.0, HealthStatus.CRITICAL.value, ["execution failed"]),
            ExecState.CANCELLED: (0.0, HealthStatus.CRITICAL.value, ["execution cancelled"]),
        }
        return mapping.get(state, (0.5, HealthStatus.UNKNOWN.value, ["unknown state"]))

    def _assess_timeliness(self, obls: List[ExecutionObligation]) -> Tuple[float, str, List[str]]:
        now = datetime.now(timezone.utc)
        overdue = 0
        upcoming = 0
        for o in obls:
            if o.due_at and o.state not in (ObligationState.SATISFIED, ObligationState.WAIVED):
                try:
                    due = datetime.fromisoformat(o.due_at)
                    if due < now:
                        overdue += 1
                    else:
                        upcoming += 1
                except (ValueError, TypeError):
                    pass
        total = overdue + upcoming
        if total == 0:
            return 1.0, HealthStatus.HEALTHY.value, ["no timed obligations"]
        score = max(0.0, 1.0 - overdue / total)
        status = self._score_to_status(score)
        ev = [f"overdue={overdue}/{total} timed obligations"]
        return score, status, ev

    def _score_to_status(self, score: float) -> str:
        if score >= self._config.health_warning_threshold:
            return HealthStatus.HEALTHY.value
        elif score >= self._config.health_critical_threshold:
            return HealthStatus.WARNING.value
        elif score > 0.0:
            return HealthStatus.AT_RISK.value
        return HealthStatus.CRITICAL.value


# =========================================================================
# 2. Timeline Intelligence Engine
# =========================================================================

class TimelineIntelligenceEngine:
    """Track execution progress and predict completion.

    Uses obligation satisfaction ratios and elapsed time to estimate
    remaining duration. Deterministic: same inputs → same outputs.
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._config = config or RuntimeConfig()

    def snapshot(self, inst: BusinessExecutionInstance,
                 obls: List[ExecutionObligation]) -> TimelineSnapshot:
        """Produce a timeline snapshot for a single execution."""
        now = datetime.now(timezone.utc)
        created = self._parse_dt(inst.created_at)
        started = self._parse_dt(inst.started_at)
        completed = self._parse_dt(inst.completed_at)

        elapsed = 0.0
        if started:
            end = completed or now
            elapsed = (end - started).total_seconds()

        # Milestones from obligation states
        milestones_passed = []
        milestones_remaining = []
        for o in obls:
            if o.state in (ObligationState.SATISFIED, ObligationState.WAIVED):
                milestones_passed.append(f"{o.obl_type}: {o.description[:40]}")
            else:
                milestones_remaining.append(f"{o.obl_type}: {o.description[:40]}")

        completion_ratio = 0.0
        if obls:
            satisfied = sum(1 for o in obls if o.state == ObligationState.SATISFIED)
            completion_ratio = satisfied / len(obls)

        remaining = None
        if completion_ratio > 0.0 and elapsed > 0:
            estimated_total = elapsed / completion_ratio
            remaining = estimated_total - elapsed
        elif completion_ratio >= 1.0:
            remaining = 0.0

        return TimelineSnapshot(
            exec_id=inst.exec_id, tenant_id=inst.tenant_id,
            created_at=inst.created_at,
            started_at=inst.started_at, completed_at=inst.completed_at,
            elapsed_seconds=elapsed, remaining_seconds_estimate=remaining,
            completion_ratio=completion_ratio,
            milestones_passed=milestones_passed,
            milestones_remaining=milestones_remaining,
        )

    def predict_completion(self, snap: TimelineSnapshot) -> CompletionPrediction:
        """Predict completion time based on timeline snapshot."""
        now = datetime.now(timezone.utc)
        basis = []

        if snap.completed_at:
            return CompletionPrediction(
                exec_id=snap.exec_id, predicted_at=snap.completed_at,
                confidence=1.0, basis=["execution already completed"],
            )

        if not snap.started_at:
            return CompletionPrediction(
                exec_id=snap.exec_id,
                predicted_at=now.isoformat(),
                confidence=0.0, basis=["execution not yet started"],
            )

        predicted = None
        confidence = 0.0

        if snap.remaining_seconds_estimate is not None and snap.remaining_seconds_estimate >= 0:
            predicted_dt = now + timedelta(seconds=snap.remaining_seconds_estimate)
            predicted = predicted_dt.isoformat()
            confidence = min(0.9, snap.completion_ratio)
            basis.append(f"estimated {snap.remaining_seconds_estimate:.0f}s remaining")
            basis.append(f"completion_ratio={snap.completion_ratio:.2f}")

            optimistic_dt = now + timedelta(seconds=snap.remaining_seconds_estimate * 0.7)
            pessimistic_dt = now + timedelta(seconds=snap.remaining_seconds_estimate * 1.5)
            opt = optimistic_dt.isoformat()
            pes = pessimistic_dt.isoformat()
        else:
            basis.append("insufficient data for prediction")
            predicted = now.isoformat()
            opt = None
            pes = None

        return CompletionPrediction(
            exec_id=snap.exec_id, predicted_at=predicted or now.isoformat(),
            confidence=confidence, optimistic_at=opt, pessimistic_at=pes,
            basis=basis,
        )

    def _parse_dt(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        try:
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            return None


# =========================================================================
# 3. Dependency Graph Engine
# =========================================================================

class DependencyGraphEngine:
    """Build and analyze execution dependency graphs.

    Finds critical paths, bottlenecks, and topological orderings.
    Pure computation: no state, no side effects.
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._config = config or RuntimeConfig()

    def build_graph(self, inst: BusinessExecutionInstance,
                    obls: List[ExecutionObligation]) -> Tuple[List[DependencyNode], List[DependencyEdge]]:
        """Build dependency graph from obligations."""
        nodes: Dict[str, DependencyNode] = {}
        edges: List[DependencyEdge] = []
        level_map: Dict[str, int] = {}

        for o in obls:
            node = DependencyNode(
                node_id=o.obl_id, exec_id=inst.exec_id,
                obl_id=o.obl_id, obl_type=o.obl_type,
                description=o.description[:60], state=o.state,
            )
            nodes[o.obl_id] = node

        # Build adjacency and compute levels via BFS
        adj: Dict[str, List[str]] = {o.obl_id: [] for o in obls}
        for o in obls:
            for dep_id in o.dependencies:
                if dep_id in nodes:
                    adj[dep_id].append(o.obl_id)
                    edges.append(DependencyEdge(
                        from_obl_id=dep_id, to_obl_id=o.obl_id,
                        exec_id=inst.exec_id,
                    ))

        # Topological level assignment
        in_degree: Dict[str, int] = {oid: 0 for oid in nodes}
        for o in obls:
            for dep_id in o.dependencies:
                if dep_id in in_degree:
                    in_degree[o.obl_id] = in_degree.get(o.obl_id, 0) + 1

        queue = deque([oid for oid, deg in in_degree.items() if deg == 0])
        level = 0
        while queue:
            for _ in range(len(queue)):
                oid = queue.popleft()
                level_map[oid] = level
                for neighbor in adj.get(oid, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            level += 1

        # Update node degrees and levels
        for oid, node in nodes.items():
            node.in_degree = sum(1 for e in edges if e.to_obl_id == oid)
            node.out_degree = sum(1 for e in edges if e.from_obl_id == oid)
            node.level = level_map.get(oid, 0)

        return list(nodes.values()), edges

    def find_critical_path(self, nodes: List[DependencyNode],
                           edges: List[DependencyEdge],
                           obls: List[ExecutionObligation]) -> CriticalPath:
        """Find the critical path — longest path through dependency graph."""
        if not nodes:
            return CriticalPath(exec_id="", path=[], total_length=0)

        exec_id = nodes[0].exec_id
        adj: Dict[str, List[str]] = defaultdict(list)
        for e in edges:
            adj[e.from_obl_id].append(e.to_obl_id)

        # Find longest path via topological DP
        topo = sorted(nodes, key=lambda n: n.level, reverse=True)
        dist: Dict[str, int] = {n.obl_id: 0 for n in nodes}
        prev: Dict[str, Optional[str]] = {n.obl_id: None for n in nodes}

        for node in topo:
            for neighbor in adj.get(node.obl_id, []):
                if dist[neighbor] < dist[node.obl_id] + 1:
                    dist[neighbor] = dist[node.obl_id] + 1
                    prev[neighbor] = node.obl_id

        # Find farthest node
        farthest = max(dist, key=lambda k: dist[k]) if dist else None
        path: List[str] = []
        if farthest:
            curr: Optional[str] = farthest
            while curr is not None:
                path.append(curr)
                curr = prev.get(curr)
            path.reverse()

        # Bottlenecks = nodes with max out-degree in critical path
        bottlenecks = sorted(
            [n for n in nodes if n.out_degree > 1],
            key=lambda n: n.out_degree, reverse=True,
        )[:5]

        return CriticalPath(
            exec_id=exec_id,
            path=path,
            total_length=dist.get(farthest, 0) if farthest else 0,
            bottlenecks=[b.obl_id for b in bottlenecks],
        )


# =========================================================================
# 4. Risk Detection Engine
# =========================================================================

class RiskDetectionEngine:
    """Detect at-risk executions before they fail.

    Evaluates known risk patterns: timeout, blocking, resource shortfall,
    exception accumulation, stalled progress.
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._config = config or RuntimeConfig()

    def assess(self, inst: BusinessExecutionInstance,
               obls: List[ExecutionObligation],
               excs: List[ExecutionException],
               health: Optional[HealthAssessment] = None) -> RiskAssessment:
        """Assess all risk factors for an execution."""
        factors: List[RiskFactor] = []
        now = datetime.now(timezone.utc)

        # 1. Timeout risk — stale active executions
        if inst.state == ExecState.ACTIVE and inst.started_at:
            started = self._parse_dt(inst.started_at)
            if started:
                elapsed_hours = (now - started).total_seconds() / 3600
                if elapsed_hours > self._config.risk_timeout_threshold_hours:
                    factors.append(RiskFactor(
                        risk_type="timeout",
                        description=f"Execution active for {elapsed_hours:.1f}h (threshold: {self._config.risk_timeout_threshold_hours}h)",
                        level=RiskLevel.HIGH.value,
                        evidence=[f"started_at={inst.started_at}", f"elapsed_hours={elapsed_hours:.1f}"],
                    ))

        # 2. Blocking risk
        blocked_obls = [o for o in obls if o.state == ObligationState.BLOCKED]
        if blocked_obls:
            factors.append(RiskFactor(
                risk_type="blocked_obligations",
                description=f"{len(blocked_obls)} blocked obligation(s)",
                level=RiskLevel.HIGH.value,
                evidence=[f"blocked={len(blocked_obls)}/{len(obls)}"],
            ))

        # 3. Resource shortfall risk
        if health:
            res_score = health.scores.get(HealthDimension.RESOURCE_POSITION.value, 1.0)
            if res_score < self._config.health_critical_threshold:
                factors.append(RiskFactor(
                    risk_type="resource_shortfall",
                    description="Resource position is critical (shortfall detected)",
                    level=RiskLevel.CRITICAL.value,
                    evidence=health.evidence.get(HealthDimension.RESOURCE_POSITION.value, []),
                ))

        # 4. Exception accumulation
        critical_excs = [e for e in excs if e.severity in ("high", "critical")]
        if critical_excs:
            factors.append(RiskFactor(
                risk_type="critical_exceptions",
                description=f"{len(critical_excs)} critical/high-severity exception(s)",
                level=RiskLevel.HIGH.value,
                evidence=[f"critical_count={len(critical_excs)}", f"total_count={len(excs)}"],
            ))

        # 5. Stalled progress
        if obls and inst.started_at:
            started = self._parse_dt(inst.started_at)
            satisfied = sum(1 for o in obls if o.state == ObligationState.SATISFIED)
            if started and satisfied == 0:
                elapsed = (now - started).total_seconds() / 3600
                if elapsed > 24:
                    factors.append(RiskFactor(
                        risk_type="stalled_progress",
                        description=f"No obligations satisfied in {elapsed:.1f}h",
                        level=RiskLevel.MEDIUM.value,
                        evidence=[f"started_at={inst.started_at}", f"elapsed_hours={elapsed:.1f}"],
                    ))

        # Overall risk level
        if not factors:
            overall = RiskLevel.NONE.value
        elif any(f.level == RiskLevel.CRITICAL.value for f in factors):
            overall = RiskLevel.CRITICAL.value
        elif any(f.level == RiskLevel.HIGH.value for f in factors):
            overall = RiskLevel.HIGH.value
        elif any(f.level == RiskLevel.MEDIUM.value for f in factors):
            overall = RiskLevel.MEDIUM.value
        else:
            overall = RiskLevel.LOW.value

        return RiskAssessment(
            exec_id=inst.exec_id, tenant_id=inst.tenant_id,
            overall_risk=overall, factors=factors,
        )

    def _parse_dt(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        try:
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            return None


# =========================================================================
# 5. Next Action Engine
# =========================================================================

class NextActionEngine:
    """Recommend next best actions for execution health.

    Deterministic rules based on state, obligations, risks, and health.
    No ML — pure decision logic with evidence.
    """

    def assess(self, inst: BusinessExecutionInstance,
               obls: List[ExecutionObligation],
               excs: List[ExecutionException],
               health: Optional[HealthAssessment] = None,
               risk: Optional[RiskAssessment] = None,
               snap: Optional[TimelineSnapshot] = None) -> List[NextAction]:
        """Generate prioritized next action recommendations."""
        actions: List[NextAction] = []
        now = self._now()

        # 1. Terminal state — no actions
        if inst.state in (ExecState.FULFILLED, ExecState.FAILED, ExecState.CANCELLED):
            return actions

        # 2. Unblock blocked obligations
        blocked = [o for o in obls if o.state == ObligationState.BLOCKED]
        for o in blocked[:3]:
            actions.append(NextAction(
                exec_id=inst.exec_id, tenant_id=inst.tenant_id,
                action_type="unblock_obligation",
                description=f"Resolve blocker for {o.obl_type}: {o.description[:50]}",
                priority=ActionPriority.IMMEDIATE.value if self._is_overdue(o, now) else ActionPriority.HIGH.value,
                evidence=[f"obl_id={o.obl_id}", f"state=blocked"],
            ))

        # 3. Satisfy ready obligations
        ready = [o for o in obls if o.state == ObligationState.READY]
        for o in ready[:3]:
            overdue = self._is_overdue(o, now)
            actions.append(NextAction(
                exec_id=inst.exec_id, tenant_id=inst.tenant_id,
                action_type="satisfy_obligation",
                description=f"Complete {o.obl_type}: {o.description[:50]}",
                priority=ActionPriority.IMMEDIATE.value if overdue else ActionPriority.HIGH.value,
                evidence=[f"obl_id={o.obl_id}", f"state=ready"] + (
                    [f"overdue={o.due_at}"] if overdue else []
                ),
            ))

        # 4. Address critical/high risks
        if risk:
            for rf in risk.factors:
                if rf.level in (RiskLevel.CRITICAL.value, RiskLevel.HIGH.value):
                    actions.append(NextAction(
                        exec_id=inst.exec_id, tenant_id=inst.tenant_id,
                        action_type="mitigate_risk",
                        description=f"Address {rf.risk_type}: {rf.description[:60]}",
                        priority=ActionPriority.IMMEDIATE.value if rf.level == RiskLevel.CRITICAL.value else ActionPriority.HIGH.value,
                        evidence=rf.evidence,
                    ))

        # 5. Allocate resources for shortfalls
        if health:
            res_status = health.dimensions.get(HealthDimension.RESOURCE_POSITION.value, "")
            if res_status in (HealthStatus.AT_RISK.value, HealthStatus.CRITICAL.value):
                actions.append(NextAction(
                    exec_id=inst.exec_id, tenant_id=inst.tenant_id,
                    action_type="allocate_resources",
                    description="Allocate additional resources to address shortfall",
                    priority=ActionPriority.HIGH.value,
                    evidence=health.evidence.get(HealthDimension.RESOURCE_POSITION.value, []),
                ))

        # 6. Follow up on overdue obligations with pending status
        overdue_pending = [o for o in obls if o.state == ObligationState.PENDING and self._is_overdue(o, now)]
        for o in overdue_pending[:2]:
            actions.append(NextAction(
                exec_id=inst.exec_id, tenant_id=inst.tenant_id,
                action_type="escalate_overdue",
                description=f"Escalate overdue {o.obl_type}: {o.description[:50]}",
                priority=ActionPriority.IMMEDIATE.value,
                evidence=[f"obl_id={o.obl_id}", f"due_at={o.due_at}"],
            ))

        # Deduplicate by action_type+description, keep highest priority
        seen: Set[str] = set()
        deduped: List[NextAction] = []
        for a in sorted(actions, key=lambda x: x.priority):
            key = f"{a.action_type}:{a.description}"
            if key not in seen:
                seen.add(key)
                deduped.append(a)

        return deduped[:10]  # cap at 10

    def _is_overdue(self, obl: ExecutionObligation, now: datetime) -> bool:
        if not obl.due_at:
            return False
        try:
            due = datetime.fromisoformat(obl.due_at)
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            return due < now
        except (ValueError, TypeError):
            return False

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)


# =========================================================================
# 6. Portfolio Intelligence
# =========================================================================

class PortfolioIntelligence:
    """Aggregate execution intelligence across all executions for a tenant.

    Provides cross-cutting health, risk, and action summaries.
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._config = config or RuntimeConfig()

    def summarize(self, tenant_id: int, service: ExecutionService,
                  health_engine: ExecutionHealthEngine,
                  risk_engine: RiskDetectionEngine,
                  action_engine: NextActionEngine) -> PortfolioSummary:
        """Generate a portfolio summary for a tenant."""
        all_execs = list(service._execs.values())
        tenant_execs = [e for e in all_execs if e.tenant_id == tenant_id]

        breakdown = PortfolioBreakdown()
        for e in tenant_execs:
            if e.state == ExecState.ACTIVE:
                breakdown.active += 1
            elif e.state == ExecState.BLOCKED:
                breakdown.blocked += 1
            elif e.state == ExecState.AT_RISK:
                breakdown.at_risk += 1
            elif e.state == ExecState.FULFILLED:
                breakdown.fulfilled += 1
            elif e.state == ExecState.FAILED:
                breakdown.failed += 1
            elif e.state == ExecState.CANCELLED:
                breakdown.cancelled += 1
            elif e.state == ExecState.PENDING:
                breakdown.pending += 1
        breakdown.total = len(tenant_execs)

        # Health distribution
        health_dist: Dict[str, int] = {}
        all_risks: List[RiskFactor] = []
        all_actions: List[NextAction] = []

        for e in tenant_execs:
            obls = [o for o in service._obls.values() if o.exec_id == e.exec_id]
            excs_list = [x for x in service._excs.values() if x.exec_id == e.exec_id]
            h = health_engine.assess(e, obls, excs_list, service)
            health_dist[h.overall] = health_dist.get(h.overall, 0) + 1

            r = risk_engine.assess(e, obls, excs_list, h)
            all_risks.extend(r.factors[:2])

            a = action_engine.assess(e, obls, excs_list, h, r)
            all_actions.extend(a[:2])

        # Overall portfolio health = mode or weighted
        if health_dist:
            overall_health = max(health_dist, key=health_dist.get)
        else:
            overall_health = HealthStatus.HEALTHY.value

        # Top risks across portfolio
        all_risks.sort(key=lambda rf: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}.get(rf.level, 5),
            -rf.confidence,
        ))
        top_risks = all_risks[:self._config.portfolio_top_k]

        # Top actions across portfolio
        all_actions.sort(key=lambda a: a.priority)
        top_actions = all_actions[:self._config.portfolio_top_k]

        return PortfolioSummary(
            tenant_id=tenant_id,
            breakdown=breakdown,
            health_distribution=health_dist,
            overall_health=overall_health,
            top_risks=top_risks,
            top_actions=top_actions,
        )


# =========================================================================
# 7. Explainability Layer
# =========================================================================

class ExplainabilityLayer:
    """Explain every intelligence output with traceable evidence chains.

    All explanations are deterministic: same inputs → same explanations.
    """

    def explain_health(self, assessment: HealthAssessment) -> Explanation:
        traces = []
        for dim, status in assessment.dimensions.items():
            score = assessment.scores.get(dim, 0.0)
            ev = assessment.evidence.get(dim, [])
            traces.append(EvidenceTrace(
                claim=f"{dim} → {status} (score={score:.2f})",
                evidence="; ".join(ev) if ev else "no evidence",
                source="ExecutionHealthEngine.assess()",
                confidence=score,
            ))
        desc = " or ".join(ev for ev_list in assessment.evidence.values() for ev in ev_list[:1]) or "no issues"
        return Explanation(
            topic=f"Execution Health: {assessment.exec_id}",
            conclusion=f"Overall health is {assessment.overall}. {desc}",
            traces=traces,
            confidence=sum(assessment.scores.values()) / max(len(assessment.scores), 1),
        )

    def explain_risk(self, assessment: RiskAssessment) -> Explanation:
        traces = []
        for f in assessment.factors:
            traces.append(EvidenceTrace(
                claim=f"Risk: {f.risk_type} ({f.level})",
                evidence="; ".join(f.evidence),
                source="RiskDetectionEngine.assess()",
                confidence=f.confidence,
            ))
        return Explanation(
            topic=f"Risk Assessment: {assessment.exec_id}",
            conclusion=f"Overall risk level is {assessment.overall_risk} with {len(assessment.factors)} factor(s)",
            traces=traces,
            confidence=0.9 if assessment.overall_risk == RiskLevel.NONE.value else 0.7,
        )

    def explain_action(self, action: NextAction) -> Explanation:
        traces = [
            EvidenceTrace(
                claim=f"Action: {action.action_type} (priority={action.priority})",
                evidence="; ".join(action.evidence),
                source="NextActionEngine.assess()",
                confidence=0.85,
            )
        ]
        return Explanation(
            topic=f"Next Action: {action.action_id[:12]}",
            conclusion=f"Recommended: {action.description}",
            traces=traces,
            confidence=0.85,
        )

    def explain_portfolio(self, summary: PortfolioSummary) -> Explanation:
        traces = [
            EvidenceTrace(
                claim=f"Portfolio: {summary.tenant_id}",
                evidence=f"{summary.breakdown.total} executions, overall health={summary.overall_health}",
                source="PortfolioIntelligence.summarize()",
                confidence=0.95,
            )
        ]
        return Explanation(
            topic=f"Portfolio Summary: tenant {summary.tenant_id}",
            conclusion=f"Tenant has {summary.breakdown.total} execution(s). "
                       f"Overall portfolio health: {summary.overall_health}. "
                       f"{summary.breakdown.at_risk} at risk, {summary.breakdown.blocked} blocked.",
            traces=traces,
            confidence=0.95,
        )


# =========================================================================
# 8. Runtime Service
# =========================================================================

class RuntimeService:
    """Coordination layer for all Execution Intelligence Engines.

    Provides unified entry points, manages engine lifecycle, and
    ensures consistent evidence tracing across all outputs.
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._config = config or RuntimeConfig()
        self._health = ExecutionHealthEngine(config)
        self._timeline = TimelineIntelligenceEngine(config)
        self._deps = DependencyGraphEngine(config)
        self._risk = RiskDetectionEngine(config)
        self._actions = NextActionEngine()
        self._portfolio = PortfolioIntelligence(config)
        self._explain = ExplainabilityLayer()
        self._event_log: List[Dict[str, Any]] = []

    @property
    def health(self) -> ExecutionHealthEngine:
        return self._health

    @property
    def timeline(self) -> TimelineIntelligenceEngine:
        return self._timeline

    @property
    def deps(self) -> DependencyGraphEngine:
        return self._deps

    @property
    def risk(self) -> RiskDetectionEngine:
        return self._risk

    @property
    def actions(self) -> NextActionEngine:
        return self._actions

    @property
    def portfolio(self) -> PortfolioIntelligence:
        return self._portfolio

    @property
    def explain(self) -> ExplainabilityLayer:
        return self._explain

    # ---- Coordinated assessments ----

    def full_assessment(self, inst: BusinessExecutionInstance,
                        service: ExecutionService) -> Dict[str, Any]:
        """Full intelligence assessment of a single execution (all engines)."""
        obls = [o for o in service._obls.values() if o.exec_id == inst.exec_id]
        excs_list = [x for x in service._excs.values() if x.exec_id == inst.exec_id]

        health = self._health.assess(inst, obls, excs_list, service)
        timeline = self._timeline.snapshot(inst, obls)
        prediction = self._timeline.predict_completion(timeline)
        nodes, edges = self._deps.build_graph(inst, obls)
        critical = self._deps.find_critical_path(nodes, edges, obls)
        risk = self._risk.assess(inst, obls, excs_list, health)
        actions = self._actions.assess(inst, obls, excs_list, health, risk, timeline)

        result = {
            "exec_id": inst.exec_id,
            "tenant_id": inst.tenant_id,
            "health": health.to_dict(),
            "timeline": timeline.to_dict(),
            "completion_prediction": prediction.to_dict(),
            "critical_path": critical.to_dict(),
            "risk": risk.to_dict(),
            "next_actions": [a.to_dict() for a in actions],
        }

        if self._config.enable_explainability:
            result["explanations"] = {
                "health": self._explain.explain_health(health).to_dict(),
                "risk": self._explain.explain_risk(risk).to_dict(),
                "actions": [self._explain.explain_action(a).to_dict() for a in actions[:3]],
            }

        self._log_event("full_assessment", inst.exec_id, inst.tenant_id)
        return result

    def portfolio_summary(self, tenant_id: int,
                          service: ExecutionService) -> Dict[str, Any]:
        """Portfolio-level intelligence for a tenant."""
        summary = self._portfolio.summarize(
            tenant_id, service, self._health, self._risk, self._actions,
        )
        result = summary.to_dict()

        if self._config.enable_explainability:
            result["explanation"] = self._explain.explain_portfolio(summary).to_dict()

        self._log_event("portfolio_summary", tenant_id=tenant_id)
        return result

    def explain_assessment(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Return explanations for a previously computed assessment dict."""
        explanations = {}
        if "health" in assessment:
            h = HealthAssessment(
                exec_id=assessment.get("exec_id", ""),
                tenant_id=assessment.get("tenant_id", 0),
                overall=assessment["health"].get("overall", "unknown"),
                dimensions=assessment["health"].get("dimensions", {}),
                scores=assessment["health"].get("scores", {}),
                evidence=assessment["health"].get("evidence", {}),
            )
            explanations["health"] = self._explain.explain_health(h).to_dict()
        return {"exec_id": assessment.get("exec_id"), "explanations": explanations}

    def get_event_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent runtime service events."""
        return list(reversed(self._event_log[-limit:]))

    def stats(self) -> Dict[str, Any]:
        """Runtime statistics."""
        return {
            "total_assessments": sum(1 for e in self._event_log if e.get("event") == "full_assessment"),
            "total_portfolio_summaries": sum(1 for e in self._event_log if e.get("event") == "portfolio_summary"),
            "config": self._config.to_dict(),
        }

    def _log_event(self, event: str, exec_id: Optional[str] = None,
                   tenant_id: Optional[int] = None) -> None:
        self._event_log.append({
            "event": event,
            "exec_id": exec_id,
            "tenant_id": tenant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


# =========================================================================
# Main Engine — Facade
# =========================================================================

class ExecutionIntelligenceEngine:
    """Facade over all Execution Intelligence engines.

    Usage:
        ei = ExecutionIntelligenceEngine()
        result = ei.full_assessment(exec_instance, execution_service)
        portfolio = ei.portfolio_summary(tenant_id, execution_service)
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        self._runtime = RuntimeService(config)

    @property
    def runtime(self) -> RuntimeService:
        return self._runtime

    def full_assessment(self, inst: BusinessExecutionInstance,
                        service: ExecutionService) -> Dict[str, Any]:
        return self._runtime.full_assessment(inst, service)

    def portfolio_summary(self, tenant_id: int,
                          service: ExecutionService) -> Dict[str, Any]:
        return self._runtime.portfolio_summary(tenant_id, service)

    def assess_health(self, inst: BusinessExecutionInstance,
                      service: ExecutionService) -> HealthAssessment:
        obls = [o for o in service._obls.values() if o.exec_id == inst.exec_id]
        excs_list = [x for x in service._excs.values() if x.exec_id == inst.exec_id]
        return self._runtime.health.assess(inst, obls, excs_list, service)

    def assess_risk(self, inst: BusinessExecutionInstance,
                    service: ExecutionService) -> RiskAssessment:
        obls = [o for o in service._obls.values() if o.exec_id == inst.exec_id]
        excs_list = [x for x in service._excs.values() if x.exec_id == inst.exec_id]
        health = self._runtime.health.assess(inst, obls, excs_list, service)
        return self._runtime.risk.assess(inst, obls, excs_list, health)

    def next_actions(self, inst: BusinessExecutionInstance,
                     service: ExecutionService) -> List[NextAction]:
        obls = [o for o in service._obls.values() if o.exec_id == inst.exec_id]
        excs_list = [x for x in service._excs.values() if x.exec_id == inst.exec_id]
        health = self._runtime.health.assess(inst, obls, excs_list, service)
        risk = self._runtime.risk.assess(inst, obls, excs_list, health)
        snap = self._runtime.timeline.snapshot(inst, obls)
        return self._runtime.actions.assess(inst, obls, excs_list, health, risk, snap)

    def timeline(self, inst: BusinessExecutionInstance,
                 service: ExecutionService) -> Dict[str, Any]:
        obls = [o for o in service._obls.values() if o.exec_id == inst.exec_id]
        snap = self._runtime.timeline.snapshot(inst, obls)
        pred = self._runtime.timeline.predict_completion(snap)
        return {"snapshot": snap.to_dict(), "prediction": pred.to_dict()}

    def dependency_graph(self, inst: BusinessExecutionInstance,
                         service: ExecutionService) -> Dict[str, Any]:
        obls = [o for o in service._obls.values() if o.exec_id == inst.exec_id]
        nodes, edges = self._runtime.deps.build_graph(inst, obls)
        critical = self._runtime.deps.find_critical_path(nodes, edges, obls)
        return {
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
            "critical_path": critical.to_dict(),
        }

    def explain(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        return self._runtime.explain_assessment(assessment)

    def stats(self) -> Dict[str, Any]:
        return self._runtime.stats()
