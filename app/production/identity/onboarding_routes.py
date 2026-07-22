"""SHUNYA — User Onboarding API (Milestone X, D1.6).

Guided onboarding workflow for new users.
Tracks progress through setup steps.
"""

from datetime import datetime

from flask import request, jsonify, session
from werkzeug.exceptions import NotFound, BadRequest

from app import db
from app.auth_routes import login_required
from app.production.identity import identity_bp

# ---------------------------------------------------------------------------
# Onboarding state — in-memory store per user
# ---------------------------------------------------------------------------

_ONBOARDING: dict = {}  # user_id -> onboarding state

_ONBOARDING_STEPS = [
    "profile",       # Complete personal profile
    "org_setup",     # Create or join organization
    "invite_team",   # Invite team members
    "workspace",     # Configure workspace
    "complete",      # Onboarding finished
]


@identity_bp.route("/onboarding/status", methods=["GET"])
@login_required
def get_onboarding_status():
    """Get the current user's onboarding progress."""
    from flask import g
    user_id = g.user.id

    state = _ONBOARDING.get(user_id, {"step": "profile", "completed": []})
    return jsonify({
        "success": True,
        "data": {
            "current_step": state["step"],
            "completed_steps": state["completed"],
            "all_steps": _ONBOARDING_STEPS,
            "is_complete": state.get("step") == "complete",
        },
    })


@identity_bp.route("/onboarding/step/<step>", methods=["PUT"])
@login_required
def update_onboarding_step(step: str):
    """Advance or set the onboarding step."""
    from flask import g
    user_id = g.user.id

    if step not in _ONBOARDING_STEPS:
        raise BadRequest(f"Invalid step '{step}'. Valid steps: {_ONBOARDING_STEPS}")

    state = _ONBOARDING.get(user_id, {"step": "profile", "completed": []})

    # Add the current step to completed if moving forward
    current_idx = _ONBOARDING_STEPS.index(state["step"])
    target_idx = _ONBOARDING_STEPS.index(step)

    if target_idx >= current_idx:
        for i in range(current_idx, target_idx):
            completed_step = _ONBOARDING_STEPS[i]
            if completed_step not in state["completed"]:
                state["completed"].append(completed_step)

    state["step"] = step
    _ONBOARDING[user_id] = state

    return jsonify({
        "success": True,
        "data": {
            "current_step": state["step"],
            "completed_steps": state["completed"],
            "is_complete": step == "complete",
        },
    })


@identity_bp.route("/onboarding/reset", methods=["POST"])
@login_required
def reset_onboarding():
    """Reset onboarding progress for a user."""
    from flask import g
    user_id = g.user.id
    _ONBOARDING.pop(user_id, None)
    return jsonify({
        "success": True,
        "data": {"current_step": "profile", "completed_steps": []},
    })