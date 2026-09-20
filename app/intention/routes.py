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
from app.attention.service import create_attention_item, list_active

intention_bp = Blueprint("intention", __name__, url_prefix="/api/v1/intention")


def _intention_org_id():
    """Resolve the current canonical org id for scoped reads, or None.

    None means "no ownership context": callers must withhold tenant-scoped
    signals (fail closed) rather than read across all tenants. Never returns a
    synthetic id.
    """
    try:
        from app.authz.decorators import _resolve_org_id
        org_id = _resolve_org_id()
        return int(org_id) if org_id else None
    except Exception:
        return None


def _resolve_identity_id() -> str | None:
    """Resolve the current identity id from session, g, or header."""
    from flask import session, g, request
    return (
        session.get("identity_id")
        or session.get("user_id")
        or getattr(g, "identity_id", None)
        or request.headers.get("X-Identity-Id")
    )


def _maybe_create_attention_from_signals():
    """Scan signals and create attention items for active ones."""
    from app.attention.service import detect_attention_from_signals
    org_id = _intention_org_id()
    identity_id = _resolve_identity_id()
    if org_id and identity_id:
        try:
            detect_attention_from_signals(
                identity_id=identity_id,
                organization_id=org_id,
            )
        except Exception:
            pass  # Non-critical — don't break signal collection


def _persist_attention_from_signals(signals: list[dict]):
    """Create attention items for high-priority signals that don't already have one."""
    org_id = _intention_org_id()
    identity_id = _resolve_identity_id()
    if not org_id or not identity_id:
        return
    from app import db
    from app.attention.service import create_attention_item
    from app.attention.models import AttentionState

    for sig in signals:
        if sig.get("priority", 0) < 3:
            continue  # Only persist priority 3+ signals

        # Dedup: skip if an active item already exists for this signal type
        existing = list_active(
            organization_id=org_id,
            identity_id=identity_id,
            limit=100,
        )
        if any(e.related_object_type == sig.get("object_type") and e.state == AttentionState.ACTIVE.value for e in existing):
            continue

        try:
            create_attention_item(
                identity_id=identity_id,
                organization_id=org_id,
                source="intention.engine",
                related_object_type=sig.get("object_type"),
                related_object_id=sig.get("object_name"),
                reason=sig.get("label", ""),
                priority=sig.get("priority", 3),
                provenance={
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                    "signal_type": sig.get("type"),
                    "method": "_collect_signals",
                },
            )
        except Exception:
            pass  # Non-critical


def _collect_signals():
    """Collect and rank contextual signals from the database."""
    from app import db
    from core.object_service import get_object_service

    signals = []

    # 0. Persist signals as attention items for active signals
    _maybe_create_attention_from_signals()

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

    # Canonical organization scope — resolved from the authenticated identity.
    # 0 means "no ownership context": tenant-scoped signals are withheld
    # (fail closed) rather than read across all tenants.
    org_id = _intention_org_id()

    # 2. Pending proposals (canonical sh_objects, scoped to the caller's org)
    draft_proposals = 0
    prop_name = None
    if org_id:
        rows = db.session.execute(
            text("SELECT COUNT(*) FROM sh_objects WHERE object_type = 'Proposal' AND status = 'draft' AND is_deleted = false AND organization_id = :org_id"),
            {"org_id": org_id},
        ).fetchone()
        draft_proposals = rows[0] if rows else 0
        if draft_proposals > 0:
            prop = db.session.execute(
                text("SELECT name FROM sh_objects WHERE object_type = 'Proposal' AND status = 'draft' AND is_deleted = false AND organization_id = :org_id ORDER BY updated_at DESC LIMIT 1"),
                {"org_id": org_id},
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

    # 3. Recent activity (last 24h) — canonical sh_objects, scoped to the org
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_count = 0
    recent = None
    if org_id:
        rows = db.session.execute(
            text("SELECT COUNT(*) FROM sh_objects WHERE created_at >= :since AND is_deleted = false AND organization_id = :org_id"),
            {"since": since, "org_id": org_id},
        ).fetchone()
        recent_count = rows[0] if rows else 0
        if recent_count > 0:
            recent = db.session.execute(
                text("SELECT name, object_type FROM sh_objects WHERE created_at >= :since AND is_deleted = false AND organization_id = :org_id ORDER BY updated_at DESC LIMIT 1"),
                {"since": since, "org_id": org_id},
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

    # 5. Most recent object (canonical sh_objects, scoped to the caller's org)
    recent_obj = None
    if org_id:
        recent_obj = db.session.execute(
            text("SELECT name, object_type FROM sh_objects WHERE object_type != 'Proposal' AND is_deleted = false AND organization_id = :org_id ORDER BY updated_at DESC LIMIT 1"),
            {"org_id": org_id},
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

    # Persist attention items for high-priority signals
    _persist_attention_from_signals(signals)

    return signals


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