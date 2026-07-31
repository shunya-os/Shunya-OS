"""
SHUNYA Autonomous Organization Runtime — Bootstrap and Middleware
"""

from flask import request, jsonify
from datetime import datetime, timezone

from app.organization.actor import Actor, ActorCapability, get_store as get_actor_store
from app.organization.responsibility import (
    Responsibility, Delegation, DelegationStatus, get_graph,
)
from app.organization.escalation import EscalationRule, get_engine as get_esc_engine
from app.organization.coordination import CoordinationSession, get_store as get_coord_store


def register_organization_middleware(app) -> None:
    @app.before_request
    def _check_org_inspect():
        if request.args.get("inspect_org"):
            return jsonify(_inspect_org())
        return None


def _inspect_org() -> dict:
    actor_store = get_actor_store()
    graph = get_graph()
    esc = get_esc_engine()
    coord = get_coord_store()

    return {
        "actors": {
            "total": actor_store.count,
            "available": len(actor_store.get_available()),
            "items": [a.to_dict() for a in actor_store._actors.values()],
        },
        "responsibilities": {
            "total": graph.count,
        },
        "delegations": {
            "total": len(graph._delegations),
        },
        "escalations": {
            "rules": esc.count,
            "events": esc.event_count,
        },
        "coordination": {
            "total": coord.count,
            "active": len(coord.get_active()),
        },
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def load_organization_data() -> None:
    """Load demo organization data. Creates sample actors and responsibilities."""
    actor_store = get_actor_store()
    graph = get_graph()
    esc = get_esc_engine()
    coord = get_coord_store()

    # ─── Create sample actors (business agnostic types) ───
    actors = [
        Actor(actor_id="actor_sarah", name="Sarah Chen", actor_type="human",
              capabilities=[ActorCapability("cap_legal", "Legal Review"), ActorCapability("cap_contract", "Contract Management")],
              max_concurrent_responsibilities=3),
        Actor(actor_id="actor_marcus", name="Marcus Webb", actor_type="human",
              capabilities=[ActorCapability("cap_finance", "Financial Analysis"), ActorCapability("cap_budget", "Budget Planning")],
              max_concurrent_responsibilities=4),
        Actor(actor_id="actor_ai", name="SHUNYA Intelligence", actor_type="ai_agent",
              capabilities=[ActorCapability("cap_analysis", "Data Analysis"), ActorCapability("cap_insight", "Insight Generation")],
              max_concurrent_responsibilities=10),
        Actor(actor_id="actor_legal_team", name="Legal Team", actor_type="team",
              capabilities=[ActorCapability("cap_compliance", "Compliance Review")],
              max_concurrent_responsibilities=8),
        Actor(actor_id="actor_ext_auditor", name="External Auditor", actor_type="vendor",
              capabilities=[ActorCapability("cap_audit", "Financial Audit")],
              max_concurrent_responsibilities=2),
    ]
    for a in actors:
        actor_store.add(a)

    # ─── Create escalation rules ───
    esc.add_rule(EscalationRule(
        rule_id="esc_time_48h", name="48-Hour Escalation", rule_type="time_based",
        condition_description="Escalate if delegation exceeds 48 hours without acceptance",
        priority=100, max_wait_hours=48,
    ))
    esc.add_rule(EscalationRule(
        rule_id="esc_capacity_90", name="Capacity Overload Escalation",
        rule_type="capacity_based",
        condition_description="Escalate if delegate capacity exceeds 90%",
        priority=80, max_capacity_ratio=0.9,
    ))