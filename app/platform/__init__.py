"""SHUNYA — Developer & Integration Platform (FDA26).

Provides:
- Webhook subscriptions with server-side delivery, HMAC signature, retry, idempotency
- Connector SDK conventions for the canonical provider fabric
- OpenAPI documentation
- API versioning/deprecation policy
- Developer diagnostics
- Integration health visibility

Architectural rule: Every connector uses the canonical provider fabric:
    authentication → authorization → tenant context → execution → retry/idempotency → evidence/audit
No new identity/tenant/event/execution/audit system is created.
"""

from flask import Blueprint

platform_bp = Blueprint("platform", __name__, url_prefix="/api/v1/platform")

# Routes are imported in routes.py and registered in __init__.py
from app.platform.routes import *  # noqa: F401, E402

__all__ = ["platform_bp"]