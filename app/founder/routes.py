"""SHUNYA — Founder Experience Routes.

Implements the complete Founder Journey:
  Sign in → Founder Home → Create Space → Enter Space →
  Create Object → Open Object → Converse → Search → Reopen → Logout
"""
import uuid
import json
from datetime import datetime

from flask import (
    Blueprint, render_template, request, jsonify, session,
    redirect, url_for, g, current_app,
)
from sqlalchemy import or_

from app import db
from app.founder import founder_bp
from app.founder.models import FounderSpace, FounderObject, FounderConversation, FounderMessage
from app.kernel.space import Space, SpaceType, SpaceRole, get_space_store, get_space_store
from app.kernel.object import UniversalObject, ObjectRegistry, get_registry
from app.kernel.identity import (
    SHUNYAIdentity, AuthenticationMethod, AuthMethodType,
    get_identity_store,
)
from app.kernel.relationship import Relationship, RelationshipType, get_relationship_engine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_id(prefix: str = "obj") -> str:
    """Generate a unique ID with prefix."""
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    rand = uuid.uuid4().hex[:16]
    return f"{prefix}_{timestamp:016x}{rand}"


def _founder_required():
    """Check that the user is authenticated with a SHUNYA identity."""
    user_id = session.get("user_id")
    identity_id = session.get("identity_id")
    if not user_id or not identity_id:
        return False
    return True


def _get_identity() -> SHUNYAIdentity | None:
    """Get the current SHUNYAIdentity from the kernel store."""
    identity_id = session.get("identity_id")
    if not identity_id:
        return None
    from app.production.identity_repository import IdentityRepository
    repo = IdentityRepository()
    return repo.get(identity_id)


def _get_identity_name() -> str:
    """Get the current user's display name."""
    user_id = session.get("user_id")
    if user_id:
        from app.auth import TeamMember
        user = db.session.get(TeamMember, user_id)
        if user:
            return user.name
    identity_id = session.get("identity_id")
    if identity_id:
        from app.production.identity_repository import IdentityRepository
        repo = IdentityRepository()
        profile = repo.get_profile(identity_id)
        if profile:
            return profile.get("display_name", "Founder")
    return "Founder"


# ---------------------------------------------------------------------------
# HTML Pages
# ---------------------------------------------------------------------------


@founder_bp.route("/founder/home")
def founder_home():
    """Founder Home — the first page after authentication."""
    if not _founder_required():
        return redirect(url_for("founder.founder_login"))
    spaces = FounderSpace.query.filter_by(
        identity_id=session.get("identity_id"),
        status="active",
    ).order_by(FounderSpace.created_at.desc()).all()
    return render_template("founder_home.html",
                           spaces=spaces,
                           founder_name=_get_identity_name())


@founder_bp.route("/founder/login")
def founder_login():
    """SHUNYA login page."""
    if _founder_required():
        return redirect(url_for("founder.founder_home"))
    return render_template("founder_login.html")


@founder_bp.route("/founder/space/create")
def founder_space_create():
    """Create a new Space."""
    if not _founder_required():
        return redirect(url_for("founder.founder_login"))
    return render_template("founder_space_create.html",
                           founder_name=_get_identity_name())


@founder_bp.route("/founder/space/<space_id>")
def founder_space_workspace(space_id: str):
    """Enter a Space — see its workspace with objects."""
    if not _founder_required():
        return redirect(url_for("founder.founder_login"))
    space = FounderSpace.query.filter_by(space_id=space_id, status="active").first()
    if not space:
        return "Space not found", 404
    objects = FounderObject.query.filter_by(
        space_id=space_id, status="active"
    ).order_by(FounderObject.updated_at.desc()).all()
    return render_template("founder_workspace.html",
                           space=space,
                           objects=objects,
                           founder_name=_get_identity_name())


@founder_bp.route("/founder/object/<object_id>")
def founder_object_view(object_id: str):
    """Open an Object and see its conversation."""
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
                           object=obj,
                           space=space,
                           conversation=conversation,
                           messages=messages,
                           founder_name=_get_identity_name())


# ---------------------------------------------------------------------------
# API — Sign In
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/signin", methods=["POST"])
def api_founder_signin():
    """Sign in with email + password. Creates identity if not exists (self-service)."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400

    # Try legacy auth first (table may not exist yet in fresh DB)
    from app.auth import TeamMember
    user = None
    try:
        user = TeamMember.query.filter_by(email=email, is_active=True).first()
    except Exception:
        pass  # Table not ready yet — will create below

    if user and user.check_password(password):
        session["user_id"] = user.id
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Ensure identity exists in kernel
        from app.production.identity_repository import IdentityRepository
        repo = IdentityRepository()
        identity = repo.find_by_auth("email", email)
        if not identity:
            identity = repo.create(display_name=user.name or email.split("@")[0],
                                   primary_email=email)
            repo.add_auth_method(identity.identity_id, "email", email, is_primary=True)
        session["identity_id"] = identity.identity_id
        return jsonify({
            "success": True,
            "redirect": url_for("founder.founder_home"),
            "name": user.name or "Founder",
        })

    # No user found — auto-create (self-service signup)
    name = data.get("name", email.split("@")[0]).strip()
    if not name:
        name = email.split("@")[0]

    from app.production.identity_repository import IdentityRepository
    repo = IdentityRepository()

    # Check if identity already exists
    existing = repo.find_by_auth("email", email)
    if existing:
        return jsonify({
            "success": False,
            "error": "An identity with this email already exists. Please sign in."
        }), 409

    # Create identity
    identity = repo.create(display_name=name, primary_email=email)
    repo.add_auth_method(identity.identity_id, "email", email, is_primary=True)

    # Create legacy user for session
    legacy_user = None
    try:
        legacy_user = TeamMember(
            name=name,
            email=email,
            role="admin",
            is_active=True,
        )
        legacy_user.set_password(password)
        legacy_user.generate_token()
        db.session.add(legacy_user)
        db.session.commit()
        session["user_id"] = legacy_user.id
    except Exception:
        # Legacy table not available — use identity_id as user_id
        session["user_id"] = identity.identity_id
    session["identity_id"] = identity.identity_id

    return jsonify({
        "success": True,
        "redirect": url_for("founder.founder_home"),
        "name": name,
        "is_new": True,
    }), 201


# ---------------------------------------------------------------------------
# API — Spaces
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/spaces", methods=["GET"])
def api_list_spaces():
    """List all spaces for the current identity."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    spaces = FounderSpace.query.filter_by(
        identity_id=session.get("identity_id"),
        status="active",
    ).order_by(FounderSpace.created_at.desc()).all()
    return jsonify({
        "success": True,
        "data": [s.to_dict() for s in spaces],
    })


@founder_bp.route("/api/v1/founder/spaces", methods=["POST"])
def api_create_space():
    """Create a new Space — persists to both kernel SpaceStore and DB."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    space_type = data.get("space_type", "organization")
    description = data.get("description", "")

    if not name:
        return jsonify({"success": False, "error": "Space name is required."}), 400

    identity_id = session.get("identity_id")

    # Create in kernel SpaceStore
    kernel_store = get_space_store()
    kernel_space = kernel_store.create(
        name=name,
        space_type=space_type,
        owner_id=identity_id,
        description=description,
    )

    # Persist to DB
    space_id = kernel_space.space_id
    db_space = FounderSpace(
        space_id=space_id,
        name=name,
        space_type=space_type,
        description=description,
        identity_id=identity_id,
        member_count=1,
    )
    db.session.add(db_space)
    db.session.commit()

    # Add relationship
    engine = get_relationship_engine()
    engine.add(Relationship(
        source_id=identity_id,
        target_id=space_id,
        relationship_type=RelationshipType.OWNS.value,
        label=f"owns {name}",
    ))

    return jsonify({
        "success": True,
        "data": db_space.to_dict(),
        "redirect": url_for("founder.founder_space_workspace", space_id=space_id),
    }), 201


@founder_bp.route("/api/v1/founder/spaces/<space_id>", methods=["GET"])
def api_get_space(space_id: str):
    """Get a single space."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    space = FounderSpace.query.filter_by(space_id=space_id, status="active").first()
    if not space:
        return jsonify({"success": False, "error": "Space not found"}), 404
    return jsonify({"success": True, "data": space.to_dict()})


# ---------------------------------------------------------------------------
# API — Objects
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/spaces/<space_id>/objects", methods=["GET"])
def api_list_objects(space_id: str):
    """List all objects in a space."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    objects = FounderObject.query.filter_by(
        space_id=space_id, status="active"
    ).order_by(FounderObject.updated_at.desc()).all()
    return jsonify({
        "success": True,
        "data": [o.to_dict() for o in objects],
    })


@founder_bp.route("/api/v1/founder/spaces/<space_id>/objects", methods=["POST"])
def api_create_object(space_id: str):
    """Create a new Object in a space."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    object_type = data.get("object_type", "Document")
    content = data.get("content", "")

    if not name:
        return jsonify({"success": False, "error": "Object name is required."}), 400

    # Verify space exists
    space = FounderSpace.query.filter_by(space_id=space_id, status="active").first()
    if not space:
        return jsonify({"success": False, "error": "Space not found"}), 404

    identity_id = session.get("identity_id")

    # Create kernel object
    obj_id = _generate_id("obj")
    kernel_obj = UniversalObject(
        object_id=obj_id,
        space_id=space_id,
        object_type=object_type,
        name=name,
        created_by=identity_id,
    )

    # Persist to DB
    db_obj = FounderObject(
        object_id=obj_id,
        space_id=space_id,
        object_type=object_type,
        name=name,
        content=content,
        created_by=identity_id,
    )
    db.session.add(db_obj)

    # Update space's updated_at
    space.updated_at = datetime.utcnow()
    db.session.commit()

    # Add relationship
    engine = get_relationship_engine()
    engine.add(Relationship(
        source_id=identity_id,
        target_id=obj_id,
        relationship_type=RelationshipType.CREATED.value,
        label=f"created {name}",
    ))
    engine.add(Relationship(
        source_id=obj_id,
        target_id=space_id,
        relationship_type=RelationshipType.PART_OF.value,
        label=f"part of {space.name}",
    ))

    return jsonify({
        "success": True,
        "data": db_obj.to_dict(),
        "redirect": url_for("founder.founder_object_view", object_id=obj_id),
    }), 201


@founder_bp.route("/api/v1/founder/objects/<object_id>", methods=["GET"])
def api_get_object(object_id: str):
    """Get a single object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return jsonify({"success": False, "error": "Object not found"}), 404
    return jsonify({"success": True, "data": obj.to_dict()})


# ---------------------------------------------------------------------------
# API — Conversations
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/objects/<object_id>/conversation", methods=["POST"])
def api_start_conversation(object_id: str):
    """Start a new conversation attached to an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    obj = FounderObject.query.filter_by(object_id=object_id, status="active").first()
    if not obj:
        return jsonify({"success": False, "error": "Object not found"}), 404

    # Check if conversation already exists
    existing = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()
    if existing:
        return jsonify({
            "success": True,
            "data": existing.to_dict(),
            "message": "Conversation already exists",
        })

    identity_id = session.get("identity_id")
    conv_id = _generate_id("conv")

    conversation = FounderConversation(
        conv_id=conv_id,
        object_id=object_id,
        title=f"About {obj.name}",
        identity_id=identity_id,
    )
    db.session.add(conversation)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": conversation.to_dict(),
    }), 201


@founder_bp.route("/api/v1/founder/objects/<object_id>/conversation", methods=["GET"])
def api_get_conversation(object_id: str):
    """Get the conversation attached to an object."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    conversation = FounderConversation.query.filter_by(
        object_id=object_id, status="active"
    ).first()
    if not conversation:
        return jsonify({"success": True, "data": None})

    messages = FounderMessage.query.filter_by(
        conv_id=conversation.conv_id
    ).order_by(FounderMessage.created_at).all()

    return jsonify({
        "success": True,
        "data": {
            **conversation.to_dict(),
            "messages": [m.to_dict() for m in messages],
        },
    })


@founder_bp.route("/api/v1/founder/conversations/<conv_id>/messages", methods=["POST"])
def api_send_message(conv_id: str):
    """Send a message in a conversation. Returns a calm response."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()

    if not content:
        return jsonify({"success": False, "error": "Message content is required."}), 400

    conversation = FounderConversation.query.filter_by(
        conv_id=conv_id, status="active"
    ).first()
    if not conversation:
        return jsonify({"success": False, "error": "Conversation not found"}), 404

    # Store human message
    human_msg = FounderMessage(
        conv_id=conv_id,
        role="human",
        content=content,
    )
    db.session.add(human_msg)

    # Generate calm assistant response
    name = _get_identity_name()
    response_text = (
        f"I hear you, {name}. "
        "I've noted your thoughts on this object. "
        "What else would you like to explore?"
    )
    assistant_msg = FounderMessage(
        conv_id=conv_id,
        role="assistant",
        content=response_text,
    )
    db.session.add(assistant_msg)

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "human": human_msg.to_dict(),
            "assistant": assistant_msg.to_dict(),
        },
    }), 201


# ---------------------------------------------------------------------------
# API — Search
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/search", methods=["GET"])
def api_search():
    """Search objects by name."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"success": True, "data": []})

    # Search in objects the user has access to (via their spaces)
    identity_id = session.get("identity_id")
    user_spaces = FounderSpace.query.filter_by(
        identity_id=identity_id, status="active"
    ).all()
    space_ids = [s.space_id for s in user_spaces]

    if not space_ids:
        return jsonify({"success": True, "data": []})

    results = FounderObject.query.filter(
        FounderObject.space_id.in_(space_ids),
        FounderObject.status == "active",
        FounderObject.name.ilike(f"%{q}%"),
    ).order_by(FounderObject.updated_at.desc()).limit(20).all()

    return jsonify({
        "success": True,
        "data": [r.to_dict() for r in results],
    })


# ---------------------------------------------------------------------------
# API — Logout
# ---------------------------------------------------------------------------


@founder_bp.route("/founder/logout", methods=["POST", "GET"])
def founder_logout():
    """Log out and clear session."""
    session.clear()
    return redirect(url_for("founder.founder_login"))


# ---------------------------------------------------------------------------
# API — Identity Profile
# ---------------------------------------------------------------------------


@founder_bp.route("/api/v1/founder/profile", methods=["GET"])
def api_founder_profile():
    """Get current founder profile."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    return jsonify({
        "success": True,
        "data": {
            "name": _get_identity_name(),
            "identity_id": session.get("identity_id"),
        },
    })