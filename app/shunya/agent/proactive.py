"""Shunya Personal Agent — Proactive Engine.

Makes the agent initiate instead of just respond.
Time-based triggers, event-based triggers, pattern learning.
"""
from __future__ import annotations
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging, random

logger = logging.getLogger("app.shunya.agent.proactive")


class TriggerType(str, Enum):
    TIME = "time"          # Every day at 10 AM
    STALE = "stale"        # Entity hasn't been touched in N days
    THRESHOLD = "threshold"  # Metric crossed a threshold
    PATTERN = "pattern"    # Learned from user behavior
    EVENT = "event"        # Something happened (entity created, status changed)
    GREETING = "greeting"  # Morning / time-of-day greeting


@dataclass
class ProactiveMessage:
    """A message the agent proactively sends to the user."""
    id: str = ""
    title: str = ""
    body: str = ""
    icon: str = "💡"
    priority: str = "normal"   # "high" | "normal" | "low"
    action_url: str = ""       # Link to take action
    action_label: str = ""     # "View →"
    trigger_type: TriggerType = TriggerType.GREETING
    ttl_minutes: int = 60      # How long this message is relevant
    confidence: float = 0.7


@dataclass
class UserPattern:
    """Learned user behavior pattern."""
    user_id: int
    tenant_id: int
    pattern_type: str          # "check_leads_morning", "invoice_evening", etc.
    trigger_hour: int          # Hour of day user typically does this
    trigger_day: str = ""      # "weekday" | "weekend" | "monday" etc.
    action_count: int = 0      # How many times observed
    last_action: str = ""      # Last time observed
    is_active: bool = True


# ---------------------------------------------------------------------------
# Pattern Learner
# ---------------------------------------------------------------------------

class PatternLearner:
    """Learns user behavior patterns from activity logs."""

    @staticmethod
    def learn(user_id: int, tenant_id: int) -> list[UserPattern]:
        """Analyze activity logs and extract patterns."""
        from app.models import ActivityLog
        patterns = []

        # Get recent activity
        recent = ActivityLog.query.filter_by(
            tenant_id=tenant_id, user_id=user_id
        ).order_by(ActivityLog.created_at.desc()).limit(100).all()

        if not recent:
            return patterns

        # Group by hour and action type
        hour_action_counts: dict[str, dict[int, int]] = {}
        for act in recent:
            if not act.created_at:
                continue
            hour = act.created_at.hour
            action = act.action.split(".")[0]  # "created", "updated", "status_changed"
            if action not in hour_action_counts:
                hour_action_counts[action] = {}
            hour_action_counts[action][hour] = hour_action_counts[action].get(hour, 0) + 1

        # Detect patterns: if an action peaks at a specific hour, it's a pattern
        for action, hours in hour_action_counts.items():
            if not hours:
                continue
            best_hour = max(hours, key=hours.get)
            count = hours[best_hour]
            total = sum(hours.values())

            # Only consider if this hour has >40% of total activity
            if total > 3 and count / total >= 0.4:
                pattern_label = {
                    "created": "check_records",
                    "status_changed": "update_status",
                    "message_sent": "send_messages",
                }.get(action, action)

                patterns.append(UserPattern(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    pattern_type=pattern_label,
                    trigger_hour=best_hour,
                    action_count=total,
                    last_action=recent[0].created_at.isoformat() if recent[0].created_at else "",
                ))

        return patterns

    @staticmethod
    def store_patterns(patterns: list[UserPattern]):
        """Store learned patterns to memory."""
        from app.shunya.memory import MemoryStore, MemoryClass
        for p in patterns:
            content = (
                f"pattern:{p.pattern_type}, hour:{p.trigger_hour}, "
                f"count:{p.action_count}, active:{p.is_active}"
            )
            MemoryStore.store(MemoryClass.LEARNING, p.tenant_id,
                              key=f"pattern_{p.user_id}_{p.pattern_type}",
                              content=content, entity_id=p.user_id)


# ---------------------------------------------------------------------------
# Trigger Checkers
# ---------------------------------------------------------------------------

def check_stale_entities(tenant_id: int, user_id: int) -> list[ProactiveMessage]:
    """Find entities that haven't been touched in N days."""
    from app.models import Entity, EntityDefinition
    from datetime import datetime, timedelta

    msgs = []
    now = datetime.utcnow()

    definitions = EntityDefinition.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    for d in definitions:
        stale = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == d.id,
            Entity.is_archived == False,
            Entity.status.in_(["new", "pending", "contacted", "sent"]),
            Entity.updated_at < now - timedelta(days=3),
        ).count()

        if stale > 0:
            msgs.append(ProactiveMessage(
                id=f"stale_{d.type}_{now.timestamp()}",
                title=f"{stale} {d.label_plural or d.label} need attention",
                body=f"{stale} record(s) in '{d.type}' haven't been updated in 3+ days.",
                icon=d.icon or "⏰",
                priority="high" if stale > 5 else "normal",
                action_url=f"/entities/{d.type}?status=new,pending",
                action_label=f"View {d.label_plural or d.label}",
                trigger_type=TriggerType.STALE,
            ))

    return msgs


def check_invoices_due(tenant_id: int, user_id: int) -> list[ProactiveMessage]:
    """Check for invoices due within 3 days."""
    from app.models import Entity, EntityDefinition

    definition = EntityDefinition.query.filter_by(tenant_id=tenant_id, type="invoice").first()
    if not definition:
        return []

    from datetime import datetime
    due_soon = Entity.query.filter(
        Entity.tenant_id == tenant_id,
        Entity.definition_id == definition.id,
        Entity.is_archived == False,
        Entity.status == "sent",
    ).all()

    msgs = []
    for inv in due_soon:
        due_date = inv.data.get("due_date", "")
        amount = inv.data.get("total", inv.data.get("amount", ""))
        customer = inv.data.get("customer_name", inv.display_name)
        msgs.append(ProactiveMessage(
            id=f"invoice_due_{inv.id}",
            title=f"💰 Invoice due: {customer}",
            body=f"₹{amount} — due {due_date}",
            priority="high",
            action_url=f"/entities/invoice/{inv.id}",
            action_label="View Invoice",
            trigger_type=TriggerType.THRESHOLD,
        ))

    return msgs


def check_unread_messages(tenant_id: int, user_id: int) -> list[ProactiveMessage]:
    """Check for unread client messages or pending approvals."""
    from app.models import ActivityLog
    pending = ActivityLog.query.filter_by(
        tenant_id=tenant_id,
        governance_level="govern",
    ).count()

    if pending > 0:
        return [ProactiveMessage(
            id=f"pending_approvals_{datetime.utcnow().timestamp()}",
            title=f"🔐 {pending} pending approval(s)",
            body="Actions waiting for your review in Governance.",
            priority="high",
            action_url="/governance",
            action_label="Review →",
            trigger_type=TriggerType.EVENT,
        )]
    return []


def generate_greeting(user_id: int, tenant_id: int, user_name: str = "") -> ProactiveMessage:
    """Generate a time-of-day greeting with context."""
    from app.models import Entity, EntityDefinition

    hour = datetime.utcnow().hour
    if hour < 12:
        greeting = "Good morning"
        icon = "🌅"
    elif hour < 17:
        greeting = "Good afternoon"
        icon = "☀️"
    else:
        greeting = "Good evening"
        icon = "🌙"

    # Count pending items
    pending = 0
    defs = EntityDefinition.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    for d in defs[:3]:
        pending += Entity.query.filter_by(
            tenant_id=tenant_id, definition_id=d.id, is_archived=False
        ).filter(Entity.status.in_(["new", "pending"])).count()

    body = f"You have {pending} items needing attention today." if pending else "Ready to make today productive?"
    name_part = f" {user_name}!" if user_name else "!"

    return ProactiveMessage(
        id=f"greeting_{datetime.utcnow().strftime('%Y%m%d')}",
        title=f"{greeting},{name_part}",
        body=body,
        icon=icon,
        priority="normal",
        trigger_type=TriggerType.GREETING,
    )


# ---------------------------------------------------------------------------
# Proactive Engine
# ---------------------------------------------------------------------------

class ProactiveEngine:
    """Generates proactive messages based on triggers and patterns."""

    CHECKERS: list[Callable] = [
        check_stale_entities,
        check_invoices_due,
        check_unread_messages,
    ]

    def __init__(self, user_id: int, tenant_id: int):
        self.user_id = user_id
        self.tenant_id = tenant_id

    def get_messages(self, max_messages: int = 5) -> list[ProactiveMessage]:
        """Get proactive messages for this user right now."""
        from app.models import TeamMember

        msgs: list[ProactiveMessage] = []

        # 1. Run all checkers
        for checker in self.CHECKERS:
            try:
                results = checker(self.tenant_id, self.user_id)
                msgs.extend(results)
            except Exception as e:
                logger.warning("Proactive checker %s failed: %s", checker.__name__, e)

        # 2. Check learned patterns
        patterns = PatternLearner.learn(self.user_id, self.tenant_id)
        current_hour = datetime.utcnow().hour
        for p in patterns:
            if p.trigger_hour == current_hour and p.is_active:
                msgs.append(ProactiveMessage(
                    id=f"pattern_{p.pattern_type}_{p.trigger_hour}",
                    title=f"📊 Time to {p.pattern_type.replace('_', ' ')}?",
                    body=f"You usually do this around this time ({p.action_count} times).",
                    priority="low",
                    trigger_type=TriggerType.PATTERN,
                    confidence=0.5,
                ))

        # 3. Sort by priority
        priority_order = {"high": 0, "normal": 1, "low": 2}
        msgs.sort(key=lambda m: priority_order.get(m.priority, 2))

        # 4. Deduplicate by id
        seen = set()
        unique = []
        for m in msgs:
            if m.id not in seen:
                seen.add(m.id)
                unique.append(m)

        return unique[:max_messages]

    def get_greeting(self, user_name: str = "") -> ProactiveMessage:
        """Get the greeting message with context."""
        greeting = generate_greeting(self.user_id, self.tenant_id, user_name)
        # Add one high-priority proactive message after greeting
        messages = self.get_messages(2)
        if messages:
            greeting.body += f" {messages[0].title}"
        return greeting

    def get_suggestions(self) -> list[dict]:
        """Get quick action suggestions based on entity types."""
        from app.models import EntityDefinition, Entity

        suggestions = []
        defs = EntityDefinition.query.filter_by(
            tenant_id=self.tenant_id, is_active=True
        ).limit(4).all()

        for d in defs:
            count = Entity.query.filter_by(
                tenant_id=self.tenant_id, definition_id=d.id, is_archived=False
            ).count()
            suggestions.append({
                "icon": d.icon or "📋",
                "text": f"Review {d.label_plural or d.label} ({count})",
                "action": f"/entities/{d.type}",
            })

        return suggestions


# ---------------------------------------------------------------------------
# Agent-level Proactive Runner (for cron)
# ---------------------------------------------------------------------------

def run_proactive_scan(tenant_id: int, user_id: int) -> list[dict]:
    """Run a proactive scan and return actionable messages."""
    engine = ProactiveEngine(user_id, tenant_id)
    messages = engine.get_messages(5)
    return [{
        "id": m.id,
        "title": m.title,
        "body": m.body,
        "icon": m.icon,
        "priority": m.priority,
        "action_url": m.action_url,
        "action_label": m.action_label,
        "trigger_type": m.trigger_type.value,
    } for m in messages]


def run_all_tenants_proactive():
    """Run proactive scans for all tenants (for scheduled cron)."""
    from app.models import Tenant, TeamMember
    all_messages = []
    tenants = Tenant.query.filter_by(is_active=True).all()
    for tenant in tenants:
        admins = TeamMember.query.filter_by(tenant_id=tenant.id, role="admin").limit(3).all()
        for admin in admins:
            try:
                msgs = run_proactive_scan(tenant.id, admin.id)
                all_messages.extend(msgs)
            except Exception as e:
                logger.error("Proactive scan failed for tenant %s: %s", tenant.id, e)
    return all_messages