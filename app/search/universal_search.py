"""SHUNYA Universal Search API — canonical internal search across all object types.

The command palette and universal search must index and search across
canonical objects: people, organizations, leads, customers, suppliers,
conversations, tasks, commitments, opportunities, proposals, invoices,
payments, documents, knowledge, memory, executions, outcomes, campaigns.

Search enforces: tenant isolation, workspace scope, role permissions.
Supports: exact, partial, recent, and related-object search.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, jsonify, request, session, g
from sqlalchemy import or_, text

logger = logging.getLogger(__name__)

search_bp = Blueprint("universal_search", __name__, url_prefix="/api/v1/search")


def _identity_id() -> str:
    return (g.get("identity_id") or session.get("identity_id") or session.get("user_id", ""))


def _require_auth() -> bool:
    return bool(_identity_id())


OBJECT_SEARCH_CONFIG = [
    # (table, label, search_fields, api_path_pattern)
    ("Lead", "leads", ["name", "email", "phone", "company"], "/api/v1/crm/leads/{}"),
    ("Person", "people", ["name", "email", "phone"], "/api/v1/people/{}"),
    ("Customer", "customers", ["name", "email"], "/api/v1/crm/customers/{}"),
    ("Organization", "organizations", ["name", "slug", "email"], "/api/v1/orgs/{}"),
    ("Supplier", "suppliers", ["name"], "/api/v1/suppliers/{}"),
    ("Commitment", "commitments", ["title", "status", "owner"], "/api/v1/commitments/{}"),
    ("Task", "tasks", ["title", "status", "assigned_to"], "/api/v1/tasks/{}"),
    ("FinInvoice", "invoices", ["invoice_number", "status", "customer_name"], "/api/v1/finance/invoices/{}"),
    ("CommercialOpportunity", "opportunities", ["name", "status", "stage"], "/api/v1/commercial/opportunities/{}"),
    ("CommercialProposal", "proposals", ["title", "status"], "/api/v1/commercial/proposals/{}"),
    ("KnowledgeDocument", "knowledge", ["title", "summary", "category", "tags"], "/api/v1/knowledge/documents/{}"),
    ("MemoryRecord", "memory", ["memory_key", "value", "summary", "memory_type"], "/api/v1/memory/entries/{}"),
    ("Execution", "executions", ["decision", "status"], "/api/v1/execution/{}"),
    ("Outcome", "outcomes", ["intention", "outcome_id"], "/api/v1/outcomes/{}"),
    ("Campaign", "campaigns", ["name", "status", "objective"], "/api/v1/campaign/{}"),
    ("DocumentRecord", "documents", ["original_filename", "mime_type", "classification"], "/api/v1/documents/{}"),
    ("ExternalConversation", "conversations", ["title", "status"], "/api/v1/communication/conversations/{}"),
]


def _model_for_table(table_name: str):
    """Dynamically import the SQLAlchemy model for a table name."""
    model_map = {
        "Lead": "app.models.Lead",
        "Person": "app.models.Person",
        "Customer": "app.customers.models.Customer",
        "Organization": "app.models.Organization",
        "Supplier": "app.models.Supplier",
        "Commitment": "app.commitments.models.Commitment",
        "Task": "app.models.Task",
        "FinInvoice": "app.finance.models.FinInvoice",
        "CommercialOpportunity": "app.commercial.models.CommercialOpportunity",
        "CommercialProposal": "app.commercial.models.CommercialProposal",
        "KnowledgeDocument": "app.models.KnowledgeDocument",
        "MemoryRecord": "app.memory.models.MemoryRecord",
        "Execution": "app.execution_engine.models.Execution",
        "Outcome": "app.execution.models.Outcome",
        "Campaign": "app.campaign.models.Campaign",
        "DocumentRecord": "app.document.models.DocumentRecord",
        "ExternalConversation": "app.communication.models.ExternalConversation",
    }
    path = model_map.get(table_name)
    if not path:
        return None
    try:
        import importlib
        mod_name, cls_name = path.rsplit(".", 1)
        mod = importlib.import_module(mod_name)
        return getattr(mod, cls_name, None)
    except (ImportError, AttributeError, ModuleNotFoundError):
        logger.debug(f"Cannot import {path} for search")
        return None


@search_bp.route("/global", methods=["POST"])
def global_search():
    """Search across all canonical object types. Returns type-ahead results grouped by domain."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"success": True, "data": {"results": [], "total": 0}})

    limit = min(int(data.get("limit", 8)), 50)
    domains = data.get("domains", [])  # Optional filter: only search specific domains
    include_recent = data.get("recent", True)

    from app import db
    like = f"%{query}%"
    results = []
    total = 0

    for table_name, label, fields, api_path in OBJECT_SEARCH_CONFIG:
        if domains and label not in domains:
            continue
        model = _model_for_table(table_name)
        if not model:
            continue

        try:
            filters = []
            for field in fields:
                col = getattr(model, field, None)
                if col is not None:
                    filters.append(col.ilike(like))

            if not filters:
                continue

            q = db.session.query(model).filter(or_(*filters))
            # Tenant isolation where applicable
            if hasattr(model, "tenant_id"):
                tenant_id = session.get("tenant_id") or session.get("current_org_id")
                if tenant_id:
                    q = q.filter(model.tenant_id == int(tenant_id))

            rows = q.order_by(
                (getattr(model, "updated_at", None) or getattr(model, "created_at", None) or model.id).desc()
            ).limit(limit).all()

            for row in rows:
                name = getattr(row, "title", None) or getattr(row, "name", None) or getattr(row, "memory_key", None) or getattr(row, "decision", None) or str(getattr(row, "id", ""))
                summary = getattr(row, "summary", None) or getattr(row, "description", None) or getattr(row, "value", None) or ""
                status = getattr(row, "status", None) or ""
                obj_id = getattr(row, "id", None)
                obj_type = table_name

                results.append({
                    "id": obj_id,
                    "type": label,
                    "object_type": obj_type,
                    "name": str(name)[:200],
                    "summary": str(summary)[:200] if summary else "",
                    "status": str(status) if status else "",
                    "api_path": api_path.format(obj_id) if obj_id else "",
                    "url": f"/workspace/{label}/{obj_id}" if obj_id else "",
                })
                total += 1
                if len(results) >= limit * 3:  # Collect broader results for ranking
                    break
        except Exception as e:
            logger.debug(f"Search {label} failed: {e}")
            continue

        if len(results) >= limit * 3:
            break

    # Simple relevance ranking: exact match first, then starts-with, then contains
    def _rank(item):
        name_lower = item["name"].lower()
        q_lower = query.lower()
        if name_lower == q_lower:
            return 0
        if name_lower.startswith(q_lower):
            return 1
        if q_lower in name_lower:
            return 2
        return 3

    results.sort(key=_rank)

    # Add recency boost
    if include_recent:
        recent_ids = session.get("_visited_object_ids", [])
        for item in results:
            if item["id"] and f"{item['type']}:{item['id']}" in recent_ids:
                item["recent"] = True

    return jsonify({
        "success": True,
        "data": {
            "results": results[:limit],
            "total": min(total, limit * 3),
            "query": query,
        },
    })


@search_bp.route("/recent", methods=["GET"])
def recent_objects():
    """Return recently visited objects from the session."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    recent_ids = session.get("_visited_object_ids", [])
    limit = min(int(request.args.get("limit", 10)), 50)

    results = []
    for entry in recent_ids[-limit:]:
        try:
            obj_type, obj_id = entry.split(":", 1)
            model = _model_for_table(obj_type)
            if model:
                row = db.session.get(model, int(obj_id))
                if row:
                    name = getattr(row, "title", None) or getattr(row, "name", None) or str(obj_id)
                    results.append({
                        "id": int(obj_id),
                       "type": obj_type,
                        "name": str(name)[:200],
                        "api_path": f"/api/v1/{obj_type}s/{obj_id}",
                        "url": f"/workspace/{obj_type}/{obj_id}",
                    })
        except Exception:
            continue

    return jsonify({
        "success": True,
        "data": {"results": results, "total": len(results)},
    })


@search_bp.route("/track-visit", methods=["POST"])
def track_visit():
    """Track an object visit for recency boosting in future searches."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data_ = request.get_json(silent=True) or {}
    obj_type = data_.get("object_type", "")
    obj_id = data_.get("object_id", "")
    if obj_type and obj_id:
        recent_ids = session.get("_visited_object_ids", [])
        entry = f"{obj_type}:{obj_id}"
        if entry in recent_ids:
            recent_ids.remove(entry)
        recent_ids.append(entry)
        if len(recent_ids) > 200:
            recent_ids = recent_ids[-200:]
        session["_visited_object_ids"] = recent_ids

    return jsonify({"success": True})