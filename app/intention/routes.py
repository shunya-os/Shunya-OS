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
from app.authz.decorators import require_permission

intention_bp = Blueprint("intention", __name__, url_prefix="/api/v1/intention")


def _collect_signals():
    """Collect and rank contextual signals from the database."""
    from app import db
    from core.object_service import get_object_service

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
    # Canonical-first read (sh_objects via ObjectService), legacy fallback
    draft_proposals = 0
    prop_name = None
    try:
        _org = _intention_org_id()
        proposals = get_object_service().get_by_type("Proposal", _org, limit=50) if _org else []
        if proposals:
            drafts = [p for p in proposals if p.get("status") == "draft"]
            draft_proposals = len(drafts)
            if drafts:
                prop_name = drafts[0].get("name")
    except Exception:
        draft_proposals = 0
    if draft_proposals == 0:
        rows = db.session.execute(
            text("SELECT COUNT(*) FROM founder_objects WHERE object_type = 'Proposal' AND status = 'draft'")
        ).fetchone()
        draft_proposals = rows[0] if rows else 0
        if draft_proposals > 0:
            prop = db.session.execute(
                text("SELECT name FROM founder_objects WHERE object_type = 'Proposal' AND status = 'draft' ORDER BY created_at DESC LIMIT 1")
            ).fetchone()
            prop_name = prop[0] if prop else None
    if draft_proposals > 0:
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
    # Canonical-first read (sh_objects via ObjectService), legacy fallback
    recent_count = 0
    recent = None
    try:
        _org = _intention_org_id()
        canonical_recent = _recent_canonical_objects(_org)
        if canonical_recent:
            recent_count = len(canonical_recent)
            if recent_count > 0:
                recent = canonical_recent[0]
    except Exception:
        recent_count = 0
    if recent_count == 0:
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
    if recent_count > 0:
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
    # Canonical-first read (sh_objects via ObjectService), legacy fallback
    recent_obj = None
    try:
        _org = _intention_org_id()
        canonical_recent_obj = _recent_canonical_objects(_org, exclude_proposals=True)
        if canonical_recent_obj:
            recent_obj = canonical_recent_obj[0]
    except Exception:
        recent_obj = None
    if recent_obj is None:
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


def _intention_org_id() -> int:
    """Resolve the current org id for scoped canonical reads (0 if unknown)."""
    try:
        from app.authz.decorators import _resolve_org_id
        return int(_resolve_org_id() or 0)
    except Exception:
        return 0


def _recent_canonical_objects(org_id: int, exclude_proposals: bool = False) -> list:
    """Recent active objects from sh_objects (timezone-aware), empty if none.

    Canonical read used first by _collect_signals; callers fall back to the
    legacy founder_objects raw SQL when this returns nothing (compat boundary).
    """
    from datetime import datetime as _dt
    from core.object_service import get_object_service
    if not org_id or org_id < 1:
        return []
    since = _dt.now(timezone.utc) - timedelta(hours=24)
    results = []
    for obj_type in ("Document", "Note", "Proposal", "Lead", "Invoice", "Contract", "Task"):
        try:
            rows = get_object_service().get_by_type(obj_type, org_id, limit=20)
        except Exception:
            rows = []
        for r in rows:
            created_raw = r.get("created_at")
            if isinstance(created_raw, str):
                try:
                    created_raw = _dt.fromisoformat(created_raw)
                except Exception:
                    continue
            if not created_raw:
                continue
            if exclude_proposals and (r.get("object_type") or "").lower() == "proposal":
                continue
            results.append((r.get("name") or "", r.get("object_type") or "Object", created_raw))
    results.sort(key=lambda t: t[2], reverse=True)
    return results[:1] if exclude_proposals else results[:50]


@intention_bp.route("", methods=["GET"])
@require_permission("ai.use")
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