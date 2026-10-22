"""Isolated test server for CommandPalette certification.

Starts a Flask app with:
- SQLite :memory: database
- Local AI provider (deterministic, no network calls)
- Testing mode (disables alert worker, rate limits)
- Creates all tables before accepting requests
- Creates a test user for authentication
- Test-mode response hold queue for deterministic race tests
"""
import os
import sys
from typing import NoReturn

# ── Safety guards: explicit opt-in + validated disposable target ────────────
# This server exists ONLY for isolated local testing.  It refuses to start
# unless every check below passes (all checks run BEFORE the app is imported
# or any database is touched):
#   1. SHUNYA_TEST_SERVER_ALLOWED is exactly "true" (explicit opt-in).
#   2. TEST_DB_PATH is an absolute path under /tmp/, named
#      shunya_test_server*.sqlite, not a symlink, and (if it exists) a
#      regular file — never an arbitrary path.
#   3. DATABASE_URL is unset, or already equals the sqlite URL derived from
#      the validated TEST_DB_PATH.  An inherited production-like DATABASE_URL
#      is refused, never silently used.
# Cleanup removes ONLY the validated path and its sqlite -wal/-shm companions,
# records the decision in output, and reports failures instead of swallowing
# them.  Unrelated pre-existing files are never touched.
_REQUIRED_ALLOW = "true"
_ALLOWED_PREFIX = "/tmp/"
_ALLOWED_BASENAME_PREFIX = "shunya_test_server"
_ALLOWED_SUFFIX = ".sqlite"


def _fail(msg: str) -> NoReturn:
    print(f"ERROR: {msg}. Refusing to start the test server.", file=sys.stderr)
    sys.exit(1)


if os.environ.get("SHUNYA_TEST_SERVER_ALLOWED", "") != _REQUIRED_ALLOW:
    _fail("SHUNYA_TEST_SERVER_ALLOWED is not set to 'true'")

_TEST_DB_PATH = os.environ.get("TEST_DB_PATH", "/tmp/shunya_test_server.sqlite")

if not os.path.isabs(_TEST_DB_PATH):
    _fail(f"TEST_DB_PATH must be an absolute path (got: {_TEST_DB_PATH!r})")
if not _TEST_DB_PATH.startswith(_ALLOWED_PREFIX):
    _fail(f"TEST_DB_PATH must live under {_ALLOWED_PREFIX} (got: {_TEST_DB_PATH!r})")
_basename = os.path.basename(_TEST_DB_PATH)
if not _basename.startswith(_ALLOWED_BASENAME_PREFIX) or not _basename.endswith(_ALLOWED_SUFFIX):
    _fail(
        "TEST_DB_PATH must be named "
        f"{_ALLOWED_BASENAME_PREFIX}*{_ALLOWED_SUFFIX} (got: {_basename!r})"
    )
if os.path.islink(_TEST_DB_PATH):
    _fail(f"TEST_DB_PATH must not be a symlink (got: {_TEST_DB_PATH!r})")
if os.path.exists(_TEST_DB_PATH) and not os.path.isfile(_TEST_DB_PATH):
    _fail(f"TEST_DB_PATH exists but is not a regular file (got: {_TEST_DB_PATH!r})")

_DERIVED_DB_URL = f"sqlite:///{_TEST_DB_PATH}"

_inherited_url = os.environ.get("DATABASE_URL")
if _inherited_url and _inherited_url != _DERIVED_DB_URL:
    _fail(
        "DATABASE_URL is already set to a different target. The test server "
        "never inherits an arbitrary database; unset DATABASE_URL or point "
        "TEST_DB_PATH at the intended isolated SQLite file"
    )

# From here on the server uses ONLY the validated derived URL.
os.environ["DATABASE_URL"] = _DERIVED_DB_URL
os.environ.setdefault("SHUNYA_AI_PROVIDERS", "local")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-certification-only")
os.environ.setdefault("DISABLE_RATE_LIMIT", "true")
os.environ.setdefault("FLASK_ENV", "testing")

# Email isolation (G1.24): this server is a browser-certification harness, so it
# must be incapable of reaching a mail provider. FORCED, not setdefault — an
# inherited EMAIL_PROVIDER=resend plus a key would otherwise send real mail from
# a test run (G1.22 INC-5). The factory's transport guard would also refuse to
# boot, but scrubbing here keeps the failure mode a clean "logged" status instead
# of a startup error during a journey run.
os.environ["EMAIL_PROVIDER"] = "smtp"
# A loopback host is the local capture sink used to verify the delivery journey;
# its credentials are throwaway and cannot reach the internet. Anything else
# loses its credentials entirely so the send path degrades to "logged".
_EMAIL_LOOPBACK = os.environ.get("EMAIL_HOST", "").strip().lower() in {
    "127.0.0.1", "localhost", "::1",
}
if not _EMAIL_LOOPBACK:
    for _secret_var in ("EMAIL_USER", "EMAIL_PASSWORD"):
        os.environ.pop(_secret_var, None)
# Resend is never used by an isolated test server, whatever the environment says.
os.environ.pop("RESEND_API_KEY", None)

# ── Concurrency guard: one process per TEST_DB_PATH ────────────────────────
# Two test servers sharing a path would let the second delete the first's live
# database.  Hold an exclusive non-blocking flock for the process lifetime.
import fcntl as _fcntl
import stat as _stat

_LOCK_PATH = _TEST_DB_PATH + ".lock"
try:
    _lock_fd = os.open(_LOCK_PATH, os.O_CREAT | os.O_RDWR, 0o600)
except OSError as _exc:
    _fail(f"Could not create lock file {_LOCK_PATH!r}: {_exc}")
_lock_st = os.fstat(_lock_fd)
if not _stat.S_ISREG(_lock_st.st_mode) or _lock_st.st_uid != os.getuid():
    _fail(f"Lock file {_LOCK_PATH!r} is not a regular file owned by the current user")
try:
    _fcntl.flock(_lock_fd, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
except OSError:
    _fail(
        f"Another test-server instance already holds {_LOCK_PATH!r}. "
        "Use a distinct TEST_DB_PATH per concurrent instance"
    )

# ── Stale-DB cleanup (validated, ownership-checked, TOCTOU-aware) ──────────
# Only the exact validated path and its sqlite -wal/-shm companions may be
# removed.  All candidates are validated first (lstat: regular file, owned by
# this user, not a symlink) so an ambiguous sidecar aborts BEFORE anything is
# deleted.  lstat is repeated immediately before unlink to narrow the
# check-to-use window; /tmp's sticky bit prevents other users from replacing
# files this user owns.
_cleanup_candidates = [
    _p for _p in (_TEST_DB_PATH, _TEST_DB_PATH + "-wal", _TEST_DB_PATH + "-shm")
    if os.path.lexists(_p)
]
for _p in _cleanup_candidates:
    try:
        _st = os.lstat(_p)
    except OSError as _exc:
        _fail(f"Cannot stat {_p!r}: {_exc}")
    if _stat.S_ISLNK(_st.st_mode):
        _fail(f"Refusing cleanup: {_p!r} is a symlink")
    if not _stat.S_ISREG(_st.st_mode):
        _fail(f"Refusing cleanup: {_p!r} is not a regular file")
    if _st.st_uid != os.getuid():
        _fail(f"Refusing cleanup: {_p!r} is not owned by the current user")

if _cleanup_candidates:
    print(
        f"Removing stale test DB at {_TEST_DB_PATH} (validated test-server path)",
        flush=True,
    )
    for _p in _cleanup_candidates:
        _st = os.lstat(_p)  # re-check immediately before use
        if _stat.S_ISLNK(_st.st_mode) or not _stat.S_ISREG(_st.st_mode) or _st.st_uid != os.getuid():
            _fail(f"Refusing cleanup: {_p!r} changed type/ownership during validation")
        try:
            os.remove(_p)
        except OSError as _exc:
            _fail(f"Could not remove stale test DB {_p!r}: {_exc}")

# ── Test-mode response hold queue ────────────────────────────────────
import threading
from flask import jsonify as _jsonify
_test_holds: dict[str, threading.Event] = {}
# Request IDs flagged to return an error when released (test-only)
_test_error_ids: set[str] = set()

from app import create_app, db

app = create_app(config_override={
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": os.environ["DATABASE_URL"],
    "SECRET_KEY": os.environ["SECRET_KEY"],
    "DISABLE_RATE_LIMIT": "true",
    "WTF_CSRF_ENABLED": False,
})

# ── Test-control routes must be reachable WITHOUT a session ──────────
# The app's session-gating middleware (create_app) denies every non-public
# route by default. The /__test__/* endpoints ARE test controls and must be
# callable from an unauthenticated browser harness script. Register the
# prefix at runtime in THIS isolated test process only — production never
# executes this module, so the public-route allowlist is untouched there.
from app.security import public_routes as _pub
_test_prefixes = _pub.PUBLIC_PREFIXES | frozenset(
    (m, "/__test__/") for m in ("GET", "POST")
)
_pub.PUBLIC_PREFIXES = _test_prefixes

with app.app_context():
    # Import all models so create_all() registers every table
    from app import models  # noqa: F401
    from app.alerting.models import AlertEvent  # noqa: F401
    from app import db
    db.create_all()
    print("All tables created", flush=True)

    # Create a test user for authentication
    from app.auth import TeamMember
    from app.models import OrgMember
    from app.tenant import Tenant

    test_email = os.environ.get("TEST_EMAIL", "test@shunyaos.com")
    test_pass = os.environ.get("TEST_PASSWORD", "test-password-for-certification")
    user = TeamMember.query.filter_by(email=test_email).first()
    if not user:
        user = TeamMember(
            email=test_email,
            name="Test User",
            role="admin",
            is_active=True,
            verified=True,
        )
        user.set_password(test_pass)
        db.session.add(user)
        db.session.flush()
        print(f"Test user created: {test_email} (id={user.id})", flush=True)
    else:
        print(f"Test user exists: {test_email} (id={user.id})", flush=True)

    # Create or ensure a personal org + workspace for the test user
    if not user.identity_id:
        from app.production.identity_repository import IdentityRepository
        repo = IdentityRepository()
        identity = repo.find_by_auth("email", test_email)
        if not identity:
            identity = repo.create(display_name=user.name, primary_email=test_email)
            repo.add_auth_method(identity.identity_id, "email", test_email, is_primary=True)
        user.identity_id = identity.identity_id
        db.session.commit()

    # Ensure OrgMember record so session middleware resolves current_org_id
    org_member = OrgMember.query.filter_by(email=test_email, is_active=True).first()
    tenant_org_id = None
    if not org_member:
        from app.tenant import Tenant
        tenant = Tenant(company_name=f"Personal-{user.name}", slug=f"personal-{user.id}")
        db.session.add(tenant)
        db.session.flush()
        tenant_org_id = tenant.id
        org_member = OrgMember(
            email=test_email,
            organization_id=tenant_org_id,
            identity_id=user.identity_id,
            name=user.name,
            role="owner",
            is_active=True,
        )
        db.session.add(org_member)
        db.session.flush()
        print(f"OrgMember created: {test_email} -> org {tenant_org_id}", flush=True)
    else:
        tenant_org_id = org_member.organization_id
        print(f"OrgMember exists: {test_email} -> org {tenant_org_id}", flush=True)

    # Mirror the legacy Tenant row into the canonical Organization table with the
    # same id. OrgMember.organization_id references organizations.id; leaving the
    # canonical table empty makes the first real organization creation collide on
    # the (organization_id, identity_id) unique index (HTTP 500).
    from app.models import Organization
    if not db.session.get(Organization, tenant_org_id):
        db.session.add(Organization(
            id=tenant_org_id,
            name=f"Personal-{user.name}",
            slug=f"personal-{user.id}",
            business_type="personal",
            is_active=True,
        ))
        db.session.flush()
        print(f"Canonical Organization mirrored for org {tenant_org_id}", flush=True)

    # Ensure a canonical Workspace exists for the org (needed by AI chat route)
    from app.objects.legacy_models import Workspace as LegacyWorkspace
    import uuid
    ws_id = f"ws_{uuid.uuid4().hex[:16]}"
    workspace = LegacyWorkspace.query.filter_by(organization_id=tenant_org_id, status='active').first()
    if not workspace:
        workspace = LegacyWorkspace(
            id=ws_id,
            name="Default Workspace",
            workspace_type="personal",
            created_by=user.identity_id,
            organization_id=tenant_org_id,
            status='active',
        )
        db.session.add(workspace)
        db.session.commit()
        print(f"Legacy Workspace created: {workspace.id} for org {tenant_org_id}", flush=True)
    else:
        print(f"Legacy Workspace exists: {workspace.id} for org {tenant_org_id}", flush=True)
        ws_id = workspace.id

    # Session context is set manually before each API call by the login flow

    # Seed default roles for the org so the ai.use permission exists
    from app.authz.services import seed_default_roles
    seed_default_roles(tenant_org_id)
    print(f"Default roles seeded for org {tenant_org_id}", flush=True)

    # Create workspace membership so workspace context authorization passes
    from app.objects.legacy_models import ShWorkspaceMembership
    membership = ShWorkspaceMembership.query.filter_by(
        workspace_id=ws_id, identity_id=user.identity_id
    ).first()
    if not membership:
        membership = ShWorkspaceMembership(
            workspace_id=ws_id,
            identity_id=user.identity_id,
            role='member',
            is_active=True,
        )
        db.session.add(membership)
        db.session.commit()
        print(f"Workspace membership created: {ws_id} for identity {user.identity_id[:24]}", flush=True)
    else:
        print(f"Workspace membership exists: {ws_id} for identity {user.identity_id[:24]}", flush=True)

if __name__ == "__main__":
    from flask import request as flask_request
    port = int(os.environ.get("TEST_SERVER_PORT", "51999"))
    print(f"Starting test server on port {port}", flush=True)

    @app.route("/__test__/hold-ai-response/<request_id>", methods=["POST"])
    def _test_hold_ai_response(request_id: str):
        """Hold a specific AI response until released."""
        _test_holds[request_id] = threading.Event()
        return {"status": "held", "request_id": request_id}

    @app.route("/__test__/error-ai-response/<request_id>", methods=["POST"])
    def _test_error_ai_response(request_id: str):
        """Hold an AI response and return an error when released."""
        _test_holds[request_id] = threading.Event()
        _test_error_ids.add(request_id)
        return {"status": "held_as_error", "request_id": request_id}

    @app.route("/__test__/release-ai-response/<request_id>", methods=["POST"])
    def _test_release_ai_response(request_id: str):
        """Release a held AI response."""
        ev = _test_holds.pop(request_id, None)
        if ev:
            ev.set()
            return {"status": "released", "request_id": request_id}
        return {"status": "not_found", "request_id": request_id}, 404

    @app.route("/__test__/drain-holds", methods=["POST"])
    def _test_drain_holds():
        """Release all held responses (cleanup)."""
        count = len(_test_holds)
        for ev in _test_holds.values():
            ev.set()
        _test_holds.clear()
        _test_error_ids.clear()
        return {"status": "drained", "count": count}

    @app.route("/__test__/get-verify-token/<email>", methods=["GET"])
    def _test_get_verify_token(email: str):
        """Return the verification token for a test user's email."""
        from app.auth import TeamMember
        member = TeamMember.query.filter_by(email=email).first()
        if not member:
            return {"error": "User not found"}, 404
        if not member.verify_token:
            return {"error": "No pending verification token", "verified": member.verified}, 200
        return {"email": email, "verify_token": member.verify_token, "verified": False}

    @app.before_request
    def _check_ai_hold():
        if flask_request.path == "/api/v1/ai/chat" and flask_request.method == "POST":
            # Use get_data() instead of get_json() to avoid consuming the body
            import json as _json
            try:
                body = _json.loads(flask_request.get_data(as_text=True) or "{}")
            except Exception:
                body = {}
            rid = str(body.get("request_id", "") or "")
            if rid and rid in _test_holds:
                ev = _test_holds.get(rid)
                if ev and not ev.is_set():
                    ev.wait(timeout=60)
                _test_holds.pop(rid, None)
                # If this request was flagged for error, short-circuit with error
                if rid in _test_error_ids:
                    print(f"__TEST_ERROR_HIT__: {rid}", flush=True)
                    _test_error_ids.discard(rid)
                    return _jsonify({
                        "error": "Simulated provider error for certification test",
                        "model": "none",
                        "fallback": True,
                    }), 503
                else:
                    print(f"__TEST_HOLD_RELEASED_NORMAL__: {rid}", flush=True)

    print(f"Test-mode hold queue active with {len(_test_holds)} pending", flush=True)
    app.run(host="127.0.0.1", port=port, debug=False)