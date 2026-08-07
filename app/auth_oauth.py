"""SHUNYA — OAuth Sign-In Routes (Google & GitHub).

Authenticates with provider, looks up or creates a SHUNYA identity by email,
saves session via SessionManager pattern (sessionStorage + X-Identity-Id header),
returns a token the frontend can store in sessionStorage.

Architecture:
  Login → redirect to provider OAuth URL
  Callback → exchange code → fetch user info → resolve/create identity → set session
"""

import os
import secrets
from urllib.parse import urlencode

import requests
from flask import Blueprint, jsonify, redirect, request, session, url_for

# ---------------------------------------------------------------------------
# Blueprint — registered on /api/v1/auth in create_app()
# ---------------------------------------------------------------------------
oauth_bp = Blueprint("oauth", __name__, url_prefix="/api/v1/auth")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_base_url() -> str:
    """Return the scheme + host for callback URLs.

    Uses X-Forwarded-Proto/ Host headers when behind a reverse proxy;
    falls back to the Flask config.
    """
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
    host = request.headers.get("X-Forwarded-Host", request.host)
    return f"{scheme}://{host}"


def _generate_state() -> str:
    """Generate a cryptographically random state value for CSRF protection."""
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    return state


def _verify_state(state: str | None) -> bool:
    """Verify that the state parameter matches the one we stored in the session."""
    saved = session.pop("oauth_state", None)
    if not saved or not state:
        return False
    return secrets.compare_digest(saved, state)


def _resolve_or_create_identity(email: str, display_name: str,
                                provider: str, provider_id: str) -> str | None:
    """Look up an existing identity by email, or create a new one.

    Stores the OAuth provider info as an auth method on the identity.
    Returns the identity_id (sid_xxx), or None on failure.
    """
    from app.production.identity_repository import IdentityRepository

    repo = IdentityRepository()

    # Try to find existing identity by email (oauth provider)
    existing = repo.find_by_auth_core("oauth", email)
    if existing:
        # Ensure the provider-specific auth method is recorded
        repo.add_auth_method(existing.identity_id, f"oauth:{provider}", provider_id)
        return existing.identity_id

    # Fallback: search by email type
    existing = repo.find_by_auth_core("email", email)
    if existing:
        # Add oauth as an additional auth method
        repo.add_auth_method(existing.identity_id, "oauth", email)
        repo.add_auth_method(existing.identity_id, f"oauth:{provider}", provider_id)
        return existing.identity_id

    # Create a brand-new identity
    identity = repo.create_core(
        display_name=display_name,
        entity_type="human",
        auth_methods=[
            {"method_type": "email", "identifier": email, "is_primary": True},
            {"method_type": "oauth", "identifier": email, "is_primary": False},
            {"method_type": f"oauth:{provider}", "identifier": provider_id, "is_primary": False},
        ],
    )
    return identity.identity_id


def _set_session(identity_id: str) -> None:
    """Set session cookies matching the existing auth pattern.

    The founder routes check session['identity_id'] and session['user_id']; the
    login_required decorator in auth_routes.py checks session['user_id'].
    """
    session["identity_id"] = identity_id
    session["user_id"] = identity_id
    session.modified = True


def _oauth_response(identity_id: str):
    """Return a JSON response the frontend can use to set sessionStorage.

    Follows the same shape as api_founder_signin() in founder/routes.py.
    The frontend stores `identity_id` and `token` in sessionStorage and
    sends X-Identity-Id on subsequent API calls.
    """
    return jsonify({
        "success": True,
        "identity_id": identity_id,
        "token": identity_id,          # Frontend stores this as sessionStorage token
        "redirect": "/workspace/",
    })


# ===========================================================================
# Google OAuth
# ===========================================================================

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_SCOPES = "openid email profile"


@oauth_bp.route("/google/login", methods=["GET"])
def google_login():
    """Redirect the user to Google's OAuth consent screen."""
    if not GOOGLE_CLIENT_ID:
        return jsonify({"success": False, "error": "Google OAuth not configured"}), 501

    base_url = _get_base_url()
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{base_url}/api/v1/auth/google/callback",
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "state": _generate_state(),
        "access_type": "online",
        "prompt": "select_account",
    }
    return redirect(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@oauth_bp.route("/google/callback", methods=["GET"])
def google_callback():
    """Handle the Google OAuth callback.

    Exchanges the authorization code for tokens, fetches the user's profile,
    looks up or creates a SHUNYA identity, and sets the session.
    """
    error = request.args.get("error")
    if error:
        return jsonify({"success": False, "error": f"Google OAuth error: {error}"}), 400

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return jsonify({"success": False, "error": "Missing authorization code"}), 400

    if not _verify_state(state):
        return jsonify({"success": False, "error": "State mismatch — possible CSRF"}), 400

    base_url = _get_base_url()

    # Exchange code for tokens
    try:
        token_resp = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": f"{base_url}/api/v1/auth/google/callback",
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
            timeout=15,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
    except requests.RequestException as e:
        return jsonify({"success": False, "error": f"Token exchange failed: {e}"}), 502

    access_token = token_data.get("access_token")
    if not access_token:
        return jsonify({"success": False, "error": "No access token in response"}), 502

    # Fetch user info
    try:
        user_resp = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        user_resp.raise_for_status()
        user_info = user_resp.json()
    except requests.RequestException as e:
        return jsonify({"success": False, "error": f"Failed to fetch user info: {e}"}), 502

    email = (user_info.get("email") or "").strip().lower()
    name = user_info.get("name") or email.split("@")[0]
    google_id = user_info.get("id") or email

    if not email:
        return jsonify({"success": False, "error": "No email returned from Google"}), 400

    # Resolve or create identity
    identity_id = _resolve_or_create_identity(
        email=email,
        display_name=name,
        provider="google",
        provider_id=google_id,
    )
    if not identity_id:
        return jsonify({"success": False, "error": "Failed to create identity"}), 500

    _set_session(identity_id)
    return _oauth_response(identity_id)


# ===========================================================================
# GitHub OAuth
# ===========================================================================

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USERINFO_URL = "https://api.github.com/user"
GITHUB_USEREMAILS_URL = "https://api.github.com/user/emails"


@oauth_bp.route("/github/login", methods=["GET"])
def github_login():
    """Redirect the user to GitHub's OAuth consent screen."""
    if not GITHUB_CLIENT_ID:
        return jsonify({"success": False, "error": "GitHub OAuth not configured"}), 501

    base_url = _get_base_url()
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": f"{base_url}/api/v1/auth/github/callback",
        "scope": "read:user user:email",
        "state": _generate_state(),
    }
    return redirect(f"{GITHUB_AUTH_URL}?{urlencode(params)}")


@oauth_bp.route("/github/callback", methods=["GET"])
def github_callback():
    """Handle the GitHub OAuth callback.

    Exchanges the authorization code for tokens, fetches the user's profile
    (including primary email), looks up or creates a SHUNYA identity,
    and sets the session.
    """
    error = request.args.get("error")
    if error:
        return jsonify({"success": False, "error": f"GitHub OAuth error: {error}"}), 400

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return jsonify({"success": False, "error": "Missing authorization code"}), 400

    if not _verify_state(state):
        return jsonify({"success": False, "error": "State mismatch — possible CSRF"}), 400

    base_url = _get_base_url()

    # Exchange code for access token
    try:
        token_resp = requests.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{base_url}/api/v1/auth/github/callback",
            },
            headers={
                "Accept": "application/json",
            },
            timeout=15,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
    except requests.RequestException as e:
        return jsonify({"success": False, "error": f"Token exchange failed: {e}"}), 502

    access_token = token_data.get("access_token")
    if not access_token:
        return jsonify({"success": False, "error": "No access token in response"}), 502

    # Fetch user info (profile)
    try:
        user_resp = requests.get(
            GITHUB_USERINFO_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            timeout=15,
        )
        user_resp.raise_for_status()
        user_info = user_resp.json()
    except requests.RequestException as e:
        return jsonify({"success": False, "error": f"Failed to fetch user profile: {e}"}), 502

    # GitHub doesn't always return the primary email in the /user response,
    # so fetch the emails endpoint if needed.
    email = (user_info.get("email") or "").strip().lower()
    if not email:
        try:
            emails_resp = requests.get(
                GITHUB_USEREMAILS_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                timeout=15,
            )
            emails_resp.raise_for_status()
            emails = emails_resp.json()
            for e in emails:
                if e.get("primary") and e.get("verified"):
                    email = e["email"].strip().lower()
                    break
            if not email and emails:
                email = emails[0].get("email", "").strip().lower()
        except requests.RequestException:
            pass

    name = user_info.get("name") or user_info.get("login") or email.split("@")[0]
    github_id = str(user_info.get("id", ""))

    if not email:
        return jsonify({
            "success": False,
            "error": "No email returned from GitHub — ensure your GitHub account has a public email",
        }), 400

    # Resolve or create identity
    identity_id = _resolve_or_create_identity(
        email=email,
        display_name=name,
        provider="github",
        provider_id=github_id,
    )
    if not identity_id:
        return jsonify({"success": False, "error": "Failed to create identity"}), 500

    _set_session(identity_id)
    return _oauth_response(identity_id)