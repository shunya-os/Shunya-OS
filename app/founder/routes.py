"""SHUNYA — Founder Experience Routes (Thin Transport Layer).

Every Founder API action flows through:
  Founder Request → Flask Route → ShunyaOS.process_intent() → Runtime Pipeline → Response

No route contains business logic. Routes parse HTTP, call the OS pipeline,
serialize responses. All business logic lives in the runtimes.

Architecture: Flask transports. ShunyaOS orchestrates. Runtimes execute.
"""

from datetime import datetime, timezone

from flask import (
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from app import db
from sqlalchemy import text
from app.adapters.os_adapter import (
    create_object,
    create_space,
    get_executive_home,
    process_intent,
    sign_in,
)
from app.founder import founder_bp
from app.authz.decorators import require_permission
from app.founder.models import (
    BusinessRelationship,
    FounderConversation,
    FounderMessage,
    FounderSpace,
)
from app.objects.legacy_models import ShunyaObject

# ---------------------------------------------------------------------------
# Helpers (auth only — no business logic)
# ---------------------------------------------------------------------------


def _founder_required() -> bool:
    """Check that the user is authenticated."""
    user_id = session.get("user_id")
    identity_id = session.get("identity_id")
    return bool(user_id and identity_id)


def _identity_id() -> str:
    """Canonical identity for the current session (``""`` when unauthenticated).

    Every canonical object read in this module must be authorized for this
    identity — the same predicate the CRUD write path uses.
    """
    return str(session.get("identity_id") or "")


def _get_identity_name() -> str:
    """Get the current user's display name from the canonical OS identity model."""
    identity_id = session.get("identity_id")
    if identity_id:
        from app.adapters.os_adapter import get_identity_name
        name = get_identity_name(identity_id)
        if name:
            return name
    return "Founder"


# ---------------------------------------------------------------------------
# HTML Pages (transitional UI — no business logic)
# ---------------------------------------------------------------------------


@founder_bp.route("/founder/home")
def founder_home():
    if not _founder_required():
        return redirect(url_for("founder.founder_login"))
    return redirect(url_for("founder.workspace"))


@founder_bp.route("/founder/login")
def founder_login():
    if _founder_required():
        return redirect(url_for("founder.founder_home"))
    # Redirect to SPA auth login — founder_login template no longer exists
    return redirect("/auth/login")


@founder_bp.route("/founder/space/create")
def founder_space_create():
    if not _founder_required():
        return redirect(url_for("founder.founder_login"))
    return render_template("founder_space_create.html",
                           founder_name=_get_identity_name())


@founder_bp.route("/founder/space/<space_id>")
def founder_space_workspace(space_id: str):
    if not _founder_required():
        return redirect(url_for("founder.founder_login"))
    row = db.session.execute(
        text("SELECT id AS space_id, name, workspace_type AS space_type, status, description, created_at FROM sh_workspaces WHERE id = :sid AND status = 'active'"),
        {"sid": space_id},
    ).first()
    if not row:
        return "Space not found", 404
    from core.object_service import get_object_service
    svc = get_object_service()
    org_id = session.get("current_org_id", 0)
    objects = svc.list_by_workspace(workspace_id=space_id, organization_id=org_id,
                                    identity_id=_identity_id())
    return render_template("founder_workspace.html",
                           space=row, objects=objects or [],
                           founder_name=_get_identity_name())


@founder_bp.route("/founder/object/<object_id>")
def founder_object_view(object_id: str):
    if not _founder_required():
        return redirect(url_for("founder.founder_login"))
    from core.object_service import get_object_service
    svc = get_object_service()
    # Canonical reads are ALWAYS organization-scoped. An unscoped lookup
    # (organization_id omitted) reads NULL-organization rows, which is not a
    # tenant-safe read surface.
    org_id = session.get("current_org_id")
    if not org_id:
        return "Organization context missing", 400
    obj = svc.get_by_object_id(object_id, organization_id=int(org_id),
                               identity_id=_identity_id())
    if not obj:
        return "Object not found", 404
    space_row = db.session.execute(
        text("SELECT id AS space_id, name, workspace_type AS space_type, status, description FROM sh_workspaces WHERE id = :sid AND status = 'active'"),
        {"sid": obj.get("workspace_id", "")},
    ).first()
    conversation = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()
    messages = []
    if conversation:
        messages = FounderMessage.query.filter_by(
            conv_id=conversation.conv_id
        ).order_by(FounderMessage.created_at).all()
    return render_template("founder_object.html",
                           object=obj, space=space_row,
                           conversation=conversation, messages=messages,
                           founder_name=_get_identity_name())


@founder_bp.route("/workspace")
@founder_bp.route("/workspace/")
@founder_bp.route("/workspace/<path:subpath>")
def workspace(subpath=None):
    """Serve the SPA for all /workspace/* paths.

    Catch-all route so the SPA (React/Vite) handles domain routing
    (e.g. /workspace/content, /workspace/sales, /workspace/people).
    If the SPA index.html is available in the built dist, serve it.
    Otherwise fall back to the Jinja template for backward compat.
    """
    if not _founder_required():
        return redirect(url_for("founder.founder_login"))
    import os
    # Serve the shell from the SAME resolved directory as the assets: the
    # immutable published release in production, so a local build cannot change
    # what production serves. Falls back to the in-checkout build.
    candidates = []
    try:
        from app.frontend_release import resolve_frontend_dist
        candidates.append(resolve_frontend_dist())
    except Exception:
        pass
    candidates.append(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
    for frontend_dist in candidates:
        if os.path.isfile(os.path.join(frontend_dist, "index.html")):
            return send_from_directory(frontend_dist, "index.html")
    return render_template("workspace.html")


# ---------------------------------------------------------------------------
# API — Sign In (thin: parse HTTP → call OS → serialize)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/signin", methods=["POST"])
def api_founder_signin():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400

    from app.auth import TeamMember, UserRole

    # PHASE 1: Find existing verified TeamMember
    tm = TeamMember.query.filter_by(email=email, is_active=True, verified=True).first()

    if tm:
        # Existing user — MUST validate password
        if not tm.check_password(password):
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

        # Authenticated — resolve identity and workspace
        session["user_id"] = tm.id
        session.modified = True

        try:
            from app.models import OrgMember, Organization
            from sqlalchemy import func
            org_members = OrgMember.query.filter_by(email=email, is_active=True).all()
            if org_members:
                org_counts = {}
                for om in org_members:
                    cnt = OrgMember.query.filter_by(organization_id=om.organization_id, is_active=True).count()
                    org_counts[om.organization_id] = cnt
                best_org_id = max(org_counts, key=org_counts.get)
                org_member = next(om for om in org_members if om.organization_id == best_org_id)
                identity_id = org_member.identity_id
                session["identity_id"] = identity_id
                session["current_org_id"] = org_member.organization_id

                # Check if user has completed onboarding (has personal workspace or org membership)
                from core.object_service import get_object_service
                svc = get_object_service()
                has_personal = len(svc.list_by_creator(
                    created_by=identity_id,
                    organization_id=org_member.organization_id,
                    identity_id=identity_id,
                    limit=1,
                )) > 0

                return jsonify({
                    "success": True,
                    "redirect": url_for("workspace_routes.workspace_home"),
                    "name": tm.name,
                    "identity_id": identity_id,
                    "onboarding_complete": has_personal or True,
                })
        except Exception:
            pass

        # Authenticated but no org membership — personal workspace
        session["identity_id"] = session.get("identity_id") or tm.email or str(tm.id)
        session.setdefault("current_org_id", 0)
        return jsonify({
            "success": True,
            "redirect": "/",
            "name": tm.name,
            "identity_id": session["identity_id"],
        })

    # Check if account exists but is unverified
    unverified = TeamMember.query.filter_by(email=email).first()
    if unverified and not unverified.verified:
        return jsonify({
            "success": False,
            "error": "Account not yet verified. Please check your email for the verification link."
        }), 403

    # PHASE 2: No account found for this email
    return jsonify({
        "success": False,
        "error": "Invalid email or password"
    }), 401


# ---------------------------------------------------------------------------
# API — Profile (read-only, transitional)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/profile", methods=["GET"])
@require_permission("org.view")
def api_founder_profile():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    return jsonify({
        "success": True,
        "data": {
            "name": _get_identity_name(),
            "identity_id": session.get("identity_id"),
        },
    })


# ---------------------------------------------------------------------------
# API — Executive Home (pipeline-powered dashboard)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/executive-home", methods=["GET"])
@require_permission("org.view")
def api_executive_home():
    """Return Executive Home dashboard data assembled from the real OS pipeline.

    Returns pipeline health, runtime summaries, recent projection traces,
    and the current state of all registered runtimes.
    """
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    result = get_executive_home(identity_id=identity_id)
    return jsonify(result)


@founder_bp.route("/api/v1/founder/pipeline/health", methods=["GET"])
@require_permission("org.view")
def api_pipeline_health():
    """Return real-time pipeline health from the OS.

    Shows which runtimes are registered, which pipeline stages have
    real vs. mock runtimes, and aggregate health status.
    """
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from core.os import get_os
    os = get_os()
    health = os.health_check()
    return jsonify({
        "success": True,
        "data": health,
    })


@founder_bp.route("/api/v1/founder/pipeline/traces", methods=["GET"])
@require_permission("org.view")
def api_pipeline_traces():
    """Return recent pipeline execution traces.

    Shows the intent, stages executed, timing, and status for recent
    pipeline executions. Useful for founder observability and debugging.
    """
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from core.os import get_os
    os = get_os()
    proj_runtime = os.get_runtime("projection")
    traces = []
    if proj_runtime and hasattr(proj_runtime, "get_traces"):
        try:
            traces = proj_runtime.get_traces(limit=20)
        except Exception:
            pass
    return jsonify({
        "success": True,
        "data": traces,
    })


# ---------------------------------------------------------------------------
# API — Logout
# ---------------------------------------------------------------------------


@founder_bp.route("/founder/logout", methods=["POST", "GET"])
def founder_logout():
    session.clear()
    return redirect(url_for("founder.founder_login"))


# ---------------------------------------------------------------------------
# API — Spaces (thin: parse HTTP → call OS → serialize)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/spaces", methods=["GET"])
@require_permission("org.view")
def api_list_spaces():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    # Org-scoped: filter by user's organization
    from app.authz.decorators import _resolve_org_id
    org_id = _resolve_org_id()
    if org_id:
        spaces = db.session.execute(
            text("SELECT id AS space_id, name, workspace_type AS space_type, status, description, created_at FROM sh_workspaces WHERE organization_id = :org_id AND status = 'active' ORDER BY created_at DESC"),
            {"org_id": org_id},
        ).fetchall()
    else:
        spaces = db.session.execute(
            text("SELECT id AS space_id, name, workspace_type AS space_type, status, description, created_at FROM sh_workspaces WHERE created_by = :identity_id AND status = 'active' ORDER BY created_at DESC"),
            {"identity_id": session.get("identity_id")},
        ).fetchall()
    spaces_list = [dict(s._mapping) for s in spaces]
    return jsonify({"success": True, "data": spaces_list})


@founder_bp.route("/api/v1/founder/spaces", methods=["POST"])
@require_permission("org.edit")
def api_create_space():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "error": "Space name is required."}), 400

    identity_id = session.get("identity_id")
    result = create_space(
        name=name,
        identity_id=identity_id,
        space_type=data.get("space_type", "organization"),
        description=data.get("description", ""),
    )
    # Dual-write: persist to DB for backward compat during migration
    space_id = result.get("object_id", "")
    if not space_id and result.get("success"):
        # Pipeline confirmed validity but doesn't generate IDs for spaces
        import uuid
        space_id = f"spc_{uuid.uuid4().hex[:16]}"
    if space_id:
        existing = db.session.execute(
            text("SELECT id FROM sh_workspaces WHERE id = :sid"),
            {"sid": space_id},
        ).first()
        if not existing:
            db.session.execute(
                text("INSERT INTO sh_workspaces (id, name, workspace_type, status, created_by, created_at, updated_at) VALUES (:id, :name, :ws_type, 'active', :created_by, NOW(), NOW())"),
                {"id": space_id, "name": name, "ws_type": data.get("space_type", "organization"), "created_by": identity_id},
            )
            db.session.commit()
        return jsonify({
            "success": True,
            "data": {"id": space_id, "name": name, "space_type": data.get("space_type", "organization"), "description": data.get("description", "")},
            "redirect": url_for("founder.founder_space_workspace", space_id=space_id),
        }), 201
    return jsonify({"success": False, "error": "Space creation failed"}), 500


@founder_bp.route("/api/v1/founder/spaces/<space_id>", methods=["GET"])
@require_permission("org.view")
def api_get_space(space_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    space = db.session.execute(
        text("SELECT id AS space_id, name, workspace_type AS space_type, status, description, created_at FROM sh_workspaces WHERE id = :sid AND status = 'active'"),
        {"sid": space_id},
    ).first()
    if not space:
        return jsonify({"success": False, "error": "Space not found"}), 404
    space_dict = dict(space._mapping)
    return jsonify({"success": True, "data": space_dict})


# ---------------------------------------------------------------------------
# API — Objects (thin: parse HTTP → call OS → serialize)
# ---------------------------------------------------------------------------


def _canonical_object_read(object_id: str) -> dict | None:
    """Read an object from the canonical store (sh_objects), scoped to the caller's org.

    Canonical-only (R6B-2.4): the legacy founder_objects fallback was removed.
    It was reachable whenever the canonical lookup returned nothing and it read
    founder_objects without any organization scope — so it could surface another
    tenant's object as the caller's truth. Canonical absence is authoritative:
    an object that is not in sh_objects for this organization is absent.
    """
    from core.object_service import get_object_service
    svc = get_object_service()
    from flask import session
    org_id = session.get("current_org_id", 0)
    return svc.get_by_object_id(object_id, organization_id=org_id,
                                identity_id=_identity_id())



@founder_bp.route("/api/v1/founder/spaces/<space_id>/objects", methods=["GET"])
@require_permission("rel.view")
def api_list_objects(space_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from core.object_service import get_object_service
    svc = get_object_service()
    org_id = session.get("current_org_id", 0)
    # Canonical read (sh_objects with workspace_id = space_id)
    canonical = []
    try:
        canonical = svc.list_by_workspace(workspace_id=space_id, organization_id=org_id,
                                          identity_id=_identity_id())
    except Exception:
        canonical = []
    # Canonical-only (R6B-2.4): no legacy founder_objects fallback. A workspace
    # with no canonical objects for this organization returns an empty list.
    return jsonify({"success": True, "data": canonical})


@founder_bp.route("/api/v1/founder/spaces/<space_id>/objects", methods=["POST"])
@require_permission("rel.create")
def api_create_object(space_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    object_type = data.get("object_type", "Document")
    content = data.get("content", "")
    if not name:
        return jsonify({"success": False, "error": "Object name is required."}), 400

    # Delegate to OS pipeline
    identity_id = session.get("identity_id")
    result = create_object(
        name=name,
        object_type=object_type,
        space_id=space_id,
        identity_id=identity_id,
        content=content,
    )

    if result["success"] and result.get("object_id"):
        obj_id = result["object_id"]
        # Canonical creation already happened via OS pipeline (create_object above).
        # The legacy dual-write to FounderObject + ShunyaObject has been removed
        # as part of canonical object convergence (R6B-2). ObjectService writes
        # directly to sh_objects and is the single production write authority.
        space = db.session.execute(
            text("SELECT id, name FROM sh_workspaces WHERE id = :sid AND status = 'active'"),
            {"sid": space_id},
        ).first()
        if space:
            from datetime import timezone
            db.session.execute(
                text("UPDATE sh_workspaces SET updated_at = :now WHERE id = :sid"),
                {"now": datetime.now(timezone.utc), "sid": space_id},
            )
            db.session.commit()

        return jsonify({
            "success": True,
            "data": {"object_id": obj_id, "name": name, "object_type": object_type},
            "redirect": url_for("founder.founder_object_view", object_id=obj_id),
        }), 201

    # Pipeline provides runtime-level error
    error = "Object creation failed"
    for r in result.get("trace", []):
        if r.get("error"):
            error = r["error"]
            break
    return jsonify({"success": False, "error": error}), 500


@founder_bp.route("/api/v1/founder/objects/<object_id>", methods=["GET"])
@require_permission("rel.view")
def api_get_object(object_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    obj = _canonical_object_read(object_id)
    if not obj:
        return jsonify({"success": False, "error": "Object not found"}), 404
    return jsonify({"success": True, "data": obj})


# ---------------------------------------------------------------------------
# API — Object Focus (read-only context assembly, transitional)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/focus/<object_id>", methods=["GET"])
@require_permission("rel.view")
def api_focus_object(object_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    org_id = session.get("current_org_id", 0)
    from core.object_service import get_object_service
    svc = get_object_service()
    obj = svc.get_by_object_id(object_id, organization_id=org_id,
                               identity_id=_identity_id())
    if not obj:
        return jsonify({"success": False, "error": "Object not found"}), 404

    space_row = db.session.execute(
        text("SELECT id AS space_id, name, workspace_type AS space_type, status, description FROM sh_workspaces WHERE id = :sid AND status = 'active'"),
        {"sid": obj.get("workspace_id", "")},
    ).first()

    related_objects = svc.list_by_workspace(workspace_id=obj.get("workspace_id", ""), organization_id=org_id,
                                            identity_id=_identity_id())
    if related_objects:
        related_objects = [r for r in related_objects if r.get("object_id") != object_id][:5]
    else:
        related_objects = []
    relationships = [{"object_id": r.get("object_id"), "name": r.get("name"), "type": r.get("object_type"), "relationship": "same_space"} for r in related_objects]

    conversation = FounderConversation.query.filter_by(object_id=object_id, status="active").first()
    messages = []
    if conversation:
        msgs = FounderMessage.query.filter_by(conv_id=conversation.conv_id).order_by(FounderMessage.created_at).all()
        messages = [m.to_dict() for m in msgs]

    obj_type = obj.get("object_type", "")
    ai_parts = []
    if obj_type:
        ai_parts.append(f"This is a {obj_type.lower()}.")
    if len(messages) > 0:
        msg_count = len(messages)
        ai_parts.append(f"{msg_count // 2} message{'s have' if msg_count // 2 != 1 else ' has'} been exchanged.")
    if space_row:
        ai_parts.append(f"It belongs to the '{space_row.name}' space.")
    if relationships:
        ai_parts.append(f"It is connected to {len(relationships)} other object{'s' if len(relationships) != 1 else ''}.")

    space_data = None
    if space_row:
        space_data = {"space_id": space_row.space_id, "name": space_row.name, "workspace_type": space_row.space_type, "status": space_row.status, "description": space_row.description}

    return jsonify({
        "success": True,
        "data": {
            "object": obj,
            "space": space_data,
            "relationships": relationships,
            "conversation": conversation.to_dict() if conversation else None,
            "messages": messages,
            "ai_understanding": " ".join(ai_parts) if ai_parts else "SHUNYA is observing this object.",
        },
    })


# ---------------------------------------------------------------------------
# API — Conversations (thin: parse HTTP → call OS → serialize)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/objects/<object_id>/conversation", methods=["POST"])
@require_permission("rel.create")
def api_start_conversation(object_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    # Canonical object lookup via ObjectService (R6B-2): conversations now
    # reference sh_objects.object_id, not founder_objects.
    # The lookup is organization-scoped from the session — the previous
    # unscoped call plus raw `SELECT ... LIMIT 1` fallback read sh_objects with
    # no tenant filter, which is not an acceptable authorization surface.
    from core.object_service import get_object_service
    svc = get_object_service()
    org_id = session.get("current_org_id")
    if not org_id:
        return jsonify({"success": False, "error": "Organization context missing"}), 400
    obj = svc.get_by_object_id(object_id, organization_id=int(org_id),
                               identity_id=_identity_id())
    if obj is None:
        return jsonify({"success": False, "error": "Object not found"}), 404
    obj_name = obj.get("name", "Object")
    existing = FounderConversation.query.filter_by(object_id=object_id, status="active").first()
    if existing:
        return jsonify({"success": True, "data": existing.to_dict(), "message": "Conversation already exists"})
    identity_id = session.get("identity_id")
    import uuid
    conv_id = f"conv_{uuid.uuid4().hex[:16]}"
    conversation = FounderConversation(conv_id=conv_id, object_id=object_id, title=f"About {obj_name}", identity_id=identity_id)
    db.session.add(conversation)
    db.session.commit()
    return jsonify({"success": True, "data": conversation.to_dict()}), 201


@founder_bp.route("/api/v1/founder/objects/<object_id>/conversation", methods=["GET"])
@require_permission("rel.view")
def api_get_conversation(object_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    conversation = FounderConversation.query.filter_by(object_id=object_id, status="active").first()
    if not conversation:
        return jsonify({"success": True, "data": None})
    messages = FounderMessage.query.filter_by(conv_id=conversation.conv_id).order_by(FounderMessage.created_at).all()
    return jsonify({"success": True, "data": {**conversation.to_dict(), "messages": [m.to_dict() for m in messages]}})


@founder_bp.route("/api/v1/founder/conversations/<conv_id>/messages", methods=["POST"])
@require_permission("rel.create")
def api_send_message(conv_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()
    if not content:
        return jsonify({"success": False, "error": "Message content is required."}), 400

    conversation = FounderConversation.query.filter_by(conv_id=conv_id, status="active").first()
    if not conversation:
        return jsonify({"success": False, "error": "Conversation not found"}), 404

    # Delegate to OS pipeline
    identity_id = session.get("identity_id")
    process_intent(
        intent="talk_to_customer",
        parameters={"message": content},
        identity_id=identity_id,
        object_id=conversation.object_id,
    )

    # Process through AI Copilot
    from app.ai.copilot import process_message
    copilot_result = process_message(conv_id=conv_id, user_message=content)

    if copilot_result["success"]:
        return jsonify({
            "success": True,
            "data": {
                "response": copilot_result["response"],
                "model": copilot_result["model"],
                "intent": copilot_result["intent"],
            },
        }), 201
    else:
        # Fallback: use old hardcoded behavior
        human_msg = FounderMessage(conv_id=conv_id, role="human", content=content)
        db.session.add(human_msg)
        response_text = "I hear you. I've noted your thoughts on this object. What else would you like to explore?"
        assistant_msg = FounderMessage(conv_id=conv_id, role="assistant", content=response_text)
        db.session.add(assistant_msg)
        conversation.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify({
            "success": True,
            "data": {"human": human_msg.to_dict(), "assistant": assistant_msg.to_dict()},
        }), 201


# ---------------------------------------------------------------------------
# API — Search (read-only, transitional)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/search", methods=["GET"])
@require_permission("knowledge.search")
def api_search():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"success": True, "data": []})
    identity_id = session.get("identity_id")
    org_id = session.get("current_org_id", 0)
    user_spaces = db.session.execute(
        text("SELECT id AS space_id FROM sh_workspaces WHERE created_by = :cid AND status = 'active'"),
        {"cid": identity_id},
    ).fetchall()
    space_ids = [s.space_id for s in user_spaces]
    if not space_ids:
        return jsonify({"success": True, "data": []})
    from core.object_service import get_object_service
    svc = get_object_service()
    results = svc.search(q, organization_id=org_id, identity_id=_identity_id(),
                             limit=20) or []
    rel_results = BusinessRelationship.query.filter(
        BusinessRelationship.space_id.in_(space_ids),
        BusinessRelationship.status == "active",
        BusinessRelationship.name.ilike(f"%{q}%"),
    ).order_by(BusinessRelationship.updated_at.desc()).limit(10).all()
    combined = list(results)
    for r in rel_results:
        d = r.to_dict()
        d["_type"] = "relationship"
        d["object_id"] = d["rel_id"]
        combined.append(d)
    return jsonify({"success": True, "data": combined[:20]})


# ---------------------------------------------------------------------------
# API — Executive Home v2 (full founder operating surface)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/executive-home-v2", methods=["GET"])
@require_permission("org.view")
def api_executive_home_v2():
    """Return the complete Executive Home payload.

    Includes: Morning Brief, Recommendations, Business Health,
    Recent Activity, Continue Working — all from real runtime state.
    """
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    assert identity_id is not None  # guarded by _founder_required
    from app.founder.executive_home_service import build_executive_home
    data = build_executive_home(identity_id=identity_id)
    return jsonify({"success": True, "data": data})


# ---------------------------------------------------------------------------
# API — Executive Intelligence (Insights, Timeline, Attention)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/insights", methods=["GET"])
@require_permission("org.view")
def api_insights():
    """Return Executive Intelligence: derived insights, attention queue, timeline."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    assert identity_id is not None
    org_id = session.get("current_org_id", 0)
    from app.founder.insight_engine import build_insights
    data = build_insights(identity_id=identity_id, organization_id=org_id)
    return jsonify({"success": True, "data": data})


@founder_bp.route("/api/v1/founder/timeline", methods=["GET"])
@require_permission("org.view")
def api_timeline():
    """Return executive timeline."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    assert identity_id is not None
    org_id = session.get("current_org_id", 0)
    from app.founder.insight_engine import build_timeline
    data = build_timeline(identity_id=identity_id, organization_id=org_id)
    return jsonify({"success": True, "data": data})


@founder_bp.route("/api/v1/founder/insights/<insight_id>/lifecycle", methods=["POST"])
@require_permission("org.edit")
def api_insight_lifecycle(insight_id: str):
    """Update insight lifecycle: acknowledge, resolve, dismiss."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")
    from app.founder.insight_engine import acknowledge_insight, resolve_insight, dismiss_insight
    handlers = {"acknowledge": acknowledge_insight, "resolve": resolve_insight, "dismiss": dismiss_insight}
    handler = handlers.get(action)
    if not handler:
        return jsonify({"success": False, "error": f"Unknown action: {action}"}), 400
    state = handler(insight_id)
    return jsonify({"success": True, "data": {"insight_id": insight_id, "lifecycle": state}})


# ---------------------------------------------------------------------------
# API — Morning Zero (read-only, transitional)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/morning-zero", methods=["GET"])
@require_permission("org.view")
def api_morning_zero():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    org_id = session.get("current_org_id", 0)
    items = []
    spaces = db.session.execute(
        text("SELECT id AS space_id, name, workspace_type AS space_type, status, created_at FROM sh_workspaces WHERE created_by = :cid AND status = 'active' ORDER BY created_at DESC"),
        {"cid": identity_id},
    ).fetchall()
    total_objects = 0
    pending_conversations = 0
    from core.object_service import get_object_service
    svc = get_object_service()
    for space in spaces:
        objects = svc.list_by_workspace(workspace_id=space.space_id, organization_id=org_id,
                                        identity_id=_identity_id())
        if not objects:
            objects = []
        total_objects += len(objects)
        for obj in objects:
            conv = FounderConversation.query.filter_by(object_id=obj.get("object_id"), status="active").first()
            if conv:
                unread = FounderMessage.query.filter_by(conv_id=conv.conv_id, role="assistant").count()
                human_msgs = FounderMessage.query.filter_by(conv_id=conv.conv_id, role="human").count()
                if unread > 0 and human_msgs > 0:
                    last_msg = FounderMessage.query.filter_by(conv_id=conv.conv_id).order_by(FounderMessage.created_at.desc()).first()
                    preview = last_msg.content[:80] if last_msg else ""
                    items.append({"title": f"{obj.get('name', 'Object')} — {unread} message{'s' if unread > 1 else ''}", "meta": preview, "priority": "attention", "focus": {"object_id": obj.get("object_id"), "type": "object"}})
                    pending_conversations += 1
    if not items:
        items.append({"title": f"Everything is quiet across {len(spaces)} space{'s' if len(spaces) != 1 else ''}.", "meta": f"{total_objects} active object{'s' if total_objects != 1 else ''}", "priority": "info", "focus": None})
    space_ids = [s.space_id for s in spaces]
    if space_ids:
        rel_count = BusinessRelationship.query.filter(BusinessRelationship.space_id.in_(space_ids), BusinessRelationship.status == "active").count()
        if rel_count > 0:
            items.append({"title": f"{rel_count} relationship{'s' if rel_count != 1 else ''} in your network", "meta": "Customers, suppliers, partners, and team members", "priority": "info", "focus": None})
    return jsonify({"success": True, "data": {"items": items[:7], "summary": {"active_spaces": len(spaces), "active_objects": total_objects, "pending_conversations": pending_conversations}}})


# ---------------------------------------------------------------------------
# API — Relationships (thin routes, transitional — CRUD passed through OS intent)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/relationships/types", methods=["GET"])
@require_permission("rel.view")
def api_rel_types():
    return jsonify({"success": True, "data": [
        {"type": "customer", "label": "Customer", "icon": "person"},
        {"type": "supplier", "label": "Supplier", "icon": "box"},
        {"type": "partner", "label": "Partner", "icon": "handshake"},
        {"type": "employee", "label": "Employee", "icon": "badge"},
        {"type": "vendor", "label": "Vendor", "icon": "building"},
    ]})


@founder_bp.route("/api/v1/founder/relationships", methods=["GET"])
@require_permission("rel.view")
def api_list_relationships():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    rel_type = request.args.get("type", "")
    q = request.args.get("q", "")
    spaces = db.session.execute(
        text("SELECT id AS space_id FROM sh_workspaces WHERE created_by = :identity_id AND status = 'active'"),
        {"identity_id": identity_id},
    ).fetchall()
    space_ids = [s.space_id for s in spaces]
    if not space_ids:
        return jsonify({"success": True, "data": []})
    query = BusinessRelationship.query.filter(BusinessRelationship.space_id.in_(space_ids), BusinessRelationship.status == "active")
    if rel_type:
        query = query.filter(BusinessRelationship.rel_type == rel_type)
    if q:
        query = query.filter(BusinessRelationship.name.ilike(f"%{q}%"))
    results = query.order_by(BusinessRelationship.updated_at.desc()).all()
    return jsonify({"success": True, "data": [r.to_dict() for r in results]})


@founder_bp.route("/api/v1/founder/relationships", methods=["POST"])
@require_permission("rel.create")
def api_create_relationship():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    rel_type = data.get("rel_type", "customer").strip()
    if not name:
        return jsonify({"success": False, "error": "Name is required."}), 400
    identity_id = session.get("identity_id")
    space = db.session.execute(
        text("SELECT id, name, workspace_type AS space_type FROM sh_workspaces WHERE created_by = :identity_id AND status = 'active' ORDER BY created_at DESC LIMIT 1"),
        {"identity_id": identity_id},
    ).first()
    if not space:
        import uuid
        space_id = f"spc_{uuid.uuid4().hex[:16]}"
        db.session.execute(
            text("INSERT INTO sh_workspaces (id, name, workspace_type, status, created_by, created_at, updated_at) VALUES (:id, :name, :ws_type, 'active', :created_by, NOW(), NOW())"),
            {"id": space_id, "name": "My Business", "ws_type": "organization", "created_by": identity_id},
        )
        db.session.commit()
    import uuid
    rel_id = f"rel_{uuid.uuid4().hex[:24]}"
    tags = data.get("tags", "")
    if isinstance(tags, list):
        tags = ", ".join(tags)
    rel = BusinessRelationship(rel_id=rel_id, space_id=space.id, rel_type=rel_type, name=name, email=data.get("email", "").strip(), phone=data.get("phone", "").strip(), company=data.get("company", "").strip(), notes=data.get("notes", "").strip(), tags=tags, created_by=identity_id)
    db.session.add(rel)
    db.session.commit()
    return jsonify({"success": True, "data": rel.to_dict()}), 201


@founder_bp.route("/api/v1/founder/relationships/<rel_id>", methods=["GET"])
@require_permission("rel.view")
def api_get_relationship(rel_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    rel = BusinessRelationship.query.filter_by(rel_id=rel_id, status="active").first()
    if not rel:
        return jsonify({"success": False, "error": "Relationship not found"}), 404
    org_id = session.get("current_org_id", 0)
    from core.object_service import get_object_service
    svc = get_object_service()
    related_objects = svc.list_by_workspace(workspace_id=rel.space_id, organization_id=org_id,
                                            identity_id=_identity_id()) or []
    return jsonify({"success": True, "data": {"relationship": rel.to_dict(), "related_objects": list(related_objects)}})


@founder_bp.route("/api/v1/founder/relationships/<rel_id>", methods=["PUT"])
@require_permission("rel.edit")
def api_update_relationship(rel_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    rel = BusinessRelationship.query.filter_by(rel_id=rel_id, status="active").first()
    if not rel:
        return jsonify({"success": False, "error": "Relationship not found"}), 404
    data = request.get_json(silent=True) or {}
    for field in ("name", "rel_type", "email", "phone", "company", "notes", "status"):
        if field in data:
            val = data[field]
            if field == "tags" and isinstance(val, list):
                val = ", ".join(val)
            setattr(rel, field, str(val).strip() if isinstance(val, str) else val)
    db.session.commit()
    return jsonify({"success": True, "data": rel.to_dict()})


@founder_bp.route("/api/v1/founder/relationships/<rel_id>", methods=["DELETE"])
@require_permission("rel.delete")
def api_delete_relationship(rel_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    rel = BusinessRelationship.query.filter_by(rel_id=rel_id).first()
    if not rel:
        return jsonify({"success": False, "error": "Relationship not found"}), 404
    rel.status = "archived"
    db.session.commit()
    return jsonify({"success": True})

@founder_bp.route("/api/v1/founder/objects/types", methods=["GET"])
@require_permission("rel.view")
def api_list_object_types():
    """List available object types and counts."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    org_id = session.get("current_org_id", 0)
    from core.object_service import get_object_service
    svc = get_object_service()
    data = svc.count_by_type(organization_id=org_id, identity_id=_identity_id()) or {}
    return jsonify({"success": True, "data": data})


@founder_bp.route("/api/v1/founder/objects", methods=["GET"])
@require_permission("rel.view")
def api_list_founder_objects():
    """List objects scoped to the current user's organization."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.authz.decorators import _resolve_org_id
    org_id = _resolve_org_id()
    from core.object_service import get_object_service
    svc = get_object_service()
    if org_id:
        # Filter by org's spaces
        space_rows = db.session.execute(
            text("SELECT id AS space_id FROM sh_workspaces WHERE organization_id = :oid"),
            {"oid": org_id},
        ).fetchall()
        space_ids = [s.space_id for s in space_rows]
        if space_ids:
            # Collect objects from all org workspaces
            all_objs = []
            for sid in space_ids:
                ws_objs = svc.list_by_workspace(workspace_id=sid, organization_id=org_id,
                                                identity_id=_identity_id()) or []
                all_objs.extend(ws_objs)
            objs = all_objs
        else:
            objs = []
    else:
        # No canonical organization context: there is no tenant scope to list
        # under, so nothing is returned rather than querying objects through a
        # synthetic organization_id=0, which was never the caller's ownership.
        objs = []
    return jsonify({"success": True, "data": list(objs), "count": len(objs)})


# ---------------------------------------------------------------------------
# M4 — Workspace Intelligence API
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/workspace/<object_id>", methods=["GET"])
@require_permission("rel.view")
def api_workspace_intelligence(object_id: str):
    """Return the complete workspace intelligence for an object.

    Assembles all M4 panels: summary, AI understanding, relationships,
    timeline, conversation, next actions, missing context, health, evidence.
    """
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    org_id = session.get("current_org_id", 0)
    from app.founder.workspace_intelligence import build_full_workspace
    result = build_full_workspace(object_id, organization_id=org_id,
                                  identity_id=_identity_id())
    return jsonify({"success": True, "data": result})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/summary", methods=["GET"])
@require_permission("rel.view")
def api_workspace_summary(object_id: str):
    """Return workspace summary for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    org_id = session.get("current_org_id", 0)
    from app.founder.workspace_intelligence import build_workspace_summary
    return jsonify({"success": True, "data": build_workspace_summary(object_id, organization_id=org_id, identity_id=_identity_id())})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/ai-understanding", methods=["GET"])
@require_permission("ai.use")
def api_ai_understanding(object_id: str):
    """Return AI Understanding panel."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    org_id = session.get("current_org_id", 0)
    from app.founder.workspace_intelligence import build_ai_understanding
    return jsonify({"success": True, "data": build_ai_understanding(object_id, organization_id=org_id, identity_id=_identity_id())})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/relationships", methods=["GET"])
@require_permission("rel.view")
def api_workspace_relationships(object_id: str):
    """Return relationship intelligence for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    org_id = session.get("current_org_id", 0)
    from app.founder.workspace_intelligence import build_relationship_intelligence
    return jsonify({"success": True, "data": build_relationship_intelligence(object_id, organization_id=org_id, identity_id=_identity_id())})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/timeline", methods=["GET"])
@require_permission("rel.view")
def api_workspace_timeline(object_id: str):
    """Return activity timeline for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    org_id = session.get("current_org_id", 0)
    from app.founder.workspace_intelligence import build_activity_timeline
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"success": True, "data": build_activity_timeline(object_id, limit=limit, organization_id=org_id, identity_id=_identity_id())})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/conversation", methods=["GET"])
@require_permission("rel.view")
def api_workspace_conversation(object_id: str):
    """Return conversation workspace for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    org_id = session.get("current_org_id", 0)
    from app.founder.workspace_intelligence import get_conversation_workspace
    return jsonify({"success": True, "data": get_conversation_workspace(object_id, organization_id=org_id, identity_id=_identity_id())})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/next-actions", methods=["GET"])
@require_permission("task.view")
def api_workspace_next_actions(object_id: str):
    """Return next actions for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    org_id = session.get("current_org_id", 0)
    from app.founder.workspace_intelligence import build_next_actions
    return jsonify({"success": True, "data": build_next_actions(object_id, organization_id=org_id, identity_id=_identity_id())})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/missing-context", methods=["GET"])
@require_permission("task.view")
def api_workspace_missing_context(object_id: str):
    """Return missing context for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    org_id = session.get("current_org_id", 0)
    from app.founder.workspace_intelligence import detect_missing_context
    return jsonify({"success": True, "data": detect_missing_context(object_id, organization_id=org_id, identity_id=_identity_id())})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/health", methods=["GET"])
@require_permission("org.view")
def api_workspace_health(object_id: str):
    """Return workspace health assessment."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    org_id = session.get("current_org_id", 0)
    from app.founder.workspace_intelligence import compute_workspace_health
    return jsonify({"success": True, "data": compute_workspace_health(object_id, organization_id=org_id, identity_id=_identity_id())})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/evidence", methods=["GET"])
@require_permission("knowledge.view")
def api_workspace_evidence(object_id: str):
    """Return evidence explorer for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    org_id = session.get("current_org_id", 0)
    from app.founder.workspace_intelligence import build_evidence_explorer
    return jsonify({"success": True, "data": build_evidence_explorer(object_id, organization_id=org_id, identity_id=_identity_id())})


@founder_bp.route("/api/v1/founder/workspace/next-actions/<int:action_id>/complete", methods=["POST"])
@require_permission("task.complete")
def api_complete_next_action(action_id: int):
    """Mark a next action as completed."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import acknowledge_next_action
    result = acknowledge_next_action(action_id)
    return jsonify({"success": result == "completed", "status": result})


@founder_bp.route("/api/v1/founder/workspace/missing-context/<int:context_id>/dismiss", methods=["POST"])
@require_permission("task.edit")
def api_dismiss_missing_context(context_id: int):
    """Dismiss a missing context entry."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import dismiss_missing_context
    result = dismiss_missing_context(context_id)
    return jsonify({"success": result == "addressed", "status": result})


@founder_bp.route("/api/v1/founder/workspace/navigate", methods=["POST"])
@require_permission("rel.create")
def api_workspace_navigate():
    """Navigate between related objects, preserving context."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    from app.founder.workspace_intelligence import navigate_to_object
    identity_id = session.get("identity_id")
    org_id = session.get("current_org_id", 0)
    result = navigate_to_object(
        source_object_id=data.get("source_object_id", ""),
        target_object_id=data.get("target_object_id", ""),
        identity_id=identity_id,
        relationship_type=data.get("relationship_type", "related"),
        context_label=data.get("context_label", ""),
        organization_id=org_id,
    )
    if "error" in result:
        return jsonify({"success": False, "error": result["error"]}), 404
    return jsonify({"success": True, "data": result})


@founder_bp.route("/api/v1/founder/workspace/navigation-history", methods=["GET"])
@require_permission("org.view")
def api_navigation_history():
    """Return navigation history for the current identity."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import get_navigation_history
    identity_id = session.get("identity_id")
    return jsonify({"success": True, "data": get_navigation_history(identity_id)})


# ---------------------------------------------------------------------------
# M5 — AI Copilot API
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/ai/summarize/<object_id>", methods=["GET"])
@require_permission("ai.use")
def api_ai_summarize(object_id: str):
    """Generate an AI summary for a business object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.ai.copilot import generate_entity_summary
    result = generate_entity_summary(object_id)
    return jsonify(result)


@founder_bp.route("/api/v1/founder/ai/health", methods=["GET"])
@require_permission("ai.use")
def api_ai_health():
    """Return AI Copilot health status."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.ai.copilot import copilot_health
    return jsonify({"success": True, "data": copilot_health()})


@founder_bp.route("/api/v1/founder/ai/chat/<conv_id>", methods=["POST"])
@require_permission("ai.use")
def api_ai_chat(conv_id: str):
    """Send a message to the AI Copilot in an existing conversation."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()
    if not content:
        return jsonify({"success": False, "error": "Message is required"}), 400
    from app.ai.copilot import process_message
    result = process_message(conv_id=conv_id, user_message=content)
    if result.get("error"):
        return jsonify({"success": False, "error": result["error"]}), 400
    return jsonify({"success": True, "data": {
        "response": result["response"],
        "model": result.get("model", "unknown"),
        "intent": result.get("intent", "general"),
    }})
