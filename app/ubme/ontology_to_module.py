"""Ontology-to-Module Converter — transforms a BusinessOntology into a ModuleDef.

This is the bridge between discovery and deployment.
The Intelligence Runtime will consume the ontology directly for AI awareness.
"""

from __future__ import annotations

from typing import Any

from app.ubme.models import (
    ActionDef, DashboardCard, FieldDef, FieldType, ModuleDef,
    NavigationEntry, ObjectTypeDef, ViewDef, ViewType,
    WorkflowDef, WorkflowStateDef, WorkflowStateType, WorkflowTransitionDef,
)
from app.ubme.ontology import (
    BusinessOntology, ConfidenceLevel, EntityDef, EntityRelationship,
    InferredMetric, InferredAutomation, OntologyEntityType,
)


def ontology_to_module(ontology: BusinessOntology) -> ModuleDef:
    """Convert a BusinessOntology into a complete ModuleDef ready for installation."""
    object_types = []
    views = []
    workflows = []
    navigation = []
    dashboard_cards = []

    for entity in ontology.entities:
        # Skip virtual/reference entities for now
        if entity.entity_type in (OntologyEntityType.VIRTUAL, OntologyEntityType.REFERENCE):
            continue

        ot = _entity_to_object_type(entity)
        object_types.append(ot)

        # Generate navigation entry
        navigation.append(NavigationEntry(
            label=ot.plural_name,
            object_type=ot.key,
            icon=ot.icon,
        ))

        # Generate views
        entity_views = _generate_views_for_entity(ot, entity)
        views.extend(entity_views)

        # Generate workflow if lifecycle exists
        if entity.lifecycle:
            wf = _lifecycle_to_workflow(entity)
            if wf:
                workflows.append(wf)

        # Generate dashboard cards for this entity
        entity_cards = _generate_cards_for_entity(ontology, entity)
        dashboard_cards.extend(entity_cards)

    # Add extra metrics as dashboard cards
    for metric in ontology.metrics:
        if not any(c.object_type == metric.entity and c.key == f"metric_{metric.key}" for c in dashboard_cards):
            dashboard_cards.append(DashboardCard(
                key=f"metric_{metric.key}",
                label=metric.label,
                card_type=metric.aggregation if metric.aggregation in ("count", "sum") else "count",
                object_type=metric.entity,
                field=metric.field or "",
                filter_criteria=metric.filter_criteria or "",
                icon=metric.icon,
            ))

    # Deduplicate cards by key
    seen_cards = set()
    unique_cards = []
    for c in dashboard_cards:
        if c.key not in seen_cards:
            seen_cards.add(c.key)
            unique_cards.append(c)

    module = ModuleDef(
        key=ontology.key,
        name=ontology.name,
        description=ontology.description[:200] if ontology.description else "",
        icon=_get_industry_icon(ontology.industry),
        color=_get_industry_color(ontology.industry),
        navigation=navigation[:8],
        object_types=object_types,
        views=views,
        workflows=workflows,
        dashboard_cards=unique_cards[:12],
        dashboard_config=ontology.to_dict() if ontology.overall_confidence() >= 0.7 else None,
    )
    return module


def _entity_to_object_type(entity: EntityDef) -> ObjectTypeDef:
    """Convert an ontology EntityDef to an ObjectTypeDef."""
    fields = []
    for ef in entity.fields:
        ft = ef.field_type
        try:
            field_type = FieldType(ft)
        except ValueError:
            field_type = FieldType.TEXT
        fields.append(FieldDef(
            key=ef.key,
            label=ef.label,
            field_type=field_type,
            required=ef.required,
            searchable=ef.searchable,
            display_in_list=ef.display_in_list,
            options=ef.options or None,
            order=ef.order,
        ))

    # Build AI semantics
    ai_semantics = {
        "description": entity.description,
        "common_intents": entity.common_intents or [
            f"view {entity.name.lower()}",
            f"create {entity.name.lower()}",
            f"update {entity.name.lower()}",
        ],
        "business_terminology": {},
    }
    for syn in entity.synonyms:
        if syn != entity.name.lower():
            ai_semantics["business_terminology"][syn] = entity.name.lower()

    actions = _generate_actions_for_entity(entity.key, entity.name)

    return ObjectTypeDef(
        key=entity.key,
        name=entity.name,
        plural_name=entity.plural_name,
        description=entity.description,
        icon=entity.icon,
        color=entity.color,
        fields=fields,
        lifecycle=[s.key for s in entity.lifecycle] if entity.lifecycle else None,
        ai_semantics=ai_semantics,
        actions=actions,
    )


def _generate_views_for_entity(ot: ObjectTypeDef, entity: EntityDef) -> list[ViewDef]:
    """Generate standard views for an object type."""
    views = []
    field_keys = [f.key for f in ot.fields]
    list_fields = [f for f in ot.fields if f.display_in_list][:8]
    list_keys = [f.key for f in list_fields] or field_keys[:5]

    views.append(ViewDef(
        key=f"{ot.key}_list",
        label=ot.plural_name,
        view_type=ViewType.LIST,
        object_type=ot.key,
        fields=list_keys,
        is_default=True,
    ))
    views.append(ViewDef(
        key=f"{ot.key}_table",
        label=ot.plural_name,
        view_type=ViewType.TABLE,
        object_type=ot.key,
        fields=field_keys[:10],
    ))
    views.append(ViewDef(
        key=f"{ot.key}_detail",
        label=f"{ot.name} Detail",
        view_type=ViewType.DETAIL,
        object_type=ot.key,
        fields=field_keys,
    ))

    # Calendar if date field exists
    date_fields = [f for f in ot.fields if f.field_type in (FieldType.DATE, FieldType.DATETIME)]
    if date_fields:
        views.append(ViewDef(
            key=f"{ot.key}_calendar",
            label="Calendar",
            view_type=ViewType.CALENDAR,
            object_type=ot.key,
            fields=list_keys,
        ))

    return views


def _lifecycle_to_workflow(entity: EntityDef) -> WorkflowDef | None:
    """Convert an entity lifecycle into a WorkflowDef."""
    if not entity.lifecycle or len(entity.lifecycle) < 2:
        return None

    states = []
    transitions = []
    for i, stage in enumerate(entity.lifecycle):
        stage_type = WorkflowStateType.INITIAL if i == 0 else (
            WorkflowStateType.FINAL if i == len(entity.lifecycle) - 1 else WorkflowStateType.INTERMEDIATE
        )
        states.append(WorkflowStateDef(
            key=stage.key,
            label=stage.label,
            state_type=stage_type,
        ))
        if i > 0:
            transitions.append(WorkflowTransitionDef(
                from_state=entity.lifecycle[i-1].key,
                to_state=stage.key,
                label=f"Move to {stage.label}",
            ))

    return WorkflowDef(
        key=f"{entity.key}_lifecycle",
        name=f"{entity.name} Lifecycle",
        object_type=entity.key,
        states=states,
        transitions=transitions,
        default_state=states[0].key if states else "",
    )


def _generate_cards_for_entity(ontology: BusinessOntology, entity: EntityDef) -> list[DashboardCard]:
    """Generate dashboard cards for a specific entity."""
    cards = []

    # Total count
    cards.append(DashboardCard(
        key=f"total_{entity.key}s",
        label=f"Total {entity.plural_name}",
        card_type="count",
        object_type=entity.key,
        icon=entity.icon,
    ))

    # If entity has lifecycle, show active count
    if entity.lifecycle and len(entity.lifecycle) >= 2:
        initial_state = entity.lifecycle[0].key
        cards.append(DashboardCard(
            key=f"active_{entity.key}s",
            label=f"Active {entity.plural_name}",
            card_type="count",
            object_type=entity.key,
            filter_criteria=f"status == '{initial_state}'",
            icon=entity.icon,
        ))

    # If entity has an amount/price field, show sum
    for field in entity.fields:
        if field.field_type in ("currency", "number", "integer"):
            cards.append(DashboardCard(
                key=f"total_{entity.key}_{field.key}",
                label=f"Total {field.label}",
                card_type="sum",
                object_type=entity.key,
                field=field.key,
                icon="💰",
            ))
            break

    return cards


def _generate_actions_for_entity(key: str, name: str) -> list[ActionDef]:
    """Generate common actions for a given entity type."""
    actions = []
    common = {
        "customer": [("view_profile", "View Profile", "👤"), ("send_email", "Send Email", "📧"), ("create_record", f"Create {name}", "➕")],
        "patient": [("view_profile", "View Profile", "👤"), ("schedule_appointment", "Schedule Appointment", "📅"), ("create_record", f"Create {name}", "➕")],
        "appointment": [("confirm", "Confirm", "✅", True), ("reschedule", "Reschedule", "🔄"), ("cancel", "Cancel", "❌", True)],
        "booking": [("confirm", "Confirm", "✅", True), ("cancel", "Cancel", "❌", True), ("reprice", "Reprice", "💰")],
        "order": [("confirm", "Confirm", "✅"), ("ship", "Mark Shipped", "🚚", True), ("cancel", "Cancel", "❌", True)],
        "invoice": [("send", "Send", "📧", True), ("mark_paid", "Mark Paid", "✅", True), ("export_pdf", "Export PDF", "📄")],
        "payment": [("record", "Record Payment", "💳"), ("send_receipt", "Send Receipt", "📧"), ("refund", "Refund", "↩️", True)],
        "task": [("complete", "Complete", "✅", True), ("reassign", "Reassign", "🔄"), ("postpone", "Postpone", "⏰")],
        "project": [("start", "Start Project", "🚀"), ("complete", "Complete", "✅", True), ("archive", "Archive", "📦")],
        "prescription": [("print", "Print", "🖨️"), ("fill", "Mark Filled", "✅"), ("void", "Void", "❌", True)],
        "treatment": [("start", "Start Treatment", "🏥"), ("complete", "Complete", "✅", True), ("cancel", "Cancel", "❌", True)],
        "case": [("open", "Open Case", "📂"), ("close", "Close Case", "🔒", True), ("reopen", "Reopen", "🔄")],
        "property": [("list", "List Property", "📢"), ("mark_sold", "Mark Sold", "💰", True), ("withdraw", "Withdraw", "🔒")],
    }
    entity_actions = common.get(key, [])
    if not entity_actions:
        entity_actions = [("edit", f"Edit {name}", "✏️"), ("delete", f"Delete", "🗑️", True)]

    for action in entity_actions:
        a = ActionDef(key=action[0], label=action[1], icon=action[2])
        if len(action) > 3 and action[3]:
            a.requires_confirmation = True
        actions.append(a)
    return actions


def _get_industry_icon(industry: str) -> str:
    icons = {
        "Healthcare": "🏥", "Technology": "💻", "Manufacturing": "🏭",
        "Retail": "🛒", "Services": "💼", "Construction": "🏗️",
        "Education": "🎓", "Hospitality": "🏨", "Entertainment": "🎬",
        "Energy": "⚡",
    }
    return icons.get(industry, "🏢")


def _get_industry_color(industry: str) -> str:
    colors = {
        "Healthcare": "#ec4899", "Technology": "#6366f1", "Manufacturing": "#f59e0b",
        "Retail": "#10b981", "Services": "#8b5cf6", "Construction": "#f97316",
        "Education": "#14b8a6", "Hospitality": "#ef4444", "Entertainment": "#f43f5e",
        "Energy": "#22c55e",
    }
    return colors.get(industry, "#6366f1")