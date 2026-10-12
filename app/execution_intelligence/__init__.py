"""Execution Intelligence — next_actions() DB-backed implementation.

Queries the canonical SHUNYA database for actionable items across
Commitments, Tasks, Invoices, Leads, and Notifications.
Provides prioritized action recommendations with evidence.
"""

import logging
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# Enums
# ════════════════════════════════════════════════════════════════

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"

class ActionPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class HealthDimension(str, Enum):
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    SECURITY = "security"
    COST = "cost"


# ════════════════════════════════════════════════════════════════
# Data Classes — kept for backward compat (all accept **kw)
# ════════════════════════════════════════════════════════════════

class HealthAssessment:
    """Multi-dimensional health evaluation with backward compat."""
    def __init__(self, **kw):
        self.overall = kw.get("overall", kw.get("status", HealthStatus.HEALTHY.value))
        self.status = kw.get("status", self.overall)
        self.score = kw.get("score", 1.0)
        self.dimensions = kw.get("dimensions", {})
        self.scores = kw.get("scores", {})
        self.evidence = kw.get("evidence", {})
        self.exec_id = kw.get("exec_id", "")
        self.tenant_id = kw.get("tenant_id", 0)


class RiskAssessment:
    """Risk evaluation with typed factors. Compat: .overall_risk .factors .to_dict()"""
    def __init__(self, **kw):
        self.overall_risk = kw.get("overall_risk", kw.get("risk_level", "low"))
        self.factors = kw.get("factors", [])
        self.exec_id = kw.get("exec_id", "")
        self.tenant_id = kw.get("tenant_id", 0)

    def to_dict(self):
        return {
            "exec_id": self.exec_id,
            "overall_risk": self.overall_risk,
            "factors": [f.to_dict() if hasattr(f, 'to_dict') else f for f in self.factors],
        }


class TimelineSnapshot:
    def __init__(self, **kw):
        self.timestamp = kw.get("timestamp", datetime.now(timezone.utc))
        self.state = kw.get("state", {})
        self.exec_id = kw.get("exec_id", "")
        self.tenant_id = kw.get("tenant_id", 0)
        self.completion_ratio = kw.get("completion_ratio", 0.0)
        self.started_at = kw.get("started_at")
        self.completed_at = kw.get("completed_at")

    def to_dict(self):
        return {
            "exec_id": self.exec_id,
            "timestamp": self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else self.timestamp,
            "completion_ratio": self.completion_ratio,
        }


class CompletionPrediction:
    def __init__(self, **kw):
        self.predicted_at = kw.get("predicted_at")
        self.confidence = kw.get("confidence", 0.0)
        self.exec_id = kw.get("exec_id", "")

    def to_dict(self):
        return {"exec_id": self.exec_id, "predicted_at": self.predicted_at, "confidence": self.confidence}


class RiskFactor:
    def __init__(self, **kw):
        self.category = kw.get("category", "unknown")
        self.risk_type = kw.get("risk_type", kw.get("category", "unknown"))
        self.description = kw.get("description", "")
        self.severity = kw.get("severity", "low")
        self.level = kw.get("level", kw.get("severity", "low"))
        self.evidence = kw.get("evidence", [])

    def to_dict(self):
        return {"risk_type": self.risk_type, "description": self.description,
                "level": self.level, "evidence": self.evidence}


class DependencyNode:
    def __init__(self, **kw):
        self.id = kw.get("id", "")
        self.type = kw.get("type", "unknown")


class DependencyEdge:
    def __init__(self, **kw):
        self.source = kw.get("source", "")
        self.target = kw.get("target", "")
        self.type = kw.get("type", "depends_on")


class CriticalPath:
    def __init__(self, **kw):
        self.path = kw.get("path", [])
        self.bottlenecks = kw.get("bottlenecks", [])
        self.total_length = kw.get("total_length", 0)

    def to_dict(self):
        return {"path": self.path, "bottlenecks": self.bottlenecks, "total_length": self.total_length}


class NextAction:
    """Returned by suggest_next_action for backward compat."""
    def __init__(self, **kw):
        self.action_id = kw.get("action_id", "")
        self.action = kw.get("action", "")
        self.action_type = kw.get("action_type", kw.get("type", ""))
        self.priority = kw.get("priority", ActionPriority.LOW)
        self.reason = kw.get("reason", "")
        self.description = kw.get("description", kw.get("title", ""))
        self.exec_id = kw.get("exec_id", "")
        self.tenant_id = kw.get("tenant_id", 0)
        self.evidence = kw.get("evidence", [])
        self.due_at = kw.get("due_at")
        self.created_at = kw.get("created_at")

    def to_dict(self):
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "priority": self.priority,
            "description": self.description,
            "exec_id": self.exec_id,
            "due_at": self.due_at,
            "created_at": self.created_at,
        }


class PortfolioSummary:
    def __init__(self, **kw):
        self.total = kw.get("total", 0)
        self.active = kw.get("active", 0)
        self.completed = kw.get("completed", 0)

    def to_dict(self):
        return {"total": self.total, "active": self.active, "completed": self.completed}


class PortfolioBreakdown:
    pass


class EvidenceTrace:
    def __init__(self, **kw):
        self.source = kw.get("source", "engine")
        self.timestamp = kw.get("timestamp", datetime.now(timezone.utc))

    def to_dict(self):
        return {"source": self.source, "timestamp": str(self.timestamp)}


class Explanation:
    def __init__(self, **kw):
        self.text = kw.get("text", "")
        self.evidence = kw.get("evidence", [])

    def to_dict(self):
        return {"text": self.text, "evidence": [e.to_dict() if hasattr(e, 'to_dict') else e for e in self.evidence]}


class RuntimeConfig:
    def __init__(self, **kw):
        self.health_warning_threshold = kw.get("health_warning_threshold", 0.7)
        self.health_critical_threshold = kw.get("health_critical_threshold", 0.4)
        self.risk_timeout_threshold_hours = kw.get("risk_timeout_threshold_hours", 48)
        self.portfolio_top_k = kw.get("portfolio_top_k", 5)
        self.enable_explainability = kw.get("enable_explainability", True)

    def to_dict(self):
        return {
            "health_warning_threshold": self.health_warning_threshold,
            "health_critical_threshold": self.health_critical_threshold,
            "risk_timeout_threshold_hours": self.risk_timeout_threshold_hours,
        }


class QueryFilter:
    pass


# ════════════════════════════════════════════════════════════════
# ActionItem — dict subclass that supports attribute access
# for legacy callers (a.action_type → a["type"])
# ════════════════════════════════════════════════════════════════

class ActionItem(dict):
    """Action dict with attribute access and alias mapping.

    Legacy callers access a.action_type → maps to a["type"]
    Legacy callers access a.exec_id → maps to a["entity_id"]
    """
    def __getattr__(self, name):
        try:
            if name == "action_type":
                return self["type"]
            if name == "exec_id":
                return self["entity_id"]
            return self[name]
        except KeyError as exc:
            raise AttributeError(f"ActionItem has no attribute '{name}'") from exc

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def to_dict(self):
        return dict(self)


# ════════════════════════════════════════════════════════════════
# Scope resolver
# ════════════════════════════════════════════════════════════════

def _resolve_scope(org_id=None, identity_id=None):
    """Resolve org_id and identity_id from kwargs or flask g."""
    result = {}
    if org_id is not None:
        result["org_id"] = org_id
    if identity_id is not None:
        result["identity_id"] = identity_id
    if result:
        return result
    # Try flask g
    try:
        from flask import g
        for key in ("organization_id", "org_id", "tenant_id"):
            if hasattr(g, key):
                result["org_id"] = getattr(g, key)
                break
        if hasattr(g, "identity_id"):
            result["identity_id"] = g.identity_id
    except Exception:
        pass
    return result


# ════════════════════════════════════════════════════════════════
# DB-backed action queries
# ════════════════════════════════════════════════════════════════

def _db():
    """Return db.session — guarded."""
    try:
        from app import db
        return db.session
    except Exception:
        return None


def _now_utc():
    return datetime.now(timezone.utc)


def _due_sort_key(a):
    prio = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    ap = a.get("priority", "low")
    due = a.get("due_at")
    due_ts = 0
    if due:
        try:
            if isinstance(due, str):
                due_ts = datetime.fromisoformat(due.replace("Z", "+00:00")).timestamp()
            elif hasattr(due, "timestamp"):
                due_ts = due.timestamp()
        except (ValueError, TypeError):
            due_ts = 0
    return (prio.get(ap, 99), due_ts if due_ts else float("inf"))


def _commitment_actions(scope: dict) -> list[dict]:
    """Overdue/in-progress commitments from app.commitments.models.Commitment."""
    try:
        from app.commitments.models import Commitment
    except ImportError:
        return []
    session = _db()
    if session is None:
        return []
    try:
        now = _now_utc()
        q = session.query(Commitment).filter(
            Commitment.status.in_(["pending", "in_progress"])
        )
        # Identity scope if applicable
        identity_id = scope.get("identity_id")
        if identity_id and hasattr(Commitment, "owner"):
            q = q.filter(Commitment.owner == identity_id)
        results = q.order_by(Commitment.created_at.desc()).limit(50).all()
    except Exception as exc:
        logger.warning("execution_intelligence commitment query failed: %s", exc)
        return []

    actions = []
    for c in results:
        overdue = False
        if c.due_at:
            cd = c.due_at
            if cd.tzinfo is None:
                try:
                    from datetime import timezone as tz
                    cd = cd.replace(tzinfo=tz.utc)
                except Exception:
                    pass
            overdue = cd < now
        priority = ActionPriority.CRITICAL if overdue else (
            ActionPriority.HIGH if c.status == "in_progress" else ActionPriority.MEDIUM
        )
        desc = c.title or f"Commitment #{c.id}"
        if overdue:
            desc = f"OVERDUE: {desc}"
        actions.append(ActionItem(
            action_id=f"commitment-{c.id}",
            type="commitment_overdue" if overdue else "commitment_pending",
            priority=priority.value,
            title=f"Commitment: {c.title or ''}"[:200],
            description=desc[:200],
            entity_type="commitment",
            entity_id=c.id,
            due_at=c.due_at.isoformat() if c.due_at else None,
            created_at=c.created_at.isoformat() if c.created_at else None,
        ))
    return actions


def _task_actions(scope: dict) -> list[dict]:
    """Open high-priority tasks and overdue tasks."""
    try:
        from app.models import Task
    except ImportError:
        return []
    session = _db()
    if session is None:
        return []
    try:
        now_dt = _now_utc()
        today = now_dt.date()
        q = session.query(Task).filter(
            Task.status.in_(["pending", "in_progress"]),
            Task.priority.in_(["high", "urgent"]),
        )
        identity_id = scope.get("identity_id")
        if identity_id and hasattr(Task, "assigned_to"):
            q = q.filter(Task.assigned_to == identity_id)
        results = q.order_by(Task.created_at.desc()).limit(50).all()
    except Exception as exc:
        logger.warning("execution_intelligence task query failed: %s", exc)
        return []

    actions = []
    for t in results:
        prio_map = {"urgent": ActionPriority.CRITICAL, "high": ActionPriority.HIGH,
                    "medium": ActionPriority.MEDIUM, "low": ActionPriority.LOW}
        priority = prio_map.get(t.priority, ActionPriority.MEDIUM)
        overdue = False
        if t.due_date:
            dd = t.due_date
            if hasattr(dd, "tzinfo") and dd.tzinfo is None:
                dd = dd
            if isinstance(dd, type(today)) and dd < today:
                priority = ActionPriority.CRITICAL
                overdue = True
            elif isinstance(dd, type(today)):
                pass
        desc = t.title or f"Task #{t.id}"
        if overdue:
            desc = f"OVERDUE: {desc}"
        actions.append(ActionItem(
            action_id=f"task-{t.id}",
            type="task_overdue" if overdue else "task_high_priority",
            priority=priority.value,
            title=f"Task: {t.title or ''}"[:200],
            description=desc[:200],
            entity_type="task",
            entity_id=t.id,
            due_at=t.due_date.isoformat() if t.due_date else None,
            created_at=t.created_at.isoformat() if t.created_at else None,
        ))
    return actions


def _invoice_actions(scope: dict) -> list[dict]:
    """Unpaid/overdue invoices."""
    try:
        from app.finance.models import FinInvoice
    except ImportError:
        return []
    session = _db()
    if session is None:
        return []
    try:
        q = session.query(FinInvoice).filter(
            FinInvoice.status.in_(["sent", "unpaid", "overdue"]),
        )
        org_id = scope.get("org_id")
        if org_id is not None and hasattr(FinInvoice, "organization_id"):
            q = q.filter(FinInvoice.organization_id == org_id)
        results = q.order_by(FinInvoice.created_at.desc()).limit(50).all()
    except Exception as exc:
        logger.warning("execution_intelligence invoice query failed: %s", exc)
        return []

    now = _now_utc()
    actions = []
    for inv in results:
        overdue = inv.status == "overdue" or (inv.due_date and _date_to_dt(inv.due_date) < now)
        priority = ActionPriority.CRITICAL if overdue else ActionPriority.HIGH
        label = f"Invoice {inv.number or f'#{inv.id}'}"
        desc = f"{'OVERDUE: ' if overdue else ''}{label} — balance due: ₹{float(inv.total_amount or 0) - float(inv.paid_amount or 0):.0f}"

        actions.append(ActionItem(
            action_id=f"invoice-{inv.id}",
            type="invoice_overdue" if overdue else "invoice_unpaid",
            priority=priority.value,
            title=f"Invoice: {inv.number or inv.id}"[:200],
            description=desc[:200],
            entity_type="invoice",
            entity_id=inv.id,
            due_at=inv.due_date.isoformat() if inv.due_date else None,
            created_at=inv.created_at.isoformat() if inv.created_at else None,
        ))
    return actions


def _lead_actions(scope: dict) -> list[dict]:
    """Leads needing follow-up (new/inquiry/in_progress with stale activity)."""
    try:
        from app.models import Lead, ActivityLog
        from sqlalchemy import func
    except ImportError:
        return []
    session = _db()
    if session is None:
        return []
    try:
        cutoff = _now_utc() - timedelta(hours=72)
        q = session.query(Lead).filter(
            Lead.status.in_(["new", "inquiry", "in_progress"]),
        )
        org_id = scope.get("org_id")
        if org_id is not None and hasattr(Lead, "tenant_id"):
            q = q.filter(Lead.tenant_id == org_id)
        identity_id = scope.get("identity_id")
        if identity_id and hasattr(Lead, "assigned_to"):
            q = q.filter(Lead.assigned_to == identity_id)
        results = q.order_by(Lead.created_at.desc()).limit(50).all()
    except Exception as exc:
        logger.warning("execution_intelligence lead query failed: %s", exc)
        return []

    actions = []
    for lead in results:
        # Check latest activity
        last_active = None
        try:
            latest = session.query(func.max(ActivityLog.created_at)).filter(
                ActivityLog.lead_id == lead.id
            ).scalar()
            if latest:
                if latest.tzinfo is None:
                    latest = latest.replace(tzinfo=timezone.utc)
                last_active = latest
        except Exception:
            pass

        follow_up_cutoff = _now_utc() - timedelta(hours=72)
        stale = last_active is None or (last_active is not None and last_active < follow_up_cutoff)
        priority = ActionPriority.HIGH if (lead.status in ("inquiry", "in_progress") and stale) else (
            ActionPriority.MEDIUM if stale else ActionPriority.LOW
        )
        if not stale and lead.status == "in_progress":
            priority = ActionPriority.MEDIUM

        desc = f"Lead {lead.code or lead.id}: {lead.customer_name or ''}"
        if stale:
            desc = f"FOLLOW-UP: {desc}"

        actions.append(ActionItem(
            action_id=f"lead-{lead.id}",
            type="lead_follow_up" if stale else "lead_active",
            priority=priority.value,
            title=f"Lead: {lead.customer_name or lead.code or lead.id}"[:200],
            description=desc[:200],
            entity_type="lead",
            entity_id=lead.id,
            due_at=None,
            created_at=lead.created_at.isoformat() if lead.created_at else None,
        ))
    return actions


def _notification_actions(scope: dict) -> list[dict]:
    """Unread notifications as pending attention items."""
    try:
        from app.models import Notification
    except ImportError:
        return []
    session = _db()
    if session is None:
        return []
    try:
        q = session.query(Notification).filter(
            Notification.is_read == False  # noqa: E712
        )
        results = q.order_by(Notification.created_at.desc()).limit(20).all()
    except Exception as exc:
        logger.warning("execution_intelligence notification query failed: %s", exc)
        return []

    actions = []
    for n in results:
        msg = n.message or n.title or f"Notification #{n.id}"
        actions.append(ActionItem(
            action_id=f"notification-{n.id}",
            type="notification_unread",
            priority=ActionPriority.LOW.value,
            title=f"Unread: {msg[:80]}",
            description=msg[:200],
            entity_type="notification",
            entity_id=n.id,
            due_at=None,
            created_at=n.created_at.isoformat() if n.created_at else None,
        ))
    return actions


def _date_to_dt(d):
    """Convert date or datetime to timezone-aware datetime."""
    from datetime import datetime, timezone
    if d is None:
        return None
    if not hasattr(d, "tzinfo"):
        return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    if d.tzinfo is None:
        return d.replace(tzinfo=timezone.utc)
    return d


# ════════════════════════════════════════════════════════════════
# Engine classes
# ════════════════════════════════════════════════════════════════

class ExecutionHealthEngine:
    def assess_health(self, *a, **kw):
        return HealthAssessment(status=HealthStatus.HEALTHY.value)


class TimelineIntelligenceEngine:
    def snapshot(self, *a, **kw):
        return TimelineSnapshot()


class DependencyGraphEngine:
    def get_critical_path(self, *a, **kw):
        return CriticalPath()


class RiskDetectionEngine:
    def assess(self, *a, **kw):
        return RiskAssessment(overall_risk=RiskLevel.LOW.value)
    def assess_risk(self, *a, **kw):
        return RiskAssessment(overall_risk=RiskLevel.LOW.value)


class NextActionEngine:
    def suggest(self, inst=None, service=None, **kw):
        return NextAction()

    def assess(self, *a, **kw):
        return []


class PortfolioIntelligence:
    def summary(self, *a, **kw):
        return PortfolioSummary()


class ExplainabilityLayer:
    def explain(self, *a, **kw):
        return Explanation(text="No explanation available")


class RuntimeService:
    pass


class ExecutionIntelligenceEngine:
    """Execution Intelligence — DB-backed next_actions() and get_execution_insights()."""

    def __init__(self):
        self.health = ExecutionHealthEngine()
        self.timeline = TimelineIntelligenceEngine()
        self.dependency = DependencyGraphEngine()
        self.risk = RiskDetectionEngine()
        self.next_action = NextActionEngine()
        self.portfolio = PortfolioIntelligence()
        self.explainability = ExplainabilityLayer()

    def assess_health(self, inst=None, service=None, **kw) -> HealthAssessment:
        """Assess execution health (backward-compat stub → returns HEALTY)."""
        return self.health.assess_health(inst, service, **kw)

    def predict_completion(self, *a, **kw):
        return CompletionPrediction()

    def assess_risk(self, inst=None, service=None, **kw) -> RiskAssessment:
        """Assess risk (backward-compat stub → returns LOW)."""
        return self.risk.assess_risk(inst, service, **kw)

    def suggest_next_action(self, *a, **kw):
        """Return the single highest-priority action, or a NextAction fallback."""
        actions = self.next_actions(*a, **kw)
        if actions:
            first = actions[0]
            return NextAction(
                action_id=first.get("action_id", ""),
                action_type=first.get("type", ""),
                priority=first.get("priority", "low"),
                description=first.get("title", ""),
                exec_id=str(first.get("entity_id", "")),
                due_at=first.get("due_at"),
                created_at=first.get("created_at"),
            )
        return NextAction(action="no_action")

    def portfolio_summary(self, *a, **kw):
        return self.portfolio.summary(*a, **kw)

    def next_actions(self, *args, **kwargs) -> list[dict]:
        """Return prioritized actionable items from the database.

        Queries Commitments (overdue/in-progress), Tasks (high/urgent/overdue),
        Invoices (unpaid/overdue), Leads (stale follow-ups), and Notifications (unread).

        Accepts optional org_id=, identity_id= to scope results.
        Falls back to flask.g if no scoping provided.
        Legacy callers using next_actions(inst, svc) are supported (scope extracted)
        — the execution-level scope is approximated via tenant_id.

        Returns: list of ActionItem dicts with keys:
            action_id, type, priority, title, description,
            entity_type, entity_id (int), due_at, created_at.
        Sorted by priority (critical > high > medium > low) then due date.
        """
        try:
            return self._collect_actions(*args, **kwargs)
        except Exception as exc:
            logger.error("execution_intelligence.next_actions failed: %s", exc)
            return []

    def _collect_actions(self, *args, **kwargs) -> list[dict]:
        # Resolve scope from kwargs
        org_id = kwargs.get("org_id") or kwargs.get("organization_id")
        identity_id = kwargs.get("identity_id")
        scope = _resolve_scope(org_id, identity_id)

        # If first positional arg looks like an execution instance, extract tenant_id
        if args and hasattr(args[0], "tenant_id"):
            try:
                tid = args[0].tenant_id
                if tid and "org_id" not in scope:
                    scope["org_id"] = tid
            except Exception:
                pass

        all_actions = []
        all_actions.extend(_commitment_actions(scope))
        all_actions.extend(_task_actions(scope))
        all_actions.extend(_invoice_actions(scope))
        all_actions.extend(_lead_actions(scope))
        all_actions.extend(_notification_actions(scope))

        # Sort by priority then due date
        all_actions.sort(key=_due_sort_key)
        return all_actions[:100]

    def get_execution_insights(self, org_id=None, identity_id=None) -> dict:
        """Return counts and risk flags across all actionable entity types.

        Returns: {
            "counts": {"commitments": N, "tasks": N, "invoices": N, "leads": N, "notifications": N},
            "risk_flags": [{"flag": "...", "count": N, "level": "..."}, ...],
            "total_actionable": N,
        }
        """
        scope = _resolve_scope(org_id, identity_id)
        counts = {}
        risk_flags = []

        try:
            actions = self._collect_actions(org_id=org_id, identity_id=identity_id)
            for a in actions:
                et = a.get("entity_type", "unknown")
                counts[et] = counts.get(et, 0) + 1
            # Risk flags
            for et, cnt in counts.items():
                overdue_count = sum(1 for a in actions if a.get("entity_type") == et and "overdue" in a.get("type", ""))
                if overdue_count:
                    risk_flags.append({
                        "flag": f"overdue_{et}s",
                        "count": overdue_count,
                        "level": "critical" if overdue_count > 5 else "high",
                    })
            return {
                "counts": counts,
                "risk_flags": risk_flags,
                "total_actionable": len(actions),
            }
        except Exception as exc:
            logger.error("execution_intelligence.get_execution_insights failed: %s", exc)
            return {"counts": {}, "risk_flags": [], "total_actionable": 0}

    def dependency_graph(self, *a, **kw):
        return {"nodes": [], "edges": [], "critical_path": {}}

    def explain(self, *a, **kw):
        return {}

    def stats(self):
        return {"status": "execution_intelligence active"}

    def timeline(self, *a, **kw):
        # Keep the self.timeline engine attribute working; this method
        # is shadowed by the instance attribute and never called in production.
        return {"snapshot": {}, "prediction": {}}


# ════════════════════════════════════════════════════════════════
# Singleton
# ════════════════════════════════════════════════════════════════

_instance = None


def get_execution_intelligence():
    global _instance
    if _instance is None:
        _instance = ExecutionIntelligenceEngine()
        logger.info("ExecutionIntelligence initialized (DB-backed next_actions)")
    return _instance


def reset_execution_intelligence():
    global _instance
    _instance = None