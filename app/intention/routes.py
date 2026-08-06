"""Intention Engine — transforms runtime signals into ranked human intentions.

Current (Phase 1): Raw database signals are collected, ranked by fixed priority,
and surfaced as recommendations. This establishes the canonical architecture.

Evolved (Phase 2, conceptual): Raw signals (overdue invoices, draft proposals,
recent activity) shall first be transformed into meaningful units of work
before prioritization. A recommendation shall describe what the user should
accomplish — "Send payment reminder to Acme Corp" — not what the database
contains — "1 overdue invoice exists."

Priority shall ultimately become context-sensitive rather than fixed:
commitments, calendar events, execution state, urgency, importance, and
confidence shall influence ranking dynamically. The engine shall evolve
from ranking database signals to ranking human intentions.

Architecture pattern:
  _collect_signals()       → raw database queries (current)
  _transform_to_intents()  → signals become work units (future)
  _rank_by_context()       → dynamic, context-sensitive priority (future)
"""
from flask import Blueprint, jsonify
from sqlalchemy import text
from datetime import datetime, timezone, timedelta

intention_bp = Blueprint("intention", __name__, url_prefix="/api/v1/intention")


def _collect_signals():
    """Collect and rank contextual signals from the database."""
    from app import db

    signals = []

    # 1. Overdue invoices
    rows = db.session.execute(
        text("SELECT COUNT(*), COALESCE(SUM(total_amount), 0) FROM fin_invoices WHERE status = 'sent' AND due_date < NOW()")
    ).fetchone()
    overdue_count = rows[0] if rows else 0
    overdue_amount = rows[1] if rows else 0
    if overdue_count > 0:
        # Fetch the most overdue invoice name
        inv = db.session.execute(
            text("SELECT name FROM fin_invoices WHERE status = 'sent' AND due_date < NOW() ORDER BY due_date ASC LIMIT 1")
        ).fetchone()
        inv_name = inv[0] if inv else None
        signals.append({
            "type": "overdue_invoice",
            "priority": 5,
            "count": overdue_count,
            "amount": float(overdue_amount),
            "object_name": inv_name,
            "object_type": "Invoice",
            "label": f"{overdue_count} overdue invoice(s)",
            "detail": f"₹{overdue_amount:,.0f} total overdue" if overdue_amount else "",
        })

    # 2. Pending proposals
    rows = db.session.execute(
        text("SELECT COUNT(*) FROM founder_objects WHERE object_type = 'Proposal' AND status = 'draft'")
    ).fetchone()
    draft_proposals = rows[0] if rows else 0
    if draft_proposals > 0:
        prop = db.session.execute(
            text("SELECT name FROM founder_objects WHERE object_type = 'Proposal' AND status = 'draft' ORDER BY created_at DESC LIMIT 1")
        ).fetchone()
        prop_name = prop[0] if prop else None
        signals.append({
            "type": "pending_proposal",
            "priority": 4,
            "count": draft_proposals,
            "object_name": prop_name,
            "object_type": "Proposal",
            "label": f"{draft_proposals} draft proposal(s)",
            "detail": "Awaiting completion",
        })

    # 3. Recent activity (last 24h)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    rows = db.session.execute(
        text("SELECT COUNT(*) FROM founder_objects WHERE created_at >= :since"),
        {"since": since},
    ).fetchone()
    recent_count = rows[0] if rows else 0
    if recent_count > 0:
        recent = db.session.execute(
            text("SELECT name, object_type FROM founder_objects WHERE created_at >= :since ORDER BY created_at DESC LIMIT 1"),
            {"since": since},
        ).fetchone()
        signals.append({
            "type": "recent_activity",
            "priority": 3,
            "count": recent_count,
            "object_name": recent[0] if recent else None,
            "object_type": recent[1] if recent else "Object",
            "label": f"{recent_count} new item(s) in last 24h",
            "detail": f"Most recent: {recent[0]}" if recent else "",
        })

    # 4. Unfinished background jobs
    from app.jobs.manager import count_active_jobs
    active_jobs = count_active_jobs()
    if active_jobs > 0:
        signals.append({
            "type": "background_jobs",
            "priority": 2,
            "count": active_jobs,
            "object_name": None,
            "object_type": "Job",
            "label": f"{active_jobs} active job(s)",
            "detail": "Running in background",
        })

    # 5. Most recent object
    recent_obj = db.session.execute(
        text("SELECT name, object_type FROM founder_objects WHERE object_type != 'Proposal' ORDER BY created_at DESC LIMIT 1")
    ).fetchone()
    if recent_obj:
        signals.append({
            "type": "recent_object",
            "priority": 1,
            "count": 1,
            "object_name": recent_obj[0],
            "object_type": recent_obj[1],
            "label": f"Last worked on: {recent_obj[0]}",
            "detail": "",
        })

    # Sort by priority (highest first)
    signals.sort(key=lambda s: -s["priority"])
    return signals


@intention_bp.route("", methods=["GET"])
def api_intention():
    """Get the highest-confidence starting point recommendation."""
    signals = _collect_signals()
    top = signals[0] if signals else None

    if not top:
        return jsonify({
            "success": True,
            "recommendation": None,
            "signals": [],
            "explanation": "No signals detected. Everything appears up to date.",
        })

    return jsonify({
        "success": True,
        "recommendation": {
            "object_name": top["object_name"],
            "object_type": top["object_type"],
            "priority": top["priority"],
            "label": top["label"],
            "detail": top["detail"],
        },
        "signals": signals,
        "explanation": f"Highest priority: {top['label']}. {top['detail']}",
    })