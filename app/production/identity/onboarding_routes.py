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
# Onboarding state — DB-backed completion flag; in-memory dict is a cache
# ---------------------------------------------------------------------------
#
# The AUTHORITATIVE, durable completion state is the DB-backed column
# TeamMember.onboarding_completed (see mark_onboarding_complete /
# check_onboarding_complete below). The _ONBOARDING dict below is only an
# ephemeral per-process cache for in-progress step granularity; it is never
# the source of truth for "has this user completed onboarding" — a restart
# must not lose the completed state (previously the dict WAS the only store
# and a restart silently reset every user to step "profile").

_ONBOARDING: dict = {}  # user_id -> onboarding state (ephemeral step cache)

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
    """Get the current user's onboarding progress.

    Completion is read from the DB flag first (durable across restarts);
    in-progress step granularity falls back to the ephemeral cache.
    """
    from flask import g
    user_id = g.user.id

    if g.user.onboarding_completed:
        return jsonify({
            "success": True,
            "data": {
                "current_step": "complete",
                "completed_steps": list(_ONBOARDING_STEPS),
                "all_steps": _ONBOARDING_STEPS,
                "is_complete": True,
            },
        })

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

    # Persist the terminal state durably: reaching the "complete" step must
    # survive a restart (previously this lived only in the in-memory dict).
    if step == "complete" and not g.user.onboarding_completed:
        g.user.onboarding_completed = True
        db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "current_step": state["step"],
            "completed_steps": state["completed"],
            "is_complete": step == "complete",
        },
    })


@identity_bp.route("/onboarding/complete", methods=["POST"])
@login_required
def mark_onboarding_complete():
    """Mark the current user's onboarding as permanently complete
    and auto-create foundational business objects."""
    from flask import g, current_app
    user = g.user
    user.onboarding_completed = True

    # Canonical ownership context: identity → organization → workspace.
    # Canonical workspace truth is sh_workspaces; a legacy FounderSpace record
    # is not an ownership authority.
    from app.authz.workspace_context import (
        OwnershipContextError, resolve_current_organization,
        resolve_current_workspace,
    )
    identity_id = str(user.id)
    email = getattr(user, "email", "") or ""
    # ONE canonical identity, resolved once. The previous version tried
    # (email, identity_id) in turn and kept whichever happened to resolve,
    # which is arbitrary resolution: two different identities could both be
    # "the caller" depending on data. The canonical identity for authorization
    # is the email when present (that is what OrgMember.identity_id holds),
    # otherwise the user id — and if that single identity has no authorized
    # context, this fails closed rather than silently trying another identity.
    canonical_identity = email or identity_id
    org_id = workspace_id = None
    try:
        org_id = resolve_current_organization(canonical_identity)
        workspace_id = resolve_current_workspace(canonical_identity, org_id)
    except OwnershipContextError:
        org_id = workspace_id = None

    # Auto-create foundational objects (Article XII). Without a canonical
    # organization and workspace there is nothing to attach them to, so none
    # are created — never under a synthetic owner or a default workspace.
    objects_created = 0
    if org_id and workspace_id:
        FOUNDATIONAL_OBJECTS = [
            ("Customer", "customer"),
            ("Supplier", "supplier"),
            ("Lead", "lead"),
            ("Opportunity", "opportunity"),
            ("Proposal", "proposal"),
            ("Invoice", "invoice"),
            ("Payment", "payment"),
            ("Task", "task"),
            ("Meeting", "meeting"),
            ("Document", "document"),
            ("Note", "note"),
            ("Reminder", "reminder"),
            ("Commitment", "commitment"),
            ("Product", "product"),
            ("Service", "service"),
            ("Project", "project"),
            ("Knowledge", "knowledge"),
            ("Calendar Event", "calendar_event"),
            ("Relationship", "relationship"),
            ("Memory", "memory"),
            ("Email", "email"),
            ("WhatsApp", "whatsapp"),
            ("Conversation", "conversation"),
            ("Company", "company"),
            ("Employee", "employee"),
            ("Quote", "quote"),
        ]
        # Canonical object creation via ObjectService (R6B-2 convergence)
        # replaces legacy FounderObject + ShunyaObject dual-write
        from core.object_service import get_object_service
        svc = get_object_service()
        for obj_name, obj_type in FOUNDATIONAL_OBJECTS:
            svc.create(
                object_type=obj_type,
                name=obj_name,
                organization_id=org_id,
                data={"content": ""},
                created_by=identity_id[:12],
                workspace_id=workspace_id,
                identity_id=identity_id,
            )
            objects_created += 1
    else:
        current_app.logger.info(
            "Onboarding complete for identity=%s but no canonical organization/"
            "workspace context — foundational objects not created.", identity_id,
        )

    db.session.commit()
    if objects_created == 0:
        current_app.logger.info(
            "Onboarding complete for identity=%s resolved org=%s workspace=%s "
            "— objects_created=0 (nothing was seeded).",
            identity_id, org_id, workspace_id,
        )
    return jsonify({
        "success": True,
        "data": {"onboarding_completed": True,
                 "objects_created": objects_created},
    })


@identity_bp.route("/onboarding/check", methods=["GET"])
@login_required
def check_onboarding_complete():
    """Check if the current user has completed onboarding."""
    from flask import g
    return jsonify({
        "success": True,
        "data": {"onboarding_completed": bool(g.user.onboarding_completed)},
    })


@identity_bp.route("/onboarding/reset", methods=["POST"])
@login_required
def reset_onboarding():
    """Reset onboarding progress for a user."""
    from flask import g
    user_id = g.user.id
    _ONBOARDING.pop(user_id, None)
    if g.user.onboarding_completed:
        g.user.onboarding_completed = False
        db.session.commit()
    return jsonify({
        "success": True,
        "data": {"current_step": "profile", "completed_steps": []},
    })