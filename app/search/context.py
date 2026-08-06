"""
Company Data Context Builder — queries sh_objects for a user's identity
and returns a rich plain-text summary for AI system prompts.

Used by:
  - POST /api/v1/ai/analyze (company analysis endpoint)
  - Any future AI feature that needs user business context
"""
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── Object type -> display label ──
TYPE_LABELS = {
    "customer": "Customer",
    "contact": "Contact",
    "invoice": "Invoice",
    "proposal": "Proposal",
    "task": "Task",
    "project": "Project",
    "employee": "Employee",
    "document": "Document",
    "note": "Note",
    "conversation": "Conversation",
}


def build_context(identity_id: str) -> str:
    """Query sh_objects for ALL objects owned by the identity.

    Returns a plain-text context string like:
        Your business data:
        - 135 invoices: $12,600 paid, 3 overdue
        - 80 proposals: $127K pipeline
        - 82 contacts
        - 135 tasks: 3 completed, 120 active

    Recent activity:
        - INV-NovaWorks: $3,200 overdue
        - Proposal for GlobalTech: sent
    """
    if not identity_id:
        return "No identity ID provided — no business data available."

    try:
        from app import db
        from sqlalchemy import text

        # 1. Fetch ALL objects for this identity
        rows = db.session.execute(
            text(
                """
                SELECT object_id, object_type, name, status, data, created_at, updated_at
                FROM sh_objects
                WHERE created_by = :identity_id
                  AND is_deleted = false
                ORDER BY updated_at DESC
                """
            ),
            {"identity_id": identity_id},
        ).fetchall()
    except Exception as e:
        logger.warning(f"build_context query failed: {e}")
        return "Unable to query business data — database error."

    if not rows:
        return "No business data found for this account."

    # 2. Classify by object_type
    by_type: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        obj = {
            "object_id": row.object_id,
            "object_type": row.object_type,
            "name": row.name or "",
            "status": row.status or "active",
            "data": row.data or {},
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        by_type[row.object_type].append(obj)

    # 3. Build summary lines
    lines = ["Your business data:"]

    # Invoice summary
    invoices = by_type.get("invoice", [])
    if invoices:
        total_paid = 0.0
        total_overdue = 0.0
        overdue_names = []
        recent_invoices = []
        for inv in invoices:
            try:
                amount = float(inv["data"].get("grand_total") or inv["data"].get("amount") or 0)
            except (ValueError, TypeError):
                amount = 0.0
            status = (inv["data"].get("payment_status") or inv["data"].get("status") or "draft").lower()

            if status == "paid":
                total_paid += amount
            elif status in ("overdue", "past_due"):
                total_overdue += amount
                overdue_names.append(inv.get("name") or f"INV-{inv['object_id'][:8]}")

        inv_line = f"- {len(invoices)} invoice"
        if len(invoices) != 1:
            inv_line += "s"
        inv_line += ": "
        parts = []
        if total_paid > 0:
            parts.append(f"${total_paid:,.2f} paid")
        if total_overdue > 0:
            parts.append(f"${total_overdue:,.2f} overdue")
            recent_invoices = overdue_names[:5]
        remaining = len(invoices) - (1 if total_paid > 0 else 0) - (1 if total_overdue > 0 else 0)
        if remaining > 0:
            parts.append(f"{remaining} {'other' if total_paid > 0 or total_overdue > 0 else ''} pending/draft")
        if parts:
            inv_line += ", ".join(parts)
        else:
            inv_line += f"{len(invoices)} total"
        lines.append(inv_line)

    # Proposal summary
    proposals = by_type.get("proposal", [])
    if proposals:
        total_pipeline = 0.0
        sent_count = 0
        recent_proposals = []
        for prop in proposals:
            try:
                amount = float(prop["data"].get("amount") or 0)
            except (ValueError, TypeError):
                amount = 0.0
            status = (prop["data"].get("status") or prop.get("status") or "draft").lower()
            if status in ("sent", "pending", "under_review"):
                total_pipeline += amount
                sent_count += 1
                recent_proposals.append(prop.get("name") or prop["object_id"][:12])

        prop_line = f"- {len(proposals)} proposal"
        if len(proposals) != 1:
            prop_line += "s"
        if total_pipeline > 0:
            prop_line += f": ${total_pipeline:,.2f} pipeline"
        lines.append(prop_line)

    # Contacts summary
    contacts = by_type.get("contact", [])
    if contacts:
        contacts_line = f"- {len(contacts)} contact"
        if len(contacts) != 1:
            contacts_line += "s"
        lines.append(contacts_line)

    # Customers summary
    customers = by_type.get("customer", [])
    if customers:
        lines.append(f"- {len(customers)} customer{'s' if len(customers) != 1 else ''}")

    # Task summary
    tasks = by_type.get("task", [])
    if tasks:
        completed = sum(1 for t in tasks if (t["data"].get("status") or t.get("status") or "").lower() == "completed")
        active = sum(1 for t in tasks if (t["data"].get("status") or t.get("status") or "").lower() in ("active", "in_progress", "pending"))
        task_line = f"- {len(tasks)} task"
        if len(tasks) != 1:
            task_line += "s"
        task_parts = []
        if completed > 0:
            task_parts.append(f"{completed} completed")
        if active > 0:
            task_parts.append(f"{active} active")
        if task_parts:
            task_line += ": " + ", ".join(task_parts)
        lines.append(task_line)

    # Projects summary
    projects = by_type.get("project", [])
    if projects:
        lines.append(f"- {len(projects)} project{'s' if len(projects) != 1 else ''}")

    # Other types (compact)
    other_types = [t for t in ("employee", "document", "note", "conversation") if t in by_type]
    for t in other_types:
        objs = by_type[t]
        label = TYPE_LABELS.get(t, t)
        lines.append(f"- {len(objs)} {label.lower()}{'s' if len(objs) != 1 else ''}")

    # 4. Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent = [o for o in rows if o.updated_at and o.updated_at >= week_ago]
    if recent:
        lines.append("")
        lines.append("Recent activity:")
        for obj in recent[:5]:
            t = obj.object_type
            label = TYPE_LABELS.get(t, t)
            name = obj.name or obj.object_id[:12]
            status = obj.status or ""
            detail = ""

            if t == "invoice":
                try:
                    amt = float(obj.data.get("grand_total") or obj.data.get("amount") or 0)
                    detail = f" ${amt:,.0f}"
                except (ValueError, TypeError):
                    pass
                if obj.data.get("payment_status"):
                    detail += f" ({obj.data['payment_status']})"
            elif t == "proposal":
                try:
                    amt = float(obj.data.get("amount") or 0)
                    detail = f" ${amt:,.0f}"
                except (ValueError, TypeError):
                    pass
                if obj.data.get("status"):
                    detail += f" ({obj.data['status']})"
            elif t == "task":
                detail = f" ({obj.data.get('status', status)})"

            lines.append(f"  - {label} — {name}{detail}")

    return "\n".join(lines)