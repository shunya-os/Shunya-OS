"""SHUNYA canonical public-route registry (B16).

Single source of truth for what the auth middleware may serve WITHOUT a
verified session. Everything not listed here is deny-by-default: the
middleware requires a session cookie (402? no — 401 for /api, redirect for
pages) and NEVER trusts the ``X-Identity-Id`` header or any other
client-supplied identity signal.

Rules for adding an entry:
  * Exact (method, path) tuples for static public routes.
  * ``PUBLIC_PREFIXES`` only for constrained dynamic flows whose path itself
    carries the capability (one-time token, provider webhook) and whose
    handler enforces signature/expiry/consumption server-side.
  * Every entry needs a reason in PUBLIC_ROUTES_REASONS; an entry without a
    reason is a review failure (asserted in tests).

The route-inventory test (tests/test_route_security_inventory.py) fails when
a route is neither allowlisted here, nor a serve-only surface, nor marked by
an authz decorator.
"""
from __future__ import annotations

# Exact public routes: (method, path).
PUBLIC_ROUTES: frozenset[tuple[str, str]] = frozenset({
    # --- Uptime / provenance (CI deploy verification depends on these) ---
    ("GET", "/health"),                 # local + public health/provenance checks
    ("GET", "/ready"),                  # readiness probe
    ("GET", "/live"),                   # liveness probe
    ("GET", "/metrics"),                # Prometheus scrape point (E8 review pending)
    # --- SPA shell / auth pages (no data rendered server-side) ---
    ("GET", "/"),                       # SPA shell — auth + routing client-side
    ("GET", "/workspace"),              # SPA shell /workspace
    ("GET", "/living"),                 # SPA shell (legacy living workspace)
    ("GET", "/auth"),
    ("GET", "/auth/"),
    ("GET", "/auth/login"),
    ("GET", "/auth/register"),
    ("GET", "/auth/signup"),
    ("GET", "/auth/forgot-password"),
    ("GET", "/auth/reset-password"),
    ("GET", "/auth/invitation"),
    ("GET", "/auth/verify-email"),
    # --- Login / logout (pre-auth by definition) ---
    ("GET", "/login"),                  # login form page
    ("POST", "/login"),                 # JSON login (used by SPA)
    ("POST", "/login/password"),        # password login
    ("GET", "/logout"),                 # clears session (idempotent)
    ("POST", "/mfa/challenge"),         # MFA challenge during login — pre-session by design
    # --- Pre-auth account flows (must be reachable without a session) ---
    ("POST", "/api/v1/auth/signup"),
    ("POST", "/api/v1/auth/request-verification"),
    ("POST", "/api/v1/auth/verify-email"),
    ("POST", "/api/v1/auth/forgot-password"),
    ("POST", "/api/v1/auth/reset-password"),
    ("GET", "/api/v1/auth/session"),    # SPA session probe — itself returns 401 when unauth
    # --- SPA redirect stubs (no data; bounce to the canonical page) ---
    ("GET", "/ai-settings"),            # redirect → /settings
    ("GET", "/finance"),                # redirect → /
    ("GET", "/financial"),              # redirect → /
    ("GET", "/relationships"),          # redirect → /
    # --- OAuth provider flows (external redirects must be reachable pre-auth) ---
    ("GET", "/api/v1/auth/google/login"),
    ("GET", "/api/v1/auth/google/callback"),
    ("GET", "/api/v1/auth/github/login"),
    ("GET", "/api/v1/auth/github/callback"),
    ("GET", "/gmail/oauth/callback"),   # Google OAuth callback (gmail connect)
    # --- Provider webhooks (handler-verified signatures/tokens) ---
    ("POST", "/api/v1/email/webhook"),  # Resend delivery/bounce/complaint events
    ("GET", "/whatsapp/webhook"),       # WhatsApp hub verification
    ("POST", "/whatsapp/webhook"),      # WhatsApp inbound messages (sig-verified)
    ("POST", "/telegram/webhook"),
    ("POST", "/api/v1/payments/razorpay/webhook"),  # Razorpay payment events — signature-verified (HMAC-SHA256)
    ("GET", "/api/v1/reality/health"),  # reality engine health probe (status only)
    ("GET", "/api/v1/audit/health"),    # audit service health probe (status only)
    ("GET", "/system/health"),          # system health probe
    ("GET", "/system/unused-intelligence"),  # probe listing engine names (E8 review)
    ("GET", "/api/v1/content/health"),  # content studio health probe
    ("GET", "/api/v1/cross-boundary/health"),  # cross-boundary health probe
    ("GET", "/api/v1/data/health"),     # import/export health probe
    ("GET", "/api/v1/deploy/health"),   # deploy health probe
    ("GET", "/api/v1/deploy/status"),   # deploy status (E8 review — deploy verification)
    ("GET", "/api/v1/knowledge/health"),# knowledge health probe
    ("GET", "/api/v1/platform/health"), # platform health probe
    ("GET", "/api/v1/workspace/health"),# workspace health probe
    ("GET", "/api/v1/platform/connector-sdk"),  # SDK documentation
    ("GET", "/api/v1/platform/openapi.json"),   # API schema documentation
    ("POST", "/api/v1/founder/signin"), # founder login (pre-auth; rate-limited)
    ("POST", "/api/v1/identity/create"),# canonical identity bootstrap — password-based (A9/D14 unification)
    ("GET", "/identity/create"),        # identity creation page (HTML, no data)
    ("GET", "/identity/created"),       # identity creation confirmation page (HTML, no data)
    # --- Generic ingestion endpoint (B16 review: restrict or sign-verify) ---
    # TODO(B16): currently accepts arbitrary JSON with client-chosen source;
    # keep public ONLY while the handler adds signature/token verification.
    ("POST", "/api/v1/webhook/"),
})

# Dynamic public prefixes: (method, prefix). The path segment beyond the
# prefix carries the capability and the handler enforces it server-side.
PUBLIC_PREFIXES: frozenset[tuple[str, str]] = frozenset({
    ("GET", "/api/v1/orgs/invitations/"),   # invite token link (one-time, expiry enforced)
    ("POST", "/api/v1/orgs/invitations/"),  # invite acceptance (token consumed server-side)
    ("GET", "/admin/"),                     # /admin/* redirect stubs → /settings
    ("GET", "/audit/"),                     # public founding/constitution documents
    ("GET", "/payment/link/"),              # customer payment link page (Razorpay)
    ("GET", "/payment/checkout/"),          # customer checkout page
    ("GET", "/payment/receipt/"),           # customer payment receipt page
    ("GET", "/proposal/"),                  # token-gated proposal view (token = capability)
    ("POST", "/proposal/"),                 # token-gated proposal accept/decline (token = capability)
})

# Serve-only surfaces (no data, no handler-side authz needed).
SPA_SHELL_PATHS: frozenset[str] = frozenset({
    "/static", "/assets", "/icon-", "/favicon", "/x",
})
SPA_SHELL_EXACT: frozenset[str] = frozenset({"/manifest.json", "/sw.js"})

PUBLIC_ROUTES_REASONS: dict[tuple[str, str], str] = {
    ("GET", "/health"): "uptime/provenance verification (CI deploy gate)",
    ("GET", "/ready"): "readiness probe",
    ("GET", "/live"): "liveness probe",
    ("GET", "/metrics"): "Prometheus scrape (E8 review pending)",
    ("GET", "/"): "SPA shell — no server-side data",
    ("GET", "/workspace"): "SPA shell — no server-side data",
    ("GET", "/living"): "SPA shell — no server-side data",
    ("GET", "/auth"): "SPA auth shell",
    ("GET", "/auth/"): "SPA auth shell",
    ("GET", "/auth/login"): "SPA auth shell",
    ("GET", "/auth/register"): "SPA auth shell",
    ("GET", "/auth/signup"): "SPA auth shell",
    ("GET", "/auth/forgot-password"): "SPA auth shell",
    ("GET", "/auth/reset-password"): "SPA auth shell",
    ("GET", "/auth/invitation"): "SPA auth shell",
    ("GET", "/auth/verify-email"): "SPA auth shell",
    ("GET", "/login"): "login form",
    ("POST", "/login"): "JSON login (SPA)",
    ("POST", "/login/password"): "password login",
    ("GET", "/logout"): "session clear (idempotent)",
    ("POST", "/mfa/challenge"): "MFA challenge during login — pre-session; TOTP verify + rate limit (E11/E12)",
    ("POST", "/api/v1/auth/signup"): "pre-auth account creation",
    ("POST", "/api/v1/auth/request-verification"): "pre-auth verification request",
    ("POST", "/api/v1/auth/verify-email"): "pre-auth email verification",
    ("POST", "/api/v1/auth/forgot-password"): "pre-auth password reset request",
    ("POST", "/api/v1/auth/reset-password"): "pre-auth password reset",
    ("GET", "/api/v1/auth/session"): "SPA session probe — 401 when unauthenticated",
    ("GET", "/ai-settings"): "redirect stub → /settings (no data)",
    ("GET", "/finance"): "redirect stub → / (no data)",
    ("GET", "/financial"): "redirect stub → / (no data)",
    ("GET", "/relationships"): "redirect stub → / (no data)",
    ("GET", "/api/v1/auth/google/login"): "OAuth flow start",
    ("GET", "/api/v1/auth/google/callback"): "OAuth provider callback",
    ("GET", "/api/v1/auth/github/login"): "OAuth flow start",
    ("GET", "/api/v1/auth/github/callback"): "OAuth provider callback",
    ("GET", "/gmail/oauth/callback"): "Google OAuth callback",
    ("POST", "/api/v1/email/webhook"): "Resend delivery events — handler verifies signature",
    ("GET", "/whatsapp/webhook"): "WhatsApp hub verification — verify_token enforced",
    ("POST", "/whatsapp/webhook"): "WhatsApp inbound — signature verified",
    ("POST", "/telegram/webhook"): "Telegram provider callback",
    ("POST", "/api/v1/payments/razorpay/webhook"): "Razorpay payment events — handler verifies HMAC-SHA256 signature",
    ("GET", "/api/v1/reality/health"): "reality engine health probe — status only, no tenant data",
    ("GET", "/api/v1/audit/health"): "audit service health probe — status only",
    ("GET", "/system/health"): "system health probe (deploy verification)",
    ("GET", "/system/unused-intelligence"): "probe listing engine names — no tenant data (E8 review)",
    ("GET", "/api/v1/content/health"): "content studio health probe — status only",
    ("GET", "/api/v1/cross-boundary/health"): "cross-boundary health probe — status only",
    ("GET", "/api/v1/data/health"): "import/export health probe — status only",
    ("GET", "/api/v1/deploy/health"): "deploy health probe — status only",
    ("GET", "/api/v1/deploy/status"): "deploy status — deploy verification (E8: minimize metadata)",
    ("GET", "/api/v1/knowledge/health"): "knowledge health probe — status only",
    ("GET", "/api/v1/platform/health"): "platform health probe — status only",
    ("GET", "/api/v1/workspace/health"): "workspace health probe — status only",
    ("GET", "/api/v1/platform/connector-sdk"): "SDK documentation — no tenant data",
    ("GET", "/api/v1/platform/openapi.json"): "API schema documentation — no tenant data",
    ("POST", "/api/v1/founder/signin"): "founder login — pre-auth, credential-verified, rate-limited",
    ("POST", "/api/v1/identity/create"): "canonical identity bootstrap — password-based (A9/D14 unification)",
    ("GET", "/identity/create"): "identity creation page — HTML, no data",
    ("GET", "/identity/created"): "identity creation confirmation page — HTML, no data",
    ("POST", "/api/v1/webhook/"): "generic ingestion — signature verification TODO (B16)",
    ("GET", "/api/v1/orgs/invitations/"): "invite token link — one-time token, expiry enforced server-side",
    ("POST", "/api/v1/orgs/invitations/"): "invite acceptance — token consumed server-side",
    ("GET", "/admin/"): "/admin/* redirect stubs → /settings (no data)",
    ("GET", "/audit/"): "public founding/constitution documents",
    ("GET", "/payment/link/"): "customer payment link page — Razorpay-hosted checkout",
    ("GET", "/payment/checkout/"): "customer checkout page",
    ("GET", "/payment/receipt/"): "customer payment receipt page",
    ("GET", "/proposal/"): "token-gated proposal view — share token is the capability, content HTML-escaped",
    ("POST", "/proposal/"): "token-gated proposal accept/decline — token consumed server-side via canonical transitions",
}


def is_public(method: str, path: str) -> bool:
    """True when the middleware may serve this request without a session."""
    if (method, path) in PUBLIC_ROUTES:
        return True
    for m, prefix in PUBLIC_PREFIXES:
        if method == m and path.startswith(prefix):
            return True
    return False


def is_serve_only(path: str) -> bool:
    """True for static assets / SPA shell files (no data, no auth needed)."""
    if path in SPA_SHELL_EXACT:
        return True
    for prefix in SPA_SHELL_PATHS:
        if path.startswith(prefix):
            return True
    return False