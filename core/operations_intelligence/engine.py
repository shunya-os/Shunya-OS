"""Universal Operations Intelligence — Core Engine.

Pure computation: bottleneck detection, throughput analysis, capacity planning,
queue analysis (Little's Law), service level monitoring, operational health
scoring, process analysis, workflow analysis, continuous improvement
recommendations, resource utilization analysis.

No Operations Runtime. No ERP Runtime. No Workflow Runtime.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.operations_intelligence.models import (
    Bottleneck,
    CapacityPlan,
    ContinuousImprovement,
    OperationalHealth,
    OperationsRecommendation,
    Process,
    ProcessStep,
    Queue,
    Resource,
    ServiceLevel,
    ThroughputMeasure,
    Workflow,
    HealthLevel,
    ServiceLevelStatus,
    ResourceType,
    _generate_id,
    _now_iso,
)


class OperationsIntelligenceEngine:
    """Pure computation engine for Universal Operations Intelligence."""

    # ── Process Analysis ─────────────────────────────────────────────────

    def analyze_process(self, process: Process) -> dict[str, Any]:
        """Analyze a process: cycle time, throughput, bottlenecks, waste."""
        total_duration = sum(s.effective_duration for s in process.steps)
        decision_points = sum(1 for s in process.steps if s.decision_point)
        parallel_steps = sum(1 for s in process.steps if s.parallel)
        quality_checks = sum(1 for s in process.steps if s.quality_check)
        rework_steps = [s for s in process.steps if s.rework_pct > 0]
        high_variability = [s for s in process.steps if s.variability_pct > 20]

        return {
            "process_id": process.process_id,
            "name": process.name,
            "total_step_duration_minutes": round(total_duration, 2),
            "cycle_time_minutes": process.cycle_time_minutes,
            "throughput_per_hour": process.throughput_per_hour,
            "effective_throughput": process.effective_throughput(),
            "defect_rate_pct": process.defect_rate_pct,
            "uptime_pct": process.uptime_pct,
            "step_count": process.step_count,
            "decision_points": decision_points,
            "parallel_steps": parallel_steps,
            "quality_checks": quality_checks,
            "rework_steps": len(rework_steps),
            "high_variability_steps": len(high_variability),
            "batch_size": process.batch_size,
            "setup_time_minutes": process.setup_time_minutes,
            "assessment": self._assess_process_efficiency(process),
        }

    def _assess_process_efficiency(self, process: Process) -> dict[str, Any]:
        """Assess overall process efficiency."""
        score = 0.5
        issues: list[str] = []
        strengths: list[str] = []

        if process.defect_rate_pct > 10:
            score -= 0.2
            issues.append(f"High defect rate ({process.defect_rate_pct}%)")
        elif process.defect_rate_pct < 2:
            score += 0.1
            strengths.append("Low defect rate")

        if process.uptime_pct < 95:
            score -= 0.15
            issues.append(f"Low uptime ({process.uptime_pct}%)")
        elif process.uptime_pct >= 99:
            score += 0.1
            strengths.append("High uptime")

        if process.setup_time_minutes > process.cycle_time_minutes * 2:
            score -= 0.1
            issues.append("High setup time relative to cycle time")

        rework_step_count = sum(1 for s in process.steps if s.rework_pct > 0)
        if rework_step_count > 0:
            score -= 0.1 * min(rework_step_count, 3)
            issues.append(f"{rework_step_count} step(s) with rework")

        if process.throughput_per_hour > 0:
            strengths.append("Throughput measurable")

        score = max(0.0, min(1.0, score))
        level = "efficient" if score >= 0.7 else "moderate" if score >= 0.4 else "inefficient"

        return {"score": round(score, 4), "level": level,
                "issues": issues, "strengths": strengths}

    # ── Workflow Analysis ────────────────────────────────────────────────

    def analyze_workflow(self, workflow: Workflow) -> dict[str, Any]:
        """Analyze a workflow: progress, bottlenecks, SLA compliance."""
        recs: list[OperationsRecommendation] = []
        issues: list[str] = []
        strengths: list[str] = []

        if workflow.current_step_index == 0 and workflow.step_count > 0:
            issues.append("Workflow not yet started")
        elif workflow.current_step_index >= workflow.step_count:
            strengths.append("Workflow completed")

        if workflow.sla_minutes > 0:
            elapsed = self._estimate_elapsed(workflow)
            if elapsed > workflow.sla_minutes:
                issues.append(f"SLA breached: {elapsed:.0f}m elapsed vs {workflow.sla_minutes}m target")
            elif elapsed > workflow.sla_minutes * 0.75:
                issues.append(f"SLA at risk: {elapsed:.0f}m elapsed of {workflow.sla_minutes}m target")
            else:
                strengths.append(f"Within SLA ({elapsed:.0f}m of {workflow.sla_minutes}m)")

        # Check for escalation path
        if workflow.escalation_path and workflow.current_step_index > 0:
            strengths.append("Escalation path configured")

        # Check for timeout steps
        timeout_steps = [s for s in workflow.steps if s.timeout_minutes > 0]
        if timeout_steps:
            strengths.append(f"{len(timeout_steps)} step(s) with timeout protection")

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "progress_pct": workflow.progress_pct,
            "step_count": workflow.step_count,
            "current_step_index": workflow.current_step_index,
            "sla_minutes": workflow.sla_minutes,
            "issues": issues,
            "strengths": strengths,
            "recommendations": [r.to_dict() for r in recs],
        }

    def _estimate_elapsed(self, workflow: Workflow) -> float:
        """Estimate elapsed time since workflow creation."""
        try:
            created = datetime.fromisoformat(workflow.created_at.replace("Z", "+00:00"))
            return (datetime.now(timezone.utc) - created).total_seconds() / 60
        except (ValueError, TypeError):
            return 0.0

    # ── Bottleneck Detection ─────────────────────────────────────────────

    def detect_bottlenecks(self, process: Process) -> list[dict[str, Any]]:
        """Detect bottlenecks in a process."""
        bottlenecks: list[dict[str, Any]] = []

        # Find steps with highest duration relative to total
        if not process.steps:
            return bottlenecks

        total_duration = sum(s.duration_minutes for s in process.steps)
        for step in process.steps:
            if total_duration == 0:
                continue
            duration_share = (step.duration_minutes / total_duration) * 100
            impact = duration_share

            # Increase impact if step has rework
            if step.rework_pct > 0:
                impact += step.rework_pct * 0.5

            if impact >= 15:
                bottlenecks.append({
                    "bottleneck_id": _generate_id(),
                    "step_id": step.step_id,
                    "name": step.name,
                    "constraint_type": "duration",
                    "current_throughput": step.duration_minutes,
                    "max_throughput": step.duration_minutes * (1 + step.rework_pct / 100),
                    "impact_pct": round(impact, 1),
                    "queue_length": 0,
                    "wait_time_minutes": step.duration_minutes * (step.variability_pct / 100),
                    "contributing_factors": [],
                    "severity": "critical" if impact >= 30 else "high" if impact >= 20 else "medium",
                    "evidence": [{"type": "duration_share", "value": round(duration_share, 1)},
                                 {"type": "rework_pct", "value": step.rework_pct}],
                })

        return bottlenecks

    # ── Throughput Analysis ──────────────────────────────────────────────

    def analyze_throughput(self, process: Process,
                           measures: list[ThroughputMeasure] | None = None) -> dict[str, Any]:
        """Analyze throughput performance."""
        if not measures:
            measures = []

        all_throughputs = [m.throughput_per_hour for m in measures if m.throughput_per_hour > 0]
        avg_throughput = sum(all_throughputs) / len(all_throughputs) if all_throughputs else 0.0
        max_throughput = max(all_throughputs) if all_throughputs else 0.0
        min_throughput = min(all_throughputs) if all_throughputs else 0.0

        total_units = sum(m.units_processed for m in measures)
        total_defective = sum(m.units_defective for m in measures)
        total_good = sum(m.good_units for m in measures)
        overall_defect_rate = (total_defective / max(total_units, 1)) * 100

        return {
            "process_id": process.process_id,
            "name": process.name,
            "current_throughput": process.throughput_per_hour,
            "effective_throughput": process.effective_throughput(),
            "average_throughput": round(avg_throughput, 2),
            "max_throughput": round(max_throughput, 2),
            "min_throughput": round(min_throughput, 2),
            "total_units_processed": total_units,
            "total_good_units": total_good,
            "total_defective_units": total_defective,
            "overall_defect_rate_pct": round(overall_defect_rate, 2),
            "measurement_periods": len(measures),
            "assessment": "high" if avg_throughput >= process.throughput_per_hour * 0.9
            else "stable" if avg_throughput >= process.throughput_per_hour * 0.7
            else "declining",
        }

    # ── Capacity Planning ────────────────────────────────────────────────

    def analyze_capacity(self, plan: CapacityPlan) -> dict[str, Any]:
        """Analyze capacity plan and identify gaps."""
        recs: list[OperationsRecommendation] = []

        overloaded = [r for r in plan.resources if r.utilization_pct > plan.target_utilization_pct + plan.buffer_pct]
        underutilized = [r for r in plan.resources if r.utilization_pct < 30]

        if overloaded:
            recs.append(OperationsRecommendation(
                title="Capacity overload detected",
                description=f"{len(overloaded)} resource(s) exceed target utilization",
                priority="high",
                reasoning=f"Resources: {', '.join(r.name for r in overloaded[:5])}",
                confidence=0.85,
                assumptions=["Demand will continue at current rate"],
                alternatives=[{"action": "Add capacity", "cost": "High"},
                              {"action": "Reallocate load", "cost": "Medium"}],
                expected_impact="Risk of quality degradation and delays",
                evidence=[{"type": "overloaded_resources", "count": len(overloaded),
                           "details": [{"name": r.name, "utilization": r.utilization_pct}
                                       for r in overloaded[:5]]}],
                affected_resource_ids=[r.resource_id for r in overloaded],
            ))

        if underutilized:
            recs.append(OperationsRecommendation(
                title="Resource underutilization",
                description=f"{len(underutilized)} resource(s) below 30% utilization",
                priority="medium",
                reasoning="Underutilized resources represent wasted capacity",
                confidence=0.7,
                assumptions=["Current demand patterns persist"],
                alternatives=[{"action": "Reduce capacity", "cost": "Savings"},
                              {"action": "Redesignate resources", "cost": "Low"}],
                expected_impact="Cost savings of up to 20% on underutilized resources",
                evidence=[{"type": "underutilized_resources", "count": len(underutilized),
                           "details": [{"name": r.name, "utilization": r.utilization_pct}
                                       for r in underutilized[:5]]}],
                affected_resource_ids=[r.resource_id for r in underutilized],
            ))

        return {
            "plan_id": plan.cap_id,
            "name": plan.name,
            "total_capacity": plan.total_capacity,
            "total_load": plan.total_load,
            "overall_utilization_pct": plan.overall_utilization_pct,
            "target_utilization_pct": plan.target_utilization_pct,
            "headroom_pct": plan.headroom_pct,
            "is_overloaded": plan.is_overloaded,
            "overloaded_resources": len(overloaded),
            "underutilized_resources": len(underutilized),
            "recommendations": [r.to_dict() for r in recs],
        }

    # ── Queue Analysis (Little's Law) ────────────────────────────────────

    def analyze_queue(self, queue: Queue) -> dict[str, Any]:
        """Analyze a queue using Little's Law and related heuristics."""
        recs: list[OperationsRecommendation] = []

        # Little's Law: L = λW, W = L/λ
        wait_minutes = queue.estimated_wait_minutes
        is_stable = queue.arrival_rate_per_hour < queue.service_rate_per_hour

        if queue.is_overloaded:
            recs.append(OperationsRecommendation(
                title="Queue is overloaded — arrival rate exceeds service rate",
                description=f"λ={queue.arrival_rate_per_hour}/hr, μ={queue.service_rate_per_hour}/hr",
                priority="critical",
                reasoning="Queue is unstable and will grow without intervention",
                confidence=0.95,
                assumptions=["Arrival and service rates remain constant"],
                alternatives=[{"action": "Increase service rate", "cost": "Medium-High"},
                              {"action": "Reduce arrival rate", "cost": "Variable"},
                              {"action": "Add parallel service channels", "cost": "High"}],
                expected_impact="Queue length will grow unboundedly without intervention",
                evidence=[{"type": "arrival_rate", "value": queue.arrival_rate_per_hour},
                          {"type": "service_rate", "value": queue.service_rate_per_hour},
                          {"type": "utilization", "value": queue.utilization}],
            ))

        if wait_minutes > 30:
            recs.append(OperationsRecommendation(
                title="Long wait time detected",
                description=f"Estimated wait: {wait_minutes} minutes (Little's Law)",
                priority="high",
                reasoning=f"Queue length ({queue.current_length}) at arrival rate {queue.arrival_rate_per_hour}/hr",
                confidence=0.8,
                assumptions=["FIFO discipline", "Poisson arrivals"],
                alternatives=[{"action": "Increase service capacity", "cost": "Medium"},
                              {"action": "Implement priority queuing", "cost": "Low"},
                              {"action": "Add self-service options", "cost": "Medium"}],
                expected_impact="Reduced wait times by 30-50%",
                evidence=[{"type": "estimated_wait_minutes", "value": wait_minutes},
                          {"type": "queue_length", "value": queue.current_length}],
            ))

        return {
            "queue_id": queue.queue_id,
            "name": queue.name,
            "current_length": queue.current_length,
            "arrival_rate_per_hour": queue.arrival_rate_per_hour,
            "service_rate_per_hour": queue.service_rate_per_hour,
            "utilization_pct": queue.utilization,
            "is_stable": is_stable,
            "is_overloaded": queue.is_overloaded,
            "estimated_wait_minutes": wait_minutes,
            "average_wait_minutes": queue.average_wait_time_minutes,
            "discipline": queue.discipline,
            "recommendations": [r.to_dict() for r in recs],
        }

    # ── Service Level Monitoring ────────────────────────────────────────

    def monitor_service_levels(self, levels: list[ServiceLevel]) -> list[dict[str, Any]]:
        """Monitor and assess service level compliance."""
        results: list[dict[str, Any]] = []

        for sl in levels:
            computed_status = sl.compute_status()
            sl.status = computed_status

            result = {
                "sl_id": sl.sl_id,
                "name": sl.name,
                "metric": sl.metric,
                "target": sl.target,
                "actual": sl.actual,
                "compliance_pct": sl.compliance_pct,
                "status": computed_status,
                "is_breached": sl.is_breached,
            }

            if computed_status == ServiceLevelStatus.VIOLATED.value:
                result["recommendation"] = OperationsRecommendation(
                    title=f"SLA breached: {sl.name}",
                    description=f"Target: {sl.target}, Actual: {sl.actual} ({sl.compliance_pct}%)",
                    priority="critical",
                    reasoning=f"Service level '{sl.name}' is below acceptable threshold",
                    confidence=0.9,
                    assumptions=["Measurement period is accurate"],
                    alternatives=[{"action": "Increase resource allocation", "cost": "High"},
                                  {"action": "Review and adjust target", "cost": "Low"},
                                  {"action": "Process improvement initiative", "cost": "Medium"}],
                    expected_impact=f"Bring {sl.metric} back to {sl.target}",
                    evidence=[{"type": "sla_violation", "metric": sl.metric,
                               "target": sl.target, "actual": sl.actual,
                               "compliance_pct": sl.compliance_pct}],
                ).to_dict()

            results.append(result)

        return results

    # ── Operational Health Scoring ───────────────────────────────────────

    def compute_operational_health(self, process: Process,
                                    queues: list[Queue] | None = None,
                                    service_levels: list[ServiceLevel] | None = None,
                                    resources: list[Resource] | None = None,
                                    improvement_items: list[ContinuousImprovement] | None = None) -> dict[str, Any]:
        """Compute overall operational health score for a process."""
        queues = queues or []
        service_levels = service_levels or []
        resources = resources or []
        improvement_items = improvement_items or []

        # Throughput score
        target_throughput = process.throughput_per_hour
        effective = process.effective_throughput()
        throughput_score = min(1.0, effective / max(target_throughput, 1)) if target_throughput > 0 else 0.5

        # Quality score
        quality_score = max(0.0, 1.0 - process.defect_rate_pct / 100.0)

        # Efficiency score
        efficiency_score = process.uptime_pct / 100.0
        rework_penalty = sum(s.rework_pct for s in process.steps) / max(len(process.steps), 1) / 100.0
        efficiency_score = max(0.0, efficiency_score - rework_penalty)

        # Capacity score
        if resources:
            avg_util = sum(r.utilization_pct for r in resources) / len(resources)
            if avg_util < 30:
                capacity_score = 0.4  # underutilized
            elif avg_util > 90:
                capacity_score = 0.3  # overutilized
            else:
                capacity_score = 0.8  # optimal
        else:
            capacity_score = 0.5

        # Service level score
        if service_levels:
            met = sum(1 for sl in service_levels if sl.compute_status() == ServiceLevelStatus.MET.value)
            sl_score = met / len(service_levels)
        else:
            sl_score = 0.5

        # Improvement momentum
        if improvement_items:
            completed = sum(1 for ci in improvement_items if ci.is_completed)
            avg_improvement = sum(ci.improvement_pct for ci in improvement_items) / max(len(improvement_items), 1)
            improvement_momentum = min(1.0, (completed / len(improvement_items)) * (avg_improvement / 100 + 1))
        else:
            improvement_momentum = 0.5

        # Composite score
        score = (
            throughput_score * 0.25 +
            quality_score * 0.25 +
            efficiency_score * 0.20 +
            capacity_score * 0.15 +
            sl_score * 0.15
        )
        score = max(0.0, min(1.0, round(score, 4)))

        if score >= 0.85:
            level = HealthLevel.EXCELLENT.value
            assessment = "operating at peak effectiveness"
        elif score >= 0.7:
            level = HealthLevel.GOOD.value
            assessment = "operating well with minor opportunities"
        elif score >= 0.5:
            level = HealthLevel.FAIR.value
            assessment = "operating adequately with notable gaps"
        elif score >= 0.3:
            level = HealthLevel.AT_RISK.value
            assessment = "multiple areas require intervention"
        else:
            level = HealthLevel.CRITICAL.value
            assessment = "operation is critically compromised"

        risk_factors = []
        strengths = []
        if throughput_score < 0.5:
            risk_factors.append("Low throughput relative to target")
        else:
            strengths.append("Good throughput performance")
        if quality_score < 0.8:
            risk_factors.append("Quality concerns — defect rate above target")
        else:
            strengths.append("Strong quality metrics")
        if capacity_score < 0.5:
            risk_factors.append("Capacity imbalance")
        else:
            strengths.append("Balanced capacity utilization")
        if sl_score < 0.7:
            risk_factors.append("Service level attainment below target")
        else:
            strengths.append("Service levels being met")

        return {
            "process_id": process.process_id,
            "name": process.name,
            "score": score,
            "level": level,
            "assessment": assessment,
            "throughput_score": round(throughput_score, 4),
            "quality_score": round(quality_score, 4),
            "efficiency_score": round(efficiency_score, 4),
            "capacity_score": round(capacity_score, 4),
            "service_level_score": round(sl_score, 4),
            "improvement_momentum": round(improvement_momentum, 4),
            "risk_factors": risk_factors,
            "strengths": strengths,
        }

    # ── Continuous Improvement Recommendations ───────────────────────────

    def recommend_improvements(self, process: Process,
                                health: dict[str, Any] | None = None) -> list[OperationsRecommendation]:
        """Generate continuous improvement recommendations."""
        recs: list[OperationsRecommendation] = []

        if health is None:
            health = self.compute_operational_health(process)

        # Quality improvement
        if process.defect_rate_pct > 5:
            recs.append(OperationsRecommendation(
                title="Reduce defect rate through process improvement",
                description=f"Current defect rate: {process.defect_rate_pct}%",
                priority="high",
                reasoning=f"Defect rate of {process.defect_rate_pct}% indicates quality gaps in the process",
                confidence=0.75,
                assumptions=["Root causes can be identified through analysis"],
                alternatives=[{"action": "Implement statistical process control", "cost": "Medium"},
                              {"action": "Root cause analysis + corrective actions", "cost": "Low"},
                              {"action": "Automated quality inspection", "cost": "High"}],
                expected_impact=f"Reduce defect rate from {process.defect_rate_pct}% to below 2%",
                evidence=[{"type": "defect_rate", "value": process.defect_rate_pct},
                          {"type": "health_score", "value": health["score"]}],
            ))

        # Throughput improvement
        if process.throughput_per_hour > 0:
            rework_steps = [s for s in process.steps if s.rework_pct > 0]
            if rework_steps:
                total_rework_loss = sum(s.rework_pct * s.duration_minutes for s in rework_steps) / 100
                recs.append(OperationsRecommendation(
                    title="Reduce rework to improve throughput",
                    description=f"{len(rework_steps)} step(s) with rework, estimated loss: {total_rework_loss:.1f}m",
                    priority="medium",
                    reasoning="Rework consumes capacity without adding value — reducing it directly increases throughput",
                    confidence=0.7,
                    assumptions=["Rework is due to identifiable process issues"],
                    alternatives=[{"action": "First-pass yield improvement program", "cost": "Medium"},
                                  {"action": "Operator training", "cost": "Low"},
                                  {"action": "Process standardization", "cost": "Medium"}],
                    expected_impact=f"Recover {total_rework_loss:.0f} minutes per cycle",
                    evidence=[{"type": "rework_steps", "count": len(rework_steps),
                               "total_loss": total_rework_loss},
                              {"type": "rework_steps_details",
                               "value": [s.name for s in rework_steps]}],
                ))

        # Uptime improvement
        if process.uptime_pct < 95:
            recs.append(OperationsRecommendation(
                title="Improve operational uptime",
                description=f"Current uptime: {process.uptime_pct}%",
                priority="high",
                reasoning=f"Uptime below 95% threshold indicates reliability issues",
                confidence=0.8,
                assumptions=["Downtime causes are identifiable and addressable"],
                alternatives=[{"action": "Preventive maintenance program", "cost": "Medium"},
                              {"action": "Redundant system deployment", "cost": "High"},
                              {"action": "Real-time monitoring and alerting", "cost": "Low"}],
                expected_impact=f"Increase uptime from {process.uptime_pct}% to 99%+",
                evidence=[{"type": "uptime_pct", "value": process.uptime_pct}],
            ))

        # Setup time improvement
        if process.setup_time_minutes > 30:
            recs.append(OperationsRecommendation(
                title="Reduce setup/changeover time",
                description=f"Current setup time: {process.setup_time_minutes} minutes",
                priority="medium",
                reasoning="Long setup times reduce available production time and increase batch size pressure",
                confidence=0.7,
                assumptions=["SMED (Single Minute Exchange of Die) principles apply"],
                alternatives=[{"action": "SMED implementation", "cost": "Medium"},
                              {"action": "Standardized setup procedures", "cost": "Low"},
                              {"action": "Dedicated setup teams", "cost": "Medium"}],
                expected_impact="Reduce setup time by 50-70%",
                evidence=[{"type": "setup_time", "value": process.setup_time_minutes}],
            ))

        return recs

    # ── Resource Utilization Analysis ────────────────────────────────────

    def analyze_resource_utilization(self, resources: list[Resource]) -> dict[str, Any]:
        """Analyze resource utilization across all resources."""
        if not resources:
            return {"total_resources": 0, "assessment": "no_resources"}

        by_type: dict[str, list[Resource]] = {}
        for r in resources:
            by_type.setdefault(r.resource_type, []).append(r)

        type_analysis = {}
        for rtype, rlist in by_type.items():
            avg_util = sum(r.utilization_pct for r in rlist) / len(rlist)
            overloaded = [r for r in rlist if r.utilization_pct > 90]
            underutilized = [r for r in rlist if r.utilization_pct < 30]
            type_analysis[rtype] = {
                "count": len(rlist),
                "avg_utilization_pct": round(avg_util, 1),
                "overloaded": len(overloaded),
                "underutilized": len(underutilized),
                "total_cost_per_hour": round(sum(r.cost_per_hour for r in rlist), 2),
            }

        overall_avg = sum(r.utilization_pct for r in resources) / len(resources)
        total_overloaded = sum(1 for r in resources if r.utilization_pct > 90)
        total_underutilized = sum(1 for r in resources if r.utilization_pct < 30)

        if overall_avg > 85:
            assessment = "overloaded"
        elif overall_avg < 40:
            assessment = "underutilized"
        else:
            assessment = "balanced"

        return {
            "total_resources": len(resources),
            "overall_avg_utilization_pct": round(overall_avg, 1),
            "overloaded_count": total_overloaded,
            "underutilized_count": total_underutilized,
            "assessment": assessment,
            "by_type": type_analysis,
            "recommendations": self._generate_resource_recs(resources, overall_avg, total_overloaded, total_underutilized),
        }

    def _generate_resource_recs(self, resources: list[Resource],
                                 overall_avg: float, overloaded: int,
                                 underutilized: int) -> list[dict[str, Any]]:
        recs: list[OperationsRecommendation] = []
        if overloaded > 0:
            recs.append(OperationsRecommendation(
                title=f"{overloaded} resource(s) overloaded",
                description=f"Overall utilization: {overall_avg:.0f}%",
                priority="high",
                reasoning="Overloaded resources are bottleneck risks",
                confidence=0.8,
                assumptions=["Current demand patterns continue"],
                alternatives=[{"action": "Add capacity", "cost": "High"},
                              {"action": "Load balancing", "cost": "Low"},
                              {"action": "Prioritize critical work", "cost": "Low"}],
                expected_impact="Reduce overload risk and improve response times",
                evidence=[{"type": "overloaded_count", "value": overloaded},
                          {"type": "overall_utilization", "value": overall_avg}],
            ))
        if underutilized > 0:
            recs.append(OperationsRecommendation(
                title=f"{underutilized} resource(s) underutilized",
                description=f"Overall utilization: {overall_avg:.0f}%",
                priority="medium",
                reasoning="Underutilized resources represent wasted capacity and cost",
                confidence=0.7,
                assumptions=["Demand cannot be increased internally"],
                alternatives=[{"action": "Consolidate and reduce", "cost": "Savings"},
                              {"action": "Retrain/redeploy", "cost": "Low"},
                              {"action": "Offer external services", "cost": "Medium"}],
                expected_impact="Cost reduction of 15-30% on underutilized resources",
                evidence=[{"type": "underutilized_count", "value": underutilized},
                          {"type": "overall_utilization", "value": overall_avg}],
            ))
        return [r.to_dict() for r in recs]

    # ── Disruption and Adaptive Execution ───────────────────────────────

    def assess_disruption(self, process: Process,
                           disruption_description: str,
                           impacted_step_ids: list[str] | None = None) -> dict[str, Any]:
        """Assess the impact of a disruption on an operation."""
        impacted = impacted_step_ids or []
        impacted_steps = [s for s in process.steps if s.step_id in impacted]

        if not impacted_steps and process.steps:
            # Assume all steps impacted if none specified
            impacted_steps = process.steps

        disruption_impact = len(impacted_steps) / max(len(process.steps), 1)
        throughput_loss = disruption_impact * process.throughput_per_hour

        if disruption_impact >= 0.5:
            severity = "critical"
        elif disruption_impact >= 0.25:
            severity = "high"
        elif disruption_impact >= 0.1:
            severity = "medium"
        else:
            severity = "low"

        return {
            "process_id": process.process_id,
            "name": process.name,
            "disruption": disruption_description,
            "impacted_steps": len(impacted_steps),
            "total_steps": len(process.steps),
            "disruption_impact_pct": round(disruption_impact * 100, 1),
            "severity": severity,
            "throughput_loss_per_hour": round(throughput_loss, 2),
            "estimated_recovery_time": self._estimate_recovery(severity),
            "recommendations": self._generate_disruption_recs(process, severity, disruption_description),
        }

    def _estimate_recovery(self, severity: str) -> str:
        estimates = {
            "critical": "days to weeks",
            "high": "hours to days",
            "medium": "minutes to hours",
            "low": "minimal impact — no recovery needed",
        }
        return estimates.get(severity, "unknown")

    def _generate_disruption_recs(self, process: Process, severity: str,
                                   disruption: str) -> list[dict[str, Any]]:
        recs: list[OperationsRecommendation] = []
        recs.append(OperationsRecommendation(
            title=f"Disruption response: {severity} severity",
            description=f"Operation '{process.name}' disrupted by: {disruption}",
            priority="critical" if severity in ("critical", "high") else "high",
            reasoning=f"Disruption impacts {severity} portion of operation",
            confidence=0.85,
            assumptions=["Disruption source is identified and contained"],
            alternatives=[{"action": "Activate contingency plan", "cost": "Variable"},
                          {"action": "Redirect to alternate process", "cost": "Medium"},
                          {"action": "Manual override procedures", "cost": "High"}],
            expected_impact="Contain disruption and resume normal operations",
            evidence=[{"type": "disruption", "value": disruption},
                      {"type": "severity", "value": severity}],
        ))
        return [r.to_dict() for r in recs]

    # ── Explainable Recommendation ──────────────────────────────────────

    def explain(self, rec: OperationsRecommendation) -> dict[str, Any]:
        """Package a recommendation with full explainability structure."""
        return {
            "recommendation": rec.title,
            "description": rec.description,
            "reasoning": rec.reasoning,
            "confidence": rec.confidence,
            "assumptions": rec.assumptions,
            "alternatives": rec.alternatives,
            "expected_impact": rec.expected_impact,
            "evidence": rec.evidence,
            "explanation": "This recommendation is based on the following evidence:",
            "evidence_summary": [
                {"basis": e.get("type", ""), "value": e.get("value", "")}
                for e in rec.evidence
            ],
        }

    # ── AI Context ──────────────────────────────────────────────────────

    def prepare_ai_context(self, process: Process,
                            queues: list[Queue] | None = None,
                            service_levels: list[ServiceLevel] | None = None,
                            resources: list[Resource] | None = None) -> dict[str, Any]:
        """Prepare structured context for AI understanding of operations."""
        queues = queues or []
        service_levels = service_levels or []
        resources = resources or []

        health = self.compute_operational_health(process, queues, service_levels, resources)
        bottlenecks = self.detect_bottlenecks(process)
        process_analysis = self.analyze_process(process)

        return {
            "process": {
                "name": process.name,
                "type": process.ops_type,
                "status": process.status,
                "purpose": process.purpose,
            },
            "process_analysis": process_analysis,
            "health": health,
            "bottlenecks": bottlenecks,
            "queues": [{"name": q.name, "length": q.current_length,
                         "utilization": q.utilization, "is_overloaded": q.is_overloaded}
                       for q in queues],
            "service_levels": [{"name": sl.name, "status": sl.compute_status(),
                                 "compliance_pct": sl.compliance_pct}
                               for sl in service_levels],
            "resources": [{"name": r.name, "type": r.resource_type,
                            "utilization_pct": r.utilization_pct}
                          for r in resources],
        }