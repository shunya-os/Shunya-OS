"""SHUNYA Content Studio API — Content Generation, Lifecycle, and Media Pipeline.

Wires Content Studio 4.0 frontend to canonical persistence with full
ACTIVE / ARCHIVED / TRASHED lifecycle management.
"""
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, session, g

logger = logging.getLogger(__name__)

content_bp = Blueprint("content_studio", __name__, url_prefix="/api/v1/content")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "")


def _require_auth() -> bool:
    return bool(_identity_id())


def _tenant_id() -> int | None:
    """Resolve tenant from canonical session — returns None if no org context."""
    from app.authz.decorators import _resolve_org_id
    org_id = _resolve_org_id()
    if org_id:
        return org_id
    tid = session.get("tenant_id")
    return int(tid) if tid else None


def _organization_id() -> int | None:
    """Resolve the caller's canonical organization ID."""
    return (
        session.get("current_org_id")
        or g.get("current_org_id")
        or session.get("tenant_id")
        or None
    )


def _workspace_id() -> str:
    """Resolve the current workspace ID from session or flask.g."""
    return (
        session.get("workspace_id")
        or g.get("workspace_id")
        or ""
    )


def _derive_lifecycle_state(item) -> str:
    """Derive the lifecycle state from model fields.

    Precedence: lifecycle_status overrides legacy is_deleted/status.
    """
    if item.lifecycle_status == "trashed":
        return "trashed"
    if item.lifecycle_status == "archived":
        return "archived"
    if item.lifecycle_status == "active":
        return "active"
    # Fallback to legacy fields
    if item.is_deleted:
        return "trashed"
    return "archived" if item.status == "archived" else "active"


LIFECYCLE_TRANSITIONS = {
    "archive": ({"active"}, "archived"),
    "trash": ({"active", "archived"}, "trashed"),
    "restore": ({"archived", "trashed"}, "active"),
}


from app.content_studio.languages import (
    AUTO,
    DEFAULT_LANGUAGE,
    language_prompt,
    normalize as normalize_language,
    registry as language_registry,
    resolve_output_language,
)


@content_bp.route("/languages", methods=["GET"])
def api_languages():
    """Canonical output-language registry — the single source of truth for the UI.

    Deliberately public (no auth): it is static capability metadata and the
    selector must render before any generation attempt.
    """
    return jsonify({
        "success": True,
        "data": language_registry(),
        "default": DEFAULT_LANGUAGE,
    })


@content_bp.route("/generate", methods=["POST"])
def api_generate():
    """Generate content via AI provider chain."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"success": False, "error": "prompt is required"}), 400

    content_type = data.get("content_type", "blog_post")
    tone = data.get("tone", "professional")
    platform = data.get("platform")
    target_audience = data.get("target_audience")
    word_count = int(data.get("word_count", 300))
    additional_instructions = data.get("additional_instructions", "")

    # -- Output language (12): validated against the canonical registry. --
    # An unsupported value is REJECTED -- an arbitrary language string is never
    # passed through to the model.
    raw_language = data.get("output_language", AUTO)
    normalized = normalize_language(raw_language)
    if normalized is None:
        return jsonify({
            "success": False,
            "code": "invalid_output_language",
            "error": f"Unsupported output_language: {raw_language!r}",
        }), 400
    lang_code, lang_source = resolve_output_language(
        normalized, f"{prompt} {additional_instructions}"
    )

    # The language is applied as a generation CONSTRAINT, not a UI-only label.
    instr = (additional_instructions or "").strip()
    language_constraint = language_prompt(lang_code)
    combined = f"{language_constraint}\n\n{instr}".strip() if instr else language_constraint

    from app.integration.service import generate_content
    result = generate_content(
        prompt=prompt,
        content_type=content_type,
        tone=tone,
        platform=platform,
        target_audience=target_audience,
        word_count=word_count,
        additional_instructions=combined,
        output_language=lang_code,
    )
    result["output_language"] = lang_code
    result["output_language_source"] = lang_source

    # Persist the generation with lifecycle_status='active'
    if result.get("success"):
        try:
            from app.integration.models import ContentGeneration
            from app import db
            now = datetime.utcnow()
            cg = ContentGeneration(
                identity_id=_identity_id(),
                organization_id=_organization_id(),
                workspace_id=_workspace_id(),
                content_type=content_type,
                platform=platform or "",
                prompt=prompt,
                generated_content=result.get("content", ""),
                tone=tone,
                target_audience=target_audience,
                word_count=word_count,
                ai_model=result.get("model") or "provider_chain",
                lifecycle_status="active",
                provider=result.get("provider"),
                generation_cost=result.get("cost"),
                generation_metadata=result.get("generation_metadata"),
                provenance=result.get("provenance"),
                source="generation",
                created_at=now,
                updated_at=now,
            )
            db.session.add(cg)
            db.session.commit()
            result["id"] = cg.id
            result["lifecycle_status"] = cg.lifecycle_status
        except Exception as e:
            logger.warning("Content persistence error: %s", e)

    return jsonify(result)


@content_bp.route("/history", methods=["GET"])
def api_history():
    """List recent content generations."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    limit = min(int(request.args.get("limit", 50)), 100)
    content_type = request.args.get("content_type")

    try:
        from app.integration.models import ContentGeneration
        from app import db

        q = ContentGeneration.query.filter_by(identity_id=_identity_id())
        if content_type:
            q = q.filter_by(content_type=content_type)
        items = q.order_by(ContentGeneration.created_at.desc()).limit(limit).all()

        return jsonify({
            "success": True,
            "data": [item.to_dict() for item in items],
            "total": len(items),
        })
    except Exception as e:
        # TRUTHFUL FAILURE -- never mask a real storage error as an empty
        # library. An empty list and an unreadable list must be
        # distinguishable, or the user is silently told their content does
        # not exist.
        logger.error("Content history error: %s", e)
        return jsonify({"success": False,
                        "error": "Content history could not be loaded"}), 500


@content_bp.route("/history/<int:item_id>", methods=["GET"])
def api_get_item(item_id: int):
    """Get a specific content generation."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app import db
        from app.integration.models import ContentGeneration
        item = db.session.get(ContentGeneration, item_id)
        if not item or item.identity_id != _identity_id():
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "data": item.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@content_bp.route("/history/<int:item_id>/favorite", methods=["POST"])
def api_toggle_favorite(item_id: int):
    """Toggle favorite status."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.integration.models import ContentGeneration
        from app import db
        item = db.session.get(ContentGeneration, item_id)
        if not item or item.identity_id != _identity_id():
            return jsonify({"success": False, "error": "Not found"}), 404
        item.is_favorited = not item.is_favorited
        db.session.commit()
        return jsonify({"success": True, "is_favorited": item.is_favorited})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@content_bp.route("/history/<int:item_id>", methods=["DELETE"])
def api_delete_item(item_id: int):
    """Delete a content generation."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.integration.models import ContentGeneration
        from app import db
        item = db.session.get(ContentGeneration, item_id)
        if not item or item.identity_id != _identity_id():
            return jsonify({"success": False, "error": "Not found"}), 404
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@content_bp.route("/history/<int:item_id>/lifecycle", methods=["POST"])
def api_lifecycle(item_id: int):
    """Apply a lifecycle action to a content generation.

    State machine (same as ObjectService lifecycle):
      ACTIVE    -> archiv -> ARCHIVED,  trash -> TRASHED
      ARCHIVED  -> restore -> ACTIVE,    trash -> TRASHED
      TRASHED   -> restore -> ACTIVE
      any       -> permanent_delete -> (removed from DB)
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    if action not in ("archive", "restore", "trash", "recover", "permanent_delete"):
        return jsonify({"error": f"Unknown lifecycle action: {action}",
                        "valid": ["archive","restore","trash","recover","permanent_delete"],
                        "success": False}), 400
    try:
        from app.integration.models import ContentGeneration
        from app import db
        actor = _identity_id()
        item = db.session.get(ContentGeneration, item_id)
        if not item or item.identity_id != actor:
            return jsonify({"success": False, "error": "Not found"}), 404

        current = _derive_lifecycle_state(item)

        # Explicit transition table. Each entry: (allowed_from, apply_fn).
        # Returning False from apply_fn means "not a valid transition".
        def _do_archive(i):
            i.lifecycle_status = "archived"
            i.archived_at = datetime.utcnow()
            i.archived_by = actor
            return True

        def _do_restore(i):
            i.lifecycle_status = "active"
            i.status = "active"
            i.is_deleted = False
            i.restored_at = datetime.utcnow()
            i.restored_by = actor
            return True

        def _do_trash(i):
            i.lifecycle_status = "trashed"
            i.is_deleted = True
            i.deleted_at = datetime.utcnow()
            i.deleted_by = actor
            return True

        def _do_recover(i):
            i.lifecycle_status = "active"
            i.is_deleted = False
            i.status = "active"
            i.restored_at = datetime.utcnow()
            i.restored_by = actor
            return True

        TRANSITIONS = {
            "archive": ({"active"}, _do_archive),
            "restore": ({"archived"}, _do_restore),
            "trash": ({"active", "archived"}, _do_trash),
            "recover": ({"trashed"}, _do_recover),
        }

        if action == "permanent_delete":
            if current != "trashed":
                return jsonify({
                    "success": False,
                    "error": "Object must be in trash before it can be "
                             "permanently deleted",
                    "state": current,
                }), 409
            db.session.delete(item)
            db.session.commit()
            return jsonify({"success": True, "action": action,
                            "state": "deleted"})

        allowed_from, apply_fn = TRANSITIONS[action]
        if current not in allowed_from:
            return jsonify({
                "success": False,
                "error": f"Cannot {action} an object in state '{current}'",
                "state": current,
                "allowed_from": sorted(allowed_from),
            }), 409
        if not apply_fn(item):
            return jsonify({"success": False,
                            "error": f"Invalid transition: {action}"}), 409
        db.session.commit()

        updated = db.session.get(ContentGeneration, item_id)
        if updated is None:  # pragma: no cover -- defensive
            return jsonify({"success": False,
                            "error": "Object disappeared during operation"}), 500
        return jsonify({"success": True, "action": action,
                        "state": _derive_lifecycle_state(updated),
                        "lifecycle_status": updated.lifecycle_status,
                        "status": updated.status,
                        "is_deleted": bool(updated.is_deleted
                                           if updated.is_deleted is not None
                                           else False)})
    except Exception as e:
        logger.error("Content lifecycle error (id=%s, action=%s): %s",
                     item_id, action, e)
        return jsonify({"success": False,
                        "error": "Lifecycle operation failed"}), 500


# =========================================================================
# Content Studio Lifecycle API (GATE 7)
# =========================================================================


@content_bp.route("/", methods=["GET"])
def api_list_content():
    """List user's content with lifecycle filter.

    Query params:
        lifecycle_status: Filter by status (active, archived, trashed).
                          Default: active.
        limit (int, default 50): Max items.
        offset (int, default 0): Pagination offset.
        content_type (str, optional): Filter by content type.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    limit = min(int(request.args.get("limit", 50)), 100)
    offset = int(request.args.get("offset", 0))
    lifecycle_status = request.args.get("lifecycle_status", "active")
    content_type = request.args.get("content_type")

    try:
        from app.integration.models import ContentGeneration
        from app import db

        q = ContentGeneration.query.filter_by(identity_id=_identity_id())
        if lifecycle_status:
            q = q.filter_by(lifecycle_status=lifecycle_status)
        if content_type:
            q = q.filter_by(content_type=content_type)

        total = q.count()
        items = q.order_by(ContentGeneration.created_at.desc()).offset(offset).limit(limit).all()

        return jsonify({
            "success": True,
            "data": [item.to_dict() for item in items],
            "total": total,
            "limit": limit,
            "offset": offset,
        })
    except Exception as e:
        logger.error("Content list error: %s", e)
        return jsonify({"success": False,
                        "error": "Content could not be loaded"}), 500


@content_bp.route("/<int:item_id>", methods=["GET"])
def api_get_content(item_id: int):
    """Get a single content item with full lifecycle metadata."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.integration.models import ContentGeneration
        from app import db
        item = db.session.get(ContentGeneration, item_id)
        if not item or item.identity_id != _identity_id():
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "data": item.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@content_bp.route("/<int:item_id>", methods=["PATCH"])
def api_patch_content(item_id: int):
    """Update content metadata (rename, description, tone, etc.)."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    allowed_fields = {"name", "tone", "target_audience", "additional_instructions",
                      "platform", "content_type"}

    try:
        from app.integration.models import ContentGeneration
        from app import db
        item = db.session.get(ContentGeneration, item_id)
        if not item or item.identity_id != _identity_id():
            return jsonify({"success": False, "error": "Not found"}), 404

        # Only allow updating content if item is not trashed
        current = _derive_lifecycle_state(item)
        if current == "trashed":
            return jsonify({
                "success": False,
                "error": "Cannot update trashed content",
                "state": current,
            }), 409

        updated = False
        for field in allowed_fields:
            if field in data:
                setattr(item, field, data[field])
                updated = True

        if updated:
            item.updated_at = datetime.utcnow()
            db.session.commit()

        return jsonify({"success": True, "data": item.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _lifecycle_operation(item_id: int, action: str, target_status: str):
    """Shared helper for archive/trash/restore operations."""
    from app.integration.models import ContentGeneration
    from app import db
    actor = _identity_id()
    item = db.session.get(ContentGeneration, item_id)
    if not item or item.identity_id != actor:
        return jsonify({"success": False, "error": "Not found"}), 404

    current = _derive_lifecycle_state(item)
    allowed_from, new_status = LIFECYCLE_TRANSITIONS[action]

    if current not in allowed_from:
        return jsonify({
            "success": False,
            "error": f"Cannot {action} content in state '{current}'",
            "state": current,
            "allowed_from": sorted(allowed_from),
        }), 409

    now = datetime.utcnow()
    if action == "archive":
        item.lifecycle_status = "archived"
        item.status = "archived"
        item.archived_at = now
        item.archived_by = actor
    elif action == "trash":
        item.lifecycle_status = "trashed"
        item.is_deleted = True
        item.deleted_at = now
        item.deleted_by = actor
    elif action == "restore":
        item.lifecycle_status = "active"
        item.status = "active"
        item.is_deleted = False
        item.restored_at = now
        item.restored_by = actor

    item.updated_at = now
    db.session.commit()

    return jsonify({
        "success": True,
        "action": action,
        "lifecycle_status": item.lifecycle_status,
        "data": item.to_dict(),
    })


@content_bp.route("/<int:item_id>/archive", methods=["POST"])
def api_archive_content(item_id: int):
    """Archive content (from ACTIVE to ARCHIVED)."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    return _lifecycle_operation(item_id, "archive", "archived")


@content_bp.route("/<int:item_id>/trash", methods=["POST"])
def api_trash_content(item_id: int):
    """Trash content (from ACTIVE or ARCHIVED to TRASHED)."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    return _lifecycle_operation(item_id, "trash", "trashed")


@content_bp.route("/<int:item_id>/restore", methods=["POST"])
def api_restore_content(item_id: int):
    """Restore content (from ARCHIVED or TRASHED back to ACTIVE)."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    return _lifecycle_operation(item_id, "restore", "active")


@content_bp.route("/<int:item_id>/permanent-delete", methods=["DELETE"])
def api_permanent_delete_content(item_id: int):
    """Permanently delete content (only allowed from TRASHED state).

    This is irreversible. The item must be in TRASHED state.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.integration.models import ContentGeneration
        from app import db
        actor = _identity_id()
        item = db.session.get(ContentGeneration, item_id)
        if not item or item.identity_id != actor:
            return jsonify({"success": False, "error": "Not found"}), 404

        current = _derive_lifecycle_state(item)
        if current != "trashed":
            return jsonify({
                "success": False,
                "error": "Content must be in trash before permanent deletion",
                "state": current,
            }), 409

        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True, "action": "permanent-delete", "state": "deleted"})
    except Exception as e:
        logger.error("Content permanent delete error (id=%s): %s", item_id, e)
        return jsonify({"success": False, "error": str(e)}), 500


# -- Universal Inhibition Layer (SUIL) Endpoint --

LEVELS = {
    0: "ALLOW",
    1: "OBSERVE",
    2: "GUARD",
    3: "CONFIRM",
    4: "RESTRICT",
    5: "BLOCK",
}


def evaluate_inhibition(action_type: str, context: dict) -> dict:
    """Universal inhibition evaluation.

    Returns deterministic risk level for any action type.
    """
    tenant_id = context.get("tenant_id", 0)
    identity = context.get("identity_id", "")
    action = action_type

    # Tenant boundary
    if not tenant_id:
        return {"allowed": False, "level": 5, "reason": "No tenant context"}

    # Budget protection (campaign spend)
    if "spend" in action or "campaign" in action:
        budget = context.get("budget", 0)
        if budget > 1000000:
            return {"allowed": False, "level": 4, "reason": "Budget exceeds limit, requires approval"}
        if budget > 500000:
            return {"allowed": True, "level": 3, "reason": "High budget, confirm required"}

    # Media generation checks
    if "media" in action or "generate" in action:
        if not identity:
            return {"allowed": False, "level": 5, "reason": "Authentication required"}
        return {"allowed": True, "level": 0, "reason": "Safe action"}

    # Publication checks
    if "publish" in action or "execute" in action:
        return {"allowed": True, "level": 3, "reason": "Requires confirmation before execution"}

    # AI command execution
    if "ai" in action and ("execute" in action or "create" in action):
        return {"allowed": True, "level": 2, "reason": "Guardrails apply"}

    # Default: allow with observe
    return {"allowed": True, "level": 1, "reason": "Observe"}


@content_bp.route("/inhibit", methods=["POST"])
def api_inhibit():
    """Evaluate a proposed action via the Universal Inhibition Layer.

    Can be called with basic session auth or, for higher-sensitivity actions,
    with canonical permission checks.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    action_type = data.get("action_type", "")
    if not action_type:
        return jsonify({"success": False, "error": "action_type is required"}), 400

    context = {
        "tenant_id": _tenant_id(),
        "identity_id": _identity_id(),
        **{ k: v for k, v in data.items() if k not in ("action_type",)},
    }

    decision = evaluate_inhibition(action_type, context)

    return jsonify({
        "success": True,
        "action_type": action_type,
        "allowed": decision["allowed"],
        "level": decision["level"],
        "level_label": LEVELS.get(decision["level"], "UNKNOWN"),
        "reason": decision["reason"],
    })


@content_bp.route("/inhibit/authz", methods=["POST"])
def api_inhibit_authz():
    """Evaluate inhibition via canonical permission-based auth.

    Uses the `authz.decorators.require_permission` chain so that SUIL
    integrates with the canonical authorization engine rather than
    bypassing it. Requires the 'admin.view_audit' permission.
    """
    from app.authz.decorators import require_permission, _resolve_identity, _resolve_org_id

    # Apply the canonical permission check inline
    identity = _resolve_identity()
    if not identity:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"success": False, "error": "No organization selected"}), 400

    from app.authz.services import check_permission
    if not check_permission(org_id, identity, "admin.view_audit"):
        return jsonify({
            "success": False,
            "error": "Forbidden: admin.view_audit permission required",
        }), 403

    data = request.get_json(silent=True) or {}
    action_type = data.get("action_type", "")
    if not action_type:
        return jsonify({"success": False, "error": "action_type is required"}), 400

    context = {
        "tenant_id": org_id,
        "identity_id": identity,
        **{ k: v for k, v in data.items() if k not in ("action_type",)},
    }

    decision = evaluate_inhibition(action_type, context)

    return jsonify({
        "success": True,
        "action_type": action_type,
        "allowed": decision["allowed"],
        "level": decision["level"],
        "level_label": LEVELS.get(decision["level"], "UNKNOWN"),
        "reason": decision["reason"],
        "authz_gate": "admin.view_audit",
    })


@content_bp.route("/health", methods=["GET"])
def api_health():
    """Health check."""
    return jsonify({
        "status": "ok",
        "service": "content-studio",
        "endpoints": [
            "POST /api/v1/content/generate",
            "GET /api/v1/content/",
            "GET /api/v1/content/<id>",
            "PATCH /api/v1/content/<id>",
            "POST /api/v1/content/<id>/archive",
            "POST /api/v1/content/<id>/trash",
            "POST /api/v1/content/<id>/restore",
            "DELETE /api/v1/content/<id>/permanent-delete",
            "GET /api/v1/content/history",
            "GET /api/v1/content/history/<id>",
            "POST /api/v1/content/history/<id>/favorite",
            "DELETE /api/v1/content/history/<id>",
            "POST /api/v1/content/history/<id>/lifecycle",
            "POST /api/v1/content/inhibit",
            "POST /api/v1/content/inhibit/authz",
        ],
    })