"""Ontology Generator — builds a BusinessOntology from interview responses.

Transforms raw interview answers into structured entities, relationships,
lifecycles, metrics, automations, and terminology.
"""

from __future__ import annotations

import re
from typing import Any

from app.ubme.ontology import (
    BusinessOntology, ConfidenceLevel, EntityDef, EntityField,
    EntityRelationship, InferredAutomation, InferredMetric,
    LifecycleStage, LifecycleStageType, OntologyEntityType,
    RelationshipCardinality,
)


def generate_ontology(answers: dict[str, Any], session_id: str = "") -> BusinessOntology:
    """Generate a complete BusinessOntology from interview answers."""
    ontology = BusinessOntology(
        key=session_id or "discovered",
        name=answers.get("business_name", "Discovered Business"),
        description=answers.get("business_description", ""),
        industry=answers.get("industry", ""),
    )

    # 1. Parse core entities from the "entities" answer
    entities = _parse_entities(answers)
    ontology.entities = entities

    # 2. Infer relationships between discovered entities
    ontology.relationships = _infer_relationships(answers, entities)

    # 3. Infer lifecycles for entities
    ontology = _infer_lifecycles(answers, ontology)

    # 4. Inferred fields for each entity
    ontology = _infer_fields(answers, ontology)

    # 5. Infer metrics/KPIs
    ontology.metrics = _infer_metrics(answers, ontology)

    # 6. Infer automations
    ontology.automations = _infer_automations(answers, ontology)

    # 7. Build terminology map
    ontology.terminology = _build_terminology(answers, ontology)

    # 8. Business rules
    ontology.business_rules = _extract_rules(answers)

    return ontology


def _parse_entities(answers: dict[str, Any]) -> list[EntityDef]:
    """Parse entity names from interview answers."""
    raw = answers.get("entities", "")
    entity_names = _parse_list(raw)

    # Add known entities from other answers
    if answers.get("has_customers"):
        if "customer" not in [n.lower() for n in entity_names]:
            entity_names.insert(0, "Customer")

    entities = []
    seen_keys = set()
    for name in entity_names:
        key = _to_key(name)
        singular_key = key.rstrip('s') if key.endswith('s') and key not in ('status', 'address', 'class') else key
        if singular_key in seen_keys:
            continue
        seen_keys.add(singular_key)
        # Use singular form for name if it was plural
        display_name = name.rstrip('s') if name.lower().endswith('s') and not name.lower().endswith('ss') else name
        entities.append(EntityDef(
            key=singular_key,
            name=display_name,
            description=f"{display_name} in the business",
            entity_type=OntologyEntityType.PRIMARY,
            synonyms=[name.lower(), singular_key],
            icon=_guess_icon(singular_key, display_name),
            color=_guess_color(singular_key),
        ))

    # Add Product/Services entity if products were described but not in entity list
    if answers.get("products") and "product" not in seen_keys:
        entities.append(EntityDef(
            key="product", name="Product", description="Products and services offered",
            entity_type=OntologyEntityType.PRIMARY,
            synonyms=["product", "service", "item"],
            icon="📦", color="#6366f1",
        ))

    return entities


def _infer_relationships(answers: dict[str, Any], entities: list[EntityDef]) -> list[EntityRelationship]:
    """Infer relationships between discovered entities."""

    relationship_patterns = [
        ("booking", "customer", RelationshipCardinality.MANY_TO_ONE, "belongs to", "has bookings"),
        ("invoice", "customer", RelationshipCardinality.MANY_TO_ONE, "belongs to", "has invoices"),
        ("invoice", "booking", RelationshipCardinality.ONE_TO_ONE, "for", "has invoice"),
        ("order", "customer", RelationshipCardinality.MANY_TO_ONE, "placed by", "placed"),
        ("payment", "invoice", RelationshipCardinality.ONE_TO_ONE, "pays", "paid by"),
        ("payment", "customer", RelationshipCardinality.MANY_TO_ONE, "made by", "made payments"),
        ("appointment", "patient", RelationshipCardinality.MANY_TO_ONE, "for", "has appointments"),
        ("appointment", "doctor", RelationshipCardinality.MANY_TO_ONE, "with", "has appointments"),
        ("prescription", "patient", RelationshipCardinality.MANY_TO_ONE, "for", "has prescriptions"),
        ("prescription", "doctor", RelationshipCardinality.MANY_TO_ONE, "prescribed by", "prescribed"),
        ("prescription", "appointment", RelationshipCardinality.ONE_TO_ONE, "from", "has prescription"),
        ("treatment", "patient", RelationshipCardinality.MANY_TO_ONE, "for", "has treatments"),
        ("treatment", "appointment", RelationshipCardinality.ONE_TO_ONE, "during", "had treatments"),
        ("project", "customer", RelationshipCardinality.MANY_TO_ONE, "for", "has projects"),
        ("invoice", "project", RelationshipCardinality.ONE_TO_ONE, "for", "has invoice"),
        ("task", "project", RelationshipCardinality.MANY_TO_ONE, "part of", "has tasks"),
        ("task", "employee", RelationshipCardinality.MANY_TO_ONE, "assigned to", "has tasks"),
        ("quotation", "customer", RelationshipCardinality.MANY_TO_ONE, "for", "has quotations"),
        ("purchase_order", "vendor", RelationshipCardinality.MANY_TO_ONE, "to", "has purchase orders"),
        ("purchase_order", "customer", RelationshipCardinality.MANY_TO_ONE, "for", "has purchase orders"),
        ("production_order", "product", RelationshipCardinality.MANY_TO_ONE, "produces", "produced by"),
        ("inventory", "product", RelationshipCardinality.ONE_TO_ONE, "for", "has inventory"),
        ("case", "client", RelationshipCardinality.MANY_TO_ONE, "for", "has cases"),
        ("hearing", "case", RelationshipCardinality.MANY_TO_ONE, "in", "has hearings"),
        ("document", "case", RelationshipCardinality.MANY_TO_ONE, "related to", "has documents"),
        ("billing", "client", RelationshipCardinality.MANY_TO_ONE, "to", "has billings"),
        ("billing", "case", RelationshipCardinality.MANY_TO_ONE, "for", "has billings"),
        ("property", "client", RelationshipCardinality.MANY_TO_ONE, "listed by", "lists properties"),
        ("viewing", "property", RelationshipCardinality.MANY_TO_ONE, "of", "has viewings"),
        ("viewing", "client", RelationshipCardinality.MANY_TO_ONE, "with", "requested viewings"),
        ("offer", "property", RelationshipCardinality.MANY_TO_ONE, "on", "has offers"),
        ("offer", "client", RelationshipCardinality.MANY_TO_ONE, "from", "made offers"),
    ]

    entity_keys = [e.key for e in entities]
    relationships = []

    # Check raw relationship answer for custom connections
    raw_rels = answers.get("entity_relationships", "")
    custom_relations = _parse_relationship_text(raw_rels) if raw_rels else []

    for src, tgt, card, label, inv_label in relationship_patterns:
        if src in entity_keys and tgt in entity_keys:
            relationships.append(EntityRelationship(
                source_entity=src, target_entity=tgt,
                cardinality=card, label=label, inverse_label=inv_label,
                confidence=ConfidenceLevel.HIGH,
            ))

    # Add custom relationships from user answers
    for src, tgt, label in custom_relations:
        src_key = _to_key(src)
        tgt_key = _to_key(tgt)
        if src_key in entity_keys and tgt_key in entity_keys:
            # Check if already exists
            exists = any(
                r.source_entity == src_key and r.target_entity == tgt_key
                for r in relationships
            )
            if not exists:
                relationships.append(EntityRelationship(
                    source_entity=src_key, target_entity=tgt_key,
                    label=label, inverse_label=f"related {tgt}",
                    confidence=ConfidenceLevel.MEDIUM,
                ))

    return relationships


def _infer_lifecycles(answers: dict[str, Any], ontology: BusinessOntology) -> BusinessOntology:
    """Infer lifecycle stages for entities based on answers."""
    for entity in ontology.entities:
        # Check if user described statuses for this entity
        status_key = f"{entity.key}_statuses"
        status_answer = answers.get(status_key, "")
        if status_answer:
            stages = _parse_list(status_answer)
            entity.lifecycle = []
            for i, stage in enumerate(stages):
                stage_type = LifecycleStageType.INITIAL if i == 0 else (
                    LifecycleStageType.FINAL if i == len(stages) - 1 else LifecycleStageType.INTERMEDIATE
                )
                entity.lifecycle.append(LifecycleStage(
                    key=_to_key(stage), label=stage, stage_type=stage_type,
                    confidence=ConfidenceLevel.HIGH,
                ))
        else:
            # Use general status answer or standard lifecycle
            status_text = answers.get("entity_statuses", "")
            if status_text:
                entity.lifecycle = _standard_lifecycle(entity.key, entity.name)
            else:
                entity.lifecycle = _inferred_lifecycle(entity.key)

    return ontology


def _infer_fields(answers: dict[str, Any], ontology: BusinessOntology) -> BusinessOntology:
    """Infer fields for each entity from interview answers."""
    for entity in ontology.entities:
        # Check for custom fields
        fields_key = f"{entity.key}_fields"
        custom_fields = answers.get(fields_key, "")
        if custom_fields:
            field_names = _parse_list(custom_fields)
            entity.fields = [_field_from_name(f) for f in field_names]
        else:
            # Use standard fields for known entity types
            entity.fields = _standard_fields(entity.key, entity.name)

        # Ensure standard fields exist
        _ensure_standard_fields(entity)

    return ontology


def _infer_metrics(answers: dict[str, Any], ontology: BusinessOntology) -> list[InferredMetric]:
    """Infer meaningful KPIs/dashboard metrics."""
    metrics = []
    raw = answers.get("metrics", "")

    for entity in ontology.entities:
        # Count metrics using correct plural
        plural = entity.plural_name
        metrics.append(InferredMetric(
            key=f"total_{entity.key}s",
            label=f"Total {plural}",
            entity=entity.key,
            aggregation="count",
            confidence=ConfidenceLevel.HIGH,
        ))

    # Parse user-specified metrics
    if raw:
        metric_names = _parse_list(raw)
        for name in metric_names[:6]:
            low = name.lower()
            matched = False
            for entity in ontology.entities:
                if entity.name.lower() in low:
                    agg = "sum" if any(w in low for w in ["revenue", "total", "amount", "income"]) else "count"
                    metrics.append(InferredMetric(
                        key=_to_key(name),
                        label=name,
                        entity=entity.key,
                        aggregation=agg,
                        field="amount" if agg == "sum" else "",
                        confidence=ConfidenceLevel.MEDIUM,
                    ))
                    matched = True
                    break
            if not matched:
                metrics.append(InferredMetric(
                    key=_to_key(name), label=name,
                    aggregation="count",
                    confidence=ConfidenceLevel.LOW,
                ))

    return metrics


def _infer_automations(answers: dict[str, Any], ontology: BusinessOntology) -> list[InferredAutomation]:
    """Infer automation opportunities from pain points and repetitive tasks."""
    automations = []

    # From pain points / delays
    delays = answers.get("workflow_delays", "")
    if delays and any(w in delays.lower() for w in ["remind", "follow", "chase", "email"]):
        automations.append(InferredAutomation(
            key="auto_reminders",
            label="Automatic Payment Reminders",
            description="Send automatic reminders for overdue payments",
            trigger="invoice.status == 'overdue'",
            action="send_email",
            confidence=ConfidenceLevel.HIGH,
        ))

    # From repetitive tasks
    repetitive = answers.get("repetitive_tasks", "")
    if repetitive:
        rep_lower = repetitive.lower()
        if any(w in rep_lower for w in ["invoice", "bill"]):
            automations.append(InferredAutomation(
                key="auto_invoice",
                label="Automatic Invoice Generation",
                description="Generate invoice when booking/order is completed",
                trigger="booking.status == 'completed'",
                action="generate_invoice",
                confidence=ConfidenceLevel.MEDIUM,
            ))
        if any(w in rep_lower for w in ["email", "send", "notify"]):
            automations.append(InferredAutomation(
                key="auto_notify",
                label="Automatic Notifications",
                description="Send notifications for key events",
                trigger="object.status changed",
                action="send_notification",
                confidence=ConfidenceLevel.MEDIUM,
            ))
        if any(w in rep_lower for w in ["approve", "approval"]):
            automations.append(InferredAutomation(
                key="auto_approval_reminder",
                label="Approval Reminder",
                description="Remind approvers of pending approvals",
                trigger="object.status == 'pending_approval'",
                action="send_reminder",
                confidence=ConfidenceLevel.MEDIUM,
            ))

    return automations


def _build_terminology(answers: dict[str, Any], ontology: BusinessOntology) -> dict[str, str]:
    """Build terminology mapping from synonyms to canonical names."""
    terminology = {}
    for entity in ontology.entities:
        name_lower = entity.name.lower()
        if entity.synonyms:
            for syn in entity.synonyms:
                if syn != name_lower:
                    terminology[syn] = name_lower

    # Common business synonyms
    common = {
        "client": "customer", "buyer": "customer",
        "vendor": "supplier", "provider": "supplier", "partner": "supplier",
        "physician": "doctor", "practitioner": "doctor",
        "bill": "invoice", "charge": "invoice",
        "rx": "prescription", "medication": "prescription",
        "task": "task", "todo": "task", "action item": "task",
        "project": "project", "engagement": "project",
        "employee": "staff", "team member": "staff",
        "product": "product", "item": "product", "service": "product",
    }
    for syn, canonical in common.items():
        if syn not in terminology:
            # Only add if the canonical entity exists in the ontology
            for entity in ontology.entities:
                if entity.key == canonical or entity.name.lower() == canonical:
                    terminology[syn] = canonical
                    break
    return terminology


def _extract_rules(answers: dict[str, Any]) -> list[str]:
    """Extract business rules from interview answers."""
    rules = []
    if answers.get("document_approvals") == "Yes":
        rules.append("Documents require approval before finalization")
    if answers.get("confidential_info") == "Yes":
        rules.append("Some information has restricted access")
    return rules


# ── Helpers ──────────────────────────────────────────────────────────────


def _parse_list(text: str) -> list[str]:
    """Parse comma, semicolon, newline, or bullet-separated text into a list."""
    parts = re.split(r'[,;、\n•\-]|\s+and\s+', text)
    result = []
    for p in parts:
        p = p.strip().strip('.').strip()
        if p and len(p) > 1:
            result.append(p)
    return result


def _parse_relationship_text(text: str) -> list[tuple[str, str, str]]:
    """Parse free-text relationship descriptions into (source, target, label) tuples."""
    relations = []
    # Split by commas and analyze each statement
    statements = [s.strip() for s in re.split(r'[,;.]+', text) if s.strip()]
    for stmt in statements:
        stmt_lower = stmt.lower().strip()
        # Remove leading article
        for article in ["a ", "an ", "the "]:
            if stmt_lower.startswith(article):
                stmt_lower = stmt_lower[len(article):]
                break
        # Try patterns
        patterns = [
            (r"^(\w+)\s+(?:belongs?\s+to|is\s+for|is\s+of|is\s+by|for)\s+(?:a\s+|an\s+|the\s+)?(\w+(?:\s+\w+)?)", "belongs to"),
            (r"^(\w+)\s+(?:has|creates|produces|issues)\s+(?:a\s+|an\s+|the\s+)?(\w+(?:\s+\w+)?)", "has"),
            (r"^(\w+)\s+(?:contains?|includes?)\s+(?:a\s+|an\s+|the\s+)?(\w+(?:\s+\w+)?)", "contains"),
        ]
        for pattern, default_label in patterns:
            m = re.match(pattern, stmt_lower)
            if m:
                src = m.group(1).strip().capitalize()
                tgt = m.group(2).strip().capitalize()
                if src and tgt and src != tgt:
                    relations.append((src, tgt, default_label))
                break
    return relations


def _to_key(name: str) -> str:
    key = name.lower().strip()
    key = re.sub(r'[^a-z0-9\s]', '', key)
    key = key.replace(' ', '_')
    return key[:40]


def _guess_icon(key: str, name: str) -> str:
    icons = {
        "customer": "👤", "client": "👤", "patient": "👤",
        "doctor": "👨‍⚕️", "dentist": "👨‍⚕️", "veterinarian": "👨‍⚕️", "vet": "👨‍⚕️",
        "appointment": "📅", "booking": "📋", "reservation": "📅",
        "invoice": "🧾", "bill": "🧾", "payment": "💳",
        "order": "📋", "purchase_order": "📋", "production_order": "🏭",
        "product": "📦", "inventory": "📦", "item": "📦",
        "supplier": "🤝", "vendor": "🤝",
        "project": "📊", "task": "✅", "todo": "✅",
        "prescription": "💊", "treatment": "💊", "medication": "💊",
        "quotation": "📄", "quote": "📄", "estimate": "📄",
        "case": "⚖️", "hearing": "📅", "document": "📄",
        "property": "🏠", "viewing": "👁️", "offer": "🤝",
        "billing": "🧾", "commission": "💰",
        "machine": "⚙️", "equipment": "⚙️",
        "dispatch": "🚚", "shipment": "🚚",
        "qc": "🔍", "quality": "🔍",
        "xray": "🩻", "x_ray": "🩻",
        "insurance": "🏛️", "claim": "📋",
        "scene": "🎬", "film": "🎥", "movie": "🎥",
        "contract": "📝", "agreement": "📝",
        "employee": "👤", "staff": "👤",
        "asset": "📱", "equipment": "⚙️",
        "report": "📊", "analysis": "📊",
    }
    return icons.get(key, icons.get(key.rstrip('s'), "📦"))


def _guess_color(key: str) -> str:
    colors = {
        "customer": "#0ea5e9", "client": "#0ea5e9", "patient": "#ec4899",
        "doctor": "#8b5cf6", "appointment": "#f59e0b", "booking": "#f59e0b",
        "invoice": "#ef4444", "payment": "#22c55e", "order": "#f59e0b",
        "product": "#6366f1", "supplier": "#8b5cf6", "vendor": "#8b5cf6",
        "project": "#14b8a6", "task": "#10b981",
        "prescription": "#10b981", "treatment": "#10b981",
        "quotation": "#f97316", "case": "#8b5cf6",
        "property": "#14b8a6", "billing": "#ef4444",
    }
    return colors.get(key, "#6366f1")


def _field_from_name(name: str) -> EntityField:
    """Generate a field definition from a descriptive name."""
    low = name.lower().strip()
    ft = "text"
    required = low in ("name", "title", "email", "id", "code")
    display_in_list = low not in ("notes", "description", "comment", "attachment", "address")
    searchable = low not in ("password", "secret", "notes")

    if any(w in low for w in ["email", "e-mail"]):
        ft = "email"
    elif any(w in low for w in ["phone", "mobile", "telephone", "cell", "tel"]):
        ft = "phone"
    elif any(w in low for w in ["date", "time"]):
        ft = "date"
    elif any(w in low for w in ["amount", "price", "cost", "fee", "rate"]):
        ft = "currency"
    elif any(w in low for w in ["quantity", "count", "qty", "number", "num", "age"]):
        ft = "integer"
    elif any(w in low for w in ["percentage", "percent", "rate"]):
        ft = "percentage"
    elif any(w in low for w in ["url", "website", "link"]):
        ft = "url"
    elif any(w in low for w in ["address", "location", "city", "state"]):
        ft = "address"
    elif low == "status":
        ft = "select"
        options = ["active", "inactive"]
        return EntityField(key=_to_key(name), label=name, field_type=ft, options=options, display_in_list=True)
    elif any(w in low for w in ["notes", "description", "comment", "detail"]):
        ft = "long_text"

    return EntityField(key=_to_key(name), label=name, field_type=ft, required=required, display_in_list=display_in_list, searchable=searchable)


def _standard_fields(key: str, name: str) -> list[EntityField]:
    """Return standard fields for known entity types."""
    base = [
        EntityField(key="name", label="Name", field_type="text", required=True, searchable=True, display_in_list=True, order=1),
    ]
    if key in ("customer", "client", "patient", "supplier", "vendor", "employee", "staff", "doctor", "dentist", "veterinarian", "vet"):
        base += [
            EntityField(key="email", label="Email", field_type="email", searchable=True, display_in_list=True, order=2),
            EntityField(key="phone", label="Phone", field_type="phone", order=3),
            EntityField(key="status", label="Status", field_type="select", options=["active", "inactive"], default="active", display_in_list=True, order=99),
        ]
    elif key in ("invoice", "bill", "billing", "payment"):
        base += [
            EntityField(key="amount", label="Amount", field_type="currency", display_in_list=True, order=2),
            EntityField(key="status", label="Status", field_type="select", options=["draft", "sent", "paid", "cancelled"], display_in_list=True, order=3),
            EntityField(key="due_date", label="Due Date", field_type="date", order=4),
        ]
    elif key in ("booking", "order", "appointment", "reservation"):
        base += [
            EntityField(key="status", label="Status", field_type="select", options=["pending", "confirmed", "completed", "cancelled"], display_in_list=True, order=2),
            EntityField(key="date", label="Date", field_type="date", order=3),
        ]
    elif key in ("product", "item"):
        base += [
            EntityField(key="unit_price", label="Unit Price", field_type="currency", display_in_list=True, order=2),
            EntityField(key="quantity", label="Quantity", field_type="integer", display_in_list=True, order=3),
            EntityField(key="status", label="Status", field_type="select", options=["active", "inactive"], display_in_list=True, order=4),
        ]
    return base


def _ensure_standard_fields(entity: EntityDef) -> None:
    """Ensure common fields exist on the entity."""
    existing_keys = {f.key for f in entity.fields}
    if "name" not in existing_keys:
        entity.fields.insert(0, EntityField(key="name", label="Name", field_type="text", required=True, searchable=True, display_in_list=True, order=1))
    if "status" not in existing_keys and entity.lifecycle:
        status_options = [s.key for s in entity.lifecycle]
        entity.fields.append(EntityField(key="status", label="Status", field_type="select", options=status_options, display_in_list=True, order=99))


def _standard_lifecycle(key: str, name: str) -> list[LifecycleStage]:
    """Return a standard lifecycle for known entities."""
    lifecycles = {
        "customer": ["lead", "active", "inactive", "archived"],
        "client": ["lead", "active", "inactive", "archived"],
        "patient": ["new", "active", "inactive", "archived"],
        "booking": ["inquiry", "confirmed", "in_progress", "completed", "cancelled"],
        "order": ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"],
        "project": ["planning", "in_progress", "on_hold", "completed", "cancelled"],
        "task": ["todo", "in_progress", "done", "cancelled"],
        "invoice": ["draft", "sent", "paid", "overdue", "cancelled"],
        "bill": ["draft", "sent", "paid", "overdue", "cancelled"],
        "appointment": ["scheduled", "checked_in", "in_progress", "completed", "cancelled"],
        "prescription": ["draft", "active", "filled", "expired"],
        "treatment": ["planned", "in_progress", "completed", "cancelled"],
        "case": ["filed", "discovery", "trial", "judgment", "closed"],
        "hearing": ["scheduled", "in_progress", "completed", "adjourned"],
        "production_order": ["planned", "in_progress", "completed", "on_hold"],
        "purchase_order": ["draft", "approved", "ordered", "received", "cancelled"],
        "quotation": ["draft", "sent", "accepted", "rejected", "expired"],
        "property": ["listed", "under_offer", "sold", "withdrawn"],
        "viewing": ["scheduled", "completed", "cancelled"],
        "film": ["development", "pre_production", "production", "post_production", "distribution", "released"],
        "scene": ["storyboard", "scheduled", "filmed", "reviewed", "approved"],
        "contract": ["draft", "negotiation", "signed", "active", "expired"],
    }
    stages = lifecycles.get(key)
    if not stages:
        return []
    result = []
    for i, stage in enumerate(stages):
        st = LifecycleStageType.INITIAL if i == 0 else (LifecycleStageType.FINAL if i == len(stages) - 1 else LifecycleStageType.INTERMEDIATE)
        result.append(LifecycleStage(key=_to_key(stage), label=stage.replace("_", " ").title(), stage_type=st, confidence=ConfidenceLevel.HIGH))
    return result


def _inferred_lifecycle(key: str) -> list[LifecycleStage]:
    """Return a minimal lifecycle for any entity."""
    return [
        LifecycleStage(key="active", label="Active", stage_type=LifecycleStageType.INITIAL, confidence=ConfidenceLevel.MEDIUM),
        LifecycleStage(key="inactive", label="Inactive", stage_type=LifecycleStageType.FINAL, confidence=ConfidenceLevel.MEDIUM),
    ]