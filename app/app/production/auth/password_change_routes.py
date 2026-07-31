"""SHUNYA — Password Change (Self-Service).

Allows an authenticated user to change their own password
by providing their current password and a new password.
"""

from flask import jsonify, request, session
from werkzeug.exceptions import BadRequest

from app import db
from app.auth import TeamMember
from app.auth_routes import auth_bp


@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    """Change the authenticated user's password.

    Requires current_password and new_password in the request body.
    The user must be authenticated via session.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    user = db.session.get(TeamMember, user_id)
    if not user or not user.is_active:
        return jsonify({"success": False, "error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password:
        raise BadRequest("'current_password' is required")

    if not new_password or len(new_password) < 6:
        raise BadRequest("'new_password' must be at least 6 characters")

    if not user.check_password(current_password):
        return jsonify({"success": False, "error": "Current password is incorrect"}), 403

    user.set_password(new_password)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Password changed successfully",
    })