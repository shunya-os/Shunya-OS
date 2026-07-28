"""
SHUNYA Universal Planning Runtime — Bootstrap and Middleware
"""

from flask import request, jsonify
from datetime import datetime, timezone

from app.planning.objective import Objective, ObjectiveStatus, get_store as get_obj_store
from app.planning.plan import Plan, Milestone, PlanEngine, PlanStatus, get_engine as get_plan_engine
from app.planning.dependency import Dependency, get_graph as get_dep_graph
from app.planning.checkpoint import Checkpoint, get_engine as get_cp_engine


def register_planning_middleware(app) -> None:
    @app.before_request
    def _check_planning_inspect():
        if request.args.get("inspect_planning"):
            return jsonify(_inspect_planning())
        return None


def _inspect_planning() -> dict:
    return {
        "objectives": {"total": get_obj_store().count, "active": len(get_obj_store().get_active())},
        "plans": {"total": get_plan_engine().count, "active": len(get_plan_engine().get_active())},
        "dependencies": {"total": get_dep_graph().count},
        "checkpoints": {"total": get_cp_engine().count},
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def load_planning_data() -> None:
    obj_store = get_obj_store()
    plan_engine = get_plan_engine()
    dep_graph = get_dep_graph()
    cp_engine = get_cp_engine()

    # Create objective
    obj = Objective(
        objective_id="obj_jupiter",
        purpose="Successfully execute the Jupiter Media partnership across 3 regions",
        priority=1,
        owner_actor_id="actor_sarah",
        stakeholder_ids=["actor_marcus", "actor_ai"],
        expected_outcomes=[
            "Content distribution live in NA, EU, APAC",
            "Revenue share 60/40 achieved",
            "Quarterly review cadence established",
        ],
        constraints=["18-month minimum engagement", "Regulatory clearance per region"],
        evidence_requirements=["Signed contract", "Regulatory clearance docs", "Q1 performance report"],
        status=ObjectiveStatus.ACTIVE,
    )
    obj_store.add(obj)

    # Create plan with milestones
    milestones = [
        Milestone(milestone_id="ms_na", plan_id="plan_ju001", label="NA region launch", description="Launch content distribution in North America", order=1, responsible_actor_id="actor_sarah"),
        Milestone(milestone_id="ms_eu", plan_id="plan_ju001", label="EU region launch", description="Launch content distribution in Europe", order=2, responsible_actor_id="actor_sarah"),
        Milestone(milestone_id="ms_apac", plan_id="plan_ju001", label="APAC region launch", description="Launch content distribution in Asia-Pacific", order=3, responsible_actor_id="actor_sarah"),
        Milestone(milestone_id="ms_review", plan_id="plan_ju001", label="First quarterly review", description="Schedule and conduct first quarterly performance review", order=4, responsible_actor_id="actor_marcus"),
    ]
    plan = plan_engine.create_plan("obj_jupiter", "Jupiter Media Partnership Execution", milestones, "Execute the Jupiter Media partnership across all 3 regions")
    plan.transition_to(PlanStatus.ACTIVE)

    # Add dependencies
    dep_graph.add(Dependency(dep_id="dep_na_to_eu", source_id="ms_na", target_id="ms_eu", dep_type="finish_to_start", label="NA must complete before EU"))
    dep_graph.add(Dependency(dep_id="dep_eu_to_apac", source_id="ms_eu", target_id="ms_apac", dep_type="finish_to_start", label="EU must complete before APAC"))

    # Add checkpoints
    for ms in milestones:
        cp = Checkpoint(
            checkpoint_id=f"cp_{ms.milestone_id}",
            milestone_id=ms.milestone_id,
            label=f"Verify {ms.label} completion",
            description=f"Evidence required: {ms.label} deliverables signed off",
            evidence_required="Signed delivery confirmation",
            action_on_fail="escalate",
        )
        cp_engine.add(cp)