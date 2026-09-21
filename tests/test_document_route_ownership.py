"""Document API route ownership — the /api/v1/documents collision guard.

Three document surfaces exist. Their relationship must be EXPLICIT, never decided
silently by blueprint registration order:

  * /api/v1/workspace/documents/*  -> app.documents_api (documents_bp)
        The FRONTEND contract. frontend/src/components/documents/document-browser.tsx
        fetches these routes.
  * /api/v1/documents (COLLECTION) -> app.document.document_intel_bp
        RBAC + tenant-isolated (@require_permission("knowledge.view")). It OWNS
        the collection rule.
  * /api/v1/documents (extensions) -> app.document_runtime.doc_bp
        Lifecycle/intelligence extensions (transition, ocr, risk, recommend,
        evidence, context, relationships, search, types, check-injection).
        It must NOT also claim the collection rule.

Why this matters: the two blueprints once registered the IDENTICAL rule
`GET /api/v1/documents`, and which one served the request depended on
registration order. The two have DIFFERENT authorization — the canonical surface
requires a permission and tenant scoping, the extension surface only requires an
identity header — so a registration reorder could silently swap an authorized
route for an unauthenticated one.
"""

from app import create_app


def _app():
    return create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })


def _owners(app):
    owners = {}
    for rule in app.url_map.iter_rules():
        for method in (rule.methods - {"HEAD", "OPTIONS"}):
            owners.setdefault((str(rule), method), []).append(rule.endpoint)
    return owners


def test_no_duplicate_document_rules():
    """No rule+method under /api/v1/documents may have two owners."""
    owners = _owners(_app())
    collisions = {
        key: eps for key, eps in owners.items()
        if len(eps) > 1 and key[0].startswith("/api/v1/documents")
    }
    assert collisions == {}, f"ambiguous blueprint precedence: {collisions}"


def test_collection_rule_owner_is_the_authorized_surface():
    """GET /api/v1/documents must belong to the RBAC surface, not doc_bp."""
    app = _app()
    endpoint, _ = app.url_map.bind("localhost").match("/api/v1/documents", method="GET")
    assert endpoint.startswith("document_intel."), (
        f"GET /api/v1/documents is owned by {endpoint!r}; the RBAC document "
        "intelligence surface must own it"
    )


def test_extension_blueprint_no_longer_claims_the_collection_rule():
    """The ambiguous duplicate must stay removed."""
    app = _app()
    endpoints = {r.endpoint for r in app.url_map.iter_rules()}
    assert "documents.list_documents" not in endpoints, (
        "doc_bp re-claimed the collection rule; ownership is ambiguous again"
    )


def test_extension_routes_still_registered():
    """De-duplicating the collection rule must not drop doc_bp's extensions."""
    app = _app()
    endpoints = {r.endpoint for r in app.url_map.iter_rules()}
    for expected in (
        "documents.create_document",
        "documents.transition_document",
        "documents.document_ocr",
        "documents.document_risk",
        "documents.check_injection",
        "documents.search_documents",
        "documents.list_document_types",
    ):
        assert expected in endpoints, f"{expected} was lost during de-duplication"


def test_document_by_id_resolution_is_explicit():
    """int ids resolve to the RBAC surface; non-int falls through to doc_bp."""
    adapter = _app().url_map.bind("localhost")
    int_endpoint, _ = adapter.match("/api/v1/documents/42", method="GET")
    assert int_endpoint.startswith("document_intel."), (
        f"int document-id resolved to {int_endpoint!r}"
    )
    str_endpoint, _ = adapter.match("/api/v1/documents/not-an-int", method="GET")
    assert str_endpoint == "documents.get_document", (
        f"non-int document-id resolved to {str_endpoint!r}"
    )


def test_frontend_contract_resolves():
    """The path the SPA actually fetches must resolve to documents_api."""
    app = _app()
    endpoint, _ = app.url_map.bind("localhost").match(
        "/api/v1/workspace/documents", method="GET")
    assert endpoint == "documents_api.list_documents"