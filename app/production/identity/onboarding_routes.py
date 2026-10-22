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

_ONBOARDING: dict = {}  # user_id -> onboarding state (process-local cache only)
# G1.21: the durable store is user_profiles.onboarding_step /
# onboarding_completed_steps. This dict is no longer authoritative — the helpers
# below read/write the database and keep the cache as a same-process shortcut.


def _onboarding_identity(user) -> str:
    """Canonical identity key for persisted onboarding state."""
    return str(
        getattr(user, "identity_id", None)
        or getattr(user, "email", None)
        or getattr(user, "id", "")
    )


def _load_onboarding(user) -> tuple[str, list[str]]:
    """Return (step, completed_steps) from the durable store.

    Falls back to the process cache, then to the first step. A user whose row has
    no persisted state is genuinely "not started" — this never invents progress.
    """
    import json

    from app.profile.models import UserProfile

    key = _onboarding_identity(user)
    profile = db.session.get(UserProfile, key)
    if profile is not None and profile.onboarding_step:
        try:
            completed = json.loads(profile.onboarding_completed_steps or "[]")
        except (TypeError, ValueError):
            completed = []
        return str(profile.onboarding_step), [str(s) for s in completed]

    cached = _ONBOARDING.get(getattr(user, "id", None))
    if cached:
        return str(cached.get("step", "profile")), list(cached.get("completed", []))
    return "profile", []


def _save_onboarding(user, step: str, completed: list[str]) -> None:
    """Persist (step, completed) for the caller, creating the profile if absent."""
    import json

    from app.profile.models import UserProfile

    key = _onboarding_identity(user)
    profile = db.session.get(UserProfile, key)
    if profile is None:
        profile = UserProfile(
            identity_id=key,
            display_name=getattr(user, "name", "") or "",
            email=getattr(user, "email", "") or "",
        )
        db.session.add(profile)
    profile.onboarding_step = step
    profile.onboarding_completed_steps = json.dumps(completed)
    _ONBOARDING[getattr(user, "id", None)] = {"step": step, "completed": completed}
    db.session.commit()

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

    step, completed = _load_onboarding(g.user)
    return jsonify({
        "success": True,
        "data": {
            "current_step": step,
            "completed_steps": completed,
            "all_steps": _ONBOARDING_STEPS,
            "is_complete": step == "complete",
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

    current_step, completed = _load_onboarding(g.user)

    # Add the traversed steps to completed when moving forward
    current_idx = _ONBOARDING_STEPS.index(current_step)
    target_idx = _ONBOARDING_STEPS.index(step)

    if target_idx >= current_idx:
        for i in range(current_idx, target_idx):
            completed_step = _ONBOARDING_STEPS[i]
            if completed_step not in completed:
                completed.append(completed_step)

    # Durable step + traversed list (G1.21): a reload, a new session or another
    # worker resumes here instead of restarting at "profile".
    _save_onboarding(g.user, step, completed)

    # The terminal flag is separate and idempotent.
    if step == "complete" and not g.user.onboarding_completed:
        g.user.onboarding_completed = True
        db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "current_step": step,
            "completed_steps": completed,
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
    email = getattr(user, "email", "") or ""
    # ONE canonical identity, resolved once, in a fixed priority order:
    #   TeamMember.identity_id (sid_*, written at signup/login and by POST /orgs)
    #   → email (legacy rows whose membership was keyed by address)
    #   → the TeamMember id (last resort; never a synthetic identity).
    # G1.21 defect: this used ``str(user.id)`` and then preferred the *email*,
    # but OrgMember.identity_id holds the sid_* canonical id, so onboarding
    # completion resolved no organization for a normal signup and silently seeded
    # zero foundational objects ("objects_created=0 — nothing was seeded").
    identity_id = str(getattr(user, "identity_id", None) or user.id)
    canonical_identity = identity_id or email

    # G1.19: onboarding can only attach foundational objects to an organization
    # that owns a canonical workspace. Organizations created before `POST /orgs`
    # provisioned one (or by an integration) are repaired here — idempotently,
    # and only through the membership-gated provisioning helper, which refuses
    # any identity that is not an active owner/admin of the organization.
    try:
        from app.authz.org_provisioning import ensure_organization_workspace
        from app.models import OrgMember

        for candidate in (identity_id, canonical_identity):
            if not candidate:
                continue
            membership = OrgMember.query.filter_by(
                identity_id=str(candidate), is_active=True
            ).first()
            if membership:
                ensure_organization_workspace(
                    membership.organization_id,
                    str(candidate),
                    name=getattr(membership, "name", "") or "",
                )
                break
    except Exception:  # noqa: BLE001 — repair is best-effort; resolution below
        from flask import current_app

        current_app.logger.warning(
            "onboarding: canonical workspace provisioning skipped for identity=%s",
            identity_id, exc_info=True,
        )

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
        from app.objects.legacy_models import ShunyaObject

        svc = get_object_service()

        # Idempotency (G1.21): completion used to create all 26 placeholders on
        # every call, so a retried/abandoned-and-resubmitted onboarding produced
        # 52, 78, … "customers". Only missing placeholders are created; existing
        # ones are never duplicated, renamed or deleted.
        already = {
            (o.object_type, o.name)
            for o in ShunyaObject.query.filter_by(
                workspace_id=workspace_id, is_deleted=False).all()
        }
        for obj_name, obj_type in FOUNDATIONAL_OBJECTS:
            if (obj_type, obj_name) in already:
                continue
            svc.create(
                object_type=obj_type,
                name=obj_name,
                organization_id=org_id,
                data={"content": ""},
                created_by=identity_id[:12],
                workspace_id=workspace_id,
                identity_id=identity_id,
                # G1.24 (D-1 = B): a provisioned placeholder is NOT user-supplied
                # business data. The marker is written at creation because it
                # cannot be reconstructed afterwards.
                provenance="onboarding_seed",
            )
            objects_created += 1
    else:
        current_app.logger.info(
            "Onboarding complete for identity=%s but no canonical organization/"
            "workspace context — foundational objects not created.", identity_id,
        )

    # Persist the terminal step in the durable resume state as well, so a status
    # read after completion is consistent with the flag.
    _cur_step, _completed = _load_onboarding(user)
    if "complete" not in _completed:
        _completed = list(_ONBOARDING_STEPS)
    from app.profile.models import UserProfile

    _profile_key = _onboarding_identity(user)
    _profile = db.session.get(UserProfile, _profile_key)
    if _profile is None:
        _profile = UserProfile(
            identity_id=_profile_key,
            display_name=getattr(user, "name", "") or "",
            email=email,
        )
        db.session.add(_profile)
    _profile.onboarding_step = "complete"
    import json as _json
    _profile.onboarding_completed_steps = _json.dumps(_completed)

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

    # Clear the durable resume state as well, otherwise the next status read
    # would answer from the database and the reset would silently not apply.
    from app.profile.models import UserProfile

    profile = db.session.get(UserProfile, _onboarding_identity(g.user))
    if profile is not None:
        profile.onboarding_step = None
        profile.onboarding_completed_steps = None

    if g.user.onboarding_completed:
        g.user.onboarding_completed = False
    db.session.commit()
    return jsonify({
        "success": True,
        "data": {"current_step": "profile", "completed_steps": []},
    })