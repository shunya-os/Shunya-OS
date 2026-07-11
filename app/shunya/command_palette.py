"""Shunya Command Palette — universal search and action execution (Cmd+K).

Search everything: entities, knowledge base, customer memory, actions.
Execute actions directly from search results — no menu navigation needed.
"""
from typing import List, Optional, Callable
from app import db
from app.models import Entity, EntityDefinition, KnowledgeEntry, TeamMember, ActivityLog
from app.shunya.memory import CustomerMemory
from datetime import datetime, timedelta


class CommandPalette:
    """Unified search across all Shunya data sources."""

    @staticmethod
    def search(query: str, tenant_id: int, user_id: int, role: str = "agent",
               limit: int = 10) -> List[dict]:
        """Search everything and return categorized results."""
        results = []
        q = f"%{query}%"

        # 1. Entities
        definitions = EntityDefinition.query.filter_by(tenant_id=tenant_id, is_active=True).all()
        for d in definitions:
            searchable = d.searchable_fields or []
            if not searchable:
                continue
            filters = []
            for field_name in searchable:
                filters.append(Entity.data[field_name].as_string().ilike(q))
            entities = Entity.query.filter(
                Entity.tenant_id == tenant_id,
                Entity.definition_id == d.id,
                Entity.is_archived == False,
                db.or_(*filters)
            ).order_by(Entity.created_at.desc()).limit(5).all()

            for e in entities:
                results.append({
                    "type": "entity",
                    "category": d.label,
                    "icon": d.icon,
                    "title": e.display_name,
                    "subtitle": f"{e.code} · {e.status}",
                    "url": f"/entities/{d.type}/{e.id}",
                    "actions": [
                        {"label": "View", "url": f"/entities/{d.type}/{e.id}"},
                        {"label": "Edit", "url": f"/entities/{d.type}/{e.id}/edit"},
                        {"label": "Quick Status", "action": "status", "entity_id": e.id},
                    ],
                    "score": 100,
                })

        # 2. Knowledge base
        knowledge = KnowledgeEntry.query.filter(
            KnowledgeEntry.tenant_id == tenant_id,
            KnowledgeEntry.question.ilike(q)
        ).order_by(KnowledgeEntry.use_count.desc()).limit(5).all()

        for k in knowledge:
            results.append({
                "type": "knowledge",
                "category": "Knowledge Base",
                "icon": "🧠",
                "title": k.question[:100],
                "subtitle": k.answer[:150],
                "url": None,
                "actions": [],
                "score": 80,
            })

        # 3. Customer memory
        entity_matches = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            db.or_(
                Entity.data["customer_name"].as_string().ilike(q),
                Entity.data["phone"].as_string().ilike(q),
                Entity.data["email"].as_string().ilike(q),
            )
        ).limit(5).all()

        for e in entity_matches:
            profile = CustomerMemory.get_profile(e.id)
            if profile:
                results.append({
                    "type": "customer",
                    "category": "Customer Memory",
                    "icon": "👤",
                    "title": profile.get("customer_name", e.display_name),
                    "subtitle": f"{len(profile.get('travel_history', []))} trips · {len(profile.get('communication_history', []))} messages",
                    "url": f"/entities/{e.definition.type if e.definition else 'entity'}/{e.id}",
                    "actions": [{"label": "View Profile", "url": f"/entities/{e.definition.type if e.definition else 'entity'}/{e.id}"}],
                    "score": 90,
                })

        # 4. Quick actions (slash commands)
        if query.startswith("/"):
            cmd = query[1:].lower().strip()
            quick_actions = CommandPalette._get_quick_actions(cmd, tenant_id, user_id, role)
            results.extend(quick_actions)

        # Sort by score
        results.sort(key=lambda r: r.get("score", 0), reverse=True)
        return results[:limit]

    @staticmethod
    def _get_quick_actions(cmd: str, tenant_id: int, user_id: int,
                           role: str) -> List[dict]:
        """Slash commands for quick actions."""
        actions = []
        definitions = EntityDefinition.query.filter_by(tenant_id=tenant_id, is_active=True).all()

        for d in definitions:
            if cmd in d.type.lower() or cmd in d.label.lower():
                actions.append({
                    "type": "quick_action",
                    "category": "Quick Actions",
                    "icon": d.icon,
                    "title": f"New {d.label}",
                    "subtitle": f"Create a new {d.label.lower()} record",
                    "url": f"/entities/{d.type}/new",
                    "actions": [{"label": "Create", "url": f"/entities/{d.type}/new"}],
                    "score": 95,
                })

        # Dashboard and settings
        if cmd in ("dashboard", "home", "dash"):
            actions.append({
                "type": "quick_action", "category": "Navigation", "icon": "🏠",
                "title": "Dashboard", "subtitle": "Go to dashboard",
                "url": "/", "actions": [], "score": 95,
            })
        if cmd in ("settings", "config", "setup"):
            actions.append({
                "type": "quick_action", "category": "Navigation", "icon": "⚙️",
                "title": "Settings", "subtitle": "Manage settings",
                "url": "/settings", "actions": [], "score": 95,
            })
        if cmd in ("sessions", "logout"):
            actions.append({
                "type": "quick_action", "category": "Navigation", "icon": "🔐",
                "title": "Sessions", "subtitle": "Manage active sessions",
                "url": "/auth/sessions", "actions": [], "score": 95,
            })

        return actions

    @staticmethod
    def execute_action(action_type: str, params: dict, tenant_id: int,
                       user_id: int) -> dict:
        """Execute a one-tap action from the command palette."""
        from app.shunya.executor import Executor, ActionType
        from app.shunya.governance import GovernanceEngine

        action_map = {
            "status": ActionType.CHANGE_STATUS,
            "message": ActionType.SEND_MESSAGE,
            "create": ActionType.CREATE_ENTITY,
            "delete": ActionType.DELETE_ENTITY,
        }

        action = action_map.get(action_type)
        if not action:
            return {"error": f"Unknown action: {action_type}"}

        # Execute through governance
        result = Executor.execute(
            tenant_id=tenant_id,
            user_id=user_id,
            user_role="agent",  # Will be overridden by actual role
            action_type=action,
            entity_id=params.get("entity_id"),
            params=params,
        )

        return result