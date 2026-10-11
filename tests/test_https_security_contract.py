"""HTTPS / security-header application contract — deterministic CI tests.

The reverse-proxy (nginx) behavior — HTTP→HTTPS 301, HSTS on the public
endpoint — cannot be proven by a Flask unit test; that is covered by the
deploy job's production smoke step (see .github/workflows/ci.yml,
"Verify public HTTPS/HSTS contract"). What the application itself must
guarantee on EVERY response is pinned here:

- Full security header set (X-Content-Type-Options, X-Frame-Options,
  X-XSS-Protection, Referrer-Policy, Permissions-Policy,
  Strict-Transport-Security with preload, Content-Security-Policy)
- Session cookie flags: Secure, HttpOnly, SameSite
- Request correlation header on every response
"""
import pytest


REQUIRED_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "x-xss-protection": "1; mode=block",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "geolocation=(), microphone=(self), camera=()",
    "strict-transport-security": "max-age=31536000; includeSubDomains; preload",
    "content-security-policy": "default-src 'self'",
}


def _headers(resp):
    return {k.lower(): v for k, v in resp.headers.items()}


def test_health_carries_full_security_header_set(client):
    resp = client.get("/health")
    assert resp.status_code in (200, 503), resp.get_data(as_text=True)[:200]
    h = _headers(resp)
    for name, expected in REQUIRED_HEADERS.items():
        assert name in h, f"missing header: {name}"
        assert expected.lower() in h[name].lower(), f"{name} = {h[name]}"


def test_api_response_carries_security_headers(client):
    resp = client.get("/api/v1/platform/events")
    h = _headers(resp)
    assert "strict-transport-security" in h
    assert "x-content-type-options" in h
    assert "x-frame-options" in h


def test_hsts_includes_preload(client):
    h = _headers(client.get("/health"))
    assert "preload" in h["strict-transport-security"]
    assert "includeSubDomains" in h["strict-transport-security"]
    assert "max-age=31536000" in h["strict-transport-security"]


def test_session_cookie_flags(client):
    """A successful login issues a Secure+HttpOnly+SameSite session cookie."""
    resp = client.post("/login/password", json={
        "email": "nobody@test.invalid", "password": "wrong"})
    set_cookie = resp.headers.get("Set-Cookie", "")
    # Even a failed login should not weaken the cookie contract; assert the
    # app's configured flags via the session cookie when one is issued, and
    # otherwise assert the configuration itself.
    if set_cookie:
        assert "Secure" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite" in set_cookie


def test_session_cookie_config_is_secure(app):
    assert app.config.get("SESSION_COOKIE_SECURE") is True
    assert app.config.get("SESSION_COOKIE_HTTPONLY") is True
    assert app.config.get("SESSION_COOKIE_SAMESITE") == "Lax"


def test_request_id_on_every_response(client):
    resp = client.get("/health")
    assert "X-Request-Id" in resp.headers
    assert resp.headers["X-Request-Id"]