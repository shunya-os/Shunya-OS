"""
SHUNYA — Home Intelligence Surface (ZGC-PR-11E).

The Home Intelligence endpoint synthesizes deterministic and AI signals
into a prioritized, explainable intelligence surface. Designed for the
SHUNYA Home — the first primary section after workspace entry.

Architecture:
  Deterministic signals (no LLM required for basic operation)
    → Priority engine (urgency, importance, relationship impact, risk)
    → AI enhancement (optional, only when useful)
    → Structured intelligence response

Deterministic signal types:
  - NOW: Immediate attention needs (overdue commitments, blocked tasks)
  - CHANGED: Meaningful state changes since last visit
  - COMMITMENTS: Active promises with status
  - TASKS: Operational execution items
  - RELATIONSHIPS: Relationship health signals
  - SHUNYA_WORK: Running/scheduled SHUNYA work
  - ORGANIZATION: Business health synthesis
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from flask import Blueprint, jsonify, g, session, request
from sqlalchemy import func

from app import db

logger = logging.getLogger(__name__)

home_bp = Blueprint("home", __name__, url_prefix="/api/v1/home")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or str(session.get("user_id", ""))


def _ws_type() -> str | None:
    return g.get("workspace_type") or session.get("workspace_type") or None


def _ws_id() -> str | None:
    return g.get("workspace_id") or session.get("workspace_id") or None


# ── Deterministic Signal Gatherers ──────────────────────────────────


def _get_overdue_commitments(ws_id: str | None) -> list[dict]:
    """Find commitments past their due date and still open."""
    try:
        from app.commitments.models import Commitment

        q = Commitment.query.filter(
            Commitment.due_at < datetime.now(timezone.utc),
            Commitment.status.in_(["pending", "in_progress"]),
        )
        if ws_id:
            from app.workspace.models import Workspace, WorkspaceMembership

            # For workspace-scoped commitments we'd filter via membership
            pass

        results = []
        for c in q.order_by(Commitment.due_at.asc()).limit(10).all():
            results.append({
                "id": c.id,
                "title": c.title,
                "owner": c.owner,
                "due_at": c.due_at.isoformat() if c.due_at else None,
                "status": c.status,
                "overdue_by_hours": round((datetime.now(timezone.utc) - c.due_at).total_seconds() / 3600) if c.due_at else None,
                "type": "commitment_overdue",
            })
        return results
    except Exception as e:
        logger.debug("Home: overdue commitments failed: %s", e)
        return []


def _get_upcoming_commitments(ws_id: str | None) -> list[dict]:
    """Find commitments due within the next 24 hours."""
    try:
        from app.commitments.models import Commitment

        now_dt = datetime.now(timezone.utc)
        cutoff = now_dt + timedelta(hours=24)
        q = Commitment.query.filter(
            Commitment.due_at >= now_dt,
            Commitment.due_at <= cutoff,
            Commitment.status.in_(["pending", "in_progress"]),
        )
        results = []
        for c in q.order_by(Commitment.due_at.asc()).limit(10).all():
            due_in_hours = round((c.due_at - now_dt).total_seconds() / 3600) if c.due_at else None
            results.append({
                "id": c.id,
                "title": c.title,
                "owner": c.owner,
                "due_at": c.due_at.isoformat() if c.due_at else None,
                "status": c.status,
                "due_in_hours": due_in_hours,
                "type": "commitment_upcoming",
            })
        return results
    except Exception as e:
        logger.debug("Home: upcoming commitments failed: %s", e)
        return []


def _get_recent_changes(ws_id: str | None, since: str | None = None) -> list[dict]:
    """Find objects that changed recently (deterministic)."""
    try:
        from app.objects.models import ShunyaObject

        q = ShunyaObject.query.filter(ShunyaObject.status == "active")
        if ws_id:
            q = q.filter(ShunyaObject.workspace_id == ws_id)

        # Last 24 hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        # Use updated_at if available; fallback to created_at
        recent = q.order_by(ShunyaObject.updated_at.desc()).limit(15).all()

        results = []
        for obj in recent:
            obj_data = obj.data or {}
            changed = obj.updated_at if obj.updated_at else obj.created_at
            if changed and changed > cutoff:
                results.append({
                    "object_id": obj.object_id,
                    "object_type": obj.object_type,
                    "name": obj.name or obj_data.get("name", "Unnamed"),
                    "status": obj_data.get("status", obj.status),
                    "changed_at": changed.isoformat() if changed else None,
                    "type": "object_updated",
                })
        return results[:10]
    except Exception as e:
        logger.debug("Home: recent changes failed: %s", e)
        return []


def _get_relationship_signals(ws_id: str | None) -> list[dict]:
    """Detect relationship health signals."""
    signals = []
    try:
        # Check relationship models
        from app.founder.routes import founder_bp  # noqa — check existing founder relationships

        # Try founder relationships endpoint pattern
        try:
            from app.models import Person, PersonIdentity
            # Find people with no recent interactions
            now_dt = datetime.now(timezone.utc)
            cutoff_quiet = now_dt - timedelta(days=14)

            # Count people with no recent updates
            quiet_count = Person.query.filter(
                Person.updated_at < cutoff_quiet
            ).count()

            if quiet_count > 0:
                signals.append({
                    "type": "relationship_quiet",
                    "count": quiet_count,
                    "message": f"{quiet_count} relationship{'s' if quiet_count > 1 else ''} {'have' if quiet_count > 1 else 'has'} been quiet for over 2 weeks",
                    "severity": "low",
                    "suggested_action": "Reach out",
                })
        except Exception:
            pass
    except Exception as e:
        logger.debug("Home: relationship signals failed: %s", e)
    return signals


def _get_shunya_work() -> list[dict]:
    """Detect running/scheduled SHUNYA background work."""
    work = []
    try:
        from app.execution_log.models import ExecutionLog

        # Find active executions
        active = ExecutionLog.query.filter(
            ExecutionLog.status == "in_progress"
        ).order_by(ExecutionLog.created_at.desc()).limit(5).all()

        for e in active:
            work.append({
                "id": e.id,
                "label": getattr(e, "label", None) or getattr(e, "action", "Task"),
                "status": "running",
                "progress": getattr(e, "progress", 0.5) or 0.5,
                "started_at": e.created_at.isoformat() if e.created_at else None,
                "type": "shunya_work_running",
            })

        # Find recently completed
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
        completed = ExecutionLog.query.filter(
            ExecutionLog.status == "completed",
            ExecutionLog.created_at >= recent_cutoff,
        ).order_by(ExecutionLog.created_at.desc()).limit(5).all()

        for e in completed:
            work.append({
                "id": e.id,
                "label": getattr(e, "label", None) or getattr(e, "action", "Task"),
                "status": "completed",
                "completed_at": getattr(e, "completed_at", None) or e.created_at.isoformat() if e.created_at else None,
                "type": "shunya_work_completed",
            })
    except Exception as e:
        logger.debug("Home: shunya work failed: %s", e)
    return work


def _get_pending_tasks(ws_id: str | None) -> list[dict]:
    """Find pending tasks."""
    try:
        tasks = []
        try:
            from app.tasks import Task
            q = Task.query.filter(Task.status.in_(["pending", "in_progress"]))
            for t in q.order_by(Task.created_at.desc()).limit(10).all():
                tasks.append({
                    "id": getattr(t, "id", None),
                    "title": getattr(t, "title", None) or getattr(t, "name", "Task"),
                    "status": getattr(t, "status", "pending"),
                    "due_at": getattr(t, "due_at", None),
                    "type": "task_pending",
                })
        except Exception:
            pass

        # Also check ShunyaObject tasks
        try:
            from app.objects.models import ShunyaObject
            obj_tasks = ShunyaObject.query.filter(
                ShunyaObject.object_type == "task",
                ShunyaObject.status == "active",
            )
            if ws_id:
                obj_tasks = obj_tasks.filter(ShunyaObject.workspace_id == ws_id)
            for t in obj_tasks.limit(5).all():
                td = t.data or {}
                tasks.append({
                    "id": t.object_id,
                    "title": t.name or td.get("title", "Task"),
                    "status": td.get("status", "active"),
                    "due_at": td.get("due_at"),
                    "type": "task_pending",
                })
        except Exception:
            pass

        return tasks[:10]
    except Exception as e:
        logger.debug("Home: pending tasks failed: %s", e)
        return []


def _get_awareness_signals() -> list[dict]:
    """Gather awareness signals from the existing engine."""
    signals = []
    try:
        from app.intelligence.awareness import scan
        raw = scan()
        for s in raw[:8]:
            signals.append({
                "type": s.get("type", "awareness"),
                "severity": s.get("severity", "low"),
                "reason": s.get("reason", s.get("message", "")),
                "suggested_action": s.get("suggested_action", ""),
                "entity_name": s.get("entity_name", ""),
                "timestamp": s.get("timestamp", ""),
                "category": "awareness",
            })
    except Exception as e:
        logger.debug("Home: awareness signals failed: %s", e)
    return signals


# ── Priority Engine ────────────────────────────────────────────────


PRIORITY_WEIGHTS = {
    "commitment_overdue": 100,
    "commitment_upcoming": 60,
    "object_updated": 30,
    "relationship_quiet": 25,
    "task_pending": 40,
    "awareness": 35,
    "shunya_work_running": 45,
    "shunya_work_completed": 15,
}


def _priority_score(item: dict) -> int:
    """Compute a priority score for a home intelligence item."""
    base = PRIORITY_WEIGHTS.get(item.get("type", ""), 20)

    # Overdue commitment = higher priority the more overdue
    if item.get("type") == "commitment_overdue":
        hours = item.get("overdue_by_hours", 0) or 0
        base += min(hours, 200)

    # Upcoming commitment = higher priority the sooner
    if item.get("type") == "commitment_upcoming":
        hours = item.get("due_in_hours", 24) or 24
        urgency_bonus = max(0, 24 - hours) * 2
        base += urgency_bonus

    # Running work = moderate priority
    if item.get("type") == "shunya_work_running":
        base += 10

    return base


def _priority_label(score: int) -> str:
    if score >= 120:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 35:
        return "normal"
    return "low"


# ── AI Enhancement (optional, only when available) ─────────────────


def _enrich_with_ai(synthesis: dict, identity_id: str, ws_type: str | None) -> dict:
    """Optionally enrich the synthesis with AI reasoning."""
    try:
        # Only if AI provider is available
        from app.ai import get_provider
        provider = get_provider()
        if not provider:
            return synthesis

        items = synthesis.get("intelligence", [])
        if not items:
            return synthesis

        # Build a concise prompt for summarization
        summary_items = []
        for item in items[:10]:
            summary_items.append(f"- {item.get('type', 'item')}: {item.get('title', item.get('message', item.get('name', '')))}")

        if not summary_items:
            return synthesis

        prompt = (
            "You are SHUNYA's Home Intelligence synthesizer. "
            "Based on these signals from the user's workspace, produce:\n"
            "1. A one-sentence summary of what's happening NOW\n"
            "2. The single most important thing to focus on\n"
            "3. A calm, evidence-backed suggestion\n\n"
            f"Signals:\n{chr(10).join(summary_items)}\n\n"
            "Response format (keep under 150 words total):\n"
            "summary: <1 sentence>\n"
            "focus: <1 sentence>\n"
            "suggestion: <1 sentence>"
        )

        resp = provider.chat([{"role": "user", "content": prompt}], model="free")
        text = resp.get("text", "") or resp.get("content", "") or ""

        # Parse structured response
        synthesis["ai_summary"] = ""
        synthesis["ai_focus"] = ""
        synthesis["ai_suggestion"] = ""

        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("summary:") or line.startswith("summary："):
                synthesis["ai_summary"] = line.split(":", 1)[1].strip()
            elif line.startswith("focus:") or line.startswith("focus："):
                synthesis["ai_focus"] = line.split(":", 1)[1].strip()
            elif line.startswith("suggestion:") or line.startswith("suggestion："):
                synthesis["ai_suggestion"] = line.split(":", 1)[1].strip()

    except Exception as e:
        logger.debug("Home: AI enrichment skipped: %s", e)
    return synthesis


# ── Main Intelligence Endpoint ─────────────────────────────────────


@home_bp.route("/intelligence", methods=["GET"])
def api_home_intelligence():
    """
    Home Intelligence — the primary surface for SHUNYA Home.

    Returns a synthesized, priority-ordered intelligence view of the
    user's current reality, designed to answer the 8 Home questions:

    WHAT IS HAPPENING? WHAT CHANGED? WHAT NEEDS ATTENTION?
    WHAT IS GOING WELL? WHAT IS AT RISK? WHAT CAN I DO NEXT?
    WHAT SHOULD I NOT MISS? WHAT CAN SHUNYA DO FOR ME?

    Query params:
      since: ISO timestamp of last visit (for change detection)
      ws_type: explicit workspace type override
      ws_id: explicit workspace id override
    """
    identity_id = _identity_id()
    ws_type = request.args.get("ws_type") or _ws_type()
    ws_id = request.args.get("ws_id") or _ws_id()
    since = request.args.get("since")

    # ── Gather deterministic signals ──
    intelligence = []

    # A. NOW — immediate attention
    overdue = _get_overdue_commitments(ws_id)
    for item in overdue:
        intelligence.append(item)

    upcoming = _get_upcoming_commitments(ws_id)
    for item in upcoming:
        intelligence.append(item)

    # B. WHAT CHANGED
    changes = _get_recent_changes(ws_id, since)
    for item in changes:
        intelligence.append(item)

    # C. RELATIONSHIPS
    rel_signals = _get_relationship_signals(ws_id)
    for item in rel_signals:
        intelligence.append(item)

    # D. TASKS
    tasks = _get_pending_tasks(ws_id)
    for item in tasks:
        intelligence.append(item)

    # E. AWARENESS
    awareness = _get_awareness_signals()
    for item in awareness:
        intelligence.append(item)

    # F. SHUNYA WORK
    shunya_work = _get_shunya_work()
    for item in shunya_work:
        intelligence.append(item)

    # ── Priority sort ──
    for item in intelligence:
        item["priority_score"] = _priority_score(item)
        item["priority"] = _priority_label(item["priority_score"])

    intelligence.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

    # Separate into priority buckets for progressive disclosure
    critical = [i for i in intelligence if i.get("priority") == "critical"]
    high = [i for i in intelligence if i.get("priority") == "high"]
    normal = [i for i in intelligence if i.get("priority") == "normal"]
    low = [i for i in intelligence if i.get("priority") == "low"]

    # ── Time awareness ──
    now_dt = datetime.now(timezone.utc)
    hour = now_dt.hour
    if hour < 5:
        time_period = "night"
    elif hour < 12:
        time_period = "morning"
    elif hour < 14:
        time_period = "midday"
    elif hour < 17:
        time_period = "afternoon"
    elif hour < 21:
        time_period = "evening"
    else:
        time_period = "night"

    # ── Build synthesis ──
    synthesis = {
        "success": True,
        "data": {
            "intelligence": intelligence,
            "priorities": {
                "critical": len(critical),
                "high": len(high),
                "normal": len(normal),
                "low": len(low),
                "total": len(intelligence),
            },
            "now": {
                "time_period": time_period,
                "immediate_count": len(critical) + len(high),
                "has_immediate": len(critical) + len(high) > 0,
                "summary": _build_now_summary(critical, high),
            },
            "changed": {
                "count": len(changes),
                "items": changes[:5],
            },
            "commitments": {
                "overdue_count": len(overdue),
                "upcoming_count": len(upcoming),
                "items": (overdue + upcoming)[:8],
            },
            "relationships": {
                "count": len(rel_signals),
                "items": rel_signals[:5],
            },
            "tasks": {
                "count": len(tasks),
                "items": tasks[:8],
            },
            "shunya_work": {
                "running": len([w for w in shunya_work if w.get("status") == "running"]),
                "completed_recent": len([w for w in shunya_work if w.get("status") == "completed"]),
                "items": shunya_work[:5],
            },
            "calm": len(critical) == 0 and len(high) == 0,
            "identity_id": identity_id,
            "workspace_type": ws_type,
            "workspace_id": ws_id,
            "synthesized_at": now_dt.isoformat(),
        },
    }

    # ── Optional AI enrichment ──
    synthesis = _enrich_with_ai(synthesis, identity_id, ws_type)

    return jsonify(synthesis)


def _build_now_summary(critical: list, high: list) -> str:
    """Build a concise natural-language summary of what needs attention now."""
    if not critical and not high:
        return "Everything is currently under control. Nothing needs immediate attention."

    parts = []
    if critical:
        c_types = {}
        for item in critical:
            t = item.get("type", "item")
            c_types[t] = c_types.get(t, 0) + 1
        type_labels = {
            "commitment_overdue": "overdue commitment",
            "shunya_work_running": "running task",
            "task_pending": "blocked or urgent task",
        }
        c_parts = []
        for t, count in c_types.items():
            label = type_labels.get(t, t.replace("_", " "))
            c_parts.append(f"{count} {label}{'s' if count > 1 else ''}")
        parts.append(f"{', '.join(c_parts)} need{'s' if len(c_parts) <= 1 else ''} immediate attention")

    if high:
        h_count = len(high)
        parts.append(f"{h_count} item{'s' if h_count > 1 else ''} should be reviewed soon")

    return "You have " + ", and ".join(parts) + "."


# ── Explainability Endpoint ────────────────────────────────────────


@home_bp.route("/explain", methods=["POST"])
def api_home_explain():
    """
    Explain why a specific intelligence item appeared.

    Body:
      type: string — the item's type
      id: string | int — the item's identifier

    Returns grounded evidence for why the item was surfaced.
    """
    data = request.get_json(silent=True) or {}
    item_type = data.get("type", "")
    item_id = data.get("id")

    if not item_type or not item_id:
        return jsonify({"success": False, "error": "type and id are required"}), 400

    explanation = {"type": item_type, "id": item_id, "evidence": [], "confidence": "deterministic"}

    if item_type == "commitment_overdue":
        try:
            from app.commitments.models import Commitment
            c = db.session.get(Commitment, int(item_id))
            if c:
                due_str = c.due_at.strftime("%B %d, %Y at %H:%M") if c.due_at else "unknown"
                explanation["evidence"] = [
                    f"This commitment was due on {due_str}",
                    f"Status is '{c.status}' — it has not been completed",
                    f"The commitment is overdue by approximately {round((datetime.now(timezone.utc) - c.due_at).total_seconds() / 3600)} hours" if c.due_at else "",
                    f"Owner: {c.owner or 'not assigned'}",
                ]
                explanation["confidence"] = "deterministic"
        except Exception as e:
            explanation["evidence"] = [f"Could not load commitment details: {e}"]

    elif item_type == "commitment_upcoming":
        try:
            from app.commitments.models import Commitment
            c = db.session.get(Commitment, int(item_id))
            if c:
                due_str = c.due_at.strftime("%B %d, %Y at %H:%M") if c.due_at else "unknown"
                explanation["evidence"] = [
                    f"This commitment is due on {due_str}",
                    f"It has not been started or completed yet (status: '{c.status}')",
                    f"It will become due in approximately {round((c.due_at - datetime.now(timezone.utc)).total_seconds() / 3600)} hours" if c.due_at else "",
                ]
                explanation["confidence"] = "deterministic"
        except Exception as e:
            explanation["evidence"] = [f"Could not load commitment details: {e}"]

    elif item_type == "object_updated":
        try:
            from app.objects.models import ShunyaObject
            obj = ShunyaObject.query.filter_by(object_id=item_id).first()
            if obj:
                explanation["evidence"] = [
                    f"Object '{obj.name}' (type: {obj.object_type}) was recently created or modified",
                    f"Status: {obj.status}",
                    f"Last changed: {obj.updated_at.strftime('%B %d, %Y at %H:%M') if obj.updated_at else 'unknown'}",
                ]
                explanation["confidence"] = "deterministic"
        except Exception as e:
            explanation["evidence"] = [f"Could not load object details: {e}"]

    elif item_type == "relationship_quiet":
        explanation["evidence"] = [
            f"{item_id} relationships have had no recorded interaction in over 14 days",
            "SHUNYA tracks relationship recency as a signal of relationship health",
            "Regular check-ins help maintain business relationships",
        ]
        explanation["confidence"] = "inference"

    elif item_type in ("shunya_work_running", "shunya_work_completed"):
        explanation["evidence"] = [
            "SHUNYA is processing or has completed background work in this workspace",
            "The status field shows whether the work is still running or finished",
        ]
        explanation["confidence"] = "deterministic"

    elif item_type == "task_pending":
        explanation["evidence"] = [
            "This task has not been marked as complete",
            "Its status indicates work is still pending",
            "Tasks that remain open beyond their expected duration are surfaced here",
        ]
        explanation["confidence"] = "deterministic"

    else:
        explanation["evidence"] = [
            f"This item was surfaced by the SHUNYA Home intelligence engine (type: {item_type})",
            "It was prioritized based on urgency, importance, and relationship impact",
        ]
        explanation["confidence"] = "inference"

    return jsonify({"success": True, "data": explanation})


# ── Feedback Endpoint ──────────────────────────────────────────────


@home_bp.route("/feedback", methods=["POST"])
def api_home_feedback():
    """
    Record user feedback on a Home intelligence item.

    Body:
      type: string — item type
      id: string | int — item identifier
      feedback: "useful" | "not_useful" | "not_now" | "dont_suggest_again"
    """
    data = request.get_json(silent=True) or {}
    feedback = data.get("feedback", "")
    item_type = data.get("type", "")
    item_id = data.get("id")

    if not feedback or not item_type:
        return jsonify({"success": False, "error": "feedback and type are required"}), 400

    try:
        from app.execution_log.models import ExecutionLog
        log = ExecutionLog(
            action=f"home_feedback:{feedback}",
            label=f"Home feedback on {item_type}:{item_id}",
            status="completed",
            data={"feedback": feedback, "item_type": item_type, "item_id": item_id},
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({"success": True, "data": {"recorded": True}})