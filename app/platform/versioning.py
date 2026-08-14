"""SHUNYA — API Versioning & Deprecation Policy (FDA26).

Versioning policy:
- The canonical API is /api/v1.
- New backward-incompatible changes are introduced as /api/v2 (already present).
- Every API response includes X-API-Version header.
- Deprecated endpoints emit a Deprecation warning header and remain
  functional for at least one minor release cycle.

Contract:
- A new connector must be addable without creating a second identity,
  event, tenant, execution, or audit system.
- Deprecation lifecycle: active → deprecated (warning header) → removed.
"""

from __future__ import annotations

from flask import g, request

CURRENT_API_VERSION = "v1"
LATEST_API_VERSION = "v1"
SUPPORTED_VERSIONS = ["v1", "v2"]

# Endpoints that have been deprecated. Format: {rule: {deprecated_in, removal_in, note}}
DEPRECATED_ENDPOINTS: dict[str, dict] = {}


def api_version() -> str:
    """Return the API version for the current request."""
    if hasattr(g, "api_version"):
        return g.api_version
    # Determine from URL prefix
    path = request.path
    for v in SUPPORTED_VERSIONS:
        if path.startswith(f"/api/{v}"):
            g.api_version = v
            return v
    g.api_version = CURRENT_API_VERSION
    return CURRENT_API_VERSION


def is_deprecated(rule: str) -> bool:
    """Check if a route rule is deprecated."""
    return rule in DEPRECATED_ENDPOINTS


def deprecate(rule: str, deprecated_in: str = "v1", removal_in: str = "v2", note: str = "") -> None:
    """Mark a route as deprecated."""
    DEPRECATED_ENDPOINTS[rule] = {
        "deprecated_in": deprecated_in,
        "removal_in": removal_in,
        "note": note,
    }


def apply_version_headers(response):
    """Attach version and deprecation headers to every API response."""
    if request.path.startswith("/api/"):
        version = api_version()
        response.headers["X-API-Version"] = version
        # Deprecation warning for deprecated endpoints
        rule = request.url_rule.rule if request.url_rule else ""
        if rule and is_deprecated(rule):
            info = DEPRECATED_ENDPOINTS[rule]
            response.headers["Deprecation"] = f'version="{info["deprecated_in"]}"'
            response.headers["Sunset"] = f'version="{info["removal_in"]}"'
            if info.get("note"):
                response.headers["Link"] = info["note"]
    return response


def version_summary() -> dict:
    """Developer-facing versioning summary for diagnostics."""
    return {
        "current_version": CURRENT_API_VERSION,
        "latest_version": LATEST_API_VERSION,
        "supported_versions": SUPPORTED_VERSIONS,
        "deprecated_endpoints": DEPRECATED_ENDPOINTS,
        "policy": (
            "Backward-incompatible changes are introduced under /api/v2. "
            "Deprecated endpoints emit Deprecation + Sunset headers and remain "
            "functional for at least one release cycle before removal."
        ),
    }
