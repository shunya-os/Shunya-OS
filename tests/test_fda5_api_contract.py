"""FDA5-G2: Canonical API Contract tests."""
import json
import pytest
from flask import Flask, g


@pytest.fixture
def app():
    from app import create_app
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "DISABLE_RATE_LIMIT": "true",
    })
    return application


class TestApiContract:
    """Verify the canonical API contract works."""

    def test_success_response_shape(self, app):
        from core.api_contract import success_response
        with app.test_request_context():
            resp = success_response(data={"key": "value"}, message="OK")
            data = json.loads(resp.get_data(as_text=True))
            assert data["success"] is True
            assert data["message"] == "OK"
            assert data["data"]["key"] == "value"
            assert "meta" in data
            assert resp.status_code == 200

    def test_error_response_shape(self, app):
        from core.api_contract import error_response
        with app.test_request_context():
            resp = error_response(message="Not found", status=404, error_code="NOT_FOUND")
            data = json.loads(resp.get_data(as_text=True))
            assert data["success"] is False
            assert data["message"] == "Not found"
            assert data["error_code"] == "NOT_FOUND"
            assert resp.status_code == 404

    def test_paginated_response(self, app):
        from core.api_contract import paginated_response
        with app.test_request_context():
            resp = paginated_response(data=[1, 2, 3], total=30, page=2, per_page=3)
            data = json.loads(resp.get_data(as_text=True))
            assert data["success"] is True
            assert data["meta"]["total"] == 30
            assert data["meta"]["page"] == 2
            assert data["meta"]["per_page"] == 3
            assert data["meta"]["total_pages"] == 10

    def test_correlation_id_injected(self, app):
        from core.api_contract import success_response
        with app.test_request_context():
            resp = success_response()
            assert "X-Correlation-ID" in resp.headers

    def test_validation_error(self, app):
        from core.api_contract import validate_required_fields
        with app.test_request_context():
            result = validate_required_fields({"a": 1}, ["a", "b"])
            assert result is not None
            data = json.loads(result.get_data(as_text=True))
            assert data["error_code"] == "VALIDATION_ERROR"
            assert result.status_code == 400

    def test_error_handlers_registered(self, app):
        from core.api_contract import register_error_handlers
        with app.app_context():
            register_error_handlers(app)
            with app.test_client() as client:
                resp = client.get("/nonexistent")
                assert resp.status_code == 404
                data = json.loads(resp.get_data(as_text=True))
                assert data["success"] is False
                assert data["error_code"] == "NOT_FOUND"

    def test_require_auth_decorator_rejects(self, app):
        from core.api_contract import require_auth, error_response
        with app.test_request_context():
            @require_auth
            def protected_route():
                return error_response(message="OK", status=200)

            resp = protected_route()
            data = json.loads(resp.get_data(as_text=True))
            assert data["error_code"] == "UNAUTHORIZED"
            assert resp.status_code == 401

    def test_pagination_validation(self, app):
        from core.api_contract import validate_pagination
        with app.test_request_context():
            page, per_page = validate_pagination("abc", "xyz")
            assert page == 1
            assert per_page == 20

            page, per_page = validate_pagination(3, 50)
            assert page == 3
            assert per_page == 50

            page, per_page = validate_pagination(1, 999)
            assert per_page == 100  # max_per_page cap

    def test_register_error_handlers_does_not_crash(self, app):
        from core.api_contract import register_error_handlers
        with app.app_context():
            register_error_handlers(app)
            # Verify 404 returns correct shape
            with app.test_client() as client:
                resp = client.get("/nonexistent")
                assert resp.status_code == 404
                data = json.loads(resp.get_data(as_text=True))
                assert data["success"] is False
                assert data["error_code"] == "NOT_FOUND"