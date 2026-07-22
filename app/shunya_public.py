"""SHUNYA — Public Routes & Identity Creation (Milestone E1).

Public-facing routes for the SHUNYA homepage, identity creation,
space selection, and pre-authentication conversation.
"""

import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for

from app import db
from app.auth import TeamMember
from app.auth_routes import login_required

shunya_bp = Blueprint("shunya", __name__)


# ---------------------------------------------------------------------------
# Identity Identifier — immutable internal ID per identity
# ---------------------------------------------------------------------------

def _generate_identity_id() -> str:
    """Generate an immutable internal identity identifier."""
    return f"sid_{uuid.uuid4().hex[:24]}"


# ---------------------------------------------------------------------------
# Homepage — Conversation Before Authentication
# ---------------------------------------------------------------------------


@shunya_bp.route("/")
def home():
    """Serve the SHUNYA homepage with pre-auth thinking surface."""
    # Initialize conversation in session if not present
    if "shunya_conversation" not in session:
        session["shunya_conversation"] = []
        session["shunya_thought_count"] = 0
    return render_template("home.html")


# ---------------------------------------------------------------------------
# Identity Creation
# ---------------------------------------------------------------------------


@shunya_bp.route("/identity/create")
def identity_create_page():
    """Serve the identity creation page."""
    return render_template("identity_create.html")


@shunya_bp.route("/identity/created")
def identity_created_page():
    """Serve the post-creation confirmation page."""
    return render_template("identity_created.html")


@shunya_bp.route("/api/v1/identity/create", methods=["POST"])
def api_create_identity():
    """Create a new SHUNYA Identity (not just an account).

    Every identity receives an immutable internal identifier.
    Identity exists independently of organizations.
    Uses the kernel-compliant IdentityRepository for persistence.
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name:
        return jsonify({"success": False, "error": "What should we call you?"}), 400
    if not email:
        return jsonify({"success": False, "error": "An email address helps us stay in touch."}), 400
    if not password or len(password) < 6:
        return jsonify({"success": False, "error": "Choose a password with at least 6 characters."}), 400

    # Check via IdentityRepository (kernel-compliant)
    from app.production.identity_repository import IdentityRepository
    repo = IdentityRepository()

    existing = repo.find_by_auth("email", email)
    if existing:
        return jsonify({
            "success": False,
            "error": "Someone with this email already has an identity here. Would you like to sign in instead?"
        }), 409

    # Also check legacy TeamMember
    from app.auth import TeamMember
    legacy = TeamMember.query.filter_by(email=email).first()
    if legacy:
        return jsonify({
            "success": False,
            "error": "Someone with this email already has an identity here. Would you like to sign in instead?"
        }), 409

    # Create via IdentityRepository (kernel)
    identity = repo.create(display_name=name, primary_email=email)

    # Add email as an auth method
    repo.add_auth_method(identity.identity_id, "email", email, is_primary=True)

    # Create legacy TeamMember for backward compatibility
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

    # Store in session
    session["user_id"] = legacy_user.id
    session["identity_id"] = identity.identity_id

    return jsonify({
        "success": True,
        "identity_id": identity.identity_id,
        "name": name,
    }), 201


@shunya_bp.route("/api/v1/identity/profile", methods=["GET"])
@login_required
def api_identity_profile():
    """Get the current identity's profile."""
    identity_id = session.get("identity_id")
    if not identity_id:
        return jsonify({"success": False, "error": "No identity found"}), 404

    from app.production.identity_repository import IdentityRepository
    repo = IdentityRepository()
    profile = repo.get_profile(identity_id)
    if not profile:
        return jsonify({"success": False, "error": "Identity not found"}), 404

    return jsonify({"success": True, "data": profile})


@shunya_bp.route("/api/v1/identity/auth-methods", methods=["GET"])
@login_required
def api_list_auth_methods():
    """List all authentication methods for the current identity."""
    identity_id = session.get("identity_id")
    if not identity_id:
        return jsonify({"success": False, "error": "No identity found"}), 404

    from app.production.identity_repository import IdentityRepository
    repo = IdentityRepository()
    methods = repo.get_auth_methods(identity_id)
    return jsonify({"success": True, "data": methods})


@shunya_bp.route("/api/v1/identity/auth-methods/link", methods=["POST"])
@login_required
def api_link_auth_method():
    """Link a new authentication method to the current identity.

    Flow: Detect → Suggest → Verify → Link → Maintain
    This endpoint handles the VERIFY → LINK step.
    """
    identity_id = session.get("identity_id")
    if not identity_id:
        return jsonify({"success": False, "error": "No identity found"}), 404

    data = request.get_json(silent=True) or {}
    method_type = data.get("method_type", "").strip()
    identifier = data.get("identifier", "").strip()
    verification_token = data.get("verification_token", "")

    if not method_type or not identifier:
        return jsonify({
            "success": False,
            "error": "Both method_type and identifier are required."
        }), 400

    from app.production.identity_repository import IdentityRepository
    repo = IdentityRepository()

    # Check this method isn't already linked to another identity
    existing = repo.find_by_auth(method_type, identifier)
    if existing and existing.identity_id != identity_id:
        return jsonify({
            "success": False,
            "error": "This authentication method is already linked to another identity.",
            "suggestion": f"Would you like to verify ownership and link these identities?",
            "detected_identity_id": existing.identity_id,
        }), 409

    # Check if already linked
    if existing and existing.identity_id == identity_id:
        return jsonify({
            "success": False,
            "error": "This authentication method is already linked to your identity.",
        }), 409

    # Add the method (in production, verification_token would be validated)
    success = repo.add_auth_method(identity_id, method_type, identifier)
    if not success:
        return jsonify({"success": False, "error": "Could not link method."}), 500

    # Auto-verify if token provided (simplified for now)
    if verification_token:
        repo.verify_auth_method(identity_id, method_type, identifier)

    return jsonify({
        "success": True,
        "message": "Authentication method linked successfully.",
        "verified": bool(verification_token),
    }), 201


@shunya_bp.route("/api/v1/identity/auth-methods/unlink", methods=["POST"])
@login_required
def api_unlink_auth_method():
    """Remove an authentication method from the current identity.

    Cannot remove the last email-type method.
    """
    identity_id = session.get("identity_id")
    if not identity_id:
        return jsonify({"success": False, "error": "No identity found"}), 404

    data = request.get_json(silent=True) or {}
    method_type = data.get("method_type", "").strip()
    identifier = data.get("identifier", "").strip()

    if not method_type or not identifier:
        return jsonify({"success": False, "error": "Both method_type and identifier are required."}), 400

    # Don't allow removing the last email method
    from app.production.identity_repository import IdentityRepository
    repo = IdentityRepository()
    methods = repo.get_auth_methods(identity_id)
    email_methods = [m for m in methods if m["type"] == "email"]
    if method_type == "email" and len(email_methods) <= 1:
        return jsonify({
            "success": False,
            "error": "Cannot remove your last email method. Add another first."
        }), 400

    success = repo.remove_auth_method(identity_id, method_type, identifier)
    if not success:
        return jsonify({"success": False, "error": "Authentication method not found."}), 404

    return jsonify({"success": True, "message": "Authentication method removed."})


# ---------------------------------------------------------------------------
# Space Selection
# ---------------------------------------------------------------------------


@shunya_bp.route("/space/personal")
def space_personal():
    """Create or enter personal space."""
    if "user_id" not in session:
        return redirect(url_for("shunya.identity_create_page"))
    return redirect(url_for("main.index"))


@shunya_bp.route("/space/organization")
def space_organization():
    """Show organization creation/join page."""
    if "user_id" not in session:
        return redirect(url_for("shunya.identity_create_page"))
    return redirect(url_for("main.index"))


# ---------------------------------------------------------------------------
# Conversation API — Pre-Auth Thinking
# ---------------------------------------------------------------------------


@shunya_bp.route("/api/v1/conversation/think", methods=["POST"])
def api_conversation_think():
    """Process a thought from the pre-auth thinking surface.

    Stores in session. When appropriate, suggests identity creation.
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"success": False, "error": "Nothing to think about?"}), 400

    conv = session.get("shunya_conversation", [])
    conv.append({
        "role": "human",
        "text": text,
        "timestamp": datetime.utcnow().isoformat(),
    })
    session["shunya_conversation"] = conv
    session["shunya_thought_count"] = len(conv)

    # Calm response — always
    response_text = "I hear you."

    # If user has shared multiple thoughts, suggest identity
    suggest_identity = len(conv) >= 2 and "user_id" not in session

    return jsonify({
        "success": True,
        "response": response_text,
        "suggest_identity": suggest_identity,
        "thought_count": len(conv),
    })