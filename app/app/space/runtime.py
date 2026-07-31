"""SHUNYA Phase A1 — Space Runtime Bootstrap.

Loads demo data and registers Space middleware.
"""
from flask import request, jsonify
from datetime import datetime, timezone

from app.space.store import get_store, reset_store
from app.space.renderer import get_renderer, reset_renderer
from app.space.navigation import get_navigator, reset_navigator
from app.space.models import (
    SpaceRelationshipRef, SpaceTimelineEvent, SpaceKnowledgeItem,
    SpacePlanRef, SpaceMetric, SpaceCommunicationRef, SpaceDocumentRef,
    SpaceResponsibility, SpaceAIUnderstanding,
)


def register_space_middleware(app) -> None:
    """Register Space inspection middleware."""
    from app.space.routes import space_bp
    app.register_blueprint(space_bp)

    @app.before_request
    def _check_space_inspect():
        if request.args.get("inspect_space"):
            return jsonify(_inspect_space())
        return None


def _inspect_space() -> dict:
    store = get_store()
    navigator = get_navigator()
    return {
        "spaces": {
            "total": store.count,
            "by_type": _count_by_type(store),
        },
        "navigation": {
            "total_spaces": store.count,
        },
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _count_by_type(store) -> dict:
    counts = {}
    for space in store.list_all():
        t = space.identity.entity_type
        counts[t] = counts.get(t, 0) + 1
    return counts


def load_space_data() -> None:
    """Load demo Space data for development/testing.

    Creates Spaces for common entity types to demonstrate the
    universal Space model. All Spaces share the same architecture.
    """
    store = get_store()
    if store.count > 0:
        return  # Already loaded

    # Load default capability mappings
    from app.space.capabilities import get_registry
    get_registry().load_default_mappings()

    # --- Customer Space ---
    customer = store.create(
        entity_id="ent_customer_001",
        entity_type="customer",
        name="Acme Corporation",
        aliases=["Acme Corp", "ACME"],
    )
    store.add_relationship(customer.space_id, SpaceRelationshipRef(
        rel_id="rel_cust_001",
        target_entity_id="ent_company_001",
        target_entity_name="SHUNYA OS",
        target_entity_type="company",
        rel_type="client_of",
        direction="outgoing",
    ))
    store.add_relationship(customer.space_id, SpaceRelationshipRef(
        rel_id="rel_cust_002",
        target_entity_id="ent_project_001",
        target_entity_name="Q4 Implementation",
        target_entity_type="project",
        rel_type="has_project",
        direction="outgoing",
    ))
    store.add_timeline_event(customer.space_id, SpaceTimelineEvent(
        event_id="tev_cust_001",
        event_type="created",
        timestamp=datetime.now(timezone.utc).isoformat(),
        title="Customer added",
        description="Acme Corporation added as a customer",
        category="observation",
        importance=0.5,
    ))
    store.add_knowledge(customer.space_id, SpaceKnowledgeItem(
        item_id="kn_cust_001",
        item_type="document",
        title="Acme Corp - Master Service Agreement",
        content_summary="Master Service Agreement signed on 2025-01-15",
    ))
    store.add_plan(customer.space_id, SpacePlanRef(
        plan_id="pln_cust_001",
        title="Q4 Onboarding Plan",
        state="active",
        priority="high",
    ))
    store.add_metric(customer.space_id, SpaceMetric(
        metric_id="met_cust_001",
        name="Customer Health",
        value="healthy",
        trend="improving",
        confidence=0.85,
    ))
    store.update_ai_understanding(customer.space_id, SpaceAIUnderstanding(
        summary="Acme Corporation is a key customer in Q4 implementation phase",
        goals=["Complete Q4 onboarding", "Renew annual contract"],
        current_risks=["Implementation timeline risk"],
        current_opportunities=["Upsell opportunity in Q1"],
    ))

    # --- Supplier Space ---
    supplier = store.create(
        entity_id="ent_supplier_001",
        entity_type="supplier",
        name="Global Logistics Inc",
        aliases=["GLI", "Global Logistics"],
    )
    store.add_relationship(supplier.space_id, SpaceRelationshipRef(
        rel_id="rel_sup_001",
        target_entity_id="ent_company_001",
        target_entity_name="SHUNYA OS",
        target_entity_type="company",
        rel_type="supplies",
        direction="outgoing",
    ))
    store.add_timeline_event(supplier.space_id, SpaceTimelineEvent(
        event_id="tev_sup_001",
        event_type="contract_signed",
        timestamp=datetime.now(timezone.utc).isoformat(),
        title="Contract signed",
        description="Annual logistics contract renewed",
        category="approval",
        importance=0.8,
    ))
    store.add_metric(supplier.space_id, SpaceMetric(
        metric_id="met_sup_001",
        name="Supplier Performance",
        value=94,
        unit="%",
        trend="improving",
        confidence=0.9,
    ))

    # --- Project Space ---
    project = store.create(
        entity_id="ent_project_001",
        entity_type="project",
        name="Q4 Implementation",
        parent_space_id=customer.space_id,
    )
    store.add_child(customer.space_id, project.space_id)
    store.add_relationship(project.space_id, SpaceRelationshipRef(
        rel_id="rel_proj_001",
        target_entity_id="ent_customer_001",
        target_entity_name="Acme Corporation",
        target_entity_type="customer",
        rel_type="for_customer",
        direction="outgoing",
    ))
    store.add_timeline_event(project.space_id, SpaceTimelineEvent(
        event_id="tev_proj_001",
        event_type="milestone",
        timestamp=datetime.now(timezone.utc).isoformat(),
        title="Milestone 1 completed",
        description="Requirements gathering phase completed",
        category="execution",
        importance=0.7,
    ))
    store.add_plan(project.space_id, SpacePlanRef(
        plan_id="pln_proj_001",
        title="Sprint 1",
        state="active",
        priority="high",
    ))
    store.add_plan(project.space_id, SpacePlanRef(
        plan_id="pln_proj_002",
        title="Sprint 2",
        state="proposed",
        priority="normal",
    ))
    store.add_metric(project.space_id, SpaceMetric(
        metric_id="met_proj_001",
        name="Progress",
        value=35,
        unit="%",
        trend="improving",
        confidence=0.8,
    ))

    # --- Employee Space ---
    employee = store.create(
        entity_id="ent_employee_001",
        entity_type="employee",
        name="Sarah Chen",
        aliases=["Sarah C.", "sarah.chen@shunya.com"],
    )
    store.add_relationship(employee.space_id, SpaceRelationshipRef(
        rel_id="rel_emp_001",
        target_entity_id="ent_project_001",
        target_entity_name="Q4 Implementation",
        target_entity_type="project",
        rel_type="works_on",
        direction="outgoing",
    ))
    store.add_communication(employee.space_id, SpaceCommunicationRef(
        comm_id="comm_emp_001",
        subject="Q4 Implementation status update",
        channel="email",
        participants=["Sarah Chen", "John Smith"],
        summary="Discussed timeline for Milestone 2",
    ))
    store.add_responsibility(employee.space_id, SpaceResponsibility(
        responsibility_id="resp_emp_001",
        actor="Sarah Chen",
        description="Lead Q4 Implementation",
        status="active",
    ))
    store.update_ai_understanding(employee.space_id, SpaceAIUnderstanding(
        summary="Sarah Chen is the lead on Q4 Implementation",
        goals=["Deliver Milestone 2 by end of month"],
        current_responsibilities=["Lead Q4 Implementation"],
    ))

    # --- Invoice Space ---
    invoice = store.create(
        entity_id="ent_invoice_001",
        entity_type="invoice",
        name="INV-2025-0042",
        aliases=["Invoice #42", "INV-0042"],
    )
    store.add_relationship(invoice.space_id, SpaceRelationshipRef(
        rel_id="rel_inv_001",
        target_entity_id="ent_customer_001",
        target_entity_name="Acme Corporation",
        target_entity_type="customer",
        rel_type="bill_to",
        direction="outgoing",
    ))
    store.add_timeline_event(invoice.space_id, SpaceTimelineEvent(
        event_id="tev_inv_001",
        event_type="sent",
        timestamp=datetime.now(timezone.utc).isoformat(),
        title="Invoice sent",
        description="Invoice INV-2025-0042 sent to customer",
        category="communication",
        importance=0.7,
    ))
    store.add_metric(invoice.space_id, SpaceMetric(
        metric_id="met_inv_001",
        name="Amount",
        value=45000,
        unit="USD",
        trend="stable",
        confidence=1.0,
    ))
    store.add_metric(invoice.space_id, SpaceMetric(
        metric_id="met_inv_002",
        name="Status",
        value="pending",
        trend="stable",
        confidence=1.0,
    ))

    # --- Company Space (root) ---
    company = store.create(
        entity_id="ent_company_001",
        entity_type="company",
        name="SHUNYA OS",
        aliases=["SHUNYA", "Shunya OS"],
    )
    store.add_child(company.space_id, customer.space_id)
    store.add_child(company.space_id, supplier.space_id)
    store.add_child(company.space_id, employee.space_id)