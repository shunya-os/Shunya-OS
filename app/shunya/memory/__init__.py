"""Customer Memory — tracks preferences, patterns, and decision history per client.

The system should gradually understand travel style, family composition, comfort
preferences, pace, prior experiences, and decision patterns. This memory persists
across conversations so customers don't need to restart their relationship.
"""
from typing import Optional, List
from datetime import datetime, date
from app import db
from app.models import Entity, EntityDefinition, Message, ActivityLog, AIFeedback


class CustomerMemory:
    """Structured memory of a customer's preferences and history."""

    @staticmethod
    def get_profile(entity_id: int) -> dict:
        """Build a complete customer profile from all available data."""
        entity = db.session.get(Entity, entity_id)
        if not entity:
            return {}

        # Extract known preferences from entity data
        data = entity.data or {}
        profile = {
            "customer_id": entity.id,
            "customer_name": data.get("customer_name", data.get("patient_name", data.get("name", ""))),
            "code": entity.code,
            "status": entity.status,
            "known_preferences": {},
            "travel_history": [],
            "communication_history": [],
            "decision_patterns": [],
            "ai_notes": entity.ai_summary or "",
        }

        # Known preferences from structured data
        pref_fields = {
            "destination": "Preferred destinations",
            "pax": "Travel composition",
            "budget": "Budget range",
            "dates": "Travel period preference",
        }
        for key, label in pref_fields.items():
            if data.get(key):
                profile["known_preferences"][label] = data[key]

        # Travel history from past entities with same name/phone
        if data.get("phone") or data.get("customer_name"):
            from sqlalchemy import or_
            filters = []
            if data.get("phone"):
                filters.append(Entity.data["phone"].as_string() == data["phone"])
            if data.get("customer_name"):
                filters.append(Entity.data["customer_name"].as_string() == data["customer_name"])

            if filters:
                past_entities = Entity.query.filter(
                    Entity.tenant_id == entity.tenant_id,
                    Entity.id != entity.id,
                    Entity.is_archived == False,
                    or_(*filters)
                ).order_by(Entity.created_at.desc()).limit(10).all()

                for pe in past_entities:
                    pd = pe.data or {}
                    profile["travel_history"].append({
                        "code": pe.code,
                        "destination": pd.get("destination", "Unknown"),
                        "status": pe.status,
                        "budget": pd.get("budget", 0),
                        "date": pe.created_at.isoformat() if pe.created_at else None,
                    })

        # Communication history
        messages = Message.query.filter_by(
            entity_id=entity.id
        ).order_by(Message.created_at.desc()).limit(20).all()

        for m in messages:
            profile["communication_history"].append({
                "channel": m.channel,
                "content": m.content[:200],
                "from_client": m.is_from_client,
                "at": m.created_at.isoformat() if m.created_at else None,
            })

        # Decision patterns from activity log
        activities = ActivityLog.query.filter_by(
            tenant_id=entity.tenant_id,
            entity_id=entity.id,
        ).order_by(ActivityLog.created_at.desc()).limit(30).all()

        status_changes = [a for a in activities if a.action == "status_changed"]
        if status_changes:
            profile["decision_patterns"].append({
                "pattern": f"Status progression: {len(status_changes)} changes",
                "detail": " → ".join([s.detail[:30] for s in reversed(status_changes[-5:])]),
            })

        # Check if customer has a history of cancellations
        cancelled = Entity.query.filter(
            Entity.tenant_id == entity.tenant_id,
            Entity.id != entity.id,
            Entity.status == "cancelled",
            or_(*filters) if filters else db.text("false"),
        ).count() if filters else 0

        if cancelled > 0:
            profile["decision_patterns"].append({
                "pattern": "Previous cancellations",
                "detail": f"This customer has cancelled {cancelled} previous bookings",
            })

        return profile

    @staticmethod
    def update_preference(entity_id: int, key: str, value: str) -> bool:
        """Update a known preference for a customer."""
        entity = db.session.get(Entity, entity_id)
        if not entity:
            return False
        if not entity.data:
            entity.data = {}
        entity.data[key] = value
        db.session.commit()
        return True

    @staticmethod
    def get_next_best_offer(entity_id: int) -> dict:
        """Based on history, suggest what this customer might want next."""
        profile = CustomerMemory.get_profile(entity_id)
        suggestions = []

        # If they've traveled to a destination before, suggest similar
        destinations = [h["destination"] for h in profile["travel_history"] if h.get("destination")]
        if destinations:
            suggestions.append({
                "type": "repeat_destination",
                "suggestion": f"Customer has visited {destinations[-1]} before",
                "confidence": "medium",
            })

        # Budget-based suggestions
        budgets = [float(h["budget"]) for h in profile["travel_history"] if h.get("budget")]
        if budgets:
            avg_budget = sum(budgets) / len(budgets)
            suggestions.append({
                "type": "budget_range",
                "suggestion": f"Typical budget range: ₹{avg_budget:,.0f}",
                "confidence": "high",
            })

        return {"customer": profile["customer_name"], "suggestions": suggestions}