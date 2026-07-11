"""Shunya Doctor — Autonomous health monitoring (cron-ready).

Runs hourly checks and alerts via WhatsApp/Telegram if issues detected.
"""
from datetime import datetime, timedelta
from app import db
from app.models import Entity, EntityDefinition, KnowledgeEntry, TeamMember, ActivityLog


class DoctorCron:
    """Hourly health checks with alerting."""

    @staticmethod
    def run_all(tenant_id: int) -> dict:
        """Run all health checks and return results + alerts."""
        alerts = []
        now = datetime.utcnow()

        # 1. Stuck entities in initial status for 7+ days
        stuck = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.status.in_(["new", "pending"]),
            Entity.created_at < now - timedelta(days=7),
        ).count()
        if stuck > 3:
            alerts.append({
                "type": "stuck_entities",
                "severity": "warning",
                "message": f"{stuck} entities stuck in initial status for 7+ days",
                "action": "Review and reassign or follow up",
            })
        elif stuck > 0:
            alerts.append({
                "type": "stuck_entities",
                "severity": "info",
                "message": f"{stuck} entities need attention",
                "action": "Quick review recommended",
            })

        # 2. Unassigned entities
        unassigned = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.assigned_to == None,
        ).count()
        if unassigned > 5:
            alerts.append({
                "type": "unassigned",
                "severity": "warning",
                "message": f"{unassigned} entities unassigned",
                "action": "Assign team members",
            })

        # 3. Knowledge gaps (no knowledge entries)
        kb_count = KnowledgeEntry.query.filter_by(tenant_id=tenant_id).count()
        if kb_count == 0:
            alerts.append({
                "type": "knowledge_gap",
                "severity": "info",
                "message": "Knowledge base is empty — AI responses won't have internal data",
                "action": "Seed knowledge base with common questions",
            })

        # 4. Low activity in last 24h
        yesterday = now - timedelta(hours=24)
        recent = ActivityLog.query.filter(
            ActivityLog.tenant_id == tenant_id,
            ActivityLog.created_at >= yesterday,
        ).count()
        if recent == 0:
            alerts.append({
                "type": "no_activity",
                "severity": "warning",
                "message": "No activity in the last 24 hours",
                "action": "Check if team is engaged",
            })

        # 5. Team health
        active_team = TeamMember.query.filter_by(
            tenant_id=tenant_id, is_active=True
        ).count()
        if active_team == 0:
            alerts.append({
                "type": "no_team",
                "severity": "critical",
                "message": "No active team members",
                "action": "Add team members immediately",
            })

        return {
            "timestamp": now.isoformat(),
            "tenant_id": tenant_id,
            "alerts": alerts,
            "alert_count": len(alerts),
            "severity": "critical" if any(a["severity"] == "critical" for a in alerts)
                        else "warning" if alerts else "healthy",
            "summary": f"{len(alerts)} issue(s) found" if alerts else "All systems healthy",
        }

    @staticmethod
    def send_alerts(tenant_id: int, phone: str = None):
        """Send health alerts via WhatsApp if configured."""
        result = DoctorCron.run_all(tenant_id)
        if not result["alerts"]:
            return

        try:
            from app.shunya.whatsapp import WhatsAppChannel
            if phone:
                text = "🏥 *Shunya Health Report*\n\n"
                for a in result["alerts"]:
                    emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
                    text += f"{emoji.get(a['severity'], '⚪')} *{a['severity'].upper()}*: {a['message']}\n   → {a['action']}\n\n"
                WhatsAppChannel.send(phone, text, tenant_id)
        except Exception:
            pass