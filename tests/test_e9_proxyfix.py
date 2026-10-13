"""E9 — ProxyFix middleware: rate-limits key on real client IPs behind nginx.

The app factory wraps wsgi_app with werkzeug's ProxyFix so that
X-Forwarded-For (one hop, nginx -> gunicorn) is trusted. Without it,
get_remote_address returns 127.0.0.1 for every client, making rate-limits
site-global instead of per-client.

Tests exercise the ProxyFix middleware directly (same config as app factory)
so they verify the WSGI-layer IP/scheme rewriting without depending on Flask
routing.
"""
import pytest
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.test import EnvironBuilder


def _proxy_env(**environ_base):
    """Build a WSGI environ, wrap it through ProxyFix(x_for=1, x_proto=1),
    return the modified environ."""
    builder = EnvironBuilder(path="/dummy", environ_base=environ_base)
    env = builder.get_environ()

    def _start_response(status, headers):
        pass

    app = ProxyFix(
        lambda e, s: ([b"ok"],),
        x_for=1, x_proto=1, x_host=1, x_prefix=0,
    )
    list(app(env, _start_response))
    return env


@pytest.fixture(scope="module")
def app():
    from app import create_app
    _app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "e9-proxyfix-test",
    })
    return _app


class TestProxyFixApplied:
    """ProxyFix wrapping is present and functional."""

    def test_wsgi_app_is_wrapped(self, app):
        """The production wsgi_app should be wrapped in ProxyFix."""
        assert isinstance(app.wsgi_app, ProxyFix), (
            "app.wsgi_app must be wrapped in ProxyFix — rate-limits would "
            "otherwise key on 127.0.0.1 for every client behind nginx"
        )

    def test_x_for_one_hop(self, app):
        """x_for=1: the RIGHTMOST X-Forwarded-For entry becomes REMOTE_ADDR.

        nginx appends the client IP to the right of the X-Forwarded-For chain.
        With one trusted hop, ProxyFix reads the last (rightmost) entry as the
        real client IP. The leftmost entries may contain values set by the
        client or intermediate proxies that nginx preserves.
        """
        env = _proxy_env(
            HTTP_X_FORWARDED_FOR="198.51.100.23, 192.168.1.1",
            REMOTE_ADDR="127.0.0.1",
        )
        # Rightmost = 192.168.1.1 (the client IP, appended by nginx)
        assert env["REMOTE_ADDR"] == "192.168.1.1", (
            f"expected rightmost IP 192.168.1.1, "
            f"got {env['REMOTE_ADDR']} — x_for=1 should read rightmost entry"
        )

    def test_x_proto_https(self, app):
        """x_proto=1: X-Forwarded-Proto sets wsgi.url_scheme to https."""
        env = _proxy_env(
            HTTP_X_FORWARDED_FOR="203.0.113.42",
            HTTP_X_FORWARDED_PROTO="https",
            REMOTE_ADDR="127.0.0.1",
        )
        assert env.get("wsgi.url_scheme") == "https", (
            f"expected https scheme, got {env.get('wsgi.url_scheme')}"
        )

    def test_no_header_fallback(self, app):
        """Without X-Forwarded-For, REMOTE_ADDR is unchanged."""
        env = _proxy_env(REMOTE_ADDR="10.0.0.1")
        assert env["REMOTE_ADDR"] == "10.0.0.1", (
            f"expected fallback 10.0.0.1, got {env['REMOTE_ADDR']}"
        )

    def test_x_for_trust_boundary(self, app):
        """x_for=1 trusts exactly one hop — the rightmost entry.

        nginx always appends the true client IP to the right of
        X-Forwarded-For. With trust=1, ProxyFix takes the rightmost entry
        (which nginx added) and discards the left portion (which the client
        or upstream proxies set). A client sending a spoofed
        'X-Forwarded-For: 1.2.3.4' becomes
        'X-Forwarded-For: 1.2.3.4, <real_ip>' after nginx appends.
        ProxyFix uses <real_ip> (rightmost) and ignores 1.2.3.4.
        """
        env = _proxy_env(
            HTTP_X_FORWARDED_FOR="1.2.3.4, 203.0.113.42",
            REMOTE_ADDR="127.0.0.1",
        )
        assert env["REMOTE_ADDR"] == "203.0.113.42", (
            f"expected rightmost IP 203.0.113.42 (the real client), "
            f"got {env['REMOTE_ADDR']} — spoofed left entries are trusted"
        )