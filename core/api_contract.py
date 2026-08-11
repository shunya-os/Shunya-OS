"""
SHUNYA — Canonical API Contract (FDA5-G2).

One coherent contract for every SHUNYA API endpoint.

Contract principles:
1. All public endpoints under /api/v1/
2. Consistent JSON request/response shapes
3. Consistent error structure
4. Authentication required by default
5. Tenant isolation enforced
6. Correlation IDs for tracing
7. Pagination and filtering where applicable
8. Idempotency keys for mutating operations
"""

import logging
import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

from flask import Response as FlaskResponse
from flask import jsonify, request, g, current_app

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Response helpers
# ═══════════════════════════════════════════════════════════════════

def success_response(
    data: Any = None,
    message: str = "OK",
    status: int = 200,
    meta: Optional[dict] = None,
) -> FlaskResponse:
    """Canonical success response."""
    body = {
        "success": True,
        "message": message,
        "data": data,
        "meta": meta or {},
    }
    resp = jsonify(body)
    resp.status_code = status
    _add_correlation_id(resp)
    return resp


def error_response(
    message: str = "An error occurred",
    status: int = 400,
    errors: Optional[list] = None,
    error_code: Optional[str] = None,
) -> FlaskResponse:
    """Canonical error response."""
    body = {
        "success": False,
        "message": message,
        "error_code": error_code,
        "errors": errors or [],
    }
    resp = jsonify(body)
    resp.status_code = status
    _add_correlation_id(resp)
    return resp


def paginated_response(
    data: list,
    total: int,
    page: int,
    per_page: int,
    message: str = "OK",
) -> FlaskResponse:
    """Canonical paginated response."""
    return success_response(
        data=data,
        message=message,
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, -(-total // per_page)),  # ceil division
        },
    )


def _add_correlation_id(resp: FlaskResponse) -> None:
    """Attach correlation ID to response headers."""
    corr_id = getattr(g, "correlation_id", None) or str(uuid.uuid4())
    resp.headers["X-Correlation-ID"] = corr_id


# ═══════════════════════════════════════════════════════════════════
# Correlation ID middleware
# ═══════════════════════════════════════════════════════════════════

def inject_correlation_id() -> Callable:
    """Middleware: ensure every request has a correlation ID."""
    from flask import g, request

    def middleware() -> None:
        corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        g.correlation_id = corr_id

    return middleware


# ═══════════════════════════════════════════════════════════════════
# Authentication helpers
# ═══════════════════════════════════════════════════════════════════

def get_current_identity() -> Optional[dict]:
    """Return the current authenticated identity from the request context."""
    return getattr(g, "identity", None)


def get_current_tenant() -> Optional[str]:
    """Return the current tenant ID from the request context."""
    identity = get_current_identity()
    if identity:
        return identity.get("tenant_id")
    return None


def require_auth(f: Callable) -> Callable:
    """Decorator: require authentication for an endpoint."""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> FlaskResponse:
        identity = get_current_identity()
        if not identity:
            return error_response(
                message="Authentication required",
                status=401,
                error_code="UNAUTHORIZED",
            )
        return f(*args, **kwargs)

    return decorated


def require_tenant(f: Callable) -> Callable:
    """Decorator: require tenant context for an endpoint."""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> FlaskResponse:
        tenant = get_current_tenant()
        if not tenant:
            return error_response(
                message="Tenant context required",
                status=403,
                error_code="TENANT_REQUIRED",
            )
        g.tenant_id = tenant
        return f(*args, **kwargs)

    return decorated


# ═══════════════════════════════════════════════════════════════════
# Validation helpers
# ═══════════════════════════════════════════════════════════════════

class ValidationError(Exception):
    """Raised when request validation fails."""

    def __init__(self, message: str, errors: Optional[list] = None):
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)


def validate_required_fields(data: dict, required: list) -> Optional[FlaskResponse]:
    """Validate that required fields are present in the request data."""
    missing = [f for f in required if f not in data or data[f] is None]
    if missing:
        return error_response(
            message=f"Missing required fields: {', '.join(missing)}",
            status=400,
            error_code="VALIDATION_ERROR",
            errors=[{"field": f, "reason": "required"} for f in missing],
        )
    return None


def validate_pagination(
    page: Any = 1,
    per_page: Any = 20,
    max_per_page: int = 100,
) -> tuple:
    """Validate and normalize pagination parameters."""
    try:
        page = max(1, int(page))
        per_page = max(1, min(max_per_page, int(per_page)))
    except (TypeError, ValueError):
        page, per_page = 1, 20
    return page, per_page


# ═══════════════════════════════════════════════════════════════════
# Error handlers
# ═══════════════════════════════════════════════════════════════════

def register_error_handlers(app: Any) -> None:
    """Register canonical error handlers on the Flask app."""

    @app.errorhandler(400)
    def bad_request(e):
        return error_response(message=str(e), status=400, error_code="BAD_REQUEST")

    @app.errorhandler(401)
    def unauthorized(e):
        return error_response(
            message="Authentication required", status=401, error_code="UNAUTHORIZED"
        )

    @app.errorhandler(403)
    def forbidden(e):
        return error_response(
            message="Access denied", status=403, error_code="FORBIDDEN"
        )

    @app.errorhandler(404)
    def not_found(e):
        return error_response(message="Not found", status=404, error_code="NOT_FOUND")

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error_response(
            message="Method not allowed", status=405, error_code="METHOD_NOT_ALLOWED"
        )

    @app.errorhandler(422)
    def unprocessable(e):
        return error_response(
            message="Unprocessable entity", status=422, error_code="UNPROCESSABLE"
        )

    @app.errorhandler(429)
    def too_many_requests(e):
        return error_response(
            message="Rate limit exceeded", status=429, error_code="RATE_LIMITED"
        )

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Internal server error")
        return error_response(
            message="Internal server error",
            status=500,
            error_code="INTERNAL_ERROR",
        )

    @app.errorhandler(ValidationError)
    def validation_error(e):
        return error_response(
            message=e.message,
            status=400,
            error_code="VALIDATION_ERROR",
            errors=e.errors,
        )