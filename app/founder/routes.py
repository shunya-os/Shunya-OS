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
    session,
    url_for,
)

from app import db
from app.adapters.os_adapter import (
    create_object,
    create_space,
    get_executive_home,
    process_intent,
    sign_in,
)
from app.founder import founder_bp
from app.founder.models import (
    BusinessRelationship,
    FounderConversation,
    FounderMessage,
    FounderObject,
    FounderSpace,
)

# ---------------------------------------------------------------------------
# Helpers (auth only — no business logic)
# ---------------------------------------------------------------------------


def _founder_required() -> bool:
    """Check that the user is authenticated."""
    user_id = session.get("user_id")
    identity_id = session.get("identity_id")
    return bool(user_id and identity_id)


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
    space = FounderSpace.query.filter_by(space_id=space_id, status="active").first()
    if not space:
        return "Space not found", 404
    objects = FounderObject.query.filter_by(
        space_id=space_id, status="active"
    ).order_by(FounderObject.updated_at.desc()).all()
    return render_template("founder_workspace.html",
                           space=space, objects=objects,
                           founder_name=_get_identity_name())


@founder_bp.route("/founder/object/<object_id>")
def founder_object_view(object_id: str):
    if not _founder_required():
        return redirect(url_for("founder.founder_login"))
    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return "Object not found", 404
    space = FounderSpace.query.filter_by(space_id=obj.space_id).first()
    conversation = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()
    messages = []
    if conversation:
        messages = FounderMessage.query.filter_by(
            conv_id=conversation.conv_id
        ).order_by(FounderMessage.created_at).all()
    return render_template("founder_object.html",
                           object=obj, space=space,
                           conversation=conversation, messages=messages,
                           founder_name=_get_identity_name())


@founder_bp.route("/workspace")
def workspace():
    """Serve the single continuous workspace shell."""
    if not _founder_required():
        return redirect(url_for("founder.founder_login"))
    return render_template("workspace.html")


# ---------------------------------------------------------------------------
# API — Sign In (thin: parse HTTP → call OS → serialize)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/signin", methods=["POST"])
def api_founder_signin():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    name = data.get("name", "").strip()

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400

    # Auto-create account on first login (founder becomes User #1)
    from app.auth import TeamMember, UserRole
    existing = TeamMember.query.filter_by(email=email).first()
    if not existing:
        tm = TeamMember(
            name=name or email.split("@")[0],
            email=email,
            role=UserRole.ADMIN.value if email == "admin@shunyaos.com" else UserRole.ADMIN.value,
            is_active=True,
        )
        tm.set_password(password)
        db.session.add(tm)
        db.session.commit()

    # PHASE 1: Check if a TeamMember account exists for this email
    tm = TeamMember.query.filter_by(email=email, is_active=True).first()
    
    if tm:
        # Existing user — MUST validate password
        if not tm.check_password(password):
            return jsonify({"success": False, "error": "Invalid email or password"}), 401
        # Authenticated via TeamMember — use their identity
        try:
            from app.models import OrgMember, Organization
            from sqlalchemy import func
            # Find OrgMember, preferring the one in the largest org
            org_members = OrgMember.query.filter_by(email=email, is_active=True).all()
            if org_members:
                # Count members per org to find the primary org
                org_counts = {}
                for om in org_members:
                    cnt = OrgMember.query.filter_by(organization_id=om.organization_id, is_active=True).count()
                    org_counts[om.organization_id] = cnt
                # Pick the org with most members
                best_org_id = max(org_counts, key=org_counts.get)
                org_member = next(om for om in org_members if om.organization_id == best_org_id)
                identity_id = org_member.identity_id
                session["identity_id"] = identity_id
                session["user_id"] = tm.id
                session["current_org_id"] = org_member.organization_id
                
                # Refresh session
                session.modified = True
                
                response = {
                    "success": True,
                    "redirect": url_for("for2.for2_home"),
                    "name": tm.name,
                    "identity_id": identity_id,
                }
                return jsonify(response)
        except Exception as e:
            pass

        # User authenticated but no org membership exists yet
        session["user_id"] = tm.id
        session.modified = True
        return jsonify({
            "success": True,
            "redirect": url_for("workspace_routes.workspace_home"),
            "name": tm.name,
            "identity_id": "",
        })
    
    # PHASE 2: New user registration — gated flow
    # Unregistered emails are NOT auto-created.
    # Return a clear error directing them to registration.
    return jsonify({
        "success": False, 
        "error": "Account not found. Please check your email or contact your organization administrator to get an invitation."
    }), 404


# ---------------------------------------------------------------------------
# API — Profile (read-only, transitional)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/profile", methods=["GET"])
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
def api_list_spaces():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    # Org-scoped: filter by user's organization
    from app.authz.decorators import _resolve_org_id
    org_id = _resolve_org_id()
    if org_id:
        spaces = FounderSpace.query.filter_by(organization_id=org_id, status="active").order_by(FounderSpace.created_at.desc()).all()
    else:
        spaces = FounderSpace.query.filter_by(identity_id=session.get("identity_id"), status="active").order_by(FounderSpace.created_at.desc()).all()
    return jsonify({"success": True, "data": [s.to_dict() for s in spaces]})


@founder_bp.route("/api/v1/founder/spaces", methods=["POST"])
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
        existing = FounderSpace.query.filter_by(space_id=space_id).first()
        if not existing:
            db_space = FounderSpace(
                space_id=space_id,
                name=name,
                space_type=data.get("space_type", "organization"),
                description=data.get("description", ""),
                identity_id=identity_id,
                member_count=1,
            )
            db.session.add(db_space)
            db.session.commit()
        return jsonify({
            "success": True,
            "data": db_space.to_dict(),
            "redirect": url_for("founder.founder_space_workspace", space_id=space_id),
        }), 201
    return jsonify({"success": False, "error": "Space creation failed"}), 500


@founder_bp.route("/api/v1/founder/spaces/<space_id>", methods=["GET"])
def api_get_space(space_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    space = FounderSpace.query.filter_by(space_id=space_id, status="active").first()
    if not space:
        return jsonify({"success": False, "error": "Space not found"}), 404
    return jsonify({"success": True, "data": space.to_dict()})


# ---------------------------------------------------------------------------
# API — Objects (thin: parse HTTP → call OS → serialize)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/spaces/<space_id>/objects", methods=["GET"])
def api_list_objects(space_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    objects = FounderObject.query.filter_by(
        space_id=space_id, status="active"
    ).order_by(FounderObject.updated_at.desc()).all()
    return jsonify({"success": True, "data": [o.to_dict() for o in objects]})


@founder_bp.route("/api/v1/founder/spaces/<space_id>/objects", methods=["POST"])
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
        # Dual-write: persist to DB for backward compat during migration
        existing = FounderObject.query.filter_by(object_id=obj_id).first()
        if not existing:
            space = FounderSpace.query.filter_by(space_id=space_id, status="active").first()
            if space:
                db_obj = FounderObject(
                    object_id=obj_id,
                    space_id=space_id,
                    object_type=object_type,
                    name=name,
                    content=content,
                    created_by=identity_id,
                )
                db.session.add(db_obj)
                space.updated_at = datetime.now(timezone.utc)
                db.session.commit()
            else:
                return jsonify({"success": False, "error": "Space not found"}), 404

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
def api_get_object(object_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return jsonify({"success": False, "error": "Object not found"}), 404
    return jsonify({"success": True, "data": obj.to_dict()})


# ---------------------------------------------------------------------------
# API — Object Focus (read-only context assembly, transitional)
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/focus/<object_id>", methods=["GET"])
def api_focus_object(object_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return jsonify({"success": False, "error": "Object not found"}), 404

    space = FounderSpace.query.filter_by(space_id=obj.space_id).first()

    related_objects = FounderObject.query.filter(
        FounderObject.space_id == obj.space_id,
        FounderObject.status == "active",
        FounderObject.object_id != object_id,
    ).limit(5).all()
    relationships = [{"object_id": r.object_id, "name": r.name, "type": r.object_type, "relationship": "same_space"} for r in related_objects]

    conversation = FounderConversation.query.filter_by(object_id=object_id, status="active").first()
    messages = []
    if conversation:
        msgs = FounderMessage.query.filter_by(conv_id=conversation.conv_id).order_by(FounderMessage.created_at).all()
        messages = [m.to_dict() for m in msgs]

    ai_parts = []
    if obj.object_type:
        ai_parts.append(f"This is a {obj.object_type.lower()}.")
    if len(messages) > 0:
        msg_count = len(messages)
        ai_parts.append(f"{msg_count // 2} message{'s have' if msg_count // 2 != 1 else ' has'} been exchanged.")
    if space:
        ai_parts.append(f"It belongs to the '{space.name}' space.")
    if relationships:
        ai_parts.append(f"It is connected to {len(relationships)} other object{'s' if len(relationships) != 1 else ''}.")

    return jsonify({
        "success": True,
        "data": {
            "object": obj.to_dict(),
            "space": space.to_dict() if space else None,
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
def api_start_conversation(object_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return jsonify({"success": False, "error": "Object not found"}), 404
    existing = FounderConversation.query.filter_by(object_id=object_id, status="active").first()
    if existing:
        return jsonify({"success": True, "data": existing.to_dict(), "message": "Conversation already exists"})
    identity_id = session.get("identity_id")
    import uuid
    conv_id = f"conv_{uuid.uuid4().hex[:16]}"
    conversation = FounderConversation(conv_id=conv_id, object_id=object_id, title=f"About {obj.name}", identity_id=identity_id)
    db.session.add(conversation)
    db.session.commit()
    return jsonify({"success": True, "data": conversation.to_dict()}), 201


@founder_bp.route("/api/v1/founder/objects/<object_id>/conversation", methods=["GET"])
def api_get_conversation(object_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    conversation = FounderConversation.query.filter_by(object_id=object_id, status="active").first()
    if not conversation:
        return jsonify({"success": True, "data": None})
    messages = FounderMessage.query.filter_by(conv_id=conversation.conv_id).order_by(FounderMessage.created_at).all()
    return jsonify({"success": True, "data": {**conversation.to_dict(), "messages": [m.to_dict() for m in messages]}})


@founder_bp.route("/api/v1/founder/conversations/<conv_id>/messages", methods=["POST"])
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
def api_search():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"success": True, "data": []})
    identity_id = session.get("identity_id")
    user_spaces = FounderSpace.query.filter_by(identity_id=identity_id, status="active").all()
    space_ids = [s.space_id for s in user_spaces]
    if not space_ids:
        return jsonify({"success": True, "data": []})
    results = FounderObject.query.filter(
        FounderObject.space_id.in_(space_ids),
        FounderObject.status == "active",
        FounderObject.name.ilike(f"%{q}%"),
    ).order_by(FounderObject.updated_at.desc()).limit(20).all()
    rel_results = BusinessRelationship.query.filter(
        BusinessRelationship.space_id.in_(space_ids),
        BusinessRelationship.status == "active",
        BusinessRelationship.name.ilike(f"%{q}%"),
    ).order_by(BusinessRelationship.updated_at.desc()).limit(10).all()
    combined = [r.to_dict() for r in results]
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
def api_insights():
    """Return Executive Intelligence: derived insights, attention queue, timeline."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    assert identity_id is not None
    from app.founder.insight_engine import build_insights
    data = build_insights(identity_id=identity_id)
    return jsonify({"success": True, "data": data})


@founder_bp.route("/api/v1/founder/timeline", methods=["GET"])
def api_timeline():
    """Return executive timeline."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    assert identity_id is not None
    from app.founder.insight_engine import build_timeline
    data = build_timeline(identity_id=identity_id)
    return jsonify({"success": True, "data": data})


@founder_bp.route("/api/v1/founder/insights/<insight_id>/lifecycle", methods=["POST"])
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
def api_morning_zero():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    items = []
    spaces = FounderSpace.query.filter_by(identity_id=identity_id, status="active").order_by(FounderSpace.created_at.desc()).all()
    total_objects = 0
    pending_conversations = 0
    for space in spaces:
        objects = FounderObject.query.filter_by(space_id=space.space_id, status="active").order_by(FounderObject.updated_at.desc()).all()
        total_objects += len(objects)
        for obj in objects:
            conv = FounderConversation.query.filter_by(object_id=obj.object_id, status="active").first()
            if conv:
                unread = FounderMessage.query.filter_by(conv_id=conv.conv_id, role="assistant").count()
                human_msgs = FounderMessage.query.filter_by(conv_id=conv.conv_id, role="human").count()
                if unread > 0 and human_msgs > 0:
                    last_msg = FounderMessage.query.filter_by(conv_id=conv.conv_id).order_by(FounderMessage.created_at.desc()).first()
                    preview = last_msg.content[:80] if last_msg else ""
                    items.append({"title": f"{obj.name} — {unread} message{'s' if unread > 1 else ''}", "meta": preview, "priority": "attention", "focus": {"object_id": obj.object_id, "type": "object"}})
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
def api_rel_types():
    return jsonify({"success": True, "data": [
        {"type": "customer", "label": "Customer", "icon": "person"},
        {"type": "supplier", "label": "Supplier", "icon": "box"},
        {"type": "partner", "label": "Partner", "icon": "handshake"},
        {"type": "employee", "label": "Employee", "icon": "badge"},
        {"type": "vendor", "label": "Vendor", "icon": "building"},
    ]})


@founder_bp.route("/api/v1/founder/relationships", methods=["GET"])
def api_list_relationships():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    rel_type = request.args.get("type", "")
    q = request.args.get("q", "")
    spaces = FounderSpace.query.filter_by(identity_id=identity_id, status="active").all()
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
def api_create_relationship():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    rel_type = data.get("rel_type", "customer").strip()
    if not name:
        return jsonify({"success": False, "error": "Name is required."}), 400
    identity_id = session.get("identity_id")
    space = FounderSpace.query.filter_by(identity_id=identity_id, status="active").first()
    if not space:
        space = FounderSpace(space_id=f"spc_{__import__('uuid').uuid4().hex[:16]}", name="My Business", space_type="organization", identity_id=identity_id)
        db.session.add(space)
        db.session.commit()
    import uuid
    rel_id = f"rel_{uuid.uuid4().hex[:24]}"
    tags = data.get("tags", "")
    if isinstance(tags, list):
        tags = ", ".join(tags)
    rel = BusinessRelationship(rel_id=rel_id, space_id=space.space_id, rel_type=rel_type, name=name, email=data.get("email", "").strip(), phone=data.get("phone", "").strip(), company=data.get("company", "").strip(), notes=data.get("notes", "").strip(), tags=tags, created_by=identity_id)
    db.session.add(rel)
    db.session.commit()
    return jsonify({"success": True, "data": rel.to_dict()}), 201


@founder_bp.route("/api/v1/founder/relationships/<rel_id>", methods=["GET"])
def api_get_relationship(rel_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    rel = BusinessRelationship.query.filter_by(rel_id=rel_id, status="active").first()
    if not rel:
        return jsonify({"success": False, "error": "Relationship not found"}), 404
    related_objects = FounderObject.query.filter(FounderObject.space_id == rel.space_id, FounderObject.status == "active").limit(5).all()
    return jsonify({"success": True, "data": {"relationship": rel.to_dict(), "related_objects": [o.to_dict() for o in related_objects]}})


@founder_bp.route("/api/v1/founder/relationships/<rel_id>", methods=["PUT"])
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
def api_list_object_types():
    """List available object types and counts."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from sqlalchemy import func
    rows = db.session.query(
        FounderObject.object_type, func.count(FounderObject.id)
    ).filter_by(status="active").group_by(FounderObject.object_type).all()
    return jsonify({"success": True, "data": {r[0]: r[1] for r in rows}})


@founder_bp.route("/api/v1/founder/objects", methods=["GET"])
def api_list_founder_objects():
    """List objects scoped to the current user's organization."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.authz.decorators import _resolve_org_id
    org_id = _resolve_org_id()
    if org_id:
        # Filter by org's spaces
        space_ids = [s.space_id for s in FounderSpace.query.filter_by(organization_id=org_id).all()]
        if space_ids:
            objs = FounderObject.query.filter(FounderObject.space_id.in_(space_ids), FounderObject.status == "active").order_by(FounderObject.updated_at.desc()).all()
        else:
            objs = []
    else:
        identity = session.get("identity_id") or session.get("user_id") or ""
        objs = FounderObject.query.filter_by(status="active", created_by=str(identity)).order_by(FounderObject.updated_at.desc()).all()
    return jsonify({"success": True, "data": [o.to_dict() for o in objs], "count": len(objs)})


# ---------------------------------------------------------------------------
# M4 — Workspace Intelligence API
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/workspace/<object_id>", methods=["GET"])
def api_workspace_intelligence(object_id: str):
    """Return the complete workspace intelligence for an object.

    Assembles all M4 panels: summary, AI understanding, relationships,
    timeline, conversation, next actions, missing context, health, evidence.
    """
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import build_full_workspace
    result = build_full_workspace(object_id)
    return jsonify({"success": True, "data": result})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/summary", methods=["GET"])
def api_workspace_summary(object_id: str):
    """Return workspace summary for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import build_workspace_summary
    return jsonify({"success": True, "data": build_workspace_summary(object_id)})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/ai-understanding", methods=["GET"])
def api_ai_understanding(object_id: str):
    """Return AI Understanding panel."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import build_ai_understanding
    return jsonify({"success": True, "data": build_ai_understanding(object_id)})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/relationships", methods=["GET"])
def api_workspace_relationships(object_id: str):
    """Return relationship intelligence for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import build_relationship_intelligence
    return jsonify({"success": True, "data": build_relationship_intelligence(object_id)})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/timeline", methods=["GET"])
def api_workspace_timeline(object_id: str):
    """Return activity timeline for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import build_activity_timeline
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"success": True, "data": build_activity_timeline(object_id, limit=limit)})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/conversation", methods=["GET"])
def api_workspace_conversation(object_id: str):
    """Return conversation workspace for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import get_conversation_workspace
    return jsonify({"success": True, "data": get_conversation_workspace(object_id)})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/next-actions", methods=["GET"])
def api_workspace_next_actions(object_id: str):
    """Return next actions for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import build_next_actions
    return jsonify({"success": True, "data": build_next_actions(object_id)})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/missing-context", methods=["GET"])
def api_workspace_missing_context(object_id: str):
    """Return missing context for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import detect_missing_context
    return jsonify({"success": True, "data": detect_missing_context(object_id)})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/health", methods=["GET"])
def api_workspace_health(object_id: str):
    """Return workspace health assessment."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import compute_workspace_health
    return jsonify({"success": True, "data": compute_workspace_health(object_id)})


@founder_bp.route("/api/v1/founder/workspace/<object_id>/evidence", methods=["GET"])
def api_workspace_evidence(object_id: str):
    """Return evidence explorer for an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import build_evidence_explorer
    return jsonify({"success": True, "data": build_evidence_explorer(object_id)})


@founder_bp.route("/api/v1/founder/workspace/next-actions/<int:action_id>/complete", methods=["POST"])
def api_complete_next_action(action_id: int):
    """Mark a next action as completed."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import acknowledge_next_action
    result = acknowledge_next_action(action_id)
    return jsonify({"success": result == "completed", "status": result})


@founder_bp.route("/api/v1/founder/workspace/missing-context/<int:context_id>/dismiss", methods=["POST"])
def api_dismiss_missing_context(context_id: int):
    """Dismiss a missing context entry."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.founder.workspace_intelligence import dismiss_missing_context
    result = dismiss_missing_context(context_id)
    return jsonify({"success": result == "addressed", "status": result})


@founder_bp.route("/api/v1/founder/workspace/navigate", methods=["POST"])
def api_workspace_navigate():
    """Navigate between related objects, preserving context."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    from app.founder.workspace_intelligence import navigate_to_object
    identity_id = session.get("identity_id")
    result = navigate_to_object(
        source_object_id=data.get("source_object_id", ""),
        target_object_id=data.get("target_object_id", ""),
        identity_id=identity_id,
        relationship_type=data.get("relationship_type", "related"),
        context_label=data.get("context_label", ""),
    )
    if "error" in result:
        return jsonify({"success": False, "error": result["error"]}), 404
    return jsonify({"success": True, "data": result})


@founder_bp.route("/api/v1/founder/workspace/navigation-history", methods=["GET"])
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
def api_ai_summarize(object_id: str):
    """Generate an AI summary for a business object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.ai.copilot import generate_entity_summary
    result = generate_entity_summary(object_id)
    return jsonify(result)


@founder_bp.route("/api/v1/founder/ai/health", methods=["GET"])
def api_ai_health():
    """Return AI Copilot health status."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.ai.copilot import copilot_health
    return jsonify({"success": True, "data": copilot_health()})


@founder_bp.route("/api/v1/founder/ai/chat/<conv_id>", methods=["POST"])
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
