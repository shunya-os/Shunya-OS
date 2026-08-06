"""Universal Operations Intelligence — Runtime.

OperationsIntelligenceRuntime composes from all frozen UCPs:
Journey (UCP-01), Relationship (UCP-02), Financial (UCP-03), Knowledge (UCP-04),
Decision (UCP-05), Agreement (UCP-06), Asset (UCP-07), Initiative (UCP-08).

No Operations Runtime. No ERP Runtime. No Workflow Runtime.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from core.operations_intelligence.engine import OperationsIntelligenceEngine
from core.operations_intelligence.models import (
    OperationsProfile,
    Process,
    ProcessStep,
    Workflow,
    WorkflowStep,
    SOP,
    Resource,
    CapacityPlan,
    Queue,
    Bottleneck,
    ThroughputMeasure,
    ServiceLevel,
    ContinuousImprovement,
    OperationsRecommendation,
    OperationsStatus,
    OperationsType,
    ResourceType,
    _generate_id,
    _now_iso,
)

logger = logging.getLogger(__name__)


class OperationsIntelligenceRuntime:
    """Universal Operations Intelligence — single capability runtime.

    Composes from frozen UCPs. Exposes operations capabilities only:
    processes, workflows, SOPs, resources, capacity, queues, bottlenecks,
    throughput, service levels, operational health, continuous improvement.
    """

    def __init__(self) -> None:
        self._engine = OperationsIntelligenceEngine()
        self._profiles: dict[str, OperationsProfile] = {}
        self._reality_listeners: list[Callable[[dict[str, Any]], None]] = []

    # ── Profile Management ───────────────────────────────────────────────

    def get_or_create_profile(self, owner_id: str, label: str = "") -> OperationsProfile:
        for p in self._profiles.values():
            if p.owner_id == owner_id:
                return p
        profile = OperationsProfile(
            owner_id=owner_id,
            label=label or f"Operations profile for {owner_id}",
        )
        self._profiles[profile.profile_id] = profile
        return profile

    def get_profile(self, profile_id: str) -> OperationsProfile | None:
        return self._profiles.get(profile_id)

    def _resolve(self, owner_id: str) -> OperationsProfile | None:
        for p in self._profiles.values():
            if p.owner_id == owner_id:
                return p
        return None

    # ── Process Management ───────────────────────────────────────────────

    def create_process(
        self,
        owner_id: str,
        ops_type: str = OperationsType.OTHER.value,
        name: str = "",
        purpose: str = "",
        scope: str = "",
        steps: list[dict[str, Any]] | None = None,
        cycle_time_minutes: float = 0.0,
        throughput_per_hour: float = 0.0,
        defect_rate_pct: float = 0.0,
        uptime_pct: float = 100.0,
        setup_time_minutes: float = 0.0,
        batch_size: int = 1,
    ) -> Process | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        process = Process(
            owner_id=owner_id,
            ops_type=ops_type,
            name=name,
            purpose=purpose,
            scope=scope,
            steps=[ProcessStep(**s) for s in (steps or [])],
            cycle_time_minutes=cycle_time_minutes,
            throughput_per_hour=throughput_per_hour,
            defect_rate_pct=defect_rate_pct,
            uptime_pct=uptime_pct,
            setup_time_minutes=setup_time_minutes,
            batch_size=batch_size,
        )
        profile.processes.append(process)
        profile.updated_at = _now_iso()
        self._notify({"type": "operations.process_created", "owner_id": owner_id,
                       "process_id": process.process_id, "name": name})
        return process

    def get_process(self, owner_id: str, process_id: str) -> Process | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        for p in profile.processes:
            if p.process_id == process_id:
                return p
        return None

    def update_process_metrics(self, owner_id: str, process_id: str,
                               **metrics: Any) -> bool:
        process = self.get_process(owner_id, process_id)
        if not process:
            return False
        for key, value in metrics.items():
            if hasattr(process, key):
                setattr(process, key, value)
        process.updated_at = _now_iso()
        return True

    # ── Workflow Management ──────────────────────────────────────────────

    def create_workflow(
        self,
        owner_id: str,
        ops_type: str = OperationsType.OTHER.value,
        name: str = "",
        purpose: str = "",
        trigger: str = "",
        steps: list[dict[str, Any]] | None = None,
        sla_minutes: float = 0.0,
        escalation_path: list[str] | None = None,
    ) -> Workflow | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        workflow = Workflow(
            owner_id=owner_id,
            ops_type=ops_type,
            name=name,
            purpose=purpose,
            trigger=trigger,
            steps=[WorkflowStep(**s) for s in (steps or [])],
            sla_minutes=sla_minutes,
            escalation_path=escalation_path or [],
        )
        profile.workflows.append(workflow)
        profile.updated_at = _now_iso()
        self._notify({"type": "operations.workflow_created", "owner_id": owner_id,
                       "workflow_id": workflow.workflow_id, "name": name})
        return workflow

    def get_workflow(self, owner_id: str, workflow_id: str) -> Workflow | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        for w in profile.workflows:
            if w.workflow_id == workflow_id:
                return w
        return None

    def advance_workflow(self, owner_id: str, workflow_id: str) -> bool:
        workflow = self.get_workflow(owner_id, workflow_id)
        if not workflow:
            return False
        if workflow.current_step_index >= workflow.step_count:
            return False
        workflow.current_step_index += 1
        workflow.updated_at = _now_iso()
        if workflow.current_step_index >= workflow.step_count:
            workflow.status = OperationsStatus.COMPLETED.value
            self._notify({"type": "operations.workflow_completed", "owner_id": owner_id,
                           "workflow_id": workflow_id})
        return True

    # ── SOP Management ───────────────────────────────────────────────────

    def create_sop(
        self,
        owner_id: str,
        ops_type: str = OperationsType.OTHER.value,
        name: str = "",
        purpose: str = "",
        instructions: list[str] | None = None,
        prerequisites: list[str] | None = None,
        quality_criteria: list[str] | None = None,
        safety_notes: list[str] | None = None,
        review_interval_days: int = 365,
    ) -> SOP | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        sop = SOP(
            owner_id=owner_id,
            ops_type=ops_type,
            name=name,
            purpose=purpose,
            instructions=instructions or [],
            prerequisites=prerequisites or [],
            quality_criteria=quality_criteria or [],
            safety_notes=safety_notes or [],
            review_interval_days=review_interval_days,
            last_reviewed=_now_iso(),
        )
        profile.sops.append(sop)
        profile.updated_at = _now_iso()
        return sop

    def get_sop(self, owner_id: str, sop_id: str) -> SOP | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        for s in profile.sops:
            if s.sop_id == sop_id:
                return s
        return None

    # ── Resource Management ──────────────────────────────────────────────

    def add_resource(
        self,
        owner_id: str,
        resource_type: str = ResourceType.OTHER.value,
        name: str = "",
        capacity_per_hour: float = 0.0,
        current_load: float = 0.0,
        efficiency_pct: float = 100.0,
        cost_per_hour: float = 0.0,
        downtime_pct: float = 0.0,
        skills: list[str] | None = None,
    ) -> Resource | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        resource = Resource(
            owner_id=owner_id,
            resource_type=resource_type,
            name=name,
            capacity_per_hour=capacity_per_hour,
            current_load=current_load,
            efficiency_pct=efficiency_pct,
            cost_per_hour=cost_per_hour,
            downtime_pct=downtime_pct,
            skills=skills or [],
        )
        profile.resources.append(resource)
        profile.updated_at = _now_iso()
        self._notify({"type": "operations.resource_added", "owner_id": owner_id,
                       "resource_id": resource.resource_id, "name": name})
        return resource

    def update_resource_load(self, owner_id: str, resource_id: str, load: float) -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        for r in profile.resources:
            if r.resource_id == resource_id:
                r.current_load = load
                r.updated_at = _now_iso()
                return True
        return False

    # ── Capacity Planning ────────────────────────────────────────────────

    def create_capacity_plan(
        self,
        owner_id: str,
        name: str = "",
        resource_ids: list[str] | None = None,
        target_utilization_pct: float = 80.0,
        buffer_pct: float = 20.0,
        period_start: str = "",
        period_end: str = "",
    ) -> CapacityPlan | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        resources = []
        if resource_ids:
            for rid in resource_ids:
                for r in profile.resources:
                    if r.resource_id == rid:
                        resources.append(r)
        plan = CapacityPlan(
            owner_id=owner_id,
            name=name,
            resources=resources,
            target_utilization_pct=target_utilization_pct,
            buffer_pct=buffer_pct,
            period_start=period_start,
            period_end=period_end,
        )
        profile.capacity_plans.append(plan)
        profile.updated_at = _now_iso()
        return plan

    # ── Queue Management ─────────────────────────────────────────────────

    def add_queue(
        self,
        owner_id: str,
        process_id: str = "",
        name: str = "",
        current_length: int = 0,
        arrival_rate_per_hour: float = 0.0,
        service_rate_per_hour: float = 0.0,
        discipline: str = "fifo",
        average_wait_time_minutes: float = 0.0,
    ) -> Queue | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        queue = Queue(
            owner_id=owner_id,
            process_id=process_id,
            name=name,
            current_length=current_length,
            arrival_rate_per_hour=arrival_rate_per_hour,
            service_rate_per_hour=service_rate_per_hour,
            discipline=discipline,
            average_wait_time_minutes=average_wait_time_minutes,
        )
        profile.queues.append(queue)
        profile.updated_at = _now_iso()
        return queue

    # ── Throughput Measures ─────────────────────────────────────────────

    def add_throughput_measure(
        self,
        owner_id: str,
        process_id: str = "",
        period_start: str = "",
        period_end: str = "",
        units_processed: int = 0,
        units_defective: int = 0,
        total_time_hours: float = 0.0,
    ) -> ThroughputMeasure | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        measure = ThroughputMeasure(
            owner_id=owner_id,
            process_id=process_id,
            period_start=period_start,
            period_end=period_end,
            units_processed=units_processed,
            units_defective=units_defective,
            total_time_hours=total_time_hours,
            good_units=units_processed - units_defective,
        )
        profile.throughput_measures.append(measure)
        profile.updated_at = _now_iso()
        return measure

    # ── Service Levels ───────────────────────────────────────────────────

    def add_service_level(
        self,
        owner_id: str,
        process_id: str = "",
        name: str = "",
        metric: str = "",
        target: float = 0.0,
        actual: float = 0.0,
        warning_threshold: float = 0.0,
        period: str = "daily",
    ) -> ServiceLevel | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        sl = ServiceLevel(
            owner_id=owner_id,
            process_id=process_id,
            name=name,
            metric=metric,
            target=target,
            actual=actual,
            warning_threshold=warning_threshold,
            period=period,
        )
        sl.status = sl.compute_status()
        profile.service_levels.append(sl)
        profile.updated_at = _now_iso()
        return sl

    def update_service_level(self, owner_id: str, sl_id: str, actual: float) -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        for sl in profile.service_levels:
            if sl.sl_id == sl_id:
                sl.actual = actual
                sl.status = sl.compute_status()
                sl.updated_at = _now_iso()
                return True
        return False

    # ── Continuous Improvement ───────────────────────────────────────────

    def add_improvement_item(
        self,
        owner_id: str,
        process_id: str = "",
        name: str = "",
        description: str = "",
        methodology: str = "kaizen",
        current_state: str = "",
        target_state: str = "",
        expected_benefit: str = "",
        metrics_before: dict[str, float] | None = None,
        priority: str = "medium",
    ) -> ContinuousImprovement | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        item = ContinuousImprovement(
            owner_id=owner_id,
            process_id=process_id,
            name=name,
            description=description,
            methodology=methodology,
            current_state=current_state,
            target_state=target_state,
            expected_benefit=expected_benefit,
            metrics_before=metrics_before or {},
            priority=priority,
        )
        profile.improvement_items.append(item)
        profile.updated_at = _now_iso()
        return item

    def complete_improvement_item(
        self,
        owner_id: str,
        ci_id: str,
        metrics_after: dict[str, float] | None = None,
    ) -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        for ci in profile.improvement_items:
            if ci.ci_id == ci_id:
                ci.status = "completed"
                ci.metrics_after = metrics_after or {}
                ci.updated_at = _now_iso()
                return True
        return False

    # ── Bottleneck Recording ─────────────────────────────────────────────

    def record_bottleneck(
        self,
        owner_id: str,
        process_id: str = "",
        step_id: str = "",
        resource_id: str = "",
        name: str = "",
        current_throughput: float = 0.0,
        max_throughput: float = 0.0,
        impact_pct: float = 0.0,
        queue_length: int = 0,
        contributing_factors: list[str] | None = None,
    ) -> Bottleneck | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        bottleneck = Bottleneck(
            owner_id=owner_id,
            process_id=process_id,
            step_id=step_id,
            resource_id=resource_id,
            name=name,
            current_throughput=current_throughput,
            max_throughput=max_throughput,
            impact_pct=impact_pct,
            queue_length=queue_length,
            contributing_factors=contributing_factors or [],
        )
        profile.bottlenecks.append(bottleneck)
        profile.updated_at = _now_iso()
        self._notify({"type": "operations.bottleneck_detected", "owner_id": owner_id,
                       "bottleneck_id": bottleneck.bottleneck_id, "name": name})
        return bottleneck

    def resolve_bottleneck(self, owner_id: str, bottleneck_id: str,
                           resolution: str = "") -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        for b in profile.bottlenecks:
            if b.bottleneck_id == bottleneck_id:
                b.resolution = resolution
                b.resolved_at = _now_iso()
                b.updated_at = _now_iso()
                self._notify({"type": "operations.bottleneck_resolved", "owner_id": owner_id,
                               "bottleneck_id": bottleneck_id})
                return True
        return False

    # ── Analysis ─────────────────────────────────────────────────────────

    def analyze(self, owner_id: str, process_id: str) -> dict[str, Any] | None:
        process = self.get_process(owner_id, process_id)
        if not process:
            return None
        profile = self._resolve(owner_id)
        queues = [q for q in profile.queues if q.process_id == process_id] if profile else []
        service_levels = [sl for sl in profile.service_levels if sl.process_id == process_id] if profile else []
        resources = list(profile.resources) if profile else []
        improvement_items = [ci for ci in profile.improvement_items if ci.process_id == process_id] if profile else []

        return {
            "process": process.to_dict(),
            "process_analysis": self._engine.analyze_process(process),
            "bottlenecks": self._engine.detect_bottlenecks(process),
            "health": self._engine.compute_operational_health(
                process, queues, service_levels, resources, improvement_items),
            "queues": [self._engine.analyze_queue(q) for q in queues],
            "service_levels": self._engine.monitor_service_levels(service_levels),
            "throughput": self._engine.analyze_throughput(process),
            "resources": self._engine.analyze_resource_utilization(resources),
        }

    def analyze_capacity(self, owner_id: str, cap_id: str) -> dict[str, Any] | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        for plan in profile.capacity_plans:
            if plan.cap_id == cap_id:
                return self._engine.analyze_capacity(plan)
        return None

    def analyze_workflow(self, owner_id: str, workflow_id: str) -> dict[str, Any] | None:
        workflow = self.get_workflow(owner_id, workflow_id)
        if not workflow:
            return None
        return self._engine.analyze_workflow(workflow)

    # ── Recommendations ──────────────────────────────────────────────────

    def get_recommendations(self, owner_id: str, process_id: str) -> list[dict[str, Any]]:
        """Generate explainable recommendations for a process."""
        process = self.get_process(owner_id, process_id)
        if not process:
            return []
        profile = self._resolve(owner_id)
        queues = [q for q in profile.queues if q.process_id == process_id] if profile else []
        service_levels = [sl for sl in profile.service_levels if sl.process_id == process_id] if profile else []
        resources = list(profile.resources) if profile else []
        improvement_items = [ci for ci in profile.improvement_items if ci.process_id == process_id] if profile else []

        recs: list[OperationsRecommendation] = []
        recs.extend(self._engine.recommend_improvements(process))
        for q in queues:
            queue_analysis = self._engine.analyze_queue(q)
            for rec_dict in queue_analysis.get("recommendations", []):
                recs.append(self._from_dict(rec_dict))
        for sl_result in self._engine.monitor_service_levels(service_levels):
            if "recommendation" in sl_result:
                recs.append(self._from_dict(sl_result["recommendation"]))

        return [r.to_dict() for r in recs]

    def _from_dict(self, d: dict[str, Any]) -> OperationsRecommendation:
        return OperationsRecommendation(
            rec_id=d.get("rec_id", _generate_id()),
            title=d.get("title", ""),
            description=d.get("description", ""),
            priority=d.get("priority", "medium"),
            reasoning=d.get("reasoning", ""),
            confidence=d.get("confidence", 0.0),
            assumptions=d.get("assumptions", []),
            alternatives=d.get("alternatives", []),
            expected_impact=d.get("expected_impact", ""),
            evidence=d.get("evidence", []),
        )

    # ── Disruption & Adaptive Execution ─────────────────────────────────

    def assess_disruption(self, owner_id: str, process_id: str,
                          disruption_description: str,
                          impacted_step_ids: list[str] | None = None) -> dict[str, Any] | None:
        process = self.get_process(owner_id, process_id)
        if not process:
            return None
        return self._engine.assess_disruption(process, disruption_description, impacted_step_ids)

    # ── Explainability ───────────────────────────────────────────────────

    def explain(self, rec: dict[str, Any]) -> dict[str, Any]:
        """Explain a recommendation with full structure."""
        return self._engine.explain(self._from_dict(rec))

    # ── Composition with Frozen UCPs ─────────────────────────────────────

    def compose(self, owner_id: str) -> dict[str, Any]:
        """Compose operations context from all frozen UCP runtimes."""
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        composition: dict[str, Any] = {
            "operations": profile.to_dict(),
            "composed_ucps": [],
        }

        # UCP-08 Initiative Intelligence
        try:
            from core.initiative_intelligence import InitiativeIntelligenceRuntime
            ini_runtime = InitiativeIntelligenceRuntime()
            ini_profile = ini_runtime.get_or_create_profile(owner_id, f"Initiatives for {owner_id}")
            composition["initiatives"] = {
                "profile_id": ini_profile.profile_id,
                "count": len(ini_profile.initiatives),
                "active": len(ini_profile.active_initiatives),
            }
            composition["composed_ucps"].append("initiative_intelligence")
        except Exception as e:  # pragma: no cover
            composition["initiatives"] = {"error": str(e)}

        # UCP-07 Asset Intelligence
        try:
            from core.asset_intelligence import AssetIntelligenceRuntime
            asset_runtime = AssetIntelligenceRuntime()
            asset_profile = asset_runtime.get_or_create_profile(owner_id, f"Assets for {owner_id}")
            composition["assets"] = {
                "profile_id": asset_profile.profile_id,
                "count": getattr(asset_profile, "total_assets", len(getattr(asset_profile, "assets", []))),
            }
            composition["composed_ucps"].append("asset_intelligence")
        except Exception as e:  # pragma: no cover
            composition["assets"] = {"error": str(e)}

        # UCP-06 Agreement Intelligence
        try:
            from core.agreement_intelligence import AgreementIntelligenceRuntime
            agreement_runtime = AgreementIntelligenceRuntime()
            agreement_profile = agreement_runtime.get_or_create_profile(owner_id, f"Agreements for {owner_id}")
            composition["agreements"] = {
                "profile_id": agreement_profile.profile_id,
                "count": getattr(agreement_profile, "total_agreements", len(getattr(agreement_profile, "agreements", []))),
            }
            composition["composed_ucps"].append("agreement_intelligence")
        except Exception as e:  # pragma: no cover
            composition["agreements"] = {"error": str(e)}

        # UCP-05 Decision Intelligence
        try:
            from core.decision_intelligence import DecisionIntelligenceRuntime
            decision_runtime = DecisionIntelligenceRuntime()
            decision_profile = decision_runtime.get_or_create_profile(owner_id, f"Decisions for {owner_id}")
            composition["decisions"] = {
                "profile_id": decision_profile.profile_id,
            }
            composition["composed_ucps"].append("decision_intelligence")
        except Exception as e:  # pragma: no cover
            composition["decisions"] = {"error": str(e)}

        # UCP-04 Knowledge Intelligence
        try:
            from core.knowledge_intelligence import KnowledgeIntelligenceRuntime
            knowledge_runtime = KnowledgeIntelligenceRuntime()
            composition["knowledge"] = {"status": "available"}
            composition["composed_ucps"].append("knowledge_intelligence")
        except Exception as e:  # pragma: no cover
            composition["knowledge"] = {"error": str(e)}

        # UCP-03 Financial Intelligence
        try:
            from core.financial_intelligence import FinancialIntelligenceRuntime
            financial_runtime = FinancialIntelligenceRuntime()
            financial_profile = financial_runtime.get_or_create_profile(owner_id, f"Finances for {owner_id}")
            composition["financial"] = {
                "profile_id": financial_profile.profile_id,
            }
            composition["composed_ucps"].append("financial_intelligence")
        except Exception as e:  # pragma: no cover
            composition["financial"] = {"error": str(e)}

        # UCP-02 Relationship Intelligence
        try:
            from core.relationship_intelligence import RelationshipIntelligenceRuntime
            relationship_runtime = RelationshipIntelligenceRuntime()
            relationship_profile = relationship_runtime.get_or_create_profile(owner_id, f"Relationships for {owner_id}")
            composition["relationships"] = {
                "profile_id": relationship_profile.profile_id,
            }
            composition["composed_ucps"].append("relationship_intelligence")
        except Exception as e:  # pragma: no cover
            composition["relationships"] = {"error": str(e)}

        # UCP-01 Journey Intelligence
        try:
            from core.journey_intelligence import JourneyIntelligenceRuntime
            journey_runtime = JourneyIntelligenceRuntime()
            journey_profile = journey_runtime.get_or_create_profile(owner_id, f"Journey for {owner_id}")
            composition["journey"] = {
                "profile_id": journey_profile.profile_id,
            }
            composition["composed_ucps"].append("journey_intelligence")
        except Exception as e:  # pragma: no cover
            composition["journey"] = {"error": str(e)}

        return composition

    # ── Reality Integration ──────────────────────────────────────────────

    def notify(self, notification: dict[str, Any]) -> None:
        ntype = notification.get("type", "")
        owner_id = notification.get("owner_id", "")

        if ntype == "operations.process_metrics_updated":
            pid = notification.get("process_id", "")
            metrics = notification.get("metrics", {})
            if owner_id and pid:
                self.update_process_metrics(owner_id, pid, **metrics)

        elif ntype == "operations.resource_load_updated":
            rid = notification.get("resource_id", "")
            load = notification.get("load", 0.0)
            if owner_id and rid:
                self.update_resource_load(owner_id, rid, load)

        elif ntype == "operations.service_level_updated":
            sl_id = notification.get("sl_id", "")
            actual = notification.get("actual", 0.0)
            if owner_id and sl_id:
                self.update_service_level(owner_id, sl_id, actual)

    def register_execution_actions(self, execution_runtime: Any) -> None:
        try:
            from core.execution_runtime.models import ActionContract
        except ImportError:
            return
        execution_runtime.register_action("operations.analyze", ActionContract(
            action_id="operations.analyze",
            description="Analyze an operation with full intelligence",
            input_schema={"type": "object", "properties": {
                "owner_id": {"type": "string"}, "process_id": {"type": "string"},
            }, "required": ["owner_id", "process_id"]},
            output_schema={"type": "object"},
        ), handler=self.analyze)

    def initialize(self) -> None:
        logger.info("OperationsIntelligenceRuntime initialized")

    def shutdown(self) -> None:
        self._profiles.clear()
        self._reality_listeners.clear()
        logger.info("OperationsIntelligenceRuntime shut down")

    def health_check(self) -> dict[str, Any]:
        return {"status": "healthy", "runtime": "operations_intelligence",
                "profile_count": len(self._profiles)}

    def handle_event(self, event: Any) -> None:
        if isinstance(event, dict):
            self.notify(event)

    def get_capabilities(self) -> list[str]:
        return [
            "operations.profile",
            "operations.process",
            "operations.workflow",
            "operations.sop",
            "operations.resource",
            "operations.capacity",
            "operations.queue",
            "operations.bottleneck",
            "operations.throughput",
            "operations.service_level",
            "operations.health",
            "operations.improvement",
            "operations.disruption",
            "operations.compose",
            "operations.reality_integration",
        ]

    def _notify(self, notification: dict[str, Any]) -> None:
        for listener in self._reality_listeners:
            try:
                listener(notification)
            except Exception:
                logger.exception("Listener failed")

    def register_reality_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        self._reality_listeners.append(listener)

    def unregister_reality_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        if listener in self._reality_listeners:
            self._reality_listeners.remove(listener)