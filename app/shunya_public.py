"""SHUNYA — Public Routes & Identity Creation (Milestone E1).

Public-facing routes for the SHUNYA homepage, identity creation,
space selection, and pre-authentication conversation.
"""

import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_from_directory

from app import db
from app.auth import TeamMember
from app.auth_routes import login_required
from app.authz.decorators import session_required

shunya_bp = Blueprint("shunya", __name__)

# Canonical frontend is the React SPA (public HomePage handles anonymous visitors).
_SPA_INDEX = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "index.html")


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
    # The React SPA has a public HomePage — serve the shell for unauthenticated visitors.
    return send_from_directory(os.path.dirname(_SPA_INDEX), "index.html")


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
        identity_id=identity.identity_id,  # Link to canonical identity
    )
    legacy_user.set_password(password)
    legacy_user.generate_token()
    db.session.add(legacy_user)
    db.session.commit()

    # Store in session
    session["user_id"] = legacy_user.id
    session["identity_id"] = identity.identity_id

    # Verification: the account is created UNVERIFIED on purpose (verified gate
    # blocks login until the inbox is proven). Previously no verify_token was
    # minted and no email was sent — the next login was blocked forever.
    # Mirror api_signup: mint a token and email it AFTER the session grant so
    # the immediate flow keeps working while the user can verify and log in
    # later.
    import secrets
    legacy_user.verify_token = secrets.token_hex(32)
    db.session.commit()
    try:
        from app.email_service import build_verification_email, send_email
        subject, body = build_verification_email(email, legacy_user.verify_token)
        send_email(to=email, subject=subject, body=body,
                   notification_type="email_verification",
                   business_event_id=f"verify:{legacy_user.id}:{legacy_user.verify_token[:8]}",
                   category="security")
    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            "Failed to send verification email to %s", email)

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
@login_required
def space_personal():
    """Create or enter personal space."""
    if "user_id" not in session:
        return redirect(url_for("shunya.identity_create_page"))
    return redirect(url_for("main.index"))


@shunya_bp.route("/space/organization")
@login_required
def space_organization():
    """Show organization creation/join page."""
    if "user_id" not in session:
        return redirect(url_for("shunya.identity_create_page"))
    return redirect(url_for("main.index"))


# ---------------------------------------------------------------------------
# Conversation API — Pre-Auth Thinking
# ---------------------------------------------------------------------------


@shunya_bp.route("/api/v1/conversation/think", methods=["POST"])
@session_required
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
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

# ── MX-01 Phase 1 Audit PDF ──
import os as _os

@shunya_bp.route("/audit/mx01-phase1")
def serve_mx01_audit():
    """Serve MX-01 Phase 1 Migration Audit PDF."""
    pdf_path = _os.path.join(_os.path.dirname(__file__), "..", "audit", "MX-01_PHASE1_AUDIT.pdf")
    if not _os.path.exists(pdf_path):
        return jsonify({"success": False, "error": "Audit PDF not found"}), 404
    from flask import send_file
    return send_file(pdf_path, mimetype="application/pdf", as_attachment=False)

@shunya_bp.route("/audit/mx01a")
def serve_mx01a_audit():
    """Serve MX-01A Dependency & Experience Audit PDF."""
    pdf_path = _os.path.join(_os.path.dirname(__file__), "..", "audit", "MX-01A_DEPENDENCY_AUDIT.pdf")
    if not _os.path.exists(pdf_path):
        return jsonify({"success": False, "error": "MX-01A audit PDF not found"}), 404
    from flask import send_file
    return send_file(pdf_path, mimetype="application/pdf", as_attachment=False)

@shunya_bp.route("/audit/lx06")
def serve_lx06_report():
    """Serve LX-06 Architectural Convergence Report PDF."""
    pdf_path = _os.path.join(_os.path.dirname(__file__), "..", "audit", "LX-06_CONVERGENCE.pdf")
    if not _os.path.exists(pdf_path):
        return jsonify({"success": False, "error": "LX-06 report not found"}), 404
    from flask import send_file
    return send_file(pdf_path, mimetype="application/pdf", as_attachment=False)

@shunya_bp.route("/audit/lx06/frontend")
def serve_lx06_frontend_duplication_map():
    """Serve LX-06 Frontend Duplication Map PDF."""
    pdf_path = _os.path.join(_os.path.dirname(__file__), "..", "audit", "LX-06_FRONTEND_DUPLICATION_MAP.pdf")
    if not _os.path.exists(pdf_path):
        return jsonify({"success": False, "error": "LX-06 Frontend Duplication Map not found"}), 404
    from flask import send_file
    return send_file(pdf_path, mimetype="application/pdf", as_attachment=False)

@shunya_bp.route("/audit/lx06/backend")
def serve_lx06_backend_duplication_report():
    """Serve LX-06 Backend Duplication Report PDF."""
    pdf_path = _os.path.join(_os.path.dirname(__file__), "..", "audit", "LX-06_BACKEND_DUPLICATION_REPORT.pdf")
    if not _os.path.exists(pdf_path):
        return jsonify({"success": False, "error": "LX-06 Backend Duplication Report not found"}), 404
    from flask import send_file
    return send_file(pdf_path, mimetype="application/pdf", as_attachment=False)

@shunya_bp.route("/audit/lx06a")
def serve_lx06a_canonical_architecture():
    """Serve LX-06A Canonical SHUNYA Architecture PDF."""
    pdf_path = _os.path.join(_os.path.dirname(__file__), "..", "audit", "LX-06A_CANONICAL_ARCHITECTURE.pdf")
    if not _os.path.exists(pdf_path):
        return jsonify({"success": False, "error": "LX-06A Canonical Architecture not found"}), 404
    from flask import send_file
    return send_file(pdf_path, mimetype="application/pdf", as_attachment=False)

@shunya_bp.route("/audit/pattern-language")
def serve_pattern_language():
    """Serve SHUNYA Pattern Language PDF."""
    pdf_path = _os.path.join(_os.path.dirname(__file__), "..", "audit", "SHUNYA_PATTERN_LANGUAGE.pdf")
    if not _os.path.exists(pdf_path):
        return jsonify({"success": False, "error": "SHUNYA Pattern Language not found"}), 404
    from flask import send_file
    return send_file(pdf_path, mimetype="application/pdf", as_attachment=False)

@shunya_bp.route("/audit/engineering-constitution")
def serve_engineering_constitution():
    """Serve SHUNYA Engineering Constitution PDF."""
    pdf_path = _os.path.join(_os.path.dirname(__file__), "..", "audit", "ENGINEERING_CONSTITUTION.pdf")
    if not _os.path.exists(pdf_path):
        return jsonify({"success": False, "error": "SHUNYA Engineering Constitution not found"}), 404
    from flask import send_file
    return send_file(pdf_path, mimetype="application/pdf", as_attachment=False)

# ---------------------------------------------------------------------------
# Generic audit PDF serving — constitutional default for all reports.
# URL convention: /audit/<slug>  where <slug> is the PDF filename (case-insensitive)
# without the .pdf extension. e.g. /audit/cdr-001 → CDR-001.pdf
# Specific routes above take precedence; this catches everything else.
# ---------------------------------------------------------------------------

@shunya_bp.route("/audit/cdr-001")
def serve_cdr_001():
    """Serve Constitutional Discovery Report CDR-001 PDF."""
    pdf_path = _os.path.join(_os.path.dirname(__file__), "..", "audit", "CDR-001.pdf")
    if not _os.path.exists(pdf_path):
        return jsonify({"success": False, "error": "CDR-001 not found"}), 404
    from flask import send_file
    return send_file(pdf_path, mimetype="application/pdf", as_attachment=False)

@shunya_bp.route("/audit/<path:slug>")
def serve_audit_pdf(slug):
    """Serve any PDF in the audit directory by filename slug (case-insensitive).

    Converts the URL slug to a canonical PDF filename and serves it. This is the
    constitutional default for all future reports so no new route is required.
    """
    audit_dir = _os.path.join(_os.path.dirname(__file__), "..", "audit")
    # Normalize: strip extension if provided, then case-insensitive match
    base = slug if slug.endswith(".pdf") else slug + ".pdf"
    target = _os.path.join(audit_dir, _os.path.basename(base))
    if not _os.path.exists(target):
        # case-insensitive fallback
        for f in _os.listdir(audit_dir):
            if f.lower() == base.lower() and f.endswith(".pdf"):
                target = _os.path.join(audit_dir, f)
                break
        else:
            from flask import current_app
            current_app.logger.warning("audit PDF not found: %s", slug)
            return jsonify({"success": False, "error": "PDF not found"}), 404
    from flask import send_file
    return send_file(target, mimetype="application/pdf", as_attachment=False)


# ---------------------------------------------------------------------------
# Token-gated proposal view/accept/decline
# The share token IS the capability — no session required. All rendered
# content is HTML-escaped; transitions reuse the canonical commercial
# service so the state machine and audit trail stay identical to the
# authenticated path.
# ---------------------------------------------------------------------------

_PROPOSAL_STATUS_LABELS = {
    "draft": "Draft", "ai_generating": "AI generating", "review": "In review",
    "sent": "Sent", "viewed": "Viewed", "negotiating": "Negotiating",
    "accepted": "Accepted", "declined": "Declined", "withdrawn": "Withdrawn",
    "expired": "Expired",
}

_PROPOSAL_PAGE_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       background: #F7F5F0; color: #1A1C1D; margin: 0; padding: 0; }
.wrap { max-width: 640px; margin: 48px auto; padding: 0 20px; }
.card { background: #fff; border: 1px solid rgba(26,28,29,0.08); border-radius: 12px;
        padding: 28px; }
.badge { display: inline-block; font-size: 12px; font-weight: 600; padding: 3px 10px;
         border-radius: 999px; background: rgba(108,74,226,0.08); color: #6C4AE2; }
h1 { font-size: 22px; font-weight: 600; margin: 12px 0 4px; }
.meta { color: rgba(26,28,29,0.55); font-size: 13px; margin-bottom: 18px; }
.section { margin: 14px 0; }
.section h3 { font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em;
              color: rgba(26,28,29,0.4); margin: 0 0 4px; }
.section p { font-size: 14px; line-height: 1.55; margin: 0; white-space: pre-wrap; }
.value { font-size: 24px; font-weight: 600; margin: 8px 0 18px; }
.actions { display: flex; gap: 10px; margin-top: 22px; }
.btn { flex: 1; text-align: center; padding: 11px 16px; border-radius: 8px;
       font-size: 14px; font-weight: 600; cursor: pointer; border: 1px solid transparent;
       text-decoration: none; font-family: inherit; }
.btn-accept { background: #2D6A4F; color: #fff; }
.btn-decline { background: #fff; color: #B91C1C; border-color: rgba(185,28,28,0.35); }
.btn-done { background: rgba(45,106,79,0.1); color: #2D6A4F; }
.btn-declined { background: rgba(185,28,28,0.08); color: #B91C1C; }
.msg { margin-top: 14px; font-size: 14px; padding: 10px 14px; border-radius: 8px; }
.msg-ok { background: rgba(45,106,79,0.08); color: #2D6A4F; }
.msg-err { background: rgba(185,28,28,0.08); color: #B91C1C; }
.foot { text-align: center; color: rgba(26,28,29,0.35); font-size: 11px; margin-top: 18px; }
"""


def _find_proposal_by_token(token: str):
    from app.commercial.models import CommercialProposal
    return CommercialProposal.query.filter_by(share_token=token).first()


def _proposal_page(proposal, message: str = "", error: str = "") -> str:
    from html import escape
    title = escape(proposal.title or "Proposal")
    status = _PROPOSAL_STATUS_LABELS.get(proposal.status, proposal.status or "")
    status_esc = escape(status)
    currency = escape(proposal.currency or "INR")
    total = proposal.total_value if proposal.total_value is not None else 0
    try:
        value = f"{currency} {float(total):,.2f}"
    except (TypeError, ValueError):
        value = f"{currency} {total}"
    value_esc = escape(value)
    scope = escape((proposal.scope_description or "No scope provided.")[:2000])
    terms = escape((proposal.terms or "")[:2000])
    meta_bits = []
    if proposal.valid_until:
        meta_bits.append(f"Valid until {escape(proposal.valid_until.strftime('%d %b %Y'))}")
    if proposal.proposal_type:
        meta_bits.append(escape(proposal.proposal_type))
    meta = " · ".join(meta_bits)

    action_html = ""
    if proposal.status in ("sent", "viewed", "negotiating"):
        # "viewed" keeps the buttons too: the first open auto-advances
        # sent → viewed (proposal_share_view), and the counterparty must
        # still be able to accept/decline on that same page load.
        action_html = (
            f'<div class="actions">'
            f'<form method="post" action="/proposal/{escape(proposal.share_token)}/accept" style="flex:1">'
            f'<button class="btn btn-accept" type="submit">Accept</button></form>'
            f'<form method="post" action="/proposal/{escape(proposal.share_token)}/decline" style="flex:1">'
            f'<button class="btn btn-decline" type="submit">Decline</button></form>'
            f'</div>'
        )
    elif proposal.status == "accepted":
        action_html = '<div class="actions"><div class="btn btn-done">Accepted — thank you</div></div>'
    elif proposal.status == "declined":
        action_html = '<div class="actions"><div class="btn btn-declined">Declined</div></div>'

    msg_html = ""
    if message:
        msg_html = f'<div class="msg msg-ok">{escape(message)}</div>'
    if error:
        msg_html = f'<div class="msg msg-err">{escape(error)}</div>'

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · SHUNYA Proposal</title><style>{_PROPOSAL_PAGE_CSS}</style></head>
<body><div class="wrap">
  <div class="card">
    <span class="badge">{status_esc}</span>
    <h1>{title}</h1>
    {f'<div class="meta">{meta}</div>' if meta else '<div class="meta">SHUNYA commercial proposal</div>'}
    <div class="section"><h3>Summary</h3><p>{scope}</p></div>
    <div class="value">{value_esc}</div>
    {f'<div class="section"><h3>Terms</h3><p>{terms}</p></div>' if terms else ''}
    {action_html}
    {msg_html}
  </div>
  <div class="foot">Prepared with SHUNYA</div>
</div></body></html>"""


@shunya_bp.route("/proposal/<token>", methods=["GET"])
def proposal_share_view(token: str):
    """Token-gated public view of a proposal (token = the capability)."""
    proposal = _find_proposal_by_token(token)
    if not proposal:
        return _proposal_page(_UnknownProposal(), error="This proposal link is invalid or no longer available."), 404

    # Advance sent → viewed when the counterparty actually opens the page.
    if proposal.status == "sent":
        try:
            from app.commercial.service import transition_proposal
            transition_proposal(proposal, "viewed", reason="Counterparty opened share link", triggered_by=f"token:{token[:8]}")
        except Exception:
            pass

    return _proposal_page(proposal)


class _UnknownProposal:
    """Stand-in for a missing proposal so the 404 renders the page shell."""
    title = "Proposal not found"
    status = "unknown"
    proposal_type = ""
    currency = ""
    total_value = 0
    scope_description = ""
    terms = ""
    valid_until = None
    share_token = ""


@shunya_bp.route("/proposal/<token>/accept", methods=["POST"])
def proposal_share_accept(token: str):
    """Token-gated accept (reuses the canonical proposal transition)."""
    proposal = _find_proposal_by_token(token)
    if not proposal:
        return _proposal_page(_UnknownProposal(), error="This proposal link is invalid or no longer available."), 404
    if proposal.status in ("accepted", "declined"):
        return _proposal_page(proposal, error=f"This proposal has already been {proposal.status}.")

    from app.commercial.service import transition_proposal
    success, err, _decision = transition_proposal(
        proposal,
        "accepted",
        reason="Accepted via share link",
        triggered_by=f"token:{token[:8]}",
    )
    if not success:
        return _proposal_page(proposal, error=err or "Could not accept this proposal."), 400
    return _proposal_page(proposal, message="Thank you — the proposal has been accepted.")


@shunya_bp.route("/proposal/<token>/decline", methods=["POST"])
def proposal_share_decline(token: str):
    """Token-gated decline (reuses the canonical proposal transition)."""
    proposal = _find_proposal_by_token(token)
    if not proposal:
        return _proposal_page(_UnknownProposal(), error="This proposal link is invalid or no longer available."), 404
    if proposal.status in ("accepted", "declined"):
        return _proposal_page(proposal, error=f"This proposal has already been {proposal.status}.")

    from app.commercial.service import transition_proposal
    success, err, _decision = transition_proposal(
        proposal,
        "declined",
        reason="Declined via share link",
        triggered_by=f"token:{token[:8]}",
    )
    if not success:
        return _proposal_page(proposal, error=err or "Could not decline this proposal."), 400
    return _proposal_page(proposal, message="The proposal has been declined.")