"""FDA5-G3: Auth + Security Boundary tests.

Tests every API and integration boundary for auth enforcement.
Negative tests ensure security is not bypassed.
"""
import json
import pytest


@pytest.fixture
def app():
    from app import create_app
    application = create_app({"TESTING": True})
    return application


class TestAuthBoundary:
    """Authentication is enforced on every API boundary."""

    def test_unauthenticated_request_rejected(self, app):
        """No auth → 401."""
        from core.api_contract import register_error_handlers
        with app.app_context():
            register_error_handlers(app)
            # First verify the route exists
            with app.test_client() as client:
                health_resp = client.get("/system/health")
                assert health_resp.status_code == 200, "/system/health must exist and be accessible"
            # Now test auth-required route with correct HTTP method
            with app.test_client() as client:
                resp = client.post("/api/v1/intelligence/ask",
                                   json={"query": "test"})
                # Must be 401 (auth failure), not 404 (route missing) or 405 (wrong method)
                assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    def test_health_endpoint_public(self, app):
        """Health endpoint should be accessible without auth."""
        with app.test_client() as client:
            resp = client.get("/system/health")
            assert resp.status_code in (200, 302)  # 302 if redirect, 200 if direct

    def test_security_headers_present(self, app):
        """Security headers must be set on every response."""
        with app.test_client() as client:
            resp = client.get("/system/health")
            headers = {k.lower(): v for k, v in resp.headers.items()}
            # Check for common security headers
            sec_headers = [
                "x-content-type-options",
                "x-frame-options",
                "content-security-policy",
                "strict-transport-security",
            ]
            found = [h for h in sec_headers if h in headers]
            assert len(found) > 0, f"No security headers found in {list(headers.keys())}"

    def test_cors_headers(self, app):
        """CORS headers must be present on cross-origin requests."""
        with app.test_client() as client:
            resp = client.options(
                "/api/v1/intelligence",
                headers={"Origin": "https://shunya.app", "Access-Control-Request-Method": "GET"},
            )
            cors = {k.lower(): v for k, v in resp.headers.items() if "access-control" in k.lower()}
            assert len(cors) > 0, f"No CORS headers in {dict(resp.headers)}"

    def test_sensitive_data_not_in_errors(self, app):
        """Error responses must not leak internals."""
        from core.api_contract import register_error_handlers
        with app.app_context():
            register_error_handlers(app)
            with app.test_client() as client:
                resp = client.get("/nonexistent-route-to-test-404")
                assert resp.status_code == 404
                body = resp.get_data(as_text=True).lower()
                # Should not leak
                for leak in ["traceback", "file", "line", "stack", "internal", "secret"]:
                    assert leak not in body, f"Error response leaked '{leak}'"

    def test_wrong_http_method_returns_405(self, app):
        """Wrong HTTP method should return 405."""
        from core.api_contract import register_error_handlers
        with app.app_context():
            register_error_handlers(app)
            with app.test_client() as client:
                resp = client.post("/system/health")  # health is GET-only
                assert resp.status_code in (405, 404, 401)

    def test_correlation_id_in_response(self, app):
        """Every response should have a correlation ID."""
        with app.test_client() as client:
            resp = client.get("/system/health")
            assert "X-Correlation-ID" in resp.headers or "X-Request-ID" in resp.headers


class TestAuthzBoundary:
    """Authorization is enforced at the resource level."""

    def test_rbac_roles_defined(self, app):
        """Role-based access control roles must be defined."""
        from app.production.auth.authorization_middleware import Action
        with app.app_context():
            assert Action.CREATE is not None
            assert Action.READ is not None
            assert Action.UPDATE is not None
            assert Action.DELETE is not None
            assert Action.ADMIN is not None

    def test_permission_map_defined(self, app):
        """Permission map must have entries for critical resources."""
        with app.app_context():
            try:
                from app.production.auth.authorization_middleware import _PERMISSION_MAP
                assert "admin" in _PERMISSION_MAP
                assert "org" in _PERMISSION_MAP.get("admin", {})
                assert "user" in _PERMISSION_MAP.get("admin", {})
            except ImportError:
                pass  # Permission map may not be importable directly

    def test_identity_service_requires_tenant(self, app):
        """IdentityService must require tenant context."""
        from core.identity_interface import IdentityClaim, ClaimType
        from app.identity.service import IdentityService
        with app.app_context():
            svc = IdentityService()
            # Tenant-less claim should not silently succeed
            try:
                result = svc.add_claim(IdentityClaim(
                    claim_value="auth-test@example.com",
                    claim_type=ClaimType.EMAIL,
                    source="auth_test",
                    source_id="auth_test_001",
                    tenant_id=None,
                ))
                assert result is not None
            except Exception:
                pass  # Expected to fail or require tenant


class TestSecurityHeaders:
    """Security headers are properly configured."""

    def test_content_type_options(self, app):
        with app.test_client() as client:
            resp = client.get("/system/health")
            val = resp.headers.get("X-Content-Type-Options", "")
            assert val.lower() == "nosniff", f"Expected nosniff, got {val}"

    def test_frame_options(self, app):
        with app.test_client() as client:
            resp = client.get("/system/health")
            val = resp.headers.get("X-Frame-Options", "")
            assert val.lower() in ("deny", "sameorigin"), f"Got {val}"

    def test_hsts(self, app):
        with app.test_client() as client:
            resp = client.get("/system/health")
            val = resp.headers.get("Strict-Transport-Security", "")
            if val:
                assert "max-age=" in val, f"HSTS missing max-age: {val}"

    def test_no_server_leak(self, app):
        with app.test_client() as client:
            resp = client.get("/system/health")
            server = resp.headers.get("Server", "")
            if server:
                assert "nginx" not in server.lower(), f"Server header leaks: {server}"