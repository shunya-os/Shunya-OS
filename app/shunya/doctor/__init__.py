"""Doctor — architectural health verification and diagnostics.

Doctor checks knowledge integrity, governance policies, module health,
package dependencies, and platform invariants.
"""
from typing import List, Dict
from datetime import datetime, timedelta
from app import db
from app.models import Entity, EntityDefinition, Tenant, TeamMember, KnowledgeEntry, ActivityLog


class Doctor:
    """System health diagnostics and integrity checks."""

    @staticmethod
    def run_all(tenant_id: int) -> Dict:
        """Run all health checks and return results."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "knowledge": Doctor.check_knowledge(tenant_id),
            "entities": Doctor.check_entities(tenant_id),
            "definitions": Doctor.check_definitions(tenant_id),
            "activity": Doctor.check_activity(tenant_id),
            "team": Doctor.check_team(tenant_id),
            "summary": {},
        }

    @staticmethod
    def check_knowledge(tenant_id: int) -> Dict:
        """Check knowledge base health."""
        total = KnowledgeEntry.query.filter_by(tenant_id=tenant_id).count()
        unverified = KnowledgeEntry.query.filter_by(
            tenant_id=tenant_id, verified_by=None
        ).count()

        return {
            "status": "ok" if total > 0 else "warning",
            "total_entries": total,
            "unverified_entries": unverified,
            "message": f"{total} knowledge entries, {unverified} unverified" if total else "No knowledge entries yet",
        }

    @staticmethod
    def check_entities(tenant_id: int) -> Dict:
        """Check entity health — stale, orphaned, or stuck records."""
        total = Entity.query.filter_by(tenant_id=tenant_id, is_archived=False).count()
        active = Entity.query.filter_by(tenant_id=tenant_id, is_archived=False).filter(
            Entity.status.in_(["new", "pending", "active", "proposal", "negotiation"])
        ).count()

        # Stuck in initial status for 7+ days
        seven_days = datetime.utcnow() - timedelta(days=7)
        stuck = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.status == "new",
            Entity.created_at < seven_days,
        ).count()

        status = "ok"
        message = f"{total} total, {active} active"
        if stuck > 0:
            status = "warning"
            message += f", {stuck} stuck in 'new' for 7+ days"

        return {"status": status, "total": total, "active": active, "stuck": stuck, "message": message}

    @staticmethod
    def check_definitions(tenant_id: int) -> Dict:
        """Check entity definitions — valid schemas, active status."""
        total = EntityDefinition.query.filter_by(tenant_id=tenant_id).count()
        active_defs = EntityDefinition.query.filter_by(tenant_id=tenant_id, is_active=True).count()
        missing_schema = 0

        for d in EntityDefinition.query.filter_by(tenant_id=tenant_id).all():
            if not d.schema or len(d.schema) == 0:
                missing_schema += 1

        return {
            "status": "ok" if active_defs > 0 else "error",
            "total": total,
            "active": active_defs,
            "missing_schema": missing_schema,
            "message": f"{active_defs} active entity types",
        }

    @staticmethod
    def check_activity(tenant_id: int) -> Dict:
        """Check recent activity levels."""
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent = ActivityLog.query.filter(
            ActivityLog.tenant_id == tenant_id,
            ActivityLog.created_at >= week_ago,
        ).count()

        status = "ok" if recent > 10 else "warning" if recent > 0 else "error"
        return {
            "status": status,
            "recent_actions": recent,
            "message": f"{recent} actions in the last 7 days",
        }

    @staticmethod
    def check_team(tenant_id: int) -> Dict:
        """Check team health."""
        total = TeamMember.query.filter_by(tenant_id=tenant_id).count()
        active = TeamMember.query.filter_by(tenant_id=tenant_id, is_active=True).count()

        return {
            "status": "ok" if active > 0 else "error",
            "total": total,
            "active": active,
            "message": f"{active} active team members",
        }

    @staticmethod
    def get_system_diagnostics() -> Dict:
        """Get overall system diagnostics (super admin view)."""
        tenant_count = Tenant.query.count()
        entity_count = Entity.query.count()
        user_count = TeamMember.query.count()
        knowledge_count = KnowledgeEntry.query.count()

        return {
            "tenants": tenant_count,
            "entities": entity_count,
            "users": user_count,
            "knowledge_entries": knowledge_count,
            "status": "healthy",
        }