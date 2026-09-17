"""Routes and blueprints that support personal workspace scope (R6B-2.7 Window 6A).

Adding a route here means it is accessible to users with only a personal
workspace (no organization membership). Routes NOT in this list remain
protected for org-only access.

A personal identity must NEVER gain access to organization data merely because
personal scope is allowed — these routes must check workspace context themselves
and reject org-scoped data when the caller holds only personal scope.
"""

# Blueprint URL prefixes that support personal workspace scope.
# A request to ANY route under these prefixes is allowed for personal-scope
# users, bypassing the global org-membership guard. Each individual route
# retains its own authorization (e.g. @require_permission for org routes).
PERSONAL_SCOPE_BLUEPRINT_PREFIXES = frozenset({
    "/api/v1/content",      # Content Studio — generate + history
    "/api/v1/ai",           # AI chat, research
    "/api/v1/workspace",    # Workspace management (list, create, switch)
    "/api/v1/space",        # Space API
})

# Specific route paths that support personal workspace scope.
# These are individual routes not covered by a personal-scope blueprint prefix.
PERSONAL_SCOPE_ROUTES = frozenset({
    "/",
    "/living",
})


def supports_personal_scope(path: str) -> bool:
    """Check whether ``path`` may be accessed with personal workspace scope.

    Returns True when the route is explicitly registered as personal-scope
    capable. Returns False for all other routes — those remain protected by
    the global org-membership guard and will be denied.
    """
    if path in PERSONAL_SCOPE_ROUTES:
        return True
    for prefix in PERSONAL_SCOPE_BLUEPRINT_PREFIXES:
        if path.startswith(prefix):
            return True
    return False