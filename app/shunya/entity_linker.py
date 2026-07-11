"""Cross-Entity Auto-Linker — automatically connects related entities.

When a lead becomes a booking, the booking data should be pre-filled
from the lead. When a booking is confirmed, an itinerary should be
auto-generated. No manual re-entry across the workflow.
"""
from typing import Optional, List
from datetime import datetime
from app import db
from app.models import Entity, EntityDefinition, ActivityLog, Notification
from app.shunya.foundation import Result
from app.shunya.observer import Observer


class EntityLinker:
    """Automatically links and transforms entities across workflows."""

    LINK_RULES = {
        "lead": {
            "child_types": ["booking", "itinerary"],
            "field_map": {
                "customer_name": "customer_name",
                "phone": "phone",
                "email": "email",
                "destination": "destination",
                "pax": "pax",
                "budget": "total_amount",
            },
        },
        "booking": {
            "child_types": ["itinerary", "invoice"],
            "field_map": {
                "customer_name": "customer_name",
                "destination": "destination",
                "total_amount": "total_amount",
            },
        },
    }

    @staticmethod
    def on_status_change(entity: Entity, new_status: str, user_id: int) -> List[dict]:
        """When an entity status changes, check if we should auto-create children."""
        results = []
        definition = entity.definition
        if not definition:
            return results

        entity_type = definition.type
        rules = EntityLinker.LINK_RULES.get(entity_type)
        if not rules:
            return results

        # Check if status triggers child creation
        if new_status in ("booked", "confirmed", "converted"):
            for child_type in rules["child_types"]:
                result = EntityLinker._auto_create_child(
                    entity, child_type, rules["field_map"], user_id
                )
                if result:
                    results.append(result)

        return results

    @staticmethod
    def _auto_create_child(parent: Entity, child_type: str,
                            field_map: dict, user_id: int) -> Optional[dict]:
        """Auto-create a child entity from a parent, mapping fields."""
        child_def = EntityDefinition.query.filter_by(
            tenant_id=parent.tenant_id, type=child_type, is_active=True
        ).first()
        if not child_def:
            return None

        # Check if child already exists for this parent
        existing = Entity.query.filter_by(
            tenant_id=parent.tenant_id,
            definition_id=child_def.id,
        ).filter(
            Entity.data["linked_from"].as_string() == str(parent.id)
        ).first()
        if existing:
            return None  # Already linked

        # Map fields
        child_data = {}
        for parent_field, child_field in field_map.items():
            if parent_field in parent.data:
                child_data[child_field] = parent.data[parent_field]
        child_data["linked_from"] = str(parent.id)
        child_data["linked_from_type"] = parent.definition.type if parent.definition else ""

        # Create child entity
        from app.models import next_entity_code
        code = next_entity_code(db.session, parent.tenant_id)

        child = Entity(
            tenant_id=parent.tenant_id,
            definition_id=child_def.id,
            code=code,
            status=child_def.statuses[0] if child_def.statuses else "new",
            data=child_data,
            created_by=user_id,
        )
        db.session.add(child)
        db.session.flush()

        # Log
        activity = ActivityLog(
            tenant_id=parent.tenant_id,
            entity_id=child.id,
            user_id=user_id,
            action="created",
            detail=f"Auto-created from {parent.definition.label if parent.definition else 'parent'} {parent.code}",
            governance_level="auto",
        )
        db.session.add(activity)

        # Notify
        notif = Notification(
            tenant_id=parent.tenant_id,
            user_id=user_id,
            entity_id=child.id,
            type="entity_created",
            title=f"{child_def.label} auto-created",
            message=f"From {parent.display_name} ({parent.code})",
            icon="🔄",
        )
        db.session.add(notif)
        db.session.commit()

        return {
            "child_type": child_type,
            "child_id": child.id,
            "child_code": code,
            "child_label": child_def.label,
        }

    @staticmethod
    def get_linked_entities(entity_id: int) -> List[dict]:
        """Get all entities linked to/from this entity."""
        entity = db.session.get(Entity, entity_id)
        if not entity:
            return []

        links = []

        # Children (entities that reference this one)
        children = Entity.query.filter(
            Entity.tenant_id == entity.tenant_id,
            Entity.data["linked_from"].as_string() == str(entity.id),
            Entity.is_archived == False,
        ).all()

        for c in children:
            links.append({
                "id": c.id,
                "code": c.code,
                "type": c.definition.type if c.definition else "unknown",
                "label": c.definition.label if c.definition else "Record",
                "icon": c.definition.icon if c.definition else "📌",
                "status": c.status,
                "display_name": c.display_name,
                "url": f"/entities/{c.definition.type if c.definition else 'entity'}/{c.id}",
                "direction": "child",
            })

        # Parent (the entity this one references)
        linked_from = entity.data.get("linked_from")
        if linked_from:
            parent = db.session.get(Entity, int(linked_from))
            if parent and not parent.is_archived:
                links.append({
                    "id": parent.id,
                    "code": parent.code,
                    "type": parent.definition.type if parent.definition else "unknown",
                    "label": parent.definition.label if parent.definition else "Record",
                    "icon": parent.definition.icon if parent.definition else "📌",
                    "status": parent.status,
                    "display_name": parent.display_name,
                    "url": f"/entities/{parent.definition.type if parent.definition else 'entity'}/{parent.id}",
                    "direction": "parent",
                })

        return links


class WorkflowAutomator:
    """Automates common workflow patterns across entity types."""

    @staticmethod
    def on_entity_create(entity: Entity, user_id: int):
        """Trigger actions when a new entity is created."""
        definition = entity.definition
        if not definition:
            return

        entity_type = definition.type

        # Auto-assign based on round-robin or availability
        if not entity.assigned_to:
            WorkflowAutomator._auto_assign(entity, entity_type)

    @staticmethod
    def _auto_assign(entity: Entity, entity_type: str):
        """Simple round-robin assignment across team members."""
        from app.models import TeamMember
        team = TeamMember.query.filter_by(
            tenant_id=entity.tenant_id, is_active=True
        ).order_by(TeamMember.last_login.asc()).all()

        if team:
            # Assign to the member who's been idle longest
            entity.assigned_to = team[0].id
            db.session.commit()

    @staticmethod
    def suggest_next_step(entity: Entity) -> Optional[str]:
        """Suggest the next logical step for an entity."""
        definition = entity.definition
        if not definition:
            return None

        statuses = definition.statuses or []
        current = entity.status
        if current in statuses:
            idx = statuses.index(current)
            if idx < len(statuses) - 1:
                return f"Move to '{statuses[idx + 1]}'"

        # Check if children exist
        linked = EntityLinker.get_linked_entities(entity.id)
        child_types = [l["type"] for l in linked if l["direction"] == "child"]
        rules = EntityLinker.LINK_RULES.get(definition.type, {})
        for ct in rules.get("child_types", []):
            if ct not in child_types:
                child_def = EntityDefinition.query.filter_by(
                    tenant_id=entity.tenant_id, type=ct, is_active=True
                ).first()
                if child_def:
                    return f"Create {child_def.label} from this {definition.label}"

        return None